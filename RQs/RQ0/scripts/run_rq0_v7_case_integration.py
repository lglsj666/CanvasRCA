#!/usr/bin/env python3
"""Paired development RCA test of renderer-v6 versus the v7 edge-key candidate."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import time
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

from PIL import Image

from RQs.RQ0.scripts.run_rq0 import GPUMonitor, _conversation
from RQs.RQ0.scripts.run_rq0_atomic_grounding import AsyncArtifactWriter
from vlmrca.eval.run_experiment import score_prediction
from vlmrca.processed import load_processed_case
from vlmrca.render.dashboard import CaseRenderView, compile_dashboard
from vlmrca.render.presets import make_dashboard_config
from vlmrca.rq0.evidence import (
    build_canonical_evidence,
    build_rq0_prompt,
    representation_audit,
)
from vlmrca.upstream import parse_answer
from vlmrca.vlm.client import call_vlm, count_vllm_prompt_tokens
from vlmrca.vlm.configs import get_config

ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = "rq0_v7_edge_key_case_integration_v1"
SOURCE_ROSTER = (
    ROOT
    / "RQs/RQ0/results/rq0_equal_information_equal_compute_v1/qualification_visual_qa/visual_qa_roster.json"
)
CONDITIONS = ("v6_curved", "v7_large_edge_key")


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()


def _sha(value: bytes | str) -> str:
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def _write_jsonl(path: Path, record: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        handle.flush()


def _append(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text)
        handle.flush()


def _episodes(path: Path) -> List[Dict[str, Any]]:
    if not path.is_file():
        return []
    return [
        record
        for line in path.read_text().splitlines()
        if (record := json.loads(line)).get("record_type") == "episode"
    ]


def condition_order(opaque_id: str) -> tuple[str, str]:
    value = int(hashlib.sha256(f"{opaque_id}:v7-order".encode()).hexdigest(), 16)
    return CONDITIONS if value % 2 == 0 else tuple(reversed(CONDITIONS))


def _same_base_pixels(v6: bytes, v7: bytes) -> bool:
    with Image.open(io.BytesIO(v6)) as left:
        with Image.open(io.BytesIO(v7)) as right:
            left_rgb = left.convert("RGB")
            crop = right.convert("RGB").crop((0, 0, left.width, left.height))
            return left_rgb.size == crop.size and left_rgb.tobytes() == crop.tobytes()


def prepare_artifacts() -> Dict[str, Any]:
    source = json.loads(SOURCE_ROSTER.read_text())["records"]
    output = ROOT / "RQs/RQ0/results" / EXPERIMENT / "artifacts"
    v6_cfg = make_dashboard_config("rq0_v6")
    v7_cfg = make_dashboard_config("rq0_v7_edge_key")
    records = []
    for item in source:
        case = load_processed_case(item["dataset"], item["private_case_id"])
        view = CaseRenderView.from_case(case)
        v6_png, v6_manifest = compile_dashboard(view, v6_cfg)
        v7_png, v7_manifest = compile_dashboard(view, v7_cfg)
        v6_ceb = build_canonical_evidence(v6_manifest)
        v7_ceb = build_canonical_evidence(v7_manifest)
        v6_audit = representation_audit(v6_ceb)
        v7_audit = representation_audit(v7_ceb)
        if not (v6_audit["parity_ok"] and v7_audit["parity_ok"]):
            raise RuntimeError(f"representation parity failed for {item['opaque_incident_id']}")
        if v6_ceb["atomic_fact_inventory_hash"] != v7_ceb["atomic_fact_inventory_hash"]:
            raise RuntimeError(f"v6/v7 atomic facts differ for {item['opaque_incident_id']}")
        if not _same_base_pixels(v6_png, v7_png):
            raise RuntimeError(f"v7 changed base dashboard pixels for {item['opaque_incident_id']}")
        opaque = item["opaque_incident_id"]
        case_root = output / opaque
        files = {
            "v6_image": case_root / "v6.png",
            "v7_image": case_root / "v7.png",
            "v6_manifest": case_root / "v6.manifest.json",
            "v7_manifest": case_root / "v7.manifest.json",
            "ceb": case_root / "common.ceb.json",
            "audit": case_root / "common.audit.json",
        }
        case_root.mkdir(parents=True, exist_ok=True)
        files["v6_image"].write_bytes(v6_png)
        files["v7_image"].write_bytes(v7_png)
        files["v6_manifest"].write_text(
            json.dumps(v6_manifest, indent=2, ensure_ascii=False) + "\n"
        )
        files["v7_manifest"].write_text(
            json.dumps(v7_manifest, indent=2, ensure_ascii=False) + "\n"
        )
        files["ceb"].write_text(json.dumps(v6_ceb, indent=2, ensure_ascii=False) + "\n")
        files["audit"].write_text(
            json.dumps(v6_audit, indent=2, ensure_ascii=False) + "\n"
        )
        records.append(
            {
                "dataset": item["dataset"],
                "private_case_id": item["private_case_id"],
                "opaque_incident_id": opaque,
                "selection_reason": item["selection_reason"],
                **{name: str(path.relative_to(ROOT)) for name, path in files.items()},
                "v6_image_sha256": _sha(v6_png),
                "v7_image_sha256": _sha(v7_png),
                "ceb_sha256": _sha(_canonical(v6_ceb)),
                "fact_inventory_hash": v6_ceb["atomic_fact_inventory_hash"],
                "base_pixels_identical": True,
                "atomic_facts_identical": True,
            }
        )
    roster = {
        "schema_version": "RQ0V7EdgeKeyCaseIntegrationV1",
        "scope": "development_only_nonconfirmatory_renderer_intervention",
        "source_roster": str(SOURCE_ROSTER.relative_to(ROOT)),
        "n_cases": len(records),
        "conditions": list(CONDITIONS),
        "v6_config": asdict(v6_cfg),
        "v7_config": asdict(v7_cfg),
        "common_text_source": "v6 CanonicalEvidenceBundle; byte-identical across conditions",
        "records": records,
    }
    roster["roster_sha256"] = _sha(_canonical(roster))
    output.mkdir(parents=True, exist_ok=True)
    (output / "artifact_roster.json").write_text(
        json.dumps(roster, indent=2, ensure_ascii=False) + "\n"
    )
    return roster


def _load_artifacts(limit: int | None) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
    roster_path = ROOT / "RQs/RQ0/results" / EXPERIMENT / "artifacts/artifact_roster.json"
    roster = json.loads(roster_path.read_text()) if roster_path.is_file() else prepare_artifacts()
    selected = roster["records"][:limit] if limit else roster["records"]
    records = []
    for item in selected:
        v6 = (ROOT / item["v6_image"]).read_bytes()
        v7 = (ROOT / item["v7_image"]).read_bytes()
        ceb = json.loads((ROOT / item["ceb"]).read_text())
        if (
            _sha(v6) != item["v6_image_sha256"]
            or _sha(v7) != item["v7_image_sha256"]
            or _sha(_canonical(ceb)) != item["ceb_sha256"]
        ):
            raise RuntimeError(f"frozen artifact drift for {item['opaque_incident_id']}")
        records.append({**item, "v6_png": v6, "v7_png": v7, "ceb_record": ceb})
    return roster, records


def summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "schema_version": "RQ0V7EdgeKeyCaseIntegrationV1",
        "scope": "development_only_nonconfirmatory_renderer_intervention",
        "n_calls": len(rows),
        "conditions": {},
    }
    for condition in CONDITIONS:
        selected = [row for row in rows if row["condition"] == condition]
        result["conditions"][condition] = {
            "n": len(selected),
            "parse_rate": sum(bool(row["parse_ok"]) for row in selected) / len(selected),
            "error_rate": sum(row["status"] == "infrastructure_failure" for row in selected)
            / len(selected),
            "mrr": sum(float(row["mrr"]) for row in selected) / len(selected),
            "ac1": sum(float(row["ac1"]) for row in selected) / len(selected),
            "ac3": sum(float(row["ac3"]) for row in selected) / len(selected),
            "ac5": sum(float(row["ac5"]) for row in selected) / len(selected),
            "avg3": sum(float(row["avg3"]) for row in selected) / len(selected),
            "avg5": sum(float(row["avg5"]) for row in selected) / len(selected),
            "mean_input_tokens": sum(int(row["input_tokens"]) for row in selected)
            / len(selected),
            "mean_output_tokens": sum(int(row["output_tokens"]) for row in selected)
            / len(selected),
            "mean_total_tokens": sum(int(row["total_tokens"]) for row in selected)
            / len(selected),
            "mean_wall_time_s": sum(float(row["wall_time_s"]) for row in selected)
            / len(selected),
        }
    indexed = {(row["case_id"], row["condition"]): row for row in rows}
    pairs = [
        (indexed[(case_id, CONDITIONS[0])], indexed[(case_id, CONDITIONS[1])])
        for case_id in sorted({row["case_id"] for row in rows})
        if (case_id, CONDITIONS[0]) in indexed and (case_id, CONDITIONS[1]) in indexed
    ]
    deltas = [float(v7["mrr"]) - float(v6["mrr"]) for v6, v7 in pairs]
    result["paired"] = {
        "n": len(pairs),
        "mean_delta_mrr_v7_minus_v6": sum(deltas) / len(deltas) if deltas else None,
        "improved": sum(delta > 0 for delta in deltas),
        "degraded": sum(delta < 0 for delta in deltas),
        "tied": sum(delta == 0 for delta in deltas),
        "top1_changed": sum(
            (v6.get("predicted") or [None])[0] != (v7.get("predicted") or [None])[0]
            for v6, v7 in pairs
        ),
        "status_counts": dict(sorted(Counter(row["status"] for row in rows).items())),
        "no_truncation": not any(row["truncated"] for row in rows),
        "server_token_count_match": all(
            row.get("server_token_count_match") in {True, None} for row in rows
        ),
        "prompt_text_hash_paired": all(
            v6["prompt_text_sha256"] == v7["prompt_text_sha256"] for v6, v7 in pairs
        ),
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="mock")
    parser.add_argument("--replicate", default="main")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    if args.prepare_only:
        roster = prepare_artifacts()
        print(json.dumps({"n_cases": roster["n_cases"], "roster_sha256": roster["roster_sha256"]}, indent=2))
        return

    roster, records = _load_artifacts(args.limit)
    model_cfg = get_config(args.model)
    run_dir = ROOT / "RQs/RQ0/results" / EXPERIMENT / f"{args.model}__development__{args.replicate}"
    trajectory = run_dir / "trajectories/episodes.jsonl"
    detailed = run_dir / "logs/detailed.jsonl"
    brief = run_dir / "logs/brief.log"
    existing = _episodes(trajectory)
    completed = {(row["case_id"], row["condition"]) for row in existing}
    total = len(records) * len(CONDITIONS)
    if not trajectory.is_file():
        header = {
            "record_type": "header",
            "schema_version": "RQ0V7EdgeKeyCaseIntegrationV1",
            "scope": "development_only_nonconfirmatory_renderer_intervention",
            "model": args.model,
            "replicate": args.replicate,
            "requested_cases": len(records),
            "requested_calls": total,
            "conditions": list(CONDITIONS),
            "model_config": asdict(model_cfg),
            "artifact_roster_sha256": roster["roster_sha256"],
            "gpu_memory_utilization": 0.65,
            "rca_metrics_applicable": True,
            "confirmatory": False,
        }
        _write_jsonl(trajectory, header)
        _write_jsonl(detailed, {"event": "run_start", **header})
        _append(brief, f"start model={args.model} requested={total}\n")

    seen = len(completed)
    writer = AsyncArtifactWriter()
    for item in records:
        case = load_processed_case(item["dataset"], item["private_case_id"])
        ceb = item["ceb_record"]
        images = {"v6_curved": item["v6_png"], "v7_large_edge_key": item["v7_png"]}
        builds = {
            condition: build_rq0_prompt(ceb, images[condition], "visual_text_topology")
            for condition in CONDITIONS
        }
        text_hashes = {
            condition: _sha(
                "\n".join(
                    part["text"]
                    for part in builds[condition]["parts"]
                    if part["type"] == "text"
                )
            )
            for condition in CONDITIONS
        }
        if len(set(text_hashes.values())) != 1:
            raise RuntimeError(f"condition prompt text differs for {item['opaque_incident_id']}")
        for condition in condition_order(item["opaque_incident_id"]):
            if (item["private_case_id"], condition) in completed:
                continue
            built = builds[condition]
            preflight = count_vllm_prompt_tokens(
                built["parts"], model_cfg, built["system"], text_only=False
            )
            text_tokens = count_vllm_prompt_tokens(
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
            predicted = parse_answer(response_text) if response_text else []
            scores = score_prediction(predicted, case)
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
            row = {
                "record_type": "episode",
                "schema_version": "RQ0V7EdgeKeyCaseIntegrationV1",
                "scope": "development_only_nonconfirmatory_renderer_intervention",
                "model": args.model,
                "replicate": args.replicate,
                "dataset": item["dataset"],
                "case_id": item["private_case_id"],
                "opaque_incident_id": item["opaque_incident_id"],
                "ground_truth": case.ground_truth,
                "fault_type": case.fault_type,
                "condition": condition,
                "condition_order": condition_order(item["opaque_incident_id"]),
                "status": status,
                "error": error,
                "parse_ok": bool(predicted) and not error,
                "truncated": truncated,
                "finish_reason": finish_reason,
                **{key: value for key, value in scores.items() if key != "accepted"},
                "input_tokens": input_tokens,
                "preflight_input_tokens": preflight,
                "text_input_tokens": text_tokens,
                "image_input_tokens": (
                    preflight - text_tokens
                    if preflight is not None and text_tokens is not None
                    else None
                ),
                "server_token_count_match": (
                    input_tokens == preflight if preflight is not None and input_tokens else None
                ),
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "wall_time_s": round(time.time() - started, 6),
                **gpu.summary(),
                "ceb_hash": ceb["ceb_hash"],
                "fact_inventory_hash": ceb["atomic_fact_inventory_hash"],
                "prompt_text_sha256": text_hashes[condition],
                "image_sha256": _sha(images[condition]),
                "response": response_text,
            }
            writer.jsonl(trajectory, row)
            writer.jsonl(detailed, {"event": "call_complete", **row})
            conversation = _conversation(
                item["private_case_id"],
                item["opaque_incident_id"],
                condition,
                built,
                item["v6_image"] if condition == "v6_curved" else item["v7_image"],
                response_text,
                row,
            )
            conversation_path = run_dir / "conversations" / f"{item['opaque_incident_id']}__{condition}.md"
            conversation_path.parent.mkdir(parents=True, exist_ok=True)
            writer.text(conversation_path, conversation)
            existing.append(row)
            seen += 1
            valid = [value for value in existing if value["status"] != "infrastructure_failure"]
            writer.text(
                brief,
                (
                    f"progress={seen}/{total} condition={condition} status={status} "
                    f"AC@1={sum(value['ac1'] for value in valid) / len(valid):.4f} "
                    f"AC@3={sum(value['ac3'] for value in valid) / len(valid):.4f} "
                    f"AC@5={sum(value['ac5'] for value in valid) / len(valid):.4f} "
                    f"AVG@3={sum(value['avg3'] for value in valid) / len(valid):.4f} "
                    f"AVG@5={sum(value['avg5'] for value in valid) / len(valid):.4f} "
                    f"MRR={sum(value['mrr'] for value in valid) / len(valid):.4f}\n"
                ),
                True,
            )
            print(
                json.dumps(
                    {
                        "progress": f"{seen}/{total}",
                        "condition": condition,
                        "opaque_incident_id": item["opaque_incident_id"],
                        "status": status,
                        "mrr": scores["mrr"],
                    }
                ),
                flush=True,
            )
            if status == "infrastructure_failure":
                writer.close()
                raise RuntimeError(error)

    writer.close()
    summary = summarize(_episodes(trajectory))
    summary.update(
        {
            "model": args.model,
            "replicate": args.replicate,
            "requested_calls": total,
            "complete": len(_episodes(trajectory)) == total,
            "artifact_roster_sha256": roster["roster_sha256"],
        }
    )
    (run_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
