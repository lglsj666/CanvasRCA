# RQ3.8：完整文本支撑下，真实运维图表的增量价值

版本：2026-09-29，`ops_components_v2`。状态：实现与资格检查中，尚未获正式执行资格。

## 1. 本轮决定与历史依据

本轮继承用户认可的统一 renderer（Git `19c40f52e`）：宽幅调用拓扑、
node→{pods}、service→{pods}、onset 时间图、下方三列 Metrics/Trace 及日志组件。
不恢复用户已放弃的窄长拓扑、额外孤立锚点、跨组件长连接线或替代布局算法。
`Observed call relationships` 本身就是观测到的调用拓扑，不再另画一份同义图。

只用历史 Qwen 结果决定研究方向；旧 Gemma MoE 不用于筛选方案，新 dense Gemma
作为独立跨模型检验。完整报告索引位于 `docs/experiment_reports/`。

| 历史证据 | 本轮推论与边界 |
|---|---|
| RQ1.1：主数据集 TPV 优于 T/V/S；Metrics、Trace 从文本转图常退化 | 精确 M/R/L 文本保留，研究图形副本，而非再次强制替换文本 |
| RQ2.1：大量新选择/画法未稳定超过 P0 | 不增加选择器，不搜索字体、分辨率或布局冠军 |
| Tournament：Metrics 文本化有明显修复，后期选择器增量收敛 | 保留原读数并分离图表读取与证据缺失；联合覆盖不当单方法准确率 |
| RQ3.1/3.2：X、SC 丢失有效资源证据；视觉不能挽救较差选择 | 冻结既有 ALL_ID 公共文本，图形只冗余投影已提供事实 |
| RQ3.3/3.4：见证追加在部分案例有修复，也把 pod 判断拉向 host | 本轮不再追加新的异常候选或宿主遥测 |
| RQ3.5/3.6 A：公共任务措辞、支持证据有条件收益 | 沿用现有公开任务和输出格式，不混入新的诊断指令 |
| RQ3.6 B1：Qwen 去掉 onset 后文本改善、图像退化，交互未通过校正 | 保留 onset 文本，单独检验 onset 图形副本，而非重跑删除时间事实 |
| RQ3.6 B3：ALL_ID 图出现正向线索，额外 BIND 非必要 | 保留明确实体和完整观测关系，不再测试长归属线 |
| RQ3.7 A：Qwen LOCAL_LINK 对 TPV 配对 ΔMRR=+0.0771，Holm p=0.0171；对 REMOTE_ID/强文本未通过校正 | 不能把收益归因于连线；检验其线索能否迁移到真实折线/条形图，而非文字面板 |

详细来源：RQ1_1_RQ2_1_findings/findings.md、Tournament_Analysis_2026-09-15.md、
RQ3_1/2/3/4/5 的 Results/Screen_Analysis、RQ3_6_Stage_A_Analysis、
RQ3_6_Mechanisms_Analysis、Cross_Experiment_Method_Profile、RQ3_7_Results_Analysis。
以上均为已暴露的探索/开发证据，不是新数据集泛化证明。

### 历史去重

RQ1.1 的 H 已测试整体冗余图文，故 **FULL 对 TEXT 不是首次证明冗余有用**。
本轮新增的是：在同一份完整文本支撑下、正常运维组件上，以固定位置的 2×2
检验 Metrics 与 Trace 图形副本的条件作用及交互；日志/onset 只移除图形副本。
它不同于 RQ1.1 的模态搬移、RQ3.6 的事实删除、RQ3.7 的数值面板邻近/连线。
全量已观测拓扑来自用户已批准的 renderer 入口；其补充关系同时进入所有 arm 的
文本，避免只有图像获得新边。不会声称“首次使用实体绑定或拓扑”。

## 2. 唯一科学实验与八个条件

实验名：`exp_operational_component_utility`。同一 RQ480、两个冻结模型、一次调用。
保留 ALL_ID 文本、候选顺序、统计窗口、数值和任务。补充 renderer 的完整观测关系
及精确组件读数为统一公共文本，所有条件一致。图像不是私有标签或新排序的来源。

| Arm | 图形内容 | 目的 |
|---|---|---|
| TEXT | 无图 | 完整同事实文本锚点 |
| TEXT_DUP | 无图，再次呈现相同组件读数/关系的结构化文本 | 区分图形与单纯重复/强调；不冒称等 token |
| MR00 | G、日志、onset，M/R 槽位留空 | 2×2 起点 |
| MR10 | MR00＋Metrics 折线 | M 的条件作用 |
| MR01 | MR00＋Trace 前后条形图 | R 的条件作用 |
| FULL | MR00＋M＋R | 预注册主方法，完整正常 Dashboard |
| NO_LOG | FULL 只去掉日志图形副本 | 日志图形是否帮助或干扰 |
| NO_ONSET | FULL 只去掉 onset 图形副本 | 时间组织的增量价值 |

