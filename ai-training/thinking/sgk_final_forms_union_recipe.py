"""Publish a hash-pinned union after verified18 append. Data only."""
from pathlib import Path
from collections import Counter
import json
from math_data_portable_resume import file_hash,save
from sgk_remaining_union_recipe import verified_bundle
import math_data_candidate_stream as C
HERE=Path(__file__).resolve().parent
RUN=HERE/'cloud_publication/sgk_final_forms_20261020'
def main():
    basepath=HERE/'cloud_publication/sgk_finish_20261020/portable_resume/member_catalog_discovered.json'
    base=json.loads(basepath.read_text('utf-8'));basehash=file_hash(basepath)
    refs=[];manifests={};proofs=[]
    for directory,cases,chats in [('sgk_finish_20261020',94,376),('sgk_remaining_20261020',36,144),('sgk_final_forms_20261020',18,72)]:
        ref,manifest,evidence=verified_bundle(HERE/'cloud_publication'/directory,cases,chats)
        refs.append(ref);manifests[ref['bundle']['sha256']]=manifest;proofs.append(evidence)
    recipe=C.build_recipe([base],refs,manifests)
    assert len(recipe['artifacts'])==34 and len(recipe['chat_members'])==28 and not recipe['pending_discovery']
    assert recipe['raw_candidate_chat_rows_including_declared_current_splits']==6501684
    recipe.update(declared_candidate_chat_rows=6501636,current_pedagogy_validation_test_rows_separate=48,historical_split_totals_pending_full_archive_audit=True,actual_train_only_row_total_verified=False)
    recipe['verification_scope']=dict(old31_payloads='HISTORICAL_PINNED_REFERENCES_NOT_FRESH_RAW_VERIFIED',three_reviewed_appends=proofs,all34_payloads_fresh_raw_verified=False)
    dest=RUN/'publish_latest_union_recipe.json';save(dest,recipe)
    scope=dict(schema='MathVisionKid.latest_union_publication_scope.v1',sha256=file_hash(dest),bytes=dest.stat().st_size,payload_references=34,chat_members=28,source_members=len(recipe['source_members']),declared_candidate_chat_rows=6501636,declared_raw_chat_rows=6501684,current_pedagogy_eval_rows_separate=48,historical_split_totals_pending_full_archive_audit=True,actual_train_only_row_total_verified=False,all34_fresh_raw_verified=False,old31_historical_metadata_only=True,accepted_append_proofs=proofs,full_archive_audit_complete=False,training_started=False)
    save(RUN/'root_evidence/latest_union_scope.json',scope)
    assert file_hash(basepath)==basehash
    print(json.dumps({k:v for k,v in scope.items() if k!='accepted_append_proofs'}))
if __name__=='__main__':main()
