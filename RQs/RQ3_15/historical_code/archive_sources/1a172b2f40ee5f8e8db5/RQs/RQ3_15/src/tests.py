"""Independent source/numeric oracles, actual PNG/DOM and whole-roster budgets."""
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
import math
import tempfile
import time
from . import exps
from .utils import ARMS,MODEL,VERSION,path,register,runtime,source_contract,read_json,write_json,sha_file,stable_hash,flag,logical_key,public_source
from RQs.RQ3_14.src.tests import DOM


def fixture():
    import pandas as pd
    rows=[]
    for i in range(48):
        t=f't{i}';time=i-24.;x=i+1.;y=2*i+1.
        rows += [[t,'p','',time,x*1000,'a','parent'],[t,'c','p',time,y*1000,'b','child']]
    return pd.DataFrame(rows,columns=exps.TRACE_COLUMNS)


def oracle(packet,audit,frame,scale,c):
    """Recompute every selected population/sampling field from source row pairs."""
    import numpy as np
    checks=0
    for r,provenance in zip(packet['relations'],audit['provenance'],strict=True):
        arrays={}
        for phase,source in provenance['phases'].items():
            positions=source['rows'];parents=frame.iloc[[p for p,ch in positions]];children=frame.iloc[[ch for p,ch in positions]]
            assert list(parents.trace_id.astype(str))==list(children.trace_id.astype(str))
            assert list(parents.span_id.astype(str))==list(children.parent_span_id.astype(str))
            xy=np.column_stack([parents.duration_ms.to_numpy(dtype=float),children.duration_ms.to_numpy(dtype=float)])*scale
            assert np.isfinite(xy).all() and (xy>=0).all()
            arrays[phase]=xy
            n=len(xy);k=min(n,c['method']['max_points_per_phase'])
            expected=np.floor(np.linspace(0,n-1,k)+.5).astype(int).tolist()
            assert expected==source['sample_indices'] and len(set(expected))==k
            assert np.all(xy[1:,0]>=xy[:-1,0])
            visible=r['phases'][phase]
            np.testing.assert_allclose(visible['points'],xy[expected],rtol=1e-12,atol=1e-12)
            np.testing.assert_allclose(visible['quantiles'],np.quantile(xy,[.5,.95],axis=0).T,rtol=1e-12,atol=1e-12)
            assert visible['n']==len(xy)
            checks+=len(xy)
        thresholds=np.quantile(arrays['reference'],.95,axis=0)
        np.testing.assert_allclose(r['thresholds'],thresholds,rtol=1e-12,atol=1e-12)
        # Use stored thresholds for exact strict-boundary semantics; independent
        # quantile calculation above tolerates only floating roundoff.
        for phase,xy in arrays.items():
            flags=xy>np.asarray(r['thresholds']);counts=[int(((flags[:,0]==a)&(flags[:,1]==b)).sum()) for a,b in ((0,0),(0,1),(1,0),(1,1))]
            assert counts==r['phases'][phase]['binary'] and sum(counts)==len(xy)
            conditional=[]
            for state in (0,1):
                values=xy[flags[:,0]==state,1]
                if len(values)>=c['method']['conditional_min']:
                    conditional.append([state,len(values),*np.quantile(values,[.5,.95]).tolist()])
            np.testing.assert_allclose(conditional,r['phases'][phase]['conditional_child'],rtol=1e-12,atol=1e-12)
    return checks


def unit_tests(c):
    import numpy as np
    import pandas as pd
    frame=fixture();mapping={'a':'123','b':'456'};ops={'parent':'parent','child':'child'}
    clock={'origin':-24.,'split':24.,'duration':48.}
    def run(f,scale=.001): return exps.extract(f,mapping,ops,clock,scale,c)
    packet,audit=run(frame);assert len(packet['relations'])==1
    assert packet['relations'][0]['phases']['reference']['n']==24
    oracle(packet,audit,frame,.001,c)
    # All traces reuse p/c identifiers. A global span join would mix48 requests.
    assert packet['relations'][0]['phases']['current']['points'][0]==[25.,49.]
    augmented=pd.concat([frame,pd.DataFrame([['t0','p2','',-24.,999999.,'a','parent']],columns=exps.TRACE_COLUMNS)],ignore_index=True)
    p,a=run(augmented);assert p['relations'][0]['phases']['reference']['n']==23 # absent child is not substituted from shorter parent
    bad=pd.concat([frame,frame.iloc[[0]]],ignore_index=True);p,a=run(bad);assert p['relations'][0]['phases']['reference']['n']==23
    cyclic=frame.copy();cyclic.loc[0,'parent_span_id']='c';p,a=run(cyclic);assert a['counts']['cyclic_rows']==2
    missing=frame.copy();missing.loc[1,'duration_ms']=np.nan;p,a=run(missing);assert p['relations'][0]['phases']['reference']['n']==23
    zero=frame.copy();zero.loc[:1,'duration_ms']=0;p,a=run(zero);assert [0.,0.] in p['relations'][0]['phases']['reference']['points']
    changed=frame.copy();changed['anomal']=True;changed['ground_truth']='secret';assert run(changed)==run(frame)
    # Unit conversions and phase boundary use observed parent timestamp, not child clock.
    ms=frame.copy();ms['duration_ms']/=1000;assert run(ms,1)[0]==packet
    ns=frame.copy();ns['duration_ms']*=1000;assert run(ns,.000001)[0]==packet
    skew=frame.copy();skew.loc[skew.span_id=='c','timestamp']+=10000;assert run(skew)[0]==packet
    short=frame.iloc[:10];assert not run(short)[0]['relations']
    for n in (1,2,20,32,33,100,103):
        indices=exps.sampled_indices(n,32);assert len(indices)==len(set(indices))==min(n,32)
        assert indices[0]==0 and indices[-1]==n-1
    with tempfile.TemporaryDirectory(prefix='rq315-marker-') as tmp:
        root=Path(tmp);key=logical_key('case','PAIR_VISUAL')
        write_json(root/'flags'/(key+'.json'),{'case':'case','arm':'PAIR_VISUAL','status':'done','call_key':'abc'})
        assert flag(root,'case','PAIR_VISUAL') is None
        write_json(root/'completed/abc.json',{'status':'complete'});assert flag(root,'case','PAIR_VISUAL')['status']=='done'
    from .gates import full_authorized
    try: full_authorized(c,None)
    except RuntimeError: pass
    else: raise AssertionError('Formal execution must remain disabled')
    assert exps.REPEATS=={'PAIR_REPEAT'}
    return ['Independent NumPy population/quantile/count/sampling oracle','Trace-scoped identity and duplicate/cycle rejection',
            'Parent selected before child availability; zero/missing/boundary and unit projections',
            'Forbidden-column perturbation and child-clock independence','Atomic commit resume; formal disabled; true repeat']


