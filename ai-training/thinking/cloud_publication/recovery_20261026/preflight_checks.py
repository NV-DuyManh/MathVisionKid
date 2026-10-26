"""CPU-only checks for the fresh 2026-10-26 branch; never reads private corpora."""
import importlib.util
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import recovery_policy_20261026 as P
spec=importlib.util.spec_from_file_location("fresh_worker",HERE/"recovery_worker_20261026.py")
W=importlib.util.module_from_spec(spec);spec.loader.exec_module(W)

def row(sid,mode,target,grade=1,topic="algebra"):
 return {"sample_id":sid,"split":"train","grade":grade,"topic":topic,"mode":mode,"messages":[{"role":"system","content":"s"},{"role":"user","content":'{"mode":"'+mode+'","problem":"p"}'},{"role":"assistant","content":target}]}

# Dedup identical hints in the derived schedule while preserving all worked examples.
rows=[row("w1","worked_solution","worked one"),row("w2","worked_solution","worked two"),row("h1","hint_level_1","same hint"),row("h2","hint_level_1","same hint")]
plan=P.prepare_plan(rows,"0"*64)
assert plan["source_rows"]==4 and plan["view_rows"]==3
assert set(plan["schedule"]) in ({"w1","w2","h1"},{"w1","w2","h2"})
assert plan["all_worked_solutions_preserved"] and plan["source_rows_modified_or_deleted"]==0

# Validate a complete synthetic paired-review gate at the first improvement gate.
fixtures=[(f"f{i:02d}","answer" if i<10 else "hint_no_answer" if i<20 else "missing_or_contradictory_info" if i<25 else "student_error") for i in range(30)]
records=[]
for i,(fid,mode) in enumerate(fixtures):
 records.append({"fixture_id":fid,"mode":mode,"grade":i%5+1,"base_pass":mode=="answer","adapter_pass":mode=="answer" or i==10,"base_hint_leak":False,"adapter_hint_leak":False,"critical_new_error":False})
bind={k:("a" if k=="dev_sha256" else "b" if k=="contract_sha256" else "c" if k=="source_plan_sha256" else "d" if k=="base_output_sha256" else "e" if k=="adapter_output_sha256" else "f")*64 for k in P.GATE_HASH_FIELDS}
bind["fixture_ids"]=[f[0] for f in fixtures]
gate={**bind,"step":100,"all_actual_outputs_reviewed":True,"human_review_claimed":False,"decision":"CONTINUE_IMPROVED","decisions":records}
assert P.validate_gate(gate,100,bind)=="CONTINUE_IMPROVED"
summary=P.summarize_decisions(records)
assert summary["candidate_eligible"] and P.selection_key(summary,"candidate")>P.selection_key(summary,"base")

# Exact row objective: unequal-length rows have equal weight after per-row token means.
import torch
logits=torch.tensor([[[3.,0.],[0.,3.],[3.,0.],[0.,3.]],[[0.,3.],[3.,0.],[0.,3.],[3.,0.]]],requires_grad=True)
labels=torch.tensor([[-100,0,0,0],[-100,1,0,-100]])
loss=W.row_mean_assistant_loss(logits,labels)
shifted_logits=logits[:,:-1,:].float();shifted_labels=labels[:,1:];row_refs=[]
for i in range(shifted_labels.shape[0]):
 mask=shifted_labels[i]!=-100
 row_refs.append(torch.nn.functional.cross_entropy(shifted_logits[i][mask],shifted_labels[i][mask]))
manual=torch.stack(row_refs).mean()
assert torch.allclose(loss,manual,atol=1e-7,rtol=1e-7)
grad_a=torch.autograd.grad(loss,logits,retain_graph=True)[0]
grad_b=torch.autograd.grad(manual,logits)[0]
assert torch.allclose(grad_a,grad_b,atol=1e-7,rtol=1e-7)
assert torch.count_nonzero(grad_a[:, :-1, :][~(shifted_labels!=-100)])==0
assert "model_inputs={k:v for k,v in batch.items() if k!='labels'}" in (HERE/"recovery_worker_20261026.py").read_text(encoding="utf-8")
print("PASS: synthetic source-plan dedup, worked-example retention, 30-fixture improvement gate, and selected-token row CE/value/gradient masking")
