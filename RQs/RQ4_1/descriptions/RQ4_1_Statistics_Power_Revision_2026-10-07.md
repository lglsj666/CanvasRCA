# RQ4.1 — Prospective bootstrap-t and power audit (v12)

## Authority and frozen scope

The user now requests improving power as well as calibration. This is a new
outcome-free revision after v11, explicitly superseding v11's stop-after-one-
candidate boundary for this additional candidate. Preserve every v11 result
and its decision not to replace the primary test. Do not inspect model answers,
select cases, change scores, change the effect target, or spend model calls.
The user has not authorized GPU smoke/formal/independent confirmation here.
Apply the experiment and design-decision workflows. Existing engineering CPU
checks continue under their own frozen v10 source.

## Candidate chosen before new simulations

Use an **equal-tail studentized pairs cluster bootstrap** on the case-weighted
mean paired score difference. This method estimates the sampling variability
from whole event groups, keeps the empirical skew shape, and avoids v11's
worst-group-size bound. Its validity is asymptotic under appropriate independent
group sampling/regularity, not an exact arbitrary-distribution finite-sample
guarantee. Simulations must check finite-sample error before any adoption.

For fixed observed pairs (S_g,n_g), with S_g the sum of paired score differences
within group g, N=sum(n_g), G groups:

    d = sum(S_g)/N
    r_g = S_g - n_g*d
    t = sum(S_g) / sqrt(G/(G-1) * sum(r_g^2)).

Each bootstrap sample draws G intact (r_g,n_g) pairs with replacement. Recompute
its total N*, mean d*=sum(r*)/N*, residuals r*-n* d*, and studentized t* using
the same G/(G-1) factor. This is equivalent to resampling uncentered (S_g,n_g)
pairs and forming (d_boot-d)/SE_boot. Never resample individual questions as
independent cases. Never replace the weighted mean by a median or mean of
unweighted group means. The numerical implementation uses group sufficient
statistics and multinomial counts, checked against explicit group expansion.

Use exactly 4,999 bootstrap draws, inclusive tail counts with plus-one Monte
Carlo correction, p=min(1,2*min(P(t*<=t),P(t*>=t))). Do not switch to a one-sided
test or absolute-tail rule after results. Bootstrap residuals are not clipped.
Zero bootstrap variance gives signed infinite t* when its numerator is nonzero,
zero otherwise; no draw is discarded. If the observed sample variance is zero,
return p=1 and explicitly report this limitation. Numerical roundoff tolerances
are fixed at 1e-12 relative to the computed second-moment terms. No CI.

Use existing six-main/two-QA Holm families without dropping failed comparisons.
All finite-family results remain subject to the test's assumptions; passing
these stress laws cannot prove independence or validity for every population.

Primary research background:
- James G. MacKinnon, *Fast cluster bootstrap methods for linear regression
  models* (Econometrics and Statistics, 2023), group sufficient-statistic
  computation: https://econ.queensu.ca/faculty/mackinnon/working-papers/qed_wp_1465.pdf.
- MacKinnon, Nielsen and Webb, *Cluster-Robust Inference: A Guide to Empirical
  Practice*: https://arxiv.org/abs/2205.03285.
- Neyman–Pearson most powerful test principle, used only for the hard-example
  oracle: https://www.math.csi.cuny.edu/~mvj/MTH410-S23/lectures/L11.html.

This scalar weighted-mean implementation is documented explicitly, rather than
claimed as a direct reproduction of every regression method in those papers.

## Fixed validation design

For the same QA87 and development220 group structures, preserve all 54 laws,
2,000 simulated datasets per law, nominal shifts 0/.02/.03/.05, alpha .05 and
maximum-cell alarm .07. Run two independent prospectively fixed banks, each
with separate data and resampling seeds. Within a bank/cohort, independently
generated bootstrap indices are shared across synthetic datasets/comparisons
for matrix efficiency; changing the bank changes both random streams. Report
this Monte Carlo convention, both banks and all cells. No method/seed search.

Preserve v11's full results for comparison; do not rerun its passed tests.
Report nominal and conservative alpha/family power (the latter is not actual
joint Holm power). Report realized means after the inherited [-1,1] clipping:
**a nominal +.03 shift need not produce a true +.03 mean change** at a boundary.
The v11 review's shorthand 'true +.03' should therefore be read as 'nominal
shift +.03' for its inherited clipped stress simulations. Its raw numbers and
non-adoption decision remain unchanged.

## What 'adequate power' means in this review

Use 80% detection probability as an explicitly new planning reference, not an
old registered gate or a guarantee. Report its attainment separately for every
stress cell/effect and after the conservative multiplicity screen; never select
only the easiest cell and describe the entire experiment as adequately powered.
No new hard power requirement is silently imposed on the RCA engineering run.

Also compute a fixed analytical hard example with D_i in {-1,+1}, n independent
cases, H0:P(D=+1)=.5 and H1:P(D=+1)=(1+delta)/2 for delta .02/.03/.05.
Enumerate the exact binomial upper-tail Neyman–Pearson test, including randomized
boundary to use precisely alpha .05. It even knows the favorable direction
and both distributions. Its power is an upper bound for any level-.05 test
**for this specific simple pair**. It is not an upper bound for low-variance
telemetry populations. This distinguishes a fundamental sample-size limitation
from v11's avoidable conservatism without relying on a normal approximation.
Compute the smallest n giving this oracle 80% power, without registering new
cases or calls. The oracle does not replace any inferential method or score.

## Execution and decision boundary

Freeze source, tests, config, trigger and these decisions first. Run only new
CPU numerical checks and the statistical audit, at most four free physical
cores (combined with v10 at most eight), within the original CPU deadline.
Keep GPU/formal switches off and all old artifacts. On implementation failure
preserve logs, repair the implementation and rerun affected checks; do not
change inference choices to improve observed simulation scores.

Review calibration and power separately. If bootstrap-t fails calibration,
do not adopt it regardless of apparent power. If it passes, quantify the power
improvement and remaining sample-size limitations before recommending use.
Do not call a low-powered setting 'adequate' just because it improves over v11.
No automatic independent confirmation, test replacement in a running frozen
contract, experiment expansion or model launch follows this audit.
