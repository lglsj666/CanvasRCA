# RQ4.3 初稿附件：历史复核、文献启发与去重

日期：2026-10-10（America/Toronto）。关联[初稿](../RQ4_3_Source_Local_Visual_Prefill_Draft_2026-10-10.md)。本附件记录计划依据，不构成新的实验结果、文献复现或执行许可。

## 1. 阅读范围与权威顺序

本轮先读 `important_docs`，再复核最新及历史报告，然后通读 `Codex.md`，随后检索并阅读论文及本地相关模型接口。读取项目历史时区分结论、资格状态和原始数据：复核报告的设计、主要定量结果、机制结论、失败分母和局限；**没有重新打开所有逐调用轨迹、所有图像或全部 CSV 行**。初稿中的数值引用最终报告，没有重算成新实验结果。

`important_docs` 的七个顶层文件（包括 `conversation_oct_06`）已读取：

| 文档 | 对本轮的作用 |
|---|---|
| [README](../../../important_docs/README.md) | 文档导航与历史状态，不替代最新实验报告 |
| [Pure Visual Direction](../../../important_docs/CanvasRCA_Pure_Visual_Direction_2026-10-06.md) | 纯视觉诊断证据、单调用；不恢复旧混合候选 |
| [Empirical to Method](../../../important_docs/CanvasRCA_Empirical_to_Method_2026-10-05.md) | 实证应导向有效方法；约 0.60 与成本目标不是已完成结果 |
| [Empirical Literature Review](../../../important_docs/CanvasRCA_Empirical_Literature_Review_2026-10-05.md) | 机制发现需要对应干预，不能只看热图或微小增益 |
| [Counterintuitive Findings](../../../important_docs/CanvasRCA_Counterintuitive_Findings_2026-10-05.md) | 保留位置／表示敏感性及 QA 脱节；旧相关性不能证明独立 |
| [Attention Storage and Sink](../../../important_docs/CanvasRCA_Attention_Storage_and_Sink_2026-10-05.md) | 小样本聚合和储存上限；高权重不等于有害 sink |
| [conversation_oct_06](../../../important_docs/conversation_oct_06) | 放弃混合路线的动机；事实来源与创新主张的边界 |

这里实际是 README、五篇主题 Markdown 及 conversation 共七个顶层文件；不把其 artifacts 子目录的每个原始文件都宣称为本轮重新全文阅读。

另通读[Codex.md](../../../Codex.md)，复核[设计决定](../../../plans/design_decisions.md)近期与当前路线相关条目，以及 literature-review 技能的完整参考索引。约束以最新用户指令为准；旧文档中的两阶段、混合补丁、训练建议不进入本方案。

## 2. 逐实验复核与本轮决定

表中“完成”表示已有结果；不意味着方法通过采用。主报告的病例附表不逐行重复审计。跨轮数据、接口和模型条件不同，不能把 MRR 串起来当同一方法的单调提升。

