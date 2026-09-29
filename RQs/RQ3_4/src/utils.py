"""Small artifact IO and strict parsing; no model or private-data imports."""

import hashlib
import json
import os
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def digest(obj):
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()
    ).hexdigest()


def save_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    with temporary.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    temporary.replace(path)


def decimal(value):
    if isinstance(value, bool):
        raise TypeError("Boolean is not a telemetry number")
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("Not a decimal") from exc
    if not number.is_finite():
        raise ValueError("Non-finite number")
    return number


def display_interval(text):
    """Closed interval, deliberately conservative at rounding ties."""
    value = decimal(text)
    half = Decimal(10) ** value.as_tuple().exponent / 2
    return str(value - half), str(value + half)


def json_fields(line):
    """Decode JSON-valued fields without eval or splitting quoted content."""
    result = {}
    decoder = json.JSONDecoder()
    offset = 0
    while match := re.search(r"\b([a-zA-Z_]\w*)=", line[offset:]):
        key = match.group(1)
        start = offset + match.end()
        try:
            value, consumed = decoder.raw_decode(line[start:])
            result[key] = value
            offset = start + consumed
        except json.JSONDecodeError:
            offset = start
    return result


def input_parts(obj):
    if set(obj) - {"call_key", "parts", "schema_version"}:
        raise ValueError("Expected saved public input, not a scored/private record")
    parts = obj["parts"]
    for part in parts:
        allowed = {"type", "text"} if part["type"] == "text" else {"type", "sha256"}
        if set(part) != allowed or part["type"] not in {"text", "image"}:
            raise ValueError("Unsupported public input part")
    return parts


def candidates(parts):
    sets = []
    sources = []
    for index, part in enumerate(parts):
        for line_no, line in enumerate(part.get("text", "").splitlines(), 1):
            if not line.startswith("Candidate IDs ("):
                continue
            payload = line.split(":", 1)[1].strip()
            values = (
                json.loads(payload)
                if payload.startswith("[")
                else [s.strip() for s in payload.split(",")]
            )
            if (
                not isinstance(values, list)
                or not values
                or any(not isinstance(v, str) for v in values)
            ):
                raise ValueError("Invalid candidate declaration")
            if len(values) != len(set(values)):
                raise ValueError("Duplicate declared candidates")
            sets.append(tuple(values))
            sources.append({"part": index, "line": line_no, "text": line})
    if not sets or any(s != sets[0] for s in sets[1:]):
        raise ValueError("Missing or inconsistent candidate declaration")
    return sets[0], sources


# RQ3.4 integrated pipeline. The completed claim-audit entry point above keeps
# its original interface; new execution uses a separate registration/result root.
ROOT = Path(__file__).resolve().parents[3]
INTEGRATED_CONFIG = ROOT / "RQs/RQ3_4/configs/integrated_round_v1.json"
VERSION = "rq34_integrated_v1"


def integrated_config(path=INTEGRATED_CONFIG):
    config = read_json(path)
    if config["registration_id"] != "rq34_integrated_design_v1":
        raise ValueError("Unknown integrated registration")
    if config["budget"]["existing_authorized_major_rq_hard_limit"] != 40000:
        raise ValueError("Major-RQ call limit changed")
    for spec in config["experiments"]:
        if len(spec["arms"]) != spec["logical_conditions"]:
            raise ValueError("Condition inventory mismatch")
        n = config["data"][spec["cohort"]]["expected_cases"]
        if (
            n * spec["new_conditions_upper"] * len(config["models"])
            != spec["formal_calls_upper"]
        ):
            raise ValueError("Call arithmetic mismatch")
    return config


def runtime_config(config):
    """Explicit inherited infrastructure adapter, not an old experiment dispatch."""
    from copy import deepcopy

    value = deepcopy(read_json(ROOT / config["runtime_authority"]))
    value["models"] = list(config["models"])
    value["unified"]["vllm"] = config["unified"]["inference"]
    value["data"]["bridge_manifest"] = None
    value["artifacts"]["root"] = config["implementation"]["output_root"]
    value["budget"]["hard_limit"] = 40000
    value["execution"]["workers"] = 8
    return value


