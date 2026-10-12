"""SourceViewPacketV1, deterministic complete-card selection and requests."""
from .utils import ROOT, RQ, RESULTS, HISTORY, MODEL, read, save, digest, stable

ARMS = ('SOURCE_ZOOM', 'REPEAT_VIEW', 'HASH_ZOOM')


def prompt_contract(processor):
    """Only inherited static task text and explicit multiview reading conventions."""
    index=read(HISTORY/'deployment_v26/request_index.json')['requests']
    references=[v for k,v in index.items() if k.endswith('__VISUAL__BASE')]
    templates={stable([v['system'],v['parts']]) for v in references}
    if len(templates)!=1:
        raise ValueError('Historical visual instructions vary: inspect before inheriting')
    original=references[0]
    text='\n'.join(p['text'] for p in original['parts'])
    text+='\nThe first image is the complete overview. The second image contains enlarged local views of complete original panels. Match original panel indices and labels across images. A local view repeats the same observations: repetition is not independent corroboration and selection does not mean an entity is more likely to be the cause. Use the complete overview for all other evidence.'
    messages=[{'role':'system','content':original['system']},{'role':'user','content':[
        {'type':'image'},{'type':'image'},{'type':'text','text':text}]}]
    prompt=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
    # Each image placeholder is replaced by its patches. Image boundary IDs stay.
    shell=len(processor.tokenizer(prompt,add_special_tokens=False)['input_ids'])-2
    return {'messages':messages,'prompt':prompt,'shell_tokens':shell,'inherited_task_hash':stable([original['system'],original['parts']])}


def detail_budget(full_tokens, kept_tokens, shell_tokens):
    import math
    return min(8192,16384-kept_tokens,math.floor(.8*full_tokens)-kept_tokens-shell_tokens)


def card_inventory(evidence, provenance, audit, processed_pixels, source_pixels, source_regions=None):
    """Public-only measurements. Fact values never enter priority scoring."""
    import math
    cards={c['id']:c for c in evidence['cards']}
    occurrences={}
    for role in provenance['roles']:
        for target in role['targets']:
            card=target['binding'].split('.')[0]
            occurrences.setdefault(card,set()).add(role['source_occurrence'])
    ratio=min(a/b for a,b in zip(processed_pixels,source_pixels))
    output=[]
    for panel in audit['panels']:
        card=cards[panel['card']]
        if panel['min_font_px'] is None:
            raise ValueError('Source card has no measurable text')
        # A scalar does not change wrapping or the source DOM. Tiny upward
        # rounding avoids a browser subpixel falling below the hard floor.
        scale=math.ceil(max(1.,18/panel['min_font_px'],1.5/panel['min_line_px'] if panel['min_line_px'] else 1.)*1024)/1024
        width=panel['box'][2]*scale;height=panel['box'][3]*scale
        restored=sum(t['chars'] for t in panel['texts'] if t['font_px']*ratio<18)
        area_tokens=math.ceil(width/32)*math.ceil(height/32)
        kind=card['kind']
        # Inventory is a directory, not a diagnostic plot. The complete
        # directory remains in U; do not promote it into a text screenshot.
        modality={'metric':'M','trace':'R','trace_joint':'R','log':'L','graph':'G'}.get(kind)
        if kind=='comparison':
            regions={source_regions[s.split('/')[0]] for s in occurrences.get(card['id'],set()) if s.split('/')[0] in (source_regions or {})}
            if len(regions)!=1:
                raise ValueError('Comparison source modality is not uniquely bound')
            modality=regions.pop()
        output.append({'card':card['id'],'entity':card.get('entity'),'modality':modality,
            'sources':sorted(occurrences.get(card['id'],set())), 'source_id':stable([card['id'],sorted(occurrences.get(card['id'],set()))]),
            'source_width':panel['box'][2],'source_height':panel['box'][3],
            'width':width,'height':height,'scale':scale,'restored_chars':restored,'area_tokens':area_tokens,
            'eligible':modality is not None and not panel['overflow'] and width<=2016 and restored>0,
            'original_min_font':panel['min_font_px'],'original_min_line':panel['min_line_px'],
            'source_box':panel['box'],'bindings':panel['bindings'],'overflow_count':len(panel['overflow'])})
    return output


def select_atlas(inventory, budget, mode):
    """Coverage rounds, deterministic next-fit shelves, no partial cards.

    Within a round prioritize a new modality then a new entity, then the
    registered utility (or fixed hash). A completed coverage round resets the
    sets. Width, canvas and algorithm are identical for SOURCE/HASH.
    """
    import math
    if mode not in {'SOURCE_ZOOM','HASH_ZOOM'}:
        raise ValueError('Unknown source selection policy')
    height=math.floor(budget/64)*32
    if height<64:
        raise ValueError('No complete detail canvas budget')
    remaining=[c.copy() for c in inventory if c['eligible']]
    placements=[];x=y=16;shelf=0;modalities=set();entities=set();skipped=[]
    while remaining:
        if {c['modality'] for c in remaining}<=modalities and {str(c['entity']) for c in remaining}<=entities:
            modalities.clear();entities.clear()
        def priority(c):
            value=-(c['restored_chars']/c['area_tokens']) if mode=='SOURCE_ZOOM' else stable(['rq44-hash-card-v1',c['source_id']])
            return (c['modality'] in modalities,str(c['entity']) in entities,value,c['source_id'])
        card=min(remaining,key=priority);remaining.remove(card)
        px,py=x,y;new_shelf=shelf
        if px+card['width']>2032:
            px=16;py=y+shelf+16;new_shelf=0
        if py+card['height']>height-16:
            skipped.append(card['card']);continue
        placements.append({k:card[k] for k in ('card','width','height','scale','source_width','source_height')}|{'x':px,'y':py})
        x=math.ceil(px+card['width'])+16;y=py;shelf=max(new_shelf,math.ceil(card['height']))
        modalities.add(card['modality']);entities.add(str(card['entity']))
    if not placements:
        raise ValueError('No complete readable source card fits registered atlas')
    return {'width':2048,'height':height,'placements':placements},skipped


