"""One-off CPU gallery; no model calls or experiment result writes."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import pickle
import shutil

from renderer.exps import export_public_case
from renderer.main import render
from renderer.utils import write
from RQs.RQ3_8.src.exps import fixed_slot_design


ROOT = Path(__file__).resolve().parents[2]
PREP = ROOT / "RQs/RQ3_8/preparation"
STAGING = ROOT / "build/renderer_previews/rq38_gallery_v5_generated"
DEST = Path("/mnt/c/Users/10511/Downloads/例图")
DATASETS = ("aegislab", "aiops2022", "aiops2025", "re2_ob", "re2_tt")
ARMS = ("FULL", "MR00", "MR10", "MR01", "NO_LOG", "NO_ONSET")
ANCHORS = {"aegislab": "INC-01BF937825D4",
           "aiops2022": "INC-0060628741E9",
           "aiops2025": "INC-03A46BA87920"}


def selected_rows():
    roster = json.loads((PREP / "ops_components_v2/roster.json").read_text())["cases"]
    selected = []
    for dataset in DATASETS:
        rows = [r for r in roster if r["dataset"] == dataset]
        rows.sort(key=lambda r: hashlib.sha256(
            ("rq38-gallery-v5:" + r["opaque_incident_id"]).encode()).hexdigest())
        anchor = ANCHORS.get(dataset)
        chosen = []
        if anchor:
            chosen.append(next(r for r in rows if r["opaque_incident_id"] == anchor))
        chosen.extend(r for r in rows if r["opaque_incident_id"] != anchor)
        selected.extend(chosen[:5])
    if len(selected) != 25 or len({r["opaque_incident_id"] for r in selected}) != 25:
        raise ValueError("Gallery selection is not exactly five distinct cases per dataset")
    return selected


def generate_case(row):
    oid = row["opaque_incident_id"]
    provenance = json.loads((PREP / "export_v1/audit" / (oid + ".json")).read_text())
    source = Path(provenance["source_context"])
    evidence, _ = export_public_case(row, pickle.loads(source.read_bytes()), source)
    records = []
    for arm in ARMS:
        selected, design = fixed_slot_design(evidence, arm)
        inputs = STAGING / "inputs" / oid / arm
        inputs.mkdir(parents=True, exist_ok=True)
        write(inputs / "evidence.json", selected)
        write(inputs / "design.json", design)
        output = STAGING / "renders" / oid / arm
        report = render(inputs / "evidence.json", inputs / "design.json", output)
        png = output / "dashboard.png"
        if report["status"] != "passed" or not png.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError(f"Invalid render: {oid} {arm}")
        records.append((row["dataset"], arm, oid, png))
    return records


def main():
    if any(DEST.iterdir()):
        raise ValueError("Windows gallery must be empty before this replacement")
    if STAGING.exists():
        raise ValueError("Staging gallery already exists; do not reuse stale renders")
    STAGING.mkdir(parents=True)
    rows = selected_rows()
    records = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(generate_case, row): row for row in rows}
        for future in as_completed(futures):
            group = future.result()
            records.extend(group)
            row = futures[future]
            print(f"rendered {row['dataset']} {row['opaque_incident_id']} ({len(records)}/150)", flush=True)
    if len(records) != 150:
        raise ValueError("Incomplete gallery")
    for dataset, arm, oid, png in records:
        target = DEST / dataset / arm
        target.mkdir(parents=True, exist_ok=True)
        shutil.copy2(png, target / (oid + ".png"))
    print(f"copied {len(records)} new PNGs to {DEST}", flush=True)


if __name__ == "__main__":
    main()
