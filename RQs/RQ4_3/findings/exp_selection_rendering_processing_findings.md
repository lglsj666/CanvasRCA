# RQ4.3 当前状态：全队列完成，报告已更新为完整数据版

2026-10-12：`formal_v7/phase_complete.json`及progress共同确认4,832/4,832位置，4,637真实完成调用＋195引用，writer已排空；22基础设施失败/14中断历史记录保留，没有未解决逻辑位置。服务自行关闭。最终保留体积未在本次报告工作中宣称通过。

按用户要求，[详细结果与决策报告](../../../docs/experiment_reports/RQ4_3_Qwen_Analysis_2026-10-12.md)已替换此前11:48截点分析。新增289个结果全部来自R_PATCH_PACK、R_HORIZON、R_PACK_HORIZON、C_PACK_OFFSET、C_READ_GUIDE、C_PACK_BG_FILL、X_SR和X_RP；原4,543个提交哈希无变化。20个当前主臂均完成220例，八臂最终标准MRR为.2535–.3252。其他12臂及历史对照指标不变。P_SOFT_IMAGE标准/宽容MRR .3491/.3627，预选X_SRP .2630/.2630，仍未达到替换历史U或超过强文本的目标。

涉及八臂的全部指标、成本、失败、分层和配对分析已更新；同族其他比较的Holm值一并重算。全部主臂共同病例数为220。R_PATCH−C_READ_GUIDE的病例/事件组未校正p为.01404/.01650，固定11项归因族校正后为.1544/.1815，归因比较未通过校正。六项事后系统比较的病例/组pH均为1。

QA严格/宽容分保持U .0583/.1194、P_LOCAL .0361/.1167、C_GLOBAL .0250/.0972；180调用、1,059适用题独立复核及固定12例36组QA—RCA回答人工对照保留。P_LOCAL ORDER额外首选翻转56.67pp，固定机制族Holm p=1.747e-7，同后端敏感性方向一致。540份attention完整匹配，摘要430,472字节；仅层3两个起始query，不能称作完整推理attention或有害sink的因果证据。这些子集在此前截点已完整，本次没有新增数据或重做人工判读。

4,832条记录的生成身份、4,652份RCA与180份QA原分数、440份历史回答，以及150项独立统计复核通过。历史后端兼容未建立、恢复R与组合版本不完全一致的限制保留。0新增模型调用；未改变运行器、输入、队列或Codex.md。旧截点清单和主表仅作为更新来源保留，当前结论以完整数据版报告为准。

# 历史状态：v17 完整扩展队列运行，部署目标完成

2026-10-11：22:40 长 HTML 请求在 KV 容量压力下触发不支持的 prefill 重算，EngineCore 退出，主进程等待孤立 RPC。修订 v17_kv_admission_v19 加入按实际混合缓存块预留完整输入＋8192 输出、引擎死亡通知和有界错误清理；用户授权显存比例由 0.75 提升至 0.80。静态及 18 项受影响回归通过。恢复后自首个新增提交起连续观察 180.1 秒通过，观察结束 2819/4832；交接核对为 2822/4832。无新增基础设施失败或中断，八个原受影响请求均已重新完成提交，抢占计数为 0。实际缓存为 18.44 GiB、281,600 等效 token（384 个可用共享块），实际解码并发峰值为 8。输入长度合适时可保持八并发，长请求按容量等待。实验继续后台运行，后续全队列状态仍以实时进度为准。 [修复记录](../../../docs/issues/RQ4_3_KV_Admission_Repair_2026-10-11.md)。

2026-10-11：1,444 个提交后，X_SRP 冷重编译出现生成身份不一致并自动停止。两次隔离复现均一致，偶发底层原因未复现；运行修订 v17_xsrp_frozen_input_v18 改为严格校验的已冻结输入，避免正式运行重做布局搜索。220 个 X_SRP 和 24 个恢复臂请求实际 CPU 检查及 13 项离线回归通过，模型/输入/队列/评分保持不变，计时明确为缓存输入。已按用户授权恢复并监控 206.1 秒，1459/4832，零新增基础设施错误，继续后台运行。详见 [修复记录](../../../docs/issues/RQ4_3_X_SRP_Runtime_Repair_2026-10-11.md)。

