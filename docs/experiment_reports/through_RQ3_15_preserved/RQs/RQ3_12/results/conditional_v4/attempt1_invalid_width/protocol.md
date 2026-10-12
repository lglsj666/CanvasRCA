# RQ3.12 预注册：候选条件化残差画布

日期：2026-10-01。实验 `exp_conditional_residual`。当前 v4 修订见§0V4；v1/v2历史协议保留。

## 0V4. 当前实现：两个共同目标的聚焦比较 — 2026-10-01

`rq312_conditional_residual_v4` / `conditional_residual_v4.json` 延续§0V3授权与数据/参考标准。v3第一次准备因Q编号不兼容现有renderer被拒绝，改为M13接续编号后，第二次真实准备发现12列中长科学计数数字/状态横向越格；18例已提交的准备和其余失败图/源快照完整保留。部分真实token检查显示Aegis新表增加24.3%输入，尚未做完整CPU，不能当资格通过。两个失败准备尝试没有GPU调用，也不重置900预算。

v4只比较选择时实际用于最大分歧的**两个共同target**，最多提供**6条新增M13–M18原始操作数**（2target加其候选最佳anchors）。所有原12M、R/L/G和完整候选仍在每臂，新增原始操作数在六臂相同，不靠删除基础证据或填充基线压低比例。候选原模型最多6行，当前更聚焦最多2行；依据最终两个目标的实际合法共同预测选最不同的2候选。预测资格与至少2共同target/.5差异、合计30/各10竞争病例门槛不变。额外候选仍在完整文本宇宙，未显示不构成排除。

复用未改的diagnostic.compact，矩阵宽度由公开有效列数统一确定`max(640,280+90*columns)`，最大1360；高度仍`max(360,340+110*prediction_rows)`，最大1120，font16和组件12不缩小。两个目标通常640宽，避免无用大画布和长数字越格；普通观测/条件预测都使用相同宽度函数。无新增操作数时既定原12M fallback仍由同函数正确处理。真实完整输入成本/容量须CPU验证，最终总token成本仍是成功条件。

该修订在任何模型调用之前只根据公开参考/图形/输入成本诊断作出；不从RCA答案/score选择参数。其他六臂、病例、配方、统计/成功目标、参考/支持域与科学/预算规则全部按§0V3。v3不是失败模型结果；v4须重新完整资格。文中旧12操作数/6profile/1360固定宽计划在当前版由本节覆盖。源与该协议在模型调用前冻结，后续状态写非协议日志。

## 0V3. 当前参考适用性修订与完整执行授权 — 2026-10-01

最新用户明确要求“先解决一下参考预测的适用性，然后就开启全量实验”。新版本 `rq312_conditional_residual_v3` / `conditional_residual_v3.json` 版本化修订参考数据支撑，授权实施、完整CPU资格、真实图像/科学/预算审查、有界GPU smoke和通过后完整140×6位置。下述v1/v2停止/预览/失败条目是历史记录；本节优先。v2完整CPU在代码/数值/图像/容量/输入成本上通过，但两AIOPS竞争均0；已归档failed_cpu_source_v2.tar.gz，0调用。

### 数据与选择

原12M的原始精确数值、R/L/G、候选/顺序、system、scorer、trace-derived相对split与140 exposed eval身份全部保留。旧12条按异常选择，不能同时假定它们适合估计指标依赖。v3从同一案例冻结label-free public observation directory绑定canonical `metrics.parquet`的匿名实体/metric/source_key，用已经验证的window与timestamp，读取已有公开列；不读取注入anchor、private root或先前模型回答，不新增数据或训练VLM。

新增指标在原64格内取有限真实采样的median，不插值。这是明确的新增原始操作数，不能称仅修展示或与RQ3.11基线字节相同。最多12条新增M13–M24指标，其准确64值以无损codec和实体/metric/native unit绑定**在六臂完全相同地提供**。原12M不替换；新ET/ER是保留原事实并共享新增操作数的更强基线。CT/CV及OT/OV仍等信息双胞胎，不能跨v2/v3直接把成绩增量归为视觉。

筛选规则冻结于config：M且实体在完整候选宇宙、公开role不为state/counter/configuration、semantic包含latency/rrt/cpu_usage/cpu.usage/cpu_load/load_average/memory/process/request/count/response之一且不包含total/seconds/limit/capacity/cache/swap/fail/error。这些只是公开语义过滤，不认证gauge/单位或请求活动；未验证的source_unit不转换或赋予物理解释。不同来源同entity/semantic按public observation ID排序选一列。原始隔离资源证据仍保留。

