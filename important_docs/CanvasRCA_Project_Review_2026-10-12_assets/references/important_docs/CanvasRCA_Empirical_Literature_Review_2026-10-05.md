# 实证研究范式、历史去重与下一阶段新意审查

日期：2026-10-05。项目级研究复核，配套[下一阶段目标与候选方法](CanvasRCA_Empirical_to_Method_2026-10-05.md)。本次没有新增推理调用、运行作者模型、修改历史实验或公共参考指南。

## 1. 问题、来源与范围

问题是：什么样的实证发现能独立改变视觉RCA的设计判断，怎样从它推出一个比“加图”更具体、可在投稿前检验的新方法？重点排除与本项目既有实验、视觉压缩、图表感知、证据组织及工具RCA的重叠。

阅读入口为Codex.md、项目reference-guide、9月30日文献/主线综述、docs实验报告索引，以及RQ3.18现行协议/findings。资料以2025–2026为主，补充TACL/ASE 2024作为成熟实证范式。正式发表身份优先查官方记录；arXiv可用于方法对比，但不冒称正式接收。技术论据不依赖聚合站、搜索摘要或新闻稿。

检索主题包括：empirical study causal RCA；multimodal text preference；visual text compression；task-aware compression；chart perception/binding；model-aware visualization；counterexample-guided visual reasoning；evidence grouping。纳入真正改变测量、算法差别或投入决策的论文。排除仅标题相似的3DGS压缩、自动驾驶传感融合、泛图生成工具；训练型方法可作新意边界，不直接移植为当前冻结模型的实现。

阅读深度有差别：下表明确区分正文关键章节复核和摘要筛查。正文复核不等于逐页验证附录证明、复现实验或审计作者代码。项目报告复核不等于重新逐条人工检查其全部回答。一次搜索找不到同名方法不能证明首创。

## 2. 实证范式与最近相关工作

