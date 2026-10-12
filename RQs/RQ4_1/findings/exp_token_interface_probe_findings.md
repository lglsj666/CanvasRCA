# RQ4.1 Qwen 视觉 token 接口实测 — 2026-10-06

**结论：当前本地 Qwen 的真实权重可以在图像编码后、语言模型读取前直接裁剪视觉 token，并继续完成自回归生成。模型级接口验证通过；现有 vLLM 服务尚未适配。**

本次是用户要求的小例子可行性实测，不是 RCA 实验或正式 smoke。使用三个已暴露 eval 病例的真实 unified-renderer dashboard、四条输入路径，共 **12 次新调用，12 次完成**。累计共享时间 **111.58 秒**，含一次零调用的环境启动失败及修复。没有启动全量、训练或 attention 采集。模型进程已退出。

原始结果：[summary.json](../results/token_interface_probe_v1/summary.json)；独立落盘审核：[offline_audit.json](../results/token_interface_probe_v1/offline_audit.json)；协议：[原始冻结登记](../results/token_interface_probe_v1/source_snapshot/RQ4_1_experiments.md)；代码：[main.py](../src/main.py)。本研究 10,000 次总上限中已消耗 12 次，余量 9,988；余量不等于已授权队列。

## 1. 实际测试了什么

本地模型目录是 `/home/lglsj/CanvasRCA/models/Qwen3.8-27B`，其配置声明架构为 `Qwen3_5ForConditionalGeneration`。使用原始 BF16 权重，全部参数冻结。Transformers 5.14.1、PyTorch 2.11.0+cu130、单 RTX PRO 6000；没有量化、训练或替换投影器。

直接复用 RQ3.21 已生成的 1120×800 原生边际图，三个 PNG 哈希逐份核对、图片实际打开审查。这些图只用于读图接口验证，不代表 RQ4 的完整 M/R/L/G 输入方案。

| 数据集 | 固定病例 | 左卡 parent / child 的图上真实值 |
|---|---|---|
| AIOPS-2022 | INC-6E627662CA32 | 45365 / 63581 |
| AIOPS-2025 | INC-D9245047C658 | 326 / 389 |
| AegisLab | INC-37ABFB78A80E | 364 / 437 |

模型仅接收图像与固定读图问题：读出左卡父、子实体标识及两个阶段。上述答案没有进入提示，图片路径、数据集、病例 ID 和评分标签也没有进入模型文本。没有根因排名问题，更没有把 QA 输出传给另一次 RCA。

四条路径均使用相同短提示、greedy 解码及最多 64 个输出 token，thinking/preserve_thinking 均关闭；不使用正式 RCA 的采样或 JSON 约束配方。这是为检查适配的逐 token 等价性而登记的独立技术协议。

## 2. 真正减少了语言模型序列长度

原 processor 实际生成 `image_grid_thw=[1,50,70]`，经原模型 2×2 merger 后有 875 个视觉 embedding，另有 90 个非图像 token。

| 路径 | 语言模型视觉 token | 总输入 token | prefill 后 full-attention cache 长度 | 输出与原生逐 token 相同 |
|---|---:|---:|---:|---:|
| native 原生图片 | 875 | 965 | 965 | 3/3（自身参照） |
| identity 手动注入全部视觉 embedding | 875 | 965 | 965 | **3/3** |
| uniform_half 保留约一半 | 438 | 528 | 528 | **3/3** |
| uniform_quarter 保留约四分之一 | 219 | 309 | 309 | 0/3 |

identity 的三个首步完整词表 logits 与原生路径的最大绝对差均为 **0**；生成 token 序列也完全相同。裁剪路径所有首步和解码步 logits 有限，所有调用自然结束，没有输出截断。保留一半/四分之一使总输入长度减少约 45.3%/68.0%。

四条路径共用本次显式位置坐标的逐 token 解码器；native 指原生图片 prefill，
不是一次另外调用 HF `generate()` 或 vLLM 的端到端对照。因此该等价性检查不覆盖
正式服务的 generation 封装、批处理和调度，不能替代后续服务资格。

这里从 `inputs_embeds` 中实际删除位置，并相应缩短 attention mask 和 KV 序列；没有把置零、隐藏图元或账面修改 token 数冒充裁剪。每个保留 embedding 使用原始三轴 MRoPE 坐标；图外静态 token 全保留。生成位置接续原始多模态坐标最大值，不能直接用裁剪后序列长度代替。每次调用独立初始化 cache。

独立 CPU 审核重新计算选择索引、非视觉 token 的保留集合、原坐标子集、prefill 与解码 cache 长度；逐份检查提交、图片和冻结代码哈希。12 份记录全部通过。

