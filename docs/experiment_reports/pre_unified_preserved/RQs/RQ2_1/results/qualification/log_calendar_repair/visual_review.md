# Corrected log projection review — 2026-09-08

The assistant opened the actual corrected PNGs for INC-8E91494BF92F
(P_LOG_FREQ and P_RANDOM), INC-9DDF62CAF256 (P0), and INC-D9ABFB644D29
(P_RANDOM). The final P_LOG_FREQ image was viewed again after adding complete
Java-date parsing. Logs retain diagnostic duration, event text, counts, bins
and LOG-R; dates are removed without adding a prompt explanation. No new
clipping or image layout defect was seen. Non-L facts and card pixels were
checked by the CPU migration. A one-pixel L top-border mismatch between the
first migration and the production renderer was found by fresh regeneration,
fixed by applying the same header compositor, and 24/24 fresh input files then
matched exactly. No model ran against an intermediate migration.

The updated scan found no residual matched calendar representation in 5,272
selected log rows. Eighty long-number rows were not indiscriminately erased:
their examples are ticket inventory counts, not timestamps. Nine sanitizer
tests distinguish dates from status codes, durations, version triples and
large counts. This is a targeted safety audit, not a proof that arbitrary
unseen log formats can never contain metadata.

Actual PNG bytes are included in the smoke comparison. A comparison which
omits the in-memory `png` member cannot establish image equality; that audit
helper was corrected. Formal reuse already uses the actual decoded RGB pixels
and therefore was not affected by this helper oversight. Of 56 qualified
logical records, 54 current inputs are unchanged; the two affected Gemma image
conditions retain their original historical smoke records and receive the
documented CPU/native-processor/manual projection correction. No new live-call
coverage is invented, and no model/scoring/prompt setting changed.
