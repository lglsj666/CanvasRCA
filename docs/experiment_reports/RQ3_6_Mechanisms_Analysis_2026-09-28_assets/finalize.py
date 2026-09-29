"""Report-only tables, conservative multiplicity sensitivity and case index.

No model calls, imports of experiment runners, or modifications to source results.
Run after analyze.py and explore.py. Labels remain evaluator-private here.
"""
from pathlib import Path
import json
import shutil

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
M = pd.read_csv(OUT/'arm_metrics.csv')
T = pd.read_csv(OUT/'paired_tests.csv')
R = pd.read_csv(OUT/'per_record.csv', dtype={'first_id': str})
P = pd.read_csv(OUT/'pattern_metrics.csv')
MODELS = ['qwen3.8-27b', 'gemma-4-26b-a4b']
FAMS = ['g_components', 'scope_competition', 'relation_binding']
SHORT = dict(zip(MODELS, ['Qwen', 'Gemma']))


def table(df):
    """Markdown without an optional tabulate dependency."""
    def cell(x):
        if isinstance(x, (float, np.floating)):
            return '—' if pd.isna(x) else f'{x:.4f}'
        return str(x).replace('|', '\\|').replace('\n', ' ')
    return '\n'.join(['| '+' | '.join(map(str, df.columns))+' |',
                      '| '+' | '.join(['---']*len(df.columns))+' |',
                      *['| '+' | '.join(cell(x) for x in row)+' |'
                        for row in df.itertuples(index=False, name=None)]])


def holm(frame, dest):
    bound = 0.
    for i, (ix, row) in enumerate(frame.sort_values('p').iterrows()):
        bound = max(bound, min(1., row.p*(len(frame)-i)))
        frame.loc[ix, dest] = bound
    return frame


carrier = holm(T[T.stat_family.str.startswith('carrier_')].copy(), 'holm_all_34')
assert len(carrier) == 34
carrier.to_csv(OUT/'carrier_global_holm.csv', index=False)
main = M[(M.population == 'common') & (M.split == 'all') & (M.scope == 'macro')]
pieces = ['# 完整数值附录', '', '自动生成。common 为实验×模型的全 arm 共同病例集；模型输出失败保留零分。', '']
for fam in FAMS:
    pieces += ['## '+fam, '']
    for model in MODELS:
        q = main[(main.family == fam) & (main.model == model)]
        pieces += ['### '+SHORT[model], '', table(q[['arm','n','mrr','ac@1','ac@3','ac@5','avg@3','avg@5']]), '']
    q = M[(M.population == 'common') & (M.split == 'all') & (M.family == fam)
          & M.scope.isin(['aiops2022','aiops2025','aegislab','aiops_combined'])]
    q = q.pivot(index=['model','arm'],columns='scope',values='mrr').reset_index()
    pieces += ['### 数据集及两 AIOPS 合并 MRR', '', table(q), '']
pieces += ['## 全部配对检验', '', table(T[['stat_family','model','contrast','n','delta','macro_delta','p','holm','dz','group_n','group_holm']]), '',
           '## 完整成本表', '', table(main[['family','model','arm','input_tokens','text_tokens','image_tokens','output_tokens','wall_time_s','ttft_s','decode_time_s']]), '',
           '## 三实验所有图文比较作为一个事后 family 的保守敏感性分析', '',
           table(carrier[['family','model','contrast','delta','p','holm','holm_all_34']]), '']
(OUT/'full_tables.md').write_text('\n'.join(pieces), encoding='utf-8')

