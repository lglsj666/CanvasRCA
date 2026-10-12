"""Pure observed-envelope compiler and deterministic RQ-local pixel adapter.

Only explicit public DTOs/font bytes enter; evaluator labels and IO are absent.
"""
from copy import deepcopy
from io import BytesIO
import json
import math
import re
from RQs.RQ3_11.src.exps import public_series
from .utils import ARMS, stable_hash

VISUAL={"EVENT_VISUAL","EVENT_PIXEL_TEXT","EVENT_VISUAL_REPEAT"}
REPEATS={"EXACT_REPEAT","EVENT_VISUAL_REPEAT"}
READING=(
    "Literal reading and evidence citations: retain explicit source units; an unverified unit label "
    "does not authorize conversion. log2 ratios are not fold changes. Three-digit IDs denote services, "
    "four-digit IDs nodes, five-digit IDs pods; bind an instance through the actual relationship facts. "
    "Independent inclusive/exclusive p95 quantiles cannot be subtracted as paired durations. "
    "Binned observation order and anomaly-onset summaries do not certify causal order or fault origin. "
    "In the required reason, cite actual M/R/L/G field IDs and distinguish measured evidence from inference. "
    "Keep the required ranked top-five JSON schema.\n"
)
GRAMMAR=(
    "Observed excursion table: each row binds an original M metric. Bin i covers [i*d/64,(i+1)*d/64] "
    "relative seconds, with the last edge at d. Reference bins end at/before the public split; current "
    "bins start at/after it. A crossing bin is omitted. This split is not known fault injection time. "
    "Envelope=[min(reference)-3*IQR,max(reference)+3*IQR], IQR=linear Q75-Q25. Reference is not "
    "certified healthy. Require12 reference/3 current finite samples and60% coverage of genuine scheduled "
    "slots in each phase; no interpolation. The same64 states read left to right: '+' above the upper "
    "bound, '-' below the lower bound, '.' within inclusive bounds, space unavailable/excluded/unsampled. "
    "Finite qualified reference bins are '.', including constant-zero reference. Missing is never zero. "
    "No excursions does not certify health. Counters, workload drift and configuration changes may depart "
    "from the envelope without being root causes. Colors/signs encode direction, not probability. "
    "Only qualified derived rows appear; omitted rows remain in the exact raw evidence. "
    "All original M/R/L/G facts and candidates remain in text.\n"
)
TABLE_HEAD="Observed excursion table\nBins0..63 left to right; states use the common legend."
COLORS={"background":(15,23,32),"panel":(24,37,48),"text":(232,239,244),
        "muted":(160,183,202),"grid":(45,64,80),"+":(99,188,251),"-":(255,173,104),".":(119,141,162)}


def dumps(value):
    return json.dumps(value,ensure_ascii=False,separators=(",",":"),allow_nan=False)


def quantile(values,p):
    ordered=sorted(values); pos=(len(ordered)-1)*p; left=math.floor(pos); right=math.ceil(pos)
    return ordered[left]+(ordered[right]-ordered[left])*(pos-left)


def phases(clock):
    width=clock["duration"]/64
    return ([i for i in range(64) if (i+1)*width<=clock["split"]],
            [i for i in range(64) if i*width>=clock["split"]])


def excursion(series,clock,support,cfg):
    values=series["values"]
    if len(values)!=64 or any(v is not None and not math.isfinite(v) for v in values):
        raise ValueError("Invalid finite original vector")
    slots=set(support); reference,current=phases(clock)
    ref=[i for i in reference if i in slots]; cur=[i for i in current if i in slots]
    ri=[i for i in ref if values[i] is not None]; ci=[i for i in cur if values[i] is not None]
    if (len(ri)<cfg["reference_min"] or len(ci)<cfg["current_min"]
            or len(ri)/max(1,len(ref))<cfg["phase_coverage_min"]
            or len(ci)/max(1,len(cur))<cfg["phase_coverage_min"]):
        return None
    reference_values=[values[i] for i in ri]
    iqr=quantile(reference_values,.75)-quantile(reference_values,.25)
    lo=min(reference_values)-cfg["iqr_margin"]*iqr
    hi=max(reference_values)+cfg["iqr_margin"]*iqr
    if not math.isfinite(lo) or not math.isfinite(hi): raise ValueError("Envelope overflow")
    states=[" "]*64
    for i in ri: states[i]="."
    for i in ci: states[i]="+" if values[i]>hi else "-" if values[i]<lo else "."
    return {"id":series["id"],"entity":series["entity"],"metric":series["metric"],"unit":series["unit"],
            "lower":lo,"upper":hi,"reference_n":len(ri),"current_n":len(ci),"states":"".join(states)}


