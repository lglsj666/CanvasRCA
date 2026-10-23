# RQ4.9 — organization_v1

## Final scientific analysis — 2026-10-22

The complete [analysis report](../../../docs/experiment_reports/RQ4_9_Qwen_Analysis_2026-10-22.md)
now covers all 5,850 formal positions, the latest `论文主线.md`, 23-arm standard
and tolerant metrics, costs, 22 registered comparisons, QA, attention and actual
answer review. New analysis material is separate from the immutable finalized
result tree. No model calls or Nibi operations were made for analysis.

Best new pure visual: P_DOMAIN MRR **0.353106**, U28 **0.348864**;
best hybrid: H_MARGINAL_DIRECT **0.440530**. Historical U/T_FULL/MARGINAL_FIVE/
H_MARGINAL remain **0.351742/0.484621/0.505379/0.491212**. No registered RCA
contrast passes its Holm family. DOMAIN−FULL is a positive development signal
(case-weighted ΔMRR +0.042803, event-group p=.044601, pH=.178405); further E50
does not add an observed MRR improvement. Protected A accounts for 93.27% of
U28 retained image positions; source means actually average non-singleton groups
at about 4.34% of retained image positions. None of the new candidates satisfies
the registered joint ranking/cost/per-dataset progression targets.

All four sink arms genuinely intervene in all 220 cases; eligible head-query
fraction is about 43.3%, released mass about 0.67% per eligible distribution.
MRR remains .3112–.3152 with no specific advantage over ordinary-background
donors. Measurements cover only registered prompt/decode-start queries and are
before the native gate, not final ranking-token attribution.

QA audit confirms a measurement limitation: 25/27 question batches reveal the
numeric-readout answer in a different question; unit majority guessing reaches
25/27. All oracles remain nonempty and visible, but numeric QA cannot be treated
as uncontaminated visual reading. The 25 synthetic label swaps also make shown
parent-current p50 exceed p95, mixing display reading with statistical priors.
These affect independent QA interpretation, not RCA labels or rankings. Original
answers and registered scores are preserved. The new qualitative review examines
9 cases / 25 responses, with explicit fixed-hash versus post-hoc selection and
source-text/geometry coverage; no additional dashboard image was opened.

The earlier `analysis/qa_rca_review.json` inside the finalized result tree still
retains its historical not-reviewed status. Use the report's separate
`qualitative_review.json` for the actual completed review; do not overwrite or
misrepresent the historical file. The offline report builder independently
reproduces all 44 event/case statistical records. RQ-specific analysis logging
uses `results/report_analysis_v1/logs/`, preserving the finalized `organization_v1`
manifest and its storage closeout receipt.

## Final storage status

Current status: **local formal execution complete; storage closeout passed,
2026-10-22**. The authoritative phase marker commits all 5,850 formal positions
(5,060 RCA, 700 QA/controls, 90 independent RCA repeats), with no missing formal
positions. Across formal and qualification scopes, 5,975 conversation records
represent 5,908 actual completed calls and 67 exact-result references. The ledger
also preserves two infrastructure-failed qualification attempts.

Storage decreased from 28.824 decimal GB to 6.847 GB, releasing 21.977 GB.
This is 11.589 GB per 10,000 actual completed calls, below the 25 GB limit.
All collected attention, including conservatively charged mapping fields,
definitions and indexes, occupies at most 0.711 GB per 10,000 calls, below 1 GB.
There are no compressed archives. Runtime caches, duplicated prepared requests,
unused HTML/images and an unused profiler were removed only after dependency
verification. Original committed records, exact prompts, actual PNGs, raw answers,
scores and frozen execution sources remain unchanged. Nibi was not contacted.

The complete conversation graph is `committed record -> shared exact request ->
shared model-visible PNGs`. The [browser instructions](../results/organization_v1/README.md)
provide direct access without exporting another copy of every input/output.
Unique evidence/provenance, private scoring contexts, actual operator mappings,
source geometry, costs/failures and all collected attention remain readable.

Four isolated storage regressions and six required-data corruption counterexamples
passed. All 5,850 formal records were rescored offline: numerical scores and RCA
statuses match, and all 92 arm/dataset aggregate groups reproduce. The 39 differing
diagnostic error strings only reorder printed JSON-schema keys; original strings
are preserved. No model calls, renderer runs or scientific qualification reruns
were performed for cleanup. Generation-code identity is unchanged; storage-code
changes are archived separately from the original qualified execution sources.

See [final storage receipt](../results/organization_v1/finalization.json),
[file hashes](../results/organization_v1/retained_manifest.json),
[attention accounting](../results/organization_v1/audits/attention_retention_accounting.json)
and [rescoring verification](../results/organization_v1/audits/storage_rescore_check.json).
Quantitative analyses are available under `analysis/`; the QA/RCA qualitative
review still reports its actual review status. Storage completion is not a
claim that the final scientific report or manual case review has been written.

## Historical execution and qualification notes

