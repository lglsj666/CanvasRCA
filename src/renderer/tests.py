"""Bounded CPU/browser regression. Browser tests opt in via RENDER_BROWSER_TESTS=1."""
import copy
import os
from pathlib import Path

import pytest

from .utils import compile_design, validate_evidence, write, read
from .exps import preset


def sample():
    return {"schema":"CanvasEvidenceV1", "cards":[
        {"id":"M1","kind":"metric","entity":"123","title":"CPU usage","unit":"%",
         "data":{"bins":[0,1,2,3,4],"values":[0,None,-5,None,12],"details":[{"name":"Reference mean","value":"0"}]}},
        {"id":"R1","kind":"trace","entity":"12345","title":"POST /checkout","unit":"ms",
         "data":{"before":0,"after":180,"details":[{"name":"Requests","value":"150"}]}},
        {"id":"L1","kind":"log","entity":"12345","title":"Template LT1","unit":"events",
         "data":{"bins":[0,3],"counts":[0,4],"template":"operation <value> & retry","details":[]}},
        {"id":"G1","kind":"graph","entity":None,"title":"System relationships","unit":"",
         "data":{"nodes":[{"id":"123","type":"service"},{"id":"456","type":"service"},
                          {"id":"1234","type":"node"},{"id":"12345","type":"pod"}],
                 "edges":[{"id":"e0","source":"123","target":"456","kind":"calls"},
                          {"id":"e1","source":"456","target":"123","kind":"calls"},
                          {"id":"e2","source":"12345","target":"12345","kind":"calls"}]}}]}


def panels(tree):
    if tree["type"]=="panel":
        return [tree]
    return [p for c in tree["children"] for p in panels(c)]


def test_deterministic_geometry_and_inventory():
    e=sample()
    for name in ("operations","relations_first","matrix"):
        d=preset(e,name)
        a=compile_design(e,d)
        assert a==compile_design(copy.deepcopy(e),copy.deepcopy(d))
        assert len(a["rectangles"])==4
        assert set(r["card"] for r in a["rectangles"])=={c["id"] for c in e["cards"]}


def test_unsupported_or_dropped_cards_rejected():
    e=sample();d=preset(e)
    panels(d["tree"])[0]["component"]="invisible"
    with pytest.raises(ValueError):compile_design(e,d)
    d=preset(e);d["tree"]["children"].pop()
    d["tree"]["weights"].pop()
    with pytest.raises(ValueError):compile_design(e,d)


@pytest.mark.parametrize("key,value",[("ground_truth","123"),("dataset","aegislab"),("private",{})])
def test_private_extra_fields_rejected(key,value):
    e=sample();e[key]=value
    with pytest.raises(ValueError):validate_evidence(e)


def test_malicious_text_not_html_and_metadata_rejected():
    e=sample();e["cards"][2]["data"]["template"]="<script>alert(1)</script>"
    validate_evidence(e)  # React will escape text; not innerHTML.
    e["cards"][0]["title"]="/home/person/private_case"
    with pytest.raises(ValueError):validate_evidence(e)


@pytest.mark.parametrize("values",[[None]*5,[0]*5,[1e12]*5,[1e-12,-1e-12,0,None,1]])
def test_extreme_and_constant_values(values):
    e=sample();e["cards"][0]["data"]["values"]=values
    compile_design(e,preset(e))


def test_no_nan_no_fake_zero():
    e=sample();e["cards"][0]["data"]["values"][0]=float('nan')
    with pytest.raises(ValueError):validate_evidence(e)
    e=sample();assert e["cards"][0]["data"]["values"][1] is None


def test_graph_isolates_are_only_hidden_after_full_relations():
    from .operations import apply_operations
    e=sample();original=copy.deepcopy(e);d=preset(e)
    a=compile_design(e,d)
    assert a["hidden_graph_isolates"]=={"G1":["1234"]}
    assert "G1.node.1234" not in a["expected_bindings"]
    assert "M1.sample.0" in a["expected_bindings"]
    changed,_=apply_operations(e,d,[{"op":"graph_visibility","args":{"show_isolates":True}}])
    assert "G1.node.1234" in compile_design(e,changed)["expected_bindings"]
    assert e==original


