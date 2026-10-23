"""Assemble the RQ4.6 report from verified offline aggregates."""
from pathlib import Path
from statistics import mean
import json

P=Path(__file__).resolve().parent
OUT=P.parents[1]/'RQ4_6_Qwen_Analysis_2026-10-19.md'
D=json.loads((P/'analysis.json').read_text())
S=json.loads((P/'supplement.json').read_text())
Q=json.loads((P/'qa_rca_answers.json').read_text())
A={(x['arm'],x['dataset']):x for x in D['aggregates']}
H={(x['arm'],x['dataset']):x for x in D['historical']}
arms=[a for a,ds in A if ds=='all']
datasets=['aiops2022','aiops2025','aegislab']
dsnames={'aiops2022':'AIOPS-2022','aiops2025':'AIOPS-2025','aegislab':'AegisLab'}
rel='artifacts/RQ4_6_2026-10-19/'
chunks=[]
def add(t):chunks.append(t.strip()+'\n')
def table(head,rows):
    add('| '+' | '.join(head)+' |\n| '+' | '.join(['---']*len(head))+' |\n'+'\n'.join('| '+' | '.join(str(v) for v in row)+' |' for row in rows))
def f(x):return f'{x:.4f}'
def pct(x):return f'{x:.2%}'
def signed(x):return f'{x:+.4f}'