参考阶段在实际采样格完整且非恒定的池上拟合全部有向一元ridge关联，这是比60%更严格的选择过滤。原12样本/6每时间块、ridge .1、双向CV RMSE比≤.8、当前≥3与60%、ref[min,max]±1SD支持和阈值3都保持。向量化参考SSE只加速候选过滤；被使用关联用独立标量fit_dependency复算，标量是权威。常量/退化参考不伪造关联；它们继续可作为原始观测和普通变化测量。可靠常量基线本身不能制造不同候选的预测。

对每个**直接匿名实体**及target，先仅按参考CV确定最优anchor，随后验证真实当前paired bins及支持。当前数据不能重拟合/放宽接受或重新挑较方便的anchor。公开对比选择可以使用当前已合格预测的分歧，与旧disagreement-first显示原则一致。每对候选按单目标分歧降序贪心选择最大分歧目标与最佳非冗余伙伴：语义不同，参考|Pearson rho|<.98，paired bins逐目标相同；不声称目标独立。选最高两目标均值的候选对，保留这两target和它们最佳anchor，再按与首候选的同目标分歧增加能放入12操作数预算的其他候选anchor。完整候选不删除；source_key、全部池/拒绝原因与数值筛选留CPU audit，不进入模型。最终仅选出操作数重新拟合，沿原公开service唯一owns扩展构造最多6profile，资格依据**最终模型**实际≥2共同目标的竞争，不以池中有潜在关联替代。

没选出新增操作数时，原12指标的v2方法作为公开固定fallback，保持完整分母；没有可计算矩阵仍不传PNG/空附录。原sparse renderer与高度函数不改。

### 科学与运行门槛

搜索许多参考关联并挑当前分歧可能选择偶然相关；CV阈值不是已校准置信度、多重检验或因果保证。可能挑中与故障无关的正常波动，OOD预测依然未知。数据是已暴露eval方法开发，不能叫独立测试；只在完整CPU检查后冻结一次版本，再跑预注册六臂，不从部分模型结果改方法。主要/次要contrast、预选CV、原统计族与成功目标均保持。

GPU前原门槛仍是AIOPS竞争合计≥30且各≥10，主要input CV/ET≤1.20，全部840完整input+8192≤40960；不得降低门槛、删病例或用模型成绩判smoke。8物理核workers/source groups交错、36请求线程/8writers、原BF16配方、无attention/训练/Gemma、smoke18次/600秒含startup仍固定。所有版本共享同一900 allocation，不是v3的新额度。

预算范围纠正：Codex.md的2026-09-12用户条目明确移除RQ3-wide40000 cap；2026-09-16恢复的是**RQ3.1**的per-major-RQ40000，不能误移到独立RQ3.12。v1/v2协议把“继承major”不清楚地扩展，是agent起草的范围错误，不是用户新限制。v3保留一个自愿保守的**RQ3.12全部版本**40000累计上限，并以所有RQ3.12 roots ledger/历史消费证据审核；同一900计划实际更严格。RQ3.10 767和RQ3.11 1121等历史调用仍分别记录，不重置、删除或伪称未消费。其他RQ可受自身授权和预算约束。本修正不扩大本轮模型调用、重置smoke或放宽科学资格。

### DD-RQ312-PUBLIC-REFERENCE-OPERANDS

Decision：用同案例完整公开参考池检验关联，再选择少量支持内、不同预测；把所有选出的原始操作数送给六臂共同基线。拒绝降低.8/60%/数量/支持阈值、参考期外拟合、将unknown填0、仅添加CT/CV指标、无限增加PNG或挑容易案例。用户的新方法授权允许该版本化数据支撑修订。

