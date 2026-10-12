# RQ4.2：基于证据来源的视觉编码分区

登记日期：2026-10-09。用户批准实施；当前阶段状态只以 RQ4_2/findings/exp_partition_findings.md 为准。本计划不是资格通过记录。

## 主线、证据与边界

让单调用、纯视觉 RCA 超过已有强文本，并控制实际部署成本。RQ4.1 T_FULL MRR 0.4846、最佳纯视觉约 0.3517；CVC token 减少 73.69%，在线耗时只减少 3.63%。现有结果没有证明绑定错误由全局 attention 引起。本轮检验这个假设，不再扩大排版搜索或微调剪枝比例。

候选贡献是利用可审计的来源绑定，在冻结视觉编码器内组织完整诊断图元，保留全部 patch、位置和后期全局融合。分组 attention、空间窗口、局部—全局融合本身不是新发明。相关文献、历史差异和四轮评审处理见本计划的 `_assets/` 附件。第四轮认为可以冻结为有界研究，不代表方法有效或论文录用；不追加第五轮。

## 完整共同图像

继承 RQ4.1 冻结公共事实、候选、数值写法、单位、阶段、样本、日志与关系。所有诊断信息仅在 `src/renderer/` 生成的图像中；提示仅含任务、读图和输出规则。不添加文本诊断兜底。

一张主图有四个等面积区域。普通卡片宽 512px，图关系和候选目录可占区域全宽。真实 DOM 测量高度并向 32px 网格取整，完整卡片不跨区域。明确来自同一来源记录的曲线及窗口统计组成不可拆分单元；实体或数值相同不能作为合并依据。候选实体顺序、M/R/L 和原记录顺序固定，其他公共实体与全局组件稳定排序。

宽、高从 3072/4096 的组合中按面积、高度、宽度选择首个合格画布。实际 processor 处理后的诊断文字至少 18px、线条至少 1.5px，总图像 token ≤16384。审核裁切、遮挡、完整样本和来源绑定。不删事实、不缩字、不改 processor 限制。**全部 220 例无法满足共同表示要求则停止候选**，不选择可容纳病例进入 GPU。几何资格不等于模型可读性。

## 编码操作与五臂

实际 Qwen 视觉编码器有 27 块：0–22 块四组 attention，23–26 块原始全局 attention。各组 patch 数严格相同。原位置嵌入与 RoPE 随 token 一起置换；第 22 块后反置换，恢复原顺序再执行全局块和 merger。每个 2×2 merger 邻域完整。不训练、不增加模型、不改变既有排名解码配方。

二次 attention 运算理论比例为 `(23/4+4)/27 = 0.3611`，不解释为整个编码器或诊断耗时比例。

| Arm | 内容 | 问题 |
|---|---|---|
| FULL | 新主图，原始完整编码器 | 新的可读编译本身的表现 |
| GEOM | 同一主图，四个空间区域分组 | 普通空间分区的作用 |
| SEM | 同一主图，按来源关系重新分组 | 预选方法，来源引导的编码是否有用 |
| SHAM | 同算法，固定受控重连关系 | 正确关系的贡献；资格失败则取消 |
| NATIVE4 | 四区域原像素导出四图，一次输入 | 原生多图这一更简单系统是否足够 |

前四臂 PNG 相同而计算不同。NATIVE4 图元、像素和总图像 token 相同，但图像边界、位置处理与融合也变化；它不是纯 attention 对照。

## 来源分组的确定性定义

仅采用冻结可见账本的 calls、request_parent、hosts、has_instance、owns，不能加入推测因果关系。图像保留重复边；仅优化目标合并同类型同端点关系，以 `1/sqrt(outdegree(source)*indegree(target))` 加权，分配到端点来源单元并按关系类型归一化后平均，避免高连接实体主导。

从 GEOM 开始，完整来源单元不拆分；枚举单元转移及两两交换，选择最大严格跨组权重降幅；差值保留 12 位，同分按稳定 ID 和目的组顺序。至多接受 100 次严格改善。每组容量为全部 merged cell 的四分之一。

仅用 renderer 证明位于所有卡片、标题等保护矩形之外的真实背景 patch 补齐容量，不用亮度判断。尽量保留原背景归属；以原始 GEOM 为参照的累计背景改组不超过全部 patch 的 5%，不是每次移动 5%。保留所有 patch 恰好一次。无改善时保留 GEOM 的完整映射并复用其回答。

SHAM 用固定哈希种子和固定 `100 × 边数` 次类型/度数保持双边交换提案；禁止自环、新重复边及把原真边当成替换边，不搜索种子。错边不画入 dashboard。

