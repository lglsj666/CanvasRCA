# What to do After RQ1.1

## Round 1

### User:
```
Me: 我的想法是做一个双agent系统，一个agent用来画dashboard（slm，10B以下）。另一个agent用来做rca（vlm，也就是我们使用的gemma的27B和qwen3.8-27B）。我的想法是确定一个dashboard的设计空间，然后训练dashboard agent来画出最好的dashboard，这样另一个agent可以在不接受训练的情况下达到或者超过sota的性能，并且节省大量token，并且dashboard的表现与信息对等的文本的表现接近或超过。我这么想的原因有三：

1. dashboard agent可以作为一个泛用性的数据处理器，我们训练它学习画dashboard，这样的话不论来了什么样的数据，它都能够将其转换为dashboard，这样一来我们的rca agent就不会受制于新的数据。因为传统方法中，假设我们在一个数据集上训练了rca agent，它不一定在另一个数据集上表现的好。然而dashboard agent只负责将数据转换为其认为最好的表现形式，说不定可以让一切rca cases都变成一个精致的且富有诊断信息且噪声较小的dashboard，从而让rca agent能够在任何rca的数据集下都能表现地很好。
2. 创新性。目前较少有related work这么做。
3. 即使这个方法在全自动的情况下不好，我们也可以将其转变为human-in-the-loop来强行解释我们这个方法的有效性。

根据以上我说的内容，请你再做一下这个任务“canvasRCA（原名visionRCA）的第一阶段的实验已经全部完成，这是其报告和详细结果。对于另一个agent总结的结论，你不一定要采信，而是将原文和所有的数据都看一遍再决定你自己的findings。我们的项目框架准备定为优化单阶段（T = 1，不属于agentic work flow），且暂时只使用一张dashboard图的canvasRCA。我们希望我们的canvasRCA能够在节省大量token的同时，提升rca的performance。根据这份报告，你认为下一步我们应该提出哪些新的research questions，并设计哪些实验？请你去找一下related work，既可以找rca相关的，也可以找dashboard相关的，并且RL，SFT等相关的也可以去找一找。注意，我们不是要证明canvas比纯文本好。我们是要找到如何优化才能使得canvas在节省token的情况下，还能超过state-of-the-art方法，并且其performance超过或者接近相同条件且信息对等时的文本实验arm。也就是说，我们的目标是打败当前rca领域的state-of-the-art，并且让canvas这个实验arm相比同等实验条件下的text实验arm的performance差的没有那么多（也就是说我们要有充分的理由为了节省token而采用canvas，即使它牺牲了一点peroformance，但是这个牺牲并不多，不足以掩盖其节省大量token的advantage），或者甚至performance也超越text。”，并给我一个新的下阶段plan。
```


### Agent:

