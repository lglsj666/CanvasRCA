# RQ3.7：数值证据与实体关系的受控视觉融合

最新状态（2026-09-28）：CPU回归、A/B GPU smoke、A/B正式实验及用户批准的120次TPV补跑已经完成；统计与案例报告见[分析报告](../experiment_reports/RQ3_7_Results_Analysis_2026-09-28.md)。用户随后明确授权阶段C：扩展路径CPU检查通过，C专属smoke通过（18/18、260.86秒），输入输出及PNG审阅通过。后台正式队列已启动，先补齐缺失上下文，再自动运行Qwen→Gemma。本次激活eval480及已暴露test360，fresh仍缺完整封存审计，不混入本次队列。历史结果不修改。下文保留原始登记与精简过程；关于120个特定TPV目标的补跑例外，以本地协议DD-RQ37-2为准；当前C授权与终态复用以DD-RQ37-3为准，其余历史缺失仍不自动重跑。

2026-09-28 精简修订：删除 A 的 `B3_T_REF` 实验条件；`TPV_REF`、`B3_G_REF` 在开发180上仅引用兼容历史结果，禁止缺失/不兼容时补跑。保留五个真正的新条件。原实现尚未注册或执行，本次不作任何历史结果清理。修订身份为 `rq37_numeric_relation_fusion_v2_pruned`；原 `fusion_v1.json` 文件名保留为唯一入口，内容已更新。

## 1. 问题与定位

固定已经选中的诊断证据，将数值变化直接关联到所属实体和系统关系，能否提高根因排名、减少故障源与受影响组件的混淆？仅改变等值数字写法或正确计量单位，诊断是否改变，图形能否降低这种敏感性？

冻结 Solver、一次调用、最多一张真实 Dashboard。无 Composer、训练、预诊断、额外选择器或多轮反馈。原 M/R/L 文本完整保留；新小图仅冗余编码其中已有数值。本轮研究证据利用，不声称解决证据缺失。

MRR 为首要终点，不以好看、token 更少或 coverage 代替正确诊断。预注册主方法为 LOCAL_LINK，不按 case 或模型挑最好图形。

## 2. 历史去重审计

| 方向 | 原有证据 | 本轮取舍 |
|---|---|---|
| 选择器、实体覆盖、配对 | Tournament、RQ3.1 X、RQ3.2 SC 及消融 | 不再扩展选择器 |
| 数值注释、均值/差值/比值、持续性 | SEARCH；RQ3.3 SEM/EXEC；RQ3.4 相对尺度下限、MAD、持续比例 | 不称新校准算法 |
| 删除 z/severity/onset | SEARCH24/31、RQ3.6 B1 | 不重复通用删除 |
| host/peer/关系/去重 | SEARCH13、RQ3.4 P×H×K、RQ3.6 B2 | 不泛泛追加上下文；不假设有跨宿主 peer |
| 实体分组、类型 | Tournament R16、SEARCH、RQ3.6 B3 | 实体分组本身不是创新 |
| 文本/截图/图形、布局/分辨率 | RQ1.1、RQ2.1、RQ3.1/3.2 | 不再搜索一般画法 |
| 图文冗余呈现 | RQ1.1 H；RQ3.1 重复负载 | 不重跑通用“加图是否更好”。H−T 的 Qwen/Gemma ΔMRR 为−.0129/−.0683；Gemma补充family Holm=.0229。不能预设重复编码获益 |
| 数值面板邻近 × 观测归属连接 | 有相关先例，没有找到固定内容/规格下完成的独立析因 | 保留主实验 |
| 等值数字写法/单位换算 | 找到单位修正及解析支持，未找到完成的受控 RCA 稳健性实验 | 保留机制实验 |

审计索引：