2026-10-11：八个恢复臂 220/220 CPU 通过、0 错误，三数据集均达适用门槛；新 GPU 资格按用户授权豁免。两个 HTML 对照均 220 例 CPU 通过，真实 smoke 共 8/8、163.54 秒，0 基础设施或格式失败。未依据 smoke MRR 调整。当前用户新增 smoke 四次机会，只使用第一轮中的八次调用。

最终 4,832 个位置、4,637 独立请求、195 个精确引用。切换前 1,190 个提交保持不变；v17 启动观察 234.4 秒后 1203 个完成结果，没有新增基础设施错误。vLLM/BF16、8 CPU 物理核 worker、8 GPU 并发、0.75 显存比例保留。状态以 `results/formal_v7/progress.json` 为准。

直接可读保留规则与自动收官已部署：普通文件、硬链接去重与共享 CSS，无压缩归档；保留完整实际输入/原回答/对话/评分上下文/事件组/全部已采集 attention 及其定义与映射。42,368 个必要文件预审无缺失。最终 25 GB/10,000 calls 密度仍待实验结束的自动核验，不宣称目前已完成该体积测量。缓存输入明确区别于完整冷启动计时。

[交付报告](../../../docs/experiment_reports/RQ4_3_Direct_Retention_and_Extension_2026-10-11.md) · [计划](../../../docs/experiment_plans/RQ4_3_Direct_Retention_and_Arm_Restoration_2026-10-11.md) · [启动核验](../results/deployment_v17/startup_monitor.json)

# 历史状态：vLLM v13 正式运行，180 秒启动观察完成

2026-10-11：用户明确要求跳过 GPU smoke 并恢复正式队列。当前主进程 PID 399377，启动基数 374/2632；首个新增提交后观察 180.10 秒，结束为 405/2632，随后审计快照 410/2632，以 `results/formal_v7/progress.json` 为权威实时状态。该区间无新增基础设施失败，实际 decode batch=8；GPU 91 次采样均值 82.43%，未达到此前接受的 85.58%，不宣称长期性能达标。正式运行保留，交由用户监控。

首批 36 个新提交中 31 个正常、5 个模型无效回答，均保留。12 个 attention 提交均有完整的两次查询区域摘要、无记录错误或漏采，包含文本与图像，每份 793–801 字节。每调用 64 KiB 硬上限不变，含索引/临时副本/共享预留的每万次上界为 730,464,256 字节，低于十进制 1 GB。已核对 P_LOCAL_BI/P_SOFT_IMAGE/P_DUAL 及控制分支计数；真实模型完整数值等价未单独验证。证据为 `results/deployment_v13/{startup_monitor02,live_audit}.json`。

静态及 14 项受影响离线测试、43 份真实输入的 gather/位置检查通过。GPU smoke 是用户跳过，不是新通过。v13 开发启动中的错误全部保留；本次有效恢复前账本为 374 complete、14 infrastructure_failure、9 interrupted。先前的失败尝试按修复凭据重试，已有提交不重答。所有臂共用 vLLM，BF16/权重/原输入/P 算子/评分保持原定义；抽样内核变化和后端版本独立记录。

当前环境没有外部 flash-attn，使用 vLLM 内置 FlashAttention；无依赖安装或升级。CPU 八个物理核 worker、RAM 有界预取，GPU 八请求并发，0.75 显存比例；不使用磁盘准备缓冲。历史 v12 374/2632 暂停及 72.30% 满在途利用率记录保留，不能继承其资格为本次性能证明。

[整体改造方案](../../../docs/experiment_plans/RQ4_3_Inference_Backend_Overhaul_2026-10-11.md) · [v13 部署记录](../../../docs/experiment_reports/RQ4_3_VLLM_Deployment_v13_2026-10-11.md)

