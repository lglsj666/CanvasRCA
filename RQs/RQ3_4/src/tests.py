"""Fast CPU-only checks, including open-world and inconsistent-KB regressions."""

import unittest

from .exps import (
    PublicEvidence,
    compile_public,
    output_contract_findings,
    screen_reason,
    verified_twin_parts,
)
from .gates import ClaimVerifier
from .utils import candidates, decimal, display_interval, input_parts, json_fields

GUIDE = "three digits identify a service, four digits identify a node, and five digits identify a pod"
CANDIDATES = 'Candidate IDs (exhaustive, fixed order): ["123","456","1234","12345"]'


def text(value):
    return {"type": "text", "text": value}


def fixture():
    return PublicEvidence(
        ("123", "456"),
        [{"text": CANDIDATES}],
        {"123": "service"},
        [{"text": GUIDE}],
        {
            "onset:123": [
                {
                    "low": "4.85",
                    "high": "4.95",
                    "unit": "minutes",
                    "source": {"text": "123 +4.9m"},
                }
            ],
            "onset:456": [
                {
                    "low": "5.15",
                    "high": "5.25",
                    "unit": "minutes",
                    "source": {"text": "456 +5.2m"},
                }
            ],
        },
        {("calls", "123", "456"): [{"text": "123 calls 456"}]},
    )


