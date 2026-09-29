# CanvasRCA consolidated devlog

## 2026-09-28 — RQ3.7 CPU/GPU资格通过，A→B正式已启动

用户授权回归、smoke后启动实验。真实CPU回归修复父版k/M/G数值缩写解析，补入来源核实的RQ37-local OTel精确指标定义（未修改旧证据选择/配置）；A smoke暴露并发进度写盘共用.partial的竞争，改用项目unique-temp atomic_write。修复后17个单元测试、3案例63编译目标通过，17.26秒，两processor容量检查通过。

A沿原始600秒窗口和18次累计调用上限续跑，两份已完成回答保留；最终18/18完成，529.37秒。B 18/18完成，269.33秒。两模型均实际覆盖；检查PNG、完整请求、raw回答/conversation持久化及成本，未发现阻塞问题。原失败报告及源码契约保存在pre_run_revisions，修复来源记录在smokes/A_repair.json；不抹去失败。依据字段核实单位定义，不按模型成绩修改设计。未知单位保留读数，实际柱图/换算适用率随case报告。

共享历史累计21469+资格36=21505；A+B正式新调用上限3420，已删除的重复参考不回退补跑，C不自动开启。源码契约1a8d2032bb94718e3a23b62d1a62e331b0b1b671410312b78e22b1dc756997a2。详细资格记录 `RQs/RQ3_7/results/fusion_v2_pruned/logs/qualification_review.md`。没有把smoke准确率当作方法效果，也不把smoke回答用于正式统计。

正式队列通过setsid后台启动，supervisor PID15647；确认A/Qwen runner PID16318实际提交推理，非仅服务占显存。11:35本地检查时已落盘3份新正式结果，共39次正式调用已登记（3 complete/36 started）；进度17/1260终态包含只读参考，不应把它们全算新增推理。队列按A→B自动切换，后台继续，无C授权。正式log：`RQs/RQ3_7/results/fusion_v2_pruned/logs/formal_A_B_supervisor.log`；阶段进度在同root的`progress/`。

## 2026-09-28 — RQ3.7删除重复生成条件（静态交付）

按用户精简授权，A删除B3_T_REF结果条件（保留历史公开输入锚点），TPV_REF/B3_G_REF改为只读兼容旧结果，缺失或不兼容登记reference_unavailable，不补跑、不记0、不重试。C在相同开发180上不能绕过此规则；其他病例必要基线仅在以后独立授权C时运行。四格和T_MATCH保留，B等价数字/单位及当前请求REPEAT保留，没有新增泛泛图文/绑定/布局比较。历史代码结果未删除。

同步计划、配置、任务生成/执行防回退、统计交集与配对扩量、测试定义、三份描述及静态审阅。A新增上限2880→1800，总保守新增13854→12774；A+B3420（含两smoke3456），C仍关闭。减少1080是最坏调用额度，不将本来可复用的旧回答谎称为实际节省。核心分析不受旧参考缺失牵连；历史对照单列有效配对N，Holm family不缩减。决策依据和影响见RQ3_7_experiments.md的DD-RQ37-1。

AST/本地导入符号/ruff/JSON版本和预算/bash语法静态检查通过；CPU与GPU资格均未运行，新模型调用0。新登记身份rq37_numeric_relation_fusion_v2_pruned，仅代码待后续资格，不启动任何队列。

## 2026-09-27 — RQ3.7实现与静态交付（未运行资格或实验）

落实用户批准的数值证据×实体关系融合协议：固定B3 ALL_ID公开内容，LOCAL/REMOTE×ID/LINK析因、同内容T_MATCH、数字写法/来源单位等价变换及独立REPEAT；C锁定泛化单独关闭。计划与历史去重索引在 `docs/experiment_plans/CanvasRCA_RQ3_7_Research_Plan.md`，源码为新 `RQs/RQ3_7/` 五模块+init，旧实现/结果/模型配置不改。

静态审阅修复了数值字面量、单位展示名称、附加M记录排版/同步、跨变体共同几何、重试prompt定位、timeout别名去重、历史锚点匹配及累计预算恢复风险。采用同一共享调用SQLite而不是另起计数器；未来预算最坏新增13854、历史设计基数21469、合计35323≤40000，实际登记时重新核对。终态flag先行续跑，历史结果只在请求与scorer兼容时引用；REPEAT不去重。语法/AST/导入符号/ruff/shell与静态预算检查通过，审阅详情 `docs/issues/RQ3_7_static_review.md`。

本轮没有CPU回归、preparation、真实渲染、GPU smoke、服务或正式实验，新增模型调用0。真实图形覆盖率、可读性、双processor容量、恢复与GPU链路仍待后续明确授权后的资格检查。没有将静态完成视为实验通过或有效性结论。

## 2026-09-28 — RQ3.6 mechanisms_v2 全量离线统计与案例审阅

队列于00:01:18 UTC正常完成，12240逻辑位：12196正常结果、6重复ID模型失败、38请求超时，无不明缺失。实际新增正式10500、smoke52；1740合法复用，历史加总21469。主分析按实验×模型全arm共同病例集，Qwen163/170/170、Gemma均180，模型失败保留0；超时按完整配对及零分分别敏感性，不新增5%门槛。

报告 `docs/experiment_reports/RQ3_6_Mechanisms_Analysis_2026-09-28.md`：34条件、三数据集及AIOPS合并、root/fault/复杂度、Pratt/dz/Holm、事件组敏感性、修复/破坏、成本，8统计图及10例21份输入输出/4原图。完整artifact审计97996引用/78815文件，12196分数重算一致；仅本次分析执行，不加到续跑。分析脚本与数据在报告assets，原实验源码/输入/配置/分数未改、新增推理0。

三个primary及绑定secondary无校正显著结果。Gemma B3 ALL_ID图文+.1056为探索线索：本实验图文family Holm .0451，三实验34项一起校正 .1279；service/pod有收益而node退化。BIND整体无提升，host增量不稳定。事后rank1对齐分层说明删除摘要可能伤害原正确提示，但不可用gold路由。案例暴露同图文本重复改变层次选择、真实CPU与微小高σ干扰竞争、正确ID但理由/关系错误。建议优先独立复制条件性视觉收益及公开摘要可靠性；不自动启动下一实验，不全局删onset/推广host或RL。三个对应findings已同步，保留资格历史。

## 2026-09-27 — 三个历史去重后机制实验资格通过

执行补记：15:48 UTC启动后台正式队列PID32627；首份结果15:50:34，观察至15:56:02超过五分钟，77份正式结果完整、无失败flag，HTTP200和GPU实际推理正常。下一模型/实验由队列顺序启动。保留运行，按用户要求结束监控；`mechanisms_v2/launch_handoff.json`是启动快照，实时看同目录queue status及各runner log。

最终合同78a10ce7：三focus静态检查、每实验13项单测、三例204请求与每实验180例容量检查通过。GPU三个有界smoke各18逻辑单元全部完成，新增18/16/18共52调用，两个自然同输入复用；完整公开回答和真实输入PNG人工审核通过，无基础设施故障。模型错述类型/时间/关系原样保留，不据此挑条件或修改prompt。取消0/180适用的跨宿主条件后，正式规模12240，累计调用当前10969，上限仍40000；不重新引入空干预。正式授权已登记，顺序G成分→宿主竞争→关系绑定，各Qwen→Gemma。启动后检查五分钟实际推理及新输出，再交由用户监控。详情见RQ3_6_mechanisms_v2_qualification_2026-09-27.md。

## 2026-09-27 — 用户批准历史核对后的机制后继

资格前180例CPU发现HP_CROSSHOST适用0例且全请求重复，取消其T/G两条件，12240正式、54smoke、累计最坏23211。host/peer/dedup有115/175/110例实际干预。原证据保留，修订发生于GPU0调用时，重新冻结及CPU检查；不为凑规模保留无效arm。

完成三个精确设计的实现草稿：G显式字段消融；固定pod锚点下host/peer 2×2及重复去重/跨host peer；固定观测的CALL/DEPLOY/ALL×绑定×T/G。移除通用截图/重述及泛泛补证据复测。12×180×2×3=12960正式逻辑单元、三smoke至多54，连同已耗10917最坏23931；共用预算SQLite。只读复用RQ3.4公开完整context，旗标续跑不重建旧请求，认证探测401/403 failfast。新增共同最坏尺寸预检和全部180例CPU容量检查，避免三例遗漏长图。下一步三focus静态、CPU、smoke，审核后正式启动并确认实际推理五分钟。当前尚未宣称资格通过。

## 2026-09-27 — 第二次历史核对修正扩展方向

用户要求再次判断三个问题是否已被回答。补查旧RQ3 SEARCH开发档案后，确认先前核对漏掉SEARCH13 hosting、SEARCH24整体时间/传播摘要删除、SEARCH31 M z标签移除；Tournament R16实体绑定与RQ3.4 H/K图文析因也必须直接承接。第二问题已有较充分现象证据，不能再泛泛复测；“宿主太多导致错误”的剂量机制尚未证实。第一/第三仍缺特定组成及图文交互，但不应包装为从未研究。完整核对落盘docs/issues/RQ3_6_historical_question_audit_2026-09-27.md。下方12960单元描述降为待修改草案，不是已完成注册；三个v2配置禁止执行，新增推理0。旧队列维持暂停，未启动CPU/GPU测试；后续须去重后重新冻结并资格化。

## 2026-09-27 — RQ3.6旧B停止，重设计与认证故障修复中

用户要求避免重复历史比较，登记超过12000正式调用，静态/CPU/smoke通过后全量启动并观察5分钟。旧B尚未正式调用，已安全停止且保留18次资格记录和五模块源码快照。明确起因为正式shell readiness遗漏Bearer认证，连续401却循环等待；不是模型加载慢。修复采用同一认证探测函数并测试拒绝错误，详见RQ3.6 B资格issues。

新三个实验研究G中诊断派生字段、合格补充证据的宿主/peer竞争、调用与部署关系×观测绑定×图文交互。每实验12条件×180重复暴露case×2模型，合计12960正式单元；三个600秒/18calls smoke。累计调用共享一个SQLite限额40000，继承10917不重置。无训练/attention/test/unused使用，继续保留P0基础证据与数字候选列表。旧B的原图文/换序/截图及MORE复测移除；新绘图接口的校准只服务同实验受控比较，不冒充首次图文结果。代码完成后必须再次进行已执行实验去重审计。

## 2026-09-26 — 跨实验方法能力画像（离线）

按用户要求整合RQ1.1/RQ2.1/Tournament/RQ3.1–3.6 A及已补算CPU基线：
137269逻辑记录、840唯一case、276阶段条件。新报告为
`docs/experiment_reports/Cross_Experiment_Method_Profile_2026-09-26.md`，
附6图、全方法root/fault可读表、各数据集/AIOPS合并CSV、配对Pratt/dz/Holm和
事件组敏感性。仅离线读取历史分数及public graph/metrics；8核提取840例特征
约11秒，汇总约131秒，无新模型调用、preparation、续跑校验或实验修改。

分层统一使用canonical完整标签名称集合，跨service/pod别名单列；保留RQ3.5/6
原生accepted集合分层与逐例对照，7个check病例service→混合的分母变化不改分数。
X网络/操作级改善迹象与node/资源破坏并存；最新S的pod/丢包与node/内存取舍需要
机制字段核查，不能用gold路由。图hop几乎为数据集指纹；Metrics数量不是复杂度。
数据集内关联排除无充分变异/单例高杠杆条件，2088可估、1575支持不足；无Metrics
项通过校正，2项图相关探索性关联不作为部署阈值。全阶段不重复计case、分层N/MRR
回算、来源文件hash一致性及报告链接已检查。未启动任何后续实验或多Agent。

## 2026-09-26 — RQ3.6阶段A正式完成及离线分析

按用户授权分析已完成A，不启动B–D、GPU或subagent。正式运行114.85分钟，
2640调用、2616份完整输出（含13份未知/重复候选零分）、24请求超时、无未解释
缺失；累计10899调用。Qwen超时涉及23例，共同97例，Gemma共同120例。
一次性离线核对19023项artifact hash、2603合法输出分数和1770输入一致性；
未增加任何续跑校验。注册Pratt/dz/Holm，另有事件组、超时和完整格子敏感性。
检验前差值round到12位避免浮点零值/并列误判，原始评分不变。

报告`docs/experiment_reports/RQ3_6_Stage_A_Analysis_2026-09-26.md`含7图及CSV；
复算脚本`RQs/RQ3_6/scripts/analysis/report_stage_a.py`。Qwen W macro=.4867，
Gemma E_S_D_P=.4290，但未确认跨模型统一新方法。Qwen P公共接口对原生T
pooled Δ=.1017、Holm=.0055、事件组=.0097；不是选择器/视觉贡献。S增加根因
关联记录但仍可能丢失关键内存等机制；pod/node取舍和W宿主误归因由输入轨迹
支持为后续假设，不从真实标签生成路由。W Qwen6修复/1破坏、Gemma2/5。
建议收窄B，保持原固定P0/D_P，只研究W资格、范围绑定和同事实图文；未改协议
或启动实验。findings、计划状态与报告索引同步，原结果/评分/配置均保持。

## 2026-09-26 — RQ3.6 A部署与资格通过，按要求停止