def exact_processed_overview(processor, image, expected_pixels):
    """The actual HF resize implementation and unchanged resample settings."""
    import torch
    import numpy as np
    from PIL import Image
    from transformers.image_utils import SizeDict
    from transformers.models.qwen2_vl.image_processing_qwen2_vl import smart_resize
    ip=processor.image_processor
    h,w=smart_resize(image.height,image.width,factor=ip.patch_size*ip.merge_size,
        min_pixels=ip.size['shortest_edge'],max_pixels=ip.size['longest_edge'])
    if [w,h]!=expected_pixels:
        raise ValueError('Historical overview processor geometry changed')
    tensor=torch.from_numpy(np.asarray(image.convert('RGB')).copy()).permute(2,0,1)[None]
    resized=ip.resize(tensor,size=SizeDict(height=h,width=w),resample=ip.resample)[0]
    if resized.dtype!=torch.uint8:
        raise ValueError('Unexpected source resize dtype')
    return Image.fromarray(resized.permute(1,2,0).numpy())


def compile_case(row, renderer, processor, contract, render_images=True):
    import math,time
    from PIL import Image
    from collections import Counter
    from .utils import historical
    from renderer.operations.source_views import repeat_view
    began=time.monotonic();base,old=historical(row);source=read(base/'processor_cpu.json')
    evidence=read(base/'evidence.json');provenance=read(base/'provenance.json')
    retained=old['actual_retention']['indices']
    if retained!=sorted(set(retained)) or retained[-1]>=source['image_tokens']:
        raise ValueError('Invalid historical retained sequence')
    full=read(HISTORY/f'formal_v28/completed/{row["id"]}__development__T_FULL__BASE.json')['input_tokens']
    budget=detail_budget(full,len(retained),contract['shell_tokens'])
    html=base/'render/dashboard.html';png=base/'render/dashboard.png'
    if digest(png)!=source['png_sha256']:
        raise ValueError('Historical overview image mismatch')
    audit=renderer.audit(html,source['source_pixels'])
    import json
    source_regions={}
    for part in read(base/'text_conditions.json')['T_LEDGER']:
        for line in part['text'].splitlines():
            if line.startswith('{"source":'):
                record=json.loads(line)
                if isinstance(record.get('value'),dict) and record['value'].get('region') in {'M','R','L','G'}:
                    source_regions[record['source']]=record['value']['region']
    inventory=card_inventory(evidence,provenance,audit,source['processed_pixels'],source['source_pixels'],source_regions)
    specs={};skipped={}
    for arm in ('SOURCE_ZOOM','HASH_ZOOM'):
        specs[arm],skipped[arm]=select_atlas(inventory,budget,arm)
    specs['REPEAT_VIEW']=specs['SOURCE_ZOOM']
    dest=RESULTS/'inputs'/row['id'];dest.mkdir(parents=True,exist_ok=True)
    packet={'schema':'SourceViewPacketV1','overview':str(png.relative_to(ROOT)),
        'overview_sha256':digest(png),'source_html':str(html.relative_to(ROOT)), 'source_html_sha256':digest(html),
        'evidence_sha256':digest(base/'evidence.json'),'provenance_sha256':digest(base/'provenance.json'),
        'source_pixels':source['source_pixels'],'processed_pixels':source['processed_pixels'],
        'overview_grid_thw':source['grid_thw'],'overview_image_tokens':source['image_tokens'],
        'overview_retained':retained,'full_text_input_tokens':full,'shell_tokens':contract['shell_tokens'],
        'detail_budget':budget,'inventory':inventory,'specs':specs,'skipped':skipped,
        'source_fact_hash':stable(evidence),'source_candidate_hash':stable([c for c in evidence['cards'] if c['kind']=='inventory']),
        'selector_value_fields':False,'render_operation':'source_views'}
    save(dest/'source_view_packet.json',packet)
    result={'id':row['id'],'dataset':row['dataset'],'detail_budget':budget,'selected':{k:len(v['placements']) for k,v in specs.items()},
        'eligible_cards':sum(c['eligible'] for c in inventory),'status':'geometry_compiled','rendered':False}
    if not render_images:
        result['seconds']=time.monotonic()-began
        return result
    by_id={p['card']:p for p in audit['panels']};audits={}
    for arm in ('SOURCE_ZOOM','HASH_ZOOM'):
        out=dest/arm
        report=renderer.export(html,source['source_pixels'],specs[arm],out)
        for panel in report['panels']:
            prior=by_id[panel['card']]
            if Counter(panel['bindings'])!=Counter(prior['bindings']) or [t['text'] for t in panel['texts']]!=[t['text'] for t in prior['texts']]:
                raise ValueError('Export changed original source glyphs/bindings')
            if panel['min_font_px']<18-1e-6 or (panel['min_line_px'] is not None and panel['min_line_px']<1.5-1e-6) or panel['overflow']:
                raise ValueError('Actual source view readability/bounds failed: '+panel['card'])
        save(out/'geometry.json',report);audits[arm]=report
    with Image.open(png) as im:
        processed=exact_processed_overview(processor,im,source['processed_pixels'])
    repeat=repeat_view(processed,source['source_pixels'],audit['panels'],specs['SOURCE_ZOOM'],dest/'REPEAT_VIEW/dashboard.png')
    save(dest/'REPEAT_VIEW/geometry.json',repeat)
    processor_results={}
    # The full overview is reused exactly; actual multimodal tokenization checks
    # every control independently, including resized pixel equality for image 0.
    overview_values=None
    for arm in ARMS:
        with Image.open(png) as a,Image.open(dest/arm/'dashboard.png') as b:
            batch=processor(text=[contract['prompt']],images=[a.convert('RGB'),b.convert('RGB')],return_tensors='pt')
        grids=batch['image_grid_thw'].tolist();n=[math.prod(g)//4 for g in grids]
        if len(grids)!=2 or grids[0]!=source['grid_thw']:
            raise ValueError('Multi-image processing changed overview grid')
        patches=batch['pixel_values'][:math.prod(grids[0])]
        if overview_values is None:
            overview_values=patches.clone()
        elif not (patches==overview_values).all():
            raise ValueError('Overview pixels differ across conditions')
        text=int(batch['input_ids'].shape[-1])-sum(n)
        processed_size=[grids[1][2]*16,grids[1][1]*16]
        spec=specs[arm]
        if processed_size!=[spec['width'],spec['height']]:
            raise ValueError('Detail view was unexpectedly rescaled')
        actual=text+len(retained)+n[1]
        if text!=contract['shell_tokens'] or n[1]>budget or actual+8192>40960 or actual>math.floor(.8*full):
            raise ValueError('Actual processor budget failed')
        processor_results[arm]={'grid_thw':grids,'encoded_image_tokens':sum(n),'retained_image_tokens':len(retained)+n[1],
            'detail_image_tokens':n[1],'input_tokens':actual,'shell_tokens':text,'png_sha256':digest(dest/arm/'dashboard.png')}
        del batch
    if processor_results['SOURCE_ZOOM']['png_sha256']==processor_results['REPEAT_VIEW']['png_sha256']:
        raise ValueError('High-resolution and repeat controls are identical')
    save(dest/'processor.json',processor_results)
    result.update(status='passed',rendered=True,processor=processor_results,seconds=time.monotonic()-began)
    return result


QA_INSTRUCTION='''Read the white-outlined panel. For its FIRST reference/current comparison, copy the displayed reference value, current value, owning entity ID, and unit of that comparison. State whether reference is greater, current is greater, or they are equal at displayed precision. A repeated panel is the same observation. Return only JSON with string fields reference, current, entity, unit, and comparison. comparison is reference_greater, current_greater, equal, or unavailable. Use unavailable for an unreadable field. This is a reading task, not a root-cause diagnosis.'''


def mechanism_roster(rows):
    chosen=[]
    for dataset in sorted({r['dataset'] for r in rows}):
        pool=sorted((r for r in rows if r['dataset']==dataset),key=lambda r:stable(['rq44-mechanism-v1',r['id']]))
        groups=set();selected=[]
        for r in pool:
            if r['event_group'] not in groups and len(selected)<10:
                selected.append(r);groups.add(r['event_group'])
        selected.extend(r for r in pool if r not in selected and len(selected)<10)
        if len(selected)!=10:
            raise ValueError('Mechanism roster incomplete')
        chosen.extend(selected)
    return chosen


def geometry_for(source_packet, arm, source_manifest):
    overview={'width':source_packet['source_pixels'][0],'height':source_packet['source_pixels'][1],
        'panels':[{'card':p['card'],'box':[p['x'],p['y'],p['width'],p['height']]} for p in source_manifest['rectangles']]}
    spec=source_packet['specs'][arm]
    detail={'width':spec['width'],'height':spec['height'],
        'panels':[{'card':p['card'],'box':[p['x'],p['y'],p['width'],p['height']]} for p in spec['placements']]}
    return [overview,detail]


def make_request(row, arm, variant='BASE', attention=False):
    from .utils import historical
    base,old=historical(row);folder=RESULTS/'inputs'/row['id']
    packet=read(folder/'source_view_packet.json');proc=read(folder/'processor.json')[arm]
    prompt=read(RESULTS/'prompt_contract.json')['prompt']
    images=[packet['overview'],str((folder/arm/'dashboard.png').relative_to(ROOT))]
    retained=[packet['overview_retained'],list(range(proc['detail_image_tokens']))]
    geometry=geometry_for(packet,arm,read(base/'render/manifest.json'))
    tokens=proc['input_tokens'];task='RCA'
    if variant in {'QA','ISOLATED_QA','ORDER'}:
        spec=read(RESULTS/'mechanism'/row['id']/'requests.json')[arm+'__'+variant]
        images=spec['images'];retained=spec['retained_by_image'];geometry=spec['geometry'];tokens=spec['input_tokens'];prompt=spec['prompt']
        task='QA' if variant!='ORDER' else 'RCA'
    seed=old['decoder_seed'] if variant=='BASE' else int(stable(['rq44-call-seed-v1',row['id'],variant])[:8],16)%2147483647
    request={'prompt':prompt,'images':images,'retained_by_image':retained,'geometry':geometry,'input_tokens':tokens,
        'task':task,'seed':seed,'attention':attention,'image_sha256':[digest(ROOT/p) for p in images]}
    # Identity includes the actual operation and all position/processor/model
    # dependencies. Observation-only attention is recorded, not a generation arm.
    identity={k:v for k,v in request.items() if k not in {'attention','geometry','images'}}
    identity['model_config']={p:digest(MODEL/p) for p in ('config.json','preprocessor_config.json','tokenizer_config.json','chat_template.jinja')}
    identity['operation']='native_visual_encode;image0_exact_U;other_images_full;native_mrope;bf16_vllm'
    identity['decoding']='RQ43_rank_greedy_reason_sampled_v13'
    request['identity']=stable(identity)
    return request


def build_queue(scope='formal'):
    from .utils import roster
    rows=roster();mechanism={r['id'] for r in read(RESULTS/'mechanism_roster.json')['formal']}
    queue=[]
    if scope=='smoke':
        fixed=read(RESULTS/'mechanism_roster.json')['smoke_ids']
        rows=sorted((r for r in rows if r['id'] in fixed),key=lambda r:r['dataset'])
        for i,row in enumerate(rows):
            queue.extend((row,a,'BASE') for a in ARMS)
            queue.extend((row,a,'QA') for a in (ARMS[i%3],ARMS[(i+1)%3]))
            queue.append((row,'SOURCE_ZOOM','ISOLATED_QA'))
    else:
        for i,row in enumerate(sorted(rows,key=lambda r:stable(['rq44-formal-order-v1',r['id']]))):
            arms=ARMS[i%3:]+ARMS[:i%3]
            queue.extend((row,a,'BASE') for a in arms)
            if row['id'] in mechanism:
                queue.extend((row,a,'QA') for a in ARMS)
                queue.extend((row,'SOURCE_ZOOM',v) for v in ('ISOLATED_QA','REPEAT','ORDER'))
    result=[];seen={}
    for row,arm,variant in queue:
        attention=(row['id'] in mechanism) if scope=='formal' else len(result)%2==0
        request=make_request(row,arm,variant,attention)
        item={'key':f'{scope}__{row["id"]}__{arm}__{variant}','id':row['id'],'dataset':row['dataset'],
              'arm':arm,'variant':variant,'task':request['task'],'identity':request['identity']}
        if variant!='REPEAT' and request['identity'] in seen:
            item['reference']=seen[request['identity']]
        else:
            seen[request['identity']]=item['key']
        result.append({'item':item,'request':request})
    if len(result)!=(18 if scope=='smoke' else 840):
        raise ValueError('Registered queue length differs')
    return result


def cold_render_check(row, arm, variant, renderer, processor, contract):
    """Cold method work in RAM, then compare with immutable registered pixels."""
    import tempfile,json,time
    from PIL import Image
    from .utils import historical
    from renderer.operations.source_views import repeat_view
    began=time.monotonic();base,_=historical(row);frozen=read(RESULTS/'inputs'/row['id']/'source_view_packet.json')
    evidence=read(base/'evidence.json');provenance=read(base/'provenance.json')
    audit=renderer.audit(base/'render/dashboard.html',frozen['source_pixels']);regions={}
    for part in read(base/'text_conditions.json')['T_LEDGER']:
        for line in part['text'].splitlines():
            if line.startswith('{"source":'):
                record=json.loads(line)
                if isinstance(record.get('value'),dict) and record['value'].get('region') in {'M','R','L','G'}:
                    regions[record['source']]=record['value']['region']
    inventory=card_inventory(evidence,provenance,audit,frozen['processed_pixels'],frozen['source_pixels'],regions)
    selected,_=select_atlas(inventory,frozen['detail_budget'],'SOURCE_ZOOM' if arm=='REPEAT_VIEW' else arm)
    if selected!=frozen['specs'][arm] or stable(evidence)!=frozen['source_fact_hash']:
        raise ValueError('Cold compilation differs from frozen inputs')
    compiled=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='canvasrq44-',dir='/dev/shm') as temporary:
        from pathlib import Path
        folder=Path(temporary)
        if arm=='REPEAT_VIEW':
            with Image.open(ROOT/frozen['overview']) as im:
                resized=exact_processed_overview(processor,im,frozen['processed_pixels'])
            target=folder/'dashboard.png';repeat_view(resized,frozen['source_pixels'],audit['panels'],selected,target)
        else:
            renderer.export(base/'render/dashboard.html',frozen['source_pixels'],selected,folder/'render')
            target=folder/'render/dashboard.png'
        expected=RESULTS/'inputs'/row['id']/arm/'dashboard.png'
        if digest(target)!=digest(expected):
            raise ValueError('Deterministic cold repaint differs')
    return {'source_read_and_compile_seconds':compiled-began,'render_seconds':time.monotonic()-compiled,
            'cold_repaint_identical':True,'disk_buffer':False}


