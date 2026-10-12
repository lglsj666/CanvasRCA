# RQ3.21 GPU 资格与正式启动记录

日期：2026-10-06（America/Toronto）。本文件记录运行资格与启动，不是正式效果报告。当前为 **GPU smoke 通过，正式后台任务已稳定启动，首批新结果完整性核验通过**。截至 13:58:47 UTC（当地09:58:47），13次新正式调用完成、36次在途，另有220条历史锚点引用。

## 授权与冻结范围

用户本次授权“可以跑 GPU smoke test，通过后即可启动全量实验，发现问题先修复”。这取代此前 CPU 后停止的执行边界。使用独立、绑定冻结版本的执行凭据；原计划、配置和历史资格材料保持不变，正式入口仍要求 CPU、视觉、smoke 和实际产物审核同时通过。

- 冻结源契约：`635f9be2633b7b2a4aa97259aa9ce874cb8bd63bafa4ba7a36a922dcaf088754`，211 个依赖文件。
- 本次没有修改实验源码、提示、事实、图像、统计比较或队列规则；原静态和完整 220 例 CPU 资格仍匹配冻结版本。
- 全部 RCA 均为单次诊断调用。QA 独立测量，不将答案传回 RCA。Attention 关闭。
- 本地 Qwen3.8-27B，BF16、无量化，context 40960，RCA 输出上限 8192、QA 上限 1024，显存利用率 0.75，请求并发 36；既有采样配方不变。
- 图像继续使用最新 unified renderer 核验通过的同一原生边际 PNG；没有新绘图实现。

## GPU smoke 结果

| 项目 | 结果 |
| --- | --- |
| 固定 eval 身份 | AIOPS-2022 `INC-6E627662CA32`；AIOPS-2025 `INC-D9245047C658`；AegisLab `INC-37ABFB78A80E` |
| 实际新增调用 | 18，全部独立提交，零引用 |
| 覆盖 | 14 次 RCA、4 次 QA；其中 11 次含图像 |
| 原子提交 | 18/18 |
| 未解决基础设施失败 / 超时 | 0 / 0 |
| 模型格式无效 / 截断 | 0 / 0 |
| 实际输入与 CPU processor 一致 | 18/18 |
| 实际输入 token 范围 | 15,221–24,592 |
| 实际输出 token 范围 | 177–308 |
| 完整逻辑 smoke 耗时 | 407.99 秒，包含两次启动修复及最终审核；没有重置 600 秒窗口 |

18 份真实输入均与冻结编译器的文本部分、PNG 哈希、system、输出 schema 及有效配置一致。实际打开三数据集 PNG；确认 14 份 RCA 各含五个不同的合法候选，4 份 QA 结构有效。完整提交图审计和独立评分重放通过；实际 provider usage 与成本账本、CPU 输入计数一致，结束原因为 `stop`，无 reasoning 文本或 attention sidecar。

两组原输入与独立重复使用相同事实和请求内容，但具有不同 call key、provider request ID 和真实调用支出；输出碰巧相同不代表引用。没有依据 smoke MRR 或答案内容调整方法。

人工阅读也发现部分模型理由存在数值变化、实体归属或关系方向误读。这些作为原始模型结果保留，留待正式解释审核；输入/渲染/评分完整性通过不等于解释正确性或方法有效性通过。

### 启动环境修复

1. 共享启动器默认打开 attention，本轮要求关闭。在服务尚未就绪、零模型请求时停止，显式设置 `CANVASRCA_ATTENTION_MODE=off` 后重启。
2. systemd 后台环境缺少 `/usr/lib/wsl/lib`，服务就绪后的显卡核验无法找到 `nvidia-smi`。自有服务正常关闭，仍为零模型请求；补齐后台 PATH 后重启。

原失败日志、监督状态和修复凭据均保留。第三次启动完成全部 18 个请求，整个过程共用最初的时间窗口和调用账本。正式服务显式关闭 attention 的三个环境开关，并使用含 infer/bin 与 `/usr/lib/wsl/lib` 的 PATH。

## 正式矩阵与预算

六个新主臂为 RAW_TEXT、RAW_VISUAL、PACK_VISUAL、ENTITY_VISUAL、PACK_ENTITY_TEXT、预选 PACK_ENTITY_VISUAL。六臂 × 220 例为 1,320 个新位置，60 例机制/重复各八项为 480 个新位置，共 **1,800 个新位置**。

另有 **220 个 ANCHOR_VISUAL 历史引用**，经 CPU 审核后复用 RQ3.16 MARGINAL_FIVE；没有重跑锚点。因此完整逻辑矩阵为 **2,020 个位置**。其中 21 个普通位置可引用本轮精确相同请求，预计无基础设施重试时为 **1,779 次正式新生成**。独立重复始终新调用。

正式尝试上限 1,922，smoke 18，总上限 1,940；122 次只供允许的基础设施恢复，不能用于重答已提交的错误排名、模型无效输出或新增实验臂。预计无重试总实际支出为 1,797 次，包含本次 smoke。

按冻结哈希队列运行，不依据部分结果改变队列。220 例全部属于已暴露开发 eval；历史锚点是跨轮参照，不能称为同期新调用或独立确认集。MRR 和 input＋output 总成本结论等待完整批次，CPU 输入下降不能代替它们。

## 后台运行与审计入口

- systemd 用户服务：`canvasrca-rq321-formal.service`。
- 状态与阶段提交：`RQs/RQ3_21/results/compact_entity_v1/formal/`。
- 监督日志：`RQs/RQ3_21/results/compact_entity_v1/logs/formal_supervisor.log`。
- GPU 资格：`qualification/smoke_review.json`；逐请求核验：`smoke/request_review.json`、`smoke/actual_output_review.json`、`smoke/artifact_review.json`。
- 启动环境修复：`qualification/gpu_startup_environment_repair.json`。
- 启动核验凭据：`formal/launch_receipt.json`，记录主监督PID 5309、server PID 5371、runner PID 6031以及首批审计快照；PID只作运维元数据。

首批六份新正式提交逐一审计完整产物图，实际usage匹配CPU、输出限额正确、finish为stop，attention和reasoning均关闭；所有新提交均不含历史锚点调用。新调用持续完成并补入待执行请求，核验时为13 complete＋36 started、无失败。对服务与运行器分别检查了attention环境及CUDA设备，冻结资格仍一致。

监督器负责完整队列及自有 GPU 服务的退出；原子完成标记用于恢复，恢复不批量重开历史图像和输入。本次在正式生成及提交核验后结束，后台继续运行；不在本轮启动其他实验。后续如需安全暂停，可向该服务主进程发送SIGUSR1，监督器停止补入新请求并排空在途工作。

相关材料：[CPU 资格报告](RQ3_21_CPU_Qualification_2026-10-06.md)、[计划](../experiment_plans/RQ3_21_Compact_Evidence_Entity_Organization_Plan_2026-10-06.md)、[唯一当前状态](../../RQs/RQ3_21/findings/exp_compact_entity_findings.md)。


## 后续运维：2026-10-06误关机恢复

当地12:36按用户要求恢复，原冻结资格不变、未新增smoke。关机断点1295完整提交＋8终态超时，35在途尝试作为interrupted保留支出；恢复476调用＋21引用。当地12:40:49核验新增16个提交，原已提交结果和终态超时均未重跑，首批5份新提交完整性与token计数通过。服务仍为canvasrca-rq321-formal.service（新监督PID1976）。详情见当前findings及formal/resume_20261006_power_loss/verified.json；以上首次启动时点数据保留为历史快照。
