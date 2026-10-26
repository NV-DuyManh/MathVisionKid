"""Actual primary782 bindings and source-only V2 migration; CPU data only.

Uses the existing pinned local tokenizer, never weights or held-out eval data.
All mutations and databases are temporary fixtures; originals are only read.
"""
import gzip
import hashlib
import json
import sqlite3
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

import exhaustive_colab_loader as L
import math_data_archive_audit as A
import math_data_full_audit_v2 as V2
import math_data_full_audit_v3 as V3
import math_data_primary782_bindings_v3 as P
from math_data_candidate_stream import build_recipe, member_key
from math_data_portable_resume import canonical, digest, file_hash


class FullAuditV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = Path(__file__).resolve().parent / 'data/primary_math_teacher_20261016/exports'
        cls.source_path = cls.base / 'accepted_teacher_cases_polished.jsonl'
        cls.source_bytes = cls.source_path.read_bytes()
        assert hashlib.sha256(cls.source_bytes).hexdigest() == V3.PRIMARY_MEMBER_SHA256
        cls.lines = cls.source_bytes.decode('utf8').splitlines()
        cls.rows = [json.loads(line) for line in cls.lines]
        cls.chat_path = cls.base / 'teacher_chat_train_polished.jsonl'
        cls.chat_bytes = cls.chat_path.read_bytes()
        assert hashlib.sha256(cls.chat_bytes).hexdigest() == P.PROVENANCE['input_files_sha256']['exports/teacher_chat_train_polished.jsonl']
        cls.chats = [json.loads(line) for line in cls.chat_bytes.splitlines()]
        cls.by_id = {}
        for row in cls.chats:
            cls.by_id.setdefault(L.case_id(row), []).append(row)
        cls.missing_index = next(i for i, row in enumerate(cls.rows) if 'can_solve' not in row)
        cls.tokenizer = L.load_qwen_tokenizer(Path.home() / '.cache/huggingface/hub/models--Qwen--Qwen3-1.7B/snapshots' / L.REVISION)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def primary_entry(self):
        return dict(file_id='fixture_primary782', file_name=self.source_path.name,
                    sha256=V3.PRIMARY_MEMBER_SHA256, bytes=len(self.source_bytes),
                    role='candidate_source', rows=782)

    def entry(self, name, rows, role):
        path = self.root / (name + '.jsonl.gz')
        path.write_bytes(gzip.compress(''.join(canonical(row) + '\n' for row in rows).encode('utf8'), mtime=0))
        return dict(file_id=name, file_name=path.name, sha256=file_hash(path),
                    bytes=path.stat().st_size, role=role, rows=len(rows)), path

    def primary_fixture(self, chats=None):
        row = self.rows[self.missing_index]
        chats = deepcopy(self.by_id[row['sample_id']]) if chats is None else chats
        source = self.primary_entry()
        chat, chat_path = self.entry('primary_chat', chats, 'candidate_chat')
        return build_recipe([{'members': [source, chat]}]), source, chat, chat_path

    def indexed_one_primary(self, recipe, source, name='one'):
        # A bounded fixture source index with an exact real row. This isolates
        # four tokenized chats without claiming a full782-row runtime audit.
        audit = V3.FullArchiveAudit(self.root / (name + '.db'), recipe, self.tokenizer)
        audit._source(self.rows[self.missing_index], member_key(source),
                      self.missing_index + 1, self.lines[self.missing_index])
        audit.db.execute('INSERT INTO members VALUES (?,?,?,1,?)',
                         (member_key(source), source['role'], source['rows'], source['rows']))
        audit.db.commit()
        return audit

    def test_all782_exact_bindings_and_all3128_full_prompt_targets(self):
        before = hashlib.sha256(self.source_bytes).hexdigest()
        V3.verify_primary_bindings()
        seen = set()
        for row, text in zip(self.rows, self.lines):
            raw = V3.rawhash(text)
            projection, binding = V3.primary_projection(row, raw)
            self.assertEqual(binding['exported_canonical_sha256'], digest(row))
            self.assertEqual(binding['original_or_derived_source_sha256'], row['verification']['source_row_sha256'])
            self.assertEqual(binding['existing_owner_attested'], row['human_verified'])
            for chat in self.by_id[row['sample_id']]:
                self.assertEqual(A.linkage_errors(chat, projection), [])
                self.assertEqual(chat['source_row_sha256'], binding['original_or_derived_source_sha256'])
                self.assertEqual(chat['row_sha256'], binding['exported_canonical_sha256'])
                self.assertEqual(digest(chat['verification']), binding['source_verification_digest'])
                seen.add(chat['sample_id'])
        self.assertEqual(len(seen), 3128)
        self.assertEqual(file_hash(self.source_path), before)
        self.assertEqual(file_hash(self.chat_path), hashlib.sha256(self.chat_bytes).hexdigest())

    def test_known_missing_can_solve_links_four_actual_tokenized_chats(self):
        recipe, source, chat, path = self.primary_fixture()
        audit = self.indexed_one_primary(recipe, source)
        try:
            audit.consume(chat, path, None)
            report = audit.report()
            self.assertEqual(report['issues'], {})
            self.assertEqual(report['source_hash_origins'], {'PRIMARY_ORIGINAL_AND_EXPORTED_HASH_VERIFIED': 4})
            self.assertEqual(report['unique_chat_rows_processed'], 4)
            self.assertGreater(report['max_sequence_tokens'], 0)
            self.assertFalse(report['TRAINING_DATASET_READY'])
            self.assertFalse(report['training_started'])
        finally:
            audit.close()

    def test_primary_any_hash_role_tampering_is_rejected_without_fallback(self):
        original = self.by_id[self.rows[self.missing_index]['sample_id']]
        for name, field, value in [('source', 'source_row_sha256', 'f' * 64),
                                   ('export', 'row_sha256', 'f' * 64),
                                   ('verification', 'verification', {})]:
            with self.subTest(role=name):
                chats = deepcopy(original)
                chats[0][field] = value
                recipe, source, chat, path = self.primary_fixture(chats)
                audit = self.indexed_one_primary(recipe, source, name)
                try:
                    audit.consume(chat, path, None)
                    report = audit.report()
                    self.assertEqual(report['issues']['SOURCE_HASH_CHAIN_MISMATCH'], 1)
                    self.assertEqual(report['source_linkage_unverified_rows'], 1)
                    self.assertFalse(report['full_archive_token_linkage_split_audit_complete'])
                finally:
                    audit.close()

    def test_projection_rejects_changed_source_or_wrong_raw_hash(self):
        row = deepcopy(self.rows[self.missing_index])
        raw = V3.rawhash(self.lines[self.missing_index])
        row['initial_guidance'] += ' fixture mutation'
        with self.assertRaisesRegex(ValueError, 'exact exported row'):
            V3.primary_projection(row, raw)
        with self.assertRaisesRegex(ValueError, 'exact exported row'):
            V3.primary_projection(self.rows[self.missing_index], 'f' * 64)

    def test_matching_hash_metadata_cannot_hide_changed_prompt_or_target(self):
        original = self.by_id[self.rows[self.missing_index]['sample_id']]
        for name, message_index, field in [('prompt', 1, 'problem'), ('target', 2, 'fixture_tamper')]:
            with self.subTest(role=name):
                chats = deepcopy(original)
                payload = json.loads(chats[0]['messages'][message_index]['content'])
                payload[field] = 'tampered fixture content'
                chats[0]['messages'][message_index]['content'] = canonical(payload)
                recipe, source, chat, path = self.primary_fixture(chats)
                audit = self.indexed_one_primary(recipe, source, name)
                try:
                    audit.consume(chat, path, None)
                    report = audit.report()
                    self.assertEqual(report['source_linkage_unverified_rows'], 1)
                    self.assertEqual(report['issues']['SOURCE_CHAT_LINKAGE_UNVERIFIED'], 1)
                    self.assertFalse(report['full_archive_token_linkage_split_audit_complete'])
                finally:
                    audit.close()

    def test_unrecognized_missing_can_solve_is_not_blanket_adapted(self):
        row = deepcopy(self.rows[self.missing_index])
        row['sample_id'] = 'fixture_unknown_missing_can_solve'
        entry, path = self.entry('unknown_source', [row], 'candidate_source')
        recipe = build_recipe([{'members': [entry]}])
        audit = V3.FullArchiveAudit(self.root / 'unknown.db', recipe, self.tokenizer)
        try:
            audit.consume(entry, path, None)
            report = audit.report()
            self.assertEqual(report['source_versions_indexed'], 0)
            self.assertEqual(report['issues']['SOURCE_SCHEMA_UNSUPPORTED_OR_HASH_MISMATCH'], 1)
            self.assertFalse(report['full_archive_token_linkage_split_audit_complete'])
        finally:
            audit.close()

    def make_v2_source_fixture(self):
        source = self.primary_entry()
        # A synthetic diagnostic with explicit regression_only label, never an
        # actual held-out question. Its finding must survive migration.
        diagnostic = deepcopy(self.rows[0])
        diagnostic['sample_id'] = 'fixture_regression_label'
        diagnostic['split'] = 'regression_only'
        other, other_path = self.entry('diagnostic', [diagnostic], 'candidate_source')
        recipe = build_recipe([{'members': [other, source]}])
        parent = self.root / 'parent_v2.db'
        audit = V2.FullArchiveAudit(parent, recipe, self.tokenizer)
        audit.consume(other, other_path, None)
        audit.consume(source, self.source_path, 2)
        audit.close()
        return parent, recipe, source

    def test_migration_preserves_parent_all_identities_cursors_issues_and_nonprimary_projection(self):
        parent, recipe, source = self.make_v2_source_fixture()
        parent_hash = file_hash(parent)
        old = sqlite3.connect(parent)
        before = {
            'members': old.execute('SELECT * FROM members ORDER BY id').fetchall(),
            'issues': old.execute('SELECT * FROM issues ORDER BY member,line,kind,detail').fetchall(),
            'identity': old.execute('SELECT identity FROM config').fetchone()[0],
            'sources': old.execute('SELECT * FROM source_versions ORDER BY id,raw_sha').fetchall(),
        }
        old.close()
        destination = self.root / 'derived_v3.db'
        receipt = V3.migrate_v2_snapshot(parent, destination, recipe, parent_hash,
                                        expected_source_versions=3, expected_members_complete=1,
                                        expected_primary_rows=2)
        self.assertEqual(file_hash(parent), parent_hash)
        self.assertEqual(receipt['primary_projections_adapted'], 2)
        self.assertEqual(receipt['issues_preserved'], 1)
        new = V3.FullArchiveAudit(destination, recipe, self.tokenizer)
        try:
            self.assertEqual(new.db.execute('SELECT * FROM members ORDER BY id').fetchall(), before['members'])
            self.assertEqual(new.db.execute('SELECT * FROM issues ORDER BY member,line,kind,detail').fetchall(), before['issues'])
            self.assertEqual(new.report()['issues'], {'SOURCE_SPLIT_MISSING_OR_UNKNOWN': 1})
            self.assertEqual(new.report()['unique_chat_rows_processed'], 0)
            self.assertNotEqual(new.identity, before['identity'])
            self.assertEqual(new.next_entry(), source)
            after = {row[0]: row for row in new.db.execute('SELECT * FROM source_versions')}
            for row in before['sources']:
                derived = after[row[0]]
                self.assertEqual(derived[:3], row[:3])
                self.assertEqual(derived[4:6], row[4:6])
                if row[0] == 'fixture_regression_label':
                    self.assertEqual(derived[:6], row)
                    self.assertEqual(derived[6:], (None, None, None))
                else:
                    binding = P.BINDINGS[row[1]]
                    self.assertEqual(digest(json.loads(derived[3])), binding['projection_sha256'])
            self.assertFalse(V3.source_chat_split_compatible('regression_only', 'train'))
            self.assertFalse(new.report()['full_archive_token_linkage_split_audit_complete'])
        finally:
            new.close()

    def test_migration_rejects_wrong_parent_hash_in_place_and_wrong_counts(self):
        parent, recipe, _ = self.make_v2_source_fixture()
        parent_hash = file_hash(parent)
        for destination, sha in [(parent, parent_hash), (self.root / 'bad_hash.db', 'f' * 64)]:
            with self.assertRaises(ValueError):
                V3.migrate_v2_snapshot(parent, destination, recipe, sha)
        with self.assertRaisesRegex(ValueError, 'Source checkpoint count'):
            V3.migrate_v2_snapshot(parent, self.root / 'wrong_count.db', recipe, parent_hash,
                                    expected_source_versions=4)
        self.assertEqual(file_hash(parent), parent_hash)

    def test_v3_refuses_v2_identity_before_any_mutation(self):
        parent, recipe, _ = self.make_v2_source_fixture()
        before = file_hash(parent)
        with self.assertRaisesRegex(ValueError, 'Different immutable audit identity'):
            V3.FullArchiveAudit(parent, recipe, self.tokenizer)
        self.assertEqual(file_hash(parent), before)


if __name__ == '__main__':
    unittest.main()