实施研究计划的A阶段11条件；B–D依赖阶段结果，未以占位分支进入dispatcher。
五模块+init、只读复用RQ3.4公共context/G图和RQ3.5精确指令块；八核心有界
预取、36并发、done/timeout fail小flag续跑，无全量缓存核验。40000累计调用
不重置，只导入RQ3.5历史8241次。未创建正式授权，未启动正式队列/训练/attention。

三轮独立静态（逻辑、运维、泄漏/语法）后运行CPU：6单元、3例×11×2=66请求，
最终9.914秒。发现并修复deferred import、projection hash序列化和GPU
post-response image_hashes接口。9个已生成Qwen回答保持原prompt/输出/评分，
仅离线完成缺失audit和flag；重测CPU后Gemma完成9次。全逻辑smoke累计18次、
原600秒窗口内558.820秒，18/18完整落盘；未重新抽样或重置时间/预算。

源单位追溯确认P0部分Trace保存微秒却命名ms，独立RQ3.6 adapter仅改unit及
字段名，不改数值/排序/选择/G图；旧代码和结果不变。已登记受影响条件不可
逐字节复用旧请求。完整会话、18回答和3图审阅通过；实体类型误述/图引用错误
保留为模型行为，S输入的literal sidecar数字/关系覆盖不足不作零幻觉宣称。
记录：docs/issues/RQ3_6_qualification_2026-09-26.md及RQ3.6 results/manual_review。
两模型服务已退出；正式A最多2640次待用户授权，未提前部署后续科学阶段。

## 2026-09-26 — RQ3.5 A/B screen60 离线分析完成

用户授权分析已完成阶段。本次不启动GPU、下一阶段或subagent，不改推理、
原始评分与结果。A/B共1440逻辑单元：1437完成、3请求超时；1248次正式新增
调用，192逻辑复用。队列正常completed_screen_ab，未进入check/C/D/test。
新增离线脚本`RQs/RQ3_5/scripts/analysis/report_screen.py`，报告与6张图及样本级
CSV在`docs/experiment_reports/RQ3_5_Screen_Analysis_2026-09-26.md`及其assets。
核对原始输入/输出、8622项必要文件存在性、得分一致性及跨模型/无操作输入。
未进行大文件全量重建。按共同完整病例和原注册family分别报告分母。

主要发现：SIRCL证据+父版指令的macro MRR为Qwen .4006/Gemma .3836，值得
复核但正向增益未获多重比较确认；Gemma换SIRCL指令平均效应-.0692，case
Holm p=.0241、事件组Holm p=.0727，伴随候选数/AC@5下降而非一致Top-1下降。
J只在28/60病例生效，105包全为request、scope为0；实际干预子组也未显示
稳定净收益。12组/10例轨迹复核显示绑定错误、显著症状竞争及模型间相反响应。
建议优先限定范围复核A，暂不自动扩张J视觉化；仅建议，未改注册或执行队列。

离线修正运行summary把entity类型表当granularity的分层错误（不改变评分）；
另记录P0/SIRCL时长投影差异的实际例子，限制纯选择器归因，保留冻结结果。
静态检查通过；报告链接和主要数表复核。历史qualification过程保留如下。

## 2026-09-26 — last-GC 时钟修复、补验通过并重启原队列

用户批准上一轮提出的遗漏GC时钟修复及4次补验。采用RQ3.5-local显示适配，
只转换两个均值，沿用原公共原点，不重新选择证据、不改标准差、不重做准备。
新输入guard覆盖last-GC；原始大内存/计数字段不按时间处理。静态及28项单测
通过，正在做120请求CPU回归、60例输入范围核对，再进行两模型共4次补验。
补验成功并检查实际输入输出后才恢复原A/B screen60；原38份结果已清除，
不再重复删除。其他RQ、模型配置、attention关闭与40000总调用上限不变。
结果：28单测、120请求CPU回归通过（25.00秒）；60例×20条件一次性范围核对
通过（107.00秒），仅17例×3个SIRCL条件改变，1149份输入不变，容量通过。
4次GPU补验全部完成（213.02秒，stop，非法ID为0），实际输入及完整输出
审阅通过。A/B正式队列已按原范围从零启动，启动前1440单元全pending。
原38次消费仍计数，重启前累计6993调用。没有新训练、attention或范围扩展。
详细协议见DD-RQ35-05，运行证据在`repairs/gc_clock_v1/`及formal_queue_status。
交接确认：队列PID37481已进入A/Qwen正式推理，新完成5/360，36请求在途；
GPU约85%，无新增错误。60份准备直接跳过，准备进程约5秒。停止人工监控，
后台队列继续；后续状态以formal_queue_status和小型done/fail标记为准。

## 2026-09-26 — 获批无损输入补验与38份正式结果清除重跑

用户批准12次定向GPU补验，并要求将此前38份正式结果全部清除后从头跑。
执行范围保持原A/B screen60，不扩至check/C/D/test。补验仍用原三例、两交叉
条件、两模型顺序运行，600秒总窗口；A累计smoke上限24→36，总调用不清零。
仅补验调度代码新增，先核对120请求身份完全一致。补验通过后删除旧正式输出、
完成标记和复用缓存，保留preparation、测试、其他RQ和累计消费记录；删除清单
及最终状态随后记录。此条是授权/计划，不提前宣称补验或重启完成。

结果：26项CPU测试、120请求身份核对通过（24.62秒）；12次补验在226.149秒
内全部完成，完整会话已检查，非法候选0。但实际输入审阅发现SIRCL路径遗漏
`istio_agent_go_memstats_last_gc_time_seconds`的相对时钟转换：补验2请求受影响，
screen中17例AIOPS-2022的3个SIRCL证据条件受影响。不是已证实读取注入时间，
但违反相对时钟契约。A标为failed_model_input_audit，未启动正式队列。
原38份正式结果已依用户指令全部删除：537文件、11,710,842字节；SQLite中的
答案缓存一并清除，消费记录保留，累计6989次。保留全部60份准备和补验记录。
最小下一步是RQ-local时钟投影修复/CPU检查，预计需另获4次定向GPU补验授权。
详情及删除清单见RQ3.5 issues和`repairs/formal_reset_20260926/`。

## 2026-09-26 — RQ3.5 全面逻辑审查及无损输入修复

用户授权修复并全面检查。覆盖五个功能模块、配置/队列及继承的请求、评分、
异步写盘和续跑边界。四个交叉条件改用分区域、逐字保留记录的文本块，消除
逐行JSON重复键与转义；未删除证据、改采样或扩大context。触发case的
E_S_D_P由Qwen38418/Gemma40691降至29471/31687输入tokens，均低于32768。
额外修复直接runner的基础设施fail跳过、模型选择和暂停提交边界；缓存重复
reference p95计算且计数等价；补齐已注册分析的macro、成本/故障分层、共同
配对集合和事件组敏感性。修复发布最终标记后置，可从中途发布恢复。

Ruff、格式及shell静态检查通过；24项CPU测试通过。60例×19条件×两模型
共2280项容量检查零失败，用时139.87秒；三例120请求集成回归通过，其中
24个交叉请求按预期改变，96个原生及B/C/D请求身份不变。最终核对还清除了
A资格中继承自上次补验的旧授权/已完成报告，避免将旧补验误读为新输入通过。

38份已完成正式结果全部保留：26份交叉结果不用于新版本，12份原生结果可复用；
60份preparation全部保留。普通续跑仍读小型状态及done/timeout flags，不加入
全量重建或重hash。A等待12次定向GPU补验的另行授权，B/C/D资格按请求一致性
证据保留；此次新增GPU调用为0，未恢复正式队列。详见
`docs/issues/RQ3_5_qualification_2026-09-25.md`及`repairs/lossless_blocks_v3/`。

## 2026-09-26 — RQ3.5 注销后恢复检查发现输入超限，尚未重启

用户要求从注销中断恢复、确认启动后停止监控。检查发现上次队列实际记录了A的
context超限退出，38/360 Qwen单元已done，60/60 preparation保留，无存活服务。
首个pending INC-1E6DCFC0A453的E_S_D_P输入Qwen38418/Gemma40691 tokens，
超过32768输入余量；原生SIRCL_IDS为29824/32035，能够装下。逐行JSON封装
增加了输入开销，并非原生证据必然超限。仅对该case做CPU tokenizer诊断，未调用
模型、修改源码、重做准备或重核验已完成结果。直接续跑会复现，因此未启动；
无损封装修订涉及模型可见输入，需确认后另行修复和核验。已记录于RQ3.5 issues。

## 2026-09-26 — RQ3.5 A/B screen 正式队列授权

用户要求启动并监控3分钟后停止助手监控，后台继续。队列限定来源准备/审计及
A、B的screen60：每项6条件×60cases×2模型，最多1440次正式调用；Qwen/Gemma
按实验顺序运行。不自动开启check120、C/D、test或新事件。复用3例准备，其余
57例仅增加所需索引；最多8个独立物理核心worker。已完成和timeout fail均读flag
跳过，其他基础设施fail需诊断；不做全量结果重建/重hash。正式模型启动前跳过
已经终结的model phase；SIGTERM停止提交、排空后释放自有服务。

新增RQ-local后台入口和小型状态文件；一次性运维激活保存旧源码/注册/资格，
检查既有函数AST与120请求身份一致后继承四项smoke，无新增smoke调用。实际启动
状态以`RQs/RQ3_5/results/outcome_linked_v1/formal_queue_status.json`为准。
静态检查、17项CPU测试及120请求身份比较通过；当前契约为
`d353320098f0020d28f3d2605f657f7d31a6e2004eb35b1f94364a1338cb79a8`。
14:44:09 UTC启动后台队列PID13906，监控约3分20秒：60/60准备完成、来源审计
正常退出，已进入A的Qwen模型启动阶段（服务PID14813），未见启动错误。
此时尚不能宣称正式推理已稳定产出；按用户要求结束助手监控，后台继续。
无训练、attention或其他项目进程操作。

## 2026-09-26 — RQ3.5 A 定向补验获授权

用户批准候选段去重后的6次GPU补验。仅原3个qualification cases × 两模型的
E_P_D_P，顺序运行，共用600秒窗口；原A的18次调用保留，同scope累计上限24，
大RQ计数不重置。新增显式补验调度及范围/预算测试，CPU核对科学输入不变后执行。
其余12份A请求及B/C/D保留，原记录不覆盖。无正式实验、训练或attention。
授权及补验产物位于`RQs/RQ3_5/results/outcome_linked_v1/repairs/candidate_once_v2/`；
结果待执行后登记，不能提前声明完成。

完成：静态检查、15项CPU测试和120请求身份一致性检查通过（21.35秒）；补验
Qwen3＋Gemma3在216.813秒内全部完成，均stop，无超时、基础设施失败或非法输出ID。
逐份确认只删除重复候选记录，其他输入、候选、schema和模型配方不变；全部会话
包含完整输入输出。A引用6新＋12原记录，B/C/D资格保留，四项当前均passed。
大RQ累计6939调用；原smoke不覆盖。reason里的类型/数值归属和因果过推问题按
模型行为保留，不用smoke成绩调参。启动警告未阻止两模型完成，无runtime修改。
自有GPU服务全部退出，未启动正式实验。详见RQ3.5资格问题记录及repair report。

## 2026-09-25 — RQ3.4四阶段完成与离线综合分析

正式队列16:05:20（America/Toronto）正常完成。3720逻辑单元＝3708 done＋12 request timeout；完整请求复用后3460唯一完整回答＋12超时＝3472次新正式调用。17份完整回答模型输出失败保留原零分，均非重试对象。原输入、图像、评分和配置未修改。

用户要求详细分析。新增 `docs/RQ3_4_Results_Analysis_2026-09-25.md` 及assets离线脚本、完整CSV/表格、八图、原G例图与conversation引用。共同病例配对、Pratt-Wilcoxon/dz/Holm、事件组敏感性、repair/break、候选提名、故障/层次/直接遥测覆盖、reason冲突告警与token成本分别分析；核对真实输入干预和六个命名case的原回答，非随机例子不作为错误率。

主方法check三数据集macro MRR为Qwen0.4219/Gemma0.3611，TPV0.4163/0.3458、MORE0.4414/0.3750；主要比较均未通过Holm。不加K的Qwen0.4468仅略高于MORE，未事后升格冠军。关系可核验与诊断相关性不同，部分类型/数值告警减少但MRR不稳定；选择性G视觉主要有排序修复线索。screen/check均已暴露开发资料，未达到独立高MRR目标。四份findings登记正式结论，历史资格过程保留。不启动新实验、训练、子agent或新的GPU调用。

## 2026-09-25 — 风扇曲线测试结束后恢复RQ3.4

用户说明暂停是为完成风扇curve测试，现明确恢复。原队列已安全paused，runner/vLLM均退出；恢复前GPU44°C、无计算进程。原60例screen准备全部保留；契约两模型360单元、因子Qwen600单元均有终结记录，因子Gemma停在37/600，无fatal。按原 `scripts/formal_queue.sh` 在独立session恢复，PID51831，日志 `RQs/RQ3_4/results/integrated_v1/logs/formal_resume_1790360297921435940.log`。跳过done/fail，不重做准备或大文件核验，不重跑smoke；Gemma剩余563单元及后续登记阶段继续执行，check120仍受原推进规则约束。未改代码、模型、输入、评分、GPU或风扇设置；停止助手监控，后台继续。

