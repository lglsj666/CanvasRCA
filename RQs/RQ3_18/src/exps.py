"""Pure public population-readout compiler; no filesystem or evaluator access."""
from copy import deepcopy
import json
import math
import re
from .utils import ARMS, MODEL, VERSION, stable_hash
from RQs.RQ3_15.src import exps as pairs

T,F,S,FS,P,FP,K,FK,TR,FR,R=ARMS
VISUAL={S,FS,P,FP,K,FK,R}
REPEATS={TR,FR,R}
FOCUSED={F,FS,FP,FK,FR,R}
FIVE=set(ARMS)
NEUTRAL_EDITS=(
    ('isolated nodes are not displayed.','unlisted isolated nodes are not included in this ledger.'),
    ('Joint and marginal graphs repeat these samples on the same log1p(ms) scale.',
     'These are exact observed millisecond values; the selected sample list is not a density estimate.'))
VISUAL_GUIDE=(
    'Image decoding: panels repeat supplied public text facts. Parent/Child and operation names identify the recorded calls. '
    'All span durations are inclusive milliseconds, not exclusive execution or waiting time. Reference is lavender and Current is teal. '
    'Sample panels show at most32 real paired observations per phase, selected by parent-duration ranks; points are not population density or temporal order. '
    'Population panels compare parent p50, parent p95, child p50, child p95 from all eligible requests. '
    'Each numeric endpoint belongs to its named phase and statistic; comparison segments do not depict a trajectory or causal propagation. '
    'Horizontal positions use log1p(duration_ms), ticks are milliseconds; coordinates share a range within each relation. '
    'Population and sampled counts are distinct. No additional incident evidence is supplied by the image.')


def schema_for(arm,base):
    if arm not in ARMS: raise ValueError('Unknown population-readout arm')
    schema=deepcopy(base);items=schema['json_schema']['schema']['properties']['services']
    if items['minItems']!=1 or items['maxItems']!=5: raise ValueError('Inherited schema drift')
    items['minItems']=5
    return schema


def request_envelope(arm,system):
    from RQs.RQ3_1.src.main import _request_envelope
    value=_request_envelope(MODEL,system=system)
    value['schema']=schema_for(arm,value['schema']);value['policy_version']=VERSION
    return value


def keys(value,expected):
    if not isinstance(value,dict) or set(value)!=set(expected): raise ValueError('Public packet whitelist mismatch')


def finite(v,integer=False):
    if type(v) not in ((int,) if integer else (int,float)) or not math.isfinite(v) or v<0:
        raise ValueError('Nonnegative public numeric value required')


