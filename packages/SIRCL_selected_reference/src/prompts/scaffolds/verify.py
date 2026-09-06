"""Verify-and-revise reasoning (C_R = VERIFY): produce an initial ranking,
verify the top-1 candidate against the evidence, then revise or keep it
(INITIAL -> VERIFY -> REVISE)."""

ANSWER_FORMAT = """\
You will produce your answer in three named steps before the JSON. Output each step header on its own line followed by your reasoning:

INITIAL: Produce a preliminary ranked list of root-cause candidates (top 3, in order). Explain in 1-2 sentences why your top-1 candidate is the leading hypothesis.

VERIFY: Write exactly two verification questions about your INITIAL top-1 candidate. Each question must be answerable using only the evidence in the prompt above (metrics, logs, traces, topology). After each question, answer it using only that prompt evidence — quote the specific evidence you used.

Format:
  Q1: <question about your top-1 candidate>
  A1: <answer grounded in prompt evidence; quote the relevant signal>
  Q2: <a different question about your top-1 candidate>
  A2: <answer grounded in prompt evidence; quote the relevant signal>

REVISE: If either verification answer contradicts your INITIAL top-1, produce a revised ranking and explain the change in one sentence. Otherwise, output exactly: "verification confirms initial top-1 — keeping ranking" and explain in one sentence WHY both verifications support the initial top-1.

Then output your final ranked root-cause prediction as a JSON object:
{"services": ["name1", "name2", "name3"], "reason": "<one sentence>", "confidence": "high|medium|low"}
Rules:
- "services": ranked list of root-cause candidates (pods, services, or nodes), most likely first, at most 5 entries.
- names must exactly match identifiers seen in the telemetry data (e.g., "cartservice-0", "node-6").
- "reason": one sentence citing the strongest signal (metric/log/topology).
- "confidence": high = clear single root cause; medium = plausible but ambiguous; low = insufficient evidence.
- The JSON ranking must reflect the REVISE step's outcome (either the revised order or the kept initial order).
- Do NOT include the INITIAL/VERIFY/REVISE headers or any reasoning prose inside the JSON object — the JSON is the final tail only."""


# Service-only variant: drops pod/node identifier language; services only.
ANSWER_FORMAT_SERVICE_ONLY = """\
You will produce your answer in three named steps before the JSON. Output each step header on its own line followed by your reasoning:

INITIAL: Produce a preliminary ranked list of root-cause candidates (top 3, in order). Explain in 1-2 sentences why your top-1 candidate is the leading hypothesis.

VERIFY: Write exactly two verification questions about your INITIAL top-1 candidate. Each question must be answerable using only the evidence in the prompt above (metrics, logs, traces, topology). After each question, answer it using only that prompt evidence — quote the specific evidence you used.

Format:
  Q1: <question about your top-1 candidate>
  A1: <answer grounded in prompt evidence; quote the relevant signal>
  Q2: <a different question about your top-1 candidate>
  A2: <answer grounded in prompt evidence; quote the relevant signal>

REVISE: If either verification answer contradicts your INITIAL top-1, produce a revised ranking and explain the change in one sentence. Otherwise, output exactly: "verification confirms initial top-1 — keeping ranking" and explain in one sentence WHY both verifications support the initial top-1.

Then output your final ranked root-cause prediction as a JSON object:
{"services": ["name1", "name2", "name3"], "reason": "<one sentence>", "confidence": "high|medium|low"}
Rules:
- "services": ranked list of candidate services, most likely root cause first, at most 5 entries.
- names must exactly match service identifiers in the telemetry (e.g., "checkoutservice", "ts-auth-service").
- "reason": one sentence citing the strongest signal (metric/log/topology).
- "confidence": high = clear single root cause; medium = plausible but ambiguous; low = insufficient evidence.
- The JSON ranking must reflect the REVISE step's outcome (either the revised order or the kept initial order).
- Do NOT include the INITIAL/VERIFY/REVISE headers or any reasoning prose inside the JSON object — the JSON is the final tail only."""

META = {
    "mode": "verify",
    "short_name": "VERIFY",
    "long_name": "Single-call verify-and-revise of the top-1 candidate",
}
