"""Recompute the post-hoc correction; certify evidence, never pedagogy."""
import hashlib
import json
from pathlib import Path
from mcq_final_answer import aggregate_normalized,parse_final
from train_real_math import rows
from real_math_data import write_json,validate

def audit(root):
    root=Path(root);old=root/'runs'/'qwen3_06b_real_mcq_2epoch_seed20261012'
    run=root/'runs'/'base_normalized_mcq_posthoc_seed20261012'
    report=json.loads((run/'completed_run.json').read_text(encoding='utf-8'))
    config=json.loads((run/'config.json').read_text(encoding='utf-8'))
    decision=json.loads((run/'reviewer_decision.json').read_text(encoding='utf-8'))
    split={s:rows(root/'data'/'clean'/(s+'.jsonl')) for s in ('train','val','test')};validate(split)
    assert config['training'] is False and report['training_performed'] is False
    assert hashlib.sha256((run/'src'/'mcq_final_answer.py').read_bytes()).hexdigest()==config['normalizer_sha256']
    assert hashlib.sha256((run/'src'/'eval_base_normalized.py').read_bytes()).hexdigest()==config['evaluator_sha256']
    assert hashlib.sha256((old/'config.json').read_bytes()).hexdigest()==config['original_run_config_sha256']
    original=json.loads((old/'config.json').read_text(encoding='utf-8'))
    for name,sha in original['source_hashes'].items():assert hashlib.sha256((root/'src'/name).read_bytes()).hexdigest()==sha
    for s,sha in config['dataset_hashes'].items():assert hashlib.sha256((root/'data'/'clean'/(s+'.jsonl')).read_bytes()).hexdigest()==sha
    val={name:aggregate_normalized(split['val'],rows(old/(file+'.jsonl'))) for name,file in
         (('base','baseline_val'),('epoch1','epoch1_val'),('epoch2','epoch2_val'))}
    assert val==report['normalized_validation']==decision['normalized_validation']
    assert max(val,key=lambda x:val[x]['accuracy'])==decision['reviewer_selected']=='base'
    for directory,file,key,shift in [(run,'base_dev_test','base_development_test',0),
        (run,'base_rotated_dev_test','base_rotated_development_test',1),
        (old,'selected_test','sft_development_test',0),(old,'selected_rotated_test','sft_rotated_development_test',1)]:
        predictions=rows(directory/(file+'.jsonl'))
        assert len(predictions)==100 and len({r['sample_id'] for r in predictions})==100
        assert aggregate_normalized(split['test'],predictions,shift)==report[key]
    raw=rows(run/'base_dev_test.jsonl');rot=rows(run/'base_rotated_dev_test.jsonl')
    pairs=[(parse_final(a['prediction'],a['scores']['truncated']),parse_final(b['prediction'],b['scores']['truncated'])) for a,b in zip(raw,rot)]
    consistency=sum(a is not None and b is not None and ord(a)-65==(ord(b)-65+1)%4 for a,b in pairs)/100
    assert consistency==report['base_choice_rotation_consistency']
    assert decision['protocol_changed_posthoc'] and decision['existing_test_is_now_development_not_new_gold']
    acceptance={'status':'BASE_RETAINED_SFT_REJECTED_RESEARCH_ONLY','reviewer_selected':'base',
        'promote_sft_adapter':False,'use_sft_adapter_as_next_training_base':False,
        'production_approved':False,'protocol_correction_is_posthoc':True,
        'untouched_gold_test_available':False,'base_validation_correct':val['base']['correct'],
        'sft_validation_correct':val['epoch2']['correct']}
    write_json(run/'reviewer_acceptance.json',acceptance);write_json(old/'reviewer_acceptance.json',acceptance)
    result={'status':'PASSED','normalizer_and_evaluator_hashes_verified':True,'original_code_hashes_preserved':True,
        'all_ids_and_scores_recomputed':True,'base_retained_by_validation':True,'no_weight_updates':True,
        'test_role':'posthoc development/regression, not new untouched gold',
        'does_not_certify_arbitrary_problem_or_explanation_correctness':True}
    write_json(run/'reviewer_audit.json',result);return result

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();print(json.dumps(audit(a.root)))
