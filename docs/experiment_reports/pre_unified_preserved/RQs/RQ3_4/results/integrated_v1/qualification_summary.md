# RQ3.4 资格测试汇总 — 2026-09-24

**最新状态：相对时钟修复及用户授权的定向GPU补验通过，四项当前qualification均为passed；正式实验未启动。**

| 本次补验 | 新调用 | 结果 | 执行耗时 |
|---|---:|---|---:|
| 契约 | 6 | 完整通过；1非法候选按模型失败保留 | 209.09秒，含入口修复前退出共314.40秒 |
| 因子 | 4 | 完整通过 | 210.89秒 |
| 图文绑定 | 6 | 完整通过 | 211.19秒 |
| 锁定复核 | 0 | 2变化单元同输入复用，16原单元引用 | 0.004秒 |

45项CPU测试及120个请求身份等价检查通过。72逻辑单元＝54不变引用＋16新推理＋2等价复用；36对跨模型公开输入一致，conversation、raw、PNG与计数完整。16新回答均stop、无截断/infra失败；6份回答12处字面类型误称及其他reason问题如实保留。累计3,395调用；原7次中断不删除。首次补验入口clock参数误传在请求前退出，0调用，其105.31秒和日志均保留计入时间预算；修复后未再出现。

权威审阅：[review.md](repairs/relative_clock_gpu_v1/review.md)、[final_review.json](../../../../../../../RQs/RQ3_4/results/integrated_v1/repairs/relative_clock_gpu_v1/final_review.json)。旧flags、原始结果和failed报告均未覆盖；`qualification/`指向新补验。全部自有测试服务已退出，无正式实验、训练或attention。以下表格和文字保留前序过程状态，不替代本节最新资格。

## 历史资格与修复过程

| 检查 | 结果 |
|---|---|
| Ruff／shell语法 | 通过 |
| 单元测试 | 最新42项通过，含时钟投影和384次并发solver生命周期测试 |
| 真实CPU输入回归 | 3 datasets × 1 case；120个完整arm/model请求通过 |
| 首次CPU时间 | 34.07秒；各case新增准备15.43、16.69、19.47秒 |
| 修复后CPU时间 | Z3修复17.87秒；本次补验入口回归20.97秒，120个输入身份均一致 |
| 时钟修复CPU时间 | 缓存投影与回归53.64秒（不含前置归档复制）；其中CPU资格16.15秒，120请求通过 |
| 时钟修复输入变化 | 96请求身份不变、24改变；3 case共12组P/H选择不变，TPV/MORE请求与G图不变 |
| 实际回答CPU核验重放 | 38份回答×5次＝190，0.68秒，无崩溃、已有verdict一致 |
| 已完成单元续跑实测 | 9个单元0.602秒直接跳过，零新请求、无准备重建 |
| exp_contract_alignment smoke | 原18/18完成，232.63秒；SIRCL时钟修复影响6输入，当前待GPU补验；原2份非法候选保留 |
| exp_evidence_reasoning_factorial smoke | 原18/18完成，243.18秒；时钟修复影响4输入，当前待GPU补验 |
| exp_verified_visual_binding 原smoke | 失败：9次发起，2份完整回答、7份partial；原失败记录保留 |
| exp_verified_visual_binding 授权补验 | 16新＋2复用＝18完成，250.50秒，无新崩溃；时钟修复影响6输入，当前待GPU补验 |
| exp_integrated_locked_check smoke | 原18/18完成，250.97秒；时钟修复影响2输入，当前待GPU补验 |

第三项Z3默认context并发段错误已修复；用户明确批准一次性16新增／600秒补验，现已完成。本项累计25次包含原中断；原失败报告不覆盖，其他smoke上限不变。两份原完整output逐字节保留，九对case×arm公开输入在两个模型间完全一致。

新请求总79次（72完成、7中断），加历史3300次合计3379。没有新增attention，没有训练，没有正式case队列，自有测试服务已退出。本补验按登记仅测试Text条件；视觉条件使用此前核查的冻结原TPV图。18份回答可解析且候选合法；4份回答中的5处实体类型称呼错误被核验器捕获，不能据此声称它捕捉所有错误或证明因果推理。

时钟修复：三个登记时钟指标共用一个公开case-local原点，只平移显示值，保留前后／跨实体差、MAD/std、选择统计。最初发现追加观测启动时钟的12单元清单保留；CPU回归进一步发现SIRCL `container_last_seen`，新增6个受影响逻辑单元，因此最终是18个，不是12个。没有证据表明这些值就是注入时间／根因标签。三个SIRCL条件共同适配，不改其原选择或其他诊断字段。详见 `repairs/relative_clock_v1/migration.json` 与 `final_consistency_audit.json`；首次CPU拦截记录另行保留。先前16次新增GPU授权已用完，本轮零新增模型调用，未自动补验。

协议、输入与输出可追溯：`registration.json`、`cpu_qualification.json`、`cpu_examples/`、`smokes/`、`stages/`、`qualification/`、`contract_migrations/z3_context_v1/`。详细事故见 `docs/issues/RQ3_4_qualification_2026-09-24.md`。历史Z3修复阶段曾凭输入完全一致承接前两项资格；本次时钟修复改变输入后，这不再是当前通过凭据。旧报告不改。

本次补验授权与原stage副本：`contract_migrations/authorized_smoke_repair_v1/`。时钟修复前的输入、配置和资格快照：`repairs/relative_clock_v1/previous/`。四项当前资格与旧运行记录分别保存，不抹去原运行成功或原崩溃，也不把旧回答复用于已经改变的请求。
