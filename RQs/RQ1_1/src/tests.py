"""Static and CPU-only qualification for RQ1.1."""

from __future__ import annotations

import ast
import hashlib
import io
import json
import math
import os
import py_compile
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pandas as pd
from PIL import Image

from unified_scripts import stable_hash
from unified_scripts.vllm_inference import VLLMInferenceConfig

from .exps import (
    QA_ARMS,
    RCA_ARMS,
    REGIONS,
    PreparedCase,
    build_visible_packet,
    build_denum_log_graph,
    compile_text_screenshot,
    denum_text,
    denum_visible_rows,
    execute_tool,
    experiment_registry,
    multi_stage_analysis_parts,
    packet_text,
    questions_for_case,
    representation_audit,
    representation_parts,
    score_qa,
    validate_diagnosis,
    validate_qa,
)
from .gates import analyze_direct_multi, analyze_records
from .utils import DEFAULT_CONFIG, ROOT, RQ1Error, load_yaml


def _assert(value: Any, message: str) -> None:
    if not value:
        raise RQ1Error(message)


def _lines(paths: list[Path]) -> int:
    return sum(len(path.read_text(encoding="utf-8").splitlines()) for path in paths)


def check_layout() -> dict[str, Any]:
    rq = ROOT / "RQs/RQ1_1"
    required_dirs = {"configs", "descriptions", "findings", "results", "scripts", "src"}
    _assert(required_dirs <= {path.name for path in rq.iterdir() if path.is_dir()}, "RQ1.1 directory layout incomplete")
    descriptions = {path.name for path in (rq / "descriptions").glob("*.md")}
    _assert(descriptions == {"RQ1_1_statement.md", "RQ1_1_experiments.md", "RQ1_1_roadMap.md"}, "descriptions must contain exactly three canonical files")
    findings = {path.name for path in (rq / "findings").glob("*.md")}
    _assert(findings == {"exp_direct_rca_findings.md", "exp_direct_qa_findings.md", "exp_multi_stage_rca_findings.md"}, "findings must contain exactly one file per experiment")
    functional = [rq / "src" / name for name in ("main.py", "utils.py", "exps.py", "tests.py", "gates.py")]
    _assert(all(path.is_file() for path in functional) and (rq / "src/__init__.py").is_file(), "functional source files missing")
    _assert(_lines(functional) <= 5000, "RQ1.1 functional Python exceeds 5000 lines")
    scripts = list((rq / "scripts").glob("*.sh"))
    _assert(len(scripts) <= 10 and _lines(scripts) <= 800, "RQ1.1 shell script budget exceeded")
    return {"functional_python_lines": _lines(functional), "shell_files": len(scripts), "shell_lines": _lines(scripts)}


def check_syntax() -> dict[str, int]:
    paths = list((ROOT / "RQs/RQ1_1").rglob("*.py"))
    for path in paths:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        py_compile.compile(str(path), doraise=True)
    return {"python_files": len(paths)}


def check_config(config: dict[str, Any]) -> dict[str, Any]:
    specs = experiment_registry(config)
    _assert(set(specs) == {"direct_rca", "direct_qa", "multi_stage_rca"}, "unexpected RQ1.1 experiment registry")
    _assert(specs["direct_rca"].arms == RCA_ARMS and specs["multi_stage_rca"].arms == RCA_ARMS, "seven RCA arms drifted")
    _assert(specs["direct_qa"].arms == QA_ARMS, "direct-QA L1-L4 arms drifted")
    _assert(specs["multi_stage_rca"].steps == 3 and specs["multi_stage_rca"].calls_per_case_arm == 6, "three-step/two-call state machine drifted")
    _assert(config["runtime"]["models"] == ["qwen3.8-27b", "gemma-4-26b-a4b"], "active model list drifted")
    _assert(config["external_methods"]["denum"]["binary_output"] is False, "binary Denum output is prohibited")
    _assert(config["runtime"]["smoke_call_cap_total"] == 18 and config["runtime"]["smoke_timeout_seconds_total"] == 600, "shared smoke bounds drifted")
    multi_plan = config["smoke_plans"]["multi_stage_rca"]
    multi_calls = sum(
        6 if arm == multi_plan["full_arm"] else 2
        for model in config["runtime"]["models"]
        for dataset in config["data"]["smoke_datasets"]
        for arm in (multi_plan[model].get(dataset) or ())
    )
    _assert(multi_plan["total_calls"] == multi_calls == 18, "multi-stage smoke does not equal the shared 18-call cap")
    _assert(sum(len(v) for k, v in config["smoke_plans"]["direct_rca"].items()) * 2 == 14, "direct-RCA smoke call count drifted")
    _assert(sum(len(v) for k, v in config["smoke_plans"]["direct_qa"].items()) * 2 == 8, "direct-QA smoke call count drifted")
    return {"experiments": sorted(specs), "models": list(config["runtime"]["models"])}


