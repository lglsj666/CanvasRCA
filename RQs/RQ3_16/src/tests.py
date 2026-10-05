"""CPU qualification of the prospective adapter, controls and full frozen roster."""
from collections import defaultdict
from copy import deepcopy
from html.parser import HTMLParser
from pathlib import Path
import math
import tempfile
import time
from . import exps
from .utils import ARMS,MODEL,VERSION,path,register,runtime,source_contract,read_json,write_json,sha_file,stable_hash,flag,logical_key
from RQs.RQ3_14.src.tests import DOM


class WithoutSamples(HTMLParser):
    """Canonical HTML event stream after removing only bound sample groups."""
    def __init__(self,text):
        super().__init__(convert_charrefs=True);self.events=[];self.depth=0;self.feed(text)

    def handle_starttag(self,tag,attrs):
        if self.depth:
            self.depth+=1;return
        if '.sample.' in dict(attrs).get('data-binding',''):
            self.depth=1;return
        self.events.append(('start',tag,tuple(attrs)))

    def handle_endtag(self,tag):
        if self.depth: self.depth-=1;return
        self.events.append(('end',tag))

    def handle_data(self,data):
        if not self.depth and data.strip(): self.events.append(('text',data))

    def handle_startendtag(self,tag,attrs):
        if not self.depth: self.events.append(('empty',tag,tuple(attrs)))


def numeric_regression(c):
    """Re-run synthetic pairing boundary tests and the independent NumPy oracle."""
    import numpy as np
    import pandas as pd
    from RQs.RQ3_15.src.tests import fixture,oracle
    parent=exps.parent;f=fixture();mapping={'a':'123','b':'456'};ops={'parent':'parent','child':'child'}
    clock={'origin':-24.,'split':24.,'duration':48.}
    def run(frame,scale=.001): return parent.extract(frame,mapping,ops,clock,scale,c)
    packet,audit=run(f);assert oracle(packet,audit,f,.001,c)==48
    assert packet['relations'][0]['phases']['current']['points'][0]==[25.,49.]
    duplicate=pd.concat([f,f.iloc[[0]]],ignore_index=True)
    assert run(duplicate)[0]['relations'][0]['phases']['reference']['n']==23
    cyclic=f.copy();cyclic.loc[0,'parent_span_id']='c';assert run(cyclic)[1]['counts']['cyclic_rows']==2
    missing=f.copy();missing.loc[1,'duration_ms']=np.nan
    assert run(missing)[0]['relations'][0]['phases']['reference']['n']==23
    zero=f.copy();zero.loc[:1,'duration_ms']=0
    assert [0.,0.] in run(zero)[0]['relations'][0]['phases']['reference']['points']
    longer=pd.concat([f,pd.DataFrame([['t0','p2','',-24.,999999.,'a','parent']],columns=parent.TRACE_COLUMNS)],ignore_index=True)
    assert run(longer)[0]['relations'][0]['phases']['reference']['n']==23
    for multiplier,scale in [(0.001,1),(1000,.000001)]:
        altered=f.copy();altered['duration_ms']*=multiplier;assert run(altered,scale)[0]==packet
    skew=f.copy();skew.loc[skew.span_id=='c','timestamp']+=10000;assert run(skew)[0]==packet
    labels=f.copy();labels['anomal']=True;labels['ground_truth']='secret';assert run(labels)==run(f)
    assert not run(f.iloc[:10])[0]['relations']
    for n in (1,2,20,32,33,100,103):
        indices=parent.sampled_indices(n,32)
        assert len(indices)==len(set(indices))==min(n,32) and indices[0]==0 and indices[-1]==n-1
    return 'Inherited extractor synthetic edge cases and independent 48-pair numerical oracle'


