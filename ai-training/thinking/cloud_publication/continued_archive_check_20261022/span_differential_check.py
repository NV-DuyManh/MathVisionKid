"""Bounded local span-size differential for V3 + batch adapter; synthetic rows only."""
from __future__ import annotations
import hashlib, json, platform, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
THINKING = ROOT / "thinking"
sys.path.insert(0, str(THINKING))

import exhaustive_colab_loader as L
import math_data_full_audit_v3 as V3
import math_data_batch_token_audit as B
from math_data_candidate_stream import build_recipe
from math_data_portable_resume import canonical, digest, file_hash
from test_math_data_batch_token_audit import fixtures, entry, snapshot

PIN = Path.home() / '.cache/huggingface/hub/models--Qwen--Qwen3-1.7B/snapshots' / L.REVISION


def run_spans(root: Path, label: str, sources, chats, span_rows: int, tokenizer):
    src, src_path = entry(root, 'span_sources', sources, 'candidate_source')
    chat, chat_path = entry(root, 'span_chats', chats, 'candidate_chat')
    recipe = build_recipe([dict(members=[src, chat])])
    audit = V3.FullArchiveAudit(root / f'{label}.sqlite', recipe, tokenizer)
    adapter = B.BatchTokenAuditAdapter(tokenizer, batch_size=256)
    try:
        source_result = audit.consume(src, src_path, max_rows=None, commit_every=256)
        spans = []
        with adapter.installed():
            while True:
                item = adapter.consume(audit, chat, chat_path, max_rows=span_rows, commit_every=256)
                spans.append(item)
                if item.get('complete') or item.get('already_complete'):
                    break
        report = audit.report()
        snap = snapshot(audit)
        return dict(payload_sha256=file_hash(chat_path), source_result=source_result, spans=spans, report=report,
                    snapshot=snap, snapshot_sha256=digest(snap),
                    report_sha256=digest(report), stats=dict(adapter.stats))
    finally:
        audit.close()


def run_malformed_boundary(root: Path, label: str, sources, chats, span_rows: int, tokenizer):
    case_root = root / label
    case_root.mkdir(parents=True)
    src, src_path = entry(case_root, 'boundary_sources', sources, 'candidate_source')
    malformed_text = ''.join(canonical(row)+'\n' for row in chats[:-1]) + '{malformed json\\n'
    chat, chat_path = entry(case_root, 'boundary_chats', chats, 'candidate_chat', texts=malformed_text)
    recipe = build_recipe([dict(members=[src, chat])])
    audit = V3.FullArchiveAudit(case_root / 'boundary.sqlite', recipe, tokenizer)
    adapter = B.BatchTokenAuditAdapter(tokenizer, batch_size=256)
    try:
        audit.consume(src, src_path, max_rows=None, commit_every=256)
        spans = 0
        failure = None
        with adapter.installed():
            while failure is None:
                try:
                    result = adapter.consume(audit, chat, chat_path, max_rows=span_rows, commit_every=256)
                    spans += 1
                    if result.get('complete') or result.get('already_complete'):
                        break
                except Exception as exc:
                    failure = {'type':type(exc).__name__, 'message':str(exc)}
        cursor = audit.db.execute('SELECT next_line,complete FROM members WHERE id=?',
                                  (V3.member_key(chat),)).fetchone()
        return {'span_rows':span_rows, 'spans_before_error':spans, 'failure':failure,
                'persisted_cursor':list(cursor) if cursor else None,
                'processed_rows':audit.report()['unique_chat_rows_processed'],
                'issues':audit.report()['issues']}
    finally:
        audit.close()


