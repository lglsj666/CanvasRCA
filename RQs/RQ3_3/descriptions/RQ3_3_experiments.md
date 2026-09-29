# RQ3.3 executable protocol v2

日期：2026-09-23。注册标识：`rq33_witness_v2`。状态：**五项bounded GPU smoke通过；正式队列的准备阶段发现旧缓存编号冲突，已定向修复，按完成flag续跑**。通过范围为注册smoke条件，不代表所有可选分支均已live验证；EVENT分支保持未获资格状态。

用户随后授权CPU回归、smoke、启动正式队列，并授权修复准备失败后重启队列。后续扩展仍遵守登记的screen/check科学决策，不自动放宽。

## 1. 权威入口与边界

- 当前注册配置：[research_v2.json](../configs/research_v2.json)，命名空间 `witness_v2`；v1为未执行旧注册，不可混用。跨RQ理由见[主计划v4](../../../docs/CanvasRCA_Next_Research_Plan_2026-09-22.md)。旧CPU准备物按其源契约保留，新契约重新准备所测三个case。
- 五功能模块：[utils](../src/utils.py)（公共源和准备）、[exps](../src/exps.py)（见证与实际输入干预）、[gates](../src/gates.py)（分区、选择和统计）、[main](../src/main.py)（执行、恢复及 CLI）、[tests](../src/tests.py)（CPU 资格）。
- 图像辅助函数为本 RQ 局部函数。默认 G 图调用父版冻结 renderer，**不修改父版源文件**。新的关系图控制明确与原图分开。
- 本地统一 `configs/vllm_inference_local.yaml`；两模型顺序运行，单请求 output cap 8192，timeout 300s。不修改模型、image processor、采样、scorer 或统一 YAML。
- 历史SC请求的运行兼容检查保留完整配置hash：只允许已证实的`request_timeout_sec: 1800→300`运维迁移。必须能由当前完整配置仅还原此字段精确重构历史hash，且其他effective字段完全一致；未知hash、额外字段变化或模型/采样/上下文/输出配方变化均报错。校准启动GPU前检查全部120条小型来源元数据，不重建已完成请求；本次修复不改变历史输入、当前实际300秒请求或原评分。
- 明确关闭 `CANVASRCA_ATTENTION_MODE/PROBE/PROBE_REQUIRED`，不是只关闭汇总而留下原始 attention。
- 一次主部署调用、一张图、候选在文本。系统提示复用父版；SIRCL 使用自身已适配的系统与用户内容。

## 2. 数据与真正独立的集合

引用 RQ3.1 已有 `data_registration_v1/private/split.json`，不再生成 raw/processed data、不移动 train/eval/test。Eval 必须仍是五数据集 480，已有 test 360 为**已暴露回归集**。

统一 segmentation 的 `connected_row_groups` 在完整注册表上构建事件别名、同源窗口重叠的传递组。跨数据集的同名 source/event 不混为同一事件；同源而窗口未知时不能凭空保证分离。

分配screen/check时，每个**完整传递组**仍是不可拆的单位，但只将该组的eval成员写进开发roster。组里同时有旧train/test/unused成员并不会令这些eval成员从开发集消失；这些历史跨分区重叠需要在暴露审计中保留，不能把开发检查说成未经历史接触的独立测试。初次CPU登记发现原实现错误地要求全组均在eval，导致AIOPS-2022仅剩7/100个合格eval、check为0；改为完整组投影后再运行登记和资格验证。

| Cohort | 最大构成 | 使用 |
| --- | --- | --- |
| diagnostic30 | 三主数据集各 10 | 来源语义核查；配置可登记定向 audit IDs，未登记时确定性 hash 选择 |
| screen | 各 20，共 60 | 校准、九条件筛查（六个W候选不变）、唯一预算检查、条件式诊断/事件研究 |
| check | 各 40，共 120 | 与 screen 和 diagnostic30 的完整组不交叉；不重新选方法 |
| mechanism120 / mechanism90 | 各 40 / 各 30 | 组织干预 / 依据移除、绑定和重复 |
| eval | 原 480 | 七方法主比较 |
| test | 原 360 | 锁定回归 |
| fresh | 每主数据集最多 30 | 仅接受完整 exposure audit 后合格的 unused 事件 |

