# Registered experiment protocol and implementation notes

The authoritative machine-readable registration is `../configs/protocol_v1.json`. The approved plan explains all interventions. This document records implementation differences, not new scientific degrees of freedom.

| New condition | Family |
|---|---|
| V_EXACT_DOMAIN | organization |
| V_SAMPLE_GLYPH | organization |
| V_SAMPLE_PACK | organization |
| V_SAMPLE_MARKLESS | organization |
| H_SAMPLE_GLYPH | organization |
| H_SAMPLE_PACK | organization |
| H_SAMPLE_MARKLESS | organization |
| F_O_SPATIAL | fusion |
| F_O_FEATURE | fusion |
| F_O_REP | fusion |
| F_O_SHAM | fusion |
| P_INK | pruning |
| P_CARD | pruning |
| P_LENGTH_CONTROL | pruning |
| S_O_REDIST | attention |
| S_SINK_REDIST | attention |
| S_BG_REDIST | attention |
| S_O_MASK | attention |
| D14_DOMAIN_FIXED | density |
| D14_DOMAIN_PACK | density |

The 4,400 RCA, 900 one-question QA, 90 QA controls and 90 independent repeats give at most 5,480 scientific calls. Three future 18-call smoke scopes plus 166 infrastructure recoveries give 5,700 total. Every attempted request counts; exact references do not. Unused calls do not create new arms.

## Historical difference checklist

| Branch | Closest history | Actual new intervention / reuse |
|---|---|---|
| V sample organization | RQ4.9 V_MARGINAL_DIRECT, native marginals | User-approved complete-pair baseline adds frozen visible numeric/statistical fields. Same new baseline across EXACT/GLYPH/PACK/MARKLESS. No claim of identity to historical native plot. |
| H sample organization | RQ4.9 H_MARGINAL_DIRECT | Same remaining text and complete-pair source; omit only sample numerals, then reclaim columns or remove only sample points. H_EXACT answer reused. |
| O fusion | RQ4.9 E fusion / P_DOMAIN | D embeddings unchanged; aggregate O into at most min(256, floor(.05D)) original representative positions. No E-fusion rerun. |
| P_INK/P_CARD/length | RQ4.9 FULL/DOMAIN | Actual rendered pixel support, card-region context, or same-length alternative positions; FULL/DOMAIN reused. |
| O attention | RQ4.9 sink redistribution | Full outside transfer or matched sink/background transfer; all full-attention layers and no previous head eligibility thresholds. Full sequence retained. |
| D14 | RQ4.9 D14_FIXED/PACK | Exact old PNGs, now all D. Original E50 outputs reused in interaction. |
| QA | RQ4.8–4.9 | One question per call, oracle-blind tolerant extraction, answer priors/no-evidence control, consistent entity renaming instead of inconsistent statistic swaps. |

## Literature adaptation

- VisionZip, CVPR 2025, [official source](https://github.com/JIA-Lab-research/VisionZip): contextual aggregation motivates O fusion. We do not reproduce its model-specific importance selector; D is supplied by audited renderer support, and representative MRoPE stays original.
- [Vision Transformers Need Registers, ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/0b408293619f725fd30162af057e531a-Abstract-Conference.html): background-like features can serve computation. We do not add learned registers or assume background useless.
- [Attention Sinks: A “Catch, Tag, Release” Mechanism, NeurIPS 2025](https://papers.nips.cc/paper_files/paper/2025/hash/77cd5a17edf97293eab706caf9bfee39-Abstract-Conference.html): motivates function-sensitive controls. Our detector is operational, not proof of harmful sinks.
- Current receiver/QA contract follows `important_docs/qa_issues_constraints.md`: nonempty answers, actual input support, displayed precision, no answer-aware parsing, valid alternatives, partial multi-value credit only without wrong extras.

## Fixed numerical rules

Spatial region capacity below one representative per nonempty region is an explicit capacity failure. Ties use original token index and stable source IDs. Cosine assignment uses FP32 normalized features, deterministic first maximum, own-seed membership and stable zero-norm behavior. Means accumulate FP32 and cast back BF16; D is never overwritten.

GLYPH/MARKLESS keep EXACT positions even after removed pixels become background. PACK alone recomputes D. Sample circles and population-quantile circles are distinguished; only sample circles disappear in MARKLESS. P_INK compares actual processor patch RGB to a registered background-fill-only export with identical geometry. Pixel emptiness is not feature emptiness.

Attention uses the original Q/K/V, causal masks and native output gate. SINK and BG release the common per-head/query minimum of available mass. O_MASK normalizes text+D, whereas redistribution preserves text mass and redirects to D. Temporary probability tiles are bounded to 32 queries; no complete attention matrix is saved. All actual group assignments and transfer/no-op counts are retained.

## QA acceptance and source policy

Thirty cases (10 per dataset) and three semantic questions are fixed before comparing methods. Public source hashes, displayed strings and actual input locators accompany each answer. A text representation may use its own visible fact ID; no backend-only locator is exposed. A target cannot be replaced based on QA/RCA outcomes. A failed visibility or precision proof blocks qualification rather than inventing an answer. Identity renaming is skipped only for a documented collision/inapplicability, never because of the model answer.

The no-evidence control carries only its one question and response instructions; it does not receive candidate IDs or diagnostic evidence as auxiliary text. Binding question wording must not disclose the asked entity. The answer extractor sees public question/type/vocabulary information, never `solutions`. Invalid IDs are filtered individually; conflicting valid answers remain ambiguous. Required multi-value proper nonempty correct subsets score 0.5, wrong extra values score 0.

## Frozen inference and reporting

Six comparison families retain their exact lists in config, including the four-term D14 display interaction. Event-group Pratt-zero signed-rank is primary; case differences and case-weighted delta are also reported. Twelve-decimal differences, paired dz, within-family Holm, no confidence intervals. Signed-rank is not described as an arbitrary mean-null test. QA items never inflate the independent-case count.

Historical answers retain backend/time provenance. Full denominators include model-invalid zeros and unknown infrastructure omissions separately. Report actual input/output tokens and timing; references save research calls but not logical deployment cost. Three nominees remain V_SAMPLE_PACK, F_O_FEATURE and H_SAMPLE_PACK even if another arm has the largest mean.
