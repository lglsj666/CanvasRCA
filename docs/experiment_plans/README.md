- [RQ4.9: organization, compression and attention](RQ4_9_Dashboard_Organization_Compression_and_Attention_Plan_2026-10-21.md): 23 conditions / 6,000-call ceiling; full 220-case CPU and three GPU smokes passed; formal 5,850-position queue launched. [Current findings](../../RQs/RQ4_9/findings/exp_organization_findings.md).

- [2026-10-22 RQ4.10: evidence domain, outside context and glyphs](RQ4_10_Evidence_Domain_Context_and_Glyph_Plan_2026-10-22.md) — 20新臂，5700调用上限；本次仅实施与静态。纯视觉完整标注基准v2已获用户批准；CPU/GPU未运行。

2026-10-20 **RQ4.7按用户要求删除三个M臂的全部实验数据与结果，仅保留S条件。** 设计文件和代码保留原协议；输入输出、对话、attention、统计与图表均按实际保留范围更新。原完整运行入口退役，不自动重建已删除条件。[设计](RQ4_7_Source_Bound_Visual_Workspace_Plan_2026-10-20.md) · [保留S报告](../experiment_reports/RQ4_7_Qwen_Analysis_2026-10-20.md) · [状态](../../RQs/RQ4_7/findings/exp_source_workspace_findings.md)。以下保留历史记录。

- [RQ4.8: card selection, hybrid recovery and valid QA](RQ4_8_Card_Selection_Hybrid_Recovery_and_Valid_QA_Plan_2026-10-20.md): implementation and CPU qualification in progress; tolerant QA/card receivers and multi-value half credit registered; no GPU/formal calls yet.

2026-10-20：原 `docs/issues/` 已归并至 [综合问题与历史解决方案](../../important_docs/general_issues.md)，原目录已删除；下方历史路径和状态按当时记录理解。

2026-10-19 **RQ4.6 全2,620位置与详细分析完成。** 2,601真实正式调用＋19引用，另18smoke；H_MARGINAL_PHASE标准MRR0.4590，总token较旧H_MARGINAL下降39.20%，MRR下降0.0322，主要损失在AegisLab。纯视觉最高新臂NEIGHBOR0.3436未超过历史U0.3517；三个预选方法未达排名目标。含完整配对统计、QA原回答审查、重复和716份attention分析。自动存储精简失败，正式结果完整，归档尚未合规；无新模型调用或后继启动。[完整报告](../experiment_reports/RQ4_6_Qwen_Analysis_2026-10-19.md) · [计划](RQ4_6_Pod_Bound_Relation_Join_Plan_2026-10-19.md) · [唯一状态](../../RQs/RQ4_6/findings/exp_pod_join_findings.md)。

2026-10-19 **RQ4.5 本地完整实验与详细分析已完成。** 1560/1560位置、1538正式实际调用+22引用，另18次本地smoke；H_MARGINAL标准MRR 0.4912、对历史强文本总token下降5.97%，两个AIOPS仍退化。预选组合0.4736、来源内均匀纯视觉0.3105，均未达推进目标；含完整统计、QA回答与412份正式attention分析。[最终报告](../experiment_reports/RQ4_5_Qwen_Analysis_2026-10-19.md) · [唯一状态](../../RQs/RQ4_5/findings/exp_exclusive_spatial_findings.md)。以下保留历史检查点。

2026-10-19 **RQ4.5 本地正式队列已启动并确认实际提交结果。** 本地完整 CPU 回归通过（32 单测、220例/1320 RCA输入、33例 QA输入、30运行探针）；18/18 GPU smoke 完成并审查通过。沿用 RQ4.4 Blackwell 原生配置，在线 smoke 速度9.94 calls/min（含启动5.15）；正式队列1560个位置，支持原子提交恢复。Nibi资格任务继续排队，未启动Nibi正式实验。[计划](RQ4_5_Exclusive_Modality_Spatial_Pruning_Plan_2026-10-18.md) · [本地启动核验](../../RQs/RQ4_5/findings/local_formal_launch_20261019.json) · [唯一状态](../../RQs/RQ4_5/findings/exp_exclusive_spatial_findings.md)。

