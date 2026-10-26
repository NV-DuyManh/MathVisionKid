"""Local synthetic differential tests and bounded full-scanner benchmark."""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timezone
import hashlib, json, platform, sys, tempfile, time, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
THINKING = ROOT / 'thinking'
sys.path.insert(0, str(THINKING))
import math_data_batch_token_audit as B
from math_data_batch_token_audit import BatchTokenAuditAdapter as OriginalAdapter
from math_data_candidate_stream import build_recipe
from math_data_portable_resume import canonical, digest, file_hash
from onepass_batch_token_audit import OnePassBatchTokenAuditAdapter, api_provenance, prepare_official_onepass
import test_math_data_batch_token_audit as reference


class OnePassDifferentialTests(reference.BatchAdapterTests):
    def test_official_batch_calls_are_independent_and_untruncated(self):
        _, rows = reference.fixtures(2)
        original_call = type(self.tokenizer).__call__
        calls = []
        def observed(instance, text, *args, **kwargs):
            calls.append((isinstance(text, list), len(text) if isinstance(text, list) else None, dict(kwargs)))
            return original_call(instance, text, *args, **kwargs)
        adapter = OnePassBatchTokenAuditAdapter(self.tokenizer)
        items = [adapter._item(reference.canonical(row)+'\n') for row in rows]
        context = B._Context(adapter, SimpleNamespace(limit=40960), 'onepass', 0, None)
        with mock.patch.object(type(self.tokenizer), '__call__', observed):
            adapter._prepare(items, context)
        self.assertEqual(len(calls), 1)
        self.assertTrue(calls[0][0] and calls[0][1] == len(rows))
        self.assertTrue(calls[0][2].get('return_offsets_mapping'))
        self.assertFalse(calls[0][2].get('truncation', True))
        self.assertFalse(calls[0][2].get('padding', True))
        self.assertEqual(adapter.stats['onepass_official_encoding_calls'], 1)
        self.assertEqual(adapter.stats['onepass_render_verification_calls'], 1)
        expected = [B._ORIGINAL_TOKENIZE(row, self.tokenizer) for row in rows]
        actual = [context.cache[B._row_bytes(row)] for row in rows]
        self.assertEqual(actual, expected)

    def test_exact_template_token_mismatch_gate(self):
        _, rows = reference.fixtures(1)
        adapter = OnePassBatchTokenAuditAdapter(self.tokenizer)
        item = adapter._item(reference.canonical(rows[0])+'\n')
        full = self.tokenizer.apply_chat_template(rows[0]['messages'], tokenize=True,
                    add_generation_prompt=False, enable_thinking=False)
        offsets = self.tokenizer(item[4], add_special_tokens=False,
                    return_offsets_mapping=True, padding=False, truncation=False)
        full_ids = list(full['input_ids'])
        full_ids[0] += 1
        prepared = B._PreparedTokenizer(item, full_ids, offsets)
        with self.assertRaisesRegex(ValueError, 'template token mismatch'):
            B._ORIGINAL_TOKENIZE(rows[0], prepared)

    def test_batch_only_row_gate_mismatch_retries_original_scalar(self):
        # A single official encoding supplies both IDs and offsets, so a
        # cross-call-only injected discrepancy no longer exists. Verify its
        # combined outputs still match the exact scalar original on fixtures.
        _, rows = reference.fixtures(3)
        adapter = OnePassBatchTokenAuditAdapter(self.tokenizer)
        items = [adapter._item(reference.canonical(row)+'\n') for row in rows]
        context = B._Context(adapter, SimpleNamespace(limit=40960), 'onepass', 0, None)
        adapter._prepare(items, context)
        expected = [B._ORIGINAL_TOKENIZE(row, self.tokenizer) for row in rows]
        actual = [context.cache[B._row_bytes(row)] for row in rows]
        self.assertEqual(actual, expected)
        self.assertEqual(adapter.stats['single_row_fallbacks'], 0)
    def test_batch_backend_failures_and_partial_cache_use_original_rows(self):
        original_call = type(self.tokenizer).__call__
        for fault in ('offsets', 'cardinality', 'partial_offset_index'):
            with self.subTest(fault=fault):
                self.root = Path(self.tmp.name) / fault; self.root.mkdir()
                sources, rows = reference.fixtures(3)
                first, second, chat, path = self.pair(sources, rows)
                first.consume(chat, path, None, 2)
                def damaged(instance, text, *args, **kwargs):
                    if isinstance(text, list) and kwargs.get('return_offsets_mapping'):
                        if fault == 'offsets': raise RuntimeError('synthetic combined backend failure')
                        result = original_call(instance, text, *args, **kwargs)
                        if fault == 'cardinality': result['input_ids'] = []
                        if fault == 'partial_offset_index': result['offset_mapping'] = result['offset_mapping'][:1]
                        return result
                    return original_call(instance, text, *args, **kwargs)
                adapter = OnePassBatchTokenAuditAdapter(self.tokenizer)
                with mock.patch.object(type(self.tokenizer), '__call__', damaged), adapter.installed():
                    adapter.consume(second, chat, path, None, 2)
                self.assertEqual(reference.snapshot(second), reference.snapshot(first))
                self.assertEqual(adapter.stats['cache_hits'], 0)
                self.assertEqual(adapter.stats['batch_prepare_fallbacks'], 1)
                self.assertEqual(adapter.stats['single_row_fallbacks'], len(rows))