| 工作、出处 | 本次核对范围 | 核心可借鉴点；与CanvasRCA的边界 |
|---|---|---|
| **Lost in the Middle**，Nelson F. Liu等，TACL 2024 | 官方元数据，正文任务、位置控制、结果、架构/查询/指令替代解释 | 有效容量与名义容量分离；自然任务和可控任务互相检验。不是顶会主会论文，也不直接证明RCA存在同一位置效应。[正式页](https://aclanthology.org/2024.tacl-1.9/)，[正文](https://arxiv.org/html/2307.03172) |
| **Words or Vision**，Ailin Deng等，CVPR 2025 | 正式PDF、正文图文条件、实验设置、影响因素和SFT方案 | 一致/冲突/无关条件共同约束偏好解释；发现推动针对性修复。它的冲突数据不等于我们正确且一致的遥测，不能直接归因本项目失败。[正式PDF](https://openaccess.thecvf.com/content/CVPR2025/papers/Deng_Words_or_Vision_Do_Vision-Language_Models_Have_Blind_Faith_in_CVPR_2025_paper.pdf)，[正文](https://arxiv.org/html/2503.02199) |
| **Root Cause Analysis…How Far Are We?**，Luan Pham、Huong Ha、Hongyu Zhang，ASE 2024 Research | 官方track；正文数据生成、实现、图恢复/定位、耗时、长度和故障时间条件 | 分解流水线、报告条件失效，复杂方法不能省略简单强基线。时间边界敏感性提示我们不得用注入时间给输入提供便利。[官方页](https://conf.researchr.org/details/ase-2024/ase-2024-research/57/Root-Cause-Analysis-for-Microservice-System-based-on-Causal-Inference-How-Far-Are-We)，[正文](https://arxiv.org/html/2408.13729) |
| **Rethinking the Evaluation…Fault Propagation-Aware Benchmark**，Aoyang Fang等，AegisLab相关研究 | 作者项目；正文研究设计、基准构造、结果和失败条件。本文不新增其venue认证 | 从旧基准的简化假设推导新评价工具；价值不限于发明排名算法。我们的Aegis实验不能再把“传播复杂”作为自己的新发现。[项目](https://operationspai.github.io/revisiting-rca-evaluation/)，[正文](https://arxiv.org/html/2510.04711v2) |
| **On the Perception Bottleneck of VLMs for Chart Understanding**，Junteng Liu等，EMNLP Findings 2025 | 官方摘要与元数据；结合项目已有阅读记录 | 已区分视觉表示与信息提取瓶颈，含训练改进。不能把“图上有但模型读不到”说成我们首创；不据摘要断言作者没有某项控制。[论文页](https://aclanthology.org/2025.findings-emnlp.573/) |
| **Text or Pixels?**，Yanhong Li等，EMNLP Findings 2025 | 官方摘要、任务及元数据 | 文字变图片的token压缩已有直接工作；本项目不复活文字截图方法。其检索/摘要结果不是RCA证据。[论文页](https://aclanthology.org/2025.findings-emnlp.558/) |
| **Vision Centric Token Compression / VIST**，NeurIPS 2025 | 正式正文架构、训练与压缩路径 | 远端文字图像与近端文字的slow/fast设计，含可训练resampler及交叉注意力。混合载体省token本身不新；现行不训练路线不能声称复现了它。[正文](https://proceedings.neurips.cc/paper_files/paper/2025/file/2f8b56543953d60f262fb2c4b85c50b3-Paper-Conference.pdf) |
| **ETC**，Yiling Gao等，arXiv v2，2026-07-23；未核实正式venue | 正文目标、注意力统计、蒸馏/训练与部分消融 | 已有任务信息保持的压缩目标。我们不能仅换“诊断充分性”名词就主张新意；其模型内部训练方法不在当前授权范围。[正文](https://arxiv.org/html/2606.00543) |
| **Record Grouping Controls Evidence Weight in Language Models**，Zhongxuan Liu等，arXiv 2026-09；未核实venue | 正文问题定义、来源分组、等长控制、实验及主结果 | 内容、分组、重复的贡献已有直接受控研究。普通来源去重/每组一次投票不应成为新核心算法。[正文](https://arxiv.org/html/2609.08698v1) |
| **Which Source Wins?**，Rodela Ghosh等，arXiv 2026-08；未核实venue | 摘要、研究设计及图表/文字冲突条件 | 模态偏好可随任务、证据和模型反转；仅“发现视觉有时好有时坏”不足。与本项目无冲突同事实条件不同。[正文](https://arxiv.org/html/2608.17205) |
| **LegendBench**，Xinnuo Zhang等，arXiv 2026-09；未核实venue | 摘要、任务分类及受控设计说明 | 图例绑定与不变性探针已有工作；不可把绑定探针或针对性训练本身称为创新。[正文](https://arxiv.org/html/2609.24172) |
| **Proof-of-Perception**，Arya Fayyazi、Haleh Akrami，arXiv 2026-02；未核实venue | 正文问题、节点证书、训练、控制器和计算分配 | 中间错误/可靠性指导预算已有相邻方法。我们拟研究离线编译、冻结模型、已知源数据与单次RCA；不继承其保证，也不宣称所有自适应可靠性方法都未做过。[正文](https://arxiv.org/html/2603.00324) |
| **MoCE**，NSDI 2026 | USENIX官方页，与项目既有方法笔记对照 | 上下文组织与异构诊断DAG已存在。类型化编译只是可复现基础设施，不能仅靠名字成为贡献。[官方页](https://www.usenix.org/conference/nsdi26/presentation/harsh) |
| **DashboardQA**，EACL Findings 2026 | 继承项目已核实官方摘要/元数据；本次未重新读完整PDF | dashboard多视图定位/问答并非空白，RCA排名和预算才是本项目需补的后果。[官方页](https://aclanthology.org/2026.findings-eacl.177/) |
| **Fico**，ACL Findings 2026 | 官方摘要/元数据筛查 | 保真、密度、OCR与任务表现需分开；不能把一般OCR压缩结果直接移植为诊断收益。[官方页](https://aclanthology.org/2026.findings-acl.1758/) |

其他邻近RCA工作（FoundRoot、TORAI、MuSe、ThinkFL、VGCure、VLM²-Bench、VLM4TS等）按[9月30日综述](../docs/CanvasRCA_Literature_Gaps_and_Storyline_2026-09-30.md)中的出处与阅读边界复核，不在本文伪称重新复现全部论文。它们已覆盖多源、图组织、工具、关联或训练路线。GiGPO/HGPO/PRM/co-evolution相关目录也已重新检查；当前时间、冻结模型和无训练条件下，不把其整套训练路线加入本轮。

本地SIRCL原始README自述为单次推理提示设计的匿名投稿材料；self-evolving目录的README使用SEER名称及离线演化/在线工具流程。没有据本地目录名认定正式发表状态。它们适合作为待协议审查的强系统基线，原项目“最佳MRR”不能无条件拼到CanvasRCA主表。

## 3. 从这些论文得到的研究方法，而不是接收秘诀

第一，找一个会改变实践的错误预期：更多上下文、更多模态、完整拓扑、数学保真，是否必然让诊断更可靠？这些预期只有被具体操控和观察，才会产生新知识。

第二，寻找反例后立即建立最小可控任务，并回到真实任务验证。合成观测可以精确标注“哪一个p95属于哪一个实体”，却不能替代真实故障标签。真实排名与公开理由分别验证，不能把理由流畅当作正确。

第三，广度来自**可分离条件**。模型、任务、密度、预算、实体粒度分别变化时，才知道规律在哪成立。不同数据集同时改变图规模、故障类型和观测来源，不能据数据集相关性发明一个通用阈值。

第四，新方法必须改变被识别的变量，而不是同时加统计、提示、图像和输出规则。我们已有足够基础设施，最值得投入的是实测联合读取错误如何改变单次诊断的表示分配；普通去重、图形库或高分臂命名均不够。

第五，严谨与速度可以兼容：复用已有有效对照，先审计CPU事实/预算；只为尚缺的关键差别花调用。所有子模块分别显著并不是系统论文的一般必要条件，但宣称哪个模块贡献了收益，就需要对应证据。当前各轮已登记规则不事后改写。

## 4. 全历史报告的复核与去重清单

下列均按当前权威版本阅读正文/结论/限制，关键数值回到原表核对。大批逐arm表和原始轨迹并未全部重新算或逐句人审；机器可读清单记录路径、SHA256及阅读范围。资格报告单独列，不能充当方法效果。没有完整报告的RQ3.9只复核描述/视觉资格，不赋予效果结论。

[阅读与来源清单](artifacts/CanvasRCA_Empirical_Literature_Review_2026-10-05/review_manifest.json)包含22份报告/回顾和9项约束、协议或状态材料；原始结果均保留。

| 报告/阶段 | 阅读后保留的设计判断 |
|---|---|
| [RQ1.1/RQ2.1](../docs/experiment_reports/RQ1_1_RQ2_1_findings/findings.md) | 条件性关系视觉收益；纯视觉/截图/随机选择并非通用赢家；QA与RCA不能互换 |
| [旧SEARCH回顾](../RQs/RQ3/findings/search_retrospective_20260912.md) | owner/资源/Trace互补有条件；更多说明、更长thinking和引用未稳定改善 |
| [Tournament](../docs/experiment_reports/Tournament_Analysis_2026-09-15.md) | 38轮停止；成功并集不是单方法性能；不能用oracle挑法 |
| [RQ3.1](../docs/experiment_reports/RQ3_1_Results_Analysis_2026-09-19.md) | 竞争包丢失资源、node证据；已有压缩/预算/鲁棒性控制须去重 |
| [RQ3.2](../docs/experiment_reports/RQ3_2_Results_Analysis_2026-09-22.md) | 覆盖修复不等于排名修复；时窗及操作无效等限制不能抹掉 |
| [RQ3.3](../docs/experiment_reports/RQ3_3_Results_Analysis_2026-09-24.md) | 追加见证比替换更可行但收益有限；两轮核验成本高 |
| [RQ3.4](../docs/experiment_reports/RQ3_4_Results_Analysis_2026-09-25.md) | 形式/引用核验不是根因保证；接口与科学机制分开 |
| [RQ3.5](../docs/experiment_reports/RQ3_5_Screen_Analysis_2026-09-26.md) | 二值联合、请求分组已经测过；后续未运行分支不能当作失败结果 |
| [RQ3.6-A](../docs/experiment_reports/RQ3_6_Stage_A_Analysis_2026-09-26.md) | 文本接口校准有收益；换证据可修复也可破坏 |
| [RQ3.6-B](../docs/experiment_reports/RQ3_6_Mechanisms_Analysis_2026-09-28.md) | 同类/宿主去重及关系视觉已有条件正证据；不是新候选首创 |
| [跨实验画像](../docs/experiment_reports/Cross_Experiment_Method_Profile_2026-09-26.md) | 资源、故障和来源严重混杂；只能同协议配对，不能跨阶段排冠军 |
| [RQ3.7-A/B](../docs/experiment_reports/RQ3_7_Results_Analysis_2026-09-28.md) | 局部融合整体有信号；归属线本身未建立贡献；单位仍敏感 |
| [RQ3.7-C/RQ3.8](../docs/experiment_reports/RQ3_7C_RQ3_8_Qwen_Analysis_2026-09-30.md) | 完整图可损害已有强文本能力；eval/test均暴露；重复/冲突控制已存在 |
| [RQ3.9描述与视觉资格](../RQs/RQ3_9/descriptions/visual_review_2026-10-01.md) | 只有局部比较/分离画法资格材料，未取得完整方法分析；不写成零收益 |
| [RQ3.10](../docs/experiment_reports/RQ3_10_Qwen_Analysis_2026-10-01.md) | 负面peer证据适用性有限，范围矩阵未建立收益且更贵 |
| [RQ3.11](../docs/experiment_reports/RQ3_11_Qwen_Analysis_2026-10-01.md) | 数值保护/精确补丁已实测失败，必须有新机制才可再研究压缩 |
| [RQ3.12](../docs/experiment_reports/RQ3_12_Qwen_Analysis_2026-10-02.md) | 参考预测可计算性不等于诊断适用性，不能重启原候选 |
| [RQ3.13资格](../docs/experiment_reports/RQ3_13_Qualification_2026-10-02.md)及[结果](../docs/experiment_reports/RQ3_13_Qwen_Analysis_2026-10-02.md) | 资格时暂停随后获授权完成；AIOPS/Aegis相反趋势、资源显著性和编号问题需分开 |
| [RQ3.14](../docs/experiment_reports/RQ3_14_Qwen_Analysis_2026-10-02.md) | 窗口统计文本是正证据；真实曲线没有超过同摘要强文本 |
| [RQ3.15](../docs/experiment_reports/RQ3_15_Qwen_Analysis_2026-10-03.md) | 连续父子配对未战胜边际；Top1/Top5及返回数量问题分开 |
| [RQ3.16](../docs/experiment_reports/RQ3_16_Qwen_Analysis_2026-10-03.md) | 固定五的收益与边际图元收益分开；点贡献未建立；≤5%成本信号有可复算依据 |
| [RQ3.17](../docs/experiment_reports/RQ3_17_Qwen_Analysis_2026-10-04.md) | 全组合不采用；CPU资格是用户豁免；节点/矩阵均未超原生边际；解释反例保留 |
| [RQ3.18现行findings](../RQs/RQ3_18/findings/exp_population_readout_findings.md)及[协议](../docs/experiment_plans/RQ3_18_Population_Readout_Plan_2026-10-04.md) | 新11臂在跑；已删除旧六臂不是当前计划；无完整正式结果，不进行部分MRR选择 |

另外复核旧Composer SFT、selection/design attribution、frozen-solver generalization的findings：SFT完成与工具格式成绩不代表RCA学习收益，后两项未完成正式研究；旧段落“未训练”与后续完成记录要按时间区分。Tournament末态报告优先于其逐轮历史运行笔记。没有重启这些路线。

## 5. 尚欠的证据与明确不做的工作

当前缺少的是：紧凑强文本与视觉替换的公平预算账、实测联合读取错误能否预测/修复RCA、冻结后的独立事件证据、协议兼容的外部基线与可测计算成本。已有事实/历史结果用于提出假设，不能追认新方法已成立。

本次不新增拓扑、截图、竞争根因规则、训练、attention、新模型或多agent；不把旧全部结果混成一个大样本做显著性投票；不将无label泄露视为足够的公平性条件。已经有明确重复的比较，不再花GPU重跑。

研究交付应是：**有用的条件规律＋由规律决定的可执行算法＋同事实强文本与同预算系统对照＋完整成本和边界。** 这比单纯“视觉有收益”更有发表价值，但仍需实际证据，而不是在计划里写成结果。