Historical Nibi CPU checkpoint (not current execution status):

2026-10-19 **RQ4.5 全部 CPU 资格通过并冻结；GPU 未运行。** 27 单测、220例/1320 RCA请求、33例/198 QA输入、30运行探针、传输不变性与重绘均通过；新模型调用0。历史基线复用，Codex 未改。[计划](RQ4_5_Exclusive_Modality_Spatial_Pruning_Plan_2026-10-18.md) · [CPU报告](../experiment_reports/RQ4_5_CPU_Qualification_2026-10-19.md) · [唯一状态](../../RQs/RQ4_5/findings/exp_exclusive_spatial_findings.md)。

2026-10-12 **RQ4.4 840/840正式位置完成，858次实际调用含smoke；完整详细分析已交付。** SOURCE标准/宽容MRR为0.3286/0.3431，未超过历史U，成本为其2.409倍；两项主要比较均未建立收益，局部高清候选按登记结束。QA定位、理由一致性及270份正式attention完成离线审核。[最终报告](../experiment_reports/RQ4_4_Qwen_Analysis_2026-10-12.md) · [计划](RQ4_4_Source_Bound_Multiscale_Plan_2026-10-12.md) · [历史复核](RQ4_4_History_and_Implementation_Review_2026-10-12.md) · [部署报告](../experiment_reports/RQ4_4_GPU_Qualification_2026-10-12.md) · [唯一状态](../../RQs/RQ4_4/findings/exp_source_views_findings.md)。

- [RQ4.3 直接可读保留、HTML 对照与八臂恢复](RQ4_3_Direct_Retention_and_Arm_Restoration_2026-10-11.md)：HTML CPU/GPU 与八臂完整 CPU 已通过；v17 共 4,832 位置已恢复并监控通过。

# 实验计划

2026-10-11 **RQ4.3 v8 X_SRP已恢复并进入正式队列**：28项CPU回归及220例审核通过、0实现错误；R/P适用42/60、57/60、84/100。只新增unified组件，旧组件及Codex未改；用户豁免新增GPU smoke。总2632位置，新增183请求＋37精确引用，原133个完成记录保留后恢复。[修复计划](RQ4_3_X_SRP_Repair_v8_2026-10-11.md) · [CPU资格报告](../experiment_reports/RQ4_3_X_SRP_CPU_Qualification_v8_2026-10-11.md)。以下保留历史检查点。


2026-10-11 **RQ4.3 v7存活队列已启动**：22项CPU回归与18/18 GPU smoke通过；GPU用时481.95秒，2条无效回答按原协议计零，无基础设施错误。2412正式新位置，启动监控进行中。R及预选X_SRP仍取消，历史依赖推断受限。[实时状态](../../RQs/RQ4_3/findings/exp_selection_rendering_processing_findings.md)。

2026-10-11 **RQ4.3 v7：九个存活条件及测量CPU资格通过，原R/X预选候选按登记取消；尚无新模型结果。** 2412开发位置＋18smoke＋234恢复＝2664。历史基线不重跑，历史依赖推断受限。[v7方案](RQ4_3_Selection_Rendering_Processing_Plan_v7_2026-10-11.md) · [CPU报告](../experiment_reports/RQ4_3_CPU_Qualification_v7_2026-10-11.md)。下方是历史检查点。

