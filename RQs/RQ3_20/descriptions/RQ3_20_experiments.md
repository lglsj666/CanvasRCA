# RQ3.20 — Budgeted visual evidence acquisition

The authoritative user-approved protocol is
[the saved plan](../../../docs/experiment_plans/RQ3_20_Budgeted_Visual_Evidence_Acquisition_Plan_2026-10-05.md).
The independent implementation starts with a complete 220-case CPU feasibility gate.
It does not inherit a predecessor's GPU qualification. A failed dataset applicability
gate ends this candidate before the downstream runtime is implemented or activated.

Five principal workflows: FULL_TEXT, SUMMARY_TEXT, SUMMARY_VISUAL, TEXT_FETCH,
VISUAL_FETCH. The last is preselected. The user-authorized v3 budgets are 0.50 of full-text input
for the first request, 0.85 for both inputs plus 512 selector output, at least
50% applicable cases in each dataset, context 40960, final output cap 8192.
All unavailable or over-budget cases use the common full-text fallback and remain
in the denominator. No case is replaced based on a model answer or private root.

The 3,000-attempt allocation is recorded in configs/budgeted_acquisition_v3.json.
It is an upper bound, not an instruction to spend unused calls. Attention, SIRCL,
and isolated confirmation each require their own applicable qualification evidence.
Only the shared 18-attempt/600-second smoke may qualify this experiment.

Implementation refinements fixed without model calls:

- The input source is the exact RQ3.19 FULL_TEXT public projection and pair packet,
  not a newly selected corpus or previous answers. All original text parts remain
  byte-identical in the complete ledger.
- Metric values/missing codecs, AUX vectors and request-pair sample points are
  deferred as complete source-bound bundles. Existing scalar summaries are retained;
  no extra anomaly score is computed. The first/last/extrema textual summaries remain.
- Relationship edges are the union of the public G block, selected-observation
  relationship records, the additional component ledger and recorded request-parent
  pairs. The old component-only helper is insufficient for this whole-text source.
  Stable typed edge direction and all supporting operation facts are retained.
- `owns` is the existing renderer's `has_instance` display alias, with explicit
  decoding. There is no new component or operation. Only the upper call graph uses
  the previously registered 3x dashed stroke/arrow scale.
- CPU uses the installed inference Python **with CUDA disabled**, because the tools
  Python lacks PyTorch needed by the actual local processor. This does not launch
  vLLM, load model weights, change the environment or authorize inference.

Status and exact executed scope are maintained only in
../findings/exp_budgeted_acquisition_findings.md. Failed qualifications are not RCA results.

## DD-RQ320-CPU-STOP: Apply the registered early stop

**Date:** 2026-10-05
**Status:** adopted

**Context.** The method requires both text and visual acquisition to fit the same
budget and at least half of each dataset to qualify before GPU work.

**Decision.** Stop the candidate after the complete 220-case necessary text screen.
Do not develop or launch downstream model stages under this failed qualification.

**Evidence.** Eligibility upper bounds are 0/60, 0/60 and 16/100. All 220 full-input
counts match the prior baseline inventory, and 12 direct processor checks agree.
The findings and independent feasibility audit bind the exact source contract.
There are no new rankings, p-values or observed inference-cost measurements.

**Alternatives rejected.** Loosening budgets, dropping entity summaries, shrinking
fonts, selecting only easy cases, or continuing GPU under the failed gate would
change the approved protocol. Rendering every graph cannot repair a failed common
text first-input requirement and is not needed to decide this gate.

**Consequences.** Preserve the CPU implementation and failure evidence. Revisit only
under a separately decided method/protocol; the negative result is scoped to this
compiler and contract, not to every form of visual evidence acquisition.

The prospective v3 execution amendment is `execution_revision_v3.md`. Original
40% failures remain failed historical qualifications, not retrospectively passed.
