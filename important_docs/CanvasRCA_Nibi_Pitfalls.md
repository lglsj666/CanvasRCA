# CanvasRCA Nibi 踩坑记录

> 更新日期：2026-10-20。本文在 **Nibi** 上维护；记录已知历史失败、原因、修复与实际验证状态。它不是 GPU 通过凭据。
>
> **当前结论：RQ4.5 的完整 CPU 资格已通过；GPU smoke 尚未完成干净资格，正式实验尚未启动。** 累计旧账本保留 42 次尝试（10 complete、26 infrastructure failure、6 interrupted），原逻辑 smoke 的 18 个位置中 10 个已提交。不同配方的通过凭据不得混用。2026-10-20 本次修复尚未新增语言模型生成调用。

## 1. 工作位置、证据与判读规则

本记录所在仓库为 `/home/lglsj/CanvasRCA_20261018`，部署分支 `nibi-deploy-20261018`。这是当前 Nibi CanvasRCA worktree，本文实际路径为 `/home/lglsj/CanvasRCA_20261018/important_docs/CanvasRCA_Nibi_Pitfalls.md`，不是本地 WSL 仓库，不需要在 worktree 下再创建一层 `CanvasRCA_nibi`。

- Nibi 远端主机：`l1.nibi.sharcnet`；连接入口 `nibi.alliancecan.ca`。
- 可删运行准备/测试缓存：`/project/def-jacobsen/canvasrca_cache/RQ4_5/`。
- 当前 CPU/资格材料：`/project/def-jacobsen/canvasrca_cache/RQ4_5/cpu_v1/`，下文简称 **RESULTS**。
- 永久正式结果：`/project/def-jacobsen/canvasrca_exp/RQ4_5/exclusive_spatial_v1/`。目前不得把目录存在解释为正式调用已经发生。
- 模型：`/scratch/lglsj/CanvasRCA/models/Qwen3.8-27B`。配置名沿用原实验，模型身份以冻结文件清单和哈希为准。
- 当前已核验运行环境：`/project/def-jacobsen/canvasrca_cache/RQ4_5/runtime_env/infer_20261019_v2/`。

### 主要历史证据

1. [RQ4.5 CPU 完整资格报告](../docs/experiment_reports/RQ4_5_CPU_Qualification_2026-10-19.md)、[机器资格凭据](../RQs/RQ4_5/findings/nibi_cpu_qualification.json)。
2. [RQ4.5 唯一 findings](../RQs/RQ4_5/findings/exp_exclusive_spatial_findings.md)、[RQ4.5 实验定义与修订](../RQs/RQ4_5/descriptions/RQ4_5_experiments.md)。
3. [RQ4.5 Nibi 环境与性能调查](../docs/issues/RQ4_5_Nibi_Runtime_Investigation_2026-10-19.md)。
4. [RQ3.8 Nibi 启动调查](../docs/issues/RQ3_8_nibi_startup_2026-09-29.md)、[开发日志](../devlog/CONSOLIDATED.md)。
5. RESULTS 下原始 `qualification/`、`runtime_profiles/`、作业日志、冻结请求、原子完成标记和 SQLite 账本，以及 Slurm `sacct`。部分早期日志可能因用户既有清理要求不再保留，本文只记录仍可由上述材料核实的事实，不补造缺失日志。

### 每个问题的记录要求

记录 **现象 → 证据/job ID → 已确认原因或待验证假设 → 修复 → 实际验证 → 仍有限制**。以下规则适用于本记录中的全部条目：

- `COMPLETED / exit 0` 不等于资格通过；还要检查业务报告、真实调用、输出及完整产物。
- `PENDING`、取消前未分配、环境检查、特征提取，都不算已完成 RCA 调用。
- 失败、超时、中断、原始输出和已经耗掉的调用必须保留；不能重新计数为零。
- 小张量正确、processor 一致、数值一致、实际推理可用、吞吐达标，是不同检查，不能互相替代。
- 旧状态保留为带日期的历史；新记录明确哪些资格被复用、哪些真正重跑。
- 不从无响应 SSH 推断实验已经停止，不从无日志推断没有提交；恢复后先查 `squeue/sacct` 与提交凭据。

## 2. RQ4.5：CPU 回归失败及修复

### CPU-01：原生边际图不能承担整组事实移交

- **现象/证据：** 第一批 unit/preflight 分别为 24540055（通过，约 50s）、24540056（通过，约 3m48s），population 24540057 失败（约 11m50s）。v1 全量 220 例中 93 例通过，122 例图像容量失败，4 例没有可移交内容，另 1 例关系端点解析错误。小样本通过没有覆盖全量布局容量。
- **修复：** 在 unified renderer 的新增 `trace_joint.complete_marginals` 中消除重复的逐样本轴/布局开销、修正行高，保留原精度样本、配对、统计及必要标签；没有用旧的两个边际分布冒充完整配对信息。
- **验证：** v2 unit 24544495（通过，约 31s）、preflight 24544496（通过，约 3m07s）、population 24544497（约 8m24s）完成；22 个 unit、6 个边界和 220 例 population 通过。后续 CPU v4 资格明确继承未经改变的输入和 population 证据。
- **教训：** 组件完成、固定例图可画与全量实际容量通过不是一回事。

### CPU-02：operation-bound 关系端点解析错误

- **现象：** 第一轮 population 有一例端点名称同时包含操作身份，简单实体解析导致错误。
- **修复：** 按公共来源的实体/操作字段区分端点，不通过字符串猜测或去重吞掉关系。
- **验证：** 已纳入后续边界与完整 population 通过；没有更改候选或私有根因信息。

### CPU-03：四例无可移交事实不等于渲染失败

- **现象：** 四例公共数据本身没有符合移交规则的诊断来源，不能造空图或伪造观测。
- **处理：** 按登记的共同残余输入记录数据不适用/回退，保留全分母及引用身份。纯视觉臂的证据仍在其完整图中，不能把 hybrid 的数据适用性回退扩展成纯视觉文本兜底。
- **验证：** population、请求和回退清单已进入通过的 CPU 资格。
- **限制：** 数据适用性与容量/代码错误必须分别报告，不能用前者掩盖后者。

### CPU-04：population 通过，但总体 token 成本门槛仍失败

- **现象：** v2 的 population 和上下文容量通过，不代表平均成本通过。AegisLab / H_TOPOLOGY 相对 T_FULL 的平均输入比为 **1.0130625**，未达到登记的低于强文本要求。后续机制作业 24544498 被取消。
- **修复：** 合并约 520 token 的重复、非诊断性公共读图说明；没有删除诊断文本、变更数值或移交事实。接口措辞修订被显式登记。
- **验证：** 最终凭据中该比率为 **0.9909024992**；三个数据集的三个 hybrid 臂平均输入均低于 T_FULL 与 MARGINAL_FIVE。v3 24545452 在进一步修复期间取消，不能误记为一次完整成功。
- **教训：** 必须计算实际完整请求的文本、全部图像、边界及格式说明，不看单张图或局部字符串长度。

### CPU-05：多图 attention 的页眉/区域归属错位

- **现象：** v3 的事实、预算和运行检查已经通过，但多图 attention 区域映射将页眉错误归属。这会污染后续 attention 分析，不等于模型输入事实错误。
- **修复：** 修正每张图独立的页眉和区域映射；不改变已冻结像素、processor 张量、gather、token ID 或 MRoPE。
- **验证：** CPU v4 **24546402 COMPLETED / 0:0，4m45s**：27 unit、30 runtime probes；实际四图新旧输入逐项比较通过。220 例、1320 RCA 请求与 198 QA 请求的此前合格载荷被明确复用，非重新推理。
- **冻结：** 139 个来源/配置文件，27 个模型/processor 文件（55,582,674,402 bytes）有哈希凭据；CPU 资格 execution fingerprint 为 `64676ea19b7d0f6d98c6d39e6bc3eeb33b70a3514f9798fe134295c87eb74879`。
- **限制：** 该资格证明 CPU 输入和测量映射，不证明 GPU 数值、真实回答、输出成本或吞吐。

### CPU-06：避免为操作性修复重复全量回归

- **问题：** 账本、时钟、共享环境或被动映射的小修复如果触发重新处理 220 例，会浪费大量时间；反过来，仅宣称“旧测试有效”而不核验影响范围也不合格。
- **做法：** 保存旧源/配方/请求指纹，比较实际影响的 AST 与载荷；不受影响的 CPU 检查显式标记 reused_with_proof，仅重跑受影响的账本、时钟、transport 或数值检查。
- **实例：** 24553260 只补账本及相关 unit；24585721 只做九份实际 processor 包的新旧环境一致性；当前完整编码器核验不重新准备遥测或重绘全量图。

## 3. RQ4.5：GPU smoke、环境和账本问题

### GPU-01：嵌套 srun 与 Slurm auth 插件版本不匹配

