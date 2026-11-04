"""Health must not pass tutoring when its authenticated endpoint is unusable."""
import importlib.util
import os
from pathlib import Path
import unittest
import contextlib
import io
from unittest.mock import patch, MagicMock

path = Path(__file__).resolve().parents[2] / 'tools/diagnostics/check_runtime.py'
spec = importlib.util.spec_from_file_location('runtime_diagnostic', path)
diagnostic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnostic)


class TutorAuthDiagnosticTest(unittest.TestCase):
    def setUp(self):
        diagnostic.RESULTS.clear()
        diagnostic.FAILURES.clear()

    def test_missing_credential_cannot_report_ready(self):
        with patch.dict(os.environ, {'INTERNAL_API_KEY': ''}):
            diagnostic.check_tutor_auth()
        self.assertEqual(diagnostic.RESULTS['Tutor internal auth'], 'BLOCKED')

    def test_success_requires_authenticated_request(self):
        response = MagicMock()
        response.__enter__.return_value.status = 200
        with patch.dict(os.environ, {'INTERNAL_API_KEY': 'synthetic-test-only'}), patch.object(diagnostic.urllib.request, 'urlopen', return_value=response) as opened:
            diagnostic.check_tutor_auth()
            request = opened.call_args.args[0]
            self.assertEqual(request.get_header('X-internal-api-key'), 'synthetic-test-only')
        self.assertEqual(diagnostic.RESULTS['Tutor internal auth'], 'PASS')

    def test_rejected_key_reports_failure_without_disclosing_exception(self):
        with patch.dict(os.environ, {'INTERNAL_API_KEY': 'synthetic-test-only'}), patch.object(diagnostic.urllib.request, 'urlopen', side_effect=RuntimeError('synthetic-test-only')):
            diagnostic.check_tutor_auth()
        self.assertEqual(diagnostic.RESULTS['Tutor internal auth'], 'FAIL')
        self.assertNotIn('synthetic-test-only', str(diagnostic.FAILURES))

    def test_healthy_ports_cannot_mask_a_blocked_tutoring_service(self):
        for name in ['Docker', 'PostgreSQL', 'MinIO', 'Redis', 'Spring Boot', 'FastAPI',
                     'Celery Worker', 'Unified Portal Web', 'Teacher Web', 'Admin Web', 'Student Metro']:
            diagnostic.record_result(name, 'PASS')
        methods = ['docker', 'postgres', 'minio', 'redis', 'spring', 'fastapi', 'celery',
                   'portal_web', 'teacher_web', 'admin_web', 'student_metro']
        lan = dict.fromkeys(['lan_ip', 'metro_state', 'metro_bind_addr', 'metro_lan_reach',
                             'spring_host_reach', 'spring_lan_reach', 'configured_host',
                             'config_source', 'mismatch_warning', 'lan_verdict'], '')
        with contextlib.ExitStack() as stack:
            for method in methods:
                stack.enter_context(patch.object(diagnostic, f'check_{method}'))
            stack.enter_context(patch.object(diagnostic, 'check_lan_diagnostics', return_value=lan))
            stack.enter_context(patch.dict(os.environ, {'INTERNAL_API_KEY': ''}))
            output = stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            self.assertEqual(diagnostic.main(), 1)
            self.assertIn('NOT_READY', output.getvalue())
            self.assertNotIn('READY_FOR_FULL_DEMO', output.getvalue())


if __name__ == '__main__':
    unittest.main()
