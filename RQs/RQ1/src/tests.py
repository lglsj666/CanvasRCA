"""CPU-only structural and contract checks for the refactored RQ1 code."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Callable

from unified_scripts import stable_hash
from unified_scripts.rca_scorer import RCAScorer, RCAScorerConfig
from unified_scripts.vllm_inference import VLLMInferenceConfig
from RQs.RQ1.src.renderer.dashboard import opaque_incident_id

from .exps import (
    DIAGNOSE_SYSTEM, DIRECT_DIAGNOSE_SYSTEM, OBSERVE_SYSTEM, PROMPT_REGION_ORDER,
    QA_SYSTEM, RCA_ARMS,
    TEMPLATE_VALUE_KINDS,
    TYPED_ANSWER_SYSTEM, TYPED_OBSERVE_SYSTEM,
    _atomic_fact, _counterfactual_pairs, balanced_arm_order, build_qa_packet,
    compile_controlled_canvas, compile_pixel_text_pages, experiment_registry, factorial_cells, handoff_parts,
    ledger_image, ledger_images, normalize_stage1_ledger, normalize_typed_qa_ledger,
    qa_representation_parts, questions_for_case, representation_parts, response_schema,
    score_reasoning, validate_diagnosis, validate_qa_response, attention_diagnostics,
    render_attention_overlay, visual_diagnostic_for_arm, visual_patch_atlas,
    common_shell, _packet_flat, _packet_text, _packet_text_region_blocks,
    stage1_prompt, stage2_prompt,
)
from .main import _concurrency_partitions
from .gates import _rbo_at_k, analyze_stage_pair, qualification_contracts
from .utils import DEFAULT_CONFIG, ROOT, RQ1Error, audit_visible, load_yaml, numeric_entity_map

FUNCTIONAL_RQ_FILES = ("main.py", "utils.py", "exps.py", "tests.py", "gates.py")
ALL_RQ_SOURCE_FILES = set(FUNCTIONAL_RQ_FILES) | {"__init__.py"}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _line_count(paths: list[Path]) -> int:
    return sum(len(path.read_text(encoding="utf-8").splitlines()) for path in paths)


def check_global_layout() -> dict[str, Any]:
    configs = {path.name for path in (ROOT / "configs").iterdir() if path.is_file()}
    _assert(
        configs == {"vllm_inference.yaml", "dataset_segmentation.yaml", "rca_scorer.yaml"},
        f"root configs must contain exactly three unified files, found {sorted(configs)}",
    )
    non_shell = [str(path.relative_to(ROOT)) for path in (ROOT / "scripts").rglob("*") if path.is_file() and path.suffix != ".sh"]
    _assert(not non_shell, f"root scripts contains non-sh files: {non_shell}")
    non_python = [
        str(path.relative_to(ROOT))
        for path in (ROOT / "src").rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".py"
    ]
    _assert(not non_python, f"root src contains non-Python files: {non_python}")
    functional = {"vllm_inference.py", "dataset_segmentation.py", "rca_scorer.py"}
    observed = {path.name for path in (ROOT / "src/unified_scripts").glob("*.py")}
    _assert(functional <= observed, "one or more unified scripts are missing")
    return {"root_configs": sorted(configs), "root_scripts_only_sh": True, "root_src_only_py": True}


def check_rq_layouts() -> dict[str, Any]:
    checked: dict[str, Any] = {}
    for rq in sorted(path for path in (ROOT / "RQs").iterdir() if path.is_dir() and path.name.startswith("RQ")):
        number = rq.name
        expected_descriptions = {f"{number}_statement.md", f"{number}_experiments.md", f"{number}_roadMap.md"}
        descriptions = {path.name for path in (rq / "descriptions").iterdir() if path.is_file()}
        _assert(descriptions == expected_descriptions, f"{number} descriptions differ: {sorted(descriptions)}")
        sources = {path.name for path in (rq / "src").iterdir() if path.is_file()}
        _assert(sources == ALL_RQ_SOURCE_FILES, f"{number} src differs: {sorted(sources)}")
        source_dirs = {path.name for path in (rq / "src").iterdir() if path.is_dir() and path.name != "__pycache__"}
        if number == "RQ1":
            _assert(source_dirs == {"renderer"}, f"RQ1 src may contain only its provisional renderer package: {sorted(source_dirs)}")
        else:
            _assert(not source_dirs, f"{number} src contains unregistered packages: {sorted(source_dirs)}")
        scripts = [path for path in (rq / "scripts").iterdir() if path.is_file()]
        _assert(len(scripts) <= 10, f"{number} scripts exceeds ten files")
        _assert(all(path.suffix == ".sh" for path in scripts), f"{number} scripts contains non-sh files")
        script_lines = _line_count(scripts)
        _assert(script_lines <= 800, f"{number} scripts exceeds 800 lines")
        source_lines = _line_count([rq / "src" / name for name in FUNCTIONAL_RQ_FILES])
        _assert(source_lines <= 5000, f"{number} functional source exceeds 5000 lines: {source_lines}")
        findings = [path.name for path in (rq / "findings").iterdir() if path.is_file()]
        _assert(all(name.startswith("exp_") and name.endswith("_findings.md") for name in findings), f"{number} has a noncanonical finding filename")
        checked[number] = {"script_files": len(scripts), "script_lines": script_lines, "functional_source_lines": source_lines, "findings": len(findings)}
    return checked


def check_python_syntax() -> dict[str, int]:
    # Generated virtual environments live inside the Nibi worktree and can
    # contain non-source files ending in .py. Audit only project-owned trees.
    files = [*ROOT.glob("*.py")]
    for source_root in (ROOT / "src", ROOT / "RQs", ROOT / "tests"):
        if source_root.is_dir():
            files.extend(source_root.rglob("*.py"))
    for path in files:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {"parsed_python_files": len(files)}


def check_unified_contracts(config: dict[str, Any]) -> dict[str, Any]:
    runtime = VLLMInferenceConfig.load(config["unified"]["vllm"])
    _assert(
        runtime.data.get("protocol_version") == "vllm-inference-v5-nibi-same-pass-attention",
        "global vLLM max-sequences-128 protocol drifted",
    )
    _assert(
        all(runtime.model(tag)["max_tokens"] == 16384
            and runtime.model(tag)["max_num_seqs"] == 128
            for tag in ("qwen3.6-27b", "gemma-4-26b-a4b")),
        "registered model output/scheduler settings drifted",
    )
    qwen_args = runtime.server_argv("qwen3.6-27b")
    gemma_args = runtime.server_argv("gemma-4-26b-a4b")
    _assert("--gpu-memory-utilization" not in qwen_args + gemma_args, "Nibi launcher still has a VRAM fraction cap")
    _assert("--mm-processor-kwargs" not in qwen_args, "Qwen still has a project pixel limit")
    _assert("--mm-processor-kwargs" in gemma_args, "Gemma soft-token policy disappeared")
    _assert("--enable-chunked-prefill" in gemma_args, "Gemma chunked prefill disappeared")
    old_port = os.environ.get("CANVASRCA_VLLM_PORT")
    os.environ["CANVASRCA_VLLM_PORT"] = "28765"
    try:
        dynamic = runtime.model("qwen3.6-27b")
        dynamic_args = runtime.server_argv("qwen3.6-27b")
    finally:
        if old_port is None:
            os.environ.pop("CANVASRCA_VLLM_PORT", None)
        else:
            os.environ["CANVASRCA_VLLM_PORT"] = old_port
    _assert(dynamic["port"] == 28765, "deployment port override was ignored")
    _assert(dynamic["base_url"] == "http://127.0.0.1:28765/v1", "deployment URL override drifted")
    _assert(dynamic_args[dynamic_args.index("--port") + 1] == "28765", "server argv ignored deployment port")
    scorer = RCAScorer(RCAScorerConfig.load(config["unified"]["scorer"]), hit=lambda a, b: a == b)
    score = scorer.score(["wrong", "root"], ["root"]).as_dict()
    _assert(score["mrr"] == 0.5 and score["ac@1"] == 0.0 and score["ac@3"] == 1.0, "scorer metric definitions drifted")
    _assert(score["avg@3"] == 2 / 3 and score["avg@5"] == 4 / 5, "AVG@K drifted from cumulative-AC definition")
    return {"qwen_server_args": qwen_args, "gemma_server_args": gemma_args, "synthetic_score": score}


def check_rq1_contract(config: dict[str, Any]) -> dict[str, Any]:
    _assert(config.get("schema_version") == "CanvasRCARQ1ConfigV5"
            and config.get("protocol_revision") == "rq1_record_key_stage1_v16",
            "direct-RCA RQ1 protocol revision drifted")
    _assert(config["runtime"].get("request_concurrency") == 4,
            "formal RQ1 runner must use case-level request concurrency four")
    partitions = _concurrency_partitions(1, 4, 4)
    _assert(partitions == tuple((1 + worker * 4, 16) for worker in range(4))
            and all(index % 4 == 1 for index, _count in partitions),
            "case-level worker partitions are not disjoint refinements of the registered shard")
    registry = experiment_registry(config)
    _assert(set(registry) == {
        "legacy_q9", "cross_region", "typed_two_stage", "direct_rca", "matched_rca",
        "visual_counterfactual_rca", "ledger_handoff_rca",
    }, "RQ1 experiment registry drifted")
    _assert(registry["matched_rca"].arms == RCA_ARMS, "RCA arms drifted")
    _assert(registry["visual_counterfactual_rca"].arms == ("H_factual", "H_targeted", "H_placebo", "H_neutral"), "counterfactual arms drifted")
    _assert(registry["ledger_handoff_rca"].arms == ("L_txt", "L_vis", "L_hyb"), "handoff arms drifted")
    smoke_plans = config.get("smoke_plans") or {}
    smoke_datasets = {"re2_ob", "aiops2022", "aiops2025"}
    _assert(set(smoke_plans) == set(registry), "every experiment must have exactly one smoke plan")
    smoke_calls: dict[str, int] = {}
    for name, spec in registry.items():
        plan = smoke_plans[name]
        _assert(set(plan) == smoke_datasets, f"{name} smoke does not use the three prescribed datasets")
        _assert(all(plan[dataset] and set(plan[dataset]) <= set(spec.arms) for dataset in smoke_datasets),
                f"{name} smoke contains an invalid or empty arm assignment")
        per_model = sum(
            (1 + len(plan[dataset])) if spec.task == "root_cause_handoff"
            else len(plan[dataset]) * spec.stages
            for dataset in smoke_datasets
        )
        _assert(per_model <= 18, f"{name} smoke exceeds 18 calls for one model")
        smoke_calls[name] = per_model
    client_source = (ROOT / "src/vlmrca/vlm/client.py").read_text()
    supervisor_source = (ROOT / "src/cli/smoke_e2e.py").read_text()
    smoke_source = (ROOT / "RQs/RQ1/scripts/smoke_nibi.sh").read_text()
    _assert("partial_output_dir" in client_source and "timeout_partial" in supervisor_source
            and "--partial-dir" in smoke_source,
            "bounded smoke no longer preserves partial responses at timeout")
    _assert(len(factorial_cells()) == 16 and len(set(factorial_cells())) == 16, "factorial cells are incomplete")
    mapping_a, kinds = numeric_entity_map(["checkout", "node-1", "checkout-abcdef12-abcde"], "INC-ABC")
    mapping_b, _ = numeric_entity_map(["checkout", "node-1", "checkout-abcdef12-abcde"], "INC-XYZ")
    _assert(mapping_a != mapping_b, "case-local IDs do not change by incident")
    _assert(len(mapping_a["checkout"]) == 3 and len(mapping_a["node-1"]) == 4 and len(mapping_a["checkout-abcdef12-abcde"]) == 5, "numeric ID widths drifted")
    qualification_contracts(config)
    private = ROOT / config["data"]["private_roster"]
    roster = json.loads(private.read_text(encoding="utf-8"))
    counts = {name: len(rows) for name, rows in roster["datasets"].items()}
    _assert(counts == {"aegislab": 96, "aiops2022": 100, "aiops2025": 93, "re2_ob": 90, "re2_tt": 90}, "frozen RQ1 roster drifted")
    _assert(sum(counts.values()) == 469, "frozen RQ1 roster must contain 469 eligible cases")
    adapter = config.get("inference_adapter") or {}
    global_inference = VLLMInferenceConfig.load(config["unified"]["vllm"])
    global_common = global_inference.data["common"]
    _assert(
        adapter.get("name") == "context_safe_output_v1"
        and adapter.get("version") == 1
        and adapter.get("max_tokens") == 8192,
        "RQ1 context-safe inference adapter drifted",
    )
    _assert(
        adapter["max_tokens"] <= global_common["max_model_len"] // 2
        and adapter["max_tokens"] <= global_common["max_tokens"],
        "RQ1 adapter must reserve at least half the context for prompt tokens",
    )
    _assert(ledger_image({}).startswith(b"\x89PNG\r\n\x1a\n"), "ledger Unicode board rendering failed")
    _assert(
        opaque_incident_id("same-case") == opaque_incident_id("same-case")
        and opaque_incident_id("same-case") != opaque_incident_id("different-case"),
        "renderer-v12 presentation identity is not deterministic and case-local",
    )
    try:
        audit_visible({"fault_type": "disk"})
    except RQ1Error:
        pass
    else:
        raise AssertionError("explicit fault_type key escaped the public-artifact audit")
    return {"experiments": sorted(registry), "factorial_cells": 16,
            "id_granularities": kinds, "eval_counts": counts,
            "per_model_smoke_calls": smoke_calls}


def _fixture_packets() -> tuple[dict[str, Any], dict[str, Any], bytes]:
    candidates = ["101", "202", "303", "404"]
    facts = [
        _atomic_fact("C", "candidate_set", {"fixed_order": candidates, "count": 4}, entities=candidates),
        _atomic_fact("C", "evidence_schema", {
            "schema_version": "RCAEvidencePacketV1", "opaque_incident_id": "INC-FIXTURE",
            "selection_summary": {"candidate_count": 4, "metric_series_scored": 2,
                                  "metric_series_shown": 2, "metric_ranker": "fixture",
                                  "hot_z_threshold": 10},
        }),
        _atomic_fact("C", "evidence_legends", {
            "entity_ids": "Service names, pod names, and node names are represented by numeric IDs.",
            "directed_edges": "A directed edge caller -> callee means caller invokes callee.",
            "relative_time": "All times are relative; null means missing.",
            "source_comparability": "Trace and metric anomaly scores are not directly comparable.",
        }),
        _atomic_fact("M", "metric_series_64", {"panel_id": "M1", "rank": 1, "service": "101",
            "metric": "latency", "values": [str(i) for i in range(64)], "missing_mask": [False] * 64,
            "baseline": "1.00", "peak": "63", "signed_z": "+9.0"}, entities=("101",), bins=range(64), unit="source_native"),
        _atomic_fact("M", "metric_series_64", {"panel_id": "M2", "rank": 2, "service": "202",
            "metric": "errors", "values": [str(100 + i) for i in range(64)], "missing_mask": [False] * 64,
            "baseline": "100", "peak": "163", "signed_z": "+8.0"}, entities=("202",), bins=range(64), unit="source_native"),
        _atomic_fact("L", "log_summary_entry", {"entry_index": 0, "service": "101", "error_count": 5}, entities=("101",)),
        _atomic_fact("L", "log_summary_entry", {"entry_index": 0, "service": "202", "error_count": 7}, entities=("202",)),
        _atomic_fact("R", "trace_summary_entry", {"entry_index": 0, "service": "101", "p95_during_ms": "12"}, entities=("101",)),
        _atomic_fact("R", "trace_summary_entry", {"entry_index": 0, "service": "202", "p95_during_ms": "18"}, entities=("202",)),
        _atomic_fact("G", "propagation_service", {"service": "101", "onset_rel_min_display": "1m"}, entities=("101",)),
        _atomic_fact("G", "propagation_service", {"service": "202", "onset_rel_min_display": "2m"}, entities=("202",)),
        _atomic_fact("G", "directed_call_edge", {"edge_index": 0, "caller": "101", "callee": "202"}, entities=("101", "202")),
        _atomic_fact("L", "explicit_missingness", {"logs_missing": False}),
        _atomic_fact("R", "explicit_missingness", {"traces_missing": False}),
        _atomic_fact("G", "explicit_missingness", {"propagation_missing": False}),
    ]
    facts = sorted(facts, key=lambda fact: (fact["region"], fact["field"], fact["fact_id"]))
    rca = {"schema_version": "RCAEvidencePacketV1", "opaque_incident_id": "INC-FIXTURE",
           "candidates": candidates, "facts": facts,
           "fact_inventory_hash": stable_hash(facts)}
    qa = build_qa_packet(rca)
    png = compile_controlled_canvas(qa)
    return rca, qa, png


def check_semantic_regressions() -> dict[str, Any]:
    rca, qa, png = _fixture_packets()
    serializer_hashes = {
        name: hashlib.sha256(value.encode("utf-8")).hexdigest()
        for name, value in {
            "common": common_shell(rca), "T": _packet_text(rca), "F": _packet_flat(rca),
        }.items()
    }
    _assert(serializer_hashes == {
        "common": "3f37b0b3fe93355a0f014adb0d001c8e0404eabde3567438fd918bc315904434",
        "T": "f12f1214d16cf8dbe813bb0d027c3d4fd83e7030821b11cec404fd7b53abfaa3",
        "F": "eac9cf2552056cc5120d6b84b4ca46de5a4f37fc49093c055ae12d2591d83e95",
    }, "registered common/SIRCL-ordered T/F serializer bytes drifted")
    text_transport = _packet_text(rca)
    text_region_offsets = [text_transport.index(marker) for marker in (
        "Metric/time evidence", "Trace evidence", "Log evidence", "Directed-topology evidence",
    )]
    _assert(text_region_offsets == sorted(text_region_offsets),
            "T transport is not ordered M -> R -> L -> G")
    flat_regions = [json.loads(line)["region"] for line in _packet_flat(rca).splitlines()]
    _assert(tuple(dict.fromkeys(flat_regions)) == PROMPT_REGION_ORDER,
            "F transport is not ordered M -> R -> L -> G")
    atlas = visual_patch_atlas(png, layout="controlled", font_point_size=15.0)
    weights = [1.0 if patch["region"] == "M" else 0.0 for patch in atlas["patches"]]
    attention = {"image_sha256": atlas["image_sha256"], "grid": atlas["grid"],
                 "weights": weights, "required_regions": ["M"], "attention_source": "synthetic_static_test"}
    attention_report = attention_diagnostics(attention, atlas)
    _assert(attention_report["required_region_attention_mass"] == 1.0
            and attention_report["blank_attention_mass"] >= 0.0,
            "attention-to-renderer atlas diagnostics drifted")
    _assert(render_attention_overlay(png, attention, atlas).startswith(b"\x89PNG\r\n\x1a\n"),
            "attention overlay is not a PNG")
    profile = visual_diagnostic_for_arm("H", "cross_region_reasoning", {"visual_evidence_atlases": {"qa": atlas}})
    _assert(profile["image_count"] == 1 and set(profile["visual_regions"]) == {"M", "L", "R", "G"},
            "existing-arm visual diagnostics drifted")
    t, v, h = (qa_representation_parts(arm, qa, png) for arm in ("T", "V", "H"))
    _assert(h == [*v, *t], "Q&A hybrid is not strict A+B")
    signatures = {
        tuple((part["type"], stable_hash(part["png"] if part["type"] == "image" else str(part["text"])))
              for part in qa_representation_parts(cell, qa, png))
        for cell in factorial_cells()
    }
    _assert(len(signatures) == 16,
            "factorial cells are not distinct")
    rca_h = representation_parts("H", rca, png, png, {}, {})
    rca_t = representation_parts("T", rca, png, png, {}, {})
    rca_v = representation_parts("V", rca, png, png, {}, {})
    pixel_pages = compile_pixel_text_pages(rca)
    rca_p = representation_parts("P", rca, png, png, {}, {}, pixel_pages)
    _assert(rca_h[:-1] == [*rca_v[:-1], *rca_t[:-1]], "RCA hybrid incident fragment is not strict A+B")
    _assert(
        rca_p[-1] == rca_t[-1]
        and len(rca_p[:-1]) == len(pixel_pages)
        and all(part["type"] == "image" for part in rca_p[:-1]),
        "RCA P is not the bounded pixel rendering of T under the common shell",
    )
    _assert(pixel_pages == compile_pixel_text_pages(rca), "pixel-text rendering is not deterministic")
    _assert(
        tuple(line for _region, lines in _packet_text_region_blocks(rca) for line in lines)
        == tuple(_packet_text(rca).splitlines()[1:]),
        "pixel-text source lines are not the exact T-arm natural-language facts",
    )
    _assert(all(fact["field"] in rca_t[-1]["text"] for fact in rca["facts"] if fact["region"] == "C"),
            "one or more common image legends/facts are absent from the shared RCA shell")
    _assert(not any(key in str(rca_t) for key in (
        "observed_counts", "onset_bin", "onset_rel_s", "persistence_bins",
    )), "metric metadata absent from the dashboard escaped into RCA text")
    _assert(all("Evidence structure and fields:" in prompt for prompt in (
        QA_SYSTEM, TYPED_OBSERVE_SYSTEM, TYPED_ANSWER_SYSTEM,
    )), "a Q&A prompt lacks its M/R/L/G field guide")
    _assert(all("RCA method:" not in prompt for prompt in (
        QA_SYSTEM, TYPED_OBSERVE_SYSTEM, TYPED_ANSWER_SYSTEM,
    )), "RCA guidance leaked into a non-RCA prompt")
    _assert("Incident-evidence structure and fields:" in OBSERVE_SYSTEM
            and "RCA method:" in OBSERVE_SYSTEM,
            "RCA Stage 1 lacks its field or diagnosis guide")
    _assert(all(marker in DIAGNOSE_SYSTEM for marker in (
        "Normalized-ledger fields:", "RCA method:", "INITIAL:", "VERIFY:", "REVISE:",
    )), "RCA Stage 2 lacks the SIRCL* VERIFY adapter or ledger guide")
    _assert(all(marker in DIRECT_DIAGNOSE_SYSTEM for marker in (
        "Incident-evidence structure and fields:", "RCA method:", "INITIAL:", "VERIFY:", "REVISE:",
    )) and "Normalized-ledger fields:" not in DIRECT_DIAGNOSE_SYSTEM,
        "direct RCA lacks its evidence/RCA/VERIFY guide or claims a ledger input")

    selector = {"record_key": "M1", "relative_bins": [3]}
    raw = {"selectors": [selector]}
    ledger = normalize_stage1_ledger(raw, rca)
    _assert(len(ledger["observations"]) == 1
            and ledger["observations"][0]["values"] == ["3"]
            and ledger["observations"][0]["attributes"]["metric"] == "latency"
            and ledger["binding_audit"]["unsupported_selectors"] == 0,
            "compact Stage-1 selector did not bind and copy exact public values")
    stage1_schema = response_schema(experiment_registry(load_yaml())["matched_rca"], 1)
    selector_schema = stage1_schema["json_schema"]["schema"]["properties"]["selectors"]
    _assert(selector_schema["maxItems"] == 16
            and selector_schema["items"]["properties"]["relative_bins"]["maxItems"] == 4
            and set(selector_schema["items"]["properties"]) == {"record_key", "relative_bins"}
            and selector_schema["items"]["required"] == ["record_key", "relative_bins"],
            "compact Stage-1 schema permits exhaustive value transcription")
    scrambled = {
        "observations": [{"region": region, "field": region} for region in ("G", "L", "M", "R")],
        "missing_evidence": [{"region": region, "missing": False} for region in ("L", "G", "R", "M")],
    }
    stage2_payload = json.loads(stage2_prompt(
        experiment_registry(load_yaml())["matched_rca"], scrambled, rca["candidates"],
    ))["normalized_evidence_ledger"]
    _assert(tuple(row["region"] for row in stage2_payload["observations"]) == PROMPT_REGION_ORDER
            and tuple(row["region"] for row in stage2_payload["missing_evidence"]) == PROMPT_REGION_ORDER,
            "Stage-2 ledger is not ordered M -> R -> L -> G")
    _assert(len(stage2_payload["observations"]) == len(scrambled["observations"]),
            "Stage-2 ordering dropped an observation")
    invalid = json.loads(json.dumps(raw)); invalid["selectors"][0]["record_key"] = "M99"
    rejected = normalize_stage1_ledger(invalid, rca)
    _assert(not rejected["observations"] and rejected["binding_audit"]["unsupported_selectors"] == 1,
            "nonexistent Stage-1 selector reached Stage 2")

    legacy, reasoning = questions_for_case(qa, "INC-FIXTURE")
    _assert({question.template for question in legacy} == {
        "metric_exact_lookup", "log_exact_lookup", "trace_exact_lookup", "earliest_onset",
        "longest_persistence", "directed_edge", "multi_hop_path",
        "entity_modality_alignment", "metric_missingness",
    }, "Legacy-Q9 semantics drifted")
    _assert(all("owning panel" not in question.text for question in reasoning[1:]),
            "cross-region questions regressed to panel-owner lookup")
    observed_templates = {1: set(), 2: set(), 3: set()}
    for index in range(2048):
        _legacy, sampled = questions_for_case(qa, f"INC-TEMPLATE-{index}")
        for question in sampled:
            observed_templates[question.level].add(question.template)
    _assert(observed_templates == {
        1: {"M_direct_bin", "L_direct_bin", "R_direct_bin", "G_direct_neighbors"},
        2: {"M_L_link", "M_R_link", "M_G_link", "L_R_link", "L_G_link", "R_G_link"},
        3: {"M_L_R_chain", "M_G_L_chain", "M_R_G_chain", "L_R_G_chain"},
    }, f"14-template registry is not fully reachable: {observed_templates}")
    response = {"answers": [{"query_id": q.query_id, "answer": {"steps": [
        {"step": index, "region": region, "values": list(q.answer_steps[index - 1])}
        for index, region in enumerate(q.regions, 1)]}} for q in reasoning]}
    validate_qa_response(response, [q.public() for q in reasoning])
    _assert(score_reasoning(response, [q.private() for q in reasoning])["complete_chain_accuracy"] == 1.0,
            "known-correct nested Q&A response did not score one")
    def selector(region: str) -> dict[str, Any]:
        row = qa["regions"][region][0]
        fields = {"M": "bins", "L": "events", "R": "spans"}
        return {
            "entity_id": (str(row["caller"]) if region == "G" else
                          str(row["entity"]) if row.get("entity") is not None else None),
            "edge_id": None if region != "R" or row.get("edge_id") is None else str(row["edge_id"]),
            "panel_id": str(row["panel_id"]) if region == "M" else None,
            "row_index": int(row["entry_index"]) if region in {"L", "R"} else None,
            "field": fields.get(region), "relative_bins": [0] if region != "G" else [],
        }
    typed = {q.query_id: {f"s{index}": selector(region)
                          for index, region in enumerate(q.regions, 1)} for q in reasoning}
    normalized_typed = normalize_typed_qa_ledger(
        typed, [q.public() for q in reasoning], qa,
    )
    _assert(normalized_typed["binding_audit"]["unsupported_steps"] == 0,
            "host-bound typed selector fixture contains unsupported steps")
    graph_entities = {str(value) for row in qa["regions"]["G"]
                      for value in (row["caller"], row["callee"])}
    isolated = next((str(row["entity"]) for row in qa["regions"]["M"]
                     if str(row["entity"]) not in graph_entities), None)
    if isolated is not None:
        absence = normalize_typed_qa_ledger(
            {"q1": {"s1": {"entity_id": isolated, "edge_id": None,
                              "panel_id": None, "row_index": None, "field": None,
                              "relative_bins": []}}},
            [{"query_id": "q1", "region_path": ["G"], "template": "G_direct_neighbors"}], qa,
        )
        record = absence["ledgers"][0]["observations"][0]["records"][0]
        _assert(record["record_kind"] == "topology_no_incident_edge",
                "verified zero-edge topology selection was treated as unsupported")
    selector_schema = response_schema(
        experiment_registry(load_yaml())["typed_two_stage"], 1,
        [q.public() for q in reasoning],
    )["json_schema"]["schema"]["properties"]
    for question in reasoning:
        for index, region in enumerate(question.regions, 1):
            properties = selector_schema[question.query_id]["properties"][f"s{index}"]["properties"]
            required_edge = ((region == "G" and TEMPLATE_VALUE_KINDS[question.template][index - 1]
                              in {"endpoint_roles", "other_endpoint_id"})
                             or (region == "R" and question.template == "R_G_link"))
            _assert(properties["edge_id"].get("type") == ("string" if required_edge else "null"),
                    "typed selector edge requirement drifted")
            _assert(properties["entity_id"].get("type") == ("null" if required_edge else "string"),
                    "typed selector entity requirement drifted")
            if required_edge:
                _assert(properties["edge_id"].get("pattern") == "^E[0-9]{2}$",
                        "typed edge ID grammar is unconstrained")
            else:
                _assert(properties["entity_id"].get("pattern") == "^[0-9]{3,5}$",
                        "typed entity ID grammar is unconstrained")
    validate_diagnosis({"services": ["101"], "reason": "evidence", "confidence": "high"}, rca["candidates"])
    registry = experiment_registry(load_yaml())
    diagnosis_schema = response_schema(registry["matched_rca"], 2)
    _assert("uniqueItems" not in str(diagnosis_schema) and "maxLength" not in str(diagnosis_schema),
            "Gemma diagnosis schema still contains xgrammar-unsupported constraints")
    try:
        validate_diagnosis({"services": ["101", "101"], "reason": "", "confidence": "high"}, rca["candidates"])
    except RQ1Error:
        pass
    else:
        raise AssertionError("post-model diagnosis validator accepted duplicate/empty output")

    large_ledger = {"observations": [{"observation_id": f"O{i:02d}", "values": ["x" * 500]} for i in range(32)]}
    pages = ledger_images(large_ledger)
    _assert(1 < len(pages) <= 8 and all(page.startswith(b"\x89PNG") for page in pages),
            "lossless visual ledger pagination failed")
    _assert(len(handoff_parts("L_vis", large_ledger, rca["candidates"])) == len(pages) + 1,
            "visual handoff dropped a ledger page")
    _assert(len(handoff_parts("L_hyb", large_ledger, rca["candidates"])) == len(pages) + 2,
            "hybrid handoff is not images plus exact text")
    registry = experiment_registry(load_yaml())
    public = {
        "rca_packet": rca,
        "legacy_questions": [question.public() for question in legacy],
        "reasoning_questions": [question.public() for question in reasoning],
    }
    compiled_arms: dict[str, int] = {}
    for name in ("legacy_q9", "cross_region", "typed_two_stage"):
        spec = registry[name]
        for arm in spec.arms:
            _assert(bool(qa_representation_parts(arm, qa, png)),
                    f"{name}/{arm} compiled no prompt parts")
        response_schema(
            spec, 1,
            public["reasoning_questions"] if name == "typed_two_stage" else (),
        )
        if spec.stages == 2:
            response_schema(spec, 2)
        compiled_arms[name] = len(spec.arms)
    variants = {"targeted": png, "placebo": png, "neutral": png}
    for name in ("direct_rca", "matched_rca", "visual_counterfactual_rca"):
        spec = registry[name]
        for arm in spec.arms:
            _assert(
                bool(representation_parts(arm, rca, png, png, {}, variants)),
                f"{name}/{arm} compiled no prompt parts",
            )
        response_schema(spec, 1)
        if spec.stages == 2:
            response_schema(spec, 2)
        compiled_arms[name] = len(spec.arms)
    direct, matched = registry["direct_rca"], registry["matched_rca"]
    _assert(direct.arms == matched.arms == RCA_ARMS and direct.stages == 1 and matched.stages == 2,
            "one/two-stage RCA representation pairing drifted")
    _assert(stage1_prompt(direct, public).startswith("Directly rank")
            and response_schema(direct, 1)["json_schema"]["name"] == "diagnosis",
            "direct RCA does not request and constrain a Stage-1 diagnosis")
    base = {"model": "fixture", "opaque_incident_id": "INC-FIXTURE", "arm": "T",
            "analysis_dataset": "aegislab", "status": "completed",
            "score": {key: 0.25 for key in ("mrr", "ac@1", "ac@3", "ac@5", "avg@3", "avg@5")}}
    comparison = analyze_stage_pair(
        [{**base, "stages": [{"total_tokens": 100, "wall_time_s": 1}]}],
        [{**base, "score": {key: 0.75 for key in base["score"]},
          "stages": [{"total_tokens": 80, "wall_time_s": 1}, {"total_tokens": 70, "wall_time_s": 2}]}],
        load_yaml(),
    )
    _assert(comparison["by_model"]["fixture"]["by_arm"]["T"]
            ["performance_two_minus_one"]["mrr"]["delta"] == 0.5,
            "one/two-stage paired RCA analysis drifted")
    handoff_spec = registry["ledger_handoff_rca"]
    for arm in handoff_spec.arms:
        _assert(bool(handoff_parts(arm, large_ledger, rca["candidates"])),
                f"ledger_handoff_rca/{arm} compiled no prompt parts")
    response_schema(handoff_spec, 1)
    response_schema(handoff_spec, 2)
    compiled_arms["ledger_handoff_rca"] = len(handoff_spec.arms)
    orders = {balanced_arm_order(RCA_ARMS, f"INC-{i}", "matched_rca") for i in range(64)}
    _assert(len(orders) >= len(RCA_ARMS), "arm order is not case-balanced")
    selection = _counterfactual_pairs({"candidates": rca["candidates"], "metric_series": [
        {"service": entity, "signed_z": score} for entity, score in zip(rca["candidates"], (10, 7, 2, 1), strict=True)],
        "propagation": {"services": [{"service": value, "onset_rel_s": index} for index, value in enumerate(rca["candidates"])],
                        "directed_call_edges": [{"caller": "101", "callee": "202"}, {"caller": "202", "callee": "303"}]}})
    _assert(selection["eligible"] and selection["targeted"] != selection["placebo"],
            "counterfactual selector did not separate targeted and placebo pairs")
    _assert(all(value in set(rca["candidates"]) for value in [*selection["targeted"], *selection["placebo"]]),
            "counterfactual selector escaped the RCA candidate set")
    _assert(_rbo_at_k(["1", "2"], ["1", "2"]) == 1.0
            and _rbo_at_k(["1", "2"], ["3", "4"]) == 0.0,
            "rank-biased-overlap implementation drifted")
    _assert(all(len(value) > 180 for value in (OBSERVE_SYSTEM, DIAGNOSE_SYSTEM, DIRECT_DIAGNOSE_SYSTEM, QA_SYSTEM, TYPED_OBSERVE_SYSTEM, TYPED_ANSWER_SYSTEM)),
            "a load-bearing prompt was compressed to a generic instruction")
    return {"legacy_questions": len(legacy), "reasoning_questions": len(reasoning),
            "reachable_reasoning_templates": {str(level): sorted(values) for level, values in observed_templates.items()},
            "ledger_pages": len(pages), "arm_orders": len(orders),
            "compiled_arms_by_experiment": compiled_arms,
            "compiled_arms_total": sum(compiled_arms.values())}


def run_static_checks(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    """Run static/CPU checks only; this function cannot invoke a model."""

    config = load_yaml(config_path)
    checks: list[tuple[str, Callable[[], Any]]] = [
        ("global_layout", check_global_layout),
        ("rq_layouts", check_rq_layouts),
        ("python_syntax", check_python_syntax),
        ("unified_contracts", lambda: check_unified_contracts(config)),
        ("rq1_contract", lambda: check_rq1_contract(config)),
        ("semantic_regressions", check_semantic_regressions),
    ]
    results: dict[str, Any] = {}
    for name, check in checks:
        results[name] = check()
    return {"passed": True, "model_calls": 0, "checks": results}


def run_live_logic_diagnostic(model: str, output: Path, config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    """Exercise all six paths for development; this is not a registered smoke."""

    from unified_scripts import canonical_json
    from unified_scripts.vllm_inference import VLLMInferenceConfig
    from vlmrca.vlm.client import text_part

    from .exps import (
        RCA_ARMS, handoff_parts, is_rca_task, normalize_stage1_ledger,
        normalize_typed_qa_ledger, qa_representation_parts, representation_parts,
        prepare_case, response_schema, stage1_prompt, stage2_prompt,
    )
    from .main import _model_call, _stage1_failure
    from .utils import parse_json_object, stable_hash, write_json

    config = load_yaml(config_path)
    smoke_profile = os.environ.get("CANVASRCA_RQ1_SMOKE_PROFILE", "all_six")
    if smoke_profile not in {"all_six", "final_patch"}:
        raise RQ1Error(f"unknown local smoke profile {smoke_profile!r}")
    registry = experiment_registry(config)
    runtime = VLLMInferenceConfig.load(config["unified"]["vllm"])
    adapter = {**dict(config["inference_adapter"])}
    adapter["adapter_sha256"] = stable_hash(adapter)
    call_options = {
        "inference_adapter": adapter,
        "context_limit": int(runtime.model(model)["max_model_len"]),
        "attention_output_root": output / "attention",
    }
    cases = {
        "aiops2022": prepare_case("aiops2022", "aiops2022_2022-03-20-cloudbed1_000", config),
        "aiops2025": prepare_case("aiops2025", "aiops2025_0419ba04-373", config),
        "re2_ob": prepare_case("re2_ob", "re2_ob_checkoutservice_cpu_1", config),
    }
    output.mkdir(parents=True, exist_ok=True)
    started, calls, records = time.time(), 0, []

    def invoke(label: str, system: str, parts: list[dict[str, Any]], schema: dict[str, Any]) -> tuple[dict[str, Any], str]:
        nonlocal calls
        if calls >= 18:
            raise RQ1Error("live logic diagnostic exceeded one model's 18-call cap")
        calls += 1
        record, raw = _model_call(model=model, system=system, parts=parts, schema=schema, **call_options)
        row = {"label": label, "call_number": calls, "call": record, "raw_response": raw}
        records.append(row)
        write_json(output / f"{calls:02d}_{label}.json", row)
        (output / f"{calls:02d}_{label}.md").write_text(
            f"# {label}\n\n```json\n{json.dumps(record['prompt'], indent=2, sort_keys=True)}\n```\n\n## Raw response\n\n```json\n{raw}\n```\n",
            encoding="utf-8",
        )
        return record, raw

    def safe_parse(raw: str) -> tuple[dict[str, Any], bool]:
        try:
            return parse_json_object(raw), True
        except Exception as error:
            return _stage1_failure(raw, error), False

    # One-stage paths: one direct packet and one cross-region packet.
    for experiment, dataset, arm in (("legacy_q9", "aiops2022", "T"), ("cross_region", "aiops2025", "H")):
        spec, prepared = registry[experiment], cases[dataset]
        parts = qa_representation_parts(arm, prepared.public["qa_packet"], prepared.qa_png)
        parts.append(text_part(stage1_prompt(spec, prepared.public)))
        call, raw = invoke(f"{experiment}_stage1", QA_SYSTEM, parts, response_schema(spec, 1))
        payload, parsed = safe_parse(raw)
        questions = prepared.public["legacy_questions"] if experiment == "legacy_q9" else prepared.public["reasoning_questions"]
        try:
            validate_qa_response(payload, questions)
        except Exception:
            parsed = False
        call["diagnostic_parse"] = parsed

    # Typed Q&A path.
    spec, prepared = registry["typed_two_stage"], cases["re2_ob"]
    parts = qa_representation_parts("H", prepared.public["qa_packet"], prepared.qa_png)
    parts.append(text_part(stage1_prompt(spec, prepared.public)))
    call1, raw1 = invoke(
        "typed_two_stage_stage1", TYPED_OBSERVE_SYSTEM, parts,
        response_schema(spec, 1, prepared.public["reasoning_questions"]),
    )
    stage1, parsed1 = safe_parse(raw1)
    try:
        stage1 = normalize_typed_qa_ledger(
            stage1, prepared.public["reasoning_questions"], prepared.public["qa_packet"],
        )
    except Exception as error:
        stage1, parsed1 = _stage1_failure(raw1, error), False
    call1["diagnostic_parse"] = parsed1
    call2, raw2 = invoke("typed_two_stage_stage2", TYPED_ANSWER_SYSTEM,
                         [text_part(stage2_prompt(spec, stage1, prepared.public["rca_packet"]["candidates"],
                                                  prepared.public["reasoning_questions"]))],
                         response_schema(spec, 2))
    payload2, parsed2 = safe_parse(raw2)
    try:
        validate_qa_response(payload2, prepared.public["reasoning_questions"], typed=True)
    except Exception:
        parsed2 = False
    call2["diagnostic_parse"] = parsed2

    def rca_pair(experiment: str, prepared: Any, arm: str) -> None:
        spec = registry[experiment]
        parts = representation_parts(arm, prepared.public["rca_packet"], prepared.full_png,
                                     prepared.routed_png, config, prepared.variant_pngs)
        parts.append(text_part(stage1_prompt(spec, prepared.public)))
        call1, raw1 = invoke(f"{experiment}_stage1", OBSERVE_SYSTEM, parts, response_schema(spec, 1))
        stage1, parsed1 = safe_parse(raw1)
        try:
            stage1 = normalize_stage1_ledger(stage1, prepared.public["rca_packet"])
        except Exception as error:
            stage1, parsed1 = _stage1_failure(raw1, error), False
        call1["diagnostic_parse"] = parsed1
        call2, raw2 = invoke(f"{experiment}_stage2", DIAGNOSE_SYSTEM,
                             [text_part(stage2_prompt(spec, stage1, prepared.public["rca_packet"]["candidates"]))],
                             response_schema(spec, 2))
        final, parsed2 = safe_parse(raw2)
        try:
            validate_diagnosis(final, prepared.public["rca_packet"]["candidates"])
        except Exception:
            parsed2 = False
        call2["diagnostic_parse"] = parsed2

    rca_pair("matched_rca", cases["aiops2022"], "R")
    if not cases["aiops2025"].private["counterfactual_pairs"]["eligible"]:
        raise RQ1Error("registered local counterfactual smoke case is ineligible")
    if smoke_profile == "all_six":
        rca_pair("visual_counterfactual_rca", cases["aiops2025"], "H_targeted")

    # Ledger handoff shares one routed observer and tests the visual+text handoff.
    if smoke_profile == "all_six":
        spec, prepared = registry["ledger_handoff_rca"], cases["re2_ob"]
        observer = representation_parts("R", prepared.public["rca_packet"], prepared.full_png,
                                        prepared.routed_png, config, prepared.variant_pngs)
        observer.append(text_part(stage1_prompt(spec, prepared.public)))
        call1, raw1 = invoke("ledger_handoff_rca_stage1", OBSERVE_SYSTEM, observer, response_schema(spec, 1))
        stage1, parsed1 = safe_parse(raw1)
        try:
            stage1 = normalize_stage1_ledger(stage1, prepared.public["rca_packet"])
        except Exception as error:
            stage1, parsed1 = _stage1_failure(raw1, error), False
        call1["diagnostic_parse"] = parsed1
        call2, raw2 = invoke("ledger_handoff_rca_stage2", DIAGNOSE_SYSTEM,
                             handoff_parts("L_hyb", stage1, prepared.public["rca_packet"]["candidates"]),
                             response_schema(spec, 2))
        final, parsed2 = safe_parse(raw2)
        try:
            validate_diagnosis(final, prepared.public["rca_packet"]["candidates"])
        except Exception:
            parsed2 = False
        call2["diagnostic_parse"] = parsed2

    for row in records:
        write_json(output / f"{int(row['call_number']):02d}_{row['label']}.json", row)
    visual_profiles = {
        "legacy_q9_T": visual_diagnostic_for_arm("T", registry["legacy_q9"].task, cases["aiops2022"].public),
        "cross_region_H": visual_diagnostic_for_arm("H", registry["cross_region"].task, cases["aiops2025"].public),
        "typed_two_stage_H": visual_diagnostic_for_arm("H", registry["typed_two_stage"].task, cases["re2_ob"].public),
        "matched_rca_R": visual_diagnostic_for_arm("R", registry["matched_rca"].task, cases["aiops2022"].public),
        "counterfactual_targeted": visual_diagnostic_for_arm(
            "H_targeted", registry["visual_counterfactual_rca"].task, cases["aiops2025"].public
        ),
        "ledger_handoff_L_hyb": visual_diagnostic_for_arm(
            "L_hyb", registry["ledger_handoff_rca"].task, cases["re2_ob"].public
        ),
    }
    report = {
        "schema_version": "RQ1LocalLiveLogicDiagnosticV2", "status": "diagnostic_completed",
        "scientific_status": "diagnostic_only_not_scientific_evidence", "model": model,
        "smoke_profile": smoke_profile,
        "model_calls": calls, "call_cap": 18, "wall_time_s": time.time() - started,
        "experiments": sorted(registry), "records": len(records),
        "parsed_records": sum(bool(row["call"].get("diagnostic_parse")) for row in records),
        "effective_max_num_seqs": int(runtime.model(model)["max_num_seqs"]),
        "global_max_tokens": int(runtime.model(model)["max_tokens"]),
        "rq1_requested_max_tokens": int(adapter["max_tokens"]),
        "visual_diagnostics": visual_profiles,
        "raw_and_conversation_artifacts_inspection_required": True,
    }
    report["report_sha256"] = stable_hash(report)
    write_json(output / "summary.json", report)
    return report


if __name__ == "__main__":
    print(json.dumps(run_static_checks(), indent=2, sort_keys=True))
