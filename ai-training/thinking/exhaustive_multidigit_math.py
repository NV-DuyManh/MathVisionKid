"""Pure, bounded-memory arithmetic extension; this module never writes a corpus.

The cloud publisher owns range locks, immutable shards, exclusions and commits.
Ordered arithmetic IDs retain the existing v1 scheme.  The fixed 1563/43
regression case remains in FULL CORPUS but is ineligible for model train/val/test.
No sealed evaluation data, model, network or storage operations occur here.
"""
from __future__ import annotations

import hashlib
import inspect
import re
from decimal import Decimal, ROUND_FLOOR, localcontext
from fractions import Fraction

import exhaustive_primary_math as base
import exhaustive_curriculum_scope as scope_module

VERSION = "exhaustive_multidigit_math.v1"
TEMPLATE_VERSION = "observable_multidigit_teaching.v1"
REGRESSION_PAIRS = frozenset({("/", 1563, 43)})
ACCEPTANCE = "ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED"


def _place(index):
    return base.PLACES[index] if index < len(base.PLACES) else f"10 mũ {index}"


def _step(title, reason, expression, result, explanation):
    return base.step(title, reason, expression, result, explanation)


def multiplication_columns(a, b):
    """Keep the supplied order: multiply a by every digit of b, then align."""
    partials, rows, details = [], [], []
    for offset, digit_char in enumerate(reversed(str(b))):
        multiplier_digit = int(digit_char)
        carry, unshifted, column_details, texts = 0, 0, [], []
        for index, char in enumerate(reversed(str(a))):
            x, incoming = int(char), carry
            total = x * multiplier_digit + incoming
            out_digit, carry = total % 10, total // 10
            unshifted += out_digit * 10 ** index
            column_details.append({"index": index, "digit": x,
                                   "incoming_carry": incoming, "total": total,
                                   "output_digit": out_digit, "outgoing_carry": carry})
            texts.append(f"Hàng {_place(index)} của số bị nhân: {x} × {multiplier_digit}"
                         + (f" + {incoming} nhớ" if incoming else "")
                         + f" = {total}; ghi {out_digit}, nhớ {carry}.")
        if carry:
            unshifted += carry * 10 ** len(str(a))
            texts.append(f"Đã hết chữ số của số bị nhân, ghi phần nhớ cuối {carry} ở bên trái.")
        shifted = unshifted * 10 ** offset
        partials.append(shifted)
        detail = {"multiplier_place": offset, "multiplier_digit": multiplier_digit,
                  "columns": column_details, "final_carry": carry,
                  "unshifted_partial": unshifted, "shifted_partial": shifted}
        details.append(detail)
        alignment = ("Đây là tích riêng của hàng đơn vị, không dịch hàng."
                     if offset == 0 else
                     f"Chữ số {multiplier_digit} ở hàng {_place(offset)} có giá trị "
                     f"{multiplier_digit * 10 ** offset}; dịch tích riêng {offset} hàng sang trái, "
                     f"được {shifted}.")
        if multiplier_digit == 0:
            alignment += " Hàng này có chữ số 0 nên tích riêng bằng 0; vẫn giữ đúng vị trí các hàng sau."
        rows.append(_step(
            f"Tích riêng theo hàng {_place(offset)} của thừa số thứ hai",
            "Phân tích thừa số thứ hai theo giá trị từng hàng; nhân từ hàng đơn vị và cộng phần nhớ.",
            f"{a}*{multiplier_digit * 10 ** offset}", shifted,
            " ".join(texts) + " " + alignment))
    result = sum(partials)
    rows.append(_step(
        "Cộng các tích riêng đã thẳng hàng",
        "Tính phân phối cho phép cộng các tích riêng theo đúng giá trị hàng để được toàn bộ tích.",
        "+".join(map(str, partials)), result,
        "Đặt các chữ số cùng hàng thẳng cột rồi cộng các tích riêng: "
        + " + ".join(map(str, partials)) + f" = {result}."))
    # Independent distributive grid uses digit pairs of both factors.  No trace
    # values or answer product are used to build this reconstruction.
    grid = sum(int(x) * int(y) * 10 ** (i + j)
               for i, x in enumerate(reversed(str(a)))
               for j, y in enumerate(reversed(str(b))))
    rows.append(_step(
        "Kiểm bằng phân tích cả hai thừa số",
        "Cộng các đóng góp của từng cặp hàng là một cách tái dựng tích độc lập với phần nhớ đã ghi.",
        None, grid,
        f"Tách {a} và {b} theo các hàng, nhân từng cặp phần rồi cộng lại được {grid}. "
        + (f"Kiểm thêm {result} : {b} = {a}." if b else
           "Thừa số thứ hai bằng 0 nên mọi phần của tích đều bằng 0; không kiểm bằng phép chia cho 0.")))
    return result, rows, {"multiplication_partial_products": details,
                          "distributive_grid_oracle": grid}


