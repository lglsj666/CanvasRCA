# RQ3.17 v4：仅加粗 topology 虚线

2026-10-03 用户最新明确范围：**只修改 Observed calls and request parents 的虚线；Observed deployment membership 完全不变。** 本修订使用 1.4 → 4.2（3×），仅适用于上方调用节点图的 request_parent 虚线。虚线箭头尖端按SVG原有strokeWidth规则同步放大3倍。calls 实线及其实线箭头、全部部署关系线及箭头、矩阵图元、配色、虚线节距、节点、文本、布局、耗时图和所有实验定义不变。

复用 unified renderer 的 component 操作，增加显式可选的 `dashed_width_scale` 参数；默认保持原行为。新配置、预备图及例图库使用 v4，v3 源及所有历史图片保留。十四臂、已暴露 eval220、比较族、额度和暂停状态继承 v3。本次只做代码、静态及必要渲染检查、三个固定病例例图，GPU/正式实验继续暂停。

核对新旧文本和事实相同、非节点臂 PNG 完全相同、节点图仅 CALLS 虚线宽度改变、部署面板像素完全不变，并检查只有 CALLS 虚线箭头尖端通过 SVG 的 strokeWidth 单位同步放大3倍。新版例图导出到 `C:\Users\10511\Downloads\例图\10_02\RQ3_17_v4` 后停止。
