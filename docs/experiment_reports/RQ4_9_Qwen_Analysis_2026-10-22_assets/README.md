# RQ4.9 final report assets

These are offline derived tables, figures, review annotations and reproducible
report code, separate from the immutable `organization_v1` experiment snapshot.
They contain no new model generations and no duplicate full conversation exports.
Case tables retain canonical request/record references; raw text, exact prompts,
images and attention remain in the finalized experiment's readable object graph.

- `snapshot.json`: aggregate data and original phase/storage provenance.
- `statistics.csv`: all 44 registered event-group/case statistical records.
- `details.json`: explicitly descriptive operator, runtime and cost sensitivities.
- `qa_target_hint_audit.csv`: confirmed cross-question numeric hints.
- `qualitative_review.json`: actual review of 9 cases / 25 raw responses.
- `verification.json`: delivery integrity, source compatibility and total storage.
- `build_report.py`: render report and six statistical figures from these data.

The source of fault annotations is identified by hash in snapshot.json; those
annotations are already retained per case in these tables. The analysis tables
are private evaluator outputs and must never be added to diagnostic model inputs.
No CIs are reported. Post-hoc analyses do not replace registered comparison families.

Reproduce using the commands in the report. Five functional experiment modules
remain below the 7,500-line limit; report generation does not run qualification,
renderer/browser, model inference or network calls.
