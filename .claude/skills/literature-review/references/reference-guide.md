# CanvasRCA / CoVisRCA 关键词与参考文献导航

> 更新时间：2026-09-01
> 用途：供本地 coding agent 在实现 Dashboard Builder、RCA Solver、VLM Scorer、RL credit assignment 和协同进化训练时快速定位论文与代码。  
> 原则：优先采用 2025–2026 年工作；较早论文只作为设计语法、贡献度量或实验基础。

## 0. 项目统一表述

本项目可以写成四个相互连接的模块：

1. **Dashboard Builder Agent**：通过受约束工具将 metrics、logs、traces、topology 和 coverage 编译为视觉—文本 dashboard。
2. **RCA Solver Agent**：从 dashboard 与有界 sidecar 中输出 root ranking、evidence IDs、confidence 和 limitations。
3. **VLM Scorer / Process Reward Model**：预测完整 dashboard utility、partial state promise、tool action progress、组件边际贡献及交互贡献。
4. **RL / Co-evolution**：使用固定外部 RCA verifier 的可验证结果训练 Builder、Solver，并周期性校准 scorer。

统一术语：

- `tool-grounded dashboard builder`
- `multimodal observation compiler`
- `evidence-grounded RCA solver`
- `multimodal process reward model`
- `anchor-state group-relative credit assignment`
- `role-specific multi-agent reinforcement learning`
- `population-based cooperative co-evolution`
- `counterfactual dashboard component contribution`

---

# 1. 关键词列表

## 1.1 多模态评分器与 Judge

- multimodal reward model
- vision-language reward model
- VLM-as-a-judge
- multimodal reasoner as a judge
- generative multimodal reward model
- discriminative multimodal reward model
- pairwise multimodal preference modeling
- multi-response reward modeling
- reward model fidelity
- multimodal reward calibration
- multimodal reward hacking

精确查询：

```text
"multimodal reward model" reinforcement learning
"vision-language reward model" pairwise preference
"multimodal reasoner as a judge"
"generative multimodal reward model" process
"multi-response reward modeling" vision language
"multimodal reward hacking" reinforcement learning
"reward model fidelity" multimodal agent
```

## 1.2 Process Reward 与步骤贡献

- multimodal process reward model
- visual process reward model
- agent process reward model
- step-wise promise and progress
- step-level reward modeling
- progress estimator agent RL
- outcome reward versus process reward
- trajectory-level versus step-level reward
- absolute and relative reward

精确查询：

```text
"multimodal process reward model"
"visual process reward model"
"agent process reward model" promise progress
"stepwise progress attribution" LLM agent
"process reward model" tool-using agent
"absolute and relative reward" vision language model
```

## 1.3 Agentic RL 与 Credit Assignment

- group-in-group policy optimization
- anchor-state grouping
- hierarchy-of-groups policy optimization
- fine-grained credit assignment LLM agents
- delayed reward redistribution
- stepwise advantage estimation
- hierarchical credit assignment
- counterfactual credit assignment
- Shapley credit assignment RLHF
- role-specific credit assignment

精确查询：

```text
"group-in-group policy optimization"
"anchor state grouping" credit assignment
"hierarchy-of-groups policy optimization"
"stepwise progress attribution" agent RL
"counterfactual credit assignment" multi-agent
"Shapley credit assignment" RLHF
"role-specific credit assignment" multi-agent LLM
```

## 1.4 Multi-Agent RL 与协同进化

- multi-agent post-co-training
- multi-agent tool-integrated policy optimization
- multi-agent RL LLM workflow
- planner worker credit assignment
- agent-wise advantage normalization
- cooperative co-evolution LLM agents
- agent-data mutual evolution
- challenger solver critic co-evolution
- population cross-play
- unseen partner generalization
- private communication protocol

精确查询：

```text
"multi-agent post-co-training" reinforcement learning
"multi-agent tool-integrated policy optimization"
"multi-agent RL" LLM workflow stability
"agent-wise advantage normalization" multi-agent LLM
"agent-data mutual evolution"
"population cross-play" LLM agents
"unseen partner generalization" multi-agent
```

## 1.5 Dashboard、Chart 与视觉 Agent

- dashboard question answering
- multimodal dashboard agent
- interactive dashboard reasoning
- visually grounded chart reasoning
- chart agent tool use
- dashboard design for VLM
- overview plus detail visualization
- synchronized multimodal dashboard
- graph visualization VLM reasoning
- progressive subgraph visualization
- constrained dashboard generation

精确查询：

