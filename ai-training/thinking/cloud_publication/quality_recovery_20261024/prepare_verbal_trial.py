from pathlib import Path
import json,hashlib,base64,shutil
p=Path(__file__).parent;q=p.parent/'verbal_recovery_20261024';q.mkdir(exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
source=(p/'recovery_worker.py').read_bytes();assert sha(source)=='345ff9d1def663bca704b4ab47ea8828c9793964bf70fb5ed2b784517b494e29'
code=source.decode()
def once(old,new):
 global code
 assert code.count(old)==1,old;code=code.replace(old,new,1)
once("H=load(root/'frozen_training_primitives.py','qrec_frozen_primitives')", """H=load(root/'frozen_training_primitives.py','qrec_frozen_primitives')
 import verbal_training_renderer_v3 as V
 if sha(root/'verbal_training_renderer_v3.py')!='6b15233ae253eed7825864413edbdf3f8553ad955ef248e045c05f64e4473057':raise ValueError('verbal renderer changed')
 def verbal_fixture_messages(fixture):
  value={'grade':fixture['grade'],'problem':fixture['userproblem'],'mode':H.MODE_MAP[fixture['mode']]}
  return [{'role':'system','content':H.SYSTEM},{'role':'user','content':V.prompt(value)}]
 H.fixture_messages=verbal_fixture_messages""")
once("by_id={x['sample_id']:x for x in rows};selected=[by_id[x] for x in plan['schedule']]", """by_id={x['sample_id']:x for x in rows};selected=[by_id[x] for x in plan['schedule']]
 original={json.loads(b)['sample_id']:(json.loads(b),digest(b)) for b in (root/'training_view.jsonl').read_bytes().splitlines()}
 projected=[]
 for row in selected:
  source_row,source_raw_hash=original[row['sample_id']];rendered,proof=V.render(source_row)
  # The training-only object carries minimal required fields, not an inherited human attestation on changed bytes.
  neutral={k:source_row[k] for k in ('sample_id','case_group_id','mode','split')}
  neutral['messages']=rendered['messages']
  encoded=helper.tokenize_assistant_only(neutral,tok,max_sequence_tokens=2048);H.validate_encoded(encoded)
  row['encoded']=encoded
  projected.append({'sample_id':row['sample_id'],'source_original_raw_row_sha256':source_raw_hash,'prompt_sha256':digest(rendered['messages'][1]['content'].encode()),'target_sha256':digest(rendered['messages'][2]['content'].encode()),'semantic_field_count':len(proof['fields']),'completion_tokens':encoded['completion_tokens']})
 projection={'schema':'MathVisionKid.verbal_training_projection.v1','source_view_sha256':H.VIEW_SHA256,'source_plan_sha256':cfg['source_plan_sha256'],'renderer_sha256':sha(root/'verbal_training_renderer_v3.py'),'rows':projected,'source_rows_modified':False,'source_acceptance_labels_changed':False,'new_human_attestation':False,'source_case_count_added':0,'max_sequence_tokens':max(len(x['encoded']['input_ids']) for x in selected)}
 atomic(root/'verbal_projection_manifest.json',projection);cfg['verbal_projection_manifest_sha256']=sha(root/'verbal_projection_manifest.json');cfg['rendering']=V.VERSION;cfg['renderer_sha256']=sha(root/'verbal_training_renderer_v3.py')""")
once("'gate_steps':[50,100,200,300],'max_successful_updates':300", "'gate_steps':[50],'max_successful_updates':50")
once("'validation_scope':'fresh30 dev screened against actual16k; not full6.5M independent estimate'", "'validation_scope':'Reused development30 for representation iteration; prior locked20 is not read or reused; no new independent-test claim'")
once("'loss_reduction':'unchanged originalmicro2 supervised-token mean weighted pair_rows/group_rows'", "'loss_reduction':'unchanged originalmicro2 supervised-token mean weighted pair_rows/group_rows; source content reformatted through hash-pinned verbal renderer'")
compile(code,'verbal_recovery_worker.py','exec');(q/'recovery_worker.py').write_text(code,encoding='utf8')
pub=(p/'publisher_runtime.py').read_bytes();assert sha(pub)=='75d85e31a396e97779f06624b66709ece14c770b46d8f2392a1cd68c4dc7c184'
pub=pub.decode().replace('/content/mathvisionkid_quality_recovery_20261024','/content/mathvisionkid_verbal_recovery_20261024').replace('MathVisionKid_QUALITY_RECOVERY_20261024','MathVisionKid_VERBAL_RECOVERY_20261024').replace('MathVisionKidQualityRecoveryPublisher','MathVisionKidVerbalRecoveryPublisher').replace('_mathvisionkid_quality_recovery_publisher_registry','_mathvisionkid_verbal_recovery_publisher_registry')
pub=pub.replace("'cpu_validation.json']","'cpu_validation.json','verbal_training_renderer_v3.py','test_verbal_training_renderer_v3.py','verbal_projection_manifest.json','projection_preflight.json','trial_scope.json']")
compile(pub,'verbal_publisher.py','exec');(q/'publisher_runtime.py').write_text(pub,encoding='utf8')
for name in ['recovery_policy.py','frozen_code_references.json','verbal_training_renderer_v3.py','test_verbal_training_renderer_v3.py','test_recovery_worker.py','test_recovery_policy.py']:
 shutil.copyfile(p/name,q/name)
scope=json.loads((p/'owner_run_scope.json').read_bytes());scope.update(authorization='Owner requested continue after rejected trial; bounded representation repair experiment within original remaining wall-clock budget',quality_plan='Fresh base, same6600-class sampling schedule, verbal prompt/target projection only;50updatecap; pairedfull-outputreview; baseeligible; noautomaticextension',actual_training_started=False,previous_trial='quality_recovery_20261024',prior_locked_test_reused=False)
(q/'owner_run_scope.json').write_text(json.dumps(scope,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
trial={'hypothesis':'Source JSON target/prompt representation may contribute to response-style drift; next-token CE parity passed, causal root cause not proven.','source_and_original_labels_preserved':True,'new_human_attestation':False,'retained_all_worked_in_sampling_plan':True,'reused_development30':True,'previous_locked20_not_read':True,'changed_factors':['prompt renderer','target renderer'],'unchanged_factors':['source problems/answers/reasons','source sampling order/IDs','modelrevision','NF4','FP16','LoRAr16alpha16','micro2effective16','LR1e-5warmup10','assistantmask/EOT','noGC/noPacking'],'max_updates':50,'hard_deadline_unix':scope['hard_deadline_unix'],'independent_final_test_pending':True}
(q/'trial_scope.json').write_text(json.dumps(trial,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
pre=json.loads((p/'verbal_projection_preflight_v3.json').read_bytes());assert pre['rows_scanned']==16000 and not pre['errors']
(q/'projection_preflight.json').write_text(json.dumps(pre,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
pins={n:sha((q/n).read_bytes()) for n in ['recovery_worker.py','publisher_runtime.py','recovery_policy.py','verbal_training_renderer_v3.py']}
(q/'code_pins.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf8')
print(json.dumps({'folder':str(q),'pins':pins,'source_worker_unchanged':sha((p/'recovery_worker.py').read_bytes())=='345ff9d1def663bca704b4ab47ea8828c9793964bf70fb5ed2b784517b494e29'}))
