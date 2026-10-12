"""Pure public compiler; never reads files, private labels or historical answers."""
from copy import deepcopy
import json
import re
from .utils import dumps,digest

F,ST,SV,T,V=('FULL_TEXT','SUMMARY_TEXT','SUMMARY_VISUAL','TEXT_FETCH','VISUAL_FETCH')
PUBLIC_FIELDS={'metric_series_64','estimated_fault_window','observation_window','trace_summary_entry',
               'explicit_missingness','trace_summary_meta','denum_log_template','denum_log_meta',
               'candidate_set','evidence_legends','sircl_star_analysis'}
DEFERRED_FIELDS={'values_codec','missing_codec','missing_mask','values'}
GUIDE=('Public telemetry index; all rows retain their stated entities, source units and public windows. '
       'M/R/L are measured metrics, recorded span statistics and logs. G records directed calls and deployment; '
       'neither graph position nor observation order proves causality. Reference/current labels are public observation phases. '
       'Inclusive durations include child spans; separate quantiles cannot be subtracted as local execution. '
       'Do not convert unverified native units. Repeated summaries are not independent votes. '
       'Unshown series samples remain available in the named complete detail bundles; absence is not zero or health. '
       'Columns define every row position exactly. Node IDs have four digits, pods five and services three. '
       'Exact sequence codecs use length and value_positions; a-b includes both endpoints, every bin occurs once, '
       'and null is an unobserved value. List-form sequences preserve their original bin order. ')
RCA_TASK=('Identify the component where the fault originated. Return exactly five distinct IDs from the exhaustive candidates, '
          'ranked by plausibility, as {"services":["..."],"reason":"...","confidence":"high|medium|low"}. '
          'Cite actual fact IDs and distinguish observations from causal hypotheses.')
SELECT_TASK=('Choose zero to eight distinct complete detail bundle IDs that would be useful for diagnosing this incident. '
             'List them in priority order, within the stated final-input budget. Output only {"bundle_ids":["..."]}. '
             'Do not output a root ranking, confidence or explanation.')
GRAPH_GUIDE=('The image carries the same typed relationship index: arrowheads point from source to target. '
             'calls and request_parent are distinct recorded relations; hosts and has_instance are deployment. '
             'has_instance is the display alias of owns. Placement and color do not indicate a root cause.')
TABLE_GUIDE=('Tables: columns name row fields; / separates nested object keys (~1 means /, ~0 means ~). '
             'fixed fields apply to every row. copy fields read the named column; index 0 means its first list item. '
             'Each row is a separate source record, even when values repeat. '
             'Window rows reference M/R/L fact IDs for entity and metric/operation label unless overridden; '
             'first/last/minimum/maximum are [original displayed value, zero-based bin]. '
             'Pair quantiles are [[parent p50,p95],[child p50,p95]]; binary order is neither, child only, '
             'parent only, both above reference p95. conditional_child rows are [parent_slow,n,child_p50,p95]. ')


def flat_record(row,prefix=''):
    out={}
    for key,value in row.items():
        path=prefix+str(key).replace('~','~0').replace('/','~1')
        if isinstance(value,dict) and value:out.update(flat_record(value,path+'/'))
        else:out[path]=deepcopy(value)
    return out


def packed_rows(rows):
    """Readable named columns, verified constants/copies; preserve record order."""
    groups=[]
    for row in rows:
        flat=flat_record(row)
        if not groups or tuple(groups[-1][0])!=tuple(flat):groups.append([])
        groups[-1].append(flat)
    result=[]
    for group in groups:
        first=group[0];fixed={};copies={}
        if len(group)>1:
            fixed={k:v for k,v in first.items() if all(dumps(r[k])==dumps(v) for r in group)}
            for target,source,index in [('service','entities',0),('entity_id','entities',0),('detail_bundle','fact_id',None)]:
                if target in first and source in first and target not in fixed:
                    if all((isinstance(r[source],list) and len(r[source])==1 and dumps(r[target])==dumps(r[source][0]))
                           if index==0 else dumps(r[target])==dumps(r[source]) for r in group):
                        copies[target]={'field':source,**({'index':index} if index is not None else {})}
        columns=[k for k in first if k not in fixed and k not in copies]
        result.append({**({'fixed':fixed} if fixed else {}),**({'copy':copies} if copies else {}),
                       'columns':columns,'rows':[[r[k] for k in columns] for r in group]})
    return result


