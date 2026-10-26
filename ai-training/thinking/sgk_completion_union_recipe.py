"""Publish RUN5's data-only union after its immutable bundle is verified.

Only the four reviewed append archives are reopened here. Older31 payloads
remain historical metadata/hash references; this is not a full archive audit.
No Drive, model, training, global-state or old-catalog writes.
"""
from pathlib import Path
import json
from math_data_portable_resume import file_hash,save
from sgk_remaining_union_recipe import verified_bundle
import math_data_candidate_stream as C

HERE=Path(__file__).resolve().parent
RUN=HERE/'cloud_publication/sgk_completion_20261021'
APPENDS=[('sgk_finish_20261020',94,376),
         ('sgk_remaining_20261020',36,144),
         ('sgk_final_forms_20261020',18,72),
         ('sgk_completion_20261021',36,144)]
EXPECTED_ARTIFACTS=35
EXPECTED_CHAT_MEMBERS=29
EXPECTED_CANDIDATE_ROWS=6501780
EXPECTED_RAW_ROWS=6501828
CURRENT_PEDAGOGY_EVAL_ROWS=48

def compile_union(base,refs,manifests):
    """Compile already verified descriptors, refuse partial/wrong-size union."""
    if len(base.get('artifacts',{}))!=31:
        raise ValueError('Expected historical31-artifact catalog; do not infer a replacement catalog')
    if len(refs)!=4 or len({r['bundle']['sha256'] for r in refs})!=4:
        raise ValueError('Exactly four distinct reviewed append descriptors required')
    recipe=C.build_recipe([base],refs,manifests)
    if recipe['pending_discovery']:
        raise ValueError('Candidate discovery unresolved; refusing partial union')
    if len(recipe['artifacts'])!=EXPECTED_ARTIFACTS or len(recipe['chat_members'])!=EXPECTED_CHAT_MEMBERS:
        raise ValueError('Union artifact/chat-member counts differ from35/29')
    if recipe['raw_candidate_chat_rows_including_declared_current_splits']!=EXPECTED_RAW_ROWS:
        raise ValueError('Union raw declared chat count differs from6501828')
    if sum(r['cases'] for r in refs)!=184 or sum(r['chat_rows'] for r in refs)!=736:
        raise ValueError('Reviewed append source/chat counts differ from184/736')
    if EXPECTED_CANDIDATE_ROWS+CURRENT_PEDAGOGY_EVAL_ROWS!=EXPECTED_RAW_ROWS:
        raise ValueError('Declared candidate/current-eval accounting inconsistent')
    recipe.update(declared_candidate_chat_rows=EXPECTED_CANDIDATE_ROWS,
        current_pedagogy_validation_test_rows_separate=CURRENT_PEDAGOGY_EVAL_ROWS,
        historical_split_totals_pending_full_archive_audit=True,
        actual_train_only_row_total_verified=False,
        full_archive_audit_complete=False,training_started=False)
    return recipe

def main():
    # Must precede any reads or output: never invent a new bundle ID/proof.
    if not (RUN/'bundle_remote_verified.json').is_file():
        raise ValueError('Run only AFTER RUN5 bundle_remote_verified.json exists; no publication proof fabricated')
    basepath=HERE/'cloud_publication/sgk_finish_20261020/portable_resume/member_catalog_discovered.json'
    basehash=file_hash(basepath);base=json.loads(basepath.read_text('utf-8'))
    refs=[];manifests={};proofs=[]
    for directory,cases,chats in APPENDS:
        # verified_bundle checks local wholeZIP bytes/SHA against published
        # full-raw receipt, hashes every manifest member, then verifies exact
        # source row -> chat hash, actual prompt/target fields, split and4modes.
        ref,manifest,evidence=verified_bundle(HERE/'cloud_publication'/directory,cases,chats)
        refs.append(ref);manifests[ref['bundle']['sha256']]=manifest;proofs.append(evidence)
    recipe=compile_union(base,refs,manifests)
    recipe['verification_scope']=dict(
        old31_payloads='HISTORICAL_PINNED_METADATA_REFERENCES_NOT_FRESH_RAW_VERIFIED_HERE',
        four_reviewed_appends=proofs,all35_payloads_fresh_raw_verified=False,
        earlier_range_directory_observation_not_full_payload_SHA=True)
    dest=RUN/'publish_latest_union_recipe.json';save(dest,recipe)
    scope=dict(schema='MathVisionKid.latest_union_publication_scope.v1',
        file=dest.name,sha256=file_hash(dest),bytes=dest.stat().st_size,
        payload_references=EXPECTED_ARTIFACTS,chat_members=EXPECTED_CHAT_MEMBERS,
        source_members=len(recipe['source_members']),
        declared_candidate_chat_rows=EXPECTED_CANDIDATE_ROWS,
        declared_raw_chat_rows=EXPECTED_RAW_ROWS,
        current_pedagogy_eval_rows_separate=CURRENT_PEDAGOGY_EVAL_ROWS,
        historical_split_totals_pending_full_archive_audit=True,
        actual_train_only_row_total_verified=False,
        reviewed_append_source_rows_verified=184,
        reviewed_append_train_chat_rows_verified=736,
        old31_historical_metadata_only=True,all35_fresh_raw_verified=False,
        accepted_append_proofs=proofs,old_catalog_sha256=basehash,
        recipe_outside_bundle_to_avoid_self_hash_circularity=True,
        full_archive_audit_complete=False,training_started=False,
        drive_mutated_by_helper=False,global_state_mutated_by_helper=False)
    save(RUN/'root_evidence/latest_union_scope.json',scope)
    if file_hash(basepath)!=basehash:raise ValueError('Historical catalog changed during union publication')
    print(json.dumps({k:v for k,v in scope.items() if k!='accepted_append_proofs'}))

if __name__=='__main__':main()
