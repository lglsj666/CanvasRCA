"""RQ4.10 static, future qualification, analysis and readable retention."""
import ast,json,os
from pathlib import Path
from functools import lru_cache
from .utils import ROOT,RQ,RESULTS,MODEL,read,save,digest,stable,ARMS,protocol,roster
@lru_cache(maxsize=1)
def generation_recipe():
    names=['config.json','generation_config.json','preprocessor_config.json','tokenizer_config.json','tokenizer.json','model.safetensors.index.json']
    return {'model':str(MODEL),'metadata':{n:digest(MODEL/n) for n in names if (MODEL/n).exists()},
        'weights':{p.name:[p.stat().st_size,p.stat().st_mtime_ns] for p in sorted(MODEL.glob('*.safetensors'))},
        'engine':read(RQ/'configs/execution_v1.json')['engine'],'temperature':1.,'top_p':.95,'top_k':-1,
        'thinking':False,'ranking':'greedy five-ID array; sampled explanation','seed':42,
        'operator':'ContextOperatorPlanV1; D original; O-only fusion; native gate/MRoPE/linear state unchanged',
        'generation_code':generation_code_identity()}


def retention_viewer(base,project,entries):
    """One small browser, with references rather than copied prompts or pictures."""
    folder=base/'conversations';folder.mkdir(parents=True,exist_ok=True)
    save(folder/'index.json',{'schema':'RQ410ConversationIndexV1','records':entries})
    relative=json.dumps(os.path.relpath(project,folder)+'/')
    page='''<!doctype html><html lang="en"><meta charset="utf-8">
<title>RQ4.10 conversations</title>
<style>body{font:15px system-ui;margin:24px;max-width:1500px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f4f4;padding:12px}img{max-width:100%;height:auto}button{margin:3px;text-align:left}input{width:90%;padding:8px}details{margin:12px 0}</style>
<h1>RQ4.10 complete conversations</h1>
<p>Exact prompts, original dashboard PNGs, raw answers, scores and collected attention. Files are shared by reference; this page contains no copied diagnostic inputs.</p>
<p id="notice"></p><input id="search" placeholder="Filter by incident, arm, task, or scope"><div id="list"></div><main id="conversation"></main>
<script>
const project=new URL(PROJECT,location.href);let records=[];
const el=(tag,text)=>{const x=document.createElement(tag);if(text!==undefined)x.textContent=text;return x};
async function get(url){const r=await fetch(url);if(!r.ok)throw Error(r.status+' '+url);return await r.json()}
async function show(row){
 const main=document.getElementById('conversation');main.replaceChildren(el('p','Loading...'));
 const record=await get(new URL(row.record,project)),request=await get(new URL(record.request_path,project));
 main.replaceChildren(el('h2',row.scope+' / '+row.key),el('h3','Exact model prompt'),el('pre',request.prompt));
 const raw=el('a','Open exact input JSON');raw.href=new URL(record.request_path,project);raw.target='_blank';main.append(raw,el('h3','Model-visible images'));
 for(const path of request.images){const a=el('a');a.href=new URL(path,project);a.target='_blank';const im=el('img');im.src=a.href;im.alt=path;a.append(im);main.append(a)}
 main.append(el('h3','Exact raw model response'),el('pre',record.raw));
 const details=el('details');details.append(el('summary','Scores, costs, token operations and audit metadata'),el('pre',JSON.stringify(record,null,2)));main.append(details);
 if(record.usage.attention_requested){const a=el('a','Open actual collected attention');a.href=new URL(row.scope+'/attention/'+record.usage.attention_record_key+'.json',new URL('../',location.href));a.target='_blank';main.append(a)}
 location.hash=new URLSearchParams({scope:row.scope,key:row.key}).toString();
}
function list(){const q=document.getElementById('search').value.toLowerCase(),matches=records.filter(r=>(r.scope+' '+r.key+' '+r.dataset+' '+r.task).toLowerCase().includes(q)),box=document.getElementById('list');box.replaceChildren(el('p',matches.length+' matches; first 100 shown'));for(const row of matches.slice(0,100)){const b=el('button',row.scope+' | '+row.key);b.onclick=()=>show(row).catch(fail);box.append(b,el('br'))}}
function fail(e){document.getElementById('notice').textContent=String(e)+'. Open this page through a local HTTP server; see README.md.'}
get(new URL('index.json',location.href)).then(x=>{records=x.records;list();const h=new URLSearchParams(location.hash.slice(1)),row=records.find(r=>r.key===h.get('key')&&r.scope===h.get('scope'));if(row)return show(row)}).catch(fail);
document.getElementById('search').addEventListener('input',list);
</script></html>'''.replace('PROJECT',relative)
    (folder/'index.html').write_text(page,encoding='utf-8')
    return folder/'index.html'