def inspect_render(folder,packet,c,arm,contract):
    from PIL import Image
    evidence,_,ops,design,op_audit=exps.design_for(packet,c,arm)
    m=read_json(folder/'manifest.json');src=folder.parent/(folder.name+'_design')
    assert m['status']=='passed' and not m['audit']['issues']
    assert m['png_sha256']==sha_file(folder/'dashboard.png') and m['html_sha256']==sha_file(folder/'dashboard.html')
    assert m['renderer_source']==contract['renderer']
    assert m['bundle_sha256']==contract['files']['src/renderer/web/dist/render.mjs']
    assert read_json(folder/'evidence.json')==evidence and read_json(folder/'design.json')==design
    assert read_json(src/'operations.json')==ops and read_json(src/'operations_audit.json')==op_audit
    with Image.open(folder/'dashboard.png') as im:
        im.load();assert im.size==(c['canvas']['width'],c['canvas']['height']) and not im.info
    dom=DOM((folder/'dashboard.html').read_text())
    for card in evidence['cards']:
        nodes=[n for n in dom.nodes if n['panel']==card['id']];samples=card['data']['samples']
        high=math.log1p(max(1,max(max(s['parent_ms'],s['child_ms']) for s in samples)))
        groups=[n for n in nodes if n['attrs'].get('data-binding','').startswith(card['id']+'.sample.')]
        assert len(groups)==len(samples)
        for i,(group,s) in enumerate(zip(groups,samples,strict=True)):
            assert group['attrs']['data-binding']==f'{card["id"]}.sample.{i}'
            assert float(group['attrs']['data-parent-ms'])==s['parent_ms'] and float(group['attrs']['data-child-ms'])==s['child_ms']
        circles=[n for n in nodes if n['tag']=='circle']
        assert len(circles)==len(samples)*(2 if arm=='MARGINAL_VISUAL' else 1)
        for i,s in enumerate(samples):
            x=90+320*math.log1p(s['parent_ms'])/high;y=354-320*math.log1p(s['child_ms'])/high
            points=circles[2*i:2*i+2] if arm=='MARGINAL_VISUAL' else circles[i:i+1]
            assert math.isclose(float(points[0]['attrs']['cx']),x,abs_tol=1e-9)
            assert math.isclose(float(points[-1]['attrs']['cy']),y,abs_tol=1e-9)
    return len(m['audit']['bindings'])


