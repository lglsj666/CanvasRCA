"""Future CPU regressions. Static checks parse this file but NEVER call these tests."""
from copy import deepcopy
from dataclasses import fields
from pathlib import Path
import json
import math
import tempfile
import time

from . import exps
from .utils import (MODEL, ARMS, path, register, runtime, read_json, write_json,
                    source_contract, logical_key, flag, stable_hash)


def unit_tests(c):
    import numpy as np
    from renderer.utils import compile_design, validate_evidence
    window=(0.,64.,127.)
    clock=np.arange(128,dtype=float)
    active={"status":"observed_active","source":"direct_operation_requests","operation":"GET",
            "reference":50,"current":50}
    unknown={"status":"unknown","source":"no_qualified_activity"}
    def obs(eid="12345",semantic="pod_cpu_usage"):
        return {"id":stable_hash([eid,semantic]),"entity":eid,"region":"M","semantic":semantic,"unit":"source_unit",
                "source_key":eid+"."+semantic,"values":{},"role":"unverified_numeric"}
    measured=lambda raw,activity=active:exps.measure(obs(),np.array(raw,dtype=float),clock,window,activity,c)
    assert {f.name for f in fields(exps.FrozenScopePoolV1)}=={"candidates","observations","relations","window","anchors"}
    assert measured([1.]*128)["status"]=="stable"
    assert measured([0.]*128)["status"]=="unknown"
    assert measured([1.]*128,unknown)["reason"]=="stable_but_activity_unknown"
    assert measured([1.]*64+[2.]*64)["status"]=="changed"
    assert measured([2.]*64+[1.]*64)["status"]=="changed"
    assert measured([100.]*64+[103.]*64)["status"]=="changed"
    assert measured([1.]*64+[float("nan")]*60+[1.]*4)["status"]=="unknown"
    # The same acquisition observed every 30s qualifies at its native cadence,
    # while losing >20% of readings or clock slots does not qualify.
    native_clock=np.arange(40,dtype=float)*30
    native=exps.measure(obs(),np.r_[np.ones(30),np.ones(10)*2],native_clock,(0.,900.,1170.),active,c)
    assert native["status"]=="changed" and native["coverage"]==1 and native["native_cadence_s"]==30
    lost=np.r_[np.ones(30),np.ones(10)*2]; lost[30:33]=np.nan
    assert exps.measure(obs(),lost,native_clock,(0.,900.,1170.),active,c)["status"]=="unknown"
    keep=np.r_[np.arange(30),np.arange(33,40)]
    assert exps.measure(obs(),np.r_[np.ones(30),np.ones(7)*2],native_clock[keep],(0.,900.,1170.),active,c)["coverage"]==.7
    assert measured([1.]*127+[1000.])["status"]=="unknown"
    negative=measured([-1.]*64+[-2.]*64)
    assert negative["status"]=="changed" and negative["delta"]<0
    tiny=measured([1e-50]*64+[2e-50]*64)
    assert tiny["status"]=="changed" and math.isfinite(tiny["delta"])
    overflow=measured([1e-300]*64+[1e300]*64)
    assert overflow["reason"]=="nonfinite_computed_statistic" and overflow["delta"] is None
    r1=measured([1.]*64+[2.]*64); r1.update(service="100",node="1000")
    r2=deepcopy(r1); r2.update(id="O"+"b"*12,entity="23456",service="200")
    r3=measured([1.]*128); r3.update(id="O"+"c"*12,entity="34567",service="300",node="1000")
    pool=exps.FrozenScopePoolV1(("100","200","300","1000","12345","23456","34567"),(),(),window,())
    hypotheses=exps.compile_scope(pool,[r1,r2,r3])
    hosts=[h for h in hypotheses if h["kind"]=="shared_host"]
    assert hosts and any(r3["id"] in h["soft_conflict"] for h in hosts)
    alone=exps.compile_scope(pool,[r1])
    assert all(not h["support"] for h in alone)
    opposite=deepcopy(r2); opposite["delta"]=-opposite["delta"]
    assert not any(h["support"] for h in exps.compile_scope(pool,[r1,opposite]))
    unknown_peer=deepcopy(r3); unknown_peer["status"]="unknown"
    uncertain=exps.compile_scope(pool,[r1,r2,unknown_peer])
    assert all(unknown_peer["id"] not in h["soft_conflict"] for h in uncertain)
    other=deepcopy(r2); other["unit"]="seconds"
    assert not any(h["kind"]=="shared_host" and h["support"] for h in exps.compile_scope(pool,[r1,other]))
    ambiguous=exps.FrozenScopePoolV1(pool.candidates,(),(("100","12345","owns"),("200","12345","owns")),window,())
    assert "12345" not in exps.memberships(ambiguous)[0]
    # Counter activity must survive the phase-boundary reset test, not merely
    # pass two independently increasing segments. No trace absence=>health.
    import pandas as pd
    counter=obs(semantic="http_requests_total"); counter["role"]="counter"
    activity_pool=exps.FrozenScopePoolV1(pool.candidates,(counter,),(),window,())
    frame=pd.DataFrame({counter["source_key"]:np.arange(128,dtype=float)})
    assert exps.activity_for(activity_pool,[obs()],frame,clock,c)["12345"]["status"]=="observed_active"
    frame[counter["source_key"]]=np.r_[np.arange(64,dtype=float),np.arange(64,dtype=float)]
    assert exps.activity_for(activity_pool,[obs()],frame,clock,c)["12345"]["status"]=="unknown"
    aggregate=obs(eid="100",semantic="GET"); aggregate['region']='R'
    aggregate['values']={'reference_interval_s':list(window[:2]),'current_interval_s':list(window[1:]),
                         'reference_observed_requests':50,'current_observed_requests':50}
    aggregate_pool=exps.FrozenScopePoolV1(pool.candidates,(aggregate,),(("100","12345","owns"),),window,())
    assert exps.activity_for(aggregate_pool,[obs()],frame,clock,c)["12345"]["status"]=="unknown"
    state=obs(); state["role"]="state"
    source_pool=exps.FrozenScopePoolV1(pool.candidates,(state,counter),(),window,((state["entity"],state["semantic"]),))
    assert exps.select_controls(source_pool,c)[0]==[]
    # Private perturbations never become an input to the public compiler.
    bundle={"parts":[{"type":"text","text":"Public facts only"}],"component_ledger":"unused",
            "evidence":{"schema":"CanvasEvidenceV1","cards":[{"id":"M1","kind":"metric",
                "title":"pod_cpu_usage","entity":"12345","unit":"source_unit",
                "data":{"bins":[0,1],"values":[1,2],"details":[]}}]}}
    payload,_=exps.visible_payload(pool,[deepcopy(r1),deepcopy(r2),deepcopy(r3)],c)
    original=exps.compile_texts(bundle,payload)
    changed=deepcopy(bundle); changed["private"]={"ground_truth":"LEAK_SENTINEL","fault_type":"LEAK_SENTINEL"}
    assert original==exps.compile_texts(changed,payload)
    assert "LEAK_SENTINEL" not in json.dumps(original)
    assert original["SCOPE_TEXT"]==original["SCOPE_MATRIX"]==original["SCOPE_TILES"]
    assert all('"soft_conflict"' not in p.get("text","") for p in original["SUPPORT_TEXT"])
    empty={"observations":[]}
    noops=exps.compile_texts(bundle,empty)
    assert all(noops[a]==noops[ARMS[0]] for a in ARMS)
    evidence,designs=exps.designs(payload,c)
    a,b=[compile_design(evidence,designs[arm]) for arm in ("SCOPE_MATRIX","SCOPE_TILES")]
    assert a["expected_bindings"]==b["expected_bindings"]
    assert a["rectangles"][0]["scope_layout"]==b["rectangles"][0]["scope_layout"]
    assert (a["width"],a["height"])==(b["width"],b["height"])
    malformed=deepcopy(evidence); malformed["cards"][0]["data"]["records"][0]["node"]="100"
    try:
        validate_evidence(malformed)
    except ValueError:
        pass
    else:
        raise AssertionError("Wrong node type accepted")
    # Small end-state files: timeout stays terminal, infrastructure requires
    # explicit diagnosis, missing marker stays pending, done is skipped.
    with tempfile.TemporaryDirectory(prefix="rq310-unit-") as name:
        root=Path(name)
        assert flag(root,"opaque",ARMS[0]) is None
        file=root/"flags"/(logical_key("opaque",ARMS[0])+".json")
        write_json(file,{"status":"fail","case":"opaque","arm":ARMS[0],"failure_class":"request_timeout"})
        assert flag(root,"opaque",ARMS[0])["status"]=="fail"
        write_json(file,{"status":"done","case":"opaque","arm":ARMS[0]})
        assert flag(root,"opaque",ARMS[0])["status"]=="done"
        write_json(file,{"status":"fail","case":"opaque","arm":ARMS[0],"failure_class":"infrastructure"})
        try:
            flag(root,"opaque",ARMS[0])
        except RuntimeError:
            pass
        else:
            raise AssertionError("Infrastructure failure silently retried")
    return {"native_cadence_and_missing_slots":True,"service_activity_not_spread_to_pods":True,
            "coverage_and_zero_scale":True,"positive_negative_and_transient":True,
            "qualified_stable_not_absence":True,"unit_and_mapping_ambiguity":True,
            "soft_conflict_vs_unknown":True,"geometry_and_field_twins":True,"durable_flags":True,
            "activity_phase_boundary_reset":True,"no_unsupported_single_anchor_vote":True,
            "private_perturbation_and_noop_twins":True}


