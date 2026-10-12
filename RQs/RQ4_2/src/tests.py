"""Independent CPU invariants, no network/model client or GPU startup."""
from collections import Counter
import itertools
import os
import pytest

from .exps import capacity_lower_bound, co_membership_distance, fill_background, optimize_groups
from .utils import generation_identity, read, write


def test_capacity_failure_is_necessary_not_false_pass():
    def row(width, height):
        return {'card': 'M1', 'width': width, 'height': height, 'min_font': 18, 'overflow': []}
    result = capacity_lower_bound({'measurements': [{'region_width': w, 'cards': [row(512, 2080)]} for w in (1536, 2048)]})
    assert not result['necessary_capacity_pass']  # Indivisible card cannot cross a quadrant.


def test_capacity_area_includes_all_occurrences():
    result = capacity_lower_bound({'measurements': [{'region_width': w,
        'cards': [{'card': str(i), 'width': 512, 'height': 1024, 'min_font': 18, 'overflow': []} for i in range(33)]}
        for w in (1536, 2048)]})
    assert not result['necessary_capacity_pass']


def test_membership_distance_ignores_group_names():
    a = dict(enumerate([0, 1, 2, 3, 0]))
    b = {k: 3-v for k, v in a.items()}
    assert co_membership_distance(a, b) == 0
    c = {**a, 4: 1}
    assert co_membership_distance(a, c) == .2


def test_real_background_minimum_changes_against_independent_bruteforce():
    original = [0, 0, 1, 1, 2, 2, 3, 3]
    protected = {'a': [0], 'b': [2]}
    assignment = {'a': 1, 'b': 1}
    actual = fill_background(original, protected, assignment, 1)
    free = [1, 3, 4, 5, 6, 7]
    candidates = []
    for labels in itertools.product(range(4), repeat=len(free)):
        result = [1 if i in (0, 2) else 0 for i in range(8)]
        for cell, group in zip(free, labels, strict=True):
            result[cell] = group
        if Counter(result) == {g: 2 for g in range(4)}:
            candidates.append(sum(result[i] != original[i] for i in free))
    assert sum(actual[i] != original[i] for i in free) == min(candidates)
    assert fill_background(original, protected, assignment, .05) is None


def test_no_action_preserves_entire_original_map():
    original = [g for g in range(4) for _ in range(10)]
    units = {'a': [0, 1], 'b': [10, 11]}
    result = optimize_groups({'a': 0, 'b': 1}, [], original, units)
    assert result['cells'] == original and result['moves'] == []


def test_optimizer_strict_improvement_equal_groups():
    original = [g for g in range(4) for _ in range(20)]
    result = optimize_groups({'a': 0, 'b': 1}, [('a', 'b', 1.)], original, {'a': [0], 'b': [20]})
    assert result['cut_reduction'] == 1
    assert Counter(result['cells']) == {g: 20 for g in range(4)}
    assert result['moves'][0]['gain'] > 0


def test_unknown_or_duplicate_units_rejected():
    with pytest.raises(ValueError):
        fill_background([0, 1, 2, 3], {'a': [0], 'b': [0]}, {'a': 0, 'b': 1})


def test_generation_identity_not_nominal_group_ids():
    common = dict(prompt='task', pixels=['digest'], model='frozen', processor='frozen', recipe='frozen', seed=1, operation='partition23')
    assert generation_identity(**common, groups=[0, 1, 0, 2]) == generation_identity(**common, groups=[3, 2, 3, 0])
    assert generation_identity(**common, groups=[0, 1, 0, 2]) != generation_identity(**common, groups=[0, 0, 1, 2])


def test_atomic_commit(tmp_path):
    path = tmp_path/'completed'/'key.json'
    write(path, {'done': True})
    assert read(path) == {'done': True}
    assert list(path.parent.iterdir()) == [path]


def test_readable_operation_is_explicit_and_preserves_facts():
    from renderer.tests import sample
    from renderer.exps import preset
    from renderer.operations import apply_operations
    from renderer.utils import digest, compile_design
    evidence = sample()
    original = digest(evidence)
    design = preset(evidence)
    assert 'readable_cards' not in design
    result, audit = apply_operations(evidence, design, [{'op': 'readable_cards', 'args': {'profile': 'source_cards_v1'}}])
    assert result['readable_cards'] == 'source_cards_v1'
    assert digest(evidence) == original and 'readable_cards' not in design
    assert compile_design(evidence, result)['expected_bindings'] == compile_design(evidence, design)['expected_bindings']
    with pytest.raises(ValueError):
        apply_operations(evidence, design, [{'op': 'readable_cards', 'args': {'profile': 'unknown'}}])


@pytest.mark.skipif(os.environ.get('RUN_RQ42_BROWSER') != '1', reason='Explicit offline DOM regression')
def test_measured_captions_preserve_bindings_and_widths(tmp_path):
    from renderer.measure import measure_jobs
    evidence = {'schema': 'CanvasEvidenceV1', 'cards': [
        {'id': 'INV001', 'kind': 'inventory', 'entity': None, 'title': 'Observed entities', 'unit': '',
         'data': {'identities': ['123'], 'details': []}},
        {'id': 'INV002', 'kind': 'inventory', 'entity': None, 'title': 'Conditional observations', 'unit': 'ms',
         'data': {'identities': ['123'], 'details': [
             {'name': 'Reference parent conditional duration quantile', 'value': '1495.0390883499997'},
             {'name': 'Current count', 'value': '0'},
             {'name': 'Operation', 'value': 'POST /escaped/<value>&service'}]}}]}
    write(tmp_path/'e.json', evidence)
    write(tmp_path/'jobs.json', [{'evidence': str(tmp_path/'e.json'), 'output': str(tmp_path/'dom.json'),
          'components': {'INV001': 'inventory.identities', 'INV002': 'inventory.identities'},
          'full_width_cards': ['INV001'], 'node_layouts': {'1536': {}, '2048': {}}}])
    measure_jobs(tmp_path/'jobs.json', tmp_path/'browser.log')
    result = read(tmp_path/'dom.json')
    for m in result['measurements']:
        candidate, auxiliary = m['cards']
        assert candidate['width'] == m['region_width'] and auxiliary['width'] == 512
        assert auxiliary['min_font'] >= 18-.0001
        assert not auxiliary['overflow']
        assert all('INV002.detail.'+str(i) in auxiliary['bindings'] for i in range(3))


