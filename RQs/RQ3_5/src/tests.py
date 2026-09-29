"""Adversarial counting tests and three-real-case, no-LLM CPU qualification."""

import copy
import hashlib
import io
import json
import signal
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from . import exps, gates
from .utils import (
    digest,
    explicit_error,
    load_config,
    read_json,
    runtime_config,
    save_json,
)


def fixture():
    spans = []
    for i in range(50):
        current = i >= 20
        y = i >= 35
        x = i >= 33
        for ident, parent, entity, error, duration in [
            ("a", "", "123", y, 100 if y else 10),
            ("b", "a", "456", x, 40 if x else 2),
        ]:
            spans.append(
                {
                    "trace": str(i),
                    "span": ident,
                    "parent": parent,
                    "entity": entity,
                    "operation": "op",
                    "time": (110 + i if current else i),
                    "duration": duration,
                    "error": error,
                    "error_semantics": "http_status",
                    "source_row": 2 * i + (ident == "b"),
                }
            )
    return {"spans": spans, "ownership": {}, "audit": {}}


class CountingTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config()

    def test_block_serializer_preserves_payloads_and_order(self):
        records = [
            {"region": "schema", "record": 'Units: ms; quotes "x"; slash \\; 中文'},
            {"region": "M", "record": "a=1.230000\ncontinuation"},
            {"region": "M", "record": ""},
            {"region": "C", "record": "common"},
            {"region": "M", "record": "b=-0.001"},
        ]
        self.assertEqual(
            exps.evidence_blocks(records),
            '[schema]\nUnits: ms; quotes "x"; slash \\; 中文\n[M]\na=1.230000\ncontinuation\n\n[C]\ncommon\n[M]\nb=-0.001',
        )
        self.assertEqual(exps.evidence_blocks([]), "")
        with self.assertRaisesRegex(ValueError, "Unknown evidence region"):
            exps.evidence_blocks([{"region": "invalid", "record": "x"}])

    def test_serializer_revision_changes_only_crossed_logical_keys(self):
        from .utils import CROSS_SERIALIZER, GC_CLOCK_ARMS, GC_CLOCK_VERSION, VERSION

        reg = {"rosters": {"screen": [{"opaque_incident_id": "fixture"}]}}
        for cell in self.config["experiments"][:3]:
            for task in gates.tasks(self.config, reg, Path("unused"), cell["id"]):
                arm = task["dimensions"]["arm"]
                old = [VERSION, task["stage"], task["model"], "fixture", arm]
                if arm in {"E_P_D_P", "E_P_D_S"}:
                    old.append("candidate_once_v2")
                expected = old + ([CROSS_SERIALIZER] if arm.startswith("E_") else [])
                expected += [GC_CLOCK_VERSION] if arm in GC_CLOCK_ARMS else []
                self.assertEqual(task["logical_key"], digest(expected))
                self.assertEqual(
                    task["logical_key"] != digest(old),
                    arm.startswith("E_") or arm in GC_CLOCK_ARMS,
                )

    def test_gc_clock_projection_preserves_dispersion_deltas_and_input(self):
        from RQs.RQ3_4.src.exps import CLOCK_GUIDE

        config = {
            "method": {
                "clock_projection": {
                    "version": "relative_clock_v1",
                    "source_seconds_metrics": ["container_start_time_seconds"],
                    "output_unit": "relative_clock_seconds",
                }
            }
        }
        observations = [
            {
                "id": "anchor",
                "region": "M",
                "semantic": "container_start_time_seconds",
                "unit": "s",
                "values": {
                    "reference_median": 1647789000,
                    "current_median": 1647789000,
                },
            }
        ]
        body = (
            "key,regular_mean,regular_std_dev,current_mean,current_std_dev\n"
            f"23045.{exps.GC_METRIC},1647789757.68,347.36,1647790967.68,346.79\n"
            "23045.rss_bytes,1647789757.68,347.36,1647790967.68,346.79\n"
        )
        parts = [{"type": "text", "text": body}]
        result = exps.project_gc_clock(parts, observations, config)
        self.assertEqual(parts[0]["text"], body)
        self.assertEqual(
            result[0]["text"],
            CLOCK_GUIDE
            + body.replace(
                f"{exps.GC_METRIC},1647789757.68,347.36,1647790967.68,346.79",
                f"{exps.GC_METRIC}[relative_clock_seconds],757.68,347.36,1967.68,346.79",
            ),
        )
        self.assertEqual(exps.project_gc_clock(result, observations, config), result)
        with self.assertRaisesRegex(ValueError, "no registered shared"):
            exps.project_gc_clock(parts, [], config)
        for bad in ("0", "-1", "NaN", "Infinity"):
            with self.assertRaises(ValueError):
                exps.project_gc_clock(
                    [{"type": "text", "text": body.replace("1647789757.68", bad)}],
                    observations,
                    config,
                )
        with self.assertRaisesRegex(ValueError, "Unprojected"):
            exps.assert_safe_clocks(parts)
        with self.assertRaisesRegex(ValueError, "CSV schema"):
            exps.project_gc_clock(
                [
                    {
                        "type": "text",
                        "text": body.replace("regular_mean", "changed_mean"),
                    }
                ],
                observations,
                config,
            )

    def test_gc_repair_is_four_calls_on_one_original_case(self):
        from .utils import ROOT

        reg = read_json(
            ROOT / self.config["implementation"]["output_root"] / "registration.json"
        )
        selected = gates.gc_repair_tasks(self.config, reg, Path("unused"))
        self.assertEqual(len(selected), 4)
        self.assertEqual(
            {t["case"]["opaque_incident_id"] for t in selected}, {"INC-0986D6C54EC6"}
        )
        self.assertEqual(
            {t["dimensions"]["arm"] for t in selected}, {"E_S_D_S", "SIRCL_IDS_NATIVE"}
        )
        for model in self.config["models"]:
            self.assertEqual(
                len(gates.gc_repair_tasks(self.config, reg, Path("unused"), model)), 2
            )
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            save_json(
                root / "repairs/lossless_blocks_v3/report.json", {"status": "complete"}
            )
            approval = {
                "user_approved": True,
                "approved_date": "2026-09-26",
                "experiment": "exp_evidence_instruction_cross",
                "case": "INC-0986D6C54EC6",
                "arms": ["E_S_D_S", "SIRCL_IDS_NATIVE"],
                "previous_calls": 36,
                "additional_calls_max": 4,
                "max_seconds": 600,
                "contract_hash": digest(reg["contract"]),
                "previous_report_hash": digest({"status": "complete"}),
            }
            save_json(root / "repairs/gc_clock_v1/authorization.json", approval)
            self.assertEqual(
                gates.gc_repair_policy(root, reg, approval["experiment"])[
                    "scope_limit"
                ],
                40,
            )
            approval["additional_calls_max"] = 5
            save_json(root / "repairs/gc_clock_v1/authorization.json", approval)
            with self.assertRaisesRegex(ValueError, "four-call"):
                gates.gc_repair_policy(root, reg, approval["experiment"])

    def test_local_reference_quantile_is_cached_without_changing_counts(self):
        import numpy as np

        with patch.object(np, "percentile", wraps=np.percentile) as percentile:
            packs, _ = exps.request_packs(fixture(), [0, 100, 200], self.config)
        self.assertEqual(percentile.call_count, 1)
        self.assertTrue(all(p["counts"] == [15, 0, 2, 13] for p in packs))

    def test_direct_runner_cannot_skip_infrastructure_or_mix_models(self):
        from .main import run, terminal_flag

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            save_json(
                root / "flags/x.json",
                {"status": "fail", "failure_class": "infrastructure"},
            )
            with self.assertRaisesRegex(ValueError, "requires diagnosis"):
                terminal_flag(root, {"logical_key": "x"})
            with self.assertRaisesRegex(ValueError, "one registered model"):
                run(self.config, {}, root, "A", None, True)

    def test_joint_cells_and_disjoint_root(self):
        packs, _ = exps.request_packs(fixture(), [0, 100, 200], self.config)
        self.assertEqual(len(packs), 2)
        for p in packs:
            self.assertEqual(p["counts"], [15, 0, 2, 13])
            self.assertEqual(p["entity"], "456")
            self.assertEqual(sum(p["counts"]), 30)

    def test_no_trace_identifier_cross_join(self):
        src = fixture()
        src["spans"].append(copy.deepcopy(src["spans"][-1]))
        packs, audit = exps.request_packs(src, [0, 100, 200], self.config)
        self.assertEqual(audit["duplicate_span_trace"], 1)
        self.assertTrue(all(p["counts"] == [14, 0, 2, 13] for p in packs))

    def test_disconnected_and_cyclic_requests_excluded(self):
        src = fixture()
        src["spans"][-1]["parent"] = "nonexistent"
        src["spans"][-3]["parent"] = "b"
        packs, audit = exps.request_packs(src, [0, 100, 200], self.config)
        self.assertEqual(audit["incomplete_or_cyclic_trace"], 2)
        self.assertTrue(all(p["counts"][0] == 13 for p in packs))

    def test_unknown_local_state_not_zero(self):
        src = fixture()
        src["spans"][-1]["error"] = None
        packs, _ = exps.request_packs(src, [0, 100, 200], self.config)
        error = next(p for p in packs if p["x"] == "explicit local error")
        self.assertEqual(sum(error["counts"]), 29)

    def test_status_not_changed_to_latency_for_better_support(self):
        src = fixture()
        for s in src["spans"]:
            if s["span"] == "a":
                s["error"] = False
        packs, _ = exps.request_packs(src, [0, 100, 200], self.config)
        self.assertEqual(packs, [])

    def test_latency_fallback_and_reference_minimum(self):
        src = fixture()
        for s in src["spans"]:
            if s["span"] == "a":
                s["error"] = None
        packs, _ = exps.request_packs(src, [0, 100, 200], self.config)
        self.assertTrue(packs)
        self.assertTrue(all("reference p95" in p["y"] for p in packs))
        src["spans"] = src["spans"][2:]
        self.assertEqual(exps.request_packs(src, [0, 100, 200], self.config)[0], [])

    def test_ambiguous_status_is_not_success(self):
        self.assertEqual(
            explicit_error({"status_code": 0, "attr.status_code": "Unset"}),
            (None, None),
        )
        self.assertEqual(
            explicit_error({"attr.http.response.status_code": 503}),
            (True, "http_status"),
        )
        self.assertEqual(
            explicit_error({"tags": [{"key": "rpc.grpc.status_code", "value": 0}]}),
            (False, "grpc_status"),
        )

    def test_scope_support_and_comparability(self):
        ownership = {
            p: {"node": "1234" if i < 2 else "5678", "service": "123"}
            for i, p in enumerate(["12345", "12346", "12347", "12348"])
        }
        states = [
            {"entity": p, "condition": "readiness false", "affected": i < 2}
            for i, p in enumerate(ownership)
        ]
        packs = exps.scope_packs(ownership, states, [0, 100, 200], self.config)
        self.assertEqual(len(packs), 2)
        self.assertEqual(packs[0]["counts"], [2, 0, 0, 2])
        self.assertEqual(
            exps.scope_packs(ownership, states[:3], [0, 100, 200], self.config), []
        )
        ownership["12348"]["service"] = "456"
        self.assertEqual(
            exps.scope_packs(ownership, states, [0, 100, 200], self.config), []
        )

    def test_marginals_hide_joint_structure(self):
        p = exps.request_packs(fixture(), [0, 100, 200], self.config)[0][0]
        other = copy.deepcopy(p)
        other["counts"] = [10, 5, 7, 8]
        self.assertEqual(exps.pack_text([p], "marg"), exps.pack_text([other], "marg"))
        self.assertNotEqual(
            exps.pack_text([p], "joint"), exps.pack_text([other], "joint")
        )
        self.assertNotIn("provenance", exps.pack_text([p]))
        self.assertEqual(exps.pack_records([p])[0]["derived"]["P_X1_given_Y1"], 1)

    def test_renderer_real_counts_and_fixed_g_geometry(self):
        from PIL import Image

        out = io.BytesIO()
        Image.new("RGB", (200, 100), "#abcdef").save(out, format="PNG")
        context = {"base_parts": [{"type": "image", "png": out.getvalue()}]}
        packs = exps.request_packs(fixture(), [0, 100, 200], self.config)[0]
        a, manifest = exps.composite(
            context, packs, self.config, g_image=True, j_image=True
        )
        b, _ = exps.composite(context, packs, self.config, g_image=True, j_image=False)
        x, y = (Image.open(io.BytesIO(p)) for p in (a, b))
        self.assertEqual(
            x.crop(tuple(manifest["g_rect"])).tobytes(),
            y.crop(tuple(manifest["g_rect"])).tobytes(),
        )
        self.assertEqual(manifest["joint_records"], exps.pack_records(packs))
        self.assertTrue(any(p["kind"] == "bar" for p in manifest["primitives"]))
        self.assertEqual(
            a,
            exps.composite(context, packs, self.config, g_image=True, j_image=True)[0],
        )

    def test_long_label_fails_instead_of_clipping(self):
        from PIL import Image

        out = io.BytesIO()
        Image.new("RGB", (20, 20)).save(out, format="PNG")
        p = exps.request_packs(fixture(), [0, 100, 200], self.config)[0][0]
        p["operation"] = "x" * 20000
        with self.assertRaisesRegex(ValueError, "slot"):
            exps.composite(
                {"base_parts": [{"type": "image", "png": out.getvalue()}]},
                [p],
                self.config,
                g_image=True,
                j_image=True,
            )

    def test_resume_is_flag_only_done_and_fail(self):
        from .main import run

        rows = [
            {"opaque_incident_id": "fixture", "dataset": d}
            for d in self.config["qualification"]["datasets"]
        ]
        registration = {"rosters": {"screen": rows}}
        exp = self.config["experiments"][0]["id"]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            cells = gates.tasks(
                self.config, registration, root, exp, self.config["models"][0], True
            )
            for i, cell in enumerate(cells):
                save_json(
                    root / "flags" / (cell["logical_key"] + ".json"),
                    {
                        "status": "done" if i % 2 else "fail",
                        "failure_class": "request_timeout",
                    },
                )
            with patch(
                "RQs.RQ3_3.src.utils.OfflineTokens",
                side_effect=AssertionError("must not instantiate"),
            ):
                self.assertEqual(
                    run(
                        self.config,
                        registration,
                        root,
                        exp,
                        self.config["models"][0],
                        True,
                    )["status"],
                    "already_terminal",
                )

    def test_smoke_calls_and_budget_bound(self):
        from vlmrca.run_state import DurableCallRegister

        with tempfile.TemporaryDirectory() as folder:
            ledger = DurableCallRegister(
                Path(folder) / "calls.sqlite", limit=40000, scope="test", scope_limit=18
            )
            self.assertEqual(ledger.limit, 40000)
            for n in range(18):
                ident, _ = ledger.begin(str(n), str(n), "solver")
                ledger.finish(ident, {"n": n})
            with self.assertRaisesRegex(RuntimeError, "smoke call limit"):
                ledger.begin("19", "19", "solver")
        for e in self.config["experiments"]:
            self.assertEqual(len(e["smoke_arms"]) * 3 * len(self.config["models"]), 18)

    def test_candidate_repair_keeps_prior_spend(self):
        from vlmrca.run_state import DurableCallRegister

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            reg = {"contract": {"test": "identity"}}
            report = {"initiated_calls": 18, "status": "complete"}
            exp = "exp_evidence_instruction_cross"
            save_json(root / "smokes" / (exp + ".json"), report)
            auth = {
                "user_approved": True,
                "approved_date": "2026-09-26",
                "experiment": exp,
                "arm": "E_P_D_P",
                "previous_calls": 18,
                "additional_calls_max": 6,
                "max_seconds": 600,
                "contract_hash": digest(reg["contract"]),
                "original_report_hash": digest(report),
            }
            path = root / "repairs/candidate_once_v2/authorization.json"
            save_json(path, auth)
            policy = gates.candidate_repair_policy(root, reg, exp)
            ledger = DurableCallRegister(
                root / "calls.sqlite",
                limit=40000,
                scope="rq35_smoke:" + exp,
                scope_limit=18,
            )
            for i in range(18):
                n, _ = ledger.begin(str(i), str(i), "solver")
                ledger.finish(n, {})
            repaired = DurableCallRegister(
                root / "calls.sqlite",
                limit=40000,
                scope=ledger.scope,
                scope_limit=policy["scope_limit"],
            )
            for i in range(18, 24):
                n, _ = repaired.begin(str(i), str(i), "solver")
                repaired.finish(n, {})
            with self.assertRaisesRegex(RuntimeError, "smoke call limit"):
                repaired.begin("25", "25", "solver")
            save_json(path, {**auth, "additional_calls_max": 7})
            with self.assertRaisesRegex(ValueError, "authorization"):
                gates.candidate_repair_policy(root, reg, exp)

    def test_candidate_repair_uses_only_six_original_targets(self):
        values = [
            {
                "dimensions": {"arm": arm},
                "stage": "smoke_A",
                "logical_key": str(i) + arm,
            }
            for i in range(6)
            for arm in ("E_P_D_P", "E_S_D_S", "SIRCL_IDS_NATIVE")
        ]
        with patch.object(gates, "tasks", return_value=values):
            selected = gates.candidate_repair_tasks(self.config, {}, Path("unused"))
        self.assertEqual(len(selected), 6)
        self.assertTrue(all(t["dimensions"]["arm"] == "E_P_D_P" for t in selected))
        self.assertTrue(all(t["stage"].endswith("candidate_once_v2") for t in selected))
        with (
            patch.object(gates, "tasks", return_value=values[:-3]),
            self.assertRaisesRegex(ValueError, "three-case roster"),
        ):
            gates.candidate_repair_tasks(self.config, {}, Path("unused"))

    def test_block_supplement_retains_24_calls_and_stops_at_36(self):
        from vlmrca.run_state import DurableCallRegister

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            reg = {"contract": {"test": "block_v3"}}
            exp = "exp_evidence_instruction_cross"
            prior = {"additional_calls": 6, "initiated_calls": 24}
            save_json(root / "repairs/candidate_once_v2/report.json", prior)
            auth = {
                "user_approved": True,
                "approved_date": "2026-09-26",
                "experiment": exp,
                "arms": ["E_P_D_P", "E_S_D_S"],
                "previous_calls": 24,
                "additional_calls_max": 12,
                "max_seconds": 600,
                "contract_hash": digest(reg["contract"]),
                "previous_report_hash": digest(prior),
            }
            path = root / "repairs/lossless_blocks_v3/authorization.json"
            save_json(path, auth)
            policy = gates.block_repair_policy(root, reg, exp)
            ledger = DurableCallRegister(
                root / "calls.sqlite",
                limit=40000,
                scope="rq35_smoke:" + exp,
                scope_limit=36,
            )
            for i in range(policy["scope_limit"]):
                ident, _ = ledger.begin(str(i), str(i), "solver")
                ledger.finish(ident, {})
            with self.assertRaisesRegex(RuntimeError, "smoke call limit"):
                ledger.begin("37", "37", "solver")
            save_json(path, {**auth, "previous_calls": 0})
            with self.assertRaisesRegex(ValueError, "authorization"):
                gates.block_repair_policy(root, reg, exp)

    def test_block_supplement_covers_two_original_arms_without_new_scope(self):
        values = [
            {
                "dimensions": {"arm": arm},
                "stage": "smoke_A",
                "ledger_scope": "original",
                "logical_key": str(i) + arm,
            }
            for i in range(6)
            for arm in ("E_P_D_P", "E_S_D_S", "SIRCL_IDS_NATIVE")
        ]
        with patch.object(gates, "tasks", return_value=values):
            chosen = gates.block_repair_tasks(self.config, {}, Path("unused"))
        self.assertEqual(len(chosen), 12)
        self.assertEqual(
            {t["dimensions"]["arm"] for t in chosen}, {"E_P_D_P", "E_S_D_S"}
        )
        self.assertTrue(all(t["ledger_scope"] == "original" for t in chosen))
        self.assertTrue(all(t["stage"].endswith("lossless_blocks_v3") for t in chosen))

    def test_formal_phase_uses_only_terminal_flags(self):
        from .main import formal_phase_state

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            tasks = [{"logical_key": name} for name in ("done", "timeout", "pending")]
            save_json(root / "flags/done.json", {"status": "done"})
            save_json(
                root / "flags/timeout.json",
                {"status": "fail", "failure_class": "request_timeout"},
            )
            with patch.object(gates, "tasks", return_value=tasks):
                state = formal_phase_state(self.config, {}, root, "A", "model")
                self.assertEqual(
                    state, {"planned": 3, "pending": 1, "done": 1, "fail": 1}
                )
                save_json(
                    root / "flags/timeout.json",
                    {"status": "fail", "failure_class": "infrastructure"},
                )
                with self.assertRaisesRegex(ValueError, "requires diagnosis"):
                    formal_phase_state(self.config, {}, root, "A", "model")

    def test_queue_rejects_unauthorized_expansion_before_start(self):
        from .main import formal_queue

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            registration = {"contract": {"fixture": "v1"}}
            save_json(
                root / "formal_authorization.json",
                {
                    "contract_hash": digest(registration["contract"]),
                    "authorized_stages": [
                        [self.config["experiments"][2]["id"], "screen"]
                    ],
                },
            )
            with self.assertRaisesRegex(ValueError, "scope is not authorized"):
                formal_queue(self.config, registration, root)

    def test_analysis_families_share_cases_macro_and_group_sensitivity(self):
        rows = []
        for model in self.config["models"]:
            for i, dataset in enumerate(
                ("aiops2022", "aiops2022", "aiops2025", "aegislab")
            ):
                for arm in self.config["experiments"][1]["arms"]:
                    value = 1.0 if dataset == "aiops2022" else 0.0
                    rows.append(
                        {
                            "case": str(i),
                            "dataset": dataset,
                            "model": model,
                            "arm": arm,
                            "status": "done",
                            "model_status": "complete",
                            "fault_type": "synthetic",
                            "granularity": "node",
                            "event_group": "shared" if i < 2 else str(i),
                            "input_tokens": 100,
                            "output_tokens": 10,
                            "metrics": dict.fromkeys(
                                ("mrr", "ac@1", "ac@3", "ac@5", "avg@3", "avg@5"), value
                            ),
                        }
                    )
        # One comparator missing: all primary contrasts exclude the same case.
        next(r for r in rows if r["case"] == "0" and r["arm"] == "MORE").update(
            status="fail"
        )
        with tempfile.TemporaryDirectory() as folder:
            result = gates.analyze_rows(
                rows, self.config, Path(folder), "exp_outcome_linked_evidence", "screen"
            )
        primary = result["primary_family"]
        self.assertEqual(len(primary), 6)
        self.assertTrue(
            all(t["n"] == 3 for t in primary if t["model"] == self.config["models"][0])
        )
        self.assertTrue(
            all(t["event_group_sensitivity"]["groups"] == 3 for t in primary)
        )
        self.assertEqual(len(result["secondary_families"]["joint_mechanism"]), 4)
        summary = [
            r
            for r in result["summaries"]
            if r["arm"] == "TPV" and r["model"] == self.config["models"][0]
        ]
        self.assertAlmostEqual(
            next(r for r in summary if r["dataset"] == "pooled")["mrr"], 0.5
        )
        self.assertAlmostEqual(
            next(r for r in summary if r["dataset"] == "primary_macro")["mrr"], 1 / 3
        )
        self.assertTrue(all(t["holm_p"] >= t["p"] for t in primary))

    def test_later_analysis_requires_registered_calibration_and_mechanisms(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for experiment, phase, family, number in (
                ("exp_joint_representation", "screen", "compositor_calibration", 2),
                ("exp_locked_outcome_linked_rca", "mechanism", "mechanism", 8),
                ("exp_locked_outcome_linked_rca", "test", "visual", 2),
            ):
                result = gates.analyze_rows([], self.config, root, experiment, phase)
                self.assertEqual(len(result["secondary_families"][family]), number)
                self.assertTrue(
                    all(
                        t["n"] == 0 and t["delta_mrr"] is None
                        for t in result["secondary_families"][family]
                    )
                )

    def test_interrupted_repair_publication_resumes_without_cpu_or_gpu(self):
        before = {"contract": {"source": "old"}}
        updated = {"contract": {"source": "new"}}
        proof = {"new_contract": digest(updated["contract"])}
        cpu = {"status": "passed", "contract_hash": proof["new_contract"]}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            repair = root / "repairs/lossless_blocks_v3"
            save_json(repair / "previous/registration.json", before)
            save_json(repair / "capacity_audit.json", {"cases": []})
            save_json(repair / "cpu_qualification.json", cpu)
            save_json(repair / "proof.json", proof)
            save_json(root / "registration.json", before)
            save_json(
                root / "formal_authorization.json", {"contract_hash": "old_authority"}
            )
            for cell in self.config["experiments"]:
                save_json(
                    repair / "previous/qualification" / (cell["id"] + ".json"),
                    {
                        "status": "passed",
                        "contract_hash": "old",
                        "approval_required": False,
                        "targeted_gpu_report": "old_repair.json",
                        "units": [{"arm": "E_P_D_P"}, {"arm": "T_NATIVE"}],
                    },
                )
            real_save = gates.save_json

            def fail_at_qualification(path, data):
                if path.parent == root / "qualification":
                    raise OSError("simulated interruption")
                real_save(path, data)

            with (
                patch.object(gates, "save_json", side_effect=fail_at_qualification),
                self.assertRaises(OSError),
            ):
                gates.publish_block_repair(
                    self.config, root, before, updated, cpu, proof
                )
            self.assertFalse((repair / "completed.json").exists())
            with (
                patch.object(gates, "contract", return_value=updated["contract"]),
                patch(
                    "RQs.RQ3_5.src.tests.cpu_qualification",
                    side_effect=AssertionError("no CPU rerun"),
                ),
            ):
                gates.finalize_block_repair(self.config, root)
            self.assertEqual(read_json(repair / "completed.json"), proof)
            self.assertEqual(
                read_json(root / "formal_authorization.json")["contract_hash"],
                "old_authority",
            )
            qualification = read_json(
                root / "qualification" / (self.config["experiments"][0]["id"] + ".json")
            )
            self.assertTrue(qualification["approval_required"])
            self.assertEqual(qualification["needed_new_calls"], 12)
            self.assertNotIn("targeted_gpu_report", qualification)
            self.assertEqual(qualification["units"], [{"arm": "T_NATIVE"}])


def cpu_qualification(
    config, registration, root, *, output_root=None, reuse_preparation_only=False
):
    from RQs.RQ3_3.src.utils import OfflineTokens
    from vlmrca.run_state import atomic_write

    from .main import compile_unit, load_context, prepare

    started = time.monotonic()
    output_root = output_root or root
    report = {
        "status": "failed",
        "contract_hash": digest(registration["contract"]),
        "units": [],
        "cases": [],
    }

    def timeout(*_):
        raise TimeoutError("CPU regression exceeded 1800 seconds")

    previous = signal.signal(signal.SIGALRM, timeout)
    signal.alarm(config["qualification"]["cpu_seconds"])
    try:
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(CountingTests)
        )
        report["unit_tests"] = {
            "run": result.testsRun,
            "errors": len(result.errors),
            "failures": len(result.failures),
        }
        if not result.wasSuccessful():
            raise AssertionError("Synthetic regression failed")
        rows = gates.qualification_rows(config, registration)
        if reuse_preparation_only:
            report["preparation"] = [
                read_json(
                    root / "preparation_flags" / (r["opaque_incident_id"] + ".json")
                )
                for r in rows
            ]
            if any(f["status"] != "done" for f in report["preparation"]):
                raise ValueError(
                    "Repair regression requires existing complete preparation"
                )
        else:
            report["preparation"] = prepare(config, registration, root, rows)
        tokens = OfflineTokens(runtime_config(config))
        for row in rows:
            context, private = load_context(root, row)
            report["cases"].append(
                {
                    "id": row["opaque_incident_id"],
                    "dataset": row["dataset"],
                    "selected": len(context["ole"]["selected"]),
                    "pool": context["ole"]["pool_count"],
                }
            )
            records = {}
            for cell in config["experiments"]:
                for model in config["models"]:
                    for arm in cell["arms"]:
                        task = {
                            "case": row,
                            "model": model,
                            "stage": "cpu_" + cell["id"],
                            "experiment": cell["id"],
                            "dimensions": {"arm": arm},
                            "logical_key": digest([row, model, arm]),
                            "ledger_scope": "cpu_no_calls",
                        }
                        request = compile_unit(
                            task, context, private, config, tokens, root
                        )
                        records[model, arm] = request
                        output = (
                            output_root
                            / "cpu_inputs"
                            / row["opaque_incident_id"]
                            / model
                            / arm
                        )
                        public = []
                        for part in request["parts"]:
                            if part["type"] == "image":
                                atomic_write(output / "dashboard.png", part["png"])
                                public.append(
                                    {
                                        "type": "image",
                                        "path": "dashboard.png",
                                        "sha256": hashlib.sha256(
                                            part["png"]
                                        ).hexdigest(),
                                    }
                                )
                            else:
                                public.append({"type": "text", "text": part["text"]})
                        save_json(
                            output / "prompt.json",
                            {"system": request["actual"]["system"], "parts": public},
                        )
                        save_json(output / "projection.json", request["projection"])
                        report["units"].append(
                            {
                                "case": row["opaque_incident_id"],
                                "model": model,
                                "arm": arm,
                                "input_identity": request["input_identity"],
                                "tokens": request["projection"]["model_token_counts"],
                            }
                        )
                        print(
                            f"CPU {row['opaque_incident_id']} {model} {arm}: compiled",
                            flush=True,
                        )
            for model in config["models"]:
                for evidence in ("P", "S"):
                    a = records[model, f"E_{evidence}_D_P"]["parts"]
                    b = records[model, f"E_{evidence}_D_S"]["parts"]
                    assert a[:1] + a[2:] == b[:1] + b[2:], (
                        "Guide changes incident facts"
                    )
                    assert a[1] != b[1], "Guide intervention is ineffective"
                    if evidence == "P":
                        assert "field=candidate_set;" not in a[3]["text"], (
                            "Duplicate candidate record in common evidence"
                        )
                        assert a[2] == records[model, "E_S_D_P"]["parts"][2], (
                            "Crossed evidence has different public candidates"
                        )
                assert records[model, "TPV"]["parts"] == context["base_parts"]
                assert (
                    records[model, "REPEAT_1"]["actual"]
                    == records[model, "REPEAT_2"]["actual"]
                )
                assert (
                    records[model, "REPEAT_1"]["input_identity"]
                    != records[model, "REPEAT_2"]["input_identity"]
                )
                for arm in ("J_MARG", "J_JOINT", "J_COND"):
                    assert (
                        records[model, arm]["projection"]["selected_packs"]
                        == context["ole"]["selected"]
                    )
                    if not context["ole"]["selected"]:
                        assert (
                            records[model, arm]["actual"]
                            == records[model, "TPV"]["actual"]
                        )
            for arm in config["experiments"][1]["arms"]:
                assert (
                    records[config["models"][0], arm]["parts"]
                    == records[config["models"][1], arm]["parts"]
                )
        report["status"] = "passed"
    except BaseException as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
        report["elapsed_s"] = time.monotonic() - started
        save_json(output_root / "cpu_qualification.json", report)
    return report


