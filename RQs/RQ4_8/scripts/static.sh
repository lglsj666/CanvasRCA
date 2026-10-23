#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/environment_local.sh"
exec python3 -B -m RQs.RQ4_8.src.main static