def test_complete_topology_not_selected_traces_or_candidate_only():
    from .topology import cards_from_topology
    graph={"nodes":[{"id":n} for n in ("a","b","mysql","isolate","host","pod")],
           "edges":[{"source":"a","target":"b"},{"source":"b","target":"mysql"},
                    {"source":"host","target":"pod"}]}
    mapping=dict(zip(("a","b","mysql","isolate","host","pod"),("111","222","333","444","1234","12345")))
    cards,audit=cards_from_topology(graph,{"node_pod_map":{"host":["pod"]}},mapping,
                                  {("mysql","a"),("a","endpoint:remote-db:5432")},
                                  {"endpoint:remote-db:5432":"database"})
    e={"schema":"CanvasEvidenceV1","cards":cards};validate_evidence(e)
    assert len(cards[0]["data"]["edges"])==4
    assert len(cards[1]["data"]["edges"])==1
    assert audit["graph_edges_classified_as_deployment"]==1
    assert any(n.get("role")=="database" and n["type"]=="external" for n in cards[0]["data"]["nodes"])
    assert any(n.get("role")=="database" and n["id"]=="333" for n in cards[0]["data"]["nodes"])
    assert mapping["isolate"]=="444" and len(mapping)==6
    scene=compile_design(e,preset(e))
    assert "G01.node.444" not in scene["expected_bindings"]
    assert "G01.node.333" in scene["expected_bindings"]


def test_trace_join_is_trace_scoped_and_retains_normal_rows():
    from .topology import trace_relations
    rows=[dict(trace_id="t1",span_id="1",parent_span_id="0",service_name="a"),
          dict(trace_id="t2",span_id="1",parent_span_id="0",service_name="x"),
          dict(trace_id="t1",span_id="2",parent_span_id="1",service_name="b"),
          dict(trace_id="t2",span_id="2",parent_span_id="1",service_name="y"),
          dict(trace_id="t3",span_id="2",parent_span_id="1",service_name="z"),
          dict(trace_id="t4",span_id="1",parent_span_id="0",service_name="c"),
          dict(trace_id="t4",span_id="1",parent_span_id="0",service_name="d"),
          dict(trace_id="t4",span_id="2",parent_span_id="1",service_name="e")]
    edges,_,audit=trace_relations(lambda:iter(rows))
    assert edges=={("a","b"),("x","y")}
    assert audit["source_rows"]==len(rows)
    assert audit["unresolved_parent_rows"]==1 and audit["ambiguous_parent_rows"]==1
    for r in rows:r.update(anomaly_score=0,ground_truth="unused")
    assert trace_relations(lambda:iter(rows))[0]==edges


def test_service_instances_use_public_resources_not_names_or_calls():
    from .topology import service_pod_relations, cards_from_topology
    mapping={"svc":"111","svc-hash-0":"12345","svc-hash-1":"12346","host":"1234"}
    rows=[{"service_name":"svc","attr.k8s.pod.name":"svc-hash-0","attr.k8s.namespace.name":"ns"}]*3
    rows += [{"service_name":"svc-hash-1"}, {"service_name":"unknown","attr.k8s.pod.name":"svc-hash-1"}]
    pairs,audit=service_pod_relations(lambda:iter(rows),mapping)
    assert pairs=={("svc","svc-hash-0")} and audit["witness_rows"][0]["rows"]==3
    assert audit["unbound_or_wrong_type_rows"]==1
    for r in rows:r.update(ground_truth="unused",anomal=1)
    assert service_pod_relations(lambda:iter(rows),mapping)[0]==pairs
    graph={"nodes":[{"id":n} for n in mapping],"edges":[]}
    cards,_=cards_from_topology(graph,{"node_pod_map":{"host":["svc-hash-0"]}},mapping,service_pairs=pairs)
    validate_evidence({"schema":"CanvasEvidenceV1","cards":cards})
    assert not cards[0]["data"]["edges"]
    assert cards[1]["data"]["edges"][0]["kind"]=="hosts"
    assert cards[2]["data"]["edges"]==[{"id":"e0","source":"111","target":"12345","kind":"has_instance"}]
    # Explicit metadata can add a correspondence; names alone did not.
    cards,_=cards_from_topology(graph,{"service_pod_map":{"svc":["svc-hash-1"]}},mapping,service_pairs=pairs)
    assert len(cards[2]["data"]["edges"])==2
    rows.append({"service_name":"svc","attr.k8s.pod.name":"svc-hash-0","attr.k8s.namespace.name":"another"})
    assert not service_pod_relations(lambda:iter(rows),mapping)[0]


