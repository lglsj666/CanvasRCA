"""Opt-in synthetic regression and bounded, real-case CPU qualification.

NOT executed by source-level static checks. `python -m ...tests` is a CPU test.
"""
from __future__ import annotations

import json
import signal
import time
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

from unified_scripts import stable_hash
from . import exps, gates
from .utils import PRIMARY, CONFIG, load_config, ContextInfeasible, NotApplicable


class WordTokens:
    def cost(self, text):
        return len(text.split())


def fixture():
    rows = []
    for i in range(6):
        rows.append({"id": "o"+str(i), "source_key": "physical:"+str(i), "entity": str(101+i),
            "region": "M", "semantic": "cpu_seconds", "unit": "s", "role": "unverified_numeric",
            "support": 12+i, "source_rows": [i], "values": {"reference_median": 10., "current_median": float(11+i),
                "reference_interval_s": [0, 10], "current_interval_s": [10, 20]},
            "definition": "Cumulative consumed CPU time."})
    return {"observations": rows, "relations": [], "request_links": [], "cohorts": []}


class SourceLogicRegression(unittest.TestCase):
    def test_log_templates_preserve_codes_entities_values_and_all_rows(self):
        import pandas as pd
        from .utils import extract_logs
        mapping = {"checkout": "101", "node-a": "1001"}
        rows = [{"container_name": "101", "_rq21_time_s": i % 20,
                 "message": f"checkout on node-a status={500 if i % 2 else 200} latency={i+1}ms request_id={i:032x}",
                 "level": "INFO"} for i in range(1000)]
        native = SimpleNamespace(logs_df=pd.DataFrame(rows), services=["101"])
        groups = extract_logs(native, {"mapping": mapping}, (0, 10, 20))
        self.assertEqual(len(groups), 2)
        self.assertEqual(sorted(i for g in groups for i in g["source_rows"]), list(range(1000)))
        for g in groups:
            v = g["values"]
            self.assertIn("101 on 1001", v["template"])
            self.assertIn("latency={num1} ms", v["template"])
            self.assertEqual(v["reference_count"]+v["current_count"], 500)
            self.assertEqual(v["reference_entity_log_count"], 500)
            self.assertEqual(v["current_entity_log_count"], 500)
            self.assertEqual(v["current_numeric_parameters"]["{num1}"]["n"], 250)
            self.assertNotIn("0000000000000000", json.dumps(v))
        self.assertEqual({g["values"]["template"].split("status=")[1].split()[0] for g in groups}, {"200", "500"})

    def test_log_numeric_change_survives_constant_counts(self):
        import pandas as pd
        from .utils import extract_logs
        rows = [{"container_name": "101", "_rq21_time_s": i,
                 "message": f"duration={10 if i < 10 else 900} ms"} for i in range(20)]
        groups = extract_logs(SimpleNamespace(logs_df=pd.DataFrame(rows), services=["101"]), {"mapping": {}}, (0, 10, 20))
        self.assertEqual(len(groups), 1)
        self.assertEqual(exps.obs_delta(groups[0]), 0)
        self.assertIn(890, exps.comparison_axes(groups[0]).values())
        self.assertEqual(len(exps.witness_pool({"observations": groups, "relations": [], "request_links": []})), 1)

    def test_cached_pack_concatenation_is_byte_exact(self):
        ctx = fixture(); pool = exps.witness_pool(ctx)
        first = exps.appendix(ctx, pool[:2], "W_SEM_EXEC")
        suffix = exps.appendix(ctx, pool[2:3], "W_SEM_EXEC")[len(exps.APPENDIX_GUIDE.rstrip())+1:]
        self.assertEqual(first+"\n"+suffix, exps.appendix(ctx, pool[:3], "W_SEM_EXEC"))

    def test_structured_log_order_and_clocks_do_not_create_templates(self):
        from .utils import log_template
        a = '{"ts":1700000000.123,"msg":"timeout","status":504,"request":{"headers":{"Traceparent":"ab12","Accept":"json"}},"duration":12}'
        b = '{"duration":99,"request":{"headers":{"Accept":"json","Traceparent":"cd34"}},"status":504,"msg":"timeout","ts":1700000010.456}'
        ta, va = log_template(a, {}, (None, {}))
        tb, vb = log_template(b, {}, (None, {}))
        self.assertEqual(ta, tb)
        self.assertEqual(list(va.values()), [12.])
        self.assertEqual(list(vb.values()), [99.])
        self.assertIn('"status":504', ta)
        self.assertNotIn('170000', ta)
        _, elapsed = log_template('{"time":20,"duration":8}', {}, (None, {}))
        self.assertEqual(sorted(elapsed.values()), [8., 20.])

    def test_parent_projection_and_batch_selection_match_reference(self):
        from .utils import full_parent_log_rows
        from RQs.RQ1_1.src.exps import denum_visible_rows
        rows = [{"entity_id": str(101+i%3), "template_id": "LT"+str(i), "count": 20-i,
                 "relative_bin": i, "level": "INFO", "template": "value={num1}",
                 "numeric_variables": {"{num1}": {"encoding": "constant", "value": "5", "count": 20-i}}}
                for i in range(10)]
        graph = {"entries": rows+[dict(rows[0])], "log_r_scores": [{"entity_id": "103", "score": 5}, {"entity_id": "101", "score": 1}]}
        self.assertEqual(list(full_parent_log_rows(graph)), denum_visible_rows(graph, len(graph["entries"]), graph["log_r_scores"]))
        class Tokens(WordTokens):
            def cost_many(self, values): return [self.cost(v) for v in values]
            def fits(self, parts, system): return ("reject-me" not in parts[-2]["text"], {})
        ctx = {"base_parts": [{"type": "text", "text": "base"}], "native_tail": [
            {"id": str(i), "text": "reject-me" if i==1 else "word "*(i%5+1)} for i in range(200)]}
        tokens = Tokens()
        for budget in (10, 30):
            expected = []
            for item in ctx["native_tail"]:
                text = "Additional parent-ranked observations:\n"+"\n".join(i["text"] for i in expected+[item])
                if tokens.cost(text) <= budget and tokens.fits(exps.append_parts(ctx["base_parts"], text), "system")[0]:
                    expected.append(item)
            self.assertEqual(exps.choose_parent_tail(ctx, tokens, budget, "system"), expected)

    def test_cached_anonymizer_matches_inherited_text(self):
        from RQs.RQ2_1.src.exps import _anonymize_text, _compiled_anonymizer
        from RQs.RQ3_1.src.exps import _public_identifier_aliases, _replace_public_identifiers
        from .utils import visible_string
        import hashlib
        mapping = {"checkout": "101", "checkout-pod": "10001", "node-a": "1001"}
        compiled = _compiled_anonymizer(mapping)
        samples = ("checkout-pod on node-a", "10.1.2.3 checkout.svc.cluster.local",
                   "id 123e4567-e89b-12d3-a456-426614174000", "", "checkout checkout-pod")
        for value in samples:
            legacy = _anonymize_text(str(value), mapping)
            aliases, _ = _public_identifier_aliases([{"payload": {"message": legacy}}])
            aliases = {key: "identifier:"+hashlib.sha256(str(key).encode()).hexdigest()[:12]
                       for key in aliases}
            expected = _replace_public_identifiers(legacy, aliases)
            self.assertEqual(visible_string(value, mapping, compiled), expected)

    def test_registered_budget(self):
        cfg = load_config(CONFIG)
        self.assertEqual(sum(v["calls_max"] for v in cfg["stages"].values())+90, 23190)
        self.assertLess(cfg["budget"]["planned_calls"], cfg["budget"]["hard_limit"])

    def test_visible_operand_math(self):
        row = fixture()["observations"][0]
        self.assertIn("1.1", " ".join(exps.computations(row)))
        row["values"]["reference_median"] = 0
        self.assertNotIn(" / reference_median", " ".join(exps.computations(row)))

    def test_sem_exec_common_observations(self):
        ctx = fixture(); packs = exps.witness_pool(ctx)[:2]
        raw = exps.appendix(ctx, packs, "W_RAW")
        sem = exps.appendix(ctx, packs, "W_SEM")
        exe = exps.appendix(ctx, packs, "W_EXEC")
        self.assertNotEqual(raw, sem); self.assertNotEqual(raw, exe)
        for o in ctx["observations"][:2]:
            if o["id"] in {m for p in packs for m in p["members"]}:
                self.assertIn(json.dumps(o["values"], sort_keys=True), raw)
                self.assertIn(json.dumps(o["values"], sort_keys=True), exe)

    def test_prefix_budget(self):
        cfg = load_config(CONFIG); ctx = fixture(); tokens = WordTokens()
        tiny, _ = exps.choose_witnesses(ctx, tokens, cfg, 1024)
        small, _ = exps.choose_witnesses(ctx, tokens, cfg, 2048, prefix=tiny)
        large, _ = exps.choose_witnesses(ctx, tokens, cfg, 4096, prefix=small)
        self.assertEqual(small[:len(tiny)], tiny)
        self.assertLessEqual(len(tiny), 2)
        self.assertEqual(large[:len(small)], small)

    def test_shared_pool_and_cost_cache_preserve_choice(self):
        cfg = load_config(CONFIG); ctx = fixture()
        class CountingTokens(WordTokens):
            def __init__(self): self.calls = 0
            def cost(self, text):
                self.calls += 1
                return super().cost(text)
        token = CountingTokens(); pool = exps.witness_pool(ctx); costs = {}
        expected_first = min(pool, key=lambda p: (
            False, False, not p["sustained_support"], -p["comparison_rank"], -p["support"],
            WordTokens().cost(exps.appendix(ctx, [p], "W_SEM_EXEC")), p["source_key"]))
        first = exps.choose_witnesses(ctx, token, cfg, 1024, shared_pool=pool, pack_costs=costs)
        self.assertEqual(first[0][0]["id"], expected_first["id"])
        second = exps.choose_witnesses(ctx, token, cfg, 2048, prefix=first[0], prefix_cohort=first[1],
                                       shared_pool=pool, pack_costs=costs)
        count = len(costs)
        repeated = exps.choose_witnesses(ctx, token, cfg, 2048, prefix=first[0], prefix_cohort=first[1],
                                         shared_pool=pool, pack_costs=costs)
        original = exps.choose_witnesses(ctx, WordTokens(), cfg, 2048, prefix=first[0], prefix_cohort=first[1])
        self.assertEqual(second, original)
        self.assertEqual(repeated, second)
        self.assertEqual(len(costs), count)

    def test_greedy_scan_matches_repeated_min_with_oversized_packs(self):
        cfg = load_config(CONFIG); ctx = fixture(); pool = exps.witness_pool(ctx)
        class ScaledTokens:
            def cost(self, text):
                return 100 * len(text.split())
            def cost_many(self, texts):
                return [self.cost(text) for text in texts]
        tokens = ScaledTokens(); budget = 2048
        remaining = list(pool); selected = []; kinds = set(); questions = set()
        while remaining and len(selected) < cfg["witness"]["budget_pack_limits"][str(budget)]:
            def key(p):
                return (p["kind"] in kinds, stable_hash(p["question"]) in questions,
                    not p["sustained_support"], -p["comparison_rank"], -p["support"],
                    tokens.cost(exps.appendix(ctx, [p], "W_SEM_EXEC")), p["source_key"])
            chosen = min(remaining, key=key); remaining.remove(chosen)
            current = {m for p in selected for m in p["members"]}
            rels = {r["id"] for p in selected for r in p["relations"]}
            if set(chosen["members"]) <= current and {r["id"] for r in chosen["relations"]} <= rels:
                continue
            text = exps.appendix(ctx, selected+[chosen], "W_SEM_EXEC")
            if tokens.cost(text) <= budget-cfg["witness"]["cohort_reserve_tokens"]:
                selected.append(chosen); kinds.add(chosen["kind"])
                questions.add(stable_hash(chosen["question"]))
        actual, _ = exps.choose_witnesses(ctx, tokens, cfg, budget, shared_pool=pool)
        self.assertEqual([p["id"] for p in actual], [p["id"] for p in selected])

    def test_marginal_is_not_a_winner_candidate(self):
        cfg = load_config(CONFIG)
        self.assertIn("W_COHORT_MARGINAL", cfg["stages"]["screen"]["arms"])
        self.assertNotIn("W_COHORT_MARGINAL", exps.W_VARIANTS)

    def test_cohort_pooled_requests_not_median_of_medians(self):
        import pandas as pd
        from unittest.mock import patch
        from .utils import extract_traces
        cfg = load_config(CONFIG); records = []
        values = [1, 2, 3, 4, 100, 200, 201, 202, 203, 204]
        for i, value in enumerate(values):
            for entity, span, parent in (("101", "parent", ""), ("102", "child", "parent")):
                records.append({"service_name": entity, "operation_name": "work", "duration_ms": value,
                    "_rq21_time_s": 12, "trace_id": str(i), "span_id": span, "parent_span_id": parent,
                    "http_status_code": 200 if i < 5 else 500})
        native = SimpleNamespace(traces_df=pd.DataFrame(records), services=["101", "102"])
        source = {"view": SimpleNamespace(dataset="synthetic"), "mapping": {"101": "101", "102": "102"}}
        with patch("RQs.RQ3_1.src.exps._registered_trace_duration_projection", return_value=(1, "synthetic_ms")):
            _, _, cohorts, _ = extract_traces(native, source, (0, 10, 20), cfg["witness"])
        self.assertEqual(len(cohorts), 2)
        for c in cohorts:
            m = c["marginal_payload"]
            self.assertEqual(m["request_max_span_median_ms"], 150.)
            self.assertEqual(m["requests"], 10)
            self.assertEqual(m["linked_edges"][0]["requests"], 10)
            self.assertNotIn("groups", m)
            self.assertEqual({k: v for k, v in c["payload"].items() if k != "groups"}, m)

    def test_binding_changes_location_not_repeated_content(self):
        ctx = fixture(); packs = exps.witness_pool(ctx)[:2]
        local = exps.appendix(ctx, packs, "W_RAW", binding="LOCAL").splitlines()
        remote = exps.appendix(ctx, packs, "W_RAW", binding="REMOTE").splitlines()
        self.assertEqual(sorted(local), sorted(remote))
        self.assertNotEqual(local, remote)
        for line in local:
            if line.startswith("Observation binding: "):
                self.assertNotIn("measurement_definition", line)

    def test_pair_closure_and_label_blindness(self):
        ctx = fixture(); ctx["prepared"] = SimpleNamespace(public={"packet": {"facts": []}})
        pack = {"id": "pair", "kind": "SCOPE", "members": ["o0", "o1"], "relations": [], "source_key": "pair-source"}
        selection = {"variant": "W_COHORT", "packs": [pack], "cohort": {"secret": "DERIVED"}, "budget_tokens": 2048}
        plan = exps.evidence_pair_plan(ctx, selection)
        ctx["private"] = {"root": "101"}
        self.assertEqual(plan, exps.evidence_pair_plan(ctx, selection))
        outputs = {}
        backgrounds = []
        for condition in ("PAIR_00", "PAIR_10", "PAIR_01", "PAIR_11"):
            value = exps.pair_selection(ctx, selection, plan, condition)
            self.assertEqual(value["variant"], "W_RAW"); self.assertIsNone(value["cohort"])
            outputs[condition] = {m for p in value["packs"] for m in p["members"]}
            text = exps.appendix(ctx, value["packs"], value["variant"])
            backgrounds.append([line for line in text.splitlines() if not line.startswith('{"entity":')])
            self.assertNotIn("calculated_comparisons", text)
            self.assertNotIn("DERIVED", text)
        self.assertEqual(outputs["PAIR_00"], set())
        self.assertEqual(outputs["PAIR_10"], {plan["a"]})
        self.assertEqual(outputs["PAIR_01"], {plan["b"]})
        self.assertEqual(outputs["PAIR_11"], {plan["a"], plan["b"]})
        self.assertTrue(all(b == backgrounds[0] for b in backgrounds))
        ctx["prepared"].public["packet"]["facts"] = [{"region": "M", "entity_ids": ["101"]}]
        with self.assertRaises(NotApplicable):
            exps.evidence_pair_plan(ctx, selection)

    def test_budget_matrix_has_distinct_identities(self):
        cfg = load_config(CONFIG)
        reg = {"rosters": {"screen": [{"dataset": d, "opaque_incident_id": d} for d in PRIMARY]}}
        tasks = gates.task_matrix(cfg, reg, "budget")
        self.assertEqual(len(tasks), 24)
        self.assertEqual(len({t["logical_key"] for t in tasks}), len(tasks))
        self.assertEqual({t["dimensions"]["budget_tokens"] for t in tasks}, {1024, 4096})

    def test_pair_preserves_headings_and_public_relations(self):
        ctx = fixture(); ctx["prepared"] = SimpleNamespace(public={"packet": {"facts": []}})
        relation = {"kind": "owns", "a": "101", "b": "10001", "id": "ownership"}
        pack = {"id": "pair", "kind": "SCOPE", "members": ["o0", "o1"], "relations": [relation], "source_key": "pair-source"}
        selection = {"variant": "W_RAW", "packs": [pack], "cohort": None}
        plan = exps.evidence_pair_plan(ctx, selection)
        backgrounds = []
        for condition in ("PAIR_00", "PAIR_10", "PAIR_01", "PAIR_11"):
            value = exps.pair_selection(ctx, selection, plan, condition)
            text = exps.appendix(ctx, value["packs"], "W_RAW")
            backgrounds.append([line for line in text.splitlines() if not line.startswith('{"entity":')])
            self.assertEqual(value["packs"][0]["relations"], [relation])
        self.assertTrue(all(b == backgrounds[0] for b in backgrounds))

    def test_pair_rejects_recycled_trace_events(self):
        ctx = fixture(); ctx["prepared"] = SimpleNamespace(public={"packet": {"facts": []}})
        for o in ctx["observations"][:2]:
            o.update(region="R", source_rows=[100, 101])
        pack = {"id": "pair", "kind": "PATH", "members": ["o0", "o1"], "relations": [], "source_key": "pair-source"}
        with self.assertRaises(NotApplicable):
            exps.evidence_pair_plan(ctx, {"packs": [pack]})

    def test_analysis_rejects_duplicate_arm_cells(self):
        row = {"case_id": "case", "model": "m", "dimensions": {"arm": "W_G"}, "status": "done"}
        with self.assertRaises(ValueError):
            gates.pairable([row, deepcopy(row)], ("W_G",), "m")

    def test_cohort_source_eligibility_is_not_appendix_eligibility(self):
        rows = [{"case_id": "case", "dataset": "aiops2022", "model": "m", "dimensions": {"arm": a},
                 "status": "done", "metrics": {"mrr": .5}, "input_identity": "same-request",
                 "manipulation": {"cohort_source_available": True, "cohort_included": False}}
                for a in ("W_SEM_EXEC", "W_COHORT_MARGINAL", "W_COHORT")]
        summary = {r["stratum"]: r for r in gates.cohort_control_summary(rows, "m") if r["population"] == "aiops2022"}
        self.assertEqual(summary["qualified_source"]["n"], 1)
        self.assertEqual(summary["appended"]["n"], 0)
        self.assertEqual(summary["no_appendix"]["identical_complete_requests"], 1)

    def test_budget_lock_prefers_accuracy_then_smallest_near_tie(self):
        cfg = load_config(CONFIG)
        def row(dataset, arm, value, budget=None):
            return {"model": cfg["primary_model"], "case_id": dataset, "dataset": dataset, "status": "done",
                    "dimensions": {"arm": arm, **({"budget_tokens": budget} if budget else {})}, "metrics": {"mrr": value}}
        screen = [row(d, "W_RAW", .6) for d in PRIMARY]
        budgets = [row(d, a, .595 if b == 1024 else .602, b) for d in PRIMARY
                   for b in (1024, 4096) for a in ("W_G", "P0_MORE_TRUE")]
        lock = gates.lock_budget({"variant": "W_RAW"}, screen, budgets, cfg)
        self.assertEqual(lock["budget_tokens"], 1024)
        for r in budgets:
            if r["dimensions"]["budget_tokens"] == 4096:
                r["metrics"]["mrr"] = .7
        self.assertEqual(gates.lock_budget({"variant": "W_RAW"}, screen, budgets, cfg)["budget_tokens"], 4096)

    def test_selection_equivariance(self):
        cfg = load_config(CONFIG); ctx = fixture(); shifted = deepcopy(ctx)
        for row in shifted["observations"]:
            row["entity"] = str(int(row["entity"])+30)
        a, _ = exps.choose_witnesses(ctx, WordTokens(), cfg)
        b, _ = exps.choose_witnesses(shifted, WordTokens(), cfg)
        self.assertEqual([p["members"] for p in a], [p["members"] for p in b])

    def test_type_preserving_ids(self):
        candidates = ["100", "101", "1000", "10001"]
        mapping = exps.typed_id_map(candidates, 42)
        self.assertEqual(len(set(mapping.values())), len(candidates))
        self.assertTrue(all(len(a) == len(b) for a, b in mapping.items()))

    def test_intact_groups(self):
        groups = [[{"opaque_incident_id": str(i)+str(j)} for j in range(n)] for i, n in enumerate((2, 3, 5))]
        selected = gates.intact_subset(groups, 6, 42, "sample")
        self.assertEqual(len(selected), 5)
        ids = {r["opaque_incident_id"] for r in selected}
        self.assertTrue(all(not ids.intersection(r["opaque_incident_id"] for r in g) or all(r["opaque_incident_id"] in ids for r in g) for g in groups))

    def test_event_overlap(self):
        a = {"dataset": "a", "source": "x", "event": "", "start": 0, "end": 10}
        self.assertTrue(gates.related(a, {**a, "start": 9, "end": 20}))
        self.assertFalse(gates.related(a, {**a, "dataset": "b"}))

    def test_request_identity(self):
        envelope = {"schema": {}, "effective_server": {"max_tokens": 8192}}
        a = exps.request_descriptor([{"type": "text", "text": "A"}], "system", envelope, "q")
        b = exps.request_descriptor([{"type": "text", "text": "A"}], "system", envelope, "g")
        self.assertNotEqual(stable_hash(a), stable_hash(b))

    def test_front_does_not_mutate_base(self):
        base = [{"type": "text", "text": "task", "attention_region": "task_question"},
                {"type": "text", "text": "facts"}, {"type": "text", "text": "closing"}]
        result = exps.append_parts(base, "witness", front=True)
        self.assertEqual([result[0], *result[2:]], base)
        self.assertEqual(len(base), 3)

    def test_no_private_input(self):
        ctx = fixture(); ctx["observations"][0]["secret"] = "PRIVATE_LABEL"
        text = exps.appendix(ctx, exps.witness_pool(ctx), "W_SEM_EXEC")
        self.assertNotIn("PRIVATE_LABEL", text)

    def test_no_label_dependent_pool(self):
        ctx = fixture(); before = exps.witness_pool(ctx)
        ctx["private"] = {"root_cause": "105"}
        self.assertEqual(before, exps.witness_pool(ctx))

    def test_bounded_smoke_matrix(self):
        cfg = load_config(CONFIG)
        roster = {"screen": [{"dataset": d, "opaque_incident_id": d} for d in PRIMARY]}
        reg = {"rosters": roster}
        for stage, spec in cfg["stages"].items():
            reg["rosters"][spec["cohort"]] = roster["screen"]
            self.assertLessEqual(len(gates.task_matrix(cfg, reg, stage, smoke=True)), 18)

    def test_terminal_resume_without_context(self):
        # Test the actual early-run branch with no tokenizer/context available.
        import tempfile
        from unittest.mock import patch
        from vlmrca.run_state import write_json
        from .main import run
        cfg = load_config(CONFIG); rows = [{"dataset": d, "opaque_incident_id": d} for d in PRIMARY]
        reg = {"rosters": {"screen": rows}, "contract": {}}
        tasks = gates.task_matrix(cfg, reg, "screen", cfg["models"][0])
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for task in tasks:
                write_json(root/"flags"/(task["logical_key"]+".json"), {"status": "fail"})
            write_json(root/"qualification/exp_witness_development.json", {"status": "passed", "contract_hash": stable_hash({})})
            write_json(root/"stages/calibration/complete.json", {"registered": 24, "terminal": 24, "failed_units": 0})
            with patch("RQs.RQ3_3.src.main.OfflineTokens", side_effect=AssertionError("must skip tokenizer")):
                result = run(cfg, reg, root, "screen", cfg["models"][0], execute=True)
            self.assertEqual(result["status"], "already_terminal")


