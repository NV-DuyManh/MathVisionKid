"""Derive the new experiment explicitly; preserve all previous run code."""
from pathlib import Path
import ast,hashlib,json

P=Path(__file__).parent
OLD=P.parent/'skill_recovery_150m_20261024'
PREP=P.parent/'conditional_grounding_20261024'
def sha(b):return hashlib.sha256(b).hexdigest()
def write(name,text):
 compile(text,name,'exec')
 path=P/name
 raw=text.encode('utf8')
 if path.exists() and path.read_bytes()!=raw:
  history=P/'authoring_history';history.mkdir(exist_ok=True)
  previous=path.read_bytes();(history/(name+'.'+sha(previous))).write_bytes(previous)
 path.write_bytes(raw)

# Remove only the later replacement of prepare_plan. The original validated
# 10-worked/6-hint schedule retains all 4000 worked rows in a one-pass view.
policy=(OLD/'recovery_policy_v2.py').read_text(encoding='utf8')
nodes=[n for n in ast.parse(policy).body if isinstance(n,ast.FunctionDef) and n.name=='prepare_plan']
assert len(nodes)==2
lines=policy.splitlines(keepends=True);node=nodes[1]
policy=''.join(lines[:node.lineno-1]+lines[node.end_lineno:])
write('recovery_policy_v2.py',policy)
write('recovery_policy.py','from recovery_policy_v2 import *\n')

inference=(OLD/'inference_contract.py').read_text(encoding='utf8')
assert inference.count('import behavior_renderer as B')==1
inference=inference.replace('import behavior_renderer as B','import conditional_behavior_renderer as B')
inference=inference.replace('MathVisionKid.skill_recovery_matched_eval.v1','MathVisionKid.conditional_native_matched_eval.v1')
inference=inference.replace('behavior_renderer.prompt: explicit mode, unchanged source problem, exact-duplicate context omitted',
 'conditional_behavior_renderer.prompt: explicit mode, unchanged source problem, conditional worked instruction; no oracle routing')
write('inference_contract.py',inference)

for name,source in {
 'conditional_behavior_renderer.py':PREP/'conditional_behavior_renderer.py',
 'behavior_renderer.py':OLD/'behavior_renderer.py',
 'verbal_training_renderer_v3.py':P.parent/'verbal_recovery_20261024/verbal_training_renderer_v3.py',
 'test_behavior_renderer.py':OLD/'test_behavior_renderer.py',
 'test_conditional_behavior_renderer.py':PREP/'test_conditional_behavior_renderer.py',
 'test_exact_math_audit.py':PREP/'test_exact_math_audit.py',
 'exact_math_audit.py':PREP/'exact_math_audit.py',
 'test_recovery_policy.py':OLD/'test_recovery_policy.py',
 'test_recovery_worker.py':OLD/'test_recovery_worker.py',
}.items():
 raw=source.read_bytes();compile(raw,name,'exec')
 target=P/name
 if target.exists() and target.read_bytes()!=raw:
  history=P/'authoring_history';history.mkdir(exist_ok=True)
  previous=target.read_bytes();(history/(name+'.'+sha(previous))).write_bytes(previous)
 target.write_bytes(raw)
worker=(OLD/'recovery_worker_v3.py').read_text(encoding='utf8')
replacements={
 'import behavior_renderer as V':'import conditional_behavior_renderer as V',
 "root/'behavior_renderer.py'":"root/'conditional_behavior_renderer.py'",
 '763da2f7a1931962a9ad1a49b16d4b8dfe5263a09e69603c49959adb02a5ec8f':sha((P/'conditional_behavior_renderer.py').read_bytes()),
 '6b44ebabad6eeca636142012418e17f126ae9d57539e10b4d1fa5b4314033bc0':sha((P/'inference_contract.py').read_bytes()),
 'from unsloth import FastLanguageModel':'from native_backend import NativeBackend as FastLanguageModel',
 "[100,300]":"[100,300,500]",
 "'max_successful_updates':300":"'max_successful_updates':500",
 "'schema':'MathVisionKid.quality_recovery_run.v1'":"'backend':'native Transformers/PEFT/bitsandbytes; no Unsloth', 'schema':'MathVisionKid.conditional_native_recovery_run.v1'",
 "'validation_scope':'Reused dev30 matched official nonthinking sampling, behavior-aligned prompts and balanced skill schedule; prior locked/final20 excluded; new final20 sealed before this branch outputs'":
 "'validation_scope':'Fresh authored development30 reviewed before model outputs and screened against actual16k source; never used as training targets. Prior used finals excluded; untouched native_locked15 reserved for final-only if eligible.'",
 "'loss_reduction':'unchanged originalmicro2 supervised-token mean weighted pair_rows/group_rows; source targets unchangedV3; mode-aware deduplicated prompt, grade/behavior/topic balanced one-pass schedule'":
 "'loss_reduction':'micro2 supervised-token mean weighted pair_rows/group_rows; source targets unchangedV3; conditional worked prompt; grade interleave10worked6hint no repeats'",
}
for old,new in replacements.items():
 assert old in worker,old
 worker=worker.replace(old,new)
