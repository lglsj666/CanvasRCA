"""CPU-only structural and contract checks for the refactored RQ1 code."""

from __future__ import annotations

import ast
import hashlib
import io
import json
import math
import os
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

from unified_scripts import stable_hash
from unified_scripts.rca_scorer import RCAScorer, RCAScorerConfig
from unified_scripts.vllm_inference import VLLMInferenceConfig
from PIL import Image, ImageChops
from RQs.RQ1.src.renderer.dashboard import opaque_incident_id

from .exps import (
    DIAGNOSE_SYSTEM, DIRECT_DIAGNOSE_SYSTEM, OBSERVE_SYSTEM, PROMPT_REGION_ORDER,
    QA_SYSTEM, RCA_ARMS,
    TEMPLATE_VALUE_KINDS,
    TYPED_ANSWER_SYSTEM, TYPED_OBSERVE_SYSTEM,
    _atomic_fact, _counterfactual_pairs, balanced_arm_order, build_qa_packet,
    compile_pixel_text_pages, experiment_registry, factorial_cells, handoff_parts,
    ledger_image, ledger_images, normalize_stage1_ledger, normalize_typed_qa_ledger,
    qa_representation_parts, questions_for_case, representation_parts, response_schema,
    score_reasoning, validate_diagnosis, validate_qa_response, attention_diagnostics,
    render_attention_overlay, visual_diagnostic_for_arm, visual_patch_atlas,
    common_shell, _packet_flat, _packet_text, _packet_text_region_blocks, _routed_image,
    stage1_prompt, stage2_prompt,
)
from .main import _concurrency_partitions, _load_roster, _request_contract
from .gates import (
    _rbo_at_k, analyze_records, analyze_stage_pair, qualification_contracts,
    verify_result_root,
)
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
        runtime.data.get("protocol_version") == "vllm-inference-v6-nibi-compact-structured-json",
        "global vLLM compact-structured-JSON protocol drifted",
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
    expected_structured = '{"backend":"xgrammar","disable_any_whitespace":true}'
    for tag, args in (("Qwen", qwen_args), ("Gemma", gemma_args)):
        _assert("--structured-outputs-config" in args,
                f"{tag} structured-output server configuration disappeared")
        value = args[args.index("--structured-outputs-config") + 1]
        _assert(value == expected_structured,
                f"{tag} permits unbounded schema-legal JSON whitespace")
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
    _assert(config.get("schema_version") == "CanvasRCARQ1ConfigV10"
            and config.get("protocol_revision") == "rq1_renderer_qa_v22",
            "RQ1 renderer-Q&A protocol revision drifted")
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
    _assert(registry["legacy_q9"].arms == ("T", "P", "V", "H")
            and len(registry["cross_region"].arms) == len(registry["typed_two_stage"].arms) == 19,
            "formal Q&A T/P/V/H or factorial registry drifted")
    _assert(registry["visual_counterfactual_rca"].arms == ("H_factual", "H_targeted", "H_placebo", "H_neutral"), "counterfactual arms drifted")
    _assert(registry["ledger_handoff_rca"].arms == ("L_txt", "L_vis", "L_hyb"), "handoff arms drifted")
    smoke_plans = config.get("smoke_plans") or {}
    smoke_datasets = {"aegislab", "aiops2022", "aiops2025"}
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
    smoke_submit_source = (ROOT / "RQs/RQ1/scripts/submit_smoke_nibi.sh").read_text()
    smoke_batch_source = (ROOT / "RQs/RQ1/scripts/submit_all_smokes_nibi.sh").read_text()
    prepare_source = (ROOT / "RQs/RQ1/scripts/prepare_nibi.sh").read_text()
    array_source = (ROOT / "RQs/RQ1/scripts/array_nibi.sh").read_text()
    _assert("partial_output_dir" in client_source and "timeout_partial" in supervisor_source
            and "--partial-dir" in smoke_source,
            "bounded smoke no longer preserves partial responses at timeout")
    _assert(
        'MODEL="${CANVASRCA_MODEL:?' in smoke_source
        and 'run_model_phase "$MODEL"' in smoke_source
        and "MODELS=(" not in smoke_source
        and smoke_submit_source.count("sbatch --parsable") == 2
        and 'CANVASRCA_MODEL=qwen3.6-27b' in smoke_submit_source
        and 'CANVASRCA_MODEL=gemma-4-26b-a4b' in smoke_submit_source
        and '--dependency="afterok:$qwen_job"' in smoke_submit_source,
        "two-job sequential one-model smoke launcher drifted",
    )
    _assert(
        'dependency="$(IFS=:; echo "${qwen_jobs[*]}")"' in smoke_batch_source
        and '--dependency="afterok:${dependency}"' in smoke_batch_source
        and smoke_batch_source.count("RQs/RQ1/scripts/smoke_nibi.sh") == 2,
        "batch smoke launcher can overlap Qwen and Gemma experiment phases",
    )
    _assert("#SBATCH --time=00:30:00" in prepare_source,
            "preparation template must request exactly 30 minutes")
    prepare_block = array_source.split("  prepare)", 1)[1].split("  submit)", 1)[0]
    _assert(
        "SLURM_ARRAY_TASK_ID" not in prepare_source
        and "--array" not in prepare_block
        and "--output-shard-count" in prepare_source
        and "ProcessPoolExecutor" in (ROOT / "RQs/RQ1/src/main.py").read_text(),
        "full-roster non-array preparation launcher drifted",
    )
    submit_source = (ROOT / "RQs/RQ1/scripts/submit_nibi.sh").read_text()
    smoke_payload_source = (ROOT / "RQs/RQ1/scripts/smoke_payload.sh").read_text()
    _assert(
        'PREPARED_ID="${CANVASRCA_PREPARED_EXPERIMENT_ID:-$EXPERIMENT_ID}"' in smoke_source
        and '"$PREPARED_ID"' in smoke_source
        and 'mkdir -p "$RESULT_ROOT"' in smoke_source
        and '--prepared-experiment-id "$PREPARED_ID"' in smoke_source
        and '--prepared-experiment-id "$PREPARED_ID"' in smoke_payload_source
        and 'PREPARED_ID="${PREPARED_BASE_ID}__${SHARD_TAG}"' in submit_source
        and '--prepared-experiment-id "$PREPARED_ID"' in submit_source
        and '--shard-index "$SHARD_INDEX"' in submit_source
        and '--shard-count "$SHARD_COUNT"' in submit_source,
        "GPU launchers do not consume the exact shared/sharded preparation authority",
    )
    _assert("prepared_paths" in verify_result_root.__annotations__,
            "verifier cannot follow the shared smoke preparation authority")
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
    smoke_roster = _load_roster(
        ROOT / "RQs/RQ1/configs/rosters/rq1_nibi_smoke_private_v1.json", config,
    )
    _assert(
        {row["dataset"] for row in smoke_roster} == {"aegislab", "aiops2022", "aiops2025"}
        and all(row["opaque_incident_id"].startswith("INC-") for row in smoke_roster),
        "registered smoke roster or frozen opaque linkage drifted",
    )
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
    audit_visible({"entity": "checkoutservice2"}, ("checkoutservice",))
    try:
        audit_visible({"entity": "checkoutservice"}, ("checkoutservice",))
    except RQ1Error:
        pass
    else:
        raise AssertionError("leakage audit missed an exact private identifier")
    audit_visible({"entity": "acheckoutservice"}, ("checkoutservice",))
    audit_visible({"entity": "checkoutservice9"}, ("checkoutservice",))
    for visible in ("checkoutservice/pod", "[checkoutservice]", "écheckoutserviceé"):
        try:
            audit_visible({"entity": visible}, ("checkoutservice",))
        except RQ1Error:
            pass
        else:
            raise AssertionError("leakage audit changed its ASCII boundary semantics")
    leakage_started = time.perf_counter()
    audit_visible({"evidence": "x" * 1_000_000}, (f"private-marker-{index}" for index in range(1000)))
    _assert(time.perf_counter() - leakage_started < 5.0,
            "literal leakage audit regressed to per-marker pathological runtime")
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
    metric_panels = []
    for index, service in enumerate(("101", "202"), 1):
        metric_panels.append({
            "kind": "metric", "panel_id": f"M{index}", "rendered_metric": "latency" if index == 1 else "errors",
            "printed_summary": {"baseline": "1.00" if index == 1 else "100",
                                "peak": "63" if index == 1 else "163",
                                "signed_z": "peak +9.0z" if index == 1 else "peak +8.0z"},
            "display_curve_contract": {"schema_version": "RendererV12MetricDisplayV1",
                "plot_width_px": 120, "plot_height_px": 80,
                "points_64": [{"x_px_from_left": i, "y_px_from_top": 64 - i} for i in range(64)],
                "y_tick_labels": [{"y_px_from_top": 40, "label": "1"}],
                "observed_bins_have_markers": True, "missing_bin_marker": None,
                "fault_band_x_px_from_left": [30, 40]},
        })
    metric_panels.append({"kind": "propagation", "rows": [
        {"service": "101", "onset_display": "1m", "severity_display": "9", "source_display": "M"},
        {"service": "202", "onset_display": "2m", "severity_display": "8", "source_display": "M"},
    ]})
    qa = build_qa_packet(rca, {"panels": metric_panels})
    png = compile_pixel_text_pages(qa)[0]
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
        "T": "46f1d23ce62b6098122f128ec9045945edf50ef6834f1be0c5253f9cc4748357",
        "F": "5dc312b6772203958cc55acd9f0a74de773fcddd2f3022bc4a1555e5d9b9978b",
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
    atlas = visual_patch_atlas(png, layout="dashboard", font_point_size=15.0)
    weights = [1.0 if patch["region"] == "M" else 0.0 for patch in atlas["patches"]]
    attention = {"image_sha256": atlas["image_sha256"], "grid": atlas["grid"],
                 "weights": weights, "required_regions": ["M"], "attention_source": "synthetic_static_test"}
    attention_report = attention_diagnostics(attention, atlas)
    _assert(abs(attention_report["required_region_attention_mass"] - 1.0) < 1e-9
            and attention_report["blank_attention_mass"] >= 0.0,
            "attention-to-renderer atlas diagnostics drifted")
    _assert(render_attention_overlay(png, attention, atlas).startswith(b"\x89PNG\r\n\x1a\n"),
            "attention overlay is not a PNG")
    source_image = Image.new("RGB", (1000, 1000), "#DDEEFF")
    source_stream = io.BytesIO(); source_image.save(source_stream, format="PNG")
    routed = Image.open(io.BytesIO(_routed_image(
        source_stream.getvalue(),
        {"panels": [{"kind": kind} for kind in (
            "metric", "propagation", "logs", "traces", "direct_identity_edge_key",
        )]},
        SimpleNamespace(long_side_px=1000, canvas_aspect=.76),
    ))).convert("RGB")
    _assert(
        ImageChops.difference(source_image.crop((0, 0, 746, 760)), routed.crop((0, 0, 746, 760))).getbbox() is None
        and ImageChops.difference(source_image.crop((746, 0, 1000, 424)), routed.crop((746, 0, 1000, 424))).getbbox() is None
        and ImageChops.difference(source_image.crop((0, 760, 1000, 1000)), routed.crop((0, 760, 1000, 1000))).getbbox() is None,
        "routed mask changed metric, propagation, or edge-key pixels",
    )
    pixel_pages = compile_pixel_text_pages(qa)
    region_pngs = {region: (png,) for region in PROMPT_REGION_ORDER}
    qa_atlases = {region: [visual_patch_atlas(png, layout=f"crop_{region}")]
                  for region in PROMPT_REGION_ORDER}
    profile = visual_diagnostic_for_arm("H", "cross_region_reasoning", {
        "visual_evidence_atlases": {"full": atlas, "qa_full": atlas,
                                     "pixel_text": [atlas], "qa_regions": qa_atlases}})
    _assert(profile["image_count"] == 1 and set(profile["visual_regions"]) == {"M", "L", "R", "G"},
            "existing-arm visual diagnostics drifted")
    t, p, v, h = (qa_representation_parts(arm, qa, png, pixel_pages, region_pngs)
                  for arm in ("T", "P", "V", "H"))
    _assert(h == [*v, *t], "Q&A hybrid is not strict A+B")
    _assert(v == [{"type": "image", "png": png}] and p == [
        {"type": "image", "png": page} for page in pixel_pages],
        "Q&A V/P do not use the real-image/exact-text-pixel sources")
    _assert(qa["evidence_text_sha256"] == stable_hash(t[0]["text"]),
            "P_QA source text is not byte-identical to T_QA")
    _assert(t[0]["text"] == "\n".join(
        line for _region, lines in _packet_text_region_blocks(qa) for line in lines
    ) + "\n", "T_QA contains text outside the exact P_QA raster source")
    signatures = {
        tuple((part["type"], stable_hash(part["png"] if part["type"] == "image" else str(part["text"])))
              for part in qa_representation_parts(cell, qa, png, pixel_pages, region_pngs))
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
        "metric_panel_entity", "metric_printed_peak", "window_duration", "log_table_cell",
        "trace_table_cell", "directed_edge", "propagation_readout",
        "metric_printed_baseline", "log_display_mode",
    }, "Legacy-Q9 semantics drifted")
    _assert(all("bin " not in question.text for question in [*legacy, *reasoning]),
            "Q&A targets an exact curve bin that is not explicitly printed")
    _assert(all("values" not in fact["payload"] and "missing_mask" not in fact["payload"]
                for fact in qa["facts"] if fact["field"] == "metric_series_64"),
            "Q&A text still exposes raw metric values absent from dashboard pixels")
    _assert(all(
        point is None or all(math.isfinite(float(value)) for value in point.values())
        for fact in qa["facts"] if fact["field"] == "metric_series_64"
        for point in fact["payload"]["display_curve"]["points_64"]
    ), "Q&A display contract contains a non-finite plot coordinate")
    no_edge_rca = {**rca, "facts": [fact for fact in rca["facts"]
                                     if fact["field"] != "directed_call_edge"]}
    no_edge_qa = {**qa, "facts": [fact for fact in qa["facts"] if fact["field"] != "directed_call_edge"]}
    no_edge_qa["facts"].append(_atomic_fact("G", "directed_edge_key_status", {"status": "none"}))
    no_edge_qa["facts"] = sorted(no_edge_qa["facts"], key=lambda fact: (
        PROMPT_REGION_ORDER.index(fact["region"]), fact["field"], fact["fact_id"]
    ))
    no_edge_legacy, no_edge_reasoning = questions_for_case(no_edge_qa, "INC-NO-EDGE")
    _assert(no_edge_legacy[5].answer_steps == (("none",),)
            and [question.level for question in no_edge_reasoning] == [1, 2, 3]
            and any(fact["field"] == "directed_edge_key_status" for fact in no_edge_qa["facts"]),
            "explicitly empty renderer edge key still makes Q&A preparation fail")
    observed_templates = {1: set(), 2: set(), 3: set()}
    for index in range(2048):
        _legacy, sampled = questions_for_case(qa, f"INC-TEMPLATE-{index}")
        for question in sampled:
            observed_templates[question.level].add(question.template)
    _assert(observed_templates == {
        1: {"M_direct_read", "L_direct_read", "R_direct_read", "G_direct_read"},
        2: {"M_L_link", "M_R_link", "M_G_link", "L_R_link", "L_G_link", "R_G_link"},
        3: {"M_locator_chain", "R_locator_chain", "L_locator_chain", "G_locator_chain"},
    }, f"14-template registry is not fully reachable: {observed_templates}")
    for index in range(256):
        _legacy, sampled = questions_for_case(qa, f"INC-TOPOLOGY-{index}")
        for question in sampled:
            if question.template in {"M_G_link", "L_G_link", "R_G_link"}:
                _assert("caller->callee edge key" in question.text
                        and all(value.startswith(("upstream=", "downstream="))
                                for value in question.answer_steps[1]),
                        "M/L/R→G no longer performs directed topology traversal")
    _assert(all(len(q.regions) == 3 and len(set(q.regions)) == 3
                for q in reasoning if q.level == 3),
            "Level-3 dependency chain does not traverse three distinct regions")

    def sparse_questions(*, paired_lr: bool) -> list[Any]:
        packet = json.loads(json.dumps(qa))
        region_entities = {"M": "101", "L": "202", "R": "202" if paired_lr else "303", "G": "404"}
        packet["facts"] = [fact for fact in packet["facts"] if fact["field"] != "directed_call_edge"]
        for fact in packet["facts"]:
            field = str(fact["field"])
            if field in {"metric_series_64", "log_summary_entry", "trace_summary_entry", "propagation_service"}:
                entity = region_entities[str(fact["region"])]
                fact["payload"]["service"] = entity
                fact["entity_ids"] = [entity]
        return questions_for_case(packet, f"INC-SPARSE-{int(paired_lr)}")[1]

    one_level = sparse_questions(paired_lr=False)
    two_levels = sparse_questions(paired_lr=True)
    _assert(
        [question.level for question in one_level] == [1]
        and [question.level for question in two_levels] == [1, 2],
        "case-local question eligibility fabricated an unsupported reasoning level",
    )
    one_level_public = [question.public() for question in one_level]
    one_level_schema = response_schema(
        experiment_registry(load_yaml())["cross_region"], 1, one_level_public,
    )["json_schema"]["schema"]["properties"]["answers"]
    _assert(
        (one_level_schema["minItems"], one_level_schema["maxItems"]) == (1, 1)
        and one_level_schema["prefixItems"][0]["properties"]["query_id"]["const"] == "q1",
        "case-local live grammar does not bind the exact eligible query inventory",
    )
    one_level_response = {"answers": [{"query_id": "q1", "answer": {"steps": [{
        "step": 1, "region": one_level[0].regions[0],
        "values": list(one_level[0].answer_steps[0]),
    }]}}]}
    sparse_score = score_reasoning(one_level_response, [one_level[0].private()])
    _assert(
        sparse_score["complete_chain_accuracy"] == 1.0
        and sparse_score["eligible_reasoning_levels"] == [1]
        and sparse_score["level_2_complete_chain_accuracy"] is None
        and sparse_score["level_3_complete_chain_accuracy"] is None,
        "an ineligible reasoning level was scored as a model failure",
    )
    response = {"answers": [{"query_id": q.query_id, "answer": {"steps": [
        {"step": index, "region": region, "values": list(q.answer_steps[index - 1])}
        for index, region in enumerate(q.regions, 1)]}} for q in reasoning]}
    validate_qa_response(response, [q.public() for q in reasoning])
    _assert(score_reasoning(response, [q.private() for q in reasoning])["complete_chain_accuracy"] == 1.0,
            "known-correct nested Q&A response did not score one")
    def selector(region: str) -> dict[str, Any]:
        return {"record_key": {"M": "M1", "L": "L:101", "R": "R:101", "G": "G:101"}[region],
                "field": None}
    typed = {q.query_id: {f"s{index}": selector(region)
                          for index, region in enumerate(q.regions, 1)} for q in reasoning}
    normalized_typed = normalize_typed_qa_ledger(
        typed, [q.public() for q in reasoning], qa,
    )
    _assert(normalized_typed["binding_audit"]["unsupported_steps"] == 0,
            "host-bound typed selector fixture contains unsupported steps")
    identity_questions = [
        {"query_id": "q1", "region_path": ["M"]},
        {"query_id": "q2", "region_path": ["G"]},
    ]
    identity_selectors = {
        "q1": {"s1": {"record_key": "M1", "field": "entity_id"}},
        "q2": {"s1": {"record_key": "G:101", "field": "entity_id"}},
    }
    identity_bound = normalize_typed_qa_ledger(identity_selectors, identity_questions, qa)
    _assert(identity_bound["binding_audit"] == {"supported_steps": 2, "unsupported_steps": 0}
            and all(any(record["entity_ids"] == ["101"]
                        for record in row["observations"][0]["records"])
                    for row in identity_bound["ledgers"]),
            "canonical entity_id selectors do not bind visible public record identities")
    invalid_identity = json.loads(json.dumps(identity_selectors))
    invalid_identity["q1"]["s1"]["field"] = "entity"
    invalid_identity["q2"]["s1"]["record_key"] = "G:999"
    invalid_bound = normalize_typed_qa_ledger(invalid_identity, identity_questions, qa)
    _assert(invalid_bound["binding_audit"] == {"supported_steps": 0, "unsupported_steps": 2},
            "typed identity binder guessed an alias or invalid public record key")
    selector_schema = response_schema(
        experiment_registry(load_yaml())["typed_two_stage"], 1,
        [q.public() for q in reasoning],
    )["json_schema"]["schema"]["properties"]
    for question in reasoning:
        for index, _region in enumerate(question.regions, 1):
            properties = selector_schema[question.query_id]["properties"][f"s{index}"]["properties"]
            _assert(set(properties) == {"record_key", "field"},
                    "typed Q&A selector is not the compact public record-key contract")
    _assert(set(qa["fact_mappings"]) == {fact["fact_id"] for fact in qa["facts"]}
            and all(set(row) == {"T_QA", "P_QA", "V_QA", "factorial_region"}
                    for row in qa["fact_mappings"].values()),
            "canonical Q&A fact-to-representation index is incomplete")
    _assert(load_yaml()["experiments"]["cross_region"]["reasoning_levels"] == [1, 2, 3],
            "absent Level 4-6 source was silently represented by template counts")
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
            _assert(bool(qa_representation_parts(arm, qa, png, pixel_pages, region_pngs)),
                    f"{name}/{arm} compiled no prompt parts")
        questions = (public["legacy_questions"] if name == "legacy_q9"
                     else public["reasoning_questions"])
        response_schema(spec, 1, questions)
        if spec.stages == 2:
            response_schema(spec, 2, questions)
        compiled_arms[name] = len(spec.arms)
    legacy_answer_schema = response_schema(
        registry["legacy_q9"], 1, public["legacy_questions"],
    )["json_schema"]["schema"]["properties"]["answers"]
    cross_answer_schema = response_schema(
        registry["cross_region"], 1, public["reasoning_questions"],
    )["json_schema"]["schema"]["properties"]["answers"]
    typed_answer_schema = response_schema(
        registry["typed_two_stage"], 2, public["reasoning_questions"],
    )["json_schema"]["schema"]["properties"]["answers"]
    _assert(
        (legacy_answer_schema["minItems"], legacy_answer_schema["maxItems"]) == (9, 9)
        and (cross_answer_schema["minItems"], cross_answer_schema["maxItems"]) == (3, 3)
        and (typed_answer_schema["minItems"], typed_answer_schema["maxItems"]) == (3, 3),
        "live Q&A grammar does not require the complete supplied query inventory",
    )
    for schema, questions, typed in (
        (legacy_answer_schema, public["legacy_questions"], False),
        (cross_answer_schema, public["reasoning_questions"], False),
        (typed_answer_schema, public["reasoning_questions"], True),
    ):
        rows = schema.get("prefixItems") or []
        _assert(len(rows) == len(questions),
                "live Q&A grammar does not bind each ordered query")
        for row, question in zip(rows, questions, strict=True):
            _assert(row["properties"]["query_id"].get("const") == question["query_id"],
                    "live Q&A grammar does not bind ordered query IDs")
            step_schema = row["properties"]["answer"]["properties"]["steps"]
            expected_regions = list(question["region_path"])
            _assert(
                (step_schema["minItems"], step_schema["maxItems"]) ==
                (len(expected_regions), len(expected_regions))
                and len(step_schema.get("prefixItems") or ()) == len(expected_regions),
                "live Q&A grammar and validator disagree on exact step count",
            )
            for index, (step, region) in enumerate(
                zip(step_schema["prefixItems"], expected_regions, strict=True), 1,
            ):
                properties = step["properties"]
                _assert(
                    properties["step"].get("const") == index
                    and properties["region"].get("const") == region,
                    "live Q&A grammar and validator disagree on the step path",
                )
                if typed:
                    expected_kinds = TEMPLATE_VALUE_KINDS[question["template"]]
                    _assert(properties["value_kind"].get("const") == expected_kinds[index - 1],
                            "typed answer grammar and validator disagree on value kind")
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
    contract = _request_contract(
        experiment_id="smoke-fixture", experiment="ledger_handoff_rca", model="fixture",
        execution_mode="smoke", opaque_incident_id="INC-FIXTURE", arm="L_hyb",
        parts=[{"type": "text", "text": "fixture"}], runtime_freeze_sha256="freeze",
        extra={"shared_stage1_call_key": "shared"},
    )
    _assert(
        len(contract["call_key"]) == 24 and contract["representation_hash"]
        and contract["runtime_freeze_sha256"] == "freeze"
        and contract["shared_stage1_call_key"] == "shared",
        "shared request-contract helper omitted resumability provenance",
    )
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


