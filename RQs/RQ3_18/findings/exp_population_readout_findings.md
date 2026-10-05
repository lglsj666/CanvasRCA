# RQ3.18 — 总体耗时读数与视觉比较

当前状态：**2026-10-05 用户授权恢复，已从1193/2420终态位置继续；新服务、恢复队列及首批新增原子结果已核验，后台运行中。** GPU smoke仍为原18/18通过；首次正式启动于2026-10-04 23:54:09 America/Toronto。预选READOUT_PROFILE与原11臂设计/输入/统计/预算保持不变。

原静态、完整220例CPU和实际例图资格通过：适用60/60、55/60、96/100；9例完整文本回退。最大input+8192=35003；每集平均input/T≤1.071365。35项renderer回归通过。旧六臂计划、代码和测试已按明确用户要求删除，其他历史保留。

本次只修改执行授权门禁。原197文件CPU冻结保留，AST与196文件精确相等证明科学资格适用；新源合同a71275854a446e551776a8c134080620f69773150e12aaf18065d739ec43a49e，单独冻结于activation_v1。18调用GPU smoke用时246.32秒，含逐份审查342.96秒；全部输入/PNG/评分/记账核验，零基础设施错误、超时、截断、无效五候选。模型解释错误记录保留，不按正确率调参。

正式2420位置预期2357真实请求+63引用，总尝试预算2500（含smoke18、正式及恢复最多2482）。所有臂固定哈希交错，独立重复新调用；无attention/训练。完整结果尚未产生，不能据smoke宣布MRR或解释可信度提升。

- [登记计划](../../../docs/experiment_plans/RQ3_18_Population_Readout_Plan_2026-10-04.md)
- [CPU资格报告（历史停止状态）](../results/population_readout_v1/qualification/report.md)
- [GPU及正式执行记录](../results/population_readout_v1/logs/2026-10-04_gpu_and_formal_execution.md)
- [每臂输入与例图](../preparation/population_readout_v1/examples/index.html)

启动核验快照（2026-10-04T23:58:42.057848-04:00）：16份新原子完成记录已审核，账本{'complete': 16, 'started': 36}，无基础设施错误。监督进程PID258591。详见 [启动核验](../results/population_readout_v1/formal/launch_verification.json)。

暂停/恢复记录：10月5日01:52收到安全暂停信号后，已发请求排空，三个自有进程退出。暂停终态为1179个done（1137真实完成＋42引用）、14个原请求超时、1227个pending，未遗留started。10月5日上午用户恢复授权后，启动监督进程PID2517，服务/runner为2551/3230；剩余队列1206真实请求＋21引用。跳过所有已提交终态，保留原超时和模型无效回答，不重跑smoke、不重置预算、不批量复验历史输入。实际服务显存比例0.75、并发36，资格合同保持一致。最新恢复核验见 [恢复收据](../results/population_readout_v1/formal/resume_verification_20261005.json)，动态进度以当前账本和flags为准；尚无完整效果结论。
