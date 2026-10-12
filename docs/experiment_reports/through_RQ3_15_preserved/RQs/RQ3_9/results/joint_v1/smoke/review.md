# RQ3.9 bounded smoke review — 2026-10-01

Outcome:12/12 requests and logical positions complete, zero infrastructure
failures, zero model-format failures, no design exclusions. Supervisor wall
time518.31s, including112.15s service startup, within600s. Ledger records12
initiated/completed calls, below18. No supplemental smoke needed.

Inspected all12 actual saved input records, full generated responses and
conversation Markdown. Every model-visible text part appears verbatim in
its persisted conversation; image digests match prepared PNGs. All completed
artifact inventories passed. The six real smoke PNGs were visually inspected
before inference; their unchanged digests bind those reviews to the actual
model requests. Text-only has no PNG; both graphical conditions have one image
and identical text; image tokens2242 each. No attention artifacts requested.

Outputs provide3–4 candidates here, which is allowed by the inherited scorer
and schema; do not force five or silently pad rankings. Explanations contain
substantive causal overreach: largest/earliest anomaly used as origin, apparent
unsupported dependencies, and host/instance scope claims not warranted by
the cited observations. These remain model outcomes and scientific limitations,
not evidence of an input mutation or a reason to tune on the smoke answers.
For example, AIOPS-2022 TEXT_JOINT explicitly questions its own hypothesized
803→330 edge, and AIOPS-2025's graphical reasons use memory/eviction causal
language without establishing that mechanism. No correctness or MRR gate was
used to pass this qualification; efficacy remains unknown.

Operational caveat: eleven request durations were173.3–230.8s; one
TEXT_JOINT request took403.3s and677 output tokens. The inherited300-second
OpenAI-client/httpx timeout is a connection/read timeout, not an absolute
deadline for an actively streaming response. No timeout value was raised;
the stream continuously progressed. The separate600-second smoke wall-clock
supervisor was armed but did not fire. Formal runs retain this existing
client behavior,8192 output ceiling and error policy. Full36-request
saturation/throughput is not proven by a12-call smoke.

Pass for the registered pilot's operational/artifact checks. No changes to
prompt, arm, roster, selector, renderer or scoring after observing responses.
Proceed only with the registered120-case Qwen queue; no test or expansion.
