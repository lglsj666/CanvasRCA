# RQ3.6 三个候选问题的第二次历史核对

日期：2026-09-27。性质：历史源码、注册协议、完成报告与已有配对汇总的审计；没有运行新推理、CPU回归或smoke。旧B队列已暂停，正式0调用，18次资格结果保留。三个新v2配置是不可执行草案，不是完成注册或通过资格的实验。

## 结论先行

三个问题都不能整体称为首次研究。第一、第三已有相关干预，第二已有较充分的现象和局部机制证据。真正缺口是特定组成及其交互，而不是重新确认“G有时有用”“补宿主有利有弊”“绑定有时有用”。上一轮提出的三组各12条件、12960单元只是一版草案，需按本核对修改后再冻结，不能为满足调用数量保留重复比较。

本次除用户列出的RQ1.1/RQ3.1–3.6，还补查RQ2.1、Tournament以及容易遗漏的旧RQ3 SEARCH开发探索。没有找到独立的 `RQ1_2` 目录或名为RQ1.2的报告/协议；不将不存在的结果编入审计，也不默认为RQ2.1。

## 1. G的收益：关系还是异常排名/严重度/onset？

### 已经执行的相关实验

1. RQ1.1四区域表示析因：G作为**整包**从文本变图，其他区域背景分别配对。报告三主数据集G平均MRR效应Qwen +0.0561、Gemma +0.0454，对应既有family Holm p=.00110/.00236。它确认整包G表示效应，不能拆分其中具体边与派生异常摘要。源码 `RQs/RQ1_1/src/exps.py` 中packet同时包含 `propagation_service`（rank/onset/severity/source）与 `directed_call_edge`。
2. RQ1.1定向身份交换/安慰剂/neutral：`counterfactual_pairs`按公开显著性选择同粒度实体，neutral重画整张无事件内容图。不是单独删除G中的时间、严重度或边。它们不能回答组件归因。
3. **旧RQ3 SEARCH24已经做过时间启发式消融**：同24个训练开发case，先更改whole-window指南，再在相同指南下删除 `estimated_fault_window` 与整条 `propagation_service`，保留具体调用边和其他观测。后一个比较A22 MRR .3986→.3819，A25 .4333→.5000；各12例，注册时间比较探索性Holm均1。源码 `project_whole_window` 确实删除整个摘要，不是只删onset数字；G内部图空间同时变化。不能说“我们从未去掉过onset/异常摘要”，也不能把它当作纯onset单因素效果。
4. **SEARCH31已有signed-z标签消融**：在SEARCH24去摘要版本上只隐藏Metrics的signed-z及其说明。A22 .3819→.3750，A25 .5000→.4167。它不是G severity的独立消融，更不是默认所有异常分数有害。
5. RQ2.1的G矩阵/分层图、onset排序/拓扑居中保持原事实；回答编码与布局影响，不回答删除哪种内容。

### 能回答与不能回答

历史足以说明：G整包表示存在条件性收益；公共时间/异常强调会改变回答；删除启发式并没有稳定改善。**还不能量化在同一事实/布局框架下，具体边、rank、severity、onset各自及图文交互。**

决策：取消再次确认一般G图文差异、整体去摘要有没有用的宽泛实验。若保留新实验，必须是历史没有分离的组件问题，并避免删除rank后仍通过按rank排序、颜色或节点大小泄出同一量。旧SEARCH24作为直接前驱，不冒称新发现。

## 2. 补证据何时有用，何时将pod误判为node？

### 已有相当直接的证据

- 旧SEARCH的top8+node CPU/内存补充，在A/B两批AIOPS训练开发例中均有正向均值；强制资源名额替换/均衡追加则退化。不是“宿主证据越多越好”。小样本、协议演进保留原边界。
- RQ3.1的X丢失node资源观测，RQ3.2的SC_BACKBONE/STRATA/STRICT_PAIR等分别检验保留、覆盖与配对；SC层次约束不是固定局部观测下的纯宿主证据开关。`RQ3_2/src/selector.py`确实重选内容。
- RQ3.3 check120，Qwen node组(n=17) TPV→W_G .1765→.3059，pod组(n=17) .1912→.1618；Gemma pod组 .4706→.4118。已有明确正反模式。
- RQ3.3 `INC-83BCD48B2886`：补入3376 load与66131 throttling，Qwen将node升到首位。`INC-BA41A280E858`：原pod46218首位正确，追加真实node5360的IO queue/iowait/await后变成node第一、pod第二。
- **RQ3.4已经完整跑了P×H×K八组合**。H在P1K0背景改变59/60例观测集合；Qwen平均H效应+.0230，Gemma0，未形成显著普适效果。它不是尚未测试的概念。`scope_candidates`将focal pod、host、同host peer、异host同service peer与hosts/owns共同组成包；`select_packs`还改变追加排序与选择。
- RQ3.4 `INC-27F3CF9F35C3` 的单pod restart 0→1、同宿主其他pod保持0，支持局部实例解释并修复排名。也有真实page-fault/关系断言压过原大延迟、破坏正确答案的K对照。
- RQ3.6 A再次观察到W修复node5900，以及同一46218/5360病例的上归因错误。**同一病例跨轮出现不是多个独立病例支持**；必须结合新增病例与全部配对分布。

### 能回答与不能回答

