#!/usr/bin/env bash
#SBATCH --cpus-per-task=8
#SBATCH --hint=nomultithread
#SBATCH --mem=32G
#SBATCH --time=01:00:00
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$PWD}"
source RQs/RQ3_8/scripts/environment.sh
export CUDA_VISIBLE_DEVICES=''
export RENDER_BROWSER_TESTS=1
artifact=RQs/RQ3_8/results/ops_components_v7/qualification
attempt_artifacts="$artifact/job-${SLURM_JOB_ID:?}"
mkdir -p "$attempt_artifacts"
mkdir -p "$artifact"
"$CANVASRCA_PYTHON" -m RQs.RQ3_8.src.main static
"$CANVASRCA_PYTHON" -m pytest --import-mode=importlib -q src/renderer/tests.py RQs/RQ3_8/src/tests.py --basetemp="$attempt_artifacts/pytest" --junitxml="$attempt_artifacts/cpu.xml"
cp "$attempt_artifacts/cpu.xml" "$artifact/cpu.xml"
"$CANVASRCA_PYTHON" -m RQs.RQ3_8.src.main seal-cpu
"$CANVASRCA_PYTHON" -m RQs.RQ3_8.src.main export --smoke-cases
"$CANVASRCA_PYTHON" -m RQs.RQ3_8.src.main render --smoke-cases
"$CANVASRCA_PYTHON" -m RQs.RQ3_8.src.main preflight --smoke-cases
if [[ "${CANVASRCA_PREPARE_ALL:-0}" == "1" ]]; then
  "$CANVASRCA_PYTHON" -m RQs.RQ3_8.src.main export
  "$CANVASRCA_PYTHON" -m RQs.RQ3_8.src.main render
fi
