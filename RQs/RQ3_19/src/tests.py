"""CPU-only full-roster fidelity, QA oracle, real renderer and lifecycle qualification."""
from collections import defaultdict,Counter
from copy import deepcopy
from pathlib import Path
from html import escape
import json
import math
import os
import re
import signal
import tempfile
import time
from unittest.mock import patch
from . import exps,gates
from .utils import (ROOT,ARMS,MODEL,VERSION,METRICS,path,config,register,runtime,source_contract,
                    read_json,write_json,sha_file,stable_hash,flag,logical_key,phase_arms)
from RQs.RQ3_14.src.tests import DOM


def rejects(fn,types=(ValueError,AssertionError,RuntimeError)):
    try:fn()
    except types:return
    raise AssertionError('Expected explicit rejection')


def restore_transfer(text,inventory):
    """Independent recursive replacement oracle from source-bound fields."""
    lookup={v['token']:v['value'] for v in inventory}
    def restore(v):
        if isinstance(v,list):return [restore(x) for x in v]
        if isinstance(v,dict):return {k:restore(x) for k,x in v.items()}
        return lookup.get(v,v) if isinstance(v,str) else v
    result=[]
    for line in text.splitlines():
        parsed=exps.json_line(line)
        if parsed:
            prefix,value=parsed;result.append(prefix+exps.dumps(restore(value)))
        else:
            for token,value in sorted(lookup.items(),key=lambda x:-len(x[0])):
                line=line.replace(repr(token),repr(value)).replace(token,str(value))
            result.append(line)
    return '\n'.join(result)


def independent_qa(public):
    """Recompute each answer using independent indexing and public graph traversal."""
    qa=public['qa']
    if qa is None:return None
    rel=public['payload']['relations'][0];ph=rel['phases']
    relation=[]
    for part in public['texts'][exps.F]:
        for line in part['text'].splitlines():
            if not line.startswith('{'):continue
            try:obj=json.loads(line)
            except ValueError:continue
            if 'columns' not in obj or 'rows' not in obj:continue
            cols=obj['columns']
            if 'data' not in cols or 'id' not in cols:continue
            for row in obj['rows']:
                edges=row[cols.index('data')].get('edges',[])
                relation.extend((row[cols.index('id')],edge) for edge in edges if len(edge)==3 and edge[2]=='calls')
    assert relation
    sign=lambda left,right:('less','equal','greater')[(left>right)-(left<right)+1]
    expected={'q1':ph['reference']['n'],'q2':{'unit':rel['unit'],'duration_type':'inclusive'},
      'q3':{'entity':rel['child'],'operation':rel['child_operation']},
      'q4':dict(zip(('source','target','relation'),relation[0][1])),
      'q5':sign(ph['current']['quantiles'][0][0],ph['reference']['quantiles'][0][0]),
      'q6':sign(ph['reference']['quantiles'][0][1],ph['reference']['quantiles'][1][1])}
    assert qa['answers']==expected
    assert sorted(qa['bound_readout'].splitlines()[1:])==sorted(qa['source_readout'].splitlines()[1:])
    assert qa['bound_readout']!=qa['source_readout'] and len(qa['sources'])==6
    assert exps.score_qa(qa,json.dumps(expected))['metrics']['qa_accuracy']==1.
    for unit in ('ms','MS','millisecond',' milliseconds '):
        equivalent=deepcopy(expected);equivalent['q2']={'unit':unit,'duration_type':' Inclusive '}
        assert exps.score_qa(qa,json.dumps(equivalent))['metrics']['qa_accuracy']==1.
    for unit,kind in (('seconds','inclusive'),('ms','exclusive')):
        wrong=deepcopy(expected);wrong['q2']={'unit':unit,'duration_type':kind}
        assert exps.score_qa(qa,json.dumps(wrong))['per_question']==[True,False,True,True,True,True]
    for field in ('q1','q2','q3','q4','q5','q6'):
        wrong=deepcopy(expected)
        if field=='q1':wrong[field]+=1
        elif field in ('q5','q6'):wrong[field]='equal' if wrong[field]!='equal' else 'less'
        else:wrong[field][next(iter(wrong[field]))]='unbound'
        assert exps.score_qa(qa,json.dumps(wrong))['per_question'].count(False)==1
    assert exps.score_qa(qa,'{}')['status']=='model_failure'
    assert exps.score_qa(qa,'not json')['metrics']['qa_accuracy']==0.
    return expected


