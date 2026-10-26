"""Restore the exact owner-paused checkpoint in Colab only; no generation."""
import hashlib, importlib, io, json, os, shutil, sqlite3, threading, time, zipfile
from datetime import datetime, timezone
from pathlib import Path
from googleapiclient.http import MediaIoBaseDownload, build_http
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.discovery import build

assert os.environ.get('COLAB_GPU', '0') in ('0', '')
assert ROOT == Path('/content/mathvisionkid_data_only')
assert not any(t.is_alive() and t.name.startswith('MathVisionKid') for t in threading.enumerate())
EXISTING_V3_ID = '16Q9ft9xhcioconk-5zpxmdRv1ZDNxqFI'
V3_ID = 'f0332df91020ace0fc48d88491fe97364d08826458d08c71ba4ec60524e25863'
EXPECTED_SHA = '3c7cb05061c0040812111a6bb73a0709cc59a244493dc135a3b95aa389bf0648'
EXPECTED_BYTES = 7083466752
assert recipe_pointer['sha256'] == '1bb69c394c7eaaea7034125c6b3361eebbbe0d77e0715a8454331fbe7cee3ff8'
assert len(recipe['source_members']) == 219 and len(recipe['chat_members']) == 32
assert state['owner_requested_pause']['checkpoint']['sha256'] == EXPECTED_SHA
assert state['owner_requested_pause']['checkpoint']['bytes'] == EXPECTED_BYTES
recipe_all = recipe
pointer_all = recipe_pointer
qa_dir = ROOT/'continued_archive_check_20261022'
qa_dir.mkdir(parents=True, exist_ok=True)
resume_dir = ROOT/'owner_resume_20261023'
resume_dir.mkdir(exist_ok=True)
RESTORED_V3_DB = ROOT/('owner_resume_'+EXPECTED_SHA[:16]+'.sqlite')
V3_DB = RESTORED_V3_DB
assert not V3_DB.exists(), 'Existing runtime checkpoint must be inspected, not overwritten'
assert shutil.disk_usage(ROOT).free > 3*EXPECTED_BYTES+1024**3

def g2_connected_api():
    # Standard build_http preserves resumable upload 308 handling.
    return build('drive', 'v3', http=AuthorizedHttp(credentials, http=build_http()), cache_discovery=False)

def file_digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8*1024*1024), b''): h.update(block)
    return h.hexdigest()

resume_status = dict(state='RESTORE_REGISTERED', owner_resume_instruction='tiếp tục',
    registered_utc=datetime.now(timezone.utc).isoformat(), checkpoint_id=EXISTING_V3_ID,
    expected_bytes=EXPECTED_BYTES, expected_sha256=EXPECTED_SHA, downloaded_bytes=0,
    training_started=False, gpu_used=False, model_weights_loaded=False, new_cases=0, new_chats=0)

def write_resume_status():
    temporary = resume_dir/'resume_status.writing'
    temporary.write_text(json.dumps(resume_status, ensure_ascii=False, indent=2))
    temporary.replace(resume_dir/'resume_status.json')

def restore_once():
    global audit_v3, batch_module, meta_before, meta_after, probe_receipt, tokenizer
    try:
        api = g2_connected_api()
        rd = GoogleDriveReader(api)
        raw = rd.read('1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX', 128*1024*1024)
        pins = {
            'data_resume_20261022/code/math_data_full_audit_v3.py':'02431da433060a6574127f9a8e14d90cabffe85d8d0150c3b2a331dc15b4be1f',
            'data_resume_20261022/code/math_data_primary782_bindings_v3.py':'4d75e90c07eecccf7571d68015dda16e85a690e7ee2379b28d517d201472580b',
            'audit_finish_20261022/math_data_batch_token_audit.py':'8d978eceeabebda9103ae23a16c23beab5b8cf5f2248984eda0b584facbedf92',
        }
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            assert hashlib.sha256(archive.read(pointer_all['member'])).hexdigest() == pointer_all['sha256']
            for member, pin in pins.items():
                data = archive.read(member)
                assert hashlib.sha256(data).hexdigest() == pin
                (ROOT/'code'/member.rsplit('/',1)[-1]).write_bytes(data)
        importlib.invalidate_caches()
        audit_v3 = importlib.import_module('math_data_full_audit_v3')
        batch_module = importlib.import_module('math_data_batch_token_audit')
        assert audit_v3.plan_identity(recipe_all) == V3_ID
        fields = 'id,size,appProperties,modifiedTime,version'
        meta_before = api.files().get(fileId=EXISTING_V3_ID, fields=fields, supportsAllDrives=True).execute()
        assert int(meta_before['size']) == EXPECTED_BYTES
        assert meta_before['appProperties']['data_sha256'] == EXPECTED_SHA
        assert meta_before['appProperties']['recipe_identity'] == V3_ID
        resume_status.update(state='RESTORING_EXACT_DRIVE_CHECKPOINT_TO_COLAB_ONLY')
        write_resume_status()
        with V3_DB.open('xb') as target:
            class Sink:
                def __init__(self): self.hasher=hashlib.sha256(); self.size=0
                def write(self,data):
                    count=target.write(data); self.hasher.update(data); self.size+=count
                    resume_status['downloaded_bytes']=self.size
                    write_resume_status()
                    return count
            sink=Sink()
            download=MediaIoBaseDownload(sink,api.files().get_media(fileId=EXISTING_V3_ID,supportsAllDrives=True),chunksize=64*1024*1024)
            done=False
            while not done: _,done=download.next_chunk(num_retries=3)
        assert sink.size==EXPECTED_BYTES and sink.hasher.hexdigest()==EXPECTED_SHA
        meta_after=api.files().get(fileId=EXISTING_V3_ID,fields=fields,supportsAllDrives=True).execute()
        assert meta_before==meta_after, 'Remote checkpoint changed during restore'
        resume_status.update(state='VERIFYING_RESTORED_DATABASE_READONLY')
        write_resume_status()
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
    except Exception as error:
        resume_status.update(state='RESTORE_STOPPED_WITH_EVIDENCE',error_type=type(error).__name__,error=str(error))
    finally: write_resume_status()

write_resume_status()
restore_thread=threading.Thread(target=restore_once,name='MathVisionKidExactPausedCheckpointRestore',daemon=True)
restore_thread.start()
print(json.dumps(resume_status,ensure_ascii=False))
