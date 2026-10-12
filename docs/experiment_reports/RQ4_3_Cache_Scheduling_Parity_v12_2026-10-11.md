# RQ4.3 v12：固定 KV 存储与 smoke／正式调度核对

## 状态与授权

2026-10-11。用户要求修复正式运行的低利用率及显存跳变，逐项核对 smoke 与正式调度；沿用“修改后静态检查与一致性通过，直接恢复正式，不另跑 smoke”的明确授权。v12 的 GPU 资格是版本绑定的用户豁免，**不是新增 smoke 通过**。本次没有新增 smoke 调用，也没有重跑全人口 CPU 回归。

v11 在 347/2632 个位置全部原子提交、零在途请求后退出。v12 从这些提交继续，队列、调用上限和已完成结果保留。静态检查通过，3774 功能行；针对改动的 7 项小范围 CPU 检查通过。另用随机初始化微型 Qwen 验证两种长度的 token／embedding 输入，4 次离线生成的新旧缓存输出一致。它们不等于真实 GPU 模型等价性证明。

## 实测问题：哪些已经确认，哪些仍只是解释

历史 smoke08 的 18 次请求在实际请求区间完成用时 226.50 秒，约 4.77 次/分钟、15.02 个输出 token/秒。v9 正式运行的 33 次请求在 522.57 秒完成，约 3.79 次/分钟、12.23 token/秒。smoke 的 8 请求在途阶段利用率均值 87.67%；v9 正式对应约 69.68%。两批病例与 arm 构成不同，不能将该差异全部归于调度。

v11 将 CPU 准备和 GPU 主机线程分到不同物理核，仍未解决问题：33 次正式请求区间 533.79 秒，6464 个输出 token。CPU 争用不是已证明的唯一根因。短时暂停准备、改变 affinity 的探针受 prefill/decode 阶段混杂，只作为定位资料，不作为加速效果结论。

已直接观察到旧路径显存从约 73–76 GiB 量级下降约 10–12 GiB 再上涨。源码确认两个开销来源：

1. 每次请求在 prefill 前持有 forward 锁，执行全设备同步并 `empty_cache()`，主动释放可复用显存。
2. full-attention 的 DynamicLayer 每一步通过 `torch.cat` 扩展 K/V，重新分配并复制已有前缀。

第三项源码确认：旧路径将大 prefill 临时张量分配到 8 个独立请求 stream，尽管 prefill 同时只能有一个。缓存分属多个 stream，无法自然复用同一个 prefill 工作区。其对总耗时的独立贡献尚未分离测量。

证据在 `RQs/RQ4_3/results/throughput_repair_v11/` 的 comparison、startup_monitor、live_memory_trace 和各探针 JSON；旧失败判断保留。

## v12 的具体修复

- 7 个普通槽位各预留 16384 token，1 个长文本槽位预留 40960 token。全部 2632 个请求逐项核对输入加 8192 输出；最高需要 32786，全部视觉请求适合普通槽位。分配器优先使用最小可容纳的空槽，释放槽位有条件变量唤醒。
- full-attention K/V 固定底层存储，更新时只复制新增 token；对模型只返回实际有效前缀。未用容量不参与 attention，不补充假 token，不裁切上下文。下一请求重置逻辑长度，旧数据无法经有效前缀读取。
- 48 个线性 attention 层使用原生更新函数和预留状态，卷积状态保持 BF16，recurrent state 保持 FP32。每请求重置原生状态。
- 8 个槽位 K/V 合计 9.5 GiB；线性状态额外约 1.15 GiB。这是模型缓存，不能与包含权重和临时工作区的总显存混淆。PyTorch 显存比例仍为 0.75，实际驱动显示还包含 CUDA 上下文等开销。
- 去掉每请求的全局同步及 `empty_cache()`；保留各请求结束同步和单一 prefill 准入锁。
- 编码与语言 prefill 共用一个 CUDA stream；解码保留 8 个独立 stream。输入就绪后 prefill stream 等待请求 stream；输出返回时请求 stream 等待 prefill，跨 stream 的 logits 与视觉特征登记 `record_stream` 生命周期。预填结束钩子在完成同步后释放 prefill 锁。
- 所有槽位在开始服务前完成缓存分配、初始化和相同的归一化内核预热；smoke 与正式调用同一初始化函数。预热不产生诊断答案或额外 LLM 调用。
- 权重、BF16、FLA 与 norm 算法、输出上限、独立采样 RNG、图像、prompt、P 算子和评分保持原协议；实现身份另记 v12，避免将实现变化隐藏在历史身份里。

