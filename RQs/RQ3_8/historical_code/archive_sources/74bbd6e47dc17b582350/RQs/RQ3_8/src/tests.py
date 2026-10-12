"""CPU regressions; no model calls, no raw-data preprocessing."""
from copy import deepcopy
import json
import os
from pathlib import Path

import pytest

from renderer.tests import sample
from renderer.exps import preset
from renderer.utils import compile_design
from . import exps
from .utils import ARMS, ROOT, config, make_profile, logical_key, read_flag, write_json


@pytest.mark.skipif(not os.environ.get("SLURM_JOB_ID"), reason="Nibi allocation environment only")
def test_nibi_cuda_toolkit_and_persistent_compiler_cache():
    import shutil
    import subprocess
    import torch
    nvcc = shutil.which("nvcc")
    assert nvcc and (Path(os.environ["CUDA_HOME"])/"include").is_dir()
    assert "release 12.9" in subprocess.check_output([nvcc,"--version"],text=True)
    assert torch.version.cuda == "12.9"
    assert os.environ["TRITON_CACHE_DIR"].endswith("/rq38-h100-cu129")
    assert os.environ["VLLM_CACHE_ROOT"].endswith("/rq38-h100-cu129")
    assert os.environ["MAX_JOBS"] == "8"
    assert os.environ["CANVASRCA_VLLM_CONFIG"].endswith("/runtime/inference.triton_v2.yaml")
    assert not torch.cuda.is_initialized()


def test_all_six_visual_conditions_freeze_geometry_and_facts():
    evidence = sample()
    original = deepcopy(evidence)
    full = compile_design(evidence, preset(evidence, "relations_first"))
    for arm in exps.GRAPHICAL:
        selected, design = exps.fixed_slot_design(evidence, arm)
        actual = compile_design(selected, design)
        kept = {c["id"] for c in selected["cards"]}
        assert actual["rectangles"] == [r for r in full["rectangles"] if r["card"] in kept]
        assert actual["width"] == full["width"] and actual["height"] == full["height"]
        assert design["bindings"] == [] and not design["graph"]["show_isolates"]
    assert evidence == original


@pytest.mark.parametrize("value", [list(range(64)), [1.25]*32+[None]*32,
    [0,-0.0,1e-20,1e20,None,-5], [{"entity":"123","value":i} for i in range(20)],
    {"data":{"values":[4,None,4,None]*16}}, sample()["cards"]])
def test_compact_ledger_is_reversible(value):
    packed = exps.compact_records(value)
    assert exps.expand_records(packed) == value


def test_ledger_repair_preserves_parent_text_and_image():
    parent = {"system":"RCA", "parts":[{"type":"text","text":"Exact original facts"},
        {"type":"text","text":"Question"}],"metrics":[],"candidates":["123"],
        "selected_relations":[],"full_relations":[]}
    bundle = exps.public_bundle(parent, sample())
    bundle["parts"][-2]["text"] = bundle["component_ledger"] = "old verbose ledger"
    png = b"\x89PNG\r\n\x1a\nfixture"
    for arm in ARMS:
        parts = exps.model_parts(bundle, arm, png if arm in exps.GRAPHICAL else None)
        assert [p["text"] for p in parts if p.get("text") in {"Exact original facts","Question"}] == ["Exact original facts","Question"]
        assert all(p.get("text") != "old verbose ledger" for p in parts)
        if arm in exps.GRAPHICAL:
            assert parts[0]["png"] == png


def test_ledger_drops_only_unprinted_edge_bookkeeping():
    evidence = sample()
    ledger = exps.matched_ledger(evidence)
    decoded = exps.expand_records(json.loads(ledger.split("\n", 1)[1]))
    for original, displayed in zip(evidence["cards"], decoded, strict=True):
        if original["kind"] != "graph":
            assert original == displayed
        else:
            assert displayed["data"]["edges"] == [
                {k:v for k,v in edge.items() if k != "id"} for edge in original["data"]["edges"]]