## 2026-09-25 — 用户要求立即暂停RQ3.4

用户在因子实验切换到Gemma后要求立即暂停。已向已核实归属的队列PID29135与runner PID50396发送SIGTERM，停止新提交并排空在途请求；由原supervisor清理自有vLLM组，不杀其他项目进程。此前契约两模型360单元及因子Qwen600单元已终结，其中3次request timeout按原规则保留fail。当前暂停不修改模型、输入、评分、源码或已完成结果；不允许自动继续后续阶段，需用户明确恢复。最终暂停状态和计数以 `RQs/RQ3_4/results/integrated_v1/formal_queue_status.json` 及当前模型progress为准。

## 2026-09-25 — RQ3.4正式队列获授权

用户授权正式运行并要求启动后停止助手监控。增加RQ-local后台调度，沿用已有prepare/run/analyze与40000累计计数；前三项screen60完成后，严格按原Qwen推进规则决定check120，不扩大实验矩阵。8物理核心CPU准备、Qwen/Gemma顺序运行、无attention/训练。启动前执行权限变更有独立归档及120个科学请求等价检查；旧smoke/失败/回答不覆盖。状态和日志存 `RQs/RQ3_4/results/integrated_v1/`，尚不在本条提前宣称已发起正式模型请求。运维授权与恢复方式详见DD-RQ34-07。

启动确认：静态检查、48项CPU测试及120请求身份等价全部通过；已有编译/选择/推理/评分函数AST不变，正式运维契约为 `bbab76d1f70d479ebdb27cd5d274282ffb51e0350f4efab86f734a99392abdf9`。普通shell后台首次未保留进程、日志为空且零调用，改用独立session可靠脱离终端；正式队列PID29135，准备PID29145，8个worker已启动、分别固定不同物理核。复用3例准备，补57例screen准备后自动推理；启动核查时尚未加载GPU、无新报错。助手按要求停止监控。启动前累计3395调用，最大追加正式3480；不新增smoke。入口及日志见运行根目录 `FORMAL_LAUNCH_20260925.md`。

## 2026-09-24 — 相对时钟定向 GPU 补验通过，未启动正式实验

补验入口曾把clock模式误传为旧布尔repair，Qwen启动后、请求前退出，0 calls；修正并加driver测试，45项CPU回归和120输入等价检查通过。失败105.31秒和日志保留并计入契约阶段600秒，不重置预算。之后契约6、因子4、图文6次新调用均完成，各209–211秒；锁定2单元同输入复用，0新调用。加54个未改输入引用，共72逻辑单元、36对跨模型输入核查通过；累计3,395 calls。16新回答全stop、无截断/infra失败；1非法候选、6份回答12处类型误称及其他reason错误保留为模型结果，不重试或改评分。详见`RQs/RQ3_4/results/integrated_v1/repairs/relative_clock_gpu_v1/review.md`。四项当前qualification已通过，原失败/flags/results不覆盖，所有自有服务退出；正式execution_enabled=false，无训练/attention。

## 2026-09-24 — 相对时钟定向 GPU 补验获授权并登记

用户授权补验18个改变输入的逻辑单元，不启动正式实验。四项独立smoke按原顺序、每项600秒；新增最多18次，预计两项完全相同请求可复用后实际16次。独立`repairs/relative_clock_gpu_v1/`保留补验输入输出，共用原calls.sqlite；原报告、flags和结果不覆盖，54个相同输入完成单元只引用。新增入口与复用检查经44项CPU测试、120请求身份等价检查通过；源码变化仅补验调度、相同模型/case/请求复用及测试。首次setup后只修正import静态格式，该无GPU的setup快照保留。协议详见DD-RQ34-06。结果待补验后登记，不提前宣布通过。

## 2026-09-24 — RQ3.4 时钟输入修复，CPU 通过，停止在 GPU 补验前

用户授权修复绝对时钟输入。新增 RQ3.4-local `relative_clock_v1`：三类来源明确的秒时钟共用公共 case-local 原点，仅平移模型可见值，保留前后差、跨实体差、MAD/std、选择统计与原始数据；未知时钟语义在请求前报错。真实回归发现先前遗漏的 SIRCL `container_last_seen`，三个 SIRCL 条件共同适配均值、不改标准差；旧实验代码及结果不动。

42项测试、Ruff/shell检查、三个case的120请求CPU回归通过。96请求不变、24改变；12组P/H证据集合、TPV/MORE请求和G图均不变。已执行smoke受影响18逻辑单元（契约6、因子4、图文6、check2），四项状态为cpu_fixed_gpu_pending，不能沿用旧输入资格。缓存修复与检查53.64秒，CPU资格本身16.15秒，未重新跑全量preparation。原输入、失败CPU尝试、原回答和partial均保留；本轮0模型调用，总计仍3379，无训练/attention/正式运行。详细依据及产物：`docs/issues/RQ3_4_qualification_2026-09-24.md`、`RQs/RQ3_4/results/integrated_v1/repairs/relative_clock_v1/`。本轮修复后停止，尚需有界的定向GPU补验。

## 2026-09-24 — 第三项授权补验完成，输入复查发现时钟字段阻塞

用户批准一次性≤16新增calls／≤600秒补验，仅第三项，同scope累计上限25，不重置计数。新增显式repair入口与授权约束；36项CPU检查、120份完整请求身份等价通过，操作性源码迁移单独保存。第三项18单元（16新＋2缓存）250.50秒完成；原失败及7份partial归档，两份原output字节不变。总79次新请求＝72完成＋7中断，承接历史3300次后计3379。无新Z3/infra错误，自有服务退出，没有正式实验。

完整回答/输入审阅发现新阻塞：追加观测暴露 `container_start_time_seconds=1647145400.0`，属绝对容器启动时钟，非已证实根因/注入时间泄漏。全部72完成单元中12份受影响（同一AIOPS2022 case：因子4、图文6、check2），后三项资格设为blocked_input_privacy；原运行报告不改写。需要语义感知的相对时钟投影或登记排除，保留restart信号，修复后按真实输入变化定向资格；本次GPU授权已用尽，未自行再跑，尚未修改科学输入。机器清单`RQs/RQ3_4/results/integrated_v1/smokes/absolute_clock_input_audit.json`，详见`docs/issues/RQ3_4_qualification_2026-09-24.md`。回答中的类型/因果推断错误按模型结果保留，有限核验不代表全面正确。

## 2026-09-24 — RQ3.4 合并路径实现与资格测试

用户授权完成代码、CPU 回归和 GPU smoke，未授权本轮自动正式运行。新增五模块内的 P/H/K 选择、scope 对照、真实可见事实编译、两模型共同 token 预算、独立回答核验、flag-only 恢复及分阶段分析入口；保留父版源码和全部历史结果。数值与实现边界登记 DD-RQ34-03。新命名空间 `RQs/RQ3_4/results/integrated_v1/`，正式 execution_enabled=false。

Ruff、shell 语法和 registration 通过。首次CPU资格：34项单元检查、三个真实主数据集 case 的120个 arm×model输入编译检查通过，总34.07秒；新增准备15.43/16.69/19.47秒，各绑独立物理核心，仅补读metrics，复用完整公共池／旧TPV图。P/H真实改变内容；同图复用和图文alias检查通过。查看三个原G图、追加观测、关系和完整conversations，不借资格调整画法。

契约和因子smoke各18/18完成（232.63/243.18秒）。第三项发起9次后Z3段错误，内核日志定位libz3；两份回答完整落盘、七份partial保留。默认context即使用短锁也可能在锁外析构；改每个核验器独立context、全部AST显式绑定，并记录子进程exit code。源码迁移归档，修复后35项CPU测试（含384次并发创建销毁）通过；120个完整请求身份不变，190次真实回答回放verdict一致。第四项在修复后18/18完成（250.97秒）。共63次新请求，含失败9次；已承接3300次历史计数，总3363。七条遗留started明确改为interrupted，不自动重试、不拼接partial。

第三项原failed状态不改写；完整补验需最多16次新请求，超出本项18-call上限，已请求一次性例外，未授权则保持待补验。没有全量实验，没有新attention；所有自有测试服务已结束。详细问题及下一步见 `docs/issues/RQ3_4_qualification_2026-09-24.md`。三个smoke通过不等于方法有效。

## 2026-09-24 — 原诊断路线与自动推理合并登记（未运行）

用户要求合并下一轮研究。RQ3.4 不再仅聚焦核验：输出／候选契约单独校准；证据优先级P、宿主—实例scope H、可核验关系K做全2×2×2并保留TPV/MORE；固定P1H1比较图文与普通重述；达到预登记MRR条件后才在旧check120锁定复核。主方法预先固定，避免逐阶段换冠军；MRR与解释可靠性分开，核验不改原排名。

登记 `RQs/RQ3_4/configs/integrated_round_v1.json` 与三份descriptions；四份新findings明确未运行。首轮2,094计划calls，条件式后续1,458，最多3,552，不叠加旧738-call聊天建议，不重置大RQ预算。资料均为已暴露eval开发组，不打开新test。此次只改设计文档和登记配置，未改实验实现／旧结果，未运行CPU实验或GPU。已完成的20项CPU核验回归不作为新GPU路径资格。完整说明同步到最新跨RQ计划，下一步为实现和资格测试。

## 2026-09-24 — RQ3.4 事实核验 CPU 可行性

用户授权推进下一步并推荐 CARS；在 RQ3.3 阴性开发结束后，选择先实现公开事实核验而不是扩大旧方法。新建 RQ3.4 的三份协议、五功能模块和 CPU 审计入口，旧 RQ 代码／结果／评分不动。文献核查包括 CARS（ICML 2026）、SAT-LM（NeurIPS 2023）和 LINC（EMNLP 2023 main）；不把精确约束采样或事实自洽当作 RCA 正确性保证。

最终审计 120 cases × 5 arms × 2 models：1,197 个完整回答、3 个原超时有明确记录，约 3.57 秒完成核验和汇总。14 份候选契约错误与原 scorer 检测重叠；247 份解释有字面断言冲突候选，不能称已确认幻觉率。抽查发现量的绑定歧义，后续必须保留 unknown／人工式复核。20 项 CPU 回归及 Ruff/语法检查通过；零模型调用、无训练。详细协议、独立审计版本、实现修复和 findings 位于 `RQs/RQ3_4/`，最终结果 `results/claim_audit_v4/`。下一步是强基线上有对照的事实／关系编译研究，尚未开启新 GPU 实验。

## 2026-09-23 — RQ3.3 超时配置兼容修复并续跑

用户授权修复20:20校准退出。仅允许完整配置hash精确证明的timeout1800→300变更，保留模型、采样、输出等其他差异的fail-fast；增加GPU加载前全部120条历史runtime元数据检查（111相同、9仅timeout）。51项CPU回归及Ruff/shell检查通过；定向CPU核查15.90秒，旧smoke90个完整输入不变，故障case双模型六个SC输入均编译通过。60份准备物与1份已有正式结果保留，无新增GPU smoke或全量重新准备。

显式契约承接及旧资格快照位于`RQs/RQ3_3/results/witness_v2/contract_migrations/calibration_timeout_only_v1/`，新契约`e0ab9bb7e75bbdda46d0bad8959e6e57ef30b54f1f69307590b46dc5247fdafe`。20:41:03重启队列PID105361；恢复预检及完成flag读取后约0.5秒即进入模型加载，未重建已完成请求。启动观察确认进入Qwen校准，已完成7/240逻辑单元（含原1份），5次正式调用完成、28次已提交处理中；此前故障case的GUIDE_FIXED/SOURCE_FIXED已有新结果，未再次触发runtime差异错误。日志`logs/formal_queue/supervisor_20260923_204103_timeout_compat.log`。模型结果未用于调整实验，继续既定队列，本轮启动确认后停止监控。

## 2026-09-23 — RQ3.3 队列准备中断与身份适配修复

正式队列尚未调用模型，在第19份准备物遇到旧parent数字ID与当前公开node/pod元数据冲突。修复仅落RQ3.3：兼容缓存复用，绑定不一致的case定向重建；历史SC校准/TPV_BRIDGE保留原输入及原评分映射。45项CPU回归、故障case双模型18个编译检查、旧smoke90个请求相等性检查通过；18份准备物保留，定向重建1例48.08秒。未新增GPU补验调用，未重跑/修改旧科学结果。源码迁移和原资格快照在`RQs/RQ3_3/results/witness_v2/contract_migrations/public_metadata_identity_v1/`；踩坑记录在`docs/issues/RQ3_3_implementation_review_2026-09-23.md`。用户授权修复后续跑剩余准备任务及登记的正式队列；不新增恢复时批量校验。

20:12:34本地重启队列PID93316，启动核查确认8个worker各绑定不同物理核心，正在处理screen剩余41份准备任务，已有19份跳过。状态入口`formal_queue_status.json`，日志`logs/formal_queue/supervisor_20260923_201234_identity_repair.log`（均在`RQs/RQ3_3/results/witness_v2/`）。累计调用仍139，含53历史失败/补验尝试；启动时没有新错误。准备结束后自动进入已登记顺序，本轮按用户要求启动后停止监控。

