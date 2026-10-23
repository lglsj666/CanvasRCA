# RQ4.5 implementation

Six main arms: H_MARGINAL, H_TOPOLOGY, H_TOPO_MARGINAL, V_DOMAIN_FULL, V_SOURCE_UNIFORM, V_CONTEXT_FILL. Historical baselines are references only.

**Current authorization: All CPU qualification passed and frozen on Nibi (job 24546402, exit 0). GPU smoke and formal inference remain disabled.**

[CPU job receipt](findings/nibi_cpu_submission.json). The original implementation delivery was static-only; the subsequent user request authorizes CPU qualification.

Static checker (does not launch qualification):

```bash
bash RQs/RQ4_5/scripts/static.sh
```

The available `cpu`, `mechanism`, `runtime`, `unit`, `budget`, `determinism`, `freeze`, `launch-smoke`, `launch-formal`, `resume`, `pause`, `status`, `analyze`, `view --key …` and `finalize` commands are implemented in `src/main.py`. `scripts/run.sh` forwards an explicit command; it grants no permissions. CPU work requires `results/exclusive_spatial_v1/qualification/cpu_authorization.json` with `authorized: true` and the current `execution_fingerprint`. The current Nibi CPU-only credential implements the user’s explicit CPU authorization. GPU scopes additionally require independent scope credentials, passed complete CPU and a frozen queue; formal requires passed smoke. No command writes its own authorization.

`freeze` requires population, input-cost, mechanism, unit, runtime, actual deterministic-repaint and visual-review reports, all passed and source-matched. Visual review records must be written after actual image inspection, not fabricated by a script. Actual Nibi images are inspected during the authorized CPU qualification; the initial static-only delivery did not render examples.

Modules: `exps.py` owns compiler/selectors/backend; `utils.py` owns central scoring/identities/storage; `main.py` owns scheduling; `gates.py` owns static checks, qualification and analysis; `tests.py` contains offline regressions. Runtime libraries and historical transport are lazy imports; static checking needs no Torch, tokenizer, GPU, browser or data processing.

[Plan](../../docs/experiment_plans/RQ4_5_Exclusive_Modality_Spatial_Pruning_Plan_2026-10-18.md) · [Unique findings status](findings/exp_exclusive_spatial_findings.md) · [Static check receipt](findings/static_check.json) · [Differences and sources](../../docs/experiment_plans/RQ4_5_History_and_Implementation_Review_2026-10-18.md)

[Complete CPU qualification report](../../docs/experiment_reports/RQ4_5_CPU_Qualification_2026-10-19.md) · [Machine receipt](findings/nibi_cpu_qualification.json). All 139 frozen source/config files match local and Nibi bytes.
