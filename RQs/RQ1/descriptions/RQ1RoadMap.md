# 我的判断

**不要再做一次更复杂的静态 H/T/I 实验，试图把 RQ0 的负结果“跑成正结果”。**

RQ0 已经以相当严格的方式回答了一个明确问题：

> 当文本已经包含完整时间序列、具体调用边、传播路径、onset、persistence、missingness、logs 和 traces 时，再附加一张静态 dashboard，不能提高当前 frozen VLM 的 one-shot RCA performance。

这个结果应当保留，而且实际上很有价值。

但它否定的只是：

> **Redundant static visual augmentation**

它没有否定：

> **Dashboard 作为预算受限、可交互、可选择的信息访问接口是否有用。**

你们当前的 `CanonicalEvidenceBundle` 已经替模型完成了大量原本由 dashboard 或工程师完成的工作：

* 遥测对齐；
* 时间分桶；
* 完整序列整理；
* entity normalization；
* edge extraction；
* path extraction；
* 缺失值标注；
* evidence compression。

因此，RQ0 的 text-only arm 并不是“工程师逐行读原始 telemetry”，而是一个非常强的、接近 lossless observability compiler 的文本输出。图像在这个条件下只能提供第二种冗余编码，同时引入视觉噪声和跨模态冲突。

你们的结果已经说明了这一点：

* 图像会改变答案；
* 图像不是完全没被读取；
* 但图像修复的错误少于它新制造的错误；
* topology 可读性改善后仍未稳定提高 RCA；
* 因而当前瓶颈主要不是“看不见”，而是**什么时候应该相信视觉信息，以及如何把视觉证据整合进诊断**。

VLM 依赖文本而弱化视觉、发生 modality collapse，并不是你们项目特有的异常现象。现有综述也指出，VLM 经常依赖文本而忽视或错误利用视觉信号。([ACL Anthology][1])

---

# 一、应该怎样重新定义 RQ1

原来的宽泛问题：

> Under equal-information and equal-compute conditions, does visual–text, topology-aware observability improve VLM-based RCA?

实际上已经被 RQ0 回答了：

> 对当前静态、one-shot、full-information 设定，不提高。

因此，不应重复问同一个问题。更合理的总问题是：

> **RQ1. Under equal evidence access and matched investigation budgets, when and how does visual–text, topology-aware observability provide incremental value for VLM-based RCA?**

建议把 RQ1 拆成四个递进子问题。

## RQ1a — Static visual augmentation

> **Under full-information one-shot conditions, does adding a static dashboard to a lossless textual representation improve RCA?**

这个问题已经完成。

结论是：

> **No. Static redundant visual augmentation does not improve RCA for the evaluated models and datasets.**

不要删除这个负结果，也不要降级成 pilot。它是后续方法存在的直接动机。

---

## RQ1b — Modality complementarity

> **Which RCA reasoning operations benefit from visual representations, and which are better served by textual or structured representations, when the underlying facts are identical?**

这一问不直接做完整 RCA，而是先找出：

* 视觉到底在哪些操作上有优势；
* 文本在哪些操作上有优势；
* 是否存在值得路由的 modality complementarity。

---

## RQ1c — Budgeted adaptive access

> **Under the same evidence universe, model-call budget, tool-call budget, and diagnosis budget, does operation-aware visual–text routing improve evidence acquisition and downstream RCA over text-only access?**

这是下一阶段最重要的主实验。

它测试的不是：

> 把图片塞给模型有没有用？

而是：

> 在真实调查式流程中，允许 Agent 在适合视觉的操作上调用 visual view，在适合文本的操作上调用 text view，是否优于所有信息均文本化？

---

## RQ1d — Causal visual utilization

> **Do controlled semantic interventions on visual evidence causally alter the Agent’s evidence ledger and final diagnosis in the predicted direction, beyond changes caused by style-preserving visual shams?**

这一问证明：

* Agent 真的利用了视觉语义；
* 不是因为“输入里有一张图片”；
* 不是因为颜色、布局、token 数或随机扰动；
* 视觉变化通过 evidence selection 影响了最终诊断。

---

# 二、为什么我不建议直接运行 coding agent 提出的六条件实验

它提出的：

```text
H factual
T text-only
I image-only
H targeted
H placebo
H neutral
```

其中 counterfactual 部分有价值，但作为下一阶段的完整主实验仍有三个问题。

## 1. 它仍然以固定模态分配为核心

真实 on-call engineer 并不会选择：

* 全部只看图；
* 全部只看文本；
* 所有信息图文重复展示。

更接近现实的是：

* 先用视觉 overview 扫描；
* 对某个服务下钻；
* 用文本读日志语义；
* 用图查看时间传播；
* 用结构化字段核验精确值。

DashboardQA 也把 dashboard 的交互、筛选和导航视为实际 analytical workflow 的核心组成，而不是静态多图拼接；其结果同时显示，当前 VLM 的困难集中在 element grounding、交互规划和跨视图推理。([ACL Anthology][2])

## 2. `H = A + B` 会再次制造模态冗余

RQ0 已经说明，重复提供同一信息可能导致：

* context dilution；
* contradictory attention；
* 视觉噪声干扰文本判断；
* 模型错误地修改原本正确的答案。

因此，新实验的主方法不应是“图文全给”，而应是：

> **每个信息操作选择一种最适合的表示。**

GraphVista 的核心设计正是这样：简单属性推理交给文本，局部和结构复杂的图推理交给视觉，再由 planning agent 进行 modality routing。([ACL Anthology][3])

## 3. Counterfactual 只能证明“被使用”，不能证明“有帮助”

即使 targeted transplant 能稳定改变答案，也只说明：