20:20再次退出的只读诊断：preparation已60/60，Qwen校准TPV_BRIDGE已完成1次；下一SC历史请求被完整配置hash检查拦截。120条manifest中9条Qwen历史配置仅因已授权的timeout1800→300改变hash（用当前配置单字段还原精确验证）；不是模型/证据变更或GPU OOM。原smoke三例均未覆盖这9例。当前尚未修复/重启，60份准备物和1份正式结果保留，累计发起调用140。详见同一RQ3.3踩坑文档最新条目。

## 2026-09-23 — RQ3.3 CPU性能与日志单位修复（资格调试）

原消息日志分组产生24万级候选；JSON键顺序/动态参数进一步碎片化模板。改为完整源行索引绑定的模板级phase统计，保留实体、状态码、数值摘要及分母；新Witness输入投影重新资格，旧正式结果不改。进一步修复P0_MORE重复tokenization（有认证边界的精确缓存）、全量Denum平方级去重、Trace反复全表扫描，以及CPU/smoke样例不一致和smoke只取旧基线的问题。数据原件、父版源文件、推理配方不动。

最终三例CPU回归106.58秒通过：AIOPS-2022从超过27分钟未完成降至89.01秒，AegisLab377.95→44.70秒，AIOPS-2025 19.88→9.73秒；包含对照准备，不是推理或系统端到端latency。32项单元检查、80项真实输入检查通过，另31项注册条件不适用；两模型各321段文本的精确缓存与完整分词一致。三例原TPV输入、父版追加候选、Trace群体及P0_MORE选择保持一致。冷日志聚合、部分截图条件不可执行和缺失来源校准manifest仍需明确处理；本轮没有GPU调用或正式实验。详见`docs/issues/RQ3_3_implementation_review_2026-09-23.md`及本RQ协议，资格产物位于`RQs/RQ3_3/results/witness_v2/`。

This is the only project-wide devlog. It keeps decisions that still affect the
current study, important reversals, validity changes, and reproducible artifact
locations. Repetitive operational narration and superseded execution plans were
removed on 2026-09-15. Detailed experiment records remain under each RQ's
machine-local `results/`; settled RQ1.1/RQ2.1 findings and retained incident
records are under `docs/`.

## RQ3.2 completed-run analysis — 2026-09-22

Offline report: `docs/RQ3_2_Results_Analysis_2026-09-22.md` (10 statistical
figures and 2 original dashboard examples). Current-task reconstruction gives
27,280 terminal units: 26,995 scored outputs including 346 model failures,
129 timeout causes and 156 non-applicable interventions; one noncurrent
output excluded, nothing deleted. SC restores node telemetry but does not
consistently beat strong baselines; full vision loses to the same SC textual
carrier; targeted deletion provides limited evidence dependence. Actual-input
audit also identifies text NO_GROUPING no-op and control/guide mismatches,
recorded in `docs/issues/RQ3_2_issues.md`. All original experiment artifacts
and scores are unchanged. No inference, training, pipeline repair or rerun
was started. Detailed per-RQ log remains with the formal run.

## Next research plan — 2026-09-20 (documentation only)

The user-confirmed RQ3.2 SignalCover plan is saved in
[CanvasRCA_RQ3_2_Research_Plan_2026-09-20.md](../docs/CanvasRCA_RQ3_2_Research_Plan_2026-09-20.md).
It uses tournament case-pattern evidence and RQ3.1's asymmetric loss/addition
of root-associated metrics to motivate P0 backbone retention, mechanism/level
coverage and bounded contrast completion, not an ensemble of past winners.
The four planned experiments separate selection, representation, mechanisms
and locked generalization; core maximum is 28,432 calls within a 40,000-call
RQ3.2 ceiling, not a new lower hard cap. Existing test360 becomes explicitly
exposed regression evidence; an unused-event audit may support up to 30 new
cases per primary dataset, without assuming unused means untouched.

This session only writes the plan and this status entry. No RQ3.2 source,
executable registration, preparation, CPU/smoke qualification, inference or
training has been performed. Prior source/results/model recipes and data
manifests remain unchanged. The plan contains the supplemental count sources
and marks the metric-coverage/MRR associations as descriptive, not causal.
RQ3.2 is the next research direction; older dated RQ3.1 execution statements
below describe their historical scope and are not RQ3.2 execution authority.

## Historical authority — 2026-09-16

- Research-plan revision 8 is implemented in `research_v2.json`: direct table
  contrast X_C_TABLE, its screenshot control and table budget/load tests;
  no engineer/user study or mandatory independent annotation. The increment is
  2,680 calls; formal 26,360; cumulative allocated core 26,432; reserve 13,568
  within 40,000. Static checks pass; CPU/smoke/model execution remain pending.
- Formal preparation did not complete: it stopped after 141/480 durable contexts
  when the old global identity scan mistook the public trace operation `set` for
  a raw entity. The successor validates TRC-L's numeric service column while
  retaining operation semantics. No formal inference call started. Existing
  context bytes are retained and may resume only between the pinned predecessor
  and successor implementation/config hashes; later changes do not inherit the
  exception automatically.
- RQ3.1 uses the user's 40,000-call ceiling. The narrower agent-drafted limit
  has been removed from active configuration, runner/recovery defaults and
  plans. Its independent user provenance was not established and must not be
  asserted. The matrix remains 23,680 formal calls; cumulative core including
  qualification and prior 18 calls is 23,752; reserve is 16,248. The earlier
  cap had not stopped a model call, but did restrict planned repair headroom.
  No inference or tests are authorized by this correction.
- CanvasRCA runs locally only. The `_nibi` worktree name is historical; no new
  Slurm/Nibi jobs or API inference are authorized.
- The first paper uses a frozen one-stage RCA Solver and studies evidence
  selection plus verifiable visual organization. Composer SFT/RL is deferred.
- RQ480 is the repeated-exposed method-development/selection eval set. It is
  not optimizer training data and is not an untouched test set.
- The registered data roles are train300 / eval480 / test360 / unused1403.
  Test contains 120 cases each from AIOPS-2022, AIOPS-2025 and AegisLab; all
  RE2 cases remain in eval. The former AIOPS validation140 is included in test
  with its exposure provenance retained. There is no active validation split.
- The current research plan is
  `docs/CanvasRCA_Research_Plan_2026-09-15.md`, revision 8. The old static pause
  was superseded by later CPU/smoke/formal authorization; runtime artifacts, not
  stale narrative status, determine actual progress. Current work is plan-only,
  then stop. New controls still require versioned implementation, registration
  and qualification; no existing smoke proves their behavior.

## 2026-09-16 — direct textual contrast and an affordable evidence chain

User identifies "why not use text for contrast?" as a central validity risk,
and has no resources for a participant study. Source inspection confirms that
X_C emits bundle references and a separate observation catalogue, not an inline
comparison table. Plan revision 8 preserves it and proposes X_C_TABLE on eval480
and test360, its exact-text screenshot on the fixed 100-case subset, and table
budget/load counterparts. Increment: 960 + 720 + 200 + 400 + 400 = 2,680 calls.
No active source/config/request or result is changed by this decision.

Visual claims must face the direct text comparator; benefits from selection,
pixel transport and visual organization are evaluated separately. Planned final
Holm family expands to 24 comparisons, with explicit secondary screenshot and
paired budget/load change-score families. Method choice remains eval-only;
test never selects the weaker comparator. Old outputs stay versioned and are
reused only when their complete contracts match.

Participant recruitment and mandatory two-annotator review of 600 responses are
removed from the paper's required work. Automatic source-bound assertion checks
report supported/contradicted/unsupported/unresolved cases with coverage and
empty-denominator handling, not complete reasoning quality. Controlled removal
measures dependence on root-associated observations, not hidden causal reasoning.
Human productivity and MTTR remain outside current claims. Author engineering
inspection of images/code is still required and is not a user study.

Decision is recorded in the latest research plan and DD-RQ31-09 in the RQ3.1
experiment description; statement and qualitative roadmap agree. This session
only edits documentation and checks its consistency. No new literature result,
model result, human annotation, implementation or qualification is claimed.
Stop after this handoff as requested; do not automatically implement the additions.

## 2026-09-16 — RQ3.1 independent per-case branches; static-only pause

User rejected the shared MET-Z/TRC-L/LOG-R/Denum candidate-pool prerequisite.
X now starts from canonical per-case public tables and graph, with its own
signed metric summaries, complete trace-group union, identical-message log
groups and concrete topology. Shared loading does not run analyzer selection.
P0/SIRCL retain their own analyzer branches; P0 calibration no longer substitutes
X statistics. Same-X representation twins remain controlled. Source-policy
comparisons include extraction, reference partition and selection, not only
ranking. Standalone observations can use the quarter-budget coverage reserve
without being mislabeled as competing-root bundles.

Formal preparation from the previous version was stopped and its two newly
generated directories removed on user request before any formal model call.
Canonical per-case data, all previous RQs and previous smoke evidence remain.
No CPU test, preparation, rendering, smoke or inference was run in this revision.
Future qualification must use the changed implementation/config hashes.

Recomputed allocation: formal 23,680; prospective qualification allowance 54;
prospective core 23,734; historical initiated calls 18; cumulative core 23,752;
hard ceiling 40,000; remaining unallocated repair reserve 16,248. Original Solver
recipes and disabled-attention setting are unchanged. Detailed contract and
static review live in `RQs/RQ3_1/descriptions/`.

## 2026-09-16 — implementation integrated; static-only handoff

Unified source-bound preparation, evidence selection, P0 calibration, all
registered request variants, bounded inference submission, exact-request reuse,
retry artifacts and two-model summary reconstruction. Removed obsolete runtime
mock/fallback paths; the mocked CPU execution helper lives only in tests.
P0 calibration now uses the same current public projection as X while retaining
parent selection; original baselines are untouched. Calibration effects must
be reported separately from selection effects.

Static checks passed for 44 Python sources, 233 local imported symbols, two JSON
configs, six shell scripts, Ruff F and changed-code import ordering, plus
`git diff --check`. The five modules plus init occupy 5,985 nonblank/noncomment
lines (docstrings included). Details are in
`RQs/RQ3_1/results/team_stage1/static_review_20260916.md`.
These checks do not execute tests or establish runtime correctness. Earlier
68-test CPU evidence predates these changes; candidate budget 96 and the
interrupted capacity audit remain unqualified. No subprocess experiment was
launched, no test telemetry opened and no shared model recipe changed.

## 2026-09-16 — active work switched to one agent

The user stopped the multi-agent workflow because of token overhead. A, B and C
had already persisted their source and CPU evidence; all child sessions are now
terminal/interrupted and must not be resumed automatically. One primary agent
inherits their work and will perform the remaining representation correction,
integration, qualification, experiment operation, statistics and stage review.
D and E were never started. This operating change does not weaken their former
quality gates: complete-result statistical analysis and stage-level academic
critique remain required, but are now performed by the primary agent.

At the switch, no GPU/model/formal experiment was running. A budget-96 CPU-only
evidence qualification process launched before the switch was stopped on the
user's subsequent pause instruction. It completed two Aegis eval cases but did
not write its complete summary; those partial files are non-authoritative and
may be resumed or rebuilt without any model call or test access. The integrated
RQ3.1 CPU suite passed 68 tests. The source package is not yet stage-complete because the standard
semantic budget remains unfrozen and processor-space readability/display-load
corrections still require final inspection. Therefore smoke and formal inference
remain unauthorized.

## 2026-09-15 — autonomous RQ3.1 team started

The clean worktree at commit `de3027724` contains a completed data registration
and five passing split tests, but no implemented contrastive RCA experiment.
No project-owned inference/training process was running at handoff. A (Sol/high)
owns evidence pools, complete contrast bundles and budgeted selection; B
(Sol/high) owns same-fact representations and a local renderer; C (Luna/high)
owns registration, execution, recovery and integrity. Their first assignments
end after runnable CPU-tested interfaces and written handoffs, without model
calls. The leader owns integration and the current protocol. D (Sol/xhigh)
starts only on complete, writer-drained experimental results; E (Astra/xhigh)
reviews each completed major stage and remains read-only.

Major stages: integrated method/protocol and CPU/visual checks; complete eval
development with method selection; mechanism/robustness evidence; locked test
and final synthesis. E reviews every stage; D precedes E for empirical stages.
Stage artifacts go under `RQs/RQ3_1/results/`, preserving the single-plan and
single-devlog cleanup. The requested final target is primary-Qwen test MRR
>=0.65 with both AIOPS datasets >=0.60, plus the complete publication evidence
chain. Target attainment must be observed, not promised. All planned controls,
negative results and test exposure provenance remain reportable. Test is not a
repeated tuning loop, and the current total budget remains 40,000 calls.

The user also requires night-time shutdown/resume. Team assignments and
incremental handoffs are durably recorded in
`RQs/RQ3_1/results/team_stage1/`; experiment recovery must pass interruption
tests before model execution. No assumption is made that an agent session
survives a reboot. Recover from saved source/artifacts/next commands and inspect
real process state before resubmitting incomplete targets.

