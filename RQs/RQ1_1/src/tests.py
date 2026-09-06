"""Static and CPU-only qualification for RQ1.1."""

from __future__ import annotations

import ast
import hashlib
import io
import json
import math
import os
import py_compile
import re
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pandas as pd
from PIL import Image

from unified_scripts import stable_hash
from unified_scripts.vllm_inference import VLLMInferenceConfig
from vlmrca.evidence import compact_evidence_text, parse_compact_evidence, semantic_packet_facts
from vlmrca.vlm.performance import parse_prometheus_metric, request_timing_summary

from .exps import (
    FACTORIAL_ARM_REGIONS,
    QA_ARMS,
    RCA_ARMS,
    RCA_SYSTEM_ROLE,
    REGIONS,
    DASHBOARD_VISUAL_GUIDE,
    PIXEL_TEXT_VISUAL_GUIDE,
    QA_GUIDE,
    PreparedCase,
    _anonymize_text,
    build_visible_packet,
    build_reasoning_trace,
    reasoning_trace_svg,
    build_denum_log_graph,
    counterfactual_pairs,
    counterfactual_rca_parts,
    compile_text_screenshot,
    denum_text,
    denum_visual_text,
    denum_visible_rows,
    direct_rca_parts,
    direct_rca_prompt,
    execute_tool,
    experiment_registry,
    packet_text,
    questions_for_case,
    qa_arm_parts,
    qa_value_support,
    representation_audit,
    representation_guide,
    representation_parts,
    score_qa,
    validate_diagnosis,
    validate_qa,
)
from .gates import analyze_factorial_rca, analyze_perception_rca, analyze_records
from .utils import DEFAULT_CONFIG, ROOT, RQ1Error, load_yaml


def _assert(value: Any, message: str) -> None:
    if not value:
        raise RQ1Error(message)


def _lines(paths: list[Path]) -> int:
    return sum(
        bool(line.strip()) and not line.lstrip().startswith("#")
        for path in paths for line in path.read_text(encoding="utf-8").splitlines()
    )


def check_layout() -> dict[str, Any]:
    rq = ROOT / "RQs/RQ1_1"
    required_dirs = {"configs", "descriptions", "findings", "results", "scripts", "src"}
    _assert(required_dirs <= {path.name for path in rq.iterdir() if path.is_dir()}, "RQ1.1 directory layout incomplete")
    descriptions = {path.name for path in (rq / "descriptions").glob("*.md")}
    _assert(descriptions == {"RQ1_1_statement.md", "RQ1_1_experiments.md", "RQ1_1_roadMap.md"}, "descriptions must contain exactly three canonical files")
    findings = {path.name for path in (rq / "findings").glob("*.md")}
    _assert(findings == {"exp_direct_rca_findings.md", "exp_direct_qa_findings.md", "exp_multi_stage_rca_findings.md", "exp_one_stage_counterfactual_rca_findings.md"}, "findings must contain exactly one file per experiment")
    functional = [rq / "src" / name for name in ("main.py", "utils.py", "exps.py", "tests.py", "gates.py")]
    _assert(all(path.is_file() for path in functional) and (rq / "src/__init__.py").is_file(), "functional source files missing")
    _assert(_lines(functional) <= 6000, "RQ1.1 functional Python exceeds 6000 lines")
    scripts = list((rq / "scripts").glob("*.sh"))
    _assert(len(scripts) <= 10 and _lines(scripts) <= 800, "RQ1.1 shell script budget exceeded")
    return {"functional_python_lines": _lines(functional), "shell_files": len(scripts), "shell_lines": _lines(scripts)}


def check_syntax() -> dict[str, int]:
    paths = list((ROOT / "RQs/RQ1_1").rglob("*.py"))
    for path in paths:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        py_compile.compile(str(path), doraise=True)
    return {"python_files": len(paths)}


def check_no_incomplete_implementations() -> dict[str, Any]:
    """Reject empty function bodies and explicit implementation skeletons."""

    incomplete: list[str] = []
    markers = ("TO" + "DO", "FIX" + "ME")
    paths = list((ROOT / "RQs/RQ1_1/src").rglob("*.py"))
    for path in paths:
        source = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker in source:
                incomplete.append(f"{path.relative_to(ROOT)}: marker {marker}")
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            body = list(node.body)
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
                body = body[1:]
            if not body or (len(body) == 1 and isinstance(body[0], (ast.Pass, ast.Expr)) and (
                isinstance(body[0], ast.Pass) or getattr(getattr(body[0], "value", None), "value", None) is Ellipsis
            )):
                incomplete.append(f"{path.relative_to(ROOT)}:{node.lineno} empty {node.name}")
            if len(body) == 1 and isinstance(body[0], ast.Raise):
                call = body[0].exc
                if isinstance(call, ast.Call) and getattr(call.func, "id", "") == "NotImplementedError":
                    incomplete.append(f"{path.relative_to(ROOT)}:{node.lineno} NotImplemented {node.name}")
    _assert(not incomplete, f"incomplete RQ1.1 implementations: {incomplete[:10]}")
    return {"python_files": len(paths), "incomplete": []}


