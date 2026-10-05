# RQ3.10 CPU qualification — source applicability blocks GPU

Historical v1 record below, preserved. The later user goal authorized deployment,
CPU/GPU regression and full submission. Adopted v2 fixes and qualification
are recorded at the start of
[active preregistration](../../RQs/RQ3_10/descriptions/RQ3_10_experiments.md),
with separate scope_v2 artifacts. v1 remains blocked with0 model calls; its
zero-eligibility result is not retroactively qualified. v2's negative-evidence
mechanism is limited to the23 directly qualified AIOPS2022 cases; inference
uses the same140-case whole roster without eligibility filtering.

Date: 2026-10-01. Latest user authorized CPU/GPU qualification followed by
remaining preparation/formal inference **after passage**. Single-agent, local
Qwen only. No GPU server, smoke call or formal request was initiated.

## Actual checks

- Synthetic CPU regressions passed after repairing an invalid test fixture:
  the mock renderer evidence needed both the CanvasEvidenceV1 schema and a
  nonempty card. Production source data and scientific inputs were not changed.
- Prepared the three preselected smoke identities, using committed full public
  caches and one targeted Metrics projection. Times: 1.52s, 2.03s, 3.89s.
  Only three cases were prepared, not the140-case formal roster.
- Three-case CPU checks exercised all six request paths, equality, actual
  offline tokenizer/image processor, and durable states. First execution7.30s;
  maximum input28,342tokens plus registered8,192output fits40,960context.
  Scope-specific CPU report is cpu_smoke.json, not whole-roster cpu.json.
- Inspected the actual rendered MATRIX PNG:1800×7894, many unshown/unknown
  cells, excessive common-cell whitespace. Automated DOM equality/overflow
  passes do not establish useful or efficient visual representation.
- Since none of these three cases had a qualified scope comparison, audited
  the entire public140-case roster before any GPU use. This reads existing
  full public contexts/selected Metrics columns, not raw logs/traces, private
  labels, model answers or full dashboard preparation. Eight physical-core
  workers completed in21.88s.

## Full-roster source audit (not model performance)

| Dataset | Cases | No eligible base resource anchor | Selected observations | Active observations | Testable scope cases | Soft-conflict cases |
|---|---:|---:|---:|---:|---:|---:|
| AIOPS-2022 |60|44|32|0|0|0|
| AIOPS-2025 |60|10|455|0|0|0|
| AegisLab |20|19|2|2|0|0|

All489 selected observations receive insufficient_coverage under the current
registered rule. No diagnosis scores were used in this audit. No inference
outcome or MRR is inferred from these counts.

| Dataset | Median finite reference/current samples | Median coverage | Maximum coverage |
|---|---|---:|---:|
| AIOPS-2022 |29/11|0.6042|0.6250|
| AIOPS-2025 |16/16|0.5000|0.6087|
| AegisLab |26/7|0.5000|0.5000|

## Causes, evidence and impact

1. **Temporal qualification definition does not fit acquisition density.**
   measure() in RQ3_10/src/exps.py counts occupied bins against64 common bins
   and requires80% occupancy in each phase. Native30–40 total source samples
   cannot fill that grid. The implementation follows the registered rule;
   the rule incorrectly treats structural oversampling as insufficient
   observation. This is a protocol/design defect, not proof the source has
   widespread NaNs. Do not invent samples or silently reduce80% to make it pass.
2. **Resource whitelist and base-anchor contract suppress applicability.**
   AIOPS-2022 contains container-prefixed readings such as
   container_cpu_load_average_10s and container_fs_usage_MB./dev/vda1; Aegis
   contains container.memory.working_set and k8s.pod.memory.working_set.
   The current exact whitelist does not include these source keys. Also,
   Aegis selected base anchors are often request-latency observations, not
   resources, so merely expanding the whitelist would not create an anchor.
   Counter/state readings cannot be relabeled as gauges to avoid this limitation.
3. **Activity is not observable at the same granularity everywhere.**
   Smoke AIOPS-2022 has144 cached Trace observations bound to pods, but its
   selected resource readings have no qualifying pod activity binding.
   Smoke AIOPS-2025 has23 Trace observations bound to services; that cannot
   establish individual-pod activity. Its source also has request/response
   metrics, but their unverified semantics do not qualify as the two registered
   monotone counters. No activity definition is silently widened.
4. **Layout is geometrically valid but unnecessarily sparse.**
   Fixed480px record slots plus the fullest cell applied across the Cartesian
   grid leave most of the7894px image blank. This compounds token/readability
   risk; a DOM pass alone is not visual qualification.

These jointly remove the proposed experiment's principal intervention from
all140 cases. Running the full matrix now would measure largely no-ops,
unknown annotations and an unnecessarily large board, not the proposed
qualified conflict mechanism. Synthetic test passage does not cure this.

## Disposition and proposed next revision

Qualification is **blocked**, not passed. CPU implementation/three-case
capacity checks passed; whole-roster CPU capacity, useful visual qualification,
GPU smoke and formal inference remain unexecuted. The earlier static-only
status is historical; the current blocker is established source applicability.

Before further inference, a separately registered revision should:

- define coverage relative to demonstrated source acquisition cadence, retain
  the80% data-quality criterion, and keep comparisons on compatible public
  windows; do not interpolate unobserved facts into existence;
- verify exact per-case gauge semantics and units, then decide explicitly
  whether resource anchors may be nominated from the already-present entities
  when their selected base metric is not a resource;
- audit direct per-instance activity at source granularity. Service aggregate
  traffic must never be spread across all its pods. Unsupported controls stay
  unknown; if activity is unavailable, narrow the hypothesis rather than
  pretend the negative-evidence experiment is viable;
- use compact shared cell geometry for MATRIX/TILES together, preserving
  their equal footprint/glyphs, with real PNG inspection.

These are load-bearing measurement/selection/representation decisions, not
an operational threshold tweak. They require explicit protocol revision; this
session does not change those scientific assumptions to force qualification.

Authority: RQs/RQ3_10/results/scope_v1/qualification/eligibility_audit.json;
cpu_smoke.json; preparation_smoke.json; actual renders beneath
RQs/RQ3_10/preparation/scope_v1/renders/. No LLM/VLM calls spent.
