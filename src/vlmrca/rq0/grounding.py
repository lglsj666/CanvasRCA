"""Development-only atomic visual-grounding tasks for renderer-v6 dashboards."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from vlmrca.vlm.client import image_part, text_part

GROUNDING_SCHEMA_VERSION = "RQ0AtomicVisualGroundingV1"
LETTERS = "ABCD"
SYSTEM = (
    "You are evaluating visual dashboard reading, not root-cause diagnosis. "
    "Answer only from the supplied dashboard pixels. Do not infer an incident "
    "cause or use outside knowledge."
)


def _hash_int(*values: str) -> int:
    return int(hashlib.sha256("\0".join(values).encode()).hexdigest(), 16)


def _compact_number(value: Any) -> str:
    """Match the compact numeric formatter used by the rendered tables."""
    if value is None:
        return "n/a"
    number = float(value)
    if not math.isfinite(number):
        return "n/a"
    absolute = abs(number)
    if absolute >= 1e9:
        return f"{number / 1e9:.1f}G"
    if absolute >= 1e6:
        return f"{number / 1e6:.1f}M"
    if absolute >= 1e3:
        return f"{number / 1e3:.1f}k"
    if absolute >= 10:
        return f"{number:.0f}"
    if absolute >= 0.01:
        return f"{number:.2f}"
    return f"{number:.1e}"


def _unique(values: Iterable[str]) -> List[str]:
    out = []
    for value in values:
        text = str(value)
        if text not in out:
            out.append(text)
    return out


def _fill_numeric_options(correct: str, candidates: Sequence[str]) -> List[str]:
    values = _unique([correct, *candidates])
    try:
        base = int(correct)
        fillers = [str(max(0, base + delta)) for delta in (-2, -1, 1, 2, 10)]
    except ValueError:
        fillers = ["0", "1", "10", "100", "n/a"]
    return _unique([*values, *fillers])[:4]


def _choice_task(
    *,
    opaque_id: str,
    task_id: str,
    category: str,
    question: str,
    correct: str,
    distractors: Sequence[str],
    visual_primitive: str,
    metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    options = _unique([correct, *distractors])
    if len(options) < 4:
        raise ValueError(f"{task_id} has only {len(options)} unique options")
    # Hash sorting gives stable, case-specific option placement without a hidden
    # global preference for A.  The correct value is not treated specially.
    options = sorted(
        options[:4], key=lambda value: hashlib.sha256(
            f"{opaque_id}:{task_id}:{value}".encode()
        ).hexdigest()
    )
    answer_index = options.index(correct)
    return {
        "task_id": task_id,
        "category": category,
        "question": question,
        "options": [
            {"label": LETTERS[index], "text": value}
            for index, value in enumerate(options)
        ],
        "answer_label": LETTERS[answer_index],
        "answer_value": correct,
        "visual_primitive": visual_primitive,
        "metadata": metadata or {},
    }


def _panel(manifest: Dict[str, Any], kind: str) -> Dict[str, Any]:
    return next(item for item in manifest.get("panels", []) if item.get("kind") == kind)


def _select(values: Sequence[Any], opaque_id: str, salt: str) -> Any:
    if not values:
        raise ValueError(f"no values available for {salt}")
    return values[_hash_int(opaque_id, salt) % len(values)]


def _service_distractors(
    manifest: Dict[str, Any], correct: str, preferred: Iterable[str]
) -> List[str]:
    visible = [
        str(row.get("service"))
        for kind in ("propagation", "logs", "traces")
        for row in _panel(manifest, kind).get("rows", _panel(manifest, kind).get("entries", []))
        if row.get("service")
    ]
    return [value for value in _unique([*preferred, *visible]) if value != correct]


def _pair(left: str, right: str) -> str:
    a, b = sorted((str(left), str(right)))
    return f"{a} ↔ {b}"


def build_atomic_grounding_tasks(manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build seven label-free questions whose answers are visible in the PNG."""
    opaque_id = str(manifest["opaque_incident_id"])
    metrics = [item for item in manifest["panels"] if item.get("kind") == "metric"]
    propagation = _panel(manifest, "propagation")
    logs = _panel(manifest, "logs")
    traces = _panel(manifest, "traces")
    prop_rows = propagation.get("rows") or []
    if len(metrics) < 4 or len(prop_rows) < 4:
        raise ValueError("atomic grounding requires at least four metric and propagation rows")

    target_metric = _select(metrics, opaque_id, "metric_service")
    metric_services = _unique(str(row["service"]) for row in metrics)
    service_distractors = _service_distractors(
        manifest,
        str(target_metric["service"]),
        metric_services,
    )
    tasks = [
        _choice_task(
            opaque_id=opaque_id,
            task_id="metric_service",
            category="metric_identity",
            question=(
                f"Which option is the service name shown in the title of panel "
                f"[{target_metric['panel_id']}]?"
            ),
            correct=str(target_metric["service"]),
            distractors=service_distractors,
            visual_primitive=str(target_metric["panel_id"]),
        )
    ]

    directional = [
        row for row in metrics
        if row.get("signed_z") is not None and abs(float(row["signed_z"])) > 0
    ]
    direction_metric = _select(directional, opaque_id, "metric_direction")
    direction = "increase" if float(direction_metric["signed_z"]) > 0 else "decrease"
    tasks.append(
        _choice_task(
            opaque_id=opaque_id,
            task_id="metric_direction",
            category="metric_pattern",
            question=(
                "From the printed baseline-to-peak annotation beneath panel "
                f"[{direction_metric['panel_id']}], what is the direction of change?"
            ),
            correct=direction,
            distractors=[
                value for value in ("increase", "decrease", "approximately unchanged", "not shown")
                if value != direction
            ],
            visual_primitive=str(direction_metric["panel_id"]),
        )
    )

    rank_row = _select(prop_rows[: min(8, len(prop_rows))], opaque_id, "propagation_rank")
    rank_services = [str(row["service"]) for row in prop_rows]
    tasks.append(
        _choice_task(
            opaque_id=opaque_id,
            task_id="propagation_rank",
            category="topology_order",
            question=(
                "Which service is printed at rank "
                f"{rank_row['rank']} in the Anomaly propagation panel?"
            ),
            correct=str(rank_row["service"]),
            distractors=[value for value in rank_services if value != rank_row["service"]],
            visual_primitive="P1",
            metadata={"rank": int(rank_row["rank"])},
        )
    )

    onset_rows = [row for row in prop_rows if row.get("onset_rel_min") is not None]
    onset_values = [f"+{float(row['onset_rel_min']):.1f}m" for row in onset_rows]
    unique_onset_rows = [
        row for row, value in zip(onset_rows, onset_values)
        if onset_values.count(value) == 1
    ]
    onset_row = _select(unique_onset_rows or onset_rows, opaque_id, "propagation_onset")
    onset_answer = f"+{float(onset_row['onset_rel_min']):.1f}m"
    onset_options = _unique(
        f"+{float(row['onset_rel_min']):.1f}m"
        for row in onset_rows
        if row.get("onset_rel_min") is not None
    )
    tasks.append(
        _choice_task(
            opaque_id=opaque_id,
            task_id="propagation_onset",
            category="topology_time",
            question=(
                "What relative onset value is printed on the row for "
                f"{onset_row['service']} in the Anomaly propagation panel?"
            ),
            correct=onset_answer,
            distractors=[value for value in onset_options if value != onset_answer],
            visual_primitive="P1",
        )
    )

    log_entries = logs.get("entries") or []
    if not log_entries:
        raise ValueError("atomic grounding requires visible log entries")
    readable_logs = [row for row in log_entries if len(str(row["service"])) <= 24] or log_entries
    log_row = _select(readable_logs, opaque_id, "log_value")
    if logs.get("mode") == "errors":
        log_field, log_column = "error_logs", "err"
    else:
        log_field, log_column = "n_during", "during"
    log_answer = str(int(log_row[log_field]))
    log_options = _fill_numeric_options(
        log_answer,
        [str(int(row[log_field])) for row in log_entries if row.get(log_field) is not None],
    )
    tasks.append(
        _choice_task(
            opaque_id=opaque_id,
            task_id="log_value",
            category="table_log",
            question=(
                f"In the Log signals table, what value is printed in the {log_column} "
                f"column for {log_row['service']}?"
            ),
            correct=log_answer,
            distractors=[value for value in log_options if value != log_answer],
            visual_primitive="G1",
            metadata={"log_mode": logs.get("mode"), "column": log_column},
        )
    )

    trace_entries = traces.get("entries") or []
    if not trace_entries:
        raise ValueError("atomic grounding requires visible trace entries")
    readable_traces = [row for row in trace_entries if len(str(row["service"])) <= 22] or trace_entries
    trace_row = _select(readable_traces, opaque_id, "trace_value")
    trace_answer = _compact_number(trace_row.get("p95_during_ms"))
    trace_options = _unique(
        _compact_number(row.get("p95_during_ms")) for row in trace_entries
    )
    if len(trace_options) < 4:
        trace_options = _unique([*trace_options, "0", "1", "10", "100", "n/a"])
    tasks.append(
        _choice_task(
            opaque_id=opaque_id,
            task_id="trace_value",
            category="table_trace",
            question=(
                "In the Trace signals table, what compact value is printed in the "
                f"during column for {trace_row['service']}?"
            ),
            correct=trace_answer,
            distractors=[value for value in trace_options if value != trace_answer],
            visual_primitive="R1",
        )
    )

    drawn_edges = [tuple(map(str, edge)) for edge in propagation.get("edges") or []]
    if drawn_edges:
        edge = _select(drawn_edges, opaque_id, "topology_edge")
        correct_pair = _pair(*edge)
        drawn_pairs = {_pair(*item) for item in drawn_edges}
        non_edges = []
        services = [str(row["service"]) for row in prop_rows]
        for i, left in enumerate(services):
            for right in services[i + 1 :]:
                candidate = _pair(left, right)
                if candidate not in drawn_pairs:
                    non_edges.append(candidate)
        tasks.append(
            _choice_task(
                opaque_id=opaque_id,
                task_id="topology_edge",
                category="topology_edge",
                question=(
                    "Which unordered service pair is joined by one of the visible "
                    "curved arrows in the Anomaly propagation panel?"
                ),
                correct=correct_pair,
                distractors=non_edges,
                visual_primitive="P1",
                metadata={"variant": "pair"},
            )
        )
    else:
        tasks.append(
            _choice_task(
                opaque_id=opaque_id,
                task_id="topology_edge",
                category="topology_edge",
                question=(
                    "How many curved call-edge arrows are visible in the Anomaly "
                    "propagation panel?"
                ),
                correct="0",
                distractors=["1", "2", "3 or more"],
                visual_primitive="P1",
                metadata={"variant": "count_zero"},
            )
        )
    return tasks


