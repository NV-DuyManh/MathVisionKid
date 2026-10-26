"""Original AI-teacher anchor problems, excluded from training and selection.

These are an independently authored development probe, not a human-certified
national curriculum benchmark. Numeric oracles are independently calculated.
"""
import ast
from fractions import Fraction
import hashlib
import json
from pathlib import Path

ANCHORS = [
    (1, 'Hoa có 8 viên bi. Sau khi cho Minh 3 viên, Hoa nhận thêm 4 viên từ mẹ. Hoa có bao nhiêu viên bi?', 'viên', [('8-3','5'),('5+4','9')]),
    (1, 'Trong hộp có 13 bút chì, gồm bút đỏ và 5 bút xanh. Có bao nhiêu bút đỏ?', 'bút', [('13-5','8')]),
    (1, 'Lan đọc 7 trang, Bình đọc 12 trang. Bình đọc nhiều hơn Lan bao nhiêu trang?', 'trang', [('12-7','5')]),
    (1, 'Tính tổng của 36 và 23.', '', [('36+23','59')]),
    (1, 'Một hàng có 19 bạn. Có 6 bạn ra sân trước. Hỏi còn bao nhiêu bạn trong hàng?', 'bạn', [('19-6','13')]),
    (2, 'Bốn bàn học đều có 3 học sinh. Một bàn khác có 2 học sinh. Có tất cả bao nhiêu học sinh?', 'học sinh', [('4*3','12'),('12+2','14')]),
    (2, 'Có 30 quả cam. Người bán chia đều vào 5 túi rồi bán 2 túi. Còn lại bao nhiêu quả cam?', 'quả', [('30/5','6'),('5-2','3'),('6*3','18')]),
    (2, 'Một sợi dây dài 1 m. Cắt đi 35 cm. Đoạn còn lại dài bao nhiêu xăng-ti-mét?', 'cm', [('1*100','100'),('100-35','65')]),
    (2, 'Buổi sáng cửa hàng bán 28 quyển vở. Buổi chiều bán nhiều hơn buổi sáng 17 quyển. Cả ngày bán bao nhiêu quyển?', 'quyển', [('28+17','45'),('28+45','73')]),
    (2, 'Chia 42 cái bánh đều cho 6 bạn. Mỗi bạn được bao nhiêu cái bánh?', 'cái', [('42/6','7')]),
    (3, 'Xếp 38 học sinh lên xe, mỗi xe chở tối đa 8 học sinh. Cần ít nhất bao nhiêu xe?', 'xe', [('(38-38%8)/8','4'),('38%8','6'),('4+1','5')]),
    (3, 'Một khu vườn hình chữ nhật rộng 7 m và dài hơn chiều rộng 5 m. Chu vi khu vườn là bao nhiêu?', 'm', [('7+5','12'),('(12+7)*2','38')]),
    (3, 'Một tiết học kéo dài 35 phút. Ba tiết học như vậy kéo dài bao nhiêu phút?', 'phút', [('35*3','105')]),
    (3, 'Có 72 nhãn vở. Tặng đi một phần ba số nhãn vở. Hỏi còn bao nhiêu nhãn vở?', 'nhãn', [('72/3','24'),('72-24','48')]),
    (3, 'Tính 3002 trừ 1785. Hãy giải thích việc mượn khi đặt tính.', '', [('3002-1785','1217')]),
    (4, 'Hai thùng có tổng cộng 84 lít nước. Thùng thứ nhất nhiều hơn thùng thứ hai 18 lít. Thùng thứ hai có bao nhiêu lít?', 'lít', [('84-18','66'),('66/2','33')]),
    (4, 'Mai dùng 2/3 tờ giấy, Nam dùng 1/6 tờ cùng loại. Hai bạn dùng tất cả bao nhiêu tờ?', 'tờ', [('2/3+1/6','5/6')]),
    (4, 'Một mảnh đất hình chữ nhật dài 25 m, rộng 16 m. Một phần tư diện tích dành trồng hoa. Diện tích trồng hoa là bao nhiêu?', 'm²', [('25*16','400'),('400/4','100')]),
    (4, 'Ba ngày cửa hàng bán lần lượt 18, 27 và 30 kg gạo. Trung bình mỗi ngày bán bao nhiêu ki-lô-gam?', 'kg', [('18+27+30','75'),('75/3','25')]),
    (4, 'Tính 3/4 chia cho 2/5.', '', [('(3/4)/(2/5)','15/8')]),
    (5, 'Một áo giá 240000 đồng được giảm 15% giá ban đầu. Người mua phải trả bao nhiêu đồng?', 'đồng', [('240000*15/100','36000'),('240000-36000','204000')]),
    (5, 'Một xe đi đều với vận tốc 36 km/giờ trong 45 phút. Xe đi được bao nhiêu ki-lô-mét?', 'km', [('45/60','3/4'),('36*(3/4)','27')]),
    (5, 'Hình thang có hai đáy 8 cm và 14 cm, chiều cao 5 cm. Tính diện tích.', 'cm²', [('8+14','22'),('22*5/2','55')]),
    (5, 'Hộp chữ nhật dài 12 cm, rộng 5 cm, cao 4 cm. Thể tích hộp là bao nhiêu?', 'cm³', [('12*5*4','240')]),
    (5, 'Mua 2,5 kg gạo với giá 18000 đồng mỗi ki-lô-gam, trả tờ 100000 đồng. Được trả lại bao nhiêu đồng?', 'đồng', [('2.5*18000','45000'),('100000-45000','55000')]),
]

