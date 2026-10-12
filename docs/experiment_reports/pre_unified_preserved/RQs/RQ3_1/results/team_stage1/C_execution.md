# RQ3.1 C execution stage 1

日期：2026-09-15  
状态：CPU 注册与恢复基础已实现；没有启动 vLLM、GPU、模型调用或正式分析。

## 已实际完成

- 新增并通过 `research_v1.json` 注册：14 个主 arm、5 个机制条目展开为 8 个 mechanism conditions、三类重复/稳健性附加矩阵、两档预算、两档冗余负载、7-method final test。
- 调用预算核对：主实验 13,440；机制 1,600；重复 1,200；稳健性 800；预算 800；负载 800；final test 5,040；三个 smoke 各保留 18-call 上限，共 54；核心合计 23,734，硬上限 28,000，保留 4,266。重试计入，复用不计作新的独立 case，重复调用有独立 ledger attempt。
- 模型顺序固定为 Qwen3.8-27B（主）→ Gemma-4-26B-A4B-it（跨模型复核）；禁止 ensemble 和 per-test oracle。RQ3.1 request adapter 显式固定 8,192 completion tokens、thinking off、attention disabled，不从全局 16,384 ceiling 偷取设置。
- `register-research` 只读取 data-registration 的 public eval identities，按 seed 42/hash 为 `re2_ob`、`aiops2022`、`aiops2025` 各选一个 smoke case；不读取 test telemetry/effect。注册产物为 `research_registration_v1.json`，`--check` 已通过，记录 `model_calls_started=false`。
- 当前 registration hash：`be8c502dd8f78a7a5efea30da1e4cdfa107d7926417d91d0dd60494f68d15b16`；final-method roster、mechanism 展开、selector budget 与 public-identity-only 输入校验均已重新生成并 byte-check 通过。
- selector 标准语义预算固定为 128，预算曲线为 0.50/0.75/1.00，fact-cost 与 q/F ablation 版本均显式注册；该预算只约束 CPU 选择，不代表已运行。
- 统一执行接线到现有 `vlmrca.vlm.client.call_vlm`、`vlmrca.run_state.persisted_model_call/DurableCallRegister`、现有 `unified_scripts.RCAScorer` 回调和 RQ2 `AsyncWriter`。每次请求规划 inputs、prompts、renders、conversations、outputs、cost、trajectories、partial、errors；shared persistence 采用 atomic write + artifact hashes。
- call key 是 experiment/model/opaque-case/dimension 的稳定 hash；ledger 对 request hash/role 做 resume identity 检查，completed 结果复用，started/failed 必须显式 reconcile，partial response 不拼接。
- 增加 stale/reused PID 检查：仅 PID 不足以证明 owner，核对 `/proc` command 与 starttime；timeout 不自动视为死亡。提供 `recover` 和 `reconcile` 可审计命令及本地 CPU shell 入口。
- 主方法选择规则已实现但未用于旧分数：只接受 `X_V_CONTRAST`/`X_MTEXT`；Qwen 五数据集等权 macro MRR，≤0.01 tie 时按两 AIOPS 最低 MRR、相对自身 T 成本、固定 method id；`method_lock` 明确要求在 test 之前冻结。最终 test task expansion 没有 lock 会 fail closed。

## CPU 验证

- `tests/test_rq31_execution.py` 与 `RQs/RQ3_1/src/tests.py`：14 passed。
- `scripts/rq31_register_local.sh --check`：passed；未启动模型。
- 全部既有 `tests/`（排除缺少 torch 的 attention test）执行到 251 passed、7 failed；7 个失败属于既有日志依赖 `drain3` 缺失及既有 RQ3 temporal expectation，不触及本 C 文件改动。带 torch 的 attention test 在 tools 环境收集失败（`ModuleNotFoundError: torch`）。这些不能被本阶段绿色占位测试解释为完成。
- 已覆盖故障点：提交前无 phantom row；提交后响应前标记 spent/interrupted；响应 artifact 落盘而 summary 未写可恢复；只有 partial 不恢复；ledger 去重；PID 存活/复用校验。未作真实模型故障注入。