def check_contract_coverage() -> dict[str, Any]:
    """Ensure every shared preparation/runtime/scoring authority is hashed."""

    source = (ROOT / "RQs/RQ1_1/src/main.py").read_text(encoding="utf-8")
    required = {
        "src/unified_scripts/dataset_segmentation.py",
        "src/unified_scripts/rca_scorer.py",
        "src/unified_scripts/vllm_inference.py",
        "src/vlmrca/evidence.py",
        "src/vlmrca/processed.py",
        "src/vlmrca/upstream.py",
        "src/vlmrca/eval/scoring.py",
        "src/vlmrca/vlm/client.py",
        "src/vlmrca/vlm/performance.py",
        "src/vlmrca/vlm/attention_probe.py",
    }
    normalized = source.replace('ROOT / "', "").replace('" / "', "/")
    missing = sorted(path for path in required if path not in normalized)
    _assert(not missing, f"run contract omits shared authorities: {missing}")
    return {"shared_authorities": len(required), "renderer_hashed_separately": True}


def check_config(config: dict[str, Any]) -> dict[str, Any]:
    specs = experiment_registry(config)
    _assert(set(specs) == {"direct_rca", "direct_qa", "one_stage_counterfactual_rca", "multi_stage_rca"}, "unexpected RQ1.1 experiment registry")
    _assert(specs["direct_rca"].arms == RCA_ARMS and len(RCA_ARMS) == 19, "19-arm RCA design drifted")
    _assert(specs["direct_qa"].arms == QA_ARMS and len(QA_ARMS) == 18, "direct-QA targeted arms drifted")
    _assert(specs["multi_stage_rca"].steps == 3 and specs["multi_stage_rca"].calls_per_case_arm == 6, "three-step/two-call state machine drifted")
    _assert(specs["multi_stage_rca"].status == "abandoned", "multi-stage RCA re-entered the active protocol")
    _assert(specs["one_stage_counterfactual_rca"].status == "qualification_pending_rq2_completion", "counterfactual RCA was enabled before RQ2 completion")
    _assert(config["runtime"]["models"] == ["qwen3.8-27b", "gemma-4-26b-a4b"], "active model list drifted")
    _assert(config["external_methods"]["denum"]["binary_output"] is False, "binary Denum output is prohibited")
    _assert(config["runtime"]["smoke_call_cap_total"] == 18 and config["runtime"]["smoke_timeout_seconds_total"] == 600, "shared smoke bounds drifted")
    _assert(config["runtime"]["max_workers"] == 8, "preparation/writer worker count drifted")
    _assert(set(config["smoke_plans"]) == {"direct_rca", "direct_qa", "one_stage_counterfactual_rca"}, "smoke registry drifted")
    for experiment in ("direct_rca", "direct_qa", "one_stage_counterfactual_rca"):
        plan = config["smoke_plans"][experiment]
        calls = sum(
            len((plan[model].get(dataset) or ()))
            for model in config["runtime"]["models"] for dataset in config["data"]["smoke_datasets"]
        )
        _assert(plan["total_calls"] == calls <= 18, f"{experiment} smoke exceeds its aggregate call cap")
    return {"experiments": sorted(specs), "models": list(config["runtime"]["models"])}


