"""Offline bot/report tests; all databases are disposable, no provider or real pupil state."""
import json
import os
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import catalog_bot as bot


class BotChecks(unittest.TestCase):
    def setUp(self):
        environment=patch.dict(os.environ,{'GITHUB_ACTIONS':'false','GITHUB_STEP_SUMMARY':'',
                                          'CATALOG_BOT_TEST_STATUS':''})
        environment.start()
        self.addCleanup(environment.stop)

    def test_public_report_has_no_private_inventory(self):
        report=bot.inspect_catalog(bot.ROOT/'ai/runtime/tests/fixtures/student_learning_regression.json')
        self.assertTrue(report['passed'])
        self.assertIsNone(report['private'])
        self.assertEqual(report['scope'],'public-ci')
        self.assertGreater(report['inventory']['cases'],0)
        self.assertIn('Không truy cập',bot.markdown(report))

    def test_private_snapshot_is_aggregate_only_and_read_only(self):
        with tempfile.TemporaryDirectory() as folder:
            database=Path(folder)/'private.sqlite3'
            store=bot.CatalogStore(database)
            store.put('plan','secret-owner','secret-source','secret-policy',b'secret-payload')
            store.get('plan','secret-owner','secret-source','secret-policy')
            before=database.read_bytes()
            report=bot.inspect_catalog(bot.ROOT/'ai/runtime/tests/fixtures/student_learning_regression.json',database)
            self.assertTrue(report['passed'])
            self.assertEqual(report['private']['groups'],[dict(kind='plan',entries=1,bytes=14,hits=1)])
            for content in (json.dumps(report),bot.dashboard(report),bot.markdown(report)):
                self.assertNotIn('secret-',content)
                self.assertNotIn(str(database),content)
            self.assertEqual(database.read_bytes(),before)

    def test_cloud_refuses_any_private_database_argument_before_reading(self):
        with patch.dict(os.environ,{'GITHUB_ACTIONS':'true'}),patch.object(bot.CatalogStore,'audit') as audit:
            with self.assertRaises(ValueError):
                bot.inspect_catalog(Path('unused'),Path('private.sqlite3'))
            with self.assertRaises(SystemExit) as error:
                bot.main(['--database','private.sqlite3'])
            self.assertEqual(error.exception.code,2)
            audit.assert_not_called()

    def test_missing_database_is_unknown_not_fabricated_zero_and_is_not_created(self):
        with tempfile.TemporaryDirectory() as folder:
            database=Path(folder)/'absent'/'private.sqlite3'
            report=bot.inspect_catalog(bot.ROOT/'ai/runtime/tests/fixtures/student_learning_regression.json',database)
            self.assertEqual(report['private'],dict(status='not-created'))
            self.assertNotIn('Kế hoạch đang lưu',bot.markdown(report))
            self.assertFalse(database.parent.exists())

    def test_corrupt_database_or_payload_reports_failure_without_deleting_it(self):
        with tempfile.TemporaryDirectory() as folder:
            database=Path(folder)/'damaged.sqlite3'
            database.write_bytes(b'not-a-sqlite-database')
            report=bot.inspect_catalog(bot.ROOT/'ai/runtime/tests/fixtures/student_learning_regression.json',database)
            self.assertFalse(report['passed'])
            self.assertEqual(report['private']['status'],'unavailable')
            self.assertEqual(database.read_bytes(),b'not-a-sqlite-database')
            database.unlink()
            store=bot.CatalogStore(database)
            store.put('plan','owner','source','v1',b'checked')
            with closing(sqlite3.connect(database)) as connection, connection:
                connection.execute("UPDATE entries SET digest='damaged'")
            report=bot.inspect_catalog(bot.ROOT/'ai/runtime/tests/fixtures/student_learning_regression.json',database)
            self.assertFalse(report['passed'])
            self.assertEqual(report['private']['corrupt'],1)
            self.assertEqual(store.audit()['groups'][0]['entries'],1)

    def test_malformed_public_corpus_creates_a_failed_report_and_nonzero_exit(self):
        with tempfile.TemporaryDirectory() as folder:
            corpus=Path(folder)/'bad.json';corpus.write_text('{}',encoding='utf-8')
            output=Path(folder)/'report'
            self.assertEqual(bot.main(['--corpus',str(corpus),'--output',str(output)]),1)
            report=json.loads(output.joinpath('status.json').read_text(encoding='utf-8'))
            self.assertFalse(report['passed'])
            self.assertIn('Có kiểm tra chưa đạt',output.joinpath('index.html').read_text(encoding='utf-8'))

    def test_github_step_summary_and_three_exact_artifacts_are_written(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'report';summary=Path(folder)/'github-summary.md'
            with patch.dict(os.environ,{'GITHUB_STEP_SUMMARY':str(summary)}):
                self.assertEqual(bot.main(['--output',str(output)]),0)
            self.assertEqual({path.name for path in output.iterdir()},{'status.json','summary.md','index.html'})
            self.assertIn('MathVision Catalog Bot',summary.read_text(encoding='utf-8'))
            html=output.joinpath('index.html').read_text(encoding='utf-8')
            self.assertIn('lang="vi"',html)
            self.assertIn('Content-Security-Policy',html)
            self.assertNotIn('<script',html)

    def test_failed_or_skipped_ci_regressions_cannot_produce_a_green_report(self):
        for outcome in ('failure','skipped','cancelled'):
            with self.subTest(outcome=outcome),patch.dict(os.environ,{'CATALOG_BOT_TEST_STATUS':outcome}):
                report=bot.inspect_catalog(bot.ROOT/'ai/runtime/tests/fixtures/student_learning_regression.json')
                self.assertFalse(report['passed'])


if __name__=='__main__':
    unittest.main()
