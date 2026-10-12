"""CPU-only registration/selection tests; no model calls and no fake smoke."""

from __future__ import annotations

import ast
import copy
import hashlib
import tempfile
import types
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from unified_scripts.token_admission import TokenAdmission

from .exps import (
    EvidenceUniverseV1,
    NativeTelemetryV1,
    item_similarity,
    select_evidence,
)
from .gates import execution_gate, verify_parent_copy
from .utils import (
    ROOT,
    RQ_ROOT,
    CallLedger,
    ProtocolError,
    RQ21SegmentationAdapter,
    load_config,
    overlap_groups,
    read_json,
    subset_groups,
)


def fixture():
    items = tuple(
        {
            "item_id": f"m{i}",
            "region": "M",
            "entity_ids": [str(100 + i // 2)],
            "source_ids": [f"column:{i}"],
            "family": "latency",
            "unit": "ms",
            "values": list(range(64)) if i < 12 else list(range(63, -1, -1)),
            "relevance": float(100 - i),
        }
        for i in range(24)
    )
    return EvidenceUniverseV1(
        "INC-ABC123",
        tuple(str(i) for i in range(100, 112)),
        items,
        {"M": tuple(f"m{i}" for i in range(12)), "R": (), "L": (), "G": ()},
        {"M": 12, "R": 0, "L": 0, "G": 0},
        "fixed-statistics",
        "source-columns",
    )


class RegistrationTests(unittest.TestCase):
    def test_projected_service_ordinal_is_not_projected_twice(self):
        from .renderer.onset import compute_service_onsets, pod_to_service

        service = pod_to_service("example-ant-10-29153760-dkvdq")
        self.assertEqual(service, "example-ant-10")
        frame = pd.DataFrame()
        actual = compute_service_onsets(frame, frame, [], None, None, [service], services_are_projected=True)
        self.assertEqual(list(actual), [service])

    def test_transitive_overlap_is_indivisible(self):
        rows = [
            {"opaque": name, "source": "one", "event": name, "start": a, "end": b}
            for name, a, b in (("a", 0, 2), ("b", 1, 3), ("c", 2.5, 4), ("d", 6, 7))
        ]
        self.assertEqual(sorted(overlap_groups(rows)), [["a", "b", "c"], ["d"]])
        self.assertEqual(subset_groups(overlap_groups(rows), 3), ["a", "b", "c"])
        with self.assertRaises(ProtocolError):
            subset_groups(overlap_groups(rows), 2)

    def test_different_sources_do_not_overlap(self):
        rows = [{"opaque": s, "source": s, "event": "same", "start": 0, "end": 5} for s in ("a", "b")]
        self.assertEqual(len(overlap_groups(rows)), 2)

    def test_roster_deterministic_and_grouped(self):
        original = read_json(RQ_ROOT / "configs/rosters/public.json")
        public, private = RQ21SegmentationAdapter(load_config()).materialize()
        self.assertEqual(original, public)
        selection = {r["opaque_incident_id"] for r in public["cases"] if r["role"] == "selection"}
        self.assertEqual(len(public["cases"]), 480)
        self.assertEqual(len(selection), 90)
        for dataset, groups in public["groups"].items():
            self.assertEqual(
                sum(r["role"] == "selection" and r["dataset"] == dataset for r in public["cases"]),
                30,
            )
            for group in groups:
                self.assertIn(len(set(group) & selection), (0, len(group)))
        self.assertNotIn("source_windows", public)
        self.assertIn("source_windows", private)

    def test_parent_byte_identity(self):
        self.assertTrue(verify_parent_copy()["passed"])

    def test_budget_and_repeat_attempts(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = CallLedger(Path(directory) / "calls.sqlite", ceiling=3)
            attempt = ledger.begin("model-A:input", "smoke", 2)
            with self.assertRaises(ProtocolError):
                ledger.begin("model-A:input", "smoke", 2)
            ledger.finish(attempt, "interrupted")
            attempt = ledger.begin("model-A:input", "smoke", 2)
            ledger.finish(attempt, "infrastructure_failure")
            with self.assertRaises(ProtocolError):
                ledger.begin("model-B:input", "smoke", 2)
            ledger.begin("model-B:input", "formal")
            with self.assertRaises(ProtocolError):
                ledger.begin("new", "formal")

    def test_execution_fails_closed(self):
        report = execution_gate({**load_config(), "execution_enabled": False})
        self.assertFalse(report["passed"])
        self.assertIn("execution_disabled", report["blockers"])


class SelectionTests(unittest.TestCase):
    def test_p0_exact_and_no_mutation(self):
        u = fixture()
        before = copy.deepcopy(u)
        result = select_evidence(u, "P0")
        self.assertEqual(result.selected, u.parent_order)
        self.assertEqual(u, before)
        self.assertEqual(result.statistics_hash, "fixed-statistics")

    def test_formal_twelve_slot_interventions(self):
        u = fixture()
        parent = set(select_evidence(u, "P0").selected["M"])
        for policy in ("P_COVERAGE", "P_DIVERSITY", "P_RANDOM"):
            result = select_evidence(u, policy)
            self.assertEqual(len(result.selected["M"]), 12)
            self.assertNotEqual(set(result.selected["M"]), parent)
            self.assertEqual(result, select_evidence(u, policy))

    def test_native_missing_is_not_shared_sort(self):
        with self.assertRaises(ProtocolError):
            select_evidence(fixture(), "P_SIGMA")

    def test_native_fill_is_explicit(self):
        result = select_evidence(fixture(), "P_SIGMA", native_ranks={"M": ("m23",)})
        self.assertEqual(result.selected["M"][0], "m23")
        self.assertEqual(len(result.filled["M"]), 11)
        with self.assertRaises(ProtocolError):
            select_evidence(fixture(), "P_SIGMA", native_ranks={"M": ("missing",)})

    def test_similarity_directions_missing_constants(self):
        a, b = dict(fixture().items[0]), dict(fixture().items[1])
        self.assertAlmostEqual(item_similarity(a, b), 1.0)
        b["values"] = list(reversed(a["values"]))
        self.assertEqual(item_similarity(a, b), 0)
        a["values"], b["values"] = [1, None, 1], [1, 0, 1]
        self.assertEqual(item_similarity(a, b), 0)
        b["values"] = [1, None, 1]
        self.assertEqual(item_similarity(a, b), 1)
        b["unit"] = "seconds"
        self.assertEqual(item_similarity(a, b), 0)

    def test_bad_score_not_zero_and_bad_id_rejected(self):
        u = fixture()
        changed = dict(u.items[0], relevance="missing")
        with self.assertRaises(ProtocolError):
            select_evidence(replace(u, items=(changed, *u.items[1:])), "P_DIVERSITY")
        changed = dict(u.items[0], entity_ids=["natural-service-name"])
        with self.assertRaises(ProtocolError):
            replace(u, items=(changed, *u.items[1:])).validate()


def original_component(relative_path):
    """Load the actual preserved source for CPU differential tests only.

    Remove only the unused external DataCase type import. Numeric code and
    output formatting execute from the original file, not a reimplementation.
    """
    path = ROOT / "packages/rq21_native/sircl_original" / relative_path
    tree = ast.parse(path.read_text(), filename=str(path))
    tree.body = [
        n
        for n in tree.body
        if not (isinstance(n, ast.ImportFrom) and any(a.name == "DataCase" for a in n.names))
    ]
    module = types.ModuleType("original_component")
    module.__package__ = "packages.rq21_native.sircl_original." + str(Path(relative_path).parent).replace(
        "/", "."
    )
    exec(compile(tree, str(path), "exec"), module.__dict__)  # noqa: S102 — execute the hash-verified reference in CPU differential tests
    return module


def native_fixture():
    start = 1_700_000_000.0
    clock = start + np.arange(24)
    metrics = pd.DataFrame(
        {
            "timestamp": clock,
            "101_latency": [1, 2, 3, 4] * 3 + [20, 21, 22, 23] * 3,
            "102_latency": [1, 2, 3, 4] * 3 + [-100, -99, -98, -97] * 3,
            "101_constant": [2] * 24,
        }
    )
    traces = pd.DataFrame(
        {
            "timestamp": clock,
            "service_name": ["101"] * 24,
            "operation_name": ["read_with,commas_and_a_long_name" * 4] * 24,
            "duration_ms": [1, 2, 3, 4] * 3 + [20, 21, 22, 23] * 3,
            "span_id": [f"s{i}" for i in range(24)],
            "parent_span_id": [None] * 24,
        }
    )
    logs = pd.DataFrame(
        {
            "timestamp": clock,
            "container_name": ["101", "102"] * 12,
            "message": [f"status 504 timeout at worker {i % 3}" for i in range(24)],
            "_source_row": range(24),
        }
    )
    return NativeTelemetryV1(metrics, traces, logs, ("101", "102"), start + 12)


class NativeToolTests(unittest.TestCase):
    def test_sigma_against_preserved_source(self):
        from packages.rq21_native.sircl_adapted.metrics.metrics_ma import (
            MetricsVariantMA,
        )

        original = original_component("metrics/metrics_ma.py")
        case = native_fixture()

        class Reference(original._ThinkFLCSVBase):
            def _get_split_time(self, _case):
                return case.analysis_start_s

        reference = Reference().get_metrics_context(case)
        adapted = MetricsVariantMA()
        self.assertEqual(reference, adapted.get_metrics_context(case))
        rows = adapted.get_metrics_context(case, structured=True)
        self.assertEqual([r["column"] for r in rows], ["101_latency", "102_latency"])
        self.assertTrue(all(r["_deviation"] > 3 for r in rows))

    def test_trace_against_preserved_source(self):
        from packages.rq21_native.sircl_adapted.extractors.tracerca_scorer import (
            score_operations_jaccard,
        )

        original = original_component("extractors/tracerca_scorer.py")
        case = native_fixture()
        ref = types.SimpleNamespace(traces_df=case.traces_df, timestamp=case.analysis_start_s)
        self.assertEqual(original.score_operations_jaccard(ref), score_operations_jaccard(case))
        rows = score_operations_jaccard(case, structured=True)
        self.assertGreater(len(rows[0]["operation"]), 80)
        self.assertAlmostEqual(rows[0]["jaccard"], 1.0)

    def test_log_against_preserved_source_and_binding(self):
        from packages.rq21_native.sircl_adapted.extractors.log_template_freq import (
            build_torai_template_freq,
        )

        original = original_component("extractors/log_template_freq.py")
        case = native_fixture()
        ref = types.SimpleNamespace(
            logs_df=case.logs_df,
            timestamp=case.analysis_start_s,
            services=case.services,
        )
        self.assertEqual(original.build_torai_template_freq(ref), build_torai_template_freq(case))
        rows = build_torai_template_freq(case, structured=True)
        self.assertEqual(sorted(i for r in rows for i in r["source_rows"]), list(range(12, 24)))
        self.assertEqual(sum(r["count"] for r in rows), 12)

    def test_baro_keeps_signed_max_not_absolute(self):
        from packages.rq21_native.baro_original.root_cause_analysis import robust_scorer

        case = native_fixture()
        result = robust_scorer(
            case.metrics_df.rename(columns={"timestamp": "time"}),
            inject_time=case.analysis_start_s,
        )
        self.assertEqual(result["ranks"], ["101_latency", "102_latency"])

    def test_relative_clock_is_supplied_not_inferred(self):
        from packages.rq21_native.sircl_adapted.extractors.tracerca_scorer import (
            score_operations_jaccard,
        )

        case = native_fixture()
        frame = case.traces_df.assign(_rq21_time_s=np.arange(24))
        relative = replace(case, traces_df=frame, analysis_start_s=12)
        self.assertEqual(
            score_operations_jaccard(case, structured=True),
            score_operations_jaccard(relative, structured=True),
        )

    def test_no_timestamp_or_private_label_attribute(self):
        case = native_fixture()
        for key in (
            "timestamp",
            "ground_truth",
            "fault_type",
            "case_id",
            "metadata",
            "dataset",
        ):
            self.assertFalse(hasattr(case, key))

    def test_source_hashes_unchanged(self):
        provenance = read_json(ROOT / "packages/rq21_native/PROVENANCE.json")
        for row in provenance["sircl"]["files"] + provenance["baro"]["files"]:
            path = ROOT / row.get("target", row.get("path"))
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), row["sha256"])

    def test_primitive_copy_before_adaptation(self):
        for name in ("parent_primitives", "parent_identity"):
            provenance = read_json(RQ_ROOT / "configs/provenance" / f"{name}.json")
            content = (ROOT / provenance["source"]).read_text()
            lines = content.splitlines(keepends=True)
            spans = {}
            for node in ast.parse(content).body:
                label = getattr(node, "name", None)
                if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
                    label = node.targets[0].id
                if label:
                    start = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])
                    spans[label] = "".join(lines[start - 1 : node.end_lineno])
            for row in provenance["sections"]:
                self.assertEqual(
                    hashlib.sha256(spans[row["name"]].encode()).hexdigest(),
                    row["sha256"],
                )


