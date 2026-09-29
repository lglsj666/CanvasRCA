# RQ3.8：完整文本支撑下，真实运维图表的增量价值

**当前状态（2026-09-29）：** v6 的第七次 GPU smoke 在模型启动前因
processor context 预检超限而失败，零模型调用；下文 v6 记录为历史快照。
文件末尾的 v7 修订保持图像和实验语义不变，只压缩各 arm 共享文本。
v7 GPU smoke 作业 22942268 已完成 18/18 次调用，两个模型与三个注册
smoke arm 均有持久化记录。用户随后明确免除 CPU 回归，授权最多四个
各八小时的 Nibi 正式作业覆盖全部 A/B/C arm。免除不等于 CPU 测试通过；
正式提交前仍需完成 smoke 产物审阅、前驱缓存同步和新分片的静态核验。

## 历史版本 v6：组件作用、图形依赖与锁定回归（2026-09-29）

**历史状态：**实现及静态检查通过，Nibi job `22941413` 已执行；
它在 CPU processor 预检阶段因请求超限失败，未加载模型、未发起推理。
CPU 回归未运行，正式实验未提交。
当前配置为 `RQs/RQ3_8/configs/ops_components_v6.json`。本节优先于下方保留的 v5 历史协议；
历史结果、配置、例图与资格记录不删除、不改判。旧 smoke 不自动证明 v6 可执行。

### 为什么扩展，以及希望形成什么故事

历史 Qwen 结果提示三个不同问题：证据被选择器遗漏、已有证据没被正确利用、不同组件之间相互干扰。
X/SC 的负结果说明不能先破坏有用资源证据，再期待视觉挽救；本轮仍不改选择器。
RQ3.7 LOCAL_LINK 对 TPV 的开发集收益，不足以说明连线本身有效，也未证明真实 Dashboard 有同样收益。
因此不再增加一批布局，而把完整故事的证据链补齐：

1. **端到端价值**：完整文本支撑下，真实图表能否提高 MRR，而非仅重复事实？
2. **组件机制**：收益来自曲线/条形、图内统计文字、调用关系，还是部署关系？哪些组合产生干扰？
3. **适用模式**：图稠密、Trace 缺失、宿主与实例竞争时，网络概览和两两关系图各自怎样修复/破坏排名？
4. **实际图形依赖**：模型是否使用曲线的时间顺序与条形长度，还是主要阅读精确文字？
5. **稳定性与成本**：变化是否超过同输入重复波动；改善需要多少真实图像 tokens、渲染和推理开销？
6. **锁定复核**：预先确定的两个视觉方法，在另外360个已暴露事件上是否保持效果？

这是一条待检验的故事，不预设“图更好”。MRR 仍是第一终点；若只观察到容易受错误图形干扰，
那是可靠性风险，不是视觉贡献。真实图表消融与全量正向比较必须同时支持贡献。
不承诺达到 MRR≥0.65，也不以微弱总体改善掩盖 node 或 AIOPS 的退化。

### 历史去重审计

| 本轮问题 | 最接近的历史实验 | 本轮保留的区别 |
|---|---|---|
| FULL 对 TEXT/TEXT_DUP | RQ1.1 H 与截图 S | 是必要校准，不宣称新的冗余理论或重新证明“截图无用” |
| M/R 图形组成 | RQ1.1 模态搬移、RQ2.1 表示搜索 | 完整 M/R/L 文本不变，组件固定槽位；估计副本作用与交互 |
| 调用图×部署图 | RQ3.6 B3 CALL/DEPLOY | 旧实验改变事实包；现在只删除图形副本，全部关系继续存在于相同文本 |
| 曲线/条形×统计页脚 | RQ1.1 S、RQ3.7 数值面板 | 不重新比较整个截图；同一真实图表内去除特定图元或统计页脚，保留其余几何 |
| 网络概览 vs 两两边 | renderer 已有 edge_pairs 组件 | 没有查到本轮同事实、同容量的正式 paired-network RCA 结果；组件存在不等于已评测 |
| 错误图形依赖 vs 重复波动 | RQ3.2 删证据/重匿名化、RQ3.7 等价单位 | 这里故意损坏图形时间或长度，文字保持真实；不冒称无语义干预 |
| test360 锁定复核 | RQ3.1/3.2、RQ3.7 已访问 test | 是新方法的跨事件回归，不是新的 untouched test 或独立泛化证明 |

