"""Bounded CPU regression and saved-output qualification; never a model judge."""

import concurrent.futures as cf
import io
import os
import re
import signal
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from . import exps, gates
from .utils import digest, read_json, runtime_config, save_json, terminal_flag


class ProtocolTests(unittest.TestCase):
    def test_component_ablation_does_not_recompute_values(self):
        facts = [
            {
                "field": "propagation_service",
                "payload": {
                    "service": "123",
                    "rank": 1,
                    "severity_z_display": 3.5,
                    "onset_rel_min_display": 2.0,
                    "evidence_source_display": "M",
                },
            },
            {
                "field": "directed_call_edge",
                "payload": {"caller": "123", "callee": "456", "count": 20},
            },
        ]
        before = digest(facts)
        for policy, key in (
            ("NO_RANK", "rank"),
            ("NO_SEVERITY", "severity_z_display"),
            ("NO_ONSET", "onset_rel_min_display"),
        ):
            actual = exps.component_facts(facts, policy)
            self.assertNotIn(key, actual[0]["payload"])
            self.assertEqual(actual[1], facts[1])
            self.assertEqual(
                actual[0]["payload"],
                {k: v for k, v in facts[0]["payload"].items() if k != key},
            )
        self.assertEqual(len(exps.component_facts(facts, "NO_CALLS")), 1)
        self.assertEqual(digest(facts), before)

    def test_readiness_auth_and_fail_fast(self):
        import json
        import threading
        from http.server import BaseHTTPRequestHandler, HTTPServer

        from .utils import endpoint_vacant, model_probe

        class Handler(BaseHTTPRequestHandler):
            code = 200

            def do_GET(self):
                code = (
                    self.code
                    if self.headers.get("Authorization") == "Bearer cpu-only-key"
                    else 401
                )
                self.send_response(code)
                self.end_headers()
                self.wfile.write(json.dumps({"data": [{"id": "cpu-model"}]}).encode())

            def log_message(self, *_):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        spec = {
            "base_url": f"http://127.0.0.1:{server.server_port}/v1",
            "served_model_name": "cpu-model",
        }
        try:
            self.assertFalse(endpoint_vacant(spec))
            with patch.dict(os.environ, {"VLLM_API_KEY": "cpu-only-key"}):
                self.assertTrue(model_probe(spec))
                Handler.code = 503
                self.assertFalse(model_probe(spec))
                Handler.code = 403
                with self.assertRaisesRegex(RuntimeError, "HTTP 403"):
                    model_probe(spec)
            with (
                patch.dict(os.environ, {"VLLM_API_KEY": "wrong"}),
                self.assertRaisesRegex(RuntimeError, "HTTP 401"),
            ):
                model_probe(spec)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
        self.assertTrue(endpoint_vacant(spec))

    def test_shared_budget_alias(self):
        from .utils import ensure_shared_ledger

        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            config = {"implementation": {"shared_ledger": str(base / "shared.sqlite")}}
            for name in ("a", "b"):
                root = base / name
                root.mkdir()
                ensure_shared_ledger(config, root)
                ensure_shared_ledger(config, root)
                self.assertEqual(
                    (root / "calls.sqlite").resolve(), base / "shared.sqlite"
                )

    def test_unit_labels_do_not_change_values_or_native_fields(self):
        parts = [
            {
                "type": "text",
                "text": "exl_p95_base_ms=1500 latency_lfc=2 current_inclusive_median_ms=1.5 counts_milliseconds_and_log2_fold_change",
            },
            {"type": "image", "png": b"unchanged"},
        ]
        renamed = exps.parent_unit_labels(parts, "us")
        self.assertEqual(
            renamed[0]["text"],
            "exl_p95_base_us=1500 latency_lfc=2 current_inclusive_median_ms=1.5 counts_microseconds_and_log2_fold_change",
        )
        self.assertEqual(renamed[1], parts[1])
        self.assertEqual(exps.parent_unit_labels(parts, "ms"), parts)
        self.assertIn("exl_p95_base_ms", parts[0]["text"])
        with self.assertRaises(ValueError):
            exps.parent_unit_labels(parts, "unknown")

    def test_exact_boundaries(self):
        self.assertEqual(
            exps.split_once("abcVERIFY:def", "VERIFY:"), ("abc", "VERIFY:def")
        )
        for value in ("no boundary", "VERIFY:xVERIFY:y"):
            with self.assertRaises(ValueError):
                exps.split_once(value, "VERIFY:")

    def test_private_is_not_compiler_argument(self):
        import inspect

        self.assertEqual(
            list(inspect.signature(exps.parts_for).parameters),
            ["context", "arm", "config"],
        )

    def test_terminal_flags_do_not_read_artifacts(self):
        task = {"logical_key": "unit"}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertIsNone(terminal_flag(root, task))
            for status in ("done", "fail"):
                value = {
                    "logical_key": "unit",
                    "status": status,
                    "failure_class": "request_timeout",
                }
                save_json(root / "flags/unit.json", value)
                with patch(
                    "RQs.RQ3_6.src.main.load_context",
                    side_effect=AssertionError("must skip"),
                ):
                    self.assertEqual(terminal_flag(root, task), value)
            save_json(
                root / "flags/unit.json",
                {
                    "logical_key": "unit",
                    "status": "fail",
                    "failure_class": "infrastructure",
                },
            )
            with self.assertRaises(ValueError):
                terminal_flag(root, task)

    def test_task_identity_and_caps(self):
        from .utils import load_config

        config = load_config()
        rows = [
            {"opaque_incident_id": str(i), "dataset": d}
            for i, d in enumerate(config["qualification"]["datasets"])
        ]
        reg = {"rosters": {"screen": rows, "check": rows}}
        smoke = gates.tasks(config, reg, smoke=True)
        self.assertEqual(len(smoke), 18)
        self.assertEqual(len({t["logical_key"] for t in smoke}), 18)
        self.assertFalse(
            {t["logical_key"] for t in smoke}
            & {t["logical_key"] for t in gates.tasks(config, reg)}
        )
        self.assertEqual(len({t["ledger_scope"] for t in smoke}), 1)
        with self.assertRaises(ValueError):
            gates.tasks(config, reg, model="wrong")

    def test_all_terminal_run_never_loads_processors(self):
        from .main import run
        from .utils import load_config

        config = load_config()
        rows = [{"opaque_incident_id": "one", "dataset": "aiops2022"}]
        reg = {"rosters": {"screen": [], "check": rows}}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tasks = gates.tasks(config, reg, model=config["models"][0])
            for t in tasks:
                save_json(
                    root / "flags" / (t["logical_key"] + ".json"),
                    {"status": "done", "logical_key": t["logical_key"]},
                )
            with (
                patch.object(gates, "authorize_run"),
                patch(
                    "RQs.RQ3_6.src.main.cpu_pool",
                    side_effect=AssertionError("no processors"),
                ),
            ):
                self.assertEqual(
                    run(config, reg, root, config["models"][0])["status"],
                    "already_terminal",
                )

    def test_peer_semantics_and_scope(self):
        from copy import deepcopy

        a = {
            "entity": "10001",
            "region": "M",
            "semantic": "cpu",
            "unit": "percent",
            "role": "gauge",
            "values": {"reference_interval_s": [0, 20], "current_interval_s": [20, 40]},
        }
        b = {**a, "entity": "10002"}
        links = [
            {"kind": "hosts", "a": "1000", "b": n} for n in (a["entity"], b["entity"])
        ]
        self.assertTrue(exps.compatible_peer(a, b, links))
        self.assertFalse(exps.compatible_peer(a, b, []))
        for key, wrong in (
            ("unit", "bytes"),
            ("semantic", "memory"),
            ("role", "counter"),
        ):
            self.assertFalse(exps.compatible_peer(a, {**b, key: wrong}, links))
        bad = deepcopy(b)
        bad["values"]["current_interval_s"] = [21, 40]
        self.assertFalse(exps.compatible_peer(a, bad, links))

    def test_observed_anchor_not_static_config_or_constant(self):
        from .utils import ROOT

        config = read_json(ROOT / "RQs/RQ3_6/configs/visual_mechanisms_v1.json")
        a = {
            "entity": "1000",
            "region": "M",
            "semantic": "cpu",
            "unit": "percent",
            "support": 8,
            "values": {"reference_median": 1, "current_median": 2},
        }
        self.assertTrue(exps.anchor_eligibility(a, config)[0])
        self.assertFalse(
            exps.anchor_eligibility({**a, "semantic": "memory_limit_bytes"}, config)[0]
        )
        self.assertFalse(
            exps.anchor_eligibility(
                {**a, "semantic": "k8s.container.memory_request"}, config
            )[0]
        )
        self.assertFalse(
            exps.anchor_eligibility(
                {**a, "values": {"reference_median": 1, "current_median": 1}}, config
            )[0]
        )
        self.assertFalse(exps.anchor_eligibility({**a, "support": 0}, config)[0])

    def test_graph_is_visible_deterministic_and_intact(self):
        from .utils import ROOT

        cfg = read_json(ROOT / "RQs/RQ3_6/configs/visual_mechanisms_v1.json")["visual"]
        facts = [
            {"field": "directed_call_edge", "payload": {"caller": a, "callee": b}}
            for a, b in (("100", "101"), ("101", "100"), ("100", "100"))
        ]
        bindings = [
            {
                "entity": "10001",
                "region": "M",
                "semantic": "observed_cpu",
                "unit": "percent",
            },
            {
                "entity": "9000",
                "region": "M",
                "semantic": "standalone_resource",
                "unit": "bytes",
            },
        ]
        relations = [{"relation": "owns", "from": "100", "to": "10001"}]
        args = (
            "Immutable numeric field = 1.250; calls 100 -> 101",
            facts,
            bindings,
            relations,
            cfg,
        )
        png, manifest = exps.render_relation_input(*args)
        self.assertEqual((png, manifest), exps.render_relation_input(*args))
        self.assertEqual(
            {p["entity"] for p in manifest["primitives"] if "entity" in p},
            {"100", "101", "10001", "9000"},
        )
        self.assertTrue(
            any(
                "observed_cpu" in p.get("binding_label", "")
                for p in manifest["primitives"]
            )
        )
        self.assertEqual(len(manifest["edges"]), 4)
        self.assertTrue(
            any(
                p.get("from") == p.get("to") == "100" and len(set(p["path"])) > 2
                for p in manifest["primitives"]
            )
        )
        for p in manifest["primitives"]:
            if "bbox" in p:
                x, y, right, bottom = p["bbox"]
                self.assertTrue(
                    0 <= x < right <= cfg["width"] and 0 <= y <= bottom <= cfg["height"]
                )
        with self.assertRaises(ValueError):
            exps.render_relation_input(
                "too long\n" * 1000, [], [], [], cfg, screenshot=True
            )

    def test_empty_witness_is_noop(self):
        from types import SimpleNamespace

        from .utils import ROOT

        cfg = read_json(ROOT / "RQs/RQ3_6/configs/visual_mechanisms_v1.json")
        context = {
            "observations": [],
            "relations": [],
            "request_links": [],
            "integrated": {"priority_audit": {}},
            "selection_metadata": {},
            "prepared": SimpleNamespace(public={"packet": {"facts": []}}),
        }
        result = exps.qualify_witnesses(
            context, cfg, SimpleNamespace(cost=lambda s: len(s))
        )
        self.assertEqual(result["raw_text"], "")
        self.assertEqual(result["no_peer_text"], "")
        self.assertEqual(result["packs"], [])