确定性 bounded subset-sum 不拆组凑数量。实际不足则缩小、记录分母；screen/check 任一主数据集完全缺失时不可选择/推进。RE2 仍完整进入主比较，不用来选择 Witness。开发集来自旧 eval，不能称 untouched heldout。

独立事件审计必须声明 `status=complete`、reviewer、已核查历史目录及 `exposed_opaque_ids`，并排除所有旧 train/eval/test 的完整重叠组。没有此文件时 fresh 明确不可执行，不把未验证的 unused 自动叫作新 test。

## 3. 公共源、类型和选择

### 3.1 不可变基础

优先读取保留的 RQ3.1 execution contexts；不存在时只用父版原语重建单个 case 的桥梁，不运行 QA 或旧 experiment dispatcher。TPV 的原 M/R/L 文本、G 像素、任务、候选和 closing 保留。

**公开身份兼容修复（2026-09-23）。** 部分旧execution context早于公开node→pod元数据的实体类型修复。继承时比较自然实体→数字ID的完整绑定，不能只比较候选数字集合。实体全集相同但绑定不同的case，在本RQ内用现有已修复父版原语重建；实体全集不同仍报错，不私自合并/删候选。兼容case继续复用，历史cache和结果不改。新screen及后续方法共享修正后的映射；历史SC三种文本校准及TPV_BRIDGE同时保留各自原输入和原评分映射，不把新编号应用到旧文本。这是身份适配修复，不是根据诊断成绩改变选择器。

资格承接依据：45项CPU单元回归通过；18个已完成准备物的小型身份审计一致；故障case定向重建后双模型18个编译条件通过；此前五项smoke的90个逻辑单元完整请求身份与评分映射均不变。因此保留原GPU资格证据，不重复smoke、不声称修复case新增live验证。原registration/资格记录快照、CPU证据及显式契约迁移位于`results/witness_v2/contract_migrations/public_metadata_identity_v1/`。本次尚无正式模型调用，旧正式结果无需重跑。此单次迁移不是续跑时的全量校验；平常恢复仍只读完成flag。

Witness 独立调用 canonical per-case loader 的 public adapter，读取全部可绑定 metrics、traces、logs、公开 hosting/call relations；不能把旧 top-k 当完整池。原始源索引、source hash、选择包身份只落在离线审计数据，不发给 Solver。

**日志单位修复（2026-09-23）。** 全源日志按实体×规范化模板×级别聚合，采用`DenumTemplatePhaseSummaryV1`。时间戳和请求标识不形成新候选；实体引用和明确status/code/errno等状态值保留在模板中。模板数值槽分别汇总reference/current的n、min、median、max，并保留事件计数、实体日志总数、相对首末观测时间和全部源行索引。不按原始完整消息逐条构造Witness，不增加日志top-k预筛。数值槽变化、记录日志速率和模板占比独立参与同语义比较，避免聚合后遗漏计数不变但诊断数值变化的信号。摘要不是原始日志的无损序列化；所有本轮变体使用相同投影。

此修复替代未通过资格的完整消息分组实现。其AIOPS-2022例将387,352条日志扩成242,353组，准备超过27分钟；AegisLab例14,343组、准备377.95秒。模板聚合是输入投影修正，会改变新Witness的内容，旧CPU产物不能作为新契约资格。TPV/P0父版、既有正式结果和原始per-case数据不改变。

操作优化：共享候选序列化及精确token结果；Trace按实际request索引聚合，操作名只净化一次；重复完整请求preflight复用有界精确缓存。单次部署准备与3预算×消融的整套实验准备分别计时，不能把预生成所有对照的时间冒充单次RCA latency。不得通过减少数据行、近似token计数或跳过完整请求容量检查提速。

