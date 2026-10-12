# RQ3.11：诊断算子保护的视觉曲线压缩

2026-10-01，当前版本 protected_compression_v2。首次GPU调用前，v1 CPU表明修补过多（37,906点，视觉输入均值15,945/16,218高于强文本15,145）；据公开数值成本增加冗余补丁移除，不使用根因或模型反馈。v1计划/源码/CPU记录保留于results/protected_v1/qualification，零GPU调用。量化q与图形未变，280张已通过的PNG及DOM记录原样复用并核对哈希。

执行授权：当前用户 goal 要求完整分析后自主决定下一步，部署、静态检查、CPU 回归、GPU smoke，通过后启动全量并停止。本计划先于新模型请求冻结；仍采用单主 agent。

## 证据与选择

[RQ3.10 完整报告](../experiment_reports/RQ3_10_Qwen_Analysis_2026-10-01.md)没有支持范围矩阵部署，主要比较均不显著，视觉矩阵比基础文本总 token 增加75.1%；AIOPS-2025/Aegis 有效负面范围对照不足。RQ3.8 全图叠全文本退化，RQ3.7C 位置机制未可靠建立。故本轮不继续添加范围文字与大矩阵，不伪造候选响应预测。

[conversation_oct_01.md](../../conversation_oct_01.md)提出 Decision-Protected Visual Compression：保留有限诊断算子，允许其他数值量化误差，计入精确修补成本，设置同编码文本对照。[Glyph 原论文](https://arxiv.org/html/2510.17800v1)研究文本图像压缩，并使用 continual pretraining、渲染搜索及后训练；其训练模型的压缩效果不能直接移植给未训练 Qwen。本轮是曲线量化与有限算子保护的开发假设，不声称新颖性已证明或无损语义压缩。[CIRCA](https://arxiv.org/html/2206.05871)明确依赖因果图及其假设，本轮不建立干预分布，不使用反事实因果措辞。

## 冻结方法

输入仅取 RQ3.8 已提交 public 基础文本和12个 metric card，不读取完整 pool 或新原始遥测。保留原选定指标、实体、单位、64个相对时间 bin、缺失、既有 M/R/L/G 汇总、所有候选、原系统/求解提示和评分规则。不按已知根因选择系列或补丁。已有故障估计窗口仍是原公开信息，不能成为新增注入时刻。公开 trace split 的 window_rel_s[0]/observation duration 对应 bin 切分，只用于压缩器诊断算子，不替换原 MET-Z。

每条曲线在自身完整可见范围 [lo,hi] 均匀量化，q=round((x−lo)/(hi−lo)*(L−1))，保留原缺失。常量曲线和全缺失显式处理。解码 x_hat=lo+q/(L−1)*(hi−lo)，未观测不插值。LOW：L=8，画布800px宽；HIGH：L=32，1120px宽。两个预算都事先固定，与新分数无关。画布2列，6行，源 renderer `metric.line`，字体16，单PNG；只画粗量化曲线。完整原标题/单位/lo/hi/bin轴、原指标汇总及缺失位置在邻接文本中精确绑定 M01..M12，图面不再重复完整长指标名称。线段是连接观测点的视觉辅助，不是中间缺失值测量。

保护算子在已显示的64-bin序列上计算：有限样本/缺失集合、最早最大/最小 bin、两阶段中位数变化的方向与3倍稳健尺度阈值状态、当前阶段超过3倍尺度的最早 bin、超过阈值的持续比例是否≥0.5。至少3个有限点/阶段；scale=max(1.4826*MAD,0.01*abs(reference median))；零 scale 与样本不足是 unknown。它们是压缩器的有限签名，既不是原 MET-Z 的重新实现，也不是根因判定器。原公开 split 跨过的 bin 不用于阶段比较。

若量化解码的有限签名不同，依原样本与量化值的绝对误差从大到小（同误差按 bin 升序）添加精确原值补丁，重算至签名一致，最坏保留全部有限点；再按逆插入顺序逐个尝试移除补丁，仅在全部有限签名仍一致时接受移除。移除步骤降低冗余，不保证全局最优。不声称最少补丁，不删难样本，不用因果标签。补丁随邻接文本送入 VLM，原数值字符串精度保留；应用补丁优先于粗图。模型不接收算子签名、CPU根因排名或“已验证正确”的案例提示。补丁保证的是离线数值签名，不保证读图或 RCA 正确。报告原始误差、无补丁算子损失、修补点数和真实 tokens，成本超过文本也保留结果。

## 八臂与信息匹配

1. EXACT_TEXT：强无损紧凑文本。指标向量及缺失 mask 用可逆 value_positions/区间序列编码；原数值字符串、其他字段和全部 R/L/G 保留。
2. EXACT_REPEAT：相同输入、相同推理配方、独立实际请求；独立 replicate 身份，禁止与 EXACT_TEXT 去重或择优。
3. COARSE_VISUAL_LOW；4. COARSE_VISUAL_HIGH：粗图与精确绑定范围/元数据，但无补丁。
5. PROTECTED_TEXT_LOW；6. PROTECTED_TEXT_HIGH：量化 q 的可逆紧凑文本、同范围/缺失及精确补丁。
7. PROTECTED_VISUAL_LOW；8. PROTECTED_VISUAL_HIGH：粗图、同范围/缺失及精确补丁；q 向量只在图中，不在文本重复。

PROTECTED_VISUAL 与同预算 PROTECTED_TEXT 具有严格相同的编码原子事实（量化值+范围+补丁）。两者与原始无损文本不是全部原数值相同，不能把 practical lossy compression 对照称为原始事实完全相等。COARSE_VISUAL 与 PROTECTED_VISUAL 的 PNG 字节相同，唯一新增信息是精确修补。所有非指标向量/缺失字段严格相同。重复原有 min/max 及汇总可帮助解释，但不能以这些字段声称所有诊断信息已保留。

## 注册矩阵与统计

沿用 RQ3.10 的140已暴露 eval及原3个 smoke身份，60/60/20；不筛选、不增补案例，不运行 test/Gemma/训练/attention。正式1120位置；至多1162次正式请求（42恢复储备），smoke至多18次，合计1180，包括所有已发起、失败、恢复请求；先前767次RQ3.10请求作为历史消耗保留，绝不归零。精确相同无补丁 arms 可引用同一实际输入，但 EXACT_REPEAT 仍实际请求。所有位置都跑完，与成绩无关。

主要族，AIOPS120逐例配对：PV_HIGH−PT_HIGH（独立视觉价值）、PV_HIGH−EXACT_TEXT（部署实用性）、PV_HIGH−COARSE_HIGH（补丁作用）、PV_LOW−PV_HIGH（固定预算曲线）。次要族：PV_LOW−PT_LOW、PV_LOW−COARSE_LOW、EXACT_REPEAT−EXACT_TEXT。Pratt Wilcoxon 差值round12位、Cohen dz、各族Holm、事件组等权敏感性、AC@1/3/5及AVG@3/5、分数据集/故障/粒度。Aegis20和按压缩误差/补丁数分层只作探索。保存逐例输入/输出/token/时间/失败和根因覆盖。

实用目标：已预选 HIGH 作为拟部署方法。相对强文本观察总 token至少降低20%，且配对 MRR不下降，是开发成本目标；单纯小于0.01的点估计损失不证明非劣。严格宣称性能与成本同时改善需主要比较Holm<.05、正增益且成本下降；视觉独立价值还需PV_HIGH−PT_HIGH显著为正。不从LOW/HIGH中选择得分更高者作为预选方法，不用smoke正确率筛选。

## 检查与启动边界

新目录 RQs/RQ3_11，五功能模块+__init__，≤7500有效行，shell只触发。新结果protected_v2，端口21941。继承共享client/原scorer和冻结本地Qwen模型：BF16、context40960、全局输出上限16384、注册请求8192；triton GDN显式本地适配、thinking off、36请求、8异步写线程。CPU≤8进程独立物理核、source组交错先dispatch，全量预渲染后才占GPU。

先静态源码/接口/隐私/协议审查；CPU合成边界与全部140×8真实processor容量、全部PNG DOM资格、原始/解码签名和同信息字段 equality；主agent学术第一阶段审查后，唯一逻辑GPU smoke运行3例×6等价路径=18：EXACT_TEXT、COARSE_VISUAL_LOW、PT_LOW/HIGH、PV_LOW/HIGH。COARSE_HIGH已由同一HIGH PNG/调用路径覆盖，REPEAT由相同TEXT请求路径覆盖；CPU仍检查所有8臂。600秒包含启动和落盘，重启不能重置。Streaming partial_responses原子持久化、完整完成响应/轨迹/对话/评分/使用量审查；准确率不是pass gate。

源码、配置、原始roster、继承依赖、renderer、client、scorer、profile、tokenizer/model修订在首调用前归档并哈希。恢复只读小索引/完成标记，先跳过已完成模型/位置再物化context；新调用提交时正常身份与commit审计。非timeout基础设施故障停止队列诊断；timeout缺失不当零分，模型解析失败保留零分。资格通过后后台启动完整固定矩阵，确认队列和首批真实atomic完成后落盘receipt并停止本轮agent，不自动分析或启动后续方法。supervisor在队列结束后自行关闭所拥有server。
