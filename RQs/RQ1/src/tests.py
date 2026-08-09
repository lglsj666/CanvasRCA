"""CPU-only structural and contract checks for the refactored RQ1 code."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any, Callable

from unified_scripts.rca_scorer import RCAScorer, RCAScorerConfig
from unified_scripts.vllm_inference import VLLMInferenceConfig

from .exps import RCA_ARMS, experiment_registry, factorial_cells
from .gates import qualification_contracts
from .utils import DEFAULT_CONFIG, ROOT, load_yaml, numeric_entity_map

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
        scripts = [path for path in (rq / "scripts").iterdir() if path.is_file()]
        _assert(len(scripts) <= 10, f"{number} scripts exceeds ten files")
        _assert(all(path.suffix == ".sh" for path in scripts), f"{number} scripts contains non-sh files")
        script_lines = _line_count(scripts)
        _assert(script_lines <= 800, f"{number} scripts exceeds 800 lines")
        source_lines = _line_count([rq / "src" / name for name in FUNCTIONAL_RQ_FILES])
        _assert(source_lines <= 2500, f"{number} functional source exceeds 2500 lines: {source_lines}")
        findings = [path.name for path in (rq / "findings").iterdir() if path.is_file()]
        _assert(all(name.startswith("exp_") and name.endswith("_findings.md") for name in findings), f"{number} has a noncanonical finding filename")
        checked[number] = {"script_files": len(scripts), "script_lines": script_lines, "functional_source_lines": source_lines, "findings": len(findings)}
    return checked


def check_python_syntax() -> dict[str, int]:
    files = [path for path in ROOT.rglob("*.py") if ".git" not in path.parts]
    for path in files:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {"parsed_python_files": len(files)}


def check_unified_contracts(config: dict[str, Any]) -> dict[str, Any]:
    runtime = VLLMInferenceConfig.load(config["unified"]["vllm"])
    qwen_args = runtime.server_argv("qwen3.6-27b")
    gemma_args = runtime.server_argv("gemma-4-26b-a4b")
    _assert("--gpu-memory-utilization" not in qwen_args + gemma_args, "Nibi launcher still has a VRAM fraction cap")
    _assert("--mm-processor-kwargs" not in qwen_args, "Qwen still has a project pixel limit")
    _assert("--mm-processor-kwargs" in gemma_args, "Gemma soft-token policy disappeared")
    _assert("--enable-chunked-prefill" in gemma_args, "Gemma chunked prefill disappeared")
    scorer = RCAScorer(RCAScorerConfig.load(config["unified"]["scorer"]), hit=lambda a, b: a == b)
    score = scorer.score(["wrong", "root"], ["root"]).as_dict()
    _assert(score["mrr"] == 0.5 and score["ac@1"] == 0.0 and score["ac@3"] == 1.0, "scorer metric definitions drifted")
    _assert(score["avg@3"] == 2 / 3 and score["avg@5"] == 4 / 5, "AVG@K drifted from cumulative-AC definition")
    return {"qwen_server_args": qwen_args, "gemma_server_args": gemma_args, "synthetic_score": score}


def check_rq1_contract(config: dict[str, Any]) -> dict[str, Any]:
    registry = experiment_registry(config)
    _assert(set(registry) == {
        "legacy_q9", "cross_region", "typed_two_stage", "matched_rca",
        "visual_counterfactual_rca", "ledger_handoff_rca",
    }, "RQ1 experiment registry drifted")
    _assert(registry["matched_rca"].arms == RCA_ARMS, "RCA arms drifted")
    _assert(registry["visual_counterfactual_rca"].arms == ("H_factual", "H_targeted", "H_placebo", "H_neutral"), "counterfactual arms drifted")
    _assert(registry["ledger_handoff_rca"].arms == ("L_txt", "L_vis", "L_hyb"), "handoff arms drifted")
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
    return {"experiments": sorted(registry), "factorial_cells": 16, "id_granularities": kinds, "eval_counts": counts}


def run_static_checks(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    """Run static/CPU checks only; this function cannot invoke a model."""

    config = load_yaml(config_path)
    checks: list[tuple[str, Callable[[], Any]]] = [
        ("global_layout", check_global_layout),
        ("rq_layouts", check_rq_layouts),
        ("python_syntax", check_python_syntax),
        ("unified_contracts", lambda: check_unified_contracts(config)),
        ("rq1_contract", lambda: check_rq1_contract(config)),
    ]
    results: dict[str, Any] = {}
    for name, check in checks:
        results[name] = check()
    return {"passed": True, "model_calls": 0, "checks": results}


if __name__ == "__main__":
    print(json.dumps(run_static_checks(), indent=2, sort_keys=True))
