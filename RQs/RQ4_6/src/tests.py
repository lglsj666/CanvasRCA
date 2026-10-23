"""Authored CPU regressions; importing or static parsing never runs them."""
import unittest
import tempfile
import json
import math
from pathlib import Path
from copy import deepcopy
from . import exps
from .utils import RuntimeSession,save,stable,score_qa,read,RQ,RESULTS


class ScoringReaderTests(unittest.TestCase):
    def fixture(self,folder):
        from .utils import digest
        context={'candidates':['123'],'numeric_to_natural':{'123':'example-service'},'accepted':['example-service']}
        identity=stable(context);path=Path(folder)/'evaluation/contexts'/(identity+'.json');save(path,context)
        index={'schema':'RQ46EvaluationContextsV1','model_visible':False,'contexts':{'case':{
            'identity':identity,'sha256':digest(path),'path':str(path.relative_to(folder))}}}
        save(Path(folder)/'evaluation/index.json',index);return context,path,index

    def test_retained_context_does_not_depend_on_historical_checkout(self):
        from unittest.mock import patch
        from . import utils
        with tempfile.TemporaryDirectory() as folder:
            context,path,index=self.fixture(folder)
            with patch.object(utils,'RESULTS',Path(folder)),patch.object(utils,'HISTORY',Path(folder)/'absent'):
                self.assertEqual(utils.score_context('case'),context)
                with self.assertRaises(ValueError):utils.score_context('unknown')

    def test_tampered_context_and_escaping_reference_rejected(self):
        from unittest.mock import patch
        from . import utils
        with tempfile.TemporaryDirectory() as folder:
            context,path,index=self.fixture(folder)
            with patch.object(utils,'RESULTS',Path(folder)):
                save(path,dict(context,accepted=['changed']))
                with self.assertRaises(ValueError):utils.score_context('case')
                index['contexts']['case']['path']='../outside.json';save(Path(folder)/'evaluation/index.json',index)
                with self.assertRaises(ValueError):utils.score_context('case')


