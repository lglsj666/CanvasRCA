"""Offline, source-bound full-roster qualification; never model inference."""
from collections import Counter, defaultdict
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
from html import escape
import hashlib
import json
import math
import os
import re
import signal
import socket
import tempfile
import time
from unittest.mock import patch
from . import exps, gates
from .utils import (ROOT, ARMS, MODEL, VERSION, config, path, register, runtime, source_contract,
                    read_json, write_json, sha_file, stable_hash, flag, logical_key, phase_arms)
from RQs.RQ3_14.src.tests import DOM


def rejects(fn, types=(ValueError, AssertionError, RuntimeError)):
    try:fn()
    except types:return
    raise AssertionError('Expected explicit failure')


def decode(text):
    # Tagged numeric tokens preserve both JSON type and original numeric spelling.
    return json.loads(text,parse_int=lambda x:('number',x),parse_float=lambda x:('number',x))


def source_record(atom):
    """Parse original bytes independently of the production flatten/pack decoder."""
    kind=atom['kind'];raw=atom['raw'].strip()
    if kind=='assignment':
        region,rest=raw.split(' evidence;',1);row={'region':region}
        parser=json.JSONDecoder(parse_int=lambda x:('number',x),parse_float=lambda x:('number',x))
        while rest.strip(' ;'):
            key,rest=rest.lstrip(' ;').split('=',1)
            if key=='field' or (key=='bins' and not rest.startswith('[')):
                value,sep,rest=rest.partition(';');assert sep
            else:value,n=parser.raw_decode(rest);rest=rest[n:]
            assert key not in row;row[key]=value
        return row
    if kind in {'component','aux'}:
        obj=decode(raw);a,b=atom['container_keys'];assert len(obj[b])==1
        return dict(zip(obj[a],obj[b][0],strict=True))
    if kind=='json':return decode(raw[len(atom['prefix'])+2:] if atom['prefix'] else raw)
    return None


def unpack_record(encoded,schemas):
    schema_id,values=decode(encoded);spec=decode(schemas[schema_id])
    assert len(values)==len(spec['columns'])
    flat={**spec['fixed'],**dict(zip(spec['columns'],values,strict=True))}
    for target,rule in spec['copy'].items():flat[target]=flat[rule['field']][int(rule['index'][1])]
    out={}
    for key,value in flat.items():
        keys=key.split('/');node=out
        for k in keys[:-1]:node=node.setdefault(k.replace('~1','/').replace('~0','~'),{})
        leaf=keys[-1].replace('~1','/').replace('~0','~');assert leaf not in node;node[leaf]=value
    return out


