我建议把这个项目的核心问题，从：

> **“如何让 VLM 阅读 dashboard 并进行 RCA？”**

提升为：

> **“如何把海量、异构、跨系统的 telemetry，压缩成一种在有限推理预算下仍然保留根因辨识能力的表示？”**

Dashboard 是这种表示的一种载体，而不必成为预先认定的答案。

**我最推荐的主线是：诊断导向的信息压缩 + 可学习的 dashboard 编译器 + 跨系统泛化。** 更具体地说，是让系统学习“保留哪些证据、保留哪些对照关系、怎样展示这些关系”，而不是简单地把更多数据画进一张图。

以下是截至 **2026 年 9 月 24 日**的跨领域检索与选题分析。文末列出了本文实际参考的 **56 篇论文及技术报告**；没有核实正式发表去向的工作按 arXiv 版本列示。这是一份面向研究选题的广覆盖调查，不声称穷尽了每个领域的全部论文。

---

# 一、你们真正有价值的研究资源，不只是“120GB 数据”

按照你描述的规模，你们有超过 120GB 的 telemetry。但研究上需要区分：

**数据字节数、独立故障事件数、系统多样性、诊断任务多样性，是四个不同的量。**

你们以前的本地审计记录显示，AIOps2022、AIOps2025、AegisLab 分别存在不同的系统、标签粒度和数据完整性；其中 AIOps2022 与 AIOps2025 都包含 HipsterShop/Online Boutique 系统家族，AegisLab 则基于增强版 Train Ticket。因此，“三个数据集”不能直接等同于“三个完全独立的应用架构”。:chatgpt-content-reference{index="0"}

我认为你们的数据条件主要支持下面这些研究问题：

| 数据特征 | 能形成的研究问题 | 不宜直接宣称的结论 |
|---|---|---|
| 超大量 metrics、logs、traces | 有限预算下如何保留诊断价值？ | 数据量大，所以方法一定更有创新性 |
| 不同日志模板、指标名称和单位 | 如何迁移语义，而不是记忆字段名？ | 统一一下字段名就解决了异构性 |
| 不同 service/pod/node 名称 | 模型是否依赖名字捷径？ | 名称不同就构成跨系统泛化 |
| 不同调用和部署关系 | 如何保留传播关系与共享资源关系？ | 调用图就是因果图 |
| service/pod/node 多粒度标签 | 如何区分故障位置、影响范围和可辨识粒度？ | 将所有标签映射成 service 后仍是同一任务 |
| 多种 failure type | 如何泛化到未见故障机制？ | 同一种故障换个实体就是未见故障 |
| 模态缺失和采集不完整 | 证据不足时如何降级诊断或拒答？ | 没有观测到异常就代表正常 |

这里还有两个会直接影响论文可信度的问题。

**第一，120GB 不等于大量独立训练样本。** 你们旧审计中，AIOps2022 的 541 个 case 有 521 个与其他 case 的时间窗口重叠；同一原始 telemetry 行可能出现在多个 case。随机按 case 划分训练集和测试集，可能造成泄漏。:chatgpt-content-reference{index="1"}

**第二，标签粒度不能被预处理悄悄改变。** 旧审计中 AegisLab 的 canonical target 是 service，但发布标签包含更细的实体；只有 AIOps2022 和 AIOps2025 直接提供 root-cause node 标签。多个实体标签也不一定意味着多个独立根因，可能只是同一故障在不同层级的映射。:chatgpt-content-reference{index="2"} :chatgpt-content-reference{index="3"}

**所以，你们最大的优势是：能够系统性研究“诊断信息在压缩、异构转换和跨系统迁移过程中如何丢失”，而不只是跑一个更大的 RCA benchmark。**

---

# 二、相关领域地图：哪些应当成为主线，哪些只是工具

下面的编号对应文末书目。“优先级”是我对你们项目的判断，不是这些领域本身的重要性。

| 领域 | 与项目最相关的问题 | 可借鉴方向与文献 | 建议定位 |
|---|---|---|---|
| **Information theory** | 什么信息必须保留，才能区分根因？ | Rate–distortion、Information Bottleneck、usable information [20–24] | **核心理论视角** |
| **Information / context compression** | 如何降低模型输入成本，又不丢失诊断证据？ | LLMLingua-2、DeepSeek-OCR、Glyph [25–27] | **核心比较对象** |
| **Root cause analysis / fault localization** | 如何区分根因与被传播影响的组件？ | Eadro、Nezha、MicroRCA、BARO、TraceRCA [6–11] | **核心任务基础** |
| **Causal inference / diagnosis** | 哪些观察支持故障传播，而不只是相关性？ | AegisLab、OpenRCA 2.0、CHASE、MetaRCA [1,5,13,16] | **高价值主线** |
| **Graph theory / heterogeneous graphs** | 怎样同时表达调用、部署、资源共享和时间关系？ | CHASE、Deep Sets [13,51] | **重要结构基础** |
| **Topological data analysis** | 动态系统结构变化是否能提供稳健特征？ | Topological Autoencoders [52] | 探索性支线 |
| **Computer vision / chart reasoning** | 模型能否读准曲线、刻度、图例、边和时间顺序？ | ChartQA、ChartGemma、PlotQA [29–31] | 必须验证的能力层 |
| **Dashboard inference** | 多面板之间的信息能否被正确关联？ | DashboardQA [28] | 近邻任务与评测启发 |
| **Visualization / image generation** | 什么图形语法能保证数据忠实、布局可读？ | Vega-Lite、Draco [34–35] | 优先使用程序化渲染 |
| **Multimodal learning** | 三种 telemetry 的互补、冗余与冲突如何处理？ | TVDiag、PID、跨模态交互分析、CLIP [14,24,36,40] | **重要方法来源** |
| **Time-series representation** | 如何抽取变化点、趋势、突变和异常形态？ | VisionTS、VLM anomaly detection、TS2Vec、Chronos [32–33,37–38] | 指标处理与强基线 |
| **Log processing** | 如何压缩重复模板，又保留稀有错误和关键参数？ | Drain、Logzip [41–42] | 数据处理基础 |
| **Trace processing** | 如何保留关键调用、异常路径和 caller/callee 区别？ | TraceRCA、TraceDiag、Dapper、Sifter [11–12,44–45] | **重要诊断证据** |
| **Big data / streaming algorithms** | 如何不扫描全部原始数据就形成有效摘要？ | DDSketch、Sifter [43,45] | 工程基础，或单独系统主线 |
| **Reinforcement learning / decision theory** | 怎样学习“展示什么”，而不必让 agent 不断试工具？ | Contextual bandit、ThinkFL、TraceDiag、DPO [12,15,46–47] | 可学习编译器 |
| **LLM fine-tuning / self-supervision** | 有大量无标签 telemetry、少量故障标签时怎样训练？ | LoRA、ChartGemma、TS2Vec、CLIP [30,37,40,48] | 训练手段，不宜单独作为创新 |
| **Domain generalization** | 跨命名、跨 schema、跨系统时什么应当保持不变？ | MetaRCA、Group DRO、DomainBed、Deep Sets [16,49–51] | **核心评测维度** |
| **Uncertainty / selective prediction** | 证据只能支持 service 时，是否应避免猜具体 pod？ | Conformal Risk Control [53] | 有潜力的独立故事 |
| **Grounding / faithfulness** | 正确答案是否真的来自 dashboard 上的证据？ | OpenRCA 2.0、ERASER [5,54] | **必须具备的验证层** |
| **Security of AI systems** | 攻击者能否通过日志内容诱导 RCA 模型？ | When AIOps Become “AI Oops” [56] | 鲁棒性支线 |

