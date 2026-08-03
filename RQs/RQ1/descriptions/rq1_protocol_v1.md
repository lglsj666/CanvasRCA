# RQ1 protocol v1: representation value through operation-aware access

## Research question

> **RQ1. Under equal evidence access and matched investigation budgets, when
> and how does visual-text, topology-aware observability provide incremental
> value for VLM-based root-cause analysis?**

This protocol operationalizes the project-wide representation-value question
without attempting to turn the completed static RQ0 result into a positive
result. The authoritative roadmap is [RQ1RoadMap.md](RQ1RoadMap.md).

## Scope and sequence

RQ1 is intentionally staged. A later stage may not run merely because its code
exists.

1. **RQ1a — static redundant augmentation.** The completed RQ0 result is the
   historical answer: attaching a static dashboard to lossless full-information
   text did not produce a stable accuracy benefit. It is retained as a negative
   result and is not rerun here.
2. **RQ1b — modality-specific visual utility.** Build `RCA-VisOps` from
   label-blind incident evidence. Measure exact lookup, temporal scanning,
   topology/path reasoning, cross-modal alignment, and missingness under paired
   text, visual, and bounded-hybrid views. Then estimate the individual and
   interaction effects of visual metrics, logs, and traces/topology.
3. **RQ1c — operation- and context-aware routing.** Only after RQ1b establishes
   complementarity, compare matched-plan all-text, routed visual-text,
   always-both, and visual-dominant investigation.
4. **RQ1d — causal visual utilization.** Only after the routed observer passes
   its development gate, apply semantic visual-tool-result interventions and
   style-preserving shams, measuring perception, ledger, and diagnosis shifts.

The original static implementation milestone prepared RQ1b contracts and
reusable interfaces without authorizing inference. The versioned
`rq1b_visops_mapping_v1` amendment now authorizes only the registered
exposed-development mapping run after its renderer qualification, runtime
freeze, and partition-aware smoke pass. It still does not authorize training,
opening a new heldout split, or making a confirmatory efficacy claim.

The CEBv1 compatibility adapter is deliberately not an executable evidence
store by itself. The implemented
`CanonicalEvidenceStoreV2WithDenseLogAndTraceTimeSlices` combines its qualified
64-bin metric facts with complete relative-time log, trace-service, and
caller-to-callee trace-edge bins, explicit zero coverage, complete graph edges,
and derived paths. Raw trace correlation IDs and absolute clocks exist only
inside the one-way narrowing step and never enter a public store. Static checks
prove compiler and contract behaviour; execution still requires a frozen
exposed roster, representative perception qualification, registered hashes,
power analysis, and smoke qualification.

## Information-equality contract

Every paired view is materialized from one immutable `QuerySpecV1` and one
ordered atomic-fact inventory. The following are mandatory and fail closed:

- the entity scope, relative time range, aggregation, precision, units,
  missingness, candidate ordering, directed edges, and multi-hop facts are
  identical across representations;
- every semantic atomic fact has a stable `fact_id`, provenance hash, and
  per-arm location in the audit sidecar; model inputs expose the same semantic
  fields while `source_pointer`, provenance hashes, and `derived_from` lineage
  remain evaluator-only so they cannot become text-only evidence;
- after duplicate encodings within an arm are ignored, text, visual, and hybrid
  inventories are exactly equal;
- a legend such as `A -> B means A calls B` never substitutes for the incident's
  concrete edges;
- a summary such as baseline/peak/onset never substitutes for the complete
  queried sequence when the visual view contains its shape;
- missing evidence remains explicit and cannot be silently dropped or filled
  differently by an arm.

For prompt-composition audits, `A` is the complete visual evidence fragment and
`B` is the complete text evidence fragment after the common system/task shell.
The bounded-hybrid user content is frozen as **exactly `A+B`**, preserving part
order, bytes, image hashes, and duplicates. It is never rewritten, summarized,
or deduplicated.

## Label-blind construction

The task compiler may read only `CaseRenderView` or a previously qualified
label-blind CEB. It must not accept a labelled `DataCase` as a renderer or task
selection input. Root labels and accepted aliases may be loaded only by a
separate evaluator after model output has been persisted.

Model-visible prompts, PNG/OCR text, view manifests, and metadata must exclude:

- raw case IDs and dataset names;
- root cause, accepted aliases as labels, or correctness annotations;
- fault type and any label-derived selection or ordering;
- absolute/injection timestamps and absolute file paths;
- private roster fields or source filenames.

Opaque incident IDs, candidate service names, relative bins/times, units, and
label-blind telemetry-derived summaries are allowed. Automatic VisOps answers
are derived only from the supplied atomic facts; root labels are never used to
construct a task, distractor, view, or answer.

## RCA-VisOps contract

Each task stores:

- `QuerySpecV1` and its hash;
- an ordered `AtomicFactV1` inventory and inventory hash;
- a deterministic question and machine-verifiable answer;
- a text artifact, a visual PNG plus primitive manifest, and exact location
  maps for both;
- the fixed prompt fragments `A`, `B`, and `A+B` with hashes;
- leakage and parity audit status.

Task families and intended controls are:

| Family | Operations | Expected role |
|---|---|---|
| Exact lookup | metric value, log/trace count, exact edge | text-favouring negative control |
| Temporal scanning | earliest onset, longest persistence, recovery/order | plausible visual advantage |
| Topology/path | edge direction, observed multi-hop path | plausible local graph advantage |
| Cross-modal alignment | entity-by-modality evidence alignment | plausible aligned-view advantage |
| Missingness | missing-vs-normal and coverage | uncertainty qualification |

No task is required to exist for a case whose source evidence cannot support a
unique, deterministic answer. Such a task is omitted by a frozen eligibility
rule, never repaired with a label or case-specific manual choice.

## Later matched-plan interface

The provisional `EvidenceLedgerV2` interface is frozen early so that RQ1b
outputs can feed RQ1c without changing their meaning. It records selected and
cited `fact_id`s, representation source, temporal relations, concrete directed
edges, candidate support/opposition, conflicts, and missing evidence. The
validator rejects unknown facts, unknown candidates, uncited claims, and any
label-bearing key.

Stage 2 diagnosis will eventually read only a validated ledger, the candidate
inventory, and the common task shell. It will not reread the original image or
text evidence.

## Execution and status gates

The checked-in configuration remains `execution_enabled: false` until all of
the following are frozen in a versioned amendment:

1. an exposed-only development roster and exposure-ledger lineage;
2. operation eligibility and sample-size/power analysis;
3. renderer/view version and visual inspection qualification;
4. prompt fragments, schemas, scoring, parsing, exclusions, and hashes;
5. model/checkpoint/tokenizer and canonical vLLM effective configuration;
6. a partition-aware smoke plan and artifact inventory.

Static checks and read-only rendering of a few real cases are qualification
work, not experiment results. They must use temporary output locations and
cannot populate `results/` or support an efficacy claim.

## Validity status

- `RQ1a`: completed historical negative result; status is unchanged.
- `RQ1b`: exposed-development VisOps mapping registered; no result yet. The
  independent gate and all downstream stages remain blocked until the frozen
  mapping rule exists and passes its own gate.
- `RQ1c`: blocked by the RQ1b complementarity gate.
- `RQ1d`: blocked by the routed-observer development gate.
- `src/`: frozen and intentionally empty until the final RQ1 solution is
  approved for submission.
