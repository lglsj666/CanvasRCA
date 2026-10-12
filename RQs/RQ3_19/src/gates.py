"""Version-bound qualification, accounting and separate RCA/QA analysis."""
from collections import Counter,defaultdict
import ast
import json
import math
import subprocess
import tarfile
import time
from . import exps
from .utils import (ROOT,ARMS,MODEL,VERSION,METRICS,config,path,register,phase_arms,logical_key,
                    flag,source_contract,read_json,write_json,sha_file,stable_hash,immutable_json,runtime)
from RQs.RQ3_18.src.gates import paired,holm,contrast,scored_metrics


def static(c):
    folder=ROOT/'RQs/RQ3_19';files=list((folder/'src').glob('*.py'));lines=0
    assert {p.name for p in files}=={'__init__.py','main.py','utils.py','exps.py','tests.py','gates.py'}
    for p in files:
        s=p.read_text();tree=ast.parse(s);compile(tree,str(p),'exec')
        lines+=sum(bool(l.strip()) and not l.lstrip().startswith('#') for l in s.splitlines())
        assert not any(isinstance(n,ast.ImportFrom) and (n.module or '').startswith(('matplotlib','PIL.ImageDraw')) for n in ast.walk(tree))
    assert lines<=7500 and len(list((folder/'descriptions').glob('*.md')))==3
    shells=list((folder/'scripts').glob('*.sh'));assert len(shells)<=10 and sum(len(p.read_text().splitlines()) for p in shells)<=800
    for p in shells:subprocess.run(['bash','-n',str(p)],check=True)
    source=(folder/'src/exps.py').read_text()
    assert not any(s in source for s in ('read_json(', 'accepted_labels','open(', 'ground_truth['))
    for name,digest in read_json(path(c['results'])/'qualification/history_protection.json').items():
        assert sha_file(ROOT/name)==digest, 'Protected file changed: '+name
    assert config()==c
    reg=register(c);assert len(reg['qa_cases'])==60 and sum(len(phase_arms(c,False,r)) for r in reg['cases'])==1480
    runtime(c)  # A local YAML projection only; no service or tokenizer is loaded.
    current=source_contract()
    result={'status':'passed','source_contract':current,'source_lines':lines,'positions':1480,'qa_cases':60,
      'checks':['AST/modules/lines/shell','public compiler boundary','four main arms and eight QA paths',
                'explicit credential required','historical source protection','exact roster and smoke caps'],
      'new_model_calls':0}
    write_json(path(c['results'])/'qualification/static.json',result)
    return {k:v for k,v in result.items() if k!='source_contract'}


def build_renderer(c):
    """Reuse the latest qualified unchanged bundle; no redundant build/renderer fork."""
    old=read_json(ROOT/'RQs/RQ3_18/results/population_readout_v1/qualification/renderer_build.json')
    current=source_contract()
    frozen=read_json(ROOT/'RQs/RQ3_18/results/population_readout_v1/qualification/source_freeze.json')['source_contract']
    if old['renderer']!=current['renderer'] or frozen['files']['src/renderer/web/dist/render.mjs']!=current['files']['src/renderer/web/dist/render.mjs']:
        raise RuntimeError('Inherited bundle incompatible: explicitly build and requalify latest renderer')
    report={'status':'built','renderer':current['renderer'],'reused_qualified_bundle':True,
            'bundle_sha256':sha_file(ROOT/'src/renderer/web/dist/render.mjs')}
    write_json(path(c['results'])/'qualification/renderer_build.json',report);return report


def require_renderer_build():
    c=config();report=read_json(path(c['results'])/'qualification/renderer_build.json')
    if report['status']!='built' or report['renderer']!=source_contract()['renderer']:
        raise RuntimeError('Latest unified renderer build required')


def freeze(c):
    root=path(c['results'])/'qualification';current=source_contract()
    for name in ('static','cpu','visual_review'):
        report=read_json(root/(name+'.json'))
        if report.get('status')!='passed' or report.get('source_contract')!=current:raise RuntimeError('Qualification missing: '+name)
    archive=root/'frozen_source.tar.gz'
    if archive.exists():
        previous=read_json(root/'source_freeze.json')
        if previous['source_contract']!=current or previous['archive_sha256']!=sha_file(archive):raise RuntimeError('Frozen version changed')
        return {'status':'already_frozen'}
    with tarfile.open(archive.with_suffix('.tmp'),'w:gz') as tar:
        for name in current['files']:tar.add(ROOT/name,arcname=name)
    archive.with_suffix('.tmp').replace(archive)
    immutable_json(root/'source_freeze.json',{'status':'frozen','source_contract':current,'archive_sha256':sha_file(archive)})
    return {'status':'frozen','files':len(current['files']),'source_hash':stable_hash(current)}


