"""Reproducible Vietnamese primary-math pilot, with exact arithmetic labels.

Synthetic templates are explicit worked examples, not OCR labels or human gold.
Numeric problem families stay in one split; val/test use held-out phrasings.
"""
import ast
from collections import Counter
from decimal import Decimal
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random

VERSION = "mvk_math_text_pilot_v1"
SYSTEM = (
    "Bạn là trợ giảng toán tiểu học Việt Nam. Chỉ giải toán lớp 1–5. "
    "Giải thích ngắn vì sao chọn phép tính, không suy đoán dữ kiện thiếu. "
    "Sau phần giải thích, trả một đối tượng JSON. Bài đủ dữ kiện: "
    '{"status":"solved","grade":số,"topic":chuỗi,"steps":'
    '[{"explanation":chuỗi,"expression":chuỗi,"result":chuỗi,"unit":chuỗi}],'
    '"answer":chuỗi,"unit":chuỗi}. '
    "Dùng + - * / và dấu chấm thập phân trong expression/result/answer; "
    "phân số viết a/b. Bài thiếu dữ kiện trả status=need_clarification và question; "
    "ngoài toán tiểu học trả status=out_of_scope và message."
)

def exact(expression):
    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return Fraction(str(node.value))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -visit(node.operand)
        if isinstance(node, ast.BinOp):
            a, b = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Add): return a + b
            if isinstance(node.op, ast.Sub): return a - b
            if isinstance(node.op, ast.Mult): return a * b
            if isinstance(node.op, ast.Div): return a / b
        raise ValueError("Unsupported arithmetic")
    if len(expression) > 160: raise ValueError("Expression too long")
    return visit(ast.parse(expression, mode="eval").body)

def number(value, decimal=False):
    value = Fraction(value)
    if value.denominator == 1: return str(value.numerator)
    if decimal:
        return format(Decimal(value.numerator) / Decimal(value.denominator), "f").rstrip("0").rstrip(".")
    return str(value)

