# 2026-07-29 RQ0 等信息、等计算实验计划

## 1. 现状判断与研究目标

### 当前实验能说明什么

现有实验不足以回答 RQ0，只能作为模型筛选、方差估计和功效分析的 pilot：

- 2026-07-27 的 AegisLab n=100 实验中，Qwen3.6-27B 的 hybrid/text/image-only MRR 分别为 0.499/0.482/0.429；四个可用开放模型的 `hybrid-text` 平均仅 +0.026，均未通过多重比较。
- 这些结果使用 renderer v4。随后确认 v4 在 AegisLab 上因稀疏 NaN 序列导致大量曲线实际为空；v5 修复后尚未进行正式 VLM 重跑。
- 当前图像标题直接显示完整 `case_id`。AegisLab 的 ID 包含服务和故障类型，例如 `mysql-partition`，构成仅视觉臂可见的非对称标签泄漏；已有 Qwen 轨迹明确利用过该信息。
- 图像标题和文本证据还包含绝对时间戳，违反当前项目的泄漏规则。
- 旧图像包含完整曲线形状，但 text-only 只序列化 baseline/peak，三种表示并非等信息。
- 旧实验实际输入 token 差异明显：Qwen 的 image-only、text-only、hybrid 约为 5,074、8,330、11,294 tokens。
- 实验只覆盖反复用于开发的 AegisLab 100 例，缺少全新留出集、AIOPS 跨数据集验证和跨架构复现。

因此，所有现有 modality 数字均不得作为 RQ0 的确认性证据。

### RQ0 与假设

> RQ0. Under equal-information and equal-compute conditions, does visual–text, topology-aware observability improve VLM-based RCA over text-only and flat structured representations?

确认性比较：

- H1a：Visual–Text Topology-aware 的 MRR 高于 Text-only。
- H1b：Visual–Text Topology-aware 的 MRR 高于 Flat Structured。
- Text-only 与 Flat Structured 的比较只用于解释表示形式效应，不属于 RQ0 的主要假设。
- 视觉和拓扑作为一个整体处理；不设置正式的 image-only、topology-off 或 visual-without-topology 主实验臂。

## 2. 实验契约

### 2.1 Canonical Evidence Bundle

为每个 incident 生成唯一、版本化、标签盲的 `CanonicalEvidenceBundle v1`，三臂只能从这个对象生成输入。其模型可见字段固定为：

- 随机生成的 opaque incident ID，不显示原始 `case_id`、数据集名、文件路径、故障类型或 ground truth。
- 完整候选服务列表，三臂顺序完全一致。
- 12 条通过冻结的标签盲规则选出的 metric series。
- 每条 series 使用同一组 64 个相对时间 bin，记录数值、缺失 mask、样本数、baseline、peak、signed-z、onset 和 persistence。
- 最多 8 条 log 变化记录及最多 8 条 trace latency/error 记录。
- 14 个标签盲选出的 propagation services，以及它们之间的有向调用边、相对 onset、severity 和 evidence source。
- 由遥测推断的相对 fault window。模型可见时间统一以窗口起点 `t=0` 表示，绝不出现 epoch 或注入时间。
- `schema_version`、CEB hash、atomic fact inventory hash 和各字段来源审计信息。

所有缺失 traces、稀疏 metrics 和孤立拓扑节点必须显式表示为 `null/missing`，不得按臂采用不同 fallback。任何基于 ground truth 的 panel、service、edge 或时间选择都禁止进入 CEB。

### 2.2 三个正式实验臂

| 臂 | 模型输入 | 约束 |
|---|---|---|
| A — Visual–Text Topology-aware | 一张基于 renderer v5 修复生成的 `v6-rq0/prop12` dashboard，加上与 B 字节级一致的 evidence text | 图像同时包含时间序列和 propagation topology；image 放在用户消息前部，随后是文本摘要 |
| B — Text-only | A 中完全相同的 deterministic evidence text | 逐条写出同一 64-bin 序列、日志、trace、onset 和所有有向边，不能只给 baseline/peak |
| C — Flat Structured | 同一 CEB 的排序稳定 JSONL fact records | 保留相同节点和边事实，但不使用图布局、视觉邻近关系或自然语言叙事 |

关键公平性定义：

