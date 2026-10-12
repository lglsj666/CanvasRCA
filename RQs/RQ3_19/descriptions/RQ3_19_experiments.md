# RQ3.19 — Visual replacement and diagnostic QA

Authority: the user on 2026-10-05 authorizes implementation, static checks,
complete CPU regression, visual review, GPU smoke, then direct formal launch.
The assistant stops after verifying startup. No subsequent research stage is
automatically selected from partial outcomes.

Scientific plan: [dual-track plan](../../../docs/experiment_plans/CanvasRCA_Dual_Track_Next_Stage_2026-10-05.md).
This is the prospective executable registration of its core: 220 exposed eval
cases (60/60/100), four main arms, two independent repeats on the fixed public
60-case subset, and eight QA/readout-intervention calls on the same subset.
Total 1,480 positions, at most 1,566 formal attempts including the reserved86;
18 shared smoke attempts within600 seconds. The whole next-stage ceiling is
3,000, including conditional allocations which remain separate and inactive.

FULL_TEXT is the exact RQ3.18 READOUT_TEXT request text. COMPACT_TEXT replaces
repeated JSON object keys with losslessly decodable named-column tables.
ADD_VISUAL adds the fixed population image. REPLACE_VISUAL transfers only
explicit fields visibly recoverable from the same image. Existing formatted
quantiles are transferred only when their displayed number equals the precise
source numeric value; all other exact values stay in text. Parent/child,
operation names and population counts also transfer from the main pair body,
not merely the duplicated readout appendix. I1/I2 denote panel order in the
shared decoding grammar. Unique facts, candidate order, all phases and M/R/L/G
remain complete. Historical PNGs are reused only after proving compatibility
with the latest src/renderer source and bundle; three current renders must be
byte-identical. No experiment-local drawing code is present.

The60 QA/repeat cases are selected by frozen hash,20 per dataset, prioritizing
different public event groups. Public eligibility requires a pair and a calls
edge; no outcomes or private labels select cases. Six questions cover count,
unit/type, endpoint binding, relation direction and two numerical comparisons.
Q0/Q1 use a separate typed QA schema; RB/RP preserve the RCA schema and contain
identical correct public statements, respectively question order and source
order. No QA model response becomes RCA evidence. Statement ordering is a
controlled presentation intervention, not pure perceptual mediation.

QA scoring normalizes outer whitespace/case for the unit and duration type;
ms, millisecond and milliseconds are equivalent. Seconds and exclusive
duration remain wrong. Numeric answers, entity/operation identity, direction
and comparison values retain their exact registered semantics. This rule is
fixed before any model output is observed.

Method primary family: V-F and V-C; QA family: Q1-Q0 for C/V and RCA RB-RP for
C/V. Each family uses two-sided Pratt-zero Wilcoxon,12-decimal differences,
Holm separately for case/event-group units and paired dz; no CI. Main adoption
requires deltas .03/.02 with both adjusted families passing, per-dataset MRR
and AC5 protection, repeat direction and total cost ratios<=1.05 against F/C.
V-A is a mechanism comparison, not a required component-wise adoption gate.
All model-invalid responses retain zero; infrastructure remains unknown with
original-denominator bounds. QA and RCA denominators are kept distinct.

Main and QA requests are interleaved by frozen hash; repeats follow the first
calls. Ordinary identical fallback requests may reference a contemporary
commit. Repeats always use independent call keys. Atomic completed markers are
trusted at resume; only pending cases are loaded. Stop signals drain active
calls, and the owned service closes at completion/pause. No submitted wrong
ranking is retried. Formal results cannot trigger conditional modules.

Runtime: canonical local Qwen3.8-27B BF16; existing decoding/template recipe,
40960 context,8192 request output adapter, memory utilization .75,36 concurrent
requests. Same registered Triton prefill operational adapter as RQ3.18. CPU
preparation has at most8 workers on different physical cores. No training.

Attention collection is now permitted by Codex.md. The separate lightweight
instrumentation has not passed its compatibility/storage qualification and is
not silently enabled in the core. Its116-call allocation remains unspent.
SIRCL220 and frozen extension1080 likewise require their registered gates;
test360 remains exposed. These are explicit pending conditional modules,
not passed qualification or core queue omissions.