def source_audit(context, row):
    """Save all shared operation rows and source definitions, never infer causality."""
    import csv

    from RQs.RQ3_1.src.exps import _registered_trace_duration_projection

    s = "\n".join(p.get("text", "") for p in exps.sircl_parts(context))
    rows, active = [], False
    for line in s.splitlines():
        if line.startswith("service,operation,"):
            active, header = True, next(csv.reader([line]))
            continue
        if active and line.startswith(("===", "Based on")):
            active = False
        if active and line.strip():
            fields = next(csv.reader([line]))
            if len(fields) == len(header):
                rows.append(dict(zip(header, fields, strict=True)))
    p = [f for f in context["prepared"].public["packet"]["facts"] if f["region"] == "R"]
    window = context["window"]
    if len(window) != 3 or window[0] != 0 or not window[0] <= window[1] <= window[2]:
        raise ValueError("Public relative analysis window changed")
    scale, source = _registered_trace_duration_projection(row["dataset"])
    return {
        "public_window": window,
        "parent_trace_facts": p,
        "sircl_trace_rows": rows,
        "sircl_stored_to_ms_scale": scale,
        "sircl_duration_source": source,
        "parent_stored_duration_unit": context["rq36_parent_trace_unit"],
        "parent_unit_repair": "field labels only; values, latency_lfc smoothing and ranking unchanged",
        "trace_source_audit": context["trace_audit"],
        "interpretation": "Whole-package comparison; parent and native S statistics/splits are not asserted equal",
    }