这个地图的含义不是“把这些技术都加进去”，而是：

> **先选一个中心问题，再从这些领域中选择必要工具。**

---

# 三、哪些看似创新的方向，实际上已经有非常接近的工作？

这是选题时最需要提前看清的部分。

| 看起来像一个新方向 | 已存在的近邻 | 你们还需要新增什么 |
|---|---|---|
| 把文本变成图片，减少输入 token | DeepSeek-OCR、Glyph；Glyph 还搜索渲染配置 | **面向诊断任务的证据保留机制**，而非普通文本光学压缩 |
| 用 RL 微调小模型做 RCA | ThinkFL 已采用多阶段 GRPO | 学习的对象应更明确，例如**证据选择与视觉编译策略** |
| 用 RL 选择图上的关键部分 | TraceDiag 已研究 RL 图剪枝 | 保留哪些**诊断对照关系**，以及压缩后如何验证 |
| 融合 logs、metrics、traces | Eadro、DiagFusion、TVDiag 等 | 不能只说“三模态融合”；要解决互补证据被压缩丢失的问题 |
| 因果图、超图、多粒度结构 | CHASE、MetaRCA | 不能只换图结构名称；要证明保留了什么新的诊断性质 |
| VLM 阅读 dashboard | DashboardQA | 从问答跨到**故障辨识、证据压缩、跨系统泛化** |
| 输出传播链或可解释证据 | OpenRCA 2.0 | 验证 dashboard 是否保留了支持正确传播解释的证据 |
| 冻结模型，只演化外部流程 | OpsHarness | 需要比一般外部流程优化更具体、可分析的机制 |

这些重叠不是说你们不能做，而是意味着论文的贡献不能停在这些组合本身。Glyph、ThinkFL、TraceDiag 和 OpenRCA 2.0 尤其需要认真区分。:chatgpt-content-reference{index="4"}

另外，2026 年的 MetaRCA 与 OpsHarness 已分别探索可迁移的 RCA 知识结构和自演化外部流程。因此，“跨系统知识”“冻结模型但学习外部组件”也不能直接当作空白领域。:chatgpt-content-reference{index="5"}

---

# 四、我最推荐的六条技术路线

## 路线 A：诊断导向压缩——保留“能区分根因的证据”，而不是保留最多数据

### 核心研究问题

> **同样的输入预算下，什么表示最能保留根因之间的可辨识性？**

这是我最看好的主线。

### 1. 为什么信息论适合，但不能直接套公式？

设原始 telemetry 为：

\[
X=(M,L,T,G)
\]

其中分别表示 metrics、logs、traces 和系统关系；dashboard 为 \(D=g(X)\)，根因为 \(Y\)。

如果 dashboard 只是由原始数据生成，那么：

\[
I(Y;D)\le I(Y;X).
\]

也就是说，**画成图并不会凭空增加原始数据中关于根因的 Shannon 信息**。

但是，模型不是无限强的解码器。某些信息存在于原始数据中，却可能因为输入长度、表示方式或推理能力限制而无法被模型有效利用。“Usable information”理论恰好研究了观察者计算能力受限时的信息价值，提供了比“图像包含更多信息”更准确的理论语言。:chatgpt-content-reference{index="6"}

因此，你们真正可以检验的是：

> **视觉编译是否让有限能力、有限上下文的模型，更容易利用已有的诊断信息？**

### 2. 一个可操作的优化目标

不建议一开始就在高维 telemetry 或像素上直接估计 mutual information。可以先定义可测量的任务目标：

\[
\min_{\theta}
\mathbb{E}
\left[
\mathcal L_{\mathrm{RCA}}
\big(f_\phi(D_\theta(X)),Y\big)
\right]
+
\lambda C(D_\theta(X))
+
\mu \mathcal L_{\mathrm{faithfulness}},
\]

其中：

- \(f_\phi\)：冻结的诊断 VLM；
- \(D_\theta\)：可学习的证据选择与渲染过程；
- \(\mathcal L_{\mathrm{RCA}}\)：根因排序、实体类型和粒度损失；
- \(C\)：实际 token、计算或延迟成本；
- \(\mathcal L_{\mathrm{faithfulness}}\)：数字、实体关系、时间关系等被错误呈现的惩罚。

这是一个**诊断任务定义的 rate–distortion 问题**，而不是以重建所有原始数据为目标的压缩。

### 3. 最值得尝试的创新：把压缩单元从“异常点”改成“诊断对照组”

例如，一个 node 出问题时，最大的延迟可能出现在入口服务。只保留异常分数最高的几个 service，会保留“症状最严重的地方”，却可能丢失根因。

我建议把选择单元设计成：

