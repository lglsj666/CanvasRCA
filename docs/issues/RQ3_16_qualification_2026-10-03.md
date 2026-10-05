# RQ3.16：设计、实现与资格报告

2026-10-03，America/Toronto。**本轮已完成并停止：静态、完整CPU、实际视觉审查及GPU smoke全部通过；正式调用0，全量启动关闭，自有服务已退出。** 这是工程资格报告，不是正式效果报告，也不构成MRR或解释可信度改善的证据。

## 研究决定及历史依据

主线仍是保留有效诊断证据，让视觉完成明确的比较任务，并在强文本上证明成本受控的排名收益；先验证收益，再研究压缩。复核19份权威实验/综合报告的设计、结论、有效性和失败机制，并核对当前Codex及conversation_oct_01主线。阅读范围、文件和SHA保存在[历史审查清单](../../RQs/RQ3_16/results/marginal_coverage_v1/qualification/history_review_manifest.json)；这不是对所有历史附录和全部单例回答重新审计的声明。

历史共同约束：补充证据、候选覆盖、可预测性和视觉展示都不自动带来诊断收益；screen优势可能在扩量后消失；缺少数据图元对照，不能把“图像输入改变了回答”称为图形计算收益；Top-1相近时Top-5仍可能显著下降；强文本及完整失败分母必须保留。

RQ3.15的预选联合图未达到采用条件，本轮不恢复二维联合图路线。MARGINAL均值较高只是事后开发线索，不能直接选为已证实方法。其图元贡献尚未被验证，同时AegisLab存在列表缩短和Top-5损失。因此新问题是：**分别比较父、子reference/current耗时分布的数据点，是否有同事实强文本之外的收益；这种效应与输出候选容量是否相关？** 不修改关系选择，不筛掉退化病例，不根据gold选择视图。

完整计划见[RQ3.16计划](../experiment_plans/RQ3_16_Marginal_Coverage_Plan_2026-10-03.md)，规范协议见[RQ目录协议](../../RQs/RQ3_16/descriptions/RQ3_16_experiments.md)。

## 八臂与判定

| Arm | 输入/输出规则 | 主要作用 |
|---|---|---|
| BASE_FLEX | 冻结WINDOW_TEXT；允许1—5候选 | 同期基础文本 |
| PAIR_FLEX | 原连续配对文本；允许1—5候选 | 同期同事实强文本 |
| MARGINAL_FLEX | PAIR＋原边际图；允许1—5候选 | 边际图同期复测 |
| BASE_FIVE | BASE；固定5候选 | 基础文本接受同样输出干预 |
| PAIR_FIVE | PAIR；固定5候选 | 同事实、同输出容量文本控制 |
| MARGINAL_FIVE | PAIR＋原边际图；固定5候选 | 预选方法 |
| MARKLESS_FIVE | 同文本、同布局，删除数据点；固定5候选 | 检验数据点的增量作用 |
| MARGINAL_REPEAT | MARGINAL_FIVE真实独立调用 | 固定配方下的可重复性 |

FIVE只改变请求schema的services.minItems（1→5，maxItems仍5），并给所有FIVE臂加入完全一致的短说明。候选、JSON字段、canonical scorer和解码配方不变；禁止输出后补写候选或去重救分。FLEX三臂登记为同期独立复测，用来减少输出干预与运行批次混淆；新调用独立记账，不覆盖旧响应，不把旧响应再次当独立样本。

保留220个exposed eval身份及冻结事件组。正式矩阵仅登记为1,760位置，预计45个精确回退引用，重复臂仍真实发起；正式attempt上限1,802，加18次smoke，总上限1,820。历史RQ消耗保留，未重置。当前没有正式执行授权。

