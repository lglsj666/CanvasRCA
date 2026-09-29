# RQ3.3 实现与静态审阅记录

日期：2026-09-23。范围：[RQ3_3](../../RQs/RQ3_3/)。用户明确只授权源码编写和静态检查；没有启动任何CPU回归、preparation、smoke、GPU/LLM调用或训练；未使用subagents。

下方原有条目是本日早前的Witness v1静态审阅；当前协议为v2，增补及最新检查见文末。旧条目不代表旧配置仍可用于新运行。

## 核对与已修正事项

| 关注点 | 实现处理与检查依据 |
| --- | --- |
| TPV被新选择器改变 | 新见证从完整per-case public adapter另建；原 `direct_rca_parts("TPV")` 与G PNG保留，追加只插入新part |
| P0_MORE实际上另一种排序 | 单独取父版score_series、TRC-L、LOG-R/Denum完整序列，原显示投影及固定区域轮转；不调用SC selector |
| 原图重绘与重排混杂 | 增加W_G_SCENE_CAL，重排只与它配对；240 calls单列，主方法不重绘 |
| RAW/SEM/EXEC选择不同 | 先以最长变体/双模型上下文确定同一组包，再切换释义/计算，4096保留2048前缀 |
| 字段语义错误 | 配置exact metric key；counter按phase计算reset-adjusted增量，不把累积量当利用率；duration保留source契约 |
| 缺请求ID误写请求量0 | 不生成不存在的request-count分母，记录实际带ID的span数 |
| HTTP/RPC小群体偷换延迟群体 | 已有status但样本不足不适用；只有status不可用才启用已登记p95路径 |
| 跨trace误接parent | `(trace_id, span_id)`唯一性校验，重复键不强接 |
| 无定义指标自动编释义 | 未识别语义保留观测，不生成SEM定义；具体覆盖率留待CPU审计 |
| 不同单位幅度直接排序 | 请求耗时/rate/error fraction分轴，同语义秩排序；不比较bytes和ms的原数值 |
| 文本ID换了但图没换 | typed字段、候选、G图及private scorer map一起变；旧ID图回放须先匹配原G |
| 静默SDK重试漏计调用 | 设置实际共享client读取的 `CANVASRCA_SDK_MAX_RETRIES=0`；统一durable call register逐次计数 |
| Attention暗中继续写 | 配置实际launcher读取的MODE/PROBE/REQUIRED关闭变量，复用无attention的record hook |
| Resume重算旧case | logical done/fail flags在加载tokenizer/context前过滤；不重建、不hash旧已完成artifact |
| 手动中断和失败 | 停止提交、排空在途；fail不自动重试，显式单flag授权；仅started pending可恢复 |
| CPU资格超时等待全部worker | 只终止本executor的子进程；不pkill其他项目进程；外层资格脚本有明确timeout |
| 统计/归因偷换分母 | case-paired比较、事件组敏感性、显式不适用域、SEM×EXEC与Witness×G的四条件交互 |

## 本轮静态检查

- AST解析全部新Python文件；不import项目模块、不加载数据或tokenizer。
- 新文件对本项目的静态 `from ... import ...` 逐一检查模块路径及顶层符号存在。
- Ruff `--select E9,F` 通过；发现的未使用导入、编辑期语法问题已修复再查。
- 两个shell入口 `bash -n` 通过，未执行脚本。
- JSON解析与注册矩阵算术检查：stage上限加五个18-call smoke =20,670，硬上限40,000。
- 五功能模块加`__init__`、三描述文档、五findings及shell数量符合当前项目结构限制。
- 逐条检查注册arm的真实dispatch、引用来源、flag与writer边界；没有 `NotImplemented`、TODO或固定成功的功能桩。唯一`pass`是服务端口未被占用时的预期异常处理分支。

## 资格边界与下一步

