# RQ0 topology-edge legibility intervention

Scope: the same 12 development dashboards used by the atomic grounding
diagnostic. The original renderer-v6 pixels remain unchanged; v1 appends
a compact directional rank-pair key and v2 appends a larger four-line key.
Actual-image, same-dataset swapped-image, and no-image controls are all
reported. This is a perception qualification, not an RCA experiment, and
does not alter the confirmatory RQ0 result.

| visual primitive | Qwen actual | Qwen swapped | Qwen no image | Gemma actual | Gemma swapped | Gemma no image |
|---|---:|---:|---:|---:|---:|---:|
| renderer-v6 curved edge | 25.0% | 0.0% | 16.7% | 8.3% | 16.7% | 0.0% |
| compact edge key | 100.0% | 0.0% | 8.3% | 41.7% | 8.3% | 0.0% |
| large edge key | 100.0% | 25.0% | 8.3% | 91.7% | 0.0% | 0.0% |

The original curved-edge and explicit-key questions are not identical, so
their percentages are a qualification comparison rather than an effect-size
estimate. The compact and large keys use the same 12 cases and task keys.

## Scale sensitivity

| model | compact actual | large actual | change | compact image tokens | large image tokens |
|---|---:|---:|---:|---:|---:|
| qwen3.6-27b | 100.0% | 100.0% | +0.0% | 1766 | 1962 |
| gemma-4-26b-a4b | 41.7% | 91.7% | +50.0% | 268 | 272 |

Gemma improves from 41.7% to 91.7% when the key is enlarged, while its
mean visual-token count changes only slightly. Qwen is already at 100%
with the compact key and remains there. The shared cross-model gate
(at least 90% actual accuracy and at least 50 percentage points over the
stronger control) is therefore passed only by the large key.

All four real runs contain 36 unique case-condition calls, no infrastructure
failures, no truncations, exact server/preflight token agreement, and 100%
parse rate in the actual-image condition. Gemma has three no-image model
formatting failures in each key experiment; these are retained as model
outcomes and do not affect the actual-image legibility gate.

## Decision

The renderer-v6 curved topology edges are not a reliable model-readable
primitive. Large explicit direction keys materially mitigate that atomic
perception bottleneck across both tested architectures. This supports a development-only
renderer-v7 candidate, but it does not establish an end-to-end RCA benefit.

Do not start generic visual-grounding SFT: both models already read most
dashboard atoms, and the isolated edge defect has a rendering fix. The next
experiment should first integrate the large key into a frozen renderer-v7
candidate and test case-level cause-versus-propagated-symptom reasoning on
development incidents with unchanged textual evidence. Only if that improves
paired RCA should the project preregister a fresh-reserve intervention study.
The original 720-case RQ0 set must remain untouched.
