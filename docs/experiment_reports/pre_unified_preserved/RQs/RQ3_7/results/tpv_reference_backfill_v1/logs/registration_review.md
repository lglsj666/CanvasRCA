# 2026-09-28 — Authorized 120-call TPV supplement

## Scope and status

User authorized completing the 120 unavailable TPV reference slots associated
with RQ3.5 screen60: AIOPS-2022/2025/AegisLab 20 cases each, both frozen models.
The three historical request timeouts are explicitly excluded. Current A/B
inference continues without source/config/registration modification. The new
supplement is a continuation of the existing TPV condition, not a new design.

## Checks and qualification basis

- AST and Ruff passed for the additive runner. The original A/B contract still
  matches `1a8d2032bb94718e3a23b62d1a62e331b0b1b671410312b78e22b1dc756997a2`.
- Three real screen cases, one per primary dataset, were compiled for both
  models (six requests), without GPU/LLM calls. The exact corrected TPV parts
  matched the existing RQ3.6 recipe; source PNG bytes, numbers, candidate order,
  evidence and instructions were unchanged. Both tokenizers/processors fit.
- Initial comparison also compared obsolete attention metadata absent from
  persisted prompts. This CPU-only false mismatch was fixed by comparing and
  sending model-visible text and original PNG bytes only; no attention is
  collected. The pre-call script registration was archived before resealing.
- Existing RQ3.6 corrected-TPV implementation and current RQ3.7 client/runtime
  qualifications are inherited. No new smoke or extra generation is claimed.
  Remaining cases must pass the same exact-input CPU checks before submission.

## Decisions and operational behavior

- A separately versioned runner under `scripts/tpv_backfill/` does not change
  any file in the current A/B runtime hash set. It blocks on A/B's queue lock,
  with no polling, server launch or GPU residency while waiting.
- Normal A/B completion plus terminal flags is required. If the predecessor
  pauses/fails, the supplement stops rather than restarting it or claiming its
  GPU. It uses the existing owned-server launcher with only the child CLI
  module redirected to the additive runner. Qwen and Gemma run sequentially.
- A single shared cumulative SQLite register still enforces 40,000 calls.
  The supplement has its own 120-attempt ceiling including interrupted and
  failed requests. No timeout retry or automatic extra budget. Completed/fail
  flags skip compilation and inference on resume.
- Only after all 120 targets terminate and writers drain are original A
  reference-unavailable placeholders replaced by references to the supplement.
  Prior flags are archived under `original_reference_flags/`. Old experimental
  inputs, responses and scores are never overwritten. A partial publication
  can resume idempotently. Non-timeout infrastructure errors stop publication.

## Budget

Added maximum: **120**, comprising 60 Qwen + 60 Gemma requests. A/B formal upper
bound 3420 → 3540; all planned RQ3.7 stages plus qualification 12774 → 12894.
At registration/check time the supplement has made **zero** model calls.

## Run/resume and artifacts

From `/home/lglsj/CanvasRCA_nibi`, source `scripts/env_local.sh`, then execute:

```bash
"$CANVASRCA_PYTHON" -m RQs.RQ3_7.scripts.tpv_backfill.main queue
```

Run detached for normal operation. State: `queue_status.json`; progress:
`progress/<model>.json`; launch output: `logs/supervisor.log`. Full prompts,
PNG, conversations, raw responses, costs and scores are under
`stages/formal_A_tpv_backfill/<model>/`. `registration.json` freezes targets,
authorization, additive source hash and parent contract. No experiment C run
is authorized by this supplement.
