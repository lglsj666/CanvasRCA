# 实验计划

2026-10-05 研究收敛补充：[五个重要反直觉现象](../../important_docs/CanvasRCA_Counterintuitive_Findings_2026-10-05.md)。QA 到 RCA 的任务相关性是下面表示分配候选的前置缺口；该候选尚未确定为下一算法。已有数值写法翻转值得优先复核，标题 attention 保留为机制线索；按用户要求补入完整文本加图退化及文本接口敏感性，分别用于研究证据干扰与控制接口差异。不新增布局消融或 attention 采集，不改变 RQ3.18。

2026-10-05 最新研究目标：[从优秀实证到预算受控的新方法](../../important_docs/CanvasRCA_Empirical_to_Method_2026-10-05.md)。将MRR约0.60与实际成本最多增加5%联合考虑；完成历史报告去重及[实证论文/最近工作复核](../../important_docs/CanvasRCA_Empirical_Literature_Review_2026-10-05.md)。提出以实际联合读取错误指导文字/图像分配的单一候选，2,880调用仅为后继资源草案、未授权注册或启动；RQ3.18冻结运行不变。历史RQ3.16成本重算保留正向信号与原采用限制。

2026-10-05 项目安排：[WWW 2027 投稿冲刺与研究收敛](CanvasRCA_WWW2027_Submission_Sprint_2026-10-05.md)。10月7日方法/主张决策截止，10月16日摘要、23日全文内部交付；先补强文本对照、技术新意、数据曝光与冻结验证证据。RQ3.18按原协议继续，本安排不修改其阈值、矩阵、源或预算，不自动启动后继实验。

2026-10-04 最新：**RQ3.18 GPU smoke 18/18通过，已按用户授权启动11臂2420位置全量。** 已确认实际推理与首批原子结果提交；[执行记录](../../RQs/RQ3_18/results/population_readout_v1/logs/2026-10-04_gpu_and_formal_execution.md)。下方CPU后停止是此次授权前的历史状态。

- [RQ3.18：总体耗时读数与视觉比较](RQ3_18_Population_Readout_Plan_2026-10-04.md)：旧六臂计划、代码和测试产物已按用户要求删除；新11臂/2420位置、2500调用预算。**静态、完整220例CPU及实际例图审查通过，已停止；GPU smoke未运行，正式未启动，模型调用0。** [资格报告](../../RQs/RQ3_18/results/population_readout_v1/qualification/report.md)；[例图](../../RQs/RQ3_18/preparation/population_readout_v1/examples/index.html)。

2026-10-04 最新完成状态：**RQ3.17 v4正式3080位置全部终态，详细分析已完成，预选组合不采用。** 2983真实响应＋76引用＋21超时，5份重复ID输出保留零分；自有GPU服务关闭。C MRR .4957，对T配对+.0265，但低于D/N，六主要比较均未通过病例/事件组校正；Aegis C−T−.0340及Top5−4pp，节点组合未修复。CPU资格保持用户豁免，不追记为通过。解释审查为503份规则筛查、119份人工阅读及12条源核验，未声称全量人工解释审计。[详细报告](../experiment_reports/RQ3_17_Qwen_Analysis_2026-10-04.md)；[完成日志](../../RQs/RQ3_17/results/topology_marginal_v4/logs/2026-10-04_final_analysis.md)。停止当前候选，不自动更换布局或追跑事后赢家；以下恢复/暂停/执行状态均为历史记录。

2026-10-04 当前：**RQ3.17 v4 已按用户要求恢复。** 从774个未完成位置继续，跳过已提交结果与组合阶段；GPU已开始推理，新结果正常落盘，显存利用率0.75。[恢复记录](../../RQs/RQ3_17/results/topology_marginal_v4/logs/2026-10-04_resume.md)。以下暂停/运行记录保留为历史状态。

