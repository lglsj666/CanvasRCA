#!/usr/bin/env bash
set -euo pipefail

# RQ2 currently has only CPU/static gates. Model-calling gates are registered
# later and must remain within the global call/time bounds.
exec "$(dirname "$0")/tests.sh" "$@"