def authorize(c):
    root=path(c['results'])/'qualification';frozen=read_json(root/'source_freeze.json');current=source_contract()
    if current!=frozen['source_contract']:raise RuntimeError('Authorization requires qualified frozen version')
    value={'status':'authorized','authority':'explicit_user_request_2026-10-05','version':VERSION,
      'source_contract_hash':stable_hash(current),'config_hash':stable_hash(c),'registration_hash':stable_hash(register(c)),
      'core_formal_positions':1480,'smoke_limit':18,'core_formal_attempt_limit':1566,'overall_limit':3000,
      'smoke_authorized':True,'formal_after_smoke_pass':True,
      'user_request':'Implement the saved plan; static then CPU then GPU smoke; after passage launch the full experiment and stop after startup.',
      'conditional_modules_not_automatically_activated':True}
    immutable_json(root/'execution_authorization.json',value);return value


def require_qualification(c,smoke=False):
    root=path(c['results'])/'qualification';current=source_contract()
    file=root/'execution_authorization.json'
    if not file.exists():raise RuntimeError('Execution disabled: no version-bound credential')
    auth=read_json(file)
    if auth.get('source_contract_hash')!=stable_hash(current) or auth.get('config_hash')!=stable_hash(c) or auth.get('registration_hash')!=stable_hash(register(c)):
        raise RuntimeError('Credential version mismatch')
    frozen=read_json(root/'source_freeze.json')
    if frozen['source_contract']!=current or sha_file(root/'frozen_source.tar.gz')!=frozen['archive_sha256']:raise RuntimeError('Freeze mismatch')
    for name in ('static','cpu','visual_review')+(() if smoke else ('smoke_review',)):
        report=read_json(root/(name+'.json'))
        if report.get('status')!='passed' or report.get('source_contract')!=current:raise RuntimeError('Required qualification: '+name)
    if not smoke:
        if not read_json(root/'smoke_review.json').get('actual_inputs_outputs_reviewed'):raise RuntimeError('Actual smoke review required')
        if read_json(path(c['results'])/'smoke/artifact_review.json')['source_contract']!=current:raise RuntimeError('Smoke artifact version mismatch')


def require_runtime_attestation(c,root):
    report=read_json(root/'attestation.json');profile,spec=runtime(c)
    if report.get('status')!='ready' or report.get('model')!=MODEL or report.get('rq319_source_contract')!=source_contract():
        raise RuntimeError('Current live attestation required')
    if report.get('recipe')!=spec or report.get('profile_sha256')!=sha_file(profile.source):raise RuntimeError('Effective recipe mismatch')


def records(c,smoke=False):
    reg=register(c);root=path(c['results'])/('smoke' if smoke else 'formal');rows=[]
    for row in reg['smoke' if smoke else 'cases']:
        oid=row['opaque_incident_id']
        for arm in phase_arms(c,smoke,row):
            value=flag(root,oid,arm) or {'status':'pending'}
            rows.append({**value,'case':oid,'arm':arm,'dataset':row['dataset'],'event_group':reg['groups'][oid]})
    return root,rows


def summarize(c,smoke=False):
    _,rows=records(c,smoke);counts=dict(Counter(r['status'] for r in rows))
    return {'status':'incomplete' if counts.get('pending') else 'complete','positions':len(rows),'counts':counts,
      'by_arm':{a:dict(Counter(r['status'] for r in rows if r['arm']==a)) for a in ARMS},
      'reference_positions':sum(bool(r.get('no_op')) for r in rows)}


