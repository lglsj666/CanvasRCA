# RQ3.4 资格测试问题与处理 — 2026-09-24

**最新状态：相对时钟修复及用户授权的定向 GPU 补验已通过；四项当前资格均为 `passed`，正式实验仍禁用。** 下文按发生顺序保留事故与处理历史，最新结果见末节。

## 原生 Z3 上下文的并发生命周期崩溃

第三项 `exp_verified_visual_binding` 的 Qwen 阶段发起9次调用后，runner突然退出，没有Python traceback。原smoke保留为failed；不把它改成timeout-only或模型质量失败。前两项各18次已完整结束；它们的输入、输出和评分不被重新解释或删除。

内核日志2026-09-24 21:14:32记录 Python PID185627 的signal11，多线程栈指向libz3.so与libc.so.6。vLLM服务日志没有对应引擎错误，随后被smoke supervisor按所属进程组清理。这不是“vLLM显存清空=模型崩溃”，而是输出后CPU核验器原生库崩溃。

实现原来虽用短锁串行执行 `response_audit`，但 `ClaimVerifier` 使用Z3默认全局Context，局部AST在函数退出、锁释放后仍可能析构；Python线程可以并发触及该全局原生上下文。内核栈证实崩溃位置，具体哪一个析构交错没有完整native core回溯；故对精确交错保留推断措辞。

修复：每个ClaimVerifier独立 `z3.Context()`，Solver、Real、RealVal、Bool及tracking sources全部绑定该context；保留输出审计短锁。子进程异常报告增加真实exit code，方便区分Python异常和signal退出。没有改变选择、prompt、图像、模型、采样或评分逻辑。

验证：Ruff通过；35项CPU测试通过，其中新增8线程、32任务×12次求解器创建/销毁。真实CPU资格17.87秒通过，三个case的120个完整请求身份与修复前完全一致。将38份已完整落盘回答重放5次，共190次审计，0.68秒完成，无崩溃；与已有sidecar的契约错误及声明verdict一致。不能把这称为穷尽所有并发状态。

## 原始结果与调用预算

第三项耗时135.87秒，9次请求已计数。两份完整回答已有outputs/conversation/completion和calls.sqlite完成记录；另7份只保留流式partial，不能拼成完整答案，也不能假装未发起调用。未完成本阶段Gemma资格。

`contract_migrations/z3_context_v1/`保留原registration、CPU资格及精确源码迁移；只允许此次三文件修复，不通用接受源码漂移。原smoke报告与失败记录不覆盖，既有调用计数不重置。

若要把第三项原计划18个单元补齐，复用两份完整回答仍需7个Qwen＋9个Gemma＝最多16次新请求，本项累计25次，超过原18次逻辑smoke上限。因此不能自行换目录当新smoke绕过。已向用户请求一次性补验授权（≤16新增calls、独立≤600秒修复窗口）；未获授权前不提交这些请求。第四项是原先独立登记的实验资格，不用于冒充第三项已经修复并完整live通过。

所有产物：`RQs/RQ3_4/results/integrated_v1/`。本轮不启动正式实验。

## 一次性补验授权

2026-09-24 用户明确回复“我批准这次补验”。因此按上述16次新增、累计25次、独立600秒范围执行，仅限第三项。原failed报告不覆盖；原stage完整副本保存在 `contract_migrations/authorized_smoke_repair_v1/failed_stage_before/`。其他smoke调用上限和正式执行禁用状态不变。

补验已完成：新增16次、复用2份完整回答，18个单元全部完成，250.50秒；第三项累计25次包含原7次中断。两份原完成output逐字节保持一致；九对case×arm在两个模型下的公开输入完全一致。36项CPU测试和120个完整请求等价检查通过。原失败报告保留，修复报告为 `smokes/exp_verified_visual_binding_repair_v1.json`。没有新基础设施失败或Z3崩溃；vLLM启动的optional deep_gemm导入警告后，冻结的triton运行路径正常完成。没有新attention、训练或正式调用，测试服务已退出。

输出审阅：18份回答均可解析且候选ID合法；其中4份回答的5处字面类型称呼错误被sidecar捕获（例如把node称为service、把pod称为service或node）。4处调用边声明是unknown而非自动判假。另有答案列表与reason重点不一致、由时间先后过强推断根因等模型行为。全部保留，不修改原排名，不以smoke准确率调参。有限字面核验不能宣称发现全部错误或证明因果推理。

## 新发现：追加指标暴露绝对启动时间，正式资格仍阻塞

在补验后的实际prompt审阅中，确认 AIOPS-2022 的 `INC-0986D6C54EC6` 将两个pod的 `container_start_time_seconds` 作为追加观测显示，reference/current median为 **1647145400.0**。这是绝对Unix启动时间，而不是duration；目前没有证据表明它等于注入时间或暴露了ground truth，但违反模型可见输入排除绝对时钟的项目契约。不能因为来自public telemetry就自动视为输入安全。

核查本轮全部72份已完成逻辑单元：12份包含此字段，均为该case；因子smoke4份、图文绑定smoke6份、锁定复核smoke2份。契约smoke未发现此项。机器可追溯清单：`smokes/absolute_clock_input_audit.json`。不据此推断更早全部实验都受影响；历史原始记录不改写。

新增时间字段来自RQ3.4追加观测，不是这次Z3/context修复引入的。原CPU检查证明的是修复前后输入相同，没有识别这种**数值字段承载时钟**的情况；这解释了为何静态/CPU全通过仍有真实输入审阅问题。后三项当前资格标为 `blocked_input_privacy`，运行报告的完成事实保留。