- **作业：** 24548141，FAILED / 1:0，约 5s；Python 和模型未启动。
- **原因：** `srun` 二进制与认证插件版本 25.11.8 / 25.11.9 不一致。
- **修复：** 在已经分配的 batch cgroup 内直接执行当前驱动，移除多余嵌套 step；不是重新申请 GPU 或更改模型。
- **验证：** 后续作业已进入模型启动，说明原 step 错误不再阻塞；这不等于后续 smoke 通过。

### GPU-02：隐藏的较短时钟在环境/JIT 启动期间耗尽

- **作业：** 24549086，FAILED / 124:0，约 10m17s，0 个生成调用；24553470 后来也被旧时钟终止。
- **原因：** 原内层约 10 分钟窗口短于实际 15 分钟 Slurm 分配，且首次 FlashInfer GDN 编译占用了启动时间。
- **修复/权限：** 用户已明确移除短时钟，后续 smoke 使用完整 **900s / 15min** 窗口。历史原始 clock 文件保留，不回写伪造成新时长。
- **验证：** 用户取消了额外 CPU 时钟作业 24554294，并明确豁免这项小修复的重测；后续续跑按新窗口执行。这里历史短时钟仅用于解释失败，不是当前规则。
- **限制：** 窗口变长不会解决实际在线内核慢的问题，不能用 timeout-only 标记通过。

### GPU-03：首次 FlashInfer 编译无界并发、缓存落入 home

- **证据：** 模型权重加载约 37s，并非全部启动时间；进程跟踪显示 Ninja 并发未限制、首次 GDN SM90 模板编译写入 home 缓存。
- **修复：** 将这项既有依赖的编译提前到 CPU 分配，`MAX_JOBS=8`；使用项目目录持久缓存。不能让昂贵 H100 分配等待首次重复编译。
- **作业：** 初次 CPU 编译 24549904，FAILED / 2:0，约 13s；并非内核本身编译失败，见下一条。修复后的 24550313 COMPLETED / 0:0，775s。
- **教训：** runtime 首次 JIT 和 telemetry preparation 都应提前，但前者是环境缓存，不是科学输入或模型输出。

### GPU-04：项目目录别名导致安全路径检查误拒绝

- **原因：** `/project/6006115` 与 `/project/def-jacobsen` 指向同一实际目录，guard 用未规范化字符串比较，拒绝合法编译缓存。
- **修复：** 两端先做 canonical realpath，再检查允许根目录；不能简单删除路径校验。
- **验证：** 24550313 成功编译相同 Ninja 图。

### GPU-05：搬走二进制缓存不代表 FlashInfer 会复用它

- **原因：** 生成 Ninja 图包含绝对路径；仅搬文件或 symlink 可能触发再次构建。一个“已存在 .so”不足以证明运行时命中。
- **修复：** 通过该版本支持的 `flashinfer_jit_cache.get_jit_cache_dir()` 提供已生成的同一二进制，不更改 site-packages 或替换模型计算。
- **证据：** 原始与发布的 `gdn_prefill_sm90.so` SHA-256 均为 `8be70538b629d46a1745332113b616732ac9feb33f3cad79d05675ad29b25a8a`。
- **作业：** pending round3 / 24549987 在未分配时取消，0 调用；24552318 后续实际初始化时大型编译没有重现，权重约 51.1GiB，engine init/profile 18.73s。
- **教训：** 保留当前 RQ4.5 自定义 worker、逐图 post-merger gather、MRoPE、KV admission、结构化排名和被动 attention；旧的 plain HTTP 启动器不能直接替代它。

### GPU-06：NFS 上 SQLite 多连接/WAL 造成账本锁停顿

- **作业：** 24552318，CANCELLED，约 6m59s。模型已加载并启动请求，但约 150s 无进度，尚无答案完成提交。
- **已确认观察：** 父进程在 NFS `rpc_wait_bit_killable`，先是 `fcntl(F_SETLK)`，后是 `close`；并发账本连接反复开关。
- **修复：** 一个进程级 owner/flock、一个持久 SQLite 连接、线程内 RLock、DELETE/FULL durable journaling；在独占 owner 的约束下使用 SQLite URI `nolock=1`，不改成 RAM 记账、不推迟预留提交。
- **验证：** CPU-only **24553260 COMPLETED，46s**；29 unit 通过；8 个并发生产线程在实际项目挂载上完成 36 次持久事务，1.3037s。另有 duplicate owner、真实进程终止、hot-journal 恢复、引用/重复检查。
- **保留：** 旧 WAL/database/shm 字节及所有已耗 attempt 原样保存；退出确认后才分类 interrupted。不允许删除账本重新开始。

### GPU-07：部分成功不代表整个 logical smoke 通过

- **Round5 / 24553470：** FAILED / 0:9，约 10m26s；5 个回答已原子提交，8 个已启动请求未完成。
- **Round6 / 24554682：** TIMEOUT，约 15m09s；当轮 11 次新增尝试，3 complete、8 timeout，还有 2 个位置从未启动。跨 round5–6 合计 8/18 个位置有完整回答，旧 lifetime ledger 当时 32 次尝试。
- **审查：** 新的 3 个输出与冻结输入、PNG、评分、token/attention 和 commit 记录一致；不是错误输出丢失，但其余 10 个位置仍未通过。
- **处理：** 用户先关闭续跑，后明确重新授权串行新轮；不把重新授权倒写成旧轮通过，不把已提交错误答案重新生成。

### GPU-08：将在线慢全部归咎于 CPU preparation 或 import

- **实测 round6：** 首次新调用前启动 238.337s；剩余 661.663s；3 个新完成调用约 **0.200/min（含启动）**、**0.272/min（首个请求后）**。它是小批、超时删失结果，不是正式稳态估计。
- **实测拆解：** 已完成请求 CPU packet prep 仅 1.34–1.58s；worker encode/transport 为 13.765、17.718、116.792s。语言区间 47.731–534.532s 包含 admission、排队和 finish RPC 等待，不能直接称为纯 decoder 时间。未观察到 KV preemption，实际 decode batch 最高 4。
- **结论：** 需要分别测启动、视觉编码、worker RPC、prefill/decode，不能为了“加速”重做已完成的全量 CPU 输入准备。
- **当前吞吐门槛：** ≥7 个实际完成调用/min；引用结果不计完成调用数，冷启动与 online 分开报告。历史本地 RQ4.4 为 840 / 6252.56s = 8.06/min，硬件、软件和输入不同，不能直接当同期 Nibi 对照。

### GPU-09：环境变量与 module 初始化路径被启动器覆盖

- **现象：** worker 导入开销大；CPU 作业继承的 `LOADEDMODULES` 与 GPU 环境不同，重写 PYTHONPATH 可丢失 module 初始化路径。
- **修复：** runtime loader 显式 `module --force purge`，加载 StdEnv/2023、Python 3.11.5、CUDA12.9、Arrow18.1.0、OpenCV4.13.0，再激活已合格环境；保留/恢复正确 module 路径，不堆叠别的机器环境。
- **同时处理：** 移除非必要 `VLLM_TRITON_FORCE_FIRST_CONFIG=1`、`CUBLAS_WORKSPACE_CONFIG`、`CUBLASLT_WORKSPACE_SIZE` 的强制覆盖。第一个变量会跳过正常调优，但不能仅凭源码就断言它造成全部变慢。
- **验证：** 24585258 primitive/import profile COMPLETED / 0:0，2m16s，0 生成；24587191 import qualification 通过（见 GPU-11）。

### GPU-10：缓存预热与固定测试顺序混淆环境变量效果

- **24585258：** 同一个旧环境的三个顺序进程 import 分别 **88.03、21.12、18.42s**；代表性 BF16 GEMM 0.817/0.813/0.813ms，Flash SDPA 1.287/1.287/1.288ms。
- **判读：** 文件缓存逐步变热，不能声称改 flag 就把 import 加快近 5 倍；GPU 原语正常也不能证明完整 encoder 正常。
- **保留：** 原始 paths/versions 在 `RQs/RQ4_5/findings/nibi_runtime_profile_24585258/`，不是只留一句“环境没问题”。

### GPU-11：Alliance wheelhouse 缺精确旧版本，包 metadata 与实际导入不一致

- **24585280：** CPU 环境构建 FAILED，约 1m48s；NumPy2.3.5、SciPy1.16.3、XGrammar0.2.3 的精确 pins 不在当前 wheelhouse。依赖的 24585461 被取消，未继续盲等。
- **24585572：** 后继构建最终 FAILED，约 25m；停止于 dependency metadata 检查，不等于所有已安装包无法导入。
- **修复：** 可用包使用精确 Alliance wheel；缺失的三个版本按已安装 RECORD 逐文件复制并验证 SHA-256，不伪造版本。实际旧 PIL 为 Pillow12.1.0，另有 stale Pillow-SIMD metadata；OpenCV 采用匹配 module 与 Alliance placeholder wheel，不混入外部二进制。
- **验证：** 24587191 COMPLETED，86s，实际导入位置和两项 metadata warning 保留；24585721 COMPLETED，200s，**九份真实 processor 包张量及 metadata 新旧逐字节相同**。
- **限制：** 不能用 `pip check` 的告警反推模型数值错误；也不能只看导入成功跳过 processor 等价验证。

