"""CPU-only corrective-run Drive publisher; definitions have no network effects.

Runtime entry: start_publisher(credentials=repair_credentials), or supply an
api_factory that builds a new Drive client inside the publisher thread. Never
share the notebook's existing Drive HTTP client across threads.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import threading
import time
import traceback
import zipfile
from datetime import datetime, timezone

ROOT = Path('/content/mathvisionkid_corrective_5h_20261024')
PARENT = '19ZxkfKVIggdcbSfsAdCtG1ibfJ0CRN3n'
FOLDER_NAME = 'MathVisionKid_CORRECTIVE_5H_20261024'
FOLDER_MIME = 'application/vnd.google-apps.folder'
SCHEMA = 'MathVisionKid.corrective5h_publication.v1'
_START_LOCK = threading.Lock()
_THREAD_NAME = 'MathVisionKidCorrective5hDrivePublisher'


class IntegrityError(ValueError):
    """Fail closed; never replace a conflicting immutable artifact."""


class SnapshotBusyError(RuntimeError):
    """A mutable file can be retried on the next publication tick."""


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.publisher_pending')
    tmp.write_bytes(json_bytes(value))
    os.replace(tmp, path)


def contained_file(parent, relative):
    rel = PurePosixPath(relative)
    if not relative or rel.is_absolute() or '..' in rel.parts or '\\' in relative:
        raise IntegrityError('Unsafe manifest path: ' + str(relative))
    path = Path(parent).joinpath(*rel.parts)
    if not path.resolve().is_relative_to(Path(parent).resolve()) or path.is_symlink():
        raise IntegrityError('Manifest path escapes its generation')
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def snapshot_file(source, dest, attempts=3):
    """Hash exactly the snapshot uploaded, including concurrently replaced JSON."""
    source, dest = Path(source), Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(attempts):
        before = source.stat()
        shutil.copyfile(source, dest)
        after = source.stat()
        if (before.st_size, before.st_mtime_ns, before.st_ino) == (after.st_size, after.st_mtime_ns, after.st_ino):
            return {'bytes': dest.stat().st_size, 'sha256': sha(dest)}
    raise SnapshotBusyError('Source repeatedly changed while taking snapshot: ' + source.name)


def package_generation(generation, work):
    """Reconstruct and verify an immutable generation, once per manifest digest."""
    generation, work = Path(generation), Path(work)
    manifest_path = generation / 'generation_manifest.json'
    raw = manifest_path.read_bytes()
    manifest = json.loads(raw)
    if manifest.get('complete') is not True or not isinstance(manifest.get('files'), dict) or not manifest['files']:
        raise IntegrityError('Incomplete or empty generation manifest')
    step, rows = manifest.get('step'), manifest.get('rows_done', manifest.get('rows'))
    if type(step) is not int or type(rows) is not int or min(step, rows) < 0:
        raise IntegrityError('Generation step/rows must be nonnegative integers')
    digest = hashlib.sha256(raw).hexdigest()
    work.mkdir(parents=True, exist_ok=True)
    dest = work / f'checkpoint_step_{step:06d}_rows_{rows:08d}_{digest[:16]}.zip'
    expected = manifest['files']
    sizes = manifest.get('file_bytes', {})
    for name, h in expected.items():
        file = contained_file(generation, name)
        if not isinstance(h, str) or len(h) != 64 or sha(file) != h:
            raise IntegrityError('Generation member hash mismatch: ' + name)
        if name in sizes and file.stat().st_size != sizes[name]:
            raise IntegrityError('Generation member byte count mismatch: ' + name)
    if not dest.exists():
        tmp = dest.with_suffix('.zip.publisher_pending')
        with zipfile.ZipFile(tmp, 'w', compression=zipfile.ZIP_STORED) as archive:
            for name in sorted(expected):
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.external_attr = 0o600 << 16
                with contained_file(generation, name).open('rb') as inp, archive.open(info, 'w', force_zip64=True) as target:
                    shutil.copyfileobj(inp, target, 4 * 1024 * 1024)
            archive.writestr(zipfile.ZipInfo('generation_manifest.json', (1980, 1, 1, 0, 0, 0)), raw)
        os.replace(tmp, dest)
    with zipfile.ZipFile(dest) as archive:
        if set(archive.namelist()) != set(expected) | {'generation_manifest.json'}:
            raise IntegrityError('Checkpoint ZIP member set differs from manifest')
        if archive.read('generation_manifest.json') != raw:
            raise IntegrityError('Checkpoint ZIP manifest differs')
        for name, h in expected.items():
            checker = hashlib.sha256()
            with archive.open(name) as stream:
                for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
                    checker.update(chunk)
            if checker.hexdigest() != h:
                raise IntegrityError('Checkpoint ZIP member hash mismatch: ' + name)
    if manifest_path.read_bytes() != raw:
        raise IntegrityError('Generation manifest changed during packaging')
    return dest, {'step': step, 'rows_done': rows, 'manifest_sha256': digest, 'generation': generation.name}


class DriveStore:
    """All requests use one client and one thread, including fresh raw readback."""
    def __init__(self, api, *, parent=PARENT, folder_name=FOLDER_NAME, sleep=time.sleep, clock=time.monotonic):
        self.api, self.parent, self.folder_name = api, parent, folder_name
        self.sleep, self.clock, self.last_request = sleep, clock, None
        self.folder = None

    def request(self, factory):
        for attempt in range(5):
            if self.last_request is not None:
                self.sleep(max(0, 1.25 - (self.clock() - self.last_request)))
            self.last_request = self.clock()
            try:
                return factory().execute(num_retries=0)
            except Exception as exc:
                status = getattr(getattr(exc, 'resp', None), 'status', None)
                msg = str(exc)
                quota = status == 429 or (status == 403 and any(x in msg for x in ('rateLimitExceeded', 'userRateLimitExceeded', 'quotaExceeded')))
                transient = status in (500, 502, 503, 504) or isinstance(exc, (TimeoutError, ConnectionError, OSError))
                if attempt == 4 or not (quota or transient):
                    raise
                self.sleep(60 if quota else min(60, 2 ** (attempt + 1)))

    def metadata(self, file_id):
        return self.request(lambda: self.api.files().get(fileId=file_id, fields='id,name,mimeType,parents,trashed,size'))

    def create(self, body, media_factory=None):
        # A caller-supplied Drive ID makes retries idempotent even if the first
        # create succeeded remotely but its response was lost in transit.
        file_id = self.request(lambda: self.api.files().generateIds(count=1, space='drive', type='files'))['ids'][0]
        body = dict(body, id=file_id)
        def request():
            kwargs = {'body': body, 'fields': 'id'}
            if media_factory is not None:
                kwargs['media_body'] = media_factory()
            return self.api.files().create(**kwargs)
        try:
            return self.request(request)
        except Exception as exc:
            if getattr(getattr(exc, 'resp', None), 'status', None) != 409:
                raise
            meta = self.metadata(file_id)
            if meta.get('name') != body['name'] or set(meta.get('parents', [])) != set(body.get('parents', [])):
                raise IntegrityError('Reserved Drive ID has conflicting metadata') from exc
            return {'id': file_id}

    def find(self, parent, name):
        escaped = name.replace('\\', '\\\\').replace("'", "\\'")
        token, files = None, []
        while True:
            result = self.request(lambda: self.api.files().list(q=f"'{parent}' in parents and name='{escaped}' and trashed=false", pageSize=100, pageToken=token, fields='nextPageToken,files(id,name,mimeType,parents,size,trashed)'))
            files.extend(result.get('files', []))
            token = result.get('nextPageToken')
            if not token:
                return files

    def ensure_folder(self):
        parent = self.metadata(self.parent)
        if parent.get('id') != self.parent or parent.get('mimeType') != FOLDER_MIME or parent.get('trashed'):
            raise IntegrityError('Expected publication parent is not an active folder')
        found = self.find(self.parent, self.folder_name)
        if len(found) > 1:
            raise IntegrityError('Duplicate stable run folders; refusing ambiguous publication')
        if found:
            file_id = found[0]['id']
        else:
            file_id = self.create({'name': self.folder_name, 'mimeType': FOLDER_MIME, 'parents': [self.parent]})['id']
        meta = self.metadata(file_id)
        if meta.get('name') != self.folder_name or meta.get('mimeType') != FOLDER_MIME or self.parent not in meta.get('parents', []) or meta.get('trashed'):
            raise IntegrityError('Stable run folder metadata/parent mismatch')
        self.folder = file_id
        return file_id

    def raw_proof(self, file_id, expected_sha, expected_bytes):
        # Full raw bytes, not a Drive md5, upload receipt, or cached local file.
        raw = self.request(lambda: self.api.files().get_media(fileId=file_id))
        if not isinstance(raw, bytes) or len(raw) != expected_bytes or hashlib.sha256(raw).hexdigest() != expected_sha:
            raise IntegrityError('Fresh Drive raw readback bytes/SHA mismatch')
        return {'id': file_id, 'sha256': expected_sha, 'bytes': expected_bytes, 'fresh_raw_readback_verified': True, 'raw_verified_utc': utc(), 'folder_id': self.folder}

    def put(self, name, snapshot, *, immutable=False):
        from googleapiclient.http import MediaFileUpload
        snapshot = Path(snapshot)
        digest, count = sha(snapshot), snapshot.stat().st_size
        found = self.find(self.folder, name)
        if len(found) > 1:
            raise IntegrityError('Duplicate artifact name: ' + name)
        if found and immutable:
            proof = self.raw_proof(found[0]['id'], digest, count)
        else:
            if found:
                meta = self.metadata(found[0]['id'])
                if self.folder not in meta.get('parents', []) or meta.get('trashed'):
                    raise IntegrityError('Mutable artifact parent mismatch')
            media = lambda: MediaFileUpload(str(snapshot), mimetype='application/octet-stream', resumable=False)
            if found:
                uploaded = self.request(lambda: self.api.files().update(fileId=found[0]['id'], media_body=media(), fields='id'))
            else:
                uploaded = self.create({'name': name, 'parents': [self.folder]}, media)
            proof = self.raw_proof(uploaded['id'], digest, count)
        return dict(proof, name=name, immutable=immutable)


class Publisher:
    def __init__(self, root, store, *, sleep=time.sleep):
        self.root, self.store, self.sleep = Path(root), store, sleep
        self.run = self.root / 'training'
        self.work = self.root / 'drive_publication'
        self.work.mkdir(parents=True, exist_ok=True)
        self.state_path = self.work / 'publication_status.json'
        if self.state_path.exists():
            self.state = json.loads(self.state_path.read_text('utf-8'))
            if self.state.get('schema') != SCHEMA:
                raise IntegrityError('Publisher state schema mismatch')
        else:
            self.state = {'schema': SCHEMA, 'artifacts': {}, 'checkpoint_generations': [], 'errors': []}
        self.state.update(folder_name=FOLDER_NAME, folder_parent_id=PARENT, training_started_by_publisher=False, production_approval=False, semantic_quality_certified=False)

    def save(self):
        atomic_json(self.state_path, self.state)

    def error(self, case, exc):
        item = {'at_utc': utc(), 'case': case, 'type': type(exc).__name__, 'message': str(exc), 'traceback_tail': traceback.format_exc()[-4000:]}
        self.state['errors'] = (self.state.get('errors', []) + [item])[-100:]
        self.state['last_error'] = item
        atomic_json(self.work / 'publisher_error.json', item)
        self.save()

    def publish(self, name, path, immutable=False):
        path = Path(path)
        snapshot = self.work / 'snapshots' / name
        details = snapshot_file(path, snapshot)
        prior = self.state['artifacts'].get(name)
        if prior and prior.get('sha256') == details['sha256'] and prior.get('bytes') == details['bytes'] and prior.get('fresh_raw_readback_verified') is True and prior.get('folder_id') == self.store.folder:
            return prior
        if prior and immutable and prior.get('sha256') != details['sha256']:
            raise IntegrityError('Immutable local artifact changed: ' + name)
        proof = self.store.put(name, snapshot, immutable=immutable)
        if any(proof.get(k) != v for k, v in details.items()) or proof.get('fresh_raw_readback_verified') is not True:
            raise IntegrityError('Store supplied no matching raw proof: ' + name)
        self.state['artifacts'][name] = proof
        self.save()
        return proof

    def publish_json(self, name, obj):
        path = self.work / 'documents' / name
        atomic_json(path, obj)
        return self.publish(name, path)

    def generation(self, gen):
        archive, detail = package_generation(gen, self.work / 'checkpoints')
        proof = dict(self.publish(archive.name, archive, immutable=True), **detail)
        existing = {x['manifest_sha256']: x for x in self.state['checkpoint_generations']}
        existing[detail['manifest_sha256']] = proof
        self.state['checkpoint_generations'] = sorted(existing.values(), key=lambda x: (x['step'], x['rows_done']))
        self.save()
        return proof

    def pointer(self):
        latest = self.run / 'latest.json'
        if not latest.is_file():
            return None
        snapshot = self.work / 'latest_local_snapshot.json'
        snapshot_file(latest, snapshot)
        pointer = json.loads(snapshot.read_text('utf-8'))
        generation = pointer.get('generation')
        if not isinstance(generation, str) or not generation.startswith('generation_step_') or Path(generation).name != generation:
            raise IntegrityError('Unsafe or absent local checkpoint generation pointer')
        proof = self.generation(self.run / generation)
        for key in ('step', 'rows_done', 'manifest_sha256'):
            if pointer.get(key) != proof[key]:
                raise IntegrityError('Local pointer differs from verified generation: ' + key)
        # This mutable recovery pointer is always published LAST, after raw ZIP verification.
        remote = self.publish_json('latest_checkpoint.json', {'schema': SCHEMA, **proof, 'checkpoint_name': proof['name'], 'local_pointer': pointer})
        self.state['last_checkpoint'] = proof
        self.state['latest_pointer_proof'] = remote
        self.save()
        return proof

    def publish_available(self):
        paths = set(self.root.glob('*.py')) | set(self.root.glob('*config*.json')) | set(self.root.glob('*manifest*.json'))
        for folder in ('code', 'helpers'):
            if (self.root / folder).is_dir():
                paths |= set((self.root / folder).glob('*.py'))
        names = ('run_config.json', 'progress.json', 'final_metrics.json', 'runtime_versions.json', 'structural_audit.json', 'target_audit.json', 'input_audit.json', 'evaluation_contract.json', 'successful_ids.jsonl', 'checkpoint_timing.jsonl', 'base_generations.jsonl', 'adapter_generations.jsonl', 'base_generation_provenance.json', 'adapter_generation_provenance.json', 'eval_contract_provenance.json', 'error.json', 'run_complete.json')
        paths |= {self.run / name for name in names}
        paths |= {self.root / name for name in ('runtime_versions.json', 'structural_audit.json', 'training_target_code_audit.json', 'frozen_config_manifest.json', 'owner_run_scope.json', 'neutral_tutor_contract.json', 'selected_view_tokenization_audit.json', 'selected_view_structural_audit.json', 'staged_code_hashes.json', 'install_status.json')}
        # Only explicitly staged CPU evidence; these globs never select corpus,
        # model weights, runtime databases or checkpoint ZIPs.
        paths |= set(self.root.glob('cpu_*.json'))
        for folder in ('cpu_evidence', 'cpu_tests'):
            if (self.root / folder).is_dir():
                paths |= set((self.root / folder).glob('*.json')) | set((self.root / folder).glob('*.txt'))
        for path in sorted(paths):
            if not path.is_file():
                continue
            # Explicit small evidence/code allowlist; never package a corpus or runtime database.
            if path.stat().st_size > 64 * 1024 * 1024:
                raise IntegrityError('Unexpected large non-checkpoint evidence file: ' + path.name)
            name = str(path.relative_to(self.root)).replace('/', '__').replace('\\', '__')
            try:
                self.publish(name, path)
                if name == 'training__progress.json':
                    self.state['last_progress'] = json.loads((self.work / 'snapshots' / name).read_text('utf-8'))
                    self.save()
            except IntegrityError:
                raise
            except Exception as exc:
                self.error('artifact:' + name, exc)

    def finish(self):
        complete_path = self.run / 'run_complete.json'
        if not complete_path.is_file():
            return False
        snapshot = self.work / 'run_complete_snapshot.json'
        snapshot_file(complete_path, snapshot)
        complete = json.loads(snapshot.read_text('utf-8'))
        if complete.get('complete') is not True:
            return False
        if complete.get('requested_training_wall_seconds') != 18000 or complete.get('full_requested_training_window_reached') is not True or complete.get('actual_training_wall_seconds', 0) < 18000:
            raise IntegrityError('Completion does not record the full authorized 18000-second optimizer window')
        files, sizes = complete.get('files'), complete.get('file_bytes')
        required = {'run_config.json', 'runtime_versions.json', 'structural_audit.json', 'final_metrics.json', 'successful_ids.jsonl', 'checkpoint_timing.jsonl', 'latest.json', 'base_generations.jsonl', 'adapter_generations.jsonl', 'adapter_export.zip'}
        if not isinstance(files, dict) or not isinstance(sizes, dict) or not required <= set(files) or set(files) != set(sizes):
            raise IntegrityError('Completion stable-file hash/byte manifest missing required evidence')
        bound = {}
        for relative, digest in sorted(files.items()):
            source = contained_file(self.run, relative)
            dest = self.work / 'final_bound' / relative
            details = snapshot_file(source, dest)
            if details != {'bytes': sizes[relative], 'sha256': digest}:
                raise IntegrityError('Final stable-file snapshot differs from completion: ' + relative)
            bound[relative] = dest
            if relative != 'adapter_export.zip':
                name = 'training__' + relative.replace('/', '__')
                self.publish(name, dest)
        adapter = bound['adapter_export.zip']
        expected = complete.get('adapter_zip_sha256')
        if not isinstance(expected, str) or len(expected) != 64 or sha(adapter) != expected:
            raise IntegrityError('Completion does not bind the final adapter SHA')
        expected_bytes = complete.get('adapter_zip_bytes', complete.get('adapter_bytes'))
        if expected_bytes is not None and expected_bytes != adapter.stat().st_size:
            raise IntegrityError('Completion adapter byte count mismatch')
        fixture_sets = []
        for name in ('base_generations.jsonl', 'adapter_generations.jsonl'):
            raw_snapshot = bound[name]
            rows = [json.loads(line) for line in raw_snapshot.read_text('utf-8').splitlines() if line.strip()]
            ids = {r.get('fixture_id') for r in rows}
            if len(rows) != 28 or len(ids) != 28 or None in ids:
                raise IntegrityError('Final generation output does not contain 28 unique fixtures: ' + name)
            fixture_sets.append(ids)
        if fixture_sets[0] != fixture_sets[1]:
            raise IntegrityError('Base/adapter fixture ID sets differ')
        if complete.get('base_output_sha256') != sha(bound['base_generations.jsonl']) or complete.get('adapter_output_sha256') != sha(bound['adapter_generations.jsonl']):
            raise IntegrityError('Completion output hashes disagree with bound output snapshots')
        cp = self.pointer()
        if not cp:
            raise IntegrityError('No verified recovery generation at completion')
        final_checkpoint = complete.get('final_checkpoint', {})
        if any(final_checkpoint.get(key) != cp[key] for key in ('generation', 'step', 'rows_done', 'manifest_sha256')) or complete.get('step') != cp['step'] or complete.get('rows_done') != cp['rows_done']:
            raise IntegrityError('Final completion does not bind the verified recovery checkpoint')
        adapter_proof = self.publish('adapter_export_' + expected + '.zip', adapter, immutable=True)
        complete_proof = self.publish('run_complete.json', snapshot)
        proof = {'schema': SCHEMA, 'complete': True, 'published_utc': utc(), 'folder_id': self.store.folder, 'folder_parent_id': PARENT, 'folder_name': FOLDER_NAME, 'adapter': adapter_proof, 'last_checkpoint': cp, 'latest_pointer': self.state['latest_pointer_proof'], 'run_complete': complete_proof, 'artifacts': dict(self.state['artifacts']), 'base_output_rows': 28, 'adapter_output_rows': 28, 'requested_training_wall_seconds': complete['requested_training_wall_seconds'], 'actual_training_wall_seconds': complete['actual_training_wall_seconds'], 'full_requested_training_window_reached': True, 'evaluation_contract_sha256': complete.get('evaluation_contract_sha256'), 'raw_integrity_verified_only': True, 'production_approval': False, 'semantic_quality_certified': False, 'training_started_by_publisher': False, 'whole_corpus_training_claimed': False}
        atomic_json(self.work / 'complete_publication_proof.json', proof)
        final_proof = self.publish('complete_publication_proof.json', self.work / 'complete_publication_proof.json')
        atomic_json(self.work / 'complete_publication_proof_readback.json', final_proof)
        self.state.update(publisher_state='COMPLETE_RAW_VERIFIED', completed_utc=utc(), complete_proof=final_proof)
        self.save()
        return True

    def run_loop(self):
        try:
            self.store.ensure_folder()
            if self.state.get('folder_id') not in (None, self.store.folder):
                raise IntegrityError('Resumed state points to a different folder')
            self.state.update(folder_id=self.store.folder, publisher_state='RUNNING', started_utc=utc())
            self.save()
            while True:
                try:
                    self.publish_available()
                    for gen in sorted(self.run.glob('generation_step_*')):
                        if gen.is_dir() and (gen / 'generation_manifest.json').is_file():
                            self.generation(gen)
                    self.pointer()
                    if self.finish():
                        return
                    self.publish_json('LIVE_publication_status.json', {'schema': SCHEMA, 'observed_utc': utc(), 'folder_id': self.store.folder, 'last_progress': self.state.get('last_progress'), 'last_checkpoint': self.state.get('last_checkpoint'), 'latest_pointer_proof': self.state.get('latest_pointer_proof'), 'progress_proof': self.state['artifacts'].get('training__progress.json'), 'publisher_state': 'RUNNING', 'last_error': self.state.get('last_error'), 'production_approval': False})
                    self.state['last_tick_utc'] = utc()
                    self.save()
                except IntegrityError:
                    raise
                except Exception as exc:
                    self.error('publication_tick', exc)
                # No stale prior budget/deadline stops publication. Worker owns 18,000s
                # optimizer budget, 1,800s evaluation/export grace, and 15-minute CPs.
                self.sleep(90)
        except Exception as exc:
            self.state['publisher_state'] = 'FAILED_INTEGRITY' if isinstance(exc, IntegrityError) else 'ERROR_RESTART_SAME_FOLDER'
            self.error('publisher', exc)


def start_publisher(*, root=ROOT, credentials=None, api_factory=None):
    """Start one daemon; authenticate/build the only Drive client in that thread."""
    root = Path(root)
    if root.resolve() != ROOT.resolve():
        raise IntegrityError('Unexpected corrective run root')
    with _START_LOCK:
        for thread in threading.enumerate():
            if thread.name == _THREAD_NAME and thread.is_alive():
                return {'started': False, 'reason': 'Publisher already running', 'thread': thread.name}
        def worker():
            pub = None
            try:
                if api_factory is None:
                    import google.auth
                    from googleapiclient.discovery import build
                    creds = credentials
                    if creds is None:
                        creds, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/drive'])
                    api = build('drive', 'v3', credentials=creds, cache_discovery=False)
                else:
                    api = api_factory()
                pub = Publisher(root, DriveStore(api))
                pub.run_loop()
            except Exception as exc:
                if pub is not None:
                    pub.error('startup', exc)
                else:
                    atomic_json(root / 'drive_publication/publisher_error.json', {'utc': utc(), 'case': 'startup', 'type': type(exc).__name__, 'message': str(exc), 'traceback_tail': traceback.format_exc()[-4000:]})
        thread = threading.Thread(target=worker, name=_THREAD_NAME, daemon=True)
        thread.start()
        return {'started': True, 'thread': thread.name, 'folder_name': FOLDER_NAME, 'root': str(root), 'drive_calls_in_calling_thread': False, 'gpu_or_training_lifecycle_changed': False}
