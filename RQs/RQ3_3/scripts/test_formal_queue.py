"""Queue routing/terminal-skip tests, with no data preparation or GPU calls."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from RQs.RQ3_3.scripts.formal_queue import Queue
from RQs.RQ3_3.src import gates
from RQs.RQ3_3.src.utils import load_config
from vlmrca.run_state import write_json


class QueueRegression(unittest.TestCase):
    def queue(self, root):
        q = object.__new__(Queue)
        q.root = root
        q.config = load_config()
        q.registration = {'contract': {}, 'rosters': {'fresh': []}}
        q.stop = False
        q.child = q.server = None
        q.step = 'test'
        for experiment in {s['experiment'] for s in q.config['stages'].values()}:
            write_json(root/'qualification'/(experiment+'.json'),
                       {'status': 'passed', 'contract_hash': gates.stable_hash({})})
        write_json(root/'capability_audit.json', {'event_branch_qualified': False})
        return q

    def route(self, positive, expansion):
        with tempfile.TemporaryDirectory() as tmp:
            q = self.queue(Path(tmp))
            def decision(kind, path):
                return {'screen_positive': positive, 'passed': expansion}
            with patch.object(q, 'account_prior_attempts'), patch.object(q, 'stop_server'), \
                    patch.object(q, 'status'), patch.object(q, 'stage') as stages, \
                    patch.object(q, 'decision', side_effect=decision), patch('signal.signal'):
                q.run()
            return [c.args[0] for c in stages.call_args_list]

    def test_positive_path_does_not_enable_event_or_fresh(self):
        self.assertEqual(self.route(True, True), ['calibration', 'screen', 'budget', 'check',
            'effectiveness', 'organization', 'interventions', 'pairs', 'binding', 'regression'])

    def test_negative_screen_only_diagnostic(self):
        self.assertEqual(self.route(False, False), ['calibration', 'screen', 'diagnostic'])

    def test_negative_check_no_large_expansion(self):
        self.assertEqual(self.route(True, False), ['calibration', 'screen', 'budget', 'check', 'diagnostic'])

    def test_terminal_flags_skip_preparation_and_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            q = self.queue(Path(tmp))
            tasks = [{'logical_key': 'one', 'model': q.config['models'][0]},
                     {'logical_key': 'two', 'model': q.config['models'][1]}]
            for task, state in zip(tasks, ['done', 'fail']):
                write_json(q.root/'flags'/(task['logical_key']+'.json'),
                           {'status': state, 'failure_class': 'request_timeout' if state == 'fail' else None})
            write_json(q.root/'analysis/calibration.json', {})
            with patch.object(q, 'check'), patch.object(q, 'status'), \
                    patch.object(q, 'command') as cmd, patch.object(q, 'start_server') as server, \
                    patch('RQs.RQ3_3.scripts.formal_queue.main.prerequisite'), \
                    patch.object(gates, 'task_matrix', return_value=tasks):
                q.stage('calibration')
                cmd.assert_not_called()
                server.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