| 实验及报告 | 状态与关键证据 | 本轮采用的决定 |
|---|---|---|
| [RQ1.1／RQ2.1](../../experiment_reports/RQ1_1_RQ2_1_findings/findings.md) | 已完成；混合 TPV 优于全视觉；关系视觉和分辨率有条件收益，截图没有普遍优势 | 保留真实图形；不以完整文字截图充当纯视觉创新 |
| [早期 Tournament](../../experiment_reports/Tournament_Analysis_2026-09-15.md) | 38 轮后用户停止；多方法成功并集不是单方法 MRR；跨方法成本高 | 不用事后 oracle 或反复换布局追成败 |
| [RQ3.1](../../experiment_reports/RQ3_1_Results_Analysis_2026-09-19.md) | 已完成分析；方法改动会遗漏 node／资源证据 | 不新增选择器丢事实 |
| [RQ3.2](../../experiment_reports/RQ3_2_Results_Analysis_2026-09-22.md) | 已完成；实体覆盖不等于解释到正确机制 | 几何来源闭合只作为资格 |
| [RQ3.3](../../experiment_reports/RQ3_3_Results_Analysis_2026-09-24.md) | 已完成；请求／证据组织已有实验；多次调用的联合成功不可当部署结果 | 不把来源分组本身称作新概念，不做两阶段 |
| [RQ3.4](../../experiment_reports/RQ3_4_Results_Analysis_2026-09-25.md) | 已完成；加入比较规则没有稳定推动排名 | 沿用已资格任务，不再堆诊断策略提示 |
| [RQ3.5](../../experiment_reports/RQ3_5_Screen_Analysis_2026-09-26.md) | 已完成筛查；二值联合信息与实际干预适用性已有验证 | 先看新计算实际是否改变，不用名义 arm 数充数 |
| [RQ3.6 A](../../experiment_reports/RQ3_6_Stage_A_Analysis_2026-09-26.md) | 已完成；接口组织存在明显效应，删除资源证据有害 | 仅改变明确登记的静态前置段，完整保留旧任务 |
| [RQ3.6 B](../../experiment_reports/RQ3_6_Mechanisms_Analysis_2026-09-28.md) | 已完成；局部关系视觉存在受条件限制的收益 | 不将局部成功推广为任何来源分组必然有效 |
| [RQ3.7](../../experiment_reports/RQ3_7_Results_Analysis_2026-09-28.md) | 已完成；局部组合有正向信号，数值写法能扰动首选 | 冻结数字写法，避免新的数值混杂 |
| [RQ3.7C／RQ3.8](../../experiment_reports/RQ3_7C_RQ3_8_Qwen_Analysis_2026-09-30.md) | 已完成；完整文本追加图像出现明确退化 | 不重新做附加完整图形或混合输入 |
| RQ3.9 | 未完成可用正式结果；历史路线不恢复 | 不作为负结果，也不补跑旧队列 |
| [RQ3.10](../../experiment_reports/RQ3_10_Qwen_Analysis_2026-10-01.md) | 已完成；scope／peer 比较的适用性和增益有限 | 不添加竞争根因面板来制造新臂 |
| [RQ3.11](../../experiment_reports/RQ3_11_Qwen_Analysis_2026-10-01.md) | 已完成；精确补丁和压缩未建立稳定增益 | 不恢复数值量化或精确文本安全网 |
| [RQ3.12](../../experiment_reports/RQ3_12_Qwen_Analysis_2026-10-02.md) | 已完成；参考预测的覆盖／诊断关联不足 | 不引入模型预测背景作为新诊断事实 |
| [RQ3.13](../../experiment_reports/RQ3_13_Qwen_Analysis_2026-10-02.md) | 已完成；AIOPS 与 AegisLab 方向不同，存在身份绑定问题 | 同时报告三数据集，检查名称／来源而非只总体 MRR |
| [RQ3.14](../../experiment_reports/RQ3_14_Qwen_Analysis_2026-10-02.md) | 已完成；全窗口摘要的收益强于继续加曲线 | 保留现有窗口信息，不将新曲线布局当核心方法 |
| [RQ3.15](../../experiment_reports/RQ3_15_Qwen_Analysis_2026-10-03.md) | 已完成；二维配对未胜过所有边际对照 | 不重复“联合图优于边际图”的旧假设 |
| [RQ3.16](../../experiment_reports/RQ3_16_Qwen_Analysis_2026-10-03.md) | 已完成；MARGINAL_FIVE 0.5054、去点 0.4963，点贡献未建立 | 复用历史混合强基线，不能改称纯视觉成果 |
| [RQ3.17](../../experiment_reports/RQ3_17_Qwen_Analysis_2026-10-04.md) | 已完成；组合未超原生边际；部分 CPU 审核由用户豁免，不能追记通过 | 不重做拓扑组合或换成其他颜色再测 |
| [RQ3.18](../../../RQs/RQ3_18/findings/exp_population_readout_findings.md) | 实际执行的是 11 臂总体读数版本；旧六臂已删除；候选未采用 | 不引用已删除计划当已运行结果，不重测同一读数卡 |
| [RQ3.19](../../../RQs/RQ3_19/findings/exp_visual_replacement_qa_findings.md) | 已完成；替换 ΔMRR 约 −0.045，成本略增；答案卡 QA 提升未可靠转化 RCA | 独立 QA 不给答案卡、不进 RCA，不靠它路由方法 |
| [RQ3.20](../../experiment_reports/RQ3_20_Qwen_Analysis_2026-10-06.md) | 已完成；取证接口大量失败，降成本伴随降排名；两阶段随后被用户关闭 | 不修复并恢复两阶段方案 |
| [RQ3.21](../../experiment_reports/RQ3_21_Qwen_Analysis_2026-10-06.md) | 已完成；压缩／实体组织降低成本但损害阶段比较和 MRR；位置扰动超重复噪声 | 不再把实体排版本身当新方法；将像素与语言侧顺序分开 |
| RQ3.22 | 用户明确取消并整体删除 | 不恢复代码、材料或实验 |
| [RQ4.1](../../experiment_reports/RQ4_1_Qwen_Analysis_2026-10-09.md) | 6,100 位置终态；均匀 E50 纯视觉最好，CVC 与剪枝代理不一致；显著位置敏感 | 以均匀 E50 为起点，停止代理覆盖率驱动的比例搜索 |
| [RQ4.2](../../experiment_reports/RQ4_2_Qwen_Analysis_2026-10-10.md) | 1,336 位置终态，0 基础设施未知；SEM 未胜 GEOM／NATIVE4／历史均匀 | 结束视觉编码器分组，转向确实不同的语言侧计算假设 |

