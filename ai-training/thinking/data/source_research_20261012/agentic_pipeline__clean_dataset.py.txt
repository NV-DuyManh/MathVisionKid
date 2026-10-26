"""Dọn dataset theo chuẩn synthetic-data:
1) rule-filter: loại đáp án âm / = 0 (lỗi logic)
2) leak-filter: loại đáp án (>20) xuất hiện sẵn trong đề
3) semantic dedup: embedding đa ngôn ngữ + cosine (chuẩn cho data LLM-sinh, hơn MinHash lexical)
"""
import argparse
import json
import re

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--in", dest="inp", default="out/gsm8k_1500.jsonl")
ap.add_argument("--out", default="out/gsm8k_clean.jsonl")
ap.add_argument("--th", type=float, default=0.92, help="ngưỡng cosine để coi là cùng khuôn")
a = ap.parse_args()

rows = [json.loads(l) for l in open(a.inp, encoding="utf-8")]
n0 = len(rows)
nums = lambda t: re.findall(r"-?\d+(?:\.\d+)?", t.replace(",", ""))

# 1) rule-based: đáp án phải > 0
def ok_rule(r):
    try:
        return float(r["final_answer"]) > 0
    except ValueError:
        return False

# 2) leak: đáp án (>20) không được xuất hiện sẵn trong đề
def ok_leak(r):
    a_ = str(r["final_answer"])
    return not (a_ in nums(r["question"]) and abs(float(a_)) > 20)

s1 = [r for r in rows if ok_rule(r)]
s2 = [r for r in s1 if ok_leak(r)]
print(f"1) rule (âm/0): {n0} -> {len(s1)}  (loại {n0-len(s1)})")
print(f"2) leak:        {len(s1)} -> {len(s2)}  (loại {len(s1)-len(s2)})")

# 3) semantic dedup (greedy, giữ cái đầu, loại near-dup nghĩa)
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
emb = np.asarray(model.encode([r["question"] for r in s2], normalize_embeddings=True, batch_size=64))

# Trùng THẬT = cùng khuôn (cosine cao) VÀ cùng đáp án. "Cùng khuôn khác số" = đề hợp lệ -> GIỮ.
kept, ans = [], [str(r["final_answer"]) for r in s2]
for i in range(len(s2)):
    dup = False
    if kept:
        sims = emb[i] @ emb[kept].T
        for ji, j in enumerate(kept):
            if sims[ji] >= a.th and ans[i] == ans[j]:
                dup = True
                break
    if not dup:
        kept.append(i)
final = [s2[i] for i in kept]
print(f"3) dedup trùng-thật (cos>={a.th} & cùng đáp án): {len(s2)} -> {len(final)}  (loại {len(s2)-len(final)})")

with open(a.out, "w", encoding="utf-8") as f:
    for r in final:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"\n==> {a.out}: {len(final)}/{n0} mẫu sạch ({100*len(final)//n0}%)")
