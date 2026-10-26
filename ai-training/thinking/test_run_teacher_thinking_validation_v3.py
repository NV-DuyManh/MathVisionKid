import copy
from run_teacher_thinking_validation_v3 import nonregression


def reference():
    return {'numeric_correct':10,'answer_unit_correct':8,
        'per_grade':{'1':{'numeric_correct':5,'answer_unit_correct':4},
                     '3':{'numeric_correct':5,'answer_unit_correct':4}}}


def test_better_units_cannot_hide_loss_of_arithmetic():
    base=reference();candidate=copy.deepcopy(base)
    candidate.update(numeric_correct=9,answer_unit_correct=9)
    assert not nonregression(base,candidate)


def test_overall_improvement_cannot_hide_grade_regression():
    base=reference();candidate=copy.deepcopy(base)
    candidate.update(numeric_correct=12,answer_unit_correct=10)
    candidate['per_grade']['3']['numeric_correct']=4
    assert not nonregression(base,candidate)


def test_same_or_better_each_generated_number_and_unit_passes():
    base=reference();candidate=copy.deepcopy(base)
    assert nonregression(base,candidate)
    candidate['answer_unit_correct']=9
    candidate['per_grade']['3']['answer_unit_correct']=5
    assert nonregression(base,candidate)
