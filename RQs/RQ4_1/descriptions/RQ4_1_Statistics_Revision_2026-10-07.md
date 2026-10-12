# RQ4.1 — Prospective bounded-mean statistics revision

## Authority and scope

The user asks to modify the failed QA statistical calibration on 2026-10-07.
This authorizes an outcome-free statistical-method repair. It supersedes the
previous prohibition on investigating a replacement test for this prospective
revision only. It does not authorize inspecting diagnostic answers to select a
test, deleting the old failure, weakening thresholds, changing experiment arms,
or launching GPU/model/confirmation work. No new RQ4.1 development or QA
responses exist. Historical token-interface probes are not used here.

The original sign-flip reports remain immutable. v10 is still checking unrelated
CPU compatibility against its frozen source; this addition does not hot-edit
those files or repeat successful rendering/encoder/selector checks. The generic
inference utility is additive under `src/scorer/bounded_mean.py`; scoring and
entity matching are unchanged. The explicit revision configuration and result
receipt are separate from the running v10 qualification.

## Why the existing check failed

The registered statistic targets the case-weighted mean paired score difference.
Sign-flip calibration assumes a sign-symmetric null, but the stress design
deliberately includes asymmetric zero-mean laws and 75% zero inflation. These
conditions are not equivalent. On the 87 applicable QA cases, three of 54 cells
exceeded the .07 alarm (maximum .081). The earlier 220-case development check
also failed (maximum .0935). Neither result measures model QA accuracy.

## One fixed candidate, registered before new simulations

Use a **fixed-sample bounded group-mean mixture e-test**. Do not search over
methods or select a new test after examining model outcomes. The inference is
two-sided and keeps the case-weighted mean target and registered Holm families
(six main contrasts, two QA contrasts). It does not test the median, the fraction
of cases won, or the unweighted event-group mean instead of MRR/QA mean gain.

For registered independent groups g with fixed case count n_g, let
S_g = sum of paired case score differences in group g, each in [-1,1]. Let
B = max_g(n_g). For each of the 32 fixed signed betting fractions
b = ±(2j+1)/32, j=0,...,15, define

    E_b = product_g (1 + b S_g / B)
    E = mean_b(E_b)
    p = min(1, 1/E).

Compute in log space. The grid and its equal weights are fixed before the
simulation, not fitted to QA or RCA results. Exact zero scores stay zero;
unknown infrastructure outcomes cannot be silently imputed or omitted to make
the test stronger. Future paired-known inference must retain original-denominator
bounds and its restricted estimand; this utility never imputes missing results.
Registered 12-decimal paired differences are aggregated before calling it.
No confidence intervals are generated.

### Elementary validity argument for the actual estimand

Under the weak null sum_g E[S_g] = 0, and independence across groups,

    E[E_b] = product_g (1 + b E[S_g]/B)
           <= exp(b sum_g E[S_g]/B) = 1.

All factors are strictly positive because |b|<1 and |S_g|<=B. Averaging the
fixed factors preserves this expectation bound. Markov's inequality gives a
super-uniform p-value min(1,1/E), to which the unchanged Holm procedure applies.
Group expectations may differ and cancel; their distributions need not be
symmetric or identical. Dependence within a group is unrestricted. Counts must
remain inside S_g; replacing S_g with a group mean changes the target and is
forbidden.

This is a project-specific fixed-sample application of standard e-value and
betting ideas, with the proof above provided explicitly. It is **not** a claim
that the cited papers directly establish this exact group-weighted implementation,
nor a new contribution of the CanvasRCA method. It is not an anytime-valid
procedure for repeatedly inspecting the experiment until significance occurs.

Background primary sources:
- Vovk and Wang, *E-values: Calibration, combination, and applications*,
  Annals of Statistics (2021): https://arxiv.org/abs/1912.06116.
- Waudby-Smith and Ramdas, *Estimating means of bounded random variables by
  betting*, JRSS-B (2024): https://doi.org/10.1093/jrsssb/qkad009.

## Qualification and power disclosure

Freeze this text, the utility, tests, shell trigger and configuration before
running new simulations. Read only the old stress registrations and group
structure, not outcome files. For both the 87-case QA and 220-case development
structures, keep all 54 stress laws, 2,000 outer replicates, shifts
0/.02/.03/.05, alpha=.05 and the maximum-cell .07 alarm. Use two independently
seeded, prospectively fixed simulation banks; no seed changes after results.
No sign flips are needed by the new deterministic test. Old 4,999-flip results
remain historical rather than being relabeled.

Report every cell's error rate and power, including a conservative alpha/family
power screen (not actual joint Holm power). Compare with the preserved old
reports, including weak results. Passing calibration does not imply useful
power for .02/.03/.05 gains. A particularly conservative test cannot be described
as having solved the sample-size problem. Do not expand the case set, call
budget, or independence assumptions merely to obtain significance.

CPU unit checks cover an independent exact-rational expectation oracle with
heterogeneous group means summing to zero, all-zero data, one dependent group,
unequal sizes/target preservation, deterministic batching and order, both
directions, extreme non-null effects, invalid bounds and Holm family handling.
Use at most two currently free physical cores, offline, no model calls, and the
original remaining CPU deadline. Preserve both simulation banks and all failures.

## Deployment boundary and remaining limitations

Calibration validity, power and engineering availability are separate statuses.
The fixed-group independence assumption remains unproven for distinct events
sharing a source; this repair addresses asymmetry, not that dependence risk or
the already-exposed development population. It cannot turn these cases into
an untouched confirmation set.

After review, record whether this version is usable as a conservative prospective
inference procedure. A new statistics receipt does not automatically rewrite the
old `no_confirmation_declaration.json`, restore the 2,400 reserved calls, or
activate GPU/confirmation. Those require a fresh complete frozen contract and
the pre-existing exposure, engineering and execution gates. The running v10
report remains a valid historical report of its original test.
