"""Fresh RQ3.18 identities; lifecycle primitives inherited from protected RQ3.16."""
from pathlib import Path
from contextlib import contextmanager
import json
import os
from unified_scripts import stable_hash
from vlmrca.run_state import read_json, write_json, sha_file, atomic_write
from RQs.RQ3_8.src.utils import exclusive, immutable_json
ROOT = Path(__file__).resolve().parents[3]
VERSION = 'rq318_population_readout_v1'
MODEL = 'qwen3.8-27b'
ARMS = ('PAIR_TEXT', 'READOUT_TEXT', 'SAMPLE_VISUAL', 'READOUT_SAMPLE', 'PROFILE_VISUAL', 'READOUT_PROFILE', 'PROFILE_MARKLESS', 'READOUT_MARKLESS', 'PAIR_TEXT_REPEAT', 'READOUT_TEXT_REPEAT', 'READOUT_PROFILE_REPEAT')
METRICS = ('mrr','ac@1','ac@3','ac@5','avg@3','avg@5')

def config():
    c=read_json(ROOT/'RQs/RQ3_18/configs/population_readout_v1.json')
    assert c['version']==VERSION and tuple(c['arms'])==ARMS and c['model']==MODEL
    assert c['case_counts']=={'aiops2022':60,'aiops2025':60,'aegislab':100}
    assert (c['formal_positions'],c['formal_attempt_limit'],c['smoke_attempt_limit'],c['total_attempt_limit'])==(2420,2482,18,2500)
    assert (c['workers'],c['concurrency'],c['max_tokens'],c['smoke_seconds'])==(8,36,8192,600)
    assert c['current_execution_boundary']=='static_cpu_then_stop'
    assert c['full_launch_authorized'] is False and c['smoke_launch_authorized'] is False
    assert len(c['primary_contrasts'])==4 and len(c['secondary_contrasts'])==14 and len(c['secondary_interactions'])==3
    assert sum(map(len,c['smoke_matrix'].values()))==18 and set(sum(c['smoke_matrix'].values(),[]))==set(ARMS)
    return c


def source_contract():
    """Source closure including relative imports; no module evaluation or GPU IO."""
    import ast
    from renderer.gates import source_fingerprint
    names=set()
    for folder in ('src','configs','scripts','descriptions'):
        names.update(p for p in (ROOT/'RQs/RQ3_18'/folder).glob('*') if p.suffix in {'.py','.json','.sh','.md'})
    renderer=source_fingerprint()
    names.update(ROOT/'src/renderer'/n for n in renderer['files'])
    names.update(ROOT/n for n in ('src/renderer/web/dist/render.mjs','src/renderer/web/assets/DejaVuSans.ttf',
        'configs/vllm_inference.yaml','configs/vllm_inference_local.yaml','configs/dataset_segmentation.yaml','configs/rca_scorer.yaml',
        'scripts/env_local.sh','scripts/env.sh','scripts/vllm_vlm/serve_canvasrca_local.sh',
        'RQs/RQ3_16/configs/marginal_coverage_v1.json','RQs/RQ3_15/configs/request_joint_v1.json',
        'RQs/RQ3_16/results/marginal_coverage_v1/qualification/cpu.json',
        'RQs/RQ3_15/results/request_joint_v1/qualification/cpu.json',
        'RQs/RQ3_11/results/protected_v2/analysis_reviewed_v1/checkpoint_verification.json',
        'docs/experiment_plans/RQ3_18_Population_Readout_Plan_2026-10-04.md'))
    profile=ROOT/'RQs/RQ3_18/results/population_readout_v1/runtime/qwen_local.yaml'
    if profile.exists(): names.add(profile)
    pending=list(names)
    while pending:
        file=pending.pop()
        if file.suffix!='.py': continue
        for node in ast.walk(ast.parse(file.read_text())):
            modules=[]
            if isinstance(node,ast.Import): modules=[a.name for a in node.names]
            elif isinstance(node,ast.ImportFrom):
                if node.level:
                    base=file.parent
                    for _ in range(node.level-1): base=base.parent
                    base=base.joinpath(*(node.module or '').split('.'))
                else:
                    name=node.module or ''
                    if not name.startswith(('RQs.','renderer.','vlmrca.','unified_scripts')): continue
                    base=(ROOT if name.startswith('RQs.') else ROOT/'src').joinpath(*name.split('.'))
                modules=[base]+[base/a.name for a in node.names]
            for mod in modules:
                if isinstance(mod,str):
                    if not mod.startswith(('RQs.','renderer.','vlmrca.','unified_scripts')): continue
                    mod=(ROOT if mod.startswith('RQs.') else ROOT/'src').joinpath(*mod.split('.'))
                p=mod.with_suffix('.py') if mod.with_suffix('.py').is_file() else mod/'__init__.py'
                if p.is_file() and p not in names: names.add(p);pending.append(p)
    return {'version':VERSION,'files':{str(p.relative_to(ROOT)):sha_file(p) for p in sorted(names)},'renderer':renderer}

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
    profile["status"] = "rq318_qwen_only_local_adapter"
    profile["rq318_adapter"] = {"version": VERSION, "source_sha256": sha_file(path(c["inference_base"]))}
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
    pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="rq318-artifact")

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
