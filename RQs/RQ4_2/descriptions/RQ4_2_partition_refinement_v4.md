# RQ4.2 source partition refinement v4 — CPU only

The user reopens method revision after the v3 scientific gate failure, asking for an algorithmic remedy, with GPU smoke still prohibited. Preserve all v1–v3 outcomes. No gate thresholds, case denominators, facts, PNGs, objective edge weights, or SHAM seeds change.

Observed defect hypothesis: strict single-step cut descent stops after few moves, despite heterogeneous source-unit sizes and a capacity/background constraint that can require coordinated exchanges. Investigate deterministic best-prefix graph refinement in the spirit of Kernighan–Lin: temporarily accept non-improving moves, lock touched units within a pass, then commit only the best strictly improving prefix; discard the tail. Every intermediate state respects exact-fill feasibility and the original 5% background cap. Source cards and 2×2 neighborhoods remain indivisible; four header units stay fixed. No admission metric/foreground mass enters optimization. Stable-ID proposal ordering, at most eight passes and 100 accepted moves/exchanges, no random restart. Both SEM and SHAM use the same algorithm and uniform original edge objective.

Probe uses the same fixed hash 30-case set as v3 (10/dataset), no reselection. If promising, audit all 220 and independently validate final maps, cut values, background movement and deterministic repeat. Reuse v3 geometry and PNG qualification; no rerendering is warranted for an encoder-only change. Remain transparent if another design is required; no positive outcome guaranteed.

Primary reference metadata verified: B. W. Kernighan and S. Lin, An Efficient Heuristic Procedure for Partitioning Graphs, Bell System Technical Journal 49(2), 291–307 (1970), https://doi.org/10.1002/j.1538-7305.1970.tb01770.x. The original paper’s metadata/abstract were verified; its full text was not retrieved. This is a constrained adaptation, not a faithful reproduction or evidence of RCA improvement.


## Literature transfer and limits

Question: can coordinated, capacity-feasible exchanges overcome strict single-step cut minima? Scope: foundational weighted graph partition refinement, not new RCA layouts or learned attention routing. Only primary sources are used.

Sanders and Schulz, *Engineering Multilevel Graph Partitioning Algorithms*, arXiv:1012.0006v3 (2011): [full paper](https://arxiv.org/html/1012.0006v3), especially §§2.2, 4, 6–7. Its local search moves units at most once per pass and rolls back to the best feasible cut. Its graph benchmarks, flow refinement, allowed imbalance and randomized scheduling are different from our exact-size four groups; no reported speed/accuracy gain transfers to RCA. We implement our own deterministic, capacity-checked moves/swaps and best-prefix rollback, not KaFFPa or a complete KL reproduction. No external runtime dependency is introduced. Official NetworkX source retrieval failed; no claim of having audited its implementation or copied it.

## Completed CPU evaluation

Full 220-case audit: SEM57/60,56/60,71/100; SHAM56/60,56/60,90/100. Original thresholds, uniform normalized relation objective, background cap, source closure, images, case population and SHAM seed are unchanged. The optimizer receives neither admission distances nor foreground weights. All 30 fixed probe results exactly match their full-audit recomputation. Two temporarily non-improving step types (zero/negative cut gain) are allowed inside a pass; only strictly improving prefixes survive. This replaces the old restriction that every individual accepted step must improve. At most100 accepted moves/exchanges and8 passes remain hard limits.

The prior header units could in principle participate in a swap with an improving evidence move; the new solver explicitly fixes all four header units. Independent full-population validation confirms their original groups. This is a correctness clarification, not a new diagnostic fact or threshold change.

CPU QA grading is now explicit: q1/q2 require exact numeric equality using Decimal (no tolerance/rounding, numeric JSON or numeric string accepted); q3 requires exact entity digits and equivalent microsecond spellings; q4 requires the exact unique directed relation-type set; q5/q6 exact comparison categories. Invalid answers score zero; N/A stays outside the corresponding question denominator and within cohort applicability reporting. No QA answer is fed to RCA.

Current-version CPU processor checks pass220 cases/558 distinct input forms without resizing: maximum16384 image tokens and16846 total input tokens; +8192 output≤40960. QA59 ready/1inapplicable,350 applicable questions. CPU offline transactions cover all five arm paths, including QA/native4, preserving cold recompile identity and trusted completion resume. Images/renderer are unchanged and inherit compatible220-case binding/geometric checks; three new QA regions and the largest-valued metric region were opened manually.

GPU smoke and formal runs remain unauthorized and unrun. Real checkpoint behavior, latency, attention overhead and MRR are not established by these CPU results. The GPU supervisor/activation remains a subsequent qualification stage; the CPU CLI fails closed for GPU stages.
