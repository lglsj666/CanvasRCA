"""Synthetic contracts and bounded CPU-only checks of actual prepared inputs."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import tempfile
import time

from . import exps
from .utils import (ROOT, VERSION, MODEL, ARMS, path, register, runtime, read_json,
                    write_json, source_contract, logical_key, flag)


def unit_tests():
    metric = lambda cid, entity: {"id": cid, "kind": "metric", "title": "cpu_usage",
        "entity": entity, "unit": "percent", "data": {"bins": list(range(64)),
            "values": [float(i) for i in range(64)], "details": []}}
    graph = {"id": "G01", "kind": "graph", "title": "Membership", "entity": None, "unit": "",
             "data": {"nodes": [{"id": "100", "type": "service"}, {"id": "12345", "type": "pod"},
                                {"id": "23456", "type": "pod"}], "edges": [
                 {"id": "e1", "source": "100", "target": "12345", "kind": "owns"},
                 {"id": "e2", "source": "100", "target": "23456", "kind": "owns"}]}}
    # Mirror the supported graph contract from a real public bundle, without
    # opening labels. Synthetic tests are not a substitute for real-case smoke.
    evidence = {"schema": "CanvasEvidenceV1", "cards": [metric("M01", "12345"), metric("M02", "23456"), graph]}
    groups, _ = exps.comparison_candidates(evidence, {"verified": True})
    assert len(groups) == 1 and groups[0]["kind"] == "same_service_instances"
    assert exps.comparison_candidates(evidence, {"verified": True})[0] == groups
    _, designs = exps.designs({"evidence": evidence}, groups)
    assert designs["VIS_JOINT"]["viewport"] == designs["VIS_SEPARATE"]["viewport"]
    assert exps.comparison_candidates(evidence, {"verified": False})[0] == []
    missing = deepcopy(evidence)
    missing["cards"][0]["data"]["values"][4] = None
    selected, layouts = exps.designs({"evidence": missing}, groups)
    assert selected["cards"][0]["data"]["values"][4] is None
    for layout in layouts.values():
        assert next(n for n in layout["tree"]["children"] if n.get("card") == "M01")["component"] == "metric.time_bars"
    with tempfile.TemporaryDirectory(prefix="rq39-flags-") as folder:
        root = Path(folder)
        assert flag(root, "INC-TEST", ARMS[0]) is None
        p = root / "flags" / (logical_key("INC-TEST", ARMS[0]) + ".json")
        write_json(p, {"status": "fail", "case": "INC-TEST", "arm": ARMS[0], "failure_class": "request_timeout"})
        assert flag(root, "INC-TEST", ARMS[0])["status"] == "fail"
        write_json(p, {"status": "done", "case": "INC-TEST", "arm": ARMS[0]})
        assert flag(root, "INC-TEST", ARMS[0])["status"] == "done"
    return {"deterministic_public_groups": True, "same_size_layouts": True,
            "missing_not_zero": True, "unverified_clock_not_paired": True,
            "done_and_timeout_flags": True}


def cpu(c):
    start = time.monotonic()
    checks = unit_tests()
    from renderer.gates import compare
    from RQs.RQ3_3.src.utils import OfflineTokens
    loaded, spec = runtime(c)
    tokenizer = OfflineTokens({"unified": {"vllm": str(loaded.source)}, "models": [MODEL]})
    rows = register(c)["cases"]
    root = path(c["preparation"])
    counts, details = [], []
    for row in rows:
        if time.monotonic()-start > 1800:
            raise TimeoutError("CPU qualification exceeded its 30-minute budget")
        oid = row["opaque_incident_id"]
        prepared = read_json(root / "public" / (oid + ".json"))
        flat = [p["text"] for p in prepared["texts"]["TEXT_FLAT"]]
        joint = [p["text"] for p in prepared["texts"]["TEXT_JOINT"]]
        assert Counter("\n".join(flat).splitlines()) == Counter("\n".join(joint).splitlines())
        if prepared["groups"]:
            a, b = [root / prepared["images"][arm]["path"] for arm in ("VIS_SEPARATE", "VIS_JOINT")]
            diff = compare(a.parent, b.parent)
            assert all(diff[k] for k in ("same_projected_evidence", "same_card_inventory", "same_field_bindings", "same_source_canvas"))
            assert not diff["changed_component"] and diff["changed_geometry"] and not diff["same_pixels"]
        for arm in ARMS:
            png = (root / prepared["images"][arm]["path"]).read_bytes() if arm in prepared["images"] else None
            parts = exps.parts_for(prepared, arm, png)
            n = tokenizer.count(parts, prepared["system"], MODEL)
            counts.append(n)
            if n+c["max_tokens"] > spec["max_model_len"]:
                raise ValueError(f"CPU context overflow: {oid} {arm} {n}")
        details.append({"case": oid, "input_tokens": dict(zip(ARMS, counts[-4:]))})
    result = {"status": "passed", "source_contract": source_contract(), "checks": checks,
              "cases": len(rows), "requests_tokenized": len(counts), "max_input_tokens": max(counts),
              "output_budget": c["max_tokens"], "context": spec["max_model_len"],
              "seconds": time.monotonic()-start, "per_case": details, "gpu_calls": 0}
    write_json(path(c["results"]) / "qualification/cpu.json", result)
    return {k: v for k, v in result.items() if k not in {"source_contract", "per_case"}}
