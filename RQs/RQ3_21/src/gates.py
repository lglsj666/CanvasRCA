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
    folder=ROOT/'RQs/RQ3_21';files=list((folder/'src').glob('*.py'));lines=0
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
    reg=register(c);assert len(reg['qa_cases'])==60 and sum(len(phase_arms(c,False,r)) for r in reg['cases'])==2020
    runtime(c)  # A local YAML projection only; no service or tokenizer is loaded.
    current=source_contract()
    result={'status':'passed','source_contract':current,'source_lines':lines,'positions':2020,'qa_cases':60,
      'checks':['AST/modules/lines/shell','public compiler boundary','six new main arms, historical anchor and eight mechanism paths',
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


def require_qualification(c,smoke=False):
    root=path(c['results'])/'qualification';current=source_contract()
    file=root/'execution_authorization.json'
    if not file.exists():raise RuntimeError('Execution disabled: no version-bound credential')
    auth=read_json(file)
    if not auth.get('smoke_authorized') or (not smoke and not auth.get('formal_authorized')):
        raise RuntimeError('This phase has no explicit user authorization')
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
    if report.get('status')!='ready' or report.get('model')!=MODEL or report.get('rq321_source_contract')!=source_contract():
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


def install_historical_references(c,root,rows):
    """Small qualified reference index, never a historical model replay."""
    missing=[r for r in rows if flag(root,r['opaque_incident_id'],exps.A) is None]
    if not missing:return
    audit=read_json(path(c['results'])/'qualification/historical_anchor_audit.json')
    if audit['status']!='passed' or audit['source_contract']!=source_contract():
        raise RuntimeError('Current historical anchor qualification required')
    for row in missing:
        oid=row['opaque_incident_id'];ref=audit['references'][oid]
        assert ref['case']==oid and ref['arm']==exps.A and ref['historical_reference'] and ref['new_calls']==0
        key=logical_key(oid,exps.A)
        write_json(root/'flags'/(key+'.json'),ref)
        write_json(root/'historical_commits'/(key+'.json'),{'status':'complete','reference_hash':stable_hash(ref)})


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
        assert all(metrics.get(k) is None or (type(metrics[k]) in (int,float) and math.isfinite(metrics[k])) for k in names)
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
    """All registered families, full denominators, and explicit cross-round history."""
    root,rows=records(c)
    if any(r['status']=='pending' for r in rows):raise RuntimeError('Complete registered matrix required')
    cases={};cost={};absolute=[]
    for row in rows:
        case=cases.setdefault(row['case'],{'case':row['case'],'dataset':row['dataset'],'event_group':row['event_group'],'arms':{}})
        item={'metrics':None,'status':row['status'],'reference':bool(row.get('no_op')),
              'historical_reference':bool(row.get('historical_reference')),'services':None,'top1':None,'cost':None}
        if row['status']=='done':
            origin=path(row['source_root']) if item['historical_reference'] else root
            ck=row['call_key'];out=read_json(origin/'outputs'/(ck+'.json'));public=read_json(path(c['preparation'])/'public'/(row['case']+'.json'))
            if row['arm'] in exps.QA:
                score=exps.score_qa(public['qa'],out['response']);assert score==out['score'];item['metrics']=score['metrics']
                item['applicable_questions']=score['applicable_questions']
            else:
                item['metrics']=scored_metrics(out['response'],read_json(path(c['preparation'])/'private'/(row['case']+'.json')),public['candidates'],row['metrics'])
                if out['status']=='complete':
                    item['services']=json.loads(out['response'])['services'];item['top1']=item['services'][0]
                else:item['top1']='__invalid_output__'
            usage=read_json(origin/'cost'/(ck+'.json'));assert usage['total_tokens']==usage['input_tokens']+usage['output_tokens']
            cost[str(origin.relative_to(ROOT))+'/'+ck]={'usage':usage,'historical_reference':item['historical_reference']}
            item['cost']=usage;item['model_status']=out['status']
        elif row.get('failure_class')!='request_timeout':raise RuntimeError('Unresolved infrastructure/semantic outcome')
        case['arms'][row['arm']]=item
    cases=list(cases.values())
    mean=lambda values:sum(values)/len(values) if values else None
    for dataset in ('all',*c['case_counts']):
        subset=[r for r in cases if dataset=='all' or r['dataset']==dataset]
        for arm in ARMS:
            items=[r['arms'][arm] for r in subset if arm in r['arms']]
            names=('qa_accuracy','reading','binding','comparison') if arm in exps.QA else (*METRICS,'precision@1','precision@3')
            metrics={};bounds={};denominators={}
            for m in names:
                # A missing QA family is not a wrong answer or an infrastructure failure.
                applicable=[x for x in items if x['metrics'] is None or x['metrics'].get(m) is not None]
                values=[x['metrics'][m] for x in applicable if x['metrics'] is not None]
                n=len(applicable);metrics[m]=mean(values);denominators[m]=len(values)
                bounds[m]=[sum(values)/n,(sum(values)+n-len(values))/n] if n else [None,None]
            absolute.append({'dataset':dataset,'arm':arm,'registered':len(items),'known':sum(x['metrics'] is not None for x in items),
              'metric_known':denominators,'metrics':metrics,'bounds':bounds,
              'model_invalid':sum(x.get('model_status')=='model_failure' for x in items),
              'cost':{m:mean([x['cost'][m] for x in items if x['cost'] is not None]) for m in ('text_tokens','image_tokens','input_tokens','output_tokens','total_tokens','wall_time_s','postprocessing_wall_s')},
              'cost_semantics':'logical deployment, including referenced inputs; historical anchor usage is from RQ3.16'})
    families={}
    definitions={'primary_method':[(a,b,'mrr') for a,b,_ in c['primary_contrasts']],
                 'visual_representation':[(a,b,'mrr') for a,b in c['visual_contrasts']],
                 'conditional_ablation':[(a,b,'mrr') for a,b in c['secondary_contrasts']]}
    for family,defs in definitions.items():
        values=[contrast([r for r in cases if a in r['arms'] and b in r['arms']],{a:1,b:-1},m) for a,b,m in defs]
        for value,(a,b,m) in zip(values,defs,strict=True):value['historical_cross_round']=exps.A in (a,b)
        for level in ('case','event_group'):holm([v[level] for v in values])
        families[family]=values
    mechanism=[]
    for a,b,m in c['qa_contrasts']:
        applicable=[r for r in cases if a in r['arms'] and b in r['arms'] and all(r['arms'][x]['metrics'] is None or r['arms'][x]['metrics'].get(m) is not None for x in (a,b))]
        mechanism.append(contrast(applicable,{a:1,b:-1},m))
    flips=[]
    for rotated,repeated,base in c['rotation_contrasts']:
        transformed=[]
        for case in cases:
            if rotated not in case['arms']:continue
            clone={**case,'arms':{}}
            for arm in (rotated,repeated):
                left,right=case['arms'][arm]['top1'],case['arms'][base]['top1']
                delta=None if left is None or right is None else float(left!=right)
                clone['arms'][arm]={'metrics':{'top1_changed':delta} if delta is not None else None}
                flips.append({'case':case['case'],'arm':arm,'base':base,'top1_changed':delta,
                              'invalid_output_in_pair':'__invalid_output__' in (left,right)})
            transformed.append(clone)
        mechanism.append(contrast(transformed,{rotated:1,repeated:-1},'top1_changed'))
    for level in ('case','event_group'):holm([v[level] for v in mechanism])
    families['mechanism']=mechanism
    descriptors={}
    for a,b in ((exps.RV,exps.A),(exps.TR,exps.CT),(exps.VR,exps.CV),(exps.VR,exps.A),(exps.VR,exps.RT)):
        descriptors[a+' - '+b]=contrast([r for r in cases if a in r['arms'] and b in r['arms']],{a:1,b:-1})
    repair=[]
    for a,b in ((exps.CV,exps.A),(exps.CV,exps.RT),(exps.CV,exps.CT)):
        for case in cases:
            x,y=case['arms'][a],case['arms'][b]
            repair.append({'case':case['case'],'dataset':case['dataset'],'new':a,'old':b,'delta':None if x['metrics'] is None or y['metrics'] is None else round(x['metrics']['mrr']-y['metrics']['mrr'],12),
              'repair':None if x['metrics'] is None or y['metrics'] is None else x['metrics']['ac@1']>y['metrics']['ac@1'],
              'break':None if x['metrics'] is None or y['metrics'] is None else x['metrics']['ac@1']<y['metrics']['ac@1']})
    budgets={}
    for ds in c['case_counts']:
        budgets[ds]={}
        for baseline in (exps.A,exps.RT):
            subset=[r for r in cases if r['dataset']==ds];known=[r for r in subset if r['arms'][baseline]['cost'] and r['arms'][exps.CV]['cost']]
            ratio=sum(r['arms'][exps.CV]['cost']['total_tokens'] for r in known)/sum(r['arms'][baseline]['cost']['total_tokens'] for r in known) if known else None
            budgets[ds][baseline]={'paired_cases':len(known),'registered':len(subset),'actual_total_token_ratio':ratio,
                'passes_full_denominator':len(known)==len(subset) and ratio is not None and ratio<=c['success']['total_token_ratio_max']}
    macro=[]
    for arm in ARMS:
        by=[r for r in absolute if r['arm']==arm and r['dataset'] in c['case_counts']]
        macro.append({'arm':arm,'metrics':{m:mean([r['metrics'][m] for r in by if r['metrics'][m] is not None]) for m in by[0]['metrics']}})
    report={'status':'complete_matrix_analysis','source_contract':source_contract(),'absolute':absolute,'macro':macro,'families':families,
      'descriptive_unadjusted':descriptors,'rotation_vs_repeat':flips,'repair_break':repair,'cases':cases,'unique_costs':cost,'budget_checks':budgets,
      'actual_new_known_tokens':sum(x['usage']['total_tokens'] for x in cost.values() if not x['historical_reference']),
      'historical_anchor_note':'Cross-round reference; common inputs and recipe audited, no claim of a contemporary control.',
      'candidate_adoption':'Review registered engineering thresholds, missingness, cost and repeat direction; no automatic selection.',
      'qa_scope':'Reading source text with/without the unchanged image, not isolated image reading or proof of a causal QA mechanism.'}
    write_json(root/'analysis/complete_core.json',report)
    return {'status':report['status'],'positions':len(rows),'families':families}
