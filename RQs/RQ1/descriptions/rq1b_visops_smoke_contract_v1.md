# RQ1b partition-aware inference smoke contract — frozen v1

The smoke uses exactly one frozen validation case from each of `re2_ob`,
`aiops2022`, and `aiops2025`, in that dataset order.  It uses the same dense V2
store, task compiler, `T/V/H` prompt composition, balanced arm ordering, unified
VLM client, asynchronous atomic writer, deterministic parser/scorer, 32,768
context, 16,384 output ceiling, and BF16 unquantized server recipe as the
mapping run.

The complete T/V/H task set is executed for each smoke case.  Passage requires:

- zero infrastructure failures;
- complete cross-arm pairing and artifact persistence;
- unchanged configuration, roster, prompt, renderer, and evidence hashes;
- working token, wall-time, GPU-active-time, and peak-memory accounting;
- successful post-hoc verifier execution.

Accuracy, parse acceptance, and answer correctness are diagnostics and cannot
determine passage.  The result is stored under the registered smoke result root
and is excluded from efficacy analysis, modality mapping, and model selection.
Gemma and Qwen each require their own passed smoke report before their mapping
cell may start.