## 历史状态：v9功能与短时速度已接受

2026-10-11最新用户决定：接受85.58%实测平均利用率，停止继续优化；原88%未达到的记录保留，已不构成准入阻塞。本条不启动正式实验。

2026-10-11：最终smoke08完成18/18，共284.21秒，0基础设施错误，2个模型无效回答保留。
确认8个独立CPU进程/物理核及8路请求、decode重叠。RAM准备缓冲峰值114.88MiB。
FLA＋编译norm保留权重/BF16、不量化；用户接受内核导致的排序变化，7/15排序差异
已记录，不以此判失败。实际推理阶段GPU采样均值85.58%，8请求阶段87.67%，
未达到88%目标。8/8新增smoke机会已用，实际81次新调用，全部失败/中断均保留。
CPU回归按用户要求豁免。正式281/2632不变，v9资格已保存，激活false，PAUSE保留；
无模型服务在跑。Codex、renderer和既有提交不改。attention803字节，开关回答相同。

[并发资格报告](../../../docs/experiment_reports/RQ4_3_Concurrency_GPU_Qualification_v9_2026-10-11.md) · [GPU证据](../results/concurrency_v9/smoke08/report.json)
· [利用率](../results/concurrency_v9/smoke08/utilization_review.json) · [运行状态](../results/deployment_v9/readiness.json)

以下为历史进展，运行状态以本页顶部及formal_v7/progress.json为准。

## v8恢复X_SRP并追加队列

2026-10-11：完整220例CPU通过；X_SRP已追加，总2632位置、2595独立生成请求。37个回退请求精确引用X_SP，原133个原子完成记录保留。新增GPU smoke按用户明确授权豁免，未伪写通过。既有29个组件文件和操作未改；6个新注册组件ID通过unified renderer。CPU资格不表示MRR或成本目标达到，见[详细报告](../../../docs/experiment_reports/RQ4_3_X_SRP_CPU_Qualification_v8_2026-10-11.md)。

下面保留历史状态，不表示旧取消状态仍适用于X_SRP v8。

# RQ4.3 current findings

2026-10-11: **formal_running_after_surviving_CPU_and_GPU_qualification**. GPU smoke completed 18/18 in 481.95 seconds; zero infrastructure errors, two invalid model answers retained as zero scores. Formal queue launched with PID 29940; startup monitoring passed after 224.0 seconds, 8/2412 positions committed with no infrastructure errors.

Nine surviving RCA conditions plus QA/order/repeats/timing qualified; 2412 new development positions. Static, 22 CPU regressions, 220 source/P cases, 440 selected images, 60 QA cases and 15 cold-identity replays passed. Original full matrix is NOT qualified. R and its dependencies are cancelled under registered gates, including preselected X_SRP; it is not replaced by another winner. S_DISTINGUISH and S_REPRESENT are cancelled as near-duplicates.

Logical smoke remains 18 calls / 600 seconds. Current allocation 2664 (including 234 infrastructure reserve), user space 8000. Historical U/T_FULL/MARGINAL_FIVE are reused. Historical backend equivalence remains not_demonstrated; dependent inferential slots are identity_ineligible, not zero effect. Codex.md unchanged.

[CPU report](../../../docs/experiment_reports/RQ4_3_CPU_Qualification_v7_2026-10-11.md) · [qualification](../results/deployment_v7/cpu_qualification.json) · [v7 plan](../../../docs/experiment_plans/RQ4_3_Selection_Rendering_Processing_Plan_v7_2026-10-11.md).

Attention enabled on registered subset: 797-byte smoke record, on/off ratio .9606 with identical response; conservative 10k storage bound 730464256 bytes. QA phase-case scoring-only correction has an AST compatibility proof and no new model calls. No ranking/prompt tuning from smoke.

Live status: `results/formal_v7/progress.json`. Commands: `bash RQs/RQ4_3/scripts/run.sh status`, `pause`, `resume`. A pause must drain the in-flight call before shutdown.
