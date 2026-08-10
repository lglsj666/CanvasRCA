# 2026-08-09 — Nibi deployment and RQ1 execution

## Status

Execution in progress. No Nibi model call had been made when this log was
opened.

## Completed preparation

- Read and reconciled the root guidance, RQ1 protocol, findings, and Nibi
  launch contracts.
- Built split base/inference environments using Nibi modules and the Alliance
  wheelhouse; verified the exact registered inference versions and imports.
- Staged both registered model revisions with byte inventories and SHA-256
  manifests.
- Converted the five read-only source datasets to the public/private per-case
  schema and validated all 469 frozen eligible cases and 1,407 relative-time
  parquet ranges.
- Reconciled canonical salted opaque IDs without changing the frozen roster.
- Fixed installed-wheel project-root discovery and added a pre-inference
  runtime-freeze equality check.
- Advanced the renderer to v16 after visual audits caught and removed natural
  entity aliases from propagation, metrics, logs, traces, and graph
  projections.
- Passed the RQ1 CPU static suite with zero model calls.

## Validity notes

The first four CPU-only smoke preparation roots used renderer-v13 through v16
while resolving display leakage. They are preserved as diagnostic artifacts
and are not inference inputs. The authoritative smoke is prepared only after
the execution config and source freeze. RE2-TT content and outcomes remain
uninspected before its registered final execution.

## Next action

Prepare the frozen smoke root, submit both 30-minute H100 smoke jobs, inspect
all artifacts, then CPU-pre-render the 469-case roster and submit all twelve
experiment/model arrays. Infrastructure defects are repaired and resumed;
efficacy threshold misses are recorded without stopping later experiments.

## Launch record

- Definitive smoke CPU preparation: job `19390717`, completed successfully;
  experiment root `rq1_nibi_smoke_v6__shard-0000-of-0001`, three cases,
  runtime freeze `872acb2a42cf84f363b5a9828c6c9b8a1b10e288f7b7ed64d730f29a9170f77a`.
- Qwen smoke: job `19390776`, 30 minutes, one H100.
- Gemma smoke: job `19390777`, 30 minutes, one H100.
- Final 469-case CPU preparation: array job `19390786`, eight shards.
- Full three-day H100 arrays (eight shards, at most four simultaneous tasks per
  array):

  | Experiment | Qwen | Gemma |
  |---|---:|---:|
  | `legacy_q9` | `19390980` | `19390981` |
  | `cross_region` | `19390982` | `19390983` |
  | `typed_two_stage` | `19390984` | `19390985` |
  | `matched_rca` | `19390986` | `19390987` |
  | `visual_counterfactual_rca` | `19390988` | `19390990` |
  | `ledger_handoff_rca` | `19390991` | `19390992` |

All full arrays carry `afterok` dependencies on the entire CPU-preparation
array and both infrastructure smoke jobs. Threshold values are not scheduler
dependencies and cannot stop the sequence.

## First launch failure and supersession

Smoke jobs `19390776` and `19390777` failed during server initialization before
any model call. Qwen's Triton helper and Gemma's FlashInfer backend attempted to
write under the quota-limited home cache. The exact fix exports Triton,
TorchInductor, CUDA, vLLM, and FlashInfer cache roots under
`CANVASRCA_CACHE_ROOT`; it does not change a model or inference parameter.

The first final CPU preparation array `19390786` independently exposed an
over-broad privacy assertion: raw fault labels such as `disk` and `socket` were
treated as forbidden substrings even when those words occurred naturally in
label-blind metric names. The renderer never receives labels and the existing
forbidden-key audit rejects an explicit `fault_type` field. The value-substring
check therefore continues for case IDs, dataset names, root causes, absolute
times, paths, and all natural entity aliases, but no longer treats a generic
fault-type word as proof of leakage.

The partial preparation and failed smoke roots are diagnostic only. Pending
full arrays `19390980`–`19390988` and `19390990`–`19390992` were cancelled
before allocation because their old runtime freeze could not be valid after
these fixes. They are superseded by the next launch record; cancelled Slurm
allocations themselves cannot be resumed, while their partial generated files
remain recoverable in the result roots.

