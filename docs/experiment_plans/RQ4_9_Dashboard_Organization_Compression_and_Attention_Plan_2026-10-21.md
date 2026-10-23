# RQ4.9：视觉证据的组织、压缩与注意力分配如何影响 RCA

Status: user-approved implementation, 2026-10-21. This protocol is prospective;
qualification and scientific results are reported separately. No qualification is
inferred from this document. Machine-readable registration:
`RQs/RQ4_9/configs/protocol_v1.json`.

## 1. Research decisions and common inputs

Improve pure-visual and hybrid ranking while explaining when organization,
compression and attention allocation help. All RCA conditions make one model
call. No agentic, preliminary selection, or multi-stage diagnosis. Hybrid is
explicitly authorized for this experiment; Codex.md is unchanged.

The latest 论文主线.md marginal-graph question is addressed within the eight
organization conditions, not by adding near-duplicate experiments. The study
has 23 RCA conditions, 220 exposed development cases (60 AIOPS-2022, 60
AIOPS-2025, 100 AegisLab), and at most 6,000 actual calls including qualification
and recovery. No training or additional model is introduced.

### Evidence-to-design review

| Historical evidence | Decision |
|---|---|
| RQ4.1 U MRR .3517 vs V_FULL .2209 and T_FULL .4846 | Keep protected anchors and deterministic spatial E50 as the common compression starting point. |
| RQ4.8 HASH_PACK .2918 vs BALANCED_PACK .2597 | Coverage proxies are not performance guarantees. |
| RQ4.8 TIME_RESTORE .4705 vs BOTH_RESTORE .4616 | Fix facts within organization comparisons; more facts need not improve ranking. |
| RQ3.16 MARGINAL_FIVE .5054 vs markless .4963 | Separate the full method from the incremental contribution of point glyphs. |
| Historical U already contains marginal plots in 211/220 cases | This is not the first use of marginal plots in pure vision. |
| RQ4.5 DOMAIN .3302, SOURCE_UNIFORM .3105, CONTEXT_FILL .3208 | Domain controls have historical precedents; reuse their conceptual role, not claim novelty. |
| RQ4.1 feature diversity and RQ4.6 neighborhood/value support did not beat U | Do not rename and rerun these selectors. |
| RQ4.8 QA has verified prose extraction false negatives and p50/current answer imbalance | Versioned offline rescoring and a new balanced, visible-answer QA contract are required. |

RQ4.8 completion authority is its formal phase marker and final analysis, not
its stale findings text. Historical U, T_FULL, MARGINAL_FIVE and H_MARGINAL
answers/cost are reused, without baseline regeneration. Historical comparisons
are engineering references, not synchronous causal comparisons. Claims in the
paper are bounded by the tested data, representations and budgets; exhaustive
dashboard search is neither required nor intended.

### U28

New images are exactly 4096×4096, with at most 28 panels including the complete
candidate directory and public observation window. Start from frozen U public
sources, not newly fetched telemetry. Preserve those two mandatory panels and
the existing at-most-two marginal relations, selecting source records and their
necessary statistics/bindings as indivisible groups. Fill remaining capacity in
M/R/L/G rounds and stable original source order, protecting available node/resource
coverage from complete disappearance. Skip whole groups that do not fit; record
every exclusion. Do not truncate records, alter number spelling, merge panels
under one outer frame to evade counting, or describe this as retaining every
historical fact. Actual processed diagnostic fonts are >=18px and lines >=1.5px.

A denotes protected identity/name/unit/phase anchors. E denotes registered
optional evidence support excluding A. q=ceil(|E|/2). U28 keeps A and q E positions
using the historical deterministic spatial farthest-point rule, not randomness.
The new pixels and selected facts make U28 a necessary new baseline, not an
identical rerun of historical U.

## 2. RCA conditions

