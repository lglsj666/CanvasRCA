# RQ1.1 — Unified representation and interactive evidence use

## Research question

Under one canonical public evidence preparation and matched model-specific
inference recipes, how do telemetry representations affect direct RCA,
cross-region dashboard reasoning, and bounded tool-using RCA?

RQ1.1 is explicitly descriptive and comparative rather than advocacy-driven.
Its purpose is not to prove that images help RCA. It measures how text,
pixels, real telemetry graphics, and modality-specific visual encodings change
accuracy, reasoning behaviour, attention allocation, and token cost. A visual
benefit, visual harm, null effect, or model-specific interaction is an equally
valid outcome.

RQ1.1 is a clean successor to RQ1. It does not rewrite or rehabilitate the
historical RQ1 artifacts. Its active models are Qwen3.8-27B and
Gemma-4-26B-A4B-it. Every model-visible entity name is replaced by a case-local
numeric ID: three digits for a service, four for a node, and five for a pod.
The private evaluator alone retains the reversible mapping.

The experiment distinguishes a real telemetry dashboard from pure natural
language and from an exact screenshot of that language. It also isolates the
visual encoding of metrics, traces, logs, and topology. Finally, it tests
whether a fixed three-step ReAct-like interaction can turn the initial
representation into better evidence search and RCA rankings.
