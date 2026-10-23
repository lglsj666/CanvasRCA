# RQ4.8 — Card selection, hybrid evidence recovery, and valid QA

Implementation registration, 2026-10-20. This records the user's approved
RQ4.8 design and the subsequent tolerant-receiver amendment. Status is tracked
in `RQs/RQ4_8/findings/exp_card_selection_findings.md`; registration is not a
claim that qualification has passed. No changes to Codex.md are authorized.

## Purpose and authority

Improve root-cause ranking while controlling actual deployment cost. In parallel,
establish valid measurements of evidence availability, reading, attribution, and
diagnostic use. The user explicitly authorizes hybrid and two-call methods for
this round, overriding the older prospective restrictions for this experiment.
One-call visual diagnosis remains an independent route with its own nominee.

The empirical questions are when reduced visual context helps, when it removes
necessary evidence, and how selection, display, and information completeness
contribute. Card IDs, cropping, hybrid transport and two calls are not themselves
claimed innovations. No training or model substitution is registered.

Historical constraints:

| Evidence | Decision |
|---|---|
| A_UNIFORM_E50 (U), MRR .3517, remains the historical visual reference | Keep its evidence, graphics, anchor protection and E50 rule |
| RQ4.4 HD supplements and RQ4.7 single-call workspaces did not improve ranking | Test removal/repacking; stage two receives no original overview |
| RQ4.7 coordinate actions were difficult to execute | Select visible card indices, not estimated coordinates |
| RQ4.5 H_MARGINAL .4912; RQ4.6 H_MARGINAL_PHASE .4590, particularly weaker on AegisLab | Restore time series and pair samples separately |
| Historical QA had empty answers, unclear localization and scoring defects | New question, visibility, prompt and scoring contracts; old low QA is not mechanism evidence |
| Correct numbers can coexist with wrong owners or contradictory rankings | Report reading, binding, ranking and explanation correctness separately |

Reuse historical RCA answers/costs for U, T_FULL, MARGINAL_FIVE, H_MARGINAL,
H_MARGINAL_PHASE. Never regenerate their whole RCA cohorts. Do not restore
deleted RQ4.7 M-condition data. All 220 cases are exposed development data:
60 AIOPS-2022, 60 AIOPS-2025, 100 AegisLab. Candidates, central scoring semantics,
five distinct ranked candidates and the frozen public evidence corpus persist.

## Accepted literature and limits

