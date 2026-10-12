"""Future CPU qualification: dependency validation, parity, capacity, checkpoint.

Nothing in this file runs on import or in a static source review.
"""
from collections import Counter
from pathlib import Path
import math
import tempfile
import time

from . import exps
from .utils import (ARMS,MODEL,VERSION,path,register,runtime,source_contract,read_json,write_json,
                    sha_file,stable_hash,flag,logical_key,sampling_support,reference_support)


def unit_tests(c):
    cfg=c["response_model"]; clock={"split":32,"duration":64}; checks=[]
    x=[float(i%8) for i in range(32)]+[3.0,4.0,5.0,6.0]*8
    y=[2*v+10 for v in x]
    a={"id":"M01","entity":"123","metric":"cpu_usage","unit":"percent","values":x}
    b={"id":"M02","entity":"456","metric":"latency","unit":"us","values":y}
    measured=exps.measure(b,clock,cfg)
    model=exps.fit_dependency(a,b,clock,cfg)
    assert model["status"]=="qualified"
    result=exps.cell(a,b,model,measured,clock,cfg)
    assert result["expected"] is not None and result["status"]=="compatible"
    altered={**b,"values":y[:32]+[v+100 for v in y[32:]]}
    assert exps.fit_dependency(a,altered,clock,cfg)==model
    changed=exps.cell(a,altered,model,exps.measure(altered,clock,cfg),clock,cfg)
    assert changed["status"]=="unexplained" and changed["residual"]>3
    checks.append("reference-only validated response versus unexplained current change")
    extra={**a,"values":x[:32]+[100.0]*32}
    assert exps.cell(extra,b,model,measured,clock,cfg)["reason"]=="out_of_reference_support"
    checks.append("unseen anchor range cannot manufacture negative evidence")
    for values in ([None]*64,[0.0]*64,[None]*31+[1.0]*33):
        candidate={**b,"values":values}
        assert exps.measure(candidate,clock,cfg)["status"]=="unknown"
        assert exps.fit_dependency(a,candidate,clock,cfg)["status"]=="unknown"
    constant={**b,"values":[2.0]*64}
    constant_measurement=exps.measure(constant,clock,cfg)
    assert constant_measurement["status"]=="observed" and constant_measurement["scale"]==0.02
    assert constant_measurement["change"]==0 and exps.fit_dependency(a,constant,clock,cfg)["status"]=="unknown"
    ref,cur=exps.phases({"split":32.5,"duration":64})
    assert 32 not in ref+cur and set(ref).isdisjoint(cur)
    checks.append("missing/constant/zero variation and crossing-bin exclusions")
    sampled_clock={**clock,"sampling_bins":list(range(0,64,2))}
    sparse_a={**a,"values":[v if i%2==0 else None for i,v in enumerate(x)]}
    sparse_b={**b,"values":[v if i%2==0 else None for i,v in enumerate(y)]}
    assert exps.measure(sparse_b,clock,cfg)["status"]=="unknown"
    assert exps.measure(sparse_b,sampled_clock,cfg)["status"]=="observed"
    assert exps.fit_dependency(sparse_a,sparse_b,sampled_clock,cfg)["status"]=="qualified"
    truly_missing={**sparse_b,"values":[None if i<16 else v for i,v in enumerate(sparse_b["values"])]}
    assert exps.measure(truly_missing,sampled_clock,cfg)["status"]=="unknown"
    assert exps.sampled_phases(sampled_clock)[0]==list(range(0,32,2))
    checks.append("unsampled grid slots versus genuine missing scheduled observations")
    reversal={**b,"values":[2*v+10 if i<16 else -2*v+30 for i,v in enumerate(x[:32])]+y[32:]}
    assert exps.fit_dependency(a,reversal,clock,cfg)["status"]=="unknown"
    checks.append("nonstationary reference fails chronological held-out reliability")
    bundle={"candidates":["123","456","789","12345","6789"],"evidence":{"cards":[]}}
    compiled=exps.compile_model(bundle,[a,b],clock,cfg)
    assert any(p["entity"]=="123" and p["cells"][0]["status"]=="conditioned" for p in compiled["profiles"])
    assert all(p["entity"] not in {"789","12345","6789"} for p in compiled["profiles"])
    assert compiled["stats"][0]["entity"]=="123"  # Isolated resource retained.
    assert exps.unpack_matrix(exps.pack_matrix(exps.conditioned_matrix(compiled,cfg)))==exps.conditioned_matrix(compiled,cfg)
    checks.append("anchors excluded from self explanation; unknown candidates and exact matrix round-trip")
    matrix=exps.conditioned_matrix(compiled,cfg)
    assert all(v is None or v["status"] not in {"unknown","conditioned"} for r in matrix["rows"] for v in r["cells"])
    unavailable=exps.compile_model(bundle,[{**a,"values":[None]*64},{**b,"values":[None]*64}],clock,cfg)
    empty=exps.conditioned_matrix(unavailable,cfg)
    assert empty["targets"]==[] and empty["rows"]==[] and exps.unpack_matrix(exps.pack_matrix(empty))==empty
    checks.append("unavailable cells and empty rows/columns omitted without zero filling")
    import numpy as np
    rng=np.random.default_rng(42)
    driver=rng.normal(size=32); noise=rng.normal(size=32)
    fixtures=[]
    for name,eid,metric,values in (
            ("a","123","cpu_usage",list(driver)+[0.8]*32),
            ("b","456","load_average",list(driver+0.03*noise)+[-0.8]*32),
            ("t","789","latency",list(10+2*driver+0.4*noise)+[10.0]*32),
            ("u","6789","memory_usage",list(10+2*driver+1.2*noise)+[10.0]*32)):
        fixtures.append({"id":name,"entity":eid,"metric":metric,"unit":"source_unit",
                         "values":list(map(float,values)),"source_key":"synthetic-"+name})
    pool={"schema":"PublicReferenceOperandPoolV3","series":fixtures}
    operands,review=exps.select_reference_operands(pool,bundle,clock,c)
    assert len(operands)>=4 and len(operands)<=12 and review["supported_candidate_pairs"]>0
    assert abs(review["target_reference_correlation"])<0.98
    assert all(set(s)=={"id","entity","metric","unit","values"} for s in operands)
    assert exps.compile_model(bundle,operands,clock,cfg)["competing"]
    # An out-of-support current phase must not be rehabilitated by selection.
    outside={"schema":pool["schema"],"series":[{**s,"values":s["values"][:32]+[1e6]*32} for s in fixtures]}
    absent,review_outside=exps.select_reference_operands(outside,bundle,clock,c)
    assert absent==[] and review_outside["candidate_target_predictions"]==0
    assert review_outside["qualified_edges"]==review["qualified_edges"]
    checks.append("full public pool selection preserves reference acceptance, support and nonduplicate targets")
    with tempfile.TemporaryDirectory() as temporary:
        root=Path(temporary); oid="INC-TEST"; arm="EXACT_TEXT"
        write_json(root/"flags"/(logical_key(oid,arm)+".json"),{"status":"done","case":oid,"arm":arm,"call_key":"synthetic"})
        assert flag(root,oid,arm) is None
        write_json(root/"completed/synthetic.json",{"status":"complete"})
        assert flag(root,oid,arm)["status"]=="done"
    checks.append("atomic commit presence determines resume without reopening graph")
    return checks


