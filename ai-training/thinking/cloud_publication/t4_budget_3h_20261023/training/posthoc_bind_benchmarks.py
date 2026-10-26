#!/usr/bin/env python3
"""CPU-only post-hoc binding for native and Unsloth fixed-16 benchmarks.

Run with the isolated training venv Python, after the verified view/manifest and
both benchmark result records exist. It tokenizes the view, derives the exact
same length-quantile 16 IDs used by both workers, and checks IDs/hashes/counts.
This reconstructs Unsloth's missing ID list post hoc; it does not claim that the
original GPU benchmark recorded those IDs.
"""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path

MODEL="Qwen/Qwen3-1.7B"
REVISION="70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
RECIPE_SHA256="1bb69c394c7eaaea7034125c6b3361eebbbe0d77e0715a8454331fbe7cee3ff8"
EXPECTED_MEMBERS=32;EXPECTED_TRAIN_ROWS=6502344
MODES={"worked_solution","hint_level_1","hint_level_2","hint_level_3"}
EXPECTED_NONPAD=4639;EXPECTED_SUPERVISED=2543

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def import_helper(path):
 spec=importlib.util.spec_from_file_location('exhaustive_colab_loader',path)
 if not spec or not spec.loader:raise RuntimeError('cannot import tokenizer helper')
 mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod);return mod

def checked_expected(manifest):
 if manifest.get('recipe_sha256')!=RECIPE_SHA256:raise ValueError('wrong recipe SHA')
 if manifest.get('members_complete')!=EXPECTED_MEMBERS or manifest.get('raw_train_rows_scanned')!=EXPECTED_TRAIN_ROWS:raise ValueError('manifest lacks exact full train member scan evidence')
 if manifest.get('all_four_modes_preserved') is not True:raise ValueError('four-mode invariant absent')
 expected={}
 cases=manifest.get('selected_cases_manifest')
 if not isinstance(cases,list):raise ValueError('selected_cases_manifest missing')
 for case in cases:
  modes=case.get('rows',{})
  if set(modes)!=MODES:raise ValueError('case mode set is not exact')
  for entry in modes.values():
   sid=entry.get('sample_id');digest=entry.get('row_sha256')
   if not sid or not digest or sid in expected:raise ValueError('duplicate/missing sample binding')
   expected[sid]=digest
 if len(expected)!=manifest.get('selected_chat_rows'):raise ValueError('selected row count differs from manifest bindings')
 return expected

def get_rows(view,manifest,helper,tokenizer,max_len):
 expected=checked_expected(manifest);found={};rows=[];case_modes={}
 with Path(view).open('rb') as f:
  for n,line in enumerate(f,1):
   raw=line.rstrip(b'\r\n')
   if not raw.strip():raise ValueError(f'blank row {n}')
   row=json.loads(raw.decode('utf-8'));sid=row.get('sample_id')
   if row.get('split')!='train':raise ValueError(f'nontrain row {n}')
   digest=hashlib.sha256(raw).hexdigest()
   if sid not in expected or expected[sid]!=digest:raise ValueError(f'row hash/ID mismatch at {n}')
   if sid in found:raise ValueError(f'duplicate sample ID at {n}')
   found[sid]=digest;case_modes.setdefault(row.get('case_group_id'),set()).add(row.get('mode'))
   enc=helper.tokenize_assistant_only(row,tokenizer,max_sequence_tokens=max_len)
   rows.append({'sample_id':sid,'encoded':enc})
 if found!=expected:raise ValueError('exact view ID set differs from selected manifest')
 if any(v!=MODES for v in case_modes.values()):raise ValueError('incomplete case modes')
 if manifest.get('training_view_sha256')!=sha(view):raise ValueError('view file SHA differs from manifest')
 rows.sort(key=lambda r:len(r['encoded']['input_ids']))
 if len(rows)<16:raise ValueError('need >=16 rows')
 chosen=[rows[round(i*(len(rows)-1)/15)] for i in range(16)]
 ids=[x['sample_id'] for x in chosen]
 nonpad=sum(sum(x['encoded']['attention_mask']) for x in chosen)
 supervised=sum(sum(t!=-100 for t in x['encoded']['labels']) for x in chosen)
 return ids,nonpad,supervised

def unsloth_benchmark_record(doc):
 if isinstance(doc.get("results"),dict):return doc["results"].get("2")
 cfg=doc.get("config",{})
 bench=cfg.get("benchmark",doc.get("benchmark",{}))
 if isinstance(bench,dict):return bench.get("2") or bench.get(2)
 return None

def check_reps(rec,name,nonpad,sup):
 if rec.get('state')!='PASS' or rec.get('optimizer_steps',rec.get('optimizer_steps_during_probe'))!=0:raise ValueError(f'{name} is not a passing optimizer-free probe')
 if rec.get('same_quantile_examples') is False or rec.get('same_16_examples') is False:raise ValueError(f'{name} denies fixed shared rows')
 reps=rec.get('timed_repeats',rec.get('repeats'))
 if not isinstance(reps,list) or not reps:raise ValueError(f'{name} missing repeat records')
 for i,r in enumerate(reps):
  if r.get('unique_examples')!=16:raise ValueError(f'{name} repeat {i} not 16 examples')
  if r.get('nonpad_tokens')!=nonpad or r.get('supervised_tokens')!=sup:raise ValueError(f'{name} repeat {i} token counts mismatch selected view')
 return reps

