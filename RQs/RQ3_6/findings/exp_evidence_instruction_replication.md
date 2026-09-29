# exp_evidence_instruction_replication

状态：2026-09-26阶段A正式check120及完整离线分析完成；B–D未启动。正式新增2640次，累计调用10899次；资格成绩仍不作效果结论。

完整报告：[RQ3.6阶段A分析](../../../docs/experiment_reports/RQ3_6_Stage_A_Analysis_2026-09-26.md)。七张图、样本级表、配对检验、分母敏感性与轨迹示例在同名assets目录。复算入口：`RQs/RQ3_6/scripts/analysis/report_stage_a.py`，不发模型请求、不改原分数。

主要发现（数据集等权macro）：Qwen共同97例，W_NO_K为.4867、TPV为.4469；Gemma120例，E_S_D_P为.4290、E_P_D_P为.3182。相应条件增益未通过完整探索性Holm校正，不能宣布统一冠军。注册证据/指令与G/V主效应、交互均未显著。Qwen公共P接口相对原生T的pooled ΔMRR=.1017、Holm p=.0055，事件组p=.0097；这属于接口整包校准，而非视觉或新选择器贡献。

S包增加根因关联M/R/L记录，但某些内存等机制信号仍被其他指标替换；两模型呈pod获益/node受损的描述性取舍，事后组间检验尚未获得稳健确认。W在Qwen有6修复/1破坏，在Gemma2修复/5破坏；动态宿主症状也可能使pod根因被错归到node，不应只过滤静态配置。公共reason、正确排名与可核验事实分别分析。

完整性：2640终态，Qwen24请求超时涉及23例；Gemma无超时。13份未知/重复候选输出按原契约零分。实验×模型共同排除后的Qwen分母为32/35/30，Gemma40/40/40；提供全120系统效用和局部格子配对敏感性，不把超时当模型质量。未解释缺失、得分不一致与保存artifact不一致均为0。全部结果来自重复暴露的check集，非新test。

后续建议：按原计划收窄B、固定P0和D_P，专门检验W动态锚点、范围绑定及同事实图文承载；不将事后最佳组合或真实根因类型用作路由。只是分析建议，未改科学协议、未授权或启动B。

## 资格检查历史

CPU覆盖11条件/3病例/两模型，共66请求；GPU覆盖两新指令条件及W_NO_K，共18/18完成，原窗口558.820秒。修复后处理image_hashes接口并离线恢复9个已保存回答，无额外调用。人工审阅见 [manual_review](../results/replication_v1/manual_review.md)，检查记录见 [qualification](../../../docs/issues/RQ3_6_qualification_2026-09-26.md)。

协议见 ../descriptions/RQ3_6_experiments.md；资格检查与正式来源 ../results/replication_v1/。历史资格结论不改，正式效果以上述报告为准。
