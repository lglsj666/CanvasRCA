from pathlib import Path
import json,csv
P=Path(__file__).resolve().parent;D=P.parents[1];ROOT=P.parents[3]
s=json.loads((P/'analysis.json').read_text());A={ (x['arm'],x['dataset']):x for x in s['aggregates']};H={(x['arm'],x['dataset']):x for x in s['historical']}
order=['H_MARGINAL','H_TOPOLOGY','H_TOPO_MARGINAL','V_DOMAIN_FULL','V_SOURCE_UNIFORM','V_CONTEXT_FILL'];ds=['aiops2022','aiops2025','aegislab'];names={'aiops2022':'AIOPS-2022','aiops2025':'AIOPS-2025','aegislab':'AegisLab'}
def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,r))+' |' for r in rows])
def f(v):return f'{v:.4f}'
def pct(v):return f'{v*100:.2f}%'
def cost(v):return f'{v:,.1f}'
def rel(v,b):return f'{100*(v/b-1):+.2f}%'
parts=[]
def add(x):parts.append(x.strip())
add('''# RQ4.5 完整实验分析：来源独占的混合表示与空间覆盖剪枝

日期：2026-10-19。状态：**本地正式实验完成，1,560/1,560 个逻辑位置提交；本报告使用完整数据，新增模型调用为 0。**

本轮最有价值的结果是：**H_MARGINAL 在不把同一耗时配对信息同时放入文本和图像的条件下，达到标准 MRR 0.4912、平均总 token 比历史强文本少 5.97%。** 这是一个值得保留的性能—成本折中，但仍未超过历史 MARGINAL_FIVE 的 0.5054，且总体收益来自 AegisLab，两个 AIOPS 数据集都有下降。

两个预选方法均未达到原定推进目标：H_TOPO_MARGINAL 为 0.4736；V_SOURCE_UNIFORM 为 0.3105。新纯视觉最高 V_DOMAIN_FULL 为 0.3302，仍低于历史 A_UNIFORM_E50 的 0.3517。**不自动将事后最高分臂改成预选成功方法；同时承认独占边际图已经取得约 0.49、成本下降的工程结果。**

## 1. 可以带走的十项发现

1. **耗时配对可以独占地交给图像，并维持接近 0.50 的整体表现。** H_MARGINAL 不依赖那组配对样本及统计在文本里再重复一遍；但它仍有大量其他 M/R/L/G 文本，绝不是纯视觉成绩。
2. **整体均值掩盖了数据集方向差异。** 相对历史 T_FULL，H_MARGINAL 在 AegisLab 增加 0.0423，在 AIOPS-2022/2025 分别下降 0.0189/0.0275。
3. **拓扑与边际图组合并未普遍更好。** 组合对单边际图整体下降 0.0176；AIOPS-2022 改善，而 AegisLab 下降。不能将单个数据集的组合收益推广到总体。
4. **本轮拓扑图的精确绑定读取很弱。** 58 道可适用关系题中，保留拓扑文本的 H_MARGINAL 宽容评分答对 51 道；H_TOPOLOGY 为 0 道，组合为 1 道。这里测的是指定实体的完整一跳关系集合，不等价于“模型完全不理解拓扑”。
5. **来源内空间覆盖没有改进历史均匀剪枝。** V_SOURCE_UNIFORM 的 token 数与 U 相同，MRR 下降 0.0412；不能用覆盖代理指标替代诊断排名。
6. **补回全部登记证据 token、或者补充邻近上下文，都不是现成的改进。** 两者比历史 U 贵约 10.3%，新结果却更低。历史比较存在运行时期差异；同期两种补充方式之间也未建立优势。
7. **纯视觉损失包含输出接口错误，但远不止这些。** 新纯视觉各有 13–14/220 个无效回答；宽容评分改善 0.0117–0.0242，仍远低于 hybrid。
8. **QA 接近零有复合原因。** 单位别名、实体/字段错位、把坐标刻度当基线、关系端点不全同时存在。不能把联合精确匹配零分直接翻译成“没有读对任何东西”。
9. **排名正确与解释可靠是两条轴。** 实际回答里既有 QA 较好却排名错误，也有根因排第一但理由中的单位、实体、倍数或根因叙述错误；只看相关系数会遗漏这些情况。
10. **本地运行和保留机制可用。** 正式批次约 148.86 分钟，10.33 次实际调用/分钟；无基础设施缺失、无 KV 抢占，保留约 3.188 GB。该速度属于本地 Blackwell，不能套用到 Nibi H100。

![整体性能与成本](artifacts/RQ4_5_2026-10-19/performance_cost.png)

图中 H-M/H-T/H-TM 分别为三个 hybrid；V-D/V-S/V-C 为三个纯视觉。菱形带星号为复用的历史结果，不是同期重新生成的对照。

## 2. 实际运行范围与输入定义

全部条件使用同一批已暴露开发病例：AIOPS-2022 60、AIOPS-2025 60、AegisLab 100，共 220 例，合并成 193 个数据集内事件组。它不是独立确认集。候选、五个不同候选的输出要求及中央 scorer 保持登记口径。

| 模块 | 逻辑位置 | 用途 |
| --- | ---: | --- |
| 六臂主矩阵 | 1,320 | 每臂 220，所有 RCA 单次调用 |
| 六臂独立 QA | 180 | 固定 30 例，每数据集 10 例；答案不传给 RCA |
| 两预选臂独立重复 | 60 | 同输入重新生成，非结果引用 |
| 正式合计 | **1,560** | **1,538 次实际调用 + 22 个精确引用** |
| 本地 GPU smoke | 18 | 不进入正式性能分母 |

本地完成账本共 1,556 次实际调用。先前 Nibi 的 smoke/失败尝试属于另一个账本，不混入本地性能；在本地分支建立时记录了 42 次远程尝试（10 完成、26 基础设施失败、6 中断）。本报告没有重新查询远程队列，因此不把该历史快照称为当前跨机器调用总数。

运行模型为本地 Qwen3.8-27B、BF16、vLLM，沿用 RQ4.4 的 Blackwell 原生后端；实际日志确认 FlashAttention 2。Context 40,960、输出上限 8,192、GPU 并发 8、8 个独立物理核 CPU worker、显存利用率 0.8。正式输入提前完成 CPU 准备，运行阶段加载已资格化文件。冻结指纹：

`d2299620a4c36294113dcced4e222b76e50e85b378ae55c41678c2cab0e55dac`

### 2.1 六个臂分别改变什么

| Arm | 实际模型输入与区别 |
| --- | --- |
| H_MARGINAL | 完整请求配对来源及其样本/统计在新 complete-marginal 图中；其余原诊断事实保留文本 |
| H_TOPOLOGY | 公共调用、部署拓扑在节点—有向箭头图中；其余事实包括配对保留文本 |
| **H_TOPO_MARGINAL（预选 hybrid）** | 两类来源均转入图像；复用单独两臂的同一图像内容 |
| V_DOMAIN_FULL | 历史 U 原 PNG，保留全部登记锚点 A 与可选证据 E；登记域外位置不进入语言模型 |
| **V_SOURCE_UNIFORM（预选纯视觉）** | 同 PNG、同 A；按来源内空间覆盖选择 ceil(size(E)/2)，数量与 U 相同 |
| V_CONTEXT_FILL | 同 PNG，从历史 U 集合开始补邻近上下文，保留总数与 V_DOMAIN_FULL 相同 |

所有视觉 token 操作发生在完整视觉编码及 merger 之后。因而“语言模型收到较少视觉 token”不等于“跳过了全部原图的视觉编码”。Hybrid 也用完整登记 A∪E，并非保留整张画布每个位置；本轮没有在 hybrid 额外施加 E50。

“独占”指同一来源及其派生诊断事实不跨模态重复；必要实体/单位/阶段标签可以重复关联。它不意味着完全消除文本内部所有历史重复。完整性指冻结证据集合，不是原始遥测库的全部记录。用户授权过跨方法信息可不同，因此跨 hybrid/纯视觉的差距评价整套方法，不能全部归于模态。

**分类以真实数据载荷为准：H_TOPOLOGY 与 H_TOPO_MARGINAL 都是 hybrid，拓扑实际在图像中，未因为旧说明残留而在文本中保留一份拓扑。** 两者的 440 个主矩阵请求及 60 个 QA 请求仍有一句历史泛化说明 `All original telemetry, additional operands, logs, relations and candidates remain in text.`，与新图像说明不一致。这是次要接口措辞限制，行为影响未单独测量；不将它当作退化的已知原因，不据此否定已完成结果或改变方法分类。

另一个已登记改动是合并静态任务/阅读规则，每例 hybrid 减少 522 个 token。这不是诊断事实删除，但不是视觉压缩独有收益；后文明确分开解释。

### 2.2 数据适用性与回退
''')
add(table(['数据集','病例','有效配对','有效拓扑','两者皆无'],[[names[x['dataset']],x['n'],x['pair'],x['topology'],x['empty_both']] for x in s['applicability']]))
add('''9 个无合格配对病例中，H_MARGINAL 与组合按登记回退为 H_TOPOLOGY 的相同输入；其中 4 个 AIOPS-2025 病例连公共拓扑也没有，三种 hybrid 均使用完整剩余文本、零图像。它们仍在主分母中，不能把这 4 例称作实际有图输入。22 个引用来自主矩阵的 18 个以及 QA 的 4 个；独立重复始终新调用。

211 个配对适用病例上，H_MARGINAL/H_TOPOLOGY/组合的 MRR 分别为 0.5023/0.4689/0.4840；9 个回退病例三者均为 0.2315。**0.5023 只是事后分层数字，不能替换主结果 0.4912。**

## 3. 完整性能

MRR 使用首个可接受候选的倒数排名；AC@k 表示前 k 个命中。AVG@k 是 AC@1…AC@k 的平均。标准评分对候选未知、重复或格式非法整答计零；宽容评分仅对已有 JSON 排名做登记的类型前缀/空白处理，未知及重复候选在原位置仍是未命中，不补候选、不移动排名。

整体是 220 例病例加权均值，AegisLab 占 100/220；宏平均另外给出，按三个数据集等权。
''')
add(table(['Arm','标准 MRR','宽容 MRR','AC@1','AC@3','AC@5','AVG@3','AVG@5','无效'],[[a,f(A[a,'all']['standard_mrr']),f(A[a,'all']['tolerant_mrr']),*[pct(A[a,'all'][k]) for k in ['ac@1','ac@3','ac@5','avg@3','avg@5']],A[a,'all']['invalid']] for a in order]))
add(table(['历史参照（220例，未重跑）','标准 MRR','AC@1','AC@3','AC@5','总 token/例'],[[a,f(H[a,'all']['mrr']),*[pct(H[a,'all'][k]) for k in ['ac@1','ac@3','ac@5']],cost(H[a,'all']['total'])] for a in ['T_FULL','MARGINAL_FIVE','A_UNIFORM_E50']]))
add('历史参照的当前表只使用原登记标准分数；不拿新宽容分数直接对比历史标准分数而声称超过历史方法。旧 MARGINAL_FIVE 将完整配对文本和边际图重复呈现，本轮 H_MARGINAL 是来源独占移交，二者并非同一方法的重跑。')
add(table(['Arm','AIOPS-2022 MRR','AIOPS-2025 MRR','AegisLab MRR','三数据集宏 MRR'],[[a,*[f(A[a,d]['standard_mrr']) for d in ds],f(sum(A[a,d]['standard_mrr'] for d in ds)/3)] for a in order]+[[a,*[f(H[a,d]['mrr']) for d in ds],f(sum(H[a,d]['mrr'] for d in ds)/3)] for a in ['T_FULL','MARGINAL_FIVE','A_UNIFORM_E50']]))
add('''![逐数据集成绩及相对历史文本的差值](artifacts/RQ4_5_2026-10-19/dataset_results.png)

H_MARGINAL 的整体 MRR 比历史文本高 0.0066，但三数据集宏 MRR 为 0.4566，略低于 T_FULL 的 0.4579。其 AC@5 在 AIOPS-2022 从 50.00% 降至 45.00%，在 AIOPS-2025 从 51.67% 升至 53.33%，在 AegisLab 从 80.00% 升至 87.00%。不能把病例加权的小幅提升解释成跨数据集稳定提升。

组合相对 H_MARGINAL 在 AIOPS-2022 为 **+0.0656**，AIOPS-2025 为 **−0.0128**，AegisLab 为 **−0.0703**。这说明增加拓扑独占移交改变了错误结构，整体不支持“更多视觉来源自然相加”。AIOPS-2022 的正向信号值得留在适用边界中，尚不足以登记一个按数据集挑赢家的可部署路由。

### 3.1 逐数据集全部排名指标
''')
for d in ds:
 add('#### '+names[d])
 add(table(['Arm','标准/宽容 MRR','AC@1','AC@3','AC@5','AVG@3','AVG@5'],[[a,f(A[a,d]['standard_mrr'])+' / '+f(A[a,d]['tolerant_mrr']),*[pct(A[a,d][k]) for k in ['ac@1','ac@3','ac@5','avg@3','avg@5']]] for a in order]))