### GPU-12：诊断 profiler 会污染吞吐测量

- **Round7 / 24585685：** TIMEOUT，约 15m24s；保留原有 8 个答案，新增 10 次尝试、2 个回答、8 个 timeout。原 logical smoke 达到 10/18，lifetime 42 attempts = 10 complete + 26 infra failures + 6 interrupted。
- **作用：** 首个 encoder/prefill 的 profiler 找到瓶颈；该轮明确只用于诊断，不具备最终吞吐资格。
- **后续要求：** 性能门槛必须使用关闭 profiler 的正常运行路径，不能用被采样干扰的时延宣称实际部署速度。

### GPU-13：H100 上 FA3 / head_dim=72 的极慢视觉内核

- **真实 profile：** 27 个 vision blocks、16 heads、head_dim72；首个实际 encoder 的 FA3 self GPU time 17.078s，约占已记录 GPU 时间的 99%；GEMM self time 仅 51ms。大图后续编码 **115.92–117.29s**。
- **24586776：** BF16、8192 patches 的独立原语：FA3 **71.34–72.69ms**，Torch Flash SDPA **1.38–1.42ms**，预设原语误差标准通过。但同 job 试 FA2 后失败（见 GPU-14）。
- **24586861 COMPLETED / 0:0，44s：**

| Patch 数量 | 原 FA3 秒/block | Torch Flash SDPA 秒/block |
|---:|---:|---:|
| 8,192 | 0.07079–0.07272 | 0.001383–0.001417 |
| 45,824 | 2.13689–2.13705 | 0.03898–0.03925 |
| 65,160 | 4.31906–4.31919 | 0.07938–0.07954 |

- **结论：** 4.319×27≈116.6s 能复现大图量级，支持将这个 native 路径识别为主要瓶颈；这不是宣称完整流水线可以加速 50 倍。
- **本地差异：** 本地 SM120 Blackwell 与 H100 SM90 的默认 flash 分支不同；没有本地同口径 profile，所以不能将全部硬件差距归因于单个分支。不得因此修改正在运行的本地 RQ4.7。

### GPU-14：安装的 FA2 二进制不支持当前 PTX 工具链

- **作业：** 24586776，FAILED，约 17s。
- **现象：** CUDA unsupported-PTX-toolchain，出现在 FA2 路径，不是已经完成的 FA3/SDPA 原语比较全部无效。
- **处理：** 后继 24586861 排除 FA2。发生 CUDA 错误后不继续信任同一上下文，也不反复提交同一个已知不支持的二进制。
- **2026-10-20 自查：** 新探针草稿再次包含 FA2，是没有充分利用历史失败记录的实施错误；已在 **24686204 分配前**取消该 pending 草稿，改为仅测试 FA3 的 72→96/128 对齐候选，未为这个重复方向消耗 GPU 或生成调用。

### GPU-15：每次 GPU 分配复制整个环境，反而卡死启动

- **24586948：** TIMEOUT，约 15m12s，0 生成、没有完整数值结果。约 13 分钟时，`cp` 在 uninterruptible file-read wait，Python/model 尚未进入。
- **原因：** 把“本地存储有时更快”的一般建议落实成每次无条件复制整套小文件环境，引入了新的 I/O 瓶颈。
- **修复：** 直接激活已核验的项目持久环境；不在 H100 计费窗口重复 bulk copy。
- **验证：** 后继 24589226 可完成三例模型特征比较，说明该启动阻塞已消除；候选本身数值仍失败，见下一条。

### GPU-16：原语差异很小，完整 encoder 的差异却超门槛

- **作业：** **24589226 FAILED / 1:0，6m05s**。0 语言生成。
- **候选：** vLLM native `mm_encoder_attn_backend=TORCH_SDPA`，相同真实图像、BF16 权重、位置、完整 encoder，不改 token 选择。
- **预注册门槛：** relative RMS≤0.01 且 cosine≥0.9999，不因看见结果而放宽。

| 固定实际包 | FA3 / SDPA 完整视觉时间（s） | Relative RMS | Cosine | 结论 |
|---|---:|---:|---:|---|
| AIOPS-2022 / V_DOMAIN_FULL | 117.51394 / 2.36110 | 0.0357843 | 0.99936008 | 不通过 |
| AIOPS-2025 / H_TOPOLOGY | 2.9430 / 0.08204 | 0.02275645 | 0.99974108 | 不通过 |
| AegisLab / H_TOPO_MARGINAL | 6.30716 / 0.163378 | 0.01753839 | 0.99984616 | 不通过 |

- **根因边界：** 已确认完整特征超门槛；具体误差在各层如何积累尚未证明。不能仅凭原语测试宣称两条整网路径无损等价。
- **处理：** 不采用 SDPA 候选，不运行依赖它的冻结/正式启动。进程退出的 `AsyncLLM.__del__` NoneType 警告是次级 cleanup 现象，不是导致数值资格失败的根因。
- **证据：** `RESULTS/qualification/visual_backend_equivalence.json`、`RESULTS/runtime_profiles/visual_backend_24589226/comparison.json`，及 cache 下对应 out/err。

### GPU-17：afterok 失败导致子作业永久 pending

- **链：** 24589226（数值失败）→24589420（runtime-freeze，DependencyNeverSatisfied）→24589619（register-smoke，Dependency）。用户看到的 pending 不是 GPU 忙或 slow startup。
- **处理：** 2026-10-20 保存两 job 的 `scontrol show job` 到 `cache/runtime_profiles/blocked_dependency_20261020.json`，取消两个尚未执行的子作业。没有直接绕过数值门槛提交 smoke。
- **后续设计：** 控制作业若采用 afterany，仍必须读取父作业状态和 source-bound 资格；失败只写 blocked 并不发起 GPU。若采用 afterok，监控发现 failed parent 必须主动收尾 pending 链，防止误报“仍在推进”。
- **代码修复：** 后续 smoke review 已改为 afterany + 显式核对 sacct 的 COMPLETED/0:0；父失败时只写终态 blocked 记录并结束，绝不发起模型或正式任务。shell/嵌入 Python 静态检查通过；新 smoke 尚未提交，不能声称已完成实际调度验证。

### GPU-18：零填充 attention head——96维数值通过，但没有解决速度

- **思路：** 保持同一 FA3，将每个 vision head 的 Q/K/V 最后维由 72 补零到 96 或 128，保留 **原始 scale=1/sqrt(72)**，输出裁回 72；数学 dot product 与模型参数不变，但 kernel 的 BF16 舍入结果必须实测。
- **实现边界：** 仅远端 RQ4.5 资格探针；不改 site-packages，不改 language attention，不改本地代码，也不直接部署进正式 worker。
- **作业：** 草稿 24686204 未分配即取消；替代 **24686266** 提交，测试 original_fa3 / fa3_pad96 / fa3_pad128 三条路径；0 语言生成。
- **资格：** 继续沿用相同三份实际包和 RMS≤0.01、cosine≥0.9999；保留每个候选失败结果。只有全部通过的候选才可按完整 encoder 总耗时选择。小张量零填充恒等检查与脚本静态检查已通过，GPU 结果待定。
- **状态：** 本段创建时 job 排队。若数值通过，仍需要前向冻结、正常 18-call smoke、实际产物审查及≥7/min 的测量，不能自动视为正式运行资格。
- **运行中观察：** 24686266 后续在 g6 分配运行。一次只读同分配快照为 GPU 100%、68,575MiB、P0、1980MHz，engine 进程为运行态；driver 等待 RPC。这次快照支持“内核仍在计算”，不支持把没有中间日志直接判断为 NFS/环境卡死，也不构成吞吐通过。新探针今后应按每个候选立即保存进度，避免只在完整三路径结束后才写第一行。候选即使数值通过，若实测完整 encoder 不快于原路径，也不花生成 smoke 额度去重复确认已知变慢。

### GPU-19：新的完整核验结果不能被“passed”字段误导（2026-10-20）

- **24686266 COMPLETED / 0:0**；总探针约694.84s，0生成调用。96维候选在三份完整encoder特征上 `max_abs_error=0`；128维候选三例均超原数值门槛。

| 实际输入 | 原FA3（s） | pad96（s） | pad96误差 | pad128（s） | pad128 relative RMS |
|---|---:|---:|---|---:|---:|
| AIOPS-2022 / V_DOMAIN_FULL | 117.4426 | 115.7724 | 逐元素相同 | 141.7167 | 0.032920 |
| AIOPS-2025 / H_TOPOLOGY | 2.8562 | 2.7157 | 逐元素相同 | 3.2426 | 0.028793 |
| AegisLab / H_TOPO_MARGINAL | 6.2958 | 6.2804 | 逐元素相同 | 7.6491 | 0.017652 |