> **候选实体 + 对照实体 + 时间变化 + 跨模态支持 + 部署/调用关系。**

一个证据组可以包含：

- 某个 pod 的异常；
- 同 service、不同 node 上的正常副本；
- 同 node、不同 service 上是否同时异常；
- 该 pod 的 caller/callee 延迟差异；
- 对应时间段出现的日志模板和关键参数。

这里的新意候选不是“保留正常数据”本身，而是：

> **在有限预算下，联合保留能够区分竞争性根因解释的证据组。**

这比“选 top-k 异常指标”更接近诊断任务本质。

### 4. 决定性实验

比较相同预算下的：

| 压缩目标 | 选择策略 |
|---|---|
| 重建保真 | 保留整体曲线形态、主要统计量 |
| 异常保真 | 保留异常分数最大的观测 |
| 覆盖保真 | 尽量覆盖更多实体、模态和时间段 |
| **诊断保真** | 保留区分候选根因的对照关系 |

如果你们能证明：**诊断导向压缩在相同预算下更好，或者在相同准确率下显著更省成本**，就有一个完整故事。

**最大风险：** 当前失败可能主要来自模型推理，而不是信息缺失。2026 年一项 RCA 分析工作也报告了推理和证据解释方面的瓶颈。因此，必须先做阶段性错误分析，不能预设压缩就是唯一瓶颈。:chatgpt-content-reference{index="7"}

---

## 路线 B：跨系统不变表示——学习故障机制，而不是记忆 service name

### 核心研究问题

> **同一类故障机制，换了名称、模板、部署关系和系统后，模型还能认出来吗？**

你们的数据异构性非常适合这条路线，但必须把不同类型的泛化拆开。

### 1. 区分三种变化

**名称变化：** `checkoutservice` 改成 `service_17`，拓扑和行为不变。

**语义等价的 schema 变化：** 同一类 CPU 指标换字段名、单位、采样频率。

**机制或结构变化：** 服务新增副本、迁移 node、调用路径变化，或者出现训练时没有的故障类型。

这三种不能混成一个“cross-dataset”分数。

### 2. 推荐的表示：保留语义，消除无关标识

构造统一、带类型的证据结构，例如：

```text
entity_type: pod
entity_id: E17
belongs_to_service: E3
hosted_on_node: E42

signal_semantics: CPU utilization
unit: ratio
change: sustained increase
relative_to_peers: unusually high
onset: before downstream latency increase

source_refs: [...]
```

这里应当去除的是容易形成捷径的任意标识，而不是 CPU、延迟、单位、错误类型等真实语义。

输出使用候选实体指针，最后映射回原始名称，避免训练一个只能输出固定 service vocabulary 的分类器。

### 3. 可以检验的性质：标识符置换等变性

对于仅改变实体名称的置换 \(\pi\)，期望：

\[
F(\pi X)=\pi F(X).
\]

直观解释：

> 把系统里所有名字一致地替换，答案应该只是跟着改名，而不应该换成另一个根因。

Deep Sets 提供了处理集合对称性的基础，但你们还需要结合有类型的实体关系和原始 ID 映射。单纯使用一个 permutation-invariant 模块，不等于整个 pipeline 已经具备这种性质。:chatgpt-content-reference{index="8"}

### 4. 可尝试的方法

训练时随机重命名、schema 等价变换、布局随机化，以及按系统/故障家族进行鲁棒优化，都可以作为工具；但要和强 ERM 基线比较。Group DRO、DomainBed 已表明，这些泛化问题有成熟的方法学背景，不能把普通域泛化训练本身当作全新贡献。:chatgpt-content-reference{index="9"}

**真正的贡献候选是：**

> 一种同时保持故障语义、实体关系和输出可追溯性的表示，并通过分解后的跨系统测试验证它消除了哪些捷径。

**最大风险：** AIOps2022→AIOps2025 的提升可能主要是同一系统家族的迁移，不能独立支撑“对任意新微服务系统泛化”。

---

## 路线 C：传播结构保真——压缩图，但不能把根因和症状压成同一种东西

### 核心研究问题

> **哪些结构关系一旦被摘要或可视化丢掉，根因就会与传播症状混淆？**

### 1. 不要把 service–pod–node 简化成一棵树

从建模上，至少有几种不同关系：

```text
service A calls service B
pod P belongs to service A
pod P is hosted on node N
multiple pods share node N
span S is a child of span R
```

一个 service 可以跨多个 node，一个 node 可以承载多个 service 的 pod。因此，应优先考虑**有类型的异构图，以及必要的共享资源超边**，而不是强行构造单一层级树。

你们旧数据文档也明确区分了 caller→callee 依赖、node→pod 部署关系，以及 TiDB 内部控制/存储关系；这些边不能一概当作普通 RPC。:chatgpt-content-reference{index="10"} :chatgpt-content-reference{index="11"}

### 2. 创新不应只是“用了超图”

CHASE 已研究多模态微服务 RCA 的异构图和超图。因此，“GNN 换成 hypergraph”本身并不足够。:chatgpt-content-reference{index="12"}

更有价值的问题是：

> **压缩后的图，是否仍能区分同一服务故障、单副本故障、宿主 node 故障和下游依赖故障？**

例如，保留某条传播路径时，不能只保留路径上的异常节点，还可能必须保留路径外的正常对照副本。

### 3. Dashboard 可以围绕竞争性解释组织

与其展示一张大而复杂的全局调用图，可以展示几组“可区分解释”的证据：

| 候选解释 | 支持或反驳它的观测 |
|---|---|
| Service 级故障 | 多个 node 上的该 service 副本是否一起异常？ |
| Pod 级故障 | 同 service 其他副本是否正常？ |
| Node 级故障 | 同 node 上不同 service 的 pod 是否共同异常？ |
| 下游依赖故障 | caller 的异常是否主要来自等待 callee？ |

这实际上是把 dashboard 从“异常展示板”变为“竞争性诊断解释的证据板”。

### 4. 验证边界必须清楚

**调用图不是因果图，时间先后也不自动构成因果证明。**

删除图中的一个 panel、替换一段曲线，只能测试模型是否依赖该输入，不能直接证明真实系统中的干预因果关系。