class SourceTests(unittest.TestCase):
    def fixture(self):
        raws=[('literal','Observed request pairs:\n[]',None),('literal','Continuous pair fields:\n[]',None),
            ('json','{"from":"123","to":"456","relation":"calls"}', '{"from":"123","to":"456","relation":"calls"}'),
            ('json','{"from":"1234","to":"12345","relation":"hosts"}', '{"from":"1234","to":"12345","relation":"hosts"}'),
            ('window','MET01 | 123 | baseline=0.0000',None)]
        atoms=[{'id':'a'+str(i),'kind':kind,'raw':raw,'value_wire':value,'part':i,'prefix':''} for i,(kind,raw,value) in enumerate(raws)]
        return {'organization':{'schema':'FullEvidenceOrganizationPacketV1','atoms':atoms,'neutral_edits':{},
            'sections':[{'part':i,'atoms':[a['id']]} for i,a in enumerate(atoms)]},'payload':{'relations':[{'id':'PAIR01'}]},
            'texts':{'RAW_TEXT':[{'type':'text','text':a['raw']} for a in atoms]},'candidates':['123','456','1234','12345']}

    def test_complete_pair_and_deployment_transfer_calls_stay_text(self):
        p=self.fixture();packet=exps.ownership(p,'H_POD_BRIDGE')
        self.assertEqual([r['owner'] for r in packet['records']],['image','image','text','image','text'])
        self.assertEqual(exps.residual_text(p,packet),[p['texts']['RAW_TEXT'][i] for i in (2,4)])

    def test_shared_facts_and_no_pair_fallback(self):
        p=self.fixture();p['payload']['relations']=[]
        a=exps.ownership(p,'H_POD_BRIDGE');b=exps.ownership(p,'H_POD_SEPARATE')
        self.assertEqual(a['records'],b['records']);self.assertTrue(a['fallback'])

    def test_duplicates_and_split_derivatives_fail(self):
        p=self.fixture();a=exps.ownership(p,'H_POD_BRIDGE');a['records'][1]['owner']='text'
        with self.assertRaises(ValueError):exps.audit_ownership(a)
        p['organization']['atoms'].append(p['organization']['atoms'][0])
        with self.assertRaises(ValueError):exps.ownership(p,'H_POD_BRIDGE')

    def test_prompt_repair_is_local_not_global_log_replacement(self):
        p=self.fixture();cfg=read(RQ/'configs/hybrid_instructions_v1.json')
        for raw in [cfg['original_window_rule'],'LOG observed template: '+cfg['obsolete_instruction']]:
            i=len(p['organization']['atoms']);aid='a'+str(i)
            p['organization']['atoms'].append({'id':aid,'kind':'literal','raw':raw,'value_wire':None,'part':i,'prefix':''})
            p['organization']['sections'].append({'part':i,'atoms':[aid]});p['texts']['RAW_TEXT'].append({'type':'text','text':raw})
        out=exps.residual_text(p,exps.ownership(p,'H_POD_BRIDGE'),qa=True)
        self.assertIn(cfg['replacement_window_rule'],[r['text'] for r in out])
        self.assertIn('LOG observed template: '+cfg['obsolete_instruction'],[r['text'] for r in out])
        self.assertNotIn(cfg['original_window_rule'],[r['text'] for r in out])

    def test_hybrid_ownership_factorization(self):
        p=self.fixture()
        for arm,want in [('H_DEPLOY_ONLY',{'deployment'}),('H_MARGINAL_PHASE',{'pair'}),('H_POD_PHASE',{'pair','deployment'})]:
            packet=exps.ownership(p,arm)
            self.assertEqual({r['family'] for r in packet['records'] if r['owner']=='image'},want)
            self.assertTrue(all(r['owner']=='text' for r in packet['records'] if r['family']=='topology'))
        self.assertEqual(exps.ownership(p,'H_POD_BRIDGE')['records'],exps.ownership(p,'H_POD_PHASE')['records'])

    def test_lexical_zero_exponents_escape_and_unknown_json(self):
        s='{"zero":0.0000,"large":1.2500e+100,"escape":"x\\ny","none":null}'
        self.assertEqual(exps.wire(exps.lexload(s)),s)
        with self.assertRaises(ValueError):exps.lexload('{"x":1,"x":2}')

    def pair_fixture(self):
        population={'n':20,'binary':[20,0,0,0],'quantiles':[[1,2],[3,4]],
            'conditional_child':[[0,20,3,4],[1,0,None,None]],'points':[[1,3]]*20}
        relation={'id':'PAIR01','parent':'123','parent_operation':'parent_op','child':'456',
            'child_operation':'child_op','unit':'ms','thresholds':[2,4],
            'phases':{p:deepcopy(population) for p in ('reference','current')}}
        binary=[['PAIR01','123','parent_op','456','child_op',[2,4],
            [[p,20,[20,0,0,0]] for p in ('reference','current')]]]
        continuous=[['PAIR01',[[p,[[1,2],[3,4]],[[0,20,3,4],[1,0,None,None]],[[1,3]]*20]
            for p in ('reference','current')]]]
        atoms=[{'id':name,'kind':'literal','raw':label+'\n'+json.dumps(value),'value_wire':None}
            for name,label,value in [('b','Observed request pairs:',binary),('c','Continuous pair fields:',continuous)]]
        return {'organization':{'atoms':atoms},'payload':{'relations':[relation]}}

    def test_pair_metadata_and_phase_membership_checked(self):
        original=self.pair_fixture();cards,_=exps.pair_cards(original)
        self.assertEqual(len(cards[0]['data']['samples']),40)
        for field,value in [('parent','789'),('child','789'),('parent_operation','wrong'),
                ('child_operation','wrong'),('thresholds',[9,9])]:
            p=deepcopy(original);p['payload']['relations'][0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):exps.pair_cards(p)
        p=deepcopy(original);p['organization']['atoms'][0]['raw']=p['organization']['atoms'][0]['raw'].replace('current','reference')
        with self.assertRaises(ValueError):exps.pair_cards(p)

    def test_pair_duplicate_tables_and_unmatched_nonempty_tables_fail(self):
        p=self.pair_fixture();p['organization']['atoms'].append(deepcopy(p['organization']['atoms'][0]))
        with self.assertRaises(ValueError):exps.pair_cards(p)

    def test_budget_pair_samples_are_observed_endpoints_and_statistics_unchanged(self):
        cards,_=exps.pair_cards(self.pair_fixture());original=deepcopy(cards)
        slim,audit=exps.budget_pair_cards(cards)
        self.assertEqual(cards,original);self.assertEqual(len(slim[0]['data']['samples']),16)
        self.assertEqual(slim[0]['data']['support'],[20,20])
        for phase,old in zip(slim[0]['data']['complete']['phases'],cards[0]['data']['complete']['phases']):
            self.assertEqual(phase['sampled'],'8')
            for field in ('n','binary','quantiles','conditional_child'):self.assertEqual(phase[field],old[field])
        self.assertEqual(audit[0]['retained_ids'][0],'R01');self.assertEqual(audit[0]['retained_ids'][-1],'R20')

    def test_budget_projection_omits_arrays_keeps_zero_extrema_and_original_lexemes(self):
        p=self.pair_fixture();p['organization'].update(neutral_edits={},sections=[])
        value=exps.lexload('{"field":"metric_series_64","values_codec":[0.0000,null,1.200e+2],"missing_codec":{"length":3,"value_positions":[[false,"0,2"],[true,"1"]]},"baseline":"0.0000","peak":"1.200e+2"}')
        raw='Metric evidence; field=metric_series_64; baseline="0.0000" peak="1.200e+2" values_codec='+exps.wire(value['values_codec'])+' missing_codec='+exps.wire(value['missing_codec'])+'\n'
        p['organization']['atoms'].append({'id':'m','kind':'assignment','raw':raw,'value_wire':exps.wire(value)})
        aux=exps.lexload('{"id":"AUX01","entity":"1234","metric":"memory","unit":"bytes","values_codec":{"length":4,"value_positions":[[1.200e+2,"0,2"],[null,"1"],[0.0000,"3"]]}}')
        table=exps.wire({'fields':list(aux),'series':[list(aux.values())]})
        p['organization']['atoms'].append({'id':'aux','kind':'aux','raw':table,'value_wire':exps.wire(aux)})
        p['organization']['sections'].append({'atoms':['aux'],'table_container':{'raw':table}})
        before=deepcopy(p);text='\n'.join(a['raw'] for a in p['organization']['atoms'])
        result,audit=exps.budget_hybrid_text(p,text)
        self.assertEqual(p,before);self.assertNotIn('values_codec',result);self.assertNotIn('missing_codec',result)
        self.assertIn('0.0000',result);self.assertIn('1.200e+2',result);self.assertIn('metric_window_summary',result)
        self.assertIn('at most eight',result.lower());self.assertFalse(audit['lossless'])
        self.assertTrue(any(a['source']=='aux' for a in audit['omissions']))

    def test_codec_rejects_duplicate_or_incomplete_observation_positions(self):
        self.assertEqual(exps.observed_codec_points([0,None,2]),[(0,0),(2,2)])
        for codec in ({'length':3,'value_positions':[[0,'0-1'],[1,'1-2']]},
                {'length':3,'value_positions':[[0,'0-1']]}):
            with self.assertRaises(ValueError):exps.observed_codec_points(codec)
        p=self.pair_fixture();p['payload']['relations']=[]
        with self.assertRaises(ValueError):exps.pair_cards(p)

    def test_topology_compiler_keeps_isolated_role_entity(self):
        value={'kind':'graph','data':{'edges':[['1234','12345','hosts']],
            'roles':[['1234','observed host'],['5678','isolated observed node']]}}
        atom={'id':'g','kind':'component','raw':'graph','value_wire':json.dumps(value)}
        cards,bindings=exps.topology_cards({'organization':{'atoms':[atom]}})
        self.assertEqual({n['id'] for n in cards[0]['data']['nodes']},{'1234','12345','5678'})
        self.assertTrue(any(b['binding']=='GDEP.node.5678' for b in bindings))
        value['data']['edges']=[];atom['value_wire']=json.dumps(value)
        with self.assertRaises(ValueError):exps.topology_cards({'organization':{'atoms':[atom]}})


