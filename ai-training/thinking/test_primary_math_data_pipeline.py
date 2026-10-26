"""Adversarial curation gates, not claims about the model or teaching quality."""
from copy import deepcopy
from fractions import Fraction
import json
import pytest
import primary_math_data_pipeline as pipeline


def example():
    return {"sample_id": "small_case", "case_group_id": "math_group_one", "grade": 1, "split": "train",
            "problem": "Hộp có 12 viên bi, thêm 3 viên. Có tất cả bao nhiêu viên bi?",
            "provenance": {"authoring_method": "original_AI_teacher", "human_verified": False},
            "initial_guidance": ["Hãy xét hai phần được gộp lại."],
            "hints": [{"level": n, "hint": "Xét hai phần cùng loại.", "question": "Em cần gộp những phần nào?"} for n in (1, 2, 3)],
            "worked_steps": [{"step_id": "s0", "title": "Gộp hai phần", "reason": "Số bi được thêm vào cùng hộp.",
                              "expression": "12+3", "result": "15", "unit": "viên bi", "explanation": "Có tất cả 15 viên bi."}],
            "expected_answer": [{"quantity": "Số viên bi trong hộp", "result": "15", "unit": "viên bi"}],
            "student_work": {"text": "", "observations": []}}


def node():
    return {"node_id": "n1", "grade": 1, "curriculum_scope": "current",
            "authoring_plan": {"core_cases": [{"case_slot": "core_0"+str(n), "context_variant": "context"+str(n),
                                                "method_variant": "method"+str(n)} for n in (1, 2, 3)]}}


def mapped(row, n=1, kind="core"):
    row["curriculum_assignment"] = {"node_id": "n1", "curriculum_scope": "current", "case_kind": kind,
                                    "case_slot": "core_0"+str(n), "context_variant": "context"+str(n),
                                    "method_variant": "method"+str(n)}
    return row


def test_exact_decimal_refs_and_no_binary_rounding():
    assert pipeline.exact("0.1+0.2") == Fraction(3, 10)
    assert pipeline.exact(pipeline.expand("{s0}/3", ["0.1+0.2"])) == Fraction(1, 10)
    with pytest.raises(ValueError): pipeline.expand("{s1}+1", ["3"])


@pytest.mark.parametrize("expression", ["__import__('os').system('echo unsafe')", "True+1", "2**99", "9%2", "+(12+3)", "1/0", "9//2"])
def test_forbidden_or_ambiguous_execution(expression):
    with pytest.raises((ValueError, ZeroDivisionError)): pipeline.exact(expression)


def test_wrong_result_or_unit_cannot_pass_mechanical_gate():
    row = example(); row["worked_steps"][0]["result"] = "14"
    assert not pipeline.inspect_case(row)["passed"]
    row = example(); row["expected_answer"][0]["unit"] = "kg"
    assert not pipeline.inspect_case(row)["passed"]


def test_empty_work_is_not_claimed_evidence_and_string_guidance_fails():
    assert pipeline.inspect_case(example())["passed"]
    row = example(); row["initial_guidance"] = "a string is not a guidance list"
    assert not pipeline.inspect_case(row)["passed"]


@pytest.mark.parametrize("field,value", [("hints", [1, 2, 3]), ("provenance", []), ("worked_steps", [None]), ("student_work", "not an object")])
def test_malformed_case_is_quarantined_instead_of_crashing(field, value):
    row = example(); row[field] = value
    assert not pipeline.inspect_case(row)["passed"]
    row = example(); row["student_work"] = {"text": "12+3=14", "observations": [{"excerpt": "borrowed twice", "claim_scope": "invented"}]}
    assert not pipeline.inspect_case(row)["passed"]


def test_correct_arithmetic_never_auto_certifies_content():
    row = example(); assert pipeline.inspect_case(row)["passed"]
    assert pipeline.review_case(row, {}) == "PENDING_CONTENT_QA"
    decision = {"sample_id": row["sample_id"], "row_sha256": pipeline.row_sha(row), "reviewer": "independent AI review", "human_verified": False,
                **{k: True for k in pipeline.REVIEW_FIELDS}}
    decision["hints_non_leaking"] = False
    assert pipeline.review_case(row, {row["sample_id"]: decision}) == "REQUIRES_CONTENT_REVISION"
    decision["hints_non_leaking"] = True; row["problem"] += " Một dữ kiện mới."
    assert pipeline.review_case(row, {row["sample_id"]: decision}) == "REVIEW_HASH_MISMATCH"


def test_guard_and_duplicate_case_groups_do_not_complete_curriculum():
    a = mapped(example(), 1); b = mapped(deepcopy(a), 2); b["sample_id"] = "paraphrase"
    c = mapped(deepcopy(a), 3, "guard"); c["sample_id"] = "guard"; c["case_group_id"] = "another_group"
    report = pipeline.coverage_for_cases([node()], [a, b, c])[0]
    assert report["accepted_core_cases"] == 1 and report["remaining_core_cases"] == 2
    assert report["accepted_guard_cases"] == 1


