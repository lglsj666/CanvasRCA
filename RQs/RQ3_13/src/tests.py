"""Meaningful numerical, binding, real-raster and whole-roster CPU qualification."""
from collections import Counter
from io import BytesIO
import time
import math
import tempfile
from . import exps
from .utils import ARMS, MODEL, VERSION, ROOT, path, register, runtime, source_contract, read_json, write_json, sha_file, stable_hash, flag, logical_key


def independent_row(series,clock,slots,cfg):
    """Independent NumPy envelope/classifier, not renderer/manifests as oracle."""
    import numpy as np
    v=np.array([np.nan if x is None else x for x in series["values"]],dtype=float)
    indices=np.arange(64); left=indices*clock["duration"]/64; right=(indices+1)*clock["duration"]/64
    scheduled=np.isin(indices,slots)
    reference=scheduled & (right<=clock["split"]); current=scheduled & (left>=clock["split"])
    rf=reference & np.isfinite(v); cf=current & np.isfinite(v)
    if (rf.sum()<cfg["reference_min"] or cf.sum()<cfg["current_min"]
            or rf.sum()/max(1,reference.sum())<cfg["phase_coverage_min"]
            or cf.sum()/max(1,current.sum())<cfg["phase_coverage_min"]): return None
    q=np.quantile(v[rf],[.25,.75],method="linear"); margin=cfg["iqr_margin"]*(q[1]-q[0])
    low=float(v[rf].min()-margin); high=float(v[rf].max()+margin)
    states=np.full(64," ",dtype="U1"); states[rf]="."
    states[cf & (v<low)]="-"; states[cf & (v>high)]="+"; states[cf & (v>=low)&(v<=high)]="."
    return {"lower":low,"upper":high,"reference_n":int(rf.sum()),"current_n":int(cf.sum()),"states":"".join(states)}


def unit_tests(c):
    cfg=c["excursion"]; clock={"split":32,"duration":64}; checks=[]
    series={"id":"M01","entity":"123","metric":"value","unit":"source_unit","values":[0.]*32+[0.,1.,-1.,0.]*8}
    row=exps.excursion(series,clock,list(range(64)),cfg)
    assert row["lower"]==row["upper"]==0 and row["states"]=="."*32+".+-."*8
    checks.append("constant-zero reference remains defined; true excursions are never zero-filled")
    for values in ([None]*64,[None]*21+[1.]*43,[0.]*32+[None]*30+[1.]*2):
        assert exps.excursion({**series,"values":values},clock,list(range(64)),cfg) is None
    slots=list(range(0,64,2)); values=[0. if i%2==0 else None for i in range(64)]
    row=exps.excursion({**series,"values":values},clock,slots,cfg)
    assert row and row["reference_n"]==16 and row["states"]==". "*32
    assert exps.excursion({**series,"values":[None if i<14 else v for i,v in enumerate(values)]},clock,slots,cfg) is None
    checks.append("genuine sampling support, null denominator, minimum samples and no interpolation")
    cross={"duration":64,"split":32.5}
    crossing=exps.excursion(series,cross,list(range(64)),cfg)
    assert crossing["states"][32]==" " and 32 not in sum(exps.phases(cross),[])
    checks.append("crossing bins excluded; public clock never changed")
    import numpy as np
    rng=np.random.default_rng(42)
    for _ in range(40):
        raw=rng.normal(size=64).tolist(); raw[33]=20.; raw[34]=-20.; raw[41]=None
        sample={**series,"values":raw}; a=exps.excursion(sample,clock,list(range(64)),cfg); b=independent_row(sample,clock,list(range(64)),cfg)
        assert a["states"]==b["states"]
        for key in ("lower","upper"): assert math.isclose(a[key],b[key],rel_tol=1e-12,abs_tol=1e-12)
    checks.append("independent NumPy quantiles/states, positive/negative excursions and exact boundary semantics")
    fixture={"schema":"ObservedExcursionTableV1","clock":clock,"rows":[exps.excursion(series,clock,list(range(64)),cfg)]}
    font=path("build/rq313_renderer/DejaVuSansMono.ttf").read_bytes()
    for pixel in (False,True):
        first=exps.render_png(fixture,c,font,pixel); assert first==exps.render_png(fixture,c,font,pixel)
        inspect_png(fixture,first[0],first[1],pixel)
    checks.append("actual raster geometry/state/text equality and deterministic bytes")
    fixture["rows"]=[]
    public={"texts":{a:[{"type":"text","text":"raw"}] for a in ARMS},"payload":fixture,"system":"task"}
    for arm in ARMS: assert exps.parts_for(public,arm)==public["texts"]["EXACT_TEXT"]
    checks.append("empty derived table omits all imagery while preserving all arms/denominators")
    with tempfile.TemporaryDirectory(prefix="rq313-marker-") as folder:
        from pathlib import Path
        root=Path(folder); key=logical_key("case","EVENT_VISUAL")
        write_json(root/"flags"/(key+".json"),{"case":"case","arm":"EVENT_VISUAL","status":"done","call_key":"abc"})
        assert flag(root,"case","EVENT_VISUAL") is None
        write_json(root/"completed/abc.json",{"status":"complete"})
        assert flag(root,"case","EVENT_VISUAL")["status"]=="done"
    assert exps.REPEATS=={"EXACT_REPEAT","EVENT_VISUAL_REPEAT"}
    checks.append("atomic commit required for resume; both identical-input repeats stay real")
    return checks


