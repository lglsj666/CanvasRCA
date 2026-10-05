# RQ3.16：边际图元与候选覆盖——Qwen 全量结果及详细机制分析

日期：2026-10-03，America/Toronto。版本 `marginal_coverage_v1`，预选方法 `MARGINAL_FIVE`。本报告为完整正式阶段的最终详细报告；资格、注册、启动、冻结材料及原始结果均保留。

**结论：正式实验已结束并通过离线有效性审计。固定五候选改善了边际图方案的 MRR 与 Top-5，但边际数据点本身的独立收益没有建立，预选方法没有通过采用门槛，应停止当前边际耗时候选，不继续自动更换布局或改选 repeat。**

`MARGINAL_FIVE` 合并 MRR **0.5054**，同事实 `PAIR_FIVE` **0.4436**，配对提升 **+0.0617**。三个数据集分别有正 MRR 差，AegisLab 也不再呈现 MRR 下降。但是 `MARKLESS_FIVE` 已达到 **0.4963**；真实数据点仅贡献 **+0.0091**，220 例中209例MRR完全相同。四项主要比较在病例与事件组的 Holm 校正后均不显著。AIOPS-2025 与 AegisLab 的 Top-5 对同事实固定五候选文本仍分别下降 **3.33、3.00 个百分点**，覆盖护栏失败。

因此，本轮支持的是“当前输入下，固定五候选可修复一部分短列表覆盖损失”，而不是“边际数据点已经提高 RCA performance”。MRR 的正点估计、图元的因果贡献、解释可信度和研究目标达成必须分开判断。

**1. 执行完成度、分母与有效性**

正式队列从多伦多时间13:22:16开始，完成标记写于 **2026-10-03T16:15:54-04:00**。1,760 个位置全部终态：**1,713 次真实响应、45 个精确回退引用、2 个请求超时**，无待处理位置。正式实际尝试1,715次，加18次既有smoke，总 **1,733/1,820**；未消耗的预算不是自动增加实验的授权。Supervisor墙钟 **10,420.07秒，173.67分钟**，包含服务启动/退出。自有supervisor/server/engine/runner均已退出；本次检查GPU为0%利用率，不把残留显存归属于已退出实验。

原220个 exposed eval 病例全部保留：AIOPS-2022/2025各60，AegisLab100。合格关系分别60/60、55/60、96/100，共211；9例按同一输出规则回退基础文本。每个回退病例五个位置引用同输入结果，repeat仍是真实独立调用。这些引用占据相应臂的研究分母，但不重复计算真实调用费用或当作独立机制样本。

超时位置：AIOPS-2025 `INC-3316B6DBC59B / BASE_FIVE`；AegisLab `INC-8E91494BF92F / MARGINAL_FLEX`。答案与usage保持未知；仅从依赖它们的配对计算中排除，完整注册分母与缺失界限保留，不补跑、不计普通模型错误零分。两次超时占真实尝试0.117%。

本轮还存在 **9 份模型输出失败**，全部是重复实体，不是超时：格式仍可解析，但canonical scorer按冻结规则整份零分。五候选只约束数组长度，并不能保证ID不同。所有1,713份真实响应均finish_reason=stop，没有length截断；9份model_failure占真实响应0.525%，零分保留。

离线核验覆盖220份公共文本/数据包/私有评分身份，1,713份唯一提交完整graph、1,758个已知位置的评分回放与实际prompt，843次实际PNG传输hash，以及全部provider usage守恒。实际输入token与CPU processor测量1,758/1,758相同。184文件有效科学依赖及仅执行授权改变的兼容关系、runtime attestation匹配；未重新加载模型权重，权重/processor核验沿用既有CPU资格。独立秩和正态近似实现复核36项Pratt检验，Holm计算亦匹配。无新模型调用，无修改评分、输入、候选或原结果。

模型：本地Qwen3.8-27B，BF16、无量化，40960 context、8192输出请求上限、显存利用率参数0.75，seed42及原解码配置不变。正式运行授权与资格材料分别保存；冻结config的原false不被改写为历史已授权。此处是已暴露eval上的开发证据，不是独立test确认。

| 数据集 | 病例 | Arm | 原始重复ID列表 |
|---|---|---|---|
| aiops2022 | INC-D639854EA9F7 | MARGINAL_FIVE | 297,262,219,228,297 |
| aiops2022 | INC-D639854EA9F7 | MARKLESS_FIVE | 297,262,219,228,297 |
| aiops2022 | INC-D639854EA9F7 | MARGINAL_REPEAT | 297,262,219,228,297 |
| aiops2022 | INC-123B5115D9C1 | MARGINAL_FIVE | 37858,745,13934,33864,37858 |
| aiops2022 | INC-123B5115D9C1 | MARKLESS_FIVE | 37858,745,13934,33864,37858 |
| aiops2022 | INC-123B5115D9C1 | MARGINAL_REPEAT | 37858,745,13934,33864,37858 |
| aiops2025 | INC-B9652C6DC060 | BASE_FIVE | 74051,984,1118,874,984 |
| aiops2025 | INC-EDDC755A08F5 | BASE_FLEX | 207,243,207 |
| aiops2025 | INC-392EE028390B | MARKLESS_FIVE | 137,614,614,614,614 |

**2. 八臂设计与本轮最终回答**

基础为RQ3.14 `WINDOW_TEXT`；连续事实、真实配对、候选、窗口、选中关系、系统提示和边际PNG均冻结于RQ3.15。FIVE仅添加共同输出说明并将schema minItems从1改为5，maxItems保持5；这是一项schema＋说明联合干预，不能单独归因于解码语法。没有文字截图臂或二维联合图臂。

| Arm | 输入/输出 | 最终观察 |
|---|---|---|
| BASE_FLEX | 强基础文本；原1—5候选 | MRR .4336；历史强文本的同期锚点 |
| PAIR_FLEX | BASE＋完整连续配对/统计；1—5候选 | MRR .4317；对BASE配对−.0018，未建立连续文本增益 |
| MARGINAL_FLEX | PAIR＋父/子分别显示reference/current分布点；1—5候选 | MRR .4716；仍有短列表和覆盖损失 |
| BASE_FIVE | BASE；恰好5候选 | MRR .4433；对FLEX配对+.0078，MRR不显著 |
| PAIR_FIVE | PAIR；恰好5候选 | MRR .4436；同事实强文本控制 |
| MARGINAL_FIVE | PAIR＋原边际图；恰好5候选；预选 | MRR .5054；正点估计，但主比较及覆盖护栏失败 |
| MARKLESS_FIVE | 相同文本/图布局/轴/范围/标签/legend；仅去掉样本数据点 | MRR .4963；接近完整图，独立图元收益未建立 |
| MARGINAL_REPEAT | 预选方法的真实独立重复 | MRR .5039；218/220 MRR相同，不择优 |

全部dashboard由`src/renderer/`注册组件生成，markless使用既有presentation控制；三个数据集原图和markless共六张实际PNG重新打开核查。控制仍含坐标范围、实体、操作名和样本量等信息，不能称空白图或无视觉信息。点样本按父耗时秩选择，最多每阶段32对，展示的是真实观测子样本，不是总体概率密度。两端位置的接近不证明配对因果，快child也不证明parent duration是本地执行时间。

**3. 完整绝对结果**

指标均为0—1。AC@K是前K位命中率，AVG@K是AC@1…AC@K的均值，MRR按首次可接受粒度命中评分。存在多个可接受根因时，命中其中一个不代表全部找全。已知均值包含模型失败零分，未知超时不填零。合并按病例加权；宏平均对三个数据集等权。不同n的均值之差不能代替配对差。

