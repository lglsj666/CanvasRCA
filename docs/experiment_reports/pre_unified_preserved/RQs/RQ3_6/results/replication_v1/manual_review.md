# 2026-09-26 — Stage A qualification review

Status: passed for stage A qualification only. Source contract `5d77be32458c919e32d61225f40fa32e4b5fddb3b5cbd2c2dfc2d1adda2b7e39`. Formal calls: zero. No subsequent stage is opened.

## Coverage and persistence

Three real discovery cases: AIOPS-2022 `INC-0986D6C54EC6`, AIOPS-2025 `INC-B8CEA35848D0`, AegisLab `INC-6A048DD0C35E`. They are existing screen cases, not test or unused cases.

CPU: six unit regressions plus all 11 arms × three cases × two models = 66 compiled requests. Final run 9.914 seconds; workers pinned to cores 0, 2, 4. Individual case times 8.30 / 7.64 / 7.97 seconds. Maximum preflight input 18,333 tokens, below the registered context minus 8,192 output allowance. No source dataset or heavy preparation regenerated.

GPU: 18 initiated calls, nine per model, all 18 complete; total original-window elapsed 558.820 seconds. Models ran sequentially. Three smoke arms are E_S_G_P_V_S, E_S_G_S_V_P and W_NO_K. Remaining eight arms are CPU-qualified inherited paths, not claimed to have new live calls. This is one logical smoke, not two independent windows. Historical accounting 8,241; new solver calls 18; cumulative total 8,259. No retry/extra sample.

All eighteen outputs, prompt structures, model-visible parts, literal-audit sidecars and conversation completeness inspected. Automated review reads and validates each conversation, raw response, persisted input, cost and completion record. Every GPU input identity matches its CPU-compiled counterpart. Two crossed prompts differ only in their registered instruction block. Candidate lists, S evidence, task and answer contract match. No unknown candidate or parse/truncation failure was recorded in these eighteen outputs. No attention artifacts were generated.

Three actual W_NO_K PNGs were visually inspected; the same image bytes are used by both models. Numeric labels and directed edge ledger remain readable; G-only masked parent canvas and concrete call edges are retained. No R latency chart is embedded, so the source-attested Trace unit-label correction affects text only. No unregistered crop, resize or renderer intervention was made.

## Repaired implementation faults

1. Static inspection corrected a wrong deferred import location for the inherited text serializer.
2. First CPU run exposed an incompatible projection hash serializer. Replaced the local digest with the unified stable_hash required by bind_task_request. Failed attempt log retained; zero model calls.
3. GPU requests completed, but post-response literal auditing accessed a missing `projection.image_hashes`. Added this provenance field and added the actual response_audit adapter to every CPU request regression. Nine Qwen responses were recovered offline: saved requests compared exactly to current compilation, original prompt/output/score/completion retained, only missing audit and terminal markers committed. Initial failure report and source/CPU snapshots remain under `repairs/`. New CPU regression passed before Gemma ran. The original start/deadline and aggregate 18-call cap were retained, including debugging time; no Qwen regeneration.

Source-unit correction is separately registered as `parent_trace_unit_labels_v1`: preserve historical stored Trace numbers and scores, label them microseconds instead of milliseconds. Do not confuse that with the projection-hash or missing-provenance operational fixes. All older RQs remain unchanged.

## Model behavior, not harness defects

- Several answers call five-digit pod IDs “service” or call a pod a node despite the explicit type contract. Example: Qwen describes 93361 as service; Gemma describes 81384 as node. Existing literal audit correctly refutes these types; original ranks are not edited.
- Some answers conflate operation names and graph entities or infer causality from entry-point position. Qwen's AIOPS-2025 E_S_G_P_V_S answer explicitly says the entry point must be the root. This is evidence for the intended instruction study, not permission to retune the smoke prompt.
- Image-grounding mistakes remain: Qwen's AegisLab W_NO_K explanation assigns the earliest G onset to 807 although the displayed earliest ID is 716; Gemma's AIOPS-2025 W_NO_K explanation calls pod51547 the earliest G event although that ID is not in the displayed G rows. Inputs were checked; these are answer claims, not altered source rows.
- Native S serialization is outside much of the inherited literal number/relation parser's grammar: it compiles zero quantities/relations on these S conditions while still checking numeric-ID types. The sidecar explicitly records unknown coverage. This is not “zero hallucinations” and must not be used for cross-format hallucination-rate comparisons. Main ranking scorer is independent and unchanged.

Qualification checks execution and artifacts, not whether the model answers correctly. No MRR promotion or design choice is made from three cases.

## Stop state

Owned Qwen/Gemma servers and workers exited after qualification. No formal_authorization.json was created. No formal experiment, B–D, training or attention job is running. Next action requires the user's decision to open the formal A check120 run.