> 图像对模型有因果影响。

RQ0 已经接近说明了这一点，因为图像确实改变了大量 top-1。

真正缺失的是：

> **怎样使这种因果影响更多地修复错误，而不是制造错误。**

因此 targeted/placebo/sham 应当保留，但放在主方法确定之后，作为 mechanism experiment。

---

# 三、我建议的 RQ1 整体实验结构

建议按三个层次执行：

```text
Experiment 1: RCA-VisOps
确定哪些 RCA 操作适合图像，哪些适合文本
                    ↓
Experiment 2: Matched-plan routed RCA
固定事实和调查计划，只改变信息表示与路由
                    ↓
Experiment 3: Adaptive tool-using RCA
Agent 自主选择查询内容和表示方式
                    ↓
Counterfactual visual interventions
证明视觉语义确实通过 evidence ledger 影响诊断
```

只有前一个层次成功，才进入下一个层次。

---

# 四、Experiment 1：建立 RCA-VisOps

当前 12-case atomic grounding 实验太小，而且主要检查“能不能读”，没有系统回答：

> 视觉在哪类 RCA operation 上优于文本？

建议从 `CanonicalEvidenceBundle` 自动生成一个 **RCA Visual Operations benchmark，RCA-VisOps**。

每一个任务都来自真实 incident，但答案可以由脚本精确验证，不依赖 LLM judge。

## Task family A：Exact lookup

例如：

* 某个时间桶的精确 latency 值是多少？
* 某条 edge 的 caller 和 callee 是谁？
* 某个 log template 的出现次数是多少？
* 某个 entity 的 coverage 是多少？

预期：

> 文本或结构化表示占优。

这是必要的负向控制，证明你们不是预设所有任务都应该视觉更好。

---

## Task family B：Temporal scanning

例如：

* 哪个实体最早发生变化？
* 哪个异常持续时间最长？
* 哪两个序列在相近时间开始异常？
* 哪个实体先出现 metric anomaly，随后出现 trace anomaly？
* 哪个序列存在 spike、持续抬升或恢复？

预期：

> visual time-series / heatmap 可能优于 64-bin JSON 序列。

---

## Task family C：Relational and topology reasoning

例如：

* `S07 → S12` 是否存在有向调用？
* 哪条边最先出现 latency increase？
* 从 symptom service 到 candidate root 的最短 observed path 是什么？
* 哪个实体同时位于两条异常传播路径上？
* 某个异常是 upstream 还是 downstream？

这里不要再使用单张完整大图。MuSe 的结果说明，大图整体渲染会产生 clutter、occlusion 和 distraction；它采用逐步选择并渲染任务相关子图。([ACL Anthology][4])

因此应该测试：

* text adjacency list；
* full graph；
* adjacency matrix；
* edge-time matrix；
* progressive local subgraph。

---

## Task family D：Cross-modal alignment

例如：

* 哪个 entity 在同一时间段同时出现 metric、log 和 trace anomaly？
* 哪个 entity 只有 metric anomaly，但 trace coverage 不足？
* 哪一组证据最支持“root 出现在 symptom 之前”？
* 哪个服务表现为下游症状，而非最早异常源？

这是 dashboard 最可能真正具有优势的地方，因为它涉及：

* 多实体；
* 多时间轴；
* 多模态；
* 空间对齐；
* 模式比较。

---

## Task family E：Missingness and uncertainty

例如：

* 这个空白区域是正常还是没有观测？
* 哪个 trace edge coverage 不足？
* 哪个实体不能根据当前 trace 下结论？
* 哪种 modality 对该 entity 不可用？

这对你们数据非常重要，因为某些 active case 虽然 trace 非空，但可能只有极少 span。

---

## RCA-VisOps 的输入条件

每个任务生成三个严格配对版本：

```text
Text view
Visual view
Visual + bounded exact sidecar
```

它们必须来自同一个：

```text
query_spec
fact_id set
time range
entity set
aggregation
missingness mask
```

示例：

```json
{
  "query_id": "Q-0017",
  "operation": "earliest_onset",
  "entities": ["S03", "S07", "S12"],
  "time_bins": [0, 63],
  "facts_sha256": "...",
  "text_artifact": "...",
  "visual_artifact": "...",
  "answer": "S07"
}
```

## 这个实验的关键输出

不是只报告总体 accuracy，而要得到一个：

> **Modality Advantage Map**

例如：

| Operation             | Text | Visual | Hybrid |
| --------------------- | ---: | -----: | -----: |
| Exact lookup          |   94 |     71 |     95 |
| Earliest onset        |   68 |     87 |     89 |
| Multi-hop path        |   72 |     84 |     86 |
| Log semantics         |   91 |     55 |     92 |
| Cross-modal alignment |   61 |     83 |     85 |

这样的结果即使不是所有视觉条件都赢，也足以建立一个强结论：

> **视觉和文本具有 operation-dependent complementarity。**

近期 GraphVista 也得出了类似的路由原则：文本适合简单属性推理，视觉适合局部、结构复杂的拓扑推理。([ACL Anthology][3])

## 第一个 Go/No-Go Gate

在做昂贵 Agent 实验前，先计算一个 oracle router：

```text
对每类 operation，选择 development 上表现更好的 modality
```

然后比较：

```text
Oracle-routed
vs
All-text
vs
All-visual
vs
Always-both
```

如果 oracle routing 都不能在新 operation tasks 上超过 all-text，那么：

> 当前 renderer、模型或任务根本不存在足够的视觉互补性，不应该继续做 Dashboard Builder RL。

这个 gate 会节省大量 GPU 预算。

---

# 五、Experiment 2：Matched-plan routed RCA

