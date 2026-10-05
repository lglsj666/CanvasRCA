"""Qualification and prospective analysis; inference authorization remains closed."""
from collections import Counter, defaultdict
from pathlib import Path
import ast
import json
import math
import subprocess
import time
from . import exps
from .utils import ROOT,ARMS,MODEL,VERSION,METRICS,config,path,register,phase_arms,logical_key,flag,source_contract,read_json,write_json,sha_file,stable_hash,immutable_json


def static(c):
    started=time.monotonic();folder=ROOT/'RQs/RQ3_18';files=list((folder/'src').glob('*.py'))
    assert {p.name for p in files}=={'__init__.py','main.py','utils.py','exps.py','tests.py','gates.py'}
    lines=0
    for p in files:
        value=p.read_text();tree=ast.parse(value);compile(tree,str(p),'exec')
        lines+=sum(bool(l.strip()) and not l.lstrip().startswith('#') for l in value.splitlines())
        for n in ast.walk(tree):
            if isinstance(n,ast.ImportFrom) and (n.module or '').startswith(('matplotlib','PIL.ImageDraw')):
                raise ValueError('Experiment-local drawing forbidden')
    assert lines<=7500 and len(list((folder/'descriptions').glob('*.md')))==3
    shell=list((folder/'scripts').glob('*.sh'));assert len(shell)<=10
    assert sum(len(p.read_text().splitlines()) for p in shell)<=800
    for p in shell:subprocess.run(['bash','-n',str(p)],check=True)
    source=(folder/'src/exps.py').read_text()
    assert not any(token in source for token in ('read_json(', 'accepted_labels', 'score_response_callback', 'open('))
    protected=read_json(path(c['results'])/'qualification/history_protection.json')
    for name,digest in protected.items():
        if sha_file(ROOT/name)!=digest:raise ValueError('Historical source/report changed: '+name)
    assert not (ROOT/'docs/experiment_plans/RQ3_18_Marginal_Attribution_Plan_2026-10-04.md').exists()
    assert not (folder/'results/marginal_attribution_v1').exists()
    assert not (ROOT/'src/renderer/operations/neutral_canvas.py').exists()
    assert c==config() and len(register(c)['cases'])==220
    result={'status':'passed','source_contract':source_contract(),'source_lines':lines,'protected_files':len(protected),
            'seconds':time.monotonic()-started,'checks':['AST/module/line/shell','11 arms and four primary contrasts',
            'public compiler IO boundary','historical source/recipe/report hashes','old RQ3.18 removed','GPU and formal closed']}
    write_json(path(c['results'])/'qualification/static.json',result)
    return {k:v for k,v in result.items() if k!='source_contract'}


def qualified_contract(c,current):
    """Accept an authorization-only successor; preserve the measured CPU freeze."""
    import tarfile
    root=path(c['results'])/'qualification'
    frozen=read_json(root/'source_freeze.json');original=frozen['source_contract']
    receipt=read_json(root/'activation_v1/source_compatibility.json')
    gate='RQs/RQ3_18/src/gates.py'
    if (frozen.get('status')!='frozen' or receipt.get('status')!='passed'
            or receipt.get('qualified_source_contract')!=original or receipt.get('effective_source_contract')!=current
            or set(original['files'])!=set(current['files']) or original['renderer']!=current['renderer']
            or {f for f in current['files'] if current['files'][f]!=original['files'][f]}!={gate}
            or sha_file(root/'frozen_source.tar.gz')!=frozen['archive_sha256']
            or sha_file(root/'activation_v1/frozen_source.tar.gz')!=receipt['effective_archive_sha256']):
        raise RuntimeError('Activation changed a qualified scientific dependency or archive')
    with tarfile.open(root/'frozen_source.tar.gz','r:gz') as archive:
        before=ast.parse(archive.extractfile(gate).read().decode())
    after=ast.parse((ROOT/gate).read_text())
    permitted={'qualified_contract','execution_authorized','require_qualification','full_authorized'}
    def remainder(tree):
        tree.body=[n for n in tree.body if not isinstance(n,ast.FunctionDef) or n.name not in permitted]
        return ast.dump(tree,include_attributes=False)
    if remainder(before)!=remainder(after):
        raise RuntimeError('Non-authorization code differs from measured freeze')
    return original


