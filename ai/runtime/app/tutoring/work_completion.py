"""Source-bound completion evidence, separate from arithmetic and teaching prose."""
import re
from typing import Annotated, Literal

from pydantic import Field

from app.tutoring.service import TutorModel, _fold


MissingType = Literal['MISSING_CALCULATION', 'MISSING_INTERMEDIATE', 'MISSING_ANSWER', 'NOT_STARTED']


class CompletionGap(TutorModel):
    requirementIndex: int = Field(ge=0, le=7, strict=True)
    type: MissingType
    quantity: str = Field(min_length=2, max_length=160)
    relatedLineIndices: list[Annotated[int, Field(ge=0, le=34, strict=True)]] = Field(default_factory=list, max_length=35)
    givenQuantities: list[str] = Field(default_factory=list, max_length=3)
    operation: Literal['ADD', 'SUBTRACT', 'MULTIPLY', 'DIVIDE'] | None = None
    operands: list[Annotated[str, Field(min_length=2, max_length=160)]] = Field(default_factory=list, max_length=2)


class MissingPart(TutorModel):
    type: MissingType
    target: str = Field(min_length=2, max_length=160)
    description: str = Field(min_length=1, max_length=240)
    hint: str = Field(min_length=1, max_length=300)
    requirementIndex: int = Field(ge=0, le=7)
    relatedLineIndices: list[int] = Field(default_factory=list, max_length=35)
    evidence: Literal['DUAL_REVIEW', 'DETERMINISTIC']


def requirements(problem: str) -> list[str]:
    """Extract question clauses, not a reference solution or mandatory method."""
    clauses = re.split(r'[?;\n]+|(?<=[.!])\s+|\s+(?=[a-h][).]\s)', problem)
    found = []
    for clause in clauses:
        clause = re.sub(r'^[a-h][).:]\s*', '', clause.strip(), flags=re.I)
        match = re.search(r'\b(?:hỏi|tính|tìm|xác định|cho biết|bao nhiêu)\b', clause, re.I)
        if not match:
            continue
        if _fold(match[0]) in {'tinh', 'tim', 'xac dinh', 'cho biet'} and match.start() and _fold(clause[:match.start()]).strip() not in {'em', 'hay', 'em hay'}:
            continue
        question = (clause if _fold(match[0]) == 'bao nhieu' else clause[match.start():]).strip(' .:')
        # Explicit independent quantities share the question's context.
        parts = re.split(r'\s+và\s+(?=(?:tính |tìm )?(?:diện tích|chu vi|thể tích|vận tốc|quãng đường|thời gian|số\b))', question, flags=re.I)
        for part in parts:
            if part and part not in found:
                found.append(part[:500])
    return found[:8]


def quantity_label(question: str) -> str:
    text = re.sub(r'^(?:(?:hãy|em|hỏi|tính|tìm|xác định|cho biết)\s+)+', '', question, flags=re.I).strip(' .:?!')
    match = re.fullmatch(r'(.+?)\s+có\s+(?:tất cả\s+)?bao nhiêu\s+(.+)', text, re.I)
    if match:
        text = f'tổng số {match[2]} của {match[1]}'
    text = re.sub(r'\s+(?:là\s+)?bao nhiêu\b', '', text, flags=re.I)
    return text[:160]


_GRAMMAR = set(_fold('tổng số phần phân chiều còn lại ban đầu cần tìm của trong cho về với các và để cả lượng').split())
_IGNORED = set(_fold('tổng số phần chỉ của trong cho về với các và để cả là có tất bao nhiêu hãy tính tìm hỏi').split())
_INPUT_CONNECTORS = set(_fold('số của trong cho về với các và để là có tất cả').split())


def _words(text):
    return set(re.findall(r'[^\W\d_]+', _fold(text)))


def _given_in_facts(name, facts):
    tokens = _words(name) - _GRAMMAR
    ratio = re.search(r'\b(?:phan so|so phan|ti so|ti le)\b', _fold(name))
    for clause in re.split(r'[,.;!\n]+', facts):
        if not tokens or not re.search(r'\d', clause) or not tokens <= _words(clause):
            continue
        if ratio and not re.search(r'\d\s*/\s*\d|\\(?:d?frac)\b|%|\bnửa\b|\bphần trăm\b', clause, re.I):
            continue
        # A relationship supplies a ratio/difference, not the value of the
        # unknown quantity itself (e.g. "width equals a fraction of length").
        relationship = re.search(r'\b(?:bang|gap|hon|kem|chiem|so voi|cua)\b', _fold(clause))
        if not relationship or ratio:
            return True
    return False


def _input_name(name, quantities):
    # Resolve an abbreviated name only when it names a unique known quantity.
    matches = {_fold(quantity): quantity for quantity in quantities
               if _fold(quantity) == _fold(name) or any(_fold(quantity).startswith(_fold(name) + ' ' + context + ' ')
                                                      for context in ('trong', 'cua', 'o', 'tai'))}
    return next(iter(matches.values())) if len(matches) == 1 else name


