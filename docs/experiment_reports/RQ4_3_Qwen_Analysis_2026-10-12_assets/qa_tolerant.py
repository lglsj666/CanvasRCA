"""User-requested post-hoc QA tolerance and linked-answer audit; no new calls.

Rules: parse original complete JSON; exact q keys take precedence; otherwise
only punctuation/case aliases of q1..q6 with one unambiguous value qualify.
Score each available question independently. For structured subanswers, decode
one valid JSON-string object, select only requested fields, normalize punctuation
around field names, and strip a trailing right-arrow from a relation type. Never
reverse relation endpoints. Preserve expected numeric precision,
entity ID, unit, phase and direction. No reconstruction of malformed JSON, no
identifier guessing, no truth-dependent choice among conflicting answers.
"""
import json,re,hashlib,warnings
from pathlib import Path
from collections import defaultdict,Counter
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from RQs.RQ4_3.src.utils import score_context,score_factual

ROOT=Path.cwd();OUT=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text())
def save(name,x):(OUT/name).write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def table(name,x):pd.DataFrame(x).to_csv(OUT/name,index=False)
snap=read(OUT/'snapshot.json');queue=read(ROOT/snap['queue_path']);items={x['key']:x for x in queue['items']}
records={x['key']:read(ROOT/x['path']) for x in snap['items']};main=pd.read_csv(OUT/'calls.csv');qrecords={};questions=[];rows=[];audits=[]
def extract(raw):
    try:a=json.loads(raw)
    except ValueError:return {},{'status':'unparseable_full_JSON','aliases':{},'conflicts':[]}
    if not isinstance(a,dict):return {},{'status':'nonobject','aliases':{},'conflicts':[]}
    out={};aliases={};conflicts=[]
    for n in range(1,7):
        q='q'+str(n)
        if q in a:out[q]=a[q];continue
        options=[(k,v) for k,v in a.items() if re.fullmatch(r'[\s.():]*q'+str(n)+r'[\s.():]*',k,re.I)]
        values={json.dumps(v,sort_keys=True,ensure_ascii=False) for k,v in options}
        if len(values)==1:out[q]=options[0][1];aliases[q]=[k for k,v in options]
        elif len(values)>1:conflicts.append(q)
    return out,{'status':'parsed','aliases':aliases,'conflicts':conflicts}

def subanswer(q,value):
    fields={'q2':['entity_id','unit'],'q5':['entity_id','unit','phase'],
            'q6':['source','type','target']}.get(q)
    if not fields:return value
    if isinstance(value,str):
        try:decoded=json.loads(value)
        except (ValueError,TypeError):decoded=None
        if isinstance(decoded,dict):value=decoded
    if not isinstance(value,dict):return value
    out={}
    for field in fields:
        if field in value:out[field]=value[field]
        else:
            matches=[v for k,v in value.items() if re.fullmatch(r'[\s.():]*'+field+r'[\s.():]*',k,re.I)]
            if len({json.dumps(v,sort_keys=True) for v in matches})==1:out[field]=matches[0]
    for field in ['entity_id','source','target']:
        if isinstance(out.get(field),int) and not isinstance(out[field],bool):out[field]=str(out[field])
    if isinstance(out.get('type'),str):out['type']=re.sub(r'\s*(?:->|→)\s*$','',out['type']).strip().lower()
    return out

# Structural normalization cannot infer a missing value or reverse an edge.
assert subanswer('q2',{'entity_id':'123','unit':'ms','extra':1})=={'entity_id':'123','unit':'ms'}
assert subanswer('q6','{"source":"123","type":"calls ->","target":"456"}')=={'source':'123','type':'calls','target':'456'}
assert subanswer('q5',{'entity_id':'123'})=={'entity_id':'123'}
assert extract('{"Q1":"2",".q1":"3"}')[0]=={}

