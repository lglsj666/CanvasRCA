"""Pure CPU full-source compiler. Diagnostic evidence only enters unified PNGs."""
from collections import Counter
from pathlib import Path
import json
import math
import re
from .utils import decode_sequence, leaves, stable_hash, read_json

ROOT = Path(__file__).resolve().parents[3]
RQ = ROOT/'RQs/RQ4_1'
SOURCE = ROOT/'RQs/RQ3_21/preparation/compact_entity_v1/public'
REGISTRATION = ROOT/'RQs/RQ3_16/results/marginal_coverage_v1/registration.json'
SYSTEM = 'You are an expert Site Reliability Engineer performing Root Cause Analysis for a microservice application on Kubernetes.'
VISUAL_TASK = '''Diagnose the initiating component using the complete telemetry dashboard. All incident observations and the exhaustive candidate IDs are in the image. Use only its candidate inventory and return exactly five distinct IDs ranked by plausibility; alternatives do not imply simultaneous causes.
Read metrics, traces, logs and observed relationships together. Bind each observation to its original entity, signal/operation, unit and reference/current interval. Native-unit axes are independent unless marked shared. Inclusive span durations include children; only explicitly exclusive latency estimates local time. Do not subtract independent quantiles. A calls B is a directed observation, not proof of causal origin. Co-location, observed onset order and correlated signals alone do not prove a cause. Missing source samples are not zeros; connecting plotted observations creates no additional measurement.
Check the leading candidate against two available observations, including one possible contradiction or alternative origin, within this single call. Return only JSON: {"services":["id1","id2","id3","id4","id5"],"reason":"at most three sentences with evidence references and the checks","confidence":"high|medium|low"}. Do not output intermediate rankings or hidden reasoning.'''
ID_COPY_GUIDE = '''Identifier transcription rule: The services array contains bare candidate IDs exactly as printed in the card titled "Candidate IDs · exhaustive fixed order". The JSON key services also permits node and pod candidates. Copy each whole ID character for character, including every digit; do not add an entity-type prefix. Card numbers, row indices, axis ticks, measurements and operation-name fragments are not candidate IDs. Before returning JSON, verify that each chosen string occurs in the candidate inventory and that all five strings differ.'''
ID_SYNTAX_GUIDE = 'Public identity encoding: service IDs have three digits, node IDs four digits and pod IDs five digits, with no leading zero. The services array accepts these three entity types. Copy IDs only from the candidate inventory; a correctly formatted number is not necessarily a candidate.'
STATIC_PREFIXES = ('A fault has occurred', 'Source reading:', 'Literal reading and evidence citations:',
    'Exact compact sequences:', 'G: calls ', 'Selected-observation bindings', '=== ',
    'Linked request observations:', 'Additional observations use ', 'Availability and recorded activity:', 'Host and instance observations:',
    'Additional component facts ', 'Full-window observations:', 'Output cardinality ', 'Based on the above',
    'Reference operands AUX')
FIELDS = {'metric_series_64', 'estimated_fault_window', 'observation_window', 'trace_summary_entry',
          'explicit_missingness', 'trace_summary_meta', 'denum_log_template', 'denum_log_meta'}
ASSIGN_KEYS = set('region fact_id field entities bins unit baseline metric missing_codec legacy_display_rank peak rank service signed_z sircl_met_z values_codec end start duration_rel_s source_metric_rows count_base count_fault count_lfc entry_index exl_p95_base_us exl_p95_fault_us inl_p95_fault_us latency_lfc operation rank_score traces_missing logs_missing omitted_services service_count count entity_id full_numeric_series_available_via_search_logs level log_r numeric_preview omitted_numeric_variables relative_bin template template_full_sha256 template_id template_truncated binary_output event_count schema_version semantic_round_trip template_count'.split())


def numeric(v):
    if v is None:
        return None
    if isinstance(v, bool):
        raise ValueError('Boolean is not a numeric observation')
    m = re.fullmatch(r'\s*([-+\d.eE]+)([kMGT]?)\s*', str(v))
    if not m:
        raise ValueError('Unrecognized public reading '+repr(v))
    out = float(m[1])*{'':1,'k':1e3,'M':1e6,'G':1e9,'T':1e12}[m[2]]
    if not math.isfinite(out):
        raise ValueError('Nonfinite observation')
    return out


def literal_records(atom, public):
    raw=atom['raw']
    if not raw.strip() or raw.startswith(STATIC_PREFIXES):
        return [], 'static_reading_instruction'
    if raw.startswith('Observed entity IDs:'):
        ids=[s.strip() for s in raw.partition(':')[2].strip().split(',') if s.strip()]
        return [{'kind':'identities','identities':ids,'name':'Observed entities'}], None
    if raw.startswith('Service names, pod names'):
        match=re.search(r'Candidate IDs \(exhaustive, fixed order\): (\[.*\])',raw)
        if not match or json.loads(match[1])!=public['candidates']:
            raise ValueError('Candidate inventory mismatch')
        return [{'kind':'identities','identities':public['candidates'],'name':'Candidate IDs · exhaustive fixed order'}],None
    if raw.startswith(('Observed request pairs:', 'Continuous pair fields:')):
        boundary=raw.find('\n[[')
        if boundary<0:
            raise ValueError('Pair source table not found')
        rows=json.loads(raw[boundary+1:])
        p=public['payload']['relations']
        if raw.startswith('Observed request pairs:'):
            expected=[[r['id'],r['parent'],r['parent_operation'],r['child'],r['child_operation'],r['thresholds'],
                [[phase,r['phases'][phase]['n'],r['phases'][phase]['binary']] for phase in ('reference','current')]] for r in p]
            kind='pair_binary'
        else:
            expected=[[r['id'],[[phase,r['phases'][phase]['quantiles'],r['phases'][phase]['conditional_child'],
                       r['phases'][phase]['points']] for phase in ('reference','current')]] for r in p]
            kind='pair_continuous'
        if rows!=expected:
            raise ValueError('Pair payload differs from frozen source')
        return [{'kind':kind,'rows':rows}],None
    raise ValueError('Unrecognized literal source; refusing silent omission: '+raw[:120])


def ledger(public):
    required={'base_facts_hash','candidates','canonical_arms','facts_hash','images','infeasible','organization',
              'output_adapter','payload','qa','system','texts'}
    if set(public)!=required or public['organization']['schema']!='FullEvidenceOrganizationPacketV1':
        raise ValueError('Unregistered source packet')
    result=[]; instructions=[]
    for atom in public['organization']['atoms']:
        if atom['kind']=='literal':
            records, disposition=literal_records(atom,public)
            if disposition:instructions.append({'source':atom['id'],'sha256':stable_hash(atom['raw']),'disposition':disposition})
            for v in records:result.append({'source':atom['id'],'kind':v.pop('kind'),'value':v})
        elif atom['kind']=='window':
            head,body=atom['raw'].split('\n',1)
            identity,entity,name,unit=head.split(' | ')
            result.append({'source':atom['id'],'kind':'window','value':{'id':identity,'entity':entity,'name':name,'unit':unit,'summary':body.strip()}})
        else:
            v=json.loads(atom['value_wire'])
            if atom['kind']=='assignment' and (set(v)-ASSIGN_KEYS or v['field'] not in FIELDS):
                raise ValueError('Unknown source field')
            if atom['kind'] not in {'assignment','json','component','aux'}:
                raise ValueError('Unknown record kind')
            result.append({'source':atom['id'],'kind':atom['kind'],'prefix':atom['prefix'],'value':v})
    return {'schema':'FullVisualSourceLedgerV1','records':result,'instructions':instructions,
            'source_hash':stable_hash(public['organization']),'candidates':public['candidates']}


