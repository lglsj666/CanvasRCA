"""CPU-only exact-artifact replay check before extending an existing method."""
import argparse
from pathlib import Path
from RQs.RQ3.src.main import load_config, _search_gallery_case
from RQs.RQ3.src.utils import ROOT, read_json, write_json, sha_file
from vlmrca.run_state import pinned_process_map


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    for name in ('config', 'parent_config', 'parent_gallery', 'source', 'output'):
        cli.add_argument('--'+name.replace('_','-'), type=Path, required=True)
    cli.add_argument('--cases', nargs='+', required=True)
    args = cli.parse_args()
    config, prior = load_config(args.config), load_config(args.parent_config)
    assert {k:v for k,v in config.items() if k!='tournament'} == {k:v for k,v in prior.items() if k!='tournament'}
    source, parent, output = args.source.resolve(), args.parent_gallery.resolve(), args.output.resolve()
    summary, index = read_json(parent/'summary.json'), read_json(source/'index.json')
    rows = {r['opaque_incident_id']:r for r in summary['cohort']['cases']}
    lookup = {r['opaque_incident_id']:r for r in index['cases']}
    original = {r['case']:r for r in summary['attempts']}
    if len(args.cases)!=len(set(args.cases)):
        raise ValueError('duplicate compatibility case')
    jobs = [(config,source,output/'compatibility_gallery',rows[c],lookup[c],index['partition']) for c in args.cases]
    replayed = [a for batch in pinned_process_map(_search_gallery_case,jobs,max_workers=3) for a in batch]
    for a in replayed:
        assert a['status']=='rendered', a
        old = original[a['case']]
        assert a['family']==old['family'] and a['selection']==old['selection']
        for suffix in ('.png','.packet.json','.manifest.json','.prompt.json'):
            left = (output/'compatibility_gallery'/a['case']/a['family']).with_suffix(suffix)
            right = (parent/a['case']/old['family']).with_suffix(suffix)
            assert sha_file(left)==sha_file(right), (a['case'],suffix)
    write_json(output/'compatibility_review.json', {'status':'passed','cases':args.cases,
        'png_packet_manifest_prompt_byte_identical':True,'model_calls':0,
        'purpose':'same native selector and renderer; expanded cohort only'})
    print('COMPATIBILITY_PASSED', args.cases, flush=True)


if __name__=='__main__':
    main()