def checkpoint_audit(profile):
    """Independent bytes checked against already verified official identities.

    Prior manifest is an identity reference, not current qualification. No
    weights are loaded and no old artifact is changed.
    """
    expected=read_json(path("RQs/RQ3_11/results/protected_v2/analysis_reviewed_v1/checkpoint_verification.json"))
    if expected.get("status")!="passed" or expected.get("tokenizer_status")!="passed":
        raise ValueError("Official checkpoint identity authority missing")
    directory=profile.model_path(MODEL)
    receipt=read_json(directory/"download_manifest.json")
    if receipt["observed_revision"]!=profile.model(MODEL)["repository_revision"]:
        raise ValueError("Checkpoint revision changed")
    files=[]
    for entry in expected["files"]+expected["tokenizer_processor_files"]:
        name=entry["file"]; file=directory/name
        if Path(name).is_absolute() or ".." in Path(name).parts or sha_file(file)!=entry["sha256"]:
            raise ValueError("Checkpoint/tokenizer identity changed: "+name)
        files.append({"file":name,"sha256":entry["sha256"]})
    return {"status":"passed","files":files,"revision":receipt["observed_revision"],
            "identity_authority_sha256":sha_file(path("RQs/RQ3_11/results/protected_v2/analysis_reviewed_v1/checkpoint_verification.json"))}