def compile_case(public):
    """All source occurrences bind to a graphic or a caption on that graphic.

    Nulls/missingness are retained in source/audit, without visual warnings.
    The source ledger is NEVER included in the visual model's textual message.
    """
    packet=ledger(public); cards=[]; components={}; mapping=[]; serial=Counter(); globals_=[]
    def add(kind,title,entity=None,unit='',data=None):
        serial[kind]+=1;cid={'trace_joint':'JNT','inventory':'INV','comparison':'CMP'}.get(kind,kind[:3].upper())+str(serial[kind]).zfill(3)
        card={'id':cid,'kind':kind,'title':title,'entity':entity,'unit':unit,'data':data or {}}
        cards.append(card)
        components[cid]={'metric':'metric.line','trace':'trace.paired_bars','log':'log.timeline',
            'graph':'graph.node_link','events':'events.onset','trace_joint':'trace_joint.marginals',
            'inventory':'inventory.identities','comparison':'comparison.paired'}[kind]
        return card
    def bind(source,path,binding,disposition='visible',value=None):
        mapping.append({'source':source,'path':path,'binding':binding,'disposition':disposition,'value_hash':stable_hash(value)})
    def caption(card,source,path,value):
        if value is None:
            bind(source,path,None,'source_null_not_marked',value);return
        rows=card['data'].setdefault('details',[])
        displayed=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,separators=(',',':'))
        rows.append({'name':detail_label(path,value,card,public),'value':displayed})
        bind(source,path,f"{card['id']}.detail.{len(rows)-1}",value=value)
    def captions(card,source,value,skip=()):
        for path,v in leaves(value):
            if any(path==p or path.startswith(p+'/') for p in skip):continue
            key=path.split('/')[1]
            if key in {'region','field','fact_id','id','kind'}:
                bind(source,path,card['id']+'.title','typed_component_identity',v)
            elif key in {'entities','service','entity','entity_id'} and card['entity'] is not None:
                bind(source,path,card['id']+'.entity',value=v)
            elif key in {'metric','operation','semantic','name'}:
                bind(source,path,card['id']+'.title','signal_or_operation_title',v)
            elif key=='unit' and card['unit']:
                bind(source,path,card['id']+'.unit','unit_semantics',v)
            elif key=='bins' and card['kind'] in {'metric','log'}:
                bind(source,path,card['id']+'.time','original_time_coordinates',v)
            elif key in {'template_full_sha256','template_truncated','full_numeric_series_available_via_search_logs'}:
                bind(source,path,None,'source_provenance_audit_only',v)
            else:caption(card,source,path,v)
    def graph(source,edges,title,roles=None):
        ns=list(dict.fromkeys(x for e in edges for x in e[:2]))
        g=add('graph',title,data={'nodes':[{'id':n,'type':{3:'service',4:'node',5:'pod',6:'external'}[len(n)],
            **({'role':dict(roles or []).get(n)} if dict(roles or []).get(n) else {})} for n in ns],
            'edges':[{'id':'e'+str(i),'source':e[0],'target':e[1],'kind':e[2]} for i,e in enumerate(edges)]})
        for i,e in enumerate(edges):
            for j,v in enumerate(e):bind(source,f'/data/edges/{i}/{j}',f"{g['id']}.edge.e{i}",value=v)
        return g
    window_records=[]; pair_sources={}; selected_edges=[]; extra_edges=[]
    for record in packet['records']:
        source,kind,v=record['source'],record['kind'],record['value']
        if kind=='window':window_records.append(record);continue
        if kind.startswith('pair_'):pair_sources[kind]=source;continue
        if kind=='identities':
            card=add('inventory',v['name'],data={'identities':v['identities'],'details':[]})
            for i,e in enumerate(v['identities']):bind(source,f'/identities/{i}',f"{card['id']}.identity.{i}",value=e)
            bind(source,'/name',card['id']+'.title',value=v['name']);continue
        if kind=='assignment':
            f=v['field']
            if f=='metric_series_64':
                values=decode_sequence(v['values_codec']);miss=decode_sequence(v['missing_codec'])
                if len(values)!=64 or miss!=[q is None for q in values]:raise ValueError('Missingness differs from sequence')
                card=add('metric',v['fact_id']+' · '+v['metric'],v['service'],v['unit'],
                    {'bins':list(range(64)),'values':[numeric(q) for q in values],'details':[]})
                for key in ('values_codec','missing_codec'):
                    for path,val in leaves(v[key],'/'+key):
                        bind(source,path,card['id']+'.time' if key=='values_codec' else None,
                             'sequence_at_original_bins' if key=='values_codec' else 'missingness_audit_only',val)
                captions(card,source,v,('/values_codec','/missing_codec'))
            elif f=='trace_summary_entry':
                # These frozen keys have already been canonicalized to microseconds.
                card=add('trace',v['fact_id']+' · '+v['operation'],v['service'],'µs',
                    {'before':numeric(v['exl_p95_base_us']),'after':numeric(v['exl_p95_fault_us']),'details':[]})
                captions(card,source,v)
            elif f=='denum_log_template':
                card=add('log',v['template_id']+' · '+v['level'],v['entity_id'],'count',
                    {'bins':[v['relative_bin']],'counts':[v['count']],'template':v['template'],'details':[]})
                bind(source,'/template',card['id']+'.template',value=v['template']);captions(card,source,v,('/template',))
            elif f=='explicit_missingness':
                for path,val in leaves(v):bind(source,path,None,'availability_audit_only_no_warning',val)
            else:globals_.append(record)
        elif kind=='aux':
            if set(v)!={'id','entity','metric','unit','values_codec'}:raise ValueError('Unknown auxiliary series')
            values=decode_sequence(v['values_codec'])
            card=add('metric',v['id']+' · '+v['metric'],v['entity'],v['unit'],
                {'bins':list(range(len(values))),'values':[numeric(q) for q in values],'details':[]})
            captions(card,source,v,('/values_codec',))
            for path,val in leaves(v['values_codec'],'/values_codec'):
                bind(source,path,card['id']+'.time','sequence_at_original_bins',val)
        elif kind=='component':
            if set(v)!={'id','entity','kind','title','unit','data'}:raise ValueError('Unknown component record')
            if v['kind']=='graph':
                if set(v['data'])-{'edges','roles'}:raise ValueError('Unknown graph fields')
                if not v['data']['edges']:
                    for path,val in leaves(v):bind(source,path,None,'empty_relation_no_panel',val)
                    continue
                g=graph(source,v['data']['edges'],v['id']+' · '+v['title'],v['data'].get('roles'))
                for path,val in leaves(v):
                    if path.startswith('/data/edges/'):continue
                    if path.startswith('/data/roles/'):
                        idx=int(path.split('/')[3]);binding=f"{g['id']}.node.{v['data']['roles'][idx][0]}"
                    else:binding=g['id']+'.title'
                    bind(source,path,binding,'component_identity_or_role',val)
            elif v['kind']=='events':
                if set(v['data'])!={'events'}:raise ValueError('Unknown event component fields')
                events=[]
                raw_events=v['data']['events']
                if isinstance(raw_events,dict):
                    if set(raw_events)!={'columns','rows'} or raw_events['columns']!=['entity','minute','severity','source']:raise ValueError('Unknown event table')
                    raw_events=[dict(zip(raw_events['columns'],row,strict=True)) for row in raw_events['rows']]
                for e in raw_events:
                    if set(e)!={'entity','minute','severity','source'}:raise ValueError('Unknown event fields')
                    events.append({'entity':e['entity'],'minute':float(e['minute']),'severity':str(e['severity']),'source':e['source']})
                card=add('events',v['title'],data={'events':events})
                for path,val in leaves(v):bind(source,path,card['id']+'.title','event_graph',val)
            else:raise ValueError('Unknown original component')
        elif kind=='json':
            prefix=record.get('prefix','')
            if prefix=='directed_call_edge':
                if set(v)!={'caller','callee'}:raise ValueError('Unknown directed edge')
                selected_edges.append((source,v))
            elif prefix=='propagation_service':
                if set(v)!={'evidence_source_display','onset_rel_min_display','rank','service','severity_z_display'}:raise ValueError('Unknown observed-onset metadata')
                globals_.append(record)
            elif 'values' in v:
                if set(v)!={'entity','region','semantic','unit','values'}:raise ValueError('Unknown supplement')
                pairs=[]; values=v['values']
                allowed={'level','template'}|{phase+'_'+key for phase in ('reference','current') for key in (
                    'count','entity_log_count','interval_s','numeric_parameters','recorded_range_s',
                    'inclusive_median_ms','observed_requests','span_count','spans_with_request_id','median','samples','mad')}
                if set(values)-allowed:raise ValueError('Unknown supplement value field')
                for key,value in values.items():
                    if key.startswith('reference_') and not isinstance(value,(list,dict,bool)) and value is not None:
                        other='current_'+key[len('reference_'):]
                        if other in values and values[other] is not None:
                            try:a,b=numeric(value),numeric(values[other])
                            except ValueError:continue
                            name=key[len('reference_'):];unit='ms' if name.endswith('_ms') else 'count' if name.endswith(('count','requests','request_id','samples')) else v['unit']
                            pairs.append({'name':name,'unit':unit,'reference':a,'current':b})
                if pairs:
                    card=add('comparison',v['semantic'],v['entity'],v['unit'],{'comparisons':pairs,'details':[]})
                    captions(card,source,v)
                else:globals_.append(record)
            elif set(v) in ({'from','to','relation'},{'child','parent','relation','supporting_span_pairs'}):
                source_id=v.get('from',v.get('parent'));target=v.get('to',v.get('child'))
                kind=v['relation']
                if isinstance(source_id,list) or isinstance(target,list):
                    if not (isinstance(source_id,list) and isinstance(target,list) and len(source_id)==len(target)==2 and kind=='observed parent span -> child span'):
                        raise ValueError('Unknown request-parent identity tuple')
                    globals_.append({'source':source,'kind':'metadata','value':{'parent':source_id,'child':target,'relation':kind}})
                    source_id,target=source_id[0],target[0];kind='request_parent'
                extra_edges.append((source,v,[source_id,target,kind]))
                if 'supporting_span_pairs' in v:globals_.append({'source':source,'kind':'metadata','value':{'edge':f'{source_id} → {target}','supporting_span_pairs':v['supporting_span_pairs']}})
            elif set(v)=={'entity','region','semantic','unit'}:globals_.append(record)
            else:raise ValueError('Unknown JSON source shape '+str(v.keys()))
        else:raise ValueError('Unhandled record kind')
    if extra_edges:
        g=graph('bound_relations',[e for _,_,e in extra_edges],'Additional observed relationships')
        for i,(source,v,_) in enumerate(extra_edges):
            for path,val in leaves(v):
                if path!='/supporting_span_pairs':bind(source,path,g['id']+'.edge.e'+str(i),value=val)
    if selected_edges:
        g=graph('selected_calls',[[v['caller'],v['callee'],'calls'] for _,v in selected_edges],'Selected observed calls')
        for i,(source,v) in enumerate(selected_edges):
            for path,val in leaves(v):bind(source,path,g['id']+'.edge.e'+str(i),value=val)
    # Each frozen window summary is a caption on its own real series/trace chart.
    for r in window_records:
        v=r['value'];matches=[c for c in cards if c['title'].startswith(v['id']+' · ')]
        if len(matches)!=1:raise ValueError('Window/card source ambiguity')
        captions(matches[0],r['source'],v)
    for relation in public['payload']['relations']:
        d={'parent':relation['parent'],'child':relation['child'],'parent_operation':relation['parent_operation'],
           'child_operation':relation['child_operation'],'support':[relation['phases'][p]['n'] for p in ('reference','current')],
           'samples':[{'phase':p,'parent_ms':q[0],'child_ms':q[1]} for p in ('reference','current') for q in relation['phases'][p]['points']]}
        card=add('trace_joint',relation['id']+' · Same-request observed durations',unit='ms',data=d)
        # Existing joint component has no details contract. Public statistics are
        # plotted in typed comparison cards and captions on a separate inventory.
        pair_id=relation['id']
        binary={k:v for k,v in relation.items() if k not in {'phases','unit'}}
        binary['phases']={phase:{k:v for k,v in values.items() if k in {'n','binary'}} for phase,values in relation['phases'].items()}
        continuous={'phases':{phase:{k:v for k,v in values.items() if k in {'quantiles','conditional_child'}} for phase,values in relation['phases'].items()}}
        globals_.append({'source':pair_sources['pair_binary'],'kind':'pair_binary_stats','title':pair_id+' · observed joint counts and reference thresholds',
                         'identities':[relation['parent'],relation['child']],'value':{pair_id:binary},'unit':'ms for duration thresholds; counts for joint groups'})
        globals_.append({'source':pair_sources['pair_continuous'],'kind':'pair_continuous_stats','title':pair_id+' · population and conditional duration quantiles',
                         'identities':[relation['parent'],relation['child']],'value':{pair_id:continuous},'unit':'ms for quantiles; counts for n'})
        for phase in ('reference','current'):
            for i,pair in enumerate(relation['phases'][phase]['points']):
                offset=0 if phase=='reference' else len(relation['phases']['reference']['points'])
                for j,value in enumerate(pair):bind(pair_sources['pair_continuous'],f"/{relation['id']}/{phase}/points/{i}/{j}",f"{card['id']}.sample.{offset+i}",value=value)
    # Public scalar metadata stays in an independent region, never attributed to
    # the first metric/candidate and never transported in model-visible text.
    for r in globals_:
        v=r['value']
        owner=v.get('entity',v.get('service'))
        identities=r.get('identities',[owner] if owner else [])
        title=r.get('title',str(v.get('semantic',v.get('field','Observed source summary'))))
        # Keep record scope visible, never interleave unrelated entity fields.
        card=add('inventory',title,unit=r.get('unit',v.get('unit') or ''),data={'identities':identities,'details':[]})
        captions(card,r['source'],v)
    cards, components, mapping, aliases = share_relationship_glyphs(cards, components, mapping)
    from renderer.utils import validate_evidence
    evidence={'schema':'CanvasEvidenceV1','cards':cards};validate_evidence(evidence)
    design=layout(evidence,components)
    return {'ledger':packet,'evidence':evidence,'design':design,'mapping':mapping,
            'relationship_aliases':aliases,'source_complete_claim':False,'note':'Projection coverage must be independently reconciled; bindings alone are not qualification.'}


