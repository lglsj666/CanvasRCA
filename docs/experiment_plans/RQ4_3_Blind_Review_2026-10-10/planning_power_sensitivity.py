"""Historical-variance sensitivity for planning; no model, renderer or qualification."""
from pathlib import Path
from collections import defaultdict
import csv, hashlib, json
import numpy as np
from scipy.stats import wilcoxon

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'RQs/RQ4_1/results/comparison_coding_v1/final_analysis_v1/calls.csv'
rows = [r for r in csv.DictReader(SOURCE.open()) if r['kind'] == 'development']
by_arm = defaultdict(dict)
for row in rows:
    by_arm[row['arm']][(row['dataset'], row['id'])] = row
records = []
repetitions = 4000
for counter, (a, b) in enumerate([('A_UNIFORM_E50', 'CVC_E50'), ('A_UNIFORM_E50', 'V_FULL')]):
    grouped = defaultdict(list)
    datasets = defaultdict(set)
    for key in sorted(by_arm[a]):
        ra, rb = by_arm[a][key], by_arm[b][key]
        group = (ra['dataset'], ra['group'])
        assert group == (rb['dataset'], rb['group'])
        grouped[group].append(float(ra['mrr']) - float(rb['mrr']))
        datasets[ra['dataset']].add(group)
    d = np.round(np.array([np.mean(v) for _, v in sorted(grouped.items())]), 12)
    magnitude = np.abs(d)
    mean_abs = float(magnitude.mean())
    rng = np.random.default_rng(20261010 + counter)
    # Resample complete group magnitudes, retain empirical zeros; signs supply
    # a stated symmetric null / sign-biased alternative, not an actual new arm.
    samples = rng.choice(magnitude, size=(repetitions, len(d)), replace=True)
    uniform = rng.random(samples.shape)
    for target in (0.0, 0.02, 0.03, 0.06, 0.10):
        prob_positive = (1 + target / mean_abs) / 2
        if prob_positive > 1:
            records.append({'scale_pair': [a,b], 'target_group_mean':target, 'status':'outside_sign_bias_support'})
            continue
        simulated = np.round(np.where(uniform < prob_positive, samples, -samples), 12)
        p = wilcoxon(simulated, axis=1, zero_method='pratt', alternative='two-sided', method='approx', correction=False).pvalue
        records.append({'scale_pair':[a,b], 'groups':len(d), 'groups_by_dataset':{k:len(v) for k,v in datasets.items()}, 'historical_difference_sd':float(d.std(ddof=1)), 'historical_zero_fraction':float(np.mean(d==0)), 'mean_absolute_difference':mean_abs, 'target_group_mean':target, 'simulated_mean':float(simulated.mean()), 'positive_probability':prob_positive, 'reject_at_0_025':float(np.mean(p<0.025)), 'reject_at_0_05':float(np.mean(p<0.05)), 'repetitions':repetitions})
result={'schema':'RQ43PlanningPowerSensitivityV1','source':str(SOURCE.relative_to(ROOT)), 'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'seed':20261010,'status':'planning_sensitivity_not_experiment_qualification','model_calls':0,'assumptions':['Resampled historical event-group absolute differences and tie mass; random signs under null, fixed sign bias under alternatives.','Alternative target is equal-event-group mean, not pooled case delta.','Alpha .025 is a conservative per-comparison threshold for a two-comparison Holm family, not the family joint power.','Results do not predict X_SRP performance or demonstrate power against arbitrary asymmetric/heterogeneous alternatives.','This simulation is not a validation of evidence selectors or a reason to select a more favorable test.'], 'records':records}
Path(__file__).with_name('planning_power_sensitivity.json').write_text(json.dumps(result,indent=2)+'\n')
for r in records:
    print(r['scale_pair'],r['target_group_mean'],r.get('reject_at_0_025'),r.get('groups'),r.get('historical_difference_sd'))
