"""Independent numerical, source retention, actual DOM and full-input regression."""
from collections import defaultdict
from copy import deepcopy
from html.parser import HTMLParser
from pathlib import Path
import math
import tempfile
import time
from . import exps
from .utils import ARMS, MODEL, VERSION, path, register, runtime, source_contract, read_json, write_json, sha_file, stable_hash, flag, logical_key


class DOM(HTMLParser):
    def __init__(self,html):
        super().__init__(); self.nodes=[]; self.stack=[]; self.panel=None; self.feed(html)

    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='section': self.panel=attrs.get('data-card')
        node={'tag':tag,'attrs':attrs,'panel':self.panel,'text':''}; self.nodes.append(node)
        if tag not in {'meta','link','br','wbr','img','input','hr'}: self.stack.append(node)

    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i]['tag']==tag:
                del self.stack[i:]; break
        if tag=='section': self.panel=None

    def handle_data(self,data):
        for n in self.stack: n['text']+=data


def inspect_render(folder,payload,c,arm,contract=None):
    from PIL import Image
    contract=source_contract() if contract is None else contract
    evidence,_,ops,design,op_audit=exps.design_for(payload,c,arm)
    manifest=read_json(folder/'manifest.json'); source=folder.parent/(folder.name+'_design')
    assert manifest['status']=='passed' and not manifest['audit']['issues']
    assert manifest['png_sha256']==sha_file(folder/'dashboard.png')
    assert manifest['html_sha256']==sha_file(folder/'dashboard.html')
    assert manifest['renderer_source']==contract['renderer']
    assert manifest['bundle_sha256']==contract['files']['src/renderer/web/dist/render.mjs']
    assert manifest['font_sha256']==contract['files']['src/renderer/web/assets/DejaVuSans.ttf']
    assert read_json(folder/'evidence.json')==evidence and read_json(folder/'design.json')==design
    assert read_json(source/'operations.json')==ops and read_json(source/'operations_audit.json')==op_audit
    with Image.open(folder/'dashboard.png') as im:
        im.load(); assert im.size==(design['viewport']['width'],design['viewport']['height']) and not im.info
    dom=DOM((folder/'dashboard.html').read_text())
    for card in evidence['cards']:
        nodes=[n for n in dom.nodes if n['panel']==card['id']]
        if card['kind']=='literal':
            actual=[n['text'] for n in nodes if n['attrs'].get('class')=='literal-line']
            assert actual==payload['lines']
        if card['kind']=='metric':
            points=[n for n in nodes if n['tag']=='circle']; lines=[n for n in nodes if n['tag']=='polyline']
            expected=[i for i,v in enumerate(card['data']['values']) if v is not None]
            if arm=='WINDOW_MARKLESS': assert not points and not lines; continue
            assert [n['attrs']['data-binding'] for n in points]==[f'{card["id"]}.sample.{i}' for i in expected]
            assert len(lines)==int(len(expected)>1)
            if lines:
                coords=[tuple(map(float,p.split(','))) for p in lines[0]['attrs']['points'].split()]
                assert coords==[(float(n['attrs']['cx']),float(n['attrs']['cy'])) for n in points]
                # Cross-gap line remains a single polyline at original time coordinates.
                for k in range(1,len(coords)):
                    dx=coords[k][0]-coords[k-1][0]
                    db=card['data']['bins'][expected[k]]-card['data']['bins'][expected[k-1]]
                    assert math.isclose(dx/db,376/(max(card['data']['bins'])-min(card['data']['bins'])),rel_tol=1e-10)
            assert not any(n['text'].strip()=='?' for n in nodes if n['tag']=='text')
    return len(manifest['audit']['bindings'])