## 3. 读图结果和限制

| 路径 | 两个实体标识均正确 | 阶段正确 |
|---|---:|---:|
| native | 3/3 | 0/3 |
| identity | 3/3 | 0/3 |
| uniform_half | 3/3 | 0/3 |
| uniform_quarter | 2/3 | 2/3 |

四分之一保留率在 AIOPS-2022 把 parent **45365** 读成 **453**，不能认为强裁剪无损。原生模型也把两个阶段答成父/子耗时轴名，而非 reference/current；其余两例的四分之一路径反而答对阶段。这只能说明本次小问题的输出如何变化，不能以三例建立准确率规律、QA 与 RCA 关系或选择正式保留率。

12 个回答均带 Markdown JSON 围栏，因此严格的裸 JSON 格式要求均未满足；去掉围栏后内容均可解析。保留原始回答，不修补答案、不追加重答。格式与读图正确率和接口通过状态分别记录。

## 4. 成本观察不能直接推广

| 路径 | 平均 prefill 秒 | 平均该次 prefill＋解码秒 | 最大 CUDA allocated GiB |
|---|---:|---:|---:|
| native | 0.511 | 3.098 | 51.545 |
| identity | 0.439 | 2.998 | 51.521 |
| uniform_half | 0.329 | 2.887 | 51.364 |
| uniform_quarter | 0.273 | 2.427 | 51.273 |

这是固定顺序、单例串行、短生成的小测试，存在预热和不同输出长度，不能当作正式吞吐或端到端降本结果。适配路径复用了该图预先计算的 encoder 特征，其上表耗时没有包含那次编码；编码耗时单独保存在每份记录中。native 则在自身 prefill 内运行 encoder。必须计入完整图像编码和选择开销后才能作部署成本比较。

本方法裁剪的是 **vision encoder 之后** 的视觉 embedding，未减少 encoder 的像素或 patch 计算。Qwen 的线性注意力状态也不会按输入 token 同比例缩小。模型权重占据主要显存，因此视觉序列减少约 50% 不等于显存或总成本下降 50%。

CUDA allocator 使用 0.75 上限，最大 allocated 约 51.55 GiB，运行中采样总占用约 55,204 MiB，低于显存总量的 75%。这不是 vLLM 的显存预留设置。模型退出后采样占用约 1,557 MiB，已无本次计算进程。

## 5. 环境修复、可复现性和服务边界

首次加载因 infer 环境缺少 `accelerate` 失败，当时 **0 次模型调用**。通过 experiment-local import 目录中的两个符号链接暴露现有 train 环境的 accelerate 1.12.0，其余库仍用 infer 环境。没有安装、覆盖或修改共享包。原失败日志、summary、freeze 及源代码保存在 `startup_failure_v1/`，修复没有重置 600 秒或调用预算。

模型加载后使用 HF 原生 Torch 的线性注意力实现，日志提示快速扩展未齐备；这不影响本次有限性和等价性检查，但速度不能与 canonical vLLM 相比。最终源码快照、实际版本、配置及输入形状已冻结在结果目录。

已安装的 vLLM `model_executor/models/qwen3_5.py` 明确设置 `supports_multimodal_pruning = False`，且 `recompute_mrope_positions` 抛出不支持异常。本次没有修改该文件，也没有把这个开关直接打开。正式服务仍须实现并资格验证变长图像 embedding、placeholder 数、位置坐标、调度 token 计数和 cache 的一致性，或明确登记不同后端及全部基线的同后端重测。

## 6. 对 RQ4.1 设计的决定

**可以把无需训练的直接视觉 token 操作纳入 RQ4.1。** 已经有实际权重和实际图像上的可行证据，不只是源码推测。

下一步的重点应是选择“保留哪些 token”：优先保护实体标识、单位、阶段绑定和比较所需的图元，同时检验同预算通用裁剪对照。50% 只是本次技术试验点，不是已经确定的最佳预算。正式候选仍须携带完整所需诊断证据的纯视觉 dashboard，并完成大图、密集关系、多组件及批处理资格。

本次没有验证 token 合并、token 重排、attention 重分配、MRR、完整图像压缩能力或 vLLM 高并发适配；不能把“裁剪可运行”扩大成这些路径全部有效。完整 RQ4.1 实验矩阵仍在设计中，未启动正式实验。

2026-10-06 后续状态补充：完整前瞻方案已定稿，见[新方案状态](exp_comparison_coding_findings.md)。用户随后将RQ4.1总上限从10,000提高到12,000；本探针的12次已耗记账不变。以上是探针完成时的原始证据和限制，不代表新方案已资格或运行。
