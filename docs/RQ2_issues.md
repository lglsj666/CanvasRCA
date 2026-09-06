# RQ2 issue register

This document records issues observed during the active RQ2 RCA-only formal
run. It includes infrastructure, persistence, prompt, renderer, scoring, and
artifact-integrity problems, including non-fatal warnings. Ordinary model
mistakes are not implementation defects, but are noted when a repeated pattern
could indicate a protocol problem.

## Active run

- Run lineage: `rq2_formal_v1_20260902`
- Active tasks: one-stage RCA only
- Abandoned task: packed QA/perception; not scheduled
- Monitoring: progress/error review every 15 minutes and one complete,
  randomly selected new case audit every 45 minutes

## Open issues

No unresolved issue is present at the 2026-09-03 resume boundary. Earlier
repaired or archived defects remain documented in their original devlogs and
invalid-artifact manifests; they are not silently reclassified here.

## Observed operational warnings

### 2026-09-03 — Non-persistent launcher attempt

The first background launch was attached to a short-lived tool shell and was
terminated when that shell closed. It initiated no accepted RCA request and
created no trajectory. RQ2 was immediately resumed through a persistent local
execution session with the same run ID; content-addressed resume retained the
existing valid records. This is an operational launch warning, not an input,
renderer, prompt, scorer, or result-validity defect.

### 2026-09-03 — Two inherited tokenizer-preflight error targets remain visible

At the first 15-minute check, Qwen development contained two terminal files
from 2026-09-02 (`INC-331437929E47`, designs D034 and D035) with
`RQ2Error: live tokenizer preflight failed`. They predate the current resume;
no matching new failure appeared in the live vLLM log, recent requests return
HTTP 200, and no output truncation was observed. The content-addressed runner
skips only `complete` targets, so these two targets remain eligible for normal
retry when their case is reached. Their final status and the registered 5%
infrastructure ceiling will be assessed after the phase drains; no protocol or
input is changed from this partial observation.

### 2026-09-03 — One Qwen request timeout during development resume

At 01:18, `INC-C1BAEE5AC440 / D019` ended with
`VLMError: qwen3.8-27b failed after 1 attempts: timed out`. The server remained
healthy, surrounding requests returned HTTP 200, GPU work continued, and no
engine crash, context overflow, or output truncation accompanied it. At the
next check this was one new timeout beside roughly 1,978 completed targets
(about 0.05%), far below the registered 5% whole-case infrastructure ceiling.
The failed record is preserved. No prompt, renderer, scheduler, timeout, or
model configuration is changed from this partial observation; final exclusion
status is evaluated only after the phase completes.

### 2026-09-03 — Three additional isolated Qwen request timeouts

Three later development targets ended at the registered 1,800-second client
timeout: `INC-A2F0E757DD2A / D022`, `INC-EAA097A406D6 / D022`, and
`INC-FFA0A74A0439 / D022`. The server remained responsive around the failures
and other designs continued to complete. At the pause boundary D022 contained
57 complete targets and three timeouts, so its observed request-error fraction
was exactly 5%; the full model-level whole-case exclusion rate is not evaluated
until the phase drains. The records are preserved and remain eligible for the
normal content-addressed resume policy. No timeout, prompt, renderer, sampling,
or model setting was changed.

### 2026-09-03 — Render-manifest primitive coordinates use the logical grid

The first scheduled 45-minute manual audit inspected
`INC-9C8982A9736C / D026`. Its trajectory, complete conversation, raw response,
RCA parse, token accounting, attention capture, and rendered PNG were intact.
The dashboard did not draw topology content into the neighbouring metric card.
An apparent overflow in the manifest was traced to mixed coordinate metadata:
after raster resizing, card and attention-region boxes are expressed in final
image pixels, while nested `primitive_geometry` remains in the renderer's
logical pre-resize coordinate system. RQ2's current attention aggregation uses
the correctly scaled card/region boxes, not `primitive_geometry`; therefore the
model input, RCA score, and recorded region attention are unaffected.

The hard-coded `clipping_audit: passed` field consequently does not independently
establish primitive-level clipping and must not be cited as such. This is a
non-fatal audit-metadata limitation for the active frozen run. It will be fixed
and tested after the current RQ2 formal run, rather than changing renderer bytes
mid-experiment. The original image and all manifests remain unchanged for
reproducibility.

### 2026-09-03 — Manual diagnostic pause required a second termination signal

