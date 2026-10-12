"""Static and CPU-only qualification for the clean RQ2 implementation."""

from __future__ import annotations

import ast
import hashlib
import io
import json
import multiprocessing as mp
import re
import tempfile
import unittest
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from unittest.mock import patch

import numpy as np
import yaml

from unified_scripts import stable_hash
from PIL import Image

from vlmrca.vlm.attention_probe import (
    _ANSWER_ARRAY_FIELDS,
    _area_map,
    _inside_registered_answer_field,
    _intersection_area,
    _publish_generation_profile,
    map_groups_to_images,
)
from vlmrca.evidence import parse_compact_evidence, semantic_packet_facts
from vlmrca.vlm.performance import parse_prometheus_metric, request_timing_summary

from .exps import (
    CONTENT_POLICIES,
    DENSE_CONTENT_POLICY,
    PreparedCase,
    RQ2_PROMPT_ADAPTATION_ID,
    SIRCL_STAR_PROMPT_PARENT_SHA256,
    TOOL_PROFILES,
    TOOL_REGION_ROW_CAPS,
    TRANSFER_ARMS,
    RQ2EvidenceBundleV1,
    _anonymize_text,
    _common_shell,
    _expand_metric_packet,
    build_twins,
    build_tool_packet,
    dashboard_config,
    direct_rca_prompt,
    filter_packet,
    packed_operations,
    _qa_value_equal,
    rq2_representation_guide,
    score_packed_qa,
)
from .gates import (
    DESIGN_FEATURES,
    DESIGN_INTERACTIONS,
    _feature_row,
    analyze_records,
    composer_attribution,
)
from .main import (
    _materialize_unit, _persist_prepared, _physical_cpu_ids, _pin_materializer,
    _read_prepared, _round_robin_case_tasks, _valid_record,
)
from .renderer.designs import (
    ComposerStateV1,
    DashboardSpecV1,
    build_evidence_cards,
    compile_dashboard_program,
    compile_composer_sft_example,
    composer_sft_actions,
    policy_regions,
    render_dashboard_design,
    replay_composer_sft_trace,
    space_filling_specs,
)
from .renderer.human_dashboard import _metric_z
from .utils import PROJECT_ROOT, RunPaths, RQ2Error, verify_roster_bundle


def _fact(region: str, field: str, payload: dict, entities=()) -> dict:
    body = {"region": region, "field": field, "entity_ids": list(entities), "relative_bins": [], "unit": None, "payload": payload}
    return {"fact_id": stable_hash(body)[:16], **body}


def synthetic_packet() -> dict:
    facts = [
        _fact("C", "candidate_set", {"fixed_order": ["123", "456"], "count": 2}, ("123", "456")),
        _fact("C", "evidence_legends", {"relative_time": "64 relative bins"}),
    ]
    for index in range(12):
        facts.append(_fact("M", "metric_series_64", {
            "panel_id": f"M{index + 1:02d}", "service": "123" if index < 6 else "456", "metric": f"metric.{index}",
            "rank": index + 1,
            "values": [None if value == 20 and index == 0 else str((index + value) % 9) for value in range(64)],
            "peak": str(index + 8), "signed_z": str(index / 2),
        }, ("123" if index < 6 else "456",)))
    facts.extend([
        _fact("R", "trace_summary_entry", {"service": "123", "operation": "GET /cart", "exl_p95_fault_ms": "42"}, ("123",)),
        _fact("L", "denum_log_template", {"template_id": "LT01", "entity_id": "123", "relative_bin": 12, "count": 4, "template": "timeout after {n1} ms"}, ("123",)),
        _fact("G", "directed_call_edge", {"caller": "123", "callee": "456"}, ("123", "456")),
        _fact("G", "propagation_service", {"service": "123", "onset_rel_min_display": "+1.2m"}, ("123",)),
        _fact("R", "explicit_missingness", {"traces_missing": False}),
    ])
    facts.sort(key=lambda row: (row["region"], row["field"], row["fact_id"]))
    packet = {
        "schema_version": "RQ2EvidencePacketV1", "opaque_incident_id": "INC-0123456789AB",
        "candidates": ["123", "456"], "facts": facts,
        "fact_inventory_hash": stable_hash(facts), "renderer_fingerprint": "synthetic",
        "source_manifest_hash": "synthetic",
    }
    packet["packet_hash"] = stable_hash(packet)
    return packet


