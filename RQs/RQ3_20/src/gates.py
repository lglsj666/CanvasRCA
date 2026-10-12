"""Source and scientific gates; a failed feasibility never enables GPU execution."""
import ast
from .utils import ROOT,config,register,read,write,sha,source_contract


def static(c):
    modules=sorted((ROOT/'RQs/RQ3_20/src').glob('*.py'))
    functional=[p for p in modules if p.name!='__init__.py']
    assert len(functional)==5
    lines=sum(len(p.read_text().splitlines()) for p in functional);assert lines<=7500
    for file in modules:ast.parse(file.read_text())
    tree=ast.parse((ROOT/'RQs/RQ3_20/src/exps.py').read_text())
    for node in ast.walk(tree):
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
            assert node.func.id not in {'open','eval','exec','compile','read_json'}
    assert config()==c and len(register(c)['cases'])==220
    assert c['max_context']==40960 and c['max_final_tokens']==8192 and c['max_select_tokens']==512
    assert not c['attention_enabled']
    from .utils import runtime,phase_arms
    runtime(c)
    assert sum(len(phase_arms(c,r)) for r in register(c)['cases'])==1520
    import subprocess
    for shell in (ROOT/'RQs/RQ3_20/scripts').glob('*.sh'):subprocess.run(['bash','-n',str(shell)],check=True)
    protection=ROOT/c['results']/'qualification/protection_before.json'
    if protection.exists():
        for name,expected in read(protection)['files'].items():assert sha(ROOT/name)==expected,'Protected source changed: '+name
    report={'status':'passed','source_contract':source_contract(c),'functional_modules':len(functional),
            'source_lines':lines,'checks':['AST','five modules and 7500 lines','public-only pure compiler',
              'immutable220 eval roster','3000-call allocation','closed GPU defaults','protected historical sources'],
            'new_model_calls':0,'scope':'source/config checks only; CPU and GPU execution require separate qualifications'}
    write(ROOT/c['results']/'qualification/static.json',report)
    return {k:v for k,v in report.items() if k!='source_contract'}


def require_feasibility(c):
    report=read(ROOT/c['results']/'qualification/cpu_feasibility.json')
    if report['status']!='passed' or report['source_contract']!=source_contract(c):
        raise RuntimeError('Scientific feasibility failed or stale; GPU prohibited')
    return report


def summarize(c,smoke=False):
    from collections import Counter
    from .utils import phase_arms,flag,MODEL
    root=ROOT/c['results']/('smoke' if smoke else 'formal');reg=register(c)
    rows=[]
    for row in reg['smoke' if smoke else 'cases']:
        for arm in phase_arms(c,row,smoke):
            rows.append(flag(root,row['opaque_incident_id'],arm) or {'case':row['opaque_incident_id'],'arm':arm,'status':'pending'})
    counts=dict(Counter(r['status'] for r in rows))
    return {'status':'complete' if not counts.get('pending') else 'incomplete','positions':len(rows),'counts':counts,
      'by_arm':{a:dict(Counter(r['status'] for r in rows if r['arm']==a)) for a in sorted({r['arm'] for r in rows})}}


def freeze(c):
    import tarfile
    from .utils import digest
    q=ROOT/c['results']/'qualification';current=source_contract(c)
    for name in ('static','cpu','visual_review','cpu_feasibility'):
        r=read(q/(name+'.json'));assert r['status']=='passed' and r['source_contract']==current,name
    assert read(q/'checkpoint_audit.json')['status']=='passed'
    archive=q/'frozen_source.tar.gz'
    if archive.exists():
        old=read(q/'source_freeze.json');assert old['source_contract']==current and old['archive_sha256']==sha(archive)
    else:
        with tarfile.open(archive.with_suffix('.tmp'),'w:gz') as tar:
            for name in current['files']:tar.add(ROOT/name,arcname=name)
        archive.with_suffix('.tmp').replace(archive)
        write(q/'source_freeze.json',{'status':'frozen','source_contract':current,'archive_sha256':sha(archive)})
    return {'status':'frozen','files':len(current['files']),'source_hash':digest(current)}


def authorize(c):
    from .utils import digest,VERSION
    q=ROOT/c['results']/'qualification';current=source_contract(c)
    assert read(q/'source_freeze.json')['source_contract']==current
    value={'status':'authorized','source_contract_hash':digest(current),'config_hash':digest(c),
      'registration_hash':digest(register(c)),'version':VERSION,'overview_fraction':.5,
      'authority':'explicit user instruction: raise first-input cap to 50%; if qualified smoke then full launch',
      'smoke_authorized':True,'formal_after_smoke_pass':True,'conditional_modules_disabled':True,
      'smoke_limit':18,'formal_limit':2312,'overall_limit':3000}
    file=q/'execution_authorization.json'
    if file.exists():assert read(file)==value
    else:write(file,value)
    return {k:v for k,v in value.items() if 'hash' not in k}


