#!/usr/bin/env bash
# Metadata-only forward freeze after actual native encoder qualification.
#SBATCH --account=def-jacobsen_cpu
#SBATCH --partition=cpubase_bycore_b1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --hint=nomultithread
#SBATCH --mem=8G
#SBATCH --time=00:10:00
#SBATCH --job-name=rq45-runtime-freeze
#SBATCH --no-requeue
set -euo pipefail
repo="${CANVASRCA_NIBI_REPO:-/home/lglsj/CanvasRCA_20261018}"
cd "$repo"
module load StdEnv/2023 python/3.11.5 cuda/12.9 arrow/18.1.0
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
bash RQs/RQ4_5/scripts/adopt_runtime_backend_nibi.sh
export CANVASRCA_RQ45_ROOT=/project/def-jacobsen/canvasrca_cache/RQ4_5/cpu_v1
export CANVASRCA_RQ45_SOURCE_ROOT=/project/def-jacobsen/canvasrca_cache/RQ4_5/source_dependencies
export CANVASRCA_QWEN_MODEL=/scratch/lglsj/CanvasRCA/models/Qwen3.8-27B
export PYTHONPATH="$repo/src:$repo" PYTHONDONTWRITEBYTECODE=1
/scratch/lglsj/CanvasRCA/.venv-inference/bin/python -B -m RQs.RQ4_5.src.main static
