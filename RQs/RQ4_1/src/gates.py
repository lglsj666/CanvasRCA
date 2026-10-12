"""Fail-closed qualification; only explicitly authorized encoder work uses GPU."""
from collections import Counter, defaultdict
from pathlib import Path
import ast
import json
import os
import time
import traceback
from . import exps
from .utils import digest, stable_hash, save_json, read_json, physical_cores, source_order, AttentionStore, foreground_support, support_saturation, isolated_glyph_tokens

ROOT=exps.ROOT
RQ=exps.RQ
OUT=RQ/'results/comparison_coding_v1'


def audit_source_projection(public,compiled,provenance):
    """Independent value/occurrence, chart and typed-role checks; no scores."""
    import re
    from .utils import leaves
    from renderer.utils import expected_bindings
    cards=compiled['evidence']['cards'];byid={c['id']:c for c in cards};mapping=compiled['mapping']
    bound=set(expected_bindings(compiled['evidence']));issues=[];expected={};occurrences=0
    for record in compiled['ledger']['records']:
        source,kind,value=record['source'],record['kind'],record['value']
        atom=next(a for a in public['organization']['atoms'] if a['id']==source)
        if atom.get('value_wire') and json.loads(atom['value_wire'])!=value:issues.append('Ledger/raw value mismatch '+source)
        if kind=='pair_binary':
            normalized={r['id']:{**{k:v for k,v in r.items() if k not in {'phases','unit'}},'phases':{p:{k:v for k,v in v.items() if k in {'n','binary'}} for p,v in r['phases'].items()}} for r in public['payload']['relations']}
            expected[source]=dict(leaves(normalized))
        elif kind=='pair_continuous':
            normalized={r['id']:{'phases':{p:{k:v for k,v in v.items() if k in {'quantiles','conditional_child'}} for p,v in r['phases'].items()}} for r in public['payload']['relations']}
            expected[source]=dict(leaves(normalized))
            for r in public['payload']['relations']:
                for phase,data in r['phases'].items():
                    for i,pair in enumerate(data['points']):
                        for j,v in enumerate(pair):expected[source][f"/{r['id']}/{phase}/points/{i}/{j}"]=v
        else:expected[source]=dict(leaves(value))
        occurrences+=len(expected[source])
    maps=defaultdict(list)
    for m in mapping:
        maps[m['source'],m['path']].append(m)
        if m['binding'] is not None and m['binding'] not in bound:issues.append('Unknown rendered binding '+m['binding'])
    for source,values in expected.items():
        for path,value in values.items():
            candidates=maps[source,path]
            if not candidates:issues.append('Unmapped original source '+source+path);continue
            if not all(m['value_hash']==stable_hash(value) for m in candidates):issues.append('Wrong source value '+source+path)
    def decode(code):
        if isinstance(code,list):return code
        output=[object() for _ in range(code['length'])];assigned=set()
        for value,positions in code['value_positions']:
            for interval in positions.split(','):
                span=list(map(int,interval.split('-')))
                for i in range(span[0],span[-1]+1):
                    if i in assigned or not 0<=i<len(output):raise ValueError('Independent sequence decode failure')
                    output[i]=value;assigned.add(i)
        if len(assigned)!=len(output):raise ValueError('Independent missing sequence position')
        return output
    def number(v):
        if v is None:return None
        m=re.fullmatch(r'\s*([-+\d.eE]+)([kMGT]?)\s*',str(v))
        if not m:raise ValueError('Unsupported frozen numerical spelling')
        return float(m[1])*{'':1,'k':1000,'M':1000000,'G':1000000000,'T':1000000000000}[m[2]]
    source_cards=defaultdict(set)
    for m in mapping:
        if m['binding']:source_cards[m['source']].add(m['binding'].split('.')[0])
    for record in compiled['ledger']['records']:
        v=record['value'];source=record['source'];related=[byid[c] for c in source_cards[source]]
        if v.get('field')=='metric_series_64' or record['kind']=='aux':
            matches=[c for c in related if c['kind']=='metric'];assert len(matches)==1
            c=matches[0];actual=c['data']['values'];expected_seq=decode(v['values_codec'])
            if actual!=[number(x) for x in expected_seq] or c['data']['bins']!=list(range(len(expected_seq))):issues.append('Series values/positions differ '+source)
            if v.get('missing_codec') is not None and decode(v['missing_codec'])!=[x is None for x in expected_seq]:issues.append('Missing pattern differs '+source)
        elif v.get('field')=='trace_summary_entry':
            c=next(c for c in related if c['kind']=='trace')
            if (c['data']['before'],c['data']['after'],c['unit'])!=(number(v['exl_p95_base_us']),number(v['exl_p95_fault_us']),'µs'):issues.append('Trace duration/unit changed '+source)
        elif v.get('field')=='denum_log_template':
            c=next(c for c in related if c['kind']=='log')
            if (c['data']['template'],c['data']['counts'],c['data']['bins'])!=(v['template'],[v['count']],[v['relative_bin']]):issues.append('Log record changed '+source)
    for relation in public['payload']['relations']:
        c=next(c for c in cards if c['kind']=='trace_joint' and c['title'].startswith(relation['id']+' · '))
        exp=[{'phase':p,'parent_ms':x,'child_ms':y} for p in ('reference','current') for x,y in relation['phases'][p]['points']]
        if c['data']['samples']!=exp:issues.append('Request sample changed '+relation['id'])
        if any(c['data'][k]!=relation[k] for k in ('parent','child','parent_operation','child_operation')):issues.append('Request binding changed '+relation['id'])
    expected_edges=set()
    for record in compiled['ledger']['records']:
        v=record['value']
        if record['kind']=='component' and v['kind']=='graph':expected_edges.update(tuple(e) for e in v['data']['edges'])
        elif record.get('prefix')=='directed_call_edge':expected_edges.add((v['caller'],v['callee'],'calls'))
        elif 'relation' in v:
            a,b=v.get('from',v.get('parent')),v.get('to',v.get('child'));kind=v['relation']
            if isinstance(a,list):a,b,kind=a[0],b[0],'request_parent'
            expected_edges.add((a,b,kind))
    actual_edges={(e['source'],e['target'],e['kind']) for c in cards if c['kind']=='graph' for e in c['data']['edges']}
    if expected_edges!=actual_edges:issues.append('Observed relationship set/direction differs')
    identities=[c['data']['identities'] for c in cards if c['title'].startswith('Candidate IDs')]
    if identities!=[public['candidates']]:issues.append('Candidate order/set differs')
    for c in cards:
        for i,item in enumerate(c['data'].get('details',[])):
            mapped=[m for m in mapping if m['binding']==f"{c['id']}.detail.{i}"]
            if not mapped:issues.append('Unbound caption');continue
            original=expected.get(mapped[0]['source'],{}).get(mapped[0]['path'],item['value'])
            text=original if isinstance(original,str) else json.dumps(original,ensure_ascii=False,separators=(',',':'))
            if text!=item['value']:issues.append('Caption altered source value')
    roles={r['id']:r for r in provenance['roles']}
    clock=public['payload']['clock']
    for role in roles.values():
        source_path=role['source_occurrence'].split('/',1)[-1]
        if source_path.split('/')[-1] in {'score','rank_score','signed_z','severity_z_display','deviation_sigma'}:
            issues.append('Anomaly score entered allocation roles')
        if source_path.startswith('log_r/'):
            field=source_path.rsplit('/',1)[-1];period=field.rsplit('_',1)[-1]
            unit='events/min' if '_rate_' in field else 'count'
            if role['unit']!=unit or role['phase']!=('reference' if period=='base' else 'current'):
                issues.append('LOG-R quantity/unit/phase differs from recorded definition')
        if role['quantity']!='recorded_series':continue
        for target in role['targets']:
            cid,_,index=target['binding'].partition('.sample.');card=byid[cid];i=int(index)
            left=card['data']['bins'][i]*clock['duration']/len(card['data']['bins'])
            right=(card['data']['bins'][i]+1)*clock['duration']/len(card['data']['bins'])
            expected_phase='reference' if (left+right)/2<clock['split'] else 'current'
            if role['phase']!=expected_phase:issues.append('Metric bin-center phase differs')
    for e in provenance['edges']:
        rr=[roles[u] for u in e['roles']]
        if len(set(e['roles']))!=len(rr):issues.append('Repeated operand in edge')
        if e['type']=='self_change':
            if [r['phase'] for r in rr]!=['reference','current'] or len({(r['entity'],r['signal'],r['quantity'],r['unit']) for r in rr})!=1:issues.append('Invalid reference/current type binding')
        if e['type']=='parent_child' and [r['phase'] for r in rr]!=['reference','current','reference','current']:issues.append('Invalid request phases')
        if e['type']=='peer' and len({(r['quantity'],r['unit'],r['phase']) for r in rr})!=1:issues.append('Invalid peer quantity/unit')
    return {'status':'passed' if not issues else 'failed','issues':issues,'original_source_occurrences':occurrences,
        'source_records':len(expected),'role_count':len(roles),'edges':len(provenance['edges']),
        'candidate_count':len(public['candidates']),'numeric_unit_pair_checks':True,'source_hash':stable_hash(public['organization'])}


def _admission_case(item):
    row,folder,cores=item
    from multiprocessing import current_process
    from renderer.main import render
    os.sched_setaffinity(0,{cores[(current_process()._identity[0]-1)%len(cores)]})
    base=Path(folder)/row['opaque_incident_id'];base.mkdir(parents=True,exist_ok=True);began=time.monotonic()
    result={'id':row['opaque_incident_id'],'dataset':row['dataset'],'status':'failed'}
    try:
        public=read_json(exps.SOURCE/(result['id']+'.json'));compiled=exps.compile_case(public)
        prov=exps.comparison_provenance(compiled,public);audit=audit_source_projection(public,compiled,prov)
        save_json(base/'source_audit.json',audit)
        if audit['status']!='passed':raise ValueError('Source/semantic audit failed: '+str(audit['issues'][:4]))
        compiled['design']['provenance']=prov['foreground']
        for name,value in [('evidence',compiled['evidence']),('design',compiled['design']),('provenance',prov),('mapping',compiled['mapping'])]:save_json(base/(name+'.json'),value)
        rendered=render(base/'evidence.json',base/'design.json',base/'render')
        result.update(status='source_and_render_passed',png_sha256=rendered['png_sha256'],
            viewport=compiled['design']['viewport'],source_audit=audit,source_sha256=digest(exps.SOURCE/(result['id']+'.json')))
    except Exception as exc:result.update(error=repr(exc),traceback=traceback.format_exc())
    result['seconds']=time.monotonic()-began;save_json(base/'completed.json',result);return result


def admission_source_render(folder_name='source_render'):
    from concurrent.futures import ProcessPoolExecutor
    if folder_name not in {'source_render','typed_source_render'}:raise ValueError('Unknown admission source version')
    folder=OUT/'cpu_admission_v4'/folder_name;folder.mkdir(exist_ok=False);cores=physical_cores(4)
    began=time.monotonic();rows=source_order(read_json(exps.REGISTRATION)['cases']);results=[]
    with ProcessPoolExecutor(max_workers=4) as pool:
        for r in pool.map(_admission_case,[(row,str(folder),cores) for row in rows],chunksize=1):
            results.append(r)
            if len(results)%10==0:print('CPU source/render',len(results),'/220',flush=True)
    result={'status':'passed' if len(results)==220 and all(r['status']=='source_and_render_passed' for r in results) else 'failed',
            'cases':results,'seconds':time.monotonic()-began,'workers':4,'physical_cores':cores,'llm_calls':0,'full_cpu_qualified':False}
    save_json(folder/'report.json',result);return result


def admission_current_base(oid):
    out=OUT/'cpu_admission_v4';fixed=out/'phase_repair'/oid
    retry=out/'typed_retry'/oid
    if (retry/'completed.json').exists():return retry
    typed=out/'typed_source_render'/oid
    if (typed/'completed.json').exists():return typed
    return fixed if (fixed/'completed.json').exists() else out/'source_render'/oid


def admission_repair_failed_render():
    from concurrent.futures import ProcessPoolExecutor
    out=OUT/'cpu_admission_v4';old=read_json(out/'typed_source_render/report.json');registry=read_json(exps.REGISTRATION)
    failed={r['id'] for r in old['cases'] if r['status']!='source_and_render_passed'}
    rows=source_order([r for r in registry['cases'] if r['opaque_incident_id'] in failed])
    folder=out/'typed_retry';folder.mkdir(exist_ok=False);cores=physical_cores(4);results=[]
    with ProcessPoolExecutor(max_workers=4) as pool:
        for r in pool.map(_admission_case,[(row,str(folder),cores) for row in rows],chunksize=1):
            results.append(r)
            if len(results)%10==0:print('Empty-container correction',len(results),'/',len(rows),flush=True)
    lookup={r['id']:r for r in results};merged=[lookup.get(r['id'],r) for r in old['cases']]
    for r in merged:r['base']=str(admission_current_base(r['id']).relative_to(ROOT))
    report={'status':'passed' if all(r['status']=='source_and_render_passed' for r in merged) else 'failed',
        'cases':merged,'retried_cases':len(results),'preserved_previous_report':str(out/'typed_source_render/report.json'),'llm_calls':0}
    save_json(out/'current_render_report.json',report);return report


def admission_phase_repair():
    from renderer.main import render
    out=OUT/'cpu_admission_v4';rows=read_json(out/'source_render/report.json')['cases'];results=[];changed=[]
    for row in rows:
        oid=row['id'];old=out/'source_render'/oid;public=read_json(exps.SOURCE/(oid+'.json'));compiled=exps.compile_case(public)
        prov=exps.comparison_provenance(compiled,public);audit=audit_source_projection(public,compiled,prov)
        if audit['status']!='passed':raise ValueError('Source re-audit failed')
        if prov!=read_json(old/'provenance.json'):
            base=out/'phase_repair'/oid;compiled['design']['provenance']=prov['foreground']
            for key,value in [('evidence',compiled['evidence']),('design',compiled['design']),('provenance',prov),('mapping',compiled['mapping']),('source_audit',audit)]:save_json(base/(key+'.json'),value)
            rendered=render(base/'evidence.json',base/'design.json',base/'render')
            if rendered['png_sha256']!=row['png_sha256']:raise ValueError('Phase audit changed diagnostic PNG')
            save_json(base/'completed.json',{**row,'source_audit':audit,'phase_rule':'source_bin_center','diagnostic_png_unchanged':True})
            # Task/source ledger and connected source groups are invariant to
            # this point-within-curve partition; check, do not assume.
            current=exps.text_conditions(public,compiled,prov);previous=read_json(old/'text_conditions.json')
            if current!=previous:raise ValueError('Phase repair needs new text token check')
            save_json(base/'text_conditions.json',current);save_json(base/'processor_cpu.json',read_json(old/'processor_cpu.json'))
            changed.append(oid)
        results.append({'id':oid,'dataset':row['dataset'],'base':str(admission_current_base(oid).relative_to(ROOT)),
            'png_sha256':row['png_sha256'],'source_audit':audit})
    report={'status':'passed','cases':results,'changed_provenance_cases':changed,'diagnostic_pngs_unchanged':True,'llm_calls':0}
    save_json(out/'current_sources.json',report);return report


def admission_processor():
    """Actual CPU processor for four text controls and the full PNG, no model."""
    import torch
    from PIL import Image
    from transformers import AutoProcessor
    os.sched_setaffinity(0,physical_cores(4));torch.set_num_threads(4)
    out=OUT/'cpu_admission_v4';source=out/'source_render'
    report=read_json(out/'current_render_report.json') if (out/'current_render_report.json').exists() else read_json(source/'report.json')
    if report['status']!='passed':raise ValueError('Source/render gate failed')
    processor=AutoProcessor.from_pretrained('/home/lglsj/CanvasRCA/models/Qwen3.8-27B',local_files_only=True)
    results=[];began=time.monotonic()
    messages=[{'role':'system','content':exps.SYSTEM},{'role':'user','content':[{'type':'image'},{'type':'text','text':exps.VISUAL_TASK}]}]
    prompt=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False,preserve_thinking=False)
    for index,row in enumerate(report['cases']):
        base=admission_current_base(row['id']);public=read_json(exps.SOURCE/(row['id']+'.json'));compiled=exps.compile_case(public)
        prov=read_json(base/'provenance.json');conditions=exps.text_conditions(public,compiled,prov);counts={}
        for arm,parts in conditions.items():
            system=public['system'] if arm in {'T_FULL','T_NATIVE'} else exps.SYSTEM
            text=processor.apply_chat_template([{'role':'system','content':system},{'role':'user','content':parts}],
                tokenize=False,add_generation_prompt=True,enable_thinking=False,preserve_thinking=False)
            counts[arm]=len(processor.tokenizer(text,add_special_tokens=False)['input_ids'])
        im=Image.open(base/'render/dashboard.png').convert('RGB')
        batch=processor(text=[prompt],images=[im],return_tensors='pt');grid=batch['image_grid_thw'][0].tolist()
        t,h,w=grid;counts['V_FULL']=batch['input_ids'].shape[1]
        record={'id':row['id'],'dataset':row['dataset'],'status':'passed' if max(counts.values())+8192<=40960 else 'failed_context',
            'counts':counts,'image_tokens':t*h*w//4,'processed_pixels':[w*16,h*16],'grid_thw':grid,
            'png_sha256':row['png_sha256'],'source_pixels':list(im.size),
            'nominal_font_after_resize':18*min(w*16/im.width,h*16/im.height),
            'text_sha256':{arm:stable_hash(parts) for arm,parts in conditions.items()}}
        save_json(base/'text_conditions.json',conditions);save_json(base/'processor_cpu.json',record);results.append(record)
        if (index+1)%20==0:print('Current actual processor',index+1,'/220',flush=True)
        del batch,im,conditions
    result={'status':'passed' if all(r['status']=='passed' for r in results) else 'failed','cases':results,
        'elapsed_seconds':time.monotonic()-began,'context_limit':40960,'output_reserve':8192,'llm_calls':0,'cuda_visible':os.getenv('CUDA_VISIBLE_DEVICES')}
    save_json(out/'processor_report.json',result);return result