def require_qualification(c,smoke=False):
    from .utils import digest
    q=ROOT/c['results']/'qualification';current=source_contract(c)
    auth=read(q/'execution_authorization.json')
    assert auth['status']=='authorized' and auth['smoke_authorized'] and auth['formal_after_smoke_pass']
    assert auth['source_contract_hash']==digest(current) and auth['config_hash']==digest(c) and auth['registration_hash']==digest(register(c))
    frozen=read(q/'source_freeze.json')
    assert frozen['source_contract']==current and sha(q/'frozen_source.tar.gz')==frozen['archive_sha256']
    for name in ('static','cpu','cpu_feasibility','visual_review')+(() if smoke else ('smoke_review',)):
        report=read(q/(name+'.json'));assert report['status']=='passed' and report['source_contract']==current,name
    if not smoke:assert read(q/'smoke_review.json')['actual_inputs_outputs_reviewed']
    import os
    assert os.environ.get('CANVASRCA_ATTENTION_PROBE','0')!='1','Unqualified legacy attention collector'


def review_smoke(c):
    from .utils import ledger_for,MODEL
    from . import exps
    from RQs.RQ3_1.src.main import audit_completion_artifacts
    from .utils import diagnostic_scorer
    q=ROOT/c['results']/'qualification';root=ROOT/c['results']/'smoke'
    outcome=read(root/'supervisor.json');assert outcome['status'] in {'complete','bounded_timeout'}
    assert not (root/'infrastructure_failure.json').exists()
    audits=[]
    for file in sorted((root/'completed').glob('*.json')):
        key=file.stem;audit_completion_artifacts(root,key)
        out=read(root/'outputs'/(key+'.json'));cost=read(root/'cost'/(key+'.json'))
        public=read(ROOT/c['preparation']/'public'/(out['case']+'.json'))
        if out['stage']=='select':
            expected={'status':'complete' if exps.selection(out['response'],public)['valid'] else 'model_failure','selection':exps.selection(out['response'],public)}
            cap=c['max_select_tokens']
        elif out['stage']=='qa':
            expected=exps.score_qa(read(root/'mechanism'/(out['case']+'.json')),out['response']);cap=c['qa_max_tokens']
        else:
            expected=diagnostic_scorer(read(ROOT/c['preparation']/'private'/(out['case']+'.json')),public['candidates'])(out['response']);cap=c['max_final_tokens']
        assert out['score']==expected and cost['output_tokens']<=cap
        assert cost['input_tokens']+cap<=40960
        marker=read(file);prompts=[p for p in marker['response_artifact_hashes'] if p.startswith('prompts/')]
        assert len(prompts)==1
        prompt=read(root/prompts[0]);assert prompt['effective_server']['max_tokens']==cap
        for part in prompt['parts']:
            if 'image_path' in part:
                from PIL import Image
                with Image.open(root/part['image_path']) as image:assert image.width==1440
        audits.append({'case':out['case'],'arm':out['arm'],'stage':out['stage'],'call_key':key,'model_status':out['status'],
          'input_tokens':cost['input_tokens'],'output_tokens':cost['output_tokens'],'image_tokens':cost['image_tokens']})
    accounting=ledger_for(c,True).summary()
    import sqlite3
    with sqlite3.connect(ROOT/c['results']/'calls.sqlite') as db:
        attempts=db.execute("select count(*) from calls where call_key like ?",('%/smoke/%',)).fetchone()[0]
    assert attempts<=18
    if outcome['status']=='complete':assert summarize(c,True)['status']=='complete'
    value={'status':'passed','source_contract':source_contract(c),'actual_inputs_outputs_reviewed':True,'audits':audits,
      'outcome':outcome,'smoke_attempts':attempts,'accounting':accounting,'coverage':summarize(c,True),
      'timeout_only':outcome['status']=='bounded_timeout','ranking_used_as_gate':False,
      'attention':'disabled: legacy collector fails bounded-record contract; no attention qualification claimed'}
    write(root/'artifact_review.json',value);write(q/'smoke_review.json',value)
    return {k:v for k,v in value.items() if k not in {'source_contract','audits'}}