def fidelity(inherited,public):
    assert public['candidates']==inherited['candidates'] and public['payload']==inherited['payload']
    assert public['system']==inherited['system'] and public['facts_hash']==inherited['facts_hash']
    original=inherited['texts']['MARGINAL_FIVE'];org=public['organization'];atoms=org['atoms'];lookup={a['id']:a for a in atoms}
    assert public['texts'][exps.A]==original and len(lookup)==len(atoms)
    reconstructed=[];parsed=0;owners=[]
    for section in org['sections']:
        rows=[lookup[x] for x in section['atoms']]
        if section.get('table_container'):
            header,*records=rows;container=section['table_container'];keys=container['keys'];table=decode(container['raw'])
            assert table[keys[0]]==container['columns'] and len(records)==len(table[keys[1]])
            for atom,row in zip(records,table[keys[1]],strict=True):
                assert source_record(atom)==dict(zip(table[keys[0]],row,strict=True))
            restored=header['raw']+container['raw']
        else:
            offset=0
            for atom in rows:
                assert atom['start']==offset;offset=atom['end']
            restored=''.join(a['raw'] for a in rows)
        assert restored==original[section['part']]['text'];reconstructed.append({'type':'text','text':restored})
    assert reconstructed==original
    for atom in atoms:
        record=source_record(atom)
        if record is None:assert atom['id'] not in org['encoded_rows'];continue
        parsed+=1
        assert record==decode(atom['value_wire'])==unpack_record(org['encoded_rows'][atom['id']],org['record_schemas'])
        if atom['owner'] is not None:
            expected=(record.get('entities') or [record.get('entity')])[0]
            assert atom['owner']==expected;owners.append(expected)
    candidate=json.dumps(public['candidates'],ensure_ascii=False,separators=(',',':'))
    for arm,mapping in org['bindings'].items():
        assert Counter(x['atom'] for x in mapping)==Counter(lookup.keys())
        parts=public['texts'][arm]
        for item in mapping:
            if 'encoded' in item:assert item['encoded'] in parts[item['part']]['text']
        packed=arm in {exps.PV,exps.CT,exps.CV,exps.ROT,exps.ROV}
        if packed:
            schemas=[p['text'].split('Record schema definitions: ',1)[1] for p in parts if 'Record schema definitions: ' in p['text']]
            assert len(schemas)==1 and decode(schemas[0])=={k:decode(v) for k,v in org['record_schemas'].items()}
            declarations=[p['text'] for p in parts if 'Candidate IDs (exhaustive, fixed order): ' in p['text']]
            assert len(declarations)==1 and 'Candidate IDs (exhaustive, fixed order): '+candidate in declarations[0]
            assert declarations[0].count(candidate)==1 and declarations[0].count('@candidate_ids')==2
        if arm in {exps.EV,exps.CT,exps.CV,exps.ROT,exps.ROV}:
            blocks=[p['text'].splitlines()[0][7:] for p in parts if re.match(r'^Entity [0-9]+\n',p['text'])]
            owned=set(a['owner'] for a in atoms if a['owner'] is not None and a['region'] in {'M','R','L'})
            expected=[x for x in public['candidates'] if x in owned]+sorted(owned-set(public['candidates']),key=lambda x:(len(x),x))
            if arm in {exps.ROT,exps.ROV}:mid=len(expected)//2;expected=expected[mid:]+expected[:mid]
            assert blocks==expected
            for block in blocks:
                pi=next(i for i,p in enumerate(parts) if p['text'].startswith('Entity '+block+'\n'))
                ids=[m['atom'] for m in mapping if m['part']==pi]
                want=[a for a in atoms if a['owner']==block and a['region'] in {'M','R','L'}]
                want.sort(key=lambda a:('MRL'.index(a['region']),a['part'],a['start'],int(a['id'][1:])))
                assert ids==[a['id'] for a in want]
    assert public['texts'][exps.TR]==public['texts'][exps.CT] and public['texts'][exps.VR]==public['texts'][exps.CV]
    normal=[x for x in public['texts'][exps.CT] if not x['text'].startswith('Entity ')]
    rotated=[x for x in public['texts'][exps.ROT] if not x['text'].startswith('Entity ')]
    assert normal==rotated
    assert Counter(x['text'] for x in public['texts'][exps.CT])==Counter(x['text'] for x in public['texts'][exps.ROT])
    return {'source_atoms':len(atoms),'structured_records':parsed,'owned_records':len(owners),'original_bytes_restored':True,'numeric_spellings_preserved':True}


def independent_qa(public):
    qa=public['qa'];records={a['id']:source_record(a) for a in public['organization']['atoms']};edges=set()
    # Source table traversal independently of the compiler's question generator.
    for record in records.values():
        if not record:continue
        if set(record)=={'from','to','relation'}:edges.add((record['from'],record['to'],record['relation']))
        if record.get('kind')=='graph':edges.update(tuple(e) for e in record['data'].get('edges',[]) if len(e)==3)
    expected={}
    numeric=lambda v:Decimal(v[1] if isinstance(v,tuple) else v)
    for q in qa['questions']:
        if qa['answers'][q] is None:expected[q]=None;continue
        item=qa['provenance'][q];r=records[item['atom']];entity=r['entities'][0]
        assert len(r['entities'])==1 and r['fact_id']==item['fact']
        family=qa['families'][q];unit=r['unit'] if r['field']=='metric_series_64' else 'microseconds'
        if family=='reading':
            value=r[item['field']];value=value[1] if isinstance(value,tuple) else value
            expected[q]={'entity':entity,'unit':unit,'value':value}
        elif family=='comparison':
            source=r['sircl_met_z'] if r['field']=='metric_series_64' else r
            left,right=map(lambda k:numeric(source[k]),item['keys'])
            expected[q]={'entity':entity,'unit':unit,'higher_phase':'current' if right>left else 'reference' if left>right else 'equal'}
        else:
            incoming=item['direction']=='incoming'
            targets=sorted({a if incoming else b for a,b,k in edges if k==item['relation'] and (b if incoming else a)==entity})
            expected[q]={'entity':entity,'relation':item['relation'],'targets':targets}
    assert expected==qa['answers']
    result=exps.score_qa(qa,json.dumps(expected));assert result['metrics']['qa_accuracy']==1.
    assert exps.score_qa(qa,'not json')['status']=='model_failure'
    for q,value in expected.items():
        if value is None:continue
        altered=deepcopy(expected);altered[q]['entity']='wrong'
        assert sum(not v for v in exps.score_qa(qa,json.dumps(altered))['per_question'].values())==1
    return qa['applicable']