def scanner_run(root: Path, label: str, sources, chats, tokenizer, adapter_type):
    case_root = root / label
    case_root.mkdir()
    source, source_path = reference.entry(case_root, 'bench_sources', sources, 'candidate_source')
    chat, chat_path = reference.entry(case_root, 'bench_chats', chats, 'candidate_chat')
    recipe = build_recipe([dict(members=[source, chat])])
    audit = reference.V3.FullArchiveAudit(case_root / 'audit.sqlite', recipe, tokenizer)
    adapter = adapter_type(tokenizer, batch_size=256)
    try:
        audit.consume(source, source_path, max_rows=None, commit_every=256)
        started = time.perf_counter()
        with adapter.installed():
            result = adapter.consume(audit, chat, chat_path, max_rows=None, commit_every=256)
        elapsed = time.perf_counter() - started
        report = audit.report()
        snap = reference.snapshot(audit)
        return {'result': result, 'report_sha256': digest(report), 'snapshot_sha256': digest(snap),
                'report': report, 'snapshot': snap, 'stats': dict(adapter.stats), 'seconds': elapsed}
    finally:
        audit.close()


def run_benchmark(tokenizer):
    sources, chats = reference.fixtures(128)
    assert len(chats) == 512
    # Deterministic mixture of Unicode, combining marks, emoji, long targets,
    # and chat modes comes from the shared synthetic fixture generator.
    base_run = scanner_run(Path(tempfile.mkdtemp(prefix='onepass_benchmark_')), 'base',
                           sources, chats, tokenizer, OriginalAdapter)
    one_run = scanner_run(Path(tempfile.mkdtemp(prefix='onepass_benchmark_')), 'onepass',
                          sources, chats, tokenizer, OnePassBatchTokenAuditAdapter)
    parity = (base_run['result'] == one_run['result']
              and base_run['report'] == one_run['report']
              and base_run['snapshot'] == one_run['snapshot'])
    if not parity:
        raise AssertionError('512-row scanner report/cursor/snapshot differential')
    if base_run['stats']['rows_batched'] != 512 or one_run['stats']['rows_batched'] != 512:
        raise AssertionError('benchmark rows not fully batched')
    if one_run['stats']['onepass_official_encoding_calls'] != 2:
        raise AssertionError('expected two onepass encoding calls for two batches of 256')
    return {
        'rows': 512,
        'fixture_sha256': digest({'sources': sources, 'chats': chats}),
        'result_and_report_and_db_cursor_parity': parity,
        'report_sha256_baseline': base_run['report_sha256'],
        'report_sha256_onepass': one_run['report_sha256'],
        'snapshot_sha256_baseline': base_run['snapshot_sha256'],
        'snapshot_sha256_onepass': one_run['snapshot_sha256'],
        'baseline': {'seconds': base_run['seconds'], 'rows_per_second': 512/base_run['seconds'],
                     'stats': base_run['stats']},
        'onepass': {'seconds': one_run['seconds'], 'rows_per_second': 512/one_run['seconds'],
                    'stats': one_run['stats']},
        'timing_scope': '512 synthetic chat rows, local CPU, source index + exact V3 scanner parity; does not forecast Colab throughput.',
    }


