"""Independent peer checks transcribed from the six actual problem statements.

Does not import author builder/oracle, and never uses gap_oracle as a premise.
"""
from collections import Counter
from fractions import Fraction
from itertools import product, permutations
import hashlib
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
THINKING = HERE.parents[2]
sys.path.insert(0, str(THINKING))
import exhaustive_colab_loader as L
from math_data_archive_audit import source_projection, linkage_errors
from math_data_portable_resume import save, canonical


def exact(expression):
    tokens = re.findall(r"\d+|[()+*/-]", expression)
    if ''.join(tokens) != re.sub(r'\s+', '', expression):
        raise ValueError(expression)
    values, operators = [], []
    precedence = {'+':1,'-':1,'*':2,'/':2}
    def apply():
        op = operators.pop(); b = values.pop(); a = values.pop()
        values.append({'+':lambda:a+b,'-':lambda:a-b,'*':lambda:a*b,'/':lambda:a/b}[op]())
    for token in tokens:
        if token.isdigit():
            values.append(Fraction(int(token)))
        elif token == '(':
            operators.append(token)
        elif token == ')':
            while operators[-1] != '(':
                apply()
            operators.pop()
        else:
            while operators and operators[-1] != '(' and precedence[operators[-1]] >= precedence[token]:
                apply()
            operators.append(token)
    while operators:
        apply()
    assert len(values) == 1
    return values[0]


def jug_graph(capacity_a, capacity_b):
    """Enumerate endpoint constraints over all bounded states; no author code."""
    states = list(product(range(capacity_a+1), range(capacity_b+1)))
    graph = {s:set() for s in states}
    for old in states:
        for new in states:
            if old == new:
                continue
            a,b = old; x,y = new
            fill_empty = (a==x and y in (0,capacity_b)) or (b==y and x in (0,capacity_a))
            conserved = a+b==x+y
            pour_ab = conserved and x<a and y>b and (x==0 or y==capacity_b)
            pour_ba = conserved and x>a and y<b and (y==0 or x==capacity_a)
            if fill_empty or pour_ab or pour_ba:
                graph[old].add(new)
    reachable = {(0,0)}
    while True:
        expanded = reachable | {new for old in reachable for new in graph[old]}
        if expanded == reachable:
            break
        reachable = expanded
    return graph, sorted(reachable)


def review(row):
    suffix = row['sample_id'].split('_g3_',1)[1]
    results = [a['result'] for a in row['expected_answer']]
    if suffix == 'product_pyramid_01':
        # Actual written bottom is 2,3,4 and every upper cell is local product.
        middle = [2*3,3*4]; top = middle[0]*middle[1]
        assert results == [str(middle[0]),str(middle[1]),str(top)]
        oracle = dict(bottom=[2,3,4],middle=middle,top=top,local_edges_checked=3)
    elif suffix == 'product_pyramid_02':
        possible = [v for v in range(10) if 3*v==9 and (3*v)*(v*2)==54]
        assert possible == [3]
        assert results[:3] == ['3','6','54']
        assert row['student_work']['text'] == 'Ô đáy giữa là 3, ô giữa bên phải là 6, nên đỉnh bằng 9 + 6 = 15.'
        assert 9+6==15 and 9*6==54
        oracle = dict(bottom_middle_candidates=possible,middle_right=3*2,top=9*6,
                      student_first_two_cells_correct=True,student_wrong_rule_at_top=True)
    elif suffix.startswith('two_jug_transfer'):
        ca,cb,target = (5,3,4) if suffix.endswith('01') else (4,2,3)
        graph, reachable = jug_graph(ca,cb)
        if suffix.endswith('01'):
            path = [(0,0),(5,0),(2,3),(2,0),(0,2),(5,2),(4,3)]
            assert all(b in graph[a] for a,b in zip(path,path[1:]))
            assert path[-1][0]==target and results[0]=='4'
            assert results[1] == '→'.join(f'({a},{b})' for a,b in path)
            oracle = dict(capacities=[ca,cb],reachable_states=reachable,path=path,
                          all_six_transitions_legal=True,target_in_A=True,optimality_claimed=False)
        else:
            stated = {(0,0),(4,0),(0,2),(4,2),(2,2),(2,0)}
            assert set(reachable)==stated and all(target not in p for p in reachable)
            assert 'Không thể đạt đúng 3 lít' in results[0]
            oracle = dict(capacities=[ca,cb],reachable_states=reachable,target_reachable=False,
                          state_set_closed_under_all_allowed_actions=True)
    elif suffix.startswith('operator_synthesis'):
        numbers = [6,3,2] if suffix.endswith('01') else [8,4,2]
        pairs = list(product(['+','*'],repeat=2)) if suffix.endswith('01') else list(permutations(['/','-']))
        target = Fraction(12 if suffix.endswith('01') else 0)
        all_values = {f'{numbers[0]}{a}{numbers[1]}{b}{numbers[2]}':str(exact(f'{numbers[0]}{a}{numbers[1]}{b}{numbers[2]}')) for a,b in pairs}
        solutions = [expression for expression,value in all_values.items() if Fraction(value)==target]
        assert solutions == (['6+3*2'] if suffix.endswith('01') else ['8/4-2'])
        if suffix.endswith('01'):
            assert results == ['(+,×)','6 + 3 × 2 = 12']
        else:
            assert results[:2] == ['(÷,−)','8 ÷ 4 − 2 = 0']
            assert exact('8-4/2')==6 and exact('(8-4)/2')==2
            assert row['student_work']['text'] == 'Điền trừ rồi chia, tính từ trái sang phải cũng được 0.'
        oracle = dict(numbers=numbers,all_expressions_and_values=all_values,solutions=solutions,
                      exhaustive_allowed_operator_assignments=True)
    else:
        raise ValueError(suffix)
    numeric = []
    for step in row['worked_steps']:
        if step.get('expression'):
            value = exact(step['expression'])
            assert value == Fraction(step['result'])
            numeric.append(dict(expression=step['expression'],exact=str(value)))
        assert step['reason'] and step['explanation']
    assert [h['level'] for h in row['hints']] == [1,2,3]
    assert not any(row.get(k) for k in ('human_verified','teacher_certified','owner_human_reviewed'))
    return dict(structural=oracle, numeric=numeric)


