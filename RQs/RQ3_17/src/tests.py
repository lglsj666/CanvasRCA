"""Full-roster CPU and actual-render qualification; no model correctness gate."""
from collections import defaultdict
from copy import deepcopy
from html.parser import HTMLParser
from pathlib import Path
import json
import tempfile
import time
from . import exps
from .utils import ARMS,MODEL,VERSION,path,register,runtime,source_contract,read_json,write_json,sha_file,stable_hash,flag,logical_key
from RQs.RQ3_16.src.tests import WithoutSamples,numeric_regression


class WithoutConnectors(HTMLParser):
    def __init__(self,text):
        super().__init__(convert_charrefs=True);self.events=[];self.depth=0;self.feed(text)
    def handle_starttag(self,tag,attrs):
        if self.depth: self.depth+=1;return
        values=dict(attrs)
        if values.get('id')=='relation-binding-overlay' or values.get('data-relation-color-generated')=='true': self.depth=1;return
        original=json.loads(values.pop('data-relation-color-original','{}'))
        values.pop('data-relation-color',None)
        for k,v in original.items():
            if v is None: values.pop(k,None)
            else: values[k]=v
        self.events.append(('start',tag,tuple(sorted(values.items()))))
    def handle_endtag(self,tag):
        if self.depth: self.depth-=1;return
        self.events.append(('end',tag))
    def handle_data(self,data):
        if not self.depth and data.strip(): self.events.append(('text',data))
    def handle_startendtag(self,tag,attrs):
        if not self.depth:self.events.append(('empty',tag,tuple(attrs)))


def scheduler_regression(c):
    """Exercise production two-phase scheduler and terminal fast resume without inference."""
    from unittest.mock import patch
    from . import main,gates
    rows=[{'opaque_incident_id':'case'+str(i),'dataset':'aiops2022','leakage_group':str(i)} for i in range(3)]
    with tempfile.TemporaryDirectory(prefix='rq317-phases-') as temp:
        root=Path(temp);prep=root/'prep';results=root/'results';called=[]
        local={**c,'preparation':str(prep),'results':str(results),'concurrency':2}
        for row in rows:
            oid=row['opaque_incident_id'];pub={'canonical_arms':{a:a for a in ARMS}}
            if oid=='case0': pub['canonical_arms'][exps.G]=exps.C
            write_json(prep/'public'/(oid+'.json'),pub);write_json(prep/'private'/(oid+'.json'),{})
            write_json(prep/'flags'/(oid+'.json'),{'canonical_arms':pub['canonical_arms'],'context_excluded':{},
                      'public_sha256':sha_file(prep/'public'/(oid+'.json')),'private_sha256':sha_file(prep/'private'/(oid+'.json'))})
        def execute(config,row,arm,public,folder,ledger):
            if arm not in {exps.C,exps.CN}: assert (folder/'dispatch_phase_0.json').exists()
            key=logical_key(row['opaque_incident_id'],arm);called.append((row['opaque_incident_id'],arm))
            write_json(folder/'completed'/(key+'.json'),{'status':'complete'})
            v={'status':'done','case':row['opaque_incident_id'],'arm':arm,'logical_key':key,'call_key':key}
            write_json(folder/'flags'/(key+'.json'),v);return v
        def summary(config,smoke=False):
            complete=all(flag(results/'formal',r['opaque_incident_id'],a) for r in rows for a in ARMS)
            return {'status':'complete' if complete else 'incomplete'}
        with patch.object(main,'path',side_effect=Path),patch.object(main,'register',return_value={'cases':rows}),\
             patch.object(main,'runtime'),patch.object(gates,'require_qualification'),patch.object(gates,'require_runtime_attestation'),\
             patch.object(gates,'summarize',side_effect=summary),patch.object(main,'execute',side_effect=execute):
            assert main.run(local)['status']=='complete'
            assert all(a in {exps.C,exps.CN} for _,a in called[:6]) and len(called)==41
            assert main.run(local)['resumed_complete_phase'] and len(called)==41
        marker=results/'formal/dispatch_phase_0.json';assert read_json(marker)['positions']==6
    return 'Production scheduler: all combinations committed before controls; aliases and completed-phase resume'