def packed_extras(lines):
    """Parse only existing JSON records; preserve headings, qualifiers and order."""
    groups=[]
    for line in lines:
        prefix='';body=line
        if not line.startswith('{') and ': {' in line:prefix,body=line.split(': ',1)
        try:value=json.loads(body)
        except ValueError:value=None
        if isinstance(value,dict):
            if not groups or groups[-1].get('prefix')!=prefix or 'records' not in groups[-1]:
                groups.append({'prefix':prefix,'records':[]})
            groups[-1]['records'].append(value)
        else:groups.append({'text':line})
    return [{**g,'records':packed_rows(g['records'])} if 'records' in g else g for g in groups]


def packed_window(lines,records):
    lookup={r['fact_id']:r for r in records if 'fact_id' in r}
    if len(lines)%2:raise ValueError('Unpaired window summary')
    rows=[]
    for head,body in zip(lines[::2],lines[1::2],strict=True):
        fields=head.split(' | ')
        if len(fields)!=4:raise ValueError('Unknown window header')
        fact,entity,label,unit=fields;row={'fact_id':fact,'unit':unit}
        record=lookup.get(fact,{})
        if record.get('entities')!=[entity]:row['entity']=entity
        inherited=fact+' · '+str(record.get('metric',record.get('operation','')))
        if label!=inherited:row['label']=label
        match=re.fullmatch(r'first (.+) @bin(\d+) ; last (.+) @bin(\d+) ; minimum (.+) @bin(\d+) ; maximum (.+) @bin(\d+)',body)
        trace=re.fullmatch(r'exclusive p95: reference (.+) ; current (.+)',body)
        if match:
            for i,name in enumerate(('first','last','minimum','maximum')):
                # Keep both value and displayed bin strings intact; no numeric rounding.
                row[name]=list(match.groups()[2*i:2*i+2])
        elif trace:row['exclusive_p95_reference'],row['exclusive_p95_current']=trace.groups()
        else:row['original_summary']=body
        rows.append(row)
    return packed_rows(rows)


def packed_edges(edges):
    groups={}
    for source,target,kind in edges:
        groups.setdefault(kind,{}).setdefault(source,[]).append(target)
    return groups


def overview_wire(public):
    idx=public['index']
    return {'records':packed_rows(idx['records']),'aux_metrics':packed_rows(idx['aux_metrics']),
            'window_summary':packed_window(idx['window_summary'],idx['records']),
            'additional_public_summaries':packed_extras(idx['additional_public_summaries']),
            'components':packed_rows(idx['components']),'roles':deepcopy(idx['roles']),
            'pairs':packed_rows(idx['pairs']),'clock':deepcopy(idx['clock']),
            'edges':packed_edges(idx['edges'])}


def retrievable_ids(public):
    """Only advertise bundles containing observations deferred from the overview."""
    idx=public['index']
    ids={r['detail_bundle'] for r in idx['records'] if 'detail_bundle' in r}
    ids.update(r['id'] for r in idx['aux_metrics'])
    ids.update(r['id'] for r in idx['pairs'])
    ids.update(r['detail_bundle'] for r in idx['components'] if 'detail_bundle' in r)
    return ids


def assignment_record(line):
    """Consume complete JSON values, never regex-match assignments inside strings."""
    region,rest=line.split(' evidence;',1);out={'region':region};decoder=json.JSONDecoder()
    while rest.strip(' ;'):
        rest=rest.lstrip(' ;');m=re.match(r'([A-Za-z_][A-Za-z0-9_]*)=',rest)
        if not m:raise ValueError('Unparsed public record: '+rest[:100])
        key=m[1];rest=rest[m.end():]
        if key in out:raise ValueError('Duplicate record key')
        if key=='field' or (key=='bins' and not rest.startswith('[')):
            value,sep,rest=rest.partition(';')
            if not sep:raise ValueError('Unterminated canonical non-JSON field')
        else:
            value,n=decoder.raw_decode(rest);rest=rest[n:]
        out[key]=value
    if out.get('field') not in PUBLIC_FIELDS:raise ValueError('Unknown canonical field')
    return out


def table(rows):
    """Named column codec retains every value; heterogeneous rows group by schema."""
    groups={}
    for row in rows:
        keys=tuple(row)
        groups.setdefault(keys,[]).append([row[k] for k in keys])
    return [{'columns':list(k),'rows':v} for k,v in groups.items()]


