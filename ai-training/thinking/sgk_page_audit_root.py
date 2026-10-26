"""Bounded page-review evidence. Records only pages actually viewed by root."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent / 'cloud_publication/sgk_page_audit_20261019'
FOLDER = ROOT / 'g4_audit'


def digest(data): return hashlib.sha256(data).hexdigest()


def record(book, descriptions):
    manifest = json.loads((FOLDER / f'{book}_pages.json').read_text(encoding='utf-8'))
    sources = {r['sample_id']: (r, digest(line)) for line in (ROOT / 'current_sources.jsonl').read_bytes().splitlines() if line for r in [json.loads(line)]}
    dest = FOLDER / 'page_review.jsonl'
    previous = [json.loads(x) for x in dest.read_text(encoding='utf-8').splitlines()] if dest.exists() else []
    keys = {(r['book_id'], r['printed_page']) for r in previous}
    fresh = []
    for page, types, ids, gaps in descriptions:
        if (book, page) in keys: continue
        image = FOLDER / f'{book}_p{page}.png'
        entry = next(x for x in manifest['pages'] if x['printed_page'] == page)
        refs = [{'sample_id': sid, 'source_row_sha256': sources[sid][1],
                 'actual_problem': sources[sid][0]['problem']} for sid in ids]
        fresh.append({'book_id': book, 'printed_page': page, 'array_index': entry['index'],
            'image_url': entry['url'], 'image_bytes': image.stat().st_size, 'image_sha256': digest(image.read_bytes()),
            'actual_visual_page_read': True, 'printed_page_number_visually_verified': True,
            'reviewer': 'ROOT', 'exercise_types_read': types, 'existing_actual_source_refs': refs,
            'gap_candidates': gaps, 'content_audit_status': 'ACTUAL_PAGE_FORMS_CATALOGUED',
            'mathematical_representation_comparison': 'Actual source problems referenced; candidate gaps require full-field semantic adjudication before new authoring.',
            'image_or_physical_modality_training_completeness_claimed': False,
            'textbook_question_text_copied': False})
    with dest.open('a', encoding='utf-8', newline='\n') as stream:
        for item in fresh: stream.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + '\n')
    for item in fresh: (FOLDER / f"{book}_p{item['printed_page']}.png").unlink()
    result = {'pages_actually_read': len(previous) + len(fresh), 'new': len(fresh),
              'last_batch_pages': [r['printed_page'] for r in fresh], 'staging_images_deleted_after_receipt': True}
    (FOLDER / 'summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('book'); parser.add_argument('batch_json')
    args = parser.parse_args()
    record(args.book, json.loads(Path(args.batch_json).read_text(encoding='utf-8')))