def review_smoke(c):
    from RQs.RQ3_1.src.main import audit_completion_artifacts,score_response_callback
    from vlmrca.run_state import DurableCallRegister
    root,rows=records(c,True);outcome=read_json(root/'supervisor.json')
    if outcome['status'] not in {'complete','bounded_timeout'}:raise RuntimeError('Smoke supervisor failed')
    assert len(rows)==18
    audits=[];seen=set()
    for row in rows:
        if row['status']=='pending':
            if outcome['status']!='bounded_timeout':raise RuntimeError('Unexplained pending smoke')
            continue
        if row['status']=='fail':
            if row.get('failure_class')!='request_timeout':raise RuntimeError('Smoke infrastructure failure')
            continue
        assert row['status']=='done'
        if row['call_key'] in seen:continue
        seen.add(row['call_key']);audit_completion_artifacts(root,row['call_key'])
        public=read_json(path(c['preparation'])/'public'/(row['case']+'.json'))
        output=read_json(root/'outputs'/(row['call_key']+'.json'))
        if row['arm'] in exps.QA:score=exps.score_qa(public['qa'],output['response'])
        else:score=score_response_callback(read_json(path(c['preparation'])/'private'/(row['case']+'.json')),public['candidates'])(output['response'])
        assert score==output['score']
        metrics=score.get('metrics',score)
        names=('qa_accuracy','reading','binding','comparison') if row['arm'] in exps.QA else METRICS
        assert all(type(metrics.get(k)) in (int,float) and math.isfinite(metrics[k]) for k in names)
        # A top-five miss has valid zero metrics and rank=None in the scorer.
        if 'rank' in metrics:assert metrics['rank'] is None or (type(metrics['rank']) is int and 1<=metrics['rank']<=5)
        audits.append({'case':row['case'],'arm':row['arm'],'call_key':row['call_key'],'model_status':output['status']})
    report={'status':'passed','source_contract':source_contract(),'outcome':outcome,'completed_audits':audits,
      'coverage_complete':all(r['status']=='done' for r in rows),
      'accounting':DurableCallRegister(root/'calls.sqlite',scope=VERSION,limit=c['smoke_attempt_limit']).summary(),
      'unfinished':[{'case':r['case'],'arm':r['arm'],'status':r['status']} for r in rows if r['status']!='done'],
      'qualification_not_rank_gate':True,'timeout_only_policy':'preserve spent calls and explicitly report incomplete coverage'}
    write_json(root/'artifact_review.json',report);return {k:v for k,v in report.items() if k!='source_contract'}


def analyze(c):
    """Separate QA denominators; no automatic winner selection or optional activation."""
    root,rows=records(c)
    if any(r['status']=='pending' for r in rows):raise RuntimeError('Complete registered core required')
    cases={};cost={};absolute=[]
    for row in rows:
        case=cases.setdefault(row['case'],{'case':row['case'],'dataset':row['dataset'],'event_group':row['event_group'],'arms':{}})
        item={'metrics':row.get('metrics'),'status':row['status'],'reference':bool(row.get('no_op'))}
        if row['status']=='done':
            ck=row['call_key'];out=read_json(root/'outputs'/(ck+'.json'));public=read_json(path(c['preparation'])/'public'/(row['case']+'.json'))
            if row['arm'] in exps.QA:assert exps.score_qa(public['qa'],out['response'])==out['score']
            else:item['metrics']=scored_metrics(out['response'],read_json(path(c['preparation'])/'private'/(row['case']+'.json')),public['candidates'],row['metrics'])
            cost[ck]=read_json(root/'cost'/(ck+'.json'));item['cost']=cost[ck];item['model_status']=out['status']
        case['arms'][row['arm']]=item
    cases=list(cases.values())
    for dataset in ('all',*c['case_counts']):
        subset=[r for r in cases if dataset=='all' or r['dataset']==dataset]
        for arm in ARMS:
            items=[r['arms'][arm] for r in subset if arm in r['arms']];known=[x for x in items if x['metrics'] is not None]
            names=('qa_accuracy','reading','binding','comparison') if arm in exps.QA else (*METRICS,'precision@1','precision@3')
            absolute.append({'dataset':dataset,'arm':arm,'registered':len(items),'known':len(known),
              'metrics':{m:sum(x['metrics'][m] for x in known)/len(known) if known else None for m in names},
              'bounds':{m:[sum(x['metrics'][m] for x in known)/len(items),(sum(x['metrics'][m] for x in known)+len(items)-len(known))/len(items)] if items else [None,None] for m in names}})
    families={}
    definitions={'primary_method':[(a,b,'mrr') for a,b,_ in c['primary_contrasts']],
      'secondary_method':[(a,b,'mrr') for a,b in c['secondary_contrasts']], 'qa_mechanism':c['qa_contrasts']}
    for family,defs in definitions.items():
        values=[contrast([r for r in cases if a in r['arms'] and b in r['arms']],{a:1,b:-1},m) for a,b,m in defs]
        for level in ('case','event_group'):holm([v[level] for v in values])
        families[family]=values
    report={'status':'complete_core_analysis','source_contract':source_contract(),'absolute':absolute,'families':families,
      'cases':cases,'unique_costs':cost,'candidate_adoption':'requires full cost, dataset and repeat review; not automatic',
      'conditional_modules':'not activated by this analysis'}
    write_json(root/'analysis/complete_core.json',report)
    return {'status':report['status'],'positions':len(rows),'families':families}
