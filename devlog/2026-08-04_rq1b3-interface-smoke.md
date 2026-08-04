# 2026-08-04 — RQ1b3 two-stage interface smoke

## Outcome

Implemented and qualified the DD-30 two-stage onset-ledger mechanism, froze
new disjoint 90-case development and 150-case gate rosters, and ran the
partition-aware Gemma Stage-1 validation smoke. Static fact parity, leakage,
answer separation, deterministic rendering, and manual visual review passed.
The v1 model interface did not pass its complete smoke gate.

## Runs

- Main Stage 1: 9/9 requests completed, parse 1.000, no truncation or
  infrastructure failure.
- Deterministic row-sham Stage 1: 6/6 requests completed, parse 0.8333, one
  output truncation.
- Failed response:
  `RQs/RQ1/results/rq1b3_two_stage_smoke_v1/gemma/sham_stage1/calls/4b0b177b78f13600b42de6bb.json`.

The failed response produced a syntactically plausible ledger prefix and then
repeated JSON-legal whitespace after a `sign` key until the frozen 16,384-token
completion ceiling. A separate diagnostic probe reproduced the whitespace
stall with a minimal JSON schema. A strict guided-regex probe returned compact
valid JSON in 11 tokens.

## Validity status

RQ1b3 v1 is a valid **failed interface smoke**, not an efficacy result. It did
not open or infer any 90-case development or 150-case gate incident. It does
not alter the status of RQ0, RQ1b mapping/gate, or RQ1b2 development. The
earlier wrong-interpreter launch sent no model requests and remains separately
invalidated.

## Decision and next step

DD-31 registers RQ1b3 v2. Preserve all v1 artifacts and hashes. Keep the same
evidence, T/V/H prompts, strict image-first A+B composition, onset semantics,
two-stage estimator, models, vLLM sampling configuration, rosters, metrics,
and thresholds. Replace only the whitespace-permissive response transport with
a task-specific no-whitespace guided regex and compact semantic ledger entries;
expand them deterministically to the full persisted ledger before Stage 2.

## V2 qualification result

V2 passed the full interface qualification:

- main Stage 1: 9/9 parsed, zero truncation and infrastructure failure;
- row-sham Stage 1: 6/6 parsed, zero truncation and infrastructure failure;
- main Stage 2: 12/12 parsed, including three oracle calls;
- row-sham Stage 2: 6/6 parsed;
- complete token/GPU accounting and verified no original-evidence access at
  Stage 2;
- oracle Stage-2 exact accuracy 1.000, above the frozen 0.95 threshold.

All compact Stage-1 outputs contained no whitespace and the maximum completion
was 103 tokens. The complete qualification file SHA256 is
`0d024dab2720f4765ce7574785d3cc12bda92e81402dd0e6830a54948b12f60a`.

DD-32 accepts the smoke and authorizes only the frozen 90-case Gemma
development cell. Qwen and the 150-case gate remain blocked until every Gemma
promotion condition passes.

## Development-roster qualification

The subsequent data-only development preparation compiled 77/90 incidents
and stopped before any model call because thirteen incidents did not support
the registered 12-panel task (AegisLab 4, AIOPS-2022 5, AIOPS-2025 4). DD-33
records this as a pre-inference roster-qualification failure and registers a
label-blind replacement rule. The original roster remains immutable; the
repaired roster retains all 77 supported cases and fills only the per-dataset
deficits by the frozen development hash order, excluding every prior RQ1 case
and the unopened independent gate. Development remains blocked until the
repaired 30/30/30 roster is requalified and frozen.

The repair completed successfully. It retained all 77 supported originals,
scanned 5/8/4 candidates in the frozen dataset-specific order, accepted the
required 4/5/4 replacements, and produced a 30/30/30 roster with zero gate
overlap. The public audit SHA256 is
`e8bd389352e53a503399c4f935acdf4f27739649ac85dddf5f13faf0173476fb`.
All 104 RQ1 tests passed after the repair implementation.

The repaired inventory then prepared 90/90 tasks and passed full
qualification: exact fact parity and leakage checks, 180 nonblank main/sham
images, 13 manually reviewed images, and 12/12 deterministic recompilations.
The qualification report SHA256 is
`9881c82166cd073e4f6b17749e9c08fbf71ed757c609c50bb9c341a2de702344`;
the frozen runtime tree is
`a951f5215bbeb170854bde7a725e161b0b50c1d55d9f3ddf0c1f8fac65c3c344`.
Main and row-sham dry-runs passed, so the complete 90-case Gemma development
cell is authorized next.

## Development execution and decision

The authorized Gemma cell completed all 990 registered calls:

- main Stage 1: 270/270;
- main Stage 2: 360/360, including 90 oracle calls;
- row-sham Stage 1: 180/180;
- row-sham Stage 2: 180/180;
- zero infrastructure failure, truncation, or paired exclusion.

The authoritative analysis is `valid_failed`. Final accuracy was
T/V/H=0.6222/0.1667/0.5889 and final H−T=−0.0333. Stage-1 panel accuracy was
T/V/H=0.8944/0.5083/0.8917 and ledger H−T=−0.0028. H repaired 10 text errors
and broke 13; H ledger error 0.0774 exceeded T's 0.0668; oracle Stage-2 accuracy
was 0.8000. Every one of the six promotion requirements failed.

The first analysis invocation exposed an analysis-only config-key typo; the
frozen file uses `oracle_stage_2_accuracy_minimum`. The analyzer was repaired,
regression-tested, and rerun without changing any model call, stored outcome,
threshold, or inference freeze. The authoritative analysis SHA256 is
`de0e304616cce1dcd09fa2440ee471adfc9b9c83fec0da38f452c0f04e92216a`.

A bounded trajectory audit found that Stage-2 parse failures were complete JSON
sets in natural numeric rather than Python lexicographic panel order. The
historical parser flags remain frozen. Under an order-insensitive sensitivity
check, T/H/V/oracle correct counts become 58/56/17/74 rather than 56/53/15/72;
H−T remains negative, repairs still do not exceed breaks, and oracle remains
below 0.95. Future set interfaces now canonicalize duplicate-free arrays, but
this forward-only repair does not authorize a rerun. All 105 RQ1 tests and
targeted Ruff checks pass after the repair.

The row sham produced Stage-1 exact-ledger agreement of 0.4556 for H and 0.0556
for V, and final agreement of 0.6556 and 0.3000. It establishes arrangement
sensitivity without beneficial accuracy.

DD-34 closes RQ1b3 and the current RQ1 visual-complementarity route. Qwen, the
locked 150-case gates, RQ1c/RQ1d, training, reserve, and heldout inference remain
unopened or blocked. The next authorized work is a separately frozen RQ2
content/encoding/arrangement protocol; no RQ2 inference is yet authorized.

## Review pause and static RQ2 handoff

DD-35 records the next protocol direction as a staged 2^4 dashboard-design
factorial, but authorizes static work only. The six RQ2 directories, frozen
non-executable YAML contract, factorial and render-plan helpers, and static
qualification artifact are present. Nine RQ2 tests, all 105 RQ1 tests, targeted
Ruff, JSON validation, and `git diff --check` pass. The RQ2 artifact remains
`passed_static_contract_only`; no RQ2 model request or efficacy experiment has
been launched. Work is paused here at the user's review boundary.
