"""Independent offline counterexamples; model answer correctness is not a gate."""
import unittest
from .utils import receive_selection,receive_qa,score_qa,validate_qa_item


def question(mode='single',solutions=None,kind='number',**extra):
    return dict(id='q1',question='Read the indicated visible value.',type=kind,mode=mode,
                solutions=solutions if solutions is not None else [['0']],
                proof={'binding':'TEST.value','display':'0'},support_cards=['TEST'],**extra)


class ReceiverTests(unittest.TestCase):
    def test_phase_field_alias_is_semantic_not_oracle_based(self):
        q=question(kind='string',solutions=[['current']],semantic={'field':'exclusive_latency_phase_comparison'})
        for answer in ('exl_p95_fault_us','exl_p95_fault_us is larger','current phase is higher.'):
            self.assertEqual(score_qa('Q1: '+answer,[q])['conditional_credit'],1.)
        for answer in ('exl_p95_base_us','exl_p95_fault_us or exl_p95_base_us'):
            self.assertEqual(score_qa('Q1: '+answer,[q])['conditional_credit'],0.)
        q['solutions']=[['reference']]
        self.assertEqual(score_qa('Q1: exl_p95_base_us is larger',[q])['conditional_credit'],1.)
        self.assertEqual(score_qa('Q1: exl_p95_fault_us',[q])['conditional_credit'],0.)
        del q['semantic']
        self.assertEqual(score_qa('Q1: exl_p95_base_us',[q])['conditional_credit'],0.)

    def test_actual_hybrid_relation_encodings(self):
        import json
        from .exps import text_relation_targets
        line='directed_call_edge: '+json.dumps({'caller':'844','callee':'945'})
        packed=json.dumps({'columns':['kind','data'],'rows':[['graph',{'edges':[['844','123','calls'],['844','777','hosts']]}]]})
        targets,proof,domain=text_relation_targets('unused',line+'\n'+packed,'844','calls')
        self.assertEqual(targets,{'945','123'});self.assertEqual(domain,{'844','945','123','777'})
        self.assertTrue(all(p['visible_raw'] in (line,packed) for p in proof))
        self.assertEqual(text_relation_targets('unused',line,'945','calls')[0],set())
        self.assertEqual(text_relation_targets('unused','explanation: 844 -> 945 calls','844','calls')[0],set())
        self.assertEqual(text_relation_targets('unused',packed,'844','hosts')[0],{'777'})

    def test_independent_repeat_never_supplies_reference_cache(self):
        from .utils import remember_reference
        repeat={'item':{'force_call':True},'generation_identity':'same','raw':'answer'}
        regular=dict(repeat,item={'force_call':False});known={}
        self.assertFalse(remember_reference(known,'repeat',repeat));self.assertEqual(known,{})
        self.assertTrue(remember_reference(known,'base',regular));self.assertEqual(known,{'same':'base'})
        remember_reference(known,'repeat',repeat);self.assertEqual(known,{'same':'base'})
        resumed={}
        for key,record in [('repeat',repeat),('base',regular)]:remember_reference(resumed,key,record)
        self.assertEqual(resumed,known)

    def test_typed_relation_summary_requires_registered_shape(self):
        from .exps import is_relation_summary
        def card(fields):
            return {'kind':'inventory','title':'Observed source summary',
                    'data':{'details':[{'name':k,'value':v} for k,v in fields.items()]}}
        relation={'parent · 0':'849','parent · 1':'op1','child · 0':'381','child · 1':'op2',
                  'relation':'observed parent span -> child span'}
        self.assertTrue(is_relation_summary(card(relation)))
        self.assertTrue(is_relation_summary(card({'edge':'849 → 381','supporting_span_pairs':'53197'})))
        self.assertFalse(is_relation_summary(card(dict(relation,relation='unknown'))))
        self.assertFalse(is_relation_summary(card({'edge':'849','supporting_span_pairs':'53197'})))
        self.assertFalse(is_relation_summary(card(dict(relation,unknown_field='must not disappear'))))

    def test_metric_only_incident_has_displayed_nonempty_questions(self):
        import tempfile,json
        from pathlib import Path
        from unittest.mock import patch
        from .exps import make_qa_targets,make_qa_request
        with tempfile.TemporaryDirectory() as tmp:
            render=Path(tmp)/'render';render.mkdir()
            (render/'dashboard.html').write_text('<div data-card="MET001"><span data-binding="MET001.entity">service 906</span>'
                '<span data-binding="MET001.unit">source unit</span><div data-binding="MET001.detail.0">baseline 0</div>'
                '<div data-binding="MET001.detail.1">peak 2</div></div>')
            card={'id':'MET001','kind':'metric','title':'MET01 · timeout','entity':'906','unit':'source_unit',
                  'data':{'details':[{'name':'baseline','value':'0'},{'name':'peak','value':'2'}]}}
            inv={'id':'fixture','base':tmp,'cards':[{'card':'MET001','index':'7'}],
                 'evidence':{'cards':[card]},'overview':{'sha256':'fixture'}}
            items=make_qa_targets(inv)
            self.assertEqual([q['solutions'] for q in items],[[['2']],[['906']],[['source unit']],[['peak']]])
            self.assertNotIn('906',items[1]['question'])
            text='Metric evidence; fact_id="MET01"; field=metric_window_summary; entities=["906"]; unit="source_unit"; baseline="0" peak="2"'
            base=dict(images=[],image_sha256=[],grid_thw=[],retained_by_image=[],geometry=[])
            with patch('RQs.RQ4_8.src.exps.make_request',side_effect=lambda *args,**kwargs:{'qa_items':kwargs['items']}):
                request,actual=make_qa_request(None,base,inv,items,'H_TIME_RESTORE',text_evidence=text)
            self.assertTrue(all(q['available'] for q in actual))
            response=json.dumps({'answers':[{'id':q['id'],'answer':q['solutions'][0][0]} for q in actual]})
            self.assertEqual(score_qa(response,request['qa_items'])['conditional_credit'],1.)

    def selection(self,text):return receive_selection(text,['1','2','3','4'],['2','3','4'])

    def test_selection_canonical(self):
        out=self.selection('{"keep_card_indices":[2,3]}')
        self.assertTrue(out['executable']);self.assertTrue(out['strict_format']);self.assertEqual(out['selected'],['2','3'])

    def test_selection_format_and_invalid_ids(self):
        fixtures=['Here is the answer:\n```json\n{keep_card_indices:["02",999,3,3,],}\n```',
                  'keep cards: 2, 3', '- 2\n- 3', '{"keep_cards":["card 2", "#3", false]}']
        for raw in fixtures:
            with self.subTest(raw=raw):self.assertEqual(self.selection(raw)['selected'],['2','3'])

    def test_selection_empty_and_protected(self):
        for raw in ['{"keep_card_indices":[]}','{"keep_card_indices":[999]}','{"keep_card_indices":[1]}']:
            with self.subTest(raw=raw):self.assertFalse(self.selection(raw)['executable'])

    def test_selection_not_rationale_digits(self):
        for raw in ['Service 2 had 3 errors; probability 0.7.','For example [2,3], but I choose [4].',
                    'The error counter values were [2,3].','For example [2,3].',
                    '{"keep_cards":[2],"delete_card_indices":[3]}','delete: [2,3]']:
            with self.subTest(raw=raw):self.assertFalse(self.selection(raw)['executable'])

    def test_selection_final_and_truncation(self):
        self.assertEqual(self.selection('Provisional [2].\nFinal answer: [3]')['selected'],['3'])
        self.assertEqual(self.selection('{"keep_card_indices":[2,3,')['selected'],['2','3'])
        self.assertEqual(self.selection('{"keep_card_indices":[2,3')['selected'],['2'])
        self.assertEqual(self.selection('[2,3]\n[3,2]')['selected'],['2','3'])

    def test_zero_not_empty(self):
        self.assertTrue(validate_qa_item(question()))
        for v in [None,'',[]]:
            with self.subTest(v=v),self.assertRaises(ValueError):validate_qa_item(question(solutions=[[v]] if v!=[] else []))
        for value in ['NaN','Infinity','not a number']:
            with self.subTest(value=value),self.assertRaises(ValueError):validate_qa_item(question(solutions=[[value]]))

    def test_qa_tolerates_format(self):
        fixtures=['```json\n{answers:[{id:"q1",answer:"0",},],}\n```',
                  'Q1: 0', '{"q1":"0"}',
                  '[{"id":"q1","answer":0}]',
                  '{"answers":[{"id":"q1","answer":"0"},{"id":"q2","answer":']
        for raw in fixtures:
            with self.subTest(raw=raw):self.assertEqual(score_qa(raw,[question()])['items'][0]['tolerant_credit'],1)

    def test_equivalent_number_formats_are_not_conflicting(self):
        result=score_qa('{"q1":10}\n{"q1":"10.0"}',[question(solutions=[['10']])])
        self.assertEqual(result['items'][0]['tolerant_credit'],1)
        self.assertEqual(result['reception']['ambiguous_ids'],[])

    def test_qa_one_bad_item_does_not_erase_other(self):
        raw='{"answers":[{"id":"q999","answer":43},{"id":"q1","answer":"0"}]}'
        score=score_qa(raw,[question()]);self.assertEqual(score['items'][0]['tolerant_credit'],1)
        self.assertFalse(score['reception']['strict_format']);self.assertEqual(len(score['reception']['discarded']),1)

    def test_id_filter_not_oracle_filter(self):
        q=question(kind='id',solutions=[['2']],id_domain=['1','2','3'])
        self.assertEqual(score_qa('{"q1":[999,"2"]}',[q])['items'][0]['tolerant_credit'],1)
        self.assertEqual(score_qa('{"q1":["3"]}',[q])['items'][0]['tolerant_credit'],0)
        self.assertEqual(score_qa('{"question_1":"service 2"}',[q])['items'][0]['tolerant_credit'],1)
        with self.assertRaises(ValueError):receive_qa('Q1:2',[q])

    def test_required_partial_credit(self):
        q=question('required_values',[['10','20','30']])
        for raw,expected in [('Q1:10',.5),('{"q1":[10,20]}',.5),('{"q1":[10,20,30]}',1),
                             ('{"q1":[10,40]}',.5),('Q1:40',0),('{"q1":[10,20,30,40]}',.5)]:
            with self.subTest(raw=raw):self.assertEqual(score_qa(raw,[q])['items'][0]['tolerant_credit'],expected)

    def test_alternative_not_required(self):
        q=question('alternatives',[['10'],['20']])
        self.assertEqual(score_qa('Q1:20',[q])['items'][0]['tolerant_credit'],1)

    def test_no_cross_product_of_solutions(self):
        q=question('required_values',[['10','20'],['30','40']])
        self.assertEqual(score_qa('{"q1":[10,40]}',[q])['items'][0]['tolerant_credit'],.5)

    def test_conflicting_answers_never_choose_oracle(self):
        q=question(solutions=[['10']]);s=score_qa('{"q1":10}\n{"q1":20}',[q])
        self.assertEqual(s['items'][0]['tolerant_credit'],0);self.assertEqual(s['reception']['ambiguous_ids'],['q1'])

    def test_display_not_raw_precision(self):
        q=question(solutions=[['4.816e5']])
        self.assertEqual(score_qa('Q1:481600',[q])['items'][0]['tolerant_credit'],1)
        self.assertEqual(score_qa('Q1:481589.75',[q])['items'][0]['tolerant_credit'],0)

    def test_availability_loss_not_reading_error(self):
        q=question(available=False);r=score_qa('Q1:0',[q])
        self.assertIsNone(r['conditional_credit']);self.assertEqual(r['end_to_end_credit'],0)

    def test_one_malformed_question_does_not_erase_another(self):
        q1=question();q2=dict(question(solutions=[['20']]),id='q2')
        result=score_qa('{"answers":[{"id":"q1","answer":0},{"id":"q2","answer":]}',[q1,q2])
        self.assertEqual([r['tolerant_credit'] for r in result['items']],[1,0])