2026-10-04 当前：**RQ3.17 v4 已按用户要求安全暂停，GPU服务已关闭。** 2306/3080位置终态（2288成功含72引用、18超时），剩余774；待用户明确恢复。[暂停记录](../../RQs/RQ3_17/results/topology_marginal_v4/PAUSED_BY_USER_2026-10-04.md)。以下运行/暂停状态为历史记录。

2026-10-03 当前：**RQ3.17 v4 GPU smoke 18/18通过，全量进程已启动。** 220例准备完成；CPU在日志160/220处由用户明确要求跳过，未记为通过。14臂/3080位置，先完成两种组合440位置。[执行记录](../../RQs/RQ3_17/results/topology_marginal_v4/logs/2026-10-03_execution.md)。以下暂停状态均为历史记录。

2026-10-03 最新：**RQ3.17 v4仅加粗上方调用图的虚线及其箭头至3倍；实线及箭头、整个deployment面板不变。** 静态/类型/三病例图像回归通过，例图供审阅，GPU/全量仍暂停。[修订](RQ3_17_Dashed_Width_2026-10-03.md)；[暂停记录](../../RQs/RQ3_17/results/topology_marginal_v4/PAUSED_BY_USER.md)。

2026-10-03 最新修订：**RQ3.17 v3 已按审图意见改为直接配色，移除跨组件圆圈与编号。** 14臂保持，静态/35项renderer回归/三个病例例图检查通过，完整CPU、GPU和正式实验仍暂停。[配色修订](RQ3_17_Direct_Color_Binding_2026-10-03.md)；[当前暂停记录](../../RQs/RQ3_17/results/topology_marginal_v3/PAUSED_BY_USER.md)。以下v2/v1为历史状态。

2026-10-03 最新补充：**RQ3.17 v2 已增加五个节点箭头对照臂，代码和例图完成，等待用户审图。** 静态、35项renderer回归和三病例例图检查通过；完整CPU/GPU/正式实验保持暂停。[14臂修订计划](RQ3_17_Topology_Encoding_Amendment_2026-10-03.md)；[交付与暂停记录](../../RQs/RQ3_17/results/topology_marginal_v2/PAUSED_BY_USER.md)。

2026-10-03 最新状态：**RQ3.17 按用户要求暂停。** 当时正在运行的 CPU 回归已完成并通过（220/220）；GPU smoke 和全量均未启动。用户指出 dashboard 存在问题，视觉资格已改为待复核，先前全量授权的执行已暂停。[暂停记录](../../RQs/RQ3_17/results/topology_marginal_v1/PAUSED_BY_USER.md)；[计划](RQ3_17_Topology_Marginal_Binding_Plan_2026-10-03.md)。

本目录集中保存研究与执行计划。报告及其图表、汇总数据位于 [experiment_reports](../experiment_reports/README.md)。

## 当前建议

2026-10-03当前最终状态：**RQ3.16全量及详细分析已完成，当前边际耗时候选停止，不自动启动后继。** 1760终态、1713响应/45引用/2超时，9个重复实体回答保持零分；[完整报告](../experiment_reports/RQ3_16_Qwen_Analysis_2026-10-03.md)。MARGINAL_FIVE MRR .5054，对同事实文本+.0617但主要四项病例/组Holm均不显著；去点对照.4963，独立数据点增益+.0091未建立。A25/Aegis对PAIR Top5下降，覆盖护栏失败。固定五有次要正结果，不能据此宣布视觉机制或RQ3主线目标已达成。自有服务关闭，旧资格与启动快照均为历史状态。

以下RQ3.16启动与资格记录保留历史，不是当前队列状态。

2026-10-03后续明确授权：**RQ3.16全量实验已于13:22:16 America/Toronto后台启动**，原八臂×220例=1,760位置；13:25:17核验7份响应已提交、36在途、无失败，显存利用率参数0.75。[启动核验](../../RQs/RQ3_16/results/marginal_coverage_v1/formal/launch_verification.json)与[授权兼容审查](../../RQs/RQ3_16/results/marginal_coverage_v1/qualification/activation_v1/activation_review.json)已落盘。保持原方法/门槛，不根据部分结果调参；结束后自动关闭自有服务。下方“资格后停止”记录为此次新授权前的历史状态。

