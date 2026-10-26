from pathlib import Path
import ast,json,base64,hashlib
P=Path(__file__).parent;OLD=P.parent/'conditional_grounding_20261025';QA=P.parent/'skill_recovery_150m_20261024'
# Reuse the reviewed transactional publisher with a new run identity.
publisher=(OLD/'publisher_runtime.py').read_bytes().decode().replace('conditional_grounding_20261025','recovery_20261026').replace('CONDITIONAL_GROUNDING_20261025','RECOVERY_20261026').replace('ConditionalGrounding','Recovery20261026')
publisher=publisher.replace("initial+=sorted(p.name for p in root.glob('test_recovery*.py'))", "initial+=['recovery_worker_20261026.py','recovery_policy_20261026.py','native_backend_20261026.py','preflight_checks.py','preflight_complete.json','preparation_provenance.json','root_reviewed_training_plan.json','active_staged_code_pins.json']\n  initial+=sorted(p.name for p in root.glob('test_recovery*.py'))")
(P/'publisher_runtime.py').write_bytes(publisher.encode())
names=['recovery_worker_20261026.py','recovery_policy_20261026.py','native_backend_20261026.py','preflight_checks.py','preparation_provenance.json','publisher_runtime.py','root_reviewed_training_plan.json']
sources={n:P/n for n in names}
for n in ['conditional_behavior_renderer.py','behavior_renderer.py','verbal_training_renderer_v3.py','inference_contract.py','exact_math_audit.py']:
 sources[n]=OLD/n
sources['new_validation_candidates.jsonl']=OLD/'development_candidates.jsonl'
sources['new_validation_candidate_notes.json']=OLD/'development_author_notes.json'
sources['prior_used_development.jsonl']=P.parent/'quality_recovery_20261024/new_validation_candidates.jsonl'
for n in ['source_semantic_review_g1_g3.json','source_semantic_review_g4_g5.json']:sources[n]=QA/n
sources['projection_preflight_previous.json']=QA/'projection_preflight.json'
sources['source_behavior_samples_previous.json']=QA/'source_behavior_samples.json'
sources['updated_owner_scope.json']=P/'owner_run_scope.json'
sources['root_prior_run_semantic_closure.json']=OLD/'root_paired_decisions_step_000100.json'
payload={n:base64.b64encode(path.read_bytes()).decode() for n,path in sources.items()}
pins={n:hashlib.sha256(path.read_bytes()).hexdigest() for n,path in sources.items()}
tree=ast.parse((OLD/'build_cloud_stage.py').read_text(encoding='utf8'))
template=next(ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='template' for t in node.targets))
template=template.replace('/content/mathvisionkid_conditional_grounding_20261025','/content/mathvisionkid_recovery_20261026').replace('1611698ac255','fb7636900c84')
template=template.replace("import recovery_policy_v2 as policy","import recovery_policy_20261026 as policy")
template=template.replace("'Fresh reviewed development30; unused native15 reserved final-only and not loaded by training worker. Owner budget unchanged.'", "'Reused development30, not unseen evaluation. Fresh base/candidate outputs under unchanged inference protocol. Native15 remains sealed. Scope updated by owner26/10.'")
template=template.replace("scope=json.loads((r/'owner_run_scope.json').read_bytes())", "old_scope=(r/'owner_run_scope.json').read_bytes()\n(r/'owner_scope_before_cutoff_update.json').write_bytes(old_scope)\n(r/'owner_run_scope.json').write_bytes((r/'updated_owner_scope.json').read_bytes())\nscope=json.loads((r/'owner_run_scope.json').read_bytes())")
template=template.replace("sys.path.insert(0,str(r))", "(r/'active_staged_code_pins.json').write_text(json.dumps(pins,sort_keys=True,indent=2)+'\\n')\npreflight=subprocess.run([str(r/'venv/bin/python'),str(r/'preflight_checks.py')],capture_output=True,text=True,timeout=60)\n(r/'preflight_complete.json').write_text(json.dumps({'returncode':preflight.returncode,'stdout':preflight.stdout,'stderr':preflight.stderr,'gpu_called':False},indent=2)+'\\n')\nassert preflight.returncode==0,preflight.stdout+preflight.stderr\nsys.path.insert(0,str(r))")
template=template.replace("'conditional_publisher_runtime'", "'recovery26_publisher_runtime'")
template=template.replace("training/pretrain_qa_approved.json","training/pretrain_source_qa_prepared.json")
code=template.replace('PAYLOAD',repr(payload)).replace('PINS',repr(pins))
compile(code,'stage26','exec');(P/'stage_runtime.py').write_bytes(code.encode())
(P/'staged_code_pins.json').write_text(json.dumps(pins,indent=2)+'\n')
print({'explicit_staged_files':len(pins),'stage_bytes':len(code.encode()),'training_started':False})
