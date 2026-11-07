"""Complete-source proofs for rectangle and remaining-land area tasks.

Only these explicit relationships are supported. Added conditions, unknown
units, multiple requested quantities or unclear shares retain reviewed AI.
"""
import re
from fractions import Fraction


def verified_plan(text, options):
    from app.tutoring.short_math import _NUMBER, _result, _plan, _measurement_expression
    from app.tutoring.math_knowledge import normalized_units
    text = normalized_units(text)
    rice = re.fullmatch(r'gia dinh ([a-z]{1,20}) co mot thua ruong dang hinh chu nhat co chieu dai (' + _NUMBER +
        r') m, chieu dai gap (' + _NUMBER + r') lan chieu rong\. gia dinh \1 trong lua tren thua ruong do\. '
        r'cu (' + _NUMBER + r') m² thu hoach duoc (\d{1,3}/[1-9]\d{0,2}) kg thoc\. hoi: '
        r'a\) gia dinh \1 thu duoc bao nhieu ta thoc tren thua ruong do\? '
        r'b\) biet moi kg thoc duoc mua voi gia la (' + _NUMBER +
        r') dong\. vay neu ban het so thoc do thi gia dinh \1 thu duoc bao nhieu tien\?', text)
    if rice:
        if options:
            return None
        length, ratio, area, amount, price = [item.replace(',', '.') for item in rice.groups()[1:]]
        if any(Fraction(value) <= 0 for value in (length, ratio, area, amount, price)) or Fraction(ratio) < 1:
            return None
        steps = []
        for title, why, how, expression, unit, sentence in [
            ('Tính chiều rộng', 'Chiều dài gấp một số lần chiều rộng. Muốn tìm chiều rộng cần chia chiều dài cho số lần đó.',
             'Lấy chiều dài chia số lần đã cho, giữ đơn vị mét.', f'{length}/{ratio}', 'm', 'Chiều rộng thửa ruộng là:'),
            ('Tính diện tích ruộng', 'Ruộng hình chữ nhật có diện tích bằng chiều dài nhân chiều rộng.',
             'Nhân chiều dài với chiều rộng vừa tìm.', f'{length}*{{s0}}', 'm²', 'Diện tích thửa ruộng là:'),
            ('Tính khối lượng thóc', 'Năng suất được ghi rõ bằng ki lô gam trên một nhóm diện tích.',
             'Chia diện tích ruộng cho diện tích một nhóm rồi nhân năng suất.', f'{{s1}}/{area}*({amount})', 'kg', 'Khối lượng thóc thu hoạch là:'),
            ('Đổi sang tạ', 'Câu đầu hỏi khối lượng bằng tạ. Một tạ bằng một trăm ki lô gam.',
             'Chia khối lượng theo ki lô gam cho một trăm.', '{s2}/100', 'tạ', 'Khối lượng thóc tính theo tạ là:'),
            ('Tính tiền bán thóc', 'Đơn giá áp dụng cho mỗi ki lô gam, nên dùng khối lượng theo ki lô gam.',
             'Lấy khối lượng ở bước tính ki lô gam nhân đơn giá.', f'{{s2}}*{price}', 'đồng', 'Số tiền bán thóc là:'),
        ]:
            step = _plan(title, why, how, expression=expression, unit=unit)['steps'][0]
            step['solutionSentence'] = sentence
            steps.append(step)
        return dict(topic='Diện tích, năng suất và tiền bán thóc', goal='Tính hai ý với đơn vị năng suất đã xác nhận.', steps=steps, finalAnswerStep=4)
    difference = re.fullmatch(r'tong dien tich hai manh dat trong khoai tay va ngo la (.+?)\. '
        r'dien tich manh dat trong khoai tay nho hon dien tich manh dat trong ngo la\s*(' + _NUMBER +
        r') m²\. vay dien tich manh dat trong khoai tay la:', text)
    if difference:
        total = _measurement_expression(difference[1], 'm²')
        if total is None:
            return None
        from app.tutoring.lesson import calculate_exact
        if not 0 < Fraction(difference[2].replace(',', '.')) < calculate_exact(total):
            return None
        why = 'Hai mảnh đất có tổng và hiệu đã biết. Bớt phần chênh lệch khỏi tổng thì còn hai phần bằng nhau, mỗi phần bằng diện tích mảnh nhỏ.'
        how = 'Đổi tổng diện tích về mét vuông, trừ hiệu rồi chia đôi. Đối chiếu với từng lựa chọn cùng đơn vị.'
        return _result('Tìm diện tích mảnh đất nhỏ', why, how,
            f'(({total})-{difference[2].replace(",", ".")})/2', options, 'm²')
    match = re.fullmatch(r'mot khu dat dang hinh chu nhat co chieu dai (' + _NUMBER +
        r') m, chieu rong bang (\d{1,3}/[1-9]\d{0,2}) chieu dai\. '
        r'hoi khu dat do co dien tich la bao nhieu ha\?', text)
    if match:
        length, share = match.groups()
        if Fraction(length.replace(',', '.')) <= 0 or not 0 < Fraction(share) <= 1:
            return None
        expression = f'{length.replace(",", ".")}*({share})'
        result = _result('Chọn diện tích khu đất',
            'Đối chiếu diện tích đã tính theo héc-ta với các phương án của đề.',
            'Giữ cùng đơn vị héc-ta khi đối chiếu kết quả.',
            f'{expression}*{length.replace(",", ".")}/10000', options, 'ha')
        if result is None:
            return None
        descriptions = [
            ('Tìm chiều rộng', 'Chiều rộng là một phần của chiều dài. Chia chiều dài theo mẫu số rồi lấy số phần mà tử số chỉ.',
             'Lấy chiều dài nhân phân số đã cho. Hai kích thước đều phải dùng đơn vị mét.', expression, 'm'),
            ('Tính diện tích khu đất', 'Hình chữ nhật gồm các hàng có cùng chiều rộng. Diện tích bằng chiều dài nhân chiều rộng vừa tìm.',
             'Lấy chiều dài nhân kết quả bước trước. Hai độ dài dùng mét nên diện tích dùng mét vuông.',
             f'{length.replace(",", ".")}*{{s0}}', 'm²'),
            ('Đổi diện tích sang héc-ta', 'Đề hỏi diện tích bằng héc-ta, còn bước trước tính bằng mét vuông. Cần đổi cách biểu diễn cùng một diện tích.',
             'Mỗi héc-ta bằng mười nghìn mét vuông. Chia diện tích vừa tìm cho mười nghìn rồi ghi đúng đơn vị.', '{s1}/10000', 'ha'),
        ]
        steps = []
        for title, why, how, expr, unit in descriptions:
            step = _plan(title, why, how, expression=expr, unit=unit)['steps'][0]
            step['solutionSentence'] = {'m': 'Chiều rộng khu đất là:', 'm²': 'Diện tích khu đất theo mét vuông là:', 'ha': 'Diện tích khu đất theo héc-ta là:'}[unit]
            steps.append(step)
        if options:
            steps.append(result['steps'][0])
        return dict(topic='Diện tích hình chữ nhật', goal='Tính diện tích và đổi về đơn vị đề yêu cầu.', steps=steps, finalAnswerStep=2)

    # Per-area prices and yields need their full rate and unit, not just the
    # rectangle dimensions. Never infer a missing crop-yield unit from an answer.
    floor = re.fullmatch(r'mot nen nha hinh chu nhat co chieu dai (' + _NUMBER +
        r')m, chieu rong bang (\d{1,3}/[1-9]\d{0,2}) chieu dai\. nguoi ta lat nen nha do bang cac vien gach hinh vuong canh (' + _NUMBER +
        r')dm\. a\) hoi can mua bao nhieu vien gach de lat kin nen nha do\? b\) biet rang (' + _NUMBER +
        r')m² loai gach do gia (' + _NUMBER + r') dong, hoi can bao nhieu tien de lat nen nha\? '
        r'\(dien tich phan mach vua khong dang ke\)\.', text)
    harvest = re.fullmatch(r'mot manh ruong hinh chu nhat co chieu dai (' + _NUMBER +
        r')m, chieu rong bang (\d{1,3}/[1-9]\d{0,2}) chieu dai\. a\. tinh dien tich manh ruong do\? '
        r'b\. nguoi ta trong san tren manh ruong do, biet rang cu (' + _NUMBER + r')m² thi thu hoach duoc (' + _NUMBER +
        r')kg san\. hoi tren ca manh ruong do thu hoach duoc bao nhieu ta san\?', text)
    wood = re.fullmatch(r'chu ([a-z]{1,20}) thue mot so nguoi tho lat san go cho nen nha hinh chu nhat dai (' + _NUMBER +
        r') m va chieu rong (' + _NUMBER + r')m\. cu (' + _NUMBER + r')m² san go phai tra (' + _NUMBER +
        r') dong \(gom ca tien san go va tien cong\)\. hoi chu \1 can tra bao nhieu tien de lat nen can nha do\.', text)
    if floor or harvest or wood:
        if (floor or harvest) and options:
            return None
        values = [item.replace(',', '.') for item in ((floor or harvest).groups() if not wood else wood.groups()[1:])]
        if any(Fraction(item) <= 0 for item in values) or (not wood and Fraction(values[1]) > 1):
            return None
        if wood:
            length, width, rate_area, price = values
            descriptions = [
                ('Tính diện tích nền nhà', 'Muốn tính tiền lát sàn, trước hết cần biết diện tích hình chữ nhật.',
                 'Nhân chiều dài với chiều rộng, cùng dùng đơn vị mét.', f'{length}*{width}', 'm²', 'Diện tích nền nhà là:'),
                ('Tính tiền lát sàn', 'Đơn giá trong đề áp dụng cho một nhóm diện tích, gồm cả vật liệu và tiền công.',
                 'Chia diện tích nền cho diện tích của một nhóm, rồi nhân với giá một nhóm.', f'{{s0}}/{rate_area}*{price}', 'đồng', 'Số tiền cần trả là:'),
            ]
            checked = _result('Chọn số tiền', 'Đối chiếu số tiền vừa tính với các phương án.',
                'Giữ đúng đơn vị đồng khi so sánh.', f'{length}*{width}/{rate_area}*{price}', options, 'dong')
            if checked is None:
                return None
        else:
            length, share = values[:2]
            descriptions = [
                ('Tính chiều rộng', 'Chiều rộng bằng phân số đã cho của chiều dài.',
                 'Lấy chiều dài nhân phân số chỉ chiều rộng.', f'{length}*({share})', 'm', 'Chiều rộng mảnh đất là:'),
                ('Tính diện tích', 'Diện tích hình chữ nhật bằng tích của hai kích thước cùng đơn vị.',
                 'Nhân chiều dài với chiều rộng vừa tìm.', f'{length}*{{s0}}', 'm²', 'Diện tích mảnh đất là:'),
            ]
            if floor:
                side, rate_area, price = values[2:]
                descriptions += [
                    ('Tính diện tích một viên gạch', 'Viên gạch hình vuông có diện tích bằng cạnh nhân với cạnh.',
                     'Cạnh dùng đề xi mét nên diện tích viên gạch dùng đề xi mét vuông.', f'{side}*{side}', 'dm²', 'Diện tích một viên gạch là:'),
                    ('Tính số viên gạch', 'Nền nhà được phủ kín bởi các viên gạch như nhau. Cần dùng cùng đơn vị diện tích để chia.',
                     'Đổi diện tích nền từ mét vuông sang đề xi mét vuông, rồi chia cho diện tích một viên.', '{s1}*100/{s2}', 'viên', 'Số viên gạch cần mua là:'),
                    ('Tính tiền lát nền', 'Giá trong đề ứng với một nhóm diện tích, không phải một viên gạch.',
                     'Dùng diện tích nền theo mét vuông chia cho diện tích một nhóm rồi nhân giá của nhóm.', f'{{s1}}/{rate_area}*{price}', 'đồng', 'Số tiền cần trả là:'),
                ]
                # A whole floor cannot use a non-integral number of these tiles.
                from app.tutoring.lesson import calculate_exact
                if calculate_exact(f'{length}*({share})*{length}*100/({side}*{side})').denominator != 1:
                    return None
            else:
                rate_area, yield_kg = values[2:]
                descriptions += [
                    ('Tính lượng sắn theo ki lô gam', 'Năng suất cho biết lượng sắn thu được trên một nhóm diện tích.',
                     'Chia diện tích ruộng cho diện tích một nhóm rồi nhân lượng sắn của nhóm.', f'{{s1}}/{rate_area}*{yield_kg}', 'kg', 'Khối lượng sắn thu hoạch là:'),
                    ('Đổi khối lượng sang tạ', 'Đề yêu cầu trả lời bằng tạ, còn bước trước tính theo ki lô gam.',
                     'Một tạ bằng một trăm ki lô gam. Chia khối lượng vừa tính cho một trăm.', '{s2}/100', 'tạ', 'Khối lượng sắn tính theo tạ là:'),
                ]
        steps = []
        for title, why, how, expr, unit, sentence in descriptions:
            step = _plan(title, why, how, expression=expr, unit=unit)['steps'][0]
            step['solutionSentence'] = sentence
            steps.append(step)
        final = len(steps) - 1
        if wood and options:
            steps.append(checked['steps'][0])
        return dict(topic='Diện tích và đại lượng theo diện tích', goal='Tính đủ các ý của đề với đúng đơn vị.', steps=steps, finalAnswerStep=final)

    one = re.fullmatch(r'nguoi ta muon xay dung mot khu chung cu tren manh dat co dien tich (' + _NUMBER +
        r') ha\. trong do (\d{1,3}/[1-9]\d{0,2}) dien tich dat duoc dung de xay cac toa nha\. '
        r'dien tich con lai lam ho dieu hoa va khu vui choi\. tinh dien tich lam ho dieu hoa va khu vui choi theo don vi m²\.', text)
    two = re.fullmatch(r'bac ([a-z]{1,20}) co (' + _NUMBER + r') ha dat\. bac da dung '
        r'(\d{1,3}/[1-9]\d{0,2}) manh dat de trong ca phe, (\d{1,3}/[1-9]\d{0,2}) dien tich dat de trong dieu\. '
        r'phan dat con lai de xay nha\. hoi bac \1 dung bao nhieu m² dat de xay nha\?', text)
    if not one and not two:
        return None
    if options:
        return None
    amount, shares = (one[1], [one[2]]) if one else (two[2], [two[3], two[4]])
    if Fraction(amount.replace(',', '.')) <= 0 or any(not 0 < Fraction(share) < 1 for share in shares) or sum(map(Fraction, shares)) >= 1:
        return None
    destination = 'làm hồ điều hòa và khu vui chơi' if one else 'xây nhà'
    steps = []
    for title, why, how, expression, unit, sentence in [
        ('Tìm phần diện tích còn lại', 'Coi toàn bộ mảnh đất là một. Phần còn lại ghép với các phần đã dùng vừa đủ toàn bộ.',
         'Viết một thành phân số cùng mẫu thích hợp rồi trừ các phần đã dùng. Phân số kết quả chưa phải diện tích.',
         '1-'+'-'.join(shares), 'phần', 'Phần diện tích còn lại là:'),
        ('Đổi tổng diện tích sang mét vuông', 'Đề cho diện tích bằng héc-ta nhưng yêu cầu kết quả bằng mét vuông, nên cần đổi về cùng đơn vị.',
         'Một héc-ta bằng mười nghìn mét vuông. Nhân tổng diện tích với hệ số này; lượng đất không thay đổi.',
         amount.replace(',', '.')+'*10000', 'm²', 'Tổng diện tích theo mét vuông là:'),
        ('Tính diện tích '+destination, 'Phân số đã tìm chỉ phần còn lại của toàn bộ đất. Nhân diện tích toàn bộ với phân số này để lấy đúng phần cần hỏi.',
         'Lấy tổng diện tích đã đổi nhân phân số còn lại. Giữ chính xác phân số khi tính và ghi đơn vị mét vuông.',
         '{s1}*{s0}', 'm²', 'Diện tích '+destination+' là:'),
    ]:
        step = _plan(title, why, how, expression=expression, unit=unit)['steps'][0]
        step['solutionSentence'] = sentence
        steps.append(step)
    return dict(topic='Diện tích phần đất còn lại', goal='Tìm đúng phần đất còn lại và biểu diễn bằng mét vuông.', steps=steps, finalAnswerStep=2)