The leader's first integration review found substantive gaps despite passing
component tests: candidate-pair semantics, residual network identifiers,
representation duplication/capacity, unknown values rendered as zero, and
experiment-matrix/resume gates. A/B/C received bounded corrections before any
model request. Stage 1 is not accepted; D/E remain unstarted. The source-level
review and each member's recovery handoff are in `results/team_stage1/`.
The experimental protocol now fixes method selection, named Holm families,
failure denominators and the `T_COMPACT` versus `X_C` distinction before new
outcomes. The sample budget is provisional, not a formal capacity decision.

On 2026-09-16 WSL restarted during the team's CPU repair stage. Live process
and agent inventories confirmed the old workers were gone, not merely slow.
All source edits and A's partial semantic-repair handoff survived. The leader
restored A/B/C from disk under the same file ownership and model settings;
there was no model call or running scientific experiment to duplicate or
invalidate. `team_state.json` records current recovery-agent identities.

The second review did not accept the first C integration: arm mapping, shared
RCA prompt, target/control removal, time-alignment/re-anonymization semantics,
and bounded supervision still had confirmed errors. Scientific intervention
implementation was reassigned to A, prompt/render changes to B, and execution
to C. All remained CPU-only. The first valid-looking capacity gallery also
retained excessive empty single-edge panels; source PNG success was not treated
as proof of VLM readability or a reason to freeze an undersized evidence budget.

The next CPU pass compacted comparison tables and shared trace/topology views
without deleting selected facts. All three saved 128-budget samples now fit;
Gemma's actual CPU image processor was inspected as well as source PNGs. A
broader nine-case CPU check is still required before budget registration.
The leader preregistered a 10% character-scale tolerance for otherwise matched
private removal controls, and complete-bundle display-load prefixes with
explicit overshoot/degenerate-level accounting. Duplicate pressure must repeat
the readable evidence, not merely add short references. A direct canonical
scorer check passed in the correctly sourced local inference environment;
the earlier missing-upstream warning was an unsourced-environment limitation,
not an absent installation. No new model call has yet run.

## 2026-07 to 2026-08 — foundation and invalidated predecessors

The repository established deterministic dashboard rendering, label-private
case views, case-local service/pod/node identifiers, unified scoring, token
accounting, resumable writers, and local vLLM recipes. Early RQ0/RQ1 work tested
text, flat, visual and mixed representations, plus several routing/two-stage
ideas. The routing and early multi-stage routes did not provide a stable gain
and were abandoned for the first paper.

All model-call results produced under the old `vllm-inference-v1` contract were
later archived as invalid for scientific claims. That decision did not alter
CPU-only renderer/data artifacts and did not rehabilitate failed or incomplete
runs. Qwen3.6 was removed from the active study; Qwen3.8-27B and
Gemma-4-26B-A4B-it became the registered frozen Solvers. Local recipes remain
model-specific and unquantized.

The project temporarily used Nibi/H100 and local hardware interchangeably.
Operational differences and preparation drift made the workflow difficult to
audit. The project subsequently standardized on local execution and stopped
using Nibi. Historical cluster scripts may remain as code provenance, but they
are not execution authority.

## 2026-08 to 2026-09 — RQ1.1

RQ1.1 narrowed the paper to one-stage RCA and tested text, screenshot, full
vision and modality-selective visual arms, along with direct QA and a bounded
counterfactual mechanism study. Image and text attention were recorded for the
completed historical experiments, but attention is treated only as a
correlational diagnostic.

A raw-to-processed consumption bug was found: an earlier consumer omitted
fields present in the source schema, weakening pod/node/process evidence. Old
derived experiments affected by that processor were cleared rather than
silently reinterpreted. The SIRCL-compatible processor was moved into the
project, made self-contained, tested against the reference transformation, and
used to build canonical V3 per-case data and the frozen RQ480 roster.

The valid RQ1.1 rerun found that visual representation can improve some RCA
arms and reduce input tokens, but full vision is not uniformly best and output
tokens do not automatically decrease. Topology-selective vision was a strong
Qwen condition. Effects varied by model, dataset, fault type and root
granularity. Direct QA exposed perception and formatting failures, but QA
accuracy— including root-connected questions—had weak association with RCA
ranking. Counterfactual inputs showed that the Solver does use visual evidence,
while also revealing shortcut and ranking failures. The consolidated numbers,
figures and caveats are in
`docs/RQ1_1_RQ2_1_findings/findings.md`; implementation incidents are retained
under `docs/issues/`.

## 2026-09 — old RQ2 abandoned and RQ2.1 completed

The first RQ2 implementation introduced a new renderer/design pipeline without
a strict RQ1.1 bridge. Its named tool profiles also collapsed to identical
model inputs, so the tool comparison could not identify tool effects. RQ2 was
abandoned in full; its source remains historical, while generated results were
removed after a retirement audit. This failure is retained because it directly
motivated input-identity checks and fixed anchors.

RQ2.1 restarted from the RQ1.1 P0 bridge and separated three interventions:
evidence selection, silhouette encoding, and canvas composition. It evaluated
both Solvers over RQ480 with fixed anchors rather than claiming a sequential
champion was globally optimal. Results showed that evidence selection matters,
but many new designs did not beat P0; encoding/layout effects were conditional
and often model-specific. Resolution and density did not yield a universal
monotonic optimum. Tool arms were audited at the actual-request level so
same-input reuse could not masquerade as an intervention. The authoritative
findings are merged with RQ1.1 in the single findings document above. RQ2/RQ2.1
operational pitfalls remain in `docs/issues/`.

## 2026-09 — RQ3 historical training branch and elimination tournament

A Qwen3.5-9B dashboard Composer was prototyped with a structured card/silhouette
DSL. Format SFT reached update 320 and improved schema/binding/render success
relative to the base model, but this did not establish downstream RCA benefit.
The proposed full RL lifecycle was therefore not promoted into the first-paper
main line. Checkpoint retention used latest-plus-every-20 during that historical
run. No current plan resumes those checkpoints automatically.

The subsequent elimination tournament explored complementary evidence
selectors without training. Each round ran only cases not previously solved by
that model; union coverage therefore measures the combined reach of many
attempts, not deployable single-call accuracy. After 38 committed rounds the
user stopped the tournament. AC@5 union coverage reached 96.7%, while persistent
AC@1 failures and many top-five-but-not-first cases pointed to competition
between plausible roots and ranking errors. The only tournament report is
`docs/Tournament_Analysis_2026-09-15.md`; it records per-round methods,
AC@1/3/5, covered/uncovered case profiles and the proposed contrastive selector.
No further tournament round is authorized.

## 2026-09-15 — RQ3.1 research direction and data roles

The new first-paper direction is a deterministic, contrastive evidence
compiler for a frozen one-shot Solver. It compares competing root explanations
using public telemetry and represents selected evidence as text, compact text,
screenshot or a real dashboard. The goal is high MRR plus grounded entity,
temporal and relational evidence—not visual novelty alone. Training is a
conditional later extension only if a fixed method first establishes useful,
case-dependent design actions.

The earlier proposal for a wholly unexposed 480-case test was infeasible with
the available AIOPS pools and was superseded by explicit user instruction.
The accepted versioned registration uses:

| Dataset | Train | Eval | Test | Unused |
|---|---:|---:|---:|---:|
| AIOPS-2022 | 150 | 100 | 120 | 171 |
| AIOPS-2025 | 150 | 100 | 120 | 30 |
| AegisLab | 0 | 100 | 120 | 1202 |
| RE2-OB | 0 | 90 | 0 | 0 |
| RE2-TT | 0 | 90 | 0 | 0 |
| **Total** | **300** | **480** | **360** | **1403** |

All 2,543 identities occur exactly once. Old train and RQ480 identities are
unchanged; all former validation140 are in test. Five CPU tests, deterministic
byte checking, independent public/private partition comparison, protected
source hashes, and Aegis source/event/window reconstruction passed. Active
train/eval/test event-window group crossings are zero. Public rows expose only
dataset and opaque ID. This accepts the data registration only; no telemetry
row, model call, renderer, smoke, training or formal experiment ran.

Artifacts:

- `RQs/RQ3_1/configs/data_split_v1.json`
- `RQs/RQ3_1/results/data_registration_v1/summary.json`
- `RQs/RQ3_1/results/data_registration_v1/registration.json`
- `RQs/RQ3_1/results/data_registration_v1/private/split.json`

## Persistent validity and operating rules

- Labels, root cause, fault type, absolute injection time, raw case identity,
  dataset name and paths remain evaluator-private and never enter model-visible
  evidence.
- Candidate identities are case-local numeric aliases. Scoring is
  granularity-aware: service predictions may resolve hashed pod aliases, while
  pod/node labels remain exact.
- Full conversations, requests, outputs, per-case metrics, failures and costs
  are recorded asynchronously for every future experiment. Infrastructure
  failures are not model-quality failures; parse/format failures remain model
  outcomes under the registered policy.
- A real dashboard, pixel screenshot and pure text are distinct. Selection must
  change actual evidence, while representation twins must preserve their
  registered semantic facts.
- Completed historical results retain their original validity class. A new
  verifier or operational rule cannot silently invalidate accepted evidence or
  rehabilitate invalid evidence.
- New inference uses local project-owned vLLM only. Model scientific settings
  remain frozen unless a new versioned experiment explicitly changes them.
- Temporary analyses belong under ignored `tmp/`; generated results, renders,
  attention, checkpoints and conversations stay machine-local and ignored.

## Current next step

Stop after the requested code/static-review handoff. Run the full CPU suite and
visual/token qualification against `research_v2.json`, then one bounded smoke
per logical experiment. If those pass, resume the 141/480 eval context cache,
complete the expanded eval and mechanism queue, freeze the visual method, and
only then prepare/open test for the eight-method final comparison. No process is
currently running and no formal model call has started.
Continue single-agent ownership. Do not restart abandoned RQ2, the tournament
or Composer training. Test remains separated from method development.

## 2026-09-16 — RQ3.1 preparation completed; P0 hostname boundary corrected

- The resumable eight-worker preparation completed all 480 eval contexts.
- Formal Qwen execution submitted four valid first-case requests, then stopped
  before submitting `P0_T_CAL` because its parent Denum template contained a raw
  Kubernetes DNS hostname. The four completed requests remain intact; the
  blocked task made no model call.
- RQ3.1 now deterministically replaces public IP, UUID and Kubernetes DNS
  strings in P0 materializations with case-local typed aliases at both fresh
  materialization and request construction. The triggering case's P0 text and
  two visual requests pass the leakage audit; focused regressions pass.
- The correction is idempotent and request-boundary compatible with all 480
  completed contexts. Preparation does not need to be rerun. Formal inference
  remains stopped pending an explicit resume.

## 2026-09-17 — RQ3.1 SIRCL text capacity repair

- Formal Qwen inference stopped after 1,215 persisted calls when AIOPS-2022
  `INC-32757906019C/SIRCL_TEXT` required 32,885 input tokens plus the frozen
  8,192-token output allowance, 117 tokens beyond the 40,960-token context.
  This was a tokenizer preflight failure, not OOM, model output, or an image
  capacity failure; the model was never called for that unit.
- Added a label-blind whole-row capacity adapter only to overlong native
  SIRCL text. It preserves the task, candidates, all modalities, topology and
  the first MET-Z row per entity, removing deepest native-ranked complete MET-Z
  rows until the qualified payload target is met. Image arms are unchanged.
- The failed request now removes 73 complete MET-Z rows and measures 29,827
  Qwen / 31,829 Gemma input tokens, leaving 2,941 / 939 tokens beyond the
  reserved completion allowance. All 80 previously completed SIRCL requests
  remain byte-identical; the other completed arms do not enter this adapter.
  Thus all 1,215 persisted calls remain reusable, and preparation remains valid.
- A four-worker read-only scan of all 480 prepared contexts found exactly three
  over-cap SIRCL payloads: `INC-D3EAA310B962`, `INC-32757906019C`, and
  `INC-4D6E62700175`. After the same shared reduction, all three fit both local
  processors with the 8,192-token completion allowance; no other arm or stored
  context was changed.
- Focused and full RQ3.1 CPU regression passed: 76 tests. No model server,
  smoke, or formal inference was started during this repair.

## 2026-09-17 — RQ3.1 capacity-case verification and formal resume

- The repaired `INC-32757906019C/SIRCL_TEXT/Qwen3.8` request completed with
  29,827 input and 87 output tokens. Artifact verification passed; the correct
  root ranked second (MRR 0.5, AC@3/5 1.0). The local server was stopped after
  this single verification call.
- Formal execution then resumed through the content-addressed full local
  supervisor. The 480-case context cache was hash-verified and reused; no
  preparation was regenerated. The pre-existing 1,215 completed calls and the
  repaired verification call remain reusable, while the old preflight failure
  is not treated as a completed model outcome.
- Resume process group 2702 is running the Qwen effectiveness phase locally
  with attention disabled. Qwen must complete before the registered Gemma
  phase and later experiment batches begin.

## 2026-09-17 — RQ3.1 user-requested safe pause

- Qwen effectiveness completed all 7,200 registered units with no failures.
- Gemma was paused after 2,971/7,200 units. The runner stopped new submissions,
  drained all eight in-flight requests and writers, and persisted 2,971/2,971
  completed units with no failures before the lifecycle wrapper shut down.
- The full supervisor, model-phase wrapper and local vLLM server are stopped;
  port 8000 is closed and no project compute process remains on the GPU. Resume
  must reuse the completed content-addressed records and continue Gemma only.

