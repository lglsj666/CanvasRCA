# RQ3.12 — 2026-10-02 完整批次结论

队列840终态；正式811请求/801响应/10超时，29引用，smoke18另计。完整输入/图像/94冻结文件+3补充依赖/801graph与评分审计通过。4模型输出失败零分保留。离线审计operand接口修复不改变运行输入/输出/score，原freeze保留。

不采用COND_VISUAL：AIOPS主要CV−ET Δ+.03842，pH .56706；CV−CT Δ+.03652，pH .56706；CV−OV Δ−.02749，pH .56706。组级未通过，主要对比分母118/115/117，成本CV/ET1.09064。普通OV−OT+.05226是未显著开发线索，不能事后改预选。完整120缺失界限CV−OV[-.03931,-.01431]，本批次方向无法补超时后转正。

104/120有竞争预测，却只有23/120目标变化|A|≥3；精确root目标0、预测行2。公开原12M没有删除，原始root-M覆盖A22 22/A25 19/Aegis13，不能把字面缺失当全部证据缺失。CPU残差启发式主要MRR.05028，不是CIRCA/强数值上界。

注册outcome-blind36例/216位置完整阅读214解释，2超时保留。五轴只对具体claim做有限裁定，未知not_certified保留；至少39条单位/时序/绑定/理由矛盾，单一主agent审核，不是全量幻觉率/校准/隐藏思维链。可信度增益不成立。

详细报告：docs/experiment_reports/RQ3_12_Qwen_Analysis_2026-10-02.md；衍生表/图/verification/manual_reason_review在results/conditional_v4/analysis_reviewed_v1。当前无RQ3.12 GPU运行；下一RQ3.13是新开发假设，重新资格，不覆盖历史结果。

---
以下为历史实施与提交记录，完成状态由上述整批报告覆盖。

# 当前进展补充 — v4参考适用性修订

用户授权解决参考预测适用性并启动全量。v4只使用同案例既有公开数据，从完整参考池中选受验证、支持内、有分歧的两个共同目标及其anchors，最多6新增原始指标在六臂相同，原12M/R/L/G/所有候选保留。原资格阈值未降低。完整CPU通过（A22/A25竞争54/50，主要input比1.092284，840输入零排除），GPU smoke18/18及完整I/O审查通过（含启动212.272s）。全量140×6已确认持续运行，提交时14原子commit/36在途，首3完整图谱复核通过，尚无整批模型性能结论；旧v1/v2失败及v3/v4准备接口失败均保留。本轮smoke消费18，不重置900 allocation。最新资格状态以conditional_v4/qualification和日志为准。

# exp_conditional_residual findings

2026-10-01。当前版本 `rq312_conditional_residual_v2`；以下 v1 CPU 结果保留为历史失败证据。

当前状态：**v2完整CPU功能回归、容量和成本通过，但方法资格失败；GPU smoke和全量未运行**。两个AIOPS有效竞争案例仍各0/60，低于登记门槛合计30/各10。没有新增模型调用、VLM输出或RCA性能结果。具体证据为 [v2 CPU记录](../../../docs/experiment_reports/through_RQ3_15_preserved/RQs/RQ3_12/results/conditional_v2/logs/2026-10-01_cpu_qualification.md)。

## v2 完整 CPU 结果

140例重新准备完成，254张实际PNG通过DOM、字段/实体绑定与SHA核对；13例无可计算表，回退原始exact文本，病例分母没有缩减。八组方法/隔离/commit检查通过，renderer CPU回归25 passed/10个opt-in browser测试skipped；实际254图均走真实浏览器审计。六张固定例图与独立预览的同输入PNG字节完全相同。

840完整输入均满足上下文上限，最大21206+8192=29398≤40960，零容量排除。官方checkpoint/tokenizer/processor共28个文件身份核对通过。主要AIOPS范围CV/ET输入token比 **1.134522**，已低于1.20；这只是输入成本门槛，不是实测输出/总成本或模型效果。

