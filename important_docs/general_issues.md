# CanvasRCA 综合问题与历史解决方案

整理日期：2026-10-20（America/Toronto）。本文件汇总并替代原 `docs/issues/` 的全部记录，覆盖 RQ1.1、旧 RQ2、RQ2.1、RQ3 系列相关资格记录、RQ4.3、RQ4.5 Nibi 运行调查及 RQ4.7 视觉操作问题。

**分类遵循用户最新口径：修复通过 CPU 检查即算已解决。** 对于运维恢复、用户要求的退役或清理，以原记录中的实际完成证据判断。实验退役、删除结果、取消不可用条件不等于修好了原科学设计，分别注明。

本次核对了原目录的 **25 份 Markdown、4 份 JSON 和 1 份压缩 JSON 校验清单，共 30 个文件**。这里只保存问题、处理方法、证据范围和来源索引，不复制原始日志、回答或已删除实验数据。旧文件中的“当前”“待修复”按其后续补记更新；没有后续记录的，不推测已经修好。结论是历史档案审计，不是本次重新运行回归，也不是 Nibi 的实时状态检查。

QA 的题目、提示、可见性和评分细节继续由 [qa_issues_constraints.md](qa_issues_constraints.md) 管理。本文件仅保留原目录中早期 QA 问题的迁移摘要；不复制该专项文档的 RQ4.1—RQ4.7 问题清单。以下两部分只记录已发生的问题、实际解决方案与确实存在的记录缺口，不把尚未证实的推测登记为故障。

## 第一部分：已经解决的问题及当时采用的方案

### A. 早期渲染、记录与运行基础设施

<a id="r01"></a>
**R01｜RQ1.1：长 Denum 日志模板导致整个 L 区放不下任何完整记录。**

