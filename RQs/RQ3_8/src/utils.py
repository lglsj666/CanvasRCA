"""Portable identities, public-only exports and explicitly versioned deployment."""
from copy import deepcopy
from pathlib import Path
import fcntl
import json
import os
import sqlite3
import time
from contextlib import contextmanager

from unified_scripts import stable_hash
from vlmrca.run_state import atomic_write, read_json, sha_file, write_json

ROOT = Path(__file__).resolve().parents[3]
VERSION = "rq38_ops_components_v7"
CONFIG = ROOT / "RQs/RQ3_8/configs/ops_components_v7.json"
MODELS = ("qwen3.8-27b", "gemma-4-31b")
ARMS = ("TEXT", "TEXT_DUP", "MR00", "MR10", "MR01", "FULL", "NO_LOG", "NO_ONSET",
        "NO_CALLS", "NO_DEPLOY", "NO_G", "FULL_PAIRS", "MR00_PAIRS",
        "MR_NO_MARKS", "MR_NO_DETAILS", "MR_NO_MARKS_DETAILS")
MECHANISMS = ("METRIC_TIME_PERMUTED", "TRACE_LENGTH_NEUTRAL", "FULL_REPEAT",
              "TEXT_REPEAT", "FULL_PAIRS_REPEAT", "MR_NO_MARKS_REPEAT")
LOCKED = ("TEXT", "FULL", "FULL_PAIRS", "MR00")
ALL_ARMS = ARMS + MECHANISMS
METRICS = ("mrr", "ac@1", "ac@3", "ac@5", "avg@3", "avg@5")
FORMAL_ROSTER = "roster_formal4_q3g1.json"


def config():
    c = read_json(CONFIG)
    if (c["version"] != VERSION or tuple(c["models"]) != MODELS
            or tuple(c["arms"]) != ARMS or c["budget"]["formal_upper"] != 19440
            or tuple(c["mechanisms"]["arms"]) != MECHANISMS
            or tuple(c["regression"]["arms"]) != LOCKED
            or c["mechanisms"]["per_dataset"] != 20 or c["mechanisms"]["seed"] != 42
            or c["regression"]["cases"] != 360 or c["budget"]["smoke_upper"] != 18
            or c["budget"]["new_round_limit"] != 20000
            or c["budget"]["formal_upper"] + c["budget"]["smoke_upper"] + c["budget"]["reserve"] != 20000
            or c["request"]["max_tokens"] != 8192
            or c["execution"]["attention"] or c["smoke"]["max_calls"] != 18
            or c["smoke"]["max_seconds"] is not None or c["smoke"]["max_jobs"] != 8
            or c["runtime_profile"] != "runtime/inference.triton_v2.yaml"
            or c["smoke"]["job_seconds"] != 1800
            or c["execution"]["formal_shards"] != {"qwen3.8-27b": 3, "gemma-4-31b": 1}
            or c["execution"]["max_formal_jobs"] != 4
            or c["execution"]["max_job_seconds"] != 28800
            or c["submission_authorization"].get("formal_cpu_waived") is not True
            or c["cpu_qualification"] != {"max_jobs": 8, "job_seconds": 3600}):
        raise ValueError("Unregistered RQ3.8 contract")
    return c


def path(value):
    p = (ROOT / value).resolve()
    if not p.is_relative_to(ROOT):
        raise ValueError("Project artifact path escaped worktree")
    return p