## 与计划的可执行性冲突及处理

当前最新数据角色取消 active validation，而 smoke skill 的旧通用文字仍要求 validation。用户本阶段明确要求只从 eval480 选开发和 smoke，因此本注册将 smoke source 固定为 eval，并拒绝 validation 配置；这不是擅自打开 test。若后续要恢复 validation smoke，必须先新增版本化数据角色和契约。

另一个容易混淆点是计划表的 54 smoke calls：每个逻辑实验的运行上限仍是 18 calls/600 seconds；注册的正常 smoke 路径只规划 3 cases × 2 models = 6 calls，剩余 cap 是重试/边界余量，仍按实际 initiated request 计费。

## 尚未完成

- A 的 `ContrastEvidencePoolV1/ContrastBundleV1/ContrastSelectionV1` 与 B 的 representation twin 尚未合并到执行 worker；当前只保留注入式接口，不会伪造 materialization 或 dashboard。
- 尚未实现三实验的真实 worker、完整 scorer private binding、summary aggregation、smoke supervisor 接合及 renderer/OCR/leakage/equality gates；因此不能宣称实验可运行或已 qualification。
- 尚未生成任何 solver conversation、input/output/cost trajectory；本报告与 research registration 是 CPU 注册证据，不是 RCA 结果。
- 不能在 test 阶段前选择方法或使用 test outcomes；需先完成 eval worker、smoke（每实验 ≤18/600s、Qwen 后 Gemma）、登记 method lock，再由组长授权 test。

## 2026-09-16 recovery pass (C)

已恢复并保存执行接口（仍为 CPU/未调用模型状态）：

- `build_solver_request` 现在对全部 14 arm 生成真实的 model-visible
  parts/envelope：继承控制复用 RQ1.1 `direct_rca_parts`；X/P0 对比条件复用
  B 的 `RepresentationTwinV1`，并把 actual request、projection、adapter 和
  dimensions 纳入绑定 key。缺失 prepared/A-B twin 会明确 fail-closed。
- `build_mechanism_request` 实际在公开 materialization 编译前执行
  no-contrast、no-grouping、no-shared-time、target/non-target bundle removal；
  双侧证据不足时返回 pending/error，不伪造通过。`REANONYMIZE` 在
  materialization 层一致重映射实体；`CANDIDATE_REORDER` 重排候选文本，拒绝
  对已有图片做假变换。
- `run_registered_experiment` 按 Qwen→Gemma 顺序使用共享
  `persisted_model_call`、RQ 级 28,000 ledger 和 canonical granularity-aware
  scorer；`aggregate_result_summary` 只在 inputs/outputs/cost/conversation/
  completion hashes 齐全时汇总，保留实际失败 cost，并提供 per-dataset 与
  per-fault-type MRR。`run_smoke_supervisor` 使用三个 primary eval stages、
  单一 18-call/600s aggregate（禁止 test/RE2）。
- 旧 `scripts/rq31_*` 已移动至 `RQs/RQ3_1/scripts/`。重新生成并 byte-check
  `research_registration_v1.json`；旧无模型调用注册保存为
  `research_registration_v1.pre_recovery.json`。
- `freeze_main_method`/`audit_method_lock` 新增真实 `ledger_hash` 要求，并继续
  强制 code/prompt/config/roster/results hash、eval registration 绑定以及
  test-outcome 先后关系。selector semantic budget 仍为 pending，未将 128
  示例值写入配置。

验证：

```text
pytest -q tests/test_rq31_execution.py tests/test_rq31_evidence.py \
  tests/test_rq31_representation.py RQs/RQ3_1/src/tests.py  # 39 passed
python -m RQs.RQ3_1.src.main validate-research                         # passed
python -m RQs.RQ3_1.src.main cpu-smoke --output /tmp/rq31-cpu-smoke-new       # 6/6, 0 LLM calls
```

