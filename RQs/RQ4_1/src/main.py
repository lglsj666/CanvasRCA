"""RQ4.1 isolated CPU entrypoints. GPU entries are fail-closed by qualification."""
import argparse
import json
from . import gates


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('static','cpu','render-roster','processor-roster','foreground-roster','shared-support','confirm-shared','saturation-features','saturation-selection','admission-render','admission-processor','admission-support','admission-encoder','admission-covariates','admission-selection','admission-input-geometry','remaining-cpu','prior-cpu','smoke','prepare-smoke','smoke-hf','smoke-native','prepare-deployment','freeze-deployment','qualify-deployment','deployment-worker','formal'))
    parser.add_argument('--prior-config',default='prior_completion_v13.json')
    parser.add_argument('--backend',choices=('hf','native'))
    args=parser.parse_args()
    if args.command=='static':
        report=gates.static_check()
    elif args.command=='cpu':
        report=gates.cpu_inventory()
    elif args.command=='render-roster':
        report=gates.render_roster()
    elif args.command=='processor-roster':
        report=gates.processor_roster()
    elif args.command=='foreground-roster':
        report=gates.foreground_roster()
    elif args.command=='shared-support':
        report=gates.shared_support_roster()
    elif args.command=='confirm-shared':
        report=gates.confirm_shared_support()
    elif args.command=='saturation-features':
        report=gates.extract_saturation_features()
    elif args.command=='saturation-selection':
        report=gates.saturation_selector_probe()
    elif args.command=='admission-render':
        report=gates.admission_source_render()
    elif args.command=='admission-processor':
        report=gates.admission_processor()
    elif args.command=='admission-support':
        report=gates.admission_support()
    elif args.command=='admission-encoder':
        report=gates.admission_encoder()
    elif args.command=='admission-covariates':
        report=gates.admission_feature_audit('covariates')
    elif args.command=='admission-selection':
        report=gates.admission_feature_audit('selection')
    elif args.command=='admission-input-geometry':
        report=gates.admission_input_geometry()
    elif args.command=='remaining-cpu':
        report=gates.remaining_cpu_audit()
    elif args.command=='prior-cpu':
        report=gates.prior_completion_audit(args.prior_config)
    elif args.command=='prepare-smoke':
        report=gates.smoke_prepare()
    elif args.command=='smoke':
        report=gates.smoke_supervisor()
    elif args.command=='smoke-hf':
        report=gates.smoke_worker_entry('hf')
    elif args.command=='smoke-native':
        report=gates.smoke_worker_entry('native')
    elif args.command=='prepare-deployment':report=gates.deployment_prepare()
    elif args.command=='freeze-deployment':report=gates.deployment_freeze()
    elif args.command=='deployment-worker':report=gates.deployment_worker(args.backend)
    else:
        report=gates.deployment_supervisor()
    print(json.dumps({k:v for k,v in report.items() if k not in {'cases','hashes'}},indent=2))
    if report['status'] not in {'passed','screen_complete','passed_encoder_only','cpu_checks_finished','completed_pending_review','paused','complete'}:raise SystemExit(1)


if __name__=='__main__':main()