def inspect_png(payload,png,manifest,pixel):
    from PIL import Image
    img=Image.open(BytesIO(png)); img.load()
    if img.size!=(manifest["width"],manifest["height"]) or img.info:
        raise ValueError("PNG geometry or hidden metadata")
    if manifest["payload_hash"]!=stable_hash(payload) or manifest["pixel_text"]!=pixel:
        raise ValueError("Manifest payload identity")
    if [p["fact_id"] for p in manifest["fact_primitives"]]!=[r["id"] for r in payload["rows"]]:
        raise ValueError("Primitive inventory/fact binding")
    for row,primitive in zip(payload["rows"],manifest["fact_primitives"],strict=True):
        if row["states"]!=primitive["states"]: raise ValueError("State inventory mismatch")
        if pixel:
            if manifest["labels"][primitive["text_line_index"]]["text"]!=exps.dumps([row["id"],row["states"]]):
                raise ValueError("Pixel text differs from the literal text table")
        else:
            for i,(x,y,state) in enumerate(primitive["points"]):
                if state!=row["states"][i]: raise ValueError("State primitive order")
                if state!=" " and img.getpixel((x,y))!=exps.COLORS[state]: raise ValueError("Actual pixel state mismatch")
    if pixel and [r["text"] for r in manifest["labels"]]!=exps.table_lines(payload):
        raise ValueError("Pixel screenshot text not identical")
    boxes=[r["bbox"] for r in manifest["labels"]]
    for i,a in enumerate(boxes):
        for b in boxes[i+1:]:
            if max(a[0],b[0])<min(a[2],b[2]) and max(a[1],b[1])<min(a[3],b[3]):
                raise ValueError("Actual text boxes overlap")
    return {"status":"passed","states":64*len(payload["rows"]),"labels":len(boxes)}


