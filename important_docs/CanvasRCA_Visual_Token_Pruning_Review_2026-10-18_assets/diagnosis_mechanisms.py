"""Offline diagnostic-impact audit. No inference, rescoring or source edits.

Geometric support is not semantic recoverability. All associations are
retrospective descriptions, never causes or new model-selection criteria.
"""
from pathlib import Path
import csv, hashlib, json, math
from collections import Counter, defaultdict
import numpy as np
from scipy.spatial import cKDTree
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
BASE = ROOT / 'RQs/RQ4_1/results/comparison_coding_v1'
ARMS = ['V_FULL'] + [f'{a}_E{q}' for a in ('A_UNIFORM','UNARY','CVC') for q in (25,50,75)] + [
    'QUOTA_E50','REWIRED_E50','A_DIVERSITY_E50','SCOPE_E50','S2PRUNE_E50','DART_E50','GPRUNE_E50']
SOURCES = {}
def read(path):
    path=Path(path); raw=path.read_bytes()
    SOURCES[str(path.relative_to(ROOT))]=hashlib.sha256(raw).hexdigest()
    return json.loads(raw)
def csvread(path):
    path=Path(path);SOURCES[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open(newline='') as f:return list(csv.DictReader(f))
def write(name,rows):
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,keys);w.writeheader();w.writerows(rows)
def save(name,x):
    (OUT/name).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def mean(values):
    x=[v for v in values if v is not None]
    return float(np.mean(x)) if x else None
def rho(a,b):
    ok=[(x,y) for x,y in zip(a,b) if x is not None and y is not None]
    if len(ok)<3 or len({x for x,y in ok})<2 or len({y for x,y in ok})<2:return None
    return float(spearmanr(*zip(*ok)).statistic)

idx=read(BASE/'deployment_v26/request_index.json')
calls=csvread(BASE/'final_analysis_v1/calls.csv')
calls={(r['id'],r['arm']):r for r in calls if r['kind']=='development' and r['arm'] in ARMS}
ids=sorted({i for i,a in calls});assert len(ids)==220 and len(calls)==220*len(ARMS)
req_by_id={u['id']:idx['requests'][u['request_key']] for u in idx['units']
           if u['kind']=='development' and u['arm']=='A_UNIFORM_E50'}
