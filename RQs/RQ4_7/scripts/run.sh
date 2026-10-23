#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD/src:$PWD${PYTHONPATH:+:$PYTHONPATH}"
# The CLI checks CPU, visual review, current source, explicit scope permission,
# and (for formal execution) smoke qualification before starting any service.
exec python3 -B -m RQs.RQ4_7.src.main "${1:-status}" --scope "${2:-formal}"
