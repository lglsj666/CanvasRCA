# RQ3.16 marginal coverage — completed, preselected method not adopted

2026-10-03 America/Toronto。正式八臂220 exposed eval共1760位置已终态：1713真实响应、45精确回退引用、2请求超时；另9份重复实体model_failure保持零分。正式1715 attempts＋18 smoke=1733/1820，自有服务退出，没有后继运行。

完整审计通过：220公共事实/身份、1713唯一graph、1758实际prompt/评分回放/processor tokens及843 PNG传输。184有效冻结源及运行attestation/执行授权兼容一致。36固定hash病例全部288理由阅读、12定向断言核验；未逐断言核对的轴保留unknown，不宣称解释可信度改善。

| Arm | pooled MRR | AIOPS-2022 MRR | AIOPS-2025 MRR | AegisLab MRR |
|---|---|---|---|---|
| BASE_FLEX | .4336 | .3014 | .3256 | .5777 |
| PAIR_FLEX | .4317 | .3069 | .2911 | .5910 |
| MARGINAL_FLEX | .4716 | .3728 | .3681 | .5943 |
| BASE_FIVE | .4433 | .3439 | .3218 | .5747 |
| PAIR_FIVE | .4436 | .3192 | .3086 | .5993 |
| MARGINAL_FIVE | .5054 | .4286 | .3708 | .6322 |
| MARKLESS_FIVE | .4963 | .3972 | .3625 | .6360 |
| MARGINAL_REPEAT | .5039 | .4244 | .3708 | .6313 |

BASE_FIVE为219 known、MARGINAL_FLEX为219，其他220。未知超时不记零，均值不同分母不能代替配对。完整六指标、全分母界限和宏平均见最终报告。

四项主要配对MRR：MARGINAL_FIVE−PAIR_FIVE+.0617（220），−MARKLESS+.0091（220），−BASE AIOPS+.0702（119），−BASE Aegis+.0575（100）。四项病例Holm均.5326，事件组.8432或.8824，均未达到pH<.05。Top5覆盖护栏在A25对BASE/PAIR及Aegis对PAIR失败。三个数据集MRR点估计虽正，数据点独立贡献未建立；Aegis完整图甚至比markless低.0038。

次要结果：固定五相对同输入边际FLEX MRR+.0315，病例/组pH=.0173/.0400；AC5+.0776，pH=.000673/.001073。PAIR固定五AC5+.0591亦显著；这只支持输出容量策略在当前输入下修复部分短列表损失，不构成主要视觉机制成功。交互不显著；不能选repeat或markless改写预选。

真实已知正式成本37926673 tokens，2超时usage未知。已知配对MARGINAL/BASE总token比1.1546/1.1867/1.1937，/PAIR1.0398/1.0436/1.0360；A25完整BASE成本界限[1.1776,1.2072]跨过1.20，不把59配对通过写成全60实测验证。MRR重复218/220相同，完整排名204/220、全文53/220相同；稳定不证明解释正确。

**Decision: stop this marginal-duration candidate under the registered rule. No automatic layout tuning, posthoc winner, new inference or test. RQ3.16 is complete; RQ3 overall deployable-performance/visual-contribution/cost/trust objective remains unmet.**

最终详细报告：[RQ3.16 analysis](../../../docs/experiment_reports/RQ3_16_Qwen_Analysis_2026-10-03.md)。离线原子证据、全部统计、成本和审查：`../results/marginal_coverage_v1/analysis_detailed_v1/`。没有改变任何冻结输入、历史结果或评分。

## Historical launch and qualification snapshots (superseded operational status)

# RQ3.16 marginal coverage — formal run in progress


Current operational status: full execution authorized by the user and launched at13:22:16 America/Toronto. At13:25:17,7 committed responses and36 active requests, no failures; registered1760 positions remain in progress. No complete-stage efficacy result or adoption decision exists. See `../results/marginal_coverage_v1/formal/launch_verification.json`. Original qualification hash below stays historical; activated source is `fbd23ac5b419c2a229c667a75403c0bceb3f04a28d32c1c3cfdc6e1d39f897a1`.

## Completed qualification history

2026-10-03 America/Toronto. Static, complete220 CPU, actual12-PNG visual
inspection and bounded18-call GPU smoke passed. Owned service stopped; formal
calls0 and formal gate closed. No RCA efficacy/adoption conclusion is available.

All211 inherited marginal PNGs reused unchanged,211 markless controls generated
by the unified renderer;9 cases fall back without exclusion.422 PNGs and32,624
bindings checked. Input budgets1.1540/1.1870/1.1941 versus BASE_FIVE and
1.0390/1.0420/1.0357 versus PAIR_FIVE pass for A22/A25/Aegis. Max input26,141.
Default three-case redraws reproduce historical bytes. No new component/operation.

Smoke:18 real calls,12 FIVE outputs all five distinct legal IDs,9 image transports,
397,439 total tokens;205.27s execution,392.91s including detailed audit. No timeout,
truncation or infrastructure failure. All18 rescoring and actual-input audits pass.
Reason errors remain, including temporal ordering contradictions, first-rank/reason
inconsistency, reversed direction and unsupported causal claims. Engineering
qualification does not establish trustworthiness or improved MRR.

The prospective eight-arm protocol tests marginal data glyphs and output capacity
under fixed evidence; previous joint-route failure remains preserved. Four primary
case/group Holm comparisons, explicit dataset/cost/top5 guards and a stop-on-failure
rule apply to any future authorized formal run. Same exposed eval is not confirmation.

Detailed qualification: [report](../../../docs/issues/RQ3_16_qualification_2026-10-03.md).
Current source contract: `612c92660201ece2cd6cdbbaf7cc7b33fe31ca18deebbea824be96b3641f82d1`.
