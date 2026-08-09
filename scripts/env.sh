#!/usr/bin/env bash
# Source this file from the repository root or from a Slurm job.

CANVASRCA_ROOT="${CANVASRCA_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
export CANVASRCA_ROOT
export RL_SLM_RCA_ROOT="${RL_SLM_RCA_ROOT:-$(cd "$CANVASRCA_ROOT/.." && pwd)/RL-SLM-RCA-rw_phase2}"
export SCRATCH="${SCRATCH:-$CANVASRCA_ROOT}"
export CANVASRCA_PROCESSED_ROOT="${CANVASRCA_PROCESSED_ROOT:-$CANVASRCA_ROOT/dataset/processed}"
export MPLBACKEND=Agg
export PYTHONUNBUFFERED=1
export PYTHONPATH="$CANVASRCA_ROOT/src:$CANVASRCA_ROOT${PYTHONPATH:+:$PYTHONPATH}"

CANVASRCA_ENV="${CANVASRCA_ENV:-$CANVASRCA_ROOT/.venv}"
if [[ -f "$CANVASRCA_ENV/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$CANVASRCA_ENV/bin/activate"
fi
