"""Timeout continuation at stage/decision boundaries; no real model calls."""
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from RQs.RQ3_3.src import exps, gates, main
from RQs.RQ3_3.src.utils import PRIMARY, load_config
from RQs.RQ3_3.scripts.test_formal_queue import QueueRegression as QueueFixture
from vlmrca.run_state import write_json


class TerminalTimeoutTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config()

    def rows(self, arms, budget=None):
        return [{'model': self.config['primary_model'], 'dataset': dataset,
                 'case_id': f'{dataset}-{i}', 'status': 'done', 'input_tokens': 100,
                 'dimensions': {'arm': arm, 'budget_tokens': budget},
                 'metrics': {'mrr': .5, 'ac@1': 0, 'ac@5': 1}}
                for dataset in PRIMARY for i in range(2) for arm in arms]

    def timeout(self, row):
        row.update(status='fail', failure_class='request_timeout', metrics=None)

    def test_terminal_counts_only_allow_classified_timeouts(self):
        self.assertEqual(gates.terminal_failure_counts([
            {'status': 'done'}, {'status': 'fail', 'failure_class': 'request_timeout'}]),
            {'failed_units': 1, 'request_timeout_units': 1, 'blocking_failure_units': 0})
        for row in ({'status': 'fail'}, {'status': 'fail', 'failure_class': 'engine_dead'},
                    {'status': 'pending'}):
            with self.subTest(row=row), self.assertRaises(ValueError):
                gates.terminal_failure_counts([row])

    def test_screen_prerequisite_legacy_marker_reads_only_small_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reg = {'rosters': {'screen': [{'dataset': d, 'opaque_incident_id': d} for d in PRIMARY]}}
            tasks = gates.task_matrix(self.config, reg, 'calibration')
            write_json(root/'registration.json', reg)
            write_json(root/'stages/calibration/complete.json',
                       {'registered': len(tasks), 'terminal': len(tasks), 'failed_units': 1})
            for task in tasks:
                write_json(root/'flags'/(task['logical_key']+'.json'), {'status': 'done'})
            failed = root/'flags'/(tasks[0]['logical_key']+'.json')
            write_json(failed, {'status': 'fail', 'failure_class': 'request_timeout'})
            with patch.object(main, 'load_context', side_effect=AssertionError('no context reads')), \
                    patch.object(main, 'OfflineTokens', side_effect=AssertionError('no tokenization')):
                self.assertIsNone(main.prerequisite(self.config, root, 'screen', False))
                write_json(failed, {'status': 'fail', 'failure_class': 'engine_dead'})
                with self.assertRaisesRegex(ValueError, 'non-timeout'):
                    main.prerequisite(self.config, root, 'screen', False)
                failed.unlink()
                with self.assertRaisesRegex(ValueError, 'incomplete'):
                    main.prerequisite(self.config, root, 'screen', False)

    def test_partial_calibration_cannot_enter_screen(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root/'stages/calibration/complete.json', {'registered': 480, 'terminal': 479})
            with self.assertRaisesRegex(ValueError, 'not fully terminal'):
                main.prerequisite(self.config, root, 'screen', False)

    def test_screen_timeout_excludes_whole_case_across_variants(self):
        rows = self.rows(('TPV', *exps.W_VARIANTS))
        target = rows[0]['case_id']
        self.timeout(rows[0])
        decision = gates.select_variant(rows, self.config)
        self.assertEqual(decision['paired_n'], 5)
        self.assertEqual(decision['excluded_timeout_case_ids'], [target])
        self.assertNotIn(target, decision['case_ids'])
        self.assertEqual(decision['baseline_mrr'], .5)
        self.assertFalse(decision['screen_positive'])
        self.assertEqual(rows[0]['status'], 'fail')

    def test_missing_or_inapplicable_primary_cell_still_blocks(self):
        rows = self.rows(('TPV', *exps.W_VARIANTS))
        for changed in (rows[1:], [{**rows[0], 'status': 'not_applicable'}, *rows[1:]],
                        [{**rows[0], 'status': 'fail', 'failure_class': 'server_error'}, *rows[1:]]):
            with self.assertRaises(ValueError):
                gates.select_variant(changed, self.config)

    def test_timeout_must_not_remove_an_entire_dataset_silently(self):
        rows = self.rows(('TPV', *exps.W_VARIANTS))
        for row in rows:
            if row['dataset'] == PRIMARY[0] and row['dimensions']['arm'] == 'TPV':
                self.timeout(row)
        with self.assertRaisesRegex(ValueError, 'all three'):
            gates.select_variant(rows, self.config)

    def test_model_failure_and_design_failure_remain_scored(self):
        rows = self.rows(('TPV', *exps.W_VARIANTS))
        rows[0].update(metrics={'mrr': 0, 'ac@1': 0, 'ac@5': 0}, model_output_status='format_error')
        rows[1].update(status='design_infeasible', metrics=None)
        decision = gates.select_variant(rows, self.config)
        self.assertEqual(decision['paired_n'], 6)
        self.assertEqual(decision['excluded_timeout_case_ids'], [])

    def test_budget_uses_same_cases_for_all_levels(self):
        screen = self.rows(('W_RAW',), 2048)
        budgets = sum((self.rows(('W_G', 'P0_MORE_TRUE'), b) for b in (1024, 4096)), [])
        failed = next(r for r in budgets if r['dimensions']['budget_tokens'] == 4096)
        target = failed['case_id']
        for r in screen + budgets:
            r['metrics']['mrr'] = 1 if r['case_id'] == target else .5
        self.timeout(failed)
        saved = deepcopy((screen, budgets))
        decision = gates.lock_budget({'variant': 'W_RAW'}, screen, budgets, self.config)
        self.assertEqual(decision['budget_paired_n'], 5)
        self.assertEqual(decision['budget_excluded_timeout_case_ids'], [target])
        self.assertEqual(decision['budget_mrr'], {1024: .5, 2048: .5, 4096: .5})
        self.assertEqual(decision['budget_tokens'], 1024)
        self.assertEqual((screen, budgets), saved)

    def test_check_thresholds_not_bypassed_by_timeout(self):
        rows = self.rows(('TPV', 'P0_MORE_TRUE', 'SIRCL_TEXT', 'W_G', 'W_T'))
        self.timeout(rows[0])
        decision = gates.check_expansion(rows, self.config)
        self.assertEqual(decision['paired_n'], 5)
        self.assertFalse(decision['passed'])
        self.assertFalse(decision['rules']['repair'])

    def test_queue_unknown_failure_cannot_be_skipped_into_next_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            queue = QueueFixture().queue(Path(tmp))
            task = {'logical_key': 'oldfail', 'model': queue.config['models'][0]}
            write_json(queue.root/'flags/oldfail.json', {'status': 'fail'})
            with patch.object(queue, 'check'), patch.object(queue, 'command') as command, \
                    patch.object(queue, 'start_server') as server, patch.object(main, 'prerequisite'), \
                    patch.object(gates, 'task_matrix', return_value=[task]):
                with self.assertRaisesRegex(ValueError, 'non-timeout'):
                    queue.stage('calibration')
                command.assert_not_called()
                server.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
