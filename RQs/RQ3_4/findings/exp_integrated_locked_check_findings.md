# exp_integrated_locked_check

## 2026-09-25 正式结果：已完成，未证明超过强基线

原推进条件通过后，check120 × 6条件 × 2模型共1440逻辑单元，1433 done、7次Qwen请求超时。whole-case配对Qwen113（38/39/36）、Gemma120（各40）；这是已暴露开发组的锁定复核，不是新独立test。

三主数据集macro MRR：主方法P1H1K1_G **Qwen 0.4219、Gemma 0.3611**；TPV **0.4163 / 0.3458**；MORE **0.4414 / 0.3750**。主方法对TPV、MORE、SIRCL_IDS跨两模型的六项比较均未通过Holm；事件组敏感性结论一致。Qwen不加K为0.4468，但仅略高于MORE，不能据此事后升格主方法。

可核验关系降低部分可抽取reason冲突告警，却不稳定提升MRR；真关系也可能干扰更强诊断证据。G图相对G文本有排序修复线索，但其结论限定为当前选择性视觉对照，不能泛化为全视觉优势。原始回答／评分／失败不改，不自动扩到RQ480或训练。详见含定量、定性、分层、成本和原图的[综合结果报告](../../../docs/RQ3_4_Results_Analysis_2026-09-25.md)。

## 历史资格记录（以下“未运行”是当时状态）

**最新资格：passed。** 相对时钟修复后的2个变化单元与前序同case、同模型的T_VERIFIED完整请求相同，直接复用；其余16单元同输入引用。18逻辑单元均完成实际输入与artifact核查，新增0调用，不重启模型。正式check120及推进判断均未运行。以下为此前过程记录。

状态（2026-09-24）：已实现并完成CPU检查；Z3-context修复后，三个开发样例的18/18调用GPU smoke通过，耗时250.97秒，未再崩溃。正式check120未运行，前序MRR推进条件尚未评估；smoke通过不等于允许或已完成锁定效果复核。

后续实际prompt审阅发现一个case的追加 `container_start_time_seconds` 为绝对Unix时钟，本smoke2份输入受影响。相对时钟修复及42项测试、120请求CPU回归通过后，当时资格为cpu_fixed_gpu_pending，现已由上述新输入的等价复用与核查覆盖。原记录保留，见[问题记录](../../../docs/issues/RQ3_4_qualification_2026-09-24.md)。

六个固定条件在旧 check120 上做锁定回归。这批 cases 已在既有研究中暴露且参与过离线核验，不能称新的 untouched test。未通过推进条件时不自动挑其他组合替代主方法，也不自动扩到 RQ480。

设计权威：[合并协议](../descriptions/RQ3_4_experiments.md)、[登记](../configs/integrated_round_v1.json)。
