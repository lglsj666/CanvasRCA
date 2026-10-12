# RQ4.3 统一 vLLM 后端 v13 部署记录

2026-10-11。用户明确要求跳过本次 GPU smoke，部署后直接恢复全量。启动前已有 374/2632 个原子提交，保留全部结果及 8 次先前基础设施中断。此记录是运行改造审计，不是科学结果报告。

## 改动及不变量

以单个 vLLM 0.24.0 AsyncLLM 取代八个独立 HF generate 循环；所有剩余 arm 共用同一引擎。CPU 保持八个独立物理核 worker，RAM/tmpfs 有界预取，GPU 最多八个请求。原队列 2632 个位置与 2595 个独立请求、评分、候选、图像、提示、选择和 P 算子定义保持原样。冻结的完整队列 SHA256 为 b960ba11a32d33e9f94fa0038a38c3e7dc4f5efc68fc8d9bd852f0aa0db01c76。

模型仍为本地 Qwen3.8-27B（实际 Qwen3_5 架构）、BF16、无量化、40960 context、8192 输出、0.75 显存预算。两种原始 EOS 均显式保留。原排名前缀 greedy、后续 temperature=1/top-p=.95 保留；抽样使用 vLLM 的独立请求随机流，不宣称与 HF 同 seed 逐字相同。后端版本和实现身份随结果保存，时延分版本报告。

RQ 隔离 worker 扩展保留视觉 token 的选择、顺序、原始三轴 MRoPE 及文本延续位置；从引擎已加载权重构造视觉/文本嵌入，再以 CPU RAM tensor 交给同一引擎。GPU→RAM→GPU 的传输开销计入实际时延。前 3 个 GDN 层只混合登记的 prefill 输出，不改变原生递归状态；第一个 full attention 层保留原投影/门控，同时实现登记分支与被动 attention。原生引擎拥有批内缓存和 decode。

当前 enforce_eager=true，不启用 CUDA Graph、prefix caching 或 chunked prefill。选择完整 prefill 是为保持登记算子的语义；本地 vLLM 对该架构关闭 chunked prefill 有非官方支持警告，适配器对拆分或重放 prefill 显式失败，不静默降级。启动与正式运行应检查此限制。

## 已完成检查

- 静态通过，功能源码 4395 行；启动资格绑定当前源指纹。
- 14 项离线测试通过：辅助算子与独立参考、线性状态、批内请求隔离、动态批次排名处理、RAM 背压、原子提交、恢复/引用。
- 43 份真实输入通过，覆盖三个数据集、全部运算类型、RCA/QA、ORDER、实际 attention 几何及长文本。原 gather 与三轴位置逐值一致，最长被核对输入未超过上下文。
- 475 个保护文件哈希保持不变，包含已有 374 个提交、Codex、renderer、历史算子与 attention 模块。
- GPU smoke：按用户明确授权跳过；真实模型数值等价未单独测试，不能写为通过。正式启动监控另行记录，不伪装为 smoke。

资格文件：`RQs/RQ4_3/results/deployment_v13/{static,offline_checks,consistency,gpu_waiver,activation}.json`。原始离线失败与修复日志保留，未消耗模型调用。

## 运行状态

统一队列于 2026-10-11 19:57 UTC 首次启动，加载器格式校验失败；第二次在无 nvcc 环境下的 FlashInfer 采样预热失败。两次均发生于模型请求之前，没有增加诊断调用。已修正插件字符串为模块:类名，并关闭需要编译的 FlashInfer 采样器，使用原生独立种子采样；FlashAttention 和 FLA 保持启用。随后通用 RPC 未保留嵌套 tensor 类型，7 次已登记尝试失败于编码前；修复为显式二进制封包，实际 Msgpack 往返核对保持 dtype 和逐值一致。恢复过程又被缺少逐尝试修复凭据拦住，没有新增调用；已补齐版本绑定凭据，旧基础设施失败行保留。实际原生路径随后发现 xgrammar JSON 特征预检查拒绝 uniqueItems，以及 GDN 的 16 个 Q/K 头与 48 个 V 头布局不同。已使用原 schema 编译的 EBNF，并补齐与原 HF 相同的 Q/K 重复映射；新增数值及原生验证器检查通过。当前启动主进程 PID 399377。累计账本在此启动前为 374 complete、14 infrastructure_failure、9 interrupted，原记录均保留。启动监控进行中，尚不声明持续吞吐或 GPU 利用率达标。权威状态为 `RQs/RQ4_3/results/formal_v7/progress.json`，异常会保存 BLOCKED 并排空；断点恢复只依据原子完成标记跳过已提交位置。

## 加速依赖核对

本环境 vLLM 0.24.0、Torch 2.11.0、FlashInfer 0.6.12；没有单独安装 flash-attn，也没有独立 vllm-flash-attn distribution。实际 FlashAttention 来自 vllm/vllm_flash_attn，启动已选择 FLASH_ATTN（version 2）。不额外安装或替换 CUDA/torch/flash-attn；已有两个包同环境不必然冲突，二进制版本不匹配才是主要兼容风险。参考[官方 GPU 安装说明](https://docs.vllm.ai/en/stable/getting_started/installation/gpu/index.html?device=cuda)。当前环境没有修改。

## 启动观察完成与交接

2026-10-11 20:19 UTC：首个新增提交后连续观察 180.10 秒，累计提交从原有 374 增至 405；随后只读审计快照为 410/2632。没有新增基础设施失败，原有 14 个基础设施失败和 9 个中断仍保留在账本。最大真实 decode batch 为 8，CPU 八个独立物理核 worker 持续准备，RAM 缓冲有界。正式进程保持运行，交给用户监控。本次没有新增 smoke 调用。

观察窗口的 91 个 GPU 采样均值为 **82.43%**。这是启动后短窗口，仍包含首次形状编译的影响；未达到此前接受的 85.58%，不宣称长期利用率达标，也不由该窗口推算全量完成时间。启动观察通过仅表示该区间持续提交且无新增基础设施错误。

首批 36 个 v13 提交中，31 个正常返回、5 个模型无效回答；后者按登记协议保留，不重答。P_LOCAL_BI 及对应控制记录 3 个分支、P_SOFT_IMAGE 记录 1 个、P_DUAL 记录 4 个、普通条件记录 0 个，与登记路径对应；输入长度验证通过。此前 43 份 CPU 输入逐值核对保留 token gather、顺序与三轴位置；这些证据不等同于完整真实模型的 HF/vLLM 逐层数值等价验证。

同一快照有 12 个要求 attention 的提交，全部找到实际记录、sample_count=2、文本/图像/其他质量之和在容差内；attention_error=null、attention_missed=0。实际每记录 **793–801 字节**，分别保存首个 full-attention 层末 prompt query 与首 decode query 的区域摘要。每调用 64 KiB 硬上限不变；包括每调用 4 KiB 索引/目录预留、32 MiB 共享预留及队列/临时副本的每万次保守上界为 **730,464,256 字节（0.730 GB）**。此限制仅指 attention 增量记录，不包含原本就保存的 dashboard、输入及模型回答；不保存完整 attention 矩阵或 Q/K/V。

原始证据：`RQs/RQ4_3/results/deployment_v13/startup_monitor02.json`、`live_audit.json`。后续进度以 `formal_v7/progress.json` 为准；本记录不替代完整科学结果报告。