OpenRCA 2.0 已利用已知故障注入进行传播路径的正向验证，你们可以借鉴其评测思想，但不要把未经验证的相关路径叫作 causal ground truth。:chatgpt-content-reference{index="13"}

**这条路线特别适合 SE 论文：** 它关注的是软件系统特有的调用、部署和传播机制，而不是通用图片分类。

---

## 路线 D：学习“展示什么”，而不是让模型反复“想什么”

### 核心研究问题

> **冻结诊断模型，只训练一个小型 dashboard 编译器，能否提高准确率—成本效率？**

这条路线最适合融入你们此前考虑的小模型生成 dashboard、较大 VLM 诊断的架构。

你们此前的 EvoRCA 快照也没有显示额外 agent 循环具有稳定优势，因此没有必要为了使用 RL 而把推理流程改成多轮 agent。:chatgpt-content-reference{index="14"}

### 1. 推荐结构

```text
原始 telemetry
    ↓
确定性的提取器与统一证据表
    ↓
小模型选择证据组、粒度、布局和分辨率
    ↓
受约束的 dashboard DSL
    ↓
确定性渲染
    ↓
冻结 VLM 诊断一次
```

这里是**诊断阶段单轮**，不是整个 pipeline 只有一次模型调用。小模型编译和 VLM 诊断的成本都要统计。

### 2. 首先把它看作 contextual bandit

如果策略读取证据后，一次性选定 dashboard，最终得到诊断 reward，那么任务层面更接近 **contextual bandit**，不需要一开始就建成长时程 RL 环境。:chatgpt-content-reference{index="15"}

动作可以包含：

\[
a=
(\text{证据组},\text{图表类型},\text{实体粒度},
\text{布局},\text{分辨率}).
\]

### 3. 推荐训练顺序

**先搜索有限模板空间，再考虑生成策略。**

先设计例如 16–32 个合法配置，检查不同 incident 的最佳配置是否确实不同。如果“每个 case 的最佳配置”与“全局最佳固定配置”几乎没有差距，那么训练复杂策略的潜在收益就很有限。

随后再考虑：

> 模板选择器 → SFT/LoRA 输出 DSL → 偏好优化 → 必要时 GRPO。

DPO、LoRA 是可用的训练工具；ThinkFL 已经把 GRPO 用于 RCA，因此你们的区分点应是**优化诊断输入的编译过程**，而不是“RCA 也用了 RL”。:chatgpt-content-reference{index="16"}

### 4. Reward 必须避免只优化表面分数

可以采用：

\[
r =
r_{\mathrm{ranking}}
-\lambda c_{\mathrm{actual}}
-\mu p_{\mathrm{invalid}}
-\nu p_{\mathrm{unsupported}}.
\]

其中分别对应根因排序、实际成本、非法渲染，以及 dashboard 出现原始数据不支持的数字或关系。

还应加入跨名称、跨布局扰动的稳定性评估，避免策略学习到“把某些实体放在左上角，VLM 就更容易选它”的投机行为。

### 5. 一个必须有的强对照

> **让同一个小模型直接输出根因，而不是生成 dashboard。**

否则，编译器可能已经完成了 RCA，再通过颜色、位置或标题把答案暗示给 VLM。那研究贡献可能是“小模型诊断器”，而不是“视觉表示”。

还必须比较**同一 DSL 的文本序列化版本**。若文本也同样有效，收益可能来自证据组织，而非视觉编码。

---

## 路线 E：诊断导向的数据摘要——让 120GB 真正成为系统研究问题

### 核心研究问题

> **能否以受控的扫描、内存和存储成本，保留稀有但关键的诊断证据？**

这条路线可以作为 A 的底层，也可以单独发展为系统论文。

### 1. 不同 telemetry 应使用不同摘要

| 模态 | 应优先保留什么 | 容易犯的错误 |
|---|---|---|
| Metrics | 变化点、尾部分位数、持续时间、相对正常副本的差异 | 只保留均值，抹平短时故障 |
| Logs | 模板变化、稀有错误、关键参数、实体与时间对应 | 所有变量都替换成通配符，删除真正的故障线索 |
| Traces | 异常路径、调用结构变化、关键 span、caller/callee 对照 | 只按慢请求采样，缺少正常对照 |
| Topology | 类型关系、共享资源组、关键传播结构 | 只保留“最异常节点”的诱导子图 |

Drain、Logzip、DDSketch、Sifter 分别提供了日志解析、日志压缩、分位数摘要和 trace 采样的基础。但它们的原始目标并不等于你们的诊断保持目标。:chatgpt-content-reference{index="17"}

### 2. 可尝试的创新

设计一种 **diagnostic coreset / diagnostic sketch**：

> 不求重建所有 telemetry，而求保留足以区分主要根因解释的少量证据及其来源索引。

值得重点测试的是：

**均匀采样、异常优先采样、稀有事件采样、结构多样性采样、诊断对照组采样，谁在同样预算下保留更多有效根因证据？**

这里还存在一个有价值的跨模态问题：单独看不重要的日志和指标，联合起来可能很重要。PID 提供了冗余、独有信息和协同信息的概念框架，但不建议直接把高维 PID 数值估计当作项目第一阶段的核心实现。:chatgpt-content-reference{index="18"}

### 3. 什么时候它能成为独立主线？

当你们能够同时展示：

> 输入规模增加 → 处理成本受控 → 关键证据保留率稳定 → RCA 性能稳定。

只把 CSV 转成 Parquet，或者使用现成 sketch，属于必要工程工作，但不足以独立构成这个故事。

---

## 路线 F：可验证、可降级的诊断——证据不足时不要假装知道

### 核心研究问题

> **当 dashboard 只支持某个 service 有问题、却无法区分具体 pod 时，系统能否输出正确粒度和可信的不确定性？**

这条路线对多粒度标签特别有价值。

### 1. Grounding 应贯穿整个表示过程

建议每个图形元素都保留：

```text
raw source
  → extracted observation
  → evidence group
  → rendered panel / glyph
  → cited diagnostic evidence
```

这样可以检查模型引用的曲线、实体或关系是否真的存在。