def registered_source_context(row, config):
    """Reuse a committed full public pool, never the historical selected packet."""
    import pickle

    source = ROOT / config["implementation"]["source_run"]
    opaque = row["opaque_incident_id"]
    marker = read_json(source / "preparation_flags" / (opaque + ".json"))
    if marker.get("status") != "done":
        raise ValueError("Parent full-pool preparation is not complete")
    with (source / "contexts" / (opaque + ".pkl")).open("rb") as stream:
        context = pickle.load(stream)
    if (
        context["schema_version"] != "WitnessPublicContextV1"
        or context["opaque_incident_id"] != opaque
    ):
        raise ValueError("Wrong parent public context")
    if context["prepared"].private:
        raise ValueError("Private fields inside public context")
    # Do not pass private labels or the natural-identity map to selectors.
    return context, read_json(source / "private" / (opaque + ".json"))


def metric_selection_metadata(context, row, config):
    """Read only the per-case metrics table, not logs/traces or cloudbed tables.

    This new offline metadata supplies sustained fractions missing from the
    predecessor cache. It never changes displayed values or public split.
    """
    from itertools import pairwise

    import numpy as np
    import pandas as pd

    from vlmrca.processed import _case_dir, processed_index

    record = processed_index(row["dataset"])[row["case_id"]]
    path = _case_dir(row["dataset"], record)
    meta = read_json(path / "metadata.json")
    if meta["schema_version"] != "CanvasRCAProcessedPublicCaseV3":
        raise ValueError("Not canonical V3")
    frame = pd.read_parquet(path / "metrics.parquet")
    if (
        list(frame.columns) != meta["retained_columns"]["metrics"]
        or len(frame) != meta["row_counts"]["metrics"]
    ):
        raise ValueError("Metrics schema/count mismatch")
    clock = pd.to_numeric(frame["timestamp"], errors="coerce").to_numpy(float)
    clock = clock - np.min(clock[np.isfinite(clock)])
    lo, split, end = context["window"]
    cfg = config["selection_parameters"]
    output = {}
    for obs in context["observations"]:
        if obs["region"] != "M":
            continue
        name = obs["source_key"]
        if name not in frame:
            raise ValueError("Cached metric has no source column")
        values = pd.to_numeric(frame[name], errors="coerce").to_numpy(float)
        valid = (
            np.isfinite(clock) & np.isfinite(values) & (clock >= lo) & (clock <= end)
        )
        pre = values[valid & (clock < split)]
        cur = values[valid & (clock >= split)]
        # Check just the current extraction's binding, not a bulk resume hash.
        if (
            len(pre) != obs["values"]["reference_samples"]
            or len(cur) != obs["values"]["current_samples"]
        ):
            raise ValueError("Cached public split and metric source disagree")
        for samples, key in ((pre, "reference_median"), (cur, "current_median")):
            if not np.isclose(
                np.median(samples), obs["values"][key], rtol=1e-7, atol=1e-12
            ):
                raise ValueError("Metric values/source binding changed")
        bins = []
        edges = np.linspace(lo, end, 65)
        for i, (a, b) in enumerate(pairwise(edges)):
            mask = valid & (clock >= a) & ((clock <= b) if i == 63 else (clock < b))
            # A bin straddling the public split contains only its assigned
            # phase's samples, never baseline observations in a current score.
            mask &= (clock < split) if (a + b) / 2 < split else (clock >= split)
            bins.append(float(np.median(values[mask])) if mask.any() else None)
        # Reference/current boundary is applied to samples, not inferred labels.
        centres = (edges[:-1] + edges[1:]) / 2
        before = [v for t, v in zip(centres, bins) if v is not None and t < split]
        after = [v for t, v in zip(centres, bins) if v is not None and t >= split]
        median = float(np.median(pre))
        mad = float(np.median(np.abs(pre - median)))
        resolution = cfg["measurement_resolution"].get(obs["semantic"], 0.0)
        scale = max(
            cfg["mad_scale"] * mad, cfg["relative_floor"] * abs(median), resolution
        )
        fraction = None
        if (
            scale > 0
            and len(before) >= cfg["reference_bins_min"]
            and len(after) >= cfg["current_bins_min"]
        ):
            high = sum(v - median > cfg["deviation_threshold"] * scale for v in after)
            low = sum(median - v > cfg["deviation_threshold"] * scale for v in after)
            fraction = max(high, low) / len(after)
        output[obs["id"]] = {
            "scale": scale,
            "sustained_fraction": fraction,
            "reference_bins": len(before),
            "current_bins": len(after),
            "finite_bins": bins,
            "source_column": name,
        }
    return output


def stage_spec(config, stage):
    matches = [e for e in config["experiments"] if e["id"] == stage]
    if len(matches) != 1:
        raise ValueError("Unregistered experiment: " + stage)
    return matches[0]