def test_json_whitespace_preserves_numbers_strings_and_prose():
    text = 'Task stays unchanged.\nmetric_series: {"name": "a b", "v": [1.00, 1e-8, -0.0, null]}\n'
    assert exps.compact_json_whitespace(text) == 'Task stays unchanged.\nmetric_series: {"name":"a b","v":[1.00,1e-8,-0.0,null]}\n'
    assert exps.compact_json_whitespace('ordinary { not json\n') == 'ordinary { not json\n'
    escaped = 'json: {"quoted": "a \\\"b\\\" c", "path": "a\\\\b"}\n'
    assert json.loads(exps.compact_json_whitespace(escaped)[6:]) == json.loads(escaped[6:])
    axis = "Metric evidence; field=metric_series_64; bins=["+",".join(map(str,range(64)))+"]; unit=x"
    assert exps.compact_json_whitespace(axis) == "Metric evidence; field=metric_series_64; bins=0..63 (inclusive); unit=x"


@pytest.mark.parametrize("message,retries", [("Unable to capture screenshot",2),("leaking content",1)])
def test_browser_retry_is_bounded_and_not_a_validation_bypass(tmp_path, monkeypatch, message, retries):
    import subprocess
    import renderer.main as renderer
    from .main import render_capture
    calls = []
    def render(*args):
        calls.append(args)
        output = args[-1]
        output.mkdir()
        (output/"browser.log").write_text(message)
        raise subprocess.CalledProcessError(1, ["browser"])
    monkeypatch.setattr(renderer,"render",render)
    with pytest.raises(subprocess.CalledProcessError):
        render_capture(tmp_path/"e.json",tmp_path/"d.json",tmp_path/"render")
    assert len(calls) == retries
    assert len(list(tmp_path.glob("render.capture_failed.*"))) == retries-1


def test_a_spacer_cannot_silently_hide_selected_evidence():
    evidence = sample()
    design = preset(evidence)
    design["tree"]["children"][0] = {"id": "empty", "type": "spacer"}
    with pytest.raises(ValueError, match="every selected card"):
        compile_design(evidence, design)


def test_no_new_graph_isolates_or_links():
    evidence = sample()
    graph = next(c for c in evidence["cards"] if c["kind"] == "graph")
    for arm in exps.GRAPHICAL:
        selected, design = exps.fixed_slot_design(evidence, arm)
        assert next(c for c in selected["cards"] if c["kind"] == "graph") == graph
        assert design["bindings"] == []


def test_text_backbone_shared_and_no_private_fields():
    parent = {"system": "RCA", "parts": [{"type":"text", "text":"Evidence"}, {"type":"text", "text":"Question"}],
              "metrics": [], "candidates": ["123"], "selected_relations": [], "full_relations": []}
    bundle = exps.public_bundle(parent, sample())
    original = deepcopy(bundle)
    for arm in ARMS:
        png = b"\x89PNG\r\n\x1a\nsynthetic" if arm in exps.GRAPHICAL else None
        parts = exps.model_parts(bundle, arm, png)
        texts = [p["text"] for p in parts if p["type"] == "text"]
        assert texts[-1] == "Question"
        assert all(p["text"] in texts for p in bundle["parts"])
        assert sum(p["type"] == "image" for p in parts) == (arm in exps.GRAPHICAL)
    assert original == bundle
    parent["ground_truth"] = "123"
    with pytest.raises(ValueError):
        exps.public_bundle(parent, sample())


def test_nullable_onset_is_not_a_fake_event():
    from renderer.topology import onset_card
    packet = {"facts": [{"field":"propagation_service", "payload":{"onset_rel_min_display":None}}]}
    assert onset_card(packet)["data"]["events"] == []


