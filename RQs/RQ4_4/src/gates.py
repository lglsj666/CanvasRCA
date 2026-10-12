"""Qualification is explicit; incomplete checks never activate GPU or formal work."""
from .utils import ROOT, RQ, RESULTS, read, save, protected_snapshot, digest, stable


def static_check():
    import ast
    modules={p.name for p in (RQ/'src').glob('*.py')}
    if modules!={'__init__.py','main.py','utils.py','exps.py','tests.py','gates.py'}:
        raise ValueError('Five functional module contract violated')
    nonblank=0
    for path in (RQ/'src').glob('*.py'):
        source=path.read_text();ast.parse(source)
        nonblank+=sum(bool(line.strip()) and not line.lstrip().startswith('#') for line in source.splitlines())
        for node in ast.walk(ast.parse(source)):
            if isinstance(node,ast.ImportFrom) and node.module and ('scor' in node.module or 'matching' in node.module):
                if node.module!='scorer':
                    raise ValueError('Scorer imports must use central package')
    if nonblank>7500:
        raise ValueError('Source line budget exceeded')
    original=read(RESULTS/'qualification/protected_sources.json')
    if protected_snapshot()!=original:
        raise ValueError('Protected historical/component/Codex source changed')
    cfg=read(RQ/'configs/protocol_v1.json')
    if cfg['smoke_enabled'] or cfg['formal_enabled']:
        raise ValueError('Default launch flags must remain closed')
    for path in cfg['global_configs']:
        if not (ROOT/path).is_file():
            raise ValueError('Missing unified config: '+path)
    if cfg['formal_positions']+cfg['smoke_calls']+cfg['infrastructure_reserve']!=cfg['total_call_limit']:
        raise ValueError('Call budget mismatch')
    result={'status':'passed','functional_nonblank_lines':nonblank,'protected_files':len(original),
            'gpu_enabled':False,'new_model_calls':0,'source_fingerprint':execution_fingerprint()}
    save(RESULTS/'qualification/static.json',result)
    return result


def execution_fingerprint():
    paths=list((RQ/'src').glob('*.py'))+list((RQ/'configs').glob('*.json'))
    paths += [ROOT/'src/renderer/operations/source_views.py',ROOT/'src/renderer/web/sourceViews.mjs',
              ROOT/'RQs/RQ4_3/src/utils.py',ROOT/'src/vlmrca/vlm/passive_summary.py',ROOT/'src/vlmrca/run_state.py']
    paths+=list((ROOT/'src/scorer').glob('*.py'))
    return stable({str(p.relative_to(ROOT)):digest(p) for p in paths})


def require_execution(scope):
    if scope not in {'smoke', 'formal'}:
        raise ValueError('Unknown execution scope')
    certificate = RESULTS / 'qualification' / f'{scope}_activation.json'
    if not certificate.exists():
        raise RuntimeError(f'{scope} is disabled: no frozen qualification credential')
    credential=read(certificate)
    if credential.get('status')!='passed' or credential.get('execution_fingerprint')!=execution_fingerprint():
        raise RuntimeError('Launch credential does not match current qualified source')
    frozen=read(RESULTS/'frozen/contract.json')
    if credential['contract_sha256']!=digest(RESULTS/'frozen/contract.json') or frozen['execution_fingerprint']!=execution_fingerprint():
        raise RuntimeError('Frozen generation dependencies changed')
    if digest(RESULTS/'frozen'/f'{scope}_queue.json')!=frozen['queues'][scope]:
        raise RuntimeError('Registered execution queue changed')
    from .utils import MODEL
    for path,checksum in frozen['global_configs'].items():
        if digest(ROOT/path)!=checksum:raise RuntimeError('Unified configuration changed after freeze')
    for path,checksum in frozen['model'].items():
        if digest(MODEL/path)!=checksum:raise RuntimeError('Model/processor identity changed after freeze')
    if scope=='formal':
        smoke=read(RESULTS/'smoke/review.json')
        if smoke['status']!='passed':raise RuntimeError('GPU smoke not qualified')


