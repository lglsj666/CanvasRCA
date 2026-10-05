"""Small registration, identities, runtime and source contracts. No model calls."""
from pathlib import Path
import json
import os
import time

from unified_scripts import stable_hash
from vlmrca.run_state import read_json, write_json, sha_file, atomic_write
from RQs.RQ3_8.src.utils import exclusive, immutable_json

ROOT = Path(__file__).resolve().parents[3]
VERSION = "rq39_joint_comparison_v1"
MODEL = "qwen3.8-27b"
ARMS = ("TEXT_FLAT", "TEXT_JOINT", "VIS_SEPARATE", "VIS_JOINT")
METRICS = ("mrr", "ac@1", "ac@3", "ac@5", "avg@3", "avg@5")


def config():
    c = read_json(ROOT / "RQs/RQ3_9/configs/joint_comparison_v1.json")
    if (c["version"] != VERSION or c["model"] != MODEL or tuple(c["arms"]) != ARMS
            or c["formal_positions"] != 480 or c["formal_attempt_limit"] != 480
            or c["max_tokens"] != 8192 or c["request_timeout"] != 300
            or c["smoke_seconds"] != 600 or c["smoke_attempt_limit"] > 18):
        raise ValueError("Unregistered RQ3.9 settings")
    return c


def path(value):
    p = (ROOT / value).resolve()
    if not p.is_relative_to(ROOT):
        raise ValueError("Artifact escaped worktree")
    return p


def logical_key(oid, arm):
    return stable_hash([VERSION, MODEL, oid, arm])


def runtime(c):
    """Inherit the qualified local Qwen recipe; no Gemma loading or environment edit."""
    import yaml
    from unified_scripts.vllm_inference import VLLMInferenceConfig
    source = path(c["inference_base"])
    profile = yaml.safe_load(source.read_text())
    # The shared profile schema requires both model recipes. Retaining an
    # unused recipe does not load its weights: RQ3.9 dispatches only MODEL.
    profile["models"][MODEL]["gdn_prefill_backend"] = "triton"
    profile["status"] = "rq39_qwen_only_local_adapter"
    profile["rq39_adapter"] = {"version": VERSION, "source_sha256": sha_file(source)}
    destination = path(c["results"]) / c["runtime_profile"]
    encoded = yaml.safe_dump(profile, sort_keys=False).encode()
    if destination.exists() and destination.read_bytes() != encoded:
        if any((path(c["results"])/phase/"calls.sqlite").exists() for phase in ("smoke", "formal")):
            raise ValueError("Runtime projection changed after calls; keep historical file")
        destination.rename(destination.with_name(destination.name + ".preflight_rejected." + str(time.time_ns())))
    if not destination.exists():
        atomic_write(destination, encoded)
    os.environ["CANVASRCA_VLLM_CONFIG"] = str(destination)
    os.environ.setdefault("CANVASRCA_VLLM_PORT", "21939")
    loaded = VLLMInferenceConfig.load(destination)
    spec = loaded.model(MODEL)
    from RQs.RQ3_8.src.utils import bind_client_endpoint
    bind_client_endpoint(MODEL, spec)
    return loaded, spec


def source_contract():
    from renderer.gates import source_fingerprint
    names = []
    for folder in ("RQs/RQ3_9/src", "RQs/RQ3_9/configs", "RQs/RQ3_9/scripts"):
        names.extend(p for p in (ROOT / folder).glob("*") if p.suffix in {".py", ".json", ".sh"})
    for name in ("RQs/RQ3_8/src/exps.py", "RQs/RQ3_8/src/utils.py", "RQs/RQ3_8/src/main.py",
                 "RQs/RQ3_1/src/main.py", "RQs/RQ3_1/src/utils.py", "RQs/RQ3_1/configs/research_v2.json",
                 "RQs/RQ3_3/src/exps.py", "RQs/RQ3_3/src/utils.py", "RQs/RQ3_3/src/main.py", "RQs/RQ3_6/src/utils.py",
                 "RQs/RQ3_8/src/gates.py", "RQs/RQ1_1/src/renderer/panels.py", "RQs/RQ1_1/src/renderer/dashboard.py",
                 "RQs/RQ2/src/exps.py", "RQs/RQ2/src/utils.py", "src/vlmrca/run_state.py",
                 "src/vlmrca/vlm/client.py", "src/vlmrca/vlm/configs.py",
                 "src/unified_scripts/vllm_inference.py", "src/unified_scripts/rca_scorer.py",
                 "configs/rca_scorer.yaml", "configs/vllm_inference_local.yaml",
                 "src/renderer/web/dist/render.mjs", "scripts/env_local.sh", "scripts/env.sh",
                 "scripts/vllm_vlm/serve_canvasrca_local.sh"):
        p = ROOT / name
        if p.exists():
            names.append(p)
    files = {str(p.relative_to(ROOT)): sha_file(p) for p in sorted(names)}
    return {"version": VERSION, "files": files, "renderer": source_fingerprint()}


def register(c):
    root = path(c["results"])
    target = root / "registration.json"
    source = path(c["parent"]) / "roster_formal4_q3g1.json"
    if target.exists():
        reg = read_json(target)
        if reg["config_hash"] != stable_hash(c):
            raise ValueError("Registration changed")
        return reg
    parent = read_json(source)
    rows = []
    for ds in c["datasets"]:
        candidates = [r for r in parent["cases"] if r["dataset"] == ds and r["cohort"] == "eval"]
        candidates.sort(key=lambda r: stable_hash([c["seed"], VERSION, r["opaque_incident_id"]]))
        rows.extend({k: r[k] for k in ("opaque_incident_id", "dataset", "cohort", "source", "leakage_group")}
                    for r in candidates[:c["per_dataset"]])
    if len(rows) != 120 or len({r["opaque_incident_id"] for r in rows}) != 120:
        raise ValueError("Expected 120 unique main-dataset development cases")
    smoke = [next(r for r in rows if r["dataset"] == ds) for ds in c["datasets"]]
    reg = {"version": VERSION, "config_hash": stable_hash(c), "cases": rows, "smoke": smoke,
           "source_roster": str(source.relative_to(ROOT)), "source_roster_hash": sha_file(source),
           "groups": parent["groups"], "selected_before_reading_outcomes": True,
           "scope": "hash-selected exposed eval; no test/unused access", "created": time.time()}
    immutable_json(target, reg)
    return reg


def flag(root, oid, arm):
    p = root / "flags" / (logical_key(oid, arm) + ".json")
    if not p.exists():
        return None
    value = read_json(p)
    if value.get("status") not in {"done", "fail", "design_infeasible"}:
        raise ValueError("Malformed terminal flag")
    if value.get("case") != oid or value.get("arm") != arm:
        raise ValueError("Terminal identity mismatch")
    if value["status"] == "fail" and value.get("failure_class") != "request_timeout":
        raise RuntimeError("Infrastructure failure requires diagnosis; no automatic retry")
    return value


def log(event, **payload):
    print(json.dumps({"time": time.time(), "event": event, **payload}, ensure_ascii=False), flush=True)