def detail_label(path, value, card, public):
    """Explicit decoding of frozen table columns, without changing values."""
    parts=path.strip('/').split('/');last=parts[-1]
    if parts[0]=='log_r' and last.endswith(('_base','_fault')):
        quantity,period=last.rsplit('_',1);phase='reference' if period=='base' else 'current'
        unit='events/min' if 'rate' in quantity else 'count'
        return 'LOG-R · '+phase+' · '+quantity.replace('_',' ')+' · '+unit
    if parts[0]=='numeric_preview' and len(parts)>1:
        unit='count' if last in {'sample_count','distinct_count'} or ('most_common' in parts and last=='1') else 'source_unit'
        quantity=('value' if last=='0' else 'occurrences') if 'most_common' in parts else last
        return 'template '+parts[1]+' · '+quantity.replace('_',' ')+' · '+unit
    relation=next((r for r in public['payload']['relations'] if r['id']==parts[0]),None)
    if relation:
        prefix=relation['id']+' · '
        if 'thresholds' in parts:return prefix+('parent' if parts[-1]=='0' else 'child')+' reference p95 · ms'
        if 'phases' in parts:
            phase=parts[2];field=parts[3];prefix+=phase+' · '
            if field=='n':return prefix+'captured requests · count'
            if field=='binary':
                label=['parent≤p95 child≤p95','parent≤p95 child>p95','parent>p95 child≤p95','parent>p95 child>p95'][int(parts[4])]
                return prefix+label+' · count'
            if field=='quantiles':return prefix+['parent','child'][int(parts[4])]+' '+['p50','p95'][int(parts[5])]+' · ms'
            if field=='conditional_child':
                group=relation['phases'][phase]['conditional_child'][int(parts[4])][0]
                prefix+=('parent>ref p95' if group else 'parent≤ref p95')+' · '
                return prefix+['parent_slow (0/1)','requests · count','child p50 · ms','child p95 · ms'][int(parts[5])]
        return prefix+' '.join(parts[1:]).replace('_',' ')
    exact={'exl_p95_base_us':'reference exclusive p95 · µs','exl_p95_fault_us':'current exclusive p95 · µs',
        'inl_p95_fault_us':'current inclusive p95 · µs','count_base':'reference span count','count_fault':'current span count',
        'count_lfc':'span count change · log2 ratio','latency_lfc':'exclusive latency change · log2 ratio'}
    return exact.get(last,path.strip('/').replace('/',' · '))