def check_provenance(config: dict[str, Any]) -> dict[str, Any]:
    # DD-135 deliberately removed the obsolete migration artifact tree.  The
    # original byte-copy provenance remains in project history; current static
    # qualification must not recreate or depend on deleted preparation state.
    rq_root = ROOT / "RQs/RQ1_1/src"
    rq_files = sorted(path for path in rq_root.rglob("*.py") if path.is_file())
    _assert(rq_files, "RQ1.1 source tree is missing")
    source_tree = {
        str(path.relative_to(rq_root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in rq_files
    }
    source = json.loads((ROOT / "packages/THIRD_PARTY_SOURCES.json").read_text())
    for name, expected in (("ReAct", config["external_methods"]["react"]["commit"]), ("Denum", config["external_methods"]["denum"]["commit"])):
        _assert(source[name]["commit"] == expected, f"{name} commit provenance drifted")
        _assert((ROOT / "packages" / name / source[name]["license_file"]).is_file(), f"{name} license missing")
    sircl_root = ROOT / "packages/SIRCL_selected_reference"
    sircl = json.loads((sircl_root / "PROVENANCE.json").read_text(encoding="utf-8"))
    for relative, expected in sircl["key_file_sha256"].items():
        actual = hashlib.sha256((sircl_root / relative).read_bytes()).hexdigest()
        _assert(actual == expected, f"SIRCL byte snapshot drifted: {relative}")
    files = sorted(path for path in sircl_root.rglob("*") if path.is_file() and path.name != "PROVENANCE.json")
    digest_lines = "".join(
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  ./{path.relative_to(sircl_root)}\n"
        for path in files
    )
    tree_hash = hashlib.sha256(digest_lines.encode()).hexdigest()
    _assert(tree_hash == sircl["copied_files_tree_sha256"] == source["SIRCL_selected_reference"]["source_tree_sha256"], "SIRCL snapshot tree hash drifted")
    prompt = direct_rca_prompt(_fixture_packet())
    for marker in ("MET-Z analyzer", "TRC-L analyzer", "LOG-R analyzer", "INITIAL:", "VERIFY:", "REVISE:"):
        _assert(marker in prompt, f"SIRCL* prompt adaptation is missing {marker}")
    _assert("case.timestamp" not in prompt and "injection" not in prompt.casefold(), "SIRCL adaptation exposed a label-time split")
    _assert("Output exactly one JSON object" in prompt, "U-BASE lost the early response contract")
    _assert(
        "Never include the literal working labels" in prompt and "at most three sentences" in prompt,
        "direct-RCA prompt does not keep internal verify/revise work out of the final reason",
    )
    _assert("Output exactly one JSON object" not in RCA_SYSTEM_ROLE, "U-BASE leaked response instructions into system role")
    from .exps import SIRCL_STAR_FACT_ADAPTER
    _assert(tuple(SIRCL_STAR_FACT_ADAPTER) == ("MET-Z", "TRC-L", "LOG-R", "TOPOLOGY"), "SIRCL fact-adapter order drifted")
    _assert("regular_mean" in SIRCL_STAR_FACT_ADAPTER["MET-Z"], "MET-Z statistics are not active")
    _assert("exl_p95_fault_ms" in SIRCL_STAR_FACT_ADAPTER["TRC-L"], "TRC-L exclusive latency is not active")
    _assert("error_rate_fault" in SIRCL_STAR_FACT_ADAPTER["LOG-R"], "LOG-R frequency ratio is not active")
    return {"current_source_tree_sha256": stable_hash(source_tree), "packages": source}


def check_renderer_inheritance() -> dict[str, Any]:
    from .renderer.dashboard import RENDERER_VERSION
    from .renderer.panels import _display_free_text

    renderer_root = ROOT / "RQs/RQ1_1/src/renderer"
    current = {
        str(path.relative_to(renderer_root)): stable_hash(
            ast.dump(ast.parse(path.read_text(encoding="utf-8")), include_attributes=False)
        )
        for path in sorted(renderer_root.rglob("*.py"))
        if path.name != "diagnostics.py"
    }
    _assert(RENDERER_VERSION == 14, "authorized RQ1.1 renderer-v14 is not active")
    _assert(
        _display_free_text(
            "hipstershop.checkoutservice/placeorder",
            {"checkoutservice": "207"},
        ) == "hipstershop.207/placeorder",
        "natural entity embedded in trace operation was not anonymized",
    )
    _assert(not (ROOT / "RQs/RQ1_1/src/renderer/diagnostics.py").exists(), "retired attention diagnostics remain active")
    return {"renderer_files": len(current), "renderer_tree_hash": stable_hash(current), "renderer_version": RENDERER_VERSION}


def check_denum() -> dict[str, Any]:
    long_suffix = "diagnostic-segment-" * 24
    frame = pd.DataFrame({
        "timestamp": [0.0, 1.0, 2.0, 3.0, 4.0],
        "container_name": ["svc-a"] * 5,
        "level": ["ERROR", "ERROR", "INFO", "ERROR", "ERROR"],
        "message": [
            "\x1b[31mtimeout after 1200 ms status=504\x1b[0m",
            "timeout after 1250 ms status=504",
            "peer=10.0.0.2 uuid=123e4567-e89b-12d3-a456-426614174000",
            "hex=0xFF float=-3.25 missing=null",
            f"request failed status=503 latency=987 {long_suffix}",
        ],
    })
    graph = build_denum_log_graph(frame, {"svc-a": "222"})
    samples = ("svc-a then SVC-A", "prefix svc-a-suffix", "unrelated")
    mapping = {"svc": "111", "svc-a": "222"}
    for sample in samples:
        legacy = sample
        for natural in sorted(mapping, key=len, reverse=True):
            legacy = re.sub(re.escape(natural), mapping[natural], legacy, flags=re.IGNORECASE)
        _assert(_anonymize_text(sample, mapping) == legacy, "optimized anonymizer changed public text")
    _assert(graph["semantic_round_trip"] and not graph["binary_output"], "Denum readable graph round-trip failed")
    rows = denum_visible_rows(graph, 8)
    text = denum_text(graph, rows)
    _assert("1200" in text and "504" in text and "LT" in text, "Denum projection discarded diagnostic numeric/template facts")
    _assert("svc-a" not in text and "222" in text, "Denum projection failed entity anonymization")
    long_source = next(row for row in graph["entries"] if "diagnostic-segment" in str(row["template"]))
    long_row = next(row for row in rows if row["template_id"] == long_source["template_id"])
    expected_hash = hashlib.sha256(str(long_source["template"]).encode()).hexdigest()
    _assert(long_row["template_truncated"] is True, "overlong Denum row was not bounded")
    _assert(len(long_row["template"]) <= 160, "bounded Denum template exceeds registered limit")
    _assert(long_row["template_full_sha256"] == expected_hash, "bounded Denum row lost its source hash")
    _assert(long_suffix not in long_row["template"], "bounded Denum projection exposed its hidden suffix")
    visual = denum_visual_text(long_row)
    _assert(expected_hash in text and expected_hash in visual, "text/visual Denum projections disagree on template identity")
    for token in ("n=", "first=", "last=", "distinct=", "top="):
        _assert(token in visual, f"visual Denum numeric summary lost {token}")
    return {
        "events": graph["event_count"], "templates": graph["template_count"],
        "character_ratio": graph["character_compression_ratio"], "template_limit": 160,
    }


def check_resume_integrity() -> dict[str, Any]:
    from .main import (
        QA_GUIDE_SYSTEM,
        _compatible_qa_terminal,
        _persist_prepared,
        _read_prepared,
        _valid_terminal_record,
    )
    from .utils import RunPaths

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "terminal.json"
        expected = {
            "call_key": "call", "run_contract_sha256": "contract",
            "prepared_evidence_sha256": "evidence",
            "evaluator_private_sha256": "private",
        }
        record = {"status": "completed", **expected}
        record["record_sha256"] = stable_hash(record)
        path.write_text(json.dumps(record), encoding="utf-8")
        path.with_suffix(".md").write_text("conversation", encoding="utf-8")
        _assert(_valid_terminal_record(path, expected), "valid terminal was not resumable")
        changed = {**expected, "prepared_evidence_sha256": "different"}
        _assert(not _valid_terminal_record(path, changed), "changed preparation reused an old terminal")
        path.with_suffix(".md").unlink()
        _assert(not _valid_terminal_record(path, expected), "missing conversation was accepted")
        qa_path = Path(directory) / "qa-terminal.json"
        public_question = {
            "query_id": "P1-R1-M", "perception_difficulty": 1,
            "reasoning_difficulty": 1, "reasoning_family": "parallel_direct_lookup",
            "effective_program_size": 1, "requested_reasoning_difficulty": 1,
            "requested_region_path": ["M"], "selection_fallback": False,
            "region_path": ["M"], "question": "Read the unique M anchor.",
        }
        private_question = {**public_question, "answer_steps": [["222"]], "supporting_fact_ids": [["f1"]]}
        normalized = {"steps": [{"region": "M", "values": ["222"]}]}
        predecessor = "predecessor-contract"
        qa_record = {
            "schema_version": "RQ1_1TrajectoryV1", "experiment": "direct_qa",
            "model": "qwen3.8-27b", "opaque_incident_id": "INC-RESUME", "arm": "L1_T",
            "run_contract_sha256": predecessor, "status": "completed", "model_calls": 1,
            "question": public_question, "qa_condition": "T", "mapped_rca_arm": "T",
            "visual_regions": [], "stages": [{"system": QA_GUIDE_SYSTEM,
            "parts": [{"type": "text", "text": "same request"}], "normalized": normalized}],
            "score": score_qa(normalized, private_question),
        }
        qa_record["record_sha256"] = stable_hash(qa_record)
        qa_path.write_text(json.dumps(qa_record), encoding="utf-8")
        qa_path.with_suffix(".md").write_text("conversation", encoding="utf-8")
        compatibility = {"resume_compatibility": {
            "direct_qa_predecessor_contract_sha256": [predecessor],
        }}
        _assert(_compatible_qa_terminal(
            qa_path, config=compatibility, model="qwen3.8-27b", opaque="INC-RESUME",
            arm="L1_T", question=public_question, private_question=private_question,
            parts=[{"type": "text", "text": "same request"}], mapped_rca_arm="T",
            visual_regions=(),
        ), "exact-compatible predecessor QA terminal was not resumable")
        _assert(not _compatible_qa_terminal(
            qa_path, config=compatibility, model="qwen3.8-27b", opaque="INC-RESUME",
            arm="L1_T", question={**public_question, "question": "changed"},
            private_question=private_question,
            parts=[{"type": "text", "text": "same request"}], mapped_rca_arm="T",
            visual_regions=(),
        ), "changed QA question reused a predecessor terminal")
        prepared = PreparedCase(
            {"opaque_incident_id": "INC-RESUME", "selected_questions": []},
            {"opaque_incident_id": "INC-RESUME", "labels": ["private"], "selected_questions": []},
            b"full", (b"screenshot",), {"M": (b"metric",)}, {"V": b"variant"},
        )
        paths = RunPaths(Path(directory) / "prepared-run")
        item = _persist_prepared(paths, prepared)
        _read_prepared(paths, item)
        (paths.root / item["region_images"]["M"][0]).write_bytes(b"corrupt")
        try:
            _read_prepared(paths, item)
        except RQ1Error:
            pass
        else:
            raise RQ1Error("corrupt prepared image was accepted")
    return {"hash_bound": True, "conversation_required": True}


def _fixture_packet() -> dict[str, Any]:
    facts = []
    for index, region in enumerate(REGIONS):
        field = {"M": "metric_series_64", "R": "trace_summary_entry", "L": "denum_log_template", "G": "directed_call_edge"}[region]
        entities = ("222", "333") if region != "G" else ("222",)
        for offset, entity in enumerate(entities):
            if region == "M":
                payload = {"panel_id": f"M0{offset + 1}", "metric": "latency", "values": ["1.0"] * 64, "peak": str(offset + 1), "signed_z": str(offset + 2)}
            elif region == "R":
                payload = {"entry_index": offset, "exl_p95_fault_ms": str(12 + offset), "rank_score": str(2 + offset)}
            elif region == "L":
                payload = {"template_id": f"LT0{offset + 1}", "relative_bin": offset, "level": "ERROR", "count": offset + 2}
            else:
                payload = {"edge_index": 0, "caller": "222", "callee": "333"}
            ids = [entity] if region != "G" else ["222", "333"]
            fact = {"region": region, "field": field, "entity_ids": ids, "relative_bins": [offset], "unit": None, "payload": payload}
            fact["fact_id"] = hashlib.sha256(stable_hash(fact).encode()).hexdigest()[:16]
            facts.append(fact)
    packet = {"schema_version": "fixture", "opaque_incident_id": "INC-FIXTURE", "candidates": ["222", "333"], "facts": facts}
    packet["fact_inventory_hash"] = stable_hash(facts)
    return packet


def check_questions_and_arms() -> dict[str, Any]:
    packet = _fixture_packet()
    from .exps import _answer_is_visible
    _assert(
        all(not _answer_is_visible((value,)) for value in ("missing", "none", "nan", "null", "n/a", "na", "unavailable", "")),
        "QA eligibility admitted a non-visible answer token",
    )
    templates, selected = questions_for_case(packet, "INC-FIXTURE")
    counts = {level: sum(q.perception_difficulty == level for q in templates) for level in range(1, 5)}
    _assert(counts == {1: 12, 2: 36, 3: 72, 4: 72}, "QA perception/reasoning matrix drifted")
    parallel = {q.query_id: q.private() for q in templates if q.reasoning_difficulty == 1}
    banned_order_cues = ("first displayed TRC-L row", "first displayed directed edge")
    _assert(
        not any(cue in q["question"] for q in parallel.values() for cue in banned_order_cues),
        "QA question depends on representation-specific trace/topology row order",
    )
    reversed_packet = {**packet, "facts": list(reversed(packet["facts"]))}
    reversed_packet["fact_inventory_hash"] = stable_hash(reversed_packet["facts"])
    reversed_templates, _ = questions_for_case(reversed_packet, "INC-FIXTURE")
    reversed_parallel = {
        q.query_id: q.private() for q in reversed_templates if q.reasoning_difficulty == 1
    }
    _assert(
        parallel == reversed_parallel,
        "QA question or private answer changed when only fact storage order changed",
    )
    _assert({q.perception_difficulty for q in selected} == {1, 2, 3, 4}, "one question per perception level was not selected")
    _assert(all(q.reasoning_difficulty in {1, 2, 3} for q in templates), "invalid QA reasoning difficulty")
    _assert(all(len(q.regions) == q.perception_difficulty for q in templates), "perception difficulty is not the distinct-region count")
    for question in selected:
        payload = {"steps": [{"region": region, "values": list(values)} for region, values in zip(question.regions, question.answer_steps, strict=True)]}
        normalized = validate_qa(payload, question.public())
        _assert(score_qa(normalized, question.private())["complete_chain_accuracy"] == 1.0, "QA exact scorer drifted")
        _assert(not qa_value_support(normalized, packet)["unsupported_values"], "correct QA value was not public")
    no_trace = {
        **packet,
        "facts": [fact for fact in packet["facts"] if fact["region"] != "R"],
    }
    no_trace["fact_inventory_hash"] = stable_hash(no_trace["facts"])
    sparse_templates, sparse_selected = questions_for_case(no_trace, "INC-NO-TRACE")
    _assert(
        {q.perception_difficulty for q in sparse_selected} == {1, 2, 3},
        "a case without visible traces did not response-blindly exclude P4",
    )
    _assert(
        all("R" not in q.regions for q in sparse_templates),
        "an eligible sparse-case QA template depends on an absent trace region",
    )
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
            }, "source_image_px": [100, 100]},
        },
        {}, png, (png,), {region: (png,) for region in REGIONS}, {"V_FACTUAL": png},
    )
    ubase = direct_rca_parts("T", prepared)
    _assert(ubase[0]["text"] == direct_rca_prompt(packet), "U-BASE task/output prefix is not first in the user turn")
    _assert("INCIDENT EVIDENCE" in ubase[1]["text"], "U-BASE evidence does not follow the response contract")
    _assert(ubase[-1]["text"].startswith("Based on the above"), "U-BASE closing query is not last")
    cf = counterfactual_rca_parts("V_FACTUAL", prepared)
    _assert(sum(part["type"] == "image" for part in cf) == 1, "counterfactual RCA must carry exactly one image")
    selector_packet = {"candidates": ["222", "333", "444", "555"], "facts": [
        {"region": "M", "field": "metric_series_64", "entity_ids": [entity],
         "payload": {"signed_z": str(index)}}
        for index, entity in enumerate(("222", "333", "444", "555"), 1)
    ]}
    selection = counterfactual_pairs(selector_packet)
    _assert(selection["eligible"] and selection["targeted"] != selection["placebo"], "label-blind counterfactual pairing failed")
    visual_words = ("dashboard", "image", "pixel", "chart", "canvas", "crop", "spatial")
    text_rca_prompt = "\n".join(
        str(part.get("text", "")) for part in ubase if part["type"] == "text"
    ).casefold()
    _assert(
        not any(word in text_rca_prompt for word in visual_words),
        "text-only RCA prompt received representation-specific visual instructions",
    )
    _assert(
        not any(word in QA_GUIDE.casefold() for word in visual_words),
        "shared QA prompt received representation-specific visual instructions",
    )
    from .main import QA_GUIDE_SYSTEM
    _assert(
        not any(word in QA_GUIDE_SYSTEM.casefold() for word in visual_words),
        "text-only QA system prompt implies visual input",
    )
    _assert(
        representation_guide("T") == "",
        "text representation unexpectedly received a visual decoding guide",
    )
    _assert(
        representation_guide("S") == PIXEL_TEXT_VISUAL_GUIDE
        and "not a telemetry dashboard" in PIXEL_TEXT_VISUAL_GUIDE,
        "pixel-text control is not explicitly separated from the real dashboard",
    )
    v_guide = representation_guide("V", REGIONS)
    for marker in (
        "M is the metric", "G is the anomaly-propagation", "R is the TRC-L",
        "L is the LOG-R", "CALLER ENTITY ID", "Visual regions in this request",
    ):
        _assert(marker in v_guide, f"real-dashboard guide is missing {marker}")
    _assert(DASHBOARD_VISUAL_GUIDE in v_guide, "visual arm lost the registered dashboard grammar")
    for arm in RCA_ARMS:
        parts = representation_parts(arm, prepared)
        _assert(parts and any(part["type"] == "image" for part in parts) == (arm not in {"T", "C"}), f"arm {arm} transport drifted")
        _assert(sum(part["type"] == "image" for part in parts) <= 1, f"arm {arm} exceeds the single-image contract")
    t_parts, v_parts, h_parts = (
        representation_parts(arm, prepared) for arm in ("T", "V", "H")
    )
    _assert(h_parts[0]["png"] == v_parts[0]["png"], "H image fragment differs from V")
    _assert(h_parts[1]["text"] == t_parts[0]["text"], "H text fragment differs from T incident evidence")
    h_full = direct_rca_parts("H", prepared)
    h_incident = [part for part in h_full if part.get("attention_region") in {"dashboard", "evidence_header"}]
    _assert(
        len(h_incident) == 2
        and h_incident[0]["png"] == v_parts[0]["png"]
        and h_incident[1]["text"] == t_parts[0]["text"],
        "representation guide changed H's strict image-first A+B incident fragments",
    )
    for question in (value.public() for value in selected):
        level = int(question["perception_difficulty"])
        conditions = ("T", "V", "S", "PATHV", "CONTEXTV") if level < 4 else ("T", "V", "S")
        for condition in conditions:
            parts, mapped, visual = qa_arm_parts(f"L{level}_{condition}", question, prepared)
            _assert(sum(part["type"] == "image" for part in parts) <= 1, "QA arm exceeds one image")
            _assert(mapped in RCA_ARMS and set(visual) <= set(REGIONS), "QA-to-RCA representation mapping drifted")
        if level < 4:
            _, _, path_visual = qa_arm_parts(f"L{level}_PATHV", question, prepared)
            _, _, context_visual = qa_arm_parts(f"L{level}_CONTEXTV", question, prepared)
            _assert(
                not set(path_visual) & set(context_visual)
                and set(path_visual) | set(context_visual) == set(REGIONS),
                "PathV and ContextV are not exact complements",
            )
    audit = representation_audit(packet, png, (png,), {region: (png,) for region in REGIONS}, text)
    _assert(audit["s_equals_t_bytes"] and audit["c_semantic_round_trip"] and len(audit["fact_inventory_hash_by_arm"]) == 19 and len(set(audit["fact_inventory_hash_by_arm"].values())) == 1, "19-arm equality audit failed")
    pages = compile_text_screenshot(text)
    _assert(pages == compile_text_screenshot(text), "pixel-text renderer is not deterministic")
    _assert(Image.open(io.BytesIO(pages[0])).size == (1800, 1600), "inherited pixel-text geometry drifted")
    validate_diagnosis({"services": ["222"], "reason": "fixture", "confidence": "high"}, packet["candidates"])
    trace = build_reasoning_trace(
        {"services": ["222"], "reason": "M01 and edge 222 -> 333 support 222", "confidence": "high"},
        packet,
        {"numeric_to_natural": {"222": "svc-a", "333": "svc-b"}, "accepted_labels": ["svc-a"]},
    )
    _assert(trace["root_evidence_cited"] and not trace["unsupported_typed_claims"], "visible reasoning trace binding failed")
    svg = reasoning_trace_svg(trace)
    _assert("Visible evidence-flow view" in svg and "hidden chain-of-thought" in svg, "reasoning view is not explicit")
    compact = compact_evidence_text(packet)
    _assert(parse_compact_evidence(compact) == semantic_packet_facts(packet), "CompactTextV1 is not an equal-fact round trip")
    _assert(all(fact["fact_id"] not in compact for fact in packet["facts"]), "compact text leaked private fact IDs")
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
    direct = []
    for case in ("INC-A", "INC-B"):
        for arm, regions in FACTORIAL_ARM_REGIONS.items():
            mrr = 0.2 + (0.1 if "M" in regions else 0.0)
            direct.append({
                "model": "qwen3.8-27b", "arm": arm, "opaque_incident_id": case,
                "analysis_dataset": "aegislab", "status": "completed", "model_output_valid": True,
                "stages": [{"input_tokens": 100 - 10 * len(regions), "normalized": {"services": ["222"]}}],
                "score": {"mrr": mrr, "ac@1": float(mrr >= 1.0)},
            })
    factorial = analyze_factorial_rca(direct, config)
    headline = next(row for row in factorial["summaries"] if row["scope"] == "headline" and row["metric"] == "mrr")
    _assert(math.isclose(headline["conditional_main_effect"]["M"]["delta"], 0.1), "M main effect drifted")
    token = next(row for row in factorial["summaries"] if row["scope"] == "headline" and row["metric"] == "input_tokens")
    _assert(math.isclose(token["conditional_main_effect"]["M"]["delta"], -10.0), "token main effect drifted")
    qa = []
    for case in ("INC-A", "INC-B"):
        for arm, mapped, score in (("L1_T", "T", 0.0), ("L1_PATHV", "MV", 1.0)):
            qa.append({
                "model": "qwen3.8-27b", "arm": arm, "mapped_rca_arm": mapped,
                "qa_condition": arm.split("_", 1)[1], "opaque_incident_id": case,
                "analysis_dataset": "aegislab", "status": "completed", "model_output_valid": True,
                "question": {"perception_difficulty": 1, "reasoning_difficulty": 1, "region_path": ["M"]},
                "stages": [{"input_tokens": 20}],
                "score": {"complete_chain_accuracy": score, "step_accuracy": score,
                          "correct_prefix_accuracy": score, "step_scores": [score]},
            })
    joint = analyze_perception_rca(direct, qa, config)
    improved = [row for row in joint["profiles"] if row["representation"] == "MV"]
    _assert(len(improved) == 2 and all(row["perception_delta_vs_level_matched_text"] == 1.0 for row in improved), "perception pairing drifted")
    return {"infrastructure_errors": 0, "model_output_errors": 1, "factorial_cases": 2, "joint_profiles": len(joint["profiles"])}


