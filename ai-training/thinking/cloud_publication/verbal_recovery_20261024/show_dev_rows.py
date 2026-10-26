from pathlib import Path
import json,sys
d=Path(__file__).parent/'review_step_000050'
def rows(name):return [json.loads(x) for x in (d/name).read_text(encoding='utf8').splitlines()]
dev=rows('new_validation_candidates.jsonl');base=rows('training__eval_step_000000__base_generations.jsonl');adapter=rows('training__eval_step_000050__adapter_generations.jsonl')
start,count=int(sys.argv[1]),int(sys.argv[2])
for i in range(start,min(start+count,len(adapter))):
 f,b,a=dev[i],base[i],adapter[i];assert f['id']==b['fixture_id']==a['fixture_id']
 print(json.dumps({'index':i,'fixture':f,'base':{k:b[k] for k in ['output','ended_eos','possibly_truncated','timed_out']},'adapter':{k:a[k] for k in ['output','ended_eos','possibly_truncated','timed_out']}},ensure_ascii=False))