for key,d in records.items():
    it=items[key]
    if it['task']!='QA':continue
    c=score_context(it);ex,meta=extract(d['response']);ex={q:subanswer(q,v) for q,v in ex.items()}
    # All missing/ambiguous fields explicitly unavailable; this is a private
    # scoring view, never an overwritten model answer or downstream RCA input.
    normalized={q:ex.get(q,'unavailable') for q in ['q1','q2','q3','q4','q5','q6']}
    result=score_factual(json.dumps(normalized),c['packet'],c['visibility'])
    row={'key':key,'id':it['id'],'dataset':it['dataset'],'arm':it['arm'],'strict':d['outcome']['score'],'tolerant':result['score'],
        'coverage':result['coverage'],'conditional_tolerant':result['conditional_score'],'parseable':meta['status']=='parsed',
        'strict_valid':d['outcome']['status']=='complete','extracted_questions':len(ex),'alias_questions':len(meta['aliases']),
        'ambiguous_questions':len(meta['conflicts']),'applicable':result['applicable'],'backend':d['usage'].get('backend','hf_legacy')}
    assert row['tolerant']+1e-12>=row['strict']
    rows.append(row);qrecords[(it['id'],it['arm'])]={'row':row,'extracted':ex,'meta':meta,'questions':{},'raw':d['response']}
    for q,truth in c['packet']['questions'].items():
        if not truth['applicable']:continue
        rr=result['questions'][q];qr={'key':key,'id':it['id'],'dataset':it['dataset'],'arm':it['arm'],'question':q,
            'kind':truth['kind'],'strict_correct':d['outcome']['questions'][q]['correct'],'correct':rr['correct'],'matches':rr['matches'],
            'visible':rr['visible'],'extracted':q in ex,'answer':json.dumps(ex.get(q),ensure_ascii=False),'truth':json.dumps(truth['answer'],ensure_ascii=False)}
        questions.append(qr);qrecords[(it['id'],it['arm'])]['questions'][q]=qr
table('qa_tolerant_calls.csv',rows);table('qa_tolerant_questions.csv',questions)
qd=pd.DataFrame(rows);summ=[]
for a,d in qd.groupby('arm'):
    for ds in ['aiops2022','aiops2025','aegislab','ALL']:
        p=d if ds=='ALL' else d[d.dataset==ds]
        summ.append({'arm':a,'dataset':ds,'n':len(p),'strict':p.strict.mean(),'tolerant':p.tolerant.mean(),'conditional_tolerant':p.conditional_tolerant.mean(),
            'strict_valid':int(p.strict_valid.sum()),'parseable':int(p.parseable.sum()),'aliases':int(p.alias_questions.sum()),'coverage':p.coverage.mean()})
table('qa_tolerant_summary.csv',summ)
table('qa_tolerant_by_question.csv',pd.DataFrame(questions).groupby(['arm','question']).agg(n=('id','count'),strict_correct=('strict_correct','sum'),tolerant_correct=('correct','sum'),visible=('visible','sum'),extracted=('extracted','sum')).reset_index().to_dict('records'))

# For U, use the already-run contemporary full independent REPEAT for the
# linked-answer description, not the historical BASE. Never substitute that
# 60-case cohort for the historical 220-case performance baseline.
linked=[];corr=[];paired=[]
for (oid,a),qr in qrecords.items():
    variant='REPEAT' if a=='U' else 'BASE';rk=oid+'__'+a+'__'+variant
    if rk not in records:continue
    r=records[rk];ans=json.loads(r['response']);reason=ans.get('reason','');ids=ans.get('services',[])
    target_entities=set();qa_entities=set()
    for q in qr['questions'].values():
        truth=json.loads(q['truth']);response=json.loads(q['answer'])
        if isinstance(truth,dict):target_entities.update(str(truth[k]) for k in ['entity_id','source','target'] if k in truth)
        if isinstance(response,dict):qa_entities.update(str(response[k]) for k in ['entity_id','source','target'] if k in response)
    mention=lambda entity:bool(re.search(r'(?<!\d)'+re.escape(entity)+r'(?!\d)',reason))
    mt=main[main.key==rk].iloc[0]
    linked.append({'id':oid,'dataset':qr['row']['dataset'],'arm':a,'qa_key':qr['row']['key'],'rca_key':rk,'qa_strict':qr['row']['strict'],
        'qa_tolerant':qr['row']['tolerant'],'rr':r['outcome']['metrics']['mrr'],'target_entities_in_top5':len(target_entities&set(ids)),
        'rr_tolerant':float(mt.tolerant_mrr),
        'QA_answer_entities_in_top5':len(qa_entities&set(ids)),'reason_mentions_target':any(mention(x) for x in target_entities),
        'reason_mentions_QA_answer_entity':any(mention(x) for x in qa_entities),'reason':reason,'ranked':json.dumps(ids),
        'same_backend':qr['row']['backend']==r['usage'].get('backend','hf_legacy')})
