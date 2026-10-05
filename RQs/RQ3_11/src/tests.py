"""Meaningful numeric boundary, identity, parity and actual-processor checks."""
import math
import tempfile
import time
from pathlib import Path

from . import exps
from .utils import (ARMS,MODEL,VERSION,path,config,register,runtime,source_contract,
                    read_json,write_json,sha_file,stable_hash,flag,logical_key,phase_arms)


def unit_tests(c):
    checks=[]
    clock={"split":32,"duration":64}
    samples=[None]*64,[2.0]*64,[0.0]*64,list(range(64)),[1.0]*32+[9.0]*32,[1.0]*63+[100.0]
    for values in samples:
        s={"id":"M01","values":values,"raw":[None if v is None else str(v) for v in values]}
        for budget in c["budgets"].values():
            r,a=exps.quantize(s,clock,budget,c["operators"])
            assert exps.diagnostic_signature(exps.decode(r),clock,c["operators"])==exps.diagnostic_signature(values,clock,c["operators"])
            assert [v is None for v in exps.decode(r)]==[v is None for v in values]
            assert 0<=a["patch_points"]<=a["finite_points"]
    checks.append("all-missing/constant/zero-scale/ramp/shift/spike signatures and exact masks")
    values=[10+i*.013 for i in range(32)]+[11+i*.071 for i in range(32)]
    s={"id":"M01","values":values,"raw":list(map(str,values))}
    r,a=exps.quantize(s,clock,c["budgets"]["LOW"],c["operators"])
    assert a["coarse_signature_changed"] and a["patch_points"]>0
    assert exps.diagnostic_signature(exps.decode(r),clock,c["operators"])==exps.diagnostic_signature(values,clock,c["operators"])
    checks.append("nontrivial quantization loss repaired without outcomes or model calls")
    for v in ([None,False,True,False]*16,["1.23456789",None]*32,list(range(64))):
        assert exps.expand_records(exps.compact_series(v))==v
    checks.append("lossless masks, exact numeric strings and all64 bins")
    line='metric="with values=inside" values=["1",null] missing_mask=[false,true] unit="source_unit"'
    replaced=exps.replace_field(line,"values","values_codec",exps.compact_series(["1",None]))
    assert 'metric="with values=inside"' in replaced
    assert exps._public_field(replaced,"values_codec")==["1",None]
    checks.append("field replacement preserves quoted unrelated fields")
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp); oid="INC-TEST"; arm="EXACT_TEXT"; call="synthetic"
        write_json(root/"flags"/(logical_key(oid,arm)+".json"),{"status":"done","case":oid,"arm":arm,"call_key":call})
        assert flag(root,oid,arm) is None
        write_json(root/"completed"/(call+".json"),{"status":"complete"})
        assert flag(root,oid,arm)["status"]=="done"
    checks.append("atomic completion presence and incomplete-resume detection without prompt graph access")
    return checks


def cpu(c,smoke=False):
    started=time.monotonic();checks=unit_tests(c)
    from RQs.RQ3_3.src.utils import OfflineTokens
    loaded,spec=runtime(c)
    tokens=OfflineTokens({"unified":{"vllm":str(loaded.source)},"models":[MODEL]})
    root=path(c["preparation"]); reg=register(c); rows=reg["smoke" if smoke else "cases"]
    contract=source_contract()
    cases=[]; counts=[];loss=0;patches=0
    for row in rows:
        if time.monotonic()-started>c["cpu_seconds"]:
            raise TimeoutError("CPU qualification30minute bound")
        oid=row["opaque_incident_id"]
        public=read_json(root/"public"/(oid+".json"));marker=read_json(root/"flags"/(oid+".json"))
        exps.visible_audit(public)
        # Recompile from the immutable predecessor, before opening private files.
        parent=read_json(path(c["parent"])/"public"/(oid+".json"))
        rebuilt,audit=exps.compile_public(parent,c)
        assert rebuilt["texts"]==public["texts"] and rebuilt["payload"]==public["payload"]
        assert marker["canonical_arms"]["EXACT_REPEAT"]=="EXACT_REPEAT"
        checked={};excluded={}
        for arm in ARMS:
            png=(root/public["images"][arm]["path"]).read_bytes() if arm in public["images"] else None
            if png:
                assert sha_file(root/public["images"][arm]["path"])==public["images"][arm]["sha256"]
                manifest=read_json((root/public["images"][arm]["path"]).parent/"manifest.json")
                assert manifest["status"]=="passed"
                assert manifest["renderer_source"]==contract["renderer"]
            n=tokens.count(exps.parts_for(public,arm,png),public["system"],MODEL)
            checked[arm]=n;counts.append(n)
            if n+c["max_tokens"]>spec["max_model_len"]:
                excluded[arm]=f"intact{n}+{c['max_tokens']} exceeds{spec['max_model_len']}"
        for key,records in public["payload"]["records"].items():
            assert public["images"]["COARSE_VISUAL_"+key]==public["images"]["PROTECTED_VISUAL_"+key]
            for s,r in zip(public["payload"]["series"],records,strict=True):
                assert exps.diagnostic_signature(exps.decode(r),public["payload"]["clock"],c["operators"])==exps.diagnostic_signature(s["values"],public["payload"]["clock"],c["operators"])
            loss+=sum(x["coarse_signature_changed"] for x in audit[key]);patches+=sum(x["patch_points"] for x in audit[key])
        marker["context_excluded"]=excluded;write_json(root/"flags"/(oid+".json"),marker)
        cases.append({"case":oid,"dataset":row["dataset"],"inputs":checked,"context_excluded":excluded,"codec":audit})
    report={"status":"passed","source_contract":source_contract(),"checks":checks,
            "scope":"smoke" if smoke else "full","cases":len(cases),"case_ids":[r["opaque_incident_id"] for r in rows],
            "per_case":cases,"max_input_tokens":max(counts),"output_budget":c["max_tokens"],
            "coarse_signature_changed_series":loss,"repair_points":patches,"seconds":time.monotonic()-started,"gpu_calls":0}
    write_json(path(c["results"])/"qualification"/("cpu_smoke.json" if smoke else "cpu.json"),report)
    return {k:v for k,v in report.items() if k not in {"source_contract","per_case"}}