def table_lines(payload):
    return TABLE_HEAD.splitlines()+[dumps([r["id"],r["states"]]) for r in payload["rows"]]


def compile_public(bundle,base_public,support,c):
    _,series,clock=public_series(bundle)
    if (support.get("schema")!="CanonicalSamplingSlotsV2" or not support["sampling_bins"]
            or support["sampling_bins"]!=sorted(set(support["sampling_bins"]))
            or any(type(i) is not int or not 0<=i<64 for i in support["sampling_bins"])):
        raise ValueError("Genuine original sampling support required")
    if (base_public["original_facts_hash"]!=bundle["facts_hash"]
            or base_public["system"]!=bundle["system"] or base_public["candidates"]!=bundle["candidates"]
            or base_public["texts"]["EXACT_TEXT"]!=base_public["texts"]["EXACT_REPEAT"]):
        raise ValueError("Frozen exact baseline differs")
    if any(v is not None and i not in support["sampling_bins"] for s in series for i,v in enumerate(s["values"])):
        raise ValueError("Original observation outside genuine sampling slots")
    rows=[r for s in series if (r:=excursion(s,clock,support["sampling_bins"],c["excursion"])) is not None]
    payload={"schema":"ObservedExcursionTableV1","clock":clock,"rows":rows}
    bindings={"clock":[clock["split"],clock["duration"]],
        "fields":["id","entity","metric","unit","lower","upper","reference_n","current_n"],
        "rows":[[r[k] for k in ("id","entity","metric","unit","lower","upper","reference_n","current_n")] for r in rows]}
    base=deepcopy(base_public["texts"]["EXACT_TEXT"])
    base.insert(1,{"type":"text","text":READING})
    texts={}
    for arm in ARMS:
        parts=deepcopy(base)
        if not arm.startswith("EXACT") and rows:
            parts.insert(len(parts)-1,{"type":"text","text":GRAMMAR+"Excursion bindings\n"+dumps(bindings)})
            if arm=="EVENT_TEXT":
                parts.insert(len(parts)-1,{"type":"text","text":"\n".join(table_lines(payload))})
        texts[arm]=parts
    public={"system":bundle["system"],"candidates":deepcopy(bundle["candidates"]),
        "original_facts_hash":bundle["facts_hash"],"facts_hash":base_public["facts_hash"],
        "payload":payload,"texts":texts,"images":{},"infeasible":{}}
    entities={r["entity"] for r in rows if "+" in r["states"] or "-" in r["states"]}
    audit={"qualified_rows":len(rows),"omitted_rows":12-len(rows),"excursion_entities":sorted(entities),
        "applicable":len(entities)>=c["readiness"]["minimum_excursion_entities"],
        "base_facts_retained":True,"sampling_support":support,"new_original_metrics":0}
    visible_audit(public)
    return public,audit


def parts_for(public,arm,png=None):
    if arm not in ARMS: raise ValueError("Unknown arm")
    parts=deepcopy(public["texts"][arm])
    if arm in VISUAL and public["payload"]["rows"]:
        if png is None or not png.startswith(b"\x89PNG\r\n\x1a\n"): raise ValueError("Actual committed PNG required")
        return [{"type":"image","png":png}]+parts
    if png is not None: raise ValueError("Image forbidden for text/empty table")
    return parts


def visible_audit(public):
    text=dumps({"system":public["system"],"texts":public["texts"],"payload":public["payload"]})
    if re.search(r"(?i)(INC-[A-F0-9]{8}|aiops202[25]|aegislab|ground_truth|injection_time|/home/|/scratch/)",text):
        raise ValueError("Source/private metadata in visible evidence")
    if any(k in text for k in ('"source_key"','"fault_type"','"cpu_ranking"')): raise ValueError("Nonpublic field")
    if public["texts"]["EXACT_TEXT"]!=public["texts"]["EXACT_REPEAT"]: raise ValueError("Text repeat mismatch")
    for arm in ("EVENT_PIXEL_TEXT","EVENT_VISUAL_REPEAT"):
        if public["texts"][arm]!=public["texts"]["EVENT_VISUAL"]: raise ValueError("Visual/repeat common parts differ")
    if public["payload"]["rows"]:
        text_parts=public["texts"]["EVENT_TEXT"]
        if text_parts[-2]["text"]!="\n".join(table_lines(public["payload"])):
            raise ValueError("State-table text parity")
        if text_parts[:-2]+text_parts[-1:]!=public["texts"]["EVENT_VISUAL"]: raise ValueError("Other facts differ")
    elif any(public["texts"][a]!=public["texts"]["EXACT_TEXT"] for a in ARMS):
        raise ValueError("Empty table must fall back identically")
    return {"status":"passed","fact_parity":True,"unknown_cells_omitted":True}


