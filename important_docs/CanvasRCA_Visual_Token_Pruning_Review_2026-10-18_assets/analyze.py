"""Read-only retrospective over completed experiments; no model calls.

Run: PYTHONPATH=src python3 important_docs/CanvasRCA_Visual_Token_Pruning_Review_2026-10-18_assets/analyze.py
Original answers/scores are not changed. Tables are independently reaggregated
from retained per-call analysis records. New tests are explicitly retrospective.
"""
from pathlib import Path
import csv, json, hashlib, itertools, math, sys
from collections import defaultdict, Counter
import numpy as np
from scipy.stats import wilcoxon
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
from scorer.bounded_mean import group_mean_test, holm_adjust

R1 = ROOT / 'RQs/RQ4_1/results/comparison_coding_v1'
R3 = ROOT / 'docs/experiment_reports/RQ4_3_Qwen_Analysis_2026-10-12_assets'
R4 = ROOT / 'RQs/RQ4_4/results/source_views_v1/analysis/detailed_v1'
SOURCES = set()

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()

def read(p):
    SOURCES.add(Path(p))
    return json.loads(Path(p).read_text())

def rows(p):
    SOURCES.add(Path(p))
    with Path(p).open(newline='') as f: return list(csv.DictReader(f))

def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')

def csvsave(name, data):
    if not data: return
    fields = list(dict.fromkeys(k for r in data for k in r))
    with (OUT / name).open('w', newline='') as f:
        w = csv.DictWriter(f, fields); w.writeheader(); w.writerows(data)

def flag(value): return str(value).lower() in ('true', '1', '1.0')
def avg(rs, field): return float(np.mean([float(r[field]) for r in rs]))

core = [f'{a}_E{q}' for a in ('A_UNIFORM', 'UNARY', 'CVC') for q in (25,50,75)] + [
    'QUOTA_E50','REWIRED_E50','A_DIVERSITY_E50','DART_E50','S2PRUNE_E50','GPRUNE_E50','SCOPE_E50']
main1 = [r for r in rows(R1/'final_analysis_v1/calls.csv') if r['kind']=='development']
main3 = [r for r in rows(R3/'calls.csv') if r['variant']=='BASE' and not flag(r['historical'])
         and r['arm'] not in ('HTML_SEMANTIC','HTML_PLOT_CODE')]
main4 = [r for r in rows(R4/'calls.csv') if r['variant']=='BASE' and r['task']=='RCA' and not flag(r['historical'])]
assert len(main3)==18*220 and len(main4)==3*220

collections = [('RQ4.1',main1,'image_retained'),('RQ4.3',main3,'image_tokens'),('RQ4.4',main4,'image_retained')]
summaries=[]; by={}; roster=None
for rq, calls, image_field in collections:
    for arm in dict.fromkeys(r['arm'] for r in calls):
        rs=[r for r in calls if r['arm']==arm]
        ids={r['id'] for r in rs}
        assert len(rs)==len(ids)==220, (rq,arm,len(rs))
        if roster is None: roster=ids
        assert ids==roster
        assert Counter(r['dataset'] for r in rs)=={'aiops2022':60,'aiops2025':60,'aegislab':100}
        by[rq,arm]={r['id']:r for r in rs}
        for dataset in ('ALL','aiops2022','aiops2025','aegislab'):
            s=rs if dataset=='ALL' else [r for r in rs if r['dataset']==dataset]
            d={'experiment':rq,'arm':arm,'dataset':dataset,'n':len(s),
               'scope':'core_pruning' if rq=='RQ4.1' and arm in core else 'inherited_pruning' if rq!='RQ4.1' else 'reference',
               **{k:avg(s,k) for k in ['mrr','tolerant_mrr','ac@1','ac@3','ac@5','precision@3','precision@5','avg@3','avg@5','input','output','total','text_tokens','image_original']},
               'image_retained':avg(s,image_field),'invalid':sum(flag(r['invalid']) for r in s),
               'unknown_candidate_outputs':sum(flag(r['unknown']) for r in s),
               'duplicate_outputs':sum(flag(r['duplicate']) for r in s),
               'event_groups':len({r['group'] for r in s}),
               'backend_counts':json.dumps(dict(Counter(r['backend'] for r in s)),sort_keys=True)}
            if rq=='RQ4.1':d.update(online_seconds=avg(s,'online_wall'),vision_seconds=avg(s,'vision_wall'),selector_seconds=avg(s,'selector_wall'))
            else:d.update(request_model_seconds=avg(s,'model_seconds'),vision_seconds=avg(s,'vision_seconds'))
            summaries.append(d)

