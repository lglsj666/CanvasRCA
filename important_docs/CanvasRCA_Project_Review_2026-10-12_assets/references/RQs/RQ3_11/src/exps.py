"""Pure public-fact codec; evaluator outcomes and IO are absent."""
from copy import deepcopy
import json
import math
import re
from statistics import median

from renderer.utils import compile_design, validate_evidence
from RQs.RQ3_8.src.exps import model_parts, _public_field, expand_records
from .utils import ARMS, stable_hash

CODEC_GUIDE = (
    "Exact compact sequences: length/value_positions lists each value and its zero-based bin positions; "
    "a-b includes both endpoints. Every bin is present exactly once. Missing/null is no observation, never zero. "
    "Metric series references M01.. bind the same entity, metric and source unit as their metadata.\n"
)
QUANT_GUIDE = (
    "Quantized metric curves: original observation bins remain0..63. Each series uses its own exact lo/hi "
    "and integer levels0..(levels-1); decode x=lo+q*(hi-lo)/(levels-1). A zero span is constant lo. "
    "All-missing range is null. The missing mask is exact. Overrides [bin,exact original value] take "
    "precedence over coarse values; unpatched values are approximations. Original printed summaries "
    "remain measured summaries and do not imply that every approximate sample is exact.\n"
)
VISUAL_GUIDE = (
    "The single PNG carries the coarse q samples, with a separate scale per series. M01.. identify the "
    "text bindings. Points are observed bins; connecting lines are visual aids, not measurements of "
    "missing intervals. Read the exact missing mask and apply the text overrides before numeric comparisons.\n"
)


