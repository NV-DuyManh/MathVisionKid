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
    def test_repeat_reads_reuse_one_durable_entry_and_count_hits(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'test.sqlite3'
            CatalogStore(path).put('plan','account-a','exact-source','policy-v1',b'checked-plan')
            for _ in range(3):
                self.assertEqual(CatalogStore(path).get('plan','account-a','exact-source','policy-v1'),b'checked-plan')
            self.assertEqual(CatalogStore(path).audit()['groups'],[
                dict(kind='plan',entries=1,bytes=12,hits=3)])

    def test_audio_keys_keep_the_two_voices_and_paragraph_order_separate(self):
        with tempfile.TemporaryDirectory() as folder:
            store=CatalogStore(Path(folder)/'test.sqlite3')
            store.put('audio','account-a','male:paragraph-1,paragraph-2','v1',b'male-audio')
            self.assertIsNone(store.get('audio','account-a','female:paragraph-1,paragraph-2','v1'))
            self.assertIsNone(store.get('audio','account-a','male:paragraph-2,paragraph-1','v1'))
            store.put('audio','account-a','female:paragraph-1,paragraph-2','v1',b'female-audio')
            self.assertEqual(store.get('audio','account-a','male:paragraph-1,paragraph-2','v1'),b'male-audio')
            self.assertEqual(store.get('audio','account-a','female:paragraph-1,paragraph-2','v1'),b'female-audio')

    def test_read_only_audit_does_not_expose_keys_or_modify_entries(self):
        with tempfile.TemporaryDirectory() as folder:
            store=CatalogStore(Path(folder)/'test.sqlite3')
            store.put('plan','private-account','private-question','private-policy',b'private-content')
            before=store.path.read_bytes()
            audit=store.audit()
            self.assertEqual(store.path.read_bytes(),before)
            self.assertEqual(audit['groups'],[dict(kind='plan',entries=1,bytes=15,hits=0)])
            self.assertNotIn('private',str(audit))

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