JSON日志先规范化键顺序，已知epoch/calendar时钟与请求标识不构成模板身份；小数值的`time`字段仍保留，避免把耗时误当绝对时间删除。诊断字段和HTTP headers不会因本次优化整块丢弃。P0_MORE采用精确批量token计算，接受一个条目后用新前缀重新计算后续候选；选择顺序和容量条件不改变。全量父版Denum投影使用线性去重，在本RQ内调用父版单行投影保持字段与顺序，父版文件不改。

精确token缓存仅对已识别的实际BPE模型、normalizer、pre-tokenizer和词表认证安全换行边界；不能跨边界的片段分别计数并按模型累加，最后取两模型的较大成本。未知配置退回完整分词，不使用近似token估算。缓存有界；完整请求仍做模型各自的上下文预检。三例共321段实际与边界文本分别在两个模型上与整段分词比对一致。

日志性能修复后的CPU回归总计106.58秒：三例分别为AIOPS-2022 89.01秒、AegisLab 44.70秒、AIOPS-2025 9.73秒，包含多个预算及对照的准备，不是单次RCA端到端耗时。随后修复G scene的graph/ledger高度分配，最终源码契约回归109.59秒通过；32项单元检查通过，111个真实case×条件中86项通过、25项按注册约束不适用。另有3项smoke认证/中断/端口所有权回归通过。来源校准manifest已完成60例、120份历史请求的真实绑定审核，五项smoke均完成；不适用不等于已获live验证。完整计时、原因及输入一致性核查见[问题记录](../../../docs/issues/RQ3_3_implementation_review_2026-09-23.md)。

**资格队列修复。** CPU与smoke共享同一seed=42的三个主数据集case，避免CPU结束后smoke访问另一组未准备case。开发smoke覆盖TPV/W_SEM_EXEC/W_COHORT，效果与泛化smoke覆盖P0_MORE_TRUE/W_T/W_G，机制smoke覆盖W_T_FLAT/W_G_RELAYOUT/W_NO_FLOW。不再机械取前三个arm导致效果smoke只覆盖旧基线。仍每实验最多18调用/600秒。GPU启动前，在同一smoke时限内检查已通过的CPU契约、准备物和实际输入，包括校准manifest；缺失依赖不能先加载GPU再报错。

### 3.2 固定的时间与测量语义

reference/current 来自父版实际 `sircl_star_analysis.window_rel_s`，而不是旧 X 的整窗中点，也不是注入时间。归一到公开观测起点的相对秒。度量单位按来源契约转换，trace aggregate 显式称 inclusive，不伪造 exclusive latency。

SEM 定义文件采用 exact metric key，不凭字符串包含 `cpu` 就判定为利用率。v1 注册 KSM 的资源 request/limit、readiness、restart 以及 cAdvisor CPU 累积时间、working set/usage；未知指标不编造释义。公共角色只在 SEM 条件解释；源 observations 不变。

RAW 提供参考/当前中位数、样本数、区间、必要状态/计数器原始操作数。EXEC 用已经可见的舍入操作数计算差、比、带实际分母的 recorded request/error/log fraction；没有请求 ID 不把请求数填成零，counter 下降按已声明规则处理。无穷/NaN 不成为分数。

Trace linking 以 `(trace_id, span_id)` 为键；重复 span key 不强行关联，不能跨 trace 猜 parent。COHORT 优先实际 HTTP/RPC 成功/错误（每组至少 5）；**状态可用但样本不足时不改换问题**。仅状态不可用时，使用至少 20 个参考请求确定 request-max-span p95，当前各群体至少 5。它是新增联合信息，不算等信息重排。

### 3.3 见证选择

SCOPE、PATH、LIVENESS 分别是实体/宿主范围、真实请求关联和可用性/活动问题。自身前后观测也可形成合法单侧见证，不强迫节点拥有 peer。跨单位不做差；不同语义的量不直接加成一个异常分数。实际 comparison 在同语义组内取秩，以观测支持、增量 token 与 stable physical source key 解并列。匿名 ID 不作为策略 tie-break。