- **判读：** 机器报告的 `passed/selected=fa3_pad96` 仅表示数值选择资格。三例总时间126.595→124.769s，单轮约1.44%的差异不足以证明稳定加速，大图核心瓶颈仍在；不能据此宣称≥7calls/min，也不需要再花18次生成去确认它仍然很慢。
- **处理：** 暂不采用这个生产补丁，不提交新smoke、不重跑已经通过的population CPU。现有BF16权重、CPU冻结输入和生产配方均保留。已准备的严格前向冻结脚本没有执行。
- **证据：** `RESULTS/qualification/visual_fastpath_equivalence.json`、`RESULTS/runtime_profiles/visual_fastpath_24686266/comparison.json`、`RESULTS/qualification/visual_fastpath_disposition_24686266.json`。累计生成attempt仍为42，没有因这次探针增长。
- **下一步边界：** 必须继续解决实际H100视觉内核路径，或经明确登记的资格修订处理后端数值差异；不能把未达到的原门槛写成通过。当前正式实验仍未启动。

## 4. RQ3.8：历史 Nibi 问题，防止在新实验中重犯

### H-01：跨主机 PNG 字节不一致与 silent rebaseline 风险

- **22921386：** 47 pass、1 fail、1 skip；失败为跨主机历史 PNG 字节比较。字体、bundle、CSS 和浏览器版本已经核对，确切光栅差异原因仍未查明。
- **22921513：** 验证同一 Nibi 冻结 reference 与 FULL 的精确相等，以及未变组件相等。跨主机差异单独记录，不用新图替换旧参考后宣称原检查通过。

### H-02：程序 exit0，但 processor 资格报告失败

- **22921513：** 作业正常退出，却出现 TEXT_DUP 输入 Qwen45,394 / Gemma47,453 token 的 context_exceeded。未保留足够输出空间，不能进入 GPU。
- **修复：** preflight 在业务报告失败时非零退出；保持 ALL_ID 事实、采样和模型长度，只用显式登记的可逆表/范围编码减少结构冗余。
- **22922052：** 58 regressions、三病例×八臂×两 processor 检查通过；后续全量 gallery 另有浏览器失败，见下条。

### H-03：Chromium 截图失败，被误当成算法或内存问题

- **22922052：** 全量 gallery 在 34/480 处，INC-9CE8985F3DCB / NO_ONSET 报 `Unable to capture screenshot`。峰值 RSS 约 5GiB，没有 Slurm OOM 证据。
- **修复：** 保留浏览器日志，仅对该精确错误允许一次 fresh-browser、相同输入重试；不吞掉其他验证异常。
- **22922484：** 19m45s，60 tests、24 processor checks 通过，480 gallery 完整持久化；已完成图复用，不全部重绘。

### H-04：遗漏 CUDA toolkit、nvcc 与 headers

- **22922720 等早期零调用 smoke：** `Could not find nvcc`、DeepGEMM CUDA discovery 等；权重加载约 21.99s（阶段约32.12s），profile/warmup292.01s。
- **修复：** 显式 module load CUDA12.9，与 Torch2.11 CUDA build 匹配；启动前检查 nvcc/headers/兼容性，不能把项目启动器遗漏说成 Nibi GPU/driver 坏了。
- **22923347：** 4m32s，61 tests 与 24 dual-processor checks 通过，全量图复用。

### H-05：硬件自动后端选择与持久编译缓存

- **现象：** H100 自动走 FlashInfer GDN SM90，旧本地/某些配置走 Triton；自动配置相同文字不代表相同实际内核。首次 GDN JIT 涉及 64 个模板实例。
- **修复：** 运行时专属、版本绑定的持久 Triton/vLLM compiler cache；原子 UUID 临时文件+os.replace；端口按 job 分配，不能通过 compiler cache 共享模型答案。
- **相关作业：** 22922720、22923667、22927066 都没有产生可审查的生成调用；其中 Slurm COMPLETED 也不算 inference pass。
- **当前启示：** 旧成功 job21217562 确实用 vLLM0.24.0 / BF16 Qwen3.5-9B / FA3 / 自动 FlashInfer GDN，完成约14,273s；但小模型、MIG、无当前 adapter，只有环境/cache 参考价值，不能整段照抄到 RQ4.5。

### H-06：旧内层时钟及 USR1 提前停止

- **现象：** 旧 smoke 内层窗口短于 30 分钟 Slurm；USR1@360 又可能把分配缩短到约24分钟。
- **处理：** 按当时用户授权修正各层停止控制，保留历史 clock；不是通过 timeout-only 宣称通过。当前 RQ4.5 规则是15分钟，不沿用这些历史短限制。

### H-07：端口不一致导致 live tokenizer preflight 失败

- **22930381：** 服务约395s后 ready，但 readiness/attestation 使用 job端口30381，client 的 `VLLM_BASE_URL` 却仍为8000，最终 live tokenizer preflight failed。
- **修复：** launcher、readiness、tokenizer和generation统一实际 endpoint；保存真实 HTTP 异常而不是 None；supervisor异常时写 failed，不留 running 假状态。随后 server 是 driver finally 清理，并非已证明 engine 自发崩溃。
- **22932223：** 分配前取消，不计为执行或生成失败。

### H-08：真实请求输出预留容量没有通过

- **22941413：** Qwen Aegis FULL 输入35,011，加8,192输出超过40,960；在 generation 前拒绝，不能因“模型支持40k”而忽略预留。
- **修复：** 保持原 PNG、固定文本/冗余视觉的比较定义，登记可逆公共 G 关系账本。输入35,011→27,769；66 processor checks通过，不删除事实或更改effect定义。
- **22942268：** 25m59s，18/18真实双模型 smoke 成功，PNG、conversation等完整审查。这个是有实际调用的通过，与早期零调用作业不同。

### H-09：rsync 未保留相对路径，输入被摊平到错误根目录

- **现象：** 漏 `-R` 使约31GB文件进入消费端不读取的根目录。不是“文件已传完就准备好了”。
- **修复：** 先验证原文件仍在，再删除仅这次新产生的错位副本；按 `-aR` 保持路径，适用时按 `-aL` 处理指向实际字节的链接。840份roster存在性核验 missing0 只证明路径存在，不替代全内容哈希或科学资格。

## 5. 跨实验运维问题

### OPS-01：SSH/MFA、tmux 与过期控制连接

- 登录超时或 control socket 存在但远端不响应，不代表作业仍正常，也不代表需要重提。
- tmux 内再次 attach 出现 `sessions should be nested with care`，是嵌套提示；按当前终端使用 switch-client，或 `TMUX= tmux attach -t canvasrca-nibi-login`。会话已经不存在时重新创建，再让用户完成 MFA。
- 仅用户交互处理 MFA，不保存口令、验证码、SSH key passphrase 或其他认证秘密。
- 重新登录后先核对 hostname、仓库绝对路径、分支、提交和 Slurm/提交凭据；不把旧会话中未返回的 sbatch 当作未提交而重复发起。

### OPS-02：home/scratch quota 与结果/缓存分区

- **已观察：** 2026-10-18 用户新增 worktree 时出现 `Disk quota exceeded`，部分文件创建失败，随后 cd 失败、命令仍在旧 checkout 运行。
- **根因边界：** 这是配额错误；未同时保留 byte/inode quota 输出时，不武断指定为哪一种额度。不能把 fetch成功误作完整worktree成功。
- **处理：** 永久精简结果写 `/project/def-jacobsen/canvasrca_exp/`，可删 preparation/test/runtime cache 写 `canvasrca_cache/`；不要在home复制模型与全量结果，也不把缓存挪到别处后宣称消失。
- **保留要求：** 输入/输出/完整对话/评分映射/调用账本/实际attention/来源配置完整且直接可读，去重后≤25GB/万次调用；attention≤1GB/万次。测试缓存与正式永久结果分开，不因清理破坏恢复依赖。

### OPS-03：远端工作不能擅自回读/回改本地实验

- **用户当前明确要求：** 只读取并修改 Nibi 上 `/home/lglsj/CanvasRCA_20261018` 的代码。本地 RQ4.7 继续运行，不读本地仓库、不改本地代码、不做双向同步。
- **实施方式：** 本机 shell 工作目录 `/tmp`；repo读取、写入、Slurm查询与提交均经 authenticated SSH 在远端执行。记录的路径和验证结果必须说明是 Nibi。
- **教训：** 不能因为本地 checkout 目录名字相似，就用其源码替代远端实际失败版本分析。

### OPS-04：本地 AsyncLLM 不需要远程 API key

- RQ4.5 的自定义 vLLM Python adapter 使用本机进程，不应凭普通 OpenAI HTTP 客户端默认行为索要公网key。需要保留当前 worker/token/attention 支持，不能为省事切成丢功能的旧 HTTP adapter。
- 若使用 HTTP endpoint，内部端口/服务认证与外部收费服务key要分清，日志不要输出任何秘密。

### OPS-05：吞吐、call、预算和冻结版本不可混淆