class ScientificContractTests(unittest.TestCase):
    def test_registered_count_and_cube(self):
        from .exps import cube_units, registered_units

        cfg = load_config()
        champions = {"P": "P_RANDOM", "S": "S_TABLE", "D": "D_AIRY"}
        counts = [len(registered_units(cfg, e, champions)) for e in cfg["experiments"]]
        self.assertEqual(counts, [16, 12, 11])
        self.assertEqual((16 + 11 + 10) * 480 * 2, cfg["budgets"]["formal_calls"])
        self.assertEqual(len(cube_units(champions)), 8)
        self.assertEqual(35520 + 54 + 4425, cfg["budgets"]["total_initiated_calls"])
        self.assertEqual(cfg["budgets"]["reserved_repair_calls"], 4425)
        for e in ("exp_silhouette_encoding", "exp_canvas_composition"):
            actual = registered_units(cfg, e, champions)
            self.assertTrue(all(u["policy"] == "P0" for u in actual))
            if e == "exp_silhouette_encoding":
                self.assertTrue(all(u["composition"] == "D0" for u in actual))
            else:
                self.assertTrue(all(u["silhouette"] == "S0" for u in actual))
        self.assertFalse(cfg["fixed_anchor"]["cube_enabled"])
        self.assertEqual(cfg["formal_order"], ["exp_silhouette_encoding", "exp_canvas_composition"])

    def test_fixed_anchor_cannot_reactivate_champion_or_cube(self):
        from .main import run_model, select_champion
        from .utils import formal_scope

        cfg = load_config()
        with self.assertRaises(ProtocolError):
            select_champion(cfg, "exp_silhouette_encoding")
        with self.assertRaises(ProtocolError):
            run_model(cfg, "exp_canvas_composition", cfg["models"][0], cube=True)
        self.assertEqual(formal_scope(cfg, "exp_silhouette_encoding"), "exp_silhouette_encoding_formal_p0_v2")

    def test_prompt_bridge_text_identity_and_visual_separation(self):
        from .exps import RCA_SYSTEM_ROLE, request_parts

        cfg = load_config()
        case = read_json(RQ_ROOT / "configs/rosters/public.json")["cases"][0]["opaque_incident_id"]
        p = read_json(ROOT / cfg["data"]["parent_prepared"] / "prepared" / f"{case}.json")["packet"]
        parts = request_parts(p)
        for model in cfg["models"]:
            stage = read_json(
                ROOT / cfg["data"]["parent_results"] / "trajectories/direct_rca" / model / f"{case}__T.json"
            )["stages"][0]
            self.assertEqual(stage["parts"][0], {"type": "text", "text": parts[0]["text"]})
            self.assertEqual(
                stage["parts"][2:],
                [{"type": "text", "text": part["text"]} for part in parts[2:]],
            )
            old_lines = stage["parts"][1]["text"].splitlines()
            new_lines = parts[1]["text"].splitlines()
            self.assertEqual(len(old_lines), len(new_lines))
            self.assertTrue(
                all(a == b or "field=propagation_meta;" in a for a, b in zip(old_lines, new_lines))
            )
            self.assertEqual(stage["system"], RCA_SYSTEM_ROLE)
            self.assertEqual(stage["requested_max_tokens"], 8192)
        self.assertNotIn("How to read the supplied telemetry dashboard", str(parts))

    def test_case_statistics_and_holm(self):
        from .exps import cube_attribution, holm, paired_statistics

        self.assertEqual(paired_statistics([1, 0], [1, 0])["p"], 1)
        self.assertEqual(
            [r["p_adjusted"] for r in holm([{"p": 0.01}, {"p": 0.04}, {"p": 0.02}])],
            [0.03, 0.04, 0.04],
        )
        cube = {
            f"{p}{s}{d}": 0.1 * p + 0.2 * s + 0.3 * d + 0.1 * p * s
            for p in (0, 1)
            for s in (0, 1)
            for d in (0, 1)
        }
        effects = cube_attribution(cube)
        self.assertAlmostEqual(sum(effects["shapley"].values()), 0.7)
        with self.assertRaises(ProtocolError):
            cube_attribution({"000": 0})

    def test_champion_never_reads_report_and_veto(self):
        from .exps import choose_champion

        rows = []
        for m in ("q", "g"):
            for d in ("a", "b", "c"):
                for arm, rr in (
                    ("S0", 0.5),
                    ("S_TABLE", 0.8 if (m, d) != ("g", "a") else 0.4),
                ):
                    rows.append(
                        {
                            "case": "c1",
                            "model": m,
                            "dataset": d,
                            "arm": arm,
                            "status": "completed",
                            "score": {"mrr": rr},
                            "input_tokens": 100,
                            "output_tokens": 20,
                        }
                    )
        result = choose_champion(
            rows,
            "S0",
            models=("q", "g"),
            datasets=("a", "b", "c"),
            cases_by_dataset={d: ["c1"] for d in ("a", "b", "c")},
            settings=load_config()["selection"],
        )
        self.assertEqual(result["winner"], "S0")
        self.assertFalse(result["candidates"]["S_TABLE"]["eligible"])