CPU smoke 是 transport/persistence check，不是 Rule-16 qualification；尚未有
live vLLM、GPU、test telemetry、正式 eval score 或 E/D review。正式 worker 需要
上下文提供 A 的 complete pool/B twin 或冻结 RQ1.1 prepared case，以及 evaluator
private labels；没有这些依赖时按协议停止而不使用 fixture 冒充结果。

## 2026-09-16 correction after A/B recovery review

上面的 recovery pass 中关于“selector 标准语义预算固定为 128”、单一
18/600 smoke、以及执行层已完成全部干预的表述已被本节 supersede：128 仍是
示例容量，配置继续为 `standard_semantic_budget=null`、
`pending_A_B_capacity_resolution`；任何预算 worker 在冻结前停止。

- C 已接入 B 的 `rq31_solver_system_prompt`/`rq31_solver_read_guide`，并保留父版
  RCA task、schema 和 closing；TPV 通过 RQ1.1 的父版 TPV bridge，不能映射为 H。
  SIRCL_TEXT 明确 fail-closed，未用 T packet 冒充比较器。
- B 的 NO_GROUPING/NO_SHARED_TIME 通过
  `plan_representation_intervention` 和精确 renderer flags 实施：不改
  `materialized`、payload、fact 数量或 relative bins；display load 只接受 A 的
  `display_reference_schedule`，不复制事件。
- A 的 no-contrast selection、matched target/non-target removal、typed
  re-anonymization、预算 floor 和 redundant-load API 已接线。matched removal
  没有已冻结 payload 阈值时停止；not-applicable/no-op 不发请求。re-anonymization
  的 mapping 和私有标签只进入离线 scorer，不进入 prompt/renderer。尚无 A/B
  attested request 的 CANDIDATE_REORDER 和其它变换保持 fail-closed。
- `_request_envelope` 读取有效 unified vLLM projection，记录 40,960 context、
  served model name 和配置 hash；执行前拒绝错误服务模型/配置。共享
  `persisted_model_call` 的真实 response/token/latency fields 未被重写。
- smoke supervisor 现在将三项 primary-eval smoke 分成三个独立逻辑 stage：每项
  各自最多 18 initiated calls、各自 600 秒，聚合上限 54；非 timeout 错误为
  failed/incomplete，不能 complete。实现包含 deadline 检查和持久化边界，但尚未
  通过 live-server termination qualification。

当前 CPU 回归为 60 passed（execution/evidence/representation）；这只证明真实
builder seam、父版 arm 映射、B flags、request identity、恢复与失败门控在无模型
环境下工作，不代表 live smoke、正式 eval 或完整 stage 已通过。没有 GPU/LLM
调用、test telemetry 或正式 RCA score；C 的剩余阻塞是配置容量冻结、A/B 完整
context/private binding、CANDIDATE_REORDER 真实变换，以及 live vLLM smoke。

本次 `register-research --check` 的当前 registration hash 为
`dd83a9e84cb05f441aa979647a59c452c5335c63cb99acaed8fc8709fd1f1ffd`；旧段落中的
hash 属于恢复前字节版本，保留作历史记录。

## 2026-09-16 final execution recovery update

本节 supersede 上述尚未接线的执行描述。当前配置已登记 matched-removal 的
`max_payload_char_delta_fraction=0.10`，并重新生成 registration；标准 semantic
budget 仍为 `null`/`pending_A_B_capacity_resolution`，没有冻结 128 或以 ratio=1
补齐容量。

当前 registration hash：`0ac2c6dede310acbe02462132bbb27c446a2d71e11cf7cf0b73140340d6f6089`。

- 新增 `prepare-contexts` CLI 和 per-case hash-checked pickle cache。它实际读取
  processed V3，调用 RQ1.1 `prepare_case`、A 的 contrast pool/bundles，并保存
  PreparedCase、候选集和 evaluator-private scorer binding；`LazyExecutionContexts`
  一次只载入当前 case，支持重启后校验 hash/opaque identity。已用一个真实
  processed AIOps-22 eval case 端到端跑通到 cache index 完成，未读 test telemetry。
  P0/twin materialization 仍等待容量冻结，故没有手工构造 mapping 或虚假 twin。