- **问题及原因：** 固定日志视口不能容纳某条模板的全部换行；完整行准入策略最终留下零行，准备阶段失败，尚未进入推理。
- **当时方案：** v7 对显示模板登记 160 字符上限，以确定性前缀加短 SHA256 标识表示长模板；文本和视觉获得相同的有界内容、截断标记、模板哈希及数值摘要，规范图仍保留完整模板。没有缩小整张图或静默裁切。
- **解决依据与限制：** 原失败病例重新编译后出现完整可见日志行，语义及几何检查通过。这是当时登记的有损显示投影，不应误称为保留全部日志文字，也不自动成为新实验的允许规则。来源：[F04](#src-f04)。

<a id="r02"></a>
**R02｜RQ1.1：并发首次初始化 tokenizer 触发 Transformers 懒加载竞态。**

- **问题：** 模型已返回，但 attention 文本映射阶段出现 `cannot import name AutoTokenizer`，无法完成记录提交。
- **方案：** supervisor 在创建四个病例线程之前，预先初始化同一个已登记的 attention 映射 tokenizer；后续共享缓存，token 映射定义不变。
- **依据：** 修复版本的检查及后续实际执行没有再次出现该导入错误。范围是初始化时序，不是改变模型或分词器。来源：[F04](#src-f04)。

<a id="r03"></a>
**R03｜RQ1.1：attention 遇到抢占重算后重复采集位置，异常杀死模型服务，runner 又连续写入失败。**

- **问题：** KV 压力下重算 prompt，探针将同一绝对位置重复追加并在 forward 内抛异常；缺少共享服务熔断器，之后产生 2,842 个基础设施错误记录。
- **方案：** V4 按绝对 prompt 位置只保留第一次 K/V 观察，重放另计；探针故障限于单请求诊断，不再杀死整个 forward。runner 对 EngineDead/致命传输错误启用阶段熔断，停止提交、排空写入、保存失败摘要并阻止后续阶段启动。
- **依据：** 修复后采集、终态和故障边界检查通过。旧失败尝试不作为有效结果；已完成的准备材料不因服务事故重建。来源：[F04](#src-f04)。

<a id="r04"></a>
**R04｜旧 RQ2：短生命周期 shell 启动后台任务，shell 退出后任务消失；人工暂停后残留父进程。**

- **方案：** 改用持久化执行会话，同一 run ID 从已完成记录续跑；暂停时确认服务、父子进程状态，仅终止本实验所属进程组，必要时发第二次终止信号。
- **依据：** 原记录明确恢复或清理完成，没有把已有成功调用重答。属于运行生命周期处理，不是输入或评分修复。来源：[F06](#src-f06)。

<a id="r05"></a>
**R05｜旧 RQ2：少量请求读流停滞，目标级错误率很低却使整病例配对排除超标。**

- **问题：** 部分请求只有 1–37 字符或少量流式片段后停滞；模型服务仍处理其他请求。按完整病例排除时，可超过原 5% 门槛，不能只看调用级错误率。
- **方案：** 暂停父调度器以阻止用不完整矩阵选型，让当前子阶段排空；保留失败记录及哈希，只用原 run ID、输入和配置补齐未完成目标。已提交的错误排名、非法候选或达到输出长度上限的回答不重采样。
- **依据：** 文档记录了 25、21、102、8 等不同阶段的定向完成批次，最终各注册阶段无遗漏；这是完成性恢复。没有定位到所有读流停滞的底层根因，也没有证明以后不再超时。来源：[F06](#src-f06)。

<a id="r06"></a>
**R06｜旧 RQ2：Trace 列重叠、贪心 packing 拒绝可行布局、坐标缩放错误，以及硬编码的“裁切检查通过”。**

- **问题：** D031 的 count 与 exclusive-p95 文本在真实 PNG 中重叠；D036/D041 的贪心装箱失败；嵌套图元仍使用逻辑坐标，而卡片采用光栅坐标；固定 `clipping_audit: passed` 没有检测这些问题。
- **方案：** 按真实字形宽度决定 Trace 是否改成堆叠行；为 first-fit 增加有界确定性回溯；所有图元转换到最终光栅坐标；用实际几何检查替换固定 verdict；拓扑表列宽与标签自适应，放不下显式失败。
- **依据：** 当时 33 项检查及 199 病例×48设计、9,552 张图的准备审核通过，另看了九张原生分辨率图。旧 D031 选型和受影响独立阶段判无效，后继重新选择；修复不追溯改变旧图有效性。来源：[F06](#src-f06)、[F07](#src-f07)。

<a id="r07"></a>
**R07｜旧 RQ2：测试准备缓存缺少后来增加的 dense_packet。**

- **方案：** 将共享测试准备版本从 v5 升为 v9，用同一 canonical compiler 重新准备三个固定资格病例；不改已有正式准备或模型设置。
- **依据：** 新版本完整执行了之前缺失的 DENSE_M24 路径。原失败发生在生成请求前，不计作模型回答失败。来源：[F06](#src-f06)。

<a id="r08"></a>
**R08｜旧 RQ2：磁盘被可再生成缓存占满；失败调用遗留孤立 attention。**

- **问题：** WSL 文件系统用满，直接证据指向约 193 GB 的 `eda_cache/` pickle；不能把这起事故全部归咎于 attention。磁盘满时还出现写了部分探针、未写成轨迹的孤立对象。
- **方案：** 停止自有服务和提交，删除并重建可再生成缓存，保留 canonical 数据和科学记录；失败记录、部分探针单独归档；只续跑未完成目标，按轨迹引用核对探针数量。
- **依据：** 原记录恢复 193 GB 空间；最终 tool 阶段 7,680 条完整轨迹对应 7,680 个引用探针，没有孤立项。一次未能写出的对话和一次未采集到的可选 attention 不能由恢复补造，见第二部分。来源：[F06](#src-f06)。

### B. 选择、身份、输入和持久化契约

<a id="r09"></a>
**R09｜RQ2.1：候选校验、SDK 隐式重试、调用前输入保存及终态/SQL 崩溃窗口。**

- **当时修复：** 非法候选按继承的整份排序失败规则处理；SDK 隐式重试关闭，每次尝试进入统一账本；请求发出前保存完整输入；终态文件已写而 SQL 尚未更新时先对账再调度别名；真实重复使用独立身份。
- **依据：** 42 项 CPU 检查覆盖恢复、缓存、预算等，1,920 个历史 T/V 桥梁分数保持不变。这里记录旧评分策略的实现一致性，不将其当作当前所有任务的最佳宽容评分方案。来源：[F05](#src-f05)。

<a id="r10"></a>
**R10｜RQ2.1：文本行高估计、某种编码不可行误阻断其他编码、卡片边角颜色误作背景。**

- **方案：** 行高按真实换行和字形测量；每种编码独立判断完整内容能否容纳；必须完成实际重绘才能提交。密度压缩的背景检测改为采样主色，不能只读带边框的角点。
- **依据：** 基础 CPU 检查及两项密度回归通过；原卡片的内容条带可逆复原，真实样例产生可验证的像素变化。真实放不下的 S0 日志仍标不可行，未被冒充已修好。来源：[F05](#src-f05)。

<a id="r11"></a>
**R11｜RQ3.2：冗余噪声消融向固定 L 卡片塞入过多长日志。**

- **方案：** `region_capped_v2` 保留固定且不看标签的 reservoir 顺序，最多十二条新增事实、其中最多两条日志，其余从后续 M/R 补齐；两种表示共同版本化。没有扩大受控画布。
- **依据：** 原规则 100 个机制病例有五个容量失败；新规则全部可构造，其中 99 例新增十二条、一例十一条。不同输入重新登记，完全相同请求才复用。来源：[F14](#src-f14)。

<a id="r12"></a>
**R12｜RQ3.2：无限反序列化缓存导致主机 OOM。**

- **问题：** `ContextStore` 永久保存全部访问过的病例，约 11.35 GiB 磁盘 pickle 膨胀为 Python 对象；内核记录被杀进程约 45.1 GiB 匿名 RSS。不是 CUDA OOM，也不能仅凭 Matplotlib 警告归因。
- **方案：** 改为线程安全、最多八病例的 LRU，保留邻近 arm 复用，驱逐后可重新读取。
- **依据：** 480 个真实上下文扫描 60.23 秒，缓存始终八例、最终 RSS 约 1.63 GiB；恢复期 36 个在途 worker 的 runner RSS 约 5.2 GB。原已提交单元先读小标记跳过。八例是当时实现，不是本文件新设全项目内存限制。来源：[F14](#src-f14)。

<a id="r13"></a>
**R13｜RQ3.2：OOM 后 ledger 留在 started；一个真实 P0_MORE 请求超上下文。**

- **方案：** 确认旧 owner 已停止后，仅对本次范围的 `started` 行标为 `interrupted`，恢复尝试继续计费；错误失败标记以追加 tombstone 解除。超上下文则使用当时已授权的文本专用规则，逆排序整条移除证据，至少保留每个已存在模态一条，保存全部移除 ID 和新请求身份。
- **依据：** 实际恢复跨过失败单元，成功结果不重建。超限修复明确改变了那份文本证据，不能称无损或挪用于当前纯视觉方案。来源：[F14](#src-f14)。

<a id="r14"></a>
**R14｜RQ3.3：见证字段、来源连接、对照事实和绑定规则的实现偏差。**

- **已实施方案：** 新见证从完整公共池建立而不改 TPV；P0_MORE 沿原父版顺序；counter 按阶段计算 reset-adjusted 增量；没有请求 ID 不生成“请求数 0”；按 `(trace_id, span_id)` 唯一身份连接；未知语义不编造定义；不同量纲不按原数值混排。
- **共同对照修复：** 联合/边际使用同一请求并集，pooled median 从原请求重算；删目标观测时删所有副本和关联计数；空包保留共同背景；LOCAL/REMOTE caption 多重集一致；预算进入任务身份；typed ID、图像和评分映射同步变化。
- **依据：** 后续 CPU 检查覆盖这些合成契约和真实请求；对不满足来源条件的分支保留 N/A，不把静态实现当作所有分支可运行。来源：[F15](#src-f15)。

<a id="r15"></a>
**R15｜RQ3.3：按完整日志消息分组导致候选爆炸；分词、Denum 去重和 Trace 扫描重复计算。**

- **方案：** 结构化键序规范化、Denum 数值模板与阶段统计；保留源行/计数和诊断数值摘要，并让普通数值槽变化进入 LIVENESS 判断。共享精确包文本及成本，批量分词；只在验证 BPE 不跨越的换行边界使用片段缓存，不适用时回到完整分词；增长列表去重改集合；Trace 建 request 索引，缓存操作名清洗。
- **依据：** 固定 A22 例日志组 242,353→5,552，准备从超过 27 分钟未完成降至 89.01 秒；Aegis 377.95→44.70 秒；三例并行完整资格 106.58 秒。321 段/模型的精确计数与完整编码一致。日志模板化属于新 Witness 的投影改变，不是原始日志的无损编码；冷日志聚合仍有开销，见 U07。来源：[F15](#src-f15)。

<a id="r16"></a>
**R16｜RQ3.3：资格病例不一致、缺前置审计、认证探测 401、人工中断误记 complete、评分环境失配。**

- **方案：** CPU 与后续资格共用固定三例，并覆盖新 Witness；来源 manifest 在服务启动前检查。readiness 带本地认证且 HTTP 错误显式报告；捕获 `BaseException`，中断写失败并清理自有服务；当时入口恢复本地 upstream scorer 的环境解析，并在提交前实际导入自测。
- **依据：** 认证、中断、端口所有权回归通过；伪造的 0-call complete 被保留为失败历史而非通过证据。**评分环境方案是历史事实；新代码的评分导入仍以 `src/scorer` 为准，不能恢复旧路径。** 来源：[F15](#src-f15)。

<a id="r17"></a>
**R17｜RQ3.3：G 场景分配空间不足，以及旧统计阅读指南与实际估计器不符。**

- **方案：** 用同字体真实换行计算完整 ledger 高度，剩余空间给 graph；校准审计核对 60病例×2模型原请求与公开上下文，限定唯一 guide span，按 O 引用说明实际估计器，撤掉笼统 midpoint/median/union 说明。
- **依据：** 三例重排均可执行，最终 111 个真实条件中 86 可构造、25 N/A。没有确认具体数值错误时，SOURCE_FIXED 与 GUIDE_FIXED 相同并复用；该审计不是全 raw span 重算。来源：[F15](#src-f15)。

<a id="r18"></a>
**R18｜RQ3.3：继承缓存早于 pod 类型修复，公开实体相同而数字绑定不同。**

- **问题：** 104 个自然实体全集相同，但旧缓存把一个 ReplicaSet hash 为七字符的 pod 当 service，造成 17 个数字绑定变化。
- **方案：** 全集相同且绑定不同的病例在本 RQ 定向重建 parent/SIRCL；全集不同仍报错。历史 SC 校准及 TPV_BRIDGE 保留原输入与原评分映射，不强行套新编号。
- **依据：** 45 项测试、失败病例两模型十八编译条件通过；原九十资格请求身份和评分映射不变，已有十八份准备物保留。来源：[F15](#src-f15)。

<a id="r19"></a>
**R19｜RQ3.3：运维 timeout 改动被误认成科学配方变化；阶段完成检查又把允许保留的 timeout 一律阻断。**

- **方案：** 只接受有完整配置哈希证明的 1800→300 秒单字段迁移，其他模型/采样/context 变化仍拒绝；GPU 启动前检查全部 120 条小元数据。阶段检查区分 request_timeout 与其他基础设施失败，legacy marker 读小 flag 核实类别；在进入阶段前更新 step。统计族采用共同可评分分母，缺失不伪造零分或零成本。
- **依据：** 120条中111完全一致、9仅timeout；相应51/65项CPU测试、原90请求身份检查通过，实际队列跨过两个阻断点。原超时结果未被自动补答。来源：[F15](#src-f15)。

### C. 原生库、时钟、序列化与资格状态

<a id="r20"></a>
**R20｜RQ3.4：Z3 默认全局 Context 的并发生命周期崩溃。**

- **问题：** runner signal11，原生栈指向 libz3；短锁并未覆盖函数退出后 AST 析构。具体析构交错没有完整 core，原文仅将其作为机制解释。
- **方案：** 每个 verifier 使用独立 `z3.Context()`，所有 Solver/Real/Bool/常量绑定同一实例，保留短锁；子进程记录真实退出码。
- **依据：** 35项CPU测试含8线程×32任务×12次创建销毁；190次原回答离线审计重放通过，120请求身份不变。故障来源是 CPU 核验器，不是服务清理后的 EngineDead。来源：[F16](#src-f16)。

<a id="r21"></a>
**R21｜RQ3.4—RQ3.5：公共数值中仍含绝对启动、last_seen 和 last-GC 时间。**

- **问题：** 字段来自公共遥测并不使绝对时钟自动合规；首轮 guard 漏掉 SIRCL CSV 的 `container_last_seen`，之后又漏掉 `istio_agent_go_memstats_last_gc_time_seconds`。
- **方案：** 对来源确认的秒时钟使用病例共享公开原点做显示平移，原点不送模型；仅修改均值/median及对应单位，不改标准差、选择、样本和实体间差值。最后单独将 last-GC 加入语义白名单与 guard，在请求构造时适配，不重建旧上下文。
- **依据：** RQ3.4 120请求核对；RQ3.5 60病例/1,200输入中恰有51份受 last-GC 影响、1,149不变，相应CPU回归通过。这里只证实登记字段的修复，不宣称所有未知时间格式已被穷尽。来源：[F16](#src-f16)、[F17](#src-f17)。

<a id="r22"></a>
**R22｜RQ3.4：修复入口把字符串 clock 传成 True，进入错误授权分支。**

- **方案与依据：** 修正参数传递并增加 driver 测试；该错误发生在启动服务后、模型请求前，原失败时间和记录保留，没有通过重置预算掩盖它。来源：[F16](#src-f16)。

<a id="r23"></a>
**R23｜RQ3.5：hash 原语不一致、错误读取 SIRCL 的第一个 part、G 图空间浪费和审计侧虚增 J 事实。**

- **方案：** binder 使用统一 `stable_hash`；按唯一 evidence header 找正文而非取 part0，保留时钟阅读句和任务边界；固定槽中放入真实 G 图与边来源裁片，两种 G 条件共享投影；只有 J 真正出现在输入图中时，审计 sidecar 才含 J 事实。
- **依据：** 13项CPU测试及三例20条件×2processor、120完整输入检查。合成 scope 检查不等于真实样例中存在 scope 包。来源：[F17](#src-f17)。

<a id="r24"></a>
**R24｜RQ3.5：候选重复呈现；旧资格/授权字段被带到已改输入的新版本。**

- **方案：** 删除两个 crossed P0 条件正文中的重复 `candidate_set`，保留同一完整候选段落；变更逻辑身份；review 拒绝把旧合同提升为新输入资格，未改变分支用输入等价证明继承。修复发布最后写完成标记，保留上一版资格；后续 metadata 更改不再继承旧 repair 的 approval 与 units。
- **依据：** 两次120请求比较分别仅12变化、再0变化；补充回归确认旧资格不会错误放行。来源：[F17](#src-f17)。

<a id="r25"></a>
**R25｜RQ3.5：逐行 JSON 包装把原本可容纳的 SIRCL 文本撑出上下文。**

- **问题：** 重复键与转义使目标 crossed 请求达到 Qwen 38,418/Gemma 40,691 输入 token；原生内容本可容纳。三例资格未覆盖此正式病例。
- **方案：** 四个 crossed 臂共同换成逐区域 verbatim blocks，保留所有记录；新增全 screen 的CPU容量/事实等价检查，旧输入完成标记不能跳过新身份。改变输入的旧结果不混入新统计。
- **依据：** 60例×19条件×2processor、2,280检查通过；触发请求降为29,471/31,687，未删事实、未调大context或削减输出预算。来源：[F17](#src-f17)。

<a id="r26"></a>
**R26｜RQ3.5：直接 run 跳过基础设施 fail、暂停竞态、重复 p95 计算及分析字段不足。**

- **方案：** direct run 与 queue 对基础设施失败采用同一阻断逻辑；等待并发额度后再次检查停止信号，拒绝未知模型；memoize每个实体/操作reference p95；补注册macro、成本/故障/粒度汇总、次要比较、事件组敏感性和共同配对集合，不给缺失结果造零成本。
- **依据：** 24项针对性CPU测试通过，120请求中只登记的24个 crossed身份改变。后来的 granularity 内容错误另见 R29/U09，不能用“加了汇总字段”冒充所有汇总正确。来源：[F17](#src-f17)。

<a id="r27"></a>
**R27｜RQ3.6：父版 Trace 原值是微秒，显示字段却写毫秒；binder 和 post-response metadata 又不匹配。**

- **方案：** 依据来源链只修三个耗时字段后缀及复合单位，保留数值、排序、平滑、选择和原图；projection采用统一digest；补 `projection.image_hashes` 并将真实 sidecar 接口纳入CPU回归。
- **依据：** 六项单测及66请求CPU检查；九个已保存答案的后处理失败通过核对请求后重建 audit/完成标记恢复，**没有重新推理**。单位标签修复不追溯覆盖历史输入。来源：[F20](#src-f20)。

<a id="r28"></a>
**R28｜RQ3.6：scope/peer语义混用、标签方向与容量不足、readiness认证遗漏，以及没有实际差异的实验条件。**

- **方案：** peer限制同语义/单位/窗口/role和公共归属，宿主相关观测单列；语义贴实体框，箭头止于边界、自环单画；ledger双列。模型调用前统一扩大当时登记画布、保持事实与字号，过滤不符合登记语义的配置/时钟关联项。正式探测复用认证接口，401/403立即失败；CPU扩大到180例。
- **重复条件处理：** 文本T_ID/T_BIND草稿相同则修编译；HP_CROSSHOST与HOST_PEER在180例完全相同的两个条件在调用前取消，记录为取消，不算有效比较。
- **依据：** v2每组13项CPU测试、三例204请求及各180例容量检查通过，认证/实际输入差异有记录。来源：[F21](#src-f21)、[F19](#src-f19)。

<a id="r29"></a>
**R29｜RQ3.5 报告：granularity 误保存整张实体类型映射。**

- **已解决部分：** 独立离线报告改从 evaluator-private accepted roots 及其类型推导根因粒度，原逐例评分不变，错误 map 不再当分类变量。
- **边界：** 解决的是该次报告汇总，未见原 runtime summary 字段修复的记录；该剩余部分列于 U09。来源：[F17](#src-f17)。

### D. 后续准备、绘图、迁移与上下文

<a id="r30"></a>
**R30｜RQ3.7：父版 k/M/G 数字、OTel 指标白名单和固定 .partial 文件名。**

- **方案：** 按父版十进制定义精确展开缩写；只补来源核实的本RQ指标语义，未知单位不猜；并发保存采用共享 `atomic_write` 的独立临时文件。
- **依据：** 17项CPU测试与三例63目标通过，含并发保存；旧RQ源码不改。来源：[F23](#src-f23)。

<a id="r31"></a>
**R31｜RQ3.7：历史引用、计数和恢复路径有重复推理或错误归因隐患。**

- **已落实方案：** 从终态引用解析实际原回答，不把无独立 outputs 副本当缺失；历史参考不可用则保留无分数而不自动调用；完整请求与scorer兼容才复用；同输入timeout别名不重答；REPEAT独立；共享原调用账本，避免重复导入历史计数；重试prompt按完成记录定位。
- **依据与范围：** 静态实现记录及之后A/B CPU资格通过。缺失参考比较单列交集/未知界限，固定校正族不因缺数据缩小。原结果未被重新包装成新独立样本。来源：[F23](#src-f23)。

<a id="r32"></a>
**R32｜RQ3.7 C：冷路径缺 `selections` 中间层；嵌套 WiredTiger 日志时钟漏清洗；准备失败后总状态仍 preparing。**

- **方案：** 冷准备先执行原有 `choose_parent_tail` 的1024→2048累积步骤，再建 integrated context并原子提交。对已确认 WiredTiger `[epoch_seconds:microseconds]` 前缀，用病例共同公开秒原点平移，微秒分量单列，非时钟字段不变；未知格式仍拒绝。helper记录失败病例及实际字段，并把总状态更新为failed。
- **依据：** 冷路径五例/五臂/两processor、50请求通过；时钟修复八项CPU测试、故障病例十请求通过，430小型公共view定向检查无剩余同类guard失败。没有将已有250个完成上下文重建。来源：[F22](#src-f22)。

<a id="r33"></a>
**R33｜RQ3.8 Nibi：auto选中不同GDN后端、脚本提前终止启动、零调用却被标通过。**

- **问题：** Hopper走FlashInfer大规模JIT，本地走Triton；权重已加载不等于API就绪。旧supervisor时间限制早于Slurm分配上限，timeout-only把0推理也算通过。
- **方案：** 独立Nibi profile显式选Triton；按用户要求移除该smoke提前终止和提前信号；状态分complete/incomplete/failed，以真实请求与产物确认执行。原零调用记录不追溯升格。
- **依据：** CPU job22930024的68项回归及24容量检查通过。不能据此保证所有Nibi启动都低于五分钟；历史脚本时间数字不是本文件新设限制。来源：[F24](#src-f24)。

<a id="r34"></a>
**R34｜RQ3.8 Nibi：launcher/probe 使用动态端口，tokenizer和生成client仍访问8000；异常后监控遗留running。**

- **方案：** RQ-local `bind_client_endpoint`和shell统一URL，attestation核对实际client端点；预检打印无敏感信息的异常类型/HTTP状态；supervisor异常路径写failed。补双模型/双端口和异常终态回归。
- **依据：** 后继实际请求及产物记录证明端口错配已消除。失败发生在generation账本开始前，不能把这类预检失败计成模型答错。来源：[F24](#src-f24)。

<a id="r35"></a>
**R35｜RQ3.8：图像加冗余文本超上下文；多源rsync把缓存压平到仓库根。**

- **容量方案：** v7对各臂共同文本做可核对的无损去重/紧凑关系编码，保留有意TEXT_DUP定义及原PNG；66个双processor检查通过，失败请求35,011→27,769输入token。
- **同步方案：** 停止错误传输，仅清除已确认误建副本；多源用`rsync -aR --partial`保留层级，指定单目录目标父路径，旧绝对ledger软链用`-aL`传实际字节；按消费者roster查必需文件。
- **依据：** 两路同步退出0，840例依赖轻量存在性检查缺失0。约31GB误传副本不是有效准备物；存在性不等于逐内容哈希验证。来源：[F24](#src-f24)。

<a id="r36"></a>
**R36｜RQ3.10 v1：64格采样覆盖规则与原生采集密度不符，全140例失去主要干预。**

- **方案：** v2从公开时钟正间隔推断原生cadence，用完整阶段的预期原生槽计算覆盖，保留80%覆盖等质量条件，不插值；核实实际资源键，必要时在既有实体中按固定hash补资源锚点；紧凑共享单元几何替代固定480px空白槽。
- **依据：** 140例、280图完整CPU容量通过，最大29,411输入token；A22有23/60例可测。原v1仍是0资格、0模型调用的阻塞版本，不改写为通过。
- **限制：** A25与Aegis的实例活动/负证据适用性没有一并解决，见U08。后继方案详情已从保留的[协议](../RQs/RQ3_10/descriptions/RQ3_10_experiments.md)核实。来源：[F08](#src-f08)。

<a id="r37"></a>
**R37｜RQ3.14：实验私有绘图、图旁重复整份摘要增加成本、准备入口漏载本地环境。**

- **方案：** 按用户要求删除未执行的本地Pillow实现，改走unified renderer注册组件/操作；图形臂去除曲线旁重复摘要，原精确向量仍保留，文本与截图控制保留其登记摘要；补source `scripts/env_local.sh`，仅续跑未完成准备。
- **依据：** 35项renderer回归通过，完整220例/660图/1,980输入检查通过。三例输入比由约1.21–1.26降到1.15–1.19，这是调用前纠正重复内容，不是事后按MRR调方案。来源：[F09](#src-f09)、[F10](#src-f10)。

<a id="r38"></a>
**R38｜RQ3.15：边际图把固定位置画在二维坐标中、长操作名溢出、CPU环境缺Transformers。**

- **方案：** 两个分布改独立值轴和明确阶段行，避免将排版位置当耗时；保留完整长名称和字号，重新分配内部空间；CPU使用已有infer环境并关闭CUDA，没有安装新包或改模型环境。
- **依据：** 全220例及图元/数值/处理器检查通过，341,635个选中总体配对独立复核。点重叠和秩抽样仍存在，见U10；环境修复不能等同于VLM已理解图形。来源：[F11](#src-f11)。

<a id="r39"></a>
**R39｜RQ3.16：去点控制的中间设计校验、绑定抑制和fixture遍历错误。**

- **方案：** C20接通已有`presentation.marks`，同步记录有意抑制的绑定；不支持该开关的C19继续拒绝；修复fixture遍历与中间设计兼容。
- **依据：** 220例完整CPU资格、422图及32,624绑定检查通过；默认图与历史PNG重绘一致，MARKLESS仅删除点组后HTML等价。旧文另记过当时timeout-only规则调整，属于后续已被用户撤销的历史操作，不作为现行规范。来源：[F12](#src-f12)。

<a id="r40"></a>
**R40｜跨实验Dashboard：特殊标注缺测点引发用户报告的诊断干扰。**

- **依据性质：** 用户在其他项目的经验报告，不是CanvasRCA已测效应量。
- **采用方案：** 使用已有`metric.line`跨缺测位置连接相邻真实观测，保留原时间坐标；不加问号、断线或警告；源数据仍保存缺失，不造观测。撤回RQ3.14缺测断线新组件方案。
- **状态：** 已采用的显示处理规则；不声称其收益已由本项目对照实验验证。来源：[F01](#src-f01)。

### E. RQ4运行修复、环境及历史清理

<a id="r41"></a>
**R41｜RQ4.3 X_SRP：在线重新绘图的生成身份偶发不一致。**

- **方案：** 直接读取已经资格化的冻结PNG、提示、保留token和分组；提交前验证完整身份、renderer manifest、实际processor计数及几何。不放宽hash检查，不用新图覆盖冻结图。
- **依据：** 全220例X_SRP及其余八臂24样例共244检查、13项离线回归通过。**按用户口径已解决。** 原偶发变化无法稳定复现，不能指定字体或并发为已证实根因。
- **计时后果：** 改记`cached_input_to_validation_seconds`，完整冷时延置空，离线绘图另计；不把缓存读取称完整冷路径。来源：[F26](#src-f26)。

<a id="r42"></a>
**R42｜RQ4.3：八个长HTML请求超过KV容量，抢占重算撞上算子限制；死引擎排空卡住。**

- **问题：** 八输入合计230,663token，已超过当时208,457等效容量且未含输出；原仅限制请求数，不为完整输出预留。
- **方案：** 从真实KVCacheConfig按full-attention/Mamba共享池和块大小计算准入，扣null block；每请求预留完整输入+原8192输出，超限FIFO在RAM等待，完成释放；等RPC时检查引擎存活、取消/清理有界；保留意外抢占检查和等待计时。用户授权本实验显存比例0.75→0.80，实际容量仍以引擎为准。
- **依据：** 原生分配离线复现，18项受影响回归通过，原八个未提交请求后来完成；权重、精度、输入及算子数学定义不变。早期两个测试fixture容量/参数错误也已修正。来源：[F25](#src-f25)。

<a id="r43"></a>
**R43｜RQ4.5 Nibi：旧精确包版本不在Alliance wheelhouse，新环境构建中断。**

- **方案：** 其余包使用可用精确Alliance wheel；NumPy2.3.5、SciPy1.16.3、XGrammar0.2.3按已安装RECORD逐文件复制并校验SHA；保留实际Pillow12.1.0，去掉陈旧Pillow-SIMD元数据；OpenCV使用正确module与placeholder wheel；保留module初始化路径。
- **依据：** 导入job24587191完成，processor等价job24585721的九份实际张量/元数据逐字节相等。**输入环境等价问题已解决。** 记录仍保留两条依赖metadata warning，未给出消除方案，列U13；不能把警告抹去。来源：[F27](#src-f27)。

<a id="r44"></a>
**R44｜早期 QA 准备与反事实：请求格均衡不等于实际题格均衡，候选表交换不等于图像改变。**

- **QA方案：** RQ1.1将逐病例fallback改为全roster、只选可解问题、最小化已实现cell计数的确定性调度；P1每格40、P2每格13–14、P3每格6–7，覆盖全部72个P4格，P4/R2使用115个实际可用病例。原1,900题均有支持，但369次fallback造成原分布偏斜。
- **反事实方案：** 原391/480 placebo图与事实图相同，因为交换仅出现于外部候选表的ID；限制身份必须实际出现在M/R/L/G图中，核对factual/target/placebo图hash确实不同。
- **依据：** 修复后的固定资格准备和冻结可用性矩阵检查通过；未将有缺陷准备送模型。QA后续规范仍见专项文档。来源：[F04](#src-f04)。

<a id="r45"></a>
**R45｜历史重复研究与名义干预：已经做过或根本无变化的条件不能继续按“新机制”运行。**

- **当时处理：** RQ3.6重新复核SEARCH13部署关系、SEARCH24整体传播摘要删除、SEARCH31 signed-z隐藏、Tournament R16实体绑定及RQ3.4 H/K析因；取消泛泛重复的截图、H开关和“图有用吗”，后继限定组成及交互。完成与仅注册未运行分开；同一病例跨轮重复不作独立证据。
- **状态：** 历史检索和方案去重已落实，不等于宿主上归因、关系机制等科学问题全部解决。HP跨宿主无干预的取消另见R28。来源：[F18](#src-f18)、[F19](#src-f19)。

<a id="r46"></a>
**R46｜历史产物清理、重复存储及取消实验：删除已完成且保护范围有核验。**

- **旧RQ2退役：** 删除294,443个拥有的原始产物文件、132,520,699,087字节，先核对288个受保护文件；源码、报告及引用图表保留。科学缺陷并未由删除修复，见U01。
- **RQ3.14重写：** 删除58个旧实现/相关文件，0模型调用，没有保留旧实现备份；统一renderer后继见R37。
- **RQ3.22取消：** 删除整个实验、计划、测试、产物及Windows例图，无备份；54次已耗测试调用只保留计数，正式调用0。不能继续把取消实验当可恢复队列。
- **首次unified之前：** 边界RQ3.8，清理12个旧实验、114目标；保留190份文档和40个迁移附件，538个报告附件及源码hash当时核对通过；文件系统释放约297.12GB。
- **扩大至RQ3.15：** 再清43目标，保留32文档、115附件；587报告/画廊附件、690源码配置及RQ3.16的23,722文件当时核对不变；释放约26.51GB。Windows旧例图386文件、91.27MB单列，不与Linux空间差值相加。
- **边界：** 这是按授权完成的清理，不是还可重评分的保证；原始结果与再生成依赖消失的后果见U15。四个清理前已有缺图见U14。本次删除的是这些旧清理记录所在的issues目录，不重新清理实验结果。

来源：[F07](#src-f07)、[F10](#src-f10)、[F13](#src-f13)、[F02](#src-f02)、[F03](#src-f03)、[F28](#src-f28)、[F29](#src-f29)、[F30](#src-f30)。

## 第二部分：未解决、只处理了一部分，或缺少解决方案记录的问题

这一部分保留已证实的历史设计失效、实际未补齐的测量、记录缺口和仍有约束的适用性。退役实验不意味着要重新启动。

<a id="u01"></a>
**U01｜旧RQ2的四种工具条件实际输入坍缩；缺少RQ1.1桥梁。状态：原科学对照失效，实验已退役。**

四profile在每个case/transport/model下实际输入相同；工具只接收已选parent packet，数值字符串适配缺失，选八实体后转set，再由共同排序及row cap定事实，权重差异没有传入请求。元数据hash不同不能证明干预不同。另同时改变证据投影、字段、顺序、预算、图和指南，不能把跨RQ降分单独归于视觉。

RQ2.1采取全公共池、原算法适配、完整输入身份检查、历史桥梁和分阶段因子设计，属于后继预防，不会追溯补成旧RQ2的有效工具对照。旧实验已取消并删除原始记录，没有可以“修复后继续分析”的原对照。来源：[F07](#src-f07)、[F05](#src-f05)。

<a id="u02"></a>
**U02｜RQ3.2已执行对照与名称/设计不一致。状态：结果保留，原对照没有修复重跑记录。**

- `NO_GROUPING/C_CONTRAST`在已评分Qwen96、Gemma100配对病例与基线输入完全相同，差异只能描述重复波动。
- `p0_more`没有P0 backbone并使用新pool/排序，不是仅扩大原P0容量。
- 继承指南写前后半窗、median/union，实际使用P0公共split/不同统计字段；444/480 eval、339/360 test的split与中点相差超过1秒。
- C-Flat/C-Contrast实际是带引用的自然/紧凑目录，非计划中的直接比较表；target removal删第一条根因关联事实，noise在选择后追加。

RQ3.3的明确指南修订和真实P0_MORE见R14/R17，不能据此把RQ3.2历史比较重新解释为原计划已经执行。来源：[F14](#src-f14)、[F15](#src-f15)。

<a id="u03"></a>
**U03｜不同证据包的Trace数量、窗口和耗时口径未全量统一。状态：单位标签已有局部解决，整包统计对齐没有完成记录。**

RQ3.2记录相同实体/操作的继承与直接来源存在不同count/duration；RQ3.5具体例的P0 p95显示30,006,458.63 ms，而SIRCL显示30,006.3 ms。RQ3.6来源链确认父版微秒标成毫秒，并在新版本修单位标签（R27）。但窗口、选择、分母和估计器差异仍不能凭单位修正消除。原来源审计不等于逐条raw span独立重算；不存在已登记的全语料统一统计修复证据。原包比较不能升级为纯selector效应。来源：[F14](#src-f14)、[F17](#src-f17)、[F20](#src-f20)。

<a id="u04"></a>
**U04｜自然语言理由核验器漏掉无依据的边和推理错误。状态：未见完整修复。**

旧RQ2实例中模型声称694→137、137→120，但实际edge ledger没有这些边，`unsupported_structured_mentions`仍为空。RQ3.4—RQ3.6也明确sidecar是partial literal audit，不能解析全部因果、时间、类型或数值声明。未发现完成全量重审或通用语义核验修复的记录。此缺口不改变已登记MRR，但“未检出错误”不能等同于解释可信。来源：[F06](#src-f06)、[F16](#src-f16)、[F17](#src-f17)、[F20](#src-f20)。

<a id="u05"></a>
**U05｜正确格式/成功运行仍有实体、数字、方向和理由—排序矛盾。状态：真实模型错误，未被工程资格消除。**

记录包括pod/node被称service、把2.15e6说成大于3.66e6、把+25分钟说成早于+18/+21、排序首位326而理由称130第一、把437→495中的437称leaf，以及把观测关联当成本地起因/传播证明。这些分别出现在RQ3.3—RQ3.6、RQ3.15、RQ3.16。原回答没有为改善成绩而改写或重答；没有证据表明某个通用修复消除了它们。独立QA的有效性与评分问题只在QA专项文档展开。来源：[F15](#src-f15)—[F17](#src-f17)、[F20](#src-f20)、[F21](#src-f21)、[F11](#src-f11)、[F12](#src-f12)。

<a id="u06"></a>
**U06｜旧RQ2有实际未采集/未保存的数据，恢复运行没有补回。状态：历史缺口。**

一份完整文本RCA（`INC-6DCAE95A54B2 / B75_DIVERSITY__text__one_stage_rca`）有prompt attention却没有generation-target attention，原状态`not_captured`；占当时content结果1/5,400，仅限attention分析缺失。另一次磁盘满的失败请求未写出Markdown对话，记录明确没有该文件。不能把恢复后总调用完整写成这些缺失测量也已恢复。旧RQ2原始结果后来全部按授权删除，本次不重建。来源：[F06](#src-f06)。

<a id="u07"></a>
**U07｜CPU准备加速不等于完整端到端部署已快。状态：已测剩余开销，无进一步消除记录。**

RQ3.3优化后固定A22日志聚合仍38.91秒、Aegis9.20秒；公开池已加载后的单方法5.281/6.159/0.729秒不含源读取、统计和推理。RQ4.3 X_SRP改用冻结输入后不再提供完整连续冷路径时间。上述不能包装为实时RCA或纯计算提速；已实施的加速/缓存修复本身仍列“已解决”，这里保留的是成本口径和剩余工作量。来源：[F15](#src-f15)、[F26](#src-f26)。

<a id="u08"></a>
**U08｜来源/容量导致部分机制不可适用。状态：按原协议保留N/A或取消，并未获得该机制的有效比较。**

- RQ2.1某些完整日志在S0固定足迹放不下，保持design infeasible，不静默截短。
- RQ3.3最终三例矩阵仍有25个N/A：16个缺独占证据对、6个缺受支持事件关系、3个Aegis事件截图容量不足；EVENT未获这些路径的资格。
- RQ3.5已选105个J包全为request-family、scope=0，不能据此回答宿主scope问题。
- RQ3.6跨宿主条件在180例无实际变化，已取消，不记作负效果。
- RQ3.10 v2直接稳定活动/冲突主要限A22的23例；A25没有稳定活动冲突，Aegis没有实例scope病例。服务流量不能摊到每个pod；从公开时钟推断cadence也不能独立发现整段采集时间戳系统性缺失。

这些是已核实的适用性边界，不是未证实的“可能风险”，不代表本次要求放宽阈值或补跑。来源：[F05](#src-f05)、[F15](#src-f15)、[F18](#src-f18)、[F19](#src-f19)、[F08](#src-f08)及RQ3.10保留协议。

<a id="u09"></a>
**U09｜RQ3.5运行摘要的granularity字段。状态：离线报告已纠正，原运行字段的修复记录缺失。**

R29记录了独立报告的正确根因粒度计算；原文明确把未来runtime summary修复列为另一个任务，没有保存已完成的源码修改及验证。本汇总不能替它补写一个解决方案，也不会因此作废原逐例MRR。来源：[F17](#src-f17)。

<a id="u10"></a>
**U10｜边际图仍有点重叠、小刻度和抽样含义限制。状态：未见对应修复。**

RQ3.15真实点存在重叠，没有用jitter伪造位置；普通例刻度偏小，精确值在当时混合输入文本中。按父耗时秩选样不保证包含全部子端极值，图中密度不等于总体概率。RQ3.16保留这些属性，MARKLESS也保留轴范围与文字。合法PNG或人工可读不自动证明模型读懂，更不能把该混合输入的文本补充作用移用于纯视觉结论。来源：[F11](#src-f11)、[F12](#src-f12)。

<a id="u11"></a>
**U11｜供应的SIRCL源码快照缺license，未记录公开再分发权限核验。状态：记录缺口。**

RQ2.1写明本地复制获得用户授权，但未核验公开再分发许可。没有后续解决方案记录。本条只是忠实转述来源/授权记录，不对许可证作新法律判断。来源：[F05](#src-f05)。

<a id="u12"></a>
**U12｜RQ4.5 Nibi视觉内核慢：原因已测到，端到端吞吐目标的完成证据未写入本地记录。**

- **已证实问题：** 真实encoder的27次FA3占约17.078秒self GPU；大图约116秒。相同BF16随机张量、真实head_dim72下，65,160patch的FA3每块约4.319秒，Torch Flash SDPA约0.0794秒；数值容差检查通过。这不是导入耗时能够解释的在线延迟。
- **已验证候选方案：** 原生`mm_encoder_attn_backend=TORCH_SDPA`的算子替代，不改权重/精度；三种长度的对比job24586861完成。这部分已有数值证据，不能写成“尚无任何解决方案”。
- **尚缺记录的部分：** 本地调查与findings最后保存的原生完整encoder/冻结链为24589226→24589420→24589619；没有对应完整方法达到≥7实际完成calls/min的结案记录。该项未闭环指**吞吐目标和完整路径的结果记录缺失**。后来本地RQ4.5完成不能自动替代Nibi证据。
- **排除误归因：** 导入88→21→18秒有进程顺序和热缓存混杂；采样GEMM及Flash-SDPA在workspace flags下基本同速，不能把这些flags直接写为已证明的50倍流水线加速原因。

原查得的profile和primitive结果仍在 [Nibi findings](../RQs/RQ4_5/findings/exp_exclusive_spatial_findings.md)及对应子目录，本次没有登录Nibi或声称这是远端实时状态。来源：[F27](#src-f27)。

<a id="u13"></a>
**U13｜RQ4.5 Nibi每job复制完整环境造成新阻塞，以及两条依赖metadata warning。状态：方案有记录，部分闭环细节未保存。**

完整encoder job24586948在进入Python前卡于环境`cp`不可中断读取而超时，没有数值结果；记录的纠正是取消每allocation完整复制，直接激活已验证的持久环境并保留module路径。其后继job当时仅登记排队，未保存这一启动修复的独立CPU完成确认，因此本条不自行写成“已经验收”。环境本身导入及processor等价通过已在R43列为已解决。

同一环境记录说保留了“两条精确metadata警告”，但这份issues文件没有列出其文本或消除方案；不能虚构已修正依赖声明。来源：[F27](#src-f27)。

<a id="u14"></a>
**U14｜四个报告图片链接在历史清理前已缺失。状态：未找到恢复记录。**

两次删除审计均明确“没有新增缺图”，并非“所有图都存在”。原清单为：

| 引用文档 | 缺失目标（原相对路径） |
|---|---|
| `docs/experiment_plans/CanvasRCA_Next_Research_Plan_2026-09-22.md` | `../experiment_reports/RQ3_2_Results_Analysis_2026-09-22_assets/evidence_coverage.png` |
| `RQs/RQ3/descriptions/RQ3_qualification_20260909.md` | `../results/exp_selection_design_attribution_smoke_v1/renders/INC-0C24330AB85D_solver_U11_2.png` |
| 同上 | `../results/exp_selection_design_attribution_smoke_v1/renders/INC-0C24330AB85D_solver_U01_2.png` |
| 同上 | `../results/exp_selection_design_attribution_smoke_v1/renders/INC-0C24330AB85D_solver_screenshot_2.png` |

来源：[F02](#src-f02)、[F03](#src-f03)、[F28](#src-f28)、[F29](#src-f29)。这是原缺失路径记录，不把它们制作成仍可打开的链接。

<a id="u15"></a>
**U15｜删除旧结果后，历史重评分和部分再生成入口不再完整。状态：授权清理的已知后果，没有补回方案。**

RQ3.15及之前原始请求、输出、对话、attention/preparation已按用户要求删除，只有代码、设计、报告及引用附件保留。RQ3.16部分旧准备入口仍依赖RQ3.15及以前产物；保留RQ3.16自身文件不等于保留全部上游重建依赖。历史JSON/轨迹路径只作为来源记载，不再保证可读。

本次进一步按用户要求删除整个issues目录，原逐文件清理JSON及压缩RQ3.16校验清单也随之删除。下面保存原文件hash、关键计数和当时保护结论；**它们不是原清单的无损替代，不能据此重新执行逐文件历史校验。** 不另建隐藏备份或恢复已删原始结果。来源：[F02](#src-f02)、[F03](#src-f03)、[F28](#src-f28)—[F30](#src-f30)。

<a id="u16"></a>
**U16｜RQ4.7两步视觉动作：已有卡片身份，却要求模型给出连续精确坐标。状态：设计缺陷已记录，index接口尚未实现。**

首轮`ACTION_GUIDE`确实说明0–1000坐标，schema只接受operation/regions，没有卡片index字段；宿主已经有DOM测得的卡片ID及box，却让模型先估边界，再反向匹配。JSON合法后仍要求整框落在唯一合法卡片内，边界容差仅原图像素坐标的1e-6，跨卡或重复来源被拒；这不是“没说明坐标制”的问题。

M_CLOSED/M_COMPARE最后使用整张卡片，却继承同一坐标准入；三者又共用完整来源容量检查。全部动作无效、为空或容量拒绝时，workspace为None，第二次诊断只接概览，首轮成本已发生且局部干预不存在。此图像回退并不等同于历史U的完整请求。

用户提出改用图内卡片index操作；只记录了方向，未改代码或做CPU验证，不能列已解决。三个M条件的原数据已按要求删除，本条仅依据保留源码，不编造失败率或恢复旧MRR，也不能由接口失败推断所有两步视觉方法无效。代码证据：[动作编译](../RQs/RQ4_7/src/exps.py)、[schema](../RQs/RQ4_7/src/utils.py)、[统一执行器](../src/renderer/operations/source_workspace.py)。来源：[F01](#src-f01)。

### 来源索引与删除范围

下表覆盖原目录全部30个文件。F编号指删除前读到的源文件，SHA-256用于标识本次汇总依据的版本；**表中的旧文件名不是仍可读取的链接**。正文的R/U编号是合并后条目，多个原问题可合并到同一类，但解决范围分别说明。

冻结结果、源码快照和`Codex.md`中历史保留的`docs/issues/...`路径不因本次汇总自动改写。今后查这些旧引用，使用本索引定位对应R/U条目。当前文档导航中的可维护引用另行指向本文件；本次不修改项目规则、不运行实验、不改答案和评分。

| 来源 | 原文件名 | 汇总位置 | 删除前 SHA-256 |
|---|---|---|---|
| <a id="src-f01"></a>F01 | `Dashboard_pitfalls.md` | R40；U16 | `d10d5e93354b31036602b6a1f3e0a8c03785162e49c5b0c26b53b84456a4cf43` |
| <a id="src-f02"></a>F02 | `Pre_Unified_Artifact_Deletion_2026-10-11.json` | R46；U14、U15 | `8af3f5909d9085c5ad713737b73b12f5d078dff391394d3c00578949704b9a03` |
| <a id="src-f03"></a>F03 | `Pre_Unified_Artifact_Deletion_2026-10-11.md` | R46；U14、U15 | `fd611e70a3fd652de3fd6e6c1668422cfc0677a4562ea23e4a92cdca2cabb04f` |
| <a id="src-f04"></a>F04 | `RQ1_1_issue.md` | R01–R03、R44 | `c41cdab9dccc07dce83d54689df6e6a3b518a7021184f6e5869b95d52448e2bd` |
| <a id="src-f05"></a>F05 | `RQ2_1_static_review.md` | R09、R10；U01、U08、U11 | `6ee9f64a6ed44fc831c7c3db1d099ab4497d2f590a06825347b383abf31e8706` |
| <a id="src-f06"></a>F06 | `RQ2_issues.md` | R04–R08；U04、U06 | `88ba325dbd2877478863e506719eb7a377ddc03a4bf44e831e19f0f691ad9452` |
| <a id="src-f07"></a>F07 | `RQ2_retirement_audit.md` | R06、R46；U01 | `d36cdbe7b72c5e7cb89a2818e84defc7ffedb4f278a8035ff2db3db46a2abfef` |
| <a id="src-f08"></a>F08 | `RQ3_10_qualification_2026-10-01.md` | R36；U08 | `ddea6d468146f04dd44b166a880b897d0d0d90578cf31366e7c256f1e1e4386a` |
| <a id="src-f09"></a>F09 | `RQ3_14_qualification_2026-10-02.md` | R37 | `14eb38889d0feb0e45f16cc73ddf40e66ad01552c80cd708127b71e665c8fd64` |
| <a id="src-f10"></a>F10 | `RQ3_14_unified_rewrite_deletion_2026-10-02.json` | R37、R46 | `b1f5dcba8ac3b0eac0a27e8dbbbe818c475f0efa4e15f3fe615dbb5b989ce519` |
| <a id="src-f11"></a>F11 | `RQ3_15_qualification_2026-10-02.md` | R38；U05、U10 | `986c4a1614f6bc9892ec98c8f3059092378f99c5757e54b1be83af57206776a6` |
| <a id="src-f12"></a>F12 | `RQ3_16_qualification_2026-10-03.md` | R39；U05、U10 | `28ef7d91a67c63ab92214600ccaa5b7ba8d064bea31243510b1ea9306acbebea` |
| <a id="src-f13"></a>F13 | `RQ3_22_Deletion_Record_2026-10-06.json` | R46 | `cfb88b92c87ca1851e682bdd08534af4422f8a4ef829f367f14be09affbc267d` |
| <a id="src-f14"></a>F14 | `RQ3_2_issues.md` | R11–R13；U02、U03 | `91d7eb3d61bff61b455be732ad55c334e86cf10ca9114e71947e0eb0b14cf20d` |
| <a id="src-f15"></a>F15 | `RQ3_3_implementation_review_2026-09-23.md` | R14–R19；U03–U05、U07、U08 | `dec02ca0e3041d2a4e46fc8080985185639702fc85ce8f38d20d889413b7ba6d` |
| <a id="src-f16"></a>F16 | `RQ3_4_qualification_2026-09-24.md` | R20–R22；U04、U05 | `66676aae26e85130928e9f91c9c9b2d99db1adf5c11f482e6e4b594a7eeab650` |
| <a id="src-f17"></a>F17 | `RQ3_5_qualification_2026-09-25.md` | R21、R23–R26、R29；U03–U05、U09 | `816eb44ad983ae11116629ed5c9c2186ada20b3a002a198bad48d6f78fcbc6ba` |
| <a id="src-f18"></a>F18 | `RQ3_6_historical_question_audit_2026-09-27.md` | R45；U08 | `1d0914d316b00edfbc867431c769f9d75d5fd488586d69f422c029f8ffff5ab0` |
| <a id="src-f19"></a>F19 | `RQ3_6_mechanisms_v2_qualification_2026-09-27.md` | R28、R45；U08 | `592635d19e818b8f45979badd1ea18493d1e6edb0462e54483ed3b10c4b9b787` |
| <a id="src-f20"></a>F20 | `RQ3_6_qualification_2026-09-26.md` | R27；U03–U05 | `58c45c9a70583474a09affb9ef79208a4bdf0415c5e0b6f39efd756d554e6884` |
| <a id="src-f21"></a>F21 | `RQ3_6_stage_B_qualification_2026-09-27.md` | R28；U05 | `48b36603f7a6d3d935f16509199e040cbadead042ceaa6e5479fa97ad4f286ff` |
| <a id="src-f22"></a>F22 | `RQ3_7_stage_C_qualification.md` | R32 | `40ab3b59ebcd39e6891a9021db8cc5d68ef4d23c44e85fa2bab33e1c9a897187` |
| <a id="src-f23"></a>F23 | `RQ3_7_static_review.md` | R30、R31 | `c0f269803cf11014065e3fd8ae27b3337825314e13d72b89d88e756e8a72e7cd` |
| <a id="src-f24"></a>F24 | `RQ3_8_nibi_startup_2026-09-29.md` | R33–R35 | `bf8962110dc781eff1cde379998590eb4d1e298a17fb967a5953c858a4a059c8` |
| <a id="src-f25"></a>F25 | `RQ4_3_KV_Admission_Repair_2026-10-11.md` | R42 | `4d2c6d1eb46c2adc8ed8ccb9bfa1e216e8d64dabbfff36d7bbcaf4c4ff1467fb` |
| <a id="src-f26"></a>F26 | `RQ4_3_X_SRP_Runtime_Repair_2026-10-11.md` | R41；U07 | `fa4bb1efa46e937a45146e4da57688bcb1fc30cabd93c42b012904f0d9d2f202` |
| <a id="src-f27"></a>F27 | `RQ4_5_Nibi_Runtime_Investigation_2026-10-19.md` | R43；U12、U13 | `49f4bfccb5f01524caf4d71df2164890d813a27ae95efd41e41fb88a0291d759` |
| <a id="src-f28"></a>F28 | `Through_RQ3_15_Artifact_Deletion_2026-10-11.json` | R46；U14、U15 | `4acb553f0252275c48cefdb6c13b3ed3d45b5e08908c5e091b93f85c6080b9e0` |
| <a id="src-f29"></a>F29 | `Through_RQ3_15_Artifact_Deletion_2026-10-11.md` | R46；U14、U15 | `f84d01fdfb994a08f5b317acb20571d72955e01aedcdbe92475316790182b6da` |
| <a id="src-f30"></a>F30 | `Through_RQ3_15_Artifact_Deletion_2026-10-11_rq316_manifest.json.gz` | R46；U15 | `585ece68c8d35dd46d4826833ae5bc803fa3d903ab7f85d1e55c1783282dfd2e` |


## R47 — RQ4.8 anchor-only card subset caused empty optional-support reduction (2026-10-20, resolved)

While preparing the fixed formal QA subset, INC-A1C6591B0184 retained only
GRCALL in the target-isolation control. Its optional-role palette and role-mask
alpha were both empty, while the anchor mask contained 62,854 nonzero pixels.
The historical support function nevertheless called `argmax` on an empty
role array, raising `ValueError: attempt to get argmax of an empty sequence`.
Preparation stopped dispatching new cases; no GPU call was made for this failure.

The RQ4.8 adapter now explicitly handles an empty role set: it rejects undeclared
role ink, computes protected token support using the same affine pixel-cell
intersections, returns an empty optional set, and preserves every anchor. The
ordinary nonempty-role path still calls the unchanged historical implementation.
Renderer pixels, old components, prompts, and model inference are unchanged.
The failed case then prepared successfully; the complete fixed 60-case QA input
set and actual input hashes/capacities passed preparation checks. The prior
15 successful bundles were reused. The 220-case CPU regression was not rerun.

Evidence: `RQs/RQ4_8/results/card_selection_v1/formal_preparation/history/anchor_only_failure/`,
`qualification/formal_qa_preparation.json`, and
`formal_preparation/input_integrity.json` under that experiment result root.

## R48 — RQ4.10 complete marginal layout and subpixel plots (2026-10-22)

The newly authorized pure-visual complete-annotation baseline initially used an equal-row layout. Two registered real cases required 4,184 and 4,842 pixels of card height against 3,986 available pixels. A measured independent-column layout removed that overflow, but actual PNG inspection exposed a second defect: a narrow numeric/sample row left its SVG only 12.5 pixels wide and 0.5625 pixels high. Font and clipping checks passed even though the sample dots were effectively invisible. The CPU run was stopped after 45 cases under that superseded version; no model calls had started.

The registered successor gives complete marginal cards a 1,344-pixel column, measures the other columns from real DOM content, and adds an explicit `complete_readable` operation for this new baseline only. It requires at least 80 pixels of sample-plot width, at least 12 pixels of plot height and a 4-pixel sample radius. It preserves frozen values, sample counts, units and source bindings. The PACK operation preserves the plot height and point radius while expanding horizontally; otherwise removing the number column also enlarged the responsive SVG height and clipped the last sample row. Hidden panels in the QA isolation control are excluded from visible-font checks only after checking they contain no visible text.

Three fixed real cases passed the revised CPU checks; the corrected PNG was inspected and its sample dots were visible. Subsequently all 220 cases passed the revised CPU qualification, including real processor capacity and geometry checks. Historical renderer components, historical PNGs and results remain unchanged. Evidence: `RQs/RQ4_10/results/domain_context_v1/qualification/manual_image_log.json`, `qualification/cpu.json`, the per-case CPU audits, and the additive `src/renderer/web/domainView.ts` operation.

The initial renderer build also supplied two entry points to an esbuild command using a single `--outfile`, which failed before rendering. Separate registered `studyView.mjs` and `domainView.mjs` build commands resolved that build failure.

## R49 — Bare GPU CLI omitted the qualified sampler environment (2026-10-22, resolved)

The first RQ4.10 organization smoke was launched directly with the inference Python executable, without the previously qualified local environment wrapper. vLLM loaded the model weights, then its dummy sampler warmup selected FlashInfer and attempted JIT compilation. Startup failed with `Could not find nvcc and default cuda_home='/usr/local/cuda' doesn't exist`. No experiment model request had started.

The fix was to source the unchanged `RQs/RQ4_9/scripts/environment_local.sh` before invoking the RQ4.10 CLI. This restores `VLLM_USE_FLASHINFER_SAMPLER=0`, the existing native allocator and local cache settings. Installing another CUDA toolkit was unnecessary. The original 900-second smoke window and call ledger were kept; no attempt budget was reset. All 18 organization requests then committed and passed artifact checks. The launch example in the RQ4.10 README now explicitly uses the wrapper, and `qualification/runtime_environment.json` records its exact hashes and effective settings. Model weights, diagnostic inputs and decoding parameters were unchanged.
