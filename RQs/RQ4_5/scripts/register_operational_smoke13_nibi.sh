#!/usr/bin/env bash
# Prospectively register one operational native-SDPA smoke after preserved CPU input proof.
#SBATCH --account=def-jacobsen_cpu
#SBATCH --partition=cpubase_bycore_b1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --hint=nomultithread
#SBATCH --mem=8G
#SBATCH --time=00:10:00
#SBATCH --job-name=rq45-register-smoke
#SBATCH --no-requeue
set -euo pipefail
repo="${CANVASRCA_NIBI_REPO:-/home/lglsj/CanvasRCA_20261018}"
cd "$repo"
module load StdEnv/2023 python/3.11.5 cuda/12.9 arrow/18.1.0
export CANVASRCA_RQ45_ROOT=/project/def-jacobsen/canvasrca_cache/RQ4_5/cpu_v1
export CANVASRCA_RQ45_SOURCE_ROOT=/project/def-jacobsen/canvasrca_cache/RQ4_5/source_dependencies
export CANVASRCA_QWEN_MODEL=/scratch/lglsj/CanvasRCA/models/Qwen3.8-27B
export PYTHONPATH="$repo/src:$repo" PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export CANVASRCA_RQ45_PROFILE_ADAPTER=0
python_bin=/scratch/lglsj/CanvasRCA/.venv-inference/bin/python
"$python_bin" -B - <<'PY'
import fcntl,sqlite3,time
from RQs.RQ4_5.src.utils import RQ,RESULTS,read,save,stable,digest
from RQs.RQ4_5.src.gates import execution_fingerprint
q=RESULTS/'qualification';fp=execution_fingerprint();attempt=13
if (q/'smoke_submission_13.json').exists():raise RuntimeError('Round 13 is already submitted; never submit twice')
authority=read(RQ/'findings/smoke_goal_authority_20261019.json')
if not authority['additional_smoke_authorized'] or authority['maximum_calls_per_attempt']!=18:
    raise RuntimeError('Serial smoke authority is unavailable')
probe=read(q/'device_uuid_probe_v1.json')
if probe.get('canonical_equal') is not True or probe['model_calls']!=0:raise RuntimeError('Actual GPU identity probe not passed')
proof=read(q/'runtime_backend_revision.json');cpu=read(q/'cpu_complete.json')
if proof.get('purpose')!='platform_integration_only_not_scientific_reproduction':raise RuntimeError('Wrong validation purpose')
if proof['status']!='passed' or proof['execution_fingerprint']!=fp or cpu['execution_fingerprint']!=fp or cpu['status']!='passed':
    raise RuntimeError('Operational runtime revision is not source-matched')
static=read(RQ/'findings/static_check.json')
if static['status']!='passed' or static['source_fingerprint']!=fp:raise RuntimeError('Native revision static checks not passed')
if (q/'formal_activation.json').exists():raise RuntimeError('Formal activation remains outside this goal')
submissions=sorted(p for p in q.glob('smoke_submission_*.json') if __import__('re').fullmatch(r'smoke_submission_[0-9]{2}\.json',p.name))
if len(submissions)!=12:raise RuntimeError('Expected exactly twelve preserved prior rounds')
path=RESULTS/'calls.sqlite';budget=read(q/'call_budget_v2.json');limit=1682+18*attempt
with (path.parent/(path.name+'.owner.lock')).open('a') as owner:
    fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
    db=sqlite3.connect(path.resolve().as_uri()+'?nolock=1',uri=True)
    try:
        if db.execute('PRAGMA journal_mode').fetchone()[0]!='delete':raise RuntimeError('Unexpected ledger mode')
        db.execute('PRAGMA synchronous=FULL')
        before=list(db.execute('SELECT * FROM calls ORDER BY id'));spent=len(before)
        previous=db.execute("SELECT value FROM settings WHERE name='hard_limit'").fetchone()[0]
        if previous not in (budget['total_limit'],limit) or previous>limit:raise RuntimeError('Unreviewed ledger limit')
        save(q/'smoke_registration_13_inprogress.json',{'spent_calls':spent,'rows_sha256':stable(before),
            'previous_limit':previous,'new_limit':limit,'execution_fingerprint':fp})
        with db:db.execute("UPDATE settings SET value=? WHERE name='hard_limit'",(limit,))
        if list(db.execute('SELECT * FROM calls ORDER BY id'))!=before:raise RuntimeError('Spent rows changed')
        save(q/'call_budget_v2.json',dict(budget,schema='RQ45ReviewedCallBudgetV3',
            total_limit=limit,registered_smoke_rounds=attempt,per_smoke_round_limit=18,
            preserved_spent_calls=spent,no_call_counter_reset=True,
            authority='User resumes unlimited serial qualification until six completed calls/minute; round 13 validates a pre-compilation layer3 capture split, native compilation elsewhere, real allocated-GPU NVML sampling and BF16, not scientific equivalence'))
        save(q/'smoke_retry_authorization_13.json',{'authorized':True,'attempt':attempt,
            'execution_fingerprint':fp,'spent_calls_preserved':spent,'preserved_rows_sha256':stable(before),
            'reason':'Platform validation: native BF16 SDPA, old feature-reproduction gate failed and remains failed; unchanged CPU-qualified inputs',
            'maximum_new_calls':18,'maximum_seconds':900,'formal_authorized':False,
            'new_generation_recipe':True,'previous_answers_preserved_not_counted_as_new_throughput':True})
    finally:db.close()
manifest=read(RESULTS/'frozen/manifest.json');manifest['calls'].update(total=limit,registered_smoke_rounds=attempt)
save(RESULTS/'frozen/manifest.json',manifest)
(q/'smoke_registration_13_inprogress.json').unlink()
print({'round':attempt,'spent_calls_preserved':spent,'new_limit':limit,'rows_unchanged':True},flush=True)
PY
bash RQs/RQ4_5/scripts/submit_gpu_smoke_nibi.sh 13
