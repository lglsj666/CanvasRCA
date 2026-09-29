#!/usr/bin/env bash
# Explicit future invocation only: one CPU run, then three bounded logical smokes.
set -euo pipefail
RQ37_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$RQ37_DIR/entry.sh" register
bash "$RQ37_DIR/entry.sh" cpu
for rq37_experiment in A B C; do
  bash "$RQ37_DIR/entry.sh" smoke --experiment "$rq37_experiment"
done
