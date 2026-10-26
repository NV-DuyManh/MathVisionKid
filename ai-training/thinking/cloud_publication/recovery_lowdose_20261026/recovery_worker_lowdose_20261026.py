"""Bounded fresh-base T4 recovery, quality pauses, immutable resumable checkpoints.



The earlier worker is a hash-pinned library only. Its old main/budget/resume,

cached-base checks and last-checkpoint selection are never invoked here.

"""

import argparse,json,hashlib,importlib.util,os,pathlib,random,signal,sys,time,traceback,zipfile

from datetime import datetime,timezone

from recovery_policy_20261026 import prepare_plan,screen_fixtures,validate_gate,summarize_decisions,selection_key,canonical,digest



MODEL='Qwen/Qwen3-1.7B';REV='70d244cc86ccca08cf5af4e1e306ecf908b1ad5e'

LIB_SHA='d5f4f0bc2df2b9ff8b2999d607f7ab0b773a76e2ececd4cf48bada99ffcc787c'

STOP=False

def row_mean_assistant_loss(logits,labels):
 """Equal-weight row mean of supervised-token CE; never scores ignored positions."""
 import torch
 shifted_logits=logits[:,:-1,:];shifted_labels=labels[:,1:]
 supervised=shifted_labels!=-100
 row_ids=supervised.nonzero(as_tuple=True)[0]
 if row_ids.numel()==0:raise ValueError('batch has no supervised assistant tokens')
 selected_logits=shifted_logits[supervised].float()
 selected_labels=shifted_labels[supervised]
 token_losses=torch.nn.functional.cross_entropy(selected_logits,selected_labels,reduction='none')
 row_sums=torch.zeros(shifted_labels.shape[0],device=token_losses.device,dtype=token_losses.dtype).index_add(0,row_ids,token_losses)
 token_counts=torch.bincount(row_ids,minlength=shifted_labels.shape[0])
 if bool((token_counts==0).any()):raise ValueError('row has no supervised assistant tokens')
 return (row_sums/token_counts).mean()

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

  'scheduler':{'type':'linear_warmup_constant','successful_updates':state['step'],'warmup_updates':10,'peak_lr':5e-6},

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



def load_scope(root):
 base=json.loads((root/'owner_run_scope.json').read_bytes())
 binding=json.loads((root/'owner_scope_binding_v2.json').read_bytes())
 if set(binding)!={'original_scope_sha256','dev_sha256','locked_test_sha256','repair_reason'}:raise ValueError('Binding may not change owner budget or authority')
 if sha(root/'owner_run_scope.json')!=binding['original_scope_sha256']:raise ValueError('Original scope hash differs')
 for key in ['dev_sha256','locked_test_sha256']:
  if len(binding[key])!=64 or any(x not in '0123456789abcdef' for x in binding[key]):raise ValueError('Invalid frozen fixture hash')
  base[key]=binding[key]
 return base