def unit_tests(c):
    import numpy as np
    from RQs.RQ2.src.exps import rca_schema
    from renderer.utils import compile_design,membership_layout
    from . import gates
    checks=[numeric_regression(c),scheduler_regression(c)]
    for arm in ARMS:
        schema=exps.schema_for(arm,rca_schema());assert schema['json_schema']['schema']['properties']['services']['minItems']==5
    assert exps.REPEATS=={exps.R,exps.RN} and logical_key('x',exps.R)!=logical_key('x',exps.C)
    assert logical_key('x',exps.RN)!=logical_key('x',exps.CN)
    assert gates.paired([0,0])['p']==1 and gates.paired([.1,.2,-.3,.4])['p']==.625
    np.testing.assert_allclose([v['holm_p'] for v in gates.holm([{'p':.01},{'p':.04},{'p':.03},{'p':None}])[:3]],[.04,.09,.09])
    syn=[{'case':d,'dataset':d,'event_group':d,'arms':{a:{'metrics':{'mrr':.5,'ac@5':1}} for a in ARMS}} for d in c['case_counts']]
    families=gates.statistical_families(c,syn)
    assert {k:len(v) for k,v in families.items()}=={'primary_mrr':6,'secondary_mrr':9,'secondary_ac5':9,'layout_mrr':5,'node_mechanism_mrr':6}
    assert all(v[level]['holm_p']==1 for values in families.values() for v in values for level in ('case','event_group'))
    for row in syn:
        for a in ARMS: row['arms'][a]['metrics']=None
    assert gates.contrast(syn,c['secondary_interaction'])['full_denominator_bounds']==[-2,2]
    source=read_json(path(c['base_preparation'])/'public'/'INC-37ABFB78A80E.json')
    public=exps.compile_public(source,c);e,_,_,design,_=exps.design_for(public['topology'],c,exps.C)
    compile_design(e,design)
    for mutation in ('reverse','duplicate','missing'):
        wrong=deepcopy(design)
        if mutation=='reverse':
            wrong_e=deepcopy(e);edge=next(x for g in wrong_e['cards'] if g['id']=='CALLS' for x in g['data']['edges'] if x['id']==wrong['relation_bindings'][0]['edge']);edge['source'],edge['target']=edge['target'],edge['source']
        else:
            wrong_e=e
            if mutation=='duplicate': wrong['relation_bindings'].append(wrong['relation_bindings'][0])
            else: wrong['relation_bindings'][0]['edge']='e999999'
        try:compile_design(wrong_e,wrong)
        except ValueError:pass
        else:raise AssertionError('Invalid relation binding accepted: '+mutation)
    variant=deepcopy(source);variant['ground_truth']='123';variant['anomal']=True
    assert exps.compile_public(variant,c)==public
    empty=deepcopy(source);empty['payload']['relations']=[]
    fallback=exps.compile_public(empty,c);assert not exps.available(fallback,exps.D) and exps.available(fallback,exps.C)
    for card in public['topology']['graph_cards']:
        if card['id']=='DEPLOY': assert membership_layout(card,1400)['cell_width']>=22
    # Duplicate observations do not create extra unique edges; self-loops and
    # multiple public edge types remain distinct directed facts.
    parts=deepcopy(source['texts']['PAIR_FIVE'])
    block=next(p for p in parts if p.get('text','').startswith('Additional component facts'))
    prefix,body=block['text'].split('\n',1);table=json.loads(body)
    records=[dict(zip(table['columns'],r)) for r in table['rows']]
    graph=next(r for r in records if r['kind']=='graph' and r['data']['edges'])
    edge=graph['data']['edges'][0];graph['data']['edges'] += [edge,[edge[0],edge[0],'calls']]
    block['text']=prefix+'\n'+json.dumps(table)
    edges,_=exps.graph_ledger(parts)
    assert len(edges)==len(set(edges)) and (edge[0],edge[0],'calls') in edges
    # One real public relation is a CPU-only structural fixture, not a changed roster input.
    fixture=deepcopy(public['topology']);fixture['pair_packet']['relations']=fixture['pair_packet']['relations'][:1]
    fixture['relation_bindings']=fixture['relation_bindings'][:1]
    fe,_,_,fd,_=exps.design_for(fixture,c,exps.C);compile_design(fe,fd)
    assert sum(x['kind']=='trace_joint' for x in fe['cards'])==1
    checks.extend(['Exact-five schema; independent repeat identity','Pratt/Holm and unknown interaction bounds',
                   'Wrong-direction/missing/duplicate binding rejection; public label perturbation; no-pair fallback'])
    return checks


