# RQ3.12 预注册：候选条件化残差画布

日期：2026-10-01。版本 `rq312_conditional_residual_v1`，实验 `exp_conditional_residual`。
初次授权只包括计划、代码部署与静态检查，该阶段已完成。**2026-10-01 用户随后授权 CPU 回归、GPU smoke，并在全部注册资格通过后启动全量实验。以下命令已成为本次授权的执行入口；实际完成状态以 qualification 和 findings 为准。** 这项授权不降低下列适用性、成本、预算或完整性门槛。

## 1. 为什么选择这一轮

决策依据是原始协议范围内的完整开发结果，不能合并不同 RQ 的分数作新检验。

| 依据 | 已验证的结果 | 对下一轮的约束 |
|---|---|---|
| [RQ3.7C/RQ3.8](../../../docs/experiment_reports/RQ3_7C_RQ3_8_Qwen_Analysis_2026-09-30.md) | RQ3.7C eval 相对强文本 n=295、macro ΔMRR +0.0566、Holm p=.1712、dz=.1341；已暴露 test n=357、+.0490、病例 p=.0532、组级 p=.0420。相对分离面板的 test 增量仅+.0032 | 数值与关系联合有条件性支持，但没有锁定局部连线机制；不能继续只换布局 |
| 同一报告 RQ3.8 C | 全图叠加相对同事实文本已暴露 test n=342、macro Δ−.0771、Holm p=.00112、组级 p=.000679，输入增加约80.5% | 不重复完整原始 dashboard；限制新增比较对象与实际成本 |
| [RQ3.10](../../../docs/experiment_reports/RQ3_10_Qwen_Analysis_2026-10-01.md) | MATRIX−BASE AIOPS Δ+.0181、Holm p=.8626；成本+75.1%。有效稳定冲突对照仅AIOPS22 23例，AIOPS25 0例，Aegis0例 | 不再假定普遍存在活跃健康 peer，也不把 node→全部 pod 写成必然故障规则 |
| [RQ3.11](../../../docs/experiment_reports/RQ3_11_Qwen_Analysis_2026-10-01.md) | PVH−ET n=120、Δ+.004861、Holm p=1、dz=.014612、总token+3.103%；PVH−PTH n=119、Δ−.000700、p=1；全部3360签名保持；手工式审核12独立案例仍有单位、时序、绑定、归因错误 | 数值保护不是诊断决策保护。停止补丁/分辨率扩量，保留其无损强文本和审计能力 |
| [conversation_oct_01.md](../../../conversation_oct_01.md) | 建议“实际性能收益＋可分离视觉价值＋可复用方法”；首先比较候选解释预测与观测的分歧，并与强文本、数值求解比较 | 将难题定义为公开可检查的预测比较，避免仅以新画布名称声称创新 |

RQ3.11 原归档 SHA256 `8cd66de375ff4f2cede5474d95bd8aedb6acf8cfac20d2fb9d27993d4f77fb7b`；RQ3.10 原归档 `5f417056831fcc8c1b32116590ee81cf4a11debc8ce432cdfe3ce6d241117548`。上述报告保留原 scorer、配方、已暴露分区与失败分母；本轮不修改它们。

## 2. 方法及其科学边界

固定现有公开证据：既有12条64-bin M、缺失、单位、M汇总、R/L/G、数值候选与顺序、system与一次求解规则。基线直接使用RQ3.11无损值/位置编码，保留原数值字符串。所有臂同一基础证据；隔离资源信号不因没有peer/trace/log而丢掉。

每条指标以既有 trace-derived 相对 split 划分参考/当前区间。跨界bin不归任一阶段，不插值、不推定缺失=0。不读注入时间。参考期并不经根因标签认证为健康。

先计算参考中位数、MAD和当前中位数，尺度 `max(1.4826*MAD, .01*abs(reference_median))`；尺度为0、覆盖不足或缺失时为未知。规范变化A以该尺度归一化。所有原始单位和精确值仍在文本，派生值只按预先固定4位有效数字显示，状态按未舍入值计算。

