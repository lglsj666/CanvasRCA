# 2026-09-28 — C nested-log clock repair and resume

## Scope and status

RQ3.7 C, eval480 and exposed test360. No fresh events. User explicitly asks to
fix the preparation crash and resume. Base scientific contract stays
`1a8d2032bb94718e3a23b62d1a62e331b0b1b671410312b78e22b1dc756997a2`;
forward privacy-projection amendment is DD-RQ37-4, with helper/adapter hashes
in `stage_c_clock_repair.json`.

## What happened

237/655 preparation results preceded an absolute-clock error. Eight-case CPU
frontier isolated RE2-TT INC-12D885A5B485. WiredTiger embeds Unix seconds inside
the log message; the outer date scrubber had missed this numeric slot. It also
appeared in the actual ALL_ID appendix, not only an unused parent condition.
Relative translation repairs it without disabling the guard. Counters,
non-clock numbers, original statistics' differences and selected packs survive.

## Verification and validity

Eight focused CPU tests, static lint/AST/shell checks and ten real request builds
pass. CPU request matrix took 77.59 seconds, both tokenizers/processors, zero
model calls. Actual PNG reviewed. 430 small current-contract views checked;
only the newly repaired case contains the applicable WiredTiger message.
Past results and model/config/prompt/render/scoring code are unchanged. C's
18-call original smoke is retained; no new GPU smoke claimed. Total cumulative
calls remain 24661 before resume. New projection provenance is CPU-side.

## Decisions and next steps

Retain 1800 A→C terminal aliases, including failures. Resume with
`bash RQs/RQ3_7/scripts/stage_c/run.sh` (detached via setsid/nohup). At restart,
250 cold contexts already exist, leaving 410. Eight independent-core workers
prepare missing cases, then formal Qwen followed by Gemma starts automatically.
No bulk completed-request verification/rebuilding; missing work only. Failures
now include case identity and top-level queue state. This is not C completion
and does not imply all 6600 remaining formal requests have started.