class OnePassNoBatchRenderAdapter(OnePassBatchTokenAuditAdapter):
    """Benchmark-only variant relying on same pinned official template source."""
    def _prepare(self, items, context):
        prepare_official_onepass(self, items, context, verify_batch_render=False)


def representative_fixture():
    sources, chats = reference.fixtures(64)
    source_by_id = {row['sample_id']: row for row in sources}
    for i, source in enumerate(sources):
        unit = ('Trong bài toán lớp học, em cần đọc kỹ các dữ kiện, giữ đúng đơn vị đo, '
                'ghi rõ phép tính và giải thích vì sao kết quả phù hợp với câu hỏi. '
                'Các ký hiệu tiếng Việt, dấu phẩy thập phân, phân số, số âm, phép nhân ×, '
                'phép chia ÷, góc 90°, chiều dài 1,25 m và chữ cái có dấu được giữ nguyên. ')
        target_chars = 950 + (i % 16) * 30
        long_problem = (unit * (target_chars // len(unit) + 1))[:target_chars]
        source['problem'] = long_problem
    for row in chats:
        source = source_by_id[row['source_sample_id']]
        prompt = json.loads(row['messages'][1]['content'])
        prompt['problem'] = source['problem']
        row['messages'][1]['content'] = json.dumps(prompt, ensure_ascii=False)
        row['source_row_sha256'] = reference.V3.rawhash(canonical(source))
    lengths = [sum(len(message['content']) for message in row['messages']) for row in chats]
    if len(chats) != 256 or min(lengths) < 1000 or max(lengths) > 1800:
        raise AssertionError(f'representative fixture lengths out of range: {min(lengths)}..{max(lengths)}')
    return sources, chats, {'rows':len(chats), 'message_chars_min':min(lengths),
                            'message_chars_max':max(lengths), 'message_chars_median':sorted(lengths)[len(lengths)//2],
                            'fixture_sha256':digest({'sources':sources,'chats':chats})}


def run_representative_benchmark(tokenizer):
    sources, chats, fixture_meta = representative_fixture()
    variants = [('baseline_two_pass', OriginalAdapter),
                ('onepass_render_verified', OnePassBatchTokenAuditAdapter),
                ('onepass_no_extra_batch_render', OnePassNoBatchRenderAdapter)]
    observations = {name:[] for name,_ in variants}
    reference_hashes = None
    # Alternate variants to reduce warm-cache/order bias; every trial rebuilds
    # only small synthetic gzip/SQLite state in a temporary directory.
    for trial in range(3):
        order = variants if trial % 2 == 0 else list(reversed(variants))
        for name, adapter_type in order:
            with tempfile.TemporaryDirectory(prefix='representative_onepass_') as td:
                run = scanner_run(Path(td), name, sources, chats, tokenizer, adapter_type)
            hashes = (run['result'], run['report_sha256'], run['snapshot_sha256'])
            if reference_hashes is None:
                reference_hashes = hashes
            elif hashes != reference_hashes:
                raise AssertionError(f'{name} report/cursor/snapshot differs from baseline')
            observations[name].append({'seconds':run['seconds'], 'rows_per_second':256/run['seconds'],
                                       'report_sha256':run['report_sha256'],
                                       'snapshot_sha256':run['snapshot_sha256'],
                                       'max_sequence_tokens':run['report']['max_sequence_tokens'],
                                       'stats':run['stats']})
    summaries = {}
    for name, trials in observations.items():
        speeds = sorted(t['seconds'] for t in trials)
        summaries[name] = {'trials':trials, 'median_seconds':speeds[1],
                           'median_rows_per_second':256/speeds[1]}
    baseline = summaries['baseline_two_pass']['median_seconds']
    for name, _ in variants[1:]:
        summaries[name]['speedup_vs_baseline'] = baseline/summaries[name]['median_seconds']
    return {'fixture':fixture_meta, 'all_variant_reports_cursors_and_snapshots_equal':True,
            'variants':summaries,
            'timing_scope':'256 synthetic chat rows with 1,000–1,800 message characters each, local CPU; no full-corpus inference.'}


def main():
    import exhaustive_colab_loader as L
    from test_math_data_batch_token_audit import PIN
    tokenizer = L.load_qwen_tokenizer(PIN)
    original_adapter = B.BatchTokenAuditAdapter
    B.BatchTokenAuditAdapter = OnePassBatchTokenAuditAdapter
    try:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(OnePassDifferentialTests)
        names = [test.id() for test in suite]
        run = unittest.TextTestRunner(verbosity=2).run(suite)
    finally:
        B.BatchTokenAuditAdapter = original_adapter
    if not run.wasSuccessful():
        raise SystemExit(1)
    benchmark = run_benchmark(tokenizer)
    import transformers
    report = {
        'schema': 'MathVisionKid.derived_onepass_batch_adapter_validation.v1',
        'success': True,
        'tests_run': run.testsRun,
        'test_names': names,
        'tested_at_utc': datetime.now(timezone.utc).isoformat(),
        'python': platform.python_version(),
        'transformers_version': transformers.__version__,
        'tokenizer_model': L.MODEL,
        'tokenizer_revision': L.REVISION,
        'tokenizer_files_sha256': {p.name:file_hash(p) for p in PIN.iterdir() if p.name != 'config.json'},
        'derived_adapter_sha256': file_hash(Path(__file__).with_name('onepass_batch_token_audit.py')),
        'api_provenance': api_provenance(tokenizer),
        'baseline_adapter_sha256': file_hash(THINKING/'math_data_batch_token_audit.py'),
        'frozen_auditor_sha256': file_hash(THINKING/'math_data_full_audit_v3.py'),
        'benchmark': benchmark,
        'representative_benchmark': run_representative_benchmark(tokenizer),
        'fixture_coverage': ['Unicode + combining marks + emoji', 'special tokens and assistant boundary',
                             'exact/over sequence limits', 'invalid JSON and gzip/UTF-8 errors',
                             'source linkage, split and duplicate behavior', '256-row batches'],
        'g2_256_chat_fixture': 'Unavailable as a bounded local synthetic fixture; did not read archived/raw G2 content.',
        'runtime_or_drive_touched': False,
        'raw_eval_concept_or_pilot_rows_read': False,
        'training_started': False,
        'model_weights_loaded': False,
        'provenance_note': 'The two independent tokenizer encodings in the prior adapter are replaced by one official apply_chat_template encoding that returns both IDs and offsets. Prefix/full rendered-string checks and original row gates remain. This is a derived adapter experiment; no frozen scanner/adapter modification or live-worker install was performed.',
    }
    output = Path(__file__).with_name('onepass_batch_token_audit_validation.json')
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'success':True,'tests':run.testsRun,'benchmark':benchmark,
                      'output':str(output)},ensure_ascii=True))

if __name__ == '__main__': main()
