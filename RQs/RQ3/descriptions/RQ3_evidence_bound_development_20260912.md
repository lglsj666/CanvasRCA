# Evidence-bound reading and top-five output — 2026-09-12

DD-RQ3-SEARCH-9. Train-only successor, no promotion or training. The 48-call
coverage24 trial failed to improve quality consistently and increased cost.
Its complete responses frequently invented edges/hosting, assigned another
entity's telemetry to a candidate, or equated first onset/large z with cause.

Return to the original ranked eight-series images, same twelve train cases,
same candidates. Test a static guide limited to the actual visual grammar,
explicit observation-versus-hypothesis discipline, and exactly five ranked
alternatives. Bind the JSON services items to the complete public candidate
enum; require min(5, number of candidates) entries. Keep the top-five JSON keys,
granularity-aware scorer, weights and decoding budgets unchanged. Duplicate
IDs, if generated, remain model failures, not automatic repairs. No labels
enter the prompt or grammar. Candidate lists remain in text, not the PNG.

Compare legacy and model-card non-thinking sampling, maximum 24 new calls.
This jointly changes guidance and output binding; it cannot identify each
component's independent contribution. Earlier same-image answers are retained
as background controls, not rerun or rescored. Both valid and invalid outcomes
must be reported. A five-item list may increase AC@5/MRR through broader ranking
coverage without improving top-1, so report rank length and AC@1 separately.

Freeze image byte identity against the original ranked gallery, audit prompt
identity apart from the candidate list, CPU-test actual request schema and
resume, then run the bounded batch. No new attention, validation, eval, SFT or RL.

## Completed development outcome

24/24 calls completed in 223.84 seconds, with no infrastructure failure,
truncation, unknown candidate or duplicate ranking. All returned five IDs.
The full CPU regression passed 170 tests. Complete prompts, images, responses,
conversations and hashes passed the artifact audit; the images are byte-identical
to the original ranked-eight gallery. Candidate enumeration is prompt/schema
only, not an image panel. An initial missing local `re` import was caught by CPU
tests and fixed before any live request.

On the six cases per dataset, legacy sampling produced AIOPS-2022/AIOPS-2025
MRR 0.3333/0.2222; model-card non-thinking sampling produced 0.2500/0.3750.
Input tokens fell by 2,067 versus the inherited prompt on identical images,
but output tokens increased. Legal ranking format did not establish improved
diagnostic reasoning: complete responses still confused capacity increases
with exhaustion, onset order with cause, and some node/service owners.
This is not promoted to validation, eval or training. Source records and the
manual review are in `../results/search_first_v1/evidence_bound_development_v1/`.
