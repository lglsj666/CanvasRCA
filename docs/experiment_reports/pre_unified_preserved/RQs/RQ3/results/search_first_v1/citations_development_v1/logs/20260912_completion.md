# 2026-09-12 — SEARCH40 completion and tournament handoff

## Scope and status

Train-only cohort C, 24 cases, 12 per AIOPS dataset. Original spec hash:
`70154fcf18b2229d82a1ccb144b6499a77042b387ce21cc647663c914dab858f`.
24/24 complete, no timeout or infrastructure/schema error. Supervisor is no
longer live; it terminated normally under the local runner's shutdown path.
No tournament or training model call was launched during this review.

## What happened

`review_citations.py` verified 48 new/reference records, prompt/conversation
presence, image hashes, candidate/schema equality and unchanged unified scores.
All 273 frozen dependencies matched BEFORE the subsequent goal/protocol edits.
The archived source tar and old work specification remain unchanged. Later
edits to the live experiment document do not alter these completed inputs.
Main agent read all 24 full answers, not just the summary.

MRR: AIOPS2022 .423611→.444444, repair/break/tie 2/1/9; AIOPS2025
.298611→.236111, 0/3/9. Holm p=.75/.50. Mean outputs 269.42/242.42,
maximum338, all finish_reason=stop. Additional static input220 tokens;
image tokens16002 unchanged. Wall345.49seconds.

All 24 answers cite sources. The strict address grammar directly bound86 of94
references; the other8 use ranges, lists, region aliases or entity suffixes.
This is not a finding of8 fabricated sources. Source-address checks do not
verify semantic or causal truth. Full-answer review still found weak causal
interpretations, hosting assumptions and overstated tiny numerical changes.
See the appended SEARCH40 section in `findings/search_retrospective_20260912.md`.

## Decisions and next work

Latest user authority: adaptive RQ480 tournament, top1 retirement transition at
80%=240/300 non-RE2 cases; then top5 retirement. Earlier70%/75% readings were
never used in an executed tournament. Post-learning MRR targets become
>.65 for each AIOPS dataset and >.75 overall. At most one modality may supply
diagnostic text; at least three remain in the same PNG. Pure vision remains
valid and SEARCH22's first-round method is not silently changed.

Config `configs/tournament_v1.yaml` and canonical experiment/rules files now
register this successor. CPU configuration/split checks passed:480 identities
in100/100/100/90/90 strata,300 non-RE2, threshold240, unchanged first-method
pool identity,14 parent checks and5999 functional source lines. The existing
eval preparation gate refused missing trained-policy freeze; no data was
prepared or deleted and no gate was bypassed. Implement a distinct adaptive
discovery adapter with resumable retirement rather than weakening formal eval.
Retain optimizer data isolation and label-free model inputs. Do not call this
union coverage a single learned pipeline's deployment accuracy.
