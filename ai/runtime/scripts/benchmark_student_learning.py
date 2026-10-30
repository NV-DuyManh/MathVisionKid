"""Fixed arithmetic oracle and optional OCR/model predictions. Never trains.

Usage: python scripts/benchmark_student_learning.py --output result.json
       ... --predictions predictions.json   # id -> {text?, finalAnswer?}
Missing predictions are reported as missing, never as successes.
"""
import argparse
from fractions import Fraction
import json
from pathlib import Path
import re
import sys
import time
import unicodedata

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.tutoring.lesson import calculate_exact


def distance(a,b):
    previous=list(range(len(b)+1))
    for i,left in enumerate(a,1):
        row=[i]
        for j,right in enumerate(b,1):row.append(min(row[-1]+1,previous[j]+1,previous[j-1]+(left!=right)))
        previous=row
    return previous[-1]


def normalized(text):
    return re.sub(r'\s+',' ',unicodedata.normalize('NFC',text)).strip()


def evaluate(corpus,predictions=None):
    results=[]
    for case in corpus['cases']:
        if not case['steps'] or len(case['steps'])!=len(case['expected']):raise ValueError('Incomplete gold case')
        began=time.perf_counter();answers=[]
        for expression,expected in zip(case['steps'],case['expected']):
            for i,answer in reversed(list(enumerate(answers))):expression=expression.replace(f'@{i}',f'({answer})')
            answer=calculate_exact(expression)
            if answer!=Fraction(expected):raise ValueError('Gold mismatch: '+case['id'])
            answers.append(str(answer))
        row=dict(id=case['id'],oraclePassed=True,oracleMs=round((time.perf_counter()-began)*1000,3),predictionPresent=False,answerCorrect=None,cer=None)
        prediction=(predictions or {}).get(case['id'])
        if isinstance(prediction,dict):
            row['predictionPresent']=True
            if isinstance(prediction.get('finalAnswer'),str):
                try:row['answerCorrect']=Fraction(prediction['finalAnswer'].replace(',','.'))==Fraction(answers[-1])
                except (ValueError,ArithmeticError):row['answerCorrect']=False
            if isinstance(prediction.get('text'),str) and len(prediction['text'])<=4000:
                gold=normalized(case['problem']);text=normalized(prediction['text'])
                row['cer']=distance(gold,text)/max(1,len(gold))
        results.append(row)
    assessed=[row for row in results if row['answerCorrect'] is not None]
    ocr=[row for row in results if row['cer'] is not None]
    return dict(corpusVersion=corpus['version'],evidence='Curated regression oracle; model/OCR scores require supplied predictions; no training and no independent-holdout claim.',
                cases=len(results),oraclePassed=sum(row['oraclePassed'] for row in results),modelAnswersAssessed=len(assessed),
                modelAnswerAccuracy=sum(row['answerCorrect'] for row in assessed)/len(assessed) if assessed else None,
                ocrTranscriptsAssessed=len(ocr),meanCer=sum(row['cer'] for row in ocr)/len(ocr) if ocr else None,results=results)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--predictions',type=Path);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    corpus=json.loads((Path(__file__).resolve().parents[1]/'tests/fixtures/student_learning_regression.json').read_text(encoding='utf-8'))
    predictions=json.loads(args.predictions.read_text(encoding='utf-8')) if args.predictions else None
    result=evaluate(corpus,predictions);args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({key:value for key,value in result.items() if key!='results'},ensure_ascii=False))
