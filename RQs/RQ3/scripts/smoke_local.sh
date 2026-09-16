#!/usr/bin/env bash
# One bounded logical smoke; learning includes one disposable optimizer step.
set -euo pipefail
cd "$(dirname "$0")/../../.."
export CANVASRCA_STANDALONE=1 PYTHONDONTWRITEBYTECODE=1
export CANVASRCA_CACHE_ROOT="$PWD/build/cache/rq3"
export PYTHONPATH="$PWD/build/rq21_python_deps:$PWD/src:$PWD${PYTHONPATH:+:$PYTHONPATH}"
source scripts/env_local.sh
RQ3_EXPERIMENT="${1:?registered experiment name required}"
QUAL_ROOT="${RQ3_QUAL_ROOT:-RQs/RQ3/results/qualification_balanced_v14}"
ATTEMPT="${RQ3_SMOKE_ATTEMPT:-${RQ3_EXPERIMENT}_smoke_repair_v3}"
ADAPTER_ARGS=()
if [[ "$RQ3_EXPERIMENT" == exp_frozen_solver_generalization ]]; then
  ADAPTER_ARGS=(--adapter-checkpoint "${RQ3_QUAL_ADAPTER:?disposable learning-smoke checkpoint required}")
fi
exec "$CANVASRCA_PYTHON" -m RQs.RQ3.src.main smoke \
  --experiment "$RQ3_EXPERIMENT" \
  --prepared "$QUAL_ROOT/validation" \
  --controls "$QUAL_ROOT/preview" \
  --optimizer-examples "$QUAL_ROOT/optimizer_examples" \
  "${ADAPTER_ARGS[@]}" \
  --output "RQs/RQ3/results/$ATTEMPT"
