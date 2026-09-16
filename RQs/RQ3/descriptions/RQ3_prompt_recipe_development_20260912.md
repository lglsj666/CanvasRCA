# RQ3 prompt and non-thinking recipe development — 2026-09-12

## DD-RQ3-SEARCH-6 — Independent prompt/sampling contrast

Status: completed train-only development, 36/36 new calls; no training,
validation, eval or new attention. No target achieved. Results and DD-SEARCH-7:
`../results/search_first_v1/prompt_recipe_development_v1/logs/20260912_review.md`.
Continue the same publicly selected twelve train cases and ranked_v1 packets
from selection_development_v1. No cases are selected by score or private label.
Candidate lists stay exclusively in prompt text; diagnostic facts remain in
one image. The new gallery must match the earlier ranked PNG bytes exactly.

The previous 72-call batch found omitted entities and unsupported relationships,
including cases where a correct ranking had an inaccurate reason. The appended
grounding warning did not consistently improve results. Test a shorter RCA
procedure that does not demand a fixed number of verification claims and that
retains explicit ID, uncertainty, local-latency and cause-versus-victim guidance.
The common visual-reading guide and frozen scorer/schema remain unchanged.

Cross two prompt conditions (inherited_v1, concise_v1) with two request recipes:

- legacy_v1: exact current request parameters.
- card_nonthinking_v1: temperature .7, top-p .8, top-k 20, min-p 0,
  presence penalty 1.5, repetition penalty 1, thinking off; seed 42.

The second recipe is recommended by the [official Qwen3.8 model card](https://huggingface.co/Qwen/Qwen3.8-27B#best-practices),
verified on 2026-09-12 and against the locally downloaded README. It is not
presumed better for RCA; the same card warns of possible language mixing and
quality reductions at high presence penalties. No quantization, context,
8192-output cap, image processor or server change is included.

Reuse the twelve inherited/legacy responses unchanged from the completed batch.
Generate the other three cells, 36 new calls, concurrency four, one-hour bound.
This is small train development, not an extra nominal smoke or final efficacy
evaluation. Every attempted call and model failure remains in the results.

The shared default YAML and client stay unchanged. The existing explicit
VLMConfig.extra request-adapter path carries the RQ3-only sampling change.
Each request envelope records the adapter and actual effective sampling in
addition to the base server recipe. CPU tests must inspect the actual serialized
SDK kwargs, not merely the configuration label, and ensure the old path is
unchanged. The new gallery records full prompts and candidate bindings.

Inspect actual prompt/image equality, responses, raw/partial artifacts and
accounting before interpreting any scores. A small favorable cell does not
authorize eval or training. Report both datasets separately and retain the
baseline source pointers; do not claim four freshly independent runs.