实施细则：单侧数值完全不变不独占一个“变化见证”，但仍可作为另一实体的真实稳定对照；请求耗时、captured rate和带分母错误比例分别保留比较轴，先分别在相同语义/单位组中取秩，再取最强同类秩排序，禁止直接对ms、bytes、次数取最大值或相加。已有充分bin支持的持续变化优先于同层仅单点变化；这个布尔优先级只用于CPU选包，不向模型提供异常推荐分。计数器计算分别在reference/current内处理reset和观测时长，不能把正常累积增长当利用率。

统一选出的observation IDs同时供RAW/SEM/EXEC/SEM_EXEC；不能为不同变体重选内容。每包最多4个源观测；1024/2048/4096 appendix tokens对应最多2/4/8包，由小到大保留已选前缀及已有群体。512-token reserve供COHORT/MARGINAL较长者，无资格则诚实no-op。真实两模型tokenizer/processor都需通过完整请求preflight；只减少新增尾部，绝不裁TPV基础或较小预算前缀。

父版的基础事实不因“提到某实体”就算已回答某个比较问题。相同源观测与统计定义才可判为重复；分析保存实际 identity。对于只有单侧数值、无法提供公共机制定义的情况，不把它描述成已经有诊断解释。

`P0_MORE_TRUE` 从父版完整 metric 原生排名、TRC-L 排名、LOG-R/Denum 完整排序中排除已展示项目，再固定 M/R/L 轮转追加，沿用父版显示投影。它不是旧 SC 的 P0_MORE 重命名，也不改原图。

## 4. 全部注册条件

| Stage | 条件 | 最大新增 calls |
| --- | --- | ---: |
| calibration | TPV_BRIDGE、SC_TEXT_AS_RUN、SC_TEXT_GUIDE_FIXED、SC_TEXT_SOURCE_FIXED | 480 |
| screen | TPV、P0_MORE_TRUE、六个W候选、W_COHORT_MARGINAL机制控制 | 1080 |
| budget | 已选W_G、P0_MORE_TRUE，各补1024与4096档 | 480 |
| check | TPV、SIRCL_TEXT、P0_MORE_TRUE、W_T、W_G | 1200 |
| effectiveness | C_LEGACY、TPV、SIRCL_TEXT、P0_MORE_TRUE、P0_T_TWIN、W_T、W_G | 6720 |
| organization | W_T_FLAT、W_G_FLAT、W_G_SCREENSHOT、W_G_SCENE_CAL、W_G_RELAYOUT、W_NO_SCOPE、W_NO_FLOW | 1680 |
| interventions | T/G × REMOVE_TARGET、REMOVE_CONTROL、REANONYMIZE、CANDIDATE_ORDER、REPLICATE_1、REPLICATE_2 | 2160 |
| pairs | mechanism90，T/G × PAIR_00、PAIR_10、PAIR_01、PAIR_11，两个模型 | 1440 |
| binding | mechanism90，T/G × BIND_LOCAL、BIND_REMOTE，两个模型 | 720 |
| events（条件式） | EVENT_TEXT、EVENT_SCREEN、EVENT_GRAPH | 360 |
| diagnostic（条件式） | FIRST_TPV、REPEAT、VERIFY_SAME、VERIFY_WITNESS | 480 |
| regression | 主比较七方法 | 5040 |
| fresh（条件式） | 主比较七方法 | 1260 |
| 五个逻辑 smoke | 每实验最多18 calls | 90 |
| **计划上限** | **含原五个smoke；不是新的硬门槛** | **23190** |

全 RQ 40,000 新增调用硬上限，失败和重试也计数。这里的调用计数不是商业 API 计费。去重节省额度不增加 arms。

### 4.1 校准不是重写历史

SC 校准读取原输入 manifest，原图 SHA（若适用）、原 system 和运行配方。每条修改必须是**唯一 exact text span**，登记 part_index、before、after、scope、audit_reference。guide 与 source_projection 补丁分组，source 条件建立在 guide 条件上；没有确认的源错误即不产生新的 source 改动。未提供真实审核 manifest 时 calibration 不能运行，不能猜一段旧 prompt。

`calibration-manifest --manifest FILE` 会验证 screen × model × 三个 SC 条件，冻结到新结果目录。文件 schema 为：`status: audited, reviewer, cases[opaque][model]`；每条 case 记录 `input_path/input_sha256/system/effective_server/images_by_sha256/guide_patches/source_patches`。所有引用在本地项目内或已明确给出的绝对路径，不修改历史文件。

