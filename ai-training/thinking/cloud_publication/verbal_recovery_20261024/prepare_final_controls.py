from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
from prepare_control_stage import build_stage
p=Path(__file__).parent;ctx=p.parents[2]/'MATH_TRAINING_CONTEXT.md'
def read(n):return json.loads((p/n).read_bytes())
report=read('final_semantic_assessment.json');pub=read('metadata_finalized/publication__publication_status.json');fe=read('metadata_finalized/final_eval_publication_status.json')
assert pub['state']==fe['state']=='COMPLETE_RAW_VERIFIED'
assert all(x['fresh_raw_readback_verified'] for x in fe['artifacts'].values())
proof=pub['artifacts']['training/final_semantic_assessment.json'];h=hashlib.sha256((p/'final_semantic_assessment.json').read_bytes()).hexdigest()
assert h==proof['sha256'] and proof['fresh_raw_readback_verified']
s=report['development_validation']['summary'];t=report['locked_final_test'];m={**report['training']['metrics'],'training_seconds':report['training']['training_seconds']}
assert m['step']==50 and m['rows_done']==800 and m['supervised_tokens']==169406
marker='### Nhật ký 24/10/2026 — kết thúc thử biểu diễn văn bản, không promote adapter'
if marker.encode() not in ctx.read_bytes():
 text='\n\n'+marker+'\n'
 text+='Chốt lúc '+datetime.now(timezone.utc).isoformat()+'. Nhánh verbal_recovery_20261024 chạy fresh base Qwen/Qwen3-1.7B revision70d244cc86ccca08cf5af4e1e306ecf908b1ad5e, NF4/FP16, LoRA r16 alpha16, microbatch2/effective16, LR1e-5 warmup10, không packing/GC. Giữ nguyên lịch lấy mẫu và nội dung toán; chỉ đổi renderer prompt/target sang văn bản. So sánh base và adapter trong đúng contract mới, không dùng điểm raw của contract JSON trước để suy nguyên nhân.\n'
 text+='Thực tế '+str(m['step'])+' updates, '+str(m['rows_done'])+' chat unique, '+str(m['supervised_tokens'])+' supervised tokens, '+str(m['training_seconds'])+' giây optimizer; 800/6625 của derived view, không phải học hết6502344 chat. Worker đã exit0; final-stage STOP, không tự train thêm.\n'
 text+='Đọc đủ30 actual pairs và ghi lý do/hash: strict full-task base '+str(s['base']['total'])+'/30, adapter '+str(s['candidate']['total'])+'/30; answer '+str(s['base']['answers'])+'/15 → '+str(s['candidate']['answers'])+'/15; baseline-pass regressions '+str(s['baseline_pass_regressions'])+', new critical '+str(s['new_critical_errors'])+', new hint leaks '+str(s['new_hint_leaks'])+'. Candidate eligible=false; giữ untrained base. Adapter có câu sửa được nhưng làm sai phần trăm100% thành105%, lộ đáp số hint và có câu lặp đến token cap. Không lấy loss giảm hoặc tổng điểm tăng riêng lẻ để kết luận adapter an toàn hơn.\n'
 text+='Sau khi khóa lựa chọn, infer bộ20 mới đúng1 lần; selected alias dùng nguyên output base, adapter bị loại không được test lại. Strict full-task '+str(t['counts']['total']['pass'])+'/20, theo mode '+json.dumps(t['counts']['by_mode'],ensure_ascii=False)+', hint leaks '+str(t['counts']['hint_leaks'])+'. '+str(t['completed_eos_count'])+'/20 hoàn tất EOS, các câu khác nếu có được ghi đúng trạng thái. Câu10034÷33 là probe chủ đã nêu, không coi là unseen generalization; kết quả chấm '+str(t['owner_requested_division']['review']['selected_pass'])+'. Không dùng kết quả final test để chọn lại hoặc train lại. Bộ test chỉ screen với actual16k, chưa chứng minh độc lập toàn corpus6.5M.\n'
 text+='Audit forward loss6 đo trên3 microbatch train × base/prior adapter: manual next-token CE khớp actual forward loss, max abs error '+str(report['loss_alignment_audit']['max_abs_next_token_loss_error'])+'. Không phát hiện lệch shift ở mẫu đã đo; chưa chứng minh toàn stack đúng và chưa cô lập nguyên nhân regression. Renderer đã fail-closed với field lạ, giữ nội dung toán/đơn vị/kiểm; không đổi nguồn AI thành người viết hoặc mở rộng owner signoff cho bytes dẫn xuất.\n'
 for cp in pub['checkpoints'].values():text+='Checkpoint step'+str(cp['step'])+' ID'+cp['id']+' SHA'+cp['sha256']+', bytes'+str(cp['bytes'])+', fresh raw readback verified.\n'
 a=pub['final_artifacts']['last_adapter_diagnostic.zip'];text+='Adapter diagnostic ID'+a['id']+' SHA'+a['sha256']+', raw verified, giữ làm audit, không promote.\n'
 text+='Báo cáo cuối ID'+proof['id']+' SHA'+h+', bytes'+str(proof['bytes'])+', fresh raw readback verified; https://drive.google.com/file/d/'+proof['id']+'/view. Run folder https://drive.google.com/drive/folders/'+pub['folder_id']+'. Final evaluation '+str(len(fe['artifacts']))+' file đã raw verified. Toàn bộ corpus/labels/checkpoint cũ giữ nguyên, không tải corpus/model về PC, không paid resource hoặc sửa production. Chưa có adapter mới được chứng minh cải thiện đủ an toàn; base cũng còn lỗi, chưa là tutor đã đạt nghiệm thu sản phẩm. Skills applied: google-drive.\n'
 with ctx.open('ab') as out:out.write(text.encode('utf8'))
