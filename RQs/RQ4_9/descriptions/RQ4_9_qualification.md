# Qualification and failure policy

Order: static → complete CPU and numerical/runtime regressions → at most six newly opened images → three independent smokes → formal freeze/run. No receipt from another version or phase constitutes qualification for this phase.

Static checks cover the module layout, 7,500 functional-line limit, 23 conditions, 6,000-call arithmetic, TypeScript, defined names, scorer imports and historical-source protection. CPU covers source closure, original values, candidate/window preservation, every condition's actual processor count, A/E support and point-only controls. Runtime checks cover independent operator arithmetic, native gates/positions, batch isolation and atomic resume. Visual review records exact image hashes and findings.

Each smoke has a single 900-second window and at most 18 actual attempts. Restarting does not reset its budget. All wrong/invalid completed answers are retained and scored; software errors are repaired without selecting methods using smoke rankings. Unknown infrastructure outcomes stay unknown. A semantic, capacity or operator failure blocks launch; it is not converted into a no-op or a cancelled control.

All actually collected attention is retained with layer/query coverage. Two observed queries per layer do not represent the complete decoding process. Results and input dependencies are direct-readable and deduplicated; the limits remain 25 decimal GB per 10,000 actual calls and 1 GB for attention.


## Completed CPU qualification and smoke repairs — 2026-10-21

All 220 cases (60/60/100) passed the full input qualification. All 23 conditions
have frozen requests. The fixed QA subset has 27 answerable cases and all 23
conditions. Target isolation and position exchange apply to all 27; statistic
label exchange applies to 25. The two inapplicable statistic exchanges remain
registered N/A. This gives 5,850 formal positions before exact-request reuse,
within the registered maximum of 5,852. Sixteen unit regressions and 85 actual
CPU processor/MRoPE checks passed. Manual review stopped at six opened images;
one earlier image is superseded after fixing the legend collision.

Repairs preserved original failures and used affected checks plus explicit
compatibility proofs for unchanged inputs:

- D14 packing now accommodates rounded column boundaries using existing margin.
  Whole-card dimensions, font floors and canvas limits are unchanged.
- Provenance-declared empty relationship panels are accepted only with an
  independently verified empty edge-set hash. Nonempty or conflicting sources fail.
- Source-caption packing preserves successful layouts, using bounded deterministic
  whole-card bin search only when greedy packing fails. Six automatic PNG witnesses
  verify byte-identical unaffected LOCAL/KEY examples.
- One fixed QA case lacks pairs/traces but has visible metric evidence. Four metric
  questions replace an empty QA input without changing the selected case. The
  independent oracle audit includes zero values, exact display labels and operands.
- Comparative prose, invalid identifiers and minor formatting are handled by an
  oracle-blind receiver. The metric-unit vocabulary was narrowed to exact whole-answer
  aliases after a counterexample showed that a contradictory unit phrase could be
  accepted. Correct numeric/ID answers in other questions remain scoreable.
- The first operator smoke attempt exposed an RPC tensor decoding error before
  generation. The worker now uses decoded tensors before gather; an independent
  wire round-trip regression covers the repair.
- A later sink attempt spent excessive CPU time rebuilding integer sets. These pure
  membership sets are now constructed once. The four redistribution tensors are
  exactly equal to the earlier arithmetic; indices, thresholds and generation
  identity are unchanged. The interrupted attempt remains in the ledger.
- Smoke review now measures the shared window from its original opening through
  the atomic phase-complete marker, including repairs and restarts. No clock or
  attempt budget was reset.

The operator smoke completed 12 positions using 14 attempts (including the two
failed/interrupted attempts), within 852.15 seconds of its shared window. The
organization/hybrid smoke completed 12 positions in 169.09 seconds. Both reviews
passed. Wrong model rankings were retained and were not used to tune methods.
QA smoke is the final pending qualification at the time of this entry.


### Final QA receiver repair and review

QA smoke completed 11/11 calls in 339.00 seconds. Raw-answer review found one
truncated answer whose first five questions had explicit `Answer:` lines;
the earlier fallback incorrectly treated question headings as answer values.
The v2 receiver separates headings from explicit section answers, preserves
completed answers before truncation, rejects conflicting section/summary answers,
and does not extract speculative values from reasoning. Independent positive,
negative and conflict tests passed (16 tests total). The actual 11 responses
were rescored offline: one changes from 0/6 to 5/6; unfinished sixth answers
remain wrong. Another truncated response contains no explicit answers and stays
zero. Original records and scores are preserved under the repair snapshot,
linked from each revised record. No model response, prompt, oracle, pixel,
operator, threshold or ranking was changed or regenerated.

Source compatibility is recorded in `cpu/qa_section_compatibility.json`.
Only the QA extractor and scoring-version tag changed. All frozen model inputs
and GPU arithmetic retain their generation identity. The three reviews use
original shared-window completion times; no timer reset or extra smoke occurred.
All three reviews passed. Historical QA was rescored separately with the v2
receiver: 939 existing responses, zero unsupported; 141 no-generation positions
remain distinct workflow failures. Original historical artifacts remain unchanged.
