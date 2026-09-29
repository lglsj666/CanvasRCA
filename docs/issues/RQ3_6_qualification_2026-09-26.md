# RQ3.6 阶段 A 实现及资格记录

本轮范围：11个A条件；不启动正式实验，不提前实施依赖A结果的B–D。保持历史源代码、配置、结果不变。

## 静态审查1：科学逻辑与组件隔离

- 沿RQ3.5 crossed_parts和RQ3.4 integrated_parts逐条追踪11条件，两个新条件只交叉G/V完整指令块，两者都有VERIFY/REVISE。
- 发现并修正新代码中 `_parts_from_prepared` 的模块导入位置（实际位于RQ3.1 main），避免延迟导入在CPU/GPU才报错。
- 确认P/S整包对照，不将来源统计/窗口差异伪装纯selector。新方法未使用gold、历史成绩或case路由。
- 发现父版Trace单位字段标注错误：stored微秒未转换，字段却命名ms。证据链为 unified_scripts/sircl_data 的源duration存储→vlmrca.processed原样读取→RQ1.1 panels直接聚合；对照RQ3.1 `_registered_trace_duration_projection` 和S分支×0.001。
- 独立RQ3.6 `parent_trace_unit_labels_v1`仅修三个时延字段后缀及复合unit。数值、排序、选择、+1平滑、G图不改。既有历史不重分类、不覆写；CPU抽查真实输入进一步确认。

## 静态审查2：资源、执行链与恢复

- 使用现有完整public context，无raw读表/OLE重建；最多8独立物理核心、每case一次加载，两模型CPU预检。准备队列≤worker数，推理队列≤36，CPU/GPU可重叠，不积压整套prepared requests。
- done及request-timeout fail只读小flag跳过；其他infra fail停止、不自动重试。flag由共享executor在输出、评分和audit写完后原子提交。partial不可拼接，尝试保留调用计数。
- 只从RQ3.5库导入历史计数，避免同时导入其已包含的RQ3.4造成双计；总40000、scope18、跨模型identity、scope去重分别检查。
- 服务只管理新session所有权；退出leader的children也清理；拒绝接管已有服务。smoke600秒覆盖启动/切换，正式路径另需用户授权，CPU/smoke通过不自动开跑。
- 底层错误会排空已有写入；磁盘不足停止新提交。源码hash仅小代码/配置文件，无per-case/hash全量恢复。

## 静态审查3：泄漏边界、语法与可执行接口

- 模型编译入口只读public context；private在构造actual request之后用于scorer；dataset仅离线选择资格病例/来源单位，未注入prompt。
- 沿SIRCL时钟适配、numeric候选、来源manifest和G图复用链检查；新增代码不调用注入时间、不接触模型权重训练。
- Ruff及AST语法、shell bash-n、import符号链检查；CPU测试将验证两模型token容量、私有标签扰动不影响输入、三个实际PNG、artifact持久化与66请求。
- 这三轮是不同检查面，不代表静态证明无bug。CPU与GPU结果见后续条目。

## 运行结果

已完成，正式实验仍未启动。

| 检查 | 结果 |
|---|---|
| 三轮静态 | 逻辑、运维恢复、泄漏/语法分别审查；最终Ruff和bash-n通过 |
| CPU回归 | 6项单元测试；3病例×11条件×2模型=66请求；最终9.914秒，0模型调用 |
| GPU smoke | 两模型各9，18/18完成；原600秒窗口内558.820秒；全部完整输出，无截断/非法候选 |
| 输入输出复核 | 完整会话及raw/score/cost/completion一致；3张实际PNG；18份输入与CPU注册identity一致 |
| 后台状态 | 本轮服务和workers均退出；没有正式实验授权文件 |

CPU发现projection使用了与统一bind_task_request不一致的digest序列化，改为统一stable_hash，之后回归通过。GPU发现post-response audit缺少`projection.image_hashes`：9个Qwen请求事实上均已完成且输入/输出/评分落盘，但该后处理异常写了fail标记。补齐metadata并将真实sidecar接口纳入CPU回归；逐条比较保存请求与当前编译，恢复这9份结果的audit/完成标记，**没有重新推理或修改答案**。旧失败报告及源/CPU快照保留在repair目录；Gemma在CPU重测通过后继续。始终使用原启动时间/截止时间，18次总额度没有重置。

两个新指令条件和W_NO_K各3例×2模型实际live覆盖；其他8条件本轮只有CPU覆盖及父版路径复用，不夸称11条件全部做过新GPU调用。模型类型误述、入口/根因混淆及图像引用错误另存人工审阅，不按smoke正确率修改条件。S输入的literal audit数值/关系覆盖不足已明确记录，不能把未解析说成没有错误。

完整审阅：[manual_review.md](../../RQs/RQ3_6/results/replication_v1/manual_review.md)；机器记录：[qualification.json](../../RQs/RQ3_6/results/replication_v1/qualification.json)。最终contract：`5d77be32458c919e32d61225f40fa32e4b5fddb3b5cbd2c2dfc2d1adda2b7e39`。
