# 历史差异、复用与新意边界

本附件对应2026-10-09批准的来源分区计划。旧 `RQ4_2_Pure_Visual_Compilation_Recommendation_2026-10-09.md` 保留作历史建议，不是执行队列。

## 复核依据

| 已读报告 | 证据 | 本轮决定 |
|---|---|---|
| RQ4_1_Qwen_Analysis_2026-10-09.md（完整708行） | T_FULL .4846；A_UNIFORM_E50 .3517；CVC_E50 .3332；剪枝节省token未等比例节省耗时；CVC/REWIRED高度相似 | 保留强文本结果，改验编码器连接；先审核实际分组差异 |
| RQ3_21_Qwen_Analysis_2026-10-06.md（完整445行） | 可逆编译仍可能损害阶段读取；位置扰动超过重复噪声 | 数学完整性与模型读取分开测；不以重新分组名义声称首次实体组织 |
| RQ3_7_Results_Analysis_2026-09-28.md（完整182行） | 完整局部绑定方案部分有效，邻近/连线单独归因有限 | 同图比较编码操作，不再排版网格搜索 |
| RQ1_1_RQ2_1_findings/findings.md（完整275行） | 已涉及表示、空间、编码、分辨率、QA与RCA关系 | 上述概念不能单独充当新贡献 |

报告行数是设计评审时快照；引用位于 `docs/experiment_reports/`。四轮评审均向评审者提供了这些完整报告，不能仅凭主方案摘要得分。

## 每臂必要性和复用

| 本轮条件 | 最近历史条件 | 实质不同 | 复用规则 |
|---|---|---|---|
| T_FULL参考 | RQ4.1 T_FULL | 无 | 220历史回答直接引用，不新增调用 |
| A_UNIFORM参考 | RQ4.1 A_UNIFORM_E50 | 无 | 历史结果引用，不新增调用 |
| FULL | RQ4.1 V_FULL | 新的受实际字体资格约束的四区完整图 | 像素/processor实际输入不同才需新调用 |
| GEOM | FULL | 0–22块四组attention，最后四块全局 | 与FULL实际计算不同 |
| SEM | GEOM | 来源引导重新分组，完整token/位置不变 | 无严格改善时完整映射等同GEOM，引用其提交 |
| SHAM | SEM、RQ4.1 REWIRED | 错误关系只改变encoder分组，不是后编码剪枝 | 强度门槛失败首次调用前取消，不换种子 |
| NATIVE4 | FULL | 原像素四图，原生图像边界/位置处理 | 系统对照，不解释为纯attention差异 |
| 独立QA | RQ4.1 QA | 新接口排除RCA任务污染，明确跨卡片关系问题 | 历史错误任务QA不能作同期正确接口回答 |

不安排常规完整输入重复、同期强文本或桥接重跑。生成身份不含scorer/arm名称，避免同一个计算因改名重复付费。历史跨时期参考不作同期速度证明。

## 阅读过方法部分的相关工作

| 文献 | 已有内容 | 与本轮的关系 |
|---|---|---|
| [Dynamic Group Transformer](https://arxiv.org/html/2203.03937v1) | 动态分组、scatter恢复、训练架构 | 不能宣称发明语义分组attention |
| [Semantic-Aware Local-Global ViT](https://arxiv.org/html/2211.14705v1) | 语义局部与全局计算 | 局部—全局融合已知 |
| [Semantic Equitable Clustering](https://arxiv.org/html/2405.13337v3) | 平衡语义聚类 | 等容量语义组本身不新 |
| [Qwen2.5-VL](https://arxiv.org/html/2502.13923v1) | 训练过的窗口及全局视觉块 | 不能直接推出冻结Qwen改连接必然有效 |
| [InternVL1.5](https://arxiv.org/html/2404.16821v1) | 图像切块及全局缩略图 | 原生多图需保留为简单系统对照 |
| [SCLIP](https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/03178.pdf)、[NACLIP](https://arxiv.org/pdf/2404.08181)、[ResCLIP](https://arxiv.org/pdf/2411.15851) | 冻结视觉模型attention修改用于分割 | 无训练attention修改也不是空白领域 |
| [图表感知研究](https://aclanthology.org/2025.findings-emnlp.573/)、[EncQA](https://arxiv.org/html/2508.04650v1)、[ChartMuseum](https://arxiv.org/html/2505.13444v1) | 编码、读取与任务推理存在不同瓶颈 | QA、排名和attention需要分别评价 |

候选贡献限定为：真实遥测来源界定的完整图元分组、冻结模型适配、原token和位置保持，以及可重复的RCA性能/成本证据。它是待验证假设，不能用工程实现代替实验结果。
