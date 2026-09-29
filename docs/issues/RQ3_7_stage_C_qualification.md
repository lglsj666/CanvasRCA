# RQ3.7 C qualification and cold preparation — 2026-09-28

## Scope

User authorizes C after A/B. Frozen scientific contract remains
`1a8d2032bb94718e3a23b62d1a62e331b0b1b671410312b78e22b1dc756997a2`.
No new model call preceded the cold-path CPU check. A/B and the 120 TPV
supplement remain immutable, including failures.

## Confirmed cold-context failure

The five-case expansion-path CPU check failed in 22.68 seconds with
`KeyError: selections`. The RQ37 cold fallback called `prepare_public_context`
then `prepare_integrated`, but the latter also consumes the RQ33
`selections['2048:more']['items']` intermediate. The A/B path reused complete
RQ34 contexts and therefore did not exercise the missing intermediate.

The stage-C preparation helper now explicitly runs the existing
`choose_parent_tail` in its registered cumulative 1024→2048 order before
`prepare_integrated`, writes the complete public context and isolated private
scoring record, then commits the preparation marker. No unrelated historical
selection experiments are computed. This is completion of the existing parent
recipe, not a changed selection rule, window, budget, renderer or model input.
The frozen compiler subsequently reads that complete local context. Full C
must run the additive preparation step before the existing formal entry point;
do not bypass it on a new cold roster. Compatible prepared and terminal units
are skipped by their small markers.

Failed CPU report/log preserved as
`RQs/RQ3_7/results/fusion_v2_pruned/logs/C_boundary_missing_intermediate.*`.
The helper is independently hashed under `scripts/stage_c/operations.py`;
no frozen RQ3.7 or predecessor source is edited. Further qualification status
will be appended after actual checks, not inferred from this correction.

## CPU boundary result

The repaired CPU-only check passed in 104.72 seconds: one fixed-hash cold test
case per primary dataset plus one eval case per RE2 dataset, each compiled into
all five arms for both models (50 requests, zero model calls). Both real
processors checked context capacity. Actual RE2-OB/TT LOCAL_LINK PNGs were
viewed: entity ownership, directed edges, full ledgers and isolated entities
are visible; known unknown-unit quantities remain readings, not invented bars.
No label or accuracy inspection was used to change the method. A separate C
smoke is now required; no GPU qualification is inferred from CPU success.

## GPU qualification and activation

C's single logical smoke passed all 18 calls in 260.863 seconds, both models,
with no artifact/infra/parse/truncation failures. All eighteen input identities
match their original A counterparts; requests are not retuned. Full saved
response/conversation review and representative actual PNG review completed;
`results/fusion_v2_pruned/smokes/C_manual_review.md` records the observed model
reasoning errors without treating them as pipeline defects. Total cumulative
initiated calls are now 24661.

Formal C activation uses `RQs/RQ3_7/scripts/stage_c/run.sh`: prepare only missing
public contexts with eight core-pinned workers, then unchanged formal C Qwen
and Gemma sequentially. No GPU service is resident during cold preparation.
Resume the same command; it trusts terminal flags and compatible cached views.
1800 development logical units already reference A, leaving at most 6600 new
formal calls. This does not activate unaudited fresh events.

## Preparation interruption: nested WiredTiger log clock

The first full C preparation stopped at 237/655 in 2359.43 seconds. No C
formal GPU calls had started. The top-level queue still said `preparing` after
the child exited; this was stale monitoring state, not an active process.
The CPU frontier reproduction identified `INC-12D885A5B485` (RE2-TT); the other
seven in-flight cases passed and their caches were retained.

The offending L observation is a MongoDB WiredTiger checkpoint message with
an embedded `[epoch_seconds:microseconds][thread]` prefix. Outer `$date` had
been scrubbed, but numeric template slot `{num1}` still held epoch values.
The source meaning is explicit in WiredTiger's
[mongodb-7.0 `__eventv` implementation](https://raw.githubusercontent.com/wiredtiger/wiredtiger/mongodb-7.0/src/support/err.c)
(epoch seconds and nanoseconds divided by 1000). A separate CPU-only actual
ALL_ID build also contained it, although the first failure was in an inherited
P/H preflight. Therefore skipping that preflight or disabling the guard would
not solve this leak. No affected formal model result was created.

RQ37's additive `clock_projection.py` now translates the known prefix's seconds
min/median/max by one common public log-clock origin per case, preserving
cross-entity and before/after differences. Per-component units are explicit;
microsecond statistics remain separate (not falsely paired with second stats).
Non-clock values, counts, templates, IDs and windows are unchanged. The origin
is recorded only in CPU diagnostics, never in model input. Unknown clock
formats, nonfinite/invalid components and nonzero transaction timestamps still
fail closed. No source-data, parent renderer, shared client or model change.
See DD-RQ37-4 for the forward projection amendment and exact hashes in
`results/fusion_v2_pruned/stage_c_clock_repair.json`.

Validation: Ruff, Python AST and shell syntax passed; eight focused CPU tests
passed. The actual failed case compiled all five C arms for both model
processors in 77.59 seconds (10 requests, **zero model calls**). Its 24 matching
log observations have safe projections; ranking axes and actual selected packs
are identical before/after repair. All ten requests pass clock/context checks;
the eight augmented requests carry corrected log values and the two TPV
requests do not contain that appendix. The actual LOCAL_LINK PNG was inspected:
the original numeric panels, isolated entities, typed relationship and full
ledger remain present; unknown physical units remain labeled readings.

A targeted impact check of all 430 small public views under the current frozen
contract found no remaining absolute-clock guard failures; the repaired case
is the only view containing this WiredTiger message. This was a one-off bug
impact audit, not new restart verification. Existing 180 development views and
249 previously successful cold contexts remain untouched; one failed context
is now complete. The already-passed C smoke (18 calls) remains unchanged; this
session generated no additional GPU qualification calls and does not claim
live testing of the newly projected case.

The helper now records the failed case/dataset and exact public offending line,
archives prior preparation reports before resume, and updates top-level state
to `failed` on a preparation exception. Actual compiled inputs also pass the
clock guard. Resume skips all 250 completed cold contexts and 1800 terminal
aliases, leaving 410 cold cases before the unchanged Qwen→Gemma formal queue.
