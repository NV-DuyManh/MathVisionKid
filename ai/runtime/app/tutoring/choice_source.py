"""Split one complete A-D question without selecting or inferring an answer."""
import re


def numeric_notation(source):
    """Equivalent visible glyphs only; never fill missing fraction tiers/operands."""
    source = source.replace('⁄', '/').replace('∕', '/')
    source = re.sub(r'(?<![\d)])\\(?:d?frac)\s*\{\s*(\d+)\s*\}\s*\{\s*(\d+)\s*\}', r'\1/\2', source)
    source = re.sub(r'(?<![\d)])\(\s*(\d+)\s*\)\s*/\s*\(\s*(\d+)\s*\)', r'\1/\2', source)
    # Grouped thousands are one number; a mixed number's whole part remains separate.
    return re.sub(r'(?<![\d.,])\d{1,3}(?:[ \u00a0\u202f\u2009]+\d{3})+(?![\d.,]|\s*/)',
                  lambda match: re.sub(r'\s', '', match[0]), source)


def split_choices(source, *, allow_statement=False):
    if not isinstance(source,str) or len(source)>4000:
        return None
    # A lowercase worksheet subpart label precedes the full question; it is not
    # the first answer choice. Retain the original source outside this parser.
    source = re.sub(r'^\s*[a-h][.)]\s+(?=\S)', '', source)
    labels=list(re.finditer(r'(?<!\w)([A-D])[.)]\s*',source,re.I))
    if [match[1].upper() for match in labels]!=list('ABCD'):
        return None
    stem=source[:labels[0].start()].strip()
    choices=[source[match.end():labels[index+1].start() if index<3 else len(source)].strip()
             for index,match in enumerate(labels)]
    # OCR may put an explicit diagram description after D. Keep that complete
    # source context in the stem instead of treating it as part of option D.
    diagram = re.search(r'\n(?=\s*Hình vẽ\b)', choices[-1], re.I)
    if diagram and choices[-1][:diagram.start()].strip():
        stem += '\n' + choices[-1][diagram.start():].strip()
        choices[-1] = choices[-1][:diagram.start()].strip()
    if (not stem or (not allow_statement and stem[-1] not in ':?') or any(not part or len(part)>100 for part in choices)
            or any(re.search(r'\b(?:Bài|Câu)\s*\d',part,re.I) for part in choices)):
        return None
    return stem,choices
