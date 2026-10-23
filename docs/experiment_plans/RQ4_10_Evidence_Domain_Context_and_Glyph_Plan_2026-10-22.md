# RQ4.10：证据域保留、域外上下文压缩与边际图表达

日期：2026-10-22。状态：用户批准实施；本次仅代码与静态检查。CPU、渲染、GPU smoke、正式调用均不在本次执行范围。

## 1. 决定与研究依据

把域外 token 移除的正向收益作为下一轮起点，同时推进纯视觉、hybrid、融合、剪枝、attention 与可信 QA。不因校正后不显著忽略实际变化，也不缩小旧统计族改写历史显著性。

| 已有证据 | 决定 |
|---|---|
| RQ4.9 DOMAIN−FULL ΔMRR≈+0.0428，43例改善、26例退化，原校正结果不变 | 区分域外信息、序列长度与attention分配 |
| P_DOMAIN 0.3531，U28 0.3489；U28约93%的保留位置属于A，删E平均只减少约224位置 | 以完整D为计算底座，不继续微调E50比例 |
| RQ4.9融合改变的保留位置比例较小 | 保留D，融合原本删除的O |
| marginal去点控制保留逐点数字 | 在没有精确数字备份时检查样本点作用 |
| RQ4.9 attention实际释放质量小 | 使用范围明确的域外操作，保留原生gate与线性层 |
| QA存在题间提示及类别偏斜 | 每次仅一道独立题，加无证据与有效绑定控制 |

A包括身份、单位、统计标签及数值文字，不只是实体名称。O不等于无信息空白，编码后可能含全局上下文。