```# 结论先行

你的双模型方案比“继续微调 RCA VLM”更有研究张力，也更符合第一阶段实验真正暴露出来的问题。我建议把项目的核心重新定义为：

> **CanvasRCA 学习的不是如何让 RCA 模型更会推理，而是如何让一个冻结的 RCA VLM 看到最适合它推理的信息表示。**

更准确的系统表述是：

$$
\text{Raw Telemetry}
\rightarrow
\text{Dashboard Agent}_{<10B}
\rightarrow
\text{One Dashboard Image}
\rightarrow
\text{Frozen RCA VLM}_{27B}
\rightarrow
\text{Root-Cause Ranking}
$$

其中 Dashboard Agent 是一个**任务导向的视觉编译器（task-oriented visual compiler）**，其输出不是自由生成的像素，而是一份受约束的 dashboard program/DSL，再由确定性 renderer 生成一张图。

这里需要提前统一术语：

* 这不是迭代式 agentic workflow，没有 observation–action–observation 循环；
* 它是一个 **two-model feed-forward pipeline**；
* RCA VLM 只调用一次，因此可以写 \(T_{\mathrm{RCA}}=1\)；
* 但整个系统有一次 SLM 调用和一次 VLM 调用，不能声称“整个系统只有一次模型调用”。

我认为最适合的论文定位是：

> **Learning What a Frozen VLM Should See: Task-Oriented Visual Compilation for Token-Efficient Root Cause Analysis**

或者：

> **CanvasRCA: A Learned Visual Compiler for Frozen-VLM Root Cause Analysis**

---

 一、重新阅读第一阶段报告后，我认为最重要的新发现

我重新检查了你上传的 18 页报告中的所有 arm、token 表、repair/break、分数据集结果、QA 分解和 attention 分析。报告列出了原始 trajectories、summary 和分析脚本的位置，但这些原始 artifacts 没有包含在本轮附件中，因此下面可以核查报告表格内部的一致性并据此设计研究，但不能声称已经重新计算每一个 case-level 统计量和 Holm \(p\)-value。

 1. 第一阶段实际上已经给出了“学习 Dashboard Policy”的充分动机

Qwen 上：

| Arm  |   MRR | Input tokens |          相对 T |
| ---- | ----: | -----------: | ------------: |
| T    | 0.499 |       13,937 |             — |
| TPV  | 0.583 |       15,621 | +12.1% tokens |
| V_LG | 0.563 |       15,106 |  +8.4% tokens |
| V_MG | 0.491 |        6,291 | −54.9% tokens |
| V    | 0.375 |        4,902 | −64.8% tokens |

因此，Qwen 的 V_MG 保留了：

$$
\frac{0.491}{0.499}=98.4\%
$$

的全文本 MRR，同时只使用约 45.1% 的输入 token。这已经非常接近你希望的“为了显著节省 token，只接受很小 performance sacrifice”的目标。

但同一表示在 Gemma 上只有：

$$
\frac{0.443}{0.527}=84.1\%
$$

的 MRR retention，尽管它节省了 63.7% token。这说明并不存在天然通用的“最佳 dashboard”；最佳表示很可能是 **receiver-dependent** 的。 

这正好支持训练 Dashboard Agent，而不是继续人工寻找一套固定 template。

---

 2. 现有结果存在很大的 instance-adaptive headroom

V_MG 的平均结果几乎等于 T，但它并不是“所有 case 都比 T 稍差一点”：

* 73 个 top-1 repair；
* 76 个 top-1 break；
* 108 个 case reciprocal rank 提升；
* 114 个 case reciprocal rank 下降。

TPV 和 V_LG 又修复了另外一批 case：

* TPV：92 repairs / 37 breaks；
* V_LG：92 repairs / 44 breaks。

这意味着不同表示在不同 incident 上有明显的互补性。

由此产生一个非常关键、但报告尚未直接回答的问题：

> **是否存在一个 label-blind policy，可以根据 incident 本身的结构，预测当前 case 应该采用哪种内容选择、布局和视觉编码，从而保留不同 dashboard 的 repair，避免它们的 break？**

这是你的 Dashboard Agent 最直接的理论依据。

下一步第一项分析不应该立即训练 SLM，而应该先用原始 trajectory 计算：

$$
\operatorname{MRR}_{\text{Oracle}}
=
\frac{1}{N}
\sum_i
\max_{a\in\mathcal A}
RR_{i,a}
$$

即对每个 case 从现有或新设计集合中选择最优 dashboard 的 oracle upper bound。

如果 per-case oracle 只比最佳固定 dashboard 高 0.01，那么 adaptive builder 的空间有限；如果高 0.10 甚至更多，那么你的方向有非常强的可行性依据。

---

 3. TPV/V_LG 应成为训练信号，而不是最终部署方案

Qwen 上：

* TPV 比 T 高 \(+0.0847\) MRR；
* V_LG 比 T 高 \(+0.0640\) MRR；
* 两者的 repairs 均明显多于 breaks。 

但它们并不节省 token，反而分别增加 12.1% 和 8.4%。所以它们最适合作为：

* Dashboard Agent 的 teacher signal；
* best-of-\(N\) 搜索中的高质量模板；
* 构造 preference pair 的正样本；
* 研究视觉结构为何有效的 mechanism arm。

它们不应该直接作为最终 token-efficiency headline。

---

 4. Full-V 的失败不是“VLM 不看图”，而是 dashboard 没有形成稳定的视觉通信协议

完整 V 中：

* Qwen top-1 从 T 的 188/469 降到 119/469；
* 根因缺席且缺乏匹配证据的 case 从 169 增至 209；
* Gemma 在完整 V 中有 285 个 case 完全遗漏根因；
* Gemma 通常只输出一个候选，存在 candidate-list collapse。

同时，Gemma 对图像的 attention mass 约是 Qwen 的 3.8 倍，却表现更差；header 反而成为高 attention density 区域。

因此问题不是简单的“模型有没有看图”，而是至少包含：

$$
\text{Candidate Coverage}
\rightarrow
\text{Visual Perception}
\rightarrow
\text{Entity Binding}
\rightarrow
\text{Evidence Selection}
\rightarrow
\text{Causal Ranking}
$$

完整 dashboard 同时损害了多个环节。

---

 5. Dashboard Agent 最需要优化的是 composition，而不只是 chart style

报告第 12 页的 region-level heatmap 显示：

* Trace visual 的直接读取能力很强；
* Metrics visual 的 exact-value extraction 很差；
* Logs 的自然语言形式仍然很有竞争力；
* Topology 对 Qwen 明显有帮助，但对 Gemma 没有稳定增益。

而 L2–L4 跨区域任务快速下降，常见错误包括：

* 数值、符号或 bin 抄错；
* topology 邻居集合不完整；
* caller/callee 方向反转；
* 跨区域切换后 entity ID 丢失；
* 第一处错误向后传播。

所以 Dashboard Agent 不应只学习：

* 折线图还是柱状图；
* 颜色、字体；
* panel 大小。

它还必须学习：

* 哪些 evidence 应该相邻；
* 哪些实体应当被共同组织；
* 哪些信息需要精确数字；
* 哪些信息只需要趋势；
* 哪些结构适合图形，哪些适合短文本；
* 如何减少 VLM 的跨区域 identity binding。

---

二、对你提出的三个理由的判断

理由一：Dashboard Agent 可以成为跨数据集的通用数据处理器

这个方向是合理的，但论文中不能直接把它当成既定事实。

Dashboard Agent 一旦通过 root-cause reward 训练，它就不再是完全 task-neutral 的数据处理器，而是整个 RCA 系统的一个 learned front end。它可能学到：

* 通用的 telemetry 表示原则；
* 也可能学到数据集特定的 fault 分布；
* 可能学到 Qwen 或 Gemma 特定的视觉偏好；
* 甚至可能通过候选顺序、颜色或位置隐式编码自己的 root prediction。

因此，最准确的 claim 应该是：

> **Dashboard Agent 是一个跨系统、跨 schema 的 RCA-oriented visual compiler，而不是适用于任意数据任务的通用 dashboard generator。**

MetaRCA 已经把跨系统 generalization 作为核心贡献，利用可复用的 meta causal knowledge，在 252 个公共和 59 个生产 failure 上报告了跨系统保持 80% 以上准确率。你们若要以 generalization 作为主要动机，就必须进行同样严格的 system-held-out evaluation，而不能只做随机 IID split。([arXiv][1])

让 Dashboard Agent 真正具备跨数据集能力的关键不是让它直接解析任意格式的 raw files，而是先建立统一的 telemetry primitives：

* `entity`
* `timeseries`
* `span/operation`
* `event/log template`
* `directed dependency edge`
* `entity hierarchy`
* `normal/current window`
* `missingness`
* `unit/schema metadata`

新数据集只需映射到这些 primitives，Dashboard Agent 再决定如何组织和表达。


理由二：创新性较强

这个判断基本成立，但需要准确划清 related-work boundary。

我在本次检索到的 primary literature 中没有看到与你们完全同构的系统，但有四组非常接近的工作：

1. **DashBot** 已经使用 deep RL 生成 dashboard，但优化的是面向人的 insight discovery，而不是冻结 VLM 的 downstream RCA。([arXiv][2])
2. **NL2Dashboard** 已经提出 structured IR、analysis–presentation decoupling 和 deterministic rendering；这是你们应直接借鉴的架构模式。([arXiv][3])
3. **BlackVIP/BBVPE** 已经表明，可以不更新下游模型，而通过 input-dependent visual prompts 或 router 改善冻结模型的行为。([arXiv][4])
4. **HORNet** 与你们的训练思想最接近：它训练一个轻量 policy，选择冻结 VLM 最需要看到的视频帧，并使用 GRPO 优化 downstream answer quality，同时减少视觉输入和 VLM 处理时间。([arXiv][5])

所以你们不能把创新点写成：

> 第一个训练小模型来决定冻结 VLM 看什么。

这一点已有 HORNet、BlackVIP 等工作。

更准确的创新点是：

> **第一个针对 RCA，将异构 metrics、traces、logs 和 topology 编译成一个 provenance-preserving、token-budgeted、machine-oriented dashboard，并通过冻结 RCA VLM 的最终诊断效用训练 dashboard policy。**

“Toward a Machine Bertin”也明确提出，人类可视化设计原则不能直接迁移到以 patch token 处理图像的机器 audience，需要研究 machine-oriented visualization。这个理论定位与你们高度契合。([arXiv][6])


理由三：全自动不好时可以转为 Human-in-the-loop

Human-in-the-loop 可以成为有价值的第二贡献，但不能被写成“用来强行解释自动方法有效”。

如果自动系统失败，而加入人后成功，科学结论只能是：

> 人类可以有效修正或选择机器生成的 dashboard。

不能反推：

> 自动 Dashboard Agent 本身有效。

正确做法是从一开始把 HITL 注册为独立 RQ：

* 自动生成；
* 人在多个候选 dashboard 中选择；
* 人编辑 dashboard DSL；
* 人从固定模板构建；
* 人使用等信息文本。

然后衡量：

* 最终 RCA 准确率；
* 人工花费时间；
* 编辑次数；
* time-to-diagnosis；
* 人类自身诊断准确率；
* 对系统置信度的校准；
* 人工修改能否作为 preference data 回流训练。

人类必须在不知道 ground truth 的情况下编辑或选择，否则没有评估意义。


三、建议的正式系统定义

3.1 架构

$$
x
\xrightarrow{G}
h
\xrightarrow{B_\phi}
z
\xrightarrow{R}
I
\xrightarrow{F_\theta}
\hat y
$$

其中：

* \(x\)：raw telemetry；
* \(G\)：确定性的 canonicalizer/analyzer；
* \(h\)：Canonical Telemetry Evidence IR；
* \(B_\phi\)：小于 10B 的 Dashboard Agent；
* \(z\)：受约束的 Dashboard DSL；
* \(R\)：确定性 renderer；
* \(I\)：唯一一张 dashboard image；
* \(F_\theta\)：冻结的 Qwen/Gemma RCA VLM；
* \(\hat y\)：固定长度的 root-cause ranking；
* \(\theta\) 始终冻结，只训练 \(\phi\)。

运行时没有循环、搜索、crop、zoom、tool call 或重新绘图。

3.2 Dashboard Agent 应输出 DSL，而不是直接生成像素

不建议让 SLM 直接输出 PNG、SVG path 或自由 HTML。原因包括：

* 数值和文本难以验证；
* 容易出现 hallucinated telemetry；
* 无法保证不同 arm 信息对等；
* 很容易通过位置、颜色或纹理形成 covert channel；
* 生成结果难以复现和消融。

更合理的是：

yaml
candidate_policy:
  max_entities: 12
  selector: multimodal_union

layout:
  family: entity_centric
  row_order: estimated_onset

metrics:
  transform: normal_current_delta
  mark: stat_card_plus_sparkline
  precision: 2

traces:
  fields: [delta_inclusive, delta_exclusive, call_fold]
  mark: paired_bar

logs:
  representation: template_card
  max_per_entity: 2

topology:
  representation: graph_plus_edge_ledger
  hops: 1

budget:
  max_visual_tokens: 2100


renderer 负责把这份 program 确定性地转成图片。

NL2Dashboard 已经证明 structured IR 与 deterministic renderer 可以避免直接生成 raw HTML 带来的 token redundancy 和 controllability 问题；Draco 则提供了把 visualization knowledge 表达为 hard/soft constraints 的成熟先例。([arXiv][3])


四、Dashboard Design Space 应如何定义

建议把设计空间拆成六层，而不是把所有自由度混在一起。

| 层级                      | Dashboard Agent 决定什么                           | 示例                                                       |
| ----------------------- | ---------------------------------------------- | -------------------------------------------------------- |
| **Content selection**   | 显示哪些 entity、metric、operation、log template、edge | Top-\(K\)、modal union、1-hop neighborhood                 |
| **Transformation**      | 如何从 raw telemetry 得到诊断 primitive               | baseline/current、signed change、onset、persistence、ExL/InL |
| **Visual encoding**     | 数据映射到何种视觉变量                                    | line、bar、heatmap、stat card、graph、table                   |
| **Composition**         | 信息在空间上如何组织                                     | modality-centric、entity-centric、topology-centric         |
| **Salience allocation** | 哪些区域获得更大面积和更高精度                                | panel size、font size、precision、annotation                |
| **Budget allocation**   | 如何使用有限的 image tokens                           | 候选数、时间 bin、分辨率、文本长度                                      |

4.1 最值得优先研究的布局：entity-centric canvas

当前 dashboard 是 modality-centric：

* 一个 metrics 区；
* 一个 traces 区；
* 一个 logs 区；
* 一个 topology 区。

这迫使 VLM 在不同区域之间反复绑定相同 entity ID，恰好放大报告中的 cross-region identity loss。

下一版可以改为：

| Candidate | Metrics         | Locality/Trace   | Logs                    | Topology/Onset      |
| --------- | --------------- | ---------------- | ----------------------- | ------------------- |
| E03       | 正常→当前、方向、幅度、持续度 | ΔInL、ΔExL、Δcalls | template、severity、count | caller/callee、onset |
| E07       | …               | …                | …                       | …                   |

同一个实体的跨模态证据位于同一行。旁边再保留一个小型 central graph 和 edge ledger。

这不是说 entity-centric 一定最好，而是它直接针对报告发现的 composition bottleneck，因而应成为优先 hypothesis。

4.2 各模态不应强制使用相同“视觉程度”

一张 dashboard 并不意味着每一块都必须画成传统 chart。

建议：

* **Topology**：保留真正的空间图结构，同时加入显式 edge ledger；
* **Metrics**：主要使用 normal/current 对比、方向、异常幅度、onset、persistence；曲线只作为短 sparkline；
* **Traces**：突出 \(\Delta InL\)、\(\Delta ExL\)、call count 和方向；
* **Logs**：保留大字体、短文本的 template skeleton、severity、count 和 onset。

报告显示 topology 是当前最稳定的正视觉信号；metrics 小曲线造成严重精确读取负担；trace table 直接读取很好但没有稳定转化为 RCA；日志文本语义仍然很强。


五、新一阶段建议提出的 Research Questions

RQ2.1：Instance-adaptive dashboard 是否优于任何固定 dashboard？

> 在相同视觉预算下，根据 incident 自适应生成 dashboard 的 learned policy，能否超过最佳固定 dashboard，并达到或超过 TextTwin？

关键比较：

* random dashboard；
* best fixed dashboard；
* oracle per-case dashboard；
* learned dashboard policy。

决定性结果不是 policy 是否高于当前 full-V，而是它能否回收 oracle–fixed gap。


RQ2.2：性能增益究竟来自 content selection，还是 visual representation？

> Dashboard Agent 的收益有多少来自选择了更好的证据，有多少来自相同证据被更好地视觉组织？

实验拆分：

1. 学习 selection，固定 layout/encoding；
2. 固定 selection，学习 layout；
3. 固定 selection/layout，学习 encoding；
4. 只学习 budget allocation；
5. full policy。

这是防止“Dashboard Agent 其实只是偷偷做了 RCA”的核心实验。


RQ2.3：在严格信息对等条件下，Canvas 能否在大幅压缩 receiver context 时保持非劣？

> 从同一个 Dashboard DSL 中生成 CanvasTwin 和 TextTwin，CanvasTwin 能否在冻结 VLM 上达到 TextTwin 的非劣性能？

两个 serializer 必须共享：

* 相同 candidate set；
* 相同 evidence set；
* 相同 transformation；
* 相同数值精度；
* 相同 entity order；
* 相同 truncation；
* 相同 provenance。

建议主门槛：

$$
\operatorname{MRR}_{Canvas}
-
\operatorname{MRR}_{TextTwin}
> -0.02
$$

且：

$$
\frac{Tokens_{Canvas,VLM}}{Tokens_{TextTwin,VLM}}
\leq 0.5
$$

也可以补充相对门槛：

$$
\operatorname{MRR}_{Canvas}
\geq 0.95 \operatorname{MRR}_{TextTwin}
$$


RQ2.4：Dashboard Policy 是否能够跨数据集、系统、故障类型和 schema 泛化？

> 在不重新训练 Dashboard Agent 和 RCA VLM 的情况下，policy 是否能处理未见过的系统和 telemetry schema？

至少进行：

* leave-one-dataset-out；
* system-held-out；
* fault-type-held-out；
* topology-size-held-out；
* missing-modality；
* unseen metric/log template；
* renamed entity/metric；
* altered sampling frequency and units。

不要只做随机 case split。


RQ2.5：最优 dashboard 是 receiver-specific，还是存在 universal machine dashboard grammar？

训练：

* \(B_Q\)：只用 Qwen reward；
* \(B_G\)：只用 Gemma reward；
* \(B_{\text{avg}}\)：优化两模型平均 reward；
* \(B_{\text{min}}\)：优化两模型 worst-case reward；
* \(B_{\text{cond}}\)：将 receiver ID 作为 condition。

然后交叉测试：

| Builder            |     Qwen |    Gemma | Unseen VLM |
| ------------------ | -------: | -------: | ---------: |
| \(B_Q\)            |        ✓ | transfer |   transfer |
| \(B_G\)            | transfer |        ✓ |   transfer |
| \(B_{\text{avg}}\) |        ✓ |        ✓ |   transfer |

第一阶段 Qwen/Gemma 的差异已经说明这是一个必要 RQ，而不是附属消融。


RQ2.6：SFT、Preference Optimization 和 RL 哪一种最适合训练 Dashboard Agent？

建议比较：

1. supervised DSL generation；
2. best-of-\(N\) imitation SFT；
3. pairwise DPO；
4. GRPO/contextual-bandit training；
5. SFT → DPO → GRPO。

Chart-R1、Chart-RVR 和 Chart-RL 都表明，程序化数据、结构化 warm start 和 verifiable reward 可以提高 chart reasoning，且 RL 在 OOD 与复杂样本上可能优于纯 SFT；不过这些工作训练的是 receiver，而你们训练的是 sender。([arXiv][7])

RQ2.7：Dashboard Agent 是否通过真实 telemetry communication 提升 RCA，而非利用 shortcut？

> Policy 是否使用可验证证据，还是通过颜色、位置、顺序和数据集特征隐式传递答案？

需要专门的 fidelity 和 shortcut benchmark，后文给出实验。


RQ2.8：完整双模型系统能否超过 protocol-matched RCA SOTA，并形成更优的 accuracy–cost Pareto frontier？

这里应同时验证：

* accuracy；
* frozen-VLM context；
* pipeline total cost；
* cross-system performance；
* worst-group performance。


RQ-H：Human steering 能否低成本修复自动 Dashboard Agent？

这是 secondary RQ，不应代替 RQ2.1–RQ2.8。


六、最重要的实验对照：必须区分三种 claim

6.1 Representation-level claim

回答：

> 相同信息用图还是用文本更适合冻结 VLM？

| Arm        | Builder selection | Serializer   |
| ---------- | ----------------- | ------------ |
| TextTwin   | 相同                | compact text |
| CanvasTwin | 相同                | one image    |

这才是严格的信息对等比较。

6.2 Learned-preprocessing claim

回答：

> 学习如何选择和组织信息是否有用？

| Arm            | 内容                      |
| -------------- | ----------------------- |
| Fixed-Text     | 固定信息选择 + 文本             |
| Fixed-Canvas   | 固定信息选择 + dashboard      |
| Learned-Text   | SLM 选择信息 + compact text |
| Learned-Canvas | SLM 选择信息 + dashboard    |

这里最重要的 comparator 是 **Learned-Text**。否则 reviewer 会直接问：

> 为什么不让同一个 7B SLM 输出紧凑 JSON，而要画图？

6.3 End-to-end system claim

回答：

> 完整 CanvasRCA 是否值得部署？

必须加入：

* SLM direct RCA；
* learned compact text → frozen VLM；
* learned dashboard → frozen VLM；
* deterministic RCA baselines；
* external SOTA。

尤其是：

> **Dashboard Agent 必须增加一个 direct-root-prediction head 或独立 prompt baseline。**

如果 SLM 自己直接做 RCA 已经达到相同性能，那么 dashboard 可能只是在把 SLM 的答案传给 VLM，而不是产生新的协同能力。


七、建议的新阶段实验路线

Phase 0：冻结研究协议

现有 469 cases 应全部归入 development pool，因为报告已经明确说明它们是 exploratory、repeated-exposed evaluation，而不是 untouched confirmation；RE2-OB/TT 也接近饱和，不适合承担主 headline。

在继续设计之前：

1. 划定新的 untouched confirmation set；
2. 同一 incident family 不得跨 train/test；
3. renderer、reward、prompt、candidate rule 冻结后才允许跑 test；
4. test label 只能在 evaluator 内部使用；
5. 当前 469 cases 用于 renderer search 和 builder training。


Phase 1：先估计 Dashboard Policy 的理论 headroom

Experiment 1A：Existing-arm oracle

从当前 16 个 factorial arms 和机制 arms 中，对每个 case 选最高 RR 的 arm：

$$
OracleExisting(i)=
\arg\max_a RR(i,a)
$$

计算：

* oracle MRR；
* oracle AC@1；
* best-fixed 与 oracle 的差距；
* 每个 arm 被 oracle 选择的频率；
* 按 dataset、fault type、root granularity、edge count 分层。

这一步不需要任何训练，却直接决定 adaptive policy 是否值得做。

Experiment 1B：新 Dashboard Library

先人工定义 16–32 个合法 dashboard configurations，不做完整笛卡尔积。建议覆盖：

* modality-centric / entity-centric / topology-centric；
* raw metric curve / stat card / delta bar / heatmap；
* trace table / ExL–InL paired bar；
* raw log rows / template cards / event timeline；
* graph only / graph + edge ledger / propagation lanes；
* \(K=8,12,16\) candidates；
* 不同视觉 token budget。

使用 fractional factorial 或 Bayesian design search，而不是穷举。

Go/no-go gate

建议：

* oracle 比 best fixed 至少高 \(0.03\) MRR：继续 adaptive policy；
* 差距低于 \(0.01\)：优先优化固定 renderer，而不是训练复杂 agent；
* 中间区域：先扩大设计空间。


Phase 2：先做离散 contextual-bandit proof-of-concept

不要第一步就让 7B SLM生成复杂 DSL。

让 Dashboard Agent 先从 16–32 个合法 template 中选择一个：

$$
a_i \in \{D_1,D_2,\ldots,D_K\}
$$

输入是 label-blind incident IR，输出是 dashboard template ID 和参数。

这是一个一步 contextual bandit：

* context：incident telemetry；
* action：dashboard specification；
* reward：冻结 VLM 的 RCA utility；
* 没有状态转移；
* 没有迭代探索。

比较：

* random selector；
* global best fixed；
* supervised oracle-arm classifier；
* contextual-bandit policy；
* GRPO policy；
* oracle upper bound。

这个实验若成功，就已经证明：

> instance-adaptive visual representation 比统一固定 dashboard 更好。

随后再扩展到 compositional DSL。


Phase 3：训练完整 Dashboard Agent

3.1 SFT warm start

训练内容：

* schema → valid DSL；
* candidate set → legal layout；
* telemetry feature → compatible mark；
* budget → area allocation；
* source fact → provenance field。

训练数据来源：

* 手工设计合法模板；
* constraint solver 输出；
* best-of-\(N\) dashboard；
* synthetic telemetry；
* 真实案例的 nuisance variants。

ChartVerse 使用程序化生成、answer-first ground truth 和一致性验证来构造可靠 chart reasoning data；你们也可以从 canonical IR 和 renderer program 中确定性产生监督，而不是让另一个 LLM自由生成答案。([arXiv][8])

3.2 Offline preference optimization

对同一个 incident 采样 \(N=8\sim16\) 个 dashboard programs：

$$
\{z_1,\ldots,z_N\}
$$

全部通过冻结 Qwen/Gemma 评测，得到：

$$
r(z_j)=
RR_j-\lambda Cost_j
$$

由此构造：

$$
(z^+,z^-)
$$

进行 DPO。

这会比从随机初始 policy 直接做 GRPO 更稳定，也能缓存 VLM reward，降低训练成本。

3.3 GRPO / one-step RL

之后在 hard cases 上做 GRPO：

* root absent；
* 高 graph density；
* 多个强 anomaly；
* modality conflict；
* node-level root；
* text 正确但 full-V break；
* TPV/V_LG repair 的案例。

HORNet 是最接近的训练先例：冻结 answer VLM，只训练轻量 input policy，并用 GRPO 优化下游结果。([arXiv][5])


八、Dashboard Agent 的 reward 应如何设计

建议先通过 hard constraints 过滤，再计算 reward。

8.1 Hard constraints

不满足以下条件直接 reward 为最低：

* DSL 可解析；
* 只能显示 IR 中存在的事实；
* 每个 visual mark 有 provenance；
* 不允许出现 root/fault label；
* 不允许 dataset/case identifier；
* 单张图；
* visual token 不超过预算；
* 字体和字段真实可见；
* candidate ID 唯一；
* 不允许任意纹理、隐藏字符或自由像素。

8.2 Task reward

$$
r_{\mathrm{task}}
=
RR
+\alpha AC@1
+\beta EvidenceGrounding
+\gamma CausalOrder
$$

其中：

* \(RR\)：真实根因 reciprocal rank；
* \(AC@1\)：top-1 bonus；
* `EvidenceGrounding`：VLM 引用的 evidence ID 是否真实存在；
* `CausalOrder`：是否将 root 排在 known propagated nodes 前面。

DynaCausal 的一个关键启示是不能只按 anomaly intensity 排序，而要显式采用 causal-prioritized pairwise ranking 来区分根因和强传播症状。([arXiv][9])

8.3 Cost reward

$$
r_{\mathrm{cost}}
=
-\lambda_1 Tok_{\mathrm{VLM}}
-\lambda_2 Tok_{\mathrm{SLM}}
-\lambda_3 Latency
$$

但建议把 VLM visual-token budget 作为硬约束，而不是完全交给 scalar reward。

否则 policy 可能通过：

* 少显示候选；
* 删除困难 evidence；
* 让 VLM 只输出一个候选；

来投机降低成本。

8.4 Universal-receiver reward

针对 Qwen 和 Gemma：

$$
r_{\mathrm{avg}}
=
\frac{r_Q+r_G}{2}
$$

或更严格：

$$
r_{\mathrm{robust}}
=
\mu\frac{r_Q+r_G}{2}
+
(1-\mu)\min(r_Q,r_G)
$$

平均 reward 更容易得到高总体性能；minimax reward 更可能得到跨 receiver 稳定的 dashboard grammar。


九、必须防止 Dashboard Agent “偷偷编码答案”

这是 reviewer 最可能攻击的地方。

9.1 可能的 shortcut

Dashboard Agent 可能学会：

* 把自己认为的 root 永远放在左上角；
* 用特定颜色表示 root；
* 用字体大小、行距、空白形成编码；
* 依赖原始 entity index；
* 根据数据集名称猜 fault；
* 只呈现一个候选，使冻结 VLM 没有选择空间。

这些策略可能提高 accuracy，但它们证明的是：

> SLM 已经在做 RCA，并通过视觉信道传递答案。

而不是：

> dashboard 提供了更有效的证据表示。

9.2 必须加入的检测实验

Value-masked test

保留：

* layout；
* color；
* candidate order；
* panel shape。

隐藏所有 telemetry values 和文本。

如果 VLM 仍显著高于随机，说明存在 layout/style covert channel。

Style-randomized test

保持事实不变，随机化：

* palette；
* font；
* row spacing；
* panel position；
* graph layout。

真实的 evidence-based policy 应相对稳定。

ID and order randomization

每个 epoch 和每个 evaluation variant 都随机：

* entity ID；
* input row order；
* metric order；
* log template ID。

Fixed-order ablation

禁止 Dashboard Agent 改变 candidate order，只允许选择 content 和 encoding。

这样可以测量有多少收益来自“排序候选”，有多少来自“帮助 VLM 推理”。

Direct-SLM RCA

让相同 SLM 直接输出 root ranking。

如果：

$$
Acc(B_{\mathrm{direct}})
\approx
Acc(B_{\mathrm{canvas}}\rightarrow VLM)
$$

那么 frozen VLM 贡献可能很小。

Learned-Text control

让同一 Dashboard Agent 把相同 evidence 输出为 compact structured text。

如果 Learned-Text 与 Learned-Canvas 相当甚至更强，那么 system-level preprocessing 有价值，但 Canvas 并没有额外贡献。


十、跨数据集与跨 receiver 泛化实验

10.1 Leave-one-dataset-out

例如：

| Train                       | Test       |
| --------------------------- | ---------- |
| AegisLab + AIOps-2022 + RE2 | AIOps-2025 |
| AegisLab + AIOps-2025 + RE2 | AIOps-2022 |
| AIOps-2022/2025 + RE2       | AegisLab   |
| AegisLab + AIOps            | RE2-OB/TT  |

test dataset 上不能：

* 改 prompt；
* 调 renderer；
* 更新 SLM；
* 重新搜索 dashboard；
* 重新设置 candidate threshold。

10.2 Schema stress test

构造语义不变的格式扰动：

* metric rename；
* unit conversion；
* sampling-rate change；
* different missingness pattern；
* log template paraphrase；
* entity renumbering；
* trace field reorder；
* topology layout change。

这能测试它是否理解 telemetry primitive，而不是记住字段名称。

10.3 Fault-type-held-out

完整故障类别只出现在 test，例如：

* network；
* resource；
* lifecycle；
* JVM/code；
* time/DNS 类。

10.4 Topology-held-out

训练只见：

* 边数 ≤10；
* propagation depth ≤2。

测试：

* 边数 >10；
* propagation depth ≥3；
* 多 branch propagation。

报告已有描述性结果表明，Qwen 的 topology visual 在 6 条边以上更有帮助，但这个分析和 dataset/fault type 混杂，应重新做预注册的复杂度实验。

10.5 Receiver transfer

最关键的四个结果：

$$
B_Q\rightarrow Q,\quad
B_Q\rightarrow G,\quad
B_G\rightarrow G,\quad
B_G\rightarrow Q
$$

若 \(B_Q\rightarrow G\) 很差，说明 policy 学到的是 Qwen-specific visual dialect；这不一定使论文失败，但主 claim 应改为 receiver-aware dashboard compilation。


十一、如何衡量“节省大量 token”

双模型系统中，不能只继续报告 RCA VLM 的 input tokens。

第一阶段的 token 表只测了 receiver 侧；同一图片在 Qwen 中约为 2,101 image tokens，在 Gemma 中约为 1,085，因此跨模型不能直接比较绝对 token。报告也明确提醒 tokenizer 和 visual processor 不同。 

新的系统至少应报告：

| 指标                              | 含义                                    |
| ------------------------------- | ------------------------------------- |
| **Receiver input tokens**       | 27B RCA VLM 实际处理的 text+image tokens   |
| **Builder input/output tokens** | <10B SLM 的全部 token                    |
| **Pipeline total tokens**       | 两个模型之和                                |
| **Model-token proxy**           | 模型规模 × processed tokens 的粗略计算代理       |
| **End-to-end latency**          | canonicalization + SLM + render + VLM |
| **Peak VRAM / energy**          | 实际部署成本                                |
| **Dollar cost**                 | 若使用 API 或统一硬件估算                       |

论文中的核心效率 claim最好写成：

> 减少 expensive frozen RCA VLM 的上下文和推理成本。

只有当 pipeline total cost 也下降时，才额外声称端到端成本降低。


十二、SOTA 评测应如何组织

RCA 领域不存在一个能直接混合比较的单一 SOTA，因为不同论文使用不同：

* 数据集；
* root granularity；
* fault-type要求；
* train/test split；
* telemetry 权限；
* 是否使用历史标签；
* 是否允许 agentic exploration。

因此要采用 **per-protocol SOTA**。

12.1 RCAEval

RCAEval 提供 735 个 failure cases 和 15 个可复现 baseline，适合做标准化的 broad benchmark。([arXiv][10])

12.2 Fault-propagation-aware hard benchmark

FSE 2026 的新 benchmark 包含：

* 1,430 个 validated cases；
* 来源于 9,152 次 fault injections；
* 25 种 fault types、6 类故障；
* 动态 workload；
* 分层 ground truth；
* 11 个 SOTA 方法平均 Top@1 只有 0.21，最强约 0.37。([arXiv][11])

这比接近饱和的 RE2 更适合作为主 headline。

12.3 GALA+

GALA+ 是多阶段 graph-guided agentic RCA，报告在 OnlineBoutique 和 TrainTicket 上分别达到 74.44% 和 73.33% AC@1。它使用 candidate generation、pod-centric diagnostic bundle、graph-guided exploration 和最终 synthesis。你们可以把多轮 localized investigation“编译”为一次空间并行 dashboard，这是非常清楚的对照叙事。([arXiv][12])

12.4 DynaCausal 和 MetaRCA

* DynaCausal 报告公共 benchmark 平均 AC@1 为 0.63，并显式优化 dynamic causal contrast 和 pairwise causal ranking。([arXiv][9])
* MetaRCA 强调跨 topology 的 reusable meta causal knowledge 和跨系统泛化。([arXiv][1])

这些不能仅引用论文数字比较，必须把 CanvasRCA 放进相同数据、split 和 granularity 中运行。


十三、建议的 Human-in-the-loop 实验

将 HITL 放在独立 extension 中：

| Arm                 | 人的角色                      |
| ------------------- | ------------------------- |
| Auto                | 无人参与                      |
| Human-select        | 从 3–4 个 SLM dashboard 中选择 |
| Human-edit          | 编辑 DSL 中的选择、布局或编码         |
| Human-from-template | 从固定合法模板自行配置               |
| Human-text          | 使用等信息文本                   |
| Human-only RCA      | 人直接做 RCA                  |

测量：

* 人类诊断准确率；
* 经人工修改后 VLM 的 MRR/AC@1；
* editing time；
* number of edits；
* 每种编辑操作的边际收益；
* confidence calibration；
* preference consistency；
* 修改是否能用于下一轮 DPO。

这种设计可以产生两个有价值的结果：

1. 人类是否能够识别“对机器更好”的 dashboard；
2. 人类修改是否能提供比 root-label reward 更稳定的 visual preference signal。

NOVAID 已经在 ITOps dashboard widget generation 中使用人机交互和用户研究验证 usability，但它优化的是人类生成监控 widget 的体验，不是 VLM RCA。([arXiv][13])


十四、完整的下一阶段执行顺序

P0：协议和基础设施

1. 当前 469 cases 全部标为 development；
2. 建立 untouched test；
3. 建立 Canonical Telemetry Evidence IR；
4. 建立 provenance-aware Dashboard DSL；
5. 实现 deterministic renderer；
6. 从同一 DSL 实现 CanvasTwin 和 TextTwin；
7. 固定 RCA VLM output schema，强制返回完整候选 ranking。

P1：无训练的设计空间研究

1. 复算现有 arm 的 per-case oracle；
2. 设计 16–32 个单图 dashboard configurations；
3. 运行 best-fixed 与 oracle；
4. 定位 selection/layout/encoding/budget 的 headroom；
5. 确定是否值得进入 learned policy。

P2：离散 Dashboard Selector

1. Dashboard Agent 只选择 template ID；
2. 比较 supervised selector、DPO 和 contextual-bandit/GRPO；
3. 分别训练 Qwen-specific、Gemma-specific 和 universal policy；
4. 检查是否超过 best fixed。

P3：完整 DSL Dashboard Agent

1. 合法 DSL SFT；
2. best-of-\(N\) reward collection；
3. pairwise DPO；
4. hard-case GRPO；
5. receiver-average/minimax reward；
6. test-time 只生成一个 dashboard，不允许 best-of-\(N\)。

P4：公平性与 shortcut 审计

1. Learned-Canvas vs Learned-Text；
2. Direct-SLM RCA；
3. fixed-order；
4. masked-value；
5. randomized style/ID；
6. evidence occlusion；
7. provenance correctness；
8. candidate coverage。

P5：OOD 泛化

1. leave-one-dataset-out；
2. system-held-out；
3. fault-held-out；
4. topology-held-out；
5. schema perturbation；
6. receiver transfer。

P6：冻结后的最终评测

1. RCAEval；
2. 1,430-case hard benchmark；
3. GALA+ exact protocols；
4. internal untouched test；
5. paired statistical tests；
6. end-to-end cost accounting。

P7：HITL extension

仅在自动系统和设计空间已经冻结之后运行。


十五、建议的成功门槛

这些可以作为初始 engineering gates，而不是提前宣称的结果。

| 目标                              |                     建议门槛 |
| ------------------------------- | -----------------------: |
| Root candidate recall@K         |                     ≥98% |
| Dashboard DSL validity          |                   ≥99.5% |
| Visual fact fidelity            |                   ≥99.5% |
| Receiver input saving           |                     ≥50% |
| End-to-end compute/cost saving  |                     ≥30% |
| Canvas vs TextTwin              |          MRR 下界不低于 −0.02 |
| Relative MRR retention          |                     ≥95% |
| Learned policy vs best fixed    |               ≥+0.03 MRR |
| Dataset worst-group degradation |             不超过 0.05 MRR |
| Shortcut masked test            |                     接近随机 |
| Final external result           | 超过 protocol-matched SOTA |

统计上：

* MRR：paired permutation test + paired bootstrap CI；
* AC@1：McNemar test；
* Canvas vs TextTwin：one-sided non-inferiority test；
* 多 dashboard/configuration：Holm correction；
* incident family 重复时：cluster bootstrap。

不要把 `MRR/token` 作为唯一目标，因为一个低 token、低 accuracy 的系统也可能得到误导性的高 ratio。主图应是 accuracy–cost Pareto frontier。


最终推荐的论文主线

你的 Dashboard Agent 应被明确视为 RCA 系统的一部分，而不是一个完全中性的美化工具。最有说服力的核心命题是：

> **异构 telemetry 的原始表示并不是冻结 VLM 的最佳输入。CanvasRCA 使用一个轻量、任务导向、可验证的 visual compiler，在一次前馈决策中为每个 incident 自适应选择证据、转换方式、布局和视觉编码，将顺序、冗长的诊断上下文压缩为一张 machine-oriented dashboard。**

最终需要证明四件事：

1. **Adaptive policy 确实超过最佳固定 dashboard，而不只是重新发现 TPV。**
2. **在同一事实、同一 selection 的 TextTwin 对照下，Canvas 以不到一半的 receiver budget 保持至少 95% 的 MRR，或者直接超过文本。**
3. **收益不是 Dashboard Agent 通过位置、颜色或候选顺序偷偷传递 root label。**
4. **在从未参与 renderer 和 policy 设计的 hard benchmark 上，完整系统超过 protocol-matched RCA SOTA，并且包括 Builder 在内的端到端成本仍然更低。**

第一阶段最重要的启示不是“full dashboard 失败了”，而是：

* Qwen 的 V_MG 已经展示了接近无损的高压缩点；
* TPV/V_LG 展示了可以提高 RCA 的视觉结构；
* 大量 repair/break 表明 case-adaptive representation 存在潜在空间；
* Qwen/Gemma 差异表明需要研究 receiver-aware visual language；
* full-V 暴露了 selection、binding 和 causal ranking 的明确训练目标。

因此，下一阶段最优先的工作不是立刻做大型 GRPO，而是：

> **先建立受约束设计空间，计算 per-case oracle headroom，再用离散 contextual-bandit selector 验证“学习为冻结 VLM 选择 dashboard”这一核心假设。**

只有这个实验成立后，才值得扩展到完整的 3–8B Dashboard DSL Agent、DPO 和 GRPO。

[1]: https://arxiv.org/abs/2603.02032 "https://arxiv.org/abs/2603.02032"
[2]: https://arxiv.org/abs/2208.01232 "https://arxiv.org/abs/2208.01232"
[3]: https://arxiv.org/abs/2601.06126 "https://arxiv.org/abs/2601.06126"
[4]: https://arxiv.org/abs/2303.14773 "https://arxiv.org/abs/2303.14773"
[5]: https://arxiv.org/abs/2603.18850 "https://arxiv.org/abs/2603.18850"
[6]: https://arxiv.org/abs/2602.01527 "https://arxiv.org/abs/2602.01527"
[7]: https://arxiv.org/abs/2507.15509 "https://arxiv.org/abs/2507.15509"
[8]: https://arxiv.org/abs/2601.13606 "https://arxiv.org/abs/2601.13606"
[9]: https://arxiv.org/abs/2510.22613 "https://arxiv.org/abs/2510.22613"
[10]: https://arxiv.org/abs/2412.17015 "https://arxiv.org/abs/2412.17015"
[11]: https://arxiv.org/abs/2510.04711 "https://arxiv.org/abs/2510.04711"
[12]: https://arxiv.org/abs/2608.08968 "https://arxiv.org/abs/2608.08968"
[13]: https://arxiv.org/abs/2601.11531 "https://arxiv.org/abs/2601.11531"
```
## Round 2

