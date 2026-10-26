"""Acceptance tests for teacher-data truth, split integrity and tutoring safety."""
from collections import Counter
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
import pytest

from teacher_math_data_v3 import (TOPICS, LEGACY_OR_ENRICHMENT, build, build_target,
    digest, evaluate_expression, export, independent_answer, make_row, number,
    prompt, result_mismatch_place, validate, vertical_steps)


@pytest.fixture(scope="module")
def rows():
    return build()


def test_all_domains_have_worked_hint_and_independent_exact_oracles(rows):
    assert len(TOPICS)==57
    assert Counter(r["split"] for r in rows)=={"train":4170,"val":262,"challenge":262}
    for split in ("train","val","challenge"):
        assert {r["topic"] for r in rows if r["split"]==split and r["target"]["status"]=="solve"}=={t.name for t in TOPICS}
        assert {r["mode"] for r in rows if r["split"]==split}=={"hint","worked_solution"}
    assert validate(rows)
    assert all(not r["human_verified"] and not r["semantic_correctness_verified"] for r in rows)


@pytest.mark.parametrize("name,values,answer",[
    ("add_join",{"a":12,"b":6},18),
    ("sub_remaining",{"a":35,"b":12},23),
    ("compare_difference",{"a":38,"b":15},23),
    ("missing_addend",{"a":11,"b":34},23),
    ("tens_place_value",{"a":57},50),
    ("equal_groups",{"a":8,"b":5},40),
    ("share_exact",{"a":45,"b":5},9),
    ("missing_factor",{"a":16,"b":2},8),
    ("multistep_add_sub",{"a":18,"b":7,"c":9},16),
    ("groups_after_sale",{"a":7,"b":4,"c":5},23),
    ("money_change",{"a":250,"b":600},350),
    ("elapsed_minutes",{"a":15,"b":44},29),
    ("division_remainder",{"a":29,"b":6},5),
    ("order_operations",{"a":8,"b":7,"c":6},50),
    ("length_m_to_cm",{"a":13},1300),
    ("hours_minutes",{"a":2,"b":17},137),
    ("mass_kg_to_g",{"a":3},3000),
    ("rectangle_perimeter",{"a":15,"b":6},42),
    ("square_perimeter",{"a":7},28),
    ("rectangle_area",{"a":12,"b":5},60),
    ("square_area",{"a":9},81),
    ("table_total",{"a":4,"b":7,"c":13},24),
    ("sum_difference_large",{"a":54,"b":10},32),
    ("sum_difference_small",{"a":54,"b":10},22),
    ("fraction_add",{"a":Fraction(2,3),"b":Fraction(1,6)},Fraction(5,6)),
    ("fraction_subtract",{"a":Fraction(5,6),"b":Fraction(1,3)},Fraction(1,2)),
    ("fraction_multiply",{"a":Fraction(3,4),"b":Fraction(2,5)},Fraction(3,10)),
    ("fraction_divide",{"a":Fraction(2,3),"b":Fraction(4,5)},Fraction(5,6)),
    ("average_three",{"a":14,"b":17,"c":20},17),
    ("fraction_of_quantity",{"a":30,"b":Fraction(2,5)},12),
    ("parallelogram_area",{"a":12,"b":7},84),
    ("ratio_share",{"a":60,"b":2,"c":3},24),
    ("multiples_missing",{"a":7,"b":14},21),
    ("decimal_add",{"a":Fraction("2.35"),"b":Fraction("0.7")},Fraction("3.05")),
    ("decimal_subtract",{"a":Fraction("4.1"),"b":Fraction("2.37")},Fraction("1.73")),
    ("decimal_multiply",{"a":Fraction("1.2"),"b":Fraction("0.35")},Fraction("0.42")),
    ("decimal_divide",{"a":Fraction("3.6"),"b":Fraction("0.8")},Fraction("4.5")),
    ("percent_part",{"a":240,"b":25},60),
    ("percent_whole",{"a":24,"b":15},160),
    ("percent_ratio",{"a":18,"b":72},25),
    ("triangle_area",{"a":13,"b":8},52),
    ("trapezoid_area",{"a":18,"b":10,"c":7},98),
    ("circle_area",{"a":3},Fraction("28.26")),
    ("circle_perimeter",{"a":4},Fraction("25.12")),
    ("box_volume",{"a":8,"b":5,"c":3},120),
    ("cube_surface",{"a":6},216),
    ("distance_from_speed_time",{"a":36,"b":Fraction("1.5")},54),
    ("speed_from_distance_time",{"a":72,"b":3},24),
    ("time_from_distance_speed",{"a":84,"b":28},3),
    ("area_unit_conversion",{"a":Fraction("0.25")},2500),
    ("volume_unit_conversion",{"a":Fraction("1.25")},1250),
    ("proportional_direct",{"a":3,"b":21000,"c":5},35000),
    ("proportional_inverse",{"a":6,"b":8,"c":4},12),
    ("probability_count",{"a":3,"b":5},Fraction(3,8)),
    ("empirical_frequency",{"a":7,"b":20},Fraction(7,20)),
    ("vertical_add",{"a":999999,"b":1},1000000),
    ("vertical_subtract",{"a":3002,"b":1785},1217),
])
def test_manual_reference_examples_all_families(name,values,answer):
    values={k:Fraction(v) for k,v in values.items()}
    t=next(t for t in TOPICS if t.name==name)
    assert independent_answer(name,values)==answer
    target=build_target(t,values,"worked_solution")
    assert Fraction(target["answer"].replace(",","."))==answer
    assert any(Fraction(s["result"].replace(",","."))==answer for s in target["steps"])
    for step in target["steps"]:
        assert evaluate_expression(step["expression"])==Fraction(step["result"].replace(",","."))


