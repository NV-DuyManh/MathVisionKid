"""Exact, source-scoped conventions. Never learn new constants from model output.

SI definitions: https://www.nist.gov/pml/special-publication-330/sp-330-section-4
Metric prefixes: https://www.bipm.org/en/publications/si-brochure
Vietnamese school mass names: tạ = 100 kg, yến = 10 kg.
"""
import ast
from fractions import Fraction
from math import prod
import re
import unicodedata
from app.tutoring.service import _fold

VERSION='primary-conventions-v1'
_LENGTH={'km':3,'hm':2,'dam':1,'m':0,'dm':-1,'cm':-2,'mm':-3}
_UNITS={}
for suffix,power,dimension in [('',1,'length'),('²',2,'area'),('³',3,'volume')]:
    _UNITS.update({unit+suffix:(dimension,Fraction(10)**(exponent*power)) for unit,exponent in _LENGTH.items()})
_UNITS.update({unit:('mass',Fraction(10)**exponent) for unit,exponent in
               {'tấn':6,'tạ':5,'yến':4,'kg':3,'hg':2,'dag':1,'g':0,'mg':-3}.items()})
_UNITS.update({'ha':('area',Fraction(10000)),
               **{unit:('volume',Fraction(10)**exponent) for unit,exponent in {'l':-3,'dl':-4,'cl':-5,'ml':-6}.items()},
               **{unit:('time',Fraction(seconds)) for unit,seconds in {'tuần':604800,'ngày':86400,'giờ':3600,'phút':60,'giây':1}.items()}})
_CANONICAL={_fold(unit):unit for unit in _UNITS}
_CANONICAL.update({'t':'tấn','h':'giờ','min':'phút','s':'giây'})
_TOKENS=re.compile(r'(?<![a-z])('+ '|'.join(re.escape(unit) for unit in sorted(_CANONICAL,key=len,reverse=True)) +r')(?![a-z0-9²³])')
_CONTEXT=re.compile(r'(?:\d+(?:[.,]\d+)?\s*|(?:sang|ra|thanh|theo|bang|so|bao nhieu|don vi|doi)\s+|=\s*(?:\.{2,}|…|\?)\s*)$')
_JOIN=r'[\s\-‐‑‒–—−]*'
_ALIASES=[
    (r'(?:ki'+_JOIN+r'lo|kilo)'+_JOIN+r'met','km'),
    (r'hec'+_JOIN+r'to'+_JOIN+r'met','hm'),
    (r'de'+_JOIN+r'ca'+_JOIN+r'met','dam'),
    (r'de'+_JOIN+r'xi'+_JOIN+r'met','dm'),
    (r'(?:xang|xen)'+_JOIN+r'ti'+_JOIN+r'met','cm'),
    (r'mi'+_JOIN+r'li'+_JOIN+r'met','mm'),
    (r'ki'+_JOIN+r'lo'+_JOIN+r'gam','kg'),
    (r'hec'+_JOIN+r'to'+_JOIN+r'gam','hg'),
    (r'de'+_JOIN+r'ca'+_JOIN+r'gam','dag'),
    (r'mi'+_JOIN+r'li'+_JOIN+r'gam','mg'),
    (r'mi'+_JOIN+r'li'+_JOIN+r'lit','ml'),
    (r'de'+_JOIN+r'xi'+_JOIN+r'lit','dl'),
    (r'(?:xang|xen)'+_JOIN+r'ti'+_JOIN+r'lit','cl'),
    (r'hec'+_JOIN+r'ta','ha'),(r'met','m'),(r'gam','g'),(r'lit','l'),
]


def normalized_units(problem):
    text=_fold(''.join(str(unicodedata.decimal(char)) if char.isdecimal() else char for char in problem))
    for pattern,symbol in _ALIASES:
        if symbol in _LENGTH:
            text=re.sub(r'(?<![a-z])'+pattern+_JOIN+r'(vuong|khoi)(?![a-z])',
                        lambda match,symbol=symbol:symbol+('²' if match[1]=='vuong' else '³'),text)
        text=re.sub(r'(?<![a-z])'+pattern+r'(?![a-z])',symbol,text)
    lengths='|'.join(sorted(_LENGTH,key=len,reverse=True))
    text=re.sub(r'(?<![a-z])('+lengths+r')\s+([²³])',r'\1\2',text)
    text=re.sub(r'(?<![a-z])('+lengths+r')'+_JOIN+r'(vuong|khoi)(?![a-z])',
                lambda match:match[1]+('²' if match[2]=='vuong' else '³'),text)
    text=re.sub(r'(?<![a-z])('+lengths+r')(?:\^\{([23])\}|\^?([23]))(?![a-z0-9])',
                lambda match:match[1]+{'2':'²','3':'³'}[match[2] or match[3]],text)
    return text


def unit_conversions(problem):
    text=normalized_units(problem)
    units=set()
    for match in _TOKENS.finditer(text):
        unit=_CANONICAL[match[1]]
        # A number or explicit requested unit grounds ambiguous names such as
        # Tân/Tạ/Hà. Bare metric length symbols retain the established contract.
        if unit in _LENGTH or (unit[-1:] in '²³' and unit[:-1] in _LENGTH) or _CONTEXT.search(text[max(0,match.start()-48):match.start()]):
            units.add(unit)
    plain=units.intersection(_LENGTH)
    if re.search(r'dien tich|hinh vuong|hinh chu nhat',text):units.update(unit+'²' for unit in plain)
    if re.search(r'the tich|hinh lap phuong|hinh hop chu nhat',text):units.update(unit+'³' for unit in plain)
    ordered=sorted(units,key=lambda unit:(_UNITS[unit][0],-_UNITS[unit][1],unit))
    conversions=[]
    for index,large in enumerate(ordered):
        dimension,scale=_UNITS[large]
        for small in ordered[index+1:]:
            other,small_scale=_UNITS[small]
            if dimension!=other:continue
            ratio=scale/small_scale
            if ratio.denominator==1 and ratio<=10**12:
                conversions.append(dict(fromUnit=large,toUnit=small,factor=str(ratio)))
    return conversions