def test_optimizer_matches_independent_exhaustive_small():
    # One-step choice is checked by exhaustive assignments and exact filler.
    old=[g for g in range(4) for _ in range(20)]
    protected={'a':[0,1],'b':[20,21],'c':[40,41],'d':[60,61]};initial=dict(zip(protected,range(4)))
    edges=[('a','b',.4),('b','c',.7),('c','d',.2),('a','d',.1)]
    result=optimize_groups(initial,edges,old,protected,1)
    cost=lambda d:sum(w for a,b,w in edges if d[a]!=d[b])
    candidates=[];keys=sorted(initial)
    for u in keys:
        for g in range(4):candidates.append({**initial,u:g})
    for i,u in enumerate(keys):
        for v in keys[i+1:]:candidates.append({**initial,u:initial[v],v:initial[u]})
    feasible=[c for c in candidates if fill_background(old,protected,c) is not None]
    assert result['cut_after']==pytest.approx(min(map(cost,feasible)))


def test_real_architecture_partition_cpu():
    torch=pytest.importorskip('torch')
    from transformers.models.qwen3_5.configuration_qwen3_5 import Qwen3_5VisionConfig
    from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5VisionModel
    from vlmrca.vlm.vision_partition import partition_vision,patch_permutation
    torch.set_num_threads(1);torch.manual_seed(421)
    cfg=Qwen3_5VisionConfig(depth=27,hidden_size=32,intermediate_size=64,num_heads=4,
                          patch_size=16,spatial_merge_size=2,temporal_patch_size=2,
                          out_hidden_size=32,num_position_embeddings=16)
    cfg._attn_implementation='sdpa';model=Qwen3_5VisionModel(cfg).eval()
    x=torch.randn(64,3*2*16*16);grid=torch.tensor([[1,8,8]])
    with torch.no_grad():
        baseline=model(x,grid).pooler_output
        with partition_vision(model,[0]*16):
            assert torch.equal(baseline,model(x,grid).pooler_output)
        groups=[i%4 for i in range(16)]
        with partition_vision(model,groups):actual=model(x,grid).pooler_output
        with partition_vision(model,[3-g for g in groups]):renamed=model(x,grid).pooler_output
        assert torch.allclose(actual,renamed,atol=1e-6,rtol=1e-5)
        assert not torch.allclose(actual,baseline,atol=1e-7,rtol=1e-7)
        with pytest.raises(RuntimeError):
            with partition_vision(model,groups):raise RuntimeError('interrupted')
        assert torch.equal(baseline,model(x,grid).pooler_output)
    perm,inv,k=patch_permutation(groups)
    assert torch.equal(perm[inv],torch.arange(64))
    assert all(len(set((perm[i:i+4]//4).tolist()))==1 for i in range(0,64,4))
    # Explicit dense mask versus independently computed four blocks.
    q,k,v=[torch.randn(1,2,64,8) for _ in range(3)]
    labels=torch.tensor(groups).repeat_interleave(4);mask=labels[:,None]==labels[None,:]
    dense=torch.nn.functional.scaled_dot_product_attention(q,k,v,attn_mask=mask)
    qp,kp,vp=[a[:,:,perm,:] for a in (q,k,v)]
    pieces=[torch.nn.functional.scaled_dot_product_attention(qp[:,:,i:i+16],kp[:,:,i:i+16],vp[:,:,i:i+16]) for i in range(0,64,16)]
    blocked=torch.cat(pieces,dim=2)[:,:,inv]
    assert torch.allclose(dense,blocked,atol=1e-6,rtol=1e-5)


def test_runtime_atomic_pause_reference_and_recovery(tmp_path):
    from .utils import CallSession,digest
    import json
    calls=[]
    def provider(request):
        assert not any(k in request for k in ('candidates','accepted','numeric_to_natural','gold'))
        calls.append(request)
        return json.dumps({'services':['111','222','333','444','555'],'reason':'test','confidence':'low'})
    request={'identity':digest('same'),'system':'static','instruction':'static','images':['opaque'],
             'operation':'full','groups':[],'task':'RCA','seed':42}
    ctx={'candidates':['111','222','333','444','555'],'numeric_to_natural':{x:x for x in ['111','222','333','444','555']},'accepted':['222']}
    session=CallSession(tmp_path,provider,limit=18)
    with pytest.raises(BlockingIOError):CallSession(tmp_path,provider,limit=18)
    with pytest.raises(RuntimeError):session.run('first',lambda:request,ctx,fail_at='after_response')
    session.close();session=CallSession(tmp_path,provider,limit=18);session.recover()
    first=session.run('first',lambda:request,ctx)
    assert first['outcome']['metrics']['mrr']==.5 and len(calls)==1
    assert session.run('first',lambda:1/0,ctx)==first  # fast resume before input access
    assert session.run('alias',lambda:request,ctx,reference='first')['actual_calls']==0
    assert len(calls)==1
    (tmp_path/'PAUSE').touch()
    assert session.run('next',lambda:1/0,ctx)['status']=='paused'
    (tmp_path/'PAUSE').unlink()
    invalid={**request,'identity':digest('invalid')};session.provider=lambda _: '{}'
    assert session.run('invalid',lambda:invalid,ctx)['outcome']['status']=='model_failure'
    session.close()


def test_passive_attention_cpu_and_storage_ceiling(tmp_path):
    torch=pytest.importorskip('torch')
    from vlmrca.vlm.passive_summary import attention_region_summary,AttentionStore,PassiveAttentionTap
    torch.manual_seed(42)
    q=torch.randn(1,4,3,8);k=torch.randn(1,2,12,8);ids=torch.tensor([0,1,1,2,2,2,3,3,3,3,4,4])
    weights=torch.softmax((q[:,:,-1:] @ k.repeat_interleave(2,dim=1).transpose(-1,-2))*(8**-.5),-1).mean((0,1,2))
    reference=torch.stack([weights[ids==i].sum() for i in range(5)])
    assert torch.allclose(attention_region_summary(q,k,ids,5,8**-.5),reference,atol=1e-7)
    assert AttentionStore.storage_ceiling(10000)<1000000000
    store=AttentionStore(tmp_path);tap=PassiveAttentionTap(store)
    from types import SimpleNamespace
    key='a'*64;tap.begin(key,ids,['other:syntax','text:task','image:header','image:labels','image:marks'],'b'*64)
    tap.observe(SimpleNamespace(layer_idx=3),q,k,None,8**-.5)
    tap.observe(SimpleNamespace(layer_idx=3),q,k,None,8**-.5)
    tap.end();tap.close();store.close()
    record=read(tmp_path/(key+'.json'))
    assert record['sample_count']==2 and len(record['text_mass'])==2
    assert (tmp_path/(key+'.json')).stat().st_size<=65536
    assert record['text_mass'][0]>0 and record['image_mass'][0]>0


def test_source_graph_rewire_degrees_and_determinism():
    from .exps import rewire_edges
    packet={'evidence':{'cards':[{'id':'G','kind':'graph','data':{'edges':[
        {'source':str(i//3),'target':str(10+i),'kind':'calls','id':str(i)} for i in range(12)]}}]}}
    a,ratio,_=rewire_edges(packet,42);b,ratio2,_=rewire_edges(packet,42)
    assert a==b and ratio==ratio2
    old=packet['evidence']['cards'][0]['data']['edges'];new=a['evidence']['cards'][0]['data']['edges']
    for key in ('source','target','kind'):assert Counter(e[key] for e in old)==Counter(e[key] for e in new)


def test_complete_partition_groups_and_background_budget():
    from .utils import RESULTS,PREPARED,roster
    for case in roster():
        p=read(RESULTS/'grouping'/case['oid']/'partition.json');original=p['maps']['GEOM'];n=len(original)
        protected={c for cells in p['protected'].values() for c in cells}
        assert len(protected)==sum(map(len,p['protected'].values()))
        for arm,mapping in p['maps'].items():
            assert len(mapping)==n and Counter(mapping)=={g:n//4 for g in range(4)}
            assert all(len({mapping[c] for c in cells})==1 for cells in p['protected'].values())
            assert sum(mapping[c]!=original[c] for c in range(n) if c not in protected)<=int(.05*n)


def test_qa_facts_and_instructions_separated():
    from .utils import RESULTS,PREPARED,mechanism_roster,qa_packet
    rows=mechanism_roster()
    assert Counter(r['dataset'] for r in rows)=={'aiops2022':20,'aiops2025':20,'aegislab':20}
    texts=set()
    for row in rows:
        packet=read(PREPARED/'capacity'/row['oid']/'packet.json');qa=qa_packet(packet,row['oid'])
        if qa['status']!='ready':continue
        assert {t['slot'] for t in qa['targets']}=={'1A','1B','2A','2B'}
        assert all(t['binding'] in packet['expected_bindings'] for t in qa['targets'])
        texts.add(qa['instruction'])
        assert row['oid'] not in qa['instruction']
    assert len(texts)<=2  # only the declared q4 applicability flag varies


def test_candidate_directories_are_global_not_record_owners():
    from .utils import RESULTS,PREPARED,roster
    from .exps import source_units
    for row in roster():
        packet=read(PREPARED/'capacity'/row['oid']/'packet.json')
        measured=read(PREPARED/'capacity'/row['oid']/'dom.json')['measurements'][0]['cards']
        units=source_units(packet,measured)
        for card in packet['evidence']['cards']:
            if card['kind']=='inventory' and card['title'] in {'Observed entities','Candidate IDs · exhaustive fixed order'}:
                unit=next(u for u in units if card['id'] in u['cards'])
                assert unit['owners']==[]
        for unit in units:
            assert unit['height']%32==0 and unit['width'] in (512,1024)


def test_optional_cycle_never_uses_admission_metric():
    original=[g for g in range(4) for _ in range(100)]
    units={'a':list(range(8)),'b':list(range(100,113)),'c':list(range(200,216)), 'd':list(range(300,305))}
    initial=dict(zip(units,range(4)))
    edges=[('a','b',.7),('b','c',.6),('c','d',.4)]
    result=optimize_groups(initial,edges,original,units,escape_cycles=True)
    costs=[result['cut_before']]+[h['cut'] for h in result['moves']]
    assert all(a>b for a,b in zip(costs,costs[1:]))
    assert sum(h['gain'] for h in result['moves'])==pytest.approx(costs[0]-costs[-1],abs=1e-10)


def test_new_renderer_operators_registered_without_default_changes():
    from renderer.operations import REGISTRY
    assert 'evidence_regions' in REGISTRY and 'question_colors' in REGISTRY
    from renderer.tests import sample
    from renderer.exps import preset
    from renderer.utils import compile_design
    evidence=sample();design=preset(evidence)
    before=compile_design(evidence,design)
    assert 'evidence_regions' not in design and 'question_colors' not in design
    invalid={**design,'question_colors':[]}
    with pytest.raises(ValueError):compile_design(evidence,invalid)
    assert before==compile_design(evidence,design)


def test_all_gpu_entrypoints_remain_closed():
    from .gates import require_execution_qualification
    from .exps import LocalSingleCallSolver
    with pytest.raises(RuntimeError):require_execution_qualification()
    with pytest.raises(RuntimeError):LocalSingleCallSolver('/must-not-create-an-attention-store')


def test_best_prefix_escapes_single_step_barrier_without_gate_inputs():
    from .exps import optimize_groups_refined
    import inspect
    assert not any(k in inspect.signature(optimize_groups_refined).parameters for k in ('ink','masses','threshold','distance'))
    original=[i//10 for i in range(40)];initial={str(i):i//3 for i in range(12)}
    protected={str(i):[10*(i//3)+i%3] for i in range(12)}
    edges=[('2','7',4.),('2','10',4.),('3','5',1.),('3','6',4.),('4','8',2.),('4','9',2.),('5','6',3.),('6','7',3.),('8','11',2.),('9','10',3.),('10','11',2.)]
    before=optimize_groups(initial,edges,original,protected)
    result=optimize_groups_refined(initial,edges,original,protected)
    assert result['cut_after']==7 < before['cut_after']==11
    assert any(s['gain']<=0 for p in result['moves'] for s in p['steps'])
    cost=lambda d:sum(w for u,v,w in edges if d[u]!=d[v])
    assert cost(result['assignments'])==result['cut_after']
    previous=cost(initial)
    for p in result['moves']:
        assert p['cut']<previous
        assert sum(s['gain'] for s in p['steps'])==pytest.approx(previous-p['cut'],abs=1e-10)
        moved=[u for s in p['steps'] for u in s['units']]
        assert len(moved)==len(set(moved))
        previous=p['cut']
    assert result==optimize_groups_refined(initial,list(reversed(edges)),original,protected)
    assert result['accepted_steps']<=100 and len(result['passes'])<=8


def test_refinement_no_relations_preserves_original_and_headers():
    from .exps import optimize_groups_refined
    original=[g for g in range(4) for _ in range(100)]
    protected={'a':[0,1],'b':[100,101],**{'HEADER'+str(g):[100*g+99] for g in range(4)}}
    initial={'a':0,'b':1,**{'HEADER'+str(g):g for g in range(4)}}
    noedge=optimize_groups_refined(initial,[],original,protected)
    assert noedge['cells']==original and noedge['moves']==[]
    x=optimize_groups_refined(initial,[('a','b',1.)],original,protected)
    assert all(x['assignments']['HEADER'+str(g)]==g for g in range(4))
    with pytest.raises(ValueError):optimize_groups_refined(initial,[('a','b',float('nan'))],original,protected)


def test_refinement_population_independent_recomputation():
    from .utils import RESULTS,PREPARED,roster
    from .exps import unit_edges,rewire_edges
    from .utils import digest
    import math
    totals={ds:[0,0] for ds in ('aiops2022','aiops2025','aegislab')}
    for row in roster():
        p=read(RESULTS/'grouping'/row['oid']/'partition.json');audit=read(RESULTS/'grouping'/row['oid']/'audit.json')
        packet=read(PREPARED/'capacity'/row['oid']/'packet.json');units=p['source_units'];original=p['maps']['GEOM']
        wrong,_,_=rewire_edges(packet,int(digest(['RQ42_SHAM_FIXED_V1',row['oid']])[:16],16))
        base={u['id']:u['group'] for u in units}
        maps={}
        for arm,objective,entry in [('SEM',packet,audit['semantic']),('SHAM',wrong,audit['sham'])]:
            mapping=p['maps'][arm];protected=p['protected'];occupied={i for cells in protected.values() for i in cells}
            assert Counter(mapping)==Counter(original)
            assert all(len(set(mapping[i] for i in cells))==1 for cells in protected.values())
            assert all(mapping[i]==g for g in range(4) for i in protected['HEADER'+str(g)])
            assert sum(mapping[i]!=original[i] for i in range(len(mapping)) if i not in occupied)<=math.floor(.05*len(mapping))
            assigned={k:mapping[cells[0]] for k,cells in protected.items()};maps[arm]={k:assigned[k] for k in base}
            edges=unit_edges(objective,units);before=sum(w for u,v,w in edges if base[u]!=base[v]);after=sum(w for u,v,w in edges if assigned[u]!=assigned[v])
            assert after==pytest.approx(entry['cut_after'],abs=1e-10)
            assert before==pytest.approx(entry['cut_before'],abs=1e-10)
            assert after<=before+1e-10
        keys=sorted(base)
        def independent_distance(a,b,mass):
            weights=[];changed=[]
            for i,u in enumerate(keys):
                for v in keys[i+1:]:
                    w=mass[u]*mass[v];weights.append(w)
                    if (a[u]==a[v])!=(b[u]==b[v]):changed.append(w)
            return math.fsum(changed)/math.fsum(weights)
        cm={u['id']:len(u['cards']) for u in units};ink=p['foreground_mass']
        card=independent_distance(base,maps['SEM'],cm);foreground=independent_distance(base,maps['SEM'],ink)
        assert card==pytest.approx(p['metrics']['card_distance'],abs=1e-12)
        assert foreground==pytest.approx(p['metrics']['foreground_distance'],abs=1e-12)
        totals[row['dataset']][0]+=1;totals[row['dataset']][1]+=card>=.2 and foreground>=.2 and audit['semantic']['cut_reduction']>=.15
    report=read(RESULTS/'grouping/report.json')
    for ds,(n,passed) in totals.items():
        assert report['datasets'][ds]['sem_pass']==passed
        assert passed>=n*.5



def test_qa_scoring_numeric_precision_units_and_invalid_shape():
    from .utils import score_qa_response
    import json
    audit={'gold':{'q1':'0.10','q2':'123456789.123456789','q3':{'entity':'123','unit':'µs'},'q4':['calls'],'q5':'higher','q6':'equal'},
           'applicable_questions':['q1','q2','q3','q4','q5','q6'],'categories':{'read':['q1','q2'],'binding':['q3','q4'],'phase':['q5','q6']}}
    answer={**audit['gold'],'q1':.1,'q3':{'entity':123,'unit':'μs'}}
    assert score_qa_response(json.dumps(answer),audit)['accuracy']==1
    numeric_literal=json.dumps(answer).replace(chr(34)+'123456789.123456789'+chr(34),'123456789.123456789')
    assert score_qa_response(numeric_literal,audit)['accuracy']==1
    answer['q2']='123456789.12345679';answer['q4']=[{}]
    result=score_qa_response(json.dumps(answer),audit)
    assert not result['questions']['q2'] and not result['questions']['q4']
    assert score_qa_response('[]',audit)['accuracy']==0


def test_attention_geometry_matches_independent_small_grid():
    import numpy as np
    from .utils import attention_regions
    m={'source_png':{'width':128,'height':96},'audit':{'bindings':[
       {'key':'g.edge.a','x':0,'y':35,'width':30,'height':15},
       {'key':'m.sample.1','x':60,'y':33,'width':50,'height':45},
       {'key':'i.label','x':31,'y':70,'width':50,'height':15}]}}
    ids=[7]+[99]*12+[7,7]
    mapped,names=attention_regions(ids,99,m)
    reference=[]
    for y in range(3):
        for x in range(4):
            mass=[0.]*7
            for box in m['audit']['bindings']:
                kind=3 if '.edge.' in box['key'] else 5 if '.sample.' in box['key'] else 4
                area=max(0,min(x*32+32,box['x']+box['width'])-max(x*32,box['x']))*max(0,min(y*32+32,box['y']+box['height'])-max(y*32,box['y']))
                mass[kind]+=area
            reference.append(2 if y==0 else int(np.argmax(mass)) if max(mass)>0 else 6)
    assert mapped.tolist()==[1]+reference+[1,1]
    native,_=attention_regions(ids,99,m,native=True)
    assert native.tolist()==[1]+np.asarray(reference).reshape(3,4).T.flatten().tolist()+[1,1]


def test_frozen_queue_exact_references_coverage_and_no_historic_calls():
    from .utils import RESULTS,ARMS
    q=read(RESULTS/'queue.json');seen={};main=Counter()
    assert q['historical_baseline_new_calls']==0
    for item in q['items']:
        if item['task']=='RCA':main[item['arm']]+=1
        if item['reference']:
            assert item['reference'] in seen and seen[item['reference']]==item['identity']
        seen[item['key']]=item['identity']
    assert main=={a:220 for a in ARMS}
    assert q['unique_calls']+q['smoke_cap']+q['infra_reserve']<=q['call_cap']



def test_admission_rejects_relaxed_thresholds(monkeypatch):
    from . import gates
    original=gates.read
    def changed(path):
        value=original(path)
        if str(path).endswith('partition_v4.json'):value={**value,'membership_change_min':.1}
        return value
    monkeypatch.setattr(gates,'read',changed)
    with pytest.raises(ValueError,match='invariant'):gates.static_check()


def test_runtime_uncommitted_retry_preserves_spent_budget(tmp_path):
    from .utils import CallSession,digest
    request={'identity':digest('retry'),'system':'static','instruction':'static','images':[],
             'operation':'full','groups':[],'task':'QA','seed':42}
    session=CallSession(tmp_path,lambda _: '{}',limit=2)
    with pytest.raises(RuntimeError):session.run('x',lambda:request,fail_at='before_provider')
    session.close();session=CallSession(tmp_path,lambda _: '{}',limit=2)
    recovered=session.recover()
    assert len(recovered['interrupted_spent_calls'])==1
    session.run('x',lambda:request,retry=True)
    assert session.calls.summary()=={'interrupted':1,'complete':1}
    with pytest.raises(RuntimeError,match='hard limit'):session.run('y',lambda:{**request,'identity':digest('y')})
    session.close()


def test_smoke_registration_is_fixed_and_covers_interfaces():
    from .exps import register_smoke
    r=register_smoke()
    assert r==register_smoke() and len(r['items'])==18
    assert len(set(i['oid'] for i in r['items']))==3
    assert {i['arm'] for i in r['items'] if i['task']=='RCA'}=={'FULL','GEOM','SEM','SHAM','NATIVE4'}
    assert {i['arm'] for i in r['items'] if i['task']=='QA'}=={'FULL','GEOM','SEM','NATIVE4'}
    assert Counter(i['dataset'] for i in r['items'])=={'aiops2022':6,'aiops2025':6,'aegislab':6}
    assert r['timeouts_pass'] is False and r['seconds']==600 and not r['formal_enabled']


def test_partial_and_deadline_do_not_commit_incomplete_output(tmp_path,monkeypatch):
    import time
    torch=pytest.importorskip('torch')
    from .exps import PartialGeneration,DeadlineStop
    from .utils import CallSession,digest
    class Tokenizer:
        def decode(self,ids,**kwargs):return ','.join(map(str,ids))
    path=tmp_path/'partial.json';stream=PartialGeneration(Tokenizer(),path,3)
    stream.put(torch.tensor([[91,92,93]]));stream.put(torch.tensor([4]));stream.put(torch.tensor([5]));stream.flush()
    assert read(path)['token_ids']==[4,5] and read(path)['generation_returned'] is False
    stream.end();assert read(path)['generation_returned'] is True
    clock=[9.];monkeypatch.setattr(time,'monotonic',lambda:clock[0])
    stop=DeadlineStop(10.);assert not stop(None,None);clock[0]=10.;assert stop(None,None)
    assert not DeadlineStop(None)(None,None)
    request={'identity':digest('partial'),'system':'static','instruction':'static','images':[],
             'operation':'full','groups':[],'task':'QA','seed':42}
    class InterruptedProvider:
        def bind_transaction(self,path):self.path=path
        def __call__(self,r):
            assert r==request
            write(self.path,{'status':'uncommitted_partial','response':'{'});raise TimeoutError('deadline')
    session=CallSession(tmp_path/'session',InterruptedProvider(),limit=18)
    with pytest.raises(TimeoutError):session.run('one',lambda:request)
    assert session.calls.summary()=={'started':1} and session.completed('one') is None
    assert read(tmp_path/'session/requests/one__call1.json')==request
    session.recover();assert session.calls.summary()=={'interrupted':1}
    session.close()


def test_smoke_watchdog_timeout_cannot_reset_or_pass(tmp_path,monkeypatch):
    import subprocess,time,os
    from . import exps,gates,utils
    from .utils import write
    monkeypatch.setattr(exps,'RESULTS',tmp_path);monkeypatch.setattr(utils,'RQ',tmp_path);monkeypatch.setattr(utils,'RESULTS',tmp_path)
    monkeypatch.setattr(gates,'require_execution_qualification',lambda stage:None)
    write(tmp_path/'qualification_complete.json',{'status':'passed'})
    write(tmp_path/'configs/smoke_v1.json',{'calls_maximum':18,'seconds':600})
    write(tmp_path/'configs/activation.json',{'allowed_stages':['smoke']})
    clock=[0.];monkeypatch.setattr(time,'monotonic',lambda:clock[0]);monkeypatch.setattr(time,'sleep',lambda s:clock.__setitem__(0,clock[0]+s))
    class Child:
        pid=987654321;returncode=None
        def poll(self):return self.returncode
        def wait(self,timeout=None):self.returncode=-15;return self.returncode
    child=Child();killed=[]
    monkeypatch.setattr(subprocess,'Popen',lambda *a,**k:child)
    monkeypatch.setattr(os,'killpg',lambda pid,sig:killed.append(pid))
    result=exps.supervise_smoke()
    assert result['status']=='failed' and result['timeout'] and result['elapsed_seconds']==600
    assert killed==[child.pid] and result['calls']=={} and result['owned_worker_stopped']
    assert not (tmp_path/'configs/activation.json').exists()
    with pytest.raises(FileExistsError):exps.supervise_smoke()
    with pytest.raises(RuntimeError,match='remaining original time'):exps.supervise_smoke(resume_startup=True)


def test_supplement_scope_and_authority_limits(tmp_path,monkeypatch):
    from . import utils,gates
    from .utils import sha
    monkeypatch.setattr(utils,'RQ',tmp_path);monkeypatch.setattr(utils,'RESULTS',tmp_path/'results')
    monkeypatch.setattr(gates,'RQ',tmp_path);monkeypatch.setattr(gates,'RESULTS',tmp_path/'results')
    write(tmp_path/'results/qualification_complete.json',{'status':'passed','source_hashes':{}})
    write(tmp_path/'results/grouping/report.json',{'sem_qualified':True})
    authority=tmp_path/'configs/smoke_supplement_authority_20261009.json'
    write(authority,{'authorized_additional_rounds':5,'calls_per_round':18,'seconds_per_round':600,'formal_authorized':False})
    cfg=tmp_path/'configs/smoke_supplement_1.json'
    write(cfg,{'authority_sha256':sha(authority),'scope':'smoke_supplement_1','supplement_number':1,'items':[{}]})
    permit={'allowed_stages':['smoke'],'smoke_scope':'smoke_supplement_1','smoke_registration_sha256':sha(cfg),
            'cpu_receipt_sha256':sha(tmp_path/'results/qualification_complete.json')}
    write(tmp_path/'configs/activation.json',permit)
    assert utils.smoke_paths()==(tmp_path/'results/gpu_smoke_supplement_1',cfg)
    gates.require_execution_qualification('smoke')
    with pytest.raises(RuntimeError):gates.require_execution_qualification('formal')
    for scope in ('smoke_supplement_6','../escape'):
        write(tmp_path/'configs/activation.json',{**permit,'smoke_scope':scope})
        with pytest.raises(ValueError,match='scope'):utils.smoke_paths()
    write(tmp_path/'configs/activation.json',permit)
    config=read(cfg);config['items']=[{}]*19;write(cfg,config)
    write(tmp_path/'configs/activation.json',{**permit,'smoke_registration_sha256':sha(cfg)})
    with pytest.raises(RuntimeError,match='authority'):gates.require_execution_qualification('smoke')


def test_supplement_only_missing_original_requests_and_compute_compatibility():
    from .utils import RQ,RESULTS
    from .exps import supplement_compatibility
    cfg=read(RQ/'configs/smoke_supplement_1.json')
    old=read(RQ/'configs/smoke_v1.json')['items']
    done={p.stem for p in (RESULTS/'gpu_smoke_v1/execution/completed').glob('*.json')}
    assert {i['key'] for i in cfg['items']}=={i['key'] for i in old}-done
    assert len(cfg['items'])==2 and len(done)==16
    assert not any(i['reference'] for i in cfg['items'])
    assert supplement_compatibility()['status']=='passed'


def test_supplement_coverage_refuses_missing_or_changed_completions(tmp_path):
    from .utils import RQ
    from .exps import combined_smoke_coverage
    cfg=read(RQ/'configs/smoke_supplement_1.json')
    for item in cfg['items']:
        write(tmp_path/'execution/completed'/(item['key']+'.json'),{'request_hash':item['identity']})
    result=combined_smoke_coverage(tmp_path,cfg)
    assert result['status']=='passed' and result['required_positions']==18 and result['inherited']==16 and result['new']==2
    p=tmp_path/'execution/completed'/(cfg['items'][0]['key']+'.json')
    write(p,{'request_hash':'changed'})
    with pytest.raises(ValueError,match='identity'):combined_smoke_coverage(tmp_path,cfg)
    p.unlink()
    with pytest.raises(ValueError,match='Missing'):combined_smoke_coverage(tmp_path,cfg)


def test_supplement_attention_map_numpy_hash_is_canonical():
    import numpy as np
    from .utils import digest
    a=np.asarray([0,1,5,6],dtype=np.int64);names=['syntax','text','mark','background']
    assert digest([list(map(int,a)),names])==digest([[0,1,5,6],names])


def formal_fixture(key='one',reference=None):
    from .utils import digest
    item={'key':key,'oid':'offline','arm':'FULL','task':'QA','identity':digest(key if reference is None else reference),'reference':reference}
    def materialize(item,folder):
        folder.mkdir(parents=True,exist_ok=False)
        write(folder/'audit.json',{'key':item['key']})
        return {'identity':item['identity'],'system':'static','instruction':'static','images':[],
                'operation':'full','groups':[],'task':'QA','seed':42}
    context={'gold':{'q1':'1'},'applicable_questions':['q1'],'categories':{'read':['q1']}}
    return item,materialize,lambda:context,lambda *args:{'status':'passed'}


def test_formal_power_loss_boundaries(tmp_path):
    """Actual SIGKILL, durable SQLite/fsync, then a fresh session for recovery."""
    import multiprocessing,signal,json
    from .utils import FormalSession
    for stage in ('before_provider','during_provider','after_response','after_ledger','before_commit','after_commit'):
        folder=tmp_path/stage;item,materialize,context,validate=formal_fixture()
        def child():
            class Provider:
                last_usage={'input_tokens':1,'output_tokens':1,'image_tokens':0}
                def bind_transaction(self,p):self.partial=p
                def __call__(self,request):
                    with (folder/'seen').open('a') as f:f.write('call\n');f.flush();os.fsync(f.fileno())
                    if stage=='during_provider':
                        write(self.partial,{'uncommitted_partial':'never score this'})
                        os.kill(os.getpid(),signal.SIGKILL)
                    return '{"q1":"1"}'
            session=FormalSession(folder/'execution',Provider(),limit=2)
            def fault(point):
                if point==stage:os.kill(os.getpid(),signal.SIGKILL)
            session.run_item(item,materialize,context,validate,fault=fault)
        process=multiprocessing.get_context('fork').Process(target=child);process.start();process.join(15)
        assert not process.is_alive() and process.exitcode==-signal.SIGKILL
        generated=[]
        session=FormalSession(folder/'execution',lambda r:generated.append(r) or '{"q1":"1"}',limit=2)
        recovery=session.recover()
        complete_before=session.completed('one') is not None
        result=session.run_item(item,materialize,context,validate)
        assert result['outcome']['qa']['accuracy']==1
        interrupted=stage in {'before_provider','during_provider'}
        assert len(generated)==int(interrupted)
        assert sum(session.calls.summary().values())==1+int(interrupted)
        assert session.calls.summary().get('interrupted',0)==int(interrupted)
        assert len(list((folder/'materialized').iterdir()))==1+int(interrupted)
        if stage in {'after_response','after_ledger','before_commit'}:
            assert result['recovered_reply'] and result['continuous_cold_seconds'] is None
        if stage=='after_commit':assert complete_before
        assert session.run_item(item,lambda *a:1/0,lambda:1/0,lambda *a:1/0)==result
        session.close()


def test_formal_pause_drain_and_fast_phase_resume(tmp_path):
    from .exps import formal_loop
    first,materialize,context,validate=formal_fixture();second=formal_fixture('two')[0]
    alias={**first,'key':'alias','reference':'one'}
    registration={'formal_attempt_cap':2,'items':[first,alias,second]};calls=[];closed=[]
    class Provider:
        last_usage={'input_tokens':1,'output_tokens':1,'image_tokens':0}
        def __call__(self,request):
            calls.append(request['identity'])
            if len(calls)==1:write(tmp_path/'execution/PAUSE',{'test':'drain'})
            return '{"q1":"1"}'
        def close(self):closed.append(True)
    result=formal_loop(tmp_path,registration,lambda p:Provider(),materialize,lambda i:context(),validate)
    assert result['status']=='paused' and result['completed']==1 and len(calls)==1 and len(closed)==1
    (tmp_path/'execution/PAUSE').unlink()
    result=formal_loop(tmp_path,registration,lambda p:Provider(),materialize,lambda i:context(),validate)
    assert result['status']=='complete' and result['positions']==3 and len(calls)==2 and len(closed)==2
    alias_record=read(tmp_path/'execution/completed/alias.json')
    assert alias_record['actual_calls']==0 and alias_record['logical_cost_source']=='one'
    assert alias_record['usage']==read(tmp_path/'execution/completed/one.json')['usage']
    assert not (tmp_path/'BLOCKED.json').exists()
    def forbidden(*args):raise AssertionError('Completed phase must not touch inputs or load a model')
    assert formal_loop(tmp_path,registration,forbidden,forbidden,forbidden,forbidden)==result


def test_formal_sigterm_drains_active_request(tmp_path):
    import multiprocessing,signal,time
    from .exps import formal_loop
    first,materialize,context,validate=formal_fixture();second=formal_fixture('two')[0]
    def child():
        class Provider:
            last_usage={'input_tokens':1,'output_tokens':1,'image_tokens':0}
            def __call__(self,request):
                write(tmp_path/'active.json',{'active':True});time.sleep(.5);return '{"q1":"1"}'
            def close(self):write(tmp_path/'closed.json',{'closed':True})
        formal_loop(tmp_path,{'formal_attempt_cap':2,'items':[first,second]},lambda p:Provider(),
                    materialize,lambda i:context(),validate,install_signals=True)
    process=multiprocessing.get_context('fork').Process(target=child);process.start()
    deadline=time.monotonic()+10
    while not (tmp_path/'active.json').exists() and time.monotonic()<deadline:time.sleep(.01)
    assert (tmp_path/'active.json').exists()
    os.kill(process.pid,signal.SIGTERM);process.join(10)
    assert process.exitcode==0 and read(tmp_path/'progress.json')['status']=='paused'
    assert len(list((tmp_path/'execution/completed').glob('*.json')))==1
    assert (tmp_path/'closed.json').exists() and not (tmp_path/'phase_complete.qwen.json').exists()


def test_formal_known_failure_blocks_automatic_retry(tmp_path):
    from .exps import formal_loop
    from .utils import FormalSession
    item,materialize,context,validate=formal_fixture()
    class Broken:
        def __call__(self,request):raise ValueError('Known integrity error')
        def close(self):pass
    registration={'formal_attempt_cap':3,'items':[item]}
    with pytest.raises(ValueError,match='integrity'):
        formal_loop(tmp_path,registration,lambda p:Broken(),materialize,lambda i:context(),validate)
    assert read(tmp_path/'progress.json')['status']=='blocked'
    with pytest.raises(RuntimeError,match='diagnosis'):
        formal_loop(tmp_path,registration,lambda p:1/0,materialize,lambda i:context(),validate)
    s=FormalSession(tmp_path/'execution',None,limit=3)
    assert s.calls.summary()=={'infrastructure_failure':1};s.close()


def test_formal_committed_invalid_output_is_terminal(tmp_path):
    from .utils import FormalSession
    item,materialize,context,validate=formal_fixture()
    calls=[];s=FormalSession(tmp_path/'execution',lambda r:calls.append(r) or 'not JSON',limit=2)
    first=s.run_item(item,materialize,context,validate)
    assert first['outcome']['status']=='model_failure'
    assert s.run_item(item,lambda *a:1/0,lambda:1/0,lambda *a:1/0)==first
    assert len(calls)==1;s.close()


def test_formal_frozen_queue_and_budget(tmp_path):
    from .utils import RQ,RESULTS,sha,FormalSession
    from .exps import formal_prior_calls
    config=read(RQ/'configs/formal_v1.json');queue=read(RESULTS/'queue.json')
    assert config['items']==queue['items'] and config['queue_sha256']==sha(RESULTS/'queue.json')
    assert config['positions']==1336 and config['unique_calls']==1328 and config['formal_attempt_cap']==1470
    assert config['prior_smoke_calls']==formal_prior_calls() and formal_prior_calls()['attempts']==19
    assert config['formal_attempt_cap']+19<=config['combined_call_ceiling']==1590
    seen={}
    for item in config['items']:
        if item['reference']:assert seen[item['reference']]==item['identity']
        seen[item['key']]=item['identity']
    s=FormalSession(tmp_path/'execution',lambda r:'{}',limit=1)
    with pytest.raises(BlockingIOError):FormalSession(tmp_path/'execution',None,limit=1)
    one,materialize,context,validate=formal_fixture();two=formal_fixture('two')[0]
    s.run_item(one,materialize,context,validate)
    with pytest.raises(RuntimeError,match='hard limit'):s.run_item(two,materialize,context,validate)
    s.close()


def test_formal_activation_fail_closed(tmp_path,monkeypatch):
    from . import gates,utils,exps
    from .utils import sha
    from unittest.mock import Mock
    monkeypatch.setattr(gates,'RQ',tmp_path);monkeypatch.setattr(gates,'RESULTS',tmp_path/'results')
    blocked=Mock(side_effect=AssertionError('Must not allocate GPU'))
    monkeypatch.setattr(exps,'LocalSingleCallSolver',blocked)
    with pytest.raises(RuntimeError):exps.run_formal()
    blocked.assert_not_called()
    write(tmp_path/'results/qualification_complete.json',{'status':'passed','source_hashes':{}})
    write(tmp_path/'results/grouping/report.json',{'sem_qualified':True})
    write(tmp_path/'results/formal_readiness.json',{'status':'ready'})
    write(tmp_path/'configs/formal_v1.json',{'frozen':True})
    monkeypatch.setattr(gates,'formal_readiness',lambda:{'status':'ready'})
    permit={'allowed_stages':['formal'],'cpu_receipt_sha256':sha(tmp_path/'results/qualification_complete.json'),
            'formal_readiness_sha256':sha(tmp_path/'results/formal_readiness.json'),
            'formal_registration_sha256':sha(tmp_path/'configs/formal_v1.json')}
    write(tmp_path/'configs/activation.json',permit)
    gates.require_execution_qualification()  # Solver's inherited default routes to formal.
    gates.require_execution_qualification('formal')
    with pytest.raises((RuntimeError,FileNotFoundError)):gates.require_execution_qualification('smoke')
    write(tmp_path/'configs/formal_v1.json',{'frozen':False})
    with pytest.raises(RuntimeError,match='registration'):gates.require_execution_qualification('formal')


def test_formal_real_cold_resume(tmp_path,monkeypatch):
    """One real renderer input through the new runner, never a GPU/model call."""
    import socket
    from .exps import cold_materialize,formal_validate
    from .utils import RQ,RESULTS,FormalSession
    monkeypatch.setattr(socket,'create_connection',lambda *a,**k:(_ for _ in ()).throw(AssertionError('No model network')))
    item=next(i for i in read(RQ/'configs/formal_v1.json')['items'] if i['task']=='QA' and i['arm']=='SEM')
    audit=read(RESULTS/'qa'/item['oid']/'audit.json')
    import json
    class Offline:
        last_usage={'input_tokens':16600,'output_tokens':100,'image_tokens':16384,'offline_fixture':True}
        def __call__(self,r):return json.dumps(audit['gold'])
    s=FormalSession(tmp_path/'execution',Offline(),limit=1)
    result=s.run_item(item,cold_materialize,lambda:audit,formal_validate)
    assert result['input_validation']['status']=='passed' and result['outcome']['qa']['accuracy']==1
    assert result['continuous_cold_seconds']>0
    assert s.run_item(item,lambda *a:1/0,lambda:1/0,lambda *a:1/0)==result
    s.close()


def test_formal_qualified_generation_unchanged():
    from .gates import formal_generation_compatibility,formal_runtime_environment
    value=formal_generation_compatibility()
    assert value['status']=='passed' and len(value['unchanged_generation_definitions'])>55
    assert formal_runtime_environment()['status']=='passed'


def test_formal_attention_retry_preserves_previous_attempt(tmp_path):
    import multiprocessing,signal
    from .exps import formal_loop
    item,materialize,context,validate=formal_fixture()
    registration={'items':[item],'formal_attempt_cap':2}
    class Provider:
        last_usage={'input_tokens':1,'output_tokens':1,'image_tokens':0}
        def __init__(self,folder,kill):self.folder=folder;self.kill=kill;folder.mkdir(parents=True,exist_ok=False)
        def __call__(self,request):
            with (self.folder/(request['identity']+'.json')).open('x') as f:
                f.write('{"status":"measured"}');f.flush();os.fsync(f.fileno())
            if self.kill:os.kill(os.getpid(),signal.SIGKILL)
            return '{"q1":"1"}'
        def close(self):pass
    def child():
        formal_loop(tmp_path,registration,lambda p:Provider(p,True),materialize,lambda i:context(),validate)
    p=multiprocessing.get_context('fork').Process(target=child);p.start();p.join(10)
    assert p.exitcode==-signal.SIGKILL
    prior=list((tmp_path/'attention').rglob('*.json'));assert len(prior)==1
    body=prior[0].read_bytes()
    result=formal_loop(tmp_path,registration,lambda p:Provider(p,False),materialize,lambda i:context(),validate)
    assert result['status']=='complete' and result['calls']=={'complete':1,'interrupted':1}
    assert len(list((tmp_path/'attention').rglob('*.json')))==2 and prior[0].read_bytes()==body


def test_formal_no_model_when_only_reply_or_reference_remains(tmp_path):
    from .utils import FormalSession
    from .exps import formal_loop
    item,materialize,context,validate=formal_fixture()
    class Provider:
        last_usage={'input_tokens':1,'output_tokens':1,'image_tokens':0}
        def __call__(self,r):return '{"q1":"1"}'
    s=FormalSession(tmp_path/'execution',Provider(),limit=1)
    def stop(point):
        if point=='after_response':raise RuntimeError('simulated lost process')
    with pytest.raises(RuntimeError):s.run_item(item,materialize,context,validate,fault=stop)
    s.close()
    alias={**item,'key':'alias','reference':item['key']}
    result=formal_loop(tmp_path,{'items':[item,alias],'formal_attempt_cap':1},lambda p:1/0,
                       lambda *a:1/0,lambda i:context(),validate)
    assert result['status']=='complete' and result['calls']=={'complete':1}
    assert read(tmp_path/'execution/completed/one.json')['continuous_cold_seconds'] is None


def test_formal_readiness_rejects_changed_dependency(tmp_path,monkeypatch):
    from . import gates,exps
    from .utils import sha
    monkeypatch.setattr(gates,'ROOT',tmp_path);monkeypatch.setattr(gates,'RQ',tmp_path/'rq')
    monkeypatch.setattr(gates,'RESULTS',tmp_path/'results')
    source=tmp_path/'code.py';source.write_text('original')
    checks=tmp_path/'results/checked.json';write(checks,{'passed':True})
    cpu=tmp_path/'results/qualification_complete.json'
    write(cpu,{'source_hashes':{'code.py':sha(source)},'check_hashes':{'checked.json':sha(checks)}})
    config=tmp_path/'rq/configs/formal_v1.json';write(config,{'prior_smoke_calls':{'attempts':19}})
    ready=tmp_path/'results/formal_readiness.json'
    write(ready,{'status':'ready','bindings':{'qualification_complete.json':sha(cpu)},'formal_registration_sha256':sha(config)})
    monkeypatch.setattr(exps,'formal_prior_calls',lambda:{'attempts':19})
    monkeypatch.setattr(gates,'formal_runtime_environment',lambda:{'status':'passed'})
    assert gates.formal_readiness()['status']=='ready'
    source.write_text('different')
    with pytest.raises(RuntimeError,match='source'):gates.formal_readiness()
    source.write_text('original');write(checks,{'passed':False})
    with pytest.raises(RuntimeError,match='artifact'):gates.formal_readiness()


def test_formal_rca_uses_central_scorer_without_private_provider_data(tmp_path):
    import json
    from .utils import FormalSession,digest
    candidates=['111','222','333','444','555'];seen=[]
    item={'key':'rca','oid':'offline','arm':'SEM','task':'RCA','reference':None,'identity':digest('rca')}
    context={'candidates':candidates,'numeric_to_natural':dict(zip(candidates,candidates)),'accepted':['222']}
    def materialize(i,p):
        return {'identity':i['identity'],'system':'static','instruction':'static','images':[],
                'operation':'full','groups':[],'task':'RCA','seed':42}
    def provider(r):
        assert not {'candidates','numeric_to_natural','accepted','gold'} & set(r)
        seen.append(r);return json.dumps({'services':candidates,'reason':'offline','confidence':'low'})
    s=FormalSession(tmp_path/'execution',provider,limit=2)
    value=s.run_item(item,materialize,lambda:context,lambda *a:{'status':'passed'})
    assert value['outcome']['metrics']['mrr']==.5
    s.provider=lambda r:json.dumps({'services':['999','222','333','444','555'],'reason':'offline','confidence':'low'})
    bad=s.run_item({**item,'key':'bad','identity':digest('bad')},materialize,lambda:context,lambda *a:{'status':'passed'})
    assert bad['outcome']['status']=='model_failure' and bad['outcome']['metrics']['mrr']==0
    s.close()


def test_formal_launcher_background_and_duplicate_lock(tmp_path,monkeypatch):
    import subprocess
    from . import exps,gates,utils
    from .utils import FormalSession
    monkeypatch.setattr(exps,'RESULTS',tmp_path)
    monkeypatch.setattr(gates,'require_execution_qualification',lambda stage:None)
    commands=[]
    class Child:
        pid=12345
        def poll(self):return None
    def start(command,**kwargs):
        commands.append((command,kwargs));assert kwargs['start_new_session'] and kwargs['stdin']==subprocess.DEVNULL
        return Child()
    monkeypatch.setattr(subprocess,'Popen',start)
    monkeypatch.setattr(utils,'formal_status',lambda root:{'owner':{'pid':12345},'live':True})
    result=exps.launch_formal()
    assert result['status']=='launched' and commands[0][0][-1]=='formal-worker'
    session=FormalSession(tmp_path/'formal_v1/execution',None,limit=1)
    with pytest.raises(BlockingIOError):exps.launch_formal()
    assert len(commands)==1;session.close()