- [SeeRepo, ASE 2026](https://conf.researchr.org/details/ase-2026/ase-2026-research-track/33/LLM-Agents-Can-See-Code-Repositories): structure/exact-content division; interactive coding savings do not establish single-call RCA savings.
- [Visual Sketchpad, NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/file/fb82011040977c7712409fbdb5456647-Paper-Conference.pdf): bounded visual operations, without executing arbitrary model code.
- [Visual Haystacks, ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/a264726ebd222124514a32bf0143b83d-Abstract-Conference.html): distinguish retained targets, distractors and position effects.
- [CharXiv, NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/hash/cdf6f8e9fd9aeaf79b6024caec24f15b-Abstract-Datasets_and_Benchmarks_Track.html), [official prompts](https://github.com/princeton-nlp/CharXiv/blob/main/src/constants.py): explicit visible referents and answer semantics; do not adopt a model judge implicitly.
- [MultiChartQA, NAACL 2025](https://aclanthology.org/2025.naacl-long.566/), [official code](https://github.com/Zivenzhu/Multi-chart-QA): separate reading, comparison and composition; distinguish generation and extraction.
- [Visual Attention Sink, ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/da8a39bc39ae1c89dd6ebb1e3bcbb3f3-Abstract-Conference.html): attention is a measurement, not proof of causal use or harmful sinks. No sink intervention here.

## Card contract and display operations

Map the existing visible numeric indices to original cards, sources, DOM geometry
and visual support. Preserve these indices after selection; never renumber.
Only the complete candidate directory, public observation window and required
reading information are protected. Diagnostic summaries are selectable even when
their renderer component is named `inventory`.

All operations use `src/renderer/` and preserve existing component defaults:

- FIXED: erase rejected cards to background; surviving pixels, positions, sizes
  and canvas remain identical.
- PACK: deterministically compact the same complete cards, in original relative
  order, with original graphics, numeric strings, font sizes and indices.
- Each retained card keeps its entity, unit, phase, axes and necessary legend.
- Record each removed card/source/support. Removal is not lossless compression.
- Use original U anchor protection plus E50 except the explicit A-union-E control.
- FIXED inherits U's processed readability limitation. PACK cannot make retained
  diagnostic text smaller after processing. No shrinking fonts or changing processor
  pixel limits. Missing observations retain the existing connecting-line semantics.

## Eleven main arms

| Arm | Definition |
|---|---|
| S_HASH_PACK | Frozen-hash selection and compact display |
| S_BALANCED_FIXED | M/R/L/G round-robin, prioritizing uncovered entities; erase unselected cards in place |
| **S_BALANCED_PACK** | Same balanced set, compact display; single-call nominee |
| M_ID_FIXED | Model-selected set, erase other cards in place |
| **M_ID_PACK** | Same model-selected set, compact display with E50; two-call nominee |
| M_MATCHED_HASH_PACK | Hash set matched to model count, modality and area strata; same compactor |
| M_ID_PACK_FULL | Exactly M_ID_PACK pixels, retaining every registered A/E token |
| H_NATIVE8 | RQ4.6 eight-sample projection, existing complete-marginal drawing |
| **H_TIME_RESTORE** | Phase marginal/eight samples; restore original complete core and AUX time series; hybrid nominee |
| H_PAIR_RESTORE | Compressed time series; restore original up-to-32 paired samples per phase |
| H_BOTH_RESTORE | Restore both time series and paired samples |

Single-call selectors keep ceil(one half of optional diagnostic cards). HASH and
BALANCED have the same count and modality quotas. No anomaly magnitude, private
label, past answer or QA error enters selection. Stable hashes resolve ties.
FIXED versus PACK evaluates a display change including position, density and
processed scale; it is not a single internal causal mechanism.

Two-call stage one sees the complete U dashboard and chooses any number of cards.
There is no half-count requirement. All four conditions share this actual selection
call; each method's logical deployment cost includes it in full. Stage two is an
independent request containing only the executed dashboard and generic instructions.
It receives no first-stage image, explanation, temporary ranking or conversation.
Keep-all is valid and recorded as no pruning. Exact request identities may reference
the same answer; references are not independent samples. Matching does not imply
exact token-cost equality; report actual differences.

Hybrid restoration uses frozen evidence, preserving original values, units,
missing positions and observation multiplicities. Pair samples/statistics belong
only to the image, other diagnostic facts to text; join labels may repeat. Use
the corrected carrier instructions. No eligible pairs means the applicable
remaining text without an image, not a topology fallback. Rendering/capacity
failure is not data inapplicability.

## Tolerant receivers — explicit user amendment

Both card selection and QA use tolerant, deterministic extraction **before**
execution/scoring. Canonical selection is `keep_card_indices`, but accept fenced
or wrapped JSON, numeric strings, documented aliases, unquoted keys, trailing
commas, explicit comma/bullet lists and complete entries in an unambiguous
truncated list. Extract only from answer fields, explicit final answers or a
single unambiguous list, never arbitrary numbers in explanations.

Deduplicate and filter invalid IDs individually. Preserve valid entries. Multiple
equivalent normalized lists are acceptable; conflicting lists without an explicit
final answer are ambiguous. Keep/delete contradiction is semantic, not a formatting
typo. Do not infer intended IDs, use labels, or call a repair model.

If no valid **diagnostic** card remains, terminate the method, do not make stage
two, and count the case as model failure with zero ranking score. No overview
fallback. Infrastructure failures remain unknown. Preserve original text, strict
format validity, extraction path, discarded values/reasons, normalized selection,
actual image and costs. Report tolerant executability separately from strict format.

QA uses the same tolerance policy for format and question/answer IDs. Unknown IDs
are removed before scoring; they cannot invalidate unrelated valid answers.
IDs occurring as actual requested answer content are checked against the public
answer domain, independently of the oracle. A valid but wrong ID remains wrong.
No parser may inspect accepted correct answers to choose a parsing interpretation.

Two distinct QA semantics:

1. **Alternative solutions:** answering any one complete allowed solution earns 1.
2. **Required multiple values:** the complete required solution earns 1; a nonempty
   proper subset containing a correct value earns **0.5**, including one correct
   value. No correct value earns 0. Retain exact/full correctness separately.

For a multi-value question, wrong in-domain extras do not receive credit: report
them and withhold full credit. Joint values must match one registered solution,
not an invented Cartesian product of fields. Partial credit is an explicit
question-level scoring policy, not permission to fuse contradictory answers.

## Valid QA and mechanism measurements

Freeze 60 cases, 20/dataset, hash-selected with distinct event groups prioritized.
Run independent QA on eleven new inputs plus U, T_FULL, H_MARGINAL and
H_MARGINAL_PHASE. These are new QA answers to new questions, not repeated RCA.
At most six questions: displayed value, owner, statistic, unit, same-definition
phase comparison, and direction/cross-card comparison. Prefer single-answer
questions; multi-answer questions stay at or below 20% per dataset/condition/global.

Mandatory contracts:

1. Nonempty typed answer and source proof; numeric zero is not empty.
2. Actual submitted image/text contains the answer or all comparison operands.
3. Locate by visible card index, field and statistic; no guessed coordinates or hidden phase terms.
4. Ownership questions do not supply their own entity answer.
5. Score displayed precision, registered unit aliases and equivalences, not hidden raw precision or blanket percentage tolerances.
6. Accept all legal alternative solutions, preserving joint solution structure.
7. Independent QA prompt/schema; no five-candidate RCA instruction inheritance.
8. Format and content are separate; one malformed item does not erase others.
9. Oracle-free extraction; conflicting answers are never resolved by correctness.
10. Save questions, raw answers, displayed strings, accepted solutions and scoring versions.

Freeze semantic targets before card selection. Removed targets are availability
loss, not ordinary answerable-reading questions and not replaced by easier ones.
Report target retention, conditional QA with retained support, and end-to-end
evidence-answer coverage. Partial token support is distinct from whole-card removal.

Three mechanism controls, up to one call each per case:

- Isolate complete target cards with original canvas, pixels and processing scale.
- Exchange compatible complete sources; indices/semantics move together, oracle unchanged.
- Exchange compatible same-unit/same-phase statistic labels, synchronizing all
  copies and deriving a new oracle. Synthetic QA only, never true-label RCA.

CPU qualification enumerates applicability first. Inapplicable controls remain
N/A, not zero effects; do not substitute cases after model outcomes. Review all
60 paired QA/RCA answers, and label additional repair/break case studies post hoc.
Separate wrong readings, wrong real sources, unit/statistic/phase mismatch,
correct observations unused, reason/rank contradictions and support deletion.

Attention uses the existing lightweight collector on actual calls only: first
registered full-attention layer, last prompt query and first decode query. Record
selection/final/QA stages, image card/title/background and instruction/diagnostic
text regions; normalize by region token counts. These are not ranking-field
queries. No replay or attention intervention. Per-call summaries <=64 KiB;
all attention plus mappings <=1 decimal GB per 10,000 completed calls.

## Calls, inference and reporting

| Allocation | Maximum |
|---|---:|
| 11 main arms x 220 final diagnoses | 2,420 |
| Shared first-stage selection x 220 | 220 |
| 15 inputs x 60 QA | 900 |
| 3 QA controls x 60 | 180 |
| Three nominees x 30 independent repeats, two-stage repeated fully | 120 |
| Three independent smokes x 18 | 54 |
| Recoverable infrastructure interruption reserve | 106 |
| **Total** | **4,000** |

Formal research maximum is 3,840 actual calls before reuse/inapplicability.
Unused calls do not authorize new arms. Committed wrong answers are not retried.

Pure-visual primary Holm family (six): S_BALANCED_PACK−S_HASH_PACK;
S_BALANCED_PACK−S_BALANCED_FIXED; M_ID_PACK−M_ID_FIXED;
M_ID_PACK−M_MATCHED_HASH_PACK; M_ID_PACK−S_BALANCED_PACK;
M_ID_PACK_FULL−M_ID_PACK. Hybrid primary family (two):
H_BOTH_RESTORE−H_TIME_RESTORE; H_BOTH_RESTORE−H_PAIR_RESTORE.
Event-group two-sided Pratt-zero Wilcoxon is primary, with case-level analysis,
12-decimal differences, paired dz, no CIs. QA mechanisms have a separate family;
questions/fields are not independent case replicates.

Engineering goals, not CPU qualification outcomes:

- Single nominee: >=.02 MRR over U, no dataset MRR/AC@5 decline, actual total tokens <=1.05 U.
- Two-stage nominee: >=.03 over U and better than contemporary single nominee; complete two-stage costs <=1.05 T_FULL per dataset.
- Hybrid nominee: aim >=.4912 MRR and >=15% total-token saving over T_FULL in each dataset.

Report standard/tolerant MRR, AC@1/3/5, Precision, AVG, macro/dataset results,
repairs/breaks, invalid IDs/actions/formats, all failures/unknown bounds, repeats
and actual costs. Include both stages, repeated encoding, rendering and wait time
in deployment accounting. Historical backend/time differences remain explicit.

## Qualification, execution and retention

Static checks precede CPU qualification, then three separate reviewed smokes,
then the frozen formal queue. A pass in one smoke never qualifies another.
Local BF16 Qwen/vLLM, existing ranking decode, 8 independently pinned CPU workers,
GPU concurrency 8, utilization .8; no Nibi work. Heavy input preparation precedes
GPU runs. Online stage-two card operations are bounded and use bounded RAM queues.

CPU covers all 220 cases: indices/protection/sources/deletions/images; tolerant
parser positive and negative cases; nonempty visible QA oracles and scorer
counterexamples; original/repacked geometry; shared token support; candidates;
atomic commits, interrupted stages, exact references and independent repeats.
Count actual processor inputs: input+registered output <=40,960; image tokens
<=16,384; each image side <=8,192. Valid selections cannot silently truncate:
execution/capacity errors block until repaired. The cumulative manual image
review allowance is 20: 13 already viewed, **at most seven new images**, no collages.

| Independent smoke | Calls | Required checks |
|---|---:|---|
| Single/hybrid | <=18 | All seven applicable arms, three datasets, longest request, actual images/scoring/accounting |
| Two-stage dashboard RCA | <=18 | Three selectors plus four finals each (15), up to three additional independent/attention/resume checks |
| QA | <=18 | Six conditions per fixed case, including visual, hybrid, selected images and controls; every prompt/input/answer/score inspected |

Each has a separate ledger and **900-second** window including startup; never
reinstate 600 seconds. No purposeless calls to exhaust allowances. Two-stage
inspection checks the actual transmitted image and no forwarded overview/history.
QA qualification checks measurement correctness, not high model accuracy. Empty
or invisible oracle, contradictory prompt, or wrongly scored correct answer blocks.
Software bugs are repaired and affected checks rerun without resetting spent calls.

Resume trusts atomic per-call/stage completion markers; do not rerun a completed
selector or bulk revalidate all old inputs. Freeze hash/balanced arm order before
formal inference; do not tune from partial MRR. Report calls/min and two-stage
cases/min separately. Formal runtime requires all qualification receipts bound
to the frozen dependencies. Entrypoints default disabled until explicitly qualified.

Retain exact inputs, images, outputs, conversations, parser audits, scores and all
collected attention as directly readable, hash-verified deduplicated objects.
Final retained footprint <=25 decimal GB per 10,000 completed actual calls;
references do not inflate denominator. No compressed archives. Keep resume
dependencies until writers drain, verify all references, then remove redundant
runtime caches. Provide conversation viewer and complete statistical exports.

Implementation is under `RQs/RQ4_8/`, five functional Python modules <=7,500 lines.
New RCA scoring imports only `scorer`; shared renderer additions are explicit and
additive. Save history differences, receiver contract, QA checklist, call ledger,
unique findings and plan-index entry. Qualification status starts **not run**.

### CPU geometry correction: processor-grid rounding

During full CPU qualification, INC-07B8919442D8 exposed a non-monotone
processor resize boundary: compacting 8192×4334 to 8192×4320 reduced the minimum
axis scale from 0.68359375 to 0.68148148. PACK now checks the actual processor
output. Only when compact canvas rounding would reduce the original display
scale, it retains the compact card positions and restores the original canvas
extent with background padding. Original card pixels, sizes, indices, evidence,
processor limits and selection remain unchanged. The actual processor check is
then repeated. This deterministic geometry correction applies to all PACK
conditions and is frozen before any model call; it does not weaken the font gate.

### QA and operational qualification corrections, before model calls

An incident with metrics but no trace/call-relation cards exposed an incomplete
question generator. If the trace/relation templates instantiate no questions,
select one metric card by a fixed public hash among cards with visible finite
baseline and peak details. Ask about the displayed peak, entity binding, literal
unit label and comparison of the displayed baseline/peak values. Corresponding
hybrid/text questions bind the same fact ID and actual visible fields. Do not
invent trace questions or empty answers, drop the case, or use its RCA outcome.
A percentile-label swap remains inapplicable without a valid percentile pair.
Existing valid targets and the fixed mechanism subset are unchanged.

Each compiled QA interface additionally checks that a CPU-only fixture containing
its actual accepted visible answers is scored correctly after invalid question IDs
are discarded. Fixture answers never enter model inputs. Runtime CPU probes also
cover the prepared QA requests and their actual attention/text/image mappings.

Operational corrections preserve the registered 900-second specialty-smoke
window across restarts, resolve cross-specialty selector references in the
conversation viewer, and isolate immutable retained inputs from writable render
cache inodes. These are not new experiment conditions or extra model calls.

## 2026-10-20 — User-authorized targeted GPU repair smoke

The user requests another GPU smoke after the artifact-review repairs and
explicitly excludes CPU regression reruns. Register `smoke_repair_v2` as one
18-call, 900-second repair window; retain the three original windows, all 48
spent attempts, original responses/scores and their frozen sources.

For each of the same three fixed eval identities, execute one new selector,
M_ID_PACK diagnosis and a true independent new diagnosis, plus three independent
QA requests (H_TIME_RESTORE, T_FULL, U): 6 positions per case, 18 total. The
selection is shared within each pair; this verifies the independent diagnostic
call/reference boundary, not the variability of two independently selected
complete workflows. No new RCA text-baseline calls are added. Do not require
correct rankings or correct QA answers for passage.

Rebuild only these smoke inputs with the corrected actual-text relation parser;
reuse unchanged source cards/images. Inspect the two previously omitted relation
questions, phase-field aliases and actual repeat call IDs after execution. Use
the same backend/model/decoding/token operations and no new manual image views.
The 18 additional reserved smoke calls are reallocated from infrastructure
recovery (106 becomes 88), keeping the 4,000-call ceiling and 3,840 formal matrix.
The prior 220-case CPU receipt and earlier offline/visual checks remain evidence
at their original revisions, with explicit source-bound inheritance; no new CPU
qualification pass is fabricated. Formal execution is not activated by this
repair scope. This amendment does not modify Codex.md.