class ClaimTests(unittest.TestCase):
    def test_scoped_smoke_repair_approval(self):
        import tempfile
        from pathlib import Path

        from .main import smoke_policy
        from .utils import digest, save_json

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage = "exp_verified_visual_binding"
            original = {"status": "failed", "initiated_calls": 9}
            save_json(root / "smokes" / (stage + ".json"), original)
            self.assertEqual(smoke_policy(root, stage)["scope_limit"], 18)
            with self.assertRaises(FileNotFoundError):
                smoke_policy(root, stage, True)
            approval = {
                "experiment": stage,
                "user_approved": True,
                "previous_calls": 9,
                "additional_calls_max": 16,
                "window_seconds": 600,
                "original_report_hash": digest(original),
            }
            path = root / "repair_authorizations/visual_binding_v1.json"
            save_json(path, approval)
            self.assertEqual(smoke_policy(root, stage, True)["scope_limit"], 25)
            with self.assertRaises(ValueError):
                smoke_policy(root, "exp_contract_alignment", True)
            save_json(path, {**approval, "additional_calls_max": 17})
            with self.assertRaises(ValueError):
                smoke_policy(root, stage, True)

    def test_public_boundary(self):
        with self.assertRaises(ValueError):
            input_parts({"parts": [], "ground_truth": "123"})

    def test_candidate_contract(self):
        evidence = compile_public([text(GUIDE), text(CANDIDATES)])
        errors = output_contract_findings(
            {"services": ["123", "node-1234", "123"]}, evidence
        )
        self.assertEqual(
            [e["kind"] for e in errors], ["unknown_candidate", "duplicate_candidate"]
        )
        verifier = ClaimVerifier(evidence)
        self.assertEqual(
            verifier.verify({"kind": "candidate", "entity": "999"})["verdict"],
            "refuted",
        )

    def test_conflicting_candidates(self):
        with self.assertRaises(ValueError):
            candidates([text(CANDIDATES), text('Candidate IDs (fixed): ["123"]')])

    def test_no_invented_type_contract(self):
        verifier = ClaimVerifier(compile_public([text(CANDIDATES)]))
        self.assertEqual(
            verifier.verify({"kind": "type", "entity": "123", "entity_type": "node"})[
                "verdict"
            ],
            "unknown",
        )

    def test_type_refutation(self):
        verifier = ClaimVerifier(fixture())
        self.assertEqual(
            verifier.verify({"kind": "type", "entity": "123", "entity_type": "node"})[
                "verdict"
            ],
            "refuted",
        )

    def test_time_order_and_core(self):
        verifier = ClaimVerifier(fixture())
        yes = verifier.verify(
            {"kind": "before", "left": "onset:123", "right": "onset:456"}
        )
        no = verifier.verify(
            {"kind": "before", "left": "onset:456", "right": "onset:123"}
        )
        self.assertEqual((yes["verdict"], no["verdict"]), ("entailed", "refuted"))
        self.assertEqual(len(no["sources"]), 2)

    def test_equal_intervals_not_ordered(self):
        e = fixture()
        e.numbers["onset:456"] = e.numbers["onset:123"]
        result = ClaimVerifier(e).verify(
            {"kind": "before", "left": "onset:123", "right": "onset:456"}
        )
        self.assertEqual(result["verdict"], "unknown")

    def test_rounded_display_is_not_exact_entailment(self):
        v = ClaimVerifier(fixture())
        self.assertEqual(
            v.verify(
                {
                    "kind": "display_number",
                    "quantity": "onset:123",
                    "value": "4.9",
                    "unit": "minutes",
                }
            )["verdict"],
            "compatible_display",
        )
        self.assertEqual(
            v.verify(
                {
                    "kind": "number",
                    "quantity": "onset:123",
                    "value": "4.9",
                    "unit": "minutes",
                }
            )["verdict"],
            "unknown",
        )
        self.assertEqual(
            v.verify(
                {
                    "kind": "display_number",
                    "quantity": "onset:123",
                    "value": "5.2",
                    "unit": "minutes",
                }
            )["verdict"],
            "refuted",
        )

    def test_inconsistent_evidence_no_explosion(self):
        e = fixture()
        e.numbers["onset:123"].append(
            {"low": "8", "high": "9", "unit": "minutes", "source": {"text": "conflict"}}
        )
        result = ClaimVerifier(e).verify({"kind": "candidate", "entity": "123"})
        self.assertEqual(result["verdict"], "inconsistent_evidence")

    def test_absent_edge_is_unknown_and_no_causality(self):
        v = ClaimVerifier(fixture())
        self.assertEqual(
            v.verify(
                {"kind": "relation", "relation": "calls", "left": "456", "right": "123"}
            )["verdict"],
            "unknown",
        )
        self.assertEqual(
            v.verify(
                {"kind": "relation", "relation": "calls", "left": "123", "right": "456"}
            )["verdict"],
            "entailed",
        )
        self.assertEqual(
            v.verify({"kind": "root_cause", "entity": "123"})["verdict"], "unsupported"
        )

    def test_units_not_assumed_compatible(self):
        v = ClaimVerifier(fixture())
        self.assertEqual(
            v.verify(
                {
                    "kind": "number",
                    "quantity": "onset:123",
                    "value": "4.9",
                    "unit": "seconds",
                }
            )["verdict"],
            "unknown",
        )

    def test_finite_values(self):
        for value in ["NaN", float("inf"), True]:
            with self.assertRaises((ValueError, TypeError)):
                decimal(value)
        self.assertEqual(display_interval("4.9"), ("4.85", "4.95"))

    def test_unsupported_negation_not_silently_ignored(self):
        v = ClaimVerifier(fixture())
        self.assertEqual(
            v.verify(
                {
                    "kind": "type",
                    "entity": "123",
                    "entity_type": "node",
                    "negated": True,
                }
            )["verdict"],
            "unsupported",
        )
        self.assertEqual(
            v.verify(
                {
                    "kind": "relation",
                    "relation": "calls",
                    "left": "123",
                    "right": "456",
                    "negated": True,
                }
            )["verdict"],
            "refuted",
        )

    def test_metric_semantics_not_just_units(self):
        e = fixture()
        e.numbers["cpu"] = [
            {
                "low": "1",
                "high": "1",
                "unit": "source_unit",
                "semantic": "cpu",
                "source": {},
            }
        ]
        e.numbers["memory"] = [
            {
                "low": "2",
                "high": "2",
                "unit": "source_unit",
                "semantic": "memory",
                "source": {},
            }
        ]
        self.assertEqual(
            ClaimVerifier(e).verify(
                {"kind": "less_than", "left": "cpu", "right": "memory"}
            )["verdict"],
            "unsupported",
        )

    def test_safe_json_field_parser(self):
        result = json_fields(
            'field=test; operation="key=other; ()" n=3 candidate=["123"]'
        )
        self.assertEqual(
            result, {"operation": "key=other; ()", "n": 3, "candidate": ["123"]}
        )

    def test_compile_onset(self):
        line = 'Topology evidence; field=propagation_service; service="123" onset_rel_min_display="+4.9m"'
        e = compile_public([text(CANDIDATES), text(line)])
        self.assertEqual(e.numbers["onset:123"][0]["low"], "4.85")
        self.assertEqual(e.numbers["onset:123"][0]["source"]["line"], 1)

    def test_null_onset_and_appendix_relation_schemas(self):
        onset = 'Topology evidence; field=propagation_service; service="123" onset_rel_min_display=null'
        appendix = 'Additional observations\n{"from":"1234","relation":"hosts","to":"12345"}\n{"parent":["123","GET"],"child":["456","GET"],"relation":"observed parent span -> child span","supporting_span_pairs":9}'
        e = compile_public([text(CANDIDATES), text(onset), text(appendix)])
        self.assertFalse(e.numbers)
        self.assertIn(("hosts", "1234", "12345"), e.relations)
        self.assertEqual(len(e.warnings), 1)

    def test_twin_only_when_inputs_match(self):
        ledger = text(
            'G: calls A -> B\nTopology evidence; field=directed_call_edge; caller="123" callee="456"'
        )
        wt = [text(CANDIDATES), ledger, text("observed")]
        wg = [
            text(CANDIDATES),
            text("How to read the real telemetry dashboard image:"),
            {"type": "image", "sha256": "abc"},
            text("observed"),
        ]
        parts, state = verified_twin_parts(wg, wt, wg)
        self.assertEqual(state, "paired_ledger_same_image")
        self.assertEqual(parts[-1], ledger)
        self.assertEqual(
            verified_twin_parts(wg, wt + [text("extra")], wg)[1], "twin_text_mismatch"
        )
        altered = [text(CANDIDATES), {"type": "image", "sha256": "different"}]
        self.assertEqual(
            verified_twin_parts(altered, wt, wg)[1], "target_image_mismatch"
        )

    def test_prose_screen_is_partial_review_only(self):
        claims = screen_reason(
            "Node 123 shows a peak starting at 4.9m. Service 456 has onset (5.2m). Graph node 123 is linked."
        )
        self.assertEqual(len(claims), 4)
        self.assertTrue(all(c["review_required"] for c in claims))
        self.assertEqual(
            [c["value"] for c in claims if c["kind"] == "display_number"],
            ["4.9", "5.2"],
        )
        self.assertEqual(screen_reason("There is insufficient evidence."), [])

    def test_relation_claim_and_real_source_coordinates(self):
        claims = screen_reason("The topology shows 123 calls 456.")
        self.assertEqual(claims[0]["relation"], "calls")
        self.assertEqual(
            ClaimVerifier(fixture()).verify(claims[0])["verdict"], "entailed"
        )
        line = 'Topology evidence; field=propagation_service; service="123" onset_rel_min_display="+4.9m"'
        e = compile_public(
            [text(CANDIDATES), text(line)],
            {
                "input_path": "visual.json",
                "part_origins": {"1": {"artifact": "twin.json", "part": 3}},
            },
        )
        source = e.numbers["onset:123"][0]["source"]
        self.assertEqual(
            (source["artifact"], source["part"], source["compiled_part"]),
            ("twin.json", 3, 1),
        )


