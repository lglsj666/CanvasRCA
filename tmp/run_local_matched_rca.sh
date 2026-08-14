#!/usr/bin/env bash
set -euo pipefail

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

sync_source() {
  mkdir -p "$PROJECT/RQs/RQ1" "$RESULTS" "$WORK/logs" "$WORK/cache"
  for d in configs src scripts requirements; do
    mkdir -p "$PROJECT/$d"; rsync -a --delete "$ROOT/$d/" "$PROJECT/$d/"
  done
  for d in configs src scripts; do
    mkdir -p "$PROJECT/RQs/RQ1/$d"
    rsync -a --delete "$ROOT/RQs/RQ1/$d/" "$PROJECT/RQs/RQ1/$d/"
  done
  cp -a "$ROOT"/pyproject.toml "$ROOT"/setup.cfg "$PROJECT/"
  [[ ! -f "$ROOT/RQs/__init__.py" ]] || cp -a "$ROOT/RQs/__init__.py" "$PROJECT/RQs/"
  [[ ! -f "$ROOT/RQs/RQ1/__init__.py" ]] || cp -a "$ROOT/RQs/RQ1/__init__.py" "$PROJECT/RQs/RQ1/"
}

manifest_for() {
  local name=$1 real=$2 remote=$3 source=$4 required=$5 target
  [[ "$(sha256sum "$source" | cut -d' ' -f1)" == "$required" ]] || {
    echo "download manifest hash mismatch for $name" >&2; exit 5;
  }
  target="$SCRATCH_VIEW/${remote#/scratch/}"
  mkdir -p "$target"
  find "$target" -mindepth 1 -depth -delete
  find "$real" -mindepth 1 -maxdepth 1 ! -name download_manifest.json -print0 |
    while IFS= read -r -d '' f; do ln -s "$f" "$target/$(basename "$f")"; done
  cp "$source" "$target/download_manifest.json"
  echo "$remote"
}

check_prepared() {
  "$PY" - "$RESULTS" "$REMOTE_CONTRACT/shard_case_lists.json" "$PREP" "$FREEZE" <<'PY'
import json, sys
from pathlib import Path
results, contract_path, base, freeze = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4]
contract = json.loads(contract_path.read_text())
seen = set()
for shard in contract["shards"]:
    index = shard["shard_index"]
    tag = f"shard-{index:04d}-of-0024"
    path = results / f"{base}__{tag}" / "prepared" / "index.json"
    if not path.is_file():
        raise SystemExit(f"missing locally prepared shard: {path}")
    local = json.loads(path.read_text())
    actual = sorted(str(row["opaque_incident_id"]) for row in local["cases"])
    expected = sorted(shard["opaque_incident_ids"])
    if actual != expected:
        raise SystemExit(f"case assignment mismatch in {tag}")
    if local["runtime_freeze"]["freeze_sha256"] != freeze:
        raise SystemExit(f"runtime freeze mismatch in {tag}")
    if not local.get("preparation_complete"):
        raise SystemExit(f"preparation incomplete in {tag}")
    seen.update(actual)
if len(seen) != 469:
    raise SystemExit(f"prepared unique case total is {len(seen)}, expected 469")
print("locally generated preparation matches 24 remote case lists (469 unique cases)")
PY
}

prepare_local() {
  local complete=1
  for i in $(seq 0 23); do
    [[ -f "$RESULTS/${PREP}__shard-$(printf '%04d' "$i")-of-0024/prepared/index.json" ]] || complete=0
  done
  if [[ "$complete" -eq 0 ]]; then
    echo "Preparing 469 cases locally from the frozen local dataset..."
    bwrap_cmd "$PY" -m RQs.RQ1.src.main prepare "$PREP" "$ROSTER" \
      --output-shard-count 24 >"$WORK/logs/prepare.log" 2>&1
  fi
  check_prepared
}

check_reused() {
  local reused
  reused="$(find "$RESULTS/${BASE}__shard-0000-of-0024/trajectories/matched_rca/qwen3.6-27b" \
    -maxdepth 1 -type f -name '*.json' 2>/dev/null | wc -l)"
  [[ "$reused" -ge 61 ]] || { echo "reusable Qwen shard-0 records: $reused, expected at least 61" >&2; exit 3; }
}

setup() {
  sync_source
  QWEN_REMOTE="$(manifest_for Qwen3.6-27B "$QWEN" \
    /scratch/lglsj/CanvasRCA/models/Qwen3.6-27B \
    "$REMOTE_CONTRACT/manifests/qwen.download_manifest.json" \
    a0d0ebe1d1ae795c263109f004c05069f53fb93833f612606caefc9aaa5cda43)"
  GEMMA_REMOTE="$(manifest_for gemma-4-26B-A4B-it "$GEMMA" \
    /scratch/lglsj/CanvasRCA/models/gemma-4-26B-A4B-it \
    "$REMOTE_CONTRACT/manifests/gemma.download_manifest.json" \
    5679748b08fd080021282ccc67ad13e63a531bc0d889fb7d3f753a596af6a756)"
  export QWEN_REMOTE GEMMA_REMOTE
  observed="$(bwrap_cmd "$PY" - <<'PY'
from RQs.RQ1.src.main import SOURCE_FILES
from RQs.RQ1.src.utils import artifact_contract, load_yaml
print(artifact_contract(config=load_yaml(), code_files=SOURCE_FILES)["freeze_sha256"])
PY
)"
  [[ "$observed" == "$FREEZE" ]] || { echo "local effective freeze mismatch: $observed" >&2; exit 6; }
  prepare_local
  check_reused
}

