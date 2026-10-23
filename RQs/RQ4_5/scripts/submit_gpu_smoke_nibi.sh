#!/usr/bin/env bash
# Submit one reviewed round; the user permits serial rounds until a clean pass.
set -euo pipefail
round="${1:-1}"
repo="${CANVASRCA_NIBI_REPO:-/home/lglsj/CanvasRCA_20261018}"
cd "$repo"
export CANVASRCA_RQ45_ROOT=/project/def-jacobsen/canvasrca_cache/RQ4_5/cpu_v1
export CANVASRCA_RQ45_SOURCE_ROOT=/project/def-jacobsen/canvasrca_cache/RQ4_5/source_dependencies
export CANVASRCA_QWEN_MODEL=/scratch/lglsj/CanvasRCA/models/Qwen3.8-27B
export PYTHONPATH="$repo/src:$repo" PYTHONDONTWRITEBYTECODE=1
python_bin=/scratch/lglsj/CanvasRCA/.venv-inference/bin/python
"$python_bin" -B - "$round" <<'PY'
from RQs.RQ4_5.src.utils import RESULTS,RQ,read,save,digest
from RQs.RQ4_5.src.gates import execution_fingerprint,require_execution
import sqlite3,time,sys,subprocess,shutil
attempt=int(sys.argv[1])
if attempt<1:raise ValueError('Positive smoke round required')
authority=read(RQ/'findings/smoke_goal_authority_20261019.json')
if authority.get('additional_smoke_authorized') is False:
    raise RuntimeError('The user closes additional smoke rounds; preserve existing outputs without new calls')
fp=execution_fingerprint()
cpu=read(RESULTS/'qualification/cpu_complete.json')
if cpu['status']!='passed' or cpu['execution_fingerprint']!=fp:
    raise RuntimeError('Current source has no complete CPU qualification')
if (RESULTS/'qualification/formal_activation.json').exists():
    raise RuntimeError('Formal activation is outside this smoke-only authorization')
if (RESULTS/'qualification'/f'smoke_submission_{attempt:02}.json').exists():
    raise RuntimeError('This round is already registered')
previous=sorted((RESULTS/'qualification').glob('smoke_submission_*.json'))
if attempt!=len(previous)+1:raise RuntimeError('Smoke rounds must be registered in sequence')
live=subprocess.run(['squeue','--me','-h','-o','%i %T'],capture_output=True,text=True,check=True).stdout.splitlines()
live={line.split()[0]:line.split()[1] for line in live if line.strip()}
for record in previous:
    job=read(record)['job_id'].split(';')[0]
    state=live.get(job,'')
    if state:raise RuntimeError('Prior smoke allocation is still live: '+job+' '+state)
    states=subprocess.run(['sacct','-n','-P','-j',job,'--format=JobIDRaw,State%32,ExitCode'],capture_output=True,text=True,check=True).stdout.splitlines()
    status=next((line.split('|')[1:3] for line in states if line.split('|')[0]==job),None)
    terminal=status[0].split()[0] if status else None
    if terminal not in {'COMPLETED','FAILED','CANCELLED','TIMEOUT','OUT_OF_MEMORY','NODE_FAIL'}:
        raise RuntimeError('Prior allocation has no verified terminal accounting: '+job)
    save(RESULTS/'qualification'/f'smoke_job_{job}_terminal.json',{'job_id':job,'state':status[0],'exit_code':status[1],'verified_unix':time.time()})
if (RESULTS/'calls.sqlite').exists():
    with sqlite3.connect('file:'+str(RESULTS/'calls.sqlite')+'?mode=ro&nolock=1',uri=True) as db:
        spent=db.execute('SELECT COUNT(*) FROM calls').fetchone()[0]
    if spent:
        proof=read(RESULTS/'qualification'/f'smoke_retry_authorization_{attempt:02}.json')
        if not proof.get('authorized') or proof['execution_fingerprint']!=fp or proof['spent_calls_preserved']!=spent:
            raise RuntimeError('Existing spent calls require an exact reviewed repair supplement')
    budget=read(RESULTS/'qualification/call_budget_v2.json')
    if budget['registered_smoke_rounds']<attempt:raise RuntimeError('Register the additional round without resetting spent calls')
