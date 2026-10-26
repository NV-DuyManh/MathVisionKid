from pathlib import Path
import json,hashlib,sys
P=Path(__file__).parent;sys.path.insert(0,str(P));from prepare_control_stage import build_stage
receipt=json.loads((P/'status_17.json').read_bytes());d=receipt['structured_content'] or receipt['data']
observation=json.loads(''.join(''.join(x.get('text',[])) for x in d['outputs'] if x.get('output_type')=='stream'))
progress=observation['training/progress.json'];cp=observation['latest_checkpoint']
assert progress['step']==100 and cp['step']==100 and cp['fresh_raw_readback_verified']
context=P.parents[2]/'MATH_TRAINING_CONTEXT.md';raw=context.read_bytes();marker='### Nhật ký 26/10/2026 — recovery đạt100updates, chờ kiểm chất lượng'
assert marker not in raw.decode()
note='''

### Nhật ký 26/10/2026 — recovery đạt100updates, chờ kiểm chất lượng
Quan sátthực09:32:15Z workerPID4050alive, đạt100updates/1600uniquechat/338187supervisedtokens,977.7664583giâyoptimizer;loss1.3935910,gradient0.7361421 hữu hạn. Đây0.241509434passcủaview6625,khônghọcfull6502344chat. Firstmicro84supervisedtokens selected-tokenrowCEsoindependentper-rowreferenceabsdiff4.76837158203125e-7; prompt/paddingkhôngchấm,forwardkhônglabels. CPUcodepeerreviewSHA920733c740a7dc3b1023279a65ea1192134428e25a65bc57606f41860de57f34,nguồn24rawhash/targetrebindđủtrướccấpapproval. Khôngthayactiveworker/configsau launch.
Freshbase30câubothEOS,outputcontentkhớp100%theotừngSHA so25/10,cùngfixtures/contract/prompttoken/seed. Rebindđánhgiárootđãđọcactualcontentgiữnguyên14/30fulltask,10/10đápsố,10hintleaks; newfrozenreviewSHA774e6069641d189871e44fb59ee515d530efc794f9e727790581c7dfec5a8344 đãrawDriveverifiedtrướccandidate. Đâydevelopmentđãdùng,khônggọiunseen. Root/peerAIreviewkhônghumanattestation; khôngtạotraindatatừtestoutputs.
Checkpoint1/16 ID1v3w6CBXD4oYvqsOx3GWQqoKIaFA2D_ZB117171216bytesSHAf204da9f5595ca8bf98b21fba8abed80f228ea9329f023dc3a493a8fb596cdd1rawverified09:15:28Z. Checkpoint100/1600 ID133WL9N5iQc_6LTZUULOM9UBlwVhlNTWR117171206bytesSHAb2e86825d1b63c4a5e2c89c66994c8eb7471015d73f80b66356f62e30b86fe03manifestSHAf6aaee3af373a3899ad4cec0c87be006f1350cea0bde87ee18c1135469fc91a7rawverified09:30:58Z. Pointerghicuốisauproof, nguồn/corpushistory/oldCPgiữ.
PublisherlúcđầudừngIntegrityErrorvìworkerghi đèlại dev_train_screening thànhsource-only trongkhibảnsource+prior-screen đãimmutableuploaded. FreshDrivereadbackxácminhbản430bytesSHAf11938e566bd4d7bc032d818d6697939586dd1bc9734934fc46f63f7c5b5074f; sourcepartkhớpsemanticbảnworkerf05a3236...,cảhaizero-collisions. Giữerrorhistoryvàbảnworker,khôiphụcđúngrawbảnfullscreenchopublisher,rồichỉrestartpublisher;khôngđổiđề/đápsố/target/gates/train/runtime. PublisherhiệnRUNNING,cácerrorcũlàhistory. Standaloneprior25reviewDriveID1gz9LMFrDvWnbHp5ycOuyQm223i5SGptL đãfreshrawreadback30486byteskhớplocalSHAởapproval26.
Mốc100đangtạo30candidateoutput,chưađủsemanticgate; khôngchạyupdates>100khi chưa rootreview đủactual30pairs vàhash-boundgate. Khôngclaimmodelđãtốthơn,khônglấylossgiảmlàproof. Hạntrain11:04:18Z/hard11:14:18Z,reserve600sgiữđúngyêucầumới. FourcontrolphasepreviousđãCOMPLETE_RAW_VERIFIED4file,receiptSHA644ba5c3d809fe55f900f03d4388b3dbb6d74acf9d6e3b173d5c49a6fe5cf8e5; phasehiệntạicầnsyncrawmới. Skills applied:plugin-management,google-drive:google-drive.
'''
context.write_bytes(raw+note.encode())
metadata=json.loads((P/'phase_run_metadata.json').read_bytes());metadata.update({'phase':'ACTUAL100_UPDATES_CANDIDATE_REVIEW_PENDING','optimizer_update_observed':True,'actual_successful_updates':100,'actual_unique_chat':1600,'actual_supervised_tokens':338187,'checkpoint_100':cp,'baseline_frozen_sha256':hashlib.sha256((P/'baseline_semantic_review_frozen.json').read_bytes()).hexdigest(),'model_improvement_established':False})
(P/'training_run_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
names=['training_run_metadata.json','baseline_semantic_review_frozen.json','baseline_content_comparison.json','independent_preoptimizer_review.json','optimizer_approval_receipt.json','screening_repair_receipt.json','status_17.json']
pins=build_stage(context.read_bytes(),metadata,{'training100/'+n:P/n for n in names},P/'publish_training_controls_runtime.py',runtime_root='/content/mathvisionkid_recovery_20261026',credentials_global='recovery_credentials',process_global='conditional_training_process')
out=P/'publish_training_controls_runtime.py';code=out.read_text(encoding='utf8').replace('from datetime import datetime,timezone','from datetime import datetime as cg_control_datetime,timezone as cg_control_timezone').replace('datetime.now(timezone.utc)','cg_control_datetime.now(cg_control_timezone.utc)');out.write_bytes(code.encode())
pins['sha256']=hashlib.sha256(out.read_bytes()).hexdigest();(P/'training_control_stage_pins.json').write_text(json.dumps(pins,indent=2)+'\n');print({k:v for k,v in pins.items() if k!='source_hashes'})