| 数据集 | Arm | n/注册 | MRR | AC@1 | AC@3 | AC@5 | AVG@3 | AVG@5 |
|---|---|---|---|---|---|---|---|---|
| all | BASE_FLEX | 220/220 | 0.4336 | 0.3227 | 0.5455 | 0.6045 | 0.4424 | 0.5036 |
| all | PAIR_FLEX | 220/220 | 0.4317 | 0.3273 | 0.5364 | 0.6000 | 0.4379 | 0.4964 |
| all | MARGINAL_FLEX | 219/220 | 0.4716 | 0.3927 | 0.5616 | 0.5890 | 0.4810 | 0.5233 |
| all | BASE_FIVE | 219/220 | 0.4433 | 0.3242 | 0.5479 | 0.6530 | 0.4399 | 0.5160 |
| all | PAIR_FIVE | 220/220 | 0.4436 | 0.3273 | 0.5455 | 0.6591 | 0.4364 | 0.5136 |
| all | MARGINAL_FIVE | 220/220 | 0.5054 | 0.4091 | 0.5818 | 0.6682 | 0.5045 | 0.5627 |
| all | MARKLESS_FIVE | 220/220 | 0.4963 | 0.4045 | 0.5682 | 0.6545 | 0.4939 | 0.5509 |
| all | MARGINAL_REPEAT | 220/220 | 0.5039 | 0.4091 | 0.5727 | 0.6682 | 0.5000 | 0.5600 |
| aiops2022 | BASE_FLEX | 60/60 | 0.3014 | 0.2000 | 0.4167 | 0.4333 | 0.3222 | 0.3667 |
| aiops2022 | PAIR_FLEX | 60/60 | 0.3069 | 0.2167 | 0.4167 | 0.4333 | 0.3222 | 0.3667 |
| aiops2022 | MARGINAL_FLEX | 60/60 | 0.3728 | 0.3000 | 0.4333 | 0.4833 | 0.3778 | 0.4167 |
| aiops2022 | BASE_FIVE | 60/60 | 0.3439 | 0.2333 | 0.4333 | 0.5333 | 0.3444 | 0.4067 |
| aiops2022 | PAIR_FIVE | 60/60 | 0.3192 | 0.2167 | 0.4167 | 0.5000 | 0.3167 | 0.3833 |
| aiops2022 | MARGINAL_FIVE | 60/60 | 0.4286 | 0.3333 | 0.4667 | 0.6167 | 0.4111 | 0.4800 |
| aiops2022 | MARKLESS_FIVE | 60/60 | 0.3972 | 0.3000 | 0.4333 | 0.5833 | 0.3833 | 0.4467 |
| aiops2022 | MARGINAL_REPEAT | 60/60 | 0.4244 | 0.3333 | 0.4500 | 0.6167 | 0.4000 | 0.4733 |
| aiops2025 | BASE_FLEX | 60/60 | 0.3256 | 0.2333 | 0.4333 | 0.4833 | 0.3278 | 0.3867 |
| aiops2025 | PAIR_FLEX | 60/60 | 0.2911 | 0.2000 | 0.3833 | 0.4833 | 0.2778 | 0.3467 |
| aiops2025 | MARGINAL_FLEX | 60/60 | 0.3681 | 0.3000 | 0.4500 | 0.4667 | 0.3778 | 0.4133 |
| aiops2025 | BASE_FIVE | 59/60 | 0.3218 | 0.2373 | 0.4068 | 0.4915 | 0.3107 | 0.3763 |
| aiops2025 | PAIR_FIVE | 60/60 | 0.3086 | 0.2167 | 0.4000 | 0.5000 | 0.2944 | 0.3667 |
| aiops2025 | MARGINAL_FIVE | 60/60 | 0.3708 | 0.3000 | 0.4500 | 0.4667 | 0.3833 | 0.4167 |
| aiops2025 | MARKLESS_FIVE | 60/60 | 0.3625 | 0.3000 | 0.4333 | 0.4500 | 0.3722 | 0.4033 |
| aiops2025 | MARGINAL_REPEAT | 60/60 | 0.3708 | 0.3000 | 0.4500 | 0.4667 | 0.3833 | 0.4167 |
| aegislab | BASE_FLEX | 100/100 | 0.5777 | 0.4500 | 0.6900 | 0.7800 | 0.5833 | 0.6560 |
| aegislab | PAIR_FLEX | 100/100 | 0.5910 | 0.4700 | 0.7000 | 0.7700 | 0.6033 | 0.6640 |
| aegislab | MARGINAL_FLEX | 99/100 | 0.5943 | 0.5051 | 0.7071 | 0.7273 | 0.6061 | 0.6545 |
| aegislab | BASE_FIVE | 100/100 | 0.5747 | 0.4300 | 0.7000 | 0.8200 | 0.5733 | 0.6640 |
| aegislab | PAIR_FIVE | 100/100 | 0.5993 | 0.4600 | 0.7100 | 0.8500 | 0.5933 | 0.6800 |
| aegislab | MARGINAL_FIVE | 100/100 | 0.6322 | 0.5200 | 0.7300 | 0.8200 | 0.6333 | 0.7000 |
| aegislab | MARKLESS_FIVE | 100/100 | 0.6360 | 0.5300 | 0.7300 | 0.8200 | 0.6333 | 0.7020 |
| aegislab | MARGINAL_REPEAT | 100/100 | 0.6313 | 0.5200 | 0.7200 | 0.8200 | 0.6300 | 0.6980 |

| 三数据集等权宏平均 | MRR | AC@1 | AC@3 | AC@5 | AVG@3 | AVG@5 |
|---|---|---|---|---|---|---|
| BASE_FLEX | 0.4015 | 0.2944 | 0.5133 | 0.5656 | 0.4111 | 0.4698 |
| PAIR_FLEX | 0.3964 | 0.2956 | 0.5000 | 0.5622 | 0.4011 | 0.4591 |
| MARGINAL_FLEX | 0.4450 | 0.3684 | 0.5301 | 0.5591 | 0.4539 | 0.4948 |
| BASE_FIVE | 0.4134 | 0.3002 | 0.5134 | 0.6150 | 0.4095 | 0.4823 |
| PAIR_FIVE | 0.4090 | 0.2978 | 0.5089 | 0.6167 | 0.4015 | 0.4767 |
| MARGINAL_FIVE | 0.4772 | 0.3844 | 0.5489 | 0.6344 | 0.4759 | 0.5322 |
| MARKLESS_FIVE | 0.4652 | 0.3767 | 0.5322 | 0.6178 | 0.4630 | 0.5173 |
| MARGINAL_REPEAT | 0.4755 | 0.3844 | 0.5400 | 0.6344 | 0.4711 | 0.5293 |

![MRR分数据集](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/mrr_by_dataset.png)

[完整绝对指标与成本CSV](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/absolute_metrics.csv)；[逐病例完整评分](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/case_metrics.csv)。

**4. 预注册主要推断与采用决定**

双侧Pratt-zero Wilcoxon、逐差round12、配对dz；四项主要比较构成病例层同一Holm族，事件组层另一个相同四项族。事件组先在dataset/event内平均病例差，再对事件组等权检验。220病例属于193个冻结事件组，AIOPS120例属于93组；BASE_FIVE超时所在单例组使该比较仅92组可用。没有CI。下述缺失结果界限仅对未知分数取[0,1]端点，不是统计置信区间。

**病例层主要比较**

| 范围/比较 | n | ΔMRR | p | Holm p | dz | 改善/变差/相同 |
|---|---|---|---|---|---|---|
| all / MARGINAL_FIVE − PAIR_FIVE | 220 | +0.0617 | 0.1620 | 0.5326 | 0.1568 | 52/43/125 |
| all / MARGINAL_FIVE − MARKLESS_FIVE | 220 | +0.0091 | 0.1332 | 0.5326 | 0.0914 | 8/3/209 |
| aiops / MARGINAL_FIVE − BASE_FIVE | 119 | +0.0702 | 0.2302 | 0.5326 | 0.1672 | 29/22/68 |
| aegislab / MARGINAL_FIVE − BASE_FIVE | 100 | +0.0575 | 0.4627 | 0.5326 | 0.1357 | 26/24/50 |

**事件组层主要比较**