def retained_attention_accounting(base,project,records,calls):
    """Conservative accounting of summaries, required mapping fields and code.

    Token-operation payloads and displayed evidence are ordinary inputs. For
    attention, count the fields actually read by attention_regions and the
    actual transport mappings, without charging identical aliases three times.
    The aliases remain byte-for-byte intact in the canonical input records.
    """
    seen=set();summary_bytes=0;request_maps=set();mapping_bytes=0;positions=0;equal_aliases=0;different_variants=0
    def size_files(paths):
        total=0
        for p in paths:
            st=p.stat();key=(st.st_dev,st.st_ino)
            if key not in seen:seen.add(key);total+=st.st_size
        return total
    def encoded(value):return len(json.dumps(value,ensure_ascii=False,indent=2).encode())
    summary_bytes=size_files(p for p in base.rglob('*') if p.is_file() and 'attention' in p.relative_to(base).parts)
    for _,r in records:
        usage=r['usage']
        if not usage.get('attention_requested'):continue
        positions+=1;path=Path(r['request_path']);path=path if path.is_absolute() else project/path;req=read(path)
        active=usage.get('actual_selection',{})
        if path not in request_maps:
            request_maps.add(path);geometry=[]
            if 'retained_by_image' in req:
                actual=active['retained_by_image']
                for variant in (req['retained_by_image'],[o['retained'] for o in req['operators']]):
                    if variant==actual:equal_aliases+=1
                    else:mapping_bytes+=encoded(variant);different_variants+=1
            for g in req.get('geometry',[]):
                item={k:g[k] for k in ('width','height','header_height') if k in g}
                item['panels']=[{k:p[k] for k in ('box','card','index','component') if k in p} for p in g['panels']]
                geometry.append(item)
            mapping_bytes+=encoded({'geometry':geometry,'grid_thw':req.get('grid_thw',[]),
                'operators':[{k:o[k] for k in ('anchors','evidence','grid','image_tokens') if k in o} for o in req.get('operators',[])]})
        mapping_bytes+=encoded({k:usage[k] for k in ('actual_selection','sink_audit') if k in usage})
    # Include entire frozen code/queue and viewing indexes as an upper bound,
    # although most of that material is shared with ordinary experiment audit.
    definitions=size_files(p for folder in (base/'frozen',base/'audits/storage_source',base/'conversations')
        for p in folder.rglob('*') if p.is_file())
    analysis=base/'analysis/attention.json';analysis_bytes=size_files([analysis]) if analysis.exists() else 0
    total=summary_bytes+mapping_bytes+definitions+analysis_bytes
    report={'schema':'RQ410AttentionRetentionAccountingV1','status':'passed' if total<=100000*calls else 'blocked',
        'actual_completed_calls':calls,'attention_conversation_positions':positions,'summary_bytes':summary_bytes,
        'conservative_mapping_bytes':mapping_bytes,'definitions_and_indexes_bytes':definitions,
        'analysis_bytes':analysis_bytes,'conservative_total_bytes':total,'budget_bytes':100000*calls,
        'equal_selection_aliases_not_charged_twice':equal_aliases,'distinct_selection_variants_charged_separately':different_variants,
        'all_collected_measurements_preserved':True,
        'mapping_policy':'Count grid, panel boxes/IDs, A/E membership and actual per-record selections/sink audits. '
            'Exact input prompts plus frozen tokenizer/processor reconstruct text/image positions. '
            'Repeated equal selection fields alias the same mapping; full diagnostic text, DOM bindings and '
            'unrelated fusion groups remain retained as ordinary inputs/operators. Entire frozen sources and indexes are additionally charged.',
        'new_model_calls':0}
    save(base/'audits/attention_retention_accounting.json',report)
    if report['status']!='passed':raise RuntimeError('Collected attention and mapping budget exceeded; no deletion performed')
    return report


