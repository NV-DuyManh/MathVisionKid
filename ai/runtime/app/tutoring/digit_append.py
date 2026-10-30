"""Exact, deliberately bounded solver for writing a digit to the right of an unknown number.

When appending digit d (0 <= d <= 9) to the right of integer x:
  new_number = 10 * x + d
Difference:
  (10 * x + d) - x = 9 * x + d = D
  x = (D - d) / 9

Unknown wording returns None and keeps the independently reviewed cloud path.
"""
import re

from app.tutoring.service import _fold


def extract_digit_append(problem: str) -> tuple[int, int, int] | None:
    text = re.sub(r"[,;]", " ", _fold(problem))
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s*\(\s*\d+(?:[.,]\d+)?\s*diem\s*\)\s*", "", text).strip()
    text = re.sub(
        r"^(?:de(?:\s+bai)?|bai(?:\s+tap)?(?:\s+so)?\s*\d+[a-z]?|cau\s*\d+[a-z]?|vi\s+du(?:\s+\d+)?)\s*[:.)-]?\s*",
        "",
        text,
    ).strip()

    # Must be writing to the right, not to the left or other operations
    if "ben trai" in text or re.search(r"\b(khong|chua|bot|mat|sau khi|truoc khi)\b", text):
        return None
    if not re.search(r"\bben\s+phai\b", text):
        return None

    # Extract digit d: single digit from 0 to 9
    digit_match = re.search(
        r"(?:viet\s+them|them)\s+(?:mot\s+)?(?:chu\s+)?so\s+(\d)\s+(?:vao\s+)?ben\s+phai\b",
        text,
    )
    if not digit_match:
        digit_match = re.search(
            r"(?:viet|them)(?:\s+them)?\s+(?:vao\s+)?ben\s+phai(?:\s+so\s+do)?(?:\s+mot)?\s+(?:chu\s+)?so\s+(\d)\b",
            text,
        )
    if not digit_match:
        return None

    # Extract difference D
    diff_match = re.search(
        r"(?:so\s+moi\s+)?(?:lon\s+hon|hon)\s+(?:so\s+(?:phai\s+tim|da\s+cho|ban\s+dau|cu|can\s+tim|do)|so\s+do)\s+(\d+)\s*(?:don\s+vi)?\b",
        text,
    )
    if not diff_match:
        diff_match = re.search(
            r"(?:duoc\s+so\s+moi\s+)?(?:lon\s+hon|hon)\s+[^0-9]{1,40}?\s*(\d+)\s*(?:don\s+vi)?\b",
            text,
        )
    if not diff_match:
        return None

    # Question check: must ask to find the original number
    if not re.search(
        r"(?:tim\s+(?:mot\s+)?so|so\s+(?:do|phai\s+tim|can\s+tim|ban\s+dau)\s+la\s+bao\s+nhieu)",
        text,
    ):
        return None

    d = int(digit_match.group(1))
    D = int(diff_match.group(1))

    if not (0 <= d <= 9) or D <= d or (D - d) % 9 != 0:
        return None

    x = (D - d) // 9
    if x <= 0:
        return None

    # Exact arithmetic verification:
    new_number = x * 10 + d
    if new_number - x != D or str(new_number) != f"{x}{d}":
        return None

    return d, D, x