def repair_capacity_audit(config, registration, root):
    """One-time CPU review of the whole screen; never invoked during resume."""
    import importlib.util

    from RQs.RQ1_1.src.exps import RCA_SYSTEM_ROLE
    from RQs.RQ3_3.src.utils import OfflineTokens

    from .main import load_context

    repair = root / "repairs/lossless_blocks_v3"
    spec = importlib.util.spec_from_file_location(
        "RQs.RQ3_5.src._pre_blocks_exps", repair / "previous/src/exps.py"
    )
    predecessor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(predecessor)
    tokens = OfflineTokens(runtime_config(config))
    save_json(repair / "capacity_contract.json", registration["contract"])
    report = {
        "status": "failed",
        "contract_hash": digest(registration["contract"]),
        "cases": [],
        "failures": [],
        "unchanged_other_inputs": 0,
    }
    started = time.monotonic()

    def timeout(*_):
        raise TimeoutError("Screen CPU capacity audit exceeded 1800 seconds")

    previous = signal.signal(signal.SIGALRM, timeout)
    signal.alarm(1800)
    try:
        for row in registration["rosters"]["screen"]:
            context, _ = load_context(root, row)
            case = {
                "case": row["opaque_incident_id"],
                "dataset": row["dataset"],
                "arms": {},
            }
            for cell in config["experiments"]:
                for arm in cell["arms"]:
                    # Reanonymization has its separate integrated three-case test.
                    if arm == "REANONYMIZE":
                        continue
                    try:
                        parts, drawing = exps.parts_for(context, arm, config)
                        old, old_drawing = predecessor.parts_for(context, arm, config)
                        if arm.startswith("E_"):
                            records = [
                                json.loads(line)
                                for line in old[3]["text"].splitlines()[1:]
                            ]
                            self_same = parts[:3] + parts[4:] == old[:3] + old[4:]
                            assert self_same and parts[3]["text"] == (
                                "Evidence by region (original fields and precision):\n"
                                + exps.evidence_blocks(records)
                            ), "Serializer changed facts, order or instructions"
                        else:
                            assert parts == old and drawing == old_drawing, (
                                "Unrelated input changed"
                            )
                            report["unchanged_other_inputs"] += 1
                        system = (
                            context["sircl_system"]
                            if arm == "SIRCL_IDS_NATIVE"
                            else RCA_SYSTEM_ROLE
                        )
                        fits, counts = tokens.fits(parts, system)
                        case["arms"][arm] = {"fits": fits, "tokens": counts}
                        if not fits:
                            report["failures"].append(
                                {"case": case["case"], "arm": arm, "counts": counts}
                            )
                    except Exception as exc:  # noqa: BLE001 -- report every CPU contract failure, never pass it
                        report["failures"].append(
                            {"case": case["case"], "arm": arm, "error": str(exc)}
                        )
            report["cases"].append(case)
            print(
                f"CAPACITY {len(report['cases'])}/60 failures={len(report['failures'])}",
                flush=True,
            )
        report["status"] = "passed" if not report["failures"] else "failed"
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
        report["elapsed_s"] = time.monotonic() - started
        save_json(repair / "capacity_audit.json", report)
    return report


