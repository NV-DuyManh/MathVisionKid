import copy
import json
from pathlib import Path

import pytest

import teacher_multitask_v4 as mixed
import train_teacher_math_v3 as numeric
from test_train_teacher_math_v3 import example, Tokenizer


def concept(mode='worked_solution'):
    row={'sample_id':'concept_one','grade':4,'mode':mode,'source':{'source_id':'official_annex_outcome'},
        'license':'original teacher text','human_verified':False,'pedagogy_teacher_reviewed':False,
        'split_group_id':'current_legacy_same_group','numeric_checks':[{'expression':'1/2+1/4','expected_result':'3/4'}],
        'messages':[{'role':'system','content':'Hướng dẫn toán tiểu học ngắn.'},
                    {'role':'user','content':'Giải thích quy đồng phân số và cho ví dụ đã giải.'},
                    {'role':'assistant','content':'Đưa hai phân số về cùng mẫu. Ví dụ: 1/2 + 1/4 = 3/4.'}]}
    if mode=='hint':
        row['messages'][1]['content']='Chỉ gợi ý cách cộng phân số, đừng giải.'
        row['messages'][2]['content']='Em có thể đưa hai phân số về cùng mẫu số bằng cách nào?'
        row['numeric_checks']=[]
    return row


def concept_eval(mode='worked_solution'):
    return {'sample_id':'concept_eval_new','grade':4,'mode':mode,
        'messages':[{'role':'system','content':'Giải thích ngắn.'},
                    {'role':'user','content':'Vì sao cần quy đồng khi cộng hai phân số khác mẫu?'}],
        'reference_answer':'Giữ giá trị, đưa về cùng mẫu rồi cộng các tử.',
        'expected_key_claims':[{'claim_id':'common','any_of':['cùng mẫu','chung mẫu']},
                               {'claim_id':'numerator','any_of':['cộng các tử','cộng tử số']}],
        'rejected_claims':['cộng các mẫu số'], 'require_image_confirmation':False}


def test_mixed_input_does_not_inject_numeric_target_or_concept_reference():
    item={'sample_id':'numeric:one','task_kind':'numeric','row':example()}
    assert mixed.mixed_messages(item)==numeric.messages(item['row'])
    concept_item={'sample_id':'concept:one','task_kind':'concept','row':concept()}
    messages=mixed.mixed_messages(concept_item)
    assert len(messages)==2 and [message['role'] for message in messages]==['system','user']
    assert '3/4' not in json.dumps(messages,ensure_ascii=False)
    assert concept_item['row']['messages'][-1]['role']=='assistant'


@pytest.mark.parametrize('task_kind',['numeric','concept'])
def test_explicit_mixed_completion_loss_masks_and_actual_eos(task_kind):
    row=example() if task_kind=='numeric' else concept()
    item={'sample_id':task_kind+':one','task_kind':task_kind,'row':row}
    encoded=mixed.mixed_serialize(item,Tokenizer(),10000)
    assert encoded['labels'][:encoded['prefix_length']]==[-100]*encoded['prefix_length']
    assert encoded['labels'][encoded['prefix_length']:]==encoded['input_ids'][encoded['prefix_length']:]
    assert encoded['input_ids'][-1]==Tokenizer.eos_token_id
    assert encoded['task_kind']==task_kind and encoded['source_sample_id']==row['sample_id']
    with pytest.raises(ValueError,match='No silent truncation'):
        mixed.mixed_serialize(item,Tokenizer(),20)


def test_concepts_remain_free_prose_not_numeric_json():
    item={'sample_id':'concept:one','task_kind':'concept','row':concept()}
    tokenizer=Tokenizer();encoded=mixed.mixed_serialize(item,tokenizer,10000)
    target=mixed.concept_target(item['row'])
    assert not target.startswith('{') and 'Ví dụ' in target
    assert encoded['completion_length']==len(tokenizer.encode(target+tokenizer.eos_token))


def test_repeat_is_explicit_with_new_instance_ids_and_original_source_identity():
    instances=mixed.build_training([example()],[concept()],3)
    assert len(instances)==4 and len({row['sample_id'] for row in instances})==4
    assert len({row['row']['sample_id'] for row in instances if row['task_kind']=='concept'})==1
    assert [row['repeat_index'] for row in instances if row['task_kind']=='concept']==[0,1,2]


def test_teacher_concept_source_and_numeric_examples_verified_only_where_declared():
    mixed.validate_concept_training(concept())
    wrong=concept();wrong['numeric_checks'][0]['expected_result']='1'
    with pytest.raises(ValueError,match='numeric example'):mixed.validate_concept_training(wrong)
    wrong=concept();wrong['human_verified']=True
    with pytest.raises(ValueError,match='teacher-certified'):mixed.validate_concept_training(wrong)
    wrong=concept();wrong.pop('license')
    with pytest.raises(ValueError,match='source/license'):mixed.validate_concept_training(wrong)