静态检查不能证明processor运行兼容、真实字段可用率、图像可读性、断电恢复速度或诊断效果。CPU/smoke/人工输入审阅均**未运行**；不能把这里的静态通过当成GPU资格。

后续首先真实审核旧SC request及guide/source exact-span补丁，注册来源和身份，再运行小范围CPU与人工图像/输入核查。独立事件exposure audit和可选桥梁兼容manifest也需要实际证据，不在本轮凭空填“通过”。这些输入由相应CLI读取、核对和冻结；缺失时会阻止对应路径，而不是静默fallback。

本轮没有修改既有实验结果、父版renderer、统一推理配置、scorer、raw/processed corpus或任何分区身份。

## 2026-09-23 增补：Witness v2 / 主计划v4

用户授权将信息论启示落实为源码与实验设计，并在静态检查后停止。当前配置为`research_v2.json`，默认结果命名空间`witness_v2`；v1仅保留历史未执行注册。计划调用23,190、硬上限40,000，仍为五个逻辑实验。

| 新审阅点 | 修正/实现 |
| --- | --- |
| 联合与边际使用不同请求 | 同一请求并集、群体大小、窗口和基础见证；边按请求去重；pooled median从原请求重算，不平均group medians |
| 组名让模型猜success/error含义 | 明确recorded_success/error或reference_p95两侧；限定同entity/operation的captured linked spans |
| 机制控制偷入方法选择 | W_COHORT_MARGINAL只分析，不进入六个部署候选；PAIR/BIND同样不择优 |
| 移除观测却留下计算结果 | PAIR四条件共同RAW、无cohort；移除全部目标副本及关联support计数，保留共同身份/关系 |
| 空包顺带丢失共同背景 | 保留标题、包顺序和公开部署关系；不能因PAIR_00没有观测就删除背景 |
| 关系或其他摘要已提供目标值 | 父版entity×region保守资格，R/L源事件重叠检查；不符合条件N/A，不改pair凑数 |
| LOCAL比REMOTE多获得事实 | 两者caption多重集一致、仅改变位置；额外512tokens不允许添加观测，原图不动 |
| 多预算在分析中互相覆盖 | budget进入任务身份，分析arm带预算后缀，重复case×arm明确报错；先比MRR，再以0.01内较小预算解并列 |
| 来源合格误当模型已收到 | 小flag记录source_available与cohort_included；复用响应仍保留当前干预标记，预定义分层和no-op计数 |
| 信息论术语超过证据 | 输出RR条件交互、实际token成本曲线，不声称PID、互信息或理论率失真界 |

源码检查：六个Python文件AST、98项静态本地import符号引用、Ruff E9/F、两个shell语法、全部JSON及每stage调用矩阵算术、描述文件本地链接通过。代码总量低于7,500非空非注释行。未来CPU测试定义新增并集统计、绑定同内容、PAIR闭包/背景、共享事件拒绝、嵌套预算、重复分析键及择优检查；**这些测试没有执行**。

限制：真实cohort可用率、512token是否够用、PAIR资格数、上下文余量和新增方法MRR均未知。不得把静态通过等同于CPU或smoke通过；本次不启动运行，也不调整历史结果。

## 2026-09-23 CPU调试增补：候选膨胀与重复计算

用户随后授权CPU回归、smoke和问题修复；本节替代前面“本次未执行CPU”的当前状态描述，但保留旧静态审阅的历史范围。尚无本轮正式推理结果，也没有新增GPU调用。

已确认的问题：

