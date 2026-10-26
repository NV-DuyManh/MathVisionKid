"""Deterministic recovery sampling and fail-closed quality gates. No I/O on import."""
import hashlib,json,random,re,unicodedata
from collections import Counter,defaultdict,deque

def digest(b):return hashlib.sha256(b).hexdigest()
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def prompt_key(s,mask_numbers=False):
 s=unicodedata.normalize('NFKC',s).casefold()
 if mask_numbers:s=re.sub(r'\d+(?:[.,/]\d+)*','#',s)
 return ''.join(c for c in s if c.isalnum() or c=='#')

def prepare_plan(raw_rows,source_sha,seed=20261024):
 """Keep every worked solution; cap identical hints within grade/topic/mode.

 No source row or acceptance label is edited/deleted. All original IDs remain
 hash-bound in the immutable input. This is a derived training view only.
 """
 seen_ids=set();worked=[];hint_groups=defaultdict(list)
 for i,row in enumerate(raw_rows):
  sid=row['sample_id']
  if sid in seen_ids or row['split']!='train':raise ValueError('duplicate or nontrain input')
  seen_ids.add(sid)
  if row['mode']=='worked_solution':worked.append(i)
  else:
   if row['mode'] not in ('hint_level_1','hint_level_2','hint_level_3'):raise ValueError('mode')
   key=(row['grade'],row.get('topic',''),row['mode'],digest(row['messages'][-1]['content'].encode()))
   hint_groups[key].append(i)
 def rank(i):return digest((str(seed)+'|'+raw_rows[i]['sample_id']).encode())
 hints=[min(v,key=rank) for v in hint_groups.values()]
 # Interleave grades and modes, then ten worked + six hint rows per group while
 # both pools have enough rows. Exhausted pools fill from the other; no repeats.
 def grade_queue(indices):
  buckets=defaultdict(list)
  for i in indices:buckets[int(raw_rows[i]['grade'])].append(i)
  for v in buckets.values():v.sort(key=rank)
  queues={g:deque(v) for g,v in buckets.items()};out=[]
  while any(queues.values()):
   for g in sorted(queues):
    if queues[g]:out.append(queues[g].popleft())
  return deque(out)
 w,h=grade_queue(worked),grade_queue(hints);order=[]
 while w or h:
  for q,n in ((w,10),(h,6)):
   for _ in range(n):
    if q:order.append(q.popleft())
  if not w or not h:
   q=w or h
   while q and len(order)%16:order.append(q.popleft())
 ids=[raw_rows[i]['sample_id'] for i in order]
 assert len(ids)==len(set(ids)) and set(worked).issubset(order)
 return {'schema':'MathVisionKid.quality_recovery_sampling.v1','source_view_sha256':source_sha,'seed':seed,
  'source_rows':len(raw_rows),'view_rows':len(order),'all_worked_solutions_preserved':True,
  'source_rows_modified_or_deleted':0,'sampling':'one pass; grade interleave;10worked+6hint while pools available; no ID repetition',
  'hint_duplicate_cap':'one representative per grade/topic/mode/exact assistant-target SHA; other original rows remain in source',
  'mode_counts':dict(Counter(raw_rows[i]['mode'] for i in order)),
  'schedule':ids,'selected_rows':[{'sample_id':raw_rows[i]['sample_id'],'canonical_embedded_row_sha256':digest(canonical(raw_rows[i]).encode()),'assistant_sha256':digest(raw_rows[i]['messages'][-1]['content'].encode())} for i in order],
  'hash_note':'canonical_embedded_row_sha256 is not the frozen original raw JSONL row hash; original raw binding remains in sampling_manifest and is independently validated by loader'}

