"""Reuse the lesson's checked solvers and plans for related practice questions."""
import ast
import asyncio
import hashlib
import json
import random
import re
from copy import deepcopy
from decimal import Decimal
from fractions import Fraction

from pydantic import Field

from app.tutoring import catalog, lesson, plan_preparation
from app.tutoring.choice_source import numeric_notation, split_choices
from app.tutoring.service import TutorModel, TutorUnavailable, _generate

_active_variants = 0

class VariantRequest(TutorModel):
    owner: str = Field(min_length=1, max_length=200)
    problemText: str = Field(min_length=3, max_length=4000)
    excludedAnswers: list[str] = Field(default_factory=list, max_length=200)
    sourceFingerprint: str | None = Field(default=None, pattern=r'^[a-f0-9]{64}$')


def exact_plan(text):
    from app.tutoring.short_math import verified_plan as short
    from app.tutoring.fraction_remainder import verified_plan as remainder
    from app.tutoring.digit_append import verified_plan as digit
    from app.tutoring.mass_fraction import verified_plan as mass
    raw = short(text) or remainder(text) or digit(text) or mass(text)
    return lesson.Plan.model_validate(raw) if raw else None


def proof(plan):
    answers, units, operations, rows = [], [], [], []
    final = plan.finalAnswerStep if plan.finalAnswerStep is not None else len(plan.steps) - 1
    for index, step in enumerate(plan.steps):
        if step.kind != 'MATH':
            raise ValueError('Only checked math plans may create practice')
        unit = step.unit
        if step.expression:
            expression = lesson.expression_at(step, answers)
            value = lesson.calculate_exact(expression)
            tree = ast.parse(expression.translate(lesson._SYMBOLS), mode='eval')
            operations.append(sorted(type(node.op).__name__ for node in ast.walk(tree) if isinstance(node, ast.BinOp)))
            rows.append(f'{lesson.solution_sentence(step) or step.title} {lesson.display_expression(expression, True)} = {value} {step.unit}'.strip())
        else:
            # A checked lesson can finish by choosing "D. 2 170 kg" after
            # computing the result. The letter and unit are presentation, not
            # a non-numeric answer or an extra mathematical operation.
            selected = re.sub(r'^[A-D][.)]\s*', '', numeric_notation(step.correctChoice), flags=re.I).strip()
            if not unit and units:
                unit = units[-1]
            if unit and selected.endswith(' ' + unit):
                selected = selected[:-len(unit)].strip()
            if not re.fullmatch(r'-?\d+(?:[.,]\d+)?(?:/\d+)?', selected):
                if len(plan.steps) != 1 or not step.choices or step.correctChoice not in step.choices:
                    raise ValueError('A checked single choice is required')
                value = Fraction(step.choices.index(step.correctChoice) + 1)
                operations.append(['CHOICE_TEXT'])
                rows.append(f'{step.title}: {step.correctChoice}. {step.explanation}')
                answers.append(str(value))
                units.append(unit)
                continue
            value = Fraction(selected.replace(',', '.'))
            if index == len(plan.steps) - 1 and answers and plan.steps[index - 1].expression:
                if value != Fraction(answers[-1]) or unit != units[-1]:
                    raise ValueError('The final answer choice contradicts the checked calculation')
            else:
                operations.append(['CHOICE'])
            rows.append(f'{step.title}: {step.correctChoice}. {step.explanation}')
        answers.append(str(value))
        units.append(unit)
    answer = Fraction(answers[final])
    return answer, units[final], operations, rows, all(Fraction(item).denominator == 1 for item in answers)


def checked_exact(text):
    plan = exact_plan(text)
    if plan:
        request = lesson.LessonRequest(owner='quiz-exact-validation', problemText=text, problemConfirmed=True)
        lesson.validate_plan(plan, request, lesson.formula_constants(text))
    return plan


def candidates(stem, rng):
    # Keep units, exercise/class labels and relation words intact. Each changed
    # whole source must be solved again, rather than copying an old answer key.
    tokens = list(re.finditer(r'(?<![\w.,/])\d+(?:[.,]\d+)?(?:/\d+)?(?![\w.,/])', stem))
    rng.shuffle(tokens)
    for token in tokens[:12]:
        original = Fraction(token[0].replace(',', '.'))
        offsets = rng.sample([1, 2, 3, -1, -2, 5], 6)
        values = [Fraction(original.numerator + offset, original.denominator) if '/' in token[0] else original + offset for offset in offsets]
        if '/' in token[0]:
            values += [Fraction(original.numerator, original.denominator + offset) for offset in [1, 2, 10]]
        for value in values:
            if value <= 0 or value == original:
                continue
            if '/' not in token[0] and value.denominator != 1:
                replacement = format(Decimal(value.numerator) / Decimal(value.denominator), 'f').replace('.', ',')
            else:
                replacement = str(value)
            yield stem[:token.start()] + replacement + stem[token.end():]