2026-10-11 **RQ4.3 v6 布局修订及 S/P CPU 阶段已完成；完整 CPU 仍未通过。** 用户允许改变换行/卡片尺寸；220例S/P来源与440张S图审核0错误，18项当前单测及220例提示/X_SP几何复核通过。R三例重排装入原画布预算，但锚点7306/5895/7206仍超过K5332/4784/5444。按登记取消两项重复S条件，当前分配5988/8000；GPU和新增模型调用0，Codex未改。[新版计划](RQ4_3_Selection_Rendering_Processing_Plan_v6_2026-10-11.md) · [详细CPU进展](../experiment_reports/RQ4_3_CPU_Progress_2026-10-11.md) · [唯一状态](../../RQs/RQ4_3/findings/exp_selection_rendering_processing_findings.md)。以下保留历史检查点。

2026-10-10 **最新：RQ4.3 第一阶段 CPU 审核完成，220/220 无运行错误；R 固定卡片可读性门槛失败，完整 CPU 未通过。** 静态及六项前置回归通过。18px 与固定卡片/原换行不兼容：AIOPS-2022 60/60、AIOPS-2025 17/60、AegisLab 69/100。S/P完整资格仍待完成；GPU和正式调用为0，Codex未改。[CPU报告](../../RQs/RQ4_3/results/cpu_feasibility_v1/CPU_Prerequisite_Report.md)。下述“尚未实施”是此前规划检查点的状态。

2026-10-10 **RQ4.3四轮独立评审完成，v5定稿；尚未实施或做CPU/GPU资格。** gpt-6-astra／xhigh准备度依次6.7、7.6、8.1、8.1；后两轮无新增设计阻塞，第五轮未使用。九优化／七控制／四组合，预选X_SRP不变；开发及测量5216、条件验证1080、smoke18、恢复234，合计6548／8000，1452未分配。历史基线复用，新增实验调用0，Codex未改。[最终方案](RQ4_3_Selection_Rendering_Processing_Plan_v5_2026-10-10.md) · [技术合同](RQ4_3_Blind_Review_2026-10-10/technical_contract_v5.md) · [四轮原始评审与处置](RQ4_3_Blind_Review_2026-10-10/README.md)。

2026-10-10 历史规划检查点（已被v4替代）：**RQ4.3 v2 扩展为选择／画法／内部处理各3个优化臂，旧弱效方案不作小改重跑。** 自查后补入背景名额分配与全局双向两个控制，现为7控制＋4个固定组合；正式新位置5,108，含smoke和恢复明确分配5,360。总上限8,000，2,640未分配；九个优化条件和预选组合不变。历史U／T_FULL／MARGINAL_FIVE复用；独立方案评审进行中，代码、CPU、GPU尚未开始。[历史v2](RQ4_3_Selection_Rendering_Processing_Plan_v2_2026-10-10.md) · [实质改动与去重](RQ4_3_Selection_Rendering_Processing_v2_assets/revision_and_novelty.md)。

2026-10-10 历史初稿：**RQ4.3 来源内双向视觉预填充初稿已落盘，当时尚未实施或资格测试。** 从历史最强纯视觉 A_UNIFORM_E50 出发，三个优化条件＋三个必要控制；当时拟议新调用上限 1,700，后由上方v2替代。已复核 important_docs、历史报告、Codex 及跨领域论文；没有新盲审或新增模型调用。[旧初稿](RQ4_3_Source_Local_Visual_Prefill_Draft_2026-10-10.md) · [阅读与去重附件](RQ4_3_Source_Local_Visual_Prefill_Draft_2026-10-10_assets/review.md)。

2026-10-09历史检查点：**RQ4.2 当时已完成正式运行器及关机恢复部署，资格 READY，正式尚未启动。** 新增18项受影响CPU测试通过，原CPU/GPU通过项继续有效；该次0模型调用。[报告](../experiment_reports/RQ4_2_Formal_Readiness_2026-10-09.md) · [恢复协议](../../RQs/RQ4_2/descriptions/RQ4_2_Formal_Recovery_2026-10-09.md)。最终完成状态见下条。

