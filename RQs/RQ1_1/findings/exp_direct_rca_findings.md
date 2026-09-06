# `direct_rca` findings

Status: **complete**. Both Qwen3.8-27B and Gemma-4-26B-A4B-it completed all
`469 × 18 = 8,442` registered case-arm records under run-contract SHA256
`90225239851410fc6af32d037642bf22c78f557b546e464d5d43498cbe9d9a50`.
There were zero infrastructure errors and zero truncations. Same-call
prefill and answer-token attention was collected for all 16,884 records.

Qwen's text baseline reached MRR 0.4985. Topology-only vision (`TPV`) reached
0.5832 (`Δ=+0.0847`, exploratory all-non-T Holm `p=0.00021`), and visual
logs plus topology (`V_LG`) reached 0.5626 (`Δ=+0.0640`, Holm `p=0.00798`).
The complete dashboard `V` fell to 0.3747. The factorial conditional main
effects were M −0.0826, R −0.0706, L −0.0157, and G +0.0467.

Gemma's text baseline reached MRR 0.5274. No visual arm exceeded it: LV was
0.5215, TPV 0.5124, V_LG 0.5082, and complete V 0.3518. Its conditional main
effects were M −0.0956, R −0.0798, L −0.0093, and G +0.0152. The visual
topology benefit is therefore Qwen-specific in this experiment.

Pixel-text S was below both T and the real dashboard for both models. Full V
reduced mean input tokens by 64.8% for Qwen and 74.1% for Gemma, but the MRR
loss makes it harmful compression. Qwen V_MG reduced tokens by 54.9% while
changing aggregate MRR by only −0.0078, although its dataset-level effects are
heterogeneous.

Attention confirms image access but not correct visual use. In V, answer-token
visual attention mass averaged 7.38% for Qwen and 28.03% for Gemma, even though
Gemma's visual performance was worse. After exact pixel-area normalization,
R/L density exceeded M density and the dashboard header remained a strong
per-pixel attention sink. These are correlational diagnostics, not causal
attributions.

The full reader-facing result, definitions, dataset breakdowns, token costs,
error audit, QA comparison, and attention analysis are in
`docs/RQ1_1_findings.md`. Recomputable tables are under
`tmp/rq1_1_findings_analysis/outputs/`.