固定 KV 不等于 vLLM 的连续批处理或分页调度，也不能保证所有临时显存完全不变。观察到显存更稳定并不自动证明吞吐达到目标。

## smoke／正式调度逐项核对

| 环节 | 共同实现或差异 | 判定与处理 |
|---|---|---|
| 入口与授权 | smoke 独立额度/600 秒；正式绑定版本和冻结队列 | 保留必要差异；没有重置已耗 smoke 额度 |
| 环境 | 同一个 infer、FLA overlay、OMP/MKL/OpenBLAS=1、native allocator 配置 | shell export 逐行相同 |
| 恢复 | 原子完成标记、call ledger、reference、已持久回答恢复 | 共用 RuntimeSession；不重新打开历史图像批量审核 |
| 输入与预处理 | prepare_initializer → prepare_formal → cold_materialize | 共用函数；CPU 子进程禁止 CUDA；统一 renderer |
| CPU 分配 | 8 进程/不同物理核；GPU 主机线程使用其余核 | 两种 scope 均使用同一 host_partition |
| RAM 预取 | 持续补满 8 个 CPU future，独立于 GPU 队列 | 同一 tmpfs 缓冲与字节计量；内存背压时才停止继续扩张 |
| 预取寿命 | smoke 仅 18 个任务，准备很快结束；正式长期持续 | 不可消除的工作负载差异；不拿短 smoke 当长期保证 |
| GPU 槽位 | 同一 ConcurrentSolvers、最多 8 个 future | v12 统一容量分配；长输入等待 40K 槽位，不降输出上限 |
| 长文本次序 | smoke 首个长文本完成后才放行其他请求；正式原哈希队列 | 保留 fail-fast 资格与冻结正式顺序的必要差异 |
| prefill 锁 | 一个准入信号量；首个 forward 完成后释放 | 共用路径；异常 finally 同样释放 |
| CUDA stream | v12 单一共享 prefill stream、8 个 decode stream | smoke／正式没有不同分支；显式跨 stream 等待和生命周期记录 |
| forward 锁 | 两者共用同一个逐 forward 的主机提交锁 | 避免 Python 线程争抢；不声称这是连续 batching |
| KV 生命周期 | 同一固定底层存储、有效前缀和逐请求状态重置 | 无逐 token 全前缀 cat；小范围独立数值检查通过 |
| 缓存回收 | 原来两者均逐请求清空；v12 两者均取消 | 保留进程关闭时回收；运行中复用工作区 |
| 常规预热 | v12 同一个 warm()、相同 shape 集合、无生成 | 不能由 scope 开关选择不同快慢路径 |
| 资格专用探针 | smoke 额外算子数值对照，正式不执行 | 明确保留；不能把这些探针当正式等价吞吐样本 |
| 采样、语法、任务 | 共用 grammar、独立每请求 RNG、生成与评分代码 | RCA 与 QA 各用原有任务接口，非调度分叉 |
| Attention | 同一 tap；smoke 固定开关配对，正式登记子集 | 科学协议差异，逐调用保存是否启用及错误 |
| 提交与失败 | 完整回答、账本、评分、原子完成标记；异常停止补任务并排空 | 共用代码；无效排名不重答，已提交结果不覆盖 |
| 时间与利用率 | smoke 有 load/首长文本/末尾排空；正式持续不同输入 | 分别报告采样区间、请求数、输出量；不混用统计口径 |
| 数据分布 | smoke 3 个固定病例；正式 220 例和机制任务 | 长度、图像形状、输出长度不同；没有同病例配对测速证明 |
| 退出 | 正常/暂停/错误均清理线程、进程、writer、锁、RAM 目录 | 共用 finally；关机仍信任原子标记恢复 |

