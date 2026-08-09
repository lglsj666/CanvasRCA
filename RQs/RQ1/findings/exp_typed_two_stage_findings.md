# Typed Two-Stage Findings

**Status:** historical exposed-development mechanism qualification; final
469-case Nibi rerun not yet completed; the historical cross-architecture gate
failed.

The typed handoff removed the earlier eight-row ledger bottleneck. On the
12-case perception qualification, Qwen passed all registered mechanism checks:
level-1 accuracy was `11/12`, level-2 was `12/12`, and the required edge/link
families passed. Gemma obtained `7/12` and `5/12`, with three Stage-1
truncations; it failed the primary gate even though Stage 2 itself parsed.

The result supports a Qwen-specific claim that the supplied dashboard and typed
handoff are usable. It does not establish a cross-architecture mechanism and it
does not measure RCA MRR. The compact implementation retains a finite failure
marker so a malformed Stage-1 response cannot flood Stage 2 with raw output.

These local outcomes are not substituted for the registered final Nibi rerun.
This file will be updated with the 289-case primary headline and separate
RE2-OB/RE2-TT slices after that run is complete and verified.
