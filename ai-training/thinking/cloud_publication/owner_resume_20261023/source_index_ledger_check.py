"""Read only source-index counts; no questions, answers, or dataset mutations."""
import json,sqlite3,hashlib
from datetime import datetime,timezone
with sqlite3.connect(V3_DB.as_uri()+'?mode=ro',uri=True,timeout=30) as db:
    db.execute('PRAGMA query_only=ON')
    source_members,complete,physical=db.execute("SELECT count(*),sum(complete),sum(next_line) FROM members WHERE role='candidate_source'").fetchone()
    versions=db.execute('SELECT count(*) FROM source_versions').fetchone()[0]
    duplicate_ids=db.execute('SELECT count(*) FROM (SELECT id FROM source_versions GROUP BY id HAVING count(*)<>1)').fetchone()[0]
    issues=dict(db.execute('SELECT kind,count(*) FROM issues GROUP BY kind'))
db.close()
declared=sum(e['rows'] for e in recipe_all['source_members'])
assert source_members==complete==219 and declared==physical==versions==1629906
assert duplicate_ids==0
receipt={'schema':'MathVisionKid.source_index_ledger_check.v1','observed_utc':datetime.now(timezone.utc).isoformat(),
         'source_members_complete':complete,'declared_source_physical_rows':declared,'indexed_source_versions':versions,
         'source_ids_with_multiple_versions':duplicate_ids,'physical_minus_indexed_source_versions':physical-versions,
         'historical_accepted_counter':state['accepted_cases'],'historical_counter_difference':state['accepted_cases']-versions,
         'historical_difference_cause_proven':False,'historical_counter_not_rewritten':True,
         'read_only':True,'question_answer_content_read':False,'training_started':False,'issues_at_observation':issues}
(resume_dir/'source_index_ledger_receipt.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps(receipt))
