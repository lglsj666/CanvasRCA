"""Versioned durable identities and local adapters; no import-time data work."""
from pathlib import Path
from contextlib import contextmanager
import json
import os
from unified_scripts import stable_hash
from vlmrca.run_state import read_json, write_json, sha_file, atomic_write
from RQs.RQ3_8.src.utils import exclusive, immutable_json
ROOT=Path(__file__).resolve().parents[3]
VERSION="rq313_observed_excursion_v1"
MODEL="qwen3.8-27b"
ARMS=("EXACT_TEXT","EXACT_REPEAT","EVENT_TEXT","EVENT_VISUAL","EVENT_PIXEL_TEXT","EVENT_VISUAL_REPEAT")
METRICS=("mrr","ac@1","ac@3","ac@5","avg@3","avg@5")


def config():
    c=read_json(ROOT/"RQs/RQ3_13/configs/observed_excursion_v1.json")
    if (c["version"]!=VERSION or c["model"]!=MODEL or tuple(c["arms"])!=ARMS
            or tuple(c["smoke_arms"])!=ARMS or c["formal_positions"]!=840
            or c["case_counts"]!={"aiops2022":60,"aiops2025":60,"aegislab":20}
            or c["formal_attempt_limit"]+c["smoke_attempt_limit"]!=900
            or c["smoke_attempt_limit"]!=18 or c["smoke_seconds"]!=600
            or c["max_tokens"]!=8192 or c["request_timeout"]!=300
            or c["workers"]!=8 or c["concurrency"]!=36
            or c["launch_policy"]!="explicit_command_after_qualification"
            or c["excursion"]!={"reference_min":12,"current_min":3,"phase_coverage_min":0.6,
                "iqr_margin":3,"quantile_method":"linear","bins":64}
            or c["preselected_method"]!="EVENT_VISUAL"):
        raise ValueError("Unregistered RQ3.13 configuration")
    return c


def source_contract():
    from importlib.metadata import version
    names=[]
    for folder in ("RQs/RQ3_13/src","RQs/RQ3_13/configs","RQs/RQ3_13/scripts"):
        names.extend(p for p in (ROOT/folder).glob("*") if p.suffix in {".py",".json",".sh"})
    dependencies=("RQs/RQ3_13/descriptions/RQ3_13_experiments.md",
        "RQs/RQ3_12/src/tests.py","RQs/RQ3_12/src/utils.py","RQs/RQ3_12/src/exps.py","RQs/RQ3_11/src/exps.py",
        "RQs/RQ3_11/src/utils.py","RQs/RQ3_11/src/gates.py",
        "RQs/RQ3_11/results/protected_v2/analysis_reviewed_v1/checkpoint_verification.json",
        "RQs/RQ3_8/src/exps.py","RQs/RQ3_8/src/main.py","RQs/RQ3_8/src/utils.py","RQs/RQ3_8/src/gates.py",
        "RQs/RQ3_1/src/main.py","RQs/RQ3_1/src/gates.py","RQs/RQ3_1/src/exps.py","RQs/RQ3_1/src/utils.py",
        "RQs/RQ3_1/configs/research_v2.json","RQs/RQ3_3/src/utils.py","RQs/RQ3_3/src/exps.py",
        "RQs/RQ3_3/src/main.py","RQs/RQ3_6/src/utils.py","RQs/RQ3_7/src/utils.py","RQs/RQ3_4/src/utils.py",
        "RQs/RQ2/src/utils.py","RQs/RQ2/src/exps.py",
        "src/vlmrca/run_state.py","src/vlmrca/vlm/client.py","src/vlmrca/vlm/configs.py",
        "src/vlmrca/vlm/performance.py","src/vlmrca/eval/scoring.py","src/vlmrca/processed.py",
        "src/unified_scripts/vllm_inference.py","src/unified_scripts/rca_scorer.py",
        "configs/vllm_inference.yaml","configs/vllm_inference_local.yaml","configs/dataset_segmentation.yaml",
        "configs/rca_scorer.yaml","scripts/env_local.sh","scripts/env.sh","scripts/vllm_vlm/serve_canvasrca_local.sh")
    names.extend(ROOT/name for name in dependencies)
    font=ROOT/"build/rq313_renderer/DejaVuSansMono.ttf"
    if font.exists(): names.append(font)
    runtime_file=path(config()["results"])/config()["runtime_profile"]
    if runtime_file.exists(): names.append(runtime_file)
    # Close project-local imports without executing any imported module.
    import ast
    pending=list(names); seen=set(names)
    while pending:
        file=pending.pop()
        if file.suffix!=".py": continue
        for node in ast.walk(ast.parse(file.read_text())):
            modules=[]
            if isinstance(node,ast.Import): modules=[a.name for a in node.names]
            elif isinstance(node,ast.ImportFrom):
                if node.level:
                    anchor=file.parent
                    for _ in range(node.level-1): anchor=anchor.parent
                    base=anchor.joinpath(*(node.module or "").split("."))
                else:
                    module=node.module or ""
                    if not module.startswith(("RQs.","renderer.","vlmrca.","unified_scripts")): continue
                    base=(ROOT if module.startswith("RQs.") else ROOT/"src").joinpath(*module.split("."))
                modules=[base]+[base/a.name for a in node.names]
            for module in modules:
                if isinstance(module,str):
                    if not module.startswith(("RQs.","renderer.","vlmrca.","unified_scripts")): continue
                    module=(ROOT if module.startswith("RQs.") else ROOT/"src").joinpath(*module.split("."))
                candidate=module.with_suffix(".py") if module.with_suffix(".py").is_file() else module/"__init__.py"
                if candidate.is_file() and candidate not in seen:
                    seen.add(candidate); pending.append(candidate)
    return {"version":VERSION,"files":{str(p.relative_to(ROOT)):sha_file(p) for p in sorted(seen)},
            "renderer":{"version":"rq313_native_pillow_v1","files":{},"pillow":version("Pillow"),
                "font_sha256":sha_file(font) if font.exists() else None}}

def path(value):
    p = (ROOT / value).resolve()
    if not p.is_relative_to(ROOT):
        raise ValueError("Artifact outside current worktree")
    return p


def logical_key(oid, arm):
    if arm not in ARMS:
        raise ValueError("Unknown arm")
    return stable_hash([VERSION, MODEL, oid, arm])


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
    if sha_file(file) != c["roster_sha256"]:
        raise ValueError("Frozen roster source changed")
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
    profile["status"] = "rq313_qwen_only_local_adapter"
    profile["rq313_adapter"] = {"version": VERSION, "source_sha256": sha_file(path(c["inference_base"]))}
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
    pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="rq313-artifact")

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