def exact(expression):
    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int,float):
            return Fraction(str(node.value))
        if not isinstance(node,ast.BinOp): raise ValueError('Unsafe oracle')
        a,b=visit(node.left),visit(node.right)
        if isinstance(node.op,ast.Add): return a+b
        if isinstance(node.op,ast.Sub): return a-b
        if isinstance(node.op,ast.Mult): return a*b
        if isinstance(node.op,ast.Div): return a/b
        if isinstance(node.op,ast.FloorDiv): return Fraction(a//b)
        if isinstance(node.op,ast.Mod): return a%b
        raise ValueError('Unsupported oracle')
    return visit(ast.parse(expression,mode='eval').body)

def create():
    rows=[]
    for grade,problem,unit,steps in ANCHORS:
        for expression,result in steps:
            assert exact(expression)==Fraction(result),(problem,expression,result)
        rows.append({'sample_id':'anchor_'+hashlib.sha256(problem.encode()).hexdigest()[:20],
            'grade':grade,'problem':problem,'mode':'worked_solution','topic':'independent_anchor',
            'split':'independent_anchor','target':{'status':'solve','steps':[{'explanation':'Giải từng lượng theo đề rồi kiểm tra kết quả.',
            'expression':e,'result':v,'unit':unit if i==len(steps)-1 else ''} for i,(e,v) in enumerate(steps)],
            'answer':steps[-1][1],'unit':unit,'hint':None},'oracle_answer':steps[-1][1],
            'human_verified':False,'pedagogy_teacher_reviewed':False,'source':'original_ai_teacher_independent_authoring',
            'curriculum_grade_verified':False,'not_used_for_checkpoint_selection':True})
    for grade,problem,status,hint in [
        (1,'Lan có một số bút rồi nhận thêm 4 bút. Lan có tất cả bao nhiêu bút?','clarify','Em cho biết Lan có bao nhiêu bút lúc đầu được không?'),
        (2,'Có 18 cái bánh chia cho các bạn. Mỗi bạn được mấy cái?','clarify','Em cho biết chia đều cho bao nhiêu bạn được không?'),
        (3,'Một hình chữ nhật dài 12 cm. Diện tích của nó là bao nhiêu?','clarify','Em cho biết chiều rộng hình chữ nhật được không?'),
        (4,'Hai bạn có tổng cộng 40 viên bi. Bạn nào có nhiều hơn và nhiều hơn bao nhiêu?','clarify','Đề còn thiếu dữ kiện nào về số bi của hai bạn?'),
        (5,'Hãy giải phương trình lượng giác sin(x) bằng 0.','unsupported','Em có thể gửi một bài Toán tiểu học không?')]:
        rows.append({'sample_id':'anchor_'+hashlib.sha256(problem.encode()).hexdigest()[:20],'grade':grade,'problem':problem,
            'mode':'worked_solution','topic':'independent_anchor_guard','split':'independent_anchor',
            'target':{'status':status,'steps':[],'answer':None,'unit':None,'hint':hint},'oracle_answer':None,
            'human_verified':False,'pedagogy_teacher_reviewed':False,'source':'original_ai_teacher_independent_authoring',
            'curriculum_grade_verified':False,'not_used_for_checkpoint_selection':True})
    return rows

if __name__=='__main__':
    path=Path(__file__).parent/'data'/'teacher_math_v3'/'independent_anchor.jsonl'
    path.parent.mkdir(parents=True,exist_ok=True)
    rows=create();path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
    print(json.dumps({'samples':len(rows),'solvable':len(ANCHORS),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'all_numeric_steps_independently_checked':True,'human_verified':False},ensure_ascii=False))
