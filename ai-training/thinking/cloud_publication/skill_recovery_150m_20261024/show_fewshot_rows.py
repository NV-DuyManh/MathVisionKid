from pathlib import Path
from base_review_notes import B
import json,sys
p=Path(__file__).parent
fixtures=[json.loads(x)for x in(p/'review_step_000100/new_validation_candidates.jsonl').read_text(encoding='utf8').splitlines()]
rows=[json.loads(x)for x in(p/'fewshot_review/fewshot_dev__generations.jsonl').read_text(encoding='utf8').splitlines()]
for i in range(int(sys.argv[1]),min(len(rows),int(sys.argv[1])+int(sys.argv[2]))):
 print(json.dumps({'index':i,'fixture':fixtures[i],'baseline_judgment':B[i],'fewshot':rows[i]},ensure_ascii=False))