来源仍为下方历史报告索引，不使用旧 Gemma MoE 的成绩选择新条件。新 dense Gemma31 单独报告。
本轮不加新选择器、训练、Composer、预诊断调用、分辨率搜索、数字单位改写或实体重匿名化。

### A：`exp_operational_component_utility`，480×16×2＝15,360

保留原八个条件，并增加八个有明确归因用途的条件：

| Arm | 图像中的变化（所有原始文字证据保留） | 目的 |
|---|---|---|
| TEXT | 无图 | 同事实强文本锚点 |
| TEXT_DUP | 无图，重复一次相同组件 ledger | 单纯重复/强调对照，不声称等 token |
| MR00 | G＋日志＋onset；M/R 槽位为空 | 数值图形2×2的起点 |
| MR10 | MR00＋M 折线 | M 的条件贡献 |
| MR01 | MR00＋R 前后条形 | R 的条件贡献 |
| FULL | 全组件 | 预注册主方法 |
| NO_LOG | FULL 去掉日志图形 | 日志副本的作用 |
| NO_ONSET | FULL 去掉 onset 图形 | 相对时间图的作用 |
| NO_CALLS | FULL 只去掉 G01 | 调用网络副本的作用 |
| NO_DEPLOY | FULL 去掉 G02/G03 | 宿主/实例映射副本的作用 |
| NO_G | FULL 去掉 G01/G02/G03 | 与前三项组成调用×部署2×2 |
| FULL_PAIRS | FULL 的 G01 改用 `graph.edge_pairs` | 两两关系是否比网络概览更易利用 |
| MR00_PAIRS | MR00 的 G01 改为两两关系 | 拓扑画法的作用是否依赖数值图表 |
| MR_NO_MARKS | 只去掉 M 曲线/点、R 条形色块 | 图形标记相对图内文字的增量 |
| MR_NO_DETAILS | 只去掉 M/R 的统计页脚 | 图内统计副本的增量 |
| MR_NO_MARKS_DETAILS | 同时去掉上述标记和页脚 | 与 FULL、前两项组成标记×页脚2×2 |

**重要语义边界**：NO_MARKS 仍保留实体、标题、单位、坐标轴刻度、Trace 的前后数值标签及其位置；
NO_DETAILS 不删除 Trace 图内前后读数。故2×2估计“指定图元”和“统计页脚”的作用，
不能把无色块条件称为完全没有数值视觉线索，也不能把两者都移除称为空白图像或等 token 控制。
所有被抑制的图像绑定在 manifest 明确列出，不伪装为仍然可见；它们的原始值仍在共同文本中。

调用图维持用户确认的单一参考画法；两两边是显式选择另一个组件，不在 node_link 内暗中切换。
G02/G03 的绘图代码、log 左右分组及 evidence→pod 映射不变。两种 G01 同一 case 使用相同边集合。
若两两边需要更大面积，仅将**所有视觉条件共同的 G01 槽位**扩至两种画法所需高度的较大者，
相同总高度、宽度、字体、编号、其他卡片尺寸；删除后的槽位留空。上限仍8192px，不截边、不缩字。
因此 v6 FULL 不能假定与旧 v5 每张 PNG 相同；本轮所有比较使用共同容量的新版本，不复用旧模型结果。

### B：`exp_graphical_reliance`，100×6×2＝1,200 新调用

按 `hash([42,"rq38_mechanisms",opaque_id])` 从五个 eval 数据集各取20个，不看标签/结果。
复用 A 的原始回答；新增六个条件：

| 条件 | 动作 |
|---|---|
| METRIC_TIME_PERMUTED | 同一卡片内对有限数值做固定置换；保留 bins、缺失位置、值的多重集、所有原始文字与统计 |
| TRACE_LENGTH_NEUTRAL | Trace 色块全部用相同长度；原数值、标签位置、统计和文字不变 |
| FULL_REPEAT | FULL 原请求独立再调用一次 |
| TEXT_REPEAT | TEXT 原请求独立再调用一次 |
| FULL_PAIRS_REPEAT | FULL_PAIRS 原请求独立再调用一次 |
| MR_NO_MARKS_REPEAT | MR_NO_MARKS 原请求独立再调用一次 |

