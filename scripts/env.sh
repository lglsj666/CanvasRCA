#!/bin/bash
# Canonical environment for CanvasRCA. Source it, do not execute it:
#   source scripts/env.sh
#
# pyarrow is NOT pip-installable on this cluster (the sdist fails to build), and
# `module load arrow` does not put it on PYTHONPATH for a venv interpreter, so
# the module's site-packages directory is added explicitly. Parquet is required
# by the AegisLab / AIOPS-2025 loaders; without it they raise at construction.

export CANVASRCA_ROOT="${CANVASRCA_ROOT:-/home/lglsj/CanvasRCA}"
export RL_SLM_RCA_ROOT="${RL_SLM_RCA_ROOT:-/home/lglsj/RL-SLM-RCA-rw_phase2}"
export SCRATCH="${SCRATCH:-/home/lglsj/CanvasRCA}"

CANVASRCA_VENV="${CANVASRCA_VENV:-$CANVASRCA_ROOT/venvs/tools}"
ARROW_SITE_PACKAGES="/cvmfs/soft.computecanada.ca/easybuild/software/2023/x86-64-v4/Compiler/gcccore/arrow/17.0.0/lib/python3.11/site-packages"

if [ -d "$CANVASRCA_VENV" ]; then
    # shellcheck disable=SC1091
    source "$CANVASRCA_VENV/bin/activate"
fi

export PYTHONPATH="$CANVASRCA_ROOT/RQs:$CANVASRCA_ROOT:$ARROW_SITE_PACKAGES${PYTHONPATH:+:$PYTHONPATH}"

# Rendered dashboards and DataCase pickles both live on scratch.
export EDA_CACHE_DIR="${EDA_CACHE_DIR:-$CANVASRCA_ROOT/.cache/eda}"
export MPLBACKEND=Agg

echo "CanvasRCA env ready: python=$(python --version 2>&1), repo=$CANVASRCA_ROOT"
