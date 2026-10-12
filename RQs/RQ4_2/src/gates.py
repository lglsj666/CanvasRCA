"""Fail-closed static, history and runtime admission checks."""
import ast
from .utils import ROOT, RQ, RESULTS, PREPARED, ARMS, read, write, sha


def protected_history():
    old = read(RESULTS/'protected_before.json')
    # The report index is intentionally updated by this task; historical report
    # bodies remain immutable. Preserve its original digest in the baseline.
    mutable_index = 'docs/experiment_reports/README.md'
    old = {p: value for p, value in old.items() if p != mutable_index}
    changed = [p for p, digest in old.items() if not (ROOT/p).is_file() or sha(ROOT/p) != digest]
    if changed:
        raise ValueError('Protected history changed: '+str(changed))
    return len(old)


def static_check():
    config = read(RQ/'configs/partition_v4.json')
    if tuple(config['arms']) != ARMS or config['gpu_enabled'] or config['formal_enabled']:
        raise ValueError('Arm inventory or disabled startup contract')
    if sum(config['calls'][k] for k in ('main', 'qa', 'smoke', 'infrastructure_reserve')) != 1500 or config['calls']['total'] != 1500:
        raise ValueError('Call budget drift')
    if config['calls']['smoke'] != 18 or config['smoke_seconds'] != 600:
        raise ValueError('Single logical smoke contract')
    invariant={'groups':4,'partition_blocks':[0,22],'global_blocks':[23,26],
      'background_change_cap':.05,'max_improvements':100,'max_refinement_passes':8,
      'membership_change_min':.2,'cut_reduction_min':.15,'joint_admission_fraction':.5,
      'sham_replacement_min':.5,'maximum_image_tokens':16384,'context':40960,'maximum_output':8192,
      'grouping_algorithm':'deterministic_best_prefix_v4','objective':'original_uniform_source_unit_edges'}
    if any(config.get(k)!=v for k,v in invariant.items()):raise ValueError('Registered method/gate invariant changed')
    # Audit results bind the algorithm actually executed, rather than merely its name.
    audited=RESULTS/'grouping/algorithm_at_audit.py'
    if audited.exists():
        current=(RQ/'src/exps.py').read_text();prior=audited.read_text()
        def functions(text):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)}
        a,b=functions(current),functions(prior)
        if any(a[k]!=b[k] for k in ('optimize_groups_refined','unit_edges','fill_background','rewire_edges')):
            raise ValueError('Grouping algorithm differs from audited version')
    expected = {'__init__.py', 'main.py', 'utils.py', 'exps.py', 'tests.py', 'gates.py'}
    files = list((RQ/'src').glob('*.py'))
    if {p.name for p in files} != expected:
        raise ValueError('Five-module source structure')
    count = 0
    for p in files:
        content = p.read_text()
        tree = ast.parse(content, filename=str(p))
        count += sum(bool(line.strip()) and not line.lstrip().startswith('#') for line in content.splitlines())
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or '']
                if any('rca_scorer' in n or 'vlmrca.eval.scoring' in n for n in names):
                    raise ValueError('Forbidden old scorer import')
    if count > 7500:
        raise ValueError('Source line cap')
    result = {'status': 'passed', 'functional_lines': count, 'protected_files': protected_history(),
              'config_sha256': sha(RQ/'configs/partition_v4.json'),
              'model_calls': 0, 'gpu_enabled': False, 'formal_enabled': False}
    write(RESULTS/'static.json', result)
    return result