def test_null_log_r_preserves_template_without_inventing_rate(monkeypatch):
    from types import SimpleNamespace
    from renderer.exps import export_public_case
    import renderer.topology as topology
    monkeypatch.setattr(topology, "development_topology", lambda *a: ([], {"source_directory":"public-only"}))
    payload = {"level":"error","numeric_preview":{},"log_r":None,"template_id":"LT01",
               "entity_id":"123","relative_bin":2,"count":4,"template":"request failed"}
    packet = {"packet_hash":"x","facts":[{"payload":payload,"field":"denum_log_template","region":"L","fact_id":"F1"}]}
    context = {"prepared":SimpleNamespace(private={},public={"packet":packet})}
    evidence, _ = export_public_case({"opaque_incident_id":"INC-X","dataset":"aegislab"},context,"public")
    assert evidence["cards"][0]["data"]["counts"] == [4]
    assert evidence["cards"][0]["data"]["details"] == [{"name":"Level","value":"error"}]


def test_dense_gemma_identity_and_only_qwen_backend_changes(tmp_path):
    from unified_scripts.vllm_inference import VLLMInferenceConfig
    target = tmp_path/"profile.yaml"
    # Passing the canonical default honors the deployment environment override;
    # use a distinct copy to really compare against the unadapted base recipe.
    original = (ROOT/"configs/vllm_inference.yaml").read_bytes()
    baseline_path = tmp_path/"base.yaml"
    baseline_path.write_bytes(original)
    baseline = VLLMInferenceConfig.load(baseline_path)
    make_profile(config(), target)
    deployed = VLLMInferenceConfig.load(target)
    expected = {**baseline.model("qwen3.8-27b"), "gdn_prefill_backend": "triton"}
    assert deployed.model("qwen3.8-27b") == expected
    argv = deployed.server_argv("qwen3.8-27b")
    assert argv[argv.index("--gdn-prefill-backend")+1] == "triton"
    assert "--no-enable-chunked-prefill" in argv
    assert (ROOT/"configs/vllm_inference.yaml").read_bytes() == original
    assert deployed.model("gemma-4-31b")["served_model_name"] == "google/gemma-4-31B-it"
    assert deployed.model("gemma-4-31b")["mm_processor_kwargs"] == {"max_soft_tokens":1120}
    assert "gemma-4-26b-a4b" not in deployed.data["models"]
    first = target.read_bytes()
    make_profile(config(), target)
    assert target.read_bytes() == first
    target.write_text("unrelated historical profile")
    with pytest.raises(ValueError, match="overwrite"):
        make_profile(config(), target)


def test_smoke_has_no_hidden_script_or_early_slurm_deadline():
    import math
    from .main import supervisor_deadline
    c = config()
    assert c["smoke"]["max_seconds"] is None
    assert c["smoke"]["job_seconds"] == 1800 and c["smoke"]["max_jobs"] == 5
    assert math.isinf(supervisor_deadline(c, 100, True))
    assert supervisor_deadline(c, 100, False) == 100+28800-360
    script = (ROOT/"RQs/RQ3_8/scripts/gpu_job.sh").read_text()
    assert "#SBATCH --signal" not in script
    assert "timeout 600" not in script
    assert script.index("bash RQs/RQ3_8/scripts/cpu_job.sh") < script.index('args=(supervise --smoke-cases)')


