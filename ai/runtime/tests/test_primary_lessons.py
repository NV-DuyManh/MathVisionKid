"""All lesson families use new model plans; no production example lookup."""
import asyncio
import copy
import json
from unittest.mock import AsyncMock
import pytest
from app.tutoring import lesson
from app.tutoring.lesson import LessonRequest, TurnRequest, start_lesson, answer_lesson
from app.tutoring.service import TutorUnavailable
from _lesson_test_data import step, mock_generation, review_for


def request(source):
    return LessonRequest(owner='pupil', problemText=source, problemConfirmed=True)


def turn(value, answer):
    return answer_lesson(TurnRequest(owner='pupil', sessionId=value.sessionId, revision=value.revision, answer=answer))


@pytest.mark.asyncio
@pytest.mark.parametrize('source,operations,expected,units', [
    ('Tìm một số biết rằng viết thêm chữ số 4 vào bên phải thì số mới hơn số phải tìm 112 đơn vị.', ['10-1','112-4','{s1}/{s0}'], ['9','108','12'], ['phần','','']),
    ('Vườn có 1/4 số cây là táo, 1/2 là xoài, còn lại 12 cây cam. Hỏi có tất cả bao nhiêu cây?', ['1/4+1/2','1-{s0}','12/{s1}'], ['3/4','1/4','48'], ['phần','phần','cây']),
    ('Tổng hai số là 82, hiệu là 14. Tìm số lớn.', ['(82-14)/2','{s0}+14'], ['34','48'], ['','']),
    ('Hình chữ nhật dài 8 cm, rộng 5 cm. Tính diện tích và chu vi.', ['8*5','(8+5)*2'], ['40','26'], ['cm²','cm']),
    ('Có 7 hộp, mỗi hộp 9 viên bi. Cho đi 11 viên. Hỏi còn bao nhiêu viên bi?', ['7*9','{s0}-11'], ['63','52'], ['viên bi','viên bi']),
    ('Có 54 học sinh chia đều vào 6 nhóm. Mỗi nhóm được thêm 2 bạn. Hỏi mỗi nhóm có bao nhiêu bạn?', ['54/6','{s0}+2'], ['9','11'], ['bạn','bạn']),
    ('Tính 5/6 - 1/4.', ['5/6-1/4','{s0}*1'], ['7/12','7/12'], ['','']),
])
async def test_every_source_reaches_model_and_independent_review_unchanged(monkeypatch, source, operations, expected, units):
    multiple = 'diện tích và chu vi' in source
    candidate=dict(topic='Giải theo đúng đề', goal='Tìm đủ đại lượng đề hỏi.',
                   finalAnswerStep=None if multiple else len(operations)-1,
                   steps=[step(title=f'Tìm lượng {name}', expression=expression, unit=unit)
                          for name, expression, unit in zip(['ban đầu','tiếp theo','cần tìm'], operations, units)])
    results=[dict(stepIndex=i, answer=answer, unit=units[i]) for i,answer in enumerate(expected)
             if multiple or i == len(expected)-1]
    cloud=mock_generation(monkeypatch,candidate,results)
    response=await start_lesson(request(source))
    assert cloud.await_count == 2
    generation, verification=cloud.await_args_list
    assert generation.args[0] == lesson.PLAN_PROMPT
    assert json.loads(generation.args[1])['problemText'] == source
    assert set(json.loads(generation.args[1])['givenNumbers'])==lesson.numeric_values(source)
    assert verification.args[0] == lesson.REVIEW_PROMPT
    data=json.loads(verification.args[1])
    assert data['problemText'] == source and data['computedAnswers'] == expected
    assert set(data['givenNumbers'])==lesson.numeric_values(source)
    assert len(data['initialTeaching']) == len(operations)
    assert 'computedAnswers' not in response.model_dump_json()
    assert 'correctChoice' not in response.model_dump_json()
    assert response.conclusion == ''
    assert generation.kwargs['max_output_tokens'] > 1500
    for answer in expected:
        assert 3 <= len(response.step.guidance) <= 6
        assert response.step.solutionSentence.endswith('là:')
        assert turn(response,'999').stepIndex == response.stepIndex
        response=turn(response,answer)
    assert response.status == 'COMPLETE'
    assert response.conclusion == ('' if multiple else f'Đáp số: {expected[-1]}' + (f' {units[-1]}' if units[-1] else '') + '.')