def membership_sample():
    nodes=[{"id":"111","type":"service"},{"id":"222","type":"service"},
           {"id":"1234","type":"node"},{"id":"9999","type":"node"}]
    nodes += [{"id":str(12000+i),"type":"pod"} for i in range(17)]
    nodes[-1]["role"]="database"
    edges=[{"id":f"e{i}","source":"1234","target":str(12000+i),"kind":"hosts"} for i in range(17)]
    edges += [{"id":f"e{17+i}","source":service,"target":str(12000+i%3),"kind":kind}
              for i,(service,kind) in enumerate([("111","has_instance"),("222","has_instance"),("111","owns")])]
    return {"schema":"CanvasEvidenceV1","cards":[{"id":"G1","kind":"graph","entity":None,
        "title":"Deployment memberships","unit":"","data":{"nodes":nodes,"edges":edges}}]}


def test_membership_layout_capacity_and_semantics():
    from .utils import deployment_layout
    from .operations import apply_operations
    e=membership_sample();original=copy.deepcopy(e);d=preset(e)
    assert panels(d["tree"])[0]["component"]=="graph.deployment_groups"
    scene=compile_design(e,d)
    assert sum(len(g["edges"]) for g in scene["rectangles"][0]["deployment_layout"]["groups"])==20
    changed,_=apply_operations(e,d,[{"op":"component","args":{"card":"G1","component":"graph.node_link"}}])
    assert compile_design(e,changed)["expected_bindings"]==scene["expected_bindings"]
    assert e==original
    with pytest.raises(ValueError,match="too narrow"):deployment_layout(e["cards"][0],240,28)
    e["cards"][0]["data"]["edges"][0]["kind"]="calls"
    with pytest.raises(ValueError,match="never calls"):compile_design(e,d)
    e=membership_sample()
    e["cards"][0]["data"]["edges"]=[dict(edge,id=f"e{i}") for i,edge in enumerate(e["cards"][0]["data"]["edges"]*50)]
    with pytest.raises(ValueError,match="capacity"):compile_design(e,d)


@pytest.mark.skipif(os.environ.get("RENDER_BROWSER_TESTS")!="1",reason="Explicit browser regression only")
@pytest.mark.parametrize("font",[16,28])
def test_browser_memberships_wrap_preserve_all_edges_and_references(tmp_path,font):
    from .main import render
    from .utils import deployment_layout
    e=membership_sample();d=preset(e);d["font_size"]=font;d["graph"]["show_isolates"]=True
    d["viewport"]["height"]=max(600,114+deployment_layout(e["cards"][0],1744,font,True)["min_height"])
    ep,dp=tmp_path/"e.json",tmp_path/"d.json";write(ep,e);write(dp,d)
    a=render(ep,dp,tmp_path/"groups");b=render(ep,dp,tmp_path/"repeat")
    assert a["png_sha256"]==b["png_sha256"] and a["status"]=="passed"
    assert len(a["audit"]["memberships"])==20
    assert len(a["audit"]["references"])==4  # 3 reused pods + 1 repeated service.
    assert "G1.node.9999" in a["expected_bindings"]
    assert 'database' in (tmp_path/"groups/dashboard.html").read_text()
    if font==16:
        # New instance relation must also remain visible in every old encoding.
        for component in ("graph.node_link","graph.matrix","graph.edge_pairs"):
            other=copy.deepcopy(d);panels(other["tree"])[0]["component"]=component
            other["viewport"]["height"]=1800;write(dp,other)
            report=render(ep,dp,tmp_path/component.split('.')[1])
            assert report["expected_bindings"]==a["expected_bindings"] and report["status"]=="passed"


def test_empty_membership_component():
    e=membership_sample();e["cards"][0]["data"]["edges"]=[]
    d=preset(e);panels(d["tree"])[0]["component"]="graph.deployment_groups"
    assert not compile_design(e,d)["rectangles"][0]["deployment_layout"]["groups"]


