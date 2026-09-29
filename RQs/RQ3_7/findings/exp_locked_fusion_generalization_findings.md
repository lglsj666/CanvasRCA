# exp_locked_fusion_generalization

Status (2026-09-28 resume update): C preparation was interrupted by a nested
WiredTiger absolute log clock. DD-RQ37-4 adds a source-bound relative projection;
eight unit checks and ten real CPU request builds passed, with unchanged
selected packs on the failing case. The queue has been restarted with 250 cold
contexts retained and 410 still to prepare; Qwen→Gemma follows automatically.
No C formal inference had started before this interruption. Details and exact
repair hashes are in `stage_c_clock_repair.json` and the qualification issue.

Original activation: user authorized C; targeted CPU check passed
(50 request builds, 104.72s), C-specific GPU smoke passed (18/18, 260.86s),
saved-input/output/image review passed. The detached C pipeline is running
missing-context CPU preparation, followed automatically by formal Qwen and
Gemma. Formal inference has not yet started at this launch handoff.
Existing test360 is exposed; fresh events remain unavailable without a complete
pre-run exposure audit. No C performance or independent-generalization claim.

2026-09-28 A/B analysis update: all registered expansion recommendation checks
pass after the120-call TPV supplement. Qwen paired macro LL−TPV=.077510,
LL−T_MATCH=.076881; node pairs Qwen24/Gemma25 meet the sample minimum.
This is only exploratory cost control, not significance/noninferiority and not
execution authorization. The analysis session started no models or C targets.
The later user instruction separately authorizes execution; see DD-RQ37-3 and
`docs/issues/RQ3_7_stage_C_qualification.md`. Compatible A terminal records are
aliased to C (1800 units), including failures and corrected TPV supplement
pointers. No A result has been regenerated or rescored.