@pytest.mark.asyncio
async def test_same_family_can_have_a_different_model_chosen_plan_and_target(monkeypatch):
    source='Tìm số mới biết rằng viết thêm chữ số 6 vào bên phải số ban đầu thì số mới hơn số ban đầu 537 đơn vị.'
    candidate=dict(topic='Tìm số mới', goal='Tìm số mới thay vì số ban đầu.', finalAnswerStep=2, steps=[
        step(title='Tìm phần giá trị gấp lên', expression='537-6'),
        step(title='Tìm số ban đầu', expression='{s0}/(10-1)'),
        step(title='Tìm số mới', expression='{s1}*10+6'),
    ])
    mock_generation(monkeypatch,candidate,[dict(stepIndex=2, answer='596', unit='')])
    response=await start_lesson(request(source))
    assert response.outline == [item['title'] for item in candidate['steps']]
    for answer in ['531','59','596']:
        response=turn(response,answer)
    assert response.conclusion == 'Đáp số: 596.'


@pytest.mark.asyncio
@pytest.mark.parametrize('source', [
    'Tìm một số biết rằng viết thêm chữ số 6 vào bên phải thì số mới hơn số phải tìm 537 đơn vị.',
    'Vườn có 1/3 số cây là táo, 2/5 là xoài, còn lại 16 cây cam. Hỏi có tất cả bao nhiêu cây?',
    'Hình chữ nhật có chiều dài 12 cm, chiều rộng 5 cm. Tính diện tích.',
])
async def test_provider_failure_never_silently_returns_a_prebuilt_lesson(monkeypatch, source):
    cloud=AsyncMock(side_effect=TutorUnavailable())
    monkeypatch.setattr(lesson,'_generate',cloud)
    lesson._sessions.clear()
    with pytest.raises(TutorUnavailable):
        await start_lesson(request(source))
    assert cloud.await_count == 1 and not lesson._sessions


def candidate():
    return dict(topic='Các nhóm bằng nhau', goal='Tìm số bút trong các hộp.', finalAnswerStep=1, steps=[
        step(title='Chọn phép tính', choices=['Nhân','Cộng'], correctChoice='Nhân'),
        step(title='Tìm số bút tất cả', expression='7*9', unit='bút'),
    ])


@pytest.mark.asyncio
@pytest.mark.parametrize('check', ['sourceFaithful','mathematicsCorrect','answersQuestion','teachingClear'])
async def test_any_failed_semantic_or_teaching_review_rejects_the_plan(monkeypatch, check):
    plan=candidate()
    # The wrong operation still uses only source numbers and computes cleanly.
    # Arithmetic grounding alone MUST NOT approve it.
    plan['steps'][1]['expression']='7+9'
    review=review_for(plan); review[check]=False
    cloud=AsyncMock(side_effect=[plan,review,plan,review]); monkeypatch.setattr(lesson,'_generate',cloud)
    lesson._sessions.clear()
    with pytest.raises(TutorUnavailable):
        await start_lesson(request('Có 7 hộp, mỗi hộp 9 bút. Hỏi có tất cả bao nhiêu bút?'))
    assert cloud.await_count == 4 and not lesson._sessions


@pytest.mark.asyncio
@pytest.mark.parametrize('results', [
    [], [dict(stepIndex=1, answer='16', unit='bút')],
    [dict(stepIndex=0, answer='63', unit='bút')],
    [dict(stepIndex=5, answer='63', unit='bút')],
    [dict(stepIndex=1, answer='63', unit='cm')],
    [dict(stepIndex=1, answer='7*9=63', unit='bút')],
    [dict(stepIndex=1, answer='63', unit='bút')]*2,
])
async def test_independent_results_must_match_the_requested_calculation_and_units(monkeypatch, results):
    plan=candidate(); cloud=AsyncMock(side_effect=[plan,review_for(plan,results)]*2)
    monkeypatch.setattr(lesson,'_generate',cloud)
    with pytest.raises(TutorUnavailable):
        await start_lesson(request('Có 7 hộp, mỗi hộp 9 bút. Hỏi có tất cả bao nhiêu bút?'))