# Label-conditioned explanation of onset/rank removal; never a deployment router.
g = pd.read_csv(OUT/'g_source_features.csv')
d = pd.read_csv(OUT/'paired_case_deltas.csv')
z = d[(d.family=='g_components') & d.contrast.isin([
    'NO_ONSET-FULL_T','NO_ONSET-FULL_G','NO_RANK-FULL_T','NO_SEVERITY-FULL_G'
])].merge(g, on='case', suffixes=('','_g'))
summaries=[]; tests=[]
for feature in ['root_in_G','root_G_earliest','root_G_rank1']:
    for (model,contrast), sub in z.groupby(['model','contrast']):
        a=sub[sub[feature]].delta; b=sub[~sub[feature]].delta
        tests.append(dict(feature=feature,model=model,contrast=contrast,
                          true_n=len(a),false_n=len(b),true_delta=a.mean(),false_delta=b.mean(),
                          p=mannwhitneyu(a,b,alternative='two-sided').pvalue))
        for ds in ['all','aiops2022','aiops2025','aegislab']:
            q=sub if ds=='all' else sub[sub.dataset==ds]
            for value,ss in q.groupby(feature):
                summaries.append(dict(feature=feature,model=model,contrast=contrast,dataset=ds,
                                      value=bool(value),n=len(ss),delta=ss.delta.mean()))
pd.DataFrame(summaries).to_csv(OUT/'g_summary_alignment.csv',index=False)
holm(pd.DataFrame(tests),'holm').to_csv(OUT/'g_alignment_heterogeneity.csv',index=False)

# Actual reviewed cases: paired examples of both benefit and harm, not a prevalence sample.
cases = [
 ('C01','g_components','qwen3.8-27b','INC-A5BE8AEFA87F',['FULL_T','NO_ONSET_T'],
  '移除 G onset 后转向 restart 与内存下降',
  '原回答围绕746的+4.0m和999构造源头；新回答选33542，service级585标签命中。输入确有restart 0→1及585 RSS约762.6M→273.4M；这支持状态信号被重新重视。数据库故障传播的延伸解释未由这些数值单独证实。'),
 ('C02','g_components','qwen3.8-27b','INC-E518E9800304',['FULL_T','NO_ONSET_T'],
  '移除 onset 也会丢失有用的竞争排序',
  '488从第一掉到第三，模型改选9852；磁盘/inode与pod异常本来就存在。原G的488 +22m和调用边支持对比，但不证明其物理因果方向。此反例反对全局删除onset。'),
 ('C03','scope_competition','qwen3.8-27b','INC-5EADA73E94EC',['ANCHOR_T','HOST_T'],
  'HOST 修复不等于新增根因宿主观测',
  '标签node 9013，新加host数据实际属于1447/7497；新回答依赖原有9013 rank1/onset，且称其Service。ID命中，但不是新增了9013的直接遥测。'),
 ('C04','scope_competition','qwen3.8-27b','INC-D3EAA310B962',['ANCHOR_T','HOST_T'],
  '补充真实 host 信息也可能引发上下文干扰',
  '437由第一变为前五外；新增8005 UDP中位数21.57→47.28被重复三次，另有5026 CPU10.21→11.38。新回答没选择这两个host，而改选原G中rank1的717。只能支持上下文改变伴随重排，不能认定某一新增数值必然致错。'),
 ('C05','scope_competition','gemma-4-26b-a4b','INC-CCCFF766DA4B',['PEER_G','HOST_PEER_G','HP_DEDUP_G'],
  '同一图片下，宿主重复证据与粒度竞争',
  '预测57600→7458→57600；三PNG字节相同。HOST_PEER重复7458 CPU10.6→16.16两次、4668 load1.24→1.485两次；DEDUP保留唯一事实而去掉重复。PEER虽ID正确，reason主要指向node；DEDUP reason才明确把pod文件系统增加视为源头。'),
 ('C06','relation_binding','gemma-4-26b-a4b','INC-7D95F2013B97',['ALL_ID_T','ALL_ID_G'],
  '图像修复：CPU pod 对比微小但高σ的 JVM 变化',
  'T选997，G选正确pod31316。M中31316 CPU baseline0.1225、peak22.53；997 Tenured Gen仅约62.5M→62.7M但deviation约1.5k。T还误称31316为node；PNG明确把31316放pod列、6825放node列。G的精确onset和CFS throttling表述不应全盘照信。'),
 ('C07','relation_binding','gemma-4-26b-a4b','INC-97ECDC5FFBD8',['ALL_ID_T','ALL_ID_G'],
  '图像退化：宿主证据仍存在，模型选择局部高强度症状',
  'T正确选node6063；G选pod59591。两者均有6063内存中位数79.86→58.25；PNG保留6063但为孤立节点，59591 CPU/Trace为共同文本。G理由引用真实CPU327σ及exclusive latency，但不能因此证明pod是源头。'),
 ('C08','relation_binding','gemma-4-26b-a4b','INC-EF768AE9D329',['ALL_ID_T','ALL_ID_G'],
  '正确提名不代表故障机制解释正确',
  'T选289，G选97990，按service兼容评分命中301/adservice。M确有97990工作集尖峰；私有fault为jvm exception，reason却称memory exhaustion，并无足够证据把异常内存观测升级为已证实故障机制。'),
 ('C09','relation_binding','gemma-4-26b-a4b','INC-D02CFDF1A4AE',['ALL_ID_T','ALL_ID_G'],
  '图像退化伴随无依据调用关系',
  'T选接受标签211，G选791。791确有rrt_max大幅变化，但显式图边/ledger没有211→791；G却称791为211依赖及公共瓶颈。T的reason同样混淆caller方向；排名与解释必须分开核验。'),
 ('C10','relation_binding','gemma-4-26b-a4b','INC-6E6E1B20F2D5',['ALL_ID_T','ALL_ID_G'],
  '图像修复 node CPU，但实体类型称呼仍错',
  'T选802，G正确选node8820；共同文本有8820 CPU baseline18.47、peak96.45。802 filesystem极小变化却有极大σ。G公开reason称8820为Service；正确ID不保证层次理解或每项时间陈述正确。'),
]
review = []; md = ['# 逐案例人工审阅', '',
 '选择规则：从差值表和哈希抽取候选中覆盖收益/损失、两模型、三数据集，再按机制挑选10个病例、21份条件记录。这是目的性审阅，不估计总体错误比例。下列原始prompt/response/conversation链接为证据；ID与标签仅供离线分析。', '']
