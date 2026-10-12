# Round 3: full-remaining SIRCL trace support/confidence

2026-09-13. Both models' round-2 commits were verified before registration.
The registered cohorts contain ALL remaining cases: Qwen 290, Gemma 308;
358 distinct cases. No inference subset is used. Only rounds 1 and the new
round 2 can supply exact-request no-op references; deleted rounds cannot.

CPU review passed for all 358 rendered cases. Fixed prompt and candidates,
source identity, private-label isolation, fact-to-primitive bindings, image
dimensions, clipping, native trace selection and unchanged M/L anchors were
checked. R selections and pixels changed in 350 cases; eight naturally have
the same representation as the retained first round.

Five actual PNGs were opened, one per dataset: INC-91CC9D691CA8,
INC-358CBE8D4527, INC-C2222DBA0446, INC-C17A00DC78FC,
INC-FCEC7B343F4C. The eight trace rows display owner/operation, counts,
baseline/current exclusive latency, and a non-time latency axis. Panels,
edge directions and numerical owner groups remain within their cards.
Dense existing labels remain small; no newly observed truncation or overlap
blocks execution. This is a visual spot check, not a proof of readability
for every glyph or of correctness of future model predictions.

The scientific change is trace evidence selection; no prompt, model recipe,
training, or attention change is introduced. All completed outcomes,
including incorrect answers and model-format failures, will be retained.

## Execution and first in-run review

Source/config archive: 181 files, SHA256
`347ae70bf85dcb9a995399e3fae3e2688c24d9763a49e1bfaf5171321f8e725c`.
Both full-cohort work specs were bound before launch. Exact-input no-ops use
seven Qwen and eight Gemma verified first-round records; they are logical
targets, not omitted cases or new random answer attempts.

The first ten-minute check found normal progress; 61 Qwen outcomes persisted
by the end of inspection, all complete, with no infrastructure failure.
Hash-selected record `b5d6743807e8a8439079bcae6c73a31561b08d7477d15115aa991645c99fec85`
is case INC-CB8AD006EA8A. Read its entire conversation and opened the exact
persisted PNG; artifact verification passed. Output is 195 tokens, stop finish,
five candidate IDs. It correctly binds log owner 59587 to service 772 and finds
955→387 and the 387 operation, but treats a 2.53→3.05 ms increase plus a caller's
HTTP error as sufficient origin evidence, overlooking much larger metric
excursions elsewhere. The supplied data and recorded input are intact. This
incorrect diagnostic outcome is retained, not retried or used to alter the
currently running method.

## Completed full round

Qwen: 290/290 logical targets, 25 new AC@1 successes. Gemma: 308/308,
43 new AC@1 successes. All 598 outcomes finished normally, with zero
infrastructure or model-schema errors. Full post-run audit passed, including
actual identical inputs for 240 shared cases. There were 583 new model calls
and 15 verified identical-input references to the retained first round;
new calls used 6,209,706 input and 99,446 output tokens. Neither the deleted
results nor extra answer retries contribute to coverage.

Read Gemma's full conversation for paired case INC-CB8AD006EA8A. It correctly
reads trace 955's count drop and the 955→387 relation, but invents an earliest
onset and log error increase for 955: the displayed logs belong to 59587/772,
and no onset list identifies 955. This is model grounding failure, not evidence
that the renderer supplied those invented facts. Both responses remain.

Cumulative AC@1 union after rounds 1–3 is 215/480 for each model, but the
solved sets differ. Per dataset (Aegis/A22/A25/OB/TT): Qwen 53/25/29/57/51;
Gemma 59/30/23/52/51. No model has reached the registered per-dataset target.
The next method must cover ALL 265 remaining cases for each model.