def prepare_mechanism(row,renderer,processor):
    import math,copy
    from decimal import Decimal
    from PIL import Image
    from .utils import historical
    from renderer.operations.source_views import mark_source_panel
    base,_=historical(row);folder=RESULTS/'inputs'/row['id'];dest=RESULTS/'mechanism'/row['id'];dest.mkdir(parents=True,exist_ok=True)
    packet=read(folder/'source_view_packet.json');manifest=read(base/'render/manifest.json')
    evidence=read(base/'evidence.json');cards={c['id']:c for c in evidence['cards']}
    eligible=[c for c in packet['inventory'] if c['eligible'] and cards[c['card']]['kind']=='comparison' and cards[c['card']].get('entity')]
    if not eligible:
        raise ValueError('No source-bound phase comparison QA can be instantiated')
    target=min(eligible,key=lambda c:stable(['rq44-qa-target-v1',row['id'],c['source_id']]))
    dom=renderer.audit(base/'render/dashboard.html',packet['source_pixels']);panel=next(p for p in dom['panels'] if p['card']==target['card'])
    answers={}
    for phase in ('reference','current'):
        values=[t['text'] for t in panel['texts'] if t['binding']==f'{target["card"]}.comparison.0.{phase}']
        if len(values)!=1:
            raise ValueError('QA value is not uniquely displayed')
        answers[phase]=values[0]
    def decimal(text):
        suffix={'k':3,'M':6,'G':9}
        return Decimal(text[:-1])*Decimal(10)**suffix[text[-1]] if text[-1] in suffix else Decimal(text)
    a,b=map(decimal,(answers['reference'],answers['current']))
    answers.update(entity=cards[target['card']]['entity'],unit=cards[target['card']]['data']['comparisons'][0]['unit'],
        comparison='reference_greater' if a>b else 'current_greater' if b>a else 'equal')
    save(dest/'answers_audit_only.json',{'target':target['card'],'answers':answers,'source_bindings':panel['bindings'],
        'selection':'public fixed hash; independent of method selection and RCA/QA answers'})
    mark_source_panel(ROOT/packet['overview'],dest/'overview_qa.png',target['source_box'])
    requests={}
    for arm in ARMS:
        geometry=geometry_for(packet,arm,manifest)
        detail=folder/arm/'dashboard.png'
        found=[p for p in geometry[1]['panels'] if p['card']==target['card']]
        if found:
            detail=dest/arm/'qa.png';mark_source_panel(folder/arm/'dashboard.png',detail,found[0]['box'])
        images=[dest/'overview_qa.png',detail]
        requests[arm+'__QA']=measure_request(processor,images,QA_INSTRUCTION,packet['overview_retained'],geometry,'QA')
    # A complete source card at the same high-definition floor, no RCA labels.
    spec={'width':2048,'height':math.ceil((target['height']+32)/32)*32,'placements':[
        {k:target[k] for k in ('card','width','height','scale','source_width','source_height')}|{'x':16,'y':16}]}
    isolation=dest/'isolated';audit=renderer.export(base/'render/dashboard.html',packet['source_pixels'],spec,isolation)
    p=spec['placements'][0];mark_source_panel(isolation/'dashboard.png',isolation/'qa.png',[p['x'],p['y'],p['width'],p['height']])
    geometry=[{'width':spec['width'],'height':spec['height'],'panels':[{'card':p['card'],'box':[p['x'],p['y'],p['width'],p['height']]}]}]
    requests['SOURCE_ZOOM__ISOLATED_QA']=measure_request(processor,[isolation/'qa.png'],QA_INSTRUCTION,None,geometry,'QA')
    # Rotate complete cards in deterministic shelf order; preserve their pixel
    # size. Use the original atlas rectangles as destination slots only when
    # they have the same shape; otherwise repack under the SAME canvas budget.
    oldspec=packet['specs']['SOURCE_ZOOM'];items=copy.deepcopy(oldspec['placements'])
    cut=len(items)//2;items=items[cut:]+items[:cut];x=y=16;shelf=0
    for p in items:
        if x+p['width']>2032:
            x=16;y+=shelf+16;shelf=0
        p['x']=x;p['y']=y;x=math.ceil(x+p['width'])+16;shelf=max(shelf,math.ceil(p['height']))
    order_spec=dict(oldspec,placements=items)
    renderer.export(base/'render/dashboard.html',packet['source_pixels'],order_spec,dest/'order')
    order_geo=geometry_for(packet,'SOURCE_ZOOM',manifest)
    order_geo[1]['panels']=[{'card':p['card'],'box':[p['x'],p['y'],p['width'],p['height']]} for p in items]
    request=measure_request(processor,[ROOT/packet['overview'],dest/'order/dashboard.png'],None,packet['overview_retained'],order_geo,'RCA')
    requests['SOURCE_ZOOM__ORDER']=request
    save(dest/'requests.json',requests)
    return {'id':row['id'],'dataset':row['dataset'],'status':'passed','target':target['card'],
        'target_in_detail':{a:any(p['card']==target['card'] for p in packet['specs'][a]['placements']) for a in ARMS},
        'request_count':len(requests),'source_card_count':len(items)}


