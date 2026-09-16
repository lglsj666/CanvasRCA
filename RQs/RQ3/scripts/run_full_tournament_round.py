"""Run one fully registered remaining-cohort round, sequentially and resumably."""
import argparse
from pathlib import Path
from RQs.RQ3.src.main import load_config, run_search_batch, manage_tournament
from RQs.RQ3.src.utils import ROOT, read_json, tournament_register


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--config',type=Path,required=True)
    cli.add_argument('--output',type=Path,required=True)
    cli.add_argument('--retry-failed',action='store_true')
    args=cli.parse_args();cfg=load_config(args.config);root=args.output.resolve()
    reg=tournament_register(cfg);round_=reg.rounds()[-1]
    if (cfg['tournament'].get('cohort_policy')!='all_unretired_v1' or
            round_.get('cohort_policy')!='all_unretired_v1' or
            round_['method']['id']!=cfg['tournament']['method_id']):
        raise ValueError('not the registered full-remaining method')
    if not (root/'source_code_snapshot.tar.gz').is_file():
        raise ValueError('pre-call source snapshot missing')
    for model in cfg['tournament']['models']:
        spec=read_json(root/model/'private/work_spec.json')
        ids=[task['case'] for task in spec['tasks']]
        if (spec['tournament_round_hash']!=round_['hash'] or
                len(ids)!=len(set(ids)) or set(ids)!=set(round_['cohorts'][model])):
            raise ValueError('work spec omits or duplicates registered remaining cases')
    for model in cfg['tournament']['models']:
        if (reg.root/round_['id']/(model+'.json')).exists():
            # Re-score and verify persisted artifacts; never blindly skip a flag.
            manage_tournament(cfg,'commit',root/model)
            print('ALREADY_COMMITTED',model,flush=True)
            continue
        print('START',model,'CASES',len(round_['cohorts'][model]),flush=True)
        run_search_batch(root/model,config_path=args.config,retry_failed=args.retry_failed)
        committed=manage_tournament(cfg,'commit',root/model)
        print('COMMITTED',model,committed['hash'],flush=True)
    print('ROUND_COMPLETE',round_['id'],flush=True)


if __name__=='__main__':main()
