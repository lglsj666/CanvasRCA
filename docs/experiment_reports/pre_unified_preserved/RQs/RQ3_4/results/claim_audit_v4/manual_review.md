# 2026-09-24 — 八条按 hash 抽样的候选断言复核

范围：两模型 × type/display_number × 各两个 refuted claim，使用 `SHA256(call_key + json.dumps(claim, sort_keys=True))` 排序。单 Agent 阅读，不是独立双人标注；不估计总体精度／召回率。完整原句和源文本见同目录 `records.json`。

| hash 前缀 | 模型／case／arm | 逐例判断 |
|---|---|---|
| 4d0757f3 | Gemma / INC-D3EAA310B962 / W_T | `jvm_classes_loaded` spike starting +28m，与 G 的实体 onset +29m 不同；metric-specific 与总体字段可能不等价。保持未确认，不能仅据差异判幻觉。 |
| 50fec306 | Gemma / INC-50C26A55D214 / W_G | `service 762 ... its onset (5.2m)` 与 G ledger 的该服务 +4.9m 相反；同段给 871 的 4.9m 实际是 762 的值。可确认对公开 G onset 的绑定错误；不据此自动改答案。 |
| 01f178e1 | Gemma / INC-B51CCEE61D70 / W_G | `service 45409` 与明确的五位 pod 映射不符；属于字面类型不合契约。尚不能据该措辞判断它是否实际把 pod 数据错绑定给了另一个实体。 |
| 025806a8 | Gemma / INC-3292326B0AA6 / W_T | `Service 9472` 是四位 node；字面类型冲突。关系推断还需逐条核验，不能把类型冲突扩展成整段都错。 |
| 0049055c | Qwen / INC-8E0FB1B7B3FE / P0_MORE_TRUE | exclusive-latency onset 34m 被粗略映射到 G 的 M 来源 onset 33m。量的绑定不成立，拒绝确认该自动数字标记。该回答 AC@1=1；不能删掉它或重新评分。 |
| 101d6c25 | Qwen / INC-B5AB9A371DE9 / W_T | 声称服务 745 的 earliest telemetry onset +24.0m，G 记录 +38.0m。存在明确的 G 引用不一致疑点，但原句随后提及特定 `mrt` 指标；未完成逐 metric 核查前仍不计为已确认的全局时间幻觉。 |
| 079d62f3 | Qwen / INC-1D40A642FA86 / TPV | `Pod 300` 与三位 service 映射冲突；局部字段归属和真实根因正确与否另行判断。 |
| 07a092d8 | Qwen / INC-392EE028390B / W_T | `service 7438` 与四位 node 映射冲突；并不单独证明其后提到的 cascade 存在或不存在。 |

附加手动形式查询（不是自动自然语言解析准确率）：在 `INC-50C26A55D214` 同内容 W_T 公共事实库中，`onset:871 < onset:762`=refuted，反向=entailed，`calls(810,762)`=entailed，`root_cause(762)`=unsupported。比较使用四舍五入区间，返回对应两行 onset / 调用边来源，无 private label 输入。
