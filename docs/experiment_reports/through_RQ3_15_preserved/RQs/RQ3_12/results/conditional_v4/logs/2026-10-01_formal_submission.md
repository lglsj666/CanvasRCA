# 2026-10-01 — RQ3.12 v4 完整实验提交与继续运行确认

已完成参考适用性修订、完整CPU回归/资格、科学/图形/预算审核、冻结、真实GPU smoke及全部实际I/O审核；全量已启动，**未完成**。本次用户停止边界为开启并确认全量。当前版本rq312_conditional_residual_v4，config conditional_residual_v4.json。

## 结果与资格

参考模型仍非因果/故障世界模型；新增原始操作数从同案例公开参考池中选择，原12M/R/L/G/完整候选保留，六臂共同增加最多6原始指标，两共同target/两probe画布。旧v1/v2资格失败和v3/v4准备接口失败均保留，0历史模型调用；没有降原CV/覆盖/支持/竞争/成本阈值。

完整140准备266PNG、840完整token检查0排除、28official文件身份通过，9方法组/25renderer CPU tests及266实际DOM通过；四PNG目视和单例确定性重绘通过。A22竞争54/60、A25 50/60，主要input比1.092283565，max21940+8192=30132≤40960。1120参考fit独立验证差≤7.542e-13，115068池向量时钟/6臂操作数相同核对。CPU389.487s、3例CPU smoke47.835s。

真实GPU smoke18发起/18完成、含启动212.272s≤600，完整图谱/输入/所有18response审查通过；输出107–223tokens，置信15high/3medium。单位、log2/倍率、时序、推理粒度错误已记录，未以准确率判qualification，未声称可信度提升，未根据这些回答修改代码/模型输入或重试。

## 正式运行

140exposed eval×6=840位置；预期811真实调用+29相同输入引用，其中140ET repeats仍真实独立。Formal≤882/所有版本共900含18smoke；保留其他RQ历史消费，预算范围与权威见协议0V3。单一官方本地Qwen BF16/triton/0.75，8192输出/40960上下文、36请求线程、8writers；无Gemma/attention/training/newtest。

提交确认时已保存14原子完成结果，36请求在途，0infra失败；首3完整commit graph独立audit通过。Supervisor PID67677、server67685、runner68101存活，GPU采样99%。Receipt formal/submission.json、logs/formal_supervisor.log及formal/logs/runner.*.log。源archive SHAb5c4458c821b9ea77aded2d6d703af3c7eeb9871ebfb95e561c49100cca9c7e3，主代码94文件归档，3额外间接recipe文件另归档并复核。

## 接手与边界

不要改冻结protocol/code/config、重新准备/重复已完成调用或从部分分数调参。先读formal/phase_complete.qwen3.8-27b.json或supervisor/phase.json和ledger；正常进程继续工作，不另开server。仅真实需要恢复时使用bash RQs/RQ3_12/scripts/local.sh supervise --execute：已有per-call/model commit优先，owned服务结束/异常退出状态在日志。

后台supervisor会完成全部队列、drain writers、写phase marker、关闭其ownedserver，不自动做新实验/训练/调参。整批结束后才检查完整性与原评分、pairedPratt/Holm/组等权、总input+output成本、36例预先hash选定理由审核。CPU/Smoke成功不是MRR/视觉/可信度实验成功，项目performance目标尚待实际完整结果。

新版每arm×dataset18例图/6PNG及完整文本输入已补到Windows原目录05_RQ3.12_v4_参考预测修订，首页入口已添加；它们为真实冻结准备输入，旧图全部保留。
