# RQ4.9 qualification and recovery contract

## Immutable scientific scope

The approved protocol defines 23 RCA conditions, 5,060 main positions, up to
621 ordinary QA positions, 81 QA-control positions and 90 independent repeats.
The formal scientific ceiling is 5,852 actual calls before exact-request reuse.
Three separately accounted smoke scopes allow at most 18 calls each; the
remaining 94 calls are exclusively for permissible infrastructure recovery.
The cumulative ceiling is 6,000. Committed wrong or invalid model answers are
terminal results and are never regenerated to improve a score.

`protocol_v1.json` contains the exact arm lists, comparisons and numerical
limits. `execution_v1.json` retains false defaults for CPU, smoke and formal
activation. An explicit command and source-bound credential are required.
Neither a static pass nor a CPU pass automatically starts a model.

## Source and input identity

`implementation_baseline.json` hashes the protected historical sources and
Codex.md before implementation. Static checks compare against that snapshot,
including pre-existing user edits; they do not assume a clean git checkout.
Only the new opt-in renderer operation and its three registration/build entries
are introduced. Historical rendering defaults remain unchanged.

CPU receipts use an input-compiler fingerprint. Analysis-only, gate-only or
CLI-only edits do not force screenshots to be regenerated. Every qualification
and execution credential additionally binds the complete execution fingerprint.
Actual generation identity includes prompts, pixels, original position mapping,
retention/fusion/intervention operators, model metadata, backend and decoding.
Arm names and scoring-only versions are not reasons to regenerate an answer.

Working source is copied into a versioned immutable snapshot before hard-link
deduplication. Mutable working files are never hard-linked as frozen source.
Historical baseline records are verified and retained by reference; their
labels and scores are evaluator-only and are never compiler inputs.

## CPU and visual acceptance

- Source selection is closed over each original occurrence and its dependent
  fields. Equal numerical values or equal entity IDs do not merge occurrences.
- Candidate directories and observation windows survive; all panels count
  toward 28. D14 retains at most 14 complete panels with the same protection.
- Every actual processor request respects 40,960 total context and 16,384
  retained image positions. The original 4096-square image is checked before
  any selective embedding operation. Font and stroke checks use actual scale.
- Fusion groups partition E, retain A, allocate exactly q representatives,
  and preserve representative positions. Independent small tensors verify
  FP32 means and BF16 conversion.
- Shape selection uses actual registered primitive support; endpoint priority
  precedes recomputation of error against the currently retained shape.
- Independent probability calculations verify redistribution, nonnegativity,
  mass conservation and a no-donor no-op. Native gate and two-request isolation
  have separate CPU doubles; these do not certify the real GPU backend.
- DIRECT/MARKLESS must have identical prompt, canvas, retained indices and
  panel geometry. Independent PNG comparison permits differences only inside
  registered point bounds (two pixels for raster antialiasing).
- QA answers are nonempty and recomputed independently. Both phase-comparison
  operands must be displayed. Synthetic label controls update every registered
  duplicate within the complete target source, and never receive RCA labels.
- Whole-source position swaps must fit without overlap. Inapplicable controls
  are explicitly counted, not silently replaced or recorded as zero effects.
- At most six new images are opened manually. The manual receipt lists exact
  hashes and observations; automatic audits are not called full manual review.

CPU preparation uses at most eight processes pinned to distinct physical cores.
It uses an offline model double and cannot start a server or send a request.
The three GPU scopes run only after the complete CPU, QA, runtime and visual
receipts all match the frozen execution version.

## Smoke and formal operation

Each smoke has one persisted 900-second window, including startup, submission,
commit and validation. Restarting does not reset its time or call budget.
All three fixed datasets and the longest prepared request are included across
the scopes. Passive collection is explicitly enabled in smoke so that a fixed
case outside the formal QA subset cannot accidentally bypass attention checks.

The audit examines actual submitted PNG hashes, actual retained slots, actual
SCOPE attention selection receipts, sink detection receipts, four measurement
layers and two queries, scoring, tokens and atomic commits. A wrong answer is
kept as a wrong answer. An invalid input, missing measurement or incorrect
scoring interface blocks qualification. An exhausted smoke is not reset with
the infrastructure allowance.

The final queue balances arm order by case and uses frozen hash case order.
Heavy compilation/rendering finishes before GPU operation. Eight independent
CPU preparation workers feed an eight-request vLLM engine through a bounded
RAM queue (16 ready/pending items, 24 decimal GB of ready tensors). There is no
disk prefetch buffer. This queue limit is not a project-wide memory restriction.

An atomic `completed/<key>.json` is the per-call commit boundary. Restart skips
committed units before input materialization and does not bulk-open historical
PNGs. A completed phase skips model startup. Pending retention finalization can
resume separately after completion, without regenerating model answers.

## Storage and reporting

Keep ordinary readable prompts, exact images, outputs, complete two-message
input plus assistant reply, invalid answers, scoring contexts, operation plans,
actual operator receipts and all collected attention. Preserve interrupted raw
streams if they contain unique information. Exact immutable objects are
deduplicated by verified content hashes. Caches are removed only after all
writers drain and required references verify.

The total retained footprint is at most 2,500,000 bytes per actual completed
call; references do not increase the denominator. Attention is at most
100,000 bytes per actual completed call and 65,536 bytes for any single summary.
These budgets include retained manifests, mappings and frozen source. No archive
or custom compressed object is used to meet them.

Analysis separates standard/tolerant scores, known/unknown denominators,
event/case inference, logical deployment cost/research expenditure, historical
comparisons/concurrent contrasts, and observed statements/internal reasoning.
The qualitative-review export starts explicitly unreviewed; generating a table
of answers is not itself a completed human interpretation audit.

## User-authorized performance qualification amendment — 2026-10-21

Formal execution is paused at 178 committed positions. Three newly bounded
performance scopes each use the same six conditions and three fixed smoke cases,
18 calls and 900 seconds each. Their 54 calls come from the original recovery
reserve (94 -> 40); the total ceiling stays 6,000. Correctness and the requested
20-second latency goal are separate results. New runtime source fingerprints
cannot silently inherit formal launch permission. See
`performance_revision_2026-10-21.md` and the per-scope timing reviews.


Latest performance amendment: five performance scopes now total 90 calls
transferred from the 94-call recovery reserve, leaving 4; the 6,000-call limit
remains fixed. The user changed acceptance to **all measured calls <=20 seconds
OR full inference-window GPU average >=82%**. Correctness remains separately
required. Model loading is separate; encoding, prefill, decoding, admission,
waiting and drain remain inside the utilization window. See the performance
revision document for complete scope history. Formal remains paused.
