"""One complete SFT epoch, all validation rows, reload verification and dev test.

Selection uses validation only. Runtime grammar guarantees are reported apart
from model planning quality. Nothing here approves a student-facing deployment.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import time

from planner_training_data import serialize,collate,epoch_batches
from planner_metrics import score_prediction,aggregate
from scope_dataset import validate,SYSTEM,prompt

MODEL='Qwen/Qwen3-0.6B'
REVISION='c1899de289a04d12100db370d81485cdf75e47ca'
RUN_ID='qwen3_06b_grounded_sft_epoch1_seed20261012'

def save_json(path,value):
    path=Path(path); temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n'); temp.replace(path)

def rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]

def evaluate(model,tokenizer,examples,path,key,batch_size=8,max_tokens=256):
    import torch
    path=Path(path); meta=path.with_suffix('.metadata.json')
    expected={'key':key,'ids':[r['sample_id'] for r in examples],
              'batch_size':batch_size,'max_tokens':max_tokens,'seed':20261012,
              'sampling':{'temperature':0.6,'top_p':0.95,'top_k':20,'thinking':True}}
    if meta.exists(): assert json.loads(meta.read_text(encoding='utf-8'))==expected, 'Evaluation changed: new run required'
    else: save_json(meta,expected)
    cached={r['sample_id']:r for r in rows(path)} if path.exists() else {}
    model.eval(); model.config.use_cache=True; tokenizer.padding_side='left'
    for start in range(0,len(examples),batch_size):
        batch=examples[start:start+batch_size]
        if all(r['sample_id'] in cached for r in batch): continue
        # Recompute a partially cached batch with its original padding/seed.
        torch.manual_seed(20261012+start); torch.cuda.manual_seed_all(20261012+start)
        strings=[tokenizer.apply_chat_template([{'role':'system','content':SYSTEM},
                 {'role':'user','content':prompt(r)}],tokenize=False,add_generation_prompt=True,enable_thinking=True) for r in batch]
        inputs=tokenizer(strings,return_tensors='pt',padding=True,add_special_tokens=False).to('cuda')
        started=time.time()
        with torch.inference_mode():
            output=model.generate(**inputs,max_new_tokens=max_tokens,do_sample=True,
                temperature=0.6,top_p=0.95,top_k=20,pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id)
        for i,row in enumerate(batch):
            ids=output[i,inputs['input_ids'].shape[-1]:].tolist()
            # The first EOS belongs to this row, later batch padding does not.
            ended=tokenizer.eos_token_id in ids
            if ended: ids=ids[:ids.index(tokenizer.eos_token_id)+1]
            truncated=not ended and len(ids)>=max_tokens
            text=tokenizer.decode(ids,skip_special_tokens=True)
            if strings[i].rstrip().endswith('<think>') and not text.lstrip().startswith('<think>'): text='<think>\n'+text
            cached[row['sample_id']]={'sample_id':row['sample_id'],'topic':row['topic'],
                'grade':row['grade'],'reference_status':row['target']['status'],
                'prediction':text,'generated_tokens':len(ids),'scores':score_prediction(row,text,truncated)}
        temp=path.with_suffix('.jsonl.tmp')
        temp.write_text(''.join(json.dumps(cached[r['sample_id']],ensure_ascii=False)+'\n' for r in examples if r['sample_id'] in cached),encoding='utf-8',newline='\n'); temp.replace(path)
        print(f'EVAL {path.stem} {min(start+batch_size,len(examples))}/{len(examples)} seconds={time.time()-started:.1f}',flush=True)
    records=[cached[r['sample_id']] for r in examples]
    summary=aggregate(records)
    summary['per_topic']={topic:aggregate([r for r in records if r['topic']==topic]) for topic in sorted({r['topic'] for r in records})}
    save_json(path.with_suffix('.summary.json'),summary)
    return summary

def adapter_hashes(model):
    from peft import get_peft_model_state_dict
    return {k:hashlib.sha256(v.detach().float().cpu().contiguous().numpy().tobytes()).hexdigest()
            for k,v in get_peft_model_state_dict(model).items()}

def main(root):
    import importlib.metadata
    import torch
    from transformers import AutoTokenizer,AutoModelForCausalLM,get_cosine_schedule_with_warmup
    from peft import LoraConfig,get_peft_model,get_peft_model_state_dict,set_peft_model_state_dict,PeftModel
    root=Path(root); run=root/'runs'/RUN_ID; run.mkdir(parents=True,exist_ok=True)
    if (run/'completed_run.json').exists():
        print('MVK_PLANNER_COMPLETED='+(run/'completed_run.json').read_text(encoding='utf-8'),flush=True); return
    assert torch.cuda.is_available(),'GPU required'
    splits={s:rows(root/'data'/(s+'.jsonl')) for s in ('train','val','test')}
    validate(sum(splits.values(),[]))
    report=json.loads((root/'data'/'dataset_report.json').read_text(encoding='utf-8'))
    fingerprints={s:hashlib.sha256((root/'data'/(s+'.jsonl')).read_bytes()).hexdigest() for s in splits}
    assert fingerprints==report['fingerprints']
    deps=['train_scope_planner.py','planner_training_data.py','planner_metrics.py','scope_contract.py','scope_dataset.py']
    source_hashes={p:hashlib.sha256((root/'src'/p).read_bytes()).hexdigest() for p in deps}
    batches=epoch_batches(len(splits['train']),2); updates=math.ceil(len(batches)/2)
    config={'model_id':MODEL,'revision':REVISION,'run_id':RUN_ID,'seed':20261012,
        'epochs':1,'batch_size':2,'accumulation':2,'max_steps':updates,'max_length':1024,
        'max_new_tokens':256,'eval_batch_size':8,'lr':1e-4,'lora_r':16,'lora_alpha':32,
        'warmup_steps':max(1,round(updates*0.05)),'dataset_fingerprints':fingerprints,'source_hashes':source_hashes,
        'packages':{p:importlib.metadata.version(p) for p in ('torch','transformers','peft','accelerate','torchao')},
        'gpu':torch.cuda.get_device_name(0),'test_role':'synthetic development, not independent real benchmark'}
    if (run/'config.json').exists(): assert json.loads((run/'config.json').read_text(encoding='utf-8'))==config,'Changed config/data/code/runtime: use new run ID'
    else: save_json(run/'config.json',config)
    tokenizer=AutoTokenizer.from_pretrained(MODEL,revision=REVISION)
    if tokenizer.pad_token_id is None: tokenizer.pad_token=tokenizer.eos_token
    encoded=[serialize(r,tokenizer,config['max_length']) for r in splits['train']]
    lengths=[len(r['input_ids']) for r in encoded]
    save_json(run/'token_audit.json',{'samples':len(encoded),'min_length':min(lengths),'max_length':max(lengths),
        'truncated':0,'assistant_only_loss':True,'all_supervised_completions_have_final_plan':True})
    torch.manual_seed(config['seed']); torch.cuda.manual_seed_all(config['seed'])
    base=AutoModelForCausalLM.from_pretrained(MODEL,revision=REVISION,dtype=torch.float16,attn_implementation='sdpa').to('cuda')
    baseline=evaluate(base,tokenizer,splits['val'],run/'baseline_val.jsonl','base:'+REVISION)
    model=get_peft_model(base,LoraConfig(task_type='CAUSAL_LM',revision=REVISION,r=16,lora_alpha=32,
        lora_dropout=0.05,bias='none',target_modules=['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj']))
    trainable=[p for p in model.parameters() if p.requires_grad]
    save_json(run/'parameters.json',{'trainable':sum(p.numel() for p in trainable),'total':sum(p.numel() for p in model.parameters())})
    optimizer=torch.optim.AdamW(trainable,lr=config['lr'],weight_decay=0.01)
    scheduler=get_cosine_schedule_with_warmup(optimizer,config['warmup_steps'],updates)
    scaler=torch.amp.GradScaler('cuda'); start=0
    checkpoint=run/'resume_state.pt'
    if checkpoint.exists():
        state=torch.load(checkpoint,map_location='cpu',weights_only=True)
        set_peft_model_state_dict(model,state['adapter']); optimizer.load_state_dict(state['optimizer'])
        scheduler.load_state_dict(state['scheduler']); scaler.load_state_dict(state['scaler']); start=state['step']
        torch.set_rng_state(state['cpu_rng']); torch.cuda.set_rng_state(state['cuda_rng'])
        # Discard uncommitted log rows after the last saved checkpoint.
        if (run/'training_log.jsonl').exists():
            log=[r for r in rows(run/'training_log.jsonl') if r['step']<=start]
            (run/'training_log.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in log),encoding='utf-8',newline='\n')
    else:
        torch.manual_seed(config['seed']); torch.cuda.manual_seed_all(config['seed'])
    model.gradient_checkpointing_enable(); model.enable_input_require_grads(); model.config.use_cache=False; model.train()
    started=time.time(); batch=None; loss=None
    for step in range(start,updates):
        optimizer.zero_grad(set_to_none=True); loss_sum=0.0
        group=batches[step*2:(step+1)*2]
        for indices in group:
            values=collate([encoded[i] for i in indices],tokenizer.pad_token_id)
            batch={k:torch.tensor(v,dtype=torch.long,device='cuda') for k,v in values.items()}
            with torch.autocast('cuda',dtype=torch.float16): loss=model(**batch).loss
            if not torch.isfinite(loss): raise RuntimeError('Nonfinite loss')
            loss_sum+=float(loss.detach()); scaler.scale(loss/len(group)).backward()
        scaler.unscale_(optimizer); norm=torch.nn.utils.clip_grad_norm_(trainable,1.0)
        if not torch.isfinite(norm): raise RuntimeError('Nonfinite gradient')
        scaler.step(optimizer); scaler.update(); scheduler.step()
        record={'step':step+1,'loss':loss_sum/len(group),'grad_norm':float(norm),
                'lr':scheduler.get_last_lr()[0],'examples_seen':sum(len(b) for b in batches[:(step+1)*2]),
                'seconds':round(time.time()-started,2),'peak_vram_gib':round(torch.cuda.max_memory_allocated()/2**30,3)}
        with (run/'training_log.jsonl').open('a',encoding='utf-8') as stream: stream.write(json.dumps(record)+'\n')
        save_json(run/'progress.json',{'phase':'training',**record,'total_steps':updates})
        if (step+1)%10==0: print('TRAIN '+json.dumps(record),flush=True)
        if (step+1)%50==0 or step+1==updates:
            state={'step':step+1,'adapter':{k:v.detach().cpu() for k,v in get_peft_model_state_dict(model).items()},
                'optimizer':optimizer.state_dict(),'scheduler':scheduler.state_dict(),'scaler':scaler.state_dict(),
                'cpu_rng':torch.get_rng_state(),'cuda_rng':torch.cuda.get_rng_state()}
            temp=run/'resume_state.tmp'; torch.save(state,temp); temp.replace(checkpoint)
            model.save_pretrained(run/'adapter'); tokenizer.save_pretrained(run/'adapter')
    before_hashes=adapter_hashes(model)
    model.gradient_checkpointing_disable()
    del state,optimizer,scheduler,scaler,model,base,trainable,batch,loss
    import gc
    gc.collect(); torch.cuda.empty_cache()
    # Actual adapter reload from saved files, on a fresh pinned base model.
    reloaded_base=AutoModelForCausalLM.from_pretrained(MODEL,revision=REVISION,dtype=torch.float16,attn_implementation='sdpa').to('cuda')
    model=PeftModel.from_pretrained(reloaded_base,run/'adapter',is_trainable=False)
    assert adapter_hashes(model)==before_hashes,'Reloaded adapter tensors differ'
    save_json(run/'reload_verification.json',{'passed':True,'tensor_count':len(before_hashes),'fresh_base_revision':REVISION})
    weight=run/'adapter'/'adapter_model.safetensors'; sha=hashlib.sha256(weight.read_bytes()).hexdigest()
    save_json(run/'progress.json',{'phase':'candidate_validation','step':updates})
    candidate=evaluate(model,tokenizer,splits['val'],run/'candidate_val.jsonl','adapter:'+sha)
    selected='adapter' if candidate['raw_plan_accuracy']>baseline['raw_plan_accuracy'] else 'base'
    # Test data is consumed only after the validation selection is fixed.
    save_json(run/'selection.json',{'selected':selected,'criterion':'strict raw-plan accuracy on all validation rows','test_used_for_selection':False})
    save_json(run/'progress.json',{'phase':'selected_development_test','selected':selected})
    if selected=='base':
        with model.disable_adapter(): test=evaluate(model,tokenizer,splits['test'],run/'selected_dev_test.jsonl','base:'+REVISION)
    else: test=evaluate(model,tokenizer,splits['test'],run/'selected_dev_test.jsonl','adapter:'+sha)
    result={'status':'SFT_COMPLETED_RESEARCH_ONLY','run_id':RUN_ID,'steps':updates,'epochs':1,
        'train_examples_seen':len(encoded),'baseline_validation':baseline,'candidate_validation':candidate,
        'selected':selected,'selected_development_test':test,'adapter_sha256':sha,'adapter_path':str(weight.parent),
        'reload_verified':True,'production_approved':False,
        'limitations':['Four topic families and 32 fixed grammars, not full grades 1-5.',
            'Test is synthetic development data, no independent teacher-reviewed benchmark.',
            'Source facts are grammar extracted; this is not free-text/OCR semantic understanding.',
            'The verifier calculates answers; raw LLM arithmetic quality is not measured.',
            'The public generated explanation is not evaluated pedagogically.',
            'Runtime guard correctness is enforced by code, not proof the LLM refuses every off-topic request.',
            'Inference cap 256 tokens; truncations are counted as failures.']}
    save_json(run/'completed_run.json',result); save_json(run/'progress.json',{'phase':'completed','status':result['status']})
    print('MVK_PLANNER_COMPLETED='+json.dumps(result,ensure_ascii=False),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--root',required=True)
    main(parser.parse_args().root)
