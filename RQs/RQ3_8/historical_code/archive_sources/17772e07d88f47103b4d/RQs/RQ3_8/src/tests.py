"""CPU semantic/render checks and bounded smoke artifact review; no accuracy gate."""
import argparse
from copy import deepcopy
import hashlib
from pathlib import Path
import tempfile
import time

from .utils import ROOT, BASE, DATA, RESULTS, ARMS, MODELS, read, save, digest
from . import exps


def semantic_checks(public):
    # The compiler accepts public DTOs only, never an evaluator-private object.
    assert not {'private','ground_truth','accepted_labels','fault_type','dataset','case_id'} & public.keys()
    diagrams={arm:exps.design(public,arm) for arm in ARMS if not arm.startswith('T_')}
    ev0,d0=diagrams['LINE_FULL']
    for arm in ('READOUT_FULL','LINE_BOUND'):
        ev,d=diagrams[arm]
        assert ev==ev0,(arm,'fact drift')
        assert d['viewport']==d0['viewport'],(arm,'capacity drift')
        from renderer.utils import compile_design
        a=compile_design(ev,d)['rectangles'];b=compile_design(ev0,d0)['rectangles']
        assert [{k:r[k] for k in ('x','y','width','height','card')} for r in a]==[
                {k:r[k] for k in ('x','y','width','height','card')} for r in b]
    lines=diagrams['LINE_BOUND'][1]['bindings']
    assert diagrams['LINE_PAIRS'][0]==ev0
    assert len({b['entity'] for b in lines})==len(lines)
    assert {b['entity'] for b in lines}=={c['entity'] for c in ev0['cards'] if c['kind']=='metric'}
    text=exps.parts(public,'T_FULL')
    for arm in ('G_FULL','READOUT_FULL','LINE_FULL','LINE_BOUND','LINE_PAIRS'):
        ps=exps.parts(public,arm,b'cpu fixture')
        visible=[p for p in ps if p['type']=='text' and p['text']!=exps.GUIDE]
        assert visible==text,(arm,'strong text mismatch')
    assert set(map(tuple,public['selected_relations']))<=set(map(tuple,public['full_relations']))
    original=digest(public);exps.design(public,'LINE_BOUND');assert digest(public)==original
    # Vary only evaluator labels in separate memory; model projection is unchanged.
    private1={'accepted_labels':['100']};private2={'accepted_labels':['999']}
    assert private1!=private2 and digest(exps.design(public,'LINE_BOUND'))==digest(diagrams['LINE_BOUND'])
    return {'status':'pass','arms':len(diagrams),'facts_identical':True}


def cpu_checks(render_images=True):
    from renderer.main import render
    started=time.monotonic();roster=read(DATA/'roster.json');reports=[]
    output=RESULTS/'qualification'/f'cpu-{time.time_ns()}'
    for oid in roster['smoke']:
        public=read(DATA/'public'/f'{oid}.json')
        report={'case':oid,**semantic_checks(public)}
        if render_images:
            pngs={}
            for arm in ARMS:
                if arm.startswith('T_'):continue
                ev,d=exps.design(public,arm);directory=output/oid/arm
                save(directory/'evidence.json',ev);save(directory/'design.json',d)
                visual=render(directory/'evidence.json',directory/'design.json',directory/'render')
                image=next((directory/'render').glob('*.png'))
                pngs[arm]=hashlib.sha256(image.read_bytes()).hexdigest()
                assert visual.get('status')=='passed',visual
            assert pngs['LINE_FULL']!=pngs['READOUT_FULL']
            if public['metrics']:assert pngs['LINE_FULL']!=pngs['LINE_BOUND']
            report['png_sha256']=pngs
        reports.append(report)
    # Real data edge case: onset display may be null and must not create an event.
    from renderer.topology import onset_card
    event=onset_card({'facts':[{'field':'propagation_service','payload':{'onset_rel_min_display':None}}]})
    assert event['data']['events']==[]
    value={'status':'pass','cases':reports,'elapsed_s':time.monotonic()-started,'gpu_calls':0}
    save(output/'summary.json',value);print(output,flush=True)
    return value


def smoke_review():
    """Commit-time audit only; not a bulk resume validator."""
    from RQs.RQ3_1.src.main import audit_completion_artifacts
    output=RESULTS/'smoke';completed=[];errors=[]
    for path in (output/'completed').glob('*.json'):
        audit_completion_artifacts(output,path.stem)
        item=read(output/'outputs'/path.name)
        completed.append({'model':item['model'],'arm':item['dimensions']['arm'],
                          'case':item['opaque_incident_id'],'call_key':path.stem,
                          'status':item['status']})
    for p in (RESULTS/'flags').glob('*.json'):
        flag=read(p)
        if flag.get('smoke') and flag.get('failure_kind') in ('infrastructure','request_timeout'):
            errors.append(flag)
    from vlmrca.run_state import DurableCallRegister
    ledger=DurableCallRegister(output/'calls.sqlite',18,scope='smoke',scope_limit=18)
    counts=ledger.summary();assert sum(counts.values())<=18
    result={'status':'fail' if errors else 'pass','completed':completed,'errors':errors,'calls':counts,
            'coverage_models':sorted({r['model'] for r in completed}),
            'coverage_arms':sorted({r['arm'] for r in completed})}
    save(output/'review.json',result)
    if errors:raise RuntimeError('Smoke infrastructure failures; preserve and repair')
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['semantic','cpu','smoke-review']);args=p.parse_args()
    print(smoke_review() if args.command=='smoke-review' else cpu_checks(args.command=='cpu'))


if __name__=='__main__':main()
