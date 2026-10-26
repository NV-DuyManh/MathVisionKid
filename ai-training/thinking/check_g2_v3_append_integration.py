"""Actual 64-case V3 integration plus append migration fixture checks.

Temporary local databases are bounded fixtures, never the cloud checkpoint.
No corpus download, generated cases, benchmark reads, training or weights.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from copy import deepcopy
from datetime import datetime, timezone
import hashlib,json,sqlite3,sys
H=Path(__file__).resolve().parent
R=H/'cloud_publication/antigravity_intake_20261022'
OUT=H/'cloud_publication/resume_after_g2_20261022'
sys.path.insert(0,str(H))
import math_data_full_audit_v3 as V
import exhaustive_colab_loader as L
from math_data_candidate_stream import member_key
from transformers import AutoTokenizer

def sha(b):return hashlib.sha256(b).hexdigest()
def tables(db):
    return {t:list(db.execute('SELECT * FROM '+t+' ORDER BY 1,2')) for t in
        ['members','source_versions','samples','occurrences','split_keys','issues']}
def main():
    bundle=json.loads((R/'bundle_remote_verified.json').read_text(encoding='utf8'))
    path=R/'derived_g2_repair_append.zip'
    assert sha(path.read_bytes())==bundle['sha256']
    manifest=json.loads((R/'manifest.json').read_text(encoding='utf8'))
    entries={}
    for role,name in [('candidate_source','accepted_cases.jsonl'),('candidate_chat','accepted_chat.jsonl')]:
        m=manifest['entries'][name]
        entries[role]=dict(role=role,member=name,member_bytes=m['bytes'],member_sha256=m['sha256'],
            rows=m['rows'],file_id=bundle['id'],file_name=bundle['file_name'],sha256=bundle['sha256'],bytes=bundle['bytes'])
    recipe=dict(source_members=[entries['candidate_source']],chat_members=[entries['candidate_chat']],pending_discovery=[])
    tokenizer=AutoTokenizer.from_pretrained(L.MODEL,revision=L.REVISION,local_files_only=True)
    with TemporaryDirectory(prefix='mvk_bounded_v3_') as tmp:
        dbpath=Path(tmp)/'bounded_actual64.sqlite'
        audit=V.FullArchiveAudit(dbpath,recipe,tokenizer)
        try:
            # Small work spans deliberately exercise exact resume cursors.
            for role in ['candidate_source','candidate_chat']:
                while True:
                    result=audit.consume(entries[role],path,max_rows=17,commit_every=7)
                    if result.get('complete') or result.get('already_complete'):break
            report=audit.report()
            assert report['unique_chat_rows_processed']==256
            assert report['source_versions_indexed']==64
            assert report['issues']=={} and report['source_linkage_unverified_rows']==0
            assert report['incomplete_four_mode_cases']==0
            assert report['full_archive_token_linkage_split_audit_complete']
            assert report['max_sequence_tokens']==1193
        finally:audit.close()
        old=json.loads((R/'parent_union_recipe.json').read_text(encoding='utf8'))
        new=json.loads((R/'publish_latest_union_recipe.json').read_text(encoding='utf8'))
        fixture=Path(tmp)/'metadata_fixture.sqlite'
        a=V.FullArchiveAudit(fixture,old,tokenizer)
        # These are synthetic diagnostic rows, not actual checkpoint evidence.
        a.db.execute('INSERT INTO members VALUES (?,?,?,?,?)',('fixture_cursor','candidate_chat',123,0,999))
        a.db.execute('INSERT INTO issues VALUES (?,?,?,?)',('fixture',7,'DIAGNOSTIC_MUST_SURVIVE','synthetic preserved issue'))
        a.db.execute('INSERT INTO split_keys VALUES (?,?,?)',('question','synthetic key','test'))
        a.db.commit();before=tables(a.db);a.close()
        p=V.FullArchiveAudit.extend_recipe(fixture,old,new)
        a=V.FullArchiveAudit(fixture,new,tokenizer)
        assert tables(a.db)==before
        assert p['previous_identity']==V.plan_identity(old) and p['next_identity']==V.plan_identity(new)
        assert a.db.execute('SELECT count(*) FROM recipe_history').fetchone()[0]==1
        a.close()
        bad=deepcopy(new);bad['source_members'][0],bad['source_members'][1]=bad['source_members'][1],bad['source_members'][0]
        try:V.FullArchiveAudit.extend_recipe(fixture,new,bad)
        except ValueError:reordered_refused=True
        else:raise AssertionError('Reordered source prefix accepted')
        a=V.FullArchiveAudit(fixture,new,tokenizer);assert tables(a.db)==before;a.close()
        # Wrong identity must fail before altering fixture configuration.
        try:V.FullArchiveAudit.extend_recipe(fixture,old,new)
        except ValueError:stale_refused=True
        else:raise AssertionError('Stale old identity accepted')
        a=V.FullArchiveAudit(fixture,new,tokenizer);assert tables(a.db)==before;a.close()
    evidence=dict(schema='MathVisionKid.BoundedG2V3Integration.v1',
        observed_utc=datetime.now(timezone.utc).isoformat(),actual_bundle_sha256=bundle['sha256'],
        actual_source_rows=64,actual_chat_rows=256,bounded_actual_report=report,
        bounded_audit_is_full_expanded_archive=False,
        migration_tests=dict(parent_and_child_recipe_identities_bound=True,
            all_existing_fixture_tables_unchanged=True,issue_and_cursor_preserved=True,
            reordered_prefix_refused=reordered_refused,stale_identity_refused=stale_refused,
            temporary_fixture_deleted=True),
        actual_cloud_checkpoint_modified=False,training_started=False,model_weights_loaded=False,
        skills_applied=['google-drive:google-drive'],code_sha256=sha(Path(__file__).read_bytes()))
    OUT.mkdir(exist_ok=True)
    (OUT/'bounded_g2_v3_integration.json').write_bytes((json.dumps(evidence,ensure_ascii=False,indent=2)+'\n').encode())
    print(json.dumps(dict(actual64_V3_passed=True,chats=256,issues=report['issues'],max_tokens=report['max_sequence_tokens'],
        append_migration_fixture_passed=True,actual_cloud_checkpoint_modified=False,training_started=False)))
if __name__=='__main__':main()