```text
"dashboard question answering" multimodal agent
"interactive dashboard reasoning" VLM
"visually grounded chart reasoning" agent
"chart agent" visual tools
"dashboard design" vision-language model
"graph visualization" VLM reasoning
"progressive subgraph visualization" VLM
```

## 1.6 RCA 与 Observability

- microservice root cause analysis
- multimodal telemetry RCA
- metrics logs traces root cause analysis
- LLM agent RCA microservices
- observability dashboard RCA
- fault propagation-aware RCA
- service call graph blind spots
- lag-aware fault propagation
- evidence-grounded RCA
- cross-system RCA generalization

精确查询：

```text
"microservice root cause analysis" metrics logs traces
"multimodal telemetry" root cause analysis
"LLM agent" microservice RCA
"fault propagation-aware benchmark" RCA
"service call graph blind spots" RCA
"lag-aware" microservice root cause analysis
"evidence-grounded" RCA agent
```

## 1.7 组件 Contribution 与 Scorer Fidelity

- counterfactual component contribution
- interventional contribution
- marginal contribution dashboard
- Shapley interaction index
- Shapley-Taylor interaction
- do-intervention contribution
- counterfactual effect decomposition
- selection regret reward model
- attribution fidelity
- interaction fidelity
- contribution sign accuracy

精确查询：

```text
"counterfactual component contribution"
"interventional contribution" dashboard OR visualization
"Shapley interaction index" component design
"counterfactual effect decomposition" multi-agent
"causal contribution" do intervention
"attribution fidelity" reward model
"selection regret" scorer fidelity
```

---

# 2. 最小必读路径

1. **RCAEval**：理解任务、指标、数据和现有 baseline。
2. **Fault Propagation-Aware RCA Benchmark**：理解简单 benchmark 为何可能高估方法。
3. **DashboardQA**：理解 VLM 在 dashboard grounding 和 reasoning 上的困难。
4. **ChartAgent**：理解视觉工具调用。
5. **R1-Reward**：理解 RL 训练生成式多模态 reward model。
6. **VisualPRM**：理解 multimodal process reward。
7. **AgentPRM**：理解 agent action 的 promise/progress。
8. **GiGPO**：理解 macro group 与 anchor-state micro group。
9. **HGPO**：理解历史上下文不一致导致的 advantage 偏差。
10. **MATPO**：理解非对称 Agent 角色的 credit assignment。
11. **Dr. MAS**：理解 multi-agent RL 的归一化和训练稳定性。
12. **Multimodal Reward Hacking**：理解优化 scorer 后的投机风险。

---

# 3. P0 核心论文

## P0-1. Group-in-Group Policy Optimization for LLM Agent Training

- **年份/状态**：2025, NeurIPS 2025
- **论文**：https://arxiv.org/abs/2505.10978
- **代码/项目**：https://github.com/langfengQ/verl-agent
- **项目用途**：Builder 完整 rollout 的 macro advantage；相同 partial DSL state 下不同 tool action 的 micro advantage。
- **实现提醒**：使用 exact state hash；不要把 GiGPO 当成 scorer 训练方法。

## P0-2. Hierarchy-of-Groups Policy Optimization for Long-Horizon Agentic Tasks

- **年份/状态**：2026, arXiv
- **论文**：https://arxiv.org/abs/2602.22817
- **代码/项目**：https://github.com/langfengQ/verl-agent/tree/master/recipe/hgpo
- **项目用途**：解决 step group 中历史上下文不一致；适合多层 partial-dashboard grouping。
- **实现提醒**：相同 DSL 结果若预算、历史观测不同，不一定是同一状态。

## P0-3. R1-Reward: Training Multimodal Reward Model Through Stable Reinforcement Learning

- **年份/状态**：2025, ICLR 2026
- **论文**：https://arxiv.org/abs/2505.02835
- **代码/项目**：https://github.com/yfzhang114/r1_reward
- **项目用途**：训练生成式 VLM scorer；pairwise winner、格式与 reasoning-decision consistency reward。
- **实现提醒**：映射为同一 case 的 Dashboard A/B 比较，而非先回归精确小数。

## P0-4. VisualPRM: An Effective Process Reward Model for Multimodal Reasoning

- **年份/状态**：2025, arXiv
- **论文**：https://arxiv.org/abs/2503.10291
- **代码/项目**：https://internvl.github.io/blog/2025-03-13-VisualPRM/
- **项目用途**：构造 multimodal process supervision；评估 step-level reward；Outcome RM 对比 PRM。
- **实现提醒**：dashboard action 没有绝对 correctness，应改成 promise/progress。

