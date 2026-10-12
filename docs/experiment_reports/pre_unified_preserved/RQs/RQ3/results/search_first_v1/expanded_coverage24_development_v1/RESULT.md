# SEARCH35 — More entity coverage does not recover diagnostic accuracy

2026-09-12. Completed **train-only exploratory paired comparison**,12 cases
per AIOPS dataset, exactly SEARCH33/34's additional cohort. No validation,
480-case eval, attention, Composer inference or training.24/24 requests ended
normally, each with five distinct allowed IDs. No infrastructure/schema errors,
timeout or output truncation; maximum343 output tokens.352.461seconds.

## Intervention and qualification

Replace SEARCH34's native24 metric ranking with the existing greedy entity-first
coverage rule, retaining24 metric slots and public membership. Each slot prefers
an unseen owner, then an unseen metric-name family, then native rank/stable ID.
No native ranking formula is rewritten. The production addition only exposes
coverage with the same public membership projection used by the reference.

The mean number of selected metric owners rises9.667→24 for AIOPS2022 and
13.583→24 for AIOPS2025. All24 fact inventories and actual PNGs change.
R/L selection, source values/windows, candidates/order, prompts, renderer,
request recipe and scorer remain unchanged. Selected-entity rules can change
G/onset/membership rows. This is a policy intervention, not an equal-information
modality contrast. All diagnostic evidence remains in one3996×4088 PNG;
candidate enumeration is prompt-only.

254 CPU tests pass, with24 source/selection/projection/prompt/geometry audits
and six coverage/native PNG byte replays. Three actual dense/sparse images
were viewed. The audit initially overconstrained the order of source metadata
after artificially reversing the pool. Ordered selected IDs, complete payloads
and per-field order were unchanged; the corrected check is documented in the
gallery's AUDIT_CORRECTION.md. No production behavior or model call was changed
to repair that audit. All270 frozen dependencies match after inference.

## Paired outcomes

| Dataset | n | Native24 MRR | Coverage24 MRR | Delta | Repair / break / tie | Holm p |
|---|---:|---:|---:|---:|---|---:|
| AIOPS2022 |12|.423611|.277778|−.145833|3 /6 /3|.710938|
| AIOPS2025 |12|.298611|.225000|−.073611|1 /3 /8|.710938|

Pooled24 MRR .361111→.251389; four repairs,nine breaks,11ties. Pratt p values
are .355469/.5; paired dz=−.216569/−.191113. Tests form the registered
exploratory two-dataset family, not confirmatory evidence after repeated search.
The observed deterioration does not establish a population-wide negative effect.

| Dataset | Coverage AC@1 /3 /5 | Coverage AVG@3 /5 | Input, both | Image tokens, both | Output native→coverage |
|---|---|---|---:|---:|---:|
| AIOPS2022 |.250000 /.333333 /.333333|.277778 /.300000|17754|16002|252.083→253.083|
| AIOPS2025 |.166667 /.250000 /.333333|.222222 /.250000|17649.5|16002|261.167→253.083|

Full fault/granularity strata and metrics: metrics_breakdown.json. All48 paired
original records, request/image hashes, complete conversation persistence and
standalone granularity-aware scorer recomputations pass. All24 new full answers
were read; the complete B324 conversation was additionally inspected end-to-end.

## What the negative result reveals

Direct root-associated metric/trace/log coverage rises18→23/24 (A22 11→12;
A25 7→11). Five cases gain an owned telemetry row, and none loses coverage;
only C0 among those five improves its rank. Fifteen cases still miss top5 despite
having such a row. Owner association is not proof that the selected row exposes
the fault: coverage can retain an uninformative metric while missing the actual
diagnostic feature. The evidence does not support maximizing owner count alone.

Representative complete-answer observations:

- **C0,0→1:** coverage restores node1267 evidence; the answer cites CPU/free
  memory. It still overstates moderate utilization as exhaustion and infers
  infrastructure causality without a depicted hosting edge.
- **BAC,0→1:** the answer combines pod-owned timeout logs and latency evidence,
  rather than elevating unrelated node variation. Its claim that a descriptor
  fall24→21 is a high-magnitude resource fault is nevertheless unsupported.
- **CC8,1→0;33C,1→0;7CE,.25→0:** the earliest-onset list and normalized deviation
  dominate the public reason. CC8 ignores the still-displayed node1523 CPU
  evidence.7CE treats z−1/start-of-recording ordering as an initiating-fault cue.
- **740,0→0:** a GC-duration change9.8e−5→9.9e−5seconds is called massive/severe
  because z is large. This is not a token limit or failed response.
- **B324,.5→0:** the model reads47.3%→47.3% and explicitly invents a
  display-truncation/near-ceiling explanation to call it resource exhaustion.
  The true node's telemetry is selected but not ranked.
- **17BB,0→0:** an available-memory increase11.2G→14.7G is described as a sharp
  drop and reinterpreted as used memory. This contradicts the metric meaning.
- **00B,1→0;CD9,1→0:** different selected context induces an application/pod
  story while the accepted component remains outside top5. Public membership
  is sometimes mistaken for stronger causal or co-location evidence.
- **BF5,1/3→1:** the correct service is ranked first, but the explanation
  alternates between origin and downstream-slowness hypotheses. A correct rank
  is not sufficient evidence of a correct causal account.

The three visual inspections retain an existing weakness: sparse F911 uses a
large G panel for a few onset/member rows, whereas dense metric labels are small
and long names wrap/shrink. The present run deliberately did not alter layout;
therefore it does not measure whether adaptive area allocation would help.

## Decision

Do not promote coverage24. Keep native24 as the same-cohort reference and preserve
all negative outcomes. More owner coverage is not a sufficient selection target.
Next work should separate feature diagnosticity and visual prominence from raw
coverage: investigate counter/gauge semantics, misleading normalized peaks and
onset priority, and unnecessary empty-space allocation with explicit, label-blind
successor interventions. No per-case private answer may determine a selection
rule, prompt or rendering correction. Do not repeat an already tested variant
under a different name. The target remains unmet; no full eval or SFT/RL starts.

Protocol: RQs/RQ3/descriptions/RQ3_experiments.md, SEARCH35. Immutable sources:
private/source_snapshot.tar.gz. Batch spec:
fefe1864af65394cef3897c150446a4f663af414ab132e2f129017f6fd10b78f.