def division_columns(a, b):
    """Digit recurrence with explicit internal/trailing zero quotient digits."""
    if b <= 0:
        raise ValueError("A numeric division requires divisor > 0")
    remainder, quotient, started = 0, 0, False
    details, steps = [], []
    digits = str(a)
    for index, char in enumerate(digits):
        digit, previous = int(char), remainder
        partial = previous * 10 + digit
        # The teaching trace finds the next digit among 0..9, rather than
        # obtaining the final quotient with integer division.
        qdigit = max(candidate for candidate in range(10) if candidate * b <= partial)
        remainder = partial - qdigit * b
        write_digit = started or qdigit != 0 or index == len(digits) - 1
        quotient = quotient * 10 + qdigit
        if write_digit:
            started = True
        detail = {"input_index": index, "brought_down_digit": digit,
                  "previous_remainder": previous, "partial_dividend": partial,
                  "quotient_digit": qdigit, "remainder": remainder,
                  "quotient_digit_written": write_digit,
                  "quotient_prefix": quotient}
        details.append(detail)
        bringdown = (f"Xét chữ số đầu {digit}." if index == 0 else
                     f"Hạ chữ số {digit} cạnh phần còn {previous}: {previous} × 10 + {digit} = {partial}.")
        if not write_digit:
            action = (f"{partial} < {b}; chưa đủ một nhóm và còn chữ số để hạ, "
                      "chưa ghi chữ số 0 đầu thương.")
        elif qdigit == 0:
            action = (f"{partial} < {b}; ghi chữ số 0 tại vị trí đang xét trong thương, "
                      "không bỏ vị trí này.")
        else:
            action = f"Chọn chữ số thương {qdigit}, vì {qdigit} × {b} ≤ {partial} < {qdigit + 1} × {b}."
        steps.append(_step(
            f"Chia sau khi xét chữ số thứ {index + 1}",
            "Đọc số bị chia từ trái sang phải; mỗi lần hạ một chữ số, tìm số nhóm đủ và giữ phần còn nhỏ hơn số chia.",
            f"{qdigit}*{b}+{remainder}", partial,
            bringdown + " " + action
            + f" Bớt {qdigit} × {b} = {qdigit * b}, còn {remainder}; 0 ≤ {remainder} < {b}."))
    steps.append(_step(
        "Ghép thương và kiểm phép chia",
        "Các chữ số thương phải giữ đúng thứ tự và cả các chữ số 0 ở giữa/cuối; thương nhân số chia cộng số dư khôi phục số bị chia.",
        f"{b}*{quotient}+{remainder}", a,
        f"Ghép các chữ số thương được {quotient}; số dư là {remainder}. "
        f"Kiểm {a} = {b} × {quotient} + {remainder} và 0 ≤ {remainder} < {b}; "
        "phần còn nhỏ hơn số chia nên không lập thêm được nhóm đủ."))
    return quotient, remainder, steps, {"long_division_digits": details,
                                       "quotient": quotient, "remainder": remainder,
                                       "modulo_oracle_metadata_only": f"{a}%{b}"}


