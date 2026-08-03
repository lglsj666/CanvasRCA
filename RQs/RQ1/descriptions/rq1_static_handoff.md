# RQ1 static implementation handoff

This handoff describes the provisional implementation under
`RQs/RQ1/scripts/`. It is not an experiment registration and does not unlock
the frozen `src/` tree.

## What can be run now

The following commands perform no model calls:

```bash
PYTHONPATH=RQs:RQs/RQ1/scripts \
  venvs/tools/bin/ruff check RQs/RQ1/scripts

PYTHONPATH=RQs:RQs/RQ1/scripts \
  venvs/tools/bin/python -m pytest -q RQs/RQ1/scripts/tests

PYTHONPATH=RQs:RQs/RQ1/scripts \
  venvs/tools/bin/python RQs/RQ1/scripts/static_check.py
```

An already exposed or validation-only case may be compiled in a temporary
directory for read-only renderer qualification:

```bash
PYTHONPATH=RQs:RQs/RQ1/scripts \
  venvs/tools/bin/python RQs/RQ1/scripts/prepare_rq1_visops.py \
  --real-case DATASET CASE_ID \
  --output /tmp/rq1-qualification-artifacts
```

The preparer writes public tasks, text views, visual PNGs, primitive maps,
prompt contracts, and paired-view audits under `public/`. Automatically derived
answers are written under a physically separate `private/` tree. These are
qualification artifacts, not experiment results.

The runner supports a no-request contract dry-run for each arm:

```bash
for arm in T V H; do
  PYTHONPATH=RQs:RQs/RQ1/scripts \
    venvs/tools/bin/python RQs/RQ1/scripts/run_rq1_visops.py \
    --prepared-root /tmp/rq1-qualification-artifacts \
    --model gemma-4-26b-a4b \
    --arm "$arm" \
    --dry-run
done
```

Here `T` is the text fragment `B`, `V` is the visual fragment `A`, and `H` is
the exact ordered part sequence `A+B`. The common task shell is identical.

## Why execution is locked

The checked-in configuration and roster deliberately fail closed. An actual
model request requires all of the following rather than a local command-line
override:

1. a frozen, exposed-only roster with an assignment hash and exposure-ledger
   lineage;
2. a frozen and representative qualification of the implemented dense V2
   evidence store containing relative-time log events and trace edge-time
   facts;
3. frozen renderer, prompt, parser, scoring, arm-order, exclusion, and runtime
   contracts;
4. a server attestation matching the registered BF16, unquantized vLLM
   configuration;
5. GPU active-time accounting and a partition-aware smoke qualification.

The CEBv1 adapter remains compatibility-only. The default preparer now combines
its qualified metric facts with dense, label-blind log, trace-service, and
trace-edge time slices to produce the required V2 store. The runner records and
checks that store schema; configuration, roster, qualification, and smoke gates
remain independently binding.

## Result analysis contract

`analyze_rq1_visops.py` accepts only complete paired `T/V/H` call sets. A
single infrastructure failure excludes the entire opaque incident for that
model; exclusion above 5% fails the analysis. Parse failures, truncations, and
invalid model outputs remain model outcomes. It reports per-arm and per-family
accuracy and query-level repair/break/net effects. Inferential comparisons first
aggregate within each opaque incident, then use paired Wilcoxon tests with Pratt
zeros and paired Cohen's dz. Token/time accounting is reported, confidence
intervals are not, and any saved analysis must be placed under
`RQs/RQ1/results/`.

Per-dataset and AIOPS-2022 leakage-group descriptions are joined only during
offline evaluation through `--private-roster`. The analyzer verifies the
roster assignment hash and copies only `analysis_dataset` and
`analysis_leakage_group_id`; raw case IDs are rejected from calls and never
enter its report.

## Frozen boundaries

- Do not import the legacy modality prompt compiler or generic one-shot runner.
- Do not expose raw case IDs, dataset names, fault types, labels, injection or
  absolute timestamps, or filesystem paths to a model-visible artifact.
- Do not derive task eligibility, distractors, panel selection, or routing from
  root labels.
- Do not write provisional code into `RQs/RQ1/src/`.
- Do not treat static artifacts, dry-runs, or renderer checks as RQ1 findings.
