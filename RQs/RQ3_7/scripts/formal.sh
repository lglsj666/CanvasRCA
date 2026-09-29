#!/usr/bin/env bash
# Caller must detach using nohup/systemd; A and B only unless C explicitly named.
set -euo pipefail
RQ37_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$#" -eq 0 ]]; then
  set -- A B
fi
exec bash "$RQ37_DIR/entry.sh" queue --experiments "$@"
