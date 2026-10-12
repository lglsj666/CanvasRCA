"""Pure complete-public-evidence compiler; no filesystem, labels or model calls."""
from collections import defaultdict
from copy import deepcopy
from decimal import Decimal, InvalidOperation
import json
import re
from .utils import ARMS, MODEL, VERSION, stable_hash
from RQs.RQ3_16.src import exps as anchor

A,RT,RV,PV,EV,CT,CV,TR,VR,QRT,QRV,QCT,QCV,ROT,ROV=ARMS
REPEATS={TR,VR}
QA={QRT,QRV,QCT,QCV}
VISUAL={A,RV,PV,EV,CV,VR,QRV,QCV,ROV}
BASES={TR:CT,VR:CV,QRT:RT,QRV:RV,QCT:CT,QCV:CV,ROT:CT,ROV:CV}
PUBLIC_FIELDS={'metric_series_64','estimated_fault_window','observation_window','trace_summary_entry',
 'explicit_missingness','trace_summary_meta','denum_log_template','denum_log_meta'}
CORE_KEYS={'region','fact_id','field','entities','bins','unit','baseline','metric','missing_codec','legacy_display_rank',
 'peak','rank','service','signed_z','sircl_met_z','values_codec','end','start','duration_rel_s','source_metric_rows',
 'count_base','count_fault','count_lfc','entry_index','exl_p95_base_us','exl_p95_fault_us','inl_p95_fault_us',
 'latency_lfc','operation','rank_score','traces_missing','omitted_services','service_count','count','entity_id',
 'full_numeric_series_available_via_search_logs','level','log_r','numeric_preview','omitted_numeric_variables',
 'relative_bin','template','template_full_sha256','template_id','truncated','binary_output','event_count',
 'schema_version','semantic_round_trip','template_count','omitted_templates','template_truncated','numeric_variables',
 'logs_missing','preview_truncated'}
PACK_GUIDE=('Record schemas define named columns and fixed fields shared by every row using that schema. '
 'A schema row is [schema_id,[column values in order]]. Each row is a separate original observation; repeated values do not merge observations. '
 'Nested keys use / separators (~1 means a literal /; ~0 means ~). Copy fields equal the named field, or its first list item when index=0. '
 'All original numeric spellings, source units, nulls and sequence positions are preserved. '
 '@candidate_ids means the complete ordered Candidate IDs list printed in this request. ')
ORGANIZATION_GUIDE=('Entity sections collect only records explicitly bound to that entity; within each section the order is M, R, L. '
 'Multi-entity relations, request pairs and global records remain in the shared section. Section position is not a root-cause rank.')
VISUAL_GUIDE=('Image decoding: this is the original same-request marginal sample display. Parent/Child and operation names bind each panel. '
 'Lavender is Reference and teal is Current. Positions use log1p(duration_ms), with millisecond tick labels and a common range within each panel. '
 'Dots are recorded samples, not the entire population. Exact samples, population statistics and all other facts remain in text. '
 'Panel position and color are not root-cause scores; these are distributions, not trajectories or causal propagation.')
QA_SYSTEM='Answer the supplied public telemetry reading questions. This is not root-cause diagnosis.'
QA_GUIDE=('Answer each non-null question independently using the supplied evidence. Return q1 through q6 with the requested fields; '
 'return null for questions explicitly marked not applicable. Preserve entity IDs and source units. For readings, value is a string containing '
 'the recorded number; do not convert units. For binding, targets contains all direct endpoints for the stated direction and relation. '
 'For comparisons return higher_phase as reference, current or equal. Give no root ranking or explanation.')
NEUTRAL_EDITS={
 'metric curves use their original time bins and independent linear native-unit axes.':
 'metric series use their original time bins and native units.',
 'Trace bars compare reference/current exclusive p95, not inclusive duration. Colors distinguish measurements, not root probability.':
 'Trace summaries compare reference/current exclusive p95, not inclusive duration.',
 'Joint and marginal graphs repeat these samples on the same log1p(ms) scale.':
 'The log1p(ms) presentation transform does not change these exact millisecond samples.'}

class Number(str):
    """JSON number lexeme, deliberately never converted through a float."""


def wire(value):
    if isinstance(value,Number):return str(value)
    if isinstance(value,dict):return '{'+','.join(json.dumps(k,ensure_ascii=False)+':'+wire(v) for k,v in value.items())+'}'
    if isinstance(value,list):return '['+','.join(wire(v) for v in value)+']'
    return json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False)