names=['final_semantic_assessment.json','record_dev_review.py','assemble_review_gate.py','build_final_assessment.py','record_final_reviews.py','prepare_final_controls.py','finalize_publication_runtime.py','start_final_evaluation_runtime.py','final_evaluation_worker.py','test_final_evaluation_worker.py','verbal_training_renderer_v3.py','trial_scope.json','projection_preflight.json','forward_loss_audit.json','code_pins.json','cpu_validation.json','metadata_finalized/publication__publication_status.json','metadata_finalized/final_eval_publication_status.json','metadata_finalized/final_eval__final_eval_manifest.json']
names += ['review_step_000050/'+n for n in ['root_gate.json','semantic_g1_g2.json','semantic_g3_g4.json','semantic_g5.json']]
names += [f'final_review/semantic_g{g}.json' for g in range(1,6)]
evidence={'evidence_final/'+n:str((p/n).resolve()) for n in names}
evidence['evidence_loss_audit/target_loss_audit_worker.py']=str((p.parent/'quality_recovery_20261024'/'target_loss_audit_worker.py').resolve())
for n in ['test_four_controls_runtime.py','test_verbal_training_renderer_v3.py','locked_test_binding.json','locked_test_notes.json']:
 evidence['evidence_final/'+n]=str((p/n).resolve())
meta={'branch':'verbal_recovery_20261024','phase':'FINAL_SEMANTIC_CLOSEOUT','status':report['status'],'new_adapter_improvement_demonstrated':False,'selected_kind':'untrained_base','actual_steps':50,'actual_unique_chats':800,'supervised_tokens':169406,'training_seconds':m['training_seconds'],'dev_base_fulltask':s['base']['total'],'dev_adapter_fulltask':s['candidate']['total'],'dev_count':30,'locked_selected_fulltask':t['counts']['total']['pass'],'locked_count':20,'final_report_proof':proof,'source_data_or_labels_modified':False,'production_approved':False,'further_training_started':False,'next':'STOP; retain all artifacts. Diagnose behavior retention and prompt/target distribution before any later long run.'}
(p/'final_run_metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(p/'final_control_evidence_map.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
result=build_stage(ctx.read_bytes(),meta,evidence,p/'publish_final_controls_runtime.py',process_global='verbal_process')
print(json.dumps({'context_bytes':ctx.stat().st_size,'context_sha256':hashlib.sha256(ctx.read_bytes()).hexdigest(),'stage':{k:v for k,v in result.items() if k!='source_hashes'}},ensure_ascii=False))
