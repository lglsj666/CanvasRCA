# RQ4.9 — evidence, differences, and interpretation

This attachment implements the approved 2026-10-21 protocol. It does not change
historical findings, register a new method after observing results, or authorize
execution independently of the version-bound qualification files.

## Historical evidence used

| Evidence | Status and limitation | Consequence in RQ4.9 |
|---|---|---|
| [RQ3.16](../../../docs/experiment_reports/RQ3_16_Qwen_Analysis_2026-10-03.md) | Completed. MARGINAL_FIVE 0.5054; markless 0.4963. The former repeats facts already supplied in text. | Reuse the historical result; compare visible points against a point-only control, rather than attributing the whole hybrid score to dots. |
| [RQ3.17](../../../docs/experiment_reports/RQ3_17_Qwen_Analysis_2026-10-04.md) | Completed combination study; full topology did not establish an improvement over native marginals. | No new topology-plus-marginal combination search. |
| [RQ3.20](../../../docs/experiment_reports/RQ3_20_Qwen_Analysis_2026-10-06.md) | Completed two-stage acquisition study with selector/interface losses. | All RQ4.9 RCA requests are independent single calls. |
| [RQ3.21](../../../docs/experiment_reports/RQ3_21_Qwen_Analysis_2026-10-06.md) | Completed evidence-organization study. Compact strings saved input but lost ranking quality. | Residual hybrid text retains the strong-input organization and numeric spelling. |
| [RQ4.1](../../../docs/experiment_reports/RQ4_1_Qwen_Analysis_2026-10-09.md) | Completed. A_UNIFORM_E50 0.3517 was the best visual point estimate, not the preselected winner. | Preserve its deterministic spatial rule; use a new concurrent U28 because the canvas and selected facts change. |
| [RQ4.2](../../../docs/experiment_reports/RQ4_2_Qwen_Analysis_2026-10-10.md) | Completed source-partition experiment; no established improvement over historical U. | Fusion changes the actual embeddings, rather than rerunning encoder partitions. |
| [RQ4.3](../../../docs/experiment_reports/RQ4_3_Qwen_Analysis_2026-10-12.md) | Completed; local processing and complex selection did not surpass historical U. | Do not rename old feature-diversity or neighborhood protection methods. |
| [RQ4.4](../../../docs/experiment_reports/RQ4_4_Qwen_Analysis_2026-10-12.md) | Completed; additional detailed views increased cost without improving ranking. | No duplicated high-resolution cards. D14 tests a specified evidence/display tradeoff. |
| [RQ4.5](../../../docs/experiment_reports/RQ4_5_Qwen_Analysis_2026-10-19.md) | Completed. Source-exclusive H_MARGINAL 0.4912 is distinct from the repeated-evidence MARGINAL_FIVE. | Reuse its full source handoff and contrast local binding against a key table. |
| [RQ4.6](../../../docs/experiment_reports/RQ4_6_Qwen_Analysis_2026-10-19.md) | Completed. H_MARGINAL_PHASE 0.4590 saved cost but lost ranking, especially on AegisLab; numerical/ownership confusions occurred in actual answers. | Do not simultaneously compress sequences or paired samples in the organization conditions. |
| [RQ4.7](../../../docs/experiment_reports/RQ4_7_Qwen_Analysis_2026-10-20.md) | Retained single-call results are completed. Deleted M-condition data are not recovered or reused. QA interface defects limit old mechanism claims. | Keep QA separate from RCA instructions and independently verify its visible answers. |
| [RQ4.8 completion](../results/../../RQ4_8/results/card_selection_v1/formal/phase_complete.json) and [final analysis](../../RQ4_8/results/card_selection_v1/analysis/formal.json) | All 3,840 formal positions committed. Some findings/index prose remained stale. | Use completed records as authority; do not reinterpret an old running status as an incomplete experiment. |

The exact reused results and costs for U, T_FULL, MARGINAL_FIVE and H_MARGINAL
are verified and indexed by `gates.prepare_historical_references`. No new RCA
generation is scheduled for those four historical comparators. The original
report metrics remain historical; a change to scoring is an offline versioned
analysis, never a reason to generate an answer again.

## What actually changes

