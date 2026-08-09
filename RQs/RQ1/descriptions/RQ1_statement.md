# RQ1 Statement

## Research question

Under equal-information and equal-compute conditions, does visual-text,
topology-aware observability improve VLM-based root-cause ranking over
text-only and flat structured representations, and which observability
operations exhibit stable modality complementarity?

## Interpretation

RQ1 separates three claims:

1. a model can read facts from a dashboard;
2. visual evidence changes what the model carries through an agent handoff; and
3. that change improves the final ranked root-cause answer.

Perception and structured-operation accuracy explain mechanisms but cannot
establish an RCA improvement. The RCA endpoint is the frozen ranked top-five
JSON evaluated with the unified scorer; its primary metric is MRR.

All representation comparisons are compiled from one label-blind evidence
packet. A fact may move between text, flat records, and pixels, or be duplicated
only in a preregistered strict hybrid, but no compared arm may gain or lose an
incident fact. The topology graph is a representation region, not an additional
raw data source.