def response(request, question, plan, rng, *, review=False):
    answer, unit, shape, rows, _ = proof(plan)
    text_choice = shape == [['CHOICE_TEXT']]
    if text_choice:
        step = plan.steps[0]
        # Publish the exact alternatives the solver checked. The private answer
        # is their one-based position, while the learner sees the full text.
        multiple = split_choices(question, allow_statement=True)
        question = multiple[0] if multiple else question
        question += ''.join(f'\n{label}. {choice}' for label, choice in zip('ABCD', step.choices))
    elif split_choices(request.problemText, allow_statement=True) and not split_choices(question, allow_statement=True):
        values = [answer, answer + 1, answer + 2, answer + 3]
        rng.shuffle(values)
        question += ''.join(f'\n{label}. {value}{" " + unit if unit else ""}' for label, value in zip('ABCD', values))
    if len(question) > 4000 or len(unit) > 30:
        raise ValueError('Practice content is too long')
    multiple = split_choices(question, allow_statement=True)
    if multiple:
        question = multiple[0] + ''.join(f'\n{label}. {choice}' for label, choice in zip('ABCD', multiple[1]))
    fingerprint = request.sourceFingerprint or hashlib.sha256(re.sub(r'[ \t\r\n\f\v]+', ' ', request.problemText.strip()).encode()).hexdigest()
    return dict(sourceFingerprint=fingerprint, questionText=question, answer=str(answer), unit=unit,
                solution='\n'.join(rows), topic=plan.topic,
                review=review, verification='TUTOR_VERIFIED', answerFormat='CHOICE' if text_choice else 'NUMBER')


async def generate(request: VariantRequest):
    global _active_variants
    if '[?]' in request.problemText or '\ufffd' in request.problemText:
        raise ValueError('Clarify the confirmed source first')
    lesson.safe_public(request.problemText)
    source_request = lesson.LessonRequest(owner=request.owner, problemText=request.problemText, problemConfirmed=True)
    multiple = split_choices(request.problemText, allow_statement=True)
    stem = numeric_notation(multiple[0] if multiple else request.problemText)
    stem = re.sub(r'^(?:Câu|Bài)\s+\d+\s*[.):]?\s*', '', stem, flags=re.I)
    source = checked_exact(request.problemText)
    if source is not None and multiple:
        calculation = checked_exact(stem)
        if calculation is not None:
            if proof(calculation)[:2] != proof(source)[:2]:
                raise ValueError('The original answer options contradict the source')
            source = calculation
    if source is None and not multiple:
        source = checked_exact(stem)
    if source is None:
        source = await asyncio.to_thread(catalog.load_plan, source_request)
    if source is None:
        # Share lesson preparation, or start it for completed work reviews that
        # never opened a lesson. Both paths use the same owner/capacity boundary.
        try:
            async with asyncio.timeout(20):
                source = await plan_preparation.prepared_plan(source_request, start_missing=True)
        except TimeoutError as error:
            raise TutorUnavailable('preparing') from error
    if source is None:
        raise TutorUnavailable('preparing')
    source = deepcopy(source)
    lesson.validate_plan(source, source_request, lesson.formula_constants(request.problemText))
    original, original_unit, shape, _, integral = proof(source)
    excluded = {Fraction(value) for value in request.excludedAnswers} | {original}
    rng = random.SystemRandom()
    for question in candidates(stem, rng):
        try:
            plan = checked_exact(question)
            if plan is None and multiple:
                question += ''.join(f'\n{label}. {choice}' for label, choice in zip('ABCD', multiple[1]))
                plan = checked_exact(question)
            if plan is None:
                continue
            answer, unit, operations, _, all_integers = proof(plan)
            if answer in excluded or answer <= 0 or unit != original_unit or operations != shape:
                continue
            if integral and not all_integers:
                continue
            return response(request, question, plan, rng)
        except (ValueError, ArithmeticError, SyntaxError, TypeError):
            continue

    if shape in ([['CHOICE']], [['CHOICE_TEXT']]):
        return response(request, request.problemText, source, rng, review=True)

    # Bound speculative provider work per runtime. A checked review remains
    # immediately available when other learners are already creating variants.
    if _active_variants >= 2:
        return response(request, request.problemText, source, rng, review=True)
    _active_variants += 1

    # Other wording can use the same independent plan review as a lesson.
    # This happens in background preparation, only after the source is checked.
    try:
        async with asyncio.timeout(26):
            proposal = await _generate(
                'Tạo đúng một bài toán tiểu học cùng dạng, số bước, quan hệ và độ khó với đề đã cho. '
                'Đổi tên hoặc ngữ cảnh phù hợp và đổi các số. Giữ đơn vị. Nếu bài gốc có đáp án nguyên thì mọi bước và đáp án mới phải nguyên dương. '
                'Chỉ trả JSON {"problemText":"đề mới"}. Không có đáp án, phương án A-D hoặc lời giải.',
                json.dumps({'problemText': stem}, ensure_ascii=False),
                max_output_tokens=1200, timeout_seconds=8,
                response_schema={'type': 'object', 'properties': {'problemText': {'type': 'string'}}, 'required': ['problemText']})
            question = proposal.get('problemText', '')
            variant_request = lesson.LessonRequest(owner=request.owner, problemText=question, problemConfirmed=True)
            plan = await lesson.checked_plan(variant_request)
            answer, unit, operations, _, all_integers = proof(plan)
            if question == stem or answer in excluded or answer <= 0 or unit != original_unit or operations != shape:
                raise ValueError('Variant does not preserve the checked task')
            if integral and not all_integers:
                raise ValueError('Variant changed integer arithmetic')
            return response(request, question, plan, rng)
    except (TutorUnavailable, TimeoutError, ValueError, ArithmeticError, SyntaxError, TypeError):
        # A provider outage does not replace a checked lesson with unrelated
        # arithmetic. Offer an explicitly labelled review of that same source.
        return response(request, request.problemText, source, rng, review=True)
    finally:
        _active_variants -= 1
