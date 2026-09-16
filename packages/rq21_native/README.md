# RQ2.1 vendored native methods

Original reference files are retained unchanged. Executable SIRCL copies live
under `sircl_adapted/`; BARO's component is imported directly from its preserved
local source. No RQ2.1 runtime imports an external SIRCL checkout. CPU tests
compare the original and adapted algorithms on identical safe telemetry, check
source-event bindings, and preserve native signs, missing handling and ties.

BARO: official repository tag 0.1.9, annotated tag object
`861ef2e09950e47574fbd3518a119cfbed6f9f82`, peeled **commit**
`0c270feae637f000a72edf33a8cd1423672b2c95`. Do not confuse a tag-object hash
with a commit/raw-file URL. MIT license is retained in `baro_original/LICENSE`.
Only RobustScorer is selected, not the full change-point/RCA system.

SIRCL: user-provided `RL-SLM-RCA-main` source, byte copies of the trace SC,
Drain log frequency/timestamp/parser and standalone metric MA modules. Source
paths and checksums are in `PROVENANCE.json`. The provided checkout has no
root license; do not silently apply the other SIRCL snapshot's MIT license to
these files or assert redistributability. Copying for this local adaptation was
expressly authorized by the user. Confirm distribution permission before
publishing these newly staged sources.

The adapters use the shared telemetry-derived analysis split, never a labelled
injection timestamp. Structured native rankings are returned before CSV display
formatting. Native insufficient rankings have explicit parent-order fill; an
exception is not a successful fallback. BARO exposes an ordinal rank list; the
adapter does not invent numeric scores absent from that native return value.

RQ3's `log_adapter.py` reuses the same native Drain frequency component with
positional source-event IDs, an explicit canonical seconds clock and public
analysis window. Native cluster counts bind exactly to Denum event groups;
the caller records its six-template selection and any original-priority fill.
This is not the complete TORAI system. The original files and their hashes
remain unchanged. An unregistered cwd `drain3.ini` is rejected rather than
silently changing parser configuration.

The source scorer is also copied unchanged; RQ2.1 uses its name-matching helpers
with the inherited granularity adapter through the unified RCA scorer. All
1,920 original T/V records retain their MRR under that path.

RQ3's `mean_shift_adapter.py` calls the copied SIRCL MA implementation on
finite public-window observations. Lossless column aliases prevent ambiguous
service prefixes; unrounded native scores rank the full pool. The strict
threshold, population deviation and constant-baseline skip are unchanged.
SIRCL MA is NOT the official ThinkFL pointwise/centered-window implementation;
the round protocol documents that distinction. No external checkout is needed.

CPU dependencies are the existing tools environment plus the versions in
`requirements.txt`. For a standalone local dependency overlay (no model-env
changes), install those requirements into `build/rq21_python_deps/`; RQ2.1
launchers already include this directory in `PYTHONPATH`.
