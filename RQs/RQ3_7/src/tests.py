"""Defined now, NOT executed at implementation time. CPU and smoke qualification."""

import concurrent.futures as cf
import io
import json
import signal
import sqlite3
import time
import unittest
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from . import exps, gates
from .utils import (
    VISUAL,
    DesignInfeasible,
    FrozenEvidenceViewV1,
    NumericPanelV1,
    decimal,
    digest,
    number,
    read_json,
    reference_only,
    save_json,
    saved_prompt_path,
    terminal_flag,
)


def fixture():
    from RQs.RQ1_1.src.exps import _natural_fact_line

    facts, panels, parts = [], [], []
    for i, (entity, before, current, role) in enumerate(
        [
            ("100", "0", "0", "bars"),
            ("2000", "-3", "9", "bars"),
            ("30000", "1E-30", "3E30", "readings"),
            ("100", "1024", "2048", "bars"),
        ]
    ):
        metric = (
            "container_memory_usage_bytes" if i == 3 else "unknown_metric_" + str(i)
        )
        f = {
            "fact_id": "f" + str(i),
            "region": "M",
            "field": "metric_series_64",
            "entity_ids": [entity],
            "relative_bins": [0, 1],
            "unit": "bytes" if i == 3 else "source_unit",
            "payload": {
                "service": entity,
                "metric": metric,
                "panel_id": "panel" + str(i),
                "rank": i + 1,
                "values": [float(before), None, float(current)],
                "missing_mask": [False, True, False],
                "baseline": float(before),
                "peak": float(current),
                "signed_z": 4000,
                "sircl_met_z": {
                    "regular_mean": float(before),
                    "current_mean": float(current),
                    "regular_std_dev": 0.0,
                    "current_std_dev": 0.1,
                    "deviation_sigma": 4000,
                },
            },
        }
        facts.append(f)
        parts.append({"type": "text", "text": _natural_fact_line(f)})
        obs = {
            "fact_id": f["fact_id"],
            "metric": metric,
            "unit": f["unit"],
            "before": before,
            "current": current,
            "glyph": role,
            "source_verified": i == 3,
        }
        if any(p.entity == entity for p in panels):
            j = next(j for j, p in enumerate(panels) if p.entity == entity)
            panels[j] = replace(panels[j], observations=panels[j].observations + (obs,))
        else:
            panels.append(NumericPanelV1(entity, (obs,)))
    ledger = (
        "calls 100 -> 30000\nhosts 2000 -> 30000\nowns 100 -> 30000\ncalls 100 -> 100"
    )
    parts += [
        {"type": "text", "text": ledger, "rq37_g": True},
        {"type": "text", "text": "Identify the root cause."},
    ]
    return FrozenEvidenceViewV1(
        tuple(parts),
        tuple(facts),
        tuple(panels),
        ("100", "2000", "30000", "400"),
        (
            ("100", "30000", "calls"),
            ("2000", "30000", "hosts"),
            ("100", "100", "calls"),
        ),
        ledger,
        ("100", "2000", "30000", "400"),
        "Frozen RCA system",
    )


def settings():
    return {
        "width": 2304,
        "height": 3072,
        "max_height": 8192,
        "font_size": 20,
        "line_height": 26,
        "margin": 32,
    }


def definitions():
    return {
        "container_memory_usage_bytes": {
            "role": "usage",
            "unit": "bytes",
            "source": "cpu-fixture-definition",
        }
    }


