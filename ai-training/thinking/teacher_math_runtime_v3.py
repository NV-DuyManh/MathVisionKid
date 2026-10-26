"""Research tutor for EXACT published authored question patterns.

The template solver reads parameters from the submitted question, independently
of the neural response. This is not arbitrary Vietnamese NLU or OCR. Numeric
model scores remain separate from this checked deterministic teaching renderer.
"""
from fractions import Fraction
from functools import lru_cache
import json
import re
import unicodedata

import teacher_math_data_v3 as data
from teacher_math_verifier_v3 import check_arithmetic
from train_teacher_math_v3 import score

NUMBER=r'\d+(?:[.,]\d+)?(?:/\d+)?'
OBSERVED=r' Học sinh ghi kết quả (\d+)\. Hãy giúp em kiểm tra; đây là bài làm quan sát được, chưa có các dấu nhớ hoặc mượn\.'

@lru_cache(maxsize=512)
def _pattern(template):
    parts=[];keys=[];cursor=0
    for found in re.finditer(r'\{([abc])\}',template):
        parts.append(re.escape(template[cursor:found.start()]));parts.append('('+NUMBER+')')
        keys.append(found[1]);cursor=found.end()
    parts.append(re.escape(template[cursor:]))
    return re.compile(''.join(parts)),keys

def _domain(topic,values,grade,variant):
    a,b,c=(values.get(k,Fraction(0)) for k in 'abc')
    if any(v<0 or abs(v)>10**8 for v in values.values()): return False
    counts={'add_join','sub_remaining','missing_addend','compare_difference','tens_place_value',
            'equal_groups','share_exact','missing_factor','multistep_add_sub','groups_after_sale',
            'money_change','elapsed_minutes','division_remainder','order_operations','hours_minutes',
            'table_total','sum_difference_large','sum_difference_small','multiples_missing',
            'probability_count','empirical_frequency','proportional_inverse','vertical_add','vertical_subtract'}
    if topic in counts and any(v.denominator!=1 for v in values.values()):return False
    if grade==1 and topic in ('add_join','sub_remaining','missing_addend','compare_difference'):
        if max(a,b)>100:return False
        if topic=='add_join' and (a+b>100 or a%10+b%10>=10):return False
        if topic in ('sub_remaining','compare_difference') and a%10<b%10:return False
        if topic=='missing_addend' and (b-a<0 or b%10<a%10):return False
    if grade==2 and topic=='equal_groups' and not (1<=a<=10 and b in (2,5)):return False
    if grade==2 and topic in ('share_exact','missing_factor') and not (b in (2,5) and 1<=a/b<=10):return False
    if topic in ('sum_difference_large','sum_difference_small') and (a<b or (a+b)%2):return False
    if topic=='fraction_of_quantity' and (a.denominator!=1 or (a*b).denominator!=1):return False
    if topic=='ratio_share' and (any(v.denominator!=1 or v<=0 for v in values.values()) or (a*b/(b+c)).denominator!=1):return False
    if topic=='percent_part' and variant==2 and (a.denominator!=1 or (a*b/100).denominator!=1):return False
    if topic=='percent_ratio' and variant in (0,3,4) and (a.denominator!=1 or b.denominator!=1 or a>b):return False
    if topic=='proportional_direct' and any(v.denominator!=1 for v in (a,c)):return False
    if topic=='order_operations' and not (1<=b<=9 and 1<=c<=9):return False
    if topic=='hours_minutes' and a>12:return False
    if topic in ('sub_remaining','compare_difference','vertical_subtract','decimal_subtract','fraction_subtract') and a<b:return False
    if topic in ('missing_addend','money_change','elapsed_minutes') and b<a:return False
    if topic in ('multistep_add_sub',) and c>a+b:return False
    if topic in ('groups_after_sale',) and c>a*b:return False
    if topic in ('share_exact','missing_factor','decimal_divide','speed_from_distance_time','time_from_distance_speed','fraction_divide','percent_whole','percent_ratio','empirical_frequency') and b<=0:return False
    if topic in ('share_exact','missing_factor') and (a.denominator!=1 or b.denominator!=1 or (a/b).denominator!=1):return False
    if topic=='division_remainder' and (a.denominator!=1 or b.denominator!=1 or b<=0):return False
    if topic=='tens_place_value' and (a.denominator!=1 or not 10<=a<=99):return False
    if topic=='elapsed_minutes' and not 0<=a<b<=59:return False
    if topic=='hours_minutes' and not (a.denominator==b.denominator==1 and 0<=b<60):return False
    if topic=='multiples_missing' and b!=2*a:return False
    if topic in ('ratio_share','proportional_inverse') and c<=0:return False
    if topic=='ratio_share' and b<=0:return False
    if topic=='proportional_direct' and a<=0:return False
    if topic=='probability_count' and a+b<=0:return False
    if topic=='empirical_frequency' and a>b:return False
    if topic in ('vertical_add','vertical_subtract') and (a.denominator!=1 or b.denominator!=1 or max(a,b)>999999):return False
    if any(key in topic for key in ('perimeter','area','volume','surface')) and any(v<=0 for v in values.values()):return False
    return True

