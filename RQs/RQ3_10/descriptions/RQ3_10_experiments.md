# RQ3.10 preregistration — 2026-10-01

## Active successor v2 — 2026-10-01 user goal

**Execution status:** CPU/visual/GPU qualified and complete formal matrix submitted
locally. Supervisor PID44540. Durable receipt: `../results/scope_v2/formal/submission.json`;
handoff: `../results/scope_v2/logs/2026-10-01_formal_submission.md`.
The agent stops after live queue/first-commit confirmation. No final MRR claimed.

The latest user authorizes deciding the next work, deploying repairs, completing
CPU/GPU regression and submitting the complete experiment, then stopping.
This adopts the source-based v2 repair below and supersedes the static-only
pause and pending-revision status. v1's blocked evidence remains unchanged.
Active config: `../configs/scope_competition_v2.json`; separate `scope_v2`
preparation/results. RQ3.9 remains paused. Single agent, Qwen-only, no training
or attention. Formal submission still depends on actual qualification.

**DD-RQ310-NATIVE-SCOPE: adopted.** The public140-case v1 source audit found
zero qualified comparisons because64 slots oversample30–40 native readings.
v2 defines cadence as the median positive gap of the unique public source
clock, independently of finite metric values. At least80% of source gaps must
be within0.1 cadence units of a positive integer multiple. Expected native
slots cover the full public baseline/current intervals; observed finite values
are aggregated only within phase-pure occupied slots. Keep80% finite coverage
in EACH phase,8 baseline/3 current slots,3 samples, all change/stability/MAD
thresholds, direct activity rules and unknown semantics. No interpolation or
fabricated values. The sampling cadence is inferred from the observed clock;
systematic absence of most acquisition timestamps cannot be independently
detected without collector metadata, and remains a measurement limitation.

