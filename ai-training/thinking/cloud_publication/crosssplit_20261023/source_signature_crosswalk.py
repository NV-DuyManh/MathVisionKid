import json,sqlite3,hashlib,collections
from datetime import datetime,timezone
with sqlite3.connect(V3_DB.as_uri()+'?mode=ro',uri=True,timeout=30) as d:
 d.execute('PRAGMA query_only=ON')
 targets={x[0] for x in d.execute("SELECT DISTINCT detail FROM issues WHERE kind='CROSS_SPLIT_CANONICAL'")}
 matches=[];counts=collections.Counter()
 for sid,raw,canon,split,sigs in d.execute('SELECT id,raw_sha,canonical_sha,source_split,signatures FROM source_versions'):
  overlaps=sorted(targets.intersection(json.loads(sigs)))
  if not overlaps:continue
  counts[str(split)]+=1
  assert len(matches)<2000,'Bounded metadata limit exceeded; preserve counter evidence separately'
  samples=[dict(zip(('sample_id','mode','split','canonical_sha256'),x)) for x in d.execute('SELECT id,mode,split,canonical_sha FROM samples WHERE case_id=? AND source_raw_sha=?',(sid,raw))]
  matches.append({'case_id':sid,'raw_sha256':raw,'canonical_sha256':canon,'source_split':split,'overlapping_signatures':overlaps,'linked_samples':samples})
 result={'observed_utc':datetime.now(timezone.utc).isoformat(),'targets':sorted(targets),'source_match_counts_by_split':dict(counts),'matches':matches,'question_or_solution_text_read':False,'data_mutated':False,'training_started':False}
 out=ROOT/'crosssplit_20261023';out.mkdir(exist_ok=True)
 b=(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode();(out/'signature_crosswalk.json').write_bytes(b)
 print(json.dumps(result,ensure_ascii=False))