可选历史桥梁 manifest 同样需要 reviewer 与完整 request descriptor、scorer hash、原始 output/cost/conversation/raw response 路径。只在完整输入一致时引用；不按 arm 名、目录名或 MRR 相近推断等价。无 manifest 时按本轮计划最坏调用量执行。

<a id="sc-source-calibration-audit"></a>
#### SC 来源校准审计（2026-09-23）

`scripts/audit_sc_calibration.py`对screen的60例×两模型绑定RQ3.2实际SC_FULL请求。读取原context中的公开selected facts，沿历史边界执行同一匿名化和自然文本序列化；120份证据文本均与原prompt逐字节相同。仅替换原guide中一个唯一段落，按已有O引用明确不同估计器：父版M的leading-half均值/离差和median bins、MET-Z公共分界的均值/标准差；新增M的公共分界median/MAD和极值bins；父版R的child-duration sum与新增R的同trace child-interval union。另澄清count/latency fold-change二元组的实际字段含义。

依据为RQ3.2 `selector.build_aligned_pool/select_signal_cover`、RQ3.1 `_direct_metric_items/_complete_trace_items`、父版`kpi_select._column_stats/score_series`及`panels`的TRC-L实现；脚本记录其源码hash，并逐条核对原prompt hash。此检查只确认来源、实际投影及guide口径，不声称独立重算了每条原始遥测。未确认需更改的数值投影，因此`source_patches=[]`，SOURCE_FIXED与GUIDE_FIXED输入相同并复用，不能作为独立干预。历史RQ3.2输入/输出不改。

审计产物：`results/witness_v2/calibration_source_audit.json`及`calibration_manifest.json`。该步骤补齐先前缺失的真实manifest，不替代正式60例语义校准的结果分析。

### 4.2 两个实际实现补强

**FRONT 边界。** 父版候选位于 inherited evidence shell 中。为避免顺手改变候选位置，W_FRONT 只在原 task 后、guide/evidence 前插入同一 W_SEM_EXEC appendix，候选及其顺序不动。它不是“前置见证＋前置候选”的混合干预。

**G 重排校准。** 原 G 是 PNG，重绘不能冒充单纯移动节点。W_G_SCENE_CAL 与 W_G_RELAYOUT 使用同一新绘图函数、字体、像素尺寸、节点/边以及完整属性 ledger，仅节点位置不同。两者必须共同可绘制；它们与原 W_G 的差别不归因于位置。历史计划v3为此增加240 calls（20,430→20,670）；当前v4已包含该控制，总量为23,190。

### 4.3 其他干预的实际语义

- W_T 和 P0_T_TWIN：G 图替换为同一完整 G fact ledger，不把它们冒称原 T；M/R/L 和候选不动。
- FLAT：相同观测与关系按区域分离，取消局部配对；不是换事实。重复字串合并不会删除唯一观测。
- SCREENSHOT：G ledger 的真实文字截图，固定原 PNG 几何，不悄悄缩字号/裁字段；不能放下则设计不适用。
- NO_SCOPE / NO_FLOW：从完整候选见证池取消对应类型并按同一规则重新补齐；这是构成消融，允许内容变化。
- 目标移除仅 evaluator-private 构造；要求存在独占根因关联观测、且基础已存在根因遥测时不声称移除了唯一支持。对照匹配模态组合、规模与 token。只能解释关联证据依赖，不自动证明故障机制因果。
- REANONYMIZE：typed ID、事实绑定、候选、G 图字形、私有 scoring map 一起变；父版 G 先在原 ID 下像素回放一致才允许改 ID。这个定向检查不是 resume 时扫描所有旧图。
- CANDIDATE_ORDER：只改候选列表唯一 exact span，数值和证据顺序不变。
- REPLICATE：显式 replicate identity，独立真实调用，缓存不能返回第一次响应。
- 事件图只用已选见证的真实 parent/hosting/ownership 关系；无实际边则不适用，不能编造因果箭头。三条件共同通过 ledger、截图和图的容量约束；原 G 上方像素原样拷贝，新区使 processor 缩放变化须单列。
- 两调用诊断共享 FIRST_TPV 的**公开响应**，不共享 private score。REPEAT 不收到旧答案；VERIFY_SAME 与 VERIFY_WITNESS 使用同一个旧答案和核验句。报告整个两调用成本，不选正确分支合并成一个答案。

