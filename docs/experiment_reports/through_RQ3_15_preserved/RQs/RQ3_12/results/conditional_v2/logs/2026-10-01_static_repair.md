# RQ3.12 v2：采样支持与无信息展示修订，停在代码边界

日期：2026-10-01。版本 `rq312_conditional_residual_v2`。当前任务边界来自用户最新指令：“代码改完之后就先停下”。单一主 agent 完成，无委派。

## 原因与改动

用户指出 v1 dashboard 几乎全是问号，并要求删除无法提供诊断信息的内容。v1 完整 CPU 资格失败：两个 AIOPS 各无有效竞争候选，CV/ET 输入比 1.339239，超过 1.20 门槛；没有启动 GPU。这些失败和全部旧图保留，不用 v2 源码重写旧结果。

旧覆盖率把均匀 64 格视作每格都应有采样；所示 Aegis 指标每条参考期只有 16/32 个有效格，未采样画布格与真正缺测混合。v2 新增只读公共采样支持 adapter：核对冻结 public context 和 canonical metric source 身份，只读取 timestamp 列，将实际源采样投射到相同图格。真实采样格中的缺失值仍计入分母；不依某条指标的非空值构造支持、不插值，原有样本数量、60% 覆盖率、参考时间折、拟合与支持域阈值保留。该支持定义仍需真实输入验证。

新比较对象只保留可计算的观测列和至少一个有效预测的候选行。未知、条件锚点自身和支持域外的单元不绘制数值、问号、斜线、状态或坐标条；OBS 只显示 A。新增 `diagnostic.compact`，按实际有效行数计算高度。整张比较表为空时不生成 PNG 或空附录，回退相同 exact 原始文本。候选全集、所有原始 exact12M/R/L/G、完整病例分母保留。显示稀疏表不等于已证明预测适用性或 RCA 收益。

文本/视觉使用同一份稀疏矩阵，稀疏列位置显式绑定；重复测量对象和无用参数不再占逐例附录，保留单位、reference/scale、公共 clock/support 与预测 paired bins。原始精确遥测不删改。无图案例未来须独立统计视觉机制不可用，不能算成功读图。

## 版本和验证边界

v1 源码、协议、renderer 和原构建包另存 `../conditional_v1/qualification/failed_cpu_source_v1.tar.gz`（相对于本版本 results 目录），receipt 保留原 source contract。v1 失败资格、配置、PNG 和调用账目不改写。新配置使用独立 `conditional_v2` preparation/results；900 次 allocation 和 18 次/600 秒 smoke 总限制继承，旧消费不清零。本实验目前模型调用为 0。

执行 `bash RQs/RQ3_12/scripts/local.sh static`：Python AST/代码编译、JSON 配置、bash 语法、项目模块接口静态连接、纯公共 compiler 依赖检查、组件注册、TypeScript `--noEmit`。结果见 [static.json](../../../../../../../../RQs/RQ3_12/results/conditional_v2/qualification/static.json)。另做 `git diff --check`。新增合成用例仅写入源码，**没有执行**。

本次未加载案例、parquet、tokenizer 或模型，未执行 v2 CPU 回归、准备、构建 renderer、浏览器/PNG、GPU smoke 或全量实验；旧构建包仍属 v1，禁止作为新版 renderer 资格。当前改动已停在代码和静态检查完成处。

之后继续时须先显式 renderer build，再刷新静态记录、登记/准备并重新验证完整 140 例及 smoke 输入、实际 PNG/DOM、数值/隔离/容量、竞争覆盖和真实 token 成本，以及科学与累计预算门禁；之后才可能进入 GPU。没有放宽竞争覆盖 30/各 AIOPS 10 或成本比 1.20 门槛，后续仍可能资格失败。