def cpu(c,smoke=False):
    started=time.monotonic(); checks=unit_tests(c)
    from .gates import require_renderer_build
    require_renderer_build()
    from RQs.RQ3_3.src.utils import OfflineTokens
    loaded,spec=runtime(c)
    tokens=OfflineTokens({"unified":{"vllm":str(loaded.source)},"models":[MODEL]})
    root=path(c["preparation"]); rows=register(c)["smoke" if smoke else "cases"]
    contract=source_contract(); cases=[];counts=[]; competing=Counter(); ratios=[]
    for row in rows:
        if time.monotonic()-started>c["cpu_seconds"]:
            raise TimeoutError("CPU qualification30minute limit")
        oid=row["opaque_incident_id"]
        public=read_json(root/"public"/(oid+".json"));marker=read_json(root/"flags"/(oid+".json"))
        if marker["preparation_source_contract"]!=contract:
            raise ValueError("Prepared source differs from current qualified code")
        exps.visible_audit(public)
        parent=read_json(path(c["parent"])/"public"/(oid+".json"))
        support=read_json(root/"sampling_support"/(oid+".json"))
        assert sha_file(root/"sampling_support"/(oid+".json"))==marker["sampling_support_sha256"]
        _,_,clock=exps.public_series(parent)
        assert support==sampling_support(c,row,clock)
        operands=read_json(root/"reference_support"/(oid+".json"))
        assert sha_file(root/"reference_support"/(oid+".json"))==marker["reference_support_sha256"]
        assert operands==reference_support(c,row,clock)
        rebuilt,audit=exps.compile_public(parent,c,support,operands)
        assert rebuilt["texts"]==public["texts"] and rebuilt["payload"]==public["payload"]
        assert marker["canonical_arms"]["EXACT_REPEAT"]=="EXACT_REPEAT"
        checked={};excluded={}
        for arm in ARMS:
            image=public["images"].get(arm); png=(root/image["path"]).read_bytes() if image else None
            if image:
                assert sha_file(root/image["path"])==image["sha256"]
                manifest=read_json((root/image["path"]).parent/"manifest.json")
                assert manifest["status"]=="passed" and manifest["renderer_source"]==contract["renderer"]
            n=tokens.count(exps.parts_for(public,arm,png),public["system"],MODEL)
            checked[arm]=n;counts.append(n)
            if n+c["max_tokens"]>spec["max_model_len"]:
                excluded[arm]=f"intact{n}+{c['max_tokens']} exceeds{spec['max_model_len']}"
        # Preflight is whole-roster and public-only; failures stop the method,
        # never select a more convenient inference cohort or discard roots.
        if row["dataset"] in c["primary_datasets"]:
            competing[row["dataset"]]+=int(audit["competing"])
            ratios.append((checked["COND_VISUAL"],checked["EXACT_TEXT"]))
        marker["context_excluded"]=excluded; write_json(root/"flags"/(oid+".json"),marker)
        cases.append({"case":oid,"dataset":row["dataset"],"inputs":checked,"context_excluded":excluded,
                      "competing":audit["competing"],"qualified_dependencies":audit["qualified_dependencies"],
                      "prediction_availability":audit["prediction_availability"],"displayed_profile_anchors":audit["displayed_profile_anchors"],
                      "reference_selection":audit["reference_selection"]})
    mean_ratio=sum(a for a,_ in ratios)/sum(b for _,b in ratios)
    full_pass=(sum(competing.values())>=c["readiness"]["primary_competing_cases_min"]
               and all(competing[d]>=c["readiness"]["per_primary_dataset_competing_cases_min"] for d in c["primary_datasets"])
               and mean_ratio<=c["readiness"]["max_mean_input_ratio"] and not any(r["context_excluded"] for r in cases))
    checkpoint=checkpoint_audit(loaded)
    report={"status":"passed" if smoke or full_pass else "failed","source_contract":source_contract(),"checks":checks,
            "scope":"smoke" if smoke else "full","case_ids":[r["opaque_incident_id"] for r in rows],"per_case":cases,
            "readiness_passed":full_pass if not smoke else False,"competing_cases":dict(competing),
            "primary_mean_input_ratio":mean_ratio,"max_input_tokens":max(counts),"output_budget":c["max_tokens"],
            "checkpoint_audit":checkpoint,"seconds":time.monotonic()-started,"gpu_calls":0}
    write_json(path(c["results"])/"qualification"/("cpu_smoke.json" if smoke else "cpu.json"),report)
    if not smoke and not full_pass:
        raise RuntimeError("Whole-roster applicability/cost/capacity failed; stop before GPU; preserve failed report")
    return {k:v for k,v in report.items() if k not in {"source_contract","per_case","checkpoint_audit"}}
