# SIRCL — Systematic Prompt Design for Single-Inference Root Cause Localization in Microservices

*Anonymized artifact accompanying a paper under double-blind review.*

## Overview

Root cause localization (RCL) pinpoints the faulty service during a microservice incident. SIRCL is a systematic prompt design framework that compiles heterogeneous telemetry (metrics, traces, logs) into **one prompt for a single frozen-model inference call** — no agentic tool-calling loop and no fine-tuning.

Full design space candidate sets are in [configs/design_space.yaml](configs/design_space.yaml).

## Repository layout

```
.
├── configs/
│   ├── design_space.yaml     # candidate sets + SIRCL-0 / SIRCL*
│   ├── datasets.yaml         # Table III splits
│   └── experiments/cues/     # HEUR heuristics bundle
├── src/
│   ├── data/                 # dataset loaders (-> DataCase) + splits.py (Table III)
│   ├── telemetry_analyzers/  # the 12 telemetry analyzers + registry
│   ├── prompts/              # design.py (Θ, Alg.1), layouts, reasoning, guidance, topology
│   ├── evaluation/           # inference, scoring, metrics, stats (Wilcoxon), runner
│   ├── selection/            # select.py (Alg.2 sequential selection)
│   └── baselines/            # RCL baseline adapters (see src/baselines/README.md)
├── scripts/
│   ├── select_sircl.py       # RQ2 — run the selection, write SIRCL*
│   ├── evaluate.py           # RQ1/RQ3 — evaluate a design on the test pool / across backbones
│   ├── analyze_limitations.py# Limitations — fault-type failure rates
│   ├── run_baselines.py        # RQ1 — classical / agentic baseline panel
│   └── smoke_new_datasets.py, warm_*_pickle.py  # loader checks + cache warming
└── sample_output/            # a few anonymized SIRCL* per-case runs (prompt + response)
```

## Datasets and splits (Table III)

Selection uses R-OB / A-22 / A-25 only (stratified 60/40 dev/val over 10 seeds);
the held-out test pool is A-22 (140), A-25 (240), Aegis (100), R-TT (90), with Aegis
and R-TT fully cross-benchmark. See [configs/datasets.yaml](configs/datasets.yaml).

Data is **not** included. Download each dataset from its original provider and extract it under
`$XXXX-7/data/` at the loader root below (any root may be overridden with the matching
`<DATASET>_ROOT` environment variable — see [src/data/splits.py](src/data/splits.py)). Loaders then
normalize every dataset into a unified `DataCase`.

| Dataset | Source | Archive(s) | Loader root |
|---|---|---|---|
| R-OB / R-TT (RCAEval) | [Zenodo 14590730](https://zenodo.org/records/14590730) | `RE2-OB.zip`, `RE2-TT.zip` | `$XXXX-7/data/rcaeval/RE2-OB`, `…/RE2-TT` |
| A-22 (AIOps-2022) | [Zenodo 19176851](https://zenodo.org/records/19176851) | `aiops2022.zip` (md5 `a468e018a256ebc5793e4c0d84f0c010`) | `$XXXX-7/data/aiops2022` |
| A-25 (AIOps-2025) | [AIOps-2025 Challenge](https://www.aiops.cn/gitlab/aiops-live-benchmark/aiopschallenge2025.git) (git-lfs: clone + `git lfs pull`) | repo tarballs | `$XXXX-7/data/aiops2025/repo` |
| Aegis (AegisLab) | [Zenodo 17105974](https://zenodo.org/records/17105974) | `rcabench-platform-feat-fse26.zip`, `rcabench-fse-26.zip`, `rcabench-absolute_anomaly.tar.gz` | `$XXXX-7/data/aegislab` |

## Installation

Python 3.11+.

```bash
pip install -r requirements.txt
```


## Configuration

Backbones and credentials come from environment variables (no keys in the repo).
Model keys are defined in `src/evaluation/inference.py`:

| Key | Backbone | Credentials |
|---|---|---|
| `slm` | Qwen3.5-9B (local) | `SLM_MODEL_ID`, `XXXX-7` (HF cache) |
| `deepseek` | DeepSeek-v4-pro | `DEEPSEEK_API_KEY` |
| `llm` / `gpt-mini` | GPT-5.4 / GPT-5.4-mini | `OPENAI_API_KEY` |
| `claude` / `gemini` / `kimi` | Claude-Opus-4.7 / Gemini-3.1-pro / Kimi-K2.5 | `<VENDOR>_API_KEY`, `<VENDOR>_BASE_URL` |

Dataset roots come from `XXXX-7` or `<DATASET>_ROOT` (see `src/data/splits.py`).

## Reproduction

```bash
# RQ2 — sequential design selection on dev/val (writes SIRCL* + a decision log)
python scripts/select_sircl.py --results-dir results/selection \
    --backbones slm,deepseek --datasets re2_ob,aiops2022,aiops2025

# RQ1 — evaluate SIRCL* on the held-out test pool
python scripts/evaluate.py --backbones slm --out results/test/eval.json

# RQ3 — transferability across backbones
python scripts/evaluate.py --backbones slm,deepseek,claude,gpt-mini,gemini,kimi

# Additional analysis — per-fault-type / per-family top-1 failure rates
python scripts/analyze_limitations.py --results-dir results/test/slm
```

`select_sircl.py` also accepts `--from-results <dir>` to run the selection logic over an
already-computed per-candidate results store (no inference). Effectiveness is reported as
MRR (primary) and Accuracy@1/@3; cost as tokens, wall-clock, calls, and USD.

## Sample output

[`sample_output/`](sample_output/) holds a few end-to-end SIRCL\* runs — one case per
dataset for both `qwen3.5-9b` and `deepseek-v4-pro`. Each JSON records the locked design
(analyzers / sequence / layout / reasoning), the single compiled prompt sent to the frozen
model (`messages`), and the model's `response` — illustrating the one-prompt,
single-inference paradigm.

## License

Released under the MIT License — see [LICENSE](LICENSE).
