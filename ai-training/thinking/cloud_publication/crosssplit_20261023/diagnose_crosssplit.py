import json,sqlite3,hashlib
from datetime import datetime,timezone
assert str(V3_DB).startswith('/content/mathvisionkid_data_only/')
with sqlite3.connect(V3_DB.as_uri()+'?mode=ro',uri=True,timeout=30) as d:
 d.execute('PRAGMA query_only=ON')
 rows=[dict(zip(('member','line','kind','detail'),x)) for x in d.execute("SELECT member,line,kind,detail FROM issues WHERE kind LIKE 'CROSS_SPLIT_%' ORDER BY member,line,kind,detail")]
 out=[]
 for x in rows:
  q=d.execute('SELECT s.id,s.case_id,s.mode,s.split,s.source_raw_sha,s.canonical_sha,o.raw_sha FROM occurrences o JOIN samples s ON s.id=o.sample_id WHERE o.member=? AND o.line=?',(x['member'],x['line'])).fetchall()
  x['sample_metadata']=[dict(zip(('sample_id','case_id','mode','split','source_raw_sha256','chat_canonical_sha256','chat_raw_sha256'),y)) for y in q]
  out.append(x)
 result={'observed_utc':datetime.now(timezone.utc).isoformat(),'diagnostics':out,'question_or_solution_text_read':False,'data_mutated':False,'training_started':False}
print(json.dumps(result,ensure_ascii=False))
