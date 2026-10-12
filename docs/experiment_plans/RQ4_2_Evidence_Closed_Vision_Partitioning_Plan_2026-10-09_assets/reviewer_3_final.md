<!-- Verbatim final message retrieved from /root/rq42_blind_3. Earlier messages are not included. -->

**This is a worthwhile change of research question, but it is not ready for a full run.** With the latest correction, I prefer it to another generic JOIN/layout experiment. My scores, on a 10-point scale, are **design 7/10, novelty 5/10, execution readiness 3/10**. These assess the proposed study, not an anticipated positive result.

I read all four requested report texts, including their tables and appendices. I did not inspect previous reviews, audit underlying trajectories, edit files, or run inference.

The history supports this change, within limits:

- [RQ4.1](/home/lglsj/CanvasRCA_nibi/docs/experiment_reports/RQ4_1_Qwen_Analysis_2026-10-09.md) establishes failure of the particular post-encoder compression candidate: CVC MRR 0.3332 versus T_FULL 0.4846; CVC/rewired masks had Jaccard 0.9861. It does **not** establish that global vision attention caused the failure. The new intervention tests that possibility more directly.
- [RQ3.21](/home/lglsj/CanvasRCA_nibi/docs/experiment_reports/RQ3_21_Qwen_Analysis_2026-10-06.md) shows that reversible compilation can damage stage comparison and ranking. The proposed complete local graphics address a documented risk, but their readability still needs qualification.
- [RQ3.7](/home/lglsj/CanvasRCA_nibi/docs/experiment_reports/RQ3_7_Results_Analysis_2026-09-28.md) supports keeping local bindings: the complete LOCAL_LINK package helped, while proximity/link component attribution remained unresolved. Repeating another proximity-versus-links matrix would offer limited new information.
- [RQ1.1/RQ2.1](/home/lglsj/CanvasRCA_nibi/docs/experiment_reports/RQ1_1_RQ2_1_findings/findings.md) already covers representation, encoding, spatial organization, resolution, and weak QA–RCA correspondence. Another broad packing or resolution sweep is unnecessary.

**The revised five-arm design is coherent.**

| Arm | Distinct question |
|---|---|
| C_FULL | What does the new readable compiler achieve under the unchanged full encoder? |
| C_GEOM | Does restricting early/middle vision attention help without navigation-informed grouping? |
| C_SEM | Does source navigation improve grouping beyond that geometric restriction? |
| C_SHAM | Does correctness of those navigation joins matter? |
| P_NATIVE | Does ordinary four-image input provide an adequate simpler alternative? |

The equal-quadrant master image, exact \(N/4\) group sizes, common hard bundles, and final four global blocks fix my principal objections to the earlier formulation. Collapsing P_GEOM/P_SEM into P_NATIVE is sensible. Native paging remains a system comparator: it changes positions, image boundaries, and its global-attention behavior. It is not a pure causal control for attention partitioning.

Keep C_SHAM only if its **actual foreground co-membership** differs substantially after optimization. Rewiring graph edges alone is insufficient. If the control fails admission, cancel it before inference and relinquish the claim that correct joins specifically explain any improvement. Do not replace it with several increasingly favorable rewiring variants.