1. `extract_logs`按完整净化消息分组，动态数值/请求标识制造海量候选。AIOPS-2022样例387,352源行→242,353日志组，原测试超过27分钟未完成；AegisLab样例14,343组，377.95秒。它们并非全部进入LLM，错误在CPU候选构造与排序的规模及语义。
2. 仅遮罩数字不够：JSON键序、headers键序、请求标识与时钟仍制造模板碎片。修复为结构化规范化＋Denum数值模板＋阶段统计；保留明确状态码、实体绑定、全部源行、计数分母与诊断数值摘要。普通数值槽变化也可触发LIVENESS，防止聚合后只看频数遗漏慢请求信号。此项属于未完成资格的新输入投影修正，旧CPU准备物不混入新契约；不是无损原始日志编码。
3. `choose_witnesses`反复序列化与tokenize相同内容；修复为共享包文本、共享精确成本、共享完整输入预检缓存，预选结果的拼接逐字节等价已测。
4. `P0_MORE_TRUE`每个预算对全部原生候选逐条tokenize。第一轮剖析中AIOPS-2022三档合计236.11秒，AegisLab163.02秒，是该轮最大耗时来源。改为精确批量计算，前缀改变时重新计算后续条目；合成超限/上下文拒绝用例与原逐条算法结果一致。
5. 父版Denum的`selected.extend(row for row in entries if row not in selected)`在扩展过程中执行增长列表的成员检查，全量投影为平方级。RQ3.3局部改成排序后集合去重＋调用父版单行显示投影；不修改RQ1.1。与含重复条目/LOG-R优先的父版投影回归相同。
6. Trace群体对完整spans/links反复扫表；改成request索引，操作名称净化缓存。窗口、状态分组、边计数及并集统计不变。
7. CPU与smoke此前分别按`cpu`/`smoke`种子域挑三例，CPU只准备三例会让smoke访问未准备数据。现在共用CPU三例。效果smoke之前取注册表前三arm，仅旧基线；现在明确覆盖新Witness。
8. 缺校准manifest/准备物此前直到GPU启动后才暴露。现在启动模型前检查；真实历史输入审阅仍需完成，不能伪造manifest或把未运行smoke叫作通过。

第一轮模板化CPU回归在415.01秒内通过111个真实输入条件（包含明确不适用的条件），但AegisLab342.62秒、AIOPS-2022 397.58秒仍慢，因此继续修复结构化模板和P0_MORE。该轮保存在`RQs/RQ3_3/results/witness_v2_numeric_templates_cpu_20260923/`。更早原消息候选测试在`witness_v2_raw_groups_interrupted_20260923/`。均为CPU调试记录，不作为科学效果结果。

### 最终计时与资格状态

当前源码的CPU回归已完成，`results/witness_v2/cpu_qualification.json`记录`status=passed`、总计106.582秒。32项针对性检查、Ruff E9/F及两个shell入口的语法检查均通过。三个case由三个固定独立核心的worker并行完成；不是把三例耗时相加作为队列耗时。

| 数据集 / case | 原完整消息分组准备 | 修复后准备 | 原日志候选→修复后模板组 |
| --- | ---: | ---: | ---: |
| AIOPS-2022 / INC-9293D99C285C | 超过27分钟，未完成 | 89.01秒 | 242,353→5,552 |
| AegisLab / INC-331437929E47 | 377.95秒 | 44.70秒 | 14,343→2,835 |
| AIOPS-2025 / INC-ABA10DF868CA | 19.88秒 | 9.73秒 | 0→0 |

以上为固定三例的实测，不是数据集均值；包含三个预算及对照准备，不包含Solver推理。源日志行数分别为387,352、73,242、0；其中可绑定且符合时间等源契约的行分别为377,352、73,056、0。模板聚合没有另外抽样或只保留前N行；不合格源行与合格行分开计数。

批量分词本身不足以解决单核心瓶颈。最终增加有界精确片段缓存：核查实际tokenizer的normalizer/pre-tokenizer、added tokens和词表，只有证明BPE不能跨越的换行边界才分段计数；不支持的配置退回完整分词。成本按每个模型分别累加，再取最大值。三例各107段实际/边界文本，即每模型321段，与完整编码完全相同；没有用近似计数换速度。384段P0_MORE候选的单核微基准为缓存冷计数0.064秒、完整编码比对0.888秒。最终三预算P0_MORE耗时AIOPS-2022为16.56秒、AegisLab为11.46秒，先前对应236.11和163.02秒。

