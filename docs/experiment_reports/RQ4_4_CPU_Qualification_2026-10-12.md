# RQ4.4 CPU 资格报告 — 2026-10-12

状态：静态、完整 CPU、实际例图及离线运行回归通过。初次 CPU 资格时新增模型调用为 0；后续 18/18 GPU smoke 已通过，见 [GPU 部署报告](RQ4_4_GPU_Qualification_2026-10-12.md)。

| 数据集 | 通过病例 | SOURCE 平均输入 token | 高清卡片数 |
|---|---:|---:|---:|
| AIOPS-2022 | 60/60 | 14028.52 | 4–5 |
| AIOPS-2025 | 60/60 | 13388.47 | 3–5 |
| AegisLab | 100/100 | 14079.87 | 3–5 |

全部660个主输入使用实际 processor；原概览PNG、grid及U保留索引不变；整卡DOM文本与绑定次数相同，SOURCE/HASH局部图处理后字号≥18px、线条≥1.5px；REPEAT仅放大processor处理后的概览像素，尺寸和卡片位置与SOURCE相同。输入预算、40960容量和预留8192均通过。

30例机制子集与额外固定smoke病例完成QA/隔离卡片QA/顺序输入。独立QA没有RCA排序指令，答案只在审核侧。最终16项单元回归及2项共享renderer注册/默认操作回归通过；三个固定病例18个真实输入的CPU MRoPE/gather独立核对与主臂确定性冷重绘通过。CPU最多8个不同物理核，网络及CUDA在worker中关闭，无模型服务。

实际打开三个数据集三臂九图、最长操作名、最密/最大卡片与孤立QA图。密集拓扑原有交叉边被完整保留；不声称图形已被模型正确读取。SOURCE每次恢复局部细节，不能将其图像token预算等同于编码加速。

来源分类从原公共记录的region获取；比较卡片不能统一当作Trace。候选目录不被选作“高清文字截图”，仍完整保留在原概览。选择优先不同模态、实体，同轮按恢复字符/面积成本或固定哈希；不读根因或历史输出选卡。

运行代码支持原子完成、断电后从持久回答恢复、独立重复与精确引用区分、暂停排空；正常完成后输出统计及保留审计。预处理8 workers，GPU并发8，RAM最多16个准备/就绪包，另有8在途；模型BF16，vLLM显存利用率0.8。

Attention采用已兼容的第3层最后prompt query和首个decode query；没有采集最终排名字段查询，不声称覆盖全过程。单记录≤64KiB、每万次含映射≤1GB。运行完成后保留完整输入输出/评分/实际attention，去重及清理无用中间HTML，按每真实完成调用≤2500000 bytes审计。

[计划](../experiment_plans/RQ4_4_Source_Bound_Multiscale_Plan_2026-10-12.md) · [例图库](../../RQs/RQ4_4/results/source_views_v1/examples/index.html) · [完整CPU凭据](../../RQs/RQ4_4/results/source_views_v1/qualification/cpu_complete.json)。历史源码、组件默认行为与Codex.md未修改。