- The user subsequently resumed the run. The full local lifecycle supervisor
  restarted with the same contexts and contracts. It first revalidates Qwen's
  7,200 completed content-addressed units without new generation, then resumes
  Gemma from 2,971/7,200 and continues the remaining registered batches.

## 2026-09-17 — RQ3.1 fast atomic resume active

- The bulk restart verifier was removed. Qwen now skips before server startup
  from its model-phase marker; Gemma skips its 2,971 atomic commits before
  loading any corresponding context.
- The lifecycle wrapper now reuses the completed 480-case context index instead
  of re-entering preparation after runner-only source edits. The context loader
  trusts the index's existing self-binding predecessor-acceptance attestation;
  duplicate mutable-source-hash gating was removed while predecessor identities
  and compatibility scope remain pinned.
- Two restart attempts stopped before any new model request while these duplicate
  gates were identified. The successful attempt resumed Gemma, committed new
  units, and reached 99% GPU utilization with no runner error. Qwen responses,
  Gemma's prior 2,971 responses, prompts, evidence, scoring and inference
  settings were unchanged.

## 2026-09-17 — RQ3.1 safe pause during mechanism experiment

- The effectiveness experiment completed both model phases at 7,200/7,200
  logical units per model with no recorded failure, then the queue entered
  `exp_visual_diagnostic_mechanisms` under Qwen.
- On user request, SIGTERM was sent only to the active runner. It stopped new
  submissions, drained six in-flight requests and asynchronous writes, and
  exited with 309/309 submitted calls committed and zero failures. Together
  with 76 registered terminal non-call units, the Qwen logical inventory now
  contains 385/800 resumable units.
- The model-phase wrapper, full lifecycle supervisor and vLLM server exited;
  port 8000 is closed and GPU memory returned to the idle baseline. Resume must
  skip those 385 Qwen units and continue the remaining mechanism matrix before
  starting Gemma or later experiments.

## 2026-09-18 — RQ3.1 final-test lock repair and resume

- All seven pre-test experiment families completed with zero recorded failures,
  but test preparation stopped before reading test contexts or making a model
  call. The lock freezer hashed all 16 actual prompt guides, including the
  screenshot-table mechanism guide, while the validator incorrectly hashed
  only the 15 effectiveness arms.
- The validator now shares the freezer's canonical arm set. The immutable old
  lock is preserved as `method_lock.v1_pre_prompt_set_fix.json`; a successor
  was recomputed before test activity from the same completed eval inventory.
  It retains `X_V_CONTRAST` and the same prompt/config/roster/result/ledger
  digests. Its full audit passed.
- The background queue resumed under process group 114730. It skipped all
  completed eval phases and entered 360-case test preparation with eight
  workers. On completion it will run the locked Qwen and Gemma final-test
  phases sequentially.
# 2026-09-18 — RQ3.1 final-test candidate-identity repair

Final-test preparation failed before any test model call because X interpreted
AIOPS metric endpoint prefixes (`*-grpc`, `*-http`) as new service candidates.
The first failing case had 85 X candidates versus the frozen 74 P0 candidates,
which would also have shifted numeric aliases.  Candidate identity now reuses
the exact shared parent entity universe while X evidence extraction remains
directly based on the complete per-case telemetry.  Registered endpoint
aggregates bind to their owning service and keep the endpoint suffix in the
metric name; unresolved columns are audit-counted and source-hashed.

The real failing case now has 74/74 identical aliases, 4,718/4,718 bound metric
columns and 377,572 direct public facts.  The focused evidence suite passed
29/29, Ruff F/E9 passed and `git diff --check` passed.  No final-test request or
result existed.  The ten predecessor-lock test context payloads are therefore
stale preparation only and will be rebuilt after a successor method freeze;
all 20,600 completed eval/mechanism calls remain untouched.
# 2026-09-19 — RQ3.1 authoritative pod typing repair

The resumed test preparation stopped at 19/360 indexed cases (26 payloads
atomically written) on a SIRCL hosting row.  Public metadata identified
`ts-auth-service-79b77c-89cp5` as a pod, but the legacy 8--10-character
ReplicaSet-name fallback classified its six-character hash as a service and
gave it a three-digit alias.  This was not an OOM or storage failure.

RQ3.1 now gives the public `node_pod_map` authority over node/pod typing and
uses name inference only outside that relation.  A full metadata audit found
8/480 eval and 2/360 test cases with this short-hash condition.  All eight eval
entities were non-root distractors and none appeared in either model's top five
across their 240 effectiveness responses.  Removing all eight cases from the
registered selection calculation still selects `X_V_CONTRAST` (macro MRR
0.446210 versus 0.431028 for `X_MTEXT`).  Existing eval results are retained
with the documented limitation rather than rerun; no test model call exists.
The incomplete test context cache must be rebuilt under the successor lock.

# 2026-09-19 — RQ3.1 selective rerun authorized

The user superseded the initial no-rerun consequence and authorized a bounded
successor rerun.  A frozen repair manifest contains the eight affected eval
identities and two affected test identities.  The active eval repair comprises
240 effectiveness calls and 108 follow-up calls; all old attempts remain
charged.  A repair utility audits the exact 348 active call records, archives
their artifacts and response-reuse pointers, removes only their logical
completion bindings, and leaves every unaffected call intact.  Successor
summaries and method selection must be recomputed before a new test lock and
test preparation are produced.

## 2026-09-20 — RQ3.2 SignalCover implementation and qualification deployment

- Implemented a new RQ-local pipeline under `RQs/RQ3_2/` from the approved
  SignalCover plan. It rebuilds the complete public pool with P0's public
  telemetry boundary, keeps P0/X/SC paths distinct, and registers selection,
  representation, mechanism, and locked-generalization experiments.
- Added eight-worker resumable CPU context preparation, same-fact text/visual
  carriers, evaluator-private mechanism interventions, request-bound local vLLM
  execution, separate call accounting, prompts/renders/conversations/costs, and
  an immutable pre-generalization method lock.
- Static syntax, shell, registration, leakage-source and unit checks passed.
  CPU/processor qualification and four sequential live smokes were deployed as
  a background queue; they remain separate gates and are not formal results.

### Qualification environment correction

The first queue completed its three-case CPU preparation but stopped before any
model call because processor preflight was mistakenly launched from the tools
environment, which intentionally lacks `transformers`. The inference environment
contains the registered processors. Qualification was corrected so pytest and
preparation remain in `venvs/tools`, while processor preflight alone uses
`venvs/infer`. The three completed context artifacts are retained and reused;
the failure changed no evidence, request, renderer, model, or scientific result.

The second qualification attempt correctly used `venvs/infer` but exposed a
second operational omission before any model call: the RQ3.2 shell entrypoints
had not sourced the canonical local environment, so processor preflight resolved
the model relative to the code checkout instead of the separate local resource
root. All RQ3.2 local entrypoints now source `scripts/env_local.sh`; this supplies
the registered local config and Qwen/Gemma model paths without changing prompts,
evidence, weights, sampling, or scoring. Existing contexts remain reusable.

## 2026-09-20 — RQ3.2 qualification provenance repair and v2 passage

Post-smoke inspection found that successful requests had used the correct local
server recipe but their saved envelope named the historical default YAML. The
RQ3.2 wrapper also prewrote an image before the shared transaction wrote the
same bytes under its canonical name, and the queue left a stale PID without a
terminal status. These were audit/persistence defects, not changes to the
model-visible evidence or inference configuration.

The request envelope now records the runtime configuration source, render
persistence has one owner, and the queue atomically records `running` followed
by `complete`/`failed` and cleans its PID. The successor contract is
`research_v2.json`; its scientific matrix is unchanged and its durable call
ledger is shared with v1.

The successor qualification passed 5/5 focused tests, prepared three real
cases, qualified eight CPU requests, and completed all 24 live smoke calls
across four experiments and two models with zero infrastructure errors. Every
completion artifact hash passed. Saved prompts uniformly name
`configs/vllm_inference_local.yaml`; six visual calls have one render each, and
the queue ended cleanly with no live vLLM process.

## 2026-09-20 — RQ3.2 bounded flag-only formal resume

Before formal launch, a direct benchmark showed that reconstructing all ten
selection requests cost about 13.6 seconds per case. Although below the user's
per-case stop threshold, it could waste roughly 1.8 hours near the end of a
480-case model phase. Formal resume therefore uses an append-only mapping from
logical unit to the atomic completion flag. Completed units receive no evidence
selection, rendering, prompt assembly, tokenization, artifact hashing, or model
call during restart. Completed model phases use one phase flag. A synthetic
worst-stage scan of 5,280 flags took 0.068 seconds; the enforced pre-server
limit is 900 seconds.

The same pre-launch matrix check found that the mechanism smoke's single cell
had not exercised RQ3.2's new comparison-bundle re-anonymization or removal
non-applicability. A local typed-key adapter was added without modifying
RQ3.1. Removal conditions with no valid evaluator-private target are now
recorded as zero-call `not_applicable` units. All 14 mechanism dimensions then
constructed or terminated as registered for the three qualification cases;
focused tests passed 7/7.

The user further required failure flags to be terminal. Formal resume now
recognizes four flag states: complete, model failure, infrastructure or
implementation failure, and not applicable. None is automatically retried.
A newly observed infrastructure/implementation failure stops further
submission after in-flight calls drain and leaves the queue failed for review;
its flagged unit remains skipped on any later manually authorized resume.

## 2026-09-20 — Retired preparation, cache, and training-artifact cleanup

After an explicit read-only ownership audit and user confirmation, obsolete
RQ1.1/RQ2.1 preparation payloads, obsolete RQ3/RQ3.1 pools and context caches,
and the abandoned Composer SFT/RL route (checkpoints, adapters, optimizer
states, training runs, and their qualification artifacts) were deleted. The
operation released 148,793,065,472 bytes (about 148.79 GB / 138.58 GiB) of
filesystem capacity and is not recoverable from this worktree without an
external backup.

The cleanup retained 45,955 historical model-visible images in their original
paths (14,813,666,398 logical bytes) wherever the corresponding formal result
did not store another image copy. It also retained all old source code,
scripts, documentation, configurations, findings, Tournament/search inference
records, RQ1.1/RQ2.1/RQ3.1 formal inference results, model weights, and model
runtime caches. RQ3.2's live dependencies were explicitly protected:
`build/local_processed_v3`, RQ3.1's data registration, both formal RQ3.1 parent
context sets, and the complete RQ3.2 results tree. Post-cleanup checks found the
RQ3.2 formal queue still running in `prepare_eval` with 111 contexts committed.

## 2026-09-20 — RQ3.2 300-second request timeout and fail-fast resume

Two Qwen selection requests remained almost entirely stalled for more than 30
minutes while hundreds of later requests completed. Their prompts were within
the successful arm's size range, the server reported no CUDA/OOM/internal-core
failure, and the later `EngineDeadError` followed the wrapper's deliberate
SIGTERM shutdown. The unified local and portable request timeout is therefore
changed from 1,800 to 300 seconds. The RQ3.2 registration records the same
bound. This is operational only and does not alter completed results.

The user retains strict fail-fast behavior and explicitly rejects adding a 5%
final-acceptance rule. Existing complete/model-failure/infrastructure-failure
terminal flags remain authoritative and are skipped by the fast resume path;
new infrastructure failures stop the phase for review and are not retried
automatically. Python compilation, 11 focused RQ3.2 tests, static registration,
and effective-client projection all passed; the client resolved a 300-second
timeout from `configs/vllm_inference_local.yaml`.

The first restart attempt also exposed that the context index had incorrectly
used the entire research registration as its preparation identity.  Therefore
the operational timeout amendment was mistaken for a context-construction
change.  Preparation now has a dedicated hash over only its data source,
roster seed, registration identity, and selector contract.  The legacy index
is accepted only when it exactly matches the immediately preceding
registration with the timeout field removed; selector or data changes still
fail closed.  The existing 480-context index migrated in 0.13 seconds with no
case regeneration.  Focused tests increased to 12 passing cases and the formal
static entry point passed.  The sequential formal queue then resumed at
`exp_signal_selection`; its fast journal/terminal-flag path skips all existing
terminal units and retains strict fail-fast for the next infrastructure error.

## 2026-09-20 — RQ3.2 request-timeout continuation amendment

Repeated isolated 300-second request timeouts stopped otherwise healthy Qwen
selection runs even though vLLM continued returning HTTP 200 responses and no
CUDA, OOM, or engine-core failure preceded shutdown. The user therefore makes
request timeout the sole exception to RQ3.2 fail-fast. New request timeouts are
persisted as distinct terminal `request_timeout` units, are skipped on resume,
are not retried automatically, and do not stop submission of the remaining
matrix. Every non-timeout infrastructure or implementation error continues to
write a terminal failure and stop the phase after active requests drain. The
300-second bound, model inputs, inference recipe, scoring and prior terminal
records are unchanged.

## 2026-09-21 — RQ3.2 host-memory OOM and bounded context cache

The apparent WSL crash during Qwen signal selection was traced to a Linux host
OOM, not to vLLM or an unexplained restart. `/var/log/kern.log` records Python
PID 217567 being killed at 45,106,408 KiB anonymous RSS. RQ3.2's 480 durable
case contexts occupy about 11.35 GiB serialized, while `ContextStore` retained
every expanded object and its runtime representation twins in an unbounded
dictionary. The runner's memory therefore grew with the number of cases until
WSL's available memory and swap were exhausted.

