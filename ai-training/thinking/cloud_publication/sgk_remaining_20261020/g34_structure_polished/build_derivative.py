"""Bounded editorial derivatives; preserve parent case/chat bytes and lineage."""
from pathlib import Path
import copy,json,hashlib,sys
B=Path(__file__).resolve().parent;P=B.parent/'g34_structure_text'
HERE=B.parents[2];sys.path.insert(0,str(HERE))
from exhaustive_primary_math import chat_records
H=lambda b:hashlib.sha256(b).hexdigest()
J=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
FIELDS=['problem','givens','requested_quantity','student_work','worked_steps','expected_answer','initial_guidance','hints']
GIVENS={
'strips_connector_chain':['P ghi104, mép trái BẮT ĐẦU, mép phải a; Q ghi005, trái a, phải b; R ghi020, trái b, phải KẾT THÚC.','Ba vị trí lần lượt là lớp triệu, lớp nghìn, lớp đơn vị; mỗi lớp có đúng ba chữ số. Không lật mảnh; dùng hết ba mảnh, mỗi mảnh một lần.'],
'strips_decoy_pin':['A ghi305, mép BẮT ĐẦU→x; B ghi040, mép x→y; C ghi007, mép y→KẾT THÚC; D ghi400, mép x→y.','Chọn đúng ba mảnh, không lật. Mảnh giữa ở lớp nghìn; chữ số hàng chục nghìn bằng4, hàng trăm nghìn bằng0.'],
'partial_products_digit_reconstruct':['Số bị nhân3a, nhân với24; tích riêng nhân4 là1b6, tích riêng nhân20 là7c0; tổng là9d6.','Mỗi dòng ghi đầy đủ giá trị và các hàng thẳng cột; a,b,c,d là chữ số từ0đến9, được lặp. Giữ mọi chữ số đã in.'],
'partial_factor_and_shift_error':['Phép nhân3a×b3: tích riêng nhân3đơn vị là93; tích riêng nhân b chục ghi đầy đủ620, gồm số0hàng đơn vị.','b là chữ số từ1đến9; a từ0đến9. Giữ nguyên hai tích riêng93và620.'],
'overlap_fixed_axis_union':['Trục chung có gốc O ở0cm; thanh đỏ phủ từ0đến12cm, thanh xanh phủ từ5đến15cm.','Giữ nguyên vị trí và chiều dài hai thanh; phần có cả hai thanh chỉ tính một lần khi tính vùng phủ bởi ít nhất một thanh.'],
'overlap_opposite_orientation':['Trên cùng trục: A ở trái gốc2cm, B ở phải gốc6cm, C ở phải gốc3cm, D ở phải gốc10cm; đỏ từ B đến A, xanh từ C đến D.','Vị trí được xác định theo gốc và chiều tăng sang phải; chiều kể đầu mút không làm độ dài âm. Giữ nguyên các đầu mút.'],
'all_ray_pairs_compound':['Các tia chung gốc O có hướng: OA0°, OB40°, OC100°; không có tia khác.','Mỗi cặp hai tia khác nhau được tính một lần, không kể thứ tự; lấy góc nhỏ không quá180°, gồm cả góc ghép.'],
'ray_pairs_exclude_straight_error':['Bốn tia chung gốc O có hướng OA0°, OB45°, OC90°, OD180°; không có tia khác.','Xét mọi cặp hai tia khác nhau, không kể thứ tự. Loại riêng góc bẹt180°, vẫn tính các góc ghép khác.'],
'collinear_four_on_line':['Trên lưới theo(cột,hàng): A(0,0), B(1,0), C(2,0), D(3,0), E(0,1); không có điểm khác.','Liệt kê mọi bộ ba điểm khác nhau thẳng hàng; đảo thứ tự tên vẫn là cùng một bộ.'],
'collinear_diagonal_missing':['Trên lưới theo(cột,hàng): O(0,0), A(1,0), B(2,0), C(0,1), D(0,2), E(1,1); không có điểm khác.','Liệt kê mọi bộ ba điểm khác nhau thẳng hàng, gồm cả đường chéo; đảo tên không tính thêm bộ mới.'],
'matrix_row_color_column_shape':['Bảng hai hàng, ba cột; các ô cùng hàng có cùng màu, các ô cùng cột có cùng loại hình. Chỉ dùng đỏ hoặc xanh và tròn, vuông hoặc tam giác.','Ô(1,1)tròn đỏ; ô(1,2)vuông đỏ; ô(1,3)tam giác đỏ; ô(2,1)tròn xanh. Cần tìm ô(2,3).'],
'matrix_two_completions':['Bảng hai hàng, hai cột; mỗi hàng có đúng một hình tròn và một hình vuông, các ô trong cùng cột có cùng màu. Chỉ dùng đỏ hoặc xanh.','Ô(1,1)tròn đỏ, ô(1,2)vuông xanh; hàng hai còn trống. Không có quy tắc buộc các ô cùng cột có cùng hình.']}
def expanded(s):
 import re
 # Explicit prose quantities only; no broad technical ID mutation.
 s=re.sub(r'(ghi|bằng|từ|đến|là|với|nhân|riêng|đủ|hàng|trái gốc|phải gốc|ở|quá|bẹt)(?=\d)',r'\1 ',s)
 s=re.sub(r'(?<=\d)(?=cm|đơn vị|hàng|và|đến)',' ',s)
 s=s.replace('số0','số 0').replace('và620','và 620').replace('OA0°','OA=0°').replace('OB40°','OB=40°').replace('OC100°','OC=100°').replace('OB45°','OB=45°').replace('OC90°','OC=90°').replace('OD180°','OD=180°')
 return s.replace('Ô(','Ô (').replace('ô(','ô (').replace('theo(','theo (').replace(')tròn',') tròn').replace(')vuông',') vuông').replace(')tam',') tam')