# Check against every available published non-macro aggregate, not rounded prose.
max_error=0.
for rq,p in [('RQ4.1',R1/'final_analysis_v1/main_summary.csv'),('RQ4.3',R3/'main_summary.csv'),('RQ4.4',R4/'main_summary.csv')]:
    lookup={(r['arm'],r['dataset']):r for r in rows(p)}
    for r in [s for s in summaries if s['experiment']==rq]:
        old=lookup[r['arm'],r['dataset']]
        for k in ('mrr','tolerant_mrr','ac@1','ac@3','ac@5','input','output','total'):
            max_error=max(max_error,abs(r[k]-float(old[k])))
assert max_error<1e-8,max_error
csvsave('all_methods_metrics.csv',summaries)

# Retrospective complete pairwise family: 16 pruning arms + unpruned V_FULL.
# 136 comparisons. Original RQ4.1 registered families remain separate.
ids=sorted(roster)
def compare(a,b,subset=None):
    keys=ids if subset is None else subset
    delta=np.round([float(a[i]['mrr'])-float(b[i]['mrr']) for i in keys],12)
    grouped=defaultdict(list)
    for i,d in zip(keys,delta):
        assert a[i]['group']==b[i]['group']
        grouped[a[i]['group']].append(d)
    sums=[sum(v) for v in grouped.values()]; sizes=[len(v) for v in grouped.values()]
    gd=np.round([np.mean(v) for v in grouped.values()],12)
    def p(x):
        return 1. if not np.any(x) else float(wilcoxon(x,zero_method='pratt',alternative='two-sided',method='approx',correction=False).pvalue)
    def dz(x):
        sd=np.std(x,ddof=1)
        return float(np.mean(x)/sd) if sd else 0.
    return {'n':len(keys),'groups':len(grouped),'delta':float(delta.mean()),'dz':dz(delta),
            'v11_p':float(group_mean_test(sums,sizes)['p_value']),
            'case_pratt_p':p(delta),'group_pratt_p':p(gd),
            'improved':int(sum(delta>0)),'worsened':int(sum(delta<0)),'tied':int(sum(delta==0)),
            'top1_repairs':sum(float(a[i]['ac@1'])>float(b[i]['ac@1']) for i in keys),
            'top1_breaks':sum(float(a[i]['ac@1'])<float(b[i]['ac@1']) for i in keys),
            'top5_repairs':sum(float(a[i]['ac@5'])>float(b[i]['ac@5']) for i in keys),
            'top5_breaks':sum(float(a[i]['ac@5'])<float(b[i]['ac@5']) for i in keys)}

tests=[]
for a,b in itertools.combinations(['V_FULL']+core,2):
    tests.append({'a':a,'b':b,**compare(by['RQ4.1',a],by['RQ4.1',b])})
assert len(tests)==136
for k in ('v11','case_pratt','group_pratt'):
    for r,h in zip(tests,holm_adjust([t[k+'_p'] for t in tests])):r[k+'_holm_136']=float(h)
csvsave('retrospective_all_136_pairs.csv',tests)

