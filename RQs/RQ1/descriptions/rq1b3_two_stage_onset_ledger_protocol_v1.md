# RQ1b3 protocol v1: fact-equal two-stage temporal evidence ledger

## Status and relationship to prior results

This is a separately registered, exposed-only RQ1b mechanism study. It does
not change the completed RQ0/RQ1a result, the failed RQ1b router gate, or the
valid-but-failed RQ1b2 development cell. It does not authorize RQ1c, RQ1d,
training, reserve, or heldout RCA.

RQ1b2 established that the current images are readable for exact lookup, but
direct image-only temporal composition is vulnerable to singleton-spike
salience, row-position bias, and tied-answer under-selection. H repaired eight
T errors and broke nine on high-complexity tasks, so simply repeating the same
one-step prompt is not justified. RQ1b3 changes the reasoning interface rather
than the facts: the model must first externalize a complete per-panel onset
ledger, then make the final selection from that ledger.

## Research question and hypotheses

> Under identical raw temporal evidence and matched two-call budgets, does an
> image added to byte-identical text improve a VLM's complete evidence ledger
> and final answer relative to text-only, and are visual outputs robust to a
> style-preserving row-order sham?

Three mandatory arms remain:

- `T`: complete raw 12×16 normalized-series facts in deterministic text;
- `V`: the visual encoding of exactly the same facts;
- `H`: exact image-first prompt composition `A_visual + B_text`, where B is
  byte-identical to T's evidence fragment.

Primary hypotheses on the independent gate:

1. `P1 — final visual increment`: H final exact-set accuracy exceeds T by at
   least `+0.10`, with paired two-sided Pratt-Wilcoxon `p < 0.05`;
2. `P2 — ledger improvement`: H incident-macro panel-onset accuracy exceeds T
   by at least `+0.05`, with paired two-sided Pratt-Wilcoxon `p < 0.05`;
3. `P3 — evidence mediation`: among T/H-discordant final answers, the arm with
   the correct final answer has a strictly lower per-panel ledger error in at
   least 75% of non-tied discordant cases, and H final repairs outnumber H
   final breaks.

V final/ledger results and H−V/V−T are mandatory secondary comparisons. V is
not required to beat T: the project claim is the incremental value of adding
the image to unchanged text, not that image-only should replace complete text.

## Data partitions

Only incidents marked `rq1_exposed_development` in the authoritative project-
history-complete exposure ledger are eligible.

- Exclude every case in the old RQ1b mapping, independent gate, and smoke
  rosters.
- Exclude every RQ1b2 development case.
- Exclude all 150 incidents in the locked RQ1b2 gate roster; that roster stays
  unopened and cannot be repurposed.
- Exclude RE2, heldout, reserve, unused, unknown, and training-only cases.
- Development: 90 new incidents, 30 per primary dataset, fixed by
  `SHA256("42:rq1b3:development:<dataset>:<private_case_id>")`.
- Independent gate: 150 additional disjoint incidents, 50 per dataset, fixed
  by `SHA256("42:rq1b3:gate:<dataset>:<private_case_id>")` after excluding the
  development roster.

Read-only roster feasibility before registration found 571 eligible incidents
after all exclusions: 178 AegisLab, 200 AIOPS-2022, and 193 AIOPS-2025. Roster
freezing may inspect only ledger metadata, never model outcomes.

## Evidence and task contract

Each eligible task uses 12 label-blind metric series and the same deterministic
16 robust-z bins as RQ1b2, including explicit missing masks and the symmetric
`+/-99.9` display cap. The cap preserves sign and the frozen onset predicate.

The common onset rule is:

```text
the first of two consecutive observed bins where |z| >= 3.0
and both values have the same sign; otherwise null
```

No arm may see a precomputed onset, winner, tie set, root cause, accepted alias,
fault type, injection/absolute time, dataset name, raw case ID, source path, or
evaluator lineage. The evaluator-private answer contains:

- each panel's exact onset or `null`;
- the minimum valid onset;
- the complete lexicographically sorted set of panels tied at that onset.

Every fact has one `fact_id` and one per-arm location mapping. Ignoring
duplicate encoding inside H, T/V/H fact inventories must be exactly equal.

## Two fixed stages

### Stage 1 — Observe and compose

Each arm makes exactly one call and returns `PanelOnsetLedgerV1`:

```json
{
  "answer": {
    "panels": [
      {
        "panel_id": "M1",
        "onset": null,
        "support_bins": [],
        "sign": null
      }
    ]
  }
}
```