def fidelity(inherited,public):
    assert public['payload']==inherited['payload'] and public['candidates']==inherited['candidates']
    assert public['texts'][exps.F]==inherited['texts']['READOUT_TEXT']
    compact=public['texts'][exps.C];visual=public['texts'][exps.V]
    assert compact[1]['text']==exps.COMPACT_GUIDE
    for original,new in zip(public['texts'][exps.F],compact[:1]+compact[2:]):
        assert exps.semantic_lines(original['text'])==exps.semantic_lines(new['text'])
    assert len(compact)==len(visual)
    for c,v in zip(compact,visual):
        if v['text'].startswith(exps.TRANSFER_PAIR_HEADER):
            original=json.loads(c['text'].rsplit('\n',1)[1]);encoded=json.loads(v['text'].rsplit('\n',1)[1]);restored=[]
            for rid,thresholds,phases in encoded:
                r=next(r for r in public['payload']['relations'] if r['id']==rid)
                restored.append([rid,r['parent'],r['parent_operation'],r['child'],r['child_operation'],thresholds,
                    [[phase,r['phases'][phase]['n'],counts] for phase,counts in phases]])
            assert original==restored
            continue
        if v['text'].startswith('Named population readout;'):
            # Read the retained quantile lines independently; the omitted categorical
            # fields are exhaustively bound to actual visible DOM in inspect_image.
            old=c['text'].splitlines();new=restore_transfer(v['text'],public['transfer']).splitlines()
            assert [x for x in old if re.match(r'(parent|child) p(50|95):',x)]==[x for x in new if re.match(r'(parent|child) p(50|95):',x)]
            original_samples=[re.search(r'text sample n=(.*)',x).group(1) for x in old if 'text sample n=' in x]
            retained_samples=[re.search(r'text sample n=(.*)',x).group(1) for x in new if 'text sample n=' in x]
            assert original_samples==retained_samples
            assert [x.split(':')[0] for x in old if x.startswith('PAIR')]==[x.split(':')[0] for x in new if x.startswith('PAIR')]
            continue
        restored=restore_transfer(v['text'],public['transfer'])
        assert exps.semantic_lines(c['text'])==exps.semantic_lines(restored),'Delegated field does not restore full source'
    for fact in public['transfer']:
        value=public['payload']
        for key in fact['source'].split('.'):
            value=value[int(key)] if isinstance(value,list) else value[key]
        assert value==fact['value']
    assert public['texts'][exps.A]==compact==public['texts'][exps.CR]
    assert public['texts'][exps.VR]==visual
    return {'facts_equal':True,'source_fields_transferred':len(public['transfer']),
      'body_transfer_count':public['body_transfer_count'],'full_text_exact':True}


def inspect_image(public,folder,c):
    from RQs.RQ3_18.src.tests import inspect_profile
    n=inspect_profile(folder,public['readout'],c,exps.previous.P,source_contract())
    dom=DOM((folder/'dashboard.html').read_text())
    bindings={x['attrs']['data-binding']:x for x in dom.nodes if 'data-binding' in x['attrs']}
    for f in public['transfer']:
        node=bindings[f['binding']]
        if '.quantiles.' in f['field']:
            assert float(node['text'])==f['value'], 'Full precision must be visible, not just data-value'
        elif f['field'].endswith('.n'):
            assert str(f['value']) in re.findall(r'\d+',node['text'])
        else:assert str(f['value']) in node['text']
    return n