| 范围/比较 | n | ΔMRR | p | Holm p | dz | 改善/变差/相同 |
|---|---|---|---|---|---|---|
| all / MARGINAL_FIVE − PAIR_FIVE | 193 | +0.0542 | 0.2941 | 0.8824 | 0.1416 | 48/43/102 |
| all / MARGINAL_FIVE − MARKLESS_FIVE | 193 | +0.0041 | 0.2108 | 0.8432 | 0.0542 | 7/3/183 |
| aiops / MARGINAL_FIVE − BASE_FIVE | 92 | +0.0629 | 0.3189 | 0.8824 | 0.1580 | 24/19/49 |
| aegislab / MARGINAL_FIVE − BASE_FIVE | 100 | +0.0575 | 0.4627 | 0.8824 | 0.1357 | 26/24/50 |

| 主比较范围 | 全注册病例差界限 | 全注册事件组差界限 |
|---|---|---|
| all {'MARGINAL_FIVE': 1, 'PAIR_FIVE': -1} | [0.061742, 0.061742] | [0.05423, 0.05423] |
| all {'MARGINAL_FIVE': 1, 'MARKLESS_FIVE': -1} | [0.009091, 0.009091] | [0.004145, 0.004145] |
| aiops {'BASE_FIVE': -1, 'MARGINAL_FIVE': 1} | [0.06125, 0.069583] | [0.051461, 0.062213] |
| aegislab {'BASE_FIVE': -1, 'MARGINAL_FIVE': 1} | [0.0575, 0.0575] | [0.0575, 0.0575] |

同事实文本比较正向52例、负向43例、相同125例，dz=.1568；Aegis对基础文本26例改善、24例变差。正均值不是大多数病例普遍受益，少量由零分到第一的幅度可以拉高MRR。事件组结果同样未显著；不能选择未校正p或只选正向故障类型宣称通过。

采用门槛逐项结论：四项主要方向均正，预设+.02同事实、+.03 AIOPS、+.02 Aegis的点估计阈值均达到，三个数据集分别对两个文本控制MRR均正；**四项病例/事件组校正显著性均失败**。覆盖护栏见下表，AIOPS-2025对两文本控制与Aegis对PAIR均负。已知配对成本通过，但AIOPS-2025一个BASE_FIVE超时使完整预算未被完全实测验证。任何必要条件失败已足以否决采用，无需事后放宽阈值。

| 数据集 | 控制 | 配对n | ΔAC@5 | 全注册界限 | 覆盖护栏 |
|---|---|---|---|---|---|
| aiops2022 | BASE_FIVE | 60 | +0.0833 | [0.083333, 0.083333] | 通过 |
| aiops2022 | PAIR_FIVE | 60 | +0.1167 | [0.116667, 0.116667] | 通过 |
| aiops2025 | BASE_FIVE | 59 | -0.0169 | [-0.033333, -0.016667] | 失败 |
| aiops2025 | PAIR_FIVE | 60 | -0.0333 | [-0.033333, -0.033333] | 失败 |
| aegislab | BASE_FIVE | 100 | +0.0000 | [0.0, 0.0] | 通过 |
| aegislab | PAIR_FIVE | 100 | -0.0300 | [-0.03, -0.03] | 失败 |

全部八臂共同完整218例的敏感性结果仍不通过：同事实ΔMRR+.0577、去点Δ+.0092，AIOPS对BASE+.0702、Aegis+.0480；主要病例Holm p在.5327—.5962，组层在.8434—.9567。共同病例是敏感性分析，不替代各注册比较自身分母。[共同完整病例](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/common_complete.json)；[逐项采用门槛](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/adoption_gates.json)。

**5. 固定五候选改变了什么，数据点又贡献了多少**

下面七项MRR属于预注册次要Holm族；AC@5对同七项单独校正，不能混用两个校正族或将次要结果改称主要成功。

**次要MRR**

| 比较 | 配对n | Δ | 病例pH | 组层n | 组层Δ | 组层pH | 病例dz |
|---|---|---|---|---|---|---|---|
| {'BASE_FIVE': 1, 'BASE_FLEX': -1} | 219 | +0.0078 | 1.00000 | 192 | +0.0022 | 1.00000 | 0.0322 |
| {'PAIR_FIVE': 1, 'PAIR_FLEX': -1} | 220 | +0.0119 | 0.22734 | 193 | +0.0115 | 0.23592 | 0.0696 |
| {'MARGINAL_FIVE': 1, 'MARGINAL_FLEX': -1} | 219 | +0.0315 | 0.01726 | 192 | +0.0266 | 0.04001 | 0.1704 |
| {'MARGINAL_FLEX': 1, 'PAIR_FLEX': -1} | 219 | +0.0379 | 1.00000 | 192 | +0.0342 | 1.00000 | 0.0918 |
| {'BASE_FLEX': -1, 'PAIR_FLEX': 1} | 220 | -0.0018 | 1.00000 | 193 | -0.0038 | 1.00000 | -0.0084 |
| {'MARGINAL_FIVE': -1, 'MARGINAL_REPEAT': 1} | 220 | -0.0015 | 0.78650 | 193 | -0.0011 | 0.78650 | -0.0854 |
| {'MARGINAL_FIVE': 1, 'MARGINAL_FLEX': -1, 'PAIR_FIVE': -1, 'PAIR_FLEX': 1} | 219 | +0.0196 | 1.00000 | 192 | +0.0151 | 1.00000 | 0.0755 |

**次要AC@5**

| 比较 | 配对n | Δ | 病例pH | 组层n | 组层Δ | 组层pH | 病例dz |
|---|---|---|---|---|---|---|---|
| {'BASE_FIVE': 1, 'BASE_FLEX': -1} | 219 | +0.0457 | 0.16503 | 192 | +0.0310 | 0.18357 | 0.1453 |
| {'PAIR_FIVE': 1, 'PAIR_FLEX': -1} | 220 | +0.0591 | 0.01716 | 193 | +0.0553 | 0.01806 | 0.2048 |
| {'MARGINAL_FIVE': 1, 'MARGINAL_FLEX': -1} | 219 | +0.0776 | 0.00067 | 192 | +0.0735 | 0.00107 | 0.2726 |
| {'MARGINAL_FLEX': 1, 'PAIR_FLEX': -1} | 219 | -0.0137 | 1.00000 | 192 | -0.0315 | 1.00000 | -0.0278 |
| {'BASE_FLEX': -1, 'PAIR_FLEX': 1} | 220 | -0.0045 | 1.00000 | 193 | -0.0093 | 1.00000 | -0.0140 |
| {'MARGINAL_FIVE': -1, 'MARGINAL_REPEAT': 1} | 220 | +0.0000 | 1.00000 | 193 | +0.0000 | 1.00000 | — |
| {'MARGINAL_FIVE': 1, 'MARGINAL_FLEX': -1, 'PAIR_FIVE': -1, 'PAIR_FLEX': 1} | 219 | +0.0183 | 1.00000 | 192 | +0.0180 | 1.00000 | 0.0463 |

`MARGINAL_FIVE−MARGINAL_FLEX` MRR **+.0315**，病例pH=.0173、事件组pH=.0400；AC@5 **+.0776**，pH=.000673/.001073，18例修复、1例破坏。PAIR固定五的AC@5 **+.0591**亦通过次要校正，BASE的+.0457没有通过。固定五的效果不是零成本尾部补齐：schema/说明会影响整个列表与理由，BASE_FIVE在Aegis MRR−.0030、AIOPS-2025配对−.0093，不能声称所有文本或所有数据集MRR都改善。

输出容量与边际表示的交互MRR **+.0196**，两层pH均1；不能证明固定五特异性增强图形推理。MARGINAL_FLEX对PAIR_FLEX配对+.0379不显著，PAIR_FLEX对BASE_FLEX−.0018不显著。由此不能把图的整体差归因于新增连续数值或输出schema某个内部机制。

真实数据点对markless仅11例MRR变化：8改善、3变差。AIOPS-2022+.0314（4改善/0变差/56相同）；AIOPS-2025+.0083（1/0/59）；Aegis **−.0038**（3/3/94）。Aegis markless MRR .6360甚至略高于完整图 .6322，Top-1也为53%对52%。所以大部分图对文本的均值优势在无数据点控制中已经出现，不能声称连续点形状/分布关系解释了增益。可能涉及相同的标签、范围、操作重新显著化、图片输入路径或模型注意分配；本设计没有分开识别这些候选解释，不能挑一个当已证实原因。

