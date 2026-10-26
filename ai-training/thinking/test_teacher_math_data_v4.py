"""Independent target integrity and adversarial tests for fresh V4 teacher data."""
import copy
from fractions import Fraction
import json
from pathlib import Path
import random

import pytest
import teacher_math_data_v4 as data
import teacher_math_data_v3 as frozen


def row(topic,values,grade=None,mode="worked_solution",observed=None):
    t=data.LOOKUP[topic]
    if grade is not None:t=data.replace(t,grade=grade)
    return data.make_row(t,"train",0,{k:Fraction(v) for k,v in values.items()},mode,observed)


@pytest.mark.parametrize("a,b,symbol",[(999999,1,"+"),(0,0,"+"),(8967,764,"+"),(100000,1,"-"),(100001,9999,"-"),(40000,39679,"-"),(1,1,"-"),(0,0,"-")])
def test_independent_column_place_values(a,b,symbol):
    trace=data.column_trace(a,b,symbol)
    result=a+b if symbol=="+" else a-b
    for state in trace:
        assert state["written"]==(result//10**state["column"])%10
        if "carry_only" not in state:
            if symbol=="+":
                # Independent prefix total measures carry into a column.
                column=state["column"]
                incoming=((a%10**column)+(b%10**column))//10**column if column else 0
                assert state["incoming_carry"]==incoming
                assert state["outgoing_carry"]==state["total"]//10
            else:
                assert state["left_after"]-state["right"]==state["written"]
                before=sum(d*10**i for i,d in enumerate(state["digits_before"]))
                after=sum(d*10**i for i,d in enumerate(state["digits_after"]))
                assert before==after, "Regrouping must preserve the original minuend value."
                if state["donor_column"] is not None:
                    assert state["digits_after"][state["donor_column"]]==state["digits_before"][state["donor_column"]]-1
                    assert all(state["digits_after"][j]==9 for j in range(state["column"]+1,state["donor_column"]))
    assert sum(s["written"]*10**s["column"] for s in trace)==result


def test_column_randomized_against_integer_arithmetic():
    rng=random.Random(45691)
    for _ in range(500):
        a,b=rng.randint(0,999999),rng.randint(0,999999)
        test_independent_column_place_values(a,b,"+")
        test_independent_column_place_values(max(a,b),min(a,b),"-")


def test_borrow_instruction_does_not_invent_student_marks():
    r=row("vertical_subtract",{"a":70000,"b":69387},grade=5,observed="623")
    assert data.validate_training_row(r)
    assert "chưa có dấu nhớ" in r["target"]["steps"][0]["explanation"]
    assert r["observed_work_verbatim"]=="623"
    assert r["target"]["answer"]=="613"
    assert "các hàng 0" in r["target"]["steps"][0]["explanation"]
    hint=row("vertical_subtract",{"a":70000,"b":69387},grade=5,mode="hint",observed="623")
    assert "hàng chục" in hint["target"]["hint"]
    assert "613" not in hint["target"]["hint"]


def test_fraction_integer_input_keeps_explicit_denominator():
    r=row("fraction_divide",{"a":Fraction(8,1),"b":Fraction(3,7)})
    assert "8/1" in r["problem"] and "3/7" in r["problem"]
    assert r["target"]["steps"][0]["result"]=="7/3"
    assert r["target"]["steps"][1]["expression"]=="8*(7/3)"
    assert Fraction(r["target"]["answer"])==Fraction(56,3)
    assert data.validate_training_row(r)


@pytest.mark.parametrize("topic,answer",[("fraction_add",Fraction(11,6)),("fraction_subtract",Fraction(5,6)),("fraction_multiply",Fraction(2,3)),("fraction_divide",Fraction(8,3))])
def test_fraction_computation_and_explanation(topic,answer):
    r=row(topic,{"a":Fraction(4,3),"b":Fraction(1,2)})
    assert Fraction(r["target"]["answer"])==answer
    if topic in ("fraction_add","fraction_subtract"):assert "ước chung lớn nhất" in r["target"]["steps"][0]["explanation"]
    if topic=="fraction_divide":assert "Đảo số chia 1/2 thành 2/1" in r["target"]["steps"][0]["explanation"]
    # Test inputs with nonmultiple denominators are mathematical, but intentionally outside g4 current training contract.
    if topic in ("fraction_add","fraction_subtract"):
        with pytest.raises(ValueError,match="DENOMINATOR"):data.validate_training_row(r)
    else:assert data.validate_training_row(r)


def test_remainder_is_not_quotient_or_whole_division_result():
    r=row("division_remainder",{"a":937,"b":8})
    assert r["target"]["answer"]=="1"
    assert r["target"]["steps"][0]["expression"]=="117*8"
    assert r["target"]["steps"][0]["result"]=="936"
    assert r["target"]["steps"][1]["expression"]=="937-936"
    assert r["target"]["steps"][1]["result"]=="1"
    assert data.validate_training_row(r)


def test_total_with_extra_rest_vs_rest_inside_total():
    total=row("hours_minutes",{"a":7,"b":23})
    active=row("hours_minutes_active",{"a":7,"b":23})
    assert total["target"]["answer"]=="443"
    assert active["target"]["answer"]=="397"
    assert "cộng thời gian hoạt động với thời gian nghỉ" in data.LOOKUP["hours_minutes"].hint
    assert "đã nằm trong tổng" in data.LOOKUP["hours_minutes_active"].hint
    assert total["target"]["steps"][1]["expression"]=="420+23"
    assert active["target"]["steps"][1]["expression"]=="420-23"


def test_sequence_rule_is_explicit_and_not_doubling():
    r=row("arithmetic_sequence",{"a":47,"b":60,"c":13})
    assert r["target"]["answer"]=="73"
    assert "tăng đúng 13" in r["problem"]
    assert r["target"]["steps"][0]["expression"]=="60+13"


def test_percent_intermediate_unit_and_geometric_dimensionality():
    r=row("percent_ratio",{"a":27,"b":90})
    assert r["target"]["steps"][0]["unit"]==""
    assert r["target"]["steps"][1]["unit"]=="%"
    trap=row("trapezoid_area",{"a":19,"b":11,"c":8})
    assert [s["unit"] for s in trap["target"]["steps"]]==["cm","cm²","cm²"]
    assert trap["target"]["answer"]=="120"
    box=row("box_volume",{"a":7,"b":6,"c":5})
    assert [s["unit"] for s in box["target"]["steps"]]==["cm²","cm³"]


@pytest.mark.parametrize("topic,values,grade,error",[
 ("vertical_add",{"a":28,"b":17},1,"GRADE_CARRY_EVENT_LIMIT"),
 ("vertical_subtract",{"a":70,"b":9},1,"GRADE_CARRY_EVENT_LIMIT"),
 ("vertical_add",{"a":100000,"b":1},3,"G3_NUMBER_BOUNDS"),
 ("mass_kg_to_g",{"a":263},3,"G3_NUMBER_BOUNDS"),
 ("rectangle_area",{"a":38,"b":23},3,"G3_TWO_DIGIT_MULTIPLIERS"),
 ("square_area",{"a":24},3,"G3_SQUARE_MULTIPLIER"),
 ("share_exact",{"a":21,"b":7},2,"G2_TABLE"),
])
def test_source_bounds_reject_known_failure_classes(topic,values,grade,error):
    r=row(topic,values,grade=grade)
    with pytest.raises(ValueError,match=error):data.grade_bounds(r)


def test_case_signature_detects_operation_equivalent_collision():
    t=data.LOOKUP["order_operations"]
    first=data.case_signature(t,{"a":Fraction(68),"b":Fraction(4),"c":Fraction(8)})
    second=data.case_signature(t,{"a":Fraction(68),"b":Fraction(8),"c":Fraction(4)})
    assert first==second
    assert data.canonical_expression("(5+8)+3")==data.canonical_expression("3+(8+5)")
    assert data.canonical_expression("5-3")!=data.canonical_expression("3-5")


@pytest.mark.parametrize("topic,values,grade",[
 ("vertical_add",{"a":487,"b":376},2),
 ("vertical_subtract",{"a":3000,"b":72},3),
 ("vertical_subtract",{"a":800000,"b":17},4),
])
def test_current_curriculum_regrouping_limits(topic,values,grade):
    r=row(topic,values,grade=grade)
    with pytest.raises(ValueError,match="GRADE_(?:CARRY|CONSECUTIVE)"):data.grade_bounds(r)
    extension=row(topic,values,grade=5)
    assert data.validate_training_row(extension)
    assert extension["curriculum_status"].startswith("CAPSTONE_HARD_COLUMN")


def test_replay_and_fresh_provenance_cannot_be_falsified():
    generated=Path(__file__).parent/"data"/"teacher_math_v4"/"generated"/"train.jsonl"
    replay=next(json.loads(line) for line in generated.read_text(encoding="utf-8").splitlines() if 'CORRECTED_REPLAY_OF_V3_TRAIN_CASE' in line)
    data.validate([replay])
    false=copy.deepcopy(replay);false["replay_provenance"]["sha256"]="0"*64
    with pytest.raises(ValueError,match="REPLAY_PROVENANCE"):data.validate([false])
    false=copy.deepcopy(replay);false["split"]="val"
    with pytest.raises(ValueError,match="REPLAY_PROVENANCE|FRESH_VAL"):data.validate([false])


def test_pilot_public_steps_linkage_is_excluded():
    cases,_,fingerprints=data.supplemental_pilot_exclusions()
    assert "independent_anchor.jsonl" in fingerprints
    assert data.digest(data.canonical_expression("(8-3)+4")) in cases
    assert data.digest(data.canonical_expression("5+4")) in cases


def test_guard_requests_specific_missing_fact_and_no_computed_answer():
    for kind in data.GUARD_WORDINGS:
        for variant in range(3):
            r=data.guard_row(kind,"train",variant,61,3,"hint")
            assert data.validate_training_row(r)
            assert r["target"]["hint"].count("?")==1
    assert "bao nhiêu quyển sách" in data.GUARD_HINTS["missing_quantity"][1]
    assert "bao nhiêu nhóm" in data.GUARD_HINTS["missing_divisor"][2].casefold()


def test_target_corruption_is_rejected():
    r=row("vertical_add",{"a":487,"b":376},grade=5)
    changed=copy.deepcopy(r);changed["target"]["steps"][1]["explanation"]="Không nhớ gì từ cột trước."
    with pytest.raises(ValueError,match="RECONSTRUCTION"):data.validate_training_row(changed)
    changed=copy.deepcopy(r);changed["column_trace"][1]["incoming_carry"]=0
    with pytest.raises(ValueError,match="TRACE"):data.validate_training_row(changed)
    changed=row("vertical_add",{"a":487,"b":376},grade=5,mode="hint")
    changed["target"]["hint"]="Em biết kết quả 863 chưa?"
    with pytest.raises(ValueError,match="DISCLOSURE"):data.validate_training_row(changed)


def test_full_generated_corpus_independence_balance_and_parser_contract():
    generated=Path(__file__).parent/"data"/"teacher_math_v4"/"generated"
    rows=[json.loads(line) for split in ("train","val") for line in (generated/f"{split}.jsonl").read_text(encoding="utf-8").splitlines()]
    exclusions,old_questions,hashes=data.v3_exclusions()
    assert data.validate(rows,exclusions,old_questions)
    report=json.loads((generated/"dataset_report.json").read_text(encoding="utf-8"))
    assert report["splits"]=={"train":7100,"val":460}
    assert set(report["grades"]["train"].values())=={1420}
    assert report["modes"]["train"]=={"worked_solution":3550,"hint":3550}
    assert hashes["train"]=="d5c836206be2dbaf9650ef414a92f8eee8592bab4e3bcec4083cdd226b9effda"
    import train_teacher_math_v3 as trainer
    for r in rows:
        assert set(json.loads(data.prompt(r)))=={"grade","problem","mode"}
        parsed=trainer.parse_output(json.dumps(r["target"],ensure_ascii=False))
        assert trainer.score(r,json.dumps(parsed,ensure_ascii=False))["correct"]


def test_import_does_not_change_frozen_module_globals():
    assert frozen.VERSION=="mvk_teacher_math_v3_20261013"
    assert len(frozen.TOPICS)==57
    assert len(frozen.TOPICS[0].templates)==5
    assert frozen.SYSTEM!=data.SYSTEM
