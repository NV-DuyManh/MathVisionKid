"""Explicit versioned OOM recovery; same data, effective batch, loss and LR."""
from pathlib import Path
import hashlib,json
P=Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
backend=(P/'native_backend_v2.py').read_text(encoding='utf8')
backend=backend.replace("assert not use_gradient_checkpointing and not use_rslora and loftq_config is None",
 "assert use_gradient_checkpointing and not use_rslora and loftq_config is None")
backend=backend.replace('prepare_model_for_kbit_training(model,use_gradient_checkpointing=False)',
 "prepare_model_for_kbit_training(model,use_gradient_checkpointing=True,gradient_checkpointing_kwargs={'use_reentrant':False})")
backend=backend.replace('model.train();model.config.use_cache=False',
 "model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False});model.train();model.config.use_cache=False")
worker=(P/'recovery_worker_v4.py').read_text(encoding='utf8')
worker=worker.replace('from native_backend_v2 import NativeBackend as FastLanguageModel',
 'from native_backend_v3 import NativeBackend as FastLanguageModel')
worker=worker.replace("'gradient_checkpointing':False", "'gradient_checkpointing':True")
worker=worker.replace('use_gradient_checkpointing=False,random_state=20261024',
 'use_gradient_checkpointing=True,random_state=20261024')
worker=worker.replace('model.gradient_checkpointing_disable();',
 "model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False});")
old="   if saved_cfg[k]!=cfg[k]:raise ValueError('resume config mismatch '+k)"
new="""   if saved_cfg[k]!=cfg[k]:
    if k!='worker_sha256':raise ValueError('resume config mismatch '+k)
    migration=json.loads((root/'memory_resume_migration.json').read_bytes())
    if saved_cfg[k]!=migration['parent_worker_sha256'] or cfg[k]!=migration['resumed_worker_sha256']:
     raise ValueError('Unapproved resume worker migration')
    if migration['changed_training_semantics'] is not False or migration['only_memory_change']!='nonreentrant_gradient_checkpointing':
     raise ValueError('Resume migration may only change recomputation memory strategy')
    permitted={'worker_sha256','gradient_checkpointing','loss_reduction'}
    differences={key for key in set(saved_cfg)|set(cfg) if saved_cfg.get(key)!=cfg.get(key)}
    if differences-permitted or saved_cfg['gradient_checkpointing'] is not False or cfg['gradient_checkpointing'] is not True:
     raise ValueError('Additional checkpoint config drift during memory migration')
    cfg['explicit_memory_resume_migration_sha256']=sha(root/'memory_resume_migration.json')"""
assert worker.count(old)==1
worker=worker.replace(old,new)
worker=worker.replace("'loss_reduction':'micro2 supervised-token mean weighted pair_rows/group_rows; source targets unchangedV3; conditional worked prompt; grade interleave10worked6hint no repeats'",
 "'loss_reduction':'row-count-weighted means of micro2 assistant-token losses, not a global token mean; unchanged objective from parentCP1; source targets unchangedV3'" )
worker=worker.replace("if state['step']==0 and j==0:","if (state['step']==0 or (args.resume_generation and cursor==resume['cursor'])) and j==0:")
worker=worker.replace("atomic(out/'native_first_microbatch_audit.json',", "atomic(out/('native_resumed_microbatch_audit.json' if args.resume_generation else 'native_first_microbatch_audit.json'),")
for name,text in [('native_backend_v3.py',backend),('recovery_worker_v5.py',worker)]:
 compile(text,name,'exec');path=P/name
 assert not path.exists(),'Versioned memory repair already prepared'
 path.write_bytes(text.encode())
migration={'schema':'MathVisionKid.explicit_memory_resume_migration.v1',
 'parent_worker_sha256':sha(P/'recovery_worker_v4.py'),'resumed_worker_sha256':sha(P/'recovery_worker_v5.py'),
 'resumed_backend_sha256':sha(P/'native_backend_v3.py'),
 'parent_checkpoint_generation':'generation_step_000001_rows_00000016',
 'parent_generation_manifest_sha256':'7b9fe87846255e4cc31b1d732c591de18c4d7dcaa5acb9c8fa04d6fd06d9fdee',
 'parent_checkpoint_archive_sha256':'5254bdff7ccd5f85ff44967082515b9b6f50d5004378b95b25af65674ea94551',
 'parent_checkpoint_drive_id':'1NOkLIubccEzcDNt5cm72FlBBPEe9Ll7K',
 'last_observed_before_OOM':{'step':6,'rows_done':96},
 'resumed_from_committed':{'step':1,'rows_done':16},
 'changed_training_semantics':False,'only_memory_change':'nonreentrant_gradient_checkpointing',
 'effective_batch':16,'microbatch':2,'learning_rate':3e-6,'targets_or_source_changed':False,
 'optimizer_scheduler_rng_and_parameter_mapping_restored':True,
 'postcheckpoint_successful_log_tail_preserved_by_resume_helper':True,
 'restored_rows_counted_once_in_final_checkpoint_metrics':True,
 'physical_extra_exposures_in_failed_attempt_not_claimed_unique':80,
 'actual_weight_updates_in_lost_tail':5,
 'loss_description_clarification':'The implementation always used len(items)/group_rows weighting of each microbatch token-mean loss. Clarified config text; no loss weighting changed.',
 'production_approved':False,'human_review_claimed':False}
(P/'memory_resume_migration.json').write_text(json.dumps(migration,indent=2)+'\n')
print(json.dumps(migration))
