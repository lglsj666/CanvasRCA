# BASE versus format-SFT: matched Composer validation

Date: 2026-09-11. Status: authorized diagnostic, before further repairs.

Latest user override: after this comparison and its report, STOP and wait.
Further diagnosis, renderer changes, training and full-RQ3 execution are not
authorized as an automatic follow-on. This supersedes earlier continuation.

## Question and exact contrast

Does the final step-320 format-SFT adapter improve legal program generation and
actual dashboard construction over its untrained Qwen3.5-9B base checkpoint?
Use all existing 140 validation cases (70 per AIOPS dataset), not eval or TT.
No further training, candidate selection, prompt optimization or Solver call.

Reuse every completed SFT response from `formal_balanced_v1`. Verify its
original prompt, prepared public pool, catalogue bindings and artifact hashes.
BASE receives byte-identical system/user parts, candidate/card ordering and
per-case seed, with the same BF16 full-support decoding, 4,096-output ceiling
and tokenizer. Only the active LoRA/model identity differs. Original SFT
responses are retained even when invalid; no best-of-N or success-only filter.
The new capacity-aware catalogue instructions are NOT supplied in this
comparison. A subprocess-scoped restoration of the archived system prompt is
allowed only by this hash-bound replay script; current source prompt and future
catalogues are not changed. The native unified request/client/writer is reused.

Render both sets of exact output programs with the current, frozen RQ3 renderer
(content-aware log sizing and label-ink audit). Score saved SFT outputs again
only on CPU, in a separate result directory. Never compare BASE under the new
renderer against SFT's old 110/140 rendering outcome. Layout repair is a shared
evaluation condition, not a benefit attributed to SFT. No schema repair or
default dashboard is applied. Record all model failures; genuine infrastructure
or renderer-integrity defects remain separate and prevent a complete claim.

## Measures and limitations

Primary: schema/card-binding validity and actual render success. Also report
JSON syntax, truncation, unknown/duplicate IDs, each failure class, output token
cost, selected-card count and pixel overlap/overflow checks. Give paired counts
(both pass, SFT-only pass, BASE-only pass, both fail), dataset breakdowns,
Pratt-Wilcoxon and paired Cohen's dz; no confidence intervals. Apply Holm to the
two primary paired comparisons. This measures legal tool use, not optimal
evidence selection or RCA MRR; no downstream diagnosis claim is permitted.
The validation set has already been inspected during renderer debugging, so it
is not a fresh held-out confirmation. One sampled output per policy/case does
not quantify between-seed variability. Freeze before looking at BASE outcomes.

## Execution and preservation

One additional BASE request per case: 140 planned calls, charged to the existing
40,000 RQ3 ceiling (not monetary billing). No SFT regeneration. Reserve up to
ten interrupted-request retries in the diagnostic scope; do not retry invalid
model answers. Reuse already-qualified native BASE serving/request and SFT
artifacts; CPU-test the diagnostic binding/writer before launch. This does not
qualify the modified catalogue or authorize pending Solver phases.

Local background supervisor owns only its server/worker and holds the existing
GPU lease. Four independent CPU render workers, up to 36 requests in flight;
all responses/conversations are durably saved before rendering. Pause/restart
recovers complete requests without generation, does not join partial answers,
and retries only explicitly interrupted attempts. Preserve all originals under
their old directories. Output: `RQs/RQ3/results/base_sft_comparison_v1/`.

Freeze the script, current source/config hashes and all input references before
execution. Any renderer/source change thereafter requires a new comparison
namespace, never partial rescoring of only one policy. Summarize and stop;
no automatic full-RQ launcher or further repair work.