def screen_fixtures(fixtures,raw_rows):
 exact={prompt_key(json.loads(r['messages'][1]['content'])['problem']) for r in raw_rows}
 masked={prompt_key(json.loads(r['messages'][1]['content'])['problem'],True) for r in raw_rows}
 ids=set();collisions=[]
 for f in fixtures:
  if f['id'] in ids:raise ValueError('duplicate fixture')
  ids.add(f['id'])
  e=prompt_key(f['userproblem']) in exact;m=prompt_key(f['userproblem'],True) in masked
  if e or m:collisions.append({'id':f['id'],'exact':e,'number_masked':m})
 return {'fixtures':len(fixtures),'training_rows_screened':len(raw_rows),'collisions':collisions,
  'scope':'exact and number-masked text against actual16kview only; no full-corpus or semantic independence claim'}

EVALUATION_MODES=('answer','hint_no_answer','missing_or_contradictory_info','student_error')
GATE_HASH_FIELDS=('dev_sha256','contract_sha256','source_plan_sha256',
 'base_output_sha256','adapter_output_sha256','generation_manifest_sha256')


def summarize_decisions(records):
 """Derive safety/selection from thirty paired full-task semantic reviews.

 Fields: fixture_id, mode, grade, base_pass, adapter_pass, base_hint_leak,
 adapter_hint_leak, critical_new_error. Five flags must be real booleans.
 Extra evidence fields may remain. No baseline-pass regression in ANY mode,
 new critical error or new hint leak is allowed. Eligibility additionally needs
 one primary-answer gain; at a perfect base-answer ceiling only, preserving all
 answers plus at least one useful-hint gain suffices. Counts are not text review
 or human certification. Generic but safe hints need not receive a task pass.
 """
 if not isinstance(records,list) or len(records)!=30:raise ValueError('decisions must contain exactly30 paired records')
 flags=('base_pass','adapter_pass','base_hint_leak','adapter_hint_leak','critical_new_error')
 ids=set()
 for r in records:
  if not isinstance(r,dict):raise ValueError('decision record must be an object')
  sid=r.get('fixture_id')
  if not isinstance(sid,str) or not sid or sid in ids:raise ValueError('missing/duplicate fixture_id')
  ids.add(sid)
  if r.get('mode') not in EVALUATION_MODES:raise ValueError('unsupported review mode')
  if type(r.get('grade')) is not int or r['grade'] not in range(1,6):raise ValueError('review grade must be integer1..5')
  if any(type(r.get(k)) is not bool for k in flags):raise ValueError('review decisions must be booleans')
  if r['mode']!='hint_no_answer' and (r['base_hint_leak'] or r['adapter_hint_leak']):raise ValueError('hint leakage flags belong to hint fixtures only')
  if r['mode']=='hint_no_answer' and ((r['base_pass'] and r['base_hint_leak']) or (r['adapter_pass'] and r['adapter_hint_leak'])):raise ValueError('a leaking hint cannot pass the full semantic task')
 def count_side(field,leak):
  result={'answers':0,'total':sum(r[field] for r in records),'hints':0,'guards':0,'feedback':0,
   'answer_denominator':sum(r['mode']=='answer' for r in records),'hint_leaks':sum(r[leak] for r in records),'by_mode':{},'by_grade':{}}
  for mode in EVALUATION_MODES:
   subset=[r for r in records if r['mode']==mode];result['by_mode'][mode]={'count':len(subset),'pass':sum(r[field] for r in subset)}
  for grade in range(1,6):
   subset=[r for r in records if r['grade']==grade]
   result['by_grade'][str(grade)]={'count':len(subset),'total':sum(r[field] for r in subset),
    'answers':sum(r[field] for r in subset if r['mode']=='answer'),'answer_denominator':sum(r['mode']=='answer' for r in subset),
    'hints':sum(r[field] for r in subset if r['mode']=='hint_no_answer'),
    'guards':sum(r[field] for r in subset if r['mode']=='missing_or_contradictory_info'),
    'feedback':sum(r[field] for r in subset if r['mode']=='student_error')}
  for key,mode in [('answers','answer'),('hints','hint_no_answer'),('guards','missing_or_contradictory_info'),('feedback','student_error')]:result[key]=result['by_mode'][mode]['pass']
  return result
 base=count_side('base_pass','base_hint_leak');candidate=count_side('adapter_pass','adapter_hint_leak')
 if not base['answer_denominator']:raise ValueError('review set needs primary answer fixtures')
 regressions=[r for r in records if r['base_pass'] and not r['adapter_pass']]
 critical=[r['fixture_id'] for r in records if r['critical_new_error']]
 leaks=[r['fixture_id'] for r in records if r['adapter_hint_leak'] and not r['base_hint_leak']]
 answer_gain=candidate['answers']-base['answers'];hint_gain=candidate['hints']-base['hints']
 perfect=base['answers']==base['answer_denominator'];safe=not regressions and not critical and not leaks
 eligible=safe and candidate['answers']>=base['answers'] and candidate['total']>base['total']
 return {'schema':'MathVisionKid.quality_recovery_decisions_summary.v1','fixture_count':30,'fixture_ids':[r['fixture_id'] for r in records],
  'base':base,'candidate':candidate,'strict_answer_gain':answer_gain,'strict_gain_vs_base':candidate['total']-base['total'],
  'useful_hint_gain':hint_gain,'baseline_answer_perfect':perfect,'baseline_pass_regressions':len(regressions),
  'baseline_pass_regression_fixture_ids':[r['fixture_id'] for r in regressions],
  'new_baseline_correct_answer_failures':sum(r['mode']=='answer' for r in regressions),
  'new_guard_failures':sum(r['mode']=='missing_or_contradictory_info' for r in regressions),
  'new_student_feedback_failures':sum(r['mode']=='student_error' for r in regressions),
  'new_useful_hint_failures':sum(r['mode']=='hint_no_answer' for r in regressions),
  'new_hint_leaks':len(leaks),'new_hint_leak_fixture_ids':leaks,
  'new_critical_errors':len(critical),'new_critical_error_fixture_ids':critical,
  'safe_to_continue_pilot':safe,'candidate_eligible':eligible,'eligibility_rule':'No baseline-pass regression/new critical/new hint leak, retain all base answers, and at least one full-task gain in any requested tutor mode'}