def unit_tests(c):
    from RQs.RQ3_16.src.tests import numeric_regression
    from RQs.RQ3_15.src.tests import fixture
    results=[numeric_regression(c)]
    # Repeated-record and nested-table decoding, including zero/null and distinct observations.
    records=[{'owner':'123','value':0,'time':0},{'owner':'123','value':None,'time':1}]
    nested={'series':records,'separate':[1,1,2]}
    assert exps.unpack(exps.pack(nested))==nested
    for source in ('\n'.join(map(exps.dumps,records)),exps.dumps(records),exps.dumps(nested)):
        assert exps.semantic_lines(exps.compact_text(source))==exps.semantic_lines(source)
    payload,_=exps.previous.pairs.extract(fixture(),{'a':'123','b':'456'},{'parent':'parent','child':'child'},
        {'origin':-24.,'duration':48.,'split':24.},.001,c)
    exps.previous.validate_pairs(payload)
    for k in ((),('clock',),('relations',0)):
        bad=deepcopy(payload);at=bad
        for key in k:at=at[key]
        at['anomal']=True;rejects(lambda:exps.previous.validate_pairs(bad))
    assert exps.display_number(0.)=='0' and float(exps.display_number(1.23456789))!=1.23456789
    assert not any(f['field']=='reference.quantiles.0.0' for f in exps.transfer_inventory({
      **payload,'relations':[{**payload['relations'][0],'phases':{**payload['relations'][0]['phases'],
      'reference':{**payload['relations'][0]['phases']['reference'],'quantiles':[[1.23456789,22.85],[24.,44.7]]}}}]}))
    for arm in ARMS:
        envelope=exps.request_envelope(arm,exps.QA_SYSTEM if arm in exps.QA else 'system')
        assert envelope['schema']==exps.qa_schema() if arm in exps.QA else envelope['schema']['json_schema']['schema']['properties']['services']['minItems']==5
    assert gates.paired([0.,0.])['p']==1.
    results+=['Lossless table roundtrip including null/zero/repeated observations','Rounded values retained as text',
              'Recursive public whitelist','Separate typed QA and fixed-five RCA schemas']
    return results


def lifecycle(c):
    """Actual queue and durable ledger with offline provider; no network/service allowed."""
    from . import main
    from RQs.RQ3_1.src import main as shared
    from vlmrca.run_state import DurableCallRegister
    from vlmrca.vlm import client
    import socket
    reg=register(c);chosen=[]
    for row in reg['cases']:
        p=read_json(path(c['preparation'])/'public'/(row['opaque_incident_id']+'.json'))
        applicable=p['qa'] is not None
        if not any(x[2]==applicable for x in chosen):chosen.append((row,p,applicable))
        if len(chosen)==2:break
    assert len(chosen)==2
    with tempfile.TemporaryDirectory(prefix='offline-',dir=path(c['results'])) as temp:
        root=Path(temp);future={**c,'results':str(root.relative_to(ROOT)),'concurrency':2}
        fake={**reg,'cases':[x[0] for x in chosen],'smoke':[x[0] for x in chosen]};seen=[];stopped=False
        def arms(c,smoke=False,row=None):
            if row is None:return ARMS
            return ARMS if next(p for r,p,a in chosen if r==row)['qa'] is not None else ARMS[:6]
        def provider(bound,parts,envelope,output,ledger,score_response):
            nonlocal stopped
            key=bound['call_key'];identity=main.CALL_IDENTITIES[key];idx,cached=ledger.begin(key,identity['request_hash'],'solver')
            assert cached is None;seen.append(identity)
            pub=next(p for r,p,a in chosen if r['opaque_incident_id']==identity['case'])
            response=json.dumps(pub['qa']['answers'] if identity['arm'] in exps.QA else {'services':pub['candidates'][:5],'reason':'offline','confidence':'medium'})
            score=score_response(response);result={'status':score['status'],'score':score,'response':response}
            write_json(output/'outputs'/(key+'.json'),result);write_json(output/'completed'/(key+'.json'),{'status':'complete','test_only':True})
            ledger.finish(idx,result)
            if not stopped:stopped=True;os.kill(os.getpid(),signal.SIGUSR1)
            return result
        fail=AssertionError('CPU test attempted model network or service startup')
        with patch.object(main,'register',return_value=fake),patch.object(gates,'register',return_value=fake),\
             patch.object(main,'phase_arms',side_effect=arms),patch.object(gates,'phase_arms',side_effect=arms),\
             patch.object(main,'runtime'),patch.object(gates,'require_qualification'),patch.object(gates,'require_runtime_attestation'),\
             patch.object(shared,'run_registered_call',side_effect=provider),patch.object(client,'call_vlm',side_effect=fail),\
             patch.object(socket,'create_connection',side_effect=fail),patch.object(main.subprocess,'Popen',side_effect=fail):
            first=main.run(future);assert first['status']=='incomplete'
            result=main.run(future);assert result['status']=='complete' and len(seen)==18
            assert len({x['call_key'] for x in seen})==18
            for row,p,a in chosen:
                for x,y in ((exps.CR,exps.C),(exps.VR,exps.V)):
                    left,right=(flag(root/'formal',row['opaque_incident_id'],arm) for arm in (x,y))
                    assert left['request_hash']==right['request_hash'] and left['call_key']!=right['call_key']
            assert main.run(future)['resumed_complete_phase'] and main.supervise(future)['launched_model'] is False
            saved=seen[0];(root/'formal/completed'/(saved['call_key']+'.json')).unlink()
            assert flag(root/'formal',saved['case'],saved['arm']) is None
        rejects(lambda:gates.require_qualification(c,True))
        register_calls=DurableCallRegister(root/'recovery.sqlite',scope='offline',limit=2)
        first,_=register_calls.begin('x','request','solver');rejects(lambda:register_calls.begin('x','request','solver'))
        assert register_calls.recover_persisted(root,audit=lambda *_:None)['interrupted_spent_calls']==[first]
        second,_=register_calls.begin('x','request','solver',retry=True);register_calls.finish(second,{'ok':True})
        rejects(lambda:register_calls.begin('z','request','solver'))
    return {'status':'passed','offline_calls':18,'model_calls':0,'safe_drain_resume':True,'atomic_boundary':True,'independent_repeats':True,'budget_persists':True}


