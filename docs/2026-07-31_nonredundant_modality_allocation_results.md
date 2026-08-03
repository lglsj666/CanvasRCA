# 2026-07-31 Nonredundant modality-allocation development result

**Scope:** exposed development data; nonconfirmatory mechanism screen  
**Effect on registered RQ0:** none

## Question

The completed RQ0 experiment added a dashboard to a lossless, byte-identical
text serialization and found no visual gain. This follow-up tests whether that
design made the image redundant and distracting: can the image help when it
transports dense temporal/topology evidence instead of competing with its full
textual duplicate?

The three conditions are:

- D, allocated visual+text: renderer-v7 image plus a common evidence summary;
- A, duplicated visual+text: the same image and summary plus lossless dense
  metric/edge text;
- B, full text-only: text byte-identical to A, with no image.

All conditions compile from the same CEB and source fact inventory. The common
summary is byte-identical. D deliberately transports dense curves and topology
through pixels rather than exact-scalar text; this is therefore an equal-source
representation mechanism test, not a replacement equal-information endpoint.

## Frozen development protocol

- 24 already exposed development incidents, eight per primary dataset;
- deterministic seed-42 roster, with no formal/reserve overlap and all SFT v1/v2
  heldout cases excluded;
- Qwen3.6-27B and Gemma-4-26B-A4B-it, both mandatory;
- 24 × 3 × 2 = 144 main calls, plus three-case-per-model smoke;
- unquantized BF16 eager vLLM, 32k context, 16k output cap, temperature 0,
  top-p 1, seed 42, thinking off, and GPU-memory ceiling 0.65;
- six D/A/B orders balanced exactly four times per model;
- future project-owned `CanvasRCAGranularityAwareScoringV1` scoring contract.

The development gate requires D−B at least +0.05 on both models, at least three
more improved than degraded pairs on each, no dataset reversal at or below
−0.10, D−A positive on both, parse at least 0.95, and complete infrastructure
pairing. Passing would only permit a separate fresh preregistration; failing
stops this representation before reserve data.

## Results

Both smoke runs completed 9/9 calls. Both main runs completed 72/72 calls, for
144 main calls total. Parse rate was 1.0 in every arm, there were no
infrastructure failures or truncations, all live/server token counts matched,
the six arm orders occurred exactly four times per model, and all leakage,
CEB/fact-hash and representation audits passed.

| model | D MRR | A MRR | B MRR | D−B | improve/degrade/tie | D−A | gate |
|---|---:|---:|---:|---:|---:|---:|:---:|
| Qwen3.6-27B | 0.4806 | 0.4806 | 0.5097 | −0.0292 | 0/2/22 | 0.0000 | fail |
| Gemma-4-26B-A4B-it | 0.5813 | 0.4958 | 0.4250 | +0.1563 | 6/1/17 | +0.0854 | pass |

Qwen's D−B effect was zero on AegisLab and AIOPS-2022 and −0.0875 on
AIOPS-2025. Gemma's effect was positive on all three datasets: +0.1563,
+0.2188, and +0.0938. Its descriptive paired Wilcoxon p was 0.0336 and paired
Cohen's d was 0.465. These are development statistics, not confirmatory tests.
The mandatory cross-model gate failed because Qwen did not benefit. No
reserve/formal case was opened.

The mean input-token counts (D/A/B) were 5,569/11,215/9,253 for Qwen and
4,219/9,919/9,647 for Gemma. Gemma's result supports the allocation premise for
that architecture, but D and B differ in two simultaneous ways: D adds an image
and removes the lossless dense-text appendix. That comparison alone cannot say
which change caused the gain.

## Decision

The registered cross-model development gate remains failed. This experiment
does not rescue or modify the completed RQ0 endpoint, and it does not authorize
reserve/formal use. D−B changes both transport modality and redundancy, so it
cannot isolate image presence. Any future modality comparison must expose the
same complete model-visible atomic facts in every arm.

## Artifacts

- Plan: `plans/2026-07-31_nonredundant_modality_allocation_development_plan.md`
- Configuration: `RQs/RQ0/configs/experiments/rq0_nonredundant_modality_allocation_v1.yaml`
- Frozen roster: `RQs/RQ0/configs/nonredundant_allocation_development_roster.json`
- Runs and analysis: `RQs/RQ0/results/rq0_nonredundant_modality_allocation_v1/`
