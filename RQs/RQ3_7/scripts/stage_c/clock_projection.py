"""RQ37-local display adapter for the source-attested WiredTiger clock prefix.

WiredTiger mongodb-7.0 src/support/err.c __eventv prints epoch seconds then
microseconds as [sec:usec][thread]. The inherited log-template extractor
retains these as numeric slots. Translate seconds by ONE public case-local
origin; never use a label, incident/injection timestamp, or per-entity origin.
No raw data, diagnostic count, slot identity, template, or selection score is
rewritten. This is an additive registered privacy repair, not a new selector.
"""

import re
from copy import deepcopy
from decimal import Decimal

VERSION = "rq37_wiredtiger_relative_clock_v1"
PREFIX = re.compile(r"\[(\{num\d+\}):(\{num\d+\})\]\[\{num\d+\}:\{hex\d+\}\], WT_SESSION\.")
STAMP = re.compile(r"(?:oldest|meta checkpoint) timestamp: \((\{num\d+\}), (\{num\d+\})\)")
STATS = ("min", "median", "max")


def _number(value):
    value = Decimal(str(value))
    if not value.is_finite():
        raise ValueError("Nonfinite WiredTiger clock component")
    return value


def project_log_clocks(observations):
    """Return a copy only for matching rows; byte-identical objects otherwise.

The seconds statistics are already rounded by the inherited public projection;
translation does NOT recover precision or combine unpaired microsecond stats.
Both components keep their own min/median/max/n. Nonzero transaction timestamp
fields need a separate semantic review; their meaning is not guessed here.
"""
    eligible, anchors = [], []
    for i, obs in enumerate(observations):
        if obs.get("region") != "L" or obs.get("semantic") != "recorded_log_template":
            continue
        values = obs["values"]
        template = values.get("template", "")
        matches = list(PREFIX.finditer(template))
        if not matches:
            continue
        if len(matches) != 1 or "WiredTiger message" not in template:
            raise ValueError("Ambiguous WiredTiger log-clock structure")
        seconds, micros = matches[0].groups()
        units = values.get("numeric_parameter_units", {})
        if units.get(seconds) == "relative_clock_seconds":
            if units.get(micros) != "microseconds_component":
                raise ValueError("Incomplete WiredTiger clock projection")
            continue
        if units:
            raise ValueError("Conflicting WiredTiger numeric-parameter units")
        present = False
        for phase in ("reference", "current"):
            params = values.get(phase + "_numeric_parameters", {})
            if not params:
                if values.get(phase + "_count", 0):
                    raise ValueError("Recorded WiredTiger phase has no clock operands")
                continue
            for slot in (seconds, micros):
                if slot not in params or set(params[slot]) != {*STATS, "n"}:
                    raise ValueError("Incomplete WiredTiger clock statistics")
                numbers = [_number(params[slot][s]) for s in STATS]
                if not numbers[0] <= numbers[1] <= numbers[2]:
                    raise ValueError("Unordered WiredTiger clock statistics")
                if slot == micros and not (0 <= numbers[0] <= numbers[2] < 1_000_000):
                    raise ValueError("WiredTiger microseconds outside source range")
                if slot == seconds and numbers[0] <= 0:
                    raise ValueError("Nonpositive WiredTiger epoch requires review")
            for pair in STAMP.findall(template):
                for slot in pair:
                    if slot not in params or any(_number(params[slot][s]) != 0 for s in STATS):
                        raise ValueError("Nonzero WiredTiger transaction timestamp requires review")
            anchors.append(_number(params[seconds]["min"]))
            present = True
        if not present:
            raise ValueError("WiredTiger template has no observed clock")
        eligible.append((i, seconds, micros))
    if not eligible:
        return observations, {"version": VERSION, "observations": []}
    origin = min(anchors)
    result = list(observations)
    changed = []
    for i, seconds, micros in eligible:
        item = deepcopy(observations[i])
        values = item["values"]
        for phase in ("reference", "current"):
            params = values.get(phase + "_numeric_parameters", {})
            if seconds not in params:
                continue
            for stat in STATS:
                translated = _number(params[seconds][stat]) - origin
                # Existing projection uses ordinary floats. Reject loss rather
                # than introduce a second rounding or an unregistered serializer.
                number = float(translated)
                if _number(number) != translated:
                    raise ValueError("WiredTiger clock translation loses decimal precision")
                params[seconds][stat] = number
        values["numeric_parameter_units"] = {
            seconds: "relative_clock_seconds", micros: "microseconds_component"}
        result[i] = item
        changed.append({"observation_id": item["id"], "seconds_slot": seconds,
                        "microseconds_slot": micros})
    # Origin stays CPU-side, never part of the returned model-visible rows.
    return result, {"version": VERSION, "observations": changed,
                    "origin": str(origin), "origin_source": "minimum_public_log_clock"}