def verify_baseline_cache(cache,fixtures,contract,csha,dev_sha,plan_sha,model_proof,source_view_sha,inference_sha,renderer_sha):
 """Verify and accept only a complete hash-bound current-dev base cache."""
 cache=pathlib.Path(cache)
 binding_path=cache/'baseline_cache_binding.json'
 binding=json.loads(binding_path.read_bytes())
 required={'schema','source_run_id','model','revision','model_artifact_proof','model_artifact_proof_sha256',
  'source_view_sha256','source_plan_sha256','dev_sha256','contract_sha256','inference_contract_sha256','renderer_sha256','fixture_ids','prompt_token_sha256',
  'seed_by_fixture','base_output_sha256','base_output_bytes','base_provenance_sha256','frozen_review_files'}
 if set(binding)!=required or binding['schema']!='MathVisionKid.immutable_dev_base_cache.v1' or not isinstance(binding.get('source_run_id'),str) or not binding['source_run_id']:raise ValueError('Baseline cache binding schema/fields differ')
 if contract.get('fixture_sha256')!=dev_sha:raise ValueError('Current development contract does not bind the configured dev SHA')
 proof_sha=digest(canonical(model_proof).encode())
 fixture_ids=[f['id'] for f in fixtures]
 seeds={f['id']:(20261024+int(digest(f['id'].encode())[:8],16))%(2**31) for f in fixtures}
 expected={'model':MODEL,'revision':REV,'model_artifact_proof':model_proof,'model_artifact_proof_sha256':proof_sha,
  'source_view_sha256':source_view_sha,'source_plan_sha256':plan_sha,'dev_sha256':dev_sha,'contract_sha256':csha,
  'inference_contract_sha256':inference_sha,'renderer_sha256':renderer_sha,
  'fixture_ids':fixture_ids,'prompt_token_sha256':contract['prompt_token_sha256'],'seed_by_fixture':seeds}
 for key,value in expected.items():
  if binding.get(key)!=value:raise ValueError('Baseline cache identity mismatch: '+key)
 output=cache/'base_generations.jsonl';provenance=cache/'base_generation_provenance.json'
 if not output.is_file() or not provenance.is_file():raise ValueError('Baseline cache output/provenance is missing')
 if sha(output)!=binding['base_output_sha256'] or output.stat().st_size!=binding['base_output_bytes']:
  raise ValueError('Baseline cache output SHA/size mismatch')
 if sha(provenance)!=binding['base_provenance_sha256']:
  raise ValueError('Baseline cache provenance SHA mismatch')
 proof=json.loads(provenance.read_bytes())
 if proof.get('model')!=MODEL or proof.get('revision')!=REV or proof.get('contract_sha256')!=csha or proof.get('fixture_sha256')!=contract['fixture_sha256'] or proof.get('stage')!='base_before_training' or proof.get('outputs_sha256')!=binding['base_output_sha256']:
  raise ValueError('Baseline cache generation provenance differs')
 rows=[json.loads(line) for line in output.read_text(encoding='utf-8').splitlines() if line.strip()]
 if len(rows)!=len(fixtures):raise ValueError('Baseline cache does not contain the complete development set')
 for row,fixture in zip(rows,fixtures):
  if row.get('fixture_id')!=fixture['id'] or row.get('grade')!=fixture['grade'] or row.get('mode')!=fixture['mode'] or row.get('stage')!='base_before_training' or row.get('contract_sha256')!=csha or row.get('prompt_token_sha256')!=contract['prompt_token_sha256'][fixture['id']] or row.get('seed')!=seeds[fixture['id']] or row.get('max_new_tokens')!=contract['decoding']['max_new_tokens'] or row.get('timed_out') is not False or row.get('possibly_truncated') is not False or row.get('ended_eos') is not True:
   raise ValueError('Baseline cache row identity/completion mismatch: '+fixture['id'])
 reviews=binding.get('frozen_review_files')
 if not isinstance(reviews,dict) or not reviews:raise ValueError('Baseline cache requires frozen review hashes')
 for name,expected_sha in reviews.items():
  if not isinstance(name,str) or pathlib.PurePosixPath(name).name!=name or not isinstance(expected_sha,str):raise ValueError('Unsafe frozen review binding')
  review=cache/'frozen_reviews'/name
  if not review.is_file() or sha(review)!=expected_sha:raise ValueError('Frozen review artifact hash mismatch: '+name)
 return {'schema':'MathVisionKid.immutable_dev_base_cache_validation.v1','source_run_id':binding['source_run_id'],
  'cache_binding_sha256':sha(binding_path),'base_output_sha256':binding['base_output_sha256'],
  'base_provenance_sha256':binding['base_provenance_sha256'],'frozen_review_files':reviews,
  'model_artifact_proof_sha256':proof_sha,'source_plan_sha256':plan_sha,'dev_sha256':dev_sha,'contract_sha256':csha,
  'inference_contract_sha256':inference_sha,'renderer_sha256':renderer_sha,
  'fixture_ids':fixture_ids,'prompt_token_sha256':contract['prompt_token_sha256'],'seed_by_fixture':seeds,
  'complete_base_rows':len(rows),'outputs_reused_without_rewriting':True}

