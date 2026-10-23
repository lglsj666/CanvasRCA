"""Audit only the retained QA inputs; no rendering, processor or model execution."""
from pathlib import Path
from collections import Counter
from decimal import Decimal, InvalidOperation
import csv, hashlib, json, math, re

ROOT=Path(__file__).resolve().parents[5]
OUT=Path(__file__).resolve().parent
R=ROOT/'RQs/RQ4_7/results/source_workspace_v1'
A=OUT.parent
read=lambda p:json.loads(Path(p).read_text())
save=lambda n,x:(OUT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')

def number(v):
    try:
        d=Decimal(str(v).strip())
        return d if d.is_finite() else None
    except InvalidOperation:return None

def support(box,geom,grid,keep):
    gw,gh=grid[2]//2,grid[1]//2
    cw,ch=geom['width']/gw,geom['height']/gh
    x,y,w,h=box;all_indices=[];kept_area=0.;keep=set(keep)
    for iy in range(max(0,int(y/ch)),min(gh,int(math.ceil((y+h)/ch)))):
        for ix in range(max(0,int(x/cw)),min(gw,int(math.ceil((x+w)/cw)))):
            area=max(0,min(x+w,(ix+1)*cw)-max(x,ix*cw))*max(0,min(y+h,(iy+1)*ch)-max(y,iy*ch))
            if area:
                idx=iy*gw+ix;all_indices.append(idx)
                if idx in keep:kept_area+=area
    return len(all_indices),sum(i in keep for i in all_indices),kept_area/(w*h) if w*h else 0.

def box_for(row,geometry):
    for q in geometry.get('rows',[]):
        if q['binding']==row['binding']:return q['box'],'comparison_row'
    for p in geometry['panels']:
        if p['card']!=row['card']:continue
        for f in p.get('local_fields',[]):
            if f['binding']==row['binding']:return f['box'],'local_source_field'
        for f in p.get('fields',[]):
            if f['binding']==row['binding']:
                x,y,w,h=f['box'];sx,sy,sw,sh=p['source_box'];scale=p['source_scale']
                return [(x-sx)*scale+p['box'][0],(y-sy)*scale+p['box'][1],w*scale,h*scale],'overview_source_field'
    return None,None

cases=read(A/'qa_case_answers.json');allrows=[];packets={};requests={}
for q in cases:
    assert q['arm']=='S_COMPARE'
    packet=read(R/'inputs'/q['id']/'packet.json');packets[q['id']]=packet
    request=read(R/'formal'/q['request_path']);requests[q['id']]=request
    location=json.loads(request['messages'][-1]['content'][-1]['text'].split('Targets: ',1)[1])
    dep=next(v for k,v in packet['source_dependencies'].items() if k.endswith('/evidence.json'))
    evidence=read(ROOT/dep);cards={c['id']:c for c in evidence['cards']}
    for i,(target,truth,loc) in enumerate(zip(q['targets'],q['expected'],location,strict=True)):
        im=loc['image'];g=request['geometry'][im]
        b=loc['box'];box=[b[0]*g['width']/1000,b[1]*g['height']/1000,
                         (b[2]-b[0])*g['width']/1000,(b[3]-b[1])*g['height']/1000]
        field,kind=box_for(target,g)
        assert field is not None,(q['id'],i)
        actualpanel=next(p for p in g['panels'] if p['card']==target['card'])
        pbox=actualpanel['box'];source=packet['inventory'][target['card']];card=cards[target['card']]
        value=number(truth['value']);texts=[x['text'] for x in source['texts']]
        values=[number(t) for t in texts]
        alln,kept,area=support(box,g,request['grid_thw'][im],request['retained_by_image'][im])
        same_boxes=[]
        for other in packet['rows'][target['card']]:
            ob,_=box_for(other,g)
            if ob and max(abs(a-b) for a,b in zip(box,ob))<1e-5:same_boxes.append(other['binding'])
        raw_exact=(value in values)
        drawn_exact=raw_exact or kind=='comparison_row'
        phase_literal=any(truth['phase'].lower() in t.lower() for t in texts)
        entity_literal=bool(truth['entity']) and any(re.search(r'(?<!\d)'+re.escape(truth['entity'])+r'(?!\d)',t) for t in texts)
        minfont=18. if kind=='comparison_row' else source['min_font_px']*(actualpanel['source_scale'] if im else 1.)
        processscale=min(request['grid_thw'][im][2]*16/g['width'],request['grid_thw'][im][1]*16/g['height'])
        row={'id':q['id'],'dataset':q['dataset'],'question':i,'image':im,'binding':target['binding'],
             'card':target['card'],'card_kind':card['kind'],'target_kind':kind,'expected':truth,
             'card_entity':card.get('entity'),'card_title':card['title'],'card_unit':card['unit'],
             'pixel_box':box,'panel_box':pbox,'coordinate_binding_error_px':max(abs(a-b) for a,b in zip(box,field)),
             'inside_canvas':box[0]>=0 and box[1]>=0 and box[0]+box[2]<=g['width']+1e-5 and box[1]+box[3]<=g['height']+1e-5,
             'inside_panel':box[0]>=pbox[0]-1e-5 and box[1]>=pbox[1]-1e-5 and box[0]+box[2]<=pbox[0]+pbox[2]+1e-5 and box[1]+box[3]<=pbox[1]+pbox[3]+1e-5,
             'source_card_exact_numeric_text_exists':raw_exact,'displayed_exact_value_at_card_or_added_row':drawn_exact,
             'same_rectangle_source_bindings':same_boxes,'empty_expected_entity':not truth['entity'],
             'expected_entity_printed_in_source_card':entity_literal,
             'expected_phase_literal_in_source_card':phase_literal,
             'processed_card_min_font_px_lower_bound':minfont*processscale,
             'intersecting_merged_tokens':alln,'retained_intersecting_merged_tokens':kept,'retained_rectangle_area_fraction':area,
             'source_texts':texts,'actual_answer':json.loads(q['qa_response'])['answers'][i]}
        allrows.append(row)

save('questions.json',allrows)
annotations=[]
for row in allrows:
    flags=[]
    if row['empty_expected_entity']:
        flags.append('invalid_empty_single_entity_for_relation_measurement')
    if row['expected']['phase'] in {'whole_window','observed_window'}:
        flags.append('undefined_canonical_phase_vocabulary')
    if row['expected']['unit'] in {'ratio_or_percent','milliseconds_or_source_unit'}:
        flags.append('unregistered_unit_spelling_equivalence')
    if row['target_kind']=='comparison_row':
        flags.append('target_rectangle_spans_measurement_and_other_numbers')
    annotations.append({
        'id':row['id'],'dataset':row['dataset'],'question_index_zero_based':row['question'],
        'binding':row['binding'],'flags':flags,
        'validity':'invalid_question' if row['empty_expected_entity'] else 'not_certified_valid',
        'original_scores_unchanged':True})
save('validity_annotations.json',annotations)
short=[]
for r in allrows:
    row={k:v for k,v in r.items() if not isinstance(v,(dict,list))}
    row.update({'expected_'+k:v for k,v in r['expected'].items()})
    short.append(row)
with (OUT/'questions.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(short[0]));w.writeheader();w.writerows(short)
summary={
 'scope':'360 retained S_COMPARE questions,60 fixed cases; original model inputs unchanged',
 'new_model_calls':0,'cases':len(cases),'questions':len(allrows),
 'targets_inside_actual_canvas':sum(r['inside_canvas'] for r in allrows),
 'targets_inside_registered_panel':sum(r['inside_panel'] for r in allrows),
 'exact_DOM_coordinate_matches':sum(r['coordinate_binding_error_px']<1e-5 for r in allrows),
 'exact_numeric_text_in_registered_source_card':sum(r['source_card_exact_numeric_text_exists'] for r in allrows),
 'exact_numeric_text_in_source_card_or_added_row':sum(r['displayed_exact_value_at_card_or_added_row'] for r in allrows),
 'target_kinds':dict(Counter(r['target_kind'] for r in allrows)),
 'empty_expected_entity':sum(r['empty_expected_entity'] for r in allrows),
 'expected_entity_not_literal_on_source_card':sum(not r['empty_expected_entity'] and not r['expected_entity_printed_in_source_card'] for r in allrows),
 'phase_counts':dict(Counter(r['expected']['phase'] for r in allrows)),
 'unit_counts':dict(Counter(r['expected']['unit'] for r in allrows)),
 'phase_not_literal_in_source_card':dict(Counter(r['expected']['phase'] for r in allrows if not r['expected_phase_literal_in_source_card'])),
 'no_retained_token_intersecting_target':sum(r['retained_intersecting_merged_tokens']==0 for r in allrows),
 'zero_support_details':[{'id':r['id'],'question':r['question'],'binding':r['binding']} for r in allrows if r['retained_intersecting_merged_tokens']==0],
 'coverage_below_half_area':sum(r['retained_rectangle_area_fraction']<.5 for r in allrows),
 'multiple_registered_rows_with_exact_same_box':sum(len(r['same_rectangle_source_bindings'])>1 for r in allrows),
 'font_note':'Conservative per-card minimum from recorded DOM and real processor grid; not a fresh OCR/per-field font measurement.',
 'invalid_empty_entity_by_dataset':dict(Counter(r['dataset'] for r in allrows if r['empty_expected_entity'])),
 'invalid_empty_entity_cases':len({r['id'] for r in allrows if r['empty_expected_entity']}),
 'undefined_canonical_phase_vocabulary':sum(r['expected']['phase'] in {'whole_window','observed_window'} for r in allrows),
 'unregistered_unit_spelling_equivalence':sum(r['expected']['unit'] in {'ratio_or_percent','milliseconds_or_source_unit'} for r in allrows),
 'flagged_question_union_not_invalid_count':sum(bool(r['flags']) for r in annotations),
 'visual_review_limit':20,
 'visual_images_reviewed_so_far':len(read(OUT/'visual_sample_index.json')) if (OUT/'visual_sample_index.json').exists() else 0,
 'visual_count_definition':'One full original workspace plus ten card crops and two target-row crops; crops count separately.',
 'limits':'DOM text presence is not proof of legible raster,OCR success or semantic uniqueness; numeric matches can coincide. No regrading.'}
save('summary.json',summary)
print(json.dumps(summary,ensure_ascii=False,indent=2))