def check_performance_metrics() -> dict[str, Any]:
    timing = request_timing_summary(request_elapsed_s=2.0, first_content_s=.5, last_content_s=1.5,
                                    output_tokens=11, content_arrivals_s=[.5, 1.0, 1.5], content_chunks=3)
    _assert(timing["ttft_s"] == .5 and timing["decode_time_s"] == 1.0 and timing["tpot_s"] == .1, "request timing math drifted")
    _assert(parse_prometheus_metric("vllm:gpu_cache_usage_perc 0.5\n", "vllm:gpu_cache_usage_perc") == [.5], "Prometheus parser drifted")
    return timing


def check_inference_projection(config: dict[str, Any]) -> dict[str, Any]:
    from .main import _vllm_config_path

    selected = VLLMInferenceConfig.load(_vllm_config_path(config))
    override = os.environ.pop("CANVASRCA_VLLM_CONFIG", None)
    try:
        nibi = VLLMInferenceConfig.load(config["unified"]["vllm"])
    finally:
        if override is not None:
            os.environ["CANVASRCA_VLLM_CONFIG"] = override
    projection_keys = (
        "served_model_name", "repository_revision", "dtype", "quantization",
        "seed", "generation_config", "max_model_len", "max_tokens",
        "temperature", "top_p", "request_timeout_sec", "wait_timeout_sec",
        "async_scheduling", "mm_processor_cache_gb", "max_num_seqs",
        "tensor_parallel_size", "max_images_per_prompt", "max_videos_per_prompt",
        "disable_thinking", "default_chat_template_kwargs", "enable_prefix_caching",
        "use_flashinfer_sampler", "enforce_eager", "trust_remote_code",
        "enable_log_requests", "batch_invariant", "enable_chunked_prefill",
        "mm_processor_kwargs", "structured_outputs_config",
    )
    projection = {
        model: {key: nibi.model(model).get(key) for key in projection_keys}
        for model in config["runtime"]["models"]
    }
    _assert(set(projection) == {"qwen3.8-27b", "gemma-4-26b-a4b"}, "active inference panel drifted")
    _assert(nibi.model("qwen3.8-27b")["mm_processor_kwargs"] is None, "Qwen3.8 image policy drifted")
    local = VLLMInferenceConfig.load("configs/vllm_inference_local.yaml")
    nibi_normalized, local_normalized = deepcopy(dict(nibi.data)), deepcopy(dict(local.data))
    for payload in (nibi_normalized, local_normalized):
        payload["deployment"] = {"profile": "normalized", "python": "normalized", "vllm_bin": "normalized"}
        payload["common"]["gpu_memory_utilization"] = "deployment-specific"
        for model in payload["models"].values():
            model["model_path"] = "deployment-specific"
    _assert(nibi_normalized == local_normalized, "local and Nibi inference profiles differ beyond paths/VRAM")
    _assert(local.data["common"]["gpu_memory_utilization"] == 0.75, "local VRAM ceiling drifted")
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
    _assert(selected.data["deployment"]["profile"] == "local", "RQ1.1 runner ignored the explicit local profile")
    _assert("sbatch" not in local_launcher.lower(), "local WSL entry points must not submit Slurm jobs")
    _assert("#SBATCH" not in local_launcher, "local WSL entry points must not contain Slurm directives")
    _assert("configs/vllm_inference.yaml" in nibi_launcher, "Nibi launcher does not reset inherited local profile")
    return {
        "nibi_projection_sha256": stable_hash(projection),
        "local_effective_sha256": local.effective_hash(),
        "selected_profile": selected.data["deployment"]["profile"],
        "parity_except_paths_and_vram": True,
    }