- [RQ1.1/RQ2.1](../experiment_reports/RQ1_1_RQ2_1_findings/findings.md)。
- [Tournament](../experiment_reports/Tournament_Analysis_2026-09-15.md)：R16 已是实体绑定卡片，不能宣称本轮首次绑定实体。
- [RQ3.1](../experiment_reports/RQ3_1_Results_Analysis_2026-09-19.md)、[RQ3.2](../experiment_reports/RQ3_2_Results_Analysis_2026-09-22.md)：X/SC 不能被当作可靠冠军。
- [RQ3.3](../experiment_reports/RQ3_3_Results_Analysis_2026-09-24.md)：binding/organization 等后续条件注册但未运行；未运行不是已被否定。
- [RQ3.4](../experiment_reports/RQ3_4_Results_Analysis_2026-09-25.md)、[RQ3.5](../experiment_reports/RQ3_5_Screen_Analysis_2026-09-26.md)。
- [RQ3.6 A](../experiment_reports/RQ3_6_Stage_A_Analysis_2026-09-26.md)、[RQ3.6 机制](../experiment_reports/RQ3_6_Mechanisms_Analysis_2026-09-28.md)：ALL_ID_G 是复核线索，不是已证实冠军。Gemma 图文差异的校正显著性取决于 family；Qwen 正向差异未显著。原纵轴调整并不稳定提高 MRR。
- 代码依据：`RQs/RQ3_6/src/exps.py` 的 `qualify_witnesses`、`scope_records`、`prepare_mechanisms`；RQ3.3 `binding` 登记；RQ3.4 综合规则。实现调用原组件，不用重新发明的近似规则冒充 B3。

新的可辨识增量是“真实数值小图的空间邻近”与“一条明确的观测归属连接”交叉，并与同组织强文本比较；不是再次比较任意文本与任意图。

## 3. 文献及推论边界

