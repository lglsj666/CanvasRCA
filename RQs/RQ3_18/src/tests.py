"""Fresh CPU qualification: source statistics, model-visible controls and offline lifecycle."""
from collections import defaultdict,Counter
from copy import deepcopy
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import hashlib
import json
import math
import os
import tempfile
import time
from unittest.mock import patch
from . import exps,gates
from .utils import ROOT,ARMS,MODEL,VERSION,path,config,register,runtime,source_contract,read_json,write_json,sha_file,stable_hash,flag,logical_key
from RQs.RQ3_14.src.tests import DOM


def rejects(fn,types=(ValueError,AssertionError,RuntimeError)):
    try:fn()
    except types:return
    raise AssertionError('Expected rejection')


def display_number(v):
    """Independent decimal oracle for JS n(): inspect actual text, not data attributes alone."""
    from decimal import Decimal,localcontext,ROUND_HALF_UP
    if v==0:return '0'
    scientific=v>=1e5 or v<.001
    with localcontext() as ctx:
        ctx.prec=400;d=Decimal.from_float(float(v));exponent=d.adjusted()
        rounded=d.quantize(Decimal(1).scaleb(exponent-(3 if scientific else 4)),rounding=ROUND_HALF_UP)
        if scientific:
            exponent=rounded.adjusted();return f'{rounded.scaleb(-exponent):.3f}e{exponent:+d}'
        value=format(rounded,'f');return value.rstrip('0').rstrip('.') if '.' in value else value


class WithoutGlyphs(HTMLParser):
    def __init__(self,value):
        super().__init__(convert_charrefs=True);self.events=[];self.depth=0;self.feed(value)
    def handle_starttag(self,tag,attrs):
        if self.depth:self.depth+=1;return
        if 'data-profile-glyph' in dict(attrs):self.depth=1;return
        self.events.append(('start',tag,tuple(attrs)))
    def handle_endtag(self,tag):
        if self.depth:self.depth-=1;return
        self.events.append(('end',tag))
    def handle_data(self,data):
        if not self.depth and data.strip():self.events.append(('text',data))
    def handle_startendtag(self,tag,attrs):
        if not self.depth:self.events.append(('empty',tag,tuple(attrs)))


def unit_tests(c):
    import numpy as np
    from RQs.RQ3_16.src.tests import numeric_regression
    from RQs.RQ3_15.src.tests import fixture
    from RQs.RQ2.src.exps import rca_schema
    checks=[numeric_regression(c)]
    packet,_=exps.pairs.extract(fixture(),{'a':'123','b':'456'},{'parent':'parent','child':'child'},
        {'origin':-24.,'duration':48.,'split':24.},.001,c)
    readout=exps.readout_packet(packet,'base')
    np.testing.assert_allclose(readout['relations'][0]['data']['quantiles'],[[12.5,36.5],[22.85,46.85],[24.,72.],[44.7,92.7]])
    # Nested labels cannot enter the public DTO, even if the root container is clean.
    for location in ((),('clock',),('relations',0),('relations',0,'phases','current')):
        bad=deepcopy(packet);target=bad
        for key in location:target=target[key]
        target['anomal']=True;rejects(lambda:exps.readout_packet(bad,'base'))
    bad=deepcopy(packet);bad['relations'][0]['phases']['current']['quantiles'][0][0]=1e10
    rejects(lambda:exps.readout_packet(bad,'base'))
    for a in ARMS:
        base=rca_schema();actual=exps.schema_for(a,base);expected=deepcopy(base)
        expected['json_schema']['schema']['properties']['services']['minItems']=5
        assert actual==expected and base==rca_schema()
    assert gates.paired([0,0,0])['p']==1 and gates.paired([.1,.2,-.3,.4])['p']==.625
    np.testing.assert_allclose([v['holm_p'] for v in gates.holm([{'p':.01},{'p':.04},{'p':.03},{'p':None}])[:3]],[.04,.09,.09])
    cases=[{'case':'one','dataset':'d','event_group':'g','arms':{a:{'metrics':{'mrr':.5}} for a in ARMS}}]
    families=gates.statistical_families(c,cases)
    assert {k:len(v) for k,v in families.items()}=={'primary_mrr':4,'secondary_mrr':17}
    cases[0]['arms'][exps.F]['metrics']=None
    assert gates.contrast(cases,{exps.F:1,exps.T:-1})['full_denominator_bounds']==[-.5,.5]
    private={'numeric_to_natural':{str(i):'service'+str(i) for i in range(100,105)},'accepted_labels':['service101']}
    from RQs.RQ3_1.src.main import score_response_callback
    candidates=list(private['numeric_to_natural'])
    answer=json.dumps({'services':candidates,'reason':'Offline regression fixture','confidence':'medium'})
    scored=score_response_callback(private,candidates)(answer);metrics=scored.get('metrics',scored)
    checked=gates.scored_metrics(answer,private,candidates,metrics)
    assert checked['mrr']==.5 and checked['precision@1']==0 and checked['precision@3']==1/3
    for wrong in ('not json',json.dumps({'services':['100']*5,'reason':'x','confidence':'medium'})):
        scored=score_response_callback(private,candidates)(wrong);m=scored.get('metrics',scored)
        assert all(v==0 for v in gates.scored_metrics(wrong,private,candidates,m).values())
    bad=dict(metrics,mrr=1.);rejects(lambda:gates.scored_metrics(answer,private,candidates,bad))
    checks+=['Recursive public whitelist and quantile-order rejection','Identical fixed-five schemas; invalid0 and explicit precision',
             'Primary4 and secondary17 Holm families; Pratt zero/ties and unknown-score bounds']
    return checks


