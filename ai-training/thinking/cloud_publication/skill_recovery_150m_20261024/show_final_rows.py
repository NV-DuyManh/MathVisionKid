from pathlib import Path
import json,sys
p=Path(__file__).parent/'final_review'
rows=[]
for g in range(1,6):rows+=json.loads((p/f'paired_g{g}.json').read_bytes())
for i in range(int(sys.argv[1]),min(len(rows),int(sys.argv[1])+int(sys.argv[2]))):
 r=rows[i];b,s=r['base'],r['selected'];out={'index':i,'fixture':r['fixture'],'base':{k:b[k]for k in ['output','ended_eos','possibly_truncated','timed_out']}}
 if s['selected_protocol']=='inference_contract':
  assert all(b[k]==s[k]for k in b),'Selected baseline row changed'
  out['selected']={'same_as_base_all_fields':True}
 else:out['selected']={k:s[k]for k in ['output','ended_eos','possibly_truncated','timed_out','selected_protocol']}
 print(json.dumps(out,ensure_ascii=False))