def verified_plan(problem: str) -> dict | None:
    extracted = extract_digit_append(problem)
    if not extracted:
        return None
    d, D, _ = extracted

    step0_title = "Tìm 9 lần số cần tìm"
    step0_sentence = "9 lần số cần tìm là:"
    step0_why = (
        f"Khi viết thêm chữ số {d} vào bên phải một số thì số mới bằng 10 lần số ban đầu cộng thêm {d} đơn vị. "
        f"Nếu bớt {d} đơn vị ở số mới thì số mới gấp 10 lần số cần tìm, và hiệu hai số khi đó bằng 9 lần số cần tìm."
    )
    step0_how = (
        f"Em lấy hiệu đã cho trừ đi chữ số viết thêm: {D} - {d}. "
        "Em tự thực hiện phép trừ để tìm giá trị của 9 lần số cần tìm nhé."
    )
    step0_question = f"Khi bớt chữ số {d} ở hàng đơn vị của số mới thì 9 lần số cần tìm bằng bao nhiêu?"
    step0_guidance = [
        f"Khi viết thêm chữ số {d} vào bên phải một số, số mới bằng 10 lần số ban đầu cộng thêm {d} đơn vị. Coi số cần tìm là 1 phần thì số mới gồm 10 phần như thế và thêm {d} đơn vị.",
        f"Đề bài cho biết số mới hơn số cần tìm {D} đơn vị. Nếu ta bớt đi {d} đơn vị ở số mới thì hiệu giữa số mới và số cần tìm sẽ là 10 trừ 1, tức là 9 lần số cần tìm.",
        step0_how,
    ]
    step0_initial = [
        f"Khi viết thêm chữ số {d} vào bên phải một số, số mới bằng 10 lần số ban đầu cộng thêm {d} đơn vị. Coi số cần tìm là 1 phần thì số mới gồm 10 phần như thế và thêm {d} đơn vị.",
        f"Đề bài cho biết số mới hơn số cần tìm {D} đơn vị. Nếu ta bớt đi {d} đơn vị ở số mới thì hiệu giữa số mới và số cần tìm sẽ là 10 trừ 1, tức là 9 lần số cần tìm.",
    ]
    step0_hints = [
        f"Em lấy hiệu {D} trừ đi chữ số {d} viết thêm ở hàng đơn vị.",
        f"Em thực hiện phép tính {D} - {d} để tìm 9 lần số cần tìm.",
    ]

    step1_title = "Tìm số cần tìm"
    step1_sentence = "Số cần tìm là:"
    step1_why = (
        "Muốn tìm số cần tìm, ta lấy giá trị 9 lần số đó vừa tìm được chia cho 9."
    )
    step1_how = (
        "Em thực hiện phép tính {s0} : 9 để tìm ra số cần tìm nhé."
    )
    step1_question = "Số cần tìm là bao nhiêu?"
    step1_guidance = [
        "Ở bước trước, em đã tính được 9 lần số cần tìm là {s0}.",
        "Vì 9 lần số cần tìm bằng {s0}, nên muốn tìm số ban đầu ta chỉ cần lấy kết quả đó chia đều cho 9 phần bằng nhau.",
        step1_how,
    ]
    step1_initial = [
        "Ở bước trước, em đã tính được 9 lần số cần tìm là {s0}.",
        "Vì 9 lần số cần tìm bằng {s0}, nên muốn tìm số ban đầu ta chỉ cần lấy kết quả đó chia đều cho 9 phần bằng nhau.",
    ]
    step1_hints = [
        "Em lấy kết quả 9 lần số cần tìm vừa tính được ở bước trước chia cho 9.",
        "Em thực hiện phép chia {s0} : 9 để tìm số ban đầu.",
    ]

    return {
        "topic": "Tìm số khi viết thêm chữ số vào bên phải",
        "goal": "Tìm 9 lần số cần tìm, rồi tính số cần tìm ban đầu.",
        "finalAnswerStep": 1,
        "steps": [
            {
                "title": step0_title,
                "solutionSentence": step0_sentence,
                "explanation": step0_why,
                "question": step0_question,
                "expression": f"{D} - {d}",
                "unit": "đơn vị",
                "fractionNotation": False,
                "guidance": step0_guidance,
                "initialGuidance": step0_initial,
                "hints": step0_hints,
            },
            {
                "title": step1_title,
                "solutionSentence": step1_sentence,
                "explanation": step1_why,
                "question": step1_question,
                "expression": "{s0} / 9",
                "unit": "đơn vị",
                "fractionNotation": False,
                "guidance": step1_guidance,
                "initialGuidance": step1_initial,
                "hints": step1_hints,
            },
        ],
    }
