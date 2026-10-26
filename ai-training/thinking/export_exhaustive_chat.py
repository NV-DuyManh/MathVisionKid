"""Join validated gzip members, retaining every selected case's four modes."""
import gzip,json,shutil,time
from pathlib import Path
from collections import Counter
import exhaustive_primary_math as e
BASE=e.HERE/'data/primary_math_teacher_20261016'
def export():
 r=e.load(e.ROOT/'full_corpus_and_training_views.json');dest=e.ROOT/'publication/teacher_chat_train_stage1.jsonl.gz';dest.parent.mkdir(parents=True,exist_ok=True)
 receipt=dest.parent/'combined_chat_receipt.json';inputs=[]
 baseline=BASE/'exports/teacher_chat_train_polished.jsonl'
 inputs.append({'path':str(baseline),'sha256':e.filehash(baseline),'rows':3128,'kind':'plain_jsonl'})
 for m in r['arithmetic_training_view_shards']:inputs.append({'path':str(e.ROOT/m['path']),'sha256':m['sha256'],'rows':m['chat_rows'],'kind':'gzip'})
 for folder,statefile in [('fractions','fraction_build_state.json'),('decimals','decimal_build_state.json')]:
  s=e.load(e.ROOT/folder/statefile);ms=s['view_manifests']
  for m in ms:inputs.append({'path':str(e.ROOT/folder/m['path']),'sha256':m['sha256'],'rows':m['chat_rows'],'kind':'gzip'})
 structure=e.ROOT/'structural/teacher_chat.jsonl.gz';inputs.append({'path':str(structure),'sha256':e.filehash(structure),'rows':60,'kind':'gzip'})
 assert sum(i['rows'] for i in inputs)==r['chat_train_rows']==6074308
 if receipt.exists():
  old=e.load(receipt);assert old['inputs']==inputs and e.filehash(dest)==old['sha256'];print(e.dumps(old));return
 tmp=dest.with_suffix('.partial.gz');start=time.monotonic()
 # An RFC1952 multi-member gzip stream is decoded normally by Python/HF
 # gzip readers. Each existing member is copied byte-for-byte, not reparsed
 # and re-encoded; the initial plain baseline is its own gzip member.
 with e.gzopen(tmp,'wt') as f:
  for line in baseline.open(encoding='utf-8'):f.write(line)
 with tmp.open('ab') as out:
  for i in inputs[1:]:
   assert e.filehash(i['path'])==i['sha256']
   with open(i['path'],'rb') as src:shutil.copyfileobj(src,out,1024*1024)
 # Full decompression readback proves no members truncated or omitted.
 actual=0
 with gzip.open(tmp,'rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):actual+=block.count(b'\n')
 assert actual==r['chat_train_rows'];tmp.replace(dest)
 result={'path':str(dest.relative_to(e.HERE.parent)),'sha256':e.filehash(dest),'bytes':dest.stat().st_size,'chat_rows':actual,'expected_chat_rows':r['chat_train_rows'],'complete_gzip_decompression_row_count_passed':True,'all_input_hashes_verified':True,'compression':'RFC1952_MULTI_MEMBER_GZIP_JSONL','inputs':inputs,'seconds':round(time.monotonic()-start,3),'baseline_preserved':True,'no_silent_drop_or_truncation':True,'training_started':False}
 e.save(receipt,result);print(e.dumps({k:v for k,v in result.items() if k!='inputs'}))
if __name__=='__main__':export()
