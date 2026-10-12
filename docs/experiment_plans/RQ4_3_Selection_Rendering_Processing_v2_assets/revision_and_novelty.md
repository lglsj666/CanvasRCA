# RQ4.3 v2：实质改动、历史去重及新增文献

关联[当前计划](../RQ4_3_Selection_Rendering_Processing_Plan_v2_2026-10-10.md)。状态：仅计划修订，无新模型调用。原有[历史报告与文献复核](../RQ4_3_Source_Local_Visual_Prefill_Draft_2026-10-10_assets/review.md)继续保留；其中六臂、1,700 调用及仅处理路径的建议已由 v2 替代。

## 1. 用户本轮决定及实际变更

- 三个方向各三个优化条件；其他条件承担控制、组合及反直觉测量。
- 最初按约5,000制定；用户同日允许提高到8,000。随后自查归因对照，新增两控制及其QA，当前具体分配5,360，尚有2,640未分配；九个优化条件和预选组合不变。
- 过去弱效方法先放下；只有针对原失败作了实质改动，才考虑再测试。
- 本轮仍在修订计划，不实施、不启动CPU或GPU、不改Codex。

因而删去原初稿的 ECHO 和 BI＋ECHO 候选；保留 BI 核心，原 SOFT_IMAGE 从控制转为第二个处理候选，再固定其组合 P_DUAL。前一轮没有发生调用，不存在丢弃负结果后改矩阵。

预算授权本身未改变矩阵；随后在用户追问下补做的主代理自查发现两个具体缺口，因此本次补充登记，并非独立盲审结论。主要比较及预选候选不变；归因族由九项增为十一项。调用数能覆盖矩阵不代表220例已具有足够统计功效；详见计划§7.1。

### 1.1 两个新增对照的缺口与预算

| 新条件 | 现有条件为什么不能替代 | 本次登记的差别 | 新调用 |
|---|---|---|---:|
| C_PACK_BG_FILL | 位置偏移会改变特征与锚点支持；读图说明控制也不能检验释放名额的用途 | 保持PATCH_PACK的PNG、总保留数量与锚点，将新释放的名额分给真实背景位置；与观测名额分配比较 | 220 RCA＋60 QA |
| C_GLOBAL_BI | 单向控制删除反向分支，SHAM保留错误的多组边界；SOFT_IMAGE使用另一种算子 | 与LOCAL_BI相同GDN层、合格token和融合公式，仅取消来源分组边界，做一个组的双向扫描 | 220 RCA＋60 QA |

合计增加560次，明确分配从4,800变为5,360。两种控制均先做实际差异与可行性资格；背景token不是语义零向量，全局双向也不保证与多组扫描同样快，计划明确限制归因。它们用于判断新方法的原因，不取代U和T_FULL作为主要性能基线。

独立病例验证是增加数据范围，不是再发明一个算法arm；它仍须先完成身份／曝光审计及冻结比较。剩余2,640次没有提前分给未经审核的新病例，也没有自动变成额外smoke。

## 2. 为什么这些不是原样重跑

| 新方向 | 最近历史及已知不足 | 本版实质改变 | 仍不能声称什么 |
|---|---|---|---|
| S_DISTINGUISH | 旧 competitor／peer／scope 条件；单独异常排名与资源遗漏 | 从完整公共 pool 选择同口径双方来源包；公共差异目标、双方闭合、实体／模态保护和几何成本同时登记 | “比较竞争根因”本身不是新发现；观测可区分不等于因果可识别 |
| S_REPRESENT | SEARCH37 形状多样性；RQ4.1 A_DIVERSITY 低于均匀 | 旧方法是按原始排名奖励并惩罚同 owner 高相关序列；本版是跨 M/R/L 完整包的总体代表性目标、类型／单位兼容和少数模式保护 | facility location 本身不是创新；统计代表性不保证根因证据代表性 |
| S_JOINT | 旧 additive／round-robin 有覆盖但容易挤掉有效来源 | 固定联合双方区分与完整池代表性，整包成本，不做逐单项异常截取 | 不承诺必胜，也不把等权相加称新理论 |
| R_PATCH_PACK | E50 锚点占保留 token 86%–90%；旧布局优化没有针对该瓶颈 | 优化真实 resize／patch／merger 后锚点 token 并集，字号和源事实不变，释放槽位给观测；另设相位偏移控制 | 不是泛称“更紧凑”“标签靠近”，也不以锚点减少替代读取验证 |
| R_HORIZON | 旧 line／heatmap／quantile atlas；增加摘要和面板未普遍提分 | 原始指标序列采用两层数值带折叠及颜色编码；不添加 peer residual、异常统计或额外面板 | 不是首次发明 horizon graph；人类实验不证明 VLM 有收益 |
| R_PACK_HORIZON | 没有把旧 atlas 或 shared-axis 换名 | 固定两种新实现的组合，不再调更多带数／颜色 | 组合高于其中一项，不自动等于协同 |
| P 三条件 | RQ4.2 改视觉编码器；结果未超过空间分组 | 改的是语言骨干的局部递归／图内 full-attention 及二者组合，同图同token | 双向处理已有文献；新意须落在来源适配、可靠实现和结果 |

