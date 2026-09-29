"""Bind the registered SC guide calibration to actual historical requests.

Read-only toward RQ3.2. No inference, raw preparation or label-based selection.
Run as a module after scripts/env_local.sh, then register its manifest with the
RQ3.3 calibration-manifest command. A source/serializer mismatch fails closed.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import pickle
from pathlib import Path

from RQs.RQ3_1.src.renderer.contrast import project_natural_text
from RQs.RQ3_1.src.exps import sanitize_parent_calibration
from RQs.RQ3_3.src import exps, gates
from RQs.RQ3_3.src.utils import ROOT, read_json


OLD = (
    "The reference interval is the first half of the observed time range; current is its second half, "
    "not a supplied failure injection boundary. Metric baseline/current values are medians. "
    "signed robust change is the largest signed deviation from the reference median divided by 1.4826 "
    "times its median absolute deviation, floored at 0.001 of the series' largest absolute value and "
    "1e-12, and capped at ±999. Each time bin shows its largest absolute excursion from that reference, "
    "with its observed sample count; min/max summaries retain full-series extrema. The non-child "
    "wall-time proxy subtracts the union of observed direct-child intervals within the same trace. "
    "It is not measured CPU execution or waiting. log counts are observed message occurrences, "
    "not LOG-R scores. Repeated identical messages are grouped without removing diagnostic numbers."
)
AUDIT = "RQs/RQ3_3/descriptions/RQ3_3_experiments.md#sc-source-calibration-audit"
SOURCES = (
    "RQs/RQ3_2/src/selector.py", "RQs/RQ3_1/src/exps.py",
    "RQs/RQ3_1/src/renderer/contrast.py", "RQs/RQ1_1/src/renderer/kpi_select.py",
    "RQs/RQ1_1/src/renderer/panels.py", "RQs/RQ1_1/src/renderer/dashboard.py",
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def guide(facts, refs):
    groups = defaultdict(list)
    for fact in facts:
        if fact["region"] not in "MRL":
            continue
        prefix = "parent" if fact["fact_id"].startswith("SC:P0:") else "direct"
        if not fact["fact_id"].startswith(("SC:P0:", "SC:NEW:")):
            raise ValueError("unrecognized SC provenance")
        groups[(prefix, fact["region"])].append(refs[fact["fact_id"]])
    lines = [
        "Read each observation using its recorded estimator. Reference/current diagnostics use the "
        "case's public telemetry-derived analysis boundary, which need not be the midpoint and is "
        "not the private injection time. A metric's baseline field and its MET-Z regular mean are "
        "different summaries and must not be interchanged."
    ]
    descriptions = {
        ("parent", "M"): (
            "use median samples within each displayed time bin. Baseline and signed z come from the "
            "mean and spread of the leading half of source rows, with the inherited spread floors; "
            "peak is the largest deviation over the observed series. The separate MET-Z regular/current "
            "fields are means and standard deviations on the public analysis split, not medians."
        ),
        ("direct", "M"): (
            "use the reference median as baseline and report current median separately. Signed robust "
            "change uses the largest excursion over the whole observed series divided by reference MAD "
            "times 1.4826, floored at 0.001 of the largest absolute series value and 1e-12, capped at "
            "±999. Each bin keeps its largest absolute excursion and observed sample count."
        ),
        ("parent", "R"): (
            "report phase-specific span counts and p95 of parent duration minus the sum of recorded "
            "child durations matched by span identifier, clipped at zero. This estimator does not "
            "merge overlapping child intervals. Its rank score sums the positive count/latency log2 "
            "fold changes when the baseline is usable."
        ),
        ("direct", "R"): (
            "report span counts and p95 of parent duration minus the union of clipped direct-child "
            "intervals matched within the same trace. Their rank score sums absolute count/latency "
            "log2 fold changes. Counts are recorded spans, not necessarily distinct end-user requests."
        ),
        ("parent", "L"): (
            "retain normalized templates, occurrence multiplicity, diagnostic numeric previews and "
            "any explicitly supplied LOG-R statistics. Template counts and LOG-R scores are distinct."
        ),
        ("direct", "L"): (
            "group identical sanitized messages without discarding diagnostic numbers; counts are "
            "observed occurrences. A supplied log-count summary is not a LOG-R score."
        ),
    }
    for key, text in descriptions.items():
        if groups[key]:
            lines.append(", ".join(sorted(groups[key])) + " " + text)
    lines.append(
        "Both trace duration estimators are proxies, not measured CPU execution or waiting. "
        "In a count/latency log2-fold-change pair, the first number is the count change and the second "
        "is the latency change; the legacy words baseline/current on that pair do not denote two "
        "time phases. Do not subtract aggregate p95 values to infer local execution time."
    )
    return "\n".join(lines)


def audit(root):
    registration = read_json(root / "registration.json")
    models = registration["config"]["models"]
    rows = registration["rosters"]["screen"]
    ids = {r["opaque_incident_id"] for r in rows}
    historical = ROOT / "RQs/RQ3_2/results/formal_signal_cover_v2"
    source = historical / "exp_signal_selection"
    index = {}
    for path in (source / "outputs").glob("*.json"):
        value = read_json(path)
        key = value["opaque_incident_id"], value["model"]
        if key[0] not in ids or key[1] not in models or value["dimensions"]["arm"] != "SC_FULL":
            continue
        if key in index:
            raise ValueError(f"ambiguous historical SC request: {key}")
        if not (source / "completed" / path.name).is_file():
            raise ValueError(f"historical source has no completion marker: {key}")
        index[key] = source / "prompts" / path.name
    manifest = {"status": "audited", "reviewer": "Codex source audit 2026-09-23",
        "scope": "exact historical SC_FULL evidence with estimator-specific guide correction",
        "audit_reference": AUDIT, "source_sha256": {p: sha(ROOT / p) for p in SOURCES},
        "cases": {}}
    checks = []
    for row in rows:
        opaque = row["opaque_incident_id"]
        path = historical / "contexts_eval/cases" / (opaque + ".pkl")
        with path.open("rb") as handle:
            ctx = pickle.load(handle)
        if ctx["opaque_incident_id"] != opaque or ctx["split_audit"]["uses_private_label"] is not False:
            raise ValueError("wrong context or private split")
        # The historical request boundary applies these aliases after loading
        # cached facts. Reproduce that exact public projection before binding.
        evidence = sanitize_parent_calibration(ctx["materialized"]["SC_FULL"])
        text, metadata = project_natural_text(evidence["facts"], evidence["bundles"])
        after = guide(evidence["facts"], metadata["fact_display_references"])
        manifest["cases"][opaque] = {}
        for model in models:
            prompt_path = index[(opaque, model)]
            prompt = read_json(prompt_path)
            if len(prompt["parts"]) != 4 or any(p["type"] != "text" for p in prompt["parts"]):
                raise ValueError("historical SC request has a different carrier")
            if prompt["parts"][1]["text"] != text or prompt["parts"][0]["text"].count(OLD) != 1:
                raise ValueError(f"source projection or exact guide span differs: {opaque}/{model}")
            record = {"input_path": str(prompt_path.relative_to(ROOT)), "input_sha256": sha(prompt_path),
                "system": prompt["system"], "effective_server": prompt["effective_server"],
                "images_by_sha256": {}, "source_patches": [],
                "guide_patches": [{"part_index": 0, "before": OLD, "after": after,
                    "scope": "guide", "audit_reference": AUDIT}]}
            manifest["cases"][opaque][model] = record
            original, _, _ = exps.calibrated_request(manifest, model, opaque, "SC_TEXT_AS_RUN")
            fixed, _, _ = exps.calibrated_request(manifest, model, opaque, "SC_TEXT_GUIDE_FIXED")
            assert original == prompt["parts"] and fixed[1:] == original[1:]
            assert fixed[0] != original[0]
            assert exps.calibrated_request(manifest, model, opaque, "SC_TEXT_SOURCE_FIXED")[0] == fixed
        checks.append({"opaque_incident_id": opaque, "dataset": row["dataset"],
            "source_context": str(path.relative_to(ROOT)), "fact_count": len(evidence["facts"]),
            "evidence_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "fact_text_byte_match": True, "guide_only_change": True, "source_patch_count": 0})
        del ctx
    summary = {"status": "passed", "cases": len(checks), "requests": len(index),
        "datasets": dict(Counter(c["dataset"] for c in checks)), "checks": checks,
        "source_repair_scope": "No numerical/source edits certified; source-fixed aliases guide-fixed.",
        "limitation": "Checks bind historical selected facts to stored requests and audited estimator code; "
            "they do not independently recompute every number from raw spans or prove equal estimators."}
    gates.immutable_json(root / "calibration_source_audit.json", summary)
    gates.immutable_json(root / "calibration_manifest.json", manifest)
    return {k: v for k, v in summary.items() if k != "checks"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT / "RQs/RQ3_3/results/witness_v2")
    args = parser.parse_args()
    print(json.dumps(audit(args.root.resolve()), indent=2))
