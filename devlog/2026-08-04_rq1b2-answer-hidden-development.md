# 2026-08-04 — RQ1b2 answer-hidden compositional development

## Scope and status

Implemented, qualified, and executed the DD-28/RQ1b2 exposed-only Gemma
development cell. The experiment is complete, technically valid, and failed
all three preregistered promotion conditions. DD-29 closes this mechanism;
Qwen development and the locked 150-case independent gate were not opened.

## Implementation and pre-inference qualification

- Reused the existing RQ1 loader, paired T/V/H compiler, vLLM runner, strict
  scorer, asynchronous writer, and accounting path.
- Added answer-hidden temporal onset, directed shortest-path, and exact metric
  lookup tasks. Every arm receives the same raw atomic facts; no derived onset,
  path, winner, label, injection time, or evaluator-only answer is visible.
- Preserved strict image-first `A+B` composition for H.
- Froze 90 new exposed development incidents, 30 per primary dataset, disjoint
  from the old RQ1b mapping/gate rosters. The separate 150-case gate roster was
  locked but not opened for inference.
- Data-only preparation yielded 366 queries: 90 exact controls, 80 paired
  low/high temporal tasks, 86 low topology paths, and 30 AegisLab-only high
  topology paths.
- Manual review found finite robust-z displays near `5e8` when baseline and MAD
  were nearly zero. Before model inference, all T/V/H public normalized facts
  were symmetrically capped at `+/-99.9`. This preserves sign and the frozen
  `|z|>=3` onset predicate. The pre-fix inventory was quarantined and all 90
  cases were regenerated.
- The final inventory passed exact fact parity, answer separation, leakage,
  nonblank rendering, 12-case manual review, and 12 deterministic raw-data
  recompilations. The current provisional RQ1 suite passes 86 tests plus lint
  and compilation.

## Smoke

The qualified Gemma smoke completed 36/36 calls across three partition-aware
cases and all three answer types. Parse rate was 1.000 with zero infrastructure
failures and truncations. Accuracy 0.8056 was diagnostic only.

One earlier launch used `venvs/tools` rather than `venvs/infer` and failed GPU
accounting before receiving a model response. It is preserved under
`invalidated_wrong_interpreter_no_pynvml/` with an invalidation manifest. It
contains no usable model result and is excluded from every experiment count.

## Development execution

- Model: Gemma-4-26B-A4B-it, unquantized BF16.
- Runtime: 32,768 context, 16,384 output ceiling, temperature 0, top-p 1,
  seed 42, thinking off, eager execution, prefix caching and chunked prefill
  off, `gpu_memory_utilization=0.65`.
- Calls: 1,098/1,098, 366 per T/V/H arm.
- Pairing: 90/90 incidents; no context or infrastructure exclusion.
- Parse / infrastructure / truncation: 1.000 / 0 / 0.
- Elapsed model-run wall time: 1,287.7 seconds.
- Raw all-query accuracy: H 0.8251, T 0.8169, V 0.6230. These pooled values
  are descriptive because they combine task families and complexity levels.

## Registered result

The inferential unit is the opaque incident. On the 80 incidents with paired
low/high temporal tasks:

| Quantity | Result | Development requirement |
|---|---:|---:|
| High temporal V−T | −0.3250 | ≥ +0.05 |
| High V / T accuracy | 0.1625 / 0.4875 | descriptive components |
| Paired high-minus-low interaction | 0.0000 | > 0 |
| High visual repairs / breaks | 4 / 30 | repairs > breaks |
| `low→T, high→V` minus best fixed H | −0.1812 | descriptive policy check |

High-complexity V−T was negative in AegisLab (−0.4286), AIOPS-2022
(−0.2800), and AIOPS-2025 (−0.2593). Its descriptive Pratt-Wilcoxon p-value is
`8.24e-6`, with paired Cohen's dz −0.571. Low-complexity V−T was also −0.3250,
which produces the zero interaction.

Controls show a complexity-specific failure rather than total visual
unreadability: exact metric lookup V was 0.9889 versus T/H 1.0000; low topology
V was 0.9884 versus T/H 1.0000; high topology V fell to 0.4333 while T/H stayed
at 1.0000. Temporal H−T was +0.0500 at low complexity but −0.0125 at high
complexity, so adding the image did not rescue the registered hard endpoint.

## Decision and validity

DD-29 marks the RQ1b2 Gemma development cell **valid and failed**. This status
is driven by the frozen mechanism criteria, not runtime failure, early stopping,
or selective model choice. Per the conditional contract:

- do not run Qwen development;
- do not prepare or infer on the 150-case independent gate;
- keep RQ1c, RQ1d, SFT/LoRA/GRPO, reserve, and heldout RCA blocked;
- allow only bounded descriptive analysis on these now-exposed trajectories;
- require a separate preregistration and disjoint development evidence for any
  successor visual mechanism.

## Authoritative artifacts

```text
prepared inventory:
7e3b50973f3181b8d8a59f88d39a80fc93bf74ae41ed0ac59663c4295afeb3f7

runtime tree freeze:
8705cf227cfc0a18ac33a8b3754e281b3d60197d2ac7bc64e6018580acf576e3

run summary SHA256:
4891706c211437193891e0c6c74234bf0ca7e1296d661c17cfbe1bb1084ef463

analysis JSON SHA256:
bab07f7e721af803642a913ddae48fb25aae96c372091659679b67f1ae67a8ee

analysis Markdown SHA256:
7d9f63f82449ef693650d65aa69f814d6ebd494f05e3a26364a2584047dce608
```

## Next step

The bounded, outcome-stratified T/V/H trajectory analysis is complete. In the
80 high-complexity temporal cases, V selected at least one panel without a
valid sustained onset 25 times, returned a singleton 58 times versus 45
singleton gold answers, and selected the top rendered row 30 times versus 15
gold occurrences. H repaired eight T errors but broke nine. Post-hoc bins by
clutter and service count were small and architecture/dataset-concentrated, so
none is promoted as a router.

The descriptive artifact is
`RQs/RQ1/results/rq1b2_compositional_development_v1/analysis/failure_analysis_v1.md`
(SHA256 `6530012a568da3926b3b1c817d83466e925bab83f56bec87a986896ab570e43b`).
It proposes, but does not register, a fact-equal two-stage per-panel onset
ledger plus a causal row-order check. Any implementation requires a new
protocol, decision, disjoint exposed roster, and pre-inference qualification;
DD-28 artifacts and its unopened gate remain unchanged.