def freeze_cpu():
    import shutil,collections
    from .utils import roster,MODEL
    from .exps import build_queue
    static_check()
    gates={name:read(RESULTS/'qualification'/f'{name}.json') for name in ('population','mechanism','unit','runtime','visual')}
    if any(g['status']!='passed' for g in gates.values()):
        raise RuntimeError('Some CPU/visual qualifications have not passed')
    if len(gates['population']['cases'])!=220 or len(gates['runtime']['requests'])!=18:
        raise ValueError('Incomplete registered coverage')
    frozen=RESULTS/'frozen';frozen.mkdir(exist_ok=True)
    if (frozen/'contract.json').exists():
        raise FileExistsError('Freeze is immutable; use an explicit revision for changes')
    queues={}
    for scope in ('smoke','formal'):
        queue=build_queue(scope);save(frozen/f'{scope}_queue.json',queue);queues[scope]=digest(frozen/f'{scope}_queue.json')
    configs={p:digest(ROOT/p) for p in read(RQ/'configs/protocol_v1.json')['global_configs']}
    model={p:digest(MODEL/p) for p in ('config.json','preprocessor_config.json','generation_config.json','tokenizer_config.json','chat_template.jinja','download_sha256.txt')}
    snapshots={}
    files=list((RQ/'src').glob('*.py'))+list((RQ/'configs').glob('*.json'))
    files+=[ROOT/p for p in ('src/renderer/operations/source_views.py','src/renderer/web/sourceViews.mjs',
        'RQs/RQ4_3/src/utils.py','src/vlmrca/vlm/passive_summary.py','src/vlmrca/run_state.py')]
    for path in files:
        target=frozen/'source'/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,target);snapshots[str(path.relative_to(ROOT))]=digest(target)
    save(frozen/'contract.json',{'schema':'RQ44FrozenContractV1','execution_fingerprint':execution_fingerprint(),
        'queues':queues,'source_snapshots':snapshots,'global_configs':configs,'model':model,
        'gpu_dtype':'bfloat16','sampling':'greedy rank prefix, existing sampled explanation','processor_limits_changed':False,
        'attention_queries':['last_prompt_query','first_decode_query'],
        'attention_scope_limitation':'Does not capture later ranked-answer field queries or the full decision process',
        'main_cases':220,'formal_positions':840,'call_limit':900,'smoke_limit':18,'smoke_seconds':600,
        'historical_references':['RQ4.1 A_UNIFORM_E50','RQ4.1 T_FULL','RQ3.16 MARGINAL_FIVE'],
        'historical_comparison_limitation':'Different historical backend; reused references are not contemporary causal controls',
        'primary_family':['SOURCE_ZOOM-REPEAT_VIEW','SOURCE_ZOOM-HASH_ZOOM'],
        'primary_test':'two-sided event-group Pratt-zero Wilcoxon; Holm; rounded 12 decimal differences; no CI'})
    summaries={}
    for ds in ('aiops2022','aiops2025','aegislab'):
        rows=[r for r in gates['population']['cases'] if r['dataset']==ds]
        summaries[ds]={'cases':len(rows),'mean_input_tokens':sum(r['processor']['SOURCE_ZOOM']['input_tokens'] for r in rows)/len(rows),
            'local_cards_min':min(r['selected']['SOURCE_ZOOM'] for r in rows),'local_cards_max':max(r['selected']['SOURCE_ZOOM'] for r in rows)}
    report={'status':'passed','scope':'static, all-case CPU, mechanism, actual views and offline runtime',
        'datasets':summaries,'new_model_calls':0,'execution_fingerprint':execution_fingerprint(),
        'contract_sha256':digest(frozen/'contract.json')}
    save(RESULTS/'qualification/cpu_complete.json',report)
    save(RESULTS/'qualification/smoke_activation.json',report)
    return report


