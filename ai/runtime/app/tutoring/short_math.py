"""Exact, whole-source proofs for short elementary exercises.

No fuzzy matching or answer guessing: unrecognized wording, extra conditions,
ambiguous choices and inconsistent units keep the independently reviewed path.
"""
import re
import ast
from fractions import Fraction

from app.tutoring.choice_source import split_choices
from app.tutoring.math_knowledge import normalized_units, unit_conversions
from app.tutoring.service import _fold


_NUMBER = r'\d{1,9}(?:[.,]\d{1,9})?'
_UNITS = r'(?:km|hm|dam|m|dm|cm|mm)(?:[²³])?|ha|kg|hg|dag|g|mg|tan|ta|yen|l|dl|cl|ml'


def _number(text):
    text = text.strip()
    if not re.fullmatch(_NUMBER + r'(?:\s*/\s*\d{1,9})?', text):
        raise ValueError('Not one exact number')
    return Fraction(text.replace(',', '.').replace(' ', ''))


def _plan(title, why, how, *, expression='', unit='', options=(), selected='', fraction=False):
    return dict(topic=title, goal='Em tự tính hoặc chọn kết quả rồi kiểm tra lại.', finalAnswerStep=0,
                steps=[dict(title=title, explanation=why, question='Em chọn kết quả nào?' if options else 'Em tính được bao nhiêu?',
                            expression=expression, unit=unit, choices=list(options), correctChoice=selected,
                            solutionSentence='' if options else 'Kết quả là:', fractionNotation=fraction,
                            initialGuidance=[why, how], guidance=[why, how], hints=[why, how])])


def _result(title, why, how, expression, options, unit='', fraction=False):
    from app.tutoring.lesson import calculate_exact
    value = calculate_exact(expression)
    if options:
        values = []
        for option in options:
            option = normalized_units(option)
            if unit and not re.fullmatch(_NUMBER + r'(?:\s*/\s*\d{1,9})?', option):
                suffix = re.fullmatch(r'(.+?)\s*(' + _UNITS + ')', option)
                if not suffix or suffix[2] != unit:
                    return None
                option = suffix[1]
            values.append(_number(option))
        if len(set(values)) != len(values) or values.count(value) != 1:
            return None
        return _plan(title, why, how, options=options, selected=options[values.index(value)])
    return _plan(title, why, how, expression=expression, unit=unit, fraction=fraction)


_DIGITS = dict(zip('khong mot hai ba bon nam sau bay tam chin'.split(), range(10)))


def _spoken_integer(words):
    """Bounded standard Vietnamese integer reading, not arbitrary word arithmetic."""
    words = words.split()
    if not words:
        return None
    if len(words) == 1 and words[0] in _DIGITS:
        return _DIGITS[words[0]]
    hundreds = 0
    if len(words) >= 2 and words[0] in _DIGITS and words[1] == 'tram':
        hundreds = _DIGITS[words[0]] * 100
        words = words[2:]
        if not words:
            return hundreds
        if words[0] in {'linh', 'le'}:
            return hundreds + _DIGITS[words[1]] if len(words) == 2 and words[1] in _DIGITS else None
    tens = None
    if words[0] == 'muoi':
        tens, rest = 10, words[1:]
    elif len(words) >= 2 and words[0] in _DIGITS and _DIGITS[words[0]] >= 2 and words[1] == 'muoi':
        tens, rest = _DIGITS[words[0]] * 10, words[2:]
    if tens is None:
        return None
    if not rest:
        return hundreds + tens
    units = {**_DIGITS, 'tu': 4, 'lam': 5}
    return hundreds + tens + units[rest[0]] if len(rest) == 1 and rest[0] in units and units[rest[0]] else None


def verified_plan(problem):
    try:
        return _verified_plan(problem)
    except (ValueError, SyntaxError, ArithmeticError, TypeError):
        return None