- 接入 A 的 source-adapted `build_sircl_text_comparator_from_v3`：SIRCL 的
  MET-Z/TRC-L/LOG-R 文本作为唯一 user payload，native role 进入 system，绝不以
  T packet 冒充。当前真实 CLI 在 adapter 隐私检查处因 dotted metric/service
  名误触过宽的 host 正则而 fail-closed；该问题已回报 A，未在 C 侧绕过 gate。
- 正式（非 smoke）execution 已使用最多 36 个 bounded worker 提交已绑定请求；
  smoke 仍按三个独立 18/600 stage 顺序执行，并使用独立 `smoke:<experiment>`
  ledger scope 防止三个 stage 互相消耗 cap。提交/完成、实际 token/cost、失败
  和 ledger 状态均由 durable writer/ledger 记录，失败不会被标成 complete。
- 新增 `model_phase.sh`：每个模型独占锁，使用 canonical
  `serve_canvasrca_local.sh`，先通过已注册 served-model readiness 检查，再运行
  单模型 phase，退出时终止服务器；未启动 GPU/LLM。
- `tests/test_rq31_execution.py` 当前 22 passed，ruff 与
  `validate-research`/`register-research --check` 均 passed；另以真实 processed
  case 跑通一个 T-arm CPU execution（1 record，0 LLM calls）。这些是执行/恢复
  证据，不是 live smoke、正式效能结果或 test 结论。

### Freeze and bounded-recovery audit

`freeze` 现在只接受磁盘上的 complete eval `summary.json`，从完整 Qwen
candidate/T cohort 重新计算 champion；调用者传入的 method/hash 只能作为一致性
断言，不能选择结果。它重新计算 code/prompt/config/roster/result digest，并用
eval-subset call-key snapshot 生成 ledger hash；拒绝缺失/伪造 inventory、已有
final-test ledger/artifacts，以及已存在的 method lock。`audit_method_lock` 也会
重新验证这些来源，而不是信任 `test_outcomes_present=false`。

smoke supervisor 可通过 `--smoke-started-at` 接收 server startup 前捕获的 wall
timestamp；首个 600 秒 deadline 会包含 readiness/startup 延迟，后续两个逻辑
stage 各自重新计时。新增 CPU 时钟回归覆盖 startup 已超时、三 stage 独立 cap；
重用 ledger entry 不新建 attempt，skip/no-op 不进入 request/scorer/call。

本轮联合 CPU 回归为 71 passed（execution/evidence/representation）；没有 GPU、
LLM、test telemetry 或正式结果。真实 context cache 成功路径仍是：
`/tmp/rq31-context-cache`，命令为
`RQs/RQ3_1/scripts/prepare_contexts.sh /tmp/rq31-context-cache 1`；该缓存是在
SIRCL adapter 修正前生成，SIRCL 新缓存需 A 修复 dotted-host 正则后增量重建。

## 2026-09-16 final-test gate and logical-experiment correction

- final-test CLI now requires `--method-lock`; task expansion calls
  `allow_test=True` only after the lock is loaded and audited. A final-test
  lock records the ledger max-id high-water mark at freeze. Pre-freeze orphan
  rows/artifacts remain rejection conditions; legitimate post-freeze rows are
  accepted only when their persisted input manifest carries the exact lock and
  config digests, so recovery after a first test call remains possible.
- Registration explicitly groups seven internal execution batches into three
  logical experiments: effectiveness; mechanisms (mechanism/replicate/budget
  batches); robustness (robustness/load/final-test batches). Exactly one
  18-call/600-second smoke parent is associated with each logical experiment;
  the seven batch IDs are accounting/resume identities, not seven independent
  scientific experiments.
- Fresh registration hash after this metadata correction:
  `f0de58faf3d09725c49b923d158f53b3f564fd36cae0f6aa0ca755b887f198cc`.
  Execution/registration tests: `33 passed`; ruff passed. The combined
  representation suite currently has two unrelated B-owned fixture expectation
  failures (missing `values:/observed counts:` wording and trace
  `baseline_ms` key); C did not alter B files.
