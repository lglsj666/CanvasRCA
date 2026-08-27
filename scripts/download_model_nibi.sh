#!/usr/bin/env bash
#SBATCH --job-name=canvasrca-model
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=08:00:00
#SBATCH --output=artifacts/model_downloads/slurm-%j.log

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
cd "$PROJECT_ROOT"
# shellcheck disable=SC1091
source scripts/load_nibi_modules.sh base
export CANVASRCA_ENV="${CANVASRCA_INFERENCE_ENV:-$PROJECT_ROOT/.venv-inference}"
# shellcheck disable=SC1091
source scripts/env.sh

MODEL="${1:?usage: download_model_nibi.sh qwen3.8-27b|gemma-4-26b-a4b}"
case "$MODEL" in
  qwen3.8-27b)
    REPOSITORY="Qwen/Qwen3.8-27B"
    REVISION="1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0"
    TARGET="${CANVASRCA_QWEN_MODEL:-$PROJECT_ROOT/models/Qwen3.8-27B}"
    ;;
  gemma-4-26b-a4b)
    REPOSITORY="google/gemma-4-26B-A4B-it"
    REVISION="4d7ae4984b7db7de8f8457170b3f1a419ee76d52"
    TARGET="${CANVASRCA_GEMMA_MODEL:-$PROJECT_ROOT/models/gemma-4-26B-A4B-it}"
    ;;
  *)
    echo "unknown model: $MODEL" >&2
    exit 2
    ;;
esac

mkdir -p "$TARGET"
"$CANVASRCA_ENV/bin/python" -m huggingface_hub.cli.hf download \
  "$REPOSITORY" --revision "$REVISION" --local-dir "$TARGET" --max-workers 4
[[ -s "$TARGET/config.json" ]] || { echo "missing config.json after download" >&2; exit 3; }
find "$TARGET" -maxdepth 1 -type f -name '*.safetensors' -size +0c | sort >"$TARGET/safetensors.inventory"
[[ -s "$TARGET/safetensors.inventory" ]] || { echo "no non-empty safetensors files" >&2; exit 3; }

curl -fsSL "https://huggingface.co/api/models/${REPOSITORY}?blobs=true" \
  | jq --arg model "$MODEL" --arg revision "$REVISION" --arg target "$TARGET" '
      {
        schema_version: "CanvasRCAModelDownloadV1",
        model: $model,
        repository: .id,
        requested_revision: $revision,
        observed_revision: .sha,
        target: $target,
        expected_total_bytes: ([.siblings[].size // 0] | add),
        expected_file_count: (.siblings | length),
        completed_at_utc: (now | strftime("%Y-%m-%dT%H:%M:%SZ"))
      }
      | if .observed_revision != .requested_revision then error("revision drift") else . end
    ' >"$TARGET/download_manifest.json"

sha256sum "$TARGET/config.json" "$TARGET"/*.safetensors >"$TARGET/download_sha256.txt"
echo "downloaded $REPOSITORY@$REVISION to $TARGET"
