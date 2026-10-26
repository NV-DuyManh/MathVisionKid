from pathlib import Path
import sys,json
rows=json.loads(Path(sys.argv[1]).read_bytes());start=int(sys.argv[2]);count=int(sys.argv[3])
for r in rows[start:start+count]:
 print(json.dumps({'fixture':r['fixture'],'base':{k:v for k,v in r['base'].items() if k in ['output','ended_eos','possibly_truncated','timed_out','generated_tokens']},'adapter':{k:v for k,v in r['adapter'].items() if k in ['output','ended_eos','possibly_truncated','timed_out','generated_tokens']}},ensure_ascii=False))