# All-outcome and paired-valid sensitivity; validity is outcome-dependent, so
# no inferential claim from conditioning on it and no replacement denominator.
valid_sensitivity=[]
for arm in ['V_FULL']+core:
    if arm=='A_UNIFORM_E50':continue
    a=by['RQ4.1','A_UNIFORM_E50'];b=by['RQ4.1',arm]
    keep=[i for i in ids if not flag(a[i]['invalid']) and not flag(b[i]['invalid'])]
    valid_sensitivity.append({'a':'A_UNIFORM_E50','b':arm,'all_n':220,
        'all_delta':float(np.mean([float(a[i]['mrr'])-float(b[i]['mrr']) for i in ids])),
        'tolerant_all_delta':float(np.mean([float(a[i]['tolerant_mrr'])-float(b[i]['tolerant_mrr']) for i in ids])),
        'both_valid_n':len(keep),'both_valid_delta':float(np.mean([float(a[i]['mrr'])-float(b[i]['mrr']) for i in keep])) if keep else None})
csvsave('paired_valid_sensitivity.csv',valid_sensitivity)

# Source/actual-mask audit over all 220 cases. This reads compact completion
# records and token-support JSON, not image tensors or pretrained weights.
idx=read(R1/'deployment_v26/request_index.json')
support={}
for u in idx['units']:
    if u['kind']=='development' and u['arm']=='A_UNIFORM_E50':
        s=read(ROOT/idx['requests'][u['request_key']]['support'])
        a=set(s['anchors']); e={int(t) for v in s['roles'].values() for t in v['tokens']}
        assert not a&e
        support[u['id']]=(a,e,s['image_tokens'])
audit=[]
for arm in ['A_UNIFORM_E50','CVC_E50','SCOPE_E50','S2PRUNE_E50','DART_E50','GPRUNE_E50']:
    for i in ids:
        r=read(R1/'formal_v28/completed'/f'{i}__development__{arm}__BASE.json')
        sel=(r.get('actual_retention') or {}).get('indices')
        if sel is None:sel=r['prior_state']['selection']['indices']
        keep=set(sel);a,e,n=support[i]
        assert len(keep)==len(sel)==len(a)+math.ceil(.5*len(e))
        audit.append({'arm':arm,'id':i,'dataset':by['RQ4.1',arm][i]['dataset'],
            'N':n,'K':len(keep),'A':len(a),'E':len(e),'A_kept':len(a&keep),'E_kept':len(e&keep),
            'outside_A_E_kept':len(keep-(a|e)),'anchor_recall':len(a&keep)/len(a),
            'optional_recall':len(e&keep)/len(e),
            'outside_A_E_fraction':len(keep-(a|e))/len(keep),
            'outside_A_E_optional_slot_fraction':len(keep-(a|e))/(len(keep)-len(a)) if a<=keep else None,
            'protection_policy':(r.get('protection_audit') or {}).get('policy','not_declared'),
            'invalid':int(flag(by['RQ4.1',arm][i]['invalid']))})
csvsave('actual_mask_audit.csv',audit)
mask_summary=[]
for arm in dict.fromkeys(r['arm'] for r in audit):
    rs=[r for r in audit if r['arm']==arm]
    for ds in ('ALL','aiops2022','aiops2025','aegislab'):
        rr=rs if ds=='ALL' else [r for r in rs if r['dataset']==ds]
        mask_summary.append({'arm':arm,'dataset':ds,'n':len(rr),
            **{k:float(np.mean([r[k] for r in rr])) for k in ('N','K','A','E','A_kept','E_kept','outside_A_E_kept','anchor_recall','optional_recall','outside_A_E_fraction')},
            'all_anchors_preserved_cases':sum(r['A']==r['A_kept'] for r in rr),
            'policies':json.dumps(dict(Counter(r['protection_policy'] for r in rr)),sort_keys=True)})
        vals=[r['outside_A_E_optional_slot_fraction'] for r in rr if r['outside_A_E_optional_slot_fraction'] is not None]
        mask_summary[-1]['outside_A_E_optional_slot_fraction']=float(np.mean(vals)) if vals else None
