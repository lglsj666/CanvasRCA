"""Independent numerical, geometry, runtime and accounting regressions."""
import unittest
import tempfile
from pathlib import Path
from .utils import read,save,stable,multimodal_gather,RuntimeSession,score_response,score_qa
from .exps import detail_budget,select_atlas
from renderer.operations.source_views import validate_spec


class TestSourceViews(unittest.TestCase):
    def test_concurrent_atomic_writers(self):
        from concurrent.futures import ThreadPoolExecutor
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'shared.json'
            def writer(i):
                save(path,{'writer':i,'values':list(range(100))})
                self.assertEqual(read(path)['values'],list(range(100)))
            with ThreadPoolExecutor(max_workers=8) as pool:
                list(pool.map(writer,range(100)))
            self.assertEqual(list(Path(folder).glob('*.tmp')),[])

    def test_retention_keeps_exact_images_and_analysis_sources(self):
        from .utils import retention_source_dependencies
        paths=retention_source_dependencies('/example')
        self.assertIn(Path('/example/render/dashboard.png'),paths)
        for name in ('evidence.json','provenance.json','mapping.json','text_conditions.json','processor_cpu.json'):
            self.assertIn(Path('/example')/name,paths)
        self.assertNotIn(Path('/example/render/dashboard.html'),paths)

    def test_retention_verifies_before_removing_intermediates(self):
        from unittest.mock import patch
        from . import utils
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);rq=root/'RQ';results=rq/'results'
            pixel=results/'inputs/image.png';pixel.parent.mkdir(parents=True);pixel.write_bytes(b'exact model bytes')
            html=pixel.with_name('dashboard.html');html.write_text('compiler-only')
            req={'identity':'id','images':['RQ/results/inputs/image.png'],'image_sha256':[utils.digest(pixel)]}
            save(results/'frozen/formal_queue.json',[{'item':{'key':'one'},'request':req}])
            save(results/'frozen/smoke_queue.json',[])
            save(results/'formal/requests/one.json',req)
            save(results/'formal/completed/one.json',{'actual_calls':1,'request_path':'requests/one.json','request_hash':'id','response':'original invalid answer'})
            with patch.object(utils,'ROOT',root),patch.object(utils,'RQ',rq),patch.object(utils,'RESULTS',results),patch.object(utils,'roster',return_value=[]):
                pixel.write_bytes(b'corrupt')
                with self.assertRaises(ValueError):utils.finalize_retention()
                self.assertTrue(html.exists())
                pixel.write_bytes(b'exact model bytes')
                report=utils.finalize_retention();self.assertEqual(report['status'],'passed')
                self.assertFalse(html.exists());self.assertEqual(pixel.read_bytes(),b'exact model bytes')
                self.assertEqual(read(results/'formal/completed/one.json')['response'],'original invalid answer')
                actual=sum(p.stat().st_size for p in results.rglob('*') if p.is_file())
                self.assertEqual(report['retained_bytes'],actual)

    def test_finalization_resume_does_not_load_model(self):
        from unittest.mock import patch
        from . import main,utils,gates
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            with patch.object(main,'RESULTS',root),patch.object(utils,'RESULTS',root),\
                 patch.object(gates,'analyze_completed') as analyze,\
                 patch.object(utils,'finalize_retention') as retain:
                with self.assertRaises(RuntimeError):main.finish_formal()
                save(root/'formal/phase_complete.json',{'status':'complete'})
                retain.side_effect=RuntimeError('power loss during finalization')
                with self.assertRaises(RuntimeError):main.finish_formal()
                retain.side_effect=None;retain.return_value={'status':'passed'}
                self.assertEqual(main.finish_formal()['status'],'passed')
                self.assertEqual(analyze.call_count,2)
                save(root/'retention.json',{'status':'passed'})
                self.assertEqual(main.finish_formal()['status'],'already_finalized')
                self.assertEqual(retain.call_count,2)

    def test_budget_boundaries(self):
        self.assertEqual(detail_budget(10000,5000,492),2508)
        self.assertEqual(detail_budget(30000,6000,492),8192)
        self.assertLess(detail_budget(1000,5000,492),0)

    def test_complete_units_and_determinism(self):
        cards=[dict(card=str(i),entity=str(i),modality='MRLG'[i%4],eligible=True,width=500.,height=400.,scale=1.,
            source_width=500.,source_height=400.,restored_chars=100+i,area_tokens=208,source_id=str(i)) for i in range(20)]
        for mode in ('SOURCE_ZOOM','HASH_ZOOM'):
            spec,skipped=select_atlas(cards,2048,mode);validate_spec(spec)
            self.assertEqual((spec,skipped),select_atlas(list(reversed(cards)),2048,mode))
            self.assertEqual(set(p['card'] for p in spec['placements'])|set(skipped),set(str(i) for i in range(20)))

    def test_no_cropping_or_anisotropic_scaling(self):
        s={'width':2048,'height':1024,'placements':[dict(card='x',x=16,y=16,width=600,height=400,scale=2,source_width=300,source_height=200)]}
        validate_spec(s);s['placements'][0]['width']=599
        with self.assertRaises(ValueError):validate_spec(s)

    def test_two_image_gather_keeps_boundary_and_text(self):
        import torch
        ids=torch.tensor([1,9,9,9,2,3,9,9,4]);pos=torch.arange(9).repeat(3,1)
        keep,coords,delta,images=multimodal_gather(ids,pos,9,[3,2],[[0,2],[0,1]])
        self.assertEqual(keep,[0,1,3,4,5,6,7,8]);self.assertEqual(images,[1,2,3,6,7])
        self.assertEqual(coords.tolist(),pos[:,keep].tolist());self.assertEqual(delta,1)

    def test_bad_per_image_indices_rejected(self):
        import torch
        ids=torch.tensor([9,9,0,9]);pos=torch.arange(4).repeat(3,1)
        for groups in ([[0,0],[0]],[[2],[0]],[[0],[1]]):
            with self.assertRaises(ValueError):multimodal_gather(ids,pos,9,[2,1],groups)

    def test_standard_and_tolerant_differ_only_registered_reading(self):
        context={'candidates':['123','234','345','456','567'],'numeric_to_natural':{s:s for s in ['123','234','345','456','567']},'accepted':['234']}
        answer='{"services":["999","service 234","345","456","567"],"reason":"r","confidence":"low"}'
        score=score_response(answer,context)
        self.assertEqual(score['standard']['metrics']['mrr'],0)
        self.assertEqual(score['tolerant']['mrr'],.5)

    def test_qa_exact_vs_numeric_equivalence(self):
        expected=dict(reference='0.10',current='0.2',entity='123',unit='source_unit',comparison='current_greater')
        reply='{"reference":"1e-1","current":"0.2","entity":"service 123","unit":"source unit","comparison":"current_greater"}'
        r=score_qa(reply,expected)
        self.assertEqual(r['tolerant'],1);self.assertLess(r['standard'],1)

    def test_empty_and_malformed_qa(self):
        for reply in ('garbage','[]','{}'):
            r=score_qa(reply,dict(reference='0',current='0',entity='123',unit='ms',comparison='equal'))
            self.assertFalse(r['schema_valid']);self.assertEqual(r['standard'],0)

    def test_atomic_power_loss_resume_and_repeat(self):
        class OfflineProvider:
            calls=0
            last_usage={'input_tokens':10,'output_tokens':4}
            def __call__(self,request):
                self.calls+=1
                return '{"reference":"0","current":"1","entity":"123","unit":"ms","comparison":"current_greater"}'
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);provider=OfflineProvider();expected=dict(reference='0',current='1',entity='123',unit='ms',comparison='current_greater')
            session=RuntimeSession(root/'run',provider,ledger_folder=root)
            request={'identity':stable('fixture'),'task':'QA'};item={'key':'one','variant':'BASE'}
            def crash(stage):
                if stage=='after_response':raise RuntimeError('power loss')
            with self.assertRaises(RuntimeError):session.run(item,request,lambda:expected,crash)
            session.close();session=RuntimeSession(root/'run',provider,ledger_folder=root)
            recovered=session.recover();self.assertEqual(len(recovered['recovered_without_generation']),1)
            first=session.run(item,request,lambda:expected);self.assertEqual(provider.calls,1)
            self.assertEqual(first,session.run(item,request,lambda:expected));self.assertEqual(provider.calls,1)
            referenced=session.run({'key':'ref','variant':'BASE','reference':'one'},request,lambda:expected)
            self.assertEqual(referenced['item']['key'],'ref');self.assertEqual(referenced['actual_calls'],0)
            self.assertEqual(provider.calls,1)
            with self.assertRaises(ValueError):session.run({'key':'bad','variant':'REPEAT','reference':'one'},request,lambda:expected)
            session.run({'key':'repeat','variant':'REPEAT'},request,lambda:expected);self.assertEqual(provider.calls,2)
            save(root/'run/PAUSE',{'pause':True})
            self.assertEqual(session.run({'key':'paused','variant':'BASE'},request,lambda:expected)['status'],'paused')
            session.close()

    def test_exclusive_owner(self):
        with tempfile.TemporaryDirectory() as folder:
            session=RuntimeSession(Path(folder)/'run',ledger_folder=folder)
            with self.assertRaises(BlockingIOError):RuntimeSession(Path(folder)/'run',ledger_folder=folder)
            session.close()

    def test_attention_ceiling(self):
        from vlmrca.vlm.passive_summary import AttentionStore
        self.assertLessEqual(AttentionStore.storage_ceiling(10000),1000000000)

    def test_logical_smoke_limit_does_not_reset(self):
        from vlmrca.run_state import DurableCallRegister
        with tempfile.TemporaryDirectory() as folder:
            ledger=DurableCallRegister(Path(folder)/'calls.sqlite',900,scope='smoke',scope_limit=18)
            for i in range(18):ledger.begin(str(i),stable(i),'QA')
            ledger=DurableCallRegister(Path(folder)/'calls.sqlite',900,scope='smoke',scope_limit=18)
            with self.assertRaises(RuntimeError):ledger.begin('next',stable(19),'QA')


def run_tests():
    import io
    from .utils import RESULTS
    stream=io.StringIO();suite=unittest.defaultTestLoader.loadTestsFromTestCase(TestSourceViews)
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    report={'status':'passed' if result.wasSuccessful() else 'failed','tests':result.testsRun,'output':stream.getvalue(),'new_model_calls':0}
    save(RESULTS/'qualification/unit.json',report);print(stream.getvalue())
    return report