| Condition(s) | Nearest predecessor | Distinct intervention / comparison |
|---|---|---|
| U28 | Historical U | A new fixed 4096-square input with at most 28 complete panels. Whole excluded sources are recorded. |
| V_BIND_LOCAL / V_BIND_KEY | U28 | Same source labels near the corresponding observation versus in a numbered card key. |
| V_MARGINAL_DIRECT / MARKLESS | U28 / old marginal controls | Explicit sample/population and endpoint/phase bindings; markless removes only registered point pixels and retains the same token slots. |
| H_MARGINAL_DIRECT / MARKLESS | RQ4.5 H_MARGINAL | Complete paired source exclusively visual; same residual text, numeric annotations and geometry across the point control. |
| H_TPV_BIND / KEY | RQ4.5 topology handoff | Same full public edges and labels; relation labels next to their exact edges versus a numbered key. Labels and neutral pointers are protected support. |
| F_LOCAL_MEAN | U28 | Mean embeddings within spatial groups in the same card. |
| F_SOURCE_MEAN | F_LOCAL_MEAN | Further restrict groups by complete source/signal/unit/statistic/phase support signatures. |
| F_SOURCE_REP | F_SOURCE_MEAN | Same groups and representative positions; keep original representative features. |
| F_SOURCE_SHAM | F_SOURCE_MEAN | Same representative positions and group sizes; fixed permutation of nonrepresentative members. |
| P_SCOPE_E50 | Historical global SCOPE | Actual penultimate vision-attention signal; selection domain is E only, with all A retained separately. |
| P_SHAPE_E50 | U28 | Preserve whole endpoint/turn supports using actual drawn geometry, then fill spatially. |
| P_FULL / P_DOMAIN | Historical full/domain controls | Necessary concurrent controls for U28; all positions versus registered A union E. |
| S_VIS_REDIST / S_EVID_REDIST | VAR-inspired intervention | Same operational sink rule and released fraction, but all nonsink image positions versus A union E as recipients. |
| S_SUPPRESS / S_SHAM_REDIST | The above intervention | Renormalization-only versus mass-matched ordinary-domain-exterior donors. |
| D14_FIXED / D14_PACK | U28 and previous deletion studies | One fixed whole-source subset; unchanged positions versus compact enlarged placement. |

All four sink conditions start with P_FULL, not a background-pruned U28. The
same *eligibility rule* is used in each arm; later-layer activations naturally
diverge, so realized eligible heads and released masses are measured and are
not falsely described as numerically identical across independently evolving
forward passes. A detected high-attention background position is an operational
candidate, not proof of a harmful sink.

## Literature adaptation

- [VisionZip, CVPR 2025, official implementation](https://github.com/JIA-Lab-research/VisionZip): motivates aggregating visual context. Source-compatible grouping, fixed representative positions and mean-versus-representative controls are local adaptations, not a faithful reproduction claim.
- [SCOPE, NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/ec6b4456c2bdfd04002d7984043c4936-Abstract-Conference.html): actual attention saliency plus coverage motivates E-restricted selection. No embedding-norm substitution is used.
- [Visual Attention Sink / VAR, ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/da8a39bc39ae1c89dd6ebb1e3bcbb3f3-Abstract-Conference.html): motivates redistributing image attention. Qwen detection uses registered queries and density, not another model's fixed activation dimensions.
- [Attention Sinks: A Catch, Tag, Release Mechanism for Embeddings, NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/77cd5a17edf97293eab706caf9bfee39-Abstract-Conference.html): motivates the ordinary-background and suppression controls; sinks are not assumed harmful.

## QA and interpretation contract

The [project QA issue record](../../../important_docs/qa_issues_constraints.md)
is the measurement authority together with the approved protocol. The receiver
sees public IDs, types and vocabularies only. It never sees accepted solutions.
Invalid question IDs are filtered individually. Conflicting answers are not
resolved by choosing the one that matches the oracle. Required multiple values
score 0.5 only for a nonempty correct proper subset with no incorrect extra value.

The generator freezes targets before selecting an arm. It distinguishes an
empty oracle (an error), zero (a value), and removed evidence (an availability
loss). The independent CPU auditor recomputes paired population answers and
requires both displayed operands for a phase comparison. Statistic and phase
hash choices are independent. The class distribution and majority-answer
baseline are reported; unavailable controls do not become zero-effect cases.

The five RCA Holm families, 6,000-call accounting, 27-case QA subset, 30-case
repeat subset, smoke windows and source hashes are machine-readable in
`configs/protocol_v1.json` and the frozen manifests. None is selected from
partial results. Public-input median strata are frozen before calls; fewer
than 20 event groups in a stratum permits description only. QA correlations
and quoted explanations do not identify internal causal reasoning.
