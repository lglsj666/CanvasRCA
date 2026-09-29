# RQ3.2 — Signal-preserving evidence selection

> How can one deterministic evidence compiler preserve heterogeneous diagnostic
> signals, distinguish competing root-cause explanations, and expose any
> incremental value of visual organization to a frozen one-stage RCA Solver?

RQ3.2 does not train a model, run a preliminary LLM diagnosis, record attention,
or perform multi-round retrieval. It rebuilds a complete public evidence pool
from canonical per-case telemetry, uses the telemetry-derived P0 analysis
boundary, and separates public statistics, selection, and representation.

The main method is `SC_FULL` (CanvasRCA-SignalCover). P0, native X, aligned X,
SIRCL text, original text, and TPV remain explicit controls. The primary outcome
is MRR; AC@1/3/5, repair/break, granularity errors, evidence coverage, tokens,
and failures are secondary outcomes.