def inspect_render(folder,packet,c,arm,contract):
    from PIL import Image
    from renderer.utils import compile_design
    e,_,_,d,_=exps.design_for(packet,c,arm);m=read_json(folder/'manifest.json')
    assert m['status']=='passed' and not m['audit']['issues']
    assert m['renderer_source']==contract['renderer'] and m['bundle_sha256']==contract['files']['src/renderer/web/dist/render.mjs']
    assert m['png_sha256']==sha_file(folder/'dashboard.png') and m['html_sha256']==sha_file(folder/'dashboard.html')
    assert read_json(folder/'evidence.json')==e and read_json(folder/'design.json')==d
    scene=compile_design(e,d);assert m['expected_bindings']==scene['expected_bindings']
    links=m.get('relation_overlay',[]);assert [{k:x[k] for k in ('card','graph','edge')} for x in links]==d.get('relation_bindings',[])
    with Image.open(folder/'dashboard.png') as im: im.load();assert im.size==(d['viewport']['width'],d['viewport']['height']) and not im.info
    return m


def control_differences(root,public,node=False):
    import numpy as np
    from PIL import Image
    ca,ua,ka=(exps.CN,exps.UN,exps.KN) if node else (exps.C,exps.U,exps.K)
    folders={a:(root/public['images'][b]['path']).parent for a,b in zip((exps.C,exps.U,exps.K),(ca,ua,ka))}
    html={a:(p/'dashboard.html').read_text() for a,p in folders.items()}
    assert WithoutConnectors(html[exps.C]).events==WithoutConnectors(html[exps.U]).events
    assert WithoutSamples(html[exps.C]).events==WithoutSamples(html[exps.K]).events
    c=read_json(folders[exps.C]/'manifest.json')
    with Image.open(folders[exps.C]/'dashboard.png') as im: base=np.asarray(im.convert('RGB'))
    with Image.open(folders[exps.U]/'dashboard.png') as im: different=np.any(base!=np.asarray(im.convert('RGB')),axis=2)
    ys,xs=np.where(different);allowed=np.zeros(len(xs),dtype=bool)
    for link in c.get('relation_overlay',[]):
        for b in link.get('color_boxes',link.get('marker_boxes',[])):
            margin=32 if node else 3  # Includes scaled dashed arrowheads beyond the path endpoint.
            allowed|=(xs>=b['x']-margin)&(xs<=b['x']+b['width']+margin)&(ys>=b['y']-margin)&(ys<=b['y']+b['height']+margin)
    assert allowed.all() and len(xs)>0
    with Image.open(folders[exps.K]/'dashboard.png') as im: different=np.any(base!=np.asarray(im.convert('RGB')),axis=2)
    ys,xs=np.where(different);allowed=np.zeros(len(xs),dtype=bool)
    for b in c['audit']['bindings']:
        if '.sample.' in b['key']:
            allowed|=(xs>=b['x']-2)&(xs<=b['x']+b['width']+2)&(ys>=b['y']-2)&(ys<=b['y']+b['height']+2)
    assert allowed.all() and len(xs)>0
    return {'binding_changed_pixels':int(len(np.where(np.any(base!=np.asarray(Image.open(folders[exps.U]/'dashboard.png').convert('RGB')),axis=2))[0])),
            'sample_changed_pixels':len(xs),'html_and_pixel_scope':'only exact edge/arrowhead/card label colors or samples; geometry/text unchanged'}