## 数据、复用和预算

220 个已暴露开发病例：AIOPS-2022/2025 各 60，AegisLab 100。历史 T_FULL 和 A_UNIFORM 直接复用，不重跑文本或桥接。各臂最近历史条件与实质改动见差异清单。

生成身份含实际提示、像素、模型及 processor、后端/精度、解码、种子、编码操作与规范化分组映射；不含 arm 名称或 scorer。所有新臂同病例同种子。计算完全相同则引用本轮原子提交回答；scorer 改变只离线重评分并保留旧分数。近似臂必须有独立问题及足够实际干预，否则取消。

机制子集哈希固定每集 20 例、优先不同事件组。FULL/GEOM/SEM/NATIVE4 各一次独立 QA，分别测量读取、实体/单位绑定、阶段比较，包含关系支持的跨卡片绑定题。图内标记目标；不继承 RCA 排名指令。问题不可构造则 N/A，不按回答重选。QA 答案不进入诊断。统计以病例/事件组为单位，不能把多题当独立病例。

attention 只复用该子集的主调用和 QA，记录文本与图像区域；每次摘要不超过 64KiB，每万次含附属、索引、临时文件不超过十进制 1GB。不保存完整矩阵/QKV，不为热图重复调用。高 attention 不等于因果使用或有害 sink。

| 用途 | 上限 |
|---|---:|
| 五臂 ×220 | 1100 |
| 四种 QA ×60 | 240 |
| 一个逻辑 GPU smoke | 18 |
| 基础设施中断恢复预留 | 142 |
| 合计 | 1500 |

约 8000 次是用户允许空间，不是需要用满的目标；余额不转新臂。别名及 SHAM 取消可减少调用。恢复预留不能重置 smoke 或重答已提交的错误排名。

## CPU 干预准入

全部 220 例审核。每数据集至少 50% 的**同一批病例**，SEM 对 GEOM 同时满足：卡片加权与前景面积加权的两种同组关系变化率 ≥20%，真实关系跨组权重下降 ≥15%。

变化率为 `sum(a_u*a_v*abs(same_A-same_B))/sum(a_u*a_v)`，遍历全部不同单元对；分别 a=1 与真实前景面积，组编号重命名不改变结果。无关系、零切边、无变化仍在分母中。SEM 不足则候选停止。SHAM 还须相对 SEM 达到相应变化门槛且加权关系替换率 ≥50%；不足则首次调用前取消 SHAM 和对应归因、缩减机制校正族，不换种子。

## 检查、执行与停止

1. 静态和 CPU：完整事实、出现次数、候选、几何、容量、背景、token、确定性；评分只从 `scorer` 导入。最多八个不同物理核 worker，优先分散 source/cloudbed。无需全 220 例 GPU 特征提取。
2. 算子：K=1 与原路径一致；小张量独立显式分块参考一致；组编号不影响结果；原位置、token 顺序和 merger 邻域完整。
3. 实际例图：每 arm/数据集一个固定例图，另看密集、长名称、极值。相同 PNG 标明共享，不重复人工审查历史全集。
4. 一个 GPU smoke：最多18调用、共享600秒，包括启动、少量特征核验、保存和验证。覆盖五臂、四种 QA；超时/未完成即未通过。若 SHAM 取消省下额度，不另填臂。沿用模型、40960 context、8192输出、GPU0.75与已登记解码，不按 smoke MRR 调参。
5. 全部资格通过后冻结运行：病例哈希顺序、均衡轮换臂序；不中途看 MRR 改队列。恢复信任原子完成标记。主冷时延在正式请求中从公共包读取到答案验证连续计时，关闭病例缓存；不能用分项耗时之和冒充连续测量。
6. 完成后排空写入、审计、完整分析、关闭自有 GPU。语义/预算/干预失败按门槛停止；未运行项目如实标记，不用成功的局部测试代替全部资格。

## 统计和推进标准

主要族 SEM−FULL、SEM−GEOM、SEM−NATIVE4，事件组 Pratt-zero Wilcoxon 为主，病例另报；共同三项 Holm，12 位差值、配对 dz、不报告 CI。机制族为 SEM−SHAM RR 与 SEM 对其余三表示的 QA；SHAM 取消前冻结缩减族。signed-rank 不解释为任意均值零假设检验。

报告病例加权 ΔMRR、绝对 MRR、AC@1/3/5、Precision、AVG、宏平均、事件组、修复/破坏、失败分母、成本、attention。模型无效计零；基础设施缺失未知，全分母紧界限；未知未解决不能宣布采用。

