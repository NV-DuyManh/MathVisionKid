import json,sqlite3
from datetime import datetime,timezone
with sqlite3.connect(V3_DB.as_uri()+'?mode=ro',uri=True,timeout=30) as _d:
 _d.execute('PRAGMA query_only=ON')
 _issues=[dict(zip(('member','line','kind','case_id'),x)) for x in _d.execute("SELECT member,line,kind,detail FROM issues WHERE kind<>'SOURCE_SPLIT_MISSING_OR_UNKNOWN' ORDER BY member,line,kind LIMIT 300")]
 _ids=sorted({x['case_id'] for x in _issues})
 _sources={x:list(_d.execute('SELECT raw_sha,source_split,adapter_kind,original_source_sha FROM source_versions WHERE id=?',(x,))) for x in _ids}
 _counts=dict(_d.execute('SELECT kind,count(*) FROM issues GROUP BY kind'))
_d.close()
_entries={batch_module.member_key(x):x for x in recipe_all['source_members']+recipe_all['chat_members']}
new_linkage_diagnostic={'observed_utc':datetime.now(timezone.utc).isoformat(),'read_only':True,'issues':_issues,'issue_counts':_counts,'source_metadata_by_id':_sources,'members':{m:_entries.get(m) for m in sorted({x['member'] for x in _issues})},'training_started':False}
(resume_dir/'new_linkage_diagnostic.json').write_text(json.dumps(new_linkage_diagnostic,ensure_ascii=False,indent=2))
print(json.dumps(new_linkage_diagnostic,ensure_ascii=False))
