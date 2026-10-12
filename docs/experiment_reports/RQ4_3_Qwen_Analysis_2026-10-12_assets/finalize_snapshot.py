"""Upgrade the offline report manifest to the complete, drained formal queue."""
import csv,hashlib,json
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

B=Path(__file__).resolve().parent;ROOT=Path.cwd()
read=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
save=lambda p,v:Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
oldpath=B/'snapshot_previous_cutoff.json'
if not oldpath.exists():oldpath.write_bytes((B/'snapshot.json').read_bytes())
old=read(oldpath);qpath=ROOT/old['queue_path'];queue=read(qpath)
run=ROOT/'RQs/RQ4_3/results/formal_v7';phase=read(run/'phase_complete.json');progress=read(run/'progress.json')
assert phase['status']=='complete' and phase['writers_drained']
assert phase['positions']==progress['completed']==progress['total']==len(queue['items'])==4832
assert sha(qpath)==phase['queue_sha256']==old['queue_sha256']
before={r['key']:r for r in old['items']};now=[];added=[];counts=Counter();actual=refs=0
for item in sorted(queue['items'],key=lambda r:r['key']):
    key=item['key'];p=run/'execution/completed'/f'{key}.json';d=read(p);digest=sha(p)
    assert d['request_hash']==item['identity'],key
    if key in before:assert digest==before[key]['sha256'],('changed prior committed result',key)
    else:
        assert item['variant']=='BASE' and item['task']=='RCA'
        assert not d['usage'].get('attention_requested'),key
        added.append(key);counts[item['arm']]+=1
    actual+=int(d['actual_calls']);refs+=int(d['actual_calls']==0)
    now.append({'key':key,'path':str(p.relative_to(ROOT)),'sha256':digest})
expected={'R_PATCH_PACK':37,'R_HORIZON':42,'R_PACK_HORIZON':30,'C_PACK_OFFSET':34,'C_READ_GUIDE':32,'C_PACK_BG_FILL':34,'X_SR':42,'X_RP':38}
assert dict(counts)==expected,(counts,expected)
assert actual==4637 and refs==195 and len(added)==289
if not (B/'main_summary_previous_cutoff.csv').exists():(B/'main_summary_previous_cutoff.csv').write_bytes((B/'main_summary.csv').read_bytes())
unchanged_names=['qa_tolerant_summary.csv','qa_tolerant_calls.csv','qa_rca_linked.csv','qa_linked_manual_sample.json',
 'qa_manual_review.md','attention_regions.csv','attention_summary.csv','attention_records.csv','attention_integrity.json','same_backend_order_summary.json']
proof={'status':'complete','prior_positions':len(before),'final_positions':len(now),'added_positions':len(added),
 'added_by_arm':dict(sorted(counts.items())),'actual_completed_calls':actual,'references':refs,
 'existing_result_hash_changes':0,'new_QA_or_attention_calls':0,'new_model_calls_for_analysis':0,
 'unchanged_analysis_artifact_hashes':{name:sha(B/name) for name in unchanged_names},
 'phase_complete_path':str((run/'phase_complete.json').relative_to(ROOT)),'phase_complete_sha256':sha(run/'phase_complete.json')}
save(B/'final_update.json',proof)
final={**old,'schema':'RQ43FinalAnalysisSnapshotV2','cutoff_local':datetime.now(ZoneInfo('America/Toronto')).isoformat(),
 'status':'complete_formal_queue_writers_drained','positions':len(now),'calls_snapshot':phase['calls'],
 'items':now,'run_status':progress,'progress_snapshot':progress,'prior_snapshot':'snapshot_previous_cutoff.json',
 'phase_complete':proof['phase_complete_path'],'phase_complete_sha256':proof['phase_complete_sha256']}
save(B/'snapshot.json',final)
print(json.dumps({k:v for k,v in proof.items() if k!='unchanged_analysis_artifact_hashes'},indent=2))