四个主要比较：MARGINAL_FIVE−PAIR_FIVE全体、−MARKLESS_FIVE全体、−BASE_FIVE在AIOPS120例、在Aegis100例。病例和事件组各执行同一四项Holm族；Pratt-zero Wilcoxon、round12差值和paired dz，不报告CI。三个FIVE−FLEX、两项FLEX内容/表示比较、重复稳定性及四臂交互为七项次要MRR族，另设相同七项AC@5族。交互要求四臂齐全，未知分数按系数计算界限，不错误限制在[-1,1]。

采用需要四项主要比较方向为正且两层pH<.05；对PAIR整体ΔMRR≥.02、对BASE在AIOPS≥.03/Aegis≥.02；三个数据集分别对BASE/PAIR均为正。另要求每数据集对两文本控制的配对AC@5不下降，以及实际input+output≤BASE1.20倍、PAIR1.10倍。AC@5护栏不是统计非劣证明。任一必要条件失败，停止该边际图候选，不自动改布局或选择事后最好臂。

## 实现及历史保护

代码位于[RQs/RQ3_16/src](../../RQs/RQ3_16/src/main.py)，采用main/utils/exps/tests/gates五功能模块，静态计数1,192有效源行，配套三份规范description和一个入口shell。公共编译器不读取私有评估标签；使用已资格的公共配对packet，私有标签只在后置评分读取。全部220例验证文本、系统指令、候选次序、事实及schema差异；私有字段扰动不改变公共输入。

复用211张RQ3.15原MARGINAL PNG，仅新增211张MARKLESS。所有新图均由统一renderer生成，复用已注册C20和已有操作；没有新增组件、操作或文字截图臂。为C20接通既有presentation.marks开关并同步有意抑制的绑定清单；不支持此开关的C19仍拒绝该配置。默认图形语义不变，旧实验图、输入、回答、分数和冻结归档均未覆盖。折线和缺测处理不变。

改变前保护清单有176个历史依赖，允许的前向变更仅renderer utils、RequestPairPlot、RequestPairMarginals及构建bundle。当前184文件源码已[冻结归档](../../RQs/RQ3_16/results/marginal_coverage_v1/qualification/source_freeze.json)，源码合同SHA为`612c92660201ece2cd6cdbbaf7cc7b33fe31ca18deebbea824be96b3641f82d1`。

## 静态与CPU结果

| 项目 | 结果 |
|---|---|
| AST/导入/JSON/bash/模块限制/历史保护 | 通过；TypeScript typecheck与统一renderer构建通过 |
| 完整CPU | 220/220，最终源码检查约100.9秒 |
| AIOPS-2022适用性 | 60/60 |
| AIOPS-2025适用性 | 55/60 |
| AegisLab适用性 | 96/100 |
| 不适用病例 | 9例完整文本回退，无病例排除，45个登记同输入引用 |
| 实际图像/绑定 | 422张图，32,624个绑定检查通过 |
| 实际重绘 | 3张默认边际图与历史PNG逐字节一致；3张MARKLESS确定性重绘一致 |
| 最大输入 | 26,141 tokens；加8,192输出=34,333＜40,960；无上下文排除 |
| 最小公共候选数 | 59，全部满足五候选要求 |
| 指定smoke病例CPU检查 | 3/3，约7.2秒，全部八臂输入路径覆盖 |

| 数据集 | MARGINAL_FIVE / BASE_FIVE输入 | MARGINAL_FIVE / PAIR_FIVE输入 |
|---|---:|---:|
| AIOPS-2022 | 1.1540 | 1.0390 |
| AIOPS-2025 | 1.1870 | 1.0420 |
| AegisLab | 1.1941 | 1.0357 |

以上为真实processor输入token，均通过1.20/1.10预算；最终输出成本尚不能从CPU结果推断。零值、缺失duration、跨Trace同名身份、重复身份、循环、重复调用、单位、阶段边界和确定抽样等合成数值回归通过，48对数据由独立NumPy计算核验。原341,635对原始数据的数值资格从RQ3.15继承，本轮没有重新处理全部原始Trace。