def hints(op):
    if op not in ("*", "/"):
        return base.hints(op)
    prompts = {
        "*": [
            ("Đặt hai thừa số sao cho các chữ số cùng hàng thẳng cột; xét các hàng của thừa số thứ hai.",
             "Em sẽ bắt đầu nhân với chữ số ở hàng nào?"),
            ("Tạo từng tích riêng, cộng phần nhớ; đặt mỗi tích riêng theo giá trị hàng của chữ số nhân.",
             "Nếu chữ số nhân ở hàng chục hoặc hàng trăm, tích riêng phải nằm ở vị trí nào?"),
            ("Cộng các tích riêng đã thẳng hàng rồi kiểm bằng phân tích theo hàng hoặc phép chia có số chia khác không.",
             "Phép kiểm có dùng đủ các hàng và bảo toàn giá trị từng hàng không?")],
        "/": [
            ("Kiểm số chia khác không; xét lần lượt các chữ số của số bị chia từ trái sang phải.",
             "Với phần đang xét, em cần tìm chữ số thương thỏa điều kiện nào?"),
            ("Ở mỗi lượt, nhân chữ số thương với số chia, trừ rồi hạ chữ số kế tiếp; giữ vị trí thương khi chưa đủ một nhóm.",
             "Một vị trí trong thương có thể bị bỏ mất nếu phần đang xét nhỏ hơn số chia không?"),
            ("Ghép các chữ số thương theo đúng thứ tự, rồi nhân thương với số chia và cộng số dư để kiểm.",
             "Phép kiểm có khôi phục số bị chia và số dư có không âm, nhỏ hơn số chia không?")],
    }
    return [{"level": i + 1, "hint": h, "question": q}
            for i, (h, q) in enumerate(prompts[op])]


def _scope(op, a, b, metadata):
    try:
        return scope_module.classify(op, a, b, metadata)
    except FileNotFoundError:
        # The previous cloud-only phase removed payload evidence locally.  No
        # invented verification or mandatory-curriculum claim replaces it.
        return {"classifier_version": VERSION,
                "grade": 4,
                "curriculum_scope": "ENRICHMENT_PENDING_SOURCE_REVALIDATION",
                "grade_is_recommendation_only": True,
                "current_node_id": None,
                "ordered_pair_retained": True,
                "source_evidence": scope_module.EVIDENCE_PATH,
                "source_evidence_sha256": scope_module.EVIDENCE_SHA256,
                "reason": "Nguồn đối chiếu đã chuyển lên Drive; chưa đọc lại nguồn hash-bound trong lượt này. Lớp 4 là gợi ý bố trí, chưa gán yêu cầu bắt buộc."}


def _numeric_expressions(op, a, b, steps, metadata):
    """Include arithmetic printed inside explanations, not only step.expression."""
    expressions = [s["expression"] for s in steps if s["expression"] is not None]
    if op == "+":
        carry, place = 0, 1
        while place <= max(a, b) or carry or place == 1:
            x, y = a // place % 10, b // place % 10
            expressions.append(f"{x}+{y}" + (f"+{carry}" if carry else ""))
            carry = (x + y + carry) // 10
            place *= 10
    elif op == "-":
        for s in steps:
            for x, y in re.findall(r"(\d+) − (\d+) =", s["explanation"]):
                expressions.append(f"{x}-{y}")
    elif op == "*":
        for partial in metadata["multiplication_partial_products"]:
            for c in partial["columns"]:
                expressions.append(f"{c['digit']}*{partial['multiplier_digit']}"
                                   + (f"+{c['incoming_carry']}" if c["incoming_carry"] else ""))
        if b:
            expressions.append(f"{a * b}/{b}")
    elif op == "/":
        for d in metadata["long_division_digits"]:
            if d["input_index"]:
                expressions.append(f"{d['previous_remainder']}*10+{d['brought_down_digit']}")
            expressions.append(f"{d['quotient_digit']}*{b}")
            if d["quotient_digit"]:
                expressions.append(f"{d['quotient_digit'] + 1}*{b}")
    return list(dict.fromkeys(expressions))


