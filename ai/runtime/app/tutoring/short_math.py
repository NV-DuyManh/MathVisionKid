"""Exact, whole-source proofs for short elementary exercises.

No fuzzy matching or answer guessing: unrecognized wording, extra conditions,
ambiguous choices and inconsistent units keep the independently reviewed path.
"""
import re
import ast
from fractions import Fraction

from app.tutoring.choice_source import numeric_notation, split_choices
from app.tutoring.math_knowledge import normalized_units, unit_conversions
from app.tutoring.service import _fold


_NUMBER = r'\d{1,9}(?:[.,]\d{1,9})?'
_UNITS = r'(?:km|hm|dam|m|dm|cm|mm)(?:[²³])?|ha|kg|hg|dag|g|mg|tan|ta|yen|l|dl|cl|ml|dong'
_UNIT_LABELS = {'tan': 'tấn', 'ta': 'tạ', 'yen': 'yến', 'dong': 'đồng'}


def _number(text):
    text = text.strip()
    if not re.fullmatch(_NUMBER + r'(?:\s*/\s*\d{1,9})?', text):
        raise ValueError('Not one exact number')
    return Fraction(text.replace(',', '.').replace(' ', ''))


def _plan(title, why, how, *, expression='', unit='', options=(), selected='', fraction=False):
    return dict(topic=title, goal='Em tự tính hoặc chọn kết quả rồi kiểm tra lại.', finalAnswerStep=0,
                steps=[dict(title=title, explanation=why, question='Em chọn kết quả nào?' if options else 'Em tính được bao nhiêu?',
                            expression=expression, unit=_UNIT_LABELS.get(unit, unit), choices=list(options), correctChoice=selected,
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
        return _plan(title, why, how, options=options, selected=options[values.index(value)], unit=unit, fraction=fraction)
    return _plan(title, why, how, expression=expression, unit=unit, fraction=fraction)


def _measurement_expression(source, target):
    """One complete simple/compound measurement in a known compatible unit."""
    term = r'(' + _NUMBER + r')\s*(' + _UNITS + r')'
    source = normalized_units(source).strip()
    match = re.fullmatch(term + r'(?:\s*' + term + r')?', source)
    if not match:
        return None
    items = [match.groups()[:2]] + ([match.groups()[2:]] if match[3] is not None else [])
    if len({unit for _, unit in items}) != len(items):
        return None
    terms = []
    for amount, unit in items:
        expression = amount.replace(',', '.')
        if unit != target:
            relation = next((row for row in unit_conversions(f'{amount} {unit} sang {target}')
                if {normalized_units(row['fromUnit']), normalized_units(row['toUnit'])} == {unit, target}), None)
            if relation is None:
                return None
            expression += ('*' if unit == normalized_units(relation['fromUnit']) else '/') + relation['factor']
        terms.append(expression)
    return '+'.join(terms)


def rounded_value(value, place):
    scale = 10**{'hang phan muoi': 1, 'hang phan tram': 2, 'so tu nhien gan nhat': 0}[place]
    shifted = value * scale + Fraction(1, 2)
    return Fraction(shifted.numerator // shifted.denominator, scale)


def _truth_statement(text):
    """Only an explicit true/false task authorizes checking a printed assertion."""
    match = re.fullmatch(r'dung ghi d,? sai ghi s\s*:\s*(.+)', text)
    if not match:
        return None
    statement = normalized_units(match[1]).strip()
    value = None
    worked = ''
    rounding = re.fullmatch(r'(' + _NUMBER + r') lam tron den '
        r'(hang phan muoi|hang phan tram|so tu nhien gan nhat) la (' + _NUMBER + r')[.]?', statement)
    if rounding:
        value = rounded_value(_number(rounding[1]), rounding[2]) == _number(rounding[3])
        why = 'Xác định hàng cần làm tròn và chữ số ngay bên phải, rồi đối chiếu với số mà câu đã nêu.'
        how = 'Chữ số bên phải từ năm trở lên thì tăng hàng cần làm tròn. Nếu nhỏ hơn năm thì giữ nguyên; không tăng theo cảm tính.'
    elif statement.count('=') == 1:
        left, right = statement.rstrip('.').split('=')
        target = re.fullmatch(r'\s*' + _NUMBER + r'\s*(' + _UNITS + r')\s*', right)
        if not target:
            return None
        a, b = _measurement_expression(left, target[1]), _measurement_expression(right, target[1])
        if a is None or b is None:
            return None
        from app.tutoring.lesson import calculate_exact
        from app.tutoring.number_tasks import _decimal
        converted, given = calculate_exact(a), calculate_exact(b)
        value = converted == given
        why = 'Cần đổi hai vế về cùng đơn vị trước khi xét xem chúng có biểu diễn cùng một lượng hay không.'
        how = 'Đổi từng phần của vế trái về đơn vị vế phải, cộng lại rồi so sánh hai giá trị.'
        unit = _UNIT_LABELS.get(target[1], target[1])
        try:
            worked = f'Vế trái đổi được {_decimal(converted)} {unit}, vế phải là {_decimal(given)} {unit}. Hai vế ' + (
                'bằng nhau nên nhận định đúng.' if value else 'khác nhau nên nhận định sai.')
        except ValueError:
            pass  # Keep the exact check even when the decimal is too long for worked help.
    if value is None:
        return None
    plan = _plan('Kiểm tra nhận định', why, how, options=['Đúng', 'Sai'], selected='Đúng' if value else 'Sai')
    if worked:
        plan['steps'][0]['guidance'].insert(1, worked)
    return plan


def _daily_sales_plan(text, options):
    # Prove the entire statement, including the constant-rate condition. Extra
    # discounts, different rates, missing conditions or units require review.
    match = re.fullmatch(
        r'mot cua hang trong (\d{1,3}) ngay ban duoc (' + _NUMBER + r') (kg|g) (gao|duong|thoc|ngo|bot)\. '
        r'hoi trong (\d{1,3}) ngay cua hang ban duoc bao nhieu (kg|g) \4\? '
        r'\(?biet so \4 moi ngay ban duoc la nhu nhau[.)]*', normalized_units(text))
    if not match:
        return None
    days, amount, unit, goods, target_days, target_unit = match.groups()
    if int(days) <= 0 or int(target_days) <= 0 or _number(amount) <= 0 or unit != target_unit:
        return None
    quantity = amount.replace(',', '.')
    checked = _result('Rút về đơn vị', '', '', f'{quantity}/{days}*{target_days}', options, unit)
    if checked is None:
        return None
    label = {'gao': 'gạo', 'duong': 'đường', 'thoc': 'thóc', 'ngo': 'ngô', 'bot': 'bột'}[goods]
    steps = []
    for title, why, how, expression, sentence in [
        (f'Tìm lượng {label} bán mỗi ngày',
         f'Cửa hàng bán đều mỗi ngày. Chia {amount} {unit} cho {days} ngày để tìm lượng bán trong một ngày.',
         'Lấy lượng đã bán chia cho số ngày đã bán, rồi kiểm tra lại bằng phép nhân.',
         f'{quantity}/{days}', f'Lượng {label} bán mỗi ngày là:'),
        (f'Tìm lượng {label} trong {target_days} ngày',
         f'Mỗi ngày bán cùng một lượng. Dùng lượng mỗi ngày vừa tính, nhân với {target_days} ngày mà đề hỏi.',
         'Lấy kết quả bước trước nhân với số ngày cần hỏi. Giữ đúng đơn vị của đề.',
         f'{{s0}}*{target_days}', f'Lượng {label} bán trong số ngày cần hỏi là:'),
    ]:
        steps.append(dict(title=title, explanation=why, question=title + ' được bao nhiêu?',
                          expression=expression, unit=unit, solutionSentence=sentence,
                          initialGuidance=[why, how], guidance=[why, how], hints=[why, how]))
    if options:
        steps.append(dict(title='Chọn đáp án', question='Em chọn phương án nào trong đề?',
                          explanation='Đối chiếu lượng vừa tính với từng phương án, giữ đúng đơn vị.',
                          choices=list(options), correctChoice=checked['steps'][0]['correctChoice'], unit=unit,
                          guidance=['So sánh kết quả vừa tính với từng đáp án trong đề.']))
    return dict(topic='Rút về đơn vị', goal=f'Tìm lượng {label} bán được theo số ngày.', finalAnswerStep=1, steps=steps)


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
    from app.tutoring.number_tasks import verified_plan as open_number_plan
    opened = open_number_plan(problem)
    if opened is not None:
        return opened
    multiple = split_choices(problem, allow_statement=True)
    stem, options = multiple if multiple else (problem, [])
    # Blank working rows are page layout, not additional operands or tasks.
    stem = '\n'.join(row for row in stem.splitlines() if not re.fullmatch(r'[\s=. …]+', row))
    text = _fold(re.sub(r'\s+', ' ', numeric_notation(stem))).strip()
    options = [numeric_notation(option) for option in options]
    text = re.sub(r'^(?:cau|bai)\s+\d+\s*[.):]?\s*(?:\(\s*\d+(?:[.,]\d+)?\s*diem\s*\)\s*)?[.:]?\s*', '', text)
    text = re.sub(r'^[a-h][.)]\s*', '', text)
    text = re.sub(r'^\(\d+(?:[.,]\d+)?\s*diem\)\s*', '', text)
    text = re.sub(r'^khoanh vao chu cai truoc cau tra loi dung[.:]?\s*', '', text)
    truth = _truth_statement(text) if not options else None
    if truth:
        return truth
    # Retain the whole task; remove only a worksheet instruction, never a condition.
    text = re.sub(r'^(?:dat tinh roi tinh|tinh gia tri cua bieu thuc|tinh bang cach thuan tien(?: nhat)?|'
                  r'viet (?:so|cac so do|so hoac so thap phan|so thap phan) thich hop vao cho (?:cham|trong)|'
                  r'dien so thich hop vao cho trong|dien so hoac don vi thich(?: hop)? vao cho cham)[.:]?\s*', '', text)

    from app.tutoring.elementary_choices import verified_choice
    concept = verified_choice(text, [_fold(option) for option in options]) if options else None
    if concept:
        # Numeric folding aids matching, but keep original Vietnamese option text.
        step = concept['steps'][0]
        index = step['choices'].index(step['correctChoice'])
        step['choices'], step['correctChoice'] = options, options[index]
        return concept

    daily_sales = _daily_sales_plan(text, options)
    if daily_sales:
        return daily_sales

    from app.tutoring.area_tasks import verified_plan as area_plan
    area = area_plan(text, options)
    if area is not None:
        return area

    # Exact arithmetic, including a single operation, decimals and fractions.
    arithmetic = re.fullmatch(r'(?:tinh\s*:?\s*|(?:ket qua (?:cua )?phep tinh)\s*)?'
                              r'([\d\s.,()+*/×÷−–:\-x]+?)\s*(?:(?:=\s*(?:\?|\.{2,}|…+)?)|(?:la\s*[:?]))?\s*[.?]?\s*', text)
    if arithmetic:
        expression = arithmetic[1].strip().replace(',', '.')
        expression = re.sub(r'\b(\d+)\s+(\d+)\s*/\s*([1-9]\d*)\b', r'(\1+\2/\3)', expression)
        if re.search(r'[:÷]', expression):
            # In school notation, 5/8 : 7/2 divides two complete fractions.
            # Group fraction operands before translating division signs; leave
            # ordinary slash chains (8/4/2) with their existing associativity.
            expression = ''.join(
                f'({part.strip()})' if re.fullmatch(r'\s*\d+(?:\.\d+)?\s*/\s*\d+(?:\.\d+)?\s*', part) else part
                for part in re.split(r'([()+*×÷:−–\-x])', expression))
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
            if re.fullmatch(r'\d+\s*/\s*\d+\s*[+-]\s*\d+\s*/\s*\d+', expression):
                title = 'Cộng, trừ hai phân số'
                why = 'Các phân số phải có cùng mẫu số để các phần có cùng kích thước trước khi cộng hoặc trừ.'
                how = 'Tìm mẫu chung. Nhân cả tử và mẫu của mỗi phân số với cùng một số để giữ nguyên giá trị; cộng hoặc trừ các tử rồi giữ mẫu chung. Rút gọn kết quả nếu có thể.'
            return _result(title, why, how,
                           expression, options, fraction='/' in expression and '.' not in expression)

    conversion = re.fullmatch(r'(?:dien vao (?:cho cham|cho trong|dau cham) de\s*:?\s*|doi\s+)?'
                             r'(' + _NUMBER + r')\s*(' + _UNITS + r')\s*(?:=|sang)\s*(?:\.{2,}|…+|\?)?\s*(' + _UNITS + r')\s*[.:?]?', normalized_units(text))
    if conversion:
        amount, source, target = conversion.groups()
        conversions = unit_conversions(f'{amount} {source} sang {target}')
        relation = next((r for r in conversions if {normalized_units(r['fromUnit']), normalized_units(r['toUnit'])} == {source, target}), None)
        if not relation:
            return None
        factor = relation['factor']
        operation = '*' if source == normalized_units(relation['fromUnit']) else '/'
        return _result('Đổi đơn vị đo', 'Cần biểu diễn cùng một lượng bằng đơn vị ở bên phải, không thay đổi lượng ban đầu.',
                       f'Từ {_UNIT_LABELS.get(source, source)} sang {_UNIT_LABELS.get(target, target)}, em {"nhân" if operation == "*" else "chia"} với {factor}. Đây là hệ số đổi giữa hai đơn vị; kết quả dùng đơn vị {_UNIT_LABELS.get(target, target)}.',
                       amount.replace(',', '.') + operation + factor, options, target)

    # A single compound measurement, not several independent worksheet questions.
    compound = re.fullmatch(r'(?:(?:viet cac so do sau duoi dang so thap phan|'
        r'so (?:thap phan )?thich hop (?:viet|dien) vao cho cham(?: cua)?)[.:]?\s*)?(?:[ab][.)]\s*)?'
        r'(' + _NUMBER + r')\s*(' + _UNITS + r')\s+(' + _NUMBER + r')\s*(' + _UNITS + r')'
        r'\s*=\s*(?:\.{2,}|…+|\?)\s*(' + _UNITS + r')\s*(?:la\s*[:?])?\s*[.]?', normalized_units(text))
    if compound:
        first, first_unit, second, second_unit, target = compound.groups()
        expression = _measurement_expression(f'{first} {first_unit} {second} {second_unit}', target)
        if expression is None:
            return None
        return _result('Viết số đo theo một đơn vị',
            'Hai phần số đo cùng biểu diễn một lượng. Cần đổi từng phần về đơn vị ở vế phải rồi cộng lại.',
            f'Đổi riêng phần {_UNIT_LABELS.get(first_unit, first_unit)} và phần {_UNIT_LABELS.get(second_unit, second_unit)} sang {_UNIT_LABELS.get(target, target)}. Giữ đủ các hàng thập phân, không ghép các chữ số theo cảm tính.',
            expression, options, target)

    comparison = re.fullmatch(r'dau thich hop dien vao cho cham (.+?)\s*(?:\.{2,}|…+)\s*(.+?)\s+la\s*[:?]', normalized_units(text))
    if comparison and options and set(options) == {'>', '<', '=', 'Không xác định được'}:
        target = re.search('(' + _UNITS + r')$', comparison[2].strip())
        if not target:
            return None
        a, b = (_measurement_expression(side, target[1]) for side in comparison.groups())
        if a is None or b is None:
            return None
        from app.tutoring.lesson import calculate_exact
        left, right = calculate_exact(a), calculate_exact(b)
        return _plan('So sánh hai số đo', 'Hai số đo phải cùng đơn vị thì mới so sánh được.',
            'Đổi các phần của mỗi số đo về đơn vị bên phải, cộng lại nếu cần rồi chọn dấu so sánh.',
            options=options, selected='>' if left > right else '<' if left < right else '=')

    smallest = re.fullmatch(r'trong cac so do khoi luong:\s*(.+?), so do be nhat la\s*[:?]', normalized_units(text))
    if smallest and options:
        items = [item.strip() for item in smallest[1].split(';')]
        if len(items) != 4:
            return None
        from app.tutoring.lesson import calculate_exact
        expressions = [_measurement_expression(item, 'kg') for item in items]
        candidates = [_measurement_expression(item, 'kg') for item in options]
        if any(item is None for item in [*expressions, *candidates]):
            return None
        values, choices = [list(map(calculate_exact, group)) for group in (expressions, candidates)]
        if sorted(values) != sorted(choices) or len(set(choices)) != 4:
            return None
        return _plan('So sánh số đo khối lượng', 'Không so sánh riêng mặt chữ số khi các số đo có dạng hoặc đơn vị khác nhau.',
            'Đổi từng số đo sang ki-lô-gam. Cộng các phần của số đo ghép rồi đối chiếu các giá trị cùng đơn vị.',
            options=options, selected=options[choices.index(min(values))])

    rectangle = re.fullmatch(r'chu vi (?:cua )?hinh chu nhat la (' + _NUMBER + r')\s*(km|m|dm|cm|mm)[.]\s*'
        r'hoi dien tich (?:manh dat|hinh chu nhat) la bao nhieu \2²[.?]\s*'
        r'biet chieu dai hon chieu rong la (' + _NUMBER + r')\s*\2[.]?', normalized_units(text))
    if rectangle:
        perimeter, unit, difference = rectangle.groups()
        p, d = _number(perimeter), _number(difference)
        if p <= 0 or d < 0 or p/2 <= d:
            return None
        expression = f'({perimeter.replace(",", ".")}/2+{difference.replace(",", ".")})/2*({perimeter.replace(",", ".")}/2-{difference.replace(",", ".")})/2'
        return _result('Diện tích hình chữ nhật từ chu vi và hiệu hai cạnh',
            'Nửa chu vi là tổng chiều dài và chiều rộng. Hiệu hai cạnh giúp tìm từng cạnh trước khi tính diện tích.',
            'Chia chu vi cho hai. Lấy tổng hai cạnh cộng hiệu rồi chia hai để tìm chiều dài; lấy tổng trừ hiệu rồi chia hai để tìm chiều rộng. Nhân hai cạnh để tính diện tích.',
            expression, options, unit+'²')

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