def check_provenance(config: dict[str, Any]) -> dict[str, Any]:
    migration = ROOT / "artifacts/rq1_1_migration"
    _assert((migration / "rq1_source.sha256").is_file(), "RQ1 source provenance missing")
    _assert((migration / "rq1_1_initial_copy.normalized.sha256").is_file(), "RQ1.1 initial-copy provenance missing")
    left = (migration / "rq1_source.sha256").read_text()
    right = (migration / "rq1_1_initial_copy.normalized.sha256").read_text()
    _assert(left == right, "RQ1→RQ1.1 initial-copy byte equality failed")
    source = json.loads((ROOT / "packages/THIRD_PARTY_SOURCES.json").read_text())
    for name, expected in (("ReAct", config["external_methods"]["react"]["commit"]), ("Denum", config["external_methods"]["denum"]["commit"])):
        _assert(source[name]["commit"] == expected, f"{name} commit provenance drifted")
        _assert((ROOT / "packages" / name / source[name]["license_file"]).is_file(), f"{name} license missing")
    return {"initial_copy_sha256": hashlib.sha256(left.encode()).hexdigest(), "packages": source}


def check_renderer_inheritance() -> dict[str, Any]:
    from .renderer.dashboard import RENDERER_VERSION

    renderer_root = ROOT / "RQs/RQ1_1/src/renderer"
    current = {
        str(path.relative_to(renderer_root)): stable_hash(
            ast.dump(ast.parse(path.read_text(encoding="utf-8")), include_attributes=False)
        )
        for path in sorted(renderer_root.rglob("*.py"))
        if path.name != "diagnostics.py"
    }
    _assert(RENDERER_VERSION == 13, "authorized RQ1.1 renderer-v13 is not active")
    _assert(not (ROOT / "RQs/RQ1_1/src/renderer/diagnostics.py").exists(), "retired attention diagnostics remain active")
    return {"renderer_files": len(current), "renderer_tree_hash": stable_hash(current), "renderer_version": RENDERER_VERSION}


def check_denum() -> dict[str, Any]:
    frame = pd.DataFrame({
        "timestamp": [0.0, 1.0, 2.0, 3.0],
        "container_name": ["svc-a"] * 4,
        "level": ["ERROR", "ERROR", "INFO", "ERROR"],
        "message": [
            "\x1b[31mtimeout after 1200 ms status=504\x1b[0m",
            "timeout after 1250 ms status=504",
            "peer=10.0.0.2 uuid=123e4567-e89b-12d3-a456-426614174000",
            "hex=0xFF float=-3.25 missing=null",
        ],
    })
    graph = build_denum_log_graph(frame, {"svc-a": "222"})
    _assert(graph["semantic_round_trip"] and not graph["binary_output"], "Denum readable graph round-trip failed")
    text = denum_text(graph, denum_visible_rows(graph, 8))
    _assert("1200" in text and "504" in text and "LT" in text, "Denum projection discarded diagnostic numeric/template facts")
    _assert("svc-a" not in text and "222" in text, "Denum projection failed entity anonymization")
    return {"events": graph["event_count"], "templates": graph["template_count"], "character_ratio": graph["character_compression_ratio"]}


def _fixture_packet() -> dict[str, Any]:
    facts = []
    for index, region in enumerate(REGIONS):
        field = {"M": "metric_series_64", "R": "trace_summary_entry", "L": "denum_log_template", "G": "directed_call_edge"}[region]
        payload: dict[str, Any]
        if region == "M":
            payload = {"panel_id": "M01", "values": ["1.0"] + [None] * 63}
        elif region == "R":
            payload = {"p95_during_ms": "12.0"}
        elif region == "L":
            payload = {"template_id": "LT01"}
        else:
            payload = {"caller": "222", "callee": "333"}
        fact = {"region": region, "field": field, "entity_ids": ["222"] if region != "G" else ["222", "333"], "relative_bins": [0], "unit": None, "payload": payload}
        fact["fact_id"] = hashlib.sha256(stable_hash(fact).encode()).hexdigest()[:16]
        facts.append(fact)
    packet = {"schema_version": "fixture", "opaque_incident_id": "INC-FIXTURE", "candidates": ["222", "333"], "facts": facts}
    packet["fact_inventory_hash"] = stable_hash(facts)
    return packet


