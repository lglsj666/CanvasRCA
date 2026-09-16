# DD-RQ3-SEARCH-22 — Typed metric owners and additive resource coverage

Train-only development, registered before new inference. Reuse SEARCH-21's
same24 train cases and immutable public pools. No validation/eval or training.
The private train audit finds both root-associated evidence absent from the
selected packet and wrong ownership/direction interpretations despite visible
signals. It guides a generic hypothesis, not per-case labels or thresholds.

Two24-call pipelines, same large canvas, guide, candidates and Qwen recipe:

1. Existing node_overview_v1, with metric labels explicitly spelling SERVICE,
   NODE or POD before the existing numeric owner. These words duplicate the
   public3/4/5-digit identity convention; no candidate-list panel is drawn.
   Compare to completed SEARCH-21 overview; preserve its original responses.
2. balanced_additive_v1: keep nativeM8, then add up to three distinct owners
   for each CPU/memory/IO/latency family in each node/non-node stratum. Choose
   by absolute period-mean change divided by max(sum of absolute means,
   twice regular standard deviation,1e-9), then native rank and fact ID.
   Reuse the existing public metric-family ontology and MET-Z periods. Skip
   unavailable period statistics. Do not use fault types, roots, source names,
   labels or case-specific branches. Existing selections never count as new
   slots for the same stratum; each stratum records up to three owners overall.
   The native eight are never removed. At most32 curves; R4/L2 unchanged,
   G context follows selected owners under the existing fixed rule.

Pipeline2 uses the same typed-owner labels as1. It tests balanced additive
coverage versus node-only coverage, not isolated reordering. Sampling noise
remains; no resampling/retaining the best answer. All failures retained.
Full candidate lists remain in prompt only, no diagnostic text, one image,
no attention. Source values/bins/units and native axes remain unchanged.

Check old default pixels unchanged, all current selected facts bound to real
primitives, deterministic bounded selection and provenance, missing/constant
statistics, public granularity only, actual typed labels and geometry. Inspect
both datasets and sparse cases before calls. Keep all48 actual requests/raw
answers/partials and source/config hashes; report per-dataset MRR/cost and
paired repair/break descriptively. These are development batches, not new
nominal smokes. Targets cannot be declared from these24 train cases.

Pre-call CPU check exposed one config error: inherited YAML loader supports
one extends level, not a chain. Both new configs now extend rq3.yaml directly
with complete versioned search settings. Source loader/shared defaults are
unchanged. Eleven other checks passed; full regression follows. Zero calls.

Full CPU regression281 passed in76.03 s; five functional modules6000 lines.
Source-value geometry, strict owner roles and missing/non-numeric period
handling tested. Native recipe/config remain unchanged. Actual typed overview
PNGs opened for A22 4BA and A25 C6AD (latter with original-detail image mode):
complete numeric owners and chart labels remain readable, no candidate panel.
Independent all-case pixel/fact/source audit and second-family review pending.

Part1 now complete:24/24 in345.991 s. MRR A22 .520833,A25 .429167 versus
untyped .5375/.3500; exploratory Holm p=1 for both. All24 answers and actual
inputs/partials read and audited; max374 output, no infrastructure/schema/
truncation failure. Explicit metric-owner words do not eliminate invented
hosting or type/direction confusion in reasons. No promotion/target claim.
Details:results/search_first_v1/typed_overview_development_v1/logs/20260912_review.md.
Both all24 gallery audits pass; balanced gallery has21–27 metric series,
all nativeM8 retained, R/L facts unchanged. Actual9FFD/492/0917 PNGs inspected;
second24 launched under work-spec
df9d484dd76a93dfcdd4fa873ad45d07ef165ef1d4edbf311ffd93e634832bc9.

Part2 complete24/24,343.297 s. Balanced MRR A22 .273611,A25 .370833;
lower than typed overview .520833/.429167. Not promoted. All answers read,
max322 output,no errors/truncation;source/candidate/conversation/partial
audits pass. Full details and negative outcomes preserved in
results/search_first_v1/typed_balanced_development_v1/logs/20260912_review.md.
All48 registered SEARCH22 calls complete; search accounting560. No follow-on
training or eval authorized by these train-only scores.