def test_unknown_node_and_wrong_grade_cannot_be_accepted_mapping():
    row = mapped(example()); row["grade"] = 5
    assert pipeline.mapping_error(row, {"n1": node()}) == "CURRICULUM_GRADE_OR_SCOPE_MISMATCH"
    row["curriculum_assignment"]["node_id"] = "nonexistent"
    assert pipeline.mapping_error(row, {"n1": node()}) == "UNKNOWN_CURRICULUM_NODE"


def test_hint_export_never_contains_worked_answer_fields_or_target_in_user():
    rows = pipeline.chat_records(example())
    assert len(rows) == 4 and len({r["case_group_id"] for r in rows}) == 1
    for row in rows:
        user = json.loads(row["messages"][1]["content"])
        assert set(user) == {"grade", "problem", "mode"}
        if row["mode"] != "worked_solution":
            target = json.loads(row["messages"][2]["content"])
            assert set(target) == {"hint", "question"}


def test_long_division_trace_cannot_bypass_remainder_case_protection():
    import teacher_math_data_v4 as v4
    row = example()
    row["givens"] = [{"value": "53"}, {"value": "7"}]
    row["canonical_case"] = {"family": "division_remainder", "numeric_values": ["53", "7"], "operations": ["53%7"]}
    row["worked_steps"][0].update(expression="53-49", result="4")
    row["expected_answer"][0]["result"] = "4"
    signatures = pipeline.answer_signatures(row, pipeline.inspect_case(row))
    assert v4.digest(v4.canonical_expression("53%7")) in signatures
    row["canonical_case"]["operations"] = ["53%8"]
    with pytest.raises(ValueError): pipeline.answer_signatures(row, pipeline.inspect_case(row))


def inverse_remainder_example():
    row = example()
    row['givens'] = [{'id':'g0','value':'7'},{'id':'g1','value':'8'},{'id':'g2','value':'3'}]
    row['worked_steps'][0].update(expression='8*7+3',result='59')
    row['expected_answer'][0]['result']='59'
    row['canonical_case']={'operations':['59%7'],'numeric_values':['7','8','3'],
        'inverse_euclidean_identity':{'dividend':'59','divisor':'7','quotient':'8','remainder':'3',
        'divisor_given_id':'g0','quotient_given_id':'g1','remainder_given_id':'g2'}}
    return row


def test_inverse_remainder_retains_modulo_protection_without_enabling_calculator_modulo():
    import teacher_math_data_v4 as v4
    row=inverse_remainder_example()
    assert v4.digest(v4.canonical_expression('59%7')) in pipeline.answer_signatures(row,pipeline.inspect_case(row))
    with pytest.raises(ValueError):pipeline.exact('59%7')


@pytest.mark.parametrize('mutation',['wrong_given_role','wrong_quotient','oversized_remainder','wrong_dividend_answer','invented_given_id','false_numeric_list'])
def test_inverse_remainder_rejects_ungrounded_metadata(mutation):
    row=inverse_remainder_example();m=row['canonical_case']['inverse_euclidean_identity']
    if mutation=='wrong_given_role':m['divisor_given_id']='g1'
    elif mutation=='wrong_quotient':m['quotient']='9'
    elif mutation=='oversized_remainder':m['remainder']='10'
    elif mutation=='wrong_dividend_answer':row['expected_answer'][0]['result']='60'
    elif mutation=='invented_given_id':m['remainder_given_id']='not_given'
    else:row['canonical_case']['numeric_values']=['59','7']
    with pytest.raises(ValueError):pipeline.answer_signatures(row,pipeline.inspect_case(row))


def test_owner_attestation_versions_metadata_but_preserves_authored_content():
    source = example(); original = deepcopy(source)
    entry = {"source_row_sha256": pipeline.row_sha(source), "attestation_id": "explicit_owner_snapshot"}
    certified = pipeline.owner_export_row(source, {source["sample_id"]: entry})
    assert source == original
    for field in ("problem", "worked_steps", "hints", "expected_answer", "student_work"):
        assert certified[field] == source[field]
    assert certified["human_verified"] and certified["teacher_certified"] and certified["owner_human_reviewed"]
    assert certified["provenance"]["authorship_origin"] == "AI_GENERATED"
    assert certified["source_role"] == "HUMAN_TEACHER_VERIFIED"
    assert pipeline.row_sha(certified) != entry["source_row_sha256"]
    assert pipeline.inspect_case(certified)["passed"]
    for chat in pipeline.chat_records(certified):
        assert chat["human_verified"] and chat["teacher_certified"]
        assert chat["source_row_sha256"] == pipeline.row_sha(source)
        assert chat["row_sha256"] == pipeline.row_sha(certified)
        assert chat["verification"]["attestation_id"] == "explicit_owner_snapshot"