def test_concept_teacher_hint_one_question_and_no_computed_answer():
    mixed.validate_concept_training(concept('hint'))
    wrong=concept('hint');wrong['messages'][-1]['content']='Đáp số là 3/4. Em hiểu chưa?'
    with pytest.raises(ValueError,match='reveals'):mixed.validate_concept_training(wrong)


def test_claim_screen_accepts_explicit_alternatives_rejects_wrong_phrase_but_never_certifies():
    row=concept_eval()
    score=mixed.score_concept(row,'Đưa về chung mẫu rồi cộng tử số.')
    assert score['screened_correct'] and score['matched_claim_groups']==2
    assert score['semantic_correctness_verified'] is False and score['pedagogy_teacher_reviewed'] is False
    wrong=mixed.score_concept(row,'Đưa về cùng mẫu rồi cộng các tử và cộng các mẫu số.')
    assert wrong['forbidden_claim_hit'] and not wrong['screened_correct']
    # A valid but unlisted synonym may miss this finite lexical screening.
    assert not mixed.score_concept(row,'Biến đổi mẫu chung rồi cộng phần ở trên.')['screened_correct']


def test_concept_reference_answer_not_used_as_generated_prediction():
    row=concept_eval();row['reference_answer']='This private reference cannot leak into input'
    assert 'private' not in json.dumps(mixed.concept_messages(row))
    assert not mixed.score_concept(row,'Tôi không biết.')['screened_correct']


def test_concept_screen_truncation_and_unfinished_thought_fail():
    row=concept_eval()
    assert not mixed.score_concept(row,'cùng mẫu cộng các tử',truncated=True)['screened_correct']
    assert not mixed.score_concept(row,'<think>cùng mẫu cộng các tử</think>')['screened_correct']


def test_positive_claim_negation_and_surface_equation_errors_do_not_pass_screen():
    row=concept_eval()
    assert not mixed.score_concept(row,'Không cần cùng mẫu; chỉ cộng các tử.')['screened_correct']
    score=mixed.score_concept(row,'Đưa về cùng mẫu rồi cộng các tử. 1/2 + 1/4 = 1.')
    assert not score['screened_correct'] and not score['displayed_arithmetic_valid']
    score=mixed.score_concept(row,'Đưa về cùng mẫu rồi cộng các tử. 1/2 + 1/4 = 3/4.')
    assert score['screened_correct'] and score['displayed_equation_checks'][0]['passed']


def test_missing_image_requires_confirmation_and_no_invented_measurement():
    row=concept_eval();row.update(mode='hint',require_image_confirmation=True,
        expected_key_claims=[{'claim_id':'request','any_of':['hình','ảnh']}])
    assert mixed.score_concept(row,'Em có thể gửi hình để mình xác định các kích thước chưa?')['screened_correct']
    assert not mixed.score_concept(row,'Hình này có cạnh 12 cm, em đồng ý chưa?')['screened_correct']


def summary(correct=10):
    value={'answer_and_unit_correct':correct,'solution_verified':correct,'hint_safe':4,
           'hint_reference_match':3,'guard_correct':3}
    value['per_grade']={'4':dict(value)}
    return value


def raw_summary(correct=10):
    return {'numeric_correct':correct,'answer_unit_correct':correct,
            'per_grade':{'4':{'numeric_correct':correct,'answer_unit_correct':correct}}}


def test_selection_requires_raw_numeric_retention_and_actual_semantic_review():
    base=summary(10);candidate=summary(11);parent=summary(11)
    b={'screened_correct':5,'hint_structurally_safe':3,'forbidden_claim_hits':0}
    c={'screened_correct':6,'hint_structurally_safe':3,'forbidden_claim_hits':0}
    raw=raw_summary(11)
    review={'passed':True,'baseline':{'acceptable':5},'candidate':{'acceptable':6}}
    assert mixed.select(base,candidate,b,c,parent,raw,raw,raw,review)['selected']=='adapter'
    assert mixed.select(base,candidate,b,c,parent,raw,raw,raw)['selected']=='base'
    assert mixed.select(base,candidate,b,c,parent,raw_summary(12),raw,raw,review)['selected']=='base'
    parent=summary(12)
    assert mixed.select(base,candidate,b,c,parent,raw,raw,raw_summary(12),review)['selected']=='base'
    review['passed']=False
    assert mixed.select(base,candidate,b,c,summary(11),raw,raw,raw,review)['selected']=='base'