再用两类测试分离“看懂”和“诊断”：

**感知测试：** 哪个实体最先升高？某条边连接谁？哪个副本仍正常？

**诊断测试：** 为什么这些观测支持 node 故障，而不是 service 故障？

ChartQA、PlotQA 和 DashboardQA 提供了图表读取方面的任务启发；ERASER 则提供了证据充分性和删除证据后变化的评估思路。它们都不能直接替代 RCA 的因果正确性验证。:chatgpt-content-reference{index="19"}

### 2. 缺失模态可以成为现实测试，而不只是预处理异常

你们旧审计曾移除 AIOps2025 的 39 个缺模态 case，其中 23 个没有 trace，16 个同时没有 log 和 trace。可以保留“完整三模态主实验”，同时增加“包含缺模态的源数据实验”，避免只在更容易的完整观测条件下评估。:chatgpt-content-reference{index="20"}

### 3. 输出应允许不同确定程度

例如：

```text
可确认：service A
无法可靠区分：pod A1 / A2
缺失证据：pod-level trace attribution
```

然后评估风险—覆盖率，而不是一律强迫模型输出唯一实体。Conformal Risk Control 可以提供校准思路，但它的保证依赖相应统计条件，不能直接宣称对任意跨系统分布变化都有效。:chatgpt-content-reference{index="21"}

### 4. 外部攻击还带来另一个问题

“攻击导致系统故障”与“攻击者通过 telemetry 操纵 RCA 模型”是不同任务。后者已有 USENIX Security 2026 工作研究。日志被渲染成图片，也不意味着其中的恶意指令失去作用，因此应把日志视为不可信数据，而不是控制指令。:chatgpt-content-reference{index="22"}

---

# 五、哪些方向适合当工具，暂时不适合当核心故事？

## 1. 自监督训练：值得做，但不要把数据体积当作标签规模

你们的大量 telemetry 可用于预训练指标表示、学习正常行为、生成图表事实问答，或者学习跨模态时间对应。TS2Vec、Chronos、CLIP 和 TVDiag 都提供了相关方法来源。:chatgpt-content-reference{index="23"}

但要注意：

> 为同一个 incident 生成一千张 dashboard，并不会得到一千个独立故障样本。

同样，使用未标注的测试系统数据训练编码器，也需要明确说明是 transductive setting，不能仍宣称完全未见系统泛化。

## 2. Image generation：优先生成程序，不要自由生成事实

我建议生成的是：

> panel specification、布局、图表类型、证据引用和样式参数。

真实数值、坐标、边关系则由确定性渲染器生成。Vega-Lite 和 Draco 是这种图形语法与约束思路的合适起点。:chatgpt-content-reference{index="24"}

自由生成图片容易让你们难以判断：性能变化来自诊断表示，还是数字、图例、曲线和边被改写。对于这个任务，图像必须首先忠实，其次才是美观。

## 3. Topological data analysis：可以探索，但优先级较低

Topological Autoencoders 研究拓扑保持的表示学习，但“保留某种拓扑性质”不自动等于“保留根因定位能力”。:chatgpt-content-reference{index="25"}

只有在初步分析已经显示某种结构变化对故障辨识很关键时，再尝试持久同调、拓扑特征等。否则容易成为难以证明必要性的技术装饰。

---

# 六、可以尝试的论文 storyline

以下标题是选题草案，不是已有论文标题。

| Storyline | 中心主张 | 必须拿出的证据 | 我的优先级 |
|---|---|---|---|
| **Compress for Diagnosis, Not Reconstruction** | 面向诊断的压缩，比面向重建或异常强度的压缩更有效 | 完整成本—准确率曲线；关键对照证据保留；强文本基线 | **最高** |
| **Learn What to Show, Not How to Diagnose** | 冻结诊断器，通过学习证据与布局改善诊断 | 固定模板 vs 学习策略；小模型直接诊断；同 DSL 文本对照 | **高，适合作为第一条的实现** |
| **Same Failure, Different Systems** | 去除名称捷径，保留故障语义与实体关系 | 名称、schema、拓扑、系统、故障类型分别留出测试 | **高** |
| **Preserve Propagation, Not Just Anomalies** | 保留传播及对照结构，才能区分根因和症状 | 结构消融；根因粒度测试；人工或注入支持的路径验证 | **高，偏 SE** |
| **When Dashboards Help—and When They Hurt** | 视觉表示的价值取决于预算、任务、模型和图形复杂度 | 公平的表示对照；感知/选择/推理错误分解；可重复结论 | **值得保留的实证路线** |
| **Diagnose What Is Observable** | 诊断粒度和置信程度应受可观测证据约束 | 缺模态、证据不足、风险—覆盖率与分层正确性 | 中高，可能单独成文 |
| **Rare Evidence at Scale** | 海量数据处理中保住少量关键证据，比平均保真更重要 | 可扩展性、稀有事件保留、端到端 RCA 收益 | 中高，偏系统 |

### 我的组合建议

**第一选择：**

> **A：诊断导向压缩作为核心问题，D：学习编译器作为实现，B：跨系统泛化作为关键验证。**

不要把它写成三个独立创新点的拼盘，而应形成一条因果链：

> 固定摘要丢失了诊断对照关系 → 学习选择和编译这些关系 → 在名称、schema 和系统变化下仍保留诊断能力。

**第二选择：**

> **C：传播结构保真作为核心，F：证据可验证性作为必要评测。**

这条路线的软件工程问题更鲜明。

就选题匹配而言，我会优先把这两类故事面向 **ICSE/FSE/ASE** 打磨；若面向 **ICLR/ICML/NeurIPS**，则需要进一步把“受限解码器下的任务导向表示学习”做成更一般的问题，而不仅是三个 RCA 数据集上的应用结果。面向 **CVPR** 则需要真正的视觉表示、感知或视觉学习贡献，单纯接入 VLM 并不够。这是选题判断，不是接收概率预测。

---

# 七、建议怎样开展实验，才能尽早知道这条路线是否值得投入？

## 1. 先建立“相同事实，不同表示”的基础实验

这是整个项目最重要的对照。

从同一份证据表生成：