真实输入检查共111项：80项通过、31项明确不适用。其中16项不满足独立且父版未出现的证据对条件，9项无损截图无法装入注册画布，6项缺少来源支持的事件关系。TPV、P0_MORE_TRUE、W_RAW、W_SEM_EXEC、W_COHORT与W_T在三个case均通过。不能把31项不适用算成已验证可运行，更不能将CPU通过写成模型调用通过。

输入一致性复核：三个case的原TPV文本与PNG、完整父版追加候选、Trace群体以及三档P0_MORE选择，均与第一轮模板化CPU准备物完全一致。日志聚合仅对新Witness投影作显式修正；旧RQ正式结果、父版源码、原per-case数据及模型配方没有修改。中间结构化模板测试保存在`results/witness_v2_structured_templates_cpu_20260923/`，未删除历史调试记录。

### 对RCA速度及剩余设计问题的判断

1. **最主要的剩余冷启动开销是日志聚合。** AIOPS-2022该步骤38.91秒，AegisLab9.20秒。当前不应声称实时RCA已经达成；后续部署应复用按source契约缓存的模板/请求索引，避免每次诊断从原始行重建，也不能把预处理移到计时外就声称系统更快。
2. **实验对照成本不是单方法成本。** 另做单核验证，在公共池已加载、processor已初始化而token成本缓存清空的条件下，只构建默认1024→2048嵌套Witness及双模型预检，不准备P0_MORE或删除消融，分别为AIOPS-2022 5.281秒、AegisLab6.159秒、AIOPS-2025 0.729秒；选择与完整准备一致。该测量不含源读取/统计或Solver推理，不是端到端latency。
3. **图像适用率仍是实验设计风险。** 三例中W_G_SCENE_CAL/W_G_RELAYOUT均因注册截图几何不适用，不能直接把它们带入全量后声称测到了布局效应；需单独审视固定条件的可执行性。此次未通过删事实或偷偷扩画布让检查“通过”。
4. **来源校准仍缺真实审计输入。** 当前`calibration_manifest`为空且没有对应文件；必须完成历史请求/释义来源审核才能执行该smoke。已改为GPU启动前发现，不伪造资格。
5. **本轮未启动GPU smoke或正式实验。** CPU性能修复已经实测；GPU资格及以上校准/适用域问题仍需后续处理。不存在需因本次修复作废的RQ3.3正式推理结果。

## 2026-09-23 GPU smoke发现、修复与补验

本节是后续用户授权GPU smoke及问题修复后的最新记录，替代上节的当前执行状态；先前条目保留其发生时的范围。正式实验未启动。

| 问题 | 已确认原因 | 修复及验证 |
| --- | --- | --- |
| 模型已加载但readiness反复401 | smoke的`/v1/models`探测未带部署认证 | 探测统一携带本地`VLLM_API_KEY`；HTTP错误立即报告。两模型后续真实调用成功，认证/端口占用CPU测试通过 |
| 手动中断却记录`complete`，实际0次调用 | `KeyboardInterrupt`不被`except Exception`捕获，finally保留初始成功状态 | 捕获`BaseException`写入失败并清理自有服务；构造中断测试确认`failed`、0 calls。早期错误报告只保留在旧attempt目录，不作为通过证据 |
| Qwen响应写入后评分崩溃 | RQ入口跳过本地upstream评分shim路径解析，引用不存在的checkout | 入口恢复本地环境解析，CPU preflight及正式请求前实际导入并自测scorer；之后所有已审查响应评分完成 |
| 关系图重排三例全部N/A | graph固定占据半幅/600px，ledger所需高度没有参与空间分配 | 用实际同字体换行结果计算完整ledger高度，将剩余空间分给graph；原PNG尺寸、字号、事实保持。SCENE_CAL/RELAYOUT共同执行此规则，三例两模型RELAYOUT均真实完成 |
| 语义校准尚无真实来源manifest | 此接口虽实现，但缺原SC请求及逐段修正的审计材料 | 新增RQ-local审计脚本；60例×2模型原请求与context公开事实文本全部逐字节对应，登记唯一guide span补丁。原先笼统的midpoint/median/union说明改为按O引用绑定实际估计器 |

