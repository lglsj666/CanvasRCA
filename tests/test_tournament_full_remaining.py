"""Full-cohort registration, asymmetric retirement, and pending resume; no inference."""
from pathlib import Path
import pytest
from vlmrca.run_state import SuccessCoverageRegister, write_json, sha_file
from RQs.RQ3.src.main import load_config


def test_partial_new_round_rejected_but_partial_model_completion_resumes(tmp_path):
    c={'models':['q','g'],'cases':['a','b','c','d'],'levels':[1,3,5],
       'threshold_cases':['a','b','c','d'],'threshold_count':4}
    reg=SuccessCoverageRegister(tmp_path/'coverage',c,tmp_path,require_full_cohort=True)
    first=reg.register({'id':'first'})
    def finish(r,m,hits):
        result=[]
        for case in r['cohorts'][m]:
            p=tmp_path/f"{r['id']}_{m}_{case}.json"
            write_json(p,{'rank':1 if case in hits else 0})
            result.append({'case':case,'hits':{str(k):case in hits for k in (1,3,5)},
                           'artifacts':{p.name:sha_file(p)}})
        reg.commit(r['id'],m,result)
    finish(first,'q',{'a'});finish(first,'g',{'b','c'})
    with pytest.raises(ValueError,match='ALL unretired'):
        reg.register({'id':'second'},{'q':['b'],'g':['a','d']})
    second=reg.register({'id':'second'})
    assert second['cohorts']=={'q':['b','c','d'],'g':['a','d']}
    assert second['cohort_policy']=='all_unretired_v1'
    finish(second,'q',{'b','c'})
    assert reg.register({'id':'second'})==second
    finish(second,'g',set())
    third=reg.register({'id':'third'})
    assert third['cohorts']=={'q':['d'],'g':['a','d']}


def test_all_new_method_configs_preserve_effective_scientific_settings():
    root=Path(__file__).resolve().parents[1]/'RQs/RQ3/configs'
    pairs={'baro':'baro24','trace_sc':'trace_sc8','log_freq':'log_freq6',
           'ma':'ma24','trace_status':'trace_status'}
    for new,old in pairs.items():
        a=load_config(root/f'tournament_full_{new}_v3.yaml')
        b=load_config(root/f'tournament_{old}_v1.yaml')
        assert a['tournament']['cohort_policy']=='all_unretired_v1'
        assert {k:v for k,v in a.items() if k!='tournament'}=={k:v for k,v in b.items() if k!='tournament'}
