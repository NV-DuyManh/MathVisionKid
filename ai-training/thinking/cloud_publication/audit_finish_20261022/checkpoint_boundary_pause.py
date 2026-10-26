# Cooperative pause only at a checkpoint whose committed cursors also match.
# This installs the controller; requesting a pause is a separate explicit cell.
import hashlib,json,sqlite3
assert globals().get('_mathvision_pause_controller_installed',False)
assert audit_v3.FullArchiveAudit.consume in (
    _mathvision_checkpoint_boundary_consume,
    globals().get('_mathvision_checkpoint_boundary_consume_v2'))

def _mathvision_checkpoint_boundary_consume_v2(self,entry,path,*args,**kwargs):
    if _mathvision_pause_requested:
        verified=full_audit_worker_state.get('checkpoint')
        if verified and verified.get('fresh_raw_readback_verified') and self.report()==verified['report_at_snapshot']:
            snapshot_path=ROOT/'full_audit_v3_snapshot.sqlite'
            with sqlite3.connect(snapshot_path.as_uri()+'?mode=ro',uri=True) as snapshot_check:
                query='SELECT id,role,next_line,complete,expected_rows FROM members ORDER BY id'
                saved_cursors=snapshot_check.execute(query).fetchall()
            current_cursors=self.db.execute(query).fetchall()
            if current_cursors==saved_cursors:
                cursor_digest=hashlib.sha256(json.dumps(saved_cursors,separators=(',',':')).encode()).hexdigest()
                full_audit_worker_state['pause_receipt']={
                    'checkpoint_sha256':verified['sha256'],
                    'committed_members_equal_verified_snapshot':True,
                    'member_cursors_sha256':cursor_digest,
                    'member_cursor_count':len(saved_cursors),
                    'working_database_byte_identity_claimed':False,
                    'safe_resume_source':'RAW_VERIFIED_SNAPSHOT',
                    'training_started':False}
                full_audit_worker_state['state']='PAUSED_AT_VERIFIED_CHECKPOINT_FOR_VALIDATED_PERFORMANCE_UPGRADE'
                full_audit_worker_state['pause_reason']='Exact batched tokenization and fewer large checkpoint copies; no data changes.'
                write_worker_status()
                raise SystemExit('Cooperative pause at verified snapshot with equal committed cursors')
    return _mathvision_original_consume(self,entry,path,*args,**kwargs)

audit_v3.FullArchiveAudit.consume=_mathvision_checkpoint_boundary_consume_v2
print({'pause_controller_version':2,'pause_requested':_mathvision_pause_requested,
       'requires_equal_committed_member_cursors':True,'training_started':False})