def layout(evidence,components):
    """Fixed pre-outcome capacity policy: font18 (existing layered-grid contract), width8192, 8 columns, user-authorized maximum8192x8192.

    Heights follow source strings/counts, never rankings or labels. No hidden
    shrink-to-fit. Overflow remains a technical failure with its full source.
    """
    columns=[[] for _ in range(8)];heights=[0]*8; entries=[]
    for card in evidence['cards']:
        k=card['kind'];d=card['data'];cid=card['id']
        head=76+25*math.ceil(len(card['title'])/90)
        details=d.get('details',[])
        lines=[max(1,math.ceil((len(r['name'])+len(r['value']))/52)) for r in details]
        dh=sum(max(lines[i:i+2])*20+6 for i in range(0,len(lines),2))
        if k=='graph':
            # Existing radial grammar; large graph requires genuine readable area.
            from renderer.utils import node_link_layout
            h=node_link_layout(card,1000,18)['min_height']+20
        elif k=='trace_joint':h=800
        elif k=='comparison':h=head+140*len(d['comparisons'])+dh
        elif k=='inventory':h=head+44*math.ceil(len(d['identities'])/10)+dh+40
        elif k=='log':h=head+200+28*math.ceil(len(d['template'])/85)+dh
        else:h=head+230+dh
        h=max(200,math.ceil(h/32)*32)
        node={'id':'P'+cid,'type':'panel','card':cid,'component':components[cid]}
        if k=='graph':node['node_layout']='layered_grid'
        entries.append((node,h))
    # Source-size packing only; preserves card contents, identities and stable
    # component indices. Candidate inventory remains the first reserved card.
    candidate={c['id'] for c in evidence['cards'] if c['title'].startswith('Candidate IDs')}
    for node,h in sorted(entries,key=lambda pair:(pair[0]['card'] not in candidate,-pair[1],pair[0]['card'])):
        col=min(range(8),key=lambda i:(heights[i],i))
        columns[col].append((node,h));heights[col]+=h+16
    full=max(heights)
    children=[]
    for i,column in enumerate(columns):
        nodes=[node for node,h in column];weights=[h for node,h in column]
        delta=full-heights[i]
        if delta:
            nodes.append({'id':'spacer'+str(i),'type':'spacer'});weights.append(max(1,delta-16))
        children.append({'id':'column'+str(i),'type':'column','children':nodes,'weights':weights})
    return {'schema':'DashboardDesignV1','viewport':{'width':8192,'height':full+110},
        'canvas_extent':'wide_8192_v1','theme':'dark','font_size':18,'gap':16,'padding':24,'scale':1,
        'indexing':{'visible':True,'start':1,'indices':{c['id']:i+1 for i,c in enumerate(evidence['cards'])}},'bindings':[],'graph':{'show_isolates':True},
        'tree':{'id':'root','type':'row','children':children,'weights':[1]*8}}


def share_relationship_glyphs(cards, components, mapping):
    """Reuse exact typed relationship assertions, not equal numeric observations.

    All original edge/node source aliases survive. An observed request-parent
    edge remains separate from aggregate calls even for the same endpoints.
    """
    graphs=[c for c in cards if c['kind']=='graph']
    if not graphs:return cards,components,mapping,[]
    bykind={}; aliases={}; audit=[]
    for card in graphs:
        for edge in card['data']['edges']:
            group='calls' if edge['kind'] in {'calls','request_parent'} else 'deployment'
            bucket=bykind.setdefault(group,{'edges':{},'nodes':{}})
            key=(edge['source'],edge['target'],edge['kind'])
            bucket['edges'].setdefault(key,[]).append((card['id'],edge['id']))
            for node in card['data']['nodes']:
                if node['id'] not in key[:2]:continue
                prior=bucket['nodes'].get(node['id'])
                if prior and prior.get('role') and node.get('role') and prior['role']!=node['role']:
                    raise ValueError('Conflicting observed entity role')
                bucket['nodes'][node['id']]={**(prior or {}),**node}
    shared=[]
    for group,bucket in bykind.items():
        cid='GRCALL' if group=='calls' else 'GRDEP'
        edges=[]
        for i,(key,sources) in enumerate(bucket['edges'].items()):
            eid='e'+str(i);edges.append(dict(id=eid,source=key[0],target=key[1],kind=key[2]))
            for old,edge in sources:
                aliases[old+'.edge.'+edge]=cid+'.edge.'+eid
                for entity in key[:2]:aliases[old+'.node.'+entity]=cid+'.node.'+entity
                aliases.setdefault(old+'.title',cid+'.title')
            audit.append({'typed_relation':list(key),'source_glyphs':[a+'.edge.'+b for a,b in sources],
                          'canonical_binding':cid+'.edge.'+eid})
        shared.append(dict(id=cid,kind='graph',entity=None,unit='',
            title='Observed calls and request parents' if group=='calls' else 'Observed deployment membership',
            data={'nodes':list(bucket['nodes'].values()),'edges':edges}))
        components[cid]='graph.node_link'
    result=[];emitted=False
    for card in cards:
        if card['kind']=='graph':
            components.pop(card['id'],None)
            if not emitted:result.extend(shared);emitted=True
        else:result.append(card)
    for row in mapping:
        if row['binding'] in aliases:row['binding']=aliases[row['binding']]
    return result,components,mapping,audit


