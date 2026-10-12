# B representation engineering — stage 1

Status: representation correction, real-eval CPU qualification, and execution-
adapter integration complete; final protocol review remains with the leader.
No model call, training, GPU use, or test-360 telemetry access occurred. The
rejected first gallery was moved to
`build/rq31_rejected_gallery/gallery_initial`; the checked gallery is current.

## Public interface and invariants

- `compile_representation_twin(materialized, candidates=...,
  renderer_parameters=..., display_reference_schedule=...)` consumes A's
  unique public fact table plus fact-ID-only bundle references. It performs no
  selection or rescoring.
- Natural text, comparative compact text, exact `X_T` screenshot, Standard,
  Contrast, and M-text all preserve the same unique fact inventory. Shared
  facts are stated/drawn once in clean arms and bundles reference their stable
  display IDs. Registered stress arms may repeat a complete bundle's readable
  presentation while retaining the same unique public fact table.
- P0 public context facts may be unpaired. They are retained in explicit
  `bundle_index=0` context blocks without inventing a bilateral comparison.
  X bundle closure remains A/selector responsibility.
- Candidate IDs remain separate public text. At most one PNG is returned for
  each visual arm. Capacity is reported per carrier: an unavailable screenshot
  does not invalidate an otherwise available compact-text or dashboard carrier.
  `RepresentationTwinV1.require_image(...)` raises the typed capacity failure
  only when C requests that unavailable carrier.
- `renderer_parameters` is exact and fail-closed:
  `{comparison_grouping: contrast|disabled, shared_time_alignment: bool,
  preserve_relative_bins: true}`. `NO_GROUPING` makes Contrast use Standard
  organization; `NO_SHARED_TIME` uses accurate panel-local relative axes and
  never rotates or edits source coordinates.
- A display-load schedule contains only ordered
  `{display_reference_id,bundle_id,occurrence_index,
  display_scope="complete_bundle"}` rows. Natural/compact text restates every
  fact referenced by that bundle, and dashboards redraw its M/R/L/G subblocks,
  explicitly labelled as the same observations. Canonical facts, payloads and
  event counts remain unchanged.
- `rq31_solver_system_prompt()` and `rq31_solver_read_guide(arm)` expose one
  inherited SIRCL* RCA discipline with carrier-accurate grammar. Pure text gets
  no visual guide; screenshot, dashboard and mixed carriers get only their
  actual syntax. No fixed twelve-metric or operation-only-trace claim remains.

## Implemented correction pass

- Removed payload-JSON-as-natural-language and bundle-by-bundle fact expansion.
  The field-aware serializer now uses readable metric, trace, log and relation
  language; compact text keeps the same comparison grouping and one catalogue.
  Compact metric rows encode a regular axis once, followed by values and
  observed counts in axis order, rather than repeating the coordinate for every
  value. The fixture gate requires compact text to be below 85% of the natural
  projection length.
- Removed accidental bundle-by-bundle fact expansion from clean arms. Every
  clean-dashboard fact has exactly one primitive binding; bundle cards use
  short observation references. Only a registered redundant-load schedule can
  add measured, manifest-bound complete-bundle presentation occurrences.
- Metric panels name entity type/ID, metric and y unit; plot true relative
  seconds when supplied (otherwise true relative bins); show numeric x/y ticks;
  and share an axis only for identical metric, unit and x semantics.
- Curves join adjacent valid observations at their real x coordinates. Missing
  bins are not zero-filled and receive no marker/index legend. An all-missing
  series is safe. Trace sides with no value draw no bar and substitute no zero.
- Long titles, side labels, templates and diagnostics use measured lossless
  wrapping. Hosting/membership graphs use type-tiered placement and readable
  relationship labels. Directed call graphs reuse the inherited RQ2.1 topology
  panel; the new typed-fact composer does not claim byte-identical inheritance
  from the full parent dashboard.
- Replaced one-large-panel-per-edge and repeated trace panels with one shared
  trace overview plus one shared topology graph and authoritative O-indexed
  edge ledger. Reference-only comparisons use a compact table; a deterministic
  two-column masonry layout avoids row-height whitespace. No fact was deleted.
- Y ticks use sufficient significant digits to remain distinct for large,
  close values. The metric plot reserves measured left margin for these labels.
- Context-only topology blocks no longer reserve an empty graph. Public log
  truncation and omitted-preview diagnostics are expressed in human language
  instead of being silently hidden or exposing their internal key names.
- Added fail-closed visible checks for raw IPv4 addresses, UUIDs and Kubernetes
  service hostnames in addition to existing dataset/path/private-key checks. A
  completed the public identity sanitizer, and the promoted gallery was rebuilt
  from its re-anonymized public materializations.

## Renderer provenance

- Parent snapshot: `RQs/RQ2_1/src/renderer/*.py`.
- Parent sorted per-file SHA-256 listing hash:
  `66b90b608fa1fcd0cba877c528daccc7d215fe8cf2b96a3f482ea250e5753f71`.
- RQ3.1 local post-import-rebind listing hash before the new projection module:
  `1f5978135408abb254e2103da70ef2059b76a0f1f9c2937b4f978d34831284c3`.
- Exact screenshot geometry/source authority: `RQs/RQ1_1/src/exps.py`, SHA-256
  `4b0decc19e14f74da157951706f274f61f904c529ddc97a5c7b106689e400794`.

## Validation evidence

Command:

```bash
/home/lglsj/CanvasRCA/venvs/tools/bin/python -m pytest -q tests/test_rq31_representation.py
```