def check_questions_and_arms() -> dict[str, Any]:
    packet = _fixture_packet()
    templates, selected = questions_for_case(packet, "INC-FIXTURE")
    counts = {level: sum(q.level == level for q in templates) for level in range(1, 5)}
    _assert(counts == {1: 4, 2: 12, 3: 24, 4: 24}, "64 ordered QA templates drifted")
    _assert({q.level for q in selected} == {1, 2, 3, 4}, "one question per level was not selected")
    for question in selected:
        payload = {"steps": [{"region": region, "values": list(values)} for region, values in zip(question.regions, question.answer_steps, strict=True)]}
        normalized = validate_qa(payload, question.public())
        _assert(score_qa(normalized, question.private())["complete_chain_accuracy"] == 1.0, "QA exact scorer drifted")
    text = packet_text(packet)
    image = Image.new("RGB", (100, 100), "white")
    with tempfile.NamedTemporaryFile(suffix=".png") as file:
        image.save(file.name)
        png = Path(file.name).read_bytes()
    prepared = PreparedCase(
        {
            "packet": packet,
            "region_crop_audit": {"crop_boxes_px": {
                "M": [[0, 0, 50, 100]], "R": [[50, 66, 100, 100]],
                "L": [[50, 33, 100, 66]], "G": [[50, 0, 100, 33]],
            }},
        },
        {}, png, (png,), {region: (png,) for region in REGIONS},
    )
    for arm in RCA_ARMS:
        parts = representation_parts(arm, prepared)
        _assert(parts and any(part["type"] == "image" for part in parts) == (arm != "T"), f"arm {arm} transport drifted")
    visual_analysis = multi_stage_analysis_parts("V", prepared, 1, [], {"status": "ok"})
    text_analysis = multi_stage_analysis_parts("T", prepared, 1, [], {"status": "ok"})
    _assert(any(part["type"] == "image" for part in visual_analysis), "visual evidence missing from post-tool analysis")
    _assert(not any(part["type"] == "image" for part in text_analysis), "text arm gained visual evidence in post-tool analysis")
    audit = representation_audit(packet, png, (png,), {region: (png,) for region in REGIONS}, text)
    _assert(audit["s_equals_t_bytes"] and len(set(audit["fact_inventory_hash_by_arm"].values())) == 1, "seven-arm equality audit failed")
    pages = compile_text_screenshot(text)
    _assert(pages == compile_text_screenshot(text), "pixel-text renderer is not deterministic")
    _assert(Image.open(io.BytesIO(pages[0])).size == (1800, 1600), "inherited pixel-text geometry drifted")
    validate_diagnosis({"services": ["222"], "reason": "fixture", "confidence": "high"}, packet["candidates"])
    return {"template_counts": counts, "selected": [q.query_id for q in selected], "arms": list(RCA_ARMS)}


def check_candidate_universe() -> dict[str, Any]:
    metric_rows = [{
        "panel_id": f"M{index + 1}", "rank": index + 1,
        "service": "222", "metric": f"metric_{index + 1}",
        "values": [float(index)] * 64, "missing_mask": [False] * 64,
        "baseline": float(index), "peak": float(index), "signed_z": 0.0,
    } for index in range(12)]
    ceb = {
        "opaque_incident_id": "INC-CANDIDATE-FIXTURE",
        "candidates": ["222", "333"],
        "metric_series": metric_rows,
        "observation_window": {"duration_rel_s": 64.0, "source_metric_rows": 12},
        "fault_window_rel_s": [20.0, 40.0],
        "trace_summary": {"entries": []},
        "propagation": {
            "mode": "onset", "selection_mode": "severity", "context_services": [],
            "services": [], "directed_call_edges": [{"caller": "222", "callee": "333"}],
            "omitted_services": 0, "omitted_edges": 0,
        },
        "missingness": {"traces_missing": True, "propagation_missing": False},
    }
    packet = build_visible_packet(ceb, "renderer-fixture", "manifest-fixture")
    visible = {entity for fact in packet["facts"] for entity in fact.get("entity_ids", ())}
    _assert(visible <= set(packet["candidates"]), "visible entity escaped the candidate universe")
    rejected = False
    try:
        build_visible_packet({**ceb, "candidates": ["222"]}, "renderer-fixture", "manifest-fixture")
    except RQ1Error as error:
        rejected = "absent from the exhaustive candidate set" in str(error)
    _assert(rejected, "incomplete candidate universe did not fail closed")
    return {"candidate_count": len(packet["candidates"]), "visible_entity_count": len(visible)}


