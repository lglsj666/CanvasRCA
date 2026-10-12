"""Offline source-fidelity and real-processor feasibility; no model client."""
from copy import deepcopy
from collections import Counter
import json
import math
import os
import re
import time
from . import exps
from .utils import ROOT,MODEL,VERSION,read,write,sha,digest,register,source_contract


def unpack_records(groups):
    """Independent test-side decoder for the model-visible named-column wire."""
    rows=[]
    for group in groups:
        columns=group['columns'];fixed=group.get('fixed',{});copies=group.get('copy',{})
        assert len(set(columns))==len(columns)
        assert not set(columns)&set(fixed) and not (set(columns)|set(fixed))&set(copies)
        for values in group['rows']:
            assert len(values)==len(columns)
            flat={**deepcopy(fixed),**dict(zip(columns,values,strict=True))}
            for target,ref in copies.items():
                val=flat[ref['field']]
                flat[target]=deepcopy(val[ref['index']] if 'index' in ref else val)
            row={}
            for path,value in flat.items():
                keys=[k.replace('~1','/').replace('~0','~') for k in path.split('/')]
                current=row
                for key in keys[:-1]:current=current.setdefault(key,{})
                assert keys[-1] not in current
                current[keys[-1]]=value
            rows.append(row)
    return rows


