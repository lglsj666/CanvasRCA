# exp_semantic_calibration

2026-09-23：实现完成、源码检查阶段；尚未准备或运行。无有效性结论。历史源请求及exact-span补丁必须先经过真实来源审核，不能用新合成输入代替旧SC输入。

执行及比较协议见 [实验说明](../descriptions/RQ3_3_experiments.md)。后续本文件记录实际校准与条件式两调用诊断，不覆盖旧RQ3.2 findings。

## 2026-09-24：校准与条件式诊断已完成

保留上述实现阶段记录；本轮结果更新如下：

- GUIDE_FIXED−AS_RUN：60-case 配对 Qwen ΔMRR +0.0061，Gemma 0；均无校正后显著收益。
- SOURCE_FIXED 与 GUIDE_FIXED 的 120 份请求相同，`source_patches=[]`；这是没有确认可修补源字段后的合法复用，不是独立新效果。
- 条件式两调用诊断在筛查 60 cases 上完成。Qwen FIRST/REPEAT/VERIFY_SAME/VERIFY_WITNESS 的 macro MRR 为 0.3500/0.3417/0.3417/0.3694；Gemma 为 0.1889/0.1833/0.2083/0.2028。
- 见证核验相对同信息核验的差异小且模型相关；总调用成本约翻倍。没有证据支持直接扩大当前两调用路线。

见[完整分析](../../../docs/RQ3_3_Results_Analysis_2026-09-24.md)。没有改动旧 RQ3.2 结论、原回答或评分。
