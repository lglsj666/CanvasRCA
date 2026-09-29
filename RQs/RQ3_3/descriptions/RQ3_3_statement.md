# RQ3.3 — Diagnostic witnesses and selective vision

状态（2026-09-23）：源码静态检查、三例CPU回归及五项两模型bounded GPU smoke通过；90个逻辑单元对应86次真实调用，完整输入输出已核对。可选EVENT分支不具备本轮样例资格，不包含在live通过声明中。未启动正式推理或训练，当前用户授权范围为CPU/smoke及问题修复，不包括正式实验。详见[问题与补验记录](../../../docs/issues/RQ3_3_implementation_review_2026-09-23.md)。

随后用户授权启动正式顺序队列；当前执行状态以`results/witness_v2/formal_queue_status.json`为准。此次授权覆盖既有注册顺序及条件式推进，不改变开发阴性时停止扩大、EVENT/fresh资格和不训练的边界。队列启动后不要求Agent持续监控。

> Can source-grounded, explicitly computed diagnostic witnesses improve a frozen one-shot RCA solver while preserving its strong TPV backbone, and when does visual relation encoding add value over equally organized text?

本研究承接 [最新版跨 RQ 计划](../../../docs/CanvasRCA_Next_Research_Plan_2026-09-22.md)。不整体替换 P0，不把“有根因相关 telemetry”当作正确诊断，不以更多实验 arm 或美化 dashboard 代替 MRR 改善。

方法把完整保留的 TPV 基础与一个有界追加区分开：新观测由完整 per-case public telemetry 提取；释义只能来自已核验测量定义；显式计算只能使用同一 RAW 条件已经给出的操作数；请求群体必须具有实际 trace/span 关联。选择不接收根因、fault type、注入时间、模型答案或成功标签。

默认部署仍为单次冻结 Solver 调用，一张 G 图加 M/R/L 文本及少量文本见证；W_T 把同一 G 改为完整关系 ledger。多调用诊断仅为阴性开发结果的机制研究，不属于 one-shot 主方法。无训练、无 attention 大文件、无外部计费 API、无 subagent。

既有 RQ1.1、RQ2.1、Tournament、RQ3.1、RQ3.2 的代码、结果、图像及报告保持原状。历史请求只在完整输入、模型配置和 scorer 可核对时引用；无法证明兼容则占用本轮预算重新调用，不能修改旧记录来凑兼容。

本轮成功标准不是必须宣布视觉有效，而是：在强 TPV/SIRCL/扩容控制下先取得配对诊断收益，再说明收益来自观测、释义、计算、群体信息、上下文位置或视觉组织的哪一环。

当前采用Witness v2注册：增加同请求集合的联合/边际统计、固定背景证据对及局部/远处绑定控制，并以嵌套预算检查准确率—成本关系。信息论用于提出可证伪假设，不将RR交互称为PID，不将token称为Shannon bits，也不训练估计器。机制控制不加入部署候选池；CPU通过不代表GPU资格或诊断效果通过。