def integrated_fixture():
    from types import SimpleNamespace

    rows = []
    for i, entity in enumerate(("12345", "12346", "12347", "1234", "5678", "123")):
        rows.append(
            {
                "id": f"o{i}",
                "source_key": f"safe:{i}",
                "entity": entity,
                "region": "M",
                "semantic": "memory_bytes",
                "unit": "bytes",
                "role": "usage",
                "support": 30 + i,
                "source_rows": [i],
                "sustained": i == 0,
                "values": {
                    "reference_median": 10.0,
                    "current_median": float(20 + i),
                    "reference_mad": 2.0,
                    "reference_samples": 20,
                    "current_samples": 10,
                    "reference_interval_s": [0, 10],
                    "current_interval_s": [10, 20],
                },
            }
        )
    relations = [
        {"id": str(i), "source_key": str(i), "kind": k, "a": a, "b": b}
        for i, (k, a, b) in enumerate(
            [
                ("hosts", "1234", "12345"),
                ("hosts", "1234", "12346"),
                ("hosts", "5678", "12347"),
                ("owns", "123", "12345"),
                ("owns", "123", "12346"),
                ("owns", "123", "12347"),
            ]
        )
    ]
    return {
        "observations": rows,
        "relations": relations,
        "request_links": [],
        "cohorts": [],
        "selection_metadata": {
            r["id"]: {
                "scale": 3.0,
                "sustained_fraction": (0.9 if i == 0 else 0.1),
                "finite_bins": [float(n + i) for n in range(16)],
            }
            for i, r in enumerate(rows)
        },
        "candidates": [r["entity"] for r in rows],
        "prepared": SimpleNamespace(public={"packet": {"facts": []}}, private={}),
    }


class CheapTokens:
    def cost(self, text):
        return len(text) // 4