已经能回答“补充宿主证据有时修复node、有时破坏pod诊断”，并有原输入和reason定位到竞争症状及范围判断。**尚不能认定是宿主证据数量过多造成破坏**：没有固定anchor/同预算的host数量或重复剂量实验。也未把H包中的host观测、同类peer、部署关系逐一独立操纵。

决策：取消重复的泛泛W-vs-TPV、H开关、强制均衡覆盖实验。保留的应是明确修复措施及其解释，例如固定局部锚点后分离host/peer、同一宿主重复观测去重是否降低错误上归因。不要简单在旧H0/H1上改名再跑；选择器变化与同事实表示变化分别计量。MRR净修复/破坏是主终点，不能只展示更少类型错误。

## 3. 调用、部署关系与绑定怎样影响图文诊断？

### 已执行与未执行必须区分

1. **旧SEARCH13已添加全量public hosting关系**：12个训练case、两条件24次Qwen调用，A22 .3333→.2500，A25 .2500→.0556，RR零修复/3破坏/9不变。trace轴为两条件共同控制。添加信息也挤占G显示空间，因此不是纯关系类型效果；但足以否定“以前没加过部署关系”。`hosting_axis_development_v1/paired_review.json`有完成/输入检查与逐例记录。
2. **Tournament R16已做实体绑定卡片**：源码 `candidate_binding_groups` 将已选M/R/L按公共归属放入typed owner card，余下事实完整保留。Qwen在128个剩余case新增Top1 3例，Gemma106例新增2例。这不是全480的同分母收益，更不是T/G完整绑定析因；但“按实体分组/注明类型”不是新动作。
3. RQ3.1执行过NO_GROUPING、NO_SHARED_TIME等；RQ3.2同事实多承载、取消局部对比等提供组织损耗证据。不能再把一般“邻近组织是否有用”当新问题。
4. **RQ3.4已做2×3图文/关系文本实验**：T/G × NONE/REPEAT/VERIFIED。Qwen screen宏MRR依次T .3472/.2790/.3182，G .3870/.4083/.3713。Gemma T均.2167，G .1917/.2167/.1833。VERIFY不稳定优于重述。源码 `integrated_parts` 保持原G PNG，只将K作为文本追加；K主要为数值、类型、时间比较，check中显式调用/部署关系仅118/1850=6.4%。**实验名字含visual_binding，不等于已经把新增部署关系/观测绑定画进图并分别消融**。
5. RQ3.3 `binding: BIND_LOCAL/BIND_REMOTE` 有代码/注册，但完成报告明确未运行；不能当作已完成否定，也不能宣称新创的方向。
6. 旧RQ3.6 B的W_SCOPE仅有资格样例18总calls中的部分，正式0；smoke不作为疗效结果。

### 决策

取消再次泛泛比较“加hosting、标类型、加验证文本或普通图文”以及通用截图控制。剩余有价值缺口是：**在固定选中观测下，调用与部署信息各自是否被正确使用，以及将同样关系绑定到图元是否减少特定误归属**。须给文本相同关系和绑定信息；不能让新图多事实。新图内容若同时重选/加关系，不能把净变化都归为视觉。

## 4. 来源与状态

- [RQ1.1/RQ2.1完整报告](../experiment_reports/RQ1_1_RQ2_1_findings/findings.md)：§4、§6、§8–9及F01/F04。
- [旧SEARCH逐轮回顾](../../RQs/RQ3/findings/search_retrospective_20260912.md) 与 [51项配对对照](../../RQs/RQ3/results/search_first_v1/retrospective_through39_20260912/matched_contrasts.md)。对应协议：`RQ3_temporal_sensitivity_20260912.md`、`RQ3_observations_20260912.md`、`RQ3_hosting_axis_development_20260912.md`；实际paired JSON与时间对照JSON均在原结果根下。
- [Tournament报告](../experiment_reports/Tournament_Analysis_2026-09-15.md)：R15/R16和node/pod分析；对应 `RQ3/src/renderer/owner_groups.py`。
- [RQ3.1报告](../experiment_reports/RQ3_1_Results_Analysis_2026-09-19.md)、[RQ3.2报告](../experiment_reports/RQ3_2_Results_Analysis_2026-09-22.md)：选择/组织/承载机制及其实际实现边界。
- [RQ3.3报告](../experiment_reports/RQ3_3_Results_Analysis_2026-09-24.md)：§1未执行清单、§7–8修复破坏；`RQ3_3/configs/research_v2.json`为注册而非完成凭证。
- [RQ3.4报告](../experiment_reports/RQ3_4_Results_Analysis_2026-09-25.md)：§2干预核对、§5析因、§6图文、§8–10事实与案例；`RQ3_4/src/exps.py::scope_candidates/select_packs/integrated_parts`。
- [RQ3.5报告](../experiment_reports/RQ3_5_Screen_Analysis_2026-09-26.md)：已选105个J包均request-family、scope=0，不能拿该轮回答宿主scope问题。
- [RQ3.6 A报告](../experiment_reports/RQ3_6_Stage_A_Analysis_2026-09-26.md)：§7–8，领域guide G与遥测区域G需区分。

本审计没有重新计算显著性或把早期小训练集与后来的eval/check合并。没有重分类历史有效性，也没有把来源未执行的设计当作结果。新模型调用为0。
