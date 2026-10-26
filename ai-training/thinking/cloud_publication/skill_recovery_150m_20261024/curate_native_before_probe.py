from pathlib import Path
import json,hashlib
p=Path(__file__).parent
for n in ['native_locked15.jsonl','native_locked15_notes.json','native_locked15_exact_checks.py']:
 history=p/'authoring_history'/(n+'.agent_v1')
 if not history.exists():history.write_bytes((p/n).read_bytes())
rows=[json.loads(x) for x in(p/'native_locked15.jsonl').read_text(encoding='utf8').splitlines()]
rows[0].update(userproblem='Có 6 bó que, mỗi bó có 10 que, và thêm 4 que lẻ. Viết số que có tất cả. Chữ số 6 trong số vừa viết có giá trị bao nhiêu đơn vị?',exact_reference_answer='64 que; chữ số 6 có giá trị 60 đơn vị',checker='exact_number_and_digit_value',oracle={'number':64,'digit_value':60},rubric={'must_do':['Nhận 6 bó chục và 4 que lẻ là 64 que.','Phân biệt chữ số6 với giá trị60 đơn vị.'],'must_not_require':['Đặt tính phép cộng có nhớ của lớp2.']})
rows[2]['userproblem']+=' Cần biết thêm điều gì?'
for row in rows:row['authorship']='Original evaluation authoring, root-curated before native-probe outputs. Not training data; no human certification. Full-corpus independence unproven.'
(p/'native_locked15.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in rows),encoding='utf8')
n=json.loads((p/'native_locked15_notes.json').read_bytes());n['distribution']['mode_counts']={'answer':10,'missing_or_contradictory_info':3,'student_error':2};n['exact_checks']['expected_results']['native15_01']='64';n['review_status']='Root LLM read all15 actual questions, references and rubrics, repaired ambiguous grade1 task before candidate outputs; no human review claim.'
n['root_repairs']=['Replaced ambiguous card-joining/addition-with-carry task with grade1-appropriate concrete tens/ones representation.','Added explicit request for missing information to hidden-card guard.','Corrected authoring mode count4guards to actual3guards.']
(p/'native_locked15_notes.json').write_text(json.dumps(n,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
s=(p/'native_locked15_exact_checks.py').read_text(encoding='utf8').replace('Fraction(47 + 25)','Fraction(6 * 10 + 4)').replace('"native15_01": "72"','"native15_01": "64"')
(p/'native_locked15_exact_checks.py').write_text(s,encoding='utf8')
print(json.dumps({'fixtures':len(rows),'native_locked15_sha256':hashlib.sha256((p/'native_locked15.jsonl').read_bytes()).hexdigest(),'all_actual_fields_read':True,'no_human_certification':True}))
