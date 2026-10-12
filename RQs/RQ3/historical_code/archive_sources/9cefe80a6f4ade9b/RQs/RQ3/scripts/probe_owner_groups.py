"""CPU-only SEARCH30 gallery from unchanged SEARCH23 training packets."""
import argparse
import time
from dataclasses import replace
from pathlib import Path
from RQs.RQ3.src.main import load_config
from RQs.RQ3.src.utils import ROOT, read_json, write_json, atomic_write, stable_hash
from RQs.RQ3.src.exps import source_metric_geometry, search_solver_parts
from RQs.RQ3.src.renderer.designs import DashboardSpecV3
from RQs.RQ3.src.renderer.owner_groups import owner_groups, owner_layout, cross_owner_groups, cross_owner_layout
from RQs.RQ3.src.renderer.card_families import render_family_dashboard, make_family_cards, metric_left_stack_tree


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--cases', nargs='*')
    cli.add_argument('--output', required=True, type=Path)
    cli.add_argument('--policy', choices=('entity_associated_four_v1', 'cross_owner_joint_v2'), default='cross_owner_joint_v2')
    args = cli.parse_args()
    load_config(ROOT / 'RQs/RQ3/configs/search_owner_header_v1.yaml')
    base = ROOT / 'RQs/RQ3/results/search_first_v1/owner_header_gallery_v2'
    reference = read_json(base / 'summary.json')
    attempts = reference['attempts']
    if args.cases and not set(args.cases) <= {a['case'] for a in attempts}:
        raise ValueError('case outside registered training cohort')
    output = []; started = time.monotonic()
    for attempt in attempts:
        if args.cases and attempt['case'] not in args.cases: continue
        case, variant = attempt['case'], attempt['family']
        stem = base / case / variant
        p = read_json(stem.with_suffix('.packet.json'))
        source = source_metric_geometry(case)
        spec = DashboardSpecV3(**attempt['spec'])
        row = {'case': case, 'model_calls': 0, 'source': str(stem.relative_to(ROOT)),
               'source_fact_hash': p['fact_inventory_hash']}
        target = args.output / case / args.policy
        try:
            native = make_family_cards(p, 'modality')
            old_png, _ = render_family_dashboard(p, spec, native,
                tree=metric_left_stack_tree(native), metric_geometry=source)
            if old_png != stem.with_suffix('.png').read_bytes():
                raise ValueError('native rendering no longer byte-identical')
            cards, audit = (cross_owner_groups(p) if args.policy == 'cross_owner_joint_v2' else owner_groups(p))
            tree, facets = (cross_owner_layout(cards, audit) if args.policy == 'cross_owner_joint_v2' else owner_layout(cards, audit))
            new_spec = replace(spec, metric_context_policy='selected_packet')
            png, manifest = render_family_dashboard(p, new_spec, cards, tree,
                facet_trees=facets, metric_geometry=source)
            parts = search_solver_parts(p, png, manifest, log_summary=True,
                                        prompt_policy='evidence_bound_membership_v1')
            previous = read_json(stem.with_suffix('.prompt.json'))
            clean = lambda ps: [{k: v for k, v in part.items() if k != 'png'} for part in ps]
            if clean(parts) != clean(previous): raise ValueError('grouping unexpectedly changes static prompt')
            atomic_write(target.with_suffix('.png'), png)
            write_json(target.with_suffix('.packet.json'), p)
            write_json(target.with_suffix('.manifest.json'), manifest)
            write_json(target.with_suffix('.prompt.json'), [{**x, 'png': 'adjacent PNG'} if 'png' in x else x for x in parts])
            row.update(status='rendered', grouping=audit, png_hash=stable_hash(png),
                       native_byte_replay=True, source_facts_unchanged=True)
        except Exception as exc:
            row.update(status='failed', error=f'{type(exc).__name__}: {exc}')
        write_json(target.with_suffix('.attempt.json'), row); output.append(row)
        print(case, row['status'], row.get('error', ''), flush=True)
    write_json(args.output / 'summary.json', {'attempts': output, 'model_calls': 0,
        'seconds': time.monotonic() - started, 'scope': 'training-only CPU layout prototype'})


if __name__ == '__main__': main()