Status: **formal local execution resumed by the user, 2026-10-22**.
Resumed from3355/5850 atomic committed positions without revalidating the full
input/image graph or repeating committed model failures. Local runner PID3947
passed220.0seconds startup observation: 3369/5850 committed,
8request capacity, bounded prepared-input queue, no new infrastructure errors.
The last length-terminated answer retains its exact hash and was not retried.
Nibi was not contacted or changed by this local resumption.

The frozen source/queue/runtime are unchanged:
`d13710530260198118475fc6d127b16d8575636d2b165b889f8bf7717e3929d9`.
Original CPU/visual/runtime and qualified acceleration smoke retain their
version-bound receipts. Scientific results remain incomplete; final retention
qualification is pending. Handoff: `logs/resume_review_2026-10-22.json`.

The protocol has 23 single-call RCA conditions on 220 exposed development
incidents (60 AIOPS-2022, 60 AIOPS-2025, 100 AegisLab). Hybrid is explicitly
authorized for this study. Historical U, T_FULL, MARGINAL_FIVE and H_MARGINAL
answers/costs are reused. Codex.md and historical experiment sources were not
changed by this implementation.

The maximum is 6,000 actual calls. The complete prepared queue has 5,850 formal
positions: 5,060 RCA, 621 QA, 79 QA controls and 90 genuine independent repeats.
The two unavailable statistic-label swaps remain N/A. Exact computation
references reduce actual calls; they do not increase the call denominator.

Original-runtime validation completed:

- Static: five functional modules, 3,366 source lines, TypeScript and registration,
  private/public boundaries, historical-source protection and closed defaults.
- CPU: all 220 cases and 23 conditions, real processor budgets, sources, candidates,
  4096-square/28-card limits, operators and matching point-removal controls.
- QA: all 27 fixed cases answerable; all 23 representations; independent oracle
  checks and 16 numerical/interface/commit regressions. Unit-conflict and comparative
  prose counterexamples are included. Historical QA was rescored offline under a
  separate version; original answers/scores are unchanged.
- Runtime: 85 real CPU processor/MRoPE probes plus independent operator checks;
  actual GPU tensors and native operator paths passed their bounded smoke.
- Visual: exactly six images opened, including one superseded collision example.
  Automatic audits cover the cohort; the sampled review does not establish universal
  readability. The densest topology remains crowded.
- Operator smoke: 12 committed positions, 14 attempts including two preserved
  infrastructure failures; 852.15 seconds including repairs/restarts, below 900.
- QA smoke: 11 committed positions in 339.01 seconds; all original answers reviewed.
  A question-heading extraction error was fixed and rescored offline, preserving old
  scores and all raw responses. No diagnostic/model calls were repeated.
- Organization/hybrid smoke: 12 committed positions in 169.09 seconds; all actual
  input hashes, operator receipts, output accounting and requested attention passed.

The detailed repair history is in
[qualification](../descriptions/RQ4_9_qualification.md). Repairs did not use smoke
MRR to choose or tune methods. Source-compatible checks were retained only with
explicit AST, input or arithmetic proofs; affected checks were rerun.

Attention covers layers 3/23/43/63, last prompt and first decode queries, with
mass/count/density and actual sink-operation audits. It does not cover the final
ranking-token reasoning process. Eight registered measurements were present in
each reviewed successful smoke call; recorded summaries remain below 64 KiB.

Authoritative artifacts and controls:

- [Qualification receipts](../results/organization_v1/qualification/)
- [Operator review](../results/organization_v1/smoke_operators/review.json)
- [Organization review](../results/organization_v1/smoke_organization/review.json)
- [Frozen queues and source snapshots](../results/organization_v1/frozen/)
- [Call ledger](../results/organization_v1/calls.sqlite)

All launches require a matching frozen source fingerprint. Formal resume trusts
atomic per-call completion markers. Eight physical-core CPU workers prepare a
bounded RAM queue; eight GPU requests use local BF16 Qwen/vLLM at 0.8 VRAM.
Exact prompts, pixels, raw responses, parsing, scores, costs and collected attention
remain directly readable and deduplicated. Finalization checks references/hashes
and the 25 GB/10,000-call and 1 GB attention budgets after writers drain.


Formal launch: 25 positions reference qualified, exactly identical smoke requests.
The remaining queue needs at most 5,783 new generations before infrastructure
recovery, including 90 true repeats. The shared call ledger already contains
37 qualification attempts (35 responses and two infrastructure failures).
Ordinary exact-request reuse never selects by score. Logical deployment costs
retain the original full usage; references add no research-call denominator.
Copied attention mappings use verified hardlinks, with source scope recorded.

Monitor with `RQs/RQ4_9/scripts/run.sh status`, or read
`results/organization_v1/formal/progress.json` and `formal/run.log`.
The launch fingerprint is
`70ddb721ab1811334da5c152e4371e7ad9a30aca0a18451e40af7ea8861ba0e7`.
Final statistical/qualitative conclusions require the completed batch; the
runner automatically performs aggregate analysis and retention checks on drain.

Startup observation passed after 191.2 seconds: 35/5,850 committed (10 new formal calls, 25 exact references), GPU concurrency 8, no infrastructure errors. Some model-generated illegal candidates are scored zero and retained under the protocol. Latest live progress supersedes this snapshot.
