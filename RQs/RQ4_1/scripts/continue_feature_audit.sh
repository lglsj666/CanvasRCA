#!/usr/bin/env bash
# Continue only the authorized encoder-dependent CPU audits, then exit.
set -euo pipefail
cd /home/lglsj/CanvasRCA_nibi
export CUDA_VISIBLE_DEVICES=""
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONPATH=src:.
rq_python=/home/lglsj/CanvasRCA/venvs/tools/bin/python
rq_out=RQs/RQ4_1/results/comparison_coding_v1/cpu_admission_v5
exec 9>"$rq_out/pipeline.lock"
flock -n 9
printf '%s\n' "$$" >"$rq_out/pipeline.pid"
set_phase() {
    printf '%s\n' "$1" >"$rq_out/pipeline.status.tmp"
    mv "$rq_out/pipeline.status.tmp" "$rq_out/pipeline.status"
    printf '%s %s\n' "$(date -u +%FT%TZ)" "$1"
}
trap 'rq_exit=$?; if (( rq_exit != 0 )); then set_phase "failed_exit_${rq_exit}"; fi' EXIT
rq_deadline="$($rq_python -c 'from RQs.RQ4_1.src.utils import read_json; p=read_json("RQs/RQ4_1/results/comparison_coding_v1/cpu_admission_v4/started.json"); print(int(p["started_unix"]+p["max_wall_seconds"]))')"
rq_encoder_deadline="$($rq_python -c 'from RQs.RQ4_1.src.utils import read_json; p=read_json("RQs/RQ4_1/results/comparison_coding_v1/cpu_admission_v5/encoder/budget.json"); c=read_json("RQs/RQ4_1/configs/encoder_admission_v5.json"); print(int(p["started_unix"]+c["wall_seconds"])+10)')"
set_phase waiting_for_authorized_encoder
while true; do
    rq_status="$($rq_python -c 'from RQs.RQ4_1.src.utils import read_json; print(read_json("RQs/RQ4_1/results/comparison_coding_v1/cpu_admission_v5/encoder/report.json")["status"])')"
    if [[ "$rq_status" == passed_encoder_only ]]; then break; fi
    if [[ "$rq_status" != running ]]; then
        printf 'Encoder did not pass: %s\n' "$rq_status" >&2
        exit 1
    fi
    rq_now=$(date +%s)
    if (( rq_now >= rq_deadline || rq_now >= rq_encoder_deadline )); then
        printf 'Original preparation deadline reached; no audit launched.\n' >&2
        exit 124
    fi
    sleep 5
done
for rq_stage in covariates selection; do
    rq_remaining=$((rq_deadline - $(date +%s)))
    if (( rq_remaining <= 0 )); then exit 124; fi
    set_phase "running_${rq_stage}"
    timeout --signal=TERM --kill-after=10 "${rq_remaining}s" "$rq_python" \
        -m RQs.RQ4_1.src.main "admission-${rq_stage}" >>"$rq_out/${rq_stage}.log" 2>&1
done
set_phase completed_requested_feature_audits_full_qualification_still_pending
# Deliberately no smoke, model service, formal launch or follow-on command.