def gc_screen_audit(config, registration, root):
    """One repair audit, never invoked by normal resume or preparation."""
    import importlib.util

    from RQs.RQ1_1.src.exps import RCA_SYSTEM_ROLE
    from RQs.RQ3_3.src.utils import OfflineTokens

    from .main import load_context
    from .utils import GC_CLOCK_ARMS

    repair = root / "repairs/gc_clock_v1"
    spec = importlib.util.spec_from_file_location(
        "RQs.RQ3_5.src.before_gc", repair / "source_before/exps.py"
    )
    predecessor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(predecessor)
    started = time.monotonic()
    tokens = OfflineTokens(runtime_config(config))
    arms = sorted({a for cell in config["experiments"] for a in cell["arms"]})
    report = {
        "status": "failed",
        "cases": [],
        "changed": [],
        "unchanged": 0,
        "contract_hash": digest(registration["contract"]),
        "errors": [],
    }
    try:
        for row in registration["rosters"]["screen"]:
            context, _ = load_context(root, row)
            case = {"case": row["opaque_incident_id"], "arms": {}}
            for arm in arms:
                parts, drawing = exps.parts_for(context, arm, config)
                exps.assert_safe_clocks(parts)
                before, before_drawing = predecessor.parts_for(context, arm, config)
                if parts != before:
                    if arm not in GC_CLOCK_ARMS or drawing != before_drawing:
                        raise ValueError("GC repair changed unrelated input")
                    # Exactly one displayed field changes; other lines and all
                    # dispersion columns must remain byte-identical.
                    old_lines = [p.get("text", "").splitlines() for p in before]
                    new_lines = [p.get("text", "").splitlines() for p in parts]
                    if len(old_lines) != len(new_lines):
                        raise ValueError("GC repair changed prompt structure")
                    for old, new in zip(old_lines, new_lines, strict=True):
                        if len(old) != len(new):
                            raise ValueError("GC repair changed guide/line count")
                        for left, right in zip(old, new, strict=True):
                            if left == right:
                                continue
                            a, b = left.split(","), right.split(",")
                            if (
                                len(a) != 5
                                or len(b) != 5
                                or exps.GC_METRIC not in a[0]
                                or b[0] != a[0] + "[relative_clock_seconds]"
                                or a[2::2] != b[2::2]
                            ):
                                raise ValueError(
                                    "GC repair changed unrelated CSV values"
                                )
                    report["changed"].append({"case": case["case"], "arm": arm})
                else:
                    if drawing != before_drawing:
                        raise ValueError("GC repair changed a dashboard")
                    report["unchanged"] += 1
                if arm in GC_CLOCK_ARMS:
                    system = (
                        context["sircl_system"]
                        if arm == "SIRCL_IDS_NATIVE"
                        else RCA_SYSTEM_ROLE
                    )
                    fits, counts = tokens.fits(parts, system)
                    case["arms"][arm] = {"fits": fits, "tokens": counts}
                    if not fits:
                        raise ValueError("GC projection exceeds input capacity")
            report["cases"].append(case)
            print(f"GC SCREEN {len(report['cases'])}/60", flush=True)
        report["status"] = "passed"
    except Exception as exc:
        report["errors"].append(f"{type(exc).__name__}: {exc}")
        raise
    finally:
        report["elapsed_s"] = time.monotonic() - started
        save_json(repair / "capacity_audit.json", report)
    return report


