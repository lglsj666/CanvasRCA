"""Pure public evidence, unique bindings and unified-renderer designs; no IO."""
from copy import deepcopy
import json
import math
import re
from RQs.RQ3_11.src.exps import public_series, compact_series, replace_field, CODEC_GUIDE
from RQs.RQ3_8.src.exps import _public_field
from RQs.RQ3_12.src.exps import REFERENCE_GRAMMAR, select_reference_operands
from RQs.RQ3_13.src.exps import READING
from renderer.utils import validate_evidence, compile_design
from renderer.operations import apply_operations
from .utils import ARMS, stable_hash

VISUAL={"WINDOW_VISUAL","WINDOW_MARKLESS","WINDOW_PIXEL","WINDOW_REPEAT"}
REPEATS={"RAW_REPEAT","WINDOW_REPEAT"}
SAFE=("Source reading: request-duration quantiles include the scope stated by their source; only explicit "
      "exclusive latency is local time after child spans. Independent quantiles must not be subtracted. "
      "Keep native units; do not infer conversions from a metric name. Resource gauges, accumulated "
      "counters, restart states and request counts have different meanings. Correlated metrics from "
      "one entity are not independent votes. Recovery does not rule out an earlier initiating fault. "
      "Observed order and calls/hosting alone do not prove origin. Bind every claim to its entity and "
      "metric or operation; cite MET/TRC/LOG/REL references where provided.\n")
GUIDE=("Full-window observations: metric curves use their original time bins and independent linear "
       "native-unit axes. Extrema and first/last values describe the whole observation window; reference "
       "and current intervals retain their public definitions. Trace bars compare reference/current "
       "exclusive p95, not inclusive duration. Colors distinguish measurements, not root probability. "
       "All original telemetry, additional operands, logs, relations and candidates remain in text.\n")


def dumps(v):
    return json.dumps(v,ensure_ascii=False,separators=(",",":"),allow_nan=False)


def fresh_raw(bundle, support, pool, legacy_config):
    """Reproduce the historical EXACT baseline adapter for the additional80 eval cases."""
    original,series,clock=public_series(bundle)
    selected,audit=select_reference_operands(pool,bundle,{**clock,"sampling_bins":support["sampling_bins"]},legacy_config)
    base=deepcopy(original)
    for p in base:
        for s in series:
            line=replace_field(s["line"],"missing_mask","missing_codec",compact_series(s["mask"]))
            line=replace_field(line,"values","values_codec",compact_series(s["raw"]))
            p["text"]=p["text"].replace(s["line"],line)
    base.insert(1,{"type":"text","text":CODEC_GUIDE})
    if selected:
        text=REFERENCE_GRAMMAR+"Additional reference operands\n"+dumps({"fields":["id","entity","metric","unit","values_codec"],
            "series":[[s["id"],s["entity"],s["metric"],s["unit"],compact_series(s["values"])] for s in selected]})
        base.insert(len(base)-1,{"type":"text","text":text})
    base.insert(1,{"type":"text","text":READING})
    return base,audit