- ≥7calls/min 计实际完成生成，不计 exact-result reference，不把CPU准备条数当模型调用。
- 首轮启动、冷路径、online、正式1560-call摊销预测分别报告；预测不冒充正式测量。
- smoke修改环境/配方后要有前向source-bound身份；旧回答保留，新配方资格不能直接继承旧配方一半成功的smoke。
- 回答错误、非法候选、无效输出保留原始输出并按协议评分，不能作为基础设施retry理由；真正基础设施中断与已提交错误答案分开。
- 全量授权与CPU/GPU资格分开：当前用户已授权资格通过后跑Nibi正式RQ4.5，但此权限不使尚失败的GPU资格自动通过。

## 6. 当前资格状态与下一步

| 项目 | 截至本次记录的状态 | 可支持什么 |
|---|---|---|
| 220例CPU/完整来源/processor/geometry | 通过，有冻结与复用凭据 | 输入资格 |
| NFS账本目标回归 | 通过 | durable accounting/恢复检查 |
| 新旧运行环境九实际包 | byte-identical通过 | processor环境等价 |
| FA3/SDPA原语 | 通过 | 小张量/原语数值与速度 |
| native SDPA完整encoder | **失败**（24589226） | 不能采用该候选 |
| FA3零填充96/128完整encoder | 24686266完成；96维逐元素相同，128维超误差；大图仍115.77s | 数值通过不代表吞吐通过；未部署 |
| 干净18-call smoke | **未通过** | 尚不能宣称GPU运行合格 |
| ≥7 actual calls/min | **未达到** | 尚不能宣称吞吐合格 |
| 正式RQ4.5 | **未启动** | 已授权资格通过后执行 |
| 本地RQ4.7 | 不在本次操作范围 | 不读取、不修改、不干预 |

下一步先看零生成调用的实际完整encoder核验；若失败，保留证据再决定候选，不反复提交已知失败路径。若通过，按相同代码前向冻结，正常smoke，逐份审查真实输入、PNG、输出、评分、attention与账本，再据实判断正式资格。所有新问题继续追加到本文，不只散落在聊天或临时日志中。

本记录汇总可检索的历史问题，不声称已经保存缺失的完整attention矩阵、已经丢失的旧日志或尚未运行的测试结果。


### GPU-20: Continue FA3 dispatch diagnosis without repeating failed alternatives (2026-10-20)

The authenticated login remains usable and no user job was live at resumption.
The pad96 probe is retained as numerically identical but insufficiently fast.
Do not repeat unsupported FA2 binaries, unchanged SDPA full-encoder failure,
CPU population preparation, or production generation on the known 116-second path.

A new zero-language-call probe compares the same BF16 FA3 operator with explicit
num_splits=1/4 and a dense single-sequence dispatch. It preserves all Q/K/V values,
72-dimensional heads, scale, and the global noncausal attention domain. The dense
argument list is derived from the installed operator call, not guessed. Progress
is saved after each candidate. Static shell and embedded Python checks passed.
The primitive gate remains RMS<=0.01 and cosine>=0.9999; only a >=3x primitive
speedup motivates full three-case encoder qualification. No production adoption
or successful throughput is claimed. No local source was read or changed.

API basis: the installed vLLM flash_attn_interface.py exposes num_splits;
https://github.com/vllm-project/vllm/blob/main/vllm/vllm_flash_attn/flash_attn_interface.py .

- Submitted diagnostic job 24719764 (15 minutes, one H100, zero generation calls). All previous failures and 42 spent attempts remain.

- Initial scheduler check: 24719764 is PENDING / ReqNodeNotAvail, UnavailableNodes:u3, Dependency=(null), no allocation and no calls. This is allocation availability, not a repeated failed dependency or an observed test failure.


### GPU-21: Constructed AST was syntactically valid but lacked source locations (2026-10-21)

Job24719764 failed in55 seconds before any attention kernel or language generation.
The probe built ast.Expression(ast.Tuple(...)) from installed operator arguments,
but did not populate the new tuple node's source locations. compile raised
`TypeError: required field lineno missing from expr`. Shell and outer-source AST
checks had passed because they did not execute this dynamically constructed AST.
This was a probe implementation defect, not a model, numerical, or GPU failure.

The probe now calls ast.fix_missing_locations before compile. The exact installed
FA3 argument tuple was compiled and evaluated with placeholders, confirming all
37 arguments and the scale/causal positions. Shell and embedded source checks
also pass. Original failed source, logs and a repair receipt are retained under
runtime_profiles/fa3_dispatch_24719764. No production adapter, frozen input,
CPU qualification, model weight, or local file was changed. New GPU execution
is required to evaluate the candidate paths; this static repair is not a GPU pass.

- Repair successor submitted as job24724822; zero new language calls, original failed job retained.


### GPU-22: Dense FA3 is absent from this build (2026-10-21)

Job24724822 failed in49seconds, before language generation. The8192-token
original/num_splits1/num_splits4 varlen measurements all succeeded and remained
about71ms; dense_split1 raised `This flash attention build only supports varlen
(for build size reasons)`. This is an unsupported compiled interface, not an
observed CUDA memory fault. The probe incorrectly treated every host RuntimeError
as a poisoned CUDA context and stopped before its longer-length cases. Original
source/logs/results are retained. Dense is removed from the candidate list for
this known build; the near-identical short varlen results do not justify another
GPU allocation merely to retest a known slow branch. No performance pass is
claimed for the unexecuted long candidates.

### OPS-06: Separate platform stability from scientific feature reproduction

The2026-10-21 user requests reviewed smokes then exactly one two-hour full-queue
job, with timeout acceptable and these results not important scientifically.
This replaces the prior six-block12-hour launch scope. Native BF16 TORCH_SDPA
is selected for this explicitly operational scope: three actual full encoders
previously completed with finite outputs and large speed improvement, but did
not meet the old1%/0.9999 feature-reproduction gate. That failed qualification
remains unchanged and is not converted to passed. New requests use a distinct
backend recipe identity and fresh smoke answers; old answers/attention/ledger
rows remain. CPU input/geometry proofs are reused because actual diagnostic
inputs, gather, MRoPE, weights, BF16 and scoring are unchanged. Runtime smoke
and>=7calls/min must still be measured. No formal launch until clean artifact
review. All new platform results are excluded from scientific comparisons.


### CPU-07: Stale protected-policy digest blocked operational static checks

The first2026-10-21 operational static check stopped before submission because
Codex.md still had its original protected digest. Its entire actual diff was
verified against exact replacements for the user-authorized removal of implicit
600-second smoke limits and registration of900seconds. No other policy text
differed. This repair did not edit Codex.md: it updated only that entry in the
protection manifest. Original manifest/reports and exact diff proof are retained
in qualification/history_policy_guard_20261021. Generation recipe, runtime,
actual inputs and model dependencies are unchanged; CPU reports are carried by
source proof, not rerun. Static checks must pass before any GPU submission.


### OPS-07: All scheduler partitions down during administrator reboot

On2026-10-21 at21:18 Eastern, smoke24760027 was accepted with no dependency
and remained PENDING/PartitionDown. sinfo reported every CPU/GPU partition DOWN;
scontrol confirms State=DOWN, while many nodes show Auto Reboot ASAP -kb from
20:26. This is an allocation outage, not another smoke/code failure; no calls
have begun. The job is retained without duplicate submission. Offline artifact
review24760032 depends on afterany:24760027 and fails closed on a failed parent.
A remote lightweight monitor records scheduler state every180seconds independently
of SSH; no two-hour GPU job is submitted before clean smoke/manual review.


## PERF-08 — 2026-10-21: host concurrency did not equal GPU decode concurrency

Round 8 (job 24760027) completed all 18 calls and its 18 actual answers/artifacts were inspected. Online throughput was 3.9581 calls/minute. The engine reported only 79,725 KV token capacity (1.95 full-context sequences); complete input-plus-8192-output reservations admitted initially two requests and at most five later short requests, despite eight host requests. A sampled request waited 86.60 seconds for KV admission. There was no preemption or artifact failure. User lowered the target prospectively to at least 6 completed calls/minute. A separate operational profile will validate GPU allocation fraction 0.90 instead of 0.80; BF16, model weights, inputs, output limits, token operations and attention protocol remain unchanged. Round 8 below-target receipts and all spent calls are preserved. No two-hour job has been submitted.


## Operational monitor blocker — 2026-10-21

RuntimeError('Measured throughput below latest6/min target; no formal submission')
No additional smoke or GPU job was submitted automatically. See qualification/platform_qualification_monitor_latest.json.


## PERF-09 — 2026-10-22: larger KV capacity was insufficient for the throughput target

