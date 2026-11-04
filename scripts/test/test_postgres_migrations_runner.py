import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('migration_runner', Path(__file__).with_name('test_postgres_migrations.py'))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class MigrationRunnerTest(unittest.TestCase):
    def test_non_ci_or_non_test_database_is_rejected_before_connecting(self):
        for environment in ({'GITHUB_ACTIONS':'false','PGDATABASE':'disposable_test'}, {'GITHUB_ACTIONS':'true','PGDATABASE':'production'}):
            with patch.dict(os.environ, environment), patch.object(runner.subprocess, 'check_output') as connect:
                with self.assertRaises(SystemExit):
                    runner.main()
                connect.assert_not_called()

    def test_nonempty_database_is_never_modified(self):
        with patch.dict(os.environ, {'GITHUB_ACTIONS':'true','PGDATABASE':'disposable_test'}), patch.object(runner.subprocess,'check_output',return_value='7\n'), patch.object(runner.subprocess,'run') as migrate:
            with self.assertRaises(SystemExit):
                runner.main()
            migrate.assert_not_called()

    def test_versions_are_numeric_and_duplicate_versions_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            for name in ('V10__later.sql','V2__middle.sql','V1__first.sql'):
                (path/name).write_text('SELECT 1;', encoding='utf-8')
            self.assertEqual([file.name for file in runner.migration_files(path)], ['V1__first.sql','V2__middle.sql','V10__later.sql'])
            (path/'V2__duplicate.sql').write_text('SELECT 1;', encoding='utf-8')
            with self.assertRaises(ValueError):
                runner.migration_files(path)


if __name__ == '__main__':
    unittest.main()
