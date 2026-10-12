# Completed-case inspection — 2026-09-08 16:53 UTC

Case: `INC-B84269FDA98E`; model: Qwen3.8; experiment: evidence selection.

Inspected all 16 completed T/V conditions, their complete public system/task/guide/evidence text, all 16 complete final responses, and all eight actual dashboard PNGs. Identical text lines were read once, with ordered fragment references retained in `machine_checks.json`; no unique input line or response was omitted. Private labels and MRR were not consulted.

The machine checks passed record/artifact hashes, persisted conversation membership, current materialized request equality, candidate consistency, single-image limits, and prefill/answer attention vector alignment and normalization. All responses ended normally (128–229 output tokens); no truncation, format failure, runaway generation or missing attention artifact was found in this sample.

Visual review confirmed actual selection changes: BARO selects the 371/460 metric families; coverage spreads metrics across entities and changes trace/edge selections; random includes constant resource/capacity series and different trace operations; sigma emphasizes 124/246/428 metrics; trace support/confidence changes the R rows while retaining the other regions. Shared P0 evidence remains recognizable across the single-region interventions. Curves and their displayed summaries, numeric IDs, log rows, and caller-to-callee edge ledgers are present; no additional blocking rendering defect was found.

Some public reasons misattribute an entity, infer an unsupported causal relationship, or contradict their own ranking. These are observed model behavior, not evidence here of a request-construction or persistence defect. They remain unchanged and are not retried. This inspection establishes sampled operational/input integrity, not correctness of the predicted root cause or proof that all cases are bug-free.

Decision: continue the registered formal suite without changing prompts, evidence, rendering or scoring.