add('''实验自动汇总还输出 Precision@1=AC@1、Precision@3=AC@3/3；这里沿用其登记的派生定义，**不将后者解释为多可接受标签场景下逐项计算的集合 precision**。例如整体 H_MARGINAL 的这两列为 0.4000/0.1833，组合为 0.3727/0.1818，V_SOURCE_UNIFORM 为 0.1955/0.1303。全部原始指标及定义保存在附件。

## 4. 成本与速度：省 token，不等于相同比例加速

下面的“输入”是实际送入语言模型的文本/模板/边界 token 加保留视觉 token；“原图 token”是剪枝前 merger 后数量，不能再次加到输入上。全部实际图像仍经过视觉编码。引用请求按逻辑部署成本计入均值，真实研究支出另按实际调用计数。
''')
add(table(['Arm','文本/边界','原图 token','保留视觉','输出','实际总 token','对 T_FULL','对 U'],[[a,cost(A[a,'all']['text_tokens']),cost(A[a,'all']['image_original']),cost(A[a,'all']['image_retained']),cost(A[a,'all']['output_tokens']),cost(A[a,'all']['total_tokens']),rel(A[a,'all']['total_tokens'],H['T_FULL','all']['total']),rel(A[a,'all']['total_tokens'],H['A_UNIFORM_E50','all']['total'])] for a in order]))
add(table(['数据集','Arm','总 token/例','相对 T_FULL','相对 MARGINAL_FIVE'],[[names[d],a,cost(A[a,d]['total_tokens']),rel(A[a,d]['total_tokens'],H['T_FULL',d]['total']),rel(A[a,d]['total_tokens'],H['MARGINAL_FIVE',d]['total'])] for d in ds for a in order[:3]]))
add('''H_MARGINAL 对 T_FULL 三数据集均省 token，整体省 1,328.0 token/例（5.97%），对 MARGINAL_FIVE 省约 9.56%。组合省 7.64%，但 MRR 更低；所以省得最多不等于最佳折中。H_TOPOLOGY/AegisLab 仅省约 0.86%，没有达到“至少 10%”的目标。

522-token 静态说明合并约占 H_MARGINAL 整体净节省的 **39.3%**。将这 522 个 token 加回、只做输入记账敏感性估算，其总成本相对 T_FULL 的下降约为 **3.62%**；这不是重新生成后的成本或排名结果。文本基线也可能使用相同静态规则优化，因此不能把全部 5.97% 宣称为图像独有降本。

纯视觉输入很小，但三个新臂仍需编码平均 16,251.6 个原图位置。A 平均 4,614.0、E 平均 1,217.5；U/V_SOURCE_UNIFORM 保留平均 5,223.0，约 **88.3% 保留名额已由 A 占据**。因此“保留一半 E”绝不等于“随机保留整图一半”。V_DOMAIN_FULL/CONTEXT_FILL 平均保留 5,831.4，增加约 608.5 个位置。

V_SOURCE_UNIFORM 与 U 在全部 220 例的保留集合都不同；平均 Jaccard 为 0.8817，替换了约 6.30% 的总保留位置。该百分比看似小，是因为强制 A 占比很大；改动集中在可选证据。V_CONTEXT_FILL 与 DOMAIN_FULL 也全部不同，平均以 608.5 个域外邻近位置替代同数登记证据位置。这是实际发生的干预，不是换名重复。

### 4.1 本地运行开销

正式阶段 8,931.832 秒，即 **148.86 分钟、10.33 次实际调用/分钟**；以 1,538 次实际正式调用计，不用 1,560 个逻辑位置或 smoke 膨胀吞吐。实际调用均正常停止，无输出上限截断；记录中的 KV preemption 为 0。
''')
add(table(['Arm','输入加载/processor 均值秒','视觉编码/传输均值秒','语言阶段均值秒','输入到验证中位数秒','P95秒'],[[a,*[f'{A[a,"all"][k]:.2f}' for k in ['prepare_seconds_mean','vision_seconds_mean','language_seconds_mean','input_to_validation_p50','input_to_validation_p95']]] for a in order]))
add('''这些是混合队列并发下的逐请求计时，不是隔离单臂服务基准；语言阶段含引擎调度等待，不能将其直接称为纯 kernel 时间。表中均值也不能相加冒充冷路径连续时间。正式“输入到验证”从已准备文件开始，**不含提前完成的原始遥测编译/绘图**。历史 T_FULL 没有本轮同期冷时延重跑，因此本报告不主张端到端加速比例。没有电价、功耗积分或云端收费数据，总 token 只是成本维度之一。

## 5. 配对统计与修复/破坏

四项预注册主要比较，以 **193 个事件组**的组内平均 RR 差作为主要推断；220 个病例的配对分析单独给出。双侧 Pratt-zero Wilcoxon，差值保留 12 位，四项同族 Holm 校正，配对 dz；不报告置信区间。Wilcoxon 的对象是配对差值的秩与分布假设，不将其表述为对任意均值零假设的直接检验。报告分析脚本从 1,560 个原子提交独立重算，与自动汇总逐项一致。
''')
for unit,label in [('event','事件组主要分析'),('case','病例配对分析')]:
 add('### '+label)
 add(table(['比较','n','平均 RR 差','原 p','Holm p','dz'],[[x['contrast'],x['n'],f(x['delta']),f(x['p']),f(x['pH']),f(x['dz'])] for x in s['primary'] if x['unit']==unit]))