def unit_tests(c):
    import numpy as np
    from unittest.mock import patch
    from RQs.RQ2.src.exps import rca_schema
    from . import gates,main
    checks=[numeric_regression(c)]
    base=rca_schema()
    for arm in ARMS:
        actual=exps.schema_for(arm,base);modified=deepcopy(base)
        if arm in exps.FIVE: modified['json_schema']['schema']['properties']['services']['minItems']=5
        assert actual==modified and base==rca_schema()
    with tempfile.TemporaryDirectory(prefix='rq316-commit-') as tmp:
        root=Path(tmp);key=logical_key('case','MARGINAL_FIVE')
        write_json(root/'flags'/(key+'.json'),{'case':'case','arm':'MARGINAL_FIVE','status':'done','call_key':'abc'})
        assert flag(root,'case','MARGINAL_FIVE') is None
        write_json(root/'completed/abc.json',{'status':'complete'});assert flag(root,'case','MARGINAL_FIVE')['status']=='done'
        phase=root/'smoke'/('phase_complete.'+MODEL+'.json');write_json(phase,{'status':'complete'})
        fail=AssertionError('Completed phase must not load a context, qualify or start a server')
        with patch.object(main,'path',return_value=root),patch.object(main,'register',side_effect=fail),\
                patch.object(main,'runtime',side_effect=fail),patch.object(main.subprocess,'Popen',side_effect=fail),\
                patch.object(gates,'require_qualification',side_effect=fail):
            assert main.run(c,True)['resumed_complete_phase']
            assert main.supervise(c,True)['launched_model'] is False
    try: gates.full_authorized(c,None)
    except RuntimeError: pass
    else: raise AssertionError('Formal gate opened')
    assert logical_key('x','MARGINAL_REPEAT')!=logical_key('x','MARGINAL_FIVE')
    assert exps.REPEATS=={'MARGINAL_REPEAT'}
    stats=gates.paired([0,0,0]);assert stats['p']==1 and stats['dz'] is None
    # Four distinct absolute ranks: five of the 16 sign assignments have
    # rank sum <=3; the two-sided exact probability is 10/16.
    assert gates.paired([.1,.2,-.3,.4])['p']==.625
    p=gates.holm([{'p':.01},{'p':.04},{'p':.03},{'p':None}]);np.testing.assert_allclose([r['holm_p'] for r in p[:3]],[.04,.09,.09])
    cases=[]
    for i,values in enumerate(([1,.5,.5,0],[0,None,1,None])):
        arms=dict(zip(c['secondary_interaction'],values))
        cases.append({'case':str(i),'dataset':'test','event_group':str(i),'arms':{a:{'metrics':None if v is None else {'mrr':v}} for a,v in arms.items()}})
    x=gates.contrast(cases,c['secondary_interaction'])
    assert x['case']['n']==1 and x['case']['delta']==0
    np.testing.assert_allclose(x['full_denominator_bounds'],[-1.,0.])
    for row in cases:
        for item in row['arms'].values(): item['metrics']=None
    assert gates.contrast(cases,c['secondary_interaction'])['full_denominator_bounds']==[-2.,2.]
    synthetic=[{'case':d,'dataset':d,'event_group':'event','arms':{a:{'metrics':{'mrr':.5,'ac@5':1.}} for a in ARMS}} for d in c['case_counts']]
    families=gates.statistical_families(c,synthetic)
    assert {k:len(v) for k,v in families.items()}=={'primary_mrr':4,'secondary_mrr':7,'secondary_ac5':7}
    assert all(v[level]['holm_p']==1. for family in families.values() for v in family for level in ('case','event_group'))
    from renderer.utils import compile_design
    packet=exps.parent.extract(__import__('RQs.RQ3_15.src.tests',fromlist=['fixture']).fixture(),{'a':'123','b':'456'},
                              {'parent':'parent','child':'child'},{'origin':-24.,'split':24.,'duration':48.},.001,c)[0]
    evidence,_,_,design,_=exps.design_for(packet,c,'MARKLESS_FIVE');compiled=compile_design(evidence,design)
    assert compiled['suppressed_visual_bindings'] and all('.sample.' in s for s in compiled['suppressed_visual_bindings'])
    wrong=deepcopy(design)
    def change(node):
        if node['type']=='panel': node['component']='trace_joint.scatter'
        else:
            for child in node['children']: change(child)
    change(wrong['tree'])
    try: compile_design(evidence,wrong)
    except ValueError: pass
    else: raise AssertionError('Unimplemented joint ablation accepted')
    checks.extend(['Schema differs only at services.minItems; base objects immutable',
                   'Atomic call and phase resume skip before any materialization/model launch',
                   'Full gate closed and independent repeat identities',
                   'Holm/all-zero Pratt and four-arm unknown bounds independently checked',
                   'Registered marginal-only glyph suppression and rejected unsupported component'])
    return checks