def make_row(op, a, b):
    """Return one deterministic source case; no filesystem side effects."""
    aliases = {"×": "*", "÷": "/", ":": "/", "−": "-"}
    op = aliases.get(op, op)
    if op not in ("+", "-", "*", "/", "invalid_division"):
        raise ValueError("Unsupported operation")
    if type(a) is not int or type(b) is not int or not (0 <= a <= 999999999 and 0 <= b <= 999999999):
        raise ValueError("Exact nonnegative integers at most 999999999 required")
    if op == "-" and a < b:
        raise ValueError("Negative results are outside this natural-number template")
    if op in ("+", "-") and max(a, b, a + b if op == "+" else a - b) > 9999999:
        raise ValueError("Reused reviewed column-place helper supports through millions only")
    if op == "/" and b == 0:
        op = "invalid_division"
    if op == "invalid_division" and b != 0:
        raise ValueError("Guard requires divisor zero")
    if op == "*" and min(a, b) > 999 and a not in (1000,) and b not in (1000,):
        raise ValueError("Reviewed multiplication domain requires a factor <=999 or power-of-ten factor1000")
    metadata = {}
    if op in ("+", "-"):
        if op == "+":
            value, trace, positions = base.addition_columns(a, b)
            metadata["carry_positions"] = positions
            topic, label = "multidigit_addition", "Tổng"
            operation_reason = "Gộp hai số hạng; cộng từ hàng đơn vị, đổi mỗi nhóm đủ mười sang hàng cao hơn."
            check_expr, check_value = f"{value}-{b}", a
        else:
            value, trace, positions = base.subtraction_columns(a, b)
            metadata["borrow_positions"] = positions
            topic, label = "multidigit_subtraction", "Hiệu"
            operation_reason = "Bớt số trừ khỏi số bị trừ; đổi nhóm khi chưa đủ bớt và cập nhật mọi hàng cho đi."
            check_expr, check_value = f"{value}+{b}", a
        steps = [_step("Đặt tính theo hàng", operation_reason, f"{a}{op}{b}", value, " ".join(trace)),
                 _step("Kiểm bằng phép tính ngược", "Phép tính ngược phải khôi phục số ban đầu.",
                       check_expr, check_value, f"{check_expr} = {check_value}, đúng số ban đầu.")]
        answers = [{"quantity": label, "result": str(value), "unit": ""}]
        problem = f"Tính {a} {'+' if op == '+' else '−'} {b}; giải thích cách đặt tính và kiểm lại."
    elif op == "*":
        value, steps, metadata = multiplication_columns(a, b)
        topic = "multidigit_multiplication"
        problem = f"Tính {a} × {b}; giải thích đặt tính, các tích riêng và cách kiểm."
        answers = [{"quantity": "Tích", "result": str(value), "unit": ""}]
    elif op == "/":
        q, r, steps, metadata = division_columns(a, b)
        topic = "multidigit_division_exact" if r == 0 else "multidigit_division_remainder"
        problem = f"Chia {a} cho {b}; đặt tính theo từng lượt, tìm thương và số dư, rồi kiểm lại."
        answers = [{"quantity": "Thương", "result": str(q), "unit": ""},
                   {"quantity": "Số dư", "result": str(r), "unit": ""}]
    else:
        topic = "division_by_zero_recognition"
        problem = f"Có thể tính {a} : 0 và ghi một thương xác định không? Giải thích điều kiện phép chia."
        explanation = (f"Mọi số nhân với 0 đều bằng 0, không thể được {a}." if a else
                       "Mọi số nhân với 0 đều bằng 0, nên quan hệ nhân ngược không chọn được đúng một thương.")
        steps = [_step("Kiểm số chia", "Phép chia số học chỉ xác định khi số chia khác không.", None,
                       "không xác định", explanation + " Vì vậy không ghi một thương số học.")]
        answers = [{"quantity": "Tính xác định", "result": "không xác định vì số chia bằng 0", "unit": ""}]
        metadata = {"invalid_division_not_numeric_answer": True}
    scope = _scope(op, a, b, metadata)
    hs = hints(op)
    signatures = [] if op == "invalid_division" else [base.numeric_group("%" if op == "/" else op, a, b)]
    if op == "/" and metadata["remainder"] == 0:
        signatures.append(base.numeric_group("/", a, b))
    metadata["checked_numeric_expressions"] = _numeric_expressions(op, a, b, steps, metadata)
    for expression in metadata["checked_numeric_expressions"]:
        signature = base.expression_group(expression)
        if signature not in signatures:
            signatures.append(signature)
    for index, s in enumerate(steps):
        s["step_id"] = f"s{index}"
        if s["expression"]:
            signature = base.expression_group(s["expression"])
            if signature not in signatures:
                signatures.append(signature)
    primary = signatures[0] if signatures else base.digest(f"invalid/{a}/{b}".encode())
    regression = (op, a, b) in REGRESSION_PAIRS
    return {
        "sample_id": base.make_id(op, a, b), "case_group_id": "math_" + primary,
        "case_kind": "invalid_operation_recognition" if op == "invalid_division" else "worked_arithmetic",
        "split": "regression_only" if regression else "train_candidate", "grade": scope["grade"],
        "topic": topic, "problem": problem,
        "givens": [{"id": "g0", "text": "Số thứ nhất", "value": str(a), "unit": ""},
                   {"id": "g1", "text": "Số thứ hai", "value": str(b), "unit": ""}],
        "requested_quantity": "; ".join(x["quantity"] for x in answers), "student_work": None,
        "initial_guidance": [hs[0]["hint"]], "hints": hs, "worked_steps": steps,
        "expected_answer": answers, "can_solve": True, "quality_status": "ACCEPTED_VALIDATED",
        "acceptance_status": ACCEPTANCE,
        "quality_validation": {"exact_integer_fraction_decimal_oracle": True,
                               "independent_trace_reconstruction": True,
                               "reviewed_template_semantics": True,
                               "every_row_human_or_LLM_review_claimed": False},
        "provenance": {"generation_method": "DETERMINISTIC_EXACT_ARITHMETIC_WITH_REVIEWED_TEACHING_TEMPLATE",
                       "generator_version": VERSION, "template_version": TEMPLATE_VERSION,
                       "authorship_origin": "PROGRAMMATIC_TEMPLATE",
                       "acceptance_basis": "OWNER_AUTHORIZED_VALIDATION",
                       "human_content_review_completed": False, "human_verified": False,
                       "teacher_certified": False, "independent_external_review": False},
        "curriculum_assignment": scope,
        "coverage": {"mode": "EXHAUSTIVE", "ordered_input_pair": [a, b], "operation": op,
                     "subtype": topic, "minimum_grade_for_this_representation": scope["grade"]},
        "canonical_signatures": signatures, "operation_metadata": metadata,
        "training_eligible": not regression,
        "training_exclusions": ["FIXED_GENERATOR_REGRESSION_NOT_GENERALIZATION_DATA"] if regression else [],
        "evaluation_eligible": not regression,
    }


