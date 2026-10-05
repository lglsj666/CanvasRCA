# RQ3.15：同请求连续耗时关系的受控视觉验证

2026-10-03最终状态：**正式矩阵及详细分析已完成；预选PAIR_VISUAL未通过采用门槛，执行本计划的停止条件。** 全1320位置终态（1279真实响应/36引用/5超时），自有服务已关闭。V−PAIR_TEXT+.0281、V−MARGINAL−.0134；V−BASE AIOPS+.0424、Aegis+.0007，主要比较病例与事件组Holm均不显著，Aegis最小收益未达到。[详细报告](../experiment_reports/RQ3_15_Qwen_Analysis_2026-10-03.md)及[最终findings](../../RQs/RQ3_15/findings/exp_request_joint_findings.md)记录完整结果和解释边界。停止该连续配对视觉路线，不自动继续调布局、选最高均值臂或启动后继实验。下列授权与运行信息保留为历史快照；原科学设计和采用标准未改变。

2026-10-03最新执行授权：用户明确要求“帮我重启实验吧。”，解除下述暂停边界。10:50:22 America/Toronto启动同一冻结矩阵的剩余任务，10:53:42确认恢复运行：804份响应已提交，其中10份为恢复后新增，36次在途，无新增失败。资格及源码一致性核对通过，队列跳过原822个终态位置，仅继续498个待完成位置（486次真实推理＋12个复用位置）；原794份响应、4个已有超时和历史花费完整保留，无重复提交旧调用。[恢复记录](../../RQs/RQ3_15/results/request_joint_v1/formal/resume_receipt.json)保存核验快照。保持原模型、输入、评分、采用门槛、预算及显存利用率0.75，不自动启动下一实验。

2026-10-03最新执行边界：**已按用户要求安全暂停**。01:06:58 America/Toronto发送暂停信号后没有新增提交，36个在途请求全部正常收尾；01:10:34确认本次runner、supervisor、模型服务与engine全部退出、端口关闭。794份真实响应和24个复用位置已提交，4个此前超时位置原样保留，498个位置待完成。保留全部结果、失败记账及原预算；在用户明确要求恢复之前，不得重新启动模型、推理或自动监控。以[暂停记录](../../RQs/RQ3_15/results/request_joint_v1/formal/pause_request.json)为当前状态；下面的正式启动授权保留为历史。

2026-10-02 最新执行授权：用户明确要求“那就启动全量实验吧”。完整 CPU、实际例图审查和18次GPU smoke均通过后，现授权运行已冻结的220例×6臂正式矩阵。此前“smoke后停止”的限制已履行，本次仅解除执行限制；以下原方案中的“仅登记／只授权smoke”保留为当时的历史边界，不改变科学设计、输入、评分、统计阈值或预算。单一主agent，不开展自动后续方法搜索。实际运行状态见[RQ3.15 roadMap](../../RQs/RQ3_15/descriptions/RQ3_15_roadMap.md)。

正式授权通过独立[执行记录](../../RQs/RQ3_15/results/request_joint_v1/qualification/activation_v1/full_authorization.json)绑定原注册、配置和当前源码。仅修改`qualified_contract`和`full_authorized`两个执行资格函数；原资格报告及冻结归档不改写，其他AST、176文件集合和全部科学依赖一致性已核验。[激活检查](../../RQs/RQ3_15/results/request_joint_v1/qualification/activation_v1/activation_review.json)通过，无新增smoke调用。已于2026-10-02 23:49:54 America/Toronto提交后台启动，状态以[启动记录](../../RQs/RQ3_15/results/request_joint_v1/formal/launch_receipt.json)为准。

原实施授权：2026-10-02批准代码、完整CPU回归、实际例图审查、GPU smoke，通过后停止。该阶段已完成；计划本身不作为完成证据。

## 1. 主线与依据

保留有效诊断证据，让视觉承担明确的比较任务，并证明其在强文本基础上提高根因排名。先验证视觉收益，再研究压缩降本。RQ3.14 视觉对同摘要强文本配对 ΔMRR=-0.0523，冻结 WINDOW_TEXT 为基础；RQ3.3/3.5 已测试请求分组和二值联合证据。本轮只验证二值化丢失的同请求连续耗时关系，不把联合比较本身当作创新。