Replacement smokes `19391289` and `19391290` then reached model loading with
the compiler caches correctly under scratch, but vLLM's optional usage-reporter
thread attempted a separate home-config write. Both were cancelled with zero
trajectory files/model calls. Final CPU preparation `19391206` was cancelled
because the deployment freeze was expanded at the same time to include shared
and RQ shell launchers, dependency requirement files, and packaging metadata.
The next launch disables vLLM usage reporting, records a sorted installed-
environment hash and termination code, and binds the newly covered deployment
files into the prepared runtime freeze.

## Authoritative replacement launch

- Smoke preparation v8: `19391480`, completed and verified; freeze
  `14818229a189af1f5544cf7ea10d1761fe01ab09ec4a179eb30a0a66a633602e`.
- Qwen/Gemma smoke jobs: `19391513` and `19391514`.
- Final 469-case preparation v3: `19391481`.
- Full replacement arrays:

  | Experiment | Qwen | Gemma |
  |---|---:|---:|
  | `legacy_q9` | `19391660` | `19391661` |
  | `cross_region` | `19391662` | `19391664` |
  | `typed_two_stage` | `19391666` | `19391667` |
  | `matched_rca` | `19391668` | `19391669` |
  | `visual_counterfactual_rca` | `19391670` | `19391671` |
  | `ledger_handoff_rca` | `19391672` | `19391673` |

These arrays use the same eight-shard/four-concurrent-task/three-day H100
contract and depend only on successful v3 preparation and both v8
infrastructure smokes. They supersede every earlier full-array job ID.

The next v8 retry (`19391949`, `19391950`) loaded the exact models and showed
the cache and usage-reporting fixes working, but the readiness `curl` omitted
the bearer token required after vLLM inherited `VLLM_API_KEY=EMPTY`. Gemma was
healthy and returned `401 Unauthorized`; neither job created a trajectory.
The smokes, remaining v3 preparation tasks, and dependent arrays
`19391953`–`19391965` were cancelled. The readiness checks now send the same
local bearer token as the client and attestation. Because launch scripts are
freeze-bound, a new preparation/launch generation is required.

## Qualified smoke and final-run authorization

The authoritative v9 smoke preparation, array job `19392100`, completed and
verified three frozen cases under runtime freeze
`886aba404e5e43b6f3425fec12a026d674d22f858db6bfca9e62267c0f9f350d`.
Its result root is
`rq1_nibi_smoke_v9__shard-0000-of-0001`.

- Qwen job `19392124` passed by the registered timeout-only rule after
  600.017 seconds. It completed four calls with valid parsed responses,
  complete token/timing accounting, and no infrastructure error before the
  supervisor terminated the outstanding work.
- Gemma job `19392125` passed normally after 257.664 seconds. It completed all
  nine expected calls with valid parsed responses, complete accounting, and
  zero infrastructure errors.
- Server access logs contain 13 successful chat-completion requests in total
  (four Qwen and nine Gemma), below the 18-call logical-smoke ceiling. Qwen
  tokenized a fifth pending input but did not initiate its chat-completion
  request before timeout.
- The final result-root verifier reports 13 trajectories, no missing artifact,
  no integrity error, and `passed: true`. Both allocations report one NVIDIA
  H100 80GB HBM3, the recorded environment/config hashes, and termination exit
  code zero.

All prompts, raw responses, conversation histories, finish reasons,
truncation fields, and accounting records were inspected. Scientific answer
quality varies, as expected, but no hidden protocol, persistence, numerical,
or infrastructure defect blocks the frozen full run. This qualification
supersedes every earlier diagnostic smoke generation.

## Authoritative full-run submission

The frozen 469-case CPU preparation was submitted as eight-shard array
`19392679` with base ID `rq1_nibi_final_469_v4`. The following three-day,
one-H100 arrays each contain eight resumable shards and cap simultaneous tasks
at four. Every array depends only on successful preparation `19392679`; there
is no scientific-threshold scheduler dependency.