| Arm | Change / question |
|---|---|
| U28 | Common selected dashboard with protected-anchor E50. |
| V_BIND_LOCAL | Put entity/statistic/unit/phase labels beside their observations. |
| V_BIND_KEY | Same labels/counts/graphics in a card-local keyed legend. |
| V_MARGINAL_DIRECT | Explicit local source/phase/statistic binding; separate samples, population p50/p95 and conditional statistics. |
| V_MARGINAL_MARKLESS | Same as DIRECT, remove only sample and quantile point glyphs. |
| H_MARGINAL_DIRECT | Complete paired sources only in the improved graph; remaining facts retain strong-text organization. |
| H_MARGINAL_MARKLESS | Same text/layout/numeric labels, remove only point glyphs. |
| H_TPV_BIND | Full topology exclusively in directed node-link plots; nearby typed endpoints. |
| H_TPV_KEY | Same topology/labels/counts, use a keyed binding legend. |
| F_LOCAL_MEAN | Protect A; spatially group E within cards and output q averaged embeddings. |
| F_SOURCE_MEAN | Additionally require compatible source/signal/unit/statistic/phase. |
| F_SOURCE_REP | Same groups and representative positions, retain original representatives without averaging. |
| F_SOURCE_SHAM | Same representative positions/group sizes; fixed permutation exchanges nonrepresentative members. |
| P_SCOPE_E50 | Actual attention saliency × coverage, alpha=1, selecting q only from E; protect A separately. |
| P_SHAPE_E50 | Retain real line turning/endpoints and bar endpoints; fill remaining q with U's rule. |
| P_FULL | All image tokens; shared control for sink conditions. |
| P_DOMAIN | Only A union E; no additional E pruning. |
| S_VIS_REDIST | Reallocate candidate-sink mass to other image positions. |
| S_EVID_REDIST | Same donor mass, reallocate to A union E. |
| S_SUPPRESS | Same attenuation, global renormalization without image-specific recipients. |
| S_SHAM_REDIST | Transfer the same mass from matched ordinary background to A union E. |
| D14_FIXED | At most 14 complete panels from U28, original positions/pixels. |
| D14_PACK | Identical selected panels, deterministic reflow and enlargement. |

V_MARGINAL_DIRECT and H_MARGINAL_DIRECT are the highlighted organization
candidates. All other optimization arms remain fully registered. The three
independent-repeat conditions are U28 and these two candidates.

### Organization and marginal controls

Retain historical relation selection, at most two relations and 32 real samples
per phase. Distinguish sample readings, population quantiles and conditional
statistics. Bind parent/child, operations, reference/current, duration type and
unit locally. Add no statistics and do not interpret parent-minus-child duration
as local execution time. Reuse complete_marginals/phase_marginals capabilities;
add explicit operations only for demonstrated missing capabilities, preserving
historical defaults. Markless retains values, axes, labels, positions AND the
marked arm's exact token indices/count. It tests point glyphs, not all visual
information. Organization pairs have identical selected facts. Hybrid retains
strong residual text without RQ4.6 series/sample compression. All values and
derived summaries from one source are assigned to exactly one carrier; linking
IDs/units/phases may repeat. Without qualified pairs, marginal pairs share the
corresponding base input and explicitly record no intervention. Rendering and
capacity errors are not data-inapplicability fallbacks. Pure/hybrid total source
sets can differ; do not interpret their difference as a pure carrier effect.

### Fusion

All fusion arms use the U28 PNG, protect A, and output q E slots. Allocate one
slot per nonempty compatible group, then use Hamilton largest remainders by
remaining group capacity. Use deterministic spatial farthest seeds and nearest
seed assignment; ties use original indices. Pick the original token nearest the
group centroid as the representative position. Accumulate means in FP32 and cast
to BF16; preserve original representative position encodings and order. Shared
tokens use their complete support signature and count once. Never average A,
insert zeros or silently mix incompatible groups when group count exceeds q.
That condition blocks qualification. SHAM keeps representatives and group sizes,
permuting other members with one frozen seed. It changes spatial and semantic
composition and is not a pure semantic-only intervention.

### Pruning

SCOPE uses actual penultimate vision attention, not a norm proxy. Restrict its
coverage objective and choices to E; protected A does not count as E coverage.
This materially differs from the historical off-domain choices and is a Qwen
adaptation, not a claim of exact original-model reproduction.

SHAPE starts from rendered geometry. Line endpoints precede iterative largest
perpendicular reconstruction error, normalized by primitive bounding-box
diagonal. Bars contribute endpoint supports. Select complete support groups by
error recovery per new token, tie by source and index; skip groups exceeding the
remaining budget and complete q using U. Do not modify the rendered line, fill
missing observations, use private labels or historical answers. DOMAIN-FULL and
U28-DOMAIN separate domain exclusion from further E deletion on this new canvas.

### Attention intervention