def contextual_facts(problem):
    text=_fold(problem)
    facts=[]
    if re.search(r'(?:viet\s+them|them).*(?:chu\s+)?so|hang\s+(?:don vi|chuc|tram)',text):
        facts.append(dict(id='decimal-place-value',constants=['9','10'],
                          statement='Dịch các chữ số sang trái một hàng nhân giá trị với 10; so với giá trị ban đầu thì có 10 − 1 phần.'))
    if '%' in text or 'phan tram' in text:
        facts.append(dict(id='percent',constants=['100'],statement='Phần trăm là số phần trong 100 phần bằng nhau của toàn bộ.'))
    for pattern,identity,constants,statement in [
        (r'hinh chu nhat','rectangle',['2'],'Hình chữ nhật: diện tích bằng dài nhân rộng; chu vi bằng tổng dài và rộng nhân 2.'),
        (r'hinh vuong','square',['4'],'Hình vuông: diện tích bằng cạnh nhân cạnh; chu vi bằng cạnh nhân 4.'),
        (r'tam giac','triangle',['2'],'Tam giác: diện tích bằng đáy nhân chiều cao tương ứng rồi chia 2; hai độ dài phải cùng đơn vị.'),
        (r'hinh thang','trapezoid',['2'],'Hình thang: diện tích bằng tổng hai đáy nhân chiều cao rồi chia 2, sau khi thống nhất đơn vị độ dài.'),
        (r'hinh lap phuong','cube',['4','6'],'Hình lập phương có 6 mặt vuông bằng nhau, 4 mặt bên; thể tích bằng cạnh nhân cạnh nhân cạnh.'),
        (r'hinh hop chu nhat','cuboid',['2'],'Hình hộp chữ nhật: thể tích bằng dài nhân rộng nhân cao; diện tích toàn phần bằng tổng diện tích ba cặp mặt.'),
    ]:
        if re.search(pattern,text):facts.append(dict(id=identity,constants=constants,statement=statement))
    return facts


def formula_constants(problem):
    constants={'1','2'}
    constants.update(row['factor'] for row in unit_conversions(problem))
    constants.update(value for fact in contextual_facts(problem) for value in fact['constants'])
    return frozenset(constants)


def normalize_conversion_factors(expression,givens,conversions):
    """Fold only unearned factors whose exact product is a grounded unit ratio.

    Accept e.g. 3*100*100 for m²→cm², retaining 3 as a source quantity.
    Never fold a whole computed answer or add/subtract invented operands.
    """
    ratios={row['factor'] for row in conversions}
    if not ratios or re.search(r'\bprior_ref_\d+\b',expression):return expression
    references={}
    def reference(match):
        name=f'prior_ref_{len(references)}';references[name]=match[0];return name
    source=re.sub(r'\{s\d+(?:_(?:numerator|denominator))?\}',reference,expression).translate(str.maketrans({'×':'*','÷':'/','−':'-'}))
    try:tree=ast.parse(source,mode='eval')
    except (SyntaxError,ValueError):return expression
    if len(list(ast.walk(tree)))>50:return expression
    changed=False
    def visit(node):
        nonlocal changed
        if not isinstance(node,ast.BinOp):return node
        if not isinstance(node.op,(ast.Mult,ast.Div)):
            node.left=visit(node.left);node.right=visit(node.right);return node
        factors=[]
        def collect(value,inverse=False):
            if isinstance(value,ast.BinOp) and isinstance(value.op,ast.Mult):collect(value.left,inverse);collect(value.right,inverse)
            elif isinstance(value,ast.BinOp) and isinstance(value.op,ast.Div):collect(value.left,inverse);collect(value.right,not inverse)
            else:factors.append((visit(value),inverse))
        collect(node)
        replacements={};removed=set()
        for inverse in (False,True):
            selected=[]
            for index,(value,side) in enumerate(factors):
                if side!=inverse or not isinstance(value,ast.Constant) or type(value.value) not in (int,float):continue
                literal=ast.get_source_segment(source,value)
                if literal is None or literal in givens:continue
                number=Fraction(literal)
                if number>0:selected.append((index,number))
            if len(selected)<2:continue
            product=prod(number for _,number in selected)
            if product.denominator==1 and str(product) in ratios:
                replacements[selected[0][0]]=ast.Constant(value=int(product))
                removed.update(index for index,_ in selected[1:]);changed=True
        if not replacements:return node
        result=None
        for index,(value,inverse) in enumerate(factors):
            if index in removed:continue
            value=replacements.get(index,value)
            if result is None:result=ast.BinOp(left=ast.Constant(value=1),op=ast.Div(),right=value) if inverse else value
            else:result=ast.BinOp(left=result,op=ast.Div() if inverse else ast.Mult(),right=value)
        return result
    tree.body=visit(tree.body)
    if not changed:return expression
    result=ast.unparse(ast.fix_missing_locations(tree))
    for name,original in references.items():result=re.sub(r'\b'+name+r'\b',lambda _:original,result)
    return result