下一步需要RQ3.4-local相对时钟投影或明确登记的clock指标排除策略，并针对这类字段增加回归。必须保留restart等有效变化信号，不按数字大小误删memory/bytes等普通大数；确定修复后的实际输入变化范围，再安排有必要的定向资格。**本次16次新增授权已用完，不自行扩大GPU补验预算；正式实验仍禁用。** 本轮尚未修改该科学输入投影。

## 已修复：共同相对时钟投影，CPU 通过，GPU 待定向补验

用户随后授权修复输入问题。新增 RQ3.4-local `relative_clock_v1`，登记三类有来源语义的秒时钟：`container_start_time_seconds`、`container_last_seen`、`istio_agent_process_start_time_seconds`。使用同 case 完整公共观测中这些指标有限 reference/current median 的最小值作为共同原点，仅对显示值做平移；不使用标签、注入时间或每实体独立原点。原点的绝对数值不进入请求。变更明确限于显示投影，原始统计、排名、样本数、MAD/std 和观测窗口不改。

启动先后、实体间时间差、前后变化均保留。例如追加证据中的 `1647145400.0` 在本样例变为 `600.0 relative_clock_seconds`，并非删除启动指标或把它当普通 duration。相对时钟与观测窗口分开标注。未知时钟语义、单位或额外数值字段在请求前报错，不按数值大小删除内存/字节等普通大数。

第一次真实 CPU 回归进一步捕获 **SIRCL CSV 中的 `container_last_seen`**：早前只查启动字段的 12 单元清单不完整。为三个 SIRCL 条件共同增加同原点适配，只平移 baseline/current mean，标准差与其他行不变。比如 `10496.container_last_seen` 修复后为 `645037.0 → 646237.0`，标准差两侧均为 `345.98`。因此本轮 `SIRCL_NATIVE` 是保留原选择和原契约的时钟安全适配，不再声称受影响请求与旧原生文本逐字节相同；三个 SIRCL 条件仍共享这一投影。原 SIRCL/RQ3.3 源码和旧推理结果不改。

验证与范围：

- Ruff、shell 语法及 **42 项单元测试**通过，包括共同平移、源数据不变、边界值、CSV 均值/标准差、旧 preparation 拒绝和 Z3 并发回归。
- 原三个资格 cases 的 **120 个完整请求**全部通过 CPU 检查；96 个请求身份不变，24 个发生必要变化，均属于同一 AIOPS-2022 case。三 case 的 12 组 P/H 选择集合不变，TPV/MORE 完整请求不变，冻结 G 图不变。
- 对已经执行的 smoke，实际影响 **18 个逻辑单元**：契约 6、因子 4、图文绑定 6、锁定复核 2。24 是 CPU 全 arm×model 矩阵中的变化数，18 是其中已执行 smoke 的单元数，不能混用；跨阶段相同请求的合法复用还可能降低未来新增调用量。
- CPU 资格检查本身 **16.15 秒**；缓存投影修复及检查阶段 **53.64 秒**（不包含此前归档复制）。复用三个已有完整证据池和图像，没有重做全量 raw/per-case preparation。
- 历史结果、conversation、原失败和 partial 均保留。当前调用数仍为历史 3,300＋72 完成＋7 中断＝**3,379**，本轮零新增模型调用，无训练、无 attention、无正式实验。

本次不是输入不变的运维修复，因此不能拿旧 GPU 完成记录宣称新输入已通过 GPU 资格。四项当前资格为 `cpu_fixed_gpu_pending`；此前 16 次补验授权已用完，本轮没有自行开启另一轮补验。只需按完整请求变化定位后续资格，不据此重跑旧全量实验。

权威产物：`RQs/RQ3_4/results/integrated_v1/repairs/relative_clock_v1/` 下的 `migration.json`、`cpu_qualification.json`、`final_consistency_audit.json` 与 `previous/`。首次被 SIRCL 时钟拦下的 CPU 尝试保留在相邻 `relative_clock_v1_first_cpu_attempt/`。新契约 `ffd6e79eb3ed84278a2392447feb50db649bea81cabfc0e3da0a36cbfda2de11`；旧契约及输入快照完整留存，不重置调用计数。

## 用户授权定向 GPU 补验完成

用户明确要求继续定向GPU补验。新增独立补验入口，只重跑改变输入；45项CPU回归和120请求身份等价检查通过。第一次入口错误地把`repair="clock"`传为`True`，进入旧图文专用授权分支，启动Qwen后退出但0请求发出；已修正传递并新增driver测试。原失败105.31秒计入契约实验600秒总预算，不掩盖或重置；失败日志独立保存。

最终新增16次、跨实验同模型/case/完整请求复用2次，另54个未改输入直接引用，四项72逻辑单元齐全。契约、因子、图文补验成功执行分别209.09、210.89、211.19秒；锁定复核全部复用，未启动服务器。契约计入首轮失败后314.40秒，仍低于600。总累计3,395次，原7个中断仍在账，无超时/崩溃/写盘错误，所有测试服务已退出。

实际prompt、PNG、raw、conversation、有效配置和成本核查通过；时钟安全投影与CPU一致，36对跨模型公开输入相同。16份新回答全部正常`stop`、无截断；1份原生SIRCL含`node-4176`非法候选，6份回答有12处字面实体类型错误，保留为模型结果。审阅还发现错误3-sigma判断、`+23m`早于`+22m`及无证据调用边等reason问题：当前核验器不能覆盖全部自然语言推理，不能写成“补验通过=诊断正确”。没有据此改排名或重采样。

完整审阅：[定向补验记录](../../RQs/RQ3_4/results/integrated_v1/repairs/relative_clock_gpu_v1/review.md)。当前四项资格为passed，但仅限注册smoke路径，正式执行仍禁用；历史failed报告及输入/输出/flags不改写。最新contract为`b6b8da780cf8141b844db782873647b84e9a729b149092697d9234eef77a132b`。
