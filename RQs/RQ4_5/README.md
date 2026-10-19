# RQ4.5 implementation

Six main arms: H_MARGINAL, H_TOPOLOGY, H_TOPO_MARGINAL, V_DOMAIN_FULL, V_SOURCE_UNIFORM, V_CONTEXT_FILL. Historical baselines are references only.

**Current authorization: code and static checks only. All runtime qualifications remain pending.**

Run only the static checker now:

```bash
bash RQs/RQ4_5/scripts/static.sh
```

The future `cpu`, `mechanism`, `runtime`, `unit`, `freeze`, `launch-smoke`, `launch-formal`, `resume`, `pause`, `status`, `analyze`, `view --key …` and `finalize` commands are implemented in `src/main.py`. `scripts/run.sh` forwards an explicit command; it grants no permissions. CPU work requires `results/exclusive_spatial_v1/qualification/cpu_authorization.json` with `authorized: true` and the current `execution_fingerprint`. It must be supplied only after a new user instruction. GPU scopes additionally require independent scope credentials, passed complete CPU and a frozen queue; formal requires passed smoke. No command writes its own authorization.

`freeze` requires population, mechanism, unit, runtime and actual visual-review reports, all passed and source-matched. Visual review records must be written after actual image inspection, not fabricated by a script. No new examples are generated in this static-only delivery.

Modules: `exps.py` owns compiler/selectors/backend; `utils.py` owns central scoring/identities/storage; `main.py` owns scheduling; `gates.py` owns static checks, qualification and analysis; `tests.py` contains future offline regressions. Runtime libraries and historical transport are lazy imports; static checking needs no Torch, tokenizer, GPU, browser or data processing.

[Plan](../../docs/experiment_plans/RQ4_5_Exclusive_Modality_Spatial_Pruning_Plan_2026-10-18.md) · [Unique findings status](findings/exp_exclusive_spatial_findings.md) · [Static check receipt](findings/static_check.json) · [Differences and sources](../../docs/experiment_plans/RQ4_5_History_and_Implementation_Review_2026-10-18.md)
