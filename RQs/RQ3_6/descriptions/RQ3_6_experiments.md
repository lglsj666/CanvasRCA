# RQ3.6 执行协议

## 当前执行版本：历史核对后的机制分解（2026-09-27）

**资格前最终减项**：完整180例CPU检查发现异宿主同owner同字段peer为0/180，因此删除HP_CROSSHOST T/G，不把全批空干预送GPU。B2现在五策略×T/G=10条件、3600单元；B1/B3各4320，总12240，含54smoke及历史10917最坏23211。B2 primary family删除该修复后为16项，CPU三例总请求为72+60+72=204。下文出现的跨宿主条件、12960/23931与216均为此次减项前注册历史，被本段显式取代。原预检证据保存在scope_competition的preinference_revisions/capacity_before_empty_arm_removal.json；减项未使用模型成绩或新标签，已生成推理0次。

用户在第二次历史审计后授权继续实现、测试，通过后全量启动。本节取代下方旧B的14条件队列及三个草案的不可执行状态。旧B正式0次、18次资格保留；A及全部旧研究结果不变。历史去重依据见 `docs/issues/RQ3_6_historical_question_audit_2026-09-27.md`，不把旧SEARCH、R16、P×H×K的发现称为新贡献。

### B1：exp_graph_diagnostic_components

六内容条件FULL、NO_RANK、NO_SEVERITY、NO_ONSET、STRUCTURE、NO_CALLS，各T/G：12条件。固定原P0 M/R/L、公共任务、候选和统计。仅操纵G的显式组成：rank、severity_z_display、onset_rel_min_display；STRUCTURE还去掉派生evidence_source_display；NO_CALLS只去具体调用边。公共源索引不显示；所有条件数字ID排序，节点大小/颜色不编码被消融的数值。保留共同实体节点名单，调用边移除后不顺带删掉孤立实体。时间/异常信息仍可能由M/R/L推断，结论仅关于G内显式提示，不称全输入无时间/严重度。

同一新的G字段明细投影用于T和G；G为真实typed有向图+完整可见明细，不是截图。整体STRUCTURE与FULL是独立组件消融的共同锚点，不再把旧SEARCH24的整体摘要删除作为新发现。新的关键比较是三个字段各自、调用边及其承载交互。FULL_T/G也只作这套投影内部校准，不重复宣称一般图优于文。

### B2：exp_scope_competition

ANCHOR、HOST、PEER、HOST_PEER、HP_DEDUP、HP_CROSSHOST，各T/G：12条件。先从完整已有公开observation池选择动态pod观测，优先不同pod，再按已冻结公开front/变化/support/source_key排序，最多四锚点；须有唯一公开宿主。没有合格pod则保留原资格包的单侧锚点并标记scope不适用，不伪造peer。

HOST选公开宿主自身的最优合格动态观测；PEER选同host、同字段/单位/role/两个窗口的其他实例，允许真实不变；CROSSHOST仅选择异host且同owner service的匹配peer，无合格对象时保留原peer并标记空干预。HOST_PEER为2×2第四格。HP_DEDUP仅移除追加正文中完全相同的观测/关系JSON重复，不删除唯一事实；研究冗余重复而不是宿主证据总剂量。跨包关系固定为共同superset，开关只改变观测。全部条件使用最坏superset的共同2048-token锚点名册，一次性从尾部减锚点到两tokenizer均合法，包含相对时钟指南；不按arm重新选锚点。HOST/PEER不存在时保留自然空干预与完整分母。

T/G仍采用原T/TPV的G承载，追加观测都为文本。这里测的是补充证据与基础G承载的交互，**不是声称新增宿主观测也被画入图像**。没有无补充TPV新arm，也不重跑旧H包开关。主问题是host和peer的独立/交互作用，以及精确去重和跨宿主peer能否减少pod→node错误同时保留node修复。

### B3：exp_relation_provenance_binding

关系ALL、CALL、DEPLOY × ID/BIND × T/G：12条件。固定资格化观测、数值、统计和追加预算。CALL只保留显式calls/request_parent；DEPLOY只保留hosts/owns并去掉原G调用边；ALL二者都保留。不是把调用边当传播边，或把同宿主视为因果关系。原M/R/L仍可能暗示关联，干预只控制显式关系字段。

ID将观测绑定放在独立明细段，G节点只有数字ID；BIND将相同绑定行邻接到首次出现该实体的关系行，G节点同时标注观测semantic/region/unit。T获得相同绑定事实和邻接组织，不额外补新关系/值。BIND是明确的冗余标注与局部组织联合干预，不声称完全隔离了重复文字、空间邻近或颜色单因素。报告真实文本行顺序/像素/完整请求变化；自然相同复用模型输出，不能因arm名不同多次调用。