RCA-VisOps 证明存在 modality complementarity 后，再运行真正的 end-to-end RCA。

这里建议采用：

> **相同调查计划、相同事实切片、相同两阶段调用，只改变每个调查操作的表示方式。**

## 1. 隐藏的 Canonical Evidence Store

完整 CEB 不再直接放入 prompt，而是作为 stage-bound evidence store：

```text
Canonical Evidence Store
├── metric series
├── log templates/messages
├── trace edges/spans
├── observed topology
├── deployment mapping
├── coverage
└── fact provenance
```

每个 Agent 只能通过工具获得其中的部分内容。

这更接近真实调查，也避免 text-only 一开始就拿到经过完整整理的所有答案相关结构。

---

## 2. Paired view tools

每一个查询工具都必须有文本和视觉两个实现，而且基于完全相同的 query spec。

例如：

```text
inspect_metric_slice(
    entities,
    metrics,
    time_range
)
```

可以返回：

```text
text_metric_view(query_spec)
visual_metric_view(query_spec)
```

两者必须绑定相同：

```text
fact_ids
source rows
time bins
normalization
coverage
```

同样：

```text
text_trace_view(query_spec)
visual_trace_view(query_spec)

text_topology_view(query_spec)
visual_subgraph_view(query_spec)

text_log_view(query_spec)
visual_log_timeline_view(query_spec)
```

---

## 3. 主实验 arms

### Arm T：Text Agent

所有调查结果均使用文本或结构化序列化。

### Arm R：Routed Visual–Text Agent

事实切片与 Arm T 完全相同，但表示由 operation 类型决定：

| Operation              | Routed representation         |
| ---------------------- | ----------------------------- |
| 精确数值、日志语义              | Text                          |
| 多实体时间比较                | Visual                        |
| 传播顺序                   | Visual                        |
| 局部 topology            | Visual subgraph / edge matrix |
| 精确 edge 或 entity ID 核验 | Text                          |
| coverage overview      | Visual + exact count          |

### Arm B：Always-both Agent

每次同时收到图像和对应文本。

这是 secondary baseline，用于验证：

> routing 是否优于 redundant fusion。

### Arm V：Visual-dominant Agent

主要用于诊断，不作为决定视觉价值的主 baseline。Logs 和精确数值天然不适合纯图像，因此 image-only 失败不能推翻视觉的条件性价值。

---

## 4. 两阶段结构

### Stage 1 — Observe and Connect

输出统一的：

```json
{
  "selected_fact_ids": [],
  "observations": [
    {
      "claim": "...",
      "fact_ids": [],
      "source_representation": "visual|text",
      "confidence": 0.0
    }
  ],
  "temporal_relations": [],
  "directed_edges": [],
  "candidate_support": {},
  "candidate_opposition": {},
  "conflicts": [],
  "missing_evidence": []
}
```

### Stage 2 — Diagnose

只读取：

* `EvidenceLedgerV2`；
* candidate inventory；
* common task shell。

它不能再直接读取全部原始文本或 dashboard。

这样能够把总错误拆成：

```text
Evidence acquisition error
vs
Diagnostic reasoning error
```

VisDoT 的结果也支持把 visual perception 与后续 logic 分开训练和评估，而不是要求模型在一次生成中同时完成视觉读取和复杂推理。([ACL Anthology][5])

---

# 六、怎样保证真正的 equal-information

新的实验不应继续使用“所有事实同时塞进 prompt”的定义，而应使用更适合 Agent 的：

> **Equal evidence access**

需要满足六类 parity。

## 1. Evidence-universe parity

所有 arms 能够访问的 fact universe 完全相同。

## 2. Query parity

Matched-plan 实验中，每个 case 的查询：

* entity scope；
* time range；
* metric family；
* edge set；
* top-K；
* aggregation；

必须完全相同。

## 3. Provenance parity

每个 text/visual result 必须有相同的：

```text
fact_ids
source row hashes
query hash
```

## 4. Investigation-budget parity

所有 arms 具有相同：

* model calls；
* tool calls；
* maximum selected facts；
* EvidenceLedger entries；
* output token ceiling；
* stopping rule。

## 5. Training parity

如果 visual observer 做 operation SFT，text observer也必须使用：

* 相同 task instances；
* 相同训练步数；
* 相同 LoRA rank；
* 相同 optimization budget。

只是输入编码不同。

## 6. Cost reporting

视觉和文本不可能实现严格相同的底层 FLOPs，因此建议报告两个协议：

### Equal-action protocol

* 相同 model turns；
* 相同查询数；
* 相同 fact slices。

### Equal-cost protocol

进一步控制：

* actual input tokens/image tokens；
* wall time；
* peak memory；
* total prefill/decode time。

最后给出 accuracy–cost Pareto curve，而不是假装一张图片和若干文本 token 的计算完全等价。

---

# 七、不要再做小规模 root-label LoRA，先训练 Observer

目前两轮 LoRA 失败，并不能说明视觉训练没有希望；它们说明的是：

> 用 24 或 30 个 case 直接训练最终 root ranking，不足以教会模型如何可靠整合视觉证据。

下一步不应再增加几十个 root-labeled case，而应从训练数据中自动生成大量可验证的 operation examples。

## Observer SFT 数据

可以自动生成：

* region → entity；
* region → time range；
* earliest onset；
* longest persistence；
* directed edge；
* multi-hop path；
* cross-modal agreement；
* missing vs normal；
* exact evidence citation；
* modality selection。

这些任务不需要人工 reasoning trace，也不需要使用 root label。

训练目标是：

```text
Visual/text evidence
        ↓
EvidenceLedger facts
```