前两项是**图文冲突/图形破坏压力测试**，不是合法部署方法、同事实图像条件或等价变换。
曲线置换会破坏时间事实；中和条长可与真实数值冲突。它们回答模型有没有受图形影响，
不能单独证明图形被正确理解或具有因果诊断能力；正文和公开 reason 仍只允许做可观察引用审计。
若缺少相应图元导致最终请求完全相同，直接引用原回答并记录 no-op，不浪费调用；repeat 永远不走此去重。
repeat 采用相同采样配方但独立身份，不能读取原回答作为结果，也不取最优答案。
相同固定 seed 下的重复只测实际执行波动，不代表独立随机种子下的完整采样分布。
一次额外重复只能提供有限的执行波动估计，不是完整方差分解。

主要看每种干预相对 FULL 的 MRR/排名/首位翻转，以及相对 FULL_REPEAT 的差异。
同时报告图元实际变化、无效干预计数和四种原请求的重复波动；不能只凭“图打乱后退化”宣称视觉贡献。

### C：`exp_locked_operations_regression`，360×4×2＝2,880

预先固定 TEXT、FULL、FULL_PAIRS、MR00；三主数据集各120个旧 test，**明确已暴露**。
不根据 A/B 成绩挑选 C 的方法、预算、候选、画法或 prompt；不按 case 选择 arm。
三个区块可装入同一批六个 job，因为 C 的方法在任何新结果前锁定，不需要等待 A 后人工挑冠军。
若方法因修复科学输入而改变，整体用新版本处理，不利用已读 C 的表现调整同一锁定版本。

公共锚点优先复用已导出的事实；C 读取既有 RQ3.7 registration 对应的 public_cache/view、
已提交的 RQ3.4/3.7 public contexts 和 evaluator-private 记录，原始大表不重做。
缺少这些来源时在 preparation 明确阻塞，需复制现有前驱 artifacts；不默默重新选择证据。
本轮仅写导入链路，**尚未核验 Nibi 的360例前驱缓存是否齐全**。此项必须在正式提交前解决。

未使用事件的独立验证仍是论文证据链缺口，但本轮不假定存在90个干净事件，更不把旧 test 改名。
待固定方法显示价值后另做完整使用史审计并取得后续预算；没有独立验证就明确限制泛化结论。

### 统计、模式与判定

- MRR 为 primary；AC@1/3/5、AVG@3/5、repair/break、前五新增、前五→第一、候选非法/格式失败、成本均保留。
- A primary family：FULL−TEXT、FULL−TEXT_DUP、FULL−MR00、FULL_PAIRS−FULL、FULL−MR_NO_MARKS，两个模型共10项 Holm。
- M×R、调用×部署、标记×页脚分别各6项 secondary family（两个主效应及交互×两模型）。
  FULL−NO_LOG/NO_ONSET/NO_CALLS/NO_DEPLOY/MR_NO_DETAILS 为另一10项 family；两两画法与M/R交互另4项。
- B 四个压力比较×两模型为8项 family；四个 repeat−原始×两模型另8项；C 三个固定比较×两模型为6项。
- 每个数据集、AIOPS 合并、三主数据集 macro、五集 macro/pooled 分开；主推断只针对三主数据集。
  点估计同时给 macro 与 pooled；Pratt 检验以配对 case 差值计算，不假称按数据集独立重复。
- 每项对比仅保留该对比所需条件都可用的配对 case；无关 arm 超时不删掉其他对比。
  超时记基础设施缺失，给最坏/最好边界；模型输出失败按既有 scorer 保留。
  设计容量不足单列可执行率并给端到端零分，实现错误不得伪装成容量失败。
- 配对 Pratt-Wilcoxon、paired dz、事件组平均差值的敏感性分析；不报告 CI。
- 预声明模式：根因 node/pod/service、fault_type、Trace/调用/部署可观测性、每个连接节点≤2或>2条调用边。
  同时给数据集内分层，避免把图复杂度当成数据集身份的替身。缺少私有故障类别时明确未知，不推断标签。
  分层检验统一放在每区块的探索性 Holm family，不把偶然显著的小组升级为主结论。
- 完整保存公共 reason、预测列表、输入/PNG/输出引用；在修复、破坏、不变中确定性抽例检查实际引用。
  reason 的文字不能直接当作隐含推理轨迹或证明模型读到了某个图元。
- 文本/图像输入、输出 tokens、实际新调用数、重复引用数、渲染/推理时长分开；引用回答不重复计入实际成本。