### 公共容量、队列和统计

三实验各screen60+check120，共180暴露例（三主数据集各60），两模型。每实验12×180×2=4320逻辑单元；正式总12960。每实验一个18-call/600秒smoke，三次共54上限。继承累计10917次，全部完成最坏总23931，小于40000；三个结果目录用同一SQLite预算库而非复制旧计数。相同请求复用会降低实际新调用，不新增其他arms填额度。

新图宽2304、基础高3072、20px字体、26px行距。每个case根据该实验所有条件的公开完整节点标签/明细，取共同最坏尺寸：图区域至少1100，整体至多8192高。所有新图条件同case同像素尺寸；不按成绩/模型选尺寸，不删事实或缩字号。实际图像tokens分别记录。父版G图原字节不动；跨父版和新图不作纯布局归因。CPU对全部180例、全部条件、两模型token上限做容量预检，以免三例smoke遗漏密图/长字段。

三个独立静态focus：科学干预/历史重叠；运维/共享预算/flags；泄漏/语法。每实验CPU三例全条件：**3×12×2=72请求，共216请求**；另全180例容量检查不调用模型。最多八独立物理核心，按source/cloudbed交错，资格及容量每项1800秒上限。保存真实prompt/PNG及私有label扰动测试。

每实验smoke从screen hash选三主数据集各一例，三个代表条件×两个模型；Qwen→Gemma，启动切换/持久化同一600秒。超时单独记录未完成覆盖，非timeout错误不得通过。检查全部已完成conversation、response和图片后方可授权formal。稳定后用户不要求长期监控；启动实际推理后观察五分钟再交还。

正式严格B1 Qwen→Gemma→B2 Qwen→Gemma→B3 Qwen→Gemma。不混模型/实验，不改模型配方/8192输出/评分/候选，不记录attention、不训练。认证models探测与请求共用Bearer凭据，401/403立即报错，只有拒绝连接/503作为加载中。记录服务ready与runner已提交请求为不同状态。resume仅小flags和阶段状态，done/timeout fail跳过，非timeout基础设施失败停止，未commit单元重来；不重建已完成请求。

统计单位case，MRR主终点；模型分开、数据集/粒度/fault分层，repair/break及pod→node错误都报告。B1每模型五个消融−FULL×两承载，共20个为primary Holm family；五个承载差值交互×两模型为secondary10项。B2 2×2host效应、peer效应、交互和两修复−HOST_PEER×两承载×两模型共20项primary family；粒度差值交互单列探索性。B3每模型CALL/DEPLOY−ALL×绑定×承载共16项primary family；六个BIND−ID×两模型共12项secondary；关系×绑定×承载条件效应如实描述。Pratt-Wilcoxon、paired dz、Holm，不报告CI。screen/check分别给表及180整体描述，不称新test。禁止用未显著等同无效或从子组成绩事后路由。

## 当前状态：第二次历史去重审计（2026-09-27）

取代下方旧B自动启动状态：旧B已暂停、正式0调用、18次资格保留。用户要求重新核对三个新问题后，发现旧RQ3 SEARCH24/31已消融时间摘要/z标签，SEARCH13已添加hosting，Tournament R16已做typed实体绑定，RQ3.4已做P×H×K及T/G×关系提示。完整[历史核对](../../../docs/issues/RQ3_6_historical_question_audit_2026-09-27.md)已落盘。宽泛问题不再视为全新；待实现方案需只保留尚未分离的组成/交互及明确修复措施。此前12960单元是初拟规模，三个v2配置明确标为不可执行草案，未运行CPU/smoke/正式。最终调用数须在去重后的具体设计冻结时重新核算；累计40000不重置。

## 阶段 B 后继协议（2026-09-27，A 历史协议保留在后）

2026-09-27 最新执行授权：用户已授权启动完整 B，并要求启动确认后停止助手监控。仅解除下文资格后暂停，不改科学配置或测试合同。按 Qwen→Gemma 运行全部180例×14条件（最多5040新增正式调用），不进入C/D。运行记录入口为 `../results/visual_mechanisms_v1/launch_B_exposed180.sh`，只读取小型flags续跑。授权时累计10917次，磁盘245GiB；当前源码/资格与5040目标检查0.064秒，无旧请求重建。

唯一配置 [visual_mechanisms_v1.json](../configs/visual_mechanisms_v1.json)，入口 `bash RQs/RQ3_6/scripts/stage_b.sh {register|cpu|smoke|review|run}`。本次只授权实现与资格，**无正式授权文件，不启动全量，不推进 C/D**。现有 A 的完整输入、输出、配置、分数和报告不动；扩展共享五模块前的 A 源码快照保存在 B 结果目录 `predecessor_source_A/`。现有 A 资格绑定历史源码，不用 B 新合同去重新解释 A 的有效性。