def test_question_only_input_has_no_teacher_oracle_or_topic(rows):
    for r in rows:
        p=json.loads(prompt(r))
        assert set(p)=={"grade","problem","mode"}
        assert p["problem"]==r["problem"]
        assert not {"facts","topic","expected_answer","oracle_answer","target","parameters","status"}&set(p)


def test_numeric_wording_groups_and_paired_modes_never_cross_split(rows):
    for key in ("numeric_case_group","split_group_id","wording_family","problem"):
        parts=[{r[key] for r in rows if r["split"]==s} for s in ("train","val","challenge")]
        for i in range(3):
            for j in range(i+1,3):assert not parts[i]&parts[j]
    assert len({r["sample_id"] for r in rows})==len(rows)
    pairs=Counter(r["numeric_case_group"] for r in rows)
    assert any(v>1 for v in pairs.values())


def test_hint_and_guard_has_one_prompt_without_computed_answer(rows):
    for r in rows:
        t=r["target"]
        if r["mode"]=="hint" or t["status"]!="solve":
            assert t["steps"]==[] and t["answer"] is None and t["unit"] is None
            assert t["hint"].count("?")==1
            assert "=" not in t["hint"]
            assert not any(ch.isdigit() for ch in t["hint"]) or r["topic"]=="zero_division"
    assert {r["topic"] for r in rows if r["target"]["status"]!="solve"}=={
        "missing_quantity","missing_divisor","ambiguous_referent","unavailable_picture","zero_division","non_math"}


def test_units_follow_actual_variant_not_original_template(rows):
    expected={"add_join":{0:"viên",1:"quả",2:"cái",3:"viên",4:"bạn"},
        "sub_remaining":{0:"viên",1:"cái",2:"bạn",3:"quả",4:"quyển"},
        "table_total":{0:"quyển",1:"cây",2:"chiếc",3:"đồ vật",4:"học sinh"},
        "percent_part":{0:"",1:"",2:"đồ vật",3:"",4:""}}
    for r in rows:
        if r["topic"] in expected and r["mode"]=="worked_solution":
            assert r["target"]["unit"]==expected[r["topic"]][r["template_variant"]]
    assert {r["target"]["unit"] for r in rows if r["topic"]=="rectangle_area" and r["mode"]=="worked_solution"}=={"cm²"}
    assert {r["target"]["unit"] for r in rows if r["topic"]=="box_volume" and r["mode"]=="worked_solution"}=={"cm³"}