class AnalysisTests(unittest.TestCase):
    def test_whole_case_exclusion_and_infeasible_denominator(self):
        from .exps import analyze_outcomes

        cfg = load_config()
        cfg["models"] = ["qwen3.8-27b"]
        cases = [
            {"opaque_incident_id": f"INC-{i}", "dataset": "aiops2022", "role": "report"} for i in range(3)
        ]
        roster = {
            "cases": cases,
            "groups": {"aiops2022": [[r["opaque_incident_id"]] for r in cases]},
        }
        rows = []
        for case in cases:
            for arm in ("P0__T", "P0__V", "P_RANDOM__T", "P_RANDOM__V"):
                rows.append(
                    {
                        "case": case["opaque_incident_id"],
                        "experiment": "exp_evidence_selection",
                        "model": cfg["models"][0],
                        "arm": arm,
                        "status": "completed",
                        "score": {"mrr": 1.0, "ac@1": 1.0},
                        "input_tokens": 100,
                        "output_tokens": 10,
                    }
                )
        rows[-1]["status"] = "infrastructure_failure"
        rows[3].update(status="design_infeasible", score={"mrr": 0.0, "ac@1": 0.0})
        report = analyze_outcomes(rows, roster, cfg)
        self.assertTrue(all(r["n"] == 2 for r in report["aggregates"]))
        self.assertEqual(report["whole_case_exclusions"][0]["excluded_cases"], ["INC-2"])
        self.assertTrue(all(r["n"] == 2 for r in report["event_group_sensitivity"]))
        self.assertEqual(
            next(r["mrr"] for r in report["aggregates"] if r["arm"] == "P_RANDOM__V"),
            0.5,
        )
        twins = [r for r in report["paired_comparisons"] if r["family"].startswith("same_policy_")]
        self.assertTrue(twins)
        self.assertTrue(all(r["arm"].replace("__V", "__T") == r["baseline"] for r in twins))

    def test_mechanism_strata_do_not_invent_missing_attention(self):
        from .exps import summarize_mechanisms

        base = {
            "experiment": "selection",
            "model": "qwen",
            "arm": "P0",
            "dataset": "aiops2022",
            "role": "report",
            "fault_type": "x",
            "root_granularity": "pod",
            "missingness_band": "none",
            "candidate_band": "<=50",
            "trace_coverage": 6,
            "graph_coverage": 14,
            "ranking_transition": "tie",
            "mrr": 0.5,
            "ac@1": 0,
            "input_tokens": 100,
            "output_tokens": 30,
            "root_cited": [],
            "attention": {},
        }
        strata, correlations = summarize_mechanisms([base])
        self.assertEqual(len(strata), 7)
        self.assertEqual(correlations, [])
        self.assertTrue(all(r["n"] == 1 and r["mrr"] == 0.5 for r in strata))


