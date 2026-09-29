"""
Shared prompt utilities for prompt conditions.
"""

from __future__ import annotations

from typing import Any, Dict, List

# -----------------------------------------------------------------------
# Output format required for ALL conditions
# -----------------------------------------------------------------------

ANSWER_FORMAT = """\
At the end of your response, output your ranked root-cause prediction as a JSON object:
{"services": ["name1", "name2", "name3"], "reason": "<one sentence>", "confidence": "high|medium|low"}
Rules:
- "services": ranked list of root-cause candidates (pods, services, or nodes), most likely first, at most 5 entries.
- names must exactly match identifiers seen in the telemetry data (e.g., "cartservice-0", "node-6").
- "reason": one sentence citing the strongest signal (metric/log/topology).
- "confidence": high = clear single root cause; medium = plausible but ambiguous; low = insufficient evidence."""

# Service-only variant for datasets where ground truth is a service name only
# (no pod replicas, no infrastructure nodes). Used for RE2-OB, RE2-TT, and any
# service-level dataset where each service is a single entity.
ANSWER_FORMAT_SERVICE_ONLY = """\
At the end of your response, output your ranked root-cause prediction as a JSON object:
{"services": ["name1", "name2", "name3"], "reason": "<one sentence>", "confidence": "high|medium|low"}
Rules:
- "services": ranked list of candidate services, most likely root cause first, at most 5 entries.
- names must exactly match service identifiers in the telemetry (e.g., "checkoutservice", "ts-auth-service").
- "reason": one sentence citing the strongest signal (metric/log/topology).
- "confidence": high = clear single root cause; medium = plausible but ambiguous; low = insufficient evidence."""

# -----------------------------------------------------------------------
# Shared task description
# -----------------------------------------------------------------------

TASK_DESCRIPTION = """\
You are an expert Site Reliability Engineer performing Root Cause Analysis (RCA) \
for a microservice application deployed on a Kubernetes cluster. A fault has \
occurred in the system. Your task is to identify the root cause of the incident.

Root causes can occur at three levels:
- Pod level: a specific container replica (e.g., "cartservice-0")
- Service level: a microservice type (e.g., "paymentservice") — predict any pod of that service
- Node level: an infrastructure host (e.g., "node-6") — nodes appear as isolated entities \
with system metrics (CPU, memory, network, disk) but no application logs or traces

The system consists of multiple services communicating over HTTP/gRPC, \
running on shared infrastructure nodes. A fault in one component (pod, \
service, or node) can propagate to dependent components, causing them to \
appear degraded even though they are not the root cause.

Node-level faults (e.g., host memory exhaustion, CPU saturation, disk I/O) \
often manifest as correlated anomalies across multiple pods. If several \
unrelated pods show simultaneous degradation and a node shows critical \
system-level metrics, the node is likely the root cause.

Focus on distinguishing the ORIGIN of the fault from its SYMPTOMS in \
downstream or co-located components."""

# Service-only variant — used when the dataset has no pod replicas or physical
# nodes (RE2-OB, RE2-TT). Root causes are always services.
TASK_DESCRIPTION_SERVICE_ONLY = """\
You are an expert Site Reliability Engineer performing Root Cause Analysis (RCA) \
for a microservice application. A fault has occurred in one of the services. \
Your task is to identify which service is the root cause of the incident.

The system consists of multiple services communicating over HTTP/gRPC. \
A fault in one service (e.g., CPU overload, memory exhaustion, network delay, \
packet loss, disk I/O stress) can propagate to dependent services, causing \
them to appear degraded even though they are not the root cause.

Focus on distinguishing the ORIGIN of the fault from its SYMPTOMS."""

# -----------------------------------------------------------------------
# Role / Background split (U-BASE / U-EARLY layouts)
# -----------------------------------------------------------------------
# These layouts decompose TASK_DESCRIPTION into the first-sentence Role and the
# remaining Background paragraphs. The split is mechanical and guarded so
# any edit to TASK_DESCRIPTION that breaks the first-sentence boundary
# fails at import time.

TASK_ROLE = TASK_DESCRIPTION.split(". ", 1)[0] + "."
TASK_BACKGROUND = TASK_DESCRIPTION[len(TASK_ROLE):].lstrip()
assert TASK_DESCRIPTION.startswith(TASK_ROLE), (
    "TASK_ROLE no longer prefixes TASK_DESCRIPTION; first-sentence split broken"
)
assert (TASK_ROLE + " " + TASK_BACKGROUND).strip() == TASK_DESCRIPTION.strip(), (
    "TASK_ROLE + TASK_BACKGROUND does not reconstruct TASK_DESCRIPTION"
)

TASK_ROLE_SERVICE_ONLY = TASK_DESCRIPTION_SERVICE_ONLY.split(". ", 1)[0] + "."
TASK_BACKGROUND_SERVICE_ONLY = TASK_DESCRIPTION_SERVICE_ONLY[len(TASK_ROLE_SERVICE_ONLY):].lstrip()
assert TASK_DESCRIPTION_SERVICE_ONLY.startswith(TASK_ROLE_SERVICE_ONLY)
assert (TASK_ROLE_SERVICE_ONLY + " " + TASK_BACKGROUND_SERVICE_ONLY).strip() == TASK_DESCRIPTION_SERVICE_ONLY.strip()


