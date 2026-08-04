# RQ1b3 protocol v2: compact no-whitespace onset-ledger transport

**Registration date:** 2026-08-04  
**Authority:** DD-30 plus DD-31  
**Parent protocol:** `rq1b3_two_stage_onset_ledger_protocol_v1.md`

## Scope of the amendment

V1 remains the authoritative scientific protocol. Its first Gemma validation
smoke exposed one interface defect before any development request was sent: a
JSON-schema completion may enter an unbounded grammar-legal whitespace path.
The main Stage-1 cell parsed 9/9, but row sham parsed 5/6 because one response
generated whitespace until the frozen 16,384-token ceiling. V1 is therefore a
preserved failed interface smoke, not an efficacy result.

V2 changes only the structured-output transport. The following remain byte-,
hash-, or contract-identical where applicable:

- the validation, 90-case development, and 150-case gate rosters;
- Canonical Evidence Store facts and T/V/H fact inventories;
- text fragment B, visual fragment A, and strict image-first A+B composition;
- renderer pixels and main/sham row-order algorithms;
- question semantics and the sustained-onset definition;
- two stages, same-arm ledger persistence, oracle diagnostic, metrics, gates,
  statistical tests, and stopping rules;
- checkpoints and every unified vLLM inference setting.

No RQ0, RQ1b, or RQ1b2 status is changed by this amendment.

## Compact Stage-1 transport

Stage 1 still reports all 12 panels in natural numeric order and the same
onset/null/sign information. Its no-whitespace JSON transport is:

```json
{"answer":{"panels":["M1:null","M2:positive@4","M3:negative@7","M4:null","M5:null","M6:null","M7:null","M8:null","M9:null","M10:null","M11:null","M12:null"]}}
```

Each entry is exactly one of:

- `PANEL:null`;
- `PANEL:positive@BIN`;
- `PANEL:negative@BIN`, where `BIN` is 0 through 14.

A task-specific vLLM guided regex fixes the 12 panel IDs and their natural
order and admits no whitespace token. After parsing, the evaluator expands a
nonnull `SIGN@BIN` to the full persisted row
`{panel_id, onset=BIN, support_bins=[BIN,BIN+1], sign=SIGN}`. `null` expands to
null onset, empty support, and null sign. This expansion is deterministic and
adds no empirical or label-derived information; the support pair is a direct
restatement of the frozen two-consecutive-bin onset rule.

Stage-1 scoring compares the expanded ledger to the same private v1
`PanelOnsetLedgerV1` answer. Stage 2 receives only this expanded persisted
same-arm ledger, never the compact model string, original image, or text.

## Compact Stage-2 transport

Stage 2 keeps the same task and output semantics: select the minimum non-null
onset and return every tied panel in lexicographic order, or the frozen
`__NO_VALID_SELECTION__` marker for an invalid/no-onset ledger. A no-whitespace
guided regex constrains the JSON array. Existing evaluator validation and set
scoring remain unchanged.

Every prompt and call contract records:

- `structured_output_transport=vllm_structured_outputs_regex_no_whitespace`;
- the exact guided-regex SHA256;
- null `response_format_sha256`, proving the v1 JSON-schema path was not used.

## Qualification and authorization

V2 must repeat static parity/leakage/answer-separation checks, deterministic
preparation, manual visual attestation, runtime freeze, main and sham Stage 1,
main and sham Stage 2, oracle Stage 2, parse/truncation checks, and full
GPU/token accounting. No development inference is authorized until the entire
v2 validation smoke passes.

After smoke, the v1 statistical contract applies unchanged:

- development n=90: final H−T at least +0.05; incident-macro Stage-1 panel
  accuracy H−T at least +0.05; H repairs exceed breaks; H ledger error below T;
  oracle Stage-2 accuracy at least 0.95; all integrity gates pass; no p-value
  promotion gate because the approximate 80%-power MDE is about 0.106;
- independent gate n=150, only after development passes: final H−T at least
  +0.10 and ledger H−T at least +0.05, each paired two-sided Pratt-Wilcoxon
  p<0.05, 75% mediation consistency, dataset safeguards, parse at least 0.95,
  and no more than 5% paired infrastructure exclusion.

Failure of the v2 smoke permits only an independently justified interface
repair on validation/exposed data. Failure of the v2 Gemma development gate
stops RQ1b3 without Qwen or independent-gate inference.

## Development-roster qualification amendment (DD-33)

The original 90-case development roster failed task-specific qualification
before any development model request: only 77 incidents supported exactly one
12-panel onset-ledger task. The thirteen unsupported incidents are not model
errors and are not silently excluded from an analysis denominator.

The original roster is preserved. A repaired roster retains all 77 supported
incidents and replaces 4 AegisLab, 5 AIOPS-2022, and 4 AIOPS-2025 incidents.
Within each dataset, remaining exposed and development-authorized cases are
ordered by the already registered
`SHA256(42:rq1b3:development:dataset:private_case_id)` key. Every prior RQ1
private-roster incident, every original RQ1b3 development incident, and the
entire unopened RQ1b3 gate are excluded. The frozen v2 data-only compiler is
then applied in order; the first cases yielding exactly one 12-panel task fill
the registered deficits. This predicate reads telemetry structure only: it
does not read a root-cause label, evaluator answer, or model output.

The replacement audit is private where it contains source identifiers and
public where it contains only opaque identifiers/counts. The repaired roster
must contain 30 qualified incidents per dataset and receives a new config,
artifact inventory, qualification, and runtime freeze. All scientific
questions, prompts, arms, statistics, thresholds, and the independent gate
remain unchanged. The completed v2 validation smoke remains valid and
immutable.