class GeometryTests(unittest.TestCase):
    def fixture(self):
        return {'id':'G','kind':'graph','data':{'nodes':[{'id':i,'type':t} for i,t in [('123','service'),('124','service'),('1234','node'),('12345','pod'),('54321','pod')]],
            'edges':[{'id':'e0','source':'123','target':'12345','kind':'has_instance'},
                {'id':'e1','source':'1234','target':'12345','kind':'hosts'},
                {'id':'e2','source':'124','target':'12345','kind':'owns'},
                {'id':'e3','source':'123','target':'12345','kind':'has_instance'}]}}
    def test_multiple_owners_parallel_edges_and_isolates_survive(self):
        from renderer.pod_relations import pod_relation_layout
        card=self.fixture()
        for variant in ('bridge','separate'):
            g=pod_relation_layout(card,2000,variant)
            self.assertCountEqual([e for r in g['rows'] for side in ('left','right') for e in r[side]],['e0','e1','e2','e3'])
            self.assertEqual(g['isolates'],['54321']);self.assertEqual(g['font'],28)
    def test_direction_unknown_kind_and_duplicate_identity_fail(self):
        from renderer.pod_relations import pod_relation_layout
        for change in ('reverse','kind','duplicate'):
            c=self.fixture()
            if change=='reverse':c['data']['edges'][0].update(source='12345',target='123')
            elif change=='kind':c['data']['edges'][0]['kind']='causes'
            else:c['data']['nodes'].append(c['data']['nodes'][0])
            with self.assertRaises(ValueError):pod_relation_layout(c,2000,'bridge')
    def test_no_shrinking_and_long_role_wrapping(self):
        from renderer.pod_relations import pod_relation_layout
        c=self.fixture()
        with self.assertRaises(ValueError):pod_relation_layout(c,600,'separate')
        c['data']['nodes'][0]['role']='x'*200;g=pod_relation_layout(c,2000,'bridge')
        self.assertGreater(len(g['labels']['123']),1);self.assertEqual(g['font'],28)
        narrow=pod_relation_layout(self.fixture(),976,'separate')
        self.assertEqual(narrow['labels']['123'],['service 123'])

    def test_long_role_changes_only_its_own_rows(self):
        from renderer.pod_relations import pod_relation_layout
        card=self.fixture();card['data']['edges'].append({'id':'e4','source':'1234','target':'54321','kind':'hosts'})
        before=pod_relation_layout(card,1004,'bridge')
        card['data']['nodes'][0]['role']='database'
        after=pod_relation_layout(card,1004,'bridge')
        self.assertGreater(after['rows'][0]['step'],before['rows'][0]['step'])
        self.assertEqual(after['rows'][1]['step'],before['rows'][1]['step'])
        self.assertEqual(after['font'],28)


