"""Check current boundary216 and pedagogyv3 240 only, no holdout files."""
from pathlib import Path
import json
import sys
import time

OUT=Path(__file__).resolve().parent;THINKING=OUT.parents[2]
sys.path.insert(0,str(THINKING))
import exhaustive_colab_loader as L
import math_data_archive_audit as A
import math_data_portable_resume as P


def main():
    full=json.loads((OUT/'member_catalog.json').read_text('utf8'))
    names=['audit/boundary_cases.jsonl','audit/pedagogy_cases_v3.jsonl','audit/boundary_chat.jsonl','audit/pedagogy_chat_v3.jsonl']
    matching=[(i,x) for name in names for i,x in enumerate(full['members']) if x['member']==name]
    if len(matching)!=4:raise ValueError('missing exact current supplement entries')
    direct=[]
    for i,x in matching:
        direct.append({'file_id':x['file_id'],'sha256':x['member_sha256'],'bytes':x['member_bytes'],
                      'role':x['role'],'rows':x['rows'],'original_archive_sha256':x['sha256'],
                      'original_member':x['member']})
    catalog={'schema':'MathVisionKid.current_supplement_direct_member_audit.v1','members':direct}
    directory=OUT/'current_supplements';directory.mkdir(exist_ok=True)
    fixed=directory/'fixed_catalog.json'
    if fixed.exists() and json.loads(fixed.read_text('utf8'))!=catalog:raise ValueError('fixed source recipe changed')
    P.save(fixed,catalog)
    tokenizer=L.load_qwen_tokenizer(Path.home()/'.cache/huggingface/hub/models--Qwen--Qwen3-1.7B/snapshots'/L.REVISION)
    checkpoint=json.loads((OUT/'portable_checkpoint.json').read_text('utf8'))
    events=[]
    for (index,original),entry in zip(matching,direct):
        task=next(k for k,v in checkpoint['tasks'].items() if v.get('catalog_entry')==index and v['spec']['action']=='CPU_DATA_ONLY_MEMBER_AUDIT')
        lease=checkpoint['tasks'][task].get('lease')
        token=lease['token'] if lease and lease['worker']=='portable-supplement-audit-worker' and lease['expires']>time.time() else P.claim(checkpoint,task,'portable-supplement-audit-worker',ttl=3600)
        if token is None:continue
        P.save(OUT/'portable_checkpoint.json',checkpoint)
        path=THINKING/'cloud_publication/sgk_page_audit_20261019/prior_balanced'/original['member']
        while True:
            store=A.AuditStore(directory/'audit.sqlite',catalog,tokenizer)
            try:
                result=store.consume(entry,path,max_rows=128 if entry['role']=='candidate_chat' else None)
                report=store.report()
            finally:store.close()
            events.append({'member':original['member'],'consume':result})
            P.acknowledge(checkpoint,task,token,{'sqlite_file':'current_supplements/audit.sqlite',
                        'next_unconsumed_line':result['rows'],'fixed_catalog_sha256':P.digest(catalog)})
            P.save(OUT/'portable_checkpoint.json',checkpoint)
            P.save(directory/'progress.json',{'events':events,'audit':report})
            if result.get('complete') or result.get('already_complete'):break
        if report['issues']:raise ValueError('unresolved source/chat issues '+json.dumps(report))
        P.acknowledge(checkpoint,task,token,result={'artifact_sha256':original['sha256'],
            'member_sha256':original['member_sha256'],'rows':entry['rows'],'role':entry['role'],
            'scope':'CURRENT_BOUNDARY_OR_PEDAGOGY_V3_ONLY','status':'COMPLETE',
            'raw_source_hash_missing_reported_not_fabricated':True,'training_started':False})
        P.save(OUT/'portable_checkpoint.json',checkpoint)
    store=A.AuditStore(directory/'audit.sqlite',catalog,tokenizer)
    try:
        report=store.report()
        splits=dict(store.db.execute('SELECT split,count(*) FROM samples GROUP BY split'))
    finally:store.close()
    if report['rows_processed']!=456 or report['issues'] or report['source_linkage_unverified_rows'] or report['untokenized_rows']:
        raise ValueError('supplement audit incomplete '+json.dumps(report))
    P.save(directory/'final_receipt.json',{'schema':'MathVisionKid.current_supplement_member_audit.v1',
        'audit':report,'by_split':splits,'candidate_train_chat_rows':408,'current_eval_chat_rows_not_promoted_to_train':48,
        'boundary_sources':69,'boundary_exported_chat_rows':216,'pedagogy_v3_sources':60,'pedagogy_v3_chat_rows':240,
        'tokenizer_revision':L.REVISION,'holdout_or_sealed_or_pilot_files_opened':False,
        'selected_balanced_diagnostic_duplicates_audited_or_added':False,'training_started':False})
    print(json.dumps({'audit':report,'by_split':splits}))


if __name__=='__main__':main()