- A 中图像与文本是同一 atomic facts 的重复编码，不得引入 B/C 没有的事实。
- 三臂的 task statement、RCA reasoning instruction、候选列表、输出 schema 和错误处理完全一致。
- 图例中的“边方向、颜色、排名和 onset 含义”也必须出现在共同说明中，避免 A 独占推理提示。
- 为每个输入生成 `fact_id → image primitive/text span/JSON pointer` 映射；忽略重复后，三臂 fact inventory 必须完全相等。

### 2.3 Equal-compute 操作性定义

采用“统一调用级推理额度”：

- 同一 checkpoint、tokenizer、vLLM 版本、GPU 类型和单次 one-shot 调用。
- 相同 `max_model_len=32768`、`max_tokens=16384`、temperature 0、top_p 1、seed 42、输出格式及 retry policy。
- Qwen thinking 关闭，prefix caching 和 chunked prefill 关闭，CUDA graphs 开启。
- BF16、无量化；`gpu_memory_utilization=0.65` 为默认运行上限，但它只是运维参数，其历史差异不影响结果有效性或可比性。
- 不使用无意义 padding 凑齐实际 token，因为 padding 会引入额外注意力负担。
- 每例记录 text tokens、image tokens、总 input/output tokens、wall time、GPU active time、峰值显存和终止原因。

该定义保证各臂拥有相同推理机会，但不声称实际 FLOPs 完全相等；实际计算消耗同时作为效率结果报告。

### 2.4 模型与数据

模型：

- 主要确认实验：Qwen3.6-27B，项目内无量化 BF16 checkpoint。
- 跨架构复现：Gemma-4-26B-A4B-it，同样使用无量化 BF16、确定性 vLLM 配方和完整三臂协议。
- 两个模型都必须运行，无论 Qwen 的中间结果是否正向；禁止条件式决定是否复现。
- 本 RQ0 仅做 frozen-model inference，不涉及 SFT、LoRA、GRPO 或其他训练。

数据：

- 正式数据只包括 AegisLab、AIOPS-2022、AIOPS-2025，每个数据集 240 个此前从未进入 results、render cache、gallery、smoke 或人工分析的 case，共 720 个 incident。
- 现有 480-case manifest 及所有历史暴露 case 全部归入 development，不得进入确认集。
- 先建立 exposure ledger；随后以 seed 42，按数据集内 `fault_type × root-cause granularity` 比例分层抽样，余数采用 largest-remainder 分配，层内按 `SHA256(seed:case_id)` 排序。
- AIOPS-2022 和 AIOPS-2025 各先保留一个 validation smoke case；AIOPS-2025 剩余未使用 case 作为预注册 reserve，不得根据模型结果替换。
- RE2-OB 只参与基础设施 smoke；RE2-OB/TT 已饱和，不进入 RQ0 headline。
- 240 × 3 arms = 每模型 2,160 次正式调用；两个模型合计 4,320 次。

## 3. 执行顺序和质量门槛

### 阶段 0：消除阻断项

在任何正式推理前必须完成：

- renderer 版本升至 v6，删除模型可见的原始 case ID、数据集名和绝对时间。
- 确认 prompt、PNG、OCR 可见文本、manifest 和 CEB 均不包含 ground truth、fault type、原始 ID、绝对时间或标签型 metadata。
- 冻结 upstream commit；当前缺失的 upstream pin 必须补齐。
- 建立 development、validation、formal、reserve/unused 分区 roster 和 exposure ledger。
- 冻结 CEB schema、三臂 serializer、共同 prompt、模型 checkpoint/tokenizer、renderer hash、依赖版本和 vLLM 配置。

### 阶段 1：静态和感知资格检查

- 对全部正式 CEB 执行三臂 fact-inventory 等价检查，任何不一致均阻止实验。
- 从三个主要数据集各选 4 个 development case，人工检查共 12 张图：稀疏曲线、长服务名、缺 traces、孤立节点、传播顺序、颜色和文字可读性。
- 覆盖 AIOPS-2025 弱拓扑、AegisLab 密集拓扑、无 trace、缺 log、全 NaN/稀疏 metric 和多 accepted-label case。
- 验证相同 CEB、配置和 renderer 重复生成完全相同的 PNG、文本、JSONL 和 hash。
- 用 development case 做非确认性的 whole-image swap 与图文顺序敏感性检查；结果只解释模型是否利用视觉，不用于更改正式输入。

### 阶段 2：运行资格检查