class PruningTests(unittest.TestCase):
    def fixture(self):
        s={'anchors':[0,5,10,15],'roles':{'r':{'tokens':[1,2,6,7,11,12,16,17]},'v':{'tokens':[2,7]}},'image_tokens':20,'grid':[4,5]}
        p={'roles':[{'id':'r','targets':[{'binding':'MET001.sample.1','part':'all'}]},
            {'id':'v','targets':[{'binding':'MET001.detail.0','part':'value'}]}]}
        return s,p
    def test_uniform_matches_independent_exhaustive_distances(self):
        s,_=self.fixture();e=set().union(*(set(v['tokens']) for v in s['roles'].values()));chosen=set(s['anchors'])
        for _ in range(math.ceil(len(e)/2)):
            t=min(e-chosen,key=lambda t:(-min(math.hypot(t%5-a%5,t//5-a//5) for a in chosen),t));chosen.add(t)
        self.assertEqual(exps.uniform_plan(s)['retained'],sorted(chosen))
    def test_same_budget_anchors_domain_gap_and_monotonic_objective(self):
        s,p=self.fixture();base=exps.uniform_plan(s)['retained']
        for arm in exps.PRUNING_ARMS:
            result=exps.refined_uniform(arm,s,p,base);keep=set(result['retained'])
            self.assertEqual(len(keep),len(base));self.assertTrue(set(s['anchors'])<=keep)
            self.assertGreaterEqual(result['final_objective'],result['initial_objective'])
            for t in result['evidence']:self.assertLessEqual(min(exps.distance2(t,a,5) for a in keep),1)
            self.assertEqual(result,exps.refined_uniform(arm,s,p,base))
    def test_shared_tokens_not_double_charged_or_synthetic(self):
        s,p=self.fixture();g,n=exps.pruning_groups(s,p)
        self.assertEqual(g,[frozenset((2,7))]);self.assertIn(frozenset((1,2)),n)
        p['roles'].append(dict(p['roles'][1],id='v2'));s['roles']['v2']=s['roles']['v']
        self.assertEqual(exps.pruning_groups(s,p),(g,n))
    def test_no_effect_never_reported_as_intervention(self):
        s={'anchors':[0],'roles':{},'image_tokens':1,'grid':[1,1]}
        p=exps.refined_uniform('P_U_COMBINED',s,{'roles':[]},[0])
        self.assertEqual(p['optional_replacement_fraction'],0);self.assertEqual(p['initial_objective'],p['final_objective'])


class QATests(unittest.TestCase):
    def test_complete_and_partial_relations_are_distinguished(self):
        expected={f'q{i}':None for i in range(1,7)};expected['q1']={'entity':'123','relation':'owns','targets':['12345','54321']}
        got=deepcopy(expected);got['q1']={'entity':'service 123','relation':'owns','targets':['pod 12345']}
        result=score_qa(json.dumps(got),expected)
        self.assertEqual(result['tolerant'],0);self.assertEqual(result['questions']['q1']['endpoint_recall'],.5)
        got['q1']['targets'].append('54321');self.assertEqual(score_qa(json.dumps(got),expected)['tolerant'],1)
    def test_numeric_binding_unit_and_value_separately_scored(self):
        expected={f'q{i}':None for i in range(1,7)};expected['q1']={'entity':'123','unit':'µs','values':['0.1000']}
        got=deepcopy(expected);got['q1']={'entity':'service 124','unit':'us','values':['1e-1']}
        r=score_qa(json.dumps(got),expected)['questions']['q1']
        self.assertTrue(r['numeric_correct']);self.assertTrue(r['unit_correct']);self.assertFalse(r['entity_correct']);self.assertFalse(r['tolerant'])
    def test_relation_join_oracle(self):
        from unittest.mock import patch
        card=GeometryTests().fixture();card['id']='GDEP'
        with patch.object(exps,'topology_cards',return_value=([card],[])):
            questions,answers,proof=exps.relation_questions({},'synthetic')
        for key in ('q5','q6'):
            self.assertEqual(answers[key]['targets'],['1234']);self.assertIn(answers[key]['entity'],['123','124'])
        self.assertEqual(questions,exps_questions_again(card))


def exps_questions_again(card):
    from unittest.mock import patch
    with patch.object(exps,'topology_cards',return_value=([card],[])):return exps.relation_questions({},'synthetic')[0]


class RetentionPreparationTests(unittest.TestCase):
    def test_only_verified_redundant_preparation_and_unreachable_objects_retire(self):
        from unittest.mock import patch
        from . import utils
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);save(root/'formal/phase_complete.json',{'status':'complete'})
            request={'identity':'same','prompt':'exact diagnostic input','attention':True}
            save(root/'frozen/formal_queue.json',[{'request':request}])
            save(root/'inputs/case/requests.json',{'arm':dict(request,attention=False)})
            keep_data=b'actual image';old_data=b'unused CPU image'
            names=[utils.hashlib.sha256(v).hexdigest()+'.png' for v in (keep_data,old_data)]
            (root/'objects').mkdir()
            for name,data in zip(names,(keep_data,old_data)):(root/'objects'/name).write_bytes(data)
            save(root/'formal/requests/call.json',dict(request,images=['objects/'+names[0]],
                historical_reference='RQs/Other/results/objects/'+names[1]))
            with patch.object(utils,'RESULTS',root):
                utils.retire_preparation_duplicates({root/'objects'/names[0]})
                self.assertFalse((root/'inputs/case/requests.json').exists())
                self.assertTrue((root/'formal/requests/call.json').exists());self.assertTrue((root/'objects'/names[0]).exists())
                self.assertFalse((root/'objects'/names[1]).exists())
                utils.retire_preparation_duplicates({root/'objects'/names[0]})

    def test_mismatched_preparation_is_preserved_and_blocks_retirement(self):
        from unittest.mock import patch
        from . import utils
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);save(root/'formal/phase_complete.json',{'status':'complete'})
            save(root/'frozen/formal_queue.json',[{'request':{'identity':'same','prompt':'exact'}}])
            path=root/'inputs/case/requests.json';save(path,{'arm':{'identity':'same','prompt':'different'}})
            with patch.object(utils,'RESULTS',root):
                with self.assertRaises(ValueError):utils.retire_preparation_duplicates(set())
            self.assertTrue(path.exists())


class RuntimeTests(unittest.TestCase):
    def test_same_case_multiple_qa_contexts_and_reference_rescoring(self):
        expected={f'q{i}':None for i in range(1,7)}
        expected['q1']={'entity':'123','unit':'ms','values':['1']}
        class OfflineProvider:
            calls=0;last_usage={'input_tokens':10,'output_tokens':3}
            def __call__(self,request):
                self.calls+=1;return json.dumps(expected)
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);provider=OfflineProvider();session=RuntimeSession(root/'run',provider,ledger_folder=root)
            try:
                request={'identity':stable('qa-a'),'task':'QA'}
                one=session.run({'id':'same-case','key':'one','variant':'QA'},request,lambda:expected)
                different=deepcopy(expected);different['q1']={'entity':'123','relation':'hosts','targets':['12345']}
                two=session.run({'id':'same-case','key':'two','variant':'QA'},
                    {'identity':stable('qa-b'),'task':'QA'},lambda:different)
                self.assertNotEqual(one['scoring_context_path'],two['scoring_context_path'])
                self.assertEqual(one['outcome']['tolerant'],1);self.assertEqual(two['outcome']['tolerant'],0)
                ref=session.run({'id':'another-case','key':'ref','variant':'QA','reference':'one'},request,lambda:different)
                self.assertEqual(ref['actual_calls'],0);self.assertEqual(ref['outcome']['tolerant'],0)
                self.assertEqual(ref['response'],one['response']);self.assertEqual(provider.calls,2)
                self.assertEqual(read(root/'run'/one['scoring_context_path']),expected)
            finally:session.close()

    def test_qualification_rejects_equal_count_duplicate_or_mislabelled_cases(self):
        from .gates import require_case_coverage
        expected=[{'id':'a','dataset':'one'},{'id':'b','dataset':'two'}]
        rows=[dict(r,status='passed') for r in expected]
        require_case_coverage({'cases':rows},expected)
        for bad in ([rows[0],rows[0]],[rows[0],dict(rows[1],dataset='one')],[rows[0]]):
            with self.assertRaises(ValueError):require_case_coverage({'cases':bad},expected)

    def test_finalization_resumes_cleanup_and_never_links_live_source(self):
        from unittest.mock import patch
        from . import utils
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);rq=root/'RQs/RQ4_6';results=rq/'results';formal=results/'formal'
            save(formal/'phase_complete.json',{'status':'complete'})
            save(results/'frozen/formal_queue.json',[{'item':{'key':'one'}}])
            context={f'q{i}':None for i in range(1,7)}
            save(formal/'scoring/qa.json',context)
            save(formal/'requests/one.json',{'identity':'test','images':[],'image_sha256':[],'attention':False})
            save(formal/'completed/one.json',{'request_hash':'test','request_path':'requests/one.json',
                'scoring_context_path':'scoring/qa.json','scoring_context_identity':stable(context),
                'artifact_hashes':{},'actual_calls':1,'attempt_id':1})
            save(results/'cache/reproducible.json',{'temporary':True})
            live=rq/'src/example.py';frozen=results/'frozen/source/example.py'
            live.parent.mkdir(parents=True);frozen.parent.mkdir(parents=True)
            live.write_text('immutable = 1\n');frozen.write_text(live.read_text())
            with patch.multiple(utils,ROOT=root,RQ=rq,RESULTS=results):
                with patch('shutil.rmtree',side_effect=OSError('interrupted cleanup')):
                    with self.assertRaises(OSError):utils.finalize_retention()
                self.assertFalse(read(results/'retention.json')['cache_cleanup_complete'])
                report=utils.finalize_retention()
                self.assertTrue(report['cache_cleanup_complete']);self.assertFalse((results/'cache').exists())
                self.assertNotEqual(live.stat().st_ino,frozen.stat().st_ino)
                live.write_text('immutable = 2\n');self.assertEqual(frozen.read_text(),'immutable = 1\n')

    def test_serial_ledger_eight_writers_and_durable_reopen(self):
        from concurrent.futures import ThreadPoolExecutor
        from .utils import serialized_call_register
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'calls.sqlite';ledger=serialized_call_register(path,32,'offline',18)
            def transaction(i):
                attempt,_=ledger.begin(str(i),str(i),'QA')
                ledger.finish(attempt,{'output':i});return attempt
            with ThreadPoolExecutor(max_workers=8) as pool:ids=list(pool.map(transaction,range(18)))
            self.assertEqual(len(set(ids)),18);self.assertEqual(ledger.summary(),{'complete':18})
            self.assertEqual(ledger.db.execute('PRAGMA journal_mode').fetchone()[0],'delete')
            self.assertEqual(ledger.db.execute('PRAGMA synchronous').fetchone()[0],2)
            with self.assertRaises(RuntimeError):ledger.begin('overflow','overflow','QA')
            ledger.close();ledger=serialized_call_register(path,32,'offline',18)
            try:self.assertEqual(ledger.summary(),{'complete':18});self.assertEqual(ledger.cached('0','0','QA'),{'output':0})
            finally:ledger.close()

    def test_ledger_owner_excludes_other_run_folders(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);one=RuntimeSession(root/'one',ledger_folder=root)
            try:
                with self.assertRaises(BlockingIOError):RuntimeSession(root/'two',ledger_folder=root)
            finally:one.close()

    def test_cpu_preparation_interleaves_registered_sources(self):
        from RQs.RQ4_1.src.utils import source_order
        rows=[{'dataset':ds,'source':str(s),'id':(ds,s,i)} for ds in ('aiops2022','aiops2025') for s in range(4) for i in range(2)]
        ordered=source_order(rows)
        self.assertEqual(len({(r['dataset'],r['source']) for r in ordered[:8]}),8)
        self.assertEqual({r['id'] for r in ordered},{r['id'] for r in rows})

    def test_power_loss_commit_reference_repeat_pause(self):
        class OfflineProvider:
            calls=0;last_usage={'input_tokens':10,'output_tokens':3}
            def __call__(self,request):
                self.calls+=1;return json.dumps({f'q{i}':None for i in range(1,7)})
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);provider=OfflineProvider();request={'identity':stable('offline'),'task':'QA'}
            expected={f'q{i}':None for i in range(1,7)};item={'key':'one','variant':'BASE'}
            session=RuntimeSession(root/'run',provider,ledger_folder=root)
            def crash(stage):
                if stage=='after_response':raise RuntimeError('simulated power loss')
            with self.assertRaises(RuntimeError):session.run(item,request,lambda:expected,crash)
            session.close();session=RuntimeSession(root/'run',provider,ledger_folder=root);session.recover()
            session.run(item,request,lambda:expected);self.assertEqual(provider.calls,1)
            session.run(item,request,lambda:expected);self.assertEqual(provider.calls,1)
            ref=session.run({'key':'ref','variant':'BASE','reference':'one'},request,lambda:expected);self.assertEqual(ref['actual_calls'],0)
            with self.assertRaises(ValueError):session.run({'key':'bad','variant':'REPEAT','reference':'one'},request,lambda:expected)
            session.run({'key':'repeat','variant':'REPEAT'},request,lambda:expected);self.assertEqual(provider.calls,2)
            save(root/'run/PAUSE',{'pause':True});self.assertEqual(session.run({'key':'paused','variant':'BASE'},request,lambda:expected)['status'],'paused')
            session.close()

    def test_duplicate_owner_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            one=RuntimeSession(Path(folder)/'run',ledger_folder=folder)
            try:
                with self.assertRaises(BlockingIOError):RuntimeSession(Path(folder)/'run',ledger_folder=folder)
            finally:one.close()

    def test_multimodal_gather_preserves_text_and_positions(self):
        import torch
        from .utils import multimodal_gather
        ids=torch.tensor([5,99,99,6,99,99,7]);positions=torch.arange(7).repeat(3,1)
        keep,coords,delta,images=multimodal_gather(ids,positions,99,[2,2],[[1],[0]])
        self.assertEqual(keep,[0,2,3,4,6]);self.assertEqual(coords[0].tolist(),keep);self.assertEqual(delta,2)

    def test_attention_storage_budget(self):
        from vlmrca.vlm.passive_summary import AttentionStore
        self.assertLessEqual(AttentionStore.storage_ceiling(10000),1000000000)

    def test_attention_distinguishes_every_image_header_and_preserves_text(self):
        from copy import deepcopy
        from .utils import attention_regions
        request={'hybrid':True,'grid_thw':[[1,8,4]]*2,'geometry':[
            {'width':64,'height':128,'panels':[{'card':'p'+str(i),'box':[0,86,64,42]}]} for i in range(2)]}
        before=deepcopy(request);images=list(range(8))+list(range(9,17))
        result=attention_regions(request,[8,8],images,list(range(17)),17)
        self.assertEqual(request,before)
        for i in range(2):
            self.assertEqual(result['ids'].count(result['names'].index(f'image:{i}:header')),6)
            self.assertEqual(result['ids'].count(result['names'].index(f'image:{i}:panel:p{i}')),2)
        self.assertEqual(result['ids'][8],1)

    def test_attention_empty_transfer_is_text_only(self):
        from .utils import attention_regions
        result=attention_regions({'hybrid':True,'grid_thw':[],'geometry':[]},[],[],[0,2],3)
        self.assertEqual(result,{'ids':[1,1],'names':['other:generated','text:instructions_and_evidence']})