The novelty needs careful positioning. Semantic grouping for attention, balanced groups, scattering outputs back to original positions, and local/global fusion already exist. Particularly relevant primary sources are [Dynamic Group Transformer](https://arxiv.org/html/2203.03937v1), [Semantic-Aware Local-Global ViT](https://arxiv.org/html/2211.14705v1), [Semantic Equitable Clustering](https://arxiv.org/html/2405.13337v3), and [Qwen2.5-VL’s window/full-attention architecture](https://arxiv.org/html/2502.13923v1). I read their method sections and relevant architecture/experimental descriptions beyond abstracts.

The defensible contribution is narrower: **training-free, provenance-defined grouping of complete diagnostic graphics inside a frozen encoder, preserving its original positions and tokens, with later global fusion**. These precedents generally involve trained architectures or different token transformations; they do not establish that this frozen intervention will work. Conversely, they preclude presenting semantic attention partitioning itself as a new principle.

I would require the following fixes before registration and execution:

1. **Specify the intervention precisely.** Freeze the actual block indices, permutation/inverse-permutation locations, positional tensors, merger ordering, dtype, and attention backend. Confirm that the model has the assumed depth and computational path. K=1 identity is necessary but insufficient: also qualify equivalence to an explicit block-diagonal reference on small synthetic tensors, preservation of every original 2×2 merger neighborhood, and invariance to group-label renaming. These are implementation checks, not additional RCA arms.

2. **Make the pixel and background contract auditable.** Background must come from renderer provenance, never a brightness heuristic that could classify thin strokes or small labels as empty. Preserve all patch-aligned card rectangles, global annotations, candidate inventory, and their multiplicities. Record processed dimensions and patch counts from the actual processor. Exact equal groups do not prove equal foreground load; report foreground/background and modality composition by group.

3. **Define what “closed” means.** Shared hard bundles already give GEOM and SEM the same local source closure. Therefore SEM−GEOM measures **additional navigation-informed contextualization**, not the benefit of placing quantity, identity, phase, and unit together. Ensure any explicit reference/current comparison remains interpretable within its retained graphics; “same phase” bundling alone does not guarantee this. Every routing edge must be traceable to the frozen diagnostic fact inventory. Public metadata is not automatically permission to introduce additional relationships.

4. **Freeze a complete partition specification and admission denominator.** Normalization order, edge aggregation, initialization, tie-breaking, move/swap order, stopping rule, failed packing, zero-cut baselines, and oversized bundles need deterministic definitions. Define the 20% co-membership difference mathematically, independently of group IDs; distinguish card-weighted and foreground-patch-weighted versions. Report admission by dataset and event group. At only 50% admission, the deployable method is materially a conditional partition/full-attention policy, and its mechanism sample may be small.

5. **Keep the common fallback genuinely common.** Generate one C_FULL answer for each nonqualifying case and reference it in all applicable arms; do not spend four or five identical calls. Those cases remain in full-denominator utility and cost accounting. Show an admitted-case mechanism analysis alongside the full policy result, without presenting the selected subset as the deployment population. CPU admission is acceptable; outcome-driven admission is not.

6. **Repair the QA experiment before it consumes its allocation.** The isolated task and field-level validator are necessary corrections to RQ4.1. Qualification should establish that targets are unambiguous, all required fields are represented, equivalent units are handled, and no unrelated RCA instruction survives. Include questions whose needed evidence is grouped differently between SEM and GEOM, selected using public sources before answers exist. Otherwise six easy within-card questions could miss the mechanism. Retain field-level and joint scores; do not treat QA gains or attention changes as causal mediation of RCA.

7. **Align statistical claims with the contrasts.** The three current primary comparisons assess partition utility and the simpler alternative. They do not test correctness of navigation joins; register SEM−SHAM in a corrected mechanism family if that claim matters. Pratt-zero Wilcoxon on event-group means and \(d_z\) are acceptable under the stated rules, provided the signed-rank interpretation is kept distinct from the case-weighted +0.02 engineering endpoint. No confidence intervals are needed. A nonsignificant component contrast should limit attribution, not erase a genuine complete-pipeline improvement.

For cost, exact \(N/4\) groups plus four final global blocks yields a clear attention-operation model: the quadratic portion scales approximately as
\[
\big((L-4)/4+4\big)/L
\]
relative to full attention, before overhead. That is **not** the ratio for the whole encoder or whole diagnosis. Patch embedding, projections, MLPs, merger, decoder, rendering, and grouping still run. Require synchronized component timings and full cold-path measurement for the current arms. Reusing historical text performance is appropriate; missing historical cold-path measurements should remain a limitation, not trigger ceremonial text reruns.

The +0.02 target over reused T_FULL is ambitious: it requires reaching roughly 0.505 from a historical pure-visual best near 0.352. Nothing reviewed makes that recovery likely enough to assume. C_FULL is essential because improved rendering could account for most of any gain. Such a result would still be useful pipeline progress, but would not validate semantic partitioning.

I recommend **one later frozen new-case stage**, provided an exposure audit identifies a defensible cohort. Prioritize it over more development arms or a second model. Compare the frozen nominated method with the strongest predeclared simpler visual comparator and strong text; reuse compatible existing answers, and register genuinely new text requests only where needed. Do not automatically run the stage because budget remains, and do not repeat it until a threshold passes. A second model is unnecessary unless cross-model applicability becomes an explicit claim.

The revised core can answer a new and useful question with approximately five main arms. The remaining work is to prove that the intended intervention is feasible and controlled—not to expand toward the 8,000-call ceiling.