def review_smoke():
    import time
    root=RESULTS/'smoke';summary=read(root/'summary.json');queue=read(RESULTS/'frozen/smoke_queue.json')
    if summary['status']!='passed' or summary['seconds']>600 or summary['completed']!=18:
        raise RuntimeError('Logical smoke incomplete, failed or outside its shared wall-clock limit')
    reviewed=[];attention=[]
    for entry in queue:
        item=entry['item'];result=read(root/'completed'/f'{item["key"]}.json')
        request=read(root/result['request_path']);usage=result['usage']
        if result['request_hash']!=entry['request']['identity'] or usage['input_tokens']!=request['input_tokens']:
            raise ValueError('Smoke request/accounting identity differs')
        if usage['branch_calls']!=0 or usage['engine_preemptions'] or usage['attention_error'] or usage['attention_missed']:
            raise ValueError('Unqualified runtime operation or attention loss')
        if usage['input_tokens']+usage['output_tokens']>40960 or usage['output_tokens']>8192:
            raise ValueError('Smoke context accounting failed')
        for path,checksum in zip(request['images'],request['image_sha256']):
            if digest(ROOT/path)!=checksum:raise ValueError('Smoke image differs from registration')
        if request['attention']:
            path=root/'attention'/f'{usage["attention_record_key"]}.json'
            if not path.exists() or path.stat().st_size>65536:raise ValueError('Missing/oversized passive attention record')
            attention.append(str(path.relative_to(ROOT)))
        reviewed.append({'key':item['key'],'task':item['task'],'response':result['response'],'outcome':result['outcome'],
                         'input_tokens':usage['input_tokens'],'output_tokens':usage['output_tokens']})
    clock=read(root/'logical_clock.json')
    if time.time()>clock['deadline_unix']:
        raise RuntimeError('Smoke verification exceeded the shared 600-second budget')
    report={'status':'passed','reviewed':reviewed,'attention_records':attention,'accuracy_is_gate':False,
        'logical_elapsed_seconds':time.time()-clock['started_unix'],
        'seconds':summary['seconds'],'execution_fingerprint':execution_fingerprint()}
    save(root/'review.json',report)
    save(RESULTS/'qualification/formal_activation.json',{'status':'passed','execution_fingerprint':execution_fingerprint(),
        'contract_sha256':digest(RESULTS/'frozen/contract.json')})
    return report


