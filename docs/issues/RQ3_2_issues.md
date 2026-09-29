# RQ3.2 issue register

This file records implementation and operational pitfalls that can invalidate,
interrupt, or silently distort RQ3.2. Ordinary model mistakes are not defects.

## Open analysis findings — 2026-09-22

Offline analysis found the following limitations of the executed contrasts.
No experimental code, inputs, scoring, or historical status was changed.
Full evidence and result-scope discussion: [RQ3.2 report, section 10](../RQ3_2_Results_Analysis_2026-09-22.md#10-解释结果前必须明确的实现范围).

- **Confirmed no-op:** `NO_GROUPING / C_CONTRAST` retains exactly the same
  model-visible input as its baseline for every paired scored case (Qwen 96,
  Gemma 100). `compile_representation_twin` passes grouping only to renderers;
  compact text still receives the same bundles. Its score differences measure
  repeat variability, not a text-grouping effect.
- **Confirmed intervention mismatch:** `selector.select_signal_cover` gives
  `p0_more` zero P0 backbone and selects from the new pool; it is not the
  registered same-P0-order capacity-only control. The final candidate sort also
  uses strength/semantic-frequency. Keep its actual scores, but do not infer a
  pure P0 capacity effect.
- **Confirmed guide mismatch:** new carriers inherit
  `rq31_solver_read_guide`'s first-half/second-half and median/union semantics,
  while aligned contexts use the P0 public split and SC includes inherited
  P0 statistical fields. The split differs from midpoint by >1 second in
  444/480 eval and 339/360 test contexts. The contrast must not be described
  as a clean isolated selector effect under perfectly matched statistical
  instructions.
- **Confirmed narrower implementation:** C-Flat is the natural catalogue
  with comparison references, C-Contrast is the compact catalogue with
  references (not the direct comparison table); target removal removes a
  first root-associated fact; redundant noise is appended after selection.
  Interpret the real carriers/interventions, not their idealized plan names.
- **Unresolved statistical-compatibility risk:** some selected same-entity,
  same-operation traces coexist with substantially different counts/durations
  across inherited/direct sources. The report saves actual examples; it does
  not claim a single root cause without a source-data audit.

These findings do not authorize a repair/rerun. Preserve all outputs and the
negative findings; resolve the intended follow-up scope with the user.

## Resolved issues

### 2026-09-22 — Redundant-noise intervention overflowed the fixed log card

**Symptom.** Qwen mechanism execution stopped at
`INC-F1CD9B69032E / REDUNDANT_NOISE / M_TEXT` with
`RepresentationCapacityError`: the unpaired public-context log block exceeded
its measured height. vLLM was healthy before the runner's fail-fast shutdown;
the later engine-dead message was a shutdown consequence, not the cause.

**Root cause.** The evaluator-private noise intervention selected the first
twelve reservoir facts without a per-region footprint rule. Long log facts
could dominate the fixed L region. This was an intervention-construction bug,
not a reason to enlarge the controlled canvas.

**Scope audit.** A CPU-only audit of all 100 mechanism cases found five
`M_TEXT` capacity failures under the predecessor rule, all in RE2 cases. A
candidate retaining the twelve-fact maximum while limiting log additions to
two constructed 100/100 requests; 99 received twelve additions and one eleven.

**Repair.** `region_capped_v2` preserves the frozen label-blind reservoir order,
admits at most twelve facts and at most two log facts, and fills remaining
positions from later eligible Metrics/Trace facts. Canvas, resolution, fonts,
renderer geometry and processor settings remain fixed. The complete
`REDUNDANT_NOISE` condition is versioned and both representations are
re-evaluated. Byte-identical requests may reuse content-addressed results;
changed requests receive new calls. All unrelated mechanism results remain
reusable.

### 2026-09-21 — Unbounded per-case context cache exhausted WSL memory

**Symptom.** During `exp_signal_selection`, the local runner disappeared with
exit code 143 after its shell reported that the Python process was `Killed`.
GPU/server logs before shutdown contained successful HTTP responses and no
CUDA OOM or vLLM `EngineDeadError`. A Matplotlib warning about more than twenty
open figures was present, but the relevant rendering paths close their figures;
that warning reflected concurrent rendering and was not the process that the
kernel selected.

**Authoritative evidence.** `/var/log/kern.log` records the host OOM killer at
2026-09-21 01:14:19 and identifies Python PID 217567 with 45,106,408 KiB
anonymous RSS. The durable context directory contains 480 pickle files totalling
about 11.35 GiB before Python object expansion.

**Root cause.** `ContextStore` memoized every deserialized case in an unbounded
dictionary. Formal execution eventually visited nearly the complete 480-case
corpus; deserialized telemetry plus per-case runtime representation twins
therefore accumulated for the lifetime of the phase. This was an object
lifetime bug in the runner, not a prompt, evidence-selection, dashboard,
model, scorer, or source-data defect.

**Repair and prevention.** RQ3.2 now uses a thread-safe LRU capped at eight
cases. This retains reuse among adjacent arms while bounding the retained
corpus. The cap is registered and statically enforced. Regression tests must
show eviction and successful reload, and a real-context memory test must scan
the corpus without cache growth. Future threaded runners must not cache a
complete per-case corpus unless a measured memory bound explicitly permits it.
Host OOM diagnosis must consult kernel logs; an application log ending in
`Killed` is not evidence of an unexplained external WSL restart.

The post-repair real-context regression loaded all 480 durable contexts in
60.23 seconds. The cache remained at eight cases, final RSS was about 1.63 GiB,
and peak RSS was about 2.01 GB, compared with the failed runner's 45.1 GiB
anonymous RSS.

**Live recovery verification.** After the focused tests and static contract
checks passed, the formal queue resumed from its append-only terminal flags.
The first stable recovery interval advanced from 4,645 to 4,655 completed
selection units while pending units fell from 112 to 102. With 36 in-flight
workers the runner RSS was about 5.2 GB; it no longer grew with the number of
corpus cases already visited. Existing completed units were skipped by a
roughly 0.06-second journal-existence scan and were neither reconstructed nor
revalidated.

**Artifact impact.** Atomic completion and terminal-failure flags written
before the OOM remain authoritative. No completed request is reconstructed or
rerun. Only units without a terminal flag are eligible after restart; partial
files from an interrupted transaction are not spliced into a new response.

### 2026-09-21 — Missing logical flags still met stale `started` ledger rows

**Symptom.** The first post-OOM restart correctly found unfinished logical
units from the append-only resume journal, but fifteen of them immediately
raised `pending/failed call requires explicit reconciliation`. Those units had
no terminal logical flag; their model-call ledger rows had simply remained in
`started` when the kernel killed the owner.

**Repair.** At the beginning of a non-smoke model phase, after the prior owner
has stopped, RQ3.2 performs one exact-scope SQLite update from `started` to
`interrupted`. The shared transaction then recognizes the state as an
authorized retry and counts the additional attempt against the hard call
budget. It does not scan, hash, reconstruct, or modify completed artifacts.
The fifteen erroneous failure flags remain as audit evidence and receive
append-only `retry_authorized` tombstones; they do not remain scientific
terminal outcomes.

The same restart exposed one genuinely over-context `P0_MORE` pure-text
request. Following the previously authorized context-safe rule, only this
kind of exact tokenizer overflow is rebuilt by removing reverse-ranked whole
evidence units while retaining at least one unit from every populated M/R/L/G
region. The model-visible subset and removed fact IDs are recorded in the
projection. No visual request is changed, and no already completed request is
rebuilt merely because it is large.

The repaired live run crossed that unit successfully. Its durable audit is
`exp_signal_selection/capacity/9e68634f04aa7055904f2b76bbfec1ff34a5377614e3298566b008bc421a8e98.json`;
it records the original and remaining fact-inventory hashes, every removed
whole fact ID, the trigger, final projection hash, and final request hash.
