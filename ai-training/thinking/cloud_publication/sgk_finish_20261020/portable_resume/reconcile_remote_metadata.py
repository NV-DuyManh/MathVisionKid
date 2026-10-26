"""Reconcile range-only central directories without opening any data payload.

Creates a NEW catalog revision; original catalog and its bound SQLite databases
stay byte-identical. Historical manifest hashes pin candidate source members;
range directory CRC/name observations alone never become SHA256 verification.
"""
from copy import deepcopy
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import zipfile

OUT=Path(__file__).resolve().parent
THINKING=OUT.parents[2]
sys.path.insert(0,str(THINKING))
import math_data_portable_resume as P


def read(path):return json.loads(path.read_text('utf8'))


def main():
    original=read(OUT/'member_catalog.json');catalog=deepcopy(original)
    catalog['schema']='MathVisionKid.full_archive_member_catalog.v2_metadata_observed'
    catalog['parent_catalog_sha256']=P.digest(original)
    existing={(x['file_id'],x['member']):x for x in catalog['members']}
    remote=OUT.parent/'remote_metadata';old=THINKING/'cloud_publication/sgk_page_audit_20261019'
    refs={}
    with zipfile.ZipFile(old/'source_progress_index.zip') as archive:
        statebytes=archive.read('cloud_resume/original_arithmetic_state.json')
        state=json.loads(statebytes)
    for domain in state['physical_shells'].values():
        for item in domain['shards']:
            name='thinking/data/exhaustive_math_v1/'+item['path'].replace('\\','/')
            refs[name]={'sha256':item['sha256'],'bytes':item['bytes'],'rows':item['rows'],
                        'hash_basis':'HISTORICAL_CURRENT_ARITHMETIC_SHARD_STATE',
                        'metadata_sha256':hashlib.sha256(statebytes).hexdigest()}
    extensioncounts={'decimals/addition':441,'decimals/subtraction':231,'decimals/multiplication':441,
                     'decimals/division':420,'decimals/division_zero':21,'fractions/addition':900,
                     'fractions/nonnegative_subtraction':487,'fractions/multiplication':900,
                     'fractions/valid_division':750,'fractions/zero_divisor_guards':150}
    for item in read(old/'prior_restore_receipt.json')['restored']:
        path=item['path']
        if path=='extensions/structural.jsonl':
            name='thinking/data/exhaustive_math_v1/structural/curriculum_subskill_cases_v2.jsonl';count=15
        elif path.startswith(('extensions/fractions/','extensions/decimals/')):
            relative=path.removeprefix('extensions/');family,filename=relative.split('/')
            name=f'thinking/data/exhaustive_math_v1/{family}/corpus/{filename}'
            count=extensioncounts[relative.removesuffix('.jsonl.gz')]
        else:continue
        refs[name]={**item,'rows':count,'hash_basis':'PRESERVED_SOURCE_RESTORE_RECEIPT'}
    primary=THINKING/'data/primary_math_teacher_20261016/exports/accepted_teacher_cases_polished.jsonl'
    refs['thinking/data/primary_math_teacher_20261016/exports/accepted_teacher_cases_polished.jsonl']={
        'sha256':P.file_hash(primary),'bytes':primary.stat().st_size,'rows':782,
        'hash_basis':'UNCHANGED_LOCAL_FINAL_782_EXPORT_MATCHES_CURRENT_CONTEXT_SHA_99aefab7'}
    expected_primary='99aefab7a58177e3b3222f7bf269c02e991fafeaf2fed79e83b5b5b39ebc5a02'
    if P.file_hash(primary)!=expected_primary:raise ValueError('baseline export changed')
    observations=[];added_sources=[]
    for discovery in original['pending_discoveries']:
        fid=discovery['file_id'];doc=read(remote/f'{fid}.json');a=original['artifacts'][fid]
        if doc['expected_archive_sha256']!=a['sha256'] or doc['total_bytes']!=a['bytes'] or doc['full_archive_hash_verified'] is not False:
            raise ValueError('range observation artifact identity/verification flag mismatch')
        entries=doc['entries'];names=[x['name'] for x in entries]
        if len(names)!=len(set(names)):raise ValueError('duplicate central directory member')
        documents={x['name']:x for x in doc['metadata_documents']}
        if a['family']=='original_corpus':
            manifest=documents.get('CLOUD_PART_MANIFEST.json')
            if not manifest or set(manifest['document']['files']) != set(names)-{'CLOUD_PART_MANIFEST.json'}:
                raise ValueError('original part directory/declared member list mismatch')
        # Source/view hashes in numeric manifest must match immutable current
        # state refs. Never trust its PREPARED_NOT_COMMITTED state as current.
        for item in documents.values():
            if item['name']=='manifest_payload.json':
                for key in ('source','view'):
                    ref=item['document'][key];prior=existing[(fid,ref['name'])]
                    if prior['member_sha256']!=ref['sha256'] or prior['member_bytes']!=ref['bytes']:
                        raise ValueError('numeric member manifest conflicts with current registered source/view')
        for entry in entries:
            name=entry['name'];key=(fid,name)
            prior=existing.get(key)
            if prior:
                if prior.get('member_bytes') is not None and prior['member_bytes']!=entry['bytes']:
                    raise ValueError('member central directory size conflict')
                prior['range_central_directory_observed']=True
                prior['range_does_not_verify_archive_sha256']=True
                continue
            ref=refs.get(name)
            metadata=documents.get(name)
            role='candidate_source' if ref else 'metadata_only' if name.endswith('.json') else 'audit_history_or_metadata'
            if any(x in name.casefold() for x in ('sealed','pilot','concept_challenge')):
                role='frozen_metadata_only_payload_never_read'
            if ref and entry['bytes']!=ref['bytes']:raise ValueError('historical source size/central directory conflict')
            m={**a,'member':name,'member_sha256':ref['sha256'] if ref else metadata.get('sha256') if metadata else None,
               'member_bytes':entry['bytes'],'role':role,'rows':ref.get('rows') if ref else None,
               'status':'HISTORICAL_HASH_PINNED_RANGE_DIRECTORY_OBSERVED_NOT_PROCESSED' if ref else 'RANGE_DIRECTORY_OBSERVED_NO_PAYLOAD_READ',
               'range_directory_evidence':{'crc32':entry['crc32'],'method':entry['method'],
                    'compressed_bytes':entry['compressed_bytes'],'local_header_offset':entry['local_header_offset']},
               'range_does_not_verify_archive_sha256':True}
            if ref:m['source_hash_provenance']=ref
            catalog['members'].append(m);existing[key]=m
            if ref:added_sources.append(m)
        observations.append({'file_id':fid,'members':len(entries),'metadata_documents':len(doc['metadata_documents']),
            'central_directory_observed':True,'fresh_full_archive_hash_verified':False,
            'evidence_sha256':P.file_hash(remote/f'{fid}.json')})
    if sum(x['rows'] for x in added_sources)!=1519171 or len(added_sources)!=205:
        raise ValueError('original accepted source inventory count mismatch')
    catalog['pending_discoveries']=[]
    catalog['complete_remote_member_inventory']=True
    catalog['range_observations']=observations
    catalog['full_archive_token_split_audit_complete']=False
    catalog['complete_source_payload_read']=False
    catalog['all_archive_member_hashes_verified']=False
    catalog['range_scope_note']='Complete central directory names/CRC/sizes only; only named metadata decoded. Historical SHA pins candidate sources. No sealed/eval/pilot payload was opened. Full archive/member byte/SHA audit remains pending.'
    P.save(OUT/'member_catalog_discovered.json',catalog)
    checkpoint=read(OUT/'portable_checkpoint.json')
    for key,item in checkpoint['tasks'].items():
        if item['spec']['action']!='DISCOVER_HASH_PINNED_METADATA_MEMBERS' or item['status']=='COMPLETE':continue
        sha=item['spec']['inputs'][0]['sha256'];a=next(x for x in observations if original['artifacts'][x['file_id']]['sha256']==sha)
        token=P.claim(checkpoint,key,'portable-metadata-coordinator',ttl=600)
        P.acknowledge(checkpoint,key,token,result={'status':'COMPLETE_METADATA_DIRECTORY_ONLY',**a,'training_started':False})
    for m in added_sources:
        spec=P.task_spec('CPU_DATA_ONLY_MEMBER_AUDIT',[{'sha256':m['sha256'],'member':m['member'],'member_sha256':m['member_sha256']}],
                        {'role':'candidate_source','tokenizer_revision':'70d244cc86ccca08cf5af4e1e306ecf908b1ad5e','auditor_schema':'archive_audit.v2'})
        key=P.add_task(checkpoint,spec)
        checkpoint['tasks'][key]['catalog_entry']=catalog['members'].index(m)
        checkpoint['tasks'][key]['catalog_file']='member_catalog_discovered.json'
    checkpoint['discovered_catalog_sha256']=P.digest(catalog)
    checkpoint['catalog_lineage_note']='Original catalog_sha256 and source/chat DB bindings retained. Additional original source tasks target member_catalog_discovered.json. Merge source split evidence across fixed task catalogs before global final gates.'
    checkpoint['revision']+=1
    P.save(OUT/'portable_checkpoint.json',checkpoint)
    result={'schema':'MathVisionKid.remote_metadata_reconciliation.v1','artifacts_directories_observed':len(observations),
      'central_directory_members':sum(x['members'] for x in observations),'total_catalog_members':len(catalog['members']),
      'original_candidate_source_members_pinned':len(added_sources),'original_source_cases_reconciled':1519171,
      'orphan_test_manifests_not_used_as_current_source':4,'all_central_directory_discovery_tasks_complete':True,
      'full_archive_hash_verified_from_ranges':False,'full_archive_token_split_audit_complete':False,
      'finite_tasks':len(checkpoint['tasks']),'completed_tasks':len(checkpoint['completed']),
      'remaining_tasks':len(checkpoint['tasks'])-len(checkpoint['completed']),
      'candidate_chat_member_rows_preserved':6501044,'training_started':False}
    P.save(OUT/'remote_metadata_reconciliation_receipt.json',result);print(json.dumps(result))


if __name__=='__main__':main()
