"""Record verified publication before bounded staging cleanup. No Drive writes."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,zipfile,shutil

HERE=Path(__file__).resolve().parent
RUN=HERE/'cloud_publication/sgk_page_audit_20261019'
DEST=HERE/'cloud_publication/sgk_page_audit_20261020_publication_receipt.json'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text('utf-8'))
def main():
    bundle=read(RUN/'bundle_remote_verified.json');controls=read(RUN/'four_controls_remote_verified.json')
    assert bundle['fresh_raw_verified'] and bundle['all_bytes_equal']
    assert len(controls)==4 and all(r['fresh_raw_verified'] and r['all_bytes_equal'] for r in controls)
    local=read(RUN/'bundle_local.json');report=read(RUN/'release/audit_report.json')
    assert sha(Path(local['path']).read_bytes())==bundle['sha256']
    with zipfile.ZipFile(local['path']) as archive:
        manifest=json.loads(archive.read('manifest.json'));assert not archive.testzip()
        for name,ref in manifest['members'].items():
            b=archive.read(name);assert len(b)==ref['bytes'] and sha(b)==ref['sha256']
        assert len(archive.read(manifest['source_member']).splitlines())==110
        assert len(archive.read(manifest['chat_member']).splitlines())==440
        assert 'data/g2v2_audit/g2_combined_candidate_adjudication.json' in manifest['members']
    with zipfile.ZipFile(RUN/'source_progress_index.zip') as old,zipfile.ZipFile(RUN/'publish_progress_index.zip') as new:
        assert all(old.read(n)==new.read(n) for n in old.namelist())
        old_progress_members=len(old.namelist())
    frozen=read(RUN/'release/preservation_frozen_local.json')
    for name,ref in frozen.items():
        b=(HERE/'data/primary_math_teacher_20261016'/name).read_bytes()
        assert len(b)==ref['bytes'] and sha(b)==ref['sha256']
    state=read(RUN/'publish_state.json')
    assert state['accepted_cases']==1629597 and state['training_chat_rows']==6501044
    assert state['all_available_chat_rows_including_evaluation_and_audit']==6501156
    assert not state['TRAINING_DATASET_READY']
    shutil.copyfile(RUN/'publish_state.json',HERE/'exhaustive_cloud_reference.json')
    result=dict(schema='verified_finite_sgk_page_publication.v1',published_utc=datetime.now(timezone.utc).isoformat(),bundle=bundle,controls=controls,prewrite_fresh_control_check=read(RUN/'prewrite_fresh_control_check.json'),accepted_cases=state['accepted_cases'],candidate_training_chat_rows=state['training_chat_rows'],all_available_chat_rows_including_evaluation_and_audit=state['all_available_chat_rows_including_evaluation_and_audit'],new_batch=report,old_progress_members_byte_preserved=old_progress_members,old_frozen_local_files_unchanged=frozen,core_coverage='495/495 cases;165/165 nodes unchanged',page_checkpoint=state['actual_sgk_page_checkpoint'],candidate_mapping_resume=state['candidate_mapping_resume'],archive_member_hashes_verified=len(manifest['members']),temporary_staging=dict(path=str(RUN),status='READY_TO_DELETE_ONLY_THIS_VERIFIED_RUN',files=sum(p.is_file() for p in RUN.rglob('*')),bytes=sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file())),training_started=False,full_sgk_semantic_coverage_complete=False,full_archive_token_split_audit_complete=False)
    DEST.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(receipt=str(DEST),new_cases=110,new_chat=440,old_progress_members=old_progress_members,staging_bytes=result['temporary_staging']['bytes'],ready_for_bounded_cleanup=True)))
if __name__=='__main__':main()
