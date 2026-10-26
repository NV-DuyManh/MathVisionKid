#!/usr/bin/env python3
"""Fixed-sample Torch/PEFT baseline benchmark; GPU only when manually launched.
No optimizer steps, evaluation corpus, or Drive operations. Benchmarking must be
serialized with the training worker (same GPU).
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, sys, time
from pathlib import Path

MODEL="Qwen/Qwen3-1.7B"
REVISION="70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
RECIPE_SHA256="1bb69c394c7eaaea7034125c6b3361eebbbe0d77e0715a8454331fbe7cee3ff8"
EXPECTED_CHAT_MEMBERS=32
EXPECTED_TRAIN_ROWS=6502344
MODES={"worked_solution","hint_level_1","hint_level_2","hint_level_3"}
TARGET_MODULES=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"]


def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()


def atomic_json(path,obj):
 path=Path(path); tmp=path.with_suffix(path.suffix+'.pending')
 tmp.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
 os.replace(tmp,path)


def load_helper(path):
 spec=importlib.util.spec_from_file_location('exhaustive_colab_loader',path)
 if not spec or not spec.loader:raise RuntimeError('cannot import assistant-only tokenizer helper')
 mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod);return mod


def raw_rows(path):
 with Path(path).open('rb') as f:
  for n,line in enumerate(f,1):
   raw=line.rstrip(b'\r\n')
   if not raw.strip():raise ValueError(f'blank train-view row {n}')
   yield n,raw


def expected_hashes(manifest):
 if manifest.get('recipe_sha256')!=RECIPE_SHA256:raise ValueError('wrong recipe SHA')
 if manifest.get('members_complete')!=EXPECTED_CHAT_MEMBERS or manifest.get('raw_train_rows_scanned')!=EXPECTED_TRAIN_ROWS:raise ValueError('manifest lacks exact all-members/all-train-row scan evidence')
 if manifest.get('all_four_modes_preserved') is not True:raise ValueError('manifest does not preserve four modes')
 if manifest.get('training_view_sha256') is None:raise ValueError('manifest lacks materialized view SHA')
 cases=manifest.get('selected_cases_manifest')
 if not isinstance(cases,list):raise ValueError('manifest lacks selected case row bindings')
 out={}
 for c in cases:
  modes=c.get('rows',{})
  if set(modes)!=MODES:raise ValueError('selected case missing one or more modes')
  for entry in modes.values():
   sid=entry.get('sample_id'); digest=entry.get('row_sha256')
   if not sid or not digest or sid in out:raise ValueError('duplicate/missing sample/hash binding')
   out[sid]=digest
 if len(out)!=manifest.get('selected_chat_rows'):raise ValueError('selected count does not match manifest bindings')
 return out


def load_encoded(path,manifest,helper,tokenizer,max_len):
 expected=expected_hashes(manifest); found=set(); rows=[]; cases={}
 for n,raw in raw_rows(path):
  digest=hashlib.sha256(raw).hexdigest(); row=json.loads(raw.decode('utf-8')); sid=row.get('sample_id')
  if row.get('split')!='train':raise ValueError(f'nontrain at row {n}')
  if not sid or sid not in expected or expected[sid]!=digest:raise ValueError(f'row SHA/sample mismatch at row {n}')
  if sid in found:raise ValueError(f'duplicate sample at row {n}')
  found.add(sid); case=row.get('case_group_id'); cases.setdefault(case,set()).add(row.get('mode'))
  enc=helper.tokenize_assistant_only(row,tokenizer,max_sequence_tokens=max_len)
  if len(enc['input_ids'])!=len(enc['labels']) or not any(x!=-100 for x in enc['labels']):raise ValueError(f'invalid assistant mask: {sid}')
  rows.append({'sample_id':sid,'case_group_id':case,'mode':row['mode'],'encoded':enc})
 if found!=set(expected):raise ValueError('materialized view ID set mismatch')
 if any(v!=MODES for v in cases.values()):raise ValueError('incomplete four-mode case')
 if sha(path)!=manifest['training_view_sha256']:raise ValueError('materialized JSONL SHA mismatch')
 return rows


def fixed_quantiles(rows):
 ordered=sorted(rows,key=lambda r:len(r['encoded']['input_ids']))
 if len(ordered)<16:raise ValueError('need at least 16 rows for comparable benchmark')
 return [ordered[round(i*(len(ordered)-1)/15)] for i in range(16)]


def batch(items,pad_id,device,torch):
 width=max(len(x['encoded']['input_ids']) for x in items); ids=[]; att=[]; labs=[]
 for x in items:
  e=x['encoded']; n=width-len(e['input_ids'])
  ids.append(e['input_ids']+[pad_id]*n);att.append(e['attention_mask']+[0]*n);labs.append(e['labels']+[-100]*n)
 return {'input_ids':torch.tensor(ids,dtype=torch.long,device=device),'attention_mask':torch.tensor(att,dtype=torch.long,device=device),'labels':torch.tensor(labs,dtype=torch.long,device=device)}


def run(args):
 import torch
 if not torch.cuda.is_available() or 't4' not in torch.cuda.get_device_name(0).lower():raise RuntimeError('requires isolated NVIDIA T4; no other GPU accepted')
 if torch.cuda.get_device_capability(0)!=(7,5):raise RuntimeError('expected T4 compute capability 7.5')
 torch.manual_seed(20261023);torch.cuda.manual_seed_all(20261023)
 from transformers import AutoModelForCausalLM,AutoTokenizer,BitsAndBytesConfig
 from peft import LoraConfig,get_peft_model
 cfg=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=torch.float16)
 tokenizer=AutoTokenizer.from_pretrained(MODEL,revision=REVISION,trust_remote_code=False)
 model=AutoModelForCausalLM.from_pretrained(MODEL,revision=REVISION,trust_remote_code=False,quantization_config=cfg,device_map={'':'cuda:0'},torch_dtype=torch.float16,attn_implementation='sdpa')
 model=get_peft_model(model,LoraConfig(r=16,lora_alpha=16,lora_dropout=0.0,bias='none',task_type='CAUSAL_LM',target_modules=TARGET_MODULES))
 model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
 model.enable_input_require_grads();model.train()
 helper=load_helper(args.tokenizer_helper);manifest=json.loads(args.manifest.read_text(encoding='utf-8'))
 rows=load_encoded(args.train_view,manifest,helper,tokenizer,args.max_seq_len); selected=fixed_quantiles(rows)
 device=torch.device('cuda');pad_id=tokenizer.pad_token_id or 151643; torch.cuda.synchronize()
 baseline_rng=(torch.get_rng_state(),torch.cuda.get_rng_state_all()); results={}
 # At most 1 warm-up and 2 timed full 16-row forward/backward groups per mode.
 for micro in (1,2):
  accum=16//micro; reps=[]; peak=0; failure=None
  try:
   for repeat in range(3):
    torch.set_rng_state(baseline_rng[0]);torch.cuda.set_rng_state_all(baseline_rng[1]);model.zero_grad(set_to_none=True)
    # Untimed warm-up first, then independent measured groups at unchanged weights.
    if repeat==0:
     for begin in range(0,16,micro):
      items=selected[begin:begin+micro]; b=batch(items,pad_id,device,torch)
      with torch.autocast('cuda',dtype=torch.float16):loss=model(**b).loss*(len(items)/16)
      if not torch.isfinite(loss):raise FloatingPointError('nonfinite warmup loss')
      loss.backward()
      del b,loss
     model.zero_grad(set_to_none=True);torch.cuda.synchronize();continue
    model.zero_grad(set_to_none=True);torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();start=time.monotonic();nonpad=sup=0
    for begin in range(0,16,micro):
     items=selected[begin:begin+micro]; b=batch(items,pad_id,device,torch)
     with torch.autocast('cuda',dtype=torch.float16):loss=model(**b).loss*(len(items)/16)
     if not torch.isfinite(loss):raise FloatingPointError('nonfinite loss')
     loss.backward()
     grads=[param.grad for param in model.parameters() if param.grad is not None]
     if any(not torch.isfinite(g).all().item() for g in grads):raise FloatingPointError('nonfinite gradient')
     nonpad+=int(b['attention_mask'].sum().item());sup+=sum(sum(t!=-100 for t in x['encoded']['labels']) for x in items)
     del b,loss
    torch.cuda.synchronize();secs=max(time.monotonic()-start,1e-9);peak=max(peak,int(torch.cuda.max_memory_allocated()))
    reps.append({'group_seconds':secs,'unique_examples':16,'nonpad_tokens':nonpad,'supervised_tokens':sup})
    model.zero_grad(set_to_none=True)
  except torch.cuda.OutOfMemoryError:
   failure='OOM';model.zero_grad(set_to_none=True);torch.cuda.empty_cache()
  finally:
   model.zero_grad(set_to_none=True)
  total=sum(x['group_seconds'] for x in reps)
  results[str(micro)]={'state':'PASS' if len(reps)==2 and failure is None else (failure or 'BENCHMARK_FAILED'),'optimizer_steps':0,'warmup_groups':1,'timed_groups':len(reps),'timed_repeats':reps,'mean_group_seconds':total/len(reps) if reps else None,'unique_examples_per_second':(16*len(reps)/total) if total else 0,'nonpad_tokens_per_second':sum(x['nonpad_tokens'] for x in reps)/total if total else 0,'supervised_tokens_per_second':sum(x['supervised_tokens'] for x in reps)/total if total else 0,'peak_vram_bytes':peak}
 if results['1']['state']!='PASS':raise RuntimeError('microbatch-1 baseline failed; cannot provide safe baseline')
 torch.set_rng_state(baseline_rng[0]);torch.cuda.set_rng_state_all(baseline_rng[1]);model.zero_grad(set_to_none=True)
 import transformers,peft,bitsandbytes
 report={'schema':'MathVisionKid.t4_fixed16_torch_baseline.v1','state':'PASS','model':MODEL,'revision':REVISION,'quantization':'NF4 double quant','compute_dtype':'float16','adapter':{'r':16,'target_modules':TARGET_MODULES},'attention':'sdpa','gradient_checkpointing':True,'loss':'native Transformers causal-LM shifted cross entropy; not the prior V3 selected-logit sparse kernel','same_quantile_examples':True,'rng_seed':20261023,'framework_versions':{'torch':torch.__version__,'cuda_runtime':torch.version.cuda,'transformers':transformers.__version__,'peft':peft.__version__,'bitsandbytes':bitsandbytes.__version__},'unique_sample_ids':[x['sample_id'] for x in selected],'training_view_sha256':sha(args.train_view),'manifest_sha256':sha(args.manifest),'eval_accessed':False,'optimizer_created_or_stepped':False,'results':results}
 atomic_json(args.output,report);print(json.dumps(report,ensure_ascii=False))


def main():
 p=argparse.ArgumentParser();p.add_argument('--train-view',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--tokenizer-helper',type=Path,default=Path('/content/mathvisionkid_full_text_training/code/exhaustive_colab_loader.py'));p.add_argument('--output',type=Path,required=True);p.add_argument('--max-seq-len',type=int,default=2048);p.add_argument('--wait-until',type=float,default=None);a=p.parse_args()
 deadline=a.wait_until
 while not(a.train_view.exists() and a.manifest.exists()):
  if deadline is not None and time.time()>=deadline:raise TimeoutError('verified view unavailable before wait deadline')
  time.sleep(10)
 run(a)
if __name__=='__main__':main()
