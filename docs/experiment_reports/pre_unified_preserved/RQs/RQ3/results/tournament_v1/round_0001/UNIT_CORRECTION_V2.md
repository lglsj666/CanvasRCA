# 2026-09-13 — Aegis trace units: superseding the initial preflight assumption

The initial PREFLIGHT_REPAIR.md assumption that Aegis duration_ms contained
actual milliseconds was incorrect. That conclusion came from its variable
name and processor comments, not a verified source-unit contract. This note
explicitly supersedes that part; RE2 remains actual milliseconds.

The official AegisLab data-format documentation specifies duration in
nanoseconds:
https://operationspai.github.io/AegisLab-doc/algorithm-developers/development-guide/data-formats/

All 100 frozen Aegis processed trace tables were checked against their retained
raw duration column, row for row. Every duration_ms column is exactly raw
duration/1000, i.e. microseconds, not milliseconds. The independent audit is
aegis_trace_unit_audit_v2.json. RQ3's display projector now divides this stored
quantity by a further 1000. No processed file or pool is rewritten. No unit is
inferred from the fault label, outcome, or apparent model correctness.

The correction is limited to the three displayed trace duration fields;
selection, counts, dimensionless fold scores, candidates and task/guide remain
unchanged. The 22 projection/display CPU tests pass. AIOPS behavior remains
unchanged; RE2 retains its already-correct millisecond projection.

The queue was stopped safely before Gemma started. Qwen has 73 completed Aegis
responses and three interrupted requests. Preserve all input/output/partial and
call records here, but these pre-correction Aegis attempts are superseded for
the new tournament's success/retirement calculation. No round/model success
commit had occurred, so no case was mistakenly retired. Do not retrofit these
outputs to the corrected inputs.

The corrected execution root is ../round_0001_unitfix_v2, attached to the same
registered first method/cohort. Only the 100 Aegis visual inputs are rebuilt;
the other 380 existing CPU artifacts are retained byte-for-byte. The original
gallery stays here. New model records use fresh request manifests and outputs.
Both models must complete the corrected 480-case round before it is committed.

This source-unit bug was found during a real conversation review of an
implausibly large absolute latency. It is not a low-MRR retry, prompt tuning,
or evidence of the model hallucinating that printed value. Historical RQ1.1,
RQ2.1 and previous exploration files remain untouched and are not re-scored or
silently reclassified by this repair.