def execution_authorized(c,current,smoke):
    file=path(c['results'])/'qualification/activation_v1/execution_authorization.json'
    if not file.exists():raise RuntimeError('Model execution disabled: no explicit user authorization')
    receipt=read_json(file)
    expected={'status':'authorized','authority':'explicit_user_request','version':VERSION,'model':MODEL,
        'config_hash':stable_hash(c),'effective_source_contract_hash':stable_hash(current),
        'registration_hash':stable_hash(register(c)),'registered_positions':c['formal_positions'],
        'smoke_attempt_limit':c['smoke_attempt_limit'],'formal_attempt_limit':c['formal_attempt_limit'],
        'total_attempt_limit':c['total_attempt_limit'],'smoke_authorized':True,'formal_after_smoke_pass':True}
    if any(receipt.get(k)!=v for k,v in expected.items()) or not receipt.get('user_request'):
        raise RuntimeError('Execution authorization does not bind this frozen experiment')


def require_qualification(c,smoke=False):
    current=source_contract();execution_authorized(c,current,smoke)
    qualified=qualified_contract(c,current);root=path(c['results'])/'qualification'
    for name in ('static','cpu','visual_review'):
        report=read_json(root/(name+'.json'))
        if report.get('status')!='passed' or report.get('source_contract')!=qualified:
            raise RuntimeError('Missing measured qualification: '+name)
    report=read_json(root/'activation_v1/static.json')
    if report.get('status')!='passed' or report.get('source_contract')!=current:
        raise RuntimeError('Current activation static check required')
    if not smoke:
        for file in (root/'smoke_review.json',path(c['results'])/'smoke/artifact_review.json'):
            review=read_json(file)
            if review.get('status')!='passed' or review.get('source_contract')!=current:
                raise RuntimeError('Current GPU smoke qualification required')
        if not read_json(root/'smoke_review.json').get('actual_inputs_outputs_reviewed'):
            raise RuntimeError('Actual GPU smoke artifact inspection required')


def full_authorized(c,current=None):
    require_qualification(c,False)


def freeze(c):
    import tarfile
    root=path(c['results'])/'qualification';current=source_contract()
    for name in ('static','cpu','visual_review'):
        report=read_json(root/(name+'.json'))
        if report.get('status')!='passed' or report.get('source_contract')!=current:
            raise RuntimeError('Current qualification required: '+name)
    archive=root/'frozen_source.tar.gz'
    if archive.exists():
        old=read_json(root/'source_freeze.json')
        if old['source_contract']!=current or old['archive_sha256']!=sha_file(archive):raise ValueError('Frozen archive changed')
        return {'status':'already_frozen'}
    temporary=archive.with_suffix('.tmp')
    with tarfile.open(temporary,'w:gz') as tar:
        for name in current['files']:tar.add(ROOT/name,arcname=name)
    temporary.replace(archive)
    value={'status':'frozen','source_contract':current,'archive_sha256':sha_file(archive),
           'gpu_smoke':'not_run','formal':'not_started','user_boundary':'static_cpu_then_stop'}
    immutable_json(root/'source_freeze.json',value)
    return {'status':'frozen','files':len(current['files']),'source_hash':stable_hash(current)}


def statistical_families(c,cases):
    families={}
    for name,definitions in (
        ('primary_mrr',[{a:1,b:-1} for a,b,_ in c['primary_contrasts']]),
        ('secondary_mrr',[{a:1,b:-1} for a,b in c['secondary_contrasts']]+c['secondary_interactions'])):
        rows=[contrast(cases,d) for d in definitions]
        for level in ('case','event_group'):holm([r[level] for r in rows])
        families[name]=rows
    return families


def scored_metrics(response,private,candidates,stored):
    """Keep canonical metrics untouched; add explicit precision for offline reporting."""
    from RQs.RQ3_1.src.main import score_response_callback
    from vlmrca.eval.scoring import is_granularity_aware_hit
    score=score_response_callback(private,candidates)(response)
    metrics=score.get('metrics',score)
    if any(metrics[m]!=stored[m] for m in METRICS):raise ValueError('Stored score disagrees with canonical replay')
    result={m:metrics[m] for m in METRICS}
    if score.get('status')=='model_failure':
        result.update({'precision@1':0.,'precision@3':0.});return result
    answer=json.loads(response);ids=answer['services']
    accepted=private.get('accepted_labels') or private['accepted']
    matches=[any(is_granularity_aware_hit(private['numeric_to_natural'][str(i)],label) for label in accepted) for i in ids]
    result.update({f'precision@{k}':sum(matches[:k])/k for k in (1,3)})
    return result