def measure_request(processor,images,instruction,first_retained,geometry,task):
    import math
    from PIL import Image
    if instruction is None:
        prompt=read(RESULTS/'prompt_contract.json')['prompt']
    else:
        prompt=processor.apply_chat_template([{'role':'system','content':'Read public telemetry graphics accurately.'},
            {'role':'user','content':[{'type':'image'} for _ in images]+[{'type':'text','text':instruction}]}],
            tokenize=False,add_generation_prompt=True,enable_thinking=False)
    opened=[]
    for path in images:
        with Image.open(path) as im:
            opened.append(im.convert('RGB'))
    batch=processor(text=[prompt],images=opened,return_tensors='pt')
    grids=batch['image_grid_thw'].tolist();counts=[math.prod(g)//4 for g in grids]
    retained=[list(range(n)) for n in counts]
    if first_retained is not None:
        retained[0]=first_retained
    text=batch['input_ids'].shape[-1]-sum(counts);n=text+sum(map(len,retained))
    if n+8192>40960:
        raise ValueError('Mechanism context capacity exceeded')
    return {'images':[str(p.relative_to(ROOT)) for p in images],'prompt':prompt,'input_tokens':n,
        'retained_by_image':retained,'geometry':geometry,'task':task,'grid_thw':grids}


# Frozen RQ4.3 vLLM adapter port; operation U only. No legacy source is edited.
class VLLMWorkerExtension:
    """One isolated worker extension; never edit vLLM/HF or historical source.

    Native vLLM owns every layer's KV/linear state and batched decode. Overrides
    affect only explicit positions, registered prefill outputs and passive taps.
    No synthetic tokens, additional language-model calls or cloned checkpoints.
    """
    def rq43_install(self,attention_folder):
        import torch
        from types import MethodType
        from vlmrca.vlm.passive_summary import AttentionStore
        from .utils import validate_vllm_metadata
        if hasattr(self,'_rq43_state'):raise RuntimeError('Worker adapter already installed')
        runner=self.model_runner;model=runner.get_model()
        if self.vllm_config.model_config.dtype!=torch.bfloat16 or self.vllm_config.parallel_config.tensor_parallel_size!=1:
            raise RuntimeError('Only registered BF16 TP1 backend')
        if self.vllm_config.scheduler_config.enable_chunked_prefill or self.vllm_config.cache_config.enable_prefix_caching:
            raise RuntimeError('Registered intervention requires fresh, complete prefill')
        state={'records':[],'requests':{},'batches':0,'decode_batches':0,'max_decode_batch':0,'max_batch':0,'preemptions':0,
            'store':AttentionStore(attention_folder),'runner':runner,'model':model,'scheduled':None}
        self._rq43_state=state
        old_positions=runner._init_mrope_positions
        def positions(this,req):
            meta=(req.sampling_params.extra_args or {}).get('canvasrca') if req.sampling_params else None
            if meta is None:return old_positions(req)
            validate_vllm_metadata(meta)
            if req.num_prompt_tokens!=meta['length']:raise ValueError('Engine prompt length differs from compiler')
            req.mrope_positions=torch.tensor(meta['positions'],dtype=torch.long)
            req.mrope_position_delta=meta['rope_delta']
        runner._init_mrope_positions=MethodType(positions,runner)
        execute=runner.execute_model
        def execute_wrapper(*args,**kwargs):
            schedule=kwargs.get('scheduler_output',args[0] if args else None)
            preempted=getattr(schedule,'preempted_req_ids',set())
            state['preemptions']+=len(preempted)
            if preempted:raise RuntimeError(f'KV admission failed to prevent recomputation: {sorted(preempted)}')
            state['scheduled']=schedule
            try:return execute(*args,**kwargs)
            finally:state['scheduled']=None;state['records']=[]
        runner.execute_model=execute_wrapper
        forward=model.forward
        def model_forward(*args,**kwargs):
            schedule=state['scheduled'];records=[]
            if schedule is not None:
                offset=0
                for req_id in runner.input_batch.req_ids[:runner.input_batch.num_reqs]:
                    length=schedule.num_scheduled_tokens.get(req_id,0)
                    if not length:continue
                    req=runner.requests[req_id];meta=(req.sampling_params.extra_args or {}).get('canvasrca')
                    if meta is None:raise ValueError('Unregistered request in experiment engine')
                    before=int(runner.input_batch.num_computed_tokens_cpu[runner.input_batch.req_id_to_index[req_id]])
                    prefill=before<req.num_prompt_tokens
                    if prefill and (before!=0 or length!=meta['length']):
                        raise ValueError(f'Split/replayed prefill is not registered: request={req_id}, before={before}, scheduled={length}, prompt={meta["length"]}')
                    if not prefill and length!=1:raise ValueError('Speculative/multi-token decode is not registered')
                    call_key=req.sampling_params.extra_args['canvasrca_call_key']
                    if call_key not in state['requests']:raise ValueError('Unregistered engine request identity')
                    records.append({'key':call_key,'start':offset,'end':offset+length,'prefill':prefill,'meta':meta})
                    offset+=length
                state['batches']+=1;state['max_batch']=max(state['max_batch'],len(records))
                decodes=sum(not r['prefill'] for r in records)
                if decodes:state['decode_batches']+=1;state['max_decode_batch']=max(state['max_decode_batch'],decodes)
            state['records']=records
            return forward(*args,**kwargs)
        model.forward=model_forward
        layers=model.language_model.model.layers
        module=layers[3].self_attn
        def full_attention(positions,output,hidden_states):
            import torch.nn.functional as F
            qkv,_=module.qkv_proj(hidden_states)
            q,k,v,gate=module._project_qkv_gate(qkv,positions)
            attn=module.attn(q,k,v)
            for rec in state['records']:
                entry=state['requests'][rec['key']];meta=rec['meta'];sl=slice(rec['start'],rec['end'])
                qq=q[sl].view(-1,module.num_heads,module.head_dim).transpose(0,1)[None]
                kk=k[sl].view(-1,module.num_kv_heads,module.head_dim).transpose(0,1)[None]
                tap=entry['tap']
                if tap is not None:
                    if rec['prefill']:
                        entry['attention_keys']=kk.clone()
                        tap.observe(entry['attention_module'],qq,kk,None,module.head_dim**-.5)
                    elif entry.get('attention_keys') is not None:
                        keys=torch.cat((entry.pop('attention_keys'),kk),dim=-2)
                        tap.observe(entry['attention_module'],qq,keys,None,module.head_dim**-.5)
            if gate is not None:attn=attn*torch.sigmoid(gate)
            output[:],_=module.o_proj(attn)
        module.forward=full_attention
        return {'schema':'RQ43VLLMInstallationV13','status':'installed','backend':'vllm','dtype':'bfloat16',
            'prefill_intervention_layers':[0,1,2,3],'native_batched_decode':True,'prefix_caching':False,
            'chunked_prefill':False,'new_diagnostic_calls':0}

    def rq43_encode(self,key,packet):
        """Use the loaded encoder/embedding weights; GPU->RAM transport is explicit."""
        import torch,time
        from types import SimpleNamespace
        from .utils import validate_vllm_metadata,stable,vllm_tensor_wire,vllm_tensor_unwire
        from vlmrca.vlm.passive_summary import PassiveAttentionTap
        state=self._rq43_state;model=state['model'];meta=validate_vllm_metadata(packet['metadata'])
        if meta['operation']!='U' or meta['groups']:raise ValueError('RQ4.4 permits only native U encoding')
        if key in state['requests']:raise RuntimeError('Duplicate active engine request')
        began=time.monotonic();batch={k:vllm_tensor_unwire(v) for k,v in packet['batch'].items()};tap=None
        with torch.inference_mode():
            ids=batch['input_ids'].to('cuda');vectors=model.language_model.embed_input_ids(ids[0])
            if packet['image_positions']:
                pixels=batch['pixel_values'].to(device='cuda',dtype=torch.bfloat16);grid=batch['image_grid_thw'].to('cuda')
                features=model.visual(pixels,grid_thw=grid)
                if features.shape!=(len(packet['image_positions']),vectors.shape[-1]):raise ValueError('Actual encoder token shape mismatch')
                vectors[packet['image_positions']]=features
            vectors=vectors[packet['keep']][packet['source_by_slot']]
            if vectors.shape[0]!=meta['length']:raise ValueError('Actual embedding prefix differs')
            if meta['attention'] is not None:
                a=meta['attention'];tap=PassiveAttentionTap(state['store'])
                tap.begin(key,torch.tensor(a['ids'],device='cuda',dtype=torch.long),a['names'],stable(a['ids']))
            host=vectors.to('cpu')
        state['requests'][key]={'branch_calls':0,'tap':tap,'attention_module':SimpleNamespace(layer_idx=3),
            'admitted_monotonic':began,'encoder_transport_seconds':time.monotonic()-began}
        return vllm_tensor_wire(host)

    def rq43_cache_profile(self):
        from .utils import vllm_cache_profile
        return vllm_cache_profile(self.model_runner.kv_cache_config)

    def rq43_finish(self,key):
        import time
        state=self._rq43_state;entry=state['requests'].pop(key)
        tap=entry['tap'];error=None;missed=0
        if tap is not None:
            tap.close();state['store'].queue.join();error=tap.error;missed=tap.missed
        return {k:v for k,v in entry.items() if k not in {'tap','attention_module','attention_keys'}}|{
            'attention_error':error,'attention_missed':missed,'finished_monotonic':time.monotonic(),
            'engine_batches':state['batches'],'engine_decode_batches':state['decode_batches'],
            'engine_max_batch':state['max_batch'],'engine_max_decode_batch':state['max_decode_batch'],
            'engine_preemptions':state['preemptions']}

    def rq43_shutdown(self):
        state=self._rq43_state
        if state['requests']:raise RuntimeError('Refuse clean shutdown with unfinished model requests')
        state['store'].close();return {'status':'drained','max_decode_batch':state['max_decode_batch']}

class VLLMSolvers:
    """Synchronous provider boundary backed by one AsyncLLM continuous engine."""
    def __init__(self,scope,folder,deadline=None):
        from .gates import require_execution
        require_execution(scope)
        import asyncio,threading,concurrent.futures
        from transformers import AutoProcessor
        from .utils import RQ
        self.local=threading.local();self.solvers=[];self.folder=folder;self.deadline=deadline;self.engine_stats={}
        self.processor=AutoProcessor.from_pretrained(str(MODEL),local_files_only=True)
        eos=read(MODEL/'generation_config.json')['eos_token_id']
        self.stop_token_ids=sorted(set(eos if isinstance(eos,list) else [eos]))
        import xgrammar as xgr
        from .utils import rca_schema
        self.rca_grammar=str(xgr.Grammar.from_json_schema(rca_schema(True),any_whitespace=False))
        self.loop=asyncio.new_event_loop();self.ready=concurrent.futures.Future()
        self.thread=threading.Thread(target=self._serve,name='rq43-vllm-control',daemon=True);self.thread.start()
        import time
        self.warmup=self.ready.result(timeout=max(.1,min(900,deadline-time.monotonic())) if deadline else 900)
    def _serve(self):
        import asyncio
        asyncio.set_event_loop(self.loop)
        async def start():
            import time
            from vllm.engine.arg_utils import AsyncEngineArgs
            from vllm.v1.engine.async_llm import AsyncLLM
            from .utils import RQ,VLLMCacheAdmission
            cfg=read(RQ/'configs/execution_v1.json');began=time.monotonic()
            self.engine=AsyncLLM.from_engine_args(AsyncEngineArgs(**dict(cfg['engine'],model=str(MODEL))),start_engine_loop=True)
            installed=await self.engine.collective_rpc('rq43_install',args=(str(self.folder),))
            profile=(await self.engine.collective_rpc('rq43_cache_profile'))[0]
            self.admission=VLLMCacheAdmission(profile)
            return {'status':'initialized','backend':'vllm','seconds':time.monotonic()-began,'model_calls':0,'adapter':installed,
                'cache_admission':profile,'operational_revision':'kv_admission_v19'}
        try:self.ready.set_result(self.loop.run_until_complete(start()));self.loop.run_forever()
        except BaseException as exc:
            if not self.ready.done():self.ready.set_exception(exc)
        finally:
            if hasattr(self,'engine'):self.engine.shutdown()
            pending=asyncio.all_tasks(self.loop)
            for task in pending:task.cancel()
            if pending:self.loop.run_until_complete(asyncio.gather(*pending,return_exceptions=True))
            self.loop.close()
    @property
    def last_usage(self):return self.local.usage
    def await_request(self,future,poll_seconds=1.):
        """Engine death also fails requests stuck in RPC, not just generate()."""
        from concurrent.futures import TimeoutError
        import time
        while True:
            try:return future.result(timeout=poll_seconds)
            except TimeoutError:
                if future.done():return future.result()
                if not self.thread.is_alive() or self.engine.errored:
                    future.cancel();raise RuntimeError('vLLM engine died while awaiting request; no output committed')
                if self.deadline is not None and time.monotonic()>=self.deadline:
                    future.cancel();raise TimeoutError('Registered GPU deadline exhausted')
    def __call__(self,request):
        import asyncio,time
        from .utils import vllm_prompt_packet
        began=time.monotonic();packet=vllm_prompt_packet(request,self.processor)
        response,usage=self.await_request(asyncio.run_coroutine_threadsafe(self._request(request,packet,began),self.loop))
        self.local.usage=usage;return response
    def invoke(self,request,packet):
        import asyncio,time
        response,usage=self.await_request(asyncio.run_coroutine_threadsafe(self._request(request,packet,time.monotonic()),self.loop))
        self.local.usage=usage
        return response
    async def _request(self,request,packet,began):
        import time,asyncio
        from vllm import SamplingParams
        from vllm.sampling_params import StructuredOutputsParams,RequestOutputKind
        from .utils import rca_schema,stable,vllm_tensor_wire,vllm_tensor_unwire
        meta=packet['metadata'];key=stable([request['identity'],time.time_ns()])
        encoded=False;submitted=False;reserved=False
        try:
            if self.engine.errored:raise self.engine.dead_error
            reservation=await self.admission.acquire(key,meta['length']);reserved=True
            if self.engine.errored:raise self.engine.dead_error
            packet=dict(packet,batch={k:vllm_tensor_wire(v) for k,v in packet['batch'].items()})
            wire=(await self.engine.collective_rpc('rq43_encode',args=(key,packet)))[0];encoded=True
            embeddings=vllm_tensor_unwire(wire)
            prompt={'prompt_embeds':embeddings,'prompt_token_ids':packet['token_ids'],
                'prompt_is_token_ids':[False]*meta['length']}
            grammar=StructuredOutputsParams(grammar=self.rca_grammar) if request['task']=='RCA' else StructuredOutputsParams(json=__import__('RQs.RQ4_4.src.utils',fromlist=['qa_schema']).qa_schema())
            params=SamplingParams(temperature=1.,top_p=.95,top_k=-1,seed=request['seed'],max_tokens=8192,
                stop_token_ids=self.stop_token_ids,structured_outputs=grammar,
                extra_args={'canvasrca':meta,'canvasrca_call_key':key},output_kind=RequestOutputKind.FINAL_ONLY)
            language=time.monotonic();last=None;submitted=True
            async for result in self.engine.generate(prompt,params,request_id=key):last=result
            if last is None or not last.finished or len(last.outputs)!=1:raise RuntimeError('Incomplete vLLM response')
            audit=(await self.engine.collective_rpc('rq43_finish',args=(key,)))[0];encoded=False
            self.engine_stats={k:audit[k] for k in ('engine_batches','engine_decode_batches','engine_max_batch','engine_max_decode_batch','engine_preemptions')}
            expected={'U':0,'TEXT':0,'P_LOCAL_BI':3,'P_SOFT_IMAGE':1,'P_DUAL':4,'C_LOCAL_FORWARD':3,'C_SHAM_BI':3,'C_GLOBAL_BI':3}[meta['operation']]
            if audit['branch_calls']!=expected:raise ValueError(f'vLLM branch count {audit["branch_calls"]} != {expected}')
            if audit['attention_error'] or audit['attention_missed']:raise RuntimeError('vLLM attention capture failed')
            answer=last.outputs[0];n=meta['length']
            if len(last.prompt_token_ids)!=n:raise ValueError('vLLM prompt accounting differs')
            usage={'input_tokens':n,'output_tokens':len(answer.token_ids),'image_tokens_original':packet['image_tokens_original'],
                'output_token_ids':list(answer.token_ids),'image_tokens_retained':sum(map(len,request['retained_by_image'])),'cache_lengths':[n],'branch_calls':audit['branch_calls'],
                'processor_model_seconds':time.monotonic()-began,'vision_seconds':audit['encoder_transport_seconds'],
                'language_seconds':time.monotonic()-language,'attention_requested':bool(request.get('attention')),
                'attention_record_key':key if request.get('attention') else None,'stop_reason':answer.finish_reason,
                'runtime_revision':'vllm_v13','backend':'vllm','request_concurrency':8,'dtype':'bfloat16',
                'sampling_rng':'vllm_independent_seeded_request','implementation_generation_identity':stable([request['identity'],'vllm_v13']),
                'operational_revision':'kv_admission_v19','cache_reservation':reservation,
                **audit}
            return answer.text,usage
        except BaseException:
            if submitted and not self.engine.errored:
                try:await asyncio.wait_for(self.engine.abort(key),timeout=5)
                except BaseException:pass
            if encoded and not self.engine.errored:
                try:await asyncio.wait_for(self.engine.collective_rpc('rq43_finish',args=(key,)),timeout=5)
                except BaseException:pass
            raise
        finally:
            if reserved:await self.admission.release(key)
    def close(self):
        import asyncio
        if self.thread.is_alive():
            try:
                if not self.engine.errored:
                    asyncio.run_coroutine_threadsafe(self.engine.collective_rpc('rq43_shutdown'),self.loop).result(timeout=30)
            finally:self.loop.call_soon_threadsafe(self.loop.stop);self.thread.join(timeout=30)
        if self.thread.is_alive():raise RuntimeError('vLLM control thread failed to stop')
