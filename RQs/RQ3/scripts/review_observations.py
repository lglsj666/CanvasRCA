"""Public-only SEARCH31 source, prompt, and actual-pixel comparison."""
from copy import deepcopy
from dataclasses import replace
from PIL import Image, ImageChops, ImageDraw
from RQs.RQ3.src.utils import ROOT,read_json,write_json,sha_file,stable_hash
from RQs.RQ3.src.gates import audit_public_pool,source_audit
from RQs.RQ3.src.main import load_config
from RQs.RQ3.src.exps import source_metric_geometry,search_solver_parts
from RQs.RQ3.src.renderer.card_families import audit_family_geometry
from RQs.RQ3.src.renderer.owner_groups import render_search_family
from RQs.RQ3.src.renderer.designs import DashboardSpecV3


def main():
    base=ROOT/'RQs/RQ3/results/search_first_v1'
    gallery=base/'observations_gallery_v1';old=base/'unanchored_gallery_v1'
    summary=read_json(gallery/'summary.json');prior=read_json(old/'summary.json')
    assert summary['cohort']==prior['cohort'] and len(summary['attempts'])==24
    cfg=load_config(ROOT/'RQs/RQ3/configs/search_observations_v1.yaml')
    refs={a['case']:a for a in prior['attempts']};results=[];static=None
    replays={'INC-4BA2D386B400','INC-492AFB4CE9D6','INC-0917F17160F5'}
    for a in summary['attempts']:
        assert a['status']=='rendered',a
        ref=refs[a['case']];stem=gallery/a['case']/a['family'];parent=old/a['case']/ref['family']
        p=read_json(stem.with_suffix('.packet.json'));m=read_json(stem.with_suffix('.manifest.json'))
        before=read_json(parent.with_suffix('.packet.json'));om=read_json(parent.with_suffix('.manifest.json'))
        parts=read_json(stem.with_suffix('.prompt.json'));op=read_json(parent.with_suffix('.prompt.json'))
        assert p==before and a['selection']==ref['selection'] and a['projection']==ref['projection']
        assert a['source_file_hash']==ref['source_file_hash']==sha_file(ROOT/a['source'])
        audit_public_pool(p);audit_family_geometry(m)
        assert m['fact_mapping']==om['fact_mapping'] and m['cards']==om['cards']
        assert m['metric_source_geometry_hash']==om['metric_source_geometry_hash']
        assert m['requested_tree']==om['requested_tree'] and m['outer_projection']==om['outer_projection']
        assert m['source_packet_fact_inventory_hash']==p['fact_inventory_hash']
        assert parts[1:3]==op[1:3] and parts[4:]==op[4:] and len(parts)==5
        exact=search_solver_parts(p,stem.with_suffix('.png').read_bytes(),m,log_summary=True,prompt_policy='evidence_observations_v1')
        assert parts==[{**x,'png':'adjacent PNG'} if 'png' in x else x for x in exact]
        current=[parts[0],*parts[3:]]
        if static is None:static=current
        assert current==static
        selected=[deepcopy(f) for f in sorted(p['facts'],key=lambda f:f['fact_id']) if f['region']!='C']
        withheld=[]
        for f in selected:
            if f['field']=='metric_series_64' and 'signed_z' in f['payload']:
                del f['payload']['signed_z'];withheld.append({'fact_id':f['fact_id'],'pointer':'/payload/signed_z'})
        assert m['withheld_fields']==withheld and m['visual_fact_inventory_hash']==stable_hash(selected)
        assert m['manifest_sha256']==stable_hash({k:v for k,v in m.items() if k!='manifest_sha256'})
        image=Image.open(stem.with_suffix('.png')).convert('RGB');original=Image.open(parent.with_suffix('.png')).convert('RGB')
        assert image.size==original.size==tuple(m['canvas_size'])
        assert sha_file(stem.with_suffix('.png'))==a['png_sha256']
        diff=ImageChops.difference(image,original);assert diff.getbbox()
        mask=ImageDraw.Draw(diff);facts={f['fact_id']:f for f in p['facts']}
        for row in m['fact_mapping']:
            if facts[row['fact_id']]['field']!='metric_series_64':continue
            # Native one-column label width max260; second summary baseline bottom-18.
            lane=next(g for g in row['primitive_geometry'] if 'bin_primitives' in g)
            x0,y0,x1,y1=lane['bbox']
            mask.rectangle((x0,y1-18,x0+260,y1+5),fill=(0,0,0))
        assert diff.getbbox() is None,'pixel change outside signed-z label strip'
        replay=a['case'] in replays
        if replay:
            native,_=render_search_family(p,DashboardSpecV3(**ref['spec']),cfg['search'],source_metric_geometry(a['case']))
            assert native==parent.with_suffix('.png').read_bytes(),'native prior PNG changed'
        results.append({'case':a['case'],'source_packet_unchanged':True,'withheld_metric_labels':len(withheld),
                        'only_z_label_pixels_changed':True,'native_replay':replay})
    result={'status':'passed','summary_hash':stable_hash(summary),'model_calls':0,'cases':results,
            'source_audit':source_audit(),'candidate_list_prompt_only':True,'native_replays':len(replays)}
    write_json(gallery/'cpu_review.json',result)
    print({k:v for k,v in result.items() if k!='cases'},flush=True)


if __name__=='__main__':main()
