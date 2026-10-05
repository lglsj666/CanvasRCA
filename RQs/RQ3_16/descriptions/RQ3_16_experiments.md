# RQ3.16 registered protocol — 2026-10-03 America/Toronto

Authority: implement, static check, complete CPU/visual qualification, bounded GPU
smoke, then stop. Formal execution is disabled in both configuration and gates.
Single primary agent; no training, attention, external models or new test scores.

## Inputs and hypotheses

Keep RQ3.15's complete 60 AIOPS-2022 / 60 AIOPS-2025 / 100 AegisLab eval roster,
event groups, WINDOW_TEXT, RequestPairPacketV1, candidate order, system prompt,
pair-selection/sampling/unit/window definitions and exact marginal PNGs. Inherit
the documented source-level numerical qualification; verify frozen packet/image
identity rather than pretend this experiment re-extracted all raw Trace rows.
Nine inapplicable cases retain their denominator and revert to the corresponding
BASE input. Never display an empty or missing-value panel.

Eight arms: BASE_FLEX, PAIR_FLEX, MARGINAL_FLEX, BASE_FIVE, PAIR_FIVE,
MARGINAL_FIVE (preselected), MARKLESS_FIVE, MARGINAL_REPEAT. FLEX uses the original
schema and prompts. All FIVE arms insert the same cardinality instruction and
change only services.minItems 1 to 5; maxItems remains 5. The canonical scorer,
JSON fields, candidate domain and decoding recipe do not change. No posthoc
padding, deduplication, reranking or favorable repeat selection. Fewer than five
public candidates is a CPU failure. A repeat is always an independent new call.

FLEX arms are explicitly charged contemporaneous replications, hash-interleaved
with the new arms to separate output-policy effects from run batches. Historical
outputs remain immutable and are not pooled as new independent observations.
Fixed-five is a schema-plus-instruction intervention, not an isolated schema or
reasoning effect. Report MRR, top-1 and reason consistency alongside top-5.

MARKLESS uses the same numerical text, component, layout, font, axes, range,
phase legend, support and operation labels, with only sample glyphs removed.
It retains axis information; do not describe it as blank/no visual information.
The registered trace_joint.marginals component now consumes the existing marks
presentation switch. Default output must reproduce representative historical
PNG bytes. No new component/operation or local drawing. Preserve missing-point
line semantics and all historical artifacts. The point samples are rank-selected
observations, not population density or causal/local-execution estimates.

## Statistics and adoption

Four primary contrasts form one Holm family at case level and a separate identical
family at equal-weight event-group level: MARGINAL_FIVE minus PAIR_FIVE (220),
minus MARKLESS_FIVE (220), minus BASE_FIVE in AIOPS (120), and in AegisLab (100).
Use two-sided Pratt-zero Wilcoxon with differences rounded to 12 decimals and
paired dz; no CI. Aggregate case differences within dataset/event group before
group-level testing. Model failures are zero under the existing scorer;
infrastructure unknowns are excluded only from the affected contrast with known
coverage and full-denominator score bounds. Never set unknown usage to zero.

Seven secondary MRR contrasts share a separate Holm family: the three matched
FIVE-FLEX differences; MARGINAL_FLEX-PAIR_FLEX; PAIR_FLEX-BASE_FLEX;
MARGINAL_REPEAT-MARGINAL_FIVE; and the within-case interaction
(MARGINAL_FIVE-PAIR_FIVE)-(MARGINAL_FLEX-PAIR_FLEX). Repeat those seven for an
explicitly separate AC@5 coverage family. Interaction needs all four outcomes;
its unknown-case bounds follow the signed coefficients, up to [-2,2].

Adoption requires all four primary directions positive and case/group Holm p<.05;
MRR delta >=.02 against PAIR_FIVE overall, >=.03 against BASE_FIVE on AIOPS,
>=.02 on AegisLab; each dataset positive against both text controls. Each dataset
must also have nonnegative paired AC@5 differences against BASE_FIVE/PAIR_FIVE
(a necessary point-estimate guard, not a statistical noninferiority claim).
Actual input+output per-dataset cost <=1.20x BASE_FIVE and <=1.10x PAIR_FIVE;
CPU checks the corresponding exact processor-input budgets. Report all six
absolute scoring metrics, pooled/macro, failures, granularity/fault strata,
repair/breaks, list lengths and usage. Preselect 12 hash-selected cases/dataset
for complete eight-arm reason inspection; unsupported claims remain unknown.

Any failed adoption condition stops this marginal candidate. Do not switch to
posthoc best FLEX/repeat, change layout or seek a favorable test subset. Exposed
eval and limited event groups do not establish independent confirmation/power.

## Execution and accounting

Formal registration: 1,760 positions, expected 45 exact fallback references;
1,802 formal attempts plus one 18-attempt smoke, total 1,820. Historical ledgers
remain separate, consumed and immutable. No attempt counter reset. Pending
infrastructure failures require explicit repair; model errors stay scored.
Completed-call markers are atomic boundaries; completed phases skip before GPU
or context materialization. Only missing commitments are resumable work.

Static source/config checks precede full 220-case CPU preparation, at most eight
distinct physical-core workers, source/cloudbed interleaved. Reuse 211 marginal
PNGs and generate only 211 markless controls through src/renderer. Audit actual
DOM geometry/bindings, text/fact equality, all token budgets, numerical/statistical
oracles, source protection, fallback and safe resume. Open actual PNGs from all
three datasets and sparse/extreme/long-name public cases. Primary-agent scientific,
visual and ledger reviews are required, explicitly not independent external review.

GPU smoke uses the inherited three eval IDs and the fixed per-dataset six-arm
matrix in config, covering all eight request paths at least twice: <=18 calls,
one cumulative 600-second wall window. Local Qwen BF16, max context 40,960,
request output 8,192, GPU memory utilization .75, original decoding. Score is
never the smoke acceptance criterion. Inspect every actual input/PNG/output/usage
and preserve errors. Close owned services after smoke and stop. Full authorization
is false and the full gate rejects; no automatic next-stage command exists.
