"""Bounded fresh-base T4 recovery, quality pauses, immutable resumable checkpoints.

The earlier worker is a hash-pinned library only. Its old main/budget/resume,
cached-base checks and last-checkpoint selection are never invoked here.
"""
import argparse,json,hashlib,importlib.util,os,pathlib,random,signal,sys,time,traceback,zipfile
from datetime import datetime,timezone
from recovery_policy import prepare_plan,screen_fixtures,validate_gate,summarize_decisions,selection_key,canonical,digest

MODEL='Qwen/Qwen3-1.7B';REV='70d244cc86ccca08cf5af4e1e306ecf908b1ad5e'
LIB_SHA='d5f4f0bc2df2b9ff8b2999d607f7ab0b773a76e2ececd4cf48bada99ffcc787c'
STOP=False
def sha(p):return digest(pathlib.Path(p).read_bytes())
def atomic(p,x):
 p=pathlib.Path(p);p.parent.mkdir(exist_ok=True,parents=True);t=p.with_name(p.name+'.pending')
 with t.open('w',encoding='utf-8') as f:
  f.write(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n');f.flush();os.fsync(f.fileno())
 os.replace(t,p)
def atomic_bytes(p,data):
 p=pathlib.Path(p);t=p.with_name(p.name+'.pending')
 with t.open('wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 os.replace(t,p)
def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def stop_requested(*_):
 global STOP;STOP=True
def verify_generation(g):
 m=json.loads((g/'generation_manifest.json').read_bytes())
 if not m.get('complete'):raise ValueError('incomplete generation')
 for n,h in m['files'].items():
  if pathlib.PurePosixPath(n).name!=n or sha(g/n)!=h:raise ValueError('checkpoint member mismatch')
  if (g/n).stat().st_size!=m['file_bytes'][n]:raise ValueError('checkpoint member size mismatch')
 return m
def restore_log_prefix(log,resume,metrics,manifest,plan,selected):
 """Reconcile only acknowledged checkpoint bytes; preserve later bytes verbatim."""
 raw=log.read_bytes();size=resume['successful_log_bytes'];prefix=raw[:size];tail=raw[size:]
 if size<0 or len(prefix)!=size or digest(prefix)!=resume['successful_log_sha256'] or (prefix and not prefix.endswith(b'\n')):raise ValueError('checkpoint log prefix mismatch')
 cursor=resume['cursor'];entries=[json.loads(s) for s in prefix.decode('utf-8').splitlines()]
 if not isinstance(cursor,int) or isinstance(cursor,bool) or not 0<=cursor<=len(selected):raise ValueError('invalid resume cursor')
 if [e['sample_id'] for e in entries]!=plan['schedule'][:cursor]:raise ValueError('acknowledged IDs/cursor differ')
 if any(e['step']!=i//16+1 for i,e in enumerate(entries)):raise ValueError('acknowledged log step differs')
 expected_step=(cursor+15)//16
 if any(s['step']!=expected_step or s['rows_done']!=cursor for s in (resume,metrics,manifest)):raise ValueError('resume/metrics/manifest exposure or update disagreement')
 if metrics.get('unique_examples')!=cursor:raise ValueError('unique exposure count differs')
 tokens=sum(sum(t!=-100 for t in x['encoded']['labels']) for x in selected[:cursor])
 if metrics['supervised_tokens']!=tokens:raise ValueError('acknowledged supervised token count differs')
 if resume['source_plan_sha256']!=digest(pathlib.Path(plan['_path']).read_bytes()):raise ValueError('resume sampling-plan hash differs')
 if tail:
  preserved=log.with_name('preserved_unapplied_log_tail_'+digest(tail)+'.jsonl')
  if preserved.exists():
   if preserved.read_bytes()!=tail:raise ValueError('immutable log tail conflicts')
  else:
   with preserved.open('xb') as f:f.write(tail);f.flush();os.fsync(f.fileno())
  atomic_bytes(log,prefix)
 return {'cursor':cursor,'supervised_tokens':tokens,'preserved_tail_bytes':len(tail),'prefix_sha256':digest(prefix)}
def verify_eval_evidence(evaldir,bindings,fixtures,contract):
 output=evaldir/'adapter_generations.jsonl';receipt=evaldir/'eval_bindings.json'
 partial=evaldir/'adapter_generations.partial.jsonl'
 if not output.exists() and not receipt.exists():
  if partial.exists():raise ValueError('partial evaluation has no complete hash-bound evidence')
  return None
 if not output.exists() or not receipt.exists():raise ValueError('evaluation output/bindings incomplete; refuse silent regeneration')
 proof=json.loads(receipt.read_bytes())
 if proof!={**bindings,'adapter_output_sha256':sha(output)}:raise ValueError('evaluation binding/hash mismatch')
 records=[json.loads(s) for s in output.read_text(encoding='utf-8').splitlines()]
 if [r['fixture_id'] for r in records]!=[f['id'] for f in fixtures]:raise ValueError('evaluation fixture IDs/order differ')
 for row,f in zip(records,fixtures):
  if row['grade']!=f['grade'] or row['mode']!=f['mode'] or row['stage']!='adapter_after_training' or row['contract_sha256']!=bindings['contract_sha256'] or row['prompt_token_sha256']!=contract['prompt_token_sha256'][f['id']] or row['max_new_tokens']!=contract['decoding']['max_new_tokens']:raise ValueError('evaluation actual contract differs')
 return proof
def choose_best(previous,summary,candidate,baseline):
 """Eligible improvement only; equal keys retain the earlier/base winner."""
 previous=dict(previous)
 if 'selection_key' not in previous:
  if previous.get('kind')!='untrained_base':raise ValueError('trained best pointer lacks score evidence')
  previous={**baseline,'selection_key':list(selection_key(summary,'base')),'semantic_review_pending':False}
 if summary['candidate_eligible'] and selection_key(summary,'candidate')>tuple(previous['selection_key']):
  return {**candidate,'selection_key':list(selection_key(summary,'candidate')),'semantic_review_pending':False}
 return previous
def validate_review_metadata(records,fixtures):
 expected={f['id']:(f['grade'],f['mode']) for f in fixtures}
 if len(records)!=len(expected) or len({r['fixture_id'] for r in records})!=len(expected):raise ValueError('review fixture count/IDs differ')
 for row in records:
  if expected.get(row['fixture_id'])!=(row['grade'],row['mode']):raise ValueError('review grade/mode differs from frozen fixture '+row['fixture_id'])
def baseline_profile(records):
 return sorted([{k:r[k] for k in ('fixture_id','grade','mode','base_pass','base_hint_leak')} for r in records],key=lambda r:r['fixture_id'])
def validate_review_completion(records,base_rows,adapter_rows):
 for side,rows in (('base',base_rows),('adapter',adapter_rows)):
  actual={r['fixture_id']:r for r in rows}
  if len(actual)!=len(records):raise ValueError('review/output fixture count differs')
  for record in records:
   row=actual[record['fixture_id']]
   if record[side+'_pass'] and (row.get('ended_eos') is not True or row.get('possibly_truncated') is not False or row.get('timed_out') is not False):raise ValueError('truncated/timed-out output cannot pass strict semantic task')
def resume_gate_required(step,cursor,total,gate_steps=(50,100,200,300),cap=300,proof_exists=False):
 return step in gate_steps or cursor==total or step>=cap or proof_exists
def save_generation(model,tok,opt,scaler,out,cfg,state,cursor,training_seconds):
 import torch
 g=out/f"generation_step_{state['step']:06d}_rows_{state['rows_done']:08d}"
 if g.exists():raise FileExistsError('immutable generation already exists; fork a new run before replaying an older checkpoint')
 p=g.with_name(g.name+'.pending');p.mkdir(exist_ok=False)
 model.save_pretrained(p,safe_serialization=True);tok.save_pretrained(p)
 metrics={**state,'unique_examples':cursor,'derived_view_fraction':cursor/cfg['derived_view_rows'],'training_seconds':training_seconds}
 atomic(p/'metrics.json',metrics);atomic(p/'run_config.json',cfg)
 log=out/'successful_ids.jsonl';log_bytes=log.read_bytes() if log.exists() else b''
 torch.save({'step':state['step'],'rows_done':state['rows_done'],'cursor':cursor,'training_seconds':training_seconds,
  'optimizer':opt.state_dict(),'optimizer_parameter_names':cfg['optimizer_parameter_names'],'scaler':scaler.state_dict(),
  'torch_cpu_rng':torch.get_rng_state(),'torch_cuda_rng':torch.cuda.get_rng_state_all(),'python_rng':random.getstate(),
  'successful_log_sha256':digest(log_bytes),'successful_log_bytes':len(log_bytes),'source_plan_sha256':cfg['source_plan_sha256'],
  'scheduler':{'type':'step_warmup_constant','successful_updates':state['step'],'warmup_updates':10,'peak_lr':1e-5},
  'hard_deadline_unix':cfg['hard_deadline_unix']},p/'resume_state.pt')
 files={x.name:sha(x) for x in p.iterdir() if x.is_file()}
 atomic(p/'generation_manifest.json',{'schema':'MathVisionKid.quality_recovery_generation.v1','complete':True,'step':state['step'],'rows_done':state['rows_done'],'files':files,'file_bytes':{x.name:x.stat().st_size for x in p.iterdir() if x.is_file()}})
 os.replace(p,g)
 atomic(out/'latest.json',{'generation':g.name,'step':state['step'],'rows_done':state['rows_done'],'manifest_sha256':sha(g/'generation_manifest.json')})
 return g
def export_adapter(g,out,filename='adapter_export.zip'):
 verify_generation(g);dest=out/filename;tmp=dest.with_suffix('.pending')
 with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(g.iterdir()):
   if p.is_file() and p.name!='resume_state.pt':z.write(p,p.name)
 os.replace(tmp,dest);return dest

def main():
 a=argparse.ArgumentParser();a.add_argument('--root',type=pathlib.Path,required=True);a.add_argument('--resume-generation',type=pathlib.Path);args=a.parse_args()
 root=args.root;out=root/'training';out.mkdir(exist_ok=True);scope=json.loads((root/'owner_run_scope.json').read_bytes())
 deadline=float(scope['hard_deadline_unix']);cutoff=deadline-1800
 if time.time()>=cutoff:raise TimeoutError('No remaining authorized train window')
 if (out/'run_config.json').exists() and args.resume_generation is None:raise FileExistsError('Do not duplicate initialized run')
 if sha(root/'frozen_training_primitives.py')!=LIB_SHA:raise ValueError('primitive code pin mismatch')
 H=load(root/'frozen_training_primitives.py','qrec_frozen_primitives')
 fixtures=[json.loads(s) for s in (root/'new_validation_candidates.jsonl').read_text().splitlines()]
 dev_sha=sha(root/'new_validation_candidates.jsonl')
 if dev_sha!=scope['dev_sha256'] or len(fixtures)!=30:raise ValueError('frozen dev mismatch')
 raw_rows=[json.loads(s) for s in (root/'training_view.jsonl').read_text().splitlines()]
 screening=screen_fixtures(fixtures,raw_rows);atomic(root/'dev_train_screening.json',screening)
 if screening['collisions']:raise ValueError('fresh dev overlaps train text; no data edits to force pass')
 plan=prepare_plan(raw_rows,H.VIEW_SHA256);plan_path=root/'derived_sampling_plan.json'
 if plan_path.exists():
  if json.loads(plan_path.read_bytes())!=plan:raise ValueError('different sampling plan already exists')
 else:atomic(plan_path,plan)
 atomic(out/'progress.json',{'state':'LOADING_FRESH_BASE','training_started':False,'step':0})
 cfg={'schema':'MathVisionKid.quality_recovery_run.v1','model':MODEL,'revision':REV,'source_view_sha256':H.VIEW_SHA256,
  'source_manifest_sha256':H.MANIFEST_SHA256,'source_plan_sha256':sha(plan_path),'source_cases':4000,'source_rows':16000,
  'derived_view_rows':len(plan['schedule']),'dev_sha256':dev_sha,'hard_deadline_unix':deadline,'train_cutoff_unix':cutoff,
  'learning_rate':1e-5,'warmup_updates':10,'lora_r':16,'lora_alpha':16,'microbatch':2,'effective_batch':16,
  'gradient_checkpointing':False,'max_sequence':2048,'silent_truncation':False,'assistant_only_loss':True,
  'enable_thinking':False,'loss_reduction':'unchanged originalmicro2 supervised-token mean weighted pair_rows/group_rows',
  'worker_sha256':sha(pathlib.Path(__file__)),'policy_sha256':sha(pathlib.Path(__file__).with_name('recovery_policy.py')),
  'packing':False,'padding_free':False,'precision':'FP16','quantization':'NF4 doublequant',
  'gate_steps':[50,100,200,300],'max_successful_updates':300,'max_derived_view_epochs':1,'best_checkpoint_includes_untrained_base':True,
  'validation_scope':'fresh30 dev screened against actual16k; not full6.5M independent estimate',
  'human_review_or_credentials_added':False,'previous_adapters_loaded':False,'whole_corpus_training_claimed':False}
 from unsloth import FastLanguageModel
 import torch,bitsandbytes as bnb
 from transformers import BitsAndBytesConfig
 if not torch.cuda.is_available() or 't4' not in torch.cuda.get_device_name(0).lower():raise RuntimeError('Expected free T4')
 random.seed(20261024);torch.manual_seed(20261024);torch.cuda.manual_seed_all(20261024)
 model,tok=FastLanguageModel.from_pretrained(model_name=MODEL,revision=REV,use_exact_model_name=True,max_seq_length=2048,dtype=torch.float16,
  load_in_4bit=True,quantization_config=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_compute_dtype=torch.float16,bnb_4bit_use_double_quant=True),attn_implementation='sdpa')
 if getattr(model.config,'_commit_hash',None)!=REV or tok.eos_token_id!=151645:raise ValueError('model/tokenizer revision mismatch')
 helper=H.load_helper(root/'exhaustive_colab_loader.py');rows,audit=H.load_view(root/'training_view.jsonl',root/'sampling_manifest.json',helper,tok)
 by_id={x['sample_id']:x for x in rows};selected=[by_id[x] for x in plan['schedule']]
 atomic(out/'input_audit.json',{**audit,'selected_rows':len(selected),'all_original_rows_retained_in_source':True})
 H.FIXTURES_SHA256=dev_sha;H.MAX_NEW_TOKENS=1024
 contract,csha=H.eval_contract(fixtures,tok);cfg['contract_sha256']=csha;atomic(out/'evaluation_contract.json',contract)
 atomic(out/'run_config.json',cfg)
 base_dir=out/'eval_step_000000';base_dir.mkdir(exist_ok=True)
 if args.resume_generation is None:
  atomic(out/'progress.json',{'state':'BASE_DEV_EVALUATION','step':0,'training_started':False})
  H.generate_fixtures(model,tok,fixtures,base_dir,'base_before_training',contract,csha,min(900,max(1,cutoff-time.time())),FastLanguageModel)
  atomic(out/'best.json',{'kind':'untrained_base','model':MODEL,'revision':REV,'validation_output_sha256':sha(base_dir/'base_generations.jsonl'),'semantic_review_pending':True})
  atomic(base_dir/'eval_bindings.json',{'dev_sha256':dev_sha,'contract_sha256':csha,'source_plan_sha256':cfg['source_plan_sha256'],'base_output_sha256':sha(base_dir/'base_generations.jsonl'),'fixture_ids':[f['id'] for f in fixtures]})
 base_binding={'dev_sha256':dev_sha,'contract_sha256':csha,'source_plan_sha256':cfg['source_plan_sha256'],'base_output_sha256':sha(base_dir/'base_generations.jsonl'),'fixture_ids':[f['id'] for f in fixtures]}
 if not (base_dir/'eval_bindings.json').exists() or json.loads((base_dir/'eval_bindings.json').read_bytes())!=base_binding:raise ValueError('base evaluation binding is missing or differs')
 model=FastLanguageModel.get_peft_model(model,r=16,lora_alpha=16,lora_dropout=0,bias='none',target_modules=H.TARGET_MODULES,use_gradient_checkpointing=False,random_state=20261024,use_rslora=False,loftq_config=None)
 def training_mode():
  FastLanguageModel.for_training(model);model.gradient_checkpointing_disable();model.config.use_cache=False;model.train()
 training_mode()
 named=[(n,p) for n,p in model.named_parameters() if p.requires_grad];params=[p for _,p in named];cfg['optimizer_parameter_names']=[n for n,_ in named]
 opt=bnb.optim.AdamW8bit(params,lr=1e-6,betas=(.9,.999),weight_decay=.01);scaler=torch.amp.GradScaler('cuda',enabled=True,init_scale=1024.)
 state={'step':0,'rows_done':0,'supervised_tokens':0,'loss_sum':0.,'last_loss':None,'last_gradient_norm':None};cursor=0;training_seconds=0.
 log=out/'successful_ids.jsonl'
 if args.resume_generation:
  from peft import set_peft_model_state_dict,get_peft_model_state_dict
  from peft.utils.save_and_load import load_peft_weights
  g=args.resume_generation;manifest=verify_generation(g);saved_cfg=json.loads((g/'run_config.json').read_bytes())
  for k in ['source_plan_sha256','dev_sha256','contract_sha256','hard_deadline_unix','source_view_sha256','source_manifest_sha256','policy_sha256','worker_sha256','optimizer_parameter_names']:
   if saved_cfg[k]!=cfg[k]:raise ValueError('resume config mismatch '+k)
  weights=load_peft_weights(str(g),device='cpu');set_peft_model_state_dict(model,weights);actual=get_peft_model_state_dict(model)
  if set(weights)!=set(actual) or any(not torch.equal(actual[k].detach().cpu(),weights[k].to(dtype=actual[k].dtype)) for k in actual):raise ValueError('resume adapter differs')
  resume=torch.load(g/'resume_state.pt',map_location='cpu',weights_only=False);metrics=json.loads((g/'metrics.json').read_bytes())
  if resume['optimizer_parameter_names']!=cfg['optimizer_parameter_names']:raise ValueError('optimizer mapping differs')
  H.optimizer_coherence(resume['optimizer'],resume['step'],params,cfg['optimizer_parameter_names'])
  prefix_check=restore_log_prefix(log,resume,metrics,manifest,{**plan,'_path':str(plan_path)},selected)
  atomic(out/'resume_log_validation.json',prefix_check)
  opt.load_state_dict(resume['optimizer']);scaler.load_state_dict(resume['scaler']);torch.set_rng_state(resume['torch_cpu_rng']);torch.cuda.set_rng_state_all(resume['torch_cuda_rng']);random.setstate(resume['python_rng'])
  state={k:metrics[k] for k in state};cursor=resume['cursor'];training_seconds=resume['training_seconds']
 else:log.write_text('')
 atomic(out/'run_config.json',cfg)
 for n in ('SIGINT','SIGTERM','SIGUSR1'):
  if hasattr(signal,n):signal.signal(getattr(signal,n),stop_requested)
 def quality_gate(g,final_stage=False):
  """No optimizer update is permitted until this exact generation is approved."""
  step=state['step'];verify_generation(g)
  fixed={**base_binding,'generation_manifest_sha256':sha(g/'generation_manifest.json'),'final_stage':final_stage}
  evaldir=out/f"eval_step_{step:06d}";evaldir.mkdir(exist_ok=True)
  proof=verify_eval_evidence(evaldir,fixed,fixtures,contract)
  if proof is None:
   available=min(900,deadline-time.time()-600)
   if available<=0:raise TimeoutError('quality evaluation would consume final export reserve')
   rng=(torch.get_rng_state(),torch.cuda.get_rng_state_all(),random.getstate())
   try:H.generate_fixtures(model,tok,fixtures,evaldir,'adapter_after_training',contract,csha,available,FastLanguageModel)
   finally:
    torch.set_rng_state(rng[0]);torch.cuda.set_rng_state_all(rng[1]);random.setstate(rng[2]);training_mode()
   proof={**fixed,'adapter_output_sha256':sha(evaldir/'adapter_generations.jsonl')}
   atomic(evaldir/'eval_bindings.json',proof)
   verify_eval_evidence(evaldir,fixed,fixtures,contract)
  bindings=proof;gatefile=out/f"gate_step_{step:06d}.json"
  atomic(out/'progress.json',{'state':'WAITING_QUALITY_REVIEW','training_started':True,**state,'bindings':bindings,'gate_file':str(gatefile),'hard_deadline_unix':deadline,'final_stage':final_stage})
  review_cutoff=deadline-600 if final_stage else cutoff
  while not gatefile.exists() and time.time()<review_cutoff and not STOP:time.sleep(2)
  if not gatefile.exists():return 'STOP_NO_REVIEW'
  gate=json.loads(gatefile.read_bytes());validate_review_metadata(gate['decisions'],fixtures)
  validate_review_completion(gate['decisions'],[json.loads(s) for s in (base_dir/'base_generations.jsonl').read_text(encoding='utf-8').splitlines()],[json.loads(s) for s in (evaldir/'adapter_generations.jsonl').read_text(encoding='utf-8').splitlines()])
  decision=validate_gate(gate,step,bindings)
  frozen_base={'base_output_sha256':base_binding['base_output_sha256'],'dev_sha256':dev_sha,'profile':baseline_profile(gate['decisions'])}
  baseprofile=out/'base_review_profile.json'
  if baseprofile.exists():
   if json.loads(baseprofile.read_bytes())!=frozen_base:raise ValueError('baseline semantic judgments changed between gates')
  else:atomic(baseprofile,frozen_base)
  if final_stage and decision!='STOP':raise ValueError('final-stage gate must STOP; no extension beyond cap/EOF')
  summary=summarize_decisions(gate['decisions'])
  previous=json.loads((out/'best.json').read_bytes())
  if previous.get('kind')=='trained_adapter':
   oldg=out/previous['generation'];verify_generation(oldg)
   oldgate=out/previous['gate_file']
   if sha(oldg/'generation_manifest.json')!=previous['manifest_sha256'] or sha(oldgate)!=previous['gate_sha256']:raise ValueError('previous best evidence changed')
   oldproof=previous['bindings']
   for key in base_binding:
    if oldproof[key]!=base_binding[key]:raise ValueError('previous best dev/base binding differs')
   verify_eval_evidence(out/f"eval_step_{previous['step']:06d}",{k:v for k,v in oldproof.items() if k!='adapter_output_sha256'},fixtures,contract)
   prior_gate=json.loads(oldgate.read_bytes());validate_review_metadata(prior_gate['decisions'],fixtures);validate_gate(prior_gate,previous['step'],oldproof)
   prior_summary=summarize_decisions(prior_gate['decisions'])
   if not prior_summary['candidate_eligible'] or list(selection_key(prior_summary,'candidate'))!=previous['selection_key']:raise ValueError('previous best score/eligibility invalid')
  elif previous.get('kind')!='untrained_base' or previous.get('model')!=MODEL or previous.get('revision')!=REV or previous.get('validation_output_sha256')!=base_binding['base_output_sha256']:raise ValueError('base best pointer differs')
  baseline={'kind':'untrained_base','model':MODEL,'revision':REV,'validation_output_sha256':base_binding['base_output_sha256'],'production_approval':False}
  candidate={'kind':'trained_adapter','generation':g.name,'manifest_sha256':bindings['generation_manifest_sha256'],'gate_file':gatefile.name,'gate_sha256':sha(gatefile),'step':step,'bindings':bindings,'production_approval':False}
  atomic(out/'best.json',choose_best(previous,summary,candidate,baseline))
  atomic(evaldir/'gate_summary.json',{'summary':summary,'decision':decision,'gate_sha256':sha(gatefile),'bindings':bindings,'selected_best':json.loads((out/'best.json').read_bytes())})
  return decision
 last=args.resume_generation;stop_reason='ONE_DERIVED_PASS_COMPLETE';last_gated_step=None
 # A checkpoint saved at a quality pause cannot bypass that pause on resume.
 resume_eval_proof=out/f"eval_step_{state['step']:06d}"/'eval_bindings.json'
 if args.resume_generation and resume_gate_required(state['step'],cursor,len(selected),cfg['gate_steps'],cfg['max_successful_updates'],resume_eval_proof.exists()):
  final=cursor==len(selected) or state['step']>=cfg['max_successful_updates']
  if resume_eval_proof.exists():final=json.loads(resume_eval_proof.read_bytes()).get('final_stage',final)
  decision=quality_gate(last,final);last_gated_step=state['step']
  if decision in ('STOP','STOP_NO_REVIEW'):stop_reason='QUALITY_GATE_STOP_ON_RESUME'
 while cursor<len(selected) and state['step']<cfg['max_successful_updates'] and stop_reason!='QUALITY_GATE_STOP_ON_RESUME':
  if STOP or time.time()>=cutoff:stop_reason='BOUNDARY_STOP_OR_TRAIN_CUTOFF';break
  group=selected[cursor:cursor+16];group=sorted(group,key=lambda x:len(x['encoded']['input_ids']));n=len(group)
  lr=1e-5*min(1.,(state['step']+1)/10)
  for pg in opt.param_groups:pg['lr']=lr
  opt.zero_grad(set_to_none=True);t=time.monotonic();loss_value=0.
  for j in range(0,n,2):
   items=group[j:j+2];batch=H.collate(items,tok,'cuda')
   with torch.autocast('cuda',dtype=torch.float16):loss=model(**batch,use_cache=False).loss*(len(items)/n)
   if not bool(torch.isfinite(loss).item()):raise FloatingPointError('nonfinite loss; no silent row skip')
   scaler.scale(loss).backward();loss_value+=float(loss.detach())
  scaler.unscale_(opt);norm=torch.nn.utils.clip_grad_norm_(params,1.,error_if_nonfinite=True,foreach=True)
  old_scale=scaler.get_scale();scaler.step(opt);scaler.update();torch.cuda.synchronize()
  if scaler.get_scale()<old_scale:raise FloatingPointError('AMP skipped optimizer update')
  if not bool(torch.isfinite(torch.stack(torch._foreach_norm([p.detach() for p in params]))).all().item()):raise FloatingPointError('nonfinite trained adapter')
  training_seconds+=time.monotonic()-t;state['step']+=1;state['rows_done']+=n;state['last_loss']=loss_value;state['loss_sum']+=loss_value;state['last_gradient_norm']=float(norm);state['last_lr']=lr
  originals=selected[cursor:cursor+n]
  state['supervised_tokens']+=sum(sum(t!=-100 for t in x['encoded']['labels']) for x in originals)
  with log.open('a',encoding='utf-8') as f:
   for x in originals:f.write(canonical({'sample_id':x['sample_id'],'step':state['step']})+'\n')
   f.flush();os.fsync(f.fileno())
  cursor+=n;opt.zero_grad(set_to_none=True)
  atomic(out/'progress.json',{'state':'TRAINING','training_started':True,**state,'unique_examples':cursor,'derived_view_rows':len(selected),'training_seconds':training_seconds,'hard_deadline_unix':deadline})
  final=cursor==len(selected) or state['step']>=cfg['max_successful_updates']
  if state['step']==1 or state['step'] in cfg['gate_steps'] or final:
   last=save_generation(model,tok,opt,scaler,out,cfg,state,cursor,training_seconds)
  if state['step'] in cfg['gate_steps'] or final:
   decision=quality_gate(last,final);last_gated_step=state['step']
   if decision in ('STOP','STOP_NO_REVIEW'):stop_reason='QUALITY_GATE_STOP';break
 if state['step'] and (last is None or json.loads((last/'metrics.json').read_bytes())['step']!=state['step']):last=save_generation(model,tok,opt,scaler,out,cfg,state,cursor,training_seconds)
 if last:
  artifact=export_adapter(last,out,'last_adapter_diagnostic.zip');artifact_info={'path':artifact.name,'bytes':artifact.stat().st_size,'sha256':sha(artifact),'diagnostic_only':True}
 else:artifact_info=None
 # A cutoff between planned gates still needs a final quality decision before selection.
 if state['step'] and last_gated_step!=state['step']:
  quality_gate(last,True);last_gated_step=state['step']
 best=json.loads((out/'best.json').read_bytes())
 if best['kind']=='trained_adapter':
  bestg=out/best['generation'];verify_generation(bestg)
  if sha(bestg/'generation_manifest.json')!=best['manifest_sha256']:raise ValueError('selected best generation changed')
  bestartifact=export_adapter(bestg,out,'selected_adapter_export.zip')
  selected_artifact={'kind':'trained_adapter','generation':bestg.name,'path':str(bestartifact.relative_to(out)),'sha256':sha(bestartifact),'bytes':bestartifact.stat().st_size,'selection_evidence':best}
 else:selected_artifact={'kind':'untrained_base','model':MODEL,'revision':REV,'adapter':None,'selection_evidence':best}
 if time.time()>=deadline:raise TimeoutError('hard owner deadline exceeded during final review/export')
 atomic(out/'run_complete.json',{'complete':True,'stop_reason':stop_reason,'metrics':state,'training_seconds':training_seconds,'unique_examples':cursor,'source_view_rows':16000,'derived_view_rows':len(selected),'derived_view_epochs':cursor/len(selected),'best':best,'selected_artifact':selected_artifact,'last_adapter':artifact_info,'completed_unix':time.time(),'hard_deadline_unix':deadline,'budget_satisfied':time.time()<deadline,'production_approval':False,'whole_corpus_training_claimed':False})
 atomic(out/'progress.json',{'state':'COMPLETE','training_started':bool(state['step']),**state,'stop_reason':stop_reason,'training_seconds':training_seconds})
if __name__=='__main__':
 try:main()
 except BaseException as e:
  args=sys.argv;root=pathlib.Path(args[args.index('--root')+1]) if '--root' in args else pathlib.Path('.')
  atomic(root/'training/error.json',{'error':repr(e),'traceback':traceback.format_exc(),'observed_utc':datetime.now(timezone.utc).isoformat(),'source_or_corpus_modified':False})
  raise
