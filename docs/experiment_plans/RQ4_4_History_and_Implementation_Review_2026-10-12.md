# RQ4.4 历史复核、差异及实施登记

本轮使用已暴露 220 例；历史结果均只读复用。未把旧批次视为同期对照。

| 报告/记录 | 状态及证据 | 设计决定 |
|---|---|---|
| RQ3_16_Qwen_Analysis_2026-10-03 | 完成；MARGINAL_FIVE .5054、PAIR .4436、去点 .4963；主要校正未通过 | 最高混合参照保留，非纯视觉 |
| RQ3_17_Qwen_Analysis_2026-10-04 | 完成；N .5048、矩阵组合 .4957、节点组合 .4778 | 不再拓扑组合 |
| RQ3_18 findings/exp_population_readout_findings | 完成；FP .4877、T .4243、F .4648；Aegis 下降 | 不以读数替代排名 |
| RQ3_19 findings/exp_visual_replacement_qa_findings | 完成；F .4562、V .4139；QA .9435→.9972，RCA 未同步 | QA 与 RCA 分开测量 |
| RQ3_20 结果及关闭取证决定 | 完成；F .4693、T .3782、V .3866；选择接口无效 | 不继承两阶段 |
| RQ3_21_Qwen_Analysis_2026-10-06 | 完成；压缩视觉 .41795、RAW_VISUAL .49338；位置翻转远多于重复 | 不压缩字符串，增加顺序控制 |
| RQ4_1 完整报告 | 完成；U .351742/.369167（标准/宽容），T .484621；CVC 省 token 未同比省时间 | 原 U 保留集合及原图作为基础 |
| RQ4_2 完整报告 | 完成；FULL .2841、SEM .3084、NATIVE4 .3235 | 不继续来源 attention 分组 |
| RQ4_3_Qwen_Analysis_2026-10-12 | 4832位置完成；P_SOFT .349091/.362727，X_SRP .262955；顺序首选翻转39/60 vs重复5/60 | 干预视觉编码前细节；不要只怪评分 |

报告源在 `docs/experiment_reports/`，RQ3.18/19 唯一报告在对应 `RQs/*/findings/`。复核亦覆盖 important_docs 的 empirical-to-method、文献、反直觉、attention 与 conversation_oct_06，以及 plans/design_decisions.md、Codex.md。旧混合/两阶段建议被最新纯视觉单调用约束取代；attention 热点不是因果使用证明。

文献区别：ViCrop 用裁剪提高小目标读取，本轮 renderer 已知来源无需模型先选区域；视觉符号绑定论文不构成本地 Qwen 的机制证明；EMNLP 图表感知论文区分视觉/提取瓶颈，本轮仅改善可见输入条件，不训练模型。

生成差异：SOURCE 与 REPEAT 卡片/位置/像素尺寸相同，唯一详情源分别是原始 DOM 与 processor 后概览像素；HASH 改优先级而保留覆盖/预算。三者均与历史 U 有新增图像和公共多图读法，因此不能引用 U 回答代替。历史评分身份与生成身份分开；评分变更仅离线重算。

未满足需求：已有区域导出只能导出固定四区，不能按完整来源卡片和实际字号生成高清/低分辨率匹配图集。新增 source_views 显式操作；不修改现有组件。实际实现细节及资格发现追加到 RQ4_4 唯一 findings，不追改历史结果。

调用登记：660主矩阵+120 QA+60重复/顺序=840正式；18共享smoke；42仅基础设施恢复，总900。未用额度不转新条件。原始 U/T/MARGINAL 均不重跑。