def check_tools(config: dict[str, Any]) -> dict[str, Any]:
    index = {
        "metrics": [{"entity_id": "222", "metric": "cpu", "values": list(map(str, range(64))), "missing_mask": [False] * 64}],
        "traces": [{"entity_id": "222", "operation": "GET", "spans": [1] * 64, "errors": [0] * 64, "p95_ms": ["2"] * 64}],
        "logs": {"entries": [{"entity_id": "222", "template_id": "LT01", "relative_bin": 4, "count": 2}]},
        "topology": [{"caller": "222", "callee": "333"}],
    }
    actions = [
        {"tool": "search_metrics", "arguments": {"entity_id": "222", "start_bin": 1, "end_bin": 2}},
        {"tool": "search_traces", "arguments": {"entity_id": "222"}},
        {"tool": "search_logs", "arguments": {"template_id": "LT01"}},
        {"tool": "search_topology", "arguments": {"entity_id": "222", "direction": "downstream"}},
    ]
    outputs = [execute_tool(action, index, config) for action in actions]
    _assert(all(row["status"] == "ok" and row["returned_rows"] == 1 for row in outputs), "canonical tool execution failed")
    _assert(execute_tool({"tool": "bad", "arguments": {}}, index, config)["status"] == "invalid_tool", "invalid tool is not deterministic")
    _assert(outputs == [execute_tool(action, index, config) for action in actions], "tool output is not deterministic")
    return {"tools": [row["tool"] for row in outputs]}


def check_analysis_semantics(config: dict[str, Any]) -> dict[str, Any]:
    spec = experiment_registry(config)["direct_rca"]
    records = [{
        "model": "qwen3.8-27b", "arm": "T", "opaque_incident_id": "INC-A",
        "analysis_dataset": "aegislab", "analysis_fault_type": "fixture",
        "status": "completed", "model_output_valid": False,
        "model_output_errors": [{"stage": 1, "error": "invalid ID"}],
        "model_calls": 1, "stages": [], "score": {"mrr": 0.0, "ac@1": 0.0},
    }]
    result = analyze_records(records, spec, config)
    _assert(result["infrastructure_errors"] == 0, "model answer error was misclassified as infrastructure")
    _assert(result["model_output_errors"] == 1 and result["parse_rate"] == 0.0, "model output validity accounting drifted")
    direct, multi = [], []
    for case, direct_hit, multi_hit in (("INC-A", 0.0, 1.0), ("INC-B", 1.0, 0.0)):
        common = {
            "model": "qwen3.8-27b", "arm": "T", "opaque_incident_id": case,
            "analysis_dataset": "aegislab", "status": "completed",
            "model_output_valid": True,
        }
        direct.append({**common, "stages": [{"total_tokens": 10}], "score": {"mrr": direct_hit, "ac@1": direct_hit}})
        multi.append({**common, "stages": [{"planner": {"total_tokens": 10}, "analysis": {"total_tokens": 20}}], "score": {"mrr": multi_hit, "ac@1": multi_hit}})
    cross = analyze_direct_multi(direct, multi, config)
    headline = next(row for row in cross["rows"] if row["scope"] == "headline")
    _assert(headline["n"] == 2 and headline["repair_rate_at_1"] == 0.5 and headline["break_rate_at_1"] == 0.5, "direct/multi repair-break analysis drifted")
    _assert(headline["token_cost_ratio"] == 3.0, "direct/multi token accounting drifted")
    return {"infrastructure_errors": 0, "model_output_errors": 1, "cross_experiment_pairs": 2}


