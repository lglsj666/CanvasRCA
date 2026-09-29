# RQ3.4 — Evidence attribution with verifiable reasoning and selective vision

最新状态（2026-09-24）：独立 CPU 可行性实验及合并路径已实现。Z3 并发与时钟输入修复后，用户授权的定向 GPU 补验已完成：16 新调用＋2 同输入复用＋54 未改输入引用，共72逻辑单元核查通过；最新45项CPU测试和120请求身份等价检查通过。四项当前资格均为 `passed`，**仅覆盖注册smoke路径，不是诊断效果结论；未启动正式实验、训练或自动答案修复**。原失败与模型错误记录保留。详见[问题记录](../../../docs/issues/RQ3_4_qualification_2026-09-24.md)。

独立 CPU 可行性原结果见 [findings](../findings/exp_claim_verification_cpu_findings.md)。RQ3.3 已正常完成，开发扩展条件未通过，原结果、分数和输入保留不动。同日用户要求将 auto reasoning 与原有下一步合并；登记入口为 `configs/integrated_round_v1.json`，正式执行仍禁用。

> Can improved evidence prioritization, host–instance comparisons, and source-grounded reasoning jointly improve one-shot RCA accuracy, and what additional value does selective vision provide under matched evidence and reasoning support?

**MRR 优先，可靠性独立衡量。** 研究三类可分离的瓶颈：诊断信息没有入选、源头与受害者缺乏区分、已知事实被错误绑定或推导。核验不是取代前两者的第四种异常排序器，也不能将“解释自洽”替代正确诊断。

统一部署候选保持完整 TPV 底座，加上有界、来源可追溯的证据及关系；冻结 Solver 只调用一次。输出／类型契约、优先级、宿主范围、核验与图文表示分别有对照，不把所有变化塞进一个新方法后只与弱基线比较。

以下为先行 CPU 子实验的原有范围说明，其结果与状态不因合并被改写。

本轮先回答前半句，不把“发现错误”冒充“已经提高 MRR”。可靠性是独立价值：核验非法实体、属性绑定、显示数值和已观测关系；不能将形式自洽直接等同于真实根因正确。

用户明确认可自洽性检查的研究价值。下一步优先从已有失败出发，实现无需训练、无需新模型调用的核验器，而不是继续扩大收益不足的 Witness 条件。首次范围仅为已暴露的 RQ3.3 check 阶段，避免重做大型 preparation 或打开新 test。

输入边界：核验器仅接收实际请求中的文本／图像身份及其已登记同事实 ledger，不接收 gold、注入时间、fault type、数据集身份或模型成绩。公开回答中的 claim 是待检验对象，不是事实库前提。离线分析层可以在核验完成后关联历史得分，但不得改写原评分。

当前实现只覆盖有限的、显式定义的断言。未抽取的自然语言、未观测边和未编码因果知识均不能当成已验证。此阶段不做完整自动语义解析，不做隐藏思维链审查。