@pytest.mark.asyncio
@pytest.mark.parametrize('mutate', [
    lambda p: p['steps'][1].update(guidance=[]),
    lambda p: p['steps'][1].update(hints=['Chỉ một gợi ý']),
    lambda p: p['steps'][1].update(solutionSentence='Nhân hai số'),
    lambda p: p['steps'][1].update(expression='7*100'),
    lambda p: p['steps'][1].update(guidance=['Kết quả là 63.']*3),
    lambda p: p['steps'][1].update(guidance=['Dùng {s1}.']*3),
    lambda p: p['steps'][1].update(guidance=['Dùng {s0}.']*3),
])
async def test_incomplete_leaking_or_ungrounded_candidate_never_reaches_review(monkeypatch, mutate):
    plan=candidate(); mutate(plan)
    cloud=AsyncMock(return_value=plan); monkeypatch.setattr(lesson,'_generate',cloud)
    with pytest.raises(TutorUnavailable):
        await start_lesson(request('Có 7 hộp, mỗi hộp 9 bút. Hỏi có tất cả bao nhiêu bút?'))
    assert cloud.await_count == 2
    assert all(call.args[0] != lesson.REVIEW_PROMPT for call in cloud.await_args_list)


@pytest.mark.asyncio
async def test_unavailable_or_incomplete_problem_does_not_open_a_session(monkeypatch):
    cloud=AsyncMock(return_value={'unavailable':True}); monkeypatch.setattr(lesson,'_generate',cloud)
    with pytest.raises(TutorUnavailable):
        await start_lesson(request('Tổng hai số là 70. Tìm hai số.'))
    assert cloud.await_count == 1


def test_formula_constants_depend_on_the_actual_source_context():
    assert lesson.formula_constants('Có 7 hộp bút.') == {'1','2'}
    assert '10' in lesson.formula_constants('Viết thêm chữ số 6 vào bên phải.')
    assert '100' in lesson.formula_constants('Tính 25% số học sinh.')
    assert '60' in lesson.formula_constants('Đổi giờ sang phút.')
    assert '100' not in lesson.formula_constants('Tìm số mới bằng cách cộng.')


@pytest.mark.asyncio
async def test_one_content_repair_keeps_original_source_and_only_publishes_reviewed_plan(monkeypatch):
    source='Có 7 hộp, mỗi hộp 9 bút. Hỏi có tất cả bao nhiêu bút?'
    bad=candidate(); bad['steps'][1]['guidance']=[]
    corrected=candidate()
    cloud=AsyncMock(side_effect=[bad,corrected,review_for(corrected)])
    monkeypatch.setattr(lesson,'_generate',cloud)
    response=await start_lesson(request(source))
    assert cloud.await_count == 3
    repair=cloud.await_args_list[1]
    assert repair.args[0].startswith(lesson.REPAIR_PROMPT)
    data=json.loads(repair.args[1])
    assert data['problemText'] == source and data['rejectedCandidate'] == bad
    checked=json.loads(cloud.await_args_list[2].args[1])
    assert 'rejectedCandidate' not in checked and checked['candidate']['steps'][1]['expression']=='7*9'
    assert '63' not in response.model_dump_json(exclude={'sessionId'})


@pytest.mark.asyncio
async def test_reviewer_failure_never_reuses_unreviewed_content_or_opens_a_session(monkeypatch):
    cloud=AsyncMock(side_effect=[candidate(),TutorUnavailable()])
    monkeypatch.setattr(lesson,'_generate',cloud)
    lesson._sessions.clear()
    with pytest.raises(TutorUnavailable):
        await start_lesson(request('Có 7 hộp, mỗi hộp 9 bút. Hỏi có tất cả bao nhiêu bút?'))
    assert cloud.await_count == 2 and not lesson._sessions


def test_division_teaching_may_name_source_digits_but_not_use_them_as_new_operands():
    source=request('Có 126 quyển vở chia đều cho 7 nhóm. Mỗi nhóm được tặng thêm 3 quyển. Hỏi mỗi nhóm có bao nhiêu quyển?')
    plan=lesson.Plan.model_validate(dict(topic='Chia vở',goal='Tìm vở mỗi nhóm.',finalAnswerStep=1,steps=[
        step(title='Tìm số vở được chia',expression='126/7',guidance=[
            'Lấy nhóm chữ số đầu 12 để bắt đầu chia. Hạ chữ số 6 sau khi em đã tự tính thương và phần còn dư.',
            'Đề cho biết tổng số vở được chia đều. Tìm lượng trong một nhóm trước khi cộng phần vở thêm.',
            'Viết câu lời giải nêu số vở mỗi nhóm nhận được. Ghi phép chia và kết quả em tự tính, kèm đơn vị.']),
        step(title='Tìm số vở có tất cả',expression='{s0}+3'),
    ]))
    lesson.validate_plan(plan,source)
    plan.steps[0].expression='12/7'
    with pytest.raises(ValueError,match='Derived literal operand'):
        lesson.validate_plan(plan,source)