def analyze(c):
    """Offline complete-matrix report; unknown infrastructure scores remain unknown."""
    root,rows=records(c)
    if any(r['status']=='pending' for r in rows):raise RuntimeError('Full registered matrix is required')
    cases={};costs={};metrics_names=(*METRICS,'precision@1','precision@3')
    for row in rows:
        oid,arm=row['case'],row['arm']
        case=cases.setdefault(oid,{'case':oid,'dataset':row['dataset'],'event_group':row['event_group'],'arms':{}})
        item={'status':row['status'],'metrics':None,'usage':None,'reference':bool(row.get('no_op')),'services':None}
        if row['status']=='done':
            if flag(root,oid,arm) is None:raise ValueError('Missing atomic commit')
            output=read_json(root/'outputs'/(row['call_key']+'.json'))
            private=read_json(path(c['preparation'])/'private'/(oid+'.json'))
            public=read_json(path(c['preparation'])/'public'/(oid+'.json'))
            item['metrics']=scored_metrics(output['response'],private,public['candidates'],row['metrics'])
            item['model_status']=output['status']
            try:item['services']=json.loads(output['response'])['services']
            except (ValueError,KeyError,TypeError):pass
            cost=read_json(root/'cost'/(row['call_key']+'.json'));costs[row['call_key']]=cost
            if all(type(cost.get(k)) in (int,float) and math.isfinite(cost[k]) and cost[k]>=0 for k in ('input_tokens','output_tokens','total_tokens')):
                if cost['input_tokens']+cost['output_tokens']!=cost['total_tokens']:raise ValueError('Token accounting mismatch')
                item['usage']={k:cost[k] for k in ('input_tokens','output_tokens','total_tokens')}
        elif row.get('failure_class')!='request_timeout':raise ValueError('Unresolved infrastructure/semantic error')
        case['arms'][arm]=item
    cases=list(cases.values());absolute=[]
    for dataset in ('all',*c['case_counts']):
        subset=[r for r in cases if dataset=='all' or r['dataset']==dataset]
        for arm in ARMS:
            items=[r['arms'][arm] for r in subset];known=[v for v in items if v['metrics'] is not None]
            absolute.append({'dataset':dataset,'arm':arm,'registered':len(items),'known':len(known),
                'metrics':{m:sum(v['metrics'][m] for v in known)/len(known) if known else None for m in metrics_names},
                'full_denominator_bounds':{m:([sum(v['metrics'][m] for v in known)/len(items),
                    (sum(v['metrics'][m] for v in known)+len(items)-len(known))/len(items)] if items else [None,None]) for m in metrics_names},
                'model_invalid':sum(v.get('model_status')=='model_failure' for v in items),
                'usage_known':sum(v['usage'] is not None for v in items)})
    macro={a:{m:None if any(r['metrics'][m] is None for r in absolute if r['dataset']!='all' and r['arm']==a)
        else sum(r['metrics'][m] for r in absolute if r['dataset']!='all' and r['arm']==a)/3 for m in metrics_names} for a in ARMS}
    costs_paired=[];transitions=[];repeat=[]
    for dataset in c['case_counts']:
        subset=[r for r in cases if r['dataset']==dataset]
        for control in (exps.T,exps.F):
            common=[r for r in subset if all(r['arms'][a]['usage'] is not None for a in (exps.FP,control))]
            den=sum(r['arms'][control]['usage']['total_tokens'] for r in common)
            costs_paired.append({'dataset':dataset,'control':control,'n':len(common),'registered':len(subset),
                'ratio':sum(r['arms'][exps.FP]['usage']['total_tokens'] for r in common)/den if den else None,
                'full_coverage':len(common)==len(subset)})
        for a,b,_ in c['primary_contrasts']:
            common=[r for r in subset if all(r['arms'][v]['metrics'] is not None for v in (a,b))]
            for metric in ('ac@1','ac@5'):
                delta=[r['arms'][a]['metrics'][metric]-r['arms'][b]['metrics'][metric] for r in common]
                transitions.append({'dataset':dataset,'a':a,'b':b,'metric':metric,'n':len(delta),
                    'repair':sum(v>0 for v in delta),'break':sum(v<0 for v in delta),'delta':sum(delta)/len(delta) if delta else None})
    for a,b in ((exps.TR,exps.T),(exps.FR,exps.F),(exps.R,exps.FP)):
        common=[r for r in cases if all(r['arms'][v]['metrics'] is not None for v in (a,b))]
        repeat.append({'repeat':a,'original':b,'n':len(common),
            'same_mrr':sum(r['arms'][a]['metrics']['mrr']==r['arms'][b]['metrics']['mrr'] for r in common),
            'same_ranking':sum(r['arms'][a]['services']==r['arms'][b]['services'] for r in common),
            'independent_calls_same_recipe_not_new_seeds':True})
    report={'status':'complete_statistics_pending_reason_and_adoption_review','source_contract':source_contract(),
        'cases':cases,'absolute':absolute,'macro':macro,'families':statistical_families(c,cases),'paired_total_cost':costs_paired,
        'repair_break':transitions,'repeat':repeat,'unique_billed_outputs':len(costs),'CI_reported':False,'unknown_usage_not_zero':True}
    write_json(root/'analysis/statistics.json',report)
    return {'status':report['status'],'cases':len(cases),'path':str(root/'analysis/statistics.json')}