def require_execution_qualification(stage=None):
    # CPU success alone never grants model execution authority. Activation is a
    # separate, version-bound artifact created only under a later user request.
    activation=RQ/'configs/activation.json'
    if not activation.exists():
        raise RuntimeError('CPU-only authorization: GPU smoke and formal calls remain disabled')
    permit=read(activation)
    # The qualified solver/session constructors share this guard. Explicit
    # callers still cannot use a formal permit to enter the smoke supervisor.
    if stage is None:
        stage='formal' if permit.get('allowed_stages')==['formal'] else 'smoke'
    if stage=='smoke':
        from .utils import smoke_paths
        _,registration=smoke_paths()
        if permit.get('smoke_registration_sha256')!=sha(registration):
            raise RuntimeError('Missing or stale smoke registration credential')
        config=read(registration)
        if registration.name.startswith('smoke_supplement_'):
            authority=RQ/'configs/smoke_supplement_authority_20261009.json'
            a=read(authority)
            if (config.get('authority_sha256')!=sha(authority) or a['authorized_additional_rounds']!=5
                or a['calls_per_round']!=18 or a['seconds_per_round']!=600 or a['formal_authorized']
                or not 1<=config['supplement_number']<=5 or len(config['items'])>18
                or config['scope']!=registration.stem or config['scope']!=f"smoke_supplement_{config['supplement_number']}"):
                raise RuntimeError('Additional smoke authority mismatch')
    receipt=RESULTS/'qualification_complete.json'
    if not receipt.exists() or read(receipt).get('status')!='passed':
        raise RuntimeError('Complete CPU qualification has not passed')
    if permit.get('cpu_receipt_sha256')!=sha(receipt) or stage not in permit.get('allowed_stages',[]):
        raise RuntimeError('Missing or stale version-bound activation credential')
    qualified=read(receipt)
    if any(sha(ROOT/p)!=value for p,value in qualified['source_hashes'].items()):
        raise RuntimeError('Qualified source/dependency version changed')
    if stage=='formal':
        ready=formal_readiness()
        if permit.get('formal_readiness_sha256')!=sha(RESULTS/'formal_readiness.json') or ready['status']!='ready':
            raise RuntimeError('Missing or stale formal readiness credential')
        if permit.get('formal_registration_sha256')!=sha(RQ/'configs/formal_v1.json'):
            raise RuntimeError('Formal registration credential mismatch')
    if read(RESULTS/'grouping/report.json').get('sem_qualified') is not True:
        raise RuntimeError('SEM intervention admission failed')