@pytest.mark.asyncio
async def test_generation_is_bounded_before_session_publication(monkeypatch):
    original_wait=asyncio.wait_for
    async def deadline(awaitable, timeout):
        assert timeout == 38.0
        return await original_wait(awaitable,timeout=0.001)
    async def slow(*args,**kwargs):
        await asyncio.sleep(1)
    monkeypatch.setattr(lesson,'_generate',slow)
    monkeypatch.setattr(lesson.asyncio,'wait_for',deadline)
    with pytest.raises(TutorUnavailable):
        await start_lesson(request('Có 7 hộp, mỗi hộp 9 bút. Hỏi có tất cả bao nhiêu bút?'))


@pytest.mark.asyncio
async def test_current_worked_calculation_opens_only_on_deep_help_or_completion(monkeypatch):
    source='Có 7 hộp, mỗi hộp 9 viên bi. Cho đi 11 viên. Hỏi còn bao nhiêu viên bi?'
    worked='Tính bằng cộng lặp: 9 + 9 + 9 + 9 + 9 + 9 + 9 = 63. Vậy số viên bi ban đầu là 63 viên bi.'
    first=step(title='Tìm số bi ban đầu',expression='7*9',unit='viên bi')
    first['guidance'].append(worked)
    first['hints'][1]=worked
    plan=dict(topic='Gộp nhóm rồi bớt đi',goal='Tìm số viên bi còn lại.',finalAnswerStep=1,
              steps=[first,step(title='Tìm số bi còn lại',expression='{s0}-11',unit='viên bi')])
    cloud=mock_generation(monkeypatch,plan)
    value=await start_lesson(request(source))
    assert worked not in value.step.guidance and '63' not in value.model_dump_json(exclude={'sessionId'})
    reviewed=json.loads(cloud.await_args_list[1].args[1])
    initial=reviewed['initialTeaching']
    assert worked not in initial[0]
    assert worked in reviewed['workedTeaching'][0]
    assert 'guidance' not in reviewed['candidate']['steps'][0]
    assert worked not in reviewed['workedTeaching'][1]
    value=answer_lesson(TurnRequest(owner='pupil',sessionId=value.sessionId,revision=value.revision,hint=True))
    assert worked not in value.step.guidance and '63' not in value.feedback
    value=answer_lesson(TurnRequest(owner='pupil',sessionId=value.sessionId,revision=value.revision,hint=True))
    assert worked in value.step.guidance and value.stepIndex==0
    assert '52' not in value.model_dump_json(exclude={'sessionId'})
    assert turn(value,'52').stepIndex==0
    value=turn(value,'63')
    assert worked in value.completed[0].guidance
    assert value.stepIndex==1 and '52' not in value.model_dump_json(exclude={'sessionId'})


def test_worked_help_must_never_contain_a_future_answer():
    value=lesson.Plan.model_validate(dict(topic='Gộp nhóm',goal='Tìm số còn lại.',finalAnswerStep=1,steps=[
        step(title='Tìm số ban đầu',expression='7*9',guidance=[
            'Đề cho các nhóm bằng nhau, cần tìm tổng lượng trước khi bớt đi phần đã cho.',
            'Tính số ban đầu rồi trừ lượng cho đi. Sau bước tiếp theo, còn lại 52 viên bi.',
            'Viết câu lời giải nêu số viên bi ban đầu, ghi phép tính và đơn vị.']),
        step(title='Tìm số còn lại',expression='{s0}-11'),
    ]))
    with pytest.raises(ValueError,match='Future answer'):
        lesson.validate_plan(value,request('Có 7 hộp, mỗi hộp 9 viên. Cho đi 11 viên. Hỏi còn bao nhiêu viên?'))


