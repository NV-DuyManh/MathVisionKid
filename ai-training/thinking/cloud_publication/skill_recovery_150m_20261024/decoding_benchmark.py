"""Bounded base-only development calibration, no optimizer or locked test."""
import pathlib,json,hashlib,sys,time,os,traceback,random
from datetime import datetime,timezone
R=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024')
REV='70d244cc86ccca08cf5af4e1e306ecf908b1ad5e'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
 b=(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode();q=p.with_suffix(p.suffix+'.pending');q.write_bytes(b);q.replace(p)
def main():
 scope=json.loads((R/'owner_run_scope.json').read_bytes());cutoff=min(time.time()+650,scope['hard_deadline_unix']-1800)
 out=R/'benchmark';out.mkdir(exist_ok=False)
 save(out/'attempt_started.json',{'started_utc':datetime.now(timezone.utc).isoformat(),'deadline_unix':cutoff,'training_performed':False,'locked_test_accessed':False})
 assert sha(R/'new_validation_candidates.jsonl')=='75eab78085830aa5bf0cf856eb6f70d2630e2407c8143409816dec94d849aaed'
 assert sha(R/'verbal_training_renderer_v3.py')=='6b15233ae253eed7825864413edbdf3f8553ad955ef248e045c05f64e4473057'
 sys.path.insert(0,str(R));import verbal_training_renderer_v3 as V
 from unsloth import FastLanguageModel
 import torch
 from transformers import BitsAndBytesConfig,GenerationConfig
 assert 'T4' in torch.cuda.get_device_name(0)
 quant=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_compute_dtype=torch.float16,bnb_4bit_use_double_quant=True)
 model,tok=FastLanguageModel.from_pretrained(model_name=scope['model'],revision=REV,use_exact_model_name=True,max_seq_length=4096,dtype=torch.float16,load_in_4bit=True,quantization_config=quant,attn_implementation='sdpa')
 assert model.config._commit_hash==REV and tok.eos_token_id==151645
 FastLanguageModel.for_inference(model);model.eval()
 fixtures=[json.loads(x) for x in (R/'new_validation_candidates.jsonl').read_text().splitlines()]
 selected=[fixtures[i] for i in [24,15,16,17]]
 system='Bạn là gia sư Toán tiểu học. Trả lời bằng tiếng Việt theo yêu cầu. Chỉ đưa lời giải đầy đủ khi được yêu cầu; gợi ý không điền đáp số. Chỉ nhận xét lời làm thực sự được cung cấp.'
 configs=[{'name':'official_nonthinking','thinking':False,'temperature':.7,'top_p':.8,'top_k':20},{'name':'official_thinking','thinking':True,'temperature':.6,'top_p':.95,'top_k':20}]
 contract={'model':scope['model'],'revision':REV,'fixture_ids':[f['id'] for f in selected],'source':'Previously used dev30; calibration only, not independent heldout.','renderer_sha256':sha(R/'verbal_training_renderer_v3.py'),'system':system,'decoding':configs,'max_new_tokens':1536,'seed':20261024,'same_prompt_text_except_enable_thinking':True,'paid_resource':False}
 save(out/'contract.json',contract);records=[]
 for f in selected:
  for c in configs:
   left=cutoff-time.time()
   if left<15:raise TimeoutError('Calibration wall-clock exhausted; keep partial evidence')
   torch.manual_seed(20261024);torch.cuda.manual_seed_all(20261024);random.seed(20261024)
   mode='hint_level_1' if f['mode']=='hint_no_answer' else 'worked_solution'
   messages=[{'role':'system','content':system},{'role':'user','content':V.prompt({'grade':f['grade'],'problem':f['userproblem'],'mode':mode})}]
   ids=tok.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,enable_thinking=c['thinking'],return_tensors='pt',return_dict=True).to('cuda')
   gc=GenerationConfig(do_sample=True,temperature=c['temperature'],top_p=c['top_p'],top_k=c['top_k'],min_p=0.,max_new_tokens=1536,eos_token_id=151645,pad_token_id=tok.pad_token_id,use_cache=True,repetition_penalty=1.)
   t=time.monotonic()
   with torch.inference_mode():result=model.generate(**ids,generation_config=gc,max_time=min(left-5,120))
   tokens=result[0,ids['input_ids'].shape[1]:];full=tok.decode(tokens,skip_special_tokens=False);eos=bool(len(tokens) and int(tokens[-1])==151645)
   closed=(not c['thinking']) or '</think>' in full
   answer=full.rsplit('</think>',1)[-1] if c['thinking'] and closed else (full if not c['thinking'] else '')
   answer=answer.replace('<|im_end|>','').strip()
   row={'fixture_id':f['id'],'grade':f['grade'],'mode':f['mode'],'configuration':c['name'],'thinking':c['thinking'],'final_answer':answer,'thinking_closed':closed,'ended_eos':eos,'generated_tokens':len(tokens),'duration_seconds':time.monotonic()-t,'possibly_truncated':not eos,'raw_output_sha256':hashlib.sha256(full.encode()).hexdigest(),'prompt_token_sha256':hashlib.sha256(json.dumps(ids['input_ids'][0].tolist()).encode()).hexdigest(),'training_performed':False}
   with (out/'raw_generations.partial.jsonl').open('a') as stream:stream.write(json.dumps({**row,'raw_output':full},ensure_ascii=False)+'\n')
   with (out/'final_generations.partial.jsonl').open('a') as stream:stream.write(json.dumps(row,ensure_ascii=False)+'\n')
   records.append(row);save(out/'progress.json',{'completed':len(records),'total':8,'last_fixture':f['id'],'last_configuration':c['name'],'last_eos':eos,'training_performed':False})
 for name in ['raw_generations','final_generations']:(out/(name+'.partial.jsonl')).replace(out/(name+'.jsonl'))
 save(out/'complete.json',{'complete':True,'count':8,'training_performed':False,'optimizer_loaded':False,'locked_test_accessed':False,'finished_utc':datetime.now(timezone.utc).isoformat(),'files':{p.name:sha(p) for p in out.iterdir() if p.is_file()}})
 print(json.dumps({'state':'CALIBRATION_COMPLETE','count':8}))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  if (R/'benchmark').exists():save(R/'benchmark/error.json',{'error':repr(e),'traceback':traceback.format_exc(),'training_performed':False})
  raise
