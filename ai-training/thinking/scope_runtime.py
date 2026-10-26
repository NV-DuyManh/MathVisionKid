"""Serve only verified, bounded MathVisionKid solutions, never raw model prose.

The callable is a future planner adapter, not a general-purpose chat endpoint.
This module has no side effects or GPU dependencies.
"""
import json
from scope_contract import inspect_problem, expected_plan, verify_plan
from scope_dataset import SYSTEM, prompt

def solve_with_planner(problem, grade, generate_plan):
    contract=inspect_problem(problem,grade)
    if contract['status']!='ready':
        # Policy is enforced outside the LLM, including unknown/off-topic inputs.
        return verify_plan(problem,grade,expected_plan(contract))
    user=prompt({'problem':problem,'grade':grade,'trusted_source_contract':contract})
    try:
        candidate=generate_plan(SYSTEM,user)
    except Exception:
        return {'accepted':False,'status':'verification_failed','answer':None,
                'reason':'PLANNER_CALL_FAILED','message':'Mình chưa xác minh được lời giải. Bạn thử lại nhé.'}
    result=verify_plan(problem,grade,candidate)
    if not result['accepted']:
        result['message']='Mình chưa xác minh được lời giải này nên chưa đưa đáp số.'
    return result

def hf_planner(model,tokenizer,max_new_tokens=512):
    """Bind a trained scope planner; this does not imply an adapter is ready."""
    def generate(system,user):
        import torch
        inputs=tokenizer.apply_chat_template([{'role':'system','content':system},
            {'role':'user','content':user}],tokenize=True,add_generation_prompt=True,
            enable_thinking=True,return_dict=True,return_tensors='pt').to(model.device)
        with torch.inference_mode():
            tokens=model.generate(**inputs,max_new_tokens=max_new_tokens,do_sample=True,
                temperature=0.6,top_p=0.95,top_k=20,pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id)
        ids=tokens[0,inputs['input_ids'].shape[-1]:]
        if len(ids)>=max_new_tokens and int(ids[-1])!=tokenizer.eos_token_id:
            raise ValueError('TRUNCATED_PLANNER_OUTPUT')
        text=tokenizer.decode(ids,skip_special_tokens=True)
        prefix=tokenizer.decode(inputs['input_ids'][0][-15:],skip_special_tokens=False)
        if prefix.rstrip().endswith('<think>') and not text.lstrip().startswith('<think>'):
            text='<think>\n'+text
        return text
    return generate