2026-10-03最新状态：**[RQ3.16：边际图元与候选覆盖](RQ3_16_Marginal_Coverage_Plan_2026-10-03.md)计划、代码和资格已完成，并按用户要求停止。** 八臂同证据/输出容量受控比较；静态、完整220例CPU、实际图像及18/18 GPU smoke通过，自有服务关闭。[详细资格报告](../issues/RQ3_16_qualification_2026-10-03.md)和[实际例图库](../../RQs/RQ3_16/results/marginal_coverage_v1/qualification/gallery/index.html)已落盘。正式1,760位置仅登记，正式调用0、启动权限关闭。它是新开发假设，不能将RQ3.15最高均值或smoke通过追认为已证实视觉收益；下列RQ3.15结论保持不变。

2026-10-03最终状态：**RQ3.15正式矩阵及详细分析已完成，预选方法不采用，按原计划停止此机制路线。** 11:42:16 America/Toronto完成1320终态；1279真实响应、36引用、5超时，自有服务关闭。[详细报告](../experiment_reports/RQ3_15_Qwen_Analysis_2026-10-03.md)给出全部指标、成本、统计和机制分析。V−PAIR_TEXT+.0281，但V−MARGINAL−.0134；Aegis对BASE+.0007，主要病例/事件组Holm均不显著。不得据此自动改布局、改用最高均值臂、消耗剩余调用或启动后继实验。RQ3整体研究目标仍未达成。

以下启动、暂停、恢复与资格状态均为历史时间点，不是当前运行状态。

2026-10-03恢复历史：10:50:22启动、10:53:42 America/Toronto核验。恢复队列沿用已有822个终态位置，继续其余498个位置；核验时累计804份响应（10份新增）、36次在途，无新增失败，旧调用未重复提交。原输入、预算和显存利用率0.75保持不变。[恢复记录](../../RQs/RQ3_15/results/request_joint_v1/formal/resume_receipt.json)保存当时的运行快照。

2026-10-03 01:10:34 America/Toronto：**RQ3.15已按用户要求安全暂停**。没有新增提交；36个在途请求全部正常收尾，794份真实响应已提交，模型服务及进程全部退出、端口关闭。不自动恢复，须等待用户明确授权。当前状态见[暂停记录](../../RQs/RQ3_15/results/request_joint_v1/formal/pause_request.json)，下列启动信息为历史。

- [RQ3.15：同请求连续耗时关系](RQ3_15_Request_Joint_Plan_2026-10-02.md)：代码、220例CPU资格及18次GPU smoke均通过；[详细资格报告](../issues/RQ3_15_qualification_2026-10-02.md)。用户随后明确授权全量实验，已于2026-10-02 23:49:54 America/Toronto启动1320位置后台队列，23:53:42确认正式推理及17份结果落盘、无失败；[启动记录](../../RQs/RQ3_15/results/request_joint_v1/formal/launch_receipt.json)保存此时快照。保持原六臂、输入、方法与采用阈值，资格通过不代表视觉收益或解释可信度成立。