def unit_tests(c):
    from RQs.RQ3_16.src.tests import numeric_regression
    checks=[numeric_regression(c)]
    from . import main
    # Exact lexical roundtrip including typed zero, exponents, strings, nulls and escaped keys.
    source='{"x":-0.00,"y":1e+09,"str":"1e+09","missing":[0,null,1.000],"a/b":{"c~d":"line\\nquote\\\""}}'
    atom={'id':'synthetic','kind':'json','prefix':'','value_wire':source}
    schemas,rows=exps.schemas_for([atom,dict(atom,id='duplicate')])
    assert unpack_record(rows['synthetic'],schemas)==decode(source)
    assert len(rows)==2 and rows['synthetic']==rows['duplicate']
    rejects(lambda:exps.lexload('{"x":1,"x":2}'))
    rejects(lambda:exps.assignment('Metric evidence; field=metric_series_64; new_unknown=1'))
    rejects(lambda:exps.atomize([{'type':'text','text':'{"new_unknown":1}'}]))
    assert exps.lexload(exps.wire(exps.lexload(source)))==exps.lexload(source)
    for arm in ARMS:
        envelope=exps.request_envelope(arm,exps.QA_SYSTEM if arm in exps.QA else 'system')
        assert envelope['effective_server']['max_tokens']==(1024 if arm in exps.QA else 8192)
        if arm not in exps.QA:assert envelope['schema']['json_schema']['schema']['properties']['services']['minItems']==5
    rejects(lambda:main.execute(c,{},exps.A,{},None,None))
    with tempfile.TemporaryDirectory(prefix='rq321-state-') as temp:
        root=Path(temp);key=logical_key('case',exps.RT)
        terminal={'case':'case','arm':exps.RT,'status':'done','call_key':'call'}
        write_json(root/'flags'/(key+'.json'),terminal);assert flag(root,'case',exps.RT) is None
        write_json(root/'completed/call.json',{'status':'complete'});assert flag(root,'case',exps.RT)==terminal
        write_json(root/'flags'/(key+'.json'),{**terminal,'status':'fail','failure_class':'request_timeout'})
        assert flag(root,'case',exps.RT)['failure_class']=='request_timeout'
        write_json(root/'flags'/(key+'.json'),{**terminal,'status':'fail','failure_class':'infrastructure'})
        rejects(lambda:flag(root,'case',exps.RT))
    with patch.object(main.subprocess,'Popen',side_effect=AssertionError('Model startup')),patch.object(socket,'create_connection',side_effect=AssertionError('Network')):
        rejects(lambda:gates.require_qualification(c,True));rejects(lambda:gates.require_qualification(c,False))
        rejects(lambda:main.run(c,True));rejects(lambda:main.supervise(c,True))
    assert gates.paired([0.,0.])['p']==1.
    assert gates.paired([.1,.2,-.3,.4])['p']==.625
    assert 'PACK_TEXT' not in ARMS and 'ENTITY_TEXT' not in ARMS
    checks+=['Independent tagged-number codec oracle; duplicates are distinct records','Unknown JSON/record fields and duplicate keys reject',
      'Fixed-five RCA / independent QA schemas','Historical anchor cannot initiate generation','All GPU and formal gates closed']
    return checks