def cpu_qualification(config, registration, root, seconds=1800):
    from vlmrca.run_state import write_json
    from .main import prepare, load_context, compile_unit
    from .utils import OfflineTokens
    if not 1 <= seconds <= 1800:
        raise ValueError("CPU regression must be bounded by 1800 seconds")
    started = time.monotonic()
    def timeout(sig, frame):
        raise TimeoutError("CPU regression time budget reached; not qualified")
    prior = signal.signal(signal.SIGALRM, timeout); signal.alarm(seconds)
    report = {"status": "failed", "contract_hash": stable_hash(registration["contract"]), "cases": [], "units": []}
    try:
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SourceLogicRegression))
        if not result.wasSuccessful():
            raise AssertionError("synthetic regression failed")
        cases = gates.qualification_rows(config, registration)
        local = deepcopy(registration); local["rosters"]["cpu_three"] = cases
        prepare(config, local, root, "cpu_three", workers=8)
        tokens = OfflineTokens(config)
        for row in cases:
            context, private = load_context(root, row)
            report["cases"].append(row["opaque_incident_id"])
            texts = [exps.appendix(context, context["selections"]["2048:full"]["packs"], v) for v in exps.W_VARIANTS]
            tail = context["native_tail"]
            probes = sorted(tail, key=lambda r: stable_hash([42, r["id"]]))[:32]
            for b in (1024, 2048, 4096):
                prefix = "Additional parent-ranked observations:\n"+"\n".join(i["text"] for i in context["selections"][f"{b}:more"]["items"])
                texts.extend(prefix+"\n"+item["text"] for item in probes)
            texts.extend(["中文 é\nMetric 🙂", "x\r\n\n{\"q\":3}", " <end_of_turn>\nAvailability", "", "\nM\nT\nL\n{"])
            report.setdefault("token_cache_checks", {})[row["opaque_incident_id"]] = tokens.verify_cost_cache(texts)
            # All registered rendering/ablation families on each real case;
            # calibration is audited separately against its original artifacts.
            arms = [*config["stages"]["screen"]["arms"], "W_T", "P0_T_TWIN", *config["stages"]["organization"]["arms"], *config["stages"]["events"]["arms"]]
            for arm in arms:
                task = {"stage": "screen", "experiment": "cpu", "model": config["models"][0], "case": row, "dimensions": {"arm": arm}}
                try:
                    request = compile_unit(task, config, root, context, private, {"variant": "W_SEM_EXEC", "budget_tokens": 2048}, tokens)
                    for i, p in enumerate(request["parts"]):
                        if p["type"] == "image":
                            from vlmrca.run_state import atomic_write
                            atomic_write(root/"cpu_examples"/row["opaque_incident_id"]/(arm+f"_{i}.png"), p["png"])
                    write_json(root/"cpu_examples"/row["opaque_incident_id"]/(arm+".json"), request["actual"])
                    report["units"].append({"case": row["opaque_incident_id"], "arm": arm, "status": "passed", "input_identity": request["input_identity"]})
                except (NotApplicable, ContextInfeasible) as exc:
                    report["units"].append({"case": row["opaque_incident_id"], "arm": arm, "status": type(exc).__name__, "reason": str(exc)})
            for stage in ("pairs", "binding", "budget"):
                spec = config["stages"][stage]
                local["rosters"][spec["cohort"]] = [row]
                for task in gates.task_matrix(config, local, stage, config["models"][0]):
                    label = task["dimensions"]["arm"]+"_"+str(task["dimensions"].get("condition", task["dimensions"].get("budget_tokens")))
                    try:
                        request = compile_unit(task, config, root, context, private, {"variant": "W_SEM_EXEC", "budget_tokens": 2048}, tokens)
                        write_json(root/"cpu_examples"/row["opaque_incident_id"]/(label+".json"), request["actual"])
                        report["units"].append({"case": row["opaque_incident_id"], "arm": label, "status": "passed", "input_identity": request["input_identity"]})
                    except (NotApplicable, ContextInfeasible) as exc:
                        report["units"].append({"case": row["opaque_incident_id"], "arm": label, "status": type(exc).__name__, "reason": str(exc)})
        # P0_MORE and W transformations may naturally be no-ops on real cases;
        # constructive synthetic tests above establish implementation capability.
        base = [u for u in report["units"] if u["arm"] in {"TPV", "W_RAW", "W_T", "P0_T_TWIN"}]
        if any(u["status"] != "passed" for u in base):
            raise ValueError("a primary baseline/witness input failed CPU qualification")
        report["status"] = "passed"
        return report
    finally:
        signal.alarm(0); signal.signal(signal.SIGALRM, prior)
        report["elapsed_s"] = time.monotonic()-started
        write_json(root/"cpu_qualification.json", report)


