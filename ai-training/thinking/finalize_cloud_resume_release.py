"""Small release artifacts and truthful counts; never reconstruct full corpus."""
import argparse,hashlib,json,shutil,zipfile
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import exhaustive_cloud_resume as c

HERE=c.HERE;RUN=c.RUN;PROJECT=HERE.parent
BALANCED=RUN/'balanced_release';BUNDLE=RUN/'MathVisionKid_BALANCED_COLAB_BUNDLE.zip'
def readrows(p):return [json.loads(l) for l in Path(p).read_text('utf-8').splitlines() if l.strip()]
def bundle():
 m=c.read(BALANCED/'MathVisionKid_BALANCED_TRAINING_MANIFEST.json')
 assert m['TRAINING_DATASET_READY'] and m['no_training_invoked']
 state=c.read(RUN/'working_cloud_state.json')
 assert sum(s['cases'] for s in state['extension_shards'])==110070
 assert all(d['missing_pairs']==0 for d in state['extension_domains'].values())
 required=['pedagogy_cases.jsonl','pedagogy_cases_v2.jsonl','pedagogy_cases_v3.jsonl',
  'pedagogy_chat.jsonl','pedagogy_chat_v2.jsonl','pedagogy_chat_v3.jsonl',
  'boundary_cases.jsonl','boundary_chat.jsonl','holdout_arithmetic_cases.jsonl','holdout_arithmetic_cases_v2.jsonl',
  'holdout_arithmetic_chat.jsonl','holdout_arithmetic_chat_v2.jsonl']
 extras=[RUN/n for n in required]
 extras+=[p for p in RUN.glob('*.json') if any(s in p.name for s in ('qa','semantic_review','reservations','original_payload_recheck','loader_tests_receipt','holdout_signatures'))]
 files=[(p,'balanced_release/'+p.relative_to(BALANCED).as_posix()) for p in BALANCED.rglob('*') if p.is_file()]
 files+=[(p,'audit/'+p.name) for p in extras]
 assert len({n for _,n in files})==len(files)
 with zipfile.ZipFile(BUNDLE,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p,name in sorted(files,key=lambda x:x[1]):
   info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.create_system=3;info.external_attr=0o100644<<16;z.writestr(info,p.read_bytes())
 assert BUNDLE.stat().st_size<100*1024*1024
 with zipfile.ZipFile(BUNDLE) as z:
  assert z.testzip() is None
  assert json.loads(z.read('balanced_release/MathVisionKid_BALANCED_TRAINING_MANIFEST.json'))==m
 receipt={'path':str(BUNDLE),'file_name':BUNDLE.name,'bytes':BUNDLE.stat().st_size,'sha256':c.filehash(BUNDLE),'members':len(files),'source_cases':m['source_cases'],'chat_rows':m['chat_rows'],'status':'LOCAL_QA_PASSED_PENDING_CLOUD_RAW_VERIFICATION'}
 c.save(RUN/'balanced_bundle_upload.json',receipt);print(c.dumps(receipt))

def metadata():
 state=c.read(RUN/'working_cloud_state.json');bundleproof=c.read(RUN/'balanced_bundle_readback.json');bookproof=c.read(RUN/'notebook_readback.json')
 for proof,path in ((bundleproof,BUNDLE),(bookproof,RUN/'MathVisionKid_DATA_ONLY_COLAB.ipynb')):
  assert proof['fresh_raw_verified'] and proof['all_bytes_equal'] and proof['sha256']==c.filehash(path) and proof['bytes']==path.stat().st_size
 assert all(d['missing_pairs']==0 and d['EXHAUSTIVE_DOMAIN_COMPLETED'] for d in state['extension_domains'].values())
 old=c.read(RUN/'source_cloud_state.json')
 assert old['parts']==state['parts']
 logical_extra=60+69+16
 assert state['accepted_cases']==old['accepted_cases']+110070
 m=c.read(BALANCED/'MathVisionKid_BALANCED_TRAINING_MANIFEST.json');token=c.read(BALANCED/'qwen_full_selected_token_audit.json');selection=c.read(BALANCED/'selection_receipt.json')
 assert m['TRAINING_DATASET_READY'] and token['status']=='PASSED'
 original_arithmetic=c.read(RUN/'metadata/thinking/data/exhaustive_math_v1/data_build_state.json')
 grade=Counter(original_arithmetic['by_grade']);topic=Counter(original_arithmetic['by_topic'])
 for shard in state['extension_shards']:
  grade.update(shard['grades']);topic.update(shard['topics'])
 # Original fraction/decimal/structural grades are counted from restored source
 # metadata, without rematerializing the arithmetic corpora.
 for family in ('fractions','decimals'):
  for p in (RUN/'preserved_extensions'/family/'corpus').glob('*.jsonl.gz'):
   for r in c.gzrows(p):grade[str(r['grade'])]+=1;topic[r['topic']]+=1
 old_sources=HERE/'data/primary_math_teacher_20261016/exports/accepted_teacher_cases_polished.jsonl'
 for r in readrows(old_sources):grade[str(r['grade'])]+=1;topic[str(r['topic'])]+=1
 for r in readrows(RUN/'preserved_extensions/structural/curriculum_subskill_cases_v2.jsonl'):grade[str(r['grade'])]+=1;topic[str(r['topic'])]+=1
 for p in ('pedagogy_cases_v3.jsonl','boundary_cases.jsonl','holdout_arithmetic_cases.jsonl','holdout_arithmetic_cases_v2.jsonl'):
  for r in readrows(RUN/p):grade[str(r['grade'])]+=1;topic[str(r['topic'])]+=1
 total=state['accepted_cases']+logical_extra
 assert sum(grade.values())==sum(topic.values())==total
 state['accepted_cases']=total;state['new_cases']+=logical_extra
 state['training_chat_rows_before_balancing']=state['training_chat_rows']+216+192
 state['training_chat_rows']=state['training_chat_rows_before_balancing']
 state['all_available_chat_rows_including_evaluation_and_audit']=state['training_chat_rows']+80+32
 state['additional_nonexhaustive_source_cases']={'new_pedagogy_logical_cases':60,'pedagogy_versions_preserved':3,'boundary_cases':69,'new_arithmetic_holdout_sources':16,'selected_arithmetic_holdout_cases':8,'superseded_arithmetic_holdout_audit_only_cases':8,'no_history_deleted':True}
 state['by_grade']=dict(grade);state['by_topic']=dict(topic)
 state['original_logical_domains']=original_arithmetic['logical_domains']
 for d in state['original_logical_domains']:
  d['EXHAUSTIVE_DOMAIN_COMPLETED']=d['missing_pairs']==0
  if d['missing_pairs'] and d['maximum']>=10000:d['status']='BLOCKED_STORAGE_CAPACITY'
 state['storage_preflight']['large_domains']='BLOCKED_STORAGE_CAPACITY'
 state['storage_preflight']['blocking_detail']='Real Drive storageQuota unavailable from current connector. Multi-TB ranges are not started; generated/validated/missing counts and measured gzip estimates remain explicit. Do not infer quota from successful bounded shard uploads.'
 state['storage_preflight']['new_phase_payload_bytes_verified']=sum(s['bundle']['bytes'] for s in state['extension_shards'])+bundleproof['bytes']+bookproof['bytes']
 state['balanced_release']={'bundle':bundleproof,'notebook':bookproof,'manifest':m,'selection_summary':{k:v for k,v in selection.items() if k not in ('selected_case_ids','excluded_cases','input_hashes')},'token_audit':token,'independence_scope':'Only this selected release is approved for training/evaluation. Older immutable candidate chat archives contain disclosed legacy numeric overlaps; do not treat them as the recommended balanced train set.'}
 state['TRAINING_DATASET_READY']=True;state['training_readiness_scope']='BALANCED_SELECTED_VIEW_ONLY'
 state['all_requested_exhaustive_domains_completed']=False;state['training_started']=False;state['gpu_used']=False
 state['status']='BALANCED_TRAINING_DATA_PREPARED_PENDING_FINAL_CONTROL_VERIFICATION_AND_CLEANUP'
 state['updated_utc']=c.utc();state['client_reporting_date']='2026-10-19 Asia/Bangkok'
 state['next_action']='Use data-only Colab notebook to replay loader/tokenizer audit. Do not start training without a separate owner instruction. Large exhaustive ranges require real quota preflight.'
 c.save(RUN/'release_cloud_state.json',state)
 chat=c.read(RUN/'chat.json');chat['archive_parts']=chat.pop('parts');chat['parts']=chat['archive_parts']
 chat['chat_rows']=state['training_chat_rows'];chat['archive_original_chat_rows']=6074308
 chat['extension_zip_shards']=[{'file_id':s['file_id'],'file_name':s['remote_name'],'bytes':s['bundle']['bytes'],'sha256':s['bundle']['sha256'],'chat_member':'chat.jsonl.gz','chat_rows':s['chat_rows'],'source_member':'source.jsonl.gz','cases':s['cases']} for s in state['extension_shards']]
 chat['recommended_training_view']={'bundle':bundleproof,'manifest_member':'balanced_release/MathVisionKid_BALANCED_TRAINING_MANIFEST.json','TRAINING_DATASET_READY':True,'train_validation_test_counts':token['by_split'],'use_train_split_only_for_future_training':True}
 chat['archive_warning']='Original7chatgzip parts and new zip/chat members are preserved candidate archives, not the balanced evaluation-disjoint release. No archive data was deleted to balance the selected release.'
 c.save(RUN/'release_chat_manifest.json',chat)
 report={'source_snapshot_sha256':c.filehash(RUN/'source_cloud_state.json'),'old_cases_preserved':1519171,'new_arithmetic_cases':110070,'new_additional_logical_cases':logical_extra,'new_total_cases':total,'chat_candidate_train_rows':state['training_chat_rows'],'all_chat_rows_including_eval_audit':state['all_available_chat_rows_including_evaluation_and_audit'],'balanced_cases':m['source_cases'],'balanced_chat_rows':m['chat_rows'],'balanced_split_chat_rows':token['by_split'],'all_small_new_domain_missing_pairs':sum(d['missing_pairs'] for d in state['extension_domains'].values()),'new_verified_shards':len(state['extension_shards']),'by_grade':state['by_grade'],'TRAINING_DATASET_READY':True,'EXHAUSTIVE_ALL_REQUESTED_DOMAINS_COMPLETED':False,'no_training_or_gpu':True}
 c.save(RUN/'final_release_report.json',report)
 context=PROJECT/'MATH_TRAINING_CONTEXT.md';text=context.read_text('utf-8');text=text.replace('Cập nhật: 18/10/2026, múi giờ Asia/Bangkok.','Cập nhật: 19/10/2026, múi giờ Asia/Bangkok.',1)
 heading='### Chuẩn bị dữ liệu cân bằng và cloud resume — 19/10/2026\n\n'
 para=(f'**Đã bảo toàn1.519.171bài cũ; thêm110.070bài số học và145case bổ sung, tổng{total:,}case quản lý. Đã chuẩn bị bộ chọn cân bằng {m["source_cases"]:,}case/{m["chat_rows"]:,}chat. Chỉ chuẩn bị dữliệu; CHƯA TRAIN, khôngGPU/modelweights/finetuning/production.**\n\n'
 f'Hoàn tất14shard mới append-only: nhân ordered0..100 loại121cặp cũ=10.080cặp; chia dividend0..100/divisor10..99=9.090; divisor100..999=90.900. Từng cặp/sourceID/oracle/digittrace đã reopen kiểm; cả14ZIP đã freshraw so từngbyte/SHA rồi mới cậpnhật stateID và dọn shardtạm. Mỗi miền mới missing_pairs=0; không biến đó thành hoàn tất hàngtỷcặp10.000/100.000. Miền lớn giữ BLOCKED_STORAGE_CAPACITY: connector không cung cấp quota, còn range/cursor/ước lượng nén trongstate.\n\n'
 f'69boundarycase có chia dài, thương chứa0, nhân nhiều chữ số;60bài sưphạm chọnv3 giữv1/v2audit;16nguồn holdout số học gồm8v1audit và8v2chọn kiểm độc lập. Bốn mode/case đi cùng nhóm. {token["by_split"]} là sốchat train/validation/test của bộ chọn. Toàn bộ {m["chat_rows"]:,}dòng được tokenaudit Qwen3-1.7B revision70d244cc86ccca08cf5af4e1e306ecf908b1ad5e, maxsequence{token["max_sequence_tokens"]}, maxcompletion{token["max_completion_tokens"]}, assistant-onlymask/EOT, khôngsilenttruncation; streaming/resume smokepassed. Không tuyênbố audit token toàn6triệuarchive, modelaccuracy hay đã chạyColabremote.\n\n'
 'Hash/ID/filemanifest: stateID1TLoQIbrRVmgsg-2uiUujCfM3HrK62Yme; chatmanifestID1tkSQoAlxXXRUg2AwYfvqsFKVEmM_LmR6; PROGRESSindexID1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX; contextID13gdIPQTFKcekoQQtgo0TXc7RgeadzIN9. Bộ khuyên dùng là MathVisionKid_BALANCED_COLAB_BUNDLE.zip / balanced_release, không nối tấtcảarchive làmtrain. NotebookMathVisionKid_DATA_ONLY_COLAB.ipynb chỉauthDrive/tokenizer/audit/loader, không cólệnhtrain. Chỉđộc lập giữa cácsplit của bộ chọn; old13ngoạilệ sốhọc còn trongaudit cũ. Sealedchallenge không đọc.\n\n'
 'Nhãn mới ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED, khônghỏi batch, khônggánđộ chínhxácthấp vìnguồnAI, khônggiảnhãnmanualhumanreview;299attestationcũ/hash giữnguyên. Provenancebảndẫnxuất táchhash nguồn/bảnxuất. Nguồn pháp lý2026/27 giữbằngchứng hash cũ, nêuenrichment/pendinggrade khi cần, khôngchứngnhậntoànpháplý/2006. Skills applied: google-drive:google-drive; last30days evidence reused; local skills matched:none.\n\n'
 'Trạng thái tạm: bundle vànotebook đãrawverified;4control phải đồngbộ/xácminh xong trước dọn thưmục staging của đợtnày. Không giữdata mới lâu dài trênmáy; giữduynhấtcontext/codethamchiếuDrive nhỏ.\n\n')
 marker='## Trạng thái hiện tại đã xác minh\n\n';assert marker in text
 text=text.replace(marker,marker+heading+para,1)
 text+='\n\n### Nhật ký19/10/2026 — dữ liệu cloud vàbộ chọnColab\n\n'+para
 context.write_text(text,'utf-8')
 print(c.dumps(report))

def index():
 state=c.read(RUN/'release_cloud_state.json');out=RUN/'MathVisionKid_PROGRESS_CLOUD_INDEX.zip'
 old=HERE/'evidence/primary_math_teacher_20261016/Primary_Math_Teacher_20261016_PROGRESS.zip'
 assert c.filehash(old)=='70071b60a78412b4d8709959414be795d2076fb9d7f71d4547a247e8e714217a'
 files=[(old,'preserved_baseline/'+old.name),(RUN/'release_cloud_state.json','thinking/exhaustive_cloud_reference.json'),(RUN/'release_chat_manifest.json','MathVisionKid_CHAT_PARTS.json'),(RUN/'final_release_report.json','final_release_report.json')]
 for p in HERE.glob('*.py'):
  if any(k in p.name for k in ('exhaustive','cloud_pedagogy','cloud_arithmetic_holdouts','multidigit_boundary','finalize_cloud_resume')):files.append((p,'thinking/'+p.name))
 files.append((HERE/'exhaustive_cloud_storage_policy.json','thinking/exhaustive_cloud_storage_policy.json'))
 ids=HERE/'data/primary_math_teacher_20261016/drive_artifacts.json';files.append((ids,ids.relative_to(PROJECT).as_posix()))
 blueprint=HERE/'data/primary_math_teacher_20261016/curriculum_blueprint.json';files.append((blueprint,blueprint.relative_to(PROJECT).as_posix()))
 for p in (RUN/'commits').glob('*.json'):files.append((p,'cloud_resume/commits/'+p.name))
 for p in RUN.glob('*.json'):
  if p.name not in ('next_cloud_state.json','working_cloud_state.json','release_cloud_state.json','release_chat_manifest.json','final_release_report.json'):files.append((p,'cloud_resume/evidence/'+p.name))
 p=RUN/'pedagogy_reviews.jsonl'
 if p.exists():files.append((p,'cloud_resume/evidence/'+p.name))
 for p in RUN.glob('*output.txt'):files.append((p,'cloud_resume/evidence/'+p.name))
 # Exact source-reference files required by configure_sources(), small only.
 for name in ('curriculum_2026_27_research.json','curriculum_math2018_annex.pdf'):
  p=RUN/'metadata/thinking/evidence/exhaustive_math_20261018'/name
  files.append((p,p.relative_to(PROJECT).as_posix()))
 # Original per-domain counts are metadata, no old gzip corpus materialization.
 p=RUN/'metadata/thinking/data/exhaustive_math_v1/data_build_state.json';files.append((p,'cloud_resume/original_arithmetic_state.json'))
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p,name in files:
   if p.exists():z.write(p,name)
 assert out.stat().st_size<100*1024*1024
 with zipfile.ZipFile(out) as z:assert z.testzip() is None
 c.save(RUN/'progress_index_upload.json',{'path':str(out),'bytes':out.stat().st_size,'sha256':c.filehash(out),'file_name':out.name})
 print(c.dumps({'index_bytes':out.stat().st_size,'members':len(files)}))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['bundle','metadata','index']);a=p.parse_args();globals()[a.action]()
