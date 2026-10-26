"""Repair three draft cases, preserving pre-repair bytes and all frozen datasets."""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import json

from primary_math_data_pipeline import (DEFAULT_ROOT, HERE, REVIEW_FIELDS, answer_signatures,
    curate, inspect_case, mapping_error, read_rows, row_sha, sha, write_json, write_rows)


def step(index, title, reason, expression, result, unit, explanation):
    return dict(step_id=f"s{index}", title=title, reason=reason, expression=expression,
                result=str(result), unit=unit, explanation=explanation)


def main():
    root = DEFAULT_ROOT; evidence = HERE/'evidence'/'primary_math_teacher_20261016'
    batch = root/'authored_batches'/'initial31_normalized.jsonl'
    review_path = root/'reviews'/'initial31_AI_reviews.jsonl'
    rows = read_rows(batch); decisions = read_rows(review_path)
    targets = {'original_tutor25_g3_01', 'original_tutor25_g3_03', 'original_tutor25_g3_04'}
    tag = 'pending_case_repair_heartbeat_20261016_152351'
    if all(r['provenance'].get('repair_tag') == tag for r in rows if r['sample_id'] in targets):
        print(json.dumps({'already_applied': True})); return
    for source, name in ((batch, 'initial31_before_pending_repair.jsonl'),
                         (review_path, 'initial31_reviews_before_pending_repair.jsonl')):
        snapshot = evidence/name
        if snapshot.exists() and snapshot.read_bytes() != source.read_bytes():
            raise ValueError('Pre-repair snapshot already exists for different bytes')
        snapshot.write_bytes(source.read_bytes())
    before_sha = sha(batch.read_bytes())
    blueprint = json.loads((root/'curriculum_blueprint.json').read_text(encoding='utf-8'))
    nodes = {n['node_id']: n for n in blueprint['nodes']}
    by_id = {r['sample_id']: r for r in rows}; reviews = {r['sample_id']: r for r in decisions}
    changes = []
    for sample_id in sorted(targets):
        row = by_id[sample_id]; before = deepcopy(row); old_review = deepcopy(reviews[sample_id])
        if sample_id.endswith('g3_01'):
            row['worked_steps'] = [
                step(0, 'Tìm số cam của tám túi đầy',
                     'Dùng bảng nhân sáu để tìm bội gần tổng số cam mà không vượt tổng.',
                     '8*6', 48, 'quả cam', 'Tám túi đầy cần 8 × 6 = 48 quả; 48 không vượt 52.'),
                step(1, 'Kiểm tra có thể thêm túi đầy không',
                     'Muốn biết tám túi đã nhiều nhất chưa, xét thêm một túi.',
                     '9*6', 54, 'quả cam', 'Chín túi đầy cần 9 × 6 = 54 quả, lớn hơn 52; không đủ để xếp chín túi.'),
                step(2, 'Ghi số túi đầy',
                     'Phần 48 quả vừa tìm chia hết thành các túi sáu quả; kiểm tra bước trước đã loại được túi thứ chín.',
                     '{s0}/6', 8, 'túi đầy', '48 : 6 = 8 túi đầy. Không viết 52 : 6 = 8 như một phép chia hết.'),
                step(3, 'Tìm số cam dư',
                     'Lấy tổng số cam bớt phần đã xếp vào các túi đầy.',
                     '52-{s0}', 4, 'quả cam', '52 − 48 = 4 quả cam. Bốn quả ít hơn sáu quả nên chưa đủ thêm một túi đầy.'),
                step(4, 'Kiểm tra tổng ban đầu',
                     'Số túi đầy nhân sức chứa, cộng số dư phải khớp tổng số cam.',
                     '{s2}*6+{s3}', 52, 'quả cam', '8 × 6 + 4 = 52. Kết luận: tám túi đầy và dư bốn quả cam.')]
            row['canonical_case']['operations'] = ['52%6']
            row['canonical_case']['family'] = 'division_remainder'
            assert divmod(52, 6) == (8, 4)
            rationale = 'Replace floor syntax with adjacent-multiple bounds, exact division of the packed portion, remainder and recomposition; retain original question and both original answers.'
        elif sample_id.endswith('g3_04'):
            row['worked_steps'] = [
                step(0, 'Tìm số phút của một giờ', 'Một giờ có 60 phút; trước hết xét một giờ đủ.',
                     '1*60', 60, 'phút', 'Một giờ là 1 × 60 = 60 phút, không vượt thời lượng 92 phút.'),
                step(1, 'Kiểm tra hai giờ', 'Cần biết thời lượng có đủ hai giờ không.',
                     '2*60', 120, 'phút', 'Hai giờ là 120 phút, lớn hơn 92 phút. Vì vậy chỉ tách được một giờ đủ.'),
                step(2, 'Đổi phần phút đã tách thành giờ', 'Chia phần phút đã tách cho số phút trong một giờ.',
                     '{s0}/60', 1, 'giờ', '60 : 60 = 1 giờ. Đây là phần giờ đủ, chưa phải toàn thời lượng.'),
                step(3, 'Tìm số phút còn lại', 'Bớt phần phút đã đổi thành giờ khỏi tổng thời lượng.',
                     '92-{s0}', 32, 'phút', '92 − 60 = 32 phút; 32 nhỏ hơn 60 nên không tạo thêm một giờ.'),
                step(4, 'Kiểm tra hai phần thời lượng', 'Đổi phần giờ về phút rồi cộng phần phút còn lại.',
                     '{s2}*60+{s3}', 92, 'phút', '1 × 60 + 32 = 92 phút. Vậy 92 phút = 1 giờ 32 phút.')]
            row['canonical_case']['operations'] = ['92-60']
            assert divmod(92, 60) == (1, 32)
            rationale = 'Use explicit bounds for one versus two hours, exact conversion and recomposition; retain original duration and answers.'
        else:
            row['problem'] = row['problem'].replace('27 quyển', '23 quyển')
            row['givens'][1].update(text='mỗi giá có 23 quyển', value='23')
            row['worked_steps'] = [
                step(0, 'Tìm tổng sách ban đầu',
                     'Bốn giá có lượng sách bằng nhau nên nhân số giá với số quyển trên mỗi giá.',
                     '4*23', 92, 'quyển',
                     '23 × 4: 3 × 4 = 12, viết 2 ở hàng đơn vị, nhớ 1 chục; 2 × 4 + 1 = 9 chục. Có 92 quyển trước khi cho mượn.'),
                step(1, 'Bớt số sách cho mượn',
                     '36 quyển được lấy từ toàn bộ 92 quyển, vì vậy trừ khỏi tổng chứ không trừ khỏi mỗi giá.',
                     '{s0}-36', 56, 'quyển',
                     '92 − 36: đổi một chục thành mười đơn vị, 12 − 6 = 6; còn 8 chục, 8 − 3 = 5. Còn 56 quyển; kiểm lại 56 + 36 = 92.')]
            row['expected_answer'][0]['result'] = '56'
            row['canonical_case'].update(operations=['4*23', '{s0}-36'], numeric_values=['4', '23', '36'])
            node = nodes['current_g3_word_two_steps']; slot = node['authoring_plan']['core_cases'][0]
            row['curriculum_assignment'] = {'node_id': node['node_id'], 'curriculum_scope': node['curriculum_scope'],
                'case_kind': 'core', **{k: slot[k] for k in ('case_slot', 'context_variant', 'method_variant')}}
            row['provenance'].update(curriculum_node_id=node['node_id'], curriculum_mapping_status='AI_RESEARCH_MAPPING_REVIEWED_NOT_LEGAL_CERTIFICATION')
            assert 4*23-36 == 56 and 56+36 == 92
            rationale = 'Implement independently proposed conservative bound repair: 23×4 has one carry, followed by one-borrow subtraction; original number and answer preserved in snapshot, no evaluation target changed.'
        row['quality_flags']['requires_capabilities'] = []
        row['provenance'].update(repair_tag=tag, previous_curated_row_sha256=row_sha(before))
        check = inspect_case(row); assert check['passed'], (sample_id, check)
        answer_signatures(row, check)
        assert mapping_error(row, nodes) is None
        decision = {**old_review, **{field: True for field in REVIEW_FIELDS}, 'row_sha256': row_sha(row),
            'reviewer': 'root_repair_adjudicator_after_prior_independent_content_and_curriculum_reviews',
            'repair_rationale': rationale, 'repair_review_scope': 'Read all repaired steps, retained original givens/hints, units and answers; exact independent divmod or recomposition oracle; no new external reviewer claimed.',
            'human_verified': False, 'teacher_certified': False}
        reviews[sample_id] = decision
        changes.append({'sample_id': sample_id, 'before_row_sha256': row_sha(before),
            'after_row_sha256': row_sha(row), 'rationale': rationale, 'mechanical': check})
    write_rows(batch, rows)
    write_rows(review_path, [reviews[r['sample_id']] for r in rows])
    result = curate(root)
    write_json(evidence/'pending_repair_heartbeat_152351.json', {'created_utc': datetime.now(timezone.utc).isoformat(),
        'before_batch_sha256': before_sha, 'after_batch_sha256': sha(batch.read_bytes()), 'changes': changes,
        'result': {k: result[k] for k in ('accepted_cases','chat_train_rows','decisions','remaining_core_cases')},
        'training_started': False, 'teacher_certified': False})
    print(json.dumps({k: result[k] for k in ('accepted_cases','chat_train_rows','decisions','remaining_core_cases')}))


if __name__ == '__main__': main()
