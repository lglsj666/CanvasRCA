# 2026-08-27 — RQ1.1 multimodal-attention static qualification

## Scope and status

RQ1.1 now records image and text attention in the original generation prefill,
without an extra model call or a second forward replay. This session performed
implementation, source audit, and CPU/static qualification only. It did not run
preparation, smoke inference, a gate, or a formal experiment. Formal execution
remains disabled in `RQs/RQ1_1/configs/rq1.yaml` pending bounded live smokes.

Protected historical RQ1 results and `docs/RQ1_report.md` were not changed. The
interrupted RQ1.1 result tree was removed earlier at the user's direction. Its
canonical preparation had lived inside that tree and therefore must be rebuilt
deterministically before the next smoke; attention collection itself does not
change the evidence preparation.

## Implemented protocol

- Every RQ1.1 request uses a custom request ID and requires a same-prefill
  attention sidecar from the registered first full-attention layer.
- The probe records the final prompt query's normalized attention over all
  preceding prompt keys, so image and text mass are directly comparable.
- Text tokens are mapped to task shell, candidate/common content, M/R/L/G
  evidence, tool history, and unassigned chat/control tokens. Boundary matching
  tolerates only the small tokenizer-template discrepancy explicitly audited by
  the static tests.
- Visual calls additionally record image-token weights, per-token value norms,
  pre-output-projection attention-weighted value norms, 16×16 grids, overlays,
  image hashes, and M/R/L/G crop aggregates.
- The first grid row is reported separately as `dashboard_header_band`; the
  top-left patch has its own rank and peak-to-median diagnostics. This is a
  grid-resolution diagnostic, not pixel-exact title segmentation.
- Text-only calls receive the same attention-integrity requirement. Missing,
  duplicate, hash-mismatched, or non-conserving artifacts fail verification.
- The probe observes tensors only; it does not modify Q/K/V, logits, sampling,
  prompts, responses, call count, or any scientific model setting.

## Title/top-left hotspot interpretation

The historical representative overlays were re-audited at their raw 16×16
grid level. The first row contained 41.1% of Qwen3.6, 41.4% of Qwen3.8, and
27.3% of Gemma visual-conditional mass for the inspected case. The
concentration is present in the captured weights, but the old visualization
made its absolute importance look stronger by normalizing only over visual
keys, scaling each overlay to its own maximum, and expanding a coarse grid over
the full image.

Accordingly, the project records this pattern only as a positional or
attention-sink candidate. A high attention weight can coexist with a low value
or attention-weighted-value contribution. It can also reflect positional bias,
a register-like token, or a mapping/display artifact. A causal sink claim needs
registered position/content interventions such as moving the image, replacing
the top-left content, and controlled ablation. These are future controls, not
silently added RQ1.1 arms.

## Static qualification

All final checks passed with zero model calls:

- Ruff `F`, `E9`, and `B023` checks over shared source, RQ1.1, and RQ2;
- Python bytecode compilation over the same trees;
- RQ1.1 static protocol suite, including both-model CPU tensor capture,
  all-prompt mass conservation, text span mapping, synthetic high-attention /
  low-contribution discrimination, seven-arm equality, renderer inheritance,
  4/12/24/24 QA templates, Denum semantic round-trip, four search tools,
  anonymization, and local/Nibi inference parity;
- RQ2 static regression suite;
- shell syntax checks and JSON/YAML parsing;
- `git diff --check`.

The final RQ1.1 static hash is
`65ccad38455e4bc72ae9b51d15dd18e60ad6e0c3bbbdb7bd916cae00127ce220`.
The implementation contains 3,230 functional Python lines and ten RQ shell
files totaling 321 lines, within the project limits.

## Repository portability

`.gitignore` ignores root `results/`, every current RQ `results/`, and future
`RQs/<rq>/results/` paths. No result file is currently tracked. `packages/ReAct`
and `packages/Denum` contain no nested Git repository and are not ignored; a
dry-run stage sees them as ordinary files. Together they occupy about 33 MB,
with a largest file of about 15.5 MB. Their license files and
`packages/THIRD_PARTY_SOURCES.json` are present, so a future commit will carry
the pinned reference sources into an ordinary GitHub checkout rather than
creating broken submodules.

## Next authorized step

Rebuild canonical preparation, then run the registered bounded smoke for each
experiment and inspect completed prompts, conversations, raw responses, tool
records, partial outputs, and attention artifacts. Do not freeze or start a
formal queue until those live checks pass.
