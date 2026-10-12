"""Versioned durable identities and local adapters; no import-time data work."""
from pathlib import Path
from contextlib import contextmanager
import json
import os
from unified_scripts import stable_hash
from vlmrca.run_state import read_json, write_json, sha_file, atomic_write
from RQs.RQ3_8.src.utils import exclusive, immutable_json
ROOT=Path(__file__).resolve().parents[3]
VERSION="rq315_request_joint_v1"
MODEL="qwen3.8-27b"
ARMS=('BASE_TEXT','BINARY_TEXT','PAIR_TEXT','PAIR_VISUAL','MARGINAL_VISUAL','PAIR_REPEAT')
METRICS=("mrr","ac@1","ac@3","ac@5","avg@3","avg@5")


def config():
    c=read_json(ROOT/"RQs/RQ3_15/configs/request_joint_v1.json")
    if (c["version"]!=VERSION or c["model"]!=MODEL or tuple(c["arms"])!=ARMS
        or c["case_counts"]!={"aiops2022":60,"aiops2025":60,"aegislab":100}
        or c["formal_positions"]!=1320 or c["total_attempt_limit"]!=1380
        or c["formal_attempt_limit"]+c["smoke_attempt_limit"]!=1380
        or c["smoke_attempt_limit"]!=18 or c["smoke_seconds"]!=600
        or c["max_tokens"]!=8192 or c["request_timeout"]!=300
        or c["workers"]!=8 or c["concurrency"]!=36):
        raise ValueError("Unregistered RQ3.15 configuration")
    from collections import Counter
    if (any(len(v)!=6 or len(set(v))!=6 for v in c["smoke_matrix"].values())
        or Counter(a for v in c["smoke_matrix"].values() for a in v)!=Counter({a:3 for a in ARMS})):
        raise ValueError("Smoke must cover six arms three times in eighteen calls")
    return c


def source_contract():
    names=[]
    for folder in ("RQs/RQ3_15/src","RQs/RQ3_15/configs","RQs/RQ3_15/scripts"):
        names.extend(p for p in (ROOT/folder).glob("*") if p.suffix in {".py",".json",".sh"})
    dependencies=("RQs/RQ3_15/descriptions/RQ3_15_experiments.md",
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
    from renderer.gates import source_fingerprint
    renderer=source_fingerprint()
    names.extend(ROOT/"src/renderer"/name for name in renderer["files"])
    names.extend(ROOT/name for name in ("src/renderer/web/dist/render.mjs", "src/renderer/web/assets/DejaVuSans.ttf"))
    names.append(ROOT/"RQs/RQ3_13/src/exps.py")
    names.append(ROOT/"RQs/RQ3_12/configs/conditional_residual_v4.json")
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
            "renderer":renderer}


def path(value):
    p = (ROOT / value).resolve()
    if not p.is_relative_to(ROOT):
        raise ValueError("Artifact outside current worktree")
    return p