add('''# RQ4.6 完整结果分析：激进 hybrid 降本、pod 关系连接与均匀剪枝优化

日期：2026-10-19，America/Toronto。实验：`pod_join_v1`。证据类别：**已暴露开发集上的完整实验**，不是独立确认集。

**本轮实现了明显的 hybrid token 降本，但未实现“排名继续上升且成本下降”。** 新臂最高标准 MRR 为 `H_MARGINAL_PHASE` 的 **0.4590**，平均每例 input＋output 为 **12,716.6 token**：比 RQ4.5 `H_MARGINAL` 少 **39.20%**，MRR 下降 **0.0322**。主要损失来自 AegisLab；两个 AIOPS 数据集相对旧边际图接近持平。纯视觉最高新臂 `P_U_NEIGHBOR_PAIR` 为 **0.3436**，仍低于历史 `A_UNIFORM_E50` 的 **0.3517**。

正式 **2,620/2,620 个位置已提交**：2,601 次真实调用＋19 次精确结果引用；另有18次 smoke，累计2,619次真实调用。本次分析未调用模型、未改变原评分、未改方法或重答任何病例。全部结果已复算并核验。

**需要单独记录一个工程未完成项：模型推理和结果提交已经完成，但结束后的自动存储精简失败。** 当前结果目录约11.724 GB，尚未达到最终保留预算。它没有造成本报告的结果缺失；详见第13节。本报告不将 `progress.json` 的 passed 扩大解释为归档也通过。

## 1. 十项主要结论

1. **激进删减确实节省了成本。** 五个 hybrid 的平均总 token 比旧 H_MARGINAL 降低约37.7%–39.2%（H_DEPLOY_ONLY 为36.4%）；成本收益来自整个输入方案，不能全部归因于视觉压缩。
2. **最有用的新工程点是低成本边际图，而不是组合候选。** H_MARGINAL_PHASE 为0.4590/12.7k token，提供了可量化的性能—成本取舍；它尚不能取代0.4912的旧 H_MARGINAL，也不能称为保性能降本。
3. **AegisLab 是本轮 hybrid 退化的主要来源。** H_MARGINAL_PHASE 相对旧 H_MARGINAL 在 AIOPS-2022/2025 为−0.0014/+0.0050，在 AegisLab 为−0.0730。三个数据集不能合并成“普遍小幅损失”。
4. **将部署关系通过 pod 串起来，没有带来稳定的整体排名改善。** Hybrid 的 bridge−separate 为−0.0023；纯视觉为−0.0315，后者标准评分经事件组 Holm 校正显著为负。
5. **组合优化可能破坏已有优势。** P_U_COMBINED 相对 P_U_NEIGHBOR_PAIR 为−0.0380，经事件组校正显著为负；宽容评分下负向结果仍通过相应敏感性校正。
6. **几何代理目标成功，不等于诊断成功。** 数值块目标由0.3067提高到0.9709，但 MRR 比历史 U 低0.0248。继续提高同一个代理分数缺乏本轮结果支持。
7. **“读到数值”与“读对数值的口径、来源”需要分开。** 实际回答出现把 p50 当成 p95、把同一数字归给另一操作、把 service 与 node 混在一个关系答案中的错误。
8. **QA 改善与 RCA 改善确实存在脱节实例。** H_POD_BRIDGE 对 H_POD_SEPARATE 的 QA 改善通过探索族校正，但主矩阵 MRR 没有相应上升；另有全部关系题回答正确、最终仍找不到故障 pod 的病例。
9. **评分接口解释了部分损失，但不是全部。** 宽容评分挽回了若干正确首选被重复候选连带清零的回答；它没有让预选剪枝方法超过邻域剪枝，亦不能把不在候选中的实体修成正确实体。
10. **Attention 提供了测量事实，尚未证明机制。** 本轮只采集第3层、最后一个 prompt query 与首个 decode query；纯视觉输入中的少量说明文字获得约86%的起始查询 attention。它不是最终排名 token 的 attention，不能据此认定文字是有害 sink。

## 2. 实际执行了什么

### 2.1 样本、模型与完整性

- 220个已暴露开发病例：AIOPS-2022 60、AIOPS-2025 60、AegisLab 100；按数据集和事件组联合身份计193组。
- 10个 RCA 臂×220例＝2,200个主位置；11个 QA 条件×固定30例＝330个位置；3个预选方法×30例独立重复＝90个位置。
- 历史 T_FULL、MARGINAL_FIVE、A_UNIFORM_E50、H_MARGINAL 共880份引用用于比较，没有重新推理。QA 的 U_QA 是新测量任务，不是重跑 U 的 RCA。
- 本地 BF16 Qwen3.8-27B，vLLM；8个独立 CPU worker、GPU并发8、显存利用率0.8；context 40,960、输出上限8,192。解码 temperature=1、top_p=0.95、top_k=−1、seed=42，thinking关闭。
- 所有诊断均为一次模型调用。QA 答案不进入 RCA。无标签进入模型输入或剪枝选择。本次冻结规则不按部分排名调整。

本次离线核验重新计算2,290份 RCA（含重复）和330份 QA，全部与已提交分数一致；核验1,928张唯一模型可见图像、5,512个已提交 sidecar 的哈希、880份历史记录哈希，以及冻结源码/配置/processor。模型权重按冻结文件大小和mtime来源记录核对，**没有重新遍历计算整套权重哈希**。所有2,601次真实正式调用均以 `stop` 结束，无基础设施未知、无KV抢占；模型无效回答仍在分母中。

冻结执行指纹：`fbefc138717ca7a050632babbfb6d82aa1432d2d10ef76a6c59d7afac81186f1`。准确复现以该清单中的源码与配置哈希为准，不能仅依赖当时的 Git commit（工作区包含已冻结的未提交修改）。

### 2.2 十臂及其比较含义

M/R/L/G 在此分别指指标、Trace、日志与关系事实。`pod join` 指通过同一 pod 将 service–pod 与 node–pod 关系连接起来；这些是观测部署关系，不是因果传播边。边际图显示同请求父/子调用在 reference/current 两阶段的耗时分布。''')
table(['Arm','核心输入/改动','预先指定的角色'],[
['H_DEPLOY_ONLY','部署关系放入 pod 连接图；请求耗时配对留在文本','hybrid 载体控制'],
['H_MARGINAL_PHASE','预算化边际图＋父/子绑定的同分位数 Ref/Cur 对照；拓扑留在文本','耗时视觉化控制'],
['H_POD_BRIDGE','预算化边际图＋pod 连接部署图','连接方法控制'],
['H_POD_SEPARATE','相同 hybrid 事实；service→pod、node→pod 分开展示','部署表达控制'],
['H_POD_PHASE','phase 边际图＋pod 连接图','**hybrid 预选方法**'],
['V_POD_BRIDGE','完整纯视觉 U 图，仅替换部署面板为 pod 连接；重新按 U 规则选 token','**纯视觉部署预选方法**'],
['V_POD_SEPARATE','完整纯视觉 U 图，部署关系分开展示','纯视觉部署控制'],
['P_U_VALUE_BLOCK','原 U PNG、prompt、K、锚点不变；交换可选 token 以覆盖完整数值块','数值支持控制'],
['P_U_NEIGHBOR_PAIR','原 U 输入和预算不变；改善同角色相邻位置的成对保留','邻域支持控制'],
['P_U_COMBINED','等权归一化组合上述两项目标；最多128次严格改善','**纯视觉剪枝预选方法**']])
add('''### 2.3 本轮 hybrid 的“压缩”是有损证据投影

用户明确允许激进删减证据，以成本下降为主要贡献之一。实际 `HybridSummaryBudgetV1`：

- 去掉核心指标的64-bin原序列及其缺失编码，保留原窗口摘要、统计、实体、单位。
- AUX 序列保留实际首、末、最小、最大观测及其原位置。
- 请求配对每阶段从最多32个样本改为8个原始观测，保留两端、确定性秩抽样和原样本编号。
- 保留 Trace、日志、总体/联合/条件统计及全部公共关系。

五个 hybrid 使用同一投影。已移交图像的来源事实不再作为另一份诊断文本重复；身份、单位、阶段等关联标签仍可重复。未移交的诊断事实继续在文本中。纯视觉臂没有采用这套删减。

数据适用性回退保留在分母内：H_MARGINAL_PHASE有9例实际无图，其余四个hybrid各4例实际无图；这是登记的来源为空情形，并非渲染失败后加回完整文本。五个纯视觉臂全部220例都有图。精确相同的请求按身份引用，因此19个引用不等于缺失结果。

因此，**hybrid 与历史完整输入/本轮纯视觉之间不是严格同事实比较**，只能评价完整系统的性能—成本取舍。旧拓扑在文本的冲突说明已在本轮修正；历史 RQ4.5 的实际拓扑载体仍是图像，不能因为旧说明而改写其方法分类。

Hybrid 图像仍通过注册支持 A∪E 选择，域外位置未送入语言模型；“完整登记支持”不等于“所有图像 patch 均保留”。所有臂先执行完整视觉编码，再进行相应的 token gather，不能把语言模型输入减少称为视觉编码计算已同比减少。

## 3. 完整主结果

下表 MRR 均为原220例分母；整体按病例加权，宏平均为三个数据集等权平均。标准评分要求完整的五个不同合法候选；任一结构/候选错误使该次标准排名计零。宽容评分读取原 JSON 排名，允许空白和显式类型前缀规范化，但未知/重复位置保持原位 miss，不修 ID、不前移后续候选。''')
table(['Arm','A22标准','A25标准','Aegis标准','整体标准','整体宽容','数据集宏平均','AC@5'],[
[a]+[f(A[a,d]['standard_mrr']) for d in datasets]+[f(A[a,'all']['standard_mrr']),f(A[a,'all']['tolerant_mrr']),f(mean(A[a,d]['standard_mrr'] for d in datasets)),f(A[a,'all']['ac@5'])] for a in arms])
add('历史参照使用相同220例的原回答与原成本，**不是本轮同期调用**；后端、提示及运行时期差异继续存在。下表只列历史标准分，不能拿新臂的宽容分与它混比。')
table(['历史方法','A22','A25','Aegis','整体 MRR','AC@1','AC@3','AC@5','总 token/例'],[
[a]+[f(H[a,d]['mrr']) for d in datasets]+[f(H[a,'all'][k]) for k in ['mrr','ac@1','ac@3','ac@5']]+[f"{H[a,'all']['total']:,.1f}"] for a in ['T_FULL','MARGINAL_FIVE','A_UNIFORM_E50','H_MARGINAL']])
add('''T_FULL 是完整强文本历史基线；MARGINAL_FIVE 是 RQ3.16 的完整文本＋重复呈现配对事实的边际图（0.5054）；H_MARGINAL 是 RQ4.5 的来源独占 hybrid（0.4912）；A_UNIFORM_E50（简称 U）是历史纯视觉、锚点保护＋可选证据域均匀保留50%的方法（0.3517）。前两个 hybrid 成绩不能作为纯视觉成绩。

![成本与排名](artifacts/RQ4_6_2026-10-19/ranking_cost.png)

图1：左侧星号为历史参照，圆点为本轮新臂；右侧展示标准与宽容评分。图不表示各点之间均具有同期、同事实的因果可比性。

![逐数据集MRR](artifacts/RQ4_6_2026-10-19/dataset_mrr.png)

### 3.1 完整排名指标

AC@k 表示前k名内命中至少一个可接受根因的比例；Precision@k 为前k位置命中可接受根因的比例；AVG@k 为 AC@1…AC@k 的算术平均。多个可接受别名/实体沿用中央评分器，Precision 不应直接等同 AC/k。以下全部为标准评分。''')
table(['Arm','AC@1','AC@3','AC@5','P@1','P@3','AVG@3','AVG@5'],[[a]+[f(A[a,'all'][k]) for k in ['ac@1','ac@3','ac@5','precision@1','precision@3','avg@3','avg@5']] for a in arms])
add('逐数据集的全部上述指标、标准/宽容 MRR、输入输出、失败及时间分布见 [完整指标 CSV]('+rel+'metrics_cost_timing.csv)。[逐病例表]('+rel+'per_case.csv) 保留配对身份，不只提供均值。')

