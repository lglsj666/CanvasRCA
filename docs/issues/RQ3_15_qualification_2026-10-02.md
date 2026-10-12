# RQ3.15 实施与 CPU / GPU 资格报告

日期：2026-10-02（America/Toronto）。状态：**代码、完整 CPU、实际例图审查及 GPU smoke 均已完成；按用户指定终点停止，正式实验未启动。**

本报告属于工程与输入资格证据，不是正式实验结论。220 例仍是已暴露 eval；本次仅对固定的三个身份执行了 18 次 smoke。没有按 smoke 排名修改方法、病例、提示词、渲染或阈值。

## 1. 交付与冻结

- 已保存[用户批准计划](../experiment_plans/RQ3_15_Request_Joint_Plan_2026-10-02.md)，修正计划索引中 RQ3.14 的过期状态。
- 新建 [RQ3_15](../../RQs/RQ3_15/)：五功能模块、配置、统一启动入口、三份协议文档、原子提交、快速恢复和调用记账。功能源为 1161 个非空非注释行，低于 7,500 上限。
- `RequestPairPacketV1` 固定公开实体、操作、阶段、样本和统计定义；七个 Trace 列白名单不含 `anomal`、答案或标签。原始身份经源行/源文件哈希在审计侧可追溯，不进入新证据文本或 PNG。
- BASE_TEXT 的 system、候选及全部 WINDOW_TEXT 文本部分保留。三组内容/表示比较和六臂的[1,320 位置事实差异清单](../../RQs/RQ3_15/results/request_joint_v1/qualification/fact_differences.json)已核对。
- 在 `src/renderer/` 注册 `trace_joint.scatter` 与 `trace_joint.marginals`，共享绘图基础。具体缺口和注册说明见[renderer README](../../src/renderer/README.md)。只复用既有布局、外观、间距、索引和组件替换操作；未增加操作、未使用实验私有画图实现。
- 旧组件注册及旧操作保持一致；旧组件函数实现未改变。`primitives.tsx` 仅扩展 TypeScript 类型。既有折线跨缺测连线规则保持；原始数据和历史输入/图像/结果均保留。见[历史保护审计](../../RQs/RQ3_15/results/request_joint_v1/qualification/historical_protection_audit.json)。
- 当前 176 个源文件已[冻结归档](../../RQs/RQ3_15/results/request_joint_v1/qualification/source_freeze.json)，后续审查确认当前源与冻结版本相同。`full_launch_authorized=false`。

## 2. 完整适用性与回退

| 数据集 | 全部病例 | 合格病例 | 比例 | 50% 门槛 |
|---|---:|---:|---:|---|
| aiops2022 | 60 | 60 | 100.00% | 通过 |
| aiops2025 | 60 | 55 | 91.67% | 通过 |
| aegislab | 100 | 96 | 96.00% | 通过 |

211/220 例合格，每例选中两条关系，共 422 条关系及 422 张独立 PNG（两种视觉臂）；PAIR_REPEAT 复用相同 PNG，但使用真实独立模型调用。每条关系两阶段各至少 20 个请求；每阶段最多 32 个原始配对，所有选中关系都满足至少一个二值分组内有四个不同的已展示配对。

9 例完整回退：AIOPS-2025 的 5 例没有公开 Trace 行；AegisLab 的 4 例没有达到双阶段支持量的关系。它们保留在 220 例分母及 CPU 成本计算中，没有空面板、问号或缺失提示。身份与原因清单见[跨臂审核](../../RQs/RQ3_15/results/request_joint_v1/qualification/cross_arm_render_audit.json)。

具体实现选择在调用前写入协议：跨实体直接父子关系；先选请求中最长父调用，再取其最长直接子调用；重复身份、循环及进入循环的链排除。按父调用的公开相对时间分段，右端点包含；参考 p95 阈值采用严格大于。条件子耗时摘要要求每个条件组至少 5 个请求。统计分位数使用线性插值，但展示样本没有插值或补值。匿名化后操作名称发生碰撞时使用确定性序号区分。

