# SFT-format validation authorization — 2026-09-11

The user authorizes validating whether completed format SFT learned legal
Composer output, with safe pause and resume. This supersedes the post-SFT
pause only for `validation_SFT_composer`; every other phase remains stopped.

Run the already registered 140 cases: 70 AIOPS-2022 and 70 AIOPS-2025, final
SFT update 320. Use one independently generated proposal per case, the frozen
catalogue, actual SFT LoRA, existing request seeds and 4,096-output-token
Composer recipe. No teacher target is supplied to inference. No BASE run or
Solver request is added. The original schedule/call identities are retained,
so these calls can be reused by later authorized pipeline validation.

The 9B LoRA-serving and probability path was exercised by generalization
repair v3. CPU tests cover committed-response reuse without a live server,
phase locks, call budget recovery and adapter identity. Later renderer repairs
do not change Composer input or serving; their CPU rendering behavior is
checked here. This is not a claim that the pending Solver-facing renderer
qualification passed. The global full-lifecycle activation is not refreshed.

The scoped launcher validates current dependencies and uses the native phase
worker, SQLite call register, asynchronous conversation writer, four-core CPU
render pool and GPU lease. Completed outcome artifacts and cached model
responses are reused. A response saved before a rendering interruption needs
only CPU work on resume; a genuinely incomplete model response is preserved
as an interrupted attempt and retried with the same input, without joining
partial answers. Model-invalid proposals remain scored failures, not retries.

The launcher owns one server and one worker. Send SIGTERM to its recorded
supervisor PID for an operational pause: native cleanup stops owned child
processes and releases GPU memory. Rerun the same launcher for recovery. An
OS/power interruption is reconciled from durable artifacts, not stale PIDs.
Never delete completed cases or reconstruct a new random sample to resume.

Output stays in `RQs/RQ3/results/formal_balanced_v1/`: existing per-call
prompts/trajectories/conversations/program_artifacts and a new
`private/validation/SFT_format.json` summary. Report JSON validity, schema/card
binding, actual render success, input/output tokens and failure reasons by
dataset. This is neither an RCA MRR evaluation nor proof against overfitting.
The validation checkpoint is fixed at 320; no 480-case eval data is opened.

After validation and its artifact check, stop. New user authorization is
required for remaining qualification, Solver validation, RL or formal eval.