add('''## 4. 成本：是真正的降本，但不是无损降本

成本定义为实际 input＋output token；其中 image_retained 是送入语言模型的视觉 token，image_original 是视觉编码前对应的图像 token。所有精确结果引用仍按逻辑部署成本记账，研究实际调用数另外计算。未测电费/功耗，token不等于GPU时间。''')
table(['Arm','文本输入','原图 token','保留图 token','总输入','输出','总 token','相对参照总成本'],[
[a]+[f"{A[a,'all'][k]:,.1f}" for k in ['text_tokens','image_original','image_retained','input_tokens','output_tokens','total_tokens']]+[f"{A[a,'all']['total_tokens']/H['H_MARGINAL' if a.startswith('H_') else 'A_UNIFORM_E50','all']['total']-1:+.2%}"] for a in arms])
add('上表 hybrid 的参照为历史 H_MARGINAL，纯视觉的参照为历史 U。三个剪枝臂的输入数量严格相同；总成本的极小差异来自生成长度，不能称为新的压缩收益。')
table(['数据集','H_MARGINAL_PHASE总token','相对旧H_MARGINAL','相对T_FULL','MRR Δ旧H_MARGINAL','MRR ΔT_FULL'],[
[dsnames[d],f"{A['H_MARGINAL_PHASE',d]['total_tokens']:,.1f}",f"{A['H_MARGINAL_PHASE',d]['total_tokens']/H['H_MARGINAL',d]['total']-1:+.2%}",f"{A['H_MARGINAL_PHASE',d]['total_tokens']/H['T_FULL',d]['total']-1:+.2%}",signed(A['H_MARGINAL_PHASE',d]['standard_mrr']-H['H_MARGINAL',d]['mrr']),signed(A['H_MARGINAL_PHASE',d]['standard_mrr']-H['T_FULL',d]['mrr'])] for d in datasets])
add('''新边际图相对 T_FULL 整体少42.83% token、MRR低0.0256；相对旧 H_MARGINAL 少39.20% token、MRR低0.0322。**这是一个有用的低成本工程点，但没有达到用户希望的“performance不掉”。** 本轮没有把旧 H_MARGINAL 放到同一删减投影下，因此无法把损失精确拆成“删序列”“32→8样本”“phase图”或“提示修正”的单独作用。

五个 hybrid 均达到相对旧 H_MARGINAL 至少20%总token下降的工程成本目标；三个预选方法均未达到对应历史基线 MRR＋0.02、各数据集不退化的排名目标。纯视觉成本在允许的1.10×U范围内，但不能用成本合格替代排名合格。

## 5. 同期配对统计与修复/破坏

预注册七项主要比较。主要推断单位为193个事件组：先在组内平均配对 RR 差，再做双侧 Pratt-zero Wilcoxon；220病例分析单独报告。差值保留12位，两个单位分别对同一七项族执行 Holm 校正。`dz` 为配对差的均值/样本标准差；不报告CI。Wilcoxon检验排名差分布，不能泛称为任意均值零假设检验。

表中 ΔMRR 为病例加权差；事件组均值差与其可能不同。正号表示左侧臂更好。''')
stats={(x['contrast'],x['unit']):x for x in D['primary']}
contrasts=[c for c,u in stats if u=='case']
table(['比较','病例ΔMRR','事件组Δ','事件组原p','事件组pH','事件组dz','病例pH'],[
[c,signed(stats[c,'case']['delta']),signed(stats[c,'event']['delta']),f(stats[c,'event']['p']),f(stats[c,'event']['pH']),f(stats[c,'event']['dz']),f(stats[c,'case']['pH'])] for c in contrasts])
add('''**两项校正后显著结果均为负向：** V_POD_BRIDGE−V_POD_SEPARATE，以及 P_U_COMBINED−P_U_NEIGHBOR_PAIR。H_POD_BRIDGE−H_DEPLOY_ONLY 有+0.0610的整体点估计、36修复/22破坏，是值得保留的观察，但事件组 pH=0.1663，未达到预注册归因要求。这里不能把其未显著写成“没有任何方法进展”，也不能宣布已证明该载体贡献。

### 5.1 逐病例修复与破坏

“修复/破坏”分别表示该病例 RR 提高/降低，不要求从完全错误变成完全正确。Top-1/5列另列二值命中的恢复/丢失。''')
pairs=[x for x in D['paired'] if x['dataset']=='all' and (x['new']+' - '+x['old'] in contrasts or (x['new'],x['old']) in [('H_MARGINAL_PHASE','H_MARGINAL'),('P_U_NEIGHBOR_PAIR','A_UNIFORM_E50'),('P_U_COMBINED','A_UNIFORM_E50')])]
table(['比较','RR修复','RR破坏','RR相同','Top1修复/破坏','Top5修复/破坏'],[
[x['new']+' − '+x['old'],x['improve'],x['worse'],x['tie'],f"{x['top1_repair']}/{x['top1_break']}",f"{x['top5_repair']}/{x['top5_break']}"] for x in pairs])
add('''### 5.2 宽容评分敏感性

离线保持同一七项比较和校正族，用已登记宽容分重新计算，属于敏感性分析，不替换主要标准分：

- V_POD_BRIDGE−V_POD_SEPARATE：病例Δ从−0.0315缩小为−0.0132，事件组 pH 从0.0116变为0.0691。其显著性受输出接口损失影响；不能把标准结果全部解释成图形理解能力下降。
- P_U_COMBINED−P_U_NEIGHBOR_PAIR：病例Δ从−0.0380变为−0.0259，事件组 pH=0.0291，负向差异仍保留。
- 只比较两臂都标准有效的病例时，上述差分别约−0.0080（197例）、−0.0292（202例）。这个子集由模型输出有效性决定，**不替代完整分母**，只用于定位损失来源。

没有基础设施未知，因此本轮已完成主矩阵不存在额外未知结果上下界；无效回答均已按规定计入，不剔除后重算 headline。

## 6. Hybrid：哪里变好，哪里变坏

### 6.1 数据集差异

H_MARGINAL_PHASE 相对旧 H_MARGINAL，AIOPS-2022/2025接近持平，AegisLab下降0.0730；按100/220权重，AegisLab贡献约−0.0332的整体差，两个AIOPS合计略有抵消，最终为−0.0322。因此最先需要定位的是 AegisLab 的损失，而不是继续扩大所有数据集的图形组合。

这不证明“AegisLab必须保留全部长序列”。本轮改变了多项输入条件，且实际失败解释中既有已删细节，也有仍保留事实被忽略/误归属。需要先逐病例检查，不能从数据集平均数直接发明路由规则。

### 6.2 根因实体粒度的事后分层

按私有评估映射中的可接受实体类别分层：node 28例、pod 23例、pod＋service多粒度17例、service 152例。它与数据集、故障类型可能混杂，**不是新的独立检验，也不能供部署时按真实标签选择方法**。当前评分上下文未提供足以做完整故障类型分层的注入类别；本报告不将实体粒度冒充故障类型。''')
g={(x['arm'],x['granularity']):x for x in D['root_granularity']}
groups=['node','pod','pod,service','service']
table(['根因粒度','n','H_MARGINAL_PHASE','H_POD_PHASE','PHASE−MARGINAL_PHASE','H_POD_PHASE−历史H_MARGINAL'],[
[gr,g['H_POD_PHASE',gr]['n'],f(g['H_MARGINAL_PHASE',gr]['mrr']),f(g['H_POD_PHASE',gr]['mrr']),signed(g['H_POD_PHASE',gr]['mrr']-g['H_MARGINAL_PHASE',gr]['mrr']),signed(g['H_POD_PHASE',gr]['delta_history'])] for gr in groups])
add('''H_POD_PHASE 对 node/pod 子集有正向点估计，但 service 子集相对 H_MARGINAL_PHASE 低约0.0592，而service占152/220，抵消了局部收益。这个异质性比“拓扑永远没用”更准确，也还不足以支持新的标签盲路由器。

### 6.3 实际输入与解释对照

以下两个AegisLab病例是**事后选择的损失示例**，不用于估计错误发生率。

- `INC-6CB07956172F`：旧 H_MARGINAL 将可接受根因563列第一，新边际图首选673且前五漏掉根因。新文本仍保留563的RSS首末/最大值（约7.76e8→1.96e9），因此不是根因证据全部消失。更关键的是，旧回答将 `MET05` 的峰值归给563，但来源实际属于413。**旧排名正确也不代表旧理由正确**，不能把它当作恢复某条“正确推理链”的金标准。
- `INC-4C4024E9EF1F`：旧 H_MARGINAL 将736列第一，新 H_MARGINAL_PHASE 将203列第一、736列第三；H_POD_PHASE则漏掉736。新文本仍有736文件系统统计从约5.82e5到8.12e6、末端达到最大值，以及203→736、736→294/997关系。解释由“持续增长”转向“更早/上游调用者”。删掉完整形状可能影响选择，但保留事实后的证据权重改变也存在，不能仅归咎于数据缺失。

正向示例 `INC-6E627662CA32`：H_MARGINAL_PHASE 找到故障pod63581，旧 H_MARGINAL只首选其相关service493；H_POD_PHASE又转向caller643并漏掉故障pod。部署连接增加了明确关系，却未保证更精细的故障定位。这是方法取舍示例，不说明连接图总是导致caller混淆。

## 7. 纯视觉剪枝：代理目标提高，诊断排序没有提高

三个剪枝臂保留原 U PNG、prompt、位置编码、锚点和每例 K；平均保留5,223个图像token，原图平均16,252个token。它们只交换相同预算内的可选支持位置，不更换诊断证据。

目标函数分别是完整数值支持、局部相邻支持及其归一化组合。下表目标值是登记优化目标的病例平均，**不是读取正确率**；不同目标列之间也不能直接横向比较高低。''')
table(['Arm','目标初值→终值','替换可选token比例','ΔMRR vs U','目标增量/RR增量Spearmanρ','探索p'],[
[x['arm'],f"{f(x['initial_objective'])} → {f(x['final_objective'])}",pct(x['optional_replaced']),signed(A[x['arm'],'all']['standard_mrr']-H['A_UNIFORM_E50','all']['mrr']),f(x['objective_rr_correlation']['rho']),f(x['objective_rr_correlation']['p_exploratory'])] for x in D['selection_summary']])
add('''这说明当前代理目标与诊断效用没有建立可用对应关系；相关性接近零且未显著，不能反过来证明两者统计独立。组合臂改动可选位置最多（约25.7%），相对U损失也最大，但这仅是三个算法的观察，不能直接推出“改动越多必然越差”。

均匀保留仍可能得益于较分散的局部上下文、较少改变原特征组合或减少模型干扰；**本轮没有隔离证明这些原因**。数值块更完整仍可能读错实体/阶段，原始视觉编码也早于gather发生，因此“某字符串支持完整”不能替代文字可辨认、来源绑定和最终选择三个环节。

## 8. 接口有效性与独立重复

### 8.1 无效回答不是基础设施失败

五个 hybrid 全部220例标准有效。纯视觉仍有未知候选或重复候选；下表两个错误计数可重叠，“宽容挽回”指标准无效而宽容RR大于0。完整原回答已保留，不是生成到非法候选就中止。''')
table(['Arm','标准无效/220','原始未知ID','重复ID','宽容挽回'],[[a,A[a,'all']['invalid'],A[a,'all']['raw_unknown'],A[a,'all']['duplicates'],A[a,'all']['salvaged_invalid']] for a in arms[5:]])
add('''例如 `INC-1595063C5B11` 的 P_U_COMBINED 输出 `[84394,33620,60764,67740,84394]`：第一名已经是可接受根因，但第五名重复导致标准RR=0，宽容RR=1。邻域臂输出合法第五名2788，标准RR=1。这类接口损失不能全部当作没有识别根因。另一方面，宽容评分不补全真实漏掉的根因，因此纯视觉剩余差距仍是实际诊断问题。

### 8.2 “独立重复”究竟相同什么

重复条件使用**完全相同请求身份、提示、图片和token选择**，但真实创建新调用/attempt，不引用之前回答。每个预选方法固定30例。同一输入不保证逐字输出相同；本地解码及执行环境下应以实测稳定性为准。''')
table(['方法','原/重复标准MRR','原/重复宽容MRR','Top1翻转/30','完整排名改变/30','回答逐字相同/30','原/重复无效'],[
[x['arm'],f"{f(x['base_mrr'])} / {f(x['repeat_mrr'])}",f"{f(x['base_tolerant'])} / {f(x['repeat_tolerant'])}",x['top1_flips'],x['ranking_changes'],x['identical_response'],f"{x['base_invalid']}/{x['repeat_invalid']}"] for x in D['repeats']])
add('''H_POD_PHASE 的RR全部不变，但只有3份原始回答逐字相同，表明解释措辞波动不等于排名波动。P_U_COMBINED 标准MRR提高0.0333，而宽容MRR完全不变，说明该平均改善来自标准接口惩罚的变化，不能称为更好的根因识别。

这个30例子集原始表现高于全220例，不可直接外推其重复均值。本轮没有给事后最高的 H_MARGINAL_PHASE 或 P_U_NEIGHBOR_PAIR 安排独立RCA重复，不能宣称它们的优势已通过重复验证。

## 9. QA：不仅比较得分，还检查模型答了什么

固定30例、每数据集10例，按预注册哈希选取。三个QA任务族测量内容不同，不能把全部题混成一个总能力分：hybrid为2道部署关系＋4道总体耗时读数；纯视觉部署为6道关系题；剪枝/U_QA为6道数值/来源题。两个无配对病例的hybrid数值题不适用，所以数值题共有112道，关系题60道。剪枝族有172道适用题。

所有330份QA均做原答案—oracle逐字段自动核对；对固定30例进行了跨臂QA与RCA回答检查，并对下述病例查看完整解释和来源。报告保留全330份原答案与对应RCA，人工审查并非对330份解释进行盲法双人编码，亦不将示例比例当作普遍发生率。''')
table(['Arm','病例平均标准QA','病例平均宽容QA','适用问题数'],[
[a,f(mean(x['qa_standard'] for x in Q if x['arm']==a)),f(mean(x['qa_tolerant'] for x in Q if x['arm']==a)),next(x['questions'] for x in D['qa_components'] if x['arm']==a and x['family']=='all')] for a in arms+['U_QA']])
add('''![QA分解](artifacts/RQ4_6_2026-10-19/qa_components.png)

图3的分量按适用题汇总，仅作描述；统计检验仍按病例，不把题目扩充成独立样本。

### 9.1 耗时移交后，数字可见不代表口径读对

H_DEPLOY_ONLY 的耗时仍在文本，112道数值题104道精确正确（92.86%）；允许事后1%数值误差时为100%。H_MARGINAL_PHASE 同一组数值题仅14/112精确正确（12.50%），1%误差后20/112（17.86%）。两者实体/单位字段接近全对，问题主要不只是单位别名或小数舍入。

实际模型可见例图如下，未重绘：

![实际phase边际图](artifacts/RQ4_6_2026-10-19/example_phase_INC-8991CE65FDA1.png)

`INC-8991CE65FDA1` 中，父调用764的 p50 为48.282/95.86，p95为60.698099999999975/190.94179999999997（reference/current）。当QA询问p95时，H_MARGINAL_PHASE回答了**正好对应p50的48.282/95.86**；子调用也发生相同口径替换。这是可核对的统计行错配，而非画布缺少p95。需要注意：这是输入PNG，模型之后还会经历已登记的视觉编码和token保留。

同一病例该臂最终RCA仍将231排第一并命中根因。因而“当前QA没读对边际图”不自动等于“这次RCA一定失败”；其他Trace事实可以支持正确排名。反过来，它也提示边际图中的新增统计未必被真正使用。

### 9.2 关系题：读到端点与完整连接并不相同

V_POD_BRIDGE 的关系exact-set宽容正确率62/180=34.44%，端点precision/recall为49.22%/50.11%；V_POD_SEPARATE为86/180=47.78%，端点precision/recall为61.30%/69.54%。部分回答找对某些端点，但漏掉其他端点、混入另一类型实体或反转方向。

[实际pod连接图](artifacts/RQ4_6_2026-10-19/example_pod_INC-8991CE65FDA1.png) 对应同一病例的公开部署来源。H_POD_PHASE在询问service309经pod关联到哪些node时，返回pod ID `[17244,89071]`，而目标node集合为 `[4624,6856,8767]`。V_POD_BRIDGE另在询问pod84528的 `incoming_hosts` 时返回 `[237,24441]`，真实目标是node3927；237实际是service。图中关系存在且方向可核对；长表式重复行可能使查找困难，但本轮没有独立隔离“重复行/密度”这一原因。

`INC-32757906019C` 的V_POD_BRIDGE六道关系QA全部正确，却在最终RCA中输出 `[524,56767,40630,9777,52792]`，遗漏故障pod59583。**关系检索成功不保证能够在这些关系上作出正确故障归因。**

### 9.3 数值与实体绑定、单位接口要拆开

P_U_VALUE_BLOCK 数值读取正确率31.40%，高于U_QA的27.91%；但实体字段正确率73.26%，低于U_QA的79.07%，完整联合正确率14.53%，低于U_QA的16.86%。组合剪枝的数值正确率也为31.40%，联合正确率只有12.21%。因此单看数字读取会掩盖绑定损失。

实际数值2627.1来自365的Trace记录，但某回答给出另一操作710.231作为owner；另有RCA将TRC01实际属于231、current约107622.1µs的耗时归给764。这是来源核对后的实体错配，不是只依据评分器说错。

同时存在 `source unit` 与 `source_unit` 等字符串不一致：登记宽容别名仅覆盖既定单位映射，没有把这些写法等同。事后仅放宽空格/下划线，完整联合题正确率为VALUE 19.77%、NEIGHBOR 22.09%、COMBINED 19.19%、U 22.09%。这说明QA的部分损失属于接口读法；原分不被改写，也不能将所有差异都解释为视觉认知能力。

### 9.4 QA—RCA 的关联证据及限制

探索族七项QA比较中，H_POD_BRIDGE−H_POD_SEPARATE 的病例平均宽容QA为+0.1222，Holm pH=0.0085；对应完整RCA矩阵ΔMRR为−0.0023。这个配对结果支持“读取任务的改善不必然转化为诊断提升”，但没有证明两者独立或找出全部中介。

所有臂内QA与RR的Spearman相关均未达到未校正p<0.05；例如H_MARGINAL_PHASE ρ=0.0129、p=0.9459。30例功效有限，且QA只覆盖部分事实；零相关估计不能当作读取永远不重要。

一个关键代表性限制：固定子集中的10个AegisLab病例，H_MARGINAL_PHASE相对旧H_MARGINAL的RR差**全部为0**，而全100例差为−0.0730。故不能用这批QA直接解释全体AegisLab损失；上节的AegisLab损失病例是另外标记的事后追踪。

### 9.5 理由与排名也可能脱节

`INC-92A00B34EECF` 的H_MARGINAL_PHASE输出 `[772,728,927,966,852]`，第一名772是可接受根因；但理由主要论证927最早/最上游，并把728/772说成并行或下游影响。**正确首选与不支持该首选的解释可以同时存在。**

解释中还出现由较早异常、调用上游或较大z-score直接推断根因的做法。没有额外时钟/干预证据时，这些只能作为模型提出的推断，不能由报告替它证明。公开理由不等于忠实的内部推理轨迹；本轮未建立解释可信度整体提高。

## 10. Attention：实际采到了什么，能说明什么

正式阶段保留716份唯一实测attention文件；对应720个登记测量位置中4个精确引用共享原测量。所有记录均成功，有两个query样本，层号为3：最后一个prompt query、首个decode query。**没有采集实际最终排名字段的token attention，也没有完整attention矩阵。**

区域按真实processor网格、逐图gather及原面板几何对应；本次重建并检查区域名称/维度、保留token计数和概率质量归一化。smoke中的映射哈希核验保持原记录；本次不将逐正式请求重新计算全部token级映射哈希描述成已完成的额外审核。

![Attention覆盖](artifacts/RQ4_6_2026-10-19/attention_scope.png)

下表仅汇总主RCA的唯一实际测量，不重复计算引用：''')
at={(x['arm'],x['stage']):x for x in D['attention'] if x['variant']=='BASE'}
table(['Arm','n','文本token占比','末prompt文本mass','末prompt图像mass','首decode图像mass'],[
[a,at[a,'last_prompt']['n'],pct(at[a,'last_prompt']['text_token_share']),pct(at[a,'last_prompt']['text_mass']),pct(at[a,'last_prompt']['image_mass']),pct(at[a,'first_decode']['image_mass'])] for a in arms])
add('''纯视觉文本只有任务/读图/输出说明，约占保留输入token的7.5%–7.6%，却获得约86%的末prompt查询mass；hybrid文本本身承载诊断信息，不能用同一解释比较两类文本mass。Attention既受查询位置/层影响，也不等于因果使用程度。

全局页眉在本轮A/E保留集合中的token数为0，因此页眉mass为0是结构性结果；这不能证明解决了历史“标题sink”。面板标题被合并在面板区域统计中，本轮无法单独区分其mass。

三个剪枝臂的粗粒度图像mass非常接近，但排名不同，说明这个区域聚合读数本身不足以解释排名差。不能据此自动删除文本、删除高attention位置或宣称新剪枝更关注根因。''')
add(f"正式attention记录本体共 **{D['attention_record_bytes']:,}字节**，最大单份 **{D['attention_max_record_bytes']:,}字节**；按测量所需几何/保留索引去重计算的映射信息约 **{D['attention_mapping_bytes_dedup']/1e6:.3f} MB**，两者合计约 **{(D['attention_record_bytes']+D['attention_mapping_bytes_dedup'])/1e6:.3f} MB**。按2,601次真实正式调用外推约 **{(D['attention_record_bytes']+D['attention_mapping_bytes_dedup'])/2601*10000/1e9:.3f} GB/万次**，低于attention专项预算。这里是记录及相应映射的分析口径，最终整个实验的存储审计仍未通过，不能与其混淆。")
add('''## 11. 运行效率与失败分母

完整正式生命周期12,874.96秒，即 **3小时34分35秒**；2,601次真实调用，平均 **12.12 calls/min**，超过此前登记的7 calls/min目标。没有为错误排名重试，没有KV抢占记录；所有基础设施位置已解决。

下表为真实调用的平均在线耗时，包含并发调度下请求等待；正式输入已经CPU准备完成。不同阶段存在并发，**不能把均值逐项相加当作串行冷启动耗时**。没有重新从原始遥测编译绘图的完整冷路径测量，也没有可用于本报告的全时段功耗/利用率序列。''')
table(['Arm','输入至验证均值s','P95 s','视觉编码均值s','语言模型阶段均值s','在线准备均值s'],[[a]+[f"{A[a,'all'][k]:.2f}" for k in ['input_to_validation_mean','input_to_validation_p95','vision_seconds_mean','language_seconds_mean','prepare_seconds_mean']] for a in arms])
add('''纯视觉视觉编码约2.44秒，hybrid约0.14–0.43秒；但每个并发请求总在线均值约37–42秒，未按输入token同比变化。因此本轮明确建立的是token成本下降与可用吞吐，未建立相对历史方法同负载、同冷路径的加速比例。

## 12. 决策：保留什么，停止什么，下一步查什么

### 12.1 本轮采用判断

| 预选方法 | 排名目标 | 成本目标 | 结论 |
| --- | --- | --- | --- |
| H_POD_PHASE | 0.4406低于旧H_MARGINAL 0.4912；未达到＋0.02及逐数据集不退化 | 总token约12.835k，成本目标通过 | 不替换旧方法；保留降本实现与子群观察 |
| V_POD_BRIDGE | 0.2771低于U 0.3517；对同期separate亦更差 | 约1.029×U，成本目标通过 | 本候选结束，不能宣称pod连接改善纯视觉 |
| P_U_COMBINED | 0.3055低于U；对NEIGHBOR有显著负差 | 约1.000×U，成本目标通过 | 不采用组合目标，不继续仅提高同一代理分数 |

H_MARGINAL_PHASE和P_U_NEIGHBOR_PAIR是本轮事后较高均值条件，不被追认为新的预选成功方法。历史MARGINAL_FIVE、H_MARGINAL及U的各自作用继续保留。

### 12.2 建议的下一步，尚未执行或注册新调用

**先围绕低成本hybrid恢复排名，暂不扩展新的布局/剪枝网格。** 本轮已拿到约39%的token余量；更有价值的问题是哪些少量被删信息或读数设计能恢复AegisLab损失，而不是再把已经完整可见的关系组合得更复杂。

1. 对 H_MARGINAL_PHASE 相对旧 H_MARGINAL 的26个RR下降病例，离线逐项区分：证据被删、仍存在但读错、口径/实体错配、推理取舍变化。把旧回答理由也对回来源，不以“旧排名正确”替代核验。对15个修复病例做同样检查，避免只挑负例。
2. 下次若立项，保留旧H_MARGINAL历史参照，设置**同一预算投影下的原边际图控制**，再只改变一个针对性补充（例如恢复有明确损失证据的局部时序细节或纠正p50/p95视觉分组）。具体规则需标签盲、由公共输入决定，不能按本次正确根因路由，也不能把事后看到的损失病例当作独立确认集。
3. 纯视觉保留U作为已知起点；只有获得能解释数值/来源错配的具体机制证据，才推进下一种剪枝。当前完整数值块和邻域目标都没有超过U，不再因目标值高就自动扩大优化。
4. 保留QA支线但缩小主张：增加与实际损失类型相符的固定测量设计时，应在下一协议中冻结；不在本报告中替换不具代表性的原30例来制造关联。输出约束、单位别名或宽容评分修订也需单独登记，历史标准分保持不变。
5. 先完成可恢复的存储收官修复，再清理冗余。该工作不需要重新生成模型回答；不应占用新的科学调用预算。

这些建议以“提高MRR，同时保住已有降本收益”为下一阶段优先事项；本次仅分析，没有启动后继实验。当前数据均已反复暴露，任何后续方法成立后仍需冻结后的合格验证。

## 13. 归档问题：结果完整，自动精简尚未完成

所有调用完成后，worker在 `finish_formal → finalize_retention → retire_preparation_duplicates` 抛出：

```text
ValueError: Preparation request has no exact frozen deployment input
```

只读检查发现，回收逻辑扫描了所有CPU准备的mechanism请求，却只用正式队列请求作为覆盖依据。机制准备包含32例，正式QA只使用30例；额外两例的22个请求中，4个用于smoke、18个仅为CPU准备，因此无法在正式队列中找到。**这是收官覆盖范围不一致，不是22个正式结果丢失。** 保护检查在删除前失败，本报告没有执行清理、覆盖结果或重新推理。

按唯一inode去重后的当前结果目录大小如下；硬链接只算一次，目录归属是审计时的首次归属，不应解释为每目录独立可释放空间。''')
table(['当前产物','十进制GB'],[[k,f"{S['storage_unique_bytes'][k]/1e9:.3f}"] for k in ['objects','cache','inputs','frozen','formal','mechanism','qualification']])
add(f"总计 **{S['storage_unique_total']/1e9:.3f} GB**。累计实际完成2,619次（含smoke），允许最终预算为 **6.5475 GB**；引用不增加分母。以上尚未加上本报告的少量派生附件，且最终审计还应覆盖实验专属外部输入依赖，因此不能把当前目录统计当作最终合规证明。没有有效的最终 `retention.json`，状态为 **待修复收官**。所有已采集attention、完整请求/图像/输出/会话/评分映射必须继续保留，不能为达标修改输入或统计协议。")
add('''## 14. 可复核材料与复算方式

正式协议：[RQ4.6计划](../experiment_plans/RQ4_6_Pod_Bound_Relation_Join_Plan_2026-10-19.md)；[冻结清单](../../RQs/RQ4_6/results/pod_join_v1/frozen/manifest.json)；[唯一findings](../../RQs/RQ4_6/findings/exp_pod_join_findings.md)。

报告的全部数字来自下列直接可读文件：''')
for file,desc in [('analysis.json','完整汇总与核验计数'),('metrics_cost_timing.csv','逐臂/数据集完整排名、成本和时间'),('per_case.csv','2,200行主矩阵逐病例数据'),('primary_statistics.json','主要比较的两套推断单位'),('paired_repairs.csv','逐数据集修复/破坏'),('paired_case_deltas.csv','所有登记与历史比较的病例差'),('repeats.json','重复稳定性'),('qa_field_audit.json','全部适用QA逐字段原答案/oracle'),('qa_rca_answers.json','330份QA与对应RCA完整回答'),('fixed30_answers.md','按固定病例阅读原始回答的导航'),('focused_response_audit.json','定向8病例的完整回答与来源请求'),('manual_review_notes.md','人工检查范围与定性证据'),('attention_per_query.csv','每份实测query的区域统计'),('attention_summary.csv','attention分组汇总'),('selection_geometry.csv','剪枝代理目标与实际RR变化'),('supplement.json','敏感性、子集代表性及存储审计'),('provenance.json','来源指纹')]:
    add(f'- [{desc}]({rel}{file})')