def inspect_image(public,folder,c):
    from PIL import Image
    evidence,_,ops,design,audit=exps.design_for(public['payload'],c,exps.CV)
    manifest=read_json(folder/'manifest.json');assert manifest['status']=='passed' and not manifest['audit']['issues']
    assert manifest['png_sha256']==sha_file(folder/'dashboard.png') and manifest['html_sha256']==sha_file(folder/'dashboard.html')
    assert read_json(folder/'evidence.json')==evidence and read_json(folder/'design.json')==design
    src=folder.parent/(folder.name+'_design')
    assert read_json(src/'operations.json')==ops and read_json(src/'operations_audit.json')==audit
    with Image.open(folder/'dashboard.png') as im:im.load();assert im.size==(1120,800) and not im.info
    dom=DOM((folder/'dashboard.html').read_text())
    for card in evidence['cards']:
        nodes=[n for n in dom.nodes if n['panel']==card['id']];samples=card['data']['samples']
        bound=[n for n in nodes if n['attrs'].get('data-binding','').startswith(card['id']+'.sample.')]
        circles=[n for n in nodes if n['tag']=='circle']
        assert len(bound)==len(samples) and len(circles)==2*len(samples)
        high=math.log1p(max(1,max(max(s['parent_ms'],s['child_ms']) for s in samples)))
        for i,(n,s) in enumerate(zip(bound,samples,strict=True)):
            assert n['attrs']['data-binding']==f'{card["id"]}.sample.{i}'
            assert float(n['attrs']['data-parent-ms'])==s['parent_ms'] and float(n['attrs']['data-child-ms'])==s['child_ms']
            for j,field in enumerate(('parent_ms','child_ms')):
                p=circles[2*i+j]['attrs'];expected=100+240*math.log1p(s[field])/high
                assert math.isclose(float(p['cx']),expected,abs_tol=1e-9)
                assert float(p['cy'])==(52 if s['phase']=='reference' else 82)+156*j
    return len(manifest['audit']['bindings'])


def historical_anchors(c):
    """Evaluator-only audit, outside compilation. No selection based on old scores."""
    from unified_scripts.vllm_inference import VLLMInferenceConfig
    from RQs.RQ3_16.src.utils import flag as old_flag
    from RQs.RQ3_1.src.main import audit_completion_artifacts,score_response_callback
    root=path(c['historical_anchor']);refs={};recipe=runtime(c)[1]
    for row in register(c)['cases']:
        oid=row['opaque_incident_id'];old=old_flag(root,oid,c['historical_anchor_arm']);assert old and old['status']=='done'
        key=old['call_key'];audit_completion_artifacts(root,key)
        public=read_json(path(c['preparation'])/'public'/(oid+'.json'));image=public['images'].get(exps.A)
        parts=exps.parts_for(public,exps.A,(path(c['preparation'])/image['path']).read_bytes() if image else None)
        expected=[{'type':'image','sha256':hashlib.sha256(p['png']).hexdigest()} if p['type']=='image' else p for p in parts]
        inputs=read_json(root/'inputs'/(key+'.json'));prompt=read_json(root/'prompts'/(key+'.json'));out=read_json(root/'outputs'/(key+'.json'))
        assert inputs['parts']==expected
        envelope=exps.request_envelope(exps.A,public['system'])
        assert prompt['system']==public['system'] and prompt['schema']==envelope['schema']
        strip=lambda v:{k:x for k,x in v.items() if k not in {'config_source','config_hash'}}
        assert strip(prompt['effective_server'])==strip(envelope['effective_server'])
        old_config=VLLMInferenceConfig.load(Path(prompt['effective_server']['config_source']))
        assert stable_hash(old_config.data)==prompt['effective_server']['config_hash']
        assert old_config.model(MODEL)==recipe
        private=read_json(path(c['preparation'])/'private'/(oid+'.json'))
        assert score_response_callback(private,public['candidates'])(out['response'])==out['score']
        assert out['score'].get('metrics',out['score'])==old['metrics']
        cost=read_json(root/'cost'/(key+'.json'));assert cost['total_tokens']==cost['input_tokens']+cost['output_tokens']
        refs[oid]={**old,'arm':exps.A,'logical_key':logical_key(oid,exps.A),'source_root':str(root.relative_to(ROOT)),
          'source_arm':c['historical_anchor_arm'],'source_commit_sha256':sha_file(root/'completed'/(key+'.json')),
          'historical_reference':True,'no_op':True,'new_calls':0,'reference_kind':'audited_cross_round',
          'request_input_sha256':sha_file(root/'inputs'/(key+'.json'))}
    report={'status':'passed','source_contract':source_contract(),'cases':len(refs),'references':refs,'new_calls':0,
            'checks':['exact model-visible input and PNG','system, schema, effective recipe','canonical scoring replay','all committed artifact hashes and usage']}
    write_json(path(c['results'])/'qualification/historical_anchor_audit.json',report)
    return {'cases':len(refs),'status':'passed','new_calls':0}