@pytest.mark.parametrize('ending', ['.', ',', ')', '。'])
def test_future_answer_is_blocked_even_before_sentence_punctuation(ending):
    value=lesson.Plan.model_validate(dict(topic='Gộp nhóm',goal='Tìm số còn lại.',finalAnswerStep=1,steps=[
        step(title='Tìm số ban đầu',expression='7*9',guidance=[
            'Đề cho các nhóm bằng nhau, cần tìm tổng lượng trước khi bớt đi phần đã cho.',
            'Sau bước tiếp theo, còn lại 52'+ending,
            'Viết câu lời giải nêu số viên bi ban đầu, ghi phép tính và đơn vị.']),
        step(title='Tìm số còn lại',expression='{s0}-11'),
    ]))
    with pytest.raises(ValueError,match='Future answer'):
        lesson.validate_plan(value,request('Có 7 hộp, mỗi hộp 9 viên. Cho đi 11 viên. Hỏi còn bao nhiêu viên?'))


def test_literal_prior_fraction_is_normalized_without_swallowing_subtraction():
    value=lesson.Plan.model_validate(dict(topic='Phân số',goal='Tìm phần còn lại.',finalAnswerStep=1,steps=[
        step(title='Tính phần đã có',expression='1/3+2/5'),
        step(title='Tính phần còn lại',expression='1-11/15'),
    ]))
    lesson.validate_plan(value,request('Có 1/3 phần táo và 2/5 phần xoài. Tìm phần còn lại.'))
    assert value.steps[1].expression=='1-{s0}'
    assert lesson.calculate_exact(lesson.expression_at(value.steps[1],['11/15']))==lesson.Fraction(4,15)


@pytest.mark.asyncio
async def test_review_rejection_can_be_rewritten_once_with_private_feedback(monkeypatch):
    rejected=candidate(); rejected['steps'][1]['expression']='7+9'
    bad_review=review_for(rejected); bad_review.update(mathematicsCorrect=False,
        results=[],issues=['Each box has equal contents: addition does not combine all boxes.'])
    corrected=candidate()
    cloud=AsyncMock(side_effect=[rejected,bad_review,corrected,review_for(corrected)])
    monkeypatch.setattr(lesson,'_generate',cloud)
    value=await start_lesson(request('Có 7 hộp, mỗi hộp 9 bút. Hỏi có tất cả bao nhiêu bút?'))
    assert cloud.await_count==4
    assert bad_review['issues'][0] not in cloud.await_args_list[2].args[0]
    assert bad_review['issues'][0] in json.loads(cloud.await_args_list[2].args[1])['validationIssue']
    assert bad_review['issues'][0] not in value.model_dump_json()
    assert json.loads(cloud.await_args_list[3].args[1])['candidate']['steps'][1]['expression']=='7*9'


def test_review_feedback_is_length_bounded():
    from pydantic import ValidationError
    value=review_for(candidate()); value['issues']=['x'*221]
    with pytest.raises(ValidationError):
        lesson.PlanReview.model_validate(value)


@pytest.mark.asyncio
async def test_json_plan_is_locally_validated_and_reviewed_and_refusal_remains_bounded(monkeypatch):
    plan=candidate()
    cloud=AsyncMock(side_effect=[{'lesson':plan},review_for(plan)])
    monkeypatch.setattr(lesson,'_generate',cloud)
    value=await start_lesson(request('Có 7 hộp, mỗi hộp 9 bút. Hỏi có tất cả bao nhiêu bút?'))
    assert value.stepIndex==0
    assert cloud.await_args_list[0].kwargs['response_schema']==lesson.PLANNING_SCHEMA
    assert cloud.await_args_list[1].kwargs['response_schema']==lesson.REVIEW_SCHEMA
    assert all(call.kwargs['reasoning'] is True for call in cloud.await_args_list)
    cloud=AsyncMock(return_value={'lesson':None})
    monkeypatch.setattr(lesson,'_generate',cloud)
    with pytest.raises(TutorUnavailable):
        await start_lesson(request('Tổng hai số là 70. Tìm hai số.'))
    assert cloud.await_count==2
    assert all(call.kwargs['response_schema']==lesson.PLANNING_SCHEMA for call in cloud.await_args_list)


