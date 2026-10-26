"""Bounded forward-only audit; never invokes optimizer or reads held-out test."""
import os
os.environ['UNSLOTH_RETURN_LOGITS']='1'
os.environ['TOKENIZERS_PARALLELISM']='false'
import pathlib,json,hashlib,sys,time,threading,traceback,inspect,collections
R=pathlib.Path('/content/mathvisionkid_quality_recovery_20261024');O=R/'target_alignment_audit'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def atomic(p,x):
 p=pathlib.Path(p);t=p.with_suffix('.pending');t.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');t.replace(p)
def main():
 O.mkdir(exist_ok=False)
 scope=json.loads((R/'owner_run_scope.json').read_bytes());end=min(time.time()+720,scope['hard_deadline_unix']-1200)
 assert time.time()<end
 def expire():atomic(O/'timeout.json',{'error':'Forward-only audit timed out','optimizer_updates':0});os._exit(124)
 timer=threading.Timer(end-time.time(),expire);timer.daemon=True;timer.start()
 try:
  sys.path.insert(0,str(R))
  import recovery_worker as W
  assert sha(R/'recovery_worker.py')=='345ff9d1def663bca704b4ab47ea8828c9793964bf70fb5ed2b784517b494e29'
  assert sha(R/'frozen_training_primitives.py')==W.LIB_SHA
  H=W.load(R/'frozen_training_primitives.py','target_audit_frozen_H')
  assert sha(R/'training_view.jsonl')==H.VIEW_SHA256
  from unsloth import FastLanguageModel
  import torch
  from transformers import BitsAndBytesConfig
  import torch.nn.functional as F
  model,tok=FastLanguageModel.from_pretrained(model_name=W.MODEL,revision=W.REV,use_exact_model_name=True,max_seq_length=2048,dtype=torch.float16,load_in_4bit=True,quantization_config=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_compute_dtype=torch.float16,bnb_4bit_use_double_quant=True),attn_implementation='sdpa')
  assert model.config._commit_hash==W.REV and tok.eos_token_id==151645
  helper=H.load_helper(R/'exhaustive_colab_loader.py')
  raw=[json.loads(x) for x in (R/'training_view.jsonl').read_text().splitlines()]
  byid={x['sample_id']:x for x in raw};plan=json.loads((R/'derived_sampling_plan.json').read_bytes())
  mode_targets=collections.Counter();student=0;guards=0
  for row in raw:
   p=json.loads(row['messages'][1]['content']);t=json.loads(row['messages'][2]['content'])
   mode_targets[(row['mode'],','.join(sorted(t)))]+=1
   student+=bool(p.get('student_work'));guards+=t.get('can_solve') is False
  atomic(O/'dataset_shape.json',{'source_sha256':H.VIEW_SHA256,'rows':len(raw),'target_key_shapes':[{'mode':k[0],'keys':k[1],'rows':v} for k,v in mode_targets.items()],'explicit_student_work_prompt_rows':student,'can_solve_false_rows':guards,'optimizer_updates':0,'source_modified':False})
  # Real train examples only, including the first acknowledged optimizer group.
  first=[byid[x] for x in plan['schedule'][:2]]
  candidates=[r for r in raw if r['mode']=='worked_solution']
  shortest=min(candidates,key=lambda r:len(r['messages'][-1]['content']))
  longest=max(candidates,key=lambda r:len(r['messages'][-1]['content']))
  hints=[r for r in raw if r['mode']=='hint_level_1']
  groups=[first,[shortest,max(hints,key=lambda r:len(r['messages'][-1]['content']))],[longest,min(hints,key=lambda r:len(r['messages'][-1]['content']))]]
  sourcepins={x['sample_id']:sha_bytes(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()) for g in groups for x in g}
  outcomes=[]
  def measure(label):
   FastLanguageModel.for_training(model);model.gradient_checkpointing_disable();model.config.use_cache=False;model.eval()
   for gi,g in enumerate(groups):
    encoded=[{'encoded':helper.tokenize_assistant_only(row,tok,max_sequence_tokens=2048)} for row in g]
    batch=H.collate(encoded,tok,'cuda')
    with torch.no_grad(),torch.autocast('cuda',dtype=torch.float16):
     actual=model(**batch,use_cache=False).loss
     logits=model(input_ids=batch['input_ids'],attention_mask=batch['attention_mask'],use_cache=False).logits
     assert isinstance(logits,torch.Tensor) and logits.shape[:2]==batch['input_ids'].shape,'No full logits; audit must not substitute assumptions'
     shifted_labels=batch['labels'][:,1:];valid=shifted_labels!=-100
     expected=F.cross_entropy(logits[:,:-1,:][valid].float(),shifted_labels[valid],reduction='mean')
     direct_valid=batch['labels']!=-100
     unshifted=F.cross_entropy(logits[direct_valid].float(),batch['labels'][direct_valid],reduction='mean')
    result={'stage':label,'group':gi,'sample_ids':[x['sample_id'] for x in g],'shapes':list(batch['input_ids'].shape),'actual_forward_loss':float(actual),'manual_next_token_ce':float(expected),'manual_unshifted_ce':float(unshifted),'absolute_error_next_token':abs(float(actual)-float(expected)),'supervised_tokens_shifted':int(valid.sum()),'finite':all(torch.isfinite(v).item() for v in [actual,expected,unshifted])}
    result['causal_loss_parity_pass']=result['finite'] and result['absolute_error_next_token']<.02
    outcomes.append(result);atomic(O/'progress.json',{'state':'FORWARD_AUDIT','results':outcomes,'optimizer_updates':0})
    del logits,batch,actual,expected,unshifted;torch.cuda.empty_cache()
  measure('untrained_base')
  from peft import PeftModel,get_peft_model_state_dict
  from peft.utils.save_and_load import load_peft_weights
  g=R/'training/generation_step_000050_rows_00000800';W.verify_generation(g)
  model=PeftModel.from_pretrained(model,str(g),is_trainable=False)
  wanted=load_peft_weights(str(g),device='cpu');actual=get_peft_model_state_dict(model)
  assert set(wanted)==set(actual) and all(torch.equal(actual[k].detach().cpu(),wanted[k].to(dtype=actual[k].dtype)) for k in wanted)
  del wanted,actual
  measure('existing_step50_adapter')
  atomic(O/'forward_loss_audit.json',{'complete':True,'results':outcomes,'all_next_token_parity_pass':all(x['causal_loss_parity_pass'] for x in outcomes),'original_training_rows_only':True,'canonical_embedded_row_pins':sourcepins,'model':W.MODEL,'revision':W.REV,'optimizer_updates':0,'new_adapter_created':False,'source_modified':False,'heldout_test_read':False,'worker_sha256':sha(__file__),'completed_unix':time.time(),'hard_deadline_unix':scope['hard_deadline_unix']})
  print(json.dumps({'complete':True,'all_next_token_parity_pass':all(x['causal_loss_parity_pass'] for x in outcomes),'results':outcomes,'optimizer_updates':0}),flush=True)
 finally:timer.cancel()
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
if __name__=='__main__':
 try:main()
 except BaseException as e:
  if O.exists():atomic(O/'error.json',{'error':repr(e),'traceback':traceback.format_exc(),'optimizer_updates':0})
  raise
