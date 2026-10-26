from pathlib import Path
import json,sys
p=Path(__file__).parent/'final_review'
f=[json.loads(x) for x in (p/'locked_test_candidates.jsonl').read_text(encoding='utf8').splitlines()]
b=[json.loads(x) for x in (p/'final_eval__base_generations.jsonl').read_text(encoding='utf8').splitlines()]
for i in range(int(sys.argv[1]),min(len(b),int(sys.argv[1])+int(sys.argv[2]))):
 assert f[i]['id']==b[i]['fixture_id']
 print(json.dumps({'index':i,'fixture':f[i],'actual':b[i]},ensure_ascii=False))