def check_inference_projection(config: dict[str, Any]) -> dict[str, Any]:
    before = json.loads((ROOT / "artifacts/rq1_1_migration/inference_effective_before.json").read_text())
    selected = VLLMInferenceConfig.load(config["unified"]["vllm"])
    override = os.environ.pop("CANVASRCA_VLLM_CONFIG", None)
    try:
        nibi = VLLMInferenceConfig.load(config["unified"]["vllm"])
    finally:
        if override is not None:
            os.environ["CANVASRCA_VLLM_CONFIG"] = override
    after = {model: {key: nibi.model(model).get(key) for key in values} for model, values in before.items()}
    _assert(before == after, "non-attention model/server/request inference projection changed")
    _assert(nibi.model("qwen3.8-27b")["mm_processor_kwargs"] is None, "Qwen3.8 image policy drifted")
    local = VLLMInferenceConfig.load("configs/vllm_inference_local.yaml")
    nibi_normalized, local_normalized = deepcopy(dict(nibi.data)), deepcopy(dict(local.data))
    for payload in (nibi_normalized, local_normalized):
        payload["deployment"] = {"profile": "normalized", "python": "normalized", "vllm_bin": "normalized"}
        payload["common"]["gpu_memory_utilization"] = "deployment-specific"
        for model in payload["models"].values():
            model["model_path"] = "deployment-specific"
    _assert(nibi_normalized == local_normalized, "local and Nibi inference profiles differ beyond paths/VRAM")
    _assert(local.data["common"]["gpu_memory_utilization"] == 0.65, "local VRAM ceiling drifted")
    _assert(nibi.data["common"]["gpu_memory_utilization"] is None, "Nibi VRAM policy drifted")
    _assert("--gpu-memory-utilization" in local.server_argv("qwen3.8-27b"), "local launcher omits VRAM ceiling")
    _assert("--gpu-memory-utilization" not in nibi.server_argv("qwen3.8-27b"), "Nibi launcher gained a VRAM ceiling")
    local_launcher = (
        (ROOT / "scripts/vllm_vlm/serve_canvasrca_local.sh").read_text()
        + (ROOT / "scripts/env_local.sh").read_text()
        + (ROOT / "RQs/RQ1_1/scripts/run_local.sh").read_text()
    )
    nibi_launcher = (ROOT / "scripts/vllm_vlm/serve_canvasrca_nibi.sh").read_text()
    _assert("vllm_inference_local.yaml" in local_launcher, "local launcher does not select local profile")
    _assert("sbatch" not in local_launcher.lower(), "local WSL entry points must not submit Slurm jobs")
    _assert("#SBATCH" not in local_launcher, "local WSL entry points must not contain Slurm directives")
    _assert("configs/vllm_inference.yaml" in nibi_launcher, "Nibi launcher does not reset inherited local profile")
    return {
        "nibi_projection_sha256": stable_hash(after),
        "local_effective_sha256": local.effective_hash(),
        "selected_profile": selected.data["deployment"]["profile"],
        "parity_except_paths_and_vram": True,
    }


