"""Fresh stable-AMP run: retry the identical group without advancing optimizer/log.

The earlier failed run stays immutable. No checkpoint is imported from it.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import time

from verified_math_training_v2 import messages,serialize,collate,score,aggregate

MODEL='Qwen/Qwen3-0.6B'
REVISION='c1899de289a04d12100db370d81485cdf75e47ca'
RUN_ID='qwen3_06b_verified_math_v2_stable_epoch1_seed20261012'
SEED=20261012
AMP_INIT_SCALE=1024
AMP_GROWTH_INTERVAL=2000
AMP_MAX_RETRIES=8

def run_amp_update(group,compute_backward,optimizer,scaler,scheduler,capture_rng,restore_rng,
                   finite_gradients,clip_gradients,on_overflow,max_retries=AMP_MAX_RETRIES):
    """One committed update, or explicit failure; retries never step parameters.

    Callbacks make the transactional behavior testable without GPU/model loading.
    compute_backward must re-run every microbatch and fail on nonfinite loss.
    """
    snapshot=capture_rng()
    for attempt in range(max_retries+1):
        if attempt:restore_rng(snapshot)
        optimizer.zero_grad(set_to_none=True)
        loss=compute_backward(group)
        if not math.isfinite(loss):raise FloatingPointError('Nonfinite forward loss')
        scaler.unscale_(optimizer)
        good=finite_gradients()
        norm=float(clip_gradients()) if good else float('inf')
        if not good or not math.isfinite(norm):
            before=float(scaler.get_scale());after=before/2
            if not math.isfinite(after) or after<=0:raise FloatingPointError('Invalid AMP scale')
            # Explicit new_scale resets GradScaler optimizer state without any
            # optimizer.step, including finite individual grads but infinite norm.
            scaler.update(new_scale=after)
            on_overflow({'attempt':attempt+1,'scale_before':before,'scale_after':after,
                         'reason':'NONFINITE_GRADIENT' if not good else 'NONFINITE_GRADIENT_NORM',
                         'retryable':attempt<max_retries,'max_retries':max_retries})
            if attempt==max_retries:
                optimizer.zero_grad(set_to_none=True)
                raise FloatingPointError('AMP overflow retry budget exhausted')
            continue
        scaler.step(optimizer);scaler.update();scheduler.step()
        return {'loss':loss,'grad_norm':norm,'overflow_retries':attempt,'amp_scale':float(scaler.get_scale())}
    raise AssertionError('Unreachable AMP state')

def save(path,value):
    path=Path(path);temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');temp.replace(path)

def rows(path):
    return [json.loads(s) for s in Path(path).read_text(encoding='utf-8').splitlines() if s.strip()]

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def evaluate(model,tokenizer,examples,path,key,max_tokens=128,batch_size=8):
    import torch
    path=Path(path)
    metadata={'key':key,'ids':[r['sample_id'] for r in examples],'greedy':True,
              'enable_thinking':False,'max_new_tokens':max_tokens,'batch_size':batch_size,'eos_token_id':tokenizer.eos_token_id}
    meta=path.with_suffix('.metadata.json')
    if meta.exists():assert json.loads(meta.read_text())==metadata,'Evaluation changed; new run required'
    else:save(meta,metadata)
    cached={r['sample_id']:r for r in rows(path)} if path.exists() else {}
    model.eval();model.config.use_cache=True;tokenizer.padding_side='left'
    for start in range(0,len(examples),batch_size):
        batch=examples[start:start+batch_size]
        if all(r['sample_id'] in cached for r in batch):continue
        strings=[tokenizer.apply_chat_template(messages(r),tokenize=False,add_generation_prompt=True,enable_thinking=False) for r in batch]
        inputs=tokenizer(strings,padding=True,return_tensors='pt',add_special_tokens=False).to('cuda')
        with torch.inference_mode(): output=model.generate(**inputs,max_new_tokens=max_tokens,do_sample=False,
            pad_token_id=tokenizer.pad_token_id,eos_token_id=tokenizer.eos_token_id)
        for i,r in enumerate(batch):
            ids=output[i,inputs['input_ids'].shape[-1]:].tolist();ended=tokenizer.eos_token_id in ids
            if ended:ids=ids[:ids.index(tokenizer.eos_token_id)+1]
            truncated=not ended and len(ids)>=max_tokens;text=tokenizer.decode(ids,skip_special_tokens=True)
            cached[r['sample_id']]={'sample_id':r['sample_id'],'topic':r.get('topic','public_source'),
                'grade':r.get('grade'),'reference_status':r['target']['status'],
                'prediction':text,'generated_tokens':len(ids),'generated_ids':ids,'scores':score(r,text,truncated)}
        temp=path.with_suffix('.jsonl.tmp');temp.write_text(''.join(json.dumps(cached[r['sample_id']],ensure_ascii=False)+'\n'
            for r in examples if r['sample_id'] in cached),encoding='utf-8',newline='\n');temp.replace(path)
        print(f'EVAL {path.stem} {min(start+batch_size,len(examples))}/{len(examples)}',flush=True)
    records=[cached[r['sample_id']] for r in examples];summary=aggregate(records)
    summary['per_grade']={str(g):aggregate([r for r in records if r['grade']==g]) for g in sorted({r['grade'] for r in records},key=str)}
    summary['per_topic']={t:aggregate([r for r in records if r['topic']==t]) for t in sorted({r['topic'] for r in records})}
    save(path.with_suffix('.summary.json'),summary);return summary

def tensor_hashes(model):
    from peft import get_peft_model_state_dict
    return {k:hashlib.sha256(v.detach().float().cpu().contiguous().numpy().tobytes()).hexdigest()
            for k,v in get_peft_model_state_dict(model).items()}

def main(root):
    import importlib.metadata
    import torch
    from transformers import AutoTokenizer,AutoModelForCausalLM,get_cosine_schedule_with_warmup
    from peft import LoraConfig,get_peft_model,get_peft_model_state_dict,set_peft_model_state_dict,PeftModel
    root=Path(root);run=root/'runs'/RUN_ID;run.mkdir(parents=True,exist_ok=True)
    if (run/'completed_run.json').exists():print((run/'completed_run.json').read_text(),flush=True);return
    assert torch.cuda.is_available(),'GPU required'
    splits={s:rows(root/'data'/(s+'.jsonl')) for s in ('train','val','test')}
    fingerprints={s:sha(root/'data'/(s+'.jsonl')) for s in splits}
    manifest=json.loads((root/'data'/'frozen_manifest.json').read_text())
    assert manifest['fingerprints']==fingerprints
    dependencies=['verified_math_data_v2.py','verified_math_training_v2.py','train_verified_math_v2_stable.py']
    source_hashes={n:sha(root/'src'/n) for n in dependencies}
    order=list(range(len(splits['train'])));random.Random(SEED).shuffle(order)
    batches=[order[i:i+2] for i in range(0,len(order),2)];updates=math.ceil(len(batches)/2)
    config={'run_id':RUN_ID,'model_id':MODEL,'revision':REVISION,'seed':SEED,'epochs':1,
        'batch_size':2,'accumulation':2,'updates':updates,'lr':1e-4,'max_length':1024,
        'max_new_tokens':128,'eval_batch_size':8,'enable_thinking':False,'dataset_fingerprints':fingerprints,
        'source_hashes':source_hashes,'lora_r':16,'lora_alpha':32,
        'amp_init_scale':AMP_INIT_SCALE,'amp_growth_interval':AMP_GROWTH_INTERVAL,'amp_max_retries':AMP_MAX_RETRIES,
        'amp_retry_policy':'same full group and RNG; halve scale; no optimizer/scheduler/log advance on overflow',
        'criterion':'val solvable exact calculated answer + unit increases; guards, exact plans and per-grade math do not regress',
        'packages':{p:importlib.metadata.version(p) for p in ('torch','transformers','peft','accelerate')},
        'gpu':torch.cuda.get_device_name(0)}
    if (run/'config.json').exists():assert json.loads((run/'config.json').read_text())==config,'Changed config; new run required'
    else:save(run/'config.json',config)
    tok=AutoTokenizer.from_pretrained(MODEL,revision=REVISION)
    if tok.pad_token_id is None:tok.pad_token=tok.eos_token
    encoded=[serialize(r,tok,1024) for r in splits['train']]
    save(run/'token_audit.json',{'samples':len(encoded),'min_length':min(len(r['input_ids']) for r in encoded),
        'max_length':max(len(r['input_ids']) for r in encoded),'truncated':0,'assistant_only_loss':True,
        'training_ids':[r['sample_id'] for r in splits['train']]})
    base=AutoModelForCausalLM.from_pretrained(MODEL,revision=REVISION,dtype=torch.float16,attn_implementation='sdpa').to('cuda')
    save(run/'progress.json',{'phase':'baseline_validation'})
    baseline=evaluate(base,tok,splits['val'],run/'baseline_val.jsonl','base:'+REVISION)
    torch.manual_seed(SEED);torch.cuda.manual_seed_all(SEED)
    model=get_peft_model(base,LoraConfig(task_type='CAUSAL_LM',revision=REVISION,r=16,lora_alpha=32,lora_dropout=.05,
        bias='none',target_modules=['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj']))
    trainable=[p for p in model.parameters() if p.requires_grad]
    opt=torch.optim.AdamW(trainable,lr=1e-4,weight_decay=.01)
    sched=get_cosine_schedule_with_warmup(opt,max(1,round(updates*.05)),updates)
    scaler=torch.amp.GradScaler('cuda',init_scale=AMP_INIT_SCALE,growth_interval=AMP_GROWTH_INTERVAL)
    start=0;checkpoint=run/'resume_state.pt';state=None
    if checkpoint.exists():
        state=torch.load(checkpoint,map_location='cpu',weights_only=True)
        set_peft_model_state_dict(model,state['adapter']);opt.load_state_dict(state['optimizer']);sched.load_state_dict(state['scheduler']);scaler.load_state_dict(state['scaler'])
        start=state['step'];torch.set_rng_state(state['cpu_rng']);torch.cuda.set_rng_state(state['cuda_rng'])
        if (run/'training_log.jsonl').exists():
            committed=[r for r in rows(run/'training_log.jsonl') if r['step']<=start]
            (run/'training_log.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in committed),encoding='utf-8')
    model.gradient_checkpointing_enable();model.enable_input_require_grads();model.config.use_cache=False;model.train()
    begun=time.time();batch=None;loss=None
    for step in range(start,updates):
        group=batches[step*2:(step+1)*2]
        def compute_backward(indices_group):
            nonlocal batch,loss
            loss_sum=0
            for indices in indices_group:
                batch={k:torch.tensor(v,dtype=torch.long,device='cuda') for k,v in collate([encoded[i] for i in indices],tok.pad_token_id).items()}
                with torch.autocast('cuda',dtype=torch.float16):loss=model(**batch).loss
                if not bool(torch.isfinite(loss)):raise FloatingPointError('Nonfinite forward loss; aborted')
                loss_sum+=float(loss.detach());scaler.scale(loss/len(indices_group)).backward()
            return loss_sum/len(indices_group)
        def on_overflow(event):
            event={'step':step+1,'batch_ids':[splits['train'][i]['sample_id'] for indices in group for i in indices],
                   'seconds':round(time.time()-begun,2),**event}
            with (run/'amp_overflow_log.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(event)+'\n')
            save(run/'progress.json',{'phase':'amp_overflow_retry' if event['retryable'] else 'amp_retry_failed',
                **{k:v for k,v in event.items() if k!='batch_ids'},'total_steps':updates})
            print('AMP_OVERFLOW '+json.dumps({k:v for k,v in event.items() if k!='batch_ids'}),flush=True)
        def finite_gradients():
            grads=[p.grad for p in trainable if p.grad is not None]
            return bool(grads) and all(bool(torch.isfinite(g).all()) for g in grads)
        result=run_amp_update(group,compute_backward,opt,scaler,sched,
            lambda:(torch.get_rng_state(),torch.cuda.get_rng_state()),
            lambda states:(torch.set_rng_state(states[0]),torch.cuda.set_rng_state(states[1])),
            finite_gradients,lambda:torch.nn.utils.clip_grad_norm_(trainable,1.0),on_overflow)
        record={'step':step+1,**result,'lr':sched.get_last_lr()[0],
            'examples_seen':sum(len(x) for x in batches[:(step+1)*2]),'batch_ids':[splits['train'][i]['sample_id'] for indices in group for i in indices],
            'seconds':round(time.time()-begun,2),'peak_vram_gib':round(torch.cuda.max_memory_allocated()/2**30,3)}
        with (run/'training_log.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(record)+'\n')
        save(run/'progress.json',{'phase':'training',**{k:v for k,v in record.items() if k!='batch_ids'},'total_steps':updates})
        if (step+1)%10==0:print('TRAIN '+json.dumps({k:v for k,v in record.items() if k!='batch_ids'}),flush=True)
        if (step+1)%50==0 or step+1==updates:
            state={'step':step+1,'adapter':{k:v.detach().cpu() for k,v in get_peft_model_state_dict(model).items()},
                'optimizer':opt.state_dict(),'scheduler':sched.state_dict(),'scaler':scaler.state_dict(),
                'cpu_rng':torch.get_rng_state(),'cuda_rng':torch.cuda.get_rng_state()}
            temp=run/'resume_state.tmp';torch.save(state,temp);temp.replace(checkpoint)
            model.save_pretrained(run/'adapter');tok.save_pretrained(run/'adapter')
    expected=tensor_hashes(model);model.gradient_checkpointing_disable()
    del state,opt,sched,scaler,model,base,trainable,batch,loss
    import gc
    gc.collect();torch.cuda.empty_cache()
    fresh=AutoModelForCausalLM.from_pretrained(MODEL,revision=REVISION,dtype=torch.float16,attn_implementation='sdpa').to('cuda')
    model=PeftModel.from_pretrained(fresh,run/'adapter',is_trainable=False)
    assert tensor_hashes(model)==expected,'Reloaded weights differ'
    save(run/'reload_verification.json',{'passed':True,'tensor_count':len(expected),'fresh_base_revision':REVISION})
    weight_sha=sha(run/'adapter'/'adapter_model.safetensors')
    save(run/'progress.json',{'phase':'candidate_validation'})
    candidate=evaluate(model,tok,splits['val'],run/'candidate_val.jsonl','adapter:'+weight_sha)
    per_grade_ok=all(candidate['per_grade'][g]['solvable_correct']>=b['solvable_correct'] for g,b in baseline['per_grade'].items())
    improved=candidate['solvable_correct']>baseline['solvable_correct'] and candidate['guard_correct']>=baseline['guard_correct'] and candidate['plan_exact']>=baseline['plan_exact'] and per_grade_ok
    selected='adapter' if improved else 'base'
    save(run/'selection.json',{'selected':selected,'criterion':config['criterion'],'test_used_for_selection':False,
        'candidate_improved':improved,'per_grade_non_regression':per_grade_ok,'production_approved':False})
    save(run/'progress.json',{'phase':'selected_development_test','selected':selected})
    if selected=='base':
        with model.disable_adapter():test=evaluate(model,tok,splits['test'],run/'selected_dev_test.jsonl','base:'+REVISION)
    else:test=evaluate(model,tok,splits['test'],run/'selected_dev_test.jsonl','adapter:'+weight_sha)
    result={'status':'SFT_COMPLETED_RESEARCH_ONLY' if improved else 'SFT_REJECTED_VALIDATION_NONIMPROVEMENT',
        'run_id':RUN_ID,'steps':updates,'epochs':1,'train_examples_seen':len(encoded),'selected':selected,
        'baseline_validation':baseline,'candidate_validation':candidate,'selected_development_test':test,
        'adapter_sha256':weight_sha,'reload_verified':True,'production_approved':False,
        'limitations':['Finite synthetic wording families; no coverage guarantee for arbitrary Vietnamese problems.',
            'Math accuracy evaluates LLM plan with an exact calculator, not raw numeric LLM arithmetic.',
            'Public train additions are source-imported with independent arithmetic checks, not semantic or teacher certification.',
            'Heldout test is synthetic development data, not a secret independent school benchmark.',
            'No OCR-to-solution pipeline or student-facing deployment is certified.']}
    save(run/'completed_run.json',result);save(run/'progress.json',{'phase':'completed','status':result['status']})
    print('MVK_VERIFIED_V2_COMPLETED='+json.dumps(result,ensure_ascii=False),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);main(parser.parse_args().root)