def wire_fidelity(public):
    idx=public['index'];wire=exps.overview_wire(public)
    for key in ('records','aux_metrics','components','pairs'):
        assert digest(unpack_records(wire[key]))==digest(idx[key]),key
    assert wire['roles']==idx['roles'] and wire['clock']==idx['clock']
    edges=sorted((source,target,kind) for kind,sources in wire['edges'].items() for source,targets in sources.items() for target in targets)
    assert edges==sorted(map(tuple,idx['edges']))
    # Every occurrence and its order are retained, including identical observations.
    rebuilt=[]
    for chunk in wire['additional_public_summaries']:
        if 'text' in chunk:rebuilt.append(chunk['text'])
        else:
            prefix=chunk['prefix']+': ' if chunk['prefix'] else ''
            rebuilt.extend(prefix+json.dumps(r,ensure_ascii=False,separators=(',',':')) for r in unpack_records(chunk['records']))
    for original,new in zip(idx['additional_public_summaries'],rebuilt,strict=True):
        if original==new:continue
        if original.startswith('{'):assert digest(json.loads(original))==digest(json.loads(new))
        else:
            a,av=original.split(': ',1);b,bv=new.split(': ',1)
            assert a==b and digest(json.loads(av))==digest(json.loads(bv))
    source_records={r['fact_id']:r for r in idx['records'] if 'fact_id' in r}
    windows=[]
    for row in unpack_records(wire['window_summary']):
        fid=row['fact_id'];record=source_records.get(fid,{})
        entity=row.get('entity',record.get('entities',[None])[0])
        label=row.get('label',fid+' · '+str(record.get('metric',record.get('operation',''))))
        windows.append(' | '.join((fid,entity,label,row['unit'])))
        if 'first' in row:
            windows.append(' ; '.join(name+' '+row[name][0]+' @bin'+row[name][1] for name in ('first','last','minimum','maximum')))
        elif 'exclusive_p95_reference' in row:windows.append('exclusive p95: reference '+row['exclusive_p95_reference']+' ; current '+row['exclusive_p95_current'])
        else:windows.append(row['original_summary'])
    assert windows==idx['window_summary'],'Window literal values, units, labels, bins or order changed'
    return {'wire_roundtrip':True,'window_rows':len(windows)//2,'extra_occurrences':len(rebuilt)}


def fidelity(original,public):
    """Independent source-value checks, including observations deferred to retrieval."""
    assert public['ledger']['full_text_parts']==original['texts']['FULL_TEXT']
    assert public['candidates']==original['candidates']
    assert public['ledger']['pair_packet']==original['payload']
    assert len({b['id'] for b in public['ledger']['bundles']})==len(public['ledger']['bundles'])
    source=original['texts']['FULL_TEXT'];bundles={b['id']:b for b in public['ledger']['bundles']}
    for b in bundles.values():
        assert digest(b['text'])==b['content_sha256']
        ref=b['source']
        if 'line' in ref:assert source[ref['part']]['text'].splitlines()[ref['line']]==b['text']
        elif 'pair_packet' in ref:
            rel=next(r for r in original['payload']['relations'] if r['id']==ref['pair_packet'])
            assert json.loads(b['text'])==rel
        elif 'series' in ref:
            raw=json.loads(source[ref['part']]['text'].rsplit('\n',1)[1])
            rows=[dict(zip(raw['fields'],r,strict=True)) for r in raw['series']]
            assert json.loads(b['text'])==next(r for r in rows if r['id']==ref['series'])
        elif 'card' in ref:
            raw=json.loads(source[ref['part']]['text'].split('\n',1)[1])
            rows=[dict(zip(raw['columns'],r,strict=True)) for r in raw['rows']]
            assert json.loads(b['text'])==next(r for r in rows if r['id']==ref['card'])
        else:raise AssertionError('Unbound detail bundle')
    for binding in public['index_source_bindings']:
        line=source[binding['part']]['text'].splitlines()[binding['line']]
        projected=public['index']['records'][binding['record']]
        # Independently compare each JSON-valued metadata operand against the canonical raw string.
        for key,value in projected.items():
            if key in {'region','field','bins','detail_bundle','fact_id'}:continue
            match=re.search(r'(?<![\w])'+re.escape(key)+'=',line)
            assert match and json.JSONDecoder().raw_decode(line[match.end():])[0]==value,(key,value)
        if projected['field']=='metric_series_64':assert projected['detail_bundle'] in bundles
    expected=set()
    for part in source:
        text=part['text']
        if text.startswith('Additional component facts'):
            raw=json.loads(text.split('\n',1)[1]);cols=raw['columns']
            for row in raw['rows']:
                card=dict(zip(cols,row,strict=True))
                if card['kind']=='graph':expected.update(tuple(e) for e in card['data']['edges'])
        if text.startswith('G:'):
            for line in text.splitlines():
                if line.startswith('directed_call_edge:'):
                    e=json.loads(line.split(':',1)[1]);expected.add((e['caller'],e['callee'],'calls'))
                elif line.startswith('{'):
                    e=json.loads(line)
                    if 'from' in e and 'to' in e:expected.add((e['from'],e['to'],e['relation']))
                    elif e.get('relation')=='observed parent span -> child span':expected.add((e['parent'][0],e['child'][0],'request_parent'))
    expected.update((r['parent'],r['child'],'request_parent') for r in original['payload']['relations'])
    assert expected==set(map(tuple,public['index']['edges']))
    rendered={(e['source'],e['target'],'owns' if e['kind']=='has_instance' and (e['source'],e['target'],'owns') in expected else e['kind'])
              for g in public['topology']['graph_cards'] for e in g['data']['edges']}
    assert rendered==expected
    for summary in public['index']['pairs']:
        raw=next(r for r in original['payload']['relations'] if r['id']==summary['id'])
        for phase,values in summary['phases'].items():
            assert values['sample_n']==len(raw['phases'][phase]['points'])
            assert 'points' not in values
            assert {k:v for k,v in values.items() if k!='sample_n'}=={k:v for k,v in raw['phases'][phase].items() if k!='points'}
    poisoned=deepcopy(original);poisoned.update(ground_truth='forbidden',anomal=True,historical_answer='forbidden')
    assert exps.compile_public(poisoned)==public
    return {**wire_fidelity(public),'original_parts_preserved':len(source),'bound_detail_bundles':len(bundles),
            'complete_edges':len(expected),'original_metric_summaries':sum(r['field']=='metric_series_64' for r in public['index']['records'])}


def unit(c):
    from .main import load_public
    reg=register(c);original,public,_=load_public(c,reg['cases'][0]);fidelity(original,public)
    ids=[b['id'] for b in public['ledger']['bundles']]
    for invalid in ('{}','{','{"bundle_ids":["unknown"]}',json.dumps({'bundle_ids':[ids[0],ids[0]]}),json.dumps({'bundle_ids':ids[:9]})):
        assert exps.selection(invalid,public)=={'schema':'FetchSelectionV1','valid':False,'bundle_ids':[]}
    assert exps.selection(json.dumps({'bundle_ids':ids[:8]}),public)['bundle_ids']==ids[:8]
    assert exps.selection('{"bundle_ids":[]}',public)['valid']
    assert exps.final_parts(public,[])==exps.overview_parts(public,task='rca')
    fixture='Log evidence; field=denum_log_template; entities=["123"]; bins=[0]; unit="count"; template="x service=evil" count=0'
    assert exps.assignment_record(fixture)['template']=='x service=evil'
    fixture='Metric evidence; field=metric_series_64; entities=["123"]; bins=0..63 (inclusive); unit="s"; values_codec=[0,null,2]'
    assert exps.assignment_record(fixture)['values_codec']==[0,None,2]
    synthetic=[{'entities':['001'],'service':'001','fact_id':'x','detail_bundle':'x',
                'nested':{'x/y':0,'~test':None,'empty':{},'number':'0.00'}},
               {'entities':['002'],'service':'002','fact_id':'y','detail_bundle':'y',
                'nested':{'x/y':False,'~test':None,'empty':{},'number':'0.00'}}]
    assert digest(unpack_records(exps.packed_rows(synthetic)))==digest(synthetic)
    assert exps.packed_edges([['1','1','calls'],['1','2','calls'],['1','2','request_parent']])=={'calls':{'1':['1','2']},'request_parent':{'1':['2']}}
    # Offline substitute: test ordering and whole-packet skips without a model client.
    count=lambda parts:sum(len(p['text']) for p in parts)
    base_count=count(exps.final_parts(public,[]))
    available=sorted(exps.retrievable_ids(public),key=lambda bid:count(exps.final_parts(public,[bid])))
    # Scale the fake count below the fixed context cap; relative packet sizes remain real.
    def offline_count(parts):return count(parts)/10
    largest,smallest=available[-1],available[0]
    limit=offline_count(exps.final_parts(public,[smallest]))
    packed=exps.budgeted_final(public,json.dumps({'bundle_ids':[largest,smallest]}),limit,offline_count)
    assert packed['accepted']==[smallest] and packed['skipped']==[largest]
    assert packed['parts']==exps.final_parts(public,[smallest])
    assert exps.budgeted_final(public,'{}',limit,offline_count)['parts']==exps.final_parts(public,[])
    assert exps.budgeted_final(public,'{}',0,offline_count)['common_fallback_required']
    no_new_details=set(ids)-exps.retrievable_ids(public)
    if no_new_details:assert not exps.selection(json.dumps({'bundle_ids':[min(no_new_details)]}),public)['valid']
    report={'status':'passed','scope':'compiler and retrieval contract unit regression',
      'checks':['verbatim full ledger','independent operand source bindings','all typed directed edges',
                'pair populations and sampled counts','private top-level poison inert','duplicate/unknown/malformed fetch IDs',
                'eight-bundle limit','empty fetch fallback','quoted assignments and zero/missing values',
                'independent complete wire roundtrip','nested key escaping and scalar types','directed multitype adjacency and self-loops',
                'whole-packet priority packing with offline counter','redundant-only packet excluded','overbudget common fallback'],
      'source_contract':source_contract(c),'new_model_calls':0}
    write(ROOT/c['results']/'qualification/unit.json',report)
    return {k:v for k,v in report.items() if k!='source_contract'}


def feasibility(c,images=False):
    """Text screen provides an upper bound; image pass computes actual eligibility."""
    from RQs.RQ3_3.src.utils import OfflineTokens
    from .main import load_public
    started=time.monotonic();reg=register(c);contract=source_contract(c)
    assert os.environ.get('CUDA_VISIBLE_DEVICES')=='','CPU run must explicitly disable CUDA'
    import torch
    torch.set_num_threads(1)
    tokens=OfflineTokens({'unified':{'vllm':c['inference_base']},'models':[MODEL]})
    spec=tokens.runtime.model(MODEL)
    assert spec['max_model_len']==40960 and spec['gpu_memory_utilization']==.75
    processor=tokens.processors[MODEL]
    image_records={}
    if images:
        rend=read(ROOT/c['results']/'qualification/renders_all.json')
        assert rend['source_contract']['renderer']==contract['renderer']
        image_records={r['case']:r for r in rend['images']}
    rows=[];prep=ROOT/c['preparation']
    for row in reg['cases']:
        if time.monotonic()-started>c['cpu_seconds']:raise TimeoutError('CPU feasibility exceeded registered bound')
        oid=row['opaque_incident_id'];original,public,parent_hash=load_public(c,row)
        checks=fidelity(original,public)
        full=tokens.count(original['texts']['FULL_TEXT'],original['system'],MODEL)
        costs={b['id']:len(processor.tokenizer.encode(b['text'],add_special_tokens=False)) for b in public['ledger']['bundles']}
        # The decimal budget has at most five digits. Count the concrete value to
        # a fixed point: changing the prompt's number cannot quietly evade cost.
        budget=math.floor(c['max_pipeline_fraction']*full)-c['max_select_tokens']
        png=None
        if images and image_records[oid]['status']=='rendered':
            entry=image_records[oid];path=prep/entry['path']
            assert sha(path)==entry['sha256'] and entry['source_public_sha256']==parent_hash
            png=path.read_bytes()
        for _ in range(10):
            tparts=exps.overview_parts(public,costs=costs,final_budget=budget)
            tc=tokens.count(tparts,public['system'],MODEL)
            vc=None
            if png:
                vparts=[{'type':'image','png':png}]+exps.overview_parts(public,True,costs=costs,final_budget=budget)
                vc=tokens.count(vparts,public['system'],MODEL)
            updated=math.floor(c['max_pipeline_fraction']*full)-c['max_select_tokens']-max(tc,vc or tc)
            if updated==budget:break
            budget=updated
        else:raise ValueError('Budget serialization did not converge')
        shell=tokens.count(exps.final_parts(public,[]),public['system'],MODEL)
        detail_counts={b['id']:tokens.count(exps.final_parts(public,[b['id']]),public['system'],MODEL)
                       for b in public['ledger']['bundles']}
        informative=exps.retrievable_ids(public)
        minimum=min((detail_counts[bid] for bid in informative),default=10**9)
        context_ok=full+8192<=40960 and minimum+8192<=40960 and shell+8192<=40960 and tc+512<=40960
        text_possible=tc<=c['max_overview_fraction']*full and minimum<=budget and bool(public['index']['edges']) and context_ok
        eligible=text_possible and vc is not None and vc<=c['max_overview_fraction']*full and vc+512<=40960
        st=tokens.count(exps.overview_parts(public,task='rca'),public['system'],MODEL)
        sv=tokens.count([{'type':'image','png':png}]+exps.overview_parts(public,True,task='rca'),public['system'],MODEL) if png else None
        record={'case':oid,'dataset':row['dataset'],'baseline_tokens':full,'text_selector_tokens':tc,
                'visual_selector_tokens':vc,'summary_text_tokens':st,'summary_visual_tokens':sv,
                'final_shell_tokens':shell,'shared_final_budget':budget,'minimum_complete_detail_input':minimum,
                'detail_inputs':detail_counts,'detail_content_tokens':costs,'retrievable_bundle_ids':sorted(informative),
                'text_possible':text_possible,
                'eligible':eligible if images else None,'text_ratio':tc/full,'visual_ratio':vc/full if vc else None,
                'context_ok':context_ok,'source_public_sha256':parent_hash,**checks}
        rows.append(record)
        # No evaluator/private records are loaded during feasibility.
        write(prep/'public'/(oid+'.json'),public)
        write(prep/'audit'/(oid+'.json'),{'source_public_sha256':parent_hash,'config_hash':digest(c),
              'compiler_sha256':sha(ROOT/'RQs/RQ3_20/src/exps.py'),'checks':checks})
        if len(rows)%20==0:print(json.dumps({'event':'feasibility_progress','cases':len(rows),'images':images,'seconds':round(time.monotonic()-started,1)}),flush=True)
    stats={}
    for ds,n in c['case_counts'].items():
        subset=[r for r in rows if r['dataset']==ds]
        stats[ds]={'cases':len(subset),'text_possible':sum(r['text_possible'] for r in subset),
                   'eligible':sum(bool(r['eligible']) for r in subset) if images else None,
                   'required':math.ceil(c['minimum_dataset_applicability']*n),'mean_text_ratio':sum(r['text_ratio'] for r in subset)/n,
                   'mean_visual_ratio':sum(r['visual_ratio'] or 0 for r in subset)/max(1,sum(r['visual_ratio'] is not None for r in subset)) if images else None}
    failures=[ds for ds,r in stats.items() if r['eligible' if images else 'text_possible']<r['required']]
    report={'status':'failed' if failures else ('passed' if images else 'text_screen_passed'),
            'scope':'complete processor image and text feasibility' if images else 'necessary text-budget screen; image qualification pending',
            'source_contract':contract,'datasets':stats,'failed_datasets':failures,'cases':rows,
            'new_model_calls':0,'seconds':time.monotonic()-started,'cuda_used':False,
            'gate':'all datasets >=50%; first input <=.50F; two inputs+512<=.85F; no data truncation'}
    assert source_contract(c)==contract
    file='cpu_feasibility.json' if images else 'cpu_text_feasibility.json'
    write(ROOT/c['results']/'qualification'/file,report)
    return {k:v for k,v in report.items() if k not in {'cases','source_contract'}}


def reuse(c):
    """Compatible frozen v2 PNG reuse; no rendering or model call is needed."""
    from .utils import runtime
    runtime(c);reg=register(c);old=ROOT/c['previous_results'];q=ROOT/c['results']/'qualification';prep=ROOT/c['preparation']
    oldprep=ROOT/'RQs/RQ3_20/preparation/budgeted_acquisition_v2'
    oldrenders=read(old/'qualification/renders_all.json');assert oldrenders['source_contract']['renderer']==source_contract(c)['renderer']
    protection=read(old/'qualification/protection_before.json')['files']
    for folder in (old,oldprep):
        for p in folder.rglob('*'):
            if p.is_file():protection[str(p.relative_to(ROOT))]=sha(p)
    protection['RQs/RQ3_20/configs/budgeted_acquisition_v2.json']=sha(ROOT/'RQs/RQ3_20/configs/budgeted_acquisition_v2.json')
    write(q/'protection_before.json',{'files':protection})
    images=[]
    from .main import load_public
    for row in reg['cases']:
        oid=row['opaque_incident_id'];original,public,parent_hash=load_public(c,row)
        assert digest(public)==digest(read(oldprep/'public'/(oid+'.json')))
        image=deepcopy(next(r for r in oldrenders['images'] if r['case']==oid))
        if image['status']=='rendered':
            oldfile=oldprep/image['path'];assert sha(oldfile)==image['sha256']
            evidence,base,ops,design,audit=exps.design_for(public,c)
            assert digest([evidence,design])==image['signature']
            image['path']=os.path.relpath(oldfile,prep)
        images.append(image)
        write(prep/'public'/(oid+'.json'),public)
        private=ROOT/c['base_preparation']/'private'/(oid+'.json')
        marker=read(ROOT/c['base_preparation']/'flags'/(oid+'.json'))
        assert sha(private)==marker['private_sha256']
        write(prep/'private'/(oid+'.json'),read(private))
    write(q/'renders_all.json',{'status':'complete','source_contract':source_contract(c),'images':images,
                              'reused_from':c['previous_results'],'new_model_calls':0})
    return {'status':'reused','public_cases':220,'unified_pngs':sum(x['status']=='rendered' for x in images),'protected_files':len(protection)}


def lifecycle(c,records,tokens):
    """Real transaction/writer/ledger/scorer with network disabled at provider."""
    from pathlib import Path
    from unittest.mock import patch
    import tempfile
    import socket
    import threading
    from . import main
    from .utils import committed_call,flag,ledger_for,runtime
    from vlmrca.vlm import client
    from vlmrca.run_state import DurableCallRegister
    runtime(c);reg=register(c);seen=[]
    row=reg['smoke'][0];oid=row['opaque_incident_id'];public=read(ROOT/c['preparation']/'public'/(oid+'.json'))
    image=next(r for r in read(ROOT/c['results']/'qualification/renders_all.json')['images'] if r['case']==oid)
    png=(ROOT/c['preparation']/image['path']).read_bytes();record=next(r for r in records if r['case']==oid)
    assert record['eligible']
    context={'public':public,'record':record,'png':png,'private':read(ROOT/c['preparation']/'private'/(oid+'.json')),
             'count':lambda parts,system:tokens.count(parts,system,MODEL)}
    ids=sorted(exps.retrievable_ids(public))[:3]
    def provider(parts,cfg,system,*args,**kwargs):
        stage='select' if cfg.max_tokens==512 else 'qa' if cfg.max_tokens==1024 else 'diagnose'
        assert cfg.max_tokens in (512,1024,8192)
        assert kwargs['max_retries']==1
        seen.append({'stage':stage,'cap':cfg.max_tokens,'parts':deepcopy(parts)})
        response={'bundle_ids':ids} if stage=='select' else {'services':public['candidates'][:5],'reason':'offline protocol regression','confidence':'medium'}
        if stage=='qa':response={'q1':[],'q2':[]}
        return client.VLMResponse(json.dumps(response),input_tokens=1000,output_tokens=12,latency_s=.01,raw={})
    fail=AssertionError('CPU attempted network/service startup')
    with tempfile.TemporaryDirectory(prefix='lifecycle-',dir=ROOT/c['results']) as temp:
        root=Path(temp);ledger=DurableCallRegister(root/'calls.sqlite',limit=100,scope='cpu_only');stop=threading.Event()
        with patch.object(client,'call_vlm',side_effect=provider),patch.object(client,'count_vllm_prompt_tokens',return_value=1000),\
             patch.object(socket,'create_connection',side_effect=fail),patch('subprocess.Popen',side_effect=fail):
            for arm in ('FULL_TEXT','TEXT_FETCH','VISUAL_FETCH','TEXT_REPEAT','VISUAL_REPEAT','SUMMARY_TEXT','SUMMARY_VISUAL',*exps.QA_ARMS,*exps.AID_ARMS):
                main.execute_workflow(c,row,arm,context,root,ledger,stop)
            for a,b in (('TEXT_FETCH','TEXT_REPEAT'),('VISUAL_FETCH','VISUAL_REPEAT')):
                left,right=flag(root,oid,a),flag(root,oid,b)
                assert left['selector_call_key']!=right['selector_call_key']
                l=read(root/'outputs'/(left['selector_call_key']+'.json'));r=read(root/'outputs'/(right['selector_call_key']+'.json'))
                assert l['request_hash']==r['request_hash']
            before=len(seen)
            for arm in ('FULL_TEXT','TEXT_FETCH','VISUAL_FETCH'):main.execute_workflow(c,row,arm,context,root,ledger,stop)
            assert len(seen)==before,'Committed calls were replayed'
            # Missing logical marker: rebuild using per-call atomic completions, no generation.
            from .utils import logical_key
            (root/'flags'/(logical_key(oid,'TEXT_FETCH')+'.json')).unlink()
            main.execute_workflow(c,row,'TEXT_FETCH',context,root,ledger,stop);assert len(seen)==before
            # A fallback case must preserve FULL_TEXT and share ordinary requests.
            fallback_row={**row,'opaque_incident_id':'CPU-FALLBACK'};fallback={**context,'record':{**record,'eligible':False},'png':None}
            start=len(seen)
            for arm in ('FULL_TEXT','SUMMARY_TEXT','SUMMARY_VISUAL','TEXT_FETCH','VISUAL_FETCH'):
                main.execute_workflow(c,fallback_row,arm,fallback,root,ledger,stop)
            assert len(seen)==start+1
            main.execute_workflow(c,fallback_row,'VISUAL_REPEAT',fallback,root,ledger,stop)
            assert len(seen)==start+2
            stop.set();assert main.execute_workflow(c,{**row,'opaque_incident_id':'CPU-STOP'},'FULL_TEXT',context,root,ledger,stop) is None
        recovery=DurableCallRegister(root/'recovery.sqlite',limit=2,scope='cpu')
        first,_=recovery.begin('x','f','select')
        try:recovery.begin('x','f','select');raise AssertionError('Duplicate start allowed')
        except RuntimeError:pass
        assert recovery.recover_persisted(root,audit=lambda *_:None)['interrupted_spent_calls']==[first]
        second,_=recovery.begin('x','f','select',retry=True);recovery.finish(second,{'ok':True})
        try:recovery.begin('y','f','select');raise AssertionError('Attempt ceiling failed')
        except RuntimeError:pass
    return {'status':'passed','offline_provider_calls':len(seen),'actual_model_calls':0,'checks':[
      'real shared persistence and scorer','stage output caps','exact-request references','fresh repeats',
      'all-arm common fallback','atomic completion resume without generation','pause stops submissions','durable interrupted-call recovery and cap']}


def cpu(c):
    """Full actual-processor gate followed by offline runtime qualification."""
    from . import gates
    from .utils import runtime,phase_arms
    from RQs.RQ3_3.src.utils import OfflineTokens
    assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
    runtime(c);current=source_contract(c);q=ROOT/c['results']/'qualification'
    assert read(q/'static.json')['source_contract']==current
    u=unit(c);f=feasibility(c,True)
    if f['status']!='passed':return f
    reg=register(c);records=read(q/'cpu_feasibility.json')['cases'];lookup={r['case']:r for r in records}
    tokens=OfflineTokens({'unified':{'vllm':c['inference_base']},'models':[MODEL]})
    images={r['case']:r for r in read(q/'renders_all.json')['images']};checks=[];maxqa=0;qa_matched=0
    from .main import mechanism_inputs
    for row in reg['cases']:
        oid=row['opaque_incident_id'];prep=ROOT/c['preparation'];pubfile=prep/'public'/(oid+'.json');public=read(pubfile);r=lookup[oid]
        assert r['summary_text_tokens']+8192<=40960
        if r['summary_visual_tokens'] is not None:assert r['summary_visual_tokens']+8192<=40960
        ids=sorted(exps.retrievable_ids(public),key=lambda x:digest(['cpu_priority',x]))[:8]
        count=lambda p,s:tokens.count(p,s,MODEL)
        if r['eligible']:
            packed=exps.budgeted_final(public,json.dumps({'bundle_ids':ids}),r['shared_final_budget'],lambda p:count(p,public['system']))
            assert not packed.get('common_fallback_required')
            assert packed['input_tokens']+max(r['text_selector_tokens'],r['visual_selector_tokens'])+512<=math.floor(.85*r['baseline_tokens'])
            assert packed['parts']==exps.final_parts(public,packed['accepted'])
            # Independently pack priority bundles and compare accepted/skipped sets.
            accepted=[];skipped=[]
            for bid in ids:
                (accepted if count(exps.final_parts(public,accepted+[bid]),public['system'])<=min(r['shared_final_budget'],32768) else skipped).append(bid)
            assert packed['accepted']==accepted and packed['skipped']==skipped
            if oid in reg['mechanism_cases'] or oid in {s['opaque_incident_id'] for s in reg['smoke']}:
                png=(prep/images[oid]['path']).read_bytes()
                packet=mechanism_inputs(c,public,png,r,packed['accepted'],count)
                if packet['applicable']:
                    qa_matched+=1
                    for arm in exps.QA_ARMS:
                        parts=exps.qa_parts(public,png,packet,arm);n=count(parts,exps.QA_SYSTEM);maxqa=max(maxqa,n)
                        assert n+c['qa_max_tokens']<=40960
                        assert exps.RCA_TASK not in parts[1]['text']
                        assert exps.score_qa(packet,json.dumps(packet['answers']))['metrics']['qa_accuracy']==1.
        audit=read(prep/'audit'/(oid+'.json'));audit.update(public_sha256=sha(pubfile),private_sha256=sha(prep/'private'/(oid+'.json')))
        write(prep/'audit'/(oid+'.json'),audit)
        checks.append({'case':oid,'arms':phase_arms(c,row),'eligible':r['eligible']})
    # Synthetic exact public matching: multi-type direction, unrelated controls, no labels.
    fixture={'ledger':{'bundles':[{'id':'m','entities':['111']}]},'index':{'edges':[['111','222','calls'],['333','444','calls']]}}
    packet=exps.mechanism_packet(fixture,['m']);assert packet['applicable'] and packet['focus_edge']==['111','222','calls']
    assert set(packet['control_edge'][:2]).isdisjoint(packet['selected_entities'])
    assert not exps.mechanism_packet(fixture,[])['applicable']
    alias={'answers':{'q1':[{'source':'111','target':'222','type':'has_instance'}],'q2':[]}}
    assert exps.score_qa(alias,json.dumps(alias['answers']))['metrics']['qa_accuracy']==1
    alias_response={'q1':[{'source':'111','target':'222','type':'owns'}],'q2':[]}
    assert exps.score_qa(alias,json.dumps(alias_response))['metrics']['qa_accuracy']==1
    from .utils import diagnostic_scorer
    private=read(ROOT/c['preparation']/'private'/(reg['cases'][0]['opaque_incident_id']+'.json'))
    public=read(ROOT/c['preparation']/'public'/(reg['cases'][0]['opaque_incident_id']+'.json'))
    scorer=diagnostic_scorer(private,public['candidates'])
    invalid=scorer(json.dumps({'services':public['candidates'][:1],'reason':'short output','confidence':'medium'}))
    assert invalid['status']=='model_failure' and invalid['metrics']['mrr']==0
    life=lifecycle(c,records,tokens)
    scheduler=scheduler_regression(c,tokens)
    attention={'status':'disabled_incompatible','collector':'src/vlmrca/vlm/attention_probe.py',
      'reason':'Legacy sidecar retains full prompt token positions/IDs and per-query prompt-key vectors; no pre-persistence 64 KiB cap or region aggregation.',
      'legacy_minimum_scalar_slots_at_20000_prompt_tokens':60000,'max_bytes_per_call':65536,
      'no_gpu_measurement_claim':True,'blocks_primary':False}
    write(q/'attention_compatibility.json',attention)
    report={'status':'passed','source_contract':current,'case_checks':checks,'datasets':f['datasets'],'unit':u,'lifecycle':life,'scheduler':scheduler,
      'mechanism_pilot_cpu_only':{'matched_cases':qa_matched,'max_qa_input_tokens':maxqa,'selection':'fixed hash packet IDs, not model selections'},
      'logical_positions':sum(len(x['arms']) for x in checks),'model_calls':0,'attention':attention,
      'conditional_modules':{'sircl':'not activated; original-system fidelity audit pending','confirmation':'not activated; candidate gate and independent exposure audit pending'}}
    assert report['logical_positions']==1520 and source_contract(c)==current
    write(q/'cpu.json',report)
    return {k:v for k,v in report.items() if k not in {'case_checks','source_contract','unit'}}


def scheduler_regression(c,tokens):
    """Exercise the real dependency scheduler, pause boundary and fast resume offline."""
    from pathlib import Path
    from unittest.mock import patch
    import tempfile
    import socket
    import signal
    from . import main,gates,utils
    from vlmrca.vlm import client
    reg=register(c);row=reg['smoke'][0];oid=row['opaque_incident_id']
    public=read(ROOT/c['preparation']/'public'/(oid+'.json'))
    subset={**reg,'cases':[row],'smoke':[row]};arms=('FULL_TEXT','TEXT_FETCH','VISUAL_FETCH','TEXT_REPEAT','VISUAL_REPEAT','QA_NONE','FOCUS_FETCH','CONTROL_FETCH')
    seen=[];paused=False
    def provider(parts,cfg,system,*args,**kwargs):
        nonlocal paused
        seen.append(cfg.max_tokens)
        response={'bundle_ids':sorted(exps.retrievable_ids(public))[:3]} if cfg.max_tokens==512 else {'q1':[],'q2':[]} if cfg.max_tokens==1024 else {
          'services':public['candidates'][:5],'reason':'offline queue test','confidence':'medium'}
        if not paused:paused=True;os.kill(os.getpid(),signal.SIGUSR1)
        return client.VLMResponse(json.dumps(response),input_tokens=1000,output_tokens=12,latency_s=.001,raw={})
    with tempfile.TemporaryDirectory(prefix='scheduler-',dir=ROOT/c['results']) as temp:
        root=Path(temp);future={**c,'results':str(root.relative_to(ROOT)),'concurrency':2}
        utils.runtime(future)
        for name in ('cpu_feasibility.json','renders_all.json'):
            write(root/'qualification'/name,read(ROOT/c['results']/'qualification'/name))
        write(root/'formal/attestation.json',{'rq320_contract_hash':digest(source_contract(future))})
        fail=AssertionError('Offline scheduler attempted network/service startup')
        with patch.object(main,'register',return_value=subset),patch.object(gates,'register',return_value=subset),\
             patch.object(utils,'register',return_value=subset),patch.object(utils,'phase_arms',return_value=arms),\
             patch.object(gates,'require_qualification'),patch.object(client,'call_vlm',side_effect=provider),\
             patch.object(client,'count_vllm_prompt_tokens',return_value=1000),patch.object(socket,'create_connection',side_effect=fail),\
             patch('subprocess.Popen',side_effect=fail),patch('RQs.RQ3_3.src.utils.OfflineTokens',return_value=tokens):
            assert main.run(future)['status']=='incomplete'
            assert main.run(future)['status']=='complete'
            n=len(seen)
            # Completed phase must bypass qualifications, contexts, tokenizers and server.
            with patch.object(main,'read',side_effect=lambda p:utils.read(p) if 'phase_complete' in str(p) else (_ for _ in ()).throw(AssertionError('Bulk reopening on complete resume'))):
                assert main.run(future)['status']=='complete'
                assert main.supervise(future)['launched_model'] is False
            assert len(seen)==n
    utils.runtime(c)
    return {'status':'passed','offline_provider_calls':len(seen),'new_model_calls':0,
            'checks':['real hash dependency queue','no mechanism before V commit','SIGUSR1 stop and resume','phase-complete bypasses service and context materialization']}
