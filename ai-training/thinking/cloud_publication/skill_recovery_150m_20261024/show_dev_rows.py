from pathlib import Path
import json,sys
p=Path(__file__).parent/f'review_step_{int(sys.argv[1]):06d}'
f=[json.loads(x) for x in (p/'new_validation_candidates.jsonl').read_text(encoding='utf8').splitlines()]
b=[json.loads(x) for x in (p/'training__eval_step_000000__base_generations.jsonl').read_text(encoding='utf8').splitlines()]
a=[json.loads(x) for x in (p/f'training__eval_step_{int(sys.argv[1]):06d}__adapter_generations.jsonl').read_text(encoding='utf8').splitlines()]
start=int(sys.argv[2]);count=int(sys.argv[3])
for i in range(start,min(len(f),start+count)):
 row={'index':i,'fixture':f[i],'base':{k:b[i][k] for k in ['output','ended_eos','possibly_truncated','timed_out']}}
 if i<len(a):row['adapter']={k:a[i][k] for k in ['output','ended_eos','possibly_truncated','timed_out']}
 print(json.dumps(row,ensure_ascii=False))