def cpu(c,smoke=False):
    started=time.monotonic();checks=unit_tests(c)
    from .gates import require_renderer_build
    from .main import render_arm
    from RQs.RQ3_3.src.utils import OfflineTokens
    from RQs.RQ3_12.src.tests import checkpoint_audit
    require_renderer_build();loaded,spec=runtime(c)
    tokens=OfflineTokens({'unified':{'vllm':str(loaded.source)},'models':[MODEL]})
    root=path(c['preparation']);parent_root=path(c['base_preparation']);reg=register(c)
    rows=reg['smoke' if smoke else 'cases'];contract=source_contract();cases=[];ratios=defaultdict(list);rerenders=[];controls=[];png_checks=0
    inherited=read_json(path('RQs/RQ3_16/results/marginal_coverage_v1/qualification/cpu.json'))
    assert inherited['status']=='passed' and inherited['case_ids']==[r['opaque_incident_id'] for r in reg['cases']]
    smoke_ids={r['opaque_incident_id'] for r in reg['smoke']}
    for row in rows:
        if time.monotonic()-started>c['cpu_seconds']:raise TimeoutError('CPU budget exceeded')
        oid=row['opaque_incident_id'];marker=read_json(root/'flags'/(oid+'.json'));public=read_json(root/'public'/(oid+'.json'))
        assert marker['status']=='done' and marker['version']==VERSION
        for cat in ('public','private'):assert sha_file(root/cat/(oid+'.json'))==marker[cat+'_sha256']
        base=read_json(parent_root/'public'/(oid+'.json'));assert sha_file(parent_root/'public'/(oid+'.json'))==marker['parent_public_sha256']
        rebuilt=exps.compile_public(base,c);rebuilt['images']=public['images'];exps.finalize_aliases(rebuilt);assert rebuilt==public
        assert public['texts'][exps.B]==base['texts']['BASE_FIVE'] and public['system']==base['system'] and public['candidates']==base['candidates']
        # Independent direct expansion of the serialized columnar graph rows.
        text=next(p['text'] for p in base['texts']['PAIR_FIVE'] if p.get('text','').startswith('Additional component facts'))
        packed=json.loads(text.split('\n',1)[1]);raw=[dict(zip(packed['columns'],r)) for r in packed['rows']]
        original={tuple(e) for r in raw if r['kind']=='graph' for e in r['data']['edges']}
        assert original=={tuple(e) for e in public['topology']['ledger_edges']}
        drawn={(e['source'],e['target'],e['kind']) for g in public['topology']['graph_cards'] for e in g['data']['edges']}
        additions={(r['parent'],r['child'],'request_parent') for r in public['payload']['relations']}
        assert drawn==original|additions
        seen=set()
        for arm,im in public['images'].items():
            file=root/im['path'];assert sha_file(file)==im['sha256']
            if arm==exps.N:
                assert im['sha256']==base['images']['MARGINAL_FIVE']['sha256'];continue
            if file in seen:continue
            seen.add(file);inspect_render(file.parent,public['topology'],c,arm,contract);png_checks+=1
        if public['payload']['relations']:
            for node in (False,True): controls.append({'case':oid,'node':node,**control_differences(root,public,node)})
        if oid in smoke_ids and not smoke:
            for arm in (exps.C,exps.CN,exps.N):
                if not exps.available(public,arm):continue
                with tempfile.TemporaryDirectory(prefix='rq317-rerender-') as tmp:
                    out=Path(tmp)/arm;render_arm(public['topology'],c,arm,out)
                    assert sha_file(out/'dashboard.png')==public['images'][arm]['sha256']
                    rerenders.append({'case':oid,'arm':arm,'png_sha256':sha_file(out/'dashboard.png')})
        inputs={};cache={};excluded={}
        for arm in ARMS:
            im=public['images'].get(arm);png=(root/im['path']).read_bytes() if im else None
            parts=exps.parts_for(public,arm,png);sig=stable_hash([public['texts'][arm],im.get('sha256') if im else None])
            if sig not in cache:cache[sig]=tokens.count(parts,public['system'],MODEL)
            inputs[arm]=cache[sig]
            if inputs[arm]+c['max_tokens']>spec['max_model_len']:excluded[arm]='Intact registered request exceeds context'
            canonical=public['canonical_arms'][arm]
            if canonical!=arm:assert public['texts'][canonical]==public['texts'][arm] and public['images'].get(canonical,{}).get('sha256')==(im or {}).get('sha256')
        if public['payload']['relations']:assert len({inputs[a] for a in exps.VISUAL-{exps.N}})==1
        ratios[row['dataset']].append((inputs[exps.C],inputs[exps.B],inputs[exps.T],inputs[exps.CN]))
        marker['context_excluded']=excluded;marker['preparation_source_contract']=contract;write_json(root/'flags'/(oid+'.json'),marker)
        cases.append({'case':oid,'dataset':row['dataset'],'inputs':inputs,'context_excluded':excluded,
                      'relations':len(public['payload']['relations']),'graph_edges':len(original),'graph_cards':len(public['topology']['graph_cards']),
                      'candidates':len(public['candidates']),'fallbacks':[a for a in exps.VISUAL if not exps.available(public,a)]})
        if len(cases)%10==0:print('CPU checked',len(cases),'/',len(rows),flush=True)
    assert contract==source_contract(),'Source changed during CPU qualification'
    ratios={d:{'visual_base':sum(v for v,b,t,n in rs)/sum(b for v,b,t,n in rs),
               'visual_pair':sum(v for v,b,t,n in rs)/sum(t for v,b,t,n in rs),
               'node_base':sum(n for v,b,t,n in rs)/sum(b for v,b,t,n in rs),
               'node_pair':sum(n for v,b,t,n in rs)/sum(t for v,b,t,n in rs)} for d,rs in ratios.items()}
    applicability={d:{'qualified':sum(v['dataset']==d and v['relations']>0 and v['graph_edges']>0 for v in cases),'total':sum(v['dataset']==d for v in cases)} for d in c['case_counts']}
    cost=all(v['visual_pair']<=1.35 and v['node_pair']<=1.35 for v in ratios.values());coverage=all(v['qualified']/v['total']>=.5 for v in applicability.values())
    passed=(smoke or cost) and coverage and not any(v['context_excluded'] for v in cases)
    checkpoint=checkpoint_audit(loaded) if not smoke else read_json(path(c['results'])/'qualification/cpu.json')['checkpoint_audit']
    report={'status':'passed' if passed else 'failed','source_contract':contract,'checks':checks,'case_ids':[r['opaque_incident_id'] for r in rows],
            'per_case':cases,'readiness_passed':passed,'dataset_input_ratios':ratios,'applicability':applicability,'cost_passed':cost,
            'max_input_tokens':max(v for r in cases for v in r['inputs'].values()),'actual_png_checks':png_checks,
            'control_differences':controls,'deterministic_rerenders':rerenders,'checkpoint_audit':checkpoint,
            'inherited_numeric_qualification':{'source':'RQ3.16 complete CPU / RQ3.15 canonical pair oracle','raw_reprocessed':False},
            'seconds':time.monotonic()-started,'gpu_calls':0}
    write_json(path(c['results'])/'qualification'/('cpu_smoke.json' if smoke else 'cpu.json'),report)
    if not passed:raise RuntimeError('CPU gate failed; no GPU launch')
    return {k:v for k,v in report.items() if k not in {'source_contract','per_case','checkpoint_audit','control_differences'}}