def validate_pairs(packet):
    keys(packet,('schema','clock','relations'));keys(packet['clock'],('duration','split'))
    if packet['schema']!='RequestPairPacketV1' or not isinstance(packet['relations'],list) or len(packet['relations'])>2:
        raise ValueError('Frozen pair schema/capacity changed')
    for v in packet['clock'].values():finite(v)
    if packet['clock']['split']>packet['clock']['duration']:raise ValueError('Invalid public phase clock')
    identities=set()
    for r in packet['relations']:
        keys(r,('id','parent','child','parent_operation','child_operation','unit','thresholds','phases'))
        if r['id'] in identities or not re.fullmatch(r'PAIR0[12]',r['id']):raise ValueError('Duplicate/unknown relation')
        identities.add(r['id'])
        if any(not isinstance(r[k],str) or not re.fullmatch(r'\d{3,6}',r[k]) for k in ('parent','child')):
            raise ValueError('Expected public entity identity')
        if r['parent']==r['child'] or r['unit']!='ms':raise ValueError('Pair direction/unit changed')
        for k in ('parent_operation','child_operation'):
            if not isinstance(r[k],str) or not 1<=len(r[k])<=10000:raise ValueError('Invalid operation label')
        if not isinstance(r['thresholds'],list) or len(r['thresholds'])!=2:raise ValueError('Threshold dimensions')
        for v in r['thresholds']:finite(v)
        keys(r['phases'],('reference','current'))
        for phase in ('reference','current'):
            v=r['phases'][phase];keys(v,('n','binary','quantiles','conditional_child','points'));finite(v['n'],True)
            if v['n']<20 or len(v['binary'])!=4:raise ValueError('Insufficient population support')
            for count in v['binary']:finite(count,True)
            if sum(v['binary'])!=v['n']:raise ValueError('Joint count mismatch')
            if len(v['quantiles'])!=2:raise ValueError('Population quantile dimensions')
            for endpoint in v['quantiles']:
                if len(endpoint)!=2:raise ValueError('Expected p50 and p95')
                for q in endpoint:finite(q)
                if endpoint[0]>endpoint[1]:raise ValueError('p50 exceeds p95')
            if len(v['points'])!=min(v['n'],32):raise ValueError('Rank sample count mismatch')
            for xy in v['points']:
                if not isinstance(xy,list) or len(xy)!=2:raise ValueError('Invalid pair')
                for q in xy:finite(q)
            for row in v['conditional_child']:
                if not isinstance(row,list) or len(row)!=4:raise ValueError('Conditional fields')
                if type(row[0])!=int or row[0] not in (0,1):raise ValueError('Conditional group')
                finite(row[1],True)
                for q in row[2:]:finite(q)
                if not 5<=row[1]<=v['n'] or row[2]>row[3]:raise ValueError('Conditional support/quantiles')


def readout_packet(payload,base_hash):
    validate_pairs(payload);relations=[]
    for index,r in enumerate(payload['relations']):
        data={k:r[k] for k in ('parent','child','parent_operation','child_operation')}
        data.update(duration_type='inclusive',support=[r['phases'][s]['n'] for s in ('reference','current')],
                    sampled=[len(r['phases'][s]['points']) for s in ('reference','current')],
                    quantiles=[[r['phases'][s]['quantiles'][endpoint][q] for s in ('reference','current')]
                               for endpoint in (0,1) for q in (0,1)])
        sources={}
        prefix=f'relations.{index}'
        for k in ('parent','child','parent_operation','child_operation'):sources[k]=prefix+'.'+k
        for j,phase in enumerate(('reference','current')):
            sources[f'support.{j}']=prefix+f'.phases.{phase}.n'
            sources[f'sampled.{j}']='len('+prefix+f'.phases.{phase}.points)'
            for endpoint in (0,1):
                for q in (0,1):sources[f'quantiles.{2*endpoint+q}.{j}']=prefix+f'.phases.{phase}.quantiles.{endpoint}.{q}'
        sources['duration_type']='RequestPairPacketV1.GUIDE:inclusive'
        relations.append({'id':r['id'],'unit':r['unit'],'data':data,'sources':sources})
    return {'schema':'PopulationReadoutPacketV1','base_facts_hash':base_hash,'pair_packet_hash':stable_hash(payload),'relations':relations}


def focus_text(packet):
    lines=['Repeated named population readout; all figures below already appear in the complete evidence. Inclusive span durations, milliseconds.']
    for r in packet['relations']:
        d=r['data'];lines.append(f"{r['id']}: parent={d['parent']}, operation={d['parent_operation']}; child={d['child']}, operation={d['child_operation']}.")
        lines.append(f"Reference/current population n={d['support'][0]}/{d['support'][1]}; text sample n={d['sampled'][0]}/{d['sampled'][1]}.")
        for label,values in zip(('parent p50','parent p95','child p50','child p95'),d['quantiles']):
            lines.append(f'{label}: reference={values[0]!r} ms; current={values[1]!r} ms (population, inclusive).')
    return '\n'.join(lines)


def base_text(inherited):
    parts=deepcopy(inherited['texts']['PAIR_FIVE'])
    for part in parts:
        for old,new in NEUTRAL_EDITS:part['text']=part['text'].replace(old,new)
    return parts


