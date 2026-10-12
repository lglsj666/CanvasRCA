# RQ3.21 — Compact evidence and entity organization

日期：2026-10-06（America/Toronto）。唯一当前状态：**正式实验全部终态，离线最终审核与详细报告完成；预选方法不采用，自有 GPU 服务已关闭，未启动后续实验。** 完整结果以 [RQ3.21 最终报告](../../../docs/experiment_reports/RQ3_21_Qwen_Analysis_2026-10-06.md) 为准。

2,020逻辑位置：1,767新返回＋21同期精确请求引用＋220历史锚点引用＋12基础设施超时。超时保留未知；8个逻辑无效回答保留零分，其中2个为历史锚点。正式1,814次尝试＝1,767返回＋12超时＋35关机中断，另18次smoke，共1,832/1,940。47次中断/超时无完整usage，不按零补齐。

A/RT/RV/PV/EV/CT/CV整体MRR：**0.5054/0.4436/0.4934/0.4307/0.4866/0.4029/0.4180**。A是RQ3.16历史引用，RV/PV/EV已知分母219/218/215，其余220。CV−A−0.08742（病例/组Holm p=0.02908/0.06099），CV−RT−0.02561未通过校正；三个数据集对A均下降，排名目标失败。CV实际input＋output较A减少16.76%/17.70%/16.29%，较RT减少13.34%/14.13%/13.19%，成本目标通过。RV−RT配对+0.04779、CV−CT+0.01508的平均正向信号保留，表示族校正未通过；不事后追认赢家。

机制：联合编码/组织后严格QA配对下降9.77/6.90个百分点；单位字符串评分边界如实披露。去掉单位要求，同病例阶段方向仍下降24.14/22.41个百分点（事后描述）。位置旋转文本/视觉首选翻转22/60、20/60，独立重复1/60、2/60，额外翻转通过预注册校正；文本旋转MRR上升、视觉下降，不把全部翻转当损害。未采集attention，不归因attention sink。

最终审核通过211冻结依赖身份、220公共/私有包、211PNG、1,987唯一完整提交图、2,008实际逻辑输入/token及20项病例/组统计独立计算。固定36例108份理由定性阅读，6例9条公共来源记录核验；发现实体、耗时类型、阶段及解释—排名矛盾，不估计总体解释错误率。正式已知新token36,260,494，smoke358,024。历史锚点跨轮；全部病例为已暴露eval；QA不直接代表边际图读取能力。

保留原完整证据/原生边际图为受保护参照，不采用当前紧凑实体组合。后续方向是保持局部实体—阶段—单位绑定的单阶段成本优化，需另行设计登记；本次没有新推理、训练、renderer修改或编码部署。

材料：[最终核心表](../results/compact_entity_v1/formal/analysis/complete_core.json)、[独立审计](../results/compact_entity_v1/analysis_reviewed_v1/audit_and_supplement.json)、[例图索引](../preparation/compact_entity_v1/examples/index.html)、[资格与启动历史](../../../docs/experiment_reports/RQ3_21_Qualification_and_Launch_2026-10-06.md)。冻结契约 `635f9be2633b7b2a4aa97259aa9ce874cb8bd63bafa4ba7a36a922dcaf088754`。

历史关机恢复凭据保留于[verified.json](../results/compact_entity_v1/formal/resume_20261006_power_loss/verified.json)。未重跑已提交结果；正式服务当前inactive/success。CPU、407.99秒18/18smoke和恢复审计保留其历史时点含义。
