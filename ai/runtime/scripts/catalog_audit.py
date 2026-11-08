"""Read-only catalog inventory for CI; private DB audit is explicit and local only."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.tutoring.catalog_store import CatalogStore,normalized_source


def audit_corpus(path):
    corpus=json.loads(path.read_text(encoding='utf-8-sig'))
    if corpus.get('version')!=1 or not isinstance(corpus.get('cases'),list):raise ValueError('Invalid regression inventory')
    ids=set();sources=set()
    for row in corpus['cases']:
        if set(row)!={'id','problem','steps','expected'}:raise ValueError('Unexpected/private fields in public inventory')
        if not isinstance(row['id'],str) or not 1<=len(row['id'])<=80 or row['id'] in ids:raise ValueError('Invalid or duplicated case ID')
        if not isinstance(row['problem'],str) or not 3<=len(row['problem'])<=4000:raise ValueError('Invalid source')
        digest=hashlib.sha256(normalized_source(row['problem']).encode()).hexdigest()
        if digest in sources:raise ValueError('Duplicated exact source')
        if not isinstance(row['steps'],list) or not 1<=len(row['steps'])<=9 or len(row['steps'])!=len(row['expected']):raise ValueError('Incomplete oracle')
        if not all(isinstance(item,str) and 0<len(item)<=160 for item in row['steps']+row['expected']):raise ValueError('Invalid oracle fields')
        ids.add(row['id']);sources.add(digest)
    return dict(cases=len(ids),distinctSources=len(sources),duplicateSources=0,
                evidence='Structure/deduplication only; this is not mathematical or OCR accuracy.')


def audit_published(path):
    if path.stat().st_size > 1_000_000: raise ValueError('Public catalog is too large')
    data=json.loads(path.read_text(encoding='utf-8'))
    if set(data)!={'version','validationPolicy','entries'} or data['version']!=1 or not re.fullmatch(r'[a-f0-9]{64}',data['validationPolicy']):
        raise ValueError('Invalid public catalog')
    if not isinstance(data['entries'],list) or not 1<=len(data['entries'])<=500: raise ValueError('Invalid public entries')
    ids=set();sources=set()
    for row in data['entries']:
        if set(row)!={'id','problemText','plan','expectedAnswers'}: raise ValueError('Unexpected/private public fields')
        if not isinstance(row['id'],str) or not re.fullmatch(r'[a-z0-9-]{1,80}',row['id']) or row['id'] in ids: raise ValueError('Invalid public ID')
        source=row['problemText']
        if not isinstance(source,str) or not 3<=len(source)<=4000 or re.search(r'@|https?://|Bearer |accessToken|sessionId',source,re.I):
            raise ValueError('Public source needs review')
        key=normalized_source(source)
        if key in sources: raise ValueError('Duplicate public source')
        steps=row['plan']['steps'];expected=row['expectedAnswers']
        if not 1<=len(steps)<=6 or not isinstance(expected,list) or len(steps)!=len(expected): raise ValueError('Incomplete public plan')
        if any(step.get('kind')!='MATH' or step.get('workExcerpt') for step in steps): raise ValueError('Private work in public plan')
        ids.add(row['id']);sources.add(key)
    return dict(exercises=len(ids),version=1,evidence='Public structure/privacy checks; mathematical verification runs in AI CI.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus',type=Path)
    parser.add_argument('--database',type=Path)
    parser.add_argument('--prune',action='store_true')
    parser.add_argument('--summary',action='store_true')
    args=parser.parse_args()
    if bool(args.corpus)==bool(args.database):parser.error('Choose exactly one source')
    if args.prune and not args.database:parser.error('Pruning is private-database maintenance only')
    result=audit_corpus(args.corpus) if args.corpus else CatalogStore(args.database).audit(prune=args.prune) if args.database.is_file() else {'status':'not-created','groups':[]}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if args.summary and os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as summary:
            summary.write('## Lesson catalog guard\n\n```json\n'+json.dumps(result,indent=2)+'\n```\n\nNo pupil database, cloud model or speech provider was accessed.\n')
