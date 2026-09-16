# DD-RQ3-TOURNAMENT-13: full-remaining exploration and authorized reset

Date: 2026-09-13. Status: adopted; supersedes all small-inference-cohort decisions.

The user clarifies that the elimination tournament IS exploration. Applying a
small-cohort screening process before deciding whether to test a method on the
remaining population was contrary to that workflow. Round 1 did cover both
models' complete RQ480. Rounds 2–5 and 10 did not cover all remaining cases;
later extension rounds do not satisfy the requested per-method sequence.

Delete rounds 2–10 result trees, their registrations and commits, and derived
analyses/coverage. Retain round 1 bytes, its 480-case/model records, the shared
pool, canonical processed corpus, model weights and implementation. Only the
deletion inventory and protection hashes remain as the reset audit. Do not
restore deleted answers via aliases or count their successes.

Restart after round 1: Qwen 166 solved / 314 unresolved; Gemma 135 solved /
345 unresolved. Rebuild the per-dataset AC@1 completion overlay from round 1.
The unchanged target is at least 80% in EACH of the five datasets for EACH
model; stop there without an AC@5 phase or automatic training.

Each newly registered method uses exactly the complete current model-specific
unretired set, with no small inference subset. Correctness, truncation and
negative results do not trigger answer retries. CPU tests and real-image
inspections precede calls but are not inference-based screening. The register
rejects a partial cohort. Resume drains the original registered cohort even
when one model has already completed it.

Restart methods in order: native BARO metric selection, native SIRCL trace
support/confidence, native SIRCL log frequency, native SIRCL three-sigma metrics,
then observed trace-status evidence. Old extension rounds were NOT additional
methods; do not create nominal repeats of the same method to manufacture
sampling successes. Every distinct method now runs the full remaining cohort
before the next one is registered. Further complementary methods follow the
same rule until the target is genuinely met.

The user explicitly requests fresh execution of the deleted rounds. The new
version does not import any of their answers. The retained round 1 is the
baseline and remains protected. Natural input no-ops are audited separately;
they are not evidence of a changed diagnostic signal. Shared model recipes,
actual output ceiling 8192, prompt structure, anonymous candidates and private
label isolation remain unchanged. No attention or training is added.

Operational evidence is under `results/tournament_v1/reset_20260913/`.
Full-remaining configs are `configs/tournament_full_*_v3.yaml`.