2026-10-10 最新：**RQ4.2 正式实验及最终分析完成，SEM 未达到采用目标，按登记结束候选。** 1,336 位置完整、无基础设施未知；五臂 MRR 为 FULL .2841、GEOM .3088、SEM .3084、SHAM .3011、NATIVE4 .3235。来源分组未超过空间分组或历史纯视觉强基线，成本/QA/attention 及解释边界详见 [最终报告](../experiment_reports/RQ4_2_Qwen_Analysis_2026-10-10.md) 和 [唯一状态](../../RQs/RQ4_2/findings/exp_partition_findings.md)。历史 T_FULL、MARGINAL_FIVE 复用比较，没有重跑；没有自动启动下一轮。以下为历史检查点。

2026-10-09 历史检查点：**RQ4.2 CPU及GPU受影响路径资格通过，正式未启动。** 新增5轮×18机会中仅使用第1轮2调用，继承16条记录，原18位置覆盖完整。首次超时仍保留失败；后续formal入口部署需另行授权。[补测报告](../experiment_reports/RQ4_2_GPU_Smoke_Supplement_2026-10-09.md) · [当前状态](../../RQs/RQ4_2/findings/exp_partition_findings.md)。

2026-10-09方向建议：**RQ4.2拟检验编码前的完整视觉比较编译，尚未完整预注册或实施。** 正常紧凑图为主对照，BOUND为拟议候选；三新条件与小规模机制/桥接建议≤900调用。先CPU可行性再登记，当前0新增调用；独立论文先行评审的OpenReview评论访问受限已披露。[方向建议](RQ4_2_Pure_Visual_Compilation_Recommendation_2026-10-09.md)。

2026-10-09最新：**RQ4.1正式实验和详细分析完成，当前CVC候选按登记收官。** 6,100位置全部终态（6,082回答＋18不适用）；纯视觉预选MRR0.3332低于强文本0.4846/0.4861，尽管总token下降73.69%。正确依赖机制未建立，位置敏感性显著；QA有效性问题与attention测量边界分别报告。条件独立确认仍未运行，没有追加实验或自动采用事后最高臂。[完整分析](../experiment_reports/RQ4_1_Qwen_Analysis_2026-10-09.md) · [唯一findings](../../RQs/RQ4_1/findings/exp_comparison_coding_findings.md)。

2026-10-07历史检查点：**RQ4.1正式实验已按用户授权启动，超过三分钟启动监控正常。** 6100个登记位置，预计6082次实际调用，后台继续运行；不重跑资格、不改队列、不按临时MRR调参。[当前状态](../../RQs/RQ4_1/findings/exp_comparison_coding_findings.md) · [实时进度](../../RQs/RQ4_1/results/comparison_coding_v1/formal_v28/summary.json)。

2026-10-07此前：**RQ4.1正式运行器及新配方部署资格通过，正式未启动。** 用户接受attention与全量时间开销；保留旧CPU资格，新增两轮共24次调用完成。配置启动错误已在原第二窗内修复；GPRUNE一次非法候选、QA及解释错误如实保留。启动凭据仍关闭，等待后续指令。[唯一当前状态](../../RQs/RQ4_1/findings/exp_comparison_coding_findings.md) · [部署报告](../../RQs/RQ4_1/results/comparison_coding_v1/deployment_v28/report.md)。

2026-10-06历史检查点：**RQ4.1本轮220例来源、实际processor和共享支持审核通过；完整CPU准入仍未完成。** 修复时间箱阶段、耗时统计标签及LOG-R单位/分数角色；31项RQ和35项renderer回归通过。新版全量真实特征/mask及部分运行路径待资格，纯CPU编码单例600秒未完成。统计压力校准触发警报，条件独立确认不运行。本次GPU工作和LLM调用均为0，smoke/formal关闭。[唯一当前状态与全部证据](../../RQs/RQ4_1/findings/exp_comparison_coding_findings.md)。

