"""RQ4.2 admission CLI; never auto-starts a GPU service."""
import argparse
import json
from . import exps, gates


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage', choices=['static', 'capacity', 'probe', 'pack', 'render', 'grouping', 'qa', 'processor', 'admission', 'smoke', 'smoke-worker', 'formal', 'formal-worker', 'formal-check', 'status', 'pause'])
    p.add_argument('--workers', type=int, default=8, choices=range(1, 9))
    p.add_argument('--resume-startup',action='store_true',help='Continue a zero-call startup failure within the ORIGINAL smoke clock')
    p.add_argument('--resume',action='store_true',help='Clear a user pause and resume the same formal queue')
    args = p.parse_args()
    if args.stage == 'static':
        result = gates.static_check()
    elif args.stage in {'capacity', 'probe'}:
        gates.static_check()
        result = exps.measure_population(limit=1 if args.stage == 'probe' else None, workers=args.workers)
        result = {k: v for k, v in result.items() if k != 'cases'}
    elif args.stage == 'pack':
        result=exps.layout_population()
    elif args.stage == 'render':
        result=dict(exps.render_population(workers=args.workers))
    elif args.stage == 'grouping':
        result=exps.refinement_audit(workers=args.workers,probe=False)
    elif args.stage == 'qa':
        result=exps.prepare_qa(workers=args.workers)
    elif args.stage == 'processor':
        result=exps.processor_population(workers=args.workers)
    elif args.stage == 'admission':
        result=gates.admission_decision()
    elif args.stage=='smoke':
        result=exps.supervise_smoke(resume_startup=args.resume_startup)
    elif args.stage=='smoke-worker':
        exps.smoke_worker();return
    elif args.stage=='formal-check':
        result=gates.formal_readiness()
    elif args.stage=='status':
        from .utils import formal_status
        result=formal_status()
    elif args.stage=='pause':
        from .utils import RESULTS,write,formal_status
        write(RESULTS/'formal_v1/execution/PAUSE',{'reason':'explicit user pause; drain current request'})
        result=formal_status()
    elif args.stage=='formal-worker':
        result=exps.run_formal()
    else:
        result=exps.launch_formal(resume=args.resume)
    print(json.dumps({k:v for k,v in result.items() if k!='cases'}, ensure_ascii=False, indent=2))
    if args.stage == 'admission' and not result['complete_cpu_qualification']:
        raise SystemExit(2)
    if args.stage=='smoke' and result['status']!='passed':raise SystemExit(2)


if __name__ == '__main__':
    main()
