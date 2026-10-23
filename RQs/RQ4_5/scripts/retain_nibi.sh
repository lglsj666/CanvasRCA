#!/usr/bin/env bash
# Host-only artifact deployment/finalization. No renderer or model invocation.
set -euo pipefail
mode="${1:?prepare or finalize}"
[[ "$mode" == prepare || "$mode" == finalize ]] || exit 2
exec /scratch/lglsj/CanvasRCA/.venv-inference/bin/python -B - "$mode" <<'PY'
import sys,os,json,shutil,sqlite3,time,fcntl
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from RQs.RQ4_5.src.utils import RESULTS,SOURCE_ROOT,RQ,read,save,digest,roster,stable
from RQs.RQ4_5.src.gates import require_execution

mode=sys.argv[1]
target=Path('/project/def-jacobsen/canvasrca_exp/RQ4_5/exclusive_spatial_v1')
target.mkdir(parents=True,exist_ok=True)
lock=(target/'retention_owner.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)

def link(source,destination):
    source=Path(source);destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    sha=digest(source)
    if destination.exists():
        if digest(destination)!=sha:raise ValueError('Immutable retention collision: '+str(destination))
        return sha
    tmp=destination.with_name(destination.name+f'.{os.getpid()}.tmp')
    try:
        try:os.link(source,tmp)
        except OSError:shutil.copyfile(source,tmp)
        if digest(tmp)!=sha:raise ValueError('Retention copy differs')
        os.replace(tmp,destination)
    finally:
        if tmp.exists():tmp.unlink()
    return sha

def tree(source,destination):
    source=Path(source)
    pairs=[(p,Path(destination)/p.relative_to(source)) for p in source.rglob('*')
           if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith(('.lock','-wal','-shm'))]
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda pair:link(*pair),pairs))

def alias(name):
    source=RESULTS/name;destination=target/name;destination.mkdir(parents=True,exist_ok=True)
    if source.is_symlink():
        if source.resolve()!=destination.resolve():raise RuntimeError('Different permanent output root')
    elif source.exists():
        if any(source.iterdir()):raise RuntimeError('Do not relocate a live/nonempty output root')
        source.rmdir();source.symlink_to(destination,target_is_directory=True)
    else:source.symlink_to(destination,target_is_directory=True)