def comparison_provenance(compiled, public):
    """Typed public operands only; no values/scores or labels enter the allocator."""
    roles={};edges=[];target_owners={};self_pairs=[];parents=[];aliases=[];canonical={};caption_pairs={}
    clock=public['payload']['clock'];duration=float(clock['duration']);split=float(clock['split'])
    if not 0<=split<=duration or duration<=0:raise ValueError('Public phase clock invalid')
    mapping=compiled['mapping'];by_binding={}
    records={r['source']:r for r in compiled['ledger']['records']}
    for m in mapping:
        if m['binding']:by_binding.setdefault(m['binding'],[]).append(m)
    def role(source,entity,signal,quantity,unit,phase,targets):
        key=[source,entity,signal,quantity,unit,phase];rid='r'+stable_hash(key)[:16]
        if rid in roles:raise ValueError('Repeated source role construction')
        unique=[]
        for target in targets:
            identity=(target['binding'],target['part'])
            if identity in target_owners:raise ValueError('Canonical foreground claimed twice')
            target_owners[identity]=rid;unique.append(target)
        if not unique:return None
        roles[rid]={'id':rid,'source_occurrence':source,'entity':entity,'signal':signal,
            'quantity':quantity,'unit':unit,'phase':phase,'targets':unique}
        return rid
    def pair(a,b):
        if a and b:self_pairs.append((a,b))
    def target(binding,part='all'):return {'binding':binding,'part':part}
    def claim(rid,source,paths):
        for path in paths:
            key=(source,path)
            if key in canonical and canonical[key]!=rid:raise ValueError('Different roles claim one source operand')
            canonical[key]=rid
    def source_of(cid,k):
        sources={m['source'] for m in mapping if m['binding'] and m['binding'].startswith(cid+'.')}
        candidates=[records[s] for s in sources if s in records and
            ((k=='metric' and (records[s]['kind']=='aux' or records[s]['value'].get('field')=='metric_series_64')) or
             (k=='trace' and records[s]['value'].get('field')=='trace_summary_entry') or
             (k=='log' and records[s]['value'].get('field')=='denum_log_template') or
             (k=='comparison' and records[s]['kind']=='json' and 'values' in records[s]['value']))]
        if len(candidates)!=1:raise ValueError('Ambiguous canonical source for '+cid)
        return candidates[0]
    for card in compiled['evidence']['cards']:
        cid,k,d=card['id'],card['kind'],card['data'];owner=card['entity'];unit=card['unit'];signal=card['title']
        if k=='metric':
            origin=source_of(cid,k);source=origin['source']+'/values_codec';signal=origin['value']['metric']
            ids={p:[] for p in ('reference','current')}
            for i,(bin,value) in enumerate(zip(d['bins'],d['values'],strict=True)):
                if value is not None:
                    # The inherited projection uses equal-width BIN CENTERS,
                    # not endpoint samples stretched over n-1 intervals.
                    phase='reference' if (bin+.5)/len(d['bins'])*duration<split else 'current'
                    ids[phase].append(target(f'{cid}.sample.{i}'))
            a=role(source,owner,signal,'recorded_series',unit,'reference',ids['reference'])
            b=role(source,owner,signal,'recorded_series',unit,'current',ids['current']);pair(a,b)
        elif k=='trace':
            origin=source_of(cid,k);source=origin['source'];signal=origin['value']['operation']
            a=role(source,owner,signal,'exclusive_p95',unit,'reference',[target(cid+'.before','marks_and_value')])
            b=role(source,owner,signal,'exclusive_p95',unit,'current',[target(cid+'.after','marks_and_value')]);pair(a,b)
            claim(a,source,['/exl_p95_base_us']);claim(b,source,['/exl_p95_fault_us'])
        elif k=='comparison':
            origin=source_of(cid,k);source=origin['source'];signal=origin['value']['semantic']
            for i,row in enumerate(d['comparisons']):
                a=role(source,owner,signal,row['name'],row['unit'],'reference',[target(f'{cid}.comparison.{i}.reference')])
                b=role(source,owner,signal,row['name'],row['unit'],'current',[target(f'{cid}.comparison.{i}.current')]);pair(a,b)
                claim(a,source,['/values/reference_'+row['name']]);claim(b,source,['/values/current_'+row['name']])
        elif k=='trace_joint':
            quartet=[]
            for side in ('parent','child'):
                staged=[]
                for phase in ('reference','current'):
                    targets=[target(f'{cid}.sample.{i}',side+'_point') for i,s in enumerate(d['samples']) if s['phase']==phase]
                    origins=[m for m in mapping if m['binding'] and m['binding'].startswith(cid+'.sample.') and m['path'].endswith('/'+str(0 if side=='parent' else 1))]
                    if not origins:raise ValueError('Joint plot has no source operands')
                    source=origins[0]['source']+'/'+card['title'].split(' · ')[0]+'/points/'+side
                    r=role(source,d[side],d[side+'_operation'],'recorded_inclusive_duration','ms',phase,targets)
                    staged.append(r);quartet.append(r)
                pair(*staged)
            if all(quartet):parents.append(quartet)
        elif k=='log':
            origin=source_of(cid,k);source=origin['source'];signal=origin['value']['template_id']
            r=role(source,owner,signal,'template_count','count','observed_window',
                 [target(f'{cid}.sample.{i}') for i in range(len(d['counts']))])
            claim(r,source,['/count'])
        # Supplemental observed values retain their source identity. Existing
        # duplicate scalar captions are aliases, not a second weighted role.
        for i,item in enumerate(d.get('details',[])):
            binding=f'{cid}.detail.{i}';mapped=by_binding.get(binding,[])
            if not mapped:raise ValueError('Caption has no public source')
            identities={(m['source'],m['path']) for m in mapped}
            if len(identities)!=1:raise ValueError('Caption aliases distinct source occurrences')
            source_id,path=next(iter(identities))
            if (source_id,path) in canonical:
                aliases.append({'binding':binding,'canonical_role':canonical[(source_id,path)],'source':source_id,'path':path})
                continue
            source=source_id+path
            record=records[source_id]['value']
            typed=caption_operand(record,path,item['value'],card,public)
            if typed is None:continue
            entity,signal,quantity,u,phase,pair_key=typed
            rid=role(source,entity,signal,quantity,u,phase,[target(binding,'value')])
            if pair_key is not None:caption_pairs.setdefault((source_id,pair_key,entity,signal,quantity,u),{})[phase]=rid
    for phases in caption_pairs.values():
        if set(phases)=={'reference','current'}:pair(phases['reference'],phases['current'])
    for a,b in self_pairs:edges.append({'type':'self_change','roles':[a,b]})
    for r in parents:edges.append({'type':'parent_child','roles':r})
    # Peer membership is public, typed, and observed. Never infer by names.
    memberships={}
    for card in compiled['evidence']['cards']:
        if card['kind']=='graph':
            for e in card['data']['edges']:
                if e['kind'] in {'hosts','owns','has_instance'}:
                    memberships.setdefault(e['source'],set()).add(e['target'])
    values=list(roles.values())
    for i,a in enumerate(values):
        for b in values[i+1:]:
            if not a['entity'] or a['entity']==b['entity']:continue
            # Remove only stable source display prefixes, not operation content.
            sa=re.sub(r'^(MET|AUX)\d+ · ','',a['signal']);sb=re.sub(r'^(MET|AUX)\d+ · ','',b['signal'])
            if (sa,a['quantity'],a['unit'],a['phase'])!=(sb,b['quantity'],b['unit'],b['phase']):continue
            if any({a['entity'],b['entity']}<=members for members in memberships.values()):
                edges.append({'type':'peer','roles':[a['id'],b['id']]})
    seen=set();dedup=[]
    for e in edges:
        key=(e['type'],tuple(e['roles']) if e['type']=='parent_child' else tuple(sorted(e['roles'])))
        if key not in seen:seen.add(key);dedup.append(e)
    paired={r for e in dedup for r in e['roles']}
    for rid in roles:
        if rid not in paired:dedup.append({'type':'singleton','roles':[rid]})
    return {'schema':'ComparisonProvenancePacketV1','roles':list(roles.values()),'edges':dedup,
            'foreground':{'schema':'CanonicalForegroundV2','roles':[{'id':r['id'],'targets':r['targets']} for r in roles.values()]},
            'private_or_score_fields':False,'phase_clock':clock,'noncanonical_presentations':aliases}


def caption_operand(record,path,display,card,public):
    """Only typed numerical observations enter allocation; text/metadata anchors."""
    parts=path.strip('/').split('/');last=parts[-1]
    if any(k in parts for k in ('id','entity','entity_id','entities','service','parent','child','region','field','unit','metric','operation',
        'parent_operation','child_operation','rank','legacy_display_rank','entry_index','rank_score','signed_z','severity_z_display',
        'score','deviation_sigma','fluctuating_3sigma','onset_rel_min_display','evidence_source_display','summary','name','source_metric_rows',
        'duration_rel_s','relative_bin','omitted_numeric_variables','omitted_services','service_count','template_count','event_count')):return None
    try:value=numeric(display)
    except ValueError:return None
    if value is None:return None
    entity=card['entity'] or record.get('entity',record.get('service'));signal=record.get('metric',record.get('operation',card['title']))
    quantity=path;unit=card['unit'];phase='whole_window';pair_key=None
    if parts[0]=='log_r':
        if last.endswith(('_base','_fault')):
            quantity,period=last.rsplit('_',1);unit='events/min' if 'rate' in quantity else 'count'
            return entity,'LOG-R',quantity,unit,'reference' if period=='base' else 'current','LOG-R/'+quantity
        raise ValueError('Unknown numerical LOG-R field')
    if parts[0]=='numeric_preview':
        unit='count' if last in {'sample_count','distinct_count'} or ('most_common' in parts and last=='1') else 'source_unit'
        return entity,signal,quantity,unit,'observed_window',None
    relation=next((r for r in public['payload']['relations'] if r['id']==parts[0]),None)
    if relation:
        if 'thresholds' in parts:
            side=['parent','child'][int(last)];return relation[side],relation[side+'_operation'],'reference_p95_threshold','ms','reference',None
        if 'phases' not in parts:return None
        phase=parts[2];field=parts[3];unit='count';entity=None;signal=relation['id'];quantity=field
        if field=='quantiles':
            side=['parent','child'][int(parts[4])];entity=relation[side];signal=relation[side+'_operation'];unit='ms'
            quantity='inclusive_'+['p50','p95'][int(parts[5])]
        elif field=='conditional_child':
            col=int(parts[5]);group=relation['phases'][phase][field][int(parts[4])][0]
            if col==0:return None
            entity=relation['child'];signal=relation['child_operation'];unit='count' if col==1 else 'ms'
            quantity='parent_slow_'+str(group)+'_'+['group','requests','inclusive_p50','inclusive_p95'][col]
        elif field=='binary':quantity='joint_binary_'+parts[4]
        elif field!='n':raise ValueError('Unknown relation statistic')
        return entity,signal,quantity,unit,phase,relation['id']+'/'+quantity
    if last.endswith('_us'):unit='µs'
    elif last.endswith('_ms'):unit='ms'
    elif last.endswith('_lfc'):unit='log2_fold_change'
    elif any(v in last for v in ('count','samples','requests','request_id')) or last in {'n','omitted_services','service_count'}:unit='count'
    if parts[0]=='values':
        if last in {'0','1'} or 'interval' in path:return None
        if last.startswith(('reference_','current_')):phase,last=last.split('_',1);quantity=last;pair_key=last
    elif last.startswith(('regular_','current_')):
        prefix,last=last.split('_',1);phase='reference' if prefix=='regular' else 'current';quantity='/'.join(parts[:-1]+[last]);pair_key=quantity
    elif last in {'count_base','count_fault'}:
        phase='reference' if last.endswith('base') else 'current';quantity='span_count';pair_key='span_count'
    if isinstance(value,bool):return None
    return entity,signal,quantity,unit,phase,pair_key


