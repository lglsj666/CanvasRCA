# RQ4.1 remaining CPU regression — v6

User authorization: complete the remaining CPU test implementation, launch its
background audit, then stop the interactive turn. No GPU smoke, model service,
language-model request, further feature extraction or formal queue is started.
This supplement implements the existing protocol; it does not relax its gates.

## Previously completed prerequisite

The v5 encoder, public covariate and final selection audits completed on all
220 cases. The twelve current selectors produced 2,640 qualified selections.
CVC_E50 versus REWIRED_E50 differs on 60/60, 59/60 and 99/100 cases. Reuse these
committed artifacts. They establish CPU feasibility, not diagnostic performance.
The existing statistical calibration remains uncalibrated; independent
confirmation remains not-run. New code does not overwrite the earlier records.

## Frozen remaining inputs

`configs/remaining_cpu_v6.json` records a deterministic 90-case mechanism
roster, 30 per dataset, rotating event groups then hashes before outcomes.
`configs/remaining_logical_inputs_v6.json` enumerates 6,100 development,
repeat, QA and intervention positions; it is not an execution credential.
The 2,400 conditional-confirmation positions remain disabled. No calls have
been initiated by these CPU manifests. Original 8,900/12,000 call accounting
is unchanged. Independent repeats use a separate seed namespace and never
reference another answer. Case/condition hash order is frozen.

Two linked QA blocks select visible scalar reference/current pairs of the same
entity, signal, quantity and unit. Both operands must have an unambiguous original
text occurrence as well as a public source binding. Deterministic anonymous
1A/1B and 2A/2B badges do not encode phases, entities, units or answers. Targets
are selected before rendering; placement failure is a failure, not permission
to pick an easier pair. Unavailable blocks are recorded as inapplicable. Scoring
uses the original exact value within half the last displayed decimal unit;
comparison uses the displayed values. Six questions remain two joint blocks.
The answer tuples stay in audit files, never model-visible questions.

POSITION rotates the existing equal-width columns without changing component
sizes, candidate order or facts. BINDING swaps a fixed eligible pair of same-kind,
same-unit/type entity captions. OPERAND changes one fixed source scalar in all
its compiled aliases. IRRELEVANT changes a header glyph with matching original
scalar DOM bounding-box area, not matching ink area. These last three do not
retain the original RCA label as a valid answer for the corrupted input. All
images are re-encoded for eventual inference; base cached features cannot be
reused for altered images. No intervention feeds a subsequent RCA call.

The independent CONTRAST_ATLAS preserves every original card and adds the
registered linear-interpolation p10/p50/p90 changes, reference MAD/IQR scale,
observed-peer differences and shared asinh color scale. Ambiguous duplicate
peer measurements do not become a silently reduced peer population: the peer
channel is inapplicable and the ambiguity is retained in its public audit.
Original evidence is preserved in that case. Fixed entity rows use the original
candidate order, original component width and sufficient row height. Failure to
fit the 8192 by 8192 canvas makes the wildcard unavailable, without dropping
facts, shrinking fonts, adding an alternative design or reassigning calls.

## Necessary additive unified-renderer interfaces

- `contrast.quantile_contrast`: metric heatmaps have time-axis semantics, while
  diagnostic matrices encode prediction/residual channels. Neither expresses
  empirical quantile versus self/peer channels. A distinct typed component
  carries entity, signal, quantity, unit and all six derived-value bindings.
  This is the concrete registry name for the protocol's proposed quantile-strip
  addition; it does not modify `comparison.paired_observations` or historical
  component behavior.
- `qa_badges`: existing owner/edge bindings do not anonymously identify two
  original scalar glyphs for independent QA. The new operation locates actual
  DOM scalar bounds, rejects obscured placements and audits all badge positions.
- `control_glyph`: explicit matched-bounding-area irrelevant-header perturbation
  for the registered control. It carries no observation or candidate value.

These interfaces activate only when explicitly requested. Default rendering is
checked by exact PNG redraws from all three datasets. Header DOM geometry is
added to the audit manifest for passive text/image attention classification;
this metadata is not painted into ordinary dashboards. Attention categories
include explicit mixed cells and do not claim to identify a token's semantic
contents.

## CPU stages and failure states

1. Frozen-source/static checks, full RQ unit tests and unified-renderer browser
   regressions, including the additive component and disabled model entries.
2. Complete source and original-card parity for 220 cases; actual processor
   budgets, source-derived quantiles, peer medians and registered variant
   geometry. QA and interventions cover the fixed 90 cases. Per-case atomic
   completion records and progress are saved as work finishes.
3. Outcome-free QA calibration on its applicable case/group structure. A failed
   statistical calibration is retained and cannot be rescued by a different
   inferential procedure.
4. Published-pruner compatibility. G-Prune is compared with its frozen official
   expression on small tensors, then checked on cached real Qwen features with
   the registered 30-second/2-GiB selector limits. The official LLaVA code has a
   split global/tile sequence and newline handling; Qwen has one projected grid,
   which is explicitly recorded. Unexpected implementation errors fail the
   audit; resource incompatibility is a not-run status. SCOPE requires an actual
   saliency signal not supplied by the current projected-feature path. DART and
   S2Prune need distinct mid-decoder hidden-state/recurrent-cache operations that
   the current pre-decoder gather does not qualify. Their unqualified paths are
   explicitly not-run, not norm/diversity surrogates under published names.