class DataContractTests(unittest.TestCase):
    def test_anonymization_roundtrip_and_precision(self):
        from .exps import _display_number
        from .utils import numeric_entity_map

        mapping, kinds = numeric_entity_map(["api", "node-1", "api-5db866cb86-hbf67"], "INC-123")
        self.assertEqual({len(v) for v in mapping.values()}, {3, 4, 5})
        self.assertEqual(len(set(mapping.values())), 3)
        self.assertEqual(kinds["node-1"], "node")
        self.assertNotEqual(mapping, numeric_entity_map(mapping, "INC-124")[0])
        self.assertIsNone(_display_number(float("nan")))
        self.assertEqual(_display_number(-1.234567), "-1.235")

    def test_unknown_prediction_matches_bridge_failure(self):
        from .exps import parse_rca, score_numeric
        from .utils import rq21_scorer

        scorer = rq21_scorer(load_config())
        score = score_numeric({"services": ["999", "123"]}, {"123": "api"}, ["api"], scorer)
        self.assertEqual(score["mrr"], 0)
        self.assertEqual(score["unknown_ids"], ["999"])
        prediction, error = parse_rca('{"services":["123"],"reason":"x","confidence":"high"}')
        self.assertIsNone(error)
        self.assertEqual(prediction["services"], ["123"])
        self.assertIsNotNone(parse_rca("incomplete {")[1])

    def test_request_hash_pixels_not_metadata_and_model_specific(self):
        import io

        from PIL import Image, PngImagePlugin

        from .utils import request_identity

        buffers = []
        for text in ("one", "two"):
            stream = io.BytesIO()
            meta = PngImagePlugin.PngInfo()
            meta.add_text("comment", text)
            Image.new("RGB", (16, 16), "blue").save(stream, format="PNG", pnginfo=meta)
            buffers.append(stream.getvalue())

        def key(png, model="q", text="task"):
            return request_identity(
                model,
                {"max_tokens": 8192},
                [{"type": "text", "text": text}, {"type": "image", "png": png}],
                "system",
                {},
                {},
            )

        self.assertEqual(key(buffers[0]), key(buffers[1]))
        self.assertNotEqual(key(buffers[0]), key(buffers[0], "g"))
        self.assertNotEqual(key(buffers[0]), key(buffers[0], text="new task"))


