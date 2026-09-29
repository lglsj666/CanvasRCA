# exp_qualified_witness_and_graph

最新状态（2026-09-27）：用户要求暂停并重设计。旧B正式调用为0；启动服务探测遗漏认证导致401等待，现有队列和服务已停止。18次smoke只保留资格意义。第二次历史核对发现旧SEARCH及RQ3.4已覆盖部分拟研究问题，后继须去重后另行冻结。详见 `docs/issues/RQ3_6_historical_question_audit_2026-09-27.md`。下方启动条目是历史记录，不表示仍在运行。

状态：2026-09-27资格通过后，用户另行授权正式B；14:17:54 UTC后台队列启动，PID4396，首个Qwen服务加载中。尚无完整阶段结果，不能报告阶段B疗效、MRR改善或视觉机制结论。当前进度以结果目录 `formal_queue_status.json` 为准；C/D不自动启动。

十四个注册条件，后续正式上限5040调用，180重复暴露病例、两模型。强关系文本、换序与截图控制用于检验旧G图优势的其他解释；同内容scope文本/图检验实体层次与观测绑定。W动态资格及去peer保留旧W/MORE对照。

资格：10单元测试、84CPU请求、18/18 GPU smoke，分别18.351秒与276.903秒。新增18调用，累计10917。输入、raw、conversation、PNG与cost均保存；没有attention。模型回答中仍有不实关系、类型混淆和正确排名下的错误解释，全部保留，不用资格结果选择方法。

协议：[experiments](../descriptions/RQ3_6_experiments.md)。
证据：[人工审查](../results/visual_mechanisms_v1/manual_review.md)、[问题及修复](../../../docs/issues/RQ3_6_stage_B_qualification_2026-09-27.md)。