以上是当前源码和记录的核对范围，不承诺无法观测的 CUDA/驱动行为不存在问题。正式启动后的稳定性、显存和吞吐实测另附本报告后续状态。

## 资格材料

`RQs/RQ4_3/results/deployment_v12/` 保存 static、consistency、GPU waiver、activation、原队列和冻结源码。`throughput_repair_v12/` 保存修复前源码、447 个受保护文件的哈希、小范围缓存检查、容量审核和恢复监控。Codex.md、renderer、历史模型实现和 347 个原子结果哈希一致。

完整人口 CPU 资格继承其原有版本和适用范围；这次小范围检查只覆盖缓存与槽位修复。GPU 不增加 smoke 调用。正式恢复后的数据按 runtime_revision 分层记录，运行时长不跨实现版本混为同一稳态估计。

## 恢复实测：利用率目标仍未达到

首次 v12 恢复前的 347 个结果继续保留；运行到 358 个原子结果时仍没有普通 Python/CUDA 异常。排除后述诊断操作后的失效区间，237 个“8 请求在途”外部采样的 GPU 利用率均值为 **72.30%**，末 60 个样本为 **71.72%**，未达到之前接受的约 85%。显存采样范围 71077–76936 MiB，仍存在工作区变化；不能声称固定 KV 已经让总显存完全稳定。

本轮缓存修复通过局部完整性检查，但**性能目标失败**。不把这项失败改写为成功，也不以短时 100% 峰值替代长期均值。对应记录：`throughput_repair_v12/utilization_summary.json`。

## 诊断操作引起的中断与恢复

外部 py-spy 采样被本机 ptrace 权限拒绝，没有修改系统权限。随后使用进程已注册的 SIGUSR1/faulthandler 线程栈诊断。第二次转储出现 `_Py_DumpTracebackThreads` 与 `torch._dynamo` 栈展开相关的段错误，进程退出。这个中断由 agent 诊断操作触发；不能归为自然模型失败或 CUDA OOM。停止这种诊断方式，保留失败日志。

358 个完成标记不受影响，8 个未提交请求按既有基础设施中断恢复规则记账，耗费不重置。清理了退出进程所属进程组的遗留 CPU 子进程及未消费 RAM scratch。以同一冻结 v12 源码恢复，PID 358210；恢复监控另存 `recovery_monitor.json`。只得到一次完整线程快照：7 个请求线程在 forward 锁等待，1 个在线性 attention forward 内。它支持源码描述的串行主机提交结构，**不能据此给出 CPU/GPU 时间的精确比例**。不完整的 12 次采样不能报告为完整 profiler 成功。

## 官方资料与论文核对：下一项优化该瞄准哪里

问题限定为：保持 BF16 权重、现有科学算子和单次 RCA 请求时，当前执行引擎为何低效？纳入官方 PyTorch/Hugging Face/vLLM 文档和原论文；不采用量化、换模型、改变输出任务或未经核验的博客倍速结论。按照项目 literature-review 流程核对，旧参考导航的混合/训练路线不构成当前执行授权。

| 证据 | 当前源码或实测 | 能支持的结论与限制 |
|---|---|---|
| 推理端没有合批 | ConcurrentSolvers 为 8 个独立 generate；逐请求 batch=1；forward_gate 串行提交整个模型 forward | 并发槽位数不等于一个 batch 的大小。准备队列充足并不能让这些独立 forward 自动合并 |
| CUDA Graph 未覆盖解码 | 只编译 norm，`triton.cudagraphs=False`；整体 cache 不可编译；主解码仍为 eager generate | 固定底层 KV 地址只是减少分配，返回前缀形状仍增长，没有整步图回放 |
| 逐 token CPU 同步 | xgrammar HF 适配器读取 `input_ids[-1].item()`；RankingPrefixGreedy 在排名阶段 `.tolist()` 后解码 | 每 token 含 CPU 往返；保持输出协议的同时应整合调度，不能简单删除约束 |
| 重复抽样开销 | IsolatedSampler 已抽一个 token，再返回单点分布，HF 又执行 softmax/multinomial | 第二次抽样没有额外决策价值。可评估同结果的选取路径，但本轮未修改采样配方 |
| 完整 attention | 当前是 PyTorch SDPA；infer 没有独立 flash_attn 包 | SDPA 自身可以调用 fused FlashAttention/cuDNN 等路径，包未安装不等于使用最慢实现；本轮没有成功的 CUDA kernel trace，不能声称每层实际选用了某个内核 |
| Qwen 混合架构 | 48 个 Gated DeltaNet 层已经使用 FLA；16 个 full-attention 层使用 SDPA | 标准 FlashAttention 不替代 48 个线性 attention 层，也不解决语法/采样和 Python 提交开销 |
| 数据供给 | 正式运行 ready RAM 中已有上百个请求，GPU future 保持 8 个 | 当前观察窗口里没有证据表明增加 CPU worker 能修复主要问题 |