而不是：

```text
Dashboard
        ↓
直接生成 root answer
```

ChartAgent 的核心也不是简单增加图片，而是把复杂视觉问题分解成视觉子任务，并通过 crop、annotation、axis localization 等视觉工具执行。([ACL Anthology][6])

---

# 八、Experiment 3：Adaptive tool-using RCA

只有 Matched-plan routed RCA 通过后，才允许 Agent 自己决定查询什么。

## Text Agent

可调用：

```text
query_metric_text
query_log_text
query_trace_text
query_topology_text
```

## Adaptive Multimodal Agent

可调用：

```text
query_metric_text
render_metric_view

query_log_text
render_log_timeline

query_trace_text
render_edge_time_matrix

query_topology_text
render_local_subgraph
```

两个 Agent 共享：

* 同一个 evidence store；
* 同一个 tool-call budget；
* 同一个模型；
* 同一个 final solver；
* 同一个 verifier。

Primary contrast：

[
\Delta_{\text{adaptive}}
========================

\mathbb E[
MRR_{\text{Adaptive-VT}}
------------------------

MRR_{\text{Text-Agent}}
]
]

这个实验才真正对应后续的 Dashboard Builder：

> Builder 不只是生成一张布局，而是在预算内选择应该呈现什么、以什么模态呈现。

整张大 topology 不应作为默认输入；更合理的是根据当前候选逐步渲染局部相关子图。MuSe 和 GraphVista 都采用了类似的 task-relevant visual subgraph 思路。([ACL Anthology][4])

---

# 九、怎样做因果视觉利用实验

coding agent 提出的 targeted/placebo/neutral 思路应该保留，但应改成**工具结果级干预**，而不是重新生成整套六臂输入。

当 Adaptive Agent 调用某个 visual tool 时，对同一个调用生成四个配对结果：

## Factual

真实视觉结果。

## Targeted semantic intervention

只修改一个有明确预测后果的语义：

* 交换两个 entity 的 onset；
* 反转一条 edge；
* 把异常路径从 candidate A 移到 candidate B；
* 改变 metric 与 trace 的时间对齐；
* 将 coverage insufficient 改成 observed。

## Style-preserving sham

不改变语义，只改变：

* palette；
* panel spacing；
* alias placement；
* line thickness；
* renderer skin；
* 非关键信息位置。

## No-view control

该视觉结果不提供，但其他调查步骤相同。

---

## 需要测量三层因果结果

### 1. Perception shift

模型是否读取了被修改的视觉事实？

### 2. Ledger shift

修改是否改变了：

* selected fact IDs；
* temporal relations；
* directed edges；
* candidate support/opposition？

### 3. Diagnosis shift

最终 root rank 是否按 targeted manipulation 的预测方向变化？

定义：

[
C_{\text{semantic}}
===================

## P(\text{predicted shift}\mid\text{targeted})

P(\text{same shift}\mid\text{sham})
]

只有 targeted 明显高于 sham，才能说明模型利用的是视觉语义，而不是普通图像扰动。

RADAR 一类近期工作也强调，视觉回答的可信性需要把 reasoning step 与具体 chart attribution 对齐，而不能只看最终答案是否变化。([ACL Anthology][7])

---

# 十、必须预注册“视觉何时应该有效”

不要只看总体平均值，还应预先定义一个 label-safe 的 **Visual Structure Complexity**。

可以只使用：

* candidate entity count；
* metric series count；
* observed edge count；
* graph diameter；
* maximum path length；
* onset dispersion；
* cross-modal evidence density；
* missingness；
* trace coverage；
* dashboard panel density。

不得使用：

* root label 是否被模型答对；
* 当前 H−T 结果；
* fault type 的测试表现；
* heldout outcome。

可以检验：

[
MRR
===

\beta_0
+\beta_1 \text{VisualArm}
+\beta_2 \text{Complexity}
+\beta_3
(\text{VisualArm}\times\text{Complexity})
]

可能出现的合理结果是：

* 低复杂度 case：text 更好；
* 高结构复杂度 case：visual routing 更好；
* 全局平均收益较小；
* adaptive router 通过只在高价值 case 调视觉而取得净增益。

这比声称：

> 所有 incident 都应该看 dashboard

更符合工程实际，也更容易形成可信贡献。

---

# 十一、统计与 heldout 设计

## Primary outcome

建议使用 paired MRR，而不是只使用 AC@1：

[
\Delta_{\text{primary}}
=======================

## MRR_{\text{Routed}}

MRR_{\text{Text}}
]

因为 MRR 能区分：

* 正确 root 从第 20 升到第 2；
* 正确 root 从第 2 降到第 3；
* 完全不在候选列表中。

## Secondary outcomes

* AC@1/3/5；
* EvidenceLedger fact precision/recall；
* directed-edge accuracy；
* temporal-relation accuracy；
* path accuracy；
* unsupported evidence rate；
* calibration；
* tool calls；
* image/text tokens；
* wall time。

## Mechanism outcomes

* targeted-vs-sham ledger shift；
* visual evidence citation rate；
* correct visual repair rate；
* harmful visual override rate；
* evidence-mediated diagnosis improvement。

## Statistical unit

case-level paired comparison。

AIOps2022 的重叠窗口 case 不能被当成完全独立样本，置信区间和重采样仍应以现有 `leakage_group_id` 为 cluster。

---

# 十二、现有 720 cases 应该怎么处理

现有 RQ0 的 720 cases 以及已经运行过的旧两阶段 cases 都已经 exposed。

它们现在非常适合：