对于任意两条不同的已选M，参考期同步有效样本至少12、覆盖至少60%，以时间顺序中点分成两个块，每块至少6点。标准化一元ridge含截距、惩罚 .1；第一块训练第二块评估，再交换。两次预测RMSE相对训练期均值预测均须≤.8，常量/退化回归拒绝。接受、拟合和锚点选择仅使用参考期，不利用当前异常调整系数/超参。

每个数值候选h的条件锚点：直接属于该实体的M；service也可包含有唯一公开has_instance/owns绑定的pod M。node不会把其宿主全部pod观测自动当锚点，歧义实例所有者不推断。没有锚点的候选不生成比较行，但仍在完整原候选列表中。被条件化的锚点自身记 `/conditioned`，不能以零残差算“已解释”。

对非锚点目标，从h的锚点中选参考CV最优的一个；不能看到当前响应后择优。当前同步有效样本至少3、覆盖60%，所有锚点值须位于参考[min,max]向两边各扩展1个参考标准差的范围，否则预测未知。当前预测是同步预测值的中位数，实际值也用同一同步bin集；A/E均以目标参考尺度表示。R=(同步实际中位数−预测中位数)/max(参考held-out RMSE,目标参考尺度)，S为该误差尺度/参考尺度。

区分 `compatible/mismatch/unexplained/over_predicted` 与 `unknown/conditioned`：3是注册变化/残差阈值。`over_predicted`表示当前观测|A|<3而|E|≥3，`unexplained`表示|A|≥3且|R|≥3。它们是依赖模型的比较状态，**不是反证候选根因或已识别传播方向**。

候选比较优先选择公开预测分歧：同一目标且同步bin相同，至少2个共同有效预测目标，以平均 `|E_h−E_k|/max(S_h,S_k,1)` 衡量差异。先选最大分歧候选对，保留可用node/pod/service类型的各一个probe，再逐步选择距已选集合最远的候选，最多6行。没有可用分歧时按固定公开hash填充，显示未知。所有12目标列与全部基础证据仍保留；此版没有压缩共享观测或选择新原始遥测。

可复用算法对象是参考依赖、候选条件预测、观测冲突及候选分歧编译。**它不保证观测依赖能外推成故障响应，不能称CIRCA/Sage复现、因果DAG、严格反事实或似然。** 不独立假设多个高度相关模态后求和。

## 3. 六臂、对照与假设

| 臂 | 信息与表示 | 用途 |
|---|---|---|
| EXACT_TEXT / ET | 完整原事实，无损紧凑M向量 | 强实际基线；字节输入可与RQ3.11核对，但本轮独立发起 |
| EXACT_REPEAT / ER | ET的完全相同输入、配方与seed；独立真实请求，不去重 | 同期重复性，不能择优 |
| OBS_TEXT / OT | ET＋公开规范变化及紧凑观测表 | 普通异常计算文本控制 |
| OBS_VISUAL / OV | OT的同一观测表移至一张真实图形PNG，其余文本相同 | 普通异常表示控制 |
| COND_TEXT / CT | ET＋观测表、条件预测、残差与模型可用性，紧凑字段数组 | 条件预测的强等信息文本 |
| COND_VISUAL / CV | CT的同一矩阵移至一张PNG，公共绑定/来源/bin/单位留文本 | **预选推荐候选**，不得事后改选其他臂 |

OT/OV与CT/CV分别做精确语义round-trip；矩阵值、顺序、空值、状态、锚点与全部背景事实均一致。CT/CV与OT/OV的差异是注册诊断计算信息，不能将这种比较叫等信息模态效应。视觉不是全文本＋整个原运维图：只传输新增派生比较矩阵；原始曲线仍精确文本。固定解码语法在图像前，事件事实严格按图像A＋原文本B传输；没有hybrid专属的RCA策略。

文本控制用固定字段顺序的紧凑typed arrays，不用刻意冗长描述。图形为统一renderer新增 `diagnostic.matrix`：12指标列、观测行与最多6候选行，1360×1120固定画布。每格保留A/E/R/S精确显示字符串和状态；signed bar固定−6..6，越界箭头与原显示值并存。不存在虚构时间轴。模型预测与观测、未知和条件锚点明确不同。候选、实体、路径、单位和相对时间不依图形改写。

