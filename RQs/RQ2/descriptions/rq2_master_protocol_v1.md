# RQ2 master protocol v1: controlled dashboard design effects

**Status:** frozen research structure; implementation and inference locked  
**Registration date:** 2026-08-04  
**Authority:** project roadmap plus DD-34/DD-35

## 1. Research question and boundary

> **RQ2. How do dashboard content, visual encoding, spatial arrangement, and
> their interactions affect RCA accuracy, evidence grounding, robustness, and
> cost?**

RQ2 does not replace or reinterpret RQ0/RQ1. The current dashboard failed to
improve equal-information RCA, and three RQ1 mechanisms failed their registered
gates. RQ2 moves one causal level earlier: it asks whether particular dashboard
design decisions help or hurt. A positive RQ2 design effect is not yet evidence
that a dashboard beats text-only RCA; that claim would require a later frozen
downstream comparison.

The three contribution classes are kept separate:

1. **content contribution:** whether a source/fact family is present;
2. **encoding contribution:** how identical facts are represented;
3. **arrangement contribution:** where identical encoded primitives are placed.

Content comparisons intentionally change the evidence set and therefore cannot
be described as equal-information. Encoding and arrangement comparisons use
identical atomic facts and differ only in the registered treatment.

## 2. Staged design and stopping logic

RQ2 has three sequential studies. A later study is blocked unless every gate of
the earlier study passes.

### RQ2a — encoding and arrangement effects on evidence operations

Use answer-hidden, automatically scored operations to estimate which visual
design choices improve perception and composition. This is the next authorized
study.

### RQ2b — content contribution and interactions

For each telemetry source, compare presence, blank removal, and budget-
reallocated removal after RQ2a freezes the visual encoding and arrangement.
This study is blocked until RQ2a confirms at least one stable design effect.

### RQ2c — downstream RCA transfer

Compare the RQ2-selected dashboard with the pre-RQ2 dashboard under an
identical-summary H design, plus the unchanged T reference. RQ2c is blocked
until RQ2a/RQ2b establish design effects on an independent operation gate.

Failure at RQ2a stops RQ2b/RQ2c and the visual Builder path. Failure at RQ2b
stops content-policy and Builder claims but may still permit an encoding-only
RQ2c if that path was explicitly confirmed in RQ2a. Failure at RQ2c prevents
any claim that the design effect transfers to RCA.

## 3. RQ2a frozen treatment universe

RQ2a uses a full `2^4=16` factorial. Every cell is generated from one canonical
atomic-fact bundle with the same image dimensions, rendering DPI, PNG format,
candidate/task shell, and maximum image count.

| Factor | Level − | Level + | Contribution class |
|---|---|---|---|
| M — metric encoding | annotated binned heatmap | annotated small-multiple lines over the same bins | encoding |
| G — graph encoding | node-link directed graph | edge-time adjacency matrix over the same nodes/edges/onsets | encoding |
| A — cross-source arrangement | modality-blocked regions | entity-aligned metric/log/trace lanes | arrangement |
| O — entity order | stable natural public-ID order | label-blind salience order from frozen public evidence strength | arrangement |

The salience score may use only model-visible atomic telemetry values,
missingness, and topology degree. It may not use root cause, accepted aliases,
fault type, injection time, dataset, private answer, model output, or any
evaluator-only lineage. Its exact formula is frozen before rendering.

All sixteen cells retain the same facts. Each fact receives mappings to every
rendered primitive. The treatment itself—encoding type, position, or order—is
recorded separately from the fact inventory so a layout difference is never
mistaken for added content.

## 4. Answer-hidden operation endpoints

Each incident is compiled into every eligible operation below. No input may
display the derived answer, precomputed winner, precomputed path, onset scalar,
or correct tie set.

1. **Temporal composition:** select the earliest sustained onset and all ties
   from raw normalized bins and missing masks.
2. **Relational composition:** compute a directed shortest path from raw nodes
   and directed edges; no path fact is supplied.
3. **Cross-source alignment:** identify the entity satisfying a registered
   conjunction over metric/log/trace time slices; no mapping-set winner is
   supplied.
