#!/usr/bin/env bash
set -euo pipefail
cd /home/lglsj/CanvasRCA_nibi
export PYTHONPATH=src:.
export CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
exec /home/lglsj/CanvasRCA/venvs/infer/bin/python -m RQs.RQ4_2.src.main formal-check
