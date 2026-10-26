# Metadata-only source/exclusion evidence; do not print question/answer content.
import sqlite3,json
from datetime import datetime,timezone
diagnostic_id='exhaustive_v1_div_1563_43'
diagnostic_db=sqlite3.connect(V3_DB.as_uri()+'?mode=ro',uri=True,timeout=3)
try:
    diagnostic_versions=diagnostic_db.execute('SELECT raw_sha,canonical_sha,source_split FROM source_versions WHERE id=?',(diagnostic_id,)).fetchall()
    diagnostic_occurrences=diagnostic_db.execute('SELECT split,count(*) FROM samples WHERE case_id=? GROUP BY split',(diagnostic_id,)).fetchall()
    diagnostic_complete=diagnostic_db.execute('SELECT role,count(*) FROM members WHERE complete=1 GROUP BY role').fetchall()
    print({'observed_utc':datetime.now(timezone.utc).isoformat(),'sample_id':diagnostic_id,
           'source_versions_metadata':diagnostic_versions,'chat_links_by_split_so_far':diagnostic_occurrences,
           'completed_members_by_role':diagnostic_complete,'zero_links_is_final_proof':False,
           'source_content_read':False,'training_started':False})
finally:
    diagnostic_db.close()
