# RQ3.9 roadmap

Current execution authority, 2026-10-01: formal execution is paused by the
user. Step4 below requires a new explicit launch instruction; qualification
completion does not authorize an automatic restart. Preserve the existing
protocol, preparation, smoke and interrupted formal artifacts.

1. Implement and freeze the four-condition small pilot. Preserve all old RQs.
2. Static logical/operational/leakage review; bounded CPU qualification;
   inspect representative real PNGs and both text arrangements.
3. Three-case bounded GPU smoke; review actual conversations and saved images.
4. Launch the complete registered120-case Qwen pilot in the background; stop
   operator monitoring once requests actually begin. Never start test expansion.
5. Only after terminal results and writer drain, analyze primary/secondary
   contrasts, applicability, failures, repair/break and costs; decide subsequent
   research from complete evidence, including negative results.

## Discussion review, 2026-10-01 — proposal, not a registered successor

Read the complete698-line `conversation_oct_01.md` and cross-check the
Qwen-only RQ1.1/2.1, RQ3.1/3.2/3.4/3.6 and completed RQ3.7-C/RQ3.8 reports.
Recommend investigating observable support and conflict between competing
fault explanations before building an uncalibrated counterfactual predictor.
Retain RQ3.9 as a bounded organization study; it cannot establish the accuracy
of candidate-conditioned response predictions.

A read-only aggregate of the120 already prepared cases found:

| Cached public-input property | AIOPS2022 | AIOPS2025 | AegisLab |
|---|---:|---:|---:|
| Cases inspected |40|40|40|
| Same-service mappings spanning multiple hosts |29|38|0|
| Cases with a selected same-service metric comparison |16|12|0|

These counts concern the frozen RQ3.8 public bundles and RQ3.9 selected groups,
not all canonical telemetry or the actual complete deployment. They do not
establish peer health, activity, metric comparability or diagnostic sufficiency.
An unused-event or full-pool availability audit has not been performed here.

Root-label granularity is not fault impact scope: a service-labelled fault may
be local to one pod, and a host fault need not affect every colocated pod.
Unknown/inactive/incomparable observations cannot be used as negative evidence.
When service and pod scopes are observationally indistinguishable, retain that
ambiguity instead of manufacturing a prediction or changing the scorer.

Proposed next step: audit public, complete per-case availability and historical
scope-confusion examples, then register one small pilot separating extra facts,
candidate-conditioned comparison, visual representation and scope geometry.
Include the strongest eligible historical visual baseline, a genuinely matched
text comparison and a CPU-only ranking from the same computed evidence.
Only explicit, qualified empirical scope assumptions may generate a support
or conflict entry; no predicted telemetry is passed off as an observation.
Do not advertise numerical prediction residuals before a response model has
independent calibration. Evaluate overall repair/break and MRR as well as
applicable cases, preserving no-op and unidentifiable cases.

Relevant primary mechanisms checked: CIRCA (KDD2022, conditional-distribution
intervention recognition) and Sage (ASPLOS2021, learned dependency-aware
counterfactual performance prediction). Neither makes counterfactual RCA a
new contribution by itself:
https://netman.aiops.org/wp-content/uploads/2022/08/KDD22-CIRCA.pdf
https://www.csl.cornell.edu/~delimitrou/papers/2021.asplos.sage.pdf

This entry records a research recommendation only. It changes no experiment
source, arm, input, qualification result or execution authorization. No CPU
regression, rendering, GPU inference or training was launched for this review.
