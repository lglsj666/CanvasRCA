# CanvasRCA consolidated devlog

This is the only project-wide devlog. It keeps decisions that still affect the
current study, important reversals, validity changes, and reproducible artifact
locations. Repetitive operational narration and superseded execution plans were
removed on 2026-09-15. Detailed experiment records remain under each RQ's
machine-local `results/`; settled RQ1.1/RQ2.1 findings and retained incident
records are under `docs/`.

## Current authority — 2026-09-15

- CanvasRCA runs locally only. The `_nibi` worktree name is historical; no new
  Slurm/Nibi jobs or API inference are authorized.
- The first paper uses a frozen one-stage RCA Solver and studies evidence
  selection plus verifiable visual organization. Composer SFT/RL is deferred.
- RQ480 is the repeated-exposed method-development/selection eval set. It is
  not optimizer training data and is not an untouched test set.
- The registered data roles are train300 / eval480 / test360 / unused1403.
  Test contains 120 cases each from AIOPS-2022, AIOPS-2025 and AegisLab; all
  RE2 cases remain in eval. The former AIOPS validation140 is included in test
  with its exposure provenance retained. There is no active validation split.
- The current research plan is
  `docs/CanvasRCA_Research_Plan_2026-09-15.md`. It authorizes planning and the
  completed CPU-only split registration, not a model run.

## 2026-07 to 2026-08 — foundation and invalidated predecessors

The repository established deterministic dashboard rendering, label-private
case views, case-local service/pod/node identifiers, unified scoring, token
accounting, resumable writers, and local vLLM recipes. Early RQ0/RQ1 work tested
text, flat, visual and mixed representations, plus several routing/two-stage
ideas. The routing and early multi-stage routes did not provide a stable gain
and were abandoned for the first paper.

All model-call results produced under the old `vllm-inference-v1` contract were
later archived as invalid for scientific claims. That decision did not alter
CPU-only renderer/data artifacts and did not rehabilitate failed or incomplete
runs. Qwen3.6 was removed from the active study; Qwen3.8-27B and
Gemma-4-26B-A4B-it became the registered frozen Solvers. Local recipes remain
model-specific and unquantized.

The project temporarily used Nibi/H100 and local hardware interchangeably.
Operational differences and preparation drift made the workflow difficult to
audit. The project subsequently standardized on local execution and stopped
using Nibi. Historical cluster scripts may remain as code provenance, but they
are not execution authority.

## 2026-08 to 2026-09 — RQ1.1

RQ1.1 narrowed the paper to one-stage RCA and tested text, screenshot, full
vision and modality-selective visual arms, along with direct QA and a bounded
counterfactual mechanism study. Image and text attention were recorded for the
completed historical experiments, but attention is treated only as a
correlational diagnostic.

A raw-to-processed consumption bug was found: an earlier consumer omitted
fields present in the source schema, weakening pod/node/process evidence. Old
derived experiments affected by that processor were cleared rather than
silently reinterpreted. The SIRCL-compatible processor was moved into the
project, made self-contained, tested against the reference transformation, and
used to build canonical V3 per-case data and the frozen RQ480 roster.

The valid RQ1.1 rerun found that visual representation can improve some RCA
arms and reduce input tokens, but full vision is not uniformly best and output
tokens do not automatically decrease. Topology-selective vision was a strong
Qwen condition. Effects varied by model, dataset, fault type and root
granularity. Direct QA exposed perception and formatting failures, but QA
accuracy— including root-connected questions—had weak association with RCA
ranking. Counterfactual inputs showed that the Solver does use visual evidence,
while also revealing shortcut and ranking failures. The consolidated numbers,
figures and caveats are in
`docs/RQ1_1_RQ2_1_findings/findings.md`; implementation incidents are retained
under `docs/issues/`.

## 2026-09 — old RQ2 abandoned and RQ2.1 completed

The first RQ2 implementation introduced a new renderer/design pipeline without
a strict RQ1.1 bridge. Its named tool profiles also collapsed to identical
model inputs, so the tool comparison could not identify tool effects. RQ2 was
abandoned in full; its source remains historical, while generated results were
removed after a retirement audit. This failure is retained because it directly
motivated input-identity checks and fixed anchors.

RQ2.1 restarted from the RQ1.1 P0 bridge and separated three interventions:
evidence selection, silhouette encoding, and canvas composition. It evaluated
both Solvers over RQ480 with fixed anchors rather than claiming a sequential
champion was globally optimal. Results showed that evidence selection matters,
but many new designs did not beat P0; encoding/layout effects were conditional
and often model-specific. Resolution and density did not yield a universal
monotonic optimum. Tool arms were audited at the actual-request level so
same-input reuse could not masquerade as an intervention. The authoritative
findings are merged with RQ1.1 in the single findings document above. RQ2/RQ2.1
operational pitfalls remain in `docs/issues/`.