## P0-5. AgentPRM: Process Reward Models for LLM Agents via Step-Wise Promise and Progress

- **年份/状态**：2025, WWW 2026
- **论文**：https://arxiv.org/abs/2511.08325
- **项目用途**：定义 partial dashboard 的未来成功概率和 tool action 的增量 progress。
- **实现提醒**：最适合作为 scorer process head 的理论母体。

## P0-6. SPA-RL: Reinforcing LLM Agents via Stepwise Progress Attribution

- **年份/状态**：2025, arXiv
- **论文**：https://arxiv.org/abs/2505.20732
- **代码/项目**：https://github.com/WangHanLinHenry/SPA-RL-Agent
- **项目用途**：训练 progress estimator；将最终 RCA reward 重分配到 Builder tool actions。
- **实现提醒**：作为 learned progress baseline，与 GiGPO 无 critic 路线对照。

## P0-7. Multi-Agent Tool-Integrated Policy Optimization

- **年份/状态**：2025, arXiv
- **论文**：https://arxiv.org/abs/2510.04678
- **代码/项目**：https://github.com/mzf666/MATPO
- **项目用途**：Builder/Solver 非对称角色 credit；shared backbone 与 role-specific prompt/LoRA。
- **实现提醒**：主实验应比较 shared-policy、isolated-LoRA 和独立模型。

## P0-8. Dr. MAS: Stable Reinforcement Learning for Multi-Agent LLM Systems

- **年份/状态**：2026, arXiv
- **论文**：https://arxiv.org/abs/2602.08847
- **代码/项目**：https://github.com/langfengQ/verl-agent
- **项目用途**：agent-wise advantage normalization；多角色 reward distribution 和 gradient 稳定性。
- **实现提醒**：持续记录每角色 reward、gradient norm、KL、entropy。

## P0-9. MAPoRL: Multi-Agent Post-Co-Training for Collaborative LLMs with RL

- **年份/状态**：ACL 2025
- **论文**：https://aclanthology.org/2025.acl-long.1459/
- **项目用途**：证明单独训练不等于协作；设计 verifier-guided multi-agent post-co-training。
- **实现提醒**：角色同质，与本项目非对称 Builder/Solver 不同。

## P0-10. CoEvolve: Training LLM Agents via Agent-Data Mutual Evolution

- **年份/状态**：2026, arXiv
- **论文**：https://arxiv.org/abs/2604.15840
- **项目用途**：闭环更新训练分布；根据 forgetting、uncertainty 和 failure patterns 生成新经验。
- **实现提醒**：只有存在动态数据/伙伴分布、generation 和 selection 时，才宜称 co-evolution。

## P0-11. CUARewardBench: Evaluating Reward Models for Computer-Using Agents

- **年份/状态**：ICML 2026
- **论文**：https://openreview.net/forum?id=Xj7V0wKlE5
- **代码/项目**：https://github.com/Tencent/CUARewardBench
- **项目用途**：设计 DashboardScorerBench；同时评估 ORM/PRM、trajectory/step。
- **实现提醒**：scorer 不确定时应允许 abstain，并报告 precision/NPV。

## P0-12. Multimodal Reward Hacking in Reinforcement Learning

- **年份/状态**：2026, arXiv
- **论文**：https://arxiv.org/abs/2607.09492
- **项目用途**：检查 proxy reward 提高但真实 RCA utility 下降；设计 NRFR 类指标。
- **实现提醒**：重点攻击：重复 panel、放大实体、颜色/顺序编码、虚假 warning。

## P0-13. DashboardQA: Benchmarking Multimodal Agents on Interactive Dashboards

- **年份/状态**：Findings EACL 2026
- **论文**：https://aclanthology.org/2026.findings-eacl.177/
- **代码/项目**：https://github.com/vis-nlp/DashboardQA
- **项目用途**：dashboard element grounding、跨 panel reasoning、交互轨迹评估。
- **实现提醒**：第一阶段宜先使用静态确定性 canvas。

## P0-14. ChartAgent: Visually Grounded Reasoning in Complex Chart QA

- **年份/状态**：ACL 2026
- **论文**：https://aclanthology.org/2026.acl-long.843/
- **项目用途**：视觉工具库：crop、annotate、localize、axis/region 操作。
- **实现提醒**：映射为 zoom incident interval、crop service row、trace selected edge。

## P0-15. MuSe: Multi-Stage Graph Reasoning via Vision-Language Models