class RendererContractTests(unittest.TestCase):
    def test_finite_curve_without_baseline_retains_observations(self):
        from .renderer import designs, panels
        from .renderer.kpi_select import ScoredSeries

        frame = pd.DataFrame({"timestamp": range(8), "123_latency": [np.nan] * 4 + [10.0, 25.0, 12.0, 15.0]})
        fig, ax = designs.plt.subplots()
        try:
            row = panels.render_metric_panel(
                ax, "M1", frame, ScoredSeries("123_latency", "123", "latency", 0, 5, 25, np.nan, np.nan)
            )
            np.testing.assert_equal(ax.lines[0].get_ydata(), [10.0, 25.0, 12.0, 15.0])
            self.assertEqual((row["n_samples"], len(ax.lines)), (4, 1))
        finally:
            designs.plt.close(fig)

    def test_overlay_joins_observed_values_at_original_times_without_imputation(self):
        from unittest.mock import patch

        from .renderer import designs

        values = [None, 10.0, None, 25.0, None, 12.0] + [None] * 58
        payload = {"rank": 1, "values": values, "metric": "latency", "panel_id": "M01", "service": "123"}
        card = {"facts": [{"unit": "ms", "payload": payload}]}
        raster = designs.raster_figure

        def inspect(fig, width, height):
            line = fig.axes[0].lines[0]
            self.assertEqual((line.get_marker(), fig.axes[0].get_xlabel()), (".", "relative minutes"))
            self.assertEqual(len(fig.axes[0].collections), 0)
            np.testing.assert_equal(line.get_ydata(), [10.0, 25.0, 12.0])
            np.testing.assert_equal(line.get_xdata(), (np.array([1, 3, 5]) + 0.5) / 64 * 60)
            return raster(fig, width, height)

        with patch.object(designs, "raster_figure", side_effect=inspect) as draw:
            designs.metric_tile(card, "S_M_OVERLAY", 1200, 450, 3600)
            self.assertEqual(draw.call_count, 1)

    def test_density_corridors_are_lossless_and_deterministic(self):
        from PIL import Image

        from .renderer.designs import compact_white_corridors

        for axis in (0, 1):
            data = np.full((100, 300, 3), 249, dtype=np.uint8)
            data[10:20, 15:80] = [20, 40, 60]
            data[40:50, 120:170] = [80, 100, 120]
            data[70:80, 220:270] = [140, 160, 180]
            source = Image.fromarray(data)
            result, audit = compact_white_corridors(source, axis, metric_seams=axis == 1)
            again, repeated = compact_white_corridors(source, axis, metric_seams=axis == 1)
            self.assertEqual((result.tobytes(), audit), (again.tobytes(), repeated))
            self.assertEqual(result.size, source.size)
            self.assertTrue(audit["changed"])
            self.assertTrue(audit["ink_bytes_preserved"])
            restored = np.full_like(data, 249)
            for strip in audit["strips"]:
                a, b = strip["source"]
                d = strip["destination_start"]
                src, dst = [slice(None)] * 3, [slice(None)] * 3
                src[axis], dst[axis] = slice(d, d + b - a), slice(a, b)
                restored[tuple(dst)] = np.asarray(result)[tuple(src)]
            self.assertTrue(np.array_equal(restored, data))
        blank = Image.new("RGB", (100, 100), "white")
        result, audit = compact_white_corridors(blank, 0)
        self.assertEqual(result.tobytes(), blank.tobytes())
        self.assertFalse(audit["changed"])

    def test_density_real_case_preserves_facts_prompt_and_card_geometry(self):
        import io

        from PIL import Image

        from .exps import cube_units, registered_units, request_parts
        from .renderer.designs import compose_dashboard, encode_dashboard
        from .utils import DesignInfeasible

        cfg = load_config()
        case = read_json(RQ_ROOT / "results/qualification/gallery_summary.json")["cases"][0]["case"]
        root = RQ_ROOT / "results/prepared_selection" / case
        png = (root / "renders/P0.png").read_bytes()
        manifest = read_json(root / "renders/P0.json")
        packet = read_json(root / "packets/P0.json")
        compact, sidecar = encode_dashboard(png, manifest, packet, "S_DENSITY_COMPACT")
        before, after = Image.open(io.BytesIO(png)), Image.open(io.BytesIO(compact))
        self.assertEqual(before.size, after.size)
        self.assertNotEqual(before.tobytes(), after.tobytes())
        self.assertEqual(manifest["cards"], sidecar["cards"])
        self.assertEqual(manifest["fact_inventory_hash"], sidecar["fact_inventory_hash"])
        for region_box in [
            manifest["header"]["box"],
            next(c["box"] for c in manifest["cards"] if c["region"] == "G"),
        ]:
            self.assertEqual(before.crop(region_box).tobytes(), after.crop(region_box).tobytes())
        text = lambda p, m: [
            r["text"] for r in request_parts(packet, png=p, manifest=m) if r["type"] == "text"
        ]
        self.assertEqual(text(png, manifest), text(compact, sidecar))
        with self.assertRaises(DesignInfeasible):
            encode_dashboard(
                png,
                {**manifest, "unrendered_regions": ["L"]},
                packet,
                "S_DENSITY_COMPACT",
            )
        champions = {"P": "P0", "S": "S_DENSITY_COMPACT", "D": "D_COMPACT"}
        self.assertEqual(len(cube_units(champions)), 8)
        for unit in registered_units(cfg, "exp_canvas_composition", champions):
            _, drawn = compose_dashboard(compact, sidecar, packet, unit["composition"])
            self.assertEqual(drawn["fact_inventory_hash"], manifest["fact_inventory_hash"])

    def test_infeasibility_is_encoding_specific_not_inherited_blindly(self):
        from unittest.mock import patch

        from PIL import Image

        from .renderer.designs import encode_dashboard, png_bytes
        from .utils import DesignInfeasible

        png = png_bytes(Image.new("RGB", (100, 100), "white"))
        card = {
            "region": "L",
            "card_id": "L",
            "box": [0, 0, 100, 100],
            "fact_ids": ["log1"],
        }
        manifest = {"cards": [card], "unrendered_regions": ["L"]}
        packet = {"facts": [{"field": "observation_window", "payload": {"duration_rel_s": 60}}]}
        with self.assertRaises(DesignInfeasible):
            encode_dashboard(png, manifest, packet, "S0")
        with (
            patch("RQs.RQ2_1.src.renderer.designs.encode_card", return_value=(None, {})),
            self.assertRaises(DesignInfeasible),
        ):
            encode_dashboard(png, manifest, packet, "S_M_HEATMAP")
        with patch(
            "RQs.RQ2_1.src.renderer.designs.encode_card",
            return_value=(Image.new("RGB", (100, 100), "blue"), {}),
        ):
            result, sidecar = encode_dashboard(png, manifest, packet, "S_L_MATRIX")
        self.assertNotEqual(result, png)
        self.assertEqual(sidecar["unrendered_regions"], [])
        self.assertEqual(sidecar["encoding_audit"]["L"]["drawn_fact_ids"], ["log1"])

    def test_incomplete_cpu_carrier_cannot_become_a_model_input(self):
        from .exps import request_parts

        with self.assertRaises(ProtocolError):
            request_parts({}, png=b"", manifest={"unrendered_regions": ["L"]})

    def test_integer_layouts_disjoint_and_same_membership(self):
        from .renderer.designs import (
            COMPOSITIONS,
            card_manifest,
            composition_boxes,
            validate_boxes,
        )

        cfg = load_config()
        case = read_json(RQ_ROOT / "configs/rosters/public.json")["cases"][0]["opaque_incident_id"]
        p = read_json(ROOT / cfg["data"]["parent_prepared"] / "prepared" / f"{case}.json")["packet"]
        from PIL import Image

        image = Image.open(ROOT / cfg["data"]["parent_prepared"] / "renders" / f"{case}.dashboard.png")
        m = card_manifest(p, image.size)
        self.assertEqual(len(m["cards"]), 7)
        for d in COMPOSITIONS:
            size, boxes = composition_boxes(m, d)
            self.assertEqual(set(boxes), {c["card_id"] for c in m["cards"]})
            validate_boxes(size, [{"boxes": b} for b in boxes.values()])
            if d in ("D_LANDSCAPE", "D_PORTRAIT"):
                self.assertLessEqual(size[0] * size[1], image.width * image.height)
        self.assertEqual(composition_boxes(m, "D_ENTITY"), composition_boxes(m, "D_ENTITY"))

    def test_exact_pixel_overlap_and_density_fairness(self):
        from vlmrca.vlm.attention_probe import _area_map, image_attention_diagnostics

        boxes = [[0, 0, 20, 10], [20, 0, 100, 10]]
        mass, density = _area_map([0.2, 0.8], boxes, (100, 10), (7, 3), mass=True)
        self.assertAlmostEqual(sum(mass), 1)
        self.assertTrue(np.allclose(density, np.repeat(0.001, 21)))
        artifact = {
            "image_size_px": [100, 10],
            "source_token_boxes_px": boxes,
            "source_attention_weights": [0.2, 0.8],
            "global_attention_mass": 1,
            "weights": mass,
            "grid": [7, 3],
        }
        part = {
            "attention_region": "dashboard",
            "attention_region_boxes": {"M": [[0, 0, 25, 10]], "R": [[25, 0, 100, 10]]},
            "attention_visual_regions": ["M", "R"],
        }
        result = image_attention_diagnostics(artifact, part)
        self.assertAlmostEqual(result["global_region_mass"]["M"], 0.25)
        self.assertAlmostEqual(result["region_density_lift"]["M"], 1)
        self.assertAlmostEqual(result["region_density_lift"]["R"], 1)

    def test_text_wrapping_lossless_and_uniform_resize(self):
        from PIL import Image, ImageDraw

        from .renderer.designs import contain_tile, fit_lines, font

        draw = ImageDraw.Draw(Image.new("RGB", (200, 100)))
        text = "a_very_long_operation_name_" * 20
        self.assertEqual("".join(fit_lines(draw, text, font(9), 100)), text)
        image = contain_tile(Image.new("RGB", (200, 100), "black"), (100, 100))
        black = np.all(np.asarray(image) == 0, axis=2)
        self.assertEqual(int(black.sum()), 5000)