def text_conditions(public, compiled, provenance):
    """Complete text controls; no facts, candidate IDs or precision removed."""
    full=public['texts']['RAW_TEXT']
    if not isinstance(full,list) or any(set(p)!={'text','type'} or p['type']!='text' for p in full):
        raise ValueError('Frozen strong text is not text-only')
    task=VISUAL_TASK.replace('using the complete telemetry dashboard. All incident observations and the exhaustive candidate IDs are in the image. Use only its candidate inventory',
        'using the complete telemetry records below. Use only the exhaustive candidate inventory')
    legend=('Complete public records; record IDs denote original occurrences, never scores. '
        'values_codec uses length and [value,zero-based-position-ranges]; all bins occur exactly once. '
        'Pair binary rows: [ID,parent,parent operation,child,child operation,[reference p95 parent,child],'
        '[[phase,total requests,[neither slow,child slow,parent slow,both slow]]]]. '
        'Pair continuous rows: [ID,[[phase,[[parent p50,p95],[child p50,p95]],'
        '[[parent slow 0/1,count,child p50,p95]],[[parent ms,child ms]]]]]. '
        'All pair durations are inclusive milliseconds; slow is strictly above reference p95. '
        'LOG-R error/log rates use events per recorded minute; their count fields are counts. '
        'Template numeric parameters have unverified source units unless explicitly declared. '
        'Comparison links register observed readings to compare, not causal edges.\n')
    records=compiled['ledger']['records']
    def serial(rows):return '\n'.join(json.dumps(r,ensure_ascii=False,separators=(',',':')) for r in rows)
    ledger_text=task+'\n'+legend+serial(records)
    # Each occurrence appears once, in connected components of the SAME public
    # comparison graph. Records without a multi-role link retain a global area.
    lookup={r['id']:r for r in provenance['roles']};parents={r['source']:r['source'] for r in records}
    def find(x):
        while parents[x]!=x:x=parents[x]
        return x
    linked=set()
    for edge in provenance['edges']:
        if len(edge['roles'])<=1:continue
        sources=[lookup[u]['source_occurrence'].split('/')[0] for u in edge['roles']]
        linked.update(sources)
        for source in sources[1:]:parents[find(source)]=find(sources[0])
    groups={}
    for record in records:
        if record['source'] in linked:groups.setdefault(find(record['source']),[]).append(record)
    sections=['Comparison-linked records '+str(i+1)+'\n'+serial(rows) for i,rows in enumerate(groups.values())]
    global_records=[r for r in records if r['source'] not in linked]
    sections.append('Independent/global records\n'+serial(global_records))
    dep_text=task+'\n'+legend+'\n'.join(sections)
    return {'T_FULL':full,'T_NATIVE':full,'T_LEDGER':[{'type':'text','text':ledger_text}],
            'T_DEP':[{'type':'text','text':dep_text}]}


QA_TASK = '''Answer the two independent factual blocks marked 1A/1B and 2A/2B in the evidence. For each applicable block report: read={value_A:number,value_B:number}; bind={A:{entity_id,signal_or_operation_id,unit,phase},B:{entity_id,signal_or_operation_id,unit,phase}}; compare=A_greater|B_greater|equal_at_display_precision. Return JSON {"blocks":[block1,block2]}; use null only for an unmarked whole block. Badges carry no phase meaning. Do not diagnose a root cause.'''
ATLAS_GUIDE = 'The quantile strips show standardized reference/current changes at p10,p50,p90 and, where observed peer support permits, deviation from the peer median. Color intensity uses asinh on a shared symmetric scale; printed values are untransformed standardized quantities. Zero denotes no measured change/deviation. Color is not causal severity. Original units and observations remain in their original components.'


def mechanism_roster(rows, per_dataset=30):
    from collections import defaultdict
    selected=[]
    for ds in ('aiops2022','aiops2025','aegislab'):
        groups=defaultdict(list)
        for r in rows:
            if r['dataset']==ds:groups[r['leakage_group']].append(r)
        ordered=[sorted(v,key=lambda r:stable_hash(['rq41_mechanism_case_v1',r['opaque_incident_id']]))
                 for k,v in sorted(groups.items(),key=lambda kv:stable_hash(['rq41_mechanism_group_v1',kv[0]]))]
        picked=[]
        while ordered and len(picked)<per_dataset:
            for group in ordered:
                if group and len(picked)<per_dataset:picked.append(group.pop(0))
            ordered=[g for g in ordered if g]
        if len(picked)!=per_dataset:raise ValueError('Insufficient mechanism roster')
        selected.extend(picked)
    return selected


def scalar_target(compiled, role):
    """Resolve only explicitly displayed single scalars, not a curve estimate."""
    if len(role['targets'])!=1:return None
    target=role['targets'][0];binding=target['binding'];cid=binding.split('.')[0]
    c=next(c for c in compiled['evidence']['cards'] if c['id']==cid);d=c['data']
    if binding.endswith(('.before','.after')):value=d[binding.rsplit('.',1)[1]];rounded=True
    elif '.detail.' in binding:value=d['details'][int(binding.rsplit('.',1)[1])]['value'];rounded=False
    elif '.comparison.' in binding:
        _,_,i,phase=binding.split('.');value=d['comparisons'][int(i)][phase];rounded=True
    else:return None
    try:v=numeric(value)
    except (TypeError,ValueError):return None
    if v is None:return None
    display=('0' if v==0 else format(v,'.3e' if abs(v)>=1e5 or abs(v)<.001 else '.5g')) if rounded else str(value)
    from decimal import Decimal,InvalidOperation
    try:tolerance=float(Decimal(display).as_tuple().exponent)
    except InvalidOperation:return None
    tolerance=.5*10**tolerance
    mapped=[m for m in compiled['mapping'] if m['binding']==binding]
    if len(mapped)!=1:return None
    return {'target':target,'value':v,'display':display,'displayed_value':float(display),'tolerance':tolerance,
        'source':mapped[0]['source'],'path':mapped[0]['path'],'role':role['id'],
        'binding_answer':{'entity_id':role['entity'],'signal_or_operation_id':role['signal'],'unit':role['unit'],'phase':role['phase']}}