def lifecycle(c):
    """Real durable transactions/writers/scorer with the provider boundary offline."""
    from . import main
    from vlmrca.run_state import DurableCallRegister
    from vlmrca.vlm import client
    reg=register(c);chosen=[]
    for row in reg['cases']:
        public=read_json(path(c['preparation'])/'public'/(row['opaque_incident_id']+'.json'));applicable=bool(public['images'])
        if not any(x[2]==applicable for x in chosen):chosen.append((row,public,applicable))
        if len(chosen)==2:break
    assert len(chosen)==2
    with tempfile.TemporaryDirectory(prefix='offline-',dir=path(c['results'])) as temp:
        root=Path(temp);future={**c,'results':str(root.relative_to(ROOT)),'concurrency':2}
        write_json(root/'qualification/historical_anchor_audit.json',read_json(path(c['results'])/'qualification/historical_anchor_audit.json'))
        fake={**reg,'cases':[x[0] for x in chosen],'smoke':[x[0] for x in chosen],'qa_cases':[x[0]['opaque_incident_id'] for x in chosen]}
        seen=[];stopped=False
        def arms(c,smoke=False,row=None):return ARMS
        def provider(parts,cfg,system,**kwargs):
            nonlocal stopped
            key=kwargs['partial_metadata']['call_key'];identity=main.CALL_IDENTITIES[key];seen.append(dict(identity))
            pub=next(p for r,p,a in chosen if r['opaque_incident_id']==identity['case']);qa=identity['arm'] in exps.QA
            assert cfg.max_tokens==(1024 if qa else 8192)
            response=json.dumps(pub['qa']['answers'] if qa else {'services':pub['candidates'][:5],'reason':'offline fixture','confidence':'medium'})
            if not stopped:stopped=True;os.kill(os.getpid(),signal.SIGUSR1)
            return client.VLMResponse(response,input_tokens=1000,output_tokens=12,latency_s=.01,model_tag=MODEL,raw={'finish_reason':'stop'})
        fail=AssertionError('CPU test attempted network or service startup')
        with patch.object(main,'register',return_value=fake),patch.object(gates,'register',return_value=fake),\
             patch.object(main,'phase_arms',side_effect=arms),patch.object(gates,'phase_arms',side_effect=arms),\
             patch.object(main,'runtime'),patch.object(gates,'require_qualification'),patch.object(gates,'require_runtime_attestation'),\
             patch.object(client,'call_vlm',side_effect=provider),patch.object(client,'count_vllm_prompt_tokens',return_value=1000),\
             patch.object(socket,'create_connection',side_effect=fail),patch.object(main.subprocess,'Popen',side_effect=fail):
            first=main.run(future);assert first['status']=='incomplete'
            result=main.run(future);assert result['status']=='complete'
            assert len(seen)==len({x['call_key'] for x in seen}) and not any(x['arm']==exps.A for x in seen)
            for row,p,applicable in chosen:
                oid=row['opaque_incident_id']
                for left,right in ((exps.TR,exps.CT),(exps.VR,exps.CV)):
                    a,b=(flag(root/'formal',oid,arm) for arm in (left,right))
                    assert a['request_hash']==b['request_hash'] and a['call_key']!=b['call_key']
                if not applicable:assert flag(root/'formal',oid,exps.RV)['call_key']==flag(root/'formal',oid,exps.RT)['call_key']
                assert flag(root/'formal',oid,exps.A)['historical_reference']
            assert main.run(future)['resumed_complete_phase'] and main.supervise(future)['launched_model'] is False
            saved=seen[0];(root/'formal/completed'/(saved['call_key']+'.json')).unlink();assert flag(root/'formal',saved['case'],saved['arm']) is None
            (root/'formal'/('phase_complete.'+MODEL+'.json')).unlink()
            before=len(seen);assert main.run(future)['status']=='complete' and len(seen)==before
            assert flag(root/'formal',saved['case'],saved['arm']) is not None
            summary=gates.analyze(future)
            assert {k:len(v) for k,v in summary['families'].items()}=={'primary_method':2,'visual_representation':2,'conditional_ablation':2,'mechanism':4}
        calls=DurableCallRegister(root/'recovery.sqlite',scope='offline',limit=2)
        n,_=calls.begin('x','request','solver');rejects(lambda:calls.begin('x','request','solver'))
        assert calls.recover_persisted(root,audit=lambda *_:None)['interrupted_spent_calls']==[n]
        n,_=calls.begin('x','request','solver',retry=True);calls.finish(n,{'ok':True});rejects(lambda:calls.begin('z','request','solver'))
        count=len(seen)
    return {'status':'passed','offline_provider_calls':count,'model_calls':0,'actual_transaction_writer_scorer':True,
      'safe_drain_resume':True,'atomic_boundary':True,'cached_response_finishes_missing_commit_without_new_generation':True,
      'independent_repeats':True,'budget_persists':True,'historical_no_generation':True,'analysis_families':True}


