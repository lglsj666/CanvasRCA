# RQ3.8：完整关系与真实时序的冗余视觉辅助

2026-09-29。实施中；须完成静态、CPU、实际 PNG 审阅和 GPU smoke 后才提交正式任务。
本轮使用 Qwen3.8-27B 与 dense Gemma-4-31B-it，不使用旧 Gemma 成绩选择方法。

## 研究决策依据

阅读范围为 `docs/experiment_reports` 的 RQ1.1/RQ2.1 汇总、Tournament、RQ3.1–3.7
及 Cross-Experiment Method Profile。以下判断只使用 Qwen 结果。

| 历史证据 | 本轮承接方式 |
|---|---|
| RQ1.1 三主数据集 TPV .3819、T .3093，全视觉 .2658；M/R 视觉化有损失 | 保留全部原 M/R/L 文本，不强迫模型从图上读取精确数字 |
| Tournament R11 改 M 承载后新增 43 个成功；后期方法增量小 | 不再增加选择器，不把联合覆盖当作单次诊断能力 |
| RQ3.1 X 丢失大量原有效资源证据；RQ3.2 去掉基础保留有害 | 冻结 ALL_ID 的原数值、证据选择和补充观测，不换统计窗口 |
| RQ3.3 W_G 比 TPV 有正向趋势；RQ3.4 增加检查未必帮助；RQ3.5 指令影响较大 | 固定科学 prompt，不加预诊断、多次修复或训练 |
| RQ3.6 关系、宿主和实例范围存在条件性作用 | 调用图来自完整 per-case 公开关系，不从已筛选 span 小池恢复关系 |
| RQ3.7 A 中 LOCAL_LINK vs TPV 的配对 MRR .4776 vs .4005，但相对文本/REMOTE 的优势不足以证明连接机制 | 不宣称已找到视觉冠军；在真实时序和模块化 renderer 中检验是否仍有收益 |
| RQ3.7 A 的 AIOPS 图主要是读数，缺少合格前后柱形；C 的 Qwen 已完成但新汇总尚不完整 | 采用原有 64-bin 样本曲线，独立设同样读数冗余控制；不依靠未知单位推导新物理量 |

新意不在于“首次使用折线图”。本轮检查的是：在精确文本保底时，恢复未被
top-k 保留的公开关系以及重复编码完整时序，是否改善**证据利用**；额外效果是否
超过仅复制读数，并在 dense 第二模型上重新检验。旧 MoE 与 dense 差异不做因果归因。

## 一个实验，八个注册条件

实验名 `operational_visual_support`；完整、固定 eval480，五个数据集均运行。
它是 repeated-exposed 方法开发/回归集，不称新独立 test。本轮不打开更多 test。

| Arm | 模型收到的内容 | 对应问题 |
|---|---|---|
| T_SELECTED | ALL_ID 公共文本、原选中关系，无图片 | 新接口的文本锚点 |
| T_FULL | 同上，增加完整公开关系，无图片 | 完整关系本身是否有用 |
| G_SELECTED | T_SELECTED＋原选中关系的新 renderer 图 | 选中关系的冗余图示 |
| G_FULL | T_FULL＋完整关系图 | 完整关系的视觉利用 |
| READOUT_FULL | T_FULL＋完整图＋已选 64-bin 数值读数面板 | 重复数字而非真实曲线的控制 |
| LINE_FULL | T_FULL＋完整图＋同样的时序折线面板 | 曲线几何是否超过重复读数 |
| LINE_BOUND | LINE_FULL＋每个观测实体一条归属虚线 | 真实曲线中的跨组件归属连接 |
| LINE_PAIRS | LINE_FULL 的调用图改成逐条有向边图块 | 密集关系展开后的实际可读性/成本 |

T/G × selected/full 构成完整 2×2，用于区分增补关系、冗余图示及其交互。
后四项不是重新筛选指标。保留全部原 M/R/L/G 文本及 ALL_ID 追加观测。
同事实视觉比较必须确认原文本包含对应 bins、数值、单位及节点类型。
READOUT/LINE_FULL/LINE_BOUND 共享全部面板尺寸和坐标；LINE_BOUND 只加归属线。
归属线不是调用或因果传播边，不计入节点连接度。

LINE_PAIRS 需要逐边图块，必要时增加整幅图高度；不能因此把其结果解释为严格
等分辨率下的纯布局效应。注册为实践中的完整编码/成本比较，不压缩字体或删边。
G_SELECTED/G_FULL 的像素尺寸可因完整图容量而不同，其 content 效应同样包含承载代价。

## 数据、图形与语义

仅复用已完成 RQ3.7 的公共缓存与既有 canonical per-case 关系字段，禁止重读原始大表。
来源索引、private evaluator 文件和模型输入物理分开。所有 case 只导出一次。
模型不接收案例路径、数据集名、标签、注入时间或选择器建议分数。

完整观测关系不是“真实系统全知拓扑”：它只覆盖该 case 公开遥测/元数据支持的边。
SQL 等外部端点保持匿名、类型明确；没有合法数据支持时不补边。保留 calls、
request-parent、hosts、service-instance 各自语义；调用图不等于传播图。
图显示连通端点；已绘指标所属实体即使孤立也保留，用于可核验归属。
node→pods 与 service→pods 使用括号分组，不强假设 service/pod 一一对应。

全部图片由 `src/renderer` 的 Python DTO + React/HTML/CSS 组件库生成。
不修改旧 RQ renderer；本轮只登记新组件、布局参数和图形语法，不以旧 PNG 冒充新 renderer。
宽 2304，字体 18，间距 18，边距 28，scale 1；高度按公共容量公式、最多 8192。
曲线连接相邻有效观测，不新增 missing 图例，不填零。计数器仍显示原累计观测，
不自动转换为速率；未知单位不猜测。单位、均值等已有读数保留为明确标签。
数值控制可用等值无损科学计数法节约空间，不额外舍入样本。