def _input_key(name):
    # "Total number of X" names the count of X; other totals, fractions and
    # remainders retain their mathematical meaning when comparing references.
    name = re.sub(r'^tổng số\b', 'số', name, flags=re.I)
    return _words(name) - _INPUT_CONNECTORS


def agreed_gaps(first, second, problem=''):
    """Both independent reviewers must name the same unmet requirement/quantity."""
    other = {(gap.requirementIndex, gap.type, _fold(gap.quantity)): gap for gap in second}
    quantities = [gap.quantity for gap in [*first, *second]]
    for gap in first:
        peer = other.get((gap.requirementIndex, gap.type, _fold(gap.quantity)))
        if peer:
            operands = []
            if gap.operation == peer.operation and len(gap.operands) == len(peer.operands) == 2:
                for left, right in zip(gap.operands, peer.operands):
                    left, right = _input_name(left, quantities), _input_name(right, quantities)
                    left_words, right_words = _input_key(left), _input_key(right)
                    # A provider may cite an exact original fact instead of its
                    # name. It is a reference only; never publish its values.
                    grounded = all(not any(char.isnumeric() for char in name) or _fold(name) in _fold(problem)
                                   for name in (left, right))
                    names = [name for name in (left, right) if not any(char.isnumeric() for char in name)]
                    if grounded and left_words and left_words == right_words and names:
                        operands.append(names[0])
            same_step = len(operands) == 2
            yield gap.model_copy(update={'relatedLineIndices': sorted(set(gap.relatedLineIndices) & set(peer.relatedLineIndices)),
                'givenQuantities': [name for name in gap.givenQuantities if _fold(name) in {_fold(value) for value in peer.givenQuantities}],
                'operation': gap.operation if same_step else None, 'operands': operands if same_step else []})


def legacy_gaps(problem, rows, goals):
    """Recover a named unmet goal only after an independent incomplete judgment.

    Unlabelled equations can be a compact valid method; absence of a heading
    alone never proves that their requested result is missing.
    """
    calculations = [row for row in rows if row.arithmeticCorrect is True and row.status == 'OK']
    if not calculations:
        return []
    labelled = []
    for row in calculations:
        if row.lineIndex and rows[row.lineIndex - 1].rowKind == 'EXPLANATION':
            labelled.append((row, rows[row.lineIndex - 1].sourceText))
        else:
            return []
    result = []
    for index, goal in enumerate(goals):
        label = quantity_label(goal)
        tokens = _words(label) - _IGNORED
        def represents(heading):
            share = r'\b(?:phan so|so phan|ti so|ti le)\b'
            return tokens <= _words(heading) and not (re.search(share, _fold(heading)) and not re.search(share, _fold(label)))
        if tokens and not any(represents(heading) for _, heading in labelled):
            result.append(CompletionGap(requirementIndex=index, type='MISSING_CALCULATION',
                                        quantity=label, relatedLineIndices=[calculations[-1].lineIndex]))
    return result


def not_started(problem, rows, goals):
    if (re.search(r'\bhinh (?:ben|duoi|sau)\b|\b(?:theo|xem) hinh\b|\bso do\b', _fold(problem))
            or not re.search(r'\d', problem) or not goals
            or any(row.rowKind != 'HEADING' and not (row.rowKind == 'EXPLANATION'
                and re.search(r'\blà\s*[:：]?\s*$', row.sourceText, re.I)) for row in rows)):
        return []
    return [CompletionGap(requirementIndex=index, type='NOT_STARTED', quantity=quantity_label(goal))
            for index, goal in enumerate(goals)]


