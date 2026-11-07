"""Exact proof for a bounded two-crop, mixed-tonne/kg fraction question.

Consume the full relation and check all answer options. Unsupported or
inconsistent sources keep the independently reviewed planner path.
"""
import re
import unicodedata
from fractions import Fraction
from app.tutoring.choice_source import numeric_notation, split_choices
from app.tutoring.service import _fold

_KG=r'(?:kg|ki[\s\-‐‑‒–—−]+lo[\s\-‐‑‒–—−]+gam)'


def verified_plan(problem):
    normalized=numeric_notation(problem)
    multiple=split_choices(normalized)
    if multiple is None:
        if re.search(r'(?<!\w)[A-D][.)]\s*',normalized,re.I):return None
        stem,options=normalized,[]
    else:
        stem,options=multiple
    original=re.sub(r'\s+',' ',unicodedata.normalize('NFC',stem)).strip()
    text=_fold(original)
    # Preserve literal crop names in teaching without an unsafe offset mapping.
    if len(text)!=len(original):return None
    heading=re.match(r'^(?:cau|bai)\s+\d+\s*[.):]?\s*(?:\(\s*\d+(?:[.,]\d+)?\s*diem\s*\)\s*)?',text)
    if heading:original=original[heading.end():];text=text[heading.end():]
    person=r'(?P<person>(?:bac|co|chu|ban|anh|chi) [a-z]{1,20}(?: [a-z]{1,20}){0,2})'
    crop=r'[a-z ]{2,50}?'
    grammar=(person+r' thu hoach duoc (?P<tonnes>\d{1,4}) tan (?P<kg>\d{1,3}) '+_KG
             +r' (?P<first>'+crop+r') va (?P<second>'+crop+r')\. '
             +r'biet (?:rang )?(?:so luong|khoi luong) (?P<share>'+crop+r') chiem '
             +r'(?:(?P<numerator>\d{1,3})\s*/\s*(?P<denominator>\d{1,3})'
             +r'|\((?P<bracket_n>\d{1,3})\)\s*/\s*\((?P<bracket_d>\d{1,3})\)) '
             +r'(?:tong so|tong khoi luong) (?P=first) va (?P=second) thu hoach duoc\. '
             +r'vay,? (?P=person) thu hoach duoc so '+_KG+r' (?P<target>'+crop+r') la\s*:')
    match=re.fullmatch(grammar,text)
    if not match:return None
    crops=[match[name].strip() for name in ('first','second')]
    if (crops[0]==crops[1] or match['share'].strip() not in crops or match['target'].strip()!=match['share'].strip()
            or any(re.search(r'\b(?:khong|chua|sau|truoc|them|bot|con|hon|kem|va|hoac|neu|it|nhieu|cua|mat)\b',name) for name in crops)):
        return None
    tonnes,kg=int(match['tonnes']),int(match['kg'])
    numerator,denominator=int(match['numerator'] or match['bracket_n']),int(match['denominator'] or match['bracket_d'])
    if not 0<tonnes or not 0<=kg<1000 or not 0<numerator<denominator:return None
    total=tonnes*1000+kg
    answer=Fraction(total*numerator,denominator)
    if total>1_000_000 or answer.denominator!=1:return None
    weights=[]
    for option in options:
        value=re.fullmatch(r'(\d{1,9}(?:[ \u00a0\u202f\u2009]+\d{3})*)\s*'+_KG,_fold(option))
        if not value:return None
        weights.append(int(re.sub(r'\s','',value[1])))
    if options and (len(set(weights))!=4 or weights.count(answer)!=1):return None
    # Exact conservation, proper share, original question target and one matching
    # option are all proved before this route can avoid a provider call.
    assert answer+(total-answer)==total and 0<answer<total
    target=original[match.start('target'):match.end('target')].strip()
    why_conversion=(f'Đề cho tổng khối lượng là {tonnes} tấn {kg} kg, còn câu hỏi dùng ki lô gam. '
                    'Cần đổi phần tấn ra ki lô gam rồi cộng với phần ki lô gam đã cho để có cùng một đơn vị.')
    how_conversion=('Một tấn bằng 1000 kg. Em nhân số tấn với 1000 rồi cộng số kg còn lại. '
                    'Đây là tổng của hai loại thu hoạch, chưa phải khối lượng riêng của loại đang được hỏi.')
    why_fraction=(f'{target[:1].upper()+target[1:]} chiếm {numerator}/{denominator} '
                  'của tổng đó, nên cần lấy tổng khối lượng nhân với phân số đã cho; đơn vị kết quả vẫn là kg.')
    how_fraction=(f'Em chia tổng khối lượng cho {denominator} để tìm một phần bằng nhau, rồi nhân với {numerator} '
                  f'để lấy đủ số phần của {target}. Tính chính xác rồi đối chiếu kết quả với các phương án của đề.')
    descriptions=[
        ('Đổi tổng khối lượng về ki lô gam','Tổng khối lượng thu hoạch là:',
         f'{tonnes}*1000+{kg}',False,why_conversion,how_conversion,'Tổng khối lượng bằng bao nhiêu ki lô gam?'),
        (f'Tìm khối lượng {target}',f'Khối lượng {target} là:',
         f'{{s0}}*{numerator}/{denominator}',True,why_fraction,how_fraction,f'Khối lượng {target} bằng bao nhiêu ki lô gam?'),
    ]
    return dict(topic='Tìm một phần khối lượng',goal=f'Đổi đơn vị rồi tìm khối lượng {target}.',finalAnswerStep=1,
                steps=[dict(title=title,solutionSentence=sentence,expression=expression,unit='kg',fractionNotation=fraction,
                            explanation=why,question=question,initialGuidance=[why,how],guidance=[why,how],hints=[why,how])
                       for title,sentence,expression,fraction,why,how,question in descriptions])