def source_oracle(c):
    from RQs.RQ3_15.src.utils import public_source
    from RQs.RQ3_15.src.tests import oracle
    from RQs.RQ3_15.src.exps import extract
    rows=[]
    for row in register(c)['smoke']:
        oid=row['opaque_incident_id'];public=read_json(path(c['base_preparation'])/'public'/(oid+'.json'))
        inherited_source_config=read_json(path('RQs/RQ3_15/configs/request_joint_v1.json'))
        frame,mapping,ops,clock,scale,audit=public_source({**inherited_source_config,**c},row,public)
        old=read_json(path('RQs/RQ3_15/preparation/request_joint_v1')/'audit'/(oid+'.json'))
        count=oracle(public['payload'],old['compiler'],frame,scale,c)
        rebuilt,_=extract(frame,mapping,ops,clock,scale,c);assert rebuilt==public['payload']
        rows.append({'case':oid,'dataset':row['dataset'],'population_pairs_checked':count,
                     'source_hashes':audit['source_hashes'],'scale_to_ms':scale,'phase_clock':clock})
    return rows


def render_boundary(c):
    from RQs.RQ3_15.src.tests import fixture
    from RQs.RQ3_15.src.exps import extract
    from .main import render_arm
    frame=fixture();frame.loc[:1,'duration_ms']=0
    packet,_=extract(frame,{'a':'123','b':'456'},{'parent':'parent','child':'child'},
                     {'origin':-24.,'split':24.,'duration':48.},.001,c)
    assert len(packet['relations'])==1 and [0.,0.] in packet['relations'][0]['phases']['reference']['points']
    target=path(c['results'])/'qualification/synthetic_single_zero'
    if not (target/'manifest.json').exists():render_arm(packet,c,exps.CV,target)
    count=inspect_image({'payload':packet},target,c)
    return {'kind':'synthetic single relation and observed zero','path':str(target.relative_to(ROOT)),
            'png_sha256':sha_file(target/'dashboard.png'),'bindings':count}


