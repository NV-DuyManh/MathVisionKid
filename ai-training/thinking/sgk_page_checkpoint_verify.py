"""Verify finite candidate references and frozen preservation; never train."""
from pathlib import Path
from collections import Counter
import hashlib,json,re

ROOT=Path(__file__).resolve().parent
RUN=ROOT/'cloud_publication/sgk_page_audit_20261019'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text('utf-8'))

def main():
    mapping=read(RUN/'g2v2_audit/g2_combined_candidate_adjudication.json')
    refs={};page_refs={}
    for name in ['current_sources.jsonl','release/accepted_cases.jsonl']:
        refs[name]=[(json.loads(b),sha(b)) for b in (RUN/name).read_bytes().splitlines() if b.strip()]
    for name in ['g2v1_audit/page_review.jsonl','g2v2_audit/page_review.jsonl']:
        page_refs[name]={sha(b):json.loads(b) for b in (RUN/name).read_bytes().splitlines() if b.strip()}
    items=mapping['adjudications'];assert len(items)==91
    assert len({r['candidate_id'] for r in items})==91
    assert dict(Counter(r['status'] for r in items))==mapping['status_counts']
    assert dict(Counter(r['book_id'] for r in items))==mapping['per_book_count']
    checked=0;pages=0
    for row in items:
        assert row['semantic_adjudication'] and row['finite_master_id']
        for ref in row['nearest_actual_valid_train_rows']:
            source,h=refs[ref['source_file']][ref['source_line_number']-1]
            assert h==ref['source_row_sha256'] and source['sample_id']==ref['sample_id']
            assert source.get('split','train')=='train' and not re.search('holdout|eval|pilot|protected',source['sample_id'],re.I)
            checked+=1
        for ref in row['actual_page_receipts']:
            source=page_refs[ref['receipt_path']][ref['receipt_line_sha256']]
            assert source['printed_page']==ref['printed_page'] and source.get('image_url',source.get('official_url'))==ref['image_url'] and source.get('image_sha256',source.get('sha256'))==ref['image_sha256']
            assert ref['actual_page_read'];pages+=1
    nearest=mapping['nearest_receipt'];assert sha((RUN/nearest['path']).read_bytes())==nearest['sha256']
    for ref in mapping['cross_grade_evidence']:
        assert sha((RUN/ref['path']).read_bytes())==ref['sha256'],ref['path']
    frozen=read(RUN/'release/preservation_frozen_local.json')
    for name,ref in frozen.items():
        b=(ROOT/'data/primary_math_teacher_20261016'/name).read_bytes()
        assert len(b)==ref['bytes'] and sha(b)==ref['sha256']
    result=dict(status='PASS_REFERENCE_INTEGRITY_AND_PRESERVATION_ONLY',mapping_sha256=sha((RUN/'g2v2_audit/g2_combined_candidate_adjudication.json').read_bytes()),candidate_count=91,source_references_checked=checked,page_references_checked=pages,frozen_files_unchanged=len(frozen),semantic_mapping_not_established_by_parser=True,training_started=False)
    (RUN/'release/checkpoint_reference_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))
if __name__=='__main__':main()
