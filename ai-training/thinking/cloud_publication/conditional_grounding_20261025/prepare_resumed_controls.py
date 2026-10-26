from pathlib import Path
import json,hashlib
from prepare_control_stage import build_stage
P=Path(__file__).parent; context=P.parents[2]/'MATH_TRAINING_CONTEXT.md'
marker='### Nhật ký 25/10/2026 — phục hồi bộ nhớ và baseline đã khóa'
raw=context.read_bytes();assert marker not in raw.decode('utf8'),'Already appended; do not duplicate'
note='''

### Nhật ký 25/10/2026 — phục hồi bộ nhớ và baseline đã khóa
Worker v4 đã thực sự train6updates/96chat rồi OOM ởmẫu dàihơn, không phải chưa train. Log/error/progress v4 đượcgiữ error_history/attempt_0002_native_OOM. Checkpoint commitcuối step1/16chat, generationmanifestSHA7b9fe87846255e4cc31b1d732c591de18c4d7dcaa5acb9c8fa04d6fd06d9fdee, DriveID1NOkLIubccEzcDNt5cm72FlBBPEe9Ll7K, ZIP31150368bytesSHA5254bdff7ccd5f85ff44967082515b9b6f50d5004378b95b25af65674ea94551 đã freshrawverified rồi reread trước resume. Không nhận5updates/80chat mấtđuôi làtrọngsố đãkhôi phục; extraexposures lưu riêng, không cộng thànhunique.
Giữruntime, thayfreshworkerprocessPID6987 từCP1, không restartVM. Versionedv5SHA8905c8f5feb9ba3df1905d3a2fdb304f5d905b7867adb358abb46825cf1362b0/backendv3SHAfd4b342388b97004fc5e947abcab4084a4e41e3042856dd0061b20e92489daff chỉbật gradientcheckpointingnonreentrant, cachefalse; configmô tảloss đượcđính chính thành row-count-weighted microbatch tokenmeans, objectivecodekhông đổi. Khôngđổi LR3e-6/effective16/micro2/source/targets/schedule/eval/gates. MigrationSHA930a1475212f4cafd7970e02996cbfd465b374480ab42b5eb8fbec935212c469 và code đã rawDriveverified trướclaunch.
Actualread-onlyruntimeproof03:24:07Z xácnhận argv đúngCP1, parentmanifestSHA, v5/backendv3filehash, diffconfigchỉworker/GC/lossdescription/migrationSHA, restoredcursor16 vàverifiedprefixSHA7b7c238ae3e95eb59472223298c826c62d345de108526cfbdd62cf7df6e332e2; tail5984bytes đượcgiữaudit. Optimizer/scaler/CPU-CUDA-PythonRNG vàparameter mappingđượcrestore. Resumedfirstmicro77supervisedtokens: explicitshiftedCE−forwardabsdiff0.0. Workerđãtiếptục26updates/416chat,86796supervisedtokens,loss3.7864053/gradient2.4405022 hữu hạn, train_seconds208.0 ởmốc này. Metrics làsnapshot cótimestamp, không lời hứatiếnđộlive sauđó.
Agentstaticreview ghi3hardeninggaps receiptbinding trongworker: không tựenforceexactCPidentity/backendhash/exactlossstring. Actualcloudproofđãđối chiếunhữnggiá trịcụthểcủarunnày; không sửaactivecode trongkhitrain. KhôngclaimproofintrospectPythonbytestrongRAM. PhiênGC cóthểkhácquỹđạosốnhỏ doFP16recompute, gategiữnguyên.
Rootđọcactual30baseline trướccandidate, khóaSHAf8c5840d99f950c261db0839234a6c30830cd9758bb55e056e171394376527ff, rawDriveID1gAs_fmIwC4DnJSGxJypy8TKaf7qAvwIk. Baseline14/30fulltask,10/10đápsốđúng,0/10hintđạt(10leak),0/5guardđạt,4/5feedbackđạt. Agentreview13/30khác1câu g3_answer02 vìheaderplaceholderthừa; rootgiữđánhgiápass chođápsố/lờigiảiđúngvàkhônggánbướchọcsinhcụthể. Disagreementlưu baseline_review_adjudication.json, khôngđổibaseline saucandidate. Khôngsuytỷlệ30câuthànhđộchínhxáctoànchươngtrình; chưaclaimmodeltốthơn.
Nguồn6502344chat/checkpointcũ/nhãn giữnguyên, corpus/model khôngtảiPC. Lịch6625chat mộtpassvàngânsách05:17:40Zkhôngđổi; gate100đangchờ. Fourcontrols cậpnhậtđúngIDs, chỉreceiptfreshrawđủ4file mới tuyênbốsync.
'''
context.write_bytes(raw+note.encode())
metadata=json.loads((P/'phase_run_metadata.json').read_bytes())
metadata.update({'phase':'MEMORY_RECOVERED_TRAINING_OBSERVED','optimizer_started_at_last_observation':True,
 'observed_utc':'2026-10-25T03:24:07Z','observed_step':26,'observed_rows':416,'observed_supervised_tokens':86796,
 'gradient_checkpointing':'nonreentrant','resumed_from_step':1,'prior_failed_attempt_last_step':6,
 'lost_tail_updates':5,'lost_tail_extra_exposures':80,'baseline_full_task_pass':14,'baseline_denominator':30,
 'baseline_answer_pass':10,'baseline_answer_denominator':10,'baseline_hints_leaked':10,
 'model_improvement_established':False,'baseline_semantic_review_frozen_sha256':hashlib.sha256((P/'baseline_semantic_review_frozen.json').read_bytes()).hexdigest()})
(P/'resumed_run_metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
names=['resumed_run_metadata.json','memory_resume_migration.json','memory_resume_code_review.json',
 'memory_live_proof_receipt_02.json','baseline_semantic_review_frozen.json','baseline_review_adjudication.json',
 'recovery_worker_v5.py','native_backend_v3.py']
evidence={'resume_update/'+name:P/name for name in names}
out=P/'publish_resumed_controls_runtime.py'
pins=build_stage(context.read_bytes(),metadata,evidence,out,credentials_global='recovery_credentials',process_global='conditional_training_process')
text=out.read_text(encoding='utf8').replace('from datetime import datetime,timezone','from datetime import datetime as cg_control_datetime,timezone as cg_control_timezone').replace('datetime.now(timezone.utc)','cg_control_datetime.now(cg_control_timezone.utc)')
out.write_text(text,encoding='utf8');pins['sha256']=hashlib.sha256(out.read_bytes()).hexdigest();pins['bytes']=out.stat().st_size
(P/'resumed_control_stage_pins.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in pins.items() if k!='source_hashes'}))
