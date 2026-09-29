# RQ3.2 static review — 2026-09-20

Status at authoring: **passed; CPU and live smoke pending**.

Checked surfaces:

- four registered experiment matrices and 28,432-call arithmetic;
- 40,000-call hard ceiling and six-call experiment smoke cells;
- complete per-case public pool reconstruction and P0 public split binding;
- separate P0, native-X, aligned-X, and SignalCover code paths;
- P0 backbone, signal/granularity coverage, discrimination, strict-pair and
  equal-capacity ablations;
- G isolated from M/R/L coverage credit;
- same-fact carrier compilation and maximum one PNG per request;
- evaluator-private labels used only for scoring and registered mechanism
  removal, never selection;
- re-anonymization scorer mapping, request-bound call keys, separate ledger,
  atomic outputs, prompts, renders, conversations, costs, and resume markers;
- attention disabled and local-only canonical vLLM launchers;
- syntax, shell syntax, module import, unit tests, source-size limit, and source
  hashes.

The CPU queue must still validate real three-case construction, renderer
determinism, both processors' true token counts, and context capacity. Each live
smoke must validate server/request/persistence behavior; this static review does
not substitute for either gate.

## Successor repair and qualification

The first completed qualification exposed three operational provenance defects:
the prompt envelope named the historical default YAML instead of the runtime
source, visual calls wrote two byte-identical PNG paths, and the queue did not
persist a terminal state or reliably remove its PID file. None changed the
model-visible request or score, but all weakened auditability.

The v2 successor records `runtime_config.source`, makes the shared call
transaction the sole render writer, and uses an EXIT trap to commit terminal
queue state and clean its PID. Focused tests, static registration, three-case
CPU qualification, and all four two-model live smokes passed. Authoritative
evidence is under `RQs/RQ3_2/results/qualification_v2/`.