def make_case(topic, rng):
    """Return params, grade, unit, phrasings, explained expressions, independent key."""
    a, b = rng.randint(1, 9), rng.randint(1, 9)
    if topic == "add_join":
        return [a,b],1,"quả",[
            f"Lan có {a} quả táo, mẹ cho thêm {b} quả. Lan có tất cả bao nhiêu quả táo?",
            f"Trong rổ có {a} quả táo. Thêm {b} quả táo vào rổ. Hỏi số táo trong rổ?",
            f"Mai có {a} quả táo và nhận thêm {b} quả nữa. Mai có bao nhiêu quả?",
            f"Một đĩa đựng {a} quả táo, đĩa kia có {b} quả. Hai đĩa có tổng cộng bao nhiêu quả?"],[
            ("Gộp hai lượng táo nên dùng phép cộng.",f"{a}+{b}")],a+b
    if topic == "sub_remaining":
        total, gone = a+b,b
        return [total,gone],1,"quả",[
            f"Lan có {total} quả táo và cho bạn {gone} quả. Lan còn bao nhiêu quả?",
            f"Có {total} quả táo trong rổ, lấy ra {gone} quả. Trong rổ còn mấy quả?",
            f"Mai có {total} quả táo, đã ăn {gone} quả. Hỏi số táo còn lại?",
            f"Một đĩa có {total} quả táo. Sau khi bớt {gone} quả, đĩa còn bao nhiêu quả?"],[
            ("Bớt lượng đã cho khỏi lượng ban đầu nên dùng phép trừ.",f"{total}-{gone}")],total-gone
    if topic == "add_books":
        a,b=rng.randint(10,40),rng.randint(10,40)
        return [a,b],2,"quyển",[
            f"Tủ thứ nhất có {a} quyển sách, tủ thứ hai có {b} quyển. Hai tủ có tất cả bao nhiêu quyển?",
            f"Nam đọc {a} quyển sách trong tháng trước và {b} quyển tháng này. Tổng số sách đã đọc?",
            f"Có {a} quyển sách Toán và {b} quyển sách Tiếng Việt. Hỏi có tất cả bao nhiêu quyển?",
            f"Thư viện nhận {a} quyển sách buổi sáng, nhận {b} quyển buổi chiều. Cả ngày nhận bao nhiêu quyển?"],[
            ("Tìm tổng hai nhóm sách bằng phép cộng.",f"{a}+{b}")],a+b
    if topic == "equal_groups":
        return [a,b],3,"bút",[
            f"Có {a} hộp, mỗi hộp có {b} bút. Có tất cả bao nhiêu bút?",
            f"Mỗi bạn được {b} bút. {a} bạn nhận tất cả bao nhiêu bút?",
            f"Nhà trường chuẩn bị {a} túi, mỗi túi đựng {b} bút. Tổng số bút là bao nhiêu?",
            f"{a} hộp bút giống nhau, mỗi hộp {b} bút. Hãy tìm số bút trong các hộp."],[
            ("Các nhóm có cùng số bút, lấy số nhóm nhân số bút mỗi nhóm.",f"{a}*{b}")],a*b
    if topic == "share_equal":
        total=a*b
        return [total,a],3,"bút",[
            f"Chia đều {total} bút cho {a} bạn. Mỗi bạn được bao nhiêu bút?",
            f"Xếp {total} bút vào {a} hộp như nhau. Mỗi hộp có mấy bút?",
            f"Có {total} bút được phân đều cho {a} học sinh. Hỏi số bút mỗi em nhận?",
            f"{a} túi đựng đều nhau tổng cộng {total} bút. Tính số bút trong một túi."],[
            ("Chia đều tổng số bút cho số nhóm bằng phép chia.",f"{total}/{a}")],total//a
    if topic == "gain_then_loss":
        a,b,c=rng.randint(20,80),rng.randint(5,30),rng.randint(1,15)
        return [a,b,c],3,"quyển",[
            f"Thư viện có {a} quyển sách, nhận thêm {b} quyển rồi cho mượn {c} quyển. Còn bao nhiêu quyển?",
            f"Nam có {a} quyển sách. Được tặng {b} quyển, sau đó tặng bạn {c} quyển. Nam còn bao nhiêu quyển?",
            f"Tủ sách ban đầu có {a} quyển. Nhập {b} quyển và chuyển đi {c} quyển. Tính số sách còn trong tủ.",
            f"Một lớp có {a} quyển sách, bổ sung {b} quyển, đem cho lớp khác {c} quyển. Lớp ấy còn mấy quyển?"],[
            ("Cộng số sách nhận thêm để tìm số sách trước khi cho mượn.",f"{a}+{b}"),
            ("Trừ số sách đã chuyển đi để tìm số còn lại.",f"{a+b}-{c}")],a+b-c
    if topic == "sum_difference":
        small=rng.randint(5,70); diff=rng.randint(2,40); big=small+diff; total=small+big
        return [total,diff],4,"quyển",[
            f"Lan và Mai có tổng cộng {total} quyển sách. Lan nhiều hơn Mai {diff} quyển. Lan có bao nhiêu quyển?",
            f"Hai tủ có {total} quyển sách. Tủ A nhiều hơn tủ B {diff} quyển. Tủ A có bao nhiêu quyển?",
            f"Tổng số sách của An và Bình là {total} quyển; An hơn Bình {diff} quyển. Tính số sách của An.",
            f"Có {total} quyển sách trong hai ngăn. Ngăn trên hơn ngăn dưới {diff} quyển. Hỏi số sách ngăn trên?"],[
            ("Cộng tổng và hiệu được hai lần số sách của người có nhiều hơn.",f"{total}+{diff}"),
            ("Chia cho hai để tìm số lớn.",f"{total+diff}/2")],big
    if topic == "fraction_add":
        d=rng.randint(4,15); a=rng.randint(1,d-2); b=rng.randint(1,d-a-1)
        return [a,b,d],4,"phần",[
            f"An dùng {a}/{d} tấm bìa, Bình dùng thêm {b}/{d} tấm từ phần còn lại. Hai bạn dùng tổng cộng bao nhiêu phần tấm bìa?",
            f"Buổi sáng dùng {a}/{d} tấm bìa, buổi chiều dùng thêm {b}/{d} tấm. Tổng phần bìa đã dùng là bao nhiêu?",
            f"Một tấm bìa được cắt hai phần không chồng nhau, lần lượt {a}/{d} và {b}/{d} tấm. Tổng hai phần là bao nhiêu?",
            f"Mai dùng {a}/{d} tấm bìa rồi dùng thêm {b}/{d} tấm bìa từ phần còn lại. Tính phần bìa Mai đã dùng."],[
            ("Hai phần không chồng nhau nên cộng hai phân số cùng mẫu.",f"{a}/{d}+{b}/{d}")],Fraction(a+b,d)
    if topic == "rectangle_area":
        a,b=rng.randint(5,30),rng.randint(2,20)
        return [a,b],4,"cm²",[
            f"Hình chữ nhật dài {a} cm, rộng {b} cm. Tính diện tích.",
            f"Tấm bìa hình chữ nhật có chiều dài {a} cm và chiều rộng {b} cm. Diện tích tấm bìa?",
            f"Một hình chữ nhật có hai kích thước {a} cm và {b} cm. Tìm diện tích hình đó.",
            f"Tính diện tích mảnh giấy hình chữ nhật dài {a} cm, rộng {b} cm."],[
            ("Diện tích hình chữ nhật bằng chiều dài nhân chiều rộng.",f"{a}*{b}")],a*b
    if topic in ("decimal_add","decimal_sub"):
        a,b=rng.randint(101,900),rng.randint(1,100)
        aa,bb=number(Fraction(a,100),True),number(Fraction(b,100),True)
        va,vb=aa.replace('.',','),bb.replace('.',',')
        if topic == "decimal_add":
            qs=[f"Có {va} kg gạo, thêm {vb} kg. Có tất cả bao nhiêu kg?",f"Hai túi gạo nặng {va} kg và {vb} kg. Tổng khối lượng?",f"Mai mua {va} kg gạo rồi mua thêm {vb} kg. Mai mua bao nhiêu kg gạo?",f"Gộp {va} kg gạo với {vb} kg gạo. Tính khối lượng sau khi gộp."]
            expr=f"{aa}+{bb}"; key=Fraction(a+b,100); why="Gộp hai khối lượng nên cộng số thập phân, đặt đúng hàng."
        else:
            qs=[f"Có {va} kg gạo, dùng {vb} kg. Còn bao nhiêu kg?",f"Túi gạo nặng {va} kg, lấy ra {vb} kg. Khối lượng còn lại?",f"Mai mua {va} kg gạo và đã nấu {vb} kg. Mai còn bao nhiêu kg?",f"Bớt {vb} kg gạo khỏi {va} kg gạo. Tính khối lượng gạo còn lại."]
            expr=f"{aa}-{bb}"; key=Fraction(a-b,100); why="Bớt lượng đã dùng nên trừ số thập phân, đặt đúng hàng."
        return [a,b],5,"kg",qs,[(why,expr)],key
    if topic == "trapezoid_area":
        a,b,h=rng.randint(8,30),rng.randint(3,7),rng.randint(2,12)
        return [a,b,h],5,"cm²",[
            f"Hình thang có hai đáy {a} cm và {b} cm, chiều cao {h} cm. Tính diện tích.",
            f"Một hình thang có đáy lớn {a} cm, đáy nhỏ {b} cm, cao {h} cm. Diện tích bằng bao nhiêu?",
            f"Tấm bìa hình thang có các đáy dài {a} cm, {b} cm; chiều cao {h} cm. Tìm diện tích tấm bìa.",
            f"Tính diện tích hình thang biết hai đáy là {a} cm và {b} cm, khoảng cách vuông góc giữa hai đáy {h} cm."],[
            ("Cộng hai độ dài đáy.",f"{a}+{b}"),
            ("Diện tích hình thang bằng tổng hai đáy nhân chiều cao rồi chia hai.",f"{a+b}*{h}/2")],Fraction((a+b)*h,2)
    raise ValueError(topic)

