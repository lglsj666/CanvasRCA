"""Reproduce output-pattern counts, checked case facts and report figures.

Case selection is outcome-stratified and retrospective, not prevalence
estimation. Reasons are emitted after the ranking and are not faithful
measurements of an internal causal reasoning trace.
"""
from pathlib import Path
import csv, hashlib, json
import numpy as np
from scipy.spatial import cKDTree
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
BASE=ROOT/'RQs/RQ4_1/results/comparison_coding_v1'
SOURCES={}
def read(p):
    p=Path(p);raw=p.read_bytes();SOURCES[str(p.relative_to(ROOT))]=hashlib.sha256(raw).hexdigest()
    return json.loads(raw)
def rows(p):
    p=Path(p);SOURCES[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
    with p.open(newline='') as f:return list(csv.DictReader(f))
def save(name,x):
    (OUT/name).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def write(name,rs):
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,list(dict.fromkeys(k for r in rs for k in r)));w.writeheader();w.writerows(rs)

calls=[r for r in rows(BASE/'final_analysis_v1/calls.csv') if r['kind']=='development']
selected_arms={r['arm'] for r in rows(OUT/'mechanism_summary.csv')}
patterns=[]
for arm in sorted(selected_arms):
    for ds in ('ALL','aiops2022','aiops2025','aegislab'):
        rs=[r for r in calls if r['arm']==arm and (ds=='ALL' or r['dataset']==ds)]
        five=three=0
        for r in rs:
            pred=list(map(int,json.loads(r['ranked'])))
            d=[b-a for a,b in zip(pred,pred[1:])]
            five+=len(set(d))==1 and abs(d[0])==1
            three+=any(abs(d[j])==1 and d[j]==d[j+1] for j in range(3))
        patterns.append({'arm':arm,'dataset':ds,'n':len(rs),'five_consecutive_ids':five,
             'any_three_consecutive_ids':three,'unknown_id_answers':sum(int(r['unknown']) for r in rs),
             'duplicate_id_answers':sum(int(r['duplicate']) for r in rs)})
write('diagnostic_output_patterns.csv',patterns)

idx=read(BASE/'deployment_v26/request_index.json')
examples=read(OUT/'mechanism_example_answers.json')
selection=read(OUT/'mechanism_example_selection.json')
ids=sorted({r['id'] for r in examples})
cards={i:{c['id']:c for c in read(ROOT/idx['cases'][i]['base']/'evidence.json')['cards']} for i in ids}
ans={(r['id'],r['arm']):r for r in examples}
checks=[]
def check(oid,arms,observation,source_cards,mode,limits):
    checks.append({'id':oid,'arms':arms,'observation':observation,'classification':mode,
       'limitation':limits,'source_cards':source_cards,
       'evidence_path':str(Path(idx['cases'][oid]['base'])/'evidence.json'),
       'responses':[{'arm':a,'path':ans[oid,a]['response_source'],
                     'mrr':ans[oid,a]['mrr'],'tolerant_mrr':ans[oid,a]['tolerant_mrr']} for a in arms]})

i='INC-CCE2A7ACCA59';c=cards[i]
assert c['TRA002']['entity']=='23295' and c['TRA002']['data']['before']==25310.7 and c['TRA002']['data']['after']==59663.1
assert min(v for v in c['MET009']['data']['values'] if v is not None)==2874000000.
assert c['JNT001']['data']['parent']=='81654' and '370' in c['JNT001']['data']['parent_operation']
check(i,['V_FULL','A_UNIFORM_E50','CVC_E50'],
    'V_FULL ranks service 370 from the operation string; the 25310.7→59663.1 us trace is bound to pod23295. '
    'Uniform/CVC instead rank accepted pod81654 and cite the parent-pod pair. Uniform nevertheless says MET09 drops to zero, '
    'while the full observed series is 2.874e9–3.765e9.',
    ['TRA002','JNT001','MET009'],'entity/granularity focus changes; correct rank with false numerical explanation',
    'This does not prove that a particular deleted token caused the focus change, or that all Uniform claims are correct.')
i='INC-1595063C5B11';c=cards[i]
assert c['MET001']['entity']==c['MET002']['entity']==c['MET010']['entity']=='84394'
assert c['TRA003']['entity']=='67740' and c['TRA003']['data']['before']==19639.8
assert c['TRA003']['data']['after']==46244.2
check(i,['A_UNIFORM_E50','CVC_E50','S2PRUNE_E50'],
    'Uniform ranks accepted pod84394, which owns the request/error/duration metrics. CVC shifts to operation service832, '
    'quotes the real 19639.8→46244.2 trace owned by pod67740, and generates three noncandidate IDs. '
    'S2Prune repeats only 33620/42129/60764 and misses 84394.',
    ['MET001','MET002','MET010','TRA003'],'evidence focus and entity granularity shift; invalid alternatives',
    'Operation service identity and span-owner pod are related but not interchangeable under the registered target.')
