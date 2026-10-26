"""All3596 audited chat associations plus adversarial read-time overlay checks."""
from copy import deepcopy
from pathlib import Path
import json
import sys

OUT=Path(__file__).resolve().parent;THINKING=OUT.parents[2]
sys.path.insert(0,str(THINKING))
import math_data_portable_resume as P
import math_data_archive_audit as A
from math_data_source_hash_overlay import VerifiedSourceHashOverlay


def rejected(function):
    try:function()
    except ValueError:return
    raise AssertionError('expected overlay rejection')


def main():
    manifest=OUT/'manifest.json';overlay=VerifiedSourceHashOverlay(manifest,P.file_hash(manifest))
    base=OUT.parent/'portable_resume';count=derived=original=0;first=None;inputs=[]
    for name in ['numeric_911a598ae1bc578f','numeric_7edba0a6ef712e51','current_supplements']:
        catalog=json.loads((base/name/'fixed_catalog.json').read_text('utf8'))
        for entry in catalog['members']:
            if entry['role']!='candidate_chat':continue
            path=THINKING/'cloud_publication/sgk_page_audit_20261019/prior_balanced'/entry['original_member'] if entry.get('original_member') else OUT.parent/'small_audit_payloads'/entry['file_name']
            before=P.file_hash(path)
            with A.payload(entry,path) as stream:
                for text in stream:
                    row=json.loads(text);snapshot=P.canonical(row);source,link=overlay.chats[row['sample_id']]
                    source_sha=source['source_binding']['member_sha256'];chat_sha=link['chat_binding']['member_sha256']
                    decorated=overlay.apply(row,source_sha,chat_sha)
                    assert P.canonical(row)==snapshot
                    assert decorated['source_row_sha256']==source['source_raw_row_sha256']
                    assert decorated['split']==row['split']
                    if decorated['sourcehash_original_field_present']:
                        original+=1;assert row['source_row_sha256']==decorated['source_row_sha256']
                    else:
                        derived+=1;assert 'source_row_sha256' not in row and decorated['sourcehash_origin']=='DERIVED_FROM_VERIFIED_PINNED_SOURCE_MEMBER'
                    count+=1
                    if first is None:first=(row,source_sha,chat_sha)
            assert before==P.file_hash(path);inputs.append({'path':str(path),'sha256':before,'unchanged':True})
    assert (count,derived,original)==(3596,3356,240)
    row,source_sha,chat_sha=first
    wrong_hash=deepcopy(row);wrong_hash['source_row_sha256']='f'*64
    rejected(lambda:overlay.apply(wrong_hash,source_sha,chat_sha))
    wrong_prompt=deepcopy(row);prompt=json.loads(wrong_prompt['messages'][1]['content']);prompt['problem']='tampered problem';wrong_prompt['messages'][1]['content']=P.canonical(prompt)
    rejected(lambda:overlay.apply(wrong_prompt,source_sha,chat_sha))
    rejected(lambda:overlay.apply(row,'f'*64,chat_sha))
    rejected(lambda:overlay.apply(row,source_sha,'f'*64))
    rejected(lambda:VerifiedSourceHashOverlay(manifest,'f'*64))
    # Field binding remains a second check even if an otherwise-authorized
    # decorated row's fingerprint were changed in process after manifest load.
    _,link=overlay.chats[row['sample_id']]
    saved=link['original_chat_canonical_sha256'];link['original_chat_canonical_sha256']=P.digest(wrong_prompt)
    rejected(lambda:overlay.apply(wrong_prompt,source_sha,chat_sha))
    link['original_chat_canonical_sha256']=saved
    result={'schema':'MathVisionKid.source_hash_overlay_validation.v1','all_chat_associations_checked':count,
      'derived_missing_field_rows':derived,'original_source_hash_field_rows_preserved':original,
      'adversarial_checks_passed':6,'raw_input_files_unchanged':inputs,'overlay_manifest_sha256':P.file_hash(manifest),
      'legacy_raw_fields_not_rewritten':True,'catalog_and_SQLite_not_modified':True,
      'training_started':False,'full_archive_token_audit_claimed':False,'status':'PASS'}
    P.save(OUT/'validation_receipt.json',result);print(json.dumps({k:v for k,v in result.items() if k!='raw_input_files_unchanged'}))


if __name__=='__main__':main()
