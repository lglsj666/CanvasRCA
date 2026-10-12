#!/usr/bin/env bash
# Shared environment for the vLLM hook and the client that consumes its sidecar.
MODEL="${1:?usage: source enable_attention_probe.sh MODEL}"
# Explicit successor diagnostic projection; historical/default launch stays on.
case "${CANVASRCA_ATTENTION_MODE:-on}" in
  off)
    export CANVASRCA_ATTENTION_PROBE=0 CANVASRCA_ATTENTION_PROBE_REQUIRED=0
    return 0 ;;
  on) ;;
  *) echo 'CANVASRCA_ATTENTION_MODE must be on or off' >&2; return 2 ;;
esac
export CANVASRCA_ATTENTION_PROBE=1
export CANVASRCA_ATTENTION_PROBE_REQUIRED=1
export CANVASRCA_ATTENTION_MODEL="$MODEL"
export CANVASRCA_ATTENTION_DIR="${CANVASRCA_ATTENTION_DIR:-$CANVASRCA_CACHE_ROOT/attention_probe}"
mkdir -p "$CANVASRCA_ATTENTION_DIR"
BOOTSTRAP="$CANVASRCA_ROOT/src/vlmrca/vlm/attention_probe_bootstrap"
case ":${PYTHONPATH:-}:" in
  *":$BOOTSTRAP:"*) ;;
  *) export PYTHONPATH="$BOOTSTRAP${PYTHONPATH:+:$PYTHONPATH}" ;;
esac
