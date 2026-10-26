"""Train-only public calculation traces, with exact arithmetic and source provenance.

Arithmetic verification does not certify the semantics of the source solution.
Dataset Python/code is never run. Ambiguous numeric grounding is rejected.
"""
import argparse
import ast
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import unicodedata

NUMBER = re.compile(r"(?<![\w.,])\d+(?:[.,]\d+)*(?:\s*/\s*\d+)?(?![\w.,])")
UNITS = re.compile(r"(?:kg|g|km|cm|dm|mm|m|m²|cm²|m³|cm³|lít|phút|giờ|ngày|tuổi|đồng|VNĐ|VND|quả|cái|chiếc|con|bạn|học sinh|cuốn|quyển|hộp|bao|viên|trang|bút|bông|người|khách|cây|chai|thùng|bộ|bài|khóm|chậu|bức|tấm|ghế|bàn|phòng|túi|dãy|đội|sản phẩm|diễn viên|bưu ảnh)(?:\s+[A-Za-zÀ-ỹ]+){0,3}", re.I)
HLLJ_REV = "a26b53f14ef4c7708858b11beb29ad95bf9a8930"
AGENTIC_REV = "13190f41e5cdf298640d6001377ad6335fe42570"


class Rejected(ValueError):
    pass


def numeric(text):
    text = re.sub(r"\s+", "", text)
    if re.search(r"\d[.,]\d{3}(?:\D|$)", text) or text.count('.') > 1 or text.count(',') > 1:
        raise Rejected("AMBIGUOUS_NUMBER_LOCALE")
    return Fraction(text.replace(',', '.'))


def facts_from_question(question):
    facts = []
    for match in NUMBER.finditer(question):
        facts.append({"id": f"f{len(facts)}", "value": str(numeric(match[0])), "unit": None,
                      "quote": match[0], "span": [match.start(), match.end()]})
    if not 2 <= len(facts) <= 18:
        raise Rejected("FACT_COUNT")
    return facts


def exact(expression):
    expression = expression.strip()
    tree = ast.parse(expression, mode='eval')
    if sum(1 for _ in ast.walk(tree)) > 100:
        raise Rejected("EXPRESSION_SIZE")
    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return numeric(ast.get_source_segment(expression, node))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            return (-1 if isinstance(node.op, ast.USub) else 1) * visit(node.operand)
        if isinstance(node, ast.BinOp):
            a, b = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Add): return a+b
            if isinstance(node.op, ast.Sub): return a-b
            if isinstance(node.op, ast.Mult): return a*b
            if isinstance(node.op, ast.Div): return a/b
        raise Rejected("UNSUPPORTED_NUMERIC_EXPRESSION")
    return visit(tree.body)


def constant_reason(value, question):
    lower = question.lower()
    if value == 1 and ('/' in lower or 'phần' in lower): return 'fraction_complement_identity'
    if value == 2 and re.search(r'nửa|tam giác|hình thang', lower): return 'half_or_geometry_factor'
    if value == 60 and re.search(r'giờ|phút|giây', lower): return 'time_conversion_factor'
    if value == 100 and ('%' in lower or 'phần trăm' in lower or re.search(r'cm|centimet', lower)): return 'percent_or_centimetre_conversion_factor'
    if value == 1000 and re.search(r'kg|kilogam|km|ki.lô.mét|lít|m³|gam', lower): return 'metric_conversion_factor'
    return None


def normalized_numeric_line(line):
    line = re.sub(r'^\s*[-*]\s+', '', line.strip()).strip('`')
    if not re.match(r'^\d', line) or '=' not in line:
        return None
    if re.search(r'\bdư\b|\.\.\.|≈|~', line, re.I):
        raise Rejected('REMAINDER_OR_APPROXIMATE_TRACE')
    line = line.replace('×', '*').replace('÷', '/').replace('−', '-').replace('–', '-')
    line = re.sub(r'(?<=[\d)])\s*x\s*(?=[\d(])', '*', line)
    line = re.sub(r'(?<=[\d)])\s*:\s*(?=[\d(])', '/', line)
    match = re.fullmatch(r'([\d.,()\s+*/%=\-]+?)(?:\s*\(([A-Za-zÀ-ỹ²³ /]+)\)|\s+([A-Za-zÀ-ỹ²³ /]+))?\s*', line)
    if not match:
        raise Rejected('UNPARSED_CALCULATION_LINE')
    expression = match[1].strip()
    suffix = (match[2] or match[3] or '').strip().rstrip('.')
    if suffix and not UNITS.fullmatch(suffix):
        raise Rejected('UNSUPPORTED_RESULT_UNIT')
    # A right-hand percent without a left-hand fraction is a unit convention,
    # not a numeric equality; keep these outside this conservative importer.
    if '%' in expression.split('=')[-1]:
        raise Rejected('PERCENT_AS_RESULT_UNIT')
    for token in NUMBER.finditer(expression):
        numeric(token[0])
    expression = re.sub(r'(\d+(?:[.,]\d+)?)\s*%', r'(\1/100)', expression).replace(',', '.')
    return expression, suffix or None


