---
name: smoke
description: Run or debug the CanvasRCA end-to-end pipeline and its partition-aware qualification. Use before a full inference or training run, after compiler/client/scorer changes, or when diagnosing infrastructure and artifact failures.
---

# Smoke qualification

Read `Codex.md` and the target RQ contract. A mock run is useful for local unit
debugging but never replaces the registered real-case qualification.

Use the target RQ's `tests.py` definition and `.sh` trigger. The shared bounded
supervisor is `src/cli/smoke_e2e.py`; it enforces time but must not invent or
expand RQ calls.

## Registered three-case smoke

Select exactly one authorized real case from each dataset:

- `re2_ob`;
- `aiops2022`;
- `aiops2025`.

Use `validation` for inference/evaluator smoke and `train` for optimizer/training
smoke. Use the preregistered seed and record opaque IDs plus roster/split hashes.
Do not use AegisLab, RE2-TT, synthetic cases, test, heldout, unused, or `.invalid`
cases. RE2-TT remains embargoed for final OOD evaluation.

Run through the same compiler, renderer, `src/vlmrca/vlm/client.py`, asynchronous
writer, evaluator, artifact inventory, verifier, and full 40960/16384 limits as
the planned run. Freeze code, model/tokenizer or adapter, configuration, prompt,
evidence, renderer, scorer, and partition hashes before the first call or
optimizer step.

The two models share at most 18 calls across all stages, cases, conditions,
retries, and processes. Model phases run sequentially, never concurrently. The
complete logical smoke shares one 600-second wall-clock budget, including model
startup and switching. Use a simple run-local process clock/state; do not
modify WSL or host clock configuration or build precision timing infrastructure.
Exit as soon as the smoke completes. If the registered timeout is the only
error, preserve completed artifacts and treat the bounded smoke as passed.
Experimental gates are capped at 36
aggregate calls and 1200 seconds; on timeout, score only cases with their
complete required condition/stage set.

## Passage criteria

Require protocol, numerical, artifact, and infrastructure integrity with zero
infrastructure failures. Do not use root-cause accuracy, MRR, reward, parse
acceptance, or the magnitude of finite loss to decide passage. Still record
parse failures, truncations, invalid output, and finite metrics as diagnostics.

Store the smoke in an isolated registered root under
`RQs/<rq>/results/<smoke-experiment>/` and exclude it from formal metrics and
model selection. If it fails, preserve its artifacts and diagnose from data to
render, prompt, backend, parser, scorer, writer, and verifier in that order.

After every smoke attempt, inspect the persisted summary and verifier output
and every completed trajectory/conversation artifact, including the
model-visible prompt, raw response, parse/truncation state and accounting. Write
the review beneath the smoke root. Record hidden issues. If an issue is safely
fixable within scope, make a forward-versioned repair, refresh affected hashes,
verify and continue; stop only for a material issue that remains unresolved
after reasonable in-scope diagnosis and repair, and record that blocker.
