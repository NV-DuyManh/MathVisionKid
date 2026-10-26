import pathlib,json,time,sys,subprocess,threading,hashlib
from datetime import datetime,timezone,timedelta
budget_root=pathlib.Path('/content/mathvisionkid_t4_budget_3h_20261023')
budget_root.mkdir(exist_ok=True)
if (budget_root/'budget_control.json').exists():
    budget_status=json.loads((budget_root/'budget_control.json').read_bytes())
else:
    now=datetime.now(timezone.utc)
    budget_status={'schema':'MathVisionKid.T4_budget3h.v1','started_utc':now.isoformat(),'deadline_utc':(now+timedelta(hours=3)).isoformat(),
      'started_unix':time.time(),'deadline_unix':time.time()+10800,'state':'INSPECTING_EXISTING_RUN','training_scope':'DETERMINISTIC_SKILL_STRATIFIED_VIEW_NOT_FULL_CORPUS',
      'original_train_rows':6502344,'original_validation_rows':24,'original_test_rows':24,'full_epoch_claim_allowed':False,'paid_resources_allowed':False}
    (budget_root/'budget_control.json').write_text(json.dumps(budget_status,indent=2))
now=datetime.now(timezone.utc)
info={'budget':budget_status,'python':sys.version,'old_training':dict(full_text_training_status),'old_worker_alive':full_text_training_thread.is_alive(),
      'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,memory.used,utilization.gpu','--format=csv,noheader'],text=True).strip(),
      'runtime_directories':[str(p) for p in pathlib.Path('/content').iterdir() if p.is_dir()],
      'audit_database_files':[dict(path=str(p),bytes=p.stat().st_size) for base in pathlib.Path('/content').iterdir() if base.is_dir() and ('math' in base.name.lower() or 'audit' in base.name.lower()) for p in list(base.rglob('*.sqlite*'))[:15]],
      'observed_utc':now.isoformat()}
for key in ('worker_stack','t4_batch_optimization_history'):
    info['old_training'].pop(key,None)
(budget_root/'initial_runtime_inventory.json').write_text(json.dumps(info,ensure_ascii=False,indent=2))
print(json.dumps(info,ensure_ascii=False))