class RecoveryContractTests(unittest.TestCase):
    def test_crash_terminal_reconciled_before_any_alias_is_scheduled(self):
        from .utils import artifact_row, stable_hash, write_json

        with tempfile.TemporaryDirectory(dir=RQ_ROOT / "results") as d:
            directory = Path(d)
            ledger = CallLedger(directory / "calls.sqlite", 3)
            target = directory / "result.json"
            evidence = directory / "response.json"
            write_json(evidence, {"response": "complete"})
            attempt = ledger.begin("key", "formal", result_path=target)
            row = {
                "call_key": "key",
                "attempt": attempt,
                "status": "completed",
                "artifacts": [artifact_row(evidence)],
            }
            write_json(target, {**row, "record_sha256": stable_hash(row)})
            ledger.recover_interrupted()
            self.assertEqual(ledger.completed("key"), target)
            self.assertEqual(ledger.count(), 1)

    def test_smoke_uses_only_fixed_cases_and_preserves_arms(self):
        from unittest.mock import patch

        from .utils import DesignInfeasible

        cfg = load_config()
        models = cfg["models"]
        plan = {m: [{"case": c, "arm": "P0__V"} for c in ("a", "b", "c")] for m in models}

        def render(_cfg, case, _unit, **_kwargs):
            if case == "a":
                raise DesignInfeasible("registered footprint")

        # Every fixed dataset case must remain represented: no silent resampling.
        with (
            patch("RQs.RQ2_1.src.main.materialize_unit", side_effect=render),
            self.assertRaises(ProtocolError),
        ):
            feasible_smoke_plan(cfg, "exp_evidence_selection", plan)
        with patch("RQs.RQ2_1.src.main.materialize_unit", return_value=None):
            actual = feasible_smoke_plan(cfg, "exp_evidence_selection", plan)
        self.assertEqual(actual, plan)

    def test_response_recovery_does_not_spend_call(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = CallLedger(Path(d) / "ledger.sqlite", 4)
            attempt = ledger.begin("key", "formal")
            ledger.recover_interrupted()
            ledger.resume_response(attempt, "key")
            self.assertEqual(ledger.count(), 1)
            ledger.finish(attempt, "model_failure")
            with self.assertRaises(ProtocolError):
                ledger.resume_response(attempt, "key")

    def test_atomic_writer_drain_and_process_lock(self):
        from .utils import AsyncWriter, RunLock

        with tempfile.TemporaryDirectory() as d:
            writer = AsyncWriter(2)
            for i in range(24):
                writer.json(Path(d) / f"{i}.json", {"index": i})
            writer.drain()
            self.assertEqual(read_json(Path(d) / "23.json"), {"index": 23})
            with RunLock(Path(d) / "lock"):  # noqa: SIM117 — outer held lock must precede the expected failing acquisition
                with self.assertRaises(ProtocolError), RunLock(Path(d) / "lock"):
                    pass

    def test_conversation_preserves_full_text(self):
        from .utils import conversation_text

        parts = [{"type": "text", "text": "verbatim\nquestion"}, {"type": "image", "png": b""}]
        text = conversation_text(
            {"experiment": "exp", "arm": "arm", "case": "INC-1", "model": "q"},
            "SYSTEM",
            parts,
            "raw {broken",
            ["a.png"],
        )
        for expected in ("SYSTEM", "verbatim\nquestion", "raw {broken", "a.png"):
            self.assertIn(expected, text)

    def test_sdk_retry_and_execution_hold(self):
        import inspect

        from .main import run_model

        self.assertIn("CANVASRCA_SDK_MAX_RETRIES", inspect.getsource(run_model))
        cfg = {**load_config(), "execution_enabled": False, "smoke_authorized": False}
        with self.assertRaises(ProtocolError):
            run_model(cfg, "exp_evidence_selection", "qwen3.8-27b")

    def test_readiness_authentication_and_fail_closed_http(self):
        import io
        from unittest.mock import patch
        from urllib.error import HTTPError

        from .main import wait_server

        with (
            patch.dict("os.environ", {"VLLM_API_KEY": "test-local-key"}),
            patch("urllib.request.urlopen") as call,
        ):
            call.return_value.__enter__.return_value = io.BytesIO(b'{"data":[{"id":"Qwen/Qwen3.8-27B"}]}')
            self.assertTrue(wait_server(load_config(), "qwen3.8-27b")["ready"])
            self.assertEqual(call.call_args.args[0].get_header("Authorization"), "Bearer test-local-key")
            for code in (401, 403, 500):
                call.side_effect = HTTPError(
                    "http://localhost/v1/models", code, "readiness failure", {}, None
                )
                with self.assertRaisesRegex(ProtocolError, f"HTTP {code}"):
                    wait_server(load_config(), "qwen3.8-27b")

    def test_full_writer_resume_dedup_and_changed_input(self):
        self._exercise_request_recovery(crash=False)

    def test_raw_response_recovers_without_second_call(self):
        self._exercise_request_recovery(crash=True)

    def _exercise_request_recovery(self, *, crash):
        import threading
        from unittest.mock import Mock, patch

        from .main import execute_unit
        from .utils import AsyncWriter

        cfg = load_config()
        unit = {
            "arm": "P_RANDOM__T",
            "policy": "P_RANDOM",
            "silhouette": "S0",
            "composition": "D0",
            "representation": "T",
        }
        packet = {"packet_hash": "packet", "candidates": ["123"], "facts": []}
        parts = [{"type": "text", "text": "public evidence only"}]
        response = types.SimpleNamespace(
            text='{"services":["123"],"reason":"evidence","confidence":"high"}',
            raw={"finish_reason": "stop"},
            performance={},
            input_tokens=100,
            output_tokens=20,
        )
        fake = Mock(return_value=response)
        (RQ_ROOT / "results").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=RQ_ROOT / "results", prefix="cpu_recovery_") as directory:
            root = Path(directory)
            ledger = CallLedger(root / "test.sqlite", ceiling=4)
            writer = AsyncWriter(2)
            args = {
                "scope": root.name,
                "ledger": ledger,
                "requests": TokenAdmission(1, 100000),
                "attention": threading.Semaphore(1),
                "stop": threading.Event(),
                "writer": writer,
            }
            with (
                patch.dict(
                    "os.environ",
                    {"CANVASRCA_VLLM_CONFIG": str(ROOT / cfg["unified"]["vllm"])},
                ),
                patch(
                    "RQs.RQ2_1.src.main.materialize_unit",
                    side_effect=lambda *a, **kw: (packet, parts, []),
                ),
                patch(
                    "RQs.RQ2_1.src.main.private_score",
                    return_value={"mrr": 1, "ac@1": 1},
                ),
                patch("RQs.RQ2_1.src.main.persist_attention", return_value=({}, [])) as attention,
                patch("vlmrca.vlm.client.count_vllm_prompt_tokens", return_value=100),
                patch("vlmrca.vlm.client.call_vlm", fake),
            ):
                if crash:
                    attention.side_effect = OSError("CPU-injected postresponse persistence failure")
                    with self.assertRaises(OSError):
                        execute_unit(cfg, "exp_evidence_selection", cfg["models"][0], "INC-CPU", unit, **args)
                    attention.side_effect = None
                    args["stop"].clear()
                execute_unit(cfg, "exp_evidence_selection", cfg["models"][0], "INC-CPU", unit, **args)
                self.assertEqual(fake.call_count, 1)
                self.assertEqual(ledger.count(), 1)
                resumed = execute_unit(
                    cfg,
                    "exp_evidence_selection",
                    cfg["models"][0],
                    "INC-CPU",
                    unit,
                    **args,
                )
                self.assertEqual(resumed["status"], "already_complete")
                # Simulate power loss after terminal fsync but before its SQL commit.
                with ledger.connect() as db:
                    db.execute("UPDATE attempts SET status='interrupted',result_path=NULL")
                execute_unit(
                    cfg,
                    "exp_evidence_selection",
                    cfg["models"][0],
                    "INC-CPU",
                    unit,
                    **args,
                )
                alias = execute_unit(
                    cfg,
                    "exp_evidence_selection",
                    cfg["models"][0],
                    "INC-CPU",
                    {**unit, "arm": "ALIAS"},
                    **args,
                )
                self.assertEqual(alias["status"], "reused")
                self.assertEqual(fake.call_count, 1)
                parts[0]["text"] = "different evidence"
                with self.assertRaises(ProtocolError):
                    execute_unit(
                        cfg,
                        "exp_evidence_selection",
                        cfg["models"][0],
                        "INC-CPU",
                        unit,
                        **args,
                    )
            writer.drain()


