# 2026-09-14 — Literature-backed, selection-only tournament catalogue

## Scope and status

RQ3 elimination tournament, CPU implementation/review only. No new LLM calls,
training, attention collection or round registration. Completed rounds 1–16 and
their cohorts/results remain unchanged. Policy contract and literature reading:
[DD-RQ3-TOURNAMENT-17](../../../../../../../../RQs/RQ3/descriptions/RQ3_experiments.md#selection-only).

## What happened

- Reviewed existing references and additional primary sources on propagation,
  log novelty, change points and RCA trajectory failures. Venue/code provenance
  and non-transferable assumptions are recorded in the contract, not inferred
  from paper names.
- Consolidated twelve unused development-policy IDs into historical/not-scheduled
  entries. Implemented six pending mechanisms: diagnostic coverage, log surprise,
  trace self-time increase, window change, variability shift and call frontier.
- Vendored the official ruptures L2 cost dependency closure. Three source files
  plus the BSD license match upstream bytes; adaptations are local imports only.
- Added per-round configuration guards: renderer, static prompt, transport,
  field budgets and model recipes cannot drift under a selection-only method.
- Full CPU suite: **141 passed in 73.05 seconds**. After the final audit-cache and
  concise-output changes, selection-focused regression: **19 passed**.
- Full remaining union: Qwen 125, Gemma 104, union 158. The final audit is at
  [final/summary.json](../../../../../../../../RQs/RQ3/results/selection_only_review_20260914/final/summary.json); its identity includes the native
  adapted source hashes. The earlier top-level audit is a preliminary catalogue
  snapshot, not a competing result set.
- Eighteen previews rendered successfully: three hash-selected public cases ×
  six policies. [Input audit](../../../../../../../../RQs/RQ3/results/selection_only_review_20260914/gallery/input_audit.json) verifies decoded pixels,
  prompt/candidate equality, source identity, primitive coverage and geometry,
  image persistence and leakage against the round-16 inputs. Fifteen images
  change; the remaining three are natural unchanged selections. Six actual PNGs
  were opened, covering every policy and all three primary datasets. No renderer
  change was made to accommodate a method.

## Validity and caveats

Each source fact retains its original values; internal selector scores never
enter the model prompt. Counts of M/R/L/G entries follow the round-16 anchor;
public service–pod closure follows the same rule. Rendered positions can respond
to different selected owners under the unchanged grouping algorithm.

Fact-set changes over the 158-case union: coverage 156, logs 153, traces 106,
windows 158, variance 157, frontier 153. These are **not accuracy gains**. The
full-pool audit's textual hash is a comparison projection, not the visual
Solver's actual input text. Exact prompt and decoded-PNG checks cover the
18-preview review separately.

The native cost computation, source equality, deterministic selection, field
budgets, constant/nonfinite/gapped data and configuration guards passed. Forty-
three renderer/prompt/local-runtime files match the round-16 frozen tree. Parent
integrity checks pass. Source modules remain below the current 10,000-line limit.

The public trace pool still inherits its existing admissibility restrictions;
a selector cannot recover telemetry absent from that pool. No new success rate,
model reliability, truncation rate or deployment benefit is claimed from CPU
tests. Every future inference round uses all unretired cases for each model,
not the three-case visual-inspection subset.

## Decisions

Future rounds change evidence selection only. Keep a complementary catalogue
instead of modality-dropping/display variants. Published mechanisms motivate
selectors but do not certify diagnostic quality; project-designed heuristics
are explicitly distinguished from copied original components. Keep unchanged
selections visible, rather than forcing arbitrary differences.

## Blockers and fixes

Two preview invocation defects were encountered and repaired before review:
Python multiprocessing spawn cannot restart a `<stdin>` entry, so preview now
has a module CLI; relative source paths failed `relative_to(ROOT)`, so preview
resolves paths at entry. A regression covers the latter. Full score dictionaries
were initially printed to the console; the CLI now prints a short summary while
retaining detailed audits on disk. No model request or historical experiment
was affected by these CPU-review defects.

No blocking defect was found in the completed CPU/input review. Live inference
behaviour remains to be tested by the next authorized tournament round.

## Next steps

1. Register `diagnostic_cover_v2` from `tournament_selection_only_v4.yaml` against
   the then-current complete remaining cohorts.
2. Render/review every registered input, then run Qwen and Gemma sequentially.
3. Finalize AC@1 retirement before registering the next mechanism. Do not reuse
   this preview subset as an inference cohort or tune using hidden root labels.
4. Continue through logs, traces, windows, variance and frontier as needed;
   measure newly retired cases, costs and failures without promising each round
   will improve coverage.
