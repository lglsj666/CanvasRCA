# RQ3.4 相对时钟定向 GPU 补验 — 2026-09-24

## 结果

**四项注册 smoke 路径的当前资格通过；正式实验未启动。** 54 个输入未变的完成单元引用原记录；16 次新推理完成，另 2 个锁定复核单元复用同 case、同模型、同完整输入的 T_VERIFIED 回答。72 个逻辑单元齐全，36 对跨模型公开输入一致。资格不代表所有非 smoke arms 均已经 live 验证，更不是 MRR 效果结论。

| 实验 | 受影响逻辑单元 | 新调用 | 本次成功执行秒数 | 含入口失败的累计秒数 |
|---|---:|---:|---:|---:|
| exp_contract_alignment | 6 | 6 | 209.09 | 314.40 |
| exp_evidence_reasoning_factorial | 4 | 4 | 210.89 | 210.89 |
| exp_verified_visual_binding | 6 | 6 | 211.19 | 211.19 |
| exp_integrated_locked_check | 2 | 0 | 0.004 | 0.004 |

每项均低于600秒，新增16次不超过本次18次定向上限。现累计3,395次：继承历史3,300＋先前72完成＋7中断＋本次16完成。不删除或清零旧调用。45项CPU测试和120个请求身份等价检查通过；补验控制入口未改变修复后科学输入。

## 入口故障及修复

首次控制器把字符串 `repair="clock"` 错传为布尔 `True`，进入只授权旧图文实验的分支。Qwen启动后、提交任何模型请求之前退出：0新增调用，耗时105.31秒。已修正标志传递并增加专门的driver回归；失败日志和metadata保存在 `../relative_clock_gpu_v1_controller_attempt1/`。该耗时计入契约实验600秒预算，未通过重置窗口规避限制。最早仅有import格式差异的无GPU setup留在 `../relative_clock_gpu_v1_setup_preformat/`。

成功补验无请求超时、vLLM engine死亡、Z3崩溃或写盘失败。日志仍有可选 deep_gemm import warning 和首次 Triton JIT 延迟提示，冻结的执行路径正常完成；未修改模型配方消除警告。测试进程和所属服务均已退出。

## 输入与产物审阅

逐项检查72个逻辑单元的实际prompt与当前CPU请求：system、文本、schema、有效配置及图片hash一致；按completion manifest定位真实raw/conversation，包含历史`__callNNNN`重试文件名，不猜文件名判断缺失。全部conversation含完整用户输入与原回答，实际图片与登记字节一致。

实际新SIRCL文本使用共同相对时钟，例如`10496.container_last_seen[relative_clock_seconds]`为`645037.0 → 646237.0`，标准差`345.98`不变。新追加观测中`container_start_time_seconds`前后为`600.0 relative_clock_seconds`，未再显示原Unix启动时钟。单位说明与观测窗口明确分开。两模型的公开输入相同，不接收private标签；选择、候选、原TPV/MORE与G图不因补验改变。

打开了本次实际收到的G PNG：冻结原TPV图、M/R/L承载文本，G保留原位置及调用边列表；不在此时钟修复中改画布布局。没有生成attention文件或进行训练。

所有16份新回答已阅读，finish_reason全部为`stop`，JSON均可解析。其中15份为普通完成，1份按原输出契约记为`model_failure`：Qwen SIRCL_NATIVE输出`node-4176`而非候选`4176`，未知ID检查捕获，保留原回答与评分，未修答案或重采样。

6份新回答的12处字面实体类型错误被核验sidecar捕获，包括把`81384`（pod）称为node/service，把`2532`（node）称为service。12为出现次数，包含同一回答重复误称，不是12个独立病例。核验器依然只是有限字面检查，并不覆盖全部reason错误：

- Qwen SIRCL_IDS_ALT把`15.25 → 48.6`在reference std=`146.17`下说成显著3-sigma偏离，数值解释不成立；未将其混为传输/代码错误。
- Qwen T_NONE称有`212 → 217`边，实际显示调用边中没有该边；缺少记录只支持“未被当前证据证实”，不自动证明真实系统没有该边。
- Qwen T_VERIFIED称`+23m`早于`+22m`，并将最高severity解释成根因；这是公开reason中的数值/推理错误，不能因增加核验块就声称已消除。
- 多份回答把最早出现或未画incoming edge直接当故障源证明；采样样例仅支持错误模式记录，不据此调设计、推断总体改善或比较MRR。

## 权威记录与下一步

- `final_review.json`：72逻辑单元、16新调用、输入一致性、逐回答与成本索引。
- `smokes/*_clock_repair_v1.json`及`*_artifact_review.json`：各项完成情况与artifact核查。
- `clock_authorization.json`：明确授权、额外调用上限、已消耗时间。
- `parent_metadata_before_acceptance/`：更新当前资格前的metadata快照。
- `acceptance.json`：当前资格承接，source contract为`b6b8da780cf8141b844db782873647b84e9a729b149092697d9234eef77a132b`。

当前主命名空间`qualification/`已指向本次补验与同输入引用证据；旧smoke报告、flags、outputs、partial和原失败状态均未覆盖。`execution_enabled=false`保持不变，等待用户决定是否启动正式开发实验。
