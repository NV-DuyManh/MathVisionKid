"""Derive a separately auditable execution overlay from the preserved v2."""
from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'t4_microbatch_optimization_v2.py').read_text(encoding='utf8')
s=s.replace('==2 and status','==3 and status').replace("'version':2","'version':3").replace('wrapper.t4_batch_overlay=2','wrapper.t4_batch_overlay=3')
s=s.replace('t4_batch_optimization_v2.json','t4_batch_optimization_v3.json')
start=s.index('        def backward(items,microbatch,pad_to=None):')
s=s[:start]+s[start:].replace('def backward(items,microbatch,pad_to=None):','def backward(items,microbatch,pad_to=None,token_budget=2962):',1)
s=s.replace('ordered=sorted(items,key=lambda x:len(x[\'encoded\'][\'input_ids\']))\n                for chunk in partition_microbatches(ordered,microbatch):',
'''chunks=adaptive_microbatches(items,microbatch,token_budget,pad_to)
                for chunk in chunks:''')
s=s.replace("'truncation_allowed':False,'version':3,'gradient_checkpointing':True,", "'truncation_allowed':False,'version':3,'gradient_checkpointing':True,'padded_token_budget':2962,'adaptive_batching':True,")
s=s.replace("'physical_microbatch':1,", "'physical_microbatch':2,")
s=s.replace("options=[(1,cp_before,False),(1,cp_before,True),(2,cp_before,True),(4,cp_before,True),(1,False,True),(2,False,True)]", "options=[(2,2962),(3,3800),(4,3800),(8,3800)]")
s=s.replace('for size,cp_enabled,selected in options:', 'for size,token_budget in options:\n                    cp_enabled=True;selected=True')
s=s.replace('for _ in range(2):','for _ in range(3):')
s=s.replace('loss=backward(group,size) if selected else compute_backward(group)','loss=backward(group,size,token_budget=token_budget)')
a=s.index('                        if selected:\n                            backward(group[:size]')
b=s.index('                        finite=all(',a)
s=s[:a]+'''                        worst_peak=representative_peak;memory_shapes=[]
                        for count in range(2,size+1):
                            length=min(1481,token_budget//count)
                            if length<max(len(x['encoded']['input_ids']) for x in group[:count]):
                                # Longer real content is retained and scheduled
                                # into smaller physical chunks, never truncated.
                                length=max(len(x['encoded']['input_ids']) for x in group[:count])
                            cleanup();torch.cuda.reset_peak_memory_stats()
                            backward(group[:count],size,pad_to=length,token_budget=token_budget)
                            torch.cuda.synchronize();peak=torch.cuda.max_memory_allocated()
                            if not all(bool(torch.isfinite(p.grad).all()) for p in parameters if p.grad is not None):
                                raise FloatingPointError('probe gradients nonfinite')
                            worst_peak=max(worst_peak,peak)
                            memory_shapes.append(dict(requested_rows=count,padded_length=length,peak_gib=peak/2**30))
''' +s[b:]
s=s.replace("result={'microbatch':size,'gradient_checkpointing':cp_enabled", "result={'microbatch':size,'padded_token_budget':token_budget,'memory_shapes':memory_shapes,'gradient_checkpointing':cp_enabled",1)
s=s.replace("result={'microbatch':size,'gradient_checkpointing':cp_enabled", "result={'microbatch':size,'padded_token_budget':token_budget,'gradient_checkpointing':cp_enabled",1)
s=s.replace("state.update(physical_microbatch=best['microbatch'],gradient_accumulation_microsteps=16//best['microbatch'],", "state.update(physical_microbatch=best['microbatch'],padded_token_budget=best['padded_token_budget'],gradient_accumulation_microsteps='VARIABLE_EXACT_GROUP_WEIGHTING',")
s=s.replace("state.update(physical_microbatch=1,gradient_checkpointing=cp_before,selected_supervised_logits=False,", "state.update(physical_microbatch=2,padded_token_budget=2962,gradient_checkpointing=True,selected_supervised_logits=True,")
s=s.replace("            except Exception as error:\n                state.update(physical_microbatch=2,padded_token_budget=2962,gradient_checkpointing=True,selected_supervised_logits=True,", """            except Exception as error:
                # A failed safety probe must not silently select the failed shape.
                safe_baseline=probe_results[0] if probe_results and probe_results[0].get('safe') else None
                prior_safe=previous and previous.get('state')=='APPLIED' and previous.get('physical_microbatch')==2 and previous.get('gradient_checkpointing') and previous.get('selected_supervised_logits') and any(p.get('safe') and p.get('microbatch')==2 and p.get('gradient_checkpointing') for p in previous.get('probes',[]))
                if not safe_baseline and (probe_results or not prior_safe):
                    state.update(state='BENCHMARK_FAILED_NO_SAFE_CONFIG',benchmark_error=str(error))
                    raise
                state.update(physical_microbatch=2,padded_token_budget=2962,gradient_checkpointing=True,selected_supervised_logits=True,""")
s=s.replace("                state.update(state='APPLIED' if state['selected_supervised_logits'] or not state['gradient_checkpointing'] else 'KEPT_ORIGINAL_BATCH',", "                state.update(state=state['state'] if state['state']=='BENCHMARK_FAILED_NO_SAFE_CONFIG' else 'APPLIED',")
s=s.replace('replacement=(lambda items:backward(items,size)) if state[\'selected_supervised_logits\'] else compute_backward', "replacement=lambda items:backward(items,size,token_budget=state['padded_token_budget'])")
s=s.replace("result.update(physical_microbatch=size,effective_optimizer_group=len(group),", "result.update(physical_microbatch=size,physical_chunk_sizes=[len(c) for c in adaptive_microbatches(group,size,state['padded_token_budget'])],padded_token_budget=state['padded_token_budget'],effective_optimizer_group=len(group),")
insert='''
def adaptive_microbatches(items,max_rows,padded_token_budget,pad_to=None):
    if type(max_rows) is not int or max_rows<1:raise ValueError('positive max_rows required')
    if type(padded_token_budget) is not int or padded_token_budget<1:raise ValueError('positive token budget required')
    ordered=sorted(items,key=lambda x:len(x['encoded']['input_ids']))
    chunks=[];chunk=[];longest=0
    for item in ordered:
        length=max(len(item['encoded']['input_ids']),pad_to or 0)
        if chunk and (len(chunk)>=max_rows or max(longest,length)*(len(chunk)+1)>padded_token_budget):
            chunks.append(chunk);chunk=[];longest=0
        chunk.append(item);longest=max(longest,length)
    if chunk:chunks.append(chunk)
    return chunks

'''
s=s.replace('def install(status,work):',insert+'def install(status,work):')
compile(s,'t4_microbatch_optimization_v3.py','exec')
(p/'t4_microbatch_optimization_v3.py').write_text(s,encoding='utf8')