add('''复算命令（只读原实验；写入报告派生表，无模型请求、无renderer、无清理）：

```bash
cd /home/lglsj/CanvasRCA_nibi
source RQs/RQ4_6/scripts/runtime_environment_local.sh
CUDA_VISIBLE_DEVICES='' "$rq46_python" -B docs/experiment_reports/artifacts/RQ4_6_2026-10-19/analyze.py
CUDA_VISIBLE_DEVICES='' "$rq46_python" -B docs/experiment_reports/artifacts/RQ4_6_2026-10-19/supplement.py
CUDA_VISIBLE_DEVICES='' "$rq46_python" -B docs/experiment_reports/artifacts/RQ4_6_2026-10-19/make_figures.py
python3 docs/experiment_reports/artifacts/RQ4_6_2026-10-19/write_report.py
```

上述脚本会再次检查冻结源码和当前缓存侧的来源记录；未来完成归档后若准备缓存被按规则删除，应按最终保留索引解析同一对象，不能因旧目录不存在而重新生成答案。报告附件中的逐病例表与原答案快照可直接阅读。图表使用普通PNG/SVG；两个实际输入例图使用已校验的硬链接，不引入另一份物理副本。

**最终状态：完整正式矩阵及详细分析完成，新增调用0；三个预选方法均未达到工程排名目标；存储自动收官仍待修复。**''')
OUT.write_text('\n'.join(chunks))
print(OUT)
