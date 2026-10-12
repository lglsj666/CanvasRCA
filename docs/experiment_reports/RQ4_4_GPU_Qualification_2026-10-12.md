# RQ4.4 GPU 资格与正式运行部署 — 2026-10-12

一个共享 GPU smoke 已完成并通过：18/18 次，含启动、保存、关停和自动核验共 199.93 秒，未重置调用或时间额度。三例固定 eval 身份覆盖三臂 RCA、独立 QA、完整目标卡片 QA 和 attention 开关。正式队列冻结为 840 个位置：660 次主矩阵、120 次 QA、60 次重复与顺序扰动；总调用上限 900，包含已用 smoke 18 和基础设施恢复预留 42。

## CPU 与实际输入

220/220 病例、660 个主输入通过完整 CPU 资格，另完成 30 例机制输入及固定 smoke 输入。16 项离线回归和两项共享 renderer 注册／默认操作回归通过。18 个实际 processor 多图输入的 MRoPE 和逐图 gather 已与独立计算核对。SOURCE_ZOOM 与 HASH_ZOOM 的局部字号和线宽通过门槛；原概览 PNG、处理几何和 U 保留索引未变。三个数据集三臂例图及长名称、密集和最大卡片已实际打开检查。

CPU 资格是几何、事实与实现检查，不表示模型一定读懂图形。Smoke 没有以 MRR 或 QA 正确率筛选输入、修改方法或追加调用。

## GPU 与 attention

真实输入 PNG、提示、逐图 token、输出、评分与调用账本均核对；无基础设施失败、额外分支模型调用、vLLM 抢占或 attention 丢失。使用本地 BF16 Qwen、vLLM、40960 context、8192 输出适配、显存利用率 0.8、8 个不同物理核 CPU worker 和 GPU 并发 8。CPU 在 RAM 中预取，最多 16 个准备／就绪任务，另有 8 个在途任务，不使用磁盘缓冲。

采集 9 份 attention 摘要，每份 3,525–3,966 字节。当前实际覆盖第 3 层最后一个 prompt query 和首个 decode query，分别记录文本及两张图的区域；没有取得后续排名／QA 答案字段查询，不能称为最终决策全过程。所有已采集值和查询／区域定义保留，不保存完整矩阵，也不为 attention 重放请求。

## 保存与恢复修复

Smoke 后的部署复查修复了同进程多线程原子写入的临时文件重名风险，补齐引用条目的逻辑身份、终态进度、断电后独立恢复收尾，以及保留文件的哈希和引用核对。16 项 CPU 回归覆盖并发写入、断电、独立重复、引用、排空及最终保留核验。

原 smoke 冻结快照及证据完整保留。修改只涉及保存／恢复和对应测试；全部 858 个冻结请求登记、生成身份、模型／processor、图像、选卡、renderer、推理路径、attention 采集和解码配方与 smoke 相同。新正式凭据显式引用原 smoke 及存储修订核验，没有把 CPU 检查写成新 GPU 测试。

运行期间保留重绘所需 HTML；全部回答提交、服务关停和写入排空后，保留精确 PNG、完整提示和回答、评分映射、公共证据、DOM 几何、token 操作、实际 attention、配置及源码。HTML 属于编译中间材料，后续查看完整输入输出、重评分、统计和已采集 attention 分析不依赖它。历史实验 HTML 不修改；本轮不再把它作为收尾后的必要依赖。采用普通文件和校验后的硬链接去重，不创建压缩归档。最终按实际完成调用数核验每次不超过 2,500,000 bytes；启动前容量估算可行，最终大小仍以排空后的实际审计为准。

## 运行与检查

查看进度：`bash RQs/RQ4_4/scripts/run.sh status`。

安全暂停：`bash RQs/RQ4_4/scripts/run.sh pause`；关闭机器前等待状态变为 `paused` 且自有服务退出。

恢复：`bash RQs/RQ4_4/scripts/run.sh resume`。已经提交的回答直接跳过；全部调用完成但收尾中断时，只恢复离线分析与保留核验，不加载模型或重新生成回答。

查看完整单条对话：`bash RQs/RQ4_4/scripts/run.sh view --key <call_key>`，输出直接可打开的 HTML，使用保留的实际图像。

[计划](../experiment_plans/RQ4_4_Source_Bound_Multiscale_Plan_2026-10-12.md) · [CPU 报告](RQ4_4_CPU_Qualification_2026-10-12.md) · [例图库](../../RQs/RQ4_4/results/source_views_v1/examples/index.html) · [GPU 原始核验](../../RQs/RQ4_4/results/source_views_v1/smoke/review.json) · [存储修订凭据](../../RQs/RQ4_4/results/source_views_v1/qualification/storage_revision.json) · [当前状态](../../RQs/RQ4_4/findings/exp_source_views_findings.md)。

启动监控完成：首批提交后持续观察180.30秒，交接时37/840已提交，8路在途、16个RAM就绪任务；无基础设施失败、KV抢占或attention丢失。日志存在已处理的可选DeepGEMM导入警告，实际使用原生FlashAttention/Triton路径，未导致调用失败。正式实验仍在运行。
