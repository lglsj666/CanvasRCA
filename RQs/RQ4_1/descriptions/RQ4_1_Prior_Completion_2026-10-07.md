# RQ4.1 — SCOPE / DART / S²Prune CPU completion, v13

**Date:** 2026-10-07. **Status:** implementation and CPU qualification; GPU/model calls disabled.

The user requests completion of all three previously unimplemented prior paths.
They do not depend on another arm's answers, selected roots, scores or MRR.
Inputs are the same public dashboard and each method's own within-call model
signals. DART/S²Prune use early layers within one forward/generation call; no
model answer is passed into a second diagnostic request.

## Reference and model contracts

Official source files and exact SHA-256 values are frozen in
`../results/comparison_coding_v1/prior_completion_v13/references/manifest.json`.
They are test references, not runtime dependencies or separately installed repos.

| Method | Official source revision | Preserved selection mechanism | Explicit Qwen adaptation |
|---|---|---|---|
| SCOPE | [kinredon/SCOPE](https://github.com/kinredon/SCOPE/tree/6bf73069e0d61307051cfda8e25925bc7b7afdd9) | Normalized feature cosine coverage, saliency times marginal gain, alpha 1; lazy greedy with exact marginal reevaluation | Qwen has no CLS token. Mean incoming **actual** attention over patch queries and heads in the penultimate vision block replaces CLIP's CLS-query saliency. Sum saliency and mean hidden vectors within each 2×2 merger group. This is a disclosed model adaptation; the repository does not specify the authors' Qwen signal mapping. |
| DART | [ZichenWen1/DART](https://github.com/ZichenWen1/DART/tree/0c888673198b0f2784053a5686f95a519ceef209) | Actual key L1 pivots; normalized updated hidden-state cosine dissimilarity; prune after decoder block 2 | Four visual and four post-image text pivots, limited by available counts. Qwen's block-2 keys are GatedDeltaNet keys before kernel normalization. Exact K uses equal quotas over the remaining K−visual-pivot slots and remainder in the fixed pivot iteration order. Released code can overshoot nominal retention; this count adaptation is declared. |
| S²Prune | [yuanyuanjia71-spec/S2Prune](https://github.com/yuanyuanjia71-spec/S2Prune/tree/b0ac197e5e765f8a151669fdcbce10b621bbf44b) | Actual first-block representation-change norm, Laplacian regional complexity, capped largest-remainder allocation, recursive cells and max ERC | Use 9×9 coarse regions on registered large Qwen grids. Original 24×24 paper-budget settings are tested separately. Qwen's consumed early recurrent state is retained; it is not an indexable token KV table. This differs from the released all-attention prefix-KV deletion policy. |

Local model configuration identifies `Qwen3_5ForConditionalGeneration`, 64
decoder blocks (three recurrent, one full-attention, repeating), hidden width
5120; vision width 1152, 27 blocks, merge size 2. Local displayed checkpoint
name remains Qwen3.8-27B. No model/config/package files are modified.

For DART/S²Prune, all early blocks consume the full prefix. At the boundary,
gather **updated** states and original four-axis positions. Later blocks consume
the shorter sequence. Keep the full consumed state of early recurrent layers;
later full-attention KV contains only its consumed shorter prefix. Cached decode
must equal full layerwise recomputation under this declared policy. Never gather
a recurrent-state tensor along an invented token dimension. This is a coherent
hybrid-model adaptation, not proof of equivalence to an all-attention model.

All priors use the already registered E50 total K for that case, without forcing
CVC anchors, typed dependencies or its eligible-support restrictions. Preserve all
static text tokens. Layerwise token-block costs and selector/signal overhead are
reported; equal retained K does not mean equal computation.

## CPU evidence and launch limits

1. Nine new tests exercise official selector parity (within the stated count/
   signal scope), ties, invalid inputs, all original S²Prune budgets, rectangular
   allocation, real installed Qwen vision classes, and real installed Qwen hybrid
   blocks with small random weights. Identity prefill, actual selector wiring and
   cached two-token continuation versus full recomputation are checked. These
   passed in `unit_attempt_01.log`; do not rerun the passes.
2. Check all 220 existing input geometries for count, contiguous image positions,
   context bounds and original MRoPE preservation. This reads existing small
   geometry/support artifacts and does not regenerate images or encoder features.
3. Run one maximum-token public case per dataset (ties by case ID), each method,
   with actual tensor dimensions and deterministic **synthetic** model signals.
   S²Prune additionally uses the actual existing PNG. These are resource/shape
   fixtures, never model selections or RCA results. Random signals cannot certify
   real-weight selection runtime. Record this limitation in every receipt.
4. Keep 30-second selector and 2-GiB process-RSS bounds; at most three pinned
   physical CPU workers, no more than 24 GiB aggregate, and the original 8-hour
   CPU clock. A resource failure is recorded, not converted to an untested pass.
5. Preserve every previous passed check, including G-Prune 220/220. Do not replay
   source rendering, actual processor, feature extraction, CVC selections or
   statistics. Source snapshots and failed attempts remain immutable.

CPU success qualifies the adapter logic and tested shapes only. Actual checkpoint
signals, native/adapter numerical equivalence, generation integration and measured
end-to-end speed still require their own registered GPU smoke. Existing smoke
slots do not silently certify an uncovered state path. SCOPE saliency extraction
recomputes attention in bounded chunks and has real overhead; no speed claim is
made from CPU unit tests. There is no new model call or GPU authorization here.

The comparison names remain historical arm IDs, but reports must label these as
Qwen adaptations and list these differences. Do not claim an unqualified faithful
prior victory or change the scientific family/call budget. GPU/smoke/formal flags
stay false. The v10 hardcoded not-run entries are preserved as historical scope
gaps, superseded only by evidence produced by this completion pass.
