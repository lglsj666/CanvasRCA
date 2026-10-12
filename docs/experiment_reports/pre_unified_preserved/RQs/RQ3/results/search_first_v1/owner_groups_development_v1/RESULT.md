# SEARCH30 — Related-owner compound cards

2026-09-12. Completed **train-only exploration**, not validation or evaluation.
24 paired cases, 12 per dataset: 20 new requests and four verified exact-input
references. One real PNG, candidates in prompt, no attention, no Composer or
training. Work-spec `288040bfc37513c3ca8c7ac32ee6f38a778e581c6b7aa16a775d5eeeffff8bc1`.

| Dataset | Reference MRR | Joint-card MRR | ΔMRR | Input tokens old/new | Output tokens old/new |
|---|---:|---:|---:|---:|---:|
| AIOPS-2022 | 0.506944 | 0.479167 | −0.027778 | 17754 / 17754 | 253.42 / 258.08 |
| AIOPS-2025 | 0.440278 | 0.277778 | −0.162500 | 17648.83 / 17648.83 | 254.33 / 245.58 |

Both exploratory Holm-adjusted p=0.75; paired dz=−0.10235/−0.41241.
Two repairs, five breaks, seventeen ties, including four referenced no-ops.
The 20 changed-input cases alone are not substituted for the registered cohort.
All model calls ended normally; maximum output367, no parse/infrastructure
failure or truncation. Batch wall time305.211s includes server lifecycle.
All20 new full answers and four referenced answers inspected, along with actual
persisted images/prompts, common conversation shell and complete artifact hashes.
No service remains owned by this batch.

## Interpretation

Not promoted. Associating publicly linked M/R/L rows in compound cards is not
sufficient to improve this cohort's RCA. Two previously correct A25 roots fall
outside the ranking after large RTT/pod panels become focal explanations.
For example, 56FC27993C6C now attributes the incident to service409 and calls
RTT a resource-exhaustion signal; D142F47FE539 prioritizes pod17272's RTT over
the original database-related hypothesis. These observations support an
attention/emphasis hypothesis only through visible answers, not measured
attention or proof of internal reasoning. The new route collected no attention.

0BD935F7BAAE improves RR0.5→1 with aligned pod CPU, logs and public service
membership. 492AFB4CE9D6 improves0.2→1/3 but still leads with an unsupported
node-origin story. The same recurring failures remain: large standardized
changes mistaken for exhaustion, heuristic onset treated as cause, operation
endpoints conflated with owners, and invented hosting/propagation. None is
repaired by changing the scorer or removing hard cases.

This is a small repeatedly exposed training subset. It neither establishes a
general negative effect nor meets the user's per-dataset/overall targets.
Keep the original modality layout as an anchor; do not advance this strategy
to validation/eval/SFT/RL. Full per-fault/granularity/cost rows are in
`metrics_breakdown.json`, paired rows in `paired_review.json`, and the offline
complete-answer review in `private/answers_review.md`.

## Provenance and rejected prototypes

The first balancing layout joined unrelated owners; it was CPU-rejected before
inference. The adopted v2 groups only one public-associated owner with at least
two modalities. All source facts, curve samples and prompt text remain equal;
24/24 public audits and237 CPU tests passed. Four exact-native PNG cases are
referenced in `reuse.json`, not relabeled as fresh calls. Current dependent
source/configuration bytes are archived in `private/source_snapshot.tar.gz`.
The original SEARCH23 records remain untouched.