def duplicate_safe(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('Duplicate JSON key '+key)
        result[key]=value
    return result


def decoder():
    return json.JSONDecoder(parse_int=Number,parse_float=Number,object_pairs_hook=duplicate_safe,
        parse_constant=lambda s:(_ for _ in ()).throw(ValueError('Nonfinite JSON '+s)))


def lexload(text):return decoder().decode(text)


def assignment(line):
    region,rest=line.split(' evidence;',1);row={'region':region};d=decoder()
    while rest.strip(' ;'):
        rest=rest.lstrip(' ;');m=re.match(r'([A-Za-z_][A-Za-z0-9_]*)=',rest)
        if not m:raise ValueError('Unknown assignment syntax '+rest[:80])
        key=m[1];rest=rest[m.end():]
        if key in row:raise ValueError('Duplicate assignment '+key)
        if key=='field' or (key=='bins' and not rest.startswith('[')):
            value,sep,rest=rest.partition(';')
            if not sep:raise ValueError('Unterminated raw field')
        else:value,n=d.raw_decode(rest);rest=rest[n:]
        row[key]=value
    if row.get('field') not in PUBLIC_FIELDS or set(row)-CORE_KEYS:raise ValueError('Unknown canonical fields: '+str(set(row)-CORE_KEYS))
    return row


def flatten(row,prefix=''):
    result={}
    for key,value in row.items():
        name=prefix+key.replace('~','~0').replace('/','~1')
        if isinstance(value,dict) and value:result.update(flatten(value,name+'/'))
        else:result[name]=value
    return result


def unflatten(row):
    result={}
    for key,value in row.items():
        keys=[s.replace('~1','/').replace('~0','~') for s in key.split('/')];target=result
        for name in keys[:-1]:target=target.setdefault(name,{})
        target[keys[-1]]=value
    return result


def owner_region(value,kind):
    if kind=='assignment':
        region={'Metric':'M','Trace':'R','Log':'L'}[value['region']]
        ids=value.get('entities',[])
        return (ids[0] if len(ids)==1 else None),region
    if kind in {'component','aux'}:
        region='M' if kind=='aux' else {'metric':'M','trace':'R','log':'L'}.get(value.get('kind'),'G')
        return value.get('entity') if region in 'MRL' else None,region
    region=value.get('region')
    return (value.get('entity') if region in ('M','R','L') else None),region or 'G'


def atomize(parts):
    """All source bytes are partitioned; only recognized public record shapes move."""
    atoms=[];sections=[]
    def add(pi,start,end,raw,kind='literal',value=None,owner=None,region='G',prefix=''):
        if value is not None:owner,region=owner_region(value,kind)
        item={'id':'a'+str(len(atoms)),'part':pi,'start':start,'end':end,'raw':raw,'kind':kind,
              'owner':owner,'region':region,'prefix':prefix,'value_wire':wire(value) if value is not None else None}
        atoms.append(item);return item['id']
    for pi,part in enumerate(parts):
        text=part['text'];ids=[]
        if text.startswith(('A fault has occurred','Source reading:','Literal reading and evidence citations:','Exact compact sequences:','Service names, pod names','Full-window observations:','Output cardinality','Based on the above','Observed request pairs:','Continuous pair fields:')):
            ids.append(add(pi,0,len(text),text));sections.append({'part':pi,'atoms':ids});continue
        if text.startswith(('Additional component facts','Reference operands')):
            boundary=re.search(r'(?m)^\{',text)
            if boundary is None:raise ValueError('Source table missing JSON object')
            start=boundary.start();ids.append(add(pi,0,start,text[:start]));v=lexload(text[start:])
            keys=('columns','rows') if text.startswith('Additional') else ('fields','series')
            if set(v)!=set(keys):raise ValueError('Unknown component/aux record container')
            columns=v[keys[0]];rows=v[keys[1]];container=[]
            for row in rows:
                if len(row)!=len(columns):raise ValueError('Nonrectangular source table')
                record=dict(zip(columns,row,strict=True));kind='component' if keys[0]=='columns' else 'aux'
                if kind=='component':
                    if set(record)!={'data','entity','id','kind','title','unit'} or record['kind'] not in {'graph','events'}:raise ValueError('Unknown component fields')
                    allowed={'edges','roles'} if record['kind']=='graph' else {'events'}
                    if set(record['data'])-allowed:raise ValueError('Unknown component data fields')
                if kind=='aux' and set(record)!={'id','entity','metric','unit','values_codec'}:raise ValueError('Unknown AUX fields')
                # A row is rendered in its original column schema in raw entity mode.
                atom_id=add(pi,start,len(text),wire({keys[0]:columns,keys[1]:[row]}),kind,record)
                atoms[-1]['container_keys']=list(keys);atoms[-1]['columns']=columns;container.append(atom_id)
            sections.append({'part':pi,'atoms':ids+container,'table_container':{'columns':columns,'keys':list(keys),'raw':text[start:]}})
            continue
        lines=text.splitlines(keepends=True);offset=0;i=0
        while i<len(lines):
            line=lines[i];body=line.rstrip('\n');kind='literal';value=None;owner=None;region='G';prefix='';raw=line
            if re.match(r'^\w+ evidence;',body) and text.startswith('=== INCIDENT EVIDENCE'):
                kind='assignment';value=assignment(body)
            elif re.match(r'^(MET|TRC)\d+ \|',body):
                if i+1>=len(lines):raise ValueError('Window record without body')
                fields=body.split(' | ')
                if len(fields)!=4:raise ValueError('Window heading changed')
                owner=fields[1];region='M' if fields[0].startswith('MET') else 'R';kind='window';raw+=lines[i+1];i+=1
            elif body.startswith('{') or re.match(r'^[a-z_]+: \{',body):
                prefix,tail=(body.split(': ',1) if not body.startswith('{') else ('',body))
                value=lexload(tail);kind='json'
                if not isinstance(value,dict):raise ValueError('Expected object record')
                allowed=({'entity','region','semantic','unit','values'},{'entity','region','semantic','unit'},{'from','to','relation'},
                         {'child','parent','relation','supporting_span_pairs'})
                if prefix:
                    if prefix not in {'propagation_service','directed_call_edge'}:raise ValueError('Unknown JSON prefix '+prefix)
                    expected={'evidence_source_display','onset_rel_min_display','rank','service','severity_z_display'} if prefix=='propagation_service' else {'caller','callee'}
                    if set(value)!=expected:raise ValueError('Unknown graph record shape '+str(set(value)))
                elif set(value) not in allowed:raise ValueError('Unknown additional record fields '+str(set(value)))
                if 'region' in value and value['region'] not in {'M','R','L'}:raise ValueError('Unknown modality')
            ids.append(add(pi,offset,offset+len(raw),raw,kind,value,owner,region,prefix));offset+=len(raw);i+=1
        if offset!=len(text):raise ValueError('Unpartitioned source bytes')
        sections.append({'part':pi,'atoms':ids})
    return atoms,sections


def schemas_for(atoms):
    groups=defaultdict(list)
    for atom in atoms:
        if atom['value_wire'] is None:continue
        flat=flatten(lexload(atom['value_wire']));groups[(atom['kind'],atom['prefix'],tuple(flat))].append((atom,flat))
    schemas={};rows={}
    for (kind,prefix,keys),items in groups.items():
        sid='S'+str(len(schemas)+1);first=items[0][1]
        fixed={k:v for k,v in first.items() if len(items)>1 and all(wire(row[k])==wire(v) for _,row in items)}
        copies={}
        for target,source in (('service','entities'),('entity_id','entities')):
            if target in first and source in first and target not in fixed and all(isinstance(r[source],list) and len(r[source])==1 and wire(r[target])==wire(r[source][0]) for _,r in items):copies[target]={'field':source,'index':0}
        columns=[k for k in keys if k not in fixed and k not in copies]
        spec={'record_kind':kind,'source_prefix':prefix,'columns':columns,'fixed':fixed,'copy':copies}
        schemas[sid]=wire(spec)
        for atom,row in items:rows[atom['id']]=wire([sid,[row[k] for k in columns]])
    return schemas,rows


def expand_schema_row(text,schemas):
    sid,values=lexload(text);s=lexload(schemas[sid])
    if len(values)!=len(s['columns']):raise ValueError('Nonrectangular packed row')
    flat=dict(s['fixed']);flat.update(zip(s['columns'],values,strict=True))
    for target,rule in s['copy'].items():flat[target]=flat[rule['field']][int(rule['index'])]
    return unflatten(flat)


def neutral(text):
    for old,new in NEUTRAL_EDITS.items():text=text.replace(old,new)
    return text


def encode_parts(original,atoms,sections,schemas,rows,packed=False,entity=False,rotate=False,candidates=()):
    lookup={a['id']:a for a in atoms};bindings=[]
    candidate_literal=json.dumps(list(candidates),ensure_ascii=False,separators=(',',':'))
    def render(atom):
        text=rows[atom['id']]+'\n' if packed and atom['id'] in rows else atom['raw']
        if packed and original[atom['part']]['text'].startswith('Service names, pod names') and 'Common evidence; field=candidate_set;' in text:
            # The first occurrence declares the complete ordered list. Only
            # subsequent exact copies can refer to that declaration.
            before,separator,after=text.partition(candidate_literal)
            if not separator:raise ValueError('Candidate declaration missing')
            text=before+separator+after.replace(candidate_literal,'@candidate_ids')
        return neutral(text)
    parts=[]
    if packed:parts.append({'type':'text','text':PACK_GUIDE+'\nRecord schema definitions: {'+','.join(wire(k)+':'+v for k,v in schemas.items())+'}'})
    def emit(items,heading=''):
        # Separators never concatenate a moved last source line with the next record.
        pieces=[render(a) for a in items];text=heading+'\n'.join(p.rstrip('\n') for p in pieces)
        parts.append({'type':'text','text':text});bindings.extend({'atom':a['id'],'part':len(parts)-1,'encoded':pieces[i].rstrip('\n')} for i,a in enumerate(items))
    if not entity:
        for section in sections:
            items=[lookup[x] for x in section['atoms']]
            if not packed or not section.get('table_container'):
                if not packed:
                    text=neutral(original[section['part']]['text']);parts.append({'type':'text','text':text})
                    # Raw source tables retain all rows together.
                    bindings.extend({'atom':a['id'],'part':len(parts)-1,'source_table':bool(section.get('table_container'))} for a in items)
                else:emit(items)
            else:emit(items)
    else:
        parts.append({'type':'text','text':ORGANIZATION_GUIDE})
        front=[];shared=[];tail=[];owned=defaultdict(list)
        for a in atoms:
            t=original[a['part']]['text']
            if t.startswith(('A fault has occurred','Source reading:','Literal reading and evidence citations:','Exact compact sequences:','Service names, pod names')):front.append(a)
            elif t.startswith(('Output cardinality','Based on the above')):tail.append(a)
            elif a['owner'] is not None and a['region'] in {'M','R','L'}:owned[a['owner']].append(a)
            else:shared.append(a)
        order=[x for x in candidates if x in owned]+sorted(set(owned)-set(candidates),key=lambda x:(len(x),x))
        if rotate and order:mid=len(order)//2;order=order[mid:]+order[:mid]
        emit(front);emit(shared,'Shared public records\n')
        for owner in order:
            items=sorted(owned[owner],key=lambda a:('MRL'.index(a['region']),a['part'],a['start'],int(a['id'][1:])))
            emit(items,'Entity '+owner+'\n')
        emit(tail)
    return parts,bindings


def qa_packet(atoms,candidates):
    records=[(a,lexload(a['value_wire'])) for a in atoms if a['kind']=='assignment']
    order=lambda x:stable_hash(['rq321_qa_v1',wire(x)])
    readings=[];comparisons=[];edges=set()
    for a,v in records:
        if len(v.get('entities',[]))!=1 or not v.get('fact_id'):continue
        owner=v['entities'][0];fid=v['fact_id'];field=v['field']
        key='baseline' if field=='metric_series_64' else 'exl_p95_fault_us' if field=='trace_summary_entry' else None
        if key and v.get(key) is not None:
            try:Decimal(str(v[key]))
            except InvalidOperation:continue
            unit=v['unit'] if field=='metric_series_64' else 'microseconds'
            readings.append({'fact':fid,'field':key,'entity':owner,'unit':unit,'value':str(v[key]),'atom':a['id']})
        pair=v.get('sircl_met_z',{}) if field=='metric_series_64' else v
        k1,k2=('regular_mean','current_mean') if field=='metric_series_64' else ('exl_p95_base_us','exl_p95_fault_us')
        try:left,right=(Decimal(str(pair[k])) for k in (k1,k2))
        except (KeyError,InvalidOperation):continue
        if not left.is_finite() or not right.is_finite():continue
        comparisons.append({'fact':fid,'keys':[k1,k2],'entity':owner,'unit':v['unit'] if field=='metric_series_64' else 'microseconds',
            'higher_phase':'reference' if left>right else 'current' if right>left else 'equal','atom':a['id']})
    for a in atoms:
        if a['value_wire'] is None:continue
        v=lexload(a['value_wire'])
        if set(v)=={'from','to','relation'}:edges.add((v['from'],v['to'],v['relation']))
        if a['kind']=='component' and v['kind']=='graph':
            edges.update(tuple(x) for x in v['data'].get('edges',[]) if len(x)==3)
    bindings=[]
    for a,v in records:
        if not v.get('fact_id') or len(v.get('entities',[]))!=1:continue
        entity=v['entities'][0]
        for kind in ('hosts','owns','has_instance'):
            for direction in ('incoming','outgoing'):
                targets=sorted({s if direction=='incoming' else t for s,t,k in edges if k==kind and (t if direction=='incoming' else s)==entity})
                if targets:bindings.append({'fact':v['fact_id'],'entity':entity,'relation':kind,'direction':direction,'targets':targets,'atom':a['id']})
    selected=[sorted(pool,key=order)[:2] for pool in (readings,bindings,comparisons)];questions={};answers={};provenance={};families={}
    for gi,(family,items) in enumerate(zip(('reading','binding','comparison'),selected,strict=True)):
        for j in range(2):
            q='q'+str(2*gi+j+1);families[q]=family
            if j>=len(items):questions[q]='not applicable';answers[q]=None;continue
            item=items[j];provenance[q]=item
            if family=='reading':
                questions[q]=f"For {item['fact']}, report its entity, source unit and recorded {item['field']} value as a string."
                answers[q]={k:item[k] for k in ('entity','unit','value')}
            elif family=='binding':
                questions[q]=f"Find the entity bound to {item['fact']}. Using only explicit {item['relation']} edges, report all its {item['direction']} direct endpoints in targets, and that entity and relation."
                answers[q]={k:item[k] for k in ('entity','relation','targets')}
            else:
                questions[q]=f"For {item['fact']}, compare {item['keys'][0]} (reference) with {item['keys'][1]} (current). Report entity, source unit, and higher_phase (reference/current/equal); do not convert units."
                answers[q]={k:item[k] for k in ('entity','unit','higher_phase')}
    return {'questions':questions,'answers':answers,'families':families,'provenance':provenance,
            'applicable':sum(v is not None for v in answers.values())}


def qa_schema():
    fields=[{'entity':{'type':'string'},'unit':{'type':'string'},'value':{'type':'string'}},
            {'entity':{'type':'string'},'relation':{'type':'string'},'targets':{'type':'array','items':{'type':'string'}}},
            {'entity':{'type':'string'},'unit':{'type':'string'},'higher_phase':{'type':'string','enum':['reference','current','equal']}}]
    props={f'q{i+1}':{'anyOf':[{'type':'null'},{'type':'object','properties':fields[i//2],'required':list(fields[i//2]),'additionalProperties':False}]} for i in range(6)}
    return {'type':'json_schema','json_schema':{'name':'rq321_telemetry_qa','strict':True,'schema':{'type':'object','properties':props,'required':list(props),'additionalProperties':False}}}


def score_qa(packet,response):
    import jsonschema
    try:answer=json.loads(response);jsonschema.validate(answer,qa_schema()['json_schema']['schema']);valid=True
    except (ValueError,TypeError,jsonschema.ValidationError):answer={};valid=False
    correct={};by=defaultdict(list)
    for q,expected in packet['answers'].items():
        if expected is None:continue
        value=deepcopy(answer.get(q));ok=False
        if value is not None:
            if packet['families'][q]=='reading':
                try:ok=Decimal(value['value'])==Decimal(expected['value']) and value['entity']==expected['entity'] and value['unit']==expected['unit']
                except (InvalidOperation,KeyError):ok=False
            elif packet['families'][q]=='binding':
                value['targets']=sorted(value['targets']);ok=value==expected and len(value['targets'])==len(set(value['targets']))
            else:ok=value==expected
        correct[q]=bool(ok);by[packet['families'][q]].append(bool(ok))
    metrics={'qa_accuracy':sum(correct.values())/len(correct) if correct else None,
       **{family:sum(by[family])/len(by[family]) if by[family] else None for family in ('reading','binding','comparison')}}
    return {'status':'complete' if valid else 'model_failure','metrics':metrics,'per_question':correct,'applicable_questions':len(correct)}


def compile_public(inherited,c):
    anchor.visible_audit(inherited)
    original=deepcopy(inherited['texts']['MARGINAL_FIVE']);atoms,sections=atomize(original);schemas,rows=schemas_for(atoms)
    texts={A:deepcopy(original)};bindings={};orders={}
    for arm,packed,entity in ((RT,False,False),(PV,True,False),(EV,False,True),(CT,True,True)):
        parts,mapping=encode_parts(original,atoms,sections,schemas,rows,packed,entity,candidates=inherited['candidates'])
        texts[arm]=parts;bindings[arm]=mapping
        if arm in (RT,CT):
            visual={RT:RV,CT:CV}[arm];texts[visual]=deepcopy(parts);bindings[visual]=mapping
    rotated,mapping=encode_parts(original,atoms,sections,schemas,rows,True,True,True,inherited['candidates'])
    texts[ROT]=rotated;texts[ROV]=deepcopy(rotated);bindings[ROT]=bindings[ROV]=mapping
    texts[TR]=deepcopy(texts[CT]);texts[VR]=deepcopy(texts[CV])
    qa=qa_packet(atoms,inherited['candidates'])
    for arm in QA:
        basis=BASES[arm];parts=deepcopy(texts[basis])
        # In entity mode each prefix/tail is a single part; remove only registered RCA instructions within it.
        kept=[]
        for part in parts:
            text=part['text']
            for old in original:
                if old['text'].startswith(('A fault has occurred','Source reading:','Literal reading and evidence citations:','Output cardinality','Based on the above')):
                    text=text.replace(neutral(old['text']),'')
            if text.strip():kept.append({'type':'text','text':text})
        texts[arm]=[{'type':'text','text':QA_GUIDE}]+kept+[{'type':'text','text':'Reading questions: '+json.dumps(qa['questions'],ensure_ascii=False)}]
    public={k:deepcopy(inherited[k]) for k in ('system','candidates','payload','facts_hash','base_facts_hash')}
    public.update(texts=texts,images={},infeasible={},canonical_arms={a:a for a in ARMS},qa=qa,
        organization={'schema':'FullEvidenceOrganizationPacketV1','atoms':atoms,'sections':sections,'record_schemas':schemas,
            'encoded_rows':rows,'bindings':bindings,'source_parts_sha256':stable_hash(original),'neutral_edits':NEUTRAL_EDITS},
        output_adapter=c['output_adapter']['version'])
    # Cache only exact same request within this experiment; repeats always independent.
    seen={}
    for arm in ARMS:
        key=stable_hash([texts[arm],arm in VISUAL and bool(public['payload']['relations']),system_for(public,arm),arm in QA,arm==A])
        if arm not in REPEATS:
            public['canonical_arms'][arm]=seen.get(key,arm);seen.setdefault(key,arm)
    visible_audit(public);return public


def system_for(public,arm):return QA_SYSTEM if arm in QA else public['system']


def request_envelope(arm,system):
    value=anchor.request_envelope('MARGINAL_FIVE',system)
    if arm in QA:value['schema']=qa_schema();value['effective_server']['max_tokens']=1024
    value['policy_version']=VERSION
    return value


def parts_for(public,arm,png=None):
    parts=deepcopy(public['texts'][arm])
    if arm in VISUAL and public['payload']['relations']:
        if not isinstance(png,bytes) or not png.startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('Actual unified PNG required')
        return [{'type':'image','png':png}]+([] if arm==A else [{'type':'text','text':VISUAL_GUIDE}])+parts
    if png is not None:raise ValueError('Text input cannot carry image')
    return parts


def design_for(payload,c,arm):return anchor.design_for(payload,c,'MARGINAL_FIVE')


def visible_audit(public):
    text=json.dumps({k:public[k] for k in ('system','texts','payload')},ensure_ascii=False)
    if re.search(r'(?i)(INC-[A-F0-9]{8}|aiops202[25]|aegislab|ground_truth|injection_time|/home/|/scratch/|trace_id|span_id|"anomal"\s*:)',text):raise ValueError('Private identity in visible input')
    for t,v in ((RT,RV),(CT,CV),(ROT,ROV)):assert public['texts'][t]==public['texts'][v]
    assert public['texts'][TR]==public['texts'][CT] and public['texts'][VR]==public['texts'][CV]
    for arm in QA:
        assert 'A fault has occurred' not in ''.join(p['text'] for p in public['texts'][arm])
    return {'status':'passed','public_schema':'FullEvidenceOrganizationPacketV1'}
