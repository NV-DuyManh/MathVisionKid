"""Finalize bounded repair bundle after actual cloud collision evidence."""
import hashlib,json,zipfile
from pathlib import Path
R=Path(__file__).resolve().parent/'cloud_publication/antigravity_intake_20261022'
sha=lambda b:hashlib.sha256(b).hexdigest()
def dump(name,value):
    (R/name).write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8')
def main():
    check=json.loads((R/'cloud_collision_check.json').read_text(encoding='utf8'))
    assert check['indexed_source_versions']==1629842
    assert not check['id_collisions'] and not check['exact_source_problem_hash_collisions']
    assert all(x['kind']=='canonical' and x['split']=='train' for x in check['observed_split_keys'])
    m=json.loads((R/'manifest.json').read_text(encoding='utf8'))
    review=json.loads((R/'root_content_review.json').read_text(encoding='utf8'))
    review.update(status='ACCEPTED_BOUNDED_REPAIR_APPEND_FULL_ARCHIVE_AUDIT_REMAINS_PENDING',
        cloud_collision_receipt_sha256=sha((R/'cloud_collision_check.json').read_bytes()),
        cloud_source_ID_and_exact_problem_field_checks_passed=True,
        full_archive_normalized_question_check_pending=True)
    dump('root_content_review.json',review)
    for name in ['root_content_review.json','cloud_collision_check.json']:
        b=(R/name).read_bytes();m['entries'][name]={'bytes':len(b),'sha256':sha(b)}
    m.update(cloud_collision_gate_pending=False,cloud_source_ID_and_exact_problem_field_checks_passed=True,
        full_archive_normalized_question_check_pending=True,full_archive_ready=False,
        active_candidate_members=['accepted_cases.jsonl','accepted_chat.jsonl'])
    dump('manifest.json',m)
    dest=R/'derived_g2_repair_append.zip'
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name in sorted(m['entries']):
            b=(R/name).read_bytes();assert sha(b)==m['entries'][name]['sha256']
            zi=zipfile.ZipInfo(name,(2026,10,22,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED;z.writestr(zi,b)
        zi=zipfile.ZipInfo('manifest.json',(2026,10,22,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED;z.writestr(zi,(R/'manifest.json').read_bytes())
    b=dest.read_bytes();ref={'path':str(dest),'bytes':len(b),'sha256':sha(b),'cases':64,'chat_rows':256,
        'file_name':'MathVisionKid_G2_DERIVED_REPAIR_20261022_'+sha(b)[:16]+'.zip'}
    dump('bundle_local_receipt.json',ref);print(json.dumps(ref))
if __name__=='__main__':main()
