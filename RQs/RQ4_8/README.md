# RQ4.8 — Card selection, evidence recovery and valid QA

The [registered plan](../../docs/experiment_plans/RQ4_8_Card_Selection_Hybrid_Recovery_and_Valid_QA_Plan_2026-10-20.md)
defines eleven new arms, three independent qualifications and a 4,000-attempt
ceiling. Hybrid and two-stage methods are explicitly authorized for this round;
Codex.md and historical experiment implementations remain unchanged.

Five modules: `exps` compiles public inputs and hosts the native vLLM adapter;
`utils` owns receivers, central scoring, transport and durable commits;
`main` schedules CPU preparation and dependency-aware inference; `gates` owns
qualification, freeze and statistics; `tests` owns offline counterexamples.

Both QA and card selection tolerate syntax defects and individually discard
invalid IDs. Required multi-value questions receive 1 for a complete solution,
0.5 for a correct but incomplete portion, and 0 for no correct values. Alternative
solutions are different: any one complete allowed alternative earns 1. Parsing
never reads the oracle. Strict formatting and full content correctness are also
retained. These changes do not alter RCA ranking scoring.

```bash
bash RQs/RQ4_8/scripts/static.sh
bash RQs/RQ4_8/scripts/cpu.sh unit
bash RQs/RQ4_8/scripts/cpu.sh cpu
bash RQs/RQ4_8/scripts/cpu.sh qa
bash RQs/RQ4_8/scripts/cpu.sh runtime
bash RQs/RQ4_8/scripts/run.sh status
```

GPU entrypoints require a source-bound qualification credential. After qualification,
`run --scope smoke_single`, `smoke_multi`, and
`smoke_qa` each have their own 18-attempt/900-second allocation. Formal requires
all three reviewed receipts and closure of the targeted repair findings. No code
import or CPU success starts a model.

The authorized formal deployment reuses the genuine 220-case CPU and visual/unit
receipts at their original revisions. The actual specialty smokes and repair smoke
supply runtime evidence; no new CPU runtime pass is fabricated. Missing formal QA
inputs are prepared separately with `prepare-formal-qa` (60 fixed cases), without
rerunning the 220-case regression. `bind-formal` verifies the source differences,
input hashes, private scoring contexts and call budget, and freezes a separate
`formal_freeze/v1` snapshot. Original smoke snapshots remain intact.

```bash
bash RQs/RQ4_8/scripts/run.sh status
tail -f RQs/RQ4_8/results/card_selection_v1/formal/run.log
```

`pause --scope formal` drains active requests; rerunning `run --scope formal`
resumes from atomic completed records after removing the explicit pause request.
The selector's committed answer is reused on a stage-two restart. No original
overview, selection rationale or chat history is forwarded to stage two.
`view --scope formal --key KEY` renders exact retained conversations for inspection.

Qualification and findings must be read from the current receipts; neither this
README nor a static pass certifies actual model execution.

The user-authorized `smoke_repair_v2` adds one targeted 18-call/900-second
repair scope, charged against recovery reserve (now 88; total ceiling unchanged).
It reuses prior CPU evidence under explicit skip-CPU authority and freezes its
sources separately. It passed with 18 actual calls; see
[repair review](results/card_selection_v1/smoke_repair_v2/REVIEW.md).