**事先的贡献判据**：主要方法应提高三主数据集 MRR，同时以同事实文本为强对照。
沿用 ΔMRR≥0.05 且对应 Holm-adjusted p<0.05 作为“实质性准确率提升”的表述门槛；
未达到时仍报告真实效应与分层，不把探索性小组显著性当作总体成功。
可解释的组件效应和跨模型复核补强主张，但不能弥补准确率明显退化。
只有与真实原图比较、受控图元消融和重复波动共同支持，才主张相应视觉编码有增量价值。
若 FULL_PAIRS 优于 FULL，解释为显式边编码的条件性效果；不能再宣称当前网络图普适最佳。
若新方法均无稳定改善，保留负结果并停止扩大该表示分支，不恢复无限布局搜索。

### 调用、资源和恢复

| 区块 | 最大新增逻辑位置 |
|---|---:|
| A：480×16×2 | 15,360 |
| B：100×6×2（原始回答由A提供） | 1,200 |
| C：360×4×2 | 2,880 |
| 一次共享资格 smoke，累计≤18 | 18 |
| **计划合计** | **19,458** |
| 中断等必要恢复余量，不自动花完 | 542 |
| **本轮新增硬上限** | **20,000** |

这是用户本次扩展授权对当前 RQ3.8 的预算修订，取代旧“研究线累计40000”对本轮扩展的限制；
不是清零既往花费。旧28216仅是特定父账本的历史快照，不冒称整个项目的全部花费。
新旧账本均保留并分列；跨六个正式 shard 的配额总和＋18严格≤20000。
新版不会利用新目录重置历史 CPU/GPU **job 数**授权。用户随后明确允许静态通过后直接提交GPU smoke：
当前入口仅开放一个新的30分钟GPU资格job（总授权从六次增至七次），不开放CPU回归或正式提交。
作业内完成必要的输入准备和真实processor容量检查，不执行pytest；CPU回归明确记录为未运行。
此例外只用于本次smoke，不冒称全量资格通过；详见DD-20260929-04。

仍最多六个正式 Nibi job（每模型三个互斥 case shards），每个≤8h、完整80GB H100、8个独占物理CPU核心。
每个 job 约3240个正式位置，模型同 case 的条件不跨 shard；36请求并发、有界队列。
相较原1280位置/job，所需吞吐明显提高。未来 smoke 必须记录实际吞吐，并估算剩余8小时能否容纳；
本轮没有测速，不保证六个8小时能跑完。若不足，先报告排期/资源冲突，不偷偷加第七个job或删case。
smoke仍只是一轮共享≤18次，不按三个科学区块拆出54次规避调用限制。

新版 CPU 定义覆盖22个条件的准备/事实/几何/两模型processor（3×22＝66条容量检查），
逻辑 smoke 只覆盖 FULL_PAIRS、MR_NO_MARKS、METRIC_TIME_PERMUTED 的三个开发case×两模型。
这18次不能冒称每条路径都已现场验证；重复调用的独立身份、Trace中和及其他组合先由CPU定义覆盖，
若将来 GPU 审查发现必须补验，先说明覆盖缺口并请求可用job/call授权，不能自行额外提交。

新渲染/事实只准备一次，同一case各arm共享；重复PNG和无动作输入按实际完整请求复用。
重复性实验显式禁止这种复用。done/fail只在持久化完成后提交；续跑只读小flag，
不重建已完成请求、不重复哈希大型PNG。300秒请求超时记录fail并继续，其他基础设施失败停止。

### 本次交付与后续资格步骤

1. 写入本协议、v6配置、条件编译器、统一renderer受控开关、分 cohort 队列、预算与分析入口。
2. 三轮静态检查：科学逻辑/历史去重；运维/恢复/资源；泄漏/数值/语法与 TypeScript 类型。
3. 补全回归定义但本次不执行。TypeScript 编译 bundle 属静态构建，不打开浏览器、不生成例图。
4. **按随后追加授权**：静态通过后同步源码及bundle至Nibi，只提交一个30分钟GPU smoke，然后停止。
   不新增CPU回归，不启动正式实验；远端登录有效且提交收到Slurm job ID才称为已提交。

本次检查记录：`RQs/RQ3_8/descriptions/RQ3_8_v6_Static_Review_2026-09-29.md`。

---

## 历史 v5 协议（保留记录，预算与活跃条件已被上文 v6 取代）

版本：2026-09-29，`ops_components_v5`。状态：新版 150 张 CPU 例图已生成；
尚未在 Nibi 完成新版 CPU/GPU 资格检查，也未启动新版正式实验。

