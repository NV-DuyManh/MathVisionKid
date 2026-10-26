"""Additive overlay derived only from the three already verified audit DBs."""
from pathlib import Path
import hashlib
import json
import sqlite3
import sys
from collections import Counter

OUT=Path(__file__).resolve().parent;THINKING=OUT.parents[2]
sys.path.insert(0,str(THINKING))
import math_data_portable_resume as P
import math_data_archive_audit as A


def main():
    base=OUT.parent/'portable_resume'
    directories=[base/'numeric_911a598ae1bc578f',base/'numeric_7edba0a6ef712e51',base/'current_supplements']
    sources={};membership=[];db_evidence=[]
    for directory in directories:
        catalog=json.loads((directory/'fixed_catalog.json').read_text('utf8'))
        entries=catalog['members'];dbpath=directory/'audit.sqlite';before=P.file_hash(dbpath)
        db=sqlite3.connect(dbpath.resolve().as_uri()+'?mode=ro',uri=True)
        try:
            if db.execute('SELECT count(*) FROM issues').fetchone()[0]:raise ValueError('unresolved source audit issue')
            if db.execute('SELECT count(*) FROM samples WHERE linkage_verified=0').fetchone()[0]:raise ValueError('unverified field association')
            keymap={P.digest({k:entry.get(k) for k in ('sha256','member','member_sha256','role')}):entry for entry in entries}
            source_entries=[x for x in entries if x['role']=='candidate_source']
            def binding(entry):
                return {'artifact_sha256':entry.get('original_archive_sha256',entry['sha256']),
                        'member':entry.get('original_member',entry.get('member')),
                        'member_sha256':entry.get('member_sha256') or entry['sha256']}
            source_member_by_id={}
            for entry in source_entries:
                if entry.get('original_member'):
                    sourcepath=THINKING/'cloud_publication/sgk_page_audit_20261019/prior_balanced'/entry['original_member']
                else:
                    sourcepath=OUT.parent/'small_audit_payloads'/entry['file_name']
                with A.payload(entry,sourcepath) as stream:
                    for text in stream:
                        row=json.loads(text);rawhash=hashlib.sha256(text.removesuffix('\n').removesuffix('\r').encode()).hexdigest()
                        if row['sample_id'] in source_member_by_id:raise ValueError('sourceID repeats across source members')
                        source_member_by_id[row['sample_id']] = (entry,rawhash,P.digest(row),P.digest(A.source_projection(row)))
            for sid,canonical_hash,raw_hash,signatures,projection in db.execute('SELECT id,hash,raw_hash,signatures,projection FROM sources'):
                entry,reopened_raw,reopened_canonical,reopened_projection=source_member_by_id[sid]
                if (raw_hash,canonical_hash,P.digest(json.loads(projection))) != (reopened_raw,reopened_canonical,reopened_projection):
                    raise ValueError('actual source member row/fingerprint does not match audited database')
                if sid in sources:raise ValueError('duplicate source identity across audit DBs')
                obj=json.loads(projection)
                sources[sid]={'source_sample_id':sid,'source_raw_row_sha256':raw_hash,
                    'source_canonical_sha256':canonical_hash,'source_binding':binding(entry),
                    'source_projection':obj,'source_projection_sha256':P.digest(obj),
                    'chat_memberships':[],'sourcehash_origin':'DERIVED_FROM_VERIFIED_PINNED_SOURCE_MEMBER',
                    'raw_chat_original_field_presence_not_claimed':True}
            for sample,member,line,chat_hash,sid,mode,split,raw_verified in db.execute('SELECT id,member,line,hash,case_id,mode,split,source_hash_verified FROM samples'):
                source=sources[sid]
                item={'sample_id':sample,'mode':mode,'split':split,'original_chat_canonical_sha256':chat_hash,
                      'chat_binding':binding(keymap[member]),'line':line,'original_source_hash_field_was_verified':bool(raw_verified)}
                source['chat_memberships'].append(item);membership.append(item)
        finally:db.close()
        if before!=P.file_hash(dbpath):raise ValueError('read-only DB mutated')
        db_evidence.append({'database':str(dbpath.relative_to(OUT.parent)),
            'sha256':before,'fixed_catalog_sha256':P.file_hash(directory/'fixed_catalog.json'),'read_only':True})
    assert len(sources)==1130 and len(membership)==3596
    path=OUT/'case_source_hash_overlay.jsonl'
    path.write_text(''.join(P.canonical(sources[sid])+'\n' for sid in sorted(sources)),encoding='utf8')
    manifest={'schema':'MathVisionKid.additive_source_hash_overlay.v1',
       'overlay':{'file_name':path.name,'sha256':P.file_hash(path),'bytes':path.stat().st_size},
       'source_cases':len(sources),'chat_memberships':len(membership),
       'by_split':dict(Counter(x['split'] for x in membership)),
       'derived_missing_field_chat_rows':sum(not x['original_source_hash_field_was_verified'] for x in membership),
       'original_field_verified_chat_rows':sum(x['original_source_hash_field_was_verified'] for x in membership),
       'source_cases_without_current_export_chat':sum(not x['chat_memberships'] for x in sources.values()),
       'database_evidence':db_evidence,
       'scope':'Only1001numeric+129currentboundary/pedagogy source cases indexed in verified bounded audits; no old payload rewrite, no full6M claim.',
       'sourcehash_origin_for_missing_raw_field':'DERIVED_FROM_VERIFIED_PINNED_SOURCE_MEMBER',
       'raw_original_field_invented':False,'new_training_eligibility_granted':False,
       'training_started':False,'drive_mutated':False}
    P.save(OUT/'manifest.json',manifest);print(json.dumps(manifest))


if __name__=='__main__':main()
