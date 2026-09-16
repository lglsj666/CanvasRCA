# Public trace-status evidence — provisional successor

## DD-RQ3-TOURNAMENT-12

Date: 2026-09-13. Status: CPU qualified; adopted for the next small registered
cohort before model calls. Inherits the AC@1-only completion policy v2.

The existing immutable pool explicitly retains TRC-L positive-change operations
with usable baselines, not all source trace observations. Status distributions
are a different signal and can be present in operations outside that filter.
Public-source spot checks found mixed status encodings: AIOPS-2022 has numeric
and textual codes, AIOPS-2025 has gRPC-like 13/14, and AegisLab has textual
Error/Unset/Ok plus a separate HTTP response field. A nonzero integer cannot
universally mean an error. Do not use the source `anomal` column.

Implement a project-owned **observed-status context** intervention, not a full
MicroRCA-Agent reproduction. Read only canonical public trace owner, operation,
timestamp and status_code. Group by owner/operation and retain the full observed
code/count distribution and its relative-bin timeline for each selected row.
Rank groups by counts outside the fixed common-default set (0, OK, Unset and
HTTP 2xx); this is a selection heuristic, not a universal error classifier.
Draw code labels without translating ambiguous integers into error names.
Select at most six groups. Where none qualify, retain the parent R region and
reuse an identical existing request rather than manufacture a new intervention.

Keep parent node-overview M selection, L, G, candidates, prompt bytes and model
recipes. Only this successor's R content/encoding changes. The source observation
window, not private injection times, defines the timeline. Source rows, skipped
rows, selected counts and file hashes remain auditable. Do not modify or rebuild
the old pool. No hidden top-k in the renderer, training or attention.

Acceptance requires CPU tests for mixed/empty statuses, count conservation,
anonymous IDs, ignored private-looking columns, deterministic selection and
actual chart geometry. Review real images before any registered model call.
This version need not improve all datasets; test a small hash-selected unresolved
cohort for each model first, then decide from recorded outcomes.

## Qualification and cohort decision

70 focused CPU tests passed after the font-spacing repair, including count
conservation, private-column
independence, inherited rendering, exact-request reuse and coverage-policy edges.
Three real CPU replays of the parent method preserve PNG, packet, manifest and
prompt bytes. New AIOPS-2022, AIOPS-2025 and AegisLab previews were opened and
checked for complete operation names, status labels, counts and relative axes.
The supplementary-source provenance resolves the canonical processed index:
the safe renderer view intentionally does not expose filesystem paths.
No immutable pool or historical result was modified.

For each model independently, select eight unresolved AIOPS-2022 cases, eight
AIOPS-2025, four AegisLab, four RE2-OB and four RE2-TT. Within each dataset sort
by SHA256 of `[42, "public_status6_v1", opaque_case_id]`, with the same priority
across models. This yields 28 logical targets per model, not a new full-roster
run. Retired cases are ineligible. Record the union gallery and per-model
cohorts before inference; reuse exact historical requests, including incorrect
answers. The larger AIOPS samples prioritize the weakest observed coverage,
without using fault labels to select cases or public evidence. All dataset
outcomes, including unchanged/no-status inputs, remain in the analysis.

Evidence: `results/trace_status_cpu_v1/parent_replay/compatibility_review.json`
and the three adjacent CPU preview folders. These are CPU qualification only,
not evidence that the method improves RCA. Test command and full gallery
audits are retained with the registered round's operational record.

## Sources screened and transfer limits

[MicroRCA-Agent](https://arxiv.org/abs/2509.15635) is a 2025 competition technical
report/preprint. Its [official trace component](https://github.com/tangpan360/MicroRCA-Agent/blob/main/src/utils/trace_utils.py)
combines status checking with a separately trained duration detector. Its fault
windows and post-recovery training data are not transferable to our label-blind
contract. Neither those checkpoints nor its multi-call pipeline are imported.
This inspection motivates testing status evidence, not a claim of replicated
accuracy or an official-component adaptation. Code redistribution permission
was not established, so this successor does not vendor that implementation.

[OpenTelemetry status](https://opentelemetry.io/docs/specs/otel/trace/api/#set-status)
and [gRPC status](https://grpc.io/docs/guides/status-codes/) are distinct protocols.
We preserve source values and avoid interpreting an unspecified code namespace.
