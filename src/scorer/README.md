# CanvasRCA RCA scorer

All new experiments import ranking and matching functions from this package:

```python
from scorer import RCAScorer, RCAScorerConfig, score_bound_response

scorer = RCAScorer(RCAScorerConfig.load())
```

CLI: `PYTHONPATH=src:. python -m scorer prediction.json --accepted ENTITY`.
Model-response validation should use `score_bound_response` with the frozen
candidate mapping and registered response schema.

`core.py` owns rank, MRR, AC@1/3/5, AVG@3/5 and bound-response validation.
`matching.py` owns name normalization, service/pod projection and granularity
matching. Configuration remains `configs/rca_scorer.yaml`. These are copies of
existing project logic with unchanged arithmetic and matching behavior; source
locations and hashes are in `PROVENANCE.json`.

There are no compatibility aliases at old scoring paths. Historical RQ2.1,
unified-script and evaluator source copies remain unchanged for audit purposes;
new code must not import those copies. The new scorer imports neither a
historical renderer nor an external RCA checkout, and does not consult
`RL_SLM_RCA_ROOT`. Installed Python libraries and the project-owned common
configuration classes remain ordinary dependencies.

Independent QA has its own registered task-specific grading protocol. This
package is the authority for RCA root-cause ranking, not a replacement of QA
answers with RCA labels. No historical scores are rewritten by this migration.