i='INC-9C8982A9736C'
assert all(v in idx['cases'][i]['candidates'] for v in ['2924','3145','25922'])
check(i,['A_UNIFORM_E50','SCOPE_E50'],
    'SCOPE outputs [2924,3145,2924,3145,2924] while its reason says these node/pod IDs are absent from the inventory '
    'and claims to select service265 instead. All three cited IDs 2924/3145/25922 are candidates. '
    'Uniform has an accepted first rank but also narrates downstream-origin versus frontend-first tension.',
    ['candidate inventory'],'candidate-inventory claim false; reason contradicts emitted ranking',
    'SCOPE retains all registered anchors. This is not proof that the renderer omitted node/pod candidates.')
i='INC-13F29FFC8DE6';c=cards[i]
assert c['MET001']['entity']=='744' and max(v for v in c['MET001']['data']['values'] if v is not None)==1054
assert c['TRA001']['entity']=='538' and c['TRA001']['data']['after']==350879.71
assert c['TRA003']['entity']=='548' and c['TRA003']['data']['before']==726.43
check(i,['A_UNIFORM_E50','CVC_E50','SCOPE_E50','S2PRUNE_E50'],
    'Uniform ranks119 and binds MET01 to119, but MET01 belongs744; its claimed peak1137.8 exceeds the observed maximum1054 '
    'and is visible as an axis tick. CVC ranks accepted705 but forms 726.43→~350800 us from two different trace cards: '
    '726.43 belongs548 reference; 350879.71 belongs538 current.',
    ['MET001','TRA001','TRA003'],'Uniform failure; CVC correct rank still has cross-card and phase misbinding',
    'A winning rank cannot validate its accompanying explanation. No causal claim from this outcome-selected example.')
i='INC-058FC5DD18AD';c=cards[i]
assert [c[f'MET{n:03d}']['entity'] for n in range(1,6)]==['650','956','351','956','908']
assert c['JNT001']['data']['parent']=='905' and c['JNT001']['data']['child']=='951'
assert c['TRA002']['entity']=='905'
check(i,['V_FULL','A_UNIFORM_E50','CVC_E50'],
    'CVC ranks the filesystem-associated entities650/956/351/908/130 and says they are exactly MET01–05, '
    'but the actual owners are650/956/351/956/908. Uniform shifts to the true observed905→951 pair and has accepted top1. '
    'Uniform still confuses inclusive/exclusive interpretation in its reason; V_FULL calls filesystem values near zero '
    'although minima are1.455e10.',
    ['MET001','MET002','MET003','MET004','MET005','TRA002','JNT001'],
    'common-resource narrative versus request-pair narrative; cross-card ownership errors',
    'Neither shared filesystem variation nor parent-child identity alone proves the initiating cause.')
i='INC-9AF32547D264'
assert ans[i,'DART_E50']['ranked'][0]=='579' and ans[i,'DART_E50']['tolerant_mrr']==1
assert ans[i,'DART_E50']['unknown_ids']==['578','575','574']
check(i,['V_FULL','A_UNIFORM_E50','DART_E50','GPRUNE_E50'],
    'V_FULL lists747 first while its reason chiefly argues for576. Uniform has accepted523 first. DART has accepted579 '
    'first but three fabricated/noncandidate alternatives make the standard result zero (tolerant RR=1). '
    'G-Prune emits345/346/347/348/349, all outside the candidate inventory, with a detailed propagation story.',
    ['candidate inventory'],'rank-reason mismatch; suffix invalidation; sequential ID completion',
    'Calling these IDs noncandidate is verified; numerical editing or label-based repairs are not performed.')

