"""Matched bounded base/adapter evaluation with official Qwen sampling settings."""
import json,hashlib,time,pathlib
import conditional_behavior_renderer as B
MODEL='Qwen/Qwen3-1.7B';REVISION='70d244cc86ccca08cf5af4e1e306ecf908b1ad5e'
MODE_MAP={'answer':'worked_solution','hint_no_answer':'hint_level_1','student_error':'worked_solution','missing_or_contradictory_info':'worked_solution'}
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def digest(x):return hashlib.sha256(x).hexdigest()
def messages(f):
 return [{'role':'system','content':B.SYSTEM},{'role':'user','content':B.prompt({'grade':f['grade'],'problem':f['userproblem'],'mode':MODE_MAP[f['mode']]})}]
def token_ids(tok,f):
 x=tok.apply_chat_template(messages(f),tokenize=True,add_generation_prompt=True,enable_thinking=False)
 return x['input_ids'] if hasattr(x,'keys') else x
def eval_contract(fixtures,tok,fixture_sha256=None):
 c={'schema':'MathVisionKid.conditional_native_matched_eval.v1','model':MODEL,'revision':REVISION,'fixture_sha256':digest(('\n'.join(canonical(f) for f in fixtures)+'\n').encode()),'fixture_ids':[f['id'] for f in fixtures],'system':B.SYSTEM,'system_sha256':digest(B.SYSTEM.encode()),'mode_map':MODE_MAP,'renderer_version':B.VERSION,'user_serialization':'conditional_behavior_renderer.prompt: explicit mode, unchanged source problem, conditional worked instruction; no oracle routing','enable_thinking':False,'add_generation_prompt':True,'prompt_token_sha256':{f['id']:digest(canonical(token_ids(tok,f)).encode()) for f in fixtures},'seed_policy':'20261024 + first8hex fixtureID SHA modulo2^31; reset per fixture, matched base/adapter','decoding':{'do_sample':True,'temperature':.7,'top_p':.8,'top_k':20,'min_p':0.,'num_beams':1,'max_new_tokens':1024,'repetition_penalty':1.,'use_cache':True,'pad_token_id':tok.pad_token_id,'eos_token_id':151645}}
 if fixture_sha256 is not None:
  if len(fixture_sha256)!=64 or any(x not in '0123456789abcdef' for x in fixture_sha256):raise ValueError('Explicit frozen fixture raw SHA required')
  c['fixture_sha256']=fixture_sha256
 return c,digest(canonical(c).encode())
def generate_fixtures(model,tok,fixtures,out,stage,contract,csha,timeout_seconds,fast_model):
 import torch,random
 from transformers import GenerationConfig
 out=pathlib.Path(out);name='base_generations.jsonl' if stage=='base_before_training' else 'adapter_generations.jsonl';path=out/name
 if path.exists():raise FileExistsError('Do not silently rerun existing generation')
 partial=path.with_name(path.stem+'.partial.jsonl')
 if partial.exists():raise FileExistsError('Partial attempt already exists; keep original evidence')
 assert digest(canonical(contract).encode())==csha
 fast_model.for_inference(model);model.eval();cutoff=time.monotonic()+timeout_seconds
 for f in fixtures:
  left=cutoff-time.monotonic()
  if left<=1:raise TimeoutError('Matched development inference budget exhausted')
  seed=(20261024+int(digest(f['id'].encode())[:8],16))%(2**31)
  torch.manual_seed(seed);torch.cuda.manual_seed_all(seed);random.seed(seed)
  ids=tok.apply_chat_template(messages(f),tokenize=True,add_generation_prompt=True,enable_thinking=False,return_tensors='pt',return_dict=True).to('cuda')
  assert digest(canonical(ids['input_ids'][0].tolist()).encode())==contract['prompt_token_sha256'][f['id']]
  t=time.monotonic()
  with torch.inference_mode():result=model.generate(**ids,generation_config=GenerationConfig(**contract['decoding']),max_time=left)
  tokens=result[0,ids['input_ids'].shape[1]:];eos=bool(len(tokens) and int(tokens[-1])==151645)
  row={'fixture_id':f['id'],'grade':f['grade'],'mode':f['mode'],'model_mode':MODE_MAP[f['mode']],'stage':stage,'contract_sha256':csha,'prompt_token_sha256':contract['prompt_token_sha256'][f['id']],'max_new_tokens':1024,'generated_tokens':len(tokens),'output':tok.decode(tokens,skip_special_tokens=True).strip(),'ended_eos':eos,'possibly_truncated':not eos,'timed_out':time.monotonic()>=cutoff,'seed':seed,'generation_seconds':time.monotonic()-t}
  with partial.open('a',encoding='utf8') as stream:stream.write(json.dumps(row,ensure_ascii=False)+'\n');stream.flush()
 partial.replace(path)
 proof={'model':MODEL,'revision':REVISION,'contract_sha256':csha,'fixture_sha256':contract['fixture_sha256'],'stage':stage,'outputs_sha256':digest(path.read_bytes()),'same_generation_protocol_as_other_model':True}
 (out/('base_generation_provenance.json' if stage=='base_before_training' else 'adapter_generation_provenance.json')).write_text(json.dumps(proof,indent=2)+'\n')
