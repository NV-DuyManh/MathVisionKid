"""Prepare explicit union metadata and replay only already-local bounded data.

No downloads, Drive operations, tokenizer/model/weights imports or training.
Frozen RUN2 checkpoint/catalogs/databases are read-only inputs.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

OUT=Path(__file__).resolve().parent;THINKING=OUT.parents[2]
sys.path.insert(0,str(THINKING))
import math_data_candidate_stream as C
import math_data_portable_resume as P
from math_data_source_hash_overlay import VerifiedSourceHashOverlay


def read(path):return json.loads(path.read_text('utf8'))


def main():
    run2=THINKING/'cloud_publication/sgk_finish_20261020';old=THINKING/'cloud_publication/sgk_page_audit_20261019'
    catalogpath=run2/'portable_resume/member_catalog_discovered.json';catalog=read(catalogpath)
    protected_paths=[catalogpath,run2/'portable_resume/member_catalog.json',run2/'portable_resume/portable_checkpoint.json',run2/'source_hash_overlay/manifest.json']
    for directory in ['numeric_911a598ae1bc578f','numeric_7edba0a6ef712e51','current_supplements']:
        protected_paths.append(run2/'portable_resume'/directory/'audit.sqlite')
    before={str(p):P.file_hash(p) for p in protected_paths}
    bundle=read(run2/'bundle_local.json');path=Path(bundle['path'])
    if P.file_hash(path)!=bundle['sha256'] or path.stat().st_size!=bundle['bytes']:raise ValueError('94 append archive identity mismatch')
    with zipfile.ZipFile(path) as archive:
        manifest=json.loads(archive.read('manifest.json'))
    if manifest['accepted_cases']!=94 or manifest['chat_rows']!=376:raise ValueError('unexpected accepted94release')
    # Root supplied this already-verified publication ID. It is a data locator,
    # not a runtime connector/account binding; content/cursor is hash-bound.
    descriptor={'run_id':'sgk_finish_20261020_accepted94','bundle':{k:bundle[k] for k in ('sha256','bytes','file_name')},
       'source_member':manifest['source_member'],'chat_member':manifest['chat_member'],'cases':94,'chat_rows':376}
    descriptor['bundle']['file_id']='1XFLAfwdhaURScQPJjysadiKB1268_joQ'
    append_manifest={bundle['sha256']:manifest}
    recipe=C.build_recipe([catalog],[descriptor],append_manifest)
    assert len(recipe['artifacts'])==32 and len(recipe['chat_members'])==26 and not recipe['pending_discovery']
    assert recipe['raw_candidate_chat_rows_including_declared_current_splits']==6501468
    P.save(OUT/'union_recipe.json',recipe)
    P.save(OUT/'recipe_scope.json',{'schema':'MathVisionKid.all_valid_candidate_stream_scope.v1',
        'parent_catalog_sha256':P.file_hash(catalogpath),'payload_artifacts':32,
        'previous_payload_artifacts':31,'explicit_accepted94_append_sha256':bundle['sha256'],
        'accepted94_verified_publication_id':'1XFLAfwdhaURScQPJjysadiKB1268_joQ',
        'candidate_chat_members':26,'source_members':len(recipe['source_members']),
        'raw_declared_chat_rows':6501468,'declared_train_candidate_rows':6501420,
        'current_pedagogy_validation_test_rows_separate':48,
        'old_6501044_train_candidates_preserved':True,'new_accepted94_chat_rows':376,
        'source_members_never_implicitly_used_as_chat':True,
        'diagnostic_selected_duplicates_and_audit_history_excluded_roles':dict(Counter(x['role'] for x in recipe['excluded_members'])),
        'future_append_contract':'Call discover_supplements on latest STATE/CHAT; register each explicit descriptor with its pinned members manifest. Any missing source_member/hash/row count is a hard error or visible pending discovery; stream refuses partial union.',
        'full_archive_token_split_audit_complete':False,'training_started':False})
    # Replay only finite local members, preserving the complete union recipe
    # separately. No absent old multi-GB member is rematerialized/downloaded.
    paths={bundle['sha256']:path};selected=[]
    latest=Path(read(old/'bundle_local.json')['path']);latestsha=P.file_hash(latest)
    numeric={name:run2/'small_audit_payloads'/name for name in (
        'MVK_multiplication_0_100_one_digit__000000000_000000900_911a598ae1bc578f.zip',
        'MVK_multiplication_0_100_three_digits__000000000_000000101_7edba0a6ef712e51.zip')}
    for local in numeric.values():paths[P.file_hash(local)]=local
    paths[latestsha]=latest
    # Boundary and pedagogy share one archive SHA in the complete recipe;
    # bounded replay uses exact hash-pinned already-restored member files.
    for entry in recipe['chat_members']:
        if entry['sha256'] in paths:selected.append(entry)
        elif entry.get('member') in ('audit/boundary_chat.jsonl','audit/pedagogy_chat_v3.jsonl'):
            direct={**entry,'sha256':entry['member_sha256'],'bytes':entry['member_bytes'],
                    'member':None,'member_sha256':None,'member_bytes':None,
                    'file_id':None,
                    'file_name':Path(entry['member']).name,'original_archive_sha256':entry['sha256']}
            paths[direct['sha256']]=old/'prior_balanced'/entry['member'];selected.append(direct)
    replay=C.build_recipe([{'members':selected}]);replay['scope']='BOUNDED_LOCAL_REPLAY_ONLY_NOT_FULL_UNION'
    if len(replay['chat_members'])!=6:raise ValueError('bounded replay explicitmember count unexpected')
    P.save(OUT/'bounded_replay_recipe.json',replay)
    overlay_manifest=run2/'source_hash_overlay/manifest.json'
    overlay=VerifiedSourceHashOverlay(overlay_manifest,'e80d24406c01faf771e7194a2dcf2bd9f803a1eb5fa473330cb9e854a1fa92fd')
    stream=C.CandidateStream(replay,paths,'train',overlay)
    counts=Counter();by_member=Counter()
    # This replay DB is new RUN3 evidence; no RUN2 database is edited.
    db=OUT/'bounded_replay_overlay_bound.sqlite';consumer=C.DataOnlyConsumer(db,stream)
    def consume(row,evidence):
        counts[evidence.get('sourcehash_origin','unknown')]+=1;by_member[evidence['member_key']]+=1
        assert row.get('split','train')=='train'
    try:
        partial=consumer.consume(consume,max_rows=256)
        consumer.close();consumer=C.DataOnlyConsumer(db,stream)
        final=consumer.consume(consume)
    finally:consumer.close()
    if final['acknowledged_rows']!=4364 or final['complete_members']!=6 or not final['stream_exhausted'] or final['incomplete_case_modes']:
        raise ValueError('bounded full-file/row/split replay failed: '+json.dumps(final))
    after={str(p):P.file_hash(p) for p in protected_paths}
    assert before==after
    result={'schema':'MathVisionKid.candidate_stream_bounded_replay.v1','scope':'4364_TRAIN_ROWS_ONLY_NO_FULL_CORPUS_CLAIM',
            'union_recipe_chat_members':26,'bounded_replay_chat_members':6,
            'final':final,'first_reopen_cursor':partial['cursor'],
            'callback_rows_this_invocation':sum(counts.values()),'callback_sourcehash_origins':dict(counts),
            'expected_existing_overlay_covered_train_rows':3548,
            'expected_derived_missing_legacy_hash_train_rows':3356,
            'new94_and_old110_original_hash_rows_not_reverified_as_source_by_reader':816,
            'all_frozen_input_hashes_unchanged':before,'tokenizer_or_model_loaded':False,
            'full_archive_token_split_audit_complete':False,'training_started':False,'drive_mutated':False}
    P.save(OUT/'bounded_replay_receipt.json',result)
    r=subprocess.run([sys.executable,str(THINKING/'test_math_data_candidate_stream.py')],capture_output=True,text=True,encoding='utf8')
    (OUT/'tests_output.txt').write_text(r.stdout+r.stderr,encoding='utf8');assert r.returncode==0
    files=[THINKING/'math_data_candidate_stream.py',THINKING/'test_math_data_candidate_stream.py']+[p for p in OUT.iterdir() if p.is_file() and p.name!='files_receipt.json']
    P.save(OUT/'files_receipt.json',{'schema':'MathVisionKid.candidate_stream_files.v1','tests_passed':14,
        'files':[{'path':str(p.resolve()),'sha256':P.file_hash(p),'bytes':p.stat().st_size} for p in files],
        'frozen_run2_modified':False,'training_started':False})
    print(json.dumps({k:v for k,v in result.items() if k not in ('all_frozen_input_hashes_unchanged','first_reopen_cursor')}))


if __name__=='__main__':main()