markless仍携带观测范围等信息，受控删除只检验数据点增量，并不证明“图片完全无用”。同样，不显著不等于严格零效果或充分功效下的等效证明。它足以说明本轮没有满足预先要求的可分离视觉贡献。

| 数据集 | MARGINAL_FIVE vs MARKLESS：相同MRR | 相同完整候选列表 |
|---|---|---|
| aiops2022 | 56/60 | 52/60 |
| aiops2025 | 59/60 | 48/60 |
| aegislab | 94/100 | 71/100 |

**6. 为什么MRR上升，Top-5仍下降：分数据集机制**

| 数据集 | 对PAIR_FIVE ΔMRR | MRR改善/变差/相同 | Top-1修复/破坏 | Top-5修复/破坏 |
|---|---|---|---|---|
| aiops2022 | +0.1094 | 18/11/31 | 12/5 | 11/4 |
| aiops2025 | +0.0622 | 12/9/39 | 8/3 | 4/6 |
| aegislab | +0.0328 | 22/23/55 | 17/11 | 5/8 |

AIOPS-2022是最明确的正点估计来源：对PAIR MRR+.1094，Top-1+11.67pp、Top-5+11.67pp；对BASE MRR+.0847。FIVE对原边际图MRR+.0558、Top-5+13.33pp，9修复/1破坏。说明短列表确实排掉了一部分可命中候选，但并非所有修复可归因于点图；markless已完成绝大部分相同改判。

AIOPS-2025对PAIR MRR+.0622、Top-1+8.33pp，却Top-5−3.33pp（4修复/6破坏）。与原边际FLEX相比，固定五MRR仅+.0028、Top-5完全不变；输出变长没有把被错误服务/节点竞争排出的根因带回来。实际边际FIVE只有46.67% Top-5，比PAIR_FIVE50%更低。仍有服务症状、基础设施变化、pod绑定之间的错误竞争。

AegisLab对PAIR MRR+.0328、Top-1+6pp，Top-5−3pp（5修复/8破坏）；MRR改善22例、变差23例，平均由幅度而非更多胜例支撑。对BASE MRR+.0575、Top-1+9pp、Top-5持平82%。与本轮原边际FLEX相比，固定五MRR+.0342、Top-5+9.09pp（99配对，9修复/0破坏）：短列表损失被修复了一部分，但PAIR_FIVE已达到85%覆盖，完整图仍只有82%，剩余3pp不可能仅用“尚未要求五个候选”解释。固定五解决了列表长度，未解决错误候选挤占和受害服务混淆。

一个错误第一名改成正确第一名会贡献+1；一个原第五名命中被遗漏只损失.2。因此数次首位修复可抵消更多低位遗漏，产生更高MRR与更差Top-5。必须同时报告两轴，而不是因MRR均值变高就称没有退化。

![排名分布](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/rank_distribution.png)

[全部修复/破坏计数](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/repair_break.json)；[固定五对FLEX列表变化](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/output_capacity_descriptive.json)。

**7. 故障类型、粒度与关系适用边界**

以下是离线标签分组后的描述性探索，许多故障只有1—6例，没有预注册分组显著性结论，不可据此做gold路由或删除下降病例。每行固定五的PAIR/完整图/markless均保留模型失败零分；完整每故障、每粒度、每适用组的六指标与成本见CSV。

| 数据集 | 故障 | n | PAIR MRR | MARGINAL MRR | MARKLESS MRR | MARGINAL−PAIR |
|---|---|---|---|---|---|---|
| aiops2022 | k8s容器cpu负载 | 6 | 0.1528 | 0.8056 | 0.8056 | +0.6528 |
| aiops2022 | k8s容器内存负载 | 6 | 0.1444 | 0.4000 | 0.2333 | +0.2556 |
| aiops2022 | k8s容器写io负载 | 2 | 0.7500 | 0.6250 | 0.6250 | -0.1250 |
| aiops2022 | k8s容器网络丢包 | 4 | 0.4375 | 0.4375 | 0.3750 | +0.0000 |
| aiops2022 | k8s容器网络延迟 | 6 | 0.2556 | 0.3667 | 0.3667 | +0.1111 |
| aiops2022 | k8s容器网络资源包损坏 | 6 | 0.4583 | 0.4500 | 0.3667 | -0.0083 |
| aiops2022 | k8s容器网络资源包重复发送 | 4 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| aiops2022 | k8s容器读io负载 | 3 | 0.5000 | 0.3333 | 0.3333 | -0.1667 |
| aiops2022 | k8s容器进程中止 | 4 | 0.5833 | 0.4583 | 0.4250 | -0.1250 |
| aiops2022 | node 内存消耗 | 2 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| aiops2022 | node 磁盘写IO消耗 | 5 | 0.3000 | 0.6000 | 0.6000 | +0.3000 |
| aiops2022 | node 磁盘空间消耗 | 4 | 0.8750 | 0.8125 | 0.8125 | -0.0625 |
| aiops2022 | node 磁盘读IO消耗 | 3 | 0.3333 | 0.3333 | 0.3333 | +0.0000 |
| aiops2022 | node节点CPU故障 | 2 | 0.0000 | 0.2500 | 0.2500 | +0.2500 |
| aiops2022 | node节点CPU爬升 | 3 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| aiops2025 | code error | 1 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| aiops2025 | cpu stress | 6 | 0.5472 | 0.5833 | 0.5833 | +0.0361 |
| aiops2025 | dns error | 3 | 0.1500 | 0.0000 | 0.0000 | -0.1500 |
| aiops2025 | io fault | 4 | 0.5000 | 0.5625 | 0.4375 | +0.0625 |
| aiops2025 | jvm cpu | 3 | 0.7778 | 1.0000 | 1.0000 | +0.2222 |
| aiops2025 | jvm exception | 1 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| aiops2025 | jvm gc | 2 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| aiops2025 | jvm latency | 3 | 0.3333 | 0.6667 | 0.6667 | +0.3333 |
| aiops2025 | memory stress | 5 | 0.1333 | 0.1000 | 0.1000 | -0.0333 |
| aiops2025 | network corrupt | 5 | 0.5333 | 0.9000 | 0.9000 | +0.3667 |
| aiops2025 | network delay | 2 | 0.6667 | 0.3333 | 0.3333 | -0.3333 |
| aiops2025 | network loss | 2 | 1.0000 | 1.0000 | 1.0000 | +0.0000 |
| aiops2025 | node cpu stress | 3 | 0.0833 | 0.1667 | 0.1667 | +0.0833 |
| aiops2025 | node disk fill | 1 | 1.0000 | 1.0000 | 1.0000 | +0.0000 |
| aiops2025 | node memory stress | 5 | 0.0400 | 0.2000 | 0.2000 | +0.1600 |
| aiops2025 | pod failure | 11 | 0.0909 | 0.1212 | 0.1212 | +0.0303 |
| aiops2025 | target port misconfig | 3 | 0.1111 | 0.0000 | 0.0000 | -0.1111 |
| aegislab | ContainerKill | 8 | 0.7812 | 0.9375 | 0.9375 | +0.1562 |
| aegislab | HTTPRequestAbort | 6 | 0.4500 | 0.1528 | 0.0972 | -0.2972 |
| aegislab | HTTPRequestDelay | 7 | 0.4690 | 0.5595 | 0.5595 | +0.0905 |
| aegislab | HTTPRequestReplaceMethod | 15 | 0.5022 | 0.5711 | 0.5711 | +0.0689 |
| aegislab | HTTPRequestReplacePath | 1 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| aegislab | HTTPResponseAbort | 3 | 0.0667 | 0.0000 | 0.0833 | -0.0667 |
| aegislab | HTTPResponseDelay | 7 | 0.7024 | 0.6786 | 0.6786 | -0.0238 |
| aegislab | HTTPResponseReplaceBody | 2 | 0.6000 | 0.1000 | 0.0000 | -0.5000 |
| aegislab | HTTPResponseReplaceCode | 13 | 0.4410 | 0.3808 | 0.3679 | -0.0603 |
| aegislab | JVMException | 3 | 0.8333 | 1.0000 | 1.0000 | +0.1667 |
| aegislab | JVMLatency | 1 | 0.0000 | 1.0000 | 1.0000 | +1.0000 |
| aegislab | JVMMemoryStress | 14 | 0.9286 | 0.9464 | 0.9464 | +0.0179 |
| aegislab | JVMReturn | 2 | 0.5000 | 0.5000 | 0.5000 | +0.0000 |
| aegislab | NetworkBandwidth | 2 | 0.6667 | 1.0000 | 1.0000 | +0.3333 |
| aegislab | NetworkCorrupt | 3 | 0.7778 | 1.0000 | 1.0000 | +0.2222 |
| aegislab | NetworkDelay | 1 | 1.0000 | 1.0000 | 1.0000 | +0.0000 |
| aegislab | NetworkLoss | 3 | 0.6111 | 0.5000 | 0.6111 | -0.1111 |
| aegislab | NetworkPartition | 6 | 0.4361 | 0.7778 | 0.7778 | +0.3417 |
| aegislab | PodFailure | 2 | 0.7500 | 0.7500 | 0.7500 | +0.0000 |
| aegislab | PodKill | 1 | 1.0000 | 0.5000 | 1.0000 | -0.5000 |

