# Nibi dependency sets

`base.txt` contains CPU preparation, rendering, and analysis dependencies.
`inference.txt` is the exact vLLM stack frozen by the global inference config.
`dev.txt` adds static-test and packaging tools.

Use `scripts/build_nibi.sh`. It follows the Alliance wheelhouse-first policy and
never assumes that compute nodes can reach PyPI. If the exact vLLM stack is not
present in the Alliance wheelhouse, set `CANVASRCA_WHEEL_DIR` to a staged,
architecture-compatible local wheel bundle or deploy an approved Apptainer
image; do not silently resolve a different runtime version.

