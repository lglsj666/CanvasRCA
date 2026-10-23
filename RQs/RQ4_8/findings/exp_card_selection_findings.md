# RQ4.8 findings and current state

## Latest: full formal experiment running

The user authorized missing QA preparation, formal binding and launch. All 60
fixed QA cases are prepared (20 per dataset); static input integrity passed for
831 applicable requests and 870 unique image hashes. Controls are applicable in
60/58/57 cases for isolation/position/statistic-label interventions. Dynamic
selected-card QA waits for the shared selector as registered.

A previously crashing anchor-only subset is repaired locally; 15 compatible
completed preparation bundles were reused and the failed case then passed.
The 220-case CPU regression was not rerun. Existing CPU/unit/visual and actual
specialty/repair smoke evidence is bound without rewriting its execution history.
The new immutable formal snapshot is `formal_freeze/v1`; the old freezes remain.

Formal launch: tmux `rq48-formal`, PID 541675. At the startup check after more
than 190 seconds: 25/3,840 logical positions committed,
24 actual calls responded, with no infrastructure error.
These are startup counts, not final scientific results. Eight CPU workers and
GPU concurrency 8 use the existing BF16 vLLM recipe with utilization 0.8.
All prior 66 smoke attempts remain recorded. No additional GPU smoke was run.

Evidence: `results/card_selection_v1/logs/formal_launch_2026-10-20.md` and
`results/card_selection_v1/logs/formal_launch_receipt.json`. Running state should
be read from `formal/progress.json`, not these historical startup counts.


## Latest: targeted GPU repair smoke passed

The user authorized another GPU smoke and explicitly skipped CPU regression.
`smoke_repair_v2` completed 18/18 actual calls in 182.00 seconds and passed
artifact review. Previous phase-alias false negatives are resolved in actual
answers; both omitted relationship questions were submitted and answered; all
three BASE/REPEAT pairs have distinct actual calls with no result references.
All 15 enabled attention summaries and mappings pass. No model output was
retried for an incorrect answer. Cumulative actual calls: 66; formal not started.

No CPU regression was rerun and no new manual image was viewed. Previous
qualification remains evidence at its original revisions. This smoke closes
the three discovered interface/repeat gaps; it does not claim that deferred
full formal QA preparation was executed. The registered 4,000-call ceiling
remains unchanged (18 repair slots drawn from recovery; 88 recovery slots left).
Owned GPU services have stopped.

Review: `results/card_selection_v1/smoke_repair_v2/REVIEW.md`.

## Previous smoke audit — preserved historical state

All three registered GPU smoke queues have finished: 54 terminal positions,
48 actual model calls, 3 exact-result references and 3 QA-inapplicable positions.
No infrastructure errors or truncated outputs occurred. Formal is not started.

Artifact review found three host-side defects: two correctly named phase fields
were scored wrong; two visible text relation targets were omitted from QA;
one ordinary M_ID_PACK result referenced its independent repeat. The first two
correct answers have versioned offline rescores. The omitted questions have no
answers and the referenced pair is excluded from independent-repeat analysis.
Original inputs, responses, scores, references and frozen sources are preserved.

The receiver, visible relation parser and repeat-cache isolation are repaired.
Six focused offline checks and current static checks pass. No additional model
calls, renderer launches, manual image views or full cohort CPU rerun occurred.
Old smoke receipts are not reissued as execution of repaired code. Single/hybrid
artifact integrity passes at its executed revision; two-stage and QA scopes retain
explicit original coverage gaps. No formal credential was issued.

All 37 unique smoke PNG hashes and complete request/response records were checked;
9 edited M images retain exact original card pixels and remove the other cards.
Second-stage requests really contain only the edited image and static instructions.
All 45 collected attention summaries and actual token/region mappings were checked.
Only layer 3's last prompt and first decode queries were collected; this is not
final-decision attention. Summaries plus readable mappings project to 0.488 decimal
GB per 10,000 actual calls in this smoke sample.

The 220-case CPU input qualification remains 218 reused passes plus the two
user-requested final cases. Full 60-case QA preparation/runtime CPU receipts remain
deferred, not passed. Update affected QA preparation before formal qualification.
The cumulative manual image quota remains 20; no additional images were opened.
Hybrid and two-stage conditions remain explicit RQ4.8 exceptions, with no Codex edit.

Detailed review: `results/card_selection_v1/logs/smoke_artifact_review_2026-10-20.md`.