class CardAndQueueTests(unittest.TestCase):
    def test_smoke_window_is_not_reset_by_restart(self):
        import tempfile
        from unittest.mock import patch
        from .utils import smoke_deadline
        with tempfile.TemporaryDirectory() as tmp:
            with patch('time.time',return_value=100.),patch('time.monotonic',return_value=10.):
                self.assertEqual(smoke_deadline(tmp,900),910.)
            with patch('time.time',return_value=200.),patch('time.monotonic',return_value=20.):
                self.assertEqual(smoke_deadline(tmp,900),820.)
            with patch('time.time',return_value=1000.):
                with self.assertRaises(TimeoutError):smoke_deadline(tmp,900)

    def test_retained_image_is_independent_of_mutable_cache(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from . import utils
        with tempfile.TemporaryDirectory(dir=utils.ROOT/'build') as tmp,patch.object(utils,'RESULTS',Path(tmp)):
            source=Path(tmp)/'cache/dashboard.png';source.parent.mkdir();source.write_bytes(b'original visible input')
            name,sha=utils.object_file(source);source.write_bytes(b'new cache generation')
            target=utils.ROOT/name
            self.assertEqual(target.read_bytes(),b'original visible input');self.assertEqual(utils.digest(target),sha)

    def test_qa_conversation_resolves_selector_from_its_own_scope(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from . import utils
        with tempfile.TemporaryDirectory(dir=utils.ROOT/'build') as tmp,patch.object(utils,'RESULTS',Path(tmp)):
            utils.save(Path(tmp)/'smoke_multi/completed/selector.json',{'raw':'keep_card_indices: [7]'})
            utils.save(Path(tmp)/'smoke_qa/completed/qa.json',{'item':{'parent_scope':'smoke_multi'},'parent':'selector','raw':'QA answer'})
            html=Path(utils.view_conversation('qa','smoke_qa')).read_text()
            self.assertIn('keep_card_indices',html);self.assertIn('QA answer',html)

    def test_concurrent_render_cache_publication_is_serial(self):
        import tempfile,time,threading
        from pathlib import Path
        from concurrent.futures import ThreadPoolExecutor
        from .utils import cache_lock
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'cache.lock';active=0;peak=0;guard=threading.Lock()
            def publish():
                nonlocal active,peak
                with cache_lock(path):
                    with guard:active+=1;peak=max(peak,active)
                    time.sleep(.015)
                    with guard:active-=1
            with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(lambda _:publish(),range(8)))
            self.assertEqual(peak,1)

    def test_atomic_failure_does_not_publish_completion(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from .utils import save,read
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'completed/call.json';save(path,{'old':True})
            with patch('os.replace',side_effect=OSError('simulated power loss')):
                with self.assertRaises(OSError):save(path,{'new':True})
            self.assertEqual(read(path),{'old':True})
            save(path,{'new':True});self.assertEqual(read(path),{'new':True})

    def test_reference_preserves_actual_answer_and_logical_usage(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from . import utils
        with tempfile.TemporaryDirectory(dir=utils.ROOT/'build') as tmp,patch.object(utils,'RESULTS',Path(tmp)):
            request={'identity':'same','task':'QA','prompt':'Q1: read 0','images':[],'qa_items':[question()]}
            item={'key':'one','task':'QA','id':'fixture'};usage={'input_tokens':7,'output_tokens':3}
            first=utils.commit_call('formal',item,request,'Q1:0',usage,1)
            second=utils.commit_call('formal',dict(item,key='two'),request,first['raw'],first['usage'],None,reference='one')
            self.assertEqual(first['request_path'],second['request_path'])
            self.assertEqual(first['scores'],second['scores']);self.assertEqual(second['usage'],usage)
            self.assertIsNone(second['attempt']);self.assertEqual(second['reference'],'one')

    def test_actual_card_pixels_and_deleted_background(self):
        import tempfile,json
        from pathlib import Path
        from PIL import Image,ImageChops
        from renderer.operations.card_subset import compose
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'source';source.mkdir()
            rectangles=[{'card':'C1','index':9,'x':24,'y':86,'width':100,'height':100},
                        {'card':'C2','index':2,'x':24,'y':202,'width':100,'height':100}]
            (source/'manifest.json').write_text(json.dumps({'width':160,'height':340,'rectangles':rectangles}))
            (source/'foreground_audit.json').write_text(json.dumps({'boxes':{},'palette':{}}))
            for name in ('dashboard.png','anchor_foreground.png','role_foreground.png'):
                img=Image.new('RGB',(160,340),(10,20,30));img.paste((200,90,10),(24,202,124,302));img.save(source/name)
            for mode in ('FIXED','PACK'):
                dest=Path(tmp)/mode;result=compose(source,{'C2'},mode,dest)
                panel=result['panels'][0];x,y,w,h=panel['box']
                with Image.open(dest/'dashboard.png') as out,Image.open(source/'dashboard.png') as original:
                    self.assertIsNone(ImageChops.difference(out.crop((x,y,x+w,y+h)),original.crop((24,202,124,302))).getbbox())
                    if mode=='FIXED':self.assertEqual(out.getpixel((30,90)),(10,20,30))
            padded=compose(source,{'C2'},'PACK',Path(tmp)/'padded',canvas_size=[160,340])
            self.assertEqual([padded['width'],padded['height']],[160,340])
            self.assertEqual(padded['panels'][0]['box'],[24,86,100,100])
            with Image.open(Path(tmp)/'padded/dashboard.png') as out,Image.open(source/'dashboard.png') as original:
                self.assertIsNone(ImageChops.difference(out.crop((24,86,124,186)),original.crop((24,202,124,302))).getbbox())
            with self.assertRaises(ValueError):compose(source,{'C2'},'PACK',Path(tmp)/'bad',canvas_size=[80,170])

    def test_selection_quotas_and_matched(self):
        from .exps import select_cpu,matched_hash
        from collections import Counter
        cards=[{'index':str(i+1),'card':f'C{i}','protected':False,'modality':'MRLG'[i%4],
                'entities':[str(i%3)],'box':[0,0,100,100+i*5]} for i in range(20)]
        inv={'id':'fixture','cards':cards};selection=select_cpu(inv)
        lookup={c['index']:c for c in cards}
        counts=lambda ids:Counter(lookup[i]['modality'] for i in ids)
        self.assertEqual(selection,select_cpu(inv));self.assertEqual(len(selection['balanced']),10)
        self.assertEqual(counts(selection['balanced']),counts(selection['hash']))
        matched=matched_hash(inv,selection['balanced']);self.assertEqual(counts(matched),counts(selection['balanced']))

    def test_fixed_and_compact_geometry(self):
        from renderer.operations.card_subset import placements
        rectangles=[{'card':'C1','index':9,'x':24,'y':86,'width':100,'height':100},
                    {'card':'C2','index':2,'x':24,'y':202,'width':100,'height':100},
                    {'card':'C3','index':11,'x':140,'y':86,'width':100,'height':100}]
        fixed=placements(rectangles,{'C2','C3'},'FIXED');packed=placements(rectangles,{'C2','C3'},'PACK')
        self.assertEqual(fixed[0]['box'],[24,202,100,100]);self.assertEqual(packed[0]['box'],[24,86,100,100])
        self.assertEqual([p['index'] for p in packed],[2,11]);self.assertEqual(packed[0]['source_box'],fixed[0]['source_box'])

    def test_registered_queues(self):
        from .utils import roster,MULTI
        from .exps import build_queue
        rows=roster();queue=build_queue(rows,'formal');self.assertEqual(len(queue),3840)
        self.assertEqual(len({i['key'] for i in queue}),3840)
        self.assertEqual(sum(i['task']=='ACTION' for i in queue),250)
        self.assertTrue(all(i['parent'] for i in queue if i['arm'] in MULTI))
        for scope in ('smoke_single','smoke_multi','smoke_qa'):
            self.assertEqual(len(build_queue(rows,scope)),18)


def run():
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__,fromlist=['*'])))
    if not result.wasSuccessful():raise RuntimeError('Offline regression failed')
    return {'status':'passed','tests':result.testsRun,'new_model_calls':0}
