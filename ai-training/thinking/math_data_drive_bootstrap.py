"""Account-neutral, data-only Colab bootstrap over fixed Drive IDs and hashes.

No training, weights, sharing edits or writes to Drive. Payloads are cached only
in the caller's runtime directory; this module is not executed on the PC.
"""
from collections.abc import Mapping
from pathlib import Path
import hashlib,io,json,zipfile

STATE_ID='1TLoQIbrRVmgsg-2uiUujCfM3HrK62Yme'
PROGRESS_ID='1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX'
CODE_FILES=('exhaustive_colab_loader.py','math_data_portable_resume.py','math_data_archive_audit.py','math_data_candidate_stream.py')
def sha(data):return hashlib.sha256(data).hexdigest()
def verify(data,ref):
    if len(data)!=ref['bytes'] or sha(data)!=ref['sha256']:raise ValueError('pinned bytes/SHA256 mismatch')
    return data

class GoogleDriveReader:
    def __init__(self,service):self.service=service
    def read(self,file_id,max_bytes):
        from googleapiclient.http import MediaIoBaseDownload
        meta=self.service.files().get(fileId=file_id,fields='id,size,mimeType',supportsAllDrives=True).execute()
        size=int(meta.get('size',-1))
        if size<0 or size>max_bytes:raise ValueError('Drive raw size exceeds bounded request')
        output=io.BytesIO();down=MediaIoBaseDownload(output,self.service.files().get_media(fileId=file_id,supportsAllDrives=True),chunksize=4*1024*1024)
        done=False
        while not done:
            _,done=down.next_chunk(num_retries=3)
            if output.tell()>max_bytes:raise ValueError('download exceeds bounded request')
        raw=output.getvalue()
        if len(raw)!=size:raise ValueError('Drive raw size changed during download')
        return raw

def latest_controls(reader):
    """Mutable STATE read twice; recipe itself is pinned by its exact hash."""
    before=reader.read(STATE_ID,16*1024*1024);state=json.loads(before)
    pointer=state['latest_all_data_union_recipe']
    if pointer['progress_id']!=PROGRESS_ID:raise ValueError('unexpected progress control ID')
    member=pointer['member']
    if not isinstance(member,str) or member.startswith('/') or '..' in Path(member).parts:raise ValueError('unsafe recipe member')
    raw=reader.read(PROGRESS_ID,128*1024*1024)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if archive.namelist().count(member)!=1:raise ValueError('missing/ambiguous latest union recipe')
        data=archive.read(member)
    if sha(data)!=pointer['sha256']:raise ValueError('STATE recipe hash differs from PROGRESS')
    recipe=json.loads(data)
    if recipe.get('pending_discovery'):raise ValueError('unresolved declared supplements; refusing partial data')
    if reader.read(STATE_ID,16*1024*1024)!=before:raise ValueError('STATE changed during read; resume from latest controls')
    if state.get('training_started'):raise ValueError('unexpected training-started state for data-only notebook')
    return state,recipe,pointer

def bootstrap_code(reader,state,directory):
    """Load exact code members from latest accepted bundle; no archive extractall."""
    runs=[r for r in state.get('sgk_finish_runs',[]) if r.get('bundle')]
    if not runs:raise ValueError('no explicit accepted code bundle')
    run=runs[-1];ref=run['bundle'];fid=ref.get('id',ref.get('file_id'))
    if not fid:raise ValueError('bundle file ID required')
    raw=verify(reader.read(fid,ref['bytes']),ref)
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    receipts=[]
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if len(archive.namelist())!=len(set(archive.namelist())):raise ValueError('duplicate bundle member')
        manifest=json.loads(archive.read('manifest.json'))
        for name in CODE_FILES:
            path='code/'+name;pin=manifest['members'].get(path)
            if not pin:raise ValueError('latest bundle lacks candidate reader dependency: '+name)
            data=verify(archive.read(path),pin)
            (directory/name).write_bytes(data);receipts.append(dict(member=path,sha256=sha(data),bytes=len(data)))
    return dict(bundle_id=fid,bundle_sha256=ref['sha256'],code_members=receipts,training_started=False)

class LazyDriveCache(Mapping):
    """One hash-verified payload cached at a time in ephemeral Colab storage.

    source/chat members remain inside their archives. Checkpoints are separate
    and never removed by cache eviction. No files are created on Drive.
    """
    def __init__(self,reader,recipe,directory):
        self.reader=reader;self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True)
        self.artifacts=recipe['artifacts'];self.lookup={};self.current=None
        for digest,ref in self.artifacts.items():
            if digest!=ref['sha256'] or not ref.get('file_ids'):raise ValueError('hash and existing Drive ID required')
            self.lookup[digest]=digest
            for fid in ref['file_ids']:self.lookup[fid]=digest
    def __iter__(self):return iter(self.lookup)
    def __len__(self):return len(self.lookup)
    def __getitem__(self,key):
        digest=self.lookup[key];ref=self.artifacts[digest]
        if self.current and self.current[0]==digest:
            path=self.current[1]
            if path.stat().st_size!=ref['bytes'] or sha(path.read_bytes())!=digest:raise ValueError('cached payload changed')
            return path
        data=verify(self.reader.read(ref['file_ids'][0],ref['bytes']),ref)
        suffix='.gz' if any(n.endswith('.gz') for n in ref.get('file_names',[])) else '.zip'
        dest=self.directory/(digest+suffix);dest.write_bytes(data)
        if self.current:
            old=self.current[1]
            if old.parent.resolve()!=self.directory.resolve():raise ValueError('cache deletion escaped runtime directory')
            old.unlink()
        self.current=(digest,dest)
        return dest

def scope_receipt(state,recipe,pointer):
    return dict(accepted_cases=state['accepted_cases'],declared_candidate_chat_rows=state['training_chat_rows'],payload_references=len(recipe['artifacts']),chat_members=len(recipe['chat_members']),recipe_sha256=pointer['sha256'],historical_train_only_total_verified=False,full_archive_token_split_audit_complete=False,TRAINING_DATASET_READY=False,training_started=False,selection='ALL_DECLARED_CANDIDATE_MEMBERS_NO_BALANCED_SUBSET',runtime_accounts='Authenticate any account with access to the same existing IDs; no credentials in dataset')