def render_png(payload,c,font_bytes,pixel_text=False):
    """Deterministic pure raster adapter; all semantics enter as public DTOs."""
    from PIL import Image, ImageDraw, ImageFont
    if not payload["rows"]: raise ValueError("No image for empty derived table")
    cfg=c["canvas"]; width=cfg["width"]; height=max(cfg["minimum_height"],256+cfg["row_height"]*len(payload["rows"]))
    font=ImageFont.truetype(BytesIO(font_bytes),cfg["font_size"])
    img=Image.new("RGB",(width,height),COLORS["background"]); draw=ImageDraw.Draw(img)
    labels=[]; primitives=[]
    def label(x,y,text,color=COLORS["text"]):
        bbox=draw.textbbox((x,y),text,font=font)
        if bbox[0]<0 or bbox[1]<0 or bbox[2]>=width or bbox[3]>=height:
            raise ValueError("Text clips canvas")
        draw.text((x,y),text,font=font,fill=color)
        labels.append({"text":text,"bbox":list(bbox)})
    if pixel_text:
        lines=table_lines(payload)
        for i,line in enumerate(lines): label(24,32+i*cfg["row_height"],line)
        primitives=[{"fact_id":r["id"],"states":r["states"],"text_line_index":j+2,
                     "bbox":labels[j+2]["bbox"]} for j,r in enumerate(payload["rows"])]
    else:
        label(24,24,"Observed excursions / common relative time")
        label(24,57,"+ above envelope   - below   . inside   blank unavailable",COLORS["muted"])
        label(24,84,"Original metrics and exact bindings are in adjacent text",COLORS["muted"])
        left=cfg["plot_left"]; cell=(width-left-cfg["plot_right"])/64
        split_x=left+payload["clock"]["split"]/payload["clock"]["duration"]*64*cell
        for bin_id in range(0,64,8): label(left+bin_id*cell,126,str(bin_id),COLORS["muted"])
        label(left+63*cell-9,126,"63",COLORS["muted"])
        draw.line((split_x,152,split_x,172+len(payload["rows"])*cfg["row_height"]),fill=COLORS["muted"],width=1)
        for j,row in enumerate(payload["rows"]):
            cy=177+j*cfg["row_height"]
            entity=row["entity"]; kind={3:"service",4:"node",5:"pod"}.get(len(entity))
            if kind is None: raise ValueError("Unbound anonymous entity type")
            label(24,cy-11,row["id"]+" "+kind+entity)
            draw.line((left,cy,width-cfg["plot_right"],cy),fill=COLORS["grid"],width=1)
            points=[]
            for i,state in enumerate(row["states"]):
                cx=round(left+(i+.5)*cell); yy=cy-8 if state=="+" else cy+8 if state=="-" else cy
                if state!=" ":
                    draw.rectangle((cx-2,yy-2,cx+2,yy+2),fill=COLORS[state])
                points.append([cx,yy,state])
            primitives.append({"fact_id":row["id"],"states":row["states"],"points":points,
                "bbox":[left,cy-14,width-cfg["plot_right"],cy+14]})
        label(24,height-50,"Bins0..63; the vertical rule is the public split",COLORS["muted"])
        label(24,height-26,"Directions and order are observations, not causal certificates",COLORS["muted"])
    output=BytesIO(); img.save(output,format="PNG",optimize=False,compress_level=6)
    png=output.getvalue()
    return png,{"status":"passed","schema":"ObservedExcursionRenderV1","pixel_text":pixel_text,
        "width":width,"height":height,"payload_hash":stable_hash(payload),"labels":labels,
        "fact_primitives":primitives,"state_colors":{s:list(COLORS[s]) for s in ("+","-",".")}}