4. **Missingness/uncertainty:** select every entity whose registered coverage
   predicate is met from raw masks/counts.

An exact lookup control is included to detect a design that improves complex
tasks by making simple value reading materially worse. Each answer is generated
deterministically from the private compiler and checked against the public
artifact by answer-separation tests.

The primary unit is an incident. Eligible operation scores are averaged within
incident before statistical testing; tasks and panels are not treated as
independent samples.

## 5. Model-visible interface

RQ2a is a visual-design study. The model receives the registered dashboard plus
only the common task shell, question, legend, allowed public IDs, and strict
output schema. It does not receive an incident evidence summary. This avoids
complete text making the visual treatment redundant and is not called an RQ1
image-versus-text comparison.

All cells use one call per operation. Set-valued responses accept any complete,
duplicate-free array of allowed IDs and are canonicalized by natural numeric
order in the evaluator; presentation order is not part of set correctness.
Prompt, output schema, max context/output, sampling, checkpoint, model server,
retry policy, and actual accounting fields are identical across the 16 cells.

The canonical vLLM contract remains unquantized BF16,
`max_model_len=32768`, `max_tokens=16384`, temperature 0, top-p 1, seed 42,
thinking off, eager execution, prefix caching off, chunked prefill off, and
`gpu_memory_utilization=0.65`.

## 6. Data and architecture split

The exposure ledger must be extended for RQ2 without weakening prior
partitions. RQ1's unopened RQ1b2 and RQ1b3 gates remain locked and unavailable.
Reserve, heldout, RE2-TT, and unknown incidents remain unopened.

- **Development screen:** 60 already exposed and already executed RQ1
  incidents, 20 per dataset, selected by
  `SHA256(42:rq2a:development:<dataset>:<private_case_id>)`. Reuse is explicit:
  this cell is exploratory and cannot support a paper claim.
- **Independent operation gate:** 150 previously unused exposed incidents, 50
  per dataset, excluding every prior private roster and locked gate, selected
  by `SHA256(42:rq2a:gate:<dataset>:<private_case_id>)` after label-blind task
  qualification.
- **Future downstream development:** 90 additional disjoint exposed incidents,
  30 per dataset, locked before RQ2a inference and opened only after RQ2a/RQ2b
  authorization.

Gemma-4-26B-A4B-it is the development architecture. If RQ2a development
promotes, the complete independent gate runs both Gemma and Qwen3.6-27B,
regardless of Gemma's gate direction. A cross-architecture statement requires
both models; one-model success is architecture-specific.

Roster qualification may inspect telemetry structure and operation eligibility
only. It may not inspect private answers beyond existence/cardinality checks,
model output, or root labels. Replacement uses the frozen dataset-specific hash
order and is fully audited.

## 7. RQ2a estimands and statistics

For factor `F` and incident `i`, average over every matched context formed by
the other three factors:

```text
main_effect_i(F) = mean(score_i(F+, context) - score_i(F-, context))
```

This is anchor-state relative credit: both actions are evaluated from the same
incident and the same remaining dashboard state. Two-factor interaction is a
paired difference of differences, for example:

```text
interaction_i(M,A)
  = [score_i(M+,A+) - score_i(M-,A+)]
  - [score_i(M+,A-) - score_i(M-,A-)]
```

Report incident-level mean effects, repair/break/tie counts, paired Cohen's dz,
and two-sided Pratt-Wilcoxon p-values. No confidence intervals are reported
under the project rule. Operation family, dataset, visual density, missingness,
candidate count, and model are registered effect modifiers, not outcome-driven
subgroup-selection licenses.

### Development promotion

The 60-case Gemma screen selects at most one direction per factor and promotes
only if all of the following hold:

1. at least one encoding or arrangement main effect is `>= +0.10` on its
   registered target operation family;
2. its repairs exceed breaks;
3. exact-lookup control degradation is greater than `-0.05`;
4. no dataset target-family effect is `<= -0.10`;
5. parse rate is at least 0.95, paired infrastructure exclusion at most 5%, and
   every parity/leakage/render/runtime gate passes.

