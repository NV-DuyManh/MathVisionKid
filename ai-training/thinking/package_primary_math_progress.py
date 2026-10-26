"""Package current data with scoped owner attestations; never train."""
from __future__ import annotations
import json
from pathlib import Path
import zipfile
from primary_math_data_pipeline import HERE,DEFAULT_ROOT,sha


def package_progress():
    project=HERE.parent
    evidence=HERE/'evidence/primary_math_teacher_20261016'
    output=evidence/'Primary_Math_Teacher_20261016_PROGRESS.zip'
    state=json.loads((DEFAULT_ROOT/'data_build_state.json').read_text('utf-8'))
    candidates=[p for p in DEFAULT_ROOT.rglob('*') if p.is_file() and p.suffix in ('.json','.jsonl','.py')]
    candidates += [p for p in evidence.iterdir() if p.is_file() and p.suffix in ('.json','.jsonl','.txt')
                   and p.name!='drive_artifact_verification.json']
    candidates += list(HERE.glob('author_primary_*.py'))+list(HERE.glob('review_primary_*.py'))
    candidates += list(HERE.glob('g1_*_author.py'))
    candidates += list(HERE.glob('author_finish_g*.py'))+list(HERE.glob('finish_g4_*.py'))
    candidates += [HERE/name for name in ('primary_math_data_pipeline.py','test_primary_math_data_pipeline.py',
                   'repair_primary_math_pending_20261016.py','package_primary_math_progress.py',
                   'author_finite_remaining.py','polish_primary_math_release.py','finalize_primary_math_finite.py',
                   'review_finish_g5.py')]
    paths=sorted({p.relative_to(project).as_posix() for p in candidates})
    files=[{'path':p,'sha256':sha((project/p).read_bytes())} for p in paths]
    manifest={'status':'FINITE_BLUEPRINT_COMPLETE_NOT_EXHAUSTIVE_CURRICULUM' if state.get('completion') else 'PARTIAL_PROGRESS_NOT_COMPLETE_CURRICULUM',
        'authored_cases':state['authored_cases'],
        'accepted_cases':state['accepted_cases'],'chat_rows':state['chat_train_rows'],
        'pending_cases':state['authored_cases']-state['accepted_cases'],
        'pending_cases_not_in_chat_export':True,
        'core_cases':495-state['remaining_core_cases'],'remaining_core_cases':state['remaining_core_cases'],
        'core_nodes_complete':state['core_nodes_complete'],
        'human_verified':state.get('human_verified',False),'teacher_certified':state.get('teacher_certified',False),
        'owner_human_reviewed':state.get('owner_human_reviewed',False),
        'source_role':state.get('source_role','AI_GENERATED'),
        'human_teacher_verified_cases':state.get('human_teacher_verified_cases',0),
        'owner_human_signoffs_sha256':state.get('owner_human_signoffs_sha256'),
        'verification_scope':'ENUMERATED_ACCEPTED_CASES_AND_DERIVED_CHAT',
        'original_source_review_and_seed_history_not_reclassified':True,
        'training_started':False,'context_file_id':'13gdIPQTFKcekoQQtgo0TXc7RgeadzIN9',
        'final_release':state.get('final_release'),
        'authoritative_release_index':'thinking/data/primary_math_teacher_20261016/final_release_index.json' if state.get('completion') else None,
        'do_not_concatenate_all_audit_or_source_jsonl_as_training_data':True,
        'limits':['Human/teacher labels record the explicit owner attestation for enumerated hashes; original authorship remains traceable.',
                  'Future process approval does not assert completed human review of unseen rows.',
                  'Pipeline requires existing project V3/V4 helpers and protected inputs, which are not bundled.',
                  'Drive readback evidence is external to this ZIP to avoid a circular hash.',
                  'Text-described tasks do not verify visual or physical performance.',
                  'Pending authored rows are not part of the accepted chat export.',
                  'Quota completion is not exhaustive curriculum coverage or model accuracy.'],
        'files':files}
    changed=True
    if output.exists():
        with zipfile.ZipFile(output) as prior:
            previous=json.loads(prior.read('PACKAGE_MANIFEST.json'))
            changed=previous!=manifest
    if changed:
        temporary=output.with_suffix('.tmp.zip')
        with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED) as archive:
            for item in files:
                info=zipfile.ZipInfo(item['path'],date_time=(2026,10,16,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED
                archive.writestr(info,(project/item['path']).read_bytes())
            info=zipfile.ZipInfo('PACKAGE_MANIFEST.json',date_time=(2026,10,16,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        temporary.replace(output)
    # Verify all bytes even when the existing archive could be reused.
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist())==len(files)+1
        for item in files:assert sha(archive.read(item['path']))==item['sha256'],item['path']
    return {'changed':changed,'bytes':output.stat().st_size,'sha256':sha(output.read_bytes()),
            'members':len(files)+1,'accepted_cases':state['accepted_cases'],'chat_rows':state['chat_train_rows']}


if __name__=='__main__':print(json.dumps(package_progress()))
