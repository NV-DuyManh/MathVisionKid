from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib
p=Path(__file__).parent;d=p/'metadata_final_all'
def read(n):return json.loads((d/n).read_bytes())
pub=read('publication__publication_status.json');fe=read('final_eval_publication_status.json');controls=read('four_controls_publication_status.json');manifest=read('four_controls_verified_manifest.json');run=read('training__run_complete.json')
assert pub['state']=='COMPLETE_RAW_VERIFIED' and pub['publication_finalized'] is True
assert fe['state']=='COMPLETE_RAW_VERIFIED' and all(x['fresh_raw_readback_verified'] for x in fe['artifacts'].values())
assert controls['state']=='COMPLETE_RAW_VERIFIED' and controls['receipt']==manifest
ids={'progress':'1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX','chat':'1tkSQoAlxXXRUg2AwYfvqsFKVEmM_LmR6','context':'13gdIPQTFKcekoQQtgo0TXc7RgeadzIN9','state':'1TLoQIbrRVmgsg-2uiUujCfM3HrK62Yme'}
assert [x['kind'] for x in manifest['verified_writes']]==['progress','chat','context','state']
for x in manifest['verified_writes']:
 assert x['id']==ids[x['kind']] and x['fresh_raw_readback_verified'] is True and x['sha256']==manifest['prepared_hashes'][x['kind']]
ctx=p.parents[2]/'MATH_TRAINING_CONTEXT.md';ch=hashlib.sha256(ctx.read_bytes()).hexdigest()
assert controls['canonical_context_sha256']==manifest['prepared_hashes']['context']==ch
report=p/'final_semantic_assessment.json';rh=hashlib.sha256(report.read_bytes()).hexdigest();proof=pub['artifacts']['training/final_semantic_assessment.json']
assert proof['sha256']==rh and proof['fresh_raw_readback_verified'] is True
assert run['metrics']['step']==50 and run['unique_examples']==800 and run['metrics']['supervised_tokens']==162336 and run['best']['kind']=='untrained_base' and not run['whole_corpus_training_claimed']
result={'verified_utc':datetime.now(timezone.utc).isoformat(),'phase':'COMPLETE_REGRESSION_REJECTED_NO_NEW_ADAPTER_PROMOTED','drive_four_controls':manifest,'run_publication_complete':True,'report_proof':proof,'locked_final_eval_raw_files':fe['artifacts'],'context_sha256':ch,'actual_training_updates':50,'actual_unique_chat_exposures':800,'new_adapter_improvement_demonstrated':False,'no_active_training_expected':True,'source_data_or_labels_modified':False}
(p/'final_closeout_verified.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':result['phase'],'report_id':proof['id'],'four_controls_raw_verified':True,'context_sha256':ch,'final_control_hashes':manifest['prepared_hashes'],'all_final_eval_files_raw_verified':True}))