@pytest.mark.asyncio
@pytest.mark.parametrize('can_solve,steps', [(False, []), ('true', []), (True, [])])
async def test_flat_draft_refusal_and_invalid_ready_shape_never_open_a_session(monkeypatch, can_solve, steps):
    draft=dict(canSolve=can_solve,topic='Kiểm tra dữ kiện',goal='Cần thêm quan hệ giữa hai số.',
               steps=steps,finalAnswerStep=None)
    cloud=AsyncMock(return_value=draft)
    monkeypatch.setattr(lesson,'_generate',cloud)
    lesson._sessions.clear()
    with pytest.raises(TutorUnavailable):
        await start_lesson(request('Tổng hai số là 70. Tìm hai số.'))
    assert cloud.await_count==2 and not lesson._sessions
    assert all(call.args[0]!=lesson.REVIEW_PROMPT for call in cloud.await_args_list)


@pytest.mark.asyncio
async def test_flat_ready_draft_still_requires_independent_result_review(monkeypatch):
    plan=candidate()
    draft={**plan,'canSolve':True}
    cloud=AsyncMock(side_effect=[draft,review_for(plan)])
    monkeypatch.setattr(lesson,'_generate',cloud)
    value=await start_lesson(request('Có 7 hộp, mỗi hộp 9 bút. Hỏi có tất cả bao nhiêu bút?'))
    assert value.stepIndex==0 and value.conclusion==''
    assert 'canSolve' not in value.model_dump_json()
    assert cloud.await_args_list[1].args[0]==lesson.REVIEW_PROMPT


@pytest.mark.asyncio
@pytest.mark.parametrize('indexes', [[0,1], [1,0], [0,2], [2], [-1], [True]])
async def test_draft_work_references_preserve_exact_source_rows_and_reject_invalid_indexes(monkeypatch, indexes):
    source='Có 7 hộp, mỗi hộp 9 bút. Hỏi có tất cả bao nhiêu bút?'
    work='Số bút có tất cả là:\n7 × 9 = 62 (bút)'
    plan=candidate(); draft={**copy.deepcopy(plan),'canSolve':True}
    draft['steps'][1]['workLineIndexes']=indexes
    reviewed=copy.deepcopy(plan); reviewed['steps'][1]['workExcerpt']=work
    cloud=AsyncMock(side_effect=[draft,review_for(reviewed)] if indexes==[0,1] else [draft,draft])
    monkeypatch.setattr(lesson,'_generate',cloud)
    if indexes==[0,1]:
        value=await start_lesson(LessonRequest(owner='pupil',problemText=source,problemConfirmed=True,
            workText=work,workConfirmed=True))
        assert json.loads(cloud.await_args_list[0].args[1])['workLines']==[
            dict(index=i,text=line) for i,line in enumerate(work.splitlines())]
        data=json.loads(cloud.await_args_list[1].args[1])
        assert data['candidate']['steps'][1]['workExcerpt']==work
        assert 'workLineIndexes' not in data['candidate']['steps'][1]
        assert 'workText' not in data and 'workLines' not in data
        value=turn(value,value.step.choices[0]); value=turn(value,'63')
        assert 'trong ảnh chưa khớp' in value.feedback
    else:
        with pytest.raises(TutorUnavailable):
            await start_lesson(LessonRequest(owner='pupil',problemText=source,problemConfirmed=True,
                workText=work,workConfirmed=True))
        assert all(call.args[0]!=lesson.REVIEW_PROMPT for call in cloud.await_args_list)


@pytest.mark.asyncio
async def test_a_false_initial_refusal_is_reconsidered_once_and_still_independently_reviewed(monkeypatch):
    plan=candidate()
    cloud=AsyncMock(side_effect=[{'lesson':None}, {'lesson':plan}, review_for(plan)])
    monkeypatch.setattr(lesson,'_generate',cloud)
    value=await start_lesson(request('Có 7 hộp, mỗi hộp 9 bút. Hỏi có tất cả bao nhiêu bút?'))
    assert cloud.await_count==3
    reconsidered=json.loads(cloud.await_args_list[1].args[1])
    assert reconsidered['problemText']=='Có 7 hộp, mỗi hộp 9 bút. Hỏi có tất cả bao nhiêu bút?'
    assert reconsidered['rejectedCandidate']=={'lesson':None}
    assert cloud.await_args_list[-1].args[0]==lesson.REVIEW_PROMPT
    assert value.stepIndex==0 and '63' not in value.model_dump_json(exclude={'sessionId'})