def build_renderer(c):
    from renderer.main import node_runtime
    from .utils import runtime
    import os
    env={**os.environ,"PATH":str(node_runtime().parent)+os.pathsep+os.environ["PATH"]}
    for command in (["npm","run","typecheck"],["npm","run","build"]):
        subprocess.run(command,cwd=ROOT/"src/renderer/web",env=env,check=True)
    runtime(c)
    report={"status":"built","renderer":source_contract()["renderer"]}
    write_json(path(c["results"])/"qualification/renderer_build.json",report)
    return report

def require_renderer_build():
    from .utils import config
    c=config(); report=read_json(path(c["results"])/"qualification/renderer_build.json")
    if report.get("status")!="built" or report["renderer"]!=source_contract()["renderer"]:
        raise ValueError("Unified renderer source/build differs")

def require_runtime_attestation(c,root):
    report=read_json(root/"attestation.json")
    if report.get("status")!="ready" or report.get("model")!=MODEL or report.get("rq318_source_contract")!=source_contract():
        raise RuntimeError("Current runtime has no matching source/model attestation")
    from .utils import runtime,sha_file
    profile,spec=runtime(c)
    if report.get("recipe")!=spec or report.get("profile_sha256")!=sha_file(profile.source):
        raise RuntimeError("Attested effective recipe/profile differs from registered runtime")

def records(c,smoke=False):
    reg=register(c)
    root=path(c["results"])/("smoke" if smoke else "formal")
    rows=[]
    for r in reg["smoke" if smoke else "cases"]:
        oid=r["opaque_incident_id"]
        for arm in phase_arms(c,smoke,r):
            file=root/"flags"/(logical_key(oid,arm)+".json")
            value=read_json(file) if file.exists() else {"status":"pending"}
            rows.append({**value,"case":oid,"arm":arm,"dataset":r["dataset"],
                         "event_group":reg["groups"].get(oid,r["leakage_group"])})
    return root,rows

def summarize(c,smoke=False):
    _,rows=records(c,smoke)
    states=dict(Counter(r["status"] for r in rows))
    return {"status":"incomplete" if states.get("pending") else "complete", "positions":len(rows),"counts":states,
            "by_arm":{a:dict(Counter(r["status"] for r in rows if r["arm"]==a)) for a in ARMS},
            "reference_positions":sum(bool(r.get("no_op")) for r in rows)}

