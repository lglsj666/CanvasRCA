"""RQ2.1 registration, provenance, private grouping and durable accounting."""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import re
import shutil
import sqlite3
import tempfile
import threading
import time
from collections import defaultdict
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

import yaml

from packages.rq21_native.sircl_original.scoring import (
    is_service_level_hit,
    normalize_service,
)
from unified_scripts import stable_hash
from unified_scripts.dataset_segmentation import CaseRecord, DatasetSegmentationConfig

from .renderer.onset import pod_to_service

ROOT = Path(__file__).resolve().parents[3]
RQ_ROOT = ROOT / "RQs/RQ2_1"
PRIMARY = ("aegislab", "aiops2022", "aiops2025")
MODELS = ("qwen3.8-27b", "gemma-4-26b-a4b")


class ProtocolError(RuntimeError):
    """Implementation/integrity failure, never a zero-quality model result."""


class DesignInfeasible(ValueError):
    """A checked design cannot fit its registered input or geometric budget."""


RQ1Error = ProtocolError

NODE_PATTERNS = (
    re.compile(r"^node[-_]?\d+$", re.IGNORECASE),
    re.compile(r"^gke-.+-[a-z0-9]{4}$", re.IGNORECASE),
    re.compile(r"^(?:worker|master)[-_]?\d+$", re.IGNORECASE),
)


REPLICA_POD = re.compile(r"^.+-[a-f0-9]{8,10}-[a-z0-9]{4,6}$", re.IGNORECASE)


ORDINAL_POD = re.compile(r"^.+-\d+$")


def entity_granularity(name: str) -> str:
    if any(pattern.fullmatch(name) for pattern in NODE_PATTERNS):
        return "node"
    if REPLICA_POD.fullmatch(name) or ORDINAL_POD.fullmatch(name):
        return "pod"
    return "service"