def main():
    started = time.monotonic()
    tokenizer = L.load_qwen_tokenizer(PIN)
    sources, chats = fixtures(17)
    assert len(chats) == 68
    # Same deterministic gzip payload bytes, member identity, recipe and 68 chat rows.
    with tempfile.TemporaryDirectory(prefix='span_differential_') as td:
        root = Path(td)
        small = run_spans(root, 'small_span', sources, chats, 17, tokenizer)
        large = run_spans(root, 'large_span', sources, chats, 68, tokenizer)
    exact_equal = all(small[k] == large[k] for k in ('source_result', 'report', 'snapshot', 'snapshot_sha256', 'report_sha256'))
    malformed_small = run_malformed_boundary(root, 'malformed_small', sources, chats, 17, tokenizer)
    malformed_large = run_malformed_boundary(root, 'malformed_large', sources, chats, 68, tokenizer)
    assert malformed_small['failure'] == malformed_large['failure']
    assert malformed_small['failure']['type'] == 'JSONDecodeError'
    assert malformed_small['persisted_cursor'] == [51, 0]
    assert malformed_large['persisted_cursor'] == [0, 0]
    assert exact_equal, 'span variants differed in completed audit state/report'
    assert len(small['spans']) == 5 and len(large['spans']) == 2
    assert small['report']['unique_chat_rows_processed'] == 68
    assert small['stats']['skipped_resume_lines'] == 170  # 17 + 34 + 51 + 68 after exact-bound final pause
    assert large['stats']['skipped_resume_lines'] == 68  # exact-bound final pause replays all 68 to prove EOF
    assert small['stats']['rows_batched'] == large['stats']['rows_batched'] == 68
    assert small['report']['issues'] == large['report']['issues'] == {}
    out = {
      'schema': 'mathvisionkid.synthetic_span_differential.v1',
      'declared_scope': 'Bounded local synthetic fixture only; not evidence that the full archive has been audited or that this exact speedup generalizes to Colab.',
      'environment': {'python': platform.python_version(), 'platform': platform.platform(),
                      'tokenizer_model': L.MODEL, 'tokenizer_revision': L.REVISION,
                      'tokenizer_path_basename': PIN.name, 'weights_loaded': False},
      'fixture': {'source_count': len(sources), 'chat_count': len(chats),
                  'source_and_chat_fixture_sha256': digest({'sources':sources,'chats':chats}),
                  'chat_payload_sha256': small['payload_sha256'],
                  'spans_compared': {'baseline_scaled_span_rows':17, 'candidate_scaled_span_rows':68}},
      'comparison': {'completed_state_exact': exact_equal,
                     'report_sha256_baseline':small['report_sha256'], 'report_sha256_candidate':large['report_sha256'],
                     'snapshot_sha256_baseline':small['snapshot_sha256'], 'snapshot_sha256_candidate':large['snapshot_sha256'],
                     'report':small['report'],
                     'baseline': {'span_count':len(small['spans']), 'skipped_resume_lines':small['stats']['skipped_resume_lines'],
                                  'rows_batched':small['stats']['rows_batched'], 'span_results':small['spans']},
                     'candidate': {'span_count':len(large['spans']), 'skipped_resume_lines':large['stats']['skipped_resume_lines'],
                                   'rows_batched':large['stats']['rows_batched'], 'span_results':large['spans']}},
      'malformed_row_boundary': {'same_error':malformed_small['failure']==malformed_large['failure'], 'expected_failure':malformed_small['failure'], 'baseline_17':malformed_small, 'candidate_68':malformed_large, 'interpretation':'Error location/type/message are identical. Persisted cursors differ because each bounded consume commits its successful span; failed-span work rolls back to that span’s start. Resume correctness depends on the existing cursor semantics, which remain unchanged.'},
      'wall_seconds': round(time.monotonic()-started, 3),
      'frozen_v3_and_adapter_modified': False,
      'colab_drive_or_corpus_accessed': False,
      'raw_eval_concept_or_pilot_data_read': False,
      'training_or_weights': False
    }
    output = Path(__file__).with_name('span_differential_check.json')
    output.write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'output':str(output), 'completed_state_exact':exact_equal,
                      'baseline_spans':len(small['spans']), 'candidate_spans':len(large['spans']),
                      'baseline_skips':small['stats']['skipped_resume_lines'],
                      'candidate_skips':large['stats']['skipped_resume_lines'],
                      'rows':small['report']['unique_chat_rows_processed']}, ensure_ascii=True))

if __name__ == '__main__': main()