def selection_key(summary,side):
 """Return (answers,total,hints,guards,feedback); higher wins, earlier wins ties.

 side='base' or 'candidate' ('adapter' alias). Key ranking NEVER substitutes for
 candidate_eligible. STOP can end training while an eligible checkpoint remains
 selectable; STOP does not make a bad candidate eligible. Worker handles ties.
 """
 if side=='adapter':side='candidate'
 if side not in ('base','candidate'):raise ValueError('selection side must be base/candidate')
 values=summary.get(side)
 if not isinstance(values,dict):raise ValueError('missing side summary')
 key=tuple(values.get(k) for k in ('answers','total','hints','guards','feedback'))
 if any(type(v) is not int or v<0 for v in key):raise ValueError('selection counts must be nonnegative integers')
 return key


def validate_gate(gate,step,bindings):
 """Bind hashes/step/full review and derive counts from decisions:list[30].

 All six GATE_HASH_FIELDS plus fixture_ids:list[30] are required bindings and
 copied into gate JSON. Review IDs must match that exact unique set; row order
 may differ. Require all_actual_outputs_reviewed:true,human_review_claimed:false.
 Ignore caller aggregate claims. STOP is allowed for any fully bound review.
 CONTINUE_PILOT requires a safe review at step50 only, without a gain requirement;
 CONTINUE_IMPROVED requires candidate_eligible, including at step100 and beyond.
 """
 if not isinstance(gate,dict) or not isinstance(bindings,dict):raise ValueError('gate/bindings must be objects')
 if any(k not in bindings for k in GATE_HASH_FIELDS) or 'fixture_ids' not in bindings:raise ValueError('missing required gate hash/fixture bindings')
 expected=bindings['fixture_ids']
 if not isinstance(expected,list) or len(expected)!=30 or any(not isinstance(x,str) or not x for x in expected) or len(set(expected))!=30:raise ValueError('bindings require exactly30 unique fixture_ids')
 for k in GATE_HASH_FIELDS:
  if not isinstance(bindings[k],str) or re.fullmatch(r'[0-9a-fA-F]{64}',bindings[k]) is None:raise ValueError('invalid bound SHA256: '+k)
 for k,v in bindings.items():
  if gate.get(k)!=v:raise ValueError('gate binding mismatch: '+k)
 if type(step) is not int or step<0 or type(gate.get('step')) is not int or gate['step']!=step or gate.get('all_actual_outputs_reviewed') is not True:raise ValueError('incomplete gate')
 if gate.get('human_review_claimed') is not False:raise ValueError('no new human attestation')
 summary=summarize_decisions(gate.get('decisions'))
 if set(summary['fixture_ids'])!=set(expected):raise ValueError('review fixture_ids differ from exact bound fixture set')
 decision=gate.get('decision')
 if decision not in ('CONTINUE_PILOT','CONTINUE_IMPROVED','STOP'):raise ValueError('unknown gate decision')
 if decision=='STOP':return decision
 if not summary['safe_to_continue_pilot']:raise ValueError('quality regression/new critical error/leak cannot continue')
 if decision=='CONTINUE_PILOT':
  if step!=50:raise ValueError('CONTINUE_PILOT is allowed only at step50')
 elif not summary['candidate_eligible']:raise ValueError('no eligible primary-answer improvement or perfect-answer useful-hint gain')
 return decision


