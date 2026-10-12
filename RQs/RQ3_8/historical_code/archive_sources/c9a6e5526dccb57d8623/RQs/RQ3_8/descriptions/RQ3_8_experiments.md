# RQ3.8 experimental contract

Experiment: exp_operational_component_utility. Version: rq38_ops_components_v2.
Complete scientific protocol, duplicate-history audit, statistical families,
roster, failure semantics and resource limits are registered in
docs/experiment_plans/CanvasRCA_RQ3_8_Operational_Components_Plan.md and
RQs/RQ3_8/configs/ops_components_v2.json. Changes require a new registration;
do not silently migrate the user-rejected predecessor layout or its tests.

TEXT/TEXT_DUP, MR00/MR10/MR01/FULL, NO_LOG/NO_ONSET all retain the complete
common public text. Only redundant graphical components are ablated. Empty
slots and stable indices preserve remaining component geometry. FULL is the
preregistered method. RQ480 is repeated-exposed; no untouched-test claim.

One logical two-model smoke is bounded by 18 initiated calls and 600 seconds.
The user additionally caps GPU smoke submissions at three jobs, each with a
30-minute Slurm walltime. This does not reset the logical call/time budget.
CPU qualification is separately capped at eight jobs, each at most one hour.
Formal launch requires static, CPU/browser, processor and smoke checks plus
actual artifact review. Six formal jobs maximum, each one full80GB H100, ≤8h.
Runtime adapter gives dense Gemma31 its true identity and official high-detail
1120 image-token setting; other frozen model fields are inherited explicitly.
Keep history and accounting. No attention, training, API services or Qwen9B use.
