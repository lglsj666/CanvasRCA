#!/usr/bin/env python3
"""Evaluate an explicit directional edge-key visual variant on development data."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

from RQs.RQ0.scripts.run_rq0 import GPUMonitor
from RQs.RQ0.scripts.run_rq0_atomic_grounding import (
    CONDITIONS,
    AsyncArtifactWriter,
    _condition_order,
    _conversation,
    _json,
    _read_episodes,
    _sha,
    _summarize,
    _write_text,
)
from vlmrca.rq0.grounding import (
    build_grounding_prompt,
    parse_grounding_answers,
    score_grounding_answers,
)
from vlmrca.rq0.topology_edge_key import (
    SCHEMA_VERSION,
    SCHEMA_VERSION_LARGE,
    build_edge_key_task,
    propagation_rank_edges,
    render_topology_edge_key,
    render_topology_edge_key_large,
)
from vlmrca.vlm.client import call_vlm, count_vllm_prompt_tokens
from vlmrca.vlm.configs import get_config

ROOT = Path(__file__).resolve().parents[3]
SOURCE_EXPERIMENT = "rq0_atomic_visual_grounding_v1"
EXPERIMENT_COMPACT = "rq0_topology_edge_key_v1"
EXPERIMENT_LARGE = "rq0_topology_edge_key_v2"


def prepare_artifacts(experiment: str, variant: str) -> Dict[str, Any]:
    source = json.loads(
        (
            ROOT / "RQs/RQ0/results" / SOURCE_EXPERIMENT / "artifacts" / "task_roster.json"
        ).read_text()
    )
    output = ROOT / "RQs/RQ0/results" / experiment / "artifacts"
    records = []
    for item in source["records"]:
        png = (ROOT / item["image"]).read_bytes()
        manifest = json.loads((ROOT / item["manifest"]).read_text())
        edge_png = (
            render_topology_edge_key_large(png, manifest)
            if variant == "large"
            else render_topology_edge_key(png, manifest)
        )
        tasks = build_edge_key_task(manifest)
        opaque = item["opaque_incident_id"]
        image_path = output / "renders" / f"{opaque}.png"
        task_path = output / "tasks" / f"{opaque}.tasks.json"
        image_path.parent.mkdir(parents=True, exist_ok=True)
        task_path.parent.mkdir(parents=True, exist_ok=True)
        image_path.write_bytes(edge_png)
        task_path.write_text(json.dumps(tasks, indent=2, ensure_ascii=False) + "\n")
        edge_values = [f"{caller}→{callee}" for caller, callee in propagation_rank_edges(manifest)]
        records.append({
            "dataset": item["dataset"],
            "private_case_id": item["private_case_id"],
            "opaque_incident_id": opaque,
            "image": str(image_path.relative_to(ROOT)),
            "tasks": str(task_path.relative_to(ROOT)),
            "image_sha256": _sha(edge_png),
            "tasks_sha256": _sha(_json(tasks)),
            "edge_values": edge_values,
            "n_tasks": 1,
        })
    roster = {
        "schema_version": SCHEMA_VERSION_LARGE if variant == "large" else SCHEMA_VERSION,
        "scope": "development_only_nonconfirmatory_renderer_intervention",
        "source_roster_sha256": source["roster_sha256"],
        "visual_change": (
            "append large multi-line caller-rank to callee-rank edge key"
            if variant == "large"
            else "append compact caller-rank to callee-rank edge key"
        ),
        "variant": variant,
        "base_dashboard_pixels_unchanged": True,
        "conditions": list(CONDITIONS),
        "n_cases": len(records),
        "records": records,
    }
    roster["roster_sha256"] = _sha(_json(roster))
    output.mkdir(parents=True, exist_ok=True)
    (output / "task_roster.json").write_text(json.dumps(roster, indent=2, ensure_ascii=False) + "\n")
    return roster


def _load_artifacts(
    experiment: str, variant: str, limit: int | None
) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
    path = ROOT / "RQs/RQ0/results" / experiment / "artifacts" / "task_roster.json"
    roster = (
        json.loads(path.read_text())
        if path.is_file()
        else prepare_artifacts(experiment, variant)
    )
    records = roster["records"][:limit] if limit else roster["records"]
    out = []
    for item in records:
        png = (ROOT / item["image"]).read_bytes()
        tasks = json.loads((ROOT / item["tasks"]).read_text())
        if _sha(png) != item["image_sha256"] or _sha(_json(tasks)) != item["tasks_sha256"]:
            raise RuntimeError(f"edge-key artifact drift for {item['opaque_incident_id']}")
        out.append({**item, "png": png, "task_records": tasks})
    return roster, out


def _donors(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Prefer a same-dataset donor that does not accidentally show the answer."""
    mapping = {}
    for item in records:
        correct = item["task_records"][0]["answer_value"]
        local = sorted(
            [row for row in records if row["dataset"] == item["dataset"] and row is not item],
            key=lambda row: row["opaque_incident_id"],
        )
        if not local:
            local = [row for row in records if row is not item]
        valid = [
            row for row in local
            if (
                correct not in row["edge_values"]
                if correct != "none among shown services"
                else bool(row["edge_values"])
            )
        ]
        mapping[item["opaque_incident_id"]] = (valid or local)[0]
    return mapping


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="mock")
    parser.add_argument("--replicate", default="main")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--variant", choices=("compact", "large"), default="compact")
    args = parser.parse_args()
    experiment = EXPERIMENT_LARGE if args.variant == "large" else EXPERIMENT_COMPACT
    schema_version = SCHEMA_VERSION_LARGE if args.variant == "large" else SCHEMA_VERSION
    if args.prepare_only:
        roster = prepare_artifacts(experiment, args.variant)
        print(json.dumps({"n_cases": roster["n_cases"], "roster_sha256": roster["roster_sha256"]}, indent=2))
        return

    roster, records = _load_artifacts(experiment, args.variant, args.limit)
    donors = _donors(records)
    model_cfg = get_config(args.model)
    run_dir = ROOT / "RQs/RQ0/results" / experiment / f"{args.model}__development__{args.replicate}"
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
            "schema_version": schema_version,
            "experiment": experiment,
            "scope": "development_only_nonconfirmatory_renderer_intervention",
            "model": args.model,
            "replicate": args.replicate,
            "requested_cases": len(records),
            "requested_calls": total,
            "conditions": list(CONDITIONS),
            "model_config": asdict(model_cfg),
            "task_roster_sha256": roster["roster_sha256"],
            "gpu_memory_utilization": 0.65,
            "rca_metrics_applicable": False,
        }
        _write_text(trajectory, json.dumps(header, ensure_ascii=False, default=str) + "\n")
        _write_text(detailed, json.dumps({"event": "run_start", **header}, ensure_ascii=False) + "\n")
        _write_text(brief, f"start model={args.model} requested={total}\n")

    writer = AsyncArtifactWriter()
    seen = len(completed)
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
                        response = call_vlm(built["parts"], model=model_cfg, system=built["system"])
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
                    "schema_version": schema_version,
                    "scope": "development_only_nonconfirmatory_renderer_intervention",
                    "model": args.model,
                    "replicate": args.replicate,
                    "dataset": item["dataset"],
                    "case_id": item["private_case_id"],
                    "opaque_incident_id": opaque,
                    "condition": condition,
                    "condition_order": list(_condition_order(opaque)),
                    "donor_opaque_incident_id": donor["opaque_incident_id"] if condition == "swapped_image" else None,
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
                    "image_input_tokens": preflight - text_preflight if preflight is not None and text_preflight is not None else None,
                    "server_token_count_match": input_tokens == preflight if preflight is not None and input_tokens else None,
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
                writer.text(
                    run_dir / "conversations" / f"{opaque}__{condition}.md",
                    _conversation(
                        item,
                        condition,
                        donor if condition == "swapped_image" else None,
                        built,
                        response_text,
                        row,
                    ),
                )
                existing.append(row)
                seen += 1
                writer.text(
                    brief,
                    f"progress={seen}/{total} ({seen / total:.1%}) "
                    f"accuracy={scores['accuracy']:.4f} status={status}\n",
                    True,
                )
                print(json.dumps({
                    "progress": f"{seen}/{total}",
                    "condition": condition,
                    "opaque_incident_id": opaque,
                    "status": status,
                    "correct": bool(scores["n_correct"]),
                }), flush=True)
                if status == "infrastructure_failure":
                    raise RuntimeError(error)
    finally:
        writer.close()

    summary = _summarize(_read_episodes(trajectory))
    summary.update({
        "schema_version": schema_version,
        "scope": "development_only_nonconfirmatory_renderer_intervention",
        "model": args.model,
        "replicate": args.replicate,
        "requested_calls": total,
        "complete": len(_read_episodes(trajectory)) == total,
        "task_roster_sha256": roster["roster_sha256"],
    })
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
