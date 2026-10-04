"""Triage local candidates and imported labels; never approve training targets."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import unicodedata

from drive_line_batch import DEFAULT_DATA, write_json


def label_flags(text):
    folded=''.join(c for c in unicodedata.normalize('NFD',text.lower()) if not unicodedata.combining(c)).replace('đ','d')
    flags=[]
    if not text.strip():flags.append('empty_imported_label')
    if re.search(r'khong co (?:chu|bat ky ky tu|hinh anh)|khong the (?:nhan dang|nhan biet)|cannot (?:read|recognize)',folded):
        flags.append('imported_provider_refusal_or_no_content_claim')
    return flags


def review(folder):
    selection=json.loads((folder/'source_selection.json').read_text(encoding='utf-8'))
    records=[];flag_counts=Counter();texts=Counter();stages=Counter()
    for index,item in enumerate(selection,1):
        record_path=folder/'local_regions'/f"{item['drive_id']}.json"
        if not record_path.exists():continue
        record=json.loads(record_path.read_text(encoding='utf-8'));flags=[]
        if record['status']!='tested':flags.append('execution_failed')
        elif not record['boxes']:flags.append('no_region_candidates')
        else:
            if len(record['boxes'])>1 and item.get('source_type')=='provided_line_crop':
                flags.append('multiple_candidates_in_supplied_line_crop')
            if record['diagnostics'].get('source_text_may_be_clipped'):flags.append('tight_crop_model_fallback')
        if record.get('image_size',[0,100])[1]<32:flags.append('source_height_under_32_pixels')
        imported=folder/'imported_labels'/f"{item['drive_id']}.json"
        if imported.exists():
            text=json.loads(imported.read_text(encoding='utf-8'))['provided_text']
            texts[text]+=1;flags.extend(label_flags(text))
        label=folder/'labels'/f"{item['drive_id']}.json"
        reference=json.loads(label.read_text(encoding='utf-8')) if label.exists() else {}
        stage=reference.get('review_status','needs_review');stages[stage]+=1
        if stage=='needs_review' and reference.get('sha256')==record.get('sha256'):
            write_json(label,{**reference,'review_flags':flags,'training_eligible':False})
        flag_counts.update(flags)
        records.append({'drive_id':item['drive_id'],'index':index,'name':item['name'],
                        'sha256':record.get('sha256'),'reference_status':stage,'flags':flags,
                        'flag_semantics':'Review priorities, not verified errors'})
    result={'selected':len(selection),'records_available':len(records),
            'flagged_sources':sum(bool(x['flags']) for x in records),'flag_counts':dict(flag_counts),
            'label_stages':dict(stages),'all_predictions_verified':False,'training_performed':False,
            'records':records}
    write_json(folder/'local_review_queue.json',result)
    write_json(folder/'imported_label_audit.json',{'provided_labels':sum(texts.values()),
               'top_repeated_texts':texts.most_common(20),'verified_reference_labels_created':0})
    print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--batch',required=True)
    args=parser.parse_args();folder=(DEFAULT_DATA/args.batch).resolve()
    if not folder.is_relative_to(DEFAULT_DATA.resolve()):parser.error('Batch must remain in private data directory')
    review(folder)