def admission_decision():
    import xml.etree.ElementTree as ET
    static=static_check()
    capacity=read(PREPARED/'capacity/report.json');packing=read(PREPARED/'packing/report.json')
    renders=read(PREPARED/'render_report.json');groups=read(RESULTS/'grouping/report.json')
    def status(name):
        path=RESULTS/name
        return read(path).get('status','pending') if path.exists() else 'pending'
    qa=read(RESULTS/'qa/report.json') if (RESULTS/'qa/report.json').exists() else {}
    tests_path=RESULTS/'regression.xml';test_status='pending'
    if tests_path.exists():
        cases=ET.parse(tests_path).getroot().findall('.//testcase')
        failed=any(c.find('failure') is not None or c.find('error') is not None for c in cases)
        inherited={c.attrib['name'] for c in ET.parse(PREPARED/'regression.xml').getroot().findall('.//testcase')
                   if not any(c.find(t) is not None for t in ('failure','error','skipped'))}
        skipped=[c.attrib['name'] for c in cases if c.find('skipped') is not None]
        test_status='passed' if len(cases)>=28 and not failed and set(skipped)<=inherited else 'failed'
    reports={
      'static':static['status'],
      'necessary_capacity':'passed' if capacity['whole_population'] and all(r['necessary_capacity_pass'] for r in capacity['cases']) else 'failed',
      'source_closed_packing':'passed' if len(packing['cases'])==220 and all(r['status']=='packed' for r in packing['cases']) else 'failed',
      'full_dashboard_rendering':'passed' if len(renders)==220 and all(r['status']=='passed' for r in renders) else 'failed',
      'SEM_population_intervention':'passed' if groups['sem_qualified'] else 'failed',
      'SHAM_population_intervention':'passed' if groups['sham_qualified'] else 'cancelled_per_protocol',
      'current_QA_inputs':'passed' if len(qa.get('cases',[]))==60 and not qa.get('counts',{}).get('failed') and sum(qa.get('counts',{}).values())==60 else 'pending',
      'current_actual_processor':status('processor/report.json'),
      'offline_cold_paths':status('offline_cold/report.json'),
      'regression':test_status,'visual_review':status('visual_review.json'),
      'compatible_prior_preparation':status('preparation_reuse.json')}
    final_tests=RESULTS/'final_gates.xml'
    if final_tests.exists():
        extra=ET.parse(final_tests).getroot().findall('.//testcase')
        reports['final_gate_regression']='passed' if len(extra)>=3 and not any(any(c.find(t) is not None for t in ('failure','error','skipped')) for c in extra) else 'failed'
    else:reports['final_gate_regression']='pending'
    precision=RESULTS/'qa_precision_regression.xml'
    if precision.exists():
        cases=ET.parse(precision).getroot().findall('.//testcase')
        reports['qa_exact_precision']='passed' if len(cases)>=3 and not any(any(c.find(t) is not None for t in ('failure','error','skipped')) for c in cases) else 'failed'
    else:reports['qa_exact_precision']='pending'
    if (RQ/'configs/smoke_v1.json').exists():
        path=RESULTS/'smoke_runner_cpu.xml'
        cases=ET.parse(path).getroot().findall('.//testcase') if path.exists() else []
        reports['bounded_smoke_runner']='passed' if len(cases)>=6 and not any(any(c.find(t) is not None for t in ('failure','error','skipped')) for c in cases) else 'pending'
    if (RQ/'configs/smoke_supplement_1.json').exists():
        path=RESULTS/'supplement_runner_cpu.xml'
        cases=ET.parse(path).getroot().findall('.//testcase') if path.exists() else []
        reports['supplement_runner']='passed' if len(cases)>=4 and not any(any(c.find(t) is not None for t in ('failure','error','skipped')) for c in cases) else 'pending'
        from .exps import supplement_compatibility
        reports['supplement_generation_compatibility']=supplement_compatibility()['status']
    # Recheck shared renderer identities before inheriting successful preparation.
    old=read(PREPARED/'cpu_source_snapshot/manifest.json')['files']
    if any(sha(ROOT/p)!=value for p,value in old.items() if p.startswith('src/renderer/')):
        reports['compatible_prior_preparation']='failed'
    passed=all(v in {'passed','passed_cpu_visual_review','cancelled_per_protocol'} for v in reports.values())
    result={'schema':'RQ42AdmissionDecisionV4','status':'passed_cpu_only' if passed else 'stopped_scientific_gate' if not groups['sem_qualified'] else 'incomplete',
            'checks':reports,'population':groups['datasets'],'model_calls':0,'gpu_started':False,
            'complete_cpu_qualification':passed,'GPU_smoke':'not_run','formal':'not_started',
            'activation_credential_present':(RQ/'configs/activation.json').exists()}
    if result['activation_credential_present']:raise ValueError('Unexpected execution activation during CPU-only work')
    write(RESULTS/'qualification_decision.json',result)
    return result