def check_attention_protocol() -> dict[str, Any]:
    from types import SimpleNamespace

    import torch
    import vlmrca.vlm.attention_probe as attention_probe
    from .main import _image_attention_diagnostics
    from vlmrca.vlm.attention_probe import _find_text_tokens, map_groups_to_images

    _assert(
        _find_text_tokens([9, 2, 3, 4, 8], [1, 2, 3, 4, 5], 0) == (1, 1, 1),
        "chat-template boundary-tolerant text mapping drifted",
    )

    image = Image.new("RGB", (100, 100), "white")
    stream = io.BytesIO(); image.save(stream, format="PNG")
    probe = {
        "method": "fixture", "request_id": "fixture", "model": "fixture",
        "layer_name": "fixture", "image_groups": [{
            "weights": [0.4, 0.1, 0.1, 0.1],
            "value_norms": [0.01, 2.0, 2.0, 2.0],
            "attention_weighted_value_norms": [0.004, 0.2, 0.2, 0.2],
        }],
    }
    mapped = map_groups_to_images(probe, [stream.getvalue()])[0]
    _assert(mapped["attention_peak_diagnostics"]["argmax_patch_index"] == 0, "attention peak index drifted")
    _assert(mapped["weighted_value_peak_diagnostics"]["argmax_patch_index"] != 0, "A·V diagnostic does not distinguish a synthetic sink")

    for model, layer, image_token in (
        ("qwen3.8-27b", 3, 248056), ("gemma-4-26b-a4b", 5, 258880),
    ):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {
                "CANVASRCA_ATTENTION_PROBE": "1", "CANVASRCA_ATTENTION_MODEL": model,
                "CANVASRCA_ATTENTION_DIR": directory,
            }, clear=False):
                request_id = "canvas-fixture-12345678"
                batch = SimpleNamespace(
                    req_ids=[request_id], num_prompt_tokens=[6],
                    num_computed_tokens_cpu=[0],
                    token_ids_cpu=torch.tensor([[101, image_token, image_token, 202, 203, 204]]),
                )
                attention_probe._STATE.runner = SimpleNamespace(input_batch=batch)
                attention_probe._STATE.scheduler_output = SimpleNamespace(
                    num_scheduled_tokens={request_id: 6},
                )
                target = SimpleNamespace(
                    layer_name=f"language_model.model.layers.{layer}.self_attn.attn",
                    num_heads=4, num_kv_heads=2, head_size=3,
                    impl=SimpleNamespace(scale=0.5, logits_soft_cap=None),
                )
                attention_probe._capture(
                    target, torch.randn(6, 12), torch.randn(6, 6), torch.randn(6, 6),
                )
                sidecar = attention_probe.read_sidecar("canvas-fixture")
                _assert(sidecar is not None and len(sidecar["prompt_token_ids"]) == 5, f"{model} prompt capture failed")
                group = sidecar["image_groups"][0]
                _assert(
                    len(group["weights"]) == len(group["value_norms"]) == len(group["attention_weighted_value_norms"]) == 2,
                    f"{model} visual value capture failed",
                )
                attention_probe._STATE.runner = attention_probe._STATE.scheduler_output = None
                attention_probe._KV.clear()

    artifact = {
        "grid": [16, 16], "image_size_px": [1600, 1200],
        "weights": [1.0 / 256] * 256, "global_attention_mass": 0.25,
    }
    part = {
        "attention_region": "dashboard",
        "attention_region_boxes": {
            "M": [[0, 0, 1200, 1000]], "R": [[1200, 700, 1600, 1000]],
            "L": [[1200, 400, 1600, 700]], "G": [[1200, 0, 1600, 400]],
        },
    }
    diagnostics = _image_attention_diagnostics(artifact, part)
    _assert(
        math.isclose(diagnostics["within_image_region_mass"]["dashboard_header_band"], 1 / 16),
        "first-grid-row dashboard header accounting drifted",
    )
    _assert(
        math.isclose(sum(diagnostics["within_image_region_mass"].values()), 1.0),
        "image attention regions do not conserve within-image mass",
    )
    launchers = [
        ROOT / "scripts/vllm_vlm/serve_canvasrca_local.sh",
        ROOT / "scripts/vllm_vlm/serve_canvasrca_nibi.sh",
    ]
    for launcher in launchers:
        text = launcher.read_text(encoding="utf-8")
        _assert("CANVASRCA_ATTENTION_PROBE=1" in text, f"attention probe disabled in {launcher.name}")
        _assert("CANVASRCA_ATTENTION_PROBE_REQUIRED=1" in text, f"attention integrity is optional in {launcher.name}")
    return {
        "same_prefill_required": True,
        "image_and_text": True,
        "weighted_value_diagnostic": True,
        "dashboard_header_band_mass": 1 / 16,
    }


def check_no_active_legacy() -> dict[str, Any]:
    active = [ROOT / "RQs/RQ1_1", ROOT / "src", ROOT / "configs", ROOT / "scripts"]
    offenders = []
    for root in active:
        for path in root.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts or path.suffix not in {".py", ".yaml", ".yml", ".sh"}:
                continue
            if path.resolve() == Path(__file__).resolve():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "CANVASRCA_LEGACY_PROCESSED_ROOT" in text or "local_legacy_adapter" in text:
                offenders.append(str(path.relative_to(ROOT)))
    _assert(not offenders, f"active legacy preparation paths remain: {sorted(set(offenders))[:10]}")
    return {"offenders": []}


def run_static_checks(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_yaml(config_path)
    result = {
        "layout": check_layout(), "syntax": check_syntax(), "config": check_config(config),
        "provenance": check_provenance(config), "renderer": check_renderer_inheritance(),
        "denum": check_denum(), "questions_and_arms": check_questions_and_arms(),
        "candidate_universe": check_candidate_universe(),
        "tools": check_tools(config), "analysis": check_analysis_semantics(config),
        "inference": check_inference_projection(config),
        "attention": check_attention_protocol(),
        "legacy_audit": check_no_active_legacy(),
    }
    result["passed"] = True
    result["static_sha256"] = stable_hash(result)
    return result
