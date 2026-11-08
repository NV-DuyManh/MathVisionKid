"""Split explicit independent worksheet rows, without calculating or inventing text."""
import re
import unicodedata
from collections import Counter

from app.tutoring.service import _fold
from app.tutoring.choice_source import numeric_notation


def _independent_rows(text):
    source_rows = [row.strip() for row in re.split(r'\n|\t+', text) if row.strip()]
    if not source_rows:
        return []
    header, *body = source_rows
    instruction = _fold(header)
    calculations = bool(re.search(r'\b(?:tinh|bieu thuc)\b', instruction))
    conversions = bool(re.search(r'\b(?:dien|viet) (?:so|don vi)\b', instruction))
    rows = []
    for row in body:
        if conversions and row.count('=') > 1:
            # OCR can serialize side-by-side cells using spaces instead of tabs.
            # A chained equality or an incomplete cell must stay together.
            cells = re.split(r'[ \u00a0\u202f]{3,}', row)
            if len(cells) > 1 and all(cell[0].isdigit() and cell.count('=') == 1
                                      and cell.split('=')[1].strip() for cell in cells):
                rows.extend(cells)
                continue
        rows.append(row)
    if len(rows) < 2:
        return []
    for row in rows:
        value = _fold(row)
        if conversions and '=' in value:
            value = re.sub(r'\b(?:km|dm|cm|mm|kg|mg|ml|ha|m|g|l|tan|ta)[²³]?\b', '', value)
        elif not calculations:
            return []
        if not (re.search(r'\d', value) and re.fullmatch(r'[\d\s.,()+*/×÷−–:\-x=…?²³]+', value)
                and re.search(r'[=+*/×÷−–:\-]', value)):
            return []
    return [(str(i+1), header + '\n' + row) for i, row in enumerate(rows)]


def selectable_questions(questions):
    result = []
    for question in questions:
        text = re.sub(r'^(\s*(?:Câu|Bài)\s+\d+\s*[.:]?\s*(?:\([^)]*điểm\)\s*)?)(?=[a-h][.)]\s)',
                      r'\1\n', question.problemText, flags=re.I)
        marks = list(re.finditer(r'(?:^|\n|\t+|[ \u00a0\u202f]{3,})[ \t]*([a-h])[.)]\s*', text))
        header = text[:marks[0].start()].strip() if marks else ''
        instruction = _fold(header)
        # Only task instructions, not shared quantities in a word problem.
        simple_header = bool(re.fullmatch(
            r'(?:(?:cau|bai)\s+\d+\s*[.:]?\s*)?(?:\([^)]*diem\)\s*[.:]?\s*)?'
            r'(?:tinh.*|dat tinh.*|viet (?:so|cac so).*|dien (?:so|don vi).*|'
            r'dung ghi.*|hoan thanh bang.*|khoanh vao chu cai.*)', instruction))
        if not simple_header and re.fullmatch(r'(?:cau|bai)\s+\d+\s*[.:]?\s*(?:\([^)]*diem\)\s*[.:]?)?', instruction):
            # Some worksheets put a) on the heading line, with a complete task
            # instruction in each subpart rather than one shared instruction.
            simple_header = all(re.match(r'(?:viet|sap xep|tinh|dien|lam tron|cac so tu nhien|so\b.+lam tron)',
                re.sub(r'^\([^)]*diem\)\s*', '',
                    _fold(text[mark.end():marks[i+1].start() if i+1 < len(marks) else len(text)].strip())))
                for i, mark in enumerate(marks))
        parts = []
        if len(marks) > 1 and simple_header:
            for index, mark in enumerate(marks):
                end = marks[index+1].start() if index+1 < len(marks) else len(text)
                body = header + '\n' + text[mark.end():end].strip()
                rows = _independent_rows(body)
                if rows:
                    parts.extend((mark[1] + ' · ' + label, part) for label, part in rows)
                else:
                    parts.append((mark[1], body))
        elif not marks:
            parts = _independent_rows(text)
        if parts and all(len(f'{question.label} · {label}') <= 100 and len(part) <= 4000 for label, part in parts):
            result.extend(type(question)(label=f'{question.label} · {label}', problemText=part,
                uncertain=question.uncertain) for label, part in parts)
        else:
            result.append(question)
    # A too-large result remains the complete original groups, never a truncated list.
    return result if len(result) <= 30 and sum(len(q.problemText) for q in result) <= 24000 else questions


def compared_questions(primary, independent):
    """Disagreement is uncertainty, never permission to choose the plausible value."""
    def signature(question):
        text = numeric_notation(unicodedata.normalize('NFC', question.problemText))
        # Ignore layout spacing and equivalent minus glyphs, but keep the order,
        # operators, accents and units. The same bag of numbers is not agreement.
        return tuple(re.findall(r'\d+(?:[.,]\d+)?|[^\W\d_]+|\S', text.replace('−', '-')))

    primary_signatures = [signature(question) for question in primary]
    independent_signatures = [signature(question) for question in independent]
    primary_counts = Counter(primary_signatures)
    independent_counts = Counter(independent_signatures)
    confirmed = {key for question, key in zip(independent, independent_signatures)
                 if not question.uncertain and independent_counts[key] == 1}
    return [question.model_copy(update={
        'uncertain': question.uncertain or primary_counts[key] != 1 or key not in confirmed})
        for question, key in zip(primary, primary_signatures)]
