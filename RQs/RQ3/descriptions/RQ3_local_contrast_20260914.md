# Round 14: trace-linked local contrast on every remaining case

**Status:** registered successor; model execution requires the normal source,
gallery, prompt, leakage, visual, and cohort audits.

Round 13 showed that changing the log transport alone almost never promoted a
remaining root to rank one. Round 14 therefore changes evidence selection and
uses the already implemented, label-blind `local_contrast_v1` policy. It ranks
24 metric series while prioritizing public trace-associated entities, distinct
resource-relevant metric families, and stronger public baseline/current shift.
Private labels, fault types, dataset identities, raw case IDs, natural entity
names, absolute time, and injection time are not selector inputs.

The method runs on **all** cases left unretired for each model after round 13;
there is no discovery subset. M/R/L/G evidence remains in one dashboard image,
the candidate list remains text, and the frozen tournament task, procedure,
output schema, scorer, model recipes, sampling, and attention-off contract do
not change. Natural input aliases are reused; wrong or failed outcomes are not
resampled. Both models run sequentially before another method is introduced.

This is a CanvasRCA selection intervention rather than a reproduction of an
external RCA system. Its purpose is to test whether entity-local resource
contrast supplies complementary top-one coverage, especially on the remaining
AIOPS cases. Low accuracy is not an implementation failure and does not justify
changing the registered method after observing outcomes.