The formal process was deliberately interrupted for the render audit above.
The first terminal interrupt stopped active inference work but left the parent
process group waiting with no healthy API endpoint. The exact process group was
then terminated cleanly before resume. No new accepted request occurred during
that interval. Existing complete and error artifacts remain content-addressed
and resumable; this was an operational lifecycle issue, not a scientific input
change.

### 2026-09-03 — Three current development infrastructure-error artifacts

At the second 15-minute check the resumed Qwen development run contained three
non-complete targets among 2,546 persisted targets (about 0.12%):

- `INC-97B043342751 / D041`: selected evidence cards could not be packed without
  overlap.
- `INC-385F3FDBBD1F / D036`: selected evidence cards could not be packed without
  overlap.
- `INC-34753C03D9F6 / D036`: live tokenizer preflight failed.

The packing errors are deterministic renderer/program feasibility failures for
those case/design pairs, not model mistakes. Their observed rate is currently
far below 5%, the run remains live and healthy, and no completed target is
affected. They are preserved and will be re-counted by design and case after
the development phase drains. A systematic design-cell failure or a final
whole-case exclusion above the registered ceiling would require remediation;
these isolated observations do not yet justify changing the frozen design
mid-run.

At Qwen phase completion the seven errors covered six distinct cases, which is
temporarily 10% of the 60-case paired development roster even though the
target-level error rate is only 0.24%. To prevent an incomplete partial phase
from entering `D*` selection, the formal parent scheduler is intentionally held
after the already-running Gemma child finishes. The Qwen phase will then be
resumed once with identical bytes and the same run ID; content-addressed resume
will skip all 2,873 complete targets and retry only the seven errors. No
completed model call is repeated and no scientific configuration changes. If
the five transient timeout/preflight targets complete, the two deterministic
packing cases leave 2/60 (3.3%) whole-case exclusions, within the registered
ceiling, before design selection proceeds.

The bounded resume completed as intended: all five transient Qwen failures
were replaced by complete, hash-valid records. Both Qwen and Gemma now contain
2,878 complete targets and the same two deterministic packing failures, so the
paired development exclusion is exactly 2/60 cases (3.3%). The parent scheduler
was released only after this symmetric, below-threshold state was verified.

### 2026-09-03 — One isolated Qwen timeout in independent design evaluation

At 886 persisted independent-design targets, `INC-1CFF421E24B / D020`
reached the registered 1,800-second client timeout. The other 885 targets were
complete, the API and GPU queues remained healthy, and the contemporaneous
manual audit found no truncation, schema, prompt, renderer, attention, or
persistence defect. The timeout record remains eligible for a bounded
same-input retry before the independent analysis is finalized.

### 2026-09-03 — Severe card-local text overlap in D031; formal run paused

The next 45-minute independent audit inspected
`INC-1E7AE92CAA11 / D031`. Unlike the earlier D026 metadata-only finding, the
original 4,401×1,776 PNG itself contains real overlap: the trace card's count
and exclusive-p95 columns are drawn on top of each other, with several values
and `Δlog2` labels no longer separable. The current hard-coded
`clipping_audit: passed` field did not detect this. D031 had been selected as
development `D*`, so treating these inputs as qualified would directly threaten
the design-selection and downstream-transfer conclusions.

The parent scheduler was already held before independent analysis. The active
Qwen child was then stopped after completed artifacts drained; no Gemma
independent call or content-budget call had begun. Existing independent records
are retained only as an audit source until renderer/design validity is
re-established. The affected scope must be determined across every selected
design, not inferred from the single sampled image. Only renderer/layout and
clipping-validation defects may be changed; the evidence packet, prompt,
scorer, model configuration, roster, and scientific design factors remain
frozen.

At this pause, Qwen independent also had 24 infrastructure-error artifacts:
13 request timeouts and 11 deterministic packing failures concentrated in
D036/D041. The latter confirms that the current greedy first-fit packer can
reject geometrically feasible card sets. These errors and the visual overlap
will be addressed together before any formal resume.

### 2026-09-03 — Resolution: lossless renderer successor; affected attempt archived

The defect was reproduced from the native 4,401×1,776 PNG rather than from a
scaled viewer. Two independent implementation faults were repaired:

- Trace values no longer share fixed fractional columns when their measured
  glyph widths do not fit. Narrow trace cards switch deterministically to a
  stacked row containing entity/operation, count change, exclusive-p95 change,
  and the baseline/fault visual mark.