def _admission_support_case(item):
    from multiprocessing import current_process
    from renderer.main import render
    row,cores=item;os.sched_setaffinity(0,{cores[(current_process()._identity[0]-1)%len(cores)]})
    base=admission_current_base(row['id']);began=time.monotonic();result={'id':row['id'],'dataset':row['dataset']}
    try:
        support=foreground_support(base/'render',row['processed_pixels'],policy='shared_v2')
        design=read_json(base/'design.json');roles={r['id']:r for r in design['provenance']['roles']};anchors=set(support['anchors']);isolated=[]
        for rid in support['uncertain_only_unanchored_roles']:
            # Use the union anchors from the complete V2 render. Isolated V1
            # glyph extraction must not reclassify other operands as anchors.
            spec={**design,'provenance':{'schema':'CanonicalForegroundV1','roles':[roles[rid]]}}
            part=base/'isolated'/rid;save_json(part/'design.json',spec)
            rendered=render(base/'evidence.json',part/'design.json',part/'render')
            if rendered['png_sha256']!=row['png_sha256']:raise ValueError('Isolated audit changed the PNG')
            tokens=isolated_glyph_tokens(part/'render/role_foreground.png',row['processed_pixels'])
            if not tokens:raise ValueError('Empty isolated foreground')
            optional=sorted(set(tokens)-anchors);gh,gw=support['grid'];xs=[t%gw for t in tokens];ys=[t//gw for t in tokens]
            support['roles'][rid].update(tokens=optional,fully_anchored=not optional,confirmed_optional_tokens=optional,
                uncertain_only_tokens=[],foreground_possible_tokens=tokens,
                bbox_diag2=float((max(xs)-min(xs)+1)**2+(max(ys)-min(ys)+1)**2),
                isolated_confirmation_sha256=digest(part/'render/role_foreground.png'))
            isolated.append(rid)
        support['uncertain_only_unanchored_roles']=[]
        empty=[u for u,r in support['roles'].items() if not r['tokens'] and not r['fully_anchored']]
        support['definite_empty_unanchored_roles']=empty;support['uncertain_empty_unanchored_roles']=[]
        multiplicity=Counter(t for r in support['roles'].values() for t in r['tokens'])
        support.update(foreground_union_tokens=len(anchors|set(multiplicity)),role_token_incidences=sum(multiplicity.values()),
            shared_nonanchor_tokens=sum(v>1 for v in multiplicity.values()),max_roles_per_token=max(multiplicity.values(),default=0))
        from .utils import evidence_budget
        plans={str(f):{k:v for k,v in evidence_budget(support['roles'],support['anchors'],support['image_tokens'],f,'optional_support_v3').items() if k!='eligible'} for f in (.25,.5,.75)}
        save_json(base/'token_support.json',support)
        result.update(status='passed' if not empty else 'failed_empty_support',empty_roles=empty,
            isolated_confirmations=isolated,role_count=len(support['roles']),anchors=len(anchors),image_tokens=support['image_tokens'],
            budgets=plans,ambiguous_tokens=support['ambiguous_tokens'],
            distance_cache_estimated_bytes=4*sum(len(r['tokens'])**2 for r in support['roles'].values()),
            role_size_quantiles=__import__('numpy').quantile([len(r['tokens']) for r in support['roles'].values()],[0,.25,.5,.75,1]).tolist())
    except Exception as exc:result.update(status='failed',error=repr(exc),traceback=traceback.format_exc())
    result['seconds']=time.monotonic()-began;save_json(base/'support_report.json',result);return result


def admission_support():
    from concurrent.futures import ProcessPoolExecutor
    report=read_json(OUT/'cpu_admission_v4/processor_report.json')
    if report['status']!='passed':raise ValueError('Processor gate failed')
    cores=physical_cores(4);results=[];began=time.monotonic()
    with ProcessPoolExecutor(max_workers=4) as pool:
        for row in pool.map(_admission_support_case,[(r,cores) for r in report['cases']],chunksize=1):
            results.append(row)
            if len(results)%20==0:print('Current support',len(results),'/220',flush=True)
    result={'status':'passed' if all(r['status']=='passed' for r in results) else 'failed','cases':results,'seconds':time.monotonic()-began,
        'workers':4,'physical_cores':cores,'llm_calls':0,'cpu_qualified':False}
    save_json(OUT/'cpu_admission_v4/support_report.json',result);return result


def admission_statistics(rows_override=None,out_override=None):
    """Prespecified outcome-free calibration; no historical/new scores read."""
    import itertools
    import numpy as np
    os.sched_setaffinity(0,physical_cores(8)[4:8])
    reg=read_json(exps.REGISTRATION);group_cases=defaultdict(list)
    for row in (reg['cases'] if rows_override is None else rows_override):group_cases[reg['groups'][row['opaque_incident_id']]].append(row['opaque_incident_id'])
    groups=sorted(group_cases);sizes=np.array([len(group_cases[g]) for g in groups]);n=int(sizes.sum());ng=len(groups)
    offsets=np.r_[0,np.cumsum(sizes)[:-1]];case_group=np.repeat(np.arange(ng),sizes)
    specs=list(itertools.product(('symmetric','skew_positive','skew_negative'),(0.,.75),(0.,.5,1.),('constant','sqrt_n','inverse_sqrt_n')))
    shifts=np.array([0.,.02,.03,.05]);m=len(specs);outer=2000;flips=4999
    seed=int(stable_hash('RQ4.1 prespecified outcome-free stress audit v1')[:16],16)
    rng=np.random.default_rng(seed);reject=np.zeros((m,4),dtype=int);means=np.zeros((m,4));began=time.monotonic()
    out=Path(out_override) if out_override is not None else OUT/'cpu_admission_v4';save_json(out/'statistics_registration.json',{'seed':seed,'replicates':outer,'flips':flips,
        'cells':[list(s) for s in specs],'shifts':shifts.tolist(),'groups':{g:group_cases[g] for g in groups},
        'registered_roster_sha256':digest(exps.REGISTRATION),'group_independence':'inherited event grouping; separate physical-source/exposure audit required',
        'mixture':'sqrt(rho)*shared + sqrt(1-rho)*independent; divide by their sum to preserve bound and variance fraction',
        'symmetric_values':[-1,1],'skew_positive_values':[-.2,.8],'skew_positive_probabilities':[.8,.2],
        'zero_inflation':'independent component draws are zero with probability0.75 before mixing',
        'scale_normalization':'divide each size-related scale by maximum across groups','shift_bounding':'clip individual case differences to [-1,1]',
        'rejection_threshold':.05,'calibration_alarm_threshold':.07,'input_scores_read':False})
    for iteration in range(outer):
        samples=[]
        for law,zero,rho,scaling in specs:
            def draw(count):
                v=np.where(rng.random(count)<(.5 if law=='symmetric' else .2),1. if law=='symmetric' else .8,-1. if law=='symmetric' else -.2)
                if law=='skew_negative':v=-v
                if zero:v*=rng.random(count)>=zero
                return v
            a,b=np.sqrt(rho),np.sqrt(1-rho)
            x=(a*draw(ng)[case_group]+b*draw(n))/(a+b)
            scale=np.ones(ng) if scaling=='constant' else np.sqrt(sizes) if scaling=='sqrt_n' else 1/np.sqrt(sizes)
            x*= (scale/scale.max())[case_group]
            bounded=np.clip(x[:,None]+shifts,-1,1)
            samples.append(np.add.reduceat(bounded,offsets,axis=0))
            means[len(samples)-1]+=bounded.mean(axis=0)
        weighted=np.stack(samples).transpose(1,0,2).reshape(ng,m*4)
        observed=np.abs(weighted.sum(axis=0))
        signs=(rng.integers(0,2,size=(flips,ng),dtype=np.int8)*2-1).astype(np.float64)
        permuted=np.abs(signs@weighted)
        p=(1+(permuted>=observed[None,:]-1e-12).sum(axis=0))/(flips+1)
        reject+=(p.reshape(m,4)<=.05)
        if (iteration+1)%100==0:
            print('Outcome-free calibration',iteration+1,'/2000',flush=True)
            save_json(out/'statistics_progress.json',{'replicates':iteration+1,'seconds':time.monotonic()-began})
    rates=reject/outer;cells=[]
    for i,spec in enumerate(specs):cells.append({'law':spec[0],'zero_inflation':spec[1],'shared_variance_fraction':spec[2],
        'scale':spec[3],'null_rejection_rate':float(rates[i,0]),'power_by_shift':dict(zip(map(str,shifts[1:]),rates[i,1:].tolist())),
        'realized_mean_by_shift':dict(zip(map(str,shifts),(means[i]/outer).tolist()))})
    result={'status':'passed' if rates[:,0].max()<=.07 else 'uncalibrated','cases':n,'event_groups':ng,'group_sizes':sizes.tolist(),
        'cells':cells,'replicates':outer,'flips':flips,'seconds':time.monotonic()-began,'max_null_rejection_rate':float(rates[:,0].max()),
        'llm_calls':0,'observed_results_read':False,'no_confidence_intervals':True,
        'group_independence_proven':False,'scope':'stress calibration only; physical/exposure assumptions audited separately'}
    save_json(out/'statistics_report.json',result);return result


def admission_event_audit():
    """Evaluator-side grouping receipt; never part of a public/model packet."""
    reg=read_json(exps.REGISTRATION);path=ROOT/'RQs/RQ3_1/results/data_registration_v1/private/split.json'
    split=read_json(path);allrows=[r for partition in split['partitions'].values() for r in partition]
    byid={r['opaque_incident_id']:r for r in allrows};rows=[byid[r['opaque_incident_id']] for r in reg['cases']];issues=[]
    inherited_groups=defaultdict(set);source_groups=defaultdict(set)
    for row in rows:
        if row['partition']!='eval':issues.append('Wrong development partition')
        oid=row['opaque_incident_id'];inherited_groups[reg['groups'][oid]].add(oid);source_groups[row['leakage_group']].add(oid)
    # Different namespace hashes are allowed; membership equivalence is the
    # grouping invariant. Never compare unrelated hash strings as identities.
    if set(map(frozenset,inherited_groups.values()))!=set(map(frozenset,source_groups.values())):issues.append('Inherited group membership differs')
    cross_group=[];shared_source=[]
    for i,a in enumerate(rows):
        for b in rows[i+1:]:
            if a['dataset']!=b['dataset'] or a['leakage_group']==b['leakage_group']:continue
            same_source=a['source']==b['source'];same_event=bool(a.get('event')) and a.get('event')==b.get('event')
            if same_source:shared_source.append([a['opaque_incident_id'],b['opaque_incident_id']])
            if same_event or (same_source and max(a['start'],b['start'])<=min(a['end'],b['end'])):
                cross_group.append([a['opaque_incident_id'],b['opaque_incident_id']])
    if cross_group:issues.append('Physical events/overlap cross registered groups')
    out=OUT/'cpu_admission_v4';stats=read_json(out/'statistics_report.json')
    report={'status':'passed_structural_group_check' if not issues else 'failed','issues':issues,
        'cases':[{k:r[k] for k in ('opaque_incident_id','dataset','partition','source','start','end','event','leakage_group')} for r in rows],
        'event_groups':len({r['leakage_group'] for r in rows}),'cross_group_overlap_or_event_pairs':cross_group,
        'cross_group_shared_source_pairs':len(shared_source),'shared_source_pairs':shared_source,
        'group_independence_proven':False,'residual_risk':'Disjoint event windows can share workload/environment/source and remain correlated.',
        'group_membership_equivalent':not any('membership' in v for v in issues),
        'namespace_hash_mapping':{g:next(reg['groups'][oid] for oid in members) for g,members in source_groups.items()},
        'frozen_split_sha256':digest(path),'registration_sha256':digest(exps.REGISTRATION),'all_development_cases_previously_exposed':True}
    save_json(out/'event_group_audit.json',report)
    if stats['status']=='uncalibrated':
        save_json(out/'no_confirmation_declaration.json',{'status':'not_run','stage':'300-case independent confirmation',
            'reason':'Registered outcome-free calibration alarm; protocol prohibits advancement using this inferential family.',
            'independent_stock':'not assessed after prerequisite failed; no claim that independent data do not exist',
            'calls_released_to_other_arms':0,'reserved_unused_calls':2400,'frozen_before_new_development_outcomes':True,
            'statistics_sha256':digest(out/'statistics_report.json'),'llm_calls_this_admission':0})
    return report


def admission_cpu_encoder_probe():
    """One bounded CPU vision forward, no decoder or CUDA; viability only."""
    import signal
    import resource
    import torch
    import numpy as np
    from PIL import Image
    from safetensors import safe_open
    from transformers import AutoConfig,AutoProcessor
    from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5VisionModel
    out=OUT/'cpu_admission_v4/cpu_encoder_probe';out.mkdir(exist_ok=False)
    report={'status':'running','llm_calls':0,'encoder_forwards':0,'language_decoder_loaded':False,'device':'cpu'}
    began=time.monotonic();os.sched_setaffinity(0,physical_cores(8)[4:8]);torch.set_num_threads(4)
    oid='INC-540349CB2170';base=OUT/'cpu_admission_v4/source_render'/oid
    def deadline(*args):raise TimeoutError('CPU vision viability deadline600s')
    old=signal.signal(signal.SIGALRM,deadline);signal.alarm(600)
    try:
        if os.getenv('CUDA_VISIBLE_DEVICES')!='':raise ValueError('CPU isolation is required')
        directory=Path('/home/lglsj/CanvasRCA/models/Qwen3.8-27B');conf=AutoConfig.from_pretrained(directory,local_files_only=True).vision_config
        conf._attn_implementation='sdpa';vision=Qwen3_5VisionModel(conf)
        index=read_json(directory/'model.safetensors.index.json')['weight_map'];prefix='model.visual.';state={};hashes={}
        import hashlib
        for shard in sorted({v for k,v in index.items() if k.startswith(prefix)}):
            with safe_open(directory/shard,framework='pt',device='cpu') as f:
                for key in f.keys():
                    if key.startswith(prefix):
                        value=f.get_tensor(key);state[key[len(prefix):]]=value
                        hashes[key]=hashlib.sha256(value.view(torch.uint16).numpy().tobytes()).hexdigest()
        vision.load_state_dict(state,strict=True,assign=True);del state
        vision=vision.to(dtype=torch.bfloat16,device='cpu').eval().requires_grad_(False)
        processor=AutoProcessor.from_pretrained(directory,local_files_only=True)
        batch=processor.image_processor(images=Image.open(base/'render/dashboard.png').convert('RGB'),return_tensors='pt')
        report.update(id=oid,png_sha256=digest(base/'render/dashboard.png'),grid=batch['image_grid_thw'].tolist(),
            weights=hashes,model_config_sha256=digest(directory/'config.json'),processor_config_sha256=digest(directory/'preprocessor_config.json'),
            initialized_cuda=torch.cuda.is_initialized(),encoder_forwards=1)
        save_json(out/'report.json',report);forward_start=time.monotonic()
        with torch.inference_mode():features=vision(batch['pixel_values'].to(torch.bfloat16),grid_thw=batch['image_grid_thw'],return_dict=True).pooler_output
        report.update(forward_seconds=time.monotonic()-forward_start,shape=list(features.shape),finite=bool(torch.isfinite(features).all()))
        if not report['finite']:raise ValueError('Nonfinite CPU features')
        np.save(out/(oid+'.bf16.npy'),features.view(torch.uint16).numpy(),allow_pickle=False)
        report.update(status='passed_cpu_encoder_only',feature_sha256=digest(out/(oid+'.bf16.npy')))
    except Exception as exc:report.update(status='failed',error=repr(exc),traceback=traceback.format_exc())
    finally:
        signal.alarm(0);signal.signal(signal.SIGALRM,old)
        report.update(seconds=time.monotonic()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
        save_json(out/'report.json',report)
    return report


def local_dependency_audit():
    """Source-only checks: no scorer imports, test execution or external checkout."""
    errors=[]
    contract=read_json(RQ/'configs/local_dependencies_v7.json')
    for relative,expected in contract['frozen_local_dependencies'].items():
        p=(ROOT/relative).resolve()
        if not p.is_relative_to(ROOT) or not p.is_file() or digest(p)!=expected:
            errors.append('Local dependency identity changed: '+relative)
    trees={p:ast.parse(p.read_text(),filename=str(p)) for p in [*(RQ/'src').glob('*.py'),*(ROOT/'src/scorer').glob('*.py')]}
    for p,tree in trees.items():
        for node in ast.walk(tree):
            names=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module or ''] if isinstance(node,ast.ImportFrom) else []
            if any(n in {'vlmrca.upstream','vlmrca.eval.scoring','unified_scripts.rca_scorer','RQs.RQ2_1.src.utils','packages.rq21_native.sircl_original.scoring'} or
                   n.startswith(('src.data','src.evaluation','src.prompts','src.baselines')) for n in names):
                errors.append('Forbidden external or historical scoring import: '+str(p.relative_to(ROOT)))
    def function(path,name):
        tree=ast.parse((ROOT/path).read_text())
        return ast.dump(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name),include_attributes=False)
    if function('src/scorer/matching.py','is_granularity_aware_hit')!=function('src/vlmrca/eval/scoring.py','is_granularity_aware_hit'):
        errors.append('Local and canonical granularity function bodies differ')
    if function('src/scorer/matching.py','pod_to_service')!=function('RQs/RQ1_1/src/renderer/onset.py','pod_to_service'):
        errors.append('Local and historical pod projection bodies differ')
    for name in ('normalize_service','is_service_level_hit'):
        if function('src/scorer/matching.py',name)!=function('packages/rq21_native/sircl_original/scoring.py',name):
            errors.append('Copied local matching helper changed: '+name)
    original=ast.parse((ROOT/'src/unified_scripts/rca_scorer.py').read_text())
    copied=ast.parse((ROOT/'src/scorer/core.py').read_text())
    for node in ast.walk(original):
        if isinstance(node,ast.ImportFrom):
            if node.level==1 and node.module is None:
                node.module='unified_scripts';node.level=0
            elif node.module=='vlmrca.eval.scoring':
                node.module='matching';node.level=1
    if ast.dump(original)!=ast.dump(copied):errors.append('Scorer logic differs beyond the two registered import changes')
    def constants(path):
        return {n.targets[0].id:ast.dump(n) for n in ast.parse((ROOT/path).read_text()).body
            if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and
            n.targets[0].id in {'_ORDINAL_SUFFIX','_REPLICASET_SUFFIX','_WORKER_NODE'}}
    if constants('src/scorer/matching.py')!=constants('RQs/RQ2_1/src/renderer/onset.py'):
        errors.append('Pod projection regular expressions changed')
    receipt=OUT/'local_dependency_repair_v7/before_migration/receipt.json'
    for row in read_json(receipt):
        if digest(ROOT/row['archive'])!=row['sha256']:errors.append('Pre-migration archive changed: '+row['source'])
        if row['source'].endswith('.py') and digest(ROOT/row['source'])!=row['sha256']:
            errors.append('Historical source changed: '+row['source'])
    return {'status':'failed' if errors else 'passed','errors':errors,'static_only':True,
        'metric_logic_and_matching_AST_unchanged':not errors,'historical_sources_preserved':not errors,
        'scorer_factory':'RQs.RQ4_1.src.utils.local_rca_scorer','external_source_repositories_required':False,
        'runtime_import_and_scoring_regression':'written_not_run_while_paused','local_files':contract['frozen_local_dependencies']}


def static_check(output_path=None):
    paths=list((RQ/'src').glob('*.py'))
    expected={'__init__.py','main.py','utils.py','exps.py','tests.py','gates.py'}
    errors=[]
    if {p.name for p in paths}!=expected:errors.append('Five functional modules plus __init__ required')
    lines=0
    for p in paths:
        ast.parse(p.read_text(),filename=str(p))
        lines+=sum(bool(s.strip()) and not s.lstrip().startswith('#') for s in p.read_text().splitlines())
    if lines>7500:errors.append('Source line cap')
    config=read_json(RQ/'configs/comparison_coding_plan_v1.json')
    if config.get('host_memory_policy'):
        policy_path=RQ/'configs'/config['host_memory_policy'];policy=read_json(policy_path)
        if digest(policy_path)!=config['host_memory_policy_sha256']:errors.append('Host-memory policy hash mismatch')
        if any(policy[k] for k in ('host_ram_admission_enabled','memory_estimate_rejection_enabled','memory_termination_enabled')):
            errors.append('Fixed host-memory gates are disabled by user authority')
        if any(policy[k] is not None for k in ('selector_max_rss_bytes','aggregate_rss_limit_bytes')):
            errors.append('No replacement numerical host-RAM limit is permitted')
        for name in ('utils.py','gates.py'):
            tree=ast.parse((RQ/'src'/name).read_text())
            if any(isinstance(n,ast.Raise) and isinstance(n.exc,ast.Call) and isinstance(n.exc.func,ast.Name)
                   and n.exc.func.id=='MemoryError' for n in ast.walk(tree)):errors.append('Host-memory rejection remains in '+name)
            for node in ast.walk(tree):
                if isinstance(node,ast.FunctionDef) and node.name=='sample_memory' and any(isinstance(n,ast.Attribute) and n.attr=='kill' for n in ast.walk(node)):
                    errors.append('Host-memory monitor must not terminate execution')
    if any(config[k] for k in ('gpu_enabled','smoke_enabled','formal_enabled')):errors.append('Launch defaults must stay disabled')
    if len(config['conditions'])!=22 or len(set(config['conditions']))!=22:errors.append('22 unique conditions required')
    if sum(config['budget'].values())!=8900 or config['user_call_ceiling']!=12000:errors.append('Call accounting changed')
    archive=read_json(RQ/'results/token_interface_probe_v1/source_archive_receipt.json')
    for row in archive:
        if digest(ROOT/row['archive'])!=row['sha256']:errors.append('Historical probe source modified')
    if AttentionStore.storage_ceiling()>1000000000:errors.append('Attention storage ceiling')
    if config.get('support_policy')=='shared_v2':
        if digest(RQ/'descriptions/RQ4_1_experiments.md')!=config['protocol_sha256']:errors.append('Current protocol hash mismatch')
        amendment=RQ/'descriptions/RQ4_1_Shared_Support_Amendment_2026-10-06.md'
        if digest(amendment)!=config.get('support_amendment_sha256'):errors.append('Shared-support amendment hash mismatch')
        for row in read_json(OUT/'cpu_stop_source_snapshot/receipt.json'):
            if digest(ROOT/row['archive'])!=row['sha256']:errors.append('Exclusive-support failure archive changed')
    if config.get('budget_policy')=='optional_support_v3':
        amendment=(RQ/'configs'/config['budget_amendment']).resolve()
        if digest(amendment)!=config['budget_amendment_sha256']:errors.append('Evidence budget amendment hash mismatch')
        if config['preselected_candidate']!='CVC_E50':errors.append('Evidence budget candidate must have explicit E50 identity')
        expected=set(config['condition_rename_v3'].values())|{'T_FULL','T_LEDGER','T_DEP','T_NATIVE','V_FULL','CONTRAST_ATLAS'}
        if set(config['conditions'])!=expected:errors.append('Evidence budget condition mapping mismatch')
        for row in read_json(OUT/'saturation_probe_v3/before_snapshot.json'):
            if digest(ROOT/row['archive'])!=row['sha256']:errors.append('Shared grid-budget snapshot changed')
    if any(s in exps.VISUAL_TASK for s in ('INC-', '/home/', 'exact values are in the text')):
        errors.append('Incident or hybrid instruction in pure-visual task')
    dependencies=local_dependency_audit()
    errors.extend(dependencies['errors'])
    report={'status':'failed' if errors else 'passed','errors':errors,'functional_lines':lines,
        'local_dependency_audit':dependencies,
        'attention_10000_peak_bound_bytes':AttentionStore.storage_ceiling(),
        'gpu_started':False,'formal_started':False,'static_only':True,
        'hashes':{str(p.relative_to(ROOT)):digest(p) for p in paths}}
    target=Path(output_path) if output_path is not None else (RQ/'configs'/config['static_report']).resolve() if config.get('static_report') else (OUT/'shared_revision_v2/static.json' if config.get('support_policy')=='shared_v2' else OUT/'static.json')
    save_json(target,report)
    return report


def prepare_one(row, out):
    oid=row['opaque_incident_id'];began=time.monotonic()
    report={'id':oid,'dataset':row['dataset'],'status':'failed','source_path':str(exps.SOURCE/(oid+'.json'))}
    try:
        public=read_json(exps.SOURCE/(oid+'.json'))
        compiled=exps.compile_case(public)
        report.update(candidate_count=len(public['candidates']),card_count=len(compiled['evidence']['cards']),
                      source_record_count=len(compiled['ledger']['records']),mapped_items=len(compiled['mapping']),
                      viewport=compiled['design']['viewport'],source_sha256=digest(exps.SOURCE/(oid+'.json')),
                      ledger_sha256=stable_hash(compiled['ledger']))
        save_json(out/'packets'/(oid+'.json'),compiled)
        from renderer.utils import compile_design
        geometry=compile_design(compiled['evidence'],compiled['design'])
        save_json(out/'geometry'/(oid+'.json'),geometry)
        # Never equate a valid component DTO with a complete-source audit.
        report['status']='source_projection_prepared'
        report['full_qualification']=False
    except Exception as exc:
        report['error_type']=type(exc).__name__;report['error']=str(exc)
    report['seconds']=time.monotonic()-began
    return report


def cpu_inventory():
    stat=static_check()
    if stat['status']!='passed':raise RuntimeError('Static checks failed')
    os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    cores=physical_cores(8)
    os.sched_setaffinity(0,cores)
    rows=read_json(exps.REGISTRATION)['cases']
    if Counter(r['dataset'] for r in rows)!=Counter({'aiops2022':60,'aiops2025':60,'aegislab':100}):
        raise ValueError('Frozen development roster mismatch')
    if any(r.get('cohort')!='eval' for r in rows):raise ValueError('Only exposed eval authorized')
    began=time.monotonic();out=OUT/'cpu_v1';out.mkdir(parents=True,exist_ok=True)
    reports=[]
    # Single process minimizes memory and source pressure; allowed maximum is 8.
    for i,row in enumerate(source_order(rows)):
        result=prepare_one(row,out);reports.append(result)
        if (i+1)%20==0:print('CPU source/capacity',i+1,'/ 220',flush=True)
    errors=Counter(r.get('error','pending source reconciliation') for r in reports if r['status']!='qualified')
    counts={d:{'total':sum(r['dataset']==d for r in reports),
               'renderer_layout_valid':sum(r['dataset']==d and r['status']=='source_projection_prepared' for r in reports),
               'qualified':0} for d in ('aiops2022','aiops2025','aegislab')}
    report={'status':'blocked','gate':'complete_source_geometry_and_capacity','cases':reports,'datasets':counts,
        'errors':dict(errors),'elapsed_seconds':time.monotonic()-began,'physical_core_affinity':cores,'workers':1,
        'actual_processor_tokens':'see separately versioned gallery processor reports; not whole-method qualification',
        'cpu_qualified':False,'gpu_smoke':'not_run','gpu_calls_started':0,
        'formal_started':False,'no_confirmation_roster':'not_audited_no_confirmation_permitted',
        'attention_collection':'storage implementation only; model capture and speed unqualified'}
    
    if (out/'report.json').exists():
        previous=read_json(out/'report.json')
        save_json(out/'history'/('report_'+stable_hash(previous)[:16]+'.json'),previous)
    save_json(out/'report.json',report)
    return report


def model_gate():
    """No generated permission from a partial CPU report or a spent probe."""
    config=read_json(RQ/'configs/comparison_coding_plan_v1.json')
    p=(RQ/'configs'/config['qualification_report']).resolve()
    if not p.exists() or not read_json(p).get('cpu_qualified'):
        raise RuntimeError('RQ4.1 full-source CPU qualification has not passed; no GPU call authorized through this entrypoint')
    raise RuntimeError('No source-bound GPU credential issued; native/backend, attention and prior paths remain unqualified')