### 4.4 v2决策：将信息论假设变为受控输入差异

**理由与替代关系。** 旧结果提示“观测存在、已被选择、能够被模型利用”是不同环节。依据主计划所列LSMI（ICML 2025）、COMI（ICLR 2026）及信息缺失研究（EMNLP 2025），新增以下控制，而不是训练互信息估计器、引入新的模型或重命名MRR。此条取代未执行v1的开发预算与机制矩阵；历史数值、推理配方、原TPV图文和数据分区不变。源码和配置版本共同升级，旧prepared artifacts不得混入v2。MRR仍是主终点。

1. **联合统计与边际统计。** `W_COHORT_MARGINAL`与`W_COHORT`采用同一entity/operation、窗口、成功/错误或快/慢请求并集、群体大小及普通见证。Marginal展示合并的请求耗时中位数和每条实际调用边的请求计数；Joint还展示群体内的同类统计。合并中位数由实际并集重算，不平均群体中位数；边按请求去重。群体名称明确为记录成功/错误或参考p95两侧。二者均需落入固定reserve，不能删普通见证为Joint腾空间。与SEM_EXEC的比较测新增请求摘要，Joint−Marginal测条件关联信息增量，**不是纯排版效应或已估计的条件互信息**。实际输入相同则复用并报告；来源合格、实际追加和未追加分层是预定义描述分析，不参与择优。

2. **证据对四条件。** 固定锁定方法的普通见证，在每case中按源身份hash选择一对观测a/b，不看根因、回答或成绩。四条件分别为E、E+a、E+b、E+a+b，**全组使用RAW、关闭SEM/EXEC与cohort**。a/b不得已在父版同entity×M/R/L区域出现；R/L不得与其他选中摘要共享源事件，M不同列可以共享时间行。移除全部重复a/b副本；标题、包顺序和公共关系保持共同背景，支持span计数不得残留泄露被移除的值。四条件及两承载、两模型共同通过预算/context才发请求，否则整组N/A，不能换pair或删基础。该严格资格可能产生较小n，必须报告分数据集资格率，不能声称覆盖所有案例。交互`J=RR11−RR10−RR01+RR00`及四个条件效应是**RR量尺上的诊断效用**，不是PID；有界RR饱和和有限Solver能力均可能影响符号。

3. **局部绑定重复。** BIND_LOCAL在普通见证每项旁重复typed entity、单位及reference/current区间；BIND_REMOTE将完全相同caption按相同内部顺序集中放在追加区开头。两者同观测、同caption多重集、不加“重要根因”分数，不动原TPV。额外512 tokens仅供这些caption，不能选择新事实。必须同时放得下，不截短；边界token差异记录实际成本。LOCAL−REMOTE检验位置绑定；各自对原W是含重复开销的补充比较。不能把该控制称为原图上的视觉效果。

4. **嵌套预算曲线。** 1,024→2,048→4,096 tokens由小到大构建，包和已选cohort均保留前缀；同预算的P0_MORE为强扩容对照。1024相对v1改变了构建顺序，因此不可复用v1名义上的2048选择缓存。报告实际input/output/image tokens与`1−MRR`；这是经验效用—成本曲线，不是Shannon率失真函数，不把token当bit，不用MRR/token替代准确率优先的选择规则。

新增调用：Marginal 120＋小预算240＋证据对1440＋绑定720＝2520。它们属于原五个逻辑实验，不增加smoke数量。未来CPU定义已覆盖source union、pooled median、同内容位置、移除闭包、预算身份和择优规则，**本次未执行这些测试**。

## 5. 锁定与统计

