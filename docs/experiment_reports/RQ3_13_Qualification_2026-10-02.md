# RQ3.13 资格检查与停止记录

**状态：代码部署、静态检查、完整 CPU 回归和 GPU smoke 已完成并通过；按照用户最新指令停止，未启动全量实验。** 本报告是运行资格证据，不是新方法的完整效果报告。

## 方案及权限

RQ3.12 完整分析不支持采用参考预测方案。下一轮注册原始观测变化的共同时间画布，保留 RQ3.12 v4 exact 基础事实和所有候选。计算仅使用原12条指标的真实观测与采样支持；参考包络外变化不等于故障或根因。新六臂包含原文/原文真实重复、派生状态强文本、时间图、强文本原样截图、时间图真实重复。两个重复真实独立调用，不择优。来源、算法、对照、统计和限定条件详见[计划](/home/lglsj/CanvasRCA_nibi/docs/experiment_plans/RQ3_13_Observed_Excursion_Plan_2026-10-02.md)及[冻结协议](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_13/descriptions/RQ3_13_experiments.md)。

完整140例 exposed eval（AIOPS2022/2025各60，Aegis20）不变。840个正式位置只是未来矩阵登记，本次执行授权仅到 smoke。配置 full_launch_authorized=false；执行门禁已实际验证，在读取资格或启动模型前拒绝正式运行。没有自动后续任务。

## 静态、准备及 CPU

- 五个功能模块加包标记，1144行有效源代码；AST/compile、局部导入、JSON/矩阵、bash语法、无空实现、纯公开 compiler/renderer 边界通过。共享模型配方、评分、数据划分和历史renderer保持原身份。
- 新图形实现是RQ局部的确定性Pillow适配器，位于exps.py，使用冻结字体，不修改历史renderer。8个不同物理核的CPU准备worker完成140例，生成266张独立PNG；7例空派生表回退原始文本，病例及所有臂仍保留。
- 七组回归覆盖常零参考、真实缺失分母、稀疏采样、跨split格排除、独立分位数/分类、实际像素/字节确定性、空表回退、atomic commit和两类真实重复。
- 全1680条原始指标与独立NumPy复算一致，包络最大相对差2.7755575615628914e−17。全部真实采样支持由canonical timestamp列独立核对；266张真实PNG的状态像素、事实绑定、文字盒、裁切/重叠、隐含metadata和hash检查通过。三例六PNG独立重绘字节一致。
- 140例×6臂全部使用实际模型processor计数，无容量排除；最大输入22143加输出8192为30335，小于40960。AIOPS主要范围视觉/原文输入token比1.087043，低于1.20门槛。
- 至少两不同实体有合格观测变化的病例：AIOPS2022为57/60，AIOPS2025为55/60，合计112/120，高于预注册合计30及每数据集10的门槛。这里是公开适用性，不能解释为根因覆盖或准确率。
- 官方checkpoint、tokenizer和processor的28个文件当前字节SHA核对通过。CPU完整资格141.054秒，smoke三例CPU资格7.841秒。没有CPU模型调用。
- 主agent实际查看每个数据集的图形/文字截图及5行稀疏例，共8PNG；科学、视觉及具体预算审查完成。仅一个reviewer，不声称独立评审或一致率。

资格证据：[cpu.json](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_13/results/observed_excursion_v1/qualification/cpu.json)、[cpu_smoke.json](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_13/results/observed_excursion_v1/qualification/cpu_smoke.json)、[visual_review.json](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_13/results/observed_excursion_v1/qualification/visual_review.json)。

## GPU smoke

冻结129个源/配置/运行投影/依赖/字体文件后，使用官方Qwen3.8-27B BF16本地服务、既定解码和评分，运行3个登记eval病例×6臂，18次均是真实调用。共185.152秒，含85.025秒模型加载，满足18调用/600秒累计逻辑smoke限制；没有重试、超时、基础设施或模型格式失败，18个atomic completion均完成。未按准确率筛选或调参。

实际18份input、system、policy、text和PNG与CPU合格准备逐项一致。prompt中的image_path/image_sha256按其存储格式核对真实PNG，再与input的sha256描述符比较；两种记录格式不能直接当作相同JSON比较。全部18个完整prompt/render/conversation/trajectory/output/cost/commit图谱审核通过。输出是有效JSON、唯一候选ID、1–5个排名项，评分error为空；原始评分和回答保留。

已知token为输入340414＝文字333979＋图像6435，输出3557，合计343971。全部18份usage已知；没有用token估计金额或把重叠请求时长相加当作GPU耗时。confidence为13high/5medium，仅是模型类别，不是校准概率。

证据：[artifact_review.json](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_13/results/observed_excursion_v1/smoke/artifact_review.json)、[input_output_verification.json](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_13/results/observed_excursion_v1/smoke/input_output_verification.json)、[smoke_review.json](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_13/results/observed_excursion_v1/qualification/smoke_review.json)。

## 解释审核及其限制

18份回答全文均已阅读，源核对聚焦三例的M/trace/onset绑定、派生数值与实际PNG；继承的完整基础事实及图边由机器身份/重放审核，未声称每条边或每个因果论断均已人工独立认证。

确认的反例包括：AIOPS2022回答将M07（service790/mrt）引用为pod63581的CPU证据；文字截图臂把R05当前91057.7µs写成91.1µs。AIOPS2025回答把M06/M07归到786/53618，实际分别为466/815；另一回答把130的18.4分钟称为最早，而E01保留123的15分钟、466的16分钟。Aegis回答多次把M03（495）归到364，或把M06（564）归到495；另把364的9.18称为最大exclusive log2 change，实际437为9.9、564为9.83。将公共split、最强偏差和图边解释为“verified origin”的语言也未获得因果认证。

这些是模型解释的科学局限，已原样保留，并非pipeline运输、渲染或评分失败。不同臂/重复可能同时有不同错误；没有据此换方法、选更好重复或改烟测答案。当前只通过运行资格，不宣称可信度提高、消除幻觉、新方法采用或全量效果改善。未穷尽审核的单位、顺序、图路径和因果轴保持未知，不提供幻觉率或一致率。

具体反例：[manual_input_output_review.json](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_13/results/observed_excursion_v1/smoke/manual_input_output_review.json)。

## 持久化与交接

当前source contract与冻结archive SHA、所有资格门禁再次核对通过。RQ3.13累计调用18，正式调用0；上一轮RQ3.12的811formal+18smoke＝829仍保留，未重置预算或历史结果。新版本总900 allocation包含18smoke，未来正式最多882 attempts，当前没有执行权限。

Owned runner、server及supervisor正常结束，GPU显存回落，21953端口不再有模型服务。没有新test、Gemma、attention、SFT/RL、正式队列或后台后续工作。完成记录：[completion.json](/home/lglsj/CanvasRCA_nibi/RQs/RQ3_13/results/observed_excursion_v1/qualification/completion.json)。后续若用户授权全量，需要记录新的执行权限并保持本次冻结科学输入及已花调用；本次不继续。