AIOPS-2022的主要均值正贡献集中在容器CPU、容器内存与节点写IO；读IO、进程中止、部分磁盘空间病例负向。AIOPS-2025的network corrupt和JVM latency正向，DNS、network delay、target-port配置负向。Aegis的ContainerKill、NetworkPartition有正向点估计，但HTTPRequestAbort、HTTPResponseReplaceBody、HTTPResponseReplaceCode等受损；延迟分布不能覆盖协议/代码/资源故障的全部判别证据，不能把高耗时组件自动当源。

选中关系达到scorer粒度兼容根因覆盖的病例只有A22 **24/60**、A25 **18/60**、Aegis **41/100**，尽管适用关系有211/220。可构造配对图不等于图选中了根因。在Aegis覆盖根因与未覆盖分组，图对PAIR的MRR差分别+.0667和+.0093；这是标签事后分组而非因果中介检验，也不是安全运行时路由器。图对文本的一些修复来自基础M/R/L/G，而不是配对端点里包含根因。

无关系9例始终保留，FIVE内容臂精确引用，不把这些零差解释为图形观测；repeat是真实调用。在适用211例内单独描述不改变完整220注册结论。

**评分标签粒度分组（描述性；混合组由多个可接受标签构成）**

| 数据集 | 标签粒度 | Arm | 已知n | MRR | AC@5 |
|---|---|---|---|---|---|
| aiops2022 | ['node'] | BASE_FIVE | 19 | 0.3368 | 0.4737 |
| aiops2022 | ['node'] | PAIR_FIVE | 19 | 0.3158 | 0.3684 |
| aiops2022 | ['node'] | MARGINAL_FIVE | 19 | 0.4079 | 0.4737 |
| aiops2022 | ['pod'] | BASE_FIVE | 23 | 0.2442 | 0.4348 |
| aiops2022 | ['pod'] | PAIR_FIVE | 23 | 0.2500 | 0.4783 |
| aiops2022 | ['pod'] | MARGINAL_FIVE | 23 | 0.4630 | 0.6957 |
| aiops2022 | ['service'] | BASE_FIVE | 18 | 0.4787 | 0.7222 |
| aiops2022 | ['service'] | PAIR_FIVE | 18 | 0.4111 | 0.6667 |
| aiops2022 | ['service'] | MARGINAL_FIVE | 18 | 0.4065 | 0.6667 |
| aiops2025 | ['node'] | BASE_FIVE | 9 | 0.1611 | 0.3333 |
| aiops2025 | ['node'] | PAIR_FIVE | 9 | 0.1611 | 0.3333 |
| aiops2025 | ['node'] | MARGINAL_FIVE | 9 | 0.2778 | 0.3333 |
| aiops2025 | ['pod', 'service'] | BASE_FIVE | 16 | 0.3073 | 0.4375 |
| aiops2025 | ['pod', 'service'] | PAIR_FIVE | 17 | 0.2735 | 0.5294 |
| aiops2025 | ['pod', 'service'] | MARGINAL_FIVE | 17 | 0.2353 | 0.2941 |
| aiops2025 | ['service'] | BASE_FIVE | 34 | 0.3711 | 0.5588 |
| aiops2025 | ['service'] | PAIR_FIVE | 34 | 0.3652 | 0.5294 |
| aiops2025 | ['service'] | MARGINAL_FIVE | 34 | 0.4632 | 0.5882 |
| aegislab | ['service'] | BASE_FIVE | 100 | 0.5747 | 0.8200 |
| aegislab | ['service'] | PAIR_FIVE | 100 | 0.5993 | 0.8500 |
| aegislab | ['service'] | MARGINAL_FIVE | 100 | 0.6322 | 0.8200 |

AIOPS-2022的正均值主要来自pod组（图.4630对PAIR.2500），service组略负（.4065对.4111）。AIOPS-2025的pod/service混合接受标签组17例中，图MRR.2353低于PAIR.2735，Top-5更从52.94%降至29.41%（9命中降至5）；纯service组34例则MRR.4632高于.3652。混合组的退化足以抵消纯service组部分覆盖提升，说明固定五并未统一修复所有粒度的实体竞争。标签分组不等于归因已经识别，也不能据此在部署时访问gold选择视觉。

[完整故障/粒度/适用表](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/strata.csv)；[关系根因覆盖与下降关系分组](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/mechanism_subgroups_descriptive.json)；[公共关系/离线覆盖索引](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/packet_features.json)。

**8. 成本、输出合规与实际效率**

下表是每已知位置平均token和请求墙钟。input已包括image tokens，不能再次加image；text是按实际processor/provider合同扣除图像预算后的记账值，不是原始字符数。引用在某arm的部署成本画像中使用其真实源调用成本，但实验总费用按call_key去重。墙钟包含服务端等待、并发请求重叠，不能当GPU忙碌时间。

