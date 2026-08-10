#!/usr/bin/env bash
# Source after scripts/env.sh to select a job-local vLLM endpoint.  Nibi can
# place multiple single-GPU allocations on one host, so port 8000 is unsafe for
# concurrent jobs even though each allocation sees a different GPU.

if [[ -n "${CANVASRCA_VLLM_PORT:-}" ]]; then
  [[ "$CANVASRCA_VLLM_PORT" =~ ^[0-9]+$ ]] || {
    echo "CANVASRCA_VLLM_PORT must be numeric" >&2
    return 2
  }
  (( CANVASRCA_VLLM_PORT >= 1024 && CANVASRCA_VLLM_PORT <= 65535 )) || {
    echo "CANVASRCA_VLLM_PORT must be in [1024, 65535]" >&2
    return 2
  }
else
  canvasrca_port_key="${SLURM_JOB_ID:-$$}"
  canvasrca_port_start=$((15000 + (canvasrca_port_key % 45000)))
  CANVASRCA_VLLM_PORT=""
  for canvasrca_port_offset in $(seq 0 1023); do
    canvasrca_port=$((15000 + ((canvasrca_port_start - 15000 + canvasrca_port_offset) % 45000)))
    if [[ -z "$(ss -H -ltn "sport = :${canvasrca_port}")" ]]; then
      CANVASRCA_VLLM_PORT="$canvasrca_port"
      break
    fi
  done
  [[ -n "$CANVASRCA_VLLM_PORT" ]] || {
    echo "unable to select a free localhost port for vLLM" >&2
    return 3
  }
fi

export CANVASRCA_VLLM_PORT
export VLLM_BASE_URL="http://127.0.0.1:${CANVASRCA_VLLM_PORT}/v1"
unset canvasrca_port canvasrca_port_key canvasrca_port_start canvasrca_port_offset