- [RQ3.14：统一事实引用与全窗口类型化比较](RQ3_14_Observed_Binding_Plan_2026-10-02.md)：九臂220 exposed eval的1980位置及详细报告已完成；预选WINDOW_VISUAL未通过采用门槛，原结果保留；[RQ目录协议](../../RQs/RQ3_14/descriptions/RQ3_14_experiments.md)。
- [RQ3.13：观测包络时间画布](RQ3_13_Observed_Excursion_Plan_2026-10-02.md)：完整840位置及详细分析已结束；[结果与失败路径](../experiment_reports/RQ3_13_Qwen_Analysis_2026-10-02.md)。A22正向开发信号、Aegis损失、图形对截图未建立增益且成本增加，不采用。
- [RQ3.12：候选条件化参考预测与视觉残差比较](../../RQs/RQ3_12/descriptions/RQ3_12_experiments.md)：v4六臂140 exposed eval完整结束；[详细报告](../experiment_reports/RQ3_12_Qwen_Analysis_2026-10-02.md)。参考可计算性未建立诊断价值，主要门槛未通过，不采用；旧失败、准备与提交记录保留。
- [RQ3.11：数值保护视觉压缩](CanvasRCA_RQ3_11_Protected_Compression_Plan.md)：整批结束，[完整报告](../experiment_reports/RQ3_11_Qwen_Analysis_2026-10-01.md)不支持采用预选HIGH或成本收益；保留历史协议。
- [RQ3.7：数值证据与实体关系的受控视觉融合](CanvasRCA_RQ3_7_Research_Plan.md)：扩量及已暴露test已完成，实际支持与限制见[RQ3.7C/RQ3.8报告](../experiment_reports/RQ3_7C_RQ3_8_Qwen_Analysis_2026-09-30.md)，不沿用早期“尚未启动”状态。
- [RQ3.6：定位修复与破坏，保留有效诊断能力](CanvasRCA_RQ3_6_Research_Plan_2026-09-26.md)：原计划保留历史；实际完成阶段与机制结果以[最新报告](../experiment_reports/RQ3_6_Mechanisms_Analysis_2026-09-28.md)为准，不再沿用早期“尚未启动”的状态。

## 历史计划

| 文件 | 用途与状态 |
|---|---|
| [2026-09-25 RQ3.5计划](CanvasRCA_RQ3_5_Research_Plan_2026-09-25.md) | A/B screen已完成，见对应报告；未执行的J扩量与视觉分支保留历史登记，不再自动作为下一步 |
| [2026-09-15 总体研究计划](CanvasRCA_Research_Plan_2026-09-15.md) | Contrast 路线及 RQ3.1 的研究背景；保留历史，不代表当前执行进度 |
| [2026-09-20 RQ3.2 计划](CanvasRCA_RQ3_2_Research_Plan_2026-09-20.md) | SignalCover 路线；实际结果见 RQ3.2 报告 |
| [2026-09-22 下一步计划及后续更新](CanvasRCA_Next_Research_Plan_2026-09-22.md) | 包含 RQ3.3 Witness、RQ3.4 综合实验的多次更新；其中运行状态为写作当时的历史记录，完成状态以对应报告为准 |

2026-09-25 整理说明：只移动 docs 中的计划、报告及其配套资源，并修正搬迁所需的相对路径。旧地址保留为相对符号链接，避免历史协议和引用失效；不是另一份内容副本。`docs/issues/` 等其他内容保持不变。没有删除历史实验结论，也没有改写原结果。


## 2026-10-02 — RQ3.12完整分析

840终态，811formal调用/801响应/10超时，18smoke。801完整graph和评分、140公开compiler parity、94冻结源/3附加runtime、实际transport及token守恒审核通过；离线operand接口修复限定report，不改变原输入/答案/分数。主要CV−ET+.0384/CV−CT+.0365/CV−OV−.0275，pH均.5671，成本+9.06%，不采用CV。参考竞争104/120但目标真实变化23/120、精确root目标0/预测行2。36case/216位置214解释阅读，未知轴保留，不宣称信任增益。报告docs/experiment_reports/RQ3_12_Qwen_Analysis_2026-10-02.md。用户授权继续结果驱动新plan/实施/全部资格及启动完整队列，single primary。

- [2026-10-02 RQ3.13 observed excursion plan](RQ3_13_Observed_Excursion_Plan_2026-10-02.md)：该计划写作时停在smoke；后来用户授权的完整队列及详细分析已结束。当时的下一步是设计RQ3.14；当前状态以本页顶部的最新条目为准。
