#!/usr/bin/env python3
"""CPU-only immutable selected-view audit. Only the bounded report is written.

No model import, training, Drive access, evaluation payload access, or target edits.
Numeric checks are arithmetic checks, never semantic/curriculum/hint approval.
"""
from __future__ import annotations
import argparse, ast, hashlib, importlib.util, json, re, sys, time
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

MODEL = "Qwen/Qwen3-1.7B"
REVISION = "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
VIEW_SHA = "14929ba64e5c94d812f1fc3804c771ca8e41fa92285aed3a925282c39b1e4331"
MANIFEST_SHA = "444db8845af0c12bb528795b7e441b996571960dd58ab6898eb9394c77031545"
MODES = {"worked_solution", "hint_level_1", "hint_level_2", "hint_level_3"}
ROOT = Path("/content/mathvisionkid_corrective_5h_20261024")
NUMERIC = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:/[+-]?\d+)?$")


def sha_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def strict_object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate JSON key: " + key)
        out[key] = value
    return out


def strict_json(text):
    return json.loads(text, object_pairs_hook=strict_object,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite JSON: " + value)))


def load_helper(path):
    spec = importlib.util.spec_from_file_location("audited_exhaustive_colab_loader", path)
    if spec is None or spec.loader is None:
        raise ValueError("helper cannot be imported")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# Verbatim existing safe evaluator from primary_math_data_pipeline.py:61-87.
# Its exact source hash is recorded in the report. Only rational + - * /.
def exact(expression):
    """Only bounded rational + - * /, without eval, calls, floats, powers, or modulo."""
    if not isinstance(expression, str) or len(expression) > 4000:
        raise ValueError("expression length/type")
    tree = ast.parse(expression, mode="eval")
    if len(list(ast.walk(tree))) > 180:
        raise ValueError("expression too complex")
    def walk(node, depth=0):
        if depth > 24: raise ValueError("expression too deep")
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            literal = ast.get_source_segment(expression, node)
            if len(literal) > 80: raise ValueError("number too long")
            value = Fraction(literal)
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            value = -walk(node.operand, depth+1)
        elif isinstance(node, ast.BinOp):
            left, right = walk(node.left, depth+1), walk(node.right, depth+1)
            if isinstance(node.op, ast.Add): value = left + right
            elif isinstance(node.op, ast.Sub): value = left - right
            elif isinstance(node.op, ast.Mult): value = left * right
            elif isinstance(node.op, ast.Div): value = left / right
            else: raise ValueError("only + - * / allowed")
        else: raise ValueError("invalid arithmetic node")
        if max(value.numerator.bit_length(), value.denominator.bit_length()) > 512:
            raise ValueError("unbounded rational")
        return value
    return walk(tree.body)


def numeric_result(value):
    if type(value) not in (str, int, float):
        raise ValueError("not a numeric scalar")
    text = str(value).strip()
    if not NUMERIC.fullmatch(text):
        raise ValueError("categorical/unit-bearing/list/comparison result")
    return exact(text)


def expand(expression, preceding):
    def replace(match):
        index = int(match[1])
        if index >= len(preceding) or not preceding[index]:
            raise ValueError("forward/absent/uncheckable step reference")
        return "(" + preceding[index] + ")"
    return re.sub(r"\{s(\d+)\}", replace, expression)


def audit_numeric(target, sid, counts, examples):
    """Structured expressions only; do not reinterpret pedagogic prose as math."""
    preceding, checked = [], []
    steps = target.get("steps", [])
    if not isinstance(steps, list):
        raise ValueError("steps is not a list: " + sid)
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            raise ValueError("step is not an object: " + sid)
        expression = step.get("expression")
        if expression is None:
            counts["steps_without_numeric_expression_uncheckable"] += 1
            preceding.append("")
            continue
        try:
            if not isinstance(expression, str):
                raise ValueError("expression is not text")
            expanded = expand(expression, preceding)
            actual = exact(expanded)
            declared = numeric_result(step.get("result"))
        except (ValueError, TypeError, SyntaxError, ZeroDivisionError, OverflowError) as error:
            counts["step_expression_or_result_uncheckable"] += 1
            preceding.append("")
            if len(examples["uncheckable"]) < 12:
                examples["uncheckable"].append({"sample_id": sid, "step_index": index, "classification": str(error)[:140]})
            continue
        preceding.append(expanded)
        if actual != declared:
            counts["numeric_step_mismatches"] += 1
            if len(examples["mismatch"]) < 20:
                examples["mismatch"].append({"sample_id": sid, "step_index": index, "expression": expression[:120], "result": str(step.get("result"))[:80], "exact_value": str(actual)})
        else:
            counts["numeric_step_equalities_verified"] += 1
            checked.append((actual, step.get("unit", "")))
    answers = target.get("answer", [])
    if not isinstance(answers, list):
        counts["nonlist_answer_uncheckable"] += 1
        return
    for answer in answers:
        if not isinstance(answer, dict):
            counts["nondict_answer_uncheckable"] += 1
            continue
        try:
            value = numeric_result(answer.get("result"))
        except (ValueError, TypeError, SyntaxError, ZeroDivisionError, OverflowError):
            counts["categorical_answer_uncheckable"] += 1
            continue
        if (value, answer.get("unit", "")) in checked:
            counts["numeric_answer_matches_checked_step_and_unit"] += 1
        else:
            counts["numeric_answer_not_grounded_in_checked_step"] += 1
            if len(examples["ungrounded_answer"]) < 20:
                examples["ungrounded_answer"].append({"sample_id": sid, "result": str(answer.get("result"))[:80], "unit": str(answer.get("unit", ""))[:40]})


def audit(args, report):
    started = time.monotonic()
    root = args.root
    view, manifest_path = root / "training_view.jsonl", root / "sampling_manifest.json"
    helper_path = args.helper or root / "exhaustive_colab_loader.py"
    report["source_sha256"] = {"view": sha_file(view), "manifest": sha_file(manifest_path), "helper": sha_file(helper_path), "audit_script": sha_file(__file__)}
    if report["source_sha256"]["view"] != VIEW_SHA or report["source_sha256"]["manifest"] != MANIFEST_SHA:
        raise ValueError("pinned view/manifest hash mismatch")
    manifest = strict_json(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("training_view_sha256") != VIEW_SHA or manifest.get("selected_chat_rows") != 16000 or manifest.get("all_four_modes_preserved") is not True:
        raise ValueError("manifest view/count/modes declaration mismatch")
    expected, expected_cases = {}, {}
    for case in manifest["selected_cases_manifest"]:
        cid, rows = case["case_id"], case["rows"]
        if cid in expected_cases or set(rows) != MODES:
            raise ValueError("manifest duplicate case or missing mode")
        expected_cases[cid] = set()
        for mode, info in rows.items():
            sid = info["sample_id"]
            if sid in expected:
                raise ValueError("manifest duplicate sample ID")
            expected[sid] = (info["row_sha256"], cid, mode)
    if len(expected) != 16000 or len(expected_cases) != 4000:
        raise ValueError("manifest exact case/sample set size mismatch")
    helper = load_helper(helper_path)
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(str(args.tokenizer), revision=REVISION, trust_remote_code=False, local_files_only=True)
    if tokenizer.eos_token_id != 151645 or tokenizer.convert_tokens_to_ids("<|im_end|>") != 151645:
        raise ValueError("runtime tokenizer EOT/EOS mismatch")
    report["tokenizer"] = {"model": str(args.tokenizer), "revision": REVISION, "local_files_only": True, "eos_token_id": tokenizer.eos_token_id, "pad_token_id": tokenizer.pad_token_id}
    report["numeric_evaluator_source_sha256"] = hashlib.sha256(__import__("inspect").getsource(exact).encode()).hexdigest()
    seen, seen_cases = set(), defaultdict(set)
    hist, completions = defaultdict(Counter), defaultdict(Counter)
    counts, numeric, examples = Counter(), Counter(), defaultdict(list)
    templates, template_modes, template_examples = Counter(), defaultdict(Counter), defaultdict(list)
    system_hashes, acceptances, prompt_keys = Counter(), Counter(), Counter()
    case_prompts, pending = {}, []
    prompt_examples, student_examples = [], []
    max_input = max_completion = 0
    for line_no, raw in enumerate(view.open("rb"), 1):
        body = raw.rstrip(b"\r\n")
        if not body:
            raise ValueError("blank view row")
        row = strict_json(body)
        sid, mode = row.get("sample_id"), row.get("mode")
        cid = row.get("source_sample_id") or str(sid).removesuffix(":" + str(mode))
        binding = expected.get(sid)
        if sid in seen or binding != (hashlib.sha256(body).hexdigest(), cid, mode):
            raise ValueError("row sample/sourceID/mode/rawhash binding mismatch at " + str(line_no))
        if row.get("split") != "train":
            raise ValueError("nontrain row")
        seen.add(sid); seen_cases[cid].add(mode)
        helper.validate_chat(row)
        system, user, assistant = [x["content"] for x in row["messages"]]
        prompt, target = strict_json(user), strict_json(assistant)
        if not isinstance(prompt, dict) or not isinstance(target, dict) or prompt.get("mode") != mode:
            raise ValueError("prompt/target object or prompt-mode mismatch: " + sid)
        # Read the real problem and supplied student_work before inspecting its target.
        problem = prompt.get("problem")
        if not isinstance(problem, str) or not problem.strip():
            raise ValueError("missing real problem text: " + sid)
        contract = {k: v for k, v in prompt.items() if k != "mode"}
        if cid in case_prompts and case_prompts[cid] != contract:
            raise ValueError("same-case prompt/student_work differs across modes: " + sid)
        case_prompts[cid] = contract
        prompt_keys.update(prompt.keys())
        if mode == "worked_solution" and len(prompt_examples) < 3:
            prompt_examples.append({"sample_id": sid, "problem_excerpt": problem[:180], "student_work_present": bool(prompt.get("student_work"))})
        if prompt.get("student_work"):
            counts["rows_with_supplied_student_work"] += 1
            if mode == "worked_solution" and len(student_examples) < 5:
                student_examples.append({"sample_id": sid, "problem_excerpt": problem[:180], "student_work_excerpt": str(prompt["student_work"])[:220]})
        status = str(row.get("acceptance_status", row.get("quality_status", "MISSING")))
        acceptances[status] += 1
        if not (status.startswith("ACCEPTED") or status == "OWNER_HUMAN_CERTIFIED"):
            raise ValueError("unaccepted/missing acceptance status: " + sid)
        system_hashes[hashlib.sha256(system.encode()).hexdigest()] += 1
        target_hash = hashlib.sha256(assistant.encode()).hexdigest()
        templates[target_hash] += 1; template_modes[target_hash][mode] += 1
        if len(template_examples[target_hash]) < 3:
            template_examples[target_hash].append(sid)
        if mode == "worked_solution":
            audit_numeric(target, sid, numeric, examples)
        else:
            counts["hint_rows_not_arithmetic_or_semantic_certified"] += 1
        encoded = helper.tokenize_assistant_only(row, tokenizer, max_sequence_tokens=2048)
        ids, mask, labels = [encoded[k] for k in ("input_ids", "attention_mask", "labels")]
        positions = [i for i, label in enumerate(labels) if label != -100]
        if len(ids) != len(mask) or len(ids) != len(labels) or not positions or len(ids) > 2048:
            raise ValueError("token/mask shape or sequence bound failure: " + sid)
        if positions[0] != encoded["prompt_tokens"] or any(labels[i] != ids[i] for i in positions) or any(mask[i] != 1 for i in range(len(ids))):
            raise ValueError("unshifted input/label or attention alignment failure: " + sid)
        if labels[positions[-1]] != 151645 or sum(labels[i] == 151645 for i in positions) != 1:
            raise ValueError("not exactly one final supervised EOT: " + sid)
        if positions[0] == 0 or sum(label != -100 for label in labels[1:]) != len(positions):
            raise ValueError("causal-shift drops assistant target: " + sid)
        if positions != list(range(positions[0], positions[-1] + 1)) or any(x != -100 for x in labels[positions[-1] + 1:]):
            raise ValueError("noncontiguous assistant or supervised suffix: " + sid)
        counts[mode] += 1; counts["rows_tokenized"] += 1
        counts["exact_one_final_supervised_eot"] += 1; counts["shifted_target_alignment_checked"] += 1
        counts["supervised_tokens"] += len(positions)
        max_input, max_completion = max(max_input, len(ids)), max(max_completion, len(positions))
        hist[mode][str(((len(ids)-1)//128)*128 + 1) + "-" + str(((len(ids)-1)//128+1)*128)] += 1
        completions[mode][str(((len(positions)-1)//128)*128 + 1) + "-" + str(((len(positions)-1)//128+1)*128)] += 1
        pending.append(encoded)
        if len(pending) == 16:
            batch = helper.pad_batch(pending, pad_token_id=tokenizer.pad_token_id)
            for e, padded_ids, padded_mask, padded_labels in zip(pending, batch["input_ids"], batch["attention_mask"], batch["labels"]):
                n = len(e["input_ids"])
                if padded_ids[:n] != e["input_ids"] or padded_labels[:n] != e["labels"] or any(padded_mask[n:]) or any(x != -100 for x in padded_labels[n:]):
                    raise ValueError("padding attention/label loss leak")
                if any(x != tokenizer.pad_token_id for x in padded_ids[n:]):
                    raise ValueError("wrong padding token")
                counts["padding_rows_checked"] += 1
                counts["padding_tokens_masked"] += len(padded_ids) - n
            pending.clear()
        if line_no % 2000 == 0:
            print(json.dumps({"audit_rows": line_no, "numeric_mismatches": numeric["numeric_step_mismatches"], "elapsed_seconds": round(time.monotonic()-started, 2)}), flush=True)
    if pending or seen != set(expected) or set(seen_cases) != set(expected_cases) or any(m != MODES for m in seen_cases.values()):
        raise ValueError("view exact sample/case/four-mode set or final padding batch mismatch")
    if counts["rows_tokenized"] != 16000 or any(counts[mode] != 4000 for mode in MODES):
        raise ValueError("tokenized mode count mismatch")
    report.update(state="PASS_STRUCTURAL_TOKENIZATION_ONLY", counts=dict(counts), numeric_checks=dict(numeric), numeric_examples=dict(examples), max_input_tokens=max_input, max_completion_tokens=max_completion,
                  input_length_histogram_by_mode={m:dict(c) for m,c in hist.items()}, completion_length_histogram_by_mode={m:dict(c) for m,c in completions.items()},
                  exact_case_count=len(seen_cases), all_sample_id_rawhash_sourceid_mode_bindings_verified=True, case_prompts_and_studentwork_identical_across_modes=True,
                  system_hash_counts=dict(system_hashes), acceptance_status_counts=dict(acceptances), prompt_key_counts=dict(prompt_keys), prompt_examples=prompt_examples, supplied_student_work_examples=student_examples,
                  duplicate_assistant_templates={"unique_target_hashes":len(templates), "repeated_target_hashes":sum(n>1 for n in templates.values()), "rows_beyond_first_identical_target":sum(n-1 for n in templates.values()), "top20":[{"sha256":h,"count":n,"by_mode":dict(template_modes[h]),"sample_ids":template_examples[h]} for h,n in templates.most_common(20)]},
                  elapsed_seconds=round(time.monotonic()-started,2))
    if numeric["numeric_step_mismatches"]:
        report["state"] = "FAIL_CONFIRMED_NUMERIC_TARGET_MISMATCH"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--helper", type=Path)
    parser.add_argument("--tokenizer", default=MODEL)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    out = args.out or args.root / "selected_view_tokenization_audit.json"
    if not out.parent.exists() or out.resolve() in {(args.root/"training_view.jsonl").resolve(), (args.root/"sampling_manifest.json").resolve()}:
        raise ValueError("report output must be an existing-directory path distinct from inputs")
    report = {"schema":"MathVisionKid.selected_view_cpu_tokenization_audit.v1", "state":"RUNNING", "gpu_used":False, "model_loaded":False, "data_modified":False, "eval_payload_read":False,
              "semantic_proof":False,"human_review_attested":False,"numeric_scope":"Existing bounded rational evaluator checks structured expression/result pairs only; categorical, prose, hint safety, feedback grounding and units' semantic correctness remain uncheckable, never automatic PASS."}
    try:
        audit(args, report)
    except Exception as error:
        report.update(state="FAIL_AUDIT", error_type=type(error).__name__, error=str(error)[:700])
    # The only persistent write performed by this script is this compact report.
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"state":report["state"],"report":str(out),"counts":report.get("counts",{}),"numeric_checks":report.get("numeric_checks",{}),"error":report.get("error")},ensure_ascii=True),flush=True)
    return 0 if report["state"] == "PASS_STRUCTURAL_TOKENIZATION_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
