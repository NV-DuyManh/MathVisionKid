"""Owner-revised publication completion contract; no thread/network at import.

Stage beside the original publisher, then call
install_revised_publication_contract(existing_module). This changes only the
Publisher.finish class method. Existing daemon/client/folder/state remain intact.
Historical publisher code and original budget evidence are preserved.
"""
import hashlib
import inspect
import json
import math
from datetime import datetime, timezone
from pathlib import Path

SCOPE = 'OWNER_REVISED_REMAINING_COLAB_WINDOW_V2'
AUTHORIZED_UTC = '2026-10-24T00:58:23Z'
TRAIN_STOP_UTC = '2026-10-24T05:13:23Z'
HARD_DEADLINE_UTC = '2026-10-24T05:28:23Z'
RESERVE_SECONDS = 900
OWNER_REVISION_SHA256 = 'e3e5b960b65e618909329e18bbf2656e4d80435a445b60e3102a176f254aab00'


def timestamp(text):
    return datetime.fromisoformat(text.replace('Z', '+00:00')).timestamp()


def validate_revised_budget(complete, error=ValueError):
    expected = {'budget_scope': SCOPE, 'hard_deadline_utc': HARD_DEADLINE_UTC,
                'train_stop_utc': TRAIN_STOP_UTC, 'reserve_seconds': RESERVE_SECONDS}
    for key, value in expected.items():
        if complete.get(key) != value:
            raise error('Owner revised budget field differs: ' + key)
    if complete.get('owner_budget_revision_sha256') != OWNER_REVISION_SHA256:
        raise error('Completion does not bind the exact owner budget revision bytes')
    if complete.get('budget_satisfied') is not True:
        raise error('Revised budget is not explicitly satisfied')
    deadline, cutoff = timestamp(HARD_DEADLINE_UTC), timestamp(TRAIN_STOP_UTC)
    if complete.get('hard_deadline_unix') != deadline:
        raise error('Revised hard deadline epoch differs from UTC')
    for key in ('prior_training_consumed_seconds', 'current_segment_training_wall_seconds', 'actual_training_wall_seconds'):
        value = complete.get(key)
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise error('Missing or invalid actual training duration: ' + key)
    prior, segment = complete['prior_training_consumed_seconds'], complete['current_segment_training_wall_seconds']
    if abs(complete['actual_training_wall_seconds'] - prior - segment) > 0.01:
        raise error('Actual training wall time must equal consumed prior plus current segment')
    # The worker owns group-boundary stopping. The publisher checks the actual
    # finalization timestamp, not the current time of a delayed upload/retry.
    completed = complete.get('completed_unix')
    if type(completed) not in (int, float) or not math.isfinite(completed) or not timestamp(AUTHORIZED_UTC) <= completed <= deadline:
        raise error('Run did not finish evaluation/export within the owner deadline')
    stopped = complete.get('training_stopped_unix', complete.get('metrics', {}).get('training_stopped_unix'))
    if type(stopped) not in (int, float) or not math.isfinite(stopped) or not cutoff <= stopped <= completed:
        raise error('Training stop timestamp must reach cutoff and precede completion')
    if complete.get('full_requested_training_window_reached') is True and complete['actual_training_wall_seconds'] < 18000:
        raise error('Completion falsely claims original 18000-second window')
    return {**expected, 'authorized_utc': AUTHORIZED_UTC, 'owner_budget_revision_sha256': OWNER_REVISION_SHA256, 'hard_deadline_unix': deadline,
            'train_stop_unix': cutoff, 'completed_unix': completed,
            'training_stopped_unix': stopped, 'budget_satisfied': True}


def validate_bound_config(config, budget, error=ValueError):
    for key in ('budget_scope', 'hard_deadline_utc', 'train_stop_utc', 'reserve_seconds', 'hard_deadline_unix', 'owner_budget_revision_sha256'):
        if config.get(key) != budget[key]:
            raise error('Hash-bound run config differs from revised owner budget: ' + key)