def test_current_grade_limits_and_extensions_not_certified(rows):
    for r in rows:
        if r["topic"] in ("add_join","sub_remaining","missing_addend","compare_difference"):
            p={k:int(Fraction(v)) for k,v in r["parameters"].items()}
            assert max(p.values())<=100
            if r["topic"]=="add_join":assert p["a"]%10+p["b"]%10<10 and p["a"]+p["b"]<=100
            elif r["topic"]=="missing_addend":assert p["b"]%10>=p["a"]%10
            else:assert p["a"]%10>=p["b"]%10
        if r["topic"] in ("equal_groups","share_exact","missing_factor"):
            assert Fraction(r["parameters"]["b"]) in (2,5)
        if r["topic"] in ("fraction_add","fraction_subtract"):
            a,b=(Fraction(r["parameters"][k]) for k in "ab")
            assert max(a.denominator,b.denominator)%min(a.denominator,b.denominator)==0
        if r["topic"]=="decimal_multiply":
            b=Fraction(r["parameters"]["b"])
            assert (b<10 and (b*10).denominator==1) or (b<1 and (b*100).denominator==1)
        if r["topic"] in LEGACY_OR_ENRICHMENT:
            assert r["curriculum_status"]=="LEGACY_OR_ENRICHMENT_UNVERIFIED"


def test_student_wrong_result_preserved_and_no_unseen_mark_diagnosis(rows):
    examples=[r for r in rows if r["observed_work_verbatim"] is not None]
    assert examples
    for r in examples:
        observed=r["observed_work_verbatim"]
        assert observed in r["problem"]
        assert Fraction(observed)!=Fraction(r["oracle_answer"])
        if r["mode"]=="hint":assert observed not in r["target"]["hint"]
        else:
            assert observed in r["target"]["steps"][0]["explanation"]
            assert "không thể xác định" in r["target"]["steps"][0]["explanation"]
    assert result_mismatch_place(1217,"1317")=="trăm"


def test_cascading_borrow_and_new_digit_carry_are_visible_and_checked():
    t=next(t for t in TOPICS if t.name=="vertical_subtract")
    target=build_target(t,{"a":Fraction(3002),"b":Fraction(1785)},"worked_solution")
    assert target["answer"]=="1217"
    assert any("qua các hàng có chữ số 0" in s["explanation"] for s in target["steps"])
    assert target["steps"][0]["expression"]=="12-5"
    assert target["steps"][-1]["result"]=="3002"
    a=next(t for t in TOPICS if t.name=="vertical_add")
    target=build_target(a,{"a":Fraction(999999),"b":Fraction(1)},"worked_solution")
    assert target["answer"]=="1000000" and any("triệu" in s["explanation"] for s in target["steps"])


@pytest.mark.parametrize("expr",["__import__('os')","sum([1,2])","2**3","1//2","True","1e99","[1]","a+3","2/0","2.5%2","1,2+3","1;2"])
def test_unsafe_unknown_and_invalid_arithmetic_rejected(expr):
    with pytest.raises(ValueError):evaluate_expression(expr)


def test_exact_decimal_format_without_float_roundoff():
    assert evaluate_expression("0.1+0.2")==Fraction(3,10)
    assert evaluate_expression("(2/3)+(1/6)")==Fraction(5,6)
    assert evaluate_expression("3.14*3*3")==Fraction(1413,50)
    assert number(Fraction(-1,20))=="-0,05"
    assert number(Fraction(1,3))=="1/3"
    assert number(Fraction(25,10))=="2,5"


def test_validation_rejects_tampered_gold_and_false_human_claim(rows):
    for key,value in (("human_verified",True),("semantic_correctness_verified",True)):
        bad=deepcopy(rows[:1]);bad[0][key]=value
        with pytest.raises(ValueError):validate(bad)
    bad=deepcopy(rows[:1]);bad[0]["target"]["steps"][0]["result"]="999999"
    with pytest.raises(ValueError):validate(bad)
    bad=deepcopy(rows[:1]);bad[0]["target"]["answer"]="999999"
    with pytest.raises(ValueError):validate(bad)


def test_export_deterministic_bytes_fingerprints_and_honest_scope(tmp_path):
    a,b=tmp_path/"a",tmp_path/"b"
    report=export(a);assert report==export(b)
    assert report["topic_count"]==57 and report["human_verified"] is False
    assert "not teacher-approved" in report["evaluation_role"]
    for split,expected in report["fingerprints"].items():
        content=(a/(split+".jsonl")).read_bytes()
        assert content==(b/(split+".jsonl")).read_bytes()
        assert hashlib.sha256(content).hexdigest()==expected
