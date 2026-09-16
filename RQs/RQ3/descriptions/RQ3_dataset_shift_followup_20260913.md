# Dataset-shift analysis: applicability and next search directions

Date: 2026-09-13. User-supplied offline analysis was read during round 9.
Round 9 stays unchanged; no new method is qualified or executed by this note.
Source: `tmp/dataset_shift_analysis_v1/report_zh.md` and `analyze.py`.
The other agent's files remain unmodified.

## What was actually checked

The report reads `/home/lglsj/CanvasRCA/dataset/processed`: 541 AIOPS-2022,
361 materialized AIOPS-2025 and 90 cases in each RE2 set. Current RQ3 config
uses `build/local_processed_v3`, whose manifests contain 541/400 AIOPS cases,
1,422 Aegis and 90/90 RE2. This verifies different input roots/counts, not
byte-equivalence of overlapping cases. The current tournament is its frozen
480-case subset, not the report's 1,082-case population.

The report's old root-candidate deficit cannot be assigned to the current
tournament: `diagnostics_through05/private/evidence_audit.json` checks all 480
current pools against the actual granularity-aware scorer. Every case has a
score-acceptable candidate and root-associated M/R/L somewhere in its pool.
The source pool and candidate policy remain unchanged through round 9.
This is an evaluator-private diagnostic, never a label-derived candidate patch.

The report's selected-root coverage tables come from older report assets,
not current tournament selections. Through round 5, 49/215 unretired primary
Qwen cases and 50/212 Gemma cases had never received root-associated direct
telemetry in an executed method. Conversely 166/162 had, but still lacked a
top-1 success. These are that historical tournament snapshot's counts, not
updated round-9 counts. Ownership alone does not prove a diagnostic signal.

The time criticism needs component-level interpretation. `score_series` still
uses the inherited first-half baseline for panel scoring. Native BARO/MA use
`metric_normalization(...).analysis_window`, inferred from public telemetry,
not automatically the first-half split. No in-flight change is justified by
assuming every component has the same baseline.

The report's classifier features include `event_fraction`, computed from
source event timestamp. Its proposed `timestamp < 0` boundary is centered on
the source event anchor. Relative formatting alone does not establish that
this is an independently observed incident signal. Do not silently inject
that boundary or private onset into this tournament's public-derived clock.
Likewise private `key_observations` counts suggest modalities worth examining,
but are not proof that every listed modality is necessary for each answer.
Do not export these hints, root labels, dataset names or classifier to a
selector/Solver. Domain classification does not prove fixed methods cannot
work, and random case folds do not establish unseen-event-group transfer.

## Search implications

1. **Candidate/metric-family coverage before extra similar curves.** Current
   top-24 images often allocate many lanes to similar JVM/memory series for
   one entity. Compare public candidate-wise/family-wise budgets and novelty
   against global top-k, retaining actual values and strict pod/node identity.
   The objective is different fault signals, not merely a larger card count.
2. **Several public change episodes rather than one largest peak.** Explore
   data-derived change points and time-ordered cards, using physical elapsed
   duration rather than the same bin count across sampling rates. Preserve
   competing episodes and long sustained changes without consulting injected
   onset, fault duration, nearby-event labels or dataset identity.
3. **Cross-source ownership bundles.** Link a selected entity's metrics,
   trace ownership, log templates and publicly supported service/pod/node
   relations in one evidence card. Current outcome reviews repeatedly show
   cross-owner rate attribution and operation-prefix/owner confusion. A
   stronger bundle is a testable representation hypothesis, not a prompt edit.
4. **Availability-aware modality allocation.** Public connectedness, observed
   span coverage, source sampling, unit semantics and template novelty can
   inform budget choices. Sparse observed call graphs are not evidence that
   all edges are absent; routine high-volume logs should not monopolize L.
5. **Counter semantics.** Monotonic counters/uptime may dominate mean-shift
   ranking without identifying a fault. A versioned rate/delta experiment
   needs explicit instrument semantics and reset handling; not every monotone
   series is a counter. Preserve source provenance and do not change units
   or derived quantities in an existing method.

These are successor hypotheses, not claims of measured benefit. First review
the recorded training-subset exploration to avoid relabelling an old method,
then qualify substantial changes on small, separately registered shrinking
cohorts for both models. Preserve fixed RCA prompt/scorer and all prior
success/failure records. No training during the tournament, no new attention.
Root-associated evidence recall is useful privately but is not a perfect hard
gate: an indirect upstream/downstream pattern may diagnose a root without its
own displayed row. Do not select examples by label-derived recall to present
an inflated method result.

## Provenance

- Report SHA256: `cc61ed9f157ec2d9cad952fb6e7ccdecc59212d4da750d64e8f9198db819c548`.
- Script SHA256: `16b80e18175802bc95055da8fbeb0920233b6e26d0c2058c1bca7da2196e9a5a`.
- Verification SHA256: `11d77feff036510c8f8ccd264b7515e596b5beb9b80bd6974270c3b71b010202`.
- Current-pool offline audit SHA256: `8b8162bf2eb0b004f9fa1c053b23441ac94689e9783190c0a70518d909166867`.

No report conclusions have been copied into an executable selection rule.
Detailed private-source review remains offline; current round inputs, configs,
models and preparation are unchanged.
