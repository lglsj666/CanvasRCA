# RQ3.15 user pause — 2026-10-03

**Historical pause; superseded by explicit user resumption at10:50:22 America/Toronto on2026-10-03.** The user requested “帮我重启实验吧。” The same frozen matrix resumes from its committed markers. Current status: `resume_receipt.json`; durable authorization: `resumes/20261003_105022/authorization.json`. Preserve the pause evidence and its accounting below.

The user explicitly requested immediate safe pause: “我准备睡觉了，帮我立刻安全暂停实验。”

Pause requested at01:06:58 America/Toronto. SIGUSR1 was sent to the verified RQ3.15 runner and its supervisor. New request submission stops immediately; existing requests and atomic artifact writers drain before the owned model service exits. See `pause_request.json` for the durable request and the latest shutdown status.

**Safe shutdown verified at01:10:34 America/Toronto.** Runner, supervisor, model server and engine have exited; port21955 is closed. All36 in-flight calls completed normally, with no new submission or failed attempt during draining.794 real responses and24 fallback references are committed;4 earlier request-timeout positions remain preserved, giving822 terminal positions and498 pending out of1320. Formal attempts798 plus prior smoke18 remain spent. SQLite quick check passed; every done flag has its atomic completion marker. The phase is incomplete, not completed. GPU memory returned to2421MiB for the whole device. Evidence: `pause_verification_20261003.json`.

This user request supersedes the earlier full-run execution authorization. **Do not resume the runner, model service, inference, or automatic monitoring until the user explicitly authorizes resumption.** Preserve all completed outputs, failed attempts, usage and unknown-usage records. The experiment remains incomplete; a pause is not a successful full run.

On authorized resume, use the existing registered supervisor and atomic per-call/phase markers. Do not reset the call budget, reprocess committed requests, alter inputs/thresholds, or substitute the old launch snapshot for current state.