5. Default PNG compatibility and actual processor/DOM attention-region mapping.
   Tensor-only adapter identity, batch permutation/padding, native-generation
   state restoration, atomic reply/marker recovery, reference versus repeat,
   invalid-answer commitment, duplicate startup and pause draining use offline
   stubs. They cannot certify real-weight cache parity, attention speed or GPU
   inference. Those remain bounded-smoke requirements.

The runner uses four persistent workers on different physical cores (at most
eight physical cores overall), starts different source/cloudbed groups first,
hides CUDA and forces local/offline model-processor loading. An aggregate
24-GiB RSS guard and the ORIGINAL v4 eight-hour wall-clock deadline are retained;
this supplement does not reset that clock. The external supervisor cleans up
its own surviving children if the audit exits or times out.

A failed prerequisite stops dependent checks. Individual rendering/variant
failures stay in per-case reports. Inapplicable controls and unqualified priors
are not represented as successful model paths. Actual visual inspection of new
examples remains pending after the background run: automated geometry checks
alone do not constitute human review. `cpu_qualified` remains false until that
review and all required CPU failures are resolved; GPU parity is a later,
separate qualification. No automatic activation follows CPU completion.

## Monitoring and durable outputs

`results/comparison_coding_v1/cpu_remaining_v6/` contains `runner.log`,
`pipeline.status`, `status.json`, `progress.json`, stage logs/results, per-case
inputs and PNGs, source freeze and final `qualification.json`. An early failure
can legitimately leave later stage files absent. Inspect `pipeline.status` and
`status.json` together. The interactive agent stops after confirming startup.

## User-directed dependency repair and central scorer — v7

The user stopped v6, required removal of external RCA source dependencies,
retained all previously passed CPU checks, and designated `src/scorer/` as the
only scoring import path for new work. Historical scorer/RQ2.1 files remain
byte-identical and have NO newly added forwarding aliases. The new scorer
contains copies of existing project code; it imports neither an external RCA
checkout, the historical scorer modules, nor a historical renderer.

RQ4.1 now imports from `scorer`. Its transaction helper also avoids importing
RQ2's utility module just for a writer, because that module imports the old
scorer at module load. It uses the existing atomic JSON writer and a bounded
standard-library worker instead. This changes dependencies/persistence wiring,
not model inputs or score semantics.

The current v7 continuation configuration is disabled. It retains 41 successful
v6 unit tests, all 37 renderer tests, the 220-case source/processor/support and
feature checks, and all 2,640 successful selector checks. The next authorized
queue runs only the failed transaction test and the new central-scorer import
regression before the still-unperformed QA/intervention/atlas/compatibility
stages. It does not rerun passed tests to refill a new report. All v6 failures,
source snapshots and pause markers remain intact. A fresh source freeze is
required before any later authorized runtime, without resetting the original
budget clock or silently converting static checks to runtime qualification.

This edit performs source-only checks. No tests, GPU calls or services are
started. Status remains paused; the new import regression is written but pending.

## Authorized v7 continuation — 2026-10-06

The user now authorizes restarting the remaining CPU tests. This lifts the v7
execution pause above for CPU work only. Preserve all previous passes and failed
records. Run the two pending repair checks first; a failure stops dependent
work. Then process the registered remaining QA/intervention/atlas and compatibility
checks. Use four workers pinned to distinct physical cores, the same 24-GiB
aggregate memory guard and the original v4 deadline without resetting it.
Freeze the repaired source, central scorer and continuation configuration before
startup. GPU smoke, model calls and formal execution remain disabled. The
interactive agent confirms successful startup and then stops for user monitoring.

## Authorized QA/atlas continuation — v10, 2026-10-06

After inspecting the repaired gallery, the user requests continuing CPU
validation. `remaining_cpu_v10.json` and `cpu_remaining_v10/` are the forward
configuration and output. Keep v6/v7 failures and frozen sources unchanged.
Retain the 41 original unit passes, 37 renderer passes, two v7 scorer repair
passes, and all completed primary encoder/selector checks. Retain 240 atomic
per-variant passed receipts (QA 9, POSITION 60, BINDING 59, OPERAND 56,
IRRELEVANT 56), including fully completed variants from interrupted cases.
Validate their small receipt and evidence/design identity without reopening
PNGs or recomputing processor/support. Ordinary graphics are unaffected by the
QA fallback; already-successful QA overlays preserve the original placement.

Run new atlas layout, retained-result integrity and dense QA badge regressions
before the cohort. Recompute CONTRAST_ATLAS for all 220 cases under its
explicit layout amendment; old infeasible results are not current passes.
Rerun failed QA and perform uncompleted variants. Keep the original CPU clock,
four workers on distinct physical cores, offline CPU processing and 24-GiB
aggregate RSS guard. On the first failed case stop dispatch, drain only its
already-running peers, and skip dependent stages. No GPU or model follow-on is
enabled. This resumption does not claim CPU qualification before completion.
