#!/usr/bin/env bash
# Offline full-input/output/attention/accounting review; no model calls.
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/runtime_environment_local.sh"
export CUDA_VISIBLE_DEVICES=''
exec "$rq45_python" -B - <<'PY'
import json,math,sqlite3,time,statistics
from collections import Counter
from RQs.RQ4_5.src.utils import RESULTS,ROOT,read,save,digest,score_response,score_qa
from RQs.RQ4_5.src.gates import review_smoke,execution_fingerprint
basic=review_smoke()
if basic['status']!='passed':raise RuntimeError(basic)
root=RESULTS/'smoke';queue=read(RESULTS/'frozen/smoke_queue.json')
summary=read(root/'summary.json');clock=read(root/'logical_clock.json')
if (len(queue),summary['completed'],summary['total'])!=(18,18,18):raise RuntimeError('Incomplete smoke')
images={};rows=[];attention=[];attempt_ids=set()
for entry in queue:
    item=entry['item'];record=read(root/'completed'/(item['key']+'.json'))
    request=read(root/record['request_path']);usage=record['usage']
    if request!=entry['request'] or record['request_hash']!=request['identity']:
        raise RuntimeError('Frozen/actual request identity differs')
    if record.get('actual_calls')!=1 or not isinstance(record['response'],str):
        raise RuntimeError('Eighteen real calls and complete raw answers required')
    if record['attempt_id'] in attempt_ids:raise RuntimeError('Duplicate call accounting')
    attempt_ids.add(record['attempt_id'])
    original=sum(math.prod(g)//4 for g in request['grid_thw']);kept=sum(map(len,request['retained_by_image']))
    if (usage['input_tokens'],usage['image_tokens_original'],usage['image_tokens_retained'])!=(request['input_tokens'],original,kept):
        raise RuntimeError('Actual token/gather accounting differs')
    if usage['input_tokens']+8192>40960 or usage['output_tokens']>8192:raise RuntimeError('Context overflow')
    if (usage['backend'],usage['dtype'],usage['branch_calls'],usage['engine_preemptions'])!=('vllm','bfloat16',0,0):
        raise RuntimeError('Native BF16 execution or KV admission failed')
    for image,sha in zip(request['images'],request['image_sha256'],strict=True):
        images.setdefault(image,digest(ROOT/image))
        if images[image]!=sha:raise RuntimeError('Model-visible PNG differs')
    for path,sha in record['artifact_hashes'].items():
        if digest(root/path)!=sha:raise RuntimeError('Conversation sidecar differs')
    context=read(root/'scoring'/(item['id']+'__'+request['task']+'.json'))
    scored=score_response(record['response'],context) if request['task']=='RCA' else score_qa(record['response'],context)
    if scored!=record['outcome']:raise RuntimeError('Offline score does not reproduce')
    if request.get('attention'):
        key=usage['attention_record_key'];path=root/'attention'/(key+'.json');a=read(path)
        if path.stat().st_size>65536 or a['layer']!=3 or a['sample_count']!=2:raise RuntimeError('Attention protocol differs')
        if usage['attention_error'] or usage['attention_missed']:raise RuntimeError('Attention capture failed')
        if a['query_definition']!='last_prompt_query_and_first_decode_query_separately':raise RuntimeError('Query scope differs')
        for masses in zip(a['text_mass'],a['image_mass'],a['other_mass'],strict=True):
            if not all(math.isfinite(x) and x>=0 for x in masses) or abs(sum(masses)-1)>1e-4:
                raise RuntimeError('Attention masses do not normalize')
        attention.append({'key':key,'bytes':path.stat().st_size,'sha256':digest(path),'record':a})
    rows.append({'key':item['key'],'task':request['task'],'images':len(request['images']),
        'prompt':request['prompt'],'raw_answer':record['response'],'outcome':record['outcome'],
        'input_tokens':usage['input_tokens'],'output_tokens':usage['output_tokens'],'stop_reason':usage['stop_reason'],
        'vision_seconds':usage['vision_seconds'],'cpu_seconds':record['preparation']['prepare_seconds']})
attempt=read(RESULTS/'qualification/smoke_activation.json')['attempt'];prefix=f'rq45_smoke_round{attempt:02}/'
with sqlite3.connect((RESULTS/'calls.sqlite').resolve().as_uri()+'?mode=ro&nolock=1',uri=True) as db:
    calls=list(db.execute('SELECT id,call_key,request_hash,state,started FROM calls WHERE substr(call_key,1,?)=?',(len(prefix),prefix)))
if len(calls)!=18 or {c[0] for c in calls}!=attempt_ids or any(c[3]!='complete' for c in calls):raise RuntimeError('Call ledger differs')
call_map={c[0]:c for c in calls}
for entry in queue:
    record=read(root/'completed'/(entry['item']['key']+'.json'));c=call_map[record['attempt_id']]
    if c[1:4]!=(prefix+entry['item']['key'],record['request_hash'],'complete'):raise RuntimeError('Wrong ledger scope')
first=min(c[4] for c in calls);end=clock['started_unix']+summary['seconds'];online=end-first
if online<=0:raise RuntimeError('Invalid clock')
report={'status':'checks_passed_manual_review_pending','execution_fingerprint':execution_fingerprint(),
 'completed_positions':18,'actual_completed_calls':18,'logical_seconds':summary['seconds'],
 'allocation_completed_calls_per_minute':1080/summary['seconds'],'online_completed_calls_per_minute':1080/online,
 'startup_to_first_reservation_seconds':first-clock['started_unix'],'online_seconds':online,
 'mean_vision_seconds':statistics.mean(r['vision_seconds'] for r in rows),
 'mean_cpu_seconds':statistics.mean(r['cpu_seconds'] for r in rows),'task_counts':dict(Counter(r['task'] for r in rows)),
 'verified_images':images,'records':rows,'attention':attention,'ranking_accuracy_is_not_a_gate':True,
 'manual_review':'Actual reading of each retained input, answer and measurement remains required',
 'reviewed_unix':time.time()}
save(RESULTS/'qualification/smoke_review_full.json',report)
print(json.dumps({k:v for k,v in report.items() if k not in {'records','attention','verified_images'}},indent=2))
PY