`ContextStore` is replaced by a thread-safe eight-case LRU, with the bound in
the RQ3.2 registration and regression coverage for eviction and reload. This
is an operational object-lifetime repair: it does not alter evidence,
representation, prompt, model, decoding, or scoring. Existing atomic terminal
flags remain valid, and restart skips them without request reconstruction;
only units with no terminal flag are resubmitted. The full diagnosis and
prevention rule are recorded in `docs/issues/RQ3_2_issues.md`.

The first restart then exposed a second recovery-boundary defect: fifteen
unflagged logical units still had `started` rows in the model-call ledger and
were incorrectly converted into RQ3.2 terminal failures. Non-smoke phase start
now marks only exact-scope stale `started` rows as `interrupted`; the shared
ledger permits those spent, unfinished calls to be retried and continues to
count every attempt. The erroneous failure records are preserved and
superseded by append-only retry tombstones. This recovery is a constant-time
SQLite update and performs no historical request or artifact validation.

One concurrently discovered `P0_MORE` pure-text unit exceeded the exact model
context. RQ3.2 now applies the user-authorized context-safe fallback only after
such an exact tokenizer overflow: reverse-ranked complete evidence units are
removed until the request fits, at least one unit per populated region is
retained, and the removed IDs are recorded in the projection. Completed
requests and all visual carriers remain unchanged.

Focused static checks and 17 RQ3.2 execution tests passed. A full 480-context
memory regression peaked at about 2.01 GB, and the resumed formal runner
advanced from 4,645 to 4,655 completed selection units with about 5.2 GB RSS
under 36-way request preparation. The previously overflowing `P0_MORE` unit
also completed through the audited capacity path. The formal queue remains
active and continues only the 102 units that lacked a terminal state at that
checkpoint.

## 2026-09-21 — User-requested safe pause during mechanism evaluation

The formal queue was deliberately terminated at `exp_signal_mechanisms` before
the overnight idle period. At the pause boundary, Qwen had 745 completed calls,
78 registered non-applicable interventions, five request timeouts, no other
terminal failure, and 572 units without a terminal flag. The experiment runner,
queue wrapper, and its local vLLM server were all stopped; no CanvasRCA process
remained. Existing atomic flags and the append-only resume journal are the
resume authority, so a later restart will submit only the 572 unfinished Qwen
mechanism units before proceeding to Gemma and subsequent queued stages.

## 2026-09-22 — Fixed-canvas redundant-noise repair

The resumed mechanism phase stopped on a representation-capacity exception in
`REDUNDANT_NOISE/M_TEXT`. The old intervention could concentrate long log facts
among its first twelve additions. A complete 100-case CPU audit found five such
failures. The successor keeps the fixed canvas and twelve-fact maximum, caps
added log facts at two, and fills remaining positions in the same frozen public
reservoir order. All 100 cases now construct; 99 receive twelve additions and
one receives eleven because its reservoir is exhausted.

The mechanism condition alone receives a new logical identity. Its C-Contrast
and M-Text outputs are re-evaluated under the successor policy: byte-identical
requests reuse content-addressed results, while changed requests receive new
calls. Mismatching predecessor artifacts remain superseded audit evidence.
Every other completed condition remains resumable. Static, CPU and focused
live qualification precede formal continuation.

The gates passed: 19 focused tests and the static registration audit passed;
all 100 formal mechanism cases constructed in M-Text with no capacity error;
and the isolated live smoke completed six of six calls across both models and
three registered datasets inside 600 seconds. All completion hashes matched,
all responses parsed and scored, and the three unique fixed-canvas PNGs were
visually inspected without overlap or clipping. Formal continuation is now
authorized from the atomic resume journal.

The formal queue subsequently resumed at the mechanism stage. Its existence-
only recovery scan took about 0.02 seconds, and it reused only byte-identical
predecessor requests. Both successor representations for the original failing
case `INC-F1CD9B69032E` completed successfully; the queue continued with zero
current terminal implementation failures.

## 2026-09-22 — Evidence-backed next research plan (documentation only)

Reviewed the RQ1.1/RQ2.1 findings, Tournament, RQ3.1 and RQ3.2 reports,
relevant implementation paths, stored examples, and primary related work.
The new proposal is recorded in
[`CanvasRCA_Next_Research_Plan_2026-09-22.md`](../docs/CanvasRCA_Next_Research_Plan_2026-09-22.md).

The proposed RQ3.3 direction preserves the complete TPV backbone and appends
bounded, source-grounded scope/path/liveness witnesses. It replaces future
large-scale SC/layout exploration with semantic calibration and a small,
fixed-cohort development comparison against genuine P0 expansion. Selective
topology vision is compared with a strong same-fact text twin; one-call
deployment remains primary, with a conditional two-call diagnostic only.

The rationale is that SC improved some telemetry coverage but still deleted
valuable prior evidence and did not beat the strong baselines; several
implemented ablations also differed from their intended meaning. These
observations do not retrospectively reclassify historical results. The old
360-case test is explicitly exposed regression data, not fresh confirmation.

The proposed maximum scheduled work is 19,710 calls, including five bounded
smokes, within the existing 40,000-call new-RQ ceiling. Expansion is conditional
on development evidence, not automatically authorized by this document.
Only this plan and the brief decision log were written. No experiment code,
configuration, scorer, result status or running process was changed; no model
call, preparation, training or multi-agent task was started.

## 2026-09-23 — Next-plan v2: separate observation, computation and presentation

Status: proposed protocol, documentation only. Updated the existing
[`next research plan`](../docs/CanvasRCA_Next_Research_Plan_2026-09-22.md)
after reviewing the RQ1.1/RQ2.1, Tournament, RQ3.1 and RQ3.2 evidence again
and consulting published Nezha (FSE), MicroRank (WWW), CIRCA (KDD), Groot
(ASE), PAL (ICML) and Lost in the Middle (TACL). Reading scope, venue/track,
source links and applicability limits are recorded in the plan.

The late Tournament registry already includes residual, window, composition
and graph selectors, but their new scores/coefficients remain CPU-only and
their input is an analyzer-derived pool. The revision therefore does not
rename those algorithms as new ideas. It prioritizes explicit measurement
semantics, deterministic computations with visible operands, and qualified
request-level joint observations. It also tests appendix position because
preserving old facts does not guarantee freedom from context interference.

This supersedes only the previous proposed development matrix: an eight-arm
60-case paired screen and optional two-arm budget check select one global
configuration, then five conditions on a disjoint-group 120-case cohort
check it without reselection. A three-condition event-ledger/image mechanism
study is conditional, not an automatic replacement of the main renderer.
The worst-case schedule is now 20,430 calls (formerly 19,710); the 40,000
hard ceiling is unchanged. No retrospective result reclassification.

No experiment implementation, model recipe, scorer, results, process or data
partition was changed; no preparation, CPU experiment, model call, training
or subagent was started. Next action requires separate implementation
authorization, beginning with public-field feasibility rather than full runs.

## 2026-09-23 — RQ3.3 Witness implementation; static-only stop

Implemented the next-research plan under `RQs/RQ3_3/`: five functional modules,
versioned registration/measurement semantics, three descriptions, five not-run
findings, and opt-in CPU/smoke entry points. New public-source witnesses preserve
the TPV backbone; SEM/EXEC share observations, COHORT requires source-linked
requests, and expanded budgets preserve the small-budget prefix. Parent-native
P0_MORE, strong text/G controls, actual interventions, method locks, paired
statistics, durable call accounting and flag-only resume are implemented.

Refined the plan to v3. A new same-renderer G scene control separates redrawing
from node rearrangement (+240 planned calls: 20,670 total; 40,000 hard cap
unchanged). FRONT preserves the original candidate location. Status-available
but undersized request cohorts cannot silently change to latency cohorts.
Original baselines and all historical experiment artifacts remain unchanged.

AST, static project-import symbol checks, Ruff E9/F, JSON/budget/structure checks
and shell syntax checks passed. The implementation review and runtime boundaries
are recorded in `docs/issues/RQ3_3_implementation_review_2026-09-23.md`.
No project module/test was executed, no data registration or preparation was
run, and no CPU regression, smoke, GPU/model call, training or subagent started.
Source calibration manifests and real-input/visual/runtime qualifications remain
future evidence requirements, not claimed successes. Stop here as requested.

## 2026-09-23 — Witness v2: information-inspired controls, static-only stop

Updated the next plan to v4 and RQ3.3's protocol/config/code to `rq33_witness_v2`.
The five experiments and six deployment candidates stay fixed. Added a
same-request marginal control, RAW evidence-pair factorial, identical-caption
local/remote binding controls and a 1024/2048/4096 nested-budget comparison.
Planned calls are 23,190 (+2,520); the hard limit remains 40,000. Mechanism
controls cannot win deployment selection. Full v2 rationale, source links,
applicability and interpretation limits are in the plan and RQ description.

Static review corrected pooled-median computation, explicit cohort group labels,
PAIR removal closure/common backgrounds, budget-specific analysis identities and
actual-input intervention metadata. Report utility interactions and empirical
cost curves, not estimated mutual information/PID or Shannon rate–distortion.
New CPU regression definitions are written but not run. AST/import-symbol,
Ruff, shell, JSON/matrix and documentation-link checks passed; see the RQ3.3
implementation review. No parent renderer, model recipe, scorer, partition or
historical result changed. No registration, preparation, CPU regression, smoke,
GPU/model call, training or subagent started. Await user authorization to test.

## 2026-09-23 — Witness v2 CPU/GPU qualification and smoke repairs

Subsequent user authorization covered CPU/GPU smoke and defect repairs, not
formal experiments. Replaced fragmented full-message log candidates with
source-indexed template/phase summaries; removed repeated serialization,
tokenization and quadratic Denum selection. The latest three-case CPU run
passed in 109.59 seconds: 32 unit checks; 86 executable real conditions and
25 explicitly inapplicable conditions. Per-case earlier post-optimization
preparation was 89.01/44.70/9.73 seconds (AIOPS-2022/AegisLab/AIOPS-2025), not
full RCA latency or dataset-wide estimates.

Live smoke exposed unauthenticated readiness probes, false success on interrupt,
an unresolved local scorer path, and G graph/ledger height-allocation failure.
Fixed all four; added three focused non-network regression tests. Completed
the missing SC calibration audit by matching 120 historical requests to public
context projections and binding estimator-specific guide edits. No numerical
source correction is certified; SOURCE_FIXED therefore aliases GUIDE_FIXED.
Old evidence, results, model recipes and scoring semantics remain unchanged.

All five logical smokes completed under 18 calls/600 seconds apiece: 90 units,
86 actual calls, 234–247 seconds each. Inputs, raw outputs, full conversations,
cost and completion hashes checked; all 86 responses ended with `stop` and were
scored. Opened actual G re-layout images; retained model reasoning/identity
mistakes as outcomes, not retried failures. EVENT remains unqualified on these
samples; no claim that every optional arm is live-covered. Earlier attempts
(0+9+44 calls) remain separate; cumulative initiated calls are 139. Services
exited after testing. No formal experiment, attention collection or training.
Details: `docs/issues/RQ3_3_implementation_review_2026-09-23.md`; artifact review:
`RQs/RQ3_3/results/witness_v2/smokes/review_2026-09-23.md`.

## 2026-09-26 — All-report gain/harm review and proposed RQ3.6

Read the RQ1.1/RQ2.1, Tournament and RQ3.1–3.5 reports. User requests equal
attention to improvements and degradations, including worthwhile nonsignificant
trends. Added a reproducible offline review of 17,502 paired comparison records
(not independent cases), 3,311 subgroup rows, event-group sensitivity, complete
cohorts and source hashes. Holm families are report-stage × subgroup axis across
listed comparisons/models; n<10 remains descriptive. Gold-root type derives from
the registered numeric-ID contract and matches the newer private-label audits;
historical mixed-type metadata is not blindly propagated. No scores changed.

Exploratory Qwen RQ3.4 G-versus-text effect on AIOPS-2025: +0.1795 MRR, 39 cases,
11 Top-1 repairs/0 breaks, Holm p=.0457, same event-group sensitivity. This does
not establish a dataset interaction or independent replication across rounds.
RQ3.5's registered Gemma instruction harm and loss of lower-rank hits motivate
separating semantic guidance from verification wording; subgroup harm and small
positive trends remain explicit rather than being filtered by headline p-values.

Decision: prioritize A check replication, then qualified dynamic W/peer component
ablations with fixed G/text twins, then bounded composition and locked evaluation.
Do not automatically expand low-coverage J or add K assertions to model input.
Plan: `docs/experiment_plans/CanvasRCA_RQ3_6_Research_Plan_2026-09-26.md`.
Full conditional workload 19,272 calls before necessary repairs; this is not a
new budget authorization or a reset of the parent 40,000-call allowance.
No inference, training, preparation, runtime/scorer changes or new subagents.
Existing source/results preserved; report/plan indexes updated. Implementation
and new experiment execution remain future work.

## 2026-09-23 — RQ3.3 formal queue launch authorization

