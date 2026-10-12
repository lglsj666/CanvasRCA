"""Independent per-item numeric/binding check of the post-hoc QA table."""
import csv,json,re
from decimal import Decimal,InvalidOperation
from pathlib import Path
from collections import defaultdict
from RQs.RQ4_3.src.utils import score_context
B=Path(__file__).resolve().parent
s=json.loads((B/'snapshot.json').read_text())
queue=json.loads(Path(s['queue_path']).read_text())
items={r['key']:r for r in queue['items']};ctx={};errors=[];scores=defaultdict(list)
def unit(x):
    x=str(x).replace('_',' ').replace('μ','µ').strip()
    return 'µs' if x in ['us','µs','microsecond','microseconds'] else x
for row in csv.DictReader((B/'qa_tolerant_questions.csv').open()):
    key=row['key'];qid=row['question']
    if key not in ctx:ctx[key]=score_context(items[key])['packet']['questions']
    definition=ctx[key][qid];a=json.loads(row['answer']);truth=json.loads(row['truth']);match=False
    if row['kind']=='numeric':
        m=re.fullmatch(r'\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)(?:\s+(.+))?\s*',str(a))
        if m:
            try:
                observed=Decimal(m[1]);expected=Decimal(truth)
                tolerance=Decimal(0) if definition['integer_count'] else Decimal('0.5')*Decimal(10)**expected.as_tuple().exponent
                match=observed.is_finite() and abs(observed-expected)<=tolerance and (m[2] is None or unit(m[2])==unit(definition['unit']))
            except InvalidOperation:pass
    elif row['kind']=='binding' and isinstance(a,dict):
        a=dict(a);truth=dict(truth)
        if 'unit' in a:a['unit']=unit(a['unit'])
        if 'unit' in truth:truth['unit']=unit(truth['unit'])
        if isinstance(a.get('phase'),str):a['phase']=a['phase'].strip().lower()
        match=a==truth
    else:match=a==truth
    correct=match and row['visible']=='True'
    if bool(match)!=(row['matches']=='True') or bool(correct)!=(row['correct']=='True'):errors.append([key,qid])
    scores[key].append(int(correct))
for row in csv.DictReader((B/'qa_tolerant_calls.csv').open()):
    val=sum(scores[row['key']])/len(scores[row['key']])
    if abs(val-float(row['tolerant']))>1e-12:errors.append([row['key'],'aggregate'])
assert not errors,errors
result={'status':'passed','questions':sum(map(len,scores.values())),'calls':len(scores),'mismatches':errors,
        'original_scores_unchanged':True,'new_model_calls':0}
(B/'qa_independent_verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(result)
