# 2026-09-13 — Non-AIOPS trace projection integration

The first full-cohort CPU gallery stopped before its first PNG or model call:
the inherited search-only trace projector whitelisted AIOPS-2022/2025. This
was an incomplete dataset adapter, not a bad case, missing trace, or failed
model response. No case was excluded and no processed data was changed.

The vendored processor was inspected: the AIOPS readers rename Jaeger duration
without scaling; the RE2 reader converts microseconds to milliseconds; Aegis
normalizes duration_ms in its reader. RQ3 now retains processor-native ms for
Aegis/RE2 rather than dividing them a second time. AIOPS retains the exact
existing division by 1,000. Selection, counts and dimensionless scores do not
change. Source dataset identity is used only by the offline unit adapter.

The pre-repair exps.py is preserved under the completed smoke's source_snapshot.
Twenty-two display/projection tests passed, covering all five datasets, source
immutability, double-projection rejection and invalid durations. The three
actual smoke packets were also compared against the pre-repair function to
verify byte-identical AIOPS projections. Old RQs, pools, prompt template,
inference recipes and model replies are untouched. This CPU adapter correction
does not require repeating those already completed, unchanged AIOPS calls.

The same precommitted round/cohort resumes CPU rendering; all produced PNGs
still require inventory and visual review before formal requests.

## CPU scheduling

The initial serial gallery produced 32 cases in about ten minutes. Its single
CPU worker, not the GPU, was the bottleneck. The public per-case render operation
was extracted unchanged into an independent job and dispatched through the
shared ordered process-map utility, up to eight workers pinned to distinct
physical cores. The ordered final summary remains in the precommitted cohort
order; completion order is only operational logging. This does not modify the
selector, card grouping, layout or prompt. No inference was active during the
change. The pre-change source and 170 completed artifact hashes are retained
under this round for a byte-level serial/parallel comparison after rendering.

Completed checks: 386 CPU/renderer/state tests passed in 80.16 seconds; all
170 serial/parallel artifact hashes match exactly. All 480 PNGs rendered with
no failure, and their source-fact inventory, primitive coverage, fixed prompt,
candidate binding, PNG integrity and clipping checks passed. One predeclared
hash-selected sample from each of the five datasets was visually inspected.
Review and per-case hashes are saved in gallery/cpu_review.json and review.json.
