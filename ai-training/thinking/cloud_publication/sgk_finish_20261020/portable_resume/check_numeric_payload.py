"""CPU-only complete audit of ONE supplied exact-ID numeric archive.

Uses a fixed per-artifact catalog/SQLite so later metadata inventory additions
cannot invalidate completed row cursors. No network or data generation.
"""
from pathlib import Path
import argparse
import json
import sys
import time

OUT = Path(__file__).resolve().parent
THINKING = OUT.parents[2]
sys.path.insert(0, str(THINKING))
import exhaustive_colab_loader as L
import math_data_archive_audit as A
import math_data_portable_resume as P


def run(file_id,payload_path,max_chat_chunk=256):
    full = json.loads((OUT/'member_catalog.json').read_text('utf8'))
    matching = [(i,x) for i,x in enumerate(full['members']) if x['file_id']==file_id and x['role'] in ('candidate_source','candidate_chat')]
    if len(matching)!=2 or {x['role'] for i,x in matching}!={'candidate_source','candidate_chat'} or any(x['family']!='numeric_extension' for i,x in matching):
        raise ValueError('require exact registered numeric source/chat pair')
    matching.sort(key=lambda x:x[1]['role']!='candidate_source')
    catalog={'schema':'MathVisionKid.single_numeric_data_audit.v1','members':[x for i,x in matching]}
    key=matching[0][1]['sha256'][:16]
    directory=OUT/('numeric_'+key);directory.mkdir(exist_ok=True)
    catalog_path=directory/'fixed_catalog.json'
    if catalog_path.exists() and json.loads(catalog_path.read_text('utf8'))!=catalog:
        raise ValueError('fixed artifact catalog changed')
    P.save(catalog_path,catalog)
    tokenizer=L.load_qwen_tokenizer(Path.home()/'.cache/huggingface/hub/models--Qwen--Qwen3-1.7B/snapshots'/L.REVISION)
    events=[]
    for original_index,entry in matching:
        checkpoint=json.loads((OUT/'portable_checkpoint.json').read_text('utf8'))
        task=next(k for k,v in checkpoint['tasks'].items() if v.get('catalog_entry')==original_index and v['spec']['action']=='CPU_DATA_ONLY_MEMBER_AUDIT')
        lease=checkpoint['tasks'][task].get('lease')
        if lease and lease['worker']=='portable-numeric-audit-worker' and lease['expires']>time.time():
            token=lease['token']  # Same serialized durable worker resumes its existing lease.
        else:
            token=P.claim(checkpoint,task,'portable-numeric-audit-worker',ttl=7200)
        if token is None:
            continue
        P.save(OUT/'portable_checkpoint.json',checkpoint)
        while True:
            store=A.AuditStore(directory/'audit.sqlite',catalog,tokenizer)
            try:
                result=store.consume(entry,payload_path,max_rows=max_chat_chunk if entry['role']=='candidate_chat' else None)
                report=store.report()
            finally:
                store.close()
            events.append(dict(role=entry['role'],consume=result))
            P.acknowledge(checkpoint,task,token,{'sqlite_file':str((directory/'audit.sqlite').relative_to(OUT)),
                'next_unconsumed_line':result['rows'],'role':entry['role'],'fixed_catalog_sha256':P.digest(catalog)})
            P.save(OUT/'portable_checkpoint.json',checkpoint)
            P.save(directory/'progress.json',{'events':events,'audit':report})
            if result.get('complete') or result.get('already_complete'):
                break
        if report['issues']:
            raise ValueError('numeric archive unresolved issue: '+json.dumps(report))
        P.acknowledge(checkpoint,task,token,result={'artifact_sha256':entry['sha256'],
            'member_sha256':entry['member_sha256'],'rows':entry['rows'],'role':entry['role'],
            'scope':'EXACT_REGISTERED_NUMERIC_ARCHIVE_MEMBER','status':'COMPLETE',
            'source_raw_row_hash_unverified_rows':report['source_raw_row_hash_unverified_rows'],
            'source_hash_caveat':'No legacy chat source_row_sha256 field is fabricated; exact member hashes and field linkage are verified separately.',
            'training_started':False})
        P.save(OUT/'portable_checkpoint.json',checkpoint)
    store=A.AuditStore(directory/'audit.sqlite',catalog,tokenizer)
    try:report=store.report()
    finally:store.close()
    expected=next(x['rows'] for i,x in matching if x['role']=='candidate_chat')
    if report['rows_processed']!=expected or report['untokenized_rows'] or report['source_linkage_unverified_rows'] or report['missing_source_signatures_rows'] or report['issues']:
        raise ValueError('numeric final gate incomplete: '+json.dumps(report))
    receipt={'schema':'MathVisionKid.numeric_archive_complete_member_audit.v1','file_id':file_id,
        'artifact_sha256':P.file_hash(payload_path),'source_rows':next(x['rows'] for i,x in matching if x['role']=='candidate_source'),
        'expected_chat_rows':expected,'audit':report,'tokenizer_revision':L.REVISION,
        'state_count_not_inferred_as_four_modes_per_preserved_source':True,
        'raw_chat_source_hash_field_caveat':'Missing historical row hash is reported, not replaced by canonical equality.',
        'model_weights_loaded':False,'training_started':False,'full_archive_token_split_audit_complete':False}
    P.save(directory/'final_receipt.json',receipt)
    print(json.dumps(receipt))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--file-id',required=True);parser.add_argument('--payload',required=True)
    parser.add_argument('--chunk-rows',type=int,default=256)
    args=parser.parse_args();run(args.file_id,Path(args.payload),args.chunk_rows)