def deployment_case(item):
    """Bind existing CPU-qualified images; prepare only new runtime metadata."""
    import numpy as np
    from transformers import AutoProcessor
    global _DEPLOY_PROCESSOR
    row,needed,attention_keys,destination=item;oid=row['id'];out=Path(destination)/'cases'/oid
    out.mkdir(parents=True,exist_ok=True);receipt=out/'index.json'
    if receipt.exists():return read_json(receipt)
    try:processor=_DEPLOY_PROCESSOR
    except NameError:
        processor=AutoProcessor.from_pretrained('/home/lglsj/CanvasRCA/models/Qwen3.8-27B',local_files_only=True);_DEPLOY_PROCESSOR=processor
    public=read_json(exps.SOURCE/(oid+'.json'));base=ROOT/row['base']
    old=read_json(OUT/'cpu_remaining_v10/cases'/oid/'completed.json')
    if old['status']!='passed':raise ValueError('Unqualified source case')
    texts=read_json(base/'text_conditions.json');requests={};sources={};compiled=None;variants=None
    case={'id':oid,'dataset':row['dataset'],'base':row['base'],'candidates':public['candidates'],
        'private':str((exps.SOURCE.parent/'private'/(oid+'.json')).relative_to(ROOT))}
    for token in needed:
        arm,variant=token.split(':');key=oid+'__'+token.replace(':','__');is_text=arm.startswith('T_')
        req={'id':oid,'variant':variant,'arm':arm,'png':None,'label_scoring_allowed':variant not in {'QA','BINDING','OPERAND','IRRELEVANT'}}
        if variant=='QA' and not old.get('qa_applicable_blocks'):
            requests[key]={**req,'not_applicable':'no_registered_scalar_pairs'};continue
        if is_text:
            if variant=='QA':
                qa=OUT/'cpu_remaining_v10/cases'/oid/'qa_text.json';text=read_json(qa)
                req.update(system='Answer only the independent factual QA task.',parts=[{'type':'text','text':text['evidence']+'\n'+exps.QA_TASK}])
                sources[str(qa.relative_to(ROOT))]=digest(qa)
            else:req.update(system=public['system'] if arm in {'T_FULL','T_NATIVE'} else exps.SYSTEM,parts=texts[arm])
        else:
            name='CONTRAST_ATLAS' if arm=='CONTRAST_ATLAS' else variant
            if name=='BASE':folder=base;local={'status':'passed'}
            else:
                local=old['variants'][name]
                if local['status'] in {'not_applicable','not_run_design_infeasible'}:
                    requests[key]={**req,'not_applicable':local.get('reason',local['status'])};continue
                folder=ROOT/local['artifact_root'] if local.get('artifact_root') else OUT/'cpu_remaining_v10/cases'/oid/name
            if local['status']!='passed':raise ValueError('Unqualified variant '+name)
            manifest=read_json(folder/'render/manifest.json')
            task=exps.QA_TASK if variant=='QA' else '\n'.join([exps.VISUAL_TASK,exps.ID_COPY_GUIDE,exps.ID_SYNTAX_GUIDE]+([exps.ATLAS_GUIDE] if name=='CONTRAST_ATLAS' else []))
            req.update(system='Answer only the independent factual QA task.' if variant=='QA' else exps.SYSTEM,
                parts=[{'type':'text','text':task}],png=str((folder/'render/dashboard.png').relative_to(ROOT)),
                png_sha256=manifest['png_sha256'],manifest=str((folder/'render/manifest.json').relative_to(ROOT)))
            if name!='CONTRAST_ATLAS':
                req['support']=str((folder/'token_support.json').relative_to(ROOT))
                support=read_json(ROOT/req['support']);req['grid_thw']=[1,support['grid'][0]*2,support['grid'][1]*2]
                if variant in {'BINDING','OPERAND','IRRELEVANT','POSITION'}:
                    if compiled is None:
                        compiled=exps.compile_case(public);prov=exps.comparison_provenance(compiled,public)
                        qa=exps.qa_packet(public,compiled,prov,oid);variants=exps.intervention_inputs(public,compiled,prov,oid,qa)
                    p=out/(variant+'_provenance.json');save_json(p,variants[variant]['provenance'])
                    req['provenance']=str(p.relative_to(ROOT))
                else:req['provenance']=str((base/'provenance.json').relative_to(ROOT))
            else:req['grid_thw']=local['grid_thw']
            sources[req['png']]=req['png_sha256']
        if variant=='QA':req['qa_audit']=str((OUT/'cpu_remaining_v10/cases'/oid/'qa_audit.json').relative_to(ROOT))
        prompt=processor.apply_chat_template(smoke_messages(req),tokenize=False,add_generation_prompt=True,enable_thinking=False,preserve_thinking=False)
        ids=np.asarray(processor.tokenizer.encode(prompt,add_special_tokens=False),dtype=np.int64)
        if req['png']:
            grid=req['grid_thw'];n=grid[1]*grid[2]//4;where=np.flatnonzero(ids==248056)
            if len(where)!=1:raise ValueError('Expected exactly one public image placeholder')
            at=int(where[0]);ids=np.concatenate((ids[:at],np.full(n,248056,dtype=np.int64),ids[at+1:]))
        req['input_tokens']=len(ids)
        if len(ids)+8192>40960:raise ValueError('Updated instruction exceeds frozen context '+key)
        req['prompt']=prompt
        if token in attention_keys and req['png']:
            info=smoke_attention_preflight(req,ids,(req['grid_thw'][1]//2,req['grid_thw'][2]//2),248056,out/(token.replace(':','__')+'_attention'))
            req.update(info)
        for field in ('manifest','support','provenance','qa_audit','attention_map'):
            if req.get(field):sources[req[field]]=digest(ROOT/req[field])
        requests[key]=req
    for p in (exps.SOURCE/(oid+'.json'),ROOT/case['private'],base/'text_conditions.json'):
        sources[str(p.relative_to(ROOT))]=digest(p)
    result={'case':case,'requests':requests,'files':sources,'status':'passed','new_model_calls':0}
    save_json(receipt,result);return result


def deployment_request_token(unit):
    if unit['arm'].startswith('T_'):arm=unit['arm']
    else:arm='CONTRAST_ATLAS' if unit['arm']=='CONTRAST_ATLAS' else 'VISUAL'
    return arm+':'+unit['variant']


def deployment_prepare():
    """New queue/backend integration audit; existing CPU results stay intact."""
    from vlmrca.run_state import pinned_process_map
    out=OUT/'deployment_v26';out.mkdir(exist_ok=True)
    original=read_json(RQ/'configs/remaining_logical_inputs_v6.json')['positions']
    rows=read_json(RQ/'configs/encoder_admission_v5.json')['cases'];mechanism={u['id'] for u in original if u['kind']=='qa'}
    units=[];needed=defaultdict(set);attentions=defaultdict(set)
    for index,old in enumerate(original):
        u={**old,'queue_index':index,'backend':'native' if old['arm']=='T_NATIVE' else 'hf'}
        token=deployment_request_token(u);u['request_key']=u['id']+'__'+token.replace(':','__')
        u['attention']=u['id'] in mechanism and u['arm'] in {'T_FULL','V_FULL','CVC_E50'} and u['kind'] in {'development','repeat','qa'}
        needed[u['id']].add(token)
        if u['attention']:attentions[u['id']].add(token)
        units.append(u)
    if len(units)!=6100 or len({u['key'] for u in units})!=6100:raise ValueError('Formal matrix changed')
    receipts=pinned_process_map(deployment_case,[(r,sorted(needed[r['id']]),sorted(attentions[r['id']]),str(out)) for r in source_order(rows)],max_workers=8)
    cases={};requests={};files={}
    for r in receipts:cases[r['case']['id']]=r['case'];requests.update(r['requests']);files.update(r['files'])
    report={'status':'passed','positions':len(units),'requests':len(requests),'cases':len(cases),
        'not_applicable_positions':sum(bool(requests[u['request_key']].get('not_applicable')) for u in units),
        'full_CPU_roster_reexecuted':False,'metadata_and_new_task_token_binding_checked':True,'new_model_calls':0}
    save_json(out/'request_index.json',{'cases':cases,'requests':requests,'files':files,'units':units})
    save_json(out/'preparation.json',report);return report


def deployment_config():
    cfg=read_json(ROOT/os.environ.get('CANVASRCA_RQ41_DEPLOYMENT_CONFIG','RQs/RQ4_1/configs/deployment_v26.json'))
    if cfg['schema']!='RQ41DeploymentV26' or cfg['gpu_allocator_fraction']!=.75 or cfg['generation']['max_new_tokens']!=8192:
        raise ValueError('Unknown deployment recipe')
    if cfg['ranking_decoder_profile']!='ranking_prefix_greedy_v25' or cfg['common_batch_size']!=1:
        raise ValueError('Unqualified decoder/batch policy')
    if cfg['generation']!={'max_new_tokens':8192,'temperature':1.,'top_p':.95,'top_k':0} or cfg['generation_schema_profile']!='public_numeric_id_v23':
        raise ValueError('Unregistered generation parameters')
    accepted=read_json(ROOT/cfg['acceptance'])
    if accepted['attention_gate']!='passed_by_explicit_user_acceptance' or accepted['time_gate']!='passed_by_explicit_user_acceptance':
        raise ValueError('Runtime acceptance missing')
    if cfg['purpose']=='qualification':
        if cfg.get('authority')!='user_2026_10_07_two_deployment_smokes' or cfg['round'] not in (1,2):raise PermissionError('No smoke authority')
        if cfg['max_calls']!=18 or cfg['wall_seconds']!=600 or len(cfg['test_units'])>18:raise ValueError('Supplement limit')
    elif cfg['purpose']=='formal':
        auth=read_json(ROOT/cfg['authorization_file'])
        if not auth.get('authorized'):raise PermissionError('Formal launch awaits explicit user instruction')
        proof=read_json(ROOT/auth['qualification'])
        if proof['status']!='deployment_qualified' or auth['source_freeze_sha256']!=digest(ROOT/cfg['freeze']):
            raise PermissionError('Launch credential does not bind the qualified source')
    else:raise ValueError('Unknown execution purpose')
    return cfg


def deployment_freeze():
    """Prospective immutable source snapshot; no generated launch permission."""
    import shutil
    cfg=read_json(RQ/'configs/deployment_v26.json');out=OUT/'deployment_v26'
    if (out/'freeze.json').exists():raise ValueError('Deployment already frozen; use an explicit successor')
    if read_json(out/'preparation.json')['status']!='passed':raise ValueError('Input registration incomplete')
    static=static_check(output_path=out/'static.json')
    if static['status']!='passed':raise ValueError('Static check failed')
    old=read_json(OUT/'gpu_smoke_v22_round05/freeze.json')
    paths=[*sorted((RQ/'src').glob('*.py')),RQ/'configs/deployment_v26.json',RQ/'configs/runtime_acceptance_v26.json',RQ/'configs/comparison_coding_plan_v1.json',
        *sorted((RQ/'configs').glob('deployment_smoke_v26_round*.json')),RQ/'scripts/run_deployment.sh',
        ROOT/cfg['native_profile'],RQ/'descriptions/RQ4_1_Deployment_Qualification_2026-10-07.md',
        out/'request_index.json',out/'preparation.json',out/'static.json',out/'targeted_tests.log',
        ROOT/'configs/dataset_segmentation.yaml',ROOT/'configs/vllm_inference.yaml',ROOT/'configs/vllm_inference_local.yaml',
        ROOT/'configs/rca_scorer.yaml',ROOT/'src/vlmrca/run_state.py',ROOT/'src/vlmrca/vlm/client.py',
        ROOT/'scripts/vllm_vlm/serve_canvasrca_local.sh',*sorted((ROOT/'src/scorer').glob('*.py'))]
    # Renderer and shared local imports are part of the qualified executable.
    paths.extend(p for base in ('src/renderer','unified_scripts','src/vlmrca/vlm') for p in (ROOT/base).rglob('*')
        if p.is_file() and not any(x in p.parts for x in ('node_modules','__pycache__','dist')) and p.suffix in {'.py','.ts','.tsx','.json','.yaml'})
    files={str(p.relative_to(ROOT)):digest(p) for p in paths}
    for path in files:
        if path==cfg['index']:continue
        target=out/'source_snapshot'/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target)
    record={'status':'frozen_for_qualification','files':files,'model_metadata':old['model_metadata'],
        'weight_file_identity':old['weight_file_identity'],'codex_sha256':digest(ROOT/'Codex.md'),
        'index':cfg['index'],'formal_started':False,'accepted_runtime_costs':read_json(ROOT/cfg['acceptance']),
        'passed_CPU_receipt':str((OUT/'cpu_completion_v17/qualification.json').relative_to(ROOT))}
    save_json(out/'freeze.json',record);return {'status':'passed','source_freeze_sha256':digest(out/'freeze.json')}


def deployment_units(cfg,index,backend=None):
    units=cfg['test_units'] if cfg['purpose']=='qualification' else index['units']
    return [u for u in units if backend is None or u['backend']==backend]


def deployment_group(unit):
    arm=unit['arm'];mode='native'
    if arm.startswith('T_'):mode='text'
    elif arm in ('DART_E50','S2PRUNE_E50'):mode='prior'
    elif arm not in ('V_FULL','CONTRAST_ATLAS'):mode='select'
    group={'name':unit['key'],'arm':arm,'mode':mode,'requests':[unit['request_key']],
        'slots':[unit['queue_index']+1],'seed':unit['seed'],'greedy':False,'attention':unit.get('attention',False)}
    if arm in ('DART_E50','S2PRUNE_E50','SCOPE_E50'):group['method']=arm.removesuffix('_E50')
    if arm in ('SCOPE_E50','S2PRUNE_E50'):group['anchor_policy']='shared_anchors_v22'
    group.update(unit.get('runtime_control',{}));return group


def deployment_bound_request(unit,index,cfg):
    req={**index['requests'][unit['request_key']]}
    group=deployment_group(unit)
    if not req.get('not_applicable'):
        # Per-new-call checks only; committed calls are skipped before this.
        for field in ('manifest','support','provenance','qa_audit','attention_map'):
            if req.get(field) and digest(ROOT/req[field])!=index['files'][req[field]]:
                raise ValueError('Bound runtime artifact changed: '+field)
        if req.get('manifest'):
            measured=read_json(ROOT/req['manifest'])
            req['preprocessing_cost']={'cache_reused':True,'renderer_seconds_from_original_build':measured.get('renderer_seconds'),
                'renderer_python_seconds_from_original_build':measured.get('python_end_to_end_seconds'),
                'cold_compiler_seconds':None,'scope':'historical measured renderer build; cold compiler cost not measured'}
    # Public model input and method/seed/backend determine logical identity;
    # scoring labels and instrumentation paths never enter model messages.
    req['request_hash']=stable_hash([smoke_messages(req) if not req.get('not_applicable') else req,
        req.get('png_sha256'),unit['arm'],unit['backend'],unit['seed'],cfg['generation'],
        cfg['ranking_decoder_profile'],cfg['generation_schema_profile'],group.get('anchor_policy'),group.get('identity',False)])
    return req


def deployment_materialize(req,processor):
    from PIL import Image
    started=time.monotonic()
    if req.get('png') and digest(ROOT/req['png'])!=req['png_sha256']:raise ValueError('Frozen diagnostic PNG changed')
    image=Image.open(ROOT/req['png']).convert('RGB') if req.get('png') else None
    batch=dict(processor(text=[req['prompt']],images=[image] if image else None,padding=True,return_tensors='pt'))
    if int(batch['attention_mask'].sum())!=req['input_tokens'] or req['input_tokens']+8192>40960:
        raise ValueError('Actual processor differs from qualified request descriptor')
    return batch,time.monotonic()-started


def deployment_attention(req,batch,out):
    """Compact shared geometry, independent of request/attempt cardinality."""
    import numpy as np
    if not req.get('png'):
        ids=np.zeros(batch['input_ids'].shape[1],dtype=np.int16)
        return {'regions':['text:diagnostic_evidence_and_instructions'],'key_region':ids,'map_hash':stable_hash(ids.tolist())}
    record=smoke_attention_input(req,batch['input_ids'][0].numpy())
    folder=out/'attention_shared';folder.mkdir(exist_ok=True)
    target=folder/(record['map_hash']+'.npz')
    if not target.exists():
        import io
        from vlmrca.run_state import atomic_write
        buf=io.BytesIO();np.savez_compressed(buf,regions=np.asarray(record['regions']),key_region=np.asarray(record['key_region'],dtype=np.int16))
        # Account allocated filesystem bytes, directory metadata and new file.
        used=sum(max(p.stat().st_blocks*512,p.stat().st_size) for p in folder.iterdir())
        if used+len(buf.getvalue())+8192>AttentionStore.SHARED_RESERVE:raise ValueError('Attention shared-map reserve exceeded')
        atomic_write(target,buf.getvalue())
    return record


def deployment_hf_runtime(cfg,out):
    import torch,xgrammar as xgr
    from transformers import AutoProcessor,Qwen3_5ForConditionalGeneration
    from .utils import PassiveAttentionTap,rca_generation_schema
    torch.set_num_threads(8);torch.cuda.set_per_process_memory_fraction(.75)
    processor=AutoProcessor.from_pretrained(cfg['model_path'],local_files_only=True);processor.tokenizer.padding_side='left'
    model=Qwen3_5ForConditionalGeneration.from_pretrained(cfg['model_path'],dtype=torch.bfloat16,device_map='cuda',attn_implementation='sdpa',local_files_only=True).eval()
    compiler=xgr.GrammarCompiler(xgr.TokenizerInfo.from_huggingface(processor.tokenizer,vocab_size=model.config.text_config.vocab_size))
    schema=rca_generation_schema(cfg['generation_schema_profile']);store=AttentionStore(out/'attention');tap=PassiveAttentionTap(store);tap.install(model)
    return {'processor':processor,'model':model,'grammar':compiler.compile_json_schema(schema,any_whitespace=False),
        'qa_grammar':compiler.compile_builtin_json_grammar(),'generation_schema':schema,'store':store,'tap':tap,
        'matched_cfg':read_json(RQ/'configs/comparison_coding_plan_v1.json'),'pairs':{}}


def deployment_hf_worker(cfg,index,out,journal,units,stopping):
    import torch
    runtime=deployment_hf_runtime(cfg,out);processor=runtime['processor'];tap=runtime['tap'];completed=0
    try:
        for unit in units:
            if stopping():break
            journal.check_writes()
            if journal.completed(unit['key']):continue
            req=deployment_bound_request(unit,index,cfg)
            if req.get('not_applicable'):journal.disposition(unit,req['not_applicable']);continue
            batch,pre_seconds=deployment_materialize(req,processor)
            attention=deployment_attention(req,batch,out) if unit.get('attention') else None
            group=deployment_group(unit);attempt=journal.begin(unit,req)
            if attempt is None:continue
            group['attention_key']=stable_hash([journal.scope,unit['key'],attempt])
            save_json(out/'status.json',{'status':'running','backend':'hf','active_key':unit['key'],'attempt_id':attempt,
                'completed_this_session':completed,'formal_started':cfg['purpose']=='formal'})
            print('START',unit['key'],flush=True)
            try:
                batch={k:v.to('cuda') for k,v in batch.items()}
                raw=hf_infer_group(runtime,group,[req],batch,index,cfg,out,attention)[0]
                raw.update(processor_wall_seconds=pre_seconds,preprocessing_cost=req.get('preprocessing_cost'),decoder_seed=unit['seed'],attention_key=group['attention_key'] if unit.get('attention') else None)
                if cfg['purpose']=='formal':
                    # Deterministic audit geometry is reconstructible from
                    # frozen sources and selected indices, not copied per call.
                    raw['original_mrope']=None
                    if raw.get('prior_state'):raw['prior_state'].pop('retained_position_ids',None)
                journal.submit(unit,req,raw,attempt);completed+=1
                print('DONE',unit['key'],'seconds',round(raw['seconds_group'],3),flush=True)
                if raw.get('parity',{}).get('passed') is False:raise ValueError('Production identity parity failed')
                if tap.error or tap.missed:raise ValueError('Passive attention record failed')
                del batch,raw
            except BaseException as exc:
                # A completed inference may already be queued for commit.
                # Drain before classifying its attempt as an interruption.
                journal.drain()
                if not (out/'trajectories'/(unit['key']+f'__call{attempt}.json')).exists():
                    with journal.calls.connect() as db:state=db.execute('SELECT state FROM calls WHERE id=?',(attempt,)).fetchone()[0]
                    if state=='started':journal.calls.finish(attempt,{'error':repr(exc)},'infrastructure_failure')
                raise
        journal.drain()
    finally:
        tap.close();runtime['store'].close()
    return {'completed_this_session':completed,'attention_records':runtime['store'].accepted,'attention_error':tap.error,'attention_missed':tap.missed}


def deployment_native_worker(cfg,index,out,journal,units,stopping):
    """Original local serving stack with the uniform per-request decoder."""
    import subprocess,socket,secrets,signal
    from concurrent.futures import ThreadPoolExecutor,wait,FIRST_COMPLETED
    from dataclasses import asdict
    from vlmrca.vlm.client import call_vlm
    from vlmrca.vlm.configs import VLMConfig
    from .utils import rca_generation_schema
    import vlmrca.vlm.client as client
    client.load_env=lambda:0
    sock=socket.socket();busy=sock.connect_ex(('127.0.0.1',8000))==0;sock.close()
    if busy:raise RuntimeError('Native port is already owned')
    key=secrets.token_urlsafe(24)
    env={**os.environ,'VLLM_API_KEY':key,'CANVASRCA_STANDALONE':'1','CANVASRCA_ATTENTION_MODE':'off',
        'CANVASRCA_VLLM_CONFIG':str(ROOT/cfg['native_profile']),
        'CANVASRCA_RQ41_NATIVE_DECODER_AUDIT':str(out/'native_decoder')}
    env.pop('RL_SLM_RCA_ROOT',None)
    log=(out/'native_server.log').open('a')
    server=subprocess.Popen(['bash','scripts/vllm_vlm/serve_canvasrca_local.sh','qwen3.8-27b'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    save_json(out/'native_server.json',{'pid':server.pid,'owned':True,'profile':cfg['native_profile']})
    os.environ['CANVASRCA_DEPLOY_BASE_URL']='http://127.0.0.1:8000/v1';os.environ['CANVASRCA_DEPLOY_API_KEY']=key
    schema=rca_generation_schema(cfg['generation_schema_profile']);schema['properties']['services'].pop('uniqueItems',None)
    deadline=read_json(out/'started.json')['started_unix']+600 if cfg['purpose']=='qualification' else None
    submitted=completed=0
    def infer(unit,req,attempt):
        audit_key=stable_hash([journal.scope,unit['key'],attempt])
        timeout=max(1.,deadline-time.time()) if deadline else 1800.
        recipe=VLMConfig(tag='qwen3.8-27b',backend='openai',model_id='Qwen/Qwen3.8-27B',max_tokens=8192,temperature=1.,top_p=.95,seed=unit['seed'],
            thinking=False,thinking_via_template=True,base_url_env='CANVASRCA_DEPLOY_BASE_URL',api_key_env='CANVASRCA_DEPLOY_API_KEY',request_timeout_s=timeout,
            extra={'extra_body':{'chat_template_kwargs':{'enable_thinking':False,'preserve_thinking':False},'top_k':-1,
                'vllm_xargs':{'rq41_ranking_profile':cfg['ranking_decoder_profile'],'rq41_audit_key':audit_key}}})
        try:
            r=call_vlm(req['parts'],recipe,system=req['system'],max_retries=1,
                response_format={'type':'json_schema','json_schema':{'name':'rca','strict':True,'schema':schema}},record_performance=True,
                registered_seed=unit['seed'])
            raw={'status':'completed','backend':'vllm_native','response':r.text,'raw':r.raw,'input_tokens':r.input_tokens,
                'output_tokens':r.output_tokens,'seconds_group':r.latency_s,'performance':r.performance,
                'recipe':asdict(recipe),'decoder_seed':unit['seed'],'ranking_decoder_profile':cfg['ranking_decoder_profile'],
                'native_decoder_audit_key':audit_key,'models':models,'generation_schema':schema}
            # Persist the returned answer before any derived score/metadata check.
            journal.submit(unit,req,raw,attempt)
            if r.input_tokens!=req['input_tokens']:raise ValueError('Native/local actual tokenizer mismatch')
            proof=read_json(out/'native_decoder'/(audit_key+'.json'))
            if not proof['ranking_complete']:raise ValueError('Native prefix was not released')
            return unit['key']
        except BaseException as exc:
            journal.drain()
            with journal.calls.connect() as db:state=db.execute('SELECT state FROM calls WHERE id=?',(attempt,)).fetchone()[0]
            if state=='started':journal.calls.finish(attempt,{'error':repr(exc)},'infrastructure_failure')
            raise
    try:
        while True:
            if server.poll() is not None:raise RuntimeError('Owned vLLM server exited')
            if stopping():return {'completed_this_session':0,'paused_before_calls':True}
            if deadline and time.time()>=deadline:raise TimeoutError('Native readiness exceeded window')
            models=smoke_probe_models('http://127.0.0.1:8000/v1/models',key)
            if models:
                if {m['id'] for m in models['data']}!={'Qwen/Qwen3.8-27B'}:raise ValueError('Wrong served checkpoint')
                break
            time.sleep(1)
        remaining=iter(units);active={};exhausted=False
        with ThreadPoolExecutor(max_workers=cfg['native_concurrency']) as pool:
            while active or not exhausted:
                journal.check_writes()
                while len(active)<cfg['native_concurrency'] and not exhausted and not stopping():
                    unit=next(remaining,None)
                    if unit is None:exhausted=True;break
                    if journal.completed(unit['key']):continue
                    req=deployment_bound_request(unit,index,cfg)
                    if req.get('not_applicable'):journal.disposition(unit,req['not_applicable']);continue
                    attempt=journal.begin(unit,req)
                    if attempt is None:continue
                    active[pool.submit(infer,unit,req,attempt)]=unit['key'];submitted+=1
                if stopping():exhausted=True
                if not active:continue
                done,_=wait(active,timeout=1,return_when=FIRST_COMPLETED)
                for future in done:
                    name=active.pop(future);future.result();completed+=1;print('DONE native',name,flush=True)
                save_json(out/'status.json',{'status':'draining' if stopping() else 'running','backend':'native',
                    'submitted_this_session':submitted,'completed_this_session':completed,'in_flight':len(active),'formal_started':cfg['purpose']=='formal'})
        journal.drain()
        return {'completed_this_session':completed,'submitted_this_session':submitted,'concurrency':cfg['native_concurrency']}
    finally:
        if server.poll() is None:
            os.killpg(server.pid,signal.SIGTERM)
            try:server.wait(timeout=8)
            except subprocess.TimeoutExpired:os.killpg(server.pid,signal.SIGKILL);server.wait()
        log.close()


def deployment_worker(backend):
    import signal
    from .utils import DeploymentJournal
    cfg=deployment_config();out=ROOT/cfg['output'];index=read_json(ROOT/cfg['index'])
    if os.environ.get('CANVASRCA_RQ41_WORKER_TOKEN')!=digest(out/'started.json'):raise PermissionError('Worker needs owning supervisor')
    if read_json(out/'started.json')['config_hash']!=stable_hash(cfg):raise ValueError('Worker configuration changed after registration')
    stopped=False
    def stop(*_):
        nonlocal stopped
        stopped=True
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    def stopping():return stopped or (out/'PAUSE').exists()
    units=deployment_units(cfg,index,backend);began=time.monotonic()
    journal=DeploymentJournal(out,cfg['max_calls'],cfg['ledger_scope'],lambda req,response:smoke_score(req,response,index['cases']))
    try:
        recovery=journal.recover();save_json(out/('recovery.'+backend+'.json'),recovery)
        pending=[u for u in units if not journal.completed(u['key'])]
        if not pending:journal.finish_phase(backend,units);return {'status':'passed','model_loaded':False}
        if stopping():return {'status':'paused','model_loaded':False}
        # Reject budget exhaustion BEFORE reserving a GPU or loading its model.
        if sum(journal.calls.summary().values())>=cfg['max_calls']:raise RuntimeError('Call reserve exhausted')
        fn=deployment_hf_worker if backend=='hf' else deployment_native_worker
        result=fn(cfg,index,out,journal,pending,stopping);journal.drain()
        complete=all(journal.completed(u['key']) for u in units)
        if complete:journal.finish_phase(backend,units)
        report={'status':'passed' if complete else 'paused','backend':backend,'model_loaded':True,**result,
            'session_reserved_device_seconds':time.monotonic()-began,'formal_started':cfg['purpose']=='formal'}
        save_json(out/'sessions'/(str(time.time_ns())+'_'+backend+'.json'),report)
        return report
    except BaseException as exc:
        save_json(out/'worker_failure.json',{'backend':backend,'error':repr(exc),'traceback':traceback.format_exc()});raise
    finally:journal.close()


def deployment_supervisor():
    import fcntl,signal,subprocess,sys,sqlite3
    cfg=deployment_config();out=ROOT/cfg['output'];out.mkdir(parents=True,exist_ok=True)
    lock=(out/'supervisor.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    frozen=read_json(ROOT/cfg['freeze'])
    # Only source/config plus the small logical index; no historical PNG sweep.
    for path,sha in frozen['files'].items():
        if digest(ROOT/path)!=sha:raise ValueError('Deployment frozen dependency changed: '+path)
    for path,sha in frozen['model_metadata'].items():
        if digest(Path(path))!=sha:raise ValueError('Checkpoint config changed')
    for row in frozen['weight_file_identity']:
        stat=Path(row['path']).stat()
        if (stat.st_size,stat.st_mtime_ns)!=(row['size'],row['mtime_ns']):raise ValueError('Checkpoint shard changed')
    if cfg['purpose']=='qualification':
        claim=OUT/'deployment_smoke_allowance_v26'/('round_'+str(cfg['round']))
        claim.parent.mkdir(exist_ok=True);claim.mkdir();save_json(claim/'claim.json',cfg)
        if (out/'started.json').exists():raise ValueError('Cannot restart spent qualification clock')
    if (out/'PAUSE').exists():return {'status':'paused','model_loaded':False}
    index=read_json(ROOT/cfg['index']);units=deployment_units(cfg,index)
    if all((out/'completed'/(u['key']+'.json')).exists() for u in units):return {'status':'passed','model_loaded':False,'already_complete':True}
    started=time.time();save_json(out/'started.json',{'started_unix':started,'pid':os.getpid(),'source_freeze_sha256':digest(ROOT/cfg['freeze']),
        'config_hash':stable_hash(cfg),'purpose':cfg['purpose']})
    stop_requested=False;child=None;summary={'status':'running','positions':len(units),'formal_started':cfg['purpose']=='formal','pid':os.getpid()}
    def stopping(*_):
        nonlocal stop_requested
        stop_requested=True;save_json(out/'PAUSE',{'reason':'supervisor_signal','time':time.time()})
    signal.signal(signal.SIGTERM,stopping);signal.signal(signal.SIGINT,stopping)
    try:
        for backend in cfg['backends']:
            group=[u for u in units if u['backend']==backend]
            if not group or (out/('phase_complete.'+backend+'.json')).exists():continue
            if stop_requested or (out/'PAUSE').exists():break
            env={**os.environ,'CANVASRCA_RQ41_WORKER_TOKEN':digest(out/'started.json')}
            child=subprocess.Popen([sys.executable,'-u','-m','RQs.RQ4_1.src.main','deployment-worker','--backend',backend],cwd=ROOT,env=env,start_new_session=True)
            save_json(out/'worker.json',{'pid':child.pid,'backend':backend});summary['backend']=backend
            while child.poll() is None:
                if cfg['purpose']=='qualification' and time.time()-started>=600:raise TimeoutError('Shared 600-second deployment smoke deadline')
                if (stop_requested or (out/'PAUSE').exists()) and child.poll() is None:child.send_signal(signal.SIGTERM)
                count=0
                if (out/'calls.sqlite').exists():
                    with sqlite3.connect(out/'calls.sqlite') as db:count=db.execute('SELECT count(*) FROM calls').fetchone()[0]
                if count>cfg['max_calls'] or count+cfg['previous_model_attempts_before_this_task']+36>cfg['global_call_ceiling']:
                    raise RuntimeError('Global/local call ceiling violated')
                summary.update(calls_started=count,calls_completed=len(list((out/'completed').glob('*.json'))),elapsed_seconds=round(time.time()-started,2))
                save_json(out/'summary.json',summary);time.sleep(1)
            if child.returncode:raise RuntimeError('Deployment worker exited '+str(child.returncode))
        complete=all((out/'completed'/(u['key']+'.json')).exists() for u in units)
        summary['status']='completed_pending_review' if complete and cfg['purpose']=='qualification' else 'complete' if complete else 'paused'
    except BaseException as exc:
        summary.update(status='timeout_blocked' if isinstance(exc,TimeoutError) else 'failed',error=repr(exc),traceback=traceback.format_exc())
        if child is not None and child.poll() is None:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
        if (out/'native_server.json').exists():
            server=read_json(out/'native_server.json');pid=server['pid']
            try:
                command=Path(f'/proc/{pid}/cmdline').read_bytes()
                if b'vllm' in command and b'serve' in command:os.killpg(pid,signal.SIGTERM)
            except ProcessLookupError:pass
            except FileNotFoundError:pass
    finally:
        summary.update(elapsed_seconds=round(time.time()-started,2),calls_completed=len(list((out/'completed').glob('*.json'))),formal_started=cfg['purpose']=='formal')
        if (out/'calls.sqlite').exists():
            with sqlite3.connect(out/'calls.sqlite') as db:summary['calls_started']=db.execute('SELECT count(*) FROM calls').fetchone()[0]
        save_json(out/'summary.json',summary);lock.close()
    return summary


def admission_encoder():
    """User-authorized vision-only extraction; never loads a language decoder."""
    import fcntl
    import signal
    import shutil
    import numpy as np
    config_path=RQ/'configs/encoder_admission_v5.json';cfg=read_json(config_path)
    if cfg.get('authorization')!='explicit_user_encoder_only':raise PermissionError('No encoder-only authorization')
    out=OUT/'cpu_admission_v5';run=out/'encoder';run.mkdir(parents=True,exist_ok=True)
    lock=(run/'lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    report_path=run/'report.json'
    if report_path.exists() and read_json(report_path)['status']=='passed_encoder_only':return read_json(report_path)
    budget_path=run/'budget.json'
    if not budget_path.exists():save_json(budget_path,{'started_unix':time.time(),'attempts':[]})
    budget=read_json(budget_path);remaining=cfg['wall_seconds']-(time.time()-budget['started_unix'])
    cpu_start=read_json(OUT/'cpu_admission_v4/started.json')
    remaining=min(remaining,cpu_start['max_wall_seconds']-(time.time()-cpu_start['started_unix']))
    if remaining<=0:raise TimeoutError('Registered preparation deadline exhausted')
    report={'status':'running','llm_calls':0,'language_decoder_loaded':False,'attention_collection':False,'cases':[]}
    def deadline(*_):raise TimeoutError('Encoder-only preparation deadline')
    previous=signal.signal(signal.SIGALRM,deadline);signal.alarm(max(1,int(remaining)))
    started=time.monotonic()
    try:
        import torch
        import transformers
        from PIL import Image
        from safetensors import safe_open
        from transformers import AutoProcessor,AutoConfig
        from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5VisionModel
        os.sched_setaffinity(0,physical_cores(4));torch.set_num_threads(4)
        pending=[r for r in cfg['cases'] if not (run/'completed'/(r['id']+'.json')).exists()]
        if shutil.disk_usage(run).free<sum(r['image_tokens']*5120*2+4096 for r in pending)+10*1024**3:
            raise OSError('Insufficient cache space with10GiB reserve')
        torch.cuda.set_per_process_memory_fraction(.75,0)
        directory=Path(cfg['model_path']);conf=AutoConfig.from_pretrained(directory,local_files_only=True).vision_config
        conf._attn_implementation='sdpa';vision=Qwen3_5VisionModel(conf)
        index=read_json(directory/'model.safetensors.index.json')['weight_map'];prefix='model.visual.';state={};weights={}
        import hashlib
        for shard in sorted({v for k,v in index.items() if k.startswith(prefix)}):
            with safe_open(directory/shard,framework='pt',device='cpu') as handle:
                for key in handle.keys():
                    if key.startswith(prefix):
                        value=handle.get_tensor(key);state[key[len(prefix):]]=value
                        weights[key]=hashlib.sha256(value.view(torch.uint16).numpy().tobytes()).hexdigest()
        vision.load_state_dict(state,strict=True,assign=True);del state
        vision=vision.to(device='cuda',dtype=torch.bfloat16).eval().requires_grad_(False)
        processor=AutoProcessor.from_pretrained(directory,local_files_only=True)
        freeze={'config_sha256':digest(config_path),'source_sha256':digest(__file__),'vision_weights':weights,
                'model_config':digest(directory/'config.json'),'processor_config':digest(directory/'preprocessor_config.json'),
                'torch':torch.__version__,'transformers':transformers.__version__,'language_decoder_loaded':False}
        freeze_path=run/'freeze.json'
        if freeze_path.exists() and read_json(freeze_path)!=freeze:raise ValueError('Encoder resume freeze changed')
        save_json(freeze_path,freeze);print('Vision encoder only loaded; frozen current images',len(cfg['cases']),flush=True)
        for row in cfg['cases']:
            commit=run/'completed'/(row['id']+'.json')
            if commit.exists():report['cases'].append(read_json(commit));continue
            if len(budget['attempts'])>=cfg['max_forwards']:raise RuntimeError('Encoder preparation attempt cap')
            path=ROOT/row['png']
            if digest(path)!=row['png_sha256']:raise ValueError('Current PNG identity changed')
            batch=processor.image_processor(images=Image.open(path).convert('RGB'),return_tensors='pt')
            grid=batch['image_grid_thw']
            if grid.tolist()!=[row['grid_thw']]:raise ValueError('Current processor grid changed')
            torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize();began=time.monotonic()
            budget['attempts'].append({'id':row['id'],'started_unix':time.time()});save_json(budget_path,budget)
            with torch.inference_mode():
                result=vision(batch['pixel_values'].to('cuda',dtype=torch.bfloat16),grid_thw=grid.to('cuda'),return_dict=True)
                features=result.pooler_output.detach().cpu();del result
            torch.cuda.synchronize();seconds=time.monotonic()-began
            if features.shape!=(row['image_tokens'],conf.out_hidden_size) or not torch.isfinite(features).all():
                raise ValueError('Invalid actual projected visual features')
            dest=run/(row['id']+'.bf16.npy');tmp=dest.with_suffix('.tmp')
            with tmp.open('wb') as handle:np.save(handle,features.view(torch.uint16).numpy(),allow_pickle=False);handle.flush();os.fsync(handle.fileno())
            os.replace(tmp,dest)
            record={**row,'feature_file':str(dest.relative_to(ROOT)),'feature_sha256':digest(dest),'shape':list(features.shape),
                    'encoder_seconds':seconds,'peak_allocated_bytes':torch.cuda.max_memory_allocated(),
                    'peak_reserved_bytes':torch.cuda.max_memory_reserved(),'status':'passed_encoder_only'}
            save_json(commit,record);report['cases'].append(record);save_json(report_path,report)
            print('Encoder',len(report['cases']),'/220',row['dataset'],round(seconds,3),'s',flush=True);del batch,features
        report['status']='passed_encoder_only'
    except Exception as exc:report.update(status='failed',error=repr(exc),traceback=traceback.format_exc())
    finally:
        signal.alarm(0);signal.signal(signal.SIGALRM,previous)
        report.update(session_seconds=time.monotonic()-started,elapsed_seconds=time.time()-budget['started_unix'],
                      initiated_forwards=len(budget['attempts']),completed_forwards=len(report['cases']),formal_started=False)
        save_json(report_path,report)
    return report


def _admission_feature_case(item):
    """A stable worker owns one physical core; cumulative RSS is conservative."""
    import math
    import resource
    import numpy as np
    from multiprocessing import current_process
    from .utils import rewire_covariates,matched_rewire,select_registered_condition,objective,audit_selected_quality,audit_rewired_graph,visual_gather_plan
    row,mode,cores=item;os.sched_setaffinity(0,{cores[(current_process()._identity[0]-1)%len(cores)]})
    out=OUT/'cpu_admission_v5';base=ROOT/row['base'];oid=row['id'];target=out/mode/oid
    marker=target/'completed.json'
    if marker.exists():return read_json(marker)
    began=time.monotonic();record={'id':oid,'dataset':row['dataset'],'status':'failed'}
    try:
        path=ROOT/row['feature_file']
        if digest(path)!=row['feature_sha256']:raise ValueError('Feature cache identity changed')
        f=(np.load(path,allow_pickle=False).astype(np.uint32)<<16).view(np.float32)
        s=read_json(base/'token_support.json');p=read_json(base/'provenance.json');h,w=s['grid']
        if digest(base/'token_support.json')!=row['support_sha256'] or digest(base/'provenance.json')!=row['provenance_sha256']:
            raise ValueError('Support/provenance changed')
        xy=np.array([[t%w,t//w] for t in range(s['image_tokens'])],dtype=np.float32)
        if mode=='covariates':
            cov=rewire_covariates(p,s,f,xy,math.prod(row['original_pixels']))
            record.update(status='passed',edges=p['edges'],covariates=cov,diagonal=math.hypot(w,h))
        elif mode=='selection':
            meta=read_json(out/'covariates'/oid/'completed.json');bins=read_json(out/'full_roster_bins.json')
            with np.load(out/'input_geometry'/(oid+'.npz'),allow_pickle=False) as geometry:
                input_ids=geometry['input_ids'];position_ids=geometry['position_ids'];attention_mask=geometry['attention_mask'];image_token_id=int(geometry['image_token_id'])
            seed=int(stable_hash(['rq41_saturation_rewire_v3',oid])[:16],16)
            rewired,audit=matched_rewire(p['edges'],meta['covariates'],bins,meta['diagonal'],seed)
            audit['independent_invariants']=audit_rewired_graph(p['edges'],rewired,meta['covariates'],bins,meta['diagonal'])
            save_json(target/'rewire.json',{'edges':rewired,'audit':audit,'bins_sha256':digest(out/'full_roster_bins.json')})
            cfg=read_json(RQ/'configs/comparison_coding_plan_v1.json');masks={};record['conditions']={}
            conditions=read_json(RQ/'configs/encoder_admission_v5.json')['matched_conditions']
            for arm in conditions:
                clock=time.monotonic()
                try:
                    result=select_registered_condition(cfg,arm,f,xy,s['roles'],s['anchors'],rewired if arm=='REWIRED_E50' else p['edges'],seconds=30)
                    elapsed=time.monotonic()-clock;peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
                    if elapsed>30:raise TimeoutError('Measured selector wall time exceeds30seconds')
                    budget=result['budget'];ids=result['indices'];allowed=set(s['anchors'])|set().union(*(set(r['tokens']) for r in s['roles'].values()))
                    if len(ids)!=budget['total_tokens'] or len(set(ids))!=len(ids) or not set(s['anchors'])<=set(ids)<=allowed:
                        raise ValueError('Selection identity/domain/count mismatch')
                    result.update(status='passed',selector_wall_seconds=elapsed,peak_process_rss_bytes=peak,
                                  true_graph_objective=objective(result['quality'],p['edges']),rewired_graph_objective=objective(result['quality'],rewired))
                    audit_start=time.monotonic()
                    result['independent_quality']=audit_selected_quality(f,xy,s['roles'],ids,result['quality'])
                    result['quality_audit_seconds']=time.monotonic()-audit_start
                    plan=visual_gather_plan(input_ids,position_ids,attention_mask,image_token_id,ids)
                    if plan['input_tokens']!=len(ids)+plan['text_tokens'] or plan['input_tokens']+8192>40960:
                        raise ValueError('Pruned actual-input count/context changed')
                    retained=plan['retained_input_indices'];before=input_ids[(attention_mask==1)&(input_ids!=image_token_id)]
                    after=input_ids[retained];after=after[after!=image_token_id]
                    if not np.array_equal(before,after):raise ValueError('Text instructions altered by pruning')
                    result['native_gather_audit']={'status':'passed','input_tokens':plan['input_tokens'],'text_tokens':plan['text_tokens'],
                        'next_text_position':plan['next_text_position'],'mrope_sha256':__import__('hashlib').sha256(plan['retained_position_ids'].tobytes()).hexdigest(),
                        'all_original_nonpadding_text_preserved':True,'original_visual_positions_preserved':True}
                    masks[arm]=set(ids)
                except Exception as exc:result={'status':'failed','error':repr(exc),'seconds':time.monotonic()-clock,'traceback':traceback.format_exc()}
                save_json(target/(arm+'.json'),result)
                record['conditions'][arm]={k:v for k,v in result.items() if k not in {'indices','quality','traceback'}}
            record['rewire']=audit
            if {'CVC_E50','REWIRED_E50'}<=set(masks):
                a,b=masks['CVC_E50'],masks['REWIRED_E50'];anchors=set(s['anchors']);aa,bb=a-anchors,b-anchors
                record['comparison']={'mask_changed':a!=b,'symmetric_difference':len(a^b),'jaccard':len(a&b)/len(a|b),
                    'optional_jaccard':len(aa&bb)/len(aa|bb) if aa|bb else 1.,
                    'rewire_status':'mask_changed' if a!=b else ('graph_changed_mask_same' if audit['graph_changed'] else 'graph_unchanged')}
            record['status']='passed' if all(r['status']=='passed' for r in record['conditions'].values()) else 'failed'
        else:raise ValueError('Unknown CPU feature stage')
    except Exception as exc:record.update(error=repr(exc),traceback=traceback.format_exc())
    record.update(seconds=time.monotonic()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                  pid=os.getpid(),physical_core=next(iter(os.sched_getaffinity(0))))
    save_json(marker,record);return record


def admission_feature_audit(mode):
    from concurrent.futures import ProcessPoolExecutor
    from .utils import fit_rewire_bins
    if mode not in {'covariates','selection'}:raise ValueError('Unknown feature audit stage')
    out=OUT/'cpu_admission_v5';encoder=read_json(out/'encoder/report.json')
    if encoder['status']!='passed_encoder_only' or len(encoder['cases'])!=220:raise ValueError('Incomplete current feature cohort')
    if mode=='selection':
        metadata=read_json(out/'covariates/report.json')
        if metadata['status']!='passed':raise ValueError('Incomplete full-roster covariates')
        if read_json(out/'input_geometry/report.json')['status']!='passed':raise ValueError('Native input geometry not qualified')
        bins=fit_rewire_bins(metadata['cases']);bin_path=out/'full_roster_bins.json'
        if bin_path.exists() and read_json(bin_path)!=bins:raise ValueError('Frozen cohort bins changed')
        save_json(bin_path,bins)
    folder=out/mode;folder.mkdir(exist_ok=True);cores=physical_cores(8);began=time.monotonic();rows=[]
    # Stable spawn workers keep distinct physical cores for their entire lives.
    # Process-lifetime high-water RSS includes prior tasks and the audit: this
    # is a conservative upper bound, not a reset or per-call allocation claim.
    import multiprocessing
    with ProcessPoolExecutor(max_workers=len(cores),mp_context=multiprocessing.get_context('spawn')) as pool:
        for row in pool.map(_admission_feature_case,[(r,mode,cores) for r in encoder['cases']],chunksize=1):
            rows.append(row)
            if len(rows)%10==0:print('CPU',mode,len(rows),'/220',flush=True)
    report={'status':'passed' if len(rows)==220 and all(r['status']=='passed' for r in rows) else 'failed',
            'cases':rows,'seconds':time.monotonic()-began,'workers':len(cores),'physical_cores':cores,'llm_calls':0,'cpu_qualified':False}
    if mode=='selection':
        report['datasets']={}
        for ds,n in [('aiops2022',60),('aiops2025',60),('aegislab',100)]:
            rr=[r for r in rows if r['dataset']==ds];changed=sum(r.get('comparison',{}).get('mask_changed',False) for r in rr)
            available=sum(r.get('conditions',{}).get('CVC_E50',{}).get('status')=='passed' for r in rr)
            report['datasets'][ds]={'registered':n,'CVC_available':available,'mask_changed':changed,'changed_fraction':changed/n,
                                   'passed':len(rr)==available==n and changed/n>=.5}
        report['full_roster_dependency_mask_gate_passed']=all(r['passed'] for r in report['datasets'].values())
        if not report['full_roster_dependency_mask_gate_passed']:report['status']='failed'
    save_json(folder/'report.json',report);return report


def admission_input_geometry():
    """Actual processor plus native coordinate helper; no model construction."""
    import numpy as np
    import torch
    from types import SimpleNamespace,MethodType
    from PIL import Image
    from transformers import AutoConfig,AutoProcessor
    from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5Model
    from .utils import visual_gather_plan
    assigned_cores=physical_cores(8)[4:]
    os.sched_setaffinity(0,set(assigned_cores));torch.set_num_threads(4)
    out=OUT/'cpu_admission_v5/input_geometry';out.mkdir(exist_ok=False)
    cfg=read_json(RQ/'configs/encoder_admission_v5.json');directory=cfg['model_path']
    conf=AutoConfig.from_pretrained(directory,local_files_only=True);processor=AutoProcessor.from_pretrained(directory,local_files_only=True)
    helper=SimpleNamespace(config=conf)
    helper.get_vision_position_ids=MethodType(Qwen3_5Model.get_vision_position_ids,helper)
    messages=[{'role':'system','content':exps.SYSTEM},{'role':'user','content':[{'type':'image'},{'type':'text','text':exps.VISUAL_TASK}]}]
    prompt=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False,preserve_thinking=False)
    results=[];began=time.monotonic()
    for row in cfg['cases']:
        base=ROOT/row['base'];im=Image.open(ROOT/row['png']).convert('RGB')
        if digest(ROOT/row['png'])!=row['png_sha256']:raise ValueError('Input geometry PNG identity changed')
        batch=processor(text=[prompt],images=[im],return_tensors='pt')
        position,delta=Qwen3_5Model.get_rope_index(helper,batch['input_ids'],mm_token_type_ids=batch['mm_token_type_ids'],
                            image_grid_thw=batch['image_grid_thw'],attention_mask=batch['attention_mask'])
        ids=batch['input_ids'][0].numpy();pos=position[:,0].numpy();mask=batch['attention_mask'][0].numpy()
        native=visual_gather_plan(ids,pos,mask,conf.image_token_id,list(range(row['image_tokens'])))
        if not np.array_equal(native['retained_input_indices'],np.arange(len(ids))) or native['rope_delta_after_gather']!=int(delta[0]):
            raise ValueError('Identity gather differs from native coordinate helper')
        if len(ids)!=read_json(base/'processor_cpu.json')['counts']['V_FULL']:raise ValueError('Actual request token count changed')
        path=out/(row['id']+'.npz')
        np.savez_compressed(path,input_ids=ids,position_ids=pos,attention_mask=mask,image_token_id=np.array(conf.image_token_id))
        results.append({'id':row['id'],'dataset':row['dataset'],'status':'passed','png_sha256':row['png_sha256'],
                        'input_tokens':len(ids),'visual_tokens':row['image_tokens'],'text_tokens':native['text_tokens'],
                        'next_text_position':native['next_text_position'],'path':str(path.relative_to(ROOT)),'sha256':digest(path)})
        if len(results)%20==0:print('CPU input geometry',len(results),'/220',flush=True)
        del batch,im,position,ids,pos,mask
    report={'status':'passed','cases':results,'seconds':time.monotonic()-began,'model_constructed':False,
            'llm_calls':0,'cuda_visible':os.getenv('CUDA_VISIBLE_DEVICES'),'CPU_physical_cores':sorted(os.sched_getaffinity(0))}
    save_json(out/'report.json',report);return report


def extract_saturation_features():
    """Three registered encoder-only forwards; no language model is loaded."""
    import signal
    import numpy as np
    config_path=RQ/'configs/saturation_probe_v3.json';cfg=read_json(config_path)
    out=OUT/'saturation_probe_v3';run=out/'encoder';run.mkdir(exist_ok=False)
    started=time.monotonic();report={'status':'running','llm_calls':0,'encoder_forwards':0,'cases':[]}
    def deadline(*_):raise TimeoutError('Registered encoder-only deadline')
    budget_path=out/'encoder_budget.json'
    if not budget_path.exists():save_json(budget_path,{'started_unix':time.time(),'max_forwards':3})
    remaining=int(cfg['encoder_wall_seconds']-(time.time()-read_json(budget_path)['started_unix']))
    if remaining<=0:raise TimeoutError('Shared encoder deadline exhausted')
    previous=signal.signal(signal.SIGALRM,deadline);signal.alarm(remaining)
    try:
        import torch
        import transformers
        from PIL import Image
        from safetensors import safe_open
        from transformers import AutoProcessor,AutoConfig
        from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5VisionModel
        os.sched_setaffinity(0,physical_cores(4));torch.set_num_threads(4)
        torch.cuda.set_per_process_memory_fraction(cfg['gpu_allocator_fraction'],0)
        directory=Path(cfg['model_path']);conf=AutoConfig.from_pretrained(directory,local_files_only=True).vision_config
        conf._attn_implementation='sdpa'
        # Construct nonpersistent RoPE buffers too; meta+assign leaves these
        # buffer values uninitialized even when all checkpoint keys match.
        vision=Qwen3_5VisionModel(conf)
        index=read_json(directory/'model.safetensors.index.json')['weight_map'];prefix='model.visual.'
        shards=sorted({v for k,v in index.items() if k.startswith(prefix)});state={};weights_hash={}
        for shard in shards:
            with safe_open(directory/shard,framework='pt',device='cpu') as handle:
                for key in handle.keys():
                    if key.startswith(prefix):
                        value=handle.get_tensor(key);state[key[len(prefix):]]=value
                        import hashlib
                        weights_hash[key]=hashlib.sha256(value.view(torch.uint16).numpy().tobytes()).hexdigest()
        vision.load_state_dict(state,strict=True,assign=True);del state
        vision=vision.to(device='cuda',dtype=torch.bfloat16).eval().requires_grad_(False)
        processor=AutoProcessor.from_pretrained(directory,local_files_only=True)
        save_json(run/'freeze.json',{'config_hash':digest(config_path),'vision_weight_hashes':weights_hash,
            'model_config':digest(directory/'config.json'),'processor_config':digest(directory/'preprocessor_config.json'),
            'torch':torch.__version__,'transformers':transformers.__version__,'source_hash':digest(__file__),
            'language_decoder_loaded':False,'attention_collection':False})
        print('Encoder only loaded; language decoder absent',flush=True)
        for row in cfg['cases']:
            if report['encoder_forwards']>=cfg['max_encoder_passes']:raise RuntimeError('Encoder pass cap')
            path=ROOT/row['png'];assert digest(path)==row['png_sha256']
            support=read_json(OUT/'shared_confirmed_v2'/row['id']/'token_support.json')
            batch=processor.image_processor(images=Image.open(path).convert('RGB'),return_tensors='pt')
            grid=batch['image_grid_thw'];assert grid.tolist()==[[1,support['grid'][0]*2,support['grid'][1]*2]]
            torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize();began=time.monotonic()
            report['encoder_forwards']+=1;save_json(run/'report.json',report)
            with torch.inference_mode():
                result=vision(batch['pixel_values'].to('cuda',dtype=torch.bfloat16),grid_thw=grid.to('cuda'),return_dict=True)
                features=result.pooler_output.detach().cpu();del result
            torch.cuda.synchronize();elapsed=time.monotonic()-began
            assert features.shape==(support['image_tokens'],conf.out_hidden_size) and torch.isfinite(features).all()
            dest=run/(row['id']+'.bf16.npy');np.save(dest,features.view(torch.uint16).numpy(),allow_pickle=False)
            record={**row,'shape':list(features.shape),'feature_file':str(dest.relative_to(ROOT)),
                'feature_sha256':digest(dest),'seconds':elapsed,'peak_allocated_bytes':torch.cuda.max_memory_allocated(),
                'peak_reserved_bytes':torch.cuda.max_memory_reserved(),'image_grid_thw':grid.tolist()}
            report['cases'].append(record);save_json(run/'report.json',report)
            print(row['dataset'],row['id'],elapsed,'seconds',flush=True);del features,batch
        report['status']='passed_encoder_only'
    except Exception as exc:
        report.update(status='failed',error=repr(exc),traceback=traceback.format_exc())
    finally:
        signal.alarm(0);signal.signal(signal.SIGALRM,previous)
        report['elapsed_seconds']=time.monotonic()-started;report['formal_started']=False
        save_json(run/'report.json',report)
    return report


def saturation_selector_probe():
    """CPU-only use of the three committed real encoder tensors."""
    import math
    import resource
    import numpy as np
    from .utils import rewire_covariates,fit_rewire_bins,matched_rewire,select_tokens,objective
    cfg=read_json(RQ/'configs/saturation_probe_v3.json');root=OUT/'saturation_probe_v3'
    extracted=read_json(root/'encoder/report.json');assert extracted['status']=='passed_encoder_only'
    out=root/'selection';out.mkdir(exist_ok=False);os.sched_setaffinity(0,physical_cores(1))
    def load_features(row):
        path=ROOT/row['feature_file'];assert digest(path)==row['feature_sha256']
        return (np.load(path,allow_pickle=False).astype(np.uint32)<<16).view(np.float32)
    cases=[]
    for row in extracted['cases']:
        oid=row['id'];s=read_json(OUT/'shared_confirmed_v2'/oid/'token_support.json')
        p=read_json(OUT/'foreground_v1'/oid/'provenance.json');h,w=s['grid']
        xy=np.array([[t%w,t//w] for t in range(s['image_tokens'])],dtype=np.float32)
        f=load_features(row);cov=rewire_covariates(p,s,f,xy,math.prod(row['original_pixels']));del f
        cases.append({'id':oid,'edges':p['edges'],'covariates':cov,'diagonal':math.hypot(w,h)})
    bins=fit_rewire_bins(cases);save_json(out/'three_case_bins.json',bins)
    summary={'status':'running','cases':[],'llm_calls':0,'full_cpu_qualified':False,'full_roster_bins':False}
    for row,meta in zip(extracted['cases'],cases,strict=True):
        oid=row['id'];s=read_json(OUT/'shared_confirmed_v2'/oid/'token_support.json');h,w=s['grid'];f=load_features(row)
        xy=np.array([[t%w,t//w] for t in range(s['image_tokens'])],dtype=np.float32)
        seed=int(stable_hash(['rq41_saturation_rewire_v3',oid])[:16],16)
        rewired,audit=matched_rewire(meta['edges'],meta['covariates'],bins,meta['diagonal'],seed)
        save_json(out/oid/'rewire.json',{'audit':audit,'edges':rewired,'covariates':meta['covariates']})
        record={'id':oid,'dataset':row['dataset'],'rewire':audit,'conditions':{}}
        for policy,modes in [('grid_v2',['CVC','REWIRED','UNARY']),('optional_support_v3',['CVC','REWIRED','UNARY','UNIFORM','QUOTA'])]:
            for mode in modes:
                label=policy+'__'+mode;began=time.monotonic()
                try:
                    chosen=rewired if mode=='REWIRED' else meta['edges']
                    result=select_tokens(f,xy,s['roles'],s['anchors'],chosen,.5,mode,seconds=cfg['selector_seconds'],budget_policy=policy)
                    result['status']='passed';result['true_graph_objective']=objective(result['quality'],meta['edges'])
                    result['rewired_graph_objective']=objective(result['quality'],rewired)
                    result['peak_process_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
                except Exception as exc:result={'status':'failed','error':repr(exc),'seconds':time.monotonic()-began}
                save_json(out/oid/(label+'.json'),result)
                record['conditions'][label]={k:v for k,v in result.items() if k not in {'indices','quality'}}
                print(row['dataset'],label,result['status'],round(result['seconds'],3),flush=True)
        for policy in ['grid_v2','optional_support_v3']:
            a=read_json(out/oid/(policy+'__CVC.json'));b=read_json(out/oid/(policy+'__REWIRED.json'))
            if a['status']==b['status']=='passed':
                sa,sb=set(a['indices']),set(b['indices']);optional=set().union(*(set(r['tokens']) for r in s['roles'].values()))
                record[policy]={'mask_changed':sa!=sb,'symmetric_difference':len(sa^sb),'jaccard':len(sa&sb)/len(sa|sb),
                    'true_all_optional_selected':optional<=sa,'rewired_all_optional_selected':optional<=sb,
                    'true_optional_omitted':len(optional-sa),'tokens':len(sa),'grid_fraction':len(sa)/s['image_tokens']}
        summary['cases'].append(record);save_json(out/'report.json',summary);del f
    summary['status']='passed' if all(v['status']=='passed' for r in summary['cases'] for v in r['conditions'].values()) else 'partial_failure'
    save_json(out/'report.json',summary);return summary


def _render_cpu_case(item):
    row,root,cores=item
    from multiprocessing import current_process
    # A stable process identity selects one distinct core for its lifetime.
    core=cores[(current_process()._identity[0]-1)%len(cores)]
    os.sched_setaffinity(0,{core})
    from renderer.main import render
    oid=row['opaque_incident_id'];base=Path(root)/oid
    prepared=exps.compile_case(read_json(exps.SOURCE/(oid+'.json')))
    save_json(base/'evidence.json',prepared['evidence']);save_json(base/'design.json',prepared['design'])
    result={'id':oid,'dataset':row['dataset'],'source_mapping':len(prepared['mapping'])}
    try:
        report=render(base/'evidence.json',base/'design.json',base/'render')
        result.update(status=report['status'],png_sha256=report['png_sha256'],viewport=prepared['design']['viewport'])
    except Exception as exc:
        result.update(status='failed',error=str(exc))
        p=base/'render/manifest.json'
        if p.exists():result['issues']=read_json(p).get('audit',{}).get('issues',[])
    return result


def render_roster():
    from concurrent.futures import ProcessPoolExecutor
    out=OUT/'gallery_v2'
    if out.exists():raise FileExistsError('Preserve existing gallery; no implicit overwrite')
    out.mkdir(parents=True)
    rows=source_order(read_json(exps.REGISTRATION)['cases']);cores=physical_cores(4)
    started=time.monotonic()
    # Each process explicitly pins its task plus its renderer descendants to
    # one physical core. Four processes cannot exceed the eight-core cap.
    items=[(row,str(out),cores) for row in rows]
    results=[]
    with ProcessPoolExecutor(max_workers=len(cores)) as pool:
        for result in pool.map(_render_cpu_case,items,chunksize=1):
            results.append(result)
            if len(results)%10==0:print('Actual unified PNG audit',len(results),'/ 220',flush=True)
    report={'status':'passed' if all(r['status']=='passed' for r in results) else 'failed',
            'cases':results,'elapsed_seconds':time.monotonic()-started,'gpu_calls':0,
            'scope':'renderer only, not complete CPU qualification','physical_cores':cores}
    save_json(out/'report.json',report)
    return report


def processor_roster():
    """CPU processor and conservative all-visible-ink occupancy, no model."""
    import numpy as np
    from PIL import Image
    import torch
    from transformers import AutoProcessor
    os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    os.sched_setaffinity(0,physical_cores(8));torch.set_num_threads(8)
    processor=AutoProcessor.from_pretrained('/home/lglsj/CanvasRCA/models/Qwen3.8-27B',local_files_only=True)
    messages=[{'role':'system','content':exps.SYSTEM},{'role':'user','content':[{'type':'image'},{'type':'text','text':exps.VISUAL_TASK}]}]
    prompt=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False,preserve_thinking=False)
    gallery=OUT/'gallery_v2';rendered=read_json(gallery/'report.json');results=[]
    for index,r in enumerate(rendered['cases']):
        if r['status']!='passed':results.append({'id':r['id'],'dataset':r['dataset'],'status':'render_failed'});continue
        base=gallery/r['id'];im=Image.open(base/'render/dashboard.png').convert('RGB')
        batch=processor(text=[prompt],images=[im],return_tensors='pt')
        t,h,w=batch['image_grid_thw'][0].tolist();n=t*h*w//4
        pixels=batch['pixel_values'].reshape(t,h//2,w//2,2,2,3,2,16,16).permute(0,6,5,1,3,7,2,4,8).reshape(t*2,3,h*16,w*16)[0]
        arr=((pixels*.5+.5)*255).round().clamp(0,255).to(torch.uint8).permute(1,2,0).numpy()
        # Includes borders, header and every visible raster difference from
        # both registered solid backgrounds; not yet a canonical role mask.
        ink=np.logical_and(np.any(arr!=[16,24,33],axis=2),np.any(arr!=[24,36,47],axis=2))
        occupied=ink.reshape(h//2,32,w//2,32).any(axis=(1,3))
        text_parts=read_json(exps.SOURCE/(r['id']+'.json'))['texts']['RAW_TEXT']
        text_messages=[{'role':'system','content':exps.SYSTEM},{'role':'user','content':text_parts}]
        full_text=processor.apply_chat_template(text_messages,tokenize=False,add_generation_prompt=True,enable_thinking=False,preserve_thinking=False)
        text_tokens=len(processor.tokenizer(full_text,add_special_tokens=False)['input_ids'])
        row={'id':r['id'],'dataset':r['dataset'],'status':'context_passed' if batch['input_ids'].shape[1]+8192<=40960 and text_tokens+8192<=40960 else 'context_failed',
            'source_png':list(im.size),'processed_pixels':[w*16,h*16],'image_tokens':n,
            'input_tokens':batch['input_ids'].shape[1],'full_text_tokens':text_tokens,
            'visible_ink_tiles':int(occupied.sum()),'half_token_budget':(n+1)//2,
            'all_ink_fits_half':bool(occupied.sum()<=(n+1)//2),
            'occupancy_scope':'RGB foreground upper screen, not source-provenance or final selector-mask qualification'}
        save_json(base/'processor_cpu.json',row);results.append(row)
        if (index+1)%20==0:print('Actual CPU processor',index+1,'/ 220',flush=True)
        del batch,pixels,arr,im,ink,occupied
    summary={'status':'screen_complete','cases':results,'gpu_calls':0,'context_passed':sum(r['status']=='context_passed' for r in results)}
    save_json(gallery/'processor_report.json',summary)
    return summary


def _foreground_case(item):
    row,out,cores=item
    from multiprocessing import current_process
    from renderer.main import render
    os.sched_setaffinity(0,{cores[(current_process()._identity[0]-1)%len(cores)]})
    oid=row['opaque_incident_id'];base=Path(out)/oid;started=time.monotonic()
    result={'id':oid,'dataset':row['dataset'],'status':'failed'}
    try:
        public=read_json(exps.SOURCE/(oid+'.json'));compiled=exps.compile_case(public)
        provenance=exps.comparison_provenance(compiled,public)
        compiled['design']['provenance']=provenance['foreground']
        for name,data in [('evidence',compiled['evidence']),('design',compiled['design']),('provenance',provenance)]:
            save_json(base/(name+'.json'),data)
        rendered=render(base/'evidence.json',base/'design.json',base/'render')
        prior=OUT/'gallery_v2'/oid
        if rendered['png_sha256']!=digest(prior/'render/dashboard.png'):
            raise ValueError('Audit operation changed model-visible PNG')
        proc=read_json(prior/'processor_cpu.json')
        support=foreground_support(base/'render',proc['processed_pixels'])
        save_json(base/'token_support.json',support)
        roles={r['id']:r for r in provenance['roles']}
        # These uncomplicated numerical fields have independent original-source
        # identities. Separate them from unfinished nested statistic typing.
        reliable=[]
        for rid in support['definite_empty_unanchored_roles']:
            r=roles[rid]
            if r['quantity'] not in {'/baseline','/peak','/signed_z','/sircl_met_z/current_mean','/sircl_met_z/current_std_dev','/sircl_met_z/regular_mean','/sircl_met_z/regular_std_dev'}:continue
            source_id=r['source_occurrence'].split('/')[0]
            origin=next(v['value'] for v in compiled['ledger']['records'] if v['source']==source_id)
            values=dict(exps.leaves(origin));value=values[r['quantity']]
            exps.numeric(value)
            if value is None:raise ValueError('Missing source cannot be a numeric witness')
            reliable.append({'role':r,'original_source_value':value,'support':support['roles'][rid],
                'competing_roles':{w['other_role']:roles[w['other_role']] for w in support['roles'][rid]['loss_witness']}})
        save_json(base/'independent_numeric_witnesses.json',reliable)
        result.update(status='failed_empty_role_support' if reliable else 'mapping_requires_review',
            main_png_unchanged=True,image_tokens=support['image_tokens'],anchors=len(support['anchors']),
            half_budget=(support['image_tokens']+1)//2,role_count=len(roles),
            definite_empty_roles=len(support['definite_empty_unanchored_roles']),
            uncertain_empty_roles=len(support['uncertain_empty_unanchored_roles']),
            independent_numeric_failure_witnesses=len(reliable),
            ambiguous_tokens=support['ambiguous_tokens'],foreground_union_tokens=support['foreground_union_tokens'])
    except Exception as exc:
        result.update(error=repr(exc))
    result['seconds']=time.monotonic()-started
    save_json(base/'report.json',result)
    return result


def foreground_roster():
    """Pre-model necessary-condition audit; never fabricates features/masks."""
    from concurrent.futures import ProcessPoolExecutor
    out=OUT/'foreground_v1'
    if out.exists():raise FileExistsError('Keep earlier audit immutable')
    out.mkdir(parents=True);cores=physical_cores(4)
    rows=source_order(read_json(exps.REGISTRATION)['cases']);start=time.monotonic();results=[]
    with ProcessPoolExecutor(max_workers=4) as pool:
        for result in pool.map(_foreground_case,[(r,str(out),cores) for r in rows],chunksize=1):
            results.append(result)
            if len(results)%10==0:print('Actual canonical foreground',len(results),'/220',flush=True)
    counts={d:{'total':sum(r['dataset']==d for r in results),
               'definite_numeric_mapping_failure':sum(r['dataset']==d and r.get('independent_numeric_failure_witnesses',0)>0 for r in results)}
            for d in ('aiops2022','aiops2025','aegislab')}
    report={'status':'failed' if any(r.get('independent_numeric_failure_witnesses',0) for r in results) else 'pending_review',
            'gate':'every_unanchored_canonical_role_has_optional_support','cases':results,'datasets':counts,
            'cpu_qualified':False,'gpu_calls_started':0,'gpu_smoke':'not_run','formal_started':False,
            'elapsed_seconds':time.monotonic()-start,'workers':4,'physical_cores':cores,
            'encoder_features':'not_extracted; necessary support gate does not depend on features',
            'rewired_final_masks':'not_run; no claim of measured changed-mask rate',
            'scope':'necessary condition only; complete semantic audit and runtime implementation not claimed'}
    save_json(out/'report.json',report)
    return report


def _shared_support_case(item):
    row,out,cores=item
    from multiprocessing import current_process
    os.sched_setaffinity(0,{cores[(current_process()._identity[0]-1)%len(cores)]})
    oid=row['opaque_incident_id'];base=Path(out)/oid;old=OUT/'foreground_v1'/oid;start=time.monotonic()
    result={'id':oid,'dataset':row['dataset'],'status':'failed'}
    try:
        manifest=read_json(old/'render/manifest.json')
        if digest(old/'render/dashboard.png')!=manifest['png_sha256']:raise ValueError('Frozen diagnostic PNG changed')
        processor=read_json(OUT/'gallery_v2'/oid/'processor_cpu.json')
        support=foreground_support(old/'render',processor['processed_pixels'],policy='shared_v2')
        previous=read_json(old/'token_support.json');provenance=read_json(old/'provenance.json')
        if {r['id'] for r in provenance['roles']}!=set(support['roles']):raise ValueError('Canonical role inventory changed')
        if previous['anchors']!=support['anchors']:raise ValueError('Shared support changed anchors')
        empty=[u for u,r in support['roles'].items() if not r['tokens'] and not r['fully_anchored']]
        formerly_empty=[u for u,r in previous['roles'].items() if not r['tokens'] and not r['fully_anchored']]
        repaired=[u for u in formerly_empty if u not in empty]
        saturation={str(r):support_saturation(support['roles'],support['anchors'],support['image_tokens'],r) for r in (.25,.5,.75)}
        save_json(base/'token_support.json',support)
        result.update(status='passed' if not empty else 'failed_empty_support',empty_roles=empty,
            formerly_empty_roles=len(formerly_empty),repaired_roles=len(repaired),roles=len(support['roles']),
            uncertain_only_optional_roles=support['uncertain_only_unanchored_roles'],
            shared_nonanchor_tokens=support['shared_nonanchor_tokens'],max_roles_per_token=support['max_roles_per_token'],
            unique_foreground_union=support['foreground_union_tokens'],role_token_incidences=support['role_token_incidences'],
            image_tokens=support['image_tokens'],anchors=len(support['anchors']),saturation=saturation,
            png_sha256=manifest['png_sha256'],source='../../foreground_v1/'+oid,
            actual_heuristic_masks_measured=False,gpu_calls=0)
    except Exception as exc:result['error']=repr(exc)
    result['seconds']=time.monotonic()-start;save_json(base/'report.json',result);return result


def shared_support_roster():
    """All220 cached actual foreground rasters; no render/model replay."""
    from concurrent.futures import ProcessPoolExecutor
    out=OUT/'shared_support_v2'
    if out.exists():raise FileExistsError('Preserve earlier revision audit')
    out.mkdir(parents=True);cores=physical_cores(4)
    old=read_json(OUT/'qualification_failure_snapshot.json')
    if digest(RQ/'src/exps.py')!=old['code']['RQs/RQ4_1/src/exps.py']:
        raise ValueError('Compiler changed; cannot inherit frozen source/PNG checks')
    for oid,sha in old['source_packets'].items():
        if digest(exps.SOURCE/(oid+'.json'))!=sha:raise ValueError('Frozen public source changed')
    rows=source_order(read_json(exps.REGISTRATION)['cases']);start=time.monotonic();results=[]
    with ProcessPoolExecutor(max_workers=4) as pool:
        for result in pool.map(_shared_support_case,[(r,str(out),cores) for r in rows],chunksize=1):
            results.append(result)
            if len(results)%20==0:print('Shared canonical support',len(results),'/220',flush=True)
    datasets={d:{'total':sum(r['dataset']==d for r in results),
        'nonempty_support_passed':sum(r['dataset']==d and r['status']=='passed' for r in results),
        'old_empty_roles_repaired':sum(r.get('repaired_roles',0) for r in results if r['dataset']==d),
        'cases_with_uncertain_only_optional_roles':sum(bool(r.get('uncertain_only_optional_roles')) for r in results if r['dataset']==d),
        'all_support_fits_half_budget':sum(r.get('saturation',{}).get('0.5',{}).get('all_support_fits',False) for r in results if r['dataset']==d)}
        for d in ('aiops2022','aiops2025','aegislab')}
    report={'status':'passed' if len(results)==220 and all(r['status']=='passed' for r in results) else 'failed',
        'scope':'shared nonempty support and feature-independent capacity only; not complete CPU qualification',
        'support_policy':'shared_v2','cases':results,'datasets':datasets,'workers':4,'physical_cores':cores,
        'elapsed_seconds':time.monotonic()-start,'renderer_reexecuted':False,'diagnostic_png_changed':False,
        'cpu_qualified':False,'gpu_calls':0,'actual_encoder_features':'not_extracted',
        'final_rewired_mask_gate':'not_measured','formal_started':False}
    save_json(out/'report.json',report);return report


def _confirm_shared_case(item):
    row,out,cores=item
    from multiprocessing import current_process
    from renderer.main import render
    os.sched_setaffinity(0,{cores[(current_process()._identity[0]-1)%len(cores)]})
    oid=row['opaque_incident_id'];base=Path(out)/oid;old=OUT/'foreground_v1'/oid;started=time.monotonic()
    result={'id':oid,'dataset':row['dataset'],'status':'failed'}
    try:
        support=read_json(OUT/'shared_support_v2'/oid/'token_support.json')
        spec=read_json(old/'design.json');registered={r['id']:r for r in spec['provenance']['roles']}
        expected=read_json(old/'render/manifest.json')['png_sha256'];anchors=set(support['anchors']);confirmed=[]
        for rid in support['uncertain_only_unanchored_roles']:
            design={**spec,'provenance':{'schema':'CanonicalForegroundV1','roles':[registered[rid]]}}
            part=base/'isolated'/rid;save_json(part/'design.json',design)
            rendered=render(old/'evidence.json',part/'design.json',part/'render')
            if rendered['png_sha256']!=expected:raise ValueError('Isolated audit changed diagnostic PNG')
            tokens=isolated_glyph_tokens(part/'render/role_foreground.png',support['processed_pixels'])
            if not tokens:raise ValueError('Registered canonical glyph has no foreground')
            r=support['roles'][rid];optional=sorted(set(tokens)-anchors);gh,gw=support['grid']
            x=[t%gw for t in tokens];y=[t//gw for t in tokens]
            r.update(tokens=optional,fully_anchored=not optional,confirmed_optional_tokens=optional,
                uncertain_only_tokens=[],foreground_possible_tokens=tokens,
                bbox_diag2=float((max(x)-min(x)+1)**2+(max(y)-min(y)+1)**2),
                isolated_confirmation_sha256=digest(part/'render/role_foreground.png'))
            confirmed.append({'role':rid,'fully_anchored':not optional,'optional_tokens':len(optional)})
        support['uncertain_only_unanchored_roles']=[]
        union=anchors|{t for r in support['roles'].values() for t in r['tokens']}
        multiplicity=Counter(t for r in support['roles'].values() for t in r['tokens'])
        support.update(foreground_union_tokens=len(union),role_token_incidences=sum(multiplicity.values()),
            shared_nonanchor_tokens=sum(v>1 for v in multiplicity.values()),max_roles_per_token=max(multiplicity.values(),default=0))
        empty=[u for u,r in support['roles'].items() if not r['tokens'] and not r['fully_anchored']]
        save_json(base/'token_support.json',support)
        result.update(status='passed' if not empty else 'failed_empty_support',empty_roles=empty,
            isolated_roles=confirmed,uncertain_only_roles_remaining=0,
            saturation={str(f):support_saturation(support['roles'],support['anchors'],support['image_tokens'],f) for f in (.25,.5,.75)},
            support_roles=len(support['roles']),unique_foreground_union=len(union),png_sha256=expected,gpu_calls=0)
    except Exception as exc:result['error']=repr(exc)
    result['seconds']=time.monotonic()-started;save_json(base/'report.json',result);return result


def confirm_shared_support():
    """Resolve uncertain-only optional support with isolated existing glyphs."""
    from concurrent.futures import ProcessPoolExecutor
    out=OUT/'shared_confirmed_v2'
    if out.exists():raise FileExistsError('Preserve prior qualification evidence')
    out.mkdir(parents=True);cores=physical_cores(4);results=[];started=time.monotonic()
    rows=source_order(read_json(exps.REGISTRATION)['cases'])
    with ProcessPoolExecutor(max_workers=4) as pool:
        for result in pool.map(_confirm_shared_case,[(r,str(out),cores) for r in rows],chunksize=1):
            results.append(result)
            if len(results)%20==0:print('Confirmed shared support',len(results),'/220',flush=True)
    datasets={d:{'total':sum(r['dataset']==d for r in results),
        'support_passed':sum(r['dataset']==d and r['status']=='passed' for r in results),
        'isolated_glyph_checks':sum(len(r.get('isolated_roles',[])) for r in results if r['dataset']==d),
        'all_support_fits_half_budget':sum(r.get('saturation',{}).get('0.5',{}).get('all_support_fits',False) for r in results if r['dataset']==d)}
        for d in ('aiops2022','aiops2025','aegislab')}
    report={'status':'passed' if len(results)==220 and all(r['status']=='passed' for r in results) else 'failed',
        'scope':'nonempty shared support; residual raster uncertainty retained; not complete CPU qualification',
        'cases':results,'datasets':datasets,'elapsed_seconds':time.monotonic()-started,
        'workers':4,'physical_cores':cores,'diagnostic_png_changed':False,'gpu_calls':0,
        'actual_rewired_masks':'not_measured','cpu_qualified':False,'formal_started':False}
    save_json(out/'report.json',report);return report


_REMAINING_PROCESSOR = None


def remaining_cpu_config():
    name=read_json(RQ/'configs/comparison_coding_plan_v1.json')['remaining_cpu_config']
    if Path(name).name!=name:raise ValueError('Unsafe remaining CPU config path')
    return read_json(RQ/'configs'/name)


def remaining_cpu_root():
    out=(ROOT/remaining_cpu_config()['output']).resolve()
    if not out.is_relative_to(OUT):raise ValueError('Remaining CPU output outside experiment')
    return out


def retained_variant(variant, ref):
    """Reuse a completed per-variant receipt, without reopening image artifacts."""
    receipt=ROOT/ref['receipt']
    if digest(receipt)!=ref['sha256']:raise ValueError('Retained variant receipt changed')
    local=read_json(receipt)
    if local['status']!='passed':raise ValueError('Retained variant did not pass')
    if stable_hash(variant['evidence'])!=ref['evidence_hash'] or stable_hash(variant['design'])!=ref['design_hash']:
        raise ValueError('Retained variant input changed')
    return {**local,'reused':True,'retained_receipt':ref['receipt'],'artifact_root':str(receipt.parent.relative_to(ROOT))}


def _remaining_case(item):
    """CPU-only source/renderer/processor qualification, no feature/model forward."""
    from multiprocessing import current_process
    from copy import deepcopy
    import numpy as np
    import resource
    from PIL import Image
    from renderer.main import render
    from renderer.utils import compile_design
    from transformers import AutoProcessor
    global _REMAINING_PROCESSOR
    row,mechanism,cores=item;os.sched_setaffinity(0,{cores[(current_process()._identity[0]-1)%len(cores)]})
    import torch
    torch.set_num_threads(1)
    if torch.cuda.is_initialized():raise RuntimeError('CPU stage initialized CUDA')
    oid=row['opaque_incident_id'];out=remaining_cpu_root()/'cases'/oid;marker=out/'completed.json'
    if marker.exists():return read_json(marker)
    out.mkdir(parents=True,exist_ok=True);began=time.monotonic()
    result={'id':oid,'dataset':row['dataset'],'mechanism':mechanism,'status':'failed','variants':{},'llm_calls':0}
    retained=remaining_cpu_config().get('retained_variants',{}).get(oid,{})
    try:
        public=read_json(exps.SOURCE/(oid+'.json'));c=exps.compile_case(public);prov=exps.comparison_provenance(c,public)
        source_base=admission_current_base(oid)
        # Reuse the completed base source audit; only new variants need auditing.
        audit=read_json(source_base/'source_audit.json')
        if audit['status']!='passed':raise ValueError('Retained source audit did not pass')
        result['base_source_audit_reused']=str((source_base/'source_audit.json').relative_to(ROOT))
        if stable_hash(c['evidence'])!=stable_hash(read_json(source_base/'evidence.json')):raise ValueError('Frozen primary evidence changed')
        if _REMAINING_PROCESSOR is None:
            _REMAINING_PROCESSOR=AutoProcessor.from_pretrained('/home/lglsj/CanvasRCA/models/Qwen3.8-27B',local_files_only=True)
        processor=_REMAINING_PROCESSOR
        variants={}
        if mechanism:
            qa=exps.qa_packet(public,c,prov,oid);save_json(out/'qa_audit.json',{k:v for k,v in qa.items() if k not in {'design','text_evidence'}})
            save_json(out/'qa_text.json',{'task':exps.QA_TASK,'evidence':qa['text_evidence']})
            result['qa_applicable_blocks']=qa['applicable_blocks']
            # Independent arithmetic and source-field verification, without labels.
            for block in qa['blocks']:
                for badge in ('A','B'):
                    p=block[badge];record=next(r for r in c['ledger']['records'] if r['source']==p['source'])
                    value=record['value']
                    for key in p['path'].split('/')[1:]:value=value[int(key)] if isinstance(value,list) else value[key.replace('~1','/').replace('~0','~')]
                    if exps.numeric(value)!=p['value']:raise ValueError('QA scalar differs from original record')
                    if p['binding_answer']['phase'] not in {'reference','current'}:raise ValueError('QA phase')
                a,b=(block[k]['displayed_value'] for k in ('A','B'))
                expected='equal_at_display_precision' if a==b else 'A_greater' if a>b else 'B_greater'
                if block['comparison']!=expected:raise ValueError('QA comparison oracle')
            text=processor.apply_chat_template([{'role':'system','content':'Answer only the independent factual QA task.'},
                {'role':'user','content':qa['text_evidence']+'\n'+exps.QA_TASK}],tokenize=False,add_generation_prompt=True,enable_thinking=False)
            text_count=len(processor.tokenizer.encode(text,add_special_tokens=False))
            if text_count+8192>40960:raise ValueError('QA full-text context')
            result['qa_text_input_tokens']=text_count
            if qa['applicable_blocks']:
                variants['QA']={'evidence':deepcopy(c['evidence']),'design':qa['design'],'provenance':prov,'audit':{'label_scoring_allowed':False,'facts_unchanged':True}}
            else:result['variants']['QA']={'status':'not_applicable','reason':'no_registered_scalar_pairs'}
            variants.update(exps.intervention_inputs(public,c,prov,oid,qa))
            for name in ('BINDING','OPERAND','IRRELEVANT'):
                if name not in variants:result['variants'][name]={'status':'not_applicable','reason':'no_public_geometry_match'}
        atlas=exps.compile_atlas(public,c);save_json(out/'atlas_audit.json',atlas['atlas_audit'])
        # Numpy is an independent quantile implementation, not the compiler helper.
        for r in atlas['atlas_audit']['rows']:
            ref=np.array(r['phases']['reference']);cur=np.array(r['phases']['current']);scale=1.4826*np.median(abs(ref-np.median(ref)))
            if scale==0:scale=(np.quantile(ref,.75)-np.quantile(ref,.25))/1.349
            if not np.allclose((np.quantile(cur,[.1,.5,.9])-np.quantile(ref,[.1,.5,.9]))/scale,r['change'],rtol=1e-12,atol=1e-12):raise ValueError('Atlas quantile arithmetic')
            if r['peer'] is not None:
                peers={s['entity']:s['change'] for s in atlas['atlas_audit']['rows'] if s['entity'] in r['peer_entities'] and
                    (s['signal'],s['quantity'],s['unit'])==(r['signal'],r['quantity'],r['unit'])}
                if len(peers)<2 or set(peers)!=set(r['peer_entities']):raise ValueError('Atlas peer provenance')
                if not np.allclose(np.array(r['change'])-np.median(list(peers.values()),axis=0),r['peer'],rtol=1e-12,atol=1e-12):raise ValueError('Atlas peer arithmetic')
        original={x['id']:x for x in c['evidence']['cards']};derived={x['id']:x for x in atlas['evidence']['cards']}
        if any(derived[k]!=v for k,v in original.items()):raise ValueError('Atlas changed original evidence')
        variants['CONTRAST_ATLAS']={'evidence':atlas['evidence'],'design':atlas['design'],'audit':{'label_scoring_allowed':True,'complete_original_cards':len(original)}}
        for name,variant in variants.items():
            if name in retained:
                result['variants'][name]=retained_variant(variant,retained[name]);continue
            folder=out/name;folder.mkdir(exist_ok=True);save_json(folder/'evidence.json',variant['evidence']);save_json(folder/'design.json',variant['design']);save_json(folder/'audit.json',variant['audit'])
            try:
                geometry=compile_design(variant['evidence'],variant['design'])
                if name=='POSITION':
                    before=compile_design(c['evidence'],c['design']);lookup={r['card']:r for r in before['rectangles']}
                    if any((r['width'],r['height'])!=(lookup[r['card']]['width'],lookup[r['card']]['height']) for r in geometry['rectangles']):raise ValueError('Position permutation resized a component')
                manifest=render(folder/'evidence.json',folder/'design.json',folder/'render')
                if manifest['status']!='passed':raise ValueError('Renderer audit failed')
                image=Image.open(folder/'render/dashboard.png').convert('RGB')
                task=exps.QA_TASK if name=='QA' else exps.VISUAL_TASK+('\n'+exps.ATLAS_GUIDE if name=='CONTRAST_ATLAS' else '')
                messages=[{'role':'system','content':exps.SYSTEM},{'role':'user','content':[{'type':'image'},{'type':'text','text':task}]}]
                prompt=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False,preserve_thinking=False)
                batch=processor(text=[prompt],images=[image],return_tensors='np');count=int(batch['attention_mask'].sum())
                if count+8192>40960:raise ValueError('Actual processor context limit')
                grid=batch['image_grid_thw'][0].tolist()
                local={'status':'passed','png_sha256':manifest['png_sha256'],'input_tokens':count,'grid_thw':grid,'render_seconds':manifest['python_end_to_end_seconds'],
                    'original_evidence_hash':stable_hash(c['evidence']),'current_evidence_hash':stable_hash(variant['evidence']),
                    'visual_manual_review':'pending_after_background_run','new_embedding_required_before_inference':True}
                if name=='QA':
                    actual=manifest.get('qa_badges',[])
                    if len(actual)!=2*qa['applicable_blocks']:raise ValueError('QA badge coverage')
                    for badge in actual:
                        target=qa['blocks'][badge['slot']-1][badge['badge']]
                        if abs(exps.numeric(badge['display'].strip())-target['value'])>target['tolerance']:raise ValueError('Actual QA glyph value differs')
                    local['question_metadata_contains_answers']=False
                if 'provenance' in variant:
                    support=foreground_support(folder/'render',(int(grid[2])*16,int(grid[1])*16),'shared_v2')
                    save_json(folder/'token_support.json',support)
                    if any(not r['tokens'] and not r.get('fully_anchored') for r in support['roles'].values()):raise ValueError('Variant has an unanchored empty role')
                    local['role_count']=len(support['roles']);local['anchors']=len(support['anchors'])
                result['variants'][name]=local;save_json(folder/'qualification.json',local)
            except Exception as exc:
                local={'status':'failed','error':repr(exc),'traceback':traceback.format_exc()}
                result['variants'][name]=local;save_json(folder/'qualification.json',local)
                break
        result['status']='passed' if all(v['status'] in {'passed','not_applicable','not_run_design_infeasible'} for v in result['variants'].values()) else 'failed'
    except Exception as exc:result.update(error=repr(exc),traceback=traceback.format_exc())
    result.update(seconds=time.monotonic()-began,pid=os.getpid(),physical_core=next(iter(os.sched_getaffinity(0))),
        peak_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,cuda_initialized=torch.cuda.is_initialized())
    save_json(marker,result);return result


def remaining_cpu_audit():
    """Complete registered CPU work, retain failures, never launch GPU follow-on."""
    import subprocess
    import sys
    import multiprocessing
    import signal
    import threading
    import psutil
    from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
    config=remaining_cpu_config()
    if not config.get('execution_enabled',False):raise PermissionError('CPU work is paused; explicit resume required')
    out=remaining_cpu_root();out.mkdir(exist_ok=True);start=time.monotonic();results={}
    import fcntl
    lock=(out/'owner.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='':raise RuntimeError('CPU-only environment required')
    os.sched_setaffinity(0,physical_cores(8))
    clock=read_json(OUT/'cpu_admission_v4/started.json');remaining=int(clock['max_wall_seconds']-(time.time()-clock['started_unix']))
    if remaining<=0:raise TimeoutError('Original CPU qualification deadline exhausted')
    peak={'rss_bytes':0,'samples':0};stop=threading.Event()
    def sample_memory():
        process=psutil.Process()
        while not stop.wait(1):
            total=0
            for p in [process,*process.children(recursive=True)]:
                try:total+=p.memory_info().rss
                except psutil.Error:pass
            peak['rss_bytes']=max(peak['rss_bytes'],total);peak['samples']+=1
            # Host RAM is an observed metric, not an admission/termination gate.
    monitor=threading.Thread(target=sample_memory,daemon=True);monitor.start()
    def stage(name,call):
        save_json(out/'status.json',{'status':'running','stage':name,'pid':os.getpid(),'completed_stages':list(results),'llm_calls':0,'gpu_started':False})
        print('START',name,flush=True);began=time.monotonic()
        try:result=call()
        except Exception as exc:result={'status':'failed','error':repr(exc),'traceback':traceback.format_exc()}
        result['stage_seconds']=time.monotonic()-began;results[name]=result;save_json(out/(name+'.json'),result);print('END',name,result['status'],flush=True)
        return result
    def command(args,log):
        with (out/log).open('w') as handle:r=subprocess.run(args,stdout=handle,stderr=subprocess.STDOUT)
        return {'status':'passed' if r.returncode==0 else 'failed','exit_code':r.returncode,'log':log}
    try:
        receipt=read_json(out/'source_snapshot/receipt.json')
        if any(digest(ROOT/r['source'])!=r['sha256'] or digest(ROOT/r['archive'])!=r['sha256'] for r in receipt):
            raise RuntimeError('Remaining CPU source freeze mismatch')
        static=stage('static',static_check)
        if static['status']!='passed':raise RuntimeError('Static prerequisite failed')
        def reuse_previous():
            # User retains passed tests. Read only small receipts, never replay them.
            refs=config['retained_cpu_results'];renderer=read_json(ROOT/refs['renderer']['report'])
            if renderer['status']!='passed':raise ValueError('Retained renderer result was not passed')
            if digest(ROOT/refs['renderer']['report'])!=refs['renderer']['report_sha256']:raise ValueError('Historical renderer receipt changed')
            if digest(ROOT/refs['unit']['log'])!=refs['unit']['log_sha256']:raise ValueError('Historical unit report changed')
            repair=refs['scorer_repair']
            if digest(ROOT/repair['report'])!=repair['report_sha256'] or read_json(ROOT/repair['report'])['status']!='passed':
                raise ValueError('Retained scorer repair receipt changed')
            if digest(ROOT/repair['log'])!=repair['log_sha256']:raise ValueError('Retained scorer repair log changed')
            return {'status':'passed','reused':True,'unit_tests':41,'scorer_repair_tests':2,'renderer_tests':37,'references':refs,'tests_executed':0}
        stage('retained_passed_tests',reuse_previous)
        if results['retained_passed_tests']['status']!='passed':raise RuntimeError('Retained qualification receipt invalid')
        unit=stage('unit_repair_tests',lambda:command([sys.executable,'-m','unittest',*config['targeted_unit_tests']],'unit_repair_tests.log'))
        if unit['status']!='passed':raise RuntimeError('Repair regression failed; remaining checks not launched')
        renderer=stage('renderer_repair_tests',lambda:command(['/home/lglsj/CanvasRCA/venvs/tools/bin/python','-m','pytest','-q',*config['targeted_renderer_tests']],'renderer_repair_tests.log'))
        if renderer['status']!='passed':raise RuntimeError('Renderer repair regression failed; cohort not launched')
        rows=read_json(exps.REGISTRATION)['cases'];mechanism={r['opaque_incident_id'] for r in config['mechanism_cases']}
        queue=read_json(RQ/'configs/remaining_logical_inputs_v6.json')['positions']
        if Counter(x['kind'] for x in queue)!=Counter({'development':4840,'repeat':360,'qa':360,'intervention':540}):raise ValueError('Registered logical matrix mismatch')
        if len({x['key'] for x in queue})!=6100 or any(x['calls_per_diagnosis']!=1 for x in queue):raise ValueError('Call identity/single-stage invariant')
        cores=physical_cores(4);reports=[]
        def cohort():
            with ProcessPoolExecutor(max_workers=len(cores),mp_context=multiprocessing.get_context('spawn')) as pool:
                todo=iter(source_order(rows));pending=set();failed=False
                def submit():
                    row=next(todo,None)
                    if row is not None:pending.add(pool.submit(_remaining_case,(row,row['opaque_incident_id'] in mechanism,cores)))
                for _ in cores:submit()
                while pending:
                    done,pending=wait(pending,return_when=FIRST_COMPLETED)
                    for future in done:
                        r=future.result();reports.append(r);failed=failed or r['status']=='failed'
                        save_json(out/'progress.json',{'completed':len(reports),'total':220,'failed':sum(x['status']=='failed' for x in reports),
                            'last':r['id'],'reused_variants':sum(v.get('reused',False) for x in reports for v in x['variants'].values()),
                            'dispatch_stopped_on_failure':failed})
                        print('Remaining CPU',len(reports),'/220',r['id'],r['status'],flush=True)
                    # Drain only already-running peers on failure; dispatch no new work.
                    if not failed:
                        for _ in done:submit()
            return {'status':'passed' if all(r['status']=='passed' for r in reports) else 'failed','cases':reports,'workers':len(cores),'physical_cores':cores}
        cohort_result=stage('source_templates_images_processor',cohort)
        if cohort_result['status']!='passed':
            raise RuntimeError('Variant qualification failed; dependent calibration and compatibility checks not launched')
        applicable={r['id'] for r in reports if r.get('qa_applicable_blocks',0)>0}
        if applicable:
            stage('qa_statistics',lambda:admission_statistics([r for r in rows if r['opaque_incident_id'] in applicable],out/'qa_calibration'))
        else:results['qa_statistics']={'status':'not_applicable','reason':'no_registered_QA_pairs'}
        stage('prior_compatibility',lambda:remaining_prior_audit())
        stage('compatibility_redraw',lambda:remaining_compatibility())
        atlas=[r.get('variants',{}).get('CONTRAST_ATLAS',{}) for r in reports]
        atlas_state='cpu_passed_manual_review_pending' if len(atlas)==220 and all(x.get('status')=='passed' for x in atlas) else 'not_run_CPU_prerequisites_not_met'
        report={'status':'cpu_checks_finished' if all(r['status'] not in {'failed'} for r in results.values()) else 'failed',
            'cpu_qualified':False,'stages':{k:{a:b for a,b in v.items() if a not in {'cases','hashes','cells'}} for k,v in results.items()},
            'atlas_status':atlas_state,'cases':len(reports),'mechanism_cases':len(mechanism),'qa_applicable_cases':len(applicable),
            'pending':['actual_visual_review_of_new_QA_intervention_atlas_examples','GPU_real_weight_equivalence_attention_speed_and_backend_smoke'],
            'statistical_status':'uncalibrated','confirmation_status':'not_run_registered_calibration_alarm','gpu_started':False,'smoke_started':False,'formal_started':False,'llm_calls':0}
    except Exception as exc:
        report={'status':'failed','cpu_qualified':False,'error':repr(exc),'traceback':traceback.format_exc(),'completed_stages':list(results),
            'gpu_started':False,'smoke_started':False,'formal_started':False,'llm_calls':0}
    finally:
        stop.set();monitor.join();lock.close()
    report.update(seconds=time.monotonic()-start,aggregate_memory=peak,original_CPU_elapsed_seconds=time.time()-clock['started_unix'])
    save_json(out/'qualification.json',report);save_json(out/'status.json',report);return report


def remaining_prior_audit():
    """No renamed approximations for unavailable published signals/state paths."""
    import numpy as np
    from .utils import gprune_select,evidence_budget
    out=remaining_cpu_root();encoder=read_json(OUT/'cpu_admission_v5/encoder/report.json');rows=[]
    for row in encoder['cases']:
        try:
            feature=(np.load(ROOT/row['feature_file'],allow_pickle=False).astype(np.uint32)<<16).view(np.float32)
            source=read_json(ROOT/row['base']/'token_support.json');k=evidence_budget(source['roles'],source['anchors'],len(feature),.5,'optional_support_v3')['total_tokens']
            result=gprune_select(feature,k);rows.append({'id':row['id'],'status':'passed','seconds':result['seconds'],'selected_count':len(result['indices'])})
            save_json(out/'prior_gprune'/(row['id']+'.json'),result);del feature
        except Exception as exc:
            rows.append({'id':row['id'],'status':'failed','error':repr(exc),
                'unexpected_implementation_failure':not isinstance(exc,(MemoryError,TimeoutError))});break
    passed=len(rows)==220 and all(r['status']=='passed' for r in rows)
    states={'GPRUNE_E50':{'status':'cpu_compatible_smoke_pending' if passed else 'not_run_resource_or_implementation_unqualified','cases':rows,'full_roster_passed':passed},
        'SCOPE_E50':{'status':'not_run_missing_qualified_signal','reason':'Current SDPA vision feature path exposes projected features, not the published saliency signal; no feature-norm surrogate substituted'},
        'S2PRUNE_E50':{'status':'not_run_unqualified_distinct_state_path','reason':'Current adapter gathers before decoder; no qualified layer1 updated-hidden-state and hybrid recurrent-cache gather'},
        'DART_E50':{'status':'not_run_unqualified_distinct_state_path','reason':'Current adapter gathers before decoder; no qualified layer2 updated-hidden-state and hybrid recurrent-cache gather'}}
    unexpected=any(r.get('unexpected_implementation_failure',False) for r in rows)
    return {'status':'failed' if unexpected else 'audited','methods':states,'prior_pruning_superiority_eligible':False,
        'prior_cpu_candidate_available':passed,'all_prior_smoke_qualified':False}


def remaining_compatibility():
    from renderer.main import render
    from .utils import attention_key_regions
    import numpy as np
    rows=read_json(RQ/'configs/encoder_admission_v5.json')['cases'];out=remaining_cpu_root()/'compatibility'
    results=[]
    for ds in ('aiops2022','aiops2025','aegislab'):
        row=min((r for r in rows if r['dataset']==ds),key=lambda r:stable_hash(['rq41_default_redraw',r['id']]))
        base=ROOT/row['base'];dest=out/row['id'];report=render(base/'evidence.json',base/'design.json',dest)
        same=report['png_sha256']==row['png_sha256']
        support=read_json(base/'token_support.json')
        with np.load(OUT/'cpu_admission_v5/input_geometry'/(row['id']+'.npz'),allow_pickle=False) as geo:
            tags=attention_key_regions(report,tuple(support['grid']),geo['input_ids'].reshape(-1),int(geo['image_token_id']))
        if len(tags['key_region'])<=support['image_tokens']:raise ValueError('Text keys missing from passive instrumentation')
        save_json(dest/'attention_regions_audit.json',{'regions':tags['regions'],'map_hash':tags['map_hash'],'kind':tags['kind'],
            'counts':{key:int(sum(tags['key_region']==i)) for i,key in enumerate(tags['regions'])},'attention_collected':False})
        results.append({'id':row['id'],'dataset':ds,'status':'passed' if same else 'failed','exact_png_bytes_unchanged':same,
            'attention_geometry_audited':True,'attention_collected':False})
    return {'status':'passed' if all(r['status']=='passed' for r in results) else 'failed','cases':results}


def _prior_resource_case(method,row,core,target):
    """Actual request shapes, synthetic model signals: never a model-arm result."""
    import resource
    import signal
    import numpy as np
    import torch
    from PIL import Image
    from .utils import scope_select,dart_select,s2prune_select,evidence_budget,visual_gather_plan
    os.sched_setaffinity(0,{core});torch.set_num_threads(1)
    start=time.monotonic();report={'method':method,'id':row['id'],'dataset':row['dataset'],
        'status':'failed','fixture':'actual_request_geometry_synthetic_model_signals','real_model_selection':False,
        'physical_core':core,'llm_calls':0}
    def timeout(*_):raise TimeoutError('Prior CPU selector exceeded30seconds')
    previous=signal.signal(signal.SIGALRM,timeout)
    try:
        support=read_json(ROOT/row['base']/'token_support.json');n=support['image_tokens']
        k=evidence_budget(support['roles'],support['anchors'],n,.5,'optional_support_v3')['total_tokens']
        with np.load(OUT/'cpu_admission_v5/input_geometry'/(row['id']+'.npz'),allow_pickle=False) as geo:
            ids=geo['input_ids'];positions=geo['position_ids'];mask=geo['attention_mask'];image_id=int(geo['image_token_id'])
        visual=np.flatnonzero(ids==image_id);rng=np.random.default_rng(int(stable_hash(['prior_resource_v13',row['id'],method])[:8],16))
        if method=='SCOPE':
            # Penultimate vision width, not cached post-merger 5120d features.
            features=rng.standard_normal((n,1152),dtype=np.float32)
            saliency=rng.uniform(.5,1.5,n).astype(np.float32);saliency/=saliency.sum()
            arguments=(features,saliency,k);selector=scope_select
        elif method=='DART':
            hidden=torch.from_numpy(rng.standard_normal((len(ids),5120),dtype=np.float32))
            keys=torch.from_numpy(rng.standard_normal((len(ids),48*128),dtype=np.float32))
            arguments=(hidden,keys,visual,k);selector=dart_select
        elif method=='S2PRUNE':
            # Real source PNG; ERC is synthetic because no decoder is loaded.
            with Image.open(ROOT/row['png']) as im:image=im.convert('RGB')
            erc=rng.uniform(0,2,n).astype(np.float32)
            arguments=(erc,image,support['grid'],k);selector=s2prune_select
        else:raise ValueError('Unknown prior resource fixture')
        began=time.monotonic();signal.alarm(30)
        result=selector(*arguments);elapsed=time.monotonic()-began;signal.alarm(0)
        peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
        report.update(selector_seconds=elapsed,peak_rss_bytes=peak,image_tokens=n,target_k=k)
        if elapsed>30:raise TimeoutError('Measured selector time exceeds30seconds')
        selected=result['indices']
        if len(selected)!=k or selected!=sorted(set(selected)) or selected[0]<0 or selected[-1]>=n:
            raise ValueError('Prior selected-count/domain mismatch')
        plan=visual_gather_plan(ids,positions,mask,image_id,selected)
        keep=plan['retained_input_indices']
        if not np.array_equal(ids[keep][ids[keep]!=image_id],ids[ids!=image_id]):raise ValueError('Prior dropped text')
        if not np.array_equal(plan['retained_position_ids'],positions[:,keep]):raise ValueError('Prior changed MRoPE coordinates')
        report.update(status='passed',selected_indices=selected,selected_sha256=stable_hash(selected),
            original_positions_preserved=True,all_text_preserved=True,input_tokens=plan['input_tokens'])
    except Exception as exc:report.update(error=repr(exc),traceback=traceback.format_exc())
    finally:
        signal.alarm(0);signal.signal(signal.SIGALRM,previous)
        report.update(seconds=time.monotonic()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
        save_json(target,report)


def prior_completion_audit(config_name='prior_completion_v13.json'):
    """Run only missing prior checks; keep earlier completed qualification intact."""
    import fcntl
    import multiprocessing
    import numpy as np
    from .utils import evidence_budget,visual_gather_plan
    if Path(config_name).name!=config_name:raise ValueError('Prior config must be local filename')
    config=read_json(RQ/'configs'/config_name);out=ROOT/config.get('result_root',str((OUT/'prior_completion_v13').relative_to(ROOT)))
    if not config['execution_enabled'] or os.getenv('CUDA_VISIBLE_DEVICES')!='':raise PermissionError('CPU-only prior audit required')
    lock=(out/'pipeline.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    clock=read_json(OUT/'cpu_admission_v4/started.json');deadline=clock['started_unix']+clock['max_wall_seconds']
    if time.time()>=deadline:raise TimeoutError('Original CPU deadline exhausted; not reset')
    report={'status':'running','llm_calls':0,'gpu_started':False,'real_checkpoint_loaded':False,
        'whole_experiment_cpu_qualified':False,'full_roster_real_signal_selection_qualified':False,
        'started_unix':time.time(),'stages':{},'methods':{}}
    save_json(out/'status.json',report)
    def stage(name,value):
        report['stages'][name]=value;save_json(out/(name+'.json'),value);save_json(out/'status.json',report)
    try:
        for entry in read_json(out/'source_snapshot/receipt.json'):
            if digest(ROOT/entry['source'])!=entry['sha256'] or digest(ROOT/entry['archive'])!=entry['sha256']:
                raise ValueError('Prior source freeze mismatch')
        log=ROOT/config['passed_unit_log']
        if digest(log)!=config['passed_unit_log_sha256'] or 'Ran 9 tests' not in log.read_text() or not log.read_text().rstrip().endswith('OK'):
            raise ValueError('Prior unit pass receipt mismatch')
        stage('retained_unit',{'status':'passed','tests':9,'reexecuted':False,'log':config['passed_unit_log'],'sha256':digest(log)})
        for i,entry in enumerate(config.get('repair_unit_logs',[])):
            log=ROOT/entry['log'];body=log.read_text()
            if digest(log)!=entry['sha256'] or f"Ran {entry['tests']} tests" not in body or not body.rstrip().endswith('OK'):
                raise ValueError('Repair unit receipt mismatch')
            stage('repair_unit_'+str(i),{'status':'passed','reexecuted':False,**entry})
        static=static_check();stage('static',static)
        if static['status']!='passed':raise ValueError('Static checks failed')
        for entry in read_json(ROOT/config.get('reference_manifest',str((out/'references/manifest.json').relative_to(ROOT)))):
            if digest(ROOT/entry['path'])!=entry['sha256']:raise ValueError('Frozen official reference changed')
        rows=read_json(OUT/'cpu_admission_v5/encoder/report.json')['cases'];geometry=[]
        retained_geometry=config.get('retained_geometry')
        if retained_geometry:
            p=ROOT/retained_geometry['path']
            if digest(p)!=retained_geometry['sha256']:raise ValueError('Retained geometry report changed')
            retained=read_json(p)
            if retained['status']!='passed' or retained['count']!=220:raise ValueError('Retained geometry incomplete')
            geometry=retained['cases']
        for row in ([] if retained_geometry else rows):
            if time.time()>=deadline:raise TimeoutError('Original CPU deadline')
            s=read_json(ROOT/row['base']/'token_support.json');n=s['image_tokens'];h,w=s['grid']
            k=evidence_budget(s['roles'],s['anchors'],n,.5,'optional_support_v3')['total_tokens']
            with np.load(OUT/'cpu_admission_v5/input_geometry'/(row['id']+'.npz'),allow_pickle=False) as geo:
                ids=geo['input_ids'];positions=geo['position_ids'];mask=geo['attention_mask'];image_id=int(geo['image_token_id'])
            visual=np.flatnonzero(ids==image_id)
            if n!=h*w or len(visual)!=n or not np.array_equal(visual,np.arange(visual[0],visual[0]+n)):
                raise ValueError('Prior image geometry invalid '+row['id'])
            if not 81<=k<=n or min(h,w)<9 or positions.shape!=(3,len(ids)):raise ValueError('Prior count/position contract')
            # This arbitrary fixture proves gather coordinates/counts only, not actual selection.
            fixture=np.linspace(0,n-1,k,dtype=int).tolist();plan=visual_gather_plan(ids,positions,mask,image_id,fixture)
            if plan['input_tokens']+8192>40960 or len(ids)+8192>40960:raise ValueError('Layerwise context limit')
            keep=plan['retained_input_indices']
            if not np.array_equal(plan['retained_position_ids'],positions[:,keep]):raise ValueError('MRoPE gather mismatch')
            geometry.append({'id':row['id'],'dataset':row['dataset'],'status':'passed','n':n,'k':k,'grid':[h,w],
                'full_sequence':len(ids),'pruned_sequence':plan['input_tokens'],
                'DART_trajectory':[len(ids)]*2+[plan['input_tokens']]*62,
                'S2PRUNE_trajectory':[len(ids)]+[plan['input_tokens']]*63,'shape_audit_only':True})
        stage('roster_geometry',{'status':'passed','cases':geometry,'count':len(geometry),'reused':bool(retained_geometry),'images_regenerated':0,'features_reextracted':0})
        # One max-token request per dataset, frozen before selector outcomes.
        selected=[next(r for r in rows if r['id']==oid) for oid in config['resource_cases']]
        context=multiprocessing.get_context('spawn');cores=physical_cores(3);jobs=[]
        for method_index,method in enumerate(('SCOPE','DART','S2PRUNE')):
            report['methods'][method]={'status':'running_cpu_resource_checks','cases':[]}
        for row in selected:
            for i,method in enumerate(('SCOPE','DART','S2PRUNE')):
                prior=config.get('retained_resource',{}).get(method+'/'+row['id'])
                if prior:
                    p=ROOT/prior['path']
                    if digest(p)!=prior['sha256']:raise ValueError('Retained resource receipt changed')
                    result=read_json(p)
                    if result['status']!='passed':raise ValueError('Cannot reuse failed resource check')
                    report['methods'][method]['cases'].append({**result,'reused':True});continue
                target=out/'resource'/method/(row['id']+'.json')
                proc=context.Process(target=_prior_resource_case,args=(method,row,cores[i],target));proc.start()
                jobs.append((method,row,target,proc,time.monotonic()))
            for method,case,target,proc,began in jobs:
                proc.join(max(0,min(90-(time.monotonic()-began),deadline-time.time())))
                if proc.is_alive():proc.terminate();proc.join(5)
                if proc.is_alive():proc.kill();proc.join()
                result=read_json(target) if target.exists() else {'status':'failed','id':case['id'],'error':'CPU worker failed or timed out','exitcode':proc.exitcode}
                report['methods'][method]['cases'].append(result);save_json(out/'status.json',report)
                print('Prior CPU resource',method,case['dataset'],result['status'],result.get('selector_seconds',result.get('seconds')),flush=True)
            jobs=[]
        for method,value in report['methods'].items():
            value['status']='cpu_adapter_checks_passed' if len(value['cases'])==3 and all(r['status']=='passed' for r in value['cases']) else 'cpu_resource_check_failed'
            value['real_weight_smoke_qualified']=False
        report['status']='passed' if all(v['status']=='cpu_adapter_checks_passed' for v in report['methods'].values()) else 'failed'
        report['pending']=['real-weight signals and selector speed','27B native/adapter prefill+decode parity and complete generation','method-specific smoke and measured end-to-end overhead']
    except Exception as exc:report.update(status='failed',error=repr(exc),traceback=traceback.format_exc())
    finally:
        for _,_,_,proc,_ in locals().get('jobs',[]):
            if proc.is_alive():proc.terminate();proc.join(5)
            if proc.is_alive():proc.kill();proc.join()
        report.update(seconds=time.time()-report['started_unix'],finished_unix=time.time())
        save_json(out/'qualification.json',report);save_json(out/'status.json',report);lock.close()
    return report


def smoke_runtime_config():
    cfg=read_json(ROOT/os.environ.get('CANVASRCA_RQ41_SMOKE_CONFIG','RQs/RQ4_1/configs/gpu_smoke_v18.json'))
    if cfg.get('authority') not in {'user_2026_10_07_start_smoke_only','user_2026_10_07_ten_additional_smokes','user_2026_10_07_five_prior_repair_smokes'} or cfg.get('formal_enabled'):
        raise PermissionError('Only the user-authorized bounded smoke may run')
    if cfg['max_calls']!=18 or cfg['wall_seconds']!=600 or cfg['gpu_allocator_fraction']!=.75:
        raise ValueError('Registered smoke limits changed')
    if cfg['authority']!='user_2026_10_07_start_smoke_only' and not (cfg.get('allowance') and cfg.get('round')):
        raise PermissionError('Additional smoke requires an explicit round allowance')
    slots=[s for g in cfg['hf_groups'] for s in g['slots']]+([cfg['native_slot']['slot']] if cfg.get('native_slot') else [])
    if not slots or len(slots)>18 or len(set(slots))!=len(slots):raise ValueError('Invalid registered smoke slot set')
    profile=cfg.get('ranking_decoder_profile')
    if profile is not None:
        if profile!='ranking_prefix_greedy_v25' or cfg.get('decoder_authority')!='user_2026_10_07_recipe_change':
            raise ValueError('Unregistered ranking decoder')
        if cfg.get('generation_schema_profile')!='public_numeric_id_v23' or cfg.get('native_slot'):
            raise ValueError('Ranking decoder requires its qualified grammar and HF execution path')
        if any(g['greedy'] or len(g['requests'])!=1 for g in cfg['hf_groups']):
            raise ValueError('Uniform prefix policy requires sampled batch-one groups')
    return cfg


def smoke_claim_round(cfg):
    """Consume an explicitly registered window once; never reset old clocks."""
    if not cfg.get('allowance'):return
    allowance=read_json(ROOT/cfg['allowance']);number=cfg['round']
    if allowance['authority']!=cfg['authority'] or not 1<=number<=allowance['additional_rounds']:
        raise PermissionError('Smoke round outside user allowance')
    if (allowance['calls_per_round'],allowance['seconds_per_round'],allowance['total_call_ceiling'])!=(18,600,12000):
        raise ValueError('Smoke allowance limits changed')
    expected=read_json(ROOT/allowance['round_configs'][str(number)])
    if cfg!=expected:raise ValueError('Smoke round configuration not registered')
    claim=ROOT/allowance['registry']/f'round_{number:02d}'
    claim.parent.mkdir(parents=True,exist_ok=True)
    claim.mkdir()  # Atomic, exclusive and durable, including failed launches.
    save_json(claim/'claim.json',{'round':number,'config':cfg,'claimed_unix':time.time(),'pid':os.getpid()})


def smoke_reuse_group(group,freeze):
    """Reuse complete committed groups before materializing their input tensors."""
    references=freeze.get('reused_slots',{})
    present=[str(s) in references for s in group['slots']]
    if not any(present):return []
    if not all(present):raise ValueError('Cannot partially reuse a batched smoke group')
    records=[]
    for slot,key in zip(group['slots'],group['requests']):
        ref=references[str(slot)];path=ROOT/ref['completed']
        if digest(path)!=ref['completed_sha256']:raise ValueError('Reused completion changed')
        record=read_json(path)
        if record['status']!='completed' or record['request_hash']!=freeze['requests'][key]['request_hash']:
            raise ValueError('Reused result has different input or is uncommitted')
        if stable_hash(group)!=ref['group_hash']:raise ValueError('Reused generation contract changed')
        if ref.get('logits') and digest(ROOT/ref['logits'])!=ref['logits_sha256']:raise ValueError('Reused logits changed')
        records.append({**record,'reuse_reference':ref,'new_model_calls':0})
    return records


def smoke_messages(request):
    content=([{'type':'image'}] if request.get('png') else [])+request['parts']
    return [{'role':'system','content':request['system']},{'role':'user','content':content}]


def smoke_attention_preflight(request,input_ids,grid,image_token_id,destination):
    """Audit actual smoke images BEFORE a GPU load or a charged attempt.

    Old manifests are immutable. A missing header is recovered only by the
    unified renderer with byte-identical PNG and identical original bindings.
    The resulting region vector is audit-side; it never enters model text.
    """
    import math
    import numpy as np
    from renderer.main import render
    from .utils import attention_key_regions
    destination=Path(destination)
    original_path=ROOT/request['manifest'];original=read_json(original_path)
    if digest(ROOT/request['png'])!=request['png_sha256'] or original['png_sha256']!=request['png_sha256']:
        raise ValueError('Attention geometry original PNG identity mismatch')
    manifest=original;resolved=original_path;rebuilt=False
    if 'header' not in original['audit']:
        resolved=destination/'compatible_render/manifest.json'
        if resolved.exists():manifest=read_json(resolved)
        else:manifest=render(original_path.parent/'evidence.json',original_path.parent/'design.json',resolved.parent)
        if digest(resolved.parent/'dashboard.png')!=request['png_sha256']:
            raise ValueError('Attention metadata repair changed original dashboard pixels')
        for key in ('png_sha256','source_png','evidence_hash','design_hash'):
            if manifest[key]!=original[key]:raise ValueError('Attention metadata identity changed: '+key)
        for key in original['audit']:
            if manifest['audit'].get(key)!=original['audit'][key]:raise ValueError('Original geometry changed: '+key)
        rebuilt=True
    header=manifest['audit'].get('header')
    if not header or any(not math.isfinite(header[k]) for k in ('x','y','width','height')):
        raise ValueError('Actual measured header geometry required')
    if header['width']<=0 or header['height']<=0 or header['x']<0 or header['y']<0:
        raise ValueError('Invalid measured header bounds')
    size=manifest['source_png']
    if header['x']+header['width']>size['width']+.01 or header['y']+header['height']>size['height']+.01:
        raise ValueError('Header outside original canvas')
    ids=np.asarray(input_ids,dtype=np.int64).reshape(-1)
    mapping=attention_key_regions(manifest,tuple(grid),ids,image_token_id)
    visual=np.flatnonzero(ids==image_token_id)
    if len(mapping['key_region'])!=len(ids) or len(visual)!=math.prod(grid):raise ValueError('Attention input/grid alignment')
    # Independently compare a physical gather with the public helper's gather.
    selected=list(range(0,len(visual),2));keep=ids!=image_token_id;keep[visual[selected]]=True
    pruned=attention_key_regions(manifest,tuple(grid),ids,image_token_id,selected)
    if not np.array_equal(pruned['key_region'],mapping['key_region'][keep]):raise ValueError('Attention subset alignment')
    record={'schema':'SmokeAttentionGeometryV1','status':'passed','png_sha256':request['png_sha256'],
        'original_manifest':request['manifest'],'original_manifest_sha256':digest(original_path),
        'measured_manifest':str(resolved.relative_to(ROOT)),'measured_manifest_sha256':digest(resolved),
        'rebuilt_metadata':rebuilt,'png_bytes_unchanged':True,'original_geometry_unchanged':True,
        'input_ids_sha256':stable_hash(ids.tolist()),'grid':list(grid),'image_token_id':int(image_token_id),
        'regions':mapping['regions'],'key_region':mapping['key_region'].tolist(),'map_hash':mapping['map_hash'],
        'partial_selection_alignment':True,'header':header,'new_model_calls':0}
    path=destination/'attention_map.json';save_json(path,record)
    return {'attention_map':str(path.relative_to(ROOT)),'attention_map_sha256':digest(path)}


def smoke_attention_input(request,input_ids):
    """Read only a frozen preflight result; no missing-metadata fallback on GPU."""
    import numpy as np
    path=request.get('attention_map')
    if not path:raise ValueError('Actual smoke request has no qualified attention map')
    if digest(ROOT/path)!=request.get('attention_map_sha256'):raise ValueError('Frozen attention map changed')
    record=read_json(ROOT/path)
    if record['status']!='passed' or record['png_sha256']!=request['png_sha256']:
        raise ValueError('Attention map belongs to a different/unqualified image')
    if record['input_ids_sha256']!=stable_hash(np.asarray(input_ids,dtype=np.int64).reshape(-1).tolist()):
        raise ValueError('Attention map belongs to a different input sequence')
    return record


def smoke_prepare():
    """Freeze just the registered three cases; no requalification of the roster."""
    import shutil
    import torch
    from PIL import Image
    from transformers import AutoProcessor
    from .utils import rca_schema,local_rca_scorer
    cfg=smoke_runtime_config();out=ROOT/cfg['output'];out.mkdir(parents=True,exist_ok=True)
    if (out/'started.json').exists():raise RuntimeError('Logical smoke already started; allowance cannot reset')
    os.sched_setaffinity(0,physical_cores(8));torch.set_num_threads(8)
    report=read_json(OUT/'cpu_completion_v17/qualification.json')
    if not report['cpu_qualified']:raise ValueError('CPU prerequisites incomplete')
    local_rca_scorer()  # Fail on missing scoring dependencies BEFORE startup/spending.
    processor=AutoProcessor.from_pretrained(cfg['model_path'],local_files_only=True)
    processor.tokenizer.padding_side='left'
    source={r['id']:r for r in read_json(RQ/'configs/encoder_admission_v5.json')['cases']}
    cases={};requests={};files={};model=Path(cfg['model_path'])
    for case in cfg['cases']:
        oid=case['id'];s=source[oid];base=ROOT/s['base'];public=read_json(exps.SOURCE/(oid+'.json'))
        private=exps.SOURCE.parent/'private'/(oid+'.json')
        files[str(private.relative_to(ROOT))]=digest(private)
        cases[oid]={**case,'base':s['base'],'candidates':public['candidates'],'private':str(private.relative_to(ROOT))}
        for p in (base/'provenance.json',base/'token_support.json',base/'text_conditions.json',exps.SOURCE/(oid+'.json')):files[str(p.relative_to(ROOT))]=digest(p)
        variants=['BASE']+(['ATLAS'] if case['dataset']=='aegislab' else [])+(['QA'] if case['dataset']=='aiops2022' else [])
        for variant in variants:
            folder=base if variant=='BASE' else OUT/'cpu_remaining_v10/cases'/oid/('CONTRAST_ATLAS' if variant=='ATLAS' else 'QA')
            png=folder/'render/dashboard.png';manifest=folder/'render/manifest.json'
            if variant!='BASE' and read_json(folder/'qualification.json')['status']!='passed':raise ValueError('Unqualified variant')
            if digest(png)!=read_json(manifest)['png_sha256']:raise ValueError('Source PNG mismatch')
            task=exps.QA_TASK if variant=='QA' else exps.VISUAL_TASK+('\n'+exps.ATLAS_GUIDE if variant=='ATLAS' else '')
            req={'system':'Answer only the independent factual QA task.' if variant=='QA' else exps.SYSTEM,
                'parts':[{'type':'text','text':task}],'png':str(png.relative_to(ROOT)),
                'manifest':str(manifest.relative_to(ROOT)),'png_sha256':digest(png),'id':oid,'variant':variant}
            req['support']=str((folder/'token_support.json').relative_to(ROOT))
            for p in (png,manifest,folder/'token_support.json'):
                if p.exists():files[str(p.relative_to(ROOT))]=digest(p)
            if variant=='QA':
                qa=OUT/'cpu_remaining_v10/cases'/oid/'qa_audit.json'
                req['qa_audit']=str(qa.relative_to(ROOT));files[req['qa_audit']]=digest(qa)
            requests[oid+'__'+variant]=req
        text=read_json(base/'text_conditions.json')['T_FULL']
        requests[oid+'__TEXT']={'system':exps.SYSTEM,'parts':text,'png':None,'id':oid,'variant':'TEXT'}
    for key,req in requests.items():
        prompt=processor.apply_chat_template(smoke_messages(req),tokenize=False,add_generation_prompt=True,enable_thinking=False,preserve_thinking=False)
        images=[Image.open(ROOT/req['png']).convert('RGB')] if req['png'] else None
        batch=processor(text=[prompt],images=images,padding=True,return_tensors='pt')
        if batch['input_ids'].shape[1]+8192>40960:raise ValueError('Context cap')
        req.update(prompt=prompt,input_tokens=int(batch['input_ids'].shape[1]),
            image_grid_thw=batch['image_grid_thw'].tolist() if images else [],request_hash=stable_hash([smoke_messages(req),req.get('png_sha256'),rca_schema(),cfg['generation']]))
        if images:
            grid=req['image_grid_thw'][0]
            req.update(smoke_attention_preflight(req,batch['input_ids'][0].numpy(),(grid[1]//2,grid[2]//2),
                processor.tokenizer.convert_tokens_to_ids('<|image_pad|>'),out/'attention_geometry'/key))
            files[req['attention_map']]=req['attention_map_sha256']
        (out/'inputs').mkdir(exist_ok=True)
        torch.save(dict(batch),out/'inputs'/(key+'.pt'))
        save_json(out/'inputs'/(key+'.json'),req)
    # Prepare the two exact padded batches; answer count is two for each forward.
    batch_keys=[cfg['cases'][0]['id']+'__BASE',cfg['cases'][1]['id']+'__BASE']
    for reverse in (False,True):
        keys=list(reversed(batch_keys)) if reverse else batch_keys
        batch=processor(text=[requests[k]['prompt'] for k in keys],images=[Image.open(ROOT/requests[k]['png']).convert('RGB') for k in keys],padding=True,return_tensors='pt')
        torch.save(dict(batch),out/'inputs'/('batch_reverse.pt' if reverse else 'batch.pt'))
    for p in sorted((out/'inputs').glob('*')):files[str(p.relative_to(ROOT))]=digest(p)
    for p in [*sorted((RQ/'src').glob('*.py')),RQ/'configs/gpu_smoke_v18.json',RQ/'configs/comparison_coding_plan_v1.json',
        RQ/'configs/statistics_active_v11.json',RQ/'configs/resource_policy_active_v16.json',
        ROOT/'configs/vllm_inference_local.yaml',ROOT/'configs/rca_scorer.yaml',ROOT/'src/vlmrca/vlm/client.py',
        ROOT/'scripts/vllm_vlm/serve_canvasrca_local.sh',ROOT/'src/scorer/rca_scorer.py']:
        if p.exists():files[str(p.relative_to(ROOT))]=digest(p)
    model_files={str(p):digest(p) for p in model.glob('*.json')}
    weights=[{'path':str(p),'size':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns} for p in sorted(model.glob('*.safetensors'))]
    freeze={'status':'prepared','config':cfg,'cases':cases,'requests':requests,'files':files,'model_metadata':model_files,
        'weight_file_identity':weights,'weight_identity_scope':'existing local checkpoint metadata/stat; no new full-weight content hash',
        'formal_enabled':False,'new_model_calls':0,'cpu_roster_rerun':False,'codex_sha256':digest(ROOT/'Codex.md')}
    save_json(out/'freeze.json',freeze)
    for path,sha in files.items():
        if '/inputs/' in path:continue
        dst=out/'source_snapshot'/path;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,dst)
    return {'status':'passed','requests':len(requests),'max_calls':18,'freeze_sha256':digest(out/'freeze.json')}


def smoke_score(req,response,cases):
    from .utils import local_rca_scorer,rca_schema
    from scorer import score_bound_response
    if req['variant']=='QA':return exps.score_linked_qa(read_json(ROOT/req['qa_audit']),response)
    if req.get('label_scoring_allowed') is False:
        c=cases[req['id']]
        checked=score_bound_response(response,c['candidates'],{x:x for x in c['candidates']},[],rca_schema(),local_rca_scorer())
        return {'status':'control_unscored','valid':checked['status']=='complete','error':checked['error'],'original_root_labels_used':False}
    c=cases[req['id']];private=read_json(ROOT/c['private'])
    return score_bound_response(response,c['candidates'],private['numeric_to_natural'],private['accepted_labels'],rca_schema(),local_rca_scorer())


def hf_infer_group(runtime,group,reqs,batch,freeze,cfg,out,attention_record=None):
    """Single production inference implementation shared by smoke and formal."""
    import torch
    import numpy as np
    from PIL import Image
    from xgrammar.contrib.hf import LogitsProcessor
    from transformers import LogitsProcessorList
    from .utils import (SmokeLogitsCapture,injected_generate,hybrid_prior_generate,pack_injected_batch,
        select_registered_condition,gprune_select,evidence_budget,ScopeVisionSignal,scope_select,RankingPrefixGreedy)
    model=runtime['model'];processor=runtime['processor'];tap=runtime['tap']
    grammar=runtime['grammar'];qa_grammar=runtime['qa_grammar'];generation_schema=runtime['generation_schema']
    pairs=runtime.setdefault('pairs',{});matched_cfg=runtime['matched_cfg'];mode=group['mode'];arm=group['arm'];records=[]
    model.config.text_config._attn_implementation='rq41_passive_sdpa' if group.get('attention') else 'sdpa'
    model.model.rope_deltas=None;torch.manual_seed(group.get('seed',42));torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize();began=time.monotonic()
    gpu_start=torch.cuda.Event(enable_timing=True);gpu_end=torch.cuda.Event(enable_timing=True);gpu_start.record()
    capture=SmokeLogitsCapture(out/'generation_progress'/f"{group['slots'][0]:02d}.json" if cfg.get('capture_generation_progress') else None,capture_logits=cfg.get('audit_logits',True))
    selection_meta=[];plans=[];features=None;positions=None;prior_state=None;packed=None;signal_audit=None
    phase_times={};prior_image=None;prior_grid=None;protected=[]
    options={**cfg['generation'],'do_sample':not group['greedy'],'logits_processor':LogitsProcessorList([capture,LogitsProcessor(qa_grammar if reqs[0]['variant']=='QA' else grammar)])}
    ranking_decoder=None
    if cfg.get('ranking_decoder_profile') and reqs[0]['variant']!='QA':
        ranking_decoder=RankingPrefixGreedy(processor.tokenizer)
        options['logits_processor'].append(ranking_decoder)
    if group['greedy']:
        options.pop('temperature',None);options.pop('top_p',None);options.pop('top_k',None)
    # Cache shapes are observed during this same generation, never replayed.
    cache_audit=[]
    def cache_hook(module,args,kwargs,output):
        c=getattr(output,'past_key_values',None)
        if c is not None and len(cache_audit)<2:
            cache_audit.append({'seq_len':int(c.get_seq_length()),'layers':[{'class':type(l).__name__,'keys':list(l.keys.shape) if getattr(l,'keys',None) is not None else None} for l in c.layers]})
    hook=model.register_forward_hook(cache_hook,with_kwargs=True)
    try:
        with torch.inference_mode():
            if reqs[0]['png']:
                positions,_=model.model.get_rope_index(batch['input_ids'],attention_mask=batch['attention_mask'],image_grid_thw=batch['image_grid_thw'],mm_token_type_ids=batch['mm_token_type_ids'])
            if mode not in ('native','text'):
                phase_start=time.monotonic();scope_signal=None
                if group.get('method')=='SCOPE':
                    with ScopeVisionSignal(model.model.visual) as scope_signal:
                        enc=model.model.get_image_features(batch['pixel_values'],batch['image_grid_thw'],return_dict=True)
                    signal_audit={'kind':'actual_penultimate_vision_incoming_attention','saliency_tokens':len(scope_signal.saliency),
                        'saliency_sum':float(scope_signal.saliency.sum()),'feature_shape':list(scope_signal.features.shape),'chunk':scope_signal.chunk}
                else:enc=model.model.get_image_features(batch['pixel_values'],batch['image_grid_thw'],return_dict=True)
                features=list(enc.pooler_output);del enc
                phase_times['vision_and_required_signal_wall']=time.monotonic()-phase_start;phase_start=time.monotonic()
                for i,(req,feature) in enumerate(zip(reqs,features)):
                    n=len(feature)
                    if group.get('anchor_policy'):
                        if group['anchor_policy'] not in ('shared_anchors_v22','inventory_context_v24') or group.get('method') not in ('SCOPE','S2PRUNE'):
                            raise ValueError('Unregistered prior protection policy')
                        protected=read_json(ROOT/req['support'])['anchors']
                        if group['anchor_policy']=='inventory_context_v24':
                            guard=read_json(ROOT/req['inventory_guard'])
                            if digest(ROOT/req['inventory_guard'])!=req['inventory_guard_sha256'] or not set(protected)<=set(guard['protected_indices']):
                                raise ValueError('Inventory guard changed/lost original anchors')
                            protected=guard['protected_indices']
                    if mode=='identity':selected=list(range(n));meta={'indices':selected}
                    else:
                        s=read_json(ROOT/req['support']);base=ROOT/freeze['cases'][req['id']]['base'];p=read_json(ROOT/req['provenance']) if req.get('provenance') else read_json(base/'provenance.json');h,w=s['grid']
                        target=n if group.get('identity') else evidence_budget(s['roles'],s['anchors'],n,.5,'optional_support_v3')['total_tokens']
                        if mode=='prior':
                            meta={'indices':None,'K':target}
                            if group.get('method')=='S2PRUNE':prior_image=Image.open(ROOT/req['png']).convert('RGB');prior_grid=(h,w)
                        elif group.get('method')=='SCOPE':
                            meta=scope_select(scope_signal.features.cpu().numpy(),scope_signal.saliency.cpu().numpy(),target,protected=protected)
                            meta['signal_audit']=signal_audit
                        elif arm=='GPRUNE_E50':meta=gprune_select(feature.float().cpu().numpy(),target)
                        else:
                            f=feature.float().cpu().numpy();xy=np.array([[t%w,t//w] for t in range(n)],np.float32)
                            edges=read_json(OUT/'cpu_admission_v5/selection'/req['id']/'rewire.json')['edges'] if arm=='REWIRED_E50' else p['edges']
                            meta=select_registered_condition(matched_cfg,arm,f,xy,s['roles'],s['anchors'],edges,seconds=30)
                            del f
                        selected=meta['indices']
                    selection_meta.append(meta)
                    if mode!='prior' and not set(protected)<=set(meta['indices']):raise ValueError('Pre-decoder prior removed protected anchors')
                phase_times['selection_and_signal_copy_wall']=time.monotonic()-phase_start;phase_start=time.monotonic()
                scope_signal=None
                if mode!='prior':
                    packed=pack_injected_batch(batch['input_ids'],batch['attention_mask'],positions,model.get_input_embeddings()(batch['input_ids']),features,model.config.image_token_id,[r['indices'] for r in selection_meta])
                    plans=packed['plans']
                phase_times['gather_wall']=time.monotonic()-phase_start
            if group.get('attention'):
                req=reqs[0];grid=batch['image_grid_thw'][0].tolist() if req['png'] else [0,0,0];grid=(grid[1]//2,grid[2]//2)
                if mode=='prior':raise ValueError('Mid-decoder attention needs a separately qualified region gather')
                region_ids=np.asarray(attention_record['key_region'])
                if mode not in ('native','text'):region_ids=region_ids[plans[0]['retained_input_indices']]
                # Observer reserves zero for generated/noninput keys.
                names=['other:generated']+attention_record['regions'];regions=torch.tensor(region_ids+1,dtype=torch.long,device='cuda')
                mapping_hash=stable_hash(region_ids.tolist())
                tap.begin(group.get('attention_key',stable_hash([cfg.get('ledger_scope','rq41_smoke_v18'),group['slots'][0]])),regions,names,mapping_hash)
                if cfg.get('audit_logits',True):
                    save_json(out/'attention_maps'/(str(group['slots'][0])+'.json'),{'names':names,'mapping_hash':mapping_hash,'grid':grid,
                        'source_map_sha256':req.get('attention_map_sha256')})
            if mode in ('native','text'):
                generated=model.generate(**batch,use_cache=True,**options)
                output_ids=generated[:,batch['input_ids'].shape[1]:]
            elif mode=='prior':
                generated,prior_state=hybrid_prior_generate(model,batch,features,selection_meta[0]['K'],group.get('method','DART'),options,
                    image=prior_image,grid=prior_grid,fixed_selection=list(range(len(features[0]))) if group.get('identity') else None,protected=protected)
                output_ids=generated
            else:
                generated=injected_generate(model,batch,features,[r['indices'] for r in selection_meta],options,prepared=packed);output_ids=generated
        gpu_end.record();torch.cuda.synchronize();elapsed=time.monotonic()-began
    finally:
        hook.remove();tap.end()
    captures=capture.values;all_tokens=output_ids.cpu().tolist()
    stop=model.generation_config.eos_token_id;stop={stop} if isinstance(stop,int) else set(stop)
    for i,(slot,req) in enumerate(zip(group['slots'],reqs)):
        tokens=all_tokens[i]
        for j,t in enumerate(tokens):
            if t in stop:tokens=tokens[:j+1];break
        response=processor.decode(tokens,skip_special_tokens=True)
        nimage=int((batch['input_ids'][i]==model.config.image_token_id).sum()) if req['png'] else 0
        count=int(batch['attention_mask'][i].sum())
        if plans:count=plans[i]['input_tokens']
        if prior_state:count=prior_state['input_tokens']
        numeric={step:value[i] for step,value in captures.items() if step<len(tokens)}
        if cfg.get('audit_logits',True):
            (out/'logits').mkdir(exist_ok=True)
            torch.save(numeric,out/'logits'/f'{slot:02d}.pt')
        result={'slot':slot,'status':'completed','request_hash':req['request_hash'],'response':response,'output_token_ids':tokens,
            'output_tokens':len(tokens),'input_tokens':count,'image_tokens_original':nimage,'seconds_group':elapsed,
            'batch_size':len(reqs),'backend':'transformers_native_generate_sdpa','mode':mode,'arm':arm,'cache_audit':cache_audit,
            'peak_allocated_bytes':torch.cuda.max_memory_allocated(),'peak_reserved_bytes':torch.cuda.max_memory_reserved(),
            'outcome':smoke_score(req,response,freeze['cases']) if cfg.get('score_in_backend',True) else None,'greedy':group['greedy'],'attention_requested':bool(group.get('attention')),
            'actual_retention':selection_meta[i] if selection_meta else None,'gather_plan':plans[i] if plans else None,
            'original_mrope':positions[:,i].cpu().tolist() if positions is not None else None,'prior_state':prior_state,
            'generation_schema_profile':cfg.get('generation_schema_profile'),'generation_schema_sha256':stable_hash(generation_schema)}
        result['ranking_decoder']=ranking_decoder.audit() if ranking_decoder is not None else None
        result['runtime_timing']={'wall_seconds':elapsed,'cuda_elapsed_span_ms':gpu_start.elapsed_time(gpu_end),
            'first_output_wall_seconds':capture.first_wall-began,'first_output_cuda_span_ms':gpu_start.elapsed_time(capture.first_cuda),
            'phases_wall_seconds':phase_times,'observer_cuda_span_ms':sum(a.elapsed_time(b) for a,b in getattr(tap,'gpu_spans',[])) if group.get('attention') else 0.,
            'timing_scope':'encoder+selector+gather+generation, same-call audit overhead; processor/render and startup separate'}
        result['signal_audit']=signal_audit
        if group.get('anchor_policy'):
            retained=prior_state['selection']['indices'] if prior_state else selection_meta[i]['indices']
            if not set(protected)<=set(retained):raise ValueError('Committed prior removed protected anchors')
            result['protection_audit']={'policy':group['anchor_policy'],'required_count':len(protected),
                'retained_count':len(set(protected)&set(retained)),'required_hash':stable_hash(protected),
                'public_support_sha256':digest(ROOT/req['support']),'all_preserved':True,
                'inventory_guard_sha256':req.get('inventory_guard_sha256')}
        pair_key=group.get('pair_key',req['id'])
        if group.get('pair_role')=='native':pairs[pair_key]={'tokens':tokens,'logits':numeric,'seconds':elapsed}
        if group.get('pair_role')=='identity':
            reference=pairs[pair_key];rows=[]
            for step,value in numeric.items():
                baseline=reference['logits'][step];diff=(value-baseline).abs()
                rows.append({'position':step,'max_absolute':float(diff.max()),'mean_absolute':float(diff.mean()),
                    'max_relative':float((diff/baseline.abs().clamp_min(.001)).max()),'mean_relative':float((diff/baseline.abs().clamp_min(.001)).mean())})
            passed=tokens==reference['tokens'] and all(r['max_absolute']<=.125 and r['mean_absolute']<=.01 for r in rows)
            result['parity']={'passed':passed,'tokens_equal':tokens==reference['tokens'],'logits':rows,'unobserved_positions':'not_tested'}
        # Convert numpy values without changing the scientific records.
        result=json.loads(json.dumps(result,default=lambda v:v.tolist() if hasattr(v,'tolist') else v.item()))
        records.append(result)
    return records


def smoke_hf_worker():
    """Registered real-checkpoint paths; each generated answer spends one slot."""
    import torch
    import numpy as np
    import xgrammar as xgr
    from xgrammar.contrib.hf import LogitsProcessor
    from transformers import AutoProcessor,Qwen3_5ForConditionalGeneration,LogitsProcessorList
    from PIL import Image
    from .utils import (SmokeLogitsCapture,injected_generate,hybrid_prior_generate,pack_injected_batch,
        select_registered_condition,gprune_select,evidence_budget,AttentionStore,PassiveAttentionTap,attention_key_regions,rca_schema,rca_generation_schema,ScopeVisionSignal,scope_select,RankingPrefixGreedy)
    from vlmrca.run_state import DurableCallRegister
    cfg=smoke_worker_authority();out=ROOT/cfg['output'];freeze=read_json(out/'freeze.json')
    progress={'status':'running','stage':'loading_hf_checkpoint','pid':os.getpid(),'calls_started':0,'calls_completed':0,'formal_started':False}
    save_json(out/'status.json',progress);print('Loading frozen Qwen BF16 checkpoint',flush=True)
    torch.set_num_threads(8);torch.cuda.set_per_process_memory_fraction(.75)
    processor=AutoProcessor.from_pretrained(cfg['model_path'],local_files_only=True);processor.tokenizer.padding_side='left'
    model=Qwen3_5ForConditionalGeneration.from_pretrained(cfg['model_path'],dtype=torch.bfloat16,device_map='cuda',attn_implementation='sdpa',local_files_only=True).eval()
    info=xgr.TokenizerInfo.from_huggingface(processor.tokenizer,vocab_size=model.config.text_config.vocab_size)
    compiler=xgr.GrammarCompiler(info)
    generation_schema=rca_generation_schema(cfg.get('generation_schema_profile'))
    grammar=compiler.compile_json_schema(generation_schema,any_whitespace=False)
    qa_grammar=compiler.compile_builtin_json_grammar()
    store=AttentionStore(out/'attention');tap=PassiveAttentionTap(store);tap.install(model)
    calls=DurableCallRegister(out/'calls.sqlite',limit=18,scope=cfg.get('ledger_scope','rq41_smoke_v18'));pairs={};results=[]
    matched_cfg=read_json(RQ/'configs/comparison_coding_plan_v1.json')
    try:
        for group in cfg['hf_groups']:
            keys=group['requests'];reqs=[freeze['requests'][k] for k in keys];mode=group['mode'];arm=group['arm']
            reused=smoke_reuse_group(group,freeze)
            if reused:
                for req,result in zip(reqs,reused):
                    if group.get('pair_role')=='native':
                        pairs[req['id']]={'tokens':result['output_token_ids'],'seconds':result['seconds_group'],
                            'logits':torch.load(ROOT/result['reuse_reference']['logits'],map_location='cpu',weights_only=True)}
                    results.append(result)
                progress['calls_completed']+=len(reused)
                print('REUSE slots',group['slots'],'no model call',flush=True)
                continue
            progress.update(stage='preparing_'+group['name'],active_slots=group['slots']);save_json(out/'status.json',progress)
            if (out/'STOP').exists():raise InterruptedError('User stop marker')
            batch_path=(ROOT/cfg['input_root'] if cfg.get('input_root') else out/'inputs')/(group.get('batch_file',keys[0])+'.pt')
            batch={k:v.to('cuda') for k,v in torch.load(batch_path,map_location='cpu',weights_only=True).items()}
            for req in reqs:
                if req['png'] and digest(ROOT/req['png'])!=req['png_sha256']:raise ValueError('PNG changed before request')
            attention_record=None
            if group.get('attention'):
                attention_record=smoke_attention_input(reqs[0],batch['input_ids'][0].cpu().numpy())
            attempt=[]
            for slot,req in zip(group['slots'],reqs):
                call_id,_=calls.begin(str(slot),stable_hash([req['request_hash'],group]),'qualification')
                attempt.append(call_id);progress['calls_started']+=1
                save_json(out/'attempts'/f'{slot:02d}.json',{'slot':slot,'request':req,'group':group,'attempt_id':call_id,'status':'started'})
            progress.update(stage='inference_'+group['name']);save_json(out/'status.json',progress)
            print('START slots',group['slots'],group['name'],flush=True)
            runtime=dict(model=model,processor=processor,tap=tap,grammar=grammar,qa_grammar=qa_grammar,
                generation_schema=generation_schema,pairs=pairs,matched_cfg=matched_cfg)
            records=hf_infer_group(runtime,group,reqs,batch,freeze,cfg,out,attention_record)
            for result,call_id in zip(records,attempt):
                slot=result['slot'];save_json(out/'trajectories'/f'{slot:02d}.json',result);calls.finish(call_id,result)
                save_json(out/'completed'/f'{slot:02d}.json',result);results.append(result);progress['calls_completed']+=1
            if any(r.get('parity',{}).get('passed') is False for r in results):raise ValueError('Native/identity numerical or token parity failed')
            progress.update(stage='completed_'+group['name']);save_json(out/'status.json',progress)
            print('DONE slots',group['slots'],'seconds',round(records[0]['seconds_group'],2),flush=True)
            del batch,records
        tap.close();store.close()
        save_json(out/'hf_report.json',{'status':'passed','completed':len(results),'attention_error':tap.error,'attention_missed':tap.missed,'attention_records':store.accepted,'formal_started':False})
    finally:
        calls=None
    return {'status':'passed'}


def smoke_probe_models(url,api_key):
    """Use the serving credential for readiness; reject auth/config errors promptly."""
    import urllib.request
    import urllib.error
    request=urllib.request.Request(url,headers={'Authorization':'Bearer '+api_key})
    try:
        with urllib.request.urlopen(request,timeout=2) as response:return json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code==503:return None
        raise RuntimeError(f'Local vLLM readiness HTTP {exc.code}; check serving/client configuration') from None
    except (OSError,TimeoutError):return None


def smoke_reused_hf_report(freeze,reused):
    """Skip a completely committed model phase without loading its weights again."""
    reference=freeze.get('hf_report_reference')
    if reference is None:return None
    expected={s for g in freeze['config']['hf_groups'] for s in g['slots']}
    if {r['slot'] for r in reused}!=expected:raise ValueError('Incomplete reused HF phase')
    if digest(ROOT/reference['path'])!=reference['sha256']:raise ValueError('Reused HF report changed')
    report=read_json(ROOT/reference['path'])
    if report['status']!='passed' or report['completed']!=len(expected) or report['attention_error'] or report['attention_missed']:
        raise ValueError('Unqualified reused HF phase')
    return {**report,'reuse_reference':reference,'new_model_calls':0}


def smoke_native_schema():
    """Project only the constraint already ignored by HF xgrammar; scorer stays strict."""
    from .utils import rca_schema
    schema=rca_schema()
    if schema['properties']['services'].pop('uniqueItems') is not True:raise ValueError('Unexpected RCA schema')
    return schema


def smoke_native_worker():
    """Production text through the canonical launcher/client; no external RCA repo."""
    import subprocess
    import urllib.request
    from dataclasses import asdict
    from vlmrca.vlm.client import call_vlm
    from vlmrca.vlm.configs import VLMConfig
    from vlmrca.run_state import DurableCallRegister
    from .utils import rca_schema
    cfg=smoke_worker_authority();out=ROOT/cfg['output'];freeze=read_json(out/'freeze.json')
    slot=cfg['native_slot'];req=freeze['requests'][slot['request']]
    # Reject an unowned listener rather than reuse or kill it.
    import socket
    import secrets
    sock=socket.socket();busy=sock.connect_ex(('127.0.0.1',8000))==0;sock.close()
    if busy:raise RuntimeError('Port8000 already owned; refusing ambiguous production server')
    api_key=os.environ.get('VLLM_API_KEY') or secrets.token_urlsafe(24)
    env={**os.environ,'VLLM_API_KEY':api_key,'CANVASRCA_STANDALONE':'1','CANVASRCA_ATTENTION_MODE':'off','CANVASRCA_VLLM_CONFIG':str(ROOT/'configs/vllm_inference_local.yaml')}
    env.pop('RL_SLM_RCA_ROOT',None)
    log=(out/'native_server.log').open('a')
    server=subprocess.Popen(['bash','scripts/vllm_vlm/serve_canvasrca_local.sh','qwen3.8-27b'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
    save_json(out/'native_server.json',{'pid':server.pid,'owned':True,'profile':env['CANVASRCA_VLLM_CONFIG']})
    save_json(out/'status.json',{'status':'running','stage':'loading_native_server','pid':os.getpid(),'formal_started':False})
    started=read_json(out/'started.json')
    try:
        while True:
            if server.poll() is not None:raise RuntimeError('Owned vLLM server exited: '+str(server.returncode))
            if time.time()-started['started_unix']>=cfg['wall_seconds']:raise TimeoutError('Native readiness deadline')
            models=smoke_probe_models('http://127.0.0.1:8000/v1/models',api_key)
            if models is not None:
                if not any(m['id']=='Qwen/Qwen3.8-27B' for m in models['data']):raise RuntimeError('Unexpected served model identity')
                break
            time.sleep(1)
        started=read_json(out/'started.json');remaining=600-(time.time()-started['started_unix'])
        if remaining<=0:raise TimeoutError('Logical smoke deadline')
        recipe=VLMConfig(tag='qwen3.8-27b',backend='openai',model_id='Qwen/Qwen3.8-27B',max_tokens=8192,temperature=1.,top_p=.95,seed=42,
            thinking=False,thinking_via_template=True,base_url_env='CANVASRCA_SMOKE_BASE_URL',api_key_env='CANVASRCA_SMOKE_API_KEY',request_timeout_s=remaining,
            extra={'extra_body':{'chat_template_kwargs':{'enable_thinking':False,'preserve_thinking':False},'top_k':-1}})
        os.environ['CANVASRCA_SMOKE_BASE_URL']='http://127.0.0.1:8000/v1';os.environ['CANVASRCA_SMOKE_API_KEY']=api_key
        calls=DurableCallRegister(out/'calls.sqlite',limit=18,scope=cfg.get('ledger_scope','rq41_smoke_v18'))
        cid,_=calls.begin(str(slot['slot']),req['request_hash'],'qualification')
        save_json(out/'attempts'/'10.json',{'slot':10,'attempt_id':cid,'request':req,'backend':'vllm_native','status':'started'})
        save_json(out/'status.json',{'status':'running','stage':'inference_native_text','active_slots':[10],'pid':os.getpid(),'formal_started':False})
        import vlmrca.vlm.client as client_module
        client_module.load_env=lambda: 0  # Explicit local adapter: never consult an external checkout for credentials.
        result=call_vlm(req['parts'],recipe,system=req['system'],max_retries=1,response_format={'type':'json_schema','json_schema':{'name':'rca','strict':True,'schema':smoke_native_schema()}},record_performance=True)
        record={'slot':10,'status':'completed','backend':'vllm_native','request_hash':req['request_hash'],'response':result.text,
            'input_tokens':result.input_tokens,'output_tokens':result.output_tokens,'seconds':result.latency_s,'performance':result.performance,
            'outcome':smoke_score(req,result.text,freeze['cases']),'recipe':asdict(recipe),'models':models,
            'generation_schema':smoke_native_schema(),'host_validation_schema':rca_schema(),
            'schema_adapter':'xgrammar ignores uniqueItems during generation; strict uniqueness retained by host scorer'}
        save_json(out/'trajectories'/'10.json',record);calls.finish(cid,record);save_json(out/'completed'/'10.json',record)
    finally:
        if server.poll() is None:
            server.terminate()
            try:server.wait(timeout=5)
            except subprocess.TimeoutExpired:server.kill();server.wait()
        log.close()
    return {'status':'passed'}


def smoke_supervisor():
    """600-second shared clock, owned process groups and no automatic full run."""
    import fcntl
    import signal
    import subprocess
    import sys
    import sqlite3
    cfg=smoke_runtime_config();out=ROOT/cfg['output'];freeze=read_json(out/'freeze.json')
    lock=(out/'owner.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if (out/'started.json').exists():raise RuntimeError('Smoke clock already started; no automatic reset/retry')
    if cfg!=freeze['config']:raise ValueError('Runtime configuration differs from freeze')
    for group in cfg['hf_groups']:
        if group.get('attention'):
            for key in group['requests']:
                request=freeze['requests'][key]
                if not request.get('attention_map') or digest(ROOT/request['attention_map'])!=request.get('attention_map_sha256'):
                    raise ValueError('Actual smoke attention geometry not qualified before model loading')
    for path,sha in freeze['files'].items():
        # Prepared request tensors were verified before this bounded startup.
        if '/inputs/' not in path and digest(ROOT/path)!=sha:raise ValueError('Frozen source changed: '+path)
    for path,sha in freeze['model_metadata'].items():
        if digest(Path(path))!=sha:raise ValueError('Checkpoint metadata changed')
    for row in freeze['weight_file_identity']:
        s=Path(row['path']).stat()
        if (s.st_size,s.st_mtime_ns)!=(row['size'],row['mtime_ns']):raise ValueError('Checkpoint shard changed')
    reused=[]
    for group in cfg['hf_groups']:reused.extend(smoke_reuse_group(group,freeze))
    reused_hf=smoke_reused_hf_report(freeze,reused)
    smoke_claim_round(cfg)
    for result in reused:save_json(out/'completed'/f"{result['slot']:02d}.json",result)
    if reused_hf:save_json(out/'hf_report.json',reused_hf)
    start=time.time();save_json(out/'started.json',{'started_unix':start,'pid':os.getpid(),'max_wall_seconds':600,'freeze_sha256':digest(out/'freeze.json')})
    summary={'status':'running','pid':os.getpid(),'calls_started':0,'calls_completed':len(reused),'max_calls':18,'max_wall_seconds':600,'formal_started':False,
        'reused_positions':len(reused),'round':cfg.get('round',0),'previous_smoke_attempts':cfg.get('previous_smoke_attempts',0)}
    child=None
    def stopping(*_):raise InterruptedError('Supervisor stop signal')
    signal.signal(signal.SIGTERM,stopping);signal.signal(signal.SIGINT,stopping)
    try:
        stages=([] if reused_hf else ['smoke-hf'])+(['smoke-native'] if cfg.get('native_slot') else [])
        for stage in stages:
            summary.update(stage=stage);save_json(out/'summary.json',summary)
            child=subprocess.Popen([sys.executable,'-u','-m','RQs.RQ4_1.src.main',stage],cwd=ROOT,start_new_session=True)
            save_json(out/'worker.json',{'pid':child.pid,'stage':stage})
            while child.poll() is None:
                if (out/'STOP').exists():raise InterruptedError('User stop marker')
                if time.time()-start>=600:raise TimeoutError('Shared600-second smoke budget exhausted; no timeout-only pass')
                summary['elapsed_seconds']=round(time.time()-start,2)
                if (out/'calls.sqlite').exists():
                    with sqlite3.connect(out/'calls.sqlite') as db:
                        summary['calls_started']=db.execute('SELECT count(*) FROM calls').fetchone()[0]
                summary['calls_completed']=len(list((out/'completed').glob('*.json')))
                save_json(out/'summary.json',summary);time.sleep(1)
            if child.returncode:
                failure=out/'worker_failure.json'
                if failure.exists():summary['worker_failure']=read_json(failure)
                raise RuntimeError(stage+' exited '+str(child.returncode))
        hf=read_json(out/'hf_report.json')
        completed=[read_json(p) for p in sorted((out/'completed').glob('*.json'))]
        expected={s for g in cfg['hf_groups'] for s in g['slots']}|({cfg['native_slot']['slot']} if cfg.get('native_slot') else set())
        if {r['slot'] for r in completed}!=expected:raise RuntimeError('Required smoke positions missing')
        parity=[r['parity']['passed'] for r in completed if 'parity' in r]
        if len(parity)!=cfg.get('expected_parity_pairs',4) or not all(parity):raise RuntimeError('Incomplete native/identity evidence')
        if hf['attention_error'] or hf['attention_missed']:raise RuntimeError('Attention instrumentation incomplete')
        # No inference-speed claim is inferred from numerical equality. Report
        # small-sample timings separately; human review precedes any activation.
        summary.update(status='completed_pending_review',gpu_qualified=False,review_required=True,
            pending=['persisted input/output and accounting review','attention and token-operation speed acceptance','formal runtime resource estimate'],
            paths_exercised=sorted({g.get('method',g['mode']) for g in cfg['hf_groups']}),formal_started=False)
    except BaseException as exc:
        summary.update(status='timeout_blocked' if isinstance(exc,TimeoutError) else 'stopped' if isinstance(exc,InterruptedError) else 'failed',
            error=repr(exc),traceback=traceback.format_exc(),gpu_qualified=False)
        print(summary['traceback'],flush=True)
    finally:
        if child is not None:
            try:os.killpg(child.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid,signal.SIGKILL);child.wait()
        summary['elapsed_seconds']=round(time.time()-start,2)
        summary['calls_completed']=len(list((out/'completed').glob('*.json')))
        if (out/'calls.sqlite').exists():
            with sqlite3.connect(out/'calls.sqlite') as db:summary['calls_started']=db.execute('SELECT count(*) FROM calls').fetchone()[0]
        summary['historical_probe_calls']=12;summary['formal_started']=False
        save_json(out/'summary.json',summary);save_json(out/'status.json',summary)
        lock.close()
    return summary


def smoke_worker_authority():
    cfg=smoke_runtime_config();out=ROOT/cfg['output']
    started=read_json(out/'started.json')
    if os.getppid()!=started['pid'] or time.time()-started['started_unix']>=cfg['wall_seconds']:
        raise PermissionError('Worker requires the live bounded supervisor; no standalone model entry')
    return cfg


def smoke_worker_entry(kind):
    """Preserve the underlying worker exception for the monitoring summary."""
    cfg=smoke_worker_authority();out=ROOT/cfg['output']
    try:
        return smoke_hf_worker() if kind=='hf' else smoke_native_worker()
    except Exception as exc:
        failure={'status':'infrastructure_failure','worker':kind,'error':repr(exc),'traceback':traceback.format_exc(),'pid':os.getpid()}
        save_json(out/'worker_failure.json',failure)
        if (out/'calls.sqlite').exists():
            from vlmrca.run_state import DurableCallRegister
            ledger=DurableCallRegister(out/'calls.sqlite',limit=18,scope=cfg.get('ledger_scope','rq41_smoke_v18'))
            with ledger.connect() as db:pending=db.execute("SELECT id FROM calls WHERE state='started'").fetchall()
            for (call_id,) in pending:ledger.finish(call_id,failure,state='infrastructure_failure')
        raise
