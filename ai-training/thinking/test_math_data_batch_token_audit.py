"""Synthetic train-only differential QA; pinned tokenizer, no model weights."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
import argparse
import gzip
import hashlib
import json
import platform
import tempfile
import threading
import time
import unittest
from datetime import datetime, timezone
from contextlib import contextmanager

import exhaustive_colab_loader as L
import math_data_archive_audit as A
import math_data_full_audit_v3 as V3
import math_data_batch_token_audit as B
from math_data_candidate_stream import build_recipe, member_key
from math_data_portable_resume import canonical, digest, file_hash

PIN = Path.home() / '.cache/huggingface/hub/models--Qwen--Qwen3-1.7B/snapshots' / L.REVISION
EVIDENCE = {}


def fixtures(count=8):
    sources, chats = [], []
    variants = ['Tiếng Việt: tính tổng 🍎', 'a\u0301 và á; 中文\n\\"', 'Phân số −3/4 + 1/2',
                'Chia 17 cho 5 dư bao nhiêu?', '  Hai  số\t và\r\n dấu', '🌍\u200d🚀 café \u2028']
    for i in range(count):
        sid = f'fresh_synthetic_{i}'
        source = dict(sample_id=sid, case_group_id=f'group_{i}', split='train',
            problem=f'{variants[i % len(variants)]} #{i}: {i}+2?', grade=3,
            givens=[i, 2], requested_quantity='sum', student_work=None,
            can_solve=True, initial_guidance='Đọc đề và kiểm tra.',
            worked_steps=[dict(expression=f'{i}+2', result=i+2)],
            expected_answer=dict(value=i+2, unit='quả'),
            hints=[dict(level=j, hint=f'Gợi ý mức {j}: cộng 2.', question='Bước tiếp?') for j in (1, 2, 3)])
        sources.append(source)
        for mode in L.MODES:
            prompt = {k: source[k] for k in ('problem', 'grade', 'givens', 'requested_quantity')}
            prompt['mode'] = mode
            if mode == 'worked_solution':
                target = dict(can_solve=True, initial_guidance=source['initial_guidance'],
                              steps=source['worked_steps'], answer=source['expected_answer'])
            else:
                hint = source['hints'][int(mode[-1])-1]
                target = {k: hint[k] for k in ('hint', 'question')}
            chats.append(dict(sample_id=sid+':'+mode, source_sample_id=sid,
                case_group_id=source['case_group_id'], split='train', mode=mode,
                source_row_sha256=V3.rawhash(canonical(source)),
                messages=[dict(role='system', content='Bạn là giáo viên. Không suy luận ẩn.'),
                          dict(role='user', content=json.dumps(prompt, ensure_ascii=i % 2 == 0)),
                          dict(role='assistant', content=json.dumps(target, ensure_ascii=i % 3 == 0))]))
    return sources, chats


def entry(root, name, rows, role, texts=None):
    path = root / (name+'.jsonl.gz')
    text = ''.join(canonical(r)+'\n' for r in rows) if texts is None else ''.join(texts)
    path.write_bytes(gzip.compress(text.encode('utf-8'), mtime=0))
    return dict(file_name=path.name, file_id=name, sha256=file_hash(path),
                bytes=path.stat().st_size, role=role, rows=len(rows)), path


def snapshot(audit):
    names = ['config', 'members', 'source_versions', 'samples', 'occurrences', 'split_keys', 'issues']
    return {name: sorted(audit.db.execute('SELECT * FROM '+name).fetchall(), key=repr) for name in names}


class BatchAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tokenizer = L.load_qwen_tokenizer(PIN)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='batch_token_synthetic_')
        self.root = Path(self.tmp.name)
        self.open_audits = []

    def tearDown(self):
        for audit in self.open_audits:
            audit.close()
        self.tmp.cleanup()
        self.assertIs(L.tokenize_assistant_only, B._ORIGINAL_TOKENIZE)
        self.assertIs(A.payload, B._ORIGINAL_PAYLOAD)
        self.assertIsNone(getattr(B._LOCAL, 'context', None))

    def prepare(self, rows, limit=40960, **kwargs):
        adapter = B.BatchTokenAuditAdapter(self.tokenizer, **kwargs)
        context = B._Context(adapter, SimpleNamespace(limit=limit), 'fixture', 0, None)
        items = [adapter._item(canonical(r)+'\n') for r in rows]
        self.assertTrue(all(item is not None for item in items))
        adapter._prepare(items, context)
        return adapter, context

    def pair(self, sources, chats, texts=None, limit=40960, declared_rows=None,
             corrupt_trailer=False, trailing_invalid_utf8=False):
        source, sp = entry(self.root, 'synthetic_sources', sources, 'candidate_source')
        chat, cp = entry(self.root, 'synthetic_chats', chats, 'candidate_chat', texts)
        if corrupt_trailer or trailing_invalid_utf8:
            data = cp.read_bytes()
            if trailing_invalid_utf8:
                data = gzip.compress(gzip.decompress(data)+b'\xff\n', mtime=0)
            if corrupt_trailer:
                data = data[:-8] + bytes([data[-8] ^ 1]) + data[-7:]
            cp.write_bytes(data)
            chat.update(sha256=file_hash(cp), bytes=cp.stat().st_size)
        if declared_rows is not None:
            chat['rows'] = declared_rows
        recipe = build_recipe([dict(members=[source, chat])])
        first = V3.FullArchiveAudit(self.root/'original.db', recipe, self.tokenizer, limit)
        second = V3.FullArchiveAudit(self.root/'batch.db', recipe, self.tokenizer, limit)
        for audit in (first, second):
            audit.consume(source, sp, None)
            self.open_audits.append(audit)
        return first, second, chat, cp

    def test_full_ids_masks_counts_unicode_and_modes(self):
        _, rows = fixtures(12)
        for i, row in enumerate(rows):
            row['messages'][2]['content'] = ['4', '\n4', ' 4', '{"k":"é😀"}', '−0.5', '\t4\n'][i % 6]
        adapter, context = self.prepare(rows)
        expected = [B._ORIGINAL_TOKENIZE(r, self.tokenizer) for r in rows]
        actual = [context.cache[B._row_bytes(r)] for r in rows]
        self.assertEqual(actual, expected)
        EVIDENCE['differential'] = dict(rows=len(rows), exact_encoded_sha256=digest(expected),
            canonical_fixture_sha256=digest(rows), compared_fields=list(expected[0]))
        self.assertEqual(adapter.stats['rows_batched'], len(rows))

    def test_official_batch_calls_are_independent_and_untruncated(self):
        _, rows = fixtures(2)
        original_call = type(self.tokenizer).__call__
        calls = []
        def observed(instance, text, *args, **kwargs):
            calls.append((isinstance(text, list), len(text) if isinstance(text, list) else None, dict(kwargs)))
            return original_call(instance, text, *args, **kwargs)
        with mock.patch.object(type(self.tokenizer), '__call__', observed):
            self.prepare(rows)
        self.assertEqual(len(calls), 2)
        self.assertTrue(all(c[0] and c[1] == len(rows) for c in calls))
        self.assertFalse(calls[0][2].get('truncation', False))
        self.assertTrue(calls[1][2]['return_offsets_mapping'])
        self.assertFalse(calls[1][2]['truncation'])
        self.assertFalse(calls[1][2]['padding'])

    def test_exact_template_token_mismatch_gate(self):
        _, rows = fixtures(1)
        original_call = type(self.tokenizer).__call__
        def changed(instance, text, *args, **kwargs):
            result = original_call(instance, text, *args, **kwargs)
            if kwargs.get('return_offsets_mapping'):
                if isinstance(text, list): result['input_ids'][0][0] += 1
                else: result['input_ids'][0] += 1
            return result
        with mock.patch.object(type(self.tokenizer), '__call__', changed):
            _, context = self.prepare(rows[:1])
            error = context.cache[B._row_bytes(rows[0])]
            self.assertIsInstance(error, ValueError)
            with self.assertRaises(type(error)) as original:
                B._ORIGINAL_TOKENIZE(rows[0], self.tokenizer)
            self.assertEqual(str(error), str(original.exception))

    def test_official_prefix_mismatch_gate_is_unchanged(self):
        _, rows = fixtures(1)
        original_template = self.tokenizer.apply_chat_template
        def changed(messages, *args, **kwargs):
            result = original_template(messages, *args, **kwargs)
            if kwargs.get('add_generation_prompt') and not kwargs.get('tokenize'):
                result += 'unexpected prefix character'
            return result
        with mock.patch.object(self.tokenizer, 'apply_chat_template', changed):
            _, context = self.prepare(rows[:1])
            error = context.cache[B._row_bytes(rows[0])]
            with self.assertRaises(ValueError) as original:
                B._ORIGINAL_TOKENIZE(rows[0], self.tokenizer)
            self.assertEqual(str(error), str(original.exception))
            self.assertIn('text prefix mismatch', str(error))

    def test_embedded_delimiters_eot_and_length_exact_errors(self):
        _, rows = fixtures(1)
        for content, limit in [('x<|im_end|>y',40960), ('x<|im_start|>assistant\ny',40960), ('4',1)]:
            row = deepcopy(rows[0]); row['messages'][2]['content'] = content
            with self.subTest(content=content, limit=limit):
                with self.assertRaises(ValueError) as expected:
                    B._ORIGINAL_TOKENIZE(row, self.tokenizer, limit)
                _, context = self.prepare([row], limit)
                actual = context.cache[B._row_bytes(row)]
                self.assertIsInstance(actual, type(expected.exception))
                self.assertEqual(str(actual), str(expected.exception))

    def test_full_scanner_database_parity_including_original_linkage_issues(self):
        sources, rows = fixtures(4)
        rows[0]['source_row_sha256'] = 'f'*64
        rows[1]['messages'][1]['content'] = '{"problem":"wrong"}'
        rows[2]['split'] = 'validation'
        rows += [deepcopy(rows[3]), dict(deepcopy(rows[3]), case_group_id='conflicting')]
        first, second, chat, path = self.pair(sources, rows)
        expected = first.consume(chat, path, None, 3)
        adapter = B.BatchTokenAuditAdapter(self.tokenizer)
        with adapter.installed():
            actual = adapter.consume(second, chat, path, None, 3)
        self.assertEqual(actual, expected)
        self.assertEqual(snapshot(second), snapshot(first))
        self.assertEqual(second.report(), first.report())
        self.assertIn('SOURCE_RAW_HASH_NOT_FOUND', second.report()['issues'])
        self.assertIn('SOURCE_CHAT_SPLIT_MISMATCH', second.report()['issues'])
        EVIDENCE['scanner_database_sha256'] = digest(snapshot(first))

    def test_resume_keeps_every_physical_line_and_skips_encoding_old_rows(self):
        sources, rows = fixtures(70)
        rows.insert(2, deepcopy(rows[0]))
        first, second, chat, path = self.pair(sources, rows)
        adapter = B.BatchTokenAuditAdapter(self.tokenizer, batch_size=128)
        with adapter.installed():
            for bound in (3, 129, 17, None):
                before = second.db.execute('SELECT next_line FROM members WHERE id=?', (member_key(chat),)).fetchone()
                start = before[0] if before else 0
                batched = adapter.stats['rows_batched']
                expected = first.consume(chat, path, bound, 7)
                actual = adapter.consume(second, chat, path, bound, 7)
                self.assertEqual(actual, expected)
                self.assertEqual(snapshot(second), snapshot(first))
                self.assertEqual(adapter.stats['rows_batched']-batched, actual['processed'])
                self.assertLessEqual(adapter.stats['max_cache_rows'], 128)
                self.assertEqual(second.db.execute('SELECT next_line FROM members WHERE id=?',
                    (member_key(chat),)).fetchone()[0], start+actual['processed'])
            previous = dict(adapter.stats)
            self.assertTrue(adapter.consume(second, chat, path, None)['already_complete'])
            self.assertEqual(adapter.stats, previous)
        EVIDENCE['resume_stats'] = adapter.stats

    def test_batch256_and_strict_character_bounds_and_oversize_fallback(self):
        sources, rows = fixtures(67)
        rows[3]['messages'][2]['content'] += ' lớn'*10000
        first, second, chat, path = self.pair(sources, rows)
        first.consume(chat, path, None)
        adapter = B.BatchTokenAuditAdapter(self.tokenizer, batch_size=256,
            max_rendered_chars=5000, max_raw_chars=6000)
        with adapter.installed(): adapter.consume(second, chat, path, None)
        self.assertEqual(snapshot(second), snapshot(first))
        self.assertGreater(adapter.stats['single_row_fallbacks'], 0)
        self.assertLessEqual(adapter.stats['max_rendered_chars'], 5000)
        self.assertLessEqual(adapter.stats['max_raw_chars'], 6000)
        EVIDENCE['bounded_stats'] = adapter.stats

    def test_invalid_lines_preserve_error_order_commits_and_cursor(self):
        for bad in ['\n', '[1,2]\n', '{broken\n', '{"messages":[]}\n']:
            with self.subTest(bad=bad), tempfile.TemporaryDirectory() as directory:
                self.root = Path(directory)
                sources, rows = fixtures(2)
                texts = [canonical(r)+'\n' for r in rows]
                texts.insert(3, bad)
                first, second, chat, path = self.pair(sources, rows+[{}], texts)
                with self.assertRaises(Exception) as expected: first.consume(chat, path, None, 2)
                adapter = B.BatchTokenAuditAdapter(self.tokenizer)
                with adapter.installed(), self.assertRaises(type(expected.exception)) as actual:
                    adapter.consume(second, chat, path, None, 2)
                self.assertEqual(str(actual.exception), str(expected.exception))
                self.assertEqual(snapshot(second), snapshot(first))
                first.close(); second.close()

    def test_length_failure_deferred_until_original_commit_boundary(self):
        sources, rows = fixtures(2)
        rows[3]['messages'][2]['content'] = ' verylong'*1000
        first, second, chat, path = self.pair(sources, rows, limit=1000)
        with self.assertRaises(ValueError) as expected: first.consume(chat, path, None, 2)
        adapter = B.BatchTokenAuditAdapter(self.tokenizer)
        with adapter.installed(), self.assertRaises(ValueError) as actual:
            adapter.consume(second, chat, path, None, 2)
        self.assertEqual(str(actual.exception), str(expected.exception))
        self.assertEqual(snapshot(second), snapshot(first))

    def test_outside_context_thread_fallback_and_clean_uninstall(self):
        _, rows = fixtures(1)
        adapter = B.BatchTokenAuditAdapter(self.tokenizer)
        expected = B._ORIGINAL_TOKENIZE(rows[0], self.tokenizer)
        results = []
        with adapter.installed():
            self.assertEqual(L.tokenize_assistant_only(rows[0], self.tokenizer), expected)
            thread = threading.Thread(target=lambda: results.append(L.tokenize_assistant_only(rows[0], self.tokenizer)))
            thread.start(); thread.join()
            self.assertEqual(results, [expected])
            self.assertEqual(adapter.stats['cache_hits'], 0)
            with self.assertRaises(RuntimeError): adapter.install()

    def test_payload_hash_remains_enforced(self):
        sources, rows = fixtures(1)
        first, second, chat, path = self.pair(sources, rows)
        adapter = B.BatchTokenAuditAdapter(self.tokenizer)
        path.write_bytes(path.read_bytes()+b'corrupt')
        with self.assertRaisesRegex(ValueError, 'payload byte/hash'): first.consume(chat, path, None)
        with adapter.installed(), self.assertRaisesRegex(ValueError, 'payload byte/hash'):
            adapter.consume(second, chat, path, None)
        self.assertEqual(snapshot(second), snapshot(first))

    def test_declared_row_count_remains_enforced(self):
        sources, rows = fixtures(1)
        first, second, chat, path = self.pair(sources, rows, declared_rows=len(rows)+1)
        adapter = B.BatchTokenAuditAdapter(self.tokenizer)
        with self.assertRaisesRegex(ValueError, 'Exact declared member row count') as expected:
            first.consume(chat, path, None, 2)
        with adapter.installed(), self.assertRaises(type(expected.exception)) as actual:
            adapter.consume(second, chat, path, None, 2)
        self.assertEqual(str(actual.exception), str(expected.exception))
        self.assertEqual(snapshot(second), snapshot(first))

    def test_buffered_stream_io_and_unicode_failures_preserve_committed_rows(self):
        original_payload = B._ORIGINAL_PAYLOAD
        faults = [lambda: OSError('synthetic stream I/O failure'),
                  lambda: UnicodeDecodeError('utf-8', b'\xff', 0, 1, 'synthetic bad byte')]
        for index, fault in enumerate(faults):
            with self.subTest(fault=index):
                self.root = Path(self.tmp.name) / str(index); self.root.mkdir()
                sources, rows = fixtures(3)
                first, second, chat, path = self.pair(sources, rows)
                @contextmanager
                def damaged_payload(e, p):
                    with original_payload(e, p) as stream:
                        def records():
                            for number, text in enumerate(stream):
                                if number == 5:
                                    raise fault()
                                yield text
                        yield records()
                adapter = B.BatchTokenAuditAdapter(self.tokenizer)
                with mock.patch.object(A, 'payload', damaged_payload), mock.patch.object(B, '_ORIGINAL_PAYLOAD', damaged_payload):
                    with self.assertRaises(Exception) as expected:
                        first.consume(chat, path, None, 2)
                    with adapter.installed(), self.assertRaises(type(expected.exception)) as actual:
                        adapter.consume(second, chat, path, None, 2)
                self.assertEqual(str(actual.exception), str(expected.exception))
                self.assertEqual(snapshot(second), snapshot(first))
                self.assertEqual(second.db.execute('SELECT next_line FROM members WHERE id=?',
                    (member_key(chat),)).fetchone(), (4,))
                self.assertEqual(adapter.stats['stream_error_buffered_rows'], 5)

    def test_actual_gzip_crc_and_utf8_damage_preserve_database_cursor(self):
        for name, kwargs in [('crc',dict(corrupt_trailer=True)),
                             ('utf8',dict(trailing_invalid_utf8=True))]:
            with self.subTest(damage=name):
                self.root = Path(self.tmp.name) / name; self.root.mkdir()
                sources, rows = fixtures(12)
                first, second, chat, path = self.pair(sources, rows, **kwargs)
                adapter = B.BatchTokenAuditAdapter(self.tokenizer)
                with self.assertRaises(Exception) as expected:
                    first.consume(chat, path, None, 2)
                with adapter.installed(), self.assertRaises(type(expected.exception)) as actual:
                    adapter.consume(second, chat, path, None, 2)
                self.assertEqual(str(actual.exception), str(expected.exception))
                self.assertEqual(snapshot(second), snapshot(first))
                self.assertGreater(adapter.stats['stream_error_buffered_rows'], 0)
                committed = second.db.execute('SELECT next_line FROM members WHERE id=?',
                    (member_key(chat),)).fetchone()[0]
                self.assertGreater(committed, 2)
                EVIDENCE['damaged_'+name] = dict(cursor=committed, error_type=type(actual.exception).__name__,
                    database_sha256=digest(snapshot(second)), stats=adapter.stats)

    def test_batch_backend_failures_and_partial_cache_use_original_rows(self):
        original_call = type(self.tokenizer).__call__
        for fault in ('template_ids', 'offsets', 'cardinality', 'partial_offset_index'):
            with self.subTest(fault=fault):
                self.root = Path(self.tmp.name) / fault; self.root.mkdir()
                sources, rows = fixtures(3)
                first, second, chat, path = self.pair(sources, rows)
                first.consume(chat, path, None, 2)
                def damaged(instance, text, *args, **kwargs):
                    batch = isinstance(text, list)
                    offsets = kwargs.get('return_offsets_mapping')
                    if batch and ((fault == 'template_ids' and not offsets) or (fault == 'offsets' and offsets)):
                        raise RuntimeError('synthetic batch-only backend failure')
                    result = original_call(instance, text, *args, **kwargs)
                    if batch and offsets and fault == 'cardinality': result['input_ids'] = []
                    if batch and offsets and fault == 'partial_offset_index': result['offset_mapping'] = result['offset_mapping'][:1]
                    return result
                adapter = B.BatchTokenAuditAdapter(self.tokenizer)
                with mock.patch.object(type(self.tokenizer), '__call__', damaged), adapter.installed():
                    adapter.consume(second, chat, path, None, 2)
                self.assertEqual(snapshot(second), snapshot(first))
                self.assertEqual(adapter.stats['cache_hits'], 0)
                self.assertEqual(adapter.stats['batch_prepare_fallbacks'], 1)
                self.assertEqual(adapter.stats['single_row_fallbacks'], len(rows))

    def test_batch_only_row_gate_mismatch_retries_original_scalar(self):
        sources, rows = fixtures(3)
        first, second, chat, path = self.pair(sources, rows)
        first.consume(chat, path, None, 2)
        original_call = type(self.tokenizer).__call__
        def damaged(instance, text, *args, **kwargs):
            result = original_call(instance, text, *args, **kwargs)
            if isinstance(text, list) and kwargs.get('return_offsets_mapping'):
                result['input_ids'][5] = result['input_ids'][5][:-1]
            return result
        adapter = B.BatchTokenAuditAdapter(self.tokenizer)
        with mock.patch.object(type(self.tokenizer), '__call__', damaged), adapter.installed():
            adapter.consume(second, chat, path, None, 2)
        self.assertEqual(snapshot(second), snapshot(first))
        self.assertEqual(adapter.stats['single_row_fallbacks'], 1)

    def test_render_failure_occurs_at_original_physical_commit_boundary(self):
        sources, rows = fixtures(3)
        rows[5]['messages'][2]['content'] = 'SYNTHETIC_RENDER_FAILURE'
        first, second, chat, path = self.pair(sources, rows)
        original_template = self.tokenizer.apply_chat_template
        def damaged(messages, *args, **kwargs):
            if (not kwargs.get('tokenize') and isinstance(messages[0], dict)
                    and any(message.get('content') == 'SYNTHETIC_RENDER_FAILURE' for message in messages)):
                raise RuntimeError('synthetic row rendering failure')
            return original_template(messages, *args, **kwargs)
        adapter = B.BatchTokenAuditAdapter(self.tokenizer)
        with mock.patch.object(self.tokenizer, 'apply_chat_template', damaged):
            with self.assertRaises(RuntimeError) as expected: first.consume(chat, path, None, 2)
            with adapter.installed(), self.assertRaises(type(expected.exception)) as actual:
                adapter.consume(second, chat, path, None, 2)
        self.assertEqual(str(actual.exception), str(expected.exception))
        self.assertEqual(snapshot(second), snapshot(first))
        self.assertEqual(second.db.execute('SELECT next_line FROM members WHERE id=?',
            (member_key(chat),)).fetchone(), (4,))
        self.assertEqual(adapter.stats['row_prepare_fallbacks'], 1)

    def test_duplicate_render_failure_keeps_original_short_circuit(self):
        sources, rows = fixtures(3)
        rows[0]['messages'][2]['content'] = 'SYNTHETIC_DUPLICATE_RENDER_FAILURE'
        rows.insert(5, deepcopy(rows[0]))
        first, second, chat, path = self.pair(sources, rows)
        for audit in (first, second): audit.consume(chat, path, 1, 1)
        original_template = self.tokenizer.apply_chat_template
        def damaged(messages, *args, **kwargs):
            if (not kwargs.get('tokenize') and isinstance(messages[0], dict)
                    and any(message.get('content') == 'SYNTHETIC_DUPLICATE_RENDER_FAILURE' for message in messages)):
                raise RuntimeError('duplicate must never render in original _chat')
            return original_template(messages, *args, **kwargs)
        adapter = B.BatchTokenAuditAdapter(self.tokenizer)
        with mock.patch.object(self.tokenizer, 'apply_chat_template', damaged):
            first.consume(chat, path, None, 2)
            with adapter.installed(): adapter.consume(second, chat, path, None, 2)
        self.assertEqual(snapshot(second), snapshot(first))
        self.assertEqual(second.report()['exact_duplicate_references'], 1)
        self.assertEqual(adapter.stats['row_prepare_fallbacks'], 1)

    def test_canonical_row_encoding_failure_keeps_original_hash_error_position(self):
        sources, rows = fixtures(3)
        rows[5]['metadata'] = '\ud800'
        texts = [json.dumps(row, ensure_ascii=True)+'\n' for row in rows]
        first, second, chat, path = self.pair(sources, rows, texts=texts)
        adapter = B.BatchTokenAuditAdapter(self.tokenizer)
        with self.assertRaises(UnicodeEncodeError) as expected: first.consume(chat, path, None, 2)
        with adapter.installed(), self.assertRaises(type(expected.exception)) as actual:
            adapter.consume(second, chat, path, None, 2)
        self.assertEqual(str(actual.exception), str(expected.exception))
        self.assertEqual(snapshot(second), snapshot(first))
        self.assertEqual(second.db.execute('SELECT next_line FROM members WHERE id=?',
            (member_key(chat),)).fetchone(), (4,))

    def test_exact_cache_key_includes_all_canonical_row_bytes(self):
        _, rows = fixtures(1)
        _, context = self.prepare(rows[:1])
        self.assertIn(B._row_bytes(json.loads(json.dumps(rows[0], ensure_ascii=True))), context.cache)
        changed = dict(rows[0], extra_metadata='different bytes')
        self.assertNotIn(B._row_bytes(changed), context.cache)


def benchmark(tokenizer):
    # Repeat exact short/long unicode fixtures, report measured wall time only.
    _, rows = fixtures(128)
    for i, row in enumerate(rows):
        if i % 8 == 0: row['messages'][2]['content'] += ' Kiểm tra phép tính và đơn vị. '*15
    B._ORIGINAL_TOKENIZE(rows[0], tokenizer)  # tokenizer/Jinja warmup
    start = time.perf_counter()
    expected = [B._ORIGINAL_TOKENIZE(row, tokenizer) for row in rows]
    original_seconds = time.perf_counter()-start
    results = {}
    for size in (128, 256):
        adapter = B.BatchTokenAuditAdapter(tokenizer, batch_size=size)
        context = B._Context(adapter, SimpleNamespace(limit=40960), 'benchmark', 0, None)
        start = time.perf_counter()
        actual = []
        for offset in range(0, len(rows), size):
            chunk = rows[offset:offset+size]
            items = [adapter._item(canonical(row)+'\n') for row in chunk]
            adapter._prepare(items, context)
            actual.extend(context.cache[B._row_bytes(row)] for row in chunk)
            context.cache.clear()
        seconds = time.perf_counter()-start
        if actual != expected: raise AssertionError('Benchmark exact outputs differ')
        results[str(size)] = dict(seconds=seconds, rows_per_second=len(rows)/seconds,
            speedup=original_seconds/seconds, stats=adapter.stats)
    return dict(rows=len(rows), fixture_sha256=digest(rows), exact_encoded_sha256=digest(expected),
        original_seconds=original_seconds, original_rows_per_second=len(rows)/original_seconds,
        batches=results, timing_scope='render + exact tokenization + original gates + bounded cache; CPU synthetic only')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    original_names = ('math_data_full_audit_v3.py', 'math_data_archive_audit.py', 'exhaustive_colab_loader.py')
    original_hashes = {name:file_hash(Path(__file__).parent/name) for name in original_names}
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(BatchAdapterTests)
    test_names = [test.id() for test in suite]
    runner = unittest.TextTestRunner(verbosity=2)
    start = time.perf_counter()
    result = runner.run(suite)
    test_seconds = time.perf_counter()-start
    if original_hashes != {name:file_hash(Path(__file__).parent/name) for name in original_names}:
        raise AssertionError('Original scanner/loader/payload files changed during QA')
    report = dict(schema='MathVisionKid.exact_batch_token_adapter_validation.v1',
        success=result.wasSuccessful(), tests_run=result.testsRun, test_names=test_names,
        tested_at_utc=datetime.now(timezone.utc).isoformat(), test_seconds=test_seconds,
        failures=[(str(test), error) for test, error in result.failures],
        errors=[(str(test), error) for test, error in result.errors],
        evidence=EVIDENCE, python=platform.python_version(),
        tokenizer_model=L.MODEL, tokenizer_revision=L.REVISION,
        transformers_version=__import__('transformers').__version__,
        tokenizer_files_sha256={p.name:file_hash(p) for p in PIN.iterdir() if p.name != 'config.json'},
        files_sha256={name:file_hash(Path(__file__).parent/name) for name in
            ('math_data_batch_token_audit.py','test_math_data_batch_token_audit.py',
             'math_data_full_audit_v3.py','math_data_archive_audit.py','exhaustive_colab_loader.py')},
        model_weights_loaded=False, training_started=False, protected_data_read=False,
        runtime_scanner_modified=False, fixtures='Fresh temporary synthetic train sources and chats only')
    report['original_files_before_and_after_sha256'] = original_hashes
    if result.wasSuccessful(): report['throughput'] = benchmark(BatchAdapterTests.tokenizer)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(success=report['success'], tests=report['tests_run'],
        throughput=report.get('throughput')), ensure_ascii=False))
    raise SystemExit(0 if result.wasSuccessful() else 1)