Evidence：v2全部823个accepted fits与独立NumPy一致；缺少合格共同目标来自参考退化/选中指标依赖稀疏及当前OOD。三个固定公开检查案例完整池存在通过原验证标准的关联；仅用于公开实施诊断，未做新VLM请求。正式资格仍须完整140验证。Primary source：CIRCA KDD2022论文讨论参考/故障分布缺乏overlap与回归误差；本项目没有其结构因果图、正常期认证或descendant adjustment，不能称复现或因果识别。[作者论文](https://netman.aiops.org/wp-content/uploads/2022/08/KDD22-CIRCA.pdf)、[官方代码](https://github.com/NetManAIOps/CIRCA)、[ACM正式记录](https://doi.org/10.1145/3534678.3539041)。它支持问题与限制，不证明本选择算法或性能。

Consequences：使用独立conditional_v3 preparation/results，重新静态/CPU/视觉/科学/budget/freeze/smoke。v1/v2失败与原源归档保留。新版本不自动获得任何资格或MRR/可信度声明。代码和协议在模型调用前冻结；运行结果记录于日志/findings，不再改本协议导致失配。


## 0. 当前 v2 修订与用户停止边界 — 2026-10-01

**最新执行授权：** 用户看过例图后要求重新进行CPU回归、GPU smoke，并仅在均通过后启动全量。本指令解除前述代码暂停；v2按既定完整140例、六臂、适用性/成本/科学/预算门禁执行。真实CPU资格、18次/600秒smoke和实际输入输出审核都须通过，才可提交formal；不降低原资格阈值、改变候选/病例或重置历史调用。旧暂停/预览记录保留为历史过程。

**当前版本 `rq312_conditional_residual_v2`，配置 `conditional_residual_v2.json`。** 用户在发现问号图后授权修订代码，并明确要求“代码改完之后就先停下”。原代码阶段停在源码/静态检查，后来仅追加下述有限预览。v2的完整案例准备、tokenizer/processor、CPU回归、全队列renderer/PNG资格、GPU smoke和全量实验均待后续继续。此前CPU→GPU→formal的执行许可仍暂停。

随后用户要求导出今天各实验和新版每个arm×数据集的例图；该新请求仅授权三个固定exposed-eval案例的预览。六张新版PNG已实际生成并通过DOM/字段检查，已目视检查三张COND例图及单例确定性重绘；没有运行完整CPU回归、模型tokenizer或GPU。预览构建包独立命名，canonical bundle、准备目录和资格登记不改写。预览暴露并修复两处接口问题：仅新的单卡 `diagnostic.compact` 允许360高度，原组件保持600下限；移除SVG内部未使用尾部空间以避免一行预测时panel overflow。失败尝试均保留于 `results/conditional_v2/preview_gallery_20261001/`。完整执行仍暂停，预览不授予科学/模型资格。

v1 是完整 CPU 可行性失败，不是模型性能失败：两个AIOPS竞争案例各0；输入token比1.339239。其140例、280图、资格/诊断/配置和代码/renderer快照保留在 `results/conditional_v1/`，源码快照为 `qualification/failed_cpu_source_v1.tar.gz`。v1 没有模型调用。以下原始协议和文献记录保留；与本节冲突的采样支持、展示和版本/执行状态由本节 supersede。

### 0.1 区分未采样画布格与真正缺测

固定原12条64-bin指标、R/L/G、候选、system、scorer与trace-derived相对split。新增只读CPU adapter：用冻结的label-free public context确认时间原点与source hash，仅从该案例canonical `metrics.parquet`读取timestamp列。身份经canonical manifest的opaque ID对应核对；不读raw benchmark、不访问标签/注入时刻、不选择新指标、不插值。

源时间戳投射到原64格，得到独立于任何单条指标数值的 `sampling_bins`。覆盖率分母是相位内实际采样格；某指标在该采样格为null时仍计入分母，真正缺测不会被排除。没有原始采样的画布格不算缺测。相位跨界格仍排除。此覆盖率是原binned证据的采样格覆盖，不能称原始每一行的完整采集率；多个源采样落在同一格时，原标量的聚合保持不变。

支持DTO缺失、源身份/hash改变、public window不符、或已有数值位于未采样格，都fail closed，不按有限值倒推“预期采样”，也不转入猜测/插值。实际source clock能否与全部140个冻结输入完全对应仍需真实CPU检查。

参考数量12、fold6、当前数量3、覆盖60%、ridge .1、两折RMSE比≤.8、支持域1个参考SD、阈值3均保留。时间块仍按相位的时间中点划分，不能按观察到的配对值重选方便的折边界。关联不能称干预，越出参考支持域仍不提供预测。修复采样支持不保证模型将变得适用。

### 0.2 删除没有可计算诊断信息的派生内容

只保留可计算的观测变化列。OBS每格只显示A；不再绘制不适用的E/R/S。候选行只有至少一个合格预测才保留；unknown/conditioned单元为空位，没有数字、问号、斜线、状态、坐标条或零填充。anchor IDs仍在行绑定中。整行无预测就删除；整列无可测观测就删除。全部基础12M和候选宇宙仍在原文本；这不构成依据缺失值删除候选。

新 `diagnostic.compact` 是独立组件，原 `diagnostic.matrix` 的有效v1输入行为保留。表格没有任何可计算观测时不生成PNG，也不增加空的比较附录；相应四派生臂明确回退相同ET输入，ER继续独立真实请求，完全相同的其他臂可引用一次已提交调用。正式案例和统计分母仍为完整140；不能据可用性另选队列。无图案例没有“视觉机制”可供检验，必须单独记录，不可将其算作读取图像成功。

观测字段/实际数值与预测字段各自区分；稀疏位置用column index明确绑定，text/visual传输相同有值表和空位。未知的详细原因和全部候选内部profile保留CPU audit，不挤占模型可见图像。参数和完整重复测量对象从逐例附录移除，保留公共clock/support、指标实体/单位、reference与scale、真实paired bins和必要静态语义。派生显示仍4位有效数字、状态按未舍入值计算。原精确遥测文本不改写。

画布宽1360，字体设置沿用16；专用比较组件内部文字12与v1一致，不靠进一步缩小文字适配。高度固定由公开有效行数计算：`max(360,340+110*prediction_rows)`，最大1120；无预测的表只画有效OBS。该公开函数在全部病例/臂统一应用，真实token成本必须重新测量，不能用静态尺寸推定已满足成本目标。

### 0.3 登记、资格和预算

v2 独立 preparation/results 名称 `conditional_v2`。沿用原140 exposed eval及三smoke身份、六臂/主要次要统计族、预选CV、成功门槛和reason审核。CPU竞争合计≥30/各AIOPS≥10、CV/ET主要范围input≤1.20、所有完整input+8192≤40960仍是GPU前门槛，不因删除未知格而放宽。

v1 消耗0模型调用；同一900 allocation带到v2，formal≤882、smoke≤18/600秒、major累计40000且全部历史消耗保留。v2 不创建新的smoke额度去抵消旧消费；v1源/图/结果不用于v2资格通过证明。

静态检查使用 `bash RQs/RQ3_12/scripts/local.sh static`，只做AST/compile、配置/接口与bash语法、TypeScript noEmit，不加载案例或构建bundle。未来原运行顺序仍要求显式build→静态刷新→登记→完整prepare/CPU→视觉/科学/budget review→freeze→有界smoke→实际输入输出审核→formal。v2代码的新测试定义尚未执行；静态通过不是功能通过。**本次静态检查完成后停止。**

## DD-RQ312-SUPPORT-SPARSE：修订采样支持并删除不可用派生字段

日期2026-10-01，状态adopted for code/static，runtime pending。Context：Aegis问号图有真实16/32参考观测，旧规则把细画布未采样格与真正缺测混合；整批还缺少竞争预测且成本超限。用户要求修代码、删没有诊断信息的内容，并停在代码完成。

Decision：source timestamp独立采样格支持、同值紧凑稀疏表、无信息不生成图，保留旧失败和完整候选/病例/阈值。

Evidence：`results/conditional_v1/qualification/cpu.json`、`diagnostic_failure.json`与 `logs/2026-10-01_cpu_qualification.md`。105个旧被接受拟合经独立数值核对；不能将修复展示认作增加了预测能力。

Rejected：把60%降至50%、插值造数、把unknown画成0/健康、删整批不适用病例、重置预算。Consequences：重新建立全套runtime资格；未来可能仍失败，不能从静态修复预测MRR、竞争覆盖或最终成本。



## 1. 为什么选择这一轮

决策依据是原始协议范围内的完整开发结果，不能合并不同 RQ 的分数作新检验。

| 依据 | 已验证的结果 | 对下一轮的约束 |
|---|---|---|
| [RQ3.7C/RQ3.8](../../../../../../../../RQs/RQ3_12/docs/experiment_reports/RQ3_7C_RQ3_8_Qwen_Analysis_2026-09-30.md) | RQ3.7C eval 相对强文本 n=295、macro ΔMRR +0.0566、Holm p=.1712、dz=.1341；已暴露 test n=357、+.0490、病例 p=.0532、组级 p=.0420。相对分离面板的 test 增量仅+.0032 | 数值与关系联合有条件性支持，但没有锁定局部连线机制；不能继续只换布局 |
| 同一报告 RQ3.8 C | 全图叠加相对同事实文本已暴露 test n=342、macro Δ−.0771、Holm p=.00112、组级 p=.000679，输入增加约80.5% | 不重复完整原始 dashboard；限制新增比较对象与实际成本 |
| [RQ3.10](../../../../../../../../RQs/RQ3_12/docs/experiment_reports/RQ3_10_Qwen_Analysis_2026-10-01.md) | MATRIX−BASE AIOPS Δ+.0181、Holm p=.8626；成本+75.1%。有效稳定冲突对照仅AIOPS22 23例，AIOPS25 0例，Aegis0例 | 不再假定普遍存在活跃健康 peer，也不把 node→全部 pod 写成必然故障规则 |
| [RQ3.11](../../../../../../../../RQs/RQ3_12/docs/experiment_reports/RQ3_11_Qwen_Analysis_2026-10-01.md) | PVH−ET n=120、Δ+.004861、Holm p=1、dz=.014612、总token+3.103%；PVH−PTH n=119、Δ−.000700、p=1；全部3360签名保持；手工式审核12独立案例仍有单位、时序、绑定、归因错误 | 数值保护不是诊断决策保护。停止补丁/分辨率扩量，保留其无损强文本和审计能力 |
| [conversation_oct_01.md](../../../../../../../../RQs/RQ3_12/conversation_oct_01.md) | 建议“实际性能收益＋可分离视觉价值＋可复用方法”；首先比较候选解释预测与观测的分歧，并与强文本、数值求解比较 | 将难题定义为公开可检查的预测比较，避免仅以新画布名称声称创新 |

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
