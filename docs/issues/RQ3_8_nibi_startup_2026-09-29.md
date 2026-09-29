# RQ3.8 Nibi 启动耗时与 smoke 时间限制

状态（2026-09-29 更新）：历史启动、端口与容量故障均保留在下文作为各次尝试的当时记录；
v7 GPU smoke 已完成并通过真实双模型调用与产物审核。四个正式 job 已提交，提交时均在排队，
尚无正式效果结果。下文早期的“待补验／不得提交”只描述对应历史尝试，不是当前状态。

## 已确认的事实

- CPU job22923347：61项回归及24项双模型processor检查通过；480份gallery完整。
- GPU jobs22922720、22923667、22927066：每次在旧脚本600秒限制结束，累计0次推理。
- job22927066的Slurm状态COMPLETED、退出0，只代表脚本正常结束；不代表vLLM就绪。
- 本地RQ3.7日志：`Using Triton/FLA GDN prefill kernel (requested=auto)`，
  32.51秒加载权重，24.66秒完成engine初始化。
- Nibi：`Using FlashInfer GDN prefill kernel (requested=auto)`，权重仅15–21秒；
  FlashInfer编译对象时间戳持续更新，旧共享库没有完成重建。GPU驱动/OOM故障未证实。
- 安装的vLLM resolver对Hopper SM90自动选择FlashInfer。本地RTX PRO6000走Triton。
  `auto`不是跨硬件固定的内核实现。FlashInfer生成器正文为2种dtype×32种布尔组合，
  共64个CUDA模板实例；不能沿用过时docstring中“32个”的描述。

## 根因与修复

1. 入口没有显式固定适合当前部署的GDN后端，触发本地没有经过的大规模SM90 JIT。
   新独立运行profile显式设`gdn_prefill_backend: triton`，不改共享默认配置或历史profile。
   这是内核实现调整，不是改变prompt、权重、精度、采样或dashboard；仍需现场资格检查。
2. Slurm申请30分钟，但supervisor硬编码600秒，更早终止了启动。用户现明确取消此限制。
   同时删除smoke的`USR1@360`提前通知，否则30分钟实际会被缩为24分钟。
   正式job的8小时drain窗口保留；300秒单请求网络超时保留。
3. 旧timeout-only规则使零推理也被写为passed。新结果明确区分complete/incomplete/failed，
   正常进程退出不能替代两模型真实调用与产物检查。历史状态不改写。

前三次日志和源码/profile快照保留。新增补验是用户单独授权的第4次，不重置18-call账数。
使用第8个CPU job核对新配置、无隐藏时间限制、状态标记、原PNG/事实与续跑语义，
通过后提交一个30分钟GPU补验。不得用六个正式jobs替代启动诊断。

## 证据位置与边界