def check_analysis_completeness(config: dict[str, Any]) -> dict[str, Any]:
    """Entirely absent model/case pairs must make a model summary incomplete."""

    spec = experiment_registry(config)["legacy_q9"]
    case_ids = ("INC-SMOKE-A", "INC-SMOKE-B", "INC-SMOKE-C")
    models = ("qwen3.6-27b", "gemma-4-26b-a4b")
    assignments = ((models[0], case_ids[:1]), (models[1], case_ids))
    records = [{
        "model": model, "opaque_incident_id": case_id, "arm": arm,
        "status": "completed", "analysis_dataset": "aiops2022",
        "score": {spec.primary_metric: 1.0},
        "stages": [{"stage": 1, "parse": True}], "visual_diagnostic": {},
    } for model, cases in assignments for case_id in cases for arm in spec.arms]
    result = analyze_records(records, spec, config, expected_models=models,
                             expected_case_ids=case_ids)
    qwen = result["by_model"][models[0]]
    gemma = result["by_model"][models[1]]
    _assert(not result["complete"] and not qwen["complete"] and gemma["complete"],
            "an incomplete model was reported complete")
    exclusion = qwen["whole_case_exclusion"]
    _assert((exclusion["total_cases"], exclusion["included_cases"],
             exclusion["incomplete_pair_cases"]) == (3, 1, 2),
            "entirely absent expected cases were not counted as incomplete")
    return {"aggregate_complete": result["complete"], "qwen_complete": qwen["complete"],
            "qwen_incomplete_cases": exclusion["incomplete_pair_cases"],
            "gemma_complete": gemma["complete"]}


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
        ("analysis_completeness", lambda: check_analysis_completeness(config)),
    ]
    results: dict[str, Any] = {}
    for name, check in checks:
        results[name] = check()
    return {"passed": True, "model_calls": 0, "checks": results}


if __name__ == "__main__":
    print(json.dumps(run_static_checks(), indent=2, sort_keys=True))
