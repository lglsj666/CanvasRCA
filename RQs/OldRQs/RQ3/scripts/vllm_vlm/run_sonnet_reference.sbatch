#!/bin/bash
#SBATCH --job-name=rq3-sonnet-ref
#SBATCH --account=def-jacobsen
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --output=RQs/RQ3/results/sbatch_logs/rq3sonnet_%j.out

# claude-sonnet-5 reference arms: three modalities, AegisLab n=100, Bedrock.
#
#   sbatch RQs/RQ3/scripts/vllm_vlm/run_sonnet_reference.sbatch
#
# No GPU -- this is an API path, so it runs on CPU alongside the open-weight
# arrays. It exists for two things Array A cannot supply on its own:
#
#   * The thesis gate needs a frontier model's answer too. If text_only matches
#     hybrid for a weak open model that might be the model's limits; if it also
#     matches for Sonnet-5, it is the representation's.
#   * Rank transfer. The RQ1 grid will be screened on an open model to keep it
#     affordable, which is only sound if that model orders configurations the
#     way Sonnet-5 does.
#
# The arms mirror Array A exactly, including v0:hybrid, for two reasons. It is
# the selector A/B (cov30 vs v0, paired over the same 100 cases) at frontier
# scale, and it is the honest successor to the committed 0.797 AegisLab number,
# which was n=20 at RENDERER_VERSION 1 under stochastic decoding and so is not
# comparable to anything produced now.
#
# On rank transfer specifically: Spearman over 3 arms cannot reach p < 0.05 --
# there are only 6 orderings, so the smallest attainable p is 0.167. A 4th arm
# takes the floor to 0.042, which is still descriptive rather than inferential.
# Read the arm ordering as a sanity check; the load-bearing transfer evidence is
# the paired selector A/B, which has n=100 on both models.
#
# Cost: ~5.2M tokens over 400 calls, roughly $16-20 against the project's
# $200-400 budget. Bedrock now receives temperature 0.0 and topP 1.0 -- it
# previously received neither, which is why two runs of one config disagreed on
# 5 of 20 cases.

set -uo pipefail

REPO="${SLURM_SUBMIT_DIR:-$PWD}"
cd "$REPO"

MODEL="${MODEL:-claude-sonnet-5}"
EXP_PREFIX="${EXP_PREFIX:-rq3_v1}"
N_CASES="${N_CASES:-100}"
DATASET="${DATASET:-aegislab}"

# Identical to Array A's ARMS, in the same order and for the same reasons: the
# thesis gate's two arms first, then the selector anchor, then the diagnostic.
ARMS=("cov30:hybrid" "cov30:text_only" "v0:hybrid" "cov30:image_only")

echo "sonnet reference: $MODEL on $DATASET n=$N_CASES"
echo "  arms=${ARMS[*]}"

rc_all=0
for arm in "${ARMS[@]}"; do
  cfg="${arm%%:*}"
  modality="${arm##*:}"
  exp="${EXP_PREFIX}_${MODEL}_${cfg}_${modality}"
  echo ""
  echo "=== arm: config=$cfg modality=$modality -> RQs/RQ3/results/$exp ==="
  (
    source scripts/env.sh
    python scripts/smoke_e2e.py \
      --model "$MODEL" --dataset "$DATASET" --n "$N_CASES" \
      --modality "$modality" --config "$cfg" --experiment "$exp" \
      --out "RQs/RQ3/results/$exp" --no-gates
  )
  rc=$?
  echo "[arm $cfg/$modality] exit: $rc"
  [ "$rc" -ne 0 ] && rc_all=1
done

echo ""
echo "sonnet reference done; worst arm exit: $rc_all"
exit 0
