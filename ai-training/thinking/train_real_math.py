"""Two bounded full epochs on imported real problems; validation selects the model.

Research MCQ candidate only. Original verified planner stays intact.
"""
import argparse
import gc
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import time
from real_math_data import SYSTEM,prompt,validate,write_json,write_rows
from real_math_training import serialize,rotated,scores,summary
from planner_training_data import collate,epoch_batches

MODEL='Qwen/Qwen3-0.6B'
REVISION='c1899de289a04d12100db370d81485cdf75e47ca'
RUN_ID='qwen3_06b_real_mcq_2epoch_seed20261012'

def rows(path):
    return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]

def state_hashes(model):
    from peft import get_peft_model_state_dict
    return {k:hashlib.sha256(v.detach().float().cpu().contiguous().numpy().tobytes()).hexdigest() for k,v in get_peft_model_state_dict(model).items()}

def evaluate(model,tokenizer,data,path,key,shift=0,max_tokens=768):
    import torch
    path=Path(path)
    expected={'key':key,'sample_ids':[r['sample_id'] for r in data],'choice_rotation':shift,
              'max_tokens':max_tokens,'batch_size':8,'thinking':True,'temperature':0.6,'top_p':0.95,'top_k':20,'seed':20261012}
    meta=path.with_suffix('.metadata.json')
    if meta.exists():assert json.loads(meta.read_text(encoding='utf-8'))==expected,'Evaluation changed'
    else:write_json(meta,expected)
    cached={r['sample_id']:r for r in rows(path)} if path.exists() else {}
    model.eval();model.config.use_cache=True;tokenizer.padding_side='left'
    for start in range(0,len(data),8):
        group=data[start:start+8]
        if all(r['sample_id'] in cached for r in group):continue
        torch.manual_seed(20261012+start);torch.cuda.manual_seed_all(20261012+start)
        texts=[tokenizer.apply_chat_template([{'role':'system','content':SYSTEM},
               {'role':'user','content':prompt(r,rotated(r,shift)[0])}],tokenize=False,add_generation_prompt=True,enable_thinking=True) for r in group]
        inputs=tokenizer(texts,padding=True,add_special_tokens=False,return_tensors='pt').to('cuda')
        with torch.inference_mode():output=model.generate(**inputs,max_new_tokens=max_tokens,do_sample=True,
             temperature=0.6,top_p=0.95,top_k=20,pad_token_id=tokenizer.pad_token_id,eos_token_id=tokenizer.eos_token_id)
        for i,r in enumerate(group):
            ids=output[i,inputs['input_ids'].shape[-1]:].tolist();ended=tokenizer.eos_token_id in ids
            if ended:ids=ids[:ids.index(tokenizer.eos_token_id)+1]
            truncated=not ended and len(ids)>=max_tokens
            text=tokenizer.decode(ids,skip_special_tokens=True)
            if texts[i].rstrip().endswith('<think>') and not text.lstrip().startswith('<think>'):text='<think>\n'+text
            cached[r['sample_id']]={'sample_id':r['sample_id'],'grade':r['grade'],'prediction':text,
                'generated_tokens':len(ids),'scores':scores(r,text,truncated,shift)}
        write_rows(path,[cached[r['sample_id']] for r in data if r['sample_id'] in cached])
        print(f'EVAL {path.stem} {min(start+8,len(data))}/{len(data)}',flush=True)
        write_json(path.parent/'progress.json',{'phase':path.stem,'evaluated':min(start+8,len(data)),'total':len(data)})
    records=[cached[r['sample_id']] for r in data];result=summary(records)
    write_json(path.with_suffix('.summary.json'),result);return result

