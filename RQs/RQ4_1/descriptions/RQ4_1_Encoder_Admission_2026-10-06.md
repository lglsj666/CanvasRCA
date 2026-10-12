# RQ4.1: authorized encoder acceleration for CPU admission

The user explicitly authorizes GPU acceleration of visual feature extraction
while continuing CPU admission. This is an execution-scope amendment, not a
diagnostic call, smoke or formal-launch authorization. It does not change the
source images, model weights, processor, CVC objective, optional-support budget,
rewiring, statistical thresholds or existing no-confirmation decision.

The exact current220-case image/support/provenance identities are registered in
`configs/encoder_admission_v5.json`, with output under
`results/comparison_coding_v1/cpu_admission_v5/`. Only the frozen BF16 visual
encoder and projector are loaded. The language decoder is never constructed.
The allocator fraction remains0.75. Every initiated visual forward is recorded
before execution; completed BF16 features and their original grid indices use
an atomic completion marker. Resume trusts committed markers. No old image's
features are reused for a changed image. Full feature tensors here are bounded
CPU qualification caches, not per-call attention records; attention collection
is off. Their disk footprint and extraction time remain reportable preparation
cost, not zero-compute preprocessing.

CPU qualification consumes these actual embeddings, fits the registered bins
on all220 cases once, and uses the unchanged public seed namespace from the
previous bounded implementation. It runs all12 registered matched allocation
conditions (six E50, three E25 and three E75). The original100% CVC technical
availability and per-dataset50% changed-final-mask gates remain mandatory.
All conditions preserve original indices and charge unique tokens once.
Independent FP64 recomputation checks the returned FP32 role qualities with a
fixed2e-6 numerical tolerance, not a changed semantic or scientific threshold.
The independent rewiring audit checks per-role/type/position degree, operand
types and bins, and each original edge's distance bin.

Use at most8 persistent CPU workers, each pinned to a distinct physical core.
Do not cycle worker identities in a way that could reassign an occupied core.
The measured process-lifetime RSS is a conservative upper bound that includes
previous tasks and independent audits, not an isolated per-call allocation.
Every selector still must finish within30seconds and2GiB; the full original
8-hour CPU and48-device-hour experiment ceilings remain in force. The initial
encoder stage additionally has its own3600-second elapsed guard and220-forward
limit. A failed or incomplete check is retained, not replaced with a pass.

No public text facts, historical answers or private labels enter the visual
model. No thresholds or seeds are searched to make dependency masks differ.
Only after the full core mask gate passes is it useful to continue the remaining
QA/intervention/wildcard and production-path qualification; none of these is
implicitly certified by encoder extraction or a selector audit.
