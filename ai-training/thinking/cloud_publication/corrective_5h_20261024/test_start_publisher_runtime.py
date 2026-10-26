"""CPU-only publication integrity tests; no Google client, GPU or network."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
import zipfile

SPEC = importlib.util.spec_from_file_location('corrective_publisher', Path(__file__).with_name('start_publisher_runtime.py'))
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)


class Store:
    folder = 'test_stable_folder'
    def __init__(self):
        self.uploads = []
    def put(self, name, path, immutable=False):
        raw = Path(path).read_bytes()
        self.uploads.append((name, raw))
        return {'id': 'id_' + str(len(self.uploads)), 'name': name, 'folder_id': self.folder, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'fresh_raw_readback_verified': True}


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='corrective_publisher_cpu_')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = Store()
        self.pub = p.Publisher(self.root, self.store)

    def generation(self, step=3):
        gen = self.root / 'training' / f'generation_step_{step:06d}_rows_00000048'
        gen.mkdir(parents=True)
        raw = b'adapter-test-bytes'
        (gen / 'adapter.bin').write_bytes(raw)
        manifest = {'complete': True, 'step': step, 'rows_done': 48, 'files': {'adapter.bin': hashlib.sha256(raw).hexdigest()}, 'file_bytes': {'adapter.bin': len(raw)}}
        p.atomic_json(gen / 'generation_manifest.json', manifest)
        p.atomic_json(gen.parent / 'latest.json', {'generation': gen.name, 'step': step, 'rows_done': 48, 'manifest_sha256': p.sha(gen / 'generation_manifest.json')})
        return gen

    def test_snapshot_survives_source_replacement(self):
        source = self.root / 'progress.json'
        source.write_text('old')
        original = p.shutil.copyfile
        calls = []
        def replacing(src, dst):
            result = original(src, dst)
            if not calls:
                calls.append(True)
                source.write_text('new contents')
            return result
        target = self.root / 'snapshot.json'
        with patch.object(p.shutil, 'copyfile', replacing):
            detail = p.snapshot_file(source, target)
        self.assertEqual(target.read_text(), 'new contents')
        self.assertEqual(detail['sha256'], p.sha(target))

    def test_generation_reuses_identical_zip(self):
        gen = self.generation()
        archive, detail = p.package_generation(gen, self.root / 'zips')
        before = (archive.read_bytes(), archive.stat().st_mtime_ns)
        again, other = p.package_generation(gen, self.root / 'zips')
        self.assertEqual((again.read_bytes(), again.stat().st_mtime_ns), before)
        self.assertEqual(detail, other)

    def test_corrupted_cached_zip_rejected(self):
        gen = self.generation()
        archive, _ = p.package_generation(gen, self.root / 'zips')
        with zipfile.ZipFile(archive, 'a') as z:
            z.writestr('unlisted', b'tamper')
        with self.assertRaises(p.IntegrityError):
            p.package_generation(gen, self.root / 'zips')

    def test_member_corruption_and_traversal_rejected(self):
        gen = self.generation()
        (gen / 'adapter.bin').write_bytes(b'changed')
        with self.assertRaises(p.IntegrityError):
            p.package_generation(gen, self.root / 'zips')
        with self.assertRaises(p.IntegrityError):
            p.contained_file(gen, '../outside')

    def test_pointer_only_after_raw_verified_checkpoint(self):
        self.generation()
        self.pub.pointer()
        names = [x[0] for x in self.store.uploads]
        self.assertTrue(names[0].startswith('checkpoint_step_'))
        self.assertEqual(names[-1], 'latest_checkpoint.json')
        self.assertTrue(json.loads(self.store.uploads[-1][1])['fresh_raw_readback_verified'])
        self.pub.pointer()
        self.assertEqual(len(self.store.uploads), 2)

    def test_invalid_store_proof_cannot_publish_pointer(self):
        self.generation()
        self.store.put = lambda *args, **kw: {'fresh_raw_readback_verified': False}
        with self.assertRaises(p.IntegrityError):
            self.pub.pointer()
        self.assertNotIn('latest_checkpoint.json', self.pub.state['artifacts'])

    def test_pointer_manifest_mismatch_rejected(self):
        gen = self.generation()
        pointer = json.loads((gen.parent / 'latest.json').read_text())
        pointer['manifest_sha256'] = '0' * 64
        p.atomic_json(gen.parent / 'latest.json', pointer)
        with self.assertRaises(p.IntegrityError):
            self.pub.pointer()
        self.assertNotIn('latest_checkpoint.json', self.pub.state['artifacts'])

    def test_snapshot_cache_and_immutable_conflict(self):
        source = self.root / 'code.py'
        source.write_text('x=1')
        self.pub.publish('code.py', source, True)
        self.pub.publish('code.py', source, True)
        self.assertEqual(len(self.store.uploads), 1)
        source.write_text('x=2')
        with self.assertRaises(p.IntegrityError):
            self.pub.publish('code.py', source, True)

    def test_complete_requires_both_actual_28_row_outputs(self):
        self.generation()
        run = self.root / 'training'
        (run / 'adapter_export.zip').write_bytes(b'final-adapter')
        for name in ('run_config.json', 'final_metrics.json', 'successful_ids.jsonl', 'checkpoint_timing.jsonl', 'runtime_versions.json', 'structural_audit.json'):
            (run / name).write_text('{}\n')
        raw = ''.join(json.dumps({'fixture_id': f'f{i}'}) + '\n' for i in range(28))
        (run / 'base_generations.jsonl').write_text(raw)
        (run / 'adapter_generations.jsonl').write_text(raw.replace('f27', 'f26'))
        def completion():
            names = ('run_config.json', 'runtime_versions.json', 'structural_audit.json', 'final_metrics.json', 'successful_ids.jsonl', 'checkpoint_timing.jsonl', 'latest.json', 'base_generations.jsonl', 'adapter_generations.jsonl', 'adapter_export.zip')
            p.atomic_json(run / 'run_complete.json', {'complete': True, 'step': 3, 'rows_done': 48, 'adapter_zip_sha256': p.sha(run / 'adapter_export.zip'), 'adapter_zip_bytes': (run / 'adapter_export.zip').stat().st_size, 'requested_training_wall_seconds': 18000, 'actual_training_wall_seconds': 18001, 'full_requested_training_window_reached': True, 'final_checkpoint': json.loads((run / 'latest.json').read_text()), 'files': {n: p.sha(run / n) for n in names}, 'file_bytes': {n: (run / n).stat().st_size for n in names}, 'base_output_sha256': p.sha(run / 'base_generations.jsonl'), 'adapter_output_sha256': p.sha(run / 'adapter_generations.jsonl')})
        completion()
        with self.assertRaises(p.IntegrityError):
            self.pub.finish()
        self.assertFalse((self.pub.work / 'complete_publication_proof.json').exists())
        (run / 'adapter_generations.jsonl').write_text(raw)
        completion()
        self.assertTrue(self.pub.finish())
        proof = json.loads((self.pub.work / 'complete_publication_proof.json').read_text())
        self.assertFalse(proof['production_approval'])
        self.assertTrue(proof['raw_integrity_verified_only'])
        self.assertEqual(self.pub.state['publisher_state'], 'COMPLETE_RAW_VERIFIED')

    def test_retry_throttles_quota_but_not_permission_errors(self):
        waits, calls = [], []
        store = p.DriveStore(None, sleep=waits.append, clock=lambda: 0)
        class Error(Exception):
            resp = types.SimpleNamespace(status=403)
        class Request:
            def execute(self, **kw):
                calls.append(True)
                if len(calls) < 3:
                    raise Error('rateLimitExceeded')
                return {'ok': True}
        self.assertEqual(store.request(Request), {'ok': True})
        self.assertEqual(waits.count(60), 2)
        self.assertEqual(waits.count(1.25), 2)
        calls.clear()
        class Denied:
            def execute(self, **kw):
                calls.append(True)
                raise Error('insufficientPermissions')
        with self.assertRaises(Error):
            store.request(Denied)
        self.assertEqual(len(calls), 1)

    def test_raw_proof_requires_full_bytes(self):
        store = p.DriveStore(None)
        store.request = lambda factory: b'wrong'
        with self.assertRaises(p.IntegrityError):
            store.raw_proof('id', hashlib.sha256(b'right').hexdigest(), 5)

    def test_reserved_drive_id_prevents_duplicate_create_after_lost_response(self):
        creates = []
        class Conflict(Exception):
            resp = types.SimpleNamespace(status=409)
        class Request:
            def __init__(self, fn):
                self.fn = fn
            def execute(self, **kw):
                return self.fn()
        class Files:
            def generateIds(self, **kw):
                return Request(lambda: {'ids': ['reserved_id']})
            def create(self, **kw):
                def perform():
                    creates.append(copy.deepcopy(kw['body']))
                    if len(creates) == 1:
                        raise OSError('Remote create succeeded, response lost')
                    raise Conflict('Already exists')
                return Request(perform)
            def get(self, **kw):
                return Request(lambda: {'id': 'reserved_id', 'name': 'artifact', 'parents': ['folder']})
        api = types.SimpleNamespace(files=lambda: Files())
        store = p.DriveStore(api, sleep=lambda _: None, clock=lambda: 0)
        self.assertEqual(store.create({'name': 'artifact', 'parents': ['folder']}), {'id': 'reserved_id'})
        self.assertEqual([x['id'] for x in creates], ['reserved_id', 'reserved_id'])

    def test_run_folder_parent_metadata_checked(self):
        store = p.DriveStore(None)
        store.metadata = lambda file_id: ({'id': p.PARENT, 'mimeType': p.FOLDER_MIME} if file_id == p.PARENT else {'name': p.FOLDER_NAME, 'mimeType': p.FOLDER_MIME, 'parents': ['wrong_parent']})
        store.find = lambda parent, name: [{'id': 'existing_run'}]
        with self.assertRaises(p.IntegrityError):
            store.ensure_folder()

    def test_old_budget_completion_cannot_stop_publisher(self):
        run = self.root / 'training'
        run.mkdir()
        p.atomic_json(run / 'run_complete.json', {'complete': True, 'requested_training_wall_seconds': 10800})
        with self.assertRaises(p.IntegrityError):
            self.pub.finish()
        self.assertFalse((self.pub.work / 'complete_publication_proof.json').exists())

    def test_available_includes_staged_audits_and_cpu_evidence(self):
        names = ('selected_view_tokenization_audit.json', 'selected_view_structural_audit.json', 'staged_code_hashes.json', 'install_status.json', 'cpu_validation_receipt.json', 'cpu_evidence/tests.json', 'training/input_audit.json', 'training/evaluation_contract.json')
        for name in names:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('{}\n')
        (self.root / 'training_view.jsonl').write_text('corpus excluded')
        self.pub.publish_available()
        uploaded = {name for name, raw in self.store.uploads}
        self.assertEqual(uploaded, {name.replace('/', '__') for name in names})


if __name__ == '__main__':
    unittest.main()