def compile_public(source):
    from RQs.RQ3_8.src.exps import expand_records
    from RQs.RQ3_17.src.exps import topology_packet,graph_ledger
    original=deepcopy(source['texts'][F]);pairs=deepcopy(source['payload'])
    # Every original text part is preserved verbatim in the full public ledger.
    ledger={'schema':'EvidenceLedgerV1','system':source['system'],'candidates':deepcopy(source['candidates']),
            'full_text_parts':original,'pair_packet':pairs,'bundles':[]}
    records=[];extras=[];window=[];aux=[];components=[];bindings=[];counts={};extra_edges=set()
    def bundle(bid,kind,entities,text,ref):
        if any(b['id']==bid for b in ledger['bundles']):raise ValueError('Ambiguous detail ID '+bid)
        ledger['bundles'].append({'id':bid,'kind':kind,'entities':entities,'text':text,
                                 'content_sha256':digest(text),'source':ref})
    for pi,part in enumerate(original):
        text=part['text']
        if text.startswith('=== INCIDENT EVIDENCE'):
            for li,line in enumerate(text.splitlines()):
                if not re.match(r'^\w+ evidence;',line):continue
                raw=assignment_record(line);field=raw['field']
                if field=='candidate_set':
                    assert raw['entities']==source['candidates'];continue
                record={k:v for k,v in raw.items() if k not in DEFERRED_FIELDS}
                if field in {'metric_series_64','trace_summary_entry','denum_log_template'}:
                    kind={'metric_series_64':'metric','trace_summary_entry':'trace','denum_log_template':'log'}[field]
                    counts[kind]=counts.get(kind,0)+1
                    bid=raw.get('fact_id',f'LOG{counts[kind]:02d}')
                    record['fact_id']=bid
                    bundle(bid,kind,raw['entities'],line,{'part':pi,'line':li})
                    if field=='metric_series_64':record['detail_bundle']=bid
                records.append(record);bindings.append({'record':len(records)-1,'part':pi,'line':li})
        elif text.startswith('G:'):
            for line in text.splitlines():
                if line.startswith('directed_call_edge:'):
                    edge=json.loads(line.split(':',1)[1]);extra_edges.add((edge['caller'],edge['callee'],'calls'));continue
                if line.startswith('G:'):continue
                if line.startswith('{'):
                    item=json.loads(line)
                    if set(item)=={'from','to','relation'}:
                        assert item['relation'] in {'calls','hosts','owns','has_instance','request_parent'}
                        extra_edges.add((item['from'],item['to'],item['relation']));continue
                    if set(item)=={'child','parent','relation','supporting_span_pairs'}:
                        assert item['relation']=='observed parent span -> child span'
                        extra_edges.add((item['parent'][0],item['child'][0],'request_parent'))
                # Retain every non-edge original graph annotation and observed-ID list.
                extras.append(line)
        elif text.startswith('Additional observations'):
            extras.extend(text.splitlines())
        elif text.startswith('Additional component facts'):
            encoded=json.loads(text.split('\n',1)[1])
            # Preserve the exact original field codecs in retrieved records;
            # expanding a table here would silently change the promised raw form.
            cards=[dict(zip(encoded['columns'],r,strict=True)) for r in encoded['rows']]
            for card in cards:
                if card['kind']=='graph':continue
                compact=deepcopy(card)
                if card['kind']=='metric':
                    compact['data']={k:v for k,v in card['data'].items() if k not in {'values','bins'}}
                    compact['detail_bundle']='CARD_'+card['id']
                elif card['kind']=='log':
                    compact['data']={k:v for k,v in card['data'].items() if k not in {'counts','bins'}}
                    compact['detail_bundle']='CARD_'+card['id']
                components.append(compact)
                bundle('CARD_'+card['id'],card['kind'],[card['entity']] if card['entity'] else [],dumps(card),{'part':pi,'card':card['id']})
        elif text.startswith('Reference operands'):
            raw=json.loads(text.rsplit('\n',1)[1])
            assert raw['fields']==['id','entity','metric','unit','values_codec']
            for values in raw['series']:
                rec=dict(zip(raw['fields'],values,strict=True))
                bundle(rec['id'],'metric',[rec['entity']],dumps(rec),{'part':pi,'series':rec['id']})
                aux.append({k:v for k,v in rec.items() if k!='values_codec'})
            extras.append('AUX series use native unit labels, unverified unless explicitly defined, and the same 64 public time bins. Complete values are available by AUX ID.')
        elif re.match(r'^(MET|TRC)\d+ \|',text):
            window.extend(text.splitlines())
    if counts.get('metric')!=12:raise ValueError('All original twelve metric summaries required')
    pair_summary=[]
    for rel in pairs['relations']:
        r=deepcopy(rel)
        for p,phase in r['phases'].items():
            points=phase.pop('points')
            phase['sample_n']=len(points)
        # The public pair package uses sampled_pairs in some predecessor versions.
        for phase in r['phases'].values():phase.pop('sampled_pairs',None)
        pair_summary.append(r)
        bundle(rel['id'],'request_pair',[rel['parent'],rel['child']],dumps(rel),{'pair_packet':rel['id']})
    topology=topology_packet(original,pairs)
    edges=set((e['source'],e['target'],e['kind']) for g in topology['graph_cards'] for e in g['data']['edges'])|extra_edges
    _,roles=graph_ledger(original)
    graphs=[]
    for cid,title,is_call in [('CALLS','Observed calls and request parents',True),('DEPLOY','Observed deployment membership',False)]:
        group=sorted((e for e in edges if (e[2] in {'calls','request_parent'})==is_call),key=lambda e:(int(e[0]),int(e[1]),e[2]))
        if not group:continue
        nodes=sorted({x for e in group for x in e[:2]},key=int)
        graphs.append({'id':cid,'kind':'graph','title':title,'entity':None,'unit':'','data':{
          'nodes':[{'id':x,'type':{3:'service',4:'node',5:'pod',6:'external'}[len(x)],**({'role':roles[x]} if x in roles else {})} for x in nodes],
          'edges':[{'id':'e'+str(i+1),'source':a,'target':b,'kind':k} for i,(a,b,k) in enumerate(group)]}})
    topology['graph_cards']=graphs
    # Only display alias, reversible in the text and plot inventories.
    for graph in topology['graph_cards']:
        for edge in graph['data']['edges']:
            if edge['kind']=='owns':edge['kind']='has_instance'
    topology['relation_bindings']=[]
    index={'schema':'EvidenceIndexV1','records':records,'aux_metrics':aux,'components':components,
           'window_summary':window,'additional_public_summaries':extras,'pairs':pair_summary,
           'clock':pairs['clock'],'edges':sorted(set(edges)),
           'roles':roles,
           'bundles':[{'id':b['id'],'kind':b['kind'],'entities':b['entities']} for b in ledger['bundles']]}
    return {'system':source['system'],'candidates':deepcopy(source['candidates']),
            'ledger':ledger,'index':index,'topology':topology,'index_source_bindings':bindings,
            'source_facts_sha256':digest(original),'schema':'BudgetedAcquisitionPublicV1'}