def test_future_or_edited_rows_cannot_inherit_completed_human_review():
    row = example()
    entry = {"source_row_sha256": pipeline.row_sha(row), "attestation_id": "existing_snapshot"}
    future = deepcopy(row); future["sample_id"] = "not_yet_reviewed"
    exported = pipeline.owner_export_row(future, {row["sample_id"]: entry})
    assert not exported["human_verified"] and not exported["teacher_certified"]
    assert not exported["owner_human_reviewed"]
    assert exported["acceptance_status"] == "ACCEPTED_OWNER_PREAUTHORIZED"
    row["hints"][0]["hint"] += " Dữ liệu thay đổi sau signoff."
    with pytest.raises(ValueError, match="source hash mismatch"):
        pipeline.owner_export_row(row, {row["sample_id"]: entry})


def test_owner_signoff_rejects_future_scope_and_duplicate_rows(tmp_path):
    entry = {"sample_id": "case1", "source_row_sha256": "a"*64, "attestation_id": "owner1",
             "human_verified": True, "teacher_certified": True, "owner_human_reviewed": True}
    statement = {"attestation_id": "owner1", "statement_text": "Owner directly confirms existing content.",
                 "scope": "FUTURE_UNSEEN_ROWS"}
    pipeline.write_json(tmp_path/"owner_human_attestations.json", {"statements": [statement]})
    pipeline.write_rows(tmp_path/"owner_human_signoffs.jsonl", [entry])
    with pytest.raises(ValueError): pipeline.load_owner_signoffs(tmp_path)
    statement["scope"] = "ENUMERATED_EXISTING_ROWS"
    pipeline.write_json(tmp_path/"owner_human_attestations.json", {"statements": [statement]})
    assert pipeline.load_owner_signoffs(tmp_path)["case1"] == entry
    pipeline.write_rows(tmp_path/"owner_human_signoffs.jsonl", [entry, entry])
    with pytest.raises(ValueError): pipeline.load_owner_signoffs(tmp_path)


def test_export_hash_is_bound_to_owner_signoff():
    row = example()
    entry = {"source_row_sha256": pipeline.row_sha(row), "attestation_id": "owner1",
             "exported_row_sha256": "0"*64}
    with pytest.raises(ValueError, match="export hash mismatch"):
        pipeline.owner_export_row(row, {row["sample_id"]: entry})


def concept_coverage_pair():
    n = node(); n.update(family="curriculum_concept_single_trial_outcomes", numeric_family_links=[])
    a = mapped(example(), 2); b = mapped(deepcopy(a), 3)
    a["sample_id"] = "bag_colors"; b["sample_id"] = "spinner_recording"
    a["problem"] = "Túi gồm các viên màu xanh, đỏ, vàng; ghi màu của một viên lấy ra."
    b["problem"] = "Vòng quay có ô A ghi sao, B ghi sao, C ghi trăng, D ghi mây; so cách ghi mã với tên."
    for x in (a, b):
        x["worked_steps"][0].update(expression="3", result="3", unit="khả năng")
        x["expected_answer"][0].update(result="3", unit="khả năng")
        x["canonical_case"] = {"operations": ["3"]}
    d = {"sample_id": b["sample_id"], "compared_sample_id": a["sample_id"],
         "source_row_sha256": pipeline.row_sha(b), "compared_source_row_sha256": pipeline.row_sha(a),
         "reviewed_semantic_group": "spinner_recording_conventions",
         "distinct_semantics_confirmed": True, "reviewer": "author semantic audit",
         "semantic_rationale": "Color list versus comparing sector codes and repeated names, reviewed explicitly.",
         "evidence_path": "paired_source_map_audit.json", **{k: True for k in pipeline.REVIEW_FIELDS}}
    return n, a, b, d


def test_same_count_needs_explicit_semantic_audit_before_extra_coverage_credit():
    n, a, b, d = concept_coverage_pair()
    assert pipeline.coverage_for_cases([n], [a, b])[0]["accepted_core_cases"] == 1
    assert pipeline.coverage_for_cases([n], [a, b], [d])[0]["accepted_core_cases"] == 2
    assert pipeline.answer_signatures(a, pipeline.inspect_case(a)) == pipeline.answer_signatures(b, pipeline.inspect_case(b))
    # The audit does not alter split groups or the mathematical exclusion signature.
    assert pipeline.chat_records(a)[0]["case_group_id"] == pipeline.chat_records(b)[0]["case_group_id"]


def test_concept_coverage_audit_cannot_survive_changed_source_or_bypass_arithmetic_grouping():
    n, a, b, d = concept_coverage_pair()
    b["problem"] += " Dữ kiện mới."
    with pytest.raises(ValueError, match="source hash mismatch"):
        pipeline.coverage_for_cases([n], [a, b], [d])
    b["worked_steps"][0].update(expression="1+2")
    d["source_row_sha256"] = pipeline.row_sha(b)
    with pytest.raises(ValueError, match="arithmetic case grouping"):
        pipeline.coverage_for_cases([n], [a, b], [d])


def test_concept_coverage_audit_requires_accepted_comparison_and_complete_review():
    n, a, b, d = concept_coverage_pair()
    with pytest.raises(ValueError, match="two distinct accepted cases"):
        pipeline.coverage_for_cases([n], [b], [d])
    d["hints_non_leaking"] = False
    with pytest.raises(ValueError, match="complete explicit semantic decision"):
        pipeline.coverage_for_cases([n], [a, b], [d])