csvsave('actual_mask_summary.csv',mask_summary)

# Token-only empirical Pareto frontier, not a speed or energy frontier.
allrows=[r for r in summaries if r['dataset']=='ALL' and r['scope']!='reference']
assert len(allrows)==37
for r in allrows:
    r['dominated_by']=json.dumps([f"{s['experiment']}/{s['arm']}" for s in allrows
        if s['total']<=r['total'] and s['mrr']>=r['mrr'] and (s['total']<r['total'] or s['mrr']>r['mrr'])])
csvsave('descriptive_token_frontier.csv',allrows)

# Figures are original report plots, not diagnostic dashboards.
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':150})
core_rows=[r for r in summaries if r['experiment']=='RQ4.1' and r['dataset']=='ALL' and r['arm'] in core+['V_FULL']]
core_rows.sort(key=lambda r:r['mrr'])
fig,ax=plt.subplots(figsize=(10,8.7));y=np.arange(len(core_rows))
for yy,r in zip(y,core_rows):
    ax.plot([r['mrr'],r['tolerant_mrr']],[yy,yy],color='#94a3b8',lw=3)
ax.scatter([r['mrr'] for r in core_rows],y,s=40,label='Registered standard MRR',color='#166534',zorder=3)
ax.scatter([r['tolerant_mrr'] for r in core_rows],y,s=35,label='Post-hoc slot-preserving tolerant MRR',color='#f59e0b',marker='D',zorder=3)
ax.axvline(next(r['mrr'] for r in summaries if r['experiment']=='RQ4.1' and r['arm']=='T_FULL' and r['dataset']=='ALL'),color='#b91c1c',ls='--',label='T_FULL (0.4846)')
ax.set_yticks(y,[r['arm'] for r in core_rows]);ax.set_xlim(0,.55);ax.set_xlabel('MRR on the same 220 exposed development cases')
ax.set_title('RQ4.1: simpler protected spatial coverage is the strongest observed pruning arm')
ax.legend(loc='lower right',fontsize=8);ax.grid(axis='x',alpha=.2);fig.tight_layout();fig.savefig(OUT/'01_pruning_mrr.png');plt.close(fig)

fig,axs=plt.subplots(1,2,figsize=(12,4.5))
for family,c in [('A_UNIFORM','#166534'),('CVC','#2563eb'),('UNARY','#9333ea')]:
    rr=[next(r for r in core_rows if r['arm']==f'{family}_E{q}') for q in (25,50,75)]
    axs[0].plot([25,50,75],[r['mrr'] for r in rr],'o-',color=c,label=family)
    axs[1].plot([r['total'] for r in rr],[r['mrr'] for r in rr],'o-',color=c,label=family)
    for r in rr:axs[1].annotate(r['arm'].split('_E')[-1],(r['total'],r['mrr']),xytext=(4,4),textcoords='offset points',fontsize=8)
axs[0].set_xlabel('Percent of OPTIONAL evidence support (all anchors retained)');axs[0].set_xticks([25,50,75]);axs[1].set_xlabel('Mean retained input + output tokens')
for ax in axs:ax.set_ylabel('Standard MRR');ax.grid(alpha=.2);ax.legend()
fig.suptitle('More optional tokens do not monotonically improve diagnosis');fig.tight_layout();fig.savefig(OUT/'02_budget_curves.png');plt.close(fig)

fig,axs=plt.subplots(1,2,figsize=(13,4.9))
for rq,c,m in [('RQ4.1','#166534','o'),('RQ4.3','#2563eb','s'),('RQ4.4','#f59e0b','^')]:
    rr=[r for r in allrows if r['experiment']==rq]
    axs[0].scatter([r['total'] for r in rr],[r['mrr'] for r in rr],color=c,marker=m,s=38,label=rq)
