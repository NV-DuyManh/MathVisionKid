from pathlib import Path
import base64, hashlib, json

P=Path(__file__).parent
def read(n): return json.loads((P/n).read_bytes())
def sha(b): return hashlib.sha256(b).hexdigest()
frozen={x['fixture_id']:x for x in read('baseline_semantic_review_frozen.json')['records']}
pairs=read('review_step_000100/paired_g123.json')+read('review_step_000100/paired_g45.json')
byid={x['fixture']['id']:x for x in pairs}
decisions=read('root_candidate_prefix6_review.json')['decisions']
for name in ['independent_candidate_middle12_review.json','independent_candidate_last12_review.json']:
 for r in read(name)['records']:
  fid=r['fixture_id']; b=frozen[fid]; pair=byid[fid]
  assert sha(pair['adapter']['output'].encode())==r['output_sha256']
  assert b['base_pass']==r['baseline_pass'] and b['base_hint_leak']==r['baseline_hint_leak']
  decisions.append({'fixture_id':fid,'grade':r['grade'],'mode':r['mode'],
   'base_pass':r['baseline_pass'],'base_hint_leak':r['baseline_hint_leak'],
   'adapter_pass':r['full_task_pass'],'adapter_hint_leak':r['hint_leak'],
   'critical_new_error':r['critical_new_error'],'base_reason':b['reason'],
   'adapter_reason':r['reason'],'base_output_sha256':sha(pair['base']['output'].encode()),
   'adapter_output_sha256':r['output_sha256']})
for d in decisions:
 pair=byid[d['fixture_id']]
 assert sha(pair['base']['output'].encode())==d['base_output_sha256']
 assert sha(pair['adapter']['output'].encode())==d['adapter_output_sha256']
 if d['fixture_id']=='dev25_g5_answer_01':
  d['critical_new_error']=False
  d['adapter_reason']='Computes the removed quantity as 24 × 3/8 = 9, and explicitly calls it the part taken out. The initial check label mentions remaining water but never asserts 9 is the remainder; root does not count a new false arithmetic claim. The response still omits the requested litre unit and a meaningful verification, so full-task fail.'
 if d['fixture_id']=='dev25_g4_answer_01':
  d['adapter_reason']='Contradictory quantity answers: first says 10/12 m, then correctly derives 9/12 = 3/4 m. The false intermediate answer is a new arithmetic error; correct final line does not remove it.'
doc={'schema':'MathVisionKid.root_paired_semantic_review.v1','step':100,'decision':'STOP',
 'all_actual_outputs_reviewed':True,'human_review_claimed':False,
 'root_has_read_all_actual_problem_rubric_base_and_candidate_outputs':True,
 'review_scope':'All 30 completed development pairs. Development has been used for tuning and is not an unseen generalization estimate. Preserve source data and diagnostic checkpoint; keep base selected.',
 'independent_reviews_sha256':{n:sha((P/n).read_bytes()) for n in ['independent_candidate_prefix6_review.json','independent_candidate_middle12_review.json','independent_candidate_last12_review.json']},
 'decisions':decisions}
out=P/'root_paired_decisions_step_000100.json'
if out.exists(): raise FileExistsError(out)
out.write_bytes((json.dumps(doc,ensure_ascii=False,indent=2)+'\n').encode())
payload={n:base64.b64encode((P/n).read_bytes()).decode() for n in ['root_paired_decisions_step_000100.json','build_quality_gate_20261026.py']}
code='''from pathlib import Path
import base64,hashlib,json,subprocess
root=Path('/content/mathvisionkid_recovery_20261026')
payload=PAYLOAD
for name,encoded in payload.items():
 raw=base64.b64decode(encoded); path=root/name
 if path.exists():
  assert path.read_bytes()==raw, 'refuse changed existing file: '+name
 else: path.write_bytes(raw)
result=subprocess.run([str(root/'venv/bin/python'),str(root/'build_quality_gate_20261026.py'),'--root',str(root),'--decisions',str(root/'root_paired_decisions_step_000100.json'),'--step','100'],capture_output=True,text=True,timeout=30)
print(json.dumps({'returncode':result.returncode,'stdout':result.stdout[-6000:],'stderr':result.stderr[-3000:]}))
assert result.returncode==0
'''.replace('PAYLOAD',repr(payload))
(P/'publish_root_gate_runtime.py').write_bytes(code.encode())
print(json.dumps({'decisions':len(decisions),'passes':sum(x['adapter_pass'] for x in decisions),'critical':sum(x['critical_new_error'] for x in decisions),'root_review_sha256':sha(out.read_bytes())}))