def main():
 p=argparse.ArgumentParser();p.add_argument('--train-view',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--tokenizer-helper',type=Path,default=Path('/content/mathvisionkid_full_text_training/code/exhaustive_colab_loader.py'));p.add_argument('--native-report',type=Path,required=True);p.add_argument('--unsloth-report',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--max-seq-len',type=int,default=2048);a=p.parse_args()
 manifest=read(a.manifest)
 if manifest.get('selected_cases')!=4000 or manifest.get('selected_chat_rows')!=16000:raise ValueError('unexpected selected-view size')
 from transformers import AutoTokenizer
 tok=AutoTokenizer.from_pretrained(MODEL,revision=REVISION,trust_remote_code=False)
 helper=import_helper(a.tokenizer_helper)
 ids,nonpad,sup=get_rows(a.train_view,manifest,helper,tok,a.max_seq_len)
 if nonpad!=EXPECTED_NONPAD or sup!=EXPECTED_SUPERVISED:raise ValueError(f'fixed sample token counts differ: observed {nonpad}/{sup}')
 native=read(a.native_report);uns=read(a.unsloth_report)
 if native.get('model')!=MODEL or native.get('revision')!=REVISION:raise ValueError('native model/revision mismatch')
 if native.get('training_view_sha256')!=sha(a.train_view) or native.get('manifest_sha256')!=sha(a.manifest):raise ValueError('native report view or manifest SHA mismatch')
 native_ids=native.get('unique_sample_ids')
 if native_ids!=ids:raise ValueError('native recorded IDs differ from reconstructed quantile IDs')
 nrec=native.get('results',{}).get('2');urec=unsloth_benchmark_record(uns)
 if not nrec or not urec:raise ValueError('microbatch-2 benchmark records missing')
 nr=check_reps(nrec,'native',nonpad,sup);ur=check_reps(urec,'unsloth',nonpad,sup)
 # Unsloth output may include hashes when persisted by the runner. If present, validate; otherwise keep explicit post-hoc label.
 if uns.get('training_view_sha256') not in (None,sha(a.train_view)) or uns.get('config',{}).get('train_view_sha256') not in (None,sha(a.train_view)):raise ValueError('Unsloth view SHA mismatch')
 if uns.get('manifest_sha256') not in (None,sha(a.manifest)) or uns.get('config',{}).get('train_view_manifest_sha256') not in (None,sha(a.manifest)):raise ValueError('Unsloth manifest SHA mismatch')
 if uns.get('model') not in (None,MODEL) or uns.get('config',{}).get('model') not in (None,MODEL):raise ValueError('Unsloth model mismatch')
 if uns.get('revision') not in (None,REVISION) or uns.get('config',{}).get('revision') not in (None,REVISION):raise ValueError('Unsloth revision mismatch')
 bundle={'schema':'MathVisionKid.t4_same16_benchmark_bundle.v1','status':'PASS','model':MODEL,'revision':REVISION,'training_view_sha256':sha(a.train_view),'manifest_sha256':sha(a.manifest),'sample_ids':ids,'sample_id_evidence':{'native':'directly_recorded_and_exactly_verified','unsloth':'posthoc_reconstructed_from_hash_verified_view_and_worker_fixed_quantile_algorithm; original_worker_did_not_log_ids'},'posthoc_reconstruction':True,'sample_token_counts':{'unique_examples':16,'nonpad_tokens':nonpad,'supervised_tokens':sup},'torch_baseline':{'microbatch':2,'optimizer_steps':0,'same_sample_ids':True,'sample_ids':ids,'sample_id_evidence':'directly_recorded_by_native_benchmark_and_checked_against_posthoc_view_reconstruction','repeats':nr,'mean_group_seconds':nrec.get('mean_group_seconds'),'unique_examples_per_second':nrec.get('unique_examples_per_second'),'nonpad_tokens_per_second':nrec.get('nonpad_tokens_per_second'),'supervised_tokens_per_second':nrec.get('supervised_tokens_per_second'),'peak_vram_bytes':nrec.get('peak_vram_bytes'),'loss_implementation':native.get('loss')},'unsloth':{'microbatch':2,'optimizer_steps':0,'same_sample_ids':True,'sample_ids':ids,'sample_id_evidence':'posthoc_reconstructed_from_hash_verified_view_and_fixed_quantile_algorithm; original_worker_did_not_log_ids','repeats':ur,'mean_group_seconds':urec.get('mean_group_seconds'),'unique_examples_per_second':urec.get('unique_examples_per_second'),'nonpad_tokens_per_second':urec.get('nonpad_tokens_per_second'),'supervised_tokens_per_second':urec.get('supervised_tokens_per_second'),'peak_vram_bytes':urec.get('peak_vram_bytes'),'loss_implementation':'Unsloth path, as emitted by worker'},'comparability_limitations':['Unsloth IDs were not written by the original worker; these IDs are reconstructed post hoc from the exact hash-verified view using its fixed-quantile algorithm.','Native path uses native Transformers causal-LM cross entropy and is not the earlier V3 sparse selected-logit path.','Throughput benchmarking alone provides no semantic-quality or training-quality guarantee.']}
 a.output.parent.mkdir(parents=True,exist_ok=True);tmp=a.output.with_suffix(a.output.suffix+'.pending');tmp.write_text(json.dumps(bundle,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8');tmp.replace(a.output);print(json.dumps({'status':'PASS','bundle':str(a.output),'ids':16,'nonpad':nonpad,'supervised':sup},ensure_ascii=False))
if __name__=='__main__':main()