def cpu_case(args):
    from PIL import Image

    from RQs.RQ3_3.src.utils import OfflineTokens
    from RQs.RQ3_5.src import exps as parent

    from .main import load_context

    config, row, tasks, output = args
    if config.get("family"):
        return cpu_case_mechanisms(args)
    if config.get("stage") == "B":
        return cpu_case_b(args)
    started = time.monotonic()
    root = Path(output)
    context, private = load_context(config, row)
    tokens = OfflineTokens(runtime_config(config))
    initial = digest(context["prepared"].public["packet"])
    blocks = exps.guide_blocks(context, config)
    arms = {a: exps.parts_for(context, a, config) for a in config["arms"]}
    # Nine inherited requests must be byte-identical, not merely semantically close.
    for arm, parts in arms.items():
        if arm not in {"E_S_G_P_V_S", "E_S_G_S_V_P"}:
            reference, _ = parent.parts_for(
                {**context, "ole": {"selected": []}}, arm, config
            )
            expected = (
                exps.parent_unit_labels(reference, context["rq36_parent_trace_unit"])
                if arm in exps.PARENT_UNITS_ARMS
                else reference
            )
            if parts != expected:
                raise ValueError("Inherited request changed: " + arm)
    sbase = arms["E_S_D_P"]
    for arm in ("E_S_D_S", "E_S_G_P_V_S", "E_S_G_S_V_P"):
        if [p for i, p in enumerate(arms[arm]) if i != 1] != [
            p for i, p in enumerate(sbase) if i != 1
        ]:
            raise ValueError(
                "Instruction intervention changed evidence/task/candidates"
            )
    if (
        sbase[1]["text"] != blocks["G_P"] + blocks["V_P"]
        or arms["E_S_D_S"][1]["text"] != blocks["G_S"] + blocks["V_S"]
    ):
        raise ValueError("Guide reconstruction mismatch")
    if (
        arms["E_S_G_P_V_S"][1]["text"] != blocks["G_P"] + blocks["V_S"]
        or arms["E_S_G_S_V_P"][1]["text"] != blocks["G_S"] + blocks["V_P"]
    ):
        raise ValueError("Crossed component not applied")
    if (
        len(
            {
                p[1]["text"]
                for a, p in arms.items()
                if a in {"E_S_D_P", "E_S_D_S", "E_S_G_P_V_S", "E_S_G_S_V_P"}
            }
        )
        != 4
    ):
        raise ValueError("Instruction factorial collapsed")
    poison = {
        **context,
        "ground_truth": "LEAK_PRIVATE_SENTINEL",
        "fault_type": "LEAK_PRIVATE_SENTINEL",
    }
    for arm, parts in arms.items():
        if parts != exps.parts_for(poison, arm, config):
            raise ValueError("Private fields changed public input")
        text = "\n".join(p.get("text", "") for p in parts)
        if re.search(
            r"INC-[A-F0-9]{12}|/home/|ground_truth|LEAK_PRIVATE_SENTINEL|aiops202[25]|aegislab",
            text,
            re.IGNORECASE,
        ):
            raise ValueError("Private/source identity in model-visible prompt")
        if (
            arm.startswith("E_")
            and text.count("Candidate IDs (exhaustive, fixed order):") != 1
        ):
            raise ValueError("Candidate list duplicated")
    if any(not re.fullmatch(r"\d{3,5}", c) for c in context["candidates"]):
        raise ValueError("Non-numeric candidate")
    units, signatures = [], {}
    for task in tasks:
        request = exps.compile_unit(task, context, private, config, tokens)
        from RQs.RQ3_4.src.main import response_audit

        audit = response_audit(
            request, '{"services":[],"reason":"CPU regression","confidence":"low"}'
        )
        if "status" not in audit or "image_hashes" not in request["projection"]:
            raise ValueError("Shared post-response audit interface incomplete")
        arm, model = task["dimensions"]["arm"], task["model"]
        # Supplying entirely different scoring metadata cannot change model inputs.
        if (
            request["actual"]
            != exps.compile_unit(
                task, context, {"root_ids": ["LEAK_PRIVATE_SENTINEL"]}, config, tokens
            )["actual"]
        ):
            raise ValueError("Evaluator-private labels leaked into request")
        signatures.setdefault(arm, []).append(digest(request["actual"]["parts"]))
        folder = root / "cpu_inputs" / row["opaque_incident_id"] / model / arm
        save_json(folder / "request.json", request["actual"])
        save_json(folder / "projection.json", request["projection"])
        for i, part in enumerate(request["parts"]):
            if part["type"] == "image":
                from vlmrca.run_state import atomic_write

                image = Image.open(io.BytesIO(part["png"]))
                image.verify()
                atomic_write(folder / f"image_{i}.png", part["png"])
        units.append(
            {
                "model": model,
                "arm": arm,
                "counts": request["projection"]["model_token_counts"],
                "input_identity": request["input_identity"],
                "request": str(folder / "request.json"),
            }
        )
    if any(len(set(values)) != 1 for values in signatures.values()):
        raise ValueError("Different public inputs across models")
    if initial != digest(context["prepared"].public["packet"]):
        raise ValueError("Shared cached evidence mutated")
    audit = source_audit(context, row)
    save_json(root / "source_audits" / (row["opaque_incident_id"] + ".json"), audit)
    save_json(root / "guide_blocks" / (row["opaque_incident_id"] + ".json"), blocks)
    return {
        "case": row["opaque_incident_id"],
        "dataset": row["dataset"],
        "units": units,
        "elapsed_s": time.monotonic() - started,
        "affinity": sorted(os.sched_getaffinity(0)),
        "source_audit": str(
            root / "source_audits" / (row["opaque_incident_id"] + ".json")
        ),
    }


