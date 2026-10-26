"""Orchestrator (CODE, deterministic): điều phối 4 subagent + GATE + lọc.
Hỗ trợ chạy song song (workers>1) để scale — logic GATE không đổi."""
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from schema import Sample
from subagents import challenge, solve, verify_cot
from verifier import answers_match


def _norm_q(q):
    return "".join(q.lower().split())


def run_one(seed, seen, idx=0, use_judge=True, lock=None):
    """Sinh 1 mẫu. Trả (Sample|None, lý_do). Thread-safe nếu truyền lock."""
    ch = challenge(seed, idx)
    q, expected = ch.get("question"), ch.get("final_answer")
    if not q or expected is None:
        return None, "challenger_fail"

    qn = _norm_q(q)
    if lock:
        with lock:
            is_dup = qn in seen
    else:
        is_dup = qn in seen
    if is_dup:
        return None, "duplicate"

    # ② Strong PHẢI đúng (đối chiếu đáp án challenger) -> verify code
    strong_cot, strong_ans = solve(q, "strong", idx)
    if not answers_match(strong_ans, expected):
        return None, "strong_mismatch"

    # ③ Weak NÊN sai -> gradient độ khó
    _, weak_ans = solve(q, "weak", idx)
    if answers_match(weak_ans, expected):
        return None, "too_easy"

    # ④ Judge phụ (chấm CoT)
    judge = verify_cot(q, strong_cot, expected, idx) if use_judge else {"valid": True, "reason": ""}
    if not judge.get("valid", False):
        return None, "bad_cot"

    if lock:
        with lock:
            seen.add(qn)
    else:
        seen.add(qn)

    return Sample(
        id=f"vi-gsm-{idx:06d}",
        question=q,
        chain_of_thought=strong_cot,
        final_answer=str(expected),
        verify={"method": "code-exec", "passed": True, "judge": judge.get("reason", "")},
        difficulty={"strong_pass": True, "weak_fail": True},
        topic=ch.get("topic", ""),
        source_seed=seed.question[:40],
        lang="vi",
    ), "kept"


def generate(seeds, n, use_judge=True, workers=1, out_path=None,
             initial_seen=None, append=False, idx_offset=0):
    """Sinh tới khi đủ n mẫu. workers>1 -> song song. Ghi streaming.
    Resume: initial_seen (dedup), append (không ghi đè), idx_offset (id không trùng)."""
    seen, kept, stats = set(initial_seen or ()), [], {}
    lock = threading.Lock()
    limit = n * 8  # trần số thử (chống loop vô hạn)
    fout = open(out_path, "a" if append else "w", encoding="utf-8") if out_path else None

    def record(s, reason):  # gọi tuần tự trong main thread -> an toàn
        stats[reason] = stats.get(reason, 0) + 1
        if s:
            kept.append(s)
            if fout:
                fout.write(json.dumps(s.to_dict(), ensure_ascii=False) + "\n")
                fout.flush()

    def task(i):
        return run_one(seeds[i % len(seeds)], seen, idx_offset + i, use_judge, lock)

    try:
        if workers <= 1:  # tuần tự
            i = 0
            while len(kept) < n and i < limit:
                s, reason = task(i)
                record(s, reason)
                i += 1
        else:  # song song: luôn giữ ~workers thử đang chạy
            with ThreadPoolExecutor(max_workers=workers) as ex:
                i = 0
                futures = set()
                while i < workers and i < limit:
                    futures.add(ex.submit(task, i))
                    i += 1
                while futures and len(kept) < n:
                    done = next(as_completed(futures))
                    futures.discard(done)
                    s, reason = done.result()
                    record(s, reason)
                    if len(kept) < n and i < limit:
                        futures.add(ex.submit(task, i))
                        i += 1
    finally:
        if fout:
            fout.close()
    return kept[:n], stats
