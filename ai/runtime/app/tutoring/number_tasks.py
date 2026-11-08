"""Exact choices for bounded open number tasks, not a general prose solver.

Generated alternatives are authorized only by re-solving the COMPLETE source.
Unknown instructions, filled tables and extra conditions retain model review.
"""
import re
from fractions import Fraction

from app.tutoring.choice_source import numeric_notation
from app.tutoring.service import _fold


def _decimal(value):
    denominator, places = value.denominator, 0
    for factor in (2, 5):
        count = 0
        while denominator % factor == 0:
            denominator //= factor
            count += 1
        places = max(places, count)
    if denominator != 1 or places > 9:
        raise ValueError('Only exact terminating decimals')
    digits = str(abs(value.numerator) * 10**places // value.denominator).zfill(places + 1)
    return ('-' if value < 0 else '') + (digits[:-places] + ',' + digits[-places:] if places else digits)


def _choices(title, why, how, values):
    from app.tutoring.short_math import _plan
    values = list(dict.fromkeys(values))
    if not 2 <= len(values) <= 4 or any(len(item) > 100 for item in values):
        return None
    selected = values[0]
    # Answer position must not always be the first button. Source values and
    # working stay unchanged; the exact solver reproduces this order on review.
    offset = sum(map(ord, selected)) % len(values)
    values = values[offset:] + values[:offset]
    return _plan(title, why, how, options=values, selected=selected)


def verified_plan(problem):
    try:
        return _verified_plan(problem)
    except (ValueError, ArithmeticError, TypeError):
        return None


def _verified_plan(problem):
    from app.tutoring.short_math import _NUMBER, _number, _spoken_integer, rounded_value
    if not isinstance(problem, str) or len(problem) > 4000 or '[?]' in problem:
        return None
    text = _fold(re.sub(r'\s+', ' ', numeric_notation(problem))).strip()
    text = re.sub(r'^(?:cau|bai)\s+\d+\s*[.):]?\s*(?:\(\d+(?:[.,]\d+)? diem\)\s*)?[.:]?\s*', '', text)
    text = re.sub(r'^\(\d+(?:[.,]\d+)? diem\)\s*', '', text)
    text = re.sub(r'^[a-h][.)]\s*', '', text)

    sorting = re.fullmatch(r'(?:viet|sap xep) cac so (?:thap phan )?(' + _NUMBER +
        r'(?:\s*;\s*' + _NUMBER + r'){1,9}) theo thu tu (tu lon den be|tu be den lon|tang dan|giam dan)[.]?', text)
    if sorting:
        values = [_number(part) for part in sorting[1].split(';')]
        correct = sorted(values, reverse=sorting[2] in {'tu lon den be', 'giam dan'})
        alternatives = [correct, list(reversed(correct)), correct[1:] + correct[:1], correct[-1:] + correct[:-1]]
        return _choices('Sắp xếp các số', 'So sánh phần nguyên trước rồi so từng hàng thập phân từ trái sang phải.',
            'Giữ đủ các số của đề, xếp theo đúng chiều được hỏi rồi kiểm tra từng cặp cạnh nhau.',
            ['; '.join(map(_decimal, items)) for items in alternatives])

    rounding = re.fullmatch(r'(?:so )?(' + _NUMBER + r') lam tron den '
        r'(hang phan muoi|hang phan tram|so tu nhien gan nhat) duoc so\s*:\s*(?:\.{2,}|…+)', text)
    if rounding:
        value = rounded_value(_number(rounding[1]), rounding[2])
        unit = Fraction(1, 10**{'hang phan muoi': 1, 'hang phan tram': 2, 'so tu nhien gan nhat': 0}[rounding[2]])
        return _choices('Làm tròn số', 'Đề chỉ rõ hàng cần làm tròn. Chữ số ngay bên phải quyết định giữ hay tăng hàng đó.',
            'Từ năm trở lên thì tăng hàng cần làm tròn; nhỏ hơn năm thì giữ nguyên, bỏ các hàng ở sau.',
            [_decimal(item) for item in (value, value + unit, value - unit, value + 2*unit)])

    interval = re.fullmatch(r'cac so tu nhien thich hop dien vao cho trong la:\s*(' + _NUMBER +
        r')\s*<\s*(?:\.{2,}|…+)\s*<\s*(' + _NUMBER + r')[.]?', text)
    if interval:
        low, high = map(_number, interval.groups())
        first, last = low.numerator // low.denominator + 1, -(-high.numerator // high.denominator) - 1
        if first < 0 or not 1 <= last - first + 1 <= 12:
            return None
        answers = [range(first, last + 1), range(first - 1, last + 1), range(first, last + 2), range(first - 1, last + 2)]
        return _choices('Tìm số tự nhiên trong khoảng', 'Dấu bé hơn ở cả hai phía yêu cầu số cần tìm nằm hẳn giữa hai cận.',
            'Bắt đầu từ số tự nhiên đầu tiên lớn hơn cận dưới, đếm tiếp và dừng trước cận trên. Không lấy hai đầu mút.',
            ['; '.join(map(str, values)) for values in answers])

    writing = re.fullmatch(r'viet so thap phan co:\s*([a-z ,]+):\s*(?:\.{2,}|…+)', text)
    if writing:
        total, places = Fraction(0), set()
        scales = {'tram': Fraction(100), 'chuc': Fraction(10), 'don vi': Fraction(1),
            'phan muoi': Fraction(1, 10), 'phan tram': Fraction(1, 100), 'phan nghin': Fraction(1, 1000)}
        for part in writing[1].split(','):
            item = re.fullmatch(r'\s*([a-z ]+?) (tram|chuc|don vi|phan muoi|phan tram|phan nghin)\s*', part)
            if not item or item[2] in places:
                return None
            amount = _spoken_integer(item[1])
            if amount is None:
                return None
            places.add(item[2]); total += amount * scales[item[2]]
        return _choices('Viết số thập phân theo các hàng', 'Mỗi cụm trong đề cho số đơn vị thuộc một hàng cụ thể, cần giữ đúng vị trí của chúng.',
            'Viết phần nguyên rồi đặt từng phần mười, phần trăm, phần nghìn vào đúng hàng. Giữ số không ở những hàng còn trống.',
            [_decimal(value) for value in (total, total + Fraction(1, 10), total + Fraction(1, 100), total + 1)])

    from app.tutoring.short_math import _UNITS, _UNIT_LABELS, _measurement_expression
    from app.tutoring.math_knowledge import _UNITS as units, normalized_units
    fill_unit = re.fullmatch(r'dien so hoac don vi thich(?: hop)? vao cho cham:\s*(.+?)\s*=\s*(' + _NUMBER + r')\s*(?:\.{2,}|…+)', text)
    if fill_unit:
        from app.tutoring.lesson import calculate_exact
        matches, alternatives = [], []
        for symbol in units:
            target = normalized_units(symbol)
            if not re.fullmatch(_UNITS, target):
                continue
            expression = _measurement_expression(fill_unit[1], target)
            if expression is not None:
                label = _UNIT_LABELS.get(target, target)
                alternatives.append(label)
                if calculate_exact(expression) == _number(fill_unit[2]):
                    matches.append(label)
        if len(matches) != 1:
            return None
        answer = matches[0]
        return _choices('Chọn đơn vị còn thiếu', 'Cùng một lượng có giá trị số khác nhau khi biểu diễn bằng các đơn vị khác nhau.',
            'Đổi hai phần số đo về từng đơn vị phù hợp rồi cộng lại. Chọn đơn vị cho đúng giá trị số đã in ở vế phải.',
            [answer, *[unit for unit in alternatives if unit != answer][:3]])

    table = re.fullmatch(r'hoan thanh bang sau:\s*\|\s*phan so\s*\|\s*phan so thap phan\s*\|\s*so thap phan\s*\|\s*'
        r'((?:\|\s*\d{1,6}\s*/\s*[1-9]\d{0,5}\s*\|\s*\|\s*\|\s*){1,6})', text)
    if table:
        fractions = re.findall(r'\d+\s*/\s*\d+', table[1])
        steps = []
        for fraction in fractions:
            value = Fraction(fraction.replace(' ', ''))
            decimal = _decimal(value)
            places = len(decimal.split(',')[1]) if ',' in decimal else 1
            denominator = 10**places
            numerator = value * denominator
            if numerator.denominator != 1:
                return None
            n = numerator.numerator
            options = [f'{n}/{denominator}; {decimal}',
                f'{n+1}/{denominator}; {_decimal(Fraction(n+1, denominator))}',
                f'{n}/{denominator}; {_decimal(Fraction(n+1, denominator))}',
                f'{n+1}/{denominator}; {decimal}']
            row = _choices('Đổi phân số ' + fraction, 'Phân số thập phân cần có mẫu là mười, một trăm, một nghìn hoặc lũy thừa tiếp theo của mười.',
                'Nhân cả tử và mẫu với cùng một số để được mẫu thích hợp. Viết số thập phân theo mẫu mới; giữ số không chỉ vị trí. Chọn cặp phân số và số thập phân cho cùng dòng.', options)
            if row is None:
                return None
            steps.extend(row['steps'])
        return dict(topic='Hoàn thành bảng phân số', goal='Đổi từng phân số thành phân số thập phân và số thập phân.',
            steps=steps, finalAnswerStep=None)
    return None
