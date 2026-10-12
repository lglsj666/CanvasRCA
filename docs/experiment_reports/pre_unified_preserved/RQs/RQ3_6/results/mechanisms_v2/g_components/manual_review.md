# 人工资格检查

两模型18/18完成；自动review核对原prompt/PNG identity与CPU结果、raw response、conversation和cost完整。逐份阅读18个公开reason及conversation结构，查看实际NO_CALLS PNG并与FULL CPU图比较：边删除、节点保留，异常字段仍在可见ledger，非G证据/候选保留。纯文本STRUCTURE只删除指定G字段，不去除M/R/L的独立异常事实。未发现基础设施、字段丢失、私有标注或错误图绑定。

模型行为：个别reason捏造输入未给出的调用/部署关系，把5位pod称node，把log-fold误读为倍率。这些是待分析的模型结果，不是本轮实现故障，不改答案、不重试、不据此选arm。smoke不作为MRR证据。