- 严格按 `Codex.md` 运行 partition-aware 三例 smoke：一个 validation RE2-OB、一个 AIOPS-2022、一个 AIOPS-2025。
- smoke 使用正式 compiler、renderer、client、writer、evaluator 和完整 32k/16k 配置；正确率不得作为通过条件。
- 每个模型用至少 20 个 development case 做同进程和跨进程 determinism gate，要求预测、MRR 和 serialized input 完全一致。
- 固定六种臂顺序 `ABC/ACB/BAC/BCA/CAB/CBA`，按 opaque incident hash 均衡分配，避免固定调用顺序产生系统偏差。

### 阶段 3：确认实验

- 先完整运行 Qwen 720×3，再在不修改任何 CEB、prompt、renderer 或分析规则的情况下完整运行 Gemma 720×3。
- 不读取部分结果做配置选择、停止决策或 case 替换。
- 基础设施失败使用预注册且跨臂一致的 retry policy；仍失败的 case 从相关配对的两臂共同排除，不记为模型错误。
- JSON parse failure 和模型主动输出截断属于模型结果，计入正式指标并单独报告。
- 任一臂 parse rate 低于 0.95，或无法配对的基础设施 case 超过 1%，该模型的 RQ0 结论记为不完整，不得用 complete-case 子集宣称成功。

## 4. 分析、判定和验收

### 指标和统计

- 主要指标：MRR。
- 次要指标：AC@1/3/5、AVG@3/5、parse/truncation/error rate、输入/输出 token、wall time、GPU active time。
- Recall@K 仅在另行注册的真正 multi-root 评估中使用；accepted aliases 不作为独立 multi-root 证据。
- 每个比较以相同 case 配对，报告 ΔMRR、paired Wilcoxon signed-rank p 和 paired Cohen’s d，不报告 confidence interval。
- Qwen 的两个主要比较采用 Holm 校正，family-wise α=0.05。
- 720 例平衡设计下，基于历史 paired SD 约 0.38–0.46，预计可分辨约 0.045–0.055 MRR；预注册最小实际重要效应为 +0.05。
- 同时报告三个数据集各自结果，不用 pooled score 掩盖异质性。
- 预注册 effect modifiers：topology edge coverage、root-evidence coverage、trace presence、candidate count、fault type、root-cause level、视觉密度和缺失率。
- 补充报告 A/B/C 的 top-1 agreement、排名重合和 correctness discordance，判断图像是否真正改变了推理。

### RQ0 判定

对单个模型，只有同时满足以下条件才判定 RQ0 supported：

1. A−B 和 A−C 的宏平均 ΔMRR 都不小于 +0.05。
2. 两个比较的 Holm-adjusted p 均小于 0.05。
3. 任一主要数据集都不存在不大于 −0.05 的实质性反向效应。
4. 资格检查、parse、truncation、配对完整性和泄漏检查全部通过。

结论分级：

- Qwen 和 Gemma 都满足：支持可跨这两个 VLM 架构推广的 RQ0 结论。
- 仅 Qwen 满足：只支持 Qwen3.6-27B-specific 结论，不能写成通用 VLM 优势。
- 只胜过 B 或只胜过 C：表示视觉对某种基线有效，但完整 RQ0 不成立。
- 正向但小于 +0.05、或未达到当前 MDE：inconclusive，不能写成“无效”。
- 显著负向：对应模型/基线上的反证。
- A 准确率没有提高但 token/GPU 时间 Pareto 更优：单独形成 efficiency 结论，不得替代 RQ0 的 accuracy 结论。

### 未来实现接口

本次只写计划，不写脚本；后续实现需冻结：

- `CanonicalEvidenceBundleV1` schema。
- `InputArm = visual_text_topology | text_only | flat_structured`。
- 每例结果增加 `opaque_incident_id`、`ceb_hash`、`fact_inventory_hash`、`arm`、`renderer_version`、完整 token/GPU accounting 和 leakage-audit 状态。
- 聚合结果必须包含 per-dataset、per-fault、effect-modifier、paired comparison 和完整 artifact inventory。

## 5. References

协议主要受以下研究约束：