## 3. CPU 与可视化验证

- 静态 AST / 导入 / 配置 / shell 检查、关键 Ruff 检查、TypeScript 类型检查及构建通过。统一 renderer 既有 35 项回归通过。
- 数值回归覆盖跨 Trace 同名 span、重复身份、循环、重复调用、缺失与零耗时、单位转换、窗口边界、确定性秩抽样。额外用独立 pandas 分组/连接核对最长直接子调用与完整合成配对集合，见[补充数值审核](../../RQs/RQ3_15/results/request_joint_v1/qualification/numeric_pairing_addendum.json)。
- 完整 220 例重新核对公共源哈希、身份映射、单位与公开时钟，独立 NumPy 计算核对 **341,635 个选中总体配对**的样本、分位数、二值计数及条件统计；源扫描共 46,676,512 行，不把全部源行误称为独立统计核对数。
- **422 张 PNG、58,496 个图元绑定**核对通过；两个视觉臂的共同标签位置/尺寸在全部 211 对图中一致。三固定病例两臂共 6 次重绘 PNG SHA256 完全相同。
- 实际打开了 **11 张当前例图**，覆盖三个数据集、双视觉臂、最低 20 请求支持、最大 3,610,007.149ms 观测与长操作名。[例图索引](../experiment_reports/through_RQ3_15_preserved/assets/RQs/RQ3_15/results/request_joint_v1/qualification/gallery.html)；[逐图审查记录](../../RQs/RQ3_15/results/request_joint_v1/qualification/visual_inspection.json)。坐标不裁切所选样本中的零值或极值；按父耗时秩抽样不保证展示总体每个子端极值。长名字完整换行，不显示缺失符号。
- 密集点有真实重叠，未用 jitter 伪造观测；普通病例的刻度字体偏小，完整精确值同时在文本中。当前全量没有单关系病例，不虚构此类真实例图。图中点密度不等于总体概率；这是按父耗时秩抽样的展示。
- 完整 CPU 审核耗时 **648.81 秒**；本地 checkpoint/tokenizer/processor 的 28 个文件身份通过。使用现有 infer 环境完成实际 processor 计数，CUDA 关闭，没有为 CPU 审核启动模型服务。
- 所有输入都满足上下文容量：最大 **26,093 输入 token + 8,192 输出预算 = 34,285 < 40,960**。全部基础部分完整保留，无裁切或上下文排除。
- 原子调用提交回归通过。真实 smoke 完成后，在禁止新进程和输入重建的检查下，runner 与 supervisor 都直接使用完成标记返回，账本仍为 18，未重载模型。

## 4. 输入预算

门槛应用于每个数据集的完整注册病例平均输入量，即同一分母下总量之比。CPU 采用实际 processor，不用字符估算。

| 数据集 | PAIR_VISUAL / BASE_TEXT ≤1.20 | PAIR_VISUAL / PAIR_TEXT ≤1.10 | 结果 |
|---|---:|---:|---|
| aiops2022 | 1.154363 | 1.039072 | 通过 |
| aiops2025 | 1.187519 | 1.042095 | 通过 |
| aegislab | 1.194581 | 1.035798 | 通过 |

| Arm | AIOPS-2022 平均输入 | AIOPS-2025 平均输入 | AegisLab 平均输入 |
|---|---:|---:|---:|
| BASE_TEXT | 20204.17 | 16758.95 | 20392.79 |
| BINARY_TEXT | 20561.83 | 17092.55 | 20748.74 |
| PAIR_TEXT | 22445.93 | 19097.65 | 23518.92 |
| PAIR_VISUAL | 23322.93 | 19901.57 | 24360.84 |
| MARGINAL_VISUAL | 23322.93 | 19901.57 | 24360.84 |
| PAIR_REPEAT | 23322.93 | 19901.57 | 24360.84 |