def numeric_entity_map(
    entities: Iterable[str], opaque_incident_id: str, seed: int = 42
) -> tuple[dict[str, str], dict[str, str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for entity in sorted(set(map(str, entities))):
        groups[entity_granularity(entity)].append(entity)
    ranges = {
        "service": range(100, 1000),
        "node": range(1000, 10000),
        "pod": range(10000, 100000),
    }
    mapping: dict[str, str] = {}
    kinds: dict[str, str] = {}
    for kind in ("service", "node", "pod"):
        names = groups[kind]
        if len(names) > len(ranges[kind]):
            raise RQ1Error(f"too many {kind} entities for numeric identity space")
        digest = hashlib.sha256(f"{seed}:{opaque_incident_id}:{kind}".encode()).digest()
        values = random.Random(int.from_bytes(digest, "big")).sample(list(ranges[kind]), len(names))
        for name, value in zip(names, values, strict=True):
            mapping[name], kinds[name] = str(value), kind
    if len(mapping) != len(set(mapping.values())):
        raise RQ1Error("case-local numeric identity collision")
    return mapping, kinds


def is_granularity_aware_hit(predicted: str, accepted: str) -> bool:
    """Match a prediction at the accepted label's declared entity granularity."""
    predicted_norm = normalize_service(predicted)
    accepted_norm = normalize_service(accepted)
    if predicted_norm == accepted_norm:
        return True
    if is_service_level_hit(predicted_norm, accepted_norm):
        return True

    # If the accepted label itself projects to a shorter service name, it is a
    # pod label and remains exact. Physical node labels remain exact as well.
    if pod_to_service(accepted_norm) != accepted_norm:
        return False
    if accepted_norm.startswith(("node-", "worker-")):
        return False
    return normalize_service(pod_to_service(predicted_norm)) == accepted_norm


def rq21_scorer(config):
    from unified_scripts.rca_scorer import RCAScorer, RCAScorerConfig

    return RCAScorer(
        RCAScorerConfig.load(ROOT / config["unified"]["scorer"]),
        hit=is_granularity_aware_hit,
    )


def read_json(path):
    return json.loads(Path(path).read_text())


def sha_file(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def atomic_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_json(path, value):
    atomic_write(
        path,
        (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode(),
    )


class AsyncWriter:
    """Bounded asynchronous writes; drain propagates every persistence error."""

    def __init__(self, workers=8):
        self.pool = ThreadPoolExecutor(max_workers=min(8, max(1, workers)))
        self.pending = []
        self.lock = threading.Lock()

    def bytes(self, path, value):
        future = self.pool.submit(atomic_write, path, value)
        with self.lock:
            self.pending.append(future)
            oldest = self.pending.pop(0) if len(self.pending) >= 128 else None
        if oldest:
            oldest.result()
        return future

    def json(self, path, value):
        return self.bytes(
            path,
            (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode(),
        )

    def drain(self):
        try:
            for future in self.pending:
                future.result()
        finally:
            self.pool.shutdown(wait=True)
            self.pending.clear()


def load_config(path=None):
    config = yaml.safe_load(Path(path or RQ_ROOT / "configs/rq2_1.yaml").read_text())
    if config["models"] != list(MODELS) or config["selection"]["diversity_lambda"] != 0.5:
        raise ProtocolError("model order or fixed selector definition changed")
    if config["request_adapter"] != {
        "name": "context_safe_output_v1",
        "max_tokens": 8192,
        "input_limit": 32768,
        "max_images": 1,
    }:
        raise ProtocolError("RQ1.1 request adapter changed")
    fixed = config.get("fixed_anchor")
    if fixed and fixed != {
        "policy": "P0",
        "silhouette": "S0",
        "composition": "D0",
        "cube_enabled": False,
        "smoke_waiver": "user_2026_09_09_fixed_anchor_only",
    }:
        raise ProtocolError("fixed-anchor protocol changed")
    if (
        config["budgets"]["formal_calls"] != (35520 if fixed else 39360)
        or config["budgets"]["total_initiated_calls"] != 39999
    ):
        raise ProtocolError("registered RQ-wide call limits changed")
    if config["silhouette_density"] != {
        "baseline": "S0",
        "gap_scale": 0.5,
        "minimum_gap_px": 6,
    }:
        raise ProtocolError("registered compact-density definition changed")
    formal = sum(e["formal_call_max"] for e in config["experiments"].values())
    smoke = len(config["experiments"]) * config["budgets"]["smoke_calls_per_experiment"]
    if (
        formal != config["budgets"]["formal_calls"]
        or formal + smoke + config["budgets"]["reserved_repair_calls"] != 39999
    ):
        raise ProtocolError("formal, smoke and repair budgets do not reconcile")
    if not 1 <= config["scheduler"]["cpu_workers"] <= 8:
        raise ProtocolError("CPU workers outside the registered 1–8 capacity")
    return config


def formal_scope(config, experiment):
    """Separate new fixed-anchor targets from retained selection and old runs."""
    scope = config.get("formal_scopes", {}).get(experiment, f"{experiment}_formal_v1")
    if Path(scope).name != scope or not scope.startswith(experiment + "_formal_"):
        raise ProtocolError("unsafe or mismatched experiment result namespace")
    return scope


@lru_cache(maxsize=4)
def checkpoint_identity(path):
    """Read local checkpoint metadata once; no weights are loaded or modified."""
    path = Path(path).resolve()
    required = ("config.json", "tokenizer_config.json", "tokenizer.json")
    optional = (
        "download_manifest.json",
        "model.safetensors.index.json",
        "generation_config.json",
        "preprocessor_config.json",
        "processor_config.json",
    )
    if any(not (path / name).is_file() for name in required):
        raise ProtocolError("local checkpoint/tokenizer metadata missing")
    return {
        "resolved_path": str(path),
        "metadata_sha256": {
            name: sha_file(path / name) for name in required + optional if (path / name).is_file()
        },
    }


def relative(path):
    return str(Path(path).absolute().relative_to(ROOT))


def regular_files(directory):
    """Walk owned regular files only; never follow a directory symlink."""
    directory = Path(directory)
    if directory.is_symlink():
        raise ProtocolError(f"refusing a symlink root: {relative(directory)}")
    for parent, dirs, files in os.walk(directory, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not (Path(parent) / d).is_symlink())
        for name in sorted(files):
            path = Path(parent) / name
            if not path.is_symlink() and path.is_file():
                yield path


def inventory(directory, *, hashes=True):
    return [
        {
            "path": relative(p),
            "bytes": p.stat().st_size,
            **({"sha256": sha_file(p)} if hashes else {}),
        }
        for p in regular_files(directory)
    ]


def inherit_renderer():
    """Copy once, compare bytes before adaptation, retain original SHA evidence."""
    source = ROOT / "RQs/RQ1_1/src/renderer"
    target = RQ_ROOT / "src/renderer"
    provenance = RQ_ROOT / "configs/provenance/parent_renderer.json"
    if provenance.exists():
        return read_json(provenance)
    if target.exists():
        raise ProtocolError("renderer exists without initial-copy provenance")
    target.mkdir(parents=True)
    rows = []
    for path in sorted(source.rglob("*.py")):
        if path.is_symlink():
            raise ProtocolError("parent renderer source is a symlink")
        destination = target / path.relative_to(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
        if path.read_bytes() != destination.read_bytes():
            raise ProtocolError("initial renderer copy differs")
        rows.append(
            {
                "source": relative(path),
                "target": relative(destination),
                "sha256": sha_file(path),
                "byte_equal_before_modification": True,
            }
        )
    result = {
        "schema": "RQ21ParentRendererCopyV1",
        "files": rows,
        "manifest_sha256": stable_hash(rows),
    }
    write_json(provenance, result)
    return result


def epoch(value):
    if isinstance(value, (int, float)):
        return float(value)
    parsed = datetime.fromisoformat(str(value))
    return (parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)).timestamp()


def source_window(dataset, opaque, private):
    """Private isolation whitelist; nothing here enters a model-visible object."""
    meta = private["source_metadata"]
    if dataset == "aiops2022":
        center = epoch(private["event"]["absolute_timestamp"])
        width = float(meta["window_sec"])
        start, end = center - width, center + width
        source = str(meta["cloudbed"])
        event = f"{source}:{center}"
    else:
        start, end = (
            epoch(meta["telemetry_start_utc"]),
            epoch(meta["telemetry_end_utc"]),
        )
        source = dataset
        event = str(meta.get("injection_id" if dataset == "aegislab" else "uuid") or "")
    if not math.isfinite(start + end) or start > end:
        raise ProtocolError("invalid private source window")
    return {
        "opaque": opaque,
        "source": source,
        "event": event,
        "start": start,
        "end": end,
    }


def overlap_groups(rows):
    parent = list(range(len(rows)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, a in enumerate(rows):
        for j, b in enumerate(rows[:i]):
            same_event = bool(a["event"]) and a["source"] == b["source"] and a["event"] == b["event"]
            overlap = a["source"] == b["source"] and max(a["start"], b["start"]) <= min(a["end"], b["end"])
            if same_event or overlap:
                parent[root(i)] = root(j)
    groups = defaultdict(list)
    for i, row in enumerate(rows):
        groups[root(i)].append(row["opaque"])
    return [sorted(g) for g in groups.values()]


def subset_groups(groups, quota=30, seed=42):
    ordered = sorted(groups, key=lambda g: stable_hash([seed, sorted(g)]))
    reachable = {0: ()}
    for index, group in enumerate(ordered):
        for size, chosen in sorted(reachable.items(), reverse=True):
            new_size = size + len(group)
            if new_size <= quota and new_size not in reachable:
                reachable[new_size] = (*chosen, index)
    if quota not in reachable:
        raise ProtocolError(f"exact {quota}-case grouped partition is infeasible")
    return sorted(item for i in reachable[quota] for item in ordered[i])


class RQ21SegmentationAdapter:
    """Explicit use of the unified identity contract, with grouped RQ-local roles."""

    def __init__(self, config):
        self.config = config
        self.base = DatasetSegmentationConfig.load(config["unified"]["segmentation"])

    def materialize(self):
        manifest_path = ROOT / self.config["data"]["rq480"]
        manifest = read_json(manifest_path)
        corpus = ROOT / self.config["data"]["processed_root"]
        private_rows, windows, all_groups, selection = [], {}, {}, []
        expected = {
            "aegislab": 100,
            "aiops2022": 100,
            "aiops2025": 100,
            "re2_ob": 90,
            "re2_tt": 90,
        }
        if {d: len(v) for d, v in manifest["datasets"].items()} != expected:
            raise ProtocolError("RQ480 roster counts changed")
        for dataset, ids in manifest["datasets"].items():
            index = {
                r["case_id"]: r
                for r in map(
                    json.loads,
                    (corpus / "private" / dataset / "manifest.jsonl").read_text().splitlines(),
                )
            }
            windows[dataset] = []
            for case_id in ids:
                opaque = self.base.opaque_id(CaseRecord(dataset, case_id, Path(".")))
                row = index[case_id]
                if opaque != row["opaque_incident_id"]:
                    raise ProtocolError("canonical opaque ID mismatch")
                case_dir = corpus / "public" / dataset / row["path"]
                if not (case_dir / "_SUCCESS").is_file():
                    raise ProtocolError("canonical case is incomplete")
                private_rows.append(
                    {
                        "dataset": dataset,
                        "case_id": case_id,
                        "opaque_incident_id": opaque,
                    }
                )
                if dataset in PRIMARY:
                    metadata = read_json(corpus / "private" / dataset / (row["path"] + ".json"))
                    windows[dataset].append(source_window(dataset, opaque, metadata))
            if dataset in PRIMARY:
                groups = overlap_groups(windows[dataset])
                all_groups[dataset] = groups
                selection.extend(subset_groups(groups, 30, self.config["seed"]))
        selection_set = set(selection)
        for row in private_rows:
            row["role"] = (
                "selection"
                if row["opaque_incident_id"] in selection_set
                else "report"
                if row["dataset"] in PRIMARY
                else row["dataset"]
            )
        public_rows = [{k: v for k, v in row.items() if k != "case_id"} for row in private_rows]
        result = {
            "schema": "RQ21GroupedRosterV1",
            "source_sha256": sha_file(manifest_path),
            "seed": self.config["seed"],
            "repeated_exposed": True,
            "cases": public_rows,
            "groups": all_groups,
        }
        result["roster_sha256"] = stable_hash(result)
        private = {
            "cases": private_rows,
            "source_windows": windows,
            "public_roster_sha256": result["roster_sha256"],
        }
        return result, private


class CallLedger:
    """Atomic cross-process quota and request-result reuse; crash attempts count."""

    def __init__(self, path, ceiling=39999):
        self.path, self.ceiling = Path(path), ceiling
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS attempts (
                    id INTEGER PRIMARY KEY, call_key TEXT NOT NULL, scope TEXT NOT NULL,
                    started REAL NOT NULL, status TEXT NOT NULL, result_path TEXT);
                CREATE INDEX IF NOT EXISTS by_key ON attempts(call_key);
            """)

    def connect(self):
        db = sqlite3.connect(self.path, timeout=60)
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=FULL")
        return db

    def begin(self, key, scope, scope_ceiling=None, *, result_path=None):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            count = db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
            scoped = db.execute("SELECT COUNT(*) FROM attempts WHERE scope=?", (scope,)).fetchone()[0]
            if count >= self.ceiling or (scope_ceiling is not None and scoped >= scope_ceiling):
                raise ProtocolError("aggregate initiated-call budget exhausted")
            if db.execute("SELECT 1 FROM attempts WHERE call_key=? AND status='running'", (key,)).fetchone():
                raise ProtocolError("identical request is already running; recover explicitly first")
            cursor = db.execute(
                "INSERT INTO attempts(call_key,scope,started,status,result_path) VALUES(?,?,?,'running',?)",
                (key, scope, time.time(), str(result_path) if result_path else None),
            )
            return cursor.lastrowid

    def finish(self, attempt, status, path=None):
        if status not in {
            "completed",
            "model_failure",
            "infrastructure_failure",
            "interrupted",
        }:
            raise ProtocolError("unknown call terminal status")
        with self.connect() as db:
            changed = db.execute(
                "UPDATE attempts SET status=?,result_path=COALESCE(?,result_path) WHERE id=? AND status='running'",
                (status, str(path) if path else None, attempt),
            ).rowcount
            if changed != 1:
                raise ProtocolError("attempt not in running state")

    def completed(self, key):
        with self.connect() as db:
            rows = db.execute(
                "SELECT result_path FROM attempts WHERE call_key=? AND status IN ('completed','model_failure') ORDER BY id",
                (key,),
            ).fetchall()
        for (value,) in rows:
            path = ROOT / value if value else None
            if path and path.is_file():
                record = read_json(path)
                checksum = record.pop("record_sha256", None)
                if (
                    checksum == stable_hash(record)
                    and record.get("call_key") == key
                    and artifacts_valid(record)
                ):
                    return path
        return None

    def recover_interrupted(self):
        """Caller must own the run lock: no other driver can still be alive."""
        with self.connect() as db:
            count = db.execute("UPDATE attempts SET status='interrupted' WHERE status='running'").rowcount
            paths = db.execute(
                "SELECT result_path FROM attempts WHERE status IN ('interrupted','infrastructure_failure') AND result_path IS NOT NULL"
            ).fetchall()
        # Reconcile before scheduling aliases, not only when the original target
        # happens to run first. At most interrupted attempts require this scan.
        for (value,) in paths:
            path = ROOT / value
            if path.is_file():
                self.reconcile_terminal(path)
        return count

    def reconcile_terminal(self, path):
        """Complete the journal after a crash between artifact fsync and SQL commit."""
        record = read_json(path)
        checksum = record.pop("record_sha256", None)
        if checksum != stable_hash(record) or not artifacts_valid(record):
            raise ProtocolError("cannot reconcile an unauthenticated terminal")
        if record["status"] not in {"completed", "model_failure"}:
            return
        with self.connect() as db:
            row = db.execute("SELECT call_key FROM attempts WHERE id=?", (record["attempt"],)).fetchone()
            if row != (record["call_key"],):
                raise ProtocolError("terminal does not bind to the recorded request attempt")
            db.execute(
                "UPDATE attempts SET status=?,result_path=? WHERE id=?",
                (record["status"], relative(path), record["attempt"]),
            )

    def resume_response(self, attempt, key):
        """Recover a durable response without initiating a new model request."""
        with self.connect() as db:
            changed = db.execute(
                "UPDATE attempts SET status='running' WHERE id=? AND call_key=? AND status IN ('interrupted','infrastructure_failure')",
                (attempt, key),
            ).rowcount
            if changed != 1:
                raise ProtocolError("durable response does not bind to a recoverable attempt")

    def count(self, scope=None):
        with self.connect() as db:
            return db.execute(
                "SELECT COUNT(*) FROM attempts" + (" WHERE scope=?" if scope else ""),
                (scope,) if scope else (),
            ).fetchone()[0]


def artifacts_valid(record):
    try:
        return bool(record.get("artifacts")) and all(
            (ROOT / row["path"]).is_file() and sha_file(ROOT / row["path"]) == row["sha256"]
            for row in record["artifacts"]
        )
    except (OSError, KeyError, TypeError):
        return False


def artifact_row(path):
    path = Path(path)
    return {
        "path": relative(path),
        "sha256": sha_file(path),
        "bytes": path.stat().st_size,
    }


def request_identity(model, recipe, parts, system, schema, adapter, replicate=0):
    """Hash only actual request content and recipe, not arm or PNG metadata."""
    import io

    from PIL import Image

    visible = []
    for part in parts:
        if part["type"] == "text":
            visible.append({"type": "text", "text": part["text"]})
        elif part["type"] == "image":
            img = Image.open(io.BytesIO(part["png"])).convert("RGB")
            visible.append(
                {
                    "type": "image",
                    "size": list(img.size),
                    "pixels": hashlib.sha256(img.tobytes()).hexdigest(),
                }
            )
        else:
            raise ProtocolError("unsupported request part")
    return stable_hash(
        {
            "model": model,
            "recipe": recipe,
            "parts": visible,
            "system": system,
            "schema": schema,
            "adapter": adapter,
            "replicate": replicate,
        }
    )


class RunLock:
    """Advisory process lock released by the OS even after power loss."""

    def __init__(self, path):
        self.path = Path(path)

    def __enter__(self):
        import fcntl

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.stream = self.path.open("a+")
        try:
            fcntl.flock(self.stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            self.stream.close()
            raise ProtocolError("another RQ2.1 driver is active") from error
        return self

    def __exit__(self, *args):
        self.stream.close()


def physical_cores():
    """One allowed logical CPU per physical core; no SMT-sibling double count."""
    cores = {}
    for cpu in sorted(os.sched_getaffinity(0)):
        root = Path(f"/sys/devices/system/cpu/cpu{cpu}/topology")
        key = (
            root.joinpath("physical_package_id").read_text().strip(),
            root.joinpath("core_id").read_text().strip(),
        )
        cores.setdefault(key, cpu)
    return list(cores.values())


def pin_worker(core_queue):
    os.sched_setaffinity(0, {core_queue.get()})
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"


def persist_attention(probe, parts, system, model, runtime, root, *, response_text=""):
    """One-call image/text diagnostics using the unchanged shared geometry code."""
    from vlmrca.vlm.attention_probe import (
        image_attention_diagnostics,
        map_groups_to_images,
        map_text_attention,
        render_overlay,
    )

    if not isinstance(probe, dict) or not probe.get("request_id"):
        raise ProtocolError("missing required same-call attention")
    root = Path(root)
    files, summary = [], {"extra_model_calls": 0, "correlational_only": True}
    raw = root / "raw_probe.json"
    write_json(raw, probe)
    files.append(raw)
    phases = [("prefill", probe)]
    generation = probe.get("generation_target_attention") or {}
    if generation.get("status") == "collected":
        phases.append(
            (
                "answer",
                {
                    **generation,
                    **{k: probe[k] for k in ("request_id", "model", "layer_name", "image_token_id")},
                },
            )
        )
    else:
        # The absence is structural only when there were no answer-bearing
        # alphanumeric tokens; do not accept arbitrary missing generation data.
        matched = re.search(r'"services"\s*:\s*\[([^\]]*)', response_text)
        if matched and re.search(r"[A-Za-z0-9]", matched.group(1)):
            raise ProtocolError("generation attention missing despite answer-bearing tokens")
        summary["answer"] = {
            "status": "not_applicable",
            "reason": "no alphanumeric answer-array token",
        }
    images = [p for p in parts if p["type"] == "image"]
    for name, source in phases:
        text = map_text_attention(source, runtime.model_path(model), system, parts)
        if text["unmatched_sources"]:
            raise ProtocolError("attention text spans failed to bind")
        for region in text["regions"].values():
            region["attention_per_token"] = (
                region["attention_mass"] / region["token_count"] if region["token_count"] else None
            )
        path = root / f"{name}_text.json"
        write_json(path, text)
        files.append(path)
        rows = (
            map_groups_to_images(
                source,
                [p["png"] for p in images],
                model_path=runtime.model_path(model),
                mm_processor_kwargs=runtime.model(model).get("mm_processor_kwargs"),
            )
            if images
            else []
        )
        regions = []
        for index, (part, artifact) in enumerate(zip(images, rows, strict=True)):
            artifact["diagnostics"] = image_attention_diagnostics(artifact, part, ("M", "R", "L", "G"))
            # Whole-canvas manifests exhaustively locate evidence and the header;
            # their remaining pixels are known neutral canvas, not unknown data.
            diagnostic = artifact["diagnostics"]
            if diagnostic.get("semantic_region") == "dashboard":
                for field in (
                    "global_region_mass",
                    "within_image_region_mass",
                    "region_pixel_area",
                ):
                    values = diagnostic[field]
                    values["blank"] += values["unassigned_image"]
                    values["unassigned_image"] = 0
                area = diagnostic["region_pixel_area"]["blank"]
                density = diagnostic["global_region_mass"]["blank"] / area if area else None
                diagnostic["region_attention_per_pixel"].update(blank=density, unassigned_image=None)
                reference = diagnostic["evidence_region_mean_attention_per_pixel"]
                diagnostic["region_density_lift"].update(
                    blank=density / reference if density is not None and reference else None,
                    unassigned_image=None,
                )
            weights = sorted(float(w) for w in artifact["weights"])
            mass, n = sum(weights), len(weights)
            probabilities = [w / mass for w in weights] if mass else []
            artifact["diagnostics"].update(
                mesh_mass_entropy=-sum(p * math.log(p) for p in probabilities if p > 0),
                mesh_mass_gini=(sum((2 * i - n - 1) * w for i, w in enumerate(weights, 1)) / (n * mass))
                if mass and n
                else None,
            )
            grid, overlay = (
                root / f"{name}_image_{index}.json",
                root / f"{name}_image_{index}.png",
            )
            write_json(grid, artifact)
            atomic_write(overlay, render_overlay(part["png"], artifact))
            files.extend([grid, overlay])
            regions.append(artifact["diagnostics"])
        summary[name] = {"text_regions": text["regions"], "image_regions": regions}
    return summary, files


def conversation_text(metadata, system, parts, response, images):
    out = [
        f"# RQ2.1 {metadata['experiment']} / {metadata['arm']}\n",
        f"Case: {metadata['case']}\nModel: {metadata['model']}\n",
        "\n## System\n",
        system,
        "\n## User\n",
    ]
    i = 0
    for part in parts:
        if part["type"] == "text":
            out.extend([part["text"], "\n"])
        else:
            out.append(f"\n![Model-visible dashboard]({images[i]})\n")
            i += 1
    out.extend(["\n## Assistant — unmodified response\n\n```text\n", response, "\n```\n"])
    return "".join(out)


def code_fingerprint():
    files = sorted((RQ_ROOT / "src").rglob("*.py"))
    files += sorted((ROOT / "packages/rq21_native").rglob("*.py"))
    files += sorted((RQ_ROOT / "scripts").glob("*.sh"))
    files += [
        ROOT / p
        for p in (
            "src/vlmrca/vlm/client.py",
            "src/vlmrca/vlm/configs.py",
            "src/vlmrca/vlm/attention_probe.py",
            "src/vlmrca/vlm/attention_probe_bootstrap/sitecustomize.py",
            "src/vlmrca/vlm/performance.py",
            "src/vlmrca/vlm/runtime_contract.py",
            "src/vlmrca/processed.py",
            "src/vlmrca/evidence.py",
            "src/vlmrca/log_calendar.py",
            "src/unified_scripts/__init__.py",
            "src/unified_scripts/dataset_segmentation.py",
            "src/unified_scripts/rca_scorer.py",
            "src/unified_scripts/vllm_inference.py",
            "src/unified_scripts/token_admission.py",
            "scripts/vllm_vlm/serve_canvasrca_local.sh",
            "scripts/vllm_vlm/enable_attention_probe.sh",
            "scripts/env_local.sh",
            "scripts/env.sh",
        )
    ]
    return stable_hash({relative(p): sha_file(p) for p in files})


def preparation_fingerprint(config):
    # Include all selection/projection helpers, not just top-level entry points.
    paths = sorted((RQ_ROOT / "src/renderer").glob("*.py")) + sorted(
        (ROOT / "packages/rq21_native").rglob("*.py")
    )
    paths += [
        RQ_ROOT / "src/exps.py",
        ROOT / config["parent"]["config"],
        ROOT / "src/vlmrca/processed.py",
        ROOT / "src/vlmrca/evidence.py",
        ROOT / "src/vlmrca/log_calendar.py",
    ]
    return stable_hash(
        {
            "files": {relative(p): sha_file(p) for p in paths},
            "seed": config["seed"],
            "selection": config["selection"],
            "data": config["data"],
        }
    )


def retire_rq2_generated():
    """Execute the approved exact-owner deletion, with durable audit before it."""
    source = ROOT / "RQs/RQ2/results"
    assets = ROOT / "docs/RQ2_retirement_assets"
    assets.mkdir(parents=True, exist_ok=True)
    marker = assets / "retirement_manifest.json"
    if marker.exists() and read_json(marker).get("status") == "completed":
        return read_json(marker)
    if source.is_symlink() or source.resolve() != source.absolute():
        raise ProtocolError("RQ2 result root is not a direct owned directory")
    protect_roots = [
        ROOT / name
        for name in (
            "RQs/RQ1_1/src",
            "RQs/RQ1_1/configs",
            "RQs/RQ2/src",
            "RQs/RQ2/configs",
            "RQs/RQ3",
            "configs",
            "docs/RQ1_1_RQ2_1_findings/assets",
        )
    ]
    protected = [row for root in protect_roots if root.is_dir() for row in inventory(root)]
    for name in (
        "docs/RQ1_1_RQ2_1_findings/findings.md",
        "docs/RQ1_report.md",
    ):
        path = ROOT / name
        if path.is_file():
            protected.append({"path": name, "bytes": path.stat().st_size, "sha256": sha_file(path)})
    write_json(assets / "protected_files.json", protected)
    paths = sorted(source.iterdir()) if source.exists() else []
    # A filesystem symlink is never followed, including during recursive deletion.
    for path in paths:
        if path.is_symlink():
            raise ProtocolError(f"resolve symlink ownership before cleanup: {relative(path)}")
    owned = inventory(source, hashes=False)
    write_json(assets / "deleted_file_inventory.json", owned)
    aggregates = []
    for path in regular_files(source):
        if (
            path.suffix == ".json"
            and (path.name.startswith("summary") or path.name in {"verification.json", "selection.json"})
            and path.stat().st_size <= 20 * 1024**2
        ):
            destination = assets / "historical_summaries" / path.relative_to(source)
            atomic_write(destination, path.read_bytes())
            aggregates.append(
                {
                    "source": relative(path),
                    "preserved": relative(destination),
                    "sha256": sha_file(path),
                }
            )
    manifest = {
        "schema": "RQ2RetirementV1",
        "status": "deletion_pending",
        "authorized_scope": "RQs/RQ2/results children only; no shared or symlink targets",
        "targets": [relative(p) for p in paths],
        "files": len(owned),
        "bytes": sum(r["bytes"] for r in owned),
        "preserved_aggregates": aggregates,
        "raw_artifacts_recoverable_from_this_repo": False,
    }
    write_json(marker, manifest)
    for path in paths:
        if path.parent != source or path.is_symlink():
            raise ProtocolError("deletion target changed after inventory")
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    for row in protected:
        path = ROOT / row["path"]
        if not path.is_file() or sha_file(path) != row["sha256"]:
            raise ProtocolError(f"protected artifact changed: {row['path']}")
    manifest.update(status="completed", protected_hashes_verified=len(protected))
    write_json(marker, manifest)
    return manifest