PyTorch 的 [GPT-fast 官方文章](https://pytorch.org/blog/accelerating-generative-ai-2/)将 batch-one 生成的 CPU 发起开销与权重访存分开，并将静态缓存和 decode 编译结合。其测试模型、硬件和倍速不直接转用于本实验。我们当前只实现了其中存储分配部分，还没有解码整图回放。

Hugging Face 的[连续批处理说明](https://huggingface.co/docs/transformers/main/continuous_batching)把请求合批、CUDA Graph 和 CPU/GPU 调度重叠作为独立机制；主分支文档不能直接当作本机 5.14.1 的兼容证明。本地实现还必须核对混合线性状态、视觉嵌入及每请求 logits processor，不能把 generate_batch 当作无条件开关。

[ORCA（OSDI 2022）](https://www.usenix.org/conference/osdi22/presentation/yu)研究逐迭代调度与选择性合批；[vLLM/PagedAttention（SOSP 2023）](https://arxiv.org/html/2309.06180)研究与合批共同设计的 KV 管理。[vLLM CUDA Graph 设计](https://docs.vllm.ai/en/latest/design/cuda_graphs/)还明确区分不同后端及混合模型的图模式。这些支持优先审查服务引擎，而非仅提高 Python 并发数；不保证本实验迁移后的具体利用率。

[FlashAttention-2 原论文](https://arxiv.org/html/2307.08691)优化精确 attention 的工作划分和数据搬运，不解决整个生成调度。[PyTorch 2.11 SDPA 文档](https://docs.pytorch.org/docs/2.11/generated/torch.nn.functional.scaled_dot_product_attention.html)说明其可自动选择融合实现。因此单独安装 flash_attn 不足以作为已知瓶颈的完整修复。

下一步优先方向是**保留定制 prefill 的科学行为，将原生 decode 接入真正的合批和 CUDA Graph**。本地 vLLM 0.24.0 注册了 Qwen3_5ForConditionalGeneration，但尚未证明支持本实验的 token 选择、P 算子、独立随机状态、排名前缀和 attention 测量。先做接口和数值兼容核对，再决定使用 vLLM 适配或 HF decode 编译；不在运行中静默切换后端。不再仅凭固定缓存或更多线程宣告完成优化。

## 最终操作状态及后端核对补充

恢复监控持续 201.28 秒，进程持续存活，原子提交从 358 增至 366；没有新增基础设施异常。随后用户要求停止零碎修复、确定方案后整体修改，正式队列排空至 **374/2632**，0 个在途请求，GPU 已释放。最后状态为 paused，不是完整实验结束或加速目标通过。

补充核对发现，历史本地 vLLM 配置明确 `enforce_eager: true`，RQ3.21 请求并发为 36。因此旧 vLLM 高利用率不能归于 CUDA Graph，且不能忽略与当前八并发的负载差异。本机 vLLM 的 Qwen3_5 类还明确禁止原生多模态剪枝的 `recompute_mrope_positions` 路径；仅注册模型类不意味着实验 token 操作直接兼容。

统一后端改造方案已保存为 [RQ4_3_Inference_Backend_Overhaul_2026-10-11.md](../experiment_plans/RQ4_3_Inference_Backend_Overhaul_2026-10-11.md)。该方案以成熟引擎合批为目标，逐项列出科学算子与输出/测量的适配要求；目前仍是方案和源码核对，未实现或激活新后端，不新增 smoke 额度。