def overview_parts(public,visual=False,task='select',costs=None,final_budget=None):
    idx=overview_wire(public)
    rows=[GUIDE+TABLE_GUIDE,'Public candidates (exhaustive, fixed order): '+dumps(public['candidates']),
          'Public phase clock: '+dumps(idx['clock']),
          'M/R/L metadata and recorded summaries: '+dumps(idx['records']),
          'Additional metric catalogue: '+dumps(idx['aux_metrics']),
          'Full-window summaries: '+dumps(idx['window_summary']),
          'Additional recorded summaries: '+dumps(idx['additional_public_summaries']),
          'Other component records: '+dumps(idx['components']),
          'Observed entity roles: '+dumps(idx['roles']),
          'Request-pair population and conditional summaries: '+dumps(idx['pairs'])]
    if visual:rows.append(GRAPH_GUIDE)
    else:rows.append('Observed directed relationships {type:{source:[targets]}}; all arrows source->target: '+dumps(idx['edges']))
    if task=='select':
        available=retrievable_ids(public)
        catalogue=[{**b,**({'input_tokens':costs[b['id']]} if costs else {})} for b in public['index']['bundles'] if b['id'] in available]
        rows.append('Complete detail bundle catalogue: '+dumps(table(catalogue)))
        rows.append('Final request input budget: '+str(final_budget if final_budget is not None else 40960)+'.')
        rows.append(SELECT_TASK)
    else:rows.append(RCA_TASK)
    return [{'type':'text','text':'\n'.join(rows)}]