for arm,rq in [('A_UNIFORM_E50','RQ4.1'),('P_SOFT_IMAGE','RQ4.3'),('X_SRP','RQ4.3'),('SOURCE_ZOOM','RQ4.4'),('S_JOINT','RQ4.3')]:
    r=next(r for r in allrows if r['arm']==arm and r['experiment']==rq)
    offset={'A_UNIFORM_E50':(12,17),'P_SOFT_IMAGE':(25,-15),'X_SRP':(12,-14),'SOURCE_ZOOM':(-110,14),'S_JOINT':(-8,-21)}[arm]
    axs[0].annotate(arm,(r['total'],r['mrr']),xytext=offset,textcoords='offset points',fontsize=8,arrowprops={'arrowstyle':'-','color':'gray'})
axs[0].set_xlim(4000,15000);axs[0].set_ylim(-.015,.41);axs[0].set_xlabel('Mean input + output tokens');axs[0].set_ylabel('Standard MRR');axs[0].legend();axs[0].grid(alpha=.2);axs[0].set_title('All 37 pruning-containing conditions (cross-run descriptive)')
rr=[r for r in core_rows if r['arm'] in ['A_UNIFORM_E50','CVC_E50','A_DIVERSITY_E50','DART_E50','S2PRUNE_E50','SCOPE_E50','GPRUNE_E50','V_FULL']]
for r in rr:
    axs[1].scatter(r['online_seconds'],r['mrr'],s=40,color='#166534')
    axs[1].annotate(r['arm'].replace('_E50',''),(r['online_seconds'],r['mrr']),xytext=(5,6 if r['arm']!='CVC_E50' else -14),textcoords='offset points',fontsize=8)
axs[1].set_xlim(17,35);axs[1].set_xlabel('Measured online seconds (RQ4.1 HF batch=1 only)');axs[1].set_ylabel('Standard MRR');axs[1].grid(alpha=.2);axs[1].set_title('Token reduction is not equivalent to latency reduction')
fig.tight_layout();fig.savefig(OUT/'03_cost_performance.png');plt.close(fig)

fig,ax=plt.subplots(figsize=(10.5,4.6))
rr=[r for r in mask_summary if r['dataset']=='ALL']
names=[r['arm'].replace('_E50','') for r in rr]; y=np.arange(len(rr));left=np.zeros(len(rr))
for field,c,label in [('A_kept','#166534','Mandatory anchor support A'),('E_kept','#2563eb','Optional evidence support E'),('outside_A_E_kept','#cbd5e1','Outside registered A / E support')]:
    values=np.array([r[field] for r in rr]);ax.barh(y,values,left=left,color=c,label=label);left+=values
ax.set_yticks(y,names);ax.invert_yaxis();ax.set_xlabel('Mean retained tokens (all six use the same per-case K)')
ax.set_title('Actual masks: equal token counts conceal different evidence allocations')
ax.legend(loc='upper center',bbox_to_anchor=(.5,-.14),ncol=3,fontsize=8)
fig.tight_layout();fig.savefig(OUT/'04_actual_mask_composition.png');plt.close(fig)

save('verification.json',{'status':'passed','new_model_calls':0,'original_answers_modified':False,
    'source_scores_reaggregated':True,'max_aggregate_error':max_error,
    'core_pruning_conditions':16,'inherited_pruning_conditions':21,'total_pruning_containing_conditions':37,
    'cases_each':220,'datasets':{'aiops2022':60,'aiops2025':60,'aegislab':100},
    'event_groups':len({r['group'] for r in by['RQ4.1','A_UNIFORM_E50'].values()}),
    'actual_mask_rows':len(audit),'new_tests':'retrospective only; complete 136-pair family; no CI',
    'python':sys.version,'numpy':np.__version__,
    'source_hashes':{str(p.relative_to(ROOT)):sha(p) for p in sorted(SOURCES)}})
print(json.dumps({'status':'passed','conditions':37,'actual_mask_rows':len(audit),'max_aggregate_error':max_error}))