def qualify(config, registration, root, experiment, manual_path):
    from .utils import read_json
    cpu = read_json(root/"cpu_qualification.json")
    manual = read_json(manual_path)
    smoke = read_json(root/"smokes"/(experiment+".json"))
    contract_hash = stable_hash(registration["contract"])
    required = ("source_units_windows", "typed_entity_bindings", "visible_inputs_no_private_labels",
                "inherited_tpv_intact", "actual_action_changes", "canvas_readability", "conversations_outputs_accounting",
                "cohort_same_request_union", "pair_common_background_no_derived_leak",
                "binding_caption_equality", "nested_budget_prefixes")
    if cpu["status"] != "passed" or cpu["contract_hash"] != contract_hash:
        raise ValueError("CPU qualification unavailable/currently failed")
    if not manual.get("reviewer") or not manual.get("artifact_paths") or manual.get("contract_hash") != contract_hash:
        raise ValueError("manual source/input/output review is incomplete")
    if any(manual.get("checks", {}).get(k) is not True for k in required):
        raise ValueError("one or more required manual checks not passed")
    if smoke["status"] not in {"complete", "bounded_timeout_only"} or smoke["initiated_calls"] > 18 or smoke["contract_hash"] != contract_hash:
        raise ValueError("bounded smoke has non-timeout errors or a contract mismatch")
    value = {"status": "passed", "contract_hash": contract_hash, "experiment": experiment,
             "smoke": smoke, "manual_audit": str(manual_path), "completed_live_units": smoke["completed_units"]}
    gates.immutable_json(root/"qualification"/(experiment+".json"), value)
    # Capability audit is a human-reviewed record, not an inference from green tests.
    gates.immutable_json(root/"capability_audit.json", {"status": "passed", "reviewer": manual["reviewer"],
                         "event_branch_qualified": bool(manual.get("event_branch_qualified")), "contract_hash": contract_hash})
    return value


if __name__ == "__main__":
    unittest.main()
