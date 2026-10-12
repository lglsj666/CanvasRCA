"""Public reference-association models and hypothesis disagreement compiler.

No IO, label, outcome, model call or source-directory access in this module.
Conditioning on observed anchors is not intervening on a root cause.
"""
from collections import defaultdict
from copy import deepcopy
import json
import math
import re
from statistics import mean, median, pstdev

from RQs.RQ3_11.src.exps import public_series, compact_series, replace_field, CODEC_GUIDE
from renderer.utils import compile_design, validate_evidence
from .utils import ARMS, stable_hash

VISUAL = {"OBS_VISUAL", "COND_VISUAL"}
GRAMMAR = (
    "Derived comparison: reference/current use the public relative split, not injection time. "
    "Reference is not certified healthy. Coverage counts genuine canonical sampling slots, "
    "not unsampled display bins; no interpolation. A is measured change in reference robust-scale units. "
    "Measurements require at least 12 reference/3 current samples and 60% scheduled-slot coverage. "
    "Robust scale=max(1.4826*MAD,0.01*abs(reference median)); zero scale is unavailable. "
    "E is a reference-regression prediction in the same units; "
    "R is measured minus predicted, divided by held-out prediction error scale. S is that error "
    "scale divided by reference robust scale, not a calibrated probability or confidence interval. "
    "Hypotheses condition on their observed anchor metrics; they are not interventions or causal "
    "certificates. A conditioned anchor is not explained evidence. Unknown, insufficient support, "
    "and out-of-reference-support predictions provide no negative evidence. Only displayed metric "
    "dependencies are modeled; logs, requests and other mechanisms retain their original semantics. "
    "Only calculable comparisons are displayed; omitted cells/rows have no qualified prediction, "
    "not a zero residual or healthy state. Displayed probes do not restrict the candidate list. Status is computed before "
    "four-significant-digit display rounding with threshold 3; boundary labels can differ from rounded values. "
    "Predictors use reference-only ridge0.1, two chronological folds with at least6 points each, "
    "both held-out RMSE ratios<=0.8; current anchors must stay within reference min/max plus1 SD.\n"
)
VISUAL_GRAMMAR = (
    "The PNG represents only the derived comparison table, not the original M/R/L/G facts, "
    "which remain in text. Columns are bound metric references, not time bins. Rows are OBS or "
    "candidate-conditioned profiles. Each cell prints the same A/E/R/S values and state as the "
    "text representation. Signed bars encode A in OBS and R in prediction cells on a common "
    "-6..6 axis; overflow triangles preserve direction and printed numbers remain exact at the "
    "declared four-significant-digit display precision. Positive/negative colors are residual "
    "direction, not root probability. Blank cells are omitted/unavailable comparisons, not zero. "
    "OBS prints A only; predictions print A/E/R/S.\n"
)


