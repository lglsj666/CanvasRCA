"""Public-only, deterministic fact transfer and QA compilation; no IO or labels."""
from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP, localcontext
import json
import math
import re
from .utils import ARMS, MODEL, VERSION, stable_hash
from RQs.RQ3_18.src import exps as previous

F,C,A,V,CR,VR,*_ = ARMS
REPEATS={CR,VR}
QA={'C_Q0','C_Q1','V_Q0','V_Q1'}
VISUAL={A,V,VR,'V_Q0','V_Q1','V_RB','V_RP'}
COMPACT_GUIDE=('Lossless record tables: table_columns names the fields of every table_rows row, in that order; '
               'a table replaces repeated object keys, retaining all values and their original record order. '
               'All original units, missing/null entries, relative times and source meanings are retained.')
VISUAL_GUIDE=('Image decoding: I1 is the left population panel (PAIR01); I2, when present, is the right panel (PAIR02). '
 'An @I1.field or @I2.field entry delegates that exact field to the named panel. Other values remain in text. '
 'Parent and Child identify recorded calls; operation labels bind each endpoint. All durations are inclusive milliseconds. '
 'Lavender is Reference; teal is Current. Rows compare parent p50/p95 and child p50/p95 over all eligible requests. '
 'Population n and text sample n are distinct; their counts are Reference then Current. '
 'Positions use log1p(duration_ms), with millisecond ticks and a common range within each panel. '
 'Rounded labels do not replace more precise text values. Segments compare phases; they are not trajectories, '
 'local execution, waiting time or causal propagation.')
TRANSFER_PAIR_HEADER=(previous.pairs.GUIDE+
    'Pair fields: [id,[parent_ref_p95,child_ref_p95],phases]. Parent/child entities, operation names and '
    'phase population n are supplied by the corresponding image panel. '
    'Phase: [name,counts[notSlow/notSlow,notSlow/slow,slow/notSlow,slow/slow]].\n')
QA_SYSTEM='Answer the supplied telemetry reading questions using only the provided evidence. Return the required JSON object.'
QA_GUIDE=('Telemetry QA, not root-cause diagnosis. Numeric IDs are case-local entities. Preserve source units, '
 'duration type, operation, relation direction and reference/current phase. Relative observations do not establish causality. '
 'Answer each of the six questions independently in the specified fields; give no ranking or extra explanation.')


