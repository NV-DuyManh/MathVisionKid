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

def supervised_prediction_positions(labels,ignore_index=-100):
    import torch
    shifted=labels[:,1:]
    if bool(((shifted!=ignore_index).sum(dim=1)==0).any()):raise ValueError('example has no supervised causal tokens')
    return torch.nonzero((shifted!=ignore_index).any(dim=0),as_tuple=False).flatten()

def selected_per_example_mean_cross_entropy(selected_logits,aligned_targets,ignore_index=-100):
    import torch.nn.functional as F
    counts=(aligned_targets!=ignore_index).sum(dim=1)
    if bool((counts==0).any()):raise ValueError('example has no supervised causal tokens')
    losses=F.cross_entropy(selected_logits.float().transpose(1,2),aligned_targets,reduction='none',ignore_index=ignore_index)
    return (losses.sum(dim=1)/counts).mean()

def install(status,work):
    """Install on main thread; all GPU probes execute at an owning-thread boundary."""
    import full_text_training_run as runner
    helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if getattr(runner.run_amp_update,'t4_batch_overlay',None)==2 and status.get('t4_batch_optimization',{}).get('code_sha256')==helper_sha256:
        return {'already_installed':True,'optimization':status.get('t4_batch_optimization')}
    previous=status.get('t4_batch_optimization')
    if previous and previous['state'] not in ('APPLIED','KEPT_ORIGINAL_BATCH','RUNTIME_OOM_FALLBACK_SAME_GROUP'):
        raise RuntimeError('Wait for existing physical batch probe to finish')
    if previous:status.setdefault('t4_batch_optimization_history',[]).append(json.loads(json.dumps(previous)))
    original=runner.run_amp_update
    while hasattr(original,'__wrapped__'):original=original.__wrapped__
    work=Path(work);work.mkdir(parents=True,exist_ok=True)
    state={'state':'QUEUED_FOR_NEXT_OPTIMIZER_BOUNDARY','physical_microbatch':1,
           'effective_optimizer_group':16,'extra_optimizer_updates':0,
           'training_rows_added_or_removed':0,'source_or_target_bytes_changed':0,
           'truncation_allowed':False,'version':2,'gradient_checkpointing':True,
           'selected_supervised_logits':False,'length_grouping_within_optimizer_step':False,
           'code_sha256':helper_sha256}
    status['t4_batch_optimization']=state
    def save():
        (work/'t4_batch_optimization_v2.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
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
        def checkpointing(enabled):
            if enabled:model.gradient_checkpointing_enable()
            else:model.gradient_checkpointing_disable()
        def backward(items,microbatch,pad_to=None):
            total=0.
            try:
                # Group boundaries and the outer acknowledgement cursor remain
                # unchanged. Only addition order inside this optimizer group varies.
                ordered=sorted(items,key=lambda x:len(x['encoded']['input_ids']))
                for chunk in partition_microbatches(ordered,microbatch):
                    values=pad_batch([x['encoded'] for x in chunk],tokenizer.pad_token_id)
                    if pad_to:
                        for key,fill in [('input_ids',tokenizer.pad_token_id),('attention_mask',0),('labels',-100)]:
                            values[key]=[r+[fill]*max(0,pad_to-len(r)) for r in values[key]]
                    batch={k:torch.tensor(v,dtype=torch.long,device='cuda') for k,v in values.items()}
                    positions=supervised_prediction_positions(batch['labels'])
                    if pad_to:positions=torch.arange(batch['labels'].shape[1]-1,device='cuda')
                    aligned=batch['labels'][:,1:].index_select(1,positions)
                    with torch.autocast('cuda',dtype=torch.float16):
                        output=model(input_ids=batch['input_ids'],attention_mask=batch['attention_mask'],use_cache=False,logits_to_keep=positions)
                        loss=selected_per_example_mean_cross_entropy(output.logits,aligned)
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
            rng=capture_rng();mode=model.training;cp_before=bool(model.is_gradient_checkpointing);weights_before=parameter_digest();scale_before=scaler.state_dict().copy()
            state['gradient_checkpointing']=cp_before
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
                    pos=supervised_prediction_positions(b['labels'])
                    output=model(input_ids=b['input_ids'],attention_mask=b['attention_mask'],use_cache=False,logits_to_keep=pos)
                    mean=float(selected_per_example_mean_cross_entropy(output.logits,b['labels'][:,1:].index_select(1,pos)));del b,output
                reference=sum(individual)/len(individual)
                state['actual_train_row_loss_parity']={'old_mean':reference,'batched_mean':mean,'abs_difference':abs(mean-reference)}
                if not math.isclose(mean,reference,rel_tol=.002,abs_tol=.005):raise ValueError('per-example loss parity failed')
                model.train(mode)
                total_memory=torch.cuda.get_device_properties(0).total_memory
                options=[(1,cp_before,False),(1,cp_before,True),(2,cp_before,True),(4,cp_before,True),(1,False,True),(2,False,True)]
                for size,cp_enabled,selected in options:
                    cleanup();checkpointing(cp_enabled);torch.cuda.reset_peak_memory_stats();times=[]
                    try:
                        for _ in range(2):
                            cleanup();torch.cuda.synchronize();start=time.perf_counter()
                            loss=backward(group,size) if selected else compute_backward(group)
                            torch.cuda.synchronize();times.append(time.perf_counter()-start)
                            if not math.isfinite(loss):raise FloatingPointError('probe loss nonfinite')
                        representative_peak=torch.cuda.max_memory_allocated()
                        cleanup();torch.cuda.reset_peak_memory_stats()
                        # Actual token content stays intact. Extra right padding
                        # tests memory at the audited corpus maximum, not fake data.
                        if selected:
                            backward(group[:size],size,pad_to=1481)
                        else:
                            padded=[]
                            for item in group[:size]:
                                encoded=dict(item['encoded'])
                                for key in ('input_ids','attention_mask','labels'):
                                    encoded[key]=list(encoded[key])
                                for key,fill in [('input_ids',tokenizer.pad_token_id),('attention_mask',0),('labels',-100)]:
                                    encoded[key]+=[fill]*max(0,1481-len(encoded[key]))
                                padded.append(dict(item,encoded=encoded))
                            compute_backward(padded)
                        torch.cuda.synchronize()
                        worst_peak=torch.cuda.max_memory_allocated()
                        finite=all(bool(torch.isfinite(p.grad).all()) for p in parameters if p.grad is not None)
                        if not finite:raise FloatingPointError('probe gradients nonfinite')
                        headroom=total_memory-worst_peak
                        result={'microbatch':size,'gradient_checkpointing':cp_enabled,'selected_supervised_logits':selected,
                          'length_grouping_within_optimizer_step':selected,'median_group_seconds':statistics.median(times),
                          'samples_per_second':len(group)/statistics.median(times),
                          'representative_peak_gib':representative_peak/2**30,'max_length_peak_gib':worst_peak/2**30,
                          'max_length_tokens':1481,'headroom_gib':headroom/2**30,'safe':headroom>=1.5*2**30}
                    except (BackwardOOM,torch.cuda.OutOfMemoryError):
                        result={'microbatch':size,'gradient_checkpointing':cp_enabled,'selected_supervised_logits':selected,
                                'safe':False,'reason':'FORWARD_BACKWARD_OOM_NO_WEIGHT_UPDATE'}
                    finally:cleanup()
                    probe_results.append(result);save()
                candidates=[x for x in probe_results if x.get('safe')]
                baseline=probe_results[0]
                if not candidates or not baseline.get('safe'):raise ValueError('No safe measured baseline')
                best=min(candidates,key=lambda x:x['median_group_seconds'])
                if best['median_group_seconds']>baseline['median_group_seconds']*.95:best=baseline
                state.update(physical_microbatch=best['microbatch'],gradient_accumulation_microsteps=16//best['microbatch'],
                             gradient_checkpointing=best['gradient_checkpointing'],selected_supervised_logits=best['selected_supervised_logits'],
                             length_grouping_within_optimizer_step=best.get('length_grouping_within_optimizer_step',False),
                             measured_speedup=baseline['median_group_seconds']/best['median_group_seconds'])
            except Exception as error:
                state.update(physical_microbatch=1,gradient_checkpointing=cp_before,selected_supervised_logits=False,
                             benchmark_error_type=type(error).__name__,benchmark_error=str(error))
            finally:
                cleanup();model.train(mode);checkpointing(state['gradient_checkpointing'])
                if weights_before!=parameter_digest() or scaler.state_dict()!=scale_before:raise RuntimeError('Probe mutated persistent model/scaler state')
                state.update(state='APPLIED' if state['selected_supervised_logits'] or not state['gradient_checkpointing'] else 'KEPT_ORIGINAL_BATCH',
                             model_weights_unchanged_during_probe=True,rng_restored_after_probe=True,
                             benchmark_optimizer_updates=0,training_rows_after_probe=status.get('rows_done'))
                save();state['drive_evidence']=store.json('t4_batch_optimization_v2.json',state);save()
        size=state['physical_microbatch'];initial_rng=capture_rng()
        while True:
            try:
                checkpointing(state['gradient_checkpointing'])
                replacement=(lambda items:backward(items,size)) if state['selected_supervised_logits'] else compute_backward
                result=original(group,replacement,optimizer,scaler,scheduler,capture_rng,restore_rng,
                                finite_gradients,clip_gradients,on_overflow,max_retries=max_retries)
                result.update(physical_microbatch=size,effective_optimizer_group=len(group),
                              selected_supervised_logits=state['selected_supervised_logits'],gradient_checkpointing=state['gradient_checkpointing'])
                return result
            except BackwardOOM:
                if size==1 and state['gradient_checkpointing']:raise
                optimizer.zero_grad(set_to_none=True);restore_rng(initial_rng);gc.collect();torch.cuda.empty_cache()
                if size>1:size=max(1,size//2)
                else:state['gradient_checkpointing']=True
                state.update(physical_microbatch=size,state='RUNTIME_OOM_FALLBACK_SAME_GROUP',
                                               last_fallback_step=status.get('step'),no_rows_acknowledged_for_failed_attempt=True)
                save();state['drive_evidence']=store.json('t4_batch_optimization_v2.json',state)
    wrapper.t4_batch_overlay=2
    runner.run_amp_update=wrapper
    return state