def missing_parts(problem, rows, goals, gaps, validate, evidence='DUAL_REVIEW'):
    parts = []
    seen = set()
    priority = {'NOT_STARTED': 0, 'MISSING_INTERMEDIATE': 1, 'MISSING_CALCULATION': 2, 'MISSING_ANSWER': 3}
    for gap in sorted(gaps, key=lambda item: (item.requirementIndex, priority[item.type])):
        if gap.requirementIndex >= len(goals) or not _words(gap.quantity) <= (_words(problem) | _GRAMMAR):
            continue
        if gap.type == 'MISSING_ANSWER' and not re.search(r'\b(?:ghi|viết|phải có)\s+(?:phần\s+)?đáp số\b', problem, re.I):
            continue
        quantity = gap.quantity.strip(' .:?!')
        key = (gap.requirementIndex, gap.type, _fold(quantity))
        if key in seen:
            continue
        related = sorted({i for i in gap.relatedLineIndices if type(i) is int and 0 <= i < len(rows)
                          and rows[i].status == 'OK' and rows[i].arithmeticCorrect is True})
        boundary = re.search(r'\b(?:hỏi|tính|tìm|xác định|cho biết)\b', problem, re.I)
        facts = problem[:boundary.start()] if boundary else problem
        givens = []
        for name in gap.givenQuantities:
            if not 2 <= len(name) <= 100 or not _words(name) <= (_words(facts) | _GRAMMAR) or not _given_in_facts(name, facts):
                continue
            try:
                validate(name)
                givens.append(name)
            except ValueError:
                pass
        given = ' và '.join(givens)
        description = f'Tính {quantity}.'
        hint = f'Em dùng {given} đề cho để tìm {quantity} nhé.' if given else f'Em dùng dữ kiện đề cho để tìm {quantity} nhé.'
        if gap.type == 'MISSING_ANSWER':
            description = f'Ghi đáp số cho {quantity}.'
            hint = f'Em giữ nguyên phép tính đã đúng và ghi đáp số cho {quantity} nhé.'
        elif gap.type == 'MISSING_INTERMEDIATE':
            hint = f'Em cần tìm {quantity} trước để tiếp tục trả lời câu hỏi của đề.'
        elif gap.type == 'NOT_STARTED':
            description = f'Bắt đầu tìm {quantity}.'
            hint = f'Em chọn dữ kiện liên quan đến {quantity} trong đề để bắt đầu bài giải nhé.'
        elif related:
            index = related[-1]
            previous = rows[index - 1] if index else None
            label = re.sub(r'\s+là\s*[:：]?$', '', previous.sourceText.strip(), flags=re.I) if previous and previous.rowKind == 'EXPLANATION' else ''
            if label and len(label) <= 100:
                label = label[0].lower() + label[1:]
                hint = f'Em đã tìm được {label}. Hãy dùng kết quả này cùng dữ kiện đề cho để tìm {quantity}.'
            else:
                hint = f'Em dùng kết quả vừa tìm được cùng dữ kiện đề cho để tìm {quantity} nhé.'
            if given:
                hint = f'Em đã tìm được {label}. Em dùng kết quả này cùng {given} đề cho để tìm {quantity}.' if label else f'Em dùng {given} đề cho cùng kết quả vừa tìm được để tìm {quantity} nhé.'
        if gap.type in {'MISSING_CALCULATION', 'MISSING_INTERMEDIATE'} and gap.operation and len(gap.operands) == 2:
            completed = []
            for index in related:
                if index and rows[index - 1].rowKind == 'EXPLANATION':
                    label = re.sub(r'\s+là\s*[:：]?$', '', rows[index - 1].sourceText.strip(), flags=re.I)
                    if label:
                        completed.append(label)
            pending = [part.target for part in parts]
            supported = lambda name: any(_fold(name) == _fold(label) for label in completed + pending) or _given_in_facts(name, facts)
            if all(supported(name) for name in gap.operands):
                left, right = gap.operands
                verb = {'ADD': 'cộng với', 'SUBTRACT': 'trừ đi', 'MULTIPLY': 'nhân với', 'DIVIDE': 'chia cho'}[gap.operation]
                prerequisites = [name for name in gap.operands if any(_fold(name) == _fold(target) for target in pending)]
                if prerequisites:
                    context = f'Trước hết, em tìm {" và ".join(prerequisites)} ở phần trên. Sau đó, '
                    action = 'em lấy'
                elif completed:
                    label = completed[-1]
                    context = f'Em đã tìm được {label[0].lower() + label[1:]}.\n'
                    action = 'Em lấy'
                else:
                    context, action = '', 'Em lấy'
                clearer = f'{context}{action} {left} {verb} {right}. Kết quả cho biết {quantity}.'
                try:
                    for text in [left, right, clearer]:
                        validate(text)
                    if len(clearer) <= 300:
                        hint = clearer
                except ValueError:
                    pass
        if any(row.status == 'FIX' and row.errorKind != 'EXPLANATION' for row in rows):
            hint = f'Em sửa các phép tính được đánh dấu trước, rồi dùng kết quả đúng để tìm {quantity}.'
        if len(hint) > 300:
            hint = f'Em dùng kết quả vừa tìm được cùng dữ kiện đề cho để tìm {quantity} nhé.'
        try:
            validate(quantity)
            validate(description)
            try:
                validate(hint)
            except ValueError:
                # Unsafe adjacent prose cannot erase the verified target.
                hint = f'Em dùng dữ kiện đã cho để tìm {quantity} nhé.'
                validate(hint)
            parts.append(MissingPart(type=gap.type, target=quantity, description=description, hint=hint,
                                     requirementIndex=gap.requirementIndex, relatedLineIndices=related, evidence=evidence))
            seen.add(key)
        except ValueError:
            continue
    return sorted(parts, key=lambda part: (part.requirementIndex, priority[part.type]))[:8]
