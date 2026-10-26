"""Owner requested save-and-pause; never interrupts a SQLite commit or upload."""
import hashlib,json,sqlite3,threading
from datetime import datetime,timezone

assert full_audit_worker.is_alive()
assert not globals().get('_owner_pause_requested',False)
_owner_pause_requested=True
owner_pause_requested_utc=datetime.now(timezone.utc).isoformat()
owner_pause_original_tokenize=batch_module._ORIGINAL_TOKENIZE

class OwnerRequestedDataOnlyPause(Exception):
    pass

def owner_pause_tokenize_gate(row,tokenizer,max_sequence_tokens=40960):
    if threading.current_thread().ident==full_audit_worker.ident and _owner_pause_requested:
        raise OwnerRequestedDataOnlyPause('Owner requested save and pause until next session; this is not a data QA finding.')
    return owner_pause_original_tokenize(row,tokenizer,max_sequence_tokens)

owner_pause_status={'state':'OWNER_PAUSE_REQUESTED_WAITING_FOR_VERIFIED_SAVE',
    'requested_utc':owner_pause_requested_utc,'training_started':False,
    'mechanism':'Stop before a later row token gate; original consume rolls back only the current uncommitted256-row transaction. Original worker saves and raw-verifies its complete portable checkpoint.',
    'data_qa_finding_created':False}

def write_owner_pause_status():
    (qa_dir/'owner_pause_receipt.json').write_text(json.dumps(owner_pause_status,ensure_ascii=False,indent=2))

def confirm_owner_pause_after_save():
    try:
        full_audit_worker.join()
        # The registered technical finalizer must not run acceptance on partial
        # rows. Keep its controlled-stop evidence before recording owner pause.
        final_metadata_thread.join(timeout=60)
        if final_metadata_thread.is_alive():
            raise RuntimeError('The finite metadata checker has not exited')
        if batch_module._ACTIVE or batch_module._OWNER is not None:
            raise RuntimeError('Audit adapter did not uninstall cleanly')
        batch_module._ORIGINAL_TOKENIZE=owner_pause_original_tokenize
        if batch_module.L.tokenize_assistant_only is owner_pause_tokenize_gate:
            batch_module.L.tokenize_assistant_only=owner_pause_original_tokenize
        if batch_module.L.tokenize_assistant_only is not owner_pause_original_tokenize:
            raise RuntimeError('Original tokenizer hook was not restored')
        raw_exit={k:full_audit_worker_state.get(k) for k in ['state','error_type','error','checkpoint_save_error']}
        if raw_exit['error_type']!='OwnerRequestedDataOnlyPause':
            raise RuntimeError('Worker stopped for a reason other than the requested pause')
        proof=full_audit_worker_state['checkpoint']
        if not proof.get('fresh_raw_readback_verified') or proof['observed_utc']<owner_pause_requested_utc:
            raise RuntimeError('No fresh raw-verified checkpoint after the owner pause request')
        snapshot=ROOT/'full_audit_v3_snapshot.sqlite'
        if snapshot.stat().st_size!=proof['bytes'] or file_digest(snapshot)!=proof['sha256']:
            raise RuntimeError('Portable snapshot differs from verified Drive checkpoint')
        with sqlite3.connect(V3_DB.as_uri()+'?mode=ro',uri=True) as a, sqlite3.connect(snapshot.as_uri()+'?mode=ro',uri=True) as b:
            cursors_a=a.execute('SELECT id,role,next_line,complete,expected_rows FROM members ORDER BY id').fetchall()
            cursors_b=b.execute('SELECT id,role,next_line,complete,expected_rows FROM members ORDER BY id').fetchall()
            issues_a=a.execute('SELECT * FROM issues ORDER BY member,line,kind,detail').fetchall()
            issues_b=b.execute('SELECT * FROM issues ORDER BY member,line,kind,detail').fetchall()
            if cursors_a!=cursors_b or issues_a!=issues_b:
                raise RuntimeError('Committed member cursor or issue rows differ from the saved snapshot')
            rows=a.execute('SELECT count(*) FROM samples').fetchone()[0]
            physical=a.execute('SELECT count(*) FROM occurrences').fetchone()[0]
            if rows!=proof['report_at_snapshot']['unique_chat_rows_processed'] or physical!=proof['report_at_snapshot']['physical_chat_occurrences_processed']:
                raise RuntimeError('Saved checkpoint does not include the final committed audit progress')
        a.close();b.close()
        metadata_path=qa_dir/'final_metadata_status.json'
        previous_metadata=json.loads(metadata_path.read_bytes()) if metadata_path.exists() else None
        owner_pause_status.update(state='PAUSED_BY_OWNER_AT_FRESH_RAW_VERIFIED_CHECKPOINT',
            verified_utc=datetime.now(timezone.utc).isoformat(),checkpoint=proof,
            unique_chat_rows_saved=rows,physical_chat_rows_saved=physical,
            member_cursors_equal_saved_snapshot=True,prior_issues_preserved=True,
            member_cursors_sha256=hashlib.sha256(json.dumps(cursors_a,separators=(',',':')).encode()).hexdigest(),
            tokenizer_hook_restored=True,raw_worker_exit_preserved=raw_exit,
            prior_final_metadata_status_preserved=previous_metadata,
            worker_alive=False,final_metadata_worker_alive=False,
            resume_policy='Restore this exact same-ID checkpoint and recipe identity. Do not rerun generation or append64. Re-register the finite final metadata check only after resuming the single worker.')
        full_audit_worker_state['owner_pause_receipt']=owner_pause_status
        full_audit_worker_state['state']='PAUSED_BY_OWNER_AT_FRESH_RAW_VERIFIED_CHECKPOINT'
        write_worker_status()
        metadata_path.write_text(json.dumps({'state':'PAUSED_BY_OWNER_AWAITING_RESUME',
            'owner_pause_requested_utc':owner_pause_requested_utc,'checkpoint_sha256':proof['sha256'],
            'unique_chat_rows_saved':rows,'prior_status_preserved':previous_metadata,
            'training_started':False},ensure_ascii=False,indent=2))
    except Exception as error:
        owner_pause_status.update(state='PAUSE_SAVE_NEEDS_ATTENTION',error_type=type(error).__name__,error=str(error))
    finally:
        write_owner_pause_status()

write_owner_pause_status()
owner_pause_confirmation_thread=threading.Thread(target=confirm_owner_pause_after_save,
    name='MathVisionKidOwnerRequestedPauseSave',daemon=True)
owner_pause_confirmation_thread.start()
batch_module._ORIGINAL_TOKENIZE=owner_pause_tokenize_gate
print(json.dumps({'owner_pause_requested':True,'state':owner_pause_status['state'],
    'not_safe_to_close_before_verification_message':True,'training_started':False}))