if mode=='prepare':
    require_execution('formal')
    manifest=read(RESULTS/'frozen/manifest.json');marker=target/'permanent_prepared.json'
    if marker.exists():
        if read(marker)['execution_fingerprint']!=manifest['execution_fingerprint']:raise RuntimeError('Permanent source mismatch')
        alias('formal');alias('analysis');print('Permanent inputs already prepared; no bulk restart audit.');sys.exit(0)
    # Ordinary content-addressed files, not archives. Retained paths resolve
    # independently of the disposable CPU preparation tree.
    tree(RESULTS/'objects',target/'objects')
    dependencies={str(RESULTS/'objects'/p.name):{'retained':str(p),'sha256':p.stem}
                  for p in (target/'objects').iterdir() if p.is_file()}
    save(target/'dependency_index.json',dependencies)
    tree(RESULTS/'frozen',target/'frozen')
    audit_transforms=[]
    for case in (RESULTS/'inputs').iterdir():
        for name in ('ownership.json','selections.json','source.json'):
            source=case/name;destination=target/'inputs'/case.name/name
            value=read(source);destination.parent.mkdir(parents=True,exist_ok=True)
            if destination.exists():
                if read(destination)!=value:raise ValueError('Audit object changed')
            else:
                destination.write_text(json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n')
            if read(destination)!=value:raise ValueError('Audit whitespace compaction lost information')
            audit_transforms.append({'path':str(destination.relative_to(target)),
                'original_sha256':digest(source),'retained_sha256':digest(destination),
                'model_input':False,'transformation':'ordinary JSON whitespace only; parsed object equality verified'})
    save(target/'audit_serialization.json',audit_transforms)
    for case in (RESULTS/'mechanism').iterdir():
        if (case/'answers_audit_only.json').exists():link(case/'answers_audit_only.json',target/'mechanism'/case.name/'answers_audit_only.json')
    for path in (RESULTS/'qualification').glob('*.json'):link(path,target/'qualification'/path.name)
    link(RESULTS/'historical_references.json',target/'historical_references.json')
    save(target/'roster.json',roster())
    # Minimal original metadata supports the existing offline analysis/scoring
    # interface without the staged historical telemetry/preparation checkout.
    history=Path('RQs/RQ4_1/results/comparison_coding_v1')
    index=read(SOURCE_ROOT/history/'deployment_v26/request_index.json')
    # The old 109-MB index redundantly embeds historical requests. Retain its
    # unchanged case metadata for future roster/scoring, with source provenance.
    save(target/'source_dependencies'/history/'deployment_v26/request_index.json',
        {'cases':index['cases'],'offline_metadata_only':True,
         'original_sha256':digest(SOURCE_ROOT/history/'deployment_v26/request_index.json')})
    relative=history/'cpu_admission_v4/event_group_audit.json'
    link(SOURCE_ROOT/relative,target/'source_dependencies'/relative)
    for row in index['cases'].values():
        private=Path(row['private'])
        if private.is_absolute():raise RuntimeError('Unregistered absolute private dependency')
        link(SOURCE_ROOT/private,target/'source_dependencies'/private)
    tree(RQ/'scripts',target/'frozen/deployment_scripts')
    alias('formal');alias('analysis')
    save(marker,{'status':'passed','execution_fingerprint':manifest['execution_fingerprint'],
        'frozen_queue_sha256':manifest['queue_sha256']['formal'],'objects':len(dependencies),
        'directly_readable':True,'input_pixels_prompts_and_generation_identities_unchanged':True})
    (target/'README.md').write_text('# RQ4.5 permanent records\n\nFormal answers and exact requests are written directly here. Immutable images, source/selection audits, frozen code and scoring metadata are ordinary hash-verified files. `dependency_index.json` resolves original host paths to permanent objects, without the temporary preparation tree.\n\nWith PYTHONPATH set to the repository and src, view a conversation using `CANVASRCA_RQ45_ROOT='+str(target)+' CANVASRCA_RQ45_SOURCE_ROOT='+str(target/'source_dependencies')+' python -m RQs.RQ4_5.src.main view --key KEY`. For analysis use the same roots and `python -m RQs.RQ4_5.src.main analyze`. Original outputs and scores are preserved.\n\nNon-model audit JSON only has whitespace compacted, with full parsed-object equality and both hashes recorded. Exact model prompts, pixels, responses and numerical strings are unchanged.\n\nFinalization verifies every actual input/output, scoring and attention reference, then audits unique bytes including residual experiment dependencies before dropping reproducible CPU caches. Completed markers are the resume boundary.\n')
    print('Permanent formal storage prepared:',target);sys.exit(0)

if (target/'finalization_complete.json').exists():
    print('Finalization already committed; no repeated full audit.');sys.exit(0)
root=target/'formal'
if not (root/'phase_complete.json').exists():raise RuntimeError('Formal calls/writers have not drained')
queue=read(target/'frozen/formal_queue.json');dependencies=read(target/'dependency_index.json')
verified={};actual=set();attention_bytes=0;attention_mapping_index={}
def verified_hash(path):
    path=Path(path)
    if str(path) not in verified:verified[str(path)]=digest(path)
    return verified[str(path)]
for entry in queue:
    item=entry['item'];record=read(root/'completed'/(item['key']+'.json'))
    request=read(root/record['request_path'])
    if request!=entry['request'] or record['request_hash']!=request['identity'] or not isinstance(record['response'],str):
        raise RuntimeError('Actual conversation differs from frozen input')
    if record['usage']['input_tokens']!=request['input_tokens']:raise RuntimeError('Actual input accounting differs')
    context=root/'scoring'/(item['id']+'__'+item['task']+'.json')
    if not context.exists():raise RuntimeError('Missing retained rescoring context')
    for image,sha in zip(request['images'],request['image_sha256'],strict=True):
        retained=dependencies[image]['retained']
        if verified_hash(retained)!=sha:raise RuntimeError('Permanent model-visible PNG differs')
    for relative,sha in record['artifact_hashes'].items():
        if verified_hash(root/relative)!=sha:raise RuntimeError('Conversation sidecar differs')
    if record.get('actual_calls',1):actual.add(('formal',record['attempt_id']))
    if request.get('attention') and record.get('actual_calls',1):
        key=record['usage'].get('attention_record_key')
        if not key or not (root/'attention'/(key+'.json')).exists():raise RuntimeError('Collected attention missing')
        if record['usage'].get('attention_error'):raise RuntimeError('Recorded attention failure')
        observed=read(root/'attention'/(key+'.json'))
        mapping={'geometry':request['geometry'],'retained_by_image':request['retained_by_image'],
            'grid_thw':request['grid_thw'],'query_policy':request['attention_query_policy'],
            'input_tokens':request['input_tokens'],'generation_identity':request['identity'],
            'actual_mapping_hash':observed['mapping_hash'],
            'definition':'Frozen attention_regions + actual processor; full IDs recoverable from exact prompt and images, not a full attention matrix'}
        mapping_id=stable(mapping);save(target/'attention_mappings'/(mapping_id+'.json'),mapping)
        attention_mapping_index[key]=mapping_id
if len(queue)!=1560:raise RuntimeError('Incomplete registered formal matrix')
save(target/'attention_mappings/index.json',attention_mapping_index)
# All actually collected smoke conversations/attention are small, retained as
# provenance; bulky reproducible CPU render/preparation materials stay outside.
for name in ('smoke','smoke_attempts'):
    source=RESULTS/name
    if source.exists():tree(source,target/'qualification'/name)
ledger_history=RESULTS/'qualification/history_ledger_v1'
if ledger_history.exists():tree(ledger_history,target/'qualification/history_ledger_v1')
for record_path in (target/'qualification').rglob('completed/*.json'):
    record=read(record_path)
    if record.get('actual_calls',1):actual.add((str(record_path.parent.parent),record['attempt_id']))
for path in (RESULTS/'qualification').glob('*.json'):
    destination=target/'qualification'/path.name
    if not destination.exists():link(path,destination)
# Slurm may append the finalizer's own final message after this audit. Snapshot
# system logs as ordinary files rather than hard-linking a still-open writer.
# Model conversations, answers and accounting above are already fully drained.
log_snapshots=[]
for path in (RESULTS/'logs').rglob('*'):
    if not path.is_file():continue
    body=path.read_bytes();destination=target/'logs'/path.relative_to(RESULTS/'logs')
    destination.parent.mkdir(parents=True,exist_ok=True)
    temporary=destination.with_name(destination.name+'.snapshot.tmp')
    with temporary.open('wb') as stream:
        stream.write(body);stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,destination)
    sha=__import__('hashlib').sha256(body).hexdigest()
    if digest(destination)!=sha:raise RuntimeError('System-log snapshot changed')
    log_snapshots.append({'path':str(destination.relative_to(target)),'sha256':sha,'bytes':len(body),
        'coverage':'system log snapshot before finalizer completion; complete model histories are retained separately'})