每张图实际新增 877 个 image token。两视觉臂以及真实重复使用相同尺寸和输入文本，输入 token 数一致。逐臂统计见[CPU CSV](../experiment_reports/through_RQ3_15_preserved/assets/RQs/RQ3_15/results/request_joint_v1/qualification/cpu_dataset_summary.csv)，逐病例输入见[完整 CPU 报告](../../RQs/RQ3_15/results/request_joint_v1/qualification/cpu.json)。

**成本余量有限。** AegisLab 的完整输入比 1.194581 接近 1.20；未来仍必须核对实际 input+output，CPU 通过不保证总成本采用门槛通过。固定 Aegis smoke 单例的输入比为 1.2000667；协议门槛是完整数据集平均值，并非单病例上限，因此该值未导致换病例或修改门槛。CPU smoke 只检查该固定三例的完整性与容量，继承已通过的全量预算判断。

## 5. GPU smoke 与逐份审计

- 固定身份：A22 `INC-6E627662CA32`，A25 `INC-D9245047C658`，Aegis `INC-37ABFB78A80E`；每例六臂，无挑例、无重试。
- 本地 Qwen、BF16、context 40960、8192 输出适配、temperature 1、top-p 0.95、seed 42、thinking/prefix caching 关闭，继承已登记 GDN triton 适配；实际 argv 和产物均确认 `gpu_memory_utilization=0.75`。
- **18/18 完成，203.26 秒（含服务启动），600 秒同一逻辑预算。** 无超时、截断或基础设施失败，全部 finish_reason=stop；3 次重复具有不同 call_key 和服务端 request_id，未复用历史答案。
- 全部持久化文本/system/schema/PNG 与冻结准备一致，逻辑请求哈希与产物 envelope 哈希分别按其定义校验；provider prompt token 与 CPU 实际计数完全相同。所有输出 JSON/候选校验、canonical scorer 重算和 token 守恒通过。
- 合计 **388,615 input token（含 7,893 image token）+ 3,313 output token = 391,928 total token**。9 个请求有图；每个请求恰为一次新 generation call。
- 18 份输出理由均已阅读；完整明细见[输入/输出审查](../../RQs/RQ3_15/results/request_joint_v1/smoke/input_output_review.json)和[逐调用结果 CSV](../experiment_reports/through_RQ3_15_preserved/assets/RQs/RQ3_15/results/request_joint_v1/qualification/smoke_outcomes.csv)。已关闭自有服务，端口 21955 关闭；结束后 GPU 总占用约 3,959 MiB，启动前约 3,993 MiB，未停止其他工作负载。

以下是 smoke 的完整评分，**每数据集只有一个固定病例，不用于估计效果、显著性或决定调参**。

| 数据集 | Arm | MRR | AC@1 | AC@3 | AC@5 | AVG@3 | AVG@5 |
|---|---|---:|---:|---:|---:|---:|---:|
| aiops2022 | BASE_TEXT | 0.3333 | 0.0000 | 1.0000 | 1.0000 | 0.3333 | 0.6000 |
| aiops2022 | BINARY_TEXT | 0.3333 | 0.0000 | 1.0000 | 1.0000 | 0.3333 | 0.6000 |
| aiops2022 | PAIR_TEXT | 0.3333 | 0.0000 | 1.0000 | 1.0000 | 0.3333 | 0.6000 |
| aiops2022 | PAIR_VISUAL | 0.5000 | 0.0000 | 1.0000 | 1.0000 | 0.6667 | 0.8000 |
| aiops2022 | MARGINAL_VISUAL | 0.5000 | 0.0000 | 1.0000 | 1.0000 | 0.6667 | 0.8000 |
| aiops2022 | PAIR_REPEAT | 0.5000 | 0.0000 | 1.0000 | 1.0000 | 0.6667 | 0.8000 |
| aiops2025 | BASE_TEXT | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| aiops2025 | BINARY_TEXT | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| aiops2025 | PAIR_TEXT | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| aiops2025 | PAIR_VISUAL | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| aiops2025 | MARGINAL_VISUAL | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| aiops2025 | PAIR_REPEAT | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| aegislab | BASE_TEXT | 0.2000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.2000 |
| aegislab | BINARY_TEXT | 0.5000 | 0.0000 | 1.0000 | 1.0000 | 0.6667 | 0.8000 |
| aegislab | PAIR_TEXT | 0.5000 | 0.0000 | 1.0000 | 1.0000 | 0.6667 | 0.8000 |
| aegislab | PAIR_VISUAL | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| aegislab | MARGINAL_VISUAL | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| aegislab | PAIR_REPEAT | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## 6. 图形感知、RCA 与解释的分开判断

