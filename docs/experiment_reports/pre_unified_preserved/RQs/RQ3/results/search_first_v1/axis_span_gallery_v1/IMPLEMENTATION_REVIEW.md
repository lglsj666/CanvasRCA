# SEARCH36 implementation checks — 2026-09-12

The first62-test CPU invocation had61 passes and one configuration-load error:
this project's loader supports one `extends` level, not recursive inheritance.
Replaced the newly added nested configuration with a direct rq3.yaml extension,
matching native24 and adding only the axis parameter. No loader/runtime edit,
model call or source artifact regeneration occurred. Preserve this failure as
an authoring error caught before execution; compare fully resolved configs.

The first gallery audit omitted the required processed-root environment before
module imports. Six source/pixel comparisons passed, then source replay stopped
at a missing default-path manifest. Reinvoke with the canonical V3 environment;
the24 generated gallery images were already built with that environment and
are unchanged. Do not alter corpus paths or add a fallback to work around it.

All24 input/pixel checks and six replays passed on the second invocation; its
final assertion incorrectly demanded every case change. Two naturally retain
their old domain and byte-identical image (819F72DDB48B,987C8AAB3A59). Permit
these no-ops, preserve them in the paired analysis, and reuse the corresponding
same-model requests only after input identity verification. No score is used
to choose reuse. This correction changes an audit assertion, not the renderer.
The opt-in axis midpoint additionally uses half-sums to avoid float overflow;
default rendering retains its original formula. Recheck before commitment.