Retain eligible base resource anchors first. If fewer than2, nominate an exact
allowlisted resource reading on an entity already displayed in a base metric
card, or its publicly mapped instance, by fixed hash, preferring instance
readings; never by anomaly, fault or prior outcome. Peer selection remains
same-key/unit/window and the existing relation-category/hash round-robin.
Add only instantaneous load/memory/disk-used keys actually present in the public
corpus. Source-specific MB/dotted names retain source_unit; no conversion or
cross-key equality assertion. Counters, limits, readiness and cumulative CPU
seconds remain in the original text and outside gauge comparisons.
Gauge-family semantics were checked against
[cAdvisor](https://github.com/google/cadvisor/blob/master/docs/storage/prometheus.md)
and [Kubelet receiver](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/receiver/kubeletstatsreceiver/documentation.md).
The local MB aliases are registered semantic inferences from their source names,
not verified collector unit conversions. Comparisons require identical keys.

Service-bound traffic never establishes pod activity. AIOPS-2025's service-only
Trace may therefore leave stable peers unknown. Shared same-direction resource
change can still supply positive support; soft-conflict claims apply only to
directly active comparable stable peers. Do not claim a general negative-evidence
test if source qualification shows that branch is inapplicable. Whole-cohort
MRR and predeclared applicability strata are both reported without selecting
eligible cases into the cohort.

Compact board:340px record slots and intrinsic per-cell heights, with row
heights bounded by their largest cell. Matrix and permuted tiles preserve each
cell's dimensions/glyphs and share a canvas sized for both layouts. Arrangement
and shared headers are the only differences. Blank cells explicitly mean
unshown/unknown. Actual DOM and PNG inspection are required.

The140 identities and three smoke identities are copied EXACTLY from v1's
immutable registration; a new version hash must not resample them. Six arms,
840 formal positions,882 formal attempts,18 smoke attempts/600s,900 aggregate
attempt ceiling,8192 output,40,960 context and statistical families unchanged.
v1 spent0 GPU calls. Preserve all later failed/partial attempts; no budget reset.
Freeze all repaired source before model calls. Full preparation and whole-roster
CPU checks may precede smoke to catch capacity/render defects before GPU use.

Qualification requires source applicability for the actual narrowed observational
mechanism, exact text/visual parity, usable PNGs, whole-roster capacity and bounded
GPU smoke with persisted artifact review. Model accuracy is never a smoke gate.
After successful submission, record process IDs, frozen hashes, logs and resume
command, then stop; do not await final scores or launch follow-up experiments.

### v2 source/CPU/visual review disposition before model calls

Prepared140 cases and280 actual boards with no design infeasibility. All intact
requests fit: maximum29,411 input +8,192 output <40,960. Renderer35 regression
tests passed, including explicit4096×3600 capacity for the64-node synthetic
fixture; old component positions were not modified. Actual native-resolution
scope PNGs inspected; deterministic real-case repeat preserves PNG/HTML hashes.

AIOPS2022:23/60 testable cases,9 service-scope and18 host-scope,327 stable-active
readings;23 cases have stable-peer shared-scope conflict. AIOPS2025:1/60 positive
scope case, zero stable-active readings/shared-stable-conflict cases. Aegis:0/20
instance-scope cases despite49 stable-active service readings. This is limited
applicability, not full cross-dataset scientific qualification of negative evidence.
The reviewed disposition under the latest user's explicit full-submission goal
is to run the unchanged bounded development cohort, retain unknowns/nonapplicability,
and restrict mechanism claims to qualified comparisons. No favorable-case
resampling or score-conditioned selection. The whole-cohort contrasts remain
the registered primary family; applicability analysis cannot replace them.

751 distinct formal requests and89 exact-request references occupy840 logical
positions. CPU-only artifacts report this before any Solver output. The
process-local runtime_io_adapter_v2 uses one8-thread writer pool with inherited
shared writer methods, preserving per-writer drain; adds case/arm/model/request
to the shared client's atomic partial_responses checkpoints; changes no model
request, output or score. One persisted logical smoke wall window prevents a
restart granting another600s. GPU smoke still required; accuracy is not a gate.

Config: `../configs/scope_competition_v1.json`. Version:
`rq310_scope_competition_v1`. Only Qwen3.8-27B, no training or Composer.

## Cohort and frozen inputs

140 exposed eval identities: 60 AIOPS-2022, 60 AIOPS-2025, 20 AegisLab. Select
by seed42/version/opaque-ID hash from the committed RQ3.8 development roster,
without labels, answers, performance or eligibility selection. Do not use
train/test/unused. Aegis is a small protection check, not generalization proof.

Preserve complete RQ3.8 ALL_ID TEXT, candidate order, public split, instructions,
sampling and granularity-aware scorer. Its lossless compacting is inherited.
Read the complete committed WitnessPublicContextV1 directory and exactly one
projected canonical per-case Metrics table, not the old selected top-k and not
raw logs/traces. Source-to-anonymous binding, sample counts and public medians
must agree. Private labels load only after public compilation/rendering.

At most12 resource series,2 retained base anchors,4 known services and3 known
hosts. Unknown mapping slots are explicit. Selection is deterministic relation
category/hash round-robin, not anomaly/outcome routing; all original evidence
survives. No eligible anchor means six identical base requests, transparently
referenced without new calls. Nonapplicability never excludes a diagnostic case.

## Qualification and scope tests

Exact metric/unit/window comparability. Source-unit values are not guessed or
converted. State/counter/configuration readings are not resource utilization.
64 common bins, samples phase-separated; finite coverage>=.8, reference>=8
bins/current>=3 bins, both phases>=3 samples. Split-overlapping bins contain
only their own phase's samples. Scale=max(1.4826*baseline MAD,.01*abs(median));
zero scale unknown. Changed: abs(delta)>=3 and same-direction fraction>=.5.
Stable: abs(delta)<=1 and max current-bin deviation<=3; stable controls also
require independently observed activity.

Direct operation requests>=5 in both matching public intervals establish
activity; otherwise exact allowlisted request counters need positive increases
in both phases and no reset anywhere, including across the phase boundary.
Unknown/inactive/missing/incomparable peers cannot become negative evidence.
Counts, operands, intervals, formulas and thresholds are visible in all
supplemental conditions. Activity is cached once per entity during compilation.

Local scope needs changed anchor plus qualified stable comparable peer.
Shared service needs same-direction changed cross-host peers; shared host needs
same-direction changed cross-service peers. Qualified stable peers supply only
soft conflict. Opposite-direction changes or ambiguous mappings remain unknown.
An anchor alone proves no scope. Node-own change supplements, but cannot replace,
cross-service instance support. Unknowns and unshown cells do not imply health.

## Registered conditions

| Arm | Input / controlled difference |
|---|---|
| BASE_TEXT | Unchanged complete inherited text |
| CONTROL_TEXT | Base plus bounded source observations, memberships, activity and qualification operands |
| SUPPORT_TEXT | Same plus qualification labels and positive support only; no negative rule text |
| SCOPE_TEXT | Same plus exact support/soft-conflict/unknown ledger and rules |
| SCOPE_MATRIX | Complete SCOPE_TEXT plus redundant signed-change cells in service-by-host coordinates |
| SCOPE_TILES | Complete SCOPE_TEXT plus identical cells/glyphs/footprint, fixed permutation, no shared headers |

All supplemental conditions share the same conditional image-reading guide;
visual requests append only one PNG, no extra guidance. Scope text and both
visual arms have identical full text/instructions, not only identical facts.
CONTROL−BASE calibrates supplementation/operands/guide jointly, not just entity
recall; SCOPE−CONTROL tests the full ledger, and SCOPE−SUPPORT is needed to
attribute any extra effect to conflict/unknown rather than positive support.

Matrix/tiles use the same DTO, precision, colors, sizes and image guide. Only
cell arrangement/shared headers differ; this is not a pure position-only claim.
Signed-change axes fixed[-6,6], overflow arrows AND exact numeric labels.
Only scope.matrix/tiles are added to the unified renderer. Old components and
operations are retained. No preview or visual qualification has yet run.

## Statistics and analysis

Primary four-comparison Holm family, AIOPS120 paired cases:
SCOPE_TEXT−CONTROL_TEXT; SCOPE_MATRIX−SCOPE_TEXT;
SCOPE_MATRIX−SCOPE_TILES; SCOPE_MATRIX−BASE_TEXT.
Secondary three-comparison family: CONTROL_TEXT−BASE_TEXT;
SCOPE_TEXT−SUPPORT_TEXT; SUPPORT_TEXT−CONTROL_TEXT.
Pratt-Wilcoxon, paired dz, no CI. Group sensitivity uses registered connected
event groups. Dataset/pooled/macro denominators distinct. Fault type, root
granularity, activity, scope applicability and conflict strata exploratory,
with explicitly separate Holm correction; include repair, break and unchanged.

Report MRR/AC@1/3/5/AVG@3/5, ranking moves, node/pod/service top1 error matrix,
illegal/duplicate IDs, candidate counts, failures and costs. Model failures
remain original zero scores. Infeasible design/context targets excluded, listed
and paired on common executable cases. Request timeouts missing with bounds,
not zero and not automatically retried. No5% tolerance gate. Reasons are
observable explanations, not the complete hidden reasoning process.

CPU-only support/(1+support+conflict) ranking uses the exact ledger, zero
unidentified candidates/hash ties, no LLM; report all cases and applicability.
The ranking never enters Solver inputs. Final accounting includes every
initiated formal/smoke attempt and partial artifacts; unknown usage remains
unknown, known costs are lower bounds when usage is unavailable.

## Runtime and authorization

Inherited BF16 Qwen local recipe,8192 output adapter,300s read-idle timeout,
36 concurrent requests,8 pinned physical preparation cores; no attention.
Actual processor capacity is checked later, without truncating inputs. Renders
and original requests persist. done/fail commits follow writer drain; resume
reads small flags before context/request construction. Only unresolved started
attempts reconcile; history is never erased or globally rebuilt/rehashed.

840 formal logical positions; formal initiated cap882 includes42 recovery-only
reserve. One complete logical smoke<=18 requests/600s across3 main-dataset eval
cases; total initiated cap900. Identical no-ops reuse one actual response.
Qualification: static→preparation→CPU≤1800s→actual visual review→bounded smoke→
input/output review→explicit authorized formal command. No automatic launch.
Low eligible-control counts require user review before GPU/formal; never weaken
thresholds or select convenient cases to force applicability.

### 2026-10-01 runtime authorization and qualification scope

The user now authorizes CPU regression, bounded GPU smoke, then remaining
preparation and formal execution if qualification passes. This supersedes only
the earlier static-only pause. Prepare the three fixed smoke cases first;
`cpu --smoke` checks synthetic regressions and all six actual requests for these
cases, recorded as `cpu_smoke.json`, never as whole-roster qualification.
After smoke artifact inspection, prepare the remaining140 roster cases (small
commits skip the already prepared three), and run whole-roster processor/fact
checks before formal launch. That separate `cpu.json` must cover all140 case
identities. Each CPU command remains bounded by1800 seconds. Scientific inputs,
roster, thresholds, call accounting and the single18-call/600s smoke are unchanged.
Report real applicability before expansion; do not automatically launch a mostly
inapplicable experiment. The missing schema in the synthetic test fixture was
repaired before any model request; no previous result or source telemetry changed.

### 2026-10-01 observed qualification blocker

The three-case CPU regression passed. A source-only audit of all140 cases then
found zero testable scope/soft-conflict cases; all489 selected observations
fail the registered64-bin coverage requirement. No-anchor counts44/60
AIOPS-2022,10/60 AIOPS-2025,19/20 Aegis. No model has been called.
Actual visual inspection also found excessive whitespace in the7894px board.
Do not describe this protocol as qualified or start formal execution merely
because synthetic/capacity checks passed. The source-applicability and visual
qualification are blocked. See docs/issues/RQ3_10_qualification_2026-10-01.md
for evidence and proposed **not yet adopted** measurement/anchor/activity/layout
revisions. No thresholds, selection rules or inputs were silently changed.