def selection(response,public,max_bundles=8):
    try:
        value=json.loads(response)
        ids=value['bundle_ids'];allowed=retrievable_ids(public)
        if set(value)!={'bundle_ids'} or not isinstance(ids,list) or len(ids)>max_bundles:raise ValueError()
        if any(not isinstance(x,str) or x not in allowed for x in ids) or len(ids)!=len(set(ids)):raise ValueError()
        return {'schema':'FetchSelectionV1','valid':True,'bundle_ids':ids}
    except (ValueError,TypeError,KeyError):
        return {'schema':'FetchSelectionV1','valid':False,'bundle_ids':[]}


def final_parts(public,bundle_ids):
    parts=overview_parts(public,task='rca')
    available={b['id']:b for b in public['ledger']['bundles']}
    if len(bundle_ids)!=len(set(bundle_ids)) or any(x not in available for x in bundle_ids):raise ValueError('Unknown/duplicate detail')
    if bundle_ids:
        parts.insert(0,{'type':'text','text':'Requested complete source details (original readings):\n'+'\n'.join(available[x]['text'] for x in bundle_ids)})
    return parts


def budgeted_final(public,response,budget,count):
    """Count complete assembled requests; skip whole bundles, never slice arrays."""
    selected=selection(response,public);accepted=[];skipped=[];limit=min(budget,40960-8192)
    base=final_parts(public,[])
    if count(base)>limit:
        return {'parts':deepcopy(public['ledger']['full_text_parts']),'common_fallback_required':True,
                'accepted':[],'skipped':selected['bundle_ids'],'selection_valid':selected['valid']}
    for bid in selected['bundle_ids']:
        candidate=final_parts(public,accepted+[bid])
        if count(candidate)<=limit:accepted.append(bid)
        else:skipped.append(bid)
    parts=final_parts(public,accepted)
    return {'parts':parts,'input_tokens':count(parts),'accepted':accepted,'skipped':skipped,
            'common_fallback_required':False,'selection_valid':selected['valid']}


def design_for(public,c):
    """Existing registered node-arrow components; no experiment-local drawing."""
    from renderer.operations import apply_operations
    from renderer.utils import node_link_layout
    cards=deepcopy(public['topology']['graph_cards']);cfg=c['canvas']
    if not cards:return None
    heights=[max(300,node_link_layout(card,cfg['width']-2*cfg['padding'])['min_height']) for card in cards]
    tree={'id':'root','type':'column','weights':heights,'children':[
        {'id':'panel_'+g['id'],'type':'panel','card':g['id'],'component':'graph.node_link'} for g in cards]}
    h=86+cfg['padding']+sum(heights)+cfg['gap']*(len(cards)-1)
    if h<600:heights[-1]+=600-h;h=600
    base={'schema':'DashboardDesignV1','viewport':{'width':cfg['width'],'height':h},'theme':'dark',
          'font_size':cfg['font_size'],'gap':cfg['gap'],'padding':cfg['padding'],'scale':1,'tree':tree,
          'bindings':[],'relation_bindings':[],'indexing':{'visible':False,'start':1},'graph':{'show_isolates':True}}
    ops=[{'op':'component','args':{'card':g['id'],'component':'graph.node_link','node_layout':'layered_grid',
          **({'dashed_width_scale':3} if g['id']=='CALLS' else {})}} for g in cards]
    evidence={'schema':'CanvasEvidenceV1','cards':cards}
    design,audit=apply_operations(evidence,base,ops)
    return evidence,base,ops,design,audit


REPEATS=('TEXT_REPEAT','VISUAL_REPEAT')
QA_ARMS=('QA_NONE','QA_FOCUS','QA_CONTROL')
AID_ARMS=('FOCUS_FETCH','CONTROL_FETCH')
QA_SYSTEM='Read only the provided public telemetry. Answer the stated relationship questions exactly; do not diagnose a root cause.'


def selection_schema():
    return {'type':'json_schema','json_schema':{'name':'fetch_selection','strict':True,'schema':{
      'type':'object','properties':{'bundle_ids':{'type':'array','items':{'type':'string'},'maxItems':8}},
      'required':['bundle_ids'],'additionalProperties':False}}}