- **年份/状态**：ACL 2026
- **论文**：https://aclanthology.org/2026.acl-long.476/
- **项目用途**：渐进采样和可视化任务相关子图；SFT + GRPO 学习 sampling policy。
- **实现提醒**：大规模 Train Ticket topology 不应一次性渲染。

## P0-16. RCAEval: A Benchmark for Root Cause Analysis of Microservice Systems

- **年份/状态**：WWW Companion 2025
- **论文**：https://arxiv.org/abs/2412.17015
- **代码/项目**：https://github.com/phamquiluan/RCAEval
- **项目用途**：RCA evaluator、数据与 15 个 baseline；AC@K、Avg@K、MRR。
- **实现提醒**：固定论文分支；外部 baseline 用独立环境。

## P0-17. Rethinking the Evaluation of Microservice RCA with a Fault Propagation-Aware Benchmark

- **年份/状态**：FSE 2026
- **论文**：https://operationspai.github.io/revisiting-rca-evaluation/
- **项目用途**：AegisLab/RCABench 来源；复杂传播、层级标签、动态 workload、SLI impact。
- **实现提醒**：简单 benchmark 上复杂模型可能被规则方法追平。

## P0-18. TORAI: Unsupervised Fine-grained RCA using Multi-Source Telemetry Data

- **年份/状态**：FSE 2026
- **论文**：https://arxiv.org/abs/2604.13522
- **项目用途**：trace blind spots 和 graph-free multi-source RCA baseline。
- **实现提醒**：dashboard 必须显式展示 coverage/unknown，而非把缺 trace 画成正常。

# 4. P1 扩展论文

## 4.1 VLM Scorer 与 Reward Model

| 论文 | 链接 | 本项目用途 |
|---|---|---|
| MR. Judge: Multimodal Reasoner as a Judge | https://arxiv.org/abs/2505.13403 | reasoning-based pairwise judge；多维 rubric；避免直接预测不稳定绝对分数 |
| Skywork-VL Reward | https://arxiv.org/abs/2505.07263 | discriminative VLM + reward head + pairwise ranking baseline |
| BaseReward | https://arxiv.org/abs/2509.16127 | reward head、数据混合、backbone/scale/ensemble 的强 baseline recipe |
| You Only Judge Once | https://arxiv.org/abs/2604.10966 | 单次前向 N-way 评分；适合同一 anchor state 的多个 actions |
| GM-PRM | https://arxiv.org/abs/2508.04088 | 找出第一处有害设计决策并生成修复建议 |
| VLM-AR3L | https://arxiv.org/abs/2607.00483 | absolute utility + relative progress 双 reward |
| Agent-RewardBench | https://arxiv.org/abs/2506.21252 | perception/planning/safety 多维 step-level reward benchmark |

## 4.2 Agentic RL、Multi-Agent 与 Co-evolution

| 论文/框架 | 链接 | 本项目用途 |
|---|---|---|
| Agent Lightning | https://arxiv.org/abs/2508.03680 | Agent execution 与训练解耦；trajectory spans；选择性优化 Agent |
| Agent Lightning code | https://github.com/microsoft/agent-lightning | RL trajectory store、tracer、runner 和 trainer 参考实现 |
| Multi-Agent Evolve | https://arxiv.org/abs/2510.23595 | Proposer–Solver–Judge co-evolution |
| SAGE | https://arxiv.org/abs/2603.15255 | Challenger–Planner–Solver–Critic；quality control 防 drift |
| When Does Multi-Agent RL Improve LLM Workflows? | https://arxiv.org/abs/2605.24202 | shared/isolated policy、workflow topology、role gradient instability |
| Relax | https://arxiv.org/abs/2604.11554 | 大规模 omni-modal asynchronous RL；后期系统扩展 |
| Relax code | https://github.com/rednote-ai/Relax | 多角色服务化、异步 rollout 与 staleness 控制 |

## 4.3 Dashboard、Chart、Graph 与视觉推理