def test_reference_path_and_hint_phrasing_are_advisory_under_declared_v4_gates():
    base=summary();candidate=summary(11);candidate['per_grade']['4']['hint_reference_match']=2
    candidate['solution_verified']=1; candidate['per_grade']['4']['solution_verified']=1
    b={'screened_correct':5,'hint_structurally_safe':3,'forbidden_claim_hits':0}
    c={'screened_correct':6,'hint_structurally_safe':3,'forbidden_claim_hits':0}
    semantic={'passed':True,'baseline':{'acceptable':5},'candidate':{'acceptable':6}}
    report=mixed.select(base,candidate,b,c,base,raw_summary(10),raw_summary(11),raw_summary(10),semantic)
    assert report['selected']=='adapter'
    assert report['reference_hint_match_advisory'] and report['reference_solution_path_advisory']
    # The immutable old selection still rejects this exact-path regression.
    assert numeric.select_candidate(base,candidate)['selected']=='base'


def test_config_fresh_base_only_and_explicit_replay_balance(tmp_path):
    path=tmp_path/'config.json';path.write_text(json.dumps({'run_id':'new_v4'}))
    config=mixed.load_config(path)
    assert config['require_v3_audit'] and config['concept_repeat']==1 and config['model_id']=='Qwen/Qwen3-1.7B'
    path.write_text(json.dumps({'run_id':'new_v4','adapter_path':'partial_v3'}))
    with pytest.raises(ValueError,match='fresh pinned base'):mixed.load_config(path)


def test_prepare_binds_exact_numeric_system_and_rejects_train_validation_question_overlap(tmp_path):
    import teacher_math_data_v3
    data=tmp_path/'data';data.mkdir()
    nr=example();nv=example();nv['sample_id']='numeric_val';nv['problem']='Đề kiểm định riêng: '+nv['problem']
    sources={'numeric_train':[nr],'numeric_val':[nv],'concept_train':[concept()],'concept_val':[concept_eval()]}
    for name,rows in sources.items():(data/(name+'.jsonl')).write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows),encoding='utf-8')
    config_path=tmp_path/'cfg.json';config_path.write_text(json.dumps({'run_id':'new','require_v3_audit':False}))
    config=mixed.load_config(config_path)
    _,run,datasets,instances,expanded=mixed.prepare(tmp_path,config)
    assert numeric.SYSTEM==teacher_math_data_v3.SYSTEM and len(instances)==2
    assert expanded['source_hashes']['train_teacher_math_v3.py']
    same=concept_eval();same['messages'][1]['content']=concept()['messages'][1]['content']
    (data/'concept_val.jsonl').write_text(json.dumps(same,ensure_ascii=False)+'\n',encoding='utf-8')
    with pytest.raises(ValueError,match='appears in training'):mixed.prepare(tmp_path,config)


def test_core_v3_audit_required_before_v4_authorization(tmp_path):
    data=tmp_path/'data';data.mkdir()
    nv=example();nv['sample_id']='numeric_val';nv['problem']='Đề kiểm định riêng: '+nv['problem']
    for name,values in {'numeric_train':[example()],'numeric_val':[nv],'concept_train':[concept()],'concept_val':[concept_eval()]}.items():
        (data/(name+'.jsonl')).write_text(''.join(json.dumps(row)+'\n' for row in values))
    path=tmp_path/'cfg.json';path.write_text(json.dumps({'run_id':'new'}))
    with pytest.raises(ValueError,match='completed audited v3'):mixed.prepare(tmp_path,mixed.load_config(path))


def test_import_no_eager_torch_dependency():
    assert 'torch' not in mixed.__dict__


def test_number_substrings_and_swapped_label_bindings_fail_screen():
    row=concept_eval();row['expected_key_claims']=[{'any_of':['43']}]
    assert not mixed.score_concept(row,'Đáp số là 143.')['screened_correct']
    assert mixed.score_concept(row,'Đáp số là 43.')['screened_correct']
    row.update(expected_key_claims=[{'any_of':['thương']}],expected_numeric_bindings=[
        {'label':'thương','expected_value':'5'},{'label':'dư','expected_value':'3'}])
    assert mixed.score_concept(row,'Thương 5, dư 3.')['screened_correct']
    assert not mixed.score_concept(row,'Thương 5, dư 3; kết luận thương 3, dư 5.')['screened_correct']


def test_parenthesized_expression_is_checked_as_whole_not_suffix():
    checks=mixed.displayed_equations('Chu vi: (8 + 3) × 2 = 22 cm; trung bình (9 + 12 + 15) : 3 = 12.')
    assert len(checks)==2 and all(item['passed'] for item in checks)
    assert checks[0]['expressions'][0]=='(8 + 3) * 2'
    assert not mixed.displayed_equations('(8 + 3) × 2 = 23')[0]['passed']


def test_all_current_concept_references_parse_without_false_arithmetic_failure():
    path=Path(__file__).with_name('data')/'teacher_math_v3'/'concept_validation_v4.jsonl'
    rows=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
    assert len(rows)==30
    for row in rows:
        result=mixed.score_concept(row,row['reference_answer'])
        assert result['screened_correct'],row['sample_id']
        assert result['semantic_correctness_verified'] is False
