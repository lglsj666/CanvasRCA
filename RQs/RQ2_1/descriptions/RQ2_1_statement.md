# RQ2.1 — Evidence selection, silhouette encoding and dashboard composition

> How do evidence selection, visual encoding, and dashboard composition—and
> their interactions—affect the accuracy and cost of a frozen one-stage RCA solver?

Status: fixed-anchor formal continuation authorized under DD-RQ21-ANCHOR-04.
The user waives another smoke for this baseline-only change. RQ2 is
abandoned. RQ1.1 remains the read-only historical bridge, not a rewritten
baseline. Qwen3.8 and Gemma diagnose once, from text or at most one real PNG.
There is no QA, multi-stage RCA or model training in this RQ.

We separate **what is selected**, **how a card is encoded**, and **where/how
large it is placed**. Selection varies at S0/D0; encoding varies at P0/D0;
composition varies at P0/S0. No champion selection or champion cube remains in
the execution path. These comparisons measure effects around the same parent
reference and do not establish arbitrary cross-component interactions.

All 480 existing evaluation cases across all five datasets are reused and
reported separately, with explicit macro and pooled descriptive summaries.
The historical selection/report split no longer chooses a design. Previously
exposed cases are not relabeled as untouched confirmation.

Positive, negative, null, infeasible and architecture-specific outcomes are
all informative. The objective is identifiable input interventions and honest
accuracy/cost comparisons, not a guaranteed higher MRR. The old observation
that generic QA correlated weakly with RCA does not establish that perception
is unnecessary. Attention is correlational, never a reward or causal proof.

RQ3 may later learn over verified actions, but this study does not automatically
move RQ3 to its champions or launch Composer training.