needle="   with torch.autocast('cuda',dtype=torch.float16):loss=model(**batch,use_cache=False).loss*(len(items)/n)"
assert worker.count(needle)==1
worker=worker.replace(needle,"""   with torch.autocast('cuda',dtype=torch.float16):
    forward=model(**batch,use_cache=False)
    if state['step']==0 and j==0:
     with torch.no_grad():
      manual=torch.nn.functional.cross_entropy(forward.logits[:,:-1,:].float().reshape(-1,forward.logits.shape[-1]),batch['labels'][:,1:].reshape(-1),ignore_index=-100)
      difference=abs(float(manual)-float(forward.loss.detach()))
      if difference>1e-4:raise ValueError('Native forward loss differs from explicit shifted assistant-only CE')
      atomic(out/'native_first_microbatch_audit.json',{'shifted_CE_matches_forward':True,'absolute_difference':difference,'supervised_tokens':int((batch['labels'][:,1:]!=-100).sum()),'prompt_tokens_excluded_by_source_mask':True,'model_backend':'native Transformers/PEFT'})
    loss=forward.loss*(len(items)/n)
   del forward""")
needle="  old_scale=scaler.get_scale();scaler.step(opt);scaler.update();torch.cuda.synchronize()"
assert worker.count(needle)==1
worker=worker.replace(needle,"  if float(norm)<=0:raise FloatingPointError('No nonzero trainable LoRA gradient; do not apply optimizer step')\n\n"+needle)
write('recovery_worker_v3.py',worker)
# Existing unit tests exercise pure checkpoint/gate/replay invariants using the
# same local module name; no model or network calls occur in these tests.
write('recovery_worker.py',worker)
write('recovery_worker_v2.py','from recovery_worker_v3 import *\n')

publisher=(OLD/'publisher_runtime.py').read_text(encoding='utf8')
publisher=publisher.replace('mathvisionkid_skill_recovery_150m_20261024','mathvisionkid_conditional_grounding_20261025')
publisher=publisher.replace('MathVisionKid_SKILL_RECOVERY_150M_20261024','MathVisionKid_CONDITIONAL_GROUNDING_20261025')
publisher=publisher.replace('MathVisionKidSkillRecoveryPublisher','MathVisionKidConditionalGroundingPublisher')
publisher=publisher.replace('_mathvisionkid_skill_recovery_publisher_registry','_mathvisionkid_conditional_grounding_publisher_registry')
needle='  initial+=sorted'
assert publisher.count(needle)==1
publisher=publisher.replace(needle,"  initial+=['conditional_behavior_renderer.py','native_backend.py','recovery_worker_v3.py','recovery_policy_v2.py','inference_contract.py','development_root_review.json','development_author_notes.json','preparation_code_provenance.json','source_qa_binding.json','cpu_validation.json','install_complete.json']\n"+needle)
write('publisher_runtime.py',publisher)
provenance={'schema':'MathVisionKid.conditional_code_derivation.v1',
 'parent_worker_sha256':sha((OLD/'recovery_worker_v3.py').read_bytes()),
 'parent_policy_sha256':sha((OLD/'recovery_policy_v2.py').read_bytes()),
 'parent_inference_sha256':sha((OLD/'inference_contract.py').read_bytes()),
 'parent_publisher_sha256':sha((OLD/'publisher_runtime.py').read_bytes()),
 'derived_files':{n:sha((P/n).read_bytes()) for n in ['recovery_worker_v3.py','recovery_policy_v2.py','inference_contract.py','publisher_runtime.py','conditional_behavior_renderer.py','native_backend.py']},
 'changes':['Conditional worked instruction; original target bytes unchanged',
 'Original10worked6hint grade-interleaved schedule retains allworked; removes later hierarchy override',
 'Native Transformers/PEFT backend uses existing Colab packages; no Unsloth claimed',
 'One derived pass with upper cap500 and gates100/300/500; deadline unchanged',
 'Fresh development30; no old final data in code payload or training'],
 'old_files_modified':False,'new_human_attestation':False}
(P/'preparation_code_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
print(json.dumps(provenance))