文字证据不随消融删除。纯文本不接收图像阅读说明；所有视觉条件共用一份静态
说明，不暴露 arm 名、实验目的、私有标签或“冠军”身份。候选始终在文本中。
所有视觉条件复用 FULL 的几何、宽高、组件编号和字体；删除图形的槽位保留为空，
其余组件不挪动/放大。空槽是受控消融，不是部署推荐布局。
FULL 的调用拓扑仍占完整宽度；不引入面板→拓扑的归属线。

完整公共文本使用已有全部 M/R/L，及 renderer 精确投影的 ledger。
Ledger 只使用可见卡片字段；图中未显示的源字段不被宣称已画出。
Nibi CPU 资格检查发现逐卡 JSON 的重复字段/时间数组使输入超限。
在任何模型调用前，ledger 改用可逆的列名＋行、规则序列和重复值位置范围表示；
逐项反解核对数值及关系，不舍弃观测、不舍入、不修改 PNG。
原 ALL_ID 的诊断措辞、字段和值保留；只去除完整 JSON 行的非字符串空格，
将十二次重复的 `bins=[0,1,...,63]` 写为精确的 `bins=0..63 (inclusive)`。
组件 ledger 不复制从未显示的内部 edge ID，但保留全部有向、带类型关系。
所有 arms 共用相同序列化，TEXT_DUP 重复同一紧凑 ledger；不增大模型长度或缩图。
图形与文本的语义重复不计作新增观测。没有有效数据的组件保留既有空图行为，
不填零、不制造边或状态，不展示调试/missing-bin 标记。

## 3. 预注册分析

Primary：FULL−TEXT、FULL−TEXT_DUP、FULL−MR00；两个模型共六项 Holm family。
同一差值报告 MRR、AC@1/3/5、AVG@3/5、repair/break、Pratt-Wilcoxon、paired dz。
不报告 CI。M 主效应、R 主效应及 M×R 交互为第二个六项 family：

```
M = ((MR10−MR00) + (FULL−MR01))/2
R = ((MR01−MR00) + (FULL−MR10))/2
M×R = FULL−MR10−MR01+MR00
```

FULL−NO_LOG、FULL−NO_ONSET，两模型共四项 secondary family。
每个 family 按实验×模型共同完整病例比较；超时是基础设施缺失，不记模型零分，
并报告配对可用与缺失最坏/最好边界敏感性。格式失败/非法候选为原评分契约终态。
全部五个数据集分别报告；三主数据集 macro 为主，另报 AIOPS 合并、五集 macro、
480 pooled。RE2 不掩盖主数据集退化，重复引用不扩大样本数。

预先定义的模式：根因 node/pod/service；资源/状态/流量/网络故障；曲线稀疏与
短脉冲/持续变化；实际 Trace/日志/onset 覆盖；完整调用图密度及部署关系覆盖。
公开特征在结果前计算；标签只由 evaluator 离线加入。报告每层计数、修复与破坏，
小样本标为探索性，不依据根因类型选择部署 arm。不用 reason 代替隐藏推理。
随机抽修复/破坏/不变案例核验数字、实体、边、时间引用；不只挑漂亮成功图。

单次成本拆为文本输入、图像输入、输出、CPU渲染与推理时间；不同设备的 latency
不与旧本地结果混作方法加速。历史 TPV/RQ3.7 仅为有明确条件差异的背景结果；
新的主要配对比较全部在本轮、同一模型配方中完成。

## 4. 数据与画布

使用原 eval480：100/100/100 个 AIOPS-2022/AIOPS-2025/AegisLab，加90/90个RE2。
不启用 test360、unused、训练或 Composer。沿用已有 case-local 数字匿名化。
每 case 一次加载现成公共 context；缺缓存才处理对应 per-case，不读取原始大表。
完整关系只来自公开 graph/Trace 身份列/部署字段，不能从筛选后的 Trace 反推全图。

优先复用已完成 public-only 导出；旧 DTO 是事实缓存，不是恢复被放弃的 renderer。
新版完整组件 DTO 单独落盘。编译器不读 private 标签，标签在输入生成之后独立评分。
基本画布采用 renderer `relations_first`：宽1800、字体16、间距18、边距28；
高度随 case 完整组件确定，最高8192。四 MR 条件和两个消融同 case 同画布。
不能通过删事实或改变某个 arm 的字体使请求装入 context。真正超出注册容量
记为设计不可执行，并同时给端到端零分和可执行率；实现错误先修复，不冒充该状态。