* 分析 image repair/break pattern；
* 构建 RCA-VisOps；
* 训练 operation observer；
* 设计 modality router；
* 选择工具；
* 确定 complexity strata；
* development gate；
* power analysis。

但它们不能再次作为 untouched confirmatory set。

当前 v2 协议将 `unused` 定义为 terminal embargo，不能静默拿来补新 heldout。需要使用这些 case 时，必须在任何新结果产生之前发布一个新的 split/protocol 版本，清楚记录：

* 原 v2 lineage；
* exposure ledger；
* 哪些 case 被重新分配；
* 新的 assignment hash；
* 哪些 checkpoint 接触过哪些 case。

否则不能声称重新获得了“未见过的测试集”。

---

# 十三、推荐的 Go/No-Go 路线

## Gate 1：Visual operation complementarity

RCA-VisOps 上：

* visual 在 temporal/relational/alignment tasks 上有稳定优势；
* text 在 exact lookup/log semantics 上保持优势；
* oracle routing 优于 best fixed modality。

失败则停止视觉 Builder 路线。

## Gate 2：Observer integration

在 exposed development cases 上：

* Routed Observer 的 ledger quality 高于 Text Observer；
* targeted visual edit 能引起正确方向的 ledger shift；
* sham 不产生类似变化。

失败则继续改 observer/tool，不进入完整 RCA。

## Gate 3：End-to-end development

Matched-plan Routed 的：

* MRR；
* evidence quality；
* harmful override rate；

优于 Text Agent，并且不是单个 case 驱动。

失败则不进入 adaptive Agent。

## Gate 4：Adaptive investigation

Adaptive VT Agent 在相同预算下优于：

* Text Agent；
* Always-both；
* Random routing；
* fixed heuristic routing。

通过后才有理由进入后续 RL、scorer 和 co-evolution。

## Gate 5：Fresh confirmatory evaluation

全部设计冻结后，再打开新的 Test-ID / Test-OOD。

---

# 十四、这会形成怎样的论文故事

目前最有说服力的故事不是：

> 我们终于找到一种 dashboard，能让所有 VLM 都比文本更准。

而是：

1. **Static visual redundancy fails.**
   在完整、lossless text 已经可用时，静态 dashboard 不增加性能。

2. **The failure is not pure visual blindness.**
   模型能读取大部分 primitive，图像也会改变答案，但整合方向不可靠。

3. **Visual utility is operation-dependent.**
   文本适合精确 lookup 和日志语义；视觉适合时间扫描、跨实体比较和局部拓扑。

4. **Selective routing removes harmful redundancy.**
   不再把所有内容图文重复，而是根据 investigation operation 选择表示。

5. **Visual tools improve evidence acquisition under bounded investigation.**
   提升首先发生在 ledger quality，然后传导到 RCA。

6. **Counterfactual interventions verify causal use.**
   targeted visual edits 改变对应 evidence 和 diagnosis，而 style sham 不会。

这与近期工作的方向也一致：DashboardQA 强调真实 dashboard 的价值来自交互；ChartAgent 通过视觉工具而不是静态输入提高 chart reasoning；GraphVista 进行 text/visual modality routing；MuSe 对复杂图进行渐进式子图可视化。([ACL Anthology][2])

近期一项 OpenRCA 预印本也报告，大量失败并不是证据不存在，而是证据已经存在但未被正确使用，即 reasoning gap 大于 data-access gap。这与你们“图像确实改变输出，但方向不可靠”的观察高度一致。([arXiv][8])

---

# 十五、我会给 coding agent 的具体执行指令

```text
1. 将现有 RQ0 正式改名为 RQ1a-static-full-information。
   保留负结果，不重新运行，不降低其地位。

2. 暂停新的 full-case H/T/I six-arm GPU 实验。

3. 建立 RCA-VisOps：
   - exact lookup
   - temporal scanning
   - topology/path
   - cross-modal alignment
   - missingness
   每个任务生成 paired text/visual artifacts 和自动真值。

4. 建立统一 QuerySpec 与 PairedView contract：
   同一 query 必须产生相同 fact_ids 和 provenance hash。

5. 在 exposed cases 上运行：
   - all-text
   - all-visual
   - bounded hybrid
   - oracle routing
   先确认是否存在 modality complementarity。

6. 使用自动生成的 VisOps 任务训练 Observer LoRA。
   不使用 root label，不训练最终 root ranking。

7. 实现 EvidenceLedgerV2。
   Stage 2 Diagnoser 对所有 arms 完全相同，只读取 ledger。

8. 实现 Matched-plan RCA：
   - Text Agent
   - Operation-routed Agent
   - Always-both Agent
   - Visual-dominant diagnostic arm

9. 只在 Routed Agent 通过 development gate 后，
   实现 adaptive query-and-modality tool loop。

10. 将 targeted/placebo/sham 改成 visual-tool-result intervention，
    测量 perception → ledger → diagnosis 三层影响。

11. 完成 exposure ledger，并在任何 fresh evaluation 前冻结新的 split protocol。

12. 只有 RQ1 fresh heldout 为正，才启动 RQ2 dashboard design、
    VLM scorer、RL credit assignment 和 co-evolution。
```

最核心的转变是：

> **不要再研究“把一张 dashboard 附加到完整文本后有没有帮助”，而要研究“视觉是否能作为一个被选择、被查询、被验证的信息访问操作，改善 Agent 的调查过程”。**

RQ0 的负结果并没有摧毁项目；它帮助你们排除了最弱、最容易被审稿人质疑的 static-fusion 方案，并把真正值得研究的方法收敛到了：

> **operation-aware modality routing + evidence-grounded two-stage RCA + tool-mediated visual investigation。**