def review_smoke(c):
    from RQs.RQ3_1.src.main import audit_completion_artifacts
    from vlmrca.run_state import DurableCallRegister
    root,rows=records(c,True)
    outcome=read_json(root/"supervisor.json")
    if outcome["status"] not in {"complete","bounded_timeout"}:
        raise RuntimeError("Smoke not qualified")
    if len(rows)!=18 or any(r["status"] not in {"done","pending","fail"} for r in rows):
        raise RuntimeError("Foreign/missing smoke matrix")
    if any(r["status"]=="fail" and r.get("failure_class")!="request_timeout" for r in rows):
        raise RuntimeError("Non-timeout smoke failure")
    if any(r["status"]=="pending" for r in rows) and outcome["status"]!="bounded_timeout":
        raise RuntimeError("Unexplained missing smoke results")
    seen=set(); audits=[]
    for r in rows:
        if r["status"]!="done" or r["call_key"] in seen:
            continue
        seen.add(r["call_key"])
        audit_completion_artifacts(root,r["call_key"])
        result=read_json(root/"outputs"/(r["call_key"]+".json"))
        score=result.get("score",{}); metrics=score.get("metrics",score)
        if any(not isinstance(metrics.get(k),(int,float)) or not math.isfinite(metrics[k]) for k in METRICS):
            raise ValueError("Nonfinite smoke scoring")
        audits.append({"case":r["case"],"arm":r["arm"],"call_key":r["call_key"],"status":result.get("status")})
    report={"status":"passed","source_contract":source_contract(),"outcome":outcome,"completed_audits":audits,
            "accounting":DurableCallRegister(root/"calls.sqlite",scope=VERSION,limit=c["smoke_attempt_limit"]).summary(),
            "coverage_complete":all(r['status']=='done' for r in rows),
            "unfinished_positions":[{'case':r['case'],'arm':r['arm'],'status':r['status']} for r in rows if r['status']!='done'],
            "timeout_only_policy":"Codex.md: timeout alone passes the logical smoke; incomplete coverage remains explicit",
            "note":"Artifact review only; human inspection of actual PNG/input/output must supply smoke_review.json"}
    write_json(root/"artifact_review.json",report)
    return {k:v for k,v in report.items() if k!="source_contract"}

def paired(values):
    """Registered Pratt-zero test; all-zero and zero-variance are explicit."""
    import numpy as np
    from scipy.stats import wilcoxon
    x=np.round(np.asarray(values,dtype=float),12)
    if not len(x): return {'n':0,'delta':None,'p':None,'dz':None,'positive':0,'negative':0,'equal':0}
    if not np.isfinite(x).all(): raise ValueError('Nonfinite paired differences')
    sd=float(x.std(ddof=1)) if len(x)>1 else 0.
    return {'n':len(x),'delta':float(x.mean()),
            'p':float(wilcoxon(x,zero_method='pratt',alternative='two-sided').pvalue) if np.any(x) else 1.,
            'dz':float(x.mean()/sd) if sd else None,'dz_undefined_zero_variance':sd==0,
            'positive':int((x>0).sum()),'negative':int((x<0).sum()),'equal':int((x==0).sum())}

def holm(rows):
    """Unestimable tests still occupy their registered family position."""
    previous=0.
    for i,row in enumerate(sorted(rows,key=lambda x:1. if x['p'] is None else x['p'])):
        if row['p'] is None: row['holm_p']=None; continue
        previous=max(previous,min(1.,row['p']*(len(rows)-i)));row['holm_p']=previous
    return rows

def contrast(cases,coefficients,metric='mrr'):
    """Complete-case linear contrast plus partial-information score bounds.

    Every unknown arm score independently occupies [0,1]. Thus a missing
    interaction may span [-2,2], while known components tighten its bounds.
    Group tests average the same observed case contrasts within frozen events;
    full-roster bounds separately retain all cases and all registered groups.
    """
    if not coefficients or abs(sum(coefficients.values()))>1e-12: raise ValueError('Not a zero-sum contrast')
    differences=[];groups=defaultdict(list);bounds=[];group_bounds=defaultdict(list);missing=[]
    for row in cases:
        values={a:row['arms'][a]['metrics'].get(metric) if row['arms'][a].get('metrics') is not None else None for a in coefficients}
        low=high=0.;group=(row['dataset'],row['event_group'])
        for arm,k in coefficients.items():
            v=values[arm]
            if v is None: low+=min(0,k);high+=max(0,k)
            else:
                if not math.isfinite(v) or not 0<=v<=1: raise ValueError('Invalid scored metric')
                low+=k*v;high+=k*v
        bounds.append((low,high));group_bounds[group].append((low,high))
        if any(v is None for v in values.values()): missing.append(row['case']);continue
        value=round(sum(coefficients[a]*v for a,v in values.items()),12)
        differences.append(value);groups[group].append(value)
    n=len(cases)
    mean=lambda xs:sum(xs)/len(xs) if xs else None
    interval=[mean([b[i] for b in bounds]) for i in (0,1)]
    grouped_interval=[mean([mean([b[i] for b in bs]) for bs in group_bounds.values()]) for i in (0,1)]
    return {'coefficients':coefficients,'metric':metric,'registered_n':n,'missing_cases':missing,
            'case':paired(differences),'event_group':paired([mean(v) for v in groups.values()]),
            'full_denominator_bounds':interval,'full_group_bounds':grouped_interval,
            'registered_groups':len(group_bounds),'observed_group_case_counts':{'|'.join(k):len(v) for k,v in groups.items()}}