def review_flags(flags):
    from RQs.RQ3_1.src.main import audit_completion_artifacts

    units = []
    for flag in flags:
        if flag["status"] != "done":
            continue
        directory, key = Path(flag["artifact_root"]), flag["call_key"]
        audit_completion_artifacts(directory, key)
        output = read_json(directory / "outputs" / (key + ".json"))
        prompt = read_json(directory / "prompts" / (key + ".json"))
        completion = read_json(directory / "completed" / (key + ".json"))
        conversation = directory / completion["conversation_path"]
        body = conversation.read_text()
        if output["response"] not in body or "## User" not in body:
            raise ValueError("Conversation omits input/output")
        if prompt["effective_server"]["max_tokens"] != 8192:
            raise ValueError("Output adapter changed")
        for part in prompt["parts"]:
            if (
                part["type"] == "image"
                and not (directory / part["image_path"]).is_file()
            ):
                raise ValueError("Model-visible PNG absent")
        units.append(
            {
                "arm": output["dimensions"]["arm"],
                "model": output["model"],
                "status": output["status"],
                "conversation": str(conversation),
                "call_key": key,
            }
        )
    return units


def review_gc_repair(config, registration, root):
    experiment = "exp_evidence_instruction_cross"
    gates.gc_repair_policy(root, registration, experiment)
    path = root / "repairs/gc_clock_v1/report.json"
    report = read_json(path)
    if (
        report["status"] not in {"complete", "bounded_timeout_only"}
        or report["additional_calls"] > 4
        or report["contract_hash"] != digest(registration["contract"])
    ):
        raise ValueError("GC supplement failed or exceeded its authorized scope")
    expected = {
        t["logical_key"]: t for t in gates.gc_repair_tasks(config, registration, root)
    }
    flags = {f["logical_key"]: f for f in report["flags"]}
    if not set(flags) <= set(expected) or (
        report["status"] == "complete" and set(flags) != set(expected)
    ):
        raise ValueError("Unexpected GC qualification inventory")
    identities = {
        (u["case"], u["model"], u["arm"]): u["input_identity"]
        for u in read_json(root / "cpu_qualification.json")["units"]
    }
    for key, flag in flags.items():
        task = expected[key]
        if (
            flag["status"] != "done"
            or flag["input_identity"]
            != identities[
                task["case"]["opaque_incident_id"],
                task["model"],
                task["dimensions"]["arm"],
            ]
        ):
            raise ValueError("GC input differs from its CPU-qualified identity")
        prompt = read_json(
            Path(flag["artifact_root"]) / "prompts" / (flag["call_key"] + ".json")
        )
        exps.assert_safe_clocks(prompt["parts"])
        if not any(
            exps.GC_METRIC + "[relative_clock_seconds]" in p.get("text", "")
            for p in prompt["parts"]
        ):
            raise ValueError("GC qualification did not exercise repaired evidence")
    units = review_flags(list(flags.values()))
    destination = root / "qualification" / (experiment + ".json")
    prior = read_json(destination)
    proof = read_json(root / "repairs/gc_clock_v1/completed.json")
    if (
        prior["status"] != "requires_targeted_gpu_requalification"
        or proof["new_contract"] != report["contract_hash"]
    ):
        raise ValueError("Missing current explicit GC migration proof")
    replaced = set(proof["replaced_qualification_call_keys"])
    retained = [u for u in prior["units"] if u["call_key"] not in replaced]
    if len(replaced) != 4 or len(retained) != 14:
        raise ValueError("GC qualification replacement exceeds the four affected units")
    save_json(path.with_name("qualification_before.json"), prior)
    current = {
        **prior,
        "status": "passed",
        "units": retained + units,
        "smoke_status": report["status"],
        "initiated_calls": report["initiated_calls"],
        "needed_new_calls": 0,
        "approval_required": False,
        "targeted_gpu_report": str(path),
        "assistant_visual_review": "complete conversations pending assistant review",
    }
    save_json(destination, current)
    return current