[1]: https://aclanthology.org/2025.findings-acl.1256/ "Can VLMs Actually See and Read? A Survey on Modality Collapse in Vision-Language Models - ACL Anthology"
[2]: https://aclanthology.org/2026.findings-eacl.177/ "DashboardQA: Benchmarking Multimodal Agents for Question Answering on Interactive Dashboards - ACL Anthology"
[3]: https://aclanthology.org/2026.findings-acl.2066/ "See or Say Graphs: Agent-Driven Scalable Graph Understanding with Vision-Language Models - ACL Anthology"
[4]: https://aclanthology.org/2026.acl-long.476/?utm_source=chatgpt.com "MuSe: Multi-Stage Graph Reasoning via Vision-Language Models - ACL Anthology"
[5]: https://aclanthology.org/2026.findings-eacl.30/?utm_source=chatgpt.com "VisDoT : Enhancing Visual Reasoning through Human-Like Interpretation Grounding and Decomposition of Thought - ACL Anthology"
[6]: https://aclanthology.org/2026.acl-long.843/?utm_source=chatgpt.com "ChartAgent: A Multimodal Agent for Visually Grounded Reasoning in Complex Chart Question Answering - ACL Anthology"
[7]: https://aclanthology.org/2026.findings-eacl.299/?utm_source=chatgpt.com "RADAR: A Reasoning-Guided Attribution Framework for Explainable Visual Data Analysis - ACL Anthology"
[8]: https://arxiv.org/abs/2607.13548?utm_source=chatgpt.com "How Far Can Root Cause Analysis Go on Real-World Telemetry Data?"

# Question: 还有一件事，是不是log，metric和trace的视觉表示也都可能产生不同的影响？比如log的视觉表示反而会添加噪声，而metrics的视觉表示可能会更有效（只是举个例子，实际上各modality数据的视觉表示的影响目前未知）。这个方面需要添加实验吗？比如添加到RQ1b之中？

## Answer:

是的，**这个实验应该加入，而且它不是可有可无的细节，而是 RQ1 的核心组成部分。**

你现在已有的 RQ0 只说明：

> 将完整 dashboard 图像整体附加到 lossless text 后，视觉没有产生稳定增益。

但这个总体负结果可能掩盖了不同 modality 之间的异质性：

* metrics 的时间趋势、异常起点和持续性可能适合视觉表达；
* traces 的调用关系和传播路径可能适合矩阵或局部拓扑图；
* logs 的核心价值往往是具体语义，强行视觉化可能压缩语义、增加密度和噪声；
* coverage、部署关系等辅助信息也可能只有在特定场景有价值。

因此，不能把“dashboard 图像”当成一个不可分割的统一 treatment。否则即使 metrics visualization 有正贡献，也可能被 logs visualization 的负贡献抵消。

# 建议重新组织 RQ1

## RQ1a — Static redundant augmentation

> **Under full-information one-shot conditions, does adding a static dashboard to a lossless textual representation improve RCA?**

这个已经被 RQ0 回答：

> 在当前模型和数据上，不提高。

---

## RQ1b — Modality-specific visual utility

建议正式改成：

> **RQ1b. Under matched evidence access and computation budgets, how do visual representations of metrics, logs, and traces/topology individually and jointly affect evidence acquisition and downstream RCA?**

中文含义：

> 在可访问证据和计算预算一致的条件下，metrics、logs、traces/topology 的视觉表示分别及联合地如何影响证据获取和最终 RCA？

这一问需要回答：

1. 哪种 modality 的视觉化有正贡献；
2. 哪种 modality 的视觉化无效或有害；
3. 不同 modality 的视觉化是否存在协同或冲突；
4. 影响首先发生在视觉读取、证据选择，还是最终诊断阶段。

---

## RQ1c — Operation- and context-dependent routing

> **RQ1c. Can an operation- and context-aware modality-routing policy exploit this heterogeneous utility to outperform any fixed visual/text allocation?**

中文含义：

> 如果不同 modality 和不同 RCA 操作适合不同表示，动态路由是否优于固定的 all-text、all-visual 或 always-both？

这样逻辑就很完整：

```text
RQ1a
整张 dashboard 冗余加入是否有效？
结果：目前无效
        ↓
RQ1b
是否因为不同 modality 的视觉作用相互抵消？
        ↓
RQ1c
能否根据 modality、operation 和 case 条件选择最适合的表示？
        ↓
RQ1d
视觉语义是否真正因果性影响 evidence ledger 和诊断？
```

---

# 一、RQ1b 应该怎样设计实验

最干净的设计是一个 **2×2×2 factorial experiment**。

三个二元因素：

* (M)：metrics 使用文本表示还是视觉表示；
* (L)：logs 使用文本表示还是视觉表示；
* (R)：traces/topology 使用文本表示还是视觉表示。

得到八个条件：

| Arm | Metrics | Logs   | Traces/topology |
| --- | ------- | ------ | --------------- |
| TTT | Text    | Text   | Text            |
| VTT | Visual  | Text   | Text            |
| TVT | Text    | Visual | Text            |
| TTV | Text    | Text   | Visual          |
| VVT | Visual  | Visual | Text            |
| VTV | Visual  | Text   | Visual          |
| TVV | Text    | Visual | Visual          |
| VVV | Visual  | Visual | Visual          |

其中：

* `TTT` 是全文本基线；
* `VTT` 隔离 metrics visual effect；
* `TVT` 隔离 logs visual effect；
* `TTV` 隔离 traces/topology visual effect；
* `VTV` 对应你猜测的 practical layout：metrics 和 traces 可视化，logs 保持文本；
* 其余组合用于估计 interaction。

如果算力有限，可以：