add('''四项均未通过 pH<0.05。其含义是：本轮没有建立组合、来源内选择或上下文补充的登记优势；不是证明这些机制永远无效。H_MARGINAL 为事后最强新臂，它对历史文本的 +0.0066 只按工程比较报告，不追加事后显著性选择或把历史比较包装成同期试验。
''')
add(table(['新−旧','RR提升/下降/相同','Top1修复/破坏','Top5修复/破坏'],[[x['new']+' − '+x['old'],f"{x['rr_improve']}/{x['rr_worse']}/{x['rr_tie']}",f"{x['top1_repair']}/{x['top1_break']}",f"{x['top5_repair']}/{x['top5_break']}"] for x in s['paired'] if x['dataset']=='all']))
add('''组合对单边际图有 24 例 RR 改善、37 例下降，Top1 修复 12、破坏 18；这比只给 ΔMRR 更清楚地显示收益与伤害共存。来源内均匀法相对历史 U 修复 Top1 仅 3 例、破坏 13 例，不支持继续把它当作已经优于 U 的起点。

## 6. 失败分母、根因粒度与重复

全部主矩阵结果均已提交，基础设施未知为 0；因此全分母上下界收敛到同一个分数。没有删除低分病例、候选错误或回退病例。
''')
fail=json.loads((P/'failure_decomposition.json').read_text())
add(table(['Arm','无效回答','含未知 ID','重复 ID','宽容后有命中','宽容 MRR 增量'],[[x['arm'],x['invalid'],x['raw_unknown'],x['duplicates'],x['tolerant_nonzero_among_invalid'],f(x['mrr_salvaged'])] for x in fail]))
add('''“未知”和“重复”可重叠，V_DOMAIN_FULL 有一例同时包含两类问题。不存在的 ID、类型/归属混淆和不满足五个不同候选是模型输出问题，不是基础设施丢失。标准分数仍是主分数；宽容后纯视觉最高只有 0.3499，说明修正格式规则本身不能填平与约 0.49 hybrid 的差距。

### 6.1 根因粒度分层（探索性）

保留评分合同明确给出可接受根因及其映射，未统一保留各数据集可直接比较的注入故障类型。下表按标签所对应的候选实体粒度分组，**不是 CPU/内存/网络故障类别**。某些病例同时接受 service 与 pod；它们单列，避免重复计数。此分层由评分侧标签生成，只用于离线分析，不能用来在线挑方法。
''')
g=list(csv.DictReader((P/'root_granularity_metrics.csv').open()))
add(table(['可接受根因粒度','n',*order],[[grp,next(x['n'] for x in g if x['granularity']==grp),*[f(float(next(x['mrr'] for x in g if x['granularity']==grp and x['arm']==a))) for a in order]] for grp in ['service','pod','node','pod,service']]))
add('''H_MARGINAL 在 service-only 152 例上为 0.5799，组合在 pod-only 23 例上为 0.5725；pure-visual 的 node-only 28 例非常弱。这个结构提示“正确找服务”与“正确追到实例或主机”难度不同，也解释为什么合并均值不能代表所有根因粒度。样本大小及数据集构成不同，尚不能归因为某种故障机制。

### 6.2 独立重复不是提高原分数的第二次机会
''')
add(table(['Arm','n','同子集原 MRR','重复 MRR','原/重复宽容 MRR','首选变化','完整排名变化','逐字输出相同'],[[x['arm'],x['n'],f(x['base_mrr']),f(x['repeat_mrr']),f(x['base_tolerant'])+' / '+f(x['repeat_tolerant']),x['top1_flips'],x['ranking_changes'],x['identical_raw']] for x in s['repeats']]))
add('''全部重复请求的生成输入身份相同、调用独立。H_TOPO_MARGINAL 仅 1/30 首选改变；V_SOURCE_UNIFORM 首选全部相同，但有 7/30 完整排名变化。后者标准 MRR 从 0.3050 到 0.3494 的增加完全对应两条原无效输出变成合法输出：宽容 MRR 前后均为 0.3494。它不能算一次新的方法收益，也不能替换原主矩阵分数。

## 7. QA：联合分数、实际读数与评分接口必须拆开

每臂固定 30 例、理论 180 题，其中 2 道关系题不适用，实际 **178 题/臂**；总体 QA 以病例内适用题比例再平均。下面同时给原登记标准/宽容分数与一个明确标为事后的单位别名敏感性分析。

原“宽容”规则允许数值字符串等价、ID 前缀/首尾空白、集合顺序等变化，但并不把 `source unit` 与 `source_unit`、`µs` 与 `microseconds` 当作同一单位。因此联合分数包含字段串行化约束，而不只是视觉读取能力。
''')
qa_raw=json.loads((P/'qa_rca_answers.json').read_text());sens={x['arm']:x for x in json.loads((P/'qa_unit_sensitivity.json').read_text())}
Sraw=json.loads((ROOT/'RQs/RQ4_5/results/exclusive_spatial_v1/analysis/summary.json').read_text())
add(table(['Arm','标准 QA','登记宽容 QA','事后单位别名敏感性'],[[a,pct(sum(x['qa_standard'] for x in qa_raw if x['arm']==a)/30),pct(sum(x['outcome']['tolerant'] for x in Sraw['qa_answer_review'] if x['item']['arm']==a)/30),pct(sens[a]['posthoc_unit_alias_case_accuracy'])] for a in order]))
add('''敏感性分析只将单位中的空格/下划线与 `μs/µs/us/microseconds` 别名统一，数字仍要求精确、实体/关系不修复、排名不变；不把复合字符串 `counts_microseconds_and_log2_fold_change` 强行当作微秒。它不是预注册新得分，也没有替换原文件。原题问“source unit”，而源 Trace 记录的整体单位字段恰好是这种复合串、目标 duration 字段则以微秒为单位，这也形成测量语义歧义。

### 7.1 全部 QA 回答的逐字段分析
''')
rc=json.loads((P/'qa_reading_counts.json').read_text());Q={(x['arm'],x['family']):x for x in s['qa_components']}
add(table(['Arm','数值正确/60','数值+实体正确/60','完整关系正确/58（宽容）','阶段方向正确/60'],[[a,next(x['numeric_only'] for x in rc if x['arm']==a),next(x['numeric_and_entity'] for x in rc if x['arm']==a),round(Q[a,'binding']['tolerant']*58),round(Q[a,'comparison']['content_correct']*60)] for a in order]))
add('''三个 hybrid 数值题均有 59/60 数值与实体一起正确，但严格联合读数题只有约 35–36/60，主要受单位表达影响。纯视觉则有 16–22/60 数值正确，关联正确实体后降至 13–18/60；既有真正读取错误，也有读对数值但挂错来源。

关系题是更强的局部诊断信号：H_MARGINAL 保留关系文本，51/58 完整正确；拓扑转图后为 0/58 或 1/58。逐份回答常给空列表、整片节点列表、把 operation 当 pod，或漏掉端点。图中边实际存在，不能把回答空列表等同于原始数据没关系。该差异与本轮图形中大量交叉边、跨卡片找目标的困难相容；没有隔离实验就不能唯一归因于交叉、剪枝或旧说明。

阶段方向题里 **53/60 的正确答案本来就是 current**；“总回答 current”已有 88.3% 的方向正确率。Hybrid 的 56/60 为 93.3%，pure-visual 为 39–44/60；单报阶段方向成功比例容易夸大实际理解。该字段分析不把同一病例的多道题当作独立统计样本。

![QA分解](artifacts/RQ4_5_2026-10-19/qa_decomposition.png)

### 7.2 QA 与 RCA 的统计联系
''')
add(table(['Arm','30例 Spearman ρ','未校正 p（探索）'],[[x['arm'], '不可计算（QA恒为0）' if x['rho'] is None else f(x['rho']),'—' if x['p_unadjusted_exploratory'] is None else f(x['p_unadjusted_exploratory'])] for x in s['qa_correlations']]))
add('''这些小样本、地板效应明显且带接口噪声的相关结果，不支持稳定正向关联；也不能证明“读取与诊断独立”。QA 目标由公共数据固定生成，并不保证对应当例根因所需的最关键证据。**QA 很低仍诊断正确，可能是使用了别的有效线索，也可能是排名碰巧正确而理由有错，必须看实际回答。**

## 8. 实际 QA—RCA 轨迹与解释可信度

本报告对全部 180 份 QA 做字段检查，另外逐份阅读 **9 个病例 × 6 臂 = 54 组 QA—RCA 完整回答**。每数据集先取固定 QA 子集中按 opaque ID 排序的首例，再取组合相对边际图 RR 差最大和最小的病例；后两项是刻意包含修复/破坏的事后样例，不能据此估计总体错误率。AIOPS-2025 的最大差值为 0，不能称作正收益实例。剩余 126 组做了结构化字段分析，未声称全部逐份定性审查。

### 8.1 坐标刻度被当作“记录基线”

AIOPS-2022 `INC-0986D6C54EC6`：MET11 的基线是 **15.25**，实体是 **81384**。V_DOMAIN_FULL 和 V_SOURCE_UNIFORM 返回 **739.7**；这个数是图上的上方 y 轴刻度，不是记录基线。MET03 应返回 **0.01942**，却返回 **0.39889**，同样对应图的上方刻度。H_MARGINAL 两题的数值、实体、单位全部正确。

同例的 hosts 关系目标是 `81384 ← 4176` 与 `88466 ← 7758`。H_MARGINAL 能完整返回端点；H_TOPOLOGY 给空集或把全部三个 node 都列入；组合给 null。实际原图及来源账本有目标关系。该例六臂最终 RR 都为 0：即使这些 QA 正确，也不足以保证找对根因 node 7758。

[查看实际部署关系 PNG](../../RQs/RQ4_5/results/exclusive_spatial_v1/objects/a318e0ffb02ec490d49cad5bef61161eae55daefab4c23853a821d9419b62294.png) · [查看同例纯视觉原图](../../RQs/RQ4_5/results/exclusive_spatial_v1/objects/6f2dcac3b45602f0b7948bd95849046128b7b202f447e380adaab61b9a9cd15b.png)。分析时已实际打开核对，未重新绘图。

### 8.2 QA 满分仍可诊断错误

AIOPS-2025 `INC-27CBD1F8668A`：三种 hybrid 的四道适用 QA 全对（两道关系题不适用），最终却都把 906 放第一；可接受根因是 343/84413，均未进入前五。图形转移目标为空，因此三臂是同一文本请求的精确引用，不能把这三次记为三份独立成功读取证据。这是“被测题答对并不保证题目足以支持正确 RCA”的明确例子。

### 8.3 根因排第一，数值及解释仍可能错误

AIOPS-2025 `INC-F328F417F5C9`：六臂都将 323 排第一，RR=1。V_SOURCE_UNIFORM 的 QA q1 正确读到 **301488.45**，但 entity 填 operation 字符串 `702.323/GetAds`、unit 填 `323`，所以联合评分为零。其 RCA 理由又把 reference/current 说成约 **0.8ms/30.1ms**，而该 TRC01 的实际记录是 **8044.9µs/301488.45µs（约8.045ms/301.488ms）**。V_DOMAIN_FULL 更将 current 说成约 **301秒**。正确的首选不能给这些解释背书。

### 8.4 理由与排序直接矛盾

AIOPS-2022 `INC-89856C07F4EE` 的 V_DOMAIN_FULL 输出第一名 **86924**，理由最后却明确排除 86924、支持 **80439**，而后者在第二名。宽容评分不能解决这种理由—排名矛盾；这需要单独的解释一致性指标。同例还有把真实延时读错量级、把不同 operation/实体连在一起的叙述，不能只统计 JSON 是否合法。

AegisLab `INC-01BF937825D4` 的组合排序是 `[519,960,836,927,689]`，理由却称 **580 是 root cause**，580 不在前五。H_TOPOLOGY 理由还把约 94ms exclusive /203ms inclusive 解释成“exclusive 超过99%”，有直接算术矛盾。

### 8.5 相同数据支持可被不同输入组织导向不同诊断

AegisLab `INC-058FC5DD18AD`：H_MARGINAL 将 905 排第一，组合把它放第二、改推 661。两者理由都引用 661→905，却对哪个是起点作出不同解释。关系 QA 中，H_MARGINAL 正确给出 `661→25836` 与 `419→40039` 的实例关系；图形条件返回混杂的大量 pod。它与组合退化方向一致，但仅是病例机制线索，不能证明 QA 错误导致该次排名变化。

另一个 AegisLab 例 `INC-332110D70FB3` 相反：组合将正确根因 328 从边际图臂第五位提高到第一位。组合的关系 QA 仍失败，却在 RCA 中使用了显著的 exclusive p95 和配对线索。**图形收益、关系 QA 与解释质量并非一个共同分数的不同名字。**

完整选样、问题、预期答案及逐字 QA/RCA 原文保存在 [回答审查附件](artifacts/RQ4_5_2026-10-19/manual_review_answers.md)。这些例子用于识别可检验的失败类型，不宣称完成了全部 1,320 条诊断的因果真实性认证。

## 9. Attention：测到了什么，没有测到什么

固定机制病例的真实调用采集到 **412 份独立正式摘要**，每份两个 query、层号 3；另有本地 smoke 的 6 份。420 个正式逻辑测量位置中的 8 个是精确引用，没有重复采集。正式摘要最大 3,922 字节，最大归一化误差约 5.37×10⁻⁶，采集记录正常。

口径只覆盖 **最后一个 prompt query 与第一个 decode query**，不是最终排名字段、不是所有输出 token，也不是所有层。文本区域在 hybrid 中包含任务说明和诊断文本，不能把它标成纯“instruction attention”；纯视觉文本才主要是静态说明。图像区域是各 panel/header/background，无法据此细分面板内部的每个数字、箭头、单位及标签。
''')
att={(x['arm'],x['stage']):x for x in s['attention'] if x['variant']=='BASE'}
add(table(['Arm','独立RCA记录','末prompt：文本/图像','首decode：文本/图像/其他'],[[a,att[a,'last_prompt']['n'],pct(att[a,'last_prompt']['text_mass'])+' / '+pct(att[a,'last_prompt']['image_mass']),' / '.join(pct(att[a,'first_decode'][k]) for k in ['text_mass','image_mass','other_mass'])] for a in order]))
add('''均值按独立实际记录计算。H_TOPOLOGY/组合各 28 份，差异来自精确引用，不能按不同有效样本数直接解释微小 attention 差异。

![实际attention汇总](artifacts/RQ4_5_2026-10-19/attention_mass.png)

纯视觉仅 421 个文本/模板 token，却获得约 86% 的末 prompt attention 质量；约五千个视觉 token 获得约 14%。三个纯视觉方法的该比例非常接近，但 MRR 不同，所以**“更多总 image attention”不是本轮可用的性能代理指标**。这只是早期 query 的平均分配，不能推出模型最终不使用图像，也不能证明文本 token 是有害 sink。

映射还显示，本次实际保留集合中 **header 区域的 token 数为 0，因此直接 header attention 为 0**。这不表示标题从原 PNG 或前置视觉编码中消失，也不能声称已经解决过去的标题 attention 现象：视觉编码仍看过标题，旧现象与当前保留集合、层/query 口径不同。面板内图文混合的全部作用仍无法从这两个摘要分开。

Attention 保留预算含摘要和附属映射共 9,278,413 字节，约等效 **0.0596 GB/万次本地完成调用**，低于 1 GB；这是已登记小样本采集方案的实际密度，不是宣称保存了完整矩阵。没有单独同期 on/off 测时，不能从本轮推断采集开销为零。

## 10. 结论边界与下一步建议

### 已得到的工程结果

H_MARGINAL 是本轮值得保留的折中点：独占配对图形、约 0.49 MRR、实际 token 下降，AegisLab 达到 0.6472。它不需要将那组配对样本和统计重复塞回文本，说明混合分工有可部署空间。这一结论比“没有显著差异所以没有成果”更符合结果，但仍不是所有数据集都提升或创新机制已获证明。

### 没达到的目标

预选 hybrid 组合低于强文本整体排名，预选纯视觉低于 U；整体没有超过旧混合最佳 0.5054，更没有接近 0.60。四项主要比较无校正后显著收益。H_MARGINAL 虽有正向工程折中，两个 AIOPS 的退化及没有独立重复臂，都限制直接采用。

### 建议的优先级（不是新实验授权）

1. **保留 H_MARGINAL 与历史 U 两个各自已测量的起点。** Hybrid 继续关注具体事实的独占承载与成本；纯视觉不将失败的来源内均匀规则替换 U。
2. **先用已有输出做低成本接口修整与测量整理。** 统一单位语义、区分字段值/坐标刻度/实体/operation、整理理由—排序矛盾；未来输入清理矛盾说明，但不改本轮冻结输入或旧分数。更好的 QA 合同能避免把格式错误当成视觉机制。
3. **拓扑下一步应解决局部可寻址绑定，而不是追加更多完整图。** 本轮已表明精确一跳端点读取很弱。若设计后续实验，应保留完整诊断作用范围、明确需要核验的绑定任务和成本，优先复用现有 renderer；不以本报告自动授权重画或重跑。
4. **不要按本轮数据集/标签事后自动挑臂。** 粒度与数据集互补只能提出下一项冻结假设，不能把事后最佳并集当作部署 MRR。
5. **真正的推进需完整方法的跨数据集收益。** 新候选应同时报告标准排名、宽容敏感性、实际总 token、有效运行耗时和解释可靠性；开发数据上成立后，再讨论冻结后的验证。

本次分析没有启动新的模型、实验、训练或盲审，也没有修改 renderer、运行代码、原始回答、登记得分或 Codex.md。

## 11. 可复核材料与保留状态

- [冻结计划与实施修订](../experiment_plans/RQ4_5_Exclusive_Modality_Spatial_Pruning_Plan_2026-10-18.md)。
- [正式提交与完成状态](../../RQs/RQ4_5/results/exclusive_spatial_v1/formal/summary.json)、[阶段完成标记](../../RQs/RQ4_5/results/exclusive_spatial_v1/formal/phase_complete.json)。
- [原自动完整汇总](../../RQs/RQ4_5/results/exclusive_spatial_v1/analysis/summary.json)保留不变，其中“manual review pending”是生成时的历史状态；本报告的额外审查范围以第8节及附件为准。
- [独立分析总表](artifacts/RQ4_5_2026-10-19/analysis.json)、[病例明细](artifacts/RQ4_5_2026-10-19/per_case.csv)、[指标/成本/计时](artifacts/RQ4_5_2026-10-19/metrics_cost_timing.csv)、[配对修复/破坏](artifacts/RQ4_5_2026-10-19/paired_repairs.csv)。
- [QA逐字段核验](artifacts/RQ4_5_2026-10-19/qa_field_audit.json)、[全部180组QA/RCA原文关联](artifacts/RQ4_5_2026-10-19/qa_rca_answers.json)、[单位敏感性](artifacts/RQ4_5_2026-10-19/qa_unit_sensitivity.json)、[attention逐query表](artifacts/RQ4_5_2026-10-19/attention_per_query.csv)。
- [可重跑离线分析脚本](artifacts/RQ4_5_2026-10-19/analyze.py)、[补充分析](artifacts/RQ4_5_2026-10-19/supplement.py)、[来源哈希](artifacts/RQ4_5_2026-10-19/provenance.json)。仅读取已保存结果，不导入模型或渲染器。
- [实验唯一findings状态](../../RQs/RQ4_5/findings/exp_exclusive_spatial_findings.md)。

运行结束的保留审核为 3,188,389,839 字节，约等效 **20.49 GB/万次完成调用**，低于 25 GB。文件直接可读、完整输入/PNG/对话/输出/评分及实际 attention 可恢复，精确引用不增加调用分母。该 receipt 描述最终运行材料；本报告与分析附件另外纳入[报告交付核验](artifacts/RQ4_5_2026-10-19/delivery_verification.json)，不以移动目录规避计量。

直接查看某条完整会话可用现有 `src/main.py view --key …` 接口；原始 `formal/completed/` 记录包含 request/trajectory 路径，`formal/requests/` 保存真实文本、图像引用及保留索引，`formal/trajectories/` 保存完整回答。原 PNG 在 `objects/` 中按哈希保存，无需解压。详见 [README](../../RQs/RQ4_5/README.md)。
''')
(D/'RQ4_5_Qwen_Analysis_2026-10-19.md').write_text('\n\n'.join(parts)+'\n')
print(D/'RQ4_5_Qwen_Analysis_2026-10-19.md')