| 条件 | 表示 |
|---|---|
| A | 结构化文本 |
| B | LLMLingua-2 等方法压缩后的文本 |
| C | 相同文本直接渲染成图片 |
| D | 相同证据转换成统计图、关系图和表格 |
| E | 图像 + 简短实体图例的混合表示 |

这样可以区分：

> **文本压缩收益、光学压缩收益、图形关系表达收益，以及混合表示收益。**

不能给图像提供 topology、正常对照和对齐时间轴，却只给文本提供几个异常分数，然后将性能差异归因于“视觉”。

同时，Glyph 和 DeepSeek-OCR 的结果不能直接当作任意冻结 VLM 的压缩能力；应测量你们实际模型的输入处理和推理成本。:chatgpt-content-reference{index="26"}

## 2. 把证据选择和视觉编码拆开

建议至少做这个 2×2：

|  | 固定证据选择 | 学习证据选择 |
|---|---|---|
| 文本编码 | 基线 | 检验证据选择收益 |
| 视觉编码 | 检验视觉收益 | 完整方法 |

否则，即使完整方法有效，也无法回答“究竟是选得更好，还是画得更好”。

对三种 telemetry，还应比较单模态、简单融合和真正交互建模。跨模态模型取得更高分，并不自动证明它使用了跨模态交互；已有工作专门指出这一评估困难。:chatgpt-content-reference{index="27"}

## 3. 成本要统计端到端，而不是只看最终 VLM 的输入 token

至少记录：

\[
T_{\mathrm{total}}
=
T_{\mathrm{extract}}
+
T_{\mathrm{select}}
+
T_{\mathrm{render}}
+
T_{\mathrm{vision}}
+
T_{\mathrm{prefill}}
+
T_{\mathrm{decode}}.
\]

另外记录小模型输入/输出 token、VLM 文本与视觉 token、峰值内存/显存，以及离线构建成本和在线诊断成本。

**PNG 文件小，不等于视觉 token 少；最终 prompt 短，也不等于整个 pipeline 便宜。**

原始唯一数据体积、解压体积、per-case 缓存体积也应分开，避免把重叠窗口的复制量算成独立数据规模。

## 4. 划分与标签隔离先于训练

你们应特别处理：

- 原始 train/test 划分、相邻时间窗与同 cloudbed 的重叠；
- metadata、文件名、故障注入配置、ground-truth explanation 的泄漏；
- 以真实故障起止时间裁剪的 oracle window，与实际告警时刻可获得窗口的区别。

旧数据格式中，`metadata.json` 包含根因与故障类型，附件可能包含注入配置；AIOps2025 的窗口也使用了 ground-truth start/end。因此必须通过输入白名单隔离，而不能直接把整个 case 目录交给模型。:chatgpt-content-reference{index="28"} :chatgpt-content-reference{index="29"}

训练 reward 使用训练集标签是正常监督；把标签内容或测试集信息混入模型输入、选择器拟合或 renderer 调参才是问题。

## 5. 指标和错误分析要对应你们的贡献

主指标可以是 Top-1、MRR、Recall@k，但还应报告：

| 研究目标 | 附加指标 |
|---|---|
| 压缩有效 | 准确率—实际成本曲线 |
| 跨系统 | 每个系统、故障类型、根因粒度的宏平均 |
| 粒度正确 | 严格 service/pod/node 正确率，不能只报宽松 service 命中 |
| 证据保持 | 关键证据与对照关系保留率 |
| 视觉可读 | 数值、实体、时间顺序、边关系的读取正确率 |
| 可验证诊断 | 证据引用有效率、经验证的路径支持 |
| 可靠输出 | 风险—覆盖率、错误细粒度断言率 |
| 可重复性 | 多次推理与按故障会话/时间组进行的置信区间 |

有多个真实根因时再使用集合指标；不要把同一根因的跨层级标签误当作 multi-root。

### 最值得先完成的五个判定实验

| 判定 | 结果意味着什么 |
|---|---|
| VLM 能否稳定读对图上的事实？ | 读不对时，先修表示，不要直接加 RL |
| 不同 incident 是否确实需要不同 dashboard？ | 没有个性化收益空间时，固定模板可能更合适 |
| 同事实、同预算下视觉是否有收益？ | 没有时，考虑混合表示或把主线转向证据选择 |
| 对照组选择是否优于异常 top-k？ | 决定“诊断导向压缩”是否有机制上的支持 |
| 重命名和跨系统测试是否仍有效？ | 决定收益是否主要来自数据集捷径 |

**不必要求视觉在所有条件下获胜。** 如果它只在低预算、强结构关系或特定故障机制下有优势，识别并解释这些适用条件，也可以成为有价值的研究结果。

---

# 八、完整参考论文清单：56 篇

下面列出本文实际使用的论文与报告。编号与前文对应；每条后的来源可以打开论文或正式出版页面。

## A. RCA、故障定位与 benchmark

**[1] Rethinking the Evaluation of Microservice RCA with a Fault Propagation-Aware Benchmark.** FSE 2026；arXiv:2510.04711。AegisLab/RCABench 的核心来源，重点阅读故障传播、数据验证和标签设计。:chatgpt-content-reference{index="30"}

**[2] A Multi-Dataset Benchmark for Evaluating LLM Agents in Microservice Failure Diagnosis.** 2026；arXiv:2606.29193。多数据集诊断评测，与 AIOps2025 及异构环境评估直接相关。:chatgpt-content-reference{index="31"}

**[3] RCAEval: A Benchmark for Root Cause Analysis of Microservice Systems with Telemetry Data.** WWW Companion 2025；arXiv:2412.17015。用于理解公开 RCA benchmark 和基线组织，不意味着必须加入你们的主实验。:chatgpt-content-reference{index="32"}

**[4] OpenRCA: Can Large Language Models Locate the Root Cause of Software Failures?** ICLR 2025。LLM RCA 的任务设计和评测参考。:chatgpt-content-reference{index="33"}

**[5] OpenRCA 2.0: From Outcome Labels to Causal Process Supervision.** 2026；arXiv:2606.27154。传播路径标注与 grounded diagnosis 的重要近邻。:chatgpt-content-reference{index="34"}