原子commit、缺少commit不得跳过、完整phase先于上下文/GPU跳过、独立重复identity、全量门禁关闭、Holm与未知交互界限等回归通过。准备使用既有最多8进程、不同物理核固定和source/cloudbed交错分派机制。

实际打开三数据集、最稀疏合格阶段、最大极值和最长操作名的12张PNG；未发现裁切、标签遮挡或位置改变。全部MARKLESS的HTML在仅去掉原数据点组后与原图一致。可浏览[实际例图库](../../RQs/RQ3_16/results/marginal_coverage_v1/qualification/gallery/index.html)。人类可读性不证明VLM能正确理解图形；点的重叠及按秩抽样的含义保留，MARKLESS仍包含轴范围和文字。

开发中修复了C20中间设计校验兼容性、一个测试fixture遍历错误，并补齐Codex的仅超时smoke规则；最终源码重新完成静态和完整CPU资格。历史规则修复前的CPU记录保留，不冒充当前源码资格；细节见[修复记录](../../RQs/RQ3_16/results/marginal_coverage_v1/qualification/implementation_repairs.json)。

## GPU smoke与输出审查

本地Qwen BF16、40,960上下文、请求输出8,192、显存利用率参数0.75、原解码配方和固定seed。沿用三个预定eval身份，每数据集六臂，共18次，八种路径各至少两次。共享600秒窗口；实际运行205.27秒，包含逐请求审查至392.91秒时完成，未用满预算、没有追加调用。

- 18/18真实调用完成，18个原子commit；无超时、基础设施错误或截断，finish_reason均为stop。
- FLEX 6次、FIVE 12次；12个FIVE结果全部恰好五个不同合法ID；没有后处理补写或救分。
- 9份实际图片传输均与资格PNG一致，每份877 image tokens。实际prompt、完整文本、schema、请求身份、图片、conversation、streaming checkpoint和轨迹均已逐请求核对。
- processor预算与实际服务端input token逐份一致，input/output/total记账守恒，共397,439 input+output tokens；18份输出使用原canonical scorer重新评分，结果一致。
- 两次repeat都有独立call identity和实际生成；同seed下相同回答是可重复性记录，不是广泛随机种子方差估计。
- 自有服务PID26529、engine26689、runner27065均退出，端口21956已关闭。真实完成态重启检查返回`launched_model=false`，调用数仍18。正式调用0。

详细证据见[逐请求输入输出审计](../../RQs/RQ3_16/results/marginal_coverage_v1/smoke/detailed_input_output_review.json)、[完整artifact审查](../../RQs/RQ3_16/results/marginal_coverage_v1/smoke/artifact_review.json)和[退出/停止状态](../../RQs/RQ3_16/results/marginal_coverage_v1/qualification/postflight.json)。

**解释质量仍有问题，已保留，不因smoke通过而隐藏：** AIOPS-2025 BASE_FIVE把+25分钟说成早于+18/+21分钟；MARKLESS_FIVE的首选列表为326，理由却说130排名第一；AegisLab MARGINAL_FIVE把437说成437→495边的leaf，并把耗时差异当作本地起因的证明；其他回答也存在由观测配对直接排除传播的过度因果推断。它们是模型结果，不是基础设施故障，也不能据此按三例smoke调提示、筛臂或改科学门槛。后续正式解释审查必须保留方向、单位、时间、列表一致性及无依据因果断言，不能以confidence替代可信度。

## 最终状态

计划、实现、配套例图、静态/CPU/GPU及单人科学/预算审查均已落盘；单人审查不是外部独立复核。**本轮到此停止。** 全量1,760位置只登记、不运行；若以后用户明确授权，再进行只改变执行权限的可审计激活，保持当前科学协议和已资格输入。RQ3整体性能、视觉贡献、成本及解释证据目标仍未达成，当前不能宣布MARGINAL或固定五候选有效。
