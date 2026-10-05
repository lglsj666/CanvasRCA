# RQ3.15：同请求连续耗时关系的受控视觉验证

2026-10-02 用户批准实施。当前执行边界：代码、完整 CPU 回归、实际例图审查、GPU smoke；通过后停止，不启动正式实验。单一主 agent。本文将已批准方案落盘；实际资格状态见 RQ3.15 roadMap，不能把计划当作完成记录。

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

## Frozen implementation definitions

Cross-entity direct observed pairs only. Identity duplicates (including conflicting
rows), cycles and chains entering cycles are excluded. Missing ancestors do not
invalidate a directly observed unique pair. Parent selection precedes child
availability. Duration ties use source span ID then source row. Reference uses
parent relative time < public split; current includes the split and last edge.
Quantiles use linear interpolation of sorted measured durations. Strictly >
reference p95 defines each binary coordinate; cells ordered00,01,10,11.
Conditional child p50/p95 is shown for each parent-slow group with at least5
requests. Diversity requires4 distinct displayed sampled pairs in one phase/binary cell.
Select by decreasing absolute parent log1p p95 change; ties by public parent,
parent operation, child, child operation. Sample rank=floor(i*(n-1)/(k-1)+0.5),
k=min(32,n), sorted by parent duration then trace/parent/child identity.
No source identity is transmitted. Quantile interpolation is a statistic, never
an inserted observation. Both plots use identical positive log1p scale with
zero retained and maximum=max(1,all sampled coordinates). No clipping.

No applicable packet: every nonrepeat arm aliases BASE_TEXT after exact-input
proof; PAIR_REPEAT remains a real call. No-op positions remain in220-case
intention-to-apply denominators. Per-applicability strata are secondary.
Only new source/compiler/renderer/runtime qualification applies to this version.
A passed CPU test never implies passed GPU smoke. Formal launch is disabled.

If anonymization collapses distinct source operation names, append a deterministic
operation ordinal within that visible-name group before pairing; never merge
different original operations. This is public identity disambiguation, not
outcome-based grouping. The marginal control uses two separate horizontal value
axes with categorical reference/current rows, never artificial duration values
on the orthogonal coordinate. Full-roster mean cost gates apply to the220 cases;
the three-case smoke CPU audit checks its intact capacity and inherits that
whole-roster cost decision rather than adding a per-case cost threshold.
