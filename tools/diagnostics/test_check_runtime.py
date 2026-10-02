import io
import json
import unittest
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


if __name__ == '__main__':
    unittest.main()