@pytest.mark.parametrize("model", ["qwen3.8-27b", "gemma-4-31b"])
@pytest.mark.parametrize("port", [30381, 45123])
def test_allocated_endpoint_reaches_probe_tokenizer_and_generation(tmp_path, monkeypatch, model, port):
    import io
    import openai
    from vlmrca.vlm import client
    from vlmrca.vlm.configs import get_config
    from RQs.RQ3_6.src.utils import model_probe
    from .utils import bind_client_endpoint
    monkeypatch.setenv("VLLM_BASE_URL", "http://127.0.0.1:8000/v1")
    monkeypatch.setenv("CANVASRCA_VLLM_PORT", str(port))
    profile_path = tmp_path/"runtime.yaml"
    runtime = make_profile(config(), profile_path)
    monkeypatch.setenv("CANVASRCA_VLLM_CONFIG", str(profile_path))
    spec = runtime["models"][model]
    bound = bind_client_endpoint(model, spec)
    cfg = get_config(model)
    assert bound["base_url"] == spec["base_url"] == f"http://127.0.0.1:{port}/v1"
    requests = []
    def urlopen(request, **kwargs):
        requests.append(request.full_url)
        value = {"data": [{"id": cfg.model_id}]} if request.full_url.endswith("/models") else {"count": 7}
        return io.BytesIO(json.dumps(value).encode())
    monkeypatch.setattr(client.urllib.request, "urlopen", urlopen)
    assert model_probe(spec)
    assert client.count_vllm_prompt_tokens([client.text_part("diagnostic fixture")], cfg) == 7
    class CapturedSDK(Exception):
        pass
    def sdk(**kwargs):
        assert kwargs["base_url"] == spec["base_url"]
        assert kwargs["timeout"] == 300
        raise CapturedSDK
    monkeypatch.setattr(openai, "OpenAI", sdk)
    with pytest.raises(CapturedSDK):
        client._call_openai([client.text_part("diagnostic fixture")], cfg, None)
    assert requests == [spec["base_url"]+"/models", f"http://127.0.0.1:{port}/tokenize"]
    assert os.environ["VLLM_BASE_URL"] == spec["base_url"]


@pytest.mark.parametrize("url", ["http://127.0.0.1:8000/v1", "http://remote:30381/v1"])
def test_endpoint_binding_rejects_wrong_port_or_nonlocal_host(tmp_path, monkeypatch, url):
    from .utils import bind_client_endpoint
    monkeypatch.setenv("CANVASRCA_VLLM_PORT", "30381")
    target = tmp_path/"runtime.yaml"
    spec = make_profile(config(), target)["models"]["qwen3.8-27b"]
    monkeypatch.setenv("CANVASRCA_VLLM_CONFIG", str(target))
    with pytest.raises(ValueError, match="loopback port"):
        bind_client_endpoint("qwen3.8-27b", {**spec, "base_url": url})


def test_tokenizer_failure_reports_address_not_credentials(tmp_path, monkeypatch, caplog):
    import urllib.error
    from vlmrca.vlm import client
    from vlmrca.vlm.configs import get_config
    target = tmp_path/"runtime.yaml"
    make_profile(config(), target)
    monkeypatch.setenv("CANVASRCA_VLLM_CONFIG", str(target))
    monkeypatch.setenv("VLLM_BASE_URL", "http://127.0.0.1:30381/v1")
    monkeypatch.setenv("VLLM_API_KEY", "not-a-real-key-test-sentinel")
    def fail(*args, **kwargs):
        raise urllib.error.URLError("private detail must not be printed")
    monkeypatch.setattr(client.urllib.request, "urlopen", fail)
    assert client.count_vllm_prompt_tokens([client.text_part("private-prompt-sentinel")], get_config("qwen3.8-27b")) is None
    assert "127.0.0.1:30381/tokenize" in caplog.text and "URLError" in caplog.text
    assert not any(s in caplog.text for s in ["not-a-real-key-test-sentinel", "private-prompt-sentinel", "private detail"])


def test_supervisor_exception_durably_replaces_running_status(tmp_path):
    from .utils import read_json, supervisor_failure_record
    write_json(tmp_path/"supervisor.json", {"status": "running"})
    with pytest.raises(RuntimeError, match="Inference driver exited"):
        with supervisor_failure_record(tmp_path, True):
            raise RuntimeError("Inference driver exited 1")
    report = read_json(tmp_path/"supervisor.json")
    assert report["status"] == report["qualification"] == "failed"
    assert "Inference driver exited 1" in report["error"] and report["seconds"] >= 0


