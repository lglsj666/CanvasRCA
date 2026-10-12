# RQ4.4 source views — current state

2026-10-12：**正式840/840全部完成并完成详细分析；总实际调用858（含18次smoke），0基础设施未知，0新增分析调用。自有服务已停止。** 660主矩阵、120 QA、60真实重复/顺序扰动均完整；42次恢复预留未用。

| Arm | 标准MRR | 宽容MRR | 平均input＋output token |
| --- | --- | --- | --- |
| SOURCE_ZOOM（预选） | 0.3286 | 0.3431 | 14,094.89 |
| REPEAT_VIEW | 0.3230 | 0.3438 | 14,098.71 |
| HASH_ZOOM | 0.3120 | 0.3309 | 14,103.03 |

SOURCE相对历史U（0.3517）的MRR为−0.02318，总token为2.409倍；相对历史强文本成本0.6337倍但MRR低0.15606。SOURCE相对两个同期控制的主要事件组比较Holm p均为1。按预登记停止条件，结束本次局部高清候选，不采用、不自动追加布局实验。

固定30例目标隔离QA两数值正确30/30；SOURCE完整图4/30。SOURCE中23/30次QA数值匹配另一真实卡片，其中18次是局部图中非目标卡。目标本身只有2/30进入SOURCE局部图，不能将完整QA差异直接归因于高清。实际阅读120 QA＋150 RCA（含重复/顺序）后记录了错目标、混绑、单位及理由—排序不一致，属于已暴露开发数据的探索观察。

270份正式attention记录、540个query映射全部核验；另有9份smoke。范围仅第3层最后prompt/首个decode，不覆盖最终排名字段。完整输入PNG、提示、输出、评分、来源及实测attention均保留为直接可读文件；最终存储及hash清单见retention.json。报告修正自动初稿P@3计算，原MRR/AC/评分和冻结输入未修改。

本轮已完结，无待恢复正式请求；下一轮需要新计划。既有CPU、GPU资格和冻结历史保留。

[最终详细报告](../../../docs/experiment_reports/RQ4_4_Qwen_Analysis_2026-10-12.md) · [统计附件](../results/source_views_v1/analysis/detailed_v1/main_summary.csv) · [人工审阅](../results/source_views_v1/analysis/detailed_v1/qualitative_review.md) · [存储核验](../results/source_views_v1/retention.json) · [CPU报告](../../../docs/experiment_reports/RQ4_4_CPU_Qualification_2026-10-12.md) · [GPU报告](../../../docs/experiment_reports/RQ4_4_GPU_Qualification_2026-10-12.md)。