def task_prompt(tasks: Sequence[Dict[str, Any]]) -> str:
    lines = [
        "Read the dashboard and answer every multiple-choice question.",
        "Return exactly one JSON object with an answers map and no other text.",
        'Example shape: {"answers":{"metric_service":"A","metric_direction":"B"}}',
        "Use only option letters A, B, C, or D.",
        "",
    ]
    for task in tasks:
        lines.append(f"[{task['task_id']}] {task['question']}")
        lines.extend(f"  {option['label']}. {option['text']}" for option in task["options"])
        lines.append("")
    return "\n".join(lines).rstrip()


def build_grounding_prompt(
    png: bytes | None, tasks: Sequence[Dict[str, Any]]
) -> Dict[str, Any]:
    parts = []
    if png is not None:
        parts.append(image_part(png))
    parts.append(text_part(task_prompt(tasks)))
    return {"system": SYSTEM, "parts": parts}


def parse_grounding_answers(text: str) -> Dict[str, str]:
    stripped = (text or "").strip()
    if stripped.startswith("```"):
        stripped = re_sub_code_fence(stripped)
    candidates = [stripped]
    start, end = stripped.find("{"), stripped.rfind("}")
    if 0 <= start < end:
        candidates.append(stripped[start : end + 1])
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        answers = value.get("answers") if isinstance(value, dict) else None
        if isinstance(answers, dict):
            return {
                str(key): str(answer).strip().upper()
                for key, answer in answers.items()
                if str(answer).strip().upper() in LETTERS
            }
    return {}


def re_sub_code_fence(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def score_grounding_answers(
    tasks: Sequence[Dict[str, Any]], answers: Dict[str, str]
) -> Dict[str, Any]:
    records = []
    for task in tasks:
        predicted = answers.get(task["task_id"])
        records.append(
            {
                "task_id": task["task_id"],
                "category": task["category"],
                "predicted_label": predicted,
                "answer_label": task["answer_label"],
                "correct": predicted == task["answer_label"],
            }
        )
    return {
        "n_tasks": len(records),
        "n_answered": sum(row["predicted_label"] is not None for row in records),
        "n_correct": sum(row["correct"] for row in records),
        "accuracy": sum(row["correct"] for row in records) / len(records) if records else 0.0,
        "tasks": records,
    }