def examples(c):
    root=path(c['preparation']);reg=register(c)
    publics={r['opaque_incident_id']:read_json(root/'public'/(r['opaque_incident_id']+'.json')) for r in reg['cases']}
    selected=defaultdict(list)
    for r in reg['smoke']:selected[r['opaque_incident_id']].append('fixed '+r['dataset'])
    valid=[oid for oid,p in publics.items() if p['images']]
    selected[max(valid,key=lambda oid:max(len(r['parent_operation'])+len(r['child_operation']) for r in publics[oid]['payload']['relations']))].append('long operation')
    selected[max(valid,key=lambda oid:max(v for r in publics[oid]['payload']['relations'] for ph in r['phases'].values() for xy in ph['points'] for v in xy))].append('extreme')
    selected[min(valid,key=lambda oid:sum(ph['n'] for r in publics[oid]['payload']['relations'] for ph in r['phases'].values()))].append('sparse')
    single=sorted(oid for oid in valid if len(publics[oid]['payload']['relations'])==1)
    if single:selected[single[0]].append('single relation')
    fallback=sorted(set(publics)-set(valid))
    if fallback:selected[fallback[0]].append('full text fallback')
    out=root/'examples';out.mkdir(exist_ok=True);index=[];html=['<!doctype html><meta charset="utf-8"><title>RQ3.21 actual inputs</title><h1>RQ3.21 input examples</h1>']
    for oid,why in selected.items():
        public=publics[oid];html.append(f'<h2>{escape(oid)} — {escape(", ".join(why))}</h2>')
        for arm in ARMS:
            entry=public['images'].get(arm);image=os.path.relpath(root/entry['path'],out) if entry else None;name=oid+'__'+arm+'.txt'
            guide=exps.VISUAL_GUIDE+'\n\n' if entry and arm!=exps.A else ''
            (out/name).write_text(exps.system_for(public,arm)+'\n\n'+guide+'\n\n'.join(x['text'] for x in public['texts'][arm]))
            html.append(f'<h3>{arm}</h3><a href="{name}">Actual text</a>')
            if image:html.append(f'<p><a href="{image}"><img src="{image}" width="1120"></a></p>')
            index.append({'case':oid,'arm':arm,'selection':why,'image':image,'text':name,'historical_reference':arm==exps.A})
    (out/'index.html').write_text('\n'.join(html));write_json(out/'index.json',index)
    return {'status':'written','examples':len(index),'index':str(out/'index.html'),'cases':dict(selected)}