Round9 GPU24763295 and offline review24763332 both completed0:0. All18 new calls committed,12RCA plus6QA; every raw answer inspected and all6 collected attention files hash/coverage/mass verified. No runtime error or KV preemption. Operational0.90 allocation increased capacity to201,142tokens/274reservationblocks and actual decode batching reached8. Nevertheless full online timing was254.4418seconds (4.2446calls/min), below6. Startup to first reservation was487.0156seconds; allocation logical total741.4574seconds. CPU packet mean1.0635seconds and vision/transport mean1.5092seconds. Multiple first-use Triton JIT warnings occurred during inference; early language calls took110–181seconds and the final three short repeats21.5–29.3seconds. Their different shapes, batching and overlap prevent assigning all excess latency to JIT without a controlled measurement. One request still waited110.98seconds for full KV admission. This is functional/artifact success, not throughput success. The controller correctly stopped with no two-hour GPU allocation submitted. Original below-target timing and old failures remain unchanged.


## PERF-10 — 2026-10-22: explicit eager execution prevents native decode graph reuse

The operational configuration explicitly used enforce_eager=True, so native vLLM disabled CUDA Graphs. The preserved round7 profile independently shows substantial Python/native-op dispatch work; round9 also logs first-use Triton specializations during online inference. Neither observation isolates the entire throughput deficit. A forward runtime enables native FULL_DECODE_ONLY with no torch.compile, captures batch sizes1–8, and forces eager execution while any scheduled request still needs its registered last-prompt or first-decode attention query. After both summaries, ordinary decode may replay the original native graph. This preserves BF16/weights, complete prompts/pixels, post-merger selection, original MRoPE, sampling,8192output,8concurrency and all actual attention. Capturing/warmup remains in allocation/startup accounting and does not generate answers. Independent offline dispatch cases pass and full static passes (2139functional lines); all1518 requests were proven unchanged except explicit runtime recipe/identity. Full CPU evidence checks are carried with lineage, not rerun. Actual graph use, eager capture, memory safety and >=6 throughput remain GPU qualification gates. The prior failed strict native-encoder feature equivalence remains failed; the purpose remains platform integration only.


## Operational monitor blocker — 2026-10-21

RuntimeError('Measured throughput below latest6/min target; no formal submission')
No additional smoke or GPU job was submitted automatically. See qualification/platform_qualification_monitor_latest.json.


## PERF-11 — 2026-10-22: decode graphs ran, but the complete smoke still missed six calls/minute

GPU job 24770165 and offline review 24770166 completed with exit 0. Round 10
committed 18 new calls (12 RCA, 6 QA), with no references counted in throughput.
All 18 actual raw answers were read, compared with committed response strings,
and ended at a normal stop. The six attention files were independently checked
for hashes, sizes, two-query coverage and finite normalized mass. There were
541 cumulative native graph decode batches, nine capture-required eager batches,
a maximum actual decode batch of eight, and no preemptions or attention errors.
The artifact review is passed; this is not a throughput or scientific pass.

Online time was 248.171447754 seconds, yielding 4.351830196 completed calls/minute,
below the user's current six/minute target. Startup to first reservation was
224.116750479 seconds; allocation/logical time was 472.288198233 seconds. Startup
was already excluded from the online rate. A first-use JIT warning also occurred
inside the online interval. No two-hour validation job was submitted. The
previous native-SDPA feature-equivalence failure remains failed, and these new
outputs remain operational validation only, not a scientific reproduction.

Canonical evidence: qualification/runtime_throughput.json,
qualification/smoke_review_full.json and
qualification/smoke_manual_artifact_review_20261022.json under
/project/def-jacobsen/canvasrca_cache/RQ4_5/cpu_v1. Original pre-review receipts are
retained under qualification/history_smoke10_manual_review_20261022.

## CPU-08 — 2026-10-22 audit: the old first-prefill profile captured an empty scheduling step

The round-7 probe selected runner.execute_model's first invocation by an ordinal
counter, without requiring nonempty scheduled tokens or an actual language-model
forward. Its first_prefill_python.txt contains only 96 calls and about 0.001
seconds, with no model-forward frame. The corresponding operator table contains
only profiler setup/synchronization, not a language-model prefill. Therefore
this file is not evidence that the true first prefill is fast. It is a profiling
coverage defect; original files remain unchanged. The separate early_steps
profile mixes prefill and decode: it includes GDN prefill, so its 21.639-second
wall time must not be labeled as pure decode throughput. No new diagnostic
profile has been run in this audit.

## PERF-12 — 2026-10-22: documentation-guided diagnosis and the next bounded repair

The user asks to consult Nibi documentation, blogs and community discussions,
rather than continue ad-hoc tuning. This review uses installed source and actual
Nibi logs as the authority for our configuration, version-pinned upstream docs
for intended behavior, and original community reports only as hypotheses.
No inference source/configuration, local source, model input, model weight,
precision or score was changed, and no new GPU job or model call was submitted.

### Facts established on our Nibi deployment

1. RQ4_5/configs/execution_v1.json sets compilation_config.mode=0,
   FULL_DECODE_ONLY, enable_chunked_prefill=false, async_scheduling=false,
   max_num_batched_tokens=40960, max_num_seqs=8, and allocation fraction 0.90.
   This is no longer full eager execution: ordinary decode graph replay really
   occurred. However, compilation is still disabled and prefill/mixed batches
   do not get piecewise compilation from this configuration.
2. smoke10_24770165.out explicitly warns that the model does not officially
   support disabling chunked prefill. Installed vLLM engine/arg_utils.py
   2471-2479 emits that warning; our worker extension rejects chunked prefill
   and requires before=0 plus scheduled length equal to the full prompt at
   exps.py 20-21 and 55-59. This is an adapter compatibility constraint, not a
   requirement imposed by token pruning itself. The warning is not proof that
   these particular answers are corrupted.
3. Current packet CPU preparation averages 1.0718 seconds per request and
   encoder/transport averages 1.5148 seconds. Their overlapping means cannot
   be added to reconstruct wall time. They do not establish CPU preparation
   or vision encoding as the dominant source of the 248-second online window.
4. Multiple Triton JIT warnings occur after requests begin. They establish
   incomplete shape warmup, not the isolated number of seconds lost to JIT.
5. All eight preparation processes plus engine/control/inference work share the
   job's eight allocated physical CPU cores. No explicit GPU-local NUMA policy
   is registered. Slurm confirms g24 has two sockets, 56 cores/socket and eight
   H100 GPUs; the eight-core allocation is real, not an eight-GPU allocation.
   Contention/remote NUMA placement is a candidate to measure, not an observed
   cause. sacct's cumulative CPU time alone cannot establish per-process stalls.
6. rq43_encode runs through collective_rpc, returns GPU embeddings to RAM, and
   feeds prompt_embeds back into the engine. This gives an identifiable
   encode/transport boundary to measure; the current measurements do not prove
   the transfers dominate or that all of them are avoidable with this API.
7. The old first-prefill profiling defect is documented as CPU-08 above. A
   label on a profile file cannot substitute for verification of captured work.

### External evidence and its transfer limits