def _verified_plan(problem):
    if len(problem) > 4000 or '[?]' in problem:
        return None
    multiple = split_choices(problem, allow_statement=True)
    stem, options = multiple if multiple else (problem, [])
    text = _fold(re.sub(r'\s+', ' ', stem)).strip()
    text = re.sub(r'^(?:cau|bai)\s+\d+\s*[.):]?\s*(?:\(\s*\d+(?:[.,]\d+)?\s*diem\s*\)\s*)?', '', text)

    # Exact arithmetic, including a single operation, decimals and fractions.
    arithmetic = re.fullmatch(r'(?:tinh\s*:?\s*|(?:ket qua (?:cua )?phep tinh)\s*)?'
                              r'([\d\s.,()+*/×÷−–:\-x]+?)\s*(?:(?:=\s*(?:\?|\.{2,}|…))|(?:la\s*[:?]))?\s*[.?]?\s*', text)
    if arithmetic:
        expression = arithmetic[1].strip().replace(',', '.')
        for old, new in [('×', '*'), ('x', '*'), ('÷', '/'), (':', '/'), ('−', '-'), ('–', '-')]:
            expression = expression.replace(old, new)
        # Reject lone numbers, implicit multiplication and malformed expressions.
        if re.search(r'\d\s*[+*/-]\s*(?:\(|\d)', expression) and not re.search(r'\)\s*\(', expression):
            title, why, how = 'Tính giá trị phép tính', 'Nhìn dấu phép tính và dấu ngoặc để chọn việc cần làm trước.', 'Tính trong ngoặc trước, rồi nhân chia trước cộng trừ. Các phép tính cùng mức thực hiện từ trái sang phải.'
            tree = ast.parse(expression, mode='eval')
            operations = [node for node in ast.walk(tree) if isinstance(node, ast.BinOp)]
            if len(operations) == 1 and type(operations[0].op) in {ast.Add, ast.Sub, ast.Mult, ast.Div}:
                title, why, how = {
                    ast.Add: ('Cộng hai số', 'Phép cộng gộp hai số lại để tìm kết quả có tất cả.', 'Bắt đầu từ số đứng trước dấu cộng rồi đếm thêm số đứng sau. Với số lớn, đặt các chữ số cùng hàng thẳng cột rồi cộng.'),
                    ast.Sub: ('Trừ hai số', 'Phép trừ tìm phần còn lại khi bớt đi một lượng.', 'Bắt đầu từ số đứng trước dấu trừ rồi bớt số đứng sau. Khi đặt tính, xếp các chữ số cùng hàng thẳng cột rồi trừ.'),
                    ast.Mult: ('Nhân hai số', 'Phép nhân gộp các nhóm có số lượng bằng nhau.', 'Xem một thừa số là số nhóm, thừa số kia là lượng trong mỗi nhóm. Tính tích để tìm lượng của tất cả các nhóm.'),
                    ast.Div: ('Chia hai số', 'Phép chia tìm lượng trong mỗi phần khi chia đều, hoặc số nhóm bằng nhau.', 'Em tìm số mà khi nhân với số chia sẽ được số bị chia. Có thể đếm các nhóm bằng nhau hoặc dùng bảng nhân để kiểm tra.'),
                }[type(operations[0].op)]
                if '.' in expression and isinstance(operations[0].op, (ast.Add, ast.Sub)):
                    how = 'Đặt hai dấu phẩy thẳng cột để các chữ số cùng hàng nằm trên nhau. Tính từng cột như với số tự nhiên rồi giữ dấu phẩy đúng cột.'
            return _result(title, why, how,
                           expression, options, fraction='/' in expression and '.' not in expression)

    conversion = re.fullmatch(r'(?:dien vao (?:cho cham|cho trong|dau cham) de\s*:?\s*|doi\s+)?'
                             r'(' + _NUMBER + r')\s*(' + _UNITS + r')\s*(?:=|sang)\s*(?:\.{2,}|…|\?)?\s*(' + _UNITS + r')\s*[.:?]?', normalized_units(text))
    if conversion:
        amount, source, target = conversion.groups()
        conversions = unit_conversions(f'{amount} {source} sang {target}')
        relation = next((r for r in conversions if {r['fromUnit'], r['toUnit']} == {source, target}), None)
        if not relation:
            return None
        factor = relation['factor']
        operation = '*' if source == relation['fromUnit'] else '/'
        return _result('Đổi đơn vị đo', 'Cần biểu diễn cùng một lượng bằng đơn vị ở bên phải, không thay đổi lượng ban đầu.',
                       f'Từ {source} sang {target}, em {"nhân" if operation == "*" else "chia"} với {factor}. Đây là hệ số đổi giữa hai đơn vị; kết quả dùng đơn vị {target}.',
                       amount.replace(',', '.') + operation + factor, options, target)

    fractions = re.fullmatch(r'cho cac phan so sau\s*:?\s*([\d\s/;,]+)[.]?\s*co\s*(?:\.{2,}|…)\s*phan so thap phan\s*[.:?]?', text)
    if fractions and options:
        items = re.split(r'\s*[;,]\s*', fractions[1].strip())
        if not 1 <= len(items) <= 12 or any(not re.fullmatch(r'\d{1,6}\s*/\s*[1-9]\d{0,5}', item) for item in items):
            return None
        denominators = [int(item.split('/')[1]) for item in items]
        count = sum(bool(re.fullmatch(r'10+', str(d))) for d in denominators)
        values = [_number(option) for option in options]
        if len(set(values)) != len(values) or values.count(count) != 1:
            return None
        return _plan('Nhận biết phân số thập phân',
                     'Phân số thập phân có mẫu số là mười, một trăm, một nghìn, hoặc các lũy thừa tiếp theo của mười.',
                     'Xem mẫu số đúng như đề đã viết rồi đếm các phân số phù hợp. Không đổi mẫu hay rút gọn trước khi phân loại.',
                     options=options, selected=options[values.index(count)])

    equivalent = re.fullmatch(r'so thap phan bang voi\s+(' + _NUMBER + r')\s*(?:la)?\s*[:?]', text)
    if equivalent and options:
        value = _number(equivalent[1])
        values = [_number(option) for option in options]
        if len(set(values)) != len(values) or values.count(value) != 1:
            return None
        return _plan('So sánh số thập phân', 'Thêm hoặc bỏ chữ số không ở tận cùng bên phải phần thập phân không đổi giá trị của số.',
                     'Đối chiếu phần nguyên và từng hàng của phần thập phân. Chữ số không ở hàng khác vẫn có thể làm thay đổi giá trị.',
                     options=options, selected=options[values.index(value)])

    reading = re.fullmatch(r'so thap phan\s*["“]([a-z ]+) phay ([a-z ]+)["”]\s*la\s*[:?]', text)
    if reading and options:
        whole = _spoken_integer(reading[1])
        digits = reading[2].split()
        decimal = ''.join(str(_DIGITS[word]) for word in digits) if all(word in _DIGITS for word in digits) else None
        if decimal is None:
            tail = _spoken_integer(reading[2])
            # "không trăm linh năm" occupies three decimal places: 005, not 5.
            decimal = str(tail).zfill(3 if 'tram' in digits else 2) if tail is not None else None
        if whole is None or decimal is None:
            return None
        values = [_number(option) for option in options]
        value = Fraction(f'{whole}.{decimal}')
        if len(set(values)) != len(values) or values.count(value) != 1:
            return None
        return _plan('Viết số thập phân theo lời đọc', 'Phần trước tiếng phẩy là phần nguyên, phần sau là phần thập phân.',
                     'Viết riêng hai phần rồi ghép bằng dấu phẩy. Chú ý thứ tự và vị trí từng chữ số khi đối chiếu các lựa chọn.',
                     options=options, selected=options[values.index(value)])

    mixed = re.fullmatch(r'hon so\s+(\d{1,6})\s+(\d{1,6})\s*/\s*(\d{1,6})\s+chuyen thanh phan so thap phan\s+la\s*[:?]', text)
    if mixed and options:
        whole, numerator, denominator = map(int, mixed.groups())
        if not 0 < numerator < denominator or not re.fullmatch(r'10+', str(denominator)):
            return None
        value = Fraction(whole) + Fraction(numerator, denominator)
        # Denominator form matters here: numeric equivalence alone is insufficient.
        candidates = [re.fullmatch(r'(\d{1,9})\s*/\s*(\d{1,9})', option.strip()) for option in options]
        if any(item is None or int(item[2]) == 0 for item in candidates):
            return None
        matches = [index for index, item in enumerate(candidates)
                   if re.fullmatch(r'10+', item[2]) and Fraction(int(item[1]), int(item[2])) == value]
        if len(set(options)) != len(options) or len(matches) != 1:
            return None
        return _plan('Đổi hỗn số thành phân số thập phân', 'Hỗn số gồm phần nguyên cộng với phần phân số; cần giữ đủ cả hai phần.',
                     'Nhân phần nguyên với mẫu số rồi cộng tử số để tìm tử mới, giữ mẫu số. Phân số thập phân phải có mẫu là một lũy thừa của mười.',
                     options=options, selected=options[matches[0]])
    return None