@pytest.mark.parametrize("outcome,keys,ready,error,expected", [
    ("complete", [], [], False, "incomplete"),
    ("bounded_timeout", [], [], False, "incomplete"),
    ("interrupted", ["q", "g"], ["qwen3.8-27b", "gemma-4-31b"], False, "incomplete"),
    ("complete", ["q"], ["qwen3.8-27b"], False, "incomplete"),
    ("complete", ["q", "g"], ["qwen3.8-27b", "gemma-4-31b"], False, "passed"),
    ("complete", ["q", "g"], ["qwen3.8-27b", "gemma-4-31b"], True, "failed"),
])
def test_smoke_status_requires_actual_completed_coverage(outcome, keys, ready, error, expected):
    from .gates import smoke_status
    flags = [{"logical_key": k, "status": "done"} for k in keys]
    states = {"infrastructure_failure": 1} if error else {}
    assert smoke_status(outcome, states, flags, {"q", "g"}, set(ready)) == expected


def test_resume_reads_terminal_flag_only(tmp_path):
    f = tmp_path/"flag.json"
    assert read_flag(f) is None
    for status in ("done", "fail", "design_infeasible"):
        write_json(f, {"status":status})
        assert read_flag(f)["status"] == status
    assert logical_key("qwen3.8-27b", "INC-0", "FULL") != logical_key("gemma-4-31b", "INC-0", "FULL")
    assert logical_key("qwen3.8-27b", "INC-0", "FULL") != logical_key("qwen3.8-27b", "INC-0", "FULL", True)


@pytest.mark.skipif(os.environ.get("RENDER_BROWSER_TESTS") != "1", reason="browser opt-in")
def test_approved_preview_pixels_and_ablated_slot_pixels(tmp_path):
    from PIL import Image, ImageChops
    from renderer.main import render
    source = ROOT/"build/renderer_previews/deployment_groups_v1/aegislab_dashboard"
    if not source.exists():
        pytest.skip("local historical PNG comparison fixture is not deployed here")
    evidence = json.loads((source/"evidence.json").read_text())
    original_design = json.loads((source/"design.json").read_text())
    assert preset(evidence, "relations_first") == original_design
    # Pin the published design and the historical web/font/dependency artifacts.
    # Cross-OS font rasterization is recorded, not confused with a layout edit.
    original_manifest = json.loads((source/"manifest.json").read_text())
    reference = render(source/"evidence.json", source/"design.json", tmp_path/"frozen_reference")
    for field in ("font_sha256", "bundle_sha256", "css_sha256", "dependency_lock_sha256"):
        assert reference[field] == original_manifest[field]
    assert reference["rectangles"] == original_manifest["rectangles"]
    outputs = {}
    for arm in ("FULL", "MR00", "NO_ONSET"):
        selected, design = exps.fixed_slot_design(evidence, arm)
        write_json(tmp_path/(arm+".e.json"), selected)
        write_json(tmp_path/(arm+".d.json"), design)
        report = render(tmp_path/(arm+".e.json"), tmp_path/(arm+".d.json"), tmp_path/arm)
        assert report["status"] == "passed"
        outputs[arm] = (Image.open(tmp_path/arm/"dashboard.png").convert("RGB"), report)
    full, _ = outputs["FULL"]
    assert ImageChops.difference(full, Image.open(tmp_path/"frozen_reference/dashboard.png").convert("RGB")).getbbox() is None
    delta = ImageChops.difference(full, Image.open(source/"dashboard.png").convert("RGB"))
    write_json(tmp_path/"cross_environment.json", {
        "historical_browser": original_manifest["browser_version"], "current_browser": reference["browser_version"],
        "identical_bytes_to_historical_host": delta.getbbox() is None,
        "different_rgb_channels": sum(value for i,value in enumerate(delta.histogram()) if i % 256 != 0),
        "scope": "Original design/geometry/artifacts exact; cross-host raster difference recorded, not silently rebaselined"})
    delta.save(tmp_path/"cross_environment_diff.png")
    for arm in ("MR00", "NO_ONSET"):
        img, report = outputs[arm]
        for r in report["rectangles"]:
            bbox = (r["x"], r["y"], r["x"]+r["width"], r["y"]+r["height"])
            assert ImageChops.difference(full.crop(bbox), img.crop(bbox)).getbbox() is None


