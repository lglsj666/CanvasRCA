# 2026-10-02 — RQ3.15 formal launch

## Scope and status

User explicitly requested the registered full experiment after successful qualification. All220 exposed eval cases and six frozen arms are running in the background. Launch23:49:54; verified23:53:42 America/Toronto. Source contract `d988af3aa1a701d68d1831fd7ddfa140bc3ca4a20ac37123967a8ef2735978bc`; config `a4a6e002a4c65c83e7856df0c8d7a56e6e7f9934de04695617a86451360895b7` unchanged.

## What happened

Added only execution-authorization and measured-source compatibility logic in `qualified_contract` and `full_authorized`. Original seven qualification reports, frozen archive, registered config, preparation, renderer, scoring and all other code AST nodes remain identical. Archived the effective source and recorded user authority with negative authorization/source/CPU/smoke checks; all passed. No repeated CPU preparation or additional smoke/model calls for activation.

Started the detached canonical local Qwen supervisor. Live attestation passed; supervisor2426, server2439 and runner2980 were alive at verification.17 real responses committed,36 requests in flight,53 formal attempts initiated,0 failed positions. These are launch-snapshot counts. GPU utilization100%; the actual argv emits memory utilization0.75, BF16 and context40960; output remains8192. The optional deep_gemm startup import emitted a warning, after which the server became ready and completed requests normally; no ERROR or failed request was observed at verification.

## Validity and caveats

Prior full CPU220, visual review and18-call smoke remain measured evidence of their unchanged scientific implementation. Activation checks do not replace those tests. The original config retains `full_launch_authorized=false` as frozen history; the new explicit receipt is the execution authority. Formal1320 positions comprise expected1284 real first-pass calls and36 exact-input fallback references; PAIR_REPEAT remains independent for every case. Formal limit1362 plus18 spent smoke calls gives total1380. Preserve original failure denominators and unknown usage. No interim efficacy scores were inspected or used for changes. Launch success is not a final scientific result.

## Decisions

The user's new request supersedes only the fulfilled stop-after-smoke execution boundary. Continue this frozen matrix without changing inputs, decoding, hypotheses, thresholds or layout. No automatic successor experiment.

## Blockers

None observed at launch verification. Original startup warning is retained and classified in `formal/launch_verification.json`.

## Next steps

Allow the detached queue to finish. Supervisor automatically closes its owned service; resume trusts atomic completed/phase markers and preserves attempt accounting. After completion, audit durable coverage, failure/usage records and registered statistics before interpreting the outcome. Stable monitoring follows the600-second project cadence; the current user request is satisfied by the verified launch.

Evidence: `qualification/activation_v1/activation_review.json`, `formal/launch_receipt.json`, `formal/launch_verification.json`, `formal/attestation.json`, `formal/calls.sqlite`, `formal/completed/`, `formal/logs/`.
