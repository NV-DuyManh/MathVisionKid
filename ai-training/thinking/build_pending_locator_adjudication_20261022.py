"""Restore exact existing locator provenance; no data authoring or publication."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
OLD = HERE / 'cloud_publication/sgk_page_audit_20261019'
QUEUE = HERE / 'cloud_publication/sgk_final_gaps_20261021/reconciliation/next_uncovered_tasks.json'
MAPPING = HERE / 'cloud_publication/sgk_finish_20261020/crossgrade_mapping/build_mapping.py'
DEST = HERE / 'cloud_publication/data_resume_20261022/locator_adjudication.json'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def main():
    inputs = [QUEUE, MAPPING, OLD / 'g3_spatial_append/adjudication.json',
              OLD / 'g2v1_audit/page_review.jsonl', OLD / 'g2v1_audit/pages.json',
              OLD / 'g3_audit/candidate_adjudication.json',
              OLD / 'g3_audit/page_review.jsonl', OLD / 'g3_audit/summary.json']
    pins = {str(path.relative_to(HERE)): sha(path.read_bytes()) for path in inputs}
    queue = read(QUEUE)
    tasks = {task['master_id']: task for task in queue['global_master_tasks']}
    assert set(tasks) == {'collinear_triple_complete_enumeration', 'placeclass_torn_strip_constraints'}
    spatial = read(OLD / 'g3_spatial_append/adjudication.json')
    aliases = spatial['cross_grade_merges']
    alias_index = next(i for i, row in enumerate(aliases) if row['canonical_form'] == 'collinear_enumeration_and_segment_pairs')
    alias = aliases[alias_index]
    receipts = []
    for line_number, line in enumerate((OLD / 'g2v1_audit/page_review.jsonl').read_bytes().splitlines(), 1):
        obj = json.loads(line)
        for source in alias['sources']:
            if (obj['book_id'], obj.get('printed_page')) == (source['book_id'], source['printed_page']):
                assert obj['image_sha256'] == source['source_image_sha256']
                assert obj['image_url'] == source['image_url']
                assert obj['actual_visual_page_read'] and obj['printed_footer_verified']
                assert obj['grade'] == 2 and obj['volume'] == 1
                receipts.append({
                    **source, 'grade': 2, 'volume': 1,
                    'book_title_from_existing_publisher_metadata': 'SGK Toán 2 Tập Một',
                    'book_series': None,
                    'reader_url': read(OLD / 'g2v1_audit/pages.json')['reader_urls'][0],
                    'receipt_file': 'sgk_page_audit_20261019/g2v1_audit/page_review.jsonl',
                    'receipt_line': line_number, 'receipt_raw_row_sha256': sha(line),
                    'prior_actual_page_read': True, 'printed_footer_verified_in_prior_receipt': True,
                    'prior_exercise_types': obj['exercise_types'],
                    'fresh_page_image_downloaded_or_visually_read_this_task': False,
                })
    assert len(receipts) == len(alias['sources']) == 7
    assert {r['printed_page'] for r in receipts} == {98, 99, 100, 101, 110, 111, 130}
    assert 'collinear_segment_all_pairs' in next(r for r in receipts if r['printed_page'] == 110)['prior_exercise_types']
    assert 'collinear_triples' in next(r for r in receipts if r['printed_page'] == 101)['prior_exercise_types']
    mapping_text = MAPPING.read_text(encoding='utf8')
    assert "if pr['book_id'].startswith('g3'):" in mapping_text
    candidates = read(OLD / 'g3_audit/candidate_adjudication.json')
    candidates = candidates if isinstance(candidates, list) else next(candidates[k] for k in ('candidates', 'adjudications') if k in candidates)
    torn = next(row for row in candidates if row['candidate_id'] == 'tornplaceclass_strip_assembly')
    assert torn['status'] == 'UNRESOLVED_LOCATOR_REQUIRED' and torn['actual_page_receipts'] == []
    g3_rows = [json.loads(line) for line in (OLD / 'g3_audit/page_review.jsonl').read_bytes().splitlines()]
    exact_torn_gap_rows = [row for row in g3_rows if 'tornplaceclass_strip_assembly' in row.get('gap_ids', [])]
    assert exact_torn_gap_rows == []
    report = {
        'schema': 'MathVisionKid.existing_source_locator_adjudication.v1',
        'scope': 'Two locator-only tasks. Existing source/receipt records and their hashes were read; no mathematical example was generated or edited. This is provenance recovery, not a new semantic or visual competence certification.',
        'input_files_sha256': pins,
        'decisions': [
            {
                'master_id': 'collinear_triple_complete_enumeration',
                'candidate_id': 'collinear_enumeration_and_segment_pairs',
                'status': 'ORIGINAL_ALIAS_LOCATORS_RECOVERED_FROM_EXISTING_G2_RECEIPTS',
                'original_locator_missing_resolved': True,
                'exact_original_record': {
                    'file': 'sgk_page_audit_20261019/g3_spatial_append/adjudication.json',
                    'json_path': 'cross_grade_merges[' + str(alias_index) + ']',
                    'canonical_form': alias['canonical_form'],
                    'canonical_record_sha256': sha(json.dumps(alias, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf8')),
                },
                'locators': receipts,
                'reason': 'The original cross-grade alias already carries seven explicit G2 book/page/image/URL sources. All seven match the independent existing page-review receipt rows exactly. The historical mapping intentionally retained only book_id starting g3, which removed these G2 locators from its derived page_receipts field. Recovering them does not invent a G3 page or replace the distinct G3 p21 locator.',
                'content_support': 'G2 p110 receipt explicitly names collinear_segment_all_pairs; p101, p111 and p130 explicitly name collinear_triples. These establish the origin of the combined alias. Other listed original pages retain their exact prior scope.',
                'grade_or_coverage_promoted': False,
                'g3_source_locator_claimed': False,
                'g2_pending_mathematical_or_visual_branches_closed': False,
                'existing_global_occurrence_counts_recomputed': False,
            },
            {
                'master_id': 'placeclass_torn_strip_constraints',
                'candidate_id': 'tornplaceclass_strip_assembly',
                'status': 'PENDING_SOURCE_ORIGINAL_G3_LOCATOR_NOT_ESTABLISHED',
                'original_locator_missing_resolved': False,
                'original_candidate_status': torn['status'],
                'original_candidate_actual_page_receipts': [],
                'g3_page_receipt_records_inspected': len(g3_rows),
                'exact_candidate_gap_id_matches_in_page_receipts': 0,
                'related_g4_receipts_preserved': tasks['placeclass_torn_strip_constraints']['exact_page_receipts'],
                'reason': 'The earliest inspected G3 candidate explicitly states UNRESOLVED_LOCATOR_REQUIRED and has no actual_page_receipts. The existing G3 page-review ledger contains no exact alias binding. The related G4 pp43-44 receipts are valid for G4, but cannot establish an original G3 locator. Broad word matching is not a proof that no such G3 page exists.',
                'text_mathematical_branch_complete_from_current_queue': tasks['placeclass_torn_strip_constraints']['text_mathematical_branch_complete'],
                'next_action': 'Keep pending-source explicitly. Reconcile only when an actual original G3 book/page/image receipt or the source that introduced this alias is available; do not generate another numeric variant or relabel G4 pages as G3.',
            },
        ],
        'network_read_attempts': [
            {'method': 'web.open', 'target': 'Existing official publisher detail and image URLs', 'result': 'Detail HTTP502; image URLs unavailable via web tool'},
            {'method': 'node fetch', 'target': 'Existing G2 p110 official publisher image URL', 'result': 'fetch failed; no bytes or new image hash obtained'},
            {'method': 'web.search', 'scope': 'Official taphuan.nxbgd.vn only', 'result': 'No matching indexed results'},
        ],
        'limits': [
            'Image hashes and actual reading are prior receipt evidence, independently cross-checked as records here; fresh remote image bytes were not obtained.',
            'No publisher book-series name is inferred from the reader slug.',
            'Recovered G2 origin is not converted into G3 evidence or a new curriculum coverage claim.',
            'Original source files, existing queue, history, accepted examples, counts and human signoffs remain unchanged.',
        ],
        'new_examples': 0, 'new_chat_rows': 0,
        'locators_resolved_from_existing_evidence': 1, 'locators_still_pending_source': 1,
        'Drive_or_Colab_modified': False, 'global_state_modified': False,
        'training_started': False, 'new_human_attestation': False,
    }
    assert {str(path.relative_to(HERE)): sha(path.read_bytes()) for path in inputs} == pins
    DEST.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(report, ensure_ascii=False, indent=2) + '\n').encode('utf8')
    if DEST.exists() and DEST.read_bytes() != payload:
        raise ValueError('Preserve existing locator adjudication; conflicting destination exists')
    DEST.write_bytes(payload)
    print(json.dumps({'file': str(DEST), 'bytes': len(payload), 'sha256': sha(payload), 'resolved': 1, 'pending_source': 1}, ensure_ascii=False))


if __name__ == '__main__':
    main()