[Number Cookbook，ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/0b8ccc9229328bdcedf54b989e7cc330-Abstract-Conference.html)支持数值表达需独立检验，不证明我们应训练数值模型。[VGCure，ACL 2025](https://aclanthology.org/2025.acl-long.1482/)支持检查视觉结构理解，不证明加图必然有效。使用已核实的论文/会议记录，不新增未核实的文献结论。不估计高维互信息、不把 token 当 bit。

## 4. 冻结内容与表示

### 4.1 科学锚点

使用 B3 ALL_ID 的原 P0 M/R/L、公开窗口、数值、资格化追加观测、调用/部署关系、候选顺序、匿名映射、任务及输出协议。沿用已修正的来源单位说明，不改变 σ/onset。候选在文本，不在图中重新筛选。TPV 单独保留强端到端基线。

180 例优先读取 RQ3.4 已保存公共 context；新 ALL_ID 文本必须与兼容的历史 B3_T 保存输入一致，否则停止诊断，而非偷偷校准。B3_T只保留为公共输入锚点，不是需要模型输出的实验条件。历史基线直接加载保存的 prompt/PNG，仅当完整输入、模型有效配置、schema 和 scorer 相符时引用旧回答。A中的历史比较缺失、不兼容或缺少必要产物时登记 `reference_unavailable`，不发新请求、不记模型零分、不自动重试；C遇到同一开发病例同样禁止绕过此规则。

### 4.2 数值小图

从已选十二条 M 的 `sircl_met_z.regular_mean/current_mean` 取值；缺少合法前后统计不拼造比较，原文本不丢。每实体全部合格指标构成一个面板。连续量使用同指标共享线性轴、包含零的成对条形图；负值正确跨零。不同指标不共轴、不暗示条长可跨指标比较。

counter/state/未知语义只显示准确标注的前后均值读数，不把累计 CPU 时间画成利用率，不把状态均值称为瞬时状态。已验证语义来自严格原字段注册表；不从指标名模糊猜单位。数值、单位、实体均显示，名称换行不截断。没有根因着色、风险分数、missing-bin 说明。未来资格报告需列出有效数值面板、实际条形图/读数的覆盖；不把“没有可用条形图”误称为成功的图形干预。

### 4.3 析因图形

| 条件 | 面板位置 | 额外观测归属线 |
|---|---|---|
| REMOTE_ID | 独立证据区 | 无 |
| REMOTE_LINK | 同上 | 有 |
| LOCAL_ID | 所属实体旁 | 无 |
| LOCAL_LINK | 同上 | 有 |

节点与系统关系路径、节点大小/颜色/字体、面板内部内容和尺寸、画布和完整 G ledger 固定；只动面板位置或开关虚线。每实体面板一条灰色虚线，含义 measurement-of，不是调用、部署、故障传播或新因果边。共同节点清单包括观测所有者和孤立实体。无标签加权。

宽2304、字20、行26、边32，高度为同 case 所有视觉/数字变体共同需求，范围3072–8192。为 LOCAL/REMOTE 保留空槽；为不同数值字符串预留共同行槽，使单位变换不移动条形几何。完整 G ledger 可见。真正容量不足是设计不可执行；编程缺陷不得伪装为不可执行。

### 4.4 强文本 T_MATCH

保留原 M/R/L 与完整 G，并添加同一批按实体分组的前后数值及归属关系。图像不能靠多提供事实获胜。文本不接收图形阅读指南。TPV/B3 原输入不因新接口而被覆盖。历史端到端差异不冒称纯视觉增益。

## 5. 实验 A：exp_numeric_relation_fusion

RQ3.6 暴露开发180（每主数据集60），两个模型。

- 五个运行条件：T_MATCH、REMOTE_ID、REMOTE_LINK、LOCAL_ID、LOCAL_LINK，最多 **1800次新增调用**。
- 两个只读参考：TPV_REF、B3_G_REF，最多720个历史引用位，**新增调用为0**。缺少旧结果时如实缺失，不补跑。
- 删除 B3_T_REF 的整项结果比较；其公共输入仍用于锚点核对，不调用模型。

A最多2520个逻辑记录，其中仅1800个允许生成。兼容引用不是独立样本，不把逻辑记录数当作新增调用数。

八项主 family：两个模型分别 LL−REMOTE_ID、LL−T_MATCH、LL−B3_G_REF、LL−TPV_REF。六项 secondary family：两个模型分别邻近主效应、连接主效应、交互：

```
邻近 = (LOCAL_ID + LOCAL_LINK − REMOTE_ID − REMOTE_LINK)/2
连接 = (REMOTE_LINK + LOCAL_LINK − REMOTE_ID − LOCAL_ID)/2
交互 = LOCAL_LINK − LOCAL_ID − REMOTE_LINK + REMOTE_ID
```

LL−T_MATCH 回答同内容视觉价值；LL−TPV 回答完整方法采用价值。两个模型完整运行，不凭先完成者取消另一者。

五个新条件采用同一完整配对集合；历史参考缺失不删掉它们已经完整的病例。LL对各历史参考的检验进一步取实际可配对交集，单列N及缺失敏感性；八项主family大小不因缺少历史比较而缩小。扩量条件使用同病例差值的三数据集macro，不相减分母不同的总均值。没有必要配对证据即不能建议C。

## 6. 实验 B：exp_numeric_encoding_robustness

按 seed42 冻结 hash 从180选每数据集30，共90。对 T_MATCH、REMOTE_ID、LOCAL_LINK 各增加 SCIENTIFIC、UNIT_EQUIVALENT、REPEAT；原输入由 A 提供。最多1620新调用。

- SCIENTIFIC：M 维数量用等值科学计数法，JSON 数字仍是数值而不是字符串；不改变 ID、时间、rank、σ、排序、候选、关系。
- UNIT_EQUIVALENT：严格来源白名单，对已证实时间/字节量作十进制单位换算；正文、重复观测、字段展示名称、小图、轴语义同步更新。保留反向转换映射、确切 Decimal 值，不新增四舍五入。未知单位不猜。无可换算量保持完整原请求，复用并报告空干预。
- REPEAT：原请求同推理配方再次调用，独立 replicate 身份；不得被去重，不取最好回答，也不把固定 seed 宣称为不同独立随机种子。

报告 MRR、首位翻转、根因排名移动、候选数量、数值误读和单位误用；将变换差异与重复波动对照。不是独立 QA。

## 7. 实验 C：exp_locked_fusion_generalization

固定 TPV_REF、B3_G_REF、T_MATCH、REMOTE_ID、LOCAL_LINK。完整 RQ480（兼容复用 A）、旧 test360（已暴露回归）、每主数据集最多30个真正未使用事件（最多90）。最多9300调用。只读审计全使用历史、事件别名和重叠窗口传递组；不拆组凑数，不把旧 test 更名。新事件名单必须在任何新结果前封存。当前配置没有完整 exposure audit，fresh 默认空并明确 unavailable；之后不能在已启动登记中偷加。

C仍不进入默认队列。原开发180的两个历史参考继续只读引用；开发180之外确无兼容旧结果的病例，未来获准C后才可生成必要基线，它们是新病例的比较依据，不是为补A缺失而重跑。C上限保守保持，实际复用会进一步降低。

不自动启动 C。完成 A/B 后，只有 Qwen 三主数据集 macro LL−TPV≥.03、LL−T_MATCH>0、任一主数据集下降≤.03、Gemma macro 下降≤.03、两模型各自 node 子组下降≤.05 且各有≥20有效配对时才建议扩量。证据不足不算通过。此为探索性控制成本的建议，不是显著性或非劣证明；还需用户授权。

## 8. 分析与模式

MRR primary；AC@1/3/5、AVG@3/5、repair/break、候选数量、非法 ID、输出失败与成本。每数据集、AIOPS合并、主数据集macro、pooled分开。统计单位case，两模型不合成答案，不把引用/重复当额外病例。Pratt-Wilcoxon、paired dz、预注册Holm，无CI。重叠事件组补充组级敏感性。

模型输出错误/截断留在原评分；请求timeout属于infra缺失，按实验×模型共同case配对（A核心与历史参考交集按第5节分开），加缺失极端差值敏感性，不新增5%门槛。只读参考缺失不是模型失败、不记0。不可执行新设计端到端记0并独列适用性。投入成本包括失败调用，token文本/图像/输出分开，跨模型只作各自基线比例，不许把更省input写成更省output。

模式审阅覆盖修复、破坏、不变：极大z但实际变化小；根因数值存在但实体孤立；宿主与实例竞争；正确引用但排名错误。公开reason仅是可观察解释，不推断隐藏思维链。自动队列保存完整输入/输出定位；人工填写仍待完成，不伪造自动因果归因。

## 9. 实现与恢复

五功能模块+init，≤7500非空非注释行；新 renderer 在RQ3.7，不修改旧 renderer。五接口：FrozenEvidenceViewV1、NumericPanelV1、FusionSceneV1、EquivalentEncodingV1、InterventionAuditV1。

公开编译/renderer不接收标签。evaluator在请求冻结之后加载private。一次case加载，公共小缓存跨arm/model复用，8独立物理核心worker、按source交错、有界预取、36请求线程、异步writer。冷缓存仅构建对应canonical per-case，不重扫全数据。

采用本工作树 `configs/vllm_inference_local.yaml`，冻结本地Qwen/Gemma BF16及8192输出adapter；300秒请求timeout终态fail继续、不自动重试；其他infra失败停止。模型服务ready与首次提交分别记录。done/fail在必要产物持久化后提交；续跑只读取小flag，完成目标不加载context/重建请求/核验大图。无commit的中断目标续做，不拼接partial答案。

共享累计40000上限不因目录重置。新目录直接链接同一个累计SQLite，在登记时只读核对实际累计，不复制一个会过时的计数器；未来新调用追加RQ3.7 scope，旧调用记录不改。所有发起请求含失败和重试计数。已完成重复请求只引用保存结果。复用索引包含完整实际请求、模型、case、replicate、formal/smoke身份。

## 10. 预算与资格

| 项目 | 最坏新增 |
|---|---:|
| A：五个新条件；历史参考不补跑 | 1800 |
| B | 1620 |
| C：eval480+test360 | 8400 |
| 新事件最多90 | 900 |
| 三个逻辑smoke | 54 |
| 合计 | 12774 |

历史设计基数21469，最坏总34243、余额5757；执行登记读取真实值，不能把余量自动转成新探索。相对原最坏新增13854减少1080（360来自删除B3_T_REF，720来自禁止另两项参考补跑），这不是承诺比原本成功复用的执行必然节省1080次。A+B最多3420次新增，含两项smoke最多3456；C仍需以后单独授权。

本轮三个静态focus：①科学逻辑/历史重复/公平性；②链路/性能/恢复/语法/占位；③泄漏/数值/绘图。只解析源码配置、AST、shell、lint，不导入实验模块执行。

未来CPU资格≤1800秒：极值/常量/负值/零/状态counter/未知单位、多指标实体/孤立/环/自环/反向边、长名称密度、真实双processor上下文、private扰动、四图事实/geometry/连接、换算可逆、快flag、repeat不去重、writer边界。真实三例来自主数据集暴露开发集。

每实验一个≤18calls、≤600秒逻辑smoke，模型顺序，含启动切换写盘，不拆分规避上限。只有总wall超时且无其他错误时可为bounded-timeout-only；覆盖未完需如实列出。真实PNG、输入、conversation和raw/partial输出还需人工查看，静态检查或自动artifact检查不能替代。

## 11. 本次交付与下一步入口

协议和源码见 `RQs/RQ3_7/`；静态审阅见 `docs/issues/RQ3_7_static_review.md`。

本轮不执行下面命令。后续明确获准后可用：

```bash
cd /home/lglsj/CanvasRCA_nibi
bash RQs/RQ3_7/scripts/entry.sh register
bash RQs/RQ3_7/scripts/entry.sh cpu
bash RQs/RQ3_7/scripts/entry.sh smoke --experiment A
bash RQs/RQ3_7/scripts/entry.sh smoke --experiment B
bash RQs/RQ3_7/scripts/entry.sh smoke --experiment C
```

正式队列需当前资格、真实输入输出人工审阅及独立的用户授权记录；默认仅A→B。C单独授权且满足扩量证据，不自动扩大。分析入口 `entry.sh analyze` 只读完成阶段、生成统计和案例审阅队列。没有实验结果之前，findings保持未运行。

## 12. 后续设计方向：贴近真实 on-call Dashboard（2026-09-28）

用户在查看当前 LOCAL_LINK 例图后指出文字过多、不像实际运维 Dashboard。后续设计以真实 on-call 工程师的观测与比较需求为参照：图表和系统关系是主体，文字承担简短的实体、指标、单位、关键数值与图例说明，不把大段证据表搬进图片当作主要视觉表达。

- 优先让趋势、前后变化、实体归属和关系容易辨认；采用清楚的视觉层次、合理的信息密度与留白，避免满屏文字框和不必要的查表跳转。
- 当前为受控比较而保留的空白槽位和长关系明细，不作为后续部署界面的默认模板。后续可以重新设计组织方式，但不能为美观偷偷删除关键诊断证据或引入根因暗示。
- 保留必要的准确标注；详细文本放在注册条件允许的文本输入中，不预设所有信息都必须重复写进图里。表示调整与证据选择分别登记，避免把信息变化解释成视觉收益。
- 后续版本先人工查看真实稀疏、密集和长名称案例的 PNG，再进入昂贵推理。美观、接近运维习惯是设计目标；MRR 仍优先，不能仅凭外观声称提高诊断或人工核验效率。

这是未来版本的设计方向，不是本轮输入修订。正在进行的 RQ3.7 阶段 C 保持既有图像、prompt、配置与比较条件不变；既有结果的状态不因此改变。本条不启动新实验。