Sink arms use P_FULL pixels and all tokens. Preserve the Qwen full-attention
layers 3,7,...63, its linear attention, native gate, weights, BF16 and RoPE.
At layer3 use the final eight public instruction queries. A background position
outside A union E is a candidate if its image-normalized density is >=5 times
uniform on >=6 queries. Freeze that set within the call. It is operationally
defined, not already proven harmful. Apply operations to text queries at full
layers3..59, leaving layer63 unchanged. Eligible heads have image mass>=.2 and
nonsink fraction>=.8. Release exactly .4 of donor mass. Recipients receive mass
proportional to their existing probabilities. SUPPRESS globally renormalizes.
SHAM uses fixed-hash ordinary background donors with the same removed mass.
Insufficient donor/recipient support gives a shared nonintervention for that
head, not an alternative threshold. Never delete BOS, instructions or diagnostic
text. No candidate means an audited no-op. Use stable grouped weighted-value
reductions, not retained full attention matrices. Measure actual overhead.

### Density

Both density arms retain the directory/window and <=14 panels including them,
as a source-complete subset of U28. FIXED preserves surviving pixels/positions;
PACK changes display size/density only. This is one 28/14 tradeoff, not a search
for an universally optimal card count.

## 3. QA and attention measurements

Fixed hash, event-diverse 27 cases, nine per dataset, across every RCA condition.
At most six independent single-answer questions per request: value, entity,
statistic, unit, phase comparison, relationship. Freeze targets before method
outputs. Balance available p50/p95/reference/current categories deterministically
and report majority-class baselines and applicability; never manufacture facts
to force balance. Use visible locators without revealing queried identities.
Every oracle is nonempty and backed by actual visible input at display precision.

The oracle-blind tolerant receiver accepts code fences, minor JSON damage and
unambiguous prose. Filter invalid question IDs individually; do not wipe valid
answers. Format and correctness are separate. Conflicting answers cannot be
selected using the oracle. Required-value questions score1 for a complete valid
solution, .5 for a nonempty correct proper subset without wrong extras, otherwise0.
Keep raw output, extraction paths, accepted alternatives and scorer versions.
Versioned historical QA rescoring never overwrites old scores or regenerates
answers. Keep >=80% semantically single-answer questions in every required slice.

Three extra U28 QA controls per case: isolate complete target cards without
changing canvas/target pixels/registered token positions; exchange complete
compatible source units with labels and unchanged answers; exchange compatible
statistic labels everywhere and register new synthetic answers. No RCA on the
synthetic inputs. Inapplicability is explicit, not replaced with favorable cases.
Report target retention, conditional QA, and end-to-end coverage separately;
partial token deletion is not automatically complete information removal.

Read actual QA-RCA answers on the fixed subset: wrong number, wrong real source,
unit/statistic/phase error, correct reading not used, and reason/ranking conflict.
Explanations are observable statements, not privileged internal reasoning. 27
cases per condition do not establish independence from nonsignificant correlation.

Attention records layers3/23/43/63, last prompt and first decode query only.
Separate instructions, hybrid evidence text, labels, data marks, title/background;
record mass, region counts and per-token density. Sink audits additionally store
candidate set, transfer mass, eligibility and no-op rates. <=64KiB/call and <=1GB
decimal per10,000 calls including mappings. No full matrices or replay calls.

## 4. Calls, statistics and decisions

| Module | Maximum |
|---|---:|
| 23×220 RCA |5060|
| 23×27 QA |621|
| 3×27 QA controls |81|
| 3×30 independent repeats |90|
| 3×18 specialized smokes |54|
| Infrastructure recovery |94|
| Total |6000|

Formal scientific calls <=5852. Repeat subsets have10 cases/dataset and contain
the nine QA cases. Exact generation identities reference answers; independent
repeats generate afresh. Unused budget does not authorize new arms.

Event-group Pratt-zero Wilcoxon is primary; case-level analysis is secondary.
Round differences to12 decimals, report paired dz and no CI. Separate Holm
families, exactly as frozen in protocol_v1.json:

- Organization: V_BIND_LOCAL-U28, LOCAL-KEY, V_MARGINAL_DIRECT-U28,
  pure DIRECT-MARKLESS, hybrid DIRECT-MARKLESS, H_TPV_BIND-H_TPV_KEY.
- Fusion: LOCAL_MEAN-U28, SOURCE_MEAN-U28, SOURCE_MEAN-LOCAL_MEAN,
  SOURCE_MEAN-SOURCE_REP, SOURCE_MEAN-SOURCE_SHAM.
