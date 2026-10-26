"""Update the one context file after the completed thinking review."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent
context = root.parent/'MATH_TRAINING_CONTEXT.md'
review = root/'evidence'/'teacher_math_v3_20261013'/'full_thinking_semantic_review'
report = json.loads((review/'final_thinking_review.json').read_text(encoding='utf-8'))
assert report['visible_outputs_reviewed'] == 524 and report['semantic_review_complete']
verification = json.loads((review/'drive_final_artifact_verification.json').read_text(encoding='utf-8'))
assert len(verification) == 3 and all(item['raw_equal'] for item in verification)
old = context.read_text(encoding='utf-8')
start = old.index('## Trạng thái hiện tại đã xác minh')
end = old.index('### Đợt đang thực hiện — teacher_math_v3, 13/10/2026', start)
latest = '''## Trạng thái hiện tại đã xác minh

**FULL_THINKING_REVIEW_COMPLETE — 13/10/2026.** Đã hoàn tất inference và audit262baseline+262candidate; đọc/review đầy đủ524 visible outputs bằng ba reviewer AI riêng cho hint/guard, baseworked và candidateworked. Không trainV4 trong lịch theo dõi. Heartbeat `nh-gi-thinking-mathvisionkid-sau-colab` đã DELETE thành công sau khi báo cáo/evidence được lưu và verified readback; không còn tự chạy lại training/evaluation này. Lịch kiểm các mốc trước nằm tại `thinking/evidence/teacher_math_v3_20261013/full_thinking_monitor.json`.

Model pinned Qwen/Qwen3-1.7B revision70d244cc86ccca08cf5af4e1e306ecf908b1ad5e; adapter20e99388093c5f7caa1aacaac2a6014cdc0bfd4b4b1bb6f25b5a593ea8beae8d. Protocol thinking sampling0.6/top_p0.95/top_k20/seed20261013/batch4/cap2048. PID10673 đã kết thúc (Zs), statecompleted_numeric_comparison, GPU3MiB/0% tại mốc06:24UTC; không dùng PID lịch sử để restart. Primary greedy selection cũ vẫnbase. Thinking adapter cũng bị từ chối bởi gate giữ raw số/unit từnglớp: tổng có tiến bộ nhưng lớp3/4 giảm. Không chấp nhận model nào để hướng dẫn học sinh tự động; production_approved=false, standalone_student_tutor_approved=false.

| Chỉ số trên validation phát triển | Base thinking | Adapter thinking |
|---|---:|---:|
| Raw số đúng |165/173 (95,4%)|167/173 (96,5%)|
| Raw số và đơn vị đúng |101/173 (58,4%)|164/173 (94,8%)|
| Strict đúng đáp số+unit |88/173|161/173|
| Strict reference-path solution_verified |1/173|134/173|
| AI review worked: nội dung toán/lời giải đúng |150/173|149/173|
| AI review worked: hướng dẫn hữu ích |129/173|145/173|
| Worked đạt toàn bộ common+method/grade/usefulness criteria |109/173|137/173|
| AI review hint hữu ích, đúng, đúnginstruction và khônglộđáp số |0/59|15/59|
| Hint lộ đáp số |58/59|30/59|
| Guard đúng nội dung |21/30|24/30|
| Guard đạt toàn bộ instruction/grounding/grade criteria |0/30|20/30|
| Output truncated toàn262 |2|4|

Guard/hint0 đạt toàn bộ không có nghĩa không lý do hay phép tính nào đúng. Semantic/math-intent review và aliases thủ công là supplemental; không thay rawmetric. Strict1/173 của base là reference/schema/pathscore, không có nghĩa base chỉ biết giải1bài. Adapter có18bài raw đáp số đúng nhưng semantic giải thích sai;19workedsevere vsbase21. Một phương pháp chia trước để tính diện tích hình thang có số đúng, nhưng lời bước cuối gọi nửa tổng là tổng và còn nói chiahai; parent đọc/adjudicate hai mẫu123/125, giữnonsevere semanticfail.

| Lớp gán kỹ thuật | Base raw số | Adapter raw số | Base AIworkedsemantic | Adapter AIworkedsemantic |
|---|---:|---:|---:|---:|
|1|15/15|15/15|13/15|14/15|
|2|15/15|15/15|15/15|15/15|
|3|38/38|36/38|36/38|30/38|
|4|35/36|32/36|32/36|25/36|
|5|62/69|69/69|54/69|65/69|

Paired raw số:159cảhaiđúng,8adapter-only,6base-only; tăng tổng2bài trong mộtseed, chưa chứng minh tăngtríthôngminh ổnđịnh. Canonicalunit:98cảhaiđúng,66adapter-only,3base-only,6cảhaisai. Lỗi điển hình:12giờ hoạt động+30phút nghỉ bị trừ thành690 thayvì cộng750; dãy bội76,152 bị nhânđôi thành304 thayvì228; kết quả học sinh605904+357733=963638 bị chấpnhận dù đúng963637; phép chia dùng result là dư cho expression toànphépchia; explanation cột nhớ/mượn và lời chia phân số bị sai. Một số đề được gánlớp3 còn có số/phépnhân vượt mức đãmapping (vd263kg→263000g, diện tích nhân2số2chữsố); phải rà chất lượng dữ liệu/gánlớp trước V4, không nhận đó là lỗi riêng của model hoặc đã bao phủ chương trình chính thức.

Sensitivity bổsung261 bỏ duy nhất valID91d23b441cd60a087952fa5c:172worked+59hint+30guard. Raw base164/172số,101/172số+unit; adapter166/172số,163/172số+unit. Gate từnglớp vẫnfail, selectionprimary262 khôngđổi. Chỉ bỏ mộtknownoperation-equivalentcollision, không chứngminh zero semantic leakage toànbộdataset.

Evidence local: `thinking/evidence/teacher_math_v3_20261013/full_thinking_readback` chứa16file raw đầyđủ; `full_thinking_semantic_review` chứapacket/audit,173base+173candidate+178hintguard decisions, hợpnhất524, numeric_and_sensitivity_report.json vàfinal_thinking_review.json. Source/dataprotocol frozen khôngđổi; reviewhelper14tests vàactualtokendecode/scores/metadata/summaryaudit PASS. Semanticreview làAI research, human_verified=false, teacher_certified=false; chỉ1seed trênAI-authoreddevelopmentval saupilot, chưabenchmark giáo viên giữkín/chưa gầnassistant/chưaOCR hoặcmọichươngtrình.

Báo cáo Drive: https://drive.google.com/file/d/11NUDecwbtP8An8F3ZHetNETBcKCsgpwD/view . ZIP review (351255bytes, SHA134481cc011e88f09f95933f5e7dc38b92b628fe4cf61bf954225067ad460f5b) https://drive.google.com/file/d/1Jcom-Whz31z4lpeFDvqygXVFTOPgFpcl/view . ZIP gồmvisiblepacket/decisions/protocol/report, khôngweights/hidden think; không nhận làmodeldeployable. ReportSHA8cb8d7aa502c3eba58d5dd8302ef975804fd108ee17a9789e6b730b9cbe37422; notebook70cellSHA9a653d13322bb5184ad247d3eee099569f100923415464a4631f9f63453ef775 đãsave cùngID17aUDHsE5hyYeDCFb3Z-iG8hRnGwvfcZM. Rawreadback cả3artifact bytes khớp;8OCRobjectgốc giữnguyên.

Bước tiếp theo cụthể: rà/sửa gánlớp và wording của training data trongversionmới; tạo ví dụteacher mới đúng từng cột, phépchia/phânsố vàvai trò dữkiện, khôngnhét nguyên câu/đáp sốvalidation vào train; tăng dữliệu hint1câuhỏi khônglộđáp án vàguardthiếudata; review lại4170numeric replay+330concept current/legacy vàLR2e-5 trướcfreezeV4. Đánhgiá outputconcise vàthinkingbudget riêng; arithmeticverifier khôngđược sửa rawmodelmetric. Dùng bài thực tế độc lập giáo viênduyệt đểđo chấtlượng;conceptchallenge50vẫn chưađọc/chưadùng. V4vẫnPREPARATION_ONLY. Khôngcommit/push/production, khôngtrainingmới trong đợtđánhgiánày.

Skills applied: google-drive:google-drive (artifact sync/rawreadback), openai-docs (lịchfollow-up); workspace ML skills matched:none. Báo cáo chỉtại fileMDngữcảnhnày, evidenceJSON/JSONL riêng.

### Lịch sử đợt teacher_math_v3, 13/10/2026 — các mốc trước khi hoàn tất review
'''
old_heading = '### Đợt đang thực hiện — teacher_math_v3, 13/10/2026'
text = old[:start]+latest+old[end+len(old_heading):]
text += '''

## Nhật ký 13/10/2026 — full thinking review hoàn tất

Đã hoàn tất audit cả262+262, review524visible, kiểmhashpercase/source, recompute coverage/booleans/counts và đónggóiZIP26members verifiedhash. Giữfrozenprimarygreedyselectionbase, từchối thinkingadapter bởi retentiontừnglớp và chưaphùhợpstudenttutor. Đãuploadreport/ZIP vàsave70cellnotebook cùngIDs, rawreadback3artifact khớp. Heartbeat đãdelete thànhcông sau khi hoàn tất báo cáo. Context được cậpnhật/syncchínhfile này. Mainmục tiêu model lớp1–5 giỏi/chính xác gầnassistant chưađạt; phaseđánhgiá này đãxong, V4chưatrain. Không dùngsemanticAIreview làmhumangold, khônglộhiddenthinking, khôngsửa source/data/curriculumfrozen.
'''
context.write_text(text,encoding='utf-8',newline='\n')
print(json.dumps({'context_bytes':context.stat().st_size,'review_outputs':524,'automation_deleted':True}))