bwrap_cmd() {
  bwrap --tmpfs / --bind / /host --symlink host/usr /usr --symlink host/bin /bin --symlink host/sbin /sbin \
    --symlink host/lib /lib --symlink host/lib64 /lib64 --symlink host/etc /etc \
    --symlink host/home /home --symlink host/mnt /mnt --symlink host/opt /opt \
    --symlink host/run /run --symlink host/var /var --dev-bind /dev /dev --proc /proc \
    --ro-bind /sys /sys --tmpfs /tmp --dir /scratch --bind "$SCRATCH_VIEW" /scratch \
    --chdir "$PROJECT" /usr/bin/env CANVASRCA_ROOT="$PROJECT" \
    CANVASRCA_QWEN_MODEL="$QWEN_REMOTE" CANVASRCA_GEMMA_MODEL="$GEMMA_REMOTE" \
    CANVASRCA_PROCESSED_ROOT=/home/lglsj/CanvasRCA/dataset/processed \
    CANVASRCA_LEGACY_PROCESSED_ROOT=/home/lglsj/CanvasRCA/dataset/processed \
    RL_SLM_RCA_ROOT="$UPSTREAM" CANVASRCA_ENV=/home/lglsj/CanvasRCA/venvs/infer \
    CANVASRCA_CACHE_ROOT="$WORK/cache" CANVASRCA_ATTENTION_DIR="$WORK/cache/attention_probe" \
    CANVASRCA_ATTENTION_PROBE=1 CANVASRCA_ATTENTION_PROBE_REQUIRED=1 \
    VLLM_BASE_URL=http://127.0.0.1:8000/v1 VLLM_API_KEY=EMPTY \
    VLLM_WORKER_MULTIPROC_METHOD=spawn VLLM_USE_FLASHINFER_SAMPLER=0 \
    VLLM_USE_AOT_COMPILE=0 VLLM_TRITON_FORCE_FIRST_CONFIG=1 \
    TOKENIZERS_PARALLELISM=false CUBLAS_WORKSPACE_CONFIG=:4096:8 CUBLASLT_WORKSPACE_SIZE=1 \
    PYTHONPATH="$PROJECT/src/vlmrca/vlm/attention_probe_bootstrap:$PROJECT/src:$PROJECT" "$@"
}

run_model() {
  local model=$1
  local args=()
  local server="$WORK/logs/$model.server.log"
  local server_pid
  mapfile -t args < <(bwrap_cmd "$PY" -m unified_scripts.vllm_inference "$model" --format argv)
  bwrap_cmd /usr/bin/env CANVASRCA_ATTENTION_MODEL="$model" VLLM_BATCH_INVARIANT="$([[ "$model" == gemma-4-26b-a4b ]] && echo 1 || echo 0)" \
    "$VLLM" serve "${args[@]}" >"$server" 2>&1 &
  server_pid=$!
  trap 'kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true' RETURN
  for _ in $(seq 1 180); do
    curl -fsS -H 'Authorization: Bearer EMPTY' http://127.0.0.1:8000/v1/models >/dev/null && break
    kill -0 "$server_pid"
    sleep 10
  done
  curl -fsS -H 'Authorization: Bearer EMPTY' http://127.0.0.1:8000/v1/models >/dev/null
  bwrap_cmd "$PY" -m cli.attest_vllm_server "$model" --out "$WORK/logs/$model.attestation.json"
  for i in $(seq 0 23); do
    tag="$(printf 'shard-%04d-of-0024' "$i")"
    bwrap_cmd "$PY" -m RQs.RQ1.src.main run "${BASE}__${tag}" matched_rca "$model" \
      --execute --prepared-experiment-id "${PREP}__${tag}" --shard-index "$i" --shard-count 24 \
      >"$WORK/logs/$model.$tag.log" 2>&1
  done
  kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true; trap - RETURN
}

verify_all() {
  local tag
  for i in $(seq 0 23); do
    tag="$(printf 'shard-%04d-of-0024' "$i")"
    bwrap_cmd "$PY" -m RQs.RQ1.src.main verify "${BASE}__${tag}" \
      --prepared-experiment-id "${PREP}__${tag}" >"$WORK/logs/verify.$tag.log" 2>&1
  done
}

case "${1:-check}" in
  init) sync_source; echo "Local shadow runtime initialized at $PROJECT" ;;
  check) setup; echo "469 locally prepared cases, 24 shard assignments, manifests and freeze verified" ;;
  qwen) setup; run_model qwen3.6-27b ;;
  gemma) setup; run_model gemma-4-26b-a4b; verify_all ;;
  all) setup; run_model qwen3.6-27b; run_model gemma-4-26b-a4b; verify_all ;;
  status) find "$WORK/logs" -type f -maxdepth 1 -printf '%TY-%Tm-%Td %TH:%TM %f %s bytes\n' 2>/dev/null | sort ;;
  *) echo "usage: $0 init|check|qwen|gemma|all|status" >&2; exit 2 ;;
esac