def dumps(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'),allow_nan=False)


def display_number(value):
    """Mirror the existing renderer's visible n(); independent JS/DOM check in CPU."""
    if value==0:return '0'
    scientific=value>=1e5 or value<.001
    with localcontext() as context:
        context.prec=400;d=Decimal.from_float(float(value));exponent=d.adjusted()
        rounded=d.quantize(Decimal(1).scaleb(exponent-(3 if scientific else 4)),rounding=ROUND_HALF_UP)
        if scientific:
            exponent=rounded.adjusted();return f'{rounded.scaleb(-exponent):.3f}e{exponent:+d}'
        text=format(rounded,'f');return text.rstrip('0').rstrip('.') if '.' in text else text


def pack(value):
    if isinstance(value,dict):
        if 'table_columns' in value or 'table_rows' in value:raise ValueError('Reserved codec field')
        return {k:pack(v) for k,v in value.items()}
    if isinstance(value,list):
        if len(value)>=2 and all(isinstance(x,dict) for x in value) and all(list(x)==list(value[0]) for x in value):
            columns=list(value[0]);table={'table_columns':columns,'table_rows':[[pack(x[k]) for k in columns] for x in value]}
            if len(dumps(table))<len(dumps(value)):return table
        return [pack(x) for x in value]
    return value


def unpack(value):
    if isinstance(value,dict):
        if set(value)=={'table_columns','table_rows'}:
            return [dict(zip(value['table_columns'],[unpack(x) for x in row])) for row in value['table_rows']]
        return {k:unpack(v) for k,v in value.items()}
    return [unpack(x) for x in value] if isinstance(value,list) else value


def json_line(line):
    """Only whole JSON records or known textual prefixes, never regex inside literals."""
    start=next((i for i,ch in enumerate(line) if ch in '[{'),-1)
    if start<0:return None
    prefix=line[:start]
    if prefix and not re.fullmatch(r'[A-Za-z_]+: ',prefix):return None
    try:return prefix,json.loads(line[start:])
    except ValueError:return None


def compact_text(text):
    lines=text.splitlines(keepends=True);out=[];i=0
    while i<len(lines):
        line=lines[i];parsed=json_line(line)
        if parsed is None:out.append(line);i+=1;continue
        prefix,value=parsed;run=[value];j=i+1
        while j<len(lines) and isinstance(value,dict):
            other=json_line(lines[j])
            if other is None or other[0]!=prefix or not isinstance(other[1],dict) or list(other[1])!=list(value):break
            run.append(other[1]);j+=1
        if len(run)>1 and isinstance(pack(run),dict):
            out.append(prefix+dumps({'record_table':pack(run)})+ ('\n' if lines[j-1].endswith('\n') else ''));i=j
        else:out.append(prefix+dumps(pack(value))+ ('\n' if line.endswith('\n') else ''));i+=1
    return ''.join(out)


def semantic_lines(text):
    """Decode table records; narrative is retained exactly, including ordering."""
    result=[]
    for line in text.splitlines():
        item=json_line(line)
        if item is None:result.append(('text',line));continue
        prefix,raw=item;v=unpack(raw)
        if isinstance(raw,dict) and set(raw)=={'record_table'}:
            result.extend(('json',prefix,x) for x in v['record_table'])
        else:result.append(('json',prefix,v))
    return result


def transfer_inventory(payload):
    facts=[]
    for i,r in enumerate(payload['relations'],1):
        for k in ('parent','child','parent_operation','child_operation'):
            facts.append({'relation':r['id'],'field':k,'value':r[k],'token':f'@I{i}.{k}',
                          'binding':r['id']+'.'+k,'source':f'relations.{i-1}.{k}'})
        for phase in ('reference','current'):
            facts.append({'relation':r['id'],'field':phase+'.n','value':r['phases'][phase]['n'],
                          'token':f'@I{i}.population_n.{phase}','binding':r['id']+'.support',
                          'source':f'relations.{i-1}.phases.{phase}.n'})
            for endpoint in (0,1):
                for q in (0,1):
                    v=r['phases'][phase]['quantiles'][endpoint][q]
                    if float(display_number(v))==v:
                        field=f'{phase}.quantiles.{endpoint}.{q}'
                        facts.append({'relation':r['id'],'field':field,'value':v,
                            'token':f'@I{i}.{"parent" if endpoint==0 else "child"}.p{50 if q==0 else 95}.{phase}',
                            'binding':f'{r["id"]}.quantile.{2*endpoint+q}.{phase}',
                            'source':f'relations.{i-1}.phases.{phase}.quantiles.{endpoint}.{q}'})
    return facts


def replace_pair_parts(parts,payload,facts):
    result=deepcopy(parts);lookup={(f['relation'],f['field']):f['token'] for f in facts};body=0
    get=lambda r,k,old:lookup.get((r,k),old)
    for part in result:
        text=part['text']
        if text.startswith(previous.pairs.GUIDE):
            head,raw=text.rsplit('\n',1);rows=json.loads(raw)
            reduced=[]
            for row in rows:
                reduced.append([row[0],row[5],[[phase[0],phase[2]] for phase in row[6]]])
                body+=4+len(row[6])
            part['text']=TRANSFER_PAIR_HEADER+dumps(reduced)
        elif text.startswith('Continuous pair fields:'):
            head,raw=text.rsplit('\n',1);rows=json.loads(raw)
            for rid,phases in rows:
                for phase in phases:
                    for e in (0,1):
                        for q in (0,1):
                            old=phase[1][e][q];phase[1][e][q]=get(rid,f'{phase[0]}.quantiles.{e}.{q}',old)
                            body+=int(phase[1][e][q]!=old)
            part['text']=head+'\n'+dumps(rows)
        elif text.startswith('Repeated named population readout;'):
            packet=deepcopy(previous.readout_packet(payload,'unused'))
            lines=['Named population readout; inclusive span durations, milliseconds.']
            for r in packet['relations']:
                d=r['data']
                for j,p in enumerate(('reference','current')):
                    for e in (0,1):
                        for q in (0,1):d['quantiles'][2*e+q][j]=get(r['id'],f'{p}.quantiles.{e}.{q}',d['quantiles'][2*e+q][j])
                lines.append(f"{r['id']}: entities, operations and population counts are in the corresponding image panel.")
                lines.append(f"Reference/current text sample n={d['sampled'][0]}/{d['sampled'][1]}.")
                for label,values in zip(('parent p50','parent p95','child p50','child p95'),d['quantiles']):
                    lines.append(f'{label}: reference={values[0]!r} ms; current={values[1]!r} ms (population, inclusive).')
            part['text']='\n'.join(lines)
    return result,body


def public_edges(inherited):
    result=[]
    for part in inherited['texts']['READOUT_TEXT']:
        for line in part['text'].splitlines():
            parsed=json_line(line)
            if parsed is None:continue
            value=parsed[1]
            if isinstance(value,dict) and set(value)=={'columns','rows'}:
                for row in value['rows']:
                    item=dict(zip(value['columns'],row));data=item.get('data',{})
                    for edge in data.get('edges',[]):
                        if len(edge)==3 and edge[2]=='calls':result.append((item['id'],*edge))
    return result


def qa_packet(inherited):
    if not inherited['payload']['relations']:return None
    edges=public_edges(inherited)
    if not edges:return None
    r=inherited['payload']['relations'][0];ref,cur=(r['phases'][p] for p in ('reference','current'))
    card,source,target,kind=edges[0]
    comparison=lambda a,b:'greater' if a>b else 'less' if a<b else 'equal'
    questions=[
      f"Q1: What is the reference population request count for {r['id']}? Return the integer count.",
      f"Q2: What are the duration unit and duration type (inclusive or exclusive) in {r['id']}?",
      f"Q3: Give the child entity ID and child operation for {r['id']}.",
      f'Q4: Give source, target and relation type of the first listed calls edge in {card}.',
      f"Q5: Is current parent p50 greater than, less than, or equal to reference parent p50 in {r['id']}?",
      f"Q6: Is reference parent p95 greater than, less than, or equal to reference child p95 in {r['id']}?"]
    answers={'q1':ref['n'],'q2':{'unit':'ms','duration_type':'inclusive'},
             'q3':{'entity':r['child'],'operation':r['child_operation']},
             'q4':{'source':source,'target':target,'relation':kind},
             'q5':comparison(cur['quantiles'][0][0],ref['quantiles'][0][0]),
             'q6':comparison(ref['quantiles'][0][1],ref['quantiles'][1][1])}
    statements=[f"{r['id']} reference population n: {ref['n']}.",
      f"{r['id']} duration unit: ms; duration type: inclusive.",
      f"{r['id']} child entity: {r['child']}; child operation: {r['child_operation']}.",
      f'{card} first calls edge: source {source}; target {target}; relation {kind}.',
      f"{r['id']} parent p50 current {cur['quantiles'][0][0]!r} ms is {answers['q5']} than reference {ref['quantiles'][0][0]!r} ms.",
      f"{r['id']} reference parent p95 {ref['quantiles'][0][1]!r} ms is {answers['q6']} than child p95 {ref['quantiles'][1][1]!r} ms."]
    sources=['relations.0.phases.reference.n','RequestPairPacketV1.GUIDE',
             'relations.0.child/child_operation',f'complete_relation_ledger.{card}.first_calls_edge',
             'relations.0.phases.{current,reference}.quantiles.0.0','relations.0.phases.reference.quantiles.{0,1}.1']
    # Same named records; question-aligned versus source-order grouping. Neither hides binding.
    b='Correct public readouts:\n'+'\n'.join(statements)
    p='Correct public readouts:\n'+'\n'.join(statements[i] for i in (3,2,1,0,4,5))
    return {'schema':'DiagnosticQAPacketV1','questions':questions,'answers':answers,'sources':sources,
            'bound_readout':b,'source_readout':p,'statement_records':statements}


def qa_schema():
    string={'type':'string'}
    def obj(properties):return {'type':'object','properties':properties,'required':list(properties),'additionalProperties':False}
    compare={'type':'string','enum':['greater','less','equal']}
    return {'type':'json_schema','json_schema':{'name':'telemetry_qa','strict':True,'schema':obj({
      'q1':{'type':'integer','minimum':0},'q2':obj({'unit':string,'duration_type':string}),
      'q3':obj({'entity':string,'operation':string}),
      'q4':obj({'source':string,'target':string,'relation':string}),'q5':compare,'q6':compare})}}


def score_qa(packet,response):
    import jsonschema
    try:
        answer=json.loads(response);jsonschema.validate(answer,qa_schema()['json_schema']['schema'])
    except (ValueError,TypeError,jsonschema.ValidationError):
        return {'status':'model_failure','metrics':{'qa_accuracy':0.,'reading':0.,'binding':0.,'comparison':0.},'per_question':[False]*6}
    # Prospective semantic equivalence for unit/type spelling; preserve exact
    # entity/operation identity and numeric comparisons. Never use RCA labels.
    for key in ('unit','duration_type'):
        answer['q2'][key]=answer['q2'][key].strip().casefold()
    if answer['q2']['unit'] in ('millisecond','milliseconds'):answer['q2']['unit']='ms'
    correct=[answer[f'q{i}']==packet['answers'][f'q{i}'] for i in range(1,7)]
    return {'status':'complete','metrics':{'qa_accuracy':sum(correct)/6,
      **{k:sum(correct[2*i:2*i+2])/2 for i,k in enumerate(('reading','binding','comparison'))}},'per_question':correct}


def compile_public(inherited,c):
    previous.visible_audit(inherited)
    full=deepcopy(inherited['texts']['READOUT_TEXT']);compact=[{'type':'text','text':compact_text(p['text'])} for p in full]
    for old,new in zip(full,compact):
        if semantic_lines(old['text'])!=semantic_lines(new['text']):raise ValueError('Lossless compaction failed')
    compact.insert(1,{'type':'text','text':COMPACT_GUIDE})
    transfer=transfer_inventory(inherited['payload'])
    replace,count=replace_pair_parts(compact,inherited['payload'],transfer)
    texts={F:full,C:compact,A:deepcopy(compact),V:replace,CR:deepcopy(compact),VR:deepcopy(replace)}
    qa=qa_packet(inherited)
    for arm in ARMS[6:]:
        basis=C if arm.startswith('C_') else V
        parts=deepcopy(texts[basis])
        if arm in QA:
            # Remove RCA task, reading/causal strategy guides, output cardinality and final task.
            parts=[p for p in parts if not any(p['text'].startswith(s) for s in (
                'A fault has occurred','Source reading:','Literal reading and evidence citations:',
                'Output cardinality for this request:','Based on the above'))]
            parts.insert(0,{'type':'text','text':QA_GUIDE})
        if qa:
            if arm.endswith(('Q1','RB','RP')):
                parts.insert(-1 if arm not in QA else len(parts),{'type':'text','text':qa['source_readout' if arm.endswith('RP') else 'bound_readout']})
            if arm in QA:parts.append({'type':'text','text':'\n'.join(qa['questions'])})
        texts[arm]=parts
    canonical={a:a for a in ARMS}
    if not inherited['payload']['relations']:canonical.update({A:C,V:C})
    public={k:deepcopy(inherited[k]) for k in ('system','candidates','payload','readout','facts_hash','base_facts_hash')}
    public.update(texts=texts,images={},canonical_arms=canonical,infeasible={},output_adapter=c['output_adapter']['version'],
                  transfer=transfer,body_transfer_count=count,qa=qa)
    visible_audit(public);return public


def system_for(public,arm):return QA_SYSTEM if arm in QA else public['system']


def request_envelope(arm,system):
    from RQs.RQ3_1.src.main import _request_envelope
    value=_request_envelope(MODEL,system=system)
    if arm in QA:value['schema']=qa_schema()
    else:value['schema']=previous.schema_for(previous.F,value['schema'])
    value['policy_version']=VERSION
    return value


def parts_for(public,arm,png=None):
    if arm in QA and public['qa'] is None:raise ValueError('QA-ineligible request')
    parts=deepcopy(public['texts'][arm])
    if arm in VISUAL and public['payload']['relations']:
        if not isinstance(png,bytes) or not png.startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('Qualified unified PNG required')
        return [{'type':'image','png':png},{'type':'text','text':VISUAL_GUIDE}]+parts
    if png is not None:raise ValueError('Text request cannot have image')
    return parts


def design_for(packet,c,arm):
    return previous.design_for(packet,c,previous.P)


def visible_audit(public):
    previous.validate_pairs(public['payload'])
    visible=dumps({k:public[k] for k in ('system','texts','payload','readout')})
    if re.search(r'(?i)(INC-[A-F0-9]{8}|aiops202[25]|aegislab|ground_truth|injection_time|/home/|trace_id|span_id|anomal\s*":)',visible):
        raise ValueError('Private identity in public request')
    assert public['texts'][C]==public['texts'][A]==public['texts'][CR]
    assert public['texts'][V]==public['texts'][VR]
    for arm in REPEATS:assert public['canonical_arms'][arm]==arm
    for arm in QA:
        assert not any(p['text'].startswith('A fault has occurred') for p in public['texts'][arm])
    if not public['payload']['relations']:assert public['texts'][V]==public['texts'][C]
    return {'status':'passed','facts_retained':True,'qa_answer_provenance':'public_only'}