def source_oracle(c):
    """Independent NumPy recomputation on all source pairs for the three fixed cases."""
    from RQs.RQ3_15.src.utils import public_source
    from RQs.RQ3_15.src.tests import oracle
    rows=[]
    for row in register(c)['smoke']:
        oid=row['opaque_incident_id'];public=read_json(path(c['base_preparation'])/'public'/(oid+'.json'))
        frame,mapping,ops,clock,scale,audit=public_source(c,row,public)
        old=read_json(path('RQs/RQ3_15/preparation/request_joint_v1')/'audit'/(oid+'.json'))
        count=oracle(public['payload'],old['compiler'],frame,scale,c)
        rebuilt,_=exps.pairs.extract(frame,mapping,ops,clock,scale,c)
        assert rebuilt==public['payload']
        rows.append({'case':oid,'dataset':row['dataset'],'population_pairs_checked':count,
                     'source_hashes':audit['source_hashes'],'scale_to_ms':scale,'phase_clock':clock})
    return rows


def historical_variance():
    """Offline feasibility context only; never used by compiler, selection or gates."""
    import csv,statistics
    file=path('RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/case_metrics.csv')
    by_case=defaultdict(dict)
    with file.open() as stream:
        for row in csv.DictReader(stream):
            if row['status']=='done' and row['mrr']:by_case[row['case']][row['arm']]=row
    comparisons=[]
    for a,b in (('MARGINAL_FIVE','PAIR_FIVE'),('MARGINAL_FIVE','MARKLESS_FIVE')):
        differences=[];groups=defaultdict(list)
        for values in by_case.values():
            if a not in values or b not in values:continue
            d=float(values[a]['mrr'])-float(values[b]['mrr']);differences.append(d)
            groups[(values[a]['dataset'],values[a]['event_group'])].append(d)
        group_differences=[statistics.mean(v) for v in groups.values()]
        comparisons.append({'contrast':a+' - '+b,'paired_cases':len(differences),'events':len(groups),
            'case_difference_sd':statistics.stdev(differences),'event_difference_sd':statistics.stdev(group_differences),
            'zero_differences':sum(abs(v)<1e-12 for v in differences)})
    return {'source':str(file.relative_to(ROOT)),'sha256':sha_file(file),'comparisons':comparisons,
            'warning':'Historical exposed development data; this is not a power guarantee. New comparisons may have different variances. More arms do not create independent cases.'}


