# RQ3.14：观测保留与实体绑定的有界修复实验

日期：2026-10-02，America/Toronto。版本 `rq314_unified_observed_v1`。本计划取代未实施的 Typed Window Comparison 计划。用户已授权替换设计、部署新代码、CPU/GPU资格及通过后启动全量；本次任务止于全量可靠启动。单一主agent，无子agent、训练、attention、新test或Gemma调用。

2026-10-02 用户修订：所有绘图均通过 unified renderer，优先复用注册组件和操作；不要特殊对待缺测点，折线跨缺测位置连接有效观测，不显示缺测标记。旧 RQ3.14 实现已删除，新实现及其资格尚未完成。本次同步这些规则不代表其余设计已重新冻结或运行资格已通过。权威规则见 [Codex.md](../../Codex.md)，经验依据见 [dashboard 踩坑记录](../issues/Dashboard_pitfalls.md)。

## 研究决定与边界

RQ3.1/3.2的竞争筛选存在能力置换，覆盖修复仍未形成稳定收益；RQ3.10范围对照适用性不足，RQ3.12参考预测未证明故障区分力。停止把候选响应预测当作默认主线。本轮检验原有观测的完整时间形态、唯一实体/操作绑定及源字段类型能否减少排序破坏，不生成候选应有响应、残差根因分数或健康反证。

RQ3.13的双M编号、参考阶段瞬态被压平、duration与exclusive混用、高显著症状盖过操作证据是具体修复依据，并非已确认因果效应。本轮是一次有界开发验证，不预先称核心算法创新、因果识别、降本或可信度提升。

## 输入与编译

保留原始12条64-bin M、所有既有R/L/G事实、候选及原任务/评分。旧140例的RAW逐部分继承RQ3.13 EXACT，不使用旧回答。新增80例Aegis按同一公共基础链构建RAW；为保持基础事实策略一致，仅在RAW基线适配中沿用RQ3.12冻结的附加operand选择与原文字说明，不显示任何条件预测。旧140的附加序列逐字保留；它们不是本轮新增计算或候选方法。基线适配成本单列。所有臂每病例的原子事实相同，标签/历史答案/胜负不进入compiler。

CANON仅改变可引用编号：MET01..12按冻结card绑定，AUX01..06为附加序列；Trace逐行TRC01..，日志LOG01..，关系REL01..；legacy panel数字另存legacy_display_rank，不作为第二套引用。源实体、metric/operation、单位、原值和顺序不变，保存离线可逆变换证明。协议读法中的旧引用也同步替换。

SAFE在CANON上追加固定源类型说明及不超过350token的规则：duration quantile不是exclusive；独立p95不可相减；未知单位不换算；累计量/资源/restart分别读取；同实体相关指标不作独立因果票；没有边、缺测、未越界和恢复均不证明健康；时间与图边不证明起因。源类型来自字段字符串的确定性映射，未知保持未知，所有数据集规则相同。

WINDOW使用全部有限观测，折线按原时间坐标跨缺测位置连接有效观测，不显示缺测标记、特殊断线或警告，不向源数据填入插值数值。记录首末、最小/最大及bin，不额外突出缺测间隔；不新增变化率或跳变分数；公共split不是注入时间。原生单位不推断修正。图形显示原始64-bin全窗口形状，范围按每条序列自身min/max明确标注，不以异常分数控制大小、颜色或顺序。实体与完整metric语义贴近图元。Trace独占p95及实际所属实体同卡表示，完整Trace细节和日志保留在各臂共同文本中，未提供逐时测量时只列窗口/聚合字段，不伪造时间曲线。图卡按实体及事实ID排序，数值同一格式，完整精度仍在共同原文。

同摘要文本与逐字截图包含同一组显示字段。原始64-bin完整序列在所有臂共同文本中；图形额外重复其形状，文本/截图给出相同摘要和原文定位。此对照测量完整表示包，包括选择性重复与空间组织，不能单独归因为某条连线或某个图元。共同原始事实和摘要的原子清单一致。未把图像有、文本没有的事实算作视觉效应。

