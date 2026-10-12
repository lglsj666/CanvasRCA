#!/usr/bin/env bash
# One train and one validation case per AIOPS dataset; no eval/TT input.
set -euo pipefail
cd "$(dirname "$0")/../../.."
export CANVASRCA_CACHE_ROOT="$PWD/build/cache/rq3"
export CANVASRCA_STANDALONE=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD/build/rq21_python_deps:$PWD/src:$PWD${PYTHONPATH:+:$PYTHONPATH}"
source scripts/env_local.sh
QUAL_ROOT="${RQ3_QUAL_ROOT:-RQs/RQ3/results/qualification_balanced_v14}"
for PARTITION in train validation; do
  "$CANVASRCA_PYTHON" -u -m RQs.RQ3.src.main prepare \
    --output "$QUAL_ROOT/$PARTITION" --partition "$PARTITION" --count 2 --workers 2
  "$CANVASRCA_PYTHON" -m RQs.RQ3.src.main catalog-preflight \
    --prepared "$QUAL_ROOT/$PARTITION" --output "$QUAL_ROOT/${PARTITION}_preflight.json"
done
"$CANVASRCA_PYTHON" -m RQs.RQ3.src.main format-examples \
  --prepared "$QUAL_ROOT/train" --output "$QUAL_ROOT/optimizer_examples" --qualification
"$CANVASRCA_PYTHON" -m RQs.RQ3.src.main preview \
  --prepared "$QUAL_ROOT/validation" --output "$QUAL_ROOT/preview"