筛查只用Qwen三主数据集等权MRR，从六W选一个全局条件；Marginal、PAIR、BIND均不进入候选池。0.01内先看实际input token，再按转换数/ID。Gemma完整报告但不调参。screen含未解释基础设施失败时不择优忽略。可选预算一次比较1024/2048/4096，以最高MRR的0.01以内取最小档；2,048复用筛查。不以MRR/token择优，允许预先跳过整项并锁`default-budget`，不得看结果后补挑档。

check 的 W_G 必须相对 TPV macro MRR≥+0.03、相对 P0_MORE_TRUE≥+0.01、相对 SIRCL≥−0.02；每数据集相对 TPV≥−0.03，AC@1/5不降，repairs>breaks，来源语义人工审核通过才推进。失败不重选，不自动启动480或test。阴性 screen 可直接锁小预算做有界 diagnostic。

统计单位 case，Pratt-Wilcoxon、paired dz、Holm，无 CI。主要比较完整使用同一 case 集；机制有明确适用域，目标移除不适用不能删掉其他非语义/重复研究的案例。每组报告已注册数、实际计分数、状态、各数据集、AIOPS合并、三/五数据集macro及pooled。

同一stage的比较跨模型、arm及报告分层构成显式宽 Holm family；事件组均值的敏感性分析单列family。源码提供 SEM×EXEC 与 Witness×G-carrier 的 case级交互；不把重复调用当新case。强效果阈值仍 ΔMRR≥0.05 且adjusted p<0.05；开发推进条件不等同于该结论。

PAIR的J对0采用Pratt-Wilcoxon及paired dz：两模型×T/G×三个数据集/主域pooled/两AIOPS合并构成单一Holm family，事件组均值单独family。绑定及三预算比较分别作为stage内secondary families。PAIR/BIND的资格失败不删除其他机制研究的case；始终同时报告注册数、可用数、N/A原因及模型/基础设施状态。不从条件排名的熵、跨case匿名ID或AC@5估算根因互信息。

定性研究以原 conversation、request、projection和raw response为依据。仅可核对公开 reason 中的引用/归属，不声称读取了隐藏推理。最终人工案例核查不是预先生成的“成功故事”。

## 6. 运维、续跑与未来命令

**2026-09-23 正式队列授权。** 用户在五项bounded smoke通过后要求启动顺序全量队列，启动后停止人工监控。新增`scripts/formal_queue.sh`显式入口（不修改冻结实验源码/配置），顺序执行calibration→screen；screen正向时进行完整三档预算比较→check，通过注册推进规则后才进入effectiveness→organization→interventions→pairs→binding→regression。screen或check阴性时仅运行已注册diagnostic后结束，不改选、不强行扩量。EVENT尚未获资格、fresh没有合格roster，因此不自动执行。配置的`automatic_full_queue=false`仍禁止隐式启动；本入口只有用户显式启动时执行。

五项人工审核/资格记录已依据现有CPU/GPU和实际图像、完整会话证据落盘，不新增模型调用。准备最多8个独立物理核心worker；按需准备各阶段cohort，复用所有已提交准备物。队列在模型启动前按小flag跳过已完成model阶段；完成和失败flag均不自动重试。中断时向当前子进程发送TERM并等待runner排空，最后关闭仅由本队列启动的服务；通过相同入口恢复。没有历史结果的大文件hash或请求重建。

修复前53次实际调用的原始计数从三个旧attempt数据库以`prior_attempt/`命名空间导入当前调用登记，仅用于硬上限记账、绝不复用响应。当前86次成功smoke加旧53次共139次；重复启动不重复导入。40,000总调用上限不变。队列启动、停止、失败状态写`results/witness_v2/formal_queue_status.json`；运行日志写该结果目录的`logs/formal_queue/`。可用`kill -TERM <queue PID>`安全暂停；fail-fast错误仍需诊断后显式retry，不自动反复重启。

最多8个物理核心独占worker，准备队列按dataset/source轮转（尽量分散cloudbed）；每worker本地tokenizer复用、BLAS单线程。全量dataframe只在单case准备时驻留；context落盘后formal阶段不重算源统计。正式推理有界36并发，主线程为下一请求编译时已提交GPU请求可继续。