def qa_schema():
    edge={'type':'object','properties':{k:{'type':'string'} for k in ('source','target','type')},
          'required':['source','target','type'],'additionalProperties':False}
    return {'type':'json_schema','json_schema':{'name':'relation_reading','strict':True,'schema':{
      'type':'object','properties':{k:{'type':'array','items':edge} for k in ('q1','q2')},
      'required':['q1','q2'],'additionalProperties':False}}}


def request_envelope(public,stage,c):
    from RQs.RQ3_1.src.main import _request_envelope
    from RQs.RQ3_18.src.exps import schema_for,F as schema_arm
    value=_request_envelope('qwen3.8-27b',system=QA_SYSTEM if stage=='qa' else public['system'])
    value['schema']=selection_schema() if stage=='select' else qa_schema() if stage=='qa' else schema_for(schema_arm,value['schema'])
    value['effective_server']['max_tokens']=c['max_select_tokens'] if stage=='select' else c['qa_max_tokens'] if stage=='qa' else c['max_final_tokens']
    value['policy_version']=c['version']
    return value


def mechanism_packet(public,accepted):
    """Outcome-blind matching using only public entities and typed degrees."""
    from collections import Counter
    import math
    entities={e for b in public['ledger']['bundles'] if b['id'] in accepted for e in b['entities']}
    edges=[tuple(e) for e in public['index']['edges']]
    degree=Counter(e for a,b,_ in edges for e in (a,b))
    def kind(e):return 'service' if len(e)==3 else 'node' if len(e)==4 else 'pod' if len(e)==5 else 'external'
    def complexity(e):
        a,b,t=e
        return (t,kind(a),kind(b),int(math.log2(1+degree[a])),int(math.log2(1+degree[b])))
    focus=sorted((e for e in edges if set(e[:2])&entities),key=lambda e:digest(['rq320_focus_v1',e]))
    controls=sorted((e for e in edges if not set(e[:2])&entities),key=lambda e:digest(['rq320_control_v1',e]))
    selected=next(((a,b) for a in focus for b in controls if complexity(a)==complexity(b)),None)
    if selected is None:return {'applicable':False,'reason':'no_public_matched_relation_pair','selected_entities':sorted(entities)}
    a,b=selected
    questions=[];answers={}
    # Question order is independent of which edge gets the focus card.
    for i,e in enumerate(sorted(selected,key=lambda x:digest(['rq320_question_v1',x]))):
        pair=sorted(e[:2]);key='q'+str(i+1)
        questions.append(key+': List every recorded directed relationship between entities '+dumps(pair)+'. Return exact source, target and type; has_instance may be written as owns.')
        answers[key]=sorted([{'source':s,'target':t,'type':k} for s,t,k in edges if sorted([s,t])==pair],key=dumps)
    def card(e):return 'Correct public relation readout (observation only): '+dumps({'source':e[0],'target':e[1],'type':e[2]})
    return {'applicable':True,'schema':'RelationInterventionV1','selected_entities':sorted(entities),
      'focus_edge':list(a),'control_edge':list(b),'matching_signature':complexity(a),
      'focus_card':card(a),'control_card':card(b),'questions':questions,'answers':answers}


def qa_parts(public,png,packet,arm):
    # Identical visual overview; replace the RCA instruction with an independent QA task.
    parts=overview_parts(public,visual=True,task='rca')
    parts[0]['text']=parts[0]['text'].removesuffix(RCA_TASK)+'\n'.join(packet['questions'])+'\nOutput only JSON with keys q1 and q2, each a list of {source,target,type} records.'
    if arm!='QA_NONE':parts.append({'type':'text','text':packet['focus_card' if arm=='QA_FOCUS' else 'control_card']})
    return [{'type':'image','png':png}]+parts


def score_qa(packet,response):
    import jsonschema
    try:
        values=json.loads(response);jsonschema.validate(values,qa_schema()['json_schema']['schema'])
        for edges in values.values():
            for edge in edges:
                if edge['type']=='has_instance':edge['type']='owns'
        expected=deepcopy(packet['answers'])
        for edges in expected.values():
            for edge in edges:
                if edge['type']=='has_instance':edge['type']='owns'
        correct=[sorted(values[k],key=dumps)==sorted(v,key=dumps) for k,v in expected.items()]
        return {'status':'complete','metrics':{'qa_accuracy':sum(correct)/len(correct)},'per_question':correct}
    except (ValueError,TypeError,KeyError,jsonschema.ValidationError):
        return {'status':'model_failure','metrics':{'qa_accuracy':0.},'per_question':[False,False]}