# Direct Euclidean brute-force verification on the three opened image cases.
for oid in ['INC-CCE2A7ACCA59','INC-9C8982A9736C','INC-13F29FFC8DE6']:
    base=ROOT/idx['cases'][oid]['base'];s=read(base/'token_support.json')
    request=idx['requests'][oid+'__VISUAL__BASE']
    png=ROOT/request['png'];digest=hashlib.sha256(png.read_bytes()).hexdigest()
    assert digest==request['png_sha256']
    SOURCES[str(png.relative_to(ROOT))]=digest
    w=s['grid'][1];e=sorted({t for v in s['roles'].values() for t in v['tokens']})
    for arm in ['A_UNIFORM_E50','CVC_E50']:
        r=read(BASE/'formal_v28/completed'/f'{oid}__development__{arm}__BASE.json')
        keep=r['actual_retention']['indices'];kxy=np.array([(t%w,t//w) for t in keep])
        exy=np.array([(t%w,t//w) for t in e]);kd=cKDTree(kxy).query(exy)[0]
        direct=[]
        for start in range(0,len(exy),32):
            direct.extend(np.sqrt(((exy[start:start+32,None,:]-kxy[None,:,:])**2).sum(-1).min(-1)))
        assert np.allclose(kd,direct,rtol=0,atol=1e-12)

save('mechanism_manual_case_audit.json',{'status':'checked','selected_strata':selection,
    'selected_cases':len(ids),'saved_answers':len(examples),
    'answers_read_for_new_qualitative_audit':42,'arms_read_per_case':
    ['V_FULL','A_UNIFORM_E50','CVC_E50','SCOPE_E50','S2PRUNE_E50','DART_E50','GPRUNE_E50'],
    'original_pngs_opened':['INC-CCE2A7ACCA59','INC-9C8982A9736C','INC-13F29FFC8DE6'],
    'no_population_error_rate_inferred':True,'checks':checks,'source_hashes':SOURCES})

summary={r['arm']:r for r in rows(OUT/'mechanism_summary.csv') if r['dataset']=='ALL'}
plt.rcParams.update({'font.size':10,'figure.dpi':150,'axes.spines.top':False,'axes.spines.right':False})
names=['A_UNIFORM_E50','UNARY_E50','CVC_E50','QUOTA_E50','A_DIVERSITY_E50','SCOPE_E50','S2PRUNE_E50','DART_E50','GPRUNE_E50']
fig,axs=plt.subplots(1,2,figsize=(12,5.5))
for a in names:
    r=summary[a];color='#166534' if a=='A_UNIFORM_E50' else '#2563eb'
    axs[0].scatter(100*(1-float(r['zero_optional_role_fraction'])),float(r['mrr']),color=color)
    offset={'CVC_E50':(-57,5),'UNARY_E50':(-65,-12),'QUOTA_E50':(-32,9),
            'SCOPE_E50':(-66,-13),'S2PRUNE_E50':(5,5),'A_UNIFORM_E50':(-38,11)}.get(a,(4,5))
    axs[0].annotate(a.replace('_E50',''),(100*(1-float(r['zero_optional_role_fraction'])),float(r['mrr'])),
                    xytext=offset,textcoords='offset points',fontsize=8,
                    arrowprops={'arrowstyle':'-','color':'#94a3b8','lw':.7})
axs[0].set_xlabel('Optional roles with at least one retained support (%)')
axs[0].set_ylabel('Standard MRR');axs[0].set_xlim(35,108);axs[0].set_ylim(-.02,.40)
axs[0].set_title('Touching every registered role does not maximize MRR');axs[0].grid(alpha=.2)
display=['A_UNIFORM_E50','CVC_E50','UNARY_E50','SCOPE_E50','S2PRUNE_E50','DART_E50','GPRUNE_E50']
v=[float(summary[a]['evidence_nearest_max_grid_units']) for a in display]
axs[1].barh([a.replace('_E50','') for a in display],v,color=['#166534']+['#2563eb']*6)
axs[1].invert_yaxis();axs[1].set_xlabel('Mean per-case maximum distance to retained A + selected tokens')
axs[1].set_title('Uniform leaves smaller spatial gaps in optional support')
for j,x in enumerate(v):axs[1].text(x+.05,j,f'{x:.2f}',va='center',fontsize=9)
axs[1].set_xlim(0,5.6);axs[1].grid(axis='x',alpha=.2)
fig.text(.5,.015,'Geometry only: distance is in merged-token grid units; support contact is not fact readability.',ha='center',fontsize=8)
fig.tight_layout(rect=(0,.04,1,1));fig.savefig(OUT/'05_support_proxy_and_geometry.png');plt.close(fig)

fig,axs=plt.subplots(1,2,figsize=(12,4.9))
for a in ['A_UNIFORM_E50','SCOPE_E50','S2PRUNE_E50','DART_E50','GPRUNE_E50']:
    r=summary[a];axs[0].plot(range(1,6),[100*float(r[f'legal_slot_{j}']) for j in range(1,6)],'o-',label=a.replace('_E50',''))
axs[0].set_xticks(range(1,6));axs[0].set_ylim(0,105);axs[0].set_xlabel('Ranked output slot');axs[0].set_ylabel('IDs belonging to the case candidate inventory (%)')
axs[0].set_title('Later alternatives lose candidate grounding');axs[0].legend(fontsize=8);axs[0].grid(alpha=.2)
trs={r['other']:r for r in rows(OUT/'diagnostic_transition_summary.csv')}
nn=['V_FULL','UNARY_E50','CVC_E50','SCOPE_E50','S2PRUNE_E50','DART_E50','GPRUNE_E50']
x=np.arange(len(nn));r=[float(trs[a]['delta_tolerant']) for a in nn];q=[float(trs[a]['interface_penalty_difference']) for a in nn]
axs[1].barh(x,r,label='Difference remaining under tolerant scoring',color='#166534')
axs[1].barh(x,q,left=r,label='Difference in whole-answer invalidation penalties',color='#f59e0b')
axs[1].set_yticks(x,[a.replace('_E50','') for a in nn]);axs[1].invert_yaxis()
axs[1].set_xlabel('Uniform minus comparison: standard MRR difference');axs[1].set_title('Scoring-loss accounting does not explain all ranking gaps')
axs[1].legend(fontsize=7,loc='lower right');axs[1].grid(axis='x',alpha=.2)
fig.text(.5,.015,'Accounting identity, not a causal decomposition. Duplicate IDs can be legal yet invalidate a whole answer.',ha='center',fontsize=8)
fig.tight_layout(rect=(0,.04,1,1));fig.savefig(OUT/'06_output_grounding_and_loss.png');plt.close(fig)
print('Output patterns, six checked cases, geometry cross-check and two figures complete.')