def preview_checks(c):
    """Artifact checks for requested examples only; never complete CPU qualification."""
    from renderer.utils import compile_design, node_link_layout
    from .main import render_arm
    root=path(c['preparation']);checks=[];contract=source_contract()
    for row in register(c)['smoke']:
        oid=row['opaque_incident_id'];public=read_json(root/'public'/(oid+'.json'))
        assert public['images'][exps.C]['sha256']==public['images'][exps.R]['sha256']
        assert public['images'][exps.CN]['sha256']==public['images'][exps.RN]['sha256']
        for node,other in exps.NODE_BASE.items():
            ne,_,_,nd,_=exps.design_for(public['topology'],c,node)
            me,_,_,md,_=exps.design_for(public['topology'],c,other)
            assert ne==me and nd['viewport']==md['viewport']
            nr=compile_design(ne,nd)['rectangles'];mr=compile_design(me,md)['rectangles']
            assert [(r['card'],r['x'],r['y'],r['width'],r['height']) for r in nr]==[(r['card'],r['x'],r['y'],r['width'],r['height']) for r in mr]
            assert public['texts'][node]==public['texts'][other]==public['texts'][exps.T]
        seen=set()
        for arm,im in public['images'].items():
            folder=(root/im['path']).parent
            if arm==exps.N or folder in seen:continue
            seen.add(folder);manifest=inspect_render(folder,public['topology'],c,arm,contract)
            legend=exps.binding_legend(public['topology'])
            for link in manifest.get('relation_overlay',[]):
                expected=next(x for x in legend if x['color']==link['color'])
                assert link['style']=='color'
                assert [link['source'],link['target']]==[expected['source'],expected['target']]
                assert link['card'] in {x['card'] for x in expected['cards']}
                assert set(link['colored_bindings'])=={link['graph']+'.edge.'+link['edge'],*[link['card']+'.'+k for k in ('parent','child','parent_operation','child_operation')]}
                assert link['arrowhead_color']==(link['color'] if arm in exps.NODE_BASE else None)
            html=(folder/'dashboard.html').read_text()
            assert 'data-relation-marker=' not in html and 'id="relation-binding-overlay"' not in html
        controls=[control_differences(root,public,node) for node in (False,True)]
        checks.append({'case':oid,'dataset':row['dataset'],'encoding_fact_and_slot_parity':True,
                       'exact_color_and_arrowhead_mapping':True,'controls':controls,'independent_repeat_inputs_identical':True})
    # Default historical matrix/native rendering remains pixel-identical.
    old=path('RQs/RQ3_17/preparation/topology_marginal_v1')
    from renderer.main import render
    historical=[]
    for row in register(c)['smoke']:
        oid=row['opaque_incident_id'];public=read_json(old/'public'/(oid+'.json'))
        source=(old/public['images'][exps.G]['path']).parent
        with tempfile.TemporaryDirectory(prefix='rq317-legacy-',dir=path(c['results'])) as tmp:
            report=render(source/'evidence.json',source/'design.json',Path(tmp)/'render')
            assert report['png_sha256']==public['images'][exps.G]['sha256']
            historical.append({'case':oid,'arm':exps.G,'pixel_equal':True})
    # Old opt-in numbered semantics also remain intact in both graph encodings.
    old=path('RQs/RQ3_17/preparation/topology_marginal_v2');oid='INC-D9245047C658'
    public=read_json(old/'public'/(oid+'.json'))
    for arm in (exps.C,exps.CN):
        source=(old/public['images'][arm]['path']).parent
        with tempfile.TemporaryDirectory(prefix='rq317-v2-legacy-',dir=path(c['results'])) as tmp:
            rendered=render(source/'evidence.json',source/'design.json',Path(tmp)/'render')
            assert rendered['png_sha256']==public['images'][arm]['sha256']
            historical.append({'case':oid,'arm':arm,'pixel_equal':True,'version':'v2 numbered'})
    deterministic=[]
    public=read_json(root/'public'/'INC-37ABFB78A80E.json')
    for arm in (exps.C,exps.CN):
        with tempfile.TemporaryDirectory(prefix='rq317-color-repeat-',dir=path(c['results'])) as tmp:
            rendered=render_arm(public['topology'],c,arm,Path(tmp)/'render')
            assert rendered['png_sha256']==public['images'][arm]['sha256']
            deterministic.append({'arm':arm,'pixel_equal':True})
    report={'status':'passed','scope':'three fixed cases; requested preview regression only, not220-case CPU/GPU qualification',
            'source_contract':contract,'cases':checks,'historical_defaults':historical,'deterministic_redraw':deterministic,'gpu_calls':0}
    write_json(path(c['results'])/'qualification/preview_checks.json',report)
    return {k:v for k,v in report.items() if k!='source_contract'}


