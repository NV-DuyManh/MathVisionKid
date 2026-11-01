"""Split one complete A-D question without selecting or inferring an answer."""
import re


def split_choices(source):
    if not isinstance(source,str) or len(source)>4000:
        return None
    labels=list(re.finditer(r'(?<!\w)([A-D])[.)]\s*',source))
    if [match[1] for match in labels]!=list('ABCD'):
        return None
    stem=source[:labels[0].start()].strip()
    choices=[source[match.end():labels[index+1].start() if index<3 else len(source)].strip()
             for index,match in enumerate(labels)]
    if (not stem or stem[-1] not in ':?' or any(not part or len(part)>100 for part in choices)
            or any(re.search(r'\b(?:Bài|Câu)\s*\d',part,re.I) for part in choices)):
        return None
    return stem,choices
