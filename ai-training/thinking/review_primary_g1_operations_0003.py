"""Record a separate content pass; this is not a separate person or teacher."""
import json
from datetime import datetime, timezone
from primary_math_data_pipeline import DEFAULT_ROOT, HERE, REVIEW_FIELDS, read_rows, write_rows, write_json, row_sha, sha, inspect_case, curate


def main():
    path=DEFAULT_ROOT/'authored_batches/g1_operations_0003.jsonl'
    reviews=DEFAULT_ROOT/'reviews/g1_operations_0003_AI_review.jsonl'
    if reviews.exists():
        print('Reviewed batch already exists; do not repeat.');return
    evidence=HERE/'evidence/primary_math_teacher_20261016'
    rows=read_rows(path)
    write_rows(evidence/'g1_operations_0003_before_content_edit.jsonl',rows)
    quantities=['Số bút chì còn trong hộp','Giá trị biểu thức','Giá trị biểu thức','Số hạt còn trong khay',
                'Số chim còn trên sân','Số viên bi xanh','Giá trị đúng của biểu thức','Số quýt còn trong rổ',
                'Số chim còn lại khi chưa có tranh và số liệu']
    notes=[
        'Removed12 from46 gives34, with6>=2 and4>=1 so no borrowing. Inverse restores46. Scenario selects removal rather than joining, matching transfer slot. All three hints withhold34 and each intermediate digit result.',
        'Two additions processed left to right:12→15→19, within100 without carrying. Reuses the first result explicitly and preserves the remaining4. Hints name the sequence of actions without giving15/19. Core01 is add/add, distinct from following mixed-sign slots.',
        'Subtraction then addition gives18→13→15. Contrast identifies why subtracting a combined7 is a different expression. All values nonnegative, no regrouping. Hint progression locates first action, remaining sign, and increase check; no13/15 disclosed.',
        'Addition then subtraction gives31→38→33, with each intermediate quantity named in seeds. Two inverse checks recover38 then31. Core03 transfer is temporal quantity tracking with independent reversal, not just another add/add substitution. No claim of seeing a photograph.',
        'Explicit departure of6 among29 yields23 still on the yard. Direct contrast with arrival explains the operation;23+6=29 checks the partition. Text suffices, but this is not evidence of recognizing birds in an actual image. Hints do not disclose23.',
        'Explicit exhaustive two-colour partition makes36−14=22 identifiable. There is no implicit third colour. Digit reasoning and14+22=36 check are correct without borrowing. Part/whole relation differs from departure case. Hints require identifying whole and known part without answering.',
        'Synthetic written18−5+2=18−7=11 changes an addition to a further subtraction. Feedback refers only to that visible transformation; no invented motor/handwriting diagnosis. Correct path18→13→15 shown, hints withhold13/15. Same math as core02 is intentionally supplemental, training-only shared grouping.',
        'Synthetic25+3=28 is arithmetically correct; the error is choosing addition for removal from the basket. Feedback explicitly distinguishes the two, then25−3=22 and22+3=25. No claim of an unseen child strategy. All hints preserve the required distinction without revealing22.',
        'Missing picture and both initial/departed counts make a numeric answer unidentifiable. Requesting picture OR both counts is sufficient. No numerical answer or fabricated count, no invented image observation. Guard is not credited as a solved core case.'
    ]
    # Independent finite-set simulation, not the AST/reference evaluation used by curator.
    def remove(n,k):
        objects=list(range(n));del objects[:k];return len(objects)
    def append(n,k):return len(['old']*n+['new']*k)
    paths=[[remove(46,12)], [append(12,3),append(append(12,3),4)],
           [remove(18,5),append(remove(18,5),2)],
           [append(31,7),remove(append(31,7),5)],
           [remove(29,6)],[len(set(range(36))-set(range(14)))],
           [remove(18,5),append(remove(18,5),2)],[remove(25,3)],[]]
    expected=[34,19,15,33,23,22,15,22,None]
    decisions=[];checks=[]
    for i,r in enumerate(rows):
        r['requested_quantity']=quantities[i]
        if r['expected_answer']:r['expected_answer'][0]['quantity']=quantities[i]
        if i==6:
            r['worked_steps'][0]['explanation']='Dòng tính đã thay việc cộng 2 bằng bớt thêm 2. Em giữ đúng thứ tự của đề: làm từ trái sang phải, 18 − 5 = 13.'
        if i==7:
            r['worked_steps'][0]['explanation']='Số quýt trong rổ giảm khi lấy ra. Phải tính 25 − 3 = 22, nên còn 22 quả. Ta sửa cách chọn phép tính để diễn tả đúng việc lấy ra.'
        inspected=inspect_case(r);assert inspected['passed'],(r['sample_id'],inspected)
        if expected[i] is not None:
            assert paths[i][-1]==expected[i]==int(r['expected_answer'][0]['result'])
            assert max(paths[i])<=100 and min(paths[i])>=0
        else:assert not r['expected_answer'] and not r['worked_steps'] and r['can_solve'] is False
        decision={'sample_id':r['sample_id'],'row_sha256':row_sha(r),
                  'reviewer':'root_single_assistant_separate_content_review_pass',
                  **{k:True for k in REVIEW_FIELDS},'notes':notes[i],
                  'human_verified':False,'teacher_certified':False,'independent_external_AI_reviewer':False,
                  'review_method':'Full visible-content read after authorship; independent finite-set arithmetic oracle, not a second actor or teacher.',
                  'oracle':{'method':'finite_set_remove_append_or_partition','intermediate_counts':paths[i],'result':expected[i]}}
        decisions.append(decision);checks.append({'sample_id':r['sample_id'],'row_sha256':row_sha(r),'mechanical':inspected,'oracle':decision['oracle']})
    write_rows(path,rows);write_rows(reviews,decisions)
    bp=json.loads((DEFAULT_ROOT/'curriculum_blueprint.json').read_text('utf-8'))
    project=HERE.parent
    frozen={p:sha((project/p).read_bytes())==h for p,h in bp['existing_inputs']['source_fingerprints'].items()}
    assert all(frozen.values())
    state=curate(DEFAULT_ROOT)
    assert state['accepted_cases']==48 and state['chat_train_rows']==192
    assert state['remaining_core_cases']==458 and state['decisions']=={'ACCEPTED_AI_RESEARCH':48}
    write_json(evidence/'g1_operations_0003_verification.json',
               {'created_utc':datetime.now(timezone.utc).isoformat(),'batch_sha256':sha(path.read_bytes()),
                'review_sha256':sha(reviews.read_bytes()),'checks':checks,'frozen_inputs_unchanged':frozen,
                'content_review_is_same_assistant_separate_pass':True,'external_independent_semantic_review':False,
                'human_verified':False,'training_started':False,'sealed_concept_challenge_read':False,
                'result':{k:state[k] for k in ('accepted_cases','chat_train_rows','remaining_core_cases','core_nodes_complete','decisions')}})
    print(json.dumps({k:state[k] for k in ('accepted_cases','chat_train_rows','remaining_core_cases','core_nodes_complete','decisions')}))


if __name__=='__main__':main()