def cpu_case_b(args):
    """Full request construction for all B arms, without contacting a server."""
    from collections import Counter

    from PIL import Image

    from RQs.RQ1_1.src.exps import _natural_fact_line
    from RQs.RQ3_3.src import exps as parent
    from RQs.RQ3_3.src.utils import OfflineTokens
    from RQs.RQ3_4.src.exps import integrated_parts
    from vlmrca.run_state import atomic_write

    from .main import load_context

    config, row, tasks, output = args
    root, started = Path(output), time.monotonic()
    context, private = load_context(config, row)
    packet = context["prepared"].public["packet"]
    before = digest(packet)
    tokens = OfflineTokens(runtime_config(config))
    data = exps.prepare_stage_b(context, config, tokens)
    arms = {a: exps.parts_for(context, a, config) for a in config["arms"]}
    for arm, source in (
        ("B0_G", "TPV"),
        ("MORE", "P0_MORE_TRUE"),
        ("W_OLD_G", "P1H1K0_G"),
        ("W_OLD_T", "P1H1K0_T"),
    ):
        expected = exps.parent_unit_labels(
            integrated_parts(context, source), context["rq36_parent_trace_unit"]
        )
        if arms[arm] != expected:
            raise ValueError("Inherited B input changed: " + arm)
    lines = [_natural_fact_line(f) for f in packet["facts"] if f["region"] == "G"]
    if Counter(data["order"].splitlines()) != Counter(lines):
        raise ValueError("G order control changed facts")
    _, ordered_facts = exps.graph_records(context, relational=True)
    if Counter(digest(f) for f in ordered_facts) != Counter(
        digest(f) for f in packet["facts"] if f["region"] == "G"
    ):
        raise ValueError("Strong text changed G inventory")
    q = data["selection"]
    if len(q["packs"]) > 4 or tokens.cost(q["raw_text"]) > 2048:
        raise ValueError("Qualified witness budget exceeded")
    for p, ablated in zip(q["packs"], q["no_peer"], strict=True):
        if (
            len(p["members"]) > 3
            or not exps.anchor_eligibility(q["display"][p["anchor"]], config)[0]
        ):
            raise ValueError("Bad witness qualification")
        if set(ablated["members"]) != set(p["members"]) - set(p["peer_members"]):
            raise ValueError("No-peer intervention reselected or removed its anchor")
        for peer in p["peer_members"]:
            if not exps.compatible_peer(
                q["display"][p["anchor"]], q["display"][peer], context["relations"]
            ):
                raise ValueError("Incompatible peer")
    matched = ("W_QUAL_T", "W_QUAL_G", "W_SCOPE_T", "W_SCOPE_G")
    if (
        len(
            {
                digest(
                    [
                        data["audits"][a]["selected_observation_inventory"],
                        data["audits"][a]["selected_relation_inventory"],
                    ]
                )
                for a in matched
            }
        )
        != 1
    ):
        raise ValueError("Qualified matched arms differ in witness facts")
    # Base non-G content, including the exact candidate list, cannot disappear.
    base = parent.inherited_parts(context, carrier="T")
    ledger = parent.g_ledger(packet)
    invariant = exps.parent_unit_labels(
        [p for p in base if p.get("text") != ledger], context["rq36_parent_trace_unit"]
    )
    for arm, parts in arms.items():
        for part in invariant:
            if part not in parts:
                raise ValueError("B intervention changed common evidence: " + arm)
        text = "\n".join(p.get("text", "") for p in parts)
        if re.search(
            r"INC-[A-F0-9]{12}|/home/|ground_truth|LEAK_PRIVATE_SENTINEL|aiops202[25]|aegislab",
            text,
            re.IGNORECASE,
        ):
            raise ValueError("Source identity exposed")
    # Renderer captions are model-visible too, not exempt from leakage checks.
    for manifest in data["render_manifests"].values():
        for primitive in manifest["primitives"]:
            if re.search(
                r"INC-|/home/|ground_truth|aiops202[25]|aegislab",
                primitive.get("text", ""),
                re.IGNORECASE,
            ):
                raise ValueError("Source identity in PNG primitive")
        if manifest["geometry"] != [
            config["visual"]["width"],
            config["visual"]["height"],
        ]:
            raise ValueError("Unexpected image geometry")
    units, signatures = [], {}
    for task in tasks:
        request = exps.compile_unit(task, context, private, config, tokens)
        from RQs.RQ3_4.src.main import response_audit

        audit = response_audit(
            request, '{"services":[],"reason":"CPU regression","confidence":"low"}'
        )
        if "status" not in audit or "image_hashes" not in request["projection"]:
            raise ValueError("Response audit persistence contract mismatch")
        if (
            request["actual"]
            != exps.compile_unit(
                task, context, {"root_ids": ["LEAK_PRIVATE_SENTINEL"]}, config, tokens
            )["actual"]
        ):
            raise ValueError("Private labels changed model input")
        arm, model = task["dimensions"]["arm"], task["model"]
        signatures.setdefault(arm, []).append(digest(request["actual"]["parts"]))
        folder = root / "cpu_inputs" / row["opaque_incident_id"] / model / arm
        save_json(folder / "request.json", request["actual"])
        save_json(folder / "projection.json", request["projection"])
        for i, part in enumerate(request["parts"]):
            if part["type"] == "image":
                Image.open(io.BytesIO(part["png"])).verify()
                atomic_write(folder / f"image_{i}.png", part["png"])
        units.append(
            {
                "model": model,
                "arm": arm,
                "counts": request["projection"]["model_token_counts"],
                "input_identity": request["input_identity"],
                "request": str(folder / "request.json"),
            }
        )
    if any(len(set(values)) != 1 for values in signatures.values()) or before != digest(
        packet
    ):
        raise ValueError("Model inputs differ or inherited cache mutated")
    audit_path = root / "source_audits" / (row["opaque_incident_id"] + ".json")
    save_json(
        audit_path,
        {
            "witness": {k: v for k, v in q.items() if k != "display"},
            "source": source_audit(context, row),
            "render_manifests": data["render_manifests"],
        },
    )
    return {
        "case": row["opaque_incident_id"],
        "dataset": row["dataset"],
        "units": units,
        "elapsed_s": time.monotonic() - started,
        "affinity": sorted(os.sched_getaffinity(0)),
        "source_audit": str(audit_path),
    }