@contextmanager
def exclusive(destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def immutable_json(destination, value):
    destination = Path(destination)
    if destination.exists():
        if read_json(destination) != value:
            raise ValueError(f"Immutable artifact changed: {destination.name}")
    else:
        write_json(destination, value)


def prior_calls(c):
    ledger = path(c["old_ledger"])
    with sqlite3.connect(f"file:{ledger}?mode=ro", uri=True) as db:
        return db.execute("SELECT COUNT(*) FROM calls").fetchone()[0]


def make_profile(c, destination):
    """Materialize a recorded Nibi adapter; never rewrite historical YAML."""
    import yaml
    base = path(c["inference_base"])
    profile = yaml.safe_load(base.read_text())
    profile["deployment"].update(python=".venv-inference/bin/python", vllm_bin=".venv-inference/bin/vllm")
    old = profile["models"].pop("gemma-4-26b-a4b")
    profile["models"]["gemma-4-31b"] = {
        **old, "model_path": "models/gemma-4-31B-it", "served_model_name": "google/gemma-4-31B-it",
        "repository_revision": "842da3794eaa0b77d5f08bae87a17459d91ff475",
        "mm_processor_kwargs": {"max_soft_tokens": 1120},
    }
    # auto chooses FlashInfer SM90 JIT on H100 but Triton/FLA on our local
    # RTX PRO6000. Pin the working backend explicitly; retain the old YAML.
    profile["models"]["qwen3.8-27b"]["gdn_prefill_backend"] = "triton"
    profile["status"] = "rq38_explicit_nibi_dense_gemma_adapter_pending_qualification"
    profile["rq38_adapter"] = {"version": "NibiGemma31QwenTritonV2", "base_sha256": sha_file(base)}
    text = yaml.safe_dump(profile, allow_unicode=True, sort_keys=False).encode()
    destination = Path(destination)
    if destination.exists() and destination.read_bytes() != text:
        raise ValueError("Refusing to overwrite another effective runtime profile")
    if not destination.exists():
        atomic_write(destination, text)
    from unified_scripts.vllm_inference import VLLMInferenceConfig
    frozen = VLLMInferenceConfig.load(destination)
    return {"path": str(destination), "sha256": sha_file(destination),
            "models": {m: frozen.model(m) for m in MODELS}}


def runtime_config(c):
    return {"models": list(MODELS), "request": {"max_tokens": 8192},
            "unified": {"vllm": str(path(c["results"])/c["runtime_profile"])}}


def bind_client_endpoint(model, spec):
    """Allocation-local transport adapter; never alter a scientific request."""
    from urllib.parse import urlsplit
    from vlmrca.vlm.configs import get_config, load_env
    load_env()
    cfg = get_config(model)
    url = str(spec["base_url"]).rstrip("/")
    parsed = urlsplit(url)
    if (parsed.scheme != "http" or parsed.hostname != "127.0.0.1"
            or parsed.port != int(spec["port"]) or parsed.path != "/v1"
            or parsed.username or parsed.password or parsed.query or parsed.fragment):
        raise ValueError("RQ3.8 endpoint must match the allocated loopback port")
    if cfg.model_id != spec["served_model_name"] or cfg.base_url_env != "VLLM_BASE_URL":
        raise ValueError("Shared client identity/endpoint adapter mismatch")
    os.environ[cfg.base_url_env] = url
    return {"model": model, "base_url": url, "port": parsed.port,
            "client_env": cfg.base_url_env}


@contextmanager
def supervisor_failure_record(root, smoke):
    """Commit an honest terminal status even when startup/driver/audit raises."""
    started = time.monotonic()
    try:
        yield
    except Exception as exc:
        write_json(Path(root)/"supervisor.json", {
            "status": "failed", "qualification": "failed", "smoke": smoke,
            "job_id": os.environ.get("SLURM_JOB_ID"),
            "seconds": time.monotonic()-started,
            "error": f"{type(exc).__name__}: {exc}", "finished": time.time()})
        raise


def load_roster(c):
    old = read_json(path(c["parent_export"])/"roster.json")
    rows = deepcopy(old["cases"])
    # Membership, not old implementation/shard choices, is inherited.
    ids = {r["opaque_incident_id"] for r in rows}
    registration = read_json(ROOT/"RQs/RQ3_7/results/fusion_v2_pruned/registration.json")
    expected = {r["opaque_incident_id"] for r in registration["rosters"]["eval"]}
    if len(rows) != 480 or ids != expected:
        raise ValueError("Export roster is not frozen RQ480")
    # Cohorts are frozen before results. Exposed test is never rebranded heldout.
    test = deepcopy(registration["rosters"]["test"])
    from collections import Counter
    if len(test) != c["regression"]["cases"] or Counter(r["dataset"] for r in test) != dict.fromkeys(("aiops2022", "aiops2025", "aegislab"), 120):
        raise ValueError("Expected exposed test360")
    if ids & {r["opaque_incident_id"] for r in test}:
        raise ValueError("Eval/test identity overlap")
    mechanism_ids = set()
    for dataset in sorted({r["dataset"] for r in rows}):
        group = sorted((r for r in rows if r["dataset"] == dataset),
                       key=lambda r: stable_hash([c["mechanisms"]["seed"], "rq38_mechanisms", r["opaque_incident_id"]]))
        mechanism_ids.update(r["opaque_incident_id"] for r in group[:c["mechanisms"]["per_dataset"]])
    for r in rows:
        r.update(cohort="eval", mechanism=r["opaque_incident_id"] in mechanism_ids)
    for r in test:
        r.update(cohort="test", mechanism=False)
    by_dataset = {}
    for r in rows+test:
        by_dataset.setdefault((r["cohort"], r["dataset"]), []).append(r)
    for dataset, group in by_dataset.items():
        group.sort(key=lambda r: stable_hash([42, r["opaque_incident_id"]]))
        for i, r in enumerate(group):
            r["shard"] = i % max(c["execution"]["formal_shards"].values())
    by_id = {r["opaque_incident_id"]: r for r in rows}
    smoke = [by_id[oid] for oid in old["smoke"]]
    for row in smoke:
        row["smoke_case"] = True
    if len(smoke) != 3 or {r["dataset"] for r in smoke} != {"aiops2022", "aiops2025", "aegislab"}:
        raise ValueError("Smoke must use three main-dataset development cases")
    if any(r["opaque_incident_id"] not in ids for r in smoke):
        raise ValueError("Smoke case outside eval")
    return {"cases": rows+test, "smoke": smoke, "scope": "exposed eval480 + exposed test360",
            "mechanisms": sorted(mechanism_ids), "groups": registration.get("groups", {})}


def case_arms(c, row, smoke=False):
    if smoke:
        return tuple(c["smoke"]["arms"])
    if row.get("cohort") == "test":
        return LOCKED
    return ARMS + (MECHANISMS if row.get("mechanism") else ())


def formal_rows(c, roster, model, shard):
    count = c["execution"]["formal_shards"][model]
    if not 0 <= shard < count:
        raise ValueError("Formal model/shard is outside the registered four-job map")
    return roster["cases"] if count == 1 else [r for r in roster["cases"] if r["shard"] == shard]


def base_arm(arm):
    return arm.removesuffix("_REPEAT")


def experiment_for(c, row, arm):
    if row.get("cohort") == "test":
        return c["regression"]["experiment"]
    return c["mechanisms"]["experiment"] if arm in MECHANISMS else c["experiment"]


def interleaved(rows):
    """Alternate source/cloudbed queues without changing case membership."""
    from collections import defaultdict, deque
    queues = defaultdict(deque)
    for row in rows:
        queues[(row["dataset"], row.get("source", row["opaque_incident_id"]))].append(row)
    answer = []
    while any(queues.values()):
        for key in sorted(queues):
            if queues[key]:
                answer.append(queues[key].popleft())
    return answer


def logical_key(model, oid, arm, smoke=False):
    return stable_hash([VERSION, "smoke" if smoke else "formal", model, oid, arm])


def read_flag(destination):
    p = Path(destination)
    if not p.exists():
        return None
    flag = read_json(p)
    if flag.get("status") not in {"done", "fail", "design_infeasible"}:
        raise ValueError("Malformed terminal flag, manual diagnosis required")
    return flag