def check_attention_protocol() -> dict[str, Any]:
    from types import SimpleNamespace

    import torch
    import vlmrca.vlm.attention_probe as attention_probe
    from .main import _fatal_inference_transport
    from vlmrca.vlm.attention_probe import (
        _find_text_tokens, _inside_registered_answer_field, image_attention_diagnostics,
        map_groups_to_images,
    )

    _assert(
        _find_text_tokens([9, 2, 3, 4, 8], [1, 2, 3, 4, 5], 0) == (1, 1, 1),
        "chat-template boundary-tolerant text mapping drifted",
    )
    _assert(
        _inside_registered_answer_field('{"services":["123')
        and _inside_registered_answer_field('{"steps":[{"values":["missing')
        and not _inside_registered_answer_field('{"services":["123"]'),
        "generation answer-field alignment drifted",
    )
    _assert(
        _fatal_inference_transport(RuntimeError("EngineDeadError: server disconnected"))
        and _fatal_inference_transport(ConnectionError("connection refused"))
        and not _fatal_inference_transport(ImportError("AutoTokenizer")),
        "fatal shared-server circuit-breaker classification drifted",
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
    geometry = {
        "source": "synthetic", "resized_image_px": [100, 100],
        "source_token_grid": [2, 2], "mapping_exact": True,
        "source_token_boxes_px": [
            [0, 0, 50, 50], [50, 0, 100, 50],
            [0, 50, 50, 100], [50, 50, 100, 100],
        ],
    }
    mapped = map_groups_to_images(
        probe, [stream.getvalue()], model_path=".", geometry_override=geometry,
    )[0]
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
                # A KV-cache preemption may make vLLM recompute the same
                # absolute prompt positions.  The probe must deduplicate that
                # replay instead of double-counting it or raising in model
                # forward.
                attention_probe._capture(
                    target, torch.randn(6, 12), torch.randn(6, 6), torch.randn(6, 6),
                )
                sidecar = attention_probe.read_sidecar("canvas-fixture")
                _assert(sidecar is not None and len(sidecar["prompt_token_ids"]) == 5, f"{model} prompt capture failed")
                _assert(
                    sidecar["recomputed_prompt_position_count"] == 6,
                    f"{model} recomputed prompt positions were not deduplicated",
                )
                group = sidecar["image_groups"][0]
                _assert(
                    len(group["weights"]) == len(group["value_norms"]) == len(group["attention_weighted_value_norms"]) == 2,
                    f"{model} visual value capture failed",
                )
                attention_probe._STATE.runner = attention_probe._STATE.scheduler_output = None
                attention_probe._KV.clear()
                attention_probe._FAILED_REQUESTS.clear()

    artifact = {
        "grid": [2, 2], "image_size_px": [100, 100],
        "weights": [0.25] * 4, "global_attention_mass": 0.25,
        "source_attention_weights": [0.0625] * 4,
        "source_token_boxes_px": geometry["source_token_boxes_px"],
    }
    part = {
        "attention_region": "dashboard",
        "attention_visual_regions": ["M", "G"],
        "attention_header_box": [0, 0, 100, 0],
        "attention_region_boxes": {
            "M": [[0, 0, 75, 100]], "R": [], "L": [], "G": [[75, 0, 100, 100]],
        },
    }
    diagnostics = image_attention_diagnostics(artifact, part, REGIONS)
    _assert(
        math.isclose(diagnostics["region_density_lift"]["M"], 1.0)
        and math.isclose(diagnostics["region_density_lift"]["G"], 1.0),
        "area normalization unfairly changed uniform-density M/G attention",
    )
    _assert(
        math.isclose(sum(diagnostics["within_image_region_mass"].values()), 1.0),
        "image attention regions do not conserve within-image mass",
    )
    launchers = [
        ROOT / "scripts/vllm_vlm/serve_canvasrca_local.sh",
        ROOT / "scripts/vllm_vlm/serve_canvasrca_nibi.sh",
    ]
    helper = (ROOT / "scripts/vllm_vlm/enable_attention_probe.sh").read_text(encoding="utf-8")
    _assert("CANVASRCA_ATTENTION_PROBE=1" in helper, "attention probe disabled in shared environment")
    _assert("CANVASRCA_ATTENTION_PROBE_REQUIRED=1" in helper, "attention integrity is optional")
    for launcher in launchers:
        text = launcher.read_text(encoding="utf-8")
        _assert("enable_attention_probe.sh" in text, f"attention environment missing in {launcher.name}")
        _assert("CANVASRCA_ATTENTION_MODEL_PATH" in text, f"answer-token tokenizer path missing in {launcher.name}")
    return {
        "same_prefill_required": True,
        "image_and_text": True,
        "weighted_value_diagnostic": True,
        "area_normalization": "evidence-region attention mass divided by exact pixel area",
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
        "layout": check_layout(), "syntax": check_syntax(),
        "implementation_completeness": check_no_incomplete_implementations(),
        "contract_coverage": check_contract_coverage(), "config": check_config(config),
        "provenance": check_provenance(config), "renderer": check_renderer_inheritance(),
        "denum": check_denum(), "resume": check_resume_integrity(),
        "questions_and_arms": check_questions_and_arms(),
        "candidate_universe": check_candidate_universe(),
        "tools": check_tools(config), "analysis": check_analysis_semantics(config),
        "performance_metrics": check_performance_metrics(),
        "inference": check_inference_projection(config),
        "attention": check_attention_protocol(),
        "legacy_audit": check_no_active_legacy(),
    }
    result["passed"] = True
    result["static_sha256"] = stable_hash(result)
    return result
