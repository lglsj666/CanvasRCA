# RQ4.1 — Adoption of conservative v11 inference

**Date:** 2026-10-07 (America/Toronto). **Status:** adopted by explicit user instruction, before new development or QA outcomes.

## Decision and precedence

The user explicitly selects v11: “明白了，那就用v11吧。” Adopt the unchanged
`fixed_bounded_group_mean_mixture_v1` implementation in
`src/scorer/bounded_mean.py` for the decisive development and QA inference.
This supersedes the earlier v11 disposition declining primary adoption and the
sign-flip primary-test clauses in the experiment protocol §§8, 13 and 16.
Historical descriptions, frozen snapshots, failures and candidate reports stay
unchanged. v12 remains rejected; no further test or seed search is scheduled.

The effective statistical registration is `configs/statistics_active_v11.json`.
It is an additive analysis-policy overlay, not a runtime launch credential.
The running v10 CPU audit keeps its original source/configuration freeze and
reports the old sign-flip calibration honestly. That old statistical status does
not describe the newly adopted v11 procedure. Bind this overlay and its hashes
into the next execution/analysis freeze before model calls; do not hot-edit the
running audit or silently treat its old configuration as the new analysis policy.

## Unchanged estimand and decision requirements

- Target the case-weighted paired mean RR or registered joint-block QA score
  difference, with paired differences rounded to 12 decimal places before
  aggregation. Preserve registered event groups, their member counts and group
  sums; do not substitute unweighted group means.
- Use v11's fixed 32 signed fractions, equal mixture, two-sided p-value and
  maximum-group-size normalization exactly as qualified. No fitted bets,
  optional stopping or selection of the most favorable test.
- Keep alpha 0.05 and the existing six-comparison primary Holm family and
  separate two-comparison QA Holm family. Positive direction and all registered
  effect-size, cost, repeat and applicability requirements remain unchanged.
- Preserve existing Wilcoxon/dz sensitivity analyses and secondary registrations;
  they do not rescue a failed primary comparison. No confidence intervals.
- Invalid committed model answers remain zero; infrastructure unknowns remain
  unknown. Paired-known estimates and full-denominator bounds keep their
  registered interpretation. Unresolved infrastructure prevents adoption.

## Evidence and accepted limitation

The unchanged implementation passed 12 numerical tests and both fixed simulation
banks for QA and development. Reuse these results without rerunning them. The
maximum observed null rejection was 0.75% in QA and 0.35% in development, below
the original 7% alarm. These simulated rates are not universal guarantees.

Power remains low. Across the registered stress laws and both banks, at a
nominal +0.03 shift followed by clipping to [-1,1], the maximum unadjusted
two-sided rejection rate was 2.15% for QA and 0.40% for development. The nominal
shift need not equal the realized mean difference after clipping. These are
simulation results, not model accuracy or a predicted experiment success rate.
The later 80% planning reference is not an added CPU/GPU launch gate.

The user accepts this conservative inference tradeoff. Report observed MRR,
QA, cost and repeat differences even if nonsignificant; nonsignificance does
not establish absence of an effect. Claims of statistically established gains
still require the unchanged registered criteria. v11's argument assumes
independence between event groups; shared-source dependence remains unresolved
and must be disclosed. Calibration does not make exposed development cases an
independent confirmation population.

## Execution boundary

This adoption neither passes unfinished engineering checks nor authorizes a
model service, GPU smoke, formal run or independent confirmation. The existing
no-confirmation declaration and unused 2,400-call allocation remain in force.
No experiment arms, evidence, prompts, model recipes, scorer values, calls or
budgets change. Previously passed CPU checks stay valid and are not repeated.

Evidence: `results/comparison_coding_v1/statistics_revision_v11/` (original
qualification), `statistics_power_v12/` (rejected alternative), and
`statistics_v11_adoption/` (adoption receipt and current CPU status snapshot).
