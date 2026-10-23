#!/usr/bin/env bash
#SBATCH --account=def-jacobsen_gpu
#SBATCH --partition=gpubase_bygpu_b1
#SBATCH --gpus=h100:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --hint=nomultithread
#SBATCH --mem=96G
#SBATCH --time=00:15:00
#SBATCH --job-name=rq45-smoke
#SBATCH --no-requeue
set -euo pipefail
allocation_started=$(date +%s)
repo="${CANVASRCA_NIBI_REPO:-/home/lglsj/CanvasRCA_20261018}"
cd "$repo"
source RQs/RQ4_5/scripts/runtime_environment_nibi.sh
"$python_bin" -B - "$allocation_started" <<'PY'
import sys
from RQs.RQ4_5.src.utils import RESULTS,RQ,read,save
path=RESULTS/'smoke/logical_clock.json'
if not path.exists():
    started=float(sys.argv[1]);limit=read(RQ/'configs/protocol_v1.json')['smoke_seconds']
    save(path,{'started_unix':started,'deadline_unix':started+limit,
        'seconds_limit':limit,'reset_allowed':False,
        'scope':'allocation entry including environment activation and model startup'})
PY
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
# The registered CPU-qualified AsyncLLM adapter owns this allocation's engine.
# It is not an HTTP API and does not need an API key. The experiment recipe
# overrides historical global server capacity: BF16, 40960, 8 seqs, VRAM 0.8.
# Slurm and the registered internal clock allow the full 15 minutes, including
# model startup. There is no additional, shorter outer watchdog.
if [[ "${CANVASRCA_RQ45_PROFILE_ADAPTER:-0}" == 1 ]]; then
  exec bash RQs/RQ4_5/scripts/profile_adapter_smoke_nibi.sh "$python_bin"
fi
exec "$python_bin" -B -u -m RQs.RQ4_5.src.main smoke
