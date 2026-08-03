# 2026-07-31 Nonredundant modality-allocation development plan

## Status and purpose

This is a development-only, falsifiable mechanism screen. It does not replace
the completed RQ0 result, does not use formal/reserve cases, and cannot by itself
support a paper claim.

RQ0 showed that adding a dashboard to an already complete, byte-identical text
serialization changes predictions but hurts more text-correct cases than it
repairs. Atomic tests show that the image is readable; renderer v7 makes
topology edges readable; two case-level SFT pilots still produce no improvement.
The next hypothesis is therefore narrower:

> H-allocation: an image can help RCA when it transports the dense temporal and
> topology evidence instead of redundantly competing with a complete textual
> copy of those facts.

This is not a license to remove inconvenient evidence. Every condition starts
from the same CEB and the same source-evidence inventory. The intervention is
where dense metric sequences and directed edges are transported.

## Three paired conditions

- **D — allocated visual+text:** renderer-v7 image first, followed by the common
  deterministic evidence summary. The image carries metric shapes and topology;
  dense 64-bin vectors and edge JSON are not repeated in text.
- **A — duplicated visual+text:** the same image and the same common summary,
  plus a dense textual appendix containing the full vectors/masks/counts and all
  directed edges.
- **B — text-only:** byte-identical A text, without the image.

Task statement, candidate order, output schema, decoding, model checkpoint,
renderer, CEB, scoring, and retry policy are identical. A versus B reproduces
the redundancy question on the development roster; D versus B is the primary
mechanism comparison; D versus A tests whether duplicate transport is the
harmful component.

The common summary retains incident/candidate metadata, metric identities and
label-blind summaries (baseline, peak, signed-z, onset, persistence), relative
fault window, logs, traces, propagation-service summaries, and explicit
missingness. Only the dense transport appendix moves between text and image.
The audit must record the common-summary hash, dense-appendix hash, CEB hash,
source fact-inventory hash, prompt hash, and image hash for every call.

## Development roster and runtime

- Select 24 already exposed development cases, eight each from AegisLab,
  AIOPS-2022, and AIOPS-2025, by deterministic hash under seed 42.
- Exclude all current SFT v1/v2 heldout cases so their model-selection outcomes
  do not choose this roster. Prior development exposure is accepted and reported;
  no inferential claim is allowed.
- Run Qwen3.6-27B and Gemma-4-26B-A4B-it regardless of the first model's sign:
  24 cases × 3 conditions × 2 models = 144 calls.
- Use the frozen unquantized BF16 eager vLLM recipe: 32,768 context, 16,384
  output cap, temperature 0, top-p 1, seed 42, thinking off, and
  `gpu_memory_utilization=0.65`.
- Balance the six DAB condition orders by opaque-incident hash.
- Use the project-owned granularity-aware scorer. Store upstream-compatible
  primary fields plus the scoring-contract identifier.

## Qualification gates

Before model calls:

1. Serializer tests must prove A and B text byte-identical and all three common
   summaries byte-identical.
2. Every condition must share the same CEB/source fact-inventory hash; the audit
   must explicitly disclose that D uses visual rather than exact-scalar textual
   transport for the dense appendix.
3. Repeated builds must give byte-identical image, summary, appendix, and hashes.
4. Renderer-v7 leakage and perception qualifications remain required.
5. One three-dataset smoke per model must complete through compiler, token
   counter, client, parser, new scorer, writer, and analyzer. Accuracy is not a
   smoke gate.

## Analysis and stop rule

Report MRR, AC@1/3/5, AVG@3/5, parse/error/truncation, input/image/output tokens,
wall time, paired direction counts, top-1 changes, Wilcoxon p, and paired effect
size. Because the roster is exposed and n=24, p-values are descriptive only.

The mechanism is eligible for a separately preregistered fresh-data replication
only if all of the following hold:

1. D−B macro MRR is at least +0.05 on both Qwen and Gemma.
2. Each model has at least three more improved than degraded pairs.
3. No dataset/model D−B delta is at or below −0.10.
4. D also beats A on both models, supporting the allocation mechanism rather
   than generic run variance.
5. Parse rate is at least 0.95 and infrastructure pairing is complete.

Failure on either architecture stops this representation from consuming fresh
reserve cases. Do not tune the roster, drop discordant cases, add training, or
select checkpoints after seeing the result. A positive development result is
only a qualification signal; a negative result is enough to stop this route.