def inspect_profile(folder,packet,c,arm,contract):
    from PIL import Image
    evidence,_,ops,design,op_audit=exps.design_for(packet,c,arm)
    m=read_json(folder/'manifest.json');source=folder.parent/(folder.name+'_design')
    assert m['status']=='passed' and not m['audit']['issues']
    assert m['png_sha256']==sha_file(folder/'dashboard.png') and m['html_sha256']==sha_file(folder/'dashboard.html')
    assert m['renderer_source']==contract['renderer'] and m['bundle_sha256']==contract['files']['src/renderer/web/dist/render.mjs']
    assert read_json(folder/'evidence.json')==evidence and read_json(folder/'design.json')==design
    assert read_json(source/'operations.json')==ops and read_json(source/'operations_audit.json')==op_audit
    with Image.open(folder/'dashboard.png') as im:im.load();assert im.size==(1120,800) and not im.info
    dom=DOM((folder/'dashboard.html').read_text())
    for r in packet['relations']:
        d=r['data'];nodes=[n for n in dom.nodes if n['panel']==r['id']]
        bound={n['attrs']['data-binding']:n for n in nodes if 'data-binding' in n['attrs']}
        for key in ('parent','child','parent_operation','child_operation'):
            assert d[key] in bound[r['id']+'.'+key]['text']
        assert 'Inclusive' in bound[r['id']+'.duration_type']['text']
        maximum=max(1,*[v for pair in d['quantiles'] for v in pair])
        for i,(reference,current) in enumerate(d['quantiles']):
            for phase,value in (('reference',reference),('current',current)):
                node=bound[f"{r['id']}.quantile.{i}.{phase}"];attrs=node['attrs']
                assert node['tag']=='text' and float(attrs['data-value'])==value
                assert node['text'].strip()==display_number(value)
                assert math.isclose(float(attrs['x']),168+240*math.log1p(value)/math.log1p(maximum),rel_tol=1e-12)
            glyph=bound.get(f"{r['id']}.glyph.{i}")
            if arm in {exps.K,exps.FK}:assert glyph is None
            else:
                assert float(glyph['attrs']['data-reference'])==reference and float(glyph['attrs']['data-current'])==current
        circles=[n for n in nodes if n['tag']=='circle']
        assert len(circles)==(0 if arm in {exps.K,exps.FK} else 8)
        if circles:
            for j,node in enumerate(circles):
                value=d['quantiles'][j//2][j%2]
                assert math.isclose(float(node['attrs']['cx']),168+240*math.log1p(value)/math.log1p(maximum),rel_tol=1e-12)
                assert float(node['attrs']['cy'])==35+(j//2)*60
        for phase in (0,1):
            assert str(d['support'][phase]) in bound[r['id']+'.support']['text']
        axis_texts=[n['text'].strip() for n in nodes if n['tag']=='text' and n['attrs'].get('y')=='279']
        assert axis_texts==[display_number(v) for v in (0.,math.expm1(.5*math.log1p(maximum)),maximum)]
    return len(m['audit']['bindings'])


def lifecycle_tests(c):
    """Use the real queue/ledger/commit boundaries with a strictly offline model substitute."""
    from . import main
    from RQs.RQ3_1.src import main as shared
    from vlmrca.run_state import DurableCallRegister
    from vlmrca.vlm import client
    import socket
    import signal
    reg=register(c);chosen=[]
    for row in reg['cases']:
        p=read_json(path(c['preparation'])/'public'/(row['opaque_incident_id']+'.json'))
        applicable=bool(p['payload']['relations'])
        if not any(x[2]==applicable for x in chosen):chosen.append((row,p,applicable))
        if len(chosen)==2:break
    assert len(chosen)==2
    with tempfile.TemporaryDirectory(prefix='rq318-offline-',dir=path(c['results'])) as tmp:
        root=Path(tmp);future=deepcopy(c);future['results']=str(root.relative_to(ROOT));future['concurrency']=2;formal=root/'formal'
        fake_reg={**reg,'cases':[x[0] for x in chosen],'smoke':[x[0] for x in chosen]};submissions=[];stop_sent=False
        def offline(bound,parts,envelope,output,ledger,score_response):
            nonlocal stop_sent
            key=bound['call_key'];identity=main.CALL_IDENTITIES[key]
            call_id,cached=ledger.begin(key,identity['request_hash'],'solver')
            assert cached is None;submissions.append(identity)
            public=next(p for row,p,_ in chosen if row['opaque_incident_id']==identity['case'])
            response=json.dumps({'services':public['candidates'][:5],'reason':'Offline fixture','confidence':'medium'})
            scored=score_response(response);result={'status':scored['status'],'score':scored,'response':response}
            write_json(output/'outputs'/(key+'.json'),result)
            write_json(output/'cost'/(key+'.json'),{'input_tokens':100,'output_tokens':20,'total_tokens':120})
            write_json(output/'completed'/(key+'.json'),{'status':'complete','test_only':True})
            ledger.finish(call_id,result)
            if not stop_sent:
                stop_sent=True;os.kill(os.getpid(),signal.SIGUSR1)
            return result
        fail=AssertionError('Network or GPU startup attempted during CPU qualification')
        with patch.object(main,'register',return_value=fake_reg),patch.object(gates,'register',return_value=fake_reg),\
             patch.object(main,'runtime',return_value=(None,None)),patch.object(gates,'require_qualification'),\
             patch.object(gates,'require_runtime_attestation'),patch.object(shared,'run_registered_call',side_effect=offline),\
             patch.object(client,'call_vlm',side_effect=fail),patch.object(socket,'create_connection',side_effect=fail),\
             patch.object(main.subprocess,'Popen',side_effect=fail):
            stopped=main.run(future);assert stopped['status']=='incomplete' and 1<=len(submissions)<=2
            stopped_keys={s['call_key'] for s in submissions}
            assert all((formal/'completed'/(key+'.json')).exists() for key in stopped_keys)
            result=main.run(future);assert result['status']=='complete' and len(submissions)==15
            assert len({s['call_key'] for s in submissions})==15
            report=gates.analyze(future);assert report['cases']==2
            assert main.run(future)['resumed_complete_phase'] and len(submissions)==15
            assert main.supervise(future)['launched_model'] is False
            with patch.object(main,'log'):
                smoke_result=main.run(future,True)
            assert smoke_result['status']=='complete'
            # Smoke has a per-dataset subset; a fallback must not depend on an absent T arm.
            for row,p,applicable in chosen:
                for arm in future['smoke_matrix'][row['dataset']]:assert flag(root/'smoke',row['opaque_incident_id'],arm) is not None
            for row,p,applicable in chosen:
                oid=row['opaque_incident_id']
                for a,b in ((exps.TR,exps.T),(exps.FR,exps.F),(exps.R,exps.FP)):
                    av,bv=flag(formal,oid,a),flag(formal,oid,b)
                    assert av['request_hash']==bv['request_hash'] and av['call_key']!=bv['call_key']
                if not applicable:
                    assert sum(bool(flag(formal,oid,a).get('no_op')) for a in ARMS)==7
            # A flag without its atomic commit never becomes a completed call.
            row=chosen[0][0];saved=flag(formal,row['opaque_incident_id'],exps.T)
            (formal/'completed'/(saved['call_key']+'.json')).unlink()
            assert flag(formal,row['opaque_incident_id'],exps.T) is None
        for smoke in (False,True):
            rejects(lambda:gates.require_qualification(c,smoke))
            with patch.object(main.subprocess,'Popen',side_effect=fail),patch.object(client,'call_vlm',side_effect=fail):
                closed=deepcopy(future);closed['results']=str((root/'blocked').relative_to(ROOT))
                rejects(lambda:main.run(closed,smoke))
                rejects(lambda:main.execute(c,chosen[0][0],exps.T,chosen[0][1],root/'blocked',None))
        # Persisted reply/ledger interruption semantics: no spent-call reset.
        ledger=DurableCallRegister(root/'recovery.sqlite',limit=2,scope='offline')
        first,_=ledger.begin('key','request','solver');rejects(lambda:ledger.begin('key','request','solver'))
        result=ledger.recover_persisted(root,audit=lambda *_:None)
        assert result['interrupted_spent_calls']==[first]
        second,_=ledger.begin('key','request','solver',retry=True);ledger.finish(second,{'ok':True})
        assert ledger.begin('key','request','solver')[1]=={'ok':True}
        rejects(lambda:ledger.begin('other','request','solver'))
    return {'offline_requests':len(submissions),'offline_formal_requests':15,'offline_smoke_requests':len(submissions)-15,
            'reference_positions':7,'network_calls':0,'completed_phase_fast_resume':True,
            'missing_atomic_commit_rejected':True,'budget_and_interruption_persist':True,
            'safe_stop_drained_then_resumed':True,'per_dataset_smoke_fallback':True}


def boundary_checks(c,public):
    from .main import render_arm
    packet=deepcopy(public['readout']);packet['relations']=packet['relations'][:1]
    d=packet['relations'][0]['data'];d['quantiles']=[[0.,0.],[0.,1e12],[1e-12,0.],[1.,1e12]]
    d['parent_operation']='POST /observed/operation/'+'long-name/'*12
    contract=source_contract()
    out=path(c['results'])/'qualification/boundary_single_zero_extreme'/contract['renderer']['sha256'][:12]
    for a in (exps.P,exps.K):
        if not (out/a/'manifest.json').exists():render_arm(packet,c,a,out/a)
    for a in (exps.P,exps.K):inspect_profile(out/a,packet,c,a,contract)
    assert WithoutGlyphs((out/exps.P/'dashboard.html').read_text()).events==WithoutGlyphs((out/exps.K/'dashboard.html').read_text()).events
    return {'synthetic_not_eval':True,'directory':str(out.relative_to(ROOT)),'checks':['single relation','zero','extreme','long operation','p50/p95']}


def cpu(c,smoke=False):
    if smoke:raise ValueError('This revision qualifies the complete220 only')
    from .main import render_arm
    from RQs.RQ3_3.src.utils import OfflineTokens
    from RQs.RQ3_12.src.tests import checkpoint_audit
    from RQs.RQ3_15.src import exps as original
    from RQs.RQ3_8.src.main import render_capture
    started=time.monotonic();contract=source_contract();q=path(c['results'])/'qualification'
    assert read_json(q/'static.json')['source_contract']==contract
    gates.require_renderer_build();loaded,spec=runtime(c)
    assert spec['max_model_len']==40960 and spec['gpu_memory_utilization']==.75
    checks=unit_tests(c);tokens=OfflineTokens({'unified':{'vllm':str(loaded.source)},'models':[MODEL]})
    root=path(c['preparation']);reg=register(c);inventory=[];rows=[];bindings=0;redraws=[];profiles=0;fallback=0
    fixed={r['opaque_incident_id'] for r in reg['smoke']}
    source_rows=source_oracle(c)
    write_json(q/'historical_variance_context.json',historical_variance())
    for row in reg['cases']:
        if time.monotonic()-started>c['cpu_seconds']:raise TimeoutError('CPU qualification budget exceeded')
        oid=row['opaque_incident_id'];base=read_json(path(c['base_preparation'])/'public'/(oid+'.json'))
        public=read_json(root/'public'/(oid+'.json'));marker=read_json(root/'flags'/(oid+'.json'))
        assert marker['status']=='done' and marker['version']==VERSION
        assert marker['parent_public_sha256']==sha_file(path(c['base_preparation'])/'public'/(oid+'.json'))
        for category in ('public','private'):assert sha_file(root/category/(oid+'.json'))==marker[category+'_sha256']
        rebuilt=exps.compile_public(base,c)
        assert {k:v for k,v in public.items() if k!='images'}=={k:v for k,v in rebuilt.items() if k!='images'}
        assert public['payload']==base['payload'] and public['candidates']==base['candidates'] and public['system']==base['system']
        base['ground_truth']='do not leak';base['anomal']=True;assert exps.compile_public(base,c)==rebuilt
        exps.visible_audit(public);applicable=bool(public['payload']['relations'])
        if applicable:
            for a in (exps.P,exps.K):bindings+=inspect_profile((root/public['images'][a]['path']).parent,public['readout'],c,a,contract)
            first=(root/public['images'][exps.P]['path']).with_suffix('.html')
            second=(root/public['images'][exps.K]['path']).with_suffix('.html')
            assert WithoutGlyphs(first.read_text()).events==WithoutGlyphs(second.read_text()).events
            assert public['images'][exps.P]==public['images'][exps.FP]==public['images'][exps.R]
            assert public['images'][exps.K]==public['images'][exps.FK] and public['images'][exps.S]==public['images'][exps.FS]
            assert sha_file(root/public['images'][exps.S]['path'])==base['images']['MARGINAL_FIVE']['sha256']
            profiles+=2
            if oid in fixed:
                for a in (exps.P,exps.K):
                    with tempfile.TemporaryDirectory(prefix='rq318-redraw-') as tmp:
                        render_arm(public['readout'],c,a,Path(tmp)/a)
                        assert sha_file(Path(tmp)/a/'dashboard.png')==public['images'][a]['sha256']
                        redraws.append({'case':oid,'arm':a,'identical':True})
                # Re-execute unchanged historical marginal component through unified renderer.
                with tempfile.TemporaryDirectory(prefix='rq318-compat-') as tmp:
                    out=Path(tmp);e,_,_,d,_=original.design_for(public['payload'],c,'MARGINAL_VISUAL')
                    write_json(out/'e.json',e);write_json(out/'d.json',d)
                    render_capture(out/'e.json',out/'d.json',out/'render')
                    assert sha_file(out/'render/dashboard.png')==base['images']['MARGINAL_FIVE']['sha256']
                    redraws.append({'case':oid,'arm':'historical_marginal','identical':True})
        else:
            assert not public['images'];fallback+=1
            assert sum(public['canonical_arms'][a]!=a for a in ARMS)==7
        cache={};inputs={};requests={}
        for a in ARMS:
            entry=public['images'].get(a);png=(root/entry['path']).read_bytes() if entry else None
            if entry:assert hashlib.sha256(png).hexdigest()==entry['sha256']
            parts=exps.parts_for(public,a,png)
            signature=stable_hash([{**p,'png':hashlib.sha256(p['png']).hexdigest()} if 'png' in p else p for p in parts])
            if signature not in cache:cache[signature]=tokens.count(parts,public['system'],MODEL)
            inputs[a]=cache[signature];requests[a]=signature
            assert inputs[a]+8192<=40960
            inventory.append({'case':oid,'dataset':row['dataset'],'arm':a,'input_tokens':inputs[a],
                'parts_hash':signature,'system_hash':stable_hash(public['system']),'png':entry,
                'logical_key':logical_key(oid,a),'canonical_arm':public['canonical_arms'][a],
                'independent_repeat':a in exps.REPEATS,'applicable':applicable})
        for a,b in ((exps.TR,exps.T),(exps.FR,exps.F),(exps.R,exps.FP)):
            assert requests[a]==requests[b] and logical_key(oid,a)!=logical_key(oid,b)
        assert inputs[exps.S]==inputs[exps.P]==inputs[exps.K]
        assert inputs[exps.FS]==inputs[exps.FP]==inputs[exps.FK]
        rows.append({'case':oid,'dataset':row['dataset'],'inputs':inputs,'applicable':applicable})
    ratios={}
    for dataset in c['case_counts']:
        selected=[r for r in rows if r['dataset']==dataset];base=sum(r['inputs'][exps.T] for r in selected)
        ratios[dataset]={a:sum(r['inputs'][a] for r in selected)/base for a in ARMS}
        assert all(v<=c['readiness']['max_mean_text_input_ratio'] for v in ratios[dataset].values())
        assert sum(r['applicable'] for r in selected)/len(selected)>=c['method']['minimum_dataset_applicability']
    fixture=boundary_checks(c,read_json(root/'public'/(reg['smoke'][0]['opaque_incident_id']+'.json')))
    lifecycle=lifecycle_tests(c);checkpoint=checkpoint_audit(loaded)
    assert contract==source_contract()
    write_json(q/'input_inventory.json',inventory)
    report={'status':'passed','source_contract':contract,'seconds':time.monotonic()-started,'cases':rows,'checks':checks,
        'positions':len(inventory),'applicability':{d:sum(r['applicable'] for r in rows if r['dataset']==d) for d in c['case_counts']},
        'fallback_cases':fallback,'fallback_references':fallback*7,'new_pngs':profiles,'reused_pngs':sum(r['applicable'] for r in rows),
        'bindings':bindings,'redraws':redraws,'source_oracle':source_rows,'source_scope':'3 fixed source recomputations; all220 frozen public packets checked; historical full-source qualification inherited',
        'maximum_input':max(v['input_tokens'] for v in inventory),'mean_input_ratios_vs_T':ratios,'checkpoint_audit':checkpoint,
        'lifecycle':lifecycle,'boundary_fixture':fixture,'new_model_calls':0,'gpu_smoke':'not_run','formal':'not_started'}
    write_json(q/'cpu.json',report);examples(c)
    return {k:v for k,v in report.items() if k not in {'source_contract','cases','checkpoint_audit'}}


def examples(c):
    reg=register(c);root=path(c['preparation']);selected={r['opaque_incident_id']:'fixed '+r['dataset'] for r in reg['smoke']}
    publics={r['opaque_incident_id']:read_json(root/'public'/(r['opaque_incident_id']+'.json')) for r in reg['cases']}
    applicable=[oid for oid,p in publics.items() if p['payload']['relations']]
    selected[max(applicable,key=lambda oid:max(len(r['parent_operation'])+len(r['child_operation']) for r in publics[oid]['payload']['relations']))]='long operation'
    selected[max(applicable,key=lambda oid:max(v for r in publics[oid]['readout']['relations'] for pair in r['data']['quantiles'] for v in pair))]='extreme'
    selected[min(applicable,key=lambda oid:sum(sum(r['data']['support']) for r in publics[oid]['readout']['relations']))]='sparse support'
    absent=[oid for oid,p in publics.items() if not p['payload']['relations']]
    if absent:selected[sorted(absent)[0]]='text fallback'
    out=root/'examples';out.mkdir(exist_ok=True);index=[];html=['<!doctype html><meta charset="utf-8"><title>RQ3.18 examples</title><h1>RQ3.18 — population readout</h1><p>Text arms and unavailable pairs have no dashboard. The complete request text is linked.</p>']
    for oid,reason in selected.items():
        public=publics[oid];row=next(r for r in reg['cases'] if r['opaque_incident_id']==oid)
        html.append(f'<h2>{escape(row["dataset"])} {escape(oid)} — {escape(reason)}</h2>')
        for arm in ARMS:
            entry=public['images'].get(arm);text=out/(oid+'__'+arm+'.txt')
            text.write_text(public['system']+'\n\n'+(exps.VISUAL_GUIDE+'\n\n' if entry else '')+'\n\n'.join(p['text'] for p in public['texts'][arm]))
            href=os.path.relpath(root/entry['path'],out) if entry else None
            html.append(f'<h3>{arm}</h3><a href="{text.name}">Full model-visible text</a>')
            if href:html.append(f'<p><a href="{escape(href)}"><img src="{escape(href)}" width="840"></a></p>')
            else:html.append('<p>Text-only input.</p>')
            index.append({'case':oid,'dataset':row['dataset'],'arm':arm,'selection_reason':reason,'image':href,'text':text.name})
    (out/'index.html').write_text('\n'.join(html));write_json(out/'index.json',index)
    return {'status':'written','examples':len(index),'cases':len(selected),'index':str(out/'index.html')}
