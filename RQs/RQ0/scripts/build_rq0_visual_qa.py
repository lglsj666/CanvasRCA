#!/usr/bin/env python3
"""Build the registered 12-case development gallery for manual visual QA."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from vlmrca.processed import load_processed_case, processed_index
from vlmrca.render.dashboard import CaseRenderView, compile_dashboard
from vlmrca.render.presets import make_dashboard_config
from vlmrca.rq0.evidence import build_canonical_evidence

ROOT = Path(__file__).resolve().parents[3]
OUT = (
    ROOT
    / "RQs/RQ0/results"
    / "rq0_equal_information_equal_compute_v1"
    / "qualification_visual_qa"
)


def _select(dataset: str, development: List[str]) -> List[Dict[str, Any]]:
    rows = [processed_index(dataset)[case_id] for case_id in development]
    criteria = (
        ("fewest_metric_rows", lambda row: (row.get("metrics_rows", 0), row["case_id"])),
        ("fewest_trace_rows", lambda row: (row.get("traces_rows", 0), row["case_id"])),
        ("fewest_log_rows", lambda row: (row.get("logs_rows", 0), row["case_id"])),
        ("densest_topology", lambda row: (-row.get("graph_edges", 0), row["case_id"])),
    )
    selected = []
    used = set()
    for reason, key in criteria:
        candidates = [row for row in rows if row["case_id"] not in used]
        row = sorted(candidates, key=key)[0]
        used.add(row["case_id"])
        selected.append({"reason": reason, **row})
    return selected


def main() -> None:
    roster = json.loads(
        (ROOT / "RQs" / "RQ0" / "configs" / "partition_roster.json").read_text()
    )
    cfg = make_dashboard_config("rq0_v6")
    records = []
    images = OUT / "renders"
    images.mkdir(parents=True, exist_ok=True)
    for dataset in ("aegislab", "aiops2022", "aiops2025"):
        chosen = _select(dataset, roster["partitions"]["development"][dataset])
        for item in chosen:
            case = load_processed_case(dataset, item["case_id"])
            png, manifest = compile_dashboard(CaseRenderView.from_case(case), cfg)
            ceb = build_canonical_evidence(manifest)
            image_path = images / f"{dataset}__{item['reason']}__{ceb['opaque_incident_id']}.png"
            image_path.write_bytes(png)
            records.append(
                {
                    "dataset": dataset,
                    "private_case_id": item["case_id"],
                    "opaque_incident_id": ceb["opaque_incident_id"],
                    "selection_reason": item["reason"],
                    "fault_type_for_development_coverage_only": item.get("fault_type"),
                    "graph_nodes": item.get("graph_nodes"),
                    "graph_edges": item.get("graph_edges"),
                    "metrics_rows": item.get("metrics_rows"),
                    "logs_rows": item.get("logs_rows"),
                    "traces_rows": item.get("traces_rows"),
                    "metric_series_rendered": len(ceb["metric_series"]),
                    "missingness": ceb["missingness"],
                    "image": str(image_path.relative_to(ROOT)),
                    "manual_review": "pending",
                }
            )
    report = {
        "schema_version": 1,
        "renderer_preset": "rq0_v6",
        "n": len(records),
        "selection_is_development_only": True,
        "records": records,
    }
    (OUT / "visual_qa_roster.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False)
    )
    print(json.dumps({"n": len(records), "out": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
