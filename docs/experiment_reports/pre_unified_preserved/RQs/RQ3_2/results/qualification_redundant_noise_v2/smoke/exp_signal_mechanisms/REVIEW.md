# 2026-09-22 — `REDUNDANT_NOISE region_capped_v2` qualification review

## Scope and status

- Qualification-only successor; not an efficacy result.
- Registered dimension: `REDUNDANT_NOISE / M_TEXT / replicate 0`.
- Real smoke roster: one case each from RE2-OB, AIOPS-2022 and AIOPS-2025.
- Models ran sequentially: Qwen3.8-27B, then Gemma-4-26B-A4B.
- Six of six requests completed inside the shared 600-second window, with zero
  infrastructure, timeout, parser or model-output failures.

## Artifact review

- Six completion markers, conversations, inputs, outputs, costs, trajectories
  and renders are present.
- Every hash named by all six atomic completion markers matches the persisted
  bytes.
- Both model phase markers report complete, with three calls each.
- All six responses are valid scored JSON and use only candidate IDs. Smoke
  accuracy was not used as a passage gate.
- The three case-specific images are byte-identical across models, as required.

## Visual and prompt review

All three unique PNGs were opened at original resolution. Trace bars, topology
edges/ledgers and the one- or two-row log blocks remain inside their registered
panels; no overlap, clipping or hidden overflow was found. The model-visible
prompts contain the mixed-carrier guide, complete candidate list and the
expected `REDUNDANT_NOISE` evidence. No private label, dataset name, file path
or absolute injection time was found in the inspected carriers.

## Decision

The fixed-canvas repair is qualified for formal continuation. Both
representations of the full formal `REDUNDANT_NOISE` condition are re-evaluated
under the new logical version. Byte-identical requests may reuse their
content-addressed prior result; requests whose facts changed require a new call.
