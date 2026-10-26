from pathlib import Path
import json,hashlib
P=Path(__file__).parent;R=P/'review_step_000100'
raw=(R/'training__eval_step_000100__adapter_generations.jsonl').read_bytes()
prefix=json.loads((P/'completed_prefix_review.json').read_bytes())
assert hashlib.sha256(b''.join(raw.splitlines(keepends=True)[:12])).hexdigest()==prefix['candidate_prefix_raw_sha256']
dev=[json.loads(x) for x in (R/'new_validation_candidates.jsonl').read_bytes().splitlines()]
base=[json.loads(x) for x in (R/'training__eval_step_000000__base_generations.jsonl').read_bytes().splitlines()]
adapter=[json.loads(x) for x in raw.splitlines()]
rows=[{'fixture':f,'base_output':b['output'],'adapter_output':a['output'],
 'completed_eos':b['ended_eos'] and a['ended_eos'],'timed_out':b['timed_out'] or a['timed_out']} for f,b,a in zip(dev,base,adapter)]
for grade in [3,4,5]:
 dest=R/f'transcript_grade{grade}.json';assert not dest.exists()
 dest.write_text(json.dumps([x for x in rows if x['fixture']['grade']==grade],ensure_ascii=False,indent=2)+'\n',encoding='utf8')
dest=R/'prefix12_reverified.json';assert not dest.exists();dest.write_text(json.dumps({'exact_completed_prefix_matches_final_file':True,'prefix_sha256':prefix['candidate_prefix_raw_sha256'],'final_raw_sha256':hashlib.sha256(raw).hexdigest()},indent=2)+'\n')
print({'full_rows':len(rows),'prefix12_matches_final_exact_bytes':True,'all_eos':all(x['completed_eos'] for x in rows),'any_timeout':any(x['timed_out'] for x in rows)})