`done / fail / design_infeasible / not_applicable` 为逻辑 case×model×condition 的小型原子flag。模型回答错误/格式失败仍为已完成模型结果，不自动重采样。写入完整raw/conversation/input/cost并排空writer后才写done。resume先读flag，done/fail直接跳过，不重建请求、不扫旧结果hash。无flag的断电pending可恢复；SQLite只处理此前未提交完的started调用，新增调用全都占预算。

300s request timeout写fail后继续；其他基础设施错误停止提交并排空已在途请求；人工中断同样停止提交后排空。失败不自动retry，必须明确 `retry --key ...`，原flag保存到retry_authorizations后才解除。Preparation失败同样有独立flag。已经成功的flag不能通过retry命令删除。

2026-09-23 阶段衔接修正：上述timeout-continue同时适用于跨阶段执行，不仅适用于单个runner。校准所有单元已terminal且失败全部明确为`request_timeout`时允许进入screen；旧complete marker只有失败总数时只读取小flag核对类别，不读取或重建历史请求。非timeout/未知失败、缺失单元、主要条件N/A仍阻断；不添加5%失败率门槛。screen、budget、check选型按同一配对可评分case集合计算，某case任一相关条件timeout则在此次比较的所有条件中共同排除，显式记录case ID、paired_n和原始失败记录，不记为零分、不自动补跑。budget的1024/2048/4096及匹配控制使用同一集合，不分别删样本造成不同分母；若任一主数据集已无可评分case则无法决策，不伪造通过。模型格式/候选错误仍按原评分保留，设计不可执行仍按注册规则计分；所有MRR阈值、tie-break、采样、输入和评分器不变。此修正于screen尚无正式结果时登记，修复旧代码将所有fail一律阻断的执行偏差，不依据成绩改规则。

首轮registration只hash源文件/配置，不hash大型processed/result目录。源代码改变后不能悄悄混入同一冻结run；操作性修复需登记迁移，不以“大规模重算所有输入”替代正确resume。

后续经过用户许可的例子（**本次未执行**）：

```bash
cd /home/lglsj/CanvasRCA_nibi
bash RQs/RQ3_3/scripts/entry.sh register
bash RQs/RQ3_3/scripts/entry.sh calibration-manifest --manifest PATH_TO_AUDITED_MANIFEST
bash RQs/RQ3_3/scripts/entry.sh cpu-check --seconds 1800
bash RQs/RQ3_3/scripts/entry.sh smoke --experiment exp_semantic_calibration
bash RQs/RQ3_3/scripts/entry.sh qualify --experiment exp_semantic_calibration --manual-audit PATH_TO_REAL_REVIEW
# 服务由本地统一 launcher 启动；run 不会猜测/杀死其他任务的服务。
bash RQs/RQ3_3/scripts/entry.sh prepare --cohort screen --workers 8
bash RQs/RQ3_3/scripts/entry.sh run --stage calibration --model qwen3.8-27b --execute
# 完成 Qwen 后切换 Gemma，两个模型完成后才进入下一阶段。
```

静态阶段只允许 AST/JSON、Ruff、shell `bash -n`、源码接口/调用链检查和 diff 检查。**不能把 `tests.py`、`cpu-check`、CLI `register` 或模块导入执行称为静态检查。**

未来每实验一个18calls/600s逻辑smoke，包含两个模型启动/切换/落盘。timeout-only须写明实际live覆盖，非timeout错误不能通过。`qualification.sh`仅CPU后顺序smoke，不启动formal。CPU/图像/源定义/真实conversation人工审核齐备才能qualify。

## 7. 当前未被静态检查证明的事项

真实字段可用率、完整case的token余量、图像可读性、tokenizer/processor兼容、吞吐、断电恢复实测及MRR均需后续运行验证。本次没有这些结果，不伪造source audit或smoke通过记录。配置中的calibration/exposure/bridge路径为可选外部输入契约，不是固定返回成功的代码占位；缺必要的真实来源凭证会明确报错或禁用该条件式分支。