def dashed_width_checks(c):
    """Against v3: only CALLS dashes and their stroke-scaled arrowheads change."""
    from .main import render_arm
    from renderer.utils import compile_design
    import numpy as np
    from PIL import Image
    class NormalizeDashes(HTMLParser):
        def __init__(self,text,new):
            super().__init__(convert_charrefs=True);self.events=[];self.dashes=0;self.solids=0;self.new=new;self.feed(text)
        def handle_starttag(self,tag,attrs):
            a=dict(attrs)
            if a.get('class')=='graph-edge':
                if 'stroke-dasharray' in a and a.get('data-binding','').startswith('CALLS.'):
                    assert a.pop('style',None)==('stroke-width:4.2' if self.new else None)
                    self.dashes+=1
                else:
                    assert 'style' not in a;self.solids+=1
            self.events.append(('start',tag,tuple(sorted(a.items()))))
        def handle_endtag(self,tag):self.events.append(('end',tag))
        def handle_data(self,data):
            if data.strip():self.events.append(('text',data))
    root=path(c['preparation']);old=path('RQs/RQ3_17/preparation/topology_marginal_v3');rows=[]
    for r in register(c)['smoke']:
        oid=r['opaque_incident_id'];new=read_json(root/'public'/(oid+'.json'));before=read_json(old/'public'/(oid+'.json'))
        assert new['texts']==before['texts'] and new['topology']==before['topology'] and new['candidates']==before['candidates']
        for arm,im in new['images'].items():
            if arm not in exps.NODE_BASE:
                assert im['sha256']==before['images'][arm]['sha256'];continue
            folder=(root/im['path']).parent;prior=(old/before['images'][arm]['path']).parent
            a=NormalizeDashes((folder/'dashboard.html').read_text(),True)
            b=NormalizeDashes((prior/'dashboard.html').read_text(),False)
            assert a.events==b.events and a.dashes==b.dashes>0 and a.solids==b.solids
            call=next(x for x in read_json(folder/'manifest.json')['rectangles'] if x['card']=='CALLS')
            with Image.open(folder/'dashboard.png') as im: current=np.asarray(im.convert('RGB'))
            with Image.open(prior/'dashboard.png') as im: original=np.asarray(im.convert('RGB'))
            diff=np.any(current!=original,axis=2);ys,xs=np.where(diff)
            assert len(xs)>0 and ((xs>=call['x'])&(xs<call['x']+call['width'])&(ys>=call['y'])&(ys<call['y']+call['height'])).all()
            rows.append({'case':oid,'arm':arm,'dashes':a.dashes,'other_edges_unchanged':a.solids,'only_calls_dash_and_arrow_changed':True,'outside_CALLS_pixels_equal':True})
        # At scale1, default geometry and stroke-scaled arrowheads reproduce v3.
        normal=deepcopy(c);normal['canvas']['calls_dashed_width_scale']=1
        with tempfile.TemporaryDirectory(prefix='rq317-arrowheads-',dir=path(c['results'])) as tmp:
            result=render_arm(new['topology'],normal,exps.CN,Path(tmp)/'render')
            assert result['png_sha256']==before['images'][exps.CN]['sha256']
    e,_,_,d,_=exps.design_for(new['topology'],c,exps.CN)
    def panels(node):
        if node['type']=='panel':yield node
        for child in node.get('children',[]):yield from panels(child)
    for value in (0,-1,True,11,float('nan')):
        bad=deepcopy(d);next(p for p in panels(bad['tree']) if p['component']=='graph.node_link')['dashed_width_scale']=value
        try:compile_design(e,bad)
        except ValueError:pass
        else:raise AssertionError('Invalid dashed width accepted')
    report={'status':'passed','scope':'three fixed previews only','source_contract':source_contract(),'width_before':1.4,'width_after':4.2,'ratio':3,
            'comparisons':rows,'non_node_PNGs_identical':True,'deployment_unchanged':True,'arrowhead_scale1_pixel_equal_cases':3,'gpu_calls':0}
    write_json(path(c['results'])/'qualification/dashed_width_checks.json',report)
    return {k:v for k,v in report.items() if k!='source_contract'}
