# 2026-09-24 — RQ3.3 完成开发阶段的离线分析

## Scope and status

对象为 `witness_v2` 完成的 calibration、screen、budget、check、diagnostic。历史已暴露的开发 eval，非正式效果/独立 test。契约 `569ba594f36c0074e788153d0c2f22da30f2153c822ee267cd1684880d194aa9`；原队列状态 `completed_negative_development`，未更改。

## What happened

只读既有 flags、analysis、输入输出、projection、conversation 和评分 metadata；制作可复算脚本、9 张统计图、3 张原输入图副本、分层表及全部 15 个首位修复/破坏转换与共同难例索引。报告位于 `docs/RQ3_3_Results_Analysis_2026-09-24.md`，附录在同名 `_assets/`。

核对 3720 个逻辑单元（3713 done、7 timeout），3161 次正式实际调用（3154 成功返回、7 基础设施失败），559 个成功逻辑单元由复用完成。没有新模型调用；没有修改实验代码、配置或评分器。

## Validity and caveats

check 共同分母 Qwen 118、Gemma 120；timeout 做配对排除，非法模型输出保留原零分。MRR、AC@1/3/5、AVG@3/5、tokens、耗时、fault/粒度与数据集均有附表；无 CI。不能将 sampling 波动、关联分层或人工案例当完整因果证明。476 个配对输入审核确认保留 TPV 原 parts；三张报告用 PNG 对输入 SHA 核对。其余历史证据按原状态保留。

## Decisions

本次仅整理结论和建议，没有新执行决策。Qwen W_G macro MRR 0.4398，TPV 0.4000、MORE 0.4304；W_G−MORE=0.0094124 未达注册 0.01。Gemma W_G 0.3333 低于 TPV 0.3708。保留原不扩量决定，不四舍五入改判。

## Blockers

后续正式效果与机制/泛化未启动。现有证据不足以扩大当前方法；主要待研究入口是选择分数并列、宿主/实例归因、实体—时间绑定、SIRCL 数字候选适配以及 Gemma 短列表行为。这里只记录分析，不自动修复或补跑。

## Next steps

由用户审阅报告，再决定是否登记针对性改进。可从现有报告脚本复算；无需重新 preparation 或加载模型。