# Explicit v2 derived schedule supersedes original prepare_plan; original gate rules stay unchanged.
"""Hierarchical deterministic one-pass balanced view; source rows stay intact."""
import hashlib
import json
from collections import Counter, defaultdict, deque

MODES = {"worked_solution", "hint_level_1", "hint_level_2", "hint_level_3"}


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _behavior(row):
    try:
        prompt = json.loads(row["messages"][1]["content"])
        target = json.loads(row["messages"][-1]["content"])
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid prompt/target JSON") from exc
    if not isinstance(prompt, dict) or not isinstance(target, dict):
        raise ValueError("prompt and target must be JSON objects")
    if prompt.get("mode") != row["mode"]:
        raise ValueError("prompt mode differs from row mode")
    if row["mode"] == "worked_solution" and target.get("can_solve") is False:
        return "guard"
    if prompt.get("student_work") is not None:
        return "student_feedback"
    return "standard"


def prepare_plan(raw_rows, source_sha, seed=20261024):
    """Deduplicate within grade/topic/mode/behavior, then hierarchically weave.

    One visit per extant topic/provenance group occurs before a second visit.
    Visits are round-robined by grade, then by behavior+mode within grade, then
    by topic/provenance within that bucket. Empty topics use identity only as
    provenance partition; this does not infer conceptual skill.
    """
    if not isinstance(raw_rows, list):
        raise ValueError("raw_rows must be a list")
    if not isinstance(source_sha, str) or len(source_sha) != 64 or any(c not in "0123456789abcdefABCDEF" for c in source_sha):
        raise ValueError("source_sha must be a 64-character SHA256 hex string")
    ids, buckets = set(), defaultdict(list)
    for i, row in enumerate(raw_rows):
        if not isinstance(row, dict) or row.get("split") != "train":
            raise ValueError("nontrain or invalid input row")
        sid, mode = row.get("sample_id"), row.get("mode")
        if not isinstance(sid, str) or not sid or sid in ids:
            raise ValueError("missing or duplicate sample_id")
        ids.add(sid)
        if not isinstance(mode, str) or mode not in MODES:
            raise ValueError("invalid mode")
        if type(row.get("grade")) is not int or row["grade"] not in range(1, 6):
            raise ValueError("invalid grade")
        if not isinstance(row.get("messages"), list) or len(row["messages"]) < 3:
            raise ValueError("invalid messages")
        behavior = _behavior(row)
        topic = row.get("topic")
        topic_key = ("topic", str(topic)) if topic else (
            "unlabeled_case", str(row.get("case_group_id") or row.get("source_sample_id") or sid))
        try:
            target = json.loads(row["messages"][-1]["content"])
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid assistant target JSON") from exc
        if not isinstance(target, dict):
            raise ValueError("assistant target must be a JSON object")
        target_hash = _sha(_canonical(target).encode("utf-8"))
        group = (row["grade"], topic_key, mode, behavior)
        buckets[(group, target_hash)].append(i)

    def rank(i):
        return _sha((str(seed) + "|" + raw_rows[i]["sample_id"]).encode("utf-8"))

    groups, provenance = defaultdict(list), {}
    for (group, _target_hash), members in buckets.items():
        rep = min(members, key=rank)
        groups[group].append(rep)
        provenance[raw_rows[rep]["sample_id"]] = sorted(raw_rows[i]["sample_id"] for i in members)

    # Within each grade, rotate behavior+mode buckets and their topic queues.
    # Then rotate grades, so abundant grade-1 groups cannot delay grade 5.
    per_grade = {}
    member_queues = {group: deque(sorted(members, key=rank)) for group, members in groups.items()}
    original_group_counts = {group: len(members) for group, members in groups.items()}
    for grade in range(1, 6):
        mode_buckets = defaultdict(list)
        for group in groups:
            if group[0] == grade:
                mode_buckets[(group[3], group[2])].append(group)
        bucket_order = sorted(mode_buckets)
        topic_queues = {
            key: deque(sorted(mode_buckets[key], key=lambda g: (g[1], g[0])))
            for key in bucket_order
        }
        group_sequence = []
        while any(topic_queues.values()):
            for key in bucket_order:
                if topic_queues[key]:
                    group_sequence.append(topic_queues[key].popleft())
        per_grade[grade] = group_sequence
    grade_cursor = {grade: 0 for grade in range(1, 6)}

    schedule = []
    while any(member_queues.values()):
        for grade in range(1, 6):
            sequence = per_grade[grade]
            if not sequence:
                continue
            # One group visit per grade per round. Advance cyclically over the
            # prewoven behavior+mode/topic sequence, skipping exhausted groups.
            for offset in range(len(sequence)):
                pos = (grade_cursor[grade] + offset) % len(sequence)
                group = sequence[pos]
                if member_queues[group]:
                    schedule.append((group, member_queues[group].popleft()))
                    grade_cursor[grade] = (pos + 1) % len(sequence)
                    break

    selected = []
    for _, i in schedule:
        row = raw_rows[i]
        selected.append({
            "sample_id": row["sample_id"],
            "selected_index": i,
            "canonical_embedded_row_sha256": _sha(_canonical(row).encode("utf-8")),
            "assistant_target_sha256": _sha(row["messages"][-1]["content"].encode("utf-8")),
            "behavior": _behavior(row),
        })
    return {
        "schema": "MathVisionKid.balanced_training_plan.v2",
        "source_raw_sha256": source_sha.lower(),
        "seed": seed,
        "source_rows": len(raw_rows),
        "view_rows": len(schedule),
        "deduplicated_rows_in_view": len(raw_rows) - len(schedule),
        "source_rows_modified_or_deleted": 0,
        "sampling": "one pass; outer grade round robin; inner behavior+mode then topic/provenance round robin",
        "topic_fallback": "blank topics partition by case_group_id, then source_sample_id, then sample_id; provenance only",
        "duplicate_rule": "one canonical assistant-target representative per grade/topic-or-fallback/mode/behavior; source IDs retained in representative_provenance",
        "behavior_counts": dict(Counter(x["behavior"] for x in selected)),
        "group_counts": {"|".join(map(str, g)): original_group_counts[g] for g in sorted(groups)},
        "schedule": [raw_rows[i]["sample_id"] for _, i in schedule],
        "selected_rows": selected,
        "representative_provenance": provenance,
        "hash_note": "source_raw_sha256 binds original raw JSONL externally; canonical_embedded_row_sha256 hashes canonical parsed JSON, not original raw JSONL line bytes",
    }
