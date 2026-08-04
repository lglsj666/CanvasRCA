---
name: smoke
description: Run or debug the CanvasRCA end-to-end pipeline and its partition-aware qualification. Use before a full inference or training run, after compiler/client/scorer changes, or when diagnosing infrastructure and artifact failures.
---

# Smoke qualification

Read `Codex.md` and the target RQ contract. A mock run is useful for local unit
debugging but never replaces the registered real-case qualification.

Do not reuse the current `scripts/smoke_e2e.py --rq0` route to qualify a new RQ;
it is tied to the completed RQ0 contract. Likewise, the generic legacy M1 path
with accuracy gates is not a Rule-16 qualification. Add and register the target
RQ's smoke integration before opening its full run.

## Registered three-case smoke

Select exactly one authorized real case from each dataset:

- `re2_ob`;
- `aiops2022`;
- `aiops2025`.

Use `validation` for inference/evaluator smoke and `train` for optimizer/training
smoke. Use the preregistered seed and record opaque IDs plus roster/split hashes.
Do not use AegisLab, RE2-TT, synthetic cases, test, heldout, unused, or `.invalid`
cases. RE2-TT remains embargoed for final OOD evaluation.

Run through the same compiler, renderer, `RQs/vlmrca/vlm/client.py`, asynchronous
writer, evaluator, artifact inventory, verifier, and full 32768/16384 limits as
the planned run. Freeze code, model/tokenizer or adapter, configuration, prompt,
evidence, renderer, scorer, and partition hashes before the first call or
optimizer step.

## Passage criteria

Require protocol, numerical, artifact, and infrastructure integrity with zero
infrastructure failures. Do not use root-cause accuracy, MRR, reward, parse
acceptance, or the magnitude of finite loss to decide passage. Still record
parse failures, truncations, invalid output, and finite metrics as diagnostics.

Store the smoke in an isolated registered root under
`RQs/<rq>/results/<smoke-experiment>/` and exclude it from formal metrics and
model selection. If it fails, preserve its artifacts and diagnose from data to
render, prompt, backend, parser, scorer, writer, and verifier in that order.
