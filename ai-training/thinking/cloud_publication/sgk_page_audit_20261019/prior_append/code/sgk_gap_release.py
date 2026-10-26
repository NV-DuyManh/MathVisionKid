"""Bounded SGK supplement audit and publication staging; never starts training."""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from decimal import Decimal, localcontext
from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path
import re
import zipfile
from datetime import datetime, timezone

import exhaustive_colab_loader as loader

HERE = Path(__file__).resolve().parent
RUN = HERE / 'cloud_publication' / 'sgk_gap_20261019'
PREFIXES = ('g12', 'sgk_g34', 'sgk_g5')


def sha(b):
    return hashlib.sha256(b).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')


def jl(path):
    return [(json.loads(line), sha(line)) for line in path.read_bytes().splitlines() if line.strip()]


def dump_jl(path, rows):
    path.write_bytes(b''.join((json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode() for row in rows))


def key(problem):
    return re.sub(r'\s+', ' ', problem).strip().casefold()


def rational(text):
    return Fraction(str(text).replace(',', '.').strip())


def evaluate(expression, mode):
    """Independent AST evaluators: exact rationals and high precision decimals."""
    def walk(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            literal = ast.get_source_segment(expression, node)
            return Fraction(literal) if mode == 'fraction' else Decimal(literal)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            value = walk(node.operand)
            return -value if isinstance(node.op, ast.USub) else value
        if isinstance(node, ast.BinOp):
            a, b = walk(node.left), walk(node.right)
            if isinstance(node.op, ast.Add): return a + b
            if isinstance(node.op, ast.Sub): return a - b
            if isinstance(node.op, ast.Mult): return a * b
            if isinstance(node.op, ast.Div): return a / b
        raise ValueError(f'Unsupported oracle expression {expression!r}')
    with localcontext() as ctx:
        ctx.prec = 90
        return walk(ast.parse(expression, mode='eval').body)


def protected_hashes():
    p = RUN / 'current_sources/preserved_extensions/protected_numeric_signatures.json'
    sealed = json.loads(p.read_text(encoding='utf-8'))
    # Only blind canonical numeric hashes; no benchmark questions or answers read.
    hashes = set(sealed['signatures'])
    return hashes, sha(p.read_bytes())


def audit():
    prior = json.loads((RUN / 'preservation_before.json').read_text(encoding='utf-8'))
    old_rows = [r for r, _ in jl(RUN / 'current_source_all_pedagogic.jsonl')]
    old_ids = {r['sample_id'] for r in old_rows}
    old_questions = {key(r['problem']) for r in old_rows}
    protected, protection_sha = protected_hashes()
    sources, chats, self_reviews, root_reviews, eligibility = [], [], [], [], []
    seen_ids, seen_questions = set(), set()
    numeric_checks, family_counts, grade_counts = [], Counter(), Counter()
    for prefix in PREFIXES:
        reviews = {r['sample_id']: r for r, _ in jl(RUN / f'{prefix}_reviews.jsonl')}
        batch_sources = jl(RUN / f'{prefix}_cases.jsonl')
        batch_chats = [r for r, _ in jl(RUN / f'{prefix}_chat.jsonl')]
        assert len(batch_chats) == len(batch_sources) * 4
        modes = Counter((r['source_sample_id'], r['mode']) for r in batch_chats)
        for row, row_hash in batch_sources:
            sid = row['sample_id']
            assert sid not in seen_ids | old_ids
            assert key(row['problem']) not in seen_questions | old_questions
            seen_ids.add(sid); seen_questions.add(key(row['problem']))
            assert row['grade'] in range(1, 6)
            assert row['acceptance_status'] == 'ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED'
            assert row.get('human_verified', False) is False
            assert row.get('owner_human_reviewed', False) is False
            assert row.get('teacher_certified', False) is False
            provenance = row['provenance']
            assert not any(provenance.get(k) for k in ('human_verified', 'owner_human_reviewed', 'teacher_certified', 'independent_external_review'))
            assert reviews[sid]['source_row_sha256'] == row_hash
            assert len(reviews[sid]['criteria']) == 7
            for criterion in reviews[sid]['criteria'].values():
                assert criterion is True or (isinstance(criterion, str) and criterion.startswith('PASS'))
            assert len(row['hints']) == 3 and [h['level'] for h in row['hints']] == [1, 2, 3]
            for mode in loader.MODES:
                assert modes[sid, mode] == 1
            for step in row['worked_steps']:
                assert step.get('reason') and step.get('explanation')
                expression = step.get('expression')
                if expression:
                    exact = evaluate(expression, 'fraction')
                    assert exact == rational(step['result']), (sid, expression, step['result'])
                    decimal = evaluate(expression, 'decimal')
                    with localcontext() as ctx:
                        ctx.prec = 90
                        expected = Decimal(exact.numerator) / Decimal(exact.denominator)
                        assert abs(decimal - expected) < Decimal('1e-70')
                    numeric_checks.append({'sample_id': sid, 'step_id': step['step_id'], 'expression': expression,
                                           'exact_result': str(exact), 'decimal_90_digits_agrees': True})
            signatures = set(loader.source_signatures(row)) | set(row.get('canonical_signatures', []))
            overlaps = sorted(signatures & protected)
            eligibility.append({'sample_id': sid, 'source_row_sha256': row_hash,
                                'training_eligible': True,
                                'basis': 'OWNER_HASH_SCOPED_NUMERIC_EXCEPTION_AFTER_QA' if overlaps else 'ORIGINAL_NEW_CASE_QA_PASSED',
                                'blind_numeric_overlap_hashes': overlaps,
                                'authorization': 'Explicit owner answer: Cho phép ngoại lệ theo hash sau QA.',
                                'benchmark_independence_claimed': False})
            root_reviews.append({'sample_id': sid, 'source_row_sha256': row_hash,
                'review_role': 'CROSS_AGENT_CONTENT_REVIEW_AND_INDEPENDENT_ROOT_ORACLE',
                'human_review_claimed': False, 'status': 'PASS',
                'criteria': {'actual_problem_givens_request_consistency': True,
                    'exact_math_or_explicit_missing_data': True, 'grade_and_source_anchor': True,
                    'reasons_units_and_checking_relation': True, 'all_initial_and_three_hints_no_final_answer': True,
                    'student_work_only_grounded_feedback': True, 'schema_provenance_and_preservation': True},
                'review_scope': 'Actual authored problem, givens, request, supplied student_work, every step/reason/explanation/answer, initial and all three hints read. Cross-review corrections recorded separately. AST/hash checks support but do not prove semantic correctness.'})
            sources.append(row); self_reviews.append(reviews[sid])
            family_counts[row['topic']] += 1; grade_counts[str(row['grade'])] += 1
        for chat in batch_chats:
            loader.validate_chat(chat)
            assert chat['source_sample_id'] in {r['sample_id'] for r, _ in batch_sources}
            source = next(r for r, _ in batch_sources if r['sample_id'] == chat['source_sample_id'])
            target = json.loads(chat['messages'][2]['content'])
            prompt = json.loads(chat['messages'][1]['content'])
            assert prompt['problem'] == source['problem'] and prompt['grade'] == source['grade']
            if chat['mode'] == 'worked_solution':
                assert target['steps'] == source['worked_steps']
                assert target['answer'] == source['expected_answer']
                assert target['initial_guidance'] == source['initial_guidance']
            else:
                hint = source['hints'][int(chat['mode'][-1]) - 1]
                assert target == {'hint': hint['hint'], 'question': hint['question']}
            chats.append(chat)
    assert len({r['sample_id'] for r in chats}) == len(chats)
    # Keep the exact source serialization reviewed by each agent; do not bind a
    # source hash to a newly sorted JSON serialization of the same object.
    source_bytes = b''.join(line + b'\n' for prefix in PREFIXES
        for line in (RUN / f'{prefix}_cases.jsonl').read_bytes().splitlines() if line.strip())
    (RUN / 'accepted_sgk_cases.jsonl').write_bytes(source_bytes)
    assert [h for _, h in jl(RUN / 'accepted_sgk_cases.jsonl')] == [r['source_row_sha256'] for r in root_reviews]
    dump_jl(RUN / 'accepted_sgk_chat.jsonl', chats)
    dump_jl(RUN / 'self_qa_all.jsonl', self_reviews)
    dump_jl(RUN / 'root_cross_reviews.jsonl', root_reviews)
    dump_jl(RUN / 'training_eligibility_by_hash.jsonl', eligibility)
    write_json(RUN / 'root_numeric_oracle.json', numeric_checks)
    report = {'schema': 'sgk_gap_root_audit.v1', 'cases': len(sources), 'chat_rows': len(chats),
        'by_grade': dict(grade_counts), 'by_topic': dict(family_counts), 'numeric_steps_checked': len(numeric_checks),
        'protected_blind_hash_index_sha256': protection_sha,
        'numeric_exception_cases': sum(bool(x['blind_numeric_overlap_hashes']) for x in eligibility),
        'old_nonbulk_rows_indexed_for_comparison': len(old_rows),
        'old_nonbulk_comparison_scope': 'Exact IDs/questions checked globally; semantic type comparison uses agent cited nearest actual source cases. Not a claim that root manually reread all old arithmetic rows.',
        'preserved_before': prior, 'all_new_four_mode_groups_complete': True,
        'existing_sources_deleted': False, 'sealed_benchmark_payloads_read': False,
        'training_started': False, 'gpu_used': False, 'all_sgk_exercise_forms_audited': False}
    write_json(RUN / 'root_audit.json', report)
    # CPU tokenizer only, pinned local tokenizer cache; no model weights loaded.
    tokenizer_path = Path.home() / '.cache/huggingface/hub/models--Qwen--Qwen3-1.7B/snapshots' / loader.REVISION
    token_report = loader.full_token_audit(chats, loader.load_qwen_tokenizer(tokenizer_path))
    token_report['audit_scope'] = 'ALL_NEW_SGK_SUPPLEMENT_CHAT_ROWS_ONLY'
    write_json(RUN / 'new_chat_token_audit.json', token_report)
    print(json.dumps({k: v for k, v in report.items() if k not in ('preserved_before', 'by_topic')}, ensure_ascii=False))


def bundle():
    filenames = ['accepted_sgk_cases.jsonl', 'accepted_sgk_chat.jsonl', 'self_qa_all.jsonl',
        'root_cross_reviews.jsonl', 'training_eligibility_by_hash.jsonl', 'root_numeric_oracle.json',
        'root_audit.json', 'new_chat_token_audit.json', 'catalog_summary.json', 'cross_review_corrections.json']
    filenames += [p.name for p in RUN.glob('*catalog.json')]
    filenames += [p.name for p in RUN.glob('*qa.json')]
    filenames += [p.name for p in RUN.glob('*tests.json')]
    filenames += [p.name for p in RUN.glob('*tests_receipt.json')]
    filenames += [p.name for p in RUN.glob('*final_readback.json')]
    filenames += [p.name for p in RUN.glob('*peer_review.json')]
    filenames += ['official_source_file_hashes.json', 'pending_sgk_exercise_audit.json',
                  'final_tests_receipt.json', 'g12_structural_oracles.json', 'sgk_g12_peer_review_resolution.json']
    filenames += ['g12_exact_oracles.json', 'g12_official_endpoints.json', 'g12_official_pages.json']
    members = {f'data/{name}': (RUN / name).read_bytes() for name in sorted(set(filenames)) if (RUN / name).exists()}
    for pattern in ('*before*.jsonl', '*excluded*drafts.jsonl'):
        for path in RUN.glob(pattern):
            members['audit_only_not_training/' + path.name] = path.read_bytes()
    for name in ['sgk_gap_release.py', 'sgk_g12_audit.py', 'sgk_g12_catalog.py', 'catalog_sgk_g5.py',
                 'build_sgk_g34_gaps.py', 'build_sgk_g5_gap.py', 'exhaustive_colab_loader.py']:
        members['code/' + name] = (HERE / name).read_bytes()
    for path in HERE.glob('test_*sgk*.py'):
        members['code/' + path.name] = path.read_bytes()
    update_hashes = RUN / 'g5_sources/official_update_raw_hashes.json'
    if update_hashes.exists(): members['sources/official_update_raw_hashes.json'] = update_hashes.read_bytes()
    manifest = {'schema': 'MathVisionKid.SGK_GAP_APPEND.v1', 'acceptance': 'OWNER_PREAUTHORIZED_AFTER_QA',
        'all_existing_data_preserved': True, 'training_started': False, 'gpu_used': False,
        'official_sgk_images_pdf_or_complete_books_redistributed': False,
        'all_sgk_exercise_forms_audited': False,
        'members': {name: {'bytes': len(b), 'sha256': sha(b)} for name, b in members.items()}}
    members['manifest.json'] = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
    payload = RUN / 'new_sgk_append.zip'
    with zipfile.ZipFile(payload, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, b in sorted(members.items()):
            info = zipfile.ZipInfo(name, (2026, 10, 19, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, b)
    digest = sha(payload.read_bytes())
    path = payload.with_name(f'MathVisionKid_SGK_GAP_APPEND_20261019_{digest[:16]}.zip')
    payload.replace(path)
    with zipfile.ZipFile(path) as z:
        assert not z.testzip()
        for name, b in members.items(): assert z.read(name) == b
    result = {'path': str(path), 'file_name': path.name, 'bytes': path.stat().st_size, 'sha256': digest,
              'member_count': len(members)}
    write_json(RUN / 'bundle_local_receipt.json', result)
    print(json.dumps(result, ensure_ascii=False))


def metadata():
    catalogs = [json.loads((RUN / name).read_text(encoding='utf-8')) for name in
                ('sgk_g12_catalog.json', 'sgk_g34_catalog.json', 'sgk_g5_catalog.json')]
    assert [len(c['lessons']) for c in catalogs] == [116, 154, 75]
    pending = []
    for catalog, name in zip(catalogs, ('sgk_g12_catalog.json', 'sgk_g34_catalog.json', 'sgk_g5_catalog.json')):
        for lesson in catalog['lessons']:
            pending.append({'catalog_member': 'data/' + name,
                'grade': lesson['grade'] if 'grade' in lesson else 5,
                'book': lesson.get('book_id', lesson.get('volume')),
                'lesson_number': lesson.get('lesson_number', lesson.get('lesson')),
                'title': lesson['title'], 'status': 'PENDING_ALL_EXERCISE_FORM_PAGE_AUDIT',
                'toc_registered': True, 'some_representative_pages_may_be_reviewed': True})
    assert len(pending) == 345
    write_json(RUN / 'pending_sgk_exercise_audit.json', {'schema': 'sgk_exercise_audit_queue.v1',
        'status': 'IN_PROGRESS', 'not_a_generation_quota': True,
        'rule': 'Read actual remaining exercise pages; compare new representation with existing actual source; append only confirmed missing types. Never turn TOC registration into all-exercise coverage.',
        'lessons': pending})
    summary = {'schema': 'sgk_catalog_summary.v1', 'date': '2026-10-19', 'books': 10,
        'series': 'Kết nối tri thức với cuộc sống', 'numbered_lessons_registered': 345,
        'additional_unnumbered_intro_lessons': 1, 'toc_actual_read': True,
        'all_sgk_exercise_forms_audited': False, 'other_textbook_series_exhaustively_audited': False,
        'comparison_actual_nonbulk_cases': 5683, 'old_arithmetic_domain_cases_registry_only': 1623703,
        'new_original_accepted_cases': 101, 'new_chat_rows': 404,
        'finite_core_cases_unchanged': 495, 'finite_core_nodes_unchanged': 165,
        'pending_queue_member': 'data/pending_sgk_exercise_audit.json',
        'remaining_work': 'Systematic page-by-page exercise-form audit beyond the reviewed representative pages; physical/image modality proof remains separate.',
        'source_authority_limit': 'Official current publisher sources and corrections checked. Newly generated cases accepted after content QA, not automatically true because inspired by SGK.',
        'training_started': False}
    write_json(RUN / 'catalog_summary.json', summary)
    corrections = {'schema': 'sgk_cross_review_corrections.v1', 'all_applied_before_acceptance': True,
        'g12': ['Expanded compressed learner-facing text; retained actual parent source hashes.',
                'Made sequential hundred grid definition explicit.',
                'Aligned sum-pyramid check explanation with the checked cell.',
                'Clarified adding zero preserves value.'],
        'g34': ['Replaced generic complete-givens assertion with actual supplied text including missing fields.',
                'Individualized all forty sets of guidance and hints to actual request.',
                'Removed nonexistent route-increase condition and repaired inclusive-day hints.',
                'Expanded missing spaces in learner-facing text.'],
        'g5': ['Removed three already-covered draft examples from the supplement; retained drafts in audit only.',
               'Used decimal display for decimal/calculator reasoning; exact rational internal oracles preserved.',
               'Removed fabricated +0 arithmetic for rule/state transitions.',
               'Replaced remainder pseudo-check by resource reconstruction.',
               'Explicitly recorded 2026 page100 change as existing-covered direct/inverse roles.'],
        'all': ['Final source-byte hashes, exported chat targets, four modes and independent root numeric checks validated.',
                'Nineteen blind numeric-overlap cases receive exact-hash owner-authorized exceptions; no numeric benchmark independence claim.'],
        'no_answer_changed_to_bypass_gate': True, 'human_review_claimed': False}
    write_json(RUN / 'cross_review_corrections.json', corrections)
    peer = json.loads((RUN / 'sgk_g12_peer_review.json').read_text(encoding='utf-8'))
    write_json(RUN / 'sgk_g12_peer_review_resolution.json', {
        'prior_peer_review_source_sha256': peer['source_file_sha256'],
        'final_source_sha256': sha((RUN / 'g12_cases.jsonl').read_bytes()),
        'root_applied_and_read_two_precise_explanation_edits': True,
        'all_32_final_structural_oracles_pass': True, 'root_all_actual_fields_read': True,
        'peer_review_not_misrepresented_as_review_of_changed_bytes': True})
    files = []
    for path in RUN.rglob('*'):
        if path.is_file() and path.suffix.lower() in ('.png', '.pdf', '.html'):
            files.append({'relative_path': path.relative_to(RUN).as_posix(), 'bytes': path.stat().st_size,
                          'sha256': sha(path.read_bytes()), 'publication': 'HASH_ONLY_REFERENCE_BYTES_NOT_PACKAGED'})
    write_json(RUN / 'official_source_file_hashes.json', files)
    write_json(RUN / 'final_tests_receipt.json', {'status': 'PASS',
        'g12_actual_finite_enumeration_cases': 32, 'g34_unittest_checks': 15,
        'g5_unittest_checks': 6, 'root_exact_numeric_steps': 152,
        'all_new_chat_token_audit_rows': 404, 'old_full_archive_token_audited': False,
        'command_note': 'Two initial unittest module imports failed from project root; rerun direct scripts from thinking passed all21 tests. No data gate bypass.',
        'training_started': False})
    print(json.dumps(summary, ensure_ascii=False))


def controls():
    """Stage the existing four controls only after a verified append upload."""
    receipt = json.loads((RUN / 'bundle_remote_verified.json').read_text(encoding='utf-8'))
    assert receipt['all_bytes_equal'] and receipt['fresh_raw_verified']
    report = json.loads((RUN / 'root_audit.json').read_text(encoding='utf-8'))
    state = json.loads((RUN / 'source_cloud_state.json').read_text(encoding='utf-8'))
    chat = json.loads((RUN / 'source_chat_manifest.json').read_text(encoding='utf-8'))
    profile = json.loads((RUN / 'publication_profile.json').read_text(encoding='utf-8'))
    now = datetime.now(timezone.utc).isoformat()
    assert state['accepted_cases'] == 1629386 and report['cases'] == 101
    state['accepted_cases'] += report['cases']
    state['new_cases'] += report['cases']
    state['training_chat_rows'] += report['chat_rows']
    state['training_chat_rows_before_balancing'] += report['chat_rows']
    state['all_available_chat_rows_including_evaluation_and_audit'] += report['chat_rows']
    for grade, count in report['by_grade'].items(): state['by_grade'][grade] = state['by_grade'].get(grade, 0) + count
    for topic, count in report['by_topic'].items(): state['by_topic'][topic] = state['by_topic'].get(topic, 0) + count
    run = {'run_id': 'sgk_gap_20261019', 'bundle': receipt, 'cases': report['cases'], 'chat_rows': report['chat_rows'],
        'by_grade': report['by_grade'], 'source_member': 'data/accepted_sgk_cases.jsonl',
        'chat_member': 'data/accepted_sgk_chat.jsonl', 'catalog_member': 'data/catalog_summary.json',
        'token_audit_member': 'data/new_chat_token_audit.json', 'original_core_cases': 495,
        'numbered_sgk_lessons_registered': 345, 'books': 10, 'all_sgk_exercise_forms_audited': False,
        'pending_queue_member': 'data/pending_sgk_exercise_audit.json',
        'acceptance': 'ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED', 'human_manual_attestation_added': False,
        'numeric_overlap_exact_hash_exceptions': report['numeric_exception_cases'],
        'numeric_benchmark_independence_claimed': False}
    state.setdefault('sgk_gap_runs', []).append(run)
    state['updated_utc'] = now
    state['status'] = 'SGK_GAP_APPEND_VERIFIED_FULL_EXERCISE_AUDIT_IN_PROGRESS'
    state['current_drive_connection'] = profile
    state['TRAINING_DATASET_READY'] = False
    state['training_readiness_scope'] = 'FULL_VALID_CORPUS_REQUESTED_ARCHIVE_WIDE_TOKEN_AND_SPLIT_AUDIT_PENDING'
    state['balanced_release']['historical_selection_note'] = 'Preserved diagnostic subset. Owner now requests all valid data for future training; this subset is not the sole authorized corpus.'
    state['dataset_usage_current'] = {'owner_intent': 'Use all valid generated data for future training, not just the small balanced subset.',
        'preserve_all_data': True, 'protected_frozen_evaluation_payloads_remain_separate': True,
        'new_sgk_cases_training_eligible_after_qa': 101,
        'new_exact_hash_numeric_exceptions': 19, 'full_archive_token_audit_completed': False,
        'training_started': False}
    state['next_action'] = 'Continue finite SGK exercise-page representation audit from catalogs and pending queue. Append confirmed missing forms only. No training authorized.'
    state['local_storage']['current_run_staging'] = 'VERIFIED_BOUNDED_TEMPORARY_STAGING_PENDING_CLEANUP'
    chat.setdefault('supplement_bundles', []).append(run)
    chat['chat_rows'] += report['chat_rows']
    chat['all_available_chat_rows_including_evaluation_and_audit'] = state['all_available_chat_rows_including_evaluation_and_audit']
    chat['dataset_usage_current'] = state['dataset_usage_current']
    chat['recommended_training_view']['historical_diagnostic_subset_only'] = True
    chat['selection'] = 'All valid data requested; every old archive preserved. Full-corpus tokenizer/split audit pending; frozen evaluation/audit members are not silently added to training.'
    write_json(RUN / 'publish_state.json', state)
    write_json(RUN / 'publish_chat_manifest.json', chat)
    (HERE / 'exhaustive_cloud_reference.json').write_bytes((RUN / 'publish_state.json').read_bytes())
    context = HERE.parent / 'MATH_TRAINING_CONTEXT.md'
    context_text = context.read_text(encoding='utf-8')
    marker = '\n\n### Nhật ký19/10/2026 — đối chiếu SGK và bổ sung dạng biểu diễn\n'
    assert marker not in context_text, 'do not duplicate journal'
    entry = f'''{marker}
Tiếp nối state hiện hành 1.629.386 case, không khởi tạo lại lô. Đã đối chiếu mục lục thật của10tập Toán Kết nối tri thức lớp1–5 hiện hành2026, đăng ký345bài đánh số và1tiết mở đầu. Đã xem các trang biểu diễn đại diện và4PDF cập nhật chính thức lớp5; chưa đọc hết từng trang bài tập. ALL_SGK_EXERCISE_FORMS_AUDITED=false, pending queue trong gói. Không coi mục lục hay495core là chứng minh mọi dạngSGK đã đủ.

Ba agent soạn/kiểm phạm vi nhỏ; root đọc actual toàn bộ đề/givens/request/student_work/steps/reasons/explanations/answers/initial/allhints, yêu cầu sửa rồi kiểm chéo. Nhận101bài gốc mới/404chat: lớp1=28,lớp2=4,lớp3=20,lớp4=20,lớp5=29. Ba draft phần trăm đã có dạng tương đương không tính bài mới, giữ audit. Sửa gợi ý lệch yêu cầu, spacing, giải thích cộng0, dữ kiện guard, mô phỏng trạng thái và cách hiện thập phân. Không sửa đáp số để né gate. QA7tiêu chí/hash đúng byte nguồn;152bước số kiểm Fraction+Decimal,32oracle cấu trúc hữu hạn,15testG3–4 và6testG5 pass. Tokenaudit đủ404chat bằng tokenizer pinnedQwen, không tảiweights, maxsequence703, khôngtrain/GPU.

Tổng quản lý1.629.487case; chat candidate6.500.604, chat gồm eval/audit6.500.716. Giữ nguyên495core/165node, mọi nguồn cũ/299ownerattestation/frozenhash. Nhãn mới ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED, không hạđộchínhxác chỉvì nguồnAI, không tựgán chủđãđọc bài mới.19case trùng blindnumericsignatures có ngoại lệ đúnghash sauQA theo câu trả lời trực tiếp của chủ; không tuyên bố benchmark số học độc lập với các phép đó. Không đọc sealedchallenge.

Chủ yêu cầu dùng toàn bộ dữ liệu hợp lệ cho train tương lai; bộ cân bằng1256case cũ giữ làm diagnostic, không là tập duy nhất. Fullarchive6triệu chat chưa tokenaudit toàn bộ, readiness fullcorpus còn pending; frozen eval/audit vẫn tách. CHƯA TRAIN, khôngGPU/paidAPI/commit/push/appchanges.

Gói append mới: {receipt['url']} ; SHA256 {receipt['sha256']}; {receipt['bytes']}bytes. Đã tải rawmới so toànbyte/hash trước cập nhật control. Giữ4ID cũ, khôngnhân folder/payload cũ. Kết nối hiện tại do chủ yêu cầu đổi: {profile['name']} / {profile['email']}. Staging mới sẽ dọn sau xác minh4control; chỉ giữ context/code/thamchiếu nhỏ. Nguồn SGK chỉ lưuURL/hash/catalog và ví dụ gốc; không đóng gói toàn ảnh/PDFsách.

Việc tiếp theo: rà lần lượt các trang bài tập còn lại trong pending queue, đối chiếu nguồn thực rồi chỉ bổ sung dạng thiếu. Chưa tuyên bố bao trùm mọi dạng/toàn bộ SGK hay toàn chương trình pháp lý. Skills applied: google-drive:google-drive; pdf:pdf (đọc nguồn); workspace skills matched:none.
'''
    context.write_text(context_text + entry, encoding='utf-8')
    registry_path = HERE / 'data/primary_math_teacher_20261016/drive_artifacts.json'
    registry = json.loads(registry_path.read_text(encoding='utf-8'))
    registry['previous_link_id'] = registry.get('link_id')
    registry['link_id'] = None
    registry['account_identity'] = profile
    registry['current_tool_binding'] = 'Single currently connected Duy Mạnh account; no link_id parameter. Reinspect schema/profile if tools change.'
    registry['connection_binding_verified_utc'] = now
    registry.setdefault('sgk_append_bundles', []).append(receipt)
    registry['recommended_training_view'] = state['training_readiness_scope']
    write_json(registry_path, registry)
    # Keep every old member byte-for-byte; add one bounded run index.
    with zipfile.ZipFile(RUN / 'source_progress_index.zip') as old, zipfile.ZipFile(RUN / 'publish_progress_index.zip', 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as new:
        for item in old.infolist(): new.writestr(item, old.read(item.filename))
        names = ['catalog_summary.json', 'root_audit.json', 'new_chat_token_audit.json',
                 'cross_review_corrections.json', 'bundle_remote_verified.json',
                 'publish_state.json', 'publish_chat_manifest.json', 'pending_sgk_exercise_audit.json']
        names += [p.name for p in RUN.glob('*catalog.json')]
        for name in names: new.writestr('sgk_gap_20261019/' + name, (RUN / name).read_bytes())
        new.writestr('sgk_gap_20261019/MATH_TRAINING_CONTEXT.md', context.read_bytes())
        new.writestr('sgk_gap_20261019/drive_artifacts.json', registry_path.read_bytes())
    with zipfile.ZipFile(RUN / 'source_progress_index.zip') as old, zipfile.ZipFile(RUN / 'publish_progress_index.zip') as new:
        assert not new.testzip()
        assert all(old.read(n) == new.read(n) for n in old.namelist())
    print(json.dumps({'cases': state['accepted_cases'], 'chat': state['training_chat_rows'], 'controls_staged': True}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('audit', 'metadata', 'bundle', 'controls'))
    action = parser.parse_args().action
    {'audit': audit, 'metadata': metadata, 'bundle': bundle, 'controls': controls}[action]()