假设：同次调用的父子连续耗时关系可能帮助区分共同变慢与某端单独变慢，二维联合图可能比强文本和单变量图更适合这一比较。相关关系不证明根因，不计算跨主机等待/关键路径/本地执行耗时。CRISP 的时钟偏差限制支持这一边界，而非本方法的 MRR 保证：[USENIX ATC 2022](https://www.usenix.org/conference/atc22/presentation/zhang-zhizhou)。图表感知与 RCA 排名分别评价：[Findings EMNLP 2025](https://aclanthology.org/2025.findings-emnlp.573/)。

## 2. 公共编译与适用性

完整保留 RQ3.14 WINDOW_TEXT 的 M/R/L/G、摘要、候选与任务。从 canonical V3 白名单 Trace 列读取实际父子 span，同 trace 内唯一身份连接，不按名称或时间猜边。使用来源核实的 duration 单位转换。每请求、每父实体/操作先选择最长父调用，再选它对应子实体/操作的最长直接子调用；缺子调用不置零。阶段由父调用按既有公共窗口划分，不使用注入时间。

每关系每阶段至少20请求。按 abs(log1p(current parent p95_ms)-log1p(reference parent p95_ms)) 降序，实体/操作标识破并列，最多两关系。每阶段按父耗时排序等距抽取最多32个实际秩位置，包含端点，不插值。展示总体支持量，明确图中为样本。文本提供完全相同的样本数值、总体二值联合计数/阈值、两端分位数与有足够支持的条件耗时摘要。

完整 CPU 门槛：三个数据集分别至少50%病例合格，合格关系至少一个二值分组保留四个不同数值配对；实体映射、公共时钟、单位来源全部核对。初查18例中17例存在足量非恒定配对不是资格证据。无合格关系完整回退基础文本，保留病例与分母；图中不画缺失/空面板。

## 3. 六臂与统计

沿用220 exposed eval：A22/A25各60，Aegis100，六臂1320正式位置仅登记。

| Arm | 内容 |
|---|---|
| BASE_TEXT | 冻结 WINDOW_TEXT |
| BINARY_TEXT | BASE + 本轮配对的二值联合摘要 |
| PAIR_TEXT | BINARY + 连续配对及完整统计 |
| PAIR_VISUAL | PAIR_TEXT + 真实二维联合散点图，预选方法 |
| MARGINAL_VISUAL | 相同文本 + 两端各自分布图 |
| PAIR_REPEAT | PAIR_VISUAL 真实独立重复 |

两个视觉臂同事实/样本/色义/面积/字体，区别为二维配对关系；没有文字截图。前三者是内容比较，不冒充表示等信息比较。

四项同一主要 Holm 族：V-T全220、V-MARGINAL全220、V-BASE AIOPS120、V-BASE Aegis100。病例与事件组分别校正；Pratt-zero Wilcoxon、逐差round12、paired dz，不报告CI。次要族为PAIR_TEXT-BINARY、BINARY-BASE、REPEAT-V。完整报告绝对MRR、AC@1/3/5、AVG@3/5、pooled/macro、修复与破坏及全部失败。模型失败保留零分；基础设施未知按比较配对排除并给[0,1]缺失界限，未知usage不填0。

采用须四主要比较均正且病例/组pH<.05；V-T整体Δ≥.02，V-BASE AIOPS≥.03、Aegis≥.02；三数据集各自相对BASE和PAIR_TEXT都正。每数据集V实际input+output≤BASE1.20倍、PAIR_TEXT1.10倍，CPU先检查输入对应门槛。阈值不按smoke或部分正式分数修改。正式1320位置+42必要操作余量，smoke至多18，总1380，历史花费不重置；本次只授权smoke。

## 4. 实施与资格

RQ3_15使用五功能模块、原子提交、冻结归档、快速恢复；正式启动默认关闭。RequestPairPacketV1仅公共实体/操作/阶段/数值/抽样/统计，原始Trace身份与源行只在审计侧，明确排除anomal/标签/历史回答。

全部绘图经src/renderer。现有曲线/独占p95条形/范围矩阵不支持连续二维配对及匹配边际分布；记录此缺口后新增两个共享基础的注册组件，复用已有布局/组件替换/外观操作。两轴同尺度、明确log1p(duration_ms)，保留零和极值，精确数值在文本。历史组件语义不改，已有曲线跨缺测连接且不标记。

顺序：静态检查→数值/身份/缺失/循环/重复/单位/窗口/抽样回归→220例完整CPU适用性与actual processor预算/事实差异/恢复检查→真实PNG人工审查和确定性重绘→冻结→GPU smoke。最多8不同物理核worker，AIOPS优先不同source/cloudbed。沿用三个预定eval smoke身份，六臂至多18发起、一个600秒累计逻辑窗口；本地Qwen、40960context、8192输出适配、原解码配方、VRAM利用率0.75。逐份检查实际input/PNG/output/score/accounting，不按MRR过门禁。CPU语义/适用性/预算失败即停止候选，不放宽门槛挑病例入GPU。完成后关闭自有服务。

## 5. 停止与收官

修正计划索引中过期的RQ3.14状态，保留历史结果。交付代码、例图、适用性表和CPU/GPU资格报告。本轮是RQ3.14失败后一次实质修订；后续正式结果若仍不超过匹配强文本和图形控制，结束此路线并整理负结果，不自动换布局。RQ3目标仍要求单一部署方法、性能/可分离视觉收益、成本与可信解释证据；历史MRR目标未满足须如实记录，exposed数据不能重新命名成独立确认集。