前三项是执行/记录缺陷；关系图修复仅影响两个注册的新G scene条件；语义说明修正仅进入显式GUIDE_FIXED/SOURCE_FIXED校准条件。旧RQ3.2、原TPV、模型配方、候选、评分契约、原始数据和正式历史结果均未修改。

### 当前CPU与已完成GPU验证

最终source contract：`9cbf7ade2af79a9ea1e728873cb1535f427221bd91b47ea02a453efa42fe884f`。CPU回归109.59秒通过，32项原针对性测试通过，111个真实条件中86个可执行、25个按注册规则N/A。新增`test_smoke_repairs.py`的3项认证/中断/端口所有权回归通过；Ruff E9/F及shell语法通过。新增审计/回归脚本不修改已冻结runtime源文件，四项已通过smoke无需重跑。

| 实验 | 两模型逻辑单元 | 实际调用 | 总耗时 | 状态 |
| --- | ---: | ---: | ---: | --- |
| exp_semantic_calibration | 18 | 18 | 246.65秒 | complete |
| exp_witness_development | 18 | 14 | 234.50秒 | complete |
| exp_witness_effectiveness | 18 | 18 | 240.61秒 | complete |
| exp_visual_and_diagnostic_mechanisms | 18 | 18 | 236.61秒 | complete |
| exp_witness_locked_generalization | 18 | 18 | 236.20秒 | complete |

开发smoke的4个单元输入相同，按完整请求复用，不是缺失。五项smoke共90个逻辑单元、86次实际调用；所有inputs、outputs、cost、原response、完整conversation及commit引用artifact均已核对，未发现缺失/损坏，86份原响应均为`finish_reason=stop`且完成评分。逐请求检查正文和响应确实进入会话；校准两模型各三例仅guide所在part改变，其余parts及system不变。实际打开三主数据集RELAYOUT PNG：完整ledger在图下方可读、未因排版删减或裁掉字段；AIOPS-2025无调用边的稀疏图保持无边，不制造连接。抽查公开reason，有模型把4/5位实体称为service、把时间先后说成因果或在缺少边时臆断上下游关系的行为，原样保留，这不是通过换答案修复的基础设施问题。smoke不据此声称MRR或推理正确性。

语义校准smoke在来源审计后完成18次调用、耗时246.65秒，没有timeout或基础设施错误。校准manifest不包含数值源修复：没有确认需要修改的具体数值，SOURCE_FIXED与GUIDE_FIXED相同并复用；该相等性在60个开发case的两个模型请求上CPU核对，未增加重复GPU调用。源审计不是对每条raw span的独立重算，也不把不同估计器的数值差异自动判为错误。

剩余25个CPU不适用条件是16个缺独占证据对、6个无受支持事件关系、3个AegisLab事件截图容量不足。它们不再包括主G scene/re-layout。条件式EVENT分支在这三例上未获资格，保持关闭；不将其写为已live验证或偷偷删事实放行。

修复前attempt保留于`witness_v2_pre_auth_fix_20260923`（0 calls）、`witness_v2_scoring_env_fix_20260923`（9 calls）和`witness_v2_geometry_fix_20260923`（44 calls）。加当前86次，共139次已发起调用；它们不混入当前资格与效果统计，但失败和补验消耗仍计入RQ累计调用，不能因换目录重置预算。五项smoke结束后自有vLLM/runner均已退出。未启动正式实验。

本轮smoke的集中审核记录位于`RQs/RQ3_3/results/witness_v2/smokes/review_2026-09-23.md`。当前contract内的98个文件hash均保持匹配；新增审计/回归脚本及文档不改变已测试输入或运行源码。