TOPICS = ("add_join","sub_remaining","add_books","equal_groups","share_equal","gain_then_loss","sum_difference","fraction_add","rectangle_area","decimal_add","decimal_sub","trapezoid_area")

def split_for(group):
    bucket=int(hashlib.sha256(group.encode()).hexdigest()[:8],16)%10
    return "test" if bucket==0 else "val" if bucket==1 else "train"

def build_dataset(per_topic=80, seed=20261011):
    rng=random.Random(seed); rows=[]; seen=set()
    for topic in TOPICS:
        count=0
        # Some grade-1 topics have only 81 distinct numeric families.
        target=min(per_topic,45) if topic=="add_join" else min(per_topic,80) if topic in ("sub_remaining","equal_groups","share_equal") else per_topic
        for attempt in range(100000):
            params,grade,unit,questions,raw_steps,key=make_case(topic,rng)
            # Swapping interchangeable quantities must not cross splits either.
            family_params = sorted(params) if topic in ("add_join","add_books","rectangle_area") else sorted(params[:2])+params[2:] if topic=="fraction_add" else params
            group=topic+":"+",".join(map(str,family_params))
            if group in seen: continue
            seen.add(group); count+=1; split=split_for(group)
            variants=(0,1) if split=="train" else (2,) if split=="val" else (3,)
            decimal=topic.startswith("decimal_")
            steps=[dict(explanation=why,expression=expr,result=number(exact(expr),decimal),unit=unit if i==len(raw_steps)-1 else unit if topic not in ("trapezoid_area",) else "cm") for i,(why,expr) in enumerate(raw_steps)]
            assert exact(steps[-1]["result"]) == key
            target_json=dict(status="solved",grade=grade,topic=topic,steps=steps,answer=number(key,decimal),unit=unit)
            for variant in variants:
                row=dict(sample_id=hashlib.sha256(f"{group}:{variant}".encode()).hexdigest()[:20],split_group_id=group,split=split,grade=grade,topic=topic,problem=questions[variant],target=target_json,worked_solution="\n".join(f"{s['explanation']} {s['expression']} = {s['result']}." for s in steps),source="programmatic_template_v1",human_verified=False,arithmetic_verified=True,dataset_version=VERSION,parameters=params,variant=variant)
                rows.append(row)
            if count>=target: break
        else: raise RuntimeError("Insufficient unique families")
    # Explicit scope/clarification templates, disjoint wording per split.
    for split,question,grade in [
        ("train","Lan có một số quyển sách, được cho thêm 5 quyển. Lan có tất cả bao nhiêu quyển?",2),
        ("val","Nam có một số bút, nhận thêm 3 bút. Hỏi Nam có bao nhiêu bút?",2),
        ("test","Mai có vài quả táo và được thêm 4 quả. Tổng số táo của Mai?",1),
        ("train","Tính diện tích hình chữ nhật biết chiều dài 12 cm.",4),
        ("val","Một hình chữ nhật rộng 7 cm. Tìm diện tích.",4),
        ("test","Mảnh đất hình chữ nhật dài 20 m. Diện tích là bao nhiêu?",4),
    ]:
        if "hình chữ nhật" in question:
            followup="Chiều dài hình chữ nhật là bao nhiêu?" if "rộng" in question else "Chiều rộng hình chữ nhật là bao nhiêu?"
        else:
            followup="Lúc đầu có chính xác bao nhiêu " + ("quyển sách?" if "sách" in question else "bút?" if "bút" in question else "quả táo?")
        target=dict(status="need_clarification",grade=grade,question=followup)
        group="clarification:"+hashlib.sha256(question.encode()).hexdigest()[:16]
        rows.append(dict(sample_id=group,split_group_id=group,split=split,grade=grade,topic="clarification",problem=question,target=target,worked_solution="Đề chưa cho đủ dữ kiện để tính một đáp số duy nhất.",source="authored_clarification_template",human_verified=False,arithmetic_verified=False,dataset_version=VERSION))
    for split,qs in {"train":["Viết chương trình sắp xếp bằng Python.","Tính đạo hàm của x^2."],"val":["Hãy viết mã JavaScript cho một trang web."],"test":["Giải phương trình vi phân y' = y."]}.items():
        for question in qs:
            group="scope:"+hashlib.sha256(question.encode()).hexdigest()[:16]
            rows.append(dict(sample_id=group,split_group_id=group,split=split,grade=None,topic="scope",problem=question,target=dict(status="out_of_scope",message="Mình chỉ hỗ trợ toán tiểu học lớp 1–5."),worked_solution="Yêu cầu này nằm ngoài phạm vi toán tiểu học.",source="authored_scope_template",human_verified=False,arithmetic_verified=False,dataset_version=VERSION))
    validate(rows)
    return rows

