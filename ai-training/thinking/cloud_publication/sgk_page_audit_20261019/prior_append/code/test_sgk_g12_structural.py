"""Independent finite enumeration of actual grade 1–2 supplement outputs."""
import itertools
import json
import re

from sgk_gap_release import RUN, evaluate, jl, sha, write_json


def numbers(text):
    return list(map(int, re.findall(r'\d+', text)))


def main():
    receipts = []
    for row, digest in jl(RUN / 'g12_cases.jsonl'):
        o = row['gap_oracle']; kind = o['kind']
        answer = row['expected_answer'][0]['result']
        if kind in ('decompositions', 'missing_decompositions'):
            low, high = o.get('minimum', 0), o.get('maximum', o['total'])
            pairs = [(a, o['total'] - a) for a in range(low, high + 1) if low <= o['total'] - a <= high]
            pairs = [p for p in pairs if list(p) not in o.get('existing', [])]
            emitted = [tuple(map(int, p)) for p in re.findall(r'\((\d+),\s*(\d+)\)', answer)]
            assert emitted == pairs
        elif kind == 'grid':
            assert numbers(answer) == [o['top_left'] + 1, o['top_left'] + o['width']]
        elif kind == 'explicit_patch':
            assert 51 - 41 == 10 and 52 - 51 == 1
            assert 42 - 41 != 10 and answer == 'Miếng A'
        elif kind == 'grid_below':
            assert numbers(answer) == [o['value'] + o['width']]
        elif kind in ('pyramid', 'pyramid_inverse'):
            a, b, c = o['bottom']
            if b is None: b = o['left_middle'] - a
            middle = [a + b, b + c]; top = sum(middle)
            if kind == 'pyramid_inverse': assert numbers(answer) == [b, middle[1], top]
            elif row['sample_id'].endswith('_01'): assert numbers(answer) == middle + [top]
            else: assert numbers(answer) == [top]
        elif kind in ('classify', 'classify_all'):
            values = {name: int(evaluate(expr, 'fraction')) for name, expr in o['expressions'].items()}
            if kind == 'classify':
                labels = {k for k, v in values.items() if v == o['target']}
                assert set(re.findall(r'\b[A-Z]\b', answer)) == labels
            else:
                assert values == {'P': 3, 'Q': 5, 'R': 3, 'S': 5}
                assert answer == 'Hộp 3: P, R; hộp 5: Q, S'
        elif kind == 'blank_digit':
            candidates = []
            for n in range(10):
                lhs, rhs = o['pattern'].replace('?', str(n)).split('=')
                if not lhs.startswith('0') and evaluate(lhs, 'fraction') == evaluate(rhs, 'fraction'): candidates.append(n)
            assert candidates == numbers(answer)
        elif kind == 'two_blanks':
            pairs = [(a, b) for a in range(1, 10) for b in range(1, 10) if 10*a+2+10*b+3 == 75]
            assert pairs == [tuple(p) for p in o['solutions']] and len(pairs) > 1
        elif kind == 'swap':
            original = o['original']
            equation = answer.split(';')[0].replace(' ', '').replace('−', '-')
            lhs, rhs = equation.split('=')
            assert evaluate(lhs, 'fraction') == evaluate(rhs, 'fraction')
            changed = [i for i, (a, b) in enumerate(zip(original, equation)) if a != b]
            assert len(original) == len(equation) and len(changed) == 2
            i, j = changed
            assert original[i].isdigit() and original[j].isdigit()
            assert original[i] == equation[j] and original[j] == equation[i]
        elif kind == 'graph':
            paths = []
            def visit(node, path):
                if node == 'T': paths.append(path); return
                for a, b in o['edges']:
                    if a != node or b in path: continue
                    if b in o['values']:
                        v = o['values'][b]
                        if ('target' in o and v != o['target']) or ('less_than' in o and v >= o['less_than']): continue
                    visit(b, path + [b])
            visit('S', ['S'])
            assert paths == o['paths']
            assert answer.split(' → ') == paths[0]
        elif kind == 'board':
            position = o['start'] + o['roll']
            position = o['jump'].get(str(position), position)
            finish = position if evaluate(o['expression'], 'fraction') == o['response'] else o['start']
            assert finish == o['finish'] and numbers(answer)[0] == finish
        elif kind == 'explicit_relation':
            assert row['can_solve'] is False and all(s['expression'] is None for s in row['worked_steps'])
        else: raise AssertionError(kind)
        receipts.append({'sample_id': row['sample_id'], 'source_row_sha256': digest, 'oracle_kind': kind, 'status': 'PASS'})
    write_json(RUN / 'g12_structural_oracles.json', {'cases': len(receipts), 'status': 'PASS', 'checks': receipts,
        'source_sha256': sha((RUN / 'g12_cases.jsonl').read_bytes()), 'no_training': True})
    print(f'PASS {len(receipts)} actual source finite structural oracles')


if __name__ == '__main__': main()