## 2026-09-23 正式准备退出：继承缓存早于实体类型修复

队列18:45:06启动，18:47:57在`INC-B4C69A1E0459`失败：`ValueError: source and parent candidates differ`。此时18/60准备完成、1失败、41待处理；正式推理尚未开始。不是GPU OOM、请求超时或原始数据丢失。

旧RQ3.1缓存把公开hosting关系中一个ReplicaSet hash为7字符的pod误判为service；当前直接源适配已按公开node_pod_map修正。两侧都是相同104个自然实体，但旧表为50 service/6 node/48 pod，新表为49/6/49，导致17个数字绑定不同。旧RQ3.1修复说明存在不代表当前继承目录中的pickle已更新；必须核对实际身份绑定，不能只看文件名/契约名称。

最小修复只修改RQ3.3的`utils.py`与`main.py`：兼容parent继续继承；全集相同、绑定不同则本RQ定向重建parent和SIRCL输入，绝不把源数据强制映射回旧错误类型。若自然实体全集不同则fail closed。保留历史SC校准与TPV_BRIDGE的原编号、原输入和原评分字典，避免新的隐性错分。旧RQ3.1/RQ3.2 artifacts、模型配置和scorer未改。

验证：45项单元测试、Ruff E9/F通过；18份完成flag对应的身份映射均与公开元数据一致；故障case重建48.08秒、104候选保留，双模型18个编译条件通过。五项原smoke合计90个逻辑请求的完整input identity及评分映射不变，故不重新发起GPU smoke；故障case的新映射仅CPU验证，不能称live通过。原smoke JSON不改；显式迁移保存旧registration/资格快照并引用`contract_migrations/public_metadata_identity_v1/cpu_repair.json`。原18份准备物保留，只将已诊断失败flag存档后重做该case；剩余41例继续正常队列。常规resume不运行该定向检查脚本、不重建完成请求。

## 2026-09-23 20:20 队列再次退出：历史配置hash误拦截超时参数变更（已定位，未修复）

此次screen preparation已60/60完成。Qwen校准第一例`INC-07B8919442D8`的TPV_BRIDGE完成并持久化；构造下一项SC_TEXT_AS_RUN时，`main.compile_unit`把历史`effective_server`和当前字典全等比较，抛出`historical calibration runtime differs; register a separate matched calibration`。runner排空已提交请求后退出，supervisor关闭自有vLLM。server随后出现的EngineDeadError属于SIGTERM关闭后果，不是启动退出原因，未发现此前CUDA OOM。

只读检查全部60×2模型的manifest运行字段：9个Qwen case仅`config_hash`不同；其余51个Qwen和全部60个Gemma一致。进一步在内存中仅将当前统一配置的`common.request_timeout_sec`从300还原到1800，重算hash准确得到历史值`76778801ff0d83aa401b05c9ba66238165043c609dbec004779861210995d84a`；当前值为`6c0f4a9be5d58feabe971bb046713edce54a2d04121f894e5ab5f63304b0d44d`。该变更已有2026-09-20超时策略记录。不能凭字典表面字段相同忽略任意hash差异；本例已有完整配置单字段重构证明，故是运维超时差异被当成科学推理配方差异拦截。

上一轮90个smoke逻辑单元只涉及3个真实case，没有覆盖这9个历史配置case；因此原smoke输入不变检查真实成立，但不足以发现全校准manifest的兼容分组。下一步应在GPU启动前检查全部120条小型运行元数据，并只接受经过证明的超时字段兼容迁移，不删除科学参数检查、不重写历史记录。

本次仅诊断并记录，未修改实验源码或重启。60份准备物与1份已完成正式调用保留；该错误在另一个请求提交前触发，不要求重跑它们。详情见`logs/formal_queue/20260923_201234_run_1790209232248632932.log`及同次server日志。