for cid, fam, model, case, arms, title, note in cases:
    recs=[]
    for arm in arms:
        r = R[(R.family==fam)&(R.model==model)&(R.case==case)&(R.arm==arm)].iloc[0]
        j = json.loads((ROOT/r.prompt_path).read_text())
        imgs=[]
        for part in j['parts']:
            if part.get('type')=='image':
                src = ROOT/r.artifact_root/part['image_path']
                assert src.is_file()
                imgs.append(str(src.relative_to(ROOT)))
                if cid in ['C05','C06','C07','C09'] and arm==arms[-1]:
                    shutil.copyfile(src, OUT/f'{cid}_actual_input.png')
        recs.append(dict(arm=arm,mrr=r.mrr,predictions=json.loads(r.predictions),reason=r.reason,
                         prompt=r.prompt_path,output=r.output_path,conversation=r.conversation_path,images=imgs))
    private=json.loads((ROOT/f'RQs/RQ3_4/results/integrated_v1/private/{case}.json').read_text())
    item=dict(id=cid,family=fam,model=model,case=case,dataset=r.dataset,fault_type=r.fault_type,
              root_ids=private['accepted_label_numeric_ids'],title=title,assessment=note,records=recs)
    review.append(item)
    md += [f'## {cid}｜{title}', '', f'`{case}` · {r.dataset} · {SHORT[model]} · {r.fault_type}', '',
           '离线接受标签：`'+json.dumps(item['root_ids'],ensure_ascii=False)+'`。', '', note, '']
    for rec in recs:
        links=' · '.join(f'[{label}](../../../{rec[key]})' for label,key in [('输入','prompt'),('回答','output'),('conversation','conversation')])
        md += [f"### {rec['arm']}：RR={rec['mrr']:.4f}；预测={rec['predictions']}", '', links, '',
               '> '+str(rec['reason']).replace('\n','\n> '), '']
    image_path=OUT/f'{cid}_actual_input.png'
    if image_path.exists():md += [f'![{cid} 模型收到的原图]({image_path.name})', '']
