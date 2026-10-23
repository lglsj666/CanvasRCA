from pathlib import Path
import json,csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
P=Path(__file__).resolve().parent;s=json.loads((P/'analysis.json').read_text())
order=['H_MARGINAL','H_TOPOLOGY','H_TOPO_MARGINAL','V_DOMAIN_FULL','V_SOURCE_UNIFORM','V_CONTEXT_FILL']
short={'H_MARGINAL':'H-M','H_TOPOLOGY':'H-T','H_TOPO_MARGINAL':'H-TM','V_DOMAIN_FULL':'V-D','V_SOURCE_UNIFORM':'V-S','V_CONTEXT_FILL':'V-C','T_FULL':'T_FULL*','MARGINAL_FIVE':'MARGINAL_FIVE*','A_UNIFORM_E50':'U*'}
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':160})
def save(name):
 plt.savefig(P/(name+'.png'),bbox_inches='tight');plt.savefig(P/(name+'.svg'),bbox_inches='tight');plt.close()
fig,ax=plt.subplots(figsize=(9,4.7));new={x['arm']:x for x in s['aggregates'] if x['dataset']=='all'}
for a in order:
 x=new[a];c='#168f83' if a.startswith('H_') else '#6254b5';ax.scatter(x['total_tokens']/1000,x['standard_mrr'],c=c,s=65,marker='o');ax.annotate(short[a],(x['total_tokens']/1000,x['standard_mrr']),xytext={'H_MARGINAL':(-5,8),'H_TOPOLOGY':(4,-13),'H_TOPO_MARGINAL':(-40,-12),'V_DOMAIN_FULL':(6,8),'V_SOURCE_UNIFORM':(7,-10),'V_CONTEXT_FILL':(7,-6)}[a],textcoords='offset points')
for x in s['historical']:
 if x['dataset']!='all':continue
 ax.scatter(x['total']/1000,x['mrr'],c='#555',marker='D',s=50);ax.annotate(short[x['arm']],(x['total']/1000,x['mrr']),xytext=(5,7),textcoords='offset points')
ax.set(ylim=(.285,.53),xlabel='Mean input + output tokens (thousands)',ylabel='Standard MRR',title='RQ4.5: ranking and deployment token cost');ax.grid(alpha=.2);fig.text(.13,-.02,'* Historical reused results; no contemporary causal comparison. All 220 exposed cases.',fontsize=9);save('performance_cost')
fig,axes=plt.subplots(1,2,figsize=(11,4.4));dsets=['aiops2022','aiops2025','aegislab'];refs={x['dataset']:x['mrr'] for x in s['historical'] if x['arm']=='T_FULL'}
m=np.array([[next(x['standard_mrr'] for x in s['aggregates'] if x['arm']==a and x['dataset']==ds) for ds in dsets] for a in order]);axes[0].imshow(m,cmap='viridis',vmin=.2,vmax=.66,aspect='auto');axes[1].imshow(m-np.array([refs[x] for x in dsets]),cmap='RdBu',vmin=-.3,vmax=.3,aspect='auto')
for ax,title,vals in [(axes[0],'Standard MRR',m),(axes[1],'Delta vs historical T_FULL',m-np.array([refs[x] for x in dsets]))]:
 ax.set_xticks(range(3),['AIOPS-2022','AIOPS-2025','AegisLab']);ax.set_yticks(range(6),[short[a] for a in order]);ax.set_title(title)
 for (i,j),val in np.ndenumerate(vals):ax.text(j,i,f'{val:.4f}',ha='center',va='center',color='white' if ax is axes[0] and val<.4 else 'black')
fig.tight_layout();save('dataset_results')
q={ (x['arm'],x['family']):x for x in s['qa_components']};sens={x['arm']:x for x in json.loads((P/'qa_unit_sensitivity.json').read_text())}
fig,axes=plt.subplots(1,2,figsize=(11,4.5));xx=np.arange(6);w=.25
axes[0].bar(xx-w,[q[a,'reading']['content_correct'] for a in order],w,label='Numeric value only');axes[0].bar(xx,[q[a,'reading']['tolerant'] for a in order],w,label='Value + entity + unit');axes[0].bar(xx+w,[q[a,'binding']['tolerant'] for a in order],w,label='Complete relation binding');axes[0].set_title('Field decomposition (60 readings; 58 bindings)')
strict={a:np.mean([x['qa_standard'] for x in json.loads((P/'qa_rca_answers.json').read_text()) if x['arm']==a]) for a in order}
axes[1].bar(xx-.17,[strict[a] for a in order],.34,label='Registered joint QA');axes[1].bar(xx+.17,[sens[a]['posthoc_unit_alias_case_accuracy'] for a in order],.34,label='Post-hoc unit-alias sensitivity');axes[1].set_title('Case-mean QA; original scores preserved')
for ax in axes:ax.set_xticks(xx,[short[a] for a in order]);ax.set_ylim(0,1.03);ax.legend(fontsize=8);ax.set_ylabel('Accuracy');ax.grid(axis='y',alpha=.2)
fig.tight_layout();save('qa_decomposition')
fig,ax=plt.subplots(figsize=(8.5,4.4));aa={x['arm']:x for x in s['attention'] if x['variant']=='BASE' and x['stage']=='last_prompt'}
ax.bar(xx,[aa[a]['text_mass'] for a in order],color='#5d6e9e',label='Text (instructions + evidence in hybrid)');ax.bar(xx,[aa[a]['image_mass'] for a in order],bottom=[aa[a]['text_mass'] for a in order],color='#27a79b',label='Retained image tokens');ax.set_xticks(xx,[short[a] for a in order]);ax.set_ylim(0,1);ax.set_ylabel('Mean attention mass over heads');ax.set_title('Layer 3, last prompt query only');ax.legend(fontsize=8,loc='lower right');fig.text(.13,-.015,'30 cases per arm (28 unique captures for H-T/H-TM); not final ranking attention.',fontsize=9);save('attention_mass')
