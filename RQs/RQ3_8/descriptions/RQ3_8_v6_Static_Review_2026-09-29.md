# RQ3.8 v6 — 三轮静态审阅

日期：2026-09-29。范围：本地 `/home/lglsj/CanvasRCA_nibi` 的计划、源码、配置与浏览器 bundle。
**结论：所执行的静态检查通过。不是 CPU/浏览器回归、GPU smoke 或 Nibi 部署资格通过。**

## 1. 科学逻辑与历史重复

- 保留必要的八个主比较，新增调用×部署、标记×页脚、显式两两拓扑机制，不再次搜索通用布局/分辨率。
- 所有正常条件保留同一完整文本；图像消融仅移除登记副本，空槽、编号及公共容量冻结。
- G01 两种画法使用相同公开投影图；只变该组件。G02/G03、node_link 参考画法及日志左右分组未改。
- 标记消融保留刻度和读数标签，未误称完全没有数值视觉信息。TRACE_LENGTH_NEUTRAL 与曲线置换明确是冲突压力测试。
- A/B/C 均在看到新结果前锁定；C 是旧 test360，不是 untouched test。
- RQ3.6 事实删除不能替代本轮图形副本消融；已有 renderer 组件不当作已完成对应 RCA 比较。
- 配对统计按具体 contrast 的必要条件形成交集，不因无关条件超时丢弃整例。

## 2. 实现、运维与恢复

- 修复八-arm旧预算分配：A15360＋B1200＋C2880＝19440；一个共享smoke18；余量542；新轮上限20000。
- 每模型三个互斥case shards；历史调用快照独立保留，旧40000规划限制的取代在DD-20260929-03明示。
- 资格与正式job计数遍历登记的历版本目录，不能通过v6新目录重置旧授权。当前提交状态为static-only。
- 修复repeat被相同请求去重的风险：repeat有独立任务身份/replicate，既不引用旧回答，也不进入普通结果复用表。
- 非repeat无动作条件按完整请求hash引用原回答；渲染缓存保留被请求的干预身份，不把共享PNG误记为不同图。
- 每case加载一次，arm之间共享上下文与PNG；已完成目标先读flag，不重建请求/校验大型文件。
- 正式服务启动前只查未完成病例的小型preparation提交标记，缺输入不先加载模型等待。
- C的前驱cache使用原RQ3.7 digest算法，不误用新稳定JSON哈希导致所有旧缓存“找不到”。
- C来源缺失明确报错；本轮未验证Nibi360例cache齐全，也未验证约3240位置/job能在8小时内完成。

## 3. 泄漏、数值、绘图与语法

- 图形开关只接收public DTO；ground truth、fault_type、dataset分层只在offline分析中加入。
- 曲线置换仅处理已有有限值，保留缺失位置和值的多重集；原始bundle不变。
- 中和Trace条长不更改原数值、单位、文字或其标签位置，不作为正常部署画法。
- `suppressed_visual_bindings`明确记录被去除的图像字段；剩余字段仍受原浏览器可见性核查。
- 改动的renderer开关默认为原行为；未修改既有图路由函数、部署映射或旧RQ renderer。
- 13个Python文件完成AST解析与编译检查，无项目函数执行；标准库symtable扫描未发现未定义全局引用。
- v6 JSON与源码arm常量、预算、分组计数一致；所有RQ3.8 shell入口通过`bash -n`。
- TypeScript `tsc --noEmit`通过；esbuild源码构建通过，未运行构建产物或启动Chromium。
- `git diff --check`通过。RQ3.8五功能模块加init合计1866条非空非注释源码行，低于7500限制。
- 环境没有pyflakes，因此没有声称pyflakes通过；采用上面的实际静态检查与人工调用链审阅。

## 可复现标识

- `configs/ops_components_v6.json` SHA256：`080f29b8c8d39d25084e1134cc1fa2cfe65d4a08cbd6a0bafe484a1295a46874`。
- `src/renderer/web/dist/render.mjs` SHA256：`2be60a8728d087a817dc8371b1cc61a0a826a67babb68bae89edc407fd047cdb`。

## 尚未执行

没有运行pytest、processor容量检查、真实case preparation、浏览器截图、模型推理或Slurm提交。
补充的回归定义覆盖图元抑制、真实标签保留、调用/部署分别删除、pair组件实际切换、
确定性置换、独立repeat、缓存复用、预算与contrast-local配对，但这些测试本轮**未执行**。
未同步v6至Nibi；后续需同步源码和bundle，再按剩余资源授权在Nibi资格检查。
静态分析不能证明视觉可读性、实际吞吐或统计收益；所有这些判断继续等待运行证据。

## 随后追加：直接GPU smoke授权与静态复查

用户在静态检查完成后授权直接提交GPU smoke。DD-20260929-04仅新增一个
30分钟Nibi资格job，不授权CPU回归或正式实验。入口改为smoke-only，单v6提交
加历版本总量双重限制；CPU例外仅用于这次smoke，并明确记录未运行。
GPU作业先准备输入并完成processor容量检查，再启动模型；没有pytest步骤。
源码契约补入实际浏览器bundle的SHA256，避免只核查TS源码却遗漏旧bundle。

上述运维修改再次通过13文件AST/compile、shell语法、配置/条件/预算一致性与
`git diff --check`；没有新增浏览器、CPU回归或GPU调用。
更新后的配置SHA256为
`af748b182cf3165eac4ca6d1cc6b274cab0dcdcaf8fa7233702067cebcd15f56`；
bundle未改变，仍为上面的`2be60a...47cdb`。
当前Nibi旧SSH无响应、新连接要求交互MFA；已请求重新登录。
故此刻**未同步v6、未提交job**；登录恢复后才能填写实际Slurm编号。

重新登录后确认旧版只有portable preparation，缺少新编译入口所需的本地前驱文件。
已为三例准备原有canonical/public数据、冻结上下文及评分记录的复制包；不重跑raw处理。
上下文来源路径只替换明确的旧仓库前缀，仍校验原字节哈希；该改动再次通过AST/compile。
历史账本是本地软链接，部署包须复制实际文件而非软链接。第一次大包终端传输时连接
断开，未解包；改为带ControlMaster的SSH登录后用SCP传输，不据此声称部署/运行成功。

## 部署与提交回执

用户完成v7登录后，SCP包两端SHA256一致；已同步源码、bundle及三个冻结smoke输入。
Nibi静态入口通过（1885条非空非注释行）；元数据初始化成功。
`sbatch`确认job `22941413`，名称`rq38v6-smoke-attempt7`，完整H10080GB，30分钟，
八CPU核心、96GB主机内存，合计≤18次推理。未提交CPU回归或正式实验。
仅确认已提交；按用户要求停止，不监控，不宣称smoke通过。
