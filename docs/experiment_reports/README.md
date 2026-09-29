# 实验报告

按研究顺序阅读；不同报告的样本集合、模型请求、排除口径和开发状态不同，不能直接将各表的最高 MRR 拼成学习曲线。

| 报告 | 主要范围 | 阅读重点 |
|---|---|---|
| [RQ1.1 / RQ2.1 汇总](RQ1_1_RQ2_1_findings/findings.md) | RQ480；直接 RCA、表示、QA、选择、剪影及编排 | 选择性视觉、信息组成与成本；QA 采用报告内注明的重评分口径 |
| [Tournament](Tournament_Analysis_2026-09-15.md) | 38 轮自适应剩余集 | 方法互补、晚覆盖和未覆盖模式；联合覆盖不等于一次推理成绩 |
| [RQ3.1](RQ3_1_Results_Analysis_2026-09-19.md) | Contrast 路线、360-case test 等 | X 的证据替换、node 盲区、强文本和 TPV 对照 |
| [RQ3.2](RQ3_2_Results_Analysis_2026-09-22.md) | SignalCover、表示、机制及锁定回归 | 基础保留、覆盖与实际实现的区别；选择收益与视觉损失 |
| [RQ3.3](RQ3_3_Results_Analysis_2026-09-24.md) | screen60、check120 及诊断条件 | 完整保留 TPV 后追加见证；联合统计的实际干预覆盖不足 |
| [RQ3.4](RQ3_4_Results_Analysis_2026-09-25.md) | 同一历史 screen60/check120；3,720 个逻辑单元 | P/H/K 因子、候选契约修复、图文承载、解释自洽与诊断质量的分离 |
| [RQ3.5 screen](RQ3_5_Screen_Analysis_2026-09-26.md) | A/B screen60；1,440逻辑单元、1,248新正式调用 | 证据×指令、候选排名深度、J实际覆盖与失败模式；不是整条RQ3.5后续路线完成 |
| [RQ3.6 阶段A](RQ3_6_Stage_A_Analysis_2026-09-26.md) | check120；11条件×2模型、2,640新正式调用 | 证据×指令与G/V拆解、接口校准、首位/尾部、pod/node取舍和机制信号；Qwen主配对97例、Gemma120例 |
| [RQ3.6 机制](RQ3_6_Mechanisms_Analysis_2026-09-28.md) | 暴露开发集；G信息来源、补充证据与关系绑定 | 调用/部署/观测绑定的条件效应，及 B3 ALL_ID 的跨模型差异 |
| [RQ3.7 A/B](RQ3_7_Results_Analysis_2026-09-28.md) | 开发180、稳健性90；含120次TPV补跑，C未运行 | Qwen相对TPV显著提升；强文本/析因尚未确认，Gemma退化线索，等价数值敏感性与真实案例 |
| [跨实验方法能力画像](Cross_Experiment_Method_Profile_2026-09-26.md) | RQ1.1–RQ3.6 A、Tournament、CPU基线；840唯一cases | root层级、fault type、依赖图规模/hop、Metrics复杂度；全方法附表、阶段内配对、数据集内调整及剩余集边界 |

`*_assets/` 和 `RQ1_1_RQ2_1_findings/assets/` 是报告的组成部分，包含图片、逐样本/汇总表及部分复算脚本，不是重复报告。应与 Markdown 一起保存。

最新阶段判断见 [RQ3.7 A/B报告](RQ3_7_Results_Analysis_2026-09-28.md)与[对应计划](../experiment_plans/CanvasRCA_RQ3_7_Research_Plan.md)。C满足探索性扩量推荐，但未运行；本次只做分析。历史报告和原始评分不改；新分层属于事后探索，不替代原登记检验。