def inspect_markless(folder,original,packet,c,contract):
    from PIL import Image
    from renderer.utils import compile_design
    evidence,_,ops,design,op_audit=exps.design_for(packet,c,'MARKLESS_FIVE')
    m=read_json(folder/'manifest.json');src=folder.parent/(folder.name+'_design')
    assert m['status']=='passed' and not m['audit']['issues']
    assert m['png_sha256']==sha_file(folder/'dashboard.png') and m['html_sha256']==sha_file(folder/'dashboard.html')
    assert m['renderer_source']==contract['renderer'] and m['bundle_sha256']==contract['files']['src/renderer/web/dist/render.mjs']
    assert read_json(folder/'evidence.json')==evidence and read_json(folder/'design.json')==design
    assert read_json(src/'operations.json')==ops and read_json(src/'operations_audit.json')==op_audit
    compiled=compile_design(evidence,design)
    assert m['suppressed_visual_bindings']==compiled['suppressed_visual_bindings']
    assert len(compiled['suppressed_visual_bindings'])==sum(len(card['data']['samples']) for card in evidence['cards'])
    dom=DOM((folder/'dashboard.html').read_text())
    assert not any(n['tag']=='circle' or '.sample.' in n['attrs'].get('data-binding','') for n in dom.nodes)
    assert WithoutSamples((folder/'dashboard.html').read_text()).events==WithoutSamples((original/'dashboard.html').read_text()).events
    with Image.open(folder/'dashboard.png') as im:
        im.load();assert im.size==(c['canvas']['width'],c['canvas']['height']) and not im.info
    return len(m['audit']['bindings'])