def cpu(c,smoke=False):
    if smoke:raise ValueError('Complete roster required for CPU qualification')
    from RQs.RQ3_3.src.utils import OfflineTokens
    from RQs.RQ3_18.src.tests import source_oracle
    from RQs.RQ3_12.src.tests import checkpoint_audit
    from .main import render_arm
    started=time.monotonic();current=source_contract();q=path(c['results'])/'qualification';root=path(c['preparation'])
    assert read_json(q/'static.json')['source_contract']==current;gates.require_renderer_build()
    loaded,spec=runtime(c);assert spec['max_model_len']==40960 and spec['gpu_memory_utilization']==.75
    checks=unit_tests(c);tokens=OfflineTokens({'unified':{'vllm':str(loaded.source)},'models':[MODEL]})
    reg=register(c);inventory=[];cases=[];bindings=0;aid_ratios=[];fixed={r['opaque_incident_id'] for r in reg['smoke']};redraws=[]
    for row in reg['cases']:
        if time.monotonic()-started>c['cpu_seconds']:raise TimeoutError('CPU qualification time budget')
        oid=row['opaque_incident_id'];inherited=read_json(path(c['base_preparation'])/'public'/(oid+'.json'))
        public=read_json(root/'public'/(oid+'.json'));marker=read_json(root/'flags'/(oid+'.json'))
        for field in ('public','private'):assert sha_file(root/field/(oid+'.json'))==marker[field+'_sha256']
        assert marker['parent_public_sha256']==sha_file(path(c['base_preparation'])/'public'/(oid+'.json'))
        rebuilt=exps.compile_public(inherited,c)
        assert {k:v for k,v in public.items() if k!='images'}=={k:v for k,v in rebuilt.items() if k!='images'}
        injected=deepcopy(inherited);injected['ground_truth']='forbidden';injected['anomal']=True
        assert exps.compile_public(injected,c)==rebuilt
        fact_report=fidelity(inherited,public);independent_qa(public)
        png=None
        if public['images']:
            image=root/public['images'][exps.V]['path'];png=image.read_bytes()
            assert sha_file(image)==public['images'][exps.V]['sha256']
            assert all(v==public['images'][exps.V] for v in public['images'].values())
            bindings+=inspect_image(public,image.parent,c)
            if oid in fixed:
                target=q/'redraws'/oid
                if not (target/'manifest.json').exists():render_arm(public['readout'],c,exps.V,target)
                assert sha_file(target/'dashboard.png')==sha_file(image)
                redraws.append({'case':oid,'png_sha256':sha_file(image),'byte_identical':True})
        arms=set(phase_arms(c,False,row))|set(phase_arms(c,True,row) if oid in fixed else ())
        counts={}
        for arm in ARMS:
            if arm not in arms:continue
            parts=exps.parts_for(public,arm,png if arm in public['images'] else None)
            system=exps.system_for(public,arm);count=tokens.count(parts,system,MODEL)
            assert count+c['max_tokens']<=40960,(oid,arm,count)
            counts[arm]=count
            inventory.append({'case':oid,'dataset':row['dataset'],'arm':arm,'scope':'formal' if arm in phase_arms(c,False,row) else 'smoke_only',
              'input_tokens':count,'system_sha256':stable_hash(system),'png_sha256':public['images'].get(arm,{}).get('sha256'),
              'text_hash':stable_hash(public['texts'][arm]),'request_family':'qa' if arm in exps.QA else 'rca'})
        if oid in reg['qa_cases']:
            for left,right in (('C_RB','C_RP'),('V_RB','V_RP')):aid_ratios.append(abs(counts[left]-counts[right])/counts[left])
            assert counts[exps.C]==counts[exps.CR] and counts[exps.V]==counts[exps.VR]
        cases.append({'case':oid,'dataset':row['dataset'],'applicable':bool(public['images']),'inputs':counts,**fact_report})
        if len(cases)%20==0:
            print(json.dumps({'event':'cpu_progress','cases':len(cases),'elapsed':time.monotonic()-started}),flush=True)
    ratios={};errors=[]
    for dataset in c['case_counts']:
        rows=[r for r in cases if r['dataset']==dataset]
        ratios[dataset]={a:sum(r['inputs'][exps.V] for r in rows)/sum(r['inputs'][a] for r in rows) for a in (exps.F,exps.C)}
        if any(v>c['readiness']['max_mean_input_ratio'] for v in ratios[dataset].values()):errors.append('input_budget:'+dataset)
        applicable=[r for r in rows if r['applicable']]
        if sum(r['body_transfer_count']>0 for r in applicable)/len(applicable)<.5:errors.append('transfer_applicability:'+dataset)
    if max(aid_ratios,default=0)>.02:errors.append('readout_token_matching')
    write_json(q/'input_inventory.json',inventory)
    report={'status':'failed' if errors else 'passed','source_contract':current,'cases':cases,'input_ratios':ratios,
      'maximum_input':max(x['input_tokens'] for x in inventory),'core_positions':sum(x['scope']=='formal' for x in inventory),
      'qa_cases':len(reg['qa_cases']),'aid_max_token_difference_ratio':max(aid_ratios,default=0),'checks':checks,
      'bindings':bindings,'deterministic_redraws':redraws,'errors':errors,'model_calls':0,'seconds':time.monotonic()-started}
    write_json(q/'cpu_feasibility.json',report)
    if errors:raise RuntimeError('Scientific/budget feasibility failed: '+str(errors))
    report['source_oracle']=source_oracle(c)
    report['lifecycle']=lifecycle(c);report['checkpoint_audit']=checkpoint_audit(loaded)
    assert source_contract()==current
    report['seconds']=time.monotonic()-started
    write_json(q/'cpu.json',report);examples(c)
    return {k:v for k,v in report.items() if k not in {'source_contract','cases','checkpoint_audit'}}


