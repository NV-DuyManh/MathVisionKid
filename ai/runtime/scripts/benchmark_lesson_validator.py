"""Evaluate local knowledge grounding; never imply model/OCR accuracy or train.

Optional --log aggregates coded decisions without exporting pupil text.
"""
import argparse
from collections import Counter
from fractions import Fraction
import json
from pathlib import Path
import re
import statistics
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.tutoring import lesson, validation_audit


def evaluate(corpus):
    rows=[]
    for case in corpus['cases']:
        started=time.perf_counter()
        if lesson.calculate_exact(case['expression'])!=Fraction(case['answer']):raise ValueError('Invalid gold arithmetic: '+case['id'])
        request=lesson.LessonRequest(owner='validator-benchmark',problemText=case['source'],problemConfirmed=True)
        plan=lesson.Plan(topic='Đổi số đo',goal='Đổi theo đơn vị được hỏi.',finalAnswerStep=1,
            steps=[lesson.Step(title=title,expression=expression,unit=case['unit'],solutionSentence='Số đo cần ghi là:',
                explanation='Dùng quan hệ giữa các đơn vị được nêu trong đề.',question='Số đo bằng bao nhiêu?',
                guidance=['Đối chiếu đơn vị trong đề với đơn vị được hỏi rồi thực hiện phép đổi.'])
                for title,expression in [('Đổi số đo',case['expression']),('Ghi số đo','{s0}*1')]])
        accepted=True;reason=''
        try:lesson.validate_plan(plan,request,lesson.formula_constants(case['source']))
        except (ValueError,ArithmeticError,SyntaxError,TypeError) as error:accepted=False;reason=validation_audit.reason_code(error)
        rows.append(dict(id=case['id'],family=case['family'],expectedAccept=case['accept'],accepted=accepted,
                         passed=accepted==case['accept'],reason=reason,elapsedMs=(time.perf_counter()-started)*1000))
    positives=[row for row in rows if row['expectedAccept']];negatives=[row for row in rows if not row['expectedAccept']]
    return dict(version=corpus['version'],scope=corpus['scope'],cases=len(rows),passed=sum(row['passed'] for row in rows),
        validCases=len(positives),invalidCases=len(negatives),
        localFalseRejectRate=sum(not row['accepted'] for row in positives)/len(positives),
        localFalseAcceptRate=sum(row['accepted'] for row in negatives)/len(negatives),
        medianMs=statistics.median(row['elapsedMs'] for row in rows),maxMs=max(row['elapsedMs'] for row in rows),results=rows)


def audit_summary(path):
    pattern=re.compile(r'lesson_validation source=([0-9a-f]{16}) attempt=\d+ code=([A-Z_]+) provider=(groq|gemini|unknown)')
    counts=Counter();sources=set()
    for line in path.read_text(encoding='utf-8',errors='replace').splitlines():
        match=pattern.search(line)
        if match:counts[match[2]]+=1;sources.add(match[1])
    return dict(codedEvents=sum(counts.values()),uniqueSourceFingerprints=len(sources),codes=dict(counts),
                note='Recovered attempts are not automatically labelled as false rejections or training examples.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--log',type=Path)
    args=parser.parse_args()
    corpus=json.loads((Path(__file__).resolve().parents[1]/'tests/fixtures/validator_knowledge_cases.json').read_text(encoding='utf-8'))
    result=evaluate(corpus)
    if args.log:result['audit']=audit_summary(args.log)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({key:value for key,value in result.items() if key!='results'},ensure_ascii=False))
    raise SystemExit(0 if result['passed']==result['cases'] else 1)
