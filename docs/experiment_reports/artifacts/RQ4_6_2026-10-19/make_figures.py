"""Plot retained offline aggregates only; no experiment execution."""
from pathlib import Path
import json
import hashlib
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

P = Path(__file__).resolve().parent
ROOT = P.parents[3]
D = json.loads((P / 'analysis.json').read_text())
A = {x['arm']: x for x in D['aggregates'] if x['dataset'] == 'all'}
H = {x['arm']: x for x in D['historical'] if x['dataset'] == 'all'}
plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False,
                     'savefig.dpi': 160, 'svg.fonttype': 'none'})

def save(fig, name):
    fig.savefig(P / (name + '.png'), bbox_inches='tight')
    fig.savefig(P / (name + '.svg'), bbox_inches='tight')
    plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(13, 5.6), gridspec_kw={'width_ratios': [1, 1.3]})
offsets = {'H_DEPLOY_ONLY': (8, -10), 'H_MARGINAL_PHASE': (-22, 12),
           'H_POD_BRIDGE': (-83, -27), 'H_POD_SEPARATE': (12, -2), 'H_POD_PHASE': (-110, 7)}
for arm, x in A.items():
    color = '#2278a8' if arm.startswith('H_') else '#d27b2c'
    axes[0].scatter(x['total_tokens']/1000, x['standard_mrr'], c=color, s=50, zorder=3)
    if arm.startswith('H_'):
        axes[0].annotate(arm.replace('H_', ''), (x['total_tokens']/1000, x['standard_mrr']),
                         xytext=offsets[arm], textcoords='offset points', fontsize=8)
for arm, x in H.items():
    axes[0].scatter(x['total']/1000, x['mrr'], marker='*', s=120, c='#626262', zorder=3)
    axes[0].annotate(arm, (x['total']/1000, x['mrr']), xytext=(-15, 10), textcoords='offset points', fontsize=8)
axes[0].set(xlabel='Mean input + output tokens (thousands)', ylabel='Standard MRR',
            title='Cost vs. ranking: full 220 cases', xlim=(4, 26), ylim=(.24, .54))
arms = list(A)
y = np.arange(len(arms))
axes[1].barh(y-.17, [A[a]['standard_mrr'] for a in arms], height=.32, color='#2278a8', label='Standard')
axes[1].barh(y+.17, [A[a]['tolerant_mrr'] for a in arms], height=.32, color='#e5ac67', label='Tolerant')
axes[1].set(yticks=y, yticklabels=arms, xlabel='MRR', xlim=(0, .54), title='Interface penalties do not explain all losses')
axes[1].invert_yaxis()
axes[1].legend(loc='lower right')
for ax in axes: ax.grid(axis='x', alpha=.15)
fig.tight_layout(w_pad=2)
save(fig, 'ranking_cost')

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
datasets = ['aiops2022', 'aiops2025', 'aegislab']
for ax, arms, base in zip(axes, [list(A)[:5], list(A)[5:]], ['H_MARGINAL', 'A_UNIFORM_E50']):
    for i, arm in enumerate(arms):
        vals = [next(x['standard_mrr'] for x in D['aggregates'] if x['arm']==arm and x['dataset']==ds) for ds in datasets]
        ax.plot(np.arange(3)+i*.012, vals, '-o', label=arm, alpha=.85)
    vals = [next(x['mrr'] for x in D['historical'] if x['arm']==base and x['dataset']==ds) for ds in datasets]
    ax.plot(range(3), vals, 'k--s', label=base+' (historical)', linewidth=2)
    ax.set(xticks=range(3), xticklabels=['AIOPS-2022', 'AIOPS-2025', 'AegisLab'], ylabel='Standard MRR', ylim=(.15, .70))
    ax.legend(fontsize=8, loc='upper left')
    ax.grid(alpha=.15)
axes[0].set_title('Hybrid: AegisLab is the main regression')
axes[1].set_title('Pure visual: no new arm exceeds historical U')
fig.tight_layout()
save(fig, 'dataset_mrr')

Q = {(x['arm'],x['family']):x for x in D['qa_components']}
fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
arms=list(A)[:5]; x=np.arange(len(arms))
axes[0].bar(x-.18,[Q[a,'numeric']['numeric_correct'] for a in arms],.34,label='Exact values',color='#2278a8')
axes[0].bar(x+.18,[Q[a,'relation']['tolerant'] for a in arms],.34,label='Relation exact set (tolerant)',color='#e5ac67')
axes[0].set(xticks=x,xticklabels=[a.replace('H_', '') for a in arms],ylim=(0,1.04),ylabel='Question-level rate',title='Hybrid QA: duration readout falls after visual handoff')
axes[0].tick_params(axis='x',labelrotation=20)
arms=['U_QA','P_U_VALUE_BLOCK','P_U_NEIGHBOR_PAIR','P_U_COMBINED'];x=np.arange(4)
for j,(k,label,color) in enumerate([('numeric_correct','Exact values','#2278a8'),('entity_correct','Correct entity','#75a6c0'),('tolerant','Joint answer','#e5ac67')]):
    axes[1].bar(x+(j-1)*.23,[Q[a,'numeric'][k] for a in arms],.22,label=label,color=color)
axes[1].set(xticks=x,xticklabels=['U QA','VALUE','NEIGHBOR','COMBINED'],ylim=(0,1.04),title='Pruning QA: values and binding are different outcomes')
for ax in axes: ax.legend(fontsize=8);ax.grid(axis='y',alpha=.15)
fig.tight_layout()
save(fig,'qa_components')

fig,ax=plt.subplots(figsize=(11,5.5));arms=list(A);y=np.arange(10)
at={x['arm']:x for x in D['attention'] if x['variant']=='BASE' and x['stage']=='last_prompt'}
ax.barh(y,[at[a]['text_mass'] for a in arms],color='#2278a8',label='Attention mass: text')
ax.barh(y,[at[a]['image_mass'] for a in arms],left=[at[a]['text_mass'] for a in arms],color='#e5ac67',label='Attention mass: image')
ax.scatter([at[a]['text_token_share'] for a in arms],y,c='black',marker='|',s=150,label='Text share of retained input tokens',zorder=4)
ax.set(yticks=y,yticklabels=arms,xlim=(0,1.03),xlabel='Share (0–1)',title='Layer 3, last prompt query only; not final ranking attention')
ax.invert_yaxis();ax.legend(fontsize=8,loc='upper left',bbox_to_anchor=(0,-.12),ncol=3)
fig.tight_layout();save(fig,'attention_scope')

# Exact model-visible PNGs; hard links avoid another physical copy.
for source, target in [
 ('399f8638484a233e9d60a2c83b3c2502f3b38d4c29c0077d6fadc6451af2e4c2.png','example_phase_INC-8991CE65FDA1.png'),
 ('5562437b457abe7f180481abe8cb816406dd86a1ea0f83c5701c2f0f280b9bfa.png','example_pod_INC-8991CE65FDA1.png')]:
    src=ROOT/'RQs/RQ4_6/results/pod_join_v1/objects'/source;dst=P/target
    assert hashlib.sha256(src.read_bytes()).hexdigest()==source[:-4]
    if not dst.exists():os.link(src,dst)
    assert hashlib.sha256(dst.read_bytes()).hexdigest()==source[:-4]
print('Four figure pairs and two verified exact-input examples saved.')
