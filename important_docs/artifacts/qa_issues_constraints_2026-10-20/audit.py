"""Read-only historical QA audit. No renderer, processor, model or scorer mutation.

Run from any directory with Python's standard library. Scoring counterexamples
execute only the isolated historical QA function AST; they are synthetic audit
inputs, never purported model responses and never replacements for old scores.
"""
from pathlib import Path
from collections import Counter
import ast
import csv
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SOURCES = {}


def read_text(path):
    p = ROOT / path
    data = p.read_bytes()
    SOURCES[str(path)] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
    return data.decode()


def read(path):
    text = read_text(path)
    return json.loads(text) if str(path).endswith('.json') else list(csv.DictReader(text.splitlines()))


def leaves(value, path=''):
    if isinstance(value, dict):
        for key, v in value.items():
            yield from leaves(v, path + '/' + key)
    elif isinstance(value, list):
        for index, v in enumerate(value):
            yield from leaves(v, path + '/' + str(index))
    else:
        yield path, value


def isolated(path, names):
    tree = ast.parse(read_text(path))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes} == set(names)
    scope = {'json': json, 'math': math}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), scope)
    return scope


summary = {'scope': 'Retained formal QA answer tables RQ4.1–RQ4.7; original scores unchanged',
           'new_model_calls': 0, 'new_images_viewed': 0, 'rounds': {}}
r41 = read('RQs/RQ4_1/results/comparison_coding_v1/final_analysis_v1/qa_interface.csv')
empty = []
scalar_count = 0
for oid in sorted({r['id'] for r in r41}):
    packet = read(f'RQs/RQ4_1/results/comparison_coding_v1/cpu_remaining_v10/cases/{oid}/qa_audit.json')
    for block in packet['blocks']:
        for side in 'AB':
            scalar_count += 1
            empty.extend({'id': oid, 'slot': block['slot'], 'side': side, 'field': k}
                         for k, v in block[side]['binding_answer'].items() if v in ('', None))
summary['rounds']['RQ4.1'] = {
    'answer_positions': len(r41), 'unique_cases': len({r['id'] for r in r41}),
    'unique_scalar_targets': scalar_count, 'empty_binding_fields': empty,
    'text_prompts_containing_RCA': sum(r['arm'] == 'T_FULL' and r['RCA_instruction_in_prompt'] == '1' for r in r41),
    'text_answers_containing_services': sum(r['arm'] == 'T_FULL' and r['returns_rca_services'] == '1' for r in r41)}

specs = [
    ('RQ4.2', 'RQs/RQ4_2/results/partition_v4/final_analysis_v1/qa_calls.csv', 'gold', 'answer'),
    ('RQ4.4', 'RQs/RQ4_4/results/source_views_v1/analysis/detailed_v1/qa_calls.csv', 'expected', 'response'),
    ('RQ4.5', 'docs/experiment_reports/artifacts/RQ4_5_2026-10-19/qa_rca_answers.json', 'expected', 'qa_response'),
    ('RQ4.6', 'docs/experiment_reports/artifacts/RQ4_6_2026-10-19/qa_rca_answers.json', 'expected', 'response')]
datasets = {}
for name, path, key, response_key in specs:
    rows = read(path)
    datasets[name] = rows
    oracles = {}
    shapes = Counter()
    for row in rows:
        oracle = json.loads(row[key]) if isinstance(row[key], str) else row[key]
        oracles[(row['id'], json.dumps(oracle, sort_keys=True))] = oracle
        try:
            answer = json.loads(row[response_key])
            shapes['json_parseable'] += 1
            shapes['exact_top_keys' if isinstance(answer, dict) and set(answer) == set(oracle)
                   else 'different_top_keys'] += 1
        except (ValueError, TypeError):
            shapes['json_unparseable'] += 1
    d = summary['rounds'][name] = {
        'answer_positions': len(rows), 'unique_cases': len({r['id'] for r in rows}),
        'distinct_case_oracle_packets': len(oracles), 'response_shape': dict(shapes),
        'blank_answer_fields': [{'id': oid, 'field': field} for (oid, _), oracle in oracles.items()
                               for field, value in leaves(oracle) if value == ''],
        'explicit_null_fields_by_path': dict(Counter(field for oracle in oracles.values()
                                                     for field, value in leaves(oracle) if value is None))}
    if name == 'RQ4.4':
        d['oracle_units'] = dict(Counter(v['unit'] for v in oracles.values()))
        d['k_M_G_suffix_oracles'] = sum(any(str(v[k])[-1:] in 'kMG' for k in ('reference', 'current'))
                                      for v in oracles.values())
        d['local_target_counts'] = dict(Counter(r['condition'] for r in rows
                                                if r['target_in_detail'] == 'True'))
    if name == 'RQ4.5':
        d['comparison_phase_distribution_one_copy_per_case'] = dict(Counter(
            v[q]['higher_phase'] for v in oracles.values() for q in ('q5', 'q6') if v[q] is not None))

r43 = read('docs/experiment_reports/RQ4_3_Qwen_Analysis_2026-10-12_assets/qa_tolerant_questions.csv')
summary['rounds']['RQ4.3'] = {
    'answer_positions': len({r['key'] for r in r43}), 'unique_cases': len({r['id'] for r in r43}),
    'applicable_question_positions': len(r43),
    'blank_answer_fields': [{'id': r['id'], 'arm': r['arm'], 'question': r['question'], 'field': k}
                           for r in r43 for k, v in leaves(json.loads(r['truth'])) if v in ('', None)],
    'support_flags': dict(Counter(r['visible'] for r in r43))}
