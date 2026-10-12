# Candidate-once repair review — 2026-09-26

Qualification passed, not efficacy evidence. User approved up to six additional
calls and one 600-second window. Six calls completed in 216.813 seconds; both
models ran sequentially. No timeout, infrastructure error, invalid JSON or
unknown candidate ID. All six raw finish reasons are `stop`.

All six responses were read and conversations checked against every input text
part and the raw output. Exact old/new request comparisons confirm deletion
of the redundant candidate record only. Candidate paragraph, all other facts,
system, output schema and inference configuration remain identical. No image
is included in this text-only arm. CPU qualification covered 120 requests and
15 tests. Source contract:
`589aff1996c5915343471413e3a2f83af5aeaa9cccfae0a21023ad4709bf3b1e`.

The current A qualification combines these six repaired references with twelve
unchanged originals. Original report hash remains
`73abf4de44189c72b223391112ab3445970cd01b4aebc1603e99783d4ae61e02`.
Original artifacts and the 18 spent calls remain. Current A cumulative spend
24; current major-RQ spend 6,939. No formal authorization or queue was created.

Model caveats: both models misname pod 81384 as a service in the first case's
reason. Qwen cites 30 seconds for the AegisLab operation whose visible inherited
value is 30,006,458.63 ms; Gemma's 30,000-second conversion is consistent with
that displayed value. The repair did not change or independently validate those
underlying source-duration conventions. Inferred causality is not established
by this qualification. Partial literal audits are not complete reasoning
verification. These outcomes are retained without score edits or resampling.

Optional backend initialization/JIT warnings did not cause failed requests.
Owned model services and runners exited and GPU compute residency was cleared.
Detailed record: `docs/issues/RQ3_5_qualification_2026-09-25.md`.
