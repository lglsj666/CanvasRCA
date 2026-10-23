# Interfaces and receiver contract

`CardInventoryV1` binds visible indices to whole source cards. `CardSelectionV1`
retains raw text, extraction path, rejected tokens and effective kept IDs.
`QAItemV2` binds a typed nonempty accepted solution to actual display evidence.

Tolerant extraction accepts common literal formatting, fences, aliases, numeric
strings, explicit lists and completed entries of clearly truncated structures.
Unknown IDs are removed individually using public ID domains. A valid wrong ID
is still wrong. Never recover arbitrary explanation numbers, guess identifiers,
use oracle values during extraction, or choose among conflicting answers by
correctness. Keep/drop contradiction fails semantically.

QA set semantics are explicit: alternatives versus jointly required values.
Full solution: 1; a correct nonempty but incomplete required solution: .5;
no correct value: 0. Incorrect in-domain extras withhold full credit. Joint
solutions cannot be assembled from incompatible alternatives. A question's
format error never erases unrelated recoverable answers.

Raw conversations, exact submitted image hashes, per-image gathers, source maps,
costs and actual attention queries remain auditable. Final retention uses ordinary
readable content-addressed files, not compressed archives. Runtime caches are
removable only after all writers drain and retained references verify.