- [vLLM 0.24 optimization guide](https://docs.vllm.ai/en/v0.24.0/configuration/optimization/):
  input chunking, batching and CPU capacity are performance-sensitive settings.
  Its NUMA section describes placement near the GPU. These are candidate
  controls, not evidence of a six/minute result on our custom adapter.
- [vLLM CUDA Graph design](https://docs.vllm.ai/en/v0.24.0/design/cuda_graphs/):
  graph replay and compilation are separate; piecewise modes require compatible
  compilation. Our observed graph replay does not imply compiled prefill.
- [vLLM engine anatomy, official blog, 2025-09-05](https://vllm.ai/blog/2025-09-05-anatomy-of-vllm):
  useful separation of prefill, decode, scheduler, input processing and sampling.
  The article's illustrative engine is a standard transformer and cannot by
  itself certify this hybrid GDN model's state handling.
- [vLLM profiling guide](https://docs.vllm.ai/en/v0.24.0/contributing/profiling/):
  profile a short diagnostic window separately from speed qualification.
- [PyTorch CUDA Graph explanation](https://pytorch.org/blog/accelerating-pytorch-with-cuda-graphs/):
  graph replay primarily reduces host launch work; it does not promise to remove
  slow kernels or work outside the captured region.
- [Original long-prefill/decode report, upstream issue 54919](https://github.com/vllm-project/vllm/issues/54919):
  reporters describe a healthy engine with available KV and severe mixed-phase
  slowdowns. They also report that smaller chunks can improve short-request
  decode while increasing total makespan. Different models, GPUs, versions and
  modified schedulers prevent treating their root causes or gains as ours.
- [Original 27B batch report, upstream issue 36010](https://github.com/vllm-project/vllm/issues/36010):
  confirms that architecture-specific batch problems have been reported. Its
  environment differs; it is not a diagnosed fix for our deployment.
- [Original H100 low-utilization forum report](https://discuss.vllm.ai/t/low-average-gpu-utilization-40-70-on-h100-with-vllm-how-to-push-toward-90/2293):
  large KV allocation and client concurrency did not ensure high utilization in
  that user's workload. Automated RunLLM replies are not measured evidence.
- [Original SM120 report](https://discuss.vllm.ai/t/sm120-rtx-pro-4000-6-5x-throughput-gain-and-v0-18-1-regression-findings/2525):
  hardware-specific results are a reason to avoid copying local Blackwell
  settings blindly onto H100; no reported speedup or clock prescription is
  transferred to this cluster.
- SHARCNET's [training catalogue](https://training.sharcnet.ca/courses/course/index.php?categoryid=6)
  describes bursty utilization and performance diagnosis. Nibi's public
  [infrastructure dashboard](https://metrics.nibi.sharcnet.ca/) was accessible.
  Direct reads of the Alliance Nibi/Slurm/PyTorch wiki pages and a SHARCNET
  migration PDF were denied by Anubis; their full contents were not read and
  are not asserted as verified here. Runtime hardware was checked with Slurm.

### Repair order selected from this evidence (planned; not implemented here)

First correct measurement: require actual nonempty prefill/mixed/decode steps,
record input admission, first token, last token, sampled batch composition and
GPU work versus host/RPC waits. Use a brief profiler window to locate stalls;
perform the throughput gate with profiling disabled. Preserve the full online
first-reservation-to-drain window, all actual calls and unchanged denominator.
Any warmup is separately reported and still charged in allocation time; it is
not an excuse to discard early slow calls from the existing smoke.

Then remove the adapter's full-prefill-only assumption. Support prompt offsets
and accumulated K support across chunks; collect the last prompt query only
when the prompt actually ends, then the first decode query. Preserve MRoPE,
all registered gather indices, every hybrid/GDN recurrent state and the native
attention gate. Do not simply flip enable_chunked_prefill: the current guard
would fail and the existing attention bookkeeping would be wrong.

Next make the instrumentation boundary compatible with upstream compilation
and mixed/prefill execution. Isolate the two registered passive captures from
the ordinary model path, rather than disabling compilation throughout all
layers. Choose a supported compilation/graph pair from the installed version;
verify graph execution and the actual two-query capture, not only startup logs.
Compilation, graph capture, and shape warmup remain separately accounted.

Reserve inference/control CPU capacity in addition to the existing eight
preparation workers, within the granted Slurm resources and GPU-local NUMA
cpuset. The worker count remains eight. Measure this if the trace shows host
starvation; do not change model weights, BF16, evidence, output limit or method
arms to meet the speed target. Native supported scheduling is preferred over
another custom scheduler. Async scheduling, prefix caching, speculative
sampling and quantization are not bundled into this repair.

Finally run only the necessary bounded qualification of the consolidated
change. Require intact actual token operations, MRoPE, two-query attention,
18/18 artifact coverage and >=6 complete calls/minute. The authorization remains
exactly one two-hour full-queue operational job after these conditions pass,
without an automatic chain. There is no promised speedup before measurement.


## PERF-13 — 2026-10-22: consolidated chunked/compiled successor qualification

The user authorizes optimization and new jobs. A staged successor enables native
chunked prefill (8192 scheduling budget), vLLM compilation mode3 and native
FULL_AND_PIECEWISE graphs. Ordinary compiled execution remains untouched; only
attention-bearing chunks explicitly bypass compilation through ForwardContext.
Exact prompt K is accumulated across contiguous chunks, and only the complete
prompt's final query plus first decode query are measured. Eight preparation
workers are retained;12 physical CPU cores and128GB are requested, reserving
four cores for engine/control. This is an operational recipe revision, not a
claim of scientific backend equivalence. Native first-token timestamps and
classified nonempty step wall spans are recorded; the spans are not mislabeled
as isolated GPU kernel time. Prior18 answers, clocks, measurements and consumed
calls remain. Targeted CPU regression plus static checks must pass before the
new eighteen-call,900-second smoke can be submitted. The complete population
CPU input checks are reused by exact unchanged-payload lineage. Failure stops
the chain; passing>=6calls/min and full artifact/attention checks releases
exactly one two-hour platform job. No local experiment code is changed.


### PERF-13 bookkeeping correction

Round11 was correctly submitted with12 CPUs and128GiB, but the inherited submit
helper initially wrote8/96G in its descriptive receipt. scontrol verified the
actual allocation request; the original receipt is preserved and only those
descriptive fields were corrected. Future receipts now match the launcher.
This correction changes neither execution fingerprint nor model inputs.


## PERF-14 — 2026-10-22: consolidated successor is functional but still below target

Affected CPU check24787209, GPU smoke24787282 and artifact review24787283 all
completed0:0.18/18 new calls committed with no infrastructure or attention
error. All raw answers were read; six attention files totaling12,635bytes were
verified, each with the complete registered two-query coverage. Actual counters
show27 partial-prefill batches,17 native-compiled-branch model entries,498 full
decode-graph batches,18 eager capture-bearing batches and zero preemptions.
Thus the chunked/compiled adapter really ran; the older disabling-chunked-prefill
warning is gone. Model mistakes remain scored outcomes and were not retried.

Online242.3792seconds yields4.4558calls/min; startup289.3977seconds and total
allocation/logical time531.7769seconds are separately retained. This remains
below6; round10 was4.3518/min with224.1168seconds startup. The small observed
rate difference is not a demonstrated stable speedup: node placement and
sampled output lengths also differ. No two-hour platform job is submitted.

The new timing records confirm CPU packets average1.0018seconds and vision/
transport1.5033seconds. Classified host execute_model spans are13.9366seconds
prefill,74.6029mixed and1.2015decode across3/29/501 nonempty steps. Those calls
return asynchronously, so1.2015seconds is NOT total GPU decode time and the
unattributed online interval is NOT proof of CPU starvation. Native first-token
latencies and decode intervals are now retained per request. Further speed work
needs a short kernel/synchronization timeline or a controlled operator measurement
before more scheduler or cache edits; no unmeasured root cause is asserted.
See qualification/operational_runtime_round11_analysis.json and the original
smoke11 logs/commits. All earlier failures, inputs, answers and spent calls remain.


## Operational monitor blocker — 2026-10-21

RuntimeError('Measured throughput below latest6/min target; no formal submission')
No additional smoke or GPU job was submitted automatically. See qualification/platform_qualification_monitor_latest.json.


## PERF-15: Missing utilization samples and whole-model capture bypass — 2026-10-22

Round11 completed all eighteen calls but saved only one-shot hardware inventory, not utilization samples. Slurm accounting also has no usable gpuutil series. Its inference-period average GPU utilization is therefore unknown and cannot be reconstructed from throughput or CPU spans.

Source inspection confirms that attention-enabled batches set skip_compiled on the entire model while only layer3 queries are collected. Round12 stages one opaque, explicitly split layer3 native-attention operator before compilation; other layers retain native compilation, and full decode graphs remain available after passive queries finish. This is a proposed acceleration until actual GPU qualification completes; CPU synthetic equality is not a substitute for model qualification.

Round12 also samples only the allocated GPU UUID with NVML at one-second intervals. Raw CSV and metadata are retained. The reported utilization interval runs from first GPU encoding entry through last model-generation completion, excluding startup/compilation and final artifact drain. Throughput retains the earlier reservation-to-provider-drain interval and the six-calls/min gate. No claim of scientific feature equivalence is made.

The installed vLLM FlashInfer sampling path falls back to native sampling whenever per-request generators exist (topk_topp_sampler.py). Enabling that environment flag alone would not accelerate this independently seeded recipe; dropping seeds is not used as a workaround.


## OPS-16: Archived receipt counted as a new smoke round — 2026-10-22

CPU job24789642 passed static checks and twelve targeted tests, preserved all1518 input payloads, and completed source adoption. Registration then stopped before any GPU submission because glob(smoke_submission_*.json) also counted smoke_submission_11_before_resource_metadata_fix.json as a twelfth round. That file is a historical correction receipt for round11, not an additional allocation. Registration and the generic submitter now accept only exact two-digit round receipt names. The archived receipt remains unchanged. This is a scheduling bookkeeping repair; population tests and source adoption are not rerun.


## Operational monitor blocker — 2026-10-21

RuntimeError("Smoke/review terminal failure: [('24789955', ('FAILED', '1:0'))]")
No additional smoke or GPU job was submitted automatically. See qualification/platform_qualification_monitor_latest.json.


## PERF-17: PyTorch/NVML GPU UUID spelling falsely rejected the allocated device — 2026-10-22

Smoke12 job24789955 failed after4m05s, during rq43_install, before any ledger reservation or diagnostic generation. Model weights, torch.compile and both piecewise/full CUDA graph warmups had completed. The exception was introduced by our new monitoring check comparing the two raw UUID strings. GPU identity probe24801112 completed in20s without loading model weights or calling the model. PyTorch _CUuuid string is `7ab3fca3-53de-1a4d-3760-a2289065f9ed`; NVML string is `GPU-7ab3fca3-53de-1a4d-3760-a2289065f9ed`. Canonical UUIDs are equal; no different physical device was observed.

The monitoring fix compares parsed canonical UUIDs, preserves raw strings/types in audit metadata, still rejects genuinely distinct/invalid identifiers, and performs the identity validation before loading weights. The layer3 attention arithmetic, compilation configuration, seeds, BF16, prepared image/text inputs, ranking and scoring are unchanged. Smoke12 remains failed, its clock/artifacts are archived unchanged, and no GPU-utilization average can be reported from it. Round13 requires affected synthetic checks then actual 18-call qualification and artifact/throughput/utilization review.


## OPS-18: Stale predecessor-version assertion in monitor-repair adoption — 2026-10-22

CPU job24801791 stopped before any source edits or model calls because its adoption script still expected the older chunked_compiled_capture_v2 predecessor, while the frozen and CPU-qualified current source is capture_partition_v3. The before-edit archive was retained. The v2 adoption script checks the actual frozen predecessor capture_partition_v3 and uses a new history directory; no scientific configuration, completed population tests or ledger rows are changed.


## GPU UUID monitoring adoption failure — 2026-10-22

RuntimeError('Unexpected model transport changes')
No GPU job submitted. See qualification/gpu_identity_adoption_failure.json.


## OPS-19: Same-named lazy factories collided in generation fingerprints — 2026-10-22

CPU job24802091 stopped before any GPU submission or input rebinding because the expected transport-change set did not match the computed change set. Investigation found both exps.py and utils.py define __getattr__; transport_code keyed only by symbol name let utils.__getattr__ overwrite the worker-factory hash. Consequently, the newly changed exps worker pre-load monitor hook was not individually represented. The change guard correctly blocked adoption.

The worker lazy factory now has the unique worker_factory fingerprint key; the original utils.__getattr__ entry remains distinct. An independent stdlib AST calculation verifies the exact expected changes (worker_factory and VLLMWorkerExtension) before resubmission. The failed adoption's uncommitted source writes were restored to their exact frozen predecessor; staged repairs and all failure archives remain. No model arithmetic, diagnostic input, answer, scoring or spent call changed.


## Operational monitor blocker — 2026-10-21

RuntimeError('Measured throughput below latest6/min target; no formal submission')
No additional smoke or GPU job was submitted automatically. See qualification/platform_qualification_monitor_latest.json.


## PERF-18: Functional smoke13 passed; numeric throughput target explicitly withdrawn — 2026-10-22

Smoke13 job24802797 completed18/18 calls (12 RCA,6 QA), with zero infrastructure or collected-attention errors and no KV preemption. Offline review24802800 plus operator review verify all actual answers/registered input identities and six layer3 two-query attention files (12,664bytes). GPU UUID monitoring is repaired;234.902s of actual inference is covered with time-weighted mean GPU utilization95.3307%,264raw1Hz samples and full interval coverage. Original first-reservation-to-provider-drain speed is4.47955calls/min over241.095s. These measured values are retained unchanged.

The old controller correctly stopped before formal submission because the earlier six-calls/min gate was unmet. The user now explicitly withdraws that numeric target and accepts measured throughput, authorizing exactly one two-hour Slurm job with one H100. This is a prospective user acceptance bound to smoke13 and its execution fingerprint, not a retroactive measured six-calls/min claim. The single job performs only retention/linking of already CPU-prepared files before model startup; no additional CPU Slurm job or continuation GPU allocation is submitted. Scientific feature-equivalence and old scientific QA limitations are not reclassified by this operational authorization.


## OPS-20 — 2026-10-22: one-token prefill tail misrouted to FULL CUDA graph

Job24806735 was the one authorized two-hour, single-H100 platform validation.
It ran on g9 from14:21:01 to15:30:22 and failed1:0 after1h09m21s, before the
2h limit. It committed262 formal calls/positions out of1560; eight in-flight
formal calls were marked infrastructure_failure when the shared engine died.
Those eight calls are one engine-failure fan-out, not eight independently
observed defects. Earlier smoke failures in the global ledger are not added to
this allocation's failure count. All committed inputs, answers, conversations,
attention and original logs remain unchanged.

The primary exception came from exps.py guarded_dispatch:
`Unsafe graph replay bypasses registered capture`. Native vLLM classifies
uniform decode using scheduled tensor lengths rather than original prompt
completion. A one-token remaining prefill chunk can match a decode graph shape.
Our adapter restricted FULL only when passive capture was pending, then also
rejected FULL for *any* prefill. This inconsistency was reached in the longer
queue. The exact failed batch counters were not logged; the installed native
dispatch and exact guard reproduce this exception on a synthetic one-token
prefill without attention. The18-call smoke did not establish coverage of this
boundary; its successful artifacts remain successful, but do not establish
long-queue reliability. This is an adapter routing defect, not evidence of an
H100 memory failure, quota failure or timer expiry.

A source-local repair now restricts any prefill or capture-pending batch to
NONE/PIECEWISE before calling native dispatch. It intersects caller mode
restrictions and preserves invalid modes, including native force-eager; it no
longer silently widens the caller's allowed modes. Genuine ordinary decode
with completed/no capture retains FULL acceleration. The post-dispatch safety
assertion remains. No model weights, BF16, token selection, MRoPE, prompts,
ranking or scoring code changed. Previous source copies and exact hashes are
in qualification/graph_dispatch_repair_24806735/.

Affected CPU validation passed12 cases using the actual native dispatch
function and exact adapter guard with synthetic batch state, without importing
torch/vLLM or loading a model. The old source reproduces the failure; new source
passes single-token prefill, mixed prefill/decode, pending/completed attention,
ordinary FULL decode, force-eager, excluded modes, no-live-request dispatch,
contradictory-mode rejection and retained fail-closed assertion. This fixes the
CPU-reproduced defect; native GPU replay on the new version is not yet measured.
The220-case data preparation was not repeated. Existing source-bound GPU
qualifications were not silently rebound to the changed version.

Actual inference interval (first committed GPU encoding start through last
committed generation completion) is3760.9873s, with97.6655% time-weighted GPU
utilization and100% sample coverage;262 completed calls yield4.17975calls/min.
This excludes model startup and does not count failed requests as completions.
All70 attention-requesting completed calls report no capture error/miss, and
committed receipts report zero KV preemptions. The withdrawn six-calls/min goal
is not reinstated. No new jobs or model calls were submitted: the explicitly
allowed single two-hour allocation is consumed. A replacement allocation needs
new user authority and source-bound native qualification. Local running code
was not read or modified by this repair.

Evidence: qualification/graph_dispatch_repair_24806735/failure_analysis.json,
targeted_cpu.json, original formal summary/commits, GPU CSV and
logs/platform_24806735.{out,err}.


## OPS-21 — 2026-10-22: append-only recovery and explicit direct-formal resume

After OPS-20, the user authorized a replacement job, explicitly instructed us
to skip new smoke and resume the interrupted formal queue. Job 24832363 is the
only replacement: one H100, two-hour allocation, 12 allocated CPU cores with
eight preparation workers, GPU concurrency eight, and no automatic requeue
or subsequent allocation. At submission it was pending resource allocation.
The old numerical throughput target remains withdrawn.

The original 262 atomic commits are preserved. The remaining 1,298 of 1,560
positions are bound to execution version f7b6392635446bc424cbd7b572bb2bbda7f477d2c457e8371c3a0e12ccf8cfca.
The eight infrastructure-failed in-flight requests receive exact key, role,
prior-attempt and new-generation-identity retry permissions. Recovery appends
a new ledger attempt instead of changing the old failure. The original 402
ledger rows and all 262 completion-file hashes were verified unchanged.

The runtime-only fix also changes the generation identity of pending requests.
Completed queue entries keep their original requests and identities. Pending
references to predecessor-version answers are not falsely reused as identical
new-version computations. The original source snapshot, queue, qualification
receipts and failure artifacts are retained. Old allocation telemetry was
moved to formal/allocation_history/24806735/ so the replacement monitor can
write its own CSV without overwriting historical measurements.

Affected checks: 12 native-dispatch guard cases and 14 append-only recovery
cases passed, along with Python static checks and protected-source checks.
The completed 220-case CPU preparation was not repeated. Unchanged CPU
qualifications carry an explicit provenance explanation; the predecessor GPU
smoke receipt is unchanged. New GPU qualification is explicitly waived by the
user, not recorded as passed. The generation transport/kernel fix has not yet
been exercised by the replacement job at the time of submission.

Submission first held the Slurm job, recorded its exact ID/source/script/queue
binding, then released that same job. Its wrapper checks that ID and binding
before formal execution, trusts committed markers, uses retained prepared
inputs, and does not launch smoke or repeat heavy CPU compilation/rendering.
A 300-second allocation reserve permits signal-driven drain within the two
hours; this is not the removed 600-second smoke rule.

Evidence: qualification/resume_20261022/adoption.json and affected_checks.json;
qualification/formal_resume_authorization.json;
qualification/infrastructure_retry_authorization.json;
qualification/platform_resume_submission_20261022.json;
RQs/RQ4_5/scripts/resume_platform_nibi_20261022.sbatch.
Local experiment code and the running local RQ4.10 were not read or modified.