## 2026-09 — RQ3 historical training branch and elimination tournament

A Qwen3.5-9B dashboard Composer was prototyped with a structured card/silhouette
DSL. Format SFT reached update 320 and improved schema/binding/render success
relative to the base model, but this did not establish downstream RCA benefit.
The proposed full RL lifecycle was therefore not promoted into the first-paper
main line. Checkpoint retention used latest-plus-every-20 during that historical
run. No current plan resumes those checkpoints automatically.

The subsequent elimination tournament explored complementary evidence
selectors without training. Each round ran only cases not previously solved by
that model; union coverage therefore measures the combined reach of many
attempts, not deployable single-call accuracy. After 38 committed rounds the
user stopped the tournament. AC@5 union coverage reached 96.7%, while persistent
AC@1 failures and many top-five-but-not-first cases pointed to competition
between plausible roots and ranking errors. The only tournament report is
`docs/Tournament_Analysis_2026-09-15.md`; it records per-round methods,
AC@1/3/5, covered/uncovered case profiles and the proposed contrastive selector.
No further tournament round is authorized.

## 2026-09-15 — RQ3.1 research direction and data roles

The new first-paper direction is a deterministic, contrastive evidence
compiler for a frozen one-shot Solver. It compares competing root explanations
using public telemetry and represents selected evidence as text, compact text,
screenshot or a real dashboard. The goal is high MRR plus grounded entity,
temporal and relational evidence—not visual novelty alone. Training is a
conditional later extension only if a fixed method first establishes useful,
case-dependent design actions.

The earlier proposal for a wholly unexposed 480-case test was infeasible with
the available AIOPS pools and was superseded by explicit user instruction.
The accepted versioned registration uses:

| Dataset | Train | Eval | Test | Unused |
|---|---:|---:|---:|---:|
| AIOPS-2022 | 150 | 100 | 120 | 171 |
| AIOPS-2025 | 150 | 100 | 120 | 30 |
| AegisLab | 0 | 100 | 120 | 1202 |
| RE2-OB | 0 | 90 | 0 | 0 |
| RE2-TT | 0 | 90 | 0 | 0 |
| **Total** | **300** | **480** | **360** | **1403** |

All 2,543 identities occur exactly once. Old train and RQ480 identities are
unchanged; all former validation140 are in test. Five CPU tests, deterministic
byte checking, independent public/private partition comparison, protected
source hashes, and Aegis source/event/window reconstruction passed. Active
train/eval/test event-window group crossings are zero. Public rows expose only
dataset and opaque ID. This accepts the data registration only; no telemetry
row, model call, renderer, smoke, training or formal experiment ran.

Artifacts:

- `RQs/RQ3_1/configs/data_split_v1.json`
- `RQs/RQ3_1/results/data_registration_v1/summary.json`
- `RQs/RQ3_1/results/data_registration_v1/registration.json`
- `RQs/RQ3_1/results/data_registration_v1/private/split.json`

## Persistent validity and operating rules

- Labels, root cause, fault type, absolute injection time, raw case identity,
  dataset name and paths remain evaluator-private and never enter model-visible
  evidence.
- Candidate identities are case-local numeric aliases. Scoring is
  granularity-aware: service predictions may resolve hashed pod aliases, while
  pod/node labels remain exact.
- Full conversations, requests, outputs, per-case metrics, failures and costs
  are recorded asynchronously for every future experiment. Infrastructure
  failures are not model-quality failures; parse/format failures remain model
  outcomes under the registered policy.
- A real dashboard, pixel screenshot and pure text are distinct. Selection must
  change actual evidence, while representation twins must preserve their
  registered semantic facts.
- Completed historical results retain their original validity class. A new
  verifier or operational rule cannot silently invalidate accepted evidence or
  rehabilitate invalid evidence.
- New inference uses local project-owned vLLM only. Model scientific settings
  remain frozen unless a new versioned experiment explicitly changes them.
- Temporary analyses belong under ignored `tmp/`; generated results, renders,
  attention, checkpoints and conversations stay machine-local and ignored.

## Current next step

Finish RQ3.1 method/interface registration and bounded CPU qualification using
the current research plan. Freeze the method before using the 360-case test.
Do not restart the abandoned RQ2, tournament, Composer SFT/RL, Nibi execution,
or model inference without a new explicit authorization.
