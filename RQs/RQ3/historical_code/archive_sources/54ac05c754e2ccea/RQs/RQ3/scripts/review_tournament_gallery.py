"""Offline tournament artifact audit; never generates requests or model inputs."""
import argparse
from collections import Counter
from pathlib import Path
from PIL import Image
from RQs.RQ3.src.utils import ROOT,read_json,write_json,stable_hash,sha_file
from RQs.RQ3.src.exps import validate_tournament_parts
from RQs.RQ3.src.gates import audit_public_pool,source_audit,parent_integrity
from RQs.RQ3.src.renderer.card_families import audit_family_geometry
from RQs.RQ2.src.utils import audit_visible
from vlmrca.peer_metrics import display_number


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--gallery',type=Path,required=True)
    cli.add_argument('--parent',type=Path,required=True)
    args=cli.parse_args();gallery=args.gallery.resolve();parent=args.parent.resolve()
    summary=read_json(gallery/'summary.json');old=read_json(parent/'summary.json')
    refs={r['case']:r for r in old['attempts']};rows=[]
    dataset={r['opaque_incident_id']:r['dataset'] for r in summary['cohort']['cases']}
    assert len(summary['attempts'])==len(dataset)
    for attempt in summary['attempts']:
        assert attempt['status']=='rendered',attempt
        case=attempt['case'];stem=gallery/case/attempt['family'];ref=refs[case]
        prior=parent/case/ref['family'];packet=read_json(stem.with_suffix('.packet.json'))
        manifest=read_json(stem.with_suffix('.manifest.json'));parts=read_json(stem.with_suffix('.prompt.json'))
        assert parts==read_json(prior.with_suffix('.prompt.json')),'fixed prompt/candidates changed'
        _,ids=validate_tournament_parts(parts);assert ids==packet['candidates']
        assert packet['fact_inventory_hash']==stable_hash(packet['facts'])
        assert manifest['source_packet_fact_inventory_hash']==packet['fact_inventory_hash']
        assert manifest['manifest_sha256']==stable_hash({k:v for k,v in manifest.items() if k!='manifest_sha256'})
        audit_public_pool(packet);audit_family_geometry(manifest)
        facts={f['fact_id']:f for f in packet['facts'] if f['region']!='C'}
        mapping={r['fact_id']:r for r in manifest['fact_mapping']}
        assert len(mapping)==len(manifest['fact_mapping']) and facts.keys()==mapping.keys()
        assert all(r['primitive_geometry'] for r in mapping.values())
        assert manifest['clipping_audit']['status']=='passed'
        image=stem.with_suffix('.png');assert sha_file(image)==attempt['png_sha256']
        with Image.open(image) as im:
            im.load();assert im.size==tuple(manifest['canvas_size'])
        private=read_json(ROOT/attempt['private'])
        markers=[private['case_id'],*private['numeric_to_natural'].values()]
        audit_visible([parts,list(facts.values()),manifest['fact_mapping'],manifest['cards']],markers)
        assert sha_file(ROOT/attempt['source'])==attempt['source_file_hash']==ref['source_file_hash']
        pp=read_json(prior.with_suffix('.packet.json'))
        panels=lambda p:{f['payload']['panel_id'] for f in p['facts'] if f['field']=='metric_series_64'}
        a,b=panels(packet),panels(pp)
        trace_ids=lambda p:{f['fact_id'] for f in p['facts'] if f['field']=='trace_summary_entry'}
        ta,tb=trace_ids(packet),trace_ids(pp)
        log_ids=lambda p:{f['fact_id'] for f in p['facts'] if f['field']=='denum_log_template'}
        la,lb=log_ids(packet),log_ids(pp)
        if attempt['selection']['policy']=='sircl_log_freq6_v1':
            assert a==b and ta==tb,'native log intervention changed M/R anchor'
        if attempt['selection']['policy']=='sircl_trace_sc8_v1':
            assert a==b and la==lb,'native trace intervention changed M/L anchor'
        if attempt['selection']['policy'] in ('sircl_ma24_v1','baro_native24_v1'):
            assert ta==tb and la==lb,'native metric intervention changed R/L anchor'
        status=attempt.get('projection',{}).get('trace_status')
        status_facts=[f for f in packet['facts'] if f['field']=='trace_status_summary']
        if status is not None:
            assert a==b and la==lb,'status intervention changed M/L anchor'
            assert [f for f in packet['facts'] if f['region']=='G']==[f for f in pp['facts'] if f['region']=='G'],'status intervention changed G anchor'
            assert bool(status_facts)==status['applied']
            assert status['source_rows']==status['eligible_rows']+status['skipped_rows']
            assert len(status_facts)==len(status['rows'])<=6
            for fact,row in zip(status_facts,status['rows']):
                assert fact['payload']=={k:v for k,v in row.items() if k not in ('nondefault_count','source_rows_hash')}
                p=fact['payload'];assert p['count']==sum(p['status_counts'].values())
                assert p['status_counts'].keys()==p['code_bin_counts'].keys()
                assert all(len(v)==64 and sum(v)==p['status_counts'][c] for c,v in p['code_bin_counts'].items())
            sources=attempt['supplemental_sources']
            assert {Path(p).name for p in sources}=={'metadata.json','metrics.parquet','traces.parquet'}
            for relative,digest in sources.items():
                path=(ROOT/relative).resolve()
                assert path.is_relative_to((ROOT/'build/local_processed_v3/public').resolve())
                assert case in path.parts and sha_file(path)==digest
        native=attempt['selection'].get('native',{})
        if attempt['selection']['policy']=='sircl_ma24_v1':
            assert native['unbound_columns']==0,'mean-shift source rank unbound'
            assert native['ranks']==[r['column'] for r in native['rows']]
            assert all(r['_deviation']>3 for r in native['rows'])
            assert all(x['_deviation']>=y['_deviation'] for x,y in zip(native['rows'],native['rows'][1:]))
        source_pool=read_json(ROOT/attempt['source'])['pool']
        original_eight=sorted((f for f in source_pool['facts'] if f['field']=='trace_summary_entry'),
            key=lambda f:(-display_number(f['payload'].get('rank_score')),f['fact_id']))[:8]
        rows.append({'case':case,'dataset':dataset[case],'facts':len(facts),'metrics':len(a),
            'added_panels':sorted(a-b),'removed_panels':sorted(b-a),
            'panel_jaccard':len(a&b)/len(a|b) if a|b else 1.,
            'differs_from_original_metric_top24':a!={f['payload']['panel_id'] for f in sorted(
                (f for f in source_pool['facts'] if f['field']=='metric_series_64'),
                key=lambda f:(f['payload']['rank'],f['fact_id']))[:24]},
            'traces':len(ta),'added_traces':sorted(ta-tb),'removed_traces':sorted(tb-ta),
            'trace_status_rows':len(status_facts),
            'trace_jaccard':len(ta&tb)/len(ta|tb) if ta|tb else 1.,
            'logs':len(la),'added_logs':sorted(la-lb),'removed_logs':sorted(lb-la),
            'log_jaccard':len(la&lb)/len(la|lb) if la|lb else 1.,
            'pixels_changed':sha_file(image)!=ref['png_sha256'],
            'native_rank_count':len(native.get('ranks',native.get('rows',[]))),
            'native_unbound_count':len(attempt['selection'].get('unbound_native_rows',[])),
            'native_selected_count':len(attempt['selection'].get('native_selected_ids',[])),
            'differs_from_original_trace_top8':ta!={f['fact_id'] for f in original_eight},
            'fill_count':len(attempt['selection'].get('fill_ids',[]))})
    result={'status':'passed','summary_hash':stable_hash(summary),'rows':rows,
            'source_audit':source_audit(),'parent_integrity':parent_integrity(),
            'cases':len(rows),'datasets':dict(Counter(r['dataset'] for r in rows)),
            'changed_pixel_cases':sum(r['pixels_changed'] for r in rows),
            'changed_panel_cases':sum(bool(r['added_panels'] or r['removed_panels']) for r in rows),
            'changed_trace_cases':sum(bool(r['added_traces'] or r['removed_traces']) for r in rows),
            'changed_log_cases':sum(bool(r['added_logs'] or r['removed_logs']) for r in rows),
            'model_calls':0,'manual_visual_review':'required_separately'}
    write_json(gallery/'cpu_review.json',result)
    print({k:v for k,v in result.items() if k!='rows'},flush=True)


if __name__=='__main__':main()
