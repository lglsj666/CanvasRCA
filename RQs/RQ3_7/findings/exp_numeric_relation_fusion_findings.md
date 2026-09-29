# exp_numeric_relation_fusion

Status (2026-09-28): complete repeated-exposed development experiment, including
the user-authorized 120-call TPV unit-label supplement. No C/test inference.
Protocol: `../descriptions/RQ3_7_experiments.md`.

Detailed Chinese report and reproducible assets:
[RQ3.7 analysis](../../../docs/experiment_reports/RQ3_7_Results_Analysis_2026-09-28.md).

- Five-arm common cohort: Qwen177, Gemma180; historical comparisons intersect
  available references. Infrastructure failures are not model zeros.
- Qwen LOCAL_LINK vs TPV: n175, paired MRR .400476→.477619,
  delta+.077143, primary-eight Holm p=.017080, dz=.266591, AC@1 repair17/break1.
- Qwen vs T_MATCH: delta+.077213, Holm=.207833; vs B3_G: +.027936,
  Holm=.513511; vs REMOTE_ID: +.028719, Holm=.718053.
- Gemma LOCAL_LINK=.297222 vs B3_G=.366667; delta−.069444,
  primary Holm=.069249. No confirmed cross-model gain.
- Neither proximity, linking nor interaction passes the registered factorial
  family. The TPV gain is a system comparison, not identified layout causality.
- Only44/180cases (all AegisLab) have genuine continuous bars; other cases retain
  accurate numeric readings. All180 five-arm fact/panel identities and visual
  common-geometry identities agree; all four visual pixel identities differ.
- Root levels and exact fault types, repair/break, costs and nine reviewed
  cases are preserved in the report. Correct ranks can have unsupported edges
  or wrong entity-type wording. No hidden-reasoning claim.

Historical implementation status: the original static-only delivery produced no
results; DD-RQ37-1 pruned B3_T generation. DD-RQ37-2 subsequently authorized only
the specified120 TPV calls. Three historical timeout references remain missing.
