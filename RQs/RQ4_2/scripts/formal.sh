#!/usr/bin/env bash
set -euo pipefail
cd /home/lglsj/CanvasRCA_nibi
export PYTHONPATH=src:.
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=1
# No activation is generated here. Deployment qualification is not permission
# to start inference. Later explicit authorization supplies a version-bound permit.
exec /home/lglsj/CanvasRCA/venvs/infer/bin/python -m RQs.RQ4_2.src.main formal "$@"
