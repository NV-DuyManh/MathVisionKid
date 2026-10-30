"""Exact, deliberately bounded solver for two shares of one counted population.

Unknown wording returns None and keeps the independently reviewed cloud path.
The grammar mirrors Smart Quiz's verified relation, not a particular exercise.
"""
import re
from fractions import Fraction

from app.tutoring.service import _fold


def verified_plan(problem: str) -> dict | None:
    text = re.sub(r"\s+", " ", _fold(problem)).strip()
    text = re.sub(r"\s*\(\d+(?:[.,]\d+)? diem\)\s*", "", text).strip()
    if re.search(r"\b(khong|chua|them|bot|mat|sau khi|truoc khi)\b", text):
        return None
    fractions = re.findall(r"\d{1,3}\s*/\s*\d{1,3}", text)
    if len(fractions) != 2:
        return None
    units = {"cay": ("cây", "cay", "cay"), "sach": ("quyển sách", "quyen(?: sach)?", "sach"),
             "keo": ("viên kẹo", "vien(?: keo)?", "keo"), "vien bi": ("viên bi", "vien bi", "bi"),
             "bong hoa": ("bông hoa", "bong hoa", "hoa"), "qua bong": ("quả bóng", "qua bong", "bong")}
    for population, (unit, counter, category_prefix) in units.items():
        if len(re.findall(r"\d\s+so " + population + r"\b", text)) != 2:
            continue
        fraction = r"\d{1,3}\s*/\s*\d{1,3}"
        grammar = (r"[^0-9?]{1,160}" + fraction + " so " + population + r" la ([a-z ]{2,70})[,;.] ?(?:va )?"
                   + fraction + " so " + population + r" la ([a-z ]{2,70})[,;.] ?(?:so " + population
                   + r" )?con lai la ([a-z ]{2,70})\. biet (?:rang )?([^.?]{1,120})\. "
                   + r"hoi ([a-z ]*(?:tat ca|tong cong|tong so)[a-z ]*)bao nhieu " + counter + r"\??")
        match = re.fullmatch(grammar, text)
        if not match:
            return None
        categories = [match[i].strip() for i in (1, 2, 3)]
        if len(set(categories)) != 3 or any(
            not name.startswith(category_prefix + " ") or name in match[5]
            or re.search(r"\b(khong|hon|kem|sau|truoc|con|nhieu|it|va)\b", name) for name in categories
        ) or any(a != b and a.startswith(b + " ") for a in categories for b in categories):
            return None
        remainder = re.escape(categories[2])
        count_match = re.fullmatch(r"(?:so )?" + remainder
            + r" (?:co trong (?:vuon|thu vien|hop|gio|lop)(?: [a-z ]{1,40})? la|la|co) (\d{1,5}) " + counter, match[4])
        if not count_match:
            count_match = re.fullmatch(r"co (\d{1,5}) (?:quyen |vien )?" + remainder, match[4])
        if not count_match:
            return None
        try:
            a, b = (Fraction(re.sub(r"\s", "", item)) for item in fractions)
            count = int(count_match[1])
            remaining = 1 - a - b
            if min(a, b, remaining, count) <= 0:
                return None
            total = count / remaining
            if total > 10000 or any(v.denominator != 1 for v in (total, total*a, total*b)):
                return None
        except (ValueError, ZeroDivisionError):
            return None
        # The proof checks all groups as positive integers and conserves the whole.
        assert total*a + total*b + count == total
        descriptions = [
            ("Gộp hai phần đã biết", "Phân số chỉ hai nhóm đã biết là:",
             "Hai phân số trong đề cùng chỉ các phần của toàn bộ. Ta cộng các phần này để biết hai nhóm đã chiếm bao nhiêu phần.",
             "Em quy đồng các phân số đã cho, rồi cộng các tử số và giữ mẫu chung. Em tự tính kết quả, giữ phân số chính xác để dùng ở bước tiếp theo.",
             f"{fractions[0]} + {fractions[1]}", "phần", "Hai nhóm đã biết chiếm mấy phần của toàn bộ?"),
            ("Tìm phần còn lại", "Phân số chỉ nhóm còn lại là:",
             "Coi toàn bộ là một đơn vị. Nhóm còn lại ghép với hai nhóm đã biết vừa đủ toàn bộ, nên ta lấy toàn bộ trừ phần vừa tìm.",
             "Em dùng kết quả đã kiểm tra ở bước trước, viết một đơn vị thành phân số cùng mẫu, rồi thực hiện phép trừ. Phân số này chỉ phần còn lại, chưa phải số đồ vật.",
             "1 - {s0}", "phần", "Nhóm còn lại chiếm mấy phần của toàn bộ?"),
            ("Tìm số lượng toàn bộ", "Số lượng trong toàn bộ là:",
             f"Đề cho nhóm còn lại có {count} {unit}. Muốn tìm toàn bộ, ta lấy số lượng đã biết chia cho phân số tương ứng. Đây là phép tìm toàn bộ từ một phần đã biết.",
             "Em dùng phân số đã kiểm tra ở bước trước làm số chia. Khi chia cho một phân số, ta nhân với phân số đảo ngược của nó; em tự thực hiện phép tính và ghi đơn vị đếm.",
             f"{count} / {{s1}}", unit, "Toàn bộ có tất cả bao nhiêu?")]
        return {"topic": "Tìm toàn bộ từ phần còn lại", "goal": "Hiểu các phần, rồi tự tính số lượng toàn bộ.",
                "finalAnswerStep": 2, "steps": [
                    {"title": title, "solutionSentence": sentence, "explanation": why, "question": question,
                     "expression": expression, "unit": step_unit, "fractionNotation": True,
                     "guidance": [(f"Phần đã kiểm tra là {{s{index-1}}}. " if index else "") + why, how],
                     "initialGuidance": [(f"Phần đã kiểm tra là {{s{index-1}}}. " if index else "") + why, how], "hints": [why, how]}
                    for index, (title, sentence, why, how, expression, step_unit, question) in enumerate(descriptions)]}
    return None
