#!/usr/bin/env bash
# Inspect the actual saved round. This never sends a model request.
set -euo pipefail
repo="${CANVASRCA_NIBI_REPO:-/home/lglsj/CanvasRCA_20261018}"
cd "$repo"
export CANVASRCA_RQ45_ROOT=/project/def-jacobsen/canvasrca_cache/RQ4_5/cpu_v1
export CANVASRCA_RQ45_SOURCE_ROOT=/project/def-jacobsen/canvasrca_cache/RQ4_5/source_dependencies
export CANVASRCA_QWEN_MODEL=/scratch/lglsj/CanvasRCA/models/Qwen3.8-27B
export PYTHONPATH="$repo/src:$repo" PYTHONDONTWRITEBYTECODE=1
exec /scratch/lglsj/CanvasRCA/.venv-inference/bin/python -B - <<'PY'
import json,math,sqlite3,time
from RQs.RQ4_5.src.utils import RESULTS,ROOT,read,save,digest,score_response,score_qa
from RQs.RQ4_5.src.gates import review_smoke,execution_fingerprint

basic=review_smoke()
if basic['status']!='passed':raise RuntimeError(basic)
root=RESULTS/'smoke';queue=read(RESULTS/'frozen/smoke_queue.json')
summary=read(root/'summary.json');seen_images={};rows=[];attention=[]
if len(queue)!=18 or summary['completed']!=18 or summary['total']!=18:
    raise RuntimeError('Incomplete actual smoke')
for entry in queue:
    item=entry['item'];record=read(root/'completed'/(item['key']+'.json'))
    request=read(root/record['request_path']);usage=record['usage']
    if request!=entry['request'] or record['request_hash']!=request['identity']:
        raise RuntimeError('Frozen/actual request identity differs')
    if record.get('actual_calls')!=1 or not isinstance(record['response'],str):
        raise RuntimeError('Smoke requires real independent calls and retained raw answers')
    original=sum(math.prod(g)//4 for g in request['grid_thw'])
    kept=sum(map(len,request['retained_by_image']))
    if usage['input_tokens']!=request['input_tokens'] or usage['image_tokens_original']!=original or usage['image_tokens_retained']!=kept:
        raise RuntimeError('Actual input/image accounting differs')
    if usage['input_tokens']+8192>40960 or usage['output_tokens']>8192:
        raise RuntimeError('Registered context/output limit exceeded')
    if usage['backend']!='vllm' or usage['dtype']!='bfloat16' or usage['branch_calls']!=0 or usage['engine_preemptions']!=0:
        raise RuntimeError('Registered native/gather execution contract differs')
    for image,sha in zip(request['images'],request['image_sha256'],strict=True):
        seen_images.setdefault(image,digest(ROOT/image))
        if seen_images[image]!=sha:raise RuntimeError('Actual model-visible PNG differs')
    for path,sha in record['artifact_hashes'].items():
        if digest(root/path)!=sha:raise RuntimeError('Actual conversation sidecar differs')
    context=read(root/'scoring'/(item['id']+'__'+request['task']+'.json'))
    outcome=score_response(record['response'],context) if request['task']=='RCA' else score_qa(record['response'],context)
    if outcome!=record['outcome']:raise RuntimeError('Offline score does not reproduce')
    if request.get('attention'):
        key=usage['attention_record_key'];path=root/'attention'/(key+'.json');a=read(path)
        if path.stat().st_size>65536 or a['layer']!=3 or a['sample_count']!=2:
            raise RuntimeError('Attention layer/query/storage coverage differs')
        if usage['attention_error'] or usage['attention_missed']:
            raise RuntimeError('Attention collection failed')
        if a['query_definition']!='last_prompt_query_and_first_decode_query_separately':
            raise RuntimeError('Unexpected query coverage')
        for masses in zip(a['text_mass'],a['image_mass'],a['other_mass'],strict=True):
            if not all(math.isfinite(x) and x>=0 for x in masses) or abs(sum(masses)-1)>1e-4:
                raise RuntimeError('Attention mass does not normalize')
        attention.append({'key':key,'sha256':digest(path),'bytes':path.stat().st_size,'record':a})
    rows.append({'key':item['key'],'task':request['task'],'images':len(request['images']),
        'input_tokens':usage['input_tokens'],'output_tokens':usage['output_tokens'],
        'stop_reason':usage['stop_reason'],'raw_answer':record['response'],'outcome':record['outcome']})
activation=read(RESULTS/'qualification/smoke_activation.json');attempt=activation['attempt']
continuation=activation.get('continuation') or {}
preserved=continuation.get('preserved_completed_sha256',{})
for name,sha in preserved.items():
    if digest(root/'completed'/name)!=sha:raise RuntimeError('Previously committed smoke answer changed')
prefix='rq45_smoke_round'+str(attempt).zfill(2)+'/'
with sqlite3.connect('file:'+str(RESULTS/'calls.sqlite')+'?mode=ro&nolock=1',uri=True) as db:
    total_spent=db.execute('SELECT COUNT(*) FROM calls').fetchone()[0]
    counts=db.execute('SELECT COUNT(*) FROM calls WHERE substr(call_key,1,?)=?',(len(prefix),prefix)).fetchone()[0]
    for entry in queue:
        record=read(root/'completed'/(entry['item']['key']+'.json'))
        call=db.execute('SELECT call_key,request_hash,state FROM calls WHERE id=?',(record['attempt_id'],)).fetchone()
        name=entry['item']['key']+'.json'
        expected_scope=prefix
        if name in preserved:
            expected_scope=continuation.get('preserved_original_scopes',{}).get(name,
                'rq45_smoke_round'+str(continuation['prior_attempt']).zfill(2)+'/')
        if call!=(expected_scope+entry['item']['key'],record['request_hash'],'complete'):
            raise RuntimeError('Committed answer does not match its real original ledger call')
if counts!=18-len(preserved):raise RuntimeError('Unexpected initiated calls: '+str(counts))
result={'status':'checks_passed_manual_review_pending','execution_fingerprint':execution_fingerprint(),
    'completed_positions':len(rows),'initiated_calls_this_continuation':counts,'preserved_prior_answers':len(preserved),
    'initiated_calls':counts+len(preserved),'logical_seconds_this_continuation':summary['seconds'],
    'global_initiated_calls_including_previous_failed_rounds':total_spent,'smoke_round':attempt,
    'verified_images':seen_images,'records':rows,'attention':attention,
    'ranking_accuracy_is_not_a_gate':True,'reviewed_unix':time.time(),
    'operator_review_required':'Read all actual raw answers, inputs/PNG identities, scores and attention coverage before setting status passed'}
save(RESULTS/'qualification/smoke_review_full.json',result)
print(json.dumps(result,ensure_ascii=False,indent=2))
PY
