# RQ1.1 — Single-stage visual RCA, perception, and token efficiency

## Research question

Under single-call and equal-information conditions, how do visual
representations of metrics, traces, logs, and topology affect perception, RCA
accuracy, attention allocation, and token efficiency—and how are perception
changes related to RCA outcomes?

RQ1.1 is explicitly descriptive and comparative rather than advocacy-driven.
Its purpose is not to prove that images help RCA. It measures how text,
pixels, real telemetry graphics, and modality-specific visual encodings change
accuracy, visible evidence use, attention allocation, and token cost. A visual
benefit, visual harm, null effect, or model-specific interaction is an equally
valid outcome.

The successor protocol includes a concise structured-text control (`C`) with
the same facts as natural-language text (`T`). This separates gains from
shorter, regular nonvisual serialization from gains due to spatial visual
encoding; it does not reintroduce the retired flat-JSONL protocol.

RQ1.1 is a clean successor to RQ1. It does not rewrite or rehabilitate the
historical RQ1 artifacts. Its active models are Qwen3.8-27B and
Gemma-4-26B-A4B-it. Every model-visible entity name is replaced by a case-local
numeric ID: three digits for a service, four for a node, and five for a pod.
The private evaluator alone retains the reversible mapping.

The experiment distinguishes a real telemetry dashboard from pure natural
language and from an exact screenshot of that language. A complete four-factor
design isolates the visual encoding and interactions of metrics (M), traces
(R), logs (L), and topology (G). A matched path-directed QA experiment measures
direct reading and cross-region composition, then joins those observations to
the same case/model/representation's RCA outcome.

Only one-stage RCA and one image per visual call are active. The retained
`multi_stage_rca` source is abandoned for this paper. Interactive dashboards
and multi-stage visual agents are future work and do not enter smoke, formal
execution, statistics, or RQ1.1 conclusions.

After the weak observed association between cross-region QA and RCA, RQ1.1
also registers a separate one-stage counterfactual RCA mechanism experiment.
It asks whether a controlled change to image semantics moves the model's
ranking in the matching direction, rather than inferring faithful diagnostic
reasoning from answer accuracy alone. This successor uses only the frozen
RQ1.1 renderer-v14, prompt, evidence packet, model recipes, scorer, and roster;
it has no dependency on any RQ2 dashboard design.

All active RQ1.1 experiments reuse the complete frozen 480-case identity
manifest after lossless V3 regeneration. Direct RCA, Direct QA, and the
one-stage counterfactual successor together require 39,360 calls. The 40,000
limit is one aggregate budget for the whole major RQ1.1, not a fresh allowance
for each subexperiment.