def validate(rows):
    groups={}; questions=set(); ids=set()
    for row in rows:
        assert row['sample_id'] not in ids, "Duplicate ID"; ids.add(row['sample_id'])
        assert row['problem'] not in questions, "Duplicate question"; questions.add(row['problem'])
        old=groups.setdefault(row['split_group_id'],row['split'])
        assert old==row['split'], "Split leakage"
        assert row['human_verified'] is False, "Synthetic data must not claim human verification"
        t=row['target']
        if t['status']=='solved':
            assert 1<=row['grade']<=5
            for s in t['steps']: assert exact(s['expression'])==exact(s['result']), "Bad step"
            assert exact(t['answer'])==exact(t['steps'][-1]['result']), "Bad final answer"
            assert t['unit']==t['steps'][-1]['unit'], "Bad unit"
            assert row['arithmetic_verified'] is True
        else: assert 'answer' not in t, "Invented answer for unsolved problem"
    assert set(groups.values())=={'train','val','test'}

def write_dataset(output, per_topic=80):
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    rows=build_dataset(per_topic); fingerprints={}
    for split in ('train','val','test'):
        data=''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows if r['split']==split)
        (output/f'{split}.jsonl').write_text(data,encoding='utf-8')
        fingerprints[split]=hashlib.sha256(data.encode()).hexdigest()
    report=dict(dataset_version=VERSION,rows=len(rows),splits=dict(Counter(r['split'] for r in rows)),grades=dict(Counter(str(r['grade']) for r in rows)),topics=dict(Counter(r['topic'] for r in rows)),group_overlap=0,fingerprints=fingerprints,source='synthetic_programmatic_templates',human_verified=False,scope='12 selected topic families; not full Vietnamese curriculum',limitations=['Arithmetic is checked; pedagogical quality is not teacher certified.','Held-out phrasings and numbers remain in familiar topic families.','Performance here is not a benchmark on real student problems.','No OCR annotations or student wrong answers are used as correct solutions.'])
    (output/'dataset_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'DATASET_CARD.md').write_text('# MathVisionKid — text math pilot\n\n'+json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('--output',required=True); p.add_argument('--per-topic',type=int,default=80)
    args=p.parse_args(); print(json.dumps(write_dataset(args.output,args.per_topic),ensure_ascii=False,indent=2))
