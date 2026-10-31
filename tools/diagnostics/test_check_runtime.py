import io
import json
import unittest
import subprocess
from unittest.mock import patch

import check_runtime


class SpringRuntimeIdentityTest(unittest.TestCase):
    def test_health_requires_this_checkout(self):
        expected = check_runtime.REPO_ROOT / 'backend' / 'business-api'
        for runtime_path, verdict in (
            (str(expected / '.'), 'PASS'),
            (str(expected.parent / 'other-backend'), 'FAIL'),
            (None, 'FAIL'),
        ):
            with self.subTest(runtime_path=runtime_path):
                check_runtime.RESULTS.clear()
                check_runtime.FAILURES.clear()
                health = {'status': 'UP', 'components': {'diskSpace': {
                    'details': {'path': runtime_path},
                }}}
                with patch('urllib.request.urlopen', return_value=io.BytesIO(json.dumps(health).encode())):
                    check_runtime.check_spring()
                self.assertEqual(verdict, check_runtime.RESULTS['Spring Boot'])


class CeleryDeadlineTest(unittest.TestCase):
    def test_import_allowance_does_not_remove_the_worker_ping_deadline(self):
        check_runtime.RESULTS.clear()
        with patch('subprocess.run', return_value=subprocess.CompletedProcess([], 0)) as run:
            check_runtime.check_celery()
        self.assertEqual(20, run.call_args.kwargs['timeout'])
        self.assertIn('timeout=2.5', run.call_args.args[0][-1])
        self.assertEqual('PASS', check_runtime.RESULTS['Celery Worker'])

    def test_stalled_process_is_reported_as_failure(self):
        check_runtime.RESULTS.clear()
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('celery', 20)):
            check_runtime.check_celery()
        self.assertEqual('FAIL', check_runtime.RESULTS['Celery Worker'])


if __name__ == '__main__':
    unittest.main()