### 后续授权修复：仅接受完整hash证明的timeout迁移

用户随后明确授权修复并续跑。`calibration_runtime_compatibility`对相同元数据保持原路径；不同情况下要求除hash外字段全等、当前完整配置hash正确且timeout=300，再将配置的唯一timeout字段还原1800并验证其完整hash等于历史值。温度、top-p、模型revision、context、output、未知hash等变化仍fail closed，不是删除hash检查，也没有修改任何统一YAML或历史SC输入。

新增`calibration_runtime_preflight`：队列在GPU启动前检查全部60×2模型来源记录，直接run入口也在提交首个请求前执行小型元数据检查。它不读全量per-case数据或重建完成请求。全部120条检查得到111条完全相同、9条仅timeout迁移。51项CPU单元测试通过，包括错误采样/权重/输出/未知hash拒绝，以及manifest不兼容时不启动GPU。

本次契约更新及兼容证据单独保存于`contract_migrations/calibration_timeout_only_v1/`，保留上一版registration/资格和此前身份修复记录；不改写原smoke报告，不用新名字重复GPU smoke。60份preparation和1份已完成正式结果不重做。

最终定向CPU核查15.90秒通过：原smoke90个完整请求identity不变，故障case的三种SC条件×两模型六个请求均可编译，事实/文本与原登记span修订一致。20:41:03队列PID105361续跑，已跨过此前配置拦截，观察到7/240个Qwen校准逻辑单元完成（含原1个）、5次真实正式调用完成、28次处理中；故障case的GUIDE_FIXED/SOURCE_FIXED结果已落盘，AS_RUN已通过构造/提交。旧完整结果flag保留，未新增资格模型调用；新正式请求仍用300秒timeout。此次不是MRR或实验效果分析。

## 2026-09-23 校准完成后的阶段切换退出：timeout策略未贯通

队列PID105361已完成480/480校准逻辑单元（Qwen238 done、2 request_timeout；Gemma240 done），60/60 preparation和calibration分析已落盘。进入screen时`main.prerequisite`把`failed_units>0`一律解释为基础设施阻断，违背已登记的300秒请求超时记录后继续规则。日志step仍显示上一条analyze，容易误认为分析失败；真正异常发生于下一阶段前置检查。没有证据表明这次由OOM或新的server故障造成。

修复范围：runner/queue完成检查区分request_timeout与非timeout失败；legacy marker仅通过小flag补核失败类别；队列在进入阶段前更新step。顺带修复后续variant/budget/check中的同类全fail拦截，采用所有相关条件共同的可评分集合，记录超时排除名单及数量；不把timeout当模型零分，不新增失败比例放行规则，不放松科学阈值。budget跨三个容量档也共享同一分母，避免静默改变样本组成。原两条timeout flag不解除、不补跑，已有成功结果和准备物不删除。

合成回归覆盖：旧marker下timeout继续、非timeout/未知失败阻断、缺flag/partial阻断、完成单元不加载context或tokenizer、选型共同排除、模型失败仍评分、数据集全部丢失不伪造macro、budget共同分母、check科学门槛不绕过。65项单元测试及Ruff E9/F通过；测试中修正一个仅含`status: complete`而缺registered/terminal计数的旧fixture，实际正式marker原本有正确计数。迁移证据使用`contract_migrations/stage_timeout_continuation_v1/`，原smoke记录保留，不声称新增GPU smoke。

定向CPU核查15.004秒，原90个smoke完整input identity一致；实际480单元小flag阶段检查0.023秒。21:27:38队列PID126989续跑，直接跳过calibration并复用准备物；21:30:37已看到Qwen screen新增14/540个done、无新fail，Gemma等待。模型返回HTTP200、GPU瞬时99%。输入、模型配方、scorer均未修改，原2条timeout保持fail、不补跑。仅确认启动后实际推进，不将短时观察当作全程无故障保证。