| Experiment | Qwen | Gemma |
|---|---:|---:|
| `legacy_q9` | `19392682` | `19392683` |
| `cross_region` | `19392684` | `19392685` |
| `typed_two_stage` | `19392686` | `19392687` |
| `matched_rca` | `19392688` | `19392689` |
| `visual_counterfactual_rca` | `19392690` | `19392691` |
| `ledger_handoff_rca` | `19392692` | `19392693` |

These job IDs supersede all earlier cancelled full-run arrays. Bugs,
contract mismatches, and infrastructure failures are repaired and resumed
under a new freeze when required; efficacy-threshold failures remain negative
results and do not stop any experiment.

## v4 port-collision failure and v5 recovery

Preparation `19392679` completed all eight shards successfully: five shards
contain 59 cases and three contain 58, for 469 unique opaque incidents under
freeze `886aba404e5e43b6f3425fec12a026d674d22f858db6bfca9e62267c0f9f350d`.
Every shard verifier passed. Once the full arrays released, Slurm placed
multiple one-GPU jobs on shared hosts. All launchers used localhost port 8000,
so some Qwen jobs reached an already-running Gemma endpoint. Live attestation
correctly rejected the mismatch in tasks `19392682_2`, `19392682_3`, and
`19392684_2`.

All v4 GPU arrays `19392682`–`19392693` were cancelled immediately. Their
partial trajectories and server logs are diagnostic only and will not be
merged or scored. The fix adds a task-local port selected from the unique
Slurm task job ID after confirming that it is unbound, then propagates the
same endpoint through serving, readiness, attestation, tokenization, and
inference. The runtime record now includes the selected port and URL. Static
and simulated two-job checks pass without changing any scientific inference
field.

Recovery submissions under the new source freeze are:

- v10 smoke preparation: `19393384`;
- v5 final 469-case preparation: `19393385`;
- v10 Qwen/Gemma 30-minute H100 smokes: `19393386` and `19393387`, dependent
  on smoke preparation.

Full arrays will be resubmitted only after the corrected smoke has exercised
the live task-local endpoints. The v5 CPU preparation runs concurrently
because it cannot call a model and its artifacts remain freeze-bound.

## Qualified recovery and authoritative v5 arrays

The v10 smoke verified 13 persisted trajectories with no missing or integrity
error. Gemma completed all nine calls normally; Qwen completed four calls and
passed by the 600-second timeout-only rule. Both live attestations matched the
requested served model, runtime ports were 58387 and 58386 respectively, and
both allocations exited zero with no fatal server signature.

Final preparation `19393385` completed five 59-case shards and three 58-case
shards. All eight verifiers pass, the union contains exactly 469 unique opaque
incidents, and every index records runtime freeze
`a1e9be3dd5196d123252e5c9283b02ed80516c9fc9d36727bccff7d748946ae3`.
Slurm declined an `afterok` dependency added after the already-verified array
had finished; the arrays were therefore submitted directly against the
existing immutable roots.

The authoritative v5 three-day H100 arrays are:

| Experiment | Qwen | Gemma |
|---|---:|---:|
| `legacy_q9` | `19393775` | `19393776` |
| `cross_region` | `19393777` | `19393778` |
| `typed_two_stage` | `19393779` | `19393780` |
| `matched_rca` | `19393781` | `19393782` |
| `visual_counterfactual_rca` | `19393783` | `19393784` |
| `ledger_handoff_rca` | `19393785` | `19393786` |

Each has eight resumable shards, an array concurrency cap of four, and no
efficacy-threshold dependency. These IDs supersede every earlier full-array
generation.

At first-wave startup, matched/Qwen task `19393781_2` selected port 59288
after the port appeared unbound but vLLM then received `EADDRINUSE`, consistent
with a foreign-process bind race between the availability check and server
bind. The task made zero model calls and exited before attestation. The other
co-located tasks continued with distinct, correctly attested endpoints. Only
that shard was resubmitted as resumable retry array `19394347` (task 2); a new
Slurm task ID supplies a different candidate port without changing the frozen
launcher or duplicating any active shard.