def test_client_database_needs_endpoint_not_sql_operation():
    from .topology import trace_relations
    rows=[{"trace_id":"1","span_id":"1","service_name":"a","parent_span_id":"0",
           "span_kind":"CLIENT","db.system":"postgresql","server.address":"db.internal","server.port":"5432"},
          {"trace_id":"1","span_id":"2","service_name":"a","parent_span_id":"1",
           "span_kind":"CLIENT","db.system":"mysql","operation_name":"SELECT secret"}]
    edges,roles,_=trace_relations(lambda:iter(rows))
    assert edges=={("a","endpoint:db.internal:5432")}
    assert roles=={"endpoint:db.internal:5432":"database"}


def test_onsets_are_relative_and_do_not_invent_duration():
    from .topology import onset_card
    p={"facts":[{"field":"propagation_service","payload":{"service":"123",
        "onset_rel_min_display":"+2.5m","severity_z_display":"4.2","evidence_source_display":"M"}},
        {"field":"propagation_service","payload":{"service":"456","onset_rel_min_display":"—"}}]}
    card=onset_card(p)
    assert card["data"]["events"]==[{"entity":"123","minute":2.5,"severity":"4.2","source":"M"}]
    validate_evidence({"schema":"CanvasEvidenceV1","cards":[card]})


@pytest.mark.skipif(os.environ.get("RENDER_BROWSER_TESTS")!="1",reason="Explicit browser regression only")
def test_browser_complete_graph_and_onset_component(tmp_path):
    from .main import render
    from .topology import onset_card
    e=sample();e["cards"]=e["cards"][-1:]
    # Large graph beyond the previous two-ring design, including a DB node.
    graph=e["cards"][0]["data"]
    graph["nodes"]=[{"id":str(100+i),"type":"service"} for i in range(64)]
    graph["nodes"][-1]["role"]="database"
    graph["edges"]=[{"id":f"e{i}","source":str(100+i),"target":str(100+(i+1)%64),"kind":"calls"} for i in range(64)]
    p={"facts":[{"field":"propagation_service","payload":{"service":"100",
        "onset_rel_min_display":"+1.0m","severity_z_display":"999","evidence_source_display":"M"}}]}
    e["cards"].append(onset_card(p))
    ep,dp=tmp_path/"e.json",tmp_path/"d.json"
    write(ep,e);write(dp,preset(e));report=render(ep,dp,tmp_path/"network")
    assert report["status"]=="passed"
    assert 'database' in (tmp_path/"network/dashboard.html").read_text()
    write(dp,preset(e,"matrix"));assert render(ep,dp,tmp_path/"matrix")["status"]=="passed"


def test_ownership_not_system_edge():
    e=sample();d=preset(e)
    d["bindings"]=[{"card":"M1","graph":"G1","entity":"123"}]
    compile_design(e,d)
    assert len(e["cards"][-1]["data"]["edges"])==3
    d["bindings"][0]["entity"]="456"
    with pytest.raises(ValueError):compile_design(e,d)


def test_operations_isolation_and_index_stability():
    from .operations import apply_operations
    e=sample();d=preset(e);initial=copy.deepcopy(e)
    changed,audit=apply_operations(e,d,[{"op":"resolution","args":{"scale":1.5}},
                                      {"op":"component","args":{"card":"M1","component":"metric.heatmap"}}])
    assert e==initial and d["scale"]==1
    assert audit[0]["changed_rectangles"]=={}
    assert audit[1]["changed_rectangles"]=={"M1":["component"]}
    first=compile_design(e,d)["rectangles"]
    second=compile_design(e,preset(e,"relations_first"))["rectangles"]
    assert {x["card"]:x["index"] for x in first}=={x["card"]:x["index"] for x in second}
    order=[c["id"] for c in reversed(d["tree"]["children"])]
    reordered,_=apply_operations(e,d,[{"op":"reorder","args":{"container":"dashboard","order":order}}])
    assert [c["id"] for c in reordered["tree"]["children"]]==order
    assert d["tree"]["weights"]==reordered["tree"]["weights"]
    with pytest.raises(ValueError):apply_operations(e,d,[{"op":"delete_evidence","args":{}}])