## 主假设和统计

预注册主方法 LINE_FULL；LINE_BOUND 是明确的机制候选，不逐 case 挑答案。
六项主比较，各模型分别检验，合为 12 项 Holm family：

1. G_FULL − T_FULL；
2. T_FULL − T_SELECTED；
3. G_FULL − G_SELECTED；
4. LINE_FULL − G_FULL；
5. LINE_FULL − READOUT_FULL；
6. LINE_BOUND − LINE_FULL。

2×2 交互、LINE_PAIRS 比较为 secondary family。Primary MRR；AC@1/3/5、
AVG@3/5、repair/break、root rank、未知 ID、格式失败及 token 成本全部保留。
Pratt Wilcoxon、paired dz、不报告 CI；case 为统计单位，重叠事件组补充敏感性分析。
分别报告五数据集、两个 AIOPS 合并、三个主数据集等权 macro、五集 macro 和 pooled。
主论点不得依赖饱和 RE2 拉高均值。ΔMRR≥.05 且 Holm p<.05 才称实质提升。

预先按公开特征分层：边增补比例、图密度、指标有效点数、平稳/持续/脉冲形态、
观测实体是否孤立、宿主与实例同时有观测。故障类型和根因层次仅用于离线分析。
检查 repair/break 的完整 reason、实体误绑定、错误关系和实际数值引用；不把公开
reason 当作隐藏推理。历史 TPV 仅为 Qwen 端到端背景/配对参考，不冒充新 dense 基线。

## 模型和运行合同

Qwen 固定 revision `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0`，与本地一致。
Gemma-4-31B-it 固定 revision `842da3794eaa0b77d5f08bae87a17459d91ff475`。
两者 BF16、不量化；40960 context、请求最多8192 output、温度1、top-p .95、seed42。
Qwen 原生图像政策不加 pixel override；Gemma 显式 `max_soft_tokens=1120`。
这是官方支持的最大高细节档，不声称全任务的经验最优。
[官方配置更新](https://huggingface.co/google/gemma-4-31B-it/commit/1b2dc44dc6bbf96c63392c0996b335b8acafba66)。
不启动 attention，保留真实 processor/token 数、PNG、完整请求、raw reply、conversation 和 scorer 结果。
Qwen/Gemma 原各自 thinking、chunked-prefill、xgrammar 设置不混同。

用户最新授权 supersede 历史 local-only 限制，仅对本轮采用 Nibi、新 Gemma 和
统一 renderer。使用专门版本化 profile，不改旧科学记录。Nibi默认不传 VRAM fraction。
每个 Slurm job `gpu:h100:1`、8 CPU、96GB RAM、最多8小时；启动时检查实际 ≥75GiB
可用设备总显存、H100 和单张分配。40GB MIG 不运行。

CPU 最多8 worker，各占独立物理核心，cloudbed/source 交错；提前生成输入，不占 GPU 等渲染。
推理最多36请求并发、scheduler256；每个 job独立端口、进程归属、ledger和日志。
请求timeout300秒记终态 fail继续；其他基础设施错误停止本 job并排空；不新增5%规则。
done/fail标记在必要产物完成后写入；恢复仅读标记。无标记目标才重建请求。
已失败目标不自动重试；已用调用永不从预算中抹除。

## 规模与次序

8×480×2 = **7,680** 个正式逻辑目标；重复完整请求应引用而非多跑。
共享历史调用基数待读取最终 ledger再锁定；当前审计为 **28,216**。
一个逻辑 smoke ≤18calls、总600秒（含模型启动与切换）；计划合计 **35,914**，
距共享40,000上限留 **4,086**。六个分片各预留1961调用、smoke18，累计仍≤40000。
预留不是新增实验授权，正式结果节约调用不转为新 arms。

1. 公共证据导出，静态三焦点审阅，3个主数据集 CPU 实例和图片审阅；
2. 在 Nibi 完成两真实 processor 容量检查及 CPU 回归；
3. 单个 bounded smoke，两模型顺序运行；记录实际覆盖，不以准确率资格化；
4. 审阅所有 smoke 完成的输入/PNG/对话，修复必要问题；
5. CPU 准备完整480，复用完成标记；根据实测吞吐确认每片适合8小时；
6. 提交不超过六个正式 GPU jobs：2模型×3个数据集均衡 shard，全部 arm固定；
7. 提交成功后按用户要求删除本地旧Gemma26并启动Gemma31下载，下载开始即停止本次工作。

不保证用满每个8小时，也不因调度等待改成40GB或量化。超时保持续跑状态；是否
另行提交重跑不得偷偷突破用户六次正式 job 限制。

## 文献和重复边界

[Dashboard Design Patterns, VIS 2022](https://virtual.ieeevis.org/year/2022/paper_v-full-1554.html)
支持把稳定组件和全局组合分开；不是新布局有用的性能证据。
[Dashboard Zoo/Census, VIS 2025](https://sfa.ieeevis.org/year/2025/program/paper_aeb6a938-4d06-4c0d-828a-6152918115c3.html)
用于现实仪表盘风格依据；不把美观等同于 RCA 正确。
RQ1.1 已做过总体图文和冗余图文比较，RQ2.1 已做过折线/表格/布局；本轮不重申
“图胜文字”的泛化问题，而冻结近期有效文本，测新增完整关系和冗余时序的条件效应。
RQ3.7 已做过数字面板归属线；LINE_BOUND 只复核其在真实曲线中的迁移，不能当成
全新的归属机制。结果若无收益，保留而不继续扩大相似布局搜索。