SEM 相对复用 T_FULL 整体 ΔMRR≥0.02（约0.505），各数据集 MRR/AC@5 不下降；各集实际 input+output ≤T_FULL×1.05；新连续冷时延 ≤历史 T_FULL 在线时延×1.05。后者是保守、跨时期且时延口径不对称的工程参照，不是同期冷启动文本速度证明。当前五臂采用相同后端、精度、负载，另测编译、绘图、编码、prefill、生成、验证。

整体方案进步而组件归因不足时承认整体进步并缩小主张；不自动改用最高分臂，不搜索层数。后续独立冻结验证须另行登记与曝光审核。

## 实施交付

`RQs/RQ4_2/` 五功能模块、≤7500行；计划、差异/文献/评审附件、来源与分组接口、资格凭据、输入清单、例图和唯一 findings。默认所有 GPU/正式入口关闭，只能由匹配冻结版本的完整资格启用。保留所有历史材料与已有组件默认语义，**不修改 Codex.md**。


## CPU implementation update — 2026-10-09

The user subsequently authorized code/plan revisions with a CPU-only stopping boundary. The [versioned revision](RQ4_2_CPU_Revision_2026-10-09.md) documents source-scoped captions, four vertical regions and qualification repairs. The common representation now passes all 220 render audits, but SEM qualifies only 38/100 AegisLab cases (required 50/100); the separately evaluated ink-weighted alternative reaches 44/100. The candidate stops under this plan's scientific gate. Full CPU admission is not passed; GPU smoke and formal execution have not run. Earlier planning-status paragraphs describe their original point in time. See the [current report](../experiment_reports/RQ4_2_CPU_Revision_2026-10-09.md).


## Latest user-authorized revision — deterministic best-prefix partitioning

The user explicitly reopened method revision after v3 failed. [v4 protocol](../../RQs/RQ4_2/descriptions/RQ4_2_partition_refinement_v4.md) replaces strict per-step descent with a deterministic capacity-feasible search pass and best strictly improving prefix. At most8 passes/100 committed moves; original objective, images, sources, thresholds, denominator and SHAM seed remain unchanged. Temporary non-improving steps are allowed only inside a pass, not as an accepted final degradation. SEM57/60,56/60,71/100 and SHAM56/60,56/60,90/100 pass the CPU intervention gates. Actual processor, QA inputs and offline paths are qualified. No new blind review, model inference, GPU smoke or formal execution has occurred. Latest status/report supersedes the earlier stopping status, retaining every failure artifact. Stop after CPU as instructed.


## GPU smoke execution update — 2026-10-09

The user subsequently authorized GPU smoke and monitoring only. CPU admission remains passed. The single original600s smoke stopped with16 committed answers and17 charged attempts; the final AegisLabSHAM request was not initiated. An execution-only overlay omitted one redundant SEMQA before any model answer after a pre-generation failure spent a call. Both implementation failures were fixed without changing inputs/model/recipe or resetting the clock. Full GPU qualification is NOT passed; no formal execution. See [GPU report](../experiment_reports/RQ4_2_GPU_Smoke_2026-10-09.md).


## Authorized affected-path supplement — 2026-10-09

The user grants five additional smoke opportunities of at most18calls each; the600-second per-opportunity cap remains. [Registered scope](../../RQs/RQ4_2/descriptions/RQ4_2_Smoke_Supplement_2026-10-09.md). Only the first was needed:2new calls,89.03seconds,passed. With16semantically compatible inherited completions, all18original smoke identities are covered. The original round remains failed_timeout. This raises maximum registered call space by90(to1590), not the formal matrix. No further supplement or formal execution was started. [Report](../experiment_reports/RQ4_2_GPU_Smoke_Supplement_2026-10-09.md).

## Formal runner deployment — 2026-10-09

User authorizes formal entry-point implementation and qualification, then stopping before launch. The [recovery amendment](../../RQs/RQ4_2/descriptions/RQ4_2_Formal_Recovery_2026-10-09.md) preserves the method and queue. Eighteen affected CPU checks pass, including six actual SIGKILL transaction boundaries, SIGTERM drain, durable-response recovery without another model call, and attention namespaces across restart. Sixty inherited generation definitions and shared dependencies are unchanged; GPU qualification is reused with an explicit receipt chain. No new model calls. Formal readiness is `ready`; the 1,336-position / 1,328-unique-call queue remains unstarted, with no active execution credential. [Report](../experiment_reports/RQ4_2_Formal_Readiness_2026-10-09.md).