def cpu_case_mechanisms(args):
    from collections import Counter

    from PIL import Image

    from RQs.RQ3_3.src import exps as parent
    from RQs.RQ3_3.src.utils import OfflineTokens
    from RQs.RQ3_4.src.main import response_audit
    from vlmrca.run_state import atomic_write

    from .main import load_context

    config, row, tasks, output = args
    root, started = Path(output), time.monotonic()
    context, private = load_context(config, row)
    tokens = OfflineTokens(runtime_config(config))
    packet = context["prepared"].public["packet"]
    before = digest(packet)
    data = exps.prepare_mechanisms(context, config, tokens)
    base = parent.inherited_parts(context, carrier="T")
    ledger = parent.g_ledger(packet)
    invariant = exps.parent_unit_labels(
        [p for p in base if p.get("text") != ledger], context["rq36_parent_trace_unit"]
    )
    arms = {a: exps.parts_for(context, a, config) for a in config["arms"]}
    leak = re.compile(
        r"INC-[A-F0-9]{12}|/home/|ground_truth|LEAK_PRIVATE_SENTINEL|aiops202[25]|aegislab",
        re.IGNORECASE,
    )
    for arm, parts in arms.items():
        if any(p not in parts for p in invariant):
            raise ValueError("Common task/M/R/L/candidates changed: " + arm)
        if leak.search("\n".join(p.get("text", "") for p in parts)):
            raise ValueError("Source identity in request")
        record = data["records"][arm]
        if tokens.cost(record["appendix"]) > config["witness"]["max_tokens"]:
            raise ValueError("Witness budget exceeded")
        twin = arm[:-1] + ("T" if arm.endswith("G") else "G")
        for key in (
            "selected_observation_inventory",
            "selected_relation_inventory",
            "g_visible_ledger_hash",
        ):
            if data["audits"][arm][key] != data["audits"][twin][key]:
                raise ValueError("Within-policy T/G facts differ")
        manifest = data["audits"][arm]["render_manifest"]
        if manifest:
            if manifest["visible_ledger_sha256"] != digest(record["text"]):
                raise ValueError("Renderer ledger differs from text")
            width, height = manifest["geometry"]
            for primitive in manifest["primitives"]:
                if leak.search(primitive.get("text", "")):
                    raise ValueError("Private/source identity in PNG")
                if "bbox" in primitive:
                    x, y, right, bottom = primitive["bbox"]
                    if not 0 <= x <= right <= width or not 0 <= y <= bottom <= height:
                        raise ValueError("Primitive outside canvas")
    if config["family"] == "g_components":
        for policy, key in (
            ("NO_RANK", "rank"),
            ("NO_SEVERITY", "severity_z_display"),
            ("NO_ONSET", "onset_rel_min_display"),
        ):
            if any(
                key in f["payload"]
                for f in data["records"][policy + "_T"]["facts"]
                if f["field"] == "propagation_service"
            ):
                raise ValueError("Ablated G field survived")
    elif config["family"] == "scope_competition":
        records = data["records"]
        for role in ("HOST", "PEER", "HOST_PEER", "HP_DEDUP"):
            if [p["anchor"] for p in records[role + "_T"]["packs"]] != data[
                "role_audit"
            ]["anchors"]:
                raise ValueError("Factor changed frozen anchors")
            if (
                data["audits"][role + "_T"]["selected_relation_inventory"]
                != data["audits"]["ANCHOR_T"]["selected_relation_inventory"]
            ):
                raise ValueError("Observation factor also changed relationships")
        if (
            data["audits"]["HOST_PEER_T"]["selected_observation_inventory"]
            != data["audits"]["HP_DEDUP_T"]["selected_observation_inventory"]
        ):
            raise ValueError("Dedup removed unique observation")
    else:
        for kind in ("ALL", "CALL", "DEPLOY"):
            pair = [
                data["records"][kind + "_" + mode + "_T"]["text"]
                for mode in ("ID", "BIND")
            ]
            if Counter(pair[0].splitlines()) != Counter(pair[1].splitlines()):
                raise ValueError("Binding changed atomic rows")
            for mode in ("ID", "BIND"):
                record = data["records"][kind + "_" + mode + "_T"]
                relations = [r["kind"] for p in record["packs"] for r in p["relations"]]
                if kind == "CALL" and set(relations) & {"hosts", "owns"}:
                    raise ValueError("Deployment survived call-only intervention")
                if kind == "DEPLOY" and (
                    set(relations) & {"calls", "request_parent"}
                    or any(f["field"] == "directed_call_edge" for f in record["facts"])
                ):
                    raise ValueError("Call survived deploy-only intervention")
    units, signatures = [], {}
    for task in tasks:
        request = exps.compile_unit(task, context, private, config, tokens)
        if "status" not in response_audit(
            request, '{"services":[],"reason":"CPU","confidence":"low"}'
        ):
            raise ValueError("Response audit contract broken")
        poisoned = exps.compile_unit(
            task,
            {**context, "ground_truth": "LEAK_PRIVATE_SENTINEL"},
            {"root_ids": ["LEAK_PRIVATE_SENTINEL"]},
            config,
            tokens,
        )
        if request["actual"] != poisoned["actual"]:
            raise ValueError("Private label changed public request")
        arm, model = task["dimensions"]["arm"], task["model"]
        signatures.setdefault(arm, []).append(digest(request["actual"]["parts"]))
        folder = root / "cpu_inputs" / row["opaque_incident_id"] / model / arm
        save_json(folder / "request.json", request["actual"])
        save_json(folder / "projection.json", request["projection"])
        for i, part in enumerate(request["parts"]):
            if part["type"] == "image":
                Image.open(io.BytesIO(part["png"])).verify()
                atomic_write(folder / f"image_{i}.png", part["png"])
        units.append(
            {
                "arm": arm,
                "model": model,
                "input_identity": request["input_identity"],
                "counts": request["projection"]["model_token_counts"],
                "request": str(folder / "request.json"),
            }
        )
    if any(len(set(v)) != 1 for v in signatures.values()) or digest(packet) != before:
        raise ValueError("Public inputs differ between models or cache mutated")
    # Byte-deterministic render, including dense/binding mode, not manifest-only.
    graph_arm = next(
        (a for a in config["arms"] if data["audits"][a]["render_manifest"]), None
    )
    if graph_arm:
        r = data["records"][graph_arm]
        png, manifest = exps.render_relation_input(
            r["text"],
            r["facts"],
            r["bindings"],
            r["relations"],
            data["audits"][graph_arm]["geometry_policy"],
        )
        if png != r["png"] or manifest != data["audits"][graph_arm]["render_manifest"]:
            raise ValueError("Renderer nondeterministic")
    save_json(
        root / "source_audits" / (row["opaque_incident_id"] + ".json"), data["audits"]
    )
    return {
        "case": row["opaque_incident_id"],
        "dataset": row["dataset"],
        "units": units,
        "elapsed_s": time.monotonic() - started,
        "affinity": sorted(os.sched_getaffinity(0)),
    }


