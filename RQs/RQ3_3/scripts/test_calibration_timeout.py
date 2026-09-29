"""Timeout-only metadata compatibility; scientific changes must still fail."""
from copy import deepcopy
from types import SimpleNamespace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from RQs.RQ3_3.src import main
from RQs.RQ3_3.scripts.test_formal_queue import QueueRegression


class CalibrationRuntimeRegression(unittest.TestCase):
    def fixture(self):
        data = {'common': {'request_timeout_sec': 300, 'temperature': 1.0,
                          'top_p': .95, 'max_model_len': 40960}, 'models': {'qwen': {'revision': 'fixed'}}}
        current = {'config_hash': main.stable_hash(data), 'max_tokens': 8192, 'dtype': 'bfloat16'}
        old = deepcopy(data); old['common']['request_timeout_sec'] = 1800
        prior = {**current, 'config_hash': main.stable_hash(old)}
        return data, current, prior

    def test_identical_metadata_needs_no_reconstruction(self):
        self.assertEqual(main.calibration_runtime_compatibility({'config_hash': 'same'}, {'config_hash': 'same'}), 'identical')

    def test_only_registered_timeout_successor_allowed_without_mutation(self):
        data, current, prior = self.fixture(); saved = deepcopy((data, current, prior))
        self.assertEqual(main.calibration_runtime_compatibility(prior, current, SimpleNamespace(data=data)),
                         'request_timeout_1800_to_300_only')
        self.assertEqual((data, current, prior), saved)

    def test_other_historical_yaml_changes_rejected(self):
        data, current, prior = self.fixture()
        variants = []
        for key, value in [('temperature', .7), ('top_p', .9), ('max_model_len', 32768)]:
            old = deepcopy(data); old['common']['request_timeout_sec'] = 1800; old['common'][key] = value
            variants.append(old)
        old = deepcopy(data); old['common']['request_timeout_sec'] = 1800; old['models']['qwen']['revision'] = 'other'
        variants.append(old)
        for variant in variants:
            with self.subTest(variant=variant), self.assertRaises(ValueError):
                main.calibration_runtime_compatibility({**prior, 'config_hash': main.stable_hash(variant)},
                                                      current, SimpleNamespace(data=data))

    def test_missing_hash_and_explicit_output_change_rejected(self):
        data, current, prior = self.fixture()
        for old in ({k: v for k, v in prior.items() if k != 'config_hash'}, {**prior, 'max_tokens': 4096}):
            with self.subTest(old=old), self.assertRaises(ValueError):
                main.calibration_runtime_compatibility(old, current, SimpleNamespace(data=data))

    def test_wrong_live_hash_or_timeout_rejected(self):
        data, current, prior = self.fixture()
        bad_data = deepcopy(data); bad_data['common']['request_timeout_sec'] = 600
        for actual, envelope in [(data, {**current, 'config_hash': 'incorrect'}),
                                 (bad_data, {**current, 'config_hash': main.stable_hash(bad_data)})]:
            with self.assertRaises(ValueError):
                main.calibration_runtime_compatibility(prior, envelope, SimpleNamespace(data=actual))

    def test_bad_manifest_blocks_queue_before_preparation_and_gpu(self):
        with tempfile.TemporaryDirectory() as tmp:
            queue = QueueRegression().queue(Path(tmp))
            task = {'logical_key': 'new', 'model': queue.config['models'][0]}
            with patch.object(queue, 'check'), patch.object(queue, 'command') as command, \
                    patch.object(queue, 'start_server') as server, patch.object(main, 'prerequisite'), \
                    patch.object(main.gates, 'task_matrix', return_value=[task]), \
                    patch.object(main, 'calibration_runtime_preflight', side_effect=ValueError('fixture config mismatch')):
                with self.assertRaisesRegex(ValueError, 'fixture config mismatch'):
                    queue.stage('calibration')
                command.assert_not_called(); server.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