def review_block_repair(config, registration, root):
    experiment = "exp_evidence_instruction_cross"
    gates.block_repair_policy(root, registration, experiment)
    path = root / "repairs/lossless_blocks_v3/report.json"
    report = read_json(path)
    if (
        report["status"] not in {"complete", "bounded_timeout_only"}
        or report["additional_calls"] > 12
        or report["contract_hash"] != digest(registration["contract"])
    ):
        raise ValueError("Block supplement failed or exceeded its authorized scope")
    expected = {
        t["logical_key"]: t
        for t in gates.block_repair_tasks(config, registration, root)
    }
    flags = {f["logical_key"]: f for f in report["flags"]}
    if not set(flags) <= set(expected) or (
        report["status"] == "complete" and set(flags) != set(expected)
    ):
        raise ValueError("Unexpected block repair inventory")
    identities = {
        (u["case"], u["model"], u["arm"]): u["input_identity"]
        for u in read_json(root / "cpu_qualification.json")["units"]
    }
    for key, flag in flags.items():
        t = expected[key]
        if (
            flag["status"] != "done"
            or flag["input_identity"]
            != identities[
                t["case"]["opaque_incident_id"], t["model"], t["dimensions"]["arm"]
            ]
        ):
            raise ValueError("Block repair does not match the CPU-qualified input")
    units = review_flags(list(flags.values()))
    destination = root / "qualification" / (experiment + ".json")
    prior = read_json(destination)
    if prior["status"] != "requires_targeted_gpu_requalification":
        raise ValueError("Cannot replace an already reviewed qualification")
    retained = [u for u in prior["units"] if not u["arm"].startswith("E_")]
    if len(retained) != 6:
        raise ValueError("Native qualification inventory changed")
    save_json(path.with_name("qualification_before.json"), prior)
    current = {
        **prior,
        "status": "passed",
        "units": retained + units,
        "smoke_status": report["status"],
        "initiated_calls": report["initiated_calls"],
        "needed_new_calls": 0,
        "approval_required": False,
        "targeted_gpu_report": str(path),
        "assistant_visual_review": "complete conversations pending assistant review",
    }
    save_json(destination, current)
    return current


