#!/usr/bin/env bash
set -euo pipefail
cd /home/lglsj/CanvasRCA_nibi
export PYTHONPATH=src:.
exec /home/lglsj/CanvasRCA/venvs/tools/bin/python -m RQs.RQ4_2.src.main status