def finalize_retention(base=None,project=None,apply=True):
    """Verify canonical conversations first; prune only verified non-dependencies.

    Explicit paths support isolated destructive-operation regression fixtures.
    Frozen inputs, answers, scores and source snapshots are never rewritten.
    """
    import re,shutil,sqlite3,time
    from collections import defaultdict
    from concurrent.futures import ThreadPoolExecutor
    from .utils import cache_lock
    base=Path(base or RESULTS).resolve();project=Path(project or ROOT).resolve()
    if not base.is_relative_to(project):raise ValueError('Retention root escapes the project')
    phase=read(base/'formal/phase_complete.json')
    if phase.get('status')!='complete':raise RuntimeError('Formal phase is incomplete')
    with cache_lock(base/'finalize.lock'):
        previous=base/'finalization.json'
        if previous.exists() and read(previous).get('status')=='passed' and read(previous).get('schema')=='RQ410FinalRetentionV3':
            report=read(previous)
            if digest(base/'retained_manifest.json')!=report['manifest_sha256']:raise ValueError('Retention manifest changed')
            return report
        def files(folder):return sorted(p for p in folder.rglob('*') if p.is_file()) if folder.exists() else []
        def size(paths):
            seen=set();total=0
            for p in paths:
                st=p.stat();key=(st.st_dev,st.st_ino)
                if key not in seen:seen.add(key);total+=st.st_size
            return total
        baseline_path=base/'audits/storage_baseline.json'
        if baseline_path.exists():before=read(baseline_path)['before_bytes']
        else:
            before=size(files(base))
            save(baseline_path,{'before_bytes':before,'phase_fingerprint':phase.get('fingerprint')})
        objects=base/'objects';objects.mkdir(exist_ok=True)
        scopes=sorted(p.parent for p in base.glob('*/completed') if p.is_dir())
        records=[];entries=[];known=set();used_images=set();by_prepared=defaultdict(list);checks={}
        def resolve(name):
            p=Path(name);p=p if p.is_absolute() else project/p;p=p.resolve()
            if not p.is_relative_to(base):raise ValueError('Retained dependency escapes experiment: '+str(p))
            return p
        def verify(p,expected=None):
            p=Path(p)
            if not p.is_file():raise ValueError('Missing retained dependency: '+str(p))
            if p not in checks:checks[p]=digest(p)
            if expected is not None and checks[p]!=expected:raise ValueError('Retained hash mismatch: '+str(p))
            return checks[p]
        for folder in scopes:
            for p in sorted((folder/'completed').glob('*.json')):
                r=read(p);reqpath=resolve(r['request_path']);verify(reqpath,r['request_sha256']);req=read(reqpath)
                if not isinstance(r['raw'],str):raise ValueError('Raw model output is missing')
                if len(req['images'])!=len(req['image_sha256']):raise ValueError('Image accounting differs')
                for image,sha in zip(req['images'],req['image_sha256'],strict=True):
                    path=resolve(image);verify(path,sha);used_images.add(path)
                if r['reference'] and not (folder/'completed'/(r['reference']+'.json')).exists():raise ValueError('Broken exact-result reference')
                if r['usage'].get('attention_requested'):
                    key=r['usage']['attention_record_key'];a=folder/'attention'/(key+'.json')
                    verify(a)
                    if a.stat().st_size>65536:raise ValueError('Collected attention exceeds its per-call budget')
                    read(a)  # Required measurement JSON must be valid, never errors="ignore".
                records.append((p,r));known.add((r['generation_identity'],r['raw']));verify(p)
                prepared=r['item'].get('request_path')
                if prepared:by_prepared[prepared].append({'record':str(p.relative_to(project)),'actual_request':r['request_path']})
                entries.append({'scope':folder.name,'key':r['item']['key'],'arm':r['item']['arm'],
                    'dataset':r['item']['dataset'],'task':r['item']['task'],'record':str(p.relative_to(project))})
        formal_count=sum(p.parent.parent.name=='formal' for p,r in records)
        if formal_count!=phase['positions'] or phase.get('expected',formal_count)!=formal_count:raise ValueError('Completion marker and committed conversations differ')
        calls=sum(r['reference'] is None for p,r in records)
        if not calls:raise ValueError('No completed actual calls for the storage denominator')
        ledger=base/'calls.sqlite'
        if ledger.exists():
            with sqlite3.connect(ledger.as_uri()+'?mode=ro',uri=True) as db:
                if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Call ledger is corrupt')
                count=db.execute("SELECT COUNT(*) FROM attempts WHERE state='responded'").fetchone()[0]
                if count!=calls:raise ValueError('Ledger and retained actual-call denominators differ')
        # Preserve provenance/role support once; discard duplicated prepared requests
        # and browser HTML exports, since exact actual requests and PNGs exist above.
        def store(value):
            content=(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
            sha=__import__('hashlib').sha256(content).hexdigest();p=objects/(sha+'.json')
            if not p.exists():
                tmp=p.with_suffix('.retention.tmp');tmp.write_bytes(content);os.replace(tmp,p)
            verify(p,sha)
            if read(p)!=value:raise ValueError('Audit normalization changed information')
            return {'path':str(p.relative_to(project)),'sha256':sha}
        image_audits={};prepared_index={};prep=base/'inputs'
        for p in files(prep):
            if re.fullmatch(r'.+\.json\.\d+\.\d+\.tmp',p.name):
                committed=p.with_name(p.name.split('.json.')[0]+'.json')
                if not committed.is_file() or p in checks:raise ValueError('Unclassified or required preparation temporary file')
                prepared_index[str(p.relative_to(project))]={'original_sha256':digest(p),
                    'disposition':'unsubmitted interrupted atomic preparation; all actual conversation inputs verified separately'}
                continue
            if p.suffix!='.json':raise ValueError('Unclassified preparation artifact: '+str(p))
            value=read(p);relative=p.relative_to(prep)
            if p.name=='images.json':
                for arm,view in value.items():
                    image=resolve(view['path'])
                    if image not in used_images:continue
                    audit={'image':str(image.relative_to(project)),'image_sha256':verify(image),
                        'html_source_sha256':view.get('html_sha256'),'html_retained':False}
                    known_fields={'path','sha256','html','html_sha256','render_folder','support','provenance','geometry',
                        'readability','operation_audit','grid','processed','operator','retained','preparation_timing','annotation_contract'}
                    if set(view)-known_fields:raise ValueError('Unclassified image preparation metadata')
                    for field in ('support','provenance','geometry','readability','operation_audit','grid','processed',
                                  'operator','retained','preparation_timing','annotation_contract'):
                        if field in view:audit[field]=store(view[field])
                    image_audits[str(relative.parent)+'/'+arm]=audit
            elif isinstance(value,dict) and {'prompt','messages','identity','images'}<=set(value):
                prepared_index[str(p.relative_to(project))]={'original_sha256':digest(p),'prepared_identity':value['identity'],
                    'actual_conversations':by_prepared.get(str(p.relative_to(project)),[]),
                    'disposition':'actual inputs are in canonical conversation requests; unused preparation is discarded'}
            else:
                target=base/'audits/cases'/relative;target.parent.mkdir(parents=True,exist_ok=True)
                if not target.exists():os.link(p,target)
                if verify(target)!=digest(p):raise ValueError('Provenance transfer differs')
        if prep.exists():
            save(base/'audits/image_support.json',{'schema':'RQ410SharedImageSupportV1','views':image_audits})
            save(base/'audits/prepared_input_index.json',{'schema':'RQ410PreparedToActualInputV1','inputs':prepared_index})
        if base==RESULTS.resolve() and not (base/'evaluation/roster.json').exists():
            save(base/'evaluation/roster.json',{'schema':'RQ410RetainedRosterV1','cases':roster(),'model_visible':False})
        viewer=retention_viewer(base,project,entries)
        attention_accounting=retained_attention_accounting(base,project,records,calls)
        # This profiler output is not a model input, response or attention record.
        # Its invalid UTF-8 caused the original overbroad JSON scan to abort.
        discard={base/'smoke_performance_v4/cpu_stacks.json',base/'preparation_json_formatting.json'}
        for folder in scopes:
            for p in (folder/'partial').glob('*.json'):
                r=read(p)
                if (r['identity'],r['raw']) in known:discard.add(p)
        def removable(p):
            return p.is_relative_to(base/'cache') or p.is_relative_to(prep) or p in discard
        # Only retained roots participate in reachability. Binary profiler output
        # is never passed off as text; malformed REQUIRED JSON still blocks deletion.
        pattern=re.compile(r'(?<![a-f0-9])[a-f0-9]{64}\.[A-Za-z0-9]+')
        marked=set();pending=[]
        def scan(p):
            try:text=p.read_text(encoding='utf-8')
            except UnicodeDecodeError as exc:raise ValueError('Required text is not UTF-8: '+str(p)) from exc
            if p.suffix=='.json':json.loads(text)
            for name in pattern.findall(text):
                path=objects/name
                if path.is_file() and path not in marked:marked.add(path);pending.append(path)
        summaries={base/'retained_manifest.json',previous,base/'retention.json'}
        roots=[p for p in files(base) if not removable(p) and not p.is_relative_to(objects) and p not in summaries]
        for p in roots:
            if p.suffix in {'.json','.html','.md','.py','.sh','.yaml','.yml','.txt','.csv'}:scan(p)
        for p in checks:
            if p.is_relative_to(objects) and p not in marked:marked.add(p);pending.append(p)
        while pending:
            p=pending.pop();verify(p,p.stem)
            if p.suffix in {'.json','.html','.md','.py','.ts','.tsx','.mjs','.css','.sh','.yaml','.yml'}:scan(p)
        # No active dependency may be inside any directory about to disappear.
        if any(removable(p) for p in checks):raise ValueError('Cleanup would remove a required input or measurement')
        all_paths=files(base)
        doomed=[p for p in all_paths if removable(p) or p.is_relative_to(objects) and p not in marked]
        doomed_set=set(doomed)
        retained=[p for p in all_paths if p not in doomed_set and p not in summaries]
        with ThreadPoolExecutor(max_workers=8) as pool:
            hashes=list(pool.map(digest,retained))
        for p,sha in zip(retained,hashes):
            if p in checks and sha!=checks[p]:raise ValueError('A writer changed a verified dependency: '+str(p))
        manifest={'schema':'RQ410ReadableRetentionManifestV1','phase_fingerprint':phase.get('fingerprint'),
            'conversations':len(records),'actual_completed_calls':calls,'raw_responses_and_requests_unchanged':True,
            'files':{str(p.relative_to(base)):{'sha256':sha,'bytes':p.stat().st_size} for p,sha in zip(retained,hashes)}}
        manifest_path=base/'retained_manifest.json';save(manifest_path,manifest)
        if not apply:return {'status':'verified_not_deleted','before_bytes':before,'planned_retained_bytes':size(retained),
            'planned_removable_bytes':size(doomed),'removable_files':len(doomed),'conversations':len(records),
            'actual_completed_calls':calls,'viewer':str(viewer),'new_model_calls':0}
        # The complete retained graph is verified and durably indexed BEFORE unlink.
        for folder in (base/'cache',prep):
            if folder.exists():shutil.rmtree(folder)
        for p in doomed:
            if p.exists():p.unlink()
        # Deduplicate immutable byte-identical snapshots/measurements, not live logs.
        immutable=[p for p in retained if p.exists() and (p.is_relative_to(objects) or p.is_relative_to(base/'frozen')
                   or 'completed' in p.parts or 'attention' in p.parts)]
        canonical={};deduplicated=0
        for p in immutable:
            info=manifest['files'][str(p.relative_to(base))];key=(info['sha256'],info['bytes']);prior=canonical.get(key)
            if prior is None:canonical[key]=p;continue
            if not os.path.samefile(prior,p):
                tmp=p.with_suffix(p.suffix+'.dedup.tmp');os.link(prior,tmp);os.replace(tmp,p);deduplicated+=1
        # Verify all final bytes again, including every copied provenance sidecar.
        with ThreadPoolExecutor(max_workers=8) as pool:after_hashes=list(pool.map(digest,retained))
        if after_hashes!=hashes:raise ValueError('A retained file changed during cleanup')
        attention_paths=[p for p in files(base) if 'attention' in p.relative_to(base).parts]
        attention=max(size(attention_paths),attention_accounting['conservative_total_bytes']);report={'schema':'RQ410FinalRetentionV3','status':'pending',
            'completed_positions':formal_count,'completed_actual_calls':calls,'retained_conversations':len(records),
            'before_bytes':before,'attention_bytes':attention,'budget_bytes':2500000*calls,
            'attention_summary_bytes':size(attention_paths),'attention_mapping_accounting':'audits/attention_retention_accounting.json',
            'attention_budget_bytes':100000*calls,'verified_objects':len(marked),'verified_files':len(retained),
            'deduplicated_files':deduplicated,'directly_readable':True,'cache_drained':True,
            'canonical_conversations':'completed record -> shared exact request -> shared model-visible PNGs',
            'viewer':str(viewer.relative_to(project)),'manifest_sha256':digest(manifest_path),'new_model_calls':0}
        for _ in range(8):
            save(previous,report);total=size(files(base));status='passed' if total<=report['budget_bytes'] and attention<=report['attention_budget_bytes'] else 'blocked'
            if report.get('retained_bytes')==total and report['status']==status:break
            report.update(retained_bytes=total,status=status,bytes_per_call=total/calls,released_bytes=before-total)
        if report['status']!='passed':raise RuntimeError('All records preserved; retained storage budget still exceeded')
        return report



def source_files():
    files=[]
    for folder in (RQ/'src',RQ/'configs',ROOT/'src/renderer',ROOT/'src/scorer',ROOT/'RQs/RQ4_1/src',ROOT/'RQs/RQ4_3/src'):
        files.extend(p for p in folder.rglob('*') if p.is_file() and p.suffix in {'.py','.json','.ts','.tsx','.css','.mjs'} and not set(p.parts)&{'node_modules','__pycache__','dist'})
    files.extend(ROOT/p for p in protocol()['global_configs']);files.append(ROOT/'src/vlmrca/vlm/passive_summary.py')
    return sorted(set(files))


def execution_fingerprint():return stable({str(p.relative_to(ROOT)):digest(p) for p in source_files()})

def input_fingerprint():return execution_fingerprint()


def generation_code_identity():
    names={'make_request','rebuild_request','VLLMWorkerExtension','VLLMSolvers','encode_operators','apply_actual_selection','cached_kv','torch_redistribute','sink_kernels','fast_sink_delta','fast_sink_correction','install_attention_layer','fusion_means','grouped_probabilities','vllm_prompt_packet','multimodal_gather','make_ranking_processor','ranking_segment','assign_feature_groups','computation_identity'}
    nodes={}
    for filename in ('exps.py','utils.py'):
        for node in ast.parse((RQ/'src'/filename).read_text()).body:
            if getattr(node,'name',None) in names:nodes[filename+':'+node.name]=ast.dump(node,include_attributes=False)
    return stable(nodes)


def static_check():
    """No imports of tests/torch/transformers/renderer; no dataset preparation."""
    import symtable,builtins,subprocess
    modules=sorted((RQ/'src').glob('*.py'));expected={'__init__.py','main.py','utils.py','exps.py','gates.py','tests.py'}
    if {p.name for p in modules}!=expected:raise ValueError('Five functional modules required')
    lines=0;imports=[]
    for p in modules+[ROOT/'src/renderer/operations/domain_views.py']:
        text=p.read_text();tree=ast.parse(text);compile(tree,str(p),'exec')
        if p in modules:lines+=sum(bool(x.strip()) and not x.lstrip().startswith('#') for x in text.splitlines())
        for n in ast.walk(tree):
            if isinstance(n,ast.ImportFrom) and n.module:
                imports.append(n.module)
                if ('scorer' in n.module or 'scoring' in n.module) and n.module.split('.')[0]!='scorer':raise ValueError('RCA scorer outside central scorer')
                if n.module.startswith('RQs.') and n.module not in {'RQs.RQ4_1.src.utils','RQs.RQ4_3.src.utils'}:raise ValueError('Unfrozen experiment dependency '+n.module)
        table=symtable.symtable(text,str(p),'exec');known={x.get_name() for x in table.get_symbols() if x.is_imported() or x.is_assigned() or x.is_namespace()}|set(dir(builtins))|{'__file__','__name__','__package__'}
        def visit(t):
            for x in t.get_symbols():
                if x.is_global() and x.is_referenced() and x.get_name() not in known:raise ValueError(f'Unbound {x.get_name()} at {p}:{t.get_name()}')
            for child in t.get_children():visit(child)
        visit(table)
    if lines>7500:raise ValueError('Functional source line budget')
    cfg=protocol();run=read(RQ/'configs/execution_v1.json')
    if len(ARMS)!=20 or len(set(ARMS))!=20:raise ValueError('Twenty new arms required')
    if sum(cfg['formal_call_components'].values())!=5480 or cfg['formal_calls']+sum(cfg['smoke_scopes'].values())+cfg['infrastructure_recovery_calls']!=5700:raise ValueError('5700-call accounting differs')
    if cfg['total_call_limit']!=5700 or len(cfg['qa_arms'])!=10 or len(cfg['nominees'])!=3:raise ValueError('Scope mismatch')
    if cfg['canvas']!=[4096,4096] or cfg['card_limit']!=28 or cfg['context']!=40960:raise ValueError('Input policy differs')
    if any(run[k] for k in ('cpu_enabled','gpu_smoke_enabled','formal_enabled')):raise ValueError('Runtime defaults must remain off')
    if run['engine']['worker_extension_cls']!='RQs.RQ4_10.src.exps.VLLMWorkerExtension' or run['cpu_workers']!=8 or run['engine']['gpu_memory_utilization']!=.8:raise ValueError('Runtime registration mismatch')
    protect=read(RQ/'configs/protected_sources.json')
    for name,sha in protect['files'].items():
        if name not in protect['additive_registry_files'] and digest(ROOT/name)!=sha:raise ValueError('Historical source changed: '+name)
    if len(list((RQ/'descriptions').glob('*.md')))!=3:raise ValueError('Exactly three description files required')
    if sum(x['id']=='domain_view' for x in read(ROOT/'src/renderer/configs/operations.json')['operations'])!=1:raise ValueError('Renderer operation registration')
    node=ROOT/'build/renderer_tooling/node-v24.20.0-linux-x64/bin/node'
    proc=subprocess.run([str(node),'node_modules/typescript/bin/tsc','--noEmit'],cwd=ROOT/'src/renderer/web',capture_output=True,text=True)
    if proc.returncode:raise ValueError('TypeScript: '+proc.stdout+proc.stderr)
    report={'status':'passed','fingerprint':execution_fingerprint(),'functional_lines':lines,'new_arms':20,'formal_positions_max':5480,
        'total_calls_max':5700,'new_calls':0,'static_only':True,'runtime_qualified':False,
        'checks':['Python AST/compile/name resolution','TypeScript noEmit','registration/budget/default-off gates','central scorer imports','protected historical source hashes','five modules/line budget'],
        'not_run':['unit tests','CPU regression','render/browser','processor token counts','GPU features','GPU smoke','formal inference']}
    save(RQ/'findings/static_check.json',report);return report


def require_authorization(scope):
    path=RESULTS/'authorization'/(scope+'.json')
    if not path.exists():raise PermissionError('No separately issued authorization for '+scope)
    auth=read(path)
    if auth.get('authorized') is not True or auth.get('fingerprint')!=execution_fingerprint():raise PermissionError('Authorization does not match current source')
    return auth


def require_check(stage):
    path=RQ/'findings/static_check.json' if stage=='static' else RESULTS/'qualification'/(stage+'.json')
    report=read(path)
    if report.get('status')!='passed' or report.get('fingerprint')!=execution_fingerprint():raise RuntimeError('Qualification missing/stale: '+stage)
    return report


def require_execution(scope):
    if scope not in {'formal',*protocol()['smoke_scopes']}:raise ValueError('Unregistered GPU scope')
    require_authorization(scope)
    for stage in ('static','unit','cpu','qa','runtime','visual'):require_check(stage)
    queue=read(RESULTS/'frozen'/(scope+'.json'))
    if queue['fingerprint']!=execution_fingerprint() or queue['sha256']!=stable(queue['items']):raise RuntimeError('Queue/source binding changed')
    if scope=='formal':
        for name in protocol()['smoke_scopes']:
            review=read(RESULTS/name/'review.json')
            if review.get('status')!='passed' or review.get('fingerprint')!=execution_fingerprint():raise RuntimeError('Missing current smoke review '+name)
    return queue


def audit_case(row,report,requests,views,domain):
    """Future full CPU case audit, separate from static registration checks."""
    from PIL import Image
    if set(requests)!=set(ARMS):raise ValueError('Arm coverage')
    for arm,req in requests.items():
        if req['input_tokens']+8192>40960 or sum(map(len,req['retained_by_image']))>16384:raise ValueError('RCA capacity failed')
        if req['task']!='RCA':raise ValueError('Wrong task in primary matrix')
        if arm.startswith('H_'):
            if not req['hybrid']:raise ValueError('Hybrid silently converted to pure vision')
        elif req['hybrid'] or req.get('diagnostic_text'):raise ValueError('Pure visual contains diagnostic text')
        for path in req['images']:
            with Image.open(ROOT/path) as im:
                if im.size!=(4096,4096):raise ValueError('Fixed canvas violated')
        for op,geom in zip(req['operators'],req['geometry'],strict=True):
            if len(geom['panels'])>28:raise ValueError('Card limit')
            if op['retained']!=sorted(set(op['retained'])):raise ValueError('Duplicate/unordered positions')
            d=set(op['anchors'])|set(op['evidence'])
            if arm!='P_LENGTH_CONTROL' and not d<=set(op['retained']):raise ValueError('D lost')
            if op['operator']=='outside_mean':
                flat=[i for g in op['groups'] for i in g['members']]
                if len(flat)!=len(set(flat)) or set(flat)!=set(op['outside']) or set(flat)&d:raise ValueError('Fusion outside partition invalid')
    for carrier in ('V','H'):
        glyph=requests[carrier+'_SAMPLE_GLYPH'];mark=requests[carrier+'_SAMPLE_MARKLESS']
        if glyph['retained_by_image']!=mark['retained_by_image'] or glyph['grid_thw']!=mark['grid_thw']:raise ValueError('Markless changes token positions')
        exact=requests['V_EXACT_DOMAIN'] if carrier=='V' else None
        if exact and exact['retained_by_image']!=glyph['retained_by_image']:raise ValueError('EXACT/GLYPH changes positions')
    aliases={}
    for arm,req in requests.items():aliases.setdefault(req['identity'],[]).append(arm)
    result={'status':'passed','id':row['id'],'fingerprint':execution_fingerprint(),'exact_request_groups':list(aliases.values()),
        'outside_fraction':len(domain['outside'])/domain['image_tokens'],'anchor_fraction':len(domain['anchors'])/len(domain['domain']),
        'cpu_model_calls':0,'scientific_blocks':report['blocks']}
    save(RESULTS/'inputs'/row['id']/'audit.json',result);return result


def prepare_evaluation():
    contexts={};idx=read(HISTORY_PATH()/'evaluation/index.json')
    for row in roster():
        info=idx['contexts'][row['id']];p=HISTORY_PATH()/info['path']
        if not p.resolve().is_relative_to((HISTORY_PATH()/'evaluation').resolve()) or digest(p)!=info['sha256']:raise ValueError('Private scoring provenance mismatch')
        target=RESULTS/'evaluation/contexts'/(row['id']+'.json');save(target,read(p));contexts[row['id']]={'path':str(target.relative_to(RESULTS)),'sha256':digest(target)}
    save(RESULTS/'evaluation/index.json',{'contexts':contexts,'model_visible':False})
    save(RESULTS/'evaluation/roster.json',{'cases':roster(),'exposed':True});return contexts


def HISTORY_PATH():
    from .utils import HISTORY
    return HISTORY


def finish_cpu():
    from .utils import subset
    require_authorization('cpu');require_check('unit');expected={r['id'] for r in subset(roster(),10,protocol()['qa_salt'])}|set(protocol()['smoke_ids']);reports=[];qas=[]
    for row in roster():
        p=RESULTS/'inputs'/row['id'];r=read(p/'complete.json')
        if r['status']!='passed' or r['fingerprint']!=input_fingerprint():raise RuntimeError('CPU case blocked/stale: '+row['id'])
        reports.append(r)
        if row['id'] in expected:
            q=read(p/'qa_complete.json')
            if q['status']!='passed' or not q['one_question_per_call']:raise ValueError('QA contract failed')
            for path in q['requests']:
                req=read(ROOT/path)
                if len(req['qa_items'])!=1 or req['task']!='QA':raise ValueError('One question per request required')
            qas.append(q)
    # Public strata thresholds are frozen before any new answers exist.
    features=[read(RESULTS/'inputs'/r['id']/'audit.json') for r in roster()]
    import statistics
    strata={k:statistics.median(r[k] for r in features) for k in ('outside_fraction','anchor_fraction')}
    save(RESULTS/'frozen/public_strata.json',{'thresholds':strata,'cases':features,'uses_outcomes':False})
    report={'status':'passed','fingerprint':execution_fingerprint(),'cases':len(reports),'new_model_calls':0}
    save(RESULTS/'qualification/cpu.json',report)
    qa={'status':'passed','fingerprint':execution_fingerprint(),'cases':len(qas),'controls':[x for q in qas for x in q['controls']],'new_model_calls':0}
    save(RESULTS/'qualification/qa.json',qa);return report


def freeze(scope):
    from .exps import build_queue
    require_authorization('cpu')
    for s in ('static','unit','cpu','qa','runtime','visual'):require_check(s)
    items=build_queue(scope);folder=RESULTS/'frozen';fp=execution_fingerprint();file=folder/(scope+'.json')
    queue={'schema':'RQ410FrozenQueueV1','items':items,'sha256':stable(items),'fingerprint':fp}
    if file.exists() and read(file)!=queue:raise ValueError('Cannot replace a frozen queue')
    for p in source_files():
        target=folder/'source'/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():target.write_bytes(p.read_bytes())
        if digest(target)!=digest(p):raise ValueError('Frozen dependency mismatch')
    save(file,queue);return {'scope':scope,'positions':len(items),'fingerprint':fp}


def status():
    return {'static':read(RQ/'findings/static_check.json') if (RQ/'findings/static_check.json').exists() else {'status':'not_run'},
        'qualifications':{p.stem:read(p).get('status') for p in (RESULTS/'qualification').glob('*.json')},
        'committed':{scope:len(list((RESULTS/scope/'completed').glob('*.json'))) for scope in ['formal',*protocol()['smoke_scopes']]}}


def accept_visual_review(path):
    require_authorization('cpu');review=read(path)
    if review.get('fingerprint')!=execution_fingerprint() or review.get('status')!='passed':raise ValueError('Visual review lacks current source binding')
    images=review.get('images',[])
    if not 1<=len(images)<=protocol()['manual_images_limit']:raise ValueError('Manual image budget')
    required={'aiops2022','aiops2025','aegislab','dense','long_names','marginal_markless'}
    if not required<={tag for r in images for tag in r.get('coverage',[])}:raise ValueError('Required finite visual review coverage missing')
    for r in images:
        if digest(ROOT/r['path'])!=r['sha256'] or r.get('readable') is not True:raise ValueError('Unreviewed/changed image')
    save(RESULTS/'qualification/visual.json',review);return review


def runtime_cpu_check():
    require_authorization('cpu');require_check('unit');require_check('cpu');prepare_evaluation()
    os.environ['CUDA_VISIBLE_DEVICES']=''
    from transformers import AutoProcessor
    from .utils import offline,vllm_prompt_packet,score_context,score_response
    from .exps import apply_actual_selection,build_queue
    offline();processor=AutoProcessor.from_pretrained(MODEL,local_files_only=True);checked=[]
    paths={i['request_path'] for s in protocol()['smoke_scopes'] for i in build_queue(s)}
    for path in sorted(paths):
        req=read(ROOT/path);req['attention']=True;packet=vllm_prompt_packet(req,processor);rebuilt=apply_actual_selection(packet,packet['operators'])
        if packet['keep']!=rebuilt['keep'] or packet['metadata']['positions']!=rebuilt['metadata']['positions']:raise ValueError('No-op transport changed MRoPE/token order')
        if len(rebuilt['metadata']['attention']['ids'])!=req['input_tokens']:raise ValueError('Text/image region mapping mismatch')
        checked.append({'request':path,'tokens':req['input_tokens']})
    for oid in protocol()['smoke_ids']:
        context=score_context(oid)
        invalid=score_response('invalid JSON',context)
        if invalid['standard']['metrics']['mrr']!=0:raise ValueError('Central invalid-answer scoring')
    report={'status':'passed','fingerprint':execution_fingerprint(),'requests':checked,'new_model_calls':0,'model_backend':'offline transport only'}
    save(RESULTS/'qualification/runtime.json',report);return report


def gpu_tensor_check():
    require_execution('smoke_operators')
    from .utils import redistribute_reference,smoke_deadline
    from .exps import fast_sink_delta,torch_redistribute,fusion_means
    import torch,numpy as np,time
    deadline=smoke_deadline(RESULTS/'smoke_operators',900);errors={}
    gen=torch.Generator(device='cuda').manual_seed(42)
    q=torch.randn((16,4,64),device='cuda',dtype=torch.bfloat16,generator=gen)
    k=torch.randn((16,2,64),device='cuda',dtype=torch.bfloat16,generator=gen);v=torch.randn(k.shape,device='cuda',dtype=torch.bfloat16,generator=gen)
    queries=torch.tensor([12,15],device='cuda');roles=torch.tensor([0,2,2,3,1,1]+[0]*10,device='cuda',dtype=torch.int32);order=torch.arange(16,device='cuda')
    from .exps import grouped_probabilities
    p=grouped_probabilities(q,k,queries)
    for arm in protocol()['sink']:
        expected,_=redistribute_reference(p.cpu().numpy(),[1,2,3,4,5],[1,2],[3],arm)
        effective,_,_=torch_redistribute(p,[1,2,3,4,5],[1,2],[3],arm)
        np.testing.assert_allclose(effective.cpu().numpy(),expected,atol=2e-6,rtol=2e-5)
        delta,_=fast_sink_delta(q,k,v,queries,roles,order,arm,protocol()['sink_policy'])
        ref=torch.einsum('htn,nhd->thd',effective-p,v.repeat_interleave(2,dim=1).float())
        torch.testing.assert_close(delta,ref,atol=3e-4,rtol=3e-3);errors[arm]=float((delta-ref).abs().max())
    if time.monotonic()>deadline:raise TimeoutError('Registered operator smoke window exhausted')
    report={'status':'passed','fingerprint':execution_fingerprint(),'errors':errors,'new_model_calls':0,'native_model_and_paged_decode':'covered by bounded operator calls'}
    save(RESULTS/'smoke_operators/gpu_tensor_check.json',report);return report


def review_smoke(scope):
    require_execution(scope);queue=read(RESULTS/'frozen'/(scope+'.json'));folder=RESULTS/scope;records=[]
    phase=read(folder/'phase_complete.json')
    if phase['status']!='complete':raise RuntimeError('Smoke not complete')
    for item in queue['items']:
        r=read(folder/'completed'/(item['key']+'.json'));req=read(ROOT/r['request_path'])
        if digest(ROOT/r['request_path'])!=r['request_sha256'] or r['generation_identity']!=req['identity']:raise ValueError('Committed smoke input changed')
        for p,sha in zip(req['images'],req['image_sha256'],strict=True):
            if digest(ROOT/p)!=sha:raise ValueError('Smoke actual image changed')
        if r['usage']['input_tokens']!=req['input_tokens'] or r['usage'].get('dtype')!='bfloat16':raise ValueError('Actual runtime differs')
        if item['task']=='QA':
            from .utils import score_qa
            if len(req['qa_items'])!=1 or score_qa(r['raw'],req['qa_items'])!=r['scores']:raise ValueError('QA grading mismatch')
            # A wrong model answer is valid. Review the contract, not accuracy.
            if not req['qa_items'][0]['solutions']:raise ValueError('Empty QA oracle')
        if item['attention']:
            a=folder/'attention'/(r['usage']['attention_record_key']+'.json')
            if not a.exists() or a.stat().st_size>65536 or len(read(a)['measurements'])!=8:raise ValueError('Incomplete attention')
        records.append(r)
    if scope=='smoke_operators':
        tensor=read(folder/'gpu_tensor_check.json')
        if tensor['status']!='passed' or tensor['fingerprint']!=execution_fingerprint():raise ValueError('Operator numerical check missing')
    # Independent human/automatic content review is bound to exact raw records.
    audit=read(folder/'artifact_review.json')
    hashes={r['item']['key']:digest(folder/'completed'/(r['item']['key']+'.json')) for r in records}
    if audit.get('status')!='passed' or audit.get('record_hashes')!=hashes:raise ValueError('Exact artifact review missing/stale')
    durations=[r['usage']['processor_model_seconds'] for r in records];speed=read(folder/'gpu_utilization.json') if (folder/'gpu_utilization.json').exists() else {}
    util=speed.get('inference_mean_percent');fast=all(t<=20 for t in durations) or util is not None and util>=82
    if not fast:raise RuntimeError('Measured speed gate not met (per-call <=20s or inference GPU mean >=82%)')
    result={'status':'passed','fingerprint':execution_fingerprint(),'calls':len(records),'mean_call_seconds':sum(durations)/len(durations),
        'inference_gpu_mean_percent':util,'calls_per_minute':None,
        'wrong_answers_are_not_implementation_failures':True}
    if records:
        span=max(r['usage']['invoke_finished_monotonic'] for r in records)-min(r['usage']['invoke_started_monotonic'] for r in records)
        result['calls_per_minute']=60*len(records)/span
    save(folder/'review.json',result);return result


def paired_family(pairs,index,rows,qa=False):
    import numpy as np
    from scipy.stats import wilcoxon
    from collections import defaultdict
    results={}
    for level in ('event_group','case'):
        tests=[]
        for pair in pairs:
            diffs=defaultdict(list);case_diffs=[];lo=hi=0.;historical=False
            for row in rows:
                vals=[]
                for arm in pair:
                    rec=index.get((row['id'],arm));historical=historical or bool(rec and rec.get('historical'))
                    if rec is None:vals.append(None)
                    elif qa:
                        binding=pair[0].startswith('Q_');vals.append(rec['binding'] if binding else rec['mean'])
                    else:vals.append(rec['scores']['standard']['metrics']['mrr'])
                if all(v is not None for v in vals):
                    delta=sum(v*(1 if i%2==0 else -1) for i,v in enumerate(vals));case_diffs.append(delta)
                    group=(row['dataset'],row['event_group']) if level=='event_group' else row['id'];diffs[group].append(delta)
                for i,v in enumerate(vals):
                    sign=1 if i%2==0 else -1
                    lo+=sign*v if v is not None else -1 if sign<0 else 0
                    hi+=sign*v if v is not None else 1 if sign>0 else 0
            d=np.round([np.mean(x) for x in diffs.values()],12);testable=bool(len(d) and np.any(d))
            p=float(wilcoxon(d,zero_method='pratt',alternative='two-sided').pvalue) if testable else 1.
            tests.append({'contrast':pair,'n_units':len(d),'paired_cases':len(case_diffs),'case_weighted_delta':float(np.mean(case_diffs)) if case_diffs else None,
                'unit_mean_delta':float(d.mean()) if len(d) else None,'p':p,'testable':testable,'historical_comparison':historical,
                'dz':float(d.mean()/d.std(ddof=1)) if len(d)>1 and d.std(ddof=1)>0 else None,
                'case_repairs':sum(x>1e-12 for x in case_diffs),'case_breakages':sum(x< -1e-12 for x in case_diffs),
                'full_denominator_bounds':[lo/len(rows),hi/len(rows)]})
        running=0.
        for rank,i in enumerate(sorted(range(len(tests)),key=lambda i:tests[i]['p'])):
            running=max(running,min(1.,(len(tests)-rank)*tests[i]['p']));tests[i]['p_holm']=running
        results[level]=tests
    return results


def analyze():
    from collections import defaultdict,Counter
    records=[read(p) for p in (RESULTS/'formal/completed').glob('*.json')];rows=roster();index={};qa_groups=defaultdict(list)
    for r in records:
        if r['item']['task']=='RCA' and not r['item']['force_call']:index[r['item']['id'],r['item']['arm']]=r
        elif r['item']['task']=='QA':qa_groups[r['item']['id'],r['item']['arm']].append(r)
    historical=[]
    for row in rows:
        for alias,arm in protocol()['historical'].items():
            path=HISTORY_PATH()/'formal/completed'/f'{row["id"]}__{arm}__RCA.json';r=read(path);r['historical']=True
            index[row['id'],alias]=r;historical.append({'case':row['id'],'arm':alias,'path':str(path.relative_to(ROOT)),'sha256':digest(path),
                'runtime_revision':r['usage'].get('runtime_revision'),'raw':r['raw'],'scores':r['scores'],'usage':r['usage']})
    save(RESULTS/'evaluation/comparison_records.json',historical)
    summary={}
    for arm in [*ARMS,*protocol()['historical']]:
        summary[arm]={}
        for ds in ['overall',*protocol()['dataset_counts']]:
            cohort=[x for x in rows if ds=='overall' or x['dataset']==ds];known=[index[x['id'],arm] for x in cohort if (x['id'],arm) in index];n=len(known);den=len(cohort)
            def mean(f):return sum(f(r) for r in known)/n if n else None
            total=sum(r['scores']['standard']['metrics']['mrr'] for r in known)
            summary[arm][ds]={'known':n,'unknown':den-n,'denominator':den,'mrr':total/n if n else None,
                'tolerant_mrr':mean(lambda r:r['scores']['tolerant']['mrr']),
                'mrr_full_denominator_bounds':[total/den,(total+den-n)/den],
                'metrics':{k:mean(lambda r:r['scores']['standard']['metrics'].get(k,0)) for k in ['ac@1','ac@3','ac@5','avg@3','avg@5','precision@1','precision@3']},
                'mean_total_tokens':mean(lambda r:r['usage']['input_tokens']+r['usage']['output_tokens']),
                'cost':{k:mean(lambda r:r['usage'].get(k,0)) for k in ['input_tokens','output_tokens','image_tokens_original','image_tokens_retained','vision_seconds','language_seconds','processor_model_seconds']},
                'invalid':sum(r['scores']['standard']['status']!='complete' for r in known)}
        summary[arm]['macro_mrr']=sum(summary[arm][d]['mrr'] for d in protocol()['dataset_counts'])/3 if all(summary[arm][d]['mrr'] is not None for d in protocol()['dataset_counts']) else None
    comparisons={name:paired_family(pairs,index,rows) for name,pairs in protocol()['comparisons'].items() if name!='qa'}
    qi={};qa_detail=[];review=[]
    for key,group in qa_groups.items():
        bycat={r['item']['measurement']:r for r in group};credits=[r['scores']['end_to_end_credit'] for r in group]
        qi[key]={'mean':sum(credits)/len(credits),'binding':bycat['binding']['scores']['end_to_end_credit'] if 'binding' in bycat else None}
        qa_detail.extend({'item':r['item'],'scores':r['scores']} for r in group)
        for r in group:
            req=read(ROOT/r['request_path']);review.append({'case':key[0],'arm':key[1],'qa_question':req['qa_items'][0]['question'],
                'source_proof':req['qa_items'][0]['proof'],'qa_raw':r['raw'],'qa_score':r['scores'],
                'rca_raw':index.get(key,{}).get('raw'),'human_classification':None,
                'categories':['read_error','wrong_source','unit_stat_phase_mismatch','correct_observation_unused','reason_ranking_contradiction']})
    from .utils import subset
    qa_rows=subset(rows,10,protocol()['qa_salt']);comparisons['qa']=paired_family(protocol()['comparisons']['qa'],qi,qa_rows,True)
    attention=[]
    for scope in ['formal',*protocol()['smoke_scopes']]:
        for p in (RESULTS/scope/'attention').glob('*.json'):attention.append(read(p))
    no_evidence=[r for r in records if r['item']['arm']=='Q_NO_EVIDENCE'];priors=Counter()
    for row in qa_rows:
        for q in read(RESULTS/'audits/cases'/row['id']/'qa_targets.json' if (RESULTS/'audits/cases'/row['id']/'qa_targets.json').exists() else RESULTS/'inputs'/row['id']/'qa_targets.json'):
            priors[(q['category'],str(q['solutions']))]+=1
    result={'summary':summary,'comparisons':comparisons,'qa':qa_detail,'qa_answer_distribution':[{'category':k[0],'answer':k[1],'count':v} for k,v in priors.items()],
        'no_evidence_calls':len(no_evidence),'independent_repeats':[r for r in records if r['item']['force_call']],
        'actual_completed_calls':sum(r['reference'] is None for r in records),'positions':len(records),
        'exposed_development':True,'causal_limit':'historical references retain batch/backend differences',
        'old_domain_full_inference':'RQ4.9 original Holm correction remains authoritative; not re-tested in a smaller family'}
    save(RESULTS/'analysis/summary.json',result);save(RESULTS/'analysis/attention.json',{'query_coverage':['last_prompt','first_decode'],'layers':[3,23,43,63],'records':attention})
    save(RESULTS/'analysis/qualitative_review.json',review);return result


def build_renderer():
    """Future CPU preparation only. Static qualification never builds/browser-runs."""
    import subprocess
    require_authorization('cpu')
    node=ROOT/'build/renderer_tooling/node-v24.20.0-linux-x64/bin/node'
    env=dict(os.environ,PATH=str(node.parent)+os.pathsep+os.environ['PATH'])
    result=subprocess.run([str(node.parent/'npm'),'run','build'],cwd=ROOT/'src/renderer/web',env=env,capture_output=True,text=True)
    if result.returncode:raise RuntimeError('Unified renderer build failed: '+result.stdout+result.stderr)
