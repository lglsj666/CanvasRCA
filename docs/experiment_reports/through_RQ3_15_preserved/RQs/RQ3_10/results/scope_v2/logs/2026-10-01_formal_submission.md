# RQ3.10 v2 local full submission — 2026-10-01

Submitted and running at 2026-10-01T16:36:34.108145+00:00. Single primary agent. Latest user goal:
read status, decide next work, deploy, CPU/GPU regress, submit full experiment,
then stop. This handoff is the stopping boundary; full efficacy analysis remains pending.

RQ1.1/RQ2.1 and Qwen RQ3.1–3.8 have durable reports. RQ3.9 remains paused;
its five scattered formal results were neither resumed nor used for this repair.
The next experiment is the adopted RQ3.10 v2 successor. v1 remains scientifically
blocked with0 GPU calls and its artifacts untouched. v2 retains the exact140
exposed-eval cases (60 AIOPS2022,60 AIOPS2025,20 Aegis) and three smoke identities.

Fixed native-cadence80% coverage and exact public source gauges replace the
v1 mismatch between64 display slots and30–40 acquisition samples. Base anchors
are retained then supplemented by a fixed public-entity resource hash policy.
No interpolation, pod activity from service aggregates, root-label selection,
threshold reduction, missing-value health inference or correctness retries.
Matrix/tiles use the same glyphs, cell dimensions and common canvas with compact
row heights. Existing renderer component behavior remains unchanged.

Qualification passed:
-12 RQ regression categories and840 actual processor checks on all140 cases;
 maximum input29,411 +8,192 output =37,603 <40,960; zero context/design exclusions.
-280 real boards passed DOM audits;35 renderer tests passed. Representative
 native PNGs were inspected and a real-case repeat matched PNG/HTML hashes.
-180.25s GPU smoke including startup:18 logical positions,16 actual complete
 calls,2 exact-input references. All outputs parsed, IDs legal, stop finish,
 usage consistent, streaming identities bound, completion artifacts audited.
-After smoke, only final offline attempt-cost reader directory was corrected.
 AST/source comparison proves all serving/request/runner/client/render/scorer
 code unchanged. Full CPU repeated (73.38s), real16-call and interrupted-stream
 cost checks passed. The original GPU source/attestation is preserved, with
 explicit successor qualification proof. No GPU replays or clock/budget reset.

Complete registered formal matrix:6 conditions ×140 =840 positions;
751 planned actual requests plus89 same-request references. Concurrent request
limit36, aggregate writer pool8. Formal attempt ceiling882; one smoke18calls/600s;
aggregate ceiling900. Every failure/interruption remains in accounting.

Runtime acknowledgement: supervisor 44540, server 44548, runner
45040; all live at receipt. Queue751+89 acknowledged; attempt states
{'complete': 34, 'started': 36}; atomic completion markers 34. These are an operational snapshot,
not final results. No partial efficacy comparison was performed.

Model: official Qwen3.8-27B revision 1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0, BF16/unquantized,
triton GDN adapter,40960 context,8192 call-level output ceiling, thinking/attention
off. Local GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition, 97887, GPU-a7d571ac-081a-a731-196d-7c073a76a4a7. No Nibi/Slurm, Gemma, training or new test calls.
Frozen formal source: RQs/RQ3_10/results/scope_v2/qualification/frozen_formal_source.tar.gz, SHA256
5f417056831fcc8c1b32116590ee81cf4a11debc8ce432cdfe3ce6d241117548. Existing dirty working-tree state was preserved;
this is a frozen source deployment, not a claim of a clean/new Git commit.

Durable receipt: ../formal/submission.json; attestation: ../formal/attestation.json.
Supervisor log: ../formal/logs/submission.log.
Runner log: ../formal/logs/runner.1790872295910472591.log.
Server log: ../formal/logs/server.1790872295910472591.log.
Qualification: ../qualification/deployment.json, cpu.json, visual_review.json,
scientific_review.json, smoke_review.json, offline_cost_reader_regression.json.

Resume only if needed with the same frozen source/config:
`bash RQs/RQ3_10/scripts/local.sh supervise --execute`.
It skips committed units before public context loading, does not bulk re-hash
historical conversations/renders, and starts no model if the roster is terminal.
Timeout flags are terminal; unexplained infrastructure failures require diagnosis.
Do not repeat smoke, reset the logical600s window, expand arms, or retune on
partial scores. Supervisor runs only this queue and shuts its owned server down
at completion; no automatic analysis/follow-up is configured.

Scientific applicability remains limited:23 AIOPS2022 cases provide directly
qualified shared stable-peer conflict; AIOPS2025/Aegis have0 such cases. The
fixed full cohort can test supplementation/computation/visual increments but
cannot establish the conflict mechanism across all datasets. All cases are
exposed eval, not independent test evidence. Smoke prose still contains scope
promotion, causal overconfidence and temporal contradictions; runtime passage
is not credibility qualification. Final MRR and all credibility/cost analyses
await the complete durable batch and a subsequent user request.