def density_gallery():
    """Review only the new condition; reuse public nine-case selection fixtures."""
    import io

    from PIL import Image

    from .exps import request_parts
    from .renderer.designs import encode_dashboard
    from .utils import DesignInfeasible, artifact_row, atomic_write, write_json

    cfg, rows = load_config(), []
    directory = RQ_ROOT / "results/qualification/density_review"
    for item in read_json(RQ_ROOT / "results/qualification/gallery_summary.json")["cases"]:
        case = item["case"]
        root = RQ_ROOT / "results/prepared_selection" / case
        for policy in ("P0", "P_COVERAGE"):
            source = root / "renders" / f"{policy}.png"
            if not source.exists():
                failure = read_json(root / "renders" / f"{policy}.infeasible.json")
                rows.append(
                    {
                        "case": case,
                        "policy": policy,
                        "status": "design_infeasible",
                        "reason": failure["reason"],
                    }
                )
                continue
            packet = read_json(root / "packets" / f"{policy}.json")
            manifest = read_json(root / "renders" / f"{policy}.json")
            png = source.read_bytes()
            try:
                result, audit = encode_dashboard(
                    png, manifest, packet, "S_DENSITY_COMPACT", density=cfg["silhouette_density"]
                )
            except DesignInfeasible as error:
                rows.append(
                    {"case": case, "policy": policy, "status": "design_infeasible", "reason": str(error)}
                )
                continue
            text = lambda p, m, packet=packet: [
                r["text"] for r in request_parts(packet, png=p, manifest=m) if r["type"] == "text"
            ]
            assert text(result, audit) == text(png, manifest)
            assert audit["cards"] == manifest["cards"]
            before, after = Image.open(io.BytesIO(png)), Image.open(io.BytesIO(result))
            assert before.size == after.size
            for card in audit["encoding_audit"].values():
                for footprint in card["footprints"]:
                    old = np.array(before.crop(footprint["interior_box"]))
                    new = np.array(after.crop(footprint["interior_box"]))
                    restored = np.empty_like(old)
                    restored[:] = footprint["background_rgb"]
                    for strip in footprint["strips"]:
                        a, b = strip["source"]
                        d = strip["destination_start"]
                        src, dst = [slice(None)] * 3, [slice(None)] * 3
                        src[footprint["axis"]], dst[footprint["axis"]] = slice(d, d + b - a), slice(a, b)
                        restored[tuple(dst)] = new[tuple(src)]
                    assert np.array_equal(restored, old)
            target = directory / case / f"{policy}.png"
            atomic_write(target, result)
            write_json(target.with_suffix(".json"), audit)
            rows.append(
                {
                    "case": case,
                    "policy": policy,
                    "status": "prepared",
                    "changed": before.tobytes() != after.tobytes(),
                    "fact_hash": packet["fact_inventory_hash"],
                    "artifacts": [
                        artifact_row(source),
                        artifact_row(target),
                        artifact_row(target.with_suffix(".json")),
                    ],
                }
            )
    report = {
        "status": "passed",
        "model_calls": 0,
        "rows": rows,
        "scope": "density only; P0 and coverage, nine selection cases",
    }
    write_json(directory / "summary.json", report)
    return report


def gallery_case(case):
    """All visual design families on one real selection case, CPU only."""
    from .exps import cube_units, registered_units
    from .main import materialize_unit
    from .utils import DesignInfeasible, artifact_row, write_json

    cfg = load_config()
    rows = []
    units = registered_units(cfg, "exp_evidence_selection")
    units += registered_units(cfg, "exp_silhouette_encoding", {"P": "P0"})
    units += registered_units(cfg, "exp_canvas_composition", {"P": "P0", "S": "S0"})
    units += cube_units({"P": "P_RANDOM", "S": "S_COMPACT_MIX", "D": "D_ENTITY"})
    for unit in units:
        try:
            packet, parts, paths = materialize_unit(cfg, case, unit)
            rows.append(
                {
                    "case": case,
                    "unit": unit,
                    "status": "prepared",
                    "fact_hash": packet["fact_inventory_hash"],
                    "text_hash": __import__("unified_scripts").stable_hash(
                        [p["text"] for p in parts if p["type"] == "text"]
                    ),
                    "artifacts": [artifact_row(p) for p in paths],
                    "model_calls": 0,
                }
            )
        except DesignInfeasible as error:
            rows.append(
                {
                    "case": case,
                    "unit": unit,
                    "status": "design_infeasible",
                    "reason": str(error),
                    "model_calls": 0,
                }
            )
    write_json(RQ_ROOT / "results/qualification/gallery" / f"{case}.json", rows)
    return {
        "case": case,
        "designs": len(rows),
        "infeasible": [
            {"arm": r["unit"]["arm"], "reason": r["reason"]} for r in rows if r["status"] != "prepared"
        ],
    }


def cpu_gallery():
    import multiprocessing as mp
    from concurrent.futures import ProcessPoolExecutor

    from unified_scripts import stable_hash

    from .utils import PRIMARY, physical_cores, pin_worker, write_json

    roster = read_json(RQ_ROOT / "configs/rosters/public.json")["cases"]
    cases = [
        case
        for d in PRIMARY
        for case in sorted(
            (r["opaque_incident_id"] for r in roster if r["dataset"] == d and r["role"] == "selection"),
            key=lambda c: stable_hash([42, "visual_review", c]),
        )[:3]
    ]
    ctx = mp.get_context("spawn")
    cores = ctx.Queue()
    for core in physical_cores()[:4]:
        cores.put(core)
    with ProcessPoolExecutor(
        max_workers=4, mp_context=ctx, initializer=pin_worker, initargs=(cores,)
    ) as pool:
        rows = list(pool.map(gallery_case, cases))
    write_json(
        RQ_ROOT / "results/qualification/gallery_summary.json",
        {"cases": rows, "model_calls": 0},
    )
    return rows


