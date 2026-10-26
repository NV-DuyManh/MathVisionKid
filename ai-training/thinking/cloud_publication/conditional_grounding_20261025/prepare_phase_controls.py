from pathlib import Path
import json,hashlib
from prepare_control_stage import build_stage
P=Path(__file__).parent;CONTEXT=P.parents[2]/'MATH_TRAINING_CONTEXT.md'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
marker='### Nhật ký 25/10/2026 — MCP Hoai và nhánh conditional native'
raw=CONTEXT.read_bytes()
assert marker not in raw.decode('utf8'),'Phase context already appended; inspect rather than duplicate'
note='''

### Nhật ký 25/10/2026 — MCP Hoai và nhánh conditional native
Chủ yêu cầu kết nối MCP qua Hoai và tiếp tục cải thiện model; chủ đã bấm Connect. MCP websocket/client_ready=true, authenticate Drive user Hoai Nam hoainam29082005@gmail.com, notebook1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l; T4 miễn phí15360MiB, không model/worker cũ ở phiên mới. Không dùng Computer Use. Giữ giới hạn tối đa2giờ30phút gần nhất như đã nêu trước launch:02:47:40Z–05:17:40Z ngày25/10 (09:47:40–12:17:40 UTC+7), cutoff train04:47:40Z để dành30phút. Không paid resource hoặc đổi production/app/Git.
Hai lần cài toànmôi trường coincided với VM thay mới; chủ xác nhận không tự đổi/restart. Chưa chứng minh nguyên nhân. Giữ receipts lỗi, không train trong các lần đó. Đổi sang thư viện gốc đã có: Python3.13.16, torch2.11.0+cu130, transformers5.20.2, PEFT0.21.2, accelerate1.15.0; chỉ cài bitsandbytes0.50.2 không dependencies trong venv riêng, runtime sau đó ổn định. Đây là backend native Transformers/PEFT, không claim tốc độ Unsloth.
Khôi phục cloud-only16kchat/4000case source rawSHA14929ba64e5c94d812f1fc3804c771ca8e41fa92285aed3a925282c39b1e4331 và manifestSHA444db8845af0c12bb528795b7e441b996571960dd58ab6898eb9394c77031545. Đủ3input/sourcecode/frozenprimitives/integritystore raw verified đúngIDs. Giữ toàn6502344chat nguồn, nhãn và checkpoint cũ; không tải corpus/model về PC. Derivedview6625chat giữđủ4000worked; lịch gradeinterleave10worked+6hint, không lặpID, không biến việc dedup view thành xóa nguồn. PlanSHAf81524997fdd0b13b1095911feefa2ba37a2f9675df450a626be5553525a5cad.
ConditionalrendererSHA78b4a5c9cfff2e33fc7610461ecab6f57447c079205b62668631f2ca4b665982 chỉ đổi suffixworked; hints/targets giữV3 nguyênbytes. Rebind24source rawrowhash và24targets về actual16k trong cloud trước optimizer; reuse24source semantic reviews và giới hạn của chúng, không claim fullcorpus QA hay humanreview mới. 44CPUtests runtime/policy/renderer PASS;11fourcontroltests PASS. Quá trình soạn code cólỗi newline khi copyfrozenrenderers: gate chặnimport, khôi phục đúngrawbytes, giữdraftlỗi trongauthoring_history trước cloudlaunch.
Một agent gpt-6-luna soạn30development mới, rootđọcđủ30 đề/expected/rubric và sửa8điểm vềmứclớp, ngữcảnh, chia dư và phânbiệtphéptínhđúng với quan hệsai. GiữdraftagentSHA df881b7ae40e37209d78b81e662c98afd89fbdca43ac31cf85759bc7d805ba0f; bảnreviewedSHA450a642e328e232dcfaf7c7d289d45c75203ef5e7ee5c5181e305af159fadd85,6câu/lớp gồm2answer/2hint/1guard/1feedback. FractionchecksPASS. Screen exact/numbermasked vớiactual16k vàprioruseddev30 đều0collision; khôngchứngminh độc lậpfull6.5M. Chỉdevelopment, không vào train. Previousfinals/protected không đọc lại/tune; native15sealSHA0526ec69b5b1730376835c2961d32c79c187f6d1d0fe3057f2d98358b71674f7 chưa infer, chỉreserve finalnếu candidate đủgate.
Worker lầnđầu dừng trước optimizer vì transformersmới để config._commit_hash=None, tokenizerEOSvẫn151645 và cachedconfig/tokenizer/index đềuđúng snapshotrevision70d244cc86ccca08cf5af4e1e306ecf908b1ad5e. Versionedrepair native_backend_v2SHAedacd60755ff5135e9d658662f3427d7410924788a78c7b977fdbf9d199a394f loadtrực tiếp cùngsnapshot local_files_only; worker_v4SHA3ce1b3c24a9741e1f93915930da5552ab41787daa6b13276b0892c7b2a529868 kiểm artifactbinding mới thayfieldprivateđãmất. Khôngđổi revision/đápsố/gate, codev3/lỗi vẫn audit. Activecode3file đã rawDriveverified trước relaunch, proofID1WGq80f4Fo9-Vya0IOzv5qPa9U6936Dn6 SHAe0a6bf26a040edf6dad91861f0b17f9088c1e5ce9c5d41a67b283e00eebc08a7. WorkerPID3092 đang load/auditnguồn lúc03:05:20Z, chưa cóoptimizerupdate đượcquan sát ởmốc này.
Cấu hình mới freshbaseQwen3-1.7B pinnedrevision, NF4doubleFP16, attentionq/k/v/oLoRAr8alpha8, LR3e-6warmup20, micro2effective16, maxseq2048 khôngsilenttruncate, assistant-onlyEOT151645, noGC/noPacking. Cap500updates hoặc1derivedpass (6625rows), gates100/300/500vàEOF; giữbase trongselection, không tiếp tục nếu baselinepassregression/newcritical/newhintleak. Nativefirstmicro sẽ kiểm explicitshiftedCEkhớpforward,finite/nonzeroLoRAgradient trướcoptimizer. Chưa claimmodeltốthơn hoặc đãtrainhết6502344chat.
Runfolder https://drive.google.com/drive/folders/1iP691P_pYTf-Pt_RdGpTZMnDtwjKR4ya; publisherchạyriêngCPU,checkpointbấtbiến/pointerghicuối sau freshrawverify. Update4controlđúngIDs bằngtransaction; chỉreceiptfreshrawđủ4file là bằngchứngsync. Skills applied: plugin-management, google-drive:google-drive. AItraining không matchinginstalledskill trongregistry dựán.
'''
CONTEXT.write_bytes(raw+note.encode())
metadata={'schema':'MathVisionKid.conditional_native_phase_metadata.v1','phase':'WORKER_LOADING_SOURCE_AUDIT_NO_OPTIMIZER_OBSERVED_YET',
 'run_folder_id':'1iP691P_pYTf-Pt_RdGpTZMnDtwjKR4ya','notebook_id':'1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l',
 'budget_start_utc':'2026-10-25T02:47:40Z','hard_deadline_utc':'2026-10-25T05:17:40Z',
 'backend':'native Transformers/PEFT/bitsandbytes','source_rows':16000,'derived_rows':6625,
 'planned_max_passes':1,'planned_max_updates':500,'gate_steps':[100,300,500],
 'optimizer_started_at_last_observation':False,'previous_adapter_loaded':False,'model_improvement_established':False,
 'new_training_cases':0,'new_evaluation_fixtures':30,'human_review_claimed':False,
 'source_and_corpus_preserved':True,'production_approved':False,'paid_resources':False,
 'skills_applied':['plugin-management','google-drive:google-drive']}
(P/'phase_run_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
names=['phase_run_metadata.json','development_root_review.json','development_author_notes.json','code_repair_snapshot_binding.json',
 'native_backend_v2.py','recovery_worker_v4.py','recovery_policy_v2.py','inference_contract.py','conditional_behavior_renderer.py',
 'preparation_code_provenance.json','cpu_validation.json','runtime_identity_01.json','runtime_identity_02.json','runtime_identity_03.json',
 'native_restore_receipt.json','snapshot_repair_receipt.json','connection_status_02.json']
evidence={n:P/n for n in names}
result=build_stage(CONTEXT.read_bytes(),metadata,evidence,P/'publish_phase_controls_runtime.py',
 runtime_root='/content/mathvisionkid_conditional_grounding_20261025',credentials_global='recovery_credentials',
 process_global='conditional_training_process',min_request_interval=1.25)
(P/'phase_control_stage_pins.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='source_hashes'}))
