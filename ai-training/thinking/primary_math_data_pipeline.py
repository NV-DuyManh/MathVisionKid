"""Curate teaching data and apply explicit, hash-bound owner teacher attestations.

Authorship, content QA and human signoff are separate records. Standing approval
never supplies evidence that a human inspected an unseen future row. Never train
or read sealed concept tests here.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import unicodedata

HERE = Path(__file__).resolve().parent
DEFAULT_ROOT = HERE / "data" / "primary_math_teacher_20261016"
REVIEW_FIELDS = ("semantic_correct", "steps_complete", "grade_appropriate",
                 "unit_consistent", "hints_non_leaking", "grounded_student_feedback", "curriculum_mapping_correct")
SYSTEM = ("Bạn là giáo viên hỗ trợ toán tiểu học Việt Nam. Dùng đúng dữ kiện, "
          "nói rõ vì sao chọn phép tính và đơn vị. Chỉ giải đầy đủ khi được yêu cầu. "
          "Khi xin gợi ý, chỉ hỗ trợ mức được yêu cầu, không đưa đáp số hay tính sẵn. "
          "Thiếu dữ kiện hoặc ảnh thì hỏi lại; không bịa kết quả quan sát hay lỗi thao tác.")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def row_sha(row):
    return sha(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode())


def normalized(text):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip().casefold()


def write_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def write_rows(path, values):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n" for value in values)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n"); temporary.replace(path)
    return {"rows": len(values), "bytes": path.stat().st_size, "sha256": sha(path.read_bytes())}


def read_rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def exact(expression):
    """Only bounded rational + - * /, without eval, calls, floats, powers, or modulo."""
    if not isinstance(expression, str) or len(expression) > 4000:
        raise ValueError("expression length/type")
    tree = ast.parse(expression, mode="eval")
    if len(list(ast.walk(tree))) > 180:
        raise ValueError("expression too complex")
    def walk(node, depth=0):
        if depth > 24: raise ValueError("expression too deep")
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            literal = ast.get_source_segment(expression, node)
            if len(literal) > 80: raise ValueError("number too long")
            value = Fraction(literal)
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            value = -walk(node.operand, depth+1)
        elif isinstance(node, ast.BinOp):
            left, right = walk(node.left, depth+1), walk(node.right, depth+1)
            if isinstance(node.op, ast.Add): value = left + right
            elif isinstance(node.op, ast.Sub): value = left - right
            elif isinstance(node.op, ast.Mult): value = left * right
            elif isinstance(node.op, ast.Div): value = left / right
            else: raise ValueError("only + - * / allowed")
        else: raise ValueError("invalid arithmetic node")
        if max(value.numerator.bit_length(), value.denominator.bit_length()) > 512:
            raise ValueError("unbounded rational")
        return value
    return walk(tree.body)


def expand(expression, preceding):
    def replace(match):
        index = int(match[1])
        if index >= len(preceding): raise ValueError("forward or absent step reference")
        return "(" + preceding[index] + ")"
    return re.sub(r"\{s(\d+)\}", replace, expression)


def inspect_case(row):
    errors, warnings, expressions = [], [], []
    try:
        if not isinstance(row.get("sample_id"), str) or not row["sample_id"]:
            raise ValueError("sample_id absent")
        if not isinstance(row.get("case_group_id"), str) or not row["case_group_id"]:
            raise ValueError("case grouping absent")
        if type(row.get("grade")) is not int or row["grade"] not in range(1, 6):
            raise ValueError("grade must be 1..5")
        if row.get("split") != "train": raise ValueError("this first authoring pack is training only")
        if not isinstance(row.get("problem"), str) or len(row["problem"].strip()) < 12:
            raise ValueError("problem absent")
        provenance = row["provenance"]
        if not isinstance(provenance, dict): raise ValueError("provenance must be an object")
        owner_attested = (provenance.get("owner_human_reviewed") is True
                          and row.get("verification", {}).get("basis") == "EXPLICIT_OWNER_HUMAN_TEACHER_ATTESTATION")
        if provenance.get("authoring_method") != "original_AI_teacher" or (provenance.get("human_verified") is not False and not owner_attested):
            raise ValueError("AI provenance required")
        if provenance.get("teacher_certified", False) and not owner_attested:
            raise ValueError("teacher certification requires a separate owner attestation")
        if not isinstance(row.get("initial_guidance"), list) or not row["initial_guidance"] or any(not isinstance(x, str) or not x.strip() for x in row["initial_guidance"]):
            raise ValueError("initial guidance absent")
        hints = row["hints"]
        if not isinstance(hints, list) or any(not isinstance(h, dict) for h in hints):
            raise ValueError("hints must be objects")
        if len(hints) != 3 or [h.get("level") for h in hints] != [1, 2, 3]:
            raise ValueError("three ordered hint levels required")
        for hint in hints:
            if not hint.get("hint") or not hint.get("question"):
                raise ValueError("hint and guiding question required")
            if "?" in hint["hint"]: raise ValueError("supporting hint must be declarative; keep one guiding question")
            if hint["question"].count("?") != 1: raise ValueError("one guiding question per level")
        answers = row["expected_answer"]
        steps = row["worked_steps"]
        if not isinstance(answers, list) or not isinstance(steps, list):
            raise ValueError("answers and steps must be lists")
        if row.get("can_solve", bool(answers)):
            if not answers or not steps: raise ValueError("solvable example needs worked steps and answer")
        elif answers or steps: raise ValueError("missing-data case must not invent a numeric solution")
        for index, step in enumerate(steps):
            if not all(isinstance(step.get(k), str) and step[k].strip() for k in ("title", "reason", "explanation")):
                raise ValueError("every step needs a title, reason and explanation")
            expression = step.get("expression")
            if expression is None:
                expressions.append("")
                warnings.append("nonnumeric step requires content review")
                continue
            expanded = expand(expression, expressions)
            if exact(expanded) != Fraction(str(step["result"])):
                raise ValueError("incorrect step result at " + str(index))
            expressions.append(expanded)
        for answer in answers:
            if not answer.get("quantity") or "result" not in answer or "unit" not in answer:
                raise ValueError("answer needs named quantity, result and explicit unit")
            try: result = Fraction(str(answer["result"]))
            except (ValueError, ZeroDivisionError):
                warnings.append("categorical answer requires content review"); continue
            matching = []
            for index, step in enumerate(steps):
                if expressions[index] and exact(expressions[index]) == result and step.get("unit") == answer["unit"]:
                    matching.append(index)
            if not matching: raise ValueError("answer not grounded in checked step with same unit")
        if row.get("student_work") and (row["student_work"].get("text") or row["student_work"].get("observations")):
            student = row["student_work"]
            if not student.get("text") or not student.get("observations"):
                raise ValueError("observed student work needs explicit evidence")
            for observation in student["observations"]:
                if observation["excerpt"] not in student["text"] or not observation.get("claim_scope"):
                    raise ValueError("ungrounded student-work observation")
    except (KeyError, TypeError, ValueError, AttributeError, SyntaxError, ZeroDivisionError, OverflowError) as error:
        errors.append(str(error))
    return {"passed": not errors, "errors": errors, "warnings": warnings,
            "expanded_expressions": expressions, "arithmetic_is_semantic_proof": False}


def protections():
    # Numeric development tests were already exposed. The sealed concept test
    # is deliberately neither opened nor used to manufacture training cases.
    import teacher_math_data_v4 as v4
    signatures, questions, fingerprints, _ = v4.v3_catalog()
    pilots, pilot_questions, pilot_fingerprints = v4.supplemental_pilot_exclusions()
    signatures |= pilots; questions |= pilot_questions
    fresh = HERE / "data" / "teacher_math_v4" / "generated" / "val.jsonl"
    if fresh.exists():
        fingerprints["v4_fresh_val"] = sha(fresh.read_bytes())
        for row in read_rows(fresh):
            if row.get("numeric_case_group"): signatures.add(row["numeric_case_group"])
            questions.add(row["problem"])
    concept_val = HERE / "data" / "teacher_math_v3" / "concept_validation_v4.jsonl"
    if concept_val.exists():
        fingerprints["known_concept_development_val30"] = sha(concept_val.read_bytes())
        for row in read_rows(concept_val):
            question = row.get("question", row.get("problem"))
            if question: questions.add(question)
            for message in row.get("messages", []):
                if message.get("role") == "user": questions.add(message["content"])
    return signatures, {normalized(q) for q in questions}, {**fingerprints, **pilot_fingerprints}


def answer_signatures(row, inspected):
    import teacher_math_data_v4 as v4
    result = set()
    for answer in row.get("expected_answer", []):
        try: number = Fraction(str(answer["result"]))
        except (ValueError, ZeroDivisionError): continue
        for expression in inspected["expanded_expressions"]:
            if expression and exact(expression) == number:
                result.add(v4.digest(v4.canonical_expression(expression)))
    # A long-division trace and a % oracle can describe the same held-out case.
    # % is metadata-only here; it is never enabled in the live app calculator.
    canonical = row.get("canonical_case", {})
    answers = set()
    for answer in row.get("expected_answer", []):
        try: answers.add(Fraction(str(answer["result"])))
        except (ValueError, ZeroDivisionError): pass
    declared_mod = False
    for expression in canonical.get("operations", []):
        if not isinstance(expression, str) or "{s" in expression or "//" in expression: continue
        tree = ast.parse(expression, mode="eval").body
        if isinstance(tree, ast.BinOp) and isinstance(tree.op, ast.Mod):
            left = exact(ast.get_source_segment(expression, tree.left))
            right = exact(ast.get_source_segment(expression, tree.right))
            declared = [Fraction(str(n)) for n in canonical.get("numeric_values", [])]
            givens = {Fraction(str(g["value"])) for g in row.get("givens", []) if g.get("value") is not None}
            if left.denominator != 1 or right.denominator != 1 or left < 0 or right <= 0:
                raise ValueError("invalid declared Euclidean identity")
            inverse = canonical.get("inverse_euclidean_identity")
            if inverse is not None:
                # Inverse tasks give divisor, quotient, remainder and ask for the
                # dividend. Bind every role to a specific actual given, never to
                # an ungrounded declared numeric list or a changed answer.
                try:
                    by_id = {g["id"]: Fraction(str(g["value"])) for g in row["givens"] if g.get("value") is not None}
                    d, q, r = [Fraction(str(inverse[k])) for k in ("divisor", "quotient", "remainder")]
                    grounded = all(by_id[inverse[k+"_given_id"]] == v for k,v in (("divisor",d),("quotient",q),("remainder",r)))
                    valid_inverse = (grounded and len({inverse[k+"_given_id"] for k in ("divisor","quotient","remainder")}) == 3
                        and all(v.denominator == 1 for v in (d,q,r)) and d > 0 and q >= 0 and 0 <= r < d
                        and Fraction(str(inverse["dividend"])) == left == d*q+r and right == d
                        and left in answers and declared == [d,q,r] and divmod(left,d) == (q,r))
                except (KeyError, TypeError, ValueError, ZeroDivisionError):
                    valid_inverse = False
                if not valid_inverse: raise ValueError("inverse remainder identity not grounded in given roles and dividend answer")
                result.add(v4.digest(v4.canonical_expression(expression)))
            elif declared[:2] != [left, right] or not {left, right} <= givens or left % right not in answers:
                raise ValueError("declared remainder identity not grounded in givens and answer")
            value = left % right; declared_mod = True
        else:
            value = exact(expression)
        if value in answers: result.add(v4.digest(v4.canonical_expression(expression)))
    if (canonical.get("family") == "division_remainder" or row.get("topic") == "division_remainder") and not declared_mod:
        raise ValueError("remainder identity requires declared verified dividend/divisor")
    return result


def review_case(row, decisions):
    decision = decisions.get(row["sample_id"])
    if not decision: return "PENDING_CONTENT_QA"
    if decision.get("row_sha256") != row_sha(row): return "REVIEW_HASH_MISMATCH"
    if decision.get("human_verified") is not False: return "REVIEW_PROVENANCE_INVALID"
    if not decision.get("reviewer") or any(type(decision.get(key)) is not bool for key in REVIEW_FIELDS):
        return "REVIEW_INCOMPLETE"
    return "ACCEPTED_AUTHOR_QA" if all(decision[k] for k in REVIEW_FIELDS) else "REQUIRES_CONTENT_REVISION"


def load_owner_signoffs(root):
    """Load only enumerated human attestations; policy defaults are not evidence."""
    path = Path(root) / "owner_human_signoffs.jsonl"
    statements_path = Path(root) / "owner_human_attestations.json"
    if not path.exists(): return {}
    statements = json.loads(statements_path.read_text(encoding="utf-8"))["statements"]
    by_id = {s["attestation_id"]: s for s in statements}
    result = {}
    for entry in read_rows(path):
        statement = by_id.get(entry.get("attestation_id"), {})
        if (not statement.get("statement_text") or statement.get("scope") != "ENUMERATED_EXISTING_ROWS"
                or entry.get("sample_id") in result
                or not all(entry.get(k) is True for k in ("human_verified", "teacher_certified", "owner_human_reviewed"))
                or not re.fullmatch(r"[0-9a-f]{64}", entry.get("source_row_sha256", ""))):
            raise ValueError("invalid or duplicate owner human signoff")
        result[entry["sample_id"]] = entry
    return result


def owner_export_row(row, signoffs):
    """Version metadata without rewriting source rows or their original QA hashes."""
    entry = signoffs.get(row["sample_id"])
    source_hash = row_sha(row)
    if entry and entry["source_row_sha256"] != source_hash:
        raise ValueError("owner human signoff source hash mismatch: " + row["sample_id"])
    output = deepcopy(row)
    verified = entry is not None
    role = "HUMAN_TEACHER_VERIFIED" if verified else "AI_GENERATED"
    status = "OWNER_HUMAN_CERTIFIED" if verified else "ACCEPTED_OWNER_PREAUTHORIZED"
    for target in (output, output["provenance"]):
        target.update(human_verified=verified, teacher_certified=verified,
                      owner_human_reviewed=verified, source_role=role)
    output["provenance"].update(authoring_label=role, authorship_origin="AI_GENERATED",
                                 content_review_status=status,
                                 independent_external_reviewer=False)
    output["acceptance_status"] = status
    output["verification"] = {"basis": "EXPLICIT_OWNER_HUMAN_TEACHER_ATTESTATION" if verified else "AUTHOR_QA_OWNER_PREAUTHORIZED",
                              "source_row_sha256": source_hash,
                              "attestation_id": entry["attestation_id"] if verified else None,
                              "reviewer_role": "PROJECT_OWNER_AND_SELF_DECLARED_TEACHER" if verified else "AUTHOR_SELF_QA",
                              "credential_independently_authenticated": False}
    if entry and entry.get("exported_row_sha256") and entry["exported_row_sha256"] != row_sha(output):
        raise ValueError("owner human signoff export hash mismatch: " + row["sample_id"])
    return output


def chat_records(row):
    prompt = {"grade": row["grade"], "problem": row["problem"]}
    if (row.get("student_work") or {}).get("text"): prompt["student_work"] = row["student_work"]["text"]
    signatures = answer_signatures(row, inspect_case(row))
    group = "math_"+sha(json.dumps(sorted(signatures)).encode()) if signatures else "text_"+sha(normalized(row["problem"]).encode())
    result = []
    for mode in ("worked_solution", "hint_level_1", "hint_level_2", "hint_level_3"):
        user = {**prompt, "mode": mode}
        if mode == "worked_solution":
            target = {"can_solve": row.get("can_solve", bool(row["expected_answer"])),
                      "initial_guidance": row["initial_guidance"], "steps": row["worked_steps"],
                      "answer": row["expected_answer"]}
        else:
            hint = row["hints"][int(mode[-1])-1]
            target = {"hint": hint["hint"], "question": hint["question"]}
        result.append({"sample_id": row["sample_id"]+":"+mode, "case_group_id": group,
                       "grade": row["grade"], "split": "train", "mode": mode,
                       "schema": "neutral_teacher_chat.v1_not_live_PlanDraft",
                       "messages": [{"role": "system", "content": SYSTEM},
                                    {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
                                    {"role": "assistant", "content": json.dumps(target, ensure_ascii=False)}],
                       "human_verified": row.get("human_verified", False),
                       "teacher_certified": row.get("teacher_certified", False),
                       "owner_human_reviewed": row.get("owner_human_reviewed", False),
                       "source_role": row.get("source_role", "AI_GENERATED"),
                       "acceptance_status": row.get("acceptance_status", "ACCEPTED_OWNER_PREAUTHORIZED"),
                       "source_row_sha256": row.get("verification", {}).get("source_row_sha256", row_sha(row)),
                       "row_sha256": row_sha(row),
                       "verification": row.get("verification", {})})
    return result


def mapping_error(row, nodes):
    assignment = row.get("curriculum_assignment")
    if not assignment: return "PENDING_CURRICULUM_MAPPING"
    if not isinstance(assignment, dict): return "INVALID_CURRICULUM_MAPPING"
    node = nodes.get(assignment.get("node_id"))
    if node is None: return "UNKNOWN_CURRICULUM_NODE"
    if row["grade"] != node["grade"] or assignment.get("curriculum_scope") != node["curriculum_scope"]:
        return "CURRICULUM_GRADE_OR_SCOPE_MISMATCH"
    kind = assignment.get("case_kind")
    if kind == "core":
        slots = {s["case_slot"]: s for s in node["authoring_plan"]["core_cases"]}
        slot = slots.get(assignment.get("case_slot"))
        if slot is None: return "UNKNOWN_CORE_SLOT"
        if any(assignment.get(k) != slot[k] for k in ("context_variant", "method_variant")):
            return "CORE_CONTEXT_OR_METHOD_UNMAPPED"
        if not row["expected_answer"] or not row["worked_steps"]: return "GUARD_CANNOT_COUNT_AS_CORE"
    elif kind not in ("misconception", "guard", "supplementary"): return "UNKNOWN_CASE_KIND"
    if kind == "misconception" and not (row.get("student_work") or {}).get("text"):
        return "MISCONCEPTION_REQUIRES_OBSERVED_OR_EXPLICIT_HYPOTHETICAL_WORK"
    return None


def reviewed_concept_coverage_groups(nodes, accepted, adjudications):
    """Apply explicit semantic audits only to constant-count concept collisions.

    This changes coverage credit, never content acceptance, protected exclusions,
    chat split groups, source rows, or owner attestations.
    """
    by_id = {r["sample_id"]: r for r in accepted}
    by_node = {n["node_id"]: n for n in nodes}
    groups = {}
    for decision in adjudications:
        row = by_id.get(decision.get("sample_id"))
        other = by_id.get(decision.get("compared_sample_id"))
        if row is None or other is None or row is other:
            raise ValueError("coverage audit requires two distinct accepted cases")
        if (decision.get("source_row_sha256") != row_sha(row)
                or decision.get("compared_source_row_sha256") != row_sha(other)):
            raise ValueError("coverage audit source hash mismatch")
        assignment, comparison = row["curriculum_assignment"], other["curriculum_assignment"]
        node = by_node.get(assignment["node_id"], {})
        if (assignment["node_id"] != comparison["node_id"]
                or assignment.get("case_kind") != "core" or comparison.get("case_kind") != "core"
                or assignment.get("case_slot") == comparison.get("case_slot")
                or not node.get("family", "").startswith("curriculum_concept_")
                or node.get("numeric_family_links") != []):
            raise ValueError("coverage audit is restricted to conceptual core pairs")
        signatures = []
        for case in (row, other):
            inspected = inspect_case(case)
            if not inspected["passed"] or mapping_error(case, by_node):
                raise ValueError("coverage audit cannot repair an invalid case")
            expressions = [x for x in inspected["expanded_expressions"] if x]
            expressions += case.get("canonical_case", {}).get("operations", [])
            if not expressions or any(not isinstance(ast.parse(x, mode="eval").body, ast.Constant)
                                      or exact(x).denominator != 1 or exact(x) < 0 for x in expressions):
                raise ValueError("coverage audit cannot override arithmetic case grouping")
            signatures.append(answer_signatures(case, inspected))
        if not signatures[0] or signatures[0] != signatures[1]:
            raise ValueError("coverage audit requires an actual shared literal-count signature")
        group = decision.get("reviewed_semantic_group", "")
        if (row["sample_id"] in groups or not re.fullmatch(r"[a-z0-9_:-]{3,120}", group)
                or decision.get("distinct_semantics_confirmed") is not True
                or not decision.get("reviewer") or not decision.get("semantic_rationale")
                or not decision.get("evidence_path")
                or not all(decision.get(k) is True for k in REVIEW_FIELDS)):
            raise ValueError("coverage audit requires a complete explicit semantic decision")
        groups[row["sample_id"]] = ("reviewed_concept", group)
    return groups


def coverage_for_cases(nodes, accepted, adjudications=()):
    reviewed_groups = reviewed_concept_coverage_groups(nodes, accepted, adjudications)
    coverage = []
    for node in nodes:
        related = [r for r in accepted if r.get("curriculum_assignment", {}).get("node_id") == node["node_id"]]
        core = [r for r in related if r["curriculum_assignment"]["case_kind"] == "core" and not mapping_error(r, {node["node_id"]: node})]
        # Three paraphrases of the same mathematical case do not fill three slots.
        groups, slots = set(), set()
        for row in core:
            slot = row["curriculum_assignment"]["case_slot"]
            signatures = answer_signatures(row, inspect_case(row))
            group = tuple(sorted(signatures)) if signatures else normalized(row["problem"])
            group = reviewed_groups.get(row["sample_id"], group)
            if group not in groups and slot not in slots:
                groups.add(group); slots.add(slot)
        target = len(node["authoring_plan"]["core_cases"])
        coverage.append({"node_id": node["node_id"], "grade": node["grade"], "curriculum_scope": node["curriculum_scope"],
                         "target_core_cases": target, "accepted_core_cases": len(slots),
                         "accepted_core_slots": sorted(slots),
                         "remaining_core_slots": [s["case_slot"] for s in node["authoring_plan"]["core_cases"] if s["case_slot"] not in slots],
                         "accepted_misconception_cases": sum(r["curriculum_assignment"]["case_kind"] == "misconception" for r in related),
                         "accepted_guard_cases": sum(r["curriculum_assignment"]["case_kind"] == "guard" for r in related),
                         "remaining_core_cases": max(0, target-len(slots))})
    return coverage


def load_numeric_overlap_exceptions(root):
    """Explicit owner-authorized, source-hash-bound exceptions; exact questions stay blocked."""
    root = Path(root)
    path = root / "numeric_overlap_exceptions.jsonl"
    if not path.exists():
        return {}
    policy_path = root / "numeric_overlap_exception_policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    if (policy.get("owner_authorized") is not True
            or policy.get("authorization_origin") != "DIRECT_HUMAN_USER_REPLY"
            or policy.get("human_review_of_content_claimed") is not False):
        raise ValueError("numeric overlap exception policy is not authorized")
    result = {}
    for record in read_rows(path):
        evidence = (HERE.parent / record["evidence_path"]).resolve()
        if (record["sample_id"] in result
                or record.get("policy_sha256") != sha(policy_path.read_bytes())
                or not evidence.is_relative_to((HERE / "evidence").resolve())
                or not evidence.is_file()
                or record.get("evidence_sha256") != sha(evidence.read_bytes())
                or record.get("numeric_test_independence_claimed") is not False):
            raise ValueError("invalid numeric overlap exception evidence")
        audit = json.loads(evidence.read_text(encoding="utf-8"))
        if not any(x.get("sample_id") == record["sample_id"]
                   and x.get("source_row_sha256") == record.get("source_row_sha256")
                   and x.get("question_exact_collision") is False
                   for x in audit.get("cases", [])):
            raise ValueError("numeric overlap audit does not bind the source row")
        result[record["sample_id"]] = record
    return result


def curate(root=DEFAULT_ROOT):
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    blueprint_path = root / "curriculum_blueprint.json"
    blueprint = json.loads(blueprint_path.read_text(encoding="utf-8")) if blueprint_path.exists() else {"nodes": []}
    nodes_by_id = {n["node_id"]: n for n in blueprint["nodes"]}
    protected, protected_questions, protected_fingerprints = protections()
    # Draft authors retain their source files unchanged. Only normalized,
    # assigned batches enter curation; their provenance points to source hashes.
    drafts = sorted(root.glob("tutoring_seed*.jsonl"))
    inputs = sorted((root/"authored_batches").glob("*.jsonl"))
    reviews = {}
    owner_signoffs = load_owner_signoffs(root)
    numeric_exceptions = load_numeric_overlap_exceptions(root)
    for path in sorted((root/"reviews").glob("*.jsonl")):
        for decision in read_rows(path):
            if decision["sample_id"] in reviews: raise ValueError("conflicting duplicate content review")
            reviews[decision["sample_id"]] = decision
    accepted, pending, manifest, source_accepted = [], [], [], []
    seen_ids, seen_questions = set(), set()
    counts = Counter(); checks = Counter()
    for path in inputs:
        for line_index, row in enumerate(read_rows(path)):
            if not isinstance(row, dict): row = {"malformed_source_value": row}
            sample_id = row.get("sample_id", "")
            if not isinstance(sample_id, str): sample_id = "invalid_"+path.stem+"_"+str(line_index)
            inspected = inspect_case(row)
            signatures = set()
            if inspected["passed"]:
                try: signatures = answer_signatures(row, inspected)
                except (ValueError, KeyError, TypeError, AttributeError, SyntaxError, ZeroDivisionError) as error:
                    inspected["errors"].append(str(error)); inspected["passed"] = False
            status = review_case(row, reviews) if inspected["passed"] else "MECHANICAL_CHECK_FAILED"
            if inspected["passed"]:
                mapping_issue = mapping_error(row, nodes_by_id)
                if mapping_issue: status = mapping_issue
            else:
                declared_steps = row.get("worked_steps")
                if isinstance(declared_steps, list) and any(isinstance(s, dict) and isinstance(s.get("expression"), str) and "//" in s["expression"] for s in declared_steps):
                    status = "EUCLIDEAN_CAPABILITY_PENDING_NOT_APP_EXECUTABLE"
            question = normalized(row.get("problem", "")) if isinstance(row.get("problem", ""), str) else ""
            if sample_id in seen_ids or question in seen_questions: status = "DUPLICATE_CASE"
            seen_ids.add(sample_id); seen_questions.add(question)
            numeric_overlap = bool(signatures & protected)
            exception = numeric_exceptions.get(sample_id)
            exception_applied = bool(
                status == "ACCEPTED_AUTHOR_QA" and numeric_overlap
                and question not in protected_questions and exception
                and exception.get("source_row_sha256") == row_sha(row))
            if question in protected_questions or (numeric_overlap and not exception_applied):
                status = "PROTECTED_DEVELOPMENT_CASE_COLLISION"
            exported = None
            if status == "ACCEPTED_AUTHOR_QA":
                exported = owner_export_row(row, owner_signoffs)
                status = exported["acceptance_status"]
            entry = {"sample_id": sample_id, "row_sha256": row_sha(exported or row),
                     "source_row_sha256": row_sha(row), "source": str(path.relative_to(root)),
                     "status": status, "mechanical": inspected,
                     "human_verified": bool(exported and exported["human_verified"]),
                     "teacher_certified": bool(exported and exported["teacher_certified"]),
                     "owner_human_reviewed": bool(exported and exported["owner_human_reviewed"]),
                     "source_role": exported["source_role"] if exported else None}
            manifest.append(entry); counts[status] += 1
            if exception_applied:
                entry["protected_numeric_overlap_adjudication"] = exception
                entry["numeric_test_independence_claimed"] = False
            checks["checked_step_expressions"] += sum(bool(e) for e in inspected["expanded_expressions"])
            if exported is not None:
                accepted.append(exported)
                source_accepted.append(row)
            else: pending.append({"row": row, "decision": entry})
    exports = root / "exports"
    artifacts = {"accepted_cases": write_rows(exports/"accepted_teacher_cases.jsonl", accepted),
                 "chat_train": write_rows(exports/"teacher_chat_train.jsonl", [v for r in accepted for v in chat_records(r)]),
                 "pending_cases": write_rows(root/"pending_cases.jsonl", pending),
                 "curation_manifest": write_rows(root/"curation_manifest.jsonl", manifest)}
    # Coverage is mathematical content; metadata certification does not fill slots.
    adjudication_path = root / "coverage_adjudications.jsonl"
    adjudications = read_rows(adjudication_path) if adjudication_path.exists() else []
    for decision in adjudications:
        evidence = (HERE.parent / decision["evidence_path"]).resolve()
        if (not evidence.is_relative_to((HERE / "evidence").resolve()) or not evidence.is_file()
                or decision.get("evidence_sha256") != sha(evidence.read_bytes())):
            raise ValueError("coverage audit evidence hash or path mismatch")
    coverage = coverage_for_cases(blueprint["nodes"], source_accepted, adjudications)
    write_json(root/"coverage_progress.json", coverage)
    remaining = [r for r in coverage if r["remaining_core_cases"]]
    report = {"schema_version": "primary_math_data_build.v1", "phase": "DATA_AUTHORING_AND_REVIEW",
              "automation_id": "t-o-d-li-u-to-n-ti-u-h-c-mathvisionkid", "training_started": False,
              "input_files": {str(p.relative_to(root)): sha(p.read_bytes()) for p in inputs},
              "draft_source_files": {str(p.relative_to(root)): sha(p.read_bytes()) for p in drafts},
              "blueprint_sha256": sha(blueprint_path.read_bytes()) if blueprint_path.exists() else None,
              "authored_cases": len(manifest), "decisions": dict(counts), "accepted_cases": len(accepted),
              "chat_train_rows": artifacts["chat_train"]["rows"], "checks": dict(checks),
              "grades_accepted": dict(Counter(r["grade"] for r in accepted)),
              "node_count": len(coverage), "core_nodes_complete": len(coverage)-len(remaining),
              "remaining_core_cases": sum(r["remaining_core_cases"] for r in coverage),
              "next_nodes": remaining[:5], "artifacts": artifacts,
              "protected_dataset_fingerprints": protected_fingerprints,
              "sealed_concept_challenge_read": False,
              "human_verified": bool(accepted) and all(r["human_verified"] for r in accepted),
              "teacher_certified": bool(accepted) and all(r["teacher_certified"] for r in accepted),
              "owner_human_reviewed": bool(accepted) and all(r["owner_human_reviewed"] for r in accepted),
              "human_teacher_verified_cases": sum(r["human_verified"] for r in accepted),
              "source_role": "HUMAN_TEACHER_VERIFIED" if accepted and all(r["human_verified"] for r in accepted) else "MIXED_VERIFICATION_SCOPES",
              "owner_human_signoffs_sha256": sha((root/"owner_human_signoffs.jsonl").read_bytes()) if owner_signoffs else None,
              "coverage_adjudications_sha256": sha(adjudication_path.read_bytes()) if adjudications else None,
              "reviewed_concept_coverage_groups": len(adjudications),
              "protected_numeric_overlap_exceptions_applied": sum(
                  "protected_numeric_overlap_adjudication" in item for item in manifest),
              "numeric_overlap_exception_policy_sha256": sha((root/"numeric_overlap_exception_policy.json").read_bytes())
                  if numeric_exceptions else None,
              "production_approved": False,
              "completion": False,
              "limits": ["Human/teacher flags record explicit owner attestations for enumerated row hashes; credentials are not independently authenticated.",
                         "Future standing approval is not a completed per-row human review; AI authorship remains traceable in frozen sources.",
                         "Canonical exclusion is bounded, not universal semantic equivalence.",
                         "Owner-authorized hash-bound numeric-overlap exceptions retain arithmetic overlap; those numeric tests are not independent for the overlapping calculations.",
                         "Neutral teacher chat is not an automatically valid application PlanDraft.",
                         "No claim of complete curriculum mastery or model accuracy; model not trained.",
                         "All variants of a case remain training-only; independent evaluation is still needed."]}
    write_json(root/"data_build_state.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args(); report = curate(args.root)
    print(json.dumps({k: report[k] for k in ("phase", "authored_cases", "accepted_cases", "chat_train_rows", "decisions", "remaining_core_cases")}, ensure_ascii=False))
