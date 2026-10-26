"""Post-hoc validation correction and base-model diagnostic, no weight updates.

The original test has already been evaluated: it is now development/regression
data, never describe this follow-up as a new untouched gold test.
"""
import argparse
import hashlib
import json
from pathlib import Path
from mcq_final_answer import aggregate_normalized,parse_final
from train_real_math import MODEL,REVISION,evaluate,rows
from real_math_data import write_json

RUN_ID='base_normalized_mcq_posthoc_seed20261012'

def main(root):
    import torch
    from transformers import AutoModelForCausalLM,AutoTokenizer
    root=Path(root);old=root/'runs'/'qwen3_06b_real_mcq_2epoch_seed20261012'
    run=root/'runs'/RUN_ID;run.mkdir(parents=True,exist_ok=True)
    if (run/'completed_run.json').exists():print((run/'completed_run.json').read_text(encoding='utf-8'));return
    splits={s:rows(root/'data'/'clean'/(s+'.jsonl')) for s in ('val','test')}
    val={name:aggregate_normalized(splits['val'],rows(old/(filename+'.jsonl'))) for name,filename in
         (('base','baseline_val'),('epoch1','epoch1_val'),('epoch2','epoch2_val'))}
    selected=max(val,key=lambda x:val[x]['accuracy'])
    assert selected=='base','Normalization did not confirm base superiority; reassess before this base-only diagnostic'
    decision={'status':'SFT_REJECTED_MATH_ACCURACY_REGRESSION','experiment_selected_by_strict_json':'epoch2',
        'reviewer_selected':'base','normalized_validation':val,'selection_uses_validation_only':True,
        'protocol_changed_posthoc':True,'existing_test_is_now_development_not_new_gold':True,
        'previous_safe_planner_preserved':True,'production_approved':False}
    write_json(run/'reviewer_decision.json',decision);write_json(old/'reviewer_rejection.json',decision)
    config={'model':MODEL,'revision':REVISION,'run_id':RUN_ID,'training':False,
        'normalizer_sha256':hashlib.sha256((run/'src'/'mcq_final_answer.py').read_bytes()).hexdigest(),
        'evaluator_sha256':hashlib.sha256((run/'src'/'eval_base_normalized.py').read_bytes()).hexdigest(),
        'original_run_config_sha256':hashlib.sha256((old/'config.json').read_bytes()).hexdigest(),
        'dataset_hashes':{s:hashlib.sha256((root/'data'/'clean'/(s+'.jsonl')).read_bytes()).hexdigest() for s in splits},
        'max_new_tokens':768,'thinking':True,'seed':20261012}
    if (run/'config.json').exists():assert json.loads((run/'config.json').read_text(encoding='utf-8'))==config
    else:write_json(run/'config.json',config)
    tokenizer=AutoTokenizer.from_pretrained(MODEL,revision=REVISION)
    if tokenizer.pad_token_id is None:tokenizer.pad_token=tokenizer.eos_token
    model=AutoModelForCausalLM.from_pretrained(MODEL,revision=REVISION,dtype=torch.float16,attn_implementation='sdpa').to('cuda')
    raw=evaluate(model,tokenizer,splits['test'],run/'base_dev_test.jsonl','base:'+REVISION)
    raw_rot=evaluate(model,tokenizer,splits['test'],run/'base_rotated_dev_test.jsonl','base:'+REVISION,shift=1)
    base_test=rows(run/'base_dev_test.jsonl');base_rotation=rows(run/'base_rotated_dev_test.jsonl')
    base=aggregate_normalized(splits['test'],base_test);rot=aggregate_normalized(splits['test'],base_rotation,1)
    sft=aggregate_normalized(splits['test'],rows(old/'selected_test.jsonl'))
    sft_rot=aggregate_normalized(splits['test'],rows(old/'selected_rotated_test.jsonl'),1)
    answers=[(parse_final(a['prediction'],a['scores']['truncated']),parse_final(b['prediction'],b['scores']['truncated'])) for a,b in zip(base_test,base_rotation)]
    consistency=sum(a is not None and b is not None and ord(a)-65==(ord(b)-65+1)%4 for a,b in answers)/len(answers)
    result={'status':'BASE_RETAINED_SFT_REJECTED_RESEARCH_ONLY','run_id':RUN_ID,'model':MODEL,'revision':REVISION,
        'normalized_validation':val,'base_development_test':base,'base_rotated_development_test':rot,
        'sft_development_test':sft,'sft_rotated_development_test':sft_rot,
        'base_choice_rotation_consistency':consistency,'strict_base_development_test':raw,
        'strict_base_rotated_development_test':raw_rot,'training_performed':False,'production_approved':False,
        'limitations':['This is a post-hoc protocol correction; test is no longer untouched.',
            'Source labels are not teacher-certified; pretraining contamination unknown.',
            'Parsing an explicit choice does not certify the free explanation or arbitrary problem semantics.',
            'Only a few grade 1–3 rows, and no grade 2 validation rows.']}
    write_json(run/'completed_run.json',result);write_json(run/'progress.json',{'phase':'completed','status':result['status']})
    print('MVK_BASE_NORMALIZED_COMPLETED='+json.dumps(result,ensure_ascii=False),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();main(a.root)
