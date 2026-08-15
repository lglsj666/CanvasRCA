#!/usr/bin/env bash
set -euo pipefail

# Local deployment adapter only. Scientific code/configuration remains in the
# synced Nibi worktree and the hash-valid shared preparation is reused.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_ADAPTER="$ROOT/tmp/run_local_matched_rca.sh"
[[ -f "$BASE_ADAPTER" ]] || { echo "missing base local adapter: $BASE_ADAPTER" >&2; exit 2; }

# Reuse only the local path mapping, preparation checks, and server helpers;
# omit the matched-RCA command dispatcher at the bottom of the base adapter.
source <(sed '/^case "${1:-check}" in/,$d' "$BASE_ADAPTER")

# BASH_SOURCE inside process substitution is not the repository path, so reset
# every site-specific variable used by the imported helper functions.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$ROOT/tmp/rq1_matched_rca_local"
PROJECT="$WORK/project"
RESULTS="$PROJECT/RQs/RQ1/results"
SCRATCH_VIEW="$WORK/scratch_view"
PY=/home/lglsj/CanvasRCA/venvs/infer/bin/python
VLLM=/home/lglsj/CanvasRCA/venvs/infer/bin/vllm
QWEN=/home/lglsj/CanvasRCA/models/Qwen3.6-27B
GEMMA=/home/lglsj/CanvasRCA/models/gemma-4-26B-A4B-it
BASE=rq1_v22b_formal_469_20260813
PREP=rq1_v22b_prepared_shared_469_20260813
FREEZE=ba25fe1dcfbce970fe2da07c298a4132fb3b7df3833c2b44483434c0e72f0118
REMOTE_CONTRACT="$WORK/remote_contract"
UPSTREAM="$REMOTE_CONTRACT/upstream_snapshot"
ROSTER="$PROJECT/RQs/RQ1/configs/rosters/rq1_frozen_eval_469_private_v1.json"

verify_shard() {
  local model=$1 index=$2 tag
  tag="$(printf 'shard-%04d-of-0024' "$index")"
  bwrap_cmd "$PY" -m RQs.RQ1.src.main verify "${BASE}__${tag}" \
    --prepared-experiment-id "${PREP}__${tag}" \
    >"$WORK/logs/direct.verify.$model.$tag.log" 2>&1
}

run_direct_model() {
  local model=$1 server_pid i tag
  local -a args=()
  mapfile -t args < <(bwrap_cmd "$PY" -m unified_scripts.vllm_inference "$model" --format argv)
  bwrap_cmd /usr/bin/env CANVASRCA_ATTENTION_MODEL="$model" \
    VLLM_BATCH_INVARIANT="$([[ "$model" == gemma-4-26b-a4b ]] && echo 1 || echo 0)" \
    "$VLLM" serve "${args[@]}" >"$WORK/logs/direct.$model.server.log" 2>&1 &
  server_pid=$!
  trap 'kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true' RETURN
  for _ in $(seq 1 180); do
    curl -fsS -H 'Authorization: Bearer EMPTY' http://127.0.0.1:8000/v1/models >/dev/null && break
    kill -0 "$server_pid"
    sleep 10
  done
  curl -fsS -H 'Authorization: Bearer EMPTY' http://127.0.0.1:8000/v1/models >/dev/null
  bwrap_cmd "$PY" -m cli.attest_vllm_server "$model" \
    --out "$WORK/logs/direct.$model.attestation.json"
  for i in $(seq 0 23); do
    tag="$(printf 'shard-%04d-of-0024' "$i")"
    bwrap_cmd "$PY" -m RQs.RQ1.src.main run "${BASE}__${tag}" direct_rca "$model" \
      --execute --prepared-experiment-id "${PREP}__${tag}" \
      --shard-index "$i" --shard-count 24 \
      >"$WORK/logs/direct.$model.$tag.log" 2>&1
    verify_shard "$model" "$i"
  done
  kill "$server_pid" 2>/dev/null || true
  wait "$server_pid" 2>/dev/null || true
  trap - RETURN
}

setup
case "${1:-all}" in
  qwen) run_direct_model qwen3.6-27b ;;
  gemma) run_direct_model gemma-4-26b-a4b ;;
  all) run_direct_model qwen3.6-27b; run_direct_model gemma-4-26b-a4b ;;
  *) echo "usage: $0 [qwen|gemma|all]" >&2; exit 2 ;;
esac