1. 在 exposed development cases 上运行完整八臂；
2. 根据预注册规则选择少数关键 contrasts；
3. 在 fresh heldout 上只确认主要结论。

不能根据哪组结果最好再临时决定 confirmatory arms。

---

# 二、视觉和文本条件到底怎样保持公平

这里不要再强制要求：

> 每个 condition 的最终 prompt 同时包含一模一样的全部 token-level facts。

这会重新回到 RQ0 的 redundant augmentation。

更合理的是使用两个层次的公平性。

## 1. Atomic representation experiment：相同事实，不同编码

针对单个 RCA operation，text 和 visual 都由同一个 `QuerySpec` 生成：

```json
{
  "entities": ["S03", "S07", "S12"],
  "time_bins": [0, 63],
  "metric": "latency_p95",
  "fact_ids": ["M001", "M002", "..."]
}
```

然后分别生成：

* 文本序列表；
* 时间序列图或热力图。

两者具有：

* 相同实体；
* 相同时间桶；
* 相同数据值；
* 相同 missingness；
* 相同排序；
* 相同 provenance。

这是纯粹的 encoding comparison。

---

## 2. End-to-end RCA：相同 evidence access，不同 presentation

在 Agent 实验中，更合理的公平性是：

* 相同 evidence universe；
* 相同查询计划；
* 相同 tool-call 数；
* 相同 entity/time 范围；
* 相同 fact IDs；
* 相同 final evidence budget；
* 只是查询结果的表示方式不同。

例如，metrics tool：

```text
inspect_metrics(query_spec)
```

可以返回：

* text condition：64-bin numeric table；
* visual condition：sparkline/heatmap。

如果 visual Agent 需要某个精确值，它可以使用共同的：

```text
lookup_exact_fact(fact_id)
```

这模拟真实工程师的操作：

> 图像负责扫描模式，文本或结构化查询负责读取精确值。

而不是要求图像既承担模式比较，又把所有数字缩成小字塞进去。

---

# 三、每种 modality 应该测试什么

## 1. Metrics

### 视觉可能擅长

* earliest onset；
* spike、trend、persistence；
* 多序列同步；
* recovery；
* cross-service comparison；
* metric 与 trace onset 对齐。

### 文本可能擅长

* 精确数值；
* metric 名称；
* threshold comparison；
* 小规模 lookup。

### 推荐视觉表示

* entity-time heatmap；
* aligned sparklines；
* overview + selected detail；
* missingness mask。

不建议把数百条折线重叠在一张图中。

---

## 2. Logs

### 视觉可能擅长

* log burst；
* template frequency shift；
* first occurrence；
* severity timeline；
* 多服务日志事件同步。

### 文本可能擅长

* exception message；
* error code；
* timeout target；
* stack trace；
* domain-specific semantic clues。

因此 logs 的“visual condition”不应该是原始日志截图，而应是：

> **event timeline/heatmap + 受限的代表性日志文本。**

更准确地说，logs 适合的是**混合表示**，而不是纯视觉。

可以设置三个 levels，而不是简单二元：

* `L0`: text template/message table；
* `L1`: visual event summary only；
* `L2`: visual event summary + representative text。

如果八臂实验需要保持规模可控，可以把 `L2` 定义为正式的 `Visual` treatment，`L1` 只作为诊断性 ablation。

---

## 3. Traces/topology

### 视觉可能擅长

* caller–callee structure；
* multi-hop path；
* propagation direction；
* anomalous edge comparison；
* fan-in/fan-out；
* local dependency context。

### 文本可能擅长

* 精确 span ID；
* operation name；
* exact latency；
* exact status；
* 单条 edge lookup。

### 推荐视觉表示

* edge-time matrix；
* adjacency matrix；
* progressive local subgraph；
* small exemplar waterfall。

不建议继续使用密集的完整 force-directed graph。

Topology 最好和 traces 作为一个 **relational bundle** 处理，而不是完全独立的第四 modality。因为 topology 很多时候来自 traces；单独把它当成新信息源会引起“是否添加额外信息”的争议。

---

# 四、如何量化每种 modality 的作用

完整 factorial design 可以直接估计 main effect。

设最终 utility 为 (U)。

## Metrics visual main effect

[
\Delta_M
========

## \mathbb E[U\mid M=V]

\mathbb E[U\mid M=T]
]

即平均比较：

```text
VTT, VVT, VTV, VVV
vs
TTT, TVT, TTV, TVV
```

## Logs visual main effect

[
\Delta_L
========

## \mathbb E[U\mid L=V]

\mathbb E[U\mid L=T]
]

## Trace visual main effect

[
\Delta_R
========

## \mathbb E[U\mid R=V]

\mathbb E[U\mid R=T]
]

还需要估计 interaction。

例如 metrics 与 traces 的协同作用：

[
I_{M,R}
=

U(VTV)-U(VTT)-U(TTV)+U(TTT)
]

如果 (I_{M,R}>0)，说明 metrics 和 trace visualizations 联合使用产生了超出各自独立作用的收益。

同样可以检查：

* metrics × logs；
* logs × traces；
* 三模态 interaction。

---

# 五、建议使用的统计模型

由于同一个 case 会在多个 arm 中重复运行，可以使用 repeated-measures mixed-effects model：

[
Y =
\beta_0
+\beta_M M
+\beta_L L
+\beta_R R
+\beta_{ML}ML
+\beta_{MR}MR
+\beta_{LR}LR
+\beta_{MLR}MLR
+\gamma_{\text{model}}
+\gamma_{\text{dataset}}
+u_{\text{case}}
+\epsilon
]

其中：