@pytest.mark.asyncio
async def test_worked_help_cannot_replace_teaching_before_the_pupil_answers(monkeypatch):
    plan=candidate()
    plan['steps'][1]['guidance']=[
        'Đọc lại dữ kiện của đề và xác định tổng số bút trong các hộp. Các hộp có số bút bằng nhau nên cần gộp các nhóm để tìm tổng.',
        'Tính mẫu của bước này: 7 × 9 = 63. Gộp các nhóm bằng nhau được 63 bút, rồi ghi phép tính và đơn vị bút vào vở.',
        'Viết câu lời giải và phép tính: Số bút có tất cả là: 7 × 9 = 63 (bút). Nhìn lại phép tính để kiểm tra đã gộp đủ các nhóm.',
    ]
    cloud=AsyncMock(return_value=plan)
    monkeypatch.setattr(lesson,'_generate',cloud)
    with pytest.raises(TutorUnavailable):
        await start_lesson(request('Có 7 hộp, mỗi hộp 9 bút. Hỏi có tất cả bao nhiêu bút?'))
    assert cloud.await_count==2
    assert all(call.args[0]!=lesson.REVIEW_PROMPT for call in cloud.await_args_list)
    issue=json.loads(cloud.await_args_list[1].args[1])['validationIssue']
    assert 'INITIAL guidance' in issue


def test_outline_cannot_reveal_the_result_of_an_earlier_unanswered_step():
    value=lesson.Plan.model_validate(dict(topic='Số bút',goal='Tìm số bút còn lại.',finalAnswerStep=1,steps=[
        step(title='Tìm số bút có tất cả',expression='12+5'),
        step(title='Lấy 17 bút bớt đi phần cho',expression='{s0}-2'),
    ]))
    with pytest.raises(ValueError,match='outline'):
        lesson.validate_plan(value,request('Có 12 bút, thêm 5 bút rồi cho 2 bút. Hỏi còn bao nhiêu bút?'))


@pytest.mark.parametrize('text',['Expo','Metro','LAN','mạng lan','network lan','Spring Boot','FastAPI','MinIO','Redis','PostgreSQL','student@gmail.com'])
def test_student_teaching_cannot_publish_developer_details_or_accounts(text):
    with pytest.raises(ValueError,match='Unsafe public lesson'):
        lesson.safe_public('Mở '+text+' để tiếp tục.')


@pytest.mark.parametrize('text', [
    'Khi viết thêm chữ số, số cũ lớn gấp 10 lần rồi thêm chữ số mới.',
    'Lan có 7 viên bi, Lân có 9 viên bi. Tìm tổng số viên bi của hai bạn.',
    'Số cây hoa lan bằng 1/3 số cây trong vườn.',
])
def test_student_teaching_preserves_vietnamese_words_and_names(text):
    lesson.safe_public(text)


@pytest.mark.asyncio
@pytest.mark.parametrize('leaks_future', [False, True])
async def test_paragraph_string_guidance_keeps_all_teaching_and_answer_guards(monkeypatch, leaks_future):
    plan=candidate()
    for item in plan['steps']:
        item['guidance']='\n\n'.join(item['guidance'])
    if leaks_future:
        plan['steps'][0]['guidance']+='\n\nSau khi làm bước tiếp theo, kết quả sẽ là 63 bút.'
        cloud=AsyncMock(return_value=plan)
        monkeypatch.setattr(lesson,'_generate',cloud)
        with pytest.raises(TutorUnavailable):
            await start_lesson(request('Có 7 hộp, mỗi hộp 9 bút. Hỏi có tất cả bao nhiêu bút?'))
        assert all(call.args[0]!=lesson.REVIEW_PROMPT for call in cloud.await_args_list)
    else:
        cloud=mock_generation(monkeypatch,plan)
        value=await start_lesson(request('Có 7 hộp, mỗi hộp 9 bút. Hỏi có tất cả bao nhiêu bút?'))
        assert value.step.guidance==plan['steps'][0]['guidance'].split('\n\n')
        reviewed=json.loads(cloud.await_args_list[1].args[1])
        assert reviewed['initialTeaching'][0]==value.step.guidance


def test_paragraph_string_never_silently_discards_excess_teaching():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        lesson.Step.model_validate(step(expression='7*9',guidance='\n\n'.join(['Một đoạn hướng dẫn.']*7)))