def analyze(c):
    """Full-denominator concurrent-method results; no automatic conditional launch."""
    from collections import defaultdict
    from .utils import phase_arms,flag,ARMS
    from RQs.RQ3_18.src.gates import contrast,holm
    reg=register(c);root=ROOT/c['results']/'formal';summary=summarize(c)
    assert summary['status']=='complete'
    cases=[]
    for row in reg['cases']:
        oid=row['opaque_incident_id'];arms={}
        for arm in phase_arms(c,row):
            item=flag(root,oid,arm);arms[arm]={'metrics':item.get('metrics'),'status':item['status'],'cost':item.get('cost'),
              'accepted':item.get('accepted',[]),'references':item.get('references',[])}
        cases.append({'case':oid,'dataset':row['dataset'],'event_group':reg['groups'][oid],'arms':arms})
    absolute=[];metrics=('mrr','ac@1','ac@3','ac@5','avg@3','avg@5')
    allarms=sorted({a for r in cases for a in r['arms']})
    for ds in ('all',*c['case_counts']):
        subset=[r for r in cases if ds=='all' or r['dataset']==ds]
        for arm in allarms:
            items=[r['arms'][arm] for r in subset if arm in r['arms']]
            applicable=[x for x in items if x['status']!='not_applicable'];known=[x for x in applicable if x['metrics'] is not None]
            keys=('qa_accuracy',) if arm.startswith('QA_') else metrics
            vals={m:sum(x['metrics'][m] for x in known) for m in keys}
            absolute.append({'dataset':ds,'arm':arm,'registered':len(items),'applicable':len(applicable),'known':len(known),
              'metrics':{m:v/len(known) if known else None for m,v in vals.items()},
              'bounds':{m:[v/len(applicable),(v+len(applicable)-len(known))/len(applicable)] if applicable else [None,None] for m,v in vals.items()},
              'mean_total_tokens':sum(x['cost']['total_tokens'] for x in known)/len(known) if known else None})
    families={}
    definitions={'primary':[{a:1,b:-1} for a,b in c['primary_contrasts']],
      'secondary':[{'TEXT_FETCH':1,'FULL_TEXT':-1},{'VISUAL_FETCH':1,'TEXT_FETCH':-1,'SUMMARY_VISUAL':-1,'SUMMARY_TEXT':1},
                   {'TEXT_REPEAT':1,'TEXT_FETCH':-1},{'VISUAL_REPEAT':1,'VISUAL_FETCH':-1}],
      'mechanism':[{'QA_FOCUS':1,'QA_NONE':-1},{'QA_CONTROL':1,'QA_NONE':-1},{'QA_FOCUS':1,'QA_CONTROL':-1},
                   {'FOCUS_FETCH':1,'VISUAL_FETCH':-1},{'CONTROL_FETCH':1,'VISUAL_FETCH':-1},{'FOCUS_FETCH':1,'CONTROL_FETCH':-1}]}
    for name,defs in definitions.items():
        values=[]
        for coeff in defs:
            subset=[r for r in cases if all(a in r['arms'] and r['arms'][a]['status']!='not_applicable' for a in coeff)]
            if not subset:
                from RQs.RQ3_18.src.gates import paired
                values.append({'coefficients':coeff,'status':'not_applicable','case':paired([]),'event_group':paired([])});continue
            values.append(contrast(subset,coeff,'qa_accuracy' if next(iter(coeff)).startswith('QA_') else 'mrr'))
        for level in ('case','event_group'):holm([v[level] for v in values if level in v])
        families[name]=values
    report={'status':'complete_core_analysis','source_contract':source_contract(c),'absolute':absolute,'families':families,
      'cases':cases,'scope':'exposed eval; full workflow costs including selector and referenced requests',
      'conditional_modules':'not automatically activated; SIRCL fidelity and independent90 exposure audit required',
      'attention':'not collected; bounded-record compatibility failed', 'adoption':'pending dataset, repeat, cost and explanation review'}
    write(root/'analysis/complete_core.json',report)
    lines=['# RQ3.20 complete core results','', '| Dataset | Arm | Known/applicable | MRR or QA | Mean total tokens |','|---|---|---:|---:|---:|']
    for r in absolute:
        value=r['metrics'].get('mrr',r['metrics'].get('qa_accuracy'))
        lines.append(f"| {r['dataset']} | {r['arm']} | {r['known']}/{r['applicable']} | {value} | {r['mean_total_tokens']} |")
    lines.extend(['','Full metrics, paired Holm families and denominators: `analysis/complete_core.json`.','No candidate adoption or independent-confirmation claim is made automatically.'])
    from vlmrca.run_state import atomic_write
    atomic_write(root/'analysis/complete_core.md',('\n'.join(lines)+'\n').encode())
    return {'status':report['status'],'positions':summary['positions']}
