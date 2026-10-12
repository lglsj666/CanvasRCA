"""Versioned registration and small durable identities; imports do not load data."""
from pathlib import Path
from contextlib import contextmanager
import json
import os

from unified_scripts import stable_hash
from vlmrca.run_state import read_json, write_json as write_json, sha_file, atomic_write
from RQs.RQ3_8.src.utils import exclusive as exclusive, immutable_json

ROOT = Path(__file__).resolve().parents[3]
VERSION = "rq311_protected_compression_v1"
MODEL = "qwen3.8-27b"
ARMS = ('EXACT_TEXT', 'EXACT_REPEAT', 'COARSE_VISUAL_LOW', 'COARSE_VISUAL_HIGH', 'PROTECTED_TEXT_LOW', 'PROTECTED_TEXT_HIGH', 'PROTECTED_VISUAL_LOW', 'PROTECTED_VISUAL_HIGH')
METRICS = ("mrr", "ac@1", "ac@3", "ac@5", "avg@3", "avg@5")


def config():
    c = read_json(ROOT / "RQs/RQ3_11/configs/protected_compression_v1.json")
    n = sum(c["case_counts"].values()) * len(ARMS)
    if (c["version"] != VERSION or c["model"] != MODEL or tuple(c["arms"]) != ARMS
            or c["case_counts"] != {"aiops2022": 60, "aiops2025": 60, "aegislab": 20}
            or n != c["formal_positions"] or n != 1120
            or c["formal_attempt_limit"] + c["smoke_attempt_limit"] != c["total_attempt_limit"]
            or c["total_attempt_limit"] != 1180 or c["smoke_attempt_limit"] != 18
            or c["smoke_seconds"] != 600 or c["max_tokens"] != 8192
            or c["launch_policy"] != "explicit_command_after_qualification"
            or c["request_timeout"] != 300 or c["workers"] != 8 or c["concurrency"] != 36):
        raise ValueError("Unregistered RQ3.11 configuration")
    return c


def path(value):
    p = (ROOT / value).resolve()
    if not p.is_relative_to(ROOT):
        raise ValueError("Artifact outside current worktree")
    return p


def logical_key(oid, arm):
    if arm not in ARMS:
        raise ValueError("Unknown arm")
    return stable_hash([VERSION, MODEL, oid, arm])


def source_contract():
    from renderer.gates import source_fingerprint
    names = []
    for folder in ("RQs/RQ3_11/src", "RQs/RQ3_11/configs", "RQs/RQ3_11/scripts"):
        names.extend(p for p in (ROOT / folder).glob("*") if p.suffix in {".py", ".json", ".sh"})
    for name in ("docs/experiment_plans/CanvasRCA_RQ3_11_Protected_Compression_Plan.md",
                 "RQs/RQ3_8/src/exps.py", "RQs/RQ3_8/src/main.py", "RQs/RQ3_8/src/utils.py",
                 "RQs/RQ3_8/src/gates.py", "RQs/RQ3_1/src/main.py", "RQs/RQ3_1/src/gates.py",
                 "RQs/RQ3_1/src/exps.py", "RQs/RQ3_3/src/exps.py", "RQs/RQ3_3/src/utils.py",
                 "RQs/RQ3_3/src/main.py", "RQs/RQ3_6/src/utils.py",
                 "RQs/RQ2/src/utils.py", "src/vlmrca/vlm/performance.py",
                 "src/vlmrca/run_state.py", "src/vlmrca/vlm/client.py", "src/vlmrca/vlm/configs.py",
                 "src/vlmrca/eval/scoring.py", "RQs/RQ3_1/src/__init__.py",
                 "src/unified_scripts/vllm_inference.py", "src/unified_scripts/rca_scorer.py",
                 "configs/rca_scorer.yaml", "configs/vllm_inference_local.yaml",
                 "configs/vllm_inference.yaml", "configs/dataset_segmentation.yaml",
                 "scripts/env_local.sh", "scripts/env.sh", "scripts/vllm_vlm/serve_canvasrca_local.sh",
                 "src/renderer/web/dist/render.mjs"):
        names.append(ROOT / name)
    return {"version": VERSION, "files": {str(p.relative_to(ROOT)): sha_file(p)
            for p in sorted(set(names))}, "renderer": source_fingerprint()}