def _mark_original_scalar(raw, path, badge):
    key=path.rsplit('/',1)[-1]
    # Match only a unique field inside this exact source occurrence, not the
    # same numerical value somewhere else in the complete text.
    pattern=r'((?:"'+re.escape(key)+r'"\s*:\s*|(?<![\w])'+re.escape(key)+r'=))(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)'
    matches=list(re.finditer(pattern,raw))
    if len(matches)!=1:raise ValueError('No unique original textual scalar locator')
    m=matches[0];return raw[:m.end()]+f' [{badge}]'+raw[m.end():]


def qa_packet(public,compiled,provenance,oid):
    from copy import deepcopy
    lookup={r['id']:r for r in provenance['roles']};atoms={a['id']:a for a in public['organization']['atoms']}
    original='\n'.join(p['text'] for p in public['texts']['RAW_TEXT']);eligible=[];seen=set()
    for edge in provenance['edges']:
        if edge['type']!='self_change':continue
        pair=[scalar_target(compiled,lookup[u]) for u in edge['roles']]
        if any(p is None for p in pair):continue
        a,b=pair;ra,rb=(lookup[p['role']] for p in pair)
        if (ra['entity'],ra['signal'],ra['quantity'],ra['unit'])!=(rb['entity'],rb['signal'],rb['quantity'],rb['unit']):continue
        if {ra['phase'],rb['phase']}!={'reference','current'}:continue
        if a['value']!=b['value'] and abs(a['displayed_value']-b['displayed_value'])<=a['tolerance']+b['tolerance']:continue
        identity=tuple(sorted((p['source'],p['path']) for p in pair))
        if identity in seen:continue
        try:
            for p in pair:
                raw=atoms[p['source']]['raw']
                if original.count(raw)!=1:raise ValueError('Ambiguous source in full text')
                _mark_original_scalar(raw,p['path'],'A')
        except ValueError:continue
        seen.add(identity);eligible.append(pair)
    chosen=sorted(eligible,key=lambda p:stable_hash(['rq41_qa_pair_v1',oid,[(v['source'],v['path']) for v in p]]))[:2]
    blocks=[];badges=[];changed={}
    for slot,pair in enumerate(chosen,1):
        pair=sorted(pair,key=lambda p:p['binding_answer']['phase'])
        if int(stable_hash(['rq41_qa_badge_v1',oid,slot])[:16],16)%2:pair.reverse()
        for name,p in zip(('A','B'),pair):
            badges.append({'slot':slot,'badge':name,**p['target']})
            raw=changed.get(p['source'],atoms[p['source']]['raw'])
            changed[p['source']]=_mark_original_scalar(raw,p['path'],str(slot)+name)
        a,b=pair;comparison='equal_at_display_precision' if a['displayed_value']==b['displayed_value'] else ('A_greater' if a['displayed_value']>b['displayed_value'] else 'B_greater')
        blocks.append({'slot':slot,'A':a,'B':b,'comparison':comparison})
    annotated=original
    for source,replacement in changed.items():annotated=annotated.replace(atoms[source]['raw'],replacement,1)
    design=deepcopy(compiled['design']);design['qa_badges']=badges;design['provenance']=provenance['foreground']
    return {'schema':'LinkedQAPacketV1','blocks':blocks,'applicable_blocks':len(blocks),
        'public_badges':badges,'static_task':QA_TASK,'text_evidence':annotated,
        'design':design,'eligible_pairs':len(eligible),'answers_are_audit_only':True}


def score_linked_qa(packet,response):
    try:
        answer=json.loads(response);blocks=answer['blocks']
        if set(answer)!={'blocks'} or not isinstance(blocks,list) or len(blocks)!=2:raise ValueError('QA response schema')
    except (ValueError,TypeError,KeyError):blocks=[]
    out=[]
    for expected in packet['blocks']:
        actual=blocks[expected['slot']-1] if len(blocks)>=expected['slot'] else None
        read=bind=compare=0
        if isinstance(actual,dict):
            try:
                read=int(all(type(actual['read']['value_'+b]) in (int,float) and math.isfinite(actual['read']['value_'+b]) and
                    abs(actual['read']['value_'+b]-expected[b]['value'])<=expected[b]['tolerance'] for b in ('A','B')))
                bind=int(all(actual['bind'][b]==expected[b]['binding_answer'] for b in ('A','B')))
                compare=int(actual['compare']==expected['comparison'])
            except (KeyError,TypeError):pass
        out.append({'read':read,'bind':bind,'compare':compare,'joint':read*bind*compare})
    return {'blocks':out,'joint':sum(r['joint'] for r in out)/len(out) if out else None,'applicable_blocks':len(out)}


def intervention_inputs(public,compiled,provenance,oid,qa):
    """Frozen public-hash controls; corruptions never use original RCA labels."""
    from copy import deepcopy
    variants={};design=deepcopy(compiled['design']);children=design['tree']['children']
    offset=1+int(stable_hash(['rq41_position_v1',oid])[:12],16)%(len(children)-1)
    design['tree']['children']=children[offset:]+children[:offset]
    variants['POSITION']={'evidence':deepcopy(compiled['evidence']),'design':design,'provenance':provenance,
        'audit':{'label_scoring_allowed':True,'facts_unchanged':True,'column_rotation':offset}}
    cards=compiled['evidence']['cards'];pairs=[]
    for i,a in enumerate(cards):
        for b in cards[i+1:]:
            if a['entity'] and b['entity'] and a['entity']!=b['entity'] and len(a['entity'])==len(b['entity']) and (a['kind'],a['unit'])==(b['kind'],b['unit']) and a['kind'] in {'metric','trace','log','comparison'}:
                pairs.append((a['id'],b['id']))
    if pairs:
        a,b=min(pairs,key=lambda p:stable_hash(['rq41_binding_swap_v1',oid,p]));c=deepcopy(compiled)
        aa,bb=(next(x for x in c['evidence']['cards'] if x['id']==cid) for cid in (a,b))
        aa['entity'],bb['entity']=bb['entity'],aa['entity'];v=comparison_provenance(c,public)
        variants['BINDING']={'evidence':c['evidence'],'design':c['design'],'provenance':v,
            'audit':{'label_scoring_allowed':False,'changed_card_entity_labels':[a,b],'original_source_preserved':True}}
    if qa['blocks']:
        operand=qa['blocks'][0]['A'];c=deepcopy(compiled);source,path=operand['source'],operand['path'];old=operand['value']
        new=old+max(1,abs(old)*.5);modified=[]
        for m in c['mapping']:
            if (m['source'],m['path'])!=(source,path) or m['binding'] is None:continue
            bits=m['binding'].split('.');card=next(x for x in c['evidence']['cards'] if x['id']==bits[0]);data=card['data']
            if bits[1] in {'before','after'}:data[bits[1]]=new
            elif bits[1]=='detail':data['details'][int(bits[2])]['value']=str(new)
            elif bits[1]=='comparison':data['comparisons'][int(bits[2])][bits[3]]=new
            else:raise ValueError('Unsupported registered scalar intervention')
            modified.append(m['binding']);m['value_hash']=stable_hash(new)
        if not modified:raise ValueError('Operand change failed to bind')
        variants['OPERAND']={'evidence':c['evidence'],'design':c['design'],'provenance':provenance,
            'audit':{'label_scoring_allowed':False,'source':source,'path':path,'old':old,'new':new,'modified_bindings':modified}}
        d=deepcopy(compiled['design']);d['control_glyph']=operand['target']
        variants['IRRELEVANT']={'evidence':deepcopy(compiled['evidence']),'design':d,'provenance':provenance,
            'audit':{'label_scoring_allowed':False,'facts_unchanged':True,'matched_area':'original scalar DOM bounding area; ink coverage not claimed equal'}}
    for v in variants.values():v['design']['provenance']=v['provenance']['foreground']
    return variants


def empirical_quantile(values,p):
    x=sorted(values);h=(len(x)-1)*p;i=math.floor(h)
    return x[i]+(x[min(i+1,len(x)-1)]-x[i])*(h-i)