RQ1.1／RQ2.1、Tournament 和 RQ4 两轮的正文读至结论及局限；RQ3 各报告复核设计、核心结果、状态、机制和限制，未重新展开每个病例附表。历史 SEARCH 的结论使用上述正式汇总及项目方向文档，不声称逐份重审全部旧 search 临时日志。

## 3. 广泛文献筛选：读到了哪里，如何使用

检索与访问日期：2026-10-10／2026-10-11 UTC。会议归属以官方会议页面／OpenReview／ACL Anthology 为准；只有预印本证据的明确标为预印本。下列迁移判断是本项目推断，不是论文对 CanvasRCA 的结论。

| 文献与一手来源 | 阅读深度与实际依据 | 本轮迁移／不采用理由 |
|---|---|---|
| [FEATHER](https://arxiv.org/html/2412.13180)；[ICCV 2025 官方](https://openaccess.thecvf.com/content/ICCV2025/html/Endo_Feather_the_Throttle_Revisiting_Visual_Token_Pruning_for_Vision-Language_Model_ICCV_2025_paper.html) | 方法、定位／OCR 实验、位置偏差与剪枝准则分析 | 支持保留均匀基线并单独测绑定；不直接将该论文剪枝算法改名为我们的新方法 |
| [SoFA](https://arxiv.org/html/2503.13792)；[CVPR 2025 PDF](https://openaccess.thecvf.com/content/CVPR2025/papers/Tian_Identifying_and_Mitigating_Position_Bias_of_Multi-image_Vision-Language_Models_CVPR_2025_paper.pdf) | 方法、训练分布偏移、主要实验；核对官方代码仓库 | 最近邻思路；保留一个明确注明差异的单图适配。原工作是多图 mask 混合且有验证集选参数，我们不是其原样复现 |
| [Gated Delta Networks](https://arxiv.org/html/2412.06464)；[ICLR 2025](https://openreview.net/forum?id=r8H7xhYPwz)；[官方仓库](https://github.com/NVlabs/GatedDeltaNet) | 更新规则、chunk 计算、检索实验、官方 README／FAQ | 用于理解本地骨干与实现可行性；原论文训练结果不支持直接承诺冻结模型局部反向扫描提分 |
| [Ask Twice, Look Twice](https://arxiv.org/html/2607.15565) | 2026 预印本；方法、位置消融、模型／任务差异及限制 | 只试静态任务前置。原工作不同顺序并非普遍增益；不复制图片、不附加病例事实 |
| [The Dual Mechanisms of Spatial Variable Binding](https://spatial.baulab.info/) | 2026 预印本；作者项目页的实验、探针与 interchange 干预说明，未声称通读全部 PDF | 提醒我们视觉信息会分布到背景；几何归属不等于特征的独占因果支持。其增强调用已学习探针，不能当无学习免费插件 |
| [On the Perception Bottleneck of VLMs for Chart Understanding](https://aclanthology.org/2025.findings-emnlp.573/) | Findings EMNLP 2025；本轮复核官方摘要与元数据，项目原有参考文献 | 编码与提取瓶颈需区分；它的训练改进不是本轮方案；QA 与 RCA 分开评价 |
| [When Do We Not Need Larger Vision Models?](https://arxiv.org/html/2403.13043)；[S² 官方代码](https://github.com/bfshi/scaling_on_scales) | 方法及多模态实现设定；不把冻结视觉塔误解为整个 VLM 无训练 | 多尺度是可借鉴的另一条线，但其 VLM 对接涉及 projector／LoRA 训练；本轮不偷偷加通道或假设成本免费 |
| [ApET](https://arxiv.org/html/2602.19870) | 2026 预印本；特征重构选择／聚合方法及评估设定 | 特征重构误差不是诊断充分性；避免再增加一个只有代理分数较好的通用剪枝臂 |
| [Attention Calibration](https://arxiv.org/html/2502.01969) | 预印本当前版本；UAC、DAC 方法与实验设定 | 空白校准值得留档，但部分路径需要学习；不把标题高 attention 当成应删除的 token |
| [SinkRec](https://arxiv.org/html/2606.09888) | 2026 推荐系统预印本；仅摘要筛选 | 提供递归记忆研究的跨领域线索，未将其训练方案纳入本轮，也不将“semantic sink”作为本模型已确诊问题 |
| [Visual Contrastive Decoding](https://openaccess.thecvf.com/content/CVPR2024/html/Leng_Mitigating_Object_Hallucinations_in_Large_Vision-Language_Models_through_Visual_Contrastive_CVPR_2024_paper.html) | CVPR 2024；官方摘要／方法概要筛选 | 原图／扰动图双分支会增加计算，且对象幻觉不等于 RCA；目前不满足低成本优先级 |
| [CRISP](https://www.usenix.org/conference/atc22/presentation/zhang-zhizhou)；[PDF](https://www.usenix.org/system/files/atc22-zhang-zhizhou.pdf) | USENIX ATC 2022；摘要及时钟偏差相关章节复核 | 计算顺序与真实时间必须分开，不通过跨主机时间推断新关键路径 |
| [RCAEval](https://arxiv.org/html/2412.17015) | WWW Companion 2025；摘要、数据与评估问题复核 | 保持多数据集／故障类型及完整分母；本地子集结果不直接等于战胜全部 RCA SOTA |

没有因“不是 RCA 论文”就排除启发；也没有因一篇论文在视觉问答有效，就认为它必然对根因排序有效。本轮真正进入方法设计的是一项新的递归局部补充假设、一项低成本提示安排，以及一个最近邻 attention 适配控制，其余用于约束错误迁移。

### 代码可用性核对

- [SoFA 官方仓库](https://github.com/xytian1008/sofa)本次打开仅见 README 待发布说明，没有可运行算法代码。初稿不承诺原样复现。
- GatedDeltaNet 官方 README 提供训练实现并指向优化的变长内核；这不等于本地冻结 Qwen 的生成接口已经适配。未来优先复用已安装运行栈，不能运行时依赖外部 RCA 仓库。
- 本地 `RQs/RQ4_1/src/exps.py` 的任务文本、`gates.py` 的消息顺序和 `utils.py` 的 embedding 注入／排名解码路径已只读核对。历史代码只作为接口证据，后继不会修改其源。
- 本地模型 config 核对的是 64 个语言块（48 递归＋16 完整 attention）和 27 个视觉块。不能把仓库名称“Qwen3.8”当作与论文架构完全相同的保证。

## 4. 与历史及本轮内部的去重清单

| 提案 | 最近历史条件 | 真正新增的干预 | 为什么不是换名重跑 |
|---|---|---|---|
| U_ECHO | RQ4.1 U；更早文本接口实验 | 同一静态任务段前置，诊断信息仍全在原图 | 任务顺序在当前递归骨干、纯视觉及原 token mask 下尚未单独测试 |
| U_LOCAL_BI | RQ4.1 U；RQ4.2 SEM | 修改语言递归层输出，保留全局路径和原图片／mask | SEM 改的是视觉编码器分组；不是这条计算路径 |
| U_LOCAL_BI_ECHO | 前两项 | 预先固定的组合 | 检验工程完整方法及交互，不把相加收益默认称协同 |
| U_LOCAL_FORWARD | BI | 去掉反向补充 | 区分局部重新上下文化与未来视觉位置可见性 |
| U_SHAM_BI | BI；历史 SHAM | 语言局部分支错误来源，同组长度相同 | 干预位置不同；历史视觉编码器 SHAM 不能回答它 |
| U_SOFT_IMAGE | SoFA 近邻思想 | 语言第一个 full-attention 层内的单图软混合 | 排除简单 attention 适配已足够的解释；明确非原论文复现 |
| 语言侧顺序机制 | RQ3.21／RQ4.1 位置扰动 | 不改像素、视觉特征、mask 或空间坐标，只改串行顺序 | 分离此前混杂的图像重编码／token 选择 |

如果完整生成身份实际相同，仍必须引用，不因列在此表就一定新调用。历史基线失败结果按原协议保留；不能以复用为名挑掉非法输出，不能削弱文本对照制造视觉收益。

## 5. 尚待评审的关键问题

1. 冻结 GDN 的局部零初态与反向分支是否会严重偏离训练分布？λ=0.25 和前三层是工程提案，不是已验证答案。
2. RQ4.1 原图存在处理后部分文字较小的上游风险，新路径无法恢复未编码的信息；保持原图换来了对照清晰，也限制潜在收益。
3. 真实来源的唯一支持能覆盖多少保留 token？不能重犯共享 token 被强制独占的错误。
4. 增量计算和真实部署耗时能否控制在约 5% 范围？必须测，不以 FLOPs 或 token 替代。
5. 与已有双向／局部递归、视觉 prefix 方法的差别是否足以支撑方法贡献？当前仅是候选，尚未完成新的独立盲审。
6. 即便胜过当前纯视觉，能否逼近并超过 0.4846 强文本？如果没有，必须承认主目标尚未完成。

这些问题用于下一次评审／可行性决策；本轮未用新调用来筛答案，也没有把初稿当作已经定稿的研究结论。