def dumps(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def fmt(value, c):
    if value is None:
        return None
    if not math.isfinite(value):
        raise ValueError("Nonfinite derived value")
    return format(0.0 if value == 0 else value, f".{c['display_significant_digits']}g")


def phases(clock):
    """Whole 64-bin supports only; never assign a crossing bin to a phase."""
    width = clock["duration"] / 64
    return ([i for i in range(64) if (i+1)*width <= clock["split"]],
            [i for i in range(64) if i*width >= clock["split"]])


def sampled_phases(clock):
    """Scheduled slots remain in the denominator even if metric values are NaN.

    Dense support is permitted for explicit synthetic function fixtures only;
    the real public compiler requires an independently sourced support DTO.
    """
    ref, cur = phases(clock)
    slots = set(clock.get("sampling_bins", range(64)))
    return [i for i in ref if i in slots], [i for i in cur if i in slots]


def measure(series, clock, c):
    ref, cur = sampled_phases(clock)
    ri = [i for i in ref if series["values"][i] is not None]
    ci = [i for i in cur if series["values"][i] is not None]
    good = (len(ri) >= c["reference_pairs_min"] and len(ci) >= c["current_pairs_min"]
            and len(ri)/max(1, len(ref)) >= c["phase_coverage_min"]
            and len(ci)/max(1, len(cur)) >= c["phase_coverage_min"])
    base = median([series["values"][i] for i in ri]) if ri else None
    now = median([series["values"][i] for i in ci]) if ci else None
    mad = median([abs(series["values"][i]-base) for i in ri]) if ri else None
    scale = max(c["mad_multiplier"]*mad, c["relative_floor"]*abs(base)) if ri else None
    status = "observed" if good and scale is not None and scale > 0 else "unknown"
    return {"id": series["id"], "entity": series["entity"], "metric": series["metric"], "unit": series["unit"],
            "reference": base, "current": now, "reference_mad": mad, "scale": scale,
            "reference_bins": ri, "current_bins": ci, "status": status,
            "change": (now-base)/scale if status == "observed" else None}


def fit_line(xs, ys, ridge):
    """Standardized one-predictor ridge, fitted on reference observations only."""
    mx, my, sx = mean(xs), mean(ys), pstdev(xs)
    if sx == 0 or pstdev(ys) == 0:
        return None
    z = [(x-mx)/sx for x in xs]
    beta = sum(a*(b-my) for a, b in zip(z, ys))/ (sum(a*a for a in z)+ridge*len(z))
    slope = beta/sx
    return {"intercept": my-slope*mx, "slope": slope, "x_mean": mx, "x_sd": sx,
            "x_min": min(xs), "x_max": max(xs)}


def fit_dependency(anchor, target, clock, c):
    """Two chronological folds; no current-phase values affect acceptance."""
    ref, _ = sampled_phases(clock)
    indices = [i for i in ref if anchor["values"][i] is not None and target["values"][i] is not None]
    if len(indices) < c["reference_pairs_min"] or len(indices)/max(1,len(ref)) < c["phase_coverage_min"]:
        return {"status": "unknown", "reason": "insufficient_reference_pairs"}
    # Keep chronological time blocks: sparse sampling must not choose a new
    # favorable split by counting only jointly observed pairs.
    whole_ref, _ = phases(clock)
    boundary = whole_ref[len(whole_ref)//2]
    halves = ([i for i in indices if i < boundary], [i for i in indices if i >= boundary])
    if min(map(len, halves)) < c["fold_samples_min"]:
        return {"status": "unknown", "reason": "insufficient_chronological_fold"}
    residuals, ratios = [], []
    for train, test in (halves, halves[::-1]):
        xs = [anchor["values"][i] for i in train]
        ys = [target["values"][i] for i in train]
        fitted = fit_line(xs, ys, c["ridge"])
        if fitted is None:
            return {"status": "unknown", "reason": "degenerate_reference_variation"}
        errors = [target["values"][i]-fitted["intercept"]-fitted["slope"]*anchor["values"][i] for i in test]
        baseline = sum((target["values"][i]-mean(ys))**2 for i in test)
        ratio = math.sqrt(sum(e*e for e in errors)/baseline) if baseline > 0 else float("inf")
        if not math.isfinite(ratio) or ratio > c["cv_rmse_ratio_max"]:
            return {"status": "unknown", "reason": "reference_prediction_not_reliable"}
        residuals.extend(errors); ratios.append(ratio)
    fitted = fit_line([anchor["values"][i] for i in indices], [target["values"][i] for i in indices], c["ridge"])
    return {"status": "qualified", **fitted, "reference_bins": indices, "cv_ratio": max(ratios),
            "error_rmse": math.sqrt(mean([e*e for e in residuals]))}


def cell(anchor, target, model, measurement, clock, c):
    result = {"status": "unknown", "anchor": anchor["id"], "observed": None, "expected": None,
              "residual": None, "error_scale": None, "paired_bins": [], "reason": model.get("reason", "unknown")}
    if model["status"] != "qualified" or measurement["status"] != "observed":
        return result
    _, current = sampled_phases(clock)
    indices = [i for i in current if anchor["values"][i] is not None and target["values"][i] is not None]
    if len(indices) < c["current_pairs_min"] or len(indices)/max(1,len(current)) < c["phase_coverage_min"]:
        result["reason"] = "insufficient_current_pairs"
        return result
    lo = model["x_min"]-c["support_margin_sd"]*model["x_sd"]
    hi = model["x_max"]+c["support_margin_sd"]*model["x_sd"]
    if any(not lo <= anchor["values"][i] <= hi for i in indices):
        result["reason"] = "out_of_reference_support"
        return result
    observed = median([target["values"][i] for i in indices])
    predicted = median([model["intercept"]+model["slope"]*anchor["values"][i] for i in indices])
    error = max(model["error_rmse"], measurement["scale"])
    a = (observed-measurement["reference"])/measurement["scale"]
    e = (predicted-measurement["reference"])/measurement["scale"]
    r = (observed-predicted)/error
    state = "mismatch" if abs(r) >= c["change_threshold"] else "compatible"
    if abs(a) < c["change_threshold"] and abs(e) >= c["change_threshold"]:
        state = "over_predicted"
    elif abs(a) >= c["change_threshold"] and abs(r) >= c["change_threshold"]:
        state = "unexplained"
    return {**result, "status": state, "reason": "qualified_reference_association", "paired_bins": indices,
            "observed": a, "expected": e, "residual": r, "error_scale": error/measurement["scale"]}


def owners(bundle):
    mapping = defaultdict(set)
    for card in bundle["evidence"]["cards"]:
        if card["kind"] == "graph":
            for e in card["data"]["edges"]:
                if e["kind"] in {"owns", "has_instance"} and len(e["source"]) == 3 and len(e["target"]) == 5:
                    mapping[e["target"]].add(e["source"])
    return {pod: next(iter(values)) for pod,values in mapping.items() if len(values) == 1}


def disagreement(left, right, minimum):
    pairs = [(a,b) for a,b in zip(left["cells"],right["cells"],strict=True)
             if a["expected"] is not None and b["expected"] is not None and a["paired_bins"] == b["paired_bins"]]
    if len(pairs) < minimum:
        return None
    # Mean contrast, not summed independent evidence or a likelihood.
    return mean(abs(a["expected"]-b["expected"])/max(a["error_scale"],b["error_scale"],1) for a,b in pairs)


def choose_profiles(profiles, c):
    """Disagreement-first bounded probes; no metric/candidate deletion."""
    ordered = sorted(profiles, key=lambda p: stable_hash([42,"profile",p["entity"]]))
    pairs = [(disagreement(a,b,c["common_targets_min"]),a,b) for i,a in enumerate(ordered) for b in ordered[i+1:]]
    valid = [(d,a,b) for d,a,b in pairs if d is not None]
    selected = []
    if valid:
        _, a, b = max(valid, key=lambda v: (v[0],stable_hash([v[1]["entity"],v[2]["entity"]])))
        selected = [a,b]
    # Preserve a probe of each available identity type before adding further
    # contrast rows. Original isolated resource evidence always stays in base.
    for size in (4,5,3):
        if not any(len(p["entity"]) == size for p in selected):
            match = next((p for p in ordered if len(p["entity"]) == size),None)
            if match is not None and len(selected) < c["hypotheses_max"]:
                selected.append(match)
    while len(selected) < min(c["hypotheses_max"],len(ordered)):
        rest = [p for p in ordered if p not in selected]
        def separation(p):
            scores = [disagreement(p,q,c["common_targets_min"]) for q in selected]
            scores = [s for s in scores if s is not None]
            return (min(scores) if scores else -1,stable_hash(p["entity"]))
        selected.append(max(rest,key=separation))
    return selected, max((d for d,_,_ in valid),default=None)


def compile_model(bundle, series, clock, c):
    stats = [measure(s,clock,c) for s in series]
    deps = {(a["id"],t["id"]): fit_dependency(a,t,clock,c) for a in series for t in series if a["id"] != t["id"]}
    owned = owners(bundle)
    profiles = []
    for eid in bundle["candidates"]:
        anchors = [s for s in series if s["entity"] == eid or (len(eid) == 3 and owned.get(s["entity"]) == eid)]
        if not anchors:
            continue
        cells = []
        for target, measured in zip(series,stats,strict=True):
            if target in anchors:
                cells.append({"status":"conditioned","anchor":target["id"],"observed":None,"expected":None,
                              "residual":None,"error_scale":None,"paired_bins":[],"reason":"anchor_not_evaluated"})
                continue
            # Select predictor using reference CV ONLY, before current observations.
            good = [(deps[a["id"],target["id"]],a) for a in anchors if deps[a["id"],target["id"]]["status"] == "qualified"]
            if good:
                model, anchor = min(good,key=lambda p:(p[0]["cv_ratio"],p[1]["id"]))
            else:
                anchor = min(anchors,key=lambda a:a["id"])
                model = deps[anchor["id"],target["id"]]
            cells.append(cell(anchor,target,model,measured,clock,c))
        profiles.append({"entity":eid,"anchors":[a["id"] for a in anchors],"cells":cells})
    # Do not occupy a comparison row with a candidate that has no prediction.
    # Preserve the complete candidate list and the full offline profile audit.
    usable = [p for p in profiles if any(v["expected"] is not None for v in p["cells"])]
    selected, maximum = choose_profiles(usable,c)
    selected_pairs = [disagreement(a,b,c["common_targets_min"]) for i,a in enumerate(selected) for b in selected[i+1:]]
    competing = any(d is not None and d >= c["disagreement_min"] for d in selected_pairs)
    return {"stats":stats,"profiles":selected,"dependencies":deps,"all_profiles":profiles,
            "max_disagreement":maximum,"competing":competing,
            "qualified_dependencies":sum(d["status"] == "qualified" for d in deps.values())}


def observed_matrix(model, c):
    usable = [s for s in model["stats"] if s["status"] == "observed"]
    cells = [{"status":"observed","observed":fmt(s["change"],c),"expected":None,"residual":None,"error_scale":None}
             for s in usable]
    return {"targets":[s["id"] for s in usable],"rows":[{"entity":None,"anchors":[],"cells":cells}] if cells else [],
            "delta_limit":6,"sparse":True}


def conditioned_matrix(model, c):
    matrix = observed_matrix(model,c)
    columns = [i for i,s in enumerate(model["stats"]) if s["id"] in matrix["targets"]]
    matrix["rows"].extend({"entity":p["entity"],"anchors":p["anchors"],"cells":[
        {"status":v["status"],**{k:fmt(v[k],c) for k in ("observed","expected","residual","error_scale")}}
        if v["expected"] is not None else None
        for v in (p["cells"][i] for i in columns)]} for p in model["profiles"]
        if any(p["cells"][i]["expected"] is not None for i in columns))
    return matrix


def pack_matrix(matrix):
    """Compact strong-text control; schema carries order, nulls and precision."""
    return {"targets":matrix["targets"],"delta_limit":matrix["delta_limit"],
            "fields":["status","observed","expected","residual","error_scale"],
            "sparse":True,"rows":[[r["entity"],r["anchors"],[[j,v["observed"] if r["entity"] is None else
                [v[k] for k in ("status","observed","expected","residual","error_scale")]]
                for j,v in enumerate(r["cells"]) if v is not None]] for r in matrix["rows"]]}


def unpack_matrix(packed):
    rows=[]
    for eid,anchors,entries in packed["rows"]:
        cells=[None]*len(packed["targets"])
        for j,value in entries:
            if not 0 <= j < len(cells) or cells[j] is not None:
                raise ValueError("Invalid/duplicate sparse matrix position")
            cells[j]=({"status":"observed","observed":value,"expected":None,"residual":None,"error_scale":None}
                      if eid is None else dict(zip(packed["fields"],value,strict=True)))
        rows.append({"entity":eid,"anchors":anchors,"cells":cells})
    return {"targets":packed["targets"],"delta_limit":packed["delta_limit"],"sparse":True,"rows":rows}


def compile_public(bundle, c, support):
    original, series, clock = public_series(bundle)
    if support.get("schema") != "CanonicalSamplingSlotsV2":
        raise ValueError("Real source sampling support is required; never infer it from finite metric values")
    slots = support["sampling_bins"]
    if not slots or sorted(set(slots)) != slots or any(type(i) is not int or not 0 <= i < 64 for i in slots):
        raise ValueError("Invalid canonical sampling slots")
    if any(v is not None and i not in slots for s in series for i,v in enumerate(s["values"])):
        raise ValueError("Frozen metric values appear outside canonical sampling support")
    clock = {**clock,"sampling_bins":slots}
    base = deepcopy(original)
    for part in base:
        for s in series:
            line = replace_field(s["line"],"missing_mask","missing_codec",compact_series(s["mask"]))
            line = replace_field(line,"values","values_codec",compact_series(s["raw"]))
            part["text"] = part["text"].replace(s["line"],line)
    base.insert(1,{"type":"text","text":CODEC_GUIDE})
    cfg = c["response_model"]
    model = compile_model(bundle,series,clock,cfg)
    matrices = {"OBS":observed_matrix(model,cfg),"COND":conditioned_matrix(model,cfg)}
    # Avoid repeating full statistics, parameter dictionaries and unused masks
    # beside a table. These normalized operands use the declared display
    # precision; the original exact telemetry remains in the baseline text.
    binding = {"clock":[clock["split"],clock["duration"]],"sampled_bins":compact_series(slots),
               "fields":["id","entity","metric","unit","reference","scale","reference_bins","current_bins"],
               "measurements":[[s["id"],s["entity"],s["metric"],s["unit"],fmt(s["reference"],cfg),fmt(s["scale"],cfg),
                   compact_series(s["reference_bins"]),compact_series(s["current_bins"])]
                   for s in model["stats"] if s["status"] == "observed"]}
    provenance = [{"entity":p["entity"],"anchors":p["anchors"],"cell_provenance":[
        [model["stats"][i]["id"],v["anchor"],compact_series(v["paired_bins"])]
        for i,v in enumerate(p["cells"]) if v["expected"] is not None]} for p in model["profiles"]]
    texts = {}
    for arm in ARMS:
        parts = deepcopy(base)
        if not arm.startswith("EXACT"):
            family = arm.split("_",1)[0]
            if not matrices[family]["targets"]:
                texts[arm] = parts  # Nothing computable: no empty appendix/image.
                continue
            content = GRAMMAR+"Derived measurement bindings\n"+dumps(binding)
            if family == "COND" and provenance:
                content += "\nPrediction provenance\n"+dumps(provenance)
            parts.insert(len(parts)-1,{"type":"text","text":content})
            if arm not in VISUAL:
                parts.insert(len(parts)-1,{"type":"text","text":"Comparison table\n"+dumps(pack_matrix(matrices[family]))})
        texts[arm] = parts
    payload = {"schema":"ConditionalResidualCanvasV2","clock":clock,"matrices":matrices,
               "binding":binding,"provenance":provenance}
    audits = {"competing":model["competing"],"max_disagreement":model["max_disagreement"],
              "qualified_dependencies":model["qualified_dependencies"],"profiles":len(model["all_profiles"]),
              "displayed_profile_anchors":{p["entity"]:len(p["anchors"]) for p in model["profiles"]},
              "prediction_availability":{reason:sum(v["reason"]==reason for p in model["all_profiles"] for v in p["cells"])
                  for reason in sorted({v["reason"] for p in model["all_profiles"] for v in p["cells"]})},
              "sampling_support":support,"observed_measurements":sum(s["status"]=="observed" for s in model["stats"]),
              "omitted_measurements":sum(s["status"]!="observed" for s in model["stats"]),
              "dependencies":[{"anchor":a,"target":t,**v} for (a,t),v in model["dependencies"].items()],
              "cpu_ranking":cpu_ranking(model,bundle["candidates"],owned=owners(bundle),c=cfg)}
    return {"system":bundle["system"],"candidates":bundle["candidates"],"facts_hash":bundle["facts_hash"],
            "payload":payload,"texts":texts,"images":{},"infeasible":{}},audits


def cpu_ranking(model, candidates, owned, c):
    """Matched residual heuristic; no independent-likelihood or causal claim."""
    profiles = model["profiles"]
    common = [i for i in range(len(model["stats"])) if profiles and all(p["cells"][i]["residual"] is not None for p in profiles)]
    applicable = len(profiles) >= 2 and len(common) >= c["common_targets_min"]
    residual = {p["entity"]:mean(abs(p["cells"][i]["residual"]) for i in common) for p in profiles} if applicable else {}
    severity = {eid:max((abs(s["change"]) for s in model["stats"] if s["change"] is not None and
                         (s["entity"] == eid or owned.get(s["entity"]) == eid)),default=0) for eid in candidates}
    ranked = sorted(candidates,key=lambda eid:(0 if eid in residual else 1,residual.get(eid,-severity[eid]),stable_hash([42,eid])))
    return {"ranking":ranked,"applicable":applicable,"common_targets":[model["stats"][i]["id"] for i in common],
            "residual_scores":residual,"fallback_severity":severity,
            "method":"mean absolute residual on common targets; unprobed/fallback candidates use measured change; heuristic, no probability"}


def designs(payload, c):
    result = {}
    for name, matrix in payload["matrices"].items():
        if not matrix["targets"]:
            continue
        evidence = validate_evidence({"schema":"CanvasEvidenceV1","cards":[{"id":"D01","kind":"diagnostic",
            "title":"Observed change" if name == "OBS" else "Candidate-conditioned reference predictions",
            "entity":None,"unit":"A/E: reference scale; R: prediction error scale; S: relative error scale","data":matrix}]})
        design = {"schema":"DashboardDesignV1","viewport":{"width":c["canvas"]["width"],"height":c["canvas"]["height"]},
                  "theme":"dark","font_size":c["canvas"]["font_size"],"gap":12,"padding":24,"scale":1,
                  "tree":{"id":"comparison","type":"panel","card":"D01","component":"diagnostic.compact"},
                  "bindings":[],"indexing":{"visible":True,"start":1}}
        design["viewport"]["height"] = max(c["display"]["minimum_height"], 340+110*(len(matrix["rows"])-1))
        if design["viewport"]["height"] > c["display"]["maximum_height"]:
            raise ValueError("Compact table exceeds registered maximum canvas")
        compile_design(evidence,design)
        result[name] = (evidence,design)
    return result


def parts_for(public, arm, png=None):
    if arm not in ARMS:
        raise ValueError("Unregistered arm")
    parts = deepcopy(public["texts"][arm])
    if arm in VISUAL:
        family = arm.split("_",1)[0]
        if not public["payload"]["matrices"][family]["targets"]:
            if png is not None: raise ValueError("Empty comparison must not carry an image")
            return parts
        if png is None or not png.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("Committed actual PNG required")
        # Static decoding grammar precedes the image-first A+B incident parts.
        return [{"type":"text","text":VISUAL_GRAMMAR},{"type":"image","png":png}]+parts
    if png is not None:
        raise ValueError("Unexpected image in text condition")
    return parts


def visible_audit(public):
    text = dumps({"system":public["system"],"texts":public["texts"],"payload":public["payload"]})
    if re.search(r"(?i)(INC-[A-F0-9]{8}|aiops202[25]|aegislab|ground_truth|injection_time|/home/|/scratch/)",text):
        raise ValueError("Private/source metadata in model input")
    if any(k in text for k in ('"source_key"','"fault_type"','"cpu_ranking"')):
        raise ValueError("Evaluator/audit fields in input")
    if public["texts"]["EXACT_TEXT"] != public["texts"]["EXACT_REPEAT"]:
        raise ValueError("Independent repeat differs")
    for family in ("OBS","COND"):
        if not public["payload"]["matrices"][family]["targets"]:
            if public["texts"][family+"_TEXT"] != public["texts"]["EXACT_TEXT"] or public["texts"][family+"_VISUAL"] != public["texts"]["EXACT_TEXT"]:
                raise ValueError("Empty table must omit both representations")
            continue
        table = public["texts"][family+"_TEXT"][-2]["text"]
        rebuilt = unpack_matrix(json.loads(table.split("Comparison table\n",1)[1]))
        if rebuilt != public["payload"]["matrices"][family]:
            raise ValueError("Text/visual semantic matrix mismatch")
        if public["texts"][family+"_TEXT"][:-2]+public["texts"][family+"_TEXT"][-1:] != public["texts"][family+"_VISUAL"]:
            raise ValueError("Representation changed non-matrix facts or question")
    return {"status":"passed","encoded_fact_parity":True,"repeat_identical":True,"base_facts_retained":True}