- Greedy first-fit packing now has a bounded deterministic backtracking
  fallback. The previously failing D036 and D041 case/card sets pack without
  changing evidence selection or any model setting.

The repair also replaced the hard-coded clipping verdict with checks over the
final raster-coordinate primitive geometry, fixed raster scaling of nested
geometry, made topology edge tables adapt their columns and fonts to the
registered silhouette, and made metric/log labels fit or fail closed rather
than silently overlap or truncate.

Validation after the repair comprised 33/33 passing RQ2 CPU/static tests and
an exhaustive four-worker render of every one of the 48 designs for all 199
prepared development and independent cases: 9,552 dashboards, zero packing,
clipping, card-overflow, or overlap failures. The aggregate audit digest is
`296a10443da9ad24c620c3f8a68c1829a23ca2e1cefe456760e72141c4b4ede8`.
Nine native-resolution dashboards (three datasets × D031/D036/D041) were also
inspected manually; no remaining cross-column, card-local, title-marker, log,
or edge-ledger overlap was found.

Because D031 was the selected D* and its model-visible pixels were defective,
the entire `rq2_formal_v1_20260902_design_development` selection and the partial
`rq2_formal_v1_20260902_independent` phase are archived as invalid audit
artifacts. Their files are preserved and explicitly marked with
`attempt_status.json`; they are not inputs to any scientific result. The
canonical prepared evidence is unaffected and may be reused because neither
the evidence compiler nor its public/private artifacts changed. The successor
uses a new result ID and protocol revision, reselects D* from development, and
must pass a bounded Rule-16 smoke before formal inference resumes.

### 2026-09-03 — Stale shared-smoke preparation omitted dense top-24 packet

The first successor `exp_content_budget_twins` smoke completed 17 of 18 units,
but the Gemma `DENSE_M24` text unit failed before a model call because the old
`rq2_smoke_shared_prepared_v5` validation artifacts predated the registered
`dense_packet`. This was a smoke-fixture compatibility defect, not a model or
formal-preparation defect: all development, independent, and downstream formal
prepared cases already contain their validated top-24 packet.

The default shared smoke-preparation ID was versioned to
`rq2_smoke_shared_prepared_v9`, and all three validation cases were freshly
prepared through the same canonical compiler. The replacement content smoke
then completed 18/18 requests with zero infrastructure or parse errors. The
equal-fact smoke passed 8/8, and downstream transfer passed 18/18. Manual review
of conversations, raw responses, dashboard images, attention artifacts, token
accounting, and the dense top-24 text projection found no remaining protocol or
representation defect. The failed predecessor smoke remains an audit artifact
and is not a qualification result.

### 2026-09-03 — Two isolated D003 development request timeouts

During the Qwen3.8 development run of the lossless-renderer successor,
`INC-6C8EA77140FF / D003` and `INC-E74124445490 / D003` reached the registered
1,800-second request timeout and were preserved as `infrastructure_error`
records. This was not an input-length or output-truncation event: the other 58
D003 requests completed normally, with a mean wall time of about 149 seconds,
and every D002 and D004 request completed. D003 therefore had 58/60 successful
units (96.7%); at discovery time the whole run had 2 errors among 765 persisted
units (0.27%), affecting 2/60 development cases (3.33%). Both rates remain below
the registered 5% infrastructure-exclusion ceiling.

The failures are retained rather than silently replaced. No prompt, renderer,
evidence, scheduler, or inference setting was changed, and no nonessential
rerun was initiated. Monitoring will check whether later cells exhibit a
similar concentration; a sustained or above-threshold pattern would require a
separate validity decision.

At the next scheduled check, two additional timeouts appeared in D006 on two
different cases. The target-level rate remained low (4/959, 0.42%), but the
four affected cases were distinct, making the whole-case rate 4/60 (6.67%) and
therefore above the registered 5% limit. The parent formal orchestrator was
paused with `SIGSTOP` while its Qwen child continued normally, preventing D*
selection or Gemma launch from using an incomplete development matrix. After
the Qwen pass drains, the four failure records will be archived and only
non-complete units will be retried through the existing resume semantics; all
completed units will remain byte-for-byte untouched. This is a necessary
infrastructure recovery, not a model-result retry or scientific protocol
change.

