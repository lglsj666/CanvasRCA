# 2026-09-12 — SEARCH35 permutation-check correction

Before model calls, the CPU audit stopped at its assertion that reversing the
entire pool must preserve the entire packet list order. The selector deliberately
preserves source metadata order, so reversing that metadata also reverses its
order in the packet. This is an overbroad audit assertion, not changed evidence
selection or a changed canonical input. The failed assertion was reproduced.

The replacement verifies identical ordered selected IDs, all complete fact
payloads, and ordered facts within each field, including every metadata field.
Source-order changes may alter the source hash, as they should. Canonical
source bytes, production selection, renderer and already-generated PNGs remain
unchanged. Full CPU regression: 254 tests, zero failures/errors/skips. The
remaining 24-case audit and six native/coverage PNG replays must still pass.
