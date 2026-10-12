# SEARCH32 first launch — zero-call worker preflight failure

The server started, but worker candidate validation still required a flat JSON
list while the registered input now used `[ID, type]` rows. The request layer's
typed-row CPU tests passed, but did not cover this second worker parser.
The worker correctly refused the mismatch before tokenizer/model submission.
Call database confirms zero rows for this batch; no model output exists.
Supervisor exited after108.137s and stopped its server normally.

Preserve `worker.log`, `qualification.json`, runtime and the original dependent
source snapshot. This is an implementation failure, not a model outcome.
Successor `../candidate_types_development_v2/` uses the identical24 registered
inputs after both paths share the same strict parser and worker tests cover
flat and typed lists. No previous scientific response is rerun or discarded.