ld=pd.DataFrame(linked);table('qa_rca_linked.csv',linked)
for a,d in ld.groupby('arm'):
    for field in ['qa_strict','qa_tolerant']:
        for outcome in ['rr','rr_tolerant']:
            if d[field].nunique()>1 and d[outcome].nunique()>1:
                result=spearmanr(d[field],d[outcome]);rho=float(result.statistic);p=float(result.pvalue)
            else:rho=p=None
            corr.append({'arm':a,'measure':field,'rca_measure':outcome,'n':len(d),'rho':rho,'p_descriptive':p})
for a,b in [('P_LOCAL_BI','U'),('P_LOCAL_BI','C_GLOBAL_BI')]:
    da=ld[ld.arm==a].set_index('id');db=ld[ld.arm==b].set_index('id');ids=sorted(set(da.index)&set(db.index))
    dx=da.loc[ids].qa_tolerant-db.loc[ids].qa_tolerant;dy=da.loc[ids].rr-db.loc[ids].rr
    z=spearmanr(dx,dy) if dx.nunique()>1 and dy.nunique()>1 else None
    agree=tot=0;wrong_agree=0
    for oid in ids:
        qa=qrecords[(oid,a)]['questions'];qb=qrecords[(oid,b)]['questions']
        for question in set(qa)&set(qb):
            xa,xb=qa[question],qb[question]
            if not xa['extracted'] or not xb['extracted']:continue
            tot+=1;equal=json.loads(xa['answer'])==json.loads(xb['answer']);agree+=equal
            wrong_agree+=equal and not xa['matches'] and not xb['matches']
    paired.append({'a':a,'b':b,'n':len(ids),'delta_QA_tolerant':float(dx.mean()),'delta_RR':float(dy.mean()),
        'delta_spearman':float(z.statistic) if z else None,'p_descriptive':float(z.pvalue) if z else None,
        'both_extracted_question_pairs':tot,'identical_answer_pairs':agree,'identical_wrong_answer_pairs':wrong_agree})
table('qa_rca_correlations.csv',corr);table('qa_paired_answer_agreement.csv',paired)
selected=[]
for ds in ['aiops2022','aiops2025','aegislab']:
    ids=sorted(set(qd[qd.dataset==ds].id),key=lambda oid:hashlib.sha256(('rq43-qa-linked-audit-v1|'+oid).encode()).hexdigest())[:4]
    selected.extend(ids)
for oid in selected:
    for a in ['U','P_LOCAL_BI','C_GLOBAL_BI']:
        qr=qrecords[(oid,a)];lr=next(x for x in linked if x['id']==oid and x['arm']==a)
        audits.append({'id':oid,'dataset':qr['row']['dataset'],'arm':a,'qa_strict':qr['row']['strict'],'qa_tolerant':qr['row']['tolerant'],
            'qa_raw':qr['raw'],'questions':qr['questions'],'extraction':qr['meta'],'rca':lr})
save('qa_linked_manual_sample.json',audits)
save('qa_tolerance_protocol.json',{'status':'posthoc_user_requested','original_strict_scores_preserved':True,'rule':__doc__,
    'numeric_units_entities_direction_unchanged':True,'missing_ambiguous_unparseable':0,'full_question_denominator_preserved':True,
    'new_model_calls':0,'analysis_cannot_be_fed_to_running_RCA':True,'manual_sample_cases':12,'manual_sample_pairs':len(audits),
    'U_linked_RCA':'contemporary REPEAT; main historical U BASE remains unchanged'})
print(json.dumps(summ,ensure_ascii=False,indent=2))
print('paired',json.dumps(paired,ensure_ascii=False))
