# Nibi Preparation Guide

This repository is deployed directly on Nibi. Build, dataset conversion, model
staging, CPU pre-rendering, smoke qualification, and full inference use the
entry points below; heavy work never runs on the login node.

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

`scripts/build_nibi.sh` loads the configured Python module, creates
`.venv-base` for deterministic processing/rendering or `.venv-inference` for
vLLM with `virtualenv --no-download`, installs from the Alliance wheelhouse
with `pip --no-index`, and installs a non-editable CanvasRCA wheel without
re-resolving dependencies. The split prevents Nibi's `torchvision`/Pillow-SIMD extension
from replacing the renderer's frozen Pillow files.

The Nibi defaults are `StdEnv/2023`, `gcc/12.3`, `python/3.11.5`,
`arrow/25.0.0`, and (for inference) `opencv/4.13.0` plus `cuda/12.6`. They may be overridden with
`CANVASRCA_STDENV_MODULE`, `CANVASRCA_COMPILER_MODULE`,
`CANVASRCA_PYTHON_MODULE`, `CANVASRCA_ARROW_MODULE`,
`CANVASRCA_OPENCV_MODULE`, and `CANVASRCA_CUDA_MODULE`; any override is runtime
metadata and belongs in the heavy-run contract. Slurm entry points load the
same stack before activating the virtual environment.

```bash
scripts/build_nibi.sh base
scripts/build_nibi.sh inference
```

`scripts/env.sh` selects `.venv-base`. Inference Slurm jobs explicitly select
`.venv-inference`; `CANVASRCA_ENV` or `CANVASRCA_INFERENCE_ENV` may override
those deployment locations and must be recorded in the run contract.
Matplotlib, Hugging Face, Triton, TorchInductor, CUDA, vLLM, and FlashInfer
caches are rooted under `CANVASRCA_CACHE_ROOT`; Nibi jobs must never fall back
to the quota-limited home cache. Optional vLLM usage reporting is disabled so
it neither contacts an external service nor writes to its home-config path.

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

The registered public checkpoints can be staged at their frozen revisions with
CPU-only Slurm jobs:

```bash
sbatch scripts/download_model_nibi.sh qwen3.6-27b
sbatch scripts/download_model_nibi.sh gemma-4-26b-a4b
```

Each download is resumable and writes a revision, size, inventory, and SHA-256
manifest under its model directory before it is accepted for a run contract.

The source datasets remain read-only. If they do not already satisfy the
per-case public/private schema, convert them in CPU Slurm jobs with:

```bash
sbatch --export=ALL,CANVASRCA_DATASET=aegislab scripts/process_dataset_nibi.sh
sbatch --export=ALL,CANVASRCA_DATASET=aiops2022 scripts/process_dataset_nibi.sh
sbatch --export=ALL,CANVASRCA_DATASET=aiops2025 scripts/process_dataset_nibi.sh
sbatch --export=ALL,CANVASRCA_DATASET=re2_ob scripts/process_dataset_nibi.sh
sbatch --export=ALL,CANVASRCA_DATASET=re2_tt scripts/process_dataset_nibi.sh
```

Supply source/cache/output locations only through `SCRATCH`,
`RL_SLM_RCA_ROOT`, and `CANVASRCA_PROCESSED_ROOT`. Conversion writes relative
time telemetry to `public/` and physically separate labels and source mappings
to `private/`; it never changes the source datasets. Validate the complete
corpus before rendering:

```bash
python -m cli.validate_processed_cases \
  --roster RQs/RQ1/configs/rosters/rq1_frozen_eval_469_private_v1.json \
  --out artifacts/data_processing/processed_validation_v1.json
```

## Slurm and vLLM

`RQs/RQ1/scripts/smoke_nibi.sh` and `RQs/RQ1/scripts/submit_nibi.sh` are
one-H100 templates. Both request 14 CPU cores and 240 GB host memory, start the
canonical server inside the allocation, wait for the models endpoint, record
an attestation, and start the RQ run. Smoke allocations are 30 minutes with a
600-second logical supervisor; full allocations are three days. Adjust wall
time through a versioned script change, not an ad hoc scientific override.

Render on CPU before allocating a GPU. The smoke uses the exact registered
three-case roster and 18 aggregate calls across both models:

```bash
RQs/RQ1/scripts/array_nibi.sh prepare SMOKE_ID \
  RQs/RQ1/configs/rosters/rq1_nibi_smoke_private_v1.json 1
sbatch --export=ALL,CANVASRCA_MODEL=qwen3.6-27b,CANVASRCA_EXPERIMENT_ID=SMOKE_ID__shard-0000-of-0001 \
  RQs/RQ1/scripts/smoke_nibi.sh
sbatch --export=ALL,CANVASRCA_MODEL=gemma-4-26b-a4b,CANVASRCA_EXPERIMENT_ID=SMOKE_ID__shard-0000-of-0001 \
  RQs/RQ1/scripts/smoke_nibi.sh
```

For the frozen run, prepare the 469 cases once in a CPU array, then submit all
six experiments for both models against those immutable prepared shards. Use
`CANVASRCA_PREPARE_JOB_ID` for an `afterok` dependency and reuse the same base
ID so completed calls remain resumable.

The Nibi launcher deliberately omits `--gpu-memory-utilization` because the
global value is `null`. This is the requested removal of the project VRAM
fraction cap; vLLM and the Slurm allocation still impose physical limits.

## Deployment checklist

1. Clone the repository and verify `git status`.
2. Stage the processed dataset, model checkpoints, optional upstream checkout,
   and exact dependency wheels or Apptainer image.
3. Build both environments and run `python -m RQs.RQ1.src.tests`.
4. Convert and validate every frozen case without modifying the source data.
5. Pre-render on CPU and freeze the code, config, model, data-adapter, and
   upstream hashes.
6. Submit the bounded smoke and inspect summaries, attestations, logs,
   conversations, prompts, raw responses, truncation, and accounting.
7. Submit all six RQ1 experiments for both models after infrastructure smoke
   qualification.
8. Repair and resume protocol, mismatch, or infrastructure failures. A missed
   scientific threshold is a negative result and does not stop later
   experiments.