| 数据集 | Arm | 已知n | text | image | input | output | 总token | 请求秒 | 平均列表长度 |
|---|---|---|---|---|---|---|---|---|---|
| all | BASE_FLEX | 220 | 19350.3 | 0.0 | 19350.3 | 183.8 | 19534.1 | 210.0 | 4.01 |
| all | PAIR_FLEX | 220 | 22020.5 | 0.0 | 22020.5 | 191.4 | 22211.9 | 211.4 | 3.90 |
| all | MARGINAL_FLEX | 219 | 22014.8 | 841.0 | 22855.7 | 216.2 | 23071.9 | 218.7 | 3.77 |
| all | BASE_FIVE | 219 | 19409.2 | 0.0 | 19409.2 | 185.5 | 19594.7 | 209.7 | 5.00 |
| all | PAIR_FIVE | 220 | 22068.5 | 0.0 | 22068.5 | 193.7 | 22262.2 | 212.3 | 5.00 |
| all | MARGINAL_FIVE | 220 | 22068.5 | 841.1 | 22909.6 | 218.0 | 23127.6 | 219.1 | 5.00 |
| all | MARKLESS_FIVE | 220 | 22068.5 | 841.1 | 22909.6 | 214.1 | 23123.8 | 216.6 | 5.00 |
| all | MARGINAL_REPEAT | 220 | 22068.5 | 841.1 | 22909.6 | 219.7 | 23129.3 | 218.0 | 5.00 |
| aiops2022 | BASE_FLEX | 60 | 20204.2 | 0.0 | 20204.2 | 189.9 | 20394.0 | 211.5 | 4.02 |
| aiops2022 | PAIR_FLEX | 60 | 22445.9 | 0.0 | 22445.9 | 189.8 | 22635.7 | 210.0 | 3.95 |
| aiops2022 | MARGINAL_FLEX | 60 | 22445.9 | 877.0 | 23322.9 | 224.8 | 23547.8 | 219.4 | 3.95 |
| aiops2022 | BASE_FIVE | 60 | 20252.2 | 0.0 | 20252.2 | 187.2 | 20439.4 | 208.9 | 5.00 |
| aiops2022 | PAIR_FIVE | 60 | 22493.9 | 0.0 | 22493.9 | 201.8 | 22695.8 | 216.5 | 5.00 |
| aiops2022 | MARGINAL_FIVE | 60 | 22493.9 | 877.0 | 23370.9 | 229.0 | 23600.0 | 220.6 | 5.00 |
| aiops2022 | MARKLESS_FIVE | 60 | 22493.9 | 877.0 | 23370.9 | 219.7 | 23590.6 | 221.6 | 5.00 |
| aiops2022 | MARGINAL_REPEAT | 60 | 22493.9 | 877.0 | 23370.9 | 230.2 | 23601.1 | 223.1 | 5.00 |
| aiops2025 | BASE_FLEX | 60 | 16759.0 | 0.0 | 16759.0 | 179.3 | 16938.3 | 208.4 | 3.92 |
| aiops2025 | PAIR_FLEX | 60 | 19097.7 | 0.0 | 19097.7 | 179.6 | 19277.2 | 207.3 | 3.72 |
| aiops2025 | MARGINAL_FLEX | 60 | 19097.7 | 803.9 | 19901.6 | 221.6 | 20123.2 | 219.6 | 3.80 |
| aiops2025 | BASE_FIVE | 59 | 16803.6 | 0.0 | 16803.6 | 194.3 | 16997.9 | 210.2 | 5.00 |
| aiops2025 | PAIR_FIVE | 60 | 19145.7 | 0.0 | 19145.7 | 188.6 | 19334.2 | 208.6 | 5.00 |
| aiops2025 | MARGINAL_FIVE | 60 | 19145.7 | 803.9 | 19949.6 | 227.8 | 20177.3 | 220.3 | 5.00 |
| aiops2025 | MARKLESS_FIVE | 60 | 19145.7 | 803.9 | 19949.6 | 216.2 | 20165.8 | 215.9 | 5.00 |
| aiops2025 | MARGINAL_REPEAT | 60 | 19145.7 | 803.9 | 19949.6 | 228.3 | 20177.9 | 217.7 | 5.00 |
| aegislab | BASE_FLEX | 100 | 20392.8 | 0.0 | 20392.8 | 182.8 | 20575.6 | 210.1 | 4.06 |
| aegislab | PAIR_FLEX | 100 | 23518.9 | 0.0 | 23518.9 | 199.5 | 23718.4 | 214.6 | 3.98 |
| aegislab | MARGINAL_FLEX | 99 | 23521.4 | 841.6 | 24363.0 | 207.6 | 24570.6 | 217.8 | 3.64 |
| aegislab | BASE_FIVE | 100 | 20440.8 | 0.0 | 20440.8 | 179.2 | 20620.0 | 209.8 | 5.00 |
| aegislab | PAIR_FIVE | 100 | 23566.9 | 0.0 | 23566.9 | 192.0 | 23758.9 | 212.0 | 5.00 |
| aegislab | MARGINAL_FIVE | 100 | 23566.9 | 841.9 | 24408.8 | 205.6 | 24614.5 | 217.5 | 5.00 |
| aegislab | MARKLESS_FIVE | 100 | 23566.9 | 841.9 | 24408.8 | 209.6 | 24618.4 | 214.0 | 5.00 |
| aegislab | MARGINAL_REPEAT | 100 | 23566.9 | 841.9 | 24408.8 | 208.3 | 24617.1 | 215.1 | 5.00 |

| 数据集 | 成本控制 | 配对n/注册 | MARGINAL input+output比 | 阈值 | 判定 |
|---|---|---|---|---|---|
| aiops2022 | BASE_FIVE | 60/60 | 1.1546 | 1.20 | 通过 |
| aiops2022 | PAIR_FIVE | 60/60 | 1.0398 | 1.10 | 通过 |
| aiops2025 | BASE_FIVE | 59/60 | 1.1867 | 1.20 | 已知配对通过；全量未知 |
| aiops2025 | PAIR_FIVE | 60/60 | 1.0436 | 1.10 | 通过 |
| aegislab | BASE_FIVE | 100/100 | 1.1937 | 1.20 | 通过 |
| aegislab | PAIR_FIVE | 100/100 | 1.0360 | 1.10 | 通过 |

A22视觉相对BASE总token+15.46%、相对PAIR+3.98%；A25已知配对+18.67%/+4.36%；Aegis+19.37%/+3.60%。不是降本方案。Aegis离1.20x上限较近，但未知usage仅影响A25的BASE比较。A25完整60例在未知BASE token保守取0到processor-input＋8192的记账界限下，比率 **[1.1776,1.2072]** 跨过1.20，不能把59配对通过写成60例完整预算已经验证通过。这些端点是未知结果界限，不代表真实消耗为零；未记录的usage保持未知。

真实已知正式成本 **37,926,673 tokens**：text36,838,829，image739,311，input37,578,140，output348,533。两个超时实际usage未知，已知总量不是含所有超时的精确总费用。既有smoke397,439 tokens另列，已知含资格合计38,324,112；历史RQ账本不重置、不并为新的独立观察。不报告未经计量的货币费用、能耗或GPU active time。

所有已知FIVE回答数组长度均为5，但其中8份含重复ID，全部按原规则零分；全部FLEX已知回答长度为3、4或5，FLEX schema允许1—5并不意味着观察到1/2。FLEX平均列表长度BASE4.01、PAIR3.90、MARGINAL3.77，Aegis边际FLEX仅3.64，且99份中只有12份返回5项。输出容量是可测机制线索，不能用事后填第五名、去重或救分替代真实实验。

[真实attempt账本导出](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/attempts.csv)；[唯一调用token与墙钟](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/accounting.json)；[每臂长度/错误/finish reason](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/output_compliance.json)；[完整成本未知界限](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/registered_cost_unknown_bounds.json)。

**9. 解释审查与可信度：稳定不等于正确**

按注册seed与salt，以`stable_hash([42,"rq316_reason_review_v1",case])`排序，每数据集12例，阅读36例全部八臂共288份reason。选择不依赖分数；审查是单一主reviewer、看过标签后的非盲描述性审查。12条断言另作定向源/内部一致性核验：10矛盾、1局部支持、1因果依据不足。这个定向集合不能外推为288份或全部输出的错误率；未逐项核验的单位、时钟、绑定和所有因果断言仍未知。全部阅读也不等于每句均已核实。

| 病例/Arm | 问题轴 | 结论 | 核对证据 |
|---|---|---|---|
| INC-16A4DF199613 / MARGINAL_FIVE | numeric_duration | contradicted | PAIR01 current parent quantiles=[median4.866,p95252.88]；把median当p95。 |
| INC-16A4DF199613 / MARGINAL_FIVE | duration_scope | contradicted | RequestPairPacketV1字段仅是span自身duration；没有exclusive字段。 |
| INC-C9BD40E14E88 / MARGINAL_FIVE | entity_binding | contradicted | 实际PAIR02 parent116 child434；PAIR01 parent434 child770；两条均不含534。 |
| INC-058FC5DD18AD / MARGINAL_FIVE | numeric_duration | locally_supported | current median/p95 parent2009.219/3330.080ms，child4.247/5.394ms；数量级匹配，不验证全部句子。 |
| INC-058FC5DD18AD / MARGINAL_FIVE | unsupported_causal_claim | unsupported | 一条直接child的自身duration不足以排除其他child、等待和并发；不是局部执行时间分解。 |
| INC-0ABCFE10D32D / MARGINAL_FIVE | temporal_order | contradicted | 24>20；response自身比较矛盾。 |
| INC-1B936A4C6354 / BASE_FLEX | temporal_order | contradicted | 15>14.2；内部矛盾，跨来源时间也不证明因果。 |
| INC-7CA062069501 / MARGINAL_FLEX | temporal_order | contradicted | 27>23。 |
| INC-9CE8985F3DCB / MARKLESS_FIVE | temporal_order | contradicted | 5.8>5.4。 |
| INC-7F84D3BE3772 / MARGINAL_FIVE | reason_rank_consistency | contradicted | services首位308；5900第四。 |
| INC-C83F01A1BA7F / MARGINAL_FIVE | reason_rank_consistency | contradicted | services首位3775节点；解释所支持实体655列第二。 |
| INC-7CA062069501 / MARGINAL_REPEAT | reason_rank_consistency | contradicted | services首位353，477第二；两个都是接受标签，MRR不能捕捉这个矛盾。 |