十四条件：`B0_T/B0_G/B0_ORDER_T/B0_REL_T/B0_REL_S/W_OLD_T/W_OLD_G/W_QUAL_T/W_QUAL_G/W_Q_NO_PEER_T/W_Q_NO_PEER_G/MORE/W_SCOPE_T/W_SCOPE_G`。

- B0_T/G、W_OLD_T/G、MORE 继承原内容和相应 G 承载，继续 A 的源单位名适配，不重算数值。
- ORDER_T 仅按数字实体、字段、固定 hash 排 G；REL_T 同序并增加实体分组；REL_S 对 REL_T 的完整 G 正文截图。所有显式 rank、onset、severity、实际边均保留。
- W_QUAL 在同一个完整公共 observation/witness 池上应用资格筛选。锚点采用原 `comparison_axes`，至少两个源观测，至少一个有限非零变化；这不是统计显著异常或根因概率。配置/request/limit、capacity 和时钟类字段不单独作为锚点。正反变化都允许。缺值不补零。
- 同字段 peer 要求相同 region=M、semantic、unit、role、reference/current 窗口及显式共同 hosts/owns。宿主自身观测可以单位不同，但归为关联观测，不称为可直接相减的 peer。非同字段关联观测也须通过动态变化资格，不能通过动态宿主顺带纳入任意静态limit/启动时钟；同字段peer则允许不变。无 peer 保留单侧锚点。最多一锚点加两个关联/peer 观测，每例最多四包、两 tokenizer 均不超过 2048 tokens。
- 沿用旧 P1H1 的 active/重复/新语义/新实体/front/持续/support/hash 字典序及两个宿主包优先保留。不改公共分数。观察与基础 P0 同实体同字段的重合单列；只有重复自身且无新关系/对照的单例包拒绝。peer 消融只删除已选 peer 及专属关系，不重新选择、不补满。无合格包不追加内容。
- W_SCOPE_T/G 选择与 W_QUAL 完全一致。新增绑定描述只重述已选实体、观测字段和已有关系，不查询额外元数据。图分 node/pod/service 三列，真实绘制有向 calls/hosts/owns、孤立实体、自环、反向边，观测语义贴在所属实体框中；数值继续在共同文本。完整 G/绑定明细在图下两个连续列可见，不能仅藏在 manifest。文本提供相同字段。两者是绑定表达对照，不是全视觉。
- 新图/截图固定 2304×3072、20px 字体、26px 行距、图上部1100px；原图字节不动。CPU发现原900px图区及2304px总高不足，模型调用前统一修改尺寸以完整显示标签/明细；字号/事实不变。图像大小的差异及实际 processor tokens 均记录，不把跨旧图比较称为纯布局效应。不能缩小字号、静默删字段或改排序绕过溢出。

正式（以后获授权时）使用冻结 screen60+check120 的三个主数据集各60例，共180例、两模型、最多5040 calls；是 repeated-exposed，不是新 test。总40000继续继承 A 的10899次调用，smoke/失败都计入，不是API计费。资格用 screen 内 hash 冻结的三个病例，每数据集一例，不用 test/unused。

静态检查分科学对照、运维恢复/预算、泄漏/语法三个 focus。CPU 限1800秒，三个不同物理核心，覆盖3×14×2=84个真实请求构建及全部新增边界测试。检查父版字节身份、M/R/L和候选未变、G事实库存、peer移除、同事实T/G、模型间相同输入、PNG可见绑定、标签扰动、token容量和done/fail快速续跑。

一个逻辑 GPU smoke：三例×`W_QUAL_T/B0_REL_S/W_SCOPE_G`×两模型，最多18次、600秒总窗口，包括服务启动切换、写盘和review。模型顺序运行，服务归属隔离；不扩窗、不自动补验。timeout-only按规则记录实际覆盖，不能冒充18个都完成；非timeout错误不通过。每份完整输入、raw/partial、conversation、PNG、accounting人工抽查；不以答案正确率筛资格。旧G路径仅声明CPU与既有资格，不冒充本轮live覆盖。

分析 family：G四个主对照×两模型=8项；W_QUAL_G对B0_G/W_OLD_G/MORE/W_QUAL_T×两模型=8项；Scope_G−Scope_T、Scope_T−W_QUAL_T、Scope_G−W_QUAL_G×两模型=6项secondary；去peer/换序各独立secondary。Pratt-Wilcoxon、paired dz、Holm；按数据集、真实granularity及公开可观测性分层，检验差值交互，修复和破坏同时报。子组发现不改变部署路由。

## 阶段 A 历史执行协议

