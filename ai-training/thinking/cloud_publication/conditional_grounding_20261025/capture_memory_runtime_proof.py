import pathlib,json,hashlib,subprocess
from datetime import datetime as proof_datetime,timezone as proof_timezone
mr=pathlib.Path('/content/mathvisionkid_conditional_grounding_20261025')
def mr_sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
mm=json.loads((mr/'memory_resume_migration.json').read_bytes())
mg=mr/'training'/mm['parent_checkpoint_generation']
assert mr_sha(mg/'generation_manifest.json')==mm['parent_generation_manifest_sha256']
assert mr_sha(mr/'recovery_worker_v5.py')==mm['resumed_worker_sha256']
assert mr_sha(mr/'native_backend_v3.py')==mm['resumed_backend_sha256']
mc=json.loads((mr/'training/run_config.json').read_bytes())
mp=json.loads((mg/'run_config.json').read_bytes())
md={k:{'before':mp.get(k),'after':mc.get(k)} for k in set(mp)|set(mc) if mp.get(k)!=mc.get(k)}
assert set(md)=={'worker_sha256','gradient_checkpointing','loss_reduction','explicit_memory_resume_migration_sha256'}
ma=json.loads((mr/'training/native_resumed_microbatch_audit.json').read_bytes())
assert ma['shifted_CE_matches_forward'] is True
assert conditional_training_process.poll() is None
mcmd=pathlib.Path('/proc')/str(conditional_training_process.pid)/'cmdline'
argv=mcmd.read_bytes().split(b'\0');argv=[v.decode() for v in argv if v]
assert str(mr/'recovery_worker_v5.py') in argv
assert argv[argv.index('--resume-generation')+1]==str(mg)
ml=json.loads((mr/'training/resume_log_validation.json').read_bytes())
proof={'schema':'MathVisionKid.actual_memory_resume_binding.v1','observed_utc':proof_datetime.now(proof_timezone.utc).isoformat(),
 'pid':conditional_training_process.pid,'actual_process_argv':argv,'parent_manifest_sha256':mr_sha(mg/'generation_manifest.json'),
 'worker_sha256':mr_sha(mr/'recovery_worker_v5.py'),'backend_sha256':mr_sha(mr/'native_backend_v3.py'),
 'exact_config_differences':md,'resumed_shifted_loss_audit':ma,'resume_log_validation':ml,
 'progress':json.loads((mr/'training/progress.json').read_bytes()),'worker_alive':True,
 'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader'],text=True).strip(),
 'training_code_or_configuration_modified':False,'proof_scope':'Read-only live process and cloud file bindings; not a memory introspection proof of imported Python bytes'}
dest=mr/'training/actual_memory_resume_binding.json'
assert not dest.exists(),'Retain original proof rather than overwrite'
dest.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(proof,ensure_ascii=False))
