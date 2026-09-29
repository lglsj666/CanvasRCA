#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."
family="${1:?Choose g_components, scope_competition, or relation_binding}"
shift
case "$family" in
  g_components|scope_competition|relation_binding) ;;
  *) echo "Unregistered experiment" >&2; exit 2 ;;
esac
export CANVASRCA_RQ36_CONFIG="RQs/RQ3_6/configs/${family}_v2.json"
exec bash RQs/RQ3_6/scripts/entry.sh "$@"