三个代表性现象：

- `INC-16A4DF199613`：边际图和markless都把正确42751升到第一，但理由把parent median4.866ms称p95≈4.9ms，真实p95是252.88ms，还把child自身duration称exclusive。正确排名可以伴随错误数值和作用域。
- `INC-C9BD40E14E88`：图和markless都修复534第一；图理由称PAIR02是434→534，而公共数据实际为116→434，另一个是434→770。这个修复不能作为模型正确读懂图绑定的证明。
- `INC-7F84D3BE3772`：强文本根因5900第一，图和markless均降至第四；图理由却明说5900是基础设施起因，services首位仍308。失败路径是证据、理由与最终排序没有一致收束，不是列表没有五个位置。

重复的全部220份调用key独立。MRR218/220相同，完整services204/220相同，回答全文仅53/220相同：A22为59/60、56/60、11/60；A25为60/60、57/60、20/60；Aegis为99/100、91/100、22/100。repeat MRR只比预选−.0015，不支持择优替换；近确定性排名不代表解释已可靠。输出confidence措辞另外保存，未当概率校准或grounding分数。

| 合并Arm | 已知n | 自报high | high但Top-1错误 | high但MRR零 |
|---|---|---|---|---|
| BASE_FLEX | 220 | 178 | 113 | 62 |
| PAIR_FLEX | 220 | 178 | 113 | 59 |
| MARGINAL_FLEX | 219 | 93 | 45 | 29 |
| BASE_FIVE | 219 | 171 | 109 | 57 |
| PAIR_FIVE | 220 | 175 | 108 | 51 |
| MARGINAL_FIVE | 220 | 97 | 42 | 23 |
| MARKLESS_FIVE | 220 | 90 | 37 | 22 |
| MARGINAL_REPEAT | 220 | 96 | 48 | 28 |

MARGINAL_FIVE的97份high中42份Top-1错误、23份MRR零；markless也有37/90份high的Top-1错误。各臂自报high比例不同，不能只比较high子集准确率就宣称置信度校准更好。这些措辞不足以替代源绑定与因果依据审查。

[36例完整理由/数据包/输出路径](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/reason_review_sample.json)；[36例阅读注释](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/manual_case_review.json)；[定向断言原文与证据](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/manual_claim_audit.json)；[重复稳定性](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/repeat_stability.json)；[confidence描述](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/confidence_descriptive.json)。

**10. 与上轮及主线的关系**

本轮三个FLEX输入与RQ3.15逐病例完全一致，图hash也一致；响应是同期交错新调用，均重新计费，不覆盖旧结果。严格共同输入历史配对：BASE_FLEX−BASE_TEXT **+.0027**（219例，211相同），PAIR_FLEX−PAIR_TEXT **+.0046**（219例，211相同），MARGINAL_FLEX−MARGINAL_VISUAL **+.0023**（217例，216相同）。所以本轮FLEX均值与历史小差主要是已知分母和少量运行波动，不能称新增算法进步。此次.5054相对旧.4692的跨轮均值差，也不能直接当视觉提升；真正输出干预效果以本轮配对FIVE−FLEX+.0315为准。

[冻结输入一致的历史配对](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/history_matched.json)。

主线仍是保留有效M/R/L/G证据，在强文本上证明一种明确且可分离的视觉比较收益，再研究压缩。RQ3.14的全窗口文本整理提供有效锚点；RQ3.15二维联合图未胜过边际对照；RQ3.16进一步发现边际图的大部分均值优势没有被数据点删除消除。结合这些结果，继续堆耗时曲线、换点布局或把markless升格新赢家都没有注册证据依据。

本轮收官动作：**停止当前边际耗时视觉候选，保存负机制证据与适用边界，不自动启动后继实验或test。** 固定五的次要正结果可作为未来输出策略的候选，但必须同时保留文本中的MRR退化、重复实体错误和成本；当前不能全项目无条件修改输出策略。未来若用户要求新计划，应先确定一种现有文本尚难完成的、与故障来源更直接相关的比较任务，并预设同事实文本/图元控制、粒度/解释一致性检查与跨数据集覆盖要求。不能仅追逐下一轮最高均值。

RQ3.16已经完成并有有效开发结论；**RQ3整体“可部署且性能、视觉贡献、成本、解释证据均成立”的目标仍未完成**。AIOPS-2022 MRR .4286、AIOPS-2025 .3708也没有达到历史提出的.60/.65目标；没有新的独立test资格或解释可信度证明。报告应将“实验执行结束”和“研究目标达成”分别陈述。

**11. 证据、复现与保护范围**

正式输入/PNG/回答/分数、准备材料、资格、冻结archive、授权及历史报告均未改写。新增内容只在离线analysis、报告、状态/findings与日志；没有模型请求、score修补、重新渲染或实验调参。分析脚本第一次因误读prompt字段名而退出，修正为原有`prompt.schema`后通过；错误仅发生于离线审计，没有修改原始prompt或source模块。

| 证据 | 位置 |
|---|---|
| 原阶段完成标记 | [原阶段完成标记](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/../formal/phase_complete.qwen3.8-27b.json) |
| 全量artifact审核 | [全量artifact审核](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/artifact_audit.json) |
| 独立Pratt/processor核对 | [独立Pratt/processor核对](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/independent_pratt_check.json) |
| 全部注册统计 | [全部注册统计](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/../formal/analysis/statistics.json) |
| 完整绝对指标 | [完整绝对指标](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/absolute_metrics.csv) |
| 逐病例全部指标 | [逐病例全部指标](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/case_metrics.csv) |
| 故障/粒度/适用全部指标 | [故障/粒度/适用全部指标](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/strata.csv) |
| 数据集探索比较 | [数据集探索比较](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/dataset_contrasts_exploratory.json) |
| 全局共同218例敏感性 | [全局共同218例敏感性](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/common_complete.json) |
| 全部理由与原响应索引 | [全部理由与原响应索引](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/response_index.json) |
| 采用决定 | [采用决定](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/adoption_gates.json) |
| 实际6张PNG阅读 | [实际6张PNG阅读](../../RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/actual_visual_review.json) |

复现（离线CPU，不发起模型调用）：

```bash
source scripts/env_local.sh
export PYTHONPATH="$PWD/src:$PWD" CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
"$CANVASRCA_PYTHON" -m RQs.RQ3_16.src.main analyze
"$CANVASRCA_PYTHON" RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/analyze.py
"$CANVASRCA_PYTHON" RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/supplement.py
"$CANVASRCA_PYTHON" RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/write_report.py
```

手工阅读注释记录的是本次已完成的review；再次运行脚本仅重建存档注释，不构成新的独立人工审核。

**附录：36个固定hash病例的八臂MRR与阅读记录**

顺序为BASE_FLEX / PAIR_FLEX / MARGINAL_FLEX / BASE_FIVE / PAIR_FIVE / MARGINAL_FIVE / MARKLESS_FIVE / REPEAT；这些是审查样本，不是另一个挑选后的性能队列。