def inspect_known_problem(problem,grade=None,mode='hint'):
    if not isinstance(problem,str) or len(problem)>2500 or mode not in ('hint','worked_solution'):return None
    problem=unicodedata.normalize('NFC',problem).strip()
    observed=None;base=problem
    tail=re.search(OBSERVED+'$',problem)
    if tail:
        observed=tail[1];base=problem[:tail.start()]
        if len(observed)>7:return None
    candidates=[]
    for topic in data.TOPICS:
        for variant,template in enumerate(topic.templates):
            pattern,keys=_pattern(template);match=pattern.fullmatch(base)
            if not match:continue
            values={};valid=True
            try:
                for key,value in zip(keys,match.groups()):
                    value=Fraction(value.replace(',','.'))
                    if key in values and values[key]!=value:valid=False;break
                    values[key]=value
                if not valid or not _domain(topic.name,values,topic.grade,variant):continue
                row=data.make_row(topic,'runtime',variant,values,mode,observed)
                if grade is not None and row['grade']!=grade:continue
                candidates.append(row)
            except (ValueError,ZeroDivisionError,KeyError,TypeError,IndexError):continue
    if not candidates and observed is None:
        for kind,templates in data.GUARDS.items():
            for variant,template in enumerate(templates):
                pattern,keys=_pattern(template);match=pattern.fullmatch(base)
                if match:
                    try:return data.guard_row(kind,'runtime',variant,int(match[1]),grade or 3,mode)
                    except (ValueError,TypeError):pass
    if len(candidates)!=1:return None
    return candidates[0]

def tutor(problem,prediction,*,grade=None,mode='hint',input_confirmed=False):
    metadata={'production_approved':False,'human_verified':False,'pedagogy_teacher_reviewed':False,
              'curriculum_grade_verified':False,
              'ocr_performed':False,'semantic_scope':'exact published authored patterns only',
              'teacher_final_authority':True,'model_answer_replaced_by_calculator':False}
    if not input_confirmed:
        return {'status':'NEEDS_CONFIRMATION','hint':'Em hãy xác nhận đề và các chữ số đã được đọc đúng nhé?',
                'retry_allowed':True,'reveal_answer':False,'metadata':metadata}
    row=inspect_known_problem(problem,grade,mode)
    if row is None:
        return {'status':'OUTSIDE_VERIFIED_CONTRACT','hint':'Em có thể viết rõ đề, các dữ kiện và điều cần tìm không?',
                'retry_allowed':True,'reveal_answer':False,'metadata':metadata}
    if mode=='hint' or row['target']['status']!='solve':
        # A known-purpose hint is used because a structurally safe model hint can
        # still contain the wrong pedagogical suggestion.
        metadata['hint_source']='authored_supported_pattern_renderer'
        return {'status':row['target']['status'],'hint':row['target']['hint'],'retry_allowed':True,
                'reveal_answer':False,'metadata':metadata}
    scored=score(row,prediction)
    if not scored['solution_verified']:
        return {'status':'MODEL_RESPONSE_REJECTED','hint':'Em hãy kiểm tra lại cách chọn phép tính và đơn vị nhé?',
                'retry_allowed':True,'reveal_answer':False,'model_scores':scored,'metadata':metadata}
    arithmetic=check_arithmetic(prediction)
    if not arithmetic['arithmetic_consistent']:
        return {'status':'ARITHMETIC_REJECTED','hint':'Em hãy kiểm tra lại các phép tính nhé?',
                'retry_allowed':True,'reveal_answer':False,'arithmetic_gate':arithmetic,'metadata':metadata}
    # The model has produced the correct answer/path. Explanatory prose is
    # rendered from the reviewed known-purpose recipe, never certified merely
    # because freely generated text accompanies a correct numeric result.
    metadata.update(explanation_source='authored_supported_pattern_renderer',numeric_model_output_verified=True,
                    input_interpretation='exact_pattern_parameter_binding',topic=row['topic'])
    return {'status':'SUPPORTED_RESEARCH_SOLUTION','solution':row['target'],'retry_allowed':True,
            'reveal_answer':True,'model_scores':scored,'metadata':metadata}