(OUT/'reviewed_cases.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'case_review.md').write_text('\n'.join(md),encoding='utf-8')

# Granularity is diagnostic stratification, not an available inference-time label.
fig,axs=plt.subplots(1,2,figsize=(12,4.5))
levels=['node','pod','pod+service','service']
for ax,model in zip(axs,MODELS):
    for arm,off,color in [('ALL_ID_T',-.18,'#4279a8'),('ALL_ID_G',.18,'#df823c')]:
        q=P[(P.family=='relation_binding')&(P.model==model)&(P.arm==arm)&(P.dataset=='all')&(P.stratum=='root_level')].set_index('value').loc[levels]
        bars=ax.bar(np.arange(4)+off,q.mrr,width=.36,label=arm,color=color)
        ax.bar_label(bars,fmt='%.3f',fontsize=8,padding=3)
        ax.set_xticks(range(4),[f'{x}\nn={n}' for x,n in zip(levels,q.n)])
    ax.set_ylim(0,.65);ax.set_title(SHORT[model]);ax.set_ylabel('MRR');ax.legend(fontsize=8)
fig.suptitle('Relation binding: same observations, T vs typed graph + ledger')
fig.tight_layout();fig.savefig(OUT/'06_root_granularity.png',dpi=180);plt.close(fig)

# Avoid duplicate tick labels overlapping the neighboring heatmap.
fig,axs=plt.subplots(1,2,figsize=(12,11),sharey=True,layout='constrained')
for ax,model in zip(axs,MODELS):
    q=M[(M.model==model)&(M.population=='common')&(M.split=='all')&M.scope.isin(['aiops2022','aiops2025','aegislab'])].copy()
    q['label']=q.family.str[:1]+':'+q.arm
    q=q.pivot(index='label',columns='scope',values='mrr')[['aiops2022','aiops2025','aegislab']]
    im=ax.imshow(q,aspect='auto',vmin=0,vmax=.85,cmap='YlGnBu')
    ax.set_yticks(range(len(q)),q.index,fontsize=8);ax.set_xticks(range(3),q.columns,fontsize=8)
    ax.set_title(SHORT[model])
    for i in range(len(q)):
        for j in range(3):ax.text(j,i,f'{q.iloc[i,j]:.2f}',ha='center',va='center',fontsize=8,color='white' if q.iloc[i,j]>.6 else 'black')
fig.colorbar(im,ax=axs,shrink=.65,label='MRR');fig.savefig(OUT/'02_datasets.png',dpi=180);plt.close(fig)

fig,axs=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
annotate={'FULL_T','FULL_G','NO_SEVERITY_G','STRUCTURE_G','ANCHOR_T','HOST_PEER_G','ALL_ID_T','ALL_ID_G','DEPLOY_ID_T'}
for ax,model in zip(axs,MODELS):
    for fam,color in zip(FAMS,['#2878b5','#dc8237','#398255']):
        q=main[(main.model==model)&(main.family==fam)]
        for suffix,marker in [('T','o'),('G','^')]:
            sub=q[q.arm.str.endswith('_'+suffix)]
            ax.scatter(sub.input_tokens,sub.mrr,c=color,marker=marker,s=35,label=fam if suffix=='T' else None)
        for _,r in q[q.arm.isin(annotate)].iterrows():
            ax.annotate(r.arm,(r.input_tokens,r.mrr),xytext=(4,4),textcoords='offset points',fontsize=7)
    ax.set_title(SHORT[model]+' (circle=T; triangle=G)');ax.set_xlabel('Mean total input tokens');ax.set_ylabel('Macro MRR');ax.legend(fontsize=7,loc='best');ax.margins(x=.12,y=.15)
fig.savefig(OUT/'04_cost_quality.png',dpi=180);plt.close(fig)

# Diagnostic facts, not post-hoc correction of any experiment score.
print('global carrier min:',carrier.sort_values('p')[['model','contrast','holm_all_34']].head(1).to_dict('records'))
print('reviewed cases',len(review),'record comparisons',sum(len(x['records']) for x in review))
print('written full_tables.md, case_review.md, reviewed_cases.json, 06_root_granularity.png')
