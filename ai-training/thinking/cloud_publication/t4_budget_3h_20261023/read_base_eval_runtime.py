import json
p=budget_root/'training/base_generations.jsonl'
rows=[json.loads(x) for x in p.read_text().splitlines()]
assert len(rows)==28
print(json.dumps({'base_outputs':rows},ensure_ascii=False))