def main(root):
    import torch
    from transformers import AutoTokenizer,AutoModelForCausalLM,get_cosine_schedule_with_warmup
    from peft import LoraConfig,get_peft_model,get_peft_model_state_dict,set_peft_model_state_dict,PeftModel
    root=Path(root);run=root/'runs'/RUN_ID;run.mkdir(parents=True,exist_ok=True)
    if (run/'completed_run.json').exists():print((run/'completed_run.json').read_text(encoding='utf-8'));return
    assert torch.cuda.is_available()
    splits={s:rows(root/'data'/'clean'/(s+'.jsonl')) for s in ('train','val','test')};validate(splits)
    fingerprints={s:hashlib.sha256((root/'data'/'clean'/(s+'.jsonl')).read_bytes()).hexdigest() for s in splits}
    tokenizer=AutoTokenizer.from_pretrained(MODEL,revision=REVISION)
    if tokenizer.pad_token_id is None:tokenizer.pad_token=tokenizer.eos_token
    encoded=[];used=[];rejected=[]
    for row in splits['train']:
        try:item=serialize(row,tokenizer)
        except ValueError as error:rejected.append({'sample_id':row['sample_id'],'reason':str(error)});continue
        encoded.append(item);used.append(row)
    assert len(encoded)>=500,'Not enough useful training examples'
    write_rows(run/'training_token_rejections.jsonl',rejected)
    write_json(run/'token_audit.json',{'accepted':len(encoded),'rejected':len(rejected),
        'max_length':max(len(x['input_ids']) for x in encoded),'assistant_only_loss':True,
        'training_ids':[r['sample_id'] for r in used],'fixed_training_choice_rotations':True,'silent_truncation':False})
    schedule=[];epoch_ends=[]
    for epoch in range(2):
        b=epoch_batches(len(encoded),2,20261012+epoch)
        schedule.extend({'epoch':epoch+1,'batches':b[i:i+2]} for i in range(0,len(b),2));epoch_ends.append(len(schedule))
    config={'run_id':RUN_ID,'model':MODEL,'revision':REVISION,'seed':20261012,'epochs':2,
        'steps':len(schedule),'epoch_ends':epoch_ends,'train_examples':len(encoded),'lr':5e-5,
        'batch_size':2,'accumulation':2,'max_length':1536,'max_new_tokens':768,
        'dataset_fingerprints':fingerprints,'source_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'src').glob('*.py'))},
        'packages':{p:importlib.metadata.version(p) for p in ('torch','transformers','peft','accelerate','torchao')},
        'gpu':torch.cuda.get_device_name(0),'selection':'validation accuracy, then macro grade accuracy; tie prefers earlier/base',
        'test_used_for_selection':False,'label_quality':'source_imported_not_teacher_verified'}
    if (run/'config.json').exists():assert json.loads((run/'config.json').read_text(encoding='utf-8'))==config,'New config requires new run'
    else:write_json(run/'config.json',config)
    torch.manual_seed(20261012);torch.cuda.manual_seed_all(20261012)
    base=AutoModelForCausalLM.from_pretrained(MODEL,revision=REVISION,dtype=torch.float16,attn_implementation='sdpa').to('cuda')
    baseline=evaluate(base,tokenizer,splits['val'],run/'baseline_val.jsonl','base:'+REVISION)
    candidates=[{'name':'base','validation':baseline,'path':None}]
    model=get_peft_model(base,LoraConfig(task_type='CAUSAL_LM',r=16,lora_alpha=32,lora_dropout=0.05,bias='none',
          target_modules=['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj']))
    params=[p for p in model.parameters() if p.requires_grad]
    optimizer=torch.optim.AdamW(params,lr=5e-5,weight_decay=0.01)
    scheduler=get_cosine_schedule_with_warmup(optimizer,max(1,round(len(schedule)*0.05)),len(schedule))
    scaler=torch.amp.GradScaler('cuda');start=0
    checkpoint=run/'resume_state.pt'
    if checkpoint.exists():
        state=torch.load(checkpoint,map_location='cpu',weights_only=True)
        set_peft_model_state_dict(model,state['adapter']);optimizer.load_state_dict(state['optimizer'])
        scheduler.load_state_dict(state['scheduler']);scaler.load_state_dict(state['scaler']);start=state['step']
        torch.set_rng_state(state['cpu_rng']);torch.cuda.set_rng_state(state['cuda_rng'])
        log=[r for r in rows(run/'training_log.jsonl') if r['step']<=start];write_rows(run/'training_log.jsonl',log)
    started=time.time();batch=None;loss=None;state=None
    model.enable_input_require_grads()
    for step,group in enumerate(schedule):
        if step<start:
            if step+1 in epoch_ends:
                epoch=group['epoch'];path=run/f'epoch{epoch}_val.summary.json'
                if not path.exists():
                    assert start==step+1,'Missing earlier epoch validation: explicit recovery required'
                    model.gradient_checkpointing_disable()
                    adapter=run/f'adapter_epoch{epoch}'
                    evaluate(model,tokenizer,splits['val'],run/f'epoch{epoch}_val.jsonl','adapter:'+hashlib.sha256((adapter/'adapter_model.safetensors').read_bytes()).hexdigest())
                candidates.append({'name':f'epoch{epoch}','validation':json.loads(path.read_text(encoding='utf-8')),'path':str(run/f'adapter_epoch{epoch}')})
            continue
        model.train();model.config.use_cache=False
        if not model.is_gradient_checkpointing:model.gradient_checkpointing_enable()
        optimizer.zero_grad(set_to_none=True);total_loss=0
        for indices in group['batches']:
            values=collate([encoded[i] for i in indices],tokenizer.pad_token_id)
            batch={k:torch.tensor(v,dtype=torch.long,device='cuda') for k,v in values.items()}
            with torch.autocast('cuda',dtype=torch.float16):loss=model(**batch).loss
            assert torch.isfinite(loss),'Nonfinite loss'
            total_loss+=float(loss.detach());scaler.scale(loss/len(group['batches'])).backward()
        scaler.unscale_(optimizer);grad=torch.nn.utils.clip_grad_norm_(params,1.0);assert torch.isfinite(grad)
        scaler.step(optimizer);scaler.update();scheduler.step()
        record={'step':step+1,'epoch':group['epoch'],'loss':total_loss/len(group['batches']),
                'sample_ids':[used[i]['sample_id'] for indices in group['batches'] for i in indices],
                'seconds':round(time.time()-started,2),'peak_vram_gib':round(torch.cuda.max_memory_allocated()/2**30,3)}
        with (run/'training_log.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(record)+'\n')
        write_json(run/'progress.json',{'phase':'training','total_steps':len(schedule),**{k:v for k,v in record.items() if k!='sample_ids'}})
        if (step+1)%10==0:print('TRAIN '+json.dumps({k:v for k,v in record.items() if k!='sample_ids'}),flush=True)
        if (step+1)%25==0 or step+1 in epoch_ends:
            state={'step':step+1,'adapter':{k:v.detach().cpu() for k,v in get_peft_model_state_dict(model).items()},
                'optimizer':optimizer.state_dict(),'scheduler':scheduler.state_dict(),'scaler':scaler.state_dict(),
                'cpu_rng':torch.get_rng_state(),'cuda_rng':torch.cuda.get_rng_state()}
            torch.save(state,run/'resume_state.tmp');(run/'resume_state.tmp').replace(checkpoint)
        if step+1 in epoch_ends:
            epoch=group['epoch'];adapter=run/f'adapter_epoch{epoch}';model.save_pretrained(adapter);tokenizer.save_pretrained(adapter)
            model.gradient_checkpointing_disable()
            val=evaluate(model,tokenizer,splits['val'],run/f'epoch{epoch}_val.jsonl','adapter:'+hashlib.sha256((adapter/'adapter_model.safetensors').read_bytes()).hexdigest())
            candidates.append({'name':f'epoch{epoch}','validation':val,'path':str(adapter)})
            # Evaluation uses fixed seeds; resume must restore the post-evaluation RNG.
            state['cpu_rng']=torch.get_rng_state();state['cuda_rng']=torch.cuda.get_rng_state()
            torch.save(state,run/'resume_state.tmp');(run/'resume_state.tmp').replace(checkpoint)
    winner=max(candidates,key=lambda c:(c['validation']['accuracy'],c['validation']['macro_grade_accuracy']))
    write_json(run/'selection.json',{'selected':winner['name'],'candidates':candidates,'test_used_for_selection':False})
    if winner['path']:
        from safetensors.torch import load_file
        expected_tensors=load_file(str(Path(winner['path'])/'adapter_model.safetensors'))
    del model,base,optimizer,scheduler,scaler,params,batch,loss,state
    gc.collect();torch.cuda.empty_cache()
    fresh=AutoModelForCausalLM.from_pretrained(MODEL,revision=REVISION,dtype=torch.float16,attn_implementation='sdpa').to('cuda')
    selected=PeftModel.from_pretrained(fresh,winner['path'],is_trainable=False) if winner['path'] else fresh
    if winner['path']:
        actual=get_peft_model_state_dict(selected)
        assert set(actual)==set(expected_tensors)
        assert all(torch.equal(actual[k].cpu(),expected_tensors[k]) for k in actual),'Reload tensors mismatch'
    write_json(run/'reload_verification.json',{'passed':True,'fresh_base_revision':REVISION,'selected':winner['name']})
    test=evaluate(selected,tokenizer,splits['test'],run/'selected_test.jsonl',winner['name'])
    rotation=evaluate(selected,tokenizer,splits['test'],run/'selected_rotated_test.jsonl',winner['name'],shift=1)
    original={r['sample_id']:r for r in rows(run/'selected_test.jsonl')};changed=rows(run/'selected_rotated_test.jsonl')
    consistency=sum(original[r['sample_id']]['scores']['predicted_answer'] is not None and r['scores']['predicted_answer'] is not None and
         (ord(original[r['sample_id']]['scores']['predicted_answer'])-65)==(ord(r['scores']['predicted_answer'])-65+1)%4 for r in changed)/len(changed)
    result={'status':'COMPLETED_RESEARCH_MCQ_ONLY','run_id':RUN_ID,'baseline_validation':baseline,'selected':winner['name'],
        'selected_validation':winner['validation'],'selected_test':test,'rotated_test':rotation,'choice_rotation_consistency':consistency,
        'train_samples_per_epoch':len(encoded),'epochs':2,'steps':len(schedule),'reload_verified':True,'production_approved':False,
        'selected_adapter_path':winner['path'],'selected_adapter_sha256':hashlib.sha256((Path(winner['path'])/'adapter_model.safetensors').read_bytes()).hexdigest() if winner['path'] else None,
        'limitations':['Source-imported benchmark, not independently teacher-certified gold.','Public pretraining contamination unknown.',
         'MCQ choice accuracy is not proof of correct explanation or free-response/OCR quality.',
         'Few grade 1–3 examples; no grade 2 validation rows.','Existing grounded planner kept separately; this candidate does not replace safe runtime.']}
    write_json(run/'completed_run.json',result);write_json(run/'progress.json',{'phase':'completed','selected':winner['name']})
    print('MVK_REAL_MATH_COMPLETED='+json.dumps(result,ensure_ascii=False),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();main(a.root)