def examples(c):
    root=path(c['preparation']);reg=register(c)
    publics={r['opaque_incident_id']:read_json(root/'public'/(r['opaque_incident_id']+'.json')) for r in reg['cases']}
    selected={r['opaque_incident_id']:'fixed '+r['dataset'] for r in reg['smoke']}
    valid=[oid for oid,p in publics.items() if p['images']]
    selected[max(valid,key=lambda x:max(len(r['parent_operation'])+len(r['child_operation']) for r in publics[x]['payload']['relations']))]='long operation'
    selected[max(valid,key=lambda x:max(v for r in publics[x]['readout']['relations'] for row in r['data']['quantiles'] for v in row))]='extreme'
    single=[oid for oid in valid if len(publics[oid]['payload']['relations'])==1]
    if single:selected[sorted(single)[0]]='single relation'
    fallback=sorted(set(publics)-set(valid))
    if fallback:selected[fallback[0]]='text fallback'
    out=root/'examples';out.mkdir(exist_ok=True);index=[];html=['<!doctype html><meta charset="utf-8"><title>RQ3.19 input examples</title><h1>RQ3.19 actual model inputs</h1>']
    for oid,why in selected.items():
        p=publics[oid];html.append(f'<h2>{escape(oid)} — {escape(why)}</h2>')
        for arm in ARMS:
            if arm in exps.QA and p['qa'] is None:continue
            entry=p['images'].get(arm);image=os.path.relpath(root/entry['path'],out) if entry else None
            name=oid+'__'+arm+'.txt'
            (out/name).write_text(exps.system_for(p,arm)+'\n\n'+(exps.VISUAL_GUIDE+'\n\n' if entry else '')+'\n\n'.join(x['text'] for x in p['texts'][arm]))
            html.append(f'<h3>{arm}</h3><a href="{name}">Actual text</a>')
            if image:html.append(f'<p><a href="{image}"><img src="{image}" width="840"></a></p>')
            index.append({'case':oid,'arm':arm,'selection':why,'image':image,'text':name})
    (out/'index.html').write_text('\n'.join(html));write_json(out/'index.json',index)
    return {'status':'written','examples':len(index),'index':str(out/'index.html')}