The ledger must contain every supplied panel exactly once in natural numeric
panel order (for example M1–M12 or P01–P12, preserving the task's prefix).
For a valid onset, `support_bins` must equal `[onset, onset+1]` and `sign` must
be `positive` or `negative`. For `null`, support bins are empty and sign is
null. Unknown, duplicate, missing, or non-panel entries fail parsing. This
complete ledger directly measures false sustained onsets, missed onsets,
off-by-one errors, sign errors, and panel omissions rather than hiding them
inside one final set.

### Stage 2 — Select from the frozen ledger

Each arm makes one more call. It receives only:

- that arm's persisted Stage-1 ledger;
- the common rule for selecting the minimum non-null onset and all ties;
- the common strict output schema.

It does not reread the image, text evidence, private answer, or another arm's
ledger. It returns:

```json
{"answer": ["M7"]}
```

If Stage 1 fails parsing or ledger validation, Stage 2 still receives its one
matched call. Its only evidence is a deterministic invalid-ledger marker with
the Stage-1 response hash and failure class; it receives neither another arm's
ledger nor reconstructed raw evidence. The registered no-evidence response is
`["__NO_VALID_SELECTION__"]`, which cannot score as a correct panel answer.
This keeps the two-call budget equal while retaining Stage-1 failure as a model
outcome.

An oracle-ledger diagnostic supplies the evaluator-derived correct ledger to
the same Stage-2 prompt. Oracle Stage-2 exact accuracy must be at least 0.95;
otherwise the selector interface is not qualified and efficacy inference is
blocked. Oracle calls are common diagnostics, not an experimental arm.

## Renderer and position-sham contract

The main renderer uses numeric panel order `M1, M2, ..., M12`, not lexical
`M1, M10, ...`. It displays all 16 annotated cells, missingness, threshold
legend, the complete two-consecutive/same-sign rule, and stable panel IDs. It
does not outline or otherwise mark the derived winning onset.

Before model inference it must pass parity, leakage, answer separation,
nonblank/OCR, missingness, rule-text, numeric-order, and deterministic-render
checks plus 12-case manual review.

The registered style-preserving sham uses the identical values, IDs, labels,
resolution, PNG encoding, and question, but permutes complete panel rows by
`SHA256("42:rq1b3:row-sham:<opaque_incident_id>:<panel_id>")`. It is run for V
and H during development after the main calls, with the same two stages. The
sham changes arrangement only and must not be interpreted as new evidence.

Report main-versus-sham Stage-1 ledger agreement, final answer agreement,
accuracy change, top-row selection frequency, and panel-position error slope.
This is a causal test of positional sensitivity, not a visual-benefit endpoint.
It is not used to select whichever order gives higher accuracy. The independent
gate uses the numeric main order frozen before development outcomes.

## Metrics and analysis

Primary inferential unit is the opaque incident. Query/panel rows are not
treated as independent incidents.

- Stage-1 incident score: fraction of 12 panels with exact onset/null; supporting
  bins and sign are integrity components and separately reported.
- Stage-1 exact-ledger rate: all 12 panel entries correct.
- Stage-1 false-onset, missed-onset, off-by-one, sign, omission, and duplicate
  rates.
- Stage-2 final exact-set accuracy.
- H-over-T final repairs, breaks, ties, and net correction.
- Ledger mediation: normalized absolute onset error with false/missed onset
  penalty 16, averaged within incident; lower is better.
- Parse, truncation, infrastructure, tokens, wall time, GPU active time, and
  peak memory.

No confidence intervals are reported under the project rule. Confirmatory
paired tests use two-sided Wilcoxon signed-rank with Pratt zero handling and
report paired Cohen's dz.

## Development promotion gate

Gemma alone runs the 90-case exposed development cell. It promotes the
independent gate only if every condition passes:

1. H−T final exact accuracy is at least `+0.05`;
2. H−T Stage-1 incident-macro panel accuracy is at least `+0.05`;
3. H final repairs exceed breaks;
4. mean H ledger error is lower than mean T ledger error;
5. oracle-ledger Stage-2 exact accuracy is at least 0.95;
6. T/V/H and sham cells meet integrity gates.

There is no development p-value threshold. With `n=90` and paired SD 0.36,
the approximate 80%-power MDE is `(1.96+0.84)*0.36/sqrt(90)=0.106`; a `+0.05`
screen is intentionally below confirmatory resolution. It only justifies
spending independent evidence and cannot support an efficacy claim.

Failure of any condition stops RQ1b3 without Qwen or independent-gate
inference. Development outcomes may not be used to choose a row order, change
the onset rule, drop a dataset, or weaken a threshold.

## Independent-gate decision

If development passes, the complete 150-case gate runs for Gemma and Qwen under
the same frozen numeric renderer, two-stage prompts, schemas, checkpoints, and
analysis. Both models run regardless of Gemma's intermediate gate outcome.

Gemma passes only if P1–P3 all pass, at least two datasets have positive H−T
final effects, no dataset is at or below `−0.10`, oracle Stage-2 accuracy is at
least 0.95, every arm/stage parse rate is at least 0.95, whole-incident paired
infrastructure exclusion is at most 5%, and all parity, leakage, determinism,
truncation, context, and accounting gates pass.

At `n=150`, paired SD 0.36 gives MDE 0.082 and conservative SD 0.50 gives 0.114.
The `+0.10` final threshold is therefore close to the design's resolvable and
practically meaningful scale. The Stage-1 `+0.05` threshold is smaller because
it averages 12 panel decisions within each incident, but it still requires the
incident-level paired p-value below 0.05.

Only Gemma passing supports a Gemma-specific mechanism. Both architectures
passing supports replication across the tested VLMs. Passing RQ1b3 authorizes
design of the next RQ1 matched-plan stage; it is not heldout RCA evidence.

## Runtime contract

- Gemma-4-26B-A4B-it primary; Qwen3.6-27B only after development promotion;
- unquantized BF16, one GPU, canonical project checkpoints;
- `max_model_len=32768`, `max_tokens=16384`, temperature 0, top-p 1, seed 42,
  thinking off, prefix caching off, chunked prefill off, eager execution;
- `gpu_memory_utilization=0.65` operational ceiling;
- same Stage-1 and Stage-2 context/output opportunity across T/V/H, without
  padding or a claim of identical realized FLOPs;
- balanced T/V/H order by opaque incident hash and balanced main/sham order;
- live-tokenizer preflight, partition-aware smoke, resumable atomic writer, and
  complete token/GPU accounting.

No model call is authorized until the new rosters, compiler, renderer, schemas,
analysis, static qualification, smoke contract, and runtime tree are frozen.
