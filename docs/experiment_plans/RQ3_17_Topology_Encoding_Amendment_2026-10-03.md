# RQ3.17 v2：矩阵与节点箭头的成对拓扑对照

本修订由用户要求增加节点箭头版本、检查颜色和编号绑定而产生。实施范围为代码、静态与必要组件检查、真实例图；CPU 全量资格、GPU smoke 和正式实验继续暂停。v1 输入、例图、报告与源归档保留，v1 CPU 通过不等于 v2 资格通过。

主线保持：保留完整公共诊断事实，在同事实强文本上验证可分离的视觉收益。本次不选择新的最高分方法，也不把布局可读性视为 MRR 证据。

## 设计变更

保留九个原 arm 名称（其拓扑是矩阵），新增五个对应 arm：

| 原矩阵 arm | 新节点箭头 arm |
|---|---|
| TOPOLOGY_VISUAL | TOPOLOGY_VISUAL_NODE |
| TOPO_MARGINAL_BOUND | TOPO_MARGINAL_BOUND_NODE |
| TOPO_MARGINAL_UNBOUND | TOPO_MARGINAL_UNBOUND_NODE |
| TOPO_MARGINAL_MARKLESS | TOPO_MARGINAL_MARKLESS_NODE |
| TOPO_MARGINAL_REPEAT | TOPO_MARGINAL_REPEAT_NODE |

BASE_FIVE、PAIR_TEXT、MARGINAL_MATCHED、MARGINAL_NATIVE 共用，不重复增加。合计14×220=3,080正式位置，登记42个基础设施重试余量，正式上限3,122；smoke仍18调用/600秒，总上限3,140，不重置历史消耗，不表示执行授权。

两种拓扑使用相同全部节点、类型、方向和关系账本；调用与部署均切换画法。字体、画布、组件槽位与耗时图尺度按两种画法所需容量的较大值共同确定。只依赖公开图结构，不按故障标签、模型结果或异常分数布置节点。保留所有边、孤立节点、自环、多关系与循环；不通过删边、缩字或裁图通过容量检查。

绑定统一改成颜色＋数字：同一准确 request_parent 边共享一个标记，多张操作卡允许共享同号；保留操作名区分卡。不同边编号不同，编号仅标识映射，不表示优先级、异常或因果。所有 T 系列文本获得相同编号—父子边—操作卡对应表；同色同号出现在目标图元及卡片上。U 只移除这些标记，K 只移除耗时样本点。两个重复臂分别与其画法组合臂输入完全相同，始终独立调用。

使用现有 graph.node_link、graph.matrix、graph.membership_matrix、trace_joint.marginals 与 component/layout/appearance/relation_bindings 操作。现有节点图默认多环排列在本批部署图最多105节点下无法维持节点间距，因此为 graph.node_link 增加显式可选的 layered_grid 排列，旧默认完全保留：强连通分量仅用于确定层次，循环及原始边照画，层内按ID分行。布局参数通过现有 component 操作选择。relation_bindings 增加可选 numbered 样式，旧虚线默认行为保持。

这不是历史 RQ3.6/3.7 图片的逐像素复刻；它检验同事实、同画布上的矩阵与节点箭头表达差异。历史参考：RQ2.1 S_G_LAYERED 五集宏MRR .3943，S_G_MATRIX .3644；这不是已确证分层显著胜出的结论。

## 统计与队列

原六项主要比较、矩阵预选方法与采用门槛保持。新增预先登记的次要 family：五项 NODE−对应矩阵比较（含重复臂）；另一个六项 family 为 C_NODE−T/G_NODE/D/N/U_NODE/K_NODE。分别报告病例和事件组 Holm、Pratt、dz、完整指标与成本。NODE 不能事后取代预选方法获得确认性采用资格；画法无显著差异也不等于排除了画法影响。

正式恢复时，第一阶段先完成两种 bound 组合的全部440位置，哈希交错；其他12臂随后运行。C/C_NODE各自保持独立规范请求，不因回退引用而提前调用其他臂；两个repeat均在第二阶段。暂停状态下不执行此队列。

未来单一18调用smoke覆盖全部14臂：A22 C/T/G/D/U/K；A25 C_NODE/BASE/G_NODE/N/R/U_NODE；Aegis C_NODE/T/D/K_NODE/R_NODE/N。不因增臂扩大smoke。实际processor输入预算和上下文必须对两种组合均检查；任一失败如实停止，不放宽门槛。

## 本次交付与边界

静态检查、受影响的组件/绑定回归与固定三个eval病例的例图检查；同病例成对比较，输出到Windows `例图/10_02/RQ3_17_v2`。旧目录保留。例图不用于评分筛选，生成例图不构成完整220例资格。待用户审图后再决定是否恢复后续资格。