r47 = read('docs/experiment_reports/artifacts/RQ4_7_2026-10-20/qa_answerability_audit/questions.json')
summary['rounds']['RQ4.7'] = {
    'answer_positions': len({r['id'] for r in r47}), 'applicable_question_positions': len(r47),
    'empty_entity_questions': sum(r['empty_expected_entity'] for r in r47),
    'empty_entity_cases': len({r['id'] for r in r47 if r['empty_expected_entity']}),
    'phase_distribution': dict(Counter(r['expected']['phase'] for r in r47)),
    'whole_comparison_row_targets': sum(r['target_kind'] == 'comparison_row' for r in r47),
    'outside_canvas': sum(not r['inside_canvas'] for r in r47),
    'source_scalar_absent_from_recorded_visible_text': sum(not r['displayed_exact_value_at_card_or_added_row'] for r in r47),
    'zero_intersecting_retained_tokens': sum(r['retained_intersecting_merged_tokens'] == 0 for r in r47)}

# Existing request, not a reconstructed prompt. Check the missing locator contract.
qa_cases = read('docs/experiment_reports/artifacts/RQ4_7_2026-10-20/qa_case_answers.json')
texts = []
for row in qa_cases:
    request = read('RQs/RQ4_7/results/source_workspace_v1/formal/' + row['request_path'])
    texts.append('\n'.join(m['content'] if isinstance(m['content'], str)
                           else '\n'.join(p.get('text', '') for p in m['content'])
                           for m in request['messages']))
summary['rounds']['RQ4.7']['actual_prompt_contract'] = {
    'requests_read': len(texts),
    'has_0_to_1000_definition': sum('0..1000' in t or '0–1000' in t or '0-1000' in t for t in texts),
    'has_left_top_right_bottom_definition': sum('left' in t and 'right' in t and 'bottom' in t for t in texts),
    'has_canonical_window_vocabulary': sum('whole_window' in t or 'observed_window' in t for t in texts)}

# Counterexamples: no jsonschema dependency or experiment-module import.
# RQ4.7 score_qa imports jsonschema, so use available environment only; if missing,
# record no probe result rather than substitute an evaluator.
probes = []
try:
    import jsonschema  # noqa: F401
    s47 = isolated('RQs/RQ4_7/src/utils.py', ['qa_schema', 'score_qa'])['score_qa']
    unit_row = next(r for r in r47 if r['expected']['unit'] == 'milliseconds_or_source_unit')
    want = unit_row['expected'].copy(); got = want.copy(); got['unit'] = 'milliseconds or source unit'
    out = s47(json.dumps({'answers': [got]}), {'answers': [want]})
    probes.append({'name': 'copy_displayed_unit_with_spaces', 'synthetic': True,
                   'id': unit_row['id'], 'expected': want, 'submitted': got,
                   'tolerant_joint': out['tolerant'], 'numeric_and_entity_unchanged': True})
    row = next(r for r in r47 if r['id'] == 'INC-C10F5EA649A5' and r['question'] == 2)
    out = s47(json.dumps({'answers': [row['actual_answer']]}), {'answers': [row['expected']]})
    probes.append({'name': 'actual_operation_name_answer', 'synthetic': False,
                   'id': row['id'], 'score': out['questions'][0]})
    s45 = isolated('RQs/RQ4_5/src/utils.py', ['qa_schema', 'score_qa'])['score_qa']
    expected = datasets['RQ4.5'][0]['expected']
    answer = json.loads(json.dumps(expected)); answer['comment'] = 'extra field'
    out = s45(json.dumps(answer), expected)
    probes.append({'name': 'all_correct_RQ45_answers_plus_unasked_extra_key', 'synthetic': True,
                   'standard': out['standard'], 'tolerant': out['tolerant'], 'schema_valid': out['schema_valid']})
except ModuleNotFoundError:
    summary['isolated_probe_status'] = 'not executed: jsonschema unavailable in this Python'
summary['isolated_scorer_counterexamples'] = probes

for f in sorted((ROOT / 'docs/experiment_reports').glob('RQ4_*_Qwen_Analysis_*.md')):
    if f.name.split('_')[1] in {'1', '2', '3', '4', '5', '6', '7'}:
        read_text(str(f.relative_to(ROOT)))
for rq in range(1, 8):
    for module in ('exps', 'utils'):
        read_text(f'RQs/RQ4_{rq}/src/{module}.py')
for path in (
    'docs/experiment_reports/RQ4_3_CPU_Qualification_v7_2026-10-11.md',
    'docs/experiment_reports/RQ4_7_QA_Answerability_Audit_2026-10-20.md',
    'RQs/RQ4_1/findings/exp_comparison_coding_findings.md',
    'RQs/RQ4_1/descriptions/RQ4_1_Statistics_V11_Adoption_2026-10-07.md',
    'src/renderer/web/components/CompleteMarginals.tsx',
    'src/renderer/web/components/PhaseMarginals.tsx',
    'src/renderer/web/factualQA.ts',
):
    read_text(path)

OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'audit_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
(OUT / 'local_sources.json').write_text(json.dumps(SOURCES, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'rounds': {k: v['answer_positions'] for k, v in summary['rounds'].items()},
                  'read_sources': len(SOURCES), 'probes': len(probes), 'new_model_calls': 0}, ensure_ascii=False))