def cpu(c,smoke=False):
    started=time.monotonic();checks=unit_tests(c)
    from .gates import require_renderer_build
    from .main import render_arm
    from RQs.RQ3_3.src.utils import OfflineTokens
    from RQs.RQ3_12.src.tests import checkpoint_audit
    from RQs.RQ3_15.src.tests import inspect_render
    require_renderer_build();loaded,spec=runtime(c)
    tokens=OfflineTokens({'unified':{'vllm':str(loaded.source)},'models':[MODEL]})
    root=path(c['preparation']);parent=path(c['base_preparation']);reg=register(c)
    rows=reg['smoke' if smoke else 'cases'];contract=source_contract()
    inherited_file=path('RQs/RQ3_15/results/request_joint_v1/qualification/cpu.json')
    inherited=read_json(inherited_file)
    assert inherited['status']=='passed' and inherited['case_ids']==[r['opaque_incident_id'] for r in reg['cases']]
    old_contract=read_json(path('RQs/RQ3_15/results/request_joint_v1/qualification/source_freeze.json'))['source_contract']
    cases=[];ratios=defaultdict(list);png_checks=bindings=0;rerenders=[];fallback_references=0
    smoke_ids={r['opaque_incident_id'] for r in reg['smoke']}
    for row in rows:
        if time.monotonic()-started>c['cpu_seconds']: raise TimeoutError('CPU qualification budget')
        oid=row['opaque_incident_id'];marker=read_json(root/'flags'/(oid+'.json'));public=read_json(root/'public'/(oid+'.json'))
        assert marker['status']=='done' and marker['version']==VERSION
        for cat in ('public','private'): assert sha_file(root/cat/(oid+'.json'))==marker[cat+'_sha256']
        base=read_json(parent/'public'/(oid+'.json'));old_marker=read_json(parent/'flags'/(oid+'.json'))
        assert old_marker['public_sha256']==sha_file(parent/'public'/(oid+'.json'))==marker['parent_public_sha256']
        rebuilt=exps.compile_public(base,c);assert {k:v for k,v in public.items() if k!='images'}=={k:v for k,v in rebuilt.items() if k!='images'}
        label_variant=deepcopy(base);label_variant['ground_truth']='arbitrary private value';label_variant['anomal']=True
        assert exps.compile_public(label_variant,c)==rebuilt
        assert public['system']==base['system'] and public['candidates']==base['candidates']
        assert public['texts']['BASE_FLEX']==base['texts']['BASE_TEXT'] and public['texts']['PAIR_FLEX']==base['texts']['PAIR_TEXT']
        saved=read_json(root/'audit'/(oid+'.json'))
        assert saved['parent_audit_sha256']==sha_file(parent/'audit'/(oid+'.json')) and saved['source_public_sha256']==sha_file(parent/'public'/(oid+'.json'))
        exps.visible_audit(public)
        applicable=bool(public['payload']['relations'])
        assert len(public['images'])==(4 if applicable else 0)
        if applicable:
            original=(parent/base['images']['MARGINAL_VISUAL']['path']).parent
            actual=root/public['images']['MARGINAL_FIVE']['path']
            assert sha_file(actual)==base['images']['MARGINAL_VISUAL']['sha256']
            assert all(public['images'][a]==public['images']['MARGINAL_FIVE'] for a in ('MARGINAL_FLEX','MARGINAL_REPEAT'))
            bindings+=inspect_render(original,public['payload'],c,'MARGINAL_VISUAL',old_contract)
            folder=(root/public['images']['MARKLESS_FIVE']['path']).parent
            bindings+=inspect_markless(folder,original,public['payload'],c,contract);png_checks+=2
            if oid in smoke_ids and not smoke:
                for arm in ('MARGINAL_FIVE','MARKLESS_FIVE'):
                    with tempfile.TemporaryDirectory(prefix='rq316-rerender-') as tmp:
                        out=Path(tmp)/arm;render_arm(public['payload'],c,arm,out)
                        target=actual if arm=='MARGINAL_FIVE' else folder/'dashboard.png'
                        assert sha_file(out/'dashboard.png')==sha_file(target)
                        rerenders.append({'case':oid,'arm':arm,'png_sha256':sha_file(target)})
        else:
            assert all(public['canonical_arms'][a] in {'BASE_FLEX','BASE_FIVE','MARGINAL_REPEAT'} for a in ARMS)
            fallback_references+=sum(public['canonical_arms'][a]!=a for a in ARMS)
        inputs={};cache={};excluded={}
        for arm in ARMS:
            im=public['images'].get(arm);png=(root/im['path']).read_bytes() if im else None
            if im: assert sha_file(root/im['path'])==im['sha256']
            parts=exps.parts_for(public,arm,png)
            signature=stable_hash([{**p,'png':stable_hash(p['png'])} if 'png' in p else p for p in parts])
            if signature not in cache: cache[signature]=tokens.count(parts,public['system'],MODEL)
            inputs[arm]=cache[signature]
            if inputs[arm]+c['max_tokens']>spec['max_model_len']: excluded[arm]='intact input exceeds context'
        assert inputs['MARGINAL_FIVE']==inputs['MARKLESS_FIVE']==inputs['MARGINAL_REPEAT']
        ratios[row['dataset']].append((inputs['MARGINAL_FIVE'],inputs['BASE_FIVE'],inputs['PAIR_FIVE']))
        marker['context_excluded']=excluded
        if marker['preparation_source_contract']!=contract:
            marker.setdefault('cpu_requalified_source_history',[]).append(stable_hash(marker['preparation_source_contract']))
            marker['preparation_source_contract']=contract
        write_json(root/'flags'/(oid+'.json'),marker)
        cases.append({'case':oid,'dataset':row['dataset'],'inputs':inputs,'context_excluded':excluded,
                      'relations':len(public['payload']['relations']),'candidates':len(public['candidates'])})
        if len(cases)%10==0: print('CPU checked',len(cases),'/',len(rows),flush=True)
    assert source_contract()==contract,'Source changed during CPU regression'
    ratios={d:{'visual_base':sum(v for v,b,t in rs)/sum(b for v,b,t in rs),'visual_pair':sum(v for v,b,t in rs)/sum(t for v,b,t in rs)} for d,rs in ratios.items()}
    applicability={d:{'qualified':sum(v['dataset']==d and v['relations']>0 for v in cases),'total':sum(v['dataset']==d for v in cases)} for d in c['case_counts']}
    cost=all(v['visual_base']<=c['readiness']['max_mean_base_input_ratio'] and v['visual_pair']<=c['readiness']['max_mean_pair_input_ratio'] for v in ratios.values())
    coverage=smoke or applicability==inherited['applicability']
    if not smoke: assert fallback_references==45
    passed=(smoke or cost) and coverage and not any(v['context_excluded'] for v in cases)
    checkpoint=checkpoint_audit(loaded) if not smoke else read_json(path(c['results'])/'qualification/cpu.json')['checkpoint_audit']
    report={'status':'passed' if passed else 'failed','source_contract':contract,'checks':checks,
            'case_ids':[r['opaque_incident_id'] for r in rows],'per_case':cases,'readiness_passed':passed,
            'dataset_input_ratios':ratios,'applicability':applicability,'cost_passed':cost,'applicability_passed':coverage,
            'max_input_tokens':max(v for r in cases for v in r['inputs'].values()),'actual_png_checks':png_checks,
            'actual_bindings_checked':bindings,'fallback_references':fallback_references,'deterministic_rerenders':rerenders,
            'inherited_numeric_qualification':{'file':str(inherited_file),'sha256':sha_file(inherited_file),
                'source_pairs_verified_in_predecessor':inherited['independently_checked_source_pairs'],'raw_data_reprocessed_this_run':False},
            'checkpoint_audit':checkpoint,'seconds':time.monotonic()-started,'gpu_calls':0}
    write_json(path(c['results'])/'qualification'/('cpu_smoke.json' if smoke else 'cpu.json'),report)
    if not passed: raise RuntimeError('Registered CPU gate failed; stop before GPU')
    return {k:v for k,v in report.items() if k not in {'source_contract','per_case','checkpoint_audit'}}