- `RQs/RQ3_7/results/fusion_v2_pruned/logs/A_qwen3.8-27b_server.log`
- `RQs/RQ3_8/results/ops_components_v2/smoke/logs/`
- `RQs/RQ3_8/results/ops_components_v2/smoke/attempts/`
- Nibi `.venv-inference/.../vllm/model_executor/layers/mamba/gdn/qwen_gdn_linear_attn.py`
- Nibi `.venv-inference/.../flashinfer/jit/gdn.py`及GDN `.ninja_log`
- [vLLM对应源文件](https://github.com/vllm-project/vllm/blob/v0.24.0/vllm/model_executor/layers/mamba/gdn/qwen_gdn_linear_attn.py)

[上游issue41865](https://github.com/vllm-project/vllm/issues/41865)报告另一个多TP场景的
GDN编译卡死，并给出Triton替代；我们的TP=1，不能把该issue的死锁结论当作本次确诊。
尚不能保证修复后启动时间或GPU测试成功，必须看新job的实际ready和完整推理产物。

## 修复资格检查

Nibi CPU job **22930024** 已于2分08秒正常完成：静态检查通过，68项回归通过
（59.95秒），24项case/arm的双processor容量检查通过（7.93秒）。既有480份gallery
复用，没有在本地执行测试。第4次GPU补验申请192GiB主机内存、8核、完整80GB H100、
30分钟；提交编号由`results/ops_components_v2/slurm/rq38ops-smoke-attempt4.json`记录。
这里没有宣称新GPU补验已经完成或正式实验已经具备资格。

## 第4次GPU补验：已就绪，但客户端端口未同步

2026-09-29核查：job **22930381** 为FAILED，退出码1，运行7分13秒。
Qwen在395.32秒（约6分35秒）达到ready；权重加载9.53秒，engine初始化266.99秒。
显式Triton路径已到达API就绪，但启动仍超过5分钟，不能宣称启动耗时问题全部解决。

本次直接退出原因是`RuntimeError: live tokenizer preflight failed`：

- `RQs/RQ3_8/scripts/environment.sh`设置job专属`CANVASRCA_VLLM_PORT=30381`。
- runtime adapter与readiness probe使用该端口，attestation记录
  `http://127.0.0.1:30381/v1`，服务日志确认`GET /v1/models`成功。
- `scripts/env.sh`将`VLLM_BASE_URL`默认设为`http://127.0.0.1:8000/v1`；
  RQ入口没有将它与上述端口同步。
- `vlmrca.vlm.configs.get_config()`同步采样等字段，但没有同步endpoint。
  `count_vllm_prompt_tokens()`及实际生成client读取的仍是`VLLM_BASE_URL`。
- tokenizer请求异常被转换为None，持久化调用入口据此抛出上述通用错误。
  该检查发生在generation ledger.begin之前，不是模型输出失败。

三个TEXT目标因预检失败结束，未进入答案生成；Gemma尚未启动。server是驱动异常后
被supervisor的finally清理，不应记为vLLM core自行崩溃。另发现supervisor异常路径
没有提交终态，留下`running/incomplete`，它不能覆盖Slurm及runner的失败证据。

后续最小修复应统一launcher、readiness、tokenizer与generation的endpoint，
并补充端口一致性检查、实际请求异常详情和supervisor异常终态记录。不需改变证据、
dashboard或模型采样。本次只完成诊断记录，未修改运行代码、清理失败标记或提交新job。

证据：`results/ops_components_v2/logs/rq38ops-smoke-attempt4-22930381.log`、
`smoke/logs/{server,runner}.qwen3.8-27b.1790704559807211014.log`、
`smoke/attestations/qwen3.8-27b.json`、`smoke/flags/`及`smoke/supervisor.json`；
上述路径均位于Nibi的`RQs/RQ3_8/`之下（smoke路径以results/ops_components_v2为基准）。

### 端口修复补验（用户另批准一个job）

RQ-local `bind_client_endpoint`使driver、tokenizer、SDK与runtime/probe使用同一URL，
shell也同步job端口；attestation再次核对实际客户端URL。预检异常日志补充无敏感数据的
endpoint、异常类型、HTTP status；supervisor异常路径提交failed而不遗留running。
新增双模型/双端口mock回归及异常状态回归。不得在本地运行测试。

第5个job22932223在分配资源前被用户取消。用户随后明确要求replacement GPU smoke
不再运行CPU回归。第6次提交直接依次运行两模型；不另提交CPU job，不扩18次
generation预算，不提交正式任务。当前源码CPU证明仅对smoke豁免，正式实验不豁免。
第4次来源快照/结果保留在`smoke/attempts/attempt4_endpoint_failure/`；仅其三个
已确诊、尚未发起generation的TEXT失败标记移至该目录后重新开放。历史ledger不重置。
本节记录修复与队列设计，不代表回归或GPU补验已经通过；结果以新job落盘记录为准。

## 后续补验与当前资格状态（2026-09-29）

- v6 第七次 smoke job `22941413` 在模型请求前失败：AegisLab
  `INC-01BF937825D4` 的 Qwen `FULL` 输入为 35,011 tokens，超过保留 8,192
  输出 tokens 后的 32,768 输入上限。这是实际图像处理器与冗余文本共同造成的容量问题；
  不能归因于模型回答，也不能仅凭“只有一张图”假设视觉 token 很少。
- 用户要求保留图像和固定文本对照的实验语义。v7 只对每个 arm 共同使用的文本做可核对的
  无损去重／紧凑关系编码；`TEXT_DUP` 的有意重复保持原定义，不改 PNG、renderer、模型、
  采样或评分。三例 66 个 case×arm 双处理器检查在 45.64 秒内通过；上述 Qwen
  `FULL` 输入降至 27,769 tokens。该检查是容量资格，不是效果结果。
- v7 smoke job **22942268** 的 Slurm 记录为 `COMPLETED`、`00:25:59`、退出码 0；
  更关键的是 `results/ops_components_v7/smoke/artifact_review.json` 记载两模型
  18/18 个真实调用及完整 conversation、PNG hash 和输出审核均通过，输入 token
  范围 11,650–27,769。`qualification/static.json` 为 passed。历史零调用的
  `COMPLETED` 不能借此改写为通过；v7 smoke 也不是正式 RCA 效果证据。
- v7 后仅改变四 job 调度、CPU waiver 与恢复控制路径；请求编译、renderer 指纹、
  客户端、模型配方和 scorer 未改变。兼容审阅在同一个 `artifact_review.json` 中列出
  原 smoke 源合同、当前合同及准确变更文件。用户明确豁免正式运行的 CPU 回归，
  状态记录为 `not_run_user_waived_for_formal`，绝非“CPU 测试通过”。
- 端口错配已在成功真实调用的 v7 路径上消除；但 25分59秒的整场 smoke 时长不等于
  单个模型启动时长，也不能声称 Qwen 在 Nibi 一定能于 5 分钟内 ready。

## 全量缓存同步踩坑与恢复（2026-09-29）

**错误与影响。** 第一次批量 `rsync` 漏了 `--relative`（`-R`），多个原本位于
`RQs/RQ3_4/results/...`、`RQs/RQ3_7/results/...` 的源路径被错误地压平到
Nibi 仓库根目录，产生约 31 GB 的非预期 `contexts/` 副本，以及根目录
`registration.json`、`export_v1/`、`public_cache/`、`preparation_flags/`、
`private/` 等路径。RQ3.8 的消费者使用 RQ-local 固定路径，所以这些根目录副本
不能满足依赖；仅凭“rsync 正在传”或总传输字节数会误判为准备就绪。

**清理边界。** 发现后先停止错误传输，逐一核查上述仓库根路径是本次新建的误传副本，
再仅删除这些明确目标；没有删除源端缓存、正确 RQ-local 数据、模型、正式结果或 smoke
证据。根目录误传副本已不可恢复，但其源文件仍在本地，且随后被重新正确上传。

**正确做法与证据。** 多源路径同步使用 `rsync -aR --partial`，保留从仓库根开始的
相对层级；单一 canonical public 目录则使用 `rsync -a` 并显式指定其目标父目录。
旧 ledger 是指向本地绝对路径的符号链接，需用 `rsync -aL` 复制实际 SQLite 字节，
避免在 Nibi 留下悬空链接。两路最终传输均退出 0：RQ3.4 上下文 180/180、
RQ3.7 上下文 660/660、父版公开导出 480/480、canonical public 文件 15,258。
按正式 roster 对 840 个案例（480 eval＋360 test）检查五类 canonical public 文件、
冻结 parent 或 predecessor context、public cache、提交标记与 evaluator-private 记录，
**缺失 0**。这只是轻量存在性核对；没有重建所有请求或做全量内容 hash，正式准备时
仍由 export 逐例核查关键来源 SHA 与实体身份。

**运维教训。** Nibi SSH/MFA 会话或多路复用 socket 失效只阻断部署，不等于实验
失败；重连后必须先检查 Slurm 收据与目标文件，不能盲目重传或重复提交。同步命令
必须先确认目标目录语义，尤其多源 `rsync` 要保留相对路径。正式提交前以 roster
逐例核对真正的消费者路径，不以仓库根目录、目录数量或传输进程结束代替。

四个 8 小时正式 job 的提交收据及调度依赖记在
`RQs/RQ3_8/results/ops_components_v7/logs/2026-09-29_formal_submission.md`；
此处只记录资格、故障与恢复，不预先宣称 19,440 个正式调用已完成。