The timeout checkpoints contain 1–37 characters of partial structured JSON and
2–21 streamed chunks, followed by a read stall until the client timeout. The
vLLM process remained healthy and continued returning HTTP 200 responses for
other requests; its log showed no OOM or engine exception. This narrows the
failure to intermittent queued/streamed requests under the high-concurrency
operational schedule, rather than malformed prompts, image clipping, context
overflow, or a deterministic D003/D006 renderer fault. Recovery will therefore
reuse the identical scientific input and inference recipe after the main pass,
when only the small failed subset remains queued.

### 2026-09-03 09:15 — Scheduled completed-case audit

A random newly completed unit, `INC-A5BE8AEFA87F / D021 / Qwen3.8`, was checked
end to end. Its 15,377-byte conversation contains the registered RCA guide,
dashboard grammar, anonymous exhaustive candidates, one PNG, and one complete
JSON response. The persisted record hash verifies; the response stopped
normally without truncation (19,878 input and 209 output tokens); same-prefill
attention was collected with zero extra calls; and the real clipping audit
passed. Native-image inspection found readable topology, metric, trace, and log
cards with no overlap or cropped evidence. Its MRR=0 is attributable to the
model's ranking, not a model-visible input or implementation defect. D021's
large unused lower canvas area is an intentional design-space outcome rather
than missing evidence or packing failure.

### 2026-09-03 10:00 — Scheduled audit found unsupported-edge matcher undercount

The random completed unit `INC-392EE028390B / D032 / Qwen3.8` passed record-hash,
render-clipping, attention, parse, and truncation checks. Its native dashboard
was readable and contained the registered candidate list and evidence. The
model nevertheless stated that 137 was a direct callee of 694 and an upstream
provider to 120, while the authoritative visible edge ledger contained neither
`694→137` nor `137→120`. This is an ordinary model grounding error, but the
persisted deterministic grounding diagnostic reported an empty
`unsupported_structured_mentions` list.

The gap is in the optional reason-grounding matcher: it recognizes mentioned
entities but does not reliably parse every natural-language caller/callee
claim. It does not affect the model-visible input, top-k prediction, private ID
mapping, or registered MRR/AC scoring, so it does not justify interrupting or
rerunning inference. Unsupported-edge rates must be recomputed post hoc from
the preserved raw reasons and exact edge ledger before they are reported; the
current online field must not be treated as complete evidence.

### 2026-09-06 — Clean-v3 development timeouts require a bounded completion pass

The lossless-renderer clean-v3 successor
`rq2_clean_v3_formal_v1_design_development` remained operationally healthy, but
its first Qwen3.8 pass had accumulated 12 isolated request timeouts among 1,630
persisted targets at the 01:05 monitoring boundary. The target-level rate was
only 0.74%, but the failures covered 12 different members of the 60-case
development roster. Treating each incomplete paired case as excluded would
therefore exceed the registered 5% whole-case ceiling and could bias `D*`
selection.

The parent formal scheduler was stopped with `SIGSTOP` while the already-running
Qwen child continued to drain normally. This prevents the scheduler from
starting Gemma or selecting `D*` from an incomplete Qwen matrix. After the
first Qwen pass drains, only non-complete timeout targets will receive a bounded
same-run completion pass using identical prepared evidence, prompts, renderer,
model configuration, sampling, scorer, and run ID. Existing complete records
remain untouched. The scheduler will resume only after paired completeness is
below the registered exclusion ceiling. This is infrastructure recovery, not
selective resampling of model-quality outcomes.

The first Qwen pass ultimately drained with 2,855 complete targets and 25
timeouts. The 25 failure records were copied byte-for-byte, with SHA256s, under
`recovery_audit/20260906_qwen_pass1_timeouts/` before recovery. The bounded
completion pass then reported `resumed_records=2855`, `model_calls=25`, and zero
new infrastructure errors; all 2,880 registered targets now have a normal-stop
trajectory, conversation, and complete prefill/generation-target attention
artifact. The parent scheduler was consequently resumed and proceeded to the
registered Gemma development pass.

Scheduled manual audits at 00:04 and 00:49 inspected all then-completed design
units for randomly selected cases `INC-0E6F68EDF409` and
`INC-992C09A89DC9`. Their trajectories, conversations, native dashboards,
attention artifacts, token accounting, label isolation, and normal stop states
were intact. One unknown candidate ID was an ordinary model answer error; the
large lower blank area in one sampled design was the registered spatial-design
condition rather than missing evidence. No new prompt, renderer, persistence,
attention, or scoring defect was found.