def dumps(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def compact_series(values):
    """Lossless scalar positions, including original number strings and masks."""
    groups = {}
    for i, value in enumerate(values):
        groups.setdefault(dumps(value), [value, []])[1].append(i)
    entries = []
    for value, indices in groups.values():
        spans = []
        for i in indices:
            if spans and i == spans[-1][1]+1:
                spans[-1][1] = i
            else:
                spans.append([i, i])
        entries.append([value, ",".join(str(a) if a == b else f"{a}-{b}" for a, b in spans)])
    choices = [values, {"length": len(values), "value_positions": entries}]
    packed = min(choices, key=lambda v: len(dumps(v)))
    if expand_records(packed) != values:
        raise ValueError("Lossless scalar codec changed values")
    return packed


def replace_field(line, name, new_name, value):
    quoted=escaped=False;outside=set()
    for i,ch in enumerate(line):
        if not quoted:
            outside.add(i)
        if escaped:
            escaped=False
        elif quoted and ch=="\\":
            escaped=True
        elif ch=='"':
            quoted=not quoted
    match=next((m for m in re.finditer(r"(?<![A-Za-z0-9_])"+re.escape(name)+r"=",line)
                if m.start() in outside),None)
    if not match:
        raise ValueError("Absent field: "+name)
    start = match.end()
    while start < len(line) and line[start].isspace():
        start += 1
    _, consumed = json.JSONDecoder().raw_decode(line[start:])
    return line[:match.start()]+new_name+"="+dumps(value)+line[start+consumed:]


def public_series(bundle):
    """Cross-bind original field lines to the already frozen twelve cards."""
    original = model_parts(bundle, "TEXT")
    text = "\n".join(p["text"] for p in original)
    window = next(line for line in text.splitlines() if "field=sircl_star_analysis;" in line)
    duration = next(line for line in text.splitlines() if "field=observation_window;" in line)
    split = _public_field(window, "window_rel_s")[0]
    length = _public_field(duration, "duration_rel_s")
    if not 0 < split < length:
        raise ValueError("Unusable public phase clock")
    # Cards may not be duplicated in the extra ledger after vector replacement.
    for p in original:
        if p["text"].startswith("Additional component facts"):
            extra = expand_records(json.loads(p["text"].split("\n", 1)[1]))
            if any(c["kind"] == "metric" for c in extra):
                raise ValueError("An additional metric ledger would leak original vectors")
    cards = [x for x in bundle["evidence"]["cards"] if x["kind"] == "metric"]
    lines = [x for x in text.splitlines() if "field=metric_series_64;" in x]
    if len(cards) != 12 or len(lines) != 12:
        raise ValueError("Registered twelve-series selection changed")
    series = []
    for card in cards:
        matches = [line for line in lines if _public_field(line, "service") == card["entity"]
                   and _public_field(line, "metric") == card["title"]]
        if len(matches) != 1:
            raise ValueError("Ambiguous original metric binding")
        line = matches[0]
        raw = _public_field(line, "values")
        values = [None if v is None else float(v) for v in raw]
        mask = _public_field(line, "missing_mask")
        if (card["data"]["values"] != values or card["data"]["bins"] != list(range(64))
                or mask != [v is None for v in values] or _public_field(line,"unit") != card["unit"]
                or any(v is not None and not math.isfinite(v) for v in values)):
            raise ValueError("Original metric/card/missingness mismatch")
        series.append({"id":card["id"], "entity":card["entity"], "metric":card["title"], "unit":card["unit"],
                       "line":line, "raw":raw, "values":values, "mask":mask})
    return original, series, {"split": split, "duration": length}


def diagnostic_signature(values, clock, c):
    """Finite codec signature on observed binned data; no RCA or causality."""
    finite = [(i, v) for i, v in enumerate(values) if v is not None]
    reference = [v for i, v in finite if (i+1)*clock["duration"]/64 <= clock["split"]]
    current = [(i, v) for i, v in finite if i*clock["duration"]/64 >= clock["split"]]
    extrema = (min(finite, key=lambda x: (-x[1], x[0]))[0], min(finite, key=lambda x:(x[1],x[0]))[0]) if finite else (None,None)
    base = (tuple(i for i, _ in finite), len(reference), len(current), extrema)
    if min(len(reference), len(current)) < c["samples_min"]:
        return base+("unknown_samples", None, None)
    center = median(reference)
    scale = max(c["mad_multiplier"]*median(abs(v-center) for v in reference), c["relative_floor"]*abs(center))
    if scale == 0:
        return base+("unknown_scale", None, None)
    delta = (median(v for _, v in current)-center)/scale
    state = "up" if delta >= c["change_threshold"] else "down" if delta <= -c["change_threshold"] else "within_threshold"
    changed = [(i, v) for i, v in current if abs((v-center)/scale) >= c["change_threshold"]]
    return base+(state, changed[0][0] if changed else None, len(changed)/len(current) >= c["sustained_min"])


def decode(record, protected=True):
    values = [None if q is None else record["lo"]+q*(record["hi"]-record["lo"])/(record["levels"]-1)
              for q in record["q"]]
    if protected:
        for i, value in record["overrides"]:
            values[i] = float(value)
    return values


def quantize(series, clock, budget, c):
    values = series["values"]; finite = [v for v in values if v is not None]
    lo, hi = (min(finite), max(finite)) if finite else (None,None)
    levels = budget["levels"]
    q = [None if v is None else 0 if hi == lo else round((v-lo)/(hi-lo)*(levels-1)) for v in values]
    record = {"id":series["id"], "levels":levels, "lo":lo, "hi":hi, "q":q, "overrides":[]}
    original = diagnostic_signature(values, clock, c)
    coarse = decode(record, False)
    order = sorted((i for i,v in enumerate(values) if v is not None), key=lambda i:(-abs(values[i]-coarse[i]),i))
    before = diagnostic_signature(coarse, clock, c)
    for i in order:
        if diagnostic_signature(decode(record),clock,c) == original:
            break
        record["overrides"].append([i, series["raw"][i]])
    if diagnostic_signature(decode(record),clock,c) != original:
        raise ValueError("Finite signature protection failed")
    # Remove each redundant override in reverse insertion order. Every removal
    # is accepted only after the complete finite signature remains identical.
    # This uses public values alone and never evaluates an RCA outcome.
    for override in list(reversed(record["overrides"])):
        before_pruning=list(record["overrides"])
        record["overrides"].remove(override)
        if diagnostic_signature(decode(record),clock,c)!=original:
            record["overrides"]=before_pruning
    audit = {"id":series["id"], "coarse_signature_changed":before != original,
             "patch_points":len(record["overrides"]), "finite_points":len(finite),
             "max_abs_coarse_error":max((abs(values[i]-coarse[i]) for i in order),default=0),
             "original_signature":original, "protected_signature":diagnostic_signature(decode(record),clock,c)}
    return record, audit


def compile_public(bundle, c):
    original, series, clock = public_series(bundle)
    records, audits = {}, {}
    for key, budget in c["budgets"].items():
        pairs = [quantize(s,clock,budget,c["operators"]) for s in series]
        records[key] = [r for r, _ in pairs]; audits[key] = [a for _, a in pairs]
    text_by_arm = {}
    for arm in ARMS:
        exact = arm.startswith("EXACT")
        key = None if exact else arm.rsplit("_",1)[1]
        visual = "VISUAL" in arm
        protected = arm.startswith("PROTECTED")
        parts = deepcopy(original)
        for p in parts:
            for s in series:
                updated = replace_field(s["line"],"missing_mask","missing_codec",compact_series(s["mask"]))
                updated = replace_field(updated,"values","values_codec" if exact else "series_ref",
                                        compact_series(s["raw"]) if exact else s["id"])
                p["text"] = p["text"].replace(s["line"],updated)
        parts.insert(1,{"type":"text","text":CODEC_GUIDE})
        if not exact:
            visible = []
            for r in records[key]:
                item = {k:r[k] for k in ("id","levels","lo","hi")}
                item["overrides"] = r["overrides"] if protected else []
                if not visual:
                    item["q_codec"] = compact_series(r["q"])
                visible.append(item)
            parts.insert(len(parts)-1,{"type":"text","text":QUANT_GUIDE+(VISUAL_GUIDE if visual else "")+
                                      "Curve bindings and exact overrides\n"+dumps(visible)})
        text_by_arm[arm] = parts
    payload = {"schema":"ProtectedCurveCodecV1", "clock":clock, "series":series, "records":records}
    return {"system":bundle["system"],"candidates":bundle["candidates"],"facts_hash":bundle["facts_hash"],
            "base_evidence":bundle["evidence"],"payload":payload,"texts":text_by_arm,"images":{},"infeasible":{}}, audits


def designs(payload, c):
    result = {}
    for key, records in payload["records"].items():
        lookup = {s["id"]:s for s in payload["series"]}
        cards = [{"id":r["id"],"kind":"metric","title":r["id"]+" · coarse metric samples",
                  "entity":lookup[r["id"]]["entity"],"unit":"quantized level0.."+str(r["levels"]-1),
                  "data":{"bins":list(range(64)),"values":r["q"],"details":[]}} for r in records]
        evidence = validate_evidence({"schema":"CanvasEvidenceV1","cards":cards})
        design = {"schema":"DashboardDesignV1", "viewport":{"width":c["budgets"][key]["width"],"height":1940},
                  "theme":"dark","font_size":16,"gap":12,"padding":24,"scale":1,
                  "tree":{"id":"curves","type":"grid","columns":2,
                          "children":[{"id":"panel"+r["id"],"type":"panel","card":r["id"],"component":"metric.line"} for r in records]},
                  "bindings":[],"indexing":{"visible":True,"start":1}}
        compile_design(evidence,design)
        result[key] = (evidence, design)
    return result


def parts_for(public, arm, png=None):
    if arm not in ARMS:
        raise ValueError("Unregistered arm")
    parts = deepcopy(public["texts"][arm])
    if "VISUAL" in arm:
        if png is None or not png.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("Actual committed PNG required")
        return [{"type":"image","png":png}]+parts
    if png is not None:
        raise ValueError("Text arm unexpectedly has image")
    return parts


def visible_audit(public):
    text = dumps({"system":public["system"],"texts":public["texts"]})
    if re.search(r"(?i)(INC-[A-F0-9]{8}|aiops202[25]|aegislab|ground_truth|injection_time|/home/|/scratch/)",text):
        raise ValueError("Source/private identity leaked")
    if any(x in text for x in ('"source_key"','"fault_type"','"original_signature"','"cpu_ranking"')):
        raise ValueError("Hidden audit/label field in input")
    if public["texts"]["EXACT_TEXT"] != public["texts"]["EXACT_REPEAT"]:
        raise ValueError("Independent repeat changed input")
    for key in ("LOW","HIGH"):
        r = public["payload"]["records"][key]
        design, _ = designs(public["payload"],{"budgets":{"LOW":{"width":800},"HIGH":{"width":1120}}})[key]
        if [c["data"]["values"] for c in design["cards"]] != [x["q"] for x in r]:
            raise ValueError("Visual samples changed encoded facts")
        pt = public["texts"]["PROTECTED_TEXT_"+key][-2]["text"]
        pv = public["texts"]["PROTECTED_VISUAL_"+key][-2]["text"]
        rows = json.loads(pt.split("Curve bindings and exact overrides\n",1)[1])
        visual_rows = json.loads(pv.split("Curve bindings and exact overrides\n",1)[1])
        if [{k:v for k,v in x.items() if k!="q_codec"} for x in rows] != visual_rows:
            raise ValueError("Encoded text/visual metadata mismatch")
        if [expand_records(x["q_codec"]) for x in rows] != [x["q"] for x in r]:
            raise ValueError("Encoded text/visual numeric mismatch")
    return {"status":"passed","encoded_fact_parity":True,"repeat_identical":True,"original_vectors_absent_visual":True}
