# exp_witness_development

2026-09-23：实现完成、源码检查阶段；未调用模型、未选择variant/预算、未产生check结论。筛查和check不共享事件组，阴性不换第二名重试。

执行及比较协议见 [实验说明](../descriptions/RQ3_3_experiments.md)。

## 2026-09-24：开发阶段已完成

本节更新阶段状态，保留上述实施时点记录。`witness_v2` 已完成 screen、budget、check；只使用登记的开发案例，不是 RQ480 正式效果或 test 结论。

- 冻结方案：W_RAW，2048-token 追加预算；check 是独立于筛查事件组的 120 cases，但仍属历史已暴露 eval。
- 三数据集等权 check MRR：Qwen TPV 0.4000、MORE 0.4304、W_G 0.4398；Gemma 分别 0.3708、0.3646、0.3333。全条件共同分母分别为 118、120。
- Qwen W_G−MORE 为 0.0094124，未达注册的 0.01 推进条件；没有因接近门槛而改判。队列正常结束为 `completed_negative_development`。
- W_G 相对 TPV：Qwen 首位修复/破坏 8/2，Gemma 1/4；本轮注册的 Holm family 没有显著比较。负向或不显著不等于证实方法无效。
- 检查中原 TPV 文本及 G 图未删改；资源见证可以修复 node 案例，也可能让局部 pod 故障被上归因给宿主。全部修复/破坏回答已纳入案例索引。

完整统计、成本、覆盖、故障分层、实际输入图及复算脚本见[本轮报告](../../../docs/RQ3_3_Results_Analysis_2026-09-24.md)。阶段权威仍为原运行的 `method_lock.json`、`expansion_decision.json` 和 `formal_queue_status.json`；本次不修改它们，不启动后续实验。