- Pruning: SCOPE-U28, SHAPE-U28, DOMAIN-FULL, U28-DOMAIN.
- Attention: VIS-FULL, EVID-FULL, EVID-VIS, EVID-SUPPRESS, EVID-SHAM.
- Density: D14_FIXED-U28, D14_PACK-D14_FIXED.

QA controls form a separate family. Fields/questions/references do not increase
independent n. Pre-register public source-confusability, shape support, topology
branch/shared-node density, marginal overlap, background/sink mass, card count
and processed font features. Input-only thresholds freeze before calls. Fault
type and root granularity are evaluation-only. Strata with<20 event groups are
descriptive. The proposed chain is intervention -> reading/binding -> observed
diagnostic use -> repairs/damage -> cost, not assumed causal mediation.

Pure-visual engineering target: >=+.02 MRR vs U28, no per-dataset MRR/AC@5 drop,
prefer actual input+output <=1.05 U28. Hybrid: maintain/exceed historical .4912,
and >=10% total-token saving vs T_FULL on each dataset. Expensive improvements
are reported as tradeoffs, not cost reductions. Admit whole-method progress even
if component attribution is weaker. No partial-MRR tuning or unregistered search.
Report standard/tolerant MRR, AC1/3/5, Precision, AVG, macro/per-dataset scores,
repair/damage, invalid/unknown/full denominators, repeats and actual costs.

## 5. Qualification, execution and retention

Implement DashboardStudyPacketV1 and VisualOperatorPlanV1; reuse QAItemV2 with
versioned receiver repairs. All RCA scoring imports scorer. All graphics use
src/renderer and additive opt-in operations; historical behavior and missing-gap
connections stay unchanged. Five functional modules, <=7500 functional lines.

Sequence: static -> complete220 CPU -> independent operator/runtime regressions
-> <=6 new manual image views -> three specialized GPU smokes -> frozen formal.
CPU checks complete source unions/ownership, candidates, geometry, masks, fusion,
pruning, attention conservation, actual processor limits and QA answer contracts.
Input+8192<=40960; image tokens<=16384. CPU success never asserts GPU correctness.
No-op and independent small-tensor checks preserve gate/linear state/RoPE/order.
Verify batch isolation, commits, references, true repeats and power-loss resume.

Each smoke has18 calls and900 seconds: organization/hybrid, operators/attention,
and QA. Together cover all paths, three datasets, longest request and persisted
inputs/outputs/scores/cost/attention. Incorrect answers are not method-tuning gates;
software/measurement errors must be fixed. Gates cannot be lowered or arms silently
removed to manufacture qualification. Heavy CPU preparation precedes GPU launch.
Local BF16 Qwen/vLLM,8 physical-core workers, concurrency8, memory utilization.8,
bounded RAM queue. Hash case order and balanced arm rotations. Trust atomic commits
on resume; never regenerate completed answers merely after reboot.

Retain directly readable exact inputs/images/prompts/outputs/conversations, score
contexts, operations and all collected attention, with verified immutable
deduplication. <=25 decimal GB/10,000 actual completed calls, attention<=1GB.
Keep resume dependencies until writers drain. No archives or hidden compression.
Final report separates engineering progress, supported attribution, unestablished
explanations and applicability/negative findings. Execution remains locked until
its source-bound qualifications pass.

### Accepted literature and adaptation boundaries

- [VisionZip, CVPR2025](https://github.com/JIA-Lab-research/VisionZip): context
  aggregation motivates mean-vs-representative controls, not lossless compression.
- [SCOPE, NeurIPS2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/ec6b4456c2bdfd04002d7984043c4936-Abstract-Conference.html): actual saliency and coverage; our E-only Qwen adaptation is explicit.
- [Catch, Tag, Release, NeurIPS2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/77cd5a17edf97293eab706caf9bfee39-Abstract-Conference.html): sinks may perform useful functions, so high background attention alone does not establish harm.
- [Visual Attention Sink/VAR, ICLR2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/da8a39bc39ae1c89dd6ebb1e3bcbb3f3-Abstract-Conference.html): head-selective redistribution; no transplantation of other models' hardcoded activation dimensions.
- CharXiv (NeurIPS2024) and MultiChartQA (NAACL2025): visible-target, answer extraction and task separation inform QA; no model judge is introduced.
- RAR (ICLR2026) is not treated as an already qualified training-free plugin:
  its reported training schedule is not reproduced here.