**工程链路通过；视觉理解与可信推理尚未建立。** 不将合法 PNG、格式正确、MRR 或口头提及 PAIR 当作图形理解证明。当前 smoke 没有独立图表问答测量，因此图形感知能力记为未验证。

- AIOPS-2025 的 PAIR_VISUAL / MARGINAL_VISUAL / PAIR_REPEAT 都把 326 排第一，但理由将 130 描述为根因，排名与解释不一致。
- Aegis 的 PAIR_REPEAT 声称 2.15e6 大于 3.66e6，存在明确数值比较错误。配对输入、源数值、坐标与单位核对通过，不能把这项模型错误改写成成功证据。
- 多个回答从同请求关联、拓扑或已有 exclusive 指标作因果与本地执行时间推断，超过新配对本身可支持的范围；尤其冻结基础文本包含历史 exclusive 证据，不能把所有解释变化单独归因于新增图。
- AIOPS-2022 的 PAIR_VISUAL 和 PAIR_REPEAT 输出完全相同，但这是两个实际独立请求。解释主要引用原有文本，不足以证明读懂了新增联合图。
- 上述问题全部原样保存；未因此改提示词、换布局、挑病例、增加调用，亦未用 smoke MRR 作为资格门槛。正式运行前后都不能自动声称可信度提高。

## 7. 修复过程与保留材料

1. 初版边际表示把两个单变量分布放进同一二维坐标，可能让固定位置被误读为耗时。调用前改为两个独立值轴与明确阶段行，两个臂继续共享样本与尺度。原预检源/图保存在 `qualification/preflight_v1/`。
2. 首轮全量准备被 unified renderer 的长操作名溢出检查拦截。保留完整文字及字号，调整图内空间，重新生成最终 220 例。原预检与失败材料保存在 `qualification/preflight_v2/`，没有模型调用。
3. 首次 CPU 命令使用 tools 环境，缺少 transformers。保留依赖失败日志，改用现有 infer 环境且关闭 CUDA；未安装或升级环境。之后全量 CPU 与固定三例 CPU 检查通过。
4. 以上修复都发生在源冻结和第一笔模型请求之前；既有预检、历史实验产物与调用账本未删改。

## 8. 当前终点与下一步

**本次授权任务完成并停止。** 正式 1,320 个位置仅登记，正式调用 0；18 次 smoke 已计账。176 文件冻结、全部资格证据、例图及报告均已保存。下一步需要用户另行指示是否启动已登记正式矩阵；当前不自动启动，也不根据三个 smoke 的排名作方法调整。

若后续正式执行，继续使用现有冻结方案和四项主要 Holm 比较；同时检查同事实强文本/边际图控制、每数据集收益、实际总 token 与解释证据。若不能超过强文本和图形控制，按预注册结束这条路线，汇总负结果和适用边界。不能以再换布局或重命名 exposed eval 延长路线。

权威终态：[final_state.json](../../RQs/RQ3_15/results/request_joint_v1/qualification/final_state.json)；[smoke 资格](../../RQs/RQ3_15/results/request_joint_v1/qualification/smoke_review.json)；[CPU 资格](../../RQs/RQ3_15/results/request_joint_v1/qualification/cpu.json)；[冻结源](../../RQs/RQ3_15/results/request_joint_v1/qualification/source_freeze.json)。
