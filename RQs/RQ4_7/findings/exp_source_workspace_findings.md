# RQ4.7 — retained single-call findings

Date:2026-10-20. **Only S_COMPARE,S_GROUND,S_REASON experiment data remain.**

The user explicitly ordered deletion of all M_CROP,M_CLOSED,M_COMPARE experiment data and results,including shared action plans,all inputs/outputs,conversations,attention,intermediate material,statistics and report artifacts. Those records have been removed without backups. Code and registered design documents remain as historical implementation/design,not evidence that deleted records are recoverable. Public source objects remain only where required by actual S inputs.

## Retained results

- S_COMPARE standard/tolerant MRR:0.2999/0.3217.
- S_GROUND:0.3005/0.3320; S_REASON:0.2712/0.2941.
- All three methods underperform historical U0.3517; S_GROUND does not advance.
- The two retained S primary comparisons keep the original preregistered Holm correction; deletion does not justify a smaller correction family.
- Retained formal subset:870 positions,750 actual calls,247 actual attention summaries. Retained smoke subset:6 positions,5 actual calls,4 attention summaries.
- S input identities and exact request/trajectory/scoring/image/attention dependencies were verified. No S answer was regenerated or altered.

## QA validity correction — 2026-10-20

An offline audit of all 360 retained QA questions found 19 invalid questions in 17 cases: relation-level measurements were assigned an empty single-entity oracle. Another 90 questions require undefined canonical phase vocabulary; 41 have unregistered equivalent unit spellings. Risk categories overlap and the remaining questions are not thereby certified valid. The original joint-zero scores are retained for provenance, not accepted as a qualified measure of visual understanding or evidence of QA–RCA independence. All target coordinates and scalar source texts were checked; 13 images including crops were visually reviewed, within the user limit of 20. No model calls, runtime/scorer changes or original-score mutations occurred. Independent RCA results are unaffected. See the [answerability audit](../../../docs/experiment_reports/RQ4_7_QA_Answerability_Audit_2026-10-20.md).

## Storage and execution state

The SQLite ledger is purged and vacuumed. Full-run authorization,qualification receipts,logs,queues,completion/aggregate summaries and mixed manifest were retired. `frozen/retained_manifest.json` and `retained_*_queue.json` describe only the retained subset. There is no valid full-run resume or model authorization. No model call or Nibi operation occurred during deletion.

[Updated S-only report](../../../docs/experiment_reports/RQ4_7_Qwen_Analysis_2026-10-20.md) retains S metrics,comparisons,costs,QA,actual answer inspection,repeats and attention. Deleted-condition results and conversation excerpts are absent from the report and its attachments.
