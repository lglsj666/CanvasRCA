"""Fresh RQ3.21 identities; lifecycle primitives inherited from protected RQ3.16."""
from pathlib import Path
from contextlib import contextmanager
from contextvars import ContextVar
import json
import os
from unified_scripts import stable_hash
from vlmrca.run_state import read_json, write_json, sha_file, atomic_write
from RQs.RQ3_8.src.utils import exclusive, immutable_json
ROOT = Path(__file__).resolve().parents[3]
VERSION = 'rq321_compact_entity_v1'
MODEL = 'qwen3.8-27b'
ARMS = ('ANCHOR_VISUAL', 'RAW_TEXT', 'RAW_VISUAL', 'PACK_VISUAL', 'ENTITY_VISUAL', 'PACK_ENTITY_TEXT', 'PACK_ENTITY_VISUAL', 'PACK_ENTITY_TEXT_REPEAT', 'PACK_ENTITY_VISUAL_REPEAT', 'QA_RAW_TEXT', 'QA_RAW_VISUAL', 'QA_PACK_ENTITY_TEXT', 'QA_PACK_ENTITY_VISUAL', 'ROTATE_TEXT', 'ROTATE_VISUAL')
METRICS = ('mrr','ac@1','ac@3','ac@5','avg@3','avg@5')
OUTPUT_LIMIT = ContextVar('rq321_output_limit', default=8192)

def config():
    c=read_json(ROOT/'RQs/RQ3_21/configs/compact_entity_v1.json')
    assert c['version']==VERSION and tuple(c['arms'])==ARMS and c['model']==MODEL
    assert c['case_counts']=={'aiops2022':60,'aiops2025':60,'aegislab':100}
    assert (c['formal_positions'],c['formal_attempt_limit'],c['smoke_attempt_limit'],c['total_attempt_limit'])==(2020,1922,18,1940)
    assert (c['workers'],c['concurrency'],c['max_tokens'],c['smoke_seconds'])==(8,36,8192,600)
    assert c['full_launch_authorized'] is False and c['smoke_launch_authorized'] is False
    assert len(c['primary_contrasts'])==2 and len(c['qa_contrasts'])==2
    assert sum(map(len,c['smoke_matrix'].values()))==18 and set(sum(c['smoke_matrix'].values(),[]))==set(ARMS)-{'ANCHOR_VISUAL'}
    return c


def source_contract():
    """Source closure including relative imports; no module evaluation or GPU IO."""
    import ast
    from renderer.gates import source_fingerprint
    names=set()
    for folder in ('src','configs','scripts','descriptions'):
        names.update(p for p in (ROOT/'RQs/RQ3_21'/folder).glob('*') if p.suffix in {'.py','.json','.sh','.md'})
    names.update((ROOT/'docs/experiment_plans/RQ3_21_Compact_Evidence_Entity_Organization_Plan_2026-10-06_assets').glob('*.md'))
    names.update((ROOT/'docs/experiment_plans/RQ3_21_Compact_Evidence_Entity_Organization_Plan_2026-10-06_assets').glob('*.json'))
    renderer=source_fingerprint()
    names.update(ROOT/'src/renderer'/n for n in renderer['files'])
    names.update(ROOT/n for n in ('src/renderer/web/dist/render.mjs','src/renderer/web/assets/DejaVuSans.ttf',
        'configs/vllm_inference.yaml','configs/vllm_inference_local.yaml','configs/dataset_segmentation.yaml','configs/rca_scorer.yaml',
        'scripts/env_local.sh','scripts/env.sh','scripts/vllm_vlm/serve_canvasrca_local.sh',
        'RQs/RQ3_16/configs/marginal_coverage_v1.json','RQs/RQ3_15/configs/request_joint_v1.json',
        'RQs/RQ3_16/results/marginal_coverage_v1/qualification/cpu.json',
        'RQs/RQ3_15/results/request_joint_v1/qualification/cpu.json',
        'RQs/RQ3_11/results/protected_v2/analysis_reviewed_v1/checkpoint_verification.json',
        'RQs/RQ3_18/configs/population_readout_v1.json',
        'docs/experiment_plans/RQ3_21_Compact_Evidence_Entity_Organization_Plan_2026-10-06.md',
        'RQs/RQ3_21/results/compact_entity_v1/qualification/history_protection.json'))
    profile=ROOT/'RQs/RQ3_21/results/compact_entity_v1/runtime/qwen_local.yaml'
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
    eligible=rows; excluded=[]  # Fixed mechanism sample does not filter by public availability or outcomes.
    selected=[]
    for dataset in c['case_counts']:
        ordered=sorted((r for r in eligible if r['dataset']==dataset),
            key=lambda r:stable_hash([c['qa_salt'],r['opaque_incident_id']]))
        unique=[]; repeated=[];seen=set()
        for r in ordered:
            group=parent['groups'].get(r['opaque_incident_id'],r['leakage_group'])
            (repeated if group in seen else unique).append(r);seen.add(group)
        chosen=(unique+repeated)[:c['qa_per_dataset']]
        if len(chosen)!=c['qa_per_dataset']: raise ValueError('Insufficient outcome-blind QA cases')
        selected.extend(r['opaque_incident_id'] for r in chosen)
    reg={"version":VERSION,"config_hash":stable_hash(c),"cases":rows,"smoke":parent["smoke"],
         'qa_cases':selected,'repeat_cases':selected,'qa_public_ineligible':excluded,
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
    profile["status"] = "rq321_qwen_only_local_adapter"
    profile["rq321_adapter"] = {"version": VERSION, "source_sha256": sha_file(path(c["inference_base"]))}
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
    if v.get("historical_reference"):
        receipt=root/"historical_commits"/(logical_key(oid,arm)+".json")
        if not receipt.exists():return None
        committed=read_json(receipt)
        if committed!={'status':'complete','reference_hash':stable_hash(v)}:
            raise ValueError('Historical reference commit mismatch')
        return v
    if v["status"]=="done" and not (root/"completed"/(v["call_key"]+".json")).exists():
        return None  # Missing atomic commit remains incomplete; no bulk audit.
    return v

def phase_arms(c, smoke=False, row=None):
    if row is None:return ARMS
    if smoke:return tuple(c['smoke_matrix'][row['dataset']])
    return ARMS if row['opaque_incident_id'] in register(c)['qa_cases'] else ARMS[:7]

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
    from vlmrca.vlm import configs as model_configs
    original_writer, original_call = parent.AsyncWriter, client.call_vlm
    original_config=model_configs.get_config
    pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="rq321-artifact")

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

    def configured(*args,**kwargs):
        kwargs['max_tokens']=OUTPUT_LIMIT.get()
        return original_config(*args,**kwargs)

    parent.AsyncWriter, client.call_vlm = PooledWriter, stream_call
    model_configs.get_config=configured
    try:
        yield
    finally:
        pool.shutdown(wait=True)
        parent.AsyncWriter, client.call_vlm = original_writer, original_call
        model_configs.get_config=original_config
