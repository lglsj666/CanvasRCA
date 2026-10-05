# RQ3.18 population readout protocol

Authoritative preregistration: [plan](../../../docs/experiment_plans/RQ3_18_Population_Readout_Plan_2026-10-04.md).

DD-318-2 (2026-10-04), adopted. User rejected the marginal-only attribution plan and explicitly authorized deletion and rewrite. The old version had zero model calls. Preserve complete M/R/L/G facts and fixed-five output; test named population readout × four representations, with three independent call repeats. This is a new population-statistic presentation, not a new causal estimator, a topology successor, or a density plot.

RQ3.16 documented median/p95 and inclusive/exclusive mistakes; rank-selected child points do not estimate population density. Existing trace.dumbbell hardcodes exclusive p95, hence a new registered trace_profile.quantiles component is necessary. No historical component semantics change. No neutral image or screenshot control.

Version rq318_population_readout_v1. Fixed220 exposed eval, eleven arms,2420 positions; overall2500 attempts including18 logical smoke, formal2482 maximum. No score-based exclusion, root-labelled routing, correctness retry, attention, training or new model. Four primary and17 secondary contrasts; separate case/group Holm families; no CI. All phase models and scalar thresholds are frozen in configs/population_readout_v1.json.

Reuse approved RQ3.16 transaction and scheduler primitives, frozen source RQ3.15 pair packets, and RQ3.16 native sample PNGs. Scientific compiler, new profile drawings, CPU/control/lifecycle/statistical tests and report adapter are newly implemented. Prior deleted RQ3.18 code or results are not imported.

Execution boundary: static+fullCPU+actualvisualreview then stop. GPU smoke and formal are unconditionally blocked until a subsequent source-bound authorization revision. CPU success cannot activate inference.
