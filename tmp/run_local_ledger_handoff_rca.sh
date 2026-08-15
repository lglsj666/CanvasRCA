#!/usr/bin/env bash
set -euo pipefail

# Local deployment adapter only; all scientific logic remains in the synced
# Nibi worktree. Reuse the already-qualified local path/runtime helpers.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_ADAPTER="$ROOT/tmp/run_local_matched_rca.sh"
[[ -f "$BASE_ADAPTER" ]] || { echo "missing base adapter: $BASE_ADAPTER" >&2; exit 2; }
source <(sed '/^case "${1:-check}" in/,$d' "$BASE_ADAPTER")

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

trajectory_root() {
  echo "$RESULTS/${BASE}__shard-0000-of-0024/trajectories/ledger_handoff_rca/$1"
}

require_qwen_checkpoint() {
  local root arms shared
  root="$(trajectory_root qwen3.6-27b)"
  arms="$(find "$root" -maxdepth 1 -type f -name '*.json' 2>/dev/null | wc -l)"
  shared="$(find "$root/_shared_stage1" -maxdepth 1 -type f -name '*.json' 2>/dev/null | wc -l)"
  [[ "$arms" -ge 51 && "$arms" -le 1407 && "$shared" -ge 17 && "$shared" -le 469 ]] || {
    echo "Qwen resumable checkpoint invalid: arms=$arms shared=$shared" >&2; exit 4;
  }
}

require_qwen_complete() {
  local arms shared
  arms="$(find "$RESULTS" -path '*/trajectories/ledger_handoff_rca/qwen3.6-27b/*.json' -type f | wc -l)"
  shared="$(find "$RESULTS" -path '*/trajectories/ledger_handoff_rca/qwen3.6-27b/_shared_stage1/*.json' -type f | wc -l)"
  [[ "$arms" -eq 1407 && "$shared" -eq 469 ]] || {
    echo "Qwen must finish first: arms=$arms/1407 shared=$shared/469" >&2; exit 4;
  }
}

verify_shard() {
  local model=$1 index=$2 tag
  tag="$(printf 'shard-%04d-of-0024' "$index")"
  bwrap_cmd "$PY" -m RQs.RQ1.src.main verify "${BASE}__${tag}" \
    --prepared-experiment-id "${PREP}__${tag}" \
    >"$WORK/logs/ledger.verify.$model.$tag.log" 2>&1
}

wait_port_clear() {
  for _ in $(seq 1 60); do
    ! curl -fsS --max-time 1 -H 'Authorization: Bearer EMPTY' \
      http://127.0.0.1:8000/v1/models >/dev/null 2>&1 && return 0
    sleep 2
  done
  echo "port 8000 still serves the retiring model" >&2; return 1
}

run_ledger_model() {
  local model=$1 server_pid i tag
  local -a args=()
  mapfile -t args < <(bwrap_cmd "$PY" -m unified_scripts.vllm_inference "$model" --format argv)
  bwrap_cmd /usr/bin/env CANVASRCA_ATTENTION_MODEL="$model" \
    VLLM_BATCH_INVARIANT="$([[ "$model" == gemma-4-26b-a4b ]] && echo 1 || echo 0)" \
    "$VLLM" serve "${args[@]}" >"$WORK/logs/ledger.$model.server.log" 2>&1 &
  server_pid=$!
  trap 'kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true' RETURN
  for _ in $(seq 1 180); do
    curl -fsS -H 'Authorization: Bearer EMPTY' http://127.0.0.1:8000/v1/models >/dev/null && break
    kill -0 "$server_pid"; sleep 10
  done
  curl -fsS -H 'Authorization: Bearer EMPTY' http://127.0.0.1:8000/v1/models >/dev/null
  bwrap_cmd "$PY" -m cli.attest_vllm_server "$model" \
    --out "$WORK/logs/ledger.$model.attestation.json"
  for i in $(seq 0 23); do
    tag="$(printf 'shard-%04d-of-0024' "$i")"
    bwrap_cmd "$PY" -m RQs.RQ1.src.main run "${BASE}__${tag}" \
      ledger_handoff_rca "$model" --execute \
      --prepared-experiment-id "${PREP}__${tag}" --shard-index "$i" --shard-count 24 \
      >"$WORK/logs/ledger.$model.$tag.log" 2>&1
    verify_shard "$model" "$i"
  done
  kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true
  wait_port_clear; trap - RETURN
}

setup
case "${1:-check}" in
  check) require_qwen_checkpoint; verify_shard checkpoint 0 ;;
  qwen) require_qwen_checkpoint; run_ledger_model qwen3.6-27b ;;
  gemma) require_qwen_complete; run_ledger_model gemma-4-26b-a4b ;;
  all) require_qwen_checkpoint; run_ledger_model qwen3.6-27b; require_qwen_complete; run_ledger_model gemma-4-26b-a4b ;;
  *) echo "usage: $0 [check|qwen|gemma|all]" >&2; exit 2 ;;
esac
