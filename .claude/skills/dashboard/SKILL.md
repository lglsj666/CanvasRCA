---
name: dashboard
description: Develop and qualify the CanvasRCA telemetry dashboard renderer. Use when editing RQs/vlmrca/render, changing a renderer preset, reviewing visual evidence, auditing leakage, or verifying cross-arm fact equality.
---

# Dashboard renderer

Read `Codex.md` before changing the renderer. The shared implementation lives
under `RQs/vlmrca/render/`; provisional RQ-specific tooling belongs in
`RQs/<rq>/scripts/`, never in frozen `src/`.

## Contract

Keep `compile_dashboard(view, cfg) -> (png_bytes, manifest)` pure and
deterministic in its inputs. Sort iteration, seed layouts, and version every
semantic renderer change.

Label blindness is broader than removing a `ground_truth` field:

- display only opaque incident IDs and relative time;
- never render raw case IDs, dataset names, fault types, file paths, absolute
  timestamps, injection time, labels, or label-derived metadata;
- audit all OCR-visible text, prompt text, manifests, and image metadata;
- isolate any label-bearing review index from model input and perception probes.

## Review workflow

1. Render representative development cases covering sparse/all-NaN metrics,
   long labels, missing logs/traces, isolated nodes, dense topology, weak
   topology, and multiple accepted labels.
2. Open the actual PNGs with the environment's image viewer. Do not approve a
   renderer from manifests or tests alone.
3. Check legibility, clipping, collision-free service identifiers, fault-window
   alignment, missingness, edge direction, multi-hop paths, and panel-to-service
   correspondence.
4. Run deterministic re-render and leakage checks, then inspect pixel changes.
5. Record renderer version, config hash, PNG hash, manifest hash, and audit
   status in the run contract.

## Information equality

For every modality comparison, map each atomic `fact_id` to the image primitive
and to the corresponding text/structured location. After deduplicating repeated
encodings within an arm, inventories must be identical. Full visual sequences
require text/structured sequences at the same bins, precision, missingness, and
units. Concrete topology edges must appear in every compared arm; an arrow
legend alone is not an edge list.

## Acceptance

Run the relevant renderer and no-leakage tests, but treat them as necessary rather
than sufficient. A valid-looking PNG can still be blank, misleading, or
label-bearing. Before updating a golden, identify the exact target, inspect the
pixel diff, update renderer/config contracts, and record the reason. Never
silently re-record goldens.
