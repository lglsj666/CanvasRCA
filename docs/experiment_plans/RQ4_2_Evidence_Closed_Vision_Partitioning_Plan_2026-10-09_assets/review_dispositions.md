# 四轮独立盲审及处理记录

此前设计阶段使用 gpt-6-astra / xhigh，先提供文献和公开真实评审材料，再提供方案和四份完整实验报告；不向后继评审透露前任评分。当前实施不追加评审或代理。

公开评审阅读使用作者保存的真实评审导出：[COLM 2024](https://cseweb.ucsd.edu/~jmcauley/pdfs/colm24.pdf)、[ACL ARR](https://ofey.me/assets/review/acl24_yang.html)。这不是声称已绕过OpenReview页面访问限制、读到完整实时论坛。

## 处理清单（总结，不冒充逐字原文）

| 轮次 | 反馈 | 处理 |
|---|---|---|
| 1 | 排版/JOIN新意弱；需要强基线、真实干预、完整成本；设计/新意/就绪度6/4/3 | 不继续泛化排版搜索；保留完整历史结果；区分冷路径和在线时间 |
| 2 | 预算扩大不能补救弱问题；优先实体、单位和阶段绑定；7/3/4 | 后续改为编码器连接实验；用户拒绝重复文本调用，历史强文本直接复用 |
| 3 | 编码器方向更有意义；分组先例明确；7/5/3 | 固定27块、23分组+4全局；严格等容量/真实背景；定义优化、别名、SHAM强度；独立QA |
| 4 | 可冻结为有界研究，无需增臂/重跑/新评审，运行可行性仍未知 | 单一18/600smoke；累计5%背景改组；分离生成/评分身份；正式连续冷时延；每数据集同批病例联合准入 |

第四轮没有给数值终评分，不自行生成“高分”。它明确指出完整证据可能放不下、分组可能不足、冻结特征可能退化或节省不抵预处理，必须服从停止规则。

## 原文保存范围

本轮工具仍可返回第2/3/4评审代理的最终消息，分别逐字保存为 [reviewer_2_final.md](reviewer_2_final.md)、[reviewer_3_final.md](reviewer_3_final.md)、[reviewer_4_final.md](reviewer_4_final.md)。第2文件是最后一次策略补充，不是先前带分数的完整评审。第1代理已不在可读取列表中；上下文只有摘要，不能据此伪造完整逐字原文。下方另存第4轮关键摘录；这些附件不是四轮所有消息的完整转录。历史建议目录中已有评审文件保持不变。

> The revised proposal is ready to freeze as a bounded next study. I find no remaining design issue that requires another arm, baseline rerun, or review round. Implementation and runtime qualification remain unproven; this assessment authorizes neither.

> The remaining risks are empirical: all facts may not fit at the required readability, the graph may fail the manipulation gate, frozen features may degrade after 23 partitioned blocks, or encoder savings may not offset preprocessing. The prescribed stop rules handle these risks without expanding the experiment.

> Achieving roughly 0.505 MRR remains an ambitious objective unsupported by existing visual results; a well-controlled negative result would still answer a genuinely new question.

以上摘自第4轮代理最终消息（实施时再次通过代理状态接口读取），不是从论文或第三方网页抄录的评审。
