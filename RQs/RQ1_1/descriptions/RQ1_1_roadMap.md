# RQ1.1 qualitative road map

1. Preserve the latest RQ1 audit results and prove the initial RQ1→RQ1.1 copy
   was byte-identical.
2. Remove preparation ambiguity and active Qwen3.6 paths while preserving the
   approved Qwen3.8/Gemma inference recipe; collect image and text attention in
   the original prefill as a non-causal diagnostic.
3. Qualify Denum semantic round-trip, renderer inheritance, seven-arm fact
   equality, the 64-question registry, deterministic tools, persistence, and
   scoring with static/CPU checks.
4. Run exactly one bounded two-model smoke per experiment. Qwen3.8 and Gemma
   execute sequentially and share 18 calls and 600 seconds. Fix a tractable
   hidden issue and repeat only the affected experiment smoke; stop on an
   unresolved material issue.
5. Freeze a versioned protocol only after all three logical smokes pass, their
   raw conversations have been inspected, and every model-visible/tool-returned
   entity is a member of the label-blind exhaustive candidate universe.
6. Run `direct_rca`, then `direct_qa`, then `multi_stage_rca`; within each,
   complete Qwen3.8 before Gemma. Do not choose whether to run a model or arm
   from an earlier result.
7. Interpret outcomes qualitatively: distinguish visual readability,
   representation efficiency, modality-specific effects, and the marginal
   value of tool interaction. A rank change without MRR gain is visual
   influence, not improvement.

Negative, null, or mixed outcomes remain valid; RQ1.1 is not designed to prove
that images help. A redesign is justified by a concrete
failure mode—fact inequality, perception failure, tool misuse, or unstable
scoring—not by the desire for a positive visual result.
