from pathlib import Path
import base64,hashlib
p=Path(__file__).resolve().parent
quota=(p/'drive_quota_resilience.py').read_bytes()
overlay=(p/'t4_microbatch_optimization_v2.py').read_bytes()
code=f'''import pathlib,base64,hashlib,importlib,sys,threading,json,traceback
assert not full_text_training_thread.is_alive()
assert full_text_training_status['t4_batch_optimization']['state']=='SAVING_PRE_OPTIMIZATION_CHECKPOINT'
root=pathlib.Path('/content/mathvisionkid_full_text_training')
for name,raw,pin in {[(n,base64.b64encode(b).decode(),hashlib.sha256(b).hexdigest()) for n,b in [('drive_quota_resilience.py',quota),('t4_microbatch_optimization_v2.py',overlay)]]!r}:
    content=base64.b64decode(raw)
    assert hashlib.sha256(content).hexdigest()==pin
    (root/'code'/name).write_bytes(content)
importlib.invalidate_caches()
import drive_quota_resilience
drive_quota_resilience.install(full_text_training_status)
def _recover_quota_checkpoint():
    try:
        import torch
        import full_text_training_run as runner
        checkpoint=root/'resume_state.pt'
        saved=torch.load(checkpoint,map_location='cpu',weights_only=True)
        assert saved['config_sha256']=='d8b0b09755917190b3dfa35250300d64b2b0552e838c6b641e110eb312034ac8'
        assert saved['step']==165 and saved['rows_done']==2640
        assert saved['step']==full_text_training_status['step'] and not saved['epoch_complete']
        assert saved['cursor']['split']=='train'
        del saved
        store=runner.RunStore(text_training_drive,'14dc5111ab4d0ac691a6f4b0d49f4395f8544145663bdd42df4e6da1fa6a4fdc',root/'run_artifacts')
        name=f'checkpoint_step_{{165:07d}}_rows_{{2640:08d}}_{{runner.digest(checkpoint)[:16]}}.pt'
        proof=store.put(name,checkpoint)
        proof.update(config_sha256='d8b0b09755917190b3dfa35250300d64b2b0552e838c6b641e110eb312034ac8',step=165,rows_done=2640,epoch_complete=False)
        store.json('checkpoint_receipt.json',proof)
        full_text_training_status.update(last_verified_checkpoint=proof,state='CHECKPOINT_RECOVERED_READY_TO_RESUME',recovery='EXACT_PRE_PROBE_SNAPSHOT_VERIFIED_NO_OPTIMIZER_ATTEMPT')
        store.json('progress.json',full_text_training_status)
    except BaseException as error:
        full_text_training_status.update(state='CHECKPOINT_RECOVERY_FAILED',recovery_error=str(error))
        (root/'recovery_error.txt').write_text(traceback.format_exc())
full_text_recovery_thread=threading.Thread(target=_recover_quota_checkpoint,name='MathVisionKidCheckpointRecovery',daemon=True)
full_text_recovery_thread.start()
print(json.dumps({{'state':'RECOVERING_EXACT_PRE_PROBE_CHECKPOINT','training_worker_alive':False,'recovery_worker_alive':full_text_recovery_thread.is_alive()}},ensure_ascii=False))
'''
compile(code,'recover_quota_runtime.py','exec')
(p/'recover_quota_runtime.py').write_text(code,encoding='utf8')