def capacity_case(args):
    """Full compiler for every registered case, only compact summaries cross IPC."""
    from .main import compile_case

    started = time.monotonic()
    units = compile_case(args)
    return {
        "case": args[1][0]["case"]["opaque_incident_id"],
        "dataset": args[1][0]["case"]["dataset"],
        "elapsed_s": time.monotonic() - started,
        "units": [
            {
                "arm": t["dimensions"]["arm"],
                "counts": r["projection"]["model_token_counts"],
                "public_input_hash": digest(r["actual"]["parts"]),
                "role_audit": r["projection"].get("role_audit", {}),
                "geometry": r["projection"].get("geometry_policy"),
            }
            for t, r in units
        ],
    }


def capacity_qualification(config, registration, root):
    from collections import defaultdict

    from RQs.RQ3_3.src.main import interleaved_sources

    from .main import close_pool, cpu_pool

    started = time.monotonic()
    grouped = defaultdict(list)
    # compile_unit preflights both tokenizers even when only one envelope is built.
    for task in gates.tasks(config, registration, model=config["models"][0]):
        grouped[task["case"]["opaque_incident_id"]].append(task)
    ordered = interleaved_sources([ts[0]["case"] for ts in grouped.values()])
    report = {
        "status": "failed",
        "contract_hash": digest(registration["contract"]),
        "cases": [],
    }
    pool, queue, _ = cpu_pool(config["execution"]["workers"])
    futures = [
        pool.submit(capacity_case, (config, grouped[r["opaque_incident_id"]]))
        for r in ordered
    ]
    try:
        for f in cf.as_completed(futures, timeout=1800):
            report["cases"].append(f.result())
            if len(report["cases"]) % 10 == 0:
                print(
                    json_line(
                        {"capacity_cases": len(report["cases"]), "total": len(futures)}
                    ),
                    flush=True,
                )
        report["status"] = "passed"
    except BaseException as exc:
        report["error"] = repr(exc)
        raise
    finally:
        close_pool(pool, queue, abort=report["status"] != "passed")
        report["elapsed_s"] = time.monotonic() - started
        save_json(root / "capacity_qualification.json", report)
    return {
        "status": "passed",
        "cases": len(report["cases"]),
        "elapsed_s": report["elapsed_s"],
    }


