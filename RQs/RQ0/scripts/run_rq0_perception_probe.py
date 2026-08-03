#!/usr/bin/env python3
"""Development-only image-swap and image/text-order probes for RQ0.

These diagnostics are deliberately excluded from confirmatory metrics. They
test whether a model responds to the visual channel and whether the registered
image-first ordering is unusually order-sensitive without changing any formal
artifact, roster, prompt, or decision rule.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

from RQs.RQ0.scripts.run_rq0 import GPUMonitor
from vlmrca.eval.run_experiment import score_prediction
from vlmrca.processed import load_processed_case
from vlmrca.render.dashboard import CaseRenderView, compile_dashboard
from vlmrca.render.presets import make_dashboard_config
from vlmrca.rq0.evidence import build_canonical_evidence, build_rq0_prompt
from vlmrca.upstream import parse_answer
from vlmrca.vlm.client import call_vlm, count_vllm_prompt_tokens
from vlmrca.vlm.configs import get_config

ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = "rq0_equal_information_equal_compute_v1"
CONDITIONS = (
    "registered_image_first",
    "same_image_text_first",
    "swapped_image_first",
)


def _sha(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode()
    return hashlib.sha256(value).hexdigest()


def _read_rows(path: Path) -> List[Dict[str, Any]]:
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text().splitlines():
        record = json.loads(line)
        if record.get("record_type") == "episode":
            rows.append(record)
    return rows


def _write(path: Path, record: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        handle.flush()


def _summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "scope": "development_only_nonconfirmatory",
        "n_calls": len(rows),
        "conditions": {},
    }
    for condition in CONDITIONS:
        selected = [row for row in rows if row["condition"] == condition]
        summary["conditions"][condition] = {
            "n": len(selected),
            "parse_rate": (
                sum(bool(row["parse_ok"]) for row in selected) / len(selected)
                if selected
                else None
            ),
            "mrr": (
                sum(float(row["mrr"]) for row in selected) / len(selected)
                if selected
                else None
            ),
            "ac1": (
                sum(float(row["ac1"]) for row in selected) / len(selected)
                if selected
                else None
            ),
        }

    indexed = {
        (row["case_id"], row["condition"]): row
        for row in rows
        if row.get("status") != "infrastructure_failure"
    }
    for comparator in ("same_image_text_first", "swapped_image_first"):
        pairs = []
        for (case_id, condition), left in indexed.items():
            if condition != "registered_image_first":
                continue
            right = indexed.get((case_id, comparator))
            if right:
                pairs.append((left, right))
        summary[f"registered_vs_{comparator}"] = {
            "n_paired": len(pairs),
            "top_rank_exact_agreement": (
                sum(
                    (left.get("predicted") or [None])[0]
                    == (right.get("predicted") or [None])[0]
                    for left, right in pairs
                )
                / len(pairs)
                if pairs
                else None
            ),
            "full_ranking_exact_agreement": (
                sum(left.get("predicted") == right.get("predicted") for left, right in pairs)
                / len(pairs)
                if pairs
                else None
            ),
            "response_exact_agreement": (
                sum(left.get("response") == right.get("response") for left, right in pairs)
                / len(pairs)
                if pairs
                else None
            ),
            "mean_delta_mrr_comparator_minus_registered": (
                sum(float(right["mrr"]) - float(left["mrr"]) for left, right in pairs)
                / len(pairs)
                if pairs
                else None
            ),
        }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--replicate", default="main")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    source = json.loads(
        (
            ROOT
            / "RQs/RQ0/results"
            / EXPERIMENT
            / "qualification_visual_qa"
            / "visual_qa_roster.json"
        ).read_text()
    )["records"]
    if args.limit:
        source = source[: args.limit]
    if len(source) < 2:
        raise RuntimeError("perception probe needs at least two development cases")

    cfg = make_dashboard_config("rq0_v6")
    model_cfg = get_config(args.model)
    run_dir = (
        ROOT
        / "RQs/RQ0/results"
        / EXPERIMENT
        / f"{args.model}__development__perception_{args.replicate}"
    )
    trajectory = run_dir / "trajectories" / "episodes.jsonl"
    existing = _read_rows(trajectory)
    completed = {(row["case_id"], row["condition"]) for row in existing}

    if not trajectory.exists():
        _write(
            trajectory,
            {
                "record_type": "header",
                "scope": "development_only_nonconfirmatory",
                "model": args.model,
                "replicate": args.replicate,
                "requested_cases": len(source),
                "requested_calls": len(source) * len(CONDITIONS),
                "model_config": asdict(model_cfg),
                "dashboard_config": asdict(cfg),
                "selection_roster": "qualification_visual_qa/visual_qa_roster.json",
            },
        )

    compiled: Dict[str, Dict[str, Any]] = {}
    for item in source:
        case = load_processed_case(item["dataset"], item["private_case_id"])
        png, manifest = compile_dashboard(CaseRenderView.from_case(case), cfg)
        compiled[item["private_case_id"]] = {
            "case": case,
            "png": png,
            "ceb": build_canonical_evidence(manifest),
            "dataset": item["dataset"],
        }

    # Swap only within a dataset so source-domain visual style is held fixed.
    donors: Dict[str, str] = {}
    for dataset in sorted({item["dataset"] for item in source}):
        ids = [item["private_case_id"] for item in source if item["dataset"] == dataset]
        if len(ids) == 1:
            # A global donor is only used for an explicitly shortened debug run.
            ids = [item["private_case_id"] for item in source]
        for index, case_id in enumerate(ids):
            donors[case_id] = ids[(index + 1) % len(ids)]

    calls_seen = len(completed)
    calls_total = len(source) * len(CONDITIONS)
    for item in source:
        case_id = item["private_case_id"]
        current = compiled[case_id]
        donor_id = donors[case_id]
        donor = compiled[donor_id]
        registered = build_rq0_prompt(
            current["ceb"], current["png"], "visual_text_topology"
        )
        condition_parts = {
            "registered_image_first": registered["parts"],
            "same_image_text_first": [
                registered["parts"][1],
                registered["parts"][0],
                registered["parts"][2],
            ],
            "swapped_image_first": build_rq0_prompt(
                current["ceb"], donor["png"], "visual_text_topology"
            )["parts"],
        }
        for condition in CONDITIONS:
            if (case_id, condition) in completed:
                continue
            parts = condition_parts[condition]
            preflight = count_vllm_prompt_tokens(
                parts, model_cfg, registered["system"], text_only=False
            )
            started = time.time()
            response_text = ""
            error = None
            input_tokens = output_tokens = 0
            finish_reason = None
            with GPUMonitor() as gpu:
                try:
                    response = call_vlm(
                        parts, model=model_cfg, system=registered["system"]
                    )
                    response_text = response.text
                    input_tokens = response.input_tokens
                    output_tokens = response.output_tokens
                    finish_reason = (response.raw or {}).get("finish_reason")
                except Exception as exc:  # noqa: BLE001
                    error = f"{type(exc).__name__}: {exc}"
            predicted = parse_answer(response_text) if response_text else []
            scores = score_prediction(predicted, current["case"])
            truncated = finish_reason in {"length", "max_tokens"}
            status = (
                "infrastructure_failure"
                if error
                else "model_truncation"
                if truncated
                else "model_parse_failure"
                if not predicted
                else "success"
            )
            image_bytes = (
                donor["png"] if condition == "swapped_image_first" else current["png"]
            )
            row = {
                "record_type": "episode",
                "scope": "development_only_nonconfirmatory",
                "model": args.model,
                "replicate": args.replicate,
                "dataset": current["dataset"],
                "case_id": case_id,
                "opaque_incident_id": current["ceb"]["opaque_incident_id"],
                "condition": condition,
                "donor_case_id": donor_id if condition == "swapped_image_first" else None,
                "donor_opaque_incident_id": (
                    donor["ceb"]["opaque_incident_id"]
                    if condition == "swapped_image_first"
                    else None
                ),
                "status": status,
                "error": error,
                "parse_ok": bool(predicted) and not error,
                "truncated": truncated,
                "finish_reason": finish_reason,
                "predicted": scores["predicted"],
                "mrr": scores["mrr"],
                "ac1": scores["ac1"],
                "input_tokens": input_tokens,
                "preflight_input_tokens": preflight,
                "server_token_count_match": (
                    input_tokens == preflight if preflight is not None and input_tokens else None
                ),
                "output_tokens": output_tokens,
                "wall_time_s": round(time.time() - started, 6),
                **gpu.summary(),
                "ceb_hash": current["ceb"]["ceb_hash"],
                "image_sha256": _sha(image_bytes),
                "response": response_text,
            }
            _write(trajectory, row)
            existing.append(row)
            calls_seen += 1
            print(
                json.dumps(
                    {
                        "progress": f"{calls_seen}/{calls_total}",
                        "dataset": current["dataset"],
                        "opaque_incident_id": current["ceb"]["opaque_incident_id"],
                        "condition": condition,
                        "status": status,
                    }
                ),
                flush=True,
            )
            if status == "infrastructure_failure":
                raise RuntimeError(error)

    summary = _summarize(existing)
    (run_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