def run_tests():
    import io
    from .gates import require_cpu
    require_cpu()
    suite=unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__,fromlist=['*']))
    buffer=io.StringIO();result=unittest.TextTestRunner(stream=buffer,verbosity=2).run(suite)
    return {'status':'passed' if result.wasSuccessful() else 'failed','tests':result.testsRun,
        'failures':len(result.failures),'errors':len(result.errors),'log':buffer.getvalue(),'new_model_calls':0}


def check_visual_determinism():
    from .utils import digest,ROOT,offline
    from .gates import require_cpu,execution_fingerprint
    from renderer.main import render
    require_cpu();offline();checks=[]
    for oid in read(RQ/'configs/protocol_v1.json')['smoke_ids']:
        source=read(RESULTS/'inputs'/oid/'source.json')
        for arm in (*exps.HYBRID_ARMS,*exps.RELATION_VISUAL_ARMS):
            for i,image in enumerate(source['images_by_arm'][arm]):
                if 'evidence' in image:evidence,design=image['evidence'],image['design']
                elif 'evidence_ref' in image:evidence,design=read(ROOT/image['evidence_ref']),read(ROOT/image['design_ref'])
                else:continue
                folder=RESULTS/'cache/determinism'/oid/arm/str(i)
                save(folder/'evidence.json',evidence);save(folder/'design.json',design)
                target=folder/'render'
                if not target.exists():render(folder/'evidence.json',folder/'design.json',target)
                if digest(target/'dashboard.png')!=image['sha256']:raise ValueError('Deterministic repaint differs')
                checks.append({'case':oid,'arm':arm,'image':i})
    if not checks:raise ValueError('No actual deterministic repaint covered')
    result={'status':'passed','execution_fingerprint':execution_fingerprint(),'checks':checks,'new_model_calls':0}
    save(RESULTS/'qualification/determinism.json',result);return result


def check_transport_invariance():
    from transformers import AutoProcessor
    from .utils import MODEL,offline,vllm_prompt_packet
    from .gates import require_cpu,execution_fingerprint
    require_cpu();offline();processor=AutoProcessor.from_pretrained(MODEL,local_files_only=True);checks=[]
    for oid in read(RQ/'configs/protocol_v1.json')['smoke_ids']:
        for arm,request in read(RESULTS/'mechanism'/oid/'requests.json').items():
            on=vllm_prompt_packet(request,processor);off=deepcopy(request);off['attention']=False;off=vllm_prompt_packet(off,processor)
            for field in ('keep','token_ids','image_positions'):
                if on[field]!=off[field]:raise ValueError('Passive measurement changed input')
            for field in ('positions','rope_delta','length'):
                if on['metadata'][field]!=off['metadata'][field]:raise ValueError('Passive measurement changed MRoPE')
            checks.append({'case':oid,'arm':arm})
    result={'status':'passed','execution_fingerprint':execution_fingerprint(),'checks':checks,'new_model_calls':0}
    save(RESULTS/'qualification/transport_audit.json',result);return result