def review_candidate_repair(config, registration, root):
    experiment = "exp_evidence_instruction_cross"
    gates.candidate_repair_policy(root, registration, experiment)
    path = root / "repairs/candidate_once_v2/report.json"
    report = read_json(path)
    if (
        report["status"] != "complete"
        or report["completed_units"] != 6
        or report["additional_calls"] > 6
        or report["contract_hash"] != digest(registration["contract"])
    ):
        raise ValueError("Targeted repair incomplete; cannot promote A qualification")
    expected = gates.candidate_repair_tasks(config, registration, root)
    if {f["logical_key"] for f in report["flags"]} != {
        t["logical_key"] for t in expected
    }:
        raise ValueError("Repair does not cover the authorized six units")
    cpu = read_json(root / "cpu_qualification.json")
    identities = {
        (u["case"], u["model"], u["arm"]): u["input_identity"] for u in cpu["units"]
    }
    flags = {f["logical_key"]: f for f in report["flags"]}
    for t in expected:
        f = flags[t["logical_key"]]
        if (
            f["status"] != "done"
            or f["input_identity"]
            != identities[t["case"]["opaque_incident_id"], t["model"], "E_P_D_P"]
        ):
            raise ValueError("Repair flag/input differs from qualified CPU input")
    new_units = review_flags(report["flags"])
    original = read_json(root / "smokes" / (experiment + ".json"))
    retained = [u for u in review_flags(original["flags"]) if u["arm"] != "E_P_D_P"]
    if len(retained) != 12 or len(new_units) != 6:
        raise ValueError("Unexpected original/repair qualification inventory")
    destination = root / "qualification" / (experiment + ".json")
    prior = read_json(destination)
    save_json(path.with_name("qualification_before.json"), prior)
    current = {
        **prior,
        "status": "passed",
        "units": retained + new_units,
        "initiated_calls": report["initiated_calls"],
        "targeted_gpu_report": str(path),
        "needed_new_calls": 0,
        "approval_required": False,
        "assistant_visual_review": "repaired text responses pending assistant review",
    }
    save_json(destination, current)
    return current