主要族（AIOPS120，双侧Pratt Wilcoxon，差值round12，Holm一起校正）：

1. CV−CT：是否有可分离视觉价值？
2. CV−OV：候选条件预测是否优于普通异常图？
3. CV−ET：最终部署是否有实际收益？

次要族：CT−OT（非视觉诊断计算）、OV−OT（普通表示）、ER−ET（真实重复）。病例与事件组等权敏感性同族校正，paired Cohen dz；无置信区间。病例、数据集、故障、根因粒度与可用性层均保留；小层与事后划分属于探索。

额外CPU数值对照不使用VLM：同一规范测量/条件矩阵与typed实例绑定，在所有被显示候选共同有效的目标上按平均绝对残差排序，至少两个候选和两个共同目标才适用；不适用及未probe候选用公开自身异常强度、固定hash并列顺序补全。每个病例均保留applicable/fallback和原scorer分数，不能只展示适用子集。它不解释全部R/L/G，也不是所有数值RCA方法的最强上界；其比较为预注册描述性证据，不能单凭胜过此启发式声称优于CIRCA。若数值方法复现收益，不能把方法复杂度或VLM价值说成必要。

## 4. 数据、预算、成功与停止边界

沿用 `RQs/RQ3_10/results/scope_v1/registration.json` 的完整140 eval：AIOPS22 60、AIOPS25 60、Aegis20，源文件SHA冻结于config。两AIOPS为主要范围，Aegis辅助探索；完全保留事件组。使用旧三primary-dataset eval smoke病例，不用test或方便的CPU子集替代正式队列。

先做整批公开CPU可行性，**不是模型推理选择**：至少30/120 AIOPS案例有≥2共同有效目标且分歧≥.5的候选对，每个AIOPS至少10例；CV相对ET的AIOPS总input平均比≤1.20；全部140×6完整输入须input+8192≤40960。任一失败：写失败报告，停止GPU，保持140例和门槛；新响应定义需新协议。未适用病例仍是本轮潜在正式队列，不能静默剔除。

仅采用CV。开发阶段的性能/视觉/成本目标是：CV−ET至少+.03 MRR、CV−CT至少+.02，两者及CV−OV的主要族Holm p<.05，组级敏感性也通过，CV−OV方向正；部署对比各AIOPS方向均正；所有主要比较完整覆盖120；配对input+output总token比≤1.20。输入预检不是最终成本收益。达成也仅是开发证据；解释审核和CPU数值比较未完成前不推荐部署。这些阶段目标不替代原项目最终MRR目标与后续独立评估要求。没有以“无显著差异”证明非劣性的路线。

本轮formal 140×6=840位置，882次发起上限（含42修复保留，无自动重试），smoke最多18次/600秒，合计900。该上限是继承major-RQ 40000 ceiling中的新分配，**不得重置任何已花费调用**；GPU前必须有当前major ledger审核，已花费+900≤40000。旧RQ3.10消耗767、RQ3.11消耗1121保留，它们不是全major累计计数。ledger_evidence须是具体file、sha256、kind和initiated列表，sqlite读calls总行数，历史json_counter按keys读取保存的消耗整数；避免重复路径，核对合计等于verified_major_spent。审核者负责major范围完整且不混入归档复制或忽略已删除历史计数。当前只登记未来上限，授权并不包括执行。

恰好同输入可以合法引用完成调用，ER永远独立；不因错误答案重试。模型非法JSON、重复ID、未知ID、截断保留原score（失败为0）；infra超时未知，usage为空时不制造成本。完整队列结束后再统计，writers drain后审核。没有对部分结果调参或从LOW/HIGH继续选赢家。

## 5. 解释可信度及审查

保持原services/reason/confidence JSON，confidence为类别而非校准概率。统计高置信错排、非法ID/重复/截断、类型冲突与证明性措辞只作screen，不能称全量幻觉率。全量response均保存。

