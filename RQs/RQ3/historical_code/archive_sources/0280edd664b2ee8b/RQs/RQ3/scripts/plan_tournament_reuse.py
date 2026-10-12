"""Find same-case, same-model input no-ops; runtime also verifies the full recipe."""
import argparse
from pathlib import Path
from RQs.RQ3.src.main import load_config
from RQs.RQ3.src.utils import ROOT,read_json,write_json,sha_file,tournament_register
from RQs.RQ3.src.gates import audit_call_artifacts


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--config',type=Path,required=True)
    cli.add_argument('--gallery',type=Path,required=True)
    cli.add_argument('--parents',type=Path,nargs='+',required=True)
    args=cli.parse_args();cfg=load_config(args.config)
    current=tournament_register(cfg).rounds()[-1];gallery=args.gallery.resolve()
    attempts={r['case']:r for r in read_json(gallery/'summary.json')['attempts']};reuse={}
    for model,cases in current['cohorts'].items():
        aliases={}
        for parent in args.parents:
            phase=parent.resolve()/model;summary=read_json(phase/'summary.json')
            if summary['status']!='complete':raise ValueError('reuse source phase incomplete')
            for row in summary['outcomes']:
                case=row['task']['case']
                if case not in cases or case in aliases:continue
                a=attempts[case];stem=gallery/case/a['family']
                new=read_json(stem.with_suffix('.prompt.json'))
                new=[{'type':'image','image_sha256':a['png_sha256']} if 'png' in p else p for p in new]
                source=phase/row['record_path'];record=read_json(source)
                prompt=next(p for p in record['artifact_hashes'] if p.startswith('prompts/'))
                old=read_json(phase/prompt)
                parts=[{k:v for k,v in p.items() if k!='image_path'} for p in old['parts']]
                if parts!=new:continue
                audit_call_artifacts(record,phase)
                aliases[case]={'record':str(source.relative_to(ROOT)),'sha256':sha_file(source)}
        reuse[model]=aliases
    target=gallery/'reuse.json'
    if target.exists() and read_json(target)!=reuse:raise ValueError('reuse mapping changed')
    write_json(target,reuse)
    print({m:sorted(v) for m,v in reuse.items()},flush=True)


if __name__=='__main__':main()