def seal_cpu_qualification():
    decision=admission_decision()
    if not decision['complete_cpu_qualification']:raise ValueError('CPU admission is incomplete')
    paths=list((RQ/'src').glob('*.py'))+[RQ/'configs/partition_v4.json',RQ/'configs/prompts_v2.json',
      RESULTS/'model_identity.json',ROOT/'src/vlmrca/vlm/vision_partition.py',ROOT/'src/vlmrca/vlm/passive_summary.py',
      ROOT/'src/vlmrca/run_state.py',ROOT/'configs/rca_scorer.yaml']
    paths+=list((ROOT/'src/scorer').glob('*.py'))
    if (RQ/'configs/smoke_v1.json').exists():paths.append(RQ/'configs/smoke_v1.json')
    paths+=list((RQ/'configs').glob('smoke_supplement_*.json'))
    paths+=list((RQ/'scripts').glob('*.sh'))
    if (RQ/'configs/formal_v1.json').exists():paths.append(RQ/'configs/formal_v1.json')
    old=read(PREPARED/'cpu_source_snapshot/manifest.json')['files']
    paths+=[ROOT/p for p in old if p.startswith('src/renderer/')]
    checks=['grouping/report.json','processor/report.json','qa/report.json','regression.xml','offline_cold/report.json','preparation_reuse.json','visual_review.json','queue.json','final_gates.xml','qa_precision_regression.xml']
    if (RQ/'configs/smoke_v1.json').exists():checks.append('smoke_runner_cpu.xml')
    if (RESULTS/'supplement_runner_cpu.xml').exists():checks.append('supplement_runner_cpu.xml')
    if (RESULTS/'formal_runner_cpu.xml').exists():checks.append('formal_runner_cpu.xml')
    receipt={'schema':'RQ42CPUQualificationV4','status':'passed','source_hashes':{str(p.relative_to(ROOT)):sha(p) for p in sorted(set(paths))},
      'check_hashes':{name:sha(RESULTS/name) for name in checks},'model_calls':0,'gpu_smoke':'not_run','formal':'not_started',
      'activation_authority':False,'inherited_preparation':str(PREPARED.relative_to(ROOT))}
    write(RESULTS/'qualification_complete.json',receipt);return receipt


def formal_generation_compatibility():
    """Exact AST proof for every previously GPU-qualified generation definition."""
    import tarfile
    prior=RESULTS/'pre_formal_runner';receipt=read(prior/'qualification_complete.json');checked=[]
    with tarfile.open(prior/'sources.tar.gz','r:gz') as archive:
        for name in ('utils.py','exps.py'):
            path=RQ/'src'/name;member=str(path.relative_to(ROOT))
            old=archive.extractfile(member).read().decode()
            def definitions(source):
                return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(source).body
                        if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
            before,after=definitions(old),definitions(path.read_text())
            for key,value in before.items():
                if after.get(key)!=value:raise ValueError('Qualified GPU computation changed: '+name+':'+key)
                checked.append(name+':'+key)
    for path,value in receipt['source_hashes'].items():
        if path.startswith('RQs/RQ4_2/src/'):continue
        if sha(ROOT/path)!=value:raise ValueError('Qualified dependency changed: '+path)
    smoke=read(prior/'gpu_smoke_complete.json')
    if smoke['status']!='passed' or smoke['cpu_receipt_sha256']!=sha(prior/'qualification_complete.json'):
        raise ValueError('Prior GPU receipt does not bind inherited CPU version')
    if sha(RESULTS/'gpu_smoke_complete.json')!=sha(prior/'gpu_smoke_complete.json'):
        raise ValueError('Current GPU receipt differs from inherited qualified round')
    return {'status':'passed','unchanged_generation_definitions':checked,
            'gpu_receipt_sha256':sha(prior/'gpu_smoke_complete.json'),
            'prior_cpu_receipt_sha256':sha(prior/'qualification_complete.json'),
            'prior_source_snapshot_sha256':sha(prior/'sources.tar.gz'),
            'scope':'new formal scheduling, bookkeeping, pause/recovery and explicit gate dispatch only',
            'new_model_calls':0}


def formal_runtime_environment():
    from pathlib import Path
    from importlib.metadata import version
    model=Path('/home/lglsj/CanvasRCA/models/Qwen3.8-27B');old=read(RESULTS/'model_identity.json')
    for name,expected in old['checkpoint_files'].items():
        st=(model/name).stat()
        if st.st_size!=expected['bytes'] or st.st_mtime_ns!=expected['mtime_ns']:
            raise ValueError('Checkpoint stat changed; explicit weight audit required')
    if any(sha(model/name)!=value for name,value in old['configs'].items()):raise ValueError('Model/processor config changed')
    if any(version(name)!=old[name] for name in ('torch','transformers')):raise ValueError('Qualified runtime version changed')
    # No checkpoint bulk hashing, tensor allocation or inference during readiness.
    return {'status':'passed','weights':'18 original shard stats','model_fingerprint':old['generation_fingerprint']}