def review_smoke(config, registration, root, experiment):
    report = read_json(root / "smokes" / (experiment + ".json"))
    if report["contract_hash"] != digest(registration["contract"]):
        qualification = read_json(root / "qualification" / (experiment + ".json"))
        proof_path = qualification.get("cpu_request_equivalence_proof")
        proof = read_json(proof_path) if proof_path else {}
        repair_path = qualification.get("targeted_gpu_report")
        repair = read_json(repair_path) if repair_path else {}
        if (
            qualification["status"] == "passed"
            and qualification["contract_hash"] == digest(registration["contract"])
            and proof.get("new_contract") == qualification["contract_hash"]
            and (
                experiment in proof.get("unchanged_experiments", [])
                or (
                    experiment == "exp_evidence_instruction_cross"
                    and repair.get("status") in {"complete", "bounded_timeout_only"}
                    and (
                        repair.get("completed_units")
                        == (
                            4
                            if repair.get("gc_repair")
                            else 12
                            if repair.get("block_repair")
                            else 6
                        )
                        or repair.get("status") == "bounded_timeout_only"
                    )
                    and repair.get("contract_hash") == qualification["contract_hash"]
                )
            )
        ):
            return qualification
        raise ValueError(
            "Historical smoke cannot qualify a changed prompt; explicit targeted requalification required"
        )
    units = review_flags(report["flags"])
    review = {
        "status": "passed"
        if report["status"] in {"complete", "bounded_timeout_only"}
        else "failed",
        "contract_hash": digest(registration["contract"]),
        "units": units,
        "initiated_calls": report["initiated_calls"],
        "smoke_status": report["status"],
        "assistant_visual_review": "pending",
    }
    save_json(root / "qualification" / (experiment + ".json"), review)
    return review


if __name__ == "__main__":
    unittest.main()