def canonicalize(raw,bundle):
    """Lossless lexical rename plus a bound identifier on each original field line."""
    ids={c["id"]:({"metric":"MET","trace":"TRC","log":"LOG","graph":"REL","events":"EVT"}[c["kind"]]+c["id"][1:])
         for c in bundle["evidence"]["cards"]}
    ids.update({f"M{i:02}":f"AUX{i-12:02}" for i in range(13,19)})
    pattern=re.compile(r'(?<![A-Za-z0-9_])('+"|".join(sorted(ids,key=len,reverse=True))+r')(?![A-Za-z0-9_])')
    reverse={v:k for k,v in ids.items()}
    inverse=re.compile(r'(?<![A-Za-z0-9_])('+"|".join(sorted(reverse,key=len,reverse=True))+r')(?![A-Za-z0-9_])')
    result=deepcopy(raw); edits=[]
    for j,part in enumerate(result):
        old=part["text"]; text=pattern.sub(lambda m:ids[m[0]],old)
        if inverse.sub(lambda m:reverse[m[0]],text)!=old: raise ValueError("Nonreversible identifier rename")
        lines=text.splitlines(keepends=True); changes=[]
        for i,line in enumerate(lines):
            kind=("metric" if "field=metric_series_64;" in line else "trace" if "field=trace_summary_entry;" in line else None)
            if not kind: continue
            semantic=_public_field(line,"metric" if kind=="metric" else "operation")
            owner=_public_field(line,"service")
            matches=[c for c in bundle["evidence"]["cards"] if c["kind"]==kind and c["title"]==semantic and c["entity"]==owner]
            if len(matches)!=1: raise ValueError("Ambiguous source/card binding")
            cid=ids[matches[0]["id"]]
            new=line.replace('panel_id=', 'legacy_display_rank=')
            new=new.replace('field=',f'fact_id="{cid}"; field=',1)
            changes.append({"line":i,"before":line,"after":new}); lines[i]=new
        modified="".join(lines)
        undo=modified.splitlines(keepends=True)
        for change in changes:
            assert undo[change["line"]]==change["after"]
            undo[change["line"]]=change["before"]
        if inverse.sub(lambda m:reverse[m[0]],"".join(undo))!=old: raise ValueError("Binding edit is lossy")
        part["text"]=modified
        edits.append({"part":j,"before_hash":stable_hash(old),"after_hash":stable_hash(modified),"line_edits":changes})
    return result,{"rename":ids,"edits":edits,"reversible":True}


def observations(values,bins):
    valid=[(b,float(v)) for b,v in zip(bins,values,strict=True) if v is not None]
    if any(not math.isfinite(v) for _,v in valid): raise ValueError("Nonfinite observation")
    if not valid: return None
    return {"first":valid[0],"last":valid[-1],"minimum":min(valid,key=lambda p:p[1]),"maximum":max(valid,key=lambda p:p[1])}


def fmt(value):
    return format(float(value),'.5g')


def summary_lines(cards,stats):
    lines=[]
    for card in cards:
        cid=card["id"]; owner=card["entity"]; unit=card["unit"]
        lines.append(f'{cid} | {owner} | {card["title"]} | {unit}')
        if card["kind"]=="metric":
            row=stats[cid]
            lines.append(' ; '.join(f'{k} {fmt(row[k][1])} @bin{row[k][0]}' for k in ("first","last","minimum","maximum")))
        else:
            d=card["data"]
            lines.append(f'exclusive p95: reference {fmt(d["before"])} ; current {fmt(d["after"])}')
    return lines


def compile_public(bundle,raw,c):
    _,series,clock=public_series(bundle)
    canonical,binding=canonicalize(raw,bundle)
    safe=deepcopy(canonical); safe.insert(1,{"type":"text","text":SAFE})
    cards=[]; stats={}; omitted=[]
    for original in bundle["evidence"]["cards"]:
        if original["kind"] not in {"metric","trace"}: continue
        card=deepcopy(original); card["id"]=binding["rename"][card["id"]]
        # Original full details remain in common raw text; charts show shape and local latency.
        card["data"]["details"]=[]
        if card["kind"]=="metric":
            observed=observations(card["data"]["values"],card["data"]["bins"])
            if observed is None: omitted.append(card["id"]); continue
            stats[card["id"]]=observed
        card["title"]=card["id"]+" · "+card["title"]
        cards.append(card)
    cards.sort(key=lambda x:(int(x["entity"]),x["id"]))
    evidence={"schema":"CanvasEvidenceV1","cards":cards}; validate_evidence(evidence)
    lines=summary_lines(cards,stats)
    payload={"schema":"BoundObservedWindowV1","clock":clock,"evidence":evidence,"statistics":stats,"lines":lines}
    texts={}
    for arm in ARMS:
        parts=deepcopy(raw if arm.startswith("RAW") else canonical if arm=="CANON_TEXT" else safe)
        if arm.startswith("WINDOW"):
            parts.insert(len(parts)-1,{"type":"text","text":GUIDE})
            # Strong text summarizes the same original vectors; visual uses their curves.
            if arm=="WINDOW_TEXT": parts.insert(len(parts)-1,{"type":"text","text":"\n".join(lines)})
        texts[arm]=parts
    public={"system":bundle["system"],"candidates":deepcopy(bundle["candidates"]),"original_facts_hash":bundle["facts_hash"],
            "facts_hash":stable_hash(raw),"payload":payload,"texts":texts,"images":{},"infeasible":{}}
    visible_audit(public)
    return public,{"binding":binding,"omitted_empty_metric_cards":omitted,"original_metrics":len(series),
                   "plotted_metrics":len(stats),"trace_cards":sum(c["kind"]=="trace" for c in cards),"source_facts_retained":True}