def resolve_task_description(case=None) -> str:
    """Pick TASK_DESCRIPTION variant based on the case's dataset (if provided).

    Falls back to the full K8s-aware description when no case is given (this
    preserves the default for the study scripts that pre-date multi-dataset support).
    """
    if case is not None and getattr(case, "dataset", "") in ("re2_ob", "re2_tt"):
        return TASK_DESCRIPTION_SERVICE_ONLY
    return TASK_DESCRIPTION


def resolve_answer_format(case=None) -> str:
    """Pick ANSWER_FORMAT variant based on the case's dataset."""
    if case is not None and getattr(case, "dataset", "") in ("re2_ob", "re2_tt"):
        return ANSWER_FORMAT_SERVICE_ONLY
    return ANSWER_FORMAT


def resolve_task_role(case=None) -> str:
    """Pick TASK_ROLE variant based on the case's dataset (A4/A5 helper)."""
    if case is not None and getattr(case, "dataset", "") in ("re2_ob", "re2_tt"):
        return TASK_ROLE_SERVICE_ONLY
    return TASK_ROLE


def resolve_task_background(case=None) -> str:
    """Pick TASK_BACKGROUND variant based on the case's dataset (A4/A5 helper)."""
    if case is not None and getattr(case, "dataset", "") in ("re2_ob", "re2_tt"):
        return TASK_BACKGROUND_SERVICE_ONLY
    return TASK_BACKGROUND


def build_given_clause(modality_phrase: str, with_topology: bool) -> str:
    """Cue line listing the evidence channels provided to the model.

    Factored out of ``_AssemblyBase.build_system_prompt`` so A4/A5 can emit
    byte-identical cue text inside the user prompt while the assembly's
    Role lives in the system prompt.
    """
    if with_topology:
        return (
            f"You are given: (1) {modality_phrase} for services in the system, "
            f"and (2) the service dependency graph."
        )
    return (
        f"You are given: {modality_phrase} for services in the system. "
        f"No service dependency graph is provided."
    )

# -----------------------------------------------------------------------
# Tool descriptions for multi-turn conditions
# -----------------------------------------------------------------------

RAW_TOOLS_DESCRIPTION = """\
You have access to the following diagnostic tools. Call them to investigate the incident.

Tool 1: search_traces(parent_span_id: str) -> str
  Returns JSON list of child spans one level below parent_span_id.
  Each span: {span_id, parent_span_id, service_name, operation_name, duration_ms, status_code, timestamp}
  Use this to trace the call graph from entry point to failing service.

Tool 2: search_fluctuating_metrics(service_name: str, timestamp: float) -> str
  Returns CSV of metrics that deviate >3σ from baseline around the fault time.
  Columns: key, regular_mean, regular_std_dev, current_mean, current_std_dev
  Use this to confirm which service has anomalous resource usage.

On each turn, follow this structure:
Thought: <what you know so far, what you need to investigate next, and why>
Action:
<tool_call>
{"tool": "<tool_name>", "args": {<args>}}
</tool_call>

After each tool result, update your reasoning before the next action.
When you have enough evidence, write a final Thought summarizing your conclusion, then output your answer."""

SUMMARIZED_TOOLS_DESCRIPTION = """\
You have access to the following diagnostic tools. Call them to investigate the incident.

Tool 1: get_metrics(service_name: str) -> str
  Returns anomaly analysis for all metrics of a service (z-score, MAD, severity).

Tool 2: get_logs(service_name: str) -> str
  Returns log pattern summary for a service (error rate, error types, burst detection).

Tool 3: get_topology(service_name: str) -> str
  Returns call graph position, upstream/downstream dependencies, betweenness centrality.

On each turn, follow this structure:
Thought: <what you know so far, what you need to investigate next, and why>
Action:
<tool_call>
{"tool": "<tool_name>", "args": {"service_name": "<name>"}}
</tool_call>

After each tool result, update your reasoning before the next action.
When you have enough evidence, write a final Thought summarizing your conclusion, then output your answer."""

SUMMARIZED_TOOLS_NO_LOGS_DESCRIPTION = """\
You have access to the following diagnostic tools. Call them to investigate the incident.

Tool 1: get_metrics(service_name: str) -> str
  Returns anomaly analysis for all metrics of a service (z-score, MAD, severity).

Tool 2: get_topology(service_name: str) -> str
  Returns call graph position, upstream/downstream dependencies, betweenness centrality.

On each turn, follow this structure:
Thought: <what you know so far, what you need to investigate next, and why>
Action:
<tool_call>
{"tool": "<tool_name>", "args": {"service_name": "<name>"}}
</tool_call>

After each tool result, update your reasoning before the next action.
When you have enough evidence, write a final Thought summarizing your conclusion, then output your answer."""


def make_tool_result_message(tool_name: str, result: str) -> Dict[str, str]:
    """Format a tool result as a user turn for multi-turn conditions."""
    return {
        "role": "user",
        "content": f"<tool_result tool=\"{tool_name}\">\n{result}\n</tool_result>",
    }