continuation_path=RESULTS/'qualification'/f'smoke_continuation_{attempt:02}.json'
continuation=read(continuation_path) if continuation_path.exists() else None
if (RESULTS/'smoke').exists():
    # A distinct attempt retains the original clock and all evidence. Spent
    # rounds additionally require the reviewed source-bound supplement above.
    last=read(previous[-1]);number=last['attempt']
    archive=RESULTS/'smoke_attempts'/f'round_{number:02}'
    if archive.exists():raise RuntimeError('Round archive already exists')
    if (RESULTS/'smoke/phase_complete.json').exists():raise RuntimeError('Completed smoke must be reviewed, not rerun')
    archive.parent.mkdir(parents=True,exist_ok=True)
    if continuation:
        if not continuation.get('authorized') or continuation['execution_fingerprint']!=fp:
            raise RuntimeError('Continuation authorization does not match current source')
        committed={p.name:digest(p) for p in (RESULTS/'smoke/completed').glob('*.json')}
        if committed!=continuation['preserved_completed_sha256']:
            raise RuntimeError('Previously committed smoke answers changed')
        # Snapshot the failed attempt without copying immutable response bytes.
        # Existing five commits stay at their original paths and are skipped.
        shutil.copytree(RESULTS/'smoke',archive,copy_function=__import__('os').link)
        for name in ('logical_clock.json','progress.json','summary.json','PAUSE'):
            path=RESULTS/'smoke'/name
            if path.exists():path.unlink()
    else:
        (RESULTS/'smoke').rename(archive)
    activation=RESULTS/'qualification/smoke_activation.json'
    if activation.exists():shutil.copyfile(activation,archive/'activation.json')
    save(archive/'archive_receipt.json',{'round':number,'job_id':last['job_id'],
        'archived_unix':time.time(),'global_spent_calls_preserved':spent if 'spent' in globals() else 0,
        'clock_preserved':True,'ledger_counters_reset':False})
authority=read(RQ/'findings/smoke_goal_authority_20261019.json')
assert authority['maximum_calls_per_attempt']==18
if authority['maximum_attempts'] is not None and attempt>authority['maximum_attempts']:
    raise RuntimeError('Smoke round allowance exhausted')
if authority['maximum_seconds_per_attempt']!=read(RQ/'configs/protocol_v1.json')['smoke_seconds']:
    raise RuntimeError('Smoke time authority and registered runtime disagree')
cache=read(__import__('pathlib').Path('/project/def-jacobsen/canvasrca_cache/shared/flashinfer/rq45_precompiled_manifest.json'))
if cache['status']!='passed' or digest(__import__('pathlib').Path(cache['published_binary']))!=cache['native_binary_sha256'] or digest(__import__('pathlib').Path(cache['provider_path'])/'flashinfer_jit_cache/__init__.py')!=cache['provider_sha256']:
    raise RuntimeError('Same-kernel precompiled cache has not been verified')
save(RESULTS/'qualification/precompiled_kernel.json',cache)
save(RESULTS/'qualification/smoke_goal_authority_20261019.json',authority)
save(RESULTS/'qualification/smoke_activation.json',{'authorized':True,
    'execution_fingerprint':fp,'scope':'smoke','attempt':attempt,'unix':time.time(),
    'maximum_calls':18,'maximum_seconds':authority['maximum_seconds_per_attempt'],'formal_authorized':False,
    'continuation':continuation,
    'authority':str(RESULTS/'qualification/smoke_goal_authority_20261019.json'),
    'launcher_sha256':digest(RQ/'scripts/gpu_smoke_nibi.sbatch'),
    'runtime_loader_sha256':digest(RQ/'scripts/runtime_environment_nibi.sh'),
    'precompiled_kernel_manifest_sha256':digest(RESULTS/'qualification/precompiled_kernel.json')})
require_execution('smoke')
print('Source-matched smoke activated; formal remains disabled:',fp,flush=True)
PY
mkdir -p "$CANVASRCA_RQ45_ROOT/logs"
dependency=()
if [[ -n "${CANVASRCA_RQ45_BUILD_JOB:-}" ]]; then dependency=(--dependency="afterok:$CANVASRCA_RQ45_BUILD_JOB"); fi
job=$(sbatch --parsable "${dependency[@]}" --output="$CANVASRCA_RQ45_ROOT/logs/smoke${round}_%j.out" \
  --error="$CANVASRCA_RQ45_ROOT/logs/smoke${round}_%j.err" RQs/RQ4_5/scripts/gpu_smoke_nibi.sbatch)
"$python_bin" -B - "$job" "$round" <<'PY'
import sys,time
from RQs.RQ4_5.src.utils import RESULTS,RQ,read,save
attempt=int(sys.argv[2])
limit=read(RQ/'findings/smoke_goal_authority_20261019.json')['maximum_seconds_per_attempt']
save(RESULTS/'qualification'/f'smoke_submission_{attempt:02}.json',{'job_id':sys.argv[1],
    'attempt':attempt,'submitted_unix':time.time(),'calls_limit':18,'seconds_limit':limit,
    'gpu':'h100:1','cpus':8,'memory':'96G','formal_authorized':False})
print('RQ4.5 GPU smoke job:',sys.argv[1],flush=True)
PY
