"""Regression for stale parent aliases and historical calibration scoring."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from RQs.RQ3_3.src import main
from RQs.RQ3_3.src.utils import parent_identity_matches


class IdentityRepairRegression(unittest.TestCase):
    def prepared(self, inverse=None):
        inverse = inverse or {"101": "service-a", "10001": "pod-a"}
        return SimpleNamespace(private={"numeric_to_natural": inverse},
            public={"packet": {"candidates": list(inverse)}})

    def test_exact_bindings_reuse(self):
        self.assertTrue(parent_identity_matches(self.prepared(), {"service-a": "101", "pod-a": "10001"}))

    def test_same_numeric_set_is_not_sufficient(self):
        self.assertFalse(parent_identity_matches(self.prepared(), {"service-a": "10001", "pod-a": "101"}))

    def test_changed_universe_is_not_alias_repair(self):
        with self.assertRaisesRegex(ValueError, "universes differ"):
            parent_identity_matches(self.prepared(), {"service-a": "101", "new-pod": "10001"})

    def test_collision_rejected(self):
        with self.assertRaisesRegex(ValueError, "non-bijective"):
            parent_identity_matches(self.prepared(), {"service-a": "101", "pod-a": "101"})

    def test_broken_candidate_inventory_rejected(self):
        prepared = self.prepared()
        prepared.public["packet"]["candidates"] = ["101"]
        with self.assertRaisesRegex(ValueError, "inventory"):
            parent_identity_matches(prepared, {"service-a": "101", "pod-a": "10001"})

    def test_calibration_retains_its_input_and_scoring_identity(self):
        old_parts = [{"type": "text", "text": "legacy 113"}]
        new_parts = [{"type": "text", "text": "current 35454"}]
        context = {"candidates": ["35454"], "sircl_system": "system", "cohorts": [],
            "source_hashes": {}, "historical_calibration": {"candidates": ["113"], "base_parts": old_parts}}
        old_private = {"numeric_to_natural": {"113": "pod-a"}}
        private = {"numeric_to_natural": {"35454": "pod-a"}, "historical_calibration_private": old_private}
        tokens = SimpleNamespace(fits=lambda *_: (True, {}))
        selection = {"variant": "none", "budget_tokens": 0, "packs": []}
        def bind(task, parts, system, projection):
            return {"parts": parts, "projection": projection, "envelope": {"effective_server": {}}}
        with patch.object(main.exps, "selection_for", return_value=selection), \
                patch.object(main.exps, "compile_parts", return_value=new_parts), \
                patch.object(main.exps, "bind_request", side_effect=bind), \
                patch.object(main, "read_json", return_value={"status": "audited", "reviewer": "fixture"}), \
                patch.object(main.exps, "calibrated_request", return_value=(old_parts, "system", None)):
            for arm in ("TPV_BRIDGE", "SC_TEXT_AS_RUN", "SC_TEXT_GUIDE_FIXED", "SC_TEXT_SOURCE_FIXED", "TPV", "W_G"):
                task = {"stage": "calibration", "model": "fixture", "case": {"opaque_incident_id": "fixture"},
                        "dimensions": {"arm": arm}}
                result = main.compile_unit(task, {"data": {}}, main.ROOT, context, private, None, tokens)
                legacy = arm == "TPV_BRIDGE" or arm.startswith("SC_TEXT_")
                self.assertEqual(result["parts"], old_parts if legacy else new_parts)
                self.assertEqual(result["candidates"], ["113"] if legacy else ["35454"])
                self.assertEqual(result["private"], old_private if legacy else private)


if __name__ == "__main__":
    unittest.main(verbosity=2)