def derive_trace(question, solution, expected, final_unit=None):
    facts = facts_from_question(question)
    by_value = {}
    for fact in facts:
        by_value.setdefault(Fraction(fact['value']), []).append(fact['id'])
    previous, constants, traces = {}, {}, []

    def ground(expression):
        # Python parses a*2/5 as (a*2)/5. Preserve the explicit literal
        # fraction so that a question quote "2/5" maps to its single fact.
        expression = re.sub(r'(?<![\w.])(\d+)\s*/\s*(\d+)(?![\w.])', r'(\1/\2)', expression.strip())
        tree = ast.parse(expression, mode='eval')
        def ref(value):
            candidates = set(by_value.get(value, []) + previous.get(value, []))
            if len(candidates) > 1: raise Rejected('AMBIGUOUS_FACT_OR_INTERMEDIATE')
            if candidates: return next(iter(candidates))
            reason = constant_reason(value, question)
            if reason:
                constants[str(value)] = reason
                return str(value)
            raise Rejected('NUMBER_NOT_GROUNDED_IN_QUESTION')
        def visit(node):
            if isinstance(node, ast.Constant) and type(node.value) in (int, float):
                return ref(numeric(ast.get_source_segment(expression, node)))
            # An explicit fraction in the source question is one fact.
            if (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)
                    and isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant)):
                value = exact(ast.get_source_segment(expression, node))
                if value in by_value: return ref(value)
            if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
                op = {ast.Add: '+', ast.Sub: '-', ast.Mult: '*', ast.Div: '/'}[type(node.op)]
                return '(' + visit(node.left) + op + visit(node.right) + ')'
            raise Rejected('UNSUPPORTED_GROUNDING_NODE')
        return visit(tree.body)

    for line in solution.splitlines():
        parsed = normalized_numeric_line(line)
        if not parsed: continue
        expression, result_unit = parsed
        pieces = [x.strip() for x in expression.split('=')]
        if len(pieces) < 2: continue
        values = [exact(piece) for piece in pieces]
        if len(set(values)) != 1:
            raise Rejected('EXACT_ARITHMETIC_MISMATCH')
        # Whole left side maps through earlier calculation results. The other
        # equal sides independently validate the stated computation.
        grounded = ground(pieces[0])
        previous.setdefault(values[0], [])
        if grounded not in previous[values[0]]: previous[values[0]].append(grounded)
        traces.append({'source_line': line, 'value': str(values[0]), 'expr': grounded, 'unit': result_unit})
    if not traces:
        raise Rejected('NO_EXPLICIT_CALCULATION_TRACE')
    if Fraction(traces[-1]['value']) != expected:
        raise Rejected('LAST_TRACE_NOT_SOURCE_FINAL_ANSWER')
    unit = final_unit or traces[-1]['unit']
    if not unit or not UNITS.fullmatch(unit):
        raise Rejected('NO_CLEAR_FINAL_UNIT')
    expression = traces[-1]['expr']
    replacements = {fact['id']: fact['value'] for fact in facts}
    substituted = re.sub(r'\bf\d+\b', lambda match: '('+replacements[match[0]]+')', expression)
    if exact(substituted) != expected:
        raise Rejected('INDEPENDENT_FINAL_RECOMPUTE_MISMATCH')
    return facts, {'status': 'solve', 'expr': expression, 'unit': unit}, traces, constants


