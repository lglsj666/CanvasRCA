"""CPU-only regression for source-bound nested log clock projection."""

import json
import unittest
from copy import deepcopy

from RQs.RQ3_3.src.exps import comparison_axes
from RQs.RQ3_4.src.exps import assert_no_absolute_clock
from RQs.RQ3_7.scripts.stage_c.clock_projection import project_log_clocks
from RQs.RQ3_7.src.utils import ROOT


def fixture():
    record = json.loads((ROOT / "RQs/RQ3_7/results/fusion_v2_pruned/diagnostics/preparation_errors/INC-12D885A5B485.json").read_text())
    row = json.loads(record["public_line"])
    row.update(id="test-log", support=24, role="log_group")
    return row


class ClockRegression(unittest.TestCase):
    def test_exact_translation_preserves_deltas_and_source(self):
        row = fixture()
        original = deepcopy(row)
        result, audit = project_log_clocks([row])
        self.assertEqual(row, original)
        self.assertEqual(comparison_axes(row), comparison_axes(result[0]))
        self.assertEqual(result[0]["id"], row["id"])
        for phase in ("reference", "current"):
            before = row["values"][phase + "_numeric_parameters"]
            after = result[0]["values"][phase + "_numeric_parameters"]
            for slot in before.keys() - {"{num1}"}:
                self.assertEqual(before[slot], after[slot])
            self.assertEqual(before["{num1}"]["n"], after["{num1}"]["n"])
        self.assertEqual(audit["origin"], "1706087500.0")
        self.assertNotIn(audit["origin"], json.dumps(result))
        assert_no_absolute_clock([{"type": "text", "text": json.dumps(result[0])}])

    def test_common_origin_not_per_entity(self):
        a, b = fixture(), fixture()
        b["id"], b["entity"] = "another-log", "777"
        for phase in ("reference", "current"):
            for stat in ("min", "median", "max"):
                b["values"][phase + "_numeric_parameters"]["{num1}"][stat] += 100
        rows, _ = project_log_clocks([a, b])
        for phase in ("reference", "current"):
            for stat in ("min", "median", "max"):
                self.assertEqual(rows[1]["values"][phase + "_numeric_parameters"]["{num1}"][stat]
                                 - rows[0]["values"][phase + "_numeric_parameters"]["{num1}"][stat], 100)

    def test_idempotent(self):
        first, _ = project_log_clocks([fixture()])
        second, audit = project_log_clocks(first)
        self.assertEqual(first, second)
        self.assertEqual(audit["observations"], [])

    def test_ordinary_large_measurement_is_unchanged(self):
        row = fixture()
        row["values"]["template"] = "memory_bytes={num1} duration_ms={num2}"
        rows, audit = project_log_clocks([row])
        self.assertIs(rows[0], row)
        self.assertFalse(audit["observations"])

    def test_unknown_clock_still_rejected(self):
        with self.assertRaises(ValueError):
            assert_no_absolute_clock([{"text": "unknown_timestamp=1706087500"}])

    def test_invalid_components_fail_closed(self):
        for value in (float("nan"), -1, 1000000):
            with self.subTest(value=value), self.assertRaises(ValueError):
                row = fixture()
                row["values"]["current_numeric_parameters"]["{num2}"]["max"] = value
                project_log_clocks([row])

    def test_nonzero_transaction_stamp_needs_review(self):
        row = fixture()
        row["values"]["current_numeric_parameters"]["{num7}"]["max"] = 1706087500
        with self.assertRaisesRegex(ValueError, "transaction timestamp"):
            project_log_clocks([row])

    def test_missing_phase_and_missing_operands(self):
        row = fixture()
        del row["values"]["current_numeric_parameters"]
        with self.assertRaises(ValueError):
            project_log_clocks([row])
        row["values"]["current_count"] = 0
        rows, _ = project_log_clocks([row])
        self.assertNotIn("current_numeric_parameters", rows[0]["values"])


if __name__ == "__main__":
    unittest.main()
