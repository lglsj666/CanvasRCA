"""Focused CPU regression for defects found in live smoke; no GPU or network."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

from RQs.RQ3_3.src import main
from RQs.RQ3_3.src.utils import load_config


class SmokeRepairRegression(unittest.TestCase):
    def exercise(self, root, *, interrupt=False, endpoint_error=False):
        config = load_config()
        with patch.object(main, "smoke_inputs", side_effect=KeyboardInterrupt() if interrupt else None), \
                patch.object(main.gates, "task_matrix", return_value=[]), \
                patch.dict(os.environ, {"VLLM_API_KEY": "cpu-fixture-only"}), \
                patch("subprocess.Popen") as launch, \
                patch("urllib.request.urlopen") as probe:
            if endpoint_error:
                probe.side_effect = urllib.error.HTTPError("http://localhost/models", 401, "fixture", {}, None)
            else:
                probe.return_value.__enter__.return_value.read.return_value = b"{}"
            with self.assertRaises(KeyboardInterrupt if interrupt else RuntimeError):
                main.smoke(config, {"contract": {}}, root, "exp_witness_development")
            launch.assert_not_called()
            if not interrupt:
                request = probe.call_args.args[0]
                self.assertEqual(request.get_header("Authorization"), "Bearer cpu-fixture-only")
        report = json.loads((root / "smokes/exp_witness_development.json").read_text())
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["initiated_calls"], 0)
        self.assertLess(report["elapsed_s"], 5)
        return report

    def test_interrupt_is_failed_not_complete(self):
        with tempfile.TemporaryDirectory() as name:
            report = self.exercise(Path(name), interrupt=True)
        self.assertIn("KeyboardInterrupt", report["error"])

    def test_existing_endpoint_auth_and_ownership(self):
        with tempfile.TemporaryDirectory() as name:
            report = self.exercise(Path(name))
        self.assertIn("already owns", report["error"])

    def test_auth_error_fails_before_launch(self):
        with tempfile.TemporaryDirectory() as name:
            report = self.exercise(Path(name), endpoint_error=True)
        self.assertIn("HTTP 401", report["error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
