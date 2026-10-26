from pathlib import Path
import json,hashlib,sys
P=Path(__file__).parent;OLD=P.parent/'conditional_grounding_20261025'
for name in ['prepare_four_controls_runtime.py','four_controls_transaction.py','prepare_control_stage.py']:
 raw=(OLD/name).read_bytes().decode().replace('conditional_grounding_20261025','recovery_20261026').replace('latest_conditional_grounding_branch','latest_recovery_20261026_branch').replace('conditional_grounding_control_publications','recovery_20261026_control_publications')
 dest=P/name
 if dest.exists():assert dest.read_bytes()==raw.encode()
 else:dest.write_bytes(raw.encode())
sys.path.insert(0,str(P));from prepare_control_stage import build_stage
context=P.parents[2]/'MATH_TRAINING_CONTEXT.md';raw=context.read_bytes()
marker='### Nhật ký 26/10/2026 — tiếp tục train trên Hoai, hạn mức140phút'
assert marker not in raw.decode(),'Do not duplicate phase log'
note='''

### Nhật ký 26/10/2026 — tiếp tục train trên Hoai, hạn mức140phút
Chủ yêu cầu nốiMCPChromeNamPerson1 rồi chuyểnlạiHoai do khôngkếtnốiT4được; chủ tựbấmMCP/T4 và yêucầukhôngthao tácchọnhardwarethay. MCPđãclient_ready=true trênHoai; runtime mớifb7636900c84, kernel1225, không cònroot/worker25/10. KhôngdùngComputerUse. Xác thực DriveHoaiNam hoainam29082005@gmail.com, nguồn16kđúngID/hash; khôngtải corpus/modelvềPC. Chỉcài thiếu bitsandbytes0.50.2 --no-deps venvriêng, giữPython3.13.16/torch2.11.0cu130/transformers5.20.2/PEFT0.21.2/accelerate1.15.0.
Chủchọnngânsách140phút gồmchuẩnbị/train/đánhgiá/lưu: bắtđầu08:54:18Z, hạncuối11:14:18Z(18:14:18UTC+7). Chủđổidừngtraintrước18:05 và10phútđánhgiá: cutoff11:04:18Z(18:04:18UTC+7), reserve600s. Giữscope25phútbanđầulàhistory, khôngđổideadline140phút. Gatechấtlượngcóthểkếtthúcsớm; khônghứamodelchắcchắntốthơn hoặcđúng100%.
Chốtđọcđủactual30pairđợt25/10:base14/30,candidate15/30,đápsốsốhọc10/10cảhai nhưngfulltaskanswer10→9,1regressiong2_answer01,3newcriticalclaims,10hintleaksbềnvững. Candidateeligible=false,rootdecisionSTOP; root/peerAIreviewkhônghumanclaim. Códisagreementvềtừđơnvịtươngđối g1 vàcarry2+7,giữcảreview. FullrootreviewđãuploadDriveID1gz9LMFrDvWnbHp5ycOuyQm223i5SGptL vàođúngfoldercũ; chưaclaimrawhashverifychỉvìupload. Checkpoint25/10step100/1600chat/338187supervisedtokens ID1hge3FGqgUPSTEkUx91gngLWsPMkXdSrf vẫnnguyên, khôngblindresumeadapterđãfail. Bộnative15sealSHA0526ec69b5b1730376835c2961d32c79c187f6d1d0fe3057f2d98358b71674f7 chưađọc/infer, protectedV4khôngđọc.
Nhánhmớirecovery_20261026freshbaseQwen3-1.7Brevision70d244cc86ccca08cf5af4e1e306ecf908b1ad5e, khôngnạpadaptercũ. HypothesisthayLoRAattention+MLPq/k/v/o/gate/up/downr16alpha16,peakLR2e-5warmup10,micro2effective16,nonreentrantGC,NF4doubleFP16. Lossmới meanCEassistant-token từngrow rồitrungbìnhrow, chỉselectshiftedlabels!=-100 trướcFP32CE, khôngchấm prompt/padding, model.forwardkhônglabelsđểtránhlossgraphthừa. PreflightCPUsoCEvalue/gradient/maskvớivòngrow PASS; actualfirstmicrocònchờ. Đâyđổiobjective/configcóghi provenance, khôngclaimnguyênnhânregressionđãcôlập.
Source16k/4000casevàtargetsrenderedgiữnguyên; derived6625chatgiữ4000worked+deduphints, mộtpasskhônglặpID;planSHAf81524997fdd0b13b1095911feefa2ba37a2f9675df450a626be5553525a5cad. Rebind24actualsourceQArawrowhash/targetsđúngnguồntrongcloud,khôngclaimđọcnghĩacả16k. Reuse30developmentđãdùngvớifreshbaseoutputvàsamecontract/seed;khônggọiunseen/independent. Khôngdùngoracle/devoutputđểsinhtraintarget. Cap300updates,gates100/300/terminal,giữbase selection; khôngbaseline-passregression/newcritical/newhintleak vàcầnfulltaskgainđểchọnadapter.
WorkerSHA b618f2d961dd0d342f006a8b07abe39268962fc0bdcab43622c425ee2bf67d4f,backendSHA66aa1473bb6835497fb59b16ab0c76e2a609eec0358d9b7cd03f2662e3f3a046,policySHA648a6a8f48ded0bf7cb2615451b895e9b3a7d72bfdd294430ec58ce4029384fd. ModeldownloadchỉofficialpinnedHFcommit vớiallowlistmetadata+indexlistedshards trongColab,local_files_onlysauđó. PublisherfolderID10drqDBNTGy60JBIUqanc9fFHFopCUivq; code/plan/sourceQA/scopeđãfreshrawDriveverifiedlúc09:03:56Z. WorkerPID4050LOADING_FRESH_BASE,step0,training_started=false ởmốcnày; optimizerapprovalHELDchờauditcuối, khôngclaimtrainđãcậpnhậttrọngsố.
Nguyêncorpus6502344chat/labels/history/checkpointcũbảotoàn;chưatrainfullcorpus,khôngpaidresource/production/app/Git. CậpnhậtPROGRESS/chat/state/contextđúngIDs;syncchỉkhi4rawreadbackkhớp. Skills applied: plugin-management,google-drive:google-drive; noinstalledmatchingAItrainingskill.
'''
context.write_bytes(raw+note.encode())
metadata={'schema':'MathVisionKid.recovery_20261026.phase_metadata.v1','phase':'MODEL_LOADING_OPTIMIZER_APPROVAL_HELD',
 'run_folder_id':'10drqDBNTGy60JBIUqanc9fFHFopCUivq','source_rows':16000,'source_cases':4000,'derived_rows':6625,
 'hard_deadline_utc':'2026-10-26T11:14:18Z','train_cutoff_utc':'2026-10-26T11:04:18Z','reserve_seconds':600,
 'optimizer_update_observed':False,'model_improvement_established':False,'prior_adapter_rejected':True,
 'previous_review_drive_id':'1gz9LMFrDvWnbHp5ycOuyQm223i5SGptL','source_and_corpus_preserved':True,
 'human_review_claimed':False,'production_approved':False,'paid_resources':False,
 'skills_applied':['plugin-management','google-drive:google-drive']}
(P/'phase_run_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
names=['phase_run_metadata.json','owner_run_scope.json','root_reviewed_training_plan.json','preparation_provenance.json','recovery_worker_20261026.py','native_backend_20261026.py','recovery_policy_20261026.py','staged_code_pins.json','stage_receipt.json','launch_receipt.json']
evidence={'recovery26_phase/'+name:P/name for name in names}
pins=build_stage(context.read_bytes(),metadata,evidence,P/'publish_phase_controls_runtime.py',runtime_root='/content/mathvisionkid_recovery_20261026',credentials_global='recovery_credentials',process_global='conditional_training_process')
out=P/'publish_phase_controls_runtime.py';code=out.read_text(encoding='utf8').replace('from datetime import datetime,timezone','from datetime import datetime as cg_control_datetime,timezone as cg_control_timezone').replace('datetime.now(timezone.utc)','cg_control_datetime.now(cg_control_timezone.utc)')
out.write_bytes(code.encode());pins['sha256']=hashlib.sha256(out.read_bytes()).hexdigest()
(P/'phase_control_stage_pins.json').write_text(json.dumps(pins,indent=2)+'\n')
print({k:v for k,v in pins.items() if k!='source_hashes'})
