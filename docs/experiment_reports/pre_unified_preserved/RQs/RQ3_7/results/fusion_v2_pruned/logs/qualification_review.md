# RQ3.7 qualification and launch — 2026-09-28

User authorizes CPU regression, GPU smoke and, after passage, the A→B formal queue. C remains separately closed. No attention or training, no subagents. The RQ-specific primary-dataset development roster and 8192 output adapter supersede legacy generic smoke defaults.

Registration completed at cumulative 21469 historical calls; planned upper12774, shared40000 ceiling unchanged. CPU qualification started in the background with a1800-second bound; no qualification success claimed yet. GPU smokes will run sequentially after CPU and real input/image review, each≤18 initiated calls and≤600 seconds across both models. Formal authorization files will be written only after actual qualification and manual inspection.

Skills: experiment/smoke govern bounded qualification and artifacts; dashboard requires actual PNG inspection; vlm-serve preserves the nibi worktree's local recipe; devlog records this handoff. Prior static-only status is superseded by today's explicit execution instruction, not retrospectively marked runtime-qualified.
# CPU qualification repair and review

## Final qualification disposition

Formal A→B launched detached via `scripts/formal.sh`, supervisor PID15647. Checked actual A/Qwen runner PID16318, live completion submissions and three new formal output commits; formal ledger showed 3 complete/36 started at 11:35 local. This is a launch check, not completion or efficacy verification. Background queue continues after handoff. No C run requested or launched.

B passed in 269.33s, both models, 18 initiated calls and 18 complete records, no integrity errors. Read all 18 B answers; inspected actual scientific-numeral prompt lines and the unit-converted AegisLab PNG (byte→decimal kB, bar geometry retained, ratio quantities unchanged). All 36 A/B saved conversations contain their exact raw answers; saved images match commit hashes; request inspection found no opaque incident IDs, dataset names, private-label keys or local source paths. At most one image per request. Sampling variations, unsupported reasoning and single-ID Gemma answers remain raw model outcomes.

Important reuse distinction: smoke A/B intentionally have separate ledger scopes (18+18 calls); formal A/B share `rq37_formal`, so identical/no-op requests can reuse formal answers while REPEAT remains distinct. No smoke result is promoted into formal efficacy results. Final cumulative calls at qualification end: 21505 (=21469 historical +36). A→B formal authorized by current user request and completed manual review. C remains closed. `authorizations/A.json` and `B.json` bind the current contract. Formal resume uses small done/fail flags; no completed-case preparation rebuild or mass revalidation.

## Concurrent activity-write repair and A smoke

Initial A runner failed when simultaneous activity updates reused the inherited `.partial` filename. Exactly two model requests had completed; their artifacts remain. RQ37 now uses existing project `atomic_write` (unique mkstemp, fsync, replace) and has a 100-write/16-thread regression. Source changes are strictly operational; no input, glyph, scoring or model recipe changes. The original failure report remains at `pre_run_revisions/activity_race/smoke_A_failure.json`.

Repaired CPU: 17 tests and all 63 real targets passed in 17.26s. A resumed within its ORIGINAL 600s window and same SQLite scope; completed targets skipped, original 18-call ceiling never reset. Explicit repair provenance is `smokes/A_repair.json`. Final A: passed, 18 calls/18 complete records, both models, 529.37s including failure/repair/reload time; no integrity errors. Read all 18 raw answers, cost records and inspected their input/PNG construction. Observed reversed relations, unsupported causal statements, and entity-type errors in some reasons are model behavior, not a qualification failure. Gemma often returns one ID, which is allowed by frozen answer/scoring contracts. No accuracy-driven modifications.

Current contract: `1a8d2032bb94718e3a23b62d1a62e331b0b1b671410312b78e22b1dc756997a2`. B smoke now pending; formal A→B still waits for B qualification and review.

- 2026-09-28: first real regression failed before any GPU calls because parent display means include decimal k/M/G suffixes. Failed registration and CPU report preserved in `pre_run_revisions/cpu_initial/`.
- Fixed suffix parsing without invented precision; added exact OTel gauge definitions from pinned v0.110.0 upstream metadata in an RQ37-only overlay. Original selected facts and old RQs unchanged. Unknown units stay unknown; unit intervention can legitimately be inapplicable.
- Repaired CPU: 16 tests passed; 63 real compile targets across aiops2022/aiops2025/aegislab passed in 20.32s; no design-infeasible inputs. Both model processors used for capacity checks. Ruff and shell syntax checks pass.
- Inspected full AegisLab LOCAL_LINK and AIOPS2022 REMOTE_ID PNGs: all entity panels and full G ledger present, bars vs labeled readings obey role whitelist, ownership dashes distinct from system arrows, no title clipping. Large white slots are frozen across factorial cells by design. Inspected actual T_MATCH/LOCAL_LINK prompt sections: candidates remain in text, M/R/L retained, G represented in its registered carrier, no labels or identifying paths added.
- Archive-only TPV unavailable for two CPU cases: no baseline generation fallback; corresponding comparisons remain unavailable rather than scored zero. B3 references available. This does not block the five-arm within-case factorial.
- GPU smoke A/B still pending; C not authorized. No efficacy claims.
