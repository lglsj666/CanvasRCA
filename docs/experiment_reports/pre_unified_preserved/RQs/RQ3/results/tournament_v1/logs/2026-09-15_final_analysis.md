# 2026-09-15 — Tournament ended; offline failure analysis

## Scope and status

User stopped adaptive exploration at 38 committed full-remaining rounds.
This is retrospective, evaluator-private analysis, not a new inference run
or confirmation experiment. Per-round contract identities are preserved in
`docs/Tournament_Analysis_2026-09-15_assets/methods.json`.

## What happened

Analyzed 10,789 logical outcomes (10,229 new calls in those historical rounds,
560 reused records). This analysis made zero model calls. Generated the dated
report, six plots, per-attempt/per-case tables, method coverage, paired tests,
failure signatures and representative conversation/evidence reviews.
Qwen AC@1/3/5 union: 394/452/464 of 480; Gemma: 414/454/464.

## Validity and caveats

Verified all 76 model-round remaining cohorts, record and prompt hashes,
stored Top-K/scorer consistency, private-label identities and common visible
inputs across models. Conversations exist. Full PNG hashing was not repeated;
representative PNGs were visually reviewed. No original result was rewritten.
Residual infrastructure failures are zero in these commits; model failures
are retained (Qwen 2, Gemma 13). Later rounds face harder selected cohorts;
their raw success rates are not standalone method comparisons. Best-of-method
coverage is not deployable accuracy. Observable explanation errors are not
claimed to reveal hidden reasoning.

## Decisions

User stop supersedes automated continuation. X is a proposal for competing-
hypothesis evidence selection, not implemented or tested. Candidate nomination
at Top-3/5 and verified evidence use remain distinct. Analysis tables contain
private labels and must not enter future selector/model inputs.

## Blockers

None for the requested analysis. No tournament continuation authorized.

## Next steps

Read `docs/Tournament_Analysis_2026-09-15.md`; await user instructions.