2026-10-06此前：**RQ4.1旧grid50饱和已在三个真实特征病例确认，证据预算CVC_E50修复已落盘。** 三例依赖mask由相同变为不同，静态与25项CPU回归通过；仅3次视觉编码前向，新增LLM调用0。全220资格及GPU smoke未完成；新版代理仍接近1，不能声称MRR收益。 [唯一结论与证据](../../RQs/RQ4_1/findings/exp_comparison_coding_findings.md)。

2026-10-06此前执行更新：**RQ4.1共享支持修订完成，静态、22项单测及220例非空支持审核通过；完整CPU资格仍待完成，GPU smoke未运行。** 一个token可支持多个字段，预算只计一次。全部220例的登记支持能放入50%预算，需核验实际依赖对照是否仍有区别，不能以修复通过替代完整资格。宽/高各8192，图像不变；新增模型调用0，旧12次探针与独占归属失败均保留。[唯一状态与详细证据](../../RQs/RQ4_1/findings/exp_comparison_coding_findings.md)。


2026-10-06规划时状态（执行更新见上）：**RQ4.1核心计划完成六轮独立盲审并定稿，当时未实施。** 主线为renderer公共比较依赖引导的纯视觉token分配，另留一个CONTRAST_ATLAS探索臂。22条件，登记总上限8,900（含已用12），用户总上限12,000，3,100未分配。第六轮84/100、整体7.6/10；评分不是效果或执行资格。[正式计划](../../RQs/RQ4_1/descriptions/RQ4_1_experiments.md)；[唯一状态](../../RQs/RQ4_1/findings/exp_comparison_coding_findings.md)；[全部评审记录](../../RQs/RQ4_1/results/planning_review_v1/review_process.md)。

2026-10-06：**RQ4.1 真实 Qwen 视觉 token 接口小测试完成，12/12。** 原生与全部 embedding 手动注入逐 token 等价，约 1/2、1/4 裁剪均能生成；强裁剪已有实体读错。只确认模型级可行性，vLLM 尚未接入，MRR 未测。10,000 次总上限已用 12，此条记录为探针完成时状态，后续计划见顶部，GPU 进程当时已退出。[原始登记协议](../../RQs/RQ4_1/results/token_interface_probe_v1/source_snapshot/RQ4_1_experiments.md)；[实测报告](../../RQs/RQ4_1/findings/exp_token_interface_probe_findings.md)。

2026-10-06：RQ3.22 已按用户要求整体删除（方案、代码、CPU/smoke 和例图），未启动正式实验。当前没有可恢复的 RQ3.22 资格或运行；后续从 **RQ4** 开始，方法改为纯视觉诊断证据，任务/读图/格式说明仍用文本。[RQ4 当前路线](../../RQs/RQ4/descriptions/RQ4_roadMap.md)。

2026-10-06 **RQ3.21全量已结束并完成最终分析，预选紧凑实体视觉方法不采用。** 2020位置终态，1767新返回、241引用、12超时；含35关机中断及18smoke共1832次尝试。CV MRR0.4180，较历史锚点−0.08742；token下降16.3%–17.7%但未保持排名。位置扰动显著超过独立重复噪声，阶段比较受损；完整绝对指标、成本、失败分母和解释核验已落盘。没有新实验或attention启动，自有GPU关闭。[最终报告](../experiment_reports/RQ3_21_Qwen_Analysis_2026-10-06.md)；[唯一状态](../../RQs/RQ3_21/findings/exp_compact_entity_findings.md)。以下CPU、启动与恢复信息均为历史记录。

