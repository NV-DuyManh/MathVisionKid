"""Precise root-requested single-field repair; preserve exact parent bytes."""
from pathlib import Path
import json,hashlib
from exhaustive_primary_math import dumps
P=Path(__file__).parent/'cloud_publication/sgk_finish_20261020/g34_network_text'
SID='sgk_finish_network_20261020_guard_unknown_eligible_set'
OLD='Giữ nhận xét ở mức chưa xác định cho đến khi có đúng phần luật thiếu.'
NEW='Đối chiếu phần luật cần hỏi với điều kiện dừng, không tự bổ sung quy tắc.'
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
parent=P/'parent_before_hint_repair';parent.mkdir(exist_ok=True)
for name in ['cases.jsonl','chat.jsonl','selfqa7.jsonl','independent_oracles.jsonl','manifest.json']:
 b=(P/name).read_bytes();dst=parent/name
 if dst.exists():assert dst.read_bytes()==b,'Repair already executed; do not run twice'
 else:dst.write_bytes(b)
cases=(P/'cases.jsonl').read_bytes().splitlines();before=[json.loads(b) for b in cases]
i=next(i for i,r in enumerate(before) if r['sample_id']==SID);r=json.loads(cases[i]);assert r['hints'][2]['hint']==OLD
oldrowhash=sha(cases[i]);r['hints'][2]['hint']=NEW;cases[i]=dump(r).encode();newrowhash=sha(cases[i])
def diff(a,b,path=''):
 if type(a)!=type(b):return [path]
 if isinstance(a,dict):return [p for k in a for p in diff(a[k],b[k],path+'.'+k)]
 if isinstance(a,list):
  assert len(a)==len(b);return [p for j in range(len(a)) for p in diff(a[j],b[j],path+f'[{j}]')]
 return [] if a==b else [path.lstrip('.')]
changes=diff(before[i],r);assert changes==['hints[2].hint']
(P/'cases.jsonl').write_bytes(b'\n'.join(cases)+b'\n')
qals=(P/'selfqa7.jsonl').read_bytes().splitlines()
for j,b in enumerate(qals):
 q=json.loads(b)
 if q['sample_id']==SID:
  assert q['source_row_sha256']==oldrowhash;q['source_row_sha256']=newrowhash;q['actual_fields']['hints'][2]['hint']=NEW;qals[j]=dump(q).encode()
(P/'selfqa7.jsonl').write_bytes(b'\n'.join(qals)+b'\n')
chatls=(P/'chat.jsonl').read_bytes().splitlines();chatdiff=[]
for j,b in enumerate(chatls):
 c=json.loads(b)
 if c['source_sample_id']!=SID:continue
 original=json.loads(b);assert c['source_row_sha256']==oldrowhash;c['source_row_sha256']=newrowhash
 if c['mode']=='hint_level_3':
  target=json.loads(c['messages'][2]['content']);assert target['hint']==OLD;target['hint']=NEW;c['messages'][2]['content']=dumps(target)
 chatls[j]=dump(c).encode();chatdiff.append(dict(sample_id=c['sample_id'],fields=diff(original,c)))
(P/'chat.jsonl').write_bytes(b'\n'.join(chatls)+b'\n')
ols=(P/'independent_oracles.jsonl').read_bytes().splitlines()
for j,b in enumerate(ols):
 o=json.loads(b)
 if o['sample_id']==SID:o.update(source_row_sha256=newrowhash,math_oracle_unchanged_after_hint_only_repair=True);ols[j]=dump(o).encode()
(P/'independent_oracles.jsonl').write_bytes(b'\n'.join(ols)+b'\n')
# Keep the authoring helper aligned without regenerating any data or comparisons.
helper=Path(__file__).parent/'sgk_finish_network_text_append.py';hb=helper.read_bytes();assert hb.count(OLD.encode())==1;helper.write_bytes(hb.replace(OLD.encode(),NEW.encode()))
delta=dict(sample_id=SID,parent_cases_sha256=sha((parent/'cases.jsonl').read_bytes()),parent_chat_sha256=sha((parent/'chat.jsonl').read_bytes()),parent_source_row_sha256=oldrowhash,final_source_row_sha256=newrowhash,source_changed_fields=changes,old_hint=OLD,new_hint=NEW,problem_givens_request_initial_steps_answers_unchanged=True,unaffected_case_rows_byte_identical=11,unaffected_chat_rows_byte_identical=44,chat_changes=chatdiff,final_cases_sha256=sha((P/'cases.jsonl').read_bytes()),final_chat_sha256=sha((P/'chat.jsonl').read_bytes()),reason='Root full-field review requested procedural hint without supplying final unknown-status label.',acceptance_status='DRAFT_PENDING_ROOT_RECHECK_CHANGED_HINT')
(P/'hint_repair_delta.json').write_text(json.dumps(delta,ensure_ascii=False,indent=2)+'\n','utf-8')
m=json.loads((parent/'manifest.json').read_text('utf-8'))
for entry in m['manifest']:
 b=(P/entry['path']).read_bytes();entry['bytes']=len(b);entry['sha256']=sha(b)
entry=dict(path='hint_repair_delta.json',bytes=(P/'hint_repair_delta.json').stat().st_size,sha256=sha((P/'hint_repair_delta.json').read_bytes()),rows=None);m['manifest'].append(entry)
m['hint_repair']=dict(source_changed_fields=changes,delta_file='hint_repair_delta.json',root_recheck_pending=True)
(P/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n','utf-8')
for old,new in zip(before,[json.loads(b) for b in (P/'cases.jsonl').read_bytes().splitlines()]):
 assert diff(old,new)==(['hints[2].hint'] if old['sample_id']==SID else [])
for c in [json.loads(b) for b in (P/'chat.jsonl').read_bytes().splitlines()]:
 if c['source_sample_id']==SID:assert c['source_row_sha256']==newrowhash
for e in m['manifest']:assert sha((P/e['path']).read_bytes())==e['sha256']
print(dump(delta|{'manifest_sha256':sha((P/'manifest.json').read_bytes())}))