def seal_formal_readiness():
    import xml.etree.ElementTree as ET
    from .exps import formal_prior_calls
    if (RQ/'configs/activation.json').exists():raise ValueError('Deployment-only work must not activate formal execution')
    receipt=read(RESULTS/'qualification_complete.json')
    if receipt['status']!='passed':raise ValueError('CPU qualification absent')
    cases=ET.parse(RESULTS/'formal_runner_cpu.xml').getroot().findall('.//testcase')
    required={'test_formal_power_loss_boundaries','test_formal_pause_drain_and_fast_phase_resume',
              'test_formal_known_failure_blocks_automatic_retry','test_formal_frozen_queue_and_budget',
              'test_formal_activation_fail_closed','test_formal_real_cold_resume'}
    if not required<={c.attrib['name'] for c in cases} or any(any(c.find(t) is not None for t in ('failure','error','skipped')) for c in cases):
        raise ValueError('Affected formal regression is incomplete')
    compatibility=formal_generation_compatibility();write(RESULTS/'formal_generation_compatibility.json',compatibility)
    config=read(RQ/'configs/formal_v1.json');queue=read(RESULTS/'queue.json')
    if config['items']!=queue['items'] or config['queue_sha256']!=sha(RESULTS/'queue.json'):
        raise ValueError('Formal queue changed')
    if config['prior_smoke_calls']!=formal_prior_calls():raise ValueError('Prior call accounting changed')
    result={'schema':'RQ42FormalReadinessV1','status':'ready','formal_started':False,'execution_authorized':False,
            'positions':queue['positions'],'unique_new_calls':queue['unique_calls'],'exact_references':8,
            'formal_attempt_cap':config['formal_attempt_cap'],'infrastructure_reserve':142,
            'prior_smoke_calls':config['prior_smoke_calls']['attempts'],
            'combined_call_ceiling':config['combined_call_ceiling'],'affected_cpu_tests':len(cases),
            'new_GPU_calls':0,'runtime':formal_runtime_environment(),
            'bindings':{'qualification_complete.json':sha(RESULTS/'qualification_complete.json'),
                        'gpu_smoke_complete.json':sha(RESULTS/'gpu_smoke_complete.json'),
                        'formal_generation_compatibility.json':sha(RESULTS/'formal_generation_compatibility.json'),
                        'formal_runner_cpu.xml':sha(RESULTS/'formal_runner_cpu.xml'),'queue.json':sha(RESULTS/'queue.json')},
            'formal_registration_sha256':sha(RQ/'configs/formal_v1.json'),
            'resumption':'trust atomic completed markers; replay only interrupted attempts without a complete durable reply'}
    write(RESULTS/'formal_readiness.json',result);return formal_readiness()


def formal_readiness():
    """Read-only launch qualification, independent from authorization to launch."""
    from .exps import formal_prior_calls
    path=RESULTS/'formal_readiness.json'
    if not path.exists():raise RuntimeError('Formal runner qualification has not passed')
    ready=read(path)
    if ready.get('status')!='ready':raise RuntimeError('Formal runner is not ready')
    for name,checksum in ready['bindings'].items():
        if sha(RESULTS/name)!=checksum:raise RuntimeError('Stale formal qualification: '+name)
    if sha(RQ/'configs/formal_v1.json')!=ready['formal_registration_sha256']:raise RuntimeError('Formal registration changed')
    receipt=read(RESULTS/'qualification_complete.json')
    if any(sha(ROOT/p)!=value for p,value in receipt['source_hashes'].items()):raise RuntimeError('Qualified formal source changed')
    if any(sha(RESULTS/p)!=value for p,value in receipt['check_hashes'].items()):raise RuntimeError('Qualified CPU artifact changed')
    if formal_prior_calls()!=read(RQ/'configs/formal_v1.json')['prior_smoke_calls']:raise RuntimeError('Call accounting changed')
    formal_runtime_environment()
    return ready