| 数据集/病例 | 八臂MRR | 阅读要点 |
|---|---|---|
| aiops2022 / INC-BA41A280E858 | 1.0000 / 1.0000 / 0.0000 / 1.0000 / 1.0000 / 0.5000 / 0.5000 / 0.5000 | 文本把46218排首位但理由偏向5360；固定五图及markless均将根因降到第二，FLEX图完全遗漏。 |
| aiops2022 / INC-F5B2E7B7AD42 | 0.0000 / 0.0000 / 0.5000 / 0.0000 / 0.0000 / 0.5000 / 0.5000 / 0.2500 | 真实图和markless均将438排第二；重复降至第四。父子耗时被解释为局部时间，结论不随单独图元隔离。 |
| aiops2022 / INC-2CABCD159021 | 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 | 八臂均漏节点9343；图和markless都转向222，不能用答案改变证明正确机制。 |
| aiops2022 / INC-EF0D5C71C864 | 0.0000 / 1.0000 / 1.0000 / 1.0000 / 0.2000 / 1.0000 / 1.0000 / 1.0000 | 图与markless均修复598至第一；PAIR_FIVE仅第五。把一条快child当排除所有下游依据，因果断言超出配对事实。 |
| aiops2022 / INC-0ABCFE10D32D | 1.0000 / 1.0000 / 0.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 | 固定五恢复43812第一，markless相同；理由把+24说成早于+20，并颠倒pod/service关系。 |
| aiops2022 / INC-1595063C5B11 | 0.5000 / 0.0000 / 0.0000 / 0.5000 / 0.2500 / 0.2000 / 0.2000 / 0.2000 | 84394从BASE第二变成图第五，FLEX图漏掉；图和markless理由混用187/832/309实体，排名与解释不一致。 |
| aiops2022 / INC-924208910E84 | 0.0000 / 0.0000 / 1.0000 / 0.0000 / 0.0000 / 1.0000 / 1.0000 / 1.0000 | 图和markless均恢复97265第一，但理由对其owner及调用角色不一致；未独立识别数据点作用。 |
| aiops2022 / INC-16A4DF199613 | 0.0000 / 0.0000 / 1.0000 / 0.0000 / 0.2500 / 1.0000 / 1.0000 / 1.0000 | 图和markless均把42751推第一；parent中位数4.866被说成p95约4.9，child自身duration被称exclusive。 |
| aiops2022 / INC-C83F01A1BA7F | 0.5000 / 0.5000 / 1.0000 / 0.5000 / 0.5000 / 1.0000 / 1.0000 / 1.0000 | 节点3775由文本第二升到图和markless第一；理由却排除节点并指向655/90187，MRR正确仍与解释冲突。 |
| aiops2022 / INC-7F84D3BE3772 | 1.0000 / 1.0000 / 0.2500 / 1.0000 / 1.0000 / 0.2500 / 0.2500 / 0.2500 | 文本5900第一，图和markless均第四；图理由明确称5900为源但services首位308，前后不一致。 |
| aiops2022 / INC-AF990A16FDD6 | 0.5000 / 0.5000 / 0.0000 / 0.5000 / 0.5000 / 0.2500 / 0.2500 / 0.2500 | service863粒度匹配被图第五位pod部分命中；图首位358与markless所论证863不一致，所有方案未排根因第一。 |
| aiops2022 / INC-FC843F9AD625 | 0.5000 / 0.5000 / 1.0000 / 0.5000 / 0.5000 / 1.0000 / 1.0000 / 1.0000 | 8953由文本第二升到图和markless第一；文本有bin44早于32、+37早于+20的内部时序矛盾。 |
| aiops2025 / INC-7CA062069501 | 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 | 多个接受根因353/477掩盖解释分歧；FLEX理由说+27早于+23，重复声称477第一而实际353第一。 |
| aiops2025 / INC-2B5B37FB4D11 | 0.0000 / 0.0000 / 0.3333 / 0.2000 / 0.0000 / 0.3333 / 0.3333 / 0.3333 | 图和markless把285保留第三；证明223是child wait却据此坚持223为源，循环推断没有解决排名。 |
| aiops2025 / INC-50AFA840E6F8 | 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 | 八臂漏903；图首位876、markless首位815均错误，事实绑定和缺少边被当排除因果依据。 |
| aiops2025 / INC-BE6A1C89D45F | 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 | 无合格关系回退，多个臂是精确引用，不能视为独立图形观察；所有臂漏949。 |
| aiops2025 / INC-28E6F5E88478 | 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 | 八臂漏节点8202；集中于615/277业务延迟，独立源与受害症状仍混淆。 |
| aiops2025 / INC-5CE6915288DD | 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 | 八臂4882第一；若干理由把+15说成先于+14，正确排名并未消除时序错误。 |
| aiops2025 / INC-D87134FF9ACF | 0.2500 / 0.2000 / 0.0000 / 1.0000 / 0.2000 / 0.0000 / 0.0000 / 0.0000 | BASE_FIVE将380修复第一，图和markless均遗漏380/96210；把早发节点网络变化当源而丢失pod直接证据。 |
| aiops2025 / INC-B8CEA35848D0 | 0.0000 / 0.3333 / 0.0000 / 0.3333 / 0.3333 / 0.0000 / 0.0000 / 0.0000 | PAIR_FIVE粒度命中第三，图和markless遗漏262；图把+17说成在+16之前，markless理由指142而首位3430。 |
| aiops2025 / INC-AC608AECC5FD | 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 | 接受多个根因686/731使八臂MRR均1；有的理由把14 log2称60000倍，图将延迟升高描述成collapsed。 |
| aiops2025 / INC-C94A18F2915E | 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 | 八臂漏525/94304；图和markless共同转向3485，重复承认hosting边未显示，机制证据仍不足。 |
| aiops2025 / INC-1B936A4C6354 | 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 / 0.5000 / 0.5000 / 0.5000 | FLEX正确404第一，固定五图和markless均改677、404第二；文本+15早于+14.2矛盾。 |
| aiops2025 / INC-92A00B34EECF | 0.5000 / 0.5000 / 0.2500 / 0.5000 / 0.5000 / 0.2500 / 0.2500 / 0.2500 | 文本根因772第二，图和markless第四；过度依赖最早调用者927作为源，拓扑方向未证明因果。 |
| aegislab / INC-C9BD40E14E88 | 0.0000 / 0.2500 / 1.0000 / 0.0000 / 0.2500 / 1.0000 / 1.0000 / 1.0000 | 图和markless均修复534第一，但PAIR02关系是116→434，理由把它误绑为434→534；正确排名含实体错误。 |
| aegislab / INC-9CE8985F3DCB | 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 | 八臂漏440/776；markless+5.8先于+5.4矛盾，图与文本在CPU/内存受害服务之间切换。 |
| aegislab / INC-776EE000D01C | 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 | 八臂漏741/688；共同坚持最早page-fault实体329，未显示调用关系不构成排除其他根因依据。 |
| aegislab / INC-133324A21C16 | 0.5000 / 0.5000 / 0.3333 / 0.5000 / 0.5000 / 0.5000 / 0.5000 / 0.5000 | 根因544在文本第二、FLEX图第三、FIVE图及markless第二；持续磁盘增长不单独证明372为起因。 |
| aegislab / INC-B95CA78A9FA8 | 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 | 八臂147第一；资源与restart事实来自强基础文本，图元贡献未分离，部分reason将restart当纯症状而未证因果。 |
| aegislab / INC-6BD7198BE675 | 0.5000 / 0.5000 / 0.5000 / 0.5000 / 0.5000 / 0.5000 / 0.5000 / 0.5000 | 所有臂692第二，均坚持高耗时调用者946第一；输出容量没有改变根因与caller症状混淆。 |
| aegislab / INC-6A048DD0C35E | 0.3333 / 0.0000 / 1.0000 / 0.3333 / 0.3333 / 1.0000 / 1.0000 / 1.0000 | 图和markless修复807第一；FIVE图把807称+4.8早发、FLEX却称+6.2，重复另给553→807关系。 |
| aegislab / INC-058FC5DD18AD | 0.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 | PAIR_FLEX已修复905第一，FIVE图/markless没有额外排名收益；一条child快不等于完整排除下游或证明local。 |
| aegislab / INC-CEDB66058BB8 | 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 | 八臂371第一；restart与Trace直接证据存在，FIVE图与markless理由近同，无图元独立收益。 |
| aegislab / INC-9FE4614C417F | 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 | 八臂粒度匹配MRR1；图首位32402是992实例，正确匹配不代表找到全部原因或解释独立可靠。 |
| aegislab / INC-EDA7F79E3BD5 | 1.0000 / 1.0000 / 1.0000 / 0.5000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 | PAIR及图534第一，BASE_FIVE改712而退化；基本文本把+5说成早于+4.5/+4.2。 |
| aegislab / INC-3C072440A74A | 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 / 0.0000 | 八臂漏568/813；图理由提到568但services仍未列入，症状强度与最早CPU峰主导错误排名。 |
