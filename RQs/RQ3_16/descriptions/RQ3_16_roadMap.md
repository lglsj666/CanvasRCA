# RQ3.16 roadmap

## Current status — formal run and detailed analysis complete; candidate stopped

2026-10-03：1760终态（1713响应、45引用、2超时），自有服务已退出。完整graph/实际输入图像/评分/成本及注册统计审计通过，36病例288解释阅读与定向核验完成。预选MARGINAL_FIVE pooled MRR .5054，但对markless仅+.0091，四项主要病例/事件组Holm均不显著；A25/Aegis覆盖护栏失败。固定五的次要MRR/Top5收益不能代替图元机制成功。按注册停止该边际耗时候选，无自动新实验、布局更改或test。RQ3整体目标仍未达成。

[Final detailed report](../../../docs/experiment_reports/RQ3_16_Qwen_Analysis_2026-10-03.md); machine-readable checks and adoption decision in `results/marginal_coverage_v1/analysis_detailed_v1/`. Historical launch/qualification below retain their time-specific authority and counts.


## Historical authorized launch

2026-10-03最新执行状态：用户随后明确授权全量实验，已于 **13:22:16 America/Toronto** 在后台启动RQ3.16原八臂、220例、1,760位置正式队列。13:25:17核验时7份真实响应已原子提交、36次在途，无失败；实际输入/PNG/token与资格一致，显存利用率参数0.75。该快照不是完整效果结果。授权仅改变两处执行兼容/权限函数，原CPU/GPU资格、配置、输入、评分、预算和统计门槛保持不变。自有服务在队列结束后自动关闭，不启动后继实验。

The frozen experiment protocol/config retain their original qualification-stage stopping boundary. The new scoped authority is `results/marginal_coverage_v1/qualification/activation_v1/full_authorization.json`; original measured reviews and archives remain immutable. Effective source hash: `fbd23ac5b419c2a229c667a75403c0bceb3f04a28d32c1c3cfdc6e1d39f897a1`.

## Qualification-stage roadmap (completed history)

1. Freeze the prospective eight-arm protocol and preserve historical sources.
2. Implement only the cardinality adapter, markless presentation and qualification.
3. Pass static, complete CPU/token/source/DOM, actual visual and scientific review.
4. Freeze measured source; run the one bounded 18-call GPU smoke and shut down.
5. Deliver qualification artifacts and stop. Formal 1,760 positions remain disabled.

Future formal execution requires a new explicit user instruction and an audited
authorization-only activation. Failed prospective adoption ends this candidate;
do not automatically tune layouts, choose a repeat or reuse exposed eval as test.