def revised_finish(self, existing_module):
    IntegrityError = existing_module.IntegrityError
    snapshot_file = existing_module.snapshot_file
    contained_file = existing_module.contained_file
    sha = existing_module.sha
    atomic_json = existing_module.atomic_json
    utc = existing_module.utc
    SCHEMA, PARENT, FOLDER_NAME = existing_module.SCHEMA, existing_module.PARENT, existing_module.FOLDER_NAME
    complete_path = self.run / 'run_complete.json'
    if not complete_path.is_file():
        return False
    snapshot = self.work / 'run_complete_snapshot.json'
    snapshot_file(complete_path, snapshot)
    complete = json.loads(snapshot.read_text('utf-8'))
    if complete.get('complete') is not True:
        return False
    budget = validate_revised_budget(complete, IntegrityError)
    files, sizes = (complete.get('files'), complete.get('file_bytes'))
    required = {'owner_budget_revision_config.json', 'run_config.json', 'runtime_versions.json', 'structural_audit.json', 'final_metrics.json', 'successful_ids.jsonl', 'checkpoint_timing.jsonl', 'latest.json', 'base_generations.jsonl', 'adapter_generations.jsonl', 'adapter_export.zip'}
    if not isinstance(files, dict) or not isinstance(sizes, dict) or (not required <= set(files)) or (set(files) != set(sizes)):
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
    if sha(bound['owner_budget_revision_config.json']) != OWNER_REVISION_SHA256:
        raise IntegrityError('Bound owner revision file differs from the authorized exact bytes')
    bound_config = json.loads(bound['run_config.json'].read_text('utf-8'))
    validate_bound_config(bound_config, budget, IntegrityError)
    cp = self.pointer()
    if not cp:
        raise IntegrityError('No verified recovery generation at completion')
    final_checkpoint = complete.get('final_checkpoint', {})
    if any((final_checkpoint.get(key) != cp[key] for key in ('generation', 'step', 'rows_done', 'manifest_sha256'))) or complete.get('step') != cp['step'] or complete.get('rows_done') != cp['rows_done']:
        raise IntegrityError('Final completion does not bind the verified recovery checkpoint')
    adapter_proof = self.publish('adapter_export_' + expected + '.zip', adapter, immutable=True)
    complete_proof = self.publish('run_complete.json', snapshot)
    proof = {'schema': SCHEMA, 'complete': True, 'published_utc': utc(), 'folder_id': self.store.folder, 'folder_parent_id': PARENT, 'folder_name': FOLDER_NAME, 'adapter': adapter_proof, 'last_checkpoint': cp, 'latest_pointer': self.state['latest_pointer_proof'], 'run_complete': complete_proof, 'artifacts': dict(self.state['artifacts']), 'base_output_rows': 28, 'adapter_output_rows': 28, 'budget_scope': budget['budget_scope'], 'owner_revised_budget': budget, 'actual_training_wall_seconds': complete.get('actual_training_wall_seconds'), 'prior_training_consumed_seconds': complete['prior_training_consumed_seconds'], 'current_segment_training_wall_seconds': complete['current_segment_training_wall_seconds'], 'original_18000_second_requirement_superseded': True, 'evaluation_contract_sha256': complete.get('evaluation_contract_sha256'), 'raw_integrity_verified_only': True, 'production_approval': False, 'semantic_quality_certified': False, 'training_started_by_publisher': False, 'whole_corpus_training_claimed': False}
    atomic_json(self.work / 'complete_publication_proof.json', proof)
    final_proof = self.publish('complete_publication_proof.json', self.work / 'complete_publication_proof.json')
    atomic_json(self.work / 'complete_publication_proof_readback.json', final_proof)
    self.state.update(publisher_state='COMPLETE_RAW_VERIFIED', completed_utc=utc(), complete_proof=final_proof)
    self.save()
    return True


def install_revised_publication_contract(existing_module):
    """Atomic Python method swap only; no thread/client/start/Drive operations."""
    if getattr(existing_module, 'FOLDER_NAME', None) != 'MathVisionKid_CORRECTIVE_5H_20261024':
        raise ValueError('Unexpected publisher folder contract')
    if getattr(existing_module, 'PARENT', None) != '19ZxkfKVIggdcbSfsAdCtG1ibfJ0CRN3n':
        raise ValueError('Unexpected publisher parent')
    if getattr(existing_module, 'SCHEMA', None) != 'MathVisionKid.corrective5h_publication.v1':
        raise ValueError('Unexpected publisher schema')
    cls = existing_module.Publisher
    if getattr(cls.finish, '_owner_revised_publication_v2', False):
        return {'installed': False, 'reason': 'Revised contract already installed', 'budget_scope': SCOPE}
    original = cls.finish
    def installed_finish(self):
        return revised_finish(self, existing_module)
    installed_finish._owner_revised_publication_v2 = True
    installed_finish._original_finish = original
    cls.finish = installed_finish
    return {'installed': True, 'budget_scope': SCOPE, 'only_method_changed': 'Publisher.finish',
            'existing_thread_client_folder_preserved': True, 'network_calls': 0,
            'original_finish_preserved': True,
            'original_finish_source_sha256': hashlib.sha256(inspect.getsource(original).encode()).hexdigest(),
            'revised_contract_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