2026-10-06 **RQ3.21 GPU smoke 18/18通过，已按用户新授权启动正式后台任务。** 实际输入/PNG、输出、评分、token与原子提交完整审核通过，累计smoke含启动环境修复及审核407.99秒；显存0.75、并发36、attention关闭。六个新主臂加机制/重复共1800新位置，另220历史锚点引用；预计1779次正式新生成。首批新提交核验通过，13:58:47 UTC快照13新完成、36在途；本次完成启动后停止操作，不提前评价MRR。[资格与启动记录](../experiment_reports/RQ3_21_Qualification_and_Launch_2026-10-06.md)；[唯一状态](../../RQs/RQ3_21/findings/exp_compact_entity_findings.md)。以下CPU后停止条目保留其历史时点含义。

2026-10-06 **RQ3.21代码、静态、完整220例CPU与实际例图审核已完成，按用户要求停止。** 六个新主臂＋60例机制/重复；历史ANCHOR复用220结果，取消PACK_TEXT/ENTITY_TEXT，新正式位置1800，总尝试上限1940。预选方法完整输入对历史锚点减少16.35%–17.82%、对RAW_TEXT减少13.32%–14.32%；没有新MRR或总生成成本结论。GPU smoke和正式均未启动，执行凭据未生成。[当前计划](RQ3_21_Compact_Evidence_Entity_Organization_Plan_2026-10-06.md)；[CPU资格报告](../experiment_reports/RQ3_21_CPU_Qualification_2026-10-06.md)；[唯一状态](../../RQs/RQ3_21/findings/exp_compact_entity_findings.md)。

2026-10-06 UTC **RQ3.20 v3 核心已完成，当前候选按登记结束。** 1520流程全部终态，1476次累计实际尝试含smoke；完整结果审核通过。V相对F配对MRR−0.0696且显著下降，已知配对总token节省16.86%；大规模选择ID接口失败及有限明细空间已定位。QA辅助改善没有可靠转化为排名收益。未启动SIRCL、独立90例或attention，不自动追加新臂。[完整报告](../experiment_reports/RQ3_20_Qwen_Analysis_2026-10-06.md)；[唯一findings](../../RQs/RQ3_20/findings/exp_budgeted_acquisition_findings.md)。以下启动/CPU失败条目是历史时点记录。

2026-10-05 **RQ3.20 v3 已通过资格并启动全量核心。** 用户只把首轮完整输入门槛调至50%，两轮85%预算保持。实际合格58/60、52/60、84/100；静态、完整CPU及GPU smoke通过（16次真实调用，1项QA不适用、1次同请求引用，0基础设施错误）。全量1,520流程位置、最多2,200调用，GPU0.75/并发36；attention关闭，条件模块未启动。[资格与启动报告](../experiment_reports/RQ3_20_Qualification_and_Launch_2026-10-05.md)；[当前唯一状态](../../RQs/RQ3_20/findings/exp_budgeted_acquisition_findings.md)。下方40%失败为历史状态。

2026-10-05 **RQ3.20 v2 压缩修订已完成CPU审核，完整视觉预算仍未通过。** 按用户新指示直接修改RQ3.20，原40%/85%/各集50%门槛不变。命名列、共享字段、窗口引用和有向关系分组使文本首轮减少20.45%–29.48%，文本可行60/60、56/60、100/100；计入216张实际统一renderer图片后共同可行0/60、1/60、0/100。220例事实反解与实际整包回归通过，历史v1材料完整保留。新增调用0、GPU未启动。[改动登记](../../RQs/RQ3_20/descriptions/compression_revision_v2.md)；[唯一当前报告](../../RQs/RQ3_20/findings/exp_budgeted_acquisition_findings.md)。下方v1停止说明保留历史时点含义。

2026-10-05 **RQ3.20 已在第一阶段 CPU 预算门槛停止，新增模型调用0。** [视觉引导的预算化取证计划](RQ3_20_Budgeted_Visual_Evidence_Acquisition_Plan_2026-10-05.md)及CPU实施已保存；静态和已实现接口回归通过，220例来源及真实processor审核完成。文本必要条件给出的最终合格上界仅A22 0/60、A25 0/60、Aegis 16/100，均不足50%；0.40/0.85预算保持原样。GPU smoke、正式实验、QA和attention均未进入。下游运行器未作为已完成实现交付。[唯一报告与状态](../../RQs/RQ3_20/findings/exp_budgeted_acquisition_findings.md)。这是当前设计的预算失败，不是新的MRR负结果。