* (Y) 可以是 reciprocal rank、ledger quality 或 evidence score；
* (u_{\text{case}}) 是 case-level random intercept；
* 也可以加入 complexity interaction：

[
M\times\text{temporal complexity}
]

[
L\times\text{log semantic density}
]

[
R\times\text{graph complexity}
]

AIOps2022 的置信区间和 bootstrap 仍需要按 leakage group 聚类，而不能把重叠窗口 case 视为完全独立。

---

# 六、不要只看最终 MRR

不同 modality 的作用可能发生在不同阶段，所以建议同时测量三层结果。

## 1. Perception / operation layer

* onset accuracy；
* directed-edge accuracy；
* log-template identification；
* path accuracy；
* missingness accuracy。

## 2. EvidenceLedger layer

* fact precision/recall；
* supporting/opposing evidence accuracy；
* temporal-relation accuracy；
* directed-edge accuracy；
* unsupported claim rate；
* modality citation rate。

## 3. Final diagnosis layer

* MRR；
* AC@1/3/5；
* confidence calibration；
* evidence-grounded accuracy。

可能出现：

```text
Metrics visual
→ onset detection 更好
→ ledger 更好
→ 但 final RCA 没提高
```

这说明 bottleneck 在 Solver reasoning，而不是 renderer。

也可能出现：

```text
Logs visual
→ burst detection 更好
→ 原始语义丢失
→ final RCA 变差
```

这说明 logs 应使用 hybrid 或 text-first representation。

---

# 七、建议加入“修复率—破坏率”指标

你们 RQ0 已经发现：

* 图像能修复一部分文本错误；
* 但也破坏更多文本正确案例。

这个指标应按 modality 拆开。

对于 modality (m)：

## Repair rate

[
Repair_m =
P(
\text{visual correct}
\mid
\text{text incorrect}
)
]

## Break rate

[
Break_m =
P(
\text{visual incorrect}
\mid
\text{text correct}
)
]

## Net correction

[
Net_m = Repair_m-Break_m
]

例如可能得到：

| Modality       | Repair | Break |  Net |
| -------------- | -----: | ----: | ---: |
| Metrics visual |    18% |    8% | +10% |
| Logs visual    |     5% |   17% | −12% |
| Trace visual   |    14% |   11% |  +3% |

这种结果能够非常直接地解释：

> 为什么 all-visual dashboard 总体没有增益，但 modality-aware routing 仍然有研究价值。

---

# 八、还要加入 modality-specific causal interventions

不能只看相关性和平均 performance。

## Metrics intervention

* 交换两个实体的 anomaly onset；
* 移动 spike 时间；
* 改变 persistence；
* 保持视觉风格不变。

检查：

* Agent 读取的 earliest entity 是否变化；
* ledger 中 temporal relation 是否变化；
* root rank 是否按预测方向变化。

## Logs intervention

* 将某个 error-template burst 移到另一个 entity；
* 替换代表性日志文本；
* 只改变颜色或 panel 顺序作为 sham。

## Trace intervention

* 反转某条 edge；
* 将异常 latency 从一条 edge 移到另一条；
* 修改局部 path；
* 保持 node 数和布局密度不变。

这样可以计算每种 modality 的：

[
C_m^{semantic}
==============

## P(\text{predicted shift}\mid targeted_m)

P(\text{shift}\mid sham_m)
]

这比笼统的“图像会改变输出”更有解释力。

---

# 九、这一实验如何连接后续 dashboard design 和 scorer

RQ1b 的结果会直接决定后面的设计空间。

例如，如果结果是：

```text
metrics visual: positive
logs visual: negative
trace matrix: positive in complex graphs
full graph: negative
coverage visual: positive for sparse traces
```

那么 RQ2 的 dashboard grammar 不应该继续平等搜索所有组合，而应该：

* 保留 metrics visual encodings；
* logs 以 text 或 hybrid 为主；
* trace 根据 graph complexity 选择 text/matrix/subgraph；
* coverage 在稀疏 case 中强制显示。

Scorer 也不能只输出一个总 dashboard score，而应预测：

```text
metric-visual contribution
log-visual contribution
trace-visual contribution
cross-modal interaction
context-dependent applicability
```

因此 RQ1b 是后续 component contribution、VLM scorer 和 RL router 的必要前置实验。

---

# 十、最终推荐的 RQ1 结构

## RQ1a — Static augmentation

> Does redundant static visual augmentation improve full-information one-shot RCA?

已有结论：没有稳定增益。

## RQ1b — Modality-specific and interaction effects

> **How do visual representations of metrics, logs, and traces/topology individually and jointly affect evidence acquisition and downstream RCA under matched evidence access and computation budgets?**

核心实验：2×2×2 factorial + modality-specific VisOps。

## RQ1c — Adaptive modality routing

> **Can an operation- and context-aware routing policy exploit modality-specific visual utility to outperform all-text, all-visual, always-both, and fixed hybrid representations?**

## RQ1d — Causal visual utilization

> **Do modality-specific semantic interventions causally alter the Agent’s evidence ledger and final diagnosis in the predicted direction beyond style-preserving shams?**

---

# 最终判断

**必须加入。**

而且它能把当前 RQ0 的总体负结果转化成一个更深入、更可信的研究问题：

> 视觉并不是统一地“有用”或“没用”；它的价值取决于 telemetry modality、RCA operation、case complexity，以及它是否替代了更合适的文本表示。

因此你们下一步不应继续寻找一张“所有内容都可视化”的 dashboard，而应首先找出：

> **哪些信息应该视觉化，哪些应该文本化，以及它们在什么条件下应该被路由给模型。**

这会为后续 Dashboard Builder Agent 提供真正可学习、可验证的动作空间。