def register(c):
    """Public roster only. No preparation, private outcomes or runtime projection."""
    target = path(c["results"]) / "registration.json"
    if target.exists():
        reg = read_json(target)
        if reg["config_hash"] != stable_hash(c):
            raise ValueError("Immutable registration/config changed")
        return reg
    # Measurement/representation repair must not select a new, easier cohort.
    file = path(c["roster_registration"])
    parent = read_json(file)
    rows = parent["cases"]
    from collections import Counter
    if dict(Counter(r["dataset"] for r in rows)) != c["case_counts"] or any(r["cohort"] != "eval" for r in rows):
        raise ValueError("Frozen predecessor cohort changed")
    if len({r["opaque_incident_id"] for r in rows}) != sum(c["case_counts"].values()):
        raise ValueError("Duplicate roster identity")
    reg = {"version": VERSION, "config_hash": stable_hash(c), "cases": rows,
           "smoke": parent["smoke"],
           "source_roster": str(file.relative_to(ROOT)), "source_roster_hash": sha_file(file),
           "groups": parent["groups"], "scope": "exposed eval, selected without outcomes"}
    immutable_json(target, reg)
    return reg


def runtime(c):
    """Materialize only on a future runtime/CPU command, not in static/register."""
    import yaml
    from unified_scripts.vllm_inference import VLLMInferenceConfig
    profile = yaml.safe_load(path(c["inference_base"]).read_text())
    profile["models"][MODEL]["gdn_prefill_backend"] = "triton"
    profile["status"] = "rq311_qwen_only_local_adapter"
    profile["rq311_adapter"] = {"version": VERSION, "source_sha256": sha_file(path(c["inference_base"]))}
    target = path(c["results"]) / c["runtime_profile"]
    payload = yaml.safe_dump(profile, sort_keys=False).encode()
    if target.exists() and target.read_bytes() != payload:
        raise ValueError("Refusing to overwrite historical runtime projection")
    if not target.exists():
        atomic_write(target, payload)
    os.environ["CANVASRCA_VLLM_CONFIG"] = str(target)
    os.environ["CANVASRCA_VLLM_PORT"] = str(c["port"])
    os.environ["CANVASRCA_RQ38_DEPLOYMENT"] = "local"
    loaded = VLLMInferenceConfig.load(target)
    spec = loaded.model(MODEL)
    from RQs.RQ3_8.src.utils import bind_client_endpoint
    bind_client_endpoint(MODEL, spec)
    return loaded, spec


def flag(root, oid, arm):
    file = root / "flags" / (logical_key(oid, arm) + ".json")
    if not file.exists():
        return None
    v = read_json(file)
    if v.get("status") not in {"done", "fail", "design_infeasible"} or v.get("case") != oid or v.get("arm") != arm:
        raise ValueError("Corrupt terminal identity/state")
    if v["status"] == "fail" and v.get("failure_class") != "request_timeout":
        raise RuntimeError("Infrastructure failure: diagnose before explicit repair, never automatically retry")
    if v["status"]=="done" and not (root/"completed"/(v["call_key"]+".json")).exists():
        return None  # Missing atomic commit remains incomplete; no bulk audit.
    return v


def phase_arms(c, smoke=False):
    return tuple(c["smoke_arms"]) if smoke else ARMS


def log(event, **fields):
    import time
    print(json.dumps({"event": event, "time": time.time(), **fields}, ensure_ascii=False), flush=True)


@contextmanager
def runtime_io_adapter(root, identities):
    """Process-local operational adapter; preserve shared inputs and scoring.

    The inherited transaction otherwise creates two threads per simultaneous
    writer and names checkpoints 'partial'. Cap the aggregate writer pool at8
    and add case/arm/request identity to the shared streaming checkpoint.
    """
    from concurrent.futures import ThreadPoolExecutor
    from RQs.RQ2.src import utils as parent
    from vlmrca.vlm import client
    original_writer, original_call = parent.AsyncWriter, client.call_vlm
    pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="rq311-artifact")

    class PooledWriter(original_writer):
        def __init__(self, workers=8):
            self._pool, self._pending = pool, []

        def drain(self):
            for future in self._pending:
                future.result()
            self._pending.clear()

    def stream_call(*args, **kwargs):
        metadata = kwargs.get("partial_metadata", {})
        identity = identities[metadata["call_key"]]
        kwargs["partial_metadata"] = {**metadata, **identity, "stage":"solver"}
        kwargs["partial_output_dir"] = root/"partial_responses"
        return original_call(*args, **kwargs)

    parent.AsyncWriter, client.call_vlm = PooledWriter, stream_call
    try:
        yield
    finally:
        pool.shutdown(wait=True)
        parent.AsyncWriter, client.call_vlm = original_writer, original_call