def design_for(payload,c,arm):
    if arm not in VISUAL: raise ValueError("Text arm has no design")
    cfg=c["canvas"]; evidence=deepcopy(payload["evidence"])
    if arm=="WINDOW_PIXEL":
        # One exact-text panel; generic registered component, never a bespoke raster path.
        evidence={"schema":"CanvasEvidenceV1","cards":[{"id":"SUMMARY","kind":"literal","title":"Full-window observations",
            "entity":None,"unit":"","data":{"lines":payload["lines"]}}]}
        tree={"id":"summary","type":"panel","card":"SUMMARY","component":"literal.text"}
        # Bound text widths conservatively before the browser's actual overflow audit.
        rows=sum(max(1,math.ceil(len(line)*cfg["font_size"]*.64/(cfg["width"]-2*cfg["padding"]-34))) for line in payload["lines"])
        height=max(600,180+math.ceil(rows*cfg["font_size"]*1.4))
    else:
        panels=[{"id":"p_"+card["id"],"type":"panel","card":card["id"],
                 "component":"metric.line" if card["kind"]=="metric" else "trace.paired_bars"} for card in evidence["cards"]]
        tree={"id":"windows","type":"grid","columns":2,"children":panels}
        height=86+cfg["padding"]+math.ceil(len(panels)/2)*(cfg["panel_height"]+cfg["gap"])-cfg["gap"]
    if height>cfg["maximum_height"]: raise ValueError("Readable design exceeds preregistered canvas capacity")
    base={"schema":"DashboardDesignV1","viewport":{"width":cfg["width"],"height":height},"theme":"light",
          "font_size":cfg["font_size"],"gap":cfg["gap"],"padding":cfg["padding"],"scale":1,
          "tree":tree,"bindings":[],"indexing":{"visible":True,"start":1}}
    if arm=="WINDOW_MARKLESS":
        base["presentation"]={card["id"]:{"marks":False,"details":False} for card in evidence["cards"]}
    # Registered operations really execute; the program and each intermediate hash are retained.
    operations=[{"op":"appearance","args":{"theme":"dark","font_size":cfg["font_size"]}},
                {"op":"indexing","args":{"visible":False,"start":1}},
                {"op":"spacing","args":{"gap":cfg["gap"],"padding":cfg["padding"]}}]
    design,audit=apply_operations(evidence,base,operations); compile_design(evidence,design)
    return evidence,base,operations,design,audit


def parts_for(public,arm,png=None):
    if arm not in ARMS: raise ValueError("Unknown arm")
    parts=deepcopy(public["texts"][arm])
    if arm in VISUAL:
        if png is None or not png.startswith(b'\x89PNG\r\n\x1a\n'): raise ValueError("Committed PNG required")
        return [{"type":"image","png":png}]+parts
    if png is not None: raise ValueError("Text arm cannot contain PNG")
    return parts


def visible_audit(public):
    text=dumps({k:public[k] for k in ("system","texts","payload")})
    if re.search(r'(?i)(INC-[A-F0-9]{8}|aiops202[25]|aegislab|ground_truth|injection_time|/home/|/scratch/)',text):
        raise ValueError("Private/source metadata in model-visible input")
    assert public['texts']['RAW_TEXT']==public['texts']['RAW_REPEAT']
    for arm in ('WINDOW_MARKLESS','WINDOW_REPEAT'):
        assert public['texts'][arm]==public['texts']['WINDOW_VISUAL']
    base=public['texts']['WINDOW_TEXT']
    assert base[-2]['text']=='\n'.join(public['payload']['lines'])
    assert base[:-2]+base[-1:]==public['texts']['WINDOW_PIXEL']==public['texts']['WINDOW_VISUAL']
    return {"status":"passed","same_underlying_facts":True,"summary_text_pixel_equal":True}
