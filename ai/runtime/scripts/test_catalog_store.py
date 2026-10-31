"""Offline stdlib-only checks for the GitHub catalog bot; no pupil database."""
from pathlib import Path
from contextlib import closing
import sqlite3
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.tutoring.catalog_store import CatalogStore


class CatalogChecks(unittest.TestCase):
    def test_storage_integrity_and_account_policy_isolation(self):
        with tempfile.TemporaryDirectory() as folder:
            store=CatalogStore(Path(folder)/'test.sqlite3')
            store.put('plan','a','source','v1',b'checked')
            self.assertEqual(store.get('plan','a','source','v1'),b'checked')
            self.assertIsNone(store.get('plan','b','source','v1'))
            self.assertIsNone(store.get('plan','a','changed-source','v1'))
            self.assertIsNone(store.get('plan','a','source','v2'))
            with closing(sqlite3.connect(store.path)) as db,db:db.execute("UPDATE entries SET digest='corrupt'")
            self.assertEqual(store.audit(prune=True)['corrupt'],1)
            self.assertIsNone(store.get('plan','a','source','v1'))

    def test_bounded_persistence_and_expiry(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'test.sqlite3';store=CatalogStore(path,max_entries=1)
            self.assertEqual(store.audit()['groups'],[])
            self.assertFalse(path.exists())
            store.put('plan','a','old','v',b'old');store.put('plan','a','new','v',b'new')
            self.assertIsNone(store.get('plan','a','old','v'))
            self.assertEqual(CatalogStore(path).get('plan','a','new','v'),b'new')
            with closing(sqlite3.connect(path)) as db,db:db.execute('UPDATE entries SET expires=0')
            self.assertIsNone(store.get('plan','a','new','v'))


if __name__=='__main__':unittest.main()
