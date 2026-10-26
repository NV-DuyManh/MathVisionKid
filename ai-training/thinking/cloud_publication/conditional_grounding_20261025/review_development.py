from pathlib import Path
from fractions import Fraction
import hashlib,json

p=Path(__file__).parent
path=p/'development_candidates.jsonl'
raw=path.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='df881b7ae40e37209d78b81e662c98afd89fbdca43ac31cf85759bc7d805ba0f'
history=p/'authoring_history';history.mkdir(exist_ok=True)
(history/'development_candidates_agent_original.jsonl').write_bytes(raw)
rows=[json.loads(x) for x in raw.splitlines()]
by_id={x['id']:x for x in rows}
edits={
 'dev25_g1_hint_no_answer_02':('Trên cành có 14 chiếc lá. Sau đó 6 chiếc rụng xuống. Hỏi trên cành còn bao nhiêu chiếc lá?',None,'Clarify initial/final time; not an already-included fallen subset.'),
 'dev25_g2_answer_01':('Một khay có 5 hàng bánh, mỗi hàng có 4 chiếc. Hỏi khay có tất cả bao nhiêu chiếc bánh?','20 chiếc bánh','Use familiar grade2 five-times table.'),
 'dev25_g2_student_error_01':('Có 2 đĩa, mỗi đĩa có 7 quả mận. Minh viết: “2 + 7 = 9 quả mận.” Hãy nhận xét đúng dòng Minh đã viết.','Phép cộng 2 + 7 = 9 đúng về số học, nhưng không biểu diễn tổng số quả. Có 2 nhóm, mỗi nhóm 7 quả nên cần 2 × 7 = 14 quả mận.','Distinguish true arithmetic from wrong relation; grade2 two-times table.'),
 'dev25_g3_answer_01':('Có 123 nhãn vở chia đều vào 5 túi, sao cho mỗi túi nhận nhiều nhãn nhất và còn thừa ít hơn 5 nhãn. Hỏi mỗi túi có bao nhiêu nhãn và còn thừa bao nhiêu nhãn?','Mỗi túi 24 nhãn, thừa 3 nhãn. Kiểm: 5 × 24 + 3 = 123 và 0 ≤ 3 < 5.','Add division-with-remainder and reconstruct/check constraints.'),
 'dev25_g4_answer_01':('Một dải giấy dùng để trang trí. Buổi sáng dùng 7/12 m, buổi chiều dùng thêm 1/6 m. Hỏi hai buổi dùng tất cả bao nhiêu mét giấy?','3/4 m','Replace grade5 decimal topic by grade4 fraction addition.'),
 'dev25_g4_hint_no_answer_01':('Một bình ban đầu có 7/8 l nước. Gia đình uống 1/4 l. Hãy tìm lượng nước còn lại.','Gợi ý: Đổi hai phân số về cùng mẫu số, rồi lấy lượng ban đầu trừ lượng đã uống. Giữ đơn vị lít.','Grade4 fractions; no final numerical answer in hint.'),
 'dev25_g4_missing_or_contradictory_info_01':('Một tấm bìa hình chữ nhật dài 15 cm. Dòng thứ nhất ghi chiều rộng 8 cm; dòng thứ hai ghi chiều rộng 6 cm. Hỏi diện tích tấm bìa là bao nhiêu?','Hai giá trị chiều rộng mâu thuẫn. Cần kiểm tra chiều rộng là 8 cm hay 6 cm trước khi chọn một diện tích duy nhất.','Replace grade5 velocity with grade4 area/contradiction; do not pick value arbitrarily.'),
 'dev25_g4_student_error_01':('Một sợi dây dài 3/4 m, đã dùng 1/8 m. Hà viết: “3/4 - 1/8 = 5/8 m còn lại.” Hãy nhận xét đúng dòng Hà đã viết.','Dòng của Hà đúng: 3/4 = 6/8 nên 6/8 - 1/8 = 5/8 m.','Grade4 fraction subtraction and correct supplied work acceptance.')}
for sid,(problem,expected,reason) in edits.items():
 row=by_id[sid];row['userproblem']=problem
 if expected is not None:row['expected_answer']=expected
 row['rubric']=[reason,'Respect actual quantities/units; do not invent student steps. For worked solutions explain the relation and verify. For hints give a useful next step without the final answer.']
checks={'g2_product':Fraction(5)*4==20,'g2_feedback':Fraction(2)*7==14,
 'g3_division_reconstruction':5*24+3==123 and 0<=3<5,
 'g4_fraction_add':Fraction(7,12)+Fraction(1,6)==Fraction(3,4),
 'g4_hint_oracle':Fraction(7,8)-Fraction(1,4)==Fraction(5,8),
 'g4_feedback':Fraction(3,4)-Fraction(1,8)==Fraction(5,8)}
assert all(checks.values())
data=''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in rows).encode()
path.write_bytes(data)
review={'schema':'MathVisionKid.development_root_author_review.v1','fixture_count':30,
 'agent_original_sha256':hashlib.sha256(raw).hexdigest(),'reviewed_raw_sha256':hashlib.sha256(data).hexdigest(),
 'all_30_actual_problems_expected_answers_and_rubrics_read':True,
 'root_grade_and_semantic_edits':{k:v[2] for k,v in edits.items()},'exact_checks':checks,
 'review_nature':'Root LLM review plus exact arithmetic; no human/external credential claim.',
 'model_outputs_seen_before_authoring':False,'model_inference_on_this_set_performed':False,
 'use':'development evaluation only; never training targets','independence_scope':'Needs cloud exact/number-masked screening versus selected actual16k and prior used development; not proven independent of full6.5M corpus.'}
(p/'development_root_review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'fixtures':30,'raw_sha256':review['reviewed_raw_sha256'],'checks':checks}))

