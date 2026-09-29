# Unified renderer：独立研发原型

2026-09-28，用户授权实现；不接入正在运行的 RQ3.7 C，不启动新推理。

## 决策与边界

用户随后明确指定实现位置为 `src/renderer/`，替代起初拟定的 RQ-local 目录。
这是可复用接口的试验场，不是替代历史 renderer 的新全局权威。
本次明确授权的源码组织例外：Python、`web/` 中的 React/TypeScript/CSS、
`scripts/` 和 `configs/` 全部收在 `src/renderer/` 下。
任何后续正式实验仍须冻结自己的版本、配置和输入。

分离三个对象：已选公开证据包、设计树、系统关系图。证据选择不属于 renderer。
设计树描述 row/column/grid/panel 嵌套；调用图允许环、孤立节点、自环及多种关系。
用户追加要求：从此新接口将“剪影”更名为“dashboard 组件”，旧报告不追溯更名。
`web/components/` 一文件一个组件，`configs/components.json` 注册稳定类型编号；
`operations/` 一文件一个全局操作，`configs/operations.json` 注册操作及参数。
每个实例同时有稳定 evidence ID 与显示 index，index 不因位置移动而变化。
组件不承担隐式筛选。树操作、组件替换操作和归属连线
操作分别配置；一次树修改未必只改变一个科学变量，必须比较实际几何。

Python 验证 DTO、计算确定性整数布局；React/SVG 绘制真正的曲线、条形、矩阵、
拓扑，CSS 处理外观与排版。Chromium 在固定 viewport、字体、locale、DPR 下
离线输出单张 PNG 和可独立打开的 HTML。禁用 GPU、动画和远程资源。
不运行开发服务器，不修改 inference 虚拟环境。

v1 覆盖 metric lines/time-bars/heatmap、trace paired-bars/dumbbell/table、
log timeline/table、topology node-link/matrix。设计空间由配置白名单约束；
新的图形语法仍需实现组件，不能声称任意 dashboard 无需改代码。

## 验收

- 同一 evidence 下所有 preset 保持相同 card inventory；不允许未引用/重复引用卡片。
- 外部 renderer 输入只接收严格公开 DTO；原来源路径、case ID、标签留在离线审计。
- 默认无诊断结论色；实体类型、单位、相对 bins、关系方向明确。
- 连续图连接相邻有效观测，不将缺失填零，不添加 missing-bin 说明。
- 输出 evidence/design/geometry hashes、字段到图元绑定、真实 DOM 边界、PNG hash。
- 拒绝越界、卡片重叠、文本溢出、未知字段及不支持的 encoding；不得自动删卡。
- 真实预览只取已有 development 案例的已缓存公开输入，不访问 test 或重新 preparation。
- 旧 packet → v1 DTO 的投影字段与未支持字段在审计中明确列出；此原型不宣称与
  旧 M/R/L/G 全请求逐事实对等，也不把 manifest 中的存在当成已绘制。
- 先静态检查，再小规模 CPU/浏览器测试、真实 PNG 人工审阅；无 LLM calls。

## 后续使用

完成原型后，后续实验可以传入 evidence JSON 与 design JSON 获得 dashboard。
只有真正改变公开事实时才修改 evidence；编码、布局、主题、字体和输出 scale
由 design 控制。网页实现、美观和缩短渲染时间都不构成 RCA 收益证据。
模型 processor 后的清晰度、上下文容量及真实 RCA 仍需另行资格化。