最多1张PNG，宽1120，高不超过2800；沿用注册组件的字体比例，主标签18px，SVG轴标签为其0.75倍（缩放另由实际面板决定），实际PNG必须可读。扩大高度用于容纳完整曲线与Trace卡，不能靠缩字满足旧2048px限制。内容超出容量时在CPU阶段重设计，不能按答案删卡或缩小字体。只有无可用观测的派生内容省略，原始事实与病例保留。以原生marks=false呈现的WINDOW_MARKLESS替换旧SAFE_EVENT_VISUAL；它保留同一面板布局、轴和共同摘要，去除曲线/条形长度标记。这样不需新增包络状态组件，也不继续引入旧参考包络机制。此为GPU调用前的公开协议修订。

## 九臂与样本

| arm | 内容 |
|---|---|
| RAW_TEXT | 原始强文本，新调用 |
| RAW_REPEAT | RAW真实重复 |
| CANON_TEXT | 仅唯一编号修复 |
| SAFE_TEXT | CANON+源类型/读法 |
| WINDOW_MARKLESS | SAFE+同摘要和统一布局，使用现有presentation开关移除图形标记 |
| WINDOW_TEXT | SAFE+新全窗口和操作摘要 |
| WINDOW_VISUAL | SAFE+同摘要及全窗口形状，预选方法 |
| WINDOW_PIXEL | SAFE+摘要文字原样截图 |
| WINDOW_REPEAT | WINDOW_VISUAL真实重复 |

220例exposed eval：固定旧A22/A25各60，Aegis完整100，旧140必须包含。新增80不是独立测试。按原事件/泄漏组核验；保持train/eval/test身份，不重新分割、不筛掉难例。全部1980位置构成正式矩阵。只有非重复臂完整请求字节等同才允许引用；重复始终真实调用。

## 统计、成本与采用

四项主要比较为WINDOW_VISUAL−RAW（AIOPS120）、WINDOW_VISUAL−RAW（Aegis100）、WINDOW_VISUAL−WINDOW_TEXT（全220）、WINDOW_VISUAL−WINDOW_PIXEL（全220），同一Holm族；病例及事件组等权分别校正。Pratt Wilcoxon双侧、逐差round12、paired dz，不报告CI。

采用须四项均正且病例/组pH<.05；AIOPS部署Δ≥.03、Aegis≥.02、图相对同摘要文本≥.02；两个AIOPS各正向；每数据集配对input+output≤RAW的1.20。统计功效不保证，未通过不改阈值。无显著下降不等于无害；仅文本/接口有效就报告该结果，不事后选择另一臂冒充预选成功。

次要六项CANON−RAW、SAFE−CANON、WINDOW_TEXT−SAFE、WINDOW_VISUAL−WINDOW_MARKLESS、WINDOW_REPEAT−WINDOW_VISUAL、RAW_REPEAT−RAW。输出各数据集绝对MRR/AC@1/3/5/AVG@3/5，pooled和macro单列。故障/粒度/公开可观测性拆分为探索，保留全部正负结果。Top1修复/破坏、top5新增/丢失单列。

模型契约错误保留原零分；基础设施未知按whole-case配对排除，另给固定已知一侧的[0,1]缺失界限；未知usage不填0。真实支出按call去重，部署成本包括图像和输出，CPU预处理/渲染时间另报。

## 资格与运行

五功能模块；全部dashboard经 `src/renderer/` unified renderer生成，使用其已注册组件和操作，包括预览与视觉控制臂。优先复用现有 `metric.line` 等组件；只有确有必要且现有组件/操作无法满足需求时，才记录原因并新增注册项。共享历史代码只读复用及哈希冻结。CPU最多8物理核固定worker，AIOPS优先不同source/cloudbed。完整220×9 actual processor输入预算、真实PNG像素/文字框/metadata/原子绑定、独立NumPy数值、参考期瞬态、常量/极小值/缺测、单位、可逆编号、采样时钟、resume/调用记账均须通过。