**[6] Eadro: An End-to-End Troubleshooting Framework for Microservices on Multi-source Data.** ICSE 2023；arXiv:2302.05092。多源 telemetry 故障诊断基线。:chatgpt-content-reference{index="35"}

**[7] Nezha: Interpretable Fine-Grained Root Causes Analysis for Microservices on Multi-modal Observability Data.** ESEC/FSE 2023。细粒度、多模态、可解释 RCA 的重要近邻。:chatgpt-content-reference{index="36"}

**[8] Robust Failure Diagnosis of Microservice System through Multimodal Data.** DiagFusion；arXiv:2302.10512，2023。多模态表示、数据增强与故障诊断。:chatgpt-content-reference{index="37"}

**[9] MicroRCA: Root Cause Localization of Performance Issues in Microservices.** NOMS 2020。性能故障与系统关系建模的经典基线。:chatgpt-content-reference{index="38"}

**[10] BARO: Robust Root Cause Analysis for Microservices via Multivariate Bayesian Online Change Point Detection.** FSE 2024；arXiv:2405.09330。变化点驱动的 RCA，适合作为强统计基线。:chatgpt-content-reference{index="39"}

**[11] Practical Root Cause Localization for Microservice Systems via Trace Analysis.** TraceRCA；IWQoS 2021。Trace 驱动的根因定位。:chatgpt-content-reference{index="40"}

**[12] TraceDiag: Adaptive, Interpretable, and Efficient Root Cause Analysis on Large-Scale Microservice Systems.** ESEC/FSE 2023 Industry Track；arXiv:2310.18740。图剪枝、适应性诊断与效率，是 RL 选择路线的重要近邻。:chatgpt-content-reference{index="41"}

**[13] CHASE: A Causal Hypergraph based Framework for Root Cause Analysis in Multimodal Microservice Systems.** arXiv:2406.19711，2024/2025 版本。异构图、超图和多模态 RCA。:chatgpt-content-reference{index="42"}

**[14] TVDiag: A Task-oriented and View-invariant Failure Diagnosis Framework with Multimodal Data.** arXiv:2407.19711，2024/2025 版本。任务导向融合、跨模态对比学习与观测缺失增强。:chatgpt-content-reference{index="43"}

**[15] ThinkFL: Self-Refining Failure Localization for Microservice Systems via Reinforcement Fine-Tuning.** TOSEM 2026；arXiv:2504.18776。小模型 RCA 强化微调的重要近邻。:chatgpt-content-reference{index="44"}

**[16] MetaRCA: A Generalizable Root Cause Analysis Framework for Cloud-Native Systems Powered by Meta Causal Knowledge.** 2026；arXiv:2603.02032。跨系统知识和因果结构迁移。:chatgpt-content-reference{index="45"}

**[17] TAMO: Fine-Grained Root Cause Analysis via Tool-Assisted LLM Agent with Multi-Modality Observation Data in Cloud-Native Systems.** 2025；arXiv:2504.20462。工具辅助、多模态、细粒度 RCA。:chatgpt-content-reference{index="46"}

**[18] From General Agents to RCA Experts: A Self-Evolving Harness for Root Cause Analysis.** OpsHarness；2026；arXiv:2608.25661。冻结通用模型、演化外部诊断流程的近邻。:chatgpt-content-reference{index="47"}

**[19] How Far Can Root Cause Analysis Go on Real-World Telemetry Data?** 2026；arXiv:2607.13548。用于分析 RCA 的证据、推理和数据歧义瓶颈。:chatgpt-content-reference{index="48"}

## B. 信息论、任务导向压缩与视觉压缩

**[20] Coding Theorems for a Discrete Source With a Fidelity Criterion.** Claude E. Shannon，1959。Rate–distortion 理论基础。:chatgpt-content-reference{index="49"}

**[21] The Information Bottleneck Method.** Allerton 1999；arXiv:physics/0004057。保留任务相关信息、压缩输入表示的基础。:chatgpt-content-reference{index="50"}

**[22] Deep Variational Information Bottleneck.** ICLR 2017；arXiv:1612.00410。可学习信息瓶颈的变分方法。:chatgpt-content-reference{index="51"}

**[23] A Theory of Usable Information Under Computational Constraints.** ICLR 2020；arXiv:2002.10689。解释“表示改变后，受限模型更能利用信息”的关键理论来源。:chatgpt-content-reference{index="52"}

**[24] Nonnegative Decomposition of Multivariate Information.** 2010；arXiv:1004.2515。冗余、独有与协同信息的 PID 框架。:chatgpt-content-reference{index="53"}

**[25] LLMLingua-2: Data Distillation for Efficient and Faithful Task-Agnostic Prompt Compression.** Findings of ACL 2024。必须考虑的文本压缩对照。:chatgpt-content-reference{index="54"}

**[26] DeepSeek-OCR: Contexts Optical Compression.** 2025；arXiv:2510.18234。文本的视觉/光学上下文压缩。:chatgpt-content-reference{index="55"}

**[27] Glyph: Scaling Context Windows via Visual-Text Compression.** 2025；arXiv:2510.17800。文本转图像与渲染配置优化，是你们最接近的非 RCA 工作之一。:chatgpt-content-reference{index="56"}

## C. Dashboard、图表理解、多模态与时序表示

**[28] DashboardQA: Benchmarking Multimodal Agents for Question Answering on Interactive Dashboards.** 2025；arXiv:2508.17398。多面板 dashboard 理解与交互问答。:chatgpt-content-reference{index="57"}

**[29] ChartQA: A Benchmark for Question Answering about Charts with Visual and Logical Reasoning.** 2022；arXiv:2203.10244。图表视觉读取和逻辑推理评测。:chatgpt-content-reference{index="58"}

**[30] ChartGemma: Visual Instruction-tuning for Chart Reasoning in the Wild.** 2024；arXiv:2407.04172。图表指令微调与训练数据构造。:chatgpt-content-reference{index="59"}

**[31] PlotQA: Reasoning over Scientific Plots.** WACV 2020；arXiv:1909.00997。数值、坐标和科学图表推理。:chatgpt-content-reference{index="60"}