def test_component_and_operation_catalogs_are_connected():
    from .utils import RENDERER
    from .operations import REGISTRY
    catalog=read(RENDERER/"configs/components.json")["components"]
    registry=(RENDERER/"web/components/index.ts").read_text()
    assert len({c["index"] for c in catalog})==len(catalog)
    for c in catalog:
        assert (RENDERER/"web/components"/c["file"]).exists()
        assert "'"+c["id"]+"'" in registry
    assert {o["id"] for o in read(RENDERER/"configs/operations.json")["operations"]}==set(REGISTRY)


def test_pair_component_switch_preserves_facts_and_checks_capacity():
    from .operations import apply_operations
    from .utils import pair_layout
    e=sample();original=copy.deepcopy(e);d=preset(e)
    changed,audit=apply_operations(e,d,[{"op":"component","args":{"card":"G1","component":"graph.edge_pairs"}}])
    before,after=compile_design(e,d),compile_design(e,changed)
    assert before["expected_bindings"]==after["expected_bindings"]
    assert e==original
    assert audit[0]["changed_rectangles"]["G1"]==["component","pair_layout"]
    back,_=apply_operations(e,changed,[{"op":"component","args":{"card":"G1","component":"graph.node_link"}}])
    assert compile_design(e,back)==before
    with pytest.raises(ValueError,match="too narrow"):
        pair_layout(e["cards"][-1],240,28)
    dense=sample();g=dense["cards"][-1]
    g["data"]["edges"]=[{"id":f"e{i}","source":"123","target":"456","kind":"calls"} for i in range(100)]
    with pytest.raises(ValueError,match="capacity"):
        compile_design(dense,changed)
    assert compile_design(dense,preset(dense,"pairs"))["evidence_hash"]


@pytest.mark.skipif(os.environ.get("RENDER_BROWSER_TESTS")!="1",reason="Explicit browser regression only")
@pytest.mark.parametrize("font,isolates",[(16,False),(28,True)])
def test_browser_edge_pairs_keep_cycle_self_loop_types_and_repetitions(tmp_path,font,isolates):
    from .main import render
    from .gates import compare
    from .operations import apply_operations
    e=sample();e["cards"]=e["cards"][-1:];g=e["cards"][0]["data"]
    g["nodes"].append({"id":"789","type":"service","role":"database"})
    g["edges"].extend([
        {"id":"e3","source":"456","target":"789","kind":"calls"},
        {"id":"e4","source":"789","target":"123","kind":"calls"},
        {"id":"e5","source":"123","target":"456","kind":"owns"},
        {"id":"e6","source":"1234","target":"12345","kind":"hosts"},
        {"id":"e7","source":"123","target":"456","kind":"request_parent"}])
    g["nodes"].append({"id":"999","type":"service"})
    dp,ep=tmp_path/"design.json",tmp_path/"evidence.json"
    d=preset(e);d["font_size"]=font;d["graph"]["show_isolates"]=isolates
    write(dp,d);write(ep,e);render(ep,dp,tmp_path/"network")
    changed,_=apply_operations(e,d,[{"op":"component","args":{"card":"G1","component":"graph.edge_pairs"}}])
    write(dp,changed);a=render(ep,dp,tmp_path/"pairs");b=render(ep,dp,tmp_path/"repeat")
    assert a["png_sha256"]==b["png_sha256"]
    comparison=compare(tmp_path/"network",tmp_path/"pairs")
    assert comparison["same_projected_evidence"] and comparison["same_field_bindings"]
    assert comparison["changed_geometry"]==[] and comparison["changed_component"]==["G1"]
    assert len(a["audit"]["pairs"])==len(g["edges"])
    assert {(p["source"],p["target"],p["kind"]) for p in a["audit"]["pairs"]}=={
        (edge["source"],edge["target"],edge["kind"]) for edge in g["edges"]}
    assert len(a["audit"]["references"])==2*len(g["edges"])-5
    assert ("G1.node.999" in a["expected_bindings"])==isolates
    assert 'database' in (tmp_path/"pairs/dashboard.html").read_text()