class IntegratedTests(unittest.TestCase):
    def setUp(self):
        from .utils import integrated_config

        self.config = integrated_config()
        self.context = integrated_fixture()

    def test_clock_projection_preserves_differences_and_source(self):
        from copy import deepcopy

        from .exps import clock_observation_index

        rows = deepcopy(self.context["observations"][:3])
        for i, row in enumerate(rows[:2]):
            row.update(semantic="container_start_time_seconds", unit="source_unit")
            row["values"].update(
                reference_median=1647145400.25 + 90 * i,
                current_median=1647145520.75 + 90 * i,
            )
        rows[2]["values"]["current_median"] = 1647145400.25  # bytes, not a clock
        before = deepcopy(rows)
        index, audit = clock_observation_index(rows, self.config)
        self.assertEqual(rows, before)
        self.assertEqual(index[rows[0]["id"]]["values"]["reference_median"], 0)
        self.assertEqual(index[rows[0]["id"]]["values"]["current_median"], 120.5)
        self.assertEqual(index[rows[1]["id"]]["values"]["reference_median"], 90)
        self.assertEqual(index[rows[0]["id"]]["values"]["reference_mad"], 2)
        self.assertEqual(index[rows[2]["id"]], rows[2])
        self.assertEqual(audit, {"version": "relative_clock_v1", "observations": 2})
        for row in rows[:2]:
            row["values"]["reference_median"] += 1000000
            row["values"]["current_median"] += 1000000
        self.assertEqual(clock_observation_index(rows, self.config)[0], index)

    def test_clock_projection_unknown_and_null_values(self):
        from copy import deepcopy

        from .exps import clock_observation_index

        row = deepcopy(self.context["observations"][0])
        row.update(semantic="container_last_seen", unit="seconds")
        row["values"].update(reference_median=1647145400, current_median=None)
        out, _ = clock_observation_index([row], self.config)
        self.assertIsNone(out[row["id"]]["values"]["current_median"])
        for bad in [0, -1, True, float("nan"), float("inf")]:
            row["values"]["current_median"] = bad
            with self.assertRaises((ValueError, TypeError)):
                clock_observation_index([row], self.config)
        row["values"]["current_median"] = 1647145500
        row["unit"] = "milliseconds"
        with self.assertRaises(ValueError):
            clock_observation_index([row], self.config)
        row["unit"] = "seconds"
        row["values"]["unregistered_clock_field"] = 1647145400
        with self.assertRaises(ValueError):
            clock_observation_index([row], self.config)

    def test_clock_safety_net_is_semantic_not_large_number_filter(self):
        from .exps import assert_no_absolute_clock

        for name in (
            "container_start_time_seconds",
            "container_last_seen",
            "istio_agent_process_start_time_seconds",
            "unknown_boot_time_seconds",
        ):
            for number in ("1647145400.0", "1.6471454e+09", "1647145400000"):
                with self.assertRaisesRegex(ValueError, "Absolute clock"):
                    assert_no_absolute_clock([text(f"{name} current={number}")])
        assert_no_absolute_clock([text("memory_bytes current=1647145400.0")])
        assert_no_absolute_clock(
            [
                text(
                    "container_start_time_seconds unit=relative_clock_seconds current=120"
                )
            ]
        )

    def test_clock_selection_has_safe_payload_and_certified_relations(self):
        import json

        from .exps import (
            CLOCK_GUIDE,
            assert_no_absolute_clock,
            relation_pair_blocks,
            select_packs,
        )

        c = self.context
        for row in c["observations"]:
            row.update(semantic="container_start_time_seconds", unit="seconds")
            row["values"].update(reference_median=1647145400, current_median=1647145520)
        selected = select_packs(c, CheapTokens(), self.config, 1, 1)
        raw = selected["raw_text"]
        self.assertTrue(raw.startswith("Additional observations"))
        self.assertIn(CLOCK_GUIDE, raw)
        self.assertNotIn("1647145400", raw)
        self.assertNotIn("1647145520", raw)
        self.assertLessEqual(selected["tokens"], 2048)
        assert_no_absolute_clock([text(raw)])
        parts = [text(GUIDE), text(CANDIDATES), text(raw)]
        blocks = relation_pair_blocks(parts, CheapTokens(), self.config)
        self.assertTrue(
            any("current_median is greater" in p["verified"] for p in blocks["claims"])
        )
        self.assertNotIn("1647145", json.dumps(blocks))

    def test_stale_clock_preparation_is_rejected(self):
        import pickle
        import tempfile
        from pathlib import Path

        from .main import load_integrated_context
        from .utils import save_json

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            save_json(root / "preparation_flags/c.json", {"status": "done"})
            (root / "contexts").mkdir()
            with (root / "contexts/c.pkl").open("wb") as stream:
                pickle.dump({"opaque_incident_id": "c", "integrated": {}}, stream)
            with self.assertRaisesRegex(ValueError, "Stale preparation"):
                load_integrated_context(root, {"opaque_incident_id": "c"})

    def test_sircl_clock_csv_changes_only_clock_means(self):
        from copy import deepcopy

        from .exps import CLOCK_GUIDE, clock_safe_sircl_parts

        row = deepcopy(self.context["observations"][0])
        row.update(semantic="container_last_seen", unit="source_unit")
        row["values"].update(reference_median=1647145400, current_median=1647145460)
        source = "key,regular_mean,regular_std_dev,current_mean,current_std_dev\n12345.container_last_seen,1647145400.0,5.25,1647145460.0,5.25\n12345.memory_bytes,1647145400.0,6.25,1647145400.0,6.25\n"
        parts = [text(source)]
        output = clock_safe_sircl_parts(parts, [row], self.config)
        self.assertEqual(parts, [text(source)])
        self.assertIn(
            "12345.container_last_seen[relative_clock_seconds],0.0,5.25,60.0,5.25",
            output[0]["text"],
        )
        self.assertIn(
            "12345.memory_bytes,1647145400.0,6.25,1647145400.0,6.25", output[0]["text"]
        )
        self.assertTrue(output[0]["text"].startswith(CLOCK_GUIDE))
        with self.assertRaises(ValueError):
            clock_safe_sircl_parts(
                [text(source.replace("regular_mean", "unknown_mean"))],
                [row],
                self.config,
            )

    def test_arm_aliases(self):
        from .exps import arm_factors

        self.assertEqual(arm_factors("G_VERIFIED"), arm_factors("P1H1K1_G"))
        self.assertEqual(arm_factors("T_NONE"), (1, 1, "T", "none"))
        with self.assertRaises(ValueError):
            arm_factors("new_unregistered_arm")

    def test_scope_four_roles_and_budget(self):
        from .exps import pareto_priorities, scope_candidates, select_packs

        c = self.context
        prior = pareto_priorities(c["observations"], c["selection_metadata"])
        packs = scope_candidates(c, prior, 1)
        self.assertTrue(packs)
        self.assertTrue(
            any(set(p["members"]) == {"o0", "o1", "o2", "o3"} for p in packs)
        )
        for p in packs:
            self.assertLessEqual(len(p["members"]), 4)
            self.assertTrue(all(r["kind"] in {"hosts", "owns"} for r in p["relations"]))
        selected = select_packs(c, CheapTokens(), self.config, 1, 1)
        self.assertLessEqual(selected["scope_selected"], 2)
        self.assertLessEqual(len(selected["packs"]), 4)
        self.assertLessEqual(selected["tokens"], 2048)

    def test_ambiguous_or_absent_hosts_no_guessed_scope(self):
        from .exps import pareto_priorities, scope_candidates

        c = self.context
        c["relations"] = [r for r in c["relations"] if r["kind"] == "calls"]
        self.assertEqual(
            scope_candidates(c, pareto_priorities(c["observations"], {}), 1), []
        )

    def test_partial_scope_retains_host_and_focal(self):
        from .exps import pareto_priorities, scope_candidates

        c = self.context
        c["observations"] = [
            o for o in c["observations"] if o["entity"] in {"12345", "1234"}
        ]
        packs = scope_candidates(c, pareto_priorities(c["observations"], {}), 1)
        self.assertTrue(any(set(p["members"]) == {"o0", "o3"} for p in packs))

    def test_pareto_no_units_mixing_or_infinite_zero_scale(self):
        from .exps import observation_priority, pareto_priorities

        c = self.context
        c["observations"][0]["unit"] = "seconds"
        c["selection_metadata"]["o0"]["scale"] = 0
        v, mode = observation_priority(c["observations"][0], c["selection_metadata"])
        self.assertEqual(mode, "absolute_zero_scale")
        self.assertEqual(v[0], 10)
        pri = pareto_priorities(c["observations"], c["selection_metadata"])
        self.assertNotEqual(pri["o0"]["group"], pri["o1"]["group"])

    def test_reverse_curve_is_not_redundant(self):
        from copy import deepcopy

        from .exps import redundant_observation

        a = self.context["observations"][0]
        b = deepcopy(a)
        b["id"] = "opposite"
        b["values"]["current_median"] = -20
        meta = {
            a["id"]: {"finite_bins": list(range(10))},
            b["id"]: {"finite_bins": list(reversed(range(10)))},
        }
        self.assertFalse(redundant_observation(a, b, meta, self.config))

    def test_scope_changes_members_not_only_name(self):
        from .exps import select_packs

        a = select_packs(self.context, CheapTokens(), self.config, 0, 0)
        b = select_packs(self.context, CheapTokens(), self.config, 0, 1)
        self.assertNotEqual(
            [(p["members"], p["relations"]) for p in a["packs"]],
            [(p["members"], p["relations"]) for p in b["packs"]],
        )

    def test_priority_intervention_actual_difference(self):
        from copy import deepcopy

        from .exps import select_packs

        c = self.context
        c["relations"] = []
        for i in range(14):
            o = deepcopy(c["observations"][0])
            o.update(
                id=f"x{i}",
                source_key=f"x{i}",
                entity=str(200 + i),
                support=500 - i,
                sustained=False,
            )
            o["values"]["current_median"] = 10 + (100 if i == 0 else i + 1)
            c["observations"].append(o)
            c["selection_metadata"][o["id"]] = {
                "scale": 1000 if i == 0 else 1,
                "sustained_fraction": 0 if i == 0 else 1,
            }
        a = select_packs(c, CheapTokens(), self.config, 0, 0)
        b = select_packs(c, CheapTokens(), self.config, 1, 0)
        self.assertNotEqual(
            [p["members"] for p in a["packs"]], [p["members"] for p in b["packs"]]
        )

    def test_relation_blocks_same_sources_and_no_causal_assertion(self):
        import json

        from .exps import relation_pair_blocks

        o = self.context["observations"][0]
        raw = {k: o[k] for k in ("entity", "region", "semantic", "unit", "values")}
        parts = [
            text(GUIDE),
            text(CANDIDATES),
            text("Additional observations\n" + json.dumps(raw)),
        ]
        blocks = relation_pair_blocks(parts, CheapTokens(), self.config)
        self.assertTrue(blocks["claims"])
        self.assertTrue(
            all(c["proof"]["verdict"] == "entailed" for c in blocks["claims"])
        )
        self.assertIn("current_median", blocks["repeat"])
        self.assertIn("greater", blocks["verified"])
        self.assertNotIn("root cause", blocks["verified"])
        self.assertLessEqual(CheapTokens().cost(blocks["verified"]), 512)

    def test_overlap_onset_no_certified_order(self):
        from .exps import relation_pair_blocks

        line = lambda ent, t: (
            f'Topology evidence; field=propagation_service; service="{ent}"; onset_rel_min_display="{t}m"'
        )
        blocks = relation_pair_blocks(
            [text(CANDIDATES), text(line("123", "5.0") + "\n" + line("456", "5.0"))],
            CheapTokens(),
            self.config,
        )
        self.assertFalse(any(c["claim"]["kind"] == "before" for c in blocks["claims"]))

    def test_private_fields_do_not_change_selection(self):
        from copy import deepcopy

        from .exps import select_packs

        a = select_packs(self.context, CheapTokens(), self.config, 1, 1)
        c = deepcopy(self.context)
        c["ground_truth"] = "danger"
        c["injection_time"] = 1234567
        self.assertEqual(a, select_packs(c, CheapTokens(), self.config, 1, 1))

    def test_call_budget_and_smoke_matrix(self):
        from .gates import integrated_tasks

        rows = [
            {"opaque_incident_id": "INC-" + str(i), "dataset": d}
            for i, d in enumerate(self.config["qualification"]["datasets"])
        ]
        reg = {"rosters": {"screen": rows, "check": rows}}
        for e in self.config["experiments"]:
            tasks = integrated_tasks(self.config, reg, e["id"], smoke=True)
            self.assertEqual(len(tasks), 18)
            self.assertEqual(len({t["logical_key"] for t in tasks}), 18)
        self.assertEqual(
            sum(
                e["formal_calls_upper"] + e["smoke_calls_upper"]
                for e in self.config["experiments"]
            ),
            3552,
        )

    def test_flag_only_resume_does_not_load_context(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch

        from .gates import integrated_tasks
        from .main import run_integrated
        from .utils import save_json

        rows = [
            {"opaque_incident_id": "INC-" + str(i), "dataset": d}
            for i, d in enumerate(self.config["qualification"]["datasets"])
        ]
        reg = {"rosters": {"screen": rows, "check": rows}}
        stage = self.config["experiments"][0]["id"]
        model = self.config["models"][0]
        with TemporaryDirectory() as folder:
            root = Path(folder)
            for i, t in enumerate(
                integrated_tasks(self.config, reg, stage, model, True)
            ):
                save_json(
                    root / "flags" / (t["logical_key"] + ".json"),
                    {"status": "done" if i % 2 else "fail"},
                )
            with patch(
                "RQs.RQ3_4.src.main.load_integrated_context",
                side_effect=AssertionError("must skip"),
            ):
                result = run_integrated(self.config, reg, root, stage, model, True)
            self.assertEqual(result["status"], "already_terminal")

    def test_clock_repair_call_limits_preserve_prior_attempts(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory

        from .main import smoke_policy
        from .utils import save_json

        limits = {
            e["id"]: (25 if i == 2 else 18, [6, 4, 6, 2][i])
            for i, e in enumerate(self.config["experiments"])
        }
        with TemporaryDirectory() as folder:
            root = Path(folder)
            approval = {
                "kind": "relative_clock_v1_targeted_gpu_repair",
                "user_approved": True,
                "max_new_calls": 18,
                "per_experiment_seconds": 600,
                "experiments": {
                    s: {"previous_calls": n, "additional_calls_max": k}
                    for s, (n, k) in limits.items()
                },
            }
            save_json(root / "clock_authorization.json", approval)
            for stage, (before, extra) in limits.items():
                self.assertEqual(
                    smoke_policy(root, stage, "clock")["scope_limit"], before + extra
                )
                self.assertEqual(smoke_policy(root, stage)["scope_limit"], 18)
            approval["max_new_calls"] = 19
            save_json(root / "clock_authorization.json", approval)
            with self.assertRaises(ValueError):
                smoke_policy(root, next(iter(limits)), "clock")

    def test_clock_repair_reuses_only_complete_matching_model_case_inputs(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory

        from .gates import integrated_tasks
        from .main import inherit_clock_smoke_units
        from .utils import read_json, save_json

        rows = [
            {"opaque_incident_id": "INC-" + str(i), "dataset": d}
            for i, d in enumerate(self.config["qualification"]["datasets"])
        ]
        registration = {"rosters": {"screen": rows, "check": rows}}
        tasks = [
            t
            for e in self.config["experiments"]
            for t in integrated_tasks(self.config, registration, e["id"], smoke=True)
        ]
        identity = lambda t: t["dimensions"][
            "arm"
        ]  # deliberately collides across models/cases
        with TemporaryDirectory() as folder:
            root, parent = Path(folder) / "repair", Path(folder) / "original"
            save_json(root / "clock_authorization.json", {"parent_root": str(parent)})
            save_json(
                root / "cpu_qualification.json",
                {
                    "units": [
                        {
                            "case": t["case"]["opaque_incident_id"],
                            "arm": t["dimensions"]["arm"],
                            "model": t["model"],
                            "input_identity": identity(t),
                        }
                        for t in tasks
                    ]
                },
            )
            for i, task in enumerate(tasks[:3]):
                save_json(
                    parent / "flags" / (task["logical_key"] + ".json"),
                    {
                        "status": "fail" if i == 2 else "done",
                        "logical_key": task["logical_key"],
                        "input_identity": "stale" if i == 1 else identity(task),
                        "call_key": str(i),
                        "artifact_root": str(parent / "artifacts"),
                    },
                )
            save_json(parent / "artifacts/completed/0.json", {"status": "complete"})
            before = (
                parent / "flags" / (tasks[0]["logical_key"] + ".json")
            ).read_bytes()
            self.assertEqual(
                inherit_clock_smoke_units(self.config, registration, root),
                [tasks[0]["logical_key"]],
            )
            self.assertEqual(
                read_json(root / "flags" / (tasks[0]["logical_key"] + ".json"))[
                    "new_generation_calls"
                ],
                0,
            )
            self.assertEqual(
                before,
                (parent / "flags" / (tasks[0]["logical_key"] + ".json")).read_bytes(),
            )
            self.assertEqual(
                inherit_clock_smoke_units(self.config, registration, root), []
            )

    def test_clock_repair_driver_preserves_repair_kind(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch

        from .main import run_integrated

        with TemporaryDirectory() as folder:
            with (
                patch("RQs.RQ3_4.src.main.smoke_policy", return_value={}) as policy,
                patch("RQs.RQ3_4.src.gates.integrated_tasks", return_value=[]),
            ):
                result = run_integrated(
                    self.config,
                    {},
                    Path(folder),
                    "exp_contract_alignment",
                    self.config["models"][0],
                    smoke=True,
                    repair="clock",
                )
            policy.assert_called_once_with(
                Path(folder), "exp_contract_alignment", "clock"
            )
            self.assertEqual(result["status"], "already_terminal")

    def test_parallel_solver_context_lifetimes(self):
        import concurrent.futures as cf
        import gc

        def task(_):
            for _ in range(12):
                v = ClaimVerifier(fixture())
                self.assertIs(v.solver.ctx, v.context)
                for quantity in v.variables.values():
                    self.assertIs(quantity.ctx, v.context)
                self.assertEqual(
                    v.verify({"kind": "candidate", "entity": "123"})["verdict"],
                    "entailed",
                )
                del v
            return True

        with cf.ThreadPoolExecutor(max_workers=8) as pool:
            self.assertTrue(all(pool.map(task, range(32))))
        gc.collect()

    def test_expansion_uses_shared_pairs(self):
        from .gates import expansion_decision

        spec = self.config["experiments"][1]
        rows = []
        for i, d in enumerate(self.config["qualification"]["datasets"]):
            for arm in spec["arms"]:
                rows.append(
                    {
                        "case_id": str(i),
                        "dataset": d,
                        "model": self.config["primary_model"],
                        "status": "done",
                        "dimensions": {"arm": arm},
                        "metrics": {"mrr": 0.5 if arm == "P1H1K1_G" else 0.4},
                    }
                )
        result = expansion_decision(rows, self.config)
        self.assertTrue(result["passed"])
        self.assertEqual(result["paired_n"], 3)
        rows[0].update(status="fail", failure_class="request_timeout")
        self.assertFalse(expansion_decision(rows, self.config)["passed"])

    def test_formal_resume_trusts_terminal_flags(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        from .main import formal_phase_state
        from .utils import save_json

        tasks = [{"logical_key": k} for k in ("done", "fail", "pending")]
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            for status in ("done", "fail"):
                save_json(root / "flags" / (status + ".json"), {"status": status})
            with (
                patch("RQs.RQ3_4.src.gates.integrated_tasks", return_value=tasks),
                patch(
                    "RQs.RQ3_4.src.main.load_integrated_context",
                    side_effect=AssertionError("No reload"),
                ),
            ):
                self.assertEqual(
                    formal_phase_state({}, {}, root, "stage", "model"),
                    {"planned": 3, "done": 1, "fail": 1, "pending": 1},
                )

    def test_formal_queue_fixed_stages_and_conditional_check(self):
        import tempfile
        from contextlib import ExitStack
        from copy import deepcopy
        from pathlib import Path
        from unittest.mock import MagicMock, patch

        from .main import integrated_formal_queue
        from .utils import digest, save_json

        for advance in (False, True):
            with (
                self.subTest(advance=advance),
                tempfile.TemporaryDirectory() as name,
                ExitStack() as stack,
            ):
                root = Path(name)
                config = deepcopy(self.config)
                config["execution_enabled"] = True
                contract = {"fixture": "CPU queue control only"}
                save_json(
                    root / "contract_migrations/formal_activation_v1/activation.json",
                    {"contract_hash": digest(contract)},
                )
                for stage in config["experiments"]:
                    save_json(
                        root / "qualification" / (stage["id"] + ".json"),
                        {"status": "passed", "contract_hash": digest(contract)},
                    )
                stack.enter_context(
                    patch("unified_scripts.vllm_inference.VLLMInferenceConfig.load")
                )
                phase = stack.enter_context(
                    patch(
                        "RQs.RQ3_4.src.main.formal_phase_state",
                        return_value={"pending": 0},
                    )
                )
                analysis = stack.enter_context(
                    patch(
                        "RQs.RQ3_4.src.gates.analyze_integrated",
                        return_value={"passed": advance},
                    )
                )
                process = MagicMock(pid=99999999, returncode=0)
                process.poll.return_value = 0
                launch = stack.enter_context(
                    patch("subprocess.Popen", return_value=process)
                )
                stack.enter_context(patch("os.killpg", side_effect=ProcessLookupError))
                result = integrated_formal_queue(config, {"contract": contract}, root)
                self.assertEqual(
                    result["state"],
                    "completed" if advance else "completed_negative_development",
                )
                # All terminal phases skip vLLM and requests; only flag-based preparation commands.
                self.assertEqual(launch.call_count, 2 if advance else 1)
                self.assertTrue(
                    all("prepare" in call.args[0] for call in launch.call_args_list)
                )
                self.assertEqual(phase.call_count, 8 if advance else 6)
                decisions = [
                    call
                    for call in analysis.call_args_list
                    if call.kwargs.get("decide")
                ]
                self.assertEqual(len(decisions), 1)
                self.assertEqual(
                    decisions[0].args[3], "exp_evidence_reasoning_factorial"
                )

    def test_formal_queue_preparation_failure_stops_before_gpu(self):
        import tempfile
        from contextlib import ExitStack
        from copy import deepcopy
        from pathlib import Path
        from unittest.mock import MagicMock, patch

        from .main import integrated_formal_queue
        from .utils import digest, read_json, save_json

        with tempfile.TemporaryDirectory() as name, ExitStack() as stack:
            root = Path(name)
            config = deepcopy(self.config)
            config["execution_enabled"] = True
            contract = {}
            save_json(
                root / "contract_migrations/formal_activation_v1/activation.json",
                {"contract_hash": digest(contract)},
            )
            for stage in config["experiments"]:
                save_json(
                    root / "qualification" / (stage["id"] + ".json"),
                    {"status": "passed", "contract_hash": digest(contract)},
                )
            stack.enter_context(
                patch("unified_scripts.vllm_inference.VLLMInferenceConfig.load")
            )
            process = MagicMock(pid=99999999, returncode=1)
            process.poll.return_value = 1
            launch = stack.enter_context(
                patch("subprocess.Popen", return_value=process)
            )
            stack.enter_context(patch("os.killpg", side_effect=ProcessLookupError))
            with self.assertRaises(RuntimeError):
                integrated_formal_queue(config, {"contract": contract}, root)
            self.assertEqual(launch.call_count, 1)
            self.assertEqual(
                read_json(root / "formal_queue_status.json")["state"], "failed"
            )


def integrated_cpu_qualification(config, registration, root):
    import hashlib
    import signal
    import time

    from RQs.RQ3_3.src.utils import OfflineTokens
    from vlmrca.run_state import atomic_write

    from .exps import integrated_parts
    from .gates import integrated_tasks, qualification_rows
    from .main import (
        compile_integrated_unit,
        load_integrated_context,
        prepare_integrated_cases,
    )
    from .utils import digest, runtime_config, save_json

    started = time.monotonic()

    def alarm(*_):
        raise TimeoutError("CPU regression exceeded 1800 seconds")

    previous = signal.signal(signal.SIGALRM, alarm)
    signal.alarm(1800)
    report = {
        "status": "failed",
        "contract_hash": digest(registration["contract"]),
        "units": [],
        "cases": [],
    }
    try:
        suite = unittest.TestSuite(
            [
                unittest.defaultTestLoader.loadTestsFromTestCase(ClaimTests),
                unittest.defaultTestLoader.loadTestsFromTestCase(IntegratedTests),
            ]
        )
        tests = unittest.TextTestRunner(verbosity=2).run(suite)
        report["unit_tests"] = {
            "run": tests.testsRun,
            "failures": len(tests.failures),
            "errors": len(tests.errors),
        }
        if not tests.wasSuccessful():
            raise AssertionError("Synthetic regression failed")
        rows = qualification_rows(config, registration)
        report["preparation"] = prepare_integrated_cases(
            config, registration, root, rows
        )
        tokens = OfflineTokens(runtime_config(config))
        for row in rows:
            context, private = load_integrated_context(root, row)
            opaque = row["opaque_incident_id"]
            report["cases"].append(opaque)
            originals = [
                hashlib.sha256(p["png"]).hexdigest()
                for p in context["base_parts"]
                if p["type"] == "image"
            ]
            seen = set()
            for e in config["experiments"]:
                for arm in e["arms"]:
                    for model in config["models"]:
                        if (arm, model) in seen:
                            continue
                        seen.add((arm, model))
                        task = {
                            "stage": "cpu",
                            "experiment": e["id"],
                            "model": model,
                            "case": row,
                            "dimensions": {"arm": arm},
                            "ledger_scope": "cpu",
                        }
                        request = compile_integrated_unit(
                            task, context, private, config, tokens
                        )
                        images = request["projection"]["image_hashes"]
                        if images and images != originals:
                            raise ValueError("Frozen G image changed")
                        text_input = "\n".join(
                            p.get("text", "") for p in request["parts"]
                        )
                        if (
                            opaque in text_input
                            or row["case_id"] in text_input
                            or str(root) in text_input
                        ):
                            raise ValueError("Private incident identity/path leaked")
                        if not arm.startswith("SIRCL_"):
                            original_text = [
                                p["text"]
                                for p in context["base_parts"]
                                if p["type"] == "text"
                                and p.get("attention_region") != "representation_guide"
                            ]
                            if any(t not in text_input for t in original_text):
                                raise ValueError("TPV backbone lost")
                        save_json(
                            root
                            / "cpu_examples"
                            / opaque
                            / (arm + "_" + model + ".json"),
                            {
                                "actual": request["actual"],
                                "projection": request["projection"],
                            },
                        )
                        for i, p in enumerate(request["parts"]):
                            if p["type"] == "image":
                                atomic_write(
                                    root
                                    / "cpu_examples"
                                    / opaque
                                    / (arm + f"_{i}.png"),
                                    p["png"],
                                )
                        report["units"].append(
                            {
                                "case": opaque,
                                "arm": arm,
                                "model": model,
                                "status": "passed",
                                "input_identity": request["input_identity"],
                                "tokens": request["projection"]["model_token_counts"],
                            }
                        )
            for a, b in (
                ("G_NONE", "P1H1K0_G"),
                ("G_VERIFIED", "P1H1K1_G"),
                ("T_VERIFIED", "P1H1K1_T"),
            ):
                if integrated_parts(context, a) != integrated_parts(context, b):
                    raise ValueError("Registered reuse is not input-identical")
            # Every smoke path belongs to the already tested same real cohort.
            for e in config["experiments"]:
                assert (
                    len(integrated_tasks(config, registration, e["id"], smoke=True))
                    <= 18
                )
        report["status"] = "passed"
        return report
    except BaseException as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
        report["elapsed_s"] = time.monotonic() - started
        save_json(root / "cpu_qualification.json", report)


def review_integrated_smoke(config, registration, root, stage, repair=False):
    """Review every completed persisted record; correctness is not a gate."""
    from pathlib import Path

    from RQs.RQ3_1.src.main import audit_completion_artifacts

    from .main import smoke_policy
    from .utils import digest, read_json, save_json

    stem = smoke_policy(root, stage, repair)["stem"]
    report = read_json(root / "smokes" / (stem + ".json"))
    if report["contract_hash"] != digest(registration["contract"]):
        raise ValueError("Smoke belongs to a different source contract")
    units = []
    for flag in report["flags"]:
        if flag["status"] != "done":
            continue
        destination = Path(flag["artifact_root"])
        key = flag["call_key"]
        audit_completion_artifacts(destination, key)
        output = read_json(destination / "outputs" / (key + ".json"))
        prompt = read_json(destination / "prompts" / (key + ".json"))
        audit = read_json(destination / "audits" / (key + ".json"))
        completion = read_json(destination / "completed" / (key + ".json"))
        conversation = destination / completion["conversation_path"]
        body = conversation.read_text()
        if (
            output["response"] not in body
            or not prompt["system"]
            or "## User" not in body
        ):
            raise ValueError("Incomplete input/output conversation")
        if prompt["effective_server"]["max_tokens"] != 8192:
            raise ValueError("Wrong output adapter")
        for part in prompt["parts"]:
            if (
                part["type"] == "image"
                and not (destination / part["image_path"]).is_file()
            ):
                raise ValueError("Model image absent")
        units.append(
            {
                "call_key": key,
                "model": output["model"],
                "arm": output["dimensions"]["arm"],
                "status": output["status"],
                "audit_status": audit["status"],
                "conversation": str(conversation),
                "input_tokens": read_json(destination / "cost" / (key + ".json"))[
                    "input_tokens"
                ],
            }
        )
    review = {
        "status": "passed"
        if report["status"] in {"complete", "bounded_timeout_only"}
        else "failed",
        "contract_hash": digest(registration["contract"]),
        "automated_artifact_review": True,
        "visual_and_semantic_human_style_review": "pending_assistant_inspection",
        "units": units,
        "initiated_calls": report["initiated_calls"],
        "smoke_status": report["status"],
    }
    save_json(root / "smokes" / (stem + "_artifact_review.json"), review)
    return review


if __name__ == "__main__":
    unittest.main()