def analyze_completed():
    import numpy as np
    from scipy.stats import wilcoxon
    from collections import defaultdict
    from .exps import ARMS
    from .utils import roster
    folder=RESULTS/'formal';rows=roster();dataset={r['id']:r['dataset'] for r in rows};events={r['id']:r['event_group'] for r in rows}
    results=[read(p) for p in (folder/'completed').glob('*.json')]
    main={}
    for r in results:
        item=r['item']
        if item['variant']=='BASE':main[(item['id'],item['arm'])]=r
    summaries=[]
    for arm in ARMS:
        for ds in ('all','aiops2022','aiops2025','aegislab'):
            ids=[r['id'] for r in rows if ds=='all' or r['dataset']==ds]
            available=[main[(i,arm)] for i in ids if (i,arm) in main]
            metrics=['mrr','ac@1','ac@3','ac@5','avg@3','avg@5']
            row={'arm':arm,'dataset':ds,'registered':len(ids),'completed':len(available),'unknown':len(ids)-len(available)}
            for mode in ('standard','tolerant'):
                vals=[r['outcome'][mode]['metrics'] if mode=='standard' else r['outcome'][mode] for r in available]
                row[mode]={k:sum(v[k] for v in vals)/len(vals) if vals else None for k in metrics}
                known=sum(v['mrr'] for v in vals);row[mode]['mrr_full_denominator_bounds']=[known/len(ids),(known+row['unknown'])/len(ids)]
                row[mode]['precision@1']=row[mode]['ac@1'];row[mode]['precision@3']=row[mode]['ac@3']/3 if vals else None
            row['mean_input_tokens']=sum(r['usage']['input_tokens'] for r in available)/len(available) if available else None
            row['mean_output_tokens']=sum(r['usage']['output_tokens'] for r in available)/len(available) if available else None
            row['invalid_model_outputs']=sum(r['outcome']['standard']['status']=='model_failure' for r in available)
            summaries.append(row)
    comparisons=[]
    for control in ('REPEAT_VIEW','HASH_ZOOM'):
        paired=[(r['id'],main[(r['id'],'SOURCE_ZOOM')]['outcome']['standard']['metrics']['mrr']-
                 main[(r['id'],control)]['outcome']['standard']['metrics']['mrr']) for r in rows
                 if (r['id'],'SOURCE_ZOOM') in main and (r['id'],control) in main]
        grouped=defaultdict(list)
        for oid,value in paired:grouped[events[oid]].append(value)
        for unit,values in [('case',[v for _,v in paired]),('event_group',[np.mean(v) for v in grouped.values()])]:
            d=np.round(np.asarray(values,dtype=float),12);sd=float(d.std(ddof=1)) if len(d)>1 else 0
            p=float(wilcoxon(d,zero_method='pratt',alternative='two-sided',method='auto').pvalue) if np.any(d) else 1.
            comparisons.append({'comparison':'SOURCE_ZOOM-'+control,'unit':unit,'n':len(d),
                'mean_delta':float(d.mean()) if len(d) else None,'p':p,'dz':float(d.mean()/sd) if sd else None,
                'improved':int((d>0).sum()),'harmed':int((d<0).sum()),'unchanged':int((d==0).sum())})
    for unit in ('case','event_group'):
        family=sorted((r for r in comparisons if r['unit']==unit),key=lambda r:r['p']);prior=0
        for i,r in enumerate(family):
            prior=max(prior,min(1.,(len(family)-i)*r['p']));r['holm_p']=prior
    attention=[]
    for path in (folder/'attention').glob('*.json'):
        record=read(path);attention.append({'path':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,
            'layer':record.get('layer'),'query_definition':record.get('query_definition'),
            'text_mass':record.get('text_mass'),'image_mass':record.get('image_mass')})
    report={'status':'complete' if len(results)==840 else 'incomplete','positions':len(results),
        'main':summaries,'primary_family':comparisons,'attention':attention,
        'mechanism_results':[r for r in results if r['item']['variant']!='BASE'],
        'qualitative_review_status':'pending manual reading of the registered 30-case QA/RCA answers',
        'historical_references':{'U_standard_mrr':.351742,'T_FULL_standard_mrr':.484621,'MARGINAL_FIVE_hybrid_mrr':.5054},
        'caveat':'Historic baselines are reused across backends; this does not establish concurrent causal effects. Attention covers only its recorded queries.'}
    save(RESULTS/'analysis/results.json',report)
    lines=['# RQ4.4 完整结果自动汇总','',f'完成位置：{len(results)}/840。定性逐回答审查仍需人工完成。','',
        '| Arm | 数据集 | 标准 MRR | 宽容 MRR | 平均输入 | 平均输出 |','|---|---|---:|---:|---:|---:|']
    for r in summaries:
        lines.append(f"| {r['arm']} | {r['dataset']} | {r['standard']['mrr']} | {r['tolerant']['mrr']} | {r['mean_input_tokens']} | {r['mean_output_tokens']} |")
    lines.extend(['','事件组主要推断、病例补充推断及两项 Holm 校正见 results.json；不报告 CI。',
        '历史 U/强文本/混合参照复用，不是同期对照。实际成本包含两张图编码开销，不能仅凭 token 数声称速度提升。'])
    (RESULTS/'analysis/report.md').write_text('\n'.join(lines)+'\n')
    return report