save(target/'system_log_snapshots.json',log_snapshots)
if (RESULTS/'calls.sqlite').exists():
    with sqlite3.connect((RESULTS/'calls.sqlite').resolve().as_uri()+'?mode=ro&nolock=1',uri=True) as source,sqlite3.connect((target/'calls.sqlite').resolve().as_uri()+'?nolock=1',uri=True) as destination:
        source.backup(destination)
        if destination.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise RuntimeError('Ledger backup integrity')
# Verify the complete retained graph before removing reproducible owned caches.
for path in target.rglob('*'):
    if path.is_file():verified_hash(path)
for name in ('cache','inputs','mechanism'):
    source=RESULTS/name
    if source.exists() and not source.is_symlink():shutil.rmtree(source)
for path in (RESULTS/'qualification').glob('history_v*'):
    if path.is_dir():shutil.rmtree(path)
# Count unique inodes across permanent data and remaining owned dependencies.
# A hardlink or move does not artificially reduce the accounted footprint.
roots=[target,RESULTS,SOURCE_ROOT];inodes={};attention_inodes={};files=[]
for base in roots:
    for path in base.rglob('*'):
        if not path.is_file() or path.name in {'retention.json','finalization_complete.json'}:continue
        stat=path.stat();key=(stat.st_dev,stat.st_ino);inodes[key]=stat.st_size
        if 'attention' in path.parts or 'attention_mappings' in path.parts:attention_inodes[key]=stat.st_size
        if path.is_relative_to(target):files.append({'path':str(path.relative_to(target)),'sha256':verified_hash(path),'bytes':stat.st_size})
base_bytes=sum(inodes.values());attention_bytes=sum(attention_inodes.values())
report={'schema':'RQ45PermanentRetentionV1','status':'pending','actual_completed_calls':len(actual),
    'accounted_roots':list(map(str,roots)),'files':files,'attention_bytes':attention_bytes,
    'limit_bytes':2500000*len(actual),'attention_limit_bytes':100000*len(actual),'directly_readable':True}
for _ in range(8):
    save(target/'retention.json',report)
    total=base_bytes+(target/'retention.json').stat().st_size+1024
    status='passed' if total<=report['limit_bytes'] and attention_bytes<=report['attention_limit_bytes'] else 'failed'
    if report.get('retained_bytes')==total and report['status']==status:break
    report.update(retained_bytes=total,status=status)
if report['status']!='passed':raise RuntimeError('Permanent retention budget failed; unique inputs/outputs are preserved')
save(target/'finalization_complete.json',{'status':'passed','positions':len(queue),'retention_sha256':digest(target/'retention.json'),'completed_unix':time.time()})
print('All formal conversations and permanent retention verified:',target)
PY
