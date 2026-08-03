# RQ1 implementation status — 2026-08-03

## Implemented in the provisional scripts tree

- six-directory RQ layout, with `src/`, `results/`, and `findings/` empty;
- public `AtomicFactV1` and `QuerySpecV1`, separated from private
  `PrivateAnswerKeyV1`;
- a CEBv1 compatibility adapter plus execution-grade
  `CanonicalEvidenceStoreV2WithDenseLogAndTraceTimeSlices`, with complete
  relative-time log, trace-service, and trace-edge bins;
- explicit caller-to-callee edge facts and explicit derived multi-hop path
  facts;
- deterministic VisOps task construction for exact lookup, temporal summary,
  topology/path, cross-modal availability, and missingness;
- paired text/visual artifact compilers with independently reconstructed
  fact inventories and complete `fact_id -> location` maps;
- image-first prompt fragment `A`, text fragment `B`, and byte/part-exact
  hybrid `A+B`;
- `EvidenceLedgerV2` schema and semantic validator;
- leakage, fact-tampering, parity, schema, deterministic-render, and execution
  interlock tests;
- a data-only artifact preparer and a contract-aware, resumable launcher with
  asynchronous atomic writes; the launcher is deliberately locked and its
  three arms have been dry-run without model calls;
- a deterministic private-answer parser/scorer for numeric, set, directed-edge,
  and ordered-path VisOps answers;
- a strict paired analyzer that enforces complete T/V/H units, whole-incident
  infrastructure exclusion with the registered 5% ceiling, parse-rate
  qualification, model-failure retention, repair/break/net effects, Wilcoxon
  Pratt tests, Cohen's dz, and token/time accounting without confidence
  intervals.
- fail-closed exposure-ledger and roster tooling that accepts only an explicit,
  project-history-complete V2 ledger, preserves dataset/leakage-group metadata
  privately, and emits a public roster containing only renderer-compatible
  opaque incident IDs.

## Reused shared code

Only safe lower-level components are reused: processed case loading,
`CaseRenderView`, deterministic renderer/preset code, CEBv1 construction, the
unified vLLM client/config (for a later enabled runner), and project scoring
utilities where applicable. The legacy `vlmrca.vlm.prompt.build_prompt`, legacy
generic one-shot runner, and RQ0 nonredundant-allocation prompt are explicitly
forbidden in the RQ1 script tree because they cannot prove current information
parity.

## Deliberately blocked before inference

The checked-in roster is empty and unfrozen, and `execution.enabled` is false.
Before any model call, RQ1 still needs:

1. exposure-ledger reconciliation and an exposed-only roster;
2. operation eligibility and power analysis;
3. version/hash freeze and representative qualification of the implemented
   dense V2 evidence-store compiler;
4. renderer/view perception qualification on the frozen exposed roster;
5. frozen prompt/artifact hashes, paired arm scheduling, and GPU active-time
   accounting for the implemented runner;
6. a partition-aware three-case vLLM smoke.

## Static qualification completed

- lint, bytecode compilation, JSON-schema checks, and the RQ1-local unit suite
  pass;
- synthetic evidence covers all five operation families and nine operations;
- read-only integration checks pass on one case from each of AegisLab,
  AIOPS-2022, AIOPS-2025, and RE2-OB;
- those checks build dense V2 stores with relative log timelines,
  trace-service timelines, trace edge-time matrices, and complete directed
  graph/path facts without labels or absolute clocks;
- text, visual, and strict `A+B` dry-runs pass for the registered Gemma model;
  the Qwen architecture-control configuration also resolves successfully;
- the legacy 488-row RQ0 exposure ledger is correctly rejected: it is not a
  complete project-history ledger and omits the later 720-case formal run;
- no vLLM request, long-running inference, training, result, or finding was
  produced.

No result or finding is established by this implementation milestone.
