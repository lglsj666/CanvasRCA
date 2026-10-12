"""Offline, immutable-cutoff analysis. No inference, runner mutation, or new calls.

Run from the repository: PYTHONPATH=src:. <infer python> this_file.py
The snapshot manifest, not a live directory scan, defines every denominator.
"""
import csv, hashlib, json, math, warnings
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon, spearmanr
from scorer import RCAScorer, RCAScorerConfig, score_bound_response, is_granularity_aware_hit
from RQs.RQ4_3.src.utils import rca_schema, score_context, score_factual

ROOT = Path.cwd()
OUT = Path(__file__).resolve().parent
RUN = ROOT / 'RQs/RQ4_3/results/formal_v7'
HIST = ROOT / 'RQs/RQ4_1/results/comparison_coding_v1/final_analysis_v1'
DS = ['aiops2022', 'aiops2025', 'aegislab']
MET = ['mrr','ac@1','ac@3','ac@5','precision@1','precision@3','precision@5','avg@3','avg@5','tolerant_mrr']
def read(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def clean(x):
    if isinstance(x, dict): return {str(k):clean(v) for k,v in x.items()}
    if isinstance(x, (list,tuple)): return [clean(v) for v in x]
    if isinstance(x, np.generic): return clean(x.item())
    if isinstance(x, float) and not math.isfinite(x): return None
    return x
def save(name,x): (OUT/name).write_text(json.dumps(clean(x),ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def table(name,rows): pd.DataFrame(rows).to_csv(OUT/name,index=False)

snap=read(OUT/'snapshot.json');queue=read(ROOT/snap['queue_path'])
assert sha(ROOT/snap['queue_path'])==snap['queue_sha256']
items={i['key']:i for i in queue['items']}
roster={i['id']:i for i in queue['statistical_roster']}
cases=read(ROOT/'RQs/RQ4_1/results/comparison_coding_v1/deployment_v26/request_index.json')['cases']
private={oid:read(ROOT/c['private']) for oid,c in cases.items()}
sc=RCAScorer(RCAScorerConfig.load());marker='__RQ41_INVALID_SLOT_'
tol=RCAScorer(sc.config,hit=lambda p,y:False if p.startswith(marker) else is_granularity_aware_hit(p,y))
records={}; requests={}; rows=[]; qa=[]; detail={}; errors=[]; lineage=[]
def response_metrics(text,oid):
    p=private[oid];c=cases[oid]
    out=score_bound_response(text,c['candidates'],p['numeric_to_natural'],p['accepted_labels'],rca_schema(),sc)
    try:a=json.loads(text)
    except (ValueError,TypeError):a={}
    ids=a.get('services',[]) if isinstance(a,dict) else []
    if not isinstance(ids,list):ids=[]
    legal=[];seen=set();unknown=[];dups=[]
    for k,v in enumerate(ids[:5]):
        if isinstance(v,str) and v in c['candidates'] and v not in seen:legal.append(p['numeric_to_natural'][v])
        else:
            legal.append(marker+str(k))
            (dups if isinstance(v,str) and v in seen else unknown).append(v)
        if isinstance(v,str):seen.add(v)
    metrics=dict(out['metrics']);metrics['tolerant_mrr']=tol.score(legal,p['accepted_labels']).mrr
    for k in (1,3,5):
        metrics[f'precision@{k}']=0. if out['status']=='model_failure' else sum(any(sc.hit(p['numeric_to_natural'][v],y) for y in p['accepted_labels']) for v in ids[:k])/k
    return out,metrics,ids,unknown,dups,a

print('Checking snapshot and rescoring committed outputs',flush=True)
for entry in snap['items']:
    path=ROOT/entry['path'];assert sha(path)==entry['sha256'],path
    d=read(path);key=entry['key'];it=items[key];oid=it['id'];records[key]=d
    assert d['request_hash']==it['identity'],key
    reqpath=RUN/'execution'/d['request_path']
    if str(reqpath) not in requests:requests[str(reqpath)]=read(reqpath)
    req=requests[str(reqpath)]
    lineage.append({'key':key,'completed':entry['path'],'request':str(reqpath.relative_to(ROOT)),
        'request_sha256':sha(reqpath),'image':req.get('image'),'image_manifest':req.get('manifest'),
        'reference':d.get('reference'),'operation':req['operation'],'identity':d['request_hash']})
    u=d['usage'];p=private[oid]
    base={'key':key,'id':oid,'dataset':it['dataset'],'group':roster[oid]['event_group'],'arm':it['arm'],
        'variant':it['variant'],'fault_type':p.get('fault_type'),'root_kind':'/'.join(sorted({p.get('entity_granularity',{}).get(x,'unknown') for x in p['accepted_labels']})),
        'actual_calls':d['actual_calls'],'reference':d.get('reference'), 'backend':u.get('backend',u.get('runtime_revision',d.get('runtime_revision','hf_legacy'))),
        'input':u.get('input_tokens',0),'output':u.get('output_tokens',0),'image_tokens':u.get('image_tokens_retained',0),
        'image_original':u.get('image_tokens_original',0),'total':u.get('input_tokens',0)+u.get('output_tokens',0),
        'model_seconds':u.get('processor_model_seconds'),'vision_seconds':u.get('vision_seconds'),
        'language_seconds':u.get('language_seconds'),'cold_seconds':d.get('continuous_cold_seconds'),
        'cached_seconds':d.get('cached_input_to_validation_seconds'),'compile_seconds':d.get('compile_seconds'),
        'timing_policy':d.get('timing_policy','continuous_cold_including_queue'),
        'attention':bool(u.get('attention_requested')),'attention_error':u.get('attention_error'),
        'attention_missed':u.get('attention_missed',0),'branch_calls':u.get('branch_calls'),
        'output_cap_hit':u.get('output_tokens',0)>=8192,'operation':req['operation'],'historical':False}
    base['text_tokens']=base['input']-base['image_tokens']
    if it['task']=='QA':
        context=score_context(it);expected=score_factual(d['response'],context['packet'],context['visibility'])
        assert expected==d['outcome'],('QA score',key)
        out=d['outcome'];qr={**base,'score':out['score'],'coverage':out['coverage'],'conditional_score':out['conditional_score'],
            'invalid':out['status']=='model_failure','empty_object':d['response'].strip()=='{}','applicable':out['applicable'],
            'questions':out['questions'],'na':out['na']};qa.append(qr)
        detail[key]={'source':entry['path'],'request':str(reqpath.relative_to(ROOT)),'response':d['response']}
    else:
        out,m,ids,unknown,dups,a=response_metrics(d['response'],oid)
        if out!=d['outcome']:errors.append(key)
        row={**base,**m,'invalid':out['status']=='model_failure','unknown':bool(unknown),'duplicate':bool(dups),
            'top1':ids[0] if ids and out['status']=='complete' else '__INVALID__','ranked':json.dumps(ids),
            'confidence':a.get('confidence') if isinstance(a,dict) else None}
        rows.append(row);detail[key]={'source':entry['path'],'request':str(reqpath.relative_to(ROOT)),
            'unknown':unknown,'duplicate':dups,'accepted':p['accepted_labels'],'accepted_numeric':p.get('accepted_label_numeric_ids'),
            'error':out['error'],'reason':a.get('reason') if isinstance(a,dict) else None}

print('Rechecking 440 historical U/T responses with central scorer',flush=True)
hd=read(HIST/'case_details.json');hc=pd.read_csv(HIST/'calls.csv')
for arm,new in [('A_UNIFORM_E50','U'),('T_FULL','T_FULL')]:
    sub=hc[(hc.arm==arm)&(hc.kind=='development')&(hc.variant=='BASE')]
    assert len(sub)==220
    for _,h in sub.iterrows():
        raw=hd[h['key']];oid=h['id'];out,m,ids,unknown,dups,a=response_metrics(raw['response'],oid)
        assert abs(m['mrr']-h['mrr'])<1e-12
        assert abs(m['tolerant_mrr']-h['tolerant_mrr'])<1e-12
        rows.append({'key':h['key'],'id':oid,'dataset':h['dataset'],'group':roster[oid]['event_group'], 'arm':new,'variant':'BASE',
            'fault_type':private[oid].get('fault_type'),'root_kind':'/'.join(sorted({private[oid].get('entity_granularity',{}).get(x,'unknown') for x in private[oid]['accepted_labels']})),
            **m,'invalid':out['status']=='model_failure','unknown':bool(unknown),'duplicate':bool(dups),
            'top1':ids[0] if ids and out['status']=='complete' else '__INVALID__','ranked':json.dumps(ids),'historical':True,
            'input':h['input'],'output':h['output'],'total':h['total'],'text_tokens':h['text_tokens'],
            'image_tokens':h['image_retained'],'image_original':h['image_original'],'model_seconds':h['model_wall'],
            'backend':h['backend'],'confidence':h['confidence'],'output_cap_hit':h['output_cap_hit']})
assert not errors,errors
df=pd.DataFrame(rows);main=df[df.variant=='BASE'];table('calls.csv',rows)
table('input_lineage.csv',lineage);save('case_audit_index.json',detail)

def aggregate(d,expected):
    n=len(d); result={'n':n,'expected':expected,'pending':expected-n}
    for k in MET+['input','output','total','text_tokens','image_tokens','image_original','model_seconds','vision_seconds','language_seconds','cold_seconds','cached_seconds','compile_seconds']:
        if k in d:result[k]=pd.to_numeric(d[k],errors='coerce').mean()
    for k in ['invalid','unknown','duplicate','output_cap_hit']:result[k]=int(d[k].map(lambda v:False if pd.isna(v) else bool(v)).sum())
    result['references']=int(d.get('reference',pd.Series(dtype=object)).notna().sum())
    result['group_mrr']=d.groupby('group').mrr.mean().mean();result['groups']=d.group.nunique()
    for metric in ['mrr','ac@1','ac@3','ac@5']:
        result[metric+'_lower']=d[metric].sum()/expected
        result[metric+'_upper']=(d[metric].sum()+expected-n)/expected
    return result
summary=[]
for arm,d in main.groupby('arm'):
    for ds in DS+['ALL']:
        part=d if ds=='ALL' else d[d.dataset==ds];den=220 if ds=='ALL' else {'aiops2022':60,'aiops2025':60,'aegislab':100}[ds]
        summary.append({'arm':arm,'dataset':ds,**aggregate(part,den)})
    summary.append({'arm':arm,'dataset':'MACRO','n':len(d),'expected':220,**{k:d.groupby('dataset')[k].mean().mean() for k in MET+['total']}})
table('main_summary.csv',summary)
table('fault_summary.csv',[{'arm':a,'dataset':ds,'fault_type':f,**aggregate(d,len(d))} for (a,ds,f),d in main.groupby(['arm','dataset','fault_type'])])
table('granularity_summary.csv',[{'arm':a,'dataset':ds,'root_kind':f,**aggregate(d,len(d))} for (a,ds,f),d in main.groupby(['arm','dataset','root_kind'])])
table('runtime_by_backend.csv',[{'arm':a,'backend':b,'timing_policy':str(p),'n':len(d),
    **{k:pd.to_numeric(d[k],errors='coerce').mean() for k in ['model_seconds','vision_seconds','language_seconds','cold_seconds','cached_seconds','compile_seconds']}}
    for (a,b,p),d in df[~df.historical].groupby(['arm','backend','timing_policy'],dropna=False)])
maps={a:d.set_index('id').to_dict('index') for a,d in main.groupby('arm')}
def wp(v):
    if not np.any(v):return 1.
    with warnings.catch_warnings():
        warnings.simplefilter('ignore');return float(wilcoxon(v,zero_method='pratt',alternative='two-sided',method='approx',correction=False).pvalue)
def calc(values):
    ids=sorted(values);d=np.round([values[i] for i in ids],12);g=defaultdict(list)
    for i,x in zip(ids,d):g[roster[i]['event_group']].append(x)
    gv=np.round([np.mean(v) for v in g.values()],12)
    dz=lambda x:float(np.mean(x)/np.std(x,ddof=1)) if len(x)>1 and np.std(x,ddof=1)>0 else (0. if not np.any(x) else None)
    return {'n':len(d),'groups':len(g),'delta':np.mean(d) if len(d) else None,'group_delta':np.mean(gv) if len(gv) else None,
        'case_p':wp(d),'group_p':wp(gv),'dz':dz(d),'group_dz':dz(gv),'improved':sum(d>0),'worsened':sum(d<0),'tied':sum(d==0)}
vectors={}
def compare(a,b,eligible=True):
    ids=sorted(set(maps.get(a,{}))&set(maps.get(b,{})))
    vals={i:maps[a][i]['mrr']-maps[b][i]['mrr'] for i in ids}
    z=calc(vals);vectors[a+' - '+b]=vals
    for k in ['ac@1','ac@5']:
        z[k+'_repairs']=sum(maps[a][i][k]>maps[b][i][k] for i in ids);z[k+'_breaks']=sum(maps[a][i][k]<maps[b][i][k] for i in ids)
    z['a_mrr']=np.mean([maps[a][i]['mrr'] for i in ids]) if ids else None;z['b_mrr']=np.mean([maps[b][i]['mrr'] for i in ids]) if ids else None
    z['a_total']=np.mean([maps[a][i]['total'] for i in ids]) if ids else None;z['b_total']=np.mean([maps[b][i]['total'] for i in ids]) if ids else None
    lo=hi=0.
    for oid in roster:
        x=maps.get(a,{}).get(oid);y=maps.get(b,{}).get(oid)
        lo+=(x['mrr'] if x else 0)-(y['mrr'] if y else 1)
        hi+=(x['mrr'] if x else 1)-(y['mrr'] if y else 0)
    z.update(a=a,b=b,delta_lower=lo/220,delta_upper=hi/220,status='eligible' if eligible else 'identity_ineligible')
    if not ids:z.update(status='not_run',case_p=1.,group_p=1.)
    elif not eligible:z.update(case_p=1.,group_p=1.)
    return z
def family(name,rr):
    for field in ['case_p','group_p']:
        order=sorted(range(len(rr)),key=lambda j:rr[j][field]);floor=0.
        for rank,j in enumerate(order):floor=max(floor,min(1.,rr[j][field]*(len(rr)-rank)));rr[j][field+'H']=floor
    table(name+'.csv',rr);return rr
primary=family('primary',[compare('X_SRP',a,False) for a in ['U','T_FULL']])
optim=['S_DISTINGUISH','S_REPRESENT','S_JOINT','R_PATCH_PACK','R_HORIZON','R_PACK_HORIZON','P_LOCAL_BI','P_SOFT_IMAGE','P_DUAL']
family('optimization',[compare(a,'U',False) for a in optim])
attribution=[(a,'C_SOURCE_HASH') for a in optim[:3]]+[('R_PATCH_PACK','C_PACK_OFFSET')]+[(a,'C_READ_GUIDE') for a in optim[3:6]]+[
    ('P_LOCAL_BI','C_LOCAL_FORWARD'),('P_LOCAL_BI','C_SHAM_BI'),('R_PATCH_PACK','C_PACK_BG_FILL'),('P_LOCAL_BI','C_GLOBAL_BI')]
family('attribution',[compare(a,b) for a,b in attribution])
inter=[{'X_SR':1,'S_JOINT':-1,'R_PATCH_PACK':-1,'U':1},{'X_SP':1,'S_JOINT':-1,'P_LOCAL_BI':-1,'U':1},
    {'X_RP':1,'R_PATCH_PACK':-1,'P_LOCAL_BI':-1,'U':1}, {'X_SRP':1,'X_SR':-1,'X_SP':-1,'X_RP':-1,'S_JOINT':1,'R_PATCH_PACK':1,'P_LOCAL_BI':1,'U':-1}]
ir=[]
for terms in inter:
    ids=set.intersection(*(set(maps[a]) for a in terms));v={i:sum(k*maps[a][i]['mrr'] for a,k in terms.items()) for i in ids}
    label=json.dumps(terms);vectors[label]=v;z=calc(v);z.update(contrast=label,status='identity_ineligible_and_R_version_mismatch' if 'X_SR' in terms else 'identity_ineligible',case_p=1.,group_p=1.);ir.append(z)
family('interactions',ir)
family('posthoc_system_comparisons',[compare(a,b) for a,b in [('HTML_PLOT_CODE','HTML_SEMANTIC'),('R_PACK_HORIZON','R_PATCH_PACK'),('R_HORIZON','R_PATCH_PACK'),('X_SRP','X_SP'),('X_RP','R_PATCH_PACK'),('X_SRP','X_SR')]])
table('historical_descriptive',[compare(a,b,False) for a in maps if a not in ['U','T_FULL'] for b in ['U','T_FULL']])

print('QA, ordering, and failure analysis',flush=True)
qdf=pd.DataFrame([{k:v for k,v in r.items() if k not in ['questions','na']} for r in qa]);table('qa_calls.csv',qdf.to_dict('records'))
qsum=[];questions=[];qmaps={a:d.set_index('id').to_dict('index') for a,d in qdf.groupby('arm')}
for a,d in qdf.groupby('arm'):
    for ds in DS+['ALL']:
        s=d if ds=='ALL' else d[d.dataset==ds];qsum.append({'arm':a,'dataset':ds,'n':len(s),'invalid':int(s.invalid.sum()),'empty_object':int(s.empty_object.sum()),'score':s.score.mean(),'coverage':s.coverage.mean(),'conditional_score':s.conditional_score.mean(),'applicable_questions':s.applicable.sum()})
for r in qa:
    for k,v in r['questions'].items():questions.append({'arm':r['arm'],'id':r['id'],'dataset':r['dataset'],'question':k,**v})
table('qa_summary.csv',qsum);table('qa_questions.csv',questions)
table('qa_question_summary.csv',pd.DataFrame(questions).groupby(['arm','question']).agg(n=('id','count'),correct=('correct','sum'),visible=('visible','sum'),unavailable=('unavailable','sum')).reset_index().to_dict('records'))
mechanism=[]
for a,b in [(a,'U') for a in ['S_DISTINGUISH','S_REPRESENT','R_PATCH_PACK','R_HORIZON','P_LOCAL_BI','X_SRP']]+[('R_PATCH_PACK','C_PACK_BG_FILL'),('P_LOCAL_BI','C_GLOBAL_BI')]:
    ids=set(qmaps.get(a,{}))&set(qmaps.get(b,{}));vals={i:qmaps[a][i]['score']-qmaps[b][i]['score'] for i in ids};z=calc(vals)
    z.update(a=a,b=b,measure='QA',status='eligible' if ids else 'not_run');mechanism.append(z);vectors['QA '+a+' - '+b]=vals
rep=[]
for a in ['U','P_LOCAL_BI']:
    subsets={v:df[(df.arm==a)&(df.variant==v)].set_index('id').to_dict('index') for v in ['ORDER','REPEAT']}
    ids=set(maps[a])&set(subsets['ORDER'])&set(subsets['REPEAT'])
    for ds in DS+['ALL']:
        ii=[i for i in ids if ds=='ALL' or roster[i]['dataset']==ds]
        rr={'arm':a,'dataset':ds,'n':len(ii),'base_mrr':np.mean([maps[a][i]['mrr'] for i in ii])}
        for v in ['ORDER','REPEAT']:
            rr[v+'_mrr']=np.mean([subsets[v][i]['mrr'] for i in ii]);rr[v+'_top1_flips']=sum(subsets[v][i]['top1']!=maps[a][i]['top1'] for i in ii)
            rr[v+'_rank_changes']=sum(subsets[v][i]['ranked']!=maps[a][i]['ranked'] for i in ii)
            valid=[i for i in ii if not subsets[v][i]['invalid'] and not maps[a][i]['invalid']]
            rr[v+'_both_valid_n']=len(valid);rr[v+'_valid_flips']=sum(subsets[v][i]['top1']!=maps[a][i]['top1'] for i in valid)
        rep.append(rr)
    vals={i:int(subsets['ORDER'][i]['top1']!=maps[a][i]['top1'])-int(subsets['REPEAT'][i]['top1']!=maps[a][i]['top1']) for i in ids};z=calc(vals);vectors[a+' order excess flips']=vals
    z.update(a=a,measure='order_excess_flip',status='eligible' if a!='U' else 'identity_ineligible')
    if a=='U':z.update(case_p=1.,group_p=1.)
    mechanism.append(z)
    vals={i:subsets['ORDER'][i]['mrr']-maps[a][i]['mrr'] for i in ids};z=calc(vals);vectors[a+' order RR']=vals
    z.update(a=a,measure='order_RR',status='eligible' if a!='U' else 'identity_ineligible')
    if a=='U':z.update(case_p=1.,group_p=1.)
    mechanism.append(z)
family('mechanism',mechanism);table('repeat_order.csv',rep);save('contrast_vectors.json',vectors)
table('output_failures.csv',[{**r,'error':detail[r['key']]['error'],'unknown_values':detail[r['key']]['unknown'],'duplicate_values':detail[r['key']]['duplicate']} for r in rows if not r['historical'] and r['invalid']])
table('confidence.csv',[{'arm':a,'confidence':c,'n':len(d),'mrr':d.mrr.mean(),'ac1':d['ac@1'].mean()} for (a,c),d in main.groupby(['arm','confidence'],dropna=False)])

common=set.intersection(*(set(maps[a]) for a in maps));table('all_arm_common_cases.csv',[{'arm':a,**aggregate(main[(main.arm==a)&main.id.isin(common)],len(common))} for a in maps])
save('integrity.json',{'snapshot_positions':len(records),'RCA_new_positions':len(df[~df.historical]),'QA_positions':len(qa),
    'historical_rechecked':440,'RCA_score_mismatches':errors,'QA_scores_rechecked':len(qa),'request_identity_errors':0,
    'historical_compatibility':'not_demonstrated; historical inferential slots p=1',
    'event_groups':{ds:len({x['event_group'] for x in roster.values() if x['dataset']==ds}) for ds in DS},
    'actual_completed_calls':sum(d['actual_calls'] for d in records.values()),'references':sum(d['actual_calls']==0 for d in records.values()),
    'attention_requested_actual':sum(bool(d['usage'].get('attention_requested')) for d in records.values() if d['actual_calls']),
    'attention_error_count':sum(bool(d['usage'].get('attention_error')) for d in records.values() if d['actual_calls']),
    'attention_missed':sum(d['usage'].get('attention_missed',0) for d in records.values() if d['actual_calls']),
    'all_arm_common_cases':len(common),'new_model_calls_for_analysis':0,'source':str(Path(__file__).relative_to(ROOT))})
print('Core tables complete',flush=True)
