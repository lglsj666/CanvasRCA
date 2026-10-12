# RQ4.2 — completed and analyzed, 2026-10-10

**All 1,336 positions completed; the preselected SEM candidate is not adopted.**
There are 1,328 real calls and 8 exact references, with no infrastructure unknowns.
FULL/GEOM/SEM/SHAM/NATIVE4 MRR is .2841/.3088/.3084/.3011/.3235.
The best completed pure-visual historical reference remains A_UNIFORM_E50 (.3517);
T_FULL (.4846) and hybrid MARGINAL_FIVE (.5054) are retained without rerunning.
SEM saves 24.02% total tokens against T_FULL but costs 2.89 times A_UNIFORM_E50.
Registered ranking and latency objectives fail; primary and mechanism families
do not pass Holm correction. The worker has exited and the phase is committed.

See the [final report](../../docs/experiment_reports/RQ4_2_Qwen_Analysis_2026-10-10.md),
[analysis artifacts](results/partition_v4/final_analysis_v1/README.md), and
[authoritative findings](findings/exp_partition_findings.md).
The following launch/readiness instructions are historical operational records;
they do not authorize another run or change the completed queue.

## Historical reporting update — 2026-10-10

Historical comparison update: include both RQ3.16 `MARGINAL_FIVE` and RQ4.1
`T_FULL`, retaining `A_UNIFORM_E50`. Reuse their completed answers with zero new
calls. Both requested baselines match all 220 registered cases. See the
[dated reporting supplement](descriptions/RQ4_2_Historical_Controls_2026-10-10.md)
and its source manifest; the frozen execution queue is unchanged.

**Historical launch checkpoint:** formal experiment launched and 180-second startup monitoring passed. At handoff the worker continued in the background. The experiment has since completed. Use `bash RQs/RQ4_2/scripts/status.sh` for authoritative persisted status.

## Historical prelaunch checkpoint — Evidence-closed vision partitioning

**Formal runner ready; not launched.** CPU, inherited GPU smoke and 18 affected formal recovery checks pass. One process owns the local model; complete replies and atomic completion markers survive restart. No active execution credential is installed.

Current queue: 1,336 positions, 8 exact references, 1,328 unique model requests; 142 infrastructure retries reserved. See the [formal readiness report](../../docs/experiment_reports/RQ4_2_Formal_Readiness_2026-10-09.md) and [current findings](findings/exp_partition_findings.md).

```bash
cd /home/lglsj/CanvasRCA_nibi
bash RQs/RQ4_2/scripts/check_formal.sh  # read-only qualification; no GPU
bash RQs/RQ4_2/scripts/status.sh       # persistent progress and process identity
```

Following later explicit user authorization, install the version-bound activation template from `results/partition_v4/formal_deployment_snapshot/activation.template.json` as `configs/activation.json`, then:

```bash
bash RQs/RQ4_2/scripts/formal.sh --resume
```

This same command starts an untouched queue or resumes after shutdown. It runs in the background and logs beneath `results/partition_v4/formal_v1/logs/`. A stale credential/source refuses execution before model allocation. A `BLOCKED.json` means a known failure needs diagnosis; do not delete it merely to retry.

```bash
bash RQs/RQ4_2/scripts/pause.sh
bash RQs/RQ4_2/scripts/status.sh
```

Pause drains the current request. Wait for `paused` and `live=false` before normal shutdown. After abrupt power loss, committed requests are skipped; durable complete replies are finalized without regeneration; incomplete calls spend a retry. Partial answers are never scored or spliced.

Five functional modules remain under `src/`; method registration is `configs/partition_v4.json`, execution is `configs/formal_v1.json`. Rendering/geometry preparation from `results/partition_v3/` remains immutable. Old smoke failures and all historical results are retained.