class ProtocolTests(unittest.TestCase):
    def test_concurrent_status_writes_are_atomic(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "activity.json"
            with cf.ThreadPoolExecutor(max_workers=16) as pool:
                list(pool.map(lambda i: save_json(path, {"i": i, "payload": "x" * 1000}), range(100)))
            self.assertIn(read_json(path)["i"], range(100))
            self.assertEqual(read_json(path)["payload"], "x" * 1000)

    def test_pruned_inventory_and_archive_only_policy(self):
        from .utils import load_config

        config = load_config()
        rows = [{"dataset": d, "opaque_incident_id": d} for d in gates.PRIMARY]
        registration = {
            "rosters": {
                "development": rows,
                "robustness": rows,
                "eval": rows,
                "test": [],
                "fresh": [],
            }
        }
        targets = gates.tasks(config, registration, "A")
        self.assertNotIn("B3_T_REF", {t["dimensions"]["arm"] for t in targets})
        self.assertEqual(len(targets), 7 * 3 * 2)
        self.assertEqual(sum(not reference_only(t, config) for t in targets), 5 * 3 * 2)
        self.assertTrue(
            all(
                reference_only(t, config)
                for t in gates.tasks(config, registration, "C")
                if t["dimensions"]["arm"].endswith("_REF")
            )
        )
        self.assertEqual(
            config["budget"]["planned_new_upper"],
            sum(e["calls_upper"] for e in config["experiments"].values()) + 54,
        )

    def test_reference_only_cannot_fall_back_to_inference(self):
        from .main import execute

        config = {"experiments": {"A": {"reference_only_arms": ["TPV_REF"]}}}
        task = {
            "logical_key": "archive",
            "dimensions": {"arm": "TPV_REF"},
            "model": "m",
            "case": {"opaque_incident_id": "a"},
            "experiment_id": "A",
        }
        with (
            TemporaryDirectory() as tmp,
            patch("RQs.RQ3_1.src.main.run_registered_call") as call,
        ):
            result = execute(task, {}, config, Path(tmp))
            call.assert_not_called()
            self.assertEqual(result["failure_class"], "reference_unavailable")
            self.assertEqual(result["new_generation_calls"], 0)
            self.assertNotIn("metrics", result)
            self.assertEqual(execute(task, {}, config, Path(tmp)), result)

    def test_expansion_uses_paired_deltas_not_unmatched_summaries(self):
        config = {"models": ["q", "g"]}
        comparisons = [
            {
                "family": "primary_eight",
                "model": m,
                "b": b,
                "primary_macro_delta": 0.04,
                "dataset_deltas": dict.fromkeys(gates.PRIMARY, 0.04),
            }
            for m in ("q", "g")
            for b in ("TPV_REF", "T_MATCH")
        ]
        patterns = [
            {
                "model": m,
                "baseline": "TPV_REF",
                "granularity": "node",
                "n": 20,
                "delta": 0,
            }
            for m in ("q", "g")
        ]
        self.assertTrue(
            gates.expansion(config, comparisons, patterns, True)["recommend_expand"]
        )
        comparisons[0]["primary_macro_delta"] = None
        self.assertFalse(
            gates.expansion(config, comparisons, patterns, True)["recommend_expand"]
        )

    def test_roles_are_attested_not_inferred_from_large_values(self):
        sample = fixture()
        facts = [deepcopy(sample.metric_facts[i % 4]) for i in range(12)]
        for i, fact in enumerate(facts):
            fact["fact_id"] = "fact" + str(i)
        facts[0]["payload"]["metric"] = "container_cpu_usage_seconds_total"
        defs = {
            **definitions(),
            "container_cpu_usage_seconds_total": {
                "role": "counter",
                "unit": "cpu_seconds",
                "source": "cpu-fixture-definition",
            },
        }
        context = {
            "prepared": SimpleNamespace(
                public={"packet": {"facts": facts}}, private={}
            ),
            "base_parts": [{"type": "image", "png": b"not-rendered-in-this-test"}],
            "candidates": list(sample.candidates),
            "rq36_parent_trace_unit": "ms",
        }
        record = {
            "text": "observed relations",
            "appendix": "",
            "entities": set(sample.entities),
            "edges": [],
        }
        with patch("RQs.RQ3_7.src.exps.all_id_record", return_value=record):
            view = exps.make_view(context, {}, None, defs)
        observations = [o for p in view.panels for o in p.observations]
        self.assertEqual(len(observations), 12)
        self.assertEqual(sum(o["glyph"] == "bars" for o in observations), 3)
        counter = next(
            o
            for o in observations
            if o["metric"] == "container_cpu_usage_seconds_total"
        )
        self.assertEqual(counter["glyph"], "readings")
        self.assertEqual(
            exps.conversion_rules(view, defs)[counter["metric"]]["display"],
            "container_cpu_usage_milliseconds_total",
        )

    def test_exact_decimals_and_scientific_literals(self):
        for value in (
            "0",
            "-3.125",
            "1e-90",
            "123456789012345678901234567890.123456789",
            "8E70",
        ):
            for exponent in (-3, 3):
                forward = number(value, "NATIVE", exponent)
                self.assertEqual(
                    decimal(number(forward, "NATIVE", -exponent)), decimal(value)
                )
            scientific = number(value, "SCIENTIFIC")
            self.assertIn("E", scientific)
            self.assertEqual(decimal(scientific), decimal(value))
        value = exps.quantity(1000, "SCIENTIFIC", 0)
        self.assertIn("E", exps.exact_json({"x": value}))
        self.assertEqual(json.loads(exps.exact_json({"x": value}))["x"], 1000)
        for value in (True, "NaN", "Infinity"):
            with self.assertRaises((TypeError, ValueError)):
                number(value)

    def test_inherited_display_suffixes_are_decimal_not_physical_units(self):
        from .utils import NumericLiteral

        for source, expected in (("1.1k", "1100"), ("56.3M", "56300000"),
                                 ("2.5G", "2500000000"), ("-1.1k", "-1100"),
                                 ("4.7e-17", "0.000000000000000047")):
            self.assertEqual(decimal(number(source)), decimal(expected))
            self.assertEqual(decimal(number(source, "SCIENTIFIC")), decimal(expected))
        for source in ("12 ms", "n/a", "1Ki", "1MB", ""):
            with self.assertRaises(ValueError):
                number(source)
        with self.assertRaises(ValueError):
            NumericLiteral("1.1k")

    def test_real_metric_registry_exact_matches_only(self):
        from .utils import load_config, measurement_definitions

        defs = measurement_definitions(load_config())
        self.assertEqual(defs["k8s.pod.memory.available"]["unit"], "bytes")
        self.assertEqual(defs["container.memory.rss"]["role"], "gauge")
        self.assertNotIn("rrt", defs)  # No name-based millisecond guess.

    def test_four_conditions_same_content_fixed_scene(self):
        view = fixture()
        geo = exps.scene(view, definitions(), settings())
        observed = {}
        for arm in VISUAL:
            parts, audit = exps.parts_for(
                view, definitions(), settings(), arm, geometry=geo
            )
            self.assertEqual(sum(p["type"] == "image" for p in parts), 1)
            self.assertEqual(
                audit["fact_hash"], digest([view.parts, view.metric_facts, view.ledger])
            )
            primitives = audit["primitives"]
            self.assertEqual(
                sum(p["kind"] == "measurement-of" for p in primitives),
                len(view.panels) if arm.endswith("LINK") else 0,
            )
            self.assertEqual(
                {p["fact"] for p in primitives if "fact" in p},
                {f["fact_id"] for f in view.metric_facts},
            )
            self.assertIn("400", {p["id"] for p in primitives if p["kind"] == "entity"})
            observed[arm] = audit
        self.assertEqual(len({a["image_hash"] for a in observed.values()}), 4)
        self.assertEqual(len({a["geometry_hash"] for a in observed.values()}), 1)
        for key in ("entity", "calls", "hosts"):
            sequences = [
                [p for p in a["primitives"] if p["kind"] == key]
                for a in observed.values()
            ]
            self.assertTrue(all(s == sequences[0] for s in sequences))

    def test_unit_geometry_invariance_and_all_references(self):
        view = fixture()
        geo = exps.scene(view, definitions(), settings())
        _native, native_audit = exps.parts_for(
            view, definitions(), settings(), "LOCAL_LINK", geometry=geo
        )
        transformed, transformed_audit = exps.parts_for(
            view, definitions(), settings(), "LOCAL_LINK", "UNIT_EQUIVALENT", geo
        )
        self.assertNotEqual(native_audit["image_hash"], transformed_audit["image_hash"])
        boxes = lambda audit: [
            (p["kind"], p.get("box"), p.get("path")) for p in audit["primitives"]
        ]
        self.assertEqual(boxes(native_audit), boxes(transformed_audit))
        self.assertEqual(
            exps.bar_geometry(1024, 2048, 640), exps.bar_geometry("1.024", "2.048", 640)
        )
        text = "\n".join(p.get("text", "") for p in transformed)
        self.assertIn("container_memory_usage_kB", text)
        self.assertNotIn('metric="container_memory_usage_bytes"', text)
        original = view.metric_facts[-1]
        new = exps.transformed_fact(
            original, "UNIT_EQUIVALENT", exps.conversion_rules(view, definitions())
        )
        for key in ("signed_z", "panel_id", "rank", "service", "missing_mask"):
            self.assertEqual(original["payload"][key], new["payload"][key])
        self.assertEqual(original["relative_bins"], new["relative_bins"])

    def test_unknown_unit_noop(self):
        view = fixture()
        for arm in ("T_MATCH", *VISUAL):
            a, _ = exps.parts_for(view, {}, settings(), arm)
            b, audit = exps.parts_for(view, {}, settings(), arm, "UNIT_EQUIVALENT")
            self.assertEqual(a, b)
            self.assertFalse(audit["encoding"]["applicable"])

    def test_bar_zero_negative_huge(self):
        self.assertEqual(exps.bar_geometry(0, 0, 640), (0, 0, 0))
        for a, b in ((-3, 2), ("1e-70", "3e-70"), ("1e90", "2e90")):
            self.assertTrue(all(0 <= x <= 640 for x in exps.bar_geometry(a, b, 640)))

    def test_long_labels_determinism_no_clipping(self):
        view = fixture()
        first = view.panels[0]
        obs = {**first.observations[0], "metric": "observed_" * 45}
        view = replace(
            view,
            panels=(
                replace(first, observations=(obs, *first.observations[1:])),
                *view.panels[1:],
            ),
        )
        geo = exps.scene(view, definitions(), settings())
        a, manifest = exps.render(view, view.panels, geo, "LOCAL_LINK", view.ledger)
        b, _ = exps.render(view, view.panels, geo, "LOCAL_LINK", view.ledger)
        self.assertEqual(a, b)
        self.assertTrue(any(obs["metric"] in p.get("reading", "") for p in manifest))
        from PIL import Image

        self.assertEqual(Image.open(io.BytesIO(a)).size, (2304, geo.height))
        with self.assertRaises(DesignInfeasible):
            exps.scene(view, definitions(), {**settings(), "max_height": 10})

    def test_repeat_distinct_and_native_cross_stage_reuse(self):
        from .main import reuse_identity

        task = {
            "model": "m1",
            "case": {"opaque_incident_id": "a"},
            "ledger_scope": "rq37_formal",
            "dimensions": {"replicate": 0},
        }
        request = {"input_identity": "same-input"}
        native = reuse_identity(task, request)
        self.assertNotEqual(
            native, reuse_identity({**task, "dimensions": {"replicate": 1}}, request)
        )
        self.assertNotEqual(native, reuse_identity({**task, "model": "m2"}, request))
        self.assertEqual(native, reuse_identity({**task, "stage": "C"}, request))

    def test_terminal_flags_do_not_open_large_artifacts(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            task = {"logical_key": "one"}
            for status in ("done", "fail"):
                save_json(
                    root / "flags/one.json", {"logical_key": "one", "status": status}
                )
                self.assertEqual(terminal_flag(root, task)["status"], status)
            self.assertIsNone(terminal_flag(root, {"logical_key": "uncommitted"}))

    def test_public_private_boundary(self):
        import inspect

        fields = set(FrozenEvidenceViewV1.__dataclass_fields__)
        self.assertFalse(
            fields & {"private", "label", "ground_truth", "fault_type", "dataset"}
        )
        for func in (exps.render, exps.scene, exps.parts_for, exps.compile_request):
            self.assertNotIn("private", inspect.signature(func).parameters)
        view = fixture()
        private = {"ground_truth": "100"}
        a, _ = exps.parts_for(view, {}, settings(), "LOCAL_LINK")
        private["ground_truth"] = "2000"
        b, _ = exps.parts_for(view, {}, settings(), "LOCAL_LINK")
        self.assertEqual(a, b)

    def test_writer_commit_and_timeout_flags(self):
        from .main import execute

        task = {
            "logical_key": "x",
            "dimensions": {},
            "model": "m",
            "case": {"opaque_incident_id": "a"},
            "experiment_id": "A",
        }
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = {"design_infeasible": "Registered capacity exceeded"}
            result = execute(task, request, {}, root)
            self.assertEqual(result["metrics"]["mrr"], 0)
            self.assertEqual(result["new_generation_calls"], 0)
            self.assertEqual(execute(task, {}, {}, root), result)


def persist_cpu_input(root, task, request):
    from vlmrca.run_state import atomic_write

    key = task["logical_key"]
    directory = root / "cpu_inputs" / key
    if "design_infeasible" in request or "reference_unavailable" in request:
        save_json(directory / "status.json", request)
        return
    parts = []
    for i, part in enumerate(request["parts"]):
        if part["type"] == "image":
            filename = f"image_{i}.png"
            atomic_write(directory / filename, part["png"])
            parts.append({"type": "image", "image_path": filename})
        else:
            parts.append(part)
    save_json(
        directory / "prompt.json",
        {"system": request["envelope"]["system"], "parts": parts},
    )
    save_json(directory / "projection.json", request["projection"])


def cpu_qualification(config, registration, root):
    from RQs.RQ3_6.src.main import close_pool, cpu_pool

    from .main import compile_case

    gates.assert_current(config, registration)
    started = time.monotonic()
    report = {
        "status": "failed",
        "contract_hash": digest(registration["contract"]),
        "completed": [],
        "infeasible": [],
    }
    pool = queue = None

    def deadline(*_):
        raise TimeoutError("CPU qualification exceeded 1800 seconds")

    previous = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, config["qualification"]["cpu_seconds"])
    try:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(ProtocolTests)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful():
            raise AssertionError("CPU synthetic regression failed")
        report["synthetic_tests"] = result.testsRun
        targets = [
            t
            for e in ("A", "B", "C")
            for t in gates.tasks(
                config, registration, e, model=config["models"][0], cpu=True
            )
        ]
        groups = {}
        for task in targets:
            groups.setdefault(task["case"]["opaque_incident_id"], []).append(task)
        pool, queue, _ = cpu_pool(min(8, len(groups)))
        futures = [
            pool.submit(compile_case, (config, registration, group))
            for group in groups.values()
        ]
        for future in cf.as_completed(futures):
            for task, request in future.result():
                persist_cpu_input(root, task, request)
                report["completed"].append(task["logical_key"])
                if "design_infeasible" in request:
                    report["infeasible"].append(
                        {
                            "task": task["logical_key"],
                            "arm": task["dimensions"]["arm"],
                            "reason": request["design_infeasible"],
                        }
                    )
        if report["infeasible"]:
            raise ValueError(
                "Qualification design-infeasible cases require review, not silent zero-pass"
            )
        report["status"] = "passed"
    except BaseException as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        if pool:
            close_pool(pool, queue, abort=report["status"] != "passed")
        report["elapsed_s"] = time.monotonic() - started
        report["scope"] = (
            "CPU only; both actual processors preflight; no runtime/visual manual approval"
        )
        save_json(root / "cpu_qualification.json", report)
    return report


def review(config, registration, root, experiment):
    """Saved-output integrity only; no requests, rescoring, or fresh model judge."""
    errors, records = [], []
    for task in gates.tasks(config, registration, experiment, smoke=True):
        flag = terminal_flag(root, task)
        if not flag:
            continue
        if flag["status"] != "done":
            errors.append({"key": task["logical_key"], "failure": flag})
            continue
        base, key = Path(flag["artifact_root"]), flag["call_key"]
        try:
            commit = read_json(base / "completed" / (key + ".json"))
            for path in (
                base / "inputs" / (key + ".json"),
                base / "outputs" / (key + ".json"),
                base / "cost" / (key + ".json"),
                base / commit["conversation_path"],
            ):
                if not path.is_file() or path.stat().st_size == 0:
                    raise ValueError("Missing persisted artifact: " + str(path))
            prompt = read_json(saved_prompt_path(base, key))
            for part in prompt["parts"]:
                if part["type"] == "image":
                    from PIL import Image

                    with Image.open(base / part["image_path"]) as im:
                        im.verify()
            records.append(
                {
                    "key": key,
                    "root": str(base),
                    "model_status": flag.get("model_status"),
                }
            )
        except (OSError, ValueError, KeyError) as exc:
            errors.append({"key": key, "error": str(exc)})
    # Catch failed client attempts even if the supervisor deadline interrupted flag writing.
    ledger = root / "calls.sqlite"
    if ledger.exists():
        with sqlite3.connect(f"file:{ledger}?mode=ro", uri=True) as db:
            prefix = "rq37_smoke_" + experiment + "/"
            failed = db.execute(
                "SELECT call_key,state FROM calls WHERE substr(call_key,1,?)=? AND state='infrastructure_failure'",
                (len(prefix), prefix),
            ).fetchall()
        errors.extend({"key": k, "state": s} for k, s in failed)
    return {
        "records": records,
        "errors": errors,
        "manual_visual_and_conversation_review": "required_not_automated",
    }