def contrast_inventory(compiled,public):
    """Public exact-source distributions; no inferred healthy-peer set."""
    series=[];clock=public['payload']['clock'];memberships={}
    for c in compiled['evidence']['cards']:
        d=c['data']
        if c['kind']=='graph':
            for e in d['edges']:
                if e['kind'] in {'hosts','owns','has_instance'}:memberships.setdefault(e['source'],set()).add(e['target'])
        if c['kind']=='metric':
            phases={p:[] for p in ('reference','current')}
            for i,v in enumerate(d['values']):
                if v is not None:phases['reference' if (i+.5)/len(d['values'])*clock['duration']<clock['split'] else 'current'].append(v)
            signal=re.sub(r'^(MET|AUX)\d+ · ','',c['title'])
            series.append({'card':c['id'],'entity':c['entity'],'signal':signal,'quantity':'recorded_series','unit':c['unit'],'phases':phases})
        elif c['kind']=='trace_joint':
            for side in ('parent','child'):
                series.append({'card':c['id'],'entity':d[side],'signal':d[side+'_operation'],'quantity':'recorded_inclusive_duration','unit':'ms',
                    'phases':{p:[r[side+'_ms'] for r in d['samples'] if r['phase']==p] for p in ('reference','current')}})
    valid=[];excluded=[];seen={}
    for s in series:
        ref,cur=(s['phases'][p] for p in ('reference','current'));key=(s['entity'],s['signal'],s['quantity'],s['unit'])
        if key in seen:
            # Distinct source records are not pooled or counted as new peers.
            # Preserve each strip and its source card; peers must be unique instances.
            pass
        seen[key]=True
        if min(len(ref),len(cur))<5:excluded.append({'card':s['card'],'entity':s['entity'],'reason':'fewer_than_five_per_phase'});continue
        med=empirical_quantile(ref,.5);scale=1.4826*empirical_quantile([abs(v-med) for v in ref],.5)
        if scale==0:scale=(empirical_quantile(ref,.75)-empirical_quantile(ref,.25))/1.349
        if scale==0:excluded.append({'card':s['card'],'entity':s['entity'],'reason':'zero_robust_scale'});continue
        qref=[empirical_quantile(ref,p) for p in (.1,.5,.9)];qcur=[empirical_quantile(cur,p) for p in (.1,.5,.9)]
        valid.append({**s,'reference_quantiles':qref,'current_quantiles':qcur,'scale':scale,'change':[(a-b)/scale for a,b in zip(qcur,qref)],'peer':None,'peer_entities':[]})
    for s in valid:
        owners=[members for members in memberships.values() if s['entity'] in members]
        peers={};ambiguous=set()
        for other in valid:
            e=other['entity']
            if e==s['entity'] or not any(e in group for group in owners) or (other['signal'],other['quantity'],other['unit'])!=(s['signal'],s['quantity'],s['unit']):continue
            if e in peers and peers[e]!=other['change']:ambiguous.add(e)
            peers[e]=other['change']
        s['ambiguous_peer_instances']=sorted(ambiguous)
        # Do not silently redefine the observed peer population by dropping
        # ambiguous duplicate-source instances. Retain the original observations.
        if len(peers)>=2 and not ambiguous:
            s['peer_entities']=sorted(peers);s['peer']=[s['change'][i]-empirical_quantile([v[i] for v in peers.values()],.5) for i in range(3)]
    return {'rows':valid,'omitted_derived_only':excluded,'all_original_evidence_preserved':True}


def compile_atlas(public,compiled):
    from copy import deepcopy
    from renderer.utils import compile_design
    inventory=contrast_inventory(compiled,public);c=deepcopy(compiled);cards=c['evidence']['cards']
    maxv=max([abs(math.asinh(v)) for r in inventory['rows'] for k in ('change','peer') for v in (r[k] or [])]+[1.])
    components={r['card']:r['component'] for r in compile_design(compiled['evidence'],compiled['design'])['rectangles']}
    for i,row in enumerate(inventory['rows']):
        cid='QCT'+str(i+1).zfill(3)
        cards.append({'id':cid,'kind':'contrast','title':'Observed quantile contrasts','entity':row['entity'],'unit':'standardized; raw units below',
            'data':{'contrast':{'limit':maxv,'rows':[{k:row[k] for k in ('signal','quantity','unit','change','peer')}]}}})
        components[cid]='contrast.quantile_contrast';row['derived_card']=cid
    # Candidate-ordered flow, down each column then left to right. Keep the
    # original card widths/heights and all derived strips, but do not reserve
    # eight mostly empty cells for every entity. No severity/outcome ordering.
    source_geometry={r['card']:r for r in compile_design(compiled['evidence'],compiled['design'])['rectangles']}
    inventories=[x for x in cards if x['title'].startswith('Candidate IDs')]
    reserved={x['id'] for x in inventories};groups=[]
    if inventories:groups.append(inventories)
    for entity in public['candidates']:
        group=[x for x in cards if x['entity']==entity and x['id'] not in reserved]
        if group:groups.append(group)
    globals_=[x for x in cards if x['entity'] not in public['candidates'] and x['id'] not in reserved]
    if globals_:groups.append(globals_)
    gap=compiled['design']['gap'];bundles=[];derived_source={r['derived_card']:r['card'] for r in inventory['rows']}
    def entry(card):
        cid=card['id']
        height=source_geometry[cid]['height'] if cid in source_geometry else 400+24*math.ceil(len(card['data']['contrast']['rows'][0]['signal'])/70)
        node={'id':'AP'+cid,'type':'panel','card':cid,'component':components[cid]}
        if card['kind']=='graph':node['node_layout']='layered_grid'
        return node,height
    for group in groups:
        # Same-entity source + derived strips are one indivisible bundle. A
        # multi-entity source stays in the global section; its entity strips
        # retain their original entity/signal labels and source audit mapping.
        used=set()
        for card in group:
            if card['kind']=='contrast':continue
            related=[x for x in group if x['kind']=='contrast' and derived_source[x['id']]==card['id']]
            bundles.append([entry(x) for x in [card,*related]]);used.update(x['id'] for x in related)
        bundles.extend([entry(x)] for x in group if x['kind']=='contrast' and x['id'] not in used)
    # Exact minimum maximum height for a contiguous eight-column partition.
    # Include one trailing gap in each bundle cost, then remove it per column.
    # This preserves the public reading order and source/strip adjacency.
    costs=[sum(h+gap for _,h in bundle) for bundle in bundles]
    def partition(limit):
        columns=[];column=[];height=0
        for bundle,cost in zip(bundles,costs):
            if column and height+cost>limit:columns.append(column);column=[];height=0
            column.extend(bundle);height+=cost
        if column:columns.append(column)
        return columns
    low=max(max(costs),math.ceil(sum(costs)/8));high=sum(costs)
    while low<high:
        middle=(low+high)//2
        if len(partition(middle))<=8:high=middle
        else:low=middle+1
    columns=partition(low);full=max(sum(h+gap for _,h in col)-gap for col in columns)
    children=[];reading=[]
    for i in range(8):
        col=columns[i] if i<len(columns) else [];nodes=[n for n,_ in col];weights=[h for _,h in col]
        reading.extend(n['card'] for n in nodes)
        delta=full-(sum(weights)+gap*(len(weights)-1)) if weights else full
        if not weights or delta>gap:
            nodes.append({'id':f'ATail{i}','type':'spacer'});weights.append(delta-gap if col else full)
        elif delta:weights[-1]+=delta
        children.append({'id':f'AColumn{i}','type':'column','children':nodes,'weights':weights})
    d=deepcopy(compiled['design']);d.pop('provenance',None);d['tree']={'id':'atlasroot','type':'row','children':children,'weights':[1]*8}
    d['viewport']['height']=full+86+d['padding']
    d['indexing']['indices']={cid:i+1 for i,cid in enumerate(reading)}
    inventory['layout']={'policy':'candidate_ordered_contiguous_columns_v2','reading_order':'top_to_bottom_then_left_to_right',
        'columns':8,'source_strip_bundles':[[n['card'] for n,_ in b] for b in bundles],
        'original_component_minimum_dimensions_preserved':True,'font_size':d['font_size'],'height':d['viewport']['height']}
    c['design']=d;c['atlas_audit']=inventory
    return c
