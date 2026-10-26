from pathlib import Path
import sys,json
r=json.loads(Path(sys.argv[1]).read_bytes());v=r.get('result') or r.get('structured_content') or r.get('data')
s=''.join(''.join(x.get('text',[])) if isinstance(x.get('text'),list) else x.get('text','') for x in v['outputs'])
d=json.loads(s);out={k:d.get(k) for k in ['observed_utc','worker_alive','worker_exit','training/progress.json','training/error.json','training/best.json','training/run_complete.json','gpu','evaluation_progress','four_controls']}
for k,v in d.items():
 if k in ['step1_probe','locked_final_eval'] or k.startswith('final_eval') or k.endswith('/probe_error.json') or k.endswith('/probe_complete.json'):out[k]=v
pub=d.get('publication',{});out['publication']={k:pub.get(k) for k in ['state','folder_id','artifact_count','recent_errors','final_artifacts']}
out['publication']['checkpoints']=[{k:x.get(k) for k in ['id','step','rows_done','sha256','bytes','fresh_raw_readback_verified']} for x in pub.get('checkpoints',{}).values()]
if not d.get('worker_alive') and d.get('worker_exit'):out['error_log_tail']=d.get('log_tail','')[-1500:]
print(json.dumps(out,ensure_ascii=False))