def chat_records(row):
    """The base neutral serializer, with a fail-closed fixed-regression gate."""
    if not row.get("training_eligible", True) or row.get("split") == "regression_only":
        return
    for record in base.chat_records(row):
        record["acceptance_status"] = ACCEPTANCE
        yield record


def validate_row(row):
    """Check all actual answers, step expressions, digit records and IDs."""
    op = row["coverage"]["operation"]
    a, b = row["coverage"]["ordered_input_pair"]
    if [g["value"] for g in row["givens"]] != [str(a), str(b)]:
        raise ValueError("Givens differ from ordered pair")
    if row["sample_id"] != base.make_id(op, a, b):
        raise ValueError("Unstable sample ID")
    primary = (base.numeric_group("%" if op == "/" else op, a, b)
               if op != "invalid_division" else base.digest(f"invalid/{a}/{b}".encode()))
    if row["case_group_id"] != "math_" + primary:
        raise ValueError("Unstable case group")
    if row["student_work"] is not None or row["can_solve"] is not True:
        raise ValueError("Unprovided student work or incorrect solve status")
    if any(s["step_id"] != f"s{i}" or s["unit"] != "" for i, s in enumerate(row["worked_steps"])):
        raise ValueError("Step identity/unit mismatch")
    ans = [x["result"] for x in row["expected_answer"]]
    with localcontext() as ctx:
        ctx.prec = 80
        if op in ("+", "-", "*"):
            fa, fb, da, db = Fraction(a), Fraction(b), Decimal(a), Decimal(b)
            fv = fa + fb if op == "+" else fa - fb if op == "-" else fa * fb
            dv = da + db if op == "+" else da - db if op == "-" else da * db
            if ans != [str(fv.numerator)] or fv.denominator != 1 or dv != Decimal(ans[0]):
                raise ValueError("Fraction/Decimal answer mismatch")
        elif op == "/":
            q, r = map(int, ans)
            fraction_q = Fraction(a, b).__floor__()
            decimal_q = int((Decimal(a) / Decimal(b)).to_integral_value(rounding=ROUND_FLOOR))
            if q != fraction_q or q != decimal_q or b * q + r != a or not 0 <= r < b:
                raise ValueError("Euclidean identity/Fraction/Decimal quotient mismatch")
        elif op == "invalid_division":
            if b != 0 or ans != ["không xác định vì số chia bằng 0"]:
                raise ValueError("Invalid zero-divisor guard")
        else:
            raise ValueError("Unknown operation")
    for s in row["worked_steps"]:
        if s["expression"] is not None:
            if "%" in s["expression"] or "//" in s["expression"]:
                raise ValueError("Modulo/floor division must remain oracle metadata")
            if base.exact_expression(s["expression"]) != Fraction(s["result"]):
                raise ValueError("Worked expression mismatch")
            if base.expression_group(s["expression"]) not in row["canonical_signatures"]:
                raise ValueError("Worked expression protection signature omitted")
    if row["hints"] != hints(op) or row["initial_guidance"] != [hints(op)[0]["hint"]]:
        raise ValueError("Hints differ from semantically reviewed answer-free template")
    if row["acceptance_status"] != ACCEPTANCE or row["provenance"]["human_verified"]:
        raise ValueError("Incorrect acceptance/provenance")
    m = row["operation_metadata"]
    if m["checked_numeric_expressions"] != _numeric_expressions(op, a, b, row["worked_steps"], m):
        raise ValueError("An embedded worked/check expression was omitted")
    for expression in m["checked_numeric_expressions"]:
        base.exact_expression(expression)
        if base.expression_group(expression) not in row["canonical_signatures"]:
            raise ValueError("An embedded arithmetic protection signature was omitted")
    if op == "*":
        total = 0
        if len(m["multiplication_partial_products"]) != len(str(b)):
            raise ValueError("Missing partial product")
        for offset, item in enumerate(m["multiplication_partial_products"]):
            digit = b // 10 ** offset % 10
            if item["multiplier_digit"] != digit or item["multiplier_place"] != offset:
                raise ValueError("Wrong multiplier place")
            if len(item["columns"]) != len(str(a)):
                raise ValueError("Missing multiplicand digit")
            carry, constructed = 0, 0
            for index, cell in enumerate(item["columns"]):
                x = a // 10 ** index % 10
                raw = x * digit + carry
                if cell != {"index": index, "digit": x, "incoming_carry": carry, "total": raw,
                            "output_digit": raw % 10, "outgoing_carry": raw // 10}:
                    raise ValueError("Carry trace mismatch")
                constructed += raw % 10 * 10 ** index
                carry = raw // 10
            constructed += carry * 10 ** len(str(a))
            if (item["final_carry"], item["unshifted_partial"], item["shifted_partial"]) != (
                    carry, constructed, constructed * 10 ** offset):
                raise ValueError("Partial alignment mismatch")
            total += item["shifted_partial"]
        grid = sum(int(x) * int(y) * 10 ** (i + j) for i, x in enumerate(reversed(str(a)))
                   for j, y in enumerate(reversed(str(b))))
        if total != a * b or m["distributive_grid_oracle"] != grid or grid != total:
            raise ValueError("Distributive reconstruction mismatch")
    elif op == "/":
        if len(m["long_division_digits"]) != len(str(a)):
            raise ValueError("Missing bring-down digit")
        previous, prefix, started = 0, 0, False
        for index, (char, item) in enumerate(zip(str(a), m["long_division_digits"])):
            partial = previous * 10 + int(char)
            digit = partial // b
            remainder = partial - digit * b
            written = started or digit != 0 or index == len(str(a)) - 1
            prefix = prefix * 10 + digit
            if item != {"input_index": index, "brought_down_digit": int(char),
                        "previous_remainder": previous, "partial_dividend": partial,
                        "quotient_digit": digit, "remainder": remainder,
                        "quotient_digit_written": written, "quotient_prefix": prefix}:
                raise ValueError("Long-division digit/zero-position mismatch")
            started = started or written
            previous = remainder
        if (prefix, previous) != (m["quotient"], m["remainder"]) or list(map(str, (prefix, previous))) != ans:
            raise ValueError("Final quotient/remainder differs from digit trace")
    elif op in ("+", "-"):
        key = "carry_positions" if op == "+" else "borrow_positions"
        if m[key] != scope_module.exchange_positions(op, a, b):
            raise ValueError("Carry/borrow metadata mismatch")
    fixed = (op, a, b) in REGRESSION_PAIRS
    if fixed and (row.get("training_eligible") or row.get("evaluation_eligible") or row["split"] != "regression_only"):
        raise ValueError("Fixed regression leaked into model data")
    # Hash actual complete row contents for downstream evidence binding.
    return {"sample_id": row["sample_id"], "validated": True,
            "row_sha256": hashlib.sha256(base.dumps(row).encode("utf-8")).hexdigest(),
            "oracle": "Fraction+Decimal+digit_trace+inverse_or_distributive_reconstruction"}


def finite_domain_specs(maximum=100, dividend_maximum=100):
    """Disjoint bounded plans, never claims that these rows were materialized."""
    specs = []
    if type(maximum) is not int or not 10 <= maximum <= 1000:
        raise ValueError("Finite multiplication bound must be10..1000")
    if type(dividend_maximum) is not int or not 0 <= dividend_maximum <= 99999:
        raise ValueError("Finite dividend bound must be0..99999")
    # Ordered bounded square minus the preexisting 0..10 square.  Splitting
    # by second operand gives one/two/three-digit-factor coverage plus1000.
    for low, high, name in ((0, 9, "one_digit"), (10, 99, "two_digits"),
                            (100, 999, "three_digits"), (1000, 1000, "factor1000")):
        high = min(high, maximum)
        if low > high:
            continue
        old = 11 * max(0, min(high, 10) - low + 1)
        count = (maximum + 1) * (high - low + 1) - old
        specs.append({"domain_id": f"multiplication_0_{maximum}_" + name, "operation": "*",
                      "a_start": 0, "a_stop_exclusive": maximum + 1,
                      "b_start": low, "b_stop_exclusive": high + 1,
                      "exclude_previous_square_max": 10, "expected_pairs": count,
                      "status": "PLANNED_NOT_MATERIALIZED", "ordered_inputs": True})
    for low, high, name in ((10, 99, "two_digits"), (100, 999, "three_digits")):
        specs.append({"domain_id": f"division_dividend_0_{dividend_maximum}_divisor_" + name,
                      "operation": "/", "a_start": 0, "a_stop_exclusive": dividend_maximum + 1,
                      "b_start": low, "b_stop_exclusive": high + 1,
                      "expected_pairs": (dividend_maximum + 1) * (high - low + 1),
                      "status": "PLANNED_NOT_MATERIALIZED", "ordered_inputs": True})
    return specs


def iter_domain_pairs(spec):
    """Publisher may bound a or use cursor; emits stable lexicographic pairs."""
    for a in range(spec["a_start"], spec["a_stop_exclusive"]):
        for b in range(spec["b_start"], spec["b_stop_exclusive"]):
            old = spec.get("exclude_previous_square_max", -1)
            if a <= old and b <= old:
                continue
            yield a, b


def template_fingerprint():
    source = "".join(inspect.getsource(f) for f in (
        _place, _step, multiplication_columns, division_columns, hints, _scope,
        _numeric_expressions, make_row, chat_records, validate_row,
        finite_domain_specs, iter_domain_pairs, base.step, base.hints,
        base.addition_columns, base.subtraction_columns, base.chat_records,
        base.make_id, base.numeric_group, base.expression_group))
    source += inspect.getsource(scope_module.classify) + inspect.getsource(scope_module.exchange_positions)
    constants = repr((base.PLACES, sorted(REGRESSION_PAIRS), ACCEPTANCE,
                      scope_module.EVIDENCE_SHA256, scope_module.ANNEX_SHA256))
    return hashlib.sha256((source + VERSION + TEMPLATE_VERSION + constants).encode("utf-8")).hexdigest()
