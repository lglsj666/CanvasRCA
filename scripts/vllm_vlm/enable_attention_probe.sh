#!/usr/bin/env bash
# Shared environment for the vLLM hook and the client that consumes its sidecar.
MODEL="${1:?usage: source enable_attention_probe.sh MODEL}"
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
