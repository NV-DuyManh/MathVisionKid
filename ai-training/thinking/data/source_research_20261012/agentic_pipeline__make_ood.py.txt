"""Tải SVAMP làm OOD eval (math word problems khác phân phối GSM8K).
Format giả-GSM8K (#### đáp số) để dùng lại translate_gsm8k.py."""
import json
import os

from datasets import load_dataset

ds = load_dataset("ChilleD/SVAMP")
split = "test" if "test" in ds else list(ds.keys())[0]
rows = list(ds[split])[:150]

os.makedirs("seeds", exist_ok=True)
with open("seeds/svamp150.jsonl", "w", encoding="utf-8") as f:
    for ex in rows:
        q = (ex["Body"].strip() + " " + ex["Question"].strip()).strip()
        ans = ex["Answer"]
        ans = str(int(ans)) if float(ans).is_integer() else str(ans)
        f.write(json.dumps({"question": q, "answer": f"#### {ans}"}, ensure_ascii=False) + "\n")

print(f"✓ SVAMP {len(rows)} bài (split={split}) -> seeds/svamp150.jsonl")