def unit_tests(c):
    import numpy as np
    from renderer.utils import validate_evidence, compile_design
    cases=[[None]*64,[0.]*64,[1.]*32+[100.,1.]+[1.]*30,[float(i) if i%2==0 else None for i in range(64)]]
    rng=np.random.default_rng(42)
    cases += [[None if i%3==0 else float(x) for i,x in enumerate(rng.normal(size=64))] for _ in range(30)]
    for values in cases:
        actual=exps.observations(values,list(range(64)))
        array=np.asarray([np.nan if v is None else v for v in values]); idx=np.flatnonzero(np.isfinite(array))
        if not len(idx): assert actual is None; continue
        expected={'first':idx[0],'last':idx[-1],'minimum':int(np.nanargmin(array)),'maximum':int(np.nanargmax(array))}
        for key,i in expected.items(): assert tuple(actual[key])==(int(i),float(array[i]))
    fixture={'schema':'CanvasEvidenceV1','cards':[{'id':'T','kind':'literal','title':'Summary','unit':'','entity':None,'data':{'lines':['safe text']}}]}
    validate_evidence(fixture)
    for value in ([],[''],['line\nline'],['ground_truth=123']):
        bad=deepcopy(fixture); bad['cards'][0]['data']['lines']=value
        try: validate_evidence(bad)
        except ValueError: pass
        else: raise AssertionError('Invalid literal input accepted')
    with tempfile.TemporaryDirectory(prefix='rq314-marker-') as folder:
        root=Path(folder); key=logical_key('case','WINDOW_VISUAL')
        write_json(root/'flags'/(key+'.json'),{'case':'case','arm':'WINDOW_VISUAL','status':'done','call_key':'abc'})
        assert flag(root,'case','WINDOW_VISUAL') is None
        write_json(root/'completed/abc.json',{'status':'complete'})
        assert flag(root,'case','WINDOW_VISUAL')['status']=='done'
    assert exps.REPEATS=={'RAW_REPEAT','WINDOW_REPEAT'}
    return ['NumPy independent full-window extrema/first/last, including reference transient and constant/sparse cases',
            'Literal public-schema rejection and injection isolation','Atomic commit resume and true-repeat semantics']


