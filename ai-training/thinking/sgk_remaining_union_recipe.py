"""After verified RUN3 publication, stage the latest data-only union controls.

No Drive/network/state writes. Old31 payloads remain historical hash references.
Only the already-local accepted94 and accepted36 release bundles are reopened
and freshly checked here. Output is outside the new bundle to avoid self hashes.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import zipfile

import exhaustive_colab_loader as L
import math_data_candidate_stream as C
from math_data_archive_audit import source_projection,linkage_errors
from math_data_portable_resume import file_hash,save,digest

HERE=Path(__file__).resolve().parent
RUN2=HERE/'cloud_publication/sgk_finish_20261020'
RUN3=HERE/'cloud_publication/sgk_remaining_20261020'


def read(path):return json.loads(path.read_text('utf8'))


def verified_bundle(directory,expected_cases,expected_rows):
    proof=read(directory/'bundle_remote_verified.json');local=read(directory/'bundle_local.json')
    if proof.get('fresh_raw_verified') is not True or proof.get('all_bytes_equal') is not True:
        raise ValueError('fresh full raw publication proof required: '+str(directory))
    fid=proof.get('file_id',proof.get('id'))
    if not fid:raise ValueError('published existing payload ID required')
    for key in ('sha256','bytes','file_name'):
        if proof.get(key)!=local.get(key):raise ValueError('local/publication artifact identity differs')
    path=Path(local['path'])
    if path.stat().st_size!=proof['bytes'] or file_hash(path)!=proof['sha256']:
        raise ValueError('fresh local release archive byte/SHA mismatch')
    with zipfile.ZipFile(path) as archive:
        names=archive.namelist()
        if len(names)!=len(set(names)):raise ValueError('duplicate archive member')
        manifest=json.loads(archive.read('manifest.json'))
        if set(names)!=set(manifest['members'])|{'manifest.json'}:raise ValueError('archive directory/member manifest differs')
        if manifest.get('accepted_cases')!=expected_cases or manifest.get('chat_rows')!=expected_rows:
            raise ValueError('accepted release count mismatch')
        # Full release-member hashing is permitted only for these accepted
        # releases. It never traverses an old corpus archive/embedded payload.
        for name,ref in manifest['members'].items():
            if any(word in name.casefold() for word in ('concept_challenge','sealed_challenge','pilot_payload')):
                raise ValueError('protected payload cannot be opened for union metadata')
            h=hashlib.sha256();count=0
            with archive.open(name) as stream:
                for chunk in iter(lambda:stream.read(1024*1024),b''):
                    h.update(chunk);count+=len(chunk)
            if count!=ref['bytes'] or h.hexdigest()!=ref['sha256']:
                raise ValueError('release member byte/SHA mismatch: '+name)
        source_lines=archive.read(manifest['source_member']).splitlines()
        chat_lines=archive.read(manifest['chat_member']).splitlines()
        if len(source_lines)!=expected_cases or len(chat_lines)!=expected_rows or any(not x for x in source_lines+chat_lines):
            raise ValueError('source/chat actual JSONL count mismatch')
        sources={}
        for line in source_lines:
            row=json.loads(line);sid=row['sample_id']
            if sid in sources or row.get('split')!='train':raise ValueError('duplicate or nontrain accepted source')
            sources[sid]=(row,hashlib.sha256(line).hexdigest())
        seen=set();modes=Counter()
        for line in chat_lines:
            row=L.validate_chat(json.loads(line));sid=L.case_id(row)
            if row.get('split')!='train' or row['sample_id'] in seen:raise ValueError('duplicate/nontrain accepted chat')
            seen.add(row['sample_id'])
            if sid not in sources:raise ValueError('chat has no matching accepted source')
            source,raw_sha=sources[sid]
            if row.get('source_row_sha256')!=raw_sha or linkage_errors(row,source_projection(source)):
                raise ValueError('accepted chat/source rawhash or field association mismatch')
            modes[(sid,row['mode'])]+=1
        if len(modes)!=expected_cases*4 or any(v!=1 for v in modes.values()):raise ValueError('fourmode grouping differs')
    ref={'file_id':fid,'file_name':proof['file_name'],'sha256':proof['sha256'],'bytes':proof['bytes']}
    descriptor={'run_id':directory.name,'bundle':ref,'source_member':manifest['source_member'],
                'chat_member':manifest['chat_member'],'cases':expected_cases,'chat_rows':expected_rows}
    evidence={**ref,'fresh_local_full_archive_sha256_verified':True,
       'fresh_local_member_sha256_verified':len(manifest['members']),
       'fresh_remote_full_raw_verified_receipt':True,'remote_verified_utc':proof.get('verified_utc'),
       'accepted_source_rows_verified':expected_cases,'accepted_chat_rows_verified':expected_rows,
       'source_raw_row_hash_and_prompt_target_linkage_verified':True,'fourmodes_per_source_verified':True}
    return descriptor,manifest,evidence


def main():
    if not (RUN3/'bundle_remote_verified.json').is_file():
        raise ValueError('Run only AFTER RUN3/bundle_remote_verified.json exists; do not fabricate publication ID/proof')
    basepath=RUN2/'portable_resume/member_catalog_discovered.json';base=read(basepath)
    frozen_before={str(p):file_hash(p) for p in [basepath,RUN2/'portable_resume/member_catalog.json',RUN2/'portable_resume/portable_checkpoint.json']}
    r94,m94,e94=verified_bundle(RUN2,94,376)
    r36,m36,e36=verified_bundle(RUN3,36,144)
    recipe=C.build_recipe([base],[r94,r36],{r94['bundle']['sha256']:m94,r36['bundle']['sha256']:m36})
    if len(recipe['artifacts'])!=33 or len(recipe['chat_members'])!=27 or recipe['pending_discovery']:
        raise ValueError('latest union artifact/member/discovery count mismatch')
    if recipe['raw_candidate_chat_rows_including_declared_current_splits']!=6501612:
        raise ValueError('latest raw rowcount differs from6501612')
    recipe['declared_candidate_chat_rows']=6501564
    recipe['historical_split_totals_pending_full_archive_audit']=True
    recipe['actual_train_only_row_total_verified']=False
    recipe['current_pedagogy_validation_test_rows_separate']=48
    recipe['full_archive_audit_complete']=False
    recipe['verification_scope']={'old31_payloads':'HISTORICAL_PINNED_METADATA_REFERENCES_NOT_FRESH_RAW_READ_HERE',
        'latest94_and36': [e94,e36],
        'all33_payloads_fresh_raw_verified_this_run':False,
        'older_range_directory_observation_not_full_SHA_verification':True}
    recipepath=RUN3/'publish_latest_union_recipe.json';save(recipepath,recipe)
    scope={'schema':'MathVisionKid.latest_union_publication_scope.v1',
        'file':recipepath.name,'sha256':file_hash(recipepath),'bytes':recipepath.stat().st_size,
        'old_payload_artifact_references':31,'latest_append_artifact_references':2,
        'all_payload_artifact_references':33,'candidate_chat_members':27,
        'source_members':len(recipe['source_members']),
        'declared_raw_chat_rows':6501612,'declared_candidate_chat_rows':6501564,
        'historical_split_totals_pending_full_archive_audit':True,
        'actual_train_only_row_total_verified':False,
        'current_pedagogy_eval_rows_kept_separate':48,
        'new_accepted94_chat_rows':376,'new_accepted36_chat_rows':144,
        'accepted_append_full_local_raw_and_member_verification':[e94,e36],
        'old31_not_fresh_raw_verified':True,'old_catalog_sha256':file_hash(basepath),
        'excluded_roles':dict(Counter(x['role'] for x in recipe['excluded_members'])),
        'unknown_future_supplements_refuse_partial_union':True,
        'split_required_explicit_no_missing_defaults':True,
        'full_archive_token_split_audit_complete':False,'training_started':False,
        'recipe_kept_outside_new_bundle_to_avoid_self_hash_circularity':True,
        'drive_mutated_by_helper':False,'state_mutated_by_helper':False}
    evidence=RUN3/'root_evidence';evidence.mkdir(exist_ok=True)
    save(evidence/'latest_union_scope.json',scope)
    # Aggregate already-run14tests and4364-row replay; do not rerun token/full
    # corpus work. Verify receipt file hashes match current implementation.
    loader=RUN3/'stream_loader';files=read(loader/'files_receipt.json')
    if files.get('tests_passed')!=14:raise ValueError('expected existing14stream tests')
    for ref in files['files']:
        path=Path(ref['path'])
        if path.stat().st_size!=ref['bytes'] or file_hash(path)!=ref['sha256']:
            raise ValueError('stream verification receipt stale: '+str(path))
    replay=read(loader/'bounded_replay_receipt.json')
    if replay['final']['acknowledged_rows']!=4364 or replay['final']['complete_members']!=6 or replay['final']['incomplete_case_modes']:
        raise ValueError('existing bounded stream replay evidence mismatch')
    if replay.get('strict_explicit_split_replay_after_final_fix')!={'CANDIDATE':4364,'MEMBER_COMPLETE':6,'EXCLUDED_OTHER_SPLIT':48}:
        raise ValueError('strictsplit real replay evidence missing')
    finalpath=RUN3/'final_receipt.json';final=read(finalpath) if finalpath.exists() else {'schema':'MathVisionKid.remaining_data_publication_receipt.v1'}
    final['latest_union_recipe']=scope
    final['stream_loader_verification']={
        'code_file':'thinking/math_data_candidate_stream.py','code_sha256':file_hash(HERE/'math_data_candidate_stream.py'),
        'tests_file':'thinking/test_math_data_candidate_stream.py','tests_sha256':file_hash(HERE/'test_math_data_candidate_stream.py'),
        'tests_passed':14,'files_receipt_sha256':file_hash(loader/'files_receipt.json'),
        'bounded_replay_receipt_sha256':file_hash(loader/'bounded_replay_receipt.json'),
        'actual_train_chat_rows_replayed':4364,'actual_other_split_rows_excluded':48,
        'actual_local_chat_members_replayed':6,'scope':'BOUNDED_ACTUAL_REPLAY_NO_FULL_6M_TOKEN_OR_SPLIT_AUDIT_CLAIM',
        'readtime_sourcehash_overlay_derived_missing_field_rows':3356,
        'readtime_original_field_verified_overlay_rows':192,
        'original_field_rows_not_reverified_as_source_by_stream':816,
        'tokenizer_or_model_loaded_in_RUN3_reader_replay':False,
        'full_archive_token_split_audit_complete':False,'training_started':False}
    final['full_archive_token_split_audit_complete']=False;final['training_started']=False
    save(finalpath,final)
    if any(file_hash(Path(p))!=sha for p,sha in frozen_before.items()):raise ValueError('frozen RUN2 changed')
    print(json.dumps({'union':str(recipepath),'scope':str(evidence/'latest_union_scope.json'),
       'aggregate_receipt':str(finalpath),'raw_rows':6501612,'candidate_rows':6501564,
       'artifacts':33,'chat_members':27,'training_started':False}))


if __name__=='__main__':main()