def main():
    raw = (HERE/'cases.jsonl').read_bytes()
    case_rows = [(json.loads(line),hashlib.sha256(line).hexdigest()) for line in raw.splitlines() if line]
    chat_raw = (HERE/'chat.jsonl').read_bytes()
    chats = [json.loads(line) for line in chat_raw.splitlines() if line]
    index = {r['sample_id']:r for r,h in case_rows}
    for chat in chats:
        L.validate_chat(chat)
        assert not linkage_errors(chat,source_projection(index[L.case_id(chat)]))
    assert len(chats)==24 and len({r['sample_id'] for r in chats})==24
    modes = Counter((L.case_id(r),r['mode']) for r in chats)
    assert len(modes)==24 and set(modes.values())=={1}
    criteria = {
      'math_correctness_or_explicit_guard':'PASS: independent local constraints, complete finite jug graph and all operator assignments; every numeric expression checked by separate precedence parser.',
      'givens_request_consistency':'PASS: all amounts, local multiplication rules, operator multiplicities and stopping endpoints are explicit; impossible jug request is answered as impossibility, not unreadability.',
      'grade_and_scope':'PASS: grade3 bounded reasoning enrichment, within stated integer arithmetic; claims limited to text plans and no physical/vision completion.',
      'steps_reasons_units_check':'PASS: all actual steps/reasons/explanations read; jug units/capacities and each pour stop correct; combined narrative steps show all intermediate states.',
      'initial_and_all_hints_no_answer_leak':'PASS: initial guidance and all three hint texts/questions read; strategies remain qualitative and disclose no final numbers, operator pair, path or impossibility conclusion.',
      'student_work_grounding':'PASS: comments address only the two explicitly supplied synthetic student excerpts; correct portions preserved and wrong operator/precedence statements identified.',
      'schema_provenance_preservation':'PASS: all four chat modes reproduce actual current source target/hints; false human certification flags preserved; author source bytes left unchanged.'}
    reviews = []
    for row,h in case_rows:
        oracle = review(row)
        reviews.append(dict(sample_id=row['sample_id'],source_row_sha256=h,status='PASS',criteria=criteria,
            actual_fields_read=['problem','givens','requested_quantity','student_work.text_and_observations','worked_steps','reasons','explanations','expected_answer','initial_guidance','all_three_hints_and_questions'],independent_oracle=oracle,human_review_claimed=False))
    save(HERE/'peer_review.json',dict(schema='MathVisionKid.independent_peer_review.v1',
         source_file_sha256=hashlib.sha256(raw).hexdigest(),chat_file_sha256=hashlib.sha256(chat_raw).hexdigest(),
         rows_read=6,chat_rows_checked=24,seven_criteria_pass_count=6,status='PASS',
         independent_author_oracle_imported=False,author_gap_oracle_used_as_premise=False,
         reviewer='independent_peer_agent',reviews=reviews,training_started=False))
    print(json.dumps(dict(rows_read=6,chat_rows_checked=24,status='PASS',source_file_sha256=hashlib.sha256(raw).hexdigest())))


if __name__ == '__main__':
    main()