技术依据：[React 静态 HTML](https://react.dev/reference/react-dom/server/renderToStaticMarkup)、
[Playwright screenshot](https://playwright.dev/docs/screenshots)、
[esbuild TSX bundling](https://esbuild.github.io/getting-started/)。

此决定暂不改变 RQ3.7 的任何科学参数、输入或运行队列。

## 2026-09-28 补充：拓扑独立于异常证据筛选

用户指出旧过滤结果不能代表完整系统关系。核查开发样例：AIOPS-2022
旧 packet 只有 9 条调用边，canonical per-case graph 有 121 条；AegisLab
旧 packet 有 4 条，canonical graph 有 107 条混合关系（进一步核查源码：
58 条调用＋49 条部署，不能全部称为调用边）。新原型不再以冻结小 packet 或 ALL_ID 的选中关系
作为全图来源，而是读取对应 public per-case graph 与完整 Trace 身份列。
后者仅以同 trace 的无歧义 parent/child 关系补边，不按异常、top-k 或分数过滤。
日志与指标筛选保持原样；不读原始全表、不调用 LLM、不修改正式实验。

全图指当前 per-case 窗口内可观测的关系，不保证恢复未被采集的真实系统全图。
完整调用图、明确部署关系、已计算的公开异常时间分别成组件；时间先后不是
因果传播。RQ1.1 的时间展示可借鉴，但不沿用其行/边上限、同时间边省略和
反转调用箭头。异常时间沿用原公开相对时间，不使用注入时间。

替代本原型先前默认显示所有孤立节点的规则：每张关系组件只显示该完整关系
集合中有边的端点；单独的 Metrics 和异常时间组件不因此被删除。数据库、缓存、
队列等依赖保留有来源的边与匿名身份；角色来自显式类型或精确公开产品名白名单，
不把任意包含 SQL 的操作名当作一个数据库。新外部端点使用独立匿名命名空间，
不改变历史服务/node/pod ID 或 Solver 候选集合。任何来源缺口与不能消歧的 parent
留在离线审计，不伪造边，也不宣称无边就是实际无联系。

`graph.show_isolates=false` 是明确设计参数，输入节点库存仍保留；隐藏的是图中的
零度节点，不是证据卡片。`events.onset` 第 11 号组件展示已有公开 onset、z 与来源；
尚不重新计算所有实体的异常时间。大图使用按连通组件排列的稳定格点与间隙布线，
无 top-k；密集图的边交叉不能靠删除真实边解决，可显式切换为邻接矩阵。

## 2026-09-29 补充：逐边成对拓扑组件

按用户要求新增 `graph.edge_pairs`（第 12 号组件），原 `graph.node_link` 和
`graph.matrix` 保留。将每条边单独画为“源实体 → 目标实体”，显示原关系类型；
例如 A→B→C→A 显示为 A→B、B→C、C→A 三个独立关系单元。不是将环裁成树，
不丢弃反向边、自环或同端点不同类型的边，也不重新筛选完整关系集合。

同一实体可能出现在多个单元中，重复出现使用同一数字 ID，不生成新实体。
事实审计区分首次绑定与冗余图元引用；边仍一一对应。默认隐藏孤立节点的规则
不变，显式启用显示孤立节点时仍需保留它们。画不下应报告容量不足，不能删边、
滚动截图漏边或自动缩小字体。`pairs` 是便利预设，可分配较大面积；它不自动与
旧预设构成单变量对照。受控比较须冻结足以容纳各组件的共同外部几何，仅替换
组件类型。逐边图更少交叉但重复实体、多跳路径需跨单元联系，哪种更利于 RCA
尚待实验；本次不新增模型调用，不更换正在运行的任何 arm。

## 2026-09-29 补充：部署分组组件

按用户要求，新增独立 `graph.deployment_groups` 组件：node→{pods} 与
service→{pods} 分开显示，保留网络、矩阵及逐边版本。相同 pod 可在宿主组和
服务组中重复出现，但始终使用同一匿名 ID。组中每个成员仍绑定一条原关系，
不得通过分组漏掉成员；不将调用边转换为归属关系。

节点部署来自公共 `node_pod_map`；服务对应优先保留明确 `service_pod_map`，
另从完整 per-case Trace 的 `service_name` 与同条资源属性 `k8s.pod.name`
提取实际观测到的服务实例关系，单独标为 `has_instance`，不称为 Kubernetes
ownerReference 或调用。不通过 pod 名称前缀猜服务，不从已筛选 Trace 小表推导。
命名空间歧义、未绑定身份仅离线报告，不生成猜测边。新组件只改变原型默认
部署画法；新增服务对应关系另记来源与覆盖，不冒充同事实画法变化。
不更改任何历史或正在运行的实验输入。

## 原型完成记录

已实现 10 种 dashboard 组件、9 种操作，均有独立实现文件和编号目录。
静态检查、19 项 CPU/浏览器回归通过；三个主数据集的既有开发案例已生成
5 张真实预览（包括同事实的矩阵版及浅色关系优先版），约 0.67–0.77 秒/张。
见 `src/renderer/README.md` 与 `src/renderer/QUALIFICATION.md`。
预览在 `build/renderer_previews/v1/`。没有新增 RCA 推理或修改在跑的实验。