本轮补读的本地去重证据：

- [旧选择目录](../../../RQs/RQ3/configs/selection_only_suite_v1.yaml)及[后继目录](../../../RQs/RQ3/configs/selection_only_suite_v5.yaml)。
- [旧形状选择配置](../../../RQs/RQ3/configs/search_shape_diversity_v1.yaml)、[实际选择函数](../../../RQs/RQ3/src/renderer/kpi_select.py)。
- [旧选择实现](../../../RQs/RQ3/src/exps.py)，包含 candidate-round-robin、family portfolio 与配对选择。
- [RQ4.1 登记](../../../RQs/RQ4_1/descriptions/RQ4_1_experiments.md)及[最终报告](../../experiment_reports/RQ4_1_Qwen_Analysis_2026-10-09.md)，包括共享支持、CVC／UNARY／A_DIVERSITY、CONTRAST_ATLAS 与锚点占用。
- [当前组件库](../../../src/renderer/configs/components.json)及[操作库](../../../src/renderer/configs/operations.json)。库中已有 heatmap、quantile contrast、line、paired bars 等，不能再把这些名字当新画法；尚未见 horizon 组件。

上表不是仅凭命名认定九臂都值得跑。最终还要看实际输入和计算差异；接近旧条件或近似彼此的条件取消。特别是 S 的保护集合可能已经消耗多数来源预算，此时新目标可能没有实质作用，必须在 CPU 时报告，而不是等做完LLM调用才解释。

## 3. 新增文献记录

### 3.1 图形空间与数值带编码

- **Title / authors:** *Sizing the Horizon: The Effects of Chart Size and Layering on the Graphical Perception of Time Series Visualizations*；Jeffrey Heer、Nicholas Kong、Maneesh Agrawala。
- **Status:** CHI 2009，DOI `10.1145/1518701.1518897`；[作者实验室页](https://idl.uw.edu/papers/horizon)、[完整论文](https://hci.stanford.edu/publications/2009/heer-horizon-chi09.pdf)。本轮核对方法、两项实验、主要结果、设计建议和限制；访问2026-10-11 UTC。
- **Evidence:** 人类数值比较，研究 chart height 与 band count 的速度／误差权衡；叠层并非在所有尺寸下更好。原文也限制到值比较任务，不能推广为全部趋势或诊断任务。
- **Transfer:** R_HORIZON 固定两层，单独检验 VLM 读取和 RCA；不沿用人类的像素最佳点，不做层数搜索。未核验可直接复用的官方实现，后继需统一 renderer 的显式新增组件。

### 3.2 预算内代表性与非冗余选择

- **Title / authors:** *A Class of Submodular Functions for Document Summarization*；Hui Lin、Jeff Bilmes。
- **Status:** ACL 2011，[正式条目](https://aclanthology.org/P11-1052/)、[论文](https://aclanthology.org/P11-1052.pdf)。本轮阅读目标函数、facility-location 对照、实验设置／结果和讨论；访问2026-10-11 UTC。
- **Evidence:** 在文档摘要中组织覆盖与多样性目标；论文部分参数用开发集优化。其 ROUGE 结果不能作为 RCA 收益依据。
- **Transfer:** 借用完整集合代表性目标，不复现其摘要系统、不使用根因标签调参，也不套用不适合双方闭合选择的次模保证。S_REPRESENT 为已知数学工具的领域适配；新的诊断价值需要与固定哈希选择及 U 比较。

### 3.3 筛除而未依赖的检索结果

Cleveland／McGill 的共同尺度感知论文已检索到出版商条目，但本次打开失败。没有据此声称完成全文阅读；普通共同轴排版已从 v2 三个绘图臂撤下。先前的 SoFA、GatedDeltaNet、FEATHER、空间绑定、S² 等记录仍见原阅读附件，未将论文对其他任务的结果改写为本项目证据。

## 4. 主张与证据的对应

| 主张 | 当前依据 | 现阶段能说到哪里 |
|---|---|---|
| 锚点占用是值得干预的工程瓶颈 | RQ4.1 报告 §8 的实际数量 | 有测量；减少占用是否提高 MRR 未知 |
| 新布局可能释放可用于图元的槽位 | 真实processor网格＋拟议编译算法 | 待CPU证明，不是已实现节省 |
| 来源包选择可能比异常Top-k更好 | 历史资源损失＋新的选择目标 | 假设；必须防止删掉真正根因证据 |
| 分层色带可能提高单位画布的信息利用 | CHI编码研究 | 跨任务迁移假设；颜色／层数可能增加读取错误 |
| 内部双向补充可能改善绑定 | 旧稿文献与本地模型结构 | 未验证适配；不承诺保持推理速度 |
| 三方向可能互补 | 固定2×2×2组合设计 | 待测；不能加总单项MRR或用事后赢家代替组合 |

更新后的候选贡献与资源分配均属开发计划。没有把未通过的方法抹去，也没有把一轮扩大矩阵宣称为项目已经接近完成。
