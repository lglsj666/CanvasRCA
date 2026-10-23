#!/usr/bin/env bash
#SBATCH --account=def-jacobsen_cpu
#SBATCH --partition=cpubase_bycore_b1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --hint=nomultithread
#SBATCH --mem=8G
#SBATCH --time=00:10:00
#SBATCH --job-name=rq45-register-smoke12
#SBATCH --no-requeue
set -euo pipefail
repo=/home/lglsj/CanvasRCA_20261018
cd "$repo"
source RQs/RQ4_5/scripts/runtime_environment_nibi.sh
bash RQs/RQ4_5/scripts/register_operational_smoke12_nibi.sh
smoke_job=$("$python_bin" -B -c 'from RQs.RQ4_5.src.utils import RESULTS,read;print(read(RESULTS/"qualification/smoke_submission_12.json")["job_id"].split(";")[0])')
review_job=$(sbatch --parsable --dependency="afterany:$smoke_job" --output="$CANVASRCA_RQ45_ROOT/logs/native_review12_%j.out" --error="$CANVASRCA_RQ45_ROOT/logs/native_review12_%j.err" RQs/RQ4_5/scripts/review_native_smoke12_nibi.sbatch)
"$python_bin" -B - "$smoke_job" "$review_job" <<'RECEIPT'
import sys,time
from RQs.RQ4_5.src.utils import RESULTS,save
save(RESULTS/'qualification/native_smoke_review_submission.json',{'smoke_job_id':sys.argv[1],'review_job_id':sys.argv[2],
 'attempt':12,'dependency':'afterany:'+sys.argv[1],'formal_authorized':False,'manual_answer_and_measurement_review_still_required':True,'submitted_unix':time.time()})
print({'smoke_job':sys.argv[1],'review_job':sys.argv[2]},flush=True)
RECEIPT