def imported_record(source_row, source):
    if source == 'hllj/vi_math_problem_crawl':
        question, solution = source_row['question'], source_row['solution']
        final = re.findall(r'(?im)^\s*đáp số\s*:\s*(.+?)\s*$', solution)
        if len(final) != 1: raise Rejected('NO_SINGLE_FINAL_ANSWER')
        match = re.fullmatch(r'\s*(\d+(?:[.,]\d+)*(?:\s*/\s*\d+)?)\s+(.+?)\s*[.]?\s*', final[0])
        if not match: raise Rejected('NON_NUMERIC_FINAL_ANSWER')
        expected, final_unit = numeric(match[1]), match[2].strip().rstrip('.')
        group, revision = source_row['source_url'], HLLJ_REV
        provenance = {'grade': source_row['grade'], 'source_id': source_row['source_id'],
                      'source_url': group, 'source_title': source_row['source_title'],
                      'content_index': source_row['content_index'], 'block_index': source_row['block_index']}
    else:
        question, solution = source_row['question'], source_row['chain_of_thought']
        expected, final_unit = numeric(source_row['final_answer']), None
        group, revision = source_row['source_seed'], AGENTIC_REV
        provenance = {'source_id': source_row['id'], 'source_seed': group,
                      'source_verification_claim': source_row['verify'],
                      'source_verification_claim_independently_certified': False,
                      'grade': None, 'topic': source_row.get('topic')}
    if re.search(r'đáp\s*(?:số|án)|lời\s+giải|hướng\s+dẫn|(?m:^\s*(?:Giải|Bài giải)\s*:)', question, re.I):
        raise Rejected('SOLUTION_OR_ANSWER_MARKUP_IN_QUESTION')
    facts, target, trace, constants = derive_trace(question, solution, expected, final_unit)
    digest = hashlib.sha256((source+'\n'+question).encode('utf-8')).hexdigest()
    return {'sample_id': 'public_'+digest[:20], 'question': question, 'facts': facts,
            'target': target, 'expected_answer': str(expected), 'split': 'train',
            'split_group_id': source+':'+hashlib.sha256(group.encode('utf-8')).hexdigest()[:20],
            'provenance': dict(provenance, source_dataset=source, revision=revision,
                               dataset_url=f'https://huggingface.co/datasets/{source}/tree/{revision}',
                               declared_license='mit', label_source='source_annotation',
                               human_verified=False, semantic_correctness_verified=False,
                               arithmetic_verified=True, arithmetic_verification_scope='explicit trace and final expression only',
                               imported_solution=solution, calculation_trace=trace,
                               whitelisted_constants=constants, supplemental_training_only=True)}


def key(question):
    return ' '.join(unicodedata.normalize('NFC', question).casefold().split())


def build(source_root, output, max_samples=300):
    output.mkdir(parents=True, exist_ok=True)
    sources = [('hllj/vi_math_problem_crawl', source_root/'tech12h_strict_wordproblem_research_UNVERIFIED.jsonl'),
               ('vuongtsc/vi-gsm8k-agentic', source_root/'agentic_source_rows.jsonl')]
    accepted, rejected, counts, raw_fingerprints = [], [], {}, {}
    for source, path in sources:
        raw_fingerprints[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
        reasons = Counter()
        for row in rows:
            try:
                item = imported_record(row, source); accepted.append(item); reasons['TRACE_ACCEPTED'] += 1
            except (Rejected, ValueError, SyntaxError, ZeroDivisionError, KeyError) as error:
                reason = str(error) if isinstance(error, Rejected) else 'PARSE_ERROR'
                reasons[reason] += 1
                rejected.append({'source': source, 'id': row.get('id', row.get('source_id')), 'reason': reason})
        counts[source] = {'input_rows': len(rows), 'result_counts': dict(reasons)}
    accepted.sort(key=lambda row: hashlib.sha256(row['sample_id'].encode()).hexdigest())
    selected, seen, groups = [], set(), Counter()
    for row in accepted:
        skeleton = re.sub(r'\d+(?:[.,]\d+)?', '#', key(row['question']))
        if skeleton in seen: continue
        if groups[row['split_group_id']] >= 2: continue
        seen.add(skeleton); groups[row['split_group_id']] += 1; selected.append(row)
        if len(selected) >= max_samples: break
    with (output/'public_train_candidates.jsonl').open('w', encoding='utf-8', newline='\n') as stream:
        for row in selected: stream.write(json.dumps(row, ensure_ascii=False)+'\n')
    report = {'status': 'TRAIN_ONLY_SOURCE_IMPORTED_ARITHMETIC_TRACE_VERIFIED_SEMANTICS_UNCERTIFIED',
              'rows': len(selected), 'groups': len(groups), 'source_counts': dict(Counter(row['provenance']['source_dataset'] for row in selected)),
              'grade_counts': dict(Counter(str(row['provenance']['grade']) for row in selected)),
              'counts_before_caps': counts, 'raw_fingerprints': raw_fingerprints,
              'selected_file_sha256': hashlib.sha256((output/'public_train_candidates.jsonl').read_bytes()).hexdigest(),
              'rules': ['All supplemental samples train only; no public rows used for validation/test.',
                        'No LLM calls or execution of source Python.', 'Whole expression built from question facts and verified earlier calculation values.',
                        'Ambiguous numeric literals/grounding, missing units and approximate calculations rejected.',
                        'At most two rows per source page/seed; exact numeric-wording skeleton deduplicated.',
                        'Source prose not fed to the model; only question and facts are input.',
                        'Grade unspecified for agentic source, not claimed to be balanced grades1–5.',
                        'Arithmetic correctness does not verify semantic choice of operations or pedagogy.'],
              'rejections': rejected}
    (output/'public_train_provenance_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True); parser.add_argument('--max-samples', type=int, default=300)
    args = parser.parse_args(); result = build(args.source_root, args.output, args.max_samples)
    print(json.dumps({key: value for key, value in result.items() if key != 'rejections'}, ensure_ascii=True, indent=2))