观测指标1075/1680条可计算，较v1的497条增加；参考期合格拟合823个（AIOPS2022 88、AIOPS2025 208、Aegis527），全部用独立NumPy标准化ridge正规方程核对一致。两个AIOPS分别只有2/6个案例有任何有效预测，全候选有效预测单元仅4/12，**任何候选对都没有两个共同有效预测目标**，不是最多六行显示选择导致。Aegis有3个案例存在共同目标候选对，但没有达到登记的预测分歧阈值。

当前不能通过CPU方法readiness；修复采样与图形仍没有建立可用于主研究问题的竞争候选比较。未降低样本、CV、支持域、共同目标数或30/10门槛，未据缺失选更容易的队列，未调用模型试分数。v2失败源码/bundle和全部准备/记录另存，按登记的GPU前停止规则保留失败。下一步需要版本化修订参考响应模型或数据支撑，不能把软件回归通过说成方法资格通过。

历史预览阶段：用户只追加“每个arm×数据集例图”请求时，仅渲染三个固定案例的六张v2 PNG，未建立canonical准备或GPU资格。三个案例观测列7/9/12，预测行0/1/0，没有据此宣称适用性/成本通过。DOM/目视和单例确定性PNG通过；预览发现的最小高度/SVG尾部空间问题已修复，失败尝试保留。随后用户授权本节所列完整CPU资格检查。

v2 从冻结 public context 所绑定的 canonical metrics 时间戳提取真实采样支持，不再把均匀图格中未安排采样的位置当作缺测；真实采样格的缺失值仍计入覆盖率分母。原始 exact12M/R/L/G 事实、候选全集和模型/评分/调用门槛保留。不可计算、锚点自身和支持域之外的派生比较不展示；OBS 只展示 A；空候选行和无观测列删除；整个表为空时不生成 PNG，使用原始 exact 文本。两种派生表示共享同一份稀疏比较数据。

这修正了采样支持与展示规则，但**尚不能说明两个 AIOPS 已达到有效竞争候选或 token 成本门槛**。之后须重新构建 renderer、准备并验证全队列，不能复用 v1 的 CPU 成功或旧 PNG 作为 v2 资格。详见[修订协议](../descriptions/RQ3_12_experiments.md)及[本次静态修改记录](../../../docs/experiment_reports/through_RQ3_15_preserved/RQs/RQ3_12/results/conditional_v2/logs/2026-10-01_static_repair.md)。

## v1 历史 CPU 结果

状态：**CPU regression passed；full method readiness failed；GPU smoke / formal not run**。没有新增模型调用、VLM输出、MRR或可信度增益结果。

140例、280张真实PNG准备完成，六组响应/隔离/数值/commit检查及25个renderer CPU tests通过，10个opt-in browser tests跳过。实际280张图的DOM审计通过，重复渲染PNG字节一致。840个完整输入均装入上下文；当前模型、tokenizer和processor身份核对通过。三例smoke输入仅完成CPU检查，不能称GPU smoke成功。

两个AIOPS各0个有效竞争候选案例，低于合计30/各10门槛；COND_VISUAL相对ET的主要范围输入token比1.339239，超过1.20。全候选也无两个共同有效预测目标的竞争对，105个通过参考检验的拟合经独立NumPy核对一致。故不能将此结果当作实现回归通过后的有效诊断方法。

用户指出的Aegis图每条指标参考32格只有16个有效格；60%规则导致全观测未知。均匀64格可能比真实采样更细，不能将这种图格缺失直接称遥测采集故障。问号与规则一致，但整图不具备可用比较信息。

遵守[协议](../descriptions/RQ3_12_experiments.md)的GPU前失败停止规则，保留全部案例/门槛/失败证据，未启动GPU。用户随后授权版本化修改，并要求代码改完就停下；v1 源码和构建包已单独保存。详细[CPU诊断](../../../docs/experiment_reports/through_RQ3_15_preserved/RQs/RQ3_12/results/conditional_v1/logs/2026-10-01_cpu_qualification.md)及机器记录为 v1 历史状态依据。
