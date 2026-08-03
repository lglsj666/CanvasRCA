#!/usr/bin/env python3
"""Run the development-only RQ0 atomic visual-grounding diagnostic.

Each frozen question bundle is evaluated with its correct dashboard, a
same-dataset swapped dashboard, and no image.  This is a perception diagnostic,
not an RCA metric and not part of the RQ0 confirmatory result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List

from RQs.RQ0.scripts.run_rq0 import GPUMonitor
from vlmrca.processed import load_processed_case
from vlmrca.render.dashboard import CaseRenderView, compile_dashboard
from vlmrca.render.presets import make_dashboard_config
from vlmrca.rq0.grounding import (
    GROUNDING_SCHEMA_VERSION,
    build_atomic_grounding_tasks,
    build_grounding_prompt,
    parse_grounding_answers,
    score_grounding_answers,
)
from vlmrca.vlm.client import call_vlm, count_vllm_prompt_tokens
from vlmrca.vlm.configs import get_config

ROOT = Path(__file__).resolve().parents[3]
SOURCE_EXPERIMENT = "rq0_equal_information_equal_compute_v1"
EXPERIMENT = "rq0_atomic_visual_grounding_v1"
CONDITIONS = ("actual_image", "swapped_image", "no_image")
ORDERS = (
    CONDITIONS,
    (CONDITIONS[0], CONDITIONS[2], CONDITIONS[1]),
    (CONDITIONS[1], CONDITIONS[0], CONDITIONS[2]),
    (CONDITIONS[1], CONDITIONS[2], CONDITIONS[0]),
    (CONDITIONS[2], CONDITIONS[0], CONDITIONS[1]),
    (CONDITIONS[2], CONDITIONS[1], CONDITIONS[0]),
)


def _sha(value: bytes | str | Path) -> str:
    if isinstance(value, Path):
        value = value.read_bytes()
    if isinstance(value, str):
        value = value.encode()
    return hashlib.sha256(value).hexdigest()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _write_text(path: Path, text: str, append: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a" if append else "w", encoding="utf-8") as handle:
        handle.write(text)
        handle.flush()


class AsyncArtifactWriter:
    """Serialize disk writes on a background thread and drain at run end."""

    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="grounding-writer")
        self._futures = []

    def text(self, path: Path, content: str, append: bool = False) -> None:
        self._futures.append(self._executor.submit(_write_text, path, content, append))

    def jsonl(self, path: Path, record: Dict[str, Any]) -> None:
        self.text(path, json.dumps(record, ensure_ascii=False, default=str) + "\n", True)

    def close(self) -> None:
        self._executor.shutdown(wait=True)
        for future in self._futures:
            future.result()


def _source_roster() -> List[Dict[str, Any]]:
    path = (
        ROOT
        / "RQs/RQ0/results"
        / SOURCE_EXPERIMENT
        / "qualification_visual_qa"
        / "visual_qa_roster.json"
    )
    return json.loads(path.read_text())["records"]


def _artifact_root() -> Path:
    return ROOT / "RQs/RQ0/results" / EXPERIMENT / "artifacts"


def prepare_artifacts() -> Dict[str, Any]:
    """Compile and freeze the 12 development dashboards and question keys."""
    cfg = make_dashboard_config("rq0_v6")
    root = _artifact_root()
    records = []
    for item in _source_roster():
        case = load_processed_case(item["dataset"], item["private_case_id"])
        png, manifest = compile_dashboard(CaseRenderView.from_case(case), cfg)
        if manifest["opaque_incident_id"] != item["opaque_incident_id"]:
            raise RuntimeError("opaque incident id changed while building grounding artifacts")
        source_png = ROOT / item["image"]
        if not source_png.is_file() or source_png.read_bytes() != png:
            raise RuntimeError(f"renderer drift for {item['opaque_incident_id']}")
        tasks = build_atomic_grounding_tasks(manifest)
        opaque = item["opaque_incident_id"]
        image_path = root / "renders" / f"{opaque}.png"
        manifest_path = root / "renders" / f"{opaque}.manifest.json"
        task_path = root / "tasks" / f"{opaque}.tasks.json"
        image_path.parent.mkdir(parents=True, exist_ok=True)
        task_path.parent.mkdir(parents=True, exist_ok=True)
        image_path.write_bytes(png)
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        task_path.write_text(json.dumps(tasks, indent=2, ensure_ascii=False) + "\n")
        records.append(
            {
                "dataset": item["dataset"],
                "private_case_id": item["private_case_id"],
                "opaque_incident_id": opaque,
                "source_selection_reason": item["selection_reason"],
                "image": str(image_path.relative_to(ROOT)),
                "manifest": str(manifest_path.relative_to(ROOT)),
                "tasks": str(task_path.relative_to(ROOT)),
                "image_sha256": _sha(png),
                "manifest_sha256": _sha(_json(manifest)),
                "tasks_sha256": _sha(_json(tasks)),
                "n_tasks": len(tasks),
                "contains_root_cause_question": False,
            }
        )
    roster = {
        "schema_version": GROUNDING_SCHEMA_VERSION,
        "scope": "development_only_nonconfirmatory",
        "source_roster": (
            "RQs/RQ0/results/rq0_equal_information_equal_compute_v1/"
            "qualification_visual_qa/visual_qa_roster.json"
        ),
        "renderer_preset": "rq0_v6",
        "renderer_version": 6,
        "conditions": list(CONDITIONS),
        "n_cases": len(records),
        "tasks_per_case": 7,
        "records": records,
    }
    roster["roster_sha256"] = _sha(_json(roster))
    root.mkdir(parents=True, exist_ok=True)
    (root / "task_roster.json").write_text(
        json.dumps(roster, indent=2, ensure_ascii=False) + "\n"
    )
    return roster


def _load_artifacts(limit: int | None = None) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
    roster_path = _artifact_root() / "task_roster.json"
    roster = json.loads(roster_path.read_text()) if roster_path.is_file() else prepare_artifacts()
    records = roster["records"][:limit] if limit else roster["records"]
    compiled = []
    for item in records:
        png = (ROOT / item["image"]).read_bytes()
        tasks = json.loads((ROOT / item["tasks"]).read_text())
        if _sha(png) != item["image_sha256"] or _sha(_json(tasks)) != item["tasks_sha256"]:
            raise RuntimeError(f"frozen grounding artifact changed for {item['opaque_incident_id']}")
        compiled.append({**item, "png": png, "task_records": tasks})
    return roster, compiled


def _donors(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    mapping = {}
    for dataset in sorted({item["dataset"] for item in records}):
        local = [item for item in records if item["dataset"] == dataset]
        if len(local) < 2:
            local = records
        ordered = sorted(local, key=lambda item: item["opaque_incident_id"])
        for index, item in enumerate(ordered):
            mapping[item["opaque_incident_id"]] = ordered[(index + 1) % len(ordered)]
    return mapping


def _condition_order(opaque_id: str) -> tuple[str, str, str]:
    return ORDERS[int(hashlib.sha256(opaque_id.encode()).hexdigest(), 16) % len(ORDERS)]


def _read_episodes(path: Path) -> List[Dict[str, Any]]:
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(errors="replace").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("record_type") == "episode":
            rows.append(record)
    return rows


def _conversation(
    item: Dict[str, Any],
    condition: str,
    donor: Dict[str, Any] | None,
    built: Dict[str, Any],
    response: str,
    result: Dict[str, Any],
) -> str:
    user_parts = []
    for part in built["parts"]:
        if part["type"] == "image":
            reference = donor["image"] if donor else item["image"]
            user_parts.append(f"[image: {reference}]")
        else:
            user_parts.append(part["text"])
    return (
        f"# Atomic visual grounding — {item['opaque_incident_id']} — {condition}\n\n"
        f"Private development case id: `{item['private_case_id']}`\n\n"
        "## System\n\n"
        + built["system"]
        + "\n\n## User\n\n"
        + "\n\n".join(user_parts)
        + "\n\n## Assistant\n\n"
        + (response or "[no response]")
        + "\n\n## Result\n\n```json\n"
        + json.dumps(result, indent=2, ensure_ascii=False, default=str)
        + "\n```\n"
    )


def _summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "schema_version": GROUNDING_SCHEMA_VERSION,
        "scope": "development_only_nonconfirmatory",
        "n_calls": len(rows),
        "conditions": {},
    }
    for condition in CONDITIONS:
        selected = [row for row in rows if row["condition"] == condition]
        tasks = [task for row in selected for task in row.get("task_scores", [])]
        by_category = {}
        for category in sorted({task["category"] for task in tasks}):
            local = [task for task in tasks if task["category"] == category]
            by_category[category] = {
                "n": len(local),
                "accuracy": sum(bool(task["correct"]) for task in local) / len(local),
            }
        summary["conditions"][condition] = {
            "n_calls": len(selected),
            "parse_rate": (
                sum(bool(row.get("parse_ok")) for row in selected) / len(selected)
                if selected else None
            ),
            "answer_completion_rate": (
                sum(int(row.get("n_answered") or 0) for row in selected)
                / sum(int(row.get("n_tasks") or 0) for row in selected)
                if selected else None
            ),
            "task_accuracy": (
                sum(bool(task["correct"]) for task in tasks) / len(tasks) if tasks else None
            ),
            "by_category": by_category,
            "avg_input_tokens": (
                sum(int(row.get("input_tokens") or 0) for row in selected) / len(selected)
                if selected else None
            ),
            "avg_output_tokens": (
                sum(int(row.get("output_tokens") or 0) for row in selected) / len(selected)
                if selected else None
            ),
            "avg_wall_time_s": (
                sum(float(row.get("wall_time_s") or 0) for row in selected) / len(selected)
                if selected else None
            ),
            "infrastructure_failures": sum(
                row.get("status") == "infrastructure_failure" for row in selected
            ),
            "truncations": sum(bool(row.get("truncated")) for row in selected),
        }
    actual = summary["conditions"]["actual_image"].get("task_accuracy")
    swapped = summary["conditions"]["swapped_image"].get("task_accuracy")
    no_image = summary["conditions"]["no_image"].get("task_accuracy")
    summary["diagnostic_deltas"] = {
        "actual_minus_swapped": actual - swapped if actual is not None and swapped is not None else None,
        "actual_minus_no_image": actual - no_image if actual is not None and no_image is not None else None,
        "multiple_choice_random_chance": 0.25,
    }
    summary["rca_metrics_applicable"] = False
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="mock")
    parser.add_argument("--replicate", default="main")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--max-consecutive-infrastructure-failures", type=int, default=3)
    args = parser.parse_args()

    if args.prepare_only:
        roster = prepare_artifacts()
        print(json.dumps({"n_cases": roster["n_cases"], "roster_sha256": roster["roster_sha256"]}, indent=2))
        return

    roster, records = _load_artifacts(args.limit)
    donors = _donors(records)
    model_cfg = get_config(args.model)
    run_dir = ROOT / "RQs/RQ0/results" / EXPERIMENT / f"{args.model}__development__{args.replicate}"
    trajectory = run_dir / "trajectories" / "episodes.jsonl"
    detailed = run_dir / "logs" / "detailed.jsonl"
    brief = run_dir / "logs" / "brief.log"
    existing = _read_episodes(trajectory)
    completed = {(row["opaque_incident_id"], row["condition"]) for row in existing}
    total = len(records) * len(CONDITIONS)
    run_dir.mkdir(parents=True, exist_ok=True)

    if not trajectory.exists():
        header = {
            "record_type": "header",
            "schema_version": GROUNDING_SCHEMA_VERSION,
            "experiment": EXPERIMENT,
            "scope": "development_only_nonconfirmatory",
            "model": args.model,
            "replicate": args.replicate,
            "requested_cases": len(records),
            "requested_calls": total,
            "conditions": list(CONDITIONS),
            "model_config": asdict(model_cfg),
            "task_roster_sha256": roster["roster_sha256"],
            "runner_sha256": _sha(Path(__file__)),
            "grounding_builder_sha256": _sha(
                ROOT / "RQs" / "vlmrca" / "rq0" / "grounding.py"
            ),
            "gpu_memory_utilization": 0.65,
            "rca_metrics_applicable": False,
        }
        _write_text(trajectory, json.dumps(header, ensure_ascii=False, default=str) + "\n")
        _write_text(detailed, json.dumps({"event": "run_start", **header}, ensure_ascii=False) + "\n")
        _write_text(brief, f"start model={args.model} requested={total}\n")

    writer = AsyncArtifactWriter()
    seen = len(completed)
    consecutive_infra = 0
    progress_lock = threading.Lock()
    try:
        for item in records:
            opaque = item["opaque_incident_id"]
            donor = donors[opaque]
            for condition in _condition_order(opaque):
                if (opaque, condition) in completed:
                    continue
                image_bytes = (
                    item["png"] if condition == "actual_image"
                    else donor["png"] if condition == "swapped_image"
                    else None
                )
                built = build_grounding_prompt(image_bytes, item["task_records"])
                preflight = count_vllm_prompt_tokens(
                    built["parts"], model_cfg, built["system"], text_only=False
                )
                text_preflight = count_vllm_prompt_tokens(
                    built["parts"], model_cfg, built["system"], text_only=True
                )
                started = time.time()
                response_text = ""
                error = None
                input_tokens = output_tokens = 0
                finish_reason = None
                with GPUMonitor() as gpu:
                    try:
                        response = call_vlm(
                            built["parts"], model=model_cfg, system=built["system"]
                        )
                        response_text = response.text
                        input_tokens = response.input_tokens
                        output_tokens = response.output_tokens
                        finish_reason = (response.raw or {}).get("finish_reason")
                    except Exception as exc:  # noqa: BLE001
                        error = f"{type(exc).__name__}: {exc}"
                answers = parse_grounding_answers(response_text)
                scores = score_grounding_answers(item["task_records"], answers)
                truncated = finish_reason in {"length", "max_tokens"}
                status = (
                    "infrastructure_failure" if error
                    else "model_truncation" if truncated
                    else "model_parse_failure" if not answers
                    else "success"
                )
                row = {
                    "record_type": "episode",
                    "schema_version": GROUNDING_SCHEMA_VERSION,
                    "scope": "development_only_nonconfirmatory",
                    "model": args.model,
                    "replicate": args.replicate,
                    "dataset": item["dataset"],
                    "case_id": item["private_case_id"],
                    "opaque_incident_id": opaque,
                    "condition": condition,
                    "condition_order": list(_condition_order(opaque)),
                    "donor_opaque_incident_id": (
                        donor["opaque_incident_id"] if condition == "swapped_image" else None
                    ),
                    "status": status,
                    "error": error,
                    "parse_ok": bool(answers) and not error,
                    "truncated": truncated,
                    "finish_reason": finish_reason,
                    "answers": answers,
                    "n_tasks": scores["n_tasks"],
                    "n_answered": scores["n_answered"],
                    "n_correct": scores["n_correct"],
                    "accuracy": scores["accuracy"],
                    "task_scores": scores["tasks"],
                    "input_tokens": input_tokens,
                    "preflight_input_tokens": preflight,
                    "text_input_tokens": text_preflight,
                    "image_input_tokens": (
                        preflight - text_preflight
                        if preflight is not None and text_preflight is not None
                        else None
                    ),
                    "server_token_count_match": (
                        input_tokens == preflight if preflight is not None and input_tokens else None
                    ),
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens,
                    "wall_time_s": round(time.time() - started, 6),
                    **gpu.summary(),
                    "question_bundle_sha256": item["tasks_sha256"],
                    "image_sha256": _sha(image_bytes) if image_bytes is not None else None,
                    "response": response_text,
                }
                writer.jsonl(trajectory, row)
                writer.jsonl(detailed, {"event": "call_complete", **row})
                image_source = donor if condition == "swapped_image" else None
                conversation_path = run_dir / "conversations" / f"{opaque}__{condition}.md"
                writer.text(
                    conversation_path,
                    _conversation(item, condition, image_source, built, response_text, row),
                )
                existing.append(row)
                with progress_lock:
                    seen += 1
                    pct = seen / total
                    print(json.dumps({
                        "progress": f"{seen}/{total}",
                        "condition": condition,
                        "opaque_incident_id": opaque,
                        "status": status,
                        "task_accuracy": scores["accuracy"],
                    }), flush=True)
                    # With 36 calls, every two completions is roughly one 5% step.
                    if seen == total or seen % max(1, round(total * 0.05)) == 0:
                        running_tasks = [
                            task for value in existing for task in value.get("task_scores", [])
                        ]
                        running_accuracy = (
                            sum(bool(task["correct"]) for task in running_tasks) / len(running_tasks)
                            if running_tasks else 0.0
                        )
                        writer.text(
                            brief,
                            f"progress={seen}/{total} ({pct:.1%}) "
                            f"task_accuracy={running_accuracy:.4f} status={status}\n",
                            True,
                        )
                if status == "infrastructure_failure":
                    consecutive_infra += 1
                    if consecutive_infra >= args.max_consecutive_infrastructure_failures:
                        raise RuntimeError(error)
                else:
                    consecutive_infra = 0
    finally:
        writer.close()

    rows = _read_episodes(trajectory)
    summary = _summarize(rows)
    summary.update({
        "model": args.model,
        "replicate": args.replicate,
        "requested_calls": total,
        "complete": len(rows) == total,
        "task_roster_sha256": roster["roster_sha256"],
    })
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
