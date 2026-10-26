# Continue read-only verification of the already raw-hash-verified snapshot.
assert not restore_thread.is_alive()
assert resume_status['state']=='RESTORE_STOPPED_WITH_EVIDENCE'
assert checkpoint_prefetch_status['state']=='RUNTIME_SNAPSHOT_HASH_REVERIFIED_READONLY'
assert checkpoint_prefetch_status['sha256']==EXPECTED_SHA
resume_status['prior_restore_exit_preserved']={'state':resume_status['state'],'error_type':resume_status.get('error_type'),'error':resume_status.get('error'),'reason':'Incorrect materialized cursor count assumption: actual225 of251 declared members, exact saved cursor digest matches'}
resume_status.pop('error_type',None);resume_status.pop('error',None)
with sqlite3.connect(V3_DB.as_uri()+'?mode=ro',uri=True) as db:
    assert db.execute('PRAGMA quick_check').fetchone()==('ok',)
    assert db.execute('SELECT identity,sequence_limit FROM config').fetchone()==(V3_ID,40960)
    cursors=db.execute('SELECT id,role,next_line,complete,expected_rows FROM members ORDER BY id').fetchall()
    declared={batch_module.member_key(e):e for e in recipe_all['source_members']+recipe_all['chat_members']}
    # Unstarted members have no materialized cursor in this partial DB.
    assert len(cursors)==225 and len(declared)==251
    for key,role,line,complete,total in cursors:
        e=declared[key]
        assert role==e['role'] and total==e['rows'] and 0<=line<=total
        if complete: assert line==total
    cursor_hash=hashlib.sha256(json.dumps(cursors,separators=(',',':')).encode()).hexdigest()
    assert cursor_hash=='7b164f0f65c91c220d91509b4db819b98e25aca523a1ca21094c696832d4f3fc'
    assert sum(r[3] for r in cursors)==224
    assert db.execute('SELECT count(*) FROM samples').fetchone()[0]==4427328
    assert db.execute('SELECT count(*) FROM occurrences').fetchone()[0]==4427328
    assert db.execute('SELECT count(*) FROM source_versions').fetchone()[0]==1629906
    issues=db.execute('SELECT member,line,kind,detail FROM issues').fetchall()
    assert issues==[('79765b8281ff64675b4e3826c07b003237875a98d67e898f22f2a4c1f687b0d1',1,'SOURCE_SPLIT_MISSING_OR_UNKNOWN','exhaustive_v1_div_1563_43')]
    expected_indexes={'mvk_report_source_label_id_hash','mvk_report_sample_link_split_case_hash','mvk_report_sample_hash_origin'}
    indexes={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='index'")}
    assert expected_indexes<=indexes
probe_receipt=dict(state='EXISTING_V3_CHECKPOINT_RAW_VERIFIED_READONLY',
    observed_utc=datetime.now(timezone.utc).isoformat(),checkpoint_id=EXISTING_V3_ID,
    checkpoint_bytes=EXPECTED_BYTES,checkpoint_sha256=EXPECTED_SHA,
    fresh_raw_readback_verified=True,remote_metadata_unchanged_during_restore=True,
    audit_identity=V3_ID,recipe_sha256=pointer_all['sha256'],
    member_cursors_sha256=cursor_hash,source_versions_indexed=1629906,
    unique_chat_rows_processed=4427328,physical_chat_occurrences_processed=4427328,
    members_complete=224,members_expected=251,prior_issues_preserved=True,
    query_indexes_preserved=True,checkpoint_mutated=False,training_started=False)
(resume_dir/'restore_readonly_receipt.json').write_text(json.dumps(probe_receipt,indent=2))
resume_status.update(state='CHECKPOINT_VERIFIED_LOADING_PINNED_TOKENIZER_ONLY',restore_receipt=probe_receipt)
write_resume_status()
from exhaustive_colab_loader import load_qwen_tokenizer
tokenizer=load_qwen_tokenizer()
resume_status.update(state='RESTORED_READY_FOR_SINGLE_WORKER',completed_utc=datetime.now(timezone.utc).isoformat())
write_resume_status()
print(json.dumps(resume_status,ensure_ascii=False))