def main():

 a=argparse.ArgumentParser();a.add_argument('--root',type=pathlib.Path,required=True);a.add_argument('--resume-generation',type=pathlib.Path);a.add_argument('--baseline-cache',type=pathlib.Path);args=a.parse_args()
 if args.resume_generation is not None:raise ValueError('low-dose trial requires a fresh base; inherited checkpoints are never accepted')

 root=args.root;out=root/'training';out.mkdir(exist_ok=True);scope=load_scope(root)

 deadline=float(scope['hard_deadline_unix']);reserve_seconds=scope.get('reserve_seconds')
 if type(reserve_seconds) is not int or reserve_seconds<=0:raise ValueError('scope must provide positive owner-authorized reserve_seconds')
 cutoff=deadline-reserve_seconds

 if time.time()>=cutoff:raise TimeoutError('No remaining authorized train window')

 if (out/'run_config.json').exists() and args.resume_generation is None:raise FileExistsError('Do not duplicate initialized run')

 if sha(root/'frozen_training_primitives.py')!=LIB_SHA:raise ValueError('primitive code pin mismatch')

 H=load(root/'frozen_training_primitives.py','qrec_frozen_primitives')
 import conditional_behavior_renderer as V
 import inference_contract as I
 if sha(root/'conditional_behavior_renderer.py')!='78b4a5c9cfff2e33fc7610461ecab6f57447c079205b62668631f2ca4b665982':raise ValueError('behavior renderer changed')
 if sha(root/'inference_contract.py')!='a8398e1c6a414aa0c9d343ebaa737f7e744f6892b8298497c317ea83927a0642':raise ValueError('inference contract changed')
 def verbal_fixture_messages(fixture):
  value={'grade':fixture['grade'],'problem':fixture['userproblem'],'mode':H.MODE_MAP[fixture['mode']]}
  return [{'role':'system','content':H.SYSTEM},{'role':'user','content':V.prompt(value)}]
 H.fixture_messages=verbal_fixture_messages
 H.generate_fixtures=I.generate_fixtures

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

 cfg={'backend':'native Transformers/PEFT/bitsandbytes; no Unsloth', 'schema':'MathVisionKid.conditional_native_recovery_run.v1','model':MODEL,'revision':REV,'source_view_sha256':H.VIEW_SHA256,

  'source_manifest_sha256':H.MANIFEST_SHA256,'source_plan_sha256':sha(plan_path),'source_cases':4000,'source_rows':16000,

  'derived_view_rows':len(plan['schedule']),'dev_sha256':dev_sha,'hard_deadline_unix':deadline,'reserve_seconds':reserve_seconds,'train_cutoff_unix':cutoff,

  'learning_rate':5e-6,'warmup_updates':10,'lora_r':16,'lora_alpha':16,'target_modules':['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj'],'microbatch':2,'effective_batch':16,

  'gradient_checkpointing':True,'max_sequence':2048,'silent_truncation':False,'assistant_only_loss':True,

  'enable_thinking':False,'loss_reduction':'equal-weight mean of per-row assistant-token mean cross-entropies across each effective batch of up to 16 rows; prompt/padding tokens ignored; denominator is supervised tokens within each row; implemented explicitly from unreduced shifted CE',

  'worker_sha256':sha(pathlib.Path(__file__)),'policy_sha256':sha(pathlib.Path(__file__).with_name('recovery_policy_20261026.py')),

  'packing':False,'padding_free':False,'precision':'FP16','quantization':'NF4 doublequant',

  'gate_steps':[100],'max_successful_updates':100,'max_derived_view_epochs':1,'best_checkpoint_includes_untrained_base':True,

  'validation_scope':'Reused preexisting 30-item development set, already seen in prior development. A fresh pinned base is loaded; its complete base outputs may be reused only through the explicit immutable cache proof. Not an unseen or independent benchmark; sealed/final fixtures are excluded.',

  'human_review_or_credentials_added':False,'previous_adapters_loaded':False,'whole_corpus_training_claimed':False,
  'branch':'recovery_lowdose_20261026','parent_run':'recovery_20261026','fresh_base_required':True,'checkpoint_resume_supported':False,'baseline_cache_requested':args.baseline_cache is not None,'minimum_prelaunch_budget_seconds':3600 if args.baseline_cache is not None else 4800,'max_dev_generation_seconds':1200,'quality_gate_finalization_buffer_seconds':120}

 from native_backend_20261026 import NativeBackend as FastLanguageModel

 import torch,bitsandbytes as bnb

 from transformers import BitsAndBytesConfig

 if not torch.cuda.is_available() or 't4' not in torch.cuda.get_device_name(0).lower():raise RuntimeError('Expected free T4')
 if cutoff-time.time()<cfg['minimum_prelaunch_budget_seconds']:raise TimeoutError('Insufficient owner-authorized time remains for the bounded low-dose trial')

 random.seed(20261024);torch.manual_seed(20261024);torch.cuda.manual_seed_all(20261024)

 model,tok=FastLanguageModel.from_pretrained(model_name=MODEL,revision=REV,use_exact_model_name=True,max_seq_length=2048,dtype=torch.float16,

  load_in_4bit=True,quantization_config=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_compute_dtype=torch.float16,bnb_4bit_use_double_quant=True),attn_implementation='sdpa')

 atomic(out/'model_artifact_binding.json',model._mathvisionkid_artifact_proof)
 if cutoff-time.time()<cfg['minimum_prelaunch_budget_seconds']:raise TimeoutError('Pinned-base download/load left insufficient budget; no optimizer was initialized')
 if getattr(model,'_mathvisionkid_artifact_revision',None)!=REV or tok.eos_token_id!=151645:raise ValueError('verified snapshot/tokenizer revision mismatch')

 helper=H.load_helper(root/'exhaustive_colab_loader.py');rows,audit=H.load_view(root/'training_view.jsonl',root/'sampling_manifest.json',helper,tok)

 by_id={x['sample_id']:x for x in rows};selected=[by_id[x] for x in plan['schedule']]
 original={json.loads(b)['sample_id']:(json.loads(b),digest(b)) for b in (root/'training_view.jsonl').read_bytes().splitlines()}
 projected=[]
 for row in selected:
  source_row,source_raw_hash=original[row['sample_id']];rendered,proof=V.render(source_row)
  # The training-only object carries minimal required fields, not an inherited human attestation on changed bytes.
  neutral={k:source_row[k] for k in ('sample_id','case_group_id','mode','split')}
  neutral['messages']=rendered['messages']
  encoded=helper.tokenize_assistant_only(neutral,tok,max_sequence_tokens=2048);H.validate_encoded(encoded)
  row['encoded']=encoded
  projected.append({'sample_id':row['sample_id'],'source_original_raw_row_sha256':source_raw_hash,'prompt_sha256':digest(rendered['messages'][1]['content'].encode()),'target_sha256':digest(rendered['messages'][2]['content'].encode()),'semantic_field_count':len(proof['fields']),'completion_tokens':encoded['completion_tokens']})
 projection={'schema':'MathVisionKid.verbal_training_projection.v1','source_view_sha256':H.VIEW_SHA256,'source_plan_sha256':cfg['source_plan_sha256'],'renderer_sha256':sha(root/'conditional_behavior_renderer.py'),'rows':projected,'source_rows_modified':False,'source_acceptance_labels_changed':False,'new_human_attestation':False,'source_case_count_added':0,'max_sequence_tokens':max(len(x['encoded']['input_ids']) for x in selected)}
 atomic(root/'verbal_projection_manifest.json',projection);cfg['verbal_projection_manifest_sha256']=sha(root/'verbal_projection_manifest.json');cfg['rendering']=V.VERSION;cfg['renderer_sha256']=sha(root/'conditional_behavior_renderer.py')

 atomic(out/'input_audit.json',{**audit,'selected_rows':len(selected),'all_original_rows_retained_in_source':True})

 H.FIXTURES_SHA256=dev_sha;H.MAX_NEW_TOKENS=1024

 contract,csha=I.eval_contract(fixtures,tok,dev_sha);cfg['contract_sha256']=csha;atomic(out/'evaluation_contract.json',contract)

 atomic(out/'run_config.json',cfg)

 base_dir=out/'eval_step_000000';base_dir.mkdir(exist_ok=False)
 if cutoff-time.time()<cfg['minimum_prelaunch_budget_seconds']:raise TimeoutError('Insufficient time remains before baseline initialization')
 cache_validation=None
 if args.baseline_cache is None:
  cfg['baseline_cache_binding_sha256']=None;cfg['baseline_cache_source_run_id']=None
  atomic(out/'progress.json',{'state':'BASE_DEV_EVALUATION','step':0,'training_started':False})
  base_timeout=min(cfg['max_dev_generation_seconds'],cutoff-time.time()-cfg['quality_gate_finalization_buffer_seconds'])
  if base_timeout<=0:raise TimeoutError('No bounded development-base inference window remains')
  H.generate_fixtures(model,tok,fixtures,base_dir,'base_before_training',contract,csha,base_timeout,FastLanguageModel)
 else:
  atomic(out/'progress.json',{'state':'VALIDATING_IMMUTABLE_BASELINE_CACHE','step':0,'training_started':False})
  if time.time()>=cutoff:raise TimeoutError('No training window remains for cache verification')
  cache_validation=verify_baseline_cache(args.baseline_cache,fixtures,contract,csha,dev_sha,cfg['source_plan_sha256'],model._mathvisionkid_artifact_proof,H.VIEW_SHA256,sha(root/'inference_contract.py'),sha(root/'conditional_behavior_renderer.py'))
  cache_root=pathlib.Path(args.baseline_cache)
  for name in ('base_generations.jsonl','base_generation_provenance.json'):
   target=base_dir/name
   if target.exists():raise FileExistsError('Refusing to overwrite a baseline evaluation file')
   atomic_bytes(target,(cache_root/name).read_bytes())
   expected_sha=cache_validation['base_output_sha256'] if name=='base_generations.jsonl' else cache_validation['base_provenance_sha256']
   if sha(target)!=expected_sha:raise ValueError('Copied baseline cache bytes differ from validated proof')
  cfg['baseline_cache_binding_sha256']=cache_validation['cache_binding_sha256'];cfg['baseline_cache_source_run_id']=cache_validation['source_run_id']
  atomic(out/'baseline_cache_validation.json',cache_validation)
  atomic(base_dir/'baseline_cache_binding_receipt.json',{'cache_binding_sha256':cache_validation['cache_binding_sha256'],'base_output_sha256':cache_validation['base_output_sha256'],'base_provenance_sha256':cache_validation['base_provenance_sha256'],'model_artifact_proof_sha256':cache_validation['model_artifact_proof_sha256'],'source_plan_sha256':cfg['source_plan_sha256'],'dev_sha256':dev_sha,'contract_sha256':csha,'fixture_ids':[f['id'] for f in fixtures],'outputs_reused_without_rewriting':True})
 base_binding={'dev_sha256':dev_sha,'contract_sha256':csha,'source_plan_sha256':cfg['source_plan_sha256'],'base_output_sha256':sha(base_dir/'base_generations.jsonl'),'fixture_ids':[f['id'] for f in fixtures],
  'baseline_cache_binding_sha256':None if cache_validation is None else cache_validation['cache_binding_sha256']}
 atomic(base_dir/'eval_bindings.json',base_binding)
 atomic(out/'best.json',{'kind':'untrained_base','model':MODEL,'revision':REV,'validation_output_sha256':base_binding['base_output_sha256'],'semantic_review_pending':True})

 approval_path=out/'pretrain_qa_approved.json'
 atomic(out/'progress.json',{'state':'WAITING_SOURCE_QA_BEFORE_OPTIMIZER','training_started':False,'step':0})
 while not approval_path.exists() and time.time()<cutoff and not STOP:time.sleep(2)
 if not approval_path.exists():raise TimeoutError('Source QA approval not provided before train cutoff')
 approval=json.loads(approval_path.read_bytes())
 if not approval.get('root_actual_source_samples_reviewed') or approval.get('human_review_claimed') is not False or approval['source_plan_sha256']!=cfg['source_plan_sha256'] or approval['renderer_sha256']!=cfg['renderer_sha256']:raise ValueError('Source QA must bind actual plan and projected renderer')

 model=FastLanguageModel.get_peft_model(model,r=16,lora_alpha=16,lora_dropout=0,bias='none',target_modules=['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj'],use_gradient_checkpointing=True,random_state=20261024,use_rslora=False,loftq_config=None)

 def training_mode():

  FastLanguageModel.for_training(model);model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False});model.config.use_cache=False;model.train()

 training_mode()

 named=[(n,p) for n,p in model.named_parameters() if p.requires_grad];params=[p for _,p in named];cfg['optimizer_parameter_names']=[n for n,_ in named]

 opt=bnb.optim.AdamW8bit(params,lr=5e-6,betas=(.9,.999),weight_decay=.01);scaler=torch.amp.GradScaler('cuda',enabled=True,init_scale=1024.)

 state={'step':0,'rows_done':0,'supervised_tokens':0,'loss_sum':0.,'last_loss':None,'last_gradient_norm':None};cursor=0;training_seconds=0.

 log=out/'successful_ids.jsonl'

 if args.resume_generation:

  from peft import set_peft_model_state_dict,get_peft_model_state_dict

  from peft.utils.save_and_load import load_peft_weights

  g=args.resume_generation;manifest=verify_generation(g);saved_cfg=json.loads((g/'run_config.json').read_bytes())

  for k in ['source_plan_sha256','dev_sha256','contract_sha256','hard_deadline_unix','source_view_sha256','source_manifest_sha256','policy_sha256','worker_sha256','optimizer_parameter_names']:

   if saved_cfg[k]!=cfg[k]:
    if k!='worker_sha256':raise ValueError('resume config mismatch '+k)
    migration=json.loads((root/'memory_resume_migration.json').read_bytes())
    if saved_cfg[k]!=migration['parent_worker_sha256'] or cfg[k]!=migration['resumed_worker_sha256']:
     raise ValueError('Unapproved resume worker migration')
    if migration['changed_training_semantics'] is not False or migration['only_memory_change']!='nonreentrant_gradient_checkpointing':
     raise ValueError('Resume migration may only change recomputation memory strategy')
    permitted={'worker_sha256','gradient_checkpointing','loss_reduction'}
    differences={key for key in set(saved_cfg)|set(cfg) if saved_cfg.get(key)!=cfg.get(key)}
    if differences-permitted or saved_cfg['gradient_checkpointing'] is not False or cfg['gradient_checkpointing'] is not True:
     raise ValueError('Additional checkpoint config drift during memory migration')
    cfg['explicit_memory_resume_migration_sha256']=sha(root/'memory_resume_migration.json')

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

   available=min(cfg['max_dev_generation_seconds'],cutoff-time.time()-cfg['quality_gate_finalization_buffer_seconds'])

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

  review_cutoff=cutoff

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

  lr=5e-6*min(1.,(state['step']+1)/10)

  for pg in opt.param_groups:pg['lr']=lr

  opt.zero_grad(set_to_none=True);t=time.monotonic();loss_value=0.

  for j in range(0,n,2):

   items=group[j:j+2];batch=H.collate(items,tok,'cuda')

   with torch.autocast('cuda',dtype=torch.float16):
    model_inputs={k:v for k,v in batch.items() if k!='labels'}
    forward=model(**model_inputs,use_cache=False)
   loss=row_mean_assistant_loss(forward.logits,batch['labels'])*(len(items)/n)
   if state['step']==0 and j==0:
    with torch.no_grad():
     labels=batch['labels'][:,1:];logits=forward.logits[:,:-1,:];ref_rows=[]
     for row_index in range(labels.shape[0]):
      mask=labels[row_index]!=-100
      ref_rows.append(torch.nn.functional.cross_entropy(logits[row_index][mask].float(),labels[row_index][mask]))
     reference=torch.stack(ref_rows).mean();difference=abs(float(loss.detach())*n/len(items)-float(reference))
     if difference>1e-6:raise ValueError('Vectorized selected-token row CE differs from per-row CE reference')
     atomic(out/'native_first_microbatch_audit.json',{'selected_token_row_CE_matches_per_row_reference':True,'absolute_difference':difference,'supervised_tokens':int((labels!=-100).sum()),'ignored_prompt_padding_positions_scored':False,'forward_called_without_labels':True,'model_backend':'native Transformers/PEFT'})
    del labels,logits,ref_rows,reference,mask,row_index
   del forward

   if not bool(torch.isfinite(loss).item()):raise FloatingPointError('nonfinite loss; no silent row skip')

   scaler.scale(loss).backward();loss_value+=float(loss.detach())

  scaler.unscale_(opt);norm=torch.nn.utils.clip_grad_norm_(params,1.,error_if_nonfinite=True,foreach=True)

  if float(norm)<=0:raise FloatingPointError('No nonzero trainable LoRA gradient; do not apply optimizer step')

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

  if state['step']==1 or state['step']%100==0 or final:

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



