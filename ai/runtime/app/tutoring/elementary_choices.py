"""Whole-question, exact proofs for elementary number concepts with visible choices.

Never use the options to guess an unknown question. Unknown wording, duplicate
values, additional conditions or ambiguous digit positions require review.
"""
import re
import math
from fractions import Fraction


def verified_choice(text, options):
    from app.tutoring.short_math import _NUMBER, _number, _plan, _spoken_integer, rounded_value
    if len(options) != 4 or len(set(options)) != 4:
        return None

    def choose(title, why, how, matches):
        indices = [i for i, yes in enumerate(matches) if yes]
        return _plan(title, why, how, options=options, selected=options[indices[0]]) if len(indices) == 1 else None

    def numbers(value):
        parts = [part.strip() for part in value.split(';')]
        return [_number(part) for part in parts] if len(parts) > 1 else None

    def numeric_choices(value):
        values = [_number(re.sub(r'\s*(?:kg|so)$', '', option)) for option in options]
        if len(set(values)) != len(values):
            return [False] * 4
        return [v == value for v in values]

    maximum_rounding = re.fullmatch(r'so thap phan lon nhat nao duoc lam tron den (' + _NUMBER +
        r') (?:khi lam tron )?(?:den )?so tu nhien gan nhat\?', text)
    if maximum_rounding:
        target = _number(maximum_rounding[1])
        values = [_number(option) for option in options]
        eligible = [value for value in values if value >= 0 and rounded_value(value, 'so tu nhien gan nhat') == target]
        if not eligible or len(set(values)) != len(values):
            return None
        return choose('Chọn số lớn nhất thỏa điều kiện làm tròn',
            'Làm tròn từng số đến số tự nhiên gần nhất rồi giữ những số có kết quả bằng số đề yêu cầu.',
            'Trong các số thỏa điều kiện, chọn số lớn nhất; không chỉ chọn số gần kết quả nhất.',
            [value == max(eligible) for value in values])

    # These are proofs of an explicit, pupil-confirmed diagram transcription,
    # not an interpretation of image pixels or an inference from the options.
    circles = re.fullmatch(r'hon so thich hop bieu dien so phan hinh tron duoc to mau la: \[(.+)\]', text)
    pentagons = re.fullmatch(r'hon so bieu dien phan to mau trong hinh la: hinh ve gom 2 hinh ngu giac\. '
        r'hinh ngu giac ben trai duoc chia thanh (\d{1,2}) phan bang nhau va to mau ca (\d{1,2}) phan\. '
        r'hinh ngu giac ben phai duoc chia thanh (\d{1,2}) phan bang nhau va to mau (\d{1,2}) phan\.', text)
    if circles or pentagons:
        if circles:
            rows = circles[1].split('. ')
            parts = [re.fullmatch(r'hinh (\d): chia (\d{1,2}) phan bang nhau, (\d{1,2}) phan to mau, (\d{1,2}) phan khong to mau[.]?', row) for row in rows]
            if not 1 <= len(parts) <= 8 or any(part is None for part in parts):
                return None
            counts = [tuple(map(int, part.groups())) for part in parts]
            if any(i != expected or not 2 <= d <= 12 or c + blank != d for expected, (i, d, c, blank) in enumerate(counts, 1)):
                return None
            values = [Fraction(c, d) for _, d, c, _ in counts]
        else:
            d, full, other_d, colored = map(int, pentagons.groups())
            if not 2 <= d <= 12 or full != d or other_d != d or not 0 <= colored <= d:
                return None
            values = [Fraction(full, d), Fraction(colored, d)]
        candidates = [re.fullmatch(r'(\d+)\s+(\d+)\s*/\s*([1-9]\d*)', option) for option in options]
        if any(item is None or int(item[2]) >= int(item[3]) for item in candidates):
            return None
        numeric = [Fraction(int(item[1])) + Fraction(int(item[2]), int(item[3])) for item in candidates]
        if len(set(numeric)) != 4:
            return None
        return choose('Đọc hỗn số từ phần tô màu', 'Mỗi hình nguyên gồm các phần bằng nhau. Gộp những hình tô đủ và phần tô chưa đủ để biểu diễn một lượng.',
            'Đếm số hình tô đủ làm phần nguyên; phần còn lại có tử là số phần tô và mẫu là số phần bằng nhau trong một hình.',
            [value == sum(values) for value in numeric])

    jugs = re.fullmatch(r'moi ca dung mot luong nuoc nhu hinh duoi day: \[4 ca nuoc\. (.+)\] ca nao dung it nuoc nhat\?', text)
    if jugs:
        parts = [re.fullmatch(r'ca (\d): (' + _NUMBER + r'(?:/[1-9]\d{0,8})?)\s*(ml|l)[.]?', row)
            for row in jugs[1].split('. ')]
        if len(parts) != 4 or any(part is None for part in parts) or [part[1] for part in parts] != list('1234'):
            return None
        values = [_number(part[2]) * (1000 if part[3] == 'l' else 1) for part in parts]
        if any(value < 0 for value in values) or values.count(min(values)) != 1:
            return None
        if sorted(options) != [f'ca so {i}' for i in range(1, 5)]:
            return None
        return choose('So sánh lượng nước', 'Các nhãn dùng lít và mi li lít, nên phải đổi về cùng đơn vị trước khi so sánh.',
            'Đổi mỗi lượng nước về mi li lít, giữ chính xác phần phân số rồi tìm ca có giá trị nhỏ nhất.',
            [option == f'ca so {values.index(min(values))+1}' for option in options])

    m = re.fullmatch(r'(?:so thap phan (?:gom|co) )?(.+?) (?:duoc )?viet la[:?]?', text)
    if m:
        value = Fraction(0)
        places = set()
        for part in m[1].split(','):
            item = re.fullmatch(r'\s*(\d+|[a-z ]+?) (chuc|don vi|phan muoi|phan tram|phan nghin)\s*', part)
            if not item or item[2] in places:
                return None
            amount = int(item[1]) if item[1].isdigit() else _spoken_integer(item[1])
            if amount is None:
                return None
            places.add(item[2])
            value += amount * {'chuc': Fraction(10), 'don vi': Fraction(1), 'phan muoi': Fraction(1,10),
                'phan tram': Fraction(1,100), 'phan nghin': Fraction(1,1000)}[item[2]]
        return choose('Viết số theo các hàng', 'Mỗi dữ kiện chỉ rõ số đơn vị ở một hàng.',
            'Đặt chữ số vào đúng hàng; hàng chưa có dữ kiện được giữ bằng số không, không ghép các số tùy ý.', numeric_choices(value))

    m = re.fullmatch(r'tim so tu nhien de dien vao cho cham sau\s*:\s*('+_NUMBER+r')\s*>\s*(?:\.{2,}|…+)\s*>\s*('+_NUMBER+r')', text)
    if m:
        high, low = _number(m[1]), _number(m[2])
        vals = [_number(option) for option in options]
        return choose('Tìm số tự nhiên trong khoảng', 'Số cần chọn phải thỏa mãn cả hai dấu so sánh.',
            'So sánh mỗi lựa chọn với cận trên và cận dưới; chỉ giữ số tự nhiên nằm giữa cả hai.',
            [v.denominator == 1 and low < v < high for v in vals])

    cards = re.fullmatch(r'tu nam tam the (\d)\s*;\s*(\d)\s*;\s*(\d)\s*;\s*(\d) va (?:dau phay,|,) co the lap duoc tat ca bao nhieu so thap phan co ba chu so o phan thap phan va cac so do be hon 1\?', text)
    digits = re.fullmatch(r'cho bon chu so\s*:?\s*(\d)\s*;\s*(\d)\s*;\s*(\d)\s*;\s*(\d)\. co the viet duoc nhieu nhat bao nhieu so thap phan co mat du bon chu so tren ma be hon 1\?', text)
    if cards or digits:
        values = (cards or digits).groups()
        if len(set(values)) != 4 or '0' not in values:
            return None
        return choose('Lập số thập phân từ các thẻ', 'Số bé hơn một phải có phần nguyên bằng không.',
            'Giữ thẻ không ở phần nguyên. Hoán đổi ba thẻ còn lại ở phần thập phân, mỗi thẻ dùng một lần.', numeric_choices(math.factorial(3)))

    m = re.fullmatch(r'phan so nao duoi day la phan so thap phan[.:?]?', text)
    if m:
        fractions = [re.fullmatch(r'\d+\s*/\s*([1-9]\d*)', option) for option in options]
        if any(item is None for item in fractions):
            return None
        return choose('Nhận biết phân số thập phân', 'Xem mẫu số của từng phân số đúng như đề đã viết.',
            'Phân số thập phân có mẫu là mười, một trăm, một nghìn hoặc lũy thừa tiếp theo của mười.',
            [bool(re.fullmatch(r'10+', item[1])) for item in fractions])

    m = re.fullmatch(r'(?:phan so\s+)?(\d+)\s*/\s*([1-9]\d*) viet (?:o )?dang hon so la[:?]?', text)
    if m:
        n, d = map(int, m.groups())
        if n <= d or n % d == 0:
            return None
        wanted = (n//d, n % d, d)
        choices = [re.fullmatch(r'(\d+)\s+(\d+)\s*/\s*([1-9]\d*)', option) for option in options]
        if any(item is None for item in choices):
            return None
        return choose('Đổi phân số thành hỗn số', 'Chia tử số cho mẫu số để tìm phần nguyên và phần còn lại.',
            'Thương là phần nguyên, số dư là tử số của phần phân số; giữ mẫu số ban đầu.',
            [tuple(map(int, item.groups())) == wanted for item in choices])

    m = re.fullmatch(r'hon so (\d+)\s+(\d+)\s*/\s*([1-9]\d*) (?:chuyen thanh|duoc viet duoi dang) so thap phan la[:?]?', text)
    if m:
        w, n, d = map(int, m.groups())
        if not 0 < n < d or not re.fullmatch(r'10+', str(d)):
            return None
        return choose('Viết hỗn số thành số thập phân', 'Hỗn số bằng phần nguyên cộng với phần phân số.',
            'Mẫu số cho biết cần bao nhiêu hàng thập phân. Giữ các số không chỉ vị trí nếu có.',
            numeric_choices(Fraction(w) + Fraction(n, d)))

    m = re.fullmatch(r'so thap phan ('+_NUMBER+r') (?:duoc )?viet duoi dang hon so (?:la)?[:?]?', text)
    if m and ',' in m[1]:
        w, tail = m[1].split(',')
        candidates = [re.fullmatch(r'(\d+)\s+(\d+)\s*/\s*([1-9]\d*)', option) for option in options]
        if any(item is None for item in candidates):
            return None
        return choose('Viết số thập phân thành hỗn số', 'Giữ phần nguyên và biểu diễn phần thập phân bằng phân số thập phân.',
            'Đếm số hàng sau dấu phẩy để xác định mẫu số. Tử số là phần chữ số sau dấu phẩy.',
            [tuple(map(int, item.groups())) == (int(w), int(tail), 10**len(tail)) for item in candidates])

    m = re.fullmatch(r'chu so (\d) trong so thap phan ('+_NUMBER+r') co gia tri la[:?]?', text)
    if m:
        digits = m[2].split(',')
        if m[2].count(m[1]) != 1:
            return None
        if m[1] in digits[0]:
            value = Fraction(int(m[1])*10**(len(digits[0])-digits[0].index(m[1])-1))
        else:
            value = Fraction(int(m[1]), 10**(digits[1].index(m[1])+1))
        return choose('Giá trị của chữ số theo hàng', 'Giá trị của chữ số phụ thuộc vào hàng mà nó đứng.',
            'Xác định vị trí so với dấu phẩy: phần mười, phần trăm, phần nghìn; không chỉ nhìn mặt chữ số.', numeric_choices(value))

    m = re.fullmatch(r'so thap phan (be|lon) nhat trong cac so ('+_NUMBER+r'(?:\s*;\s*'+_NUMBER+r')+)\s*(?:la)?[:?]?', text)
    if m:
        values = numbers(m[2])
        return choose('So sánh số thập phân', 'So sánh phần nguyên trước, rồi từng hàng thập phân từ trái sang phải.',
            'Có thể thêm số không vào cuối phần thập phân để các số có cùng số hàng.', numeric_choices((min if m[1] == 'be' else max)(values)))

    m = re.fullmatch(r'(?:sap xep|viet) cac so (?:thap phan )?('+_NUMBER+r'(?:\s*;\s*'+_NUMBER+r')+) theo thu tu (tu be den lon|tu lon den be|tang dan|giam dan)\s*(?:la)?[:?.]?', text)
    direction = m[2] if m else None
    originals = numbers(m[1]) if m else None
    if not m and re.fullmatch(r'day so nao (?:duoc xep|duoc sap xep) theo thu tu (?:tang dan|tu be den lon)[:?]?', text):
        direction = 'tang dan'
    if direction:
        candidates = [numbers(option) for option in options]
        if any(value is None for value in candidates):
            return None
        reverse = direction in {'tu lon den be', 'giam dan'}
        return choose('Sắp xếp số thập phân', 'So sánh từng hàng để xếp các số theo đúng chiều mà đề yêu cầu.',
            'So phần nguyên trước. Nếu phần nguyên bằng nhau, so lần lượt phần mười, phần trăm, phần nghìn.',
            [items == sorted(items, reverse=reverse) and (originals is None or sorted(items) == sorted(originals)) for items in candidates])

    rounding = re.fullmatch(r'(?:so )?('+_NUMBER+r') lam tron den (hang phan muoi|hang phan tram|so tu nhien gan nhat) (?:ta )?duoc(?: so)?[:?]?', text)
    if not rounding:
        rounding = re.fullmatch(r'lam tron so ('+_NUMBER+r') den (hang phan muoi|hang phan tram|so tu nhien gan nhat) (?:ta )?duoc[:?]?', text)
    weight = re.fullmatch(r'ban ([a-z ]+) nang ('+_NUMBER+r') kg\. can nang cua ban \1 khi lam tron den so tu nhien gan nhat la[:?]?', text)
    if rounding or weight:
        value = _number(rounding[1] if rounding else weight[2])
        rounded = rounded_value(value, rounding[2] if rounding else 'so tu nhien gan nhat')
        return choose('Làm tròn số', 'Xác định hàng cần làm tròn rồi nhìn chữ số ngay bên phải hàng đó.',
            'Nếu chữ số bên phải từ năm trở lên thì tăng hàng cần làm tròn; nếu nhỏ hơn năm thì giữ nguyên.', numeric_choices(rounded))

    m = re.fullmatch(r'so thap phan ('+_NUMBER+r') doc la[:?]?', text)
    if m and ',' in m[1]:
        w, tail = m[1].split(',')
        if tail.startswith('0'):
            return None  # A value-only comparison cannot verify spoken leading zero positions.
        read = [re.fullmatch(r'([a-z ]+) phay ([a-z ]+)', option) for option in options]
        return choose('Đọc số thập phân', 'Đọc phần nguyên, tiếng phẩy, rồi phần thập phân.',
            'Giữ đủ giá trị và vị trí của các chữ số ở phần thập phân.',
            [bool(item and _spoken_integer(item[1]) == int(w) and _spoken_integer(item[2]) == int(tail)) for item in read])
    return None
