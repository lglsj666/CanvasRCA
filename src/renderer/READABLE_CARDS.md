# Explicit narrow-card readability profile

`readable_cards(profile="source_cards_v1")` is an opt-in operation. RQ4.2's
512px ordinary panels exposed two limitations of the existing defaults:

- Two-column caption labels can squeeze scalar values into vertical digit
  columns even though the DOM binding still exists.
- A nominal CSS font does not guarantee a minimum physical SVG glyph size.

The profile flows captions across the panel, keeps fitting atomic values on
one line, and applies a local physical floor of 18px to diagnostic glyphs and
1.5px to strokes. It retains every source string and binding, does not round
values, delete duplicate observations, change chart domains, or alter missing
sample semantics. Processor scaling, overlaps and total capacity must still be
audited separately; this operation does not certify a dashboard.

The existing component implementations and default stylesheet are unchanged.
Without the explicit design field the renderer does not inject these styles or
execute the readability adjustment. `measure.py` / `web/measure.tsx` use the
same registered Panel/components and font to measure intrinsic card heights;
they emit CPU audit records and optionally card-only review screenshots. They
cannot declare a set of disconnected card screenshots a qualified dashboard.

No separate RQ-local renderer, model call, evidence selection or numeric
conversion is introduced.

### Explicit source_scopes_v2 and source-region operations

RQ4.2's common full-evidence canvas needs contiguous field-name scopes and
intrinsic-height source cards. `source_scopes_v2` retains every original value,
field occurrence and bound source spelling; scoped prefixes remain visible and
are independently reversible. Diagnostic text is at least 18 physical pixels,
with a 1.5 px stroke floor. Prose wraps; scalar digit strings are not truncated.
Old `source_cards_v1` and the default styles retain their original behavior.

`evidence_regions` adds explicit, nonoverlapping 32 px grid placements because
nested proportional layout cannot reproduce measured unequal card heights.
Every card stays within one of four equal vertical regions. Native region PNGs
are exported by the same renderer and checked against exact master pixels.
`CardDiagnosticInkV1` excludes constant backing fills from audit-only foreground
mass; the normal diagnostic PNG is captured before this measurement.

`question_colors` marks four existing numeric glyphs for independent QA. It
changes only color/underline, preserves glyph geometry and text, and requires
four unique registered slots/bindings. Existing `qa_badges` behavior is unchanged.

## Full-string reflow (`source_reflow_v3`, 2026-10-11)

Opt-in RQ4.3 layout repair authorized by the user. Existing v1 cannot fit the
18px full-string probe within its historical image-token ceilings; v2 factors
field names, which is outside this repair. v3 keeps the ordinary Details
component and every complete name/value, reducing panel padding/gaps and line
height only. It does not change any previous profile, components or defaults.
DOM measurement accepts an explicit font size and indexing metadata; omitted
parameters retain historical behavior. Geometry admission, processed font/line
limits, foreground binding and renderer audit still apply.

## Explicit anchor packing (`anchor_pack`, 2026-10-11)

RQ4.3 needs to replay bounded offsets of complete diagnostic label blocks;
existing layout operations position cards rather than individual DOM blocks.
The operation accepts stable block IDs and integer offsets within ±16px.
`packAudit` identifies actual DOM boxes; experiment preprocessing searches
the measured anchor alpha footprint. `anchorPacking` replays those offsets
through the shared renderer, which retains its normal validation and audits.
Unsupported transforms, invalid or repeated IDs, and excessive offsets fail.
Topology labels and shared pixels remain fixed in the registered CPU prototype.
The search is not a rendering path, and its predictions never replace actual
rendered alpha verification. Defaults are unchanged when the operation is absent.
