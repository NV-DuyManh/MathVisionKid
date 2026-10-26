import pathlib,json,functools,inspect,zipfile,time
import full_text_training_run as old_runner
assert full_text_training_thread.is_alive()
assert time.time()<budget_status['deadline_unix']-1800
class BudgetScopeBoundaryStop(RuntimeError):pass
_old_budget_amp=old_runner.run_amp_update
@functools.wraps(_old_budget_amp)
def _save_old_scope_then_stop(group,compute_backward,*args,**kwargs):
    owner=inspect.currentframe().f_back
    persist=owner.f_locals.get('persist');store=owner.f_locals.get('store')
    if persist is None or store is None:raise RuntimeError('Expected owning optimizer boundary')
    step=full_text_training_status['step'];rows=full_text_training_status['rows_done']
    budget_status.update(state='PRESERVING_OLD_CHECKPOINT_AT_BOUNDARY',old_step=step,old_rows=rows)
    (budget_root/'budget_control.json').write_text(json.dumps(budget_status,indent=2))
    if full_text_training_status.get('last_verified_checkpoint',{}).get('step')!=step:persist()
    cp=full_text_training_status['last_verified_checkpoint']
    assert cp['step']==step and cp['rows_done']==rows and cp['fresh_raw_readback_verified']
    context=dict(zip(compute_backward.__code__.co_freevars,[c.cell_contents for c in compute_backward.__closure__]))
    adapter=budget_root/f'old_adapter_step_{step:07d}'
    context['model'].save_pretrained(adapter);context['tokenizer'].save_pretrained(adapter)
    package=budget_root/f'old_adapter_step_{step:07d}.zip'
    with zipfile.ZipFile(package,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in adapter.iterdir():
            if p.is_file():z.write(p,p.name)
        z.writestr('lineage.json',json.dumps({'old_step':step,'rows_done':rows,'base_revision':'70d244cc86ccca08cf5af4e1e306ecf908b1ad5e','optimizer':'torch.optim.AdamW','epoch_complete':False}))
    proof=store.put(package.name,package)
    receipt={'state':'OLD_RUN_PRESERVED_FOR_NEW_OWNER_AUTHORIZED_3H_BRANCH','old_checkpoint':cp,'old_adapter':proof,'old_rows_done':rows,
      'old_step':step,'new_branch_optimizer_resume':False,'reason':'New user scope permits stratified view; AdamW8bit does not resume regular AdamW state',
      'source_data_changed':False,'runtime_restart_required':False,'frozen_ocr_changed':False,'saved_unix':time.time()}
    (budget_root/'pause_receipt.json').write_text(json.dumps(receipt,indent=2))
    store.json('owner_budget3h_scope_transition.json',receipt)
    budget_status.update(state='OLD_RUN_SAFELY_PRESERVED_READY_FOR_BENCHMARK',old_checkpoint=cp,old_adapter=proof)
    (budget_root/'budget_control.json').write_text(json.dumps(budget_status,indent=2))
    full_text_training_status['owner_requested_scope_transition']=receipt
    raise BudgetScopeBoundaryStop('Owner changed objective to a bounded stratified 3-hour run; exact old checkpoint and adapter verified')
old_runner.run_amp_update=_save_old_scope_then_stop
print(json.dumps({'state':'OLD_RUN_SAFE_BOUNDARY_SAVE_QUEUED','current_step':full_text_training_status.get('step'),'no_runtime_restart':True}))
