from pathlib import Path
import json,hashlib
p=Path(__file__).parent
def sha(f): return hashlib.sha256(f.read_bytes()).hexdigest()
policy={
 'schema':'MathVisionKid.mode_context_selection_policy.v1',
 'frozen_before_fewshot_outputs':True,
 'purpose':'Compare source-only inference context on unchanged base weights; not more weight training.',
 'development_fixture_sha256':'75eab78085830aa5bf0cf856eb6f70d2630e2407c8143409816dec94d849aaed',
 'baseline_output_sha256':'c97a1d277b7f7eed85e27c1375855fb88a7a5ef1ba7392b7eb35b49b97e97173',
 'source_bank_sha256':sha(p/'source_example_bank.json'),
 'baseline_review_sha256':sha(p/'base_review_notes.py'),
 'selection_groups':{'worked_solution':['answer','student_error','missing_or_contradictory_info'],'hint_level_1':['hint_no_answer']},
 'unvalidated_modes_keep_baseline':['hint_level_2','hint_level_3'],
 'eligibility_per_entire_group':{'minimum_full_task_gain':1,'maximum_baseline_pass_regressions':0,'maximum_new_critical_errors':0,'maximum_new_hint_leaks':0,'retain_all_baseline_answer_passes':True},
 'allowed_routing_inputs':['explicit requested model mode'],
 'forbidden_routing_inputs':['fixture ID','grade','expected answer','oracle','ground-truth guard/student-error category','individual fixture score'],
 'final_test_use':'Once after this development selection; never change weights, context, or selection from final outputs.',
 'corpus_or_model_download_to_pc':False,'new_human_review_claimed':False,'paid_resources':False,
}
qa={'schema':'MathVisionKid.source_context_bank_root_review.v1','source_bank_sha256':policy['source_bank_sha256'],'all_nine_actual_prompts_and_targets_read':True,'original_source_row_and_prompt_target_hashes_present':True,'arithmetic_and_units_correct_in_worked_examples':True,'supplied_student_work_grounded':True,'missing_data_guard_no_fabrication':True,'all_six_hints_withhold_final_answer':True,'source_targets_unchanged':True,'cpu_bank_tests_passed':5,'human_or_teacher_attestation_claimed':False,'limits':'Small fixed source bank, not exhaustive review of original16k or proof of model improvement.'}
for n,v in [('fewshot_selection_policy.json',policy),('source_example_bank_root_review.json',qa)]:
 f=p/n;raw=(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
 if f.exists():assert f.read_bytes()==raw,'Preserve frozen policy/QA'
 else:f.write_bytes(raw)
 print(n,sha(f))
