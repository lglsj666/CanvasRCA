# 2026-10-01 — RQ3.12 v4 参考适用性修订与完整CPU资格

当前状态：**完整CPU passed；GPU smoke/full pending**。全部数据为原140已暴露eval，未请求新test/训练/Gemma/attention。当前版本rq312_conditional_residual_v4。

v2数学实现正确，但旧12指标不足以建立候选共同预测。v3改为完整公开参考池、共享新增原始操作数，准备暴露了编号/长数字宽度问题；v4聚焦两个共同目标、两个竞争候选、最多6新增原始指标（六臂相同），原12M/R/L/G和完整候选保留。只修改compact内容宽的按实际列数资格，旧12列界限/旧matrix保持。所有未通过准备、配置、源快照保留，0VLM结果反馈。

资格门槛未降低：12/6/3样本、60%真实采样格覆盖、ridge.1、双向CV比≤.8、支持域±1SD、2共同目标/.5差异、合计30/各10、input比≤1.20。新实际结果：A22竞争54/60，A25 50/60，Aegis辅助15/20；没有删不适用病例。140例准备266图，7例空矩阵无PNG回退，8例没有新增操作数。

9组方法回归通过；renderer25tests passed/10旧opt-in浏览器测试跳过，另全部266实际browser DOM/field/PNG哈希审核通过。四图实际目视通过，A25条件图独立重绘字节一致。115068池向量与独立源采样格一致，1120选中拟合用NumPy独立正规方程核对，最大相对差7.542e-13。新增原始操作数在六臂精确相同，text/visual派生表roundtrip通过。

全部840真实processor输入通过，0容量排除；最大21940+8192=30132≤40960。主要input比CV/ET=1.092283565，增加9.23%而非降低9.23%。官方checkpoint/tokenizer/processor28文件hash核对，CPU389.487s。

这是方法适用性/实现/输入资格；不证明MRR、视觉优势、总token成本或解释可信度。当前选最大支持内预测分歧可能对应正常波动，关联池搜索会有偶然相关；没有因果/正常期认证，也不是CIRCA复现。仍要完成18次/600s含启动的真实smoke及逐输出/完整图谱审核，然后按原六臂140全量一次运行。预算范围在协议0V3纠正为RQ3.12全部版本共享900，原用户RQ3.1 cap仍在其RQ；先前RQ调用分别保留。

证据：qualification/cpu.json、independent_selected_audit.json、cpu_stage_completion_audit.json、determinism.json；实验协议当前0V4/0V3。运行代码/协议将在GPU前冻结，后续不根据部分模型结果改变方法。
