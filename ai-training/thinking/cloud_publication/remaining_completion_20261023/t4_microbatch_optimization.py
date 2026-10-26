"""Measured physical batching overlay; optimizer groups, corpus and masks stay fixed."""
from pathlib import Path
import functools, gc, hashlib, inspect, json, math, statistics, time

def partition_microbatches(items,microbatch_size):
    if type(microbatch_size) is not int or microbatch_size<=0:
        raise ValueError('positive microbatch_size required')
    return [items[i:i+microbatch_size] for i in range(0,len(items),microbatch_size)]

def per_example_mean_cross_entropy(logits,labels,ignore_index=-100):
    """Same causal, per-example mean objective as the original microbatch=1 loop."""
    import torch
    import torch.nn.functional as F
    shifted=labels[:,1:]
    counts=(shifted!=ignore_index).sum(dim=1)
    if bool((counts==0).any()):raise ValueError('example has no supervised causal tokens')
    losses=F.cross_entropy(logits[:,:-1,:].float().transpose(1,2),shifted,
                           reduction='none',ignore_index=ignore_index)
    return (losses.sum(dim=1)/counts).mean()

class BackwardOOM(RuntimeError):
    pass

def install(status,work):
    """Install on main thread; all GPU probes execute at an owning-thread boundary."""
    import full_text_training_run as runner
    if hasattr(runner.run_amp_update,'t4_batch_overlay'):
        return {'already_installed':True,'optimization':status.get('t4_batch_optimization')}
    original=runner.run_amp_update
    work=Path(work);work.mkdir(parents=True,exist_ok=True)
    state={'state':'QUEUED_FOR_NEXT_OPTIMIZER_BOUNDARY','physical_microbatch':1,
           'effective_optimizer_group':16,'extra_optimizer_updates':0,
           'training_rows_added_or_removed':0,'source_or_target_bytes_changed':0,
           'truncation_allowed':False,'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    status['t4_batch_optimization']=state
    def save():
        (work/'t4_batch_optimization.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    save()
    @functools.wraps(original)
    def wrapper(group,compute_backward,optimizer,scaler,scheduler,capture_rng,restore_rng,
                finite_gradients,clip_gradients,on_overflow,max_retries=8):
        import torch
        from exhaustive_colab_loader import pad_batch
        context=dict(zip(compute_backward.__code__.co_freevars,[c.cell_contents for c in (compute_backward.__closure__ or ())]))
        model=context['model'];tokenizer=context['tokenizer']
        owner=inspect.currentframe().f_back
        persist=owner.f_locals.get('persist');store=owner.f_locals.get('store')
        # update_group's closure contains persist/store even though it is currently
        # before run_amp_update; no other thread touches the model or optimizer.
        if persist is None or store is None:raise RuntimeError('Expected owning training update closure')
        parameters=[p for p in model.parameters() if p.requires_grad]
        def backward(items,microbatch,pad_to=None):
            total=0.
            try:
                for chunk in partition_microbatches(items,microbatch):
                    values=pad_batch([x['encoded'] for x in chunk],tokenizer.pad_token_id)
                    if pad_to:
                        for key,fill in [('input_ids',tokenizer.pad_token_id),('attention_mask',0),('labels',-100)]:
                            values[key]=[r+[fill]*max(0,pad_to-len(r)) for r in values[key]]
                    batch={k:torch.tensor(v,dtype=torch.long,device='cuda') for k,v in values.items()}
                    with torch.autocast('cuda',dtype=torch.float16):
                        output=model(input_ids=batch['input_ids'],attention_mask=batch['attention_mask'],use_cache=False)
                        loss=per_example_mean_cross_entropy(output.logits,batch['labels'])
                    if not bool(torch.isfinite(loss)):raise FloatingPointError('nonfinite physical batch loss')
                    weight=len(chunk)/len(items);total+=float(loss.detach())*weight
                    scaler.scale(loss*weight).backward()
                    del output,loss,batch
                return total
            except torch.cuda.OutOfMemoryError as error:
                # This exception is raised only before any optimizer step.
                raise BackwardOOM('OOM in forward/backward; no optimizer update') from error
        def parameter_digest():
            h=hashlib.sha256()
            for p in parameters:h.update(p.detach().cpu().contiguous().numpy().tobytes())
            return h.hexdigest()
        if state['state']=='QUEUED_FOR_NEXT_OPTIMIZER_BOUNDARY':
            state.update(state='SAVING_PRE_OPTIMIZATION_CHECKPOINT',before_step=status.get('step'),before_rows=status.get('rows_done'))
            save();persist()
            state['checkpoint_before']=status['last_verified_checkpoint']
            rng=capture_rng();mode=model.training;weights_before=parameter_digest();scale_before=scaler.state_dict().copy()
            probe_results=[];state.update(state='BENCHMARKING_WITHOUT_OPTIMIZER_UPDATES',probes=probe_results);save()
            def cleanup():
                optimizer.zero_grad(set_to_none=True);restore_rng(rng);gc.collect();torch.cuda.empty_cache()
            try:
                # Verify the changed reduction on actual current train rows with
                # dropout off. Fixtures independently cover unequal target lengths.
                model.eval();small=group[:2]
                with torch.no_grad(),torch.autocast('cuda',dtype=torch.float16):
                    individual=[]
                    for item in small:
                        b={k:torch.tensor(v,dtype=torch.long,device='cuda') for k,v in pad_batch([item['encoded']],tokenizer.pad_token_id).items()}
                        individual.append(float(model(**b).loss));del b
                    b={k:torch.tensor(v,dtype=torch.long,device='cuda') for k,v in pad_batch([x['encoded'] for x in small],tokenizer.pad_token_id).items()}
                    output=model(input_ids=b['input_ids'],attention_mask=b['attention_mask'],use_cache=False)
                    mean=float(per_example_mean_cross_entropy(output.logits,b['labels']));del b,output
                reference=sum(individual)/len(individual)
                state['actual_train_row_loss_parity']={'old_mean':reference,'batched_mean':mean,'abs_difference':abs(mean-reference)}
                if not math.isclose(mean,reference,rel_tol=.002,abs_tol=.005):raise ValueError('per-example loss parity failed')
                model.train(mode)
                total_memory=torch.cuda.get_device_properties(0).total_memory
                for size in (1,2,4):
                    cleanup();torch.cuda.reset_peak_memory_stats();times=[]
                    try:
                        for _ in range(2):
                            cleanup();torch.cuda.synchronize();start=time.perf_counter()
                            loss=compute_backward(group) if size==1 else backward(group,size)
                            torch.cuda.synchronize();times.append(time.perf_counter()-start)
                            if not math.isfinite(loss):raise FloatingPointError('probe loss nonfinite')
                        representative_peak=torch.cuda.max_memory_allocated()
                        cleanup();torch.cuda.reset_peak_memory_stats()
                        # Actual token content stays intact. Extra right padding
                        # tests memory at the audited corpus maximum, not fake data.
                        backward(group[:size],size,pad_to=1481);torch.cuda.synchronize()
                        worst_peak=torch.cuda.max_memory_allocated()
                        finite=all(bool(torch.isfinite(p.grad).all()) for p in parameters if p.grad is not None)
                        if not finite:raise FloatingPointError('probe gradients nonfinite')
                        headroom=total_memory-worst_peak
                        result={'microbatch':size,'median_group_seconds':statistics.median(times),
                          'samples_per_second':len(group)/statistics.median(times),
                          'representative_peak_gib':representative_peak/2**30,'max_length_peak_gib':worst_peak/2**30,
                          'max_length_tokens':1481,'headroom_gib':headroom/2**30,'safe':headroom>=1.5*2**30}
                    except (BackwardOOM,torch.cuda.OutOfMemoryError):
                        result={'microbatch':size,'safe':False,'reason':'FORWARD_BACKWARD_OOM_NO_WEIGHT_UPDATE'}
                    finally:cleanup()
                    probe_results.append(result);save()
                candidates=[x for x in probe_results if x.get('safe')]
                baseline=next(x for x in probe_results if x['microbatch']==1)
                if not candidates or not baseline.get('safe'):raise ValueError('No safe measured baseline')
                best=min(candidates,key=lambda x:x['median_group_seconds'])
                if best['median_group_seconds']>baseline['median_group_seconds']*.95:best=baseline
                state.update(physical_microbatch=best['microbatch'],gradient_accumulation_microsteps=16//best['microbatch'],
                             measured_speedup=baseline['median_group_seconds']/best['median_group_seconds'])
            except Exception as error:
                state.update(physical_microbatch=1,benchmark_error_type=type(error).__name__,benchmark_error=str(error))
            finally:
                cleanup();model.train(mode)
                if weights_before!=parameter_digest() or scaler.state_dict()!=scale_before:raise RuntimeError('Probe mutated persistent model/scaler state')
                state.update(state='APPLIED' if state['physical_microbatch']>1 else 'KEPT_ORIGINAL_BATCH',
                             model_weights_unchanged_during_probe=True,rng_restored_after_probe=True,
                             benchmark_optimizer_updates=0,training_rows_after_probe=status.get('rows_done'))
                save();state['drive_evidence']=store.json('t4_batch_optimization.json',state);save()
        size=state['physical_microbatch'];initial_rng=capture_rng()
        while True:
            try:
                replacement=compute_backward if size==1 else lambda items:backward(items,size)
                result=original(group,replacement,optimizer,scaler,scheduler,capture_rng,restore_rng,
                                finite_gradients,clip_gradients,on_overflow,max_retries=max_retries)
                result.update(physical_microbatch=size,effective_optimizer_group=len(group))
                return result
            except BackwardOOM:
                if size==1:raise
                optimizer.zero_grad(set_to_none=True);restore_rng(initial_rng);gc.collect();torch.cuda.empty_cache()
                size=max(1,size//2);state.update(physical_microbatch=size,state='RUNTIME_OOM_FALLBACK_SAME_GROUP',
                                               last_fallback_step=status.get('step'),no_rows_acknowledged_for_failed_attempt=True)
                save();state['drive_evidence']=store.json('t4_batch_optimization.json',state)
    wrapper.t4_batch_overlay=True
    runner.run_amp_update=wrapper
    return state
