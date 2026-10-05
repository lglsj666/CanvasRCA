# Protected compression findings

2026-10-01: protected_compression_v2 formal queue finished; final offline artifact/score/statistical review and detailed report complete. The frozen HIGH candidate is not recommended for deployment. Exposed development evidence only.

Formal: 1120 positions terminal, 1108 with results (17 exact-input references), 12 request timeouts retained unknown. 1103 independent requests initiated, 1091 completed; 18 separate smoke calls. Two duplicate-ID model outputs retain zero scores. All completed outputs stopped normally; no truncations or unexplained omissions. Owned GPU service exited at 16:12 Toronto, formal wall 4548.56s.

Primary AIOPS: PV_HIGH−EXACT_TEXT ΔMRR +.004861, n120, Holm p1; total tokens +3.103%. PV_HIGH−PT_HIGH −.000700, n119, p1, tokens +5.704%; PV_HIGH−COARSE_HIGH −.018091, n117, p.6091, tokens +3.774%. LOW−HIGH +.029412, n119, raw p.0414 but Holm .1656 and event-group .3893. No registered primary/secondary contrast significant. HIGH remains the a priori candidate; no post-result winner substitution.

Known-side timeout bounds on full120 AIOPS mean deltas: HIGH visual−encoded text [-.009028,-.000694], HIGH protected−coarse [-.030139,-.005139]. These are deterministic missing-outcome ranges, not confidence intervals or population tests. Numeric signatures match for3360 budget-series; patches11824 LOW/8297 HIGH. Numerical preservation did not establish RCA or explanation gains.

Final audit:1091 unique calls,1108 result positions,140 public-only compiler reconstructions,280 PNGs,85 archived files,20 checkpoint SHA256 entries plus8 tokenizer/processor metadata/blob identities; original scores reproduced unchanged. Added reporting-only main/gates code has separate provenance. Read24 paired review entries/12 cases and4 full PNGs; remaining67 review entries not adjudicated. Unit, chronology, instance binding and attribution faults persist, including correct-ranked answers with faulty reasons.

Detailed report: [RQ3_11_Qwen_Analysis_2026-10-01.md](../../../docs/experiment_reports/RQ3_11_Qwen_Analysis_2026-10-01.md). Reviewed tables, verification, statistics check, manual review and standalone PNG/SVG: results/protected_v2/analysis_reviewed_v1/. No new model request, timeout retry, test, training or successor method launched during this analysis.

Historical qualification and submission below remain preserved.

CPU140cases in62.93s,max18914+8192<40960,zeroexclusions.280unchanged realPNG/DOM outputs reused and hash/source audited; actual visual review and deterministic repeat passed.18GPUsmoke completions in170.24s inclstartup,final core verifier270.88s<600; all persisted prompts,images,outputs,streams/conversations and originalscores reviewed. Unit/origin/chronology reasoning errors retained as model diagnostics.

v1 zeroGPUcalls; public CPU cost prompted preGPU removal of redundant overrides.37,906→20,121 exact patches while finite signatures remain exact. This is not minimum repair or full semantic/causal preservation. Preset image/input costs remain to be measured with formal output utility; do not claim savings from qualification.

Durable receipt: results/protected_v2/formal/submission.json. Full handoff: results/protected_v2/logs/2026-10-01_formal_submission.md. Frozen archive8cd66de375ff4f2cede5474d95bd8aedb6acf8cfac20d2fb9d27993d4f77fb7b. Resume explicit local.sh supervise --execute only if interrupted. Agent stops after confirmed first92atomic completions; no automatic next experiment. Allcases exposed eval; no independent test/Gemma/training/attention.