2026-10-05 **当前最终状态：RQ3.19核心1480位置终态，详细分析完成；预选视觉替换V不采用，按登记结束候选。** 1449真实返回＋18引用＋13超时，5模型无效保留零分；含smoke实际1480次调用。F/C/A/V MRR .4562/.4308/.4569/.4139，V−F配对−.0450、完整分母差值界限仍为负，成本没有下降。机制线得到视觉QA受辅助后显著提升（+5.46个百分点，pH .000381），但未建立可靠RCA组织收益，天花板/题目相关性/解释错误边界均已报告。[完整报告](../../RQs/RQ3_19/findings/exp_visual_replacement_qa_findings.md)；[完成日志](../../RQs/RQ3_19/results/visual_replacement_qa_v2/logs/2026-10-05_final_analysis.md)。自有GPU服务关闭，attention、SIRCL与扩展验证未启动；没有自动追跑最高分臂。3,000是上限，不是需要消耗完的队列。冻结[双线计划](CanvasRCA_Dual_Track_Next_Stage_2026-10-05.md)保留登记时内容；[资格与启动报告](../experiment_reports/RQ3_19_Qualification_and_Launch_2026-10-05.md)是历史快照，不能继续读作当前正在运行。

2026-10-05 研究收敛补充：[五个重要反直觉现象](../../important_docs/CanvasRCA_Counterintuitive_Findings_2026-10-05.md)。QA 到 RCA 的任务相关性是下面表示分配候选的前置缺口；该候选尚未确定为下一算法。已有数值写法翻转值得优先复核，标题 attention 保留为机制线索；按用户要求补入完整文本加图退化及文本接口敏感性，分别用于研究证据干扰与控制接口差异。不新增布局消融或 attention 采集，不改变 RQ3.18。

2026-10-05 最新研究目标：[从优秀实证到预算受控的新方法](../../important_docs/CanvasRCA_Empirical_to_Method_2026-10-05.md)。将MRR约0.60与实际成本最多增加5%联合考虑；完成历史报告去重及[实证论文/最近工作复核](../../important_docs/CanvasRCA_Empirical_Literature_Review_2026-10-05.md)。提出以实际联合读取错误指导文字/图像分配的单一候选，2,880调用仅为后继资源草案、未授权注册或启动；RQ3.18冻结运行不变。历史RQ3.16成本重算保留正向信号与原采用限制。

2026-10-05 项目安排：[WWW 2027 投稿冲刺与研究收敛](CanvasRCA_WWW2027_Submission_Sprint_2026-10-05.md)。10月7日方法/主张决策截止，10月16日摘要、23日全文内部交付；先补强文本对照、技术新意、数据曝光与冻结验证证据。RQ3.18按原协议继续，本安排不修改其阈值、矩阵、源或预算，不自动启动后继实验。

2026-10-05 最新执行状态：**RQ3.18 全2420位置终态，详细分析已完成；预选总体读数候选未通过采用，按登记结束。** 2328真实返回、63引用、29超时；FP MRR .4877，FP−F +.0220但校正未通过、Aegis退化及重复方向失败。自有GPU服务关闭，无后继实验自动启动。[完整报告](../../RQs/RQ3_18/findings/exp_population_readout_findings.md)；[执行历史](../../RQs/RQ3_18/results/population_readout_v1/logs/2026-10-04_gpu_and_formal_execution.md)。