@pytest.mark.skipif(os.environ.get("RENDER_BROWSER_TESTS")!="1",reason="Explicit browser regression only")
def test_browser_encodings_determinism_and_failure(tmp_path):
    from .main import render
    from .gates import compare
    e=sample(); ep=tmp_path/"evidence.json"; dp=tmp_path/"design.json"
    write(ep,e);d=preset(e);write(dp,d)
    a=render(ep,dp,tmp_path/"a");b=render(ep,dp,tmp_path/"b")
    assert a["png_sha256"]==b["png_sha256"]
    assert compare(tmp_path/"a",tmp_path/"b")["same_pixels"]
    assert '&lt;value&gt;' in (tmp_path/"a/dashboard.html").read_text()
    for name,encodings in [("matrix",{}),("bars",{"M1":"metric.time_bars","R1":"trace.table","L1":"log.table"})]:
        changed=preset(e,"matrix" if name=="matrix" else "operations")
        for p in panels(changed["tree"]):p["component"]=encodings.get(p["card"],p["component"])
        write(dp,changed);report=render(ep,dp,tmp_path/name)
        assert report["status"]=="passed"
        assert compare(tmp_path/"a",tmp_path/name)["same_projected_evidence"]
    # A single internal encoding change does not reflow other panels.
    d=preset(e);panels(d["tree"])[0]["component"]="metric.time_bars";write(dp,d)
    render(ep,dp,tmp_path/"one_change")
    contrast=compare(tmp_path/"a",tmp_path/"one_change")
    assert contrast["changed_geometry"]==[] and contrast["changed_component"]==["M1"]
    # Actual ownership layer, with adjacent panel and graph. Instance IDs remain
    # evidence identities; catalog IDs and displayed indices are separate.
    linked=copy.deepcopy(e)
    linked["cards"]=[c for c in linked["cards"] if c["id"] in {"M1","G1"}]
    linked_design=preset(linked)
    linked_design["viewport"]={"width":1800,"height":900}
    linked_design["tree"]={"id":"dashboard","type":"row","weights":[1,2],"children":[
        {"id":"left","type":"panel","card":"M1","component":"metric.line"},
        {"id":"right","type":"panel","card":"G1","component":"graph.node_link"}]}
    linked_design["bindings"]=[{"card":"M1","graph":"G1","entity":"123"}]
    write(ep,linked);write(dp,linked_design)
    linked_report=render(ep,dp,tmp_path/"linked")
    assert len(linked_report["overlay"])==1 and linked_report["status"]=="passed"
    # Global operations are exercised in the browser as well as structurally.
    from .operations import apply_operations
    global_design,_=apply_operations(e,preset(e),[
        {"op":"appearance","args":{"theme":"light","font_size":16}},
        {"op":"spacing","args":{"gap":22,"padding":30}},
        {"op":"resolution","args":{"scale":1.25}},
        {"op":"indexing","args":{"visible":False,"start":20}}])
    write(ep,e);write(dp,global_design)
    global_report=render(ep,dp,tmp_path/"global_ops")
    assert global_report["source_png"]["width"]==2250
    # A real overflow must fail, not silently clip or shrink the font.
    write(dp,preset(e))
    e["cards"][0]["title"]="Very long diagnostic field "*100;write(ep,e)
    with pytest.raises(Exception):render(ep,dp,tmp_path/"overflow")
    assert read(tmp_path/"overflow/manifest.json")["status"]=="failed"
    assert any('overflow' in i for i in read(tmp_path/"overflow/manifest.json")["audit"]["issues"])


@pytest.mark.skipif(os.environ.get("RENDER_BROWSER_TESTS")!="1",reason="Explicit browser regression only")
@pytest.mark.parametrize("values",[[None]*5,[0]*5,[1e12]*5,[1e-12,-1e-12,0,None,1]])
def test_browser_numeric_edge_cases(tmp_path,values):
    from .main import render
    e=sample();e["cards"]=e["cards"][:1];e["cards"][0]["data"]["values"]=values
    ep=tmp_path/"e.json";dp=tmp_path/"d.json"
    write(ep,e);write(dp,preset(e))
    assert render(ep,dp,tmp_path/"render")["status"]=="passed"