def public_source(c, row, inherited):
    """Canonical public source; identity bridge is recomputed without labels."""
    import pickle
    import numpy as np
    import pandas as pd
    import pyarrow.parquet as pq
    from vlmrca.processed import processed_index, _case_dir
    from renderer.topology import frozen_candidate_mapping
    from RQs.RQ3_1.src.exps import _registered_trace_duration_projection
    from RQs.RQ3_3.src.utils import visible_string
    from RQs.RQ2_1.src.exps import _compiled_anonymizer
    from .exps import TRACE_COLUMNS
    oid=row['opaque_incident_id']
    source=read_json(path(c['parent_export'])/'audit'/(oid+'.json'))
    context_file=path(str(source['source_context']).removeprefix(str(ROOT)+'/'))
    if sha_file(context_file)!=source['context_sha256']: raise ValueError('Public context identity changed')
    ctx=pickle.loads(context_file.read_bytes())
    if ctx['prepared'].private or ctx['opaque_incident_id']!=oid: raise ValueError('Nonpublic context')
    clock=inherited['payload']['clock']
    if list(map(float,ctx['window']))!=[0.,float(clock['split']),float(clock['duration'])]:
        raise ValueError('Public phase clock mismatch')
    matches=[r for r in processed_index(row['dataset']).values() if r['opaque_incident_id']==oid]
    if len(matches)!=1: raise ValueError('Canonical case identity ambiguous')
    directory=_case_dir(row['dataset'],matches[0])
    hashes={name:sha_file(directory/name) for name in ('traces.parquet','metrics.parquet','metadata.json','graph.json')}
    if any(ctx['source_hashes'][k]!=v for k,v in hashes.items()): raise ValueError('Canonical source changed')
    mapping=frozen_candidate_mapping(row,ctx,directory,read_json(directory/'metadata.json'))
    if set(mapping.values())!=set(inherited['candidates']): raise ValueError('Baseline identity mismatch')
    times=pd.to_numeric(pq.read_table(directory/'metrics.parquet',columns=['timestamp'])['timestamp'].to_pandas(),errors='coerce')
    origin=float(times[np.isfinite(times)].min())
    if not np.isfinite(origin): raise ValueError('No public observation origin')
    file=pq.ParquetFile(directory/'traces.parquet')
    missing=sorted(set(TRACE_COLUMNS)-set(file.schema_arrow.names))
    frame=file.read(columns=list(TRACE_COLUMNS),use_threads=False).to_pandas() if not missing else pd.DataFrame(columns=TRACE_COLUMNS)
    projection,unit_contract=_registered_trace_duration_projection(row['dataset'])
    anonymizer=_compiled_anonymizer(mapping)
    operations={str(op):visible_string(str(op),mapping,anonymizer) for op in frame['operation_name'].dropna().unique()}
    from collections import defaultdict
    collisions=defaultdict(list)
    for original,visible in operations.items(): collisions[visible].append(original)
    for visible,originals in collisions.items():
        if len(originals)>1:
            for i,original in enumerate(sorted(originals),1): operations[original]=visible+' [operation '+str(i)+']'
    if len(set(operations.values()))!=len(operations): raise ValueError('Operation identity collision')
    return frame,mapping,operations,{**clock,'origin':origin},projection,{
        'source_hashes':hashes,'public_context_sha256':source['context_sha256'],
        'public_identity_map_sha256':stable_hash(mapping),'duration_projection':unit_contract,
        'duration_scale_to_ms':projection,'columns':list(TRACE_COLUMNS),'missing_columns':missing,
        'operation_alias_sha256':stable_hash(operations),'disambiguated_operation_groups':sum(len(v)>1 for v in collisions.values()),
        'source_trace_rows':file.metadata.num_rows,'clock':{**clock,'origin':origin},
        'label_access':False,'identity_bridge':'existing frozen_candidate_mapping on public source only'}


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
    file=path(c["roster_registration"])
    if sha_file(file)!=c["roster_sha256"]: raise ValueError("Frozen predecessor roster changed")
    parent=read_json(file); rows=parent["cases"]
    from collections import Counter
    if dict(Counter(r["dataset"] for r in rows))!=c["case_counts"] or any(r["cohort"]!="eval" for r in rows):
        raise ValueError("Registered exposed-eval roster changed")
    reg={"version":VERSION,"config_hash":stable_hash(c),"cases":rows,"smoke":parent["smoke"],
         "source_roster":str(file.relative_to(ROOT)),"source_roster_hash":sha_file(file),
         "groups":parent["groups"],"scope":"exposed eval; inherited complete220 without outcomes"}
    immutable_json(target, reg)
    return reg


def runtime(c):
    """Materialize only on a future runtime/CPU command, not in static/register."""
    import yaml
    from unified_scripts.vllm_inference import VLLMInferenceConfig
    profile = yaml.safe_load(path(c["inference_base"]).read_text())
    profile["models"][MODEL]["gdn_prefill_backend"] = "triton"
    profile["status"] = "rq315_qwen_only_local_adapter"
    profile["rq315_adapter"] = {"version": VERSION, "source_sha256": sha_file(path(c["inference_base"]))}
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


def phase_arms(c, smoke=False, row=None):
    return tuple(c["smoke_matrix"][row["dataset"]]) if smoke and row else ARMS


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
    pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="rq315-artifact")

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