def cpu_qualification(config, registration, root):
    from .main import close_pool, cpu_pool
    from .utils import call_count

    started, before = time.monotonic(), call_count(root)
    report = {
        "status": "failed",
        "contract_hash": digest(registration["contract"]),
        "cases": [],
    }
    pool = queue = None
    old_alarm = signal.getsignal(signal.SIGALRM)

    def expire(*_):
        raise TimeoutError("CPU regression exceeds 1800 seconds")

    signal.signal(signal.SIGALRM, expire)
    signal.setitimer(signal.ITIMER_REAL, config["qualification"]["cpu_seconds"])
    try:
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(ProtocolTests)
        )
        report["unit_tests"] = {
            "run": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
        }
        if not result.wasSuccessful():
            raise ValueError("Unit regression failed")
        rows = gates.qualification_rows(config, registration)
        tasks = gates.tasks(config, registration, cpu=True)
        pool, queue, _ = cpu_pool(len(rows))
        futures = [
            pool.submit(
                cpu_case,
                (config, row, [t for t in tasks if t["case"] == row], str(root)),
            )
            for row in rows
        ]
        for future in cf.as_completed(futures):
            value = future.result()
            report["cases"].append(value)
            print(
                json_line({"cpu_case": value["case"], "elapsed_s": value["elapsed_s"]}),
                flush=True,
            )
        if call_count(root) != before:
            raise ValueError("CPU regression unexpectedly initiated a model call")
        if len({c["affinity"][0] for c in report["cases"]}) != len(rows) or any(
            len(c["affinity"]) != 1 for c in report["cases"]
        ):
            raise ValueError("CPU workers not pinned to distinct cores")
        report["status"] = "passed"
    except BaseException as exc:
        report["error"] = repr(exc)
        raise
    finally:
        if pool is not None:
            close_pool(pool, queue, abort=report["status"] != "passed")
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_alarm)
        report.update(
            elapsed_s=time.monotonic() - started,
            new_model_calls=call_count(root) - before,
        )
        save_json(root / "cpu_qualification.json", report)
    return report


def json_line(value):
    import json

    return json.dumps(value, ensure_ascii=False)


def review(config, registration, root):
    from RQs.RQ3_5.src.tests import review_flags

    flags = []
    for task in gates.tasks(config, registration, smoke=True):
        flag = terminal_flag(root, task)
        if flag is not None:
            if flag["status"] != "done":
                raise ValueError("Smoke contains a failed call")
            flags.append(flag)
    units = review_flags(flags)
    # Saved requests must match their CPU-qualified input, excluding audit metadata.
    cpu = read_json(root / "cpu_qualification.json")
    allowed = {u["input_identity"] for c in cpu["cases"] for u in c["units"]}
    if any(f["input_identity"] not in allowed for f in flags):
        raise ValueError("GPU smoke input differs from CPU-qualified request")
    return {
        "status": "passed",
        "completed_units": len(units),
        "planned_units": 18,
        "units": units,
        "uncompleted_not_live_validated": 18 - len(units),
    }
