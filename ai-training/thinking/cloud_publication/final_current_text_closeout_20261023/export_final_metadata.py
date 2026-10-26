"""Run only in Colab after the one scanner and finalizer have both exited.

Export a bounded metadata archive through MCP. Never export SQLite or corpus
members, and never create a Drive file or start training.
"""
import base64
import hashlib
import io
import json
import zipfile

assert not full_audit_worker.is_alive()
assert not final_metadata_thread.is_alive()
assert full_audit_worker_state['state'] == 'AUDIT_FINISHED_WITH_FINDINGS'
assert full_audit_worker_state['report']['unique_chat_rows_processed'] == 6502392
assert full_audit_worker_state['checkpoint']['fresh_raw_readback_verified'] is True
_final_state = json.loads((qa_dir/'final_metadata_status.json').read_bytes())
assert _final_state['state'] == 'FINAL_TEXT_TECHNICAL_EVIDENCE_COMPLETE_PENDING_CONTROL_PUBLICATION'

_export_paths = [
    qa_dir/name for name in (
        'final_metadata_status.json',
        'final_raw_v3_report_preserved.json',
        'final_candidate_chat_technical_adjudication.json',
        'final_current_text_candidate_manifest.json',
        'final_antijoin_execution.json',
        'final_source_chat_antijoin.json',
    )
] + [
    resume_dir/name for name in (
        'source_index_ledger_receipt.json', 'read_cache_receipt.json',
        'status_report_cache_receipt.json',
    )
]
_status_usage = {
    'registration': globals().get('status_cache_receipt'),
    'final_usage': dict(globals()['_status_report_cache'].metadata)
        if '_status_report_cache' in globals() else None,
    'scope': 'Status-report cache usage only; checkpoint/final/error reports always original fresh.',
    'training_started': False,
}
_usage_path = resume_dir/'status_report_cache_final_usage.json'
_usage_path.write_text(json.dumps(_status_usage, ensure_ascii=False, indent=2), encoding='utf8')
_export_paths.append(_usage_path)
_stream = io.BytesIO()
_metadata_files = []
with zipfile.ZipFile(_stream, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as _archive:
    for _path in _export_paths:
        assert _path.parent in (qa_dir, resume_dir)
        assert _path.suffix == '.json' and _path.is_file()
        _data = _path.read_bytes()
        assert len(_data) <= 24*1024*1024
        json.loads(_data)
        _archive.writestr(_path.name, _data)
        _metadata_files.append({'name':_path.name, 'bytes':len(_data),
                                'sha256':hashlib.sha256(_data).hexdigest()})
_export_bytes = _stream.getvalue()
assert len(_export_bytes) <= 4*1024*1024
assert sum(x['bytes'] for x in _metadata_files) <= 32*1024*1024
print(json.dumps({'schema':'MathVisionKid.bounded_final_metadata_export.v1',
    'files':_metadata_files, 'zip_bytes':len(_export_bytes),
    'zip_sha256':hashlib.sha256(_export_bytes).hexdigest(),
    'sqlite_or_corpus_exported':False, 'training_started':False,
    'zip_b64':base64.b64encode(_export_bytes).decode('ascii')}))
