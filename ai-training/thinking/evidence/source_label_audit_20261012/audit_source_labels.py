"""Read-only audit of frozen real_math_v1 source labels and unsafe MCQ rotation."""
from pathlib import Path
import hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import real_math_data as old
from real_math_training import rotated
SOURCE=ROOT/'data'/'real_math_v1'
OUT=Path(__file__).resolve().parent
FINAL_DECL=re.compile(r'(?i)đáp án\s+(?:cần chọn|phải chọn|ta chọn)\s+(?:là\s*)?[:：]?\s*([ABCD])\b')
META=re.compile(r'(?i)cả\s+(?:hai|ba)|đáp án\s+(?:trên|dưới)|phương án\s+(?:trên|dưới)|\b(?:A và B|A, B|B và C)\b')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
paths=[SOURCE/'raw'/'vietjack.json']+[SOURCE/'clean'/(s+'.jsonl') for s in ('train','val','test')]+[ROOT/n for n in ('real_math_data.py','real_math_training.py','train_real_math.py','mcq_final_answer.py')]
before={str(p.relative_to(ROOT)):sha(p) for p in paths}
raw=json.loads(paths[0].read_text(encoding='utf-8'))
by_id={}
for parent in raw:
 for i,p in enumerate(parent.get('problems',[])):
  q=old.norm(re.sub(r'^\s*Câu\s*\d+\s*[:.]\s*','',p.get('question',''),flags=re.I))
  sid=old.digest(parent['url']+'\n'+str(i)+'\n'+q)[:24]
  by_id[sid]={'source_page':parent['url'],'source_index':i,'raw_question':p.get('question'),'raw_choices':p.get('choices'),'raw_explanation':p.get('explanation')}
conflicts=[];risk=[];counts={};remaining_letters={}
for split in ('train','val','test'):
 rows=[json.loads(x) for x in (SOURCE/'clean'/(split+'.jsonl')).read_text(encoding='utf-8').splitlines() if x.strip()]
 splitconf=[];splitrisk=[]
 remaining_letters[split]=sum(bool(re.search(r'\b[ABCD]\b',r['explanation'])) for r in rows)
 for r in rows:
  source=by_id[r['sample_id']]
  finals=set(x.upper() for x in FINAL_DECL.findall(old.norm(source['raw_explanation'])))
  if finals and any(a!=r['answer'] for a in finals):
   item={'split':split,'sample_id':r['sample_id'],'question':r['question'],'choices':r['choices'],'stored_answer':r['answer'],'explicit_source_final_answers':sorted(finals),'stored_explanation':r['explanation'],'diagnosis':'OLD_LABEL_REGEX_READS_INNER_OPTION_REFERENCE_AND_MISSES_SOURCE_FINAL_DECLARATION','verification':'SOURCE_ANNOTATION_CONFLICT_NOT_TEACHER_SEMANTIC_CERTIFICATION',**source}
   splitconf.append(item);conflicts.append(item)
  if any(META.search(c) for c in r['choices']):
   training_shift=int(old.digest(r['sample_id'])[:8],16)%4
   choice1,answer1=rotated(r,1)
   item={'split':split,'sample_id':r['sample_id'],'question':r['question'],'choices':r['choices'],'stored_answer':r['answer'],'training_shift':training_shift,'shift1_choices':choice1,'shift1_target':answer1,'stored_explanation':r['explanation'],'diagnosis':'UNSAFE_META_OR_POSITIONAL_OPTION_REFERENCE_NOT_REWRITTEN_BY_ROTATED_FUNCTION','notes':'Flagged transformation risk; not every letter is an answer reference. C/r in geometry formulas are excluded. References to all preceding options must not be rotated without rewriting semantics.',**source}
   splitrisk.append(item);risk.append(item)
 counts[split]={'rows':len(rows),'explicit_final_label_conflicts':len(splitconf),'unsafe_meta_or_positional_option_rotation_candidates':len(splitrisk),'training_risky_nonzero_rotation':sum(i['training_shift']!=0 for i in splitrisk) if split=='train' else None}
after={str(p.relative_to(ROOT)):sha(p) for p in paths}
assert before==after
assert counts['train']['explicit_final_label_conflicts']==3
assert counts['val']['explicit_final_label_conflicts']==0
assert counts['test']['explicit_final_label_conflicts']==0
assert [counts[s]['unsafe_meta_or_positional_option_rotation_candidates'] for s in ('train','val','test')]==[11,1,2]
report={'audit_id':'source_label_audit_20261012','status':'COMPLETED_READ_ONLY_FROZEN_SOURCE_UNCHANGED','counts':counts,'source_final_conflicts':conflicts,'meta_or_positional_option_rotation_candidates':risk,'residual_single_letter_rationale_counts_not_all_errors':remaining_letters,'frozen_sha256':before,'frozen_sources_unchanged':True,'limitations':['This deterministic audit is a targeted lower bound, not a full certification of963rows.','The three source-final conflicts show actual extraction corruption; all remaining labels may still have semantic issues.','Meta-option candidates identify unsafe rotation semantics; existing old run logs/predictions must stay frozen.','Old base-vs-adapter validation ordering remains observation against imperfect source keys, not certified mathematical accuracy.','Whole-dataset choice-rotation accuracy/consistency is contaminated by two invalid transformed test questions.','No GPU process or training was run; no frozen files were edited.'],'recommended_action':['Exclude all meta/positional option references from future transformed MCQ datasets, or rewrite and reverify every reference.','For next dataset, train free-response plans/answers with exact arithmetic and provenance instead of one-letter options.','Use independently parsed explicit answer declarations, fail closed on ambiguity, and never globally delete answer-looking substrings from rationale.','Keep old evidence historical and mark label-audit caveats in the canonical context.']}
(OUT/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print(json.dumps({'status':report['status'],'counts':counts,'frozen_sources_unchanged':True,'output':str(OUT/'audit.json')},ensure_ascii=True))