No development p-value is required. With `n=60`, paired SD 0.36 gives

```text
MDE ~= (1.96 + 0.84) * 0.36 / sqrt(60) = 0.130.
```

The +0.10 signal is therefore a spending screen below confirmatory resolution,
not evidence of efficacy. A factor with less than +0.10 is not promoted by
choosing a favorable subgroup or interaction after seeing outcomes.

### Independent gate

Only the frozen development-selected factor directions are tested. The primary
family contains at most four main effects and uses Holm correction. A design
effect is confirmed for one model only if:

1. target-family effect is at least +0.10;
2. Holm-adjusted paired Pratt-Wilcoxon p is below 0.05;
3. repairs exceed breaks;
4. exact-lookup degradation is greater than -0.05;
5. at least two datasets are positive and none is at or below -0.10;
6. parse rate is at least 0.95, paired infrastructure exclusion at most 5%, and
   every integrity gate passes.

For `n=150`, paired SD 0.36 gives MDE 0.082 and SD 0.50 gives MDE 0.114, placing
the +0.10 practical threshold near the expected resolution. Holm correction
controls the probability of any false positive across the selected factor
family. The -0.05 lookup bound prevents gaining on composition by sacrificing
simple readability at the same magnitude used as the project's smallest
practical effect. The cross-dataset rule prevents a pooled design recommendation
that materially harms one source.

Two-factor interactions are secondary and Holm-corrected within a separate
family. They may explain context dependence but cannot rescue a failed primary
main-effect gate unless a distinct interaction hypothesis was frozen before
development outcomes.

## 8. RQ2b content contribution

Content is evaluated only after RQ2a freezes a qualified encoding/layout. For
each source family—metrics, logs, traces/topology—compare:

1. full dashboard;
2. blank removal, leaving the removed area blank;
3. budget-reallocated removal, deterministically reallocating the area to the
   remaining panels.

This separates the information value of the source from the value of freed
screen budget. Results are labeled unequal-content causal ablations and are
never pooled with equal-fact encoding/arrangement effects. The utility vector
contains evidence accuracy, downstream accuracy when authorized, parse,
tokens, GPU active time, wall time, and harmful override rate.

## 9. RQ2c downstream transfer

RQ2c uses a new frozen roster and the same two architectures. Its mandatory
arms are:

- `T`: complete text evidence;
- `H0`: the pre-RQ2 dashboard plus byte-identical T evidence;
- `H1`: the RQ2-selected dashboard plus the same byte-identical T evidence.

Both hybrid prompts are exact image-first `A+B`; H0/H1 differ only in the
registered dashboard design. The primary RQ2 transfer comparison is H1−H0,
which isolates dashboard design. H1−T is secondary evidence about whether the
redesigned image finally adds value beyond text and cannot be inferred from an
H1−H0 win alone.

RQ2c thresholds and sample size must be separately preregistered after RQ2a/b;
they may not be chosen from RQ2a/b downstream outcomes.

## 10. Qualification and implementation lock

Before any RQ2 request:

- freeze an RQ2 exposure ledger and private/public rosters;
- freeze atomic facts, private answers, all 16 renderer configs, the salience
  formula, task shell, response schemas, model checkpoints, and analysis code;
- prove exact fact equality across all encoding/arrangement cells;
- prove no label, raw ID, dataset, fault type, absolute/injection time, source
  path, or evaluator lineage is visible in pixels, OCR text, prompt, or metadata;
- verify deterministic rendering and exact image dimensions/PNG ordering;
- manually review at least four cases per dataset covering sparse/dense,
  missing-source, long-label, isolated-node, and high-clutter conditions;
- run partition-aware smoke, oracle-answer interface checks, context preflight,
  accounting checks, and runtime freeze;
- keep `RQs/RQ2/src/` untouched until RQ2 is complete and final submission code
  is approved.

This protocol authorizes static implementation and qualification only. RQ2a
model inference requires a separate design decision after every pre-inference
artifact and gate is frozen.
