#!/usr/bin/env bash
#SBATCH --gres=gpu:h100:1
#SBATCH --cpus-per-task=8
#SBATCH --hint=nomultithread
#SBATCH --mem=96G
#SBATCH --time=08:00:00
#SBATCH --signal=B:USR1@360
#SBATCH --no-requeue
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?Slurm allocation required}"
source RQs/RQ3_8/scripts/environment.sh
mode="${1:?smoke or formal}"
if [[ "$mode" == smoke ]]; then
  args=(supervise --smoke-cases)
elif [[ "$mode" == formal ]]; then
  args=(supervise --model "${2:?model required}" --shard "${3:?shard required}")
else
  exit 2
fi
"$CANVASRCA_PYTHON" -m RQs.RQ3_8.src.main "${args[@]}" &
owner=$!
trap 'kill -USR1 "$owner" 2>/dev/null || true' USR1 TERM INT
# wait can be interrupted by the shell trap; keep waiting for the owned drain.
set +e
while true; do
  wait "$owner"
  result=$?
  kill -0 "$owner" 2>/dev/null || break
done
exit "$result"
