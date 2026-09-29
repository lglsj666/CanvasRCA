# RQ3.2 findings — 2026-09-22

Authoritative detailed analysis: [RQ3.2 quantitative, qualitative and pattern report](../../../docs/RQ3_2_Results_Analysis_2026-09-22.md).

Scope: only the completed `formal_signal_cover_v2` run; current logical task
identities, not an indiscriminate union of historical output files. 27,280
terminal logical units comprise 26,995 scored outputs (346 model failures),
129 timeout causes and 156 non-applicable interventions. One noncurrent output
is excluded without deleting it. No inference or experiment changes were made
for this analysis.

Main findings:

- SC restores much of X's missing node telemetry, but does not consistently
  outperform P0 or strong T/TPV/SIRCL_TEXT baselines.
- Both models lose accuracy with SC full vision relative to its text carrier;
  Metrics-in-text recovers part, but not all, of that loss.
- Root-associated fact removal is more damaging than matched non-target
  removal in several pooled mechanism contrasts. Applicability and hard-dataset
  power limits are explicit in the report.
- Rank success does not ensure factual or entity-binding correctness of the
  public reason; actual input/output examples are linked.
- Some intended contrasts were not implemented as named. The text NO_GROUPING
  input is identical; P0_MORE changes selection, not just capacity; the common
  guide retains midpoint statistics while aligned inputs use a public P0
  split. Interpret actual pipeline outcomes, not idealized interventions.

The report contains 10 statistical figures, 2 original model-visible dashboard
examples, all-arm CSVs, paired tests, case metadata, cost checks and scripts.
No historical validity status is silently changed; no next experiment is
started by this findings entry.