配置：[replication_v1.json](../configs/replication_v1.json)。执行入口 `bash RQs/RQ3_6/scripts/entry.sh {cpu|smoke|review|run}`。2026-09-26资格通过后，用户另行授权启动阶段A正式check120；这取代之前的资格后暂停边界，不授权B–D。运行命令记录及顺序队列位于 `../results/replication_v1/launch_A_check120.sh`，不改已资格化的科学源码、配置和输入。

## 条件与数据

`exp_evidence_instruction_replication` 共11条件：E_P_D_P、E_P_D_S、E_S_D_P、E_S_D_S、E_S_G_P_V_S、E_S_G_S_V_P、T_NATIVE、SIRCL_IDS_NATIVE、TPV、MORE、W_NO_K。新增两条件只交叉指令块。D_P 在 `Before committing the final ranking,` 前分割；D_S 在 `INITIAL: Consider three ranked hypotheses` 前分割。原串=G+V；任务、证据、候选、输出JSON不变。每个实际块单独落盘及hash，不重新写提示词。

### 已证实的单位标注修复：parent_trace_unit_labels_v1

源码追溯发现，三个主数据集的processed `duration_ms`实际保存微秒；统一源适配器 `_registered_trace_duration_projection` 明确要求×0.001，S分支已经应用。父版 renderer 则直接聚合存储值并命名 `exl_p95_base_ms/exl_p95_fault_ms/inl_p95_fault_ms`。因此本轮P侧、T_NATIVE、TPV、MORE、W_NO_K只将这三个字段后缀改为`_us`，及复合unit中的milliseconds改microseconds；值、排序、log-fold-change（原存储单位上的+1平滑）、时间区间、统计、选择及G图片全部不动。S侧已正确归一化的ms字段不改。

这属于主计划要求的源证据证实后独立版本化修复，不是新的选择器。旧结果/缓存/父版源码不改；新P侧不能声称与旧请求逐字节相同，也不复用单位文字不同的旧推理。CPU先核对九父条件未经适配时的字节身份，再核对适配后只发生上述白名单替换。图像仅为G，没有被误标的R时延图，不需要重新渲染。

正式 check120 继承 RQ3.5，三个主数据集各40；最多2640次。screen60用于三例资格，按 `hash(42,cpu,opaque)` 各选一例。两集合是重复暴露病例，不是独立测试。RQ3.4完整公共context、时钟修复和图像只读复用，不重跑raw/preparation；缺缓存明确报错，不暗中换池。模型保持各自统一local profile和8192输出适配器。

## 三轮静态与CPU

三轮分别检查科学逻辑；性能/链路/恢复/预算；泄漏与语法。记录在 docs/issues/RQ3_6_qualification_2026-09-26.md，不把重复运行同一检查当三轮。CPU最多1800秒、三例×11条件×两模型=66份请求，三独立物理核心；测试九父条件字节身份、两交叉动作、四格不坍缩、公开时间、私有标签扰动不改变输入、跨模型同输入、两模型真实token容量、图片可读、flags恢复不触碰cache。保存全部共同operation源行供单位/统计定义人工审核；同名字段数值不同不是自动判错。静态不能证明无bug，三例不能证明全体容量。

## Smoke与恢复

一个逻辑smoke：三个资格病例×E_S_G_P_V_S/E_S_G_S_V_P/W_NO_K×两个模型=18次以内；600秒包括预检、模型启动切换、请求、持久化。先Qwen再Gemma；只管理本supervisor拥有的进程，已有服务拒绝接管。到期中止，不续开另一计时窗。纯到期可通过但记录未覆盖；请求/协议/持久化等异常不通过。检查conversation完整输入输出、raw/partial、PNG及accounting；模型答错不是资格失败。

历史调用只从RQ3.5累计账本导入一次（该库已包含更早调用），整个大RQ总上限40000，重试与失败也计数，不涉及API收费。范围内完整请求去重；模型身份在请求identity中，smoke与formal隔离。新任务flag在写盘完成后提交；done、request_timeout fail只读flag跳过，不重建旧输入；其他infra fail立即停止，修复需显式处理，不自动重跑。中断无flag的单元续跑，已发未完成请求仍算额度。

运行器每case加载一次context，最多八核心worker进行有界预取，36推理并发。CPU与推理重叠，不逐arm重算源统计；不足10GiB停止新提交并排空。停止后保留完成记录、超时flag和partial，不拼接半截答案。模型输出、原始conversation、给模型的图片及离线核验sidecar均持久化。离线核验不改模型排名。

## 分析合同

阶段A主效应、交互和新两指令条件均按完整case配对。MRR=AC@1+tail-RR，另报AC@3/5、候选数、repair/break、未知ID与截断；Pratt-Wilcoxon、paired dz、预注册Holm，分模型/数据集/根因层次和group敏感性。具体family与后续推进规则沿主计划；不使用资格成绩选条件，不只报告成功cases。
