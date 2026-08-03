---
name: smoke
description: Run or debug the end-to-end VLM-RCA pipeline (case → dashboard → VLM → parse → score) and check the M1 gates. Use when verifying the pipeline still works after a change, onboarding a new model or dataset, or diagnosing why an experiment returns zero/unparseable answers.
---

# Smoke test

The fastest way to prove the whole chain is intact. Run it after any change to
the renderer, prompt, client, or scoring.

```bash
source scripts/env.sh
python scripts/smoke_e2e.py --model mock --n 5                 # no credentials, no cost
python scripts/smoke_e2e.py --model claude-sonnet-5 --n 20     # real model
```

`--model mock` is the debugging default: it exercises rendering, prompt
assembly, parsing, scoring and trajectory writing with no network and no spend.
Use it to isolate pipeline bugs from model behaviour.

## M1 gates

| Gate | Threshold | Meaning |
|---|---|---|
| `parse_rate` | ≥ 0.95 | at most 1 unparseable answer in 20 |
| `mrr` | ≥ 0.35 | random top-5 over 10 services is ≈ 0.21 |
| render time | < 5 s/case | keeps the RQ1 grid affordable |
| perception probe | ≥ 90% | model can transcribe panel titles (render-reviewer agent) |

Status: passed on 2026-07-22 with `claude-opus-4-7` on 20 RE2-OB cases —
MRR 1.000, parse 1.000, 4.4k tokens/case, 6.9 s/case.

**Read the RE2-OB result carefully.** It is the easiest dataset; the prior
text-based project already scored 0.976–0.994 there, so 1.000 confirms the
pipeline works and proves nothing about the method. Real signal comes from
AegisLab (text SOTA 0.679) and AIOPS-2025 (0.390).

## Debug order

Work outward from the data; most failures are in the first two steps.

1. **Render** — `python scripts/render_gallery.py --dataset <ds> --n 3` and look
   at the PNG. Blank or garbled panels explain everything downstream.
2. **Prompt** — check `prompt_chars` in the trajectory. Near-zero means the
   evidence text failed to build; huge means something is dumping raw telemetry.
3. **Model call** — a per-turn `error` field in the trajectory means the call
   itself failed (credentials, model id, image size), not a wrong answer.
   Credentials come from the upstream repo's `.env` via `vlm.configs.load_env`.
4. **Parse** — `parse_ok=false` with non-empty `response` means the model
   answered in prose. Check that `ANSWER_FORMAT` is still the last prompt part.
5. **Score** — a correct-looking prediction scoring 0 usually means name
   normalisation: `score_prediction` applies service-level leniency and
   multi-root-cause acceptance, so check `extra.rank` and `accepted`.

## Outputs

```
results/<experiment>/
  trajectories/<experiment>__<model>.jsonl   # header line + one line per case
  renders/<case_id>__<config>.png            # gitignored
  summary.json                               # point-estimate metrics
```

Trajectory schema matches the upstream project's `configs/metrics_spec.yaml`
plus an `images` field, so upstream analysis scripts read these unchanged.