User authorizes the full sequential queue and requests no continued agent
monitoring after startup. Added an explicit RQ-local queue wrapper, preserving
all frozen inference/evidence source hashes. Four lightweight scheduler tests
pass: positive path, negative screen/check routing, and done/fail flag-only
resume without preparation or model launch. Existing evidence-backed manual
review and all five smoke reports registered as passed qualifications.

Queue prepares screen60 with eight core-pinned workers (three contexts already
committed), then calibration and screen, Qwen before Gemma per stage. The
registered budget/check decisions control later eval/mechanism/test expansion;
negative development leads only to the bounded registered diagnostic. EVENT
and fresh remain unavailable rather than silently enabled. Historical 53 model
attempts are counted once alongside 86 current smoke calls in the hard budget,
without treating those old responses as reusable results. Resume trusts small
terminal flags; no bulk artifact rehash or completed-request reconstruction.
SIGTERM drains the active runner and releases only queue-owned services.

Operational authority: `RQs/RQ3_3/results/witness_v2/formal_queue_status.json`.
Logs: `RQs/RQ3_3/results/witness_v2/logs/formal_queue/`. No scientific result or
MRR claim is implied by launching the queue.

## 2026-09-25 — RQ3.5 implementation and bounded qualification

Implemented independent RQ3.5 evidence×instruction, outcome-linked joint-count,
G/J representation and locked replication/generalization paths. Reuses RQ3.4
public contexts and persistence infrastructure; new indices read whitelisted
per-case fields without gold or raw-log expansion. Runtime/scorer remain
unchanged, attention disabled, one Solver call and at most one image.

Static checks and 13 CPU unit tests pass; three real cases compile all 20 arms
for both model processors (120 units). Final cached CPU regression: 21.37 s;
cold case preparation 14.61–19.86 s, new indices 5.63–10.94 s. Early binder-hash
and SIRCL-part-boundary bugs were caught and fixed before GPU. Composite G
uses parent-registered crops in fixed slots; native B is unchanged. Audit-only
joint evidence is restricted to facts actually visible in the corresponding
input. Pre-inference revisions retained rather than silently overwritten.

Four original GPU smokes completed 72/72 logical units in 263.51/227.00/235.72/
252.85 seconds, using 18/14/16/18 actual calls (66 total, cumulative 6,933).
Input/output/conversation persistence and sampled real PNGs were reviewed.
Post-smoke review found duplicate candidate records in A's two common P0
conditions. Removed the duplicate while preserving the common candidate list;
CPU proof shows 12 changed inputs and 108 unchanged. Native controls and B/C/D
retain their input contracts. A second review-only fix prevents old smoke
records from qualifying changed inputs; another 120-request CPU comparison
shows no further changes, all 13 unit tests pass, final CPU run 21.20 seconds.
B/C/D remain qualified. A requires six targeted calls; a one-time exception
to its exhausted original cap has been requested but not presumed authorized.
All original artifacts are preserved. Owned GPU services have exited. No
formal execution or expansion has been started. Artifact authority:
`RQs/RQ3_5/results/outcome_linked_v1/qualification/`;
implementation/issue record: `docs/issues/RQ3_5_qualification_2026-09-25.md`.

## 2026-09-23 — RQ3.3 calibration-to-screen timeout repair

Calibration completed 480 logical units (478 done, 2 request timeouts), but the
old next-stage check treated every fail as blocking. Aligned stage admission
and subsequent decision pairing with the existing timeout-continue policy;
other infrastructure errors still stop. No automatic retry or 5% gate. Common
decision cohorts and exclusion IDs are explicit, including all budget levels;
science thresholds and model inputs unchanged. 65 tests and static checks pass;
15.00-second targeted CPU audit preserves all 90 smoke input identities and
480 calibration flags. Actual tiny-flag stage check: 0.023 seconds. No new GPU
qualification calls or preparation rebuild. Full repair record:
`RQs/RQ3_3/results/witness_v2/logs/stage_timeout_repair_20260923.md`.

## 2026-09-27 — RQ3.6 B implementation and qualification; stop before formal

User authorized B plan/code/static/CPU/GPU qualification only. Preserved A
inputs/results/config/report and snapshotted its predecessor source. Added
five controls to the original nine: G order, relational text, its screenshot,
and matched typed scope text/graph. Qualified witnesses filter static/clock
anchors and incompatible peers; unrelated static companions cannot sneak in
through a dynamic host. Same-field unchanged peers remain valid controls.
No labels or response outcomes select inputs; no training or attention.

CPU caught graph/ledger overflow before inference. Registered one fixed
2304×3072 geometry with1100px graph height, unchanged20px font, no omitted
facts. Completed three-focus static review,10unit tests,84real CPU request
builds in18.351s. One logical GPU smoke completed18/18 in276.903s, both models,
without timeout/infra/parse failure. Conversations include all input text;
12saved PNGs match qualified bytes. Read all responses: unsupported causal
edges/type confusions remain model errors, not grounds to tune this smoke.

Optional deep_gemm import and Triton JIT warnings preserved; frozen serving
recipe unchanged. Total calls10917=10899prior+18smoke; newformal0. Owned
services exited. No B formal authorization, no C/D launch. Full audit:
`docs/issues/RQ3_6_stage_B_qualification_2026-09-27.md`.

## 2026-09-27 — RQ3.6 B formal launch

User separately authorized full B and no assistant monitoring after startup.
Current qualified source unchanged; authorization/flags check0.064s,245GiB
free, cumulative10917 calls before launch. Detached sequential Qwen→Gemma
queue PID4396 started14:17:54UTC; first owned server4430 loading. Scope only
180exposed cases×14arms×2models,5040 maximum newcalls; no C/D. Run-local
shell transcript/atomic status/logs in `RQs/RQ3_6/results/visual_mechanisms_v1/`.
Tiny terminal flags drive resume; no old request rebuilding. No new MRR claim.

## 2026-09-28 — Future Dashboard design: chart-first, on-call-oriented

After inspecting a real RQ3.7 LOCAL_LINK image, the user identified excessive
text and requested more attractive, realistic on-call dashboards in subsequent
iterations. Adopt chart/relationship-first presentation with concise necessary
labels, clear visual hierarchy and appropriate density; do not use long text
ledgers or experimental empty slots as the default deployment interface.
Preserve diagnostic evidence and separate selection changes from representation
changes. Appearance is not evidence of higher MRR or engineer efficiency.

Recorded the future-only direction in section 12 of
`docs/experiment_plans/CanvasRCA_RQ3_7_Research_Plan.md`. Current stage C inputs,
renderer, configuration, running processes and historical results are unchanged.
Documentation only; no tests, model calls or new experiments started.

## 2026-09-28 — Unified renderer prototype authorized (isolated)

User requested a configurable Python + React/HTML/CSS/TypeScript renderer while
RQ3.7 C continues. Initially proposed `RQs/RendererLab/`; the user then explicitly
requested `src/renderer/` instead. All renderer code, web assets, configs and
scripts now belong in that directory (authorized organization exception).
Evidence DTO, layout tree and cyclic system graph are separate. No mutation of
running experiment inputs, shared inference recipe, older renderers or results.
Decision and qualification scope: `docs/experiment_plans/CanvasRCA_Unified_Renderer_Prototype.md`.
This is a renderer prototype, not a new scientific efficacy experiment or globally
promoted pipeline. Runtime and artifact validation will be recorded on completion.

User further specified an explicit component library (one file per dashboard
component) and global operation library (spacing, relationships, resolution,
layout, indexing). New interfaces rename “silhouette” to “dashboard component”.
Component type numbers and stable instance indices are distinct; moving a panel
does not renumber it. Historical reports/configs retain their original terminology.

Completed independent implementation: 10 component files, 9 operation files,
strict public DTO, explicit layout tree, React/SVG/CSS, offline HTML + PNG exporter,
visible-field and geometry audits. Python AST/shell/TypeScript checks passed;
19 CPU/browser tests passed (6.86s), including intentional rejection paths.
Five final real-development previews passed (0.668–0.768s/export) in
`build/renderer_previews/v1/`; visual inspection covered lines, bars, heatmap,
graph/matrix and light/dark variants. Scope and adapter coverage exclusions are
recorded in `src/renderer/QUALIFICATION.md`; prototype is not whole-parent-input
equivalence or an efficacy result. No LLM/GPU inference, no attention, no old
renderer/source/config edits, and no change to the running RQ3.7 experiment.

## 2026-09-29 — Unified renderer: topology must bypass diagnostic filters

User requires complete observed relationships, connected nodes only, observable
database/external dependencies, and richer RQ1.1-like onset information. They
correctly identified that a graph built from filtered Trace summaries may omit
real connections. Replaced the prototype's filtered ALL_ID relationship source
with targeted canonical public per-case graph/metadata + full Trace identity-column
reads; M/R/L selection and all historical experiments remain untouched.

Important source finding: AegisLab's canonical graph mixes 58 call edges and 49
hosting edges in the audited development example (`sircl_data/aegislab.py` explicitly
adds both). Classify these separately in new code, not all as calls. AIOPS-2022
example has 121 observed calls vs 9 old packet rows; AegisLab has 58 vs 4. AIOPS-2025
example has no Trace rows or observed edges; do not invent connections from names.

New `topology.py`: trace-scoped parent binding, ambiguity audit, explicit client-peer
endpoints, preserved numeric aliases, dependency roles and independent six-digit
external namespace without changing candidates. New C11 `events.onset`: existing
relative time/z/source readings, no reverse causal arrows or fabricated persistence.
O10 `graph_visibility` hides only full-graph isolates; evidence cards remain. This
supersedes the prototype v1 isolate-display default, not historical results.

Static checks and 25 CPU/browser regressions passed (8.21 s); three development
examples plus network/matrix galleries rendered and visually inspected. Export
0.020–1.976 s, browser rendering 0.718–0.819 s in these individual measurements.
Final artifacts: `build/renderer_previews/full_topology_final/`; qualification and
limitations: `src/renderer/QUALIFICATION.md`. Graph completeness means observed
per-case data only; onset coverage remains the existing public P0 rows. Dense graphs
remain a readability concern, not a reason to silently drop edges. No LLM calls,
GPU use, historical renderer edits or intervention in the running experiment.

## 2026-09-29 — Pairwise relationship dashboard component

User requests a cleaner per-edge alternative while retaining the overall network.
Added `graph.edge_pairs` (C12): every original edge receives one independent
source→target tile, typed relation and unchanged numeric endpoint IDs. Cycles,
reverse edges, self-loops and typed parallel edges remain; repeated endpoints are
audited as references to the same node, not additional facts. Existing node-link
and matrix components remain available. Explicit capacity check rejects overflow,
never truncates or silently shrinks. `pairs` preset allocates space by edge count;
controlled comparisons must separately freeze sufficient common geometry.

Static checks and 28 CPU/browser regressions passed (11.39 s). Fixed an operation
audit KeyError risk for component-specific derived rectangle keys. Rendered three
existing development DTOs, plus a matched 58-edge network/pairs pair with identical
facts, canvas and outer geometry. Actual pair PNG inspected under dashboard skill.
Artifacts: `build/renderer_previews/edge_pairs_v1/`; checks/usage in renderer README
and QUALIFICATION. No RCA calls, inference changes, active-experiment modification
or claim that pairwise topology improves MRR. Its lower edge-crossing burden trades
off against repeated IDs and cross-tile multi-hop integration.

## 2026-09-29 — Deployment brace groups and service/pod correspondence

Implemented the user's node→{pods} and service→{pods} request as independent C13
`graph.deployment_groups` under `src/renderer/`; existing network/matrix/pairs remain.
Default prototype deployment cards use braces; call diagrams keep their chosen
encoding. Exact membership edges and repeated pod identities are audited, with
capacity failures rather than member truncation. Service instances are extracted
from full public per-case Trace resource attributes with compatible existing
aliases; explicit metadata preserved, ambiguous namespaces rejected, no name-based
inference. `has_instance` is not a Kubernetes ownerReference or invocation claim.
Decision registered in the unified-renderer prototype plan.

Static checks and 33 CPU/browser regressions passed (15.30 s); three development
dashboards and deployment-only galleries rendered. Actual AegisLab group PNG
inspected: 49 hosting and 30 service-instance edges; those 30 groups each have one
pod, while 19 other hosted pods lack observed service bindings. This is sample
coverage, not a dataset-wide cardinality assertion. Tests cover one-to-many and
shared-pod associations. Artifacts and limits in renderer QUALIFICATION.md and
`build/renderer_previews/deployment_groups_v1/`. No GPU/LLM calls, historical edits,
experiment restarts or active-scientific-input changes.

## 2026-09-29 — GitHub synchronization ignore audit

Expanded `.gitignore` for preparation/cache workspaces, model checkpoints,
renderer outputs, local credential filenames (including `secert.md`), and bulky
case-level report attachments. Reports, figures, aggregate tables, source and
configuration remain eligible for Git. Local artifacts were not deleted.
All 16 representative ignore checks passed; `git ls-files -ci --exclude-standard`
found no tracked files matching ignore rules. Remaining visible untracked files
have no individual file above 5 MiB. `git add --dry-run --all` passed; no actual
staging, commit, push, history rewrite or experiment intervention was performed.
Previously committed data remains in Git history; ignore rules do not erase it.