- [OpenRCA: Can Large Language Models Locate the Root Cause of Software Failures? — ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/d29b8d53678015079e1d245c023e49d2-Abstract-Conference.html)：说明真实遥测 RCA 仍有明显推理瓶颈。
- [FAMOS: Fault Diagnosis for Microservice Systems through Effective Multi-modal Data Fusion — ICSE 2025](https://conf.researchr.org/details/icse-2025/icse-2025-research-track/79/FAMOS-Fault-diagnosis-for-Microservice-Systems-through-Effective-Multi-modal-Data-Fu)：支持跨 logs、metrics、traces 的关系建模，但不能直接证明视觉表示有效。
- [Too Many Cooks: Assessing the Need for Multi-Source Data in Microservice Failure Diagnosis — ISSRE 2025](https://doi.org/10.1109/ISSRE66568.2025.00014)：更多模态或数据源并不必然提升诊断，要求实验保持可证伪并报告负效应。
- [SEAM: Semantically Equivalent Across Modalities — COLM 2025](https://openreview.net/forum?id=lI4LgGv4sX)：直接支持 atomic-fact 等价、跨模态 agreement 和表示隔离设计。
- [Words or Vision: Do Vision-Language Models Have Blind Faith in Text? — CVPR 2025](https://openaccess.thecvf.com/content/CVPR2025/html/Deng_Words_or_Vision_Do_Vision-Language_Models_Have_Blind_Faith_in_CVPR_2025_paper.html)：要求审计 text bias、模态冲突和 token order。
- [ChartMuseum — NeurIPS 2025 Datasets and Benchmarks](https://papers.nips.cc/paper_files/paper/2025/hash/ca20efa9cf3703186d91424cf4876f8b-Abstract-Datasets_and_Benchmarks_Track.html)：显示当前 VLM 的视觉图表推理远未饱和，支持单独的 perception qualification。
- [VLM2-Bench — ACL 2025](https://aclanthology.org/2025.acl-long.372/)：支持验证 VLM 是否能在视觉中连接对应线索，而非只依赖语言先验。
- [Time-VLM — ICML 2025](https://proceedings.mlr.press/v267/zhong25a.html)：说明文本语义和视觉时间模式可能互补，但仍需等信息对照验证。
- [Text or Pixels? — Findings of EMNLP 2025](https://aclanthology.org/2025.findings-emnlp.558/)：支持把 token efficiency 作为独立于准确率的第二结果轴。
- [Mitigating Vision-Text Order Bias in Vision-Language Model — CVPR Findings 2026](https://openaccess.thecvf.com/content/CVPR2026F/html/Gan_Mitigating_Vision-Text_Order_Bias_in_Vision-Language_Model_CVPRF_2026_paper.html)：支持冻结图文顺序并进行顺序敏感性检查。
- [MoCE: A Mixture-of-Context Aware Experts Framework — NSDI 2026](https://www.usenix.org/conference/nsdi26/presentation/harsh)：说明不同 incident context 的诊断异质性很强，支持预注册 effect modifiers。
- [How Far Can Root Cause Analysis Go on Real-World Telemetry Data? — 2026 arXiv preprint](https://arxiv.org/abs/2607.13548)：最新但尚未同行评审；其 evidence-present/reasoning-gap 区分支持本计划的 evidence-coverage 分析。
- [Giving Every Modality a Voice in Microservice Failure Diagnosis — ASE 2024](https://conf.researchr.org/details/ase-2024/ase-2024-research/89/Giving-Every-Modality-a-Voice-in-Microservice-Failure-Diagnosis-via-Multimodal-Adapti)：提示强势模态可能压制其他模态，支持跨模型和跨故障类型分析。
- [MULAN: Multi-modal Causal Structure Learning and Root Cause Analysis — WWW 2024](https://arxiv.org/abs/2402.02357)：为多源证据与拓扑/因果关系的联合使用提供基础。
- [Eadro: An End-to-End Troubleshooting Framework for Microservices on Multi-source Data — ICSE 2023](https://conf.researchr.org/details/icse-2023/icse-2023-technical-track/114/Eadro-An-End-to-End-Troubleshooting-Framework-for-Microservices-on-Multi-source-Data)：作为多源 telemetry RCA 的早期强基线和设计背景。

## 默认假设

- 未收到选择卡片答复，因此采用推荐默认值：调用级统一推理额度、Qwen 主实验加 Gemma 复现、每个非饱和数据集 240 个全新 case。
- 本次工作只保存计划和 references；不运行实验、不训练模型、不编写正式实验脚本。
