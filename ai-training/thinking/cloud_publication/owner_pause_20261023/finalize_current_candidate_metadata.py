"""One finite metadata-only finalization after the existing CPU scanner exits.

Execute inside the authenticated DATA_ONLY Colab runtime, not on the user's PC.
This creates no data cases, training process, Drive file, or acceptance signoff.
It preserves the raw V3 finding and writes separate, narrower conclusions.
"""
import hashlib
import importlib.util
import json
import sqlite3
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path


def register_final_metadata_check(namespace):
    root = namespace['ROOT']
    directory = namespace['qa_dir']
    worker = namespace['full_audit_worker']
    database = namespace['V3_DB']
    expected_identity = 'f0332df91020ace0fc48d88491fe97364d08826458d08c71ba4ec60524e25863'
    expected_recipe_sha = '1bb69c394c7eaaea7034125c6b3361eebbbe0d77e0715a8454331fbe7cee3ff8'
    if namespace['V3_ID'] != expected_identity or namespace['pointer_all']['sha256'] != expected_recipe_sha:
        raise ValueError('Only the exact current recipe may be finalized')
    if any(t.name == 'MathVisionKidFinalMetadataOnly' and t.is_alive() for t in threading.enumerate()):
        raise RuntimeError('A final metadata check already waits for this worker')
    directory.mkdir(exist_ok=True, parents=True)

    def save(name, value):
        path = directory / name
        data = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
        temporary = path.with_suffix(path.suffix + '.writing')
        temporary.write_bytes(data)
        temporary.replace(path)
        return {'name': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

    status = {'state': 'WAITING_FOR_EXISTING_FULL_SCAN',
              'registered_utc': datetime.now(timezone.utc).isoformat(),
              'recipe_identity': expected_identity, 'recipe_sha256': expected_recipe_sha,
              'training_started': False, 'new_cases': 0, 'new_chat_rows': 0}
    save('final_metadata_status.json', status)

    def finish_once():
        try:
            # This is a background wait, not a second scanner or a polling loop.
            worker.join()
            state = namespace['full_audit_worker_state']
            if state.get('state') != 'AUDIT_FINISHED_WITH_FINDINGS':
                raise ValueError('Worker did not finish with only its known preserved finding: ' + str(state.get('state')))
            raw_report = state['report']
            proof = state['checkpoint']
            if not proof.get('fresh_raw_readback_verified') or proof['id'] != '16Q9ft9xhcioconk-5zpxmdRv1ZDNxqFI':
                raise ValueError('Final checkpoint lacks exact-ID fresh raw readback')
            if proof['report_at_snapshot'] != raw_report:
                raise ValueError('Final report differs from the verified checkpoint report')
            snapshot = root / 'full_audit_v3_snapshot.sqlite'
            if snapshot.stat().st_size != proof['bytes'] or namespace['file_digest'](snapshot) != proof['sha256']:
                raise ValueError('Final portable snapshot bytes no longer match verified proof')

            recipe = namespace['recipe_all']
            members = [{'id': namespace['batch_module'].member_key(e),
                        'role': e['role'], 'rows': e['rows']}
                       for e in recipe['source_members'] + recipe['chat_members']]
            with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True, timeout=30) as db:
                db.execute('PRAGMA query_only=ON')
                if db.execute('SELECT identity,sequence_limit FROM config').fetchone() != (expected_identity, 40960):
                    raise ValueError('Final working database identity or sequence limit changed')
                actual = {r[0]: tuple(r[1:]) for r in db.execute(
                    'SELECT id,role,next_line,complete,expected_rows FROM members')}
                expected = {m['id']: (m['role'], m['rows'], 1, m['rows']) for m in members}
                if actual != expected:
                    raise ValueError('Exact final member cursors/roles/row counts differ')
                issue_rows = [dict(zip(('member','line','kind','detail'), r)) for r in db.execute(
                    'SELECT member,line,kind,detail FROM issues ORDER BY member,line,kind,detail')]
                source = db.execute('SELECT id,source_split,raw_sha,canonical_sha FROM source_versions WHERE id=?',
                                    ('exhaustive_v1_div_1563_43',)).fetchall()
                if len(source) != 1:
                    raise ValueError('Diagnostic source identity is ambiguous or absent')
                diagnostic = dict(zip(('sample_id','split','raw_sha256','canonical_sha256'), source[0]))
                links = db.execute('SELECT count(*) FROM samples WHERE case_id=?',
                                   ('exhaustive_v1_div_1563_43',)).fetchone()[0]
                invalid_tokens = db.execute('SELECT count(*) FROM samples WHERE sequence_tokens<=0 OR sequence_tokens>40960 OR completion_tokens<=0 OR completion_tokens>sequence_tokens').fetchone()[0]
                if invalid_tokens:
                    raise ValueError('Invalid per-row sequence/completion lengths remain')
                case_splits = dict(db.execute('SELECT split,count(DISTINCT case_id) FROM samples GROUP BY split'))
                if case_splits != {'train':1625586, 'validation':6, 'test':6}:
                    raise ValueError('Actual unique case split counts differ')
            db.close()

            spec = importlib.util.spec_from_file_location('mvk_final_adjudication', directory/'final_technical_adjudication.py')
            adjudicator = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(adjudicator)
            result = adjudicator.adjudicate_final_v3_metadata(raw_report, issue_rows, diagnostic,
                {'exhaustive_v1_div_1563_43': {'linked_chat_rows': links}},
                {'members':members, 'unique_chat_rows':6502392,
                 'unique_chat_rows_by_split': {'train':6502344,'validation':24,'test':24},
                 'modes_per_case':4})
            raw_ref = save('final_raw_v3_report_preserved.json', raw_report)
            result.update(observed_utc=datetime.now(timezone.utc).isoformat(),
                          checkpoint=proof, exact_member_cursors_verified=True,
                          per_row_token_lengths_verified=True, actual_cases_by_split=case_splits,
                          raw_report_artifact=raw_ref, tokenizer_revision=namespace['batch_module'].L.REVISION)
            result_ref = save('final_candidate_chat_technical_adjudication.json', result)

            command = [sys.executable, str(directory/'final_source_chat_antijoin.py'),
                       str(database), str(directory/'final_source_chat_antijoin.json'),
                       '--protected-index', str(directory/'protected_numeric_signatures.json'),
                       '--holdout-index', str(directory/'holdout_signatures.json')]
            anti = subprocess.run(command, capture_output=True, text=True, timeout=900)
            save('final_antijoin_execution.json', {'returncode':anti.returncode,
                 'stdout':anti.stdout[-4000:], 'stderr':anti.stderr[-4000:],
                 'payload_or_question_content_read':False})
            if anti.returncode:
                raise ValueError('Source-only reconciliation failed; preserve all evidence')
            classification = json.loads((directory/'final_source_chat_antijoin.json').read_bytes())
            if classification['counts']['classifications'].get('UNRESOLVED_QUARANTINE', 0):
                raise ValueError('Unresolved source-only rows remain quarantined')
            manifest = {
                'schema':'MathVisionKid.current_text_candidate_view_final_metadata.v1',
                'status':'CURRENT_TEXT_CANDIDATE_VIEW_TECHNICALLY_VERIFIED',
                'recipe_identity':expected_identity, 'recipe_sha256':expected_recipe_sha,
                'candidate_chat_rows':6502344, 'candidate_case_ids':1625586,
                'validation_chat_rows':24, 'test_chat_rows':24,
                'raw_chat_rows_all_current_splits':6502392,
                'source_versions_retained':1629906,
                'source_only_audit_rows_retained':classification['counts']['unlinked_source_versions'],
                'selection':'All and only current accepted candidate rows with explicit split=train; preserve evaluation splits.',
                'core_cases':495, 'core_nodes':165, 'core_chat_rows':1980,
                'technical_adjudication':result_ref, 'checkpoint':proof,
                'physical_observation_tasks_pending':5, 'asset_masters_pending':10,
                'g3_source_locator_pending':1, 'whole_curriculum_certified':False,
                'all_rows_semantically_human_reviewed':False,
                'TRAINING_DATASET_READY':False, 'training_started':False,
                'scope_limit':'Technical verification of the current full text candidate view; remaining physical/image/source curriculum acceptance is separate. No training launched.',
            }
            manifest_ref = save('final_current_text_candidate_manifest.json', manifest)
            status.update(state='FINAL_TEXT_TECHNICAL_EVIDENCE_COMPLETE_PENDING_CONTROL_PUBLICATION',
                          completed_utc=datetime.now(timezone.utc).isoformat(),
                          manifest=manifest_ref, checkpoint=proof,
                          source_only_classifications=classification['counts']['classifications'])
        except Exception as error:
            status.update(state='FINALIZATION_STOPPED_WITH_EVIDENCE', error_type=type(error).__name__,
                          error=str(error), stopped_utc=datetime.now(timezone.utc).isoformat())
        finally:
            save('final_metadata_status.json', status)

    thread = threading.Thread(target=finish_once, name='MathVisionKidFinalMetadataOnly', daemon=True)
    thread.start()
    return thread, dict(status)