def verify_cpu_gallery():
    """Real-case parity and pixel checks, separate from manual legibility review."""

    import numpy as np
    from PIL import Image

    from .utils import artifact_row, artifacts_valid, write_json

    cfg = load_config()
    summary = read_json(RQ_ROOT / "results/qualification/gallery_summary.json")
    count = 0
    cases = []
    artifacts = []
    for item in summary["cases"]:
        case = item["case"]
        base = RQ_ROOT / "results/prepared_selection" / case
        source = ROOT / cfg["data"]["parent_prepared"] / "renders" / f"{case}.dashboard.png"
        old = np.asarray(Image.open(source).convert("RGB"))
        new = np.asarray(Image.open(base / "renders/P0.png").convert("RGB"))
        manifest = read_json(base / "renders/P0.json")
        mask = np.ones(old.shape[:2], dtype=bool)
        for x, y, a, b in manifest["header"]["caption_boxes"]:
            mask[y : b + 1, x : a + 1] = False
        if old.shape != new.shape or not np.array_equal(old[mask], new[mask]):
            raise ProtocolError("calibration changed non-caption pixels")
        rows = read_json(RQ_ROOT / "results/qualification/gallery" / f"{case}.json")
        pixel_hashes = {}
        for row in rows:
            if row["status"] != "prepared":
                continue
            packet = read_json(base / "packets" / f"{row['unit']['policy']}.json")
            if row["fact_hash"] != packet["fact_inventory_hash"]:
                raise ProtocolError("design changed selected facts")
            if row["unit"]["representation"] == "V":
                if not artifacts_valid(row):
                    raise ProtocolError("gallery artifacts corrupt")
                path = next(ROOT / a["path"] for a in row["artifacts"] if a["path"].endswith("manifest.json"))
                m = read_json(path)
                present = set(m["common_fact_ids"]) | {f for card in m["cards"] for f in card["fact_ids"]}
                if present != {f["fact_id"] for f in packet["facts"]}:
                    raise ProtocolError("card membership lost selected facts")
                if len(m["cards"]) != 7:
                    raise ProtocolError("composition split or merged cards")
                png = next(ROOT / a["path"] for a in row["artifacts"] if a["path"].endswith(".png"))
                image = Image.open(png).convert("RGB")
                pixel_hashes[row["unit"]["arm"]] = hashlib.sha256(image.tobytes()).hexdigest()
                count += 1
        cases.append(
            {
                "case": case,
                "selection_fact_inventories": len(
                    {
                        read_json(base / "packets" / f"{p}.json")["fact_inventory_hash"]
                        for p in cfg["policies"]
                    }
                ),
                "distinct_decoded_pngs": len(set(pixel_hashes.values())),
                "design_infeasible": item["infeasible"],
            }
        )
        artifacts += [artifact_row(RQ_ROOT / "results/qualification/gallery" / f"{case}.json")]
    result = {
        "passed": True,
        "cases": cases,
        "checked_pngs": count,
        "artifacts": artifacts,
        "model_calls": 0,
    }
    write_json(RQ_ROOT / "results/qualification/gallery_contract_check.json", result)
    return result


def feasible_smoke_plan(config, experiment, plan):
    """Place arms on the same three fixed CPU-qualified cases, without labels."""
    from .exps import registered_units
    from .main import materialize_unit
    from .utils import DesignInfeasible

    units = {u["arm"]: u for u in registered_units(config, experiment, {"P": "P0", "S": "S0"})}
    cases = sorted({row["case"] for rows in plan.values() for row in rows})
    result = copy.deepcopy(plan)
    for rows in result.values():
        for row in rows:
            original = row["case"]
            for case in [original] + [c for c in cases if c != original]:
                try:
                    materialize_unit(config, case, units[row["arm"]], allow_render=False)
                except DesignInfeasible:
                    continue
                row["case"] = case
                break
            else:
                raise ProtocolError(f"smoke arm {row['arm']} cannot execute on any fixed smoke case")
    if {r["case"] for rows in result.values() for r in rows} != set(cases):
        raise ProtocolError("smoke would omit a fixed dataset case; inspect qualification before inference")
    return result


def bounded_smoke(experiment):
    """Single 18-call/600-second supervisor; intentionally not invoked by tests."""
    import os
    import signal
    import subprocess
    import time

    from .exps import registered_units
    from .gates import protocol_fingerprint
    from .main import build_smoke_plan, load_terminal, prepare_batch
    from .utils import RunLock, artifact_row, code_fingerprint, write_json

    config = load_config()
    if experiment not in config["experiments"] or not config["smoke_authorized"]:
        raise ProtocolError("smoke awaits user authorization")
    if not execution_gate(config, formal=False, smoke=True)["passed"]:
        raise ProtocolError("CPU/review prerequisites incomplete")
    build_smoke_plan(config)
    plan = read_json(RQ_ROOT / "configs/smoke_plan.json")[experiment]
    cases = sorted({r["case"] for rows in plan.values() for r in rows})
    # Rendering is CPU qualification before the single supervisor clock starts.
    prepare_batch(config, cases)
    prepare_batch(
        config,
        cases,
        units=registered_units(config, experiment, {"P": "P0", "S": "S0"}),
    )
    # Only placement within the existing three cases may change. Formal arms,
    # their infeasible outcomes, and the selected cases themselves are untouched.
    registered_plan = read_json(RQ_ROOT / "configs/smoke_plan.json")
    qualified_plan = feasible_smoke_plan(config, experiment, plan)
    registered_plan[experiment] = qualified_plan
    write_json(RQ_ROOT / "configs/smoke_plan.json", registered_plan)
    root = RQ_ROOT / "results" / f"{experiment}_smoke_v1"
    if (root / "qualification.json").exists():
        raise ProtocolError("one logical smoke already completed; inspect it rather than silently rerunning")
    with RunLock(RQ_ROOT / "results/smoke_supervisor.lock"):
        started = time.monotonic()
        deadline = started + 600
        write_json(
            root / "supervisor.json",
            {
                "started_epoch": time.time(),
                "deadline_epoch": time.time() + 600,
                "max_calls": 18,
                "original_assignments": plan,
                "qualified_assignments": qualified_plan,
            },
        )
        errors = []
        timeout = False
        for model in config["models"]:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timeout = True
                break
            with (root / f"{model}.supervisor.log").open("ab") as log:
                process = subprocess.Popen(
                    [
                        "bash",
                        str(RQ_ROOT / "scripts/model_phase.sh"),
                        experiment,
                        model,
                        "smoke",
                    ],
                    cwd=ROOT,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                try:
                    code = process.wait(timeout=remaining)
                    if code:
                        errors.append(f"{model}: subprocess exit {code}")
                        break
                except subprocess.TimeoutExpired:
                    timeout = True
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                    break
        records = []
        for path in sorted((root / "trajectories").rglob("*.json")):
            try:
                record = load_terminal(path)
                if record is None or record.get("parse_error") or record["status"] == "design_infeasible":
                    errors.append(f"non-timeout smoke target failure: {path.name}")
                records.append(artifact_row(path))
            except Exception as error:  # noqa: BLE001 — report verification failures, never classify them as timeout
                errors.append(str(error))
        errors += [str(p) for p in (root / "errors").rglob("*.json")]
        ledger = CallLedger(RQ_ROOT / "results/call_ledger.sqlite", 39999)
        initiated = ledger.count(f"{experiment}_smoke_v1")
        if initiated > 18:
            errors.append("aggregate smoke budget exceeded")
        result = {
            "passed": not errors,
            "timeout_only": timeout and not errors,
            "errors": errors,
            "initiated_calls": initiated,
            "completed_records": len(records),
            "planned": 18,
            "elapsed_seconds": time.monotonic() - started,
            "code": code_fingerprint(),
            "protocol": protocol_fingerprint(config),
            "artifacts": records,
            "human_conversation_review_required": True,
        }
        write_json(root / "qualification.json", result)
        return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--gallery":
        import json

        print(json.dumps(cpu_gallery(), indent=2))
        raise SystemExit(0)
    if len(sys.argv) > 1 and sys.argv[1] == "--smoke":
        import json

        result = bounded_smoke(sys.argv[2])
        print(json.dumps(result, indent=2))
        raise SystemExit(not result["passed"])
    unittest.main()