metrics=[];pairrows=[];outputs=[];mask_agreement=[]
for ix,oid in enumerate(ids):
    req=req_by_id[oid]; sup=read(ROOT/req['support']);prov=read(ROOT/req['provenance'])
    private=read(ROOT/idx['cases'][oid]['private'])
    roots=set(private['accepted_label_numeric_ids'].values())
    candidates=set(idx['cases'][oid]['candidates']);natural=private['numeric_to_natural']
    rolemeta={r['id']:r for r in prov['roles']}
    roleids=[u for u,r in sup['roles'].items() if r['tokens']]
    rs={u:set(sup['roles'][u]['tokens']) for u in roleids}
    assert set(rolemeta)==set(sup['roles'])
    a=set(sup['anchors']);e=set().union(*rs.values());n=sup['image_tokens'];h,w=sup['grid']
    assert n==h*w and not a&e
    es=np.array(sorted(e));exy=np.column_stack((es%w,es//w))
    allxy=np.column_stack((np.arange(n)%w,np.arange(n)//w))
    bundles=[edge for edge in prov['edges'] if len(edge['roles'])>=2 and all(u in rs for u in edge['roles'])]
    rootroles=[u for u in roleids if str(rolemeta[u].get('entity')) in roots]
    masks={};case_rows={}
    for arm in ARMS:
        row=calls[oid,arm]
        p=BASE/'formal_v28/completed'/f'{oid}__development__{arm}__BASE.json'
        r=read(p)
        answer=json.loads(r['response']); ranked=answer['services'];reason=answer['reason']
        assert ranked==json.loads(row['ranked']) and reason==row['reason']
        if arm=='V_FULL':keep=set(range(n));quality=None
        else:
            retention=r.get('actual_retention') or {}
            selection=retention.get('indices')
            if selection is None:selection=r['prior_state']['selection']['indices']
            keep=set(selection);assert len(keep)==len(selection)
            quality=retention.get('objective')
        masks[arm]=keep
        kept_roles={u:len(ts&keep) for u,ts in rs.items()}
        role_fraction={u:kept_roles[u]/len(rs[u]) for u in roleids}
        near=cKDTree(allxy[sorted(keep)]).query(exy)[0]
        legal=[v in candidates for v in ranked]
        unique=[];seen=set()
        for v in ranked:
            unique.append(v in candidates and v not in seen);seen.add(v)
        entities={str(rolemeta[u].get('entity')) for u in roleids}
        represented={str(rolemeta[u].get('entity')) for u in roleids if kept_roles[u]}
        m={'id':oid,'dataset':row['dataset'],'arm':arm,'fault_type':row['fault_type'],
           'mrr':float(row['mrr']),'tolerant_mrr':float(row['tolerant_mrr']),
           'invalid':int(row['invalid']),'high_confidence':int(row['confidence']=='high'),
           'high_confidence_miss':int(row['confidence']=='high' and float(row['tolerant_mrr'])==0),
           'legal_top1':int(legal[0]),'all_legal':int(all(legal)),'unknown_slots':sum(not x for x in legal),
           'legal_unique_slots':sum(unique),'K':len(keep),'anchor_recall':len(keep&a)/len(a),
           'evidence_recall':len(keep&e)/len(e),'outside_fraction':len(keep-(a|e))/len(keep),
           'optional_roles':len(rs),'zero_optional_roles':sum(v==0 for v in kept_roles.values()),
           'zero_optional_role_fraction':mean([v==0 for v in kept_roles.values()]),
           'mean_optional_role_recall':mean(role_fraction.values()),
           'full_optional_role_fraction':mean([v==1 for v in role_fraction.values()]),
           'multi_operand_bundles':len(bundles),
           'all_operands_touched':mean([all(kept_roles[u]>0 for u in edge['roles']) for edge in bundles]),
           'evidence_nearest_mean_grid_units':float(near.mean()),
           'evidence_nearest_p95_grid_units':float(np.quantile(near,.95)),
           'evidence_nearest_max_grid_units':float(near.max()),
           'optional_entities':len(entities),'zero_optional_entities':len(entities-represented),
           'root_optional_role_count':len(rootroles),
           'root_zero_optional_role_fraction':mean([kept_roles[u]==0 for u in rootroles]),
           'root_optional_role_recall':mean([role_fraction[u] for u in rootroles]),
           'registered_feature_objective':quality,
           'top1':ranked[0], 'top1_type':private['entity_granularity'].get(natural.get(ranked[0],''),'unknown'),
           'top1_matches_first_candidate':int(ranked[0]==idx['cases'][oid]['candidates'][0]),
           'root_id_mentioned_in_reason':int(any(__import__('re').search(r'(?<!\d)'+v+r'(?!\d)',reason) for v in roots))}
        for prefix in ('MET','TRA','CMP','LOG'):
            subset=[u for u in roleids if any(t['binding'].startswith(prefix) for t in rolemeta[u]['targets'])]
            m[prefix+'_role_count']=len(subset)
            m[prefix+'_zero_optional_role_fraction']=mean([kept_roles[u]==0 for u in subset])
        for j in range(5):m[f'legal_slot_{j+1}']=int(legal[j])
        metrics.append(m);case_rows[arm]=m
        outputs.append({'id':oid,'dataset':row['dataset'],'arm':arm,'root_ids':sorted(roots),
                        'ranked':ranked,'reason':reason,'mrr':m['mrr'],'tolerant_mrr':m['tolerant_mrr'],
                        'unknown_ids':[v for v in ranked if v not in candidates],
                        'response_source':str(p.relative_to(ROOT)), 'png':req['png'],
                        'evidence':str(Path(req['support']).parent/'evidence.json')})
    u=case_rows['A_UNIFORM_E50']
    for arm in ARMS:
        if arm=='A_UNIFORM_E50':continue
        m=case_rows[arm];t=calls[oid,arm];ut=calls[oid,'A_UNIFORM_E50']
        rr={'id':oid,'dataset':m['dataset'],'other':arm,'u_mrr':u['mrr'],'other_mrr':m['mrr'],
            'delta_mrr':u['mrr']-m['mrr'],'delta_tolerant':u['tolerant_mrr']-m['tolerant_mrr'],
            'interface_penalty_difference':(m['tolerant_mrr']-m['mrr'])-(u['tolerant_mrr']-u['mrr']),
            'top1_changed':int(u['top1']!=m['top1']),
            'whole_rank_changed':int(ut['ranked']!=t['ranked']),
            'both_valid':int(not u['invalid'] and not m['invalid']),
            'u_valid_other_invalid':int(not u['invalid'] and bool(m['invalid'])),
            'u_invalid_other_valid':int(bool(u['invalid']) and not m['invalid']),
            'u_top1_repair':int(float(ut['ac@1'])>float(t['ac@1'])),
            'u_top1_break':int(float(ut['ac@1'])<float(t['ac@1'])),
            'u_top5_repair':int(float(ut['ac@5'])>float(t['ac@5'])),
            'u_top5_break':int(float(ut['ac@5'])<float(t['ac@5']))}
        assert abs(rr['delta_mrr']-rr['delta_tolerant']-rr['interface_penalty_difference'])<1e-12
        pairrows.append(rr)
        ku=masks['A_UNIFORM_E50'];kb=masks[arm]
        mask_agreement.append({'id':oid,'dataset':m['dataset'],'other':arm,
            'jaccard':len(ku&kb)/len(ku|kb),'u_only':len(ku-kb),'other_only':len(kb-ku),
            'top1_changed':rr['top1_changed'],'delta_mrr':rr['delta_mrr']})
    if (ix+1)%40==0:print(f'Audited {ix+1}/220 cases',flush=True)

write('mechanism_case_metrics.csv',metrics)
write('diagnostic_transitions.csv',pairrows)
write('mask_rank_agreement.csv',mask_agreement)
summaries=[]
for arm in ARMS:
    for ds in ('ALL','aiops2022','aiops2025','aegislab'):
        rows=[r for r in metrics if r['arm']==arm and (ds=='ALL' or r['dataset']==ds)]
        d={'arm':arm,'dataset':ds,'n':len(rows)}
        for k in rows[0]:
            if k not in ['id','dataset','arm','fault_type','top1','top1_type']:
                d[k]=mean(r[k] for r in rows)
        for kind in ('service','pod','node','unknown'):d['top1_'+kind+'_count']=sum(r['top1_type']==kind for r in rows)
        d['zero_role_vs_mrr_spearman_descriptive']=rho([r['zero_optional_role_fraction'] for r in rows],[r['mrr'] for r in rows])
        d['zero_role_vs_tolerant_spearman_descriptive']=rho([r['zero_optional_role_fraction'] for r in rows],[r['tolerant_mrr'] for r in rows])
        summaries.append(d)
write('mechanism_summary.csv',summaries)
transition_summary=[]
for arm in ARMS:
    if arm=='A_UNIFORM_E50':continue
    rr=[r for r in pairrows if r['other']==arm]
    d={'other':arm,'n':len(rr)}
    for k in rr[0]:
        if k not in ['id','dataset','other']:d[k]=mean(r[k] for r in rr)
    d['rr_improved']=sum(r['delta_mrr']>1e-12 for r in rr)
    d['rr_worsened']=sum(r['delta_mrr']<-1e-12 for r in rr)
    transition_summary.append(d)
write('diagnostic_transition_summary.csv',transition_summary)
strata=[]
for (ds,ft) in sorted({(r['dataset'],r['fault_type']) for r in metrics}):
    for arm in ARMS:
        rr=[r for r in metrics if r['dataset']==ds and r['fault_type']==ft and r['arm']==arm]
        strata.append({'dataset':ds,'fault_type':ft,'arm':arm,'n':len(rr),
                       **{k:mean(r[k] for r in rr) for k in ['mrr','tolerant_mrr','invalid','zero_optional_role_fraction','root_optional_role_recall']}})
write('mechanism_fault_strata.csv',strata)

# Descriptive exemplars: first hash in each predeclared outcome stratum and dataset.
# Not a prevalence sample and not chosen by attractive wording of explanations.
selection=[]
for ds in ('aiops2022','aiops2025','aegislab'):
    for kind in ('U_top1_V_miss','V_top1_U_miss','U_top1_CVC_miss','CVC_top1_U_miss'):
        aa,bb=('A_UNIFORM_E50','V_FULL') if kind.startswith('U_top1_V_') else ('V_FULL','A_UNIFORM_E50') if kind.startswith('V_top1_') else ('A_UNIFORM_E50','CVC_E50') if kind.startswith('U_top1_CVC_') else ('CVC_E50','A_UNIFORM_E50')
        eligible=[i for i in ids if calls[i,aa]['dataset']==ds and float(calls[i,aa]['ac@1'])==1 and float(calls[i,bb]['tolerant_mrr'])==0]
        oid=min(eligible,key=lambda i:hashlib.sha256(('pruning-diagnosis-v1|'+i).encode()).hexdigest()) if eligible else None
        selection.append({'dataset':ds,'stratum':kind,'eligible':len(eligible),'id':oid})
chosen={r['id'] for r in selection if r['id']}
save('mechanism_example_selection.json',selection)
save('mechanism_example_answers.json',[r for r in outputs if r['id'] in chosen and r['arm'] in
     ['V_FULL','A_UNIFORM_E50','CVC_E50','UNARY_E50','SCOPE_E50','S2PRUNE_E50','DART_E50','GPRUNE_E50']])
save('mechanism_verification.json',{'status':'passed','new_model_calls':0,'cases':220,
    'conditions':len(ARMS),'actual_mask_response_pairs':len(metrics),'outcome_conservation_error_max':
    max(abs(r['delta_mrr']-r['delta_tolerant']-r['interface_penalty_difference']) for r in pairrows),
    'scope':'Retrospective descriptive association. Optional-support contact is not readable evidence or causal mediation.',
    'source_hashes':SOURCES})
print('Completed mechanism audit',len(metrics),'rows',flush=True)