def cpu(c,smoke=False):
    started=time.monotonic()
    checks=unit_tests(c)
    from RQs.RQ3_3.src.utils import OfflineTokens
    from renderer.gates import compare
    loaded,spec=runtime(c)
    tokens=OfflineTokens({"unified":{"vllm":str(loaded.source)},"models":[MODEL]})
    reg=register(c); root=path(c["preparation"])
    cases=[]; applicability={ds:{"cases":0,"qualified_conflict_cases":0,"stable_active_cases":0,
                                "unknown_activity_cases":0,"changed":0,"stable":0,"unknown":0,"no_op":0}
                            for ds in c["case_counts"]}
    counts=[]
    rows=reg["smoke" if smoke else "cases"]
    for row in rows:
        if time.monotonic()-started>c["cpu_seconds"]:
            raise TimeoutError("CPU qualification exceeded30 minutes")
        oid=row["opaque_incident_id"]
        public=read_json(root/"public"/(oid+".json")); marker=read_json(root/"flags"/(oid+".json"))
        exps.visible_audit(public)
        p=public["payload"]; a=applicability[row["dataset"]]
        a["cases"]+=1; a["no_op"]+=not bool(p["observations"])
        a["qualified_conflict_cases"]+=any(h["soft_conflict"] for h in p["hypotheses"])
        a["stable_active_cases"]+=any(r["status"]=="stable" for r in p["observations"])
        a["unknown_activity_cases"]+=any(r["activity"]["status"]=="unknown" for r in p["observations"])
        for r in p["observations"]: a[r["status"]]+=1
        if public["images"]:
            diff=compare(*[(root/public["images"][arm]["path"]).parent for arm in ("SCOPE_MATRIX","SCOPE_TILES")])
            assert all(diff[k] for k in ("same_projected_evidence","same_field_bindings","same_source_canvas","same_card_inventory"))
        counted={}; excluded={}
        for arm in ARMS:
            if arm in public["infeasible"]:
                continue
            png=(root/public["images"][arm]["path"]).read_bytes() if arm in public["images"] else None
            parts=exps.parts_for(public,arm,png)
            n=tokens.count(parts,public["system"],MODEL); counted[arm]=n; counts.append(n)
            if n+c["max_tokens"]>spec["max_model_len"]:
                excluded[arm]=f"intact registered input has{n} input tokens plus{c['max_tokens']} output; exceeds{spec['max_model_len']}"
        # Atomic small operational extension, not request mutation. Identical
        # no-op arms must share the same context exclusion.
        marker["context_excluded"]=excluded
        write_json(root/"flags"/(oid+".json"),marker)
        test_counts={kind:sum(h["kind"]==kind and (len(h["support"])>=2 or bool(h["soft_conflict"])) for h in p["hypotheses"])
                     for kind in ("local_instance","shared_service","shared_host")}
        for kind,n in test_counts.items():
            key=kind+"_testable_cases"; a[key]=a.get(key,0)+int(n>0)
        audit=read_json(root/"audit"/(oid+".json"))
        cases.append({"case":oid,"inputs":counted,"design_excluded":public["infeasible"],"context_excluded":excluded,
                      "qualified_tests":test_counts,"source_projection":audit["measurement"]})
    report={"status":"passed","source_contract":source_contract(),"checks":checks,"cases":len(cases),
            "scope":"smoke" if smoke else "full","case_ids":[r["opaque_incident_id"] for r in rows],
            "per_case":cases,"max_input_tokens":max(counts) if counts else None,"output_budget":c["max_tokens"],
            "applicability":applicability,"seconds":time.monotonic()-started,"gpu_calls":0,
            "eligibility_warning":"Review actual stable-active/conflict counts before authorizing formal inference. Low applicability is not remedied by deleting cases or lowering thresholds."}
    write_json(path(c["results"])/"qualification"/("cpu_smoke.json" if smoke else "cpu.json"),report)
    return {k:v for k,v in report.items() if k not in {"per_case","source_contract"}}