def test_pending_skip_does_not_open_contexts(tmp_path):
    from .main import pending_rows
    oid, model = "INC-ABC", "qwen3.8-27b"
    for arm in ARMS:
        key = logical_key(model, oid, arm)
        write_json(tmp_path/"flags"/(key+".json"), {"status":"done","logical_key":key})
    assert pending_rows(tmp_path,[{"opaque_incident_id":oid}],model,ARMS,False) == []


def test_non_timeout_failure_blocks_but_timeout_is_skipped(tmp_path):
    from .main import terminal
    key = logical_key("qwen3.8-27b","INC-X","FULL")
    f = tmp_path/"flags"/(key+".json")
    write_json(f,{"status":"fail","logical_key":key,"failure_class":"request_timeout"})
    assert terminal(tmp_path,"qwen3.8-27b","INC-X","FULL",False)["status"] == "fail"
    write_json(f,{"status":"fail","logical_key":key,"failure_class":"infrastructure"})
    with pytest.raises(RuntimeError,match="diagnosis"):
        terminal(tmp_path,"qwen3.8-27b","INC-X","FULL",False)


def test_shared_budget_caps_include_all_six_shards_and_smoke():
    c = config()
    roster = json.loads((ROOT/c["preparation"]/"roster.json").read_text())
    assert sum(sum(r["shard"]==s for r in roster["cases"]) for s in range(3)) == 480
    caps = [sum(r["shard"]==s for r in roster["cases"])*8+500 for m in range(2) for s in range(3)]
    assert 28216+sum(caps)+18 == 38914 < 40000


@pytest.mark.parametrize("failure", [None,"timeout","infrastructure","context"])
def test_transaction_terminal_and_dedup(tmp_path, monkeypatch, failure):
    import threading
    from . import main
    from RQs.RQ3_1.src import main as parent
    row = {"opaque_incident_id":"INC-ABC", "dataset":"aiops2025"}
    c = {"preparation":"prep", "experiment":"unit", "execution":{"min_free_disk_gib":0}}
    monkeypatch.setattr(main,"path",lambda p:tmp_path/p)
    bundle = exps.public_bundle({"system":"RCA","parts":[{"type":"text","text":"Facts"},{"type":"text","text":"Question"}],
        "metrics":[],"candidates":["123"],"selected_relations":[],"full_relations":[]},sample())
    write_json(tmp_path/"prep/public/INC-ABC.json",bundle)
    # Equal PNGs deliberately exercise exact-request reuse across arm names.
    png = tmp_path/"prep/example.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\nfixture")
    write_json(tmp_path/"prep/render_flags/INC-ABC.json",{"arms":{a:{"png":"example.png"} for a in ("FULL","MR10")}})
    write_json(tmp_path/"prep/private/INC-ABC.json",{"numeric_to_natural":{"123":"svc"},"accepted_labels":["svc"]})
    monkeypatch.setattr(parent,"_request_envelope",lambda *a,**k:{"schema":{},"system":"RCA","effective_server":{}})
    monkeypatch.setattr(parent,"score_response_callback",lambda *a:lambda text:{})
    calls=[]
    def call(task,*a,**k):
        calls.append(task)
        if failure=="timeout":
            raise TimeoutError("transport")
        if failure=="infrastructure":
            raise RuntimeError("engine died")
        if failure=="context":
            raise ValueError("input exceeds context: 40000+8192")
        return {"status":"complete","call_key":task["call_key"]}
    monkeypatch.setattr(parent,"run_registered_call",call)
    root=tmp_path/"out"
    root.mkdir()
    stop=threading.Event()
    if failure=="infrastructure":
        with pytest.raises(RuntimeError,match="engine died"):
            main.execute_case(c,row,"qwen3.8-27b",["FULL","MR10"],root,None,stop,False)
        assert stop.is_set()
        return
    main.execute_case(c,row,"qwen3.8-27b",["FULL","MR10"],root,None,stop,False)
    assert len(calls)==(1 if failure is None else 2)
    n=len(calls)
    main.execute_case(c,row,"qwen3.8-27b",["FULL","MR10"],root,None,stop,False)
    assert len(calls)==n
