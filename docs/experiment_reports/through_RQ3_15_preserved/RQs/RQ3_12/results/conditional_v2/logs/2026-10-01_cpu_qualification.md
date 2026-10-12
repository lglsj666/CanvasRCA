# RQ3.12 v2 完整 CPU：软件通过，方法资格失败

用户看过例图后授权CPU回归、GPU smoke，均通过后全量。单一主agent恢复资格检查；没有委派、Slurm、训练或模型调用。前述代码/例图暂停已经解除，当前停止来自登记的GPU前方法门槛失败。

## 完整执行与结果

显式build canonical renderer、刷新static、登记原140 exposed-eval身份；八个distinct physical-core preparation workers，source/cloudbed交错，完整准备140例。254张真实PNG逐张DOM/字段/实体/输入hash核对通过，13例比较表空时按既定规则不生成图，保留相同exact文本和病例分母。static AST/接口/bash/TypeScript通过；renderer CPU测试25 passed，10个opt-in browser tests跳过。此跳过不代替新PNG审计：254实际新PNG均走真实浏览器。

`cpu --execute`运行132.843秒；八组方法、参考/当前隔离、真实采样格缺失、稀疏矩阵和atomic commit检查通过。840完整输入全部满足容量，最大21206+8192=29398≤40960；零context exclusion。官方checkpoint/tokenizer/processor28文件SHA与revision核对通过。六个固定例同值evidence/design与先前独立预览完全一致，PNG SHA一致，确认真实重复渲染确定性。

主要AIOPS CV/ET输入token比1.1345221458912604≤1.20，较v1的1.3392393476改善；不是模型输出/总token成本。完整140×6输入均检查，未做更容易的推理子集。

## 失败点与独立核对

| 数据集 | 案例 | 可计算观测列总数 | 合格参考拟合 | 有任意预测的案例 | 全候选有效预测单元 | 满足两个共同预测目标的案例 | 登记竞争案例 |
|---|---:|---:|---:|---:|---:|---:|---:|
| AIOPS-2022 |60|453|88|2|4|0|0|
| AIOPS-2025 |60|445|208|6|12|0|0|
| AegisLab |20|177|527|4|106|3|0|

原资格要求两个AIOPS合计竞争案例≥30、各≥10。当前各0，因此完整CPU report状态failed；这不是CPU断言、容量或token成本失败。Aegis虽有三个可共同比较的案例，其预测分歧仍低于登记阈值，不满足竞争定义。

823个合格参考拟合全部用独立NumPy标准化ridge正规方程核对，最大预测相对差3.5411e−14。全候选profile核对在最多六行显示筛选之前完成：AIOPS连两个共同有效目标都没有，因此不是显示行数或选择器造成失败。主要参考拒绝原因包括变化退化、held-out预测不可靠；通过参考检验的预测还受当前支持域约束。关联拟合的数值正确不等于存在可用的故障解释响应。

改善覆盖与展示使1075/1680条指标可测（v1为497）；这不能建立预注册主研究问题所需的竞争候选比较。CPU regressions passed与method readiness failed分别保存，不生成passed GPU/科学资格标记。

## 保存与边界

机器证据：`qualification/cpu.json`、`cpu_regression_review.json`、`render_cpu_audit.json`、`public_response_diagnostic.json`、`diagnostic_failure.json`、`runtime_boundary_audit.json`。当前源/协议/renderer/bundle snapshot存 `failed_cpu_source_v2.tar.gz`，receipt含原source contract和SHA；v1原失败全部保留。

当前GPU smoke、formal和科学/预算freeze都没有运行，0模型调用。未修改12M/R/L/G、候选、样本数、CV/支持域/共同目标/竞争门槛、模型/评分、病例分母或900次allocation。没有从case标签或模型答案调参。

下一步需要新的版本化参考响应/数据支撑设计。不能用额外模型调用、降阈值、允许无依据外推、选更易病例或把未适用预测画成0来让本次资格通过。当前授权条件尚未满足，不提交GPU smoke或全量。
