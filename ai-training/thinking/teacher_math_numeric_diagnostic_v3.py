"""Direct generated answer diagnostic independent of strict teaching schema.

This never repairs a mathematical answer or inserts an oracle result. It only
reads the answer/unit fields of a bounded JSON output. Output-format compliance
and reference-path scores remain in the unchanged original trainer reports.
"""
from fractions import Fraction
import json
import re
import unicodedata

NUMBER=r'[+-]?\d+(?:[.,]\d+)?(?:/\d+)?'
ALIASES={'viên bi':'viên','viên kẹo':'viên','quyển vở':'quyển','quyển sách':'quyển',
         'chiếc bút':'chiếc','cái bánh':'cái','quả cam':'quả','quả táo':'quả',
         'cm2':'cm²','m2':'m²','cm3':'cm³','m3':'m³','ki-lô-gam':'kg','kilôgam':'kg',
         'xăng-ti-mét':'cm','mét':'m','ki-lô-mét':'km','gam':'g','km/giờ':'km/h',
         'ki-lô-mét/giờ':'km/h','lít nước':'lít','học sinh':'học sinh'}

def unit(value):
    if value is None:return ''
    if not isinstance(value,str):raise ValueError('Invalid unit')
    value=re.sub(r'\s+',' ',unicodedata.normalize('NFC',value).strip().casefold())
    return ALIASES.get(value,value)

def unique(pairs):
    value={}
    for key,item in pairs:
        if key in value:raise ValueError('Duplicate key')
        value[key]=item
    return value

def extract(text):
    if not isinstance(text,str) or len(text)>24000:raise ValueError('Text limit')
    if '</think>' in text:text=text.rsplit('</think>',1)[-1]
    if '<think>' in text:raise ValueError('Unfinished thinking')
    text=text.strip()
    if text.startswith('```'):
        text=re.sub(r'^```(?:json)?\s*','',text);text=re.sub(r'\s*```$','',text)
    obj=json.loads(text,object_pairs_hook=unique)
    if not isinstance(obj,dict):raise ValueError('Object required')
    answer=obj.get('answer');declared=obj.get('unit')
    if isinstance(answer,bool) or not isinstance(answer,(str,int,float)):raise ValueError('No numeric answer')
    token=str(answer).strip()
    found=re.fullmatch('('+NUMBER+r')(?:\s+(.+))?',token)
    if not found:raise ValueError('Unparseable numeric answer')
    number=Fraction(found[1].replace(',','.'))
    if abs(number)>10**15 or number.denominator>10**12:raise ValueError('Number limit')
    embedded=found[2]
    if embedded and declared and unit(embedded)!=unit(declared):raise ValueError('Conflicting answer units')
    return number,unit(declared or embedded)

def diagnostic(references,predictions):
    by_id={row['sample_id']:row for row in references}
    rows=[]
    for pred in predictions:
        row=by_id[pred['sample_id']]
        if row['mode']!='worked_solution' or row['target']['status']!='solve':continue
        item={'sample_id':row['sample_id'],'grade':row['grade'],'topic':row['topic'],
              'answer_extracted':False,'numeric_correct':False,'answer_unit_correct':False,
              'strict_schema_valid':pred['scores']['schema_valid']}
        try:
            if pred['scores']['truncated']:raise ValueError('Truncated output')
            value,label=extract(pred['prediction']);expected=Fraction(row['target']['answer'].replace(',','.'))
            item.update(answer_extracted=True,numeric_correct=value==expected,
                        answer_unit_correct=value==expected and label==unit(row['target']['unit']),
                        generated_answer=str(value),generated_unit=label)
        except (ValueError,TypeError,ZeroDivisionError,json.JSONDecodeError):pass
        rows.append(item)
    summary={'solution_samples':len(rows),'answer_extracted':sum(r['answer_extracted'] for r in rows),
        'numeric_correct':sum(r['numeric_correct'] for r in rows),'answer_unit_correct':sum(r['answer_unit_correct'] for r in rows),
        'strict_schema_valid':sum(r['strict_schema_valid'] for r in rows),
        'protocol':'bounded JSON answer/unit extraction; explicit noun/unit aliases; generated number never replaced with oracle',
        'teacher_pedagogy_verified':False,'protocol_is_posthoc':True}
    summary['per_grade']={str(g):{'samples':sum(r['grade']==g for r in rows),
        'numeric_correct':sum(r['numeric_correct'] for r in rows if r['grade']==g),
        'answer_unit_correct':sum(r['answer_unit_correct'] for r in rows if r['grade']==g)} for g in sorted({r['grade'] for r in rows})}
    return {'summary':summary,'records':rows}