预先按公开case hash每数据集选12例，共36例，不按得分变化抽样；六臂完整解释均审核，包括缺失位置，不另找有利替代。审核数值/单位、时序、实例与callee绑定、预测是否伪装成观测、无依据因果断言，记录具体claim、可见证据位置和unknown。排序正确性与解释错误分开报告；36例仍不是全量真值、独立多评审数据或模型隐藏推理。`analyze`只生成pending审核表，绝不自动裁定“可信度提升”。

## 6. 部署、静态检查与未来运行

源码遵循五模块＋package marker：utils（注册/身份/局部recipe）、exps（纯公开预测/矩阵编译）、main（持久化调用/流程）、tests（未来CPU资格）、gates（静态/资格/统计/完整性）。共有新source低于7500行；一份shell trigger低于800行。项目根目录仍只三科学配置＋既有local projection。新renderer只添加独立component/DTO，不覆盖旧组件；原冻结实验继续以其归档为准。

本次唯一执行入口：

```bash
bash RQs/RQ3_12/scripts/local.sh static
```

AST/compile不执行被解析源码，JSON配置/矩阵预算与外部导出接口检查、bash -n、TypeScript noEmit、公开DTO字段级审查、路径/模块限制。无case编译、CPU单测、tokenizer/processor、renderer build、浏览器、PNG或GPU运行。静态成功不传递为任何runtime资格。

未来重新获运行授权后（此处未执行）：

```bash
bash RQs/RQ3_12/scripts/local.sh build-renderer --execute
bash RQs/RQ3_12/scripts/local.sh static
bash RQs/RQ3_12/scripts/local.sh register
bash RQs/RQ3_12/scripts/local.sh prepare --execute
bash RQs/RQ3_12/scripts/local.sh cpu --execute
bash RQs/RQ3_12/scripts/local.sh cpu --smoke --execute
```

build只构建bundle并保存renderer/source/bundle身份receipt；随后static刷新bundle hash。所有图像在GPU前完整预渲染。CPU仅8个distinct physical-core workers，source/cloudbed轮转优先；模型36并发、全局8writers。tools为CPU编译与渲染，infer为实际processor预检与vLLM，CUDA在CPU脚本禁用。

未来primary agent具体审阅后，将JSON审核保存到本RQ results/qualification，使用 `accept-review --review-kind visual|scientific|budget --review-file <project-relative-json> --execute` 接受。每份含status=passed、reviewer、当前source_contract；visual还需inspected_pngs和deterministic_rerender，scientific需prediction_limitations_reviewed；budget需major_ceiling=40000、verified_major_spent、ledger_evidence。不能从静态结果生成这些通过标记。

```bash
bash RQs/RQ3_12/scripts/local.sh freeze --execute
bash RQs/RQ3_12/scripts/local.sh supervise --smoke --execute
bash RQs/RQ3_12/scripts/local.sh review-smoke --execute
```

审阅真实smoke输入、图像、完整输出及commit后，另一份smoke review含actual_inputs_outputs_reviewed=true，再经accept-review记录；运行只对当前source和完整140例CPU成功、预测适用性、token成本、renderer/学术/major预算/source freeze通过放行。smoke的600秒包括启动和持久化，逻辑clock跨restart不能重置，正确率不是smoke gate。

最后未来显式启动 `supervise --execute` 普通后台进程；完成整批后 `analyze --execute`。owned server退出时自动关闭。无Slurm、远端fallback、训练、attention、自动后继。`completed/<callkey>.json`是原子单位边界，`phase_complete.qwen3.8-27b.json`是阶段边界；resume先信任phase marker，再读取小flag，完成单位不加载上下文、不重哈希完整graph。最终完整性audit离线进行，不移到resume。

## 7. 文献核查与claim ledger

问题：参考条件依赖与候选残差比较是否已有先例？哪些假设可移植，哪些视觉/成本声明必须本项目实验支持？2026-10-01检索，优先2025–2026，纳入直接提供相关条件预测/干预定义的早期基础工作。仅采用论文正文、作者发布与官方代码；搜索式包括“CIRCA conditional distribution intervention recognition”“Sage microservices performance debugging”。排除同名自动驾驶SAGE、聚合摘要、不能核查实验的2026名录。没有声称系统性文献穷尽或创新性已获证明。