class RQ2StaticTests(unittest.TestCase):
    def setUp(self) -> None:
        self.packet = synthetic_packet()
        self.parent = "parent-renderer-v14"
        self.base_spec = DashboardSpecV1(renderer_parent_hash=self.parent, fact_inventory_hash=self.packet["fact_inventory_hash"])

    def test_v3_target_reuses_full_rq1_case_universe(self) -> None:
        config = yaml.safe_load((PROJECT_ROOT / "RQs/RQ2/configs/rq2.yaml").read_text())
        data = config["data"]
        self.assertEqual(data["roster_status"], "materialized_from_complete_v3_corpus")
        self.assertTrue(data["source_rq1_roster"].endswith("480_private_v3.json"))
        self.assertTrue(data["bundle"].endswith("bundle_v3.json"))
        self.assertEqual(sum(data["exact_counts"]["development"].values()), 60)
        self.assertEqual(sum(data["exact_counts"]["independent"].values()), 150)
        self.assertEqual(sum(data["exact_counts"]["downstream_lock"].values()), 90)
        self.assertEqual(sum(data["exact_counts"]["tool_full"].values()), 480)
        verified = verify_roster_bundle(PROJECT_ROOT / data["bundle"])
        self.assertEqual(verified, {"status": "passed", "rosters": 3, "cases": 300})

    def test_five_module_source_budget(self) -> None:
        source = PROJECT_ROOT / "RQs/RQ2/src"
        paths = [source / name for name in ("main.py", "utils.py", "exps.py", "tests.py", "gates.py")]
        logical_lines = sum(
            bool(line.strip()) and not line.lstrip().startswith("#")
            for path in paths for line in path.read_text(encoding="utf-8").splitlines()
        )
        self.assertLessEqual(logical_lines, 6000)

    def test_no_incomplete_implementation_skeletons(self) -> None:
        incomplete = []
        markers = ("TO" + "DO", "FIX" + "ME")
        for path in (PROJECT_ROOT / "RQs/RQ2/src").rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            for marker in markers:
                if marker in source:
                    incomplete.append(f"{path.name}: marker {marker}")
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
                    incomplete.append(f"{path.name}:{node.lineno} empty {node.name}")
                if len(body) == 1 and isinstance(body[0], ast.Raise):
                    call = body[0].exc
                    if isinstance(call, ast.Call) and getattr(call.func, "id", "") == "NotImplementedError":
                        incomplete.append(f"{path.name}:{node.lineno} NotImplemented {node.name}")
        self.assertEqual(incomplete, [])

    def test_renderer_parent_provenance(self) -> None:
        provenance = json.loads((PROJECT_ROOT / "RQs/RQ2/configs/provenance/renderer_parent_v14.json").read_text())
        self.assertTrue(provenance["byte_identical_before_modification"])
        for name, expected in provenance["files"].items():
            source = PROJECT_ROOT / provenance["source"] / name
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), expected)

    def test_card_grid_design_is_space_filling_reproducible_and_unique(self) -> None:
        specs = space_filling_specs(self.parent, self.packet["fact_inventory_hash"])
        self.assertEqual(specs, space_filling_specs(self.parent, self.packet["fact_inventory_hash"]))
        self.assertEqual(len(specs), 48)
        self.assertEqual(len({spec.cell_id for spec in specs}), 48)
        self.assertEqual({spec.entity_order for spec in specs}, {"stable_id", "salience_onset", "topology_bfs"})
        self.assertGreaterEqual(len({spec.cell_edge_px for spec in specs}), 8)
        self.assertEqual({spec.layout_family for spec in specs}, {"modality_grouped", "entity_grouped", "salience_first", "topology_centered"})
        self.assertEqual({spec.footprint_policy for spec in specs}, {"compact", "balanced", "detailed"})
        self.assertEqual({spec.trace_encoding for spec in specs}, {"trace_dumbbell", "trace_baseline_fault_bars"})
        self.assertEqual(
            {spec.metric_encoding for spec in specs},
            {"heatmap", "small_multiple_lines", "overlay_lines"},
        )
        self.assertTrue(all(
            spec.metric_scale_policy == "common_robust"
            for spec in specs if spec.metric_encoding == "overlay_lines"
        ))
        self.assertEqual({spec.log_encoding for spec in specs}, {"template_frequency_timeline", "template_time_matrix"})
        self.assertEqual({spec.coordination_mode for spec in specs}, {"none", "shared_entity", "shared_time"})
        full_grid = 2 * 2 * 2 * 3 * 2 * 4 * 3 * 3 * 3 * 8 * 4
        self.assertLess(len(specs), full_grid)

        matrix = []
        for spec in specs:
            features = _feature_row(spec.__dict__)
            matrix.append([
                1.0,
                *(features[name] for name in DESIGN_FEATURES),
                *(features[left] * features[right] for left, right in DESIGN_INTERACTIONS),
            ])
        design = np.asarray(matrix, dtype=float)
        self.assertEqual(np.linalg.matrix_rank(design), design.shape[1])
        self.assertLess(np.linalg.cond(design), 200.0)

    def test_equal_fact_cells_render_deterministically(self) -> None:
        hashes = set()
        specs = space_filling_specs(self.parent, self.packet["fact_inventory_hash"])
        for spec in (specs[0], specs[6], specs[12], specs[24], specs[36], specs[39]):
            first, manifest = render_dashboard_design(self.packet, spec)
            second, again = render_dashboard_design(self.packet, spec)
            self.assertEqual(first, second)
            self.assertEqual(manifest, again)
            self.assertEqual(manifest["fact_inventory_hash"], self.packet["fact_inventory_hash"])
            self.assertEqual(
                {row["fact_id"] for row in manifest["fact_mapping"]},
                {row["fact_id"] for row in self.packet["facts"] if row["region"] in {"M", "R", "L", "G"}},
            )
            hashes.add(hashlib.sha256(first).hexdigest())
        self.assertGreaterEqual(len(hashes), 5)

    def test_dense_overlay_anchor_has_a_feasible_lossless_silhouette(self) -> None:
        # D022 combines the registered 160 px cell anchor with compact
        # footprints.  Eight-series overlays still need a four-row legend and
        # must therefore never be packed into the generic 3x3 metric card.
        target = space_filling_specs(self.parent, self.packet["fact_inventory_hash"])[22]
        self.assertEqual(target.cell_id, "D022")
        self.assertEqual(target.metric_encoding, "overlay_lines")
        program = compile_dashboard_program(self.packet, target)
        dense_metric = [
            silhouette for silhouette in program.silhouettes
            if next(card for card in program.cards if card.card_id == silhouette.card_id).semantic_type == "metric_bundle"
            and sum(
                fact["field"] == "metric_series_64"
                for fact in self.packet["facts"]
                if fact["fact_id"] in next(card for card in program.cards if card.card_id == silhouette.card_id).fact_ids
            ) > 4
        ]
        self.assertTrue(dense_metric)
        self.assertTrue(all((item.width_cells, item.height_cells) == (4, 4) for item in dense_metric))
        _png, manifest = render_dashboard_design(self.packet, target)
        self.assertEqual(manifest["clipping_audit"]["status"], "passed")

    def test_all_registered_designs_pack_and_scaled_geometry_stays_in_card(self) -> None:
        for spec in space_filling_specs(self.parent, self.packet["fact_inventory_hash"]):
            _png, manifest = render_dashboard_design(self.packet, spec)
            self.assertEqual(manifest["clipping_audit"]["status"], "passed")
            self.assertFalse(manifest["clipping_audit"]["card_local_overflow"])
            for row in manifest["fact_mapping"]:
                owner = row["bbox"]
                for primitive in row["primitive_geometry"]:
                    bbox = primitive.get("bbox")
                    if bbox:
                        self.assertGreaterEqual(bbox[0], owner[0])
                        self.assertGreaterEqual(bbox[1], owner[1])
                        self.assertLessEqual(bbox[2], owner[2])
                        self.assertLessEqual(bbox[3], owner[3])

    def test_composer_sft_trace_replays_exact_spec(self) -> None:
        target = space_filling_specs(self.parent, self.packet["fact_inventory_hash"])[31]
        program = compile_dashboard_program(self.packet, target)
        cards = build_evidence_cards(self.packet)
        initial = ComposerStateV1(
            case_evidence_hash=self.packet["packet_hash"], partial_spec={
                "design_id": target.design_id, "design_role": target.design_role,
                "renderer_parent_hash": target.renderer_parent_hash,
                "fact_inventory_hash": target.fact_inventory_hash,
            }, remaining_fact_budget=len(self.packet["facts"]),
            remaining_pixel_budget=target.canvas_size[0] * target.canvas_size[1],
            remaining_token_budget=32768,
            available_card_ids=tuple(card.card_id for card in cards),
        )
        state = replay_composer_sft_trace(initial, composer_sft_actions(program))
        self.assertEqual(len(state.history), 5)
        self.assertEqual(state.state_hash, state.state_hash)
        example = compile_composer_sft_example(initial, program)
        self.assertEqual(len(example["transitions"]), 5)
        self.assertEqual(example["final_state_hash"], state.state_hash)

    def test_every_selected_card_has_exactly_one_equal_fact_silhouette(self) -> None:
        program = compile_dashboard_program(self.packet, self.base_spec)
        self.assertTrue(any(len(card.fact_ids) > 1 for card in program.cards))
        self.assertEqual(len(program.cards), len(program.silhouettes))
        self.assertEqual({card.card_id for card in program.cards}, {item.card_id for item in program.silhouettes})
        self.assertEqual(
            {card.card_id: card.fact_inventory_hash for card in program.cards},
            {item.card_id: item.fact_inventory_hash for item in program.silhouettes},
        )
        occupied = sum(item.width_cells * item.height_cells for item in program.placements)
        self.assertEqual(occupied + program.empty_cells, self.base_spec.capacity_cells)

    def test_sparse_atomic_renderer_is_only_an_explicit_control(self) -> None:
        composite = build_evidence_cards(self.packet)
        sparse = build_evidence_cards(self.packet, "sparse_atomic_control")
        self.assertLess(len(composite), len(sparse))
        self.assertTrue(any(len(card.fact_ids) > 1 for card in composite))
        metric_sparse = [card for card in sparse if card.semantic_type == "metric_series"]
        self.assertTrue(metric_sparse)
        self.assertTrue(all(len(card.fact_ids) == 1 for card in metric_sparse))

    def test_composer_attribution_balances_sibling_and_telescoping_credit(self) -> None:
        rows = []
        for value, mrr in (("heatmap", 0.2), ("lines", 0.6)):
            rows.append({
                "status": "complete", "model": "qwen", "dataset": "aegislab",
                "opaque_incident_id": "INC-A", "score": {"mrr": mrr},
                "call": {"input_tokens": 100},
                "composer_attribution": {"kind": "matched_sibling", "anchor_state_hash": "S1", "action": "metric_encoding", "action_value": value},
            })
        for index, mrr in enumerate((0.1, 0.3, 0.4)):
            rows.append({
                "status": "complete", "model": "qwen", "dataset": "aegislab",
                "opaque_incident_id": "INC-A", "score": {"mrr": mrr},
                "composer_attribution": {"kind": "telescoping", "ledger_id": "L1", "stage_index": index},
            })
        for role, mrr in (("final", 0.6), ("reverted", 0.35)):
            rows.append({
                "status": "complete", "model": "qwen", "dataset": "aegislab",
                "opaque_incident_id": "INC-A", "score": {"mrr": mrr},
                "composer_attribution": {"kind": "component_reversion", "intervention_id": "I1", "component": "resolution", "role": role},
            })
        for checkpoint, mrr in (("base", 0.2), ("sft", 0.2), ("rl", 0.55)):
            rows.append({
                "status": "complete", "model": "qwen", "dataset": "aegislab",
                "opaque_incident_id": "INC-A", "score": {"mrr": mrr},
                "composer_checkpoint": checkpoint,
            })
        for left, right, mrr in ((0, 0, 0.1), (1, 0, 0.2), (0, 1, 0.25), (1, 1, 0.5)):
            rows.append({
                "status": "complete", "model": "qwen", "dataset": "aegislab",
                "opaque_incident_id": "INC-A", "score": {"mrr": mrr},
                "composer_attribution": {"kind": "component_interaction_2x2", "interaction_id": "metric_x_resolution", "left_on": left, "right_on": right},
            })
        result = composer_attribution(rows)
        credits = sorted(row["rr_credit"] for row in result["matched_sibling_credit"])
        self.assertAlmostEqual(credits[0], -0.4)
        self.assertAlmostEqual(credits[1], 0.4)
        self.assertAlmostEqual(result["ordered_telescoping"][0]["accounting_residual"], 0.0)
        self.assertAlmostEqual(result["controlled_component_reversions"][0]["controlled_effect"], 0.25)
        self.assertAlmostEqual(result["registered_component_interactions"][0]["difference_in_differences"], 0.15)
        self.assertAlmostEqual(result["checkpoint_deltas"][0]["successive_deltas"]["sft_to_rl"], 0.35)

    def test_content_policy_and_twin_equality(self) -> None:
        prepared = PreparedCase({"packet": self.packet}, {}, b"", ())
        for policy in CONTENT_POLICIES:
            twin = build_twins(prepared, self.base_spec, policy)
            selected = {str(row["fact_id"]) for row in twin.canvas_manifest["fact_mapping"]}
            filtered = filter_packet(self.packet, policy_regions(policy), selected)
            self.assertEqual(twin.fact_inventory_hash, filtered["fact_inventory_hash"])
            self.assertEqual(twin.canvas_manifest["fact_inventory_hash"], filtered["fact_inventory_hash"])
            self.assertEqual(
                {row["fact_id"] for row in twin.text_mapping},
                {row["fact_id"] for row in filtered["facts"] if row["region"] in {"M", "R", "L", "G"}},
            )
            self.assertEqual(parse_compact_evidence(twin.compact_fragment), semantic_packet_facts(filtered))
            self.assertEqual(
                {row["fact_id"] for row in twin.compact_mapping},
                {row["fact_id"] for row in filtered["facts"] if row["region"] in {"M", "R", "L", "G"}},
            )
            question, gold = packed_operations(self.packet, filtered)
            self.assertEqual(len(question["operations"]), 7)
            self.assertEqual(set(dict(gold.answerable)), {row["operation_id"] for row in question["operations"]})

    def test_deterministic_tool_profiles_are_label_blind_and_have_equal_fact_twins(self) -> None:
        prepared = PreparedCase({"packet": self.packet}, {}, b"", ())
        for profile in TOOL_PROFILES:
            first = build_tool_packet(self.packet, profile, entity_budget=2)
            second = build_tool_packet(self.packet, profile, entity_budget=2)
            self.assertEqual(first, second)
            audit = first["tool_selection_audit"]
            self.assertFalse(audit["label_access"])
            self.assertEqual(audit["model_calls"], 0)
            self.assertNotIn("ground_truth", json.dumps(first))
            self.assertTrue(all(
                audit["retained_rows"][region] <= TOOL_REGION_ROW_CAPS[region]
                for region in ("M", "R", "L", "G")
            ))
            twin = build_twins(
                prepared, self.base_spec, "FULL", source_packet_override=first,
            )
            canvas_ids = {str(row["fact_id"]) for row in twin.canvas_manifest["fact_mapping"]}
            text_ids = {str(row["fact_id"]) for row in twin.text_mapping}
            self.assertEqual(canvas_ids, text_ids)
            self.assertEqual(twin.fact_inventory_hash, first["fact_inventory_hash"])

    def test_dense_top24_canvas_and_text_are_equal_fact_twins(self) -> None:
        extra = []
        for index in range(12, 24):
            extra.append(_fact("M", "metric_series_64", {
                "panel_id": f"M{index + 1:02d}", "service": "123" if index < 18 else "456",
                "metric": f"metric.{index}", "rank": index + 1,
                "values": [str((index + value) % 11) for value in range(64)],
                "peak": str(index + 10), "signed_z": str(index / 3),
            }, ("123" if index < 18 else "456",)))
        dense_source = {
            **self.packet,
            "facts": sorted((*self.packet["facts"], *extra), key=lambda row: (row["region"], row["field"], row["fact_id"])),
        }
        dense_source["fact_inventory_hash"] = stable_hash(dense_source["facts"])
        dense_source["packet_hash"] = stable_hash({key: value for key, value in dense_source.items() if key != "packet_hash"})
        dense_packet = _expand_metric_packet(self.packet, dense_source)
        prepared = PreparedCase({"packet": self.packet, "dense_packet": dense_packet}, {}, b"", ())
        twin = build_twins(prepared, self.base_spec, DENSE_CONTENT_POLICY)
        canvas_ids = {str(row["fact_id"]) for row in twin.canvas_manifest["fact_mapping"]}
        text_ids = {str(row["fact_id"]) for row in twin.text_mapping}
        self.assertEqual(canvas_ids, text_ids)
        self.assertEqual(twin.fact_inventory_hash, dense_packet["fact_inventory_hash"])
        self.assertEqual(sum(fact["field"] == "metric_series_64" for fact in dense_packet["facts"]), 24)
        metric_cards = [
            row for row in twin.canvas_manifest["cards"]
            if row["card"]["semantic_type"] == "metric_bundle"
        ]
        self.assertEqual(len(metric_cards), 3)
        self.assertTrue(all(row["silhouette"]["encoding"] == "overlay_lines" for row in metric_cards))

    def test_packed_operations_are_visible_and_exactly_scorable(self) -> None:
        public, gold = packed_operations(self.packet)
        self.assertEqual(len(public["operations"]), 7)
        metric_question = next(
            row["question"] for row in public["operations"]
            if row["operation_id"] == "metric_read"
        )
        self.assertIn("explicitly printed peak value", metric_question)
        score = score_packed_qa(gold.as_dict(), gold)
        self.assertTrue(score["complete_chain"])
        self.assertEqual(score["operation_accuracy"], 1.0)

        display_response = gold.as_dict()
        display_response["trace_read"] = ["42", display_response["trace_read"][1]]
        display_response["log_read"][0] = f"b{display_response['log_read'][0]}"
        self.assertEqual(score_packed_qa(display_response, gold)["operation_accuracy"], 1.0)
        display_response["metric_read"] = ["not-the-peak"]
        self.assertEqual(score_packed_qa(display_response, gold)["operation_scores"]["metric_read"], 0.0)
        self.assertTrue(_qa_value_equal("metric_read", 0, "878M", "8.776e+08"))
        self.assertTrue(_qa_value_equal("trace_read", 0, "1.58k", "1580.75"))
        self.assertFalse(_qa_value_equal("trace_read", 0, "1.6k", "1580.75"))

    def test_registered_visual_treatments_change_pixels_and_order(self) -> None:
        base = self.base_spec
        variants = (
            DashboardSpecV1(**{**base.__dict__, "metric_encoding": "overlay_lines"}),
            DashboardSpecV1(**{**base.__dict__, "trace_encoding": "trace_baseline_fault_bars"}),
            DashboardSpecV1(**{**base.__dict__, "log_encoding": "template_time_matrix"}),
            DashboardSpecV1(**{**base.__dict__, "topology_encoding": "edge_table"}),
            DashboardSpecV1(**{**base.__dict__, "propagation_encoding": "propagation_timeline"}),
            DashboardSpecV1(**{**base.__dict__, "coordination_mode": "shared_entity"}),
        )
        hashes = {hashlib.sha256(render_dashboard_design(self.packet, spec)[0]).hexdigest() for spec in (base, *variants)}
        self.assertEqual(len(hashes), 1 + len(variants))
        stable = compile_dashboard_program(self.packet, base)
        salience = compile_dashboard_program(self.packet, DashboardSpecV1(**{**base.__dict__, "entity_order": "salience_onset"}))
        self.assertNotEqual(stable.placements, salience.placements)

    def test_missing_metric_is_a_gap_and_topology_is_a_real_primitive(self) -> None:
        _png, manifest = render_dashboard_design(self.packet, self.base_spec)
        metric = next(row for row in manifest["fact_mapping"] if row["fact_id"] == next(f["fact_id"] for f in self.packet["facts"] if f["field"] == "metric_series_64" and f["payload"]["panel_id"] == "M01"))
        bins = metric["primitive_geometry"][0]["bin_primitives"]
        self.assertTrue(any(row["bin"] == 20 and row["missing"] for row in bins))
        edge = next(row for row in manifest["fact_mapping"] if row["fact_id"] == next(f["fact_id"] for f in self.packet["facts"] if f["field"] == "directed_call_edge"))
        self.assertEqual(edge["primitive_geometry"][0]["kind"], "directed_arrow")

    def test_blank_and_reflow_share_facts_but_not_layout(self) -> None:
        prepared = PreparedCase({"packet": self.packet}, {}, b"", ())
        reflow = build_twins(prepared, self.base_spec, "B50_RANDOM", "reflow")
        blank = build_twins(prepared, self.base_spec, "B50_RANDOM", "blank")
        self.assertEqual(reflow.fact_inventory_hash, blank.fact_inventory_hash)
        self.assertEqual(
            {row["fact_id"] for row in reflow.canvas_manifest["fact_mapping"]},
            {row["fact_id"] for row in blank.canvas_manifest["fact_mapping"]},
        )
        self.assertNotEqual(reflow.canvas_manifest["program_hash"], blank.canvas_manifest["program_hash"])
        self.assertGreater(
            reflow.canvas_manifest["packing_audit"]["occupancy"],
            blank.canvas_manifest["packing_audit"]["occupancy"],
        )

    def test_evidence_bundle_round_trip(self) -> None:
        bundle = RQ2EvidenceBundleV1.from_packet(self.packet)
        self.assertEqual(bundle.fact_inventory_hash, self.packet["fact_inventory_hash"])
        self.assertEqual(bundle.candidates, ("123", "456"))

    def test_common_shell_lists_candidates_once(self) -> None:
        packet = {
            "candidates": ["123", "456"],
            "facts": [
                _fact("C", "candidate_set", {"fixed_order": ["123", "456"], "count": 2}, ("123", "456")),
                _fact("C", "relative_window", {"start": 0, "end": 60}),
            ],
        }
        shell = _common_shell(packet)
        self.assertEqual(shell.count('["123","456"]'), 1)
        self.assertNotIn("field=candidate_set", shell)
        self.assertIn("field=relative_window", shell)

    def test_rq2_prompt_is_minimal_sircl_adaptation_and_guides_stay_separate(self) -> None:
        from RQs.RQ1_1.src.exps import SIRCL_STAR_RCA_PROCEDURE as parent_prompt

        prompt = direct_rca_prompt(self.packet)
        design_control = (
            "RQ2 may vary which public evidence cards are supplied and how selected facts are encoded, "
            "positioned, sized, ordered, styled, or rasterized. Treat those design choices as presentation "
            "or control variables, not diagnostic facts. Use only the M/R/L/G facts actually supplied; blank "
            "or omitted evidence is unavailable under that registered condition, not zero and not evidence "
            "against an entity."
        )
        expected = parent_prompt.replace(
            "twelve selected entity/metric series",
            "the supplied selected entity/metric series",
        ).replace(
            "\n\nUse the selected SIRCL* diagnostic discipline",
            f"\n\n{design_control}\n\nUse the selected SIRCL* diagnostic discipline",
        )
        self.assertEqual(prompt, expected)
        self.assertEqual(RQ2_PROMPT_ADAPTATION_ID, "sircl_star_minimal_rq2_v1")
        self.assertEqual(hashlib.sha256(parent_prompt.encode()).hexdigest(), SIRCL_STAR_PROMPT_PARENT_SHA256)
        for phrase in (
            "Use the selected SIRCL* diagnostic discipline in M -> R -> L -> G order",
            "MET-Z analyzer", "TRC-L analyzer", "LOG-R analyzer",
            "INITIAL:", "VERIFY:", "REVISE:", design_control,
        ):
            self.assertIn(phrase, prompt)
        self.assertEqual(rq2_representation_guide("text"), "")
        visual = rq2_representation_guide("rq2_dashboard")
        for phrase in ("square-cell grid", "coordinated visual encoding", "adjacency matrix", "content-budget"):
            self.assertIn(phrase, visual)
        for phrase in (
            "onset +21.0m", "2.34ks", "Δlog2=+1", "volume_drop_x30",
            "rows are callers", "not the ground-truth injection time",
            "M16 7425", "exactly 3 digits means service",
            "19783 · grpc.hipstershop.535/Charge",
        ):
            self.assertIn(phrase, visual)
        self.assertIn("not a telemetry dashboard", rq2_representation_guide("pixel_text"))

    def test_rq2_typography_fields_do_not_leak_into_parent_renderer_overrides(self) -> None:
        config = yaml.safe_load((PROJECT_ROOT / "RQs/RQ2/configs/rq2.yaml").read_text())
        renderer = config["renderer"]
        self.assertEqual(float(renderer["typography_baseline_scale"]), 1.18)
        self.assertNotIn("typography_baseline_scale", renderer["overrides"])
        self.assertNotIn("typography_rule", renderer["overrides"])
        dashboard_config(config)

    def test_rq1_1_non_prompt_experiment_protocol_was_not_copied_into_rq2(self) -> None:
        source = (PROJECT_ROOT / "RQs/RQ2/src/exps.py").read_text()
        forbidden = (
            "FACTORIAL_ARM_REGIONS", "questions_for_case", "planner_schema",
            "temporary_schema", "execute_tool", "multi_stage_analysis_parts",
            "SIRCL_STAR_RCA_PROCEDURE", "reasoning_trace_svg",
        )
        for symbol in forbidden:
            self.assertNotIn(symbol, source)

    def test_unified_inference_hash_is_frozen(self) -> None:
        path = PROJECT_ROOT / "configs/vllm_inference_local.yaml"
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), "4f7ee9fe4f9ecb448116a22bf85d6dafc468d10cb46f5868ff74967fc3ae886c")

    def test_execution_and_smokes_are_bounded(self) -> None:
        config = yaml.safe_load((PROJECT_ROOT / "RQs/RQ2/configs/rq2.yaml").read_text())
        # The protocol is fail-closed until smoke qualification.  Once the
        # explicitly recorded authorization is present, the same invariant
        # guards the enabled state instead of permanently forbidding formal
        # execution.
        if config["execution_enabled"]:
            self.assertEqual(config["status"], "smoke_qualified_formal_authorized_rca_only")
        else:
            self.assertNotEqual(config["status"], "smoke_qualified_formal_authorized_rca_only")
        self.assertEqual(config["runtime"]["deployment"], "local_wsl_only")
        self.assertTrue(config["runtime"]["slurm_submission_forbidden"])
        self.assertEqual(config["unified"]["vllm"], "configs/vllm_inference_local.yaml")
        self.assertEqual(config["solver"]["checkpoint_root_env"], "CANVASRCA_MODEL_ROOT")
        self.assertFalse(config["solver"]["weights_trainable_in_rq2"])
        self.assertEqual(
            config["composer"]["model_path"],
            "${CANVASRCA_COMPOSER_MODEL}",
        )
        self.assertFalse(config["composer"]["execution_in_rq2"])
        self.assertFalse(config["composer"]["training_in_rq2"])
        main_source = (PROJECT_ROOT / "RQs/RQ2/src/main.py").read_text()
        self.assertNotIn("serve_canvasrca_" + "nibi.sh", main_source)
        self.assertTrue(all(row["total_calls"] <= 18 for row in config["smoke_plans"].values()))
        self.assertEqual(config["runtime"]["smoke_timeout_seconds_total"], 600)
        self.assertEqual(config["runtime"]["max_workers"], 8)
        calls = config["runtime"]["registered_formal_calls_after_v3"]
        self.assertEqual(calls["total"], sum(value for key, value in calls.items() if key != "total"))
        self.assertLessEqual(calls["total"], config["runtime"]["major_rq_call_cap"])

    def test_scheduler_uses_eight_distinct_physical_cores_and_interleaves_cases(self) -> None:
        cpu_ids = _physical_cpu_ids(8)
        self.assertEqual(len(cpu_ids), 8)
        self.assertEqual(len(set(cpu_ids)), 8)
        cases = [
            [(f"case-{case}", {"unit_id": f"u{unit}"}) for unit in range(3)]
            for case in range(5)
        ]
        ordered = _round_robin_case_tasks(cases)
        self.assertEqual([row[0] for row in ordered[:5]], [f"case-{case}" for case in range(5)])
        for case in range(5):
            self.assertEqual(
                [row[1]["unit_id"] for row in ordered if row[0] == f"case-{case}"],
                ["u0", "u1", "u2"],
            )

    def test_optimized_anonymizer_preserves_sequential_semantics(self) -> None:
        mapping = {"svc": "111", "svc-a": "222"}
        for sample in ("svc-a then SVC-A", "prefix svc-a-suffix", "unrelated"):
            legacy = sample
            for natural in sorted(mapping, key=len, reverse=True):
                legacy = re.sub(re.escape(natural), mapping[natural], legacy, flags=re.IGNORECASE)
            self.assertEqual(_anonymize_text(sample, mapping), legacy)

    def test_resume_requires_artifact_hashes_and_conversation(self) -> None:
        expected = {
            "contract_sha256": "contract", "experiment": "experiment",
            "model": "model", "opaque_incident_id": "incident", "unit_id": "unit",
            "prepared_evidence_sha256": "evidence",
            "evaluator_private_sha256": "private",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "terminal.json"
            record = {"status": "complete", **expected}
            record["record_sha256"] = stable_hash(record)
            path.write_text(json.dumps(record))
            path.with_suffix(".md").write_text("conversation")
            self.assertTrue(_valid_record(path, expected))
            changed = {**expected, "prepared_evidence_sha256": "changed"}
            self.assertFalse(_valid_record(path, changed))
            path.with_suffix(".md").unlink()
            self.assertFalse(_valid_record(path, expected))
            prepared = PreparedCase(
                {"opaque_incident_id": "INC-RESUME"}, {"labels": ["private"]},
                b"full", (b"screenshot",),
            )
            paths = RunPaths(Path(directory) / "prepared-run")
            item = _persist_prepared(paths, prepared)
            _read_prepared(paths, item)
            (paths.root / item["full_image"]).write_bytes(b"corrupt")
            with self.assertRaises(RQ2Error):
                _read_prepared(paths, item)

    def test_eight_materializers_are_pinned_and_emit_complete_requests(self) -> None:
        cpu_ids = _physical_cpu_ids(8)
        prepared = PreparedCase(
            {"packet": self.packet, "opaque_incident_id": self.packet["opaque_incident_id"]},
            {"dataset": "synthetic", "fault_type": "synthetic"}, b"", (),
        )
        specs = space_filling_specs(self.parent, self.packet["fact_inventory_hash"])
        units = [
            {"unit_id": f"{spec.cell_id}__one_stage_rca", "task": "one_stage_rca", "spec": spec}
            for spec in specs[:8]
        ]
        with ProcessPoolExecutor(
            max_workers=8, mp_context=mp.get_context("spawn"),
            initializer=_pin_materializer, initargs=(cpu_ids,),
        ) as pool:
            rows = list(pool.map(
                _materialize_unit,
                ["exp_equal_fact_design"] * 8, ["qwen3.8-27b"] * 8,
                [prepared] * 8, units, ["scheduler-test"] * 8,
            ))
        affinities = [tuple(row["materializer_affinity"]) for row in rows]
        self.assertTrue(all(len(value) == 1 and value[0] in cpu_ids for value in affinities))
        self.assertEqual(set(affinities), {(cpu,) for cpu in cpu_ids})
        self.assertTrue(all(row["parts"] and row["image"] for row in rows))

    def test_attention_generation_sidecar_is_not_rewritten_per_token(self) -> None:
        state = {
            "generation_target_count": 3, "generation_target_seen": 3,
            "payload": {"request_id": "response"},
            "engine_request_id": "engine", "response_request_id": "response",
        }
        with patch(
            "vlmrca.vlm.attention_probe._generation_profile",
            return_value={"status": "collected"},
        ), patch("vlmrca.vlm.attention_probe._write_sidecar") as write:
            _publish_generation_profile(state)
            _publish_generation_profile(state)
            self.assertEqual(write.call_count, 2)
            state["generation_target_count"] = 4
            _publish_generation_profile(state)
            self.assertEqual(write.call_count, 4)

    def test_attention_tracks_rca_and_retained_abandoned_qa_answer_arrays(self) -> None:
        expected = {
            "services", "values", "metric_read", "trace_read", "log_read",
            "temporal_onset", "directed_path", "cross_source_alignment", "missingness",
        }
        self.assertEqual(set(_ANSWER_ARRAY_FIELDS), expected)
        for field in sorted(expected):
            self.assertFalse(_inside_registered_answer_field(f'{{"{field}":'))
            self.assertTrue(_inside_registered_answer_field(f'{{"{field}":["answer"'))
            self.assertFalse(_inside_registered_answer_field(f'{{"{field}":["answer"]'))

    def test_zero_visual_attention_is_a_valid_diagnostic(self) -> None:
        stream = io.BytesIO()
        Image.new("RGB", (32, 32), "white").save(stream, format="PNG")
        probe = {
            "method": "unit-test", "request_id": "zero-mass", "model": "qwen3.8-27b",
            "layer_name": "layer", "image_token_id": 1,
            "image_groups": [{
                "weights": [0.0] * 4, "value_norms": [1.0] * 4,
                "attention_weighted_value_norms": [0.0] * 4,
                "weighted_value_diagnostic_available": False,
            }],
        }
        geometry = {
            "source_token_grid": [2, 2],
            "source_token_boxes_px": [[0, 0, 16, 16], [16, 0, 32, 16],
                                      [0, 16, 16, 32], [16, 16, 32, 32]],
        }
        artifact = map_groups_to_images(
            probe, [stream.getvalue()], model_path="unused",
            geometry_override=geometry,
        )[0]
        self.assertEqual(artifact["global_attention_mass"], 0.0)
        self.assertEqual(artifact["mesh_normalization_status"], "zero_attention_mass")
        self.assertTrue(all(value == 0.0 for value in artifact["weights"]))

    def test_sparse_area_mapping_matches_registered_dense_definition(self) -> None:
        width, height, columns, rows = 191, 107, 11, 7
        x_edges = [round(index * width / columns) for index in range(columns + 1)]
        y_edges = [round(index * height / rows) for index in range(rows + 1)]
        boxes = [
            [x_edges[column], y_edges[row], x_edges[column + 1], y_edges[row + 1]]
            for row in range(rows) for column in range(columns)
        ]
        source = [((index * 17) % 31) / 31 for index in range(len(boxes))]
        target_columns, target_rows = 16, 16
        target_x = [round(index * width / target_columns) for index in range(target_columns + 1)]
        target_y = [round(index * height / target_rows) for index in range(target_rows + 1)]
        cells = [
            [target_x[column], target_y[row], target_x[column + 1], target_y[row + 1]]
            for row in range(target_rows) for column in range(target_columns)
        ]
        for mass in (True, False):
            expected = []
            for cell in cells:
                overlaps = [_intersection_area(box, cell) for box in boxes]
                if mass:
                    value = sum(
                        item * overlap / max(1, (box[2] - box[0]) * (box[3] - box[1]))
                        for item, box, overlap in zip(source, boxes, overlaps, strict=True)
                    )
                else:
                    total = sum(overlaps)
                    value = sum(
                        item * overlap for item, overlap in zip(source, overlaps, strict=True)
                    ) / total if total else 0.0
                expected.append(value)
            actual, _density = _area_map(
                source, boxes, (width, height), (target_columns, target_rows), mass=mass,
            )
            self.assertTrue(all(abs(left - right) < 1e-12 for left, right in zip(actual, expected)))

    def test_flat_metric_renders_as_zero_sigma_line(self) -> None:
        self.assertEqual(
            _metric_z(
                {"sircl_met_z": {"regular_mean": 7.5, "regular_std_dev": 0.0}},
                [7.5, 7.5, None, 7.5],
            ),
            [0.0, 0.0, None, 0.0],
        )

    def test_d_star_is_structural_not_case_bound_and_qa_independent(self) -> None:
        records = []
        for spec in space_filling_specs(self.parent, self.packet["fact_inventory_hash"]):
            records.append({
                "status": "complete", "task": "one_stage_rca", "model": "qwen3.8-27b",
                "dataset": "aegislab", "opaque_incident_id": "INC-A",
                "unit_id": f"{spec.cell_id}__one_stage_rca", "design_spec": spec.__dict__,
                "score": {"mrr": 0.5}, "call": {"input_tokens": 100},
            })
        selected = analyze_records(records, "exp_equal_fact_design", {"abandoned_tasks": {"packed_qa": {}}}, select=True)["selection"]
        self.assertEqual(selected["d_star"]["fact_inventory_hash"], "")

    def test_packed_qa_is_preserved_but_not_an_active_rq2_task(self) -> None:
        config = yaml.safe_load((PROJECT_ROOT / "RQs/RQ2/configs/rq2.yaml").read_text())
        self.assertEqual(config["abandoned_tasks"]["packed_qa"]["status"], "abandoned")
        self.assertTrue(all(
            tasks == ["one_stage_rca"]
            for tasks in (row["tasks"] for row in config["experiments"].values())
        ))
        self.assertEqual(tuple(config["experiments"]["exp_downstream_transfer"]["arms"]), TRANSFER_ARMS)
        self.assertEqual(len(TRANSFER_ARMS), 14)

    def test_request_performance_math_and_prometheus_parser(self) -> None:
        value = request_timing_summary(request_elapsed_s=4, first_content_s=1, last_content_s=3,
                                       output_tokens=5, content_arrivals_s=[1, 2, 3], content_chunks=3)
        self.assertEqual((value["ttft_s"], value["decode_time_s"], value["tpot_s"]), (1, 2, .5))
        self.assertEqual(parse_prometheus_metric("vllm:gpu_cache_usage_perc 0.25\n", "vllm:gpu_cache_usage_perc"), [.25])

    def test_no_old_rq2_roster_or_qwen36_path(self) -> None:
        roster_names = {path.name for path in (PROJECT_ROOT / "RQs/RQ2/configs/rosters").glob("*.json")}
        self.assertTrue(roster_names)
        self.assertTrue(all(name.endswith("_v3.json") for name in roster_names))
        self.assertFalse(any("fresh_roster" in name for name in roster_names))
        source = "\n".join(path.read_text() for path in (PROJECT_ROOT / "RQs/RQ2/src").glob("*.py"))
        self.assertNotIn("Qwen" + "3.6", source)


if __name__ == "__main__":
    unittest.main()