v5 只改变 G01 顶部调用概览的图像表达：沿用参考图原有的环形坐标和直接连线，
取消按节点数切换至网格折线路由；可信的公开 service→pod 对应可将 pod 调用
汇总到 service 层，不能可靠映射的 pod 则原样留在 G01，不猜测、不丢边。
所有原始有向调用边仍在各 arm 共有的文本 ledger；G02 node→pod 和 G03
service→pod 两个组件及绘图代码保持不变。此改动进入正式 `render_one()` →
`fixed_slot_design()` → `renderer.main.render()` 路径，不是仅在例图脚本中生效。

v4 补充 G03 的公开 service→pod 身份关系：从 `node_pod_map` 已登记的 pod
出发，沿用 RQ1.1/RQ3.1 已有的 pod 名称投影，仅在投影后的 service 和 pod
都具有正确类型的匿名 ID、且无冲突或 namespace 歧义时建立对应。它不是
trace 同行观测，也不是 Kubernetes ownerReference 或故障传播边。明确的
metadata/trace 绑定优先，三种来源在离线审计分别记录。AIOPS-2022 的
smoke 案例有 42 个公开托管 pod，但旧 G03 因缺少同行 `k8s.pod.name`
而为空；此修正同时改变公共文本 ledger 与图像，因此独立注册 v4，
不复用 v2/v3 的运行资格或模型结果。

## 1. 本轮决定与历史依据

本轮以统一 renderer（Git `19c40f52e`）为来源：宽幅调用拓扑、
node→{pods}、service→{pods}、onset 时间图、下方三列 Metrics/Trace 及日志组件。
不恢复用户已放弃的窄长拓扑、额外孤立锚点或跨组件长连接线。
`Observed call relationships` 本身就是观测到的调用拓扑，不再另画一份同义图。

历史 v3 曾改成所有节点规模均使用有界网格及折线路由；用户复核真实例图后
否定了这种效果，v5 恢复参考图的视觉语法并将其用于所有节点规模。

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
第4次job22930381已ready但客户端仍用8000、服务用30381，token预检失败，未发起生成。
用户随后批准修复并增加且仅增加第5个GPU job：仍30分钟、同一18-call累计额度。
本次在该GPU allocation内先跑禁用CUDA的CPU回归及processor检查，合格才加载模型；
不增加第9个CPU job。同步endpoint、记录异常终态；不改变科学输入/模型配方/画图。
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

1. 冻结本计划、输入/输出契约及 C09 单一网格＋折线视觉语法。
2. 三轮静态检查：科学动作与历史重叠；调用链/恢复/预算/速度；泄漏/单位/可见字段。
3. CPU 回归：原完整预览像素回归；固定槽位消融的未变区域像素一致；无隐形字段；
   明确证据归属、孤立图节点不注入、折线路由、长标题/密图/空数据和双模型 context。
4. Nibi 一个有边界 smoke：三个主数据集各一个固定开发 case，TEXT/FULL/MR00，
   两模型共18次内。检查实际PNG、完整输入/输出、conversation、终态标记、实际吞吐。
   未完成的路径如实报告incomplete，不冒称其已live验证；原timeout-only历史记录不改写。
5. 资格通过后最多六个8小时正式 job；后台保存日志和可恢复结果。
6. 正式提交确认后才删除本地旧 Gemma26，原模型目录下启动 Gemma31 下载。
   不删除 Qwen9B、Qwen3.8 或其他项目缓存；下载开始后本次工作可停止。

本轮不保证 MRR 提升，也不把能渲染等同于模型能读懂。希望区分：有准确文本支撑时，
真实图表是否成为有用的第二种读取方式，还是给诊断增加竞争与干扰。
# 2026-09-29 v7 amendment: capacity without changing the visual estimand

The `ops_components_v7` request compiler keeps all registered visual arms,
images, selected facts, model recipes, and fixed base text across arms. It
removes only component-ledger observations proven to be exact duplicates of
the existing public M/R/L/onset anchor and serializes directed G edges in a
reversible compact table. The intentional `TEXT_DUP` control remains. This
preserves the question “does the dashboard add value over the same text?” and
does **not** switch to disjoint text/image evidence. The failed v6
processor-only smoke is not an efficacy result. On the three prepared smoke
cases, v7's real dual-processor, all-arm check passed (66 case×arm rows; zero
over-limit). The subsequent v7 GPU smoke finished 18/18 live calls; it is
qualification, not efficacy evidence. The four-job formal authorization and
CPU waiver are recorded in RQ3_8_experiments.md DD-20260929-07.