Qwen ledger-handoff tasks `19393785_0` and `19393785_1` subsequently exposed
a separate experiment bug after one successful stage-1 call each. The visual
handoff used `ImageFont.load_default()`; Pillow-SIMD 9.5's bitmap font could
not encode the em dash in the fixed board title and raised
`UnicodeEncodeError` before any stage-2 trajectory was persisted. The remaining
Qwen ledger tasks and the not-yet-started Gemma ledger array were cancelled;
their v5 artifacts are diagnostic only. The other five v5 experiments remain
unchanged and active.

Both base and inference environments successfully render the same title with
the portable logical font name `DejaVuSansMono.ttf`. After every non-ledger v5
shard has finished, the ledger renderer will adopt that font, receive a fresh
runtime freeze/preparation, and rerun all ledger shards for both models. This
sequencing avoids invalidating pending v5 shards while still repairing and
completing the sixth experiment.

## v5 context failure and complete replacement

Before the non-ledger arrays finished, completed Gemma `legacy_q9` shards
revealed six deterministic HTTP-400 infrastructure records: the T and H arms
of three frozen RE2-TT cases supplied at least 16,385 prompt tokens and also
requested the complete 16,384-token output ceiling under a 32,768-token
context. No scientific response or label was used in diagnosing the request
arithmetic. The same frozen text packets can occur in the other experiments,
so continuing v5 would knowingly create incomplete paired cases.

All remaining v5 arrays `19393775` through `19393786` and the isolated matched
retry `19394347` were cancelled. Roughly 4,652 successful calls already made
under that freeze remain diagnostic and are excluded in full; no partial v5
outcome is used for prompt, renderer, model, stopping, or architecture
selection. This supersedes the preceding plan to let non-ledger v5 shards
finish before changing the renderer.

The replacement protocol adopts `context_safe_output_v1`: all RQ1 calls now
request 8,192 output tokens, independent of model, case, dataset, experiment,
arm, or stage, and perform a live-tokenizer context guard before inference.
The global 16,384 ceiling is unchanged. The adapter content/hash is frozen and
persisted per stage. The ledger board now uses the portable Unicode-capable
`DejaVuSansMono.ttf` font at 12 px; it passed both base/inference rendering and
visual inspection. The complete zero-call static suite passes with all six
experiments, 469 exact cases, and 1,858 functional RQ1 source lines.

## Replacement v11/v6 submissions

The corrected smoke preparation is array `19397130` with base ID
`rq1_nibi_smoke_v11`; the fresh eight-shard 469-case preparation is array
`19397131` with base ID `rq1_nibi_final_469_v6`. The two 30-minute H100 smokes
are Qwen `19397136` and Gemma `19397137`, each dependent on successful smoke
preparation.

All twelve three-day H100 arrays were submitted up front with a joint
`afterok` dependency on the complete final preparation and both smokes:

| Experiment | Qwen | Gemma |
|---|---:|---:|
| `legacy_q9` | `19397332` | `19397333` |
| `cross_region` | `19397334` | `19397335` |
| `typed_two_stage` | `19397336` | `19397337` |
| `matched_rca` | `19397338` | `19397339` |
| `visual_counterfactual_rca` | `19397340` | `19397341` |
| `ledger_handoff_rca` | `19397342` | `19397343` |

Every full array has eight resumable shards, caps concurrency at four, requests
one H100 with 14 CPUs and 240 GB RAM per task, and has a three-day allocation.
There is no efficacy-threshold dependency.

The v11/v6 preparation jobs failed in seven to eight seconds before creating a
prepared index because the submission environment omitted the runtime-only
`RL_SLM_RCA_ROOT` override and fell back to the nonexistent legacy sibling
name. Their dependent smokes and full arrays were cancelled without starting.
The source/config freeze did not fail; this was a Slurm export omission.

Clean replacement submissions explicitly export the upstream adapter root,
processed-case root, and scratch root:

- v12 smoke preparation `19397350`, Qwen smoke `19397353`, Gemma smoke
  `19397354`;
- v7 final preparation `19397351`;
- full arrays `19397355` through `19397366`, in the same experiment/model order
  as the preceding table.

The v7 arrays retain the joint `afterok` dependency on complete preparation
and both corrected smokes.

Both v12 H100 smokes qualified. Gemma `19397354` completed all 9 calls normally
in 245.71 supervisor seconds; Qwen `19397353` completed 4 calls and passed by
the registered timeout-only rule at 600.01 seconds. Together the server logs
record 13 successful chat-completion requests, below the 18-call cap. All 13
persisted trajectories are completed and parsed, none finished by length, and
every stage records an 8,192-token request, 32,768-token context, positive
headroom, and complete token/time accounting. There are 13 matching
conversation Markdown files. The result-root verifier reports zero missing or
integrity errors, and both Slurm allocations terminated with exit code zero.

Final v7 preparation `19397351` then completed all eight CPU shards with exit
code zero. Counts are `[59, 59, 59, 59, 59, 58, 58, 58]`, totalling 469 cases
and 469 unique opaque incident IDs. Every shard verifier passes with no missing
or integrity error, and all indexes share runtime freeze
`73f2667acdfc03b5b32a1aa0e9c57111647941502a29ce5feecbc6e0e74a747a`.
The twelve full arrays were consequently released from their dependencies.

The user subsequently limited future sharded GPU array elements to one day.
Active v7 arrays `19397355`–`19397366` are intentionally unchanged and continue
running or waiting under their submitted three-day limits. The launcher is
freeze-covered, so its default will change only after this formal run reaches
a lifecycle boundary and before a future sharded submission.

The user then reduced the future per-shard limit again, from one day to six
hours, based on the observed completion time of early v7 shards. This
supersedes the one-day future preference. Active v7 arrays remain unchanged;
the freeze-covered launcher will be updated and requalified only after v7's
lifecycle boundary.

The user also capped every new Slurm job at 100 GiB of host RAM. Active v7
arrays remain unchanged at their submitted 240 GiB per task. Existing CPU job
types already request less than the cap. Any new GPU repair submission before
the v7 lifecycle boundary must use explicit 100 GiB and six-hour `sbatch`
overrides without editing the active freeze-covered launcher; after the
lifecycle boundary, those values become the requalified launcher defaults.

## v7 first-wave progress and array-release anomaly

The first four Gemma `legacy_q9` shards completed with 708/708 expected
trajectory records, zero infrastructure errors, matching conversation files,
and exit code zero. All four Gemma `cross_region` first-wave shards also
completed cleanly with 4,012/4,012 expected records and matching conversations.
Qwen `legacy_q9` shard 2 independently completed 177/177 records with the same
clean persistence and termination checks. These are operational completeness
statements only; partial scientific outcomes remain uninspected.

Slurm has not released a successor from any of those arrays. The pending
umbrella records retain `ArrayTaskThrottle=4`, have no dependency, receive live
`LastSchedEval` updates, and report `JobArrayTaskLimit` even after their earlier
tasks are terminal. The same behavior now affects multiple parent arrays, so it
is not attributable to one experiment artifact. Other active v7 tasks continue
to make progress and no task has failed. In accordance with the instruction to
leave already-submitted jobs unchanged, no array throttle, priority, resource,
or task state has been modified. Continue six-minute monitoring while useful
active work remains; if the pending second waves become the execution blocker,
document the final scheduler evidence and select a non-overlapping remedy that
preserves the instruction to leave the current submissions unchanged. Any
newly submitted job must use the recorded 100 GiB and six-hour limits.

The user then increased the future sharded GPU limit from six to twelve hours.
Audited Qwen `legacy_q9` shards had already required 6:01:50 and 6:03:18, and
several more expensive experiment types remained active, so six hours lacked
practical headroom. Active v7 jobs remain unchanged. Any new GPU submission
uses at most 100 GiB RAM and a twelve-hour limit; these become requalified
launcher defaults only after the active v7 lifecycle boundary.