def cpu(c,smoke=False):
    started=time.monotonic();checks=unit_tests(c)
    from .gates import require_renderer_build
    from .main import render_arm
    from RQs.RQ3_3.src.utils import OfflineTokens
    from RQs.RQ3_12.src.tests import checkpoint_audit
    require_renderer_build();loaded,spec=runtime(c)
    tokens=OfflineTokens({'unified':{'vllm':str(loaded.source)},'models':[MODEL]})
    root=path(c['preparation']);reg=register(c);rows=reg['smoke' if smoke else 'cases'];contract=source_contract()
    cases=[];ratios=defaultdict(list);png_checks=bindings=source_pairs=0;rerenders=[]
    smoke_ids={r['opaque_incident_id'] for r in reg['smoke']}
    for row in rows:
        if time.monotonic()-started>c['cpu_seconds']: raise TimeoutError('CPU qualification budget')
        oid=row['opaque_incident_id'];marker=read_json(root/'flags'/(oid+'.json'));public=read_json(root/'public'/(oid+'.json'))
        assert marker['status']=='done' and marker['version']==VERSION
        for cat in ('public','private'): assert sha_file(root/cat/(oid+'.json'))==marker[cat+'_sha256']
        base=read_json(path(c['base_preparation'])/'public'/(oid+'.json'))
        f,mapping,ops,clock,scale,src=public_source(c,row,base)
        rebuilt,audit=exps.compile_public(base,f,mapping,ops,clock,scale,c)
        assert rebuilt['texts']==public['texts'] and rebuilt['payload']==public['payload']
        assert public['texts']['BASE_TEXT']==base['texts']['WINDOW_TEXT'] and public['system']==base['system']
        saved=read_json(root/'audit'/(oid+'.json'));assert saved['source']==src and saved['compiler']==audit
        source_pairs+=oracle(public['payload'],audit,f,scale,c)
        exps.visible_audit(public)
        for arm in ('PAIR_VISUAL','MARGINAL_VISUAL'):
            if arm not in public['images']: continue
            folder=(root/public['images'][arm]['path']).parent
            bindings+=inspect_render(folder,public['payload'],c,arm,contract);png_checks+=1
            if oid in smoke_ids and not smoke:
                with tempfile.TemporaryDirectory(prefix='rq315-repeat-') as tmp:
                    out=Path(tmp)/arm;render_arm(public['payload'],c,arm,out)
                    assert sha_file(out/'dashboard.png')==sha_file(folder/'dashboard.png')
                    rerenders.append({'case':oid,'arm':arm,'png_sha256':sha_file(out/'dashboard.png')})
        inputs={};cache={};excluded={}
        for arm in ARMS:
            im=public['images'].get(arm);png=(root/im['path']).read_bytes() if im else None
            parts=exps.parts_for(public,arm,png)
            signature=stable_hash([{**p,'png':stable_hash(p['png'])} if 'png' in p else p for p in parts])
            if signature not in cache: cache[signature]=tokens.count(parts,public['system'],MODEL)
            inputs[arm]=cache[signature]
            if inputs[arm]+c['max_tokens']>spec['max_model_len']: excluded[arm]='intact input exceeds context'
        assert public['texts']['PAIR_REPEAT']==public['texts']['PAIR_VISUAL']
        assert public['canonical_arms']['PAIR_REPEAT']=='PAIR_REPEAT'
        ratios[row['dataset']].append((inputs['PAIR_VISUAL'],inputs['BASE_TEXT'],inputs['PAIR_TEXT']))
        marker['context_excluded']=excluded
        if marker['preparation_source_contract']!=contract:
            marker.setdefault('cpu_requalified_source_history',[]).append(stable_hash(marker['preparation_source_contract']))
            marker['preparation_source_contract']=contract
        write_json(root/'flags'/(oid+'.json'),marker)
        cases.append({'case':oid,'dataset':row['dataset'],'inputs':inputs,'context_excluded':excluded,
                      'relations':len(public['payload']['relations']),'eligible_relations':audit['eligible_relations']})
        if len(cases)%10==0: print('CPU checked',len(cases),'/',len(rows),flush=True)
    assert source_contract()==contract,'Source changed during CPU regression'
    ratios={d:{'visual_base':sum(v for v,b,t in rs)/sum(b for v,b,t in rs),'visual_pair':sum(v for v,b,t in rs)/sum(t for v,b,t in rs)} for d,rs in ratios.items()}
    applicability={d:{'qualified':sum(v['dataset']==d and v['relations']>0 for v in cases),'total':sum(v['dataset']==d for v in cases)} for d in c['case_counts']}
    cost=all(v['visual_base']<=c['readiness']['max_mean_base_input_ratio'] and v['visual_pair']<=c['readiness']['max_mean_pair_input_ratio'] for v in ratios.values())
    coverage=smoke or all(v['qualified']/v['total']>=c['method']['minimum_dataset_applicability'] for v in applicability.values())
    passed=cost and coverage and not any(v['context_excluded'] for v in cases)
    checkpoint=checkpoint_audit(loaded) if not smoke else read_json(path(c['results'])/'qualification/cpu.json')['checkpoint_audit']
    report={'status':'passed' if passed else 'failed','source_contract':contract,'checks':checks,'case_ids':[r['opaque_incident_id'] for r in rows],
        'per_case':cases,'readiness_passed':passed,'dataset_input_ratios':ratios,'applicability':applicability,
        'cost_passed':cost,'applicability_passed':coverage,'max_input_tokens':max(v for r in cases for v in r['inputs'].values()),
        'actual_png_checks':png_checks,'actual_bindings_checked':bindings,'independently_checked_source_pairs':source_pairs,
        'deterministic_rerenders':rerenders,'checkpoint_audit':checkpoint,'seconds':time.monotonic()-started,'gpu_calls':0}
    write_json(path(c['results'])/'qualification'/('cpu_smoke.json' if smoke else 'cpu.json'),report)
    if not passed: raise RuntimeError('Registered CPU applicability/cost/capacity gate failed; stop before GPU')
    return {k:v for k,v in report.items() if k not in {'source_contract','per_case','checkpoint_audit'}}