def compile_public(inherited,c):
    payload=deepcopy(inherited['payload']);packet=readout_packet(payload,inherited['base_facts_hash'])
    if len(inherited['candidates'])<5:raise ValueError('Five candidates required')
    base=base_text(inherited);applicable=bool(payload['relations'])
    texts={a:pairs.append(base,focus_text(packet)) if applicable and a in FOCUSED else deepcopy(base) for a in ARMS}
    public={'system':inherited['system'],'candidates':deepcopy(inherited['candidates']),'texts':texts,'images':{},
            'payload':payload,'readout':packet,'facts_hash':inherited['facts_hash'],'base_facts_hash':inherited['base_facts_hash'],
            'canonical_arms':{a:a if applicable or a in REPEATS else T for a in ARMS},'infeasible':{},'output_adapter':c['output_adapter']['version']}
    visible_audit(public);return public


def design_for(packet,c,arm):
    if arm not in {P,FP,K,FK,R}:raise ValueError('Only population-profile rendering here; sample PNG inherited verbatim')
    from renderer.operations import apply_operations
    evidence={'schema':'CanvasEvidenceV1','cards':[{'id':r['id'],'kind':'trace_profile','title':'Population duration comparison',
        'entity':None,'unit':'ms','data':deepcopy(r['data'])} for r in packet['relations']]}
    if not evidence['cards']:raise ValueError('Text-only fallback cannot render an empty panel')
    cv=c['canvas'];panels=[{'id':'p_'+r['id'],'type':'panel','card':r['id'],'component':'trace_profile.quantiles'} for r in packet['relations']]
    base={'schema':'DashboardDesignV1','viewport':{'width':cv['width'],'height':cv['height']},'theme':'light','font_size':cv['font_size'],
          'gap':cv['gap'],'padding':cv['padding'],'scale':1,'tree':{'id':'population','type':'grid','columns':len(panels),'children':panels},
          'bindings':[],'indexing':{'visible':False,'start':1}}
    if arm in {K,FK}:base['presentation']={r['id']:{'marks':False,'details':True} for r in packet['relations']}
    operations=[{'op':'appearance','args':{'theme':'dark','font_size':cv['font_size']}},
                {'op':'spacing','args':{'gap':cv['gap'],'padding':cv['padding']}}]
    design,audit=apply_operations(evidence,base,operations)
    return evidence,base,operations,design,audit


def parts_for(public,arm,png=None):
    if arm not in ARMS:raise ValueError('Unknown arm')
    parts=deepcopy(public['texts'][arm])
    if arm in VISUAL and public['payload']['relations']:
        if not isinstance(png,bytes) or not png.startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('Committed PNG required')
        return [{'type':'image','png':png},{'type':'text','text':VISUAL_GUIDE}]+parts
    if png is not None:raise ValueError('Text/fallback cannot receive an image')
    return parts


def visible_audit(public):
    validate_pairs(public['payload'])
    assert public['readout']==readout_packet(public['payload'],public['base_facts_hash'])
    visible=json.dumps({k:public[k] for k in ('system','texts','payload','readout')},ensure_ascii=False)
    if re.search(r'(?i)(INC-[A-F0-9]{8}|aiops202[25]|aegislab|ground_truth|injection_time|/home/|trace_id|span_id|anomal\s*":)',visible):
        raise ValueError('Private/source identity in public input')
    for a in ARMS:
        assert public['texts'][a]==public['texts'][F if a in FOCUSED else T]
        assert all(p['type']=='text' and not re.search(r'(?i)\b(image|dashboard|canvas|pixel|chart)\b',p['text']) for p in public['texts'][a])
        if a in REPEATS:assert public['canonical_arms'][a]==a
    if public['payload']['relations']:
        focus=public['texts'][F];assert focus[:-2]+focus[-1:]==public['texts'][T]
        assert focus[-2]['text']==focus_text(public['readout'])
    else:assert all(public['texts'][a]==public['texts'][T] for a in ARMS)
    return {'status':'passed','full_facts_retained':True,'population_not_resampled':True}
