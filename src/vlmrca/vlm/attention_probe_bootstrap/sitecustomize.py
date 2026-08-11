"""Lazy vLLM attention-probe bootstrap; activated only by environment flag."""

from vlmrca.vlm.attention_probe import install_import_hooks

install_import_hooks()
