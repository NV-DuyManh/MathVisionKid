"""Exact, deliberately bounded solver for two shares of one counted population.

Unknown wording returns None and keeps the independently reviewed cloud path.
The grammar mirrors Smart Quiz's verified relation, not a particular exercise.
"""
import re
import unicodedata
from fractions import Fraction

from app.tutoring.service import _fold


def subject_pattern():
    person = r"(?:ban|be|bac|co|chu) [a-z]{1,20}(?: [a-z]{1,20}){0,3}"
    place = r"(?:vuon(?: cay)?|thu vien|hop|gio|lop)(?: (?:nha|cua) " + person + r")?"
    return r"(?:trong )?(?:(?:mot )?" + place + "|" + person + ")"


def same_context(source, question):
    stated = re.match('(' + subject_pattern() + r') co ', source)
    asked = re.sub(r'(?:^| )(?:co )?(?:tat ca|tong cong|tong so)(?: |$).*', '', question).strip()
    count_place = re.search(r' co trong ([a-z ]{1,70}) la [0-9]', source)
    if not stated:
        return False
    def identity(label):
        label = re.sub(r'^(?:trong )?(?:mot )?', '', label)
        parts = re.split(r' (?:nha|cua) ', label, maxsplit=1)
        if re.match(r'(?:ban|be|bac|co|chu) ', label):return None,label
        return parts[0].removesuffix(' cay'), parts[1] if len(parts)>1 else None
    place,person = identity(stated[1])
    for label in ([asked] if asked else []) + ([count_place[1]] if count_place else []):
        if not re.fullmatch(subject_pattern(), label):return False
        target_place,target_person = identity(label)
        if target_place and target_place!=place or target_person and target_person!=person:return False
    return True


def verified_plan(problem: str) -> dict | None:
    return _verified_content(problem)


def verified_summary(problem: str) -> dict | None:
    return _verified_content(problem, summary_only=True)


def _verified_content(problem: str, *, summary_only: bool = False) -> dict | None:
    if not isinstance(problem, str) or len(problem) > 4000:
        return None
    original = re.sub(r"\s+", " ", unicodedata.normalize('NFC', problem)).strip()
    text = _fold(original)
    # A single worksheet label is metadata, never an extra mathematical given.
    label = re.match(r'^(?:bai|cau)\s+(?:so\s+)?\d+[a-z]?\s*[:.)]?\s*', text)
    if label:
        original = original[label.end():]
    score = re.search(r"\s*\(\d+(?:[.,]\d+)? diem\)\s*$", _fold(original))
    if score:
        original = original[:score.start()]
    text = _fold(original)
    if len(original) != len(text):
        return None
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
        # An arbitrary prose prefix hid conditions such as "the total is odd".
        intro = (subject_pattern() + r" co (?:mot so (?:quyen |cuon |vien )?" + population
                 + r"[.;] trong do[,;]? )?")
        total_question = r"(?:" + subject_pattern() + r" )?(?:co )?(?:tat ca|tong cong|tong so) "
        grammar = (intro + fraction + " so " + population + r" la ([a-z ]{2,70})[,;.] ?(?:va )?"
                   + fraction + " so " + population + r" la ([a-z ]{2,70})[,;.] ?(?:so " + population
                   + r" )?con lai la ([a-z ]{2,70})\. biet (?:rang )?([^.?]{1,120})\. "
                   + r"hoi (" + total_question + r")bao nhieu " + counter + r"\??")
        match = re.fullmatch(grammar, text)
        if not match:
            return None
        if not same_context(text, match[5]):
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
        first, second, rest = (original[match.start(i):match.end(i)].strip() for i in (1, 2, 3))
        context = re.match(subject_pattern() + r' co ', text)[0][:-4]
        subject = original[:len(context)]
        location = re.sub(r'^(?:trong )?(?:một )?', '', subject, flags=re.I)
        place = f' trong {location[0].lower() + location[1:]}' if not re.match(r'(ban|be|bac|co|chu) ', _fold(location)) else f' của {location[0].lower() + location[1:]}'
        question = original[match.start(5):].strip().rstrip('?')
        total_name = 'sách' if population == 'sach' else unit
        if summary_only:
            return {'givens': [f'{fractions[0]} số {total_name}{place} là {first}.',
                               f'{fractions[1]} số {total_name}{place} là {second}.',
                               f'Số {total_name} còn lại là {rest}.',
                               f'Số {rest}{place} là {count} {unit}.'],
                    'question': f'Tìm tổng số {total_name}{place}.'}
        intros = [f"Đề bài cho biết phần {first} và phần {second}. Em cần tìm xem phần {rest} chiếm bao nhiêu trong tổng số {total_name}.",
                  f"Em hãy dùng phần {rest} đã tìm ở bước trước và dữ kiện {count} {unit} để tìm tổng số {total_name}."]
        descriptions = [
            (f"Tìm phân số chỉ số {rest}", f"Phân số chỉ số {rest}{place} là:",
             f"Đề bài cho biết phần {first} và phần {second}. Phần còn lại là {rest}. Nếu coi tổng số {total_name} là một đơn vị, em sẽ tìm phần {rest} như thế nào?",
             f"Cộng phần {first} và phần {second}, rồi lấy một đơn vị trừ tổng đó để tìm phần {rest}. Ta quy đồng để các phần có cùng kích thước trước khi cộng hoặc trừ.",
             f"1-({fractions[0]}+{fractions[1]})", "", f"Số {rest} chiếm bao nhiêu phần tổng số {unit}{place}?"),
            (f"Tìm tổng số {unit}{place}", f"Tổng số {unit}{place} là:",
             f"Em đã tìm được phân số chỉ phần {rest} và đề bài cho biết có {count} {unit} thuộc phần đó. Làm thế nào để tìm tổng số {unit} khi đã biết giá trị của phần này?",
             f"Lấy {count} {unit} chia cho phân số chỉ phần {rest} để tìm tổng số {unit}. Chia cho một phân số là nhân với phân số đảo ngược của nó.",
             f"{count}/{{s0}}", unit, question[0].upper() + question[1:] + '?')]
        return {"topic": "Tìm toàn bộ từ phần đã biết", "goal": f"Tìm tổng số {unit}{place} từ phần {rest}.",
                "finalAnswerStep": 1, "steps": [
                    {"title": title, "solutionSentence": sentence, "explanation": why, "question": question,
                     "expression": expression, "unit": step_unit, "fractionNotation": True, "intro": intros[index],
                     "guidance": [(f"Phần đã kiểm tra là {{s{index-1}}}. " if index else "") + why, how],
                     "initialGuidance": [(f"Phần đã kiểm tra là {{s{index-1}}}. " if index else "") + why, how], "hints": [why, how]}
                    for index, (title, sentence, why, how, expression, step_unit, question) in enumerate(descriptions)]}
    return None