def diffs(a,b,path=''):
 if type(a)!=type(b):return[dict(path=path,before=a,after=b)]
 if isinstance(a,dict):return sum([diffs(a[k],b[k],path+'/'+k)for k in a if k in b],[])+[dict(path=path+'/'+k,before=None,after=b[k])for k in b if k not in a]
 if isinstance(a,list):return sum([diffs(x,y,path+'/'+str(i))for i,(x,y)in enumerate(zip(a,b))],[])
 return[]if a==b else[dict(path=path,before=a,after=b)]
def main():
 parent_cases=(P/'cases.jsonl').read_bytes();parent_chat=(P/'chat.jsonl').read_bytes();lines=parent_cases.splitlines();old=[json.loads(l)for l in lines];assert len(old)==12
 rows=[];deltas=[]
 for source,raw in zip(old,lines):
  row=copy.deepcopy(source);topic=row['topic'];assert topic in GIVENS
  for given,text in zip(row['givens'],GIVENS[topic]):given['text']=expanded(text)
  if topic=='partial_products_digit_reconstruct':
   row['worked_steps'][0]['result']='Số bị nhân thuộc 35,36,37,38,39; cần xét tiếp dòng đơn vị.'
   row['worked_steps'][1]['result']='Số bị nhân 39; a=9; b=5; c=8; 39×4=156 và 39×20=780.'
  # Preserve task identity: this is a selected derivative replacing parent, not
  # twelve new mathematical cases. Exact hashes disambiguate versions.
  row['provenance'].update(derivative_kind='EDITORIAL_CLARITY_DERIVATIVE',parent_source_file=str((P/'cases.jsonl').relative_to(HERE)),parent_sample_id=source['sample_id'],parent_source_row_sha256=H(raw),selection_policy='REPLACES_PARENT_IN_RELEASE_NOT_ADDITIONAL_CASE',derivative_human_review_completed=False)
  row['quality_status']='POLISHED_DERIVATIVE_PENDING_INDEPENDENT_PEER_AND_ROOT_QA';row['acceptance_status']='DRAFT_AWAITING_ROOT_CONTENT_QA';row['coverage']['derived_replacement_not_new_case']=True
  assert row['problem']==source['problem']and row['student_work']==source['student_work']and row['expected_answer']==source['expected_answer']and row['hints']==source['hints']and row['initial_guidance']==source['initial_guidance']
  rows.append(row);deltas.append(dict(sample_id=row['sample_id'],parent_source_row_sha256=H(raw),parent_actual_fields={k:source.get(k)for k in FIELDS},derived_actual_fields={k:row.get(k)for k in FIELDS},field_deltas=diffs(source,row)))
 def write(name,rr):
  data=('\n'.join(J(r)for r in rr)+'\n').encode();(B/name).write_bytes(data);return dict(path=name,rows=len(rr),bytes=len(data),sha256=H(data))
 manifests=[write('cases.jsonl',rows)];newlines=(B/'cases.jsonl').read_bytes().splitlines();hashes={r['sample_id']:H(l)for r,l in zip(rows,newlines)};chats=[]
 for row in rows:
  for c in chat_records(row):c.update(source_row_sha256=hashes[row['sample_id']],acceptance_status=row['acceptance_status'],quality_status=row['quality_status']);chats.append(c)
 assert len(chats)==48;manifests+=[write('chat.jsonl',chats)]
 for d in deltas:d['derived_source_row_sha256']=hashes[d['sample_id']]
 manifests.append(write('parent_derivative_delta.jsonl',deltas))
 # Full rowhash lineage and unchanged inputs are independently reopenchecked.
 assert(P/'cases.jsonl').read_bytes()==parent_cases and(P/'chat.jsonl').read_bytes()==parent_chat
 report=dict(status='DERIVED12_REPLACE_PARENT12_PENDING_FRESH_PEER_QA',case_count=12,chat_count=48,additional_case_count=0,parent_cases_sha256=H(parent_cases),parent_chat_sha256=H(parent_chat),parent_bytes_unchanged=True,answers_problem_studentwork_allhints_initial_identical=True,changes='Expand24compactgivenstexts; partialproducts move finaldigit conclusion from step0 to step1. Add exact parenthash lineage and derivative status only.',manifest=manifests,helper_sha256=H(Path(__file__).read_bytes()))
 (B/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