Final representation-only result: `18 passed`; final integrated RQ3.1
test-file result: `64 passed in 8.62s`. The tests cover exact inventories, one-PNG
carriers, deterministic bytes, unique dashboard primitives, exact screenshot
source binding, same-semantic axes, all-missing metrics, trace missing-side
behavior, long-field wrap-or-explicit-capacity-failure, P0 unpaired context,
raw-IP/UUID/Kubernetes-host/private-key leakage, readable diagnostic-limit
retention, malformed bilateral bundles, explicit capacity failure, common
prompt grammar, real renderer intervention flags, immutable time coordinates,
complete-bundle display-load repeats, per-carrier typed capacity isolation,
shared relation/trace overviews, and distinct large numeric axis ticks.

Manual CPU fixture inspection opened
`build/rq31_fixture/contrast2.png` with `view_image`. The 2400×2764 PNG had
readable typed IDs, metric/unit axes, trace values, logs, and a non-overlapping
pod→node / pod→service topology. This fixture is implementation evidence,
not the required real-eval gallery.

The final real-eval gallery contains one AIOps-2022, AIOps-2025 and AegisLab
case at budget 64. `view_image` inspected Standard and Contrast for every case,
plus the exact screenshot and mixed carrier. The AIOps-2025/AegisLab Contrast
heights fell from 6905/7267 to 2851/2913 without changing selected facts.
Long blank corridors are gone; comparison rows, traces and the complete edge
ledger are readable and uncropped.

The same saved selections were replayed at 64 and 128 without reselection. All
six now fit: Contrast heights are AIOps-2022 2917/3282, AIOps-2025 2851/3245,
and AegisLab 2913/3065 for 64/128. This supersedes the earlier pre-layout
capacity errors and the provisional recommendation of 64. The budget remains
unfrozen; these are three-case capacity observations, not a scientific freeze.
See `build/rq31_capacity/layout_recovery_summary.json` (`RQ31LayoutRecoveryV6`).

The earlier six-image processor audit remains historical evidence for the
three-case gallery. It is superseded for budget choice by the nine-case audit
below. No model weights or generation were invoked.

## Final nine-case CPU and processor qualification

A deterministic seed-42 cohort contains three registered eval cases from each
of AegisLab, AIOps-2022 and AIOps-2025. The selector was rerun independently at
64, 96 and 128; smaller arms were not truncated from the 128 selection. Across
the 27 selections, 12 used the exact budget and 15 stopped below it because no
additional atomic closed bundle fit. The minimum realized ratio was 0.9583.
This is coverage evidence, not permission to synthesize filler or vary budget
by case.

All base carriers at all three budgets were available in all nine cases. The
natural and compact line bindings, exact screenshot pages, Standard, Contrast
and M-text bboxes were within their canvases and carried the same fact
inventory. A deterministic 128 rerender matched all six carrier hashes for all
nine cases. The model-visible text leakage scan was clean.

`NO_GROUPING` and `NO_SHARED_TIME` changed Contrast pixels in all nine cases
without changing the source fact inventory. `NO_GROUPING` equalled the
corresponding Standard image in all nine; `NO_SHARED_TIME` retained source bins
and rendered the panel-local axes.

The 0.25/0.50 redundant-load conditions now repeat complete bundle
presentations. Because selection is an atomic prefix, realized extra cost was
0.28125–0.44444 and 0.54472–0.71875 respectively. All source carriers fit the
8192-pixel hard height, but this is not sufficient processor-space evidence.

Actual local Qwen and Gemma processors compiled 252 complete requests: full
RQ3.1 RCA guide, evidence carrier, complete candidate list and closing, with an
8,192-token output reserve inside a 40,960 context. Every request fit. Maximum
input was 28,370 tokens for Gemma and 28,161 for Qwen, leaving 4,398 and 4,607
tokens respectively before the reserved output region.

The actual Gemma `max_soft_tokens=1120` geometry gives these operational font
observations (not a performance or validity threshold): budget-64 and
budget-96 Contrast minima were 10.07/10.17 px; budget-128 base Contrast and
Standard minima were 8.50/8.84 px; the 128 exact screenshot was 7.91 px; and
the 0.25/0.50 complete-bundle visual loads fell to 7.47/6.80 px. Three exact
reconstructions of actual Gemma processor outputs were opened with
`view_image`. The two 0.50 stress examples were visibly dense/tiny; the
AIOps-2025 128-base image was structurally clear but marginal at about 8.5 px.

Authoritative audit entry point:
`build/rq31_qualification9/qualification_summary.json`. Supporting artifacts
are `cohort.json`, `evidence_summary.json`, `render_summary.json`,
`processor_token_preflight.json`, `deterministic_rerender.json`, and
`processor_views/gemma1120/manifest.json`; `artifact_sha256.txt` records the
point-in-time source/config/report/image hashes used by this qualification.
The standard budget remains
unfrozen. Root must decide whether the marginal AIOps-2025 base image and the
sub-9-px screenshot/stress arms are acceptable or require a protocol/layout
change; this audit did not silently lower any case.

## Integration state and remaining leader actions

C now consumes the common system/read-guide APIs, routes all three P0 anchors
through the same compiled P0 twin, passes A's renderer parameters and ordered
display-reference schedule, and no longer mutates comparison keys or rotates
relative bins. The integrated tests exercise these paths. The leader must
review the final images and choose one global semantic budget; no per-case or
per-dataset fallback is justified by this audit. A live server qualification
and formal inference remain out of scope.

No background process is running; PID: none.

Resume command:

```bash
cd /home/lglsj/CanvasRCA_nibi && git status --short && \
  /home/lglsj/CanvasRCA/venvs/tools/bin/python -m pytest -q tests/test_rq31_representation.py
```
