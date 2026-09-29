#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."
phase="${1:-cpu}"
case "$phase" in cpu|smoke) ;; *) echo "Choose cpu or smoke" >&2; exit 2 ;; esac
for family in g_components scope_competition relation_binding; do
  root="RQs/RQ3_6/results/mechanisms_v2/$family"
  mkdir -p "$root/logs"
  bash RQs/RQ3_6/scripts/mechanisms_v2.sh "$family" "$phase" > "$root/logs/${phase}_qualification.log" 2>&1
  if [[ "$phase" == cpu ]]; then
    bash RQs/RQ3_6/scripts/mechanisms_v2.sh "$family" capacity > "$root/logs/capacity_qualification.log" 2>&1
  fi
done
