"""GPU pilot: fixed baseline -> LoRA FP16 -> same validation -> held-out test.

Checkpoint is a research adapter, never automatically promoted to production.
Only the assistant completion contributes to the training loss.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import random
import time

import torch
from huggingface_hub import HfApi
from peft import LoraConfig, get_peft_model
from transformers import AutoTokenizer, AutoModelForCausalLM
from dataset import SYSTEM, validate
from metrics import score, aggregate

def write_json(path,value):
    path=Path(path); tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8'); tmp.replace(path)

def read_rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]

def prompt(row):
    grade=row['grade']; return f"Lớp: {grade if grade else 'chưa xác định'}.\nĐề: {row['problem']}\nGiải thích tối đa 80 từ rồi trả JSON theo cấu trúc đã yêu cầu."

def serialize(row,tokenizer):
    prefix=tokenizer.apply_chat_template([dict(role='system',content=SYSTEM),dict(role='user',content=prompt(row))],tokenize=False,add_generation_prompt=True,enable_thinking=True)
    opening='' if prefix.rstrip().endswith('<think>') else '<think>\n'
    completion=opening+row['worked_solution']+'\n</think>\n'+json.dumps(row['target'],ensure_ascii=False,separators=(',',':'))+tokenizer.eos_token
    a=tokenizer(prefix,add_special_tokens=False)['input_ids']; b=tokenizer(completion,add_special_tokens=False)['input_ids']
    assert b and a
    return dict(input_ids=a+b,labels=[-100]*len(a)+b,attention_mask=[1]*(len(a)+len(b)))

def selected(rows,per_topic=1):
    groups={}
    for row in sorted(rows,key=lambda r:r['sample_id']):
        values=groups.setdefault(row['topic'],[])
        if len(values)<per_topic: values.append(row)
    return [r for values in groups.values() for r in values]

def evaluate(model,tokenizer,rows,out,max_new_tokens=768):
    out=Path(out); cached={r['sample_id']:r for r in read_rows(out)} if out.exists() else {}
    model.eval(); model.config.use_cache=True
    records=[]
    for index,row in enumerate(rows):
        if row['sample_id'] in cached:
            records.append(cached[row['sample_id']]); continue
        torch.manual_seed(20261011+index); torch.cuda.manual_seed_all(20261011+index)
        inputs=tokenizer.apply_chat_template([dict(role='system',content=SYSTEM),dict(role='user',content=prompt(row))],tokenize=True,add_generation_prompt=True,enable_thinking=True,return_dict=True,return_tensors='pt').to('cuda')
        started=time.time()
        with torch.inference_mode():
            output=model.generate(**inputs,max_new_tokens=max_new_tokens,do_sample=True,temperature=0.6,top_p=0.95,top_k=20,pad_token_id=tokenizer.pad_token_id,eos_token_id=tokenizer.eos_token_id)
        ids=output[0,inputs['input_ids'].shape[-1]:]
        text=tokenizer.decode(ids,skip_special_tokens=True)
        # Some templates include <think> in the prompt, so decoding starts inside it.
        prefix=tokenizer.decode(inputs['input_ids'][0][-15:],skip_special_tokens=False)
        if prefix.rstrip().endswith('<think>') and not text.lstrip().startswith('<think>'): text='<think>\n'+text
        record=dict(sample_id=row['sample_id'],topic=row['topic'],grade=row['grade'],reference_status=row['target']['status'],prediction=text,scores=score(text,row['target']),truncated=len(ids)>=max_new_tokens and int(ids[-1])!=tokenizer.eos_token_id,generated_tokens=len(ids),seconds=round(time.time()-started,2))
        with out.open('a',encoding='utf-8') as stream: stream.write(json.dumps(record,ensure_ascii=False)+'\n')
        records.append(record)
        print(f"EVAL {out.stem} {index+1}/{len(rows)} correct={record['scores']['answer_correct']} truncated={record['truncated']}",flush=True)
    summary=aggregate(records)
    summary['per_grade']={str(g):aggregate([r for r in records if r['grade']==g]) for g in range(1,6)}
    write_json(out.with_suffix('.summary.json'),summary)
    return summary

def main(root,steps=32,accumulation=4):
    root=Path(root); assert torch.cuda.is_available(), 'T4/GPU required for this pilot'
    data=root/'data'; splits={s:read_rows(data/f'{s}.jsonl') for s in ('train','val','test')}
    validate(sum(splits.values(),[]))
    run=root/'runs'/f'qwen3_06b_lora_pilot{steps}_seed20261011'; run.mkdir(parents=True,exist_ok=True)
    if (run/'completed_run.json').exists():
        print((run/'completed_run.json').read_text(encoding='utf-8')); return
    torch.manual_seed(20261011); torch.cuda.manual_seed_all(20261011)
    config_path=run/'config.json'
    if config_path.exists(): config=json.loads(config_path.read_text(encoding='utf-8'))
    else:
        config=dict(model_id='Qwen/Qwen3-0.6B',model_revision=HfApi().model_info('Qwen/Qwen3-0.6B').sha,max_steps=steps,gradient_accumulation=accumulation,learning_rate=1e-4,lora_r=16,lora_alpha=32,max_length=1024,max_new_tokens=768,seed=20261011,precision='FP16 LoRA',dataset_report=json.loads((data/'dataset_report.json').read_text(encoding='utf-8')),packages={p:importlib.metadata.version(p) for p in ('torch','transformers','peft','accelerate')},gpu=torch.cuda.get_device_name(0))
        write_json(config_path,config)
    fingerprints={s:hashlib.sha256((data/f'{s}.jsonl').read_bytes()).hexdigest() for s in splits}
    assert fingerprints==config['dataset_report']['fingerprints'], 'Dataset changed: choose a new run ID'
    assert config['max_steps']==steps and config['gradient_accumulation']==accumulation
    tokenizer=AutoTokenizer.from_pretrained(config['model_id'],revision=config['model_revision'])
    if tokenizer.pad_token_id is None: tokenizer.pad_token=tokenizer.eos_token
    encoded=[serialize(row,tokenizer) for row in splits['train']]
    lengths=[len(r['input_ids']) for r in encoded]
    assert max(lengths)<=config['max_length'], f'Long sample {max(lengths)}: never silently truncate labels'
    assert all(any(v!=-100 for v in r['labels']) for r in encoded)
    write_json(run/'token_audit.json',dict(samples=len(encoded),max_length=max(lengths),min_length=min(lengths),assistant_only_loss=True,examples_truncated=0))
    val=selected(splits['val']); test=selected(splits['test'])
    write_json(run/'fixed_eval_ids.json',dict(val=[r['sample_id'] for r in val],test=[r['sample_id'] for r in test],selection='one per topic, fixed before baseline; not all held-out data'))
    print('Loading pinned Qwen3-0.6B',config['model_revision'],flush=True)
    base=AutoModelForCausalLM.from_pretrained(config['model_id'],revision=config['model_revision'],dtype=torch.float16,attn_implementation='sdpa').to('cuda')
    baseline=evaluate(base,tokenizer,val,run/'baseline_val.jsonl',config['max_new_tokens'])
    model=get_peft_model(base,LoraConfig(task_type='CAUSAL_LM',revision=config['model_revision'],r=16,lora_alpha=32,lora_dropout=0.05,target_modules=['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj'],bias='none'))
    trainable=[p for p in model.parameters() if p.requires_grad]
    write_json(run/'parameters.json',dict(trainable=sum(p.numel() for p in trainable),total=sum(p.numel() for p in model.parameters())))
    optimizer=torch.optim.AdamW(trainable,lr=config['learning_rate'],weight_decay=0.01)
    scaler=torch.amp.GradScaler('cuda'); start=0
    state_path=run/'resume_state.pt'
    if state_path.exists():
        from peft import set_peft_model_state_dict
        state=torch.load(state_path,map_location='cpu',weights_only=True)
        set_peft_model_state_dict(model,state['adapter']); optimizer.load_state_dict(state['optimizer']); scaler.load_state_dict(state['scaler']); start=state['step']
        torch.set_rng_state(state['cpu_rng']); torch.cuda.set_rng_state(state['cuda_rng'])
    else:
        torch.manual_seed(20261011); torch.cuda.manual_seed_all(20261011)
    order=list(range(len(encoded))); random.Random(20261011).shuffle(order)
    model.gradient_checkpointing_enable(); model.enable_input_require_grads(); model.config.use_cache=False; model.train()
    started=time.time()
    for update in range(start,steps):
        optimizer.zero_grad(set_to_none=True); loss_sum=0.0
        for micro in range(accumulation):
            row=encoded[order[(update*accumulation+micro)%len(order)]]
            batch={k:torch.tensor([v],dtype=torch.long,device='cuda') for k,v in row.items()}
            with torch.autocast('cuda',dtype=torch.float16): loss=model(**batch).loss
            if not torch.isfinite(loss): raise RuntimeError('Non-finite loss: training stopped')
            loss_sum+=float(loss.detach()); scaler.scale(loss/accumulation).backward()
        scaler.unscale_(optimizer); grad=torch.nn.utils.clip_grad_norm_(trainable,1.0)
        if not torch.isfinite(grad): raise RuntimeError('Non-finite gradient: training stopped')
        scaler.step(optimizer); scaler.update()
        record=dict(step=update+1,loss=loss_sum/accumulation,grad_norm=float(grad),seconds=round(time.time()-started,2),peak_vram_gib=round(torch.cuda.max_memory_allocated()/2**30,3))
        with (run/'training_log.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps(record)+'\n')
        print('TRAIN',json.dumps(record),flush=True)
        if (update+1)%8==0 or update+1==steps:
            from peft import get_peft_model_state_dict
            state=dict(step=update+1,adapter={k:v.detach().cpu() for k,v in get_peft_model_state_dict(model).items()},optimizer=optimizer.state_dict(),scaler=scaler.state_dict(),cpu_rng=torch.get_rng_state(),cuda_rng=torch.cuda.get_rng_state())
            tmp=run/'resume_state.tmp'; torch.save(state,tmp); tmp.replace(state_path)
            model.save_pretrained(run/'adapter'); tokenizer.save_pretrained(run/'adapter')
    model.gradient_checkpointing_disable()
    candidate=evaluate(model,tokenizer,val,run/'candidate_val.jsonl',config['max_new_tokens'])
    # Test is never used to pick training settings or the base-vs-adapter winner.
    test_metrics=evaluate(model,tokenizer,test,run/'candidate_test.jsonl',config['max_new_tokens'])
    adapter=run/'adapter'/'adapter_model.safetensors'
    report=dict(status='PILOT_COMPLETED_NOT_PRODUCTION',baseline_validation=baseline,candidate_validation=candidate,candidate_test=test_metrics,steps=steps,examples_seen=steps*accumulation,adapter_path=str(adapter.parent),adapter_sha256=hashlib.sha256(adapter.read_bytes()).hexdigest(),production_approved=False,promotion='No automatic promotion; small synthetic test is insufficient.',limitations=['32-step smoke/pilot is not full training.','Only selected 12 topic families, few guard examples.','Strict reference-plan matching rejects some equivalent valid plans.','No independent teacher-reviewed real-problem benchmark yet.','Specialization does not erase other base-model knowledge.'])
    write_json(run/'completed_run.json',report); print('MVK_PILOT_COMPLETED='+json.dumps(report,ensure_ascii=False),flush=True)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--root',required=True); p.add_argument('--steps',type=int,default=32)
    args=p.parse_args(); main(args.root,args.steps)