- [RQ3.18：总体耗时读数与视觉比较](RQ3_18_Population_Readout_Plan_2026-10-04.md)：旧六臂方案按用户要求删除；新11臂/2420位置已完成，共2375次尝试含18smoke，保留29超时及10模型无效零分。静态、完整CPU、实际例图及GPU资格通过；**预选方法不采用，等待新指示**。[完整报告](../../RQs/RQ3_18/findings/exp_population_readout_findings.md)；[历史CPU资格](../../RQs/RQ3_18/results/population_readout_v1/qualification/report.md)；[例图](../../RQs/RQ3_18/preparation/population_readout_v1/examples/index.html)。冻结计划内的“CPU后停止”保留为其登记时状态，不改写历史授权。

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

2026-10-03最新状态：**[RQ3.16：边际图元与候选覆盖](RQ3_16_Marginal_Coverage_Plan_2026-10-03.md)计划、代码和资格已完成，并按用户要求停止。** 八臂同证据/输出容量受控比较；静态、完整220例CPU、实际图像及18/18 GPU smoke通过，自有服务关闭。[资格问题汇总](../../important_docs/general_issues.md#r39)和[实际例图库](../../RQs/RQ3_16/results/marginal_coverage_v1/qualification/gallery/index.html)已落盘。正式1,760位置仅登记，正式调用0、启动权限关闭。它是新开发假设，不能将RQ3.15最高均值或smoke通过追认为已证实视觉收益；下列RQ3.15结论保持不变。

2026-10-03最终状态：**RQ3.15正式矩阵及详细分析已完成，预选方法不采用，按原计划停止此机制路线。** 11:42:16 America/Toronto完成1320终态；1279真实响应、36引用、5超时，自有服务关闭。[详细报告](../experiment_reports/RQ3_15_Qwen_Analysis_2026-10-03.md)给出全部指标、成本、统计和机制分析。V−PAIR_TEXT+.0281，但V−MARGINAL−.0134；Aegis对BASE+.0007，主要病例/事件组Holm均不显著。不得据此自动改布局、改用最高均值臂、消耗剩余调用或启动后继实验。RQ3整体研究目标仍未达成。

以下启动、暂停、恢复与资格状态均为历史时间点，不是当前运行状态。

2026-10-03恢复历史：10:50:22启动、10:53:42 America/Toronto核验。恢复队列沿用已有822个终态位置，继续其余498个位置；核验时累计804份响应（10份新增）、36次在途，无新增失败，旧调用未重复提交。原输入、预算和显存利用率0.75保持不变。[恢复记录](../../RQs/RQ3_15/results/request_joint_v1/formal/resume_receipt.json)保存当时的运行快照。

2026-10-03 01:10:34 America/Toronto：**RQ3.15已按用户要求安全暂停**。没有新增提交；36个在途请求全部正常收尾，794份真实响应已提交，模型服务及进程全部退出、端口关闭。不自动恢复，须等待用户明确授权。当前状态见[暂停记录](../../RQs/RQ3_15/results/request_joint_v1/formal/pause_request.json)，下列启动信息为历史。

- [RQ3.15：同请求连续耗时关系](RQ3_15_Request_Joint_Plan_2026-10-02.md)：代码、220例CPU资格及18次GPU smoke均通过；[资格问题汇总](../../important_docs/general_issues.md#r38)。用户随后明确授权全量实验，已于2026-10-02 23:49:54 America/Toronto启动1320位置后台队列，23:53:42确认正式推理及17份结果落盘、无失败；[启动记录](../../RQs/RQ3_15/results/request_joint_v1/formal/launch_receipt.json)保存此时快照。保持原六臂、输入、方法与采用阈值，资格通过不代表视觉收益或解释可信度成立。

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

- [RQ4.3 v9八路并发与加速](RQ4_3_Concurrency_v9_2026-10-11.md)：功能smoke通过，CPU重跑豁免；利用率目标未达到，正式暂停。

- [RQ4.3 v11宿主核隔离修复](RQ4_3_Scheduling_Repair_v11_2026-10-11.md)：保持8 CPU/8 GPU和RAM预取；队列及模型计算不变。