## 5. 模型、Nibi 部署与预算

用户新授权覆盖历史 local-only 限制；本轮 Nibi 使用 Qwen3.8-27B 和 Gemma-4-31B-it，
不会修改历史 Gemma26 的身份或结果，不碰其他项目 Qwen9B。
Qwen revision：`1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0`；
Gemma31 revision：`842da3794eaa0b77d5f08bae87a17459d91ff475`。
两模型 BF16、无量化、冻结采样、context40960、实际输出8192、无 attention。
新模型通过单独版本化 profile 接入统一 client，不伪装成旧 Gemma26。

Gemma 采用 `max_soft_tokens=1120`：官方支持的高细节档位，推荐小字/OCR任务使用
较高预算；这不是官方证明对所有 dashboard 全局最优。源图尺寸与实际 processor
geometry/token 均记录，不能保证长图里的每个小字仍可辨。
[官方模型卡，Variable Image Resolution](https://huggingface.co/google/gemma-4-31B-it#5-variable-image-resolution)。
Qwen 保持本地同版本的原生 image processor，不增加 pixel override。

正式最多 **8×480×2=7680** 调用；一个逻辑 smoke 累计≤18 calls（两模型顺序）。
2026-09-29 最新用户修订：前三次600秒窗口均未开始推理，保留记录；允许第4次
GPU补验，取消脚本内部总时限及提前6分钟结束的smoke信号，只由Slurm限制30分钟。
通过即停止补验；多job不能重置18次逻辑smoke调用计数或冒充多个独立实验。
新运行在独立profile中显式指定Qwen GDN为Triton，避免H100下auto选择FlashInfer
触发大规模SM90编译；其余模型/采样/证据不变，旧profile保留。详细诊断和资格条件
见RQ3_8_experiments.md的最新修订。零次推理或未完成检查不再显示为新的smoke通过。
CPU回归最多8个job，每个最多1小时；按需提交，不把8个job当成必须消耗的额度。
2026-09-29 只读 SQLite 核对本研究线已发起 **28216** 次；计划合计最多 **35914**，
累计40000上限余4086，仅供已授权必要修复/重试，不自动增加 arms。
正式提交前重新读真实累计数；每个 shard 独立调用计数及固定配额，避免跨节点共享
SQLite 写锁，也防止六个 job 各自把40000当新增额度。

最多六个正式 job：每模型三个互斥 case shards，约160例×8条件=1280位置/job。
各 job 申请一个完整80GB H100（非40GB MIG）、≤8小时、8个物理CPU核心。
同 case 所有条件留在同 shard；数据集内稳定 hash 交错分片，不根据成绩分配。
资格检查先测吞吐和内存；若8小时无法覆盖预算，在首次正式提交前缩减设计规模并
重新登记，不把未完成称为完成，也不偷偷提交第七个正式 job。

CPU 与浏览器 preparation 先完成，GPU作业只消费已准备输入；36请求并发，有限预取。
请求 timeout300秒记录终态fail并继续；非timeout基础设施错误停止并保留产物。
done/fail在输入、PNG、回答、conversation、评分与成本持久化后提交。
续跑只读小标记，跳过完整单元，不重建全部请求/重哈希全部图片。
显式记录服务 ready 与 first request，避免只加载权重却无推理的假启动。

## 6. 执行顺序与验收

1. 冻结本计划、输入/输出契约及源代码；不恢复废弃布局。
2. 三轮静态检查：科学动作与历史重叠；调用链/恢复/预算/速度；泄漏/单位/可见字段。
3. CPU 回归：原完整预览像素回归；固定槽位消融的未变区域像素一致；无隐形字段；
   明确证据归属、孤立图节点不注入、曲线连接、长标题/密图/空数据和双模型 context。
4. Nibi 一个有边界 smoke：三个主数据集各一个固定开发 case，TEXT/FULL/MR00，
   两模型共18次内。检查实际PNG、完整输入/输出、conversation、终态标记、实际吞吐。
   未完成的路径如实报告incomplete，不冒称其已live验证；原timeout-only历史记录不改写。
5. 资格通过后最多六个8小时正式 job；后台保存日志和可恢复结果。
6. 正式提交确认后才删除本地旧 Gemma26，原模型目录下启动 Gemma31 下载。
   不删除 Qwen9B、Qwen3.8 或其他项目缓存；下载开始后本次工作可停止。

本轮不保证 MRR 提升，也不把能渲染等同于模型能读懂。希望区分：有准确文本支撑时，
真实图表是否成为有用的第二种读取方式，还是给诊断增加竞争与干扰。