def cpu(c,smoke=False):
    if smoke:raise ValueError('Complete220 required')
    from RQs.RQ3_3.src.utils import OfflineTokens
    from RQs.RQ3_12.src.tests import checkpoint_audit
    from .main import render_arm
    started=time.monotonic();current=source_contract();q=path(c['results'])/'qualification';root=path(c['preparation'])
    assert read_json(q/'static.json')['source_contract']==current;gates.require_renderer_build()
    preparation=read_json(q/'preparation.json')
    assert preparation['status']=='complete' and preparation['cases']==220
    loaded,spec=runtime(c);assert spec['max_model_len']==40960 and spec['gpu_memory_utilization']==.75
    checks=unit_tests(c);tokens=OfflineTokens({'unified':{'vllm':str(loaded.source)},'models':[MODEL]})
    reg=register(c);inventory=[];cases=[];bindings=0;fixed={r['opaque_incident_id'] for r in reg['smoke']};redraws=[];aliases=0
    for row in reg['cases']:
        if time.monotonic()-started>c['cpu_seconds']:raise TimeoutError('CPU qualification budget')
        oid=row['opaque_incident_id'];inherited=read_json(path(c['base_preparation'])/'public'/(oid+'.json'));public=read_json(root/'public'/(oid+'.json'));marker=read_json(root/'flags'/(oid+'.json'))
        for field in ('public','private'):assert sha_file(root/field/(oid+'.json'))==marker[field+'_sha256']
        assert marker['parent_public_sha256']==sha_file(path(c['base_preparation'])/'public'/(oid+'.json'))
        rebuilt=exps.compile_public(inherited,c)
        assert {k:v for k,v in public.items() if k!='images'}=={k:v for k,v in rebuilt.items() if k!='images'}
        injected=deepcopy(inherited);injected['ground_truth']='forbidden';injected['anomal']=True;assert exps.compile_public(injected,c)==rebuilt
        fact_report=fidelity(inherited,public);qa_n=independent_qa(public);png=None
        if public['images']:
            image=root/public['images'][exps.CV]['path'];png=image.read_bytes();assert sha_file(image)==public['images'][exps.CV]['sha256']
            assert all(v==public['images'][exps.CV] for v in public['images'].values());bindings+=inspect_image(public,image.parent,c)
            if oid in fixed:
                target=q/'redraws'/oid
                if not (target/'manifest.json').exists():render_arm(public['payload'],c,exps.CV,target)
                assert sha_file(target/'dashboard.png')==sha_file(image)
                redraws.append({'case':oid,'png_sha256':sha_file(image),'byte_identical':True})
        formal=phase_arms(c,False,row);arms=set(formal)|set(phase_arms(c,True,row) if oid in fixed else ());counts={}
        for arm in ARMS:
            if arm not in arms:continue
            parts=exps.parts_for(public,arm,png if arm in public['images'] else None);system=exps.system_for(public,arm)
            count=tokens.count(parts,system,MODEL);output=1024 if arm in exps.QA else 8192
            assert count+output<=40960,(oid,arm,count);counts[arm]=count
            schema=exps.request_envelope(arm,system)['schema'];request_id=stable_hash([system,schema,[(p['type'],p.get('text',hashlib.sha256(p.get('png',b'')).hexdigest())) for p in parts],output])
            inventory.append({'case':oid,'dataset':row['dataset'],'arm':arm,'scope':'formal' if arm in formal else 'smoke_only',
              'input_tokens':count,'output_limit':output,'system_sha256':stable_hash(system),'png_sha256':public['images'].get(arm,{}).get('sha256'),
              'text_hash':stable_hash(public['texts'][arm]),'request_hash':request_id,'request_family':'qa' if arm in exps.QA else 'rca',
              'historical_reference':arm==exps.A,'canonical_arm':public['canonical_arms'][arm]})
        local={r['arm']:r for r in inventory if r['case']==oid}
        for arm in formal:
            canonical=public['canonical_arms'][arm]
            if arm!=canonical:
                assert local[arm]['request_hash']==local[canonical]['request_hash'];aliases+=1
        if oid in reg['qa_cases']:
            for a,b in ((exps.TR,exps.CT),(exps.VR,exps.CV)):assert local[a]['request_hash']==local[b]['request_hash'] and logical_key(oid,a)!=logical_key(oid,b)
        cases.append({'case':oid,'dataset':row['dataset'],'applicable':bool(public['images']),'inputs':counts,'qa_applicable_questions':qa_n,**fact_report})
        if len(cases)%20==0:print(json.dumps({'event':'cpu_progress','cases':len(cases),'seconds':time.monotonic()-started}),flush=True)
    ratios={};errors=[]
    for dataset in c['case_counts']:
        subset=[r for r in cases if r['dataset']==dataset]
        ratios[dataset]={a:sum(r['inputs'][exps.CV] for r in subset)/sum(r['inputs'][a] for r in subset) for a in (exps.A,exps.RT)}
        if any(v>c['readiness']['max_mean_input_ratio'] for v in ratios[dataset].values()):errors.append('input_budget:'+dataset)
    report={'status':'failed' if errors else 'passed','source_contract':current,'cases':cases,'input_ratios':ratios,'maximum_input':max(x['input_tokens'] for x in inventory),
      'core_positions':sum(x['scope']=='formal' for x in inventory),'new_formal_positions':sum(x['scope']=='formal' and not x['historical_reference'] for x in inventory),
      'exact_current_references':aliases,'qa_cases':len(reg['qa_cases']),'checks':checks,'bindings':bindings,'deterministic_redraws':redraws,
      'errors':errors,'model_calls':0,'seconds':time.monotonic()-started}
    write_json(q/'input_inventory.json',inventory);write_json(q/'cpu_feasibility.json',report)
    if errors:raise RuntimeError('Scientific budget failed: '+str(errors))
    assert report['core_positions']==c['formal_positions'] and report['new_formal_positions']==c['formal_new_call_positions']
    report['source_oracle']=source_oracle(c);report['synthetic_render']=render_boundary(c)
    report['historical_anchor_audit']=historical_anchors(c);report['lifecycle']=lifecycle(c)
    report['checkpoint_audit']=checkpoint_audit(loaded)
    assert source_contract()==current;report['seconds']=time.monotonic()-started;write_json(q/'cpu.json',report);examples(c)
    return {k:v for k,v in report.items() if k not in {'source_contract','cases','checkpoint_audit'}}