def cpu(c,smoke=False):
    started=time.monotonic(); checks=unit_tests(c)
    from .gates import require_renderer_build
    from .main import render_arm
    from RQs.RQ3_3.src.utils import OfflineTokens
    from RQs.RQ3_12.src.tests import checkpoint_audit
    from RQs.RQ3_12.src.utils import sampling_support
    require_renderer_build(); loaded,spec=runtime(c)
    tokens=OfflineTokens({'unified':{'vllm':str(loaded.source)},'models':[MODEL]})
    root=path(c['preparation']); reg=register(c); rows=reg['smoke' if smoke else 'cases']
    contract=source_contract(); cases=[]; ratios=defaultdict(list); png_checks=bindings=metric_checks=0
    smoke_ids={r['opaque_incident_id'] for r in reg['smoke']}; rerenders=[]
    import numpy as np
    for row in rows:
        if time.monotonic()-started>c['cpu_seconds']: raise TimeoutError('CPU qualification limit')
        oid=row['opaque_incident_id']; marker=read_json(root/'flags'/(oid+'.json')); public=read_json(root/'public'/(oid+'.json'))
        assert marker['status']=='done' and marker['version']==VERSION
        for cat in ('public','private'): assert sha_file(root/cat/(oid+'.json'))==marker[cat+'_sha256']
        parent=read_json(path(c['parent'])/'public'/(oid+'.json')); raw=read_json(root/'raw'/(oid+'.json'))
        rebuilt,audit=exps.compile_public(parent,raw,c)
        assert rebuilt['texts']==public['texts'] and stable_hash(rebuilt['payload'])==stable_hash(public['payload'])
        assert public['texts']['RAW_TEXT']==raw and audit['binding']['reversible']
        # Match every finite curve value to the original public card and genuine sampling clock.
        _,_,clock=exps.public_series(parent); support=sampling_support(c,row,clock)
        for card in public['payload']['evidence']['cards']:
            original=next(o for o in parent['evidence']['cards'] if o['entity']==card['entity'] and o['title']==card['title'].split(' · ',1)[1] and o['kind']==card['kind'])
            assert card['unit']==original['unit']
            if card['kind']=='metric':
                assert card['data']['values']==original['data']['values'] and card['data']['bins']==original['data']['bins']
                arr=np.array([np.nan if v is None else v for v in card['data']['values']]); idx=np.flatnonzero(np.isfinite(arr))
                assert set(idx)<=set(support['sampling_bins'])
                stats=public['payload']['statistics'][card['id']]
                for k,i in {'first':idx[0],'last':idx[-1],'minimum':np.nanargmin(arr),'maximum':np.nanargmax(arr)}.items():
                    assert stats[k]==[card['data']['bins'][i],arr[i]]
                metric_checks+=1
            else: assert all(card['data'][k]==original['data'][k] for k in ('before','after'))
        exps.visible_audit(public)
        for arm in ('WINDOW_VISUAL','WINDOW_MARKLESS','WINDOW_PIXEL'):
            folder=(root/public['images'][arm]['path']).parent
            bindings+=inspect_render(folder,public['payload'],c,arm,contract); png_checks+=1
            if oid in smoke_ids and not smoke:
                # Unique outputs; no overwriting historical gallery evidence.
                with tempfile.TemporaryDirectory(prefix='rq314-repeat-') as tmp:
                    out=Path(tmp)/arm; render_arm(public['payload'],c,arm,out)
                    assert sha_file(out/'dashboard.png')==sha_file(folder/'dashboard.png')
                    rerenders.append({'case':oid,'arm':arm,'png_sha256':sha_file(out/'dashboard.png')})
        inputs={}; cached={}; excluded={}
        for arm in ARMS:
            image=public['images'].get(arm); png=(root/image['path']).read_bytes() if image else None
            parts=exps.parts_for(public,arm,png)
            signature=stable_hash([{**p,'png':stable_hash(p['png'])} if 'png' in p else p for p in parts])
            if signature not in cached: cached[signature]=tokens.count(parts,public['system'],MODEL)
            inputs[arm]=cached[signature]
            if inputs[arm]+c['max_tokens']>spec['max_model_len']: excluded[arm]='intact input exceeds context'
        assert marker['canonical_arms']=={a:a for a in ARMS}
        ratios[row['dataset']].append((inputs['WINDOW_VISUAL'],inputs['RAW_TEXT']))
        marker['context_excluded']=excluded
        # CPU replay above establishes unchanged public semantics after pre-inference repairs.
        if marker['preparation_source_contract']!=contract:
            marker.setdefault('cpu_requalified_source_history',[]).append(stable_hash(marker['preparation_source_contract']))
            marker['preparation_source_contract']=contract
        write_json(root/'flags'/(oid+'.json'),marker)
        cases.append({'case':oid,'dataset':row['dataset'],'inputs':inputs,'context_excluded':excluded,
                      'plotted_metrics':audit['plotted_metrics'],'trace_cards':audit['trace_cards']})
        if len(cases)%20==0: print('CPU checked',len(cases),'/',len(rows),flush=True)
    assert source_contract()==contract, 'Source changed during CPU regression'
    dataset_ratio={d:sum(a for a,b in pairs)/sum(b for a,b in pairs) for d,pairs in ratios.items()}
    passed=not any(r['context_excluded'] for r in cases) and all(v<=c['readiness']['max_mean_input_ratio'] for v in dataset_ratio.values())
    checkpoint=checkpoint_audit(loaded) if not smoke else read_json(path(c['results'])/'qualification/cpu.json')['checkpoint_audit']
    report={'status':'passed' if passed else 'failed','source_contract':contract,'checks':checks,
            'case_ids':[r['opaque_incident_id'] for r in rows],'per_case':cases,'readiness_passed':passed,
            'dataset_input_ratios':dataset_ratio,'max_input_tokens':max(v for r in cases for v in r['inputs'].values()),
            'actual_png_checks':png_checks,'actual_bindings_checked':bindings,'independent_metric_checks':metric_checks,
            'deterministic_rerenders':rerenders,'checkpoint_audit':checkpoint,'seconds':time.monotonic()-started,'gpu_calls':0}
    write_json(path(c['results'])/'qualification'/('cpu_smoke.json' if smoke else 'cpu.json'),report)
    if not passed: raise RuntimeError('Whole-roster cost/capacity gate failed; no GPU calls authorized by this gate')
    return {k:v for k,v in report.items() if k not in {'source_contract','per_case','checkpoint_audit'}}
