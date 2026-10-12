#!/usr/bin/env bash
set -euo pipefail
RQ320_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$RQ320_ROOT"
source scripts/env_local.sh
export CUDA_VISIBLE_DEVICES=''
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=1
RQ320_CPU_PYTHON=/home/lglsj/CanvasRCA/venvs/infer/bin/python
"$RQ320_CPU_PYTHON" -m RQs.RQ3_20.src.main static
"$RQ320_CPU_PYTHON" -m RQs.RQ3_20.src.main unit
"$RQ320_CPU_PYTHON" -m RQs.RQ3_20.src.main text-feasibility
"$RQ320_CPU_PYTHON" - <<'PY'
from RQs.RQ3_20.src.utils import ROOT,config,read
c=config();r=read(ROOT/c['results']/'qualification/cpu_text_feasibility.json')
if r['status']=='failed':
    raise SystemExit('Candidate stopped: necessary text-budget feasibility failed; no model calls')
PY
"$RQ320_CPU_PYTHON" -m RQs.RQ3_20.src.main render-all
"$RQ320_CPU_PYTHON" -m RQs.RQ3_20.src.main feasibility
"$RQ320_CPU_PYTHON" - <<'PY'
from RQs.RQ3_20.src.utils import config
from RQs.RQ3_20.src.gates import require_feasibility
require_feasibility(config())
PY