| 来源（正文及代码核查） | 直接支持 | 本轮推断及禁止外推 |
|---|---|---|
| Mingjie Li等，Causal Inference-Based Root Cause Analysis for Online Service Systems with Intervention Recognition，KDD2022，arXiv v1 2022-06-13，DOI10.1145/3534678.3539041：[正文](https://arxiv.org/html/2206.05871)、[官方代码](https://github.com/NetManAIOps/CIRCA) | §3条件分布变化的干预判据依赖CBN/DAG/Markov/faithfulness；§4含structural graph、回归检验、descendant adjustment；§5含仿真与99个Oracle故障，Table3 CIRCA AC1 .404 vs NSigma .323；§5.4及结论讨论假设/模型边界。代码分graph/scorer、RHT及ANM接口 | 参考关系预测可以产生可审核比较对象是本项目推断。这里只有经验关联和参考block-CV，不能搬用其因果定理、预测论文同等收益或称完整复现；样本和score不可比 |
| Yu Gan、Mingyu Liang、Sundar Dev、David Lo、Christina Delimitrou，Sage: Practical & Scalable ML-Driven Performance Debugging in Microservices，ASPLOS2021：[作者正文](https://people.csail.mit.edu/delimitrou/papers/2021.asplos.sage.pdf)、[作者研究页](https://people.csail.mit.edu/delimitrou/Research.html) | 正文abstract/introduction、§3/4方法、§5/6实验与§7讨论：RPC依赖CBN＋GVAE构造假设情景；受控微服务实验及部署恢复，与autoscaling/既有debugging比较；处理图/训练更新的限制 | 预测/假设诊断不是视觉专有或新概念。此版不训练GVAE、不操控资源或验证干预；其系统收益不能证明CanvasRCA视觉收益。官方实现仓库未在此次核查中独立确认，不标“已复现” |

已阅读与核查位置涵盖摘要、引言、方法、设置、主结果、消融/讨论和结论，CIRCA README接口。移植仅是自研受限参考预测器，无外部源码vendor、额外依赖安装或论文结果合并。

Claim分类：①参考条件变化/假设预测已有研究依据（直接证据）；②同候选的差异表可能减少症状显著性误导（CanvasRCA推断）；③图形优于等信息文本、成本可控、输出更可信（本轮必须测量，当前无证据）；④“任意node故障影响全部pod”“低残差就是根因”“模型预测是观测真值”不成立，已在代码/grammar显式禁止。

## DD-RQ312-CONDITIONAL：采用参考依赖的候选比较，不重复压缩搜索

**状态：adopted for static deployment；runtime和研究效力pending。日期2026-10-01。**

Context：用户要求结合历史、当前结果和conversation选择下一实验并部署，只做静态检查后停。RQ3.11有限保护成功却没有视觉/成本收益；RQ3.10健康peer覆盖不足；RQ3.8整图负向；单一新布局不足以建立贡献。

Decision：固定核心证据，加入低自由度、参考CV验收的候选预测与误差；按候选分歧编译bounded比较，六臂和数值对照分解价值，预选CV、成本与适用性GPU前把关。参考期关联模型是科学范围限定，不是已经成立的故障响应模型。

Evidence：见§1完整报告、范围与归档；非独立eval开发，负结果不等于普遍视觉无效。文献§7只支持定义与边界，不证明本方法性能。

Alternatives rejected：继续保护算子/分辨率网格（没有新机制依据）；重新拼接大图（RQ3.8负证据）；单纯service×node scope（RQ3.10稀缺对照）；完整学习式反事实世界模型/多轮LLM（额外假设、成本和训练权限不匹配）。本轮未排除未来更充分的响应模型；若reference预测不适用，保留失败CPU证据再登记修订。

Consequences：维护equal-fact twins、私有边界、原score和数据角色；必须未来真实CPU/PNG及学术审查才可smoke；初版不保证覆盖网络/代码/多根因，不删这些case，不宣称新test或独立因果/信任验证。本次在静态检查后停止。
