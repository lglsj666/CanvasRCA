# Nibi Preparation Guide

This repository is prepared on WSL but deployed and executed later on Nibi.
The preparation does not include model weights, datasets, virtual environments,
live vLLM attestations, smoke tests, or GPU inference.

## Alliance conventions used

The implementation follows the Digital Research Alliance documentation:

- [Nibi](https://docs.alliancecan.ca/wiki/Nibi) is a Slurm cluster with H100
  GPU resources.
- [Available software](https://docs.alliancecan.ca/wiki/Available_software)
  is exposed through Lmod modules; most Python packages are distributed as
  Alliance-built wheels. Docker is unavailable and Apptainer is supported.
- [Python](https://docs.alliancecan.ca/wiki/Python) recommends an isolated
  virtual environment and wheelhouse-first installation with `--no-index`.
- [Using GPUs with Slurm](https://docs.alliancecan.ca/wiki/Using_GPUs_with_Slurm)
  defines GPU requests such as `--gpus=h100:1`.
- [Running jobs](https://docs.alliancecan.ca/wiki/Running_jobs) requires heavy
  work to be submitted to Slurm rather than run on login nodes.

## Environment build

`scripts/build_nibi.sh` loads the configured Python module, creates `.venv`
with `virtualenv --no-download` where available, installs from the Alliance
wheelhouse with `pip --no-index`, and installs CanvasRCA editable without
re-resolving dependencies.

```bash
scripts/build_nibi.sh base
scripts/build_nibi.sh inference
```

The inference environment is version-locked to
`configs/vllm_inference.yaml`. If the exact vLLM stack is absent from the
Alliance wheelhouse, stage compatible wheels and set:

```bash
export CANVASRCA_WHEEL_DIR=wheelhouse
scripts/build_nibi.sh inference
```

An approved Apptainer image is the fallback for compiled dependency conflicts.
Do not use Docker or silently install a different version.

## Data and models

Deployment supplies these locations through environment variables when they
are not copied into the repository-relative defaults:

```bash
export CANVASRCA_PROCESSED_ROOT=dataset/processed
export CANVASRCA_QWEN_MODEL=models/Qwen3.6-27B
export CANVASRCA_GEMMA_MODEL=models/gemma-4-26B-A4B-it
export RL_SLM_RCA_ROOT=../RL-SLM-RCA-rw_phase2
```

The dataset remains read-only. Generate public/private segmentation artifacts
after the processed corpus is present and freeze their hashes before any model
call.

## Slurm and vLLM

`RQs/RQ1/scripts/submit_nibi.sh` is a one-H100 template. It requests 14 CPU
cores and 240 GB host memory, starts the canonical server inside the allocation,
waits for the models endpoint, records an attestation, and starts the RQ run.
Adjust wall time through a versioned script change; do not alter scientific
parameters through ad hoc command-line flags.

The Nibi launcher deliberately omits `--gpu-memory-utilization` because the
global value is `null`. This is the requested removal of the project VRAM
fraction cap; vLLM and the Slurm allocation still impose physical limits.

## Deployment checklist

1. Clone the repository and verify `git status`.
2. Stage the processed dataset, model checkpoints, optional upstream checkout,
   and exact dependency wheels or Apptainer image.
3. Build the environment and run `scripts/static_checks.sh`.
4. Generate and freeze split manifests.
5. Freeze the global vLLM implementation lock.
6. Enable one RQ-specific run config under a new experiment ID.
7. Submit the bounded smoke; inspect all persisted outputs.
8. Submit the heavy Slurm experiment only after smoke passage.