文献：[VisionZip，CVPR 2025](https://github.com/JIA-Lab-research/VisionZip)提供保留重要位置并聚合上下文的启发；[Vision Transformers Need Registers，ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/0b408293619f725fd30162af057e531a-Abstract-Conference.html)及[Attention Sinks: A “Catch, Tag, Release” Mechanism，NeurIPS 2025](https://papers.nips.cc/paper_files/paper/2025/hash/77cd5a17edf97293eab706caf9bfee39-Abstract-Conference.html)提示背景/sink不必然有害。本轮是冻结Qwen上的适配，不称原论文复现。

解释链：输入/算子改变→读取与归属→实际诊断引用→排名→成本。用户确认保留多方向、复用对照；允许省略逐点精确标注；总调用≤5700；静态通过后停下。Hybrid为本轮明确授权，不改Codex.md。

## 2. 公共输入与20个新条件

同一220个已暴露开发病例：AIOPS-2022/2025各60、AegisLab 100。全部RCA单次调用；模型、候选、评分和排名解码冻结。复用RQ4.9的4096²、最多28卡公共输入及其已登记遗漏，不重新选择遥测。

D=A∪E，O为其补集。P_DOMAIN保留D，P_FULL保留全部位置。历史FULL、DOMAIN、U28、D14、强文本及marginal结果复用，披露运行版本及跨批次限制。

### 2.1 组织：七个新臂与一个复用臂

| Arm | 固定行为 |
|---|---|
| V_EXACT_DOMAIN | 完整边际图及精确逐点数字，保留全部D |
| V_SAMPLE_GLYPH | 只移除逐样本耗时数字；几何与EXACT保留索引相同 |
| V_SAMPLE_PACK | 同GLYPH内容，卡内收回空数值列，扩展真实图形；重新计算D；纯视觉预选 |
| V_SAMPLE_MARKLESS | 同GLYPH，仅再删除样本点，统计图元保留，索引不变 |
| H_SAMPLE_GLYPH | hybrid版GLYPH |
| H_SAMPLE_PACK | hybrid版PACK；hybrid预选 |
| H_SAMPLE_MARKLESS | hybrid版MARKLESS |
| H_EXACT（复用） | RQ4.9 H_MARGINAL_DIRECT |

最多两关系，每阶段最多32原样本。实体、操作、单位、阶段、样本编号、总体数、p50/p95、条件统计及阈值不变。GLYPH删除文字后仍保留该位置token，隔离序列长度。PACK仅调整同一卡内部，不移动其他卡，不添高清副本。真实父子样本用原编号关联，不连接reference/current为同一请求。Hybrid配对来源独占图像，省略数字不回填文本。无配对登记无实际干预，精确相同请求引用。省略精确样本数字是信息精度取舍，不称无损。

### 2.2 域外融合：四臂

b=min(|O|,256,max(1,floor(0.05|D|)))。O为空引用DOMAIN。D的原embedding不变。

| Arm | 固定行为 |
|---|---|
| F_O_SPATIAL | O按卡内/卡外区域分配名额，在区域内按空间分组求均值 |
| F_O_FEATURE | 相同代表位置，O按embedding余弦相似度分组求均值；预选 |
| F_O_REP | 相同代表位置，仅保留其原embedding |
| F_O_SHAM | FEATURE代表与组大小不变，固定哈希置换非代表成员后均值 |

非空区域至少一代表，剩余按最大余数法；首点最靠近区域中心，之后最远点，同分按原索引。区域数>b时明确容量阻塞，不暗中跨区分配SPATIAL。FEATURE可跨区域，但不纳入D。代表始终属于自身组；零范数采用稳定索引规则。FP32累加转BF16，无额外输出归一化或零向量。保留原MRoPE及顺序。SHAM不搜种子。

### 2.3 域外剪枝：三新臂

| Arm | 固定行为 |
|---|---|
| P_INK | 全D＋O中覆盖可见非背景像素的位置 |
| P_CARD | 全D＋卡片内容区域内所有位置 |
| P_LENGTH_CONTROL | 全A＋从E∪O空间选择恰好|E|个位置，总数同DOMAIN |

前两者为候选，第三者仅机制控制，明确丢失E。INK使用unified renderer仅背景填充底图，经同processor几何后与真实图像比较；不以特征范数猜测空白。不删除D。FULL/DOMAIN复用为边界控制。

### 2.4 Attention：四新臂

全部使用FULL原图和完整序列。

| Arm | 固定行为 |
|---|---|
| S_O_REDIST | 全O质量转到D，按D原质量比例分配 |
| S_SINK_REDIST | 候选sink质量转到D |
| S_BG_REDIST | 普通O移出与SINK共同可提供的相同质量，再转D |
| S_O_MASK | 屏蔽O后对文本及D整体归一化 |

沿用第3层最后八个公共指令查询、≥6个查询达到5倍均匀密度的检测，调用内固定。干预full-attention层3、7…63中可访问图像的文本查询；去掉旧head筛选。保留线性attention、权重、gate、位置。SINK/BG每head/query释放min(sink质量,普通O质量)，BG不含候选sink。D质量为零/无供体时登记无操作。通过融合加权和计算，不保存完整矩阵。MASK/REDIST不等价于缩短经历线性层的序列。

### 2.5 数量与显示：两新臂

D14_DOMAIN_FIXED/D14_DOMAIN_PACK分别复用RQ4.9 D14_FIXED/D14_PACK像素，但保留全D。结合旧E50版及U28/DOMAIN检验显示与token规则的交互，不新搜索卡数。

## 3. QA、attention、统计与预算

哈希固定30例，每集10例，优先不同事件组。每例三题分别调用：数值读取（显示精确值或图形区间）、来源绑定（实体/单位/统计口径均衡）、同口径阶段比较。目标先冻结，不按模型错误/排名选择。只用可见定位，绑定问题不泄答案。省略精确数字后不要求原精度。

十QA输入：P_FULL、P_DOMAIN、U28、V_SAMPLE_GLYPH、V_SAMPLE_PACK、H_SAMPLE_GLYPH、H_SAMPLE_PACK、F_O_FEATURE、P_INK、S_O_REDIST。另每例三个绑定控制：无证据、同像素/位置/尺度的目标隔离、全局一致实体重命名。合成题不用故障标签评分RCA，不再制造p50>p95。

宽容提取只依据公开题号与格式；过滤非法题号不抹掉合法答案；不读oracle择答案。替代正确答案完整接受；真正多值题非空正确子集0.5，含错误内容不给部分命中分。报告条件QA、目标保留及端到端覆盖；保存显示精度与可见证明。固定子集阅读QA/RCA，区分读错、归属错、未采用及理由排名矛盾。

attention记录层3/23/43/63、最后prompt及首decode，分指令/hybrid文字/标签与数值/图元/装饰背景；保存O构成、融合组、供受质量、无操作率、质量与每token密度。公开分层变量在调用前冻结；故障类型只离线分析；不足20事件组只描述。

事件组Pratt-zero Wilcoxon为主要推断，病例另报，差值12位、配对dz、无CI。冻结Holm族：

- 组织：V/H各GLYPH−EXACT、PACK−GLYPH、GLYPH−MARKLESS。
- 融合：SPATIAL−DOMAIN、FEATURE−DOMAIN、FEATURE−SPATIAL、FEATURE−REP、FEATURE−SHAM。
- 剪枝：INK−DOMAIN、CARD−DOMAIN、INK−CARD、DOMAIN−LENGTH_CONTROL。
- Attention：O_REDIST−FULL、SINK_REDIST−FULL、SINK_REDIST−BG_REDIST、O_REDIST−O_MASK、O_REDIST−SINK_REDIST。
- 数量：D14_DOMAIN_FIXED−DOMAIN、D14_DOMAIN_PACK−D14_DOMAIN_FIXED、新旧token规则PACK−FIXED的交互。
- QA：V/H的PACK−GLYPH，FEATURE−DOMAIN，INK−DOMAIN，O_REDIST−FULL，三个控制各对DOMAIN。

旧DOMAIN−FULL保留旧校正身份，不借新族宣布显著。报告标准/宽容MRR、AC、Precision、AVG、逐集、修复/破坏、无效输出/未知分母及实际成本。纯视觉争取对DOMAIN+0.02及各集MRR/AC@5不降，实际总token优先≤1.05倍；hybrid争取0.4912且各集对T_FULL至少省10%。工程进步与机制证据分别记录，不追认最高分为预选。

| 用途 | 最大新增calls |
|---|---:|
| 20新RCA×220 | 4400 |
| 10QA输入×30例×3独立问题 | 900 |
| 三QA控制×30 | 90 |
| V_SAMPLE_PACK/F_O_FEATURE/H_SAMPLE_PACK各30独立重复 | 90 |
| 三专项smoke各18 | 54 |
| 基础设施恢复 | 166 |
| 总计 | 5700 |

正式科研最多5480；精确引用/不适用减少实际调用，余额不自动变新臂。

## 4. 实现及后续资格合同

RQs/RQ4_10五功能模块≤7500行。新增EvidenceDomainPacketV2、AnnotationContractV1、ContextOperatorPlanV1；复用已验证单调用、融合内核、原子提交、快速恢复。新评分只从scorer导入，历史源码/结果不变。

后续测试覆盖220例来源/候选/几何/预算；EXACT/GLYPH索引；仅样本去点；PACK标签完整；hybrid无诊断副本；D不变/O融合分区；小张量独立均值和质量守恒；gate/MRoPE/顺序/批处理；QA oracle/可见性/自然语言/格式；原子提交/引用/重复/断电恢复。输入+8192≤40960，图像≤16384 token、4096²、≤28卡。实际相同请求引用，近似无干预公开记录。

未来先重型CPU准备，再三专项smoke（组织/hybrid、算子、QA，各18 calls、900秒）。8独立CPU worker、GPU并发8、显存0.8、有界RAM；慢分支逐次≤20s或推理区间平均GPU≥82%。完整直接可读输入/PNG/对话/输出/评分/映射/attention去重保留，每万次≤25GB，attention≤1GB；不使用压缩归档。

## 5. 本次实施边界

计划与附件落盘→代码→AST/语法、TS类型、注册/依赖、行数、私有边界、历史保护、默认关闭入口的静态检查→停止。**不执行测试用例、prepare、renderer/browser、processor计数、特征提取、CPU回归、GPU smoke或正式调用。**

静态成功不能代替运行资格。未来执行必须重新取得绑定当前冻结版本的授权，静态检查不会自动启用任何模型入口。


## 实施期核实与用户批准的修订：纯视觉完整标注基准 v2

2026-10-22 静态源码及保留输入复核发现，RQ4.9 的纯视觉 `V_MARGINAL_DIRECT` 使用 `trace_joint.marginals`，没有逐样本精确数字列；hybrid 使用 `trace_joint.complete_marginals`，具有该列。原计划把两者当成相同画法的前提不成立。

用户明确批准：“允许建立新版完整标注对照”。因此，四个纯视觉组织条件共同改用新的完整标注基准：从 RQ4.9 保留的 hybrid 配对包中匹配相同父/子实体、操作、总体计数和完整样本集合，加入已有的完整配对字段与统计。只使用冻结来源，不获取新遥测。记录每项新增可见字段及来源哈希。

`V_EXACT_DOMAIN` 是新完整标注基准，不能写成“旧原生图只改了 token 选择”。它与三个派生纯视觉条件共享新增事实及新基准布局；PACK 只在该基准卡片内部回收数字列。其他卡片的事实集合保留，原始 U28、P_DOMAIN、融合和剪枝等分支不采用这个新增包。新基准通过现有 fixed-canvas preset 和 complete_marginals 编译；如果 4096²/28卡/字号容量不成立，后续 CPU 阶段明确阻塞，不删除事实、不缩字、不伪装无操作通过。

Hybrid 完整标注对照仍直接引用历史结果。调用条件数、预算和比较族不变。组内数字/点对照保持有效；与旧 U28 的差异必须同时披露可见事实和基准布局变化。


## 本次交付状态

2026-10-22：计划及代码已落盘，静态检查通过（有效代码2865行，五功能模块）。状态凭据：`RQs/RQ4_10/findings/static_check.json`；唯一 findings：`RQs/RQ4_10/findings/exp_domain_context_findings.md`。CPU回归、渲染、实际processor计数、GPU smoke及正式实验均未运行；新增模型调用0。已按用户要求停止，不自动推进后续资格。


## 2026-10-22 执行授权与 CPU 实现修复

用户已授权 CPU 回归、三项登记 smoke，全部通过后启动正式队列。执行开关仍默认关闭，阶段凭据单独绑定当前源版本。

新版完整标注基准采用现有 renderer 的 DOM 测量及 row/column 布局操作，按实测高度将完整卡片放入独立列，长卡优先、同高按来源顺序，每列内部保持来源顺序。这避免等高行让短卡浪费大块高度；不删除来源、不缩字体、不改变历史布局。四个纯视觉组织臂共用这一新基准。PACK 只扩宽样本 SVG 的横向范围，保持其原屏幕高度和点半径，避免响应式 SVG 随宽度增高而裁掉末尾样本。

CPU 已确认并修复：新导出构建目标错误、QA 隔离审核误读隐藏卡片空字号、句末标点与显式单位导致正确 QA 数值/实体被误拒。单位换算只使用题目登记的实际单位，不读取 oracle 作提取选择，不放宽数值误差。三个固定真实病例已通过修复后的准备；14项离线单元回归通过。全220例审核进行中，GPU与正式调用均尚未开始。


### 实图抽查后的完整标注几何修复

第一次实际PNG抽查发现：窄等宽列中，逐样本数字占据了180px最小宽度，剩余SVG仅约12.5px宽、0.56px高，点实际不可见。仅检查文字字号与线宽不足以发现该问题。旧资格不据此宣称视觉通过。

新版V基准改用1344px宽的完整边际卡专列，其他卡片按实际DOM高度分配到独立列；所有来源与原数字不变。新显式complete_readable操作要求每个样本图区≥80px宽、≥12px高、样本点半径4px，随后四个组织条件由该共同基准派生。GLYPH保留空数字列，PACK回收该列横向空间并保持点半径及高度，MARKLESS仅隐藏样本点。旧组件默认行为、历史PNG与hybrid完整标注对照保持原样。三个固定病例已通过此修复的CPU准备，实际抽查确认点可见。


## 2026-10-22 本次实测速度的用户接受与正式启动授权

全部220例CPU资格、三项GPU smoke的数值与产物检查已通过。算子smoke共18次，完整推理区间GPU平均利用率81.2892%，低于登记82%（并发区间84.5225%）；原始门槛结果仍保留为未达到。用户明确回复“接受本次速度，启动正式实验（推荐）”，因此本次运行按该速度获得独立执行许可。这不是将81.2892%改写为达到82%，也不修改未来通用门槛、科学输入或统计协议。绑定源版本 `8bca5ee08aea68122411b76fb2be23e38ff60109168d90d77526ffb5575884e6`，冻结正式队列5465个位置。操作授权及原测量保存在 `authorization/operator_speed_acceptance.json` 和 `smoke_operators/speed_review.json`。