def cpu(c,smoke=False):
    started=time.monotonic(); checks=unit_tests(c)
    from .gates import require_renderer_build
    require_renderer_build()
    from RQs.RQ3_3.src.utils import OfflineTokens
    from RQs.RQ3_12.src.tests import checkpoint_audit
    from RQs.RQ3_12.src.utils import sampling_support
    loaded,spec=runtime(c); tokens=OfflineTokens({"unified":{"vllm":str(loaded.source)},"models":[MODEL]})
    root=path(c["preparation"]); rows=register(c)["smoke" if smoke else "cases"]
    contract=source_contract(); cases=[]; counts=[]; applicable=Counter(); ratios=[]; maximum_difference=0.; row_checks=0; png_checks=0
    font=path("build/rq313_renderer/DejaVuSansMono.ttf").read_bytes()
    smoke_ids={r["opaque_incident_id"] for r in register(c)["smoke"]}
    for row in rows:
        if time.monotonic()-started>c["cpu_seconds"]: raise TimeoutError("CPU qualification30-minute limit")
        oid=row["opaque_incident_id"]; marker=read_json(root/"flags"/(oid+".json")); public=read_json(root/"public"/(oid+".json"))
        if marker["status"]!="done" or marker["version"]!=VERSION or marker["preparation_source_contract"]!=contract:
            raise ValueError("Prepared source/version does not match")
        for category in ("public","private"):
            if sha_file(root/category/(oid+".json"))!=marker[category+"_sha256"]: raise ValueError("Prepared payload changed")
        parent=read_json(path(c["parent"])/"public"/(oid+".json")); base=read_json(path(c["base_preparation"])/"public"/(oid+".json"))
        support=read_json(root/"sampling_support"/(oid+".json")); _,series,clock=exps.public_series(parent)
        if sampling_support(c,row,clock)!=support: raise ValueError("Independent canonical source-clock support changed")
        rebuilt,audit=exps.compile_public(parent,base,support,c)
        if rebuilt["texts"]!=public["texts"] or rebuilt["payload"]!=public["payload"]: raise ValueError("Pure compiler replay mismatch")
        exps.visible_audit(public)
        for s in series:
            expected=independent_row(s,clock,support["sampling_bins"],c["excursion"])
            found=next((r for r in public["payload"]["rows"] if r["id"]==s["id"]),None)
            if (expected is None)!=(found is None): raise ValueError("Qualification of a row differs")
            if found:
                for k in ("states","reference_n","current_n"):
                    if expected[k]!=found[k]: raise ValueError("Independent state/missingness check")
                for k in ("lower","upper"):
                    difference=abs(expected[k]-found[k])/max(1.,abs(expected[k])); maximum_difference=max(maximum_difference,difference)
                    if difference>1e-12: raise ValueError("Independent envelope differs")
            row_checks+=1
        for arm,pixel in (("EVENT_VISUAL",False),("EVENT_PIXEL_TEXT",True)):
            if arm not in public["images"]: continue
            file=root/public["images"][arm]["path"]; manifest=read_json(file.parent/"manifest.json")
            if sha_file(file)!=public["images"][arm]["sha256"] or manifest["renderer_source"]!=contract["renderer"]:
                raise ValueError("PNG/renderer identity differs")
            inspect_png(public["payload"],file.read_bytes(),manifest,pixel); png_checks+=1
            if oid in smoke_ids and exps.render_png(public["payload"],c,font,pixel)[0]!=file.read_bytes():
                raise ValueError("Independent deterministic real-case rerender differs")
        if marker["canonical_arms"]["EXACT_REPEAT"]!="EXACT_REPEAT" or marker["canonical_arms"]["EVENT_VISUAL_REPEAT"]!="EVENT_VISUAL_REPEAT":
            raise ValueError("A repeat must never alias")
        inputs={}; excluded={}
        for arm in ARMS:
            image=public["images"].get(arm); png=(root/image["path"]).read_bytes() if image else None
            inputs[arm]=tokens.count(exps.parts_for(public,arm,png),public["system"],MODEL); counts.append(inputs[arm])
            if inputs[arm]+c["max_tokens"]>spec["max_model_len"]: excluded[arm]="intact input exceeds model context"
        if row["dataset"] in c["primary_datasets"]:
            applicable[row["dataset"]]+=int(audit["applicable"]); ratios.append((inputs["EVENT_VISUAL"],inputs["EXACT_TEXT"]))
        marker["context_excluded"]=excluded; write_json(root/"flags"/(oid+".json"),marker)
        cases.append({"case":oid,"dataset":row["dataset"],"inputs":inputs,"context_excluded":excluded,
                      "qualified_rows":audit["qualified_rows"],"excursion_entities":audit["excursion_entities"],"applicable":audit["applicable"]})
    ratio=sum(a for a,_ in ratios)/sum(b for _,b in ratios)
    full_pass=(sum(applicable.values())>=c["readiness"]["primary_cases_min"]
        and all(applicable[d]>=c["readiness"]["per_primary_dataset_cases_min"] for d in c["primary_datasets"])
        and ratio<=c["readiness"]["max_mean_input_ratio"] and not any(r["context_excluded"] for r in cases))
    checkpoint=checkpoint_audit(loaded) if not smoke else read_json(path(c["results"])/"qualification/cpu.json")["checkpoint_audit"]
    report={"status":"passed" if smoke or full_pass else "failed","source_contract":contract,"checks":checks,
        "scope":"smoke" if smoke else "full","case_ids":[r["opaque_incident_id"] for r in rows],"per_case":cases,
        "readiness_passed":full_pass,"applicable_cases":dict(applicable),"primary_mean_input_ratio":ratio,
        "max_input_tokens":max(counts),"output_budget":c["max_tokens"],"actual_png_checks":png_checks,
        "independent_original_rows":row_checks,"independent_envelope_max_relative_difference":maximum_difference,
        "canonical_sampling_support_independently_checked":True,"checkpoint_audit":checkpoint,
        "seconds":time.monotonic()-started,"gpu_calls":0}
    write_json(path(c["results"])/"qualification"/("cpu_smoke.json" if smoke else "cpu.json"),report)
    if not smoke and not full_pass: raise RuntimeError("Whole-roster applicability/cost/capacity failed; preserve result and stop before GPU")
    return {k:v for k,v in report.items() if k not in {"source_contract","per_case","checkpoint_audit"}}