本地Qwen3.8-27B BF16，同一canonical local launcher/client、40960context、继承8192请求输出适配、temperature1/topP.95/seed42；不改共享配方。继承已资格的本地GDN triton backend适配，记录有效profile。启动前核验checkpoint/tokenizer/processor及全部科学源。

单一18call/600秒smoke，三个主要数据集eval各1例，沿用公开预定旧smoke身份，不按得分挑样本。九臂各两次：A22 RAW/RAW_REPEAT/CANON/SAFE/WINDOW_MARKLESS/WINDOW_TEXT；A25 RAW/RAW_REPEAT/CANON/WINDOW_VISUAL/WINDOW_PIXEL/WINDOW_REPEAT；Aegis SAFE/WINDOW_MARKLESS/WINDOW_TEXT/WINDOW_VISUAL/WINDOW_PIXEL/WINDOW_REPEAT。每臂未在全部数据集GPU覆盖须明确披露，全矩阵CPU transport验证补充但不冒充GPU资格。smoke不以MRR/排名/模型parse正确率筛选，记录所有失败；完整性/协议/基础设施必须通过。

正式上限1980调用+42必要修复余量，smoke18，总allocation2040；保留此前所有支出。正式全量前门禁要求CPU、图像人工检查、科学/预算审查、冻结源及smoke实际输入/输出审阅。后台持久化、atomic call/phase、轻量resume；完成自动关闭自有GPU服务。启动稳定后本任务停止，不等待全量结果、不提前分析中途胜负。

解释审核预定每数据集12例，salt=rq314_reason_review_v1、seed42，按canonical JSON [seed,salt,opaque_id] SHA256选择，36×9=324位置。单位、时序、实体绑定、缺失当健康、因果越界分别核验；未知保留，核验机会分母单列；这是后续完整报告工作。

## 系列收官与停止

本轮不满足采用门槛时，保留负结果并结束这一实现；只有发现新的可证伪机制及独立适用性依据，才可另行注册最多一次实质修订，不能自动换布局继续跑。若图形不胜匹配文本/截图，不宣称视觉机制成立。候选条件预测路线不自动重启。

若通过，冻结一个方法，再单独登记一个有限收官批次：强文本/历史TPV视觉锚点、同预算比较与少量预算点、机制/鲁棒性、解释核验及泛化范围。当前exposed eval/test可做回归，独立确认须有经过审核的独立事件。此收官批次未在本次1980调用中执行，也不由启动本轮自动授权。历史test360≥.65及两个AIOPS≥.60目标仍未满足，不因当前实验完成而改称达标。

## Unified rewrite implementation contract

The main image selects existing `metric.line` and `trace.paired_bars`. Registered `appearance`, `indexing`, and `spacing` operations are executed and their intermediate design hashes are saved. No operations are added. `literal.text` is the sole additive component: existing modality-specific tables cannot display the exact mixed summary lines without schema distortion. It is used only for WINDOW_PIXEL. WINDOW_VISUAL, WINDOW_TEXT, WINDOW_MARKLESS and WINDOW_REPEAT share the same summary text; WINDOW_PIXEL replaces those exact lines with their unified-renderer screenshot. All arms retain full original observations in text. This tests a representation package, including selective repetition; it is not a pure information-free visual-mechanism contrast.

The main image keeps native measurements and the original entity/metric/operation bindings, does not compute response predictions, and never treats sampling gaps specially. Derived full-window extrema retain early/transient events that phase averages suppress. Component details omitted from the image remain in common raw text. The old140 RAW inputs are reused byte-for-byte as data; added80 use the identical historical raw adapter, including its frozen auxiliary-operand selection. Selection CPU costs and the inherited reference grammar are reported separately from this observed-only intervention. No historical renderer executes in this path.

CPU input ratio gate remains1.20 separately for all three datasets; context40960 and output8192 are unchanged. Scientific review must inspect whole-roster cost and actual PNGs before any model calls. The proposed exact-text control and markless arm are diagnostic controls, not deployment candidates.
