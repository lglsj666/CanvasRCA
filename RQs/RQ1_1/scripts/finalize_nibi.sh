#!/usr/bin/env bash
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=logs/rq1_1_finalize_%j.log
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
# shellcheck disable=SC1091
source scripts/env.sh
export CANVASRCA_VLLM_CONFIG="$ROOT/configs/vllm_inference.yaml"
RUN_ID="${1:?usage: finalize_nibi.sh RUN_ID PREPARED_ID}"
PREPARED_ID="${2:?}"
PYTHON_BIN="${CANVASRCA_PYTHON:-python}"
for experiment in direct_rca direct_qa; do
  "$PYTHON_BIN" -m RQs.RQ1_1.src.main analyse "$RUN_ID" "$experiment"
done
"$PYTHON_BIN" -m RQs.RQ1_1.src.main analyse-suite "$RUN_ID"
"$PYTHON_BIN" -m RQs.RQ1_1.src.main verify "$RUN_ID" --prepared-experiment-id "$PREPARED_ID"