### Me:
```
还有就是组员也提到dashboard可以不弄这种M/L/T/G四种组合的形式，也可以是per-service_name的布局。比如dashboard上画我们选出的十几个services，每个service下面显示一些图表。比如有一个service的metrics有问题，那么我们只显示metrics图表。另一个service的log有问题，那么我们只显示log图表等。还有就是也可以把per-service_name布局仅限某些modality的数据，比如把M/L/T显示为per-service布局，而把全局的G作为一个单独的部分显示出来等。我觉得dashboard有很多种设计方式，但是我们要把这些设计方式总结或者抽象为有限的离散设计空间，或者说无限的连续设计空间，这样我们才能够设计出来奖励和训练信号。你现在可以参考一些dashboard方面的文章，帮我想一想我们如何来设计这个dashboard的设计空间。你在看dashboard的时候，可以不光去看论文，也去看看一些大公司的运维dashboard是什么样子，怎么设计的，以及为何那样设计。然后，你把这一次你看的dashboard相关的文章，还有上一轮对话里你看了的RL、RCA、SFT、Fault localization等文章也都列出来，这样我也可以丰富一下参考文献库，让我的本地coding和planning agent可以有更多参考资料。
我发现你看了qlora的文章，实际上我们不需要quantization，我们有96GB的显存，finetune一个10B一下的模型并同时装载一个27B的模型是足够的。
你怎么停下了？有写出计划吗？
```
### Agent:
```
有。上一条在检索和整理资料时中断了，没有把正文正常发出来。下面是整合后的**Dashboard 设计空间、训练信号、实验路线和参考文献库**。

先修正训练配置：**不采用 QLoRA，也不做权重量化。**建议默认配置为：

$$
\text{Frozen 27B RCA VLM in BF16}
+
\text{3B–8B Dashboard SLM in BF16 with LoRA/DoRA}
$$

27B BF16 权重大约占 54GB，7B BF16 权重大约占 14GB，因此两套基础权重可以同时驻留在 96GB 显存中。使用 BF16 LoRA/DoRA、gradient checkpointing 和较短的结构化输出训练 Dashboard Agent 是合理的。需要区别的是，**7B–10B 的 full-parameter AdamW 微调**还会产生梯度、optimizer states 和 activations，和常驻 27B 模型一起不一定能稳妥放入 96GB；若以后确实要做 full fine-tuning，可以先离线缓存 VLM reward，训练时不常驻 27B，或者使用 optimizer offload。这里完全不需要对模型权重做 4-bit/8-bit quantization。

---

一、核心建议：不要把设计空间定义为 M/L/Tr/G 的子集

第一阶段把 dashboard 分成 Metrics、Traces、Logs、Topology 四块，是很好的 factorial experiment，但不适合作为最终 Dashboard Agent 的 action space。

报告已经表明：

* Metrics visual 对精确读取明显不友好；
* Trace visual 的单区域读取很好，但没有稳定转化为 RCA 增益；
* Logs 仍然很依赖可读文本；
* Topology 对 Qwen 有帮助，但对 Gemma 不稳定；
* 最大的问题之一是跨区域切换时丢失 service identity。 

因此，新的设计空间应以“**信息如何围绕候选 service 组织**”为核心，而不是以“哪种 modality 被视觉化”为核心。

我建议将 Dashboard Agent 定义成一个受约束的 dashboard program generator：

$$
B_\phi(X, r, B)\rightarrow z
$$

其中：

* \(X\)：canonical telemetry IR；
* \(r\)：receiver 类型，例如 Qwen 或 Gemma；
* \(B\)：视觉 token、像素面积或 chart-card 数预算；
* \(z\)：Dashboard DSL；
* 确定性 renderer 将 \(z\) 变成唯一一张图。

Dashboard program 可以形式化为：

$$
z=
(\ell,\;S^\*,\;D,\;E,\;H,\;O,\;A,\;P)
$$

| 变量       | 含义                                      |
| -------- | --------------------------------------- |
| \(\ell\) | 整体 layout family                        |
| \(S^\*\) | 被选入 dashboard 的 services                |
| \(D\)    | 每个 service、每种 modality 的显示级别            |
| \(E\)    | 每个 evidence cell 的视觉编码                  |
| \(H\)    | 全局模块，如 topology、onset strip、SLI summary |
| \(O\)    | service、panel 和 evidence 的排序规则          |
| \(A\)    | 面积、精度和视觉预算分配                            |
| \(P\)    | provenance：每个视觉元素对应哪些原始事实               |

这会形成一个**有限但组合规模很大的离散空间**。第二阶段再增加半连续的面积和精度分配，不建议一开始进入完全自由的像素空间。

---

二、推荐的 Dashboard Layout Families

我建议把整体布局限制为下面 8 个 family。每个 family 内部再选择 service、modality 和 encoding。

F0：Global Modality Grid

即第一阶段的形式：

text
┌──────── Metrics ────────┬──────── Traces ────────┐
├──────── Logs ───────────┼──────── Topology ──────┤


用途：

* 作为旧版固定 baseline；
* 保留与第一阶段的直接可比性；
* 不建议成为最终主布局。

---

F1：Service-Row Matrix

每个 service 一行，modality 是列：

text
Service    Metrics       Traces        Logs
E01        [chart]       [summary]     —
E02        —             [chart]       [log card]
E03        [summary]     —             [chart]


优点：

* 同一个 service 的多模态证据天然对齐；
* 显著减少 cross-region identity loss；
* 列位置固定，VLM 更容易形成稳定的视觉语法；
* 空 cell 可以直接省略、灰化，或者用极小占位符表示“没有诊断性证据”。

Grafana 的生产 dashboard 设计建议就包含“一个 service 一行”，并建议按照数据流顺序排列 service；同时，它强调 dashboard 不需要显示全部服务器，只显示真正有问题的对象，以降低认知负担。([Grafana][1])

---

F2：Variable Service Cards

每个 service 是一张可变大小的 card，只显示该 service 被选中的 modality：

text
┌ E01 ─────────────┐  ┌ E02 ─────────────────┐
│ Metrics chart    │  │ Log template          │
│ Trace summary    │  │ count / onset         │
└──────────────────┘  └────────────────────────┘

┌ E03 ──────────────────────────────────────────┐
│ InL / ExL / call-count / downstream relation │
└────────────────────────────────────────────────┘


这正好表达组员提出的想法：

* E01 只有 metrics 异常，就只显示 metric；
* E02 只有 logs 有诊断价值，就只显示 log；
* E03 的 trace 能区分 local slowdown 与 downstream waiting，就只显示 trace；
* 多个 modality 都重要时，card 内可以并列两到三块。

这种布局表达能力高，但位置和大小变化也更大，可能增加 VLM 的视觉不稳定性。因此应和 F1 的固定矩阵严格比较。

---

F3：Per-Service Evidence + Global Topology

这是我最推荐的主布局：

text
┌────────────── Global topology / propagation / edge ledger ──────────────┐
│ E01 → E04 → E07          onset: E07 < E04 < E01                         │
└──────────────────────────────────────────────────────────────────────────┘

┌ E01 ─────────────┐ ┌ E04 ─────────────┐ ┌ E07 ────────────────────────┐
│ Metrics           │ │ Logs              │ │ Trace-locality              │
│ ↑ latency         │ │ timeout burst     │ │ ExL ↑↑, InL ↑↑             │
└───────────────────┘ └───────────────────┘ └─────────────────────────────┘


即：

* M/Tr/L 按 service 组织；
* G 独立作为全局结构区；
* graph node 和 service card 使用相同 ID；
* graph 下最好附带 edge ledger，例如 `E01 → E04`，避免只靠箭头 OCR；
* 所有 service mini-chart 使用共享时间轴。

这一结构与 AWS、Datadog、Splunk 的生产观测产品非常接近：先通过全局 service map 理解依赖与健康状况，再查看单个 service 的请求、错误、延迟、logs、traces 和依赖详情。([AWS 文档][2])

---

F4：Topology-Centered Evidence Satellites

把拓扑放在中央，被选中的 service 周围附着 evidence：

text
             [E02 log]
                 |
[E01 metric] — E01 → E04 → E07 — [E07 trace]
                       |
                   [E04 metric]


优点：

* evidence 与 graph node 的 binding 很强；
* topology 与 local evidence 的空间距离较小。

风险：

* service 较多时容易出现拥挤和不规则位置；
* 可能使模型依赖“离中心位置”这种 shortcut；
* 不适合 dense topology。

适合作为结构推理能力较强的 receiver-specific layout，而不是默认 universal layout。

---

F5：Propagation Swimlane

按时间或 estimated onset 排列 service：

text
time ───────────────────────────────────────────→

E07      metric spike ━━━━━━━━━━━━━
E04              trace latency ━━━━━━━━━━━━━
E01                        error burst ━━━━━━━


旁边附加 caller→callee 信息。

适合研究：

* earliest anomaly；
* root 与 propagated symptom 的区分；
* 多级传播路径；
* abnormality onset ordering。

第一阶段中，Qwen topology visual 的重要 repair 机制就是利用 onset 和调用方向，把较早出现的候选排到较晚的传播节点之前。

---

F6：Candidate Comparison Matrix

将 service 作为行，将诊断证据作为列：

| Service | Metric Δ | Persistence | ΔExL | ΔInL | Log burst | Onset | In/Out edges |
| ------- | -------: | ----------: | ---: | ---: | --------: | ----: | ------------ |
| E01     |    +2.1σ |        high | +0.1 | +3.2 |        no |    41 | 0/2          |
| E04     |    +1.0σ |         med | +2.8 | +3.0 |       yes |    30 | 1/1          |
| E07     |    +3.7σ |        high | +4.5 | +4.6 |       yes |    18 | 1/0          |

它更接近“machine-readable evidence board”，而不是传统面向人的 dashboard。

优点：

* 候选间直接比较非常容易；
* 字段对齐；
* 特别适合冻结 VLM 做 ranking。

缺点：

* 视觉结构优势有限；
* 容易退化为 pixel-text table；
* 必须控制字体、行数和精度。

---

F7：Focus + Context

将最值得详细检查的 2–4 个 service 画成大卡片，其余 service 只显示极简 summary：

text
Detailed:
[E07 large card] [E04 large card]

Context:
E01 ↑lat   E02 log-new   E03 normal   E05 trace-wait ...


这是工业 dashboard 中常见的“overview + focus”思想。在一张图的限制下，它可以近似替代 interactive drill-down。

---

三、Per-Service Modality Gate：如何表达“只画有用的数据”

对每个入选 service \(s_i\)，对三个局部 modality 定义：

$$
d_{i,m}\in\{0,1,2\},
\qquad
m\in\{M,Tr,L\}
$$

其中：

* \(0\)：不显示；
* \(1\)：显示 compact summary；
* \(2\)：显示 detailed chart。

为了避免 Trace 和全信息文本 arm 的 \(T\) 混淆，后续建议统一用 `Tr` 表示 traces。

例如：

| Service |  M | Tr |  L | 含义                              |
| ------- | -: | -: | -: | ------------------------------- |
| E01     |  2 |  0 |  0 | 详细显示 metrics                    |
| E02     |  0 |  0 |  2 | 详细显示 logs                       |
| E03     |  1 |  2 |  0 | metric summary + detailed trace |
| E04     |  1 |  1 |  1 | 三类证据都显示，但均为 compact             |
| E05     |  0 |  0 |  0 | 不应占据 service card               |

这里的“有用”不能来自 ground-truth label，而应来自 label-blind telemetry features：

* anomaly strength；
* onset；
* persistence；
* normal/current difference；
* exclusive latency；
* call-count change；
* new log template；
* error burst；
* topology neighborhood；
* modality disagreement。

全局 topology 则另外定义：

$$
g\in
\{
\text{none},
\text{selected-induced},
\text{selected+1hop},
\text{full-pruned},
\text{graph+ledger},
\text{onset-lanes}
\}
$$

我建议最初强制 \(g\neq\text{none}\)，因为 topology 是第一阶段最明确的正向视觉结构之一；但需要保留 no-G ablation。

---

四、各 Modality 的有限视觉编码字典

Dashboard Agent 不应自由发明 chart type，而应从经过验证的 encoding vocabulary 中选择。

4.1 Metrics

| Encoding ID | 表示形式                            | 主要作用                                 |
| ----------- | ------------------------------- | ------------------------------------ |
| M0          | stat-only card                  | baseline、current、signed change、onset |
| M1          | short sparkline + baseline band | 保留趋势和 persistence                    |
| M2          | normal/current paired bars      | 直接比较两个窗口                             |
| M3          | anomaly heat strip              | 高密度表达时间与异常方向                         |
| M4          | distribution comparison         | 区分均值变化与尾部变化                          |
| M5          | delta + persistence glyph       | 最低视觉成本的诊断摘要                          |

第一阶段说明，密集 metric curves 对 exact value、bin 和 metric identity 很不友好，所以 M1 不应成为默认；M0、M2、M3 和 M5 应被重点测试。

---

4.2 Traces

| Encoding ID | 表示形式                               | 主要作用                       |
| ----------- | ---------------------------------- | -------------------------- |
| Tr0         | ΔInL / ΔExL paired bar             | 区分本地变慢与等待下游                |
| Tr1         | call-count / latency compact table | 比较调用量和 local latency       |
| Tr2         | top-operation ranked rows          | 定位异常 operation             |
| Tr3         | mini trace waterfall               | 表达局部 parent-child 结构       |
| Tr4         | response-time contribution         | 显示该服务对端到端延迟的贡献             |
| Tr5         | edge-level RED card                | 显示 service-to-service 调用异常 |

Splunk 会列出 self-time 最高的 operations；Dynatrace 会显示下游调用、数据库调用和服务内部执行分别贡献了多少响应时间，这些都支持将 `InL/ExL/contribution` 作为主要 trace primitives，而不是简单展示原始 span。([Splunk Docs][3])

---

4.3 Logs

| Encoding ID | 表示形式                             | 主要作用                  |
| ----------- | -------------------------------- | --------------------- |
| L0          | template card                    | 保留错误语义和关键变量           |
| L1          | baseline/current rate comparison | 表达新增、突增或下降            |
| L2          | severity × time heat strip       | 表达事件时间分布              |
| L3          | event timeline                   | 与 deployment/onset 对齐 |
| L4          | top templates ranked list        | 高密度显示多个模式             |
| L5          | new/burst/drop flags             | 极低成本 summary          |

日志不应被变成纯 icon。第一阶段显示，自然语言日志仍然很强；合理做法是保留短文本骨架和诊断数字，但删除重复行。 

---

4.4 Topology

| Encoding ID | 表示形式                         | 适用情况           |
| ----------- | ---------------------------- | -------------- |
| G0          | node-link graph              | 稀疏 topology    |
| G1          | node-link + onset            | 强调传播顺序         |
| G2          | graph + explicit edge ledger | 减少方向误读         |
| G3          | propagation swimlane         | 时序传播明显         |
| G4          | adjacency matrix             | dense topology |
| G5          | selected induced subgraph    | service 数较多    |
| G6          | selected + one-hop context   | 保留局部上下游关系      |

当边数多时，不应强制使用 node-link graph。Dense graph 可以切换成 adjacency matrix 或 pruned local topology。

---

五、为什么应采用“半离散空间”，而不是完全离散或完全连续

5.1 第一阶段：离散结构化 DSL

Dashboard Agent 直接产生：

* layout family；
* selected services；
* modality detail level；
* encoding ID；
* global topology mode；
* ordering mode；
* budget tier。

优点：

* 可验证；
* 可复现；
* 可以 constrained decoding；
* 便于做完整消融；
* 不容易通过像素纹理偷偷编码答案。

5.2 第二阶段：连续 utility score + 确定性 packer

当离散 selector 可行后，让 SLM 输出：

$$
q_i=\text{service utility}
$$

$$
q_{i,m}=\text{modality utility}
$$

$$
a_{i,m}=\text{desired visual area}
$$

再由确定性布局器解决：

$$
\max_z
\sum_{i,m}q_{i,m}u(e_{i,m})
$$

subject to：

$$
\sum_{i,m}Cost(e_{i,m},a_{i,m})\le B
$$

并满足：

* 最小字体；
* 最小 chart 尺寸；
* 最大 service 数；
* 最大 evidence card 数；
* 不重叠；
* 单图；
* provenance 完整。

实际面积最好量化成：

$$
a_{i,m}\in\{\text{small},\text{medium},\text{large}\}
$$

或者 8 个离散档位，而不是允许任意像素坐标。

5.3 不建议完全自由的连续像素空间

原因包括：

* Frozen VLM reward 不可微；
* 搜索空间极大；
* 很难保证 telemetry fidelity；
* 极易产生 covert visual channel；
* 很难区分“视觉设计”与“SLM 已经猜出根因后编码答案”；
* 不利于 reviewer 复现。

---

六、建议的 Dashboard DSL

yaml
layout:
  family: HYBRID_SERVICE_GLOBAL_G
  service_arrangement: ROW_MATRIX
  service_order: FIXED_CASE_ID

global:
  topology:
    mode: SELECTED_PLUS_ONE_HOP
    encoding: GRAPH_PLUS_EDGE_LEDGER
  onset_strip: true
  sli_strip: false

services:
  - id: E07
    metric:
      detail: 2
      encoding: DELTA_STAT_SPARKLINE
      facts: [M_E07_03, M_E07_11]
    trace:
      detail: 1
      encoding: INL_EXL_PAIR
      facts: [TR_E07_02]
    log:
      detail: 0

  - id: E04
    metric:
      detail: 0
    trace:
      detail: 1
      encoding: EDGE_RED_CARD
      facts: [TR_E04_06]
    log:
      detail: 2
      encoding: TEMPLATE_CARD
      facts: [L_E04_01, L_E04_04]

budget:
  max_services: 12
  max_cards: 18
  max_visual_tokens: 2100
  min_font_px: 18
  temporal_bins: 32

style:
  palette_id: FIXED_03
  font_id: FIXED_01


关键设计：

* `facts` 必须指向 canonical IR 中真实存在的 fact ID；
* renderer 不接受 Dashboard Agent 自由生成的新数字和自由文本；
* style 最初不由 agent 控制；
* palette、font、stroke 和 decorative elements 应固定或随机化；
* service order 最初也应固定，避免 agent 通过第一行位置直接传递 root prediction。

---

七、从大型运维产品中得到的设计启示

7.1 Service-centric 是主流组织方式

Google SRE 将 dashboard 定义为 service 核心指标的 summary view，强调 dashboard 应回答明确的服务问题，并优先覆盖 latency、traffic、errors 和 saturation；同时强调监控系统应尽可能简单、低噪声。([Google SRE][4])

Grafana 明确展示了：

* 一个 service 一行；
* 行顺序遵循 data flow；
* service 用 RED：Rate、Errors、Duration；
* infrastructure 用 USE；
* 不要展示全部对象，只展示需要调查的异常对象。([Grafana][1])

这直接支持 F1/F3，而不是固定四大 modality panel。

7.2 全局 topology + 局部 service evidence 是稳定模式

AWS CloudWatch、Datadog 和 Splunk 均采用：

1. 全局 application/service map；
2. 选择或隔离 service；
3. 查看该 service 的 latency、requests、errors、dependencies、logs 和 traces。

AWS 还会按 dependency 自动分组，并突出 SLO breach；Datadog 支持 isolating a service 和查看 upstream/downstream；Splunk 支持只显示某节点及其 immediate dependencies。([AWS 文档][2])

这支持：

> **Global G + adaptive per-service M/Tr/L cards**

作为 CanvasRCA 的默认主 family。

## 7.3 当前状态应与正常状态对照

New Relic Lookout 默认比较最近五分钟和此前一小时，用：

* 大小表达 deviation magnitude；
* 颜色表达变化方向或严重性；
* 排序表达需要优先关注的实体。([New Relic 文档][5])

Honeycomb BubbleUp 也以“被选择的异常 population 与 baseline population 的字段分布差异”为核心。([Honeycomb Docs][6])

所以每个 service card 不应只画 current curve，而应优先表达：

$$
normal\rightarrow current
$$

这比单纯显示异常值更能跨数据集泛化。

7.4 Dense graph 必须过滤和聚合

Dynatrace 会根据响应时间贡献聚合低贡献 services，以提高 service-flow 的可读性；Azure Application Map 的 Intelligent View 会过滤大量节点和边，只突出需要调查的 hotspot edges，并使用 failure rate、request count、duration、anomaly 和 dependency type 等信号。([Dynatrace 文档][7])

这说明 CanvasRCA 中的 G 不应总是显示完整 graph，而应允许：

* selected induced graph；
* one-hop context；
* low-impact node aggregation；
* graph + edge ledger；
* dense graph → adjacency matrix。

---

八、Reward 与训练信号

8.1 先执行 hard constraints

以下任一失败，dashboard reward 直接设为最低：

* DSL 无法解析；
* 显示不存在的 telemetry fact；
* 数值与 canonical IR 不一致；
* 使用 root label、fault label、dataset ID 或 case ID；
* 超出单图预算；
* 字体或图表低于可读尺寸；
* service ID 重复或映射错误；
* provenance 缺失；
* 使用未批准的自由文本、纹理或颜色通道。

8.2 RCA utility reward

对于 receiver \(v\)：

$$
R_v =
RR_v
+\alpha\mathbf 1[\text{Top1 correct}]
+\beta R_{\text{grounding}}
+\gamma R_{\text{causal-order}}
$$

其中：

* \(RR_v\)：真实根因 reciprocal rank；
* `Top1 correct`：第一名命中；
* \(R_{\text{grounding}}\)：VLM 引用的 evidence ID 是否存在；
* \(R_{\text{causal-order}}\)：是否将真实根因排在已知 propagated symptoms 之前。

不要只用 AC@1，否则第二名和完全遗漏会得到同样的 0 reward，训练信号过于稀疏。

8.3 多 receiver reward

训练 universal dashboard：

$$
R_{\mathrm{avg}}
=
\frac{R_Q+R_G}{2}
$$

更加稳健的版本：

$$
R_{\mathrm{robust}}
=
\mu \frac{R_Q+R_G}{2}
+
(1-\mu)\min(R_Q,R_G)
$$

还应训练：

* Qwen-specific builder；
* Gemma-specific builder；
* receiver-conditioned builder；
* universal/minimax builder。

第一阶段中，同一 topology visual 对 Qwen 和 Gemma 的作用明显不同，因此“是否存在 universal machine dashboard grammar”本身就是一个重要 RQ。

8.4 Cost reward

建议将 receiver visual-token budget 设为 hard constraint，例如：

$$
Tok_{\mathrm{VLM}}\le 0.5 Tok_{\mathrm{TextTwin}}
$$

而不是完全依赖 token penalty。否则 agent 可能通过：

* 只显示一个 service；
* 删除所有困难证据；
* 让 receiver 只输出一个候选；

来投机降低成本。

可在满足预算后增加较弱的成本项：

$$
R_{\mathrm{cost}}
=
-\lambda_1 Tok_{\mathrm{SLM}}
-\lambda_2 Latency_{\mathrm{SLM}}
-\lambda_3 Latency_{\mathrm{render}}
$$

---

九、最重要的实验分解：Selection 和 Presentation 必须分开

否则 reviewer 会认为 Dashboard Agent 已经自己完成 RCA，只是把答案画给 VLM。

建议设计以下 arms：

| Arm                      | Evidence selection | 表示                     | 回答者        | 回答的问题              |
| ------------------------ | ------------------ | ---------------------- | ---------- | ------------------ |
| RawText                  | 旧固定规则              | 长文本                    | Frozen VLM | 当前文本 baseline      |
| TextTwin                 | 固定、与 Canvas 相同     | compact text           | Frozen VLM | 信息对等文本             |
| FixedCanvas              | 固定                 | 固定 dashboard           | Frozen VLM | 最佳固定视觉表示           |
| Learned-Presentation     | 固定                 | SLM 只选 layout/encoding | Frozen VLM | 视觉设计本身的贡献          |
| Learned-Selection-Text   | SLM 选择             | compact text           | Frozen VLM | 数据筛选贡献             |
| Learned-Selection-Canvas | SLM 选择             | 固定 canvas              | Frozen VLM | selection + visual |
| Full CanvasRCA           | SLM 选择并设计          | learned canvas         | Frozen VLM | 完整系统               |
| Direct-SLM               | SLM 直接输出 root      | 无                      | SLM        | SLM 本身是否已能做 RCA    |
| Oracle-Design            | 每 case 选最佳合法设计     | canvas                 | Frozen VLM | 设计空间上界             |

尤其要比较：

$$
\text{Learned-Selection-Canvas}
\quad vs.\quad
\text{Learned-Selection-Text}
$$

因为这才能证明图像是否在同一个 learned preprocessor 后仍有额外价值。

---

十、下一阶段完整实验计划

Phase 0：协议冻结

1. 当前 469 cases 全部作为 development；
2. 新建 untouched confirmation set；
3. 建立 canonical telemetry IR；
4. 每个事实分配 provenance ID；
5. 建立 Dashboard DSL 和 deterministic renderer；
6. 从同一个 DSL 生成 CanvasTwin 和 TextTwin；
7. 固定 RCA VLM prompt、output schema 和 decoding。

报告本身已经明确将当前评估定义为 exploratory、repeated-exposed，而不是 untouched confirmation。 

---

Phase 1：建立 24–48 个固定 Dashboard Specifications

不是完整笛卡尔积，而是覆盖：

* 8 个 layout families；
* 3 种 service 数：8、12、16；
* 3 种 modality gating policy；
* 4 种 topology mode；
* 若干重点 encoding combinations。

先在约 120 个 stratified development cases 上运行：

* Qwen；
* Gemma；
* TextTwin；
* Direct-QA 子任务；
* candidate coverage 和 grounding。

筛选到 8–12 个有明显差异、性能较好的 dashboard specs。

---

Phase 2：计算 Per-Case Oracle Headroom

对每个 case 计算：

$$
RR_i^{oracle}
=
\max_{z\in\mathcal Z}RR_{i,z}
$$

然后计算：

$$
Gap_{\text{adaptive}}
=
MRR_{\text{oracle}}
-
MRR_{\text{best-fixed}}
$$

建议 go/no-go：

* \(Gap\ge0.03\)：训练 adaptive policy 很有价值；
* \(Gap\ge0.08\)：这是非常强的研究信号；
* \(Gap<0.01\)：应先扩展或改进设计空间，而不是急着做 RL。

第一阶段 TPV、V_LG、V_MG 同时存在大量不同方向的 repair/break，已经提示 per-case oracle 可能具有较大空间。

---

Phase 3：离散 Dashboard Selector

第一版 Dashboard Agent 只需要从 8–12 个模板中选一个：

$$
\pi_\phi(X,r,B)\rightarrow z_k
$$

比较：

* random selector；
* global best fixed；
* supervised oracle-template classifier；
* DPO selector；
* GRPO contextual-bandit selector；
* oracle selector。

这一步可以低成本验证核心命题：

> Incident-adaptive dashboard 是否超过任何统一固定 dashboard？

---

Phase 4：Compositional Dashboard Agent

离散 selector 成功后，让 SLM输出完整 DSL：

1. SFT：学习合法 DSL 和约束；
2. best-of-\(N\) sampling：每个 case 生成 8–16 个 dashboard；
3. Frozen VLM 对所有 dashboard 打 reward；
4. 构造 preference pairs；
5. DPO；
6. hard-case GRPO；
7. 最终 inference 只生成一张 dashboard，不允许 best-of-\(N\)。

DashBot 已把 dashboard generation 表述为受约束的 RL 问题，并将 presentation、parsimony 和 insightfulness 放入 reward；你们的关键区别是把下游 frozen VLM 的 RCA utility 作为主 reward。([arXiv][8])

HORNet 则提供了更接近的训练范式：训练轻量 policy 决定冻结 VLM 应看到哪些输入，并使用 GRPO 根据下游回答质量优化 policy。([arXiv][9])

---

Phase 5：Shortcut 与 Covert Channel 审计

必须包括：

1. **Value-masked**：隐藏全部 telemetry values，只保留 layout/style；
2. **Fixed-order**：禁止 agent 排 service；
3. **Random-ID**：随机重编号 services；
4. **Random-palette/font**：语义不变，随机 style；
5. **Layout permutation**：同一 DSL 的合法 nuisance variations；
6. **Direct-SLM RCA**；
7. **Learned-Text control**；
8. **Evidence occlusion**：遮挡被引用的关键 evidence；
9. **Unseen renderer style**；
10. **Root-position distribution audit**。

Value-masked 条件如果仍显著高于随机，就说明 agent 在通过位置或样式编码自己的 root prediction。

---

Phase 6：跨数据集和跨 receiver 泛化

进行：

* leave-one-dataset-out；
* system-held-out；
* fault-type-held-out；
* topology-size-held-out；
* unseen metric names；
* log template paraphrase；
* unit conversion；
* sampling-frequency change；
* missing modality；
* service-ID randomization；
* Qwen-trained builder → Gemma；
* Gemma-trained builder → Qwen；
* universal builder → unseen VLM。

---

Phase 7：最终 SOTA 评估

至少包括：

* RCAEval；
* GALA+ 的 exact OnlineBoutique/TrainTicket protocol；
* DynaCausal 对应 split；
* 1,430-case fault-propagation-aware benchmark；
* internal untouched confirmation set。

最终主图不是单一 `MRR/token`，而应是：

* MRR–receiver-token Pareto frontier；
* MRR–end-to-end latency frontier；
* token saving at 95% TextTwin performance；
* MRR at 50% TextTwin budget；
* worst-dataset performance。

---

十一、建议的成功门槛

| 指标                           |                     Gate |
| ---------------------------- | -----------------------: |
| Root candidate recall@K      |                     ≥98% |
| DSL validity                 |                   ≥99.5% |
| Visual fact fidelity         |                   ≥99.5% |
| Receiver input saving        |                     ≥50% |
| Canvas vs TextTwin           |       非劣界 \(>-0.02\) MRR |
| Relative MRR retention       |                     ≥95% |
| Learned policy vs best fixed |               ≥+0.03 MRR |
| Nuisance consistency         |     ≥90% top-1 agreement |
| Value-masked accuracy        |                     接近随机 |
| Worst-dataset degradation    |             不超过 0.05 MRR |
| External performance         | 超过 protocol-matched SOTA |

---

十二、参考文献库

下面是本轮和上一轮真正相关的参考资料。可以直接交给本地 coding/planning agent 分类建库。

A. Dashboard、Visualization Grammar 与自动设计

1. **What Do We Talk About When We Talk About Dashboards?**
   Dashboard 目标、交互和实践的总体设计空间；DOI: 10.1109/TVCG.2018.2864903。([PubMed][10])

2. **Dashboard Design Patterns**，arXiv:2205.00757。
   从真实 dashboard 中抽象多类 composition/design patterns。([arXiv][11])

3. **DMiner: Dashboard Design Mining and Recommendation**，arXiv:2209.01599。
   从大量 dashboard 中挖掘布局与协调特征。([arXiv][12])

4. **DashBot: Insight-Driven Dashboard Generation Based on Deep Reinforcement Learning**，arXiv:2208.01232。
   最直接的 RL dashboard generation 先例。([arXiv][8])

5. **NL2Dashboard: A Lightweight and Controllable Framework for Generating Dashboards with LLMs**，arXiv:2601.06126。
   Structured IR、analysis/presentation decoupling、deterministic rendering。([arXiv][13])

6. **Vega-Lite: A Grammar of Interactive Graphics**。
   视觉 encoding、mark、transform 和 composition grammar；DOI: 10.1109/TVCG.2016.2599030。([数字对象标识符][14])

7. **Formalizing Visualization Design Knowledge as Constraints: Actionable and Extensible Models in Draco**。
   Hard/soft constraint 设计空间和可学习偏好权重。([Bohrium][15])

8. **Draco 2: An Extensible Platform to Model Visualization Design**，arXiv:2308.14247。
   Renderer-agnostic structured specification 和 multi-view constraints。([arXiv][16])

9. **Lyra: An Interactive Visualization Design Environment**。
   将 data、transform、mark、scale、layout 拆成可操作 primitives。([UW Interactive Data Lab][17])

10. **Semantic Snapping for Guided Multi-View Visualization Design**。
    多视图共享字段、scale 和布局时的 consistency constraints。([IEEE VIS Virtual][18])

11. **A Nested Model for Visualization Design and Validation**。
    Domain problem → data/task abstraction → encoding/interaction → algorithm；DOI: 10.1109/TVCG.2009.111。([数字对象标识符][19])

12. **Voyager: Exploratory Analysis via Faceted Browsing of Visualization Recommendations**。
    有限 grammar、规则和推荐排序。([CMU Data Interaction Group][20])

13. **Mod2Dash: A Model-Driven Approach to Dashboard Generation**。
    显式模型和 dashboard generation separation。([arXiv][21])

14. **Toward a Machine Bertin: Machine-Oriented Visualization Design Principles**，arXiv:2602.01527。
    强调面向机器的可视化不应简单照搬面向人的 perceptual guidelines。([arXiv][22])

15. **DracoGPT**。
    研究 LLM 与传统 visualization constraints/人类偏好的差异。([arXiv][23])

16. **Large-Scale Census of 25,620 Tableau Dashboards**。
    可用于提取真实 dashboard 的 chart、layout 和 composition 先验。([arXiv][24])

---

B. 大型公司的运维 Dashboard 和 Observability 设计

1. **Google SRE — Monitoring Distributed Systems**。
   Four Golden Signals、低噪声、简单和 service-oriented dashboard。([Google SRE][4])

2. **Grafana Dashboard Best Practices**。
   RED/USE、one row per service、data-flow order、只显示异常对象。([Grafana][1])

3. **AWS CloudWatch Application Map / Service Detail**。
   全局 topology、dependency grouping、SLO health、per-service detail。([AWS 文档][2])

4. **Datadog Service Map / Service Page**。
   动态依赖、service isolation、upstream/downstream、RED、logs 和 traces。([Datadog监控][25])

5. **Splunk APM Service Map / Service View**。
   global map + per-service SLI、RED、runtime、infrastructure、logs、traces。([Splunk Docs][26])

6. **Dynatrace Service Flow / Response Time Analysis**。
   response-time contribution、downstream waiting、低贡献 service 聚合。([Dynatrace 文档][27])

7. **New Relic Lookout**。
   当前窗口与历史窗口对比，按 deviation 的大小、颜色和排序分配显著性。([New Relic 文档][5])

8. **Honeycomb BubbleUp**。
   比较异常 selection 与 baseline population 的字段分布。([Honeycomb Docs][6])

9. **Azure Application Insights Application Map / Intelligent View**。
   过滤复杂 topology，突出 failure/performance hotspot edges。([Microsoft Learn][28])

---

C. Chart、Dashboard 与 VLM

1. **On the Perception Bottleneck of VLMs for Chart Understanding**，arXiv:2503.18435。
   区分 vision encoder information loss 与 language-side extraction failure。([arXiv][29])

2. **DashboardQA**，arXiv:2508.17398。
   多区域 dashboard grounding 和跨 panel reasoning。([arXiv][30])

3. **VLM²-Bench**。
   视觉上连接、匹配多个线索本身是一项独立困难。([arXiv][31])

4. **ChartMuseum**，arXiv:2505.13444。
   高复杂度 chart reasoning，visual-heavy 问题显著困难。([arXiv][32])

5. **Visual Graph Understanding / VGCure**。
   VLM 在边方向、邻接、集合和结构推理上的局限。([arXiv][33])

6. **Words or Vision: Do Vision-Language Models Have a Text Bias?**
   分析 multimodal 输入中的 text preference 和顺序影响。([arXiv][34])

7. **Text or Pixels? Evaluating Efficiency and Understanding of LLMs with Visual Text Inputs**，arXiv:2510.18279，EMNLP Findings 2025。
   视觉文本压缩和 token efficiency；不等于说明 RCA screenshot 可行。([arXiv][35])

8. **LensVLM: Selective Context Expansion for Compressed Visual Representation of Text**，arXiv:2605.07019。
   分析高压缩下的视觉分辨率瓶颈；其 expansion 是多阶段方法，只适合作为机制参考。([arXiv][36])

9. **S-VCO: Symmetrical Visual Contrastive Optimization**，arXiv:2502.13928。
   用 minimal visual contrasts 增强视觉 grounding。([arXiv][37])

10. **BlackVIP: Black-Box Visual Prompting for Robust Transfer Learning**，arXiv:2303.14773。
    不更新 receiver，通过 input-dependent visual prompt 调整冻结模型行为。([arXiv][38])

11. **HORNet**，arXiv:2603.18850。
    训练轻量 policy 选择冻结 VLM 应看到的输入，并使用 GRPO 优化 downstream utility。([arXiv][9])

12. **Chart-R1**。
    Programmatic chart synthesis、SFT warm start 和 GRPO。([arXiv][39])

13. **Chart-RVR**，arXiv:2507.15509。
    chart type、table reconstruction 和 reasoning process 的 verifiable rewards。([arXiv][40])

14. **Chart-RL**。
    Verifiable RL，并分析 complex training examples 的重要性。([arXiv][41])

15. **ChartVerse**，arXiv:2601.13606。
    answer-first synthetic generation、严格一致性过滤、SFT/RL 数据构造。([arXiv][42])

---

D. RCA、Fault Localization 与跨系统泛化

1. **RCAEval: A Benchmark for Root Cause Analysis of Microservice Systems**，arXiv:2412.17015。
   735 cases 和 15 个可复现 baselines。([arXiv][43])

2. **MicroRCA: Root Cause Localization of Performance Issues in Microservices**。
   attributed graph、service dependencies 与 resource correlation。([数字对象标识符][44])

3. **MicroRank: End-to-End Latency Issue Localization with Extended Spectrum Analysis**。
   normal/abnormal traces、PageRank 与 spectrum-based localization。([数字对象标识符][45])

4. **MicroHECL: High-Efficient Root Cause Localization in Large-Scale Microservice Systems**，arXiv:2103.01782。
   动态调用图、传播链和 graph pruning。([arXiv][46])

5. **Eadro: An End-to-End Troubleshooting Framework for Microservices on Multi-source Data**。
   联合 anomaly detection 与 root cause localization。([arXiv][47])

6. **DiagFusion: Towards Effective and Interpretable Diagnosis in Microservice Systems via Multi-Modal Data**。
   metrics、logs、traces 的多模态融合和图推理。([arXiv][48])

7. **CausalRCA: Causal Inference Based Precise Fine-Grained Root Cause Localization**。
   weighted causal graph 与 metric-level RCA。([arXiv][49])

8. **TraceDiag**。
   使用 reinforcement learning 进行 trace graph pruning 和 fault localization。([arXiv][50])

9. **DynaCausal: Dynamic Multimodal Root Cause Analysis**，arXiv:2510.22613。
   normal/current contrast、动态因果关系和 causal-prioritized pairwise ranking。([arXiv][51])

10. **GALA+: Graph-Guided Agentic Root Cause Analysis**，arXiv:2608.08968。
    candidate generation、localized diagnostic bundles、graph-guided multi-stage investigation。([arXiv][52])

11. **MetaRCA**，arXiv:2603.02032。
    可复用 meta-causal knowledge 和跨系统 generalization。([arXiv][53])

12. **Beyond Fault Localization: Evaluating Evidence and Reasoning Quality in LLM-Based RCA**，arXiv:2608.21310。
    强调最终答案正确不代表 evidence 或 diagnostic trajectory 正确。([arXiv][54])

13. **A Fault-Propagation-Aware Benchmark for Microservice RCA**，arXiv:2510.04711。
    1,430 个 validated cases、25 种 fault types，用于更困难的 SOTA comparison。([arXiv][55])

14. **TORAI**。
    研究实际 microservice telemetry 中的 observability blind spots 和不完整调用图。([arXiv][56])

15. **NexusRCL**。
    处理 service/host 等异构节点与跨层 root localization。([arXiv][57])

16. **CARE: Context-Aware Root Cause Analysis with Spectrum Analysis**。
    Context-aware fault localization 和候选排序。([Researchr][58])

---

E. Dashboard Agent 的训练方法

1. **LoRA: Low-Rank Adaptation of Large Language Models**，arXiv:2106.09685。
   本项目采用 BF16 base weights + LoRA，不做低比特量化。([arXiv][59])

2. **DoRA: Weight-Decomposed Low-Rank Adaptation**，arXiv:2402.09353。
   可作为 LoRA 的非量化 PEFT 对照。([arXiv][60])

3. **Direct Preference Optimization: Your Language Model is Secretly a Reward Model**，arXiv:2305.18290。
   适合使用 same-case dashboard preference pairs。([arXiv][61])

4. **SimPO: Simple Preference Optimization with a Reference-Free Reward**，arXiv:2405.14734。
   可作为不常驻 reference model 的 preference baseline。([arXiv][62])

5. **DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models**，arXiv:2402.03300。
   GRPO 的原始重要来源，适合 one-step contextual-bandit dashboard policy。([arXiv.gg][63])

---

最先应执行的三个实验

优先顺序应当非常明确：

1. **实现 F1、F2、F3、F5、F6 五种布局，并在完全相同事实下与 TextTwin 配对。**
2. **构造 24–48 个固定 dashboard specifications，计算 best-fixed 和 per-case oracle gap。**
3. **若 oracle gap ≥0.03 MRR，再训练一个仅从 8–12 个模板中选择的 BF16 Dashboard SLM；先证明 adaptive selection 有价值，再进入完整 DSL、DPO 和 GRPO。**

这一顺序可以最快回答项目当前最重要的问题：

> 是设计空间本身没有足够好的 dashboard，还是已经存在好 dashboard，只是需要一个 learned policy 针对不同 incident、不同 receiver 做选择？

[1]: https://grafana.com/docs/grafana/latest/visualizations/dashboards/build-dashboards/best-practices/ "https://grafana.com/docs/grafana/latest/visualizations/dashboards/build-dashboards/best-practices/"
[2]: https://docs.aws.amazon.com/hi_in/AmazonCloudWatch/latest/monitoring/ServiceMap.html "https://docs.aws.amazon.com/hi_in/AmazonCloudWatch/latest/monitoring/ServiceMap.html"
[3]: https://help.splunk.com/en/splunk-observability-cloud/monitor-application-performance/manage-services-spans-and-traces-in-splunk-apm/view-and-filter-for-spans-within-a-trace "https://help.splunk.com/en/splunk-observability-cloud/monitor-application-performance/manage-services-spans-and-traces-in-splunk-apm/view-and-filter-for-spans-within-a-trace"
[4]: https://sre.google/sre-book/monitoring-distributed-systems/ "https://sre.google/sre-book/monitoring-distributed-systems/"
[5]: https://docs.newrelic.com/docs/new-relic-solutions/new-relic-one/core-concepts/new-relic-explorer-view-performance-across-apps-services-hosts/ "https://docs.newrelic.com/docs/new-relic-solutions/new-relic-one/core-concepts/new-relic-explorer-view-performance-across-apps-services-hosts/"
[6]: https://docs.honeycomb.io/investigate/analyze/identify-outliers/ "https://docs.honeycomb.io/investigate/analyze/identify-outliers/"
[7]: https://docs.dynatrace.com/docs/observe/application-observability/services-classic/service-flow "https://docs.dynatrace.com/docs/observe/application-observability/services-classic/service-flow"
[8]: https://arxiv.org/abs/2208.01232 "https://arxiv.org/abs/2208.01232"
[9]: https://arxiv.org/abs/2603.18850 "https://arxiv.org/abs/2603.18850"
[10]: https://pubmed.ncbi.nlm.nih.gov/30136958/ "https://pubmed.ncbi.nlm.nih.gov/30136958/"
[11]: https://arxiv.org/abs/2205.00757 "https://arxiv.org/abs/2205.00757"
[12]: https://arxiv.org/abs/2209.01599 "https://arxiv.org/abs/2209.01599"
[13]: https://arxiv.org/abs/2601.06126 "https://arxiv.org/abs/2601.06126"
[14]: https://doi.org/10.1109/tvcg.2016.2599030 "https://doi.org/10.1109/tvcg.2016.2599030"
[15]: https://bohrium.dp.tech/paper/arxiv/2fa999d413e840cfc7a1268eb0ed2f77f923428aef269585e82689356d8eb29b "https://bohrium.dp.tech/paper/arxiv/2fa999d413e840cfc7a1268eb0ed2f77f923428aef269585e82689356d8eb29b"
[16]: https://arxiv.org/abs/2308.14247 "https://arxiv.org/abs/2308.14247"
[17]: https://idl.cs.washington.edu/projects/lyra/ "https://idl.cs.washington.edu/projects/lyra/"
[18]: https://virtual.ieeevis.org/year/2021/paper_v-full-1349.html "https://virtual.ieeevis.org/year/2021/paper_v-full-1349.html"
[19]: https://doi.org/10.1109/TVCG.2009.111 "https://doi.org/10.1109/TVCG.2009.111"
[20]: https://dig.cmu.edu/publications/2015-voyager.html "https://dig.cmu.edu/publications/2015-voyager.html"
[21]: https://arxiv.org/abs/2205.07204 "https://arxiv.org/abs/2205.07204"
[22]: https://arxiv.org/abs/2602.01527 "https://arxiv.org/abs/2602.01527"
[23]: https://arxiv.org/abs/2408.06845 "https://arxiv.org/abs/2408.06845"
[24]: https://arxiv.org/abs/2306.16513 "https://arxiv.org/abs/2306.16513"
[25]: https://docs.datadoghq.com/tracing/services/services_map/ "https://docs.datadoghq.com/tracing/services/services_map/"
[26]: https://help.splunk.com/en/splunk-observability-cloud/monitor-application-performance/manage-services-spans-and-traces-in-splunk-apm/use-the-service-view-in-splunk-apm "https://help.splunk.com/en/splunk-observability-cloud/monitor-application-performance/manage-services-spans-and-traces-in-splunk-apm/use-the-service-view-in-splunk-apm"
[27]: https://docs.dynatrace.com/docs/observe/application-observability/services/response-time-analysis "https://docs.dynatrace.com/docs/observe/application-observability/services/response-time-analysis"
[28]: https://learn.microsoft.com/en-us/azure/azure-monitor/app/app-map "https://learn.microsoft.com/en-us/azure/azure-monitor/app/app-map"
[29]: https://arxiv.org/abs/2503.18435 "https://arxiv.org/abs/2503.18435"
[30]: https://arxiv.org/abs/2508.17398 "https://arxiv.org/abs/2508.17398"
[31]: https://arxiv.org/abs/2502.12084 "https://arxiv.org/abs/2502.12084"
[32]: https://arxiv.org/abs/2505.13444 "https://arxiv.org/abs/2505.13444"
[33]: https://arxiv.org/abs/2412.13540 "https://arxiv.org/abs/2412.13540"
[34]: https://arxiv.org/abs/2503.02199 "https://arxiv.org/abs/2503.02199"
[35]: https://arxiv.org/abs/2510.18279 "https://arxiv.org/abs/2510.18279"
[36]: https://arxiv.org/abs/2605.07019 "https://arxiv.org/abs/2605.07019"
[37]: https://arxiv.org/abs/2502.13928 "https://arxiv.org/abs/2502.13928"
[38]: https://arxiv.org/abs/2303.14773 "https://arxiv.org/abs/2303.14773"
[39]: https://arxiv.org/abs/2507.15509 "https://arxiv.org/abs/2507.15509"
[40]: https://arxiv.org/abs/2510.10973 "https://arxiv.org/abs/2510.10973"
[41]: https://arxiv.org/abs/2603.06958 "https://arxiv.org/abs/2603.06958"
[42]: https://arxiv.org/abs/2601.13606 "https://arxiv.org/abs/2601.13606"
[43]: https://arxiv.org/abs/2412.17015 "https://arxiv.org/abs/2412.17015"
[44]: https://doi.org/10.1109/noms47738.2020.9110353 "https://doi.org/10.1109/noms47738.2020.9110353"
[45]: https://doi.org/10.1145/3442381.3449905 "https://doi.org/10.1145/3442381.3449905"
[46]: https://arxiv.org/abs/2103.01782 "https://arxiv.org/abs/2103.01782"
[47]: https://arxiv.org/abs/2302.05092 "https://arxiv.org/abs/2302.05092"
[48]: https://arxiv.org/abs/2302.10512 "https://arxiv.org/abs/2302.10512"
[49]: https://arxiv.org/abs/2209.02500 "https://arxiv.org/abs/2209.02500"
[50]: https://arxiv.org/abs/2310.18740 "https://arxiv.org/abs/2310.18740"
[51]: https://arxiv.org/abs/2510.22613 "https://arxiv.org/abs/2510.22613"
[52]: https://arxiv.org/abs/2608.08968 "https://arxiv.org/abs/2608.08968"
[53]: https://arxiv.org/abs/2603.02032 "https://arxiv.org/abs/2603.02032"
[54]: https://arxiv.org/abs/2608.21310 "https://arxiv.org/abs/2608.21310"
[55]: https://arxiv.org/abs/2510.04711 "https://arxiv.org/abs/2510.04711"
[56]: https://arxiv.org/abs/2604.13522 "https://arxiv.org/abs/2604.13522"
[57]: https://arxiv.org/abs/2604.26670 "https://arxiv.org/abs/2604.26670"
[58]: https://conf.researchr.org/details/fse-2026/fse-2026-journal-first/32/CARE-Context-Aware-Root-Cause-Identification-Using-Distributed-Traces-and-Profiling- "https://conf.researchr.org/details/fse-2026/fse-2026-journal-first/32/CARE-Context-Aware-Root-Cause-Identification-Using-Distributed-Traces-and-Profiling-"
[59]: https://arxiv.org/abs/2106.09685 "https://arxiv.org/abs/2106.09685"
[60]: https://arxiv.org/abs/2402.09353 "https://arxiv.org/abs/2402.09353"
[61]: https://arxiv.org/abs/2305.18290 "https://arxiv.org/abs/2305.18290"
[62]: https://arxiv.org/abs/2405.14734 "https://arxiv.org/abs/2405.14734"
[63]: https://arxiv.gg/abs/2402.03300 "https://arxiv.gg/abs/2402.03300"
```