**[32] VisionTS: Visual Masked Autoencoders Are Free-Lunch Zero-Shot Time Series Forecasters.** ICML 2025；arXiv:2408.17253。时序转视觉表示的相关路线，但任务是预测而非 RCA。:chatgpt-content-reference{index="61"}

**[33] Harnessing Vision-Language Models for Time Series Anomaly Detection.** 2025；arXiv:2506.06836。VLM 用于时间序列异常检测。:chatgpt-content-reference{index="62"}

**[34] Vega-Lite: A Grammar of Interactive Graphics.** IEEE TVCG 2017。受约束的图形语法和确定性可视化。:chatgpt-content-reference{index="63"}

**[35] Formalizing Visualization Design Knowledge as Constraints: Actionable and Extensible Models in Draco.** IEEE TVCG 2019。把可视化设计知识表达为约束。:chatgpt-content-reference{index="64"}

**[36] Does my multimodal model learn cross-modal interactions? It’s harder to tell than you might think!** EMNLP 2020。用于设计真正检验跨模态交互的实验。:chatgpt-content-reference{index="65"}

**[37] TS2Vec: Towards Universal Representation of Time Series.** AAAI 2022；arXiv:2106.10466。时序自监督表示学习。:chatgpt-content-reference{index="66"}

**[38] Chronos: Learning the Language of Time Series.** TMLR 2024；arXiv:2403.07815。时序基础模型路线，可用于数值表示基线或后端。:chatgpt-content-reference{index="67"}

**[39] Time-MMD: Multi-Domain Multimodal Dataset for Time Series Analysis.** NeurIPS 2024 Datasets and Benchmarks；arXiv:2406.08627。多域、多模态时序任务的评测设计参考。:chatgpt-content-reference{index="68"}

**[40] Learning Transferable Visual Models From Natural Language Supervision.** CLIP；ICML 2021；arXiv:2103.00020。跨模态对齐的基础参考，不应直接假设其目标适合全部 telemetry 信息。:chatgpt-content-reference{index="69"}

## D. 日志、调用链、压缩与流式处理

**[41] Drain: An Online Log Parsing Approach with Fixed Depth Tree.** ICWS 2017。在线日志模板解析。:chatgpt-content-reference{index="70"}

**[42] Logzip: Extracting Hidden Structures via Iterative Clustering for Log Compression.** ASE 2019；arXiv:1910.00409。日志结构提取与压缩。:chatgpt-content-reference{index="71"}

**[43] DDSketch: A Fast and Fully-Mergeable Quantile Sketch with Relative-Error Guarantees.** PVLDB 2019；arXiv:1908.10693。可合并分位数摘要，适合指标流处理。:chatgpt-content-reference{index="72"}

**[44] Dapper, a Large-Scale Distributed Systems Tracing Infrastructure.** Google 技术报告，2010。分布式 tracing 基础。:chatgpt-content-reference{index="73"}

**[45] Sifter: Scalable Sampling for Distributed Traces, without Feature Engineering.** SoCC 2019。大规模调用链采样与多样性保留。:chatgpt-content-reference{index="74"}

## E. 强化学习、微调、泛化与结构学习

**[46] A Contextual-Bandit Approach to Personalized News Article Recommendation.** WWW 2010；arXiv:1003.0146。单次上下文决策的方法基础，可迁移为 dashboard 配置选择。:chatgpt-content-reference{index="75"}

**[47] Direct Preference Optimization: Your Language Model is Secretly a Reward Model.** NeurIPS 2023；arXiv:2305.18290。利用 dashboard 优劣偏好训练生成策略。:chatgpt-content-reference{index="76"}

**[48] LoRA: Low-Rank Adaptation of Large Language Models.** ICLR 2022；arXiv:2106.09685。小模型编译器的参数高效微调。:chatgpt-content-reference{index="77"}

**[49] Distributionally Robust Neural Networks for Group Shifts: On the Importance of Regularization for Worst-Case Generalization.** ICLR 2020；arXiv:1911.08731。Group DRO 与最差群组表现。:chatgpt-content-reference{index="78"}

**[50] In Search of Lost Domain Generalization.** ICLR 2021；arXiv:2007.01434。DomainBed、强基线和域泛化模型选择。:chatgpt-content-reference{index="79"}

**[51] Deep Sets.** NeurIPS 2017；arXiv:1703.06114。集合不变性与实体顺序/标识对称性的基础。:chatgpt-content-reference{index="80"}

**[52] Topological Autoencoders.** ICML 2020。拓扑保持表示学习的探索性参考。:chatgpt-content-reference{index="81"}

## F. 可靠性、解释性与安全

**[53] Conformal Risk Control.** ICLR 2024；arXiv:2208.02814。选择性输出、候选集合与风险校准的参考。:chatgpt-content-reference{index="82"}

**[54] ERASER: A Benchmark to Evaluate Rationalized NLP Models.** ACL 2020；arXiv:1911.03429。证据充分性、完整性与解释评测。:chatgpt-content-reference{index="83"}

**[55] An Evaluation of Similarity Coefficients for Software Fault Localization.** PRDC 2006。传统故障定位中成功/失败执行对照的基础参考；迁移到 traces 时需重新定义观测与标签。:chatgpt-content-reference{index="84"}

**[56] When AIOps Become “AI Oops”: Subverting LLM-driven IT Operations via Telemetry Manipulation.** USENIX Security 2026。Telemetry 操纵与 LLM 运维系统安全。:chatgpt-content-reference{index="85"}

---

## 最后的判断

**我不会优先押注“dashboard 比文本更好”，也不会优先押注“加 RL 就能提升 RCA”。**

我会押注一个更具体、也更容易被严谨验证的假设：

> **当前 RCA 摘要通常保留最明显的异常，却容易丢失区分根因与传播症状所需的对照关系。通过诊断导向的证据选择与受约束视觉编译，可以在有限预算下保留这些关系，并降低对系统名称、模板和固定拓扑的依赖。**

这条主线同时解释了：**为什么需要压缩、为什么需要结构、为什么可能需要视觉、为什么需要学习，以及为什么你们这三个异构数据集适合验证它。**