| 论文/项目 | 链接 | 本项目用途 |
|---|---|---|
| Dash-M5H | https://aclanthology.org/2026.acl-demo.14/ | 多模态信号时间同步；overview-to-detail evidence tracing |
| Dash-M5H code | https://github.com/nd-hal/M5H-Dashboard-VLM | Quarto + Observable JS + D3 实现参考 |
| ChartMuseum — NeurIPS 2025 Datasets and Benchmarks | https://papers.nips.cc/paper_files/paper/2025/hash/ca20efa9cf3703186d91424cf4876f8b-Abstract-Datasets_and_Benchmarks_Track.html | 复杂 visual reasoning benchmark；区分视觉推理与文本捷径 |
| The Perils of Chart Deception — IEEE VIS 2025 short paper / Best Short Paper | https://sfa.ieeevis.org/year/2025/program/paper_1628b4eb-473e-4157-9d19-44990b75efc7.html | 轴、比例、颜色和编码对 VLM 的误导与 stress test；short-paper status 不写成 VIS full paper |
| Look Less, Reason More | https://aclanthology.org/2026.acl-long.225/ | 学习何时使用 crop/zoom 等视觉操作 |
| Visually-Guided Policy Optimization | https://aclanthology.org/2026.acl-long.301/ | 防止 VLM RL 忽略图像；visual activation 和 visual forgetting |
| VGPO code | https://github.com/wzb-bupt/VGPO | visual-aware advantage 实现参考 |
| MUSE: Unified Agentic Harness for MLLMs | https://arxiv.org/abs/2606.03005 | structured parsing、deterministic verification、verifier-guided repair |
| Multimodal Self-Instruct | https://aclanthology.org/2024.emnlp-main.1072/ | 合成 dashboards/graphs/flowcharts 与 atomic grounding data |
| ScreenAI | https://arxiv.org/abs/2402.04615 | UI/infographic understanding、region annotation |
| Ferret-UI | https://arxiv.org/abs/2404.05719 | 高分辨率 UI grounding 和小区域理解 |

## 4.5 RQ2 固定 Dashboard 设计空间

下表只记录已由会议官网、ACL Anthology、CVF Open Access 或正式
proceedings 核验的发表状态。它们为 RQ2 的 design language、资格检查和
机制分析提供依据；它们不预先证明某个 CanvasRCA dashboard 设计会提高
RCA。

| 论文 | 已核验状态与链接 | RQ2 可迁移要点 |
|---|---|---|
| DashBot | [IEEE VIS 2022 full paper](https://virtual.ieeevis.org/year/2022/paper_v-full-1033.html) | 将 dashboard 设计写成显式、受约束的动作空间；不把其训练型 RL selector 搬入 RQ2 |
| Dashboard Design Patterns | IEEE VIS 2022（会议 papers/sessions 正式记录） | 用 arrangement、coordination 和多视图关系定义可审计设计因素 |
| DMiner | [IEEE VIS 2023 / TVCG](https://content.ieeevis.org/year/2023/paper_v-tvcg-10057994.html) | 区分单视图 encoding 与跨视图 arrangement/coordination，支持 RQ2 的 M/G/A 因素边界 |
| From Dashboard Zoo to Census | [IEEE VIS 2025](https://sfa.ieeevis.org/year/2025/program/paper_aeb6a938-4d06-4c0d-828a-6152918115c3.html) | 用 content blocks 与关系图描述 dashboard composition，支持固定 DSL 而不是自由像素生成 |
| Vega-Lite | [IEEE VIS 2016](https://www.ieeevis.org/year/2016/info/overview-amp-topics/papers-sessions) | 声明式 grammar 使 encoding、layout 和 data transform 可复现、可消融 |
| Draco | [IEEE VIS 2018](https://www.ieeevis.org/year/2018/info/papers-sessions) | 用约束和偏好表达 visualization design space；RQ2 只借用显式约束思想，不借用 learned selector |
| Draco 2 | [IEEE VIS 2023 short paper](https://content.ieeevis.org/year/2023/paper_v-short-1018.html) | 可扩展约束平台支持将设计规则版本化并检查非法组合 |
| ChartVerse | [ACL 2026 long paper](https://aclanthology.org/2026.acl-long.344/) | answer-first、truth-anchored QA 合成支持从可见事实确定性地产生 packed operation questions |
| ChartMuseum | [NeurIPS 2025 Datasets and Benchmarks](https://papers.nips.cc/paper_files/paper/2025/hash/ca20efa9cf3703186d91424cf4876f8b-Abstract-Datasets_and_Benchmarks_Track.html) | 将 chart perception 与语言捷径分离，并单独报告复杂视觉读取失败 |
| On the Perception Bottleneck of VLMs for Chart Understanding | [Findings of EMNLP 2025](https://aclanthology.org/2025.findings-emnlp.573/) | packed QA 需要分别评价 lookup、组合和最终 RCA，不能用 RCA 分数掩盖 perception failure |
| VLM²-Bench | [ACL 2025 long paper](https://aclanthology.org/2025.acl-long.372/) | 测试模型能否连接显式对应线索，支持 cross-source alignment operation |
| Visual Graph Understanding / VGCure | [ACL 2025 long paper](https://aclanthology.org/2025.acl-long.1482/) | 单独测试节点、边方向和路径，避免用整体 RCA 替代 topology qualification |
| Words or Vision | [CVPR 2025](https://openaccess.thecvf.com/content/CVPR2025/html/Deng_Words_or_Vision_Do_Vision-Language_Models_Have_Blind_Faith_in_CVPR_2025_paper.html) | 冻结图文顺序并检查 text bias；attention 只作为相关性诊断 |
| S-VCO | [ACL 2025 long paper](https://aclanthology.org/2025.acl-long.1462/) | 对称视觉对比提示说明非语义视觉扰动应作为稳定性控制，而非新事实 |
| BlackVIP | [CVPR 2023](https://openaccess.thecvf.com/content/CVPR2023/html/Oh_BlackVIP_Black-Box_Visual_Prompting_for_Robust_Transfer_Learning_CVPR_2023_paper.html) | 黑盒视觉提示可改变 frozen model 行为，支持 skin perturbation 但不支持把它解释为事实贡献 |
| Text or Pixels? | [Findings of EMNLP 2025](https://aclanthology.org/2025.findings-emnlp.558/) | 将 token efficiency 与 accuracy 分轴报告，并保留 text screenshot negative control |
| HORNet | [CVPR 2026 Workshop](https://openaccess.thecvf.com/content/CVPR2026W/CV4Smalls/html/Bai_HORNet_Task-Guided_Frame_Selection_for_Video_Question_Answering_with_Vision-Language_CVPRW_2026_paper.html) | 仅作为 task-guided input selection 的 workshop 证据；不得写成 CVPR main-track，也不在 RQ2 训练 selector |
| CLEVR | [CVPR 2017](https://openaccess.thecvf.com/content_cvpr_2017/html/Johnson_CLEVR_A_Diagnostic_CVPR_2017_paper.html) | 用可执行函数程序与 effective program size 衡量必要推理深度，并检查能跳过中间步骤仍答对的 shortcut；支持将 reasoning difficulty 与视觉区域数分开 |
| MultiChartQA | [NAACL 2025 long paper](https://aclanthology.org/2025.naacl-long.566/) | 区分 direct、parallel、comparative 与 sequential multi-chart reasoning；支持 RQ1.1 的 direct lookup、dependent bridge 与 compare-and-aggregate 三类程序 |
| StrategyQA | [TACL 2021](https://aclanthology.org/2021.tacl-1.21/) | 每题同时保留分解步骤和逐步支持证据，支持公开问题/私有确定性 solver/support fact 的物理分离 |

仍保持 `preprint`：`NL2Dashboard` 与 `Toward a Machine Bertin`。在未找到
会议官网、ACL Anthology、CVF、IEEE VIS、PMLR 或 OpenReview 正式记录前，
不得自行升级 venue。

## 4.4 RCA 与 Observability

| 论文/项目 | 链接 | 本项目用途 |
|---|---|---|
| MicroRCA-Agent | https://arxiv.org/abs/2509.15635 | Drain 日志压缩、trace 异常、node-service-pod LLM RCA |
| MicroRCA-Agent code | https://github.com/tangpan360/MicroRCA-Agent | 可运行 LLM/Agent RCA baseline |
| LATS-RCA | https://arxiv.org/abs/2605.03505 | reflection-guided tree search 和多 Agent RCA |
| How Far Can RCA Go on Real-World Telemetry? | https://arxiv.org/abs/2607.13548 | 区分 Reasoning Gap 与 Data Ambiguity；Builder/Solver failure 分解 |
| Lag-Aware RCA | https://conf.researchr.org/details/fse-2026/fse-2026-industry-papers/18/ | propagation lag；避免把上下游症状当同步事件 |
| CARE | https://conf.researchr.org/details/fse-2026/fse-2026-journal-first/32/ | trace + profiling metrics；request/service/community context |
| Active Intervention Multi-Root RCA | https://conf.researchr.org/details/fse-2026/fse-2026-research-papers/144/ | 后续 multi-root 与 active diagnostic RL |

---

# 5. Contribution Ground Truth 与 Scorer Fidelity

| 论文 | 链接 | 本项目用途 |
|---|---|---|
| Counterfactual Effect Decomposition in Multi-Agent Sequential Decision Making | https://proceedings.mlr.press/v267/triantafyllou25a.html | 分解 Builder action 通过 Solver 行为与环境状态对最终 RCA 的影响 |
| SCAR: Shapley Credit Assignment for RLHF | https://arxiv.org/abs/2505.20417 | Shapley-style dense reward baseline |
| Shapley-Taylor Interaction Index | https://proceedings.mlr.press/v119/sundararajan20a.html | dashboard component 二阶交互贡献 |
| KernelSHAP-IQ | https://proceedings.mlr.press/v235/fumagalli24a.html | 昂贵 RCA rollout 下高效近似 interaction |
| On Measuring Causal Contributions via do-interventions | https://proceedings.mlr.press/v162/jung22a.html | 区分相关归因和 causal contribution |
| Structure-Preserving Interventions | https://proceedings.mlr.press/v238/janzing24a.html | 替换 panel 时尽量保持整体结构和分布 |

推荐 reference contribution：

```text
Q_x(s,a)
  = E[ downstream RCA utility
       | same case, same partial state, choose action a,
         matched completion seeds, matched Solver population ]

credit_x(s,a)
  = Q_x(s,a) - mean_{a' in legal_actions(s)} Q_x(s,a')
```

优先级：

1. RL primary credit：anchor-state sibling action relative credit。
2. 局部解释：single-factor controlled intervention。
3. 全局总结：Monte Carlo Shapley-style average。
4. 交互分析：二阶 intervention / Shapley-Taylor。
5. 不把 Shapley 值自动称为 causal contribution。

---

# 6. Scorer 精度评估指标

## 6.1 完整 Dashboard Utility

- MAE / normalized MAE
- Spearman correlation
- Kendall correlation
- pairwise preference accuracy
- K-way ranking accuracy
- top-K layout recall
- ECE / calibration
- uncertainty–error correlation

## 6.2 Anchor-State Action Credit

- within-anchor Spearman
- within-anchor Kendall
- best-action accuracy
- selection regret
- contribution sign accuracy
- neutral-action F1
- promise MAE
- progress MAE

## 6.3 Interaction Credit

- synergy/redundancy sign accuracy
- pairwise interaction rank correlation
- top-K interaction recall
- attribution completeness residual

## 6.4 下游用途

- scorer 选中 layout 的真实 RCA utility
- simple regret
- best utility after N real evaluations
- area under search curve
- 达到目标 utility 所需 executor calls
- Test-ID / Test-OOD 表现

## 6.5 Reward Hacking

- Newly Rewarded Failure Rate
- layout-only leakage probe
- panel duplication attack
- color/size/order shortcut sensitivity
- unseen Solver transfer
- unseen renderer skin transfer

---

# 7. “迷茫时查哪篇”索引

| 问题 | 首先阅读 | 然后阅读 |
|---|---|---|
| 不知道如何定义 step credit | AgentPRM | SPA-RL, GiGPO |
| 同一 anchor group credit 很噪 | HGPO | GiGPO |
| VLM scorer RL 不稳定 | R1-Reward | Dr. MAS |
| scalar 还是 pairwise scorer | MR. Judge | Skywork-VL Reward, You Only Judge Once |
| 想定位第一处有害 layout action | GM-PRM | VisualPRM |
| absolute utility 与 relative progress | VLM-AR3L | AgentPRM |
| Builder/Solver reward 难拆 | MATPO | Counterfactual Effect Decomposition |
| 多 Agent 梯度爆炸/角色失衡 | Dr. MAS | When Does Multi-Agent RL Improve LLM Workflows? |
| 是否能称 co-evolution | CoEvolve | Multi-Agent Evolve, SAGE |
| dashboard 太密集 | DashboardQA | ChartMuseum |
| Solver 需要视觉工具 | ChartAgent | Look Less, Reason More |
| 大 topology 图太乱 | MuSe | TORAI |
| RL 后模型忽略图像 | VGPO | Multimodal Reward Hacking |
| 图表样式误导 VLM | Chart Deception | Multimodal Reward Hacking |
| RCA baseline 怎么跑 | RCAEval | TORAI, MicroRCA-Agent |
| 失败来自 Builder 还是 Solver | How Far Can RCA Go? | VisualPRM |
| contribution reference target | Counterfactual Effect Decomposition | do-interventions, Shapley-Taylor |
| 组件交互贡献 | Shapley-Taylor | KernelSHAP-IQ |
| Agent RL 基础设施 | Agent Lightning | Relax |
| 浏览器多模态 dashboard | Dash-M5H | DashboardQA |

---

# 8. 代码模块与论文映射

```text
src/
├── builder/
│   ├── policy.py
│   ├── tools.py
│   ├── state_hash.py
│   └── rollout.py
│       # GiGPO, HGPO, ChartAgent, MuSe
│
├── solver/
│   ├── model.py
│   ├── certificate.py
│   └── visual_tools.py
│       # ChartAgent, VGPO, MicroRCA-Agent
│
├── scorer/
│   ├── pairwise_judge.py
│   ├── absolute_head.py
│   ├── process_head.py
│   ├── interaction_head.py
│   └── calibration.py
│       # R1-Reward, VisualPRM, AgentPRM,
│       # MR. Judge, VLM-AR3L, BaseReward
│
├── credit/
│   ├── macro_group.py
│   ├── anchor_group.py
│   ├── promise_progress.py
│   ├── counterfactual.py
│   └── interactions.py
│       # GiGPO, HGPO, SPA-RL, SCAR,
│       # Counterfactual Effect Decomposition,
│       # Shapley-Taylor
│
├── coevolution/
│   ├── alternating.py
│   ├── population.py
│   ├── cross_play.py
│   └── archive.py
│       # MAPoRL, MATPO, Dr. MAS, CoEvolve, SAGE
│
├── verifier/
│   ├── rca_utility.py
│   ├── evidence.py
│   ├── faithfulness.py
│   ├── leakage.py
│   └── reward_hacking.py
│       # CUARewardBench, Multimodal Reward Hacking, RCAEval
│
└── dashboards/
    ├── dsl.py
    ├── renderer.py
    ├── registry.py
    └── validators.py
        # DashboardQA, Dash-M5H, Chart Deception, ScreenAI
```

---

# 9. 不能混淆的概念

1. **GiGPO 不是 scorer 训练方法。**  
   它训练 agent policy；其 macro/micro groups 可以用于构造 scorer target。

2. **VisualPRM 的 step correctness 不等于 dashboard action correctness。**  
   dashboard action 应按 conditional promise/progress 定义。

3. **Shapley value 不自动等于 causal contribution。**  
   必须明确 baseline、coalition distribution、预算重分配和 intervention 规则。

4. **动态 scorer 不能成为最终真值。**  
   objective RCA verifier 必须固定；scorer 是 learned surrogate/critic。

5. **联合训练不自动等于协同进化。**  
   至少需要 generation/snapshot、动态伙伴或数据分布、selection 和 cross-play。

6. **最终配对表现高不证明通用协作。**  
   必须评估 unseen partner、unseen backbone、layout leakage 和跨系统 OOD。

7. **由同一 telemetry 渲染图像不代表加入新信息。**  
   应表述为 representation 或 inductive bias。

---

# 10. 定期更新检索模板

```text
site:arxiv.org ("multimodal reward model" OR "VLM judge") after:2026-07-01
site:arxiv.org ("process reward model" AND agent) after:2026-07-01
site:arxiv.org ("credit assignment" AND "LLM agent") after:2026-07-01
site:arxiv.org ("multi-agent RL" AND LLM) after:2026-07-01
site:arxiv.org ("co-evolution" AND LLM agent) after:2026-07-01
site:aclanthology.org dashboard multimodal agent 2026
site:conf.researchr.org root cause analysis microservice 2026
site:arxiv.org dashboard VLM reinforcement learning
```

纳入文献库前检查：

- 是否有官方论文页；
- 是否有正式 venue 或明确标注为 preprint；
- 是否有官方代码；
- 是否真正解决 scorer、credit、dashboard、RCA 或 co-evolution；
- 是否只是名称相似；
- 训练设置、数据规模、reward 定义是否可复现。

---

# 11. 当前最可执行的技术组合

- **Builder RL**：GiGPO + HGPO-style context-consistent anchor groups
- **Scorer**：R1-Reward-style generative pairwise judge
- **Process target**：AgentPRM promise/progress + VisualPRM-style process data
- **Multi-agent training**：MATPO role-specific credit + Dr. MAS agent-wise normalization
- **Co-evolution**：alternating population cross-play，参考 MAPoRL/CoEvolve
- **Visual tools**：ChartAgent-style typed tools
- **Reward safety**：CUARewardBench protocol + Multimodal Reward Hacking stress tests
- **RCA evaluation**：RCAEval + fault-propagation-aware benchmark
- **Contribution reference**：anchor-state sibling interventions；Shapley-Taylor 仅用于全局 interaction summary

研究链：

```text
dashboard representation
→ component effects
→ reference contribution
→ scorer fidelity
→ scorer-guided selection
→ RL credit assignment
→ Builder–Scorer–Solver co-evolution
```
