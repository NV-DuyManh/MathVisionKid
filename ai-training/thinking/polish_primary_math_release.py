import json,re,sys
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parent))
from primary_math_data_pipeline import *
R=DEFAULT_ROOT;E=HERE/'evidence/primary_math_teacher_20261016'
def tidy(text,quote=None):
 if not isinstance(text,str):return text
 if quote and quote in text:text=text.replace(quote,'§§UNCHANGED_QUOTED_STUDENT_WORK§§')
 text=re.sub(r'(?<=[A-Za-zÀ-ỹ])(?=[0-9])',' ',text)
 text=re.sub(r'(?<=[0-9])(?=[A-Za-zÀ-ỹ])',' ',text)
 text=re.sub(r'(?<=[²³%])(?=[A-Za-zÀ-ỹ])',' ',text)
 text=re.sub(r'([,;:.!?])(?=[A-Za-zÀ-ỹ])',r'\1 ',text)
 text=re.sub(r'([A-Za-zÀ-ỹ])([;:.!?])(?=[0-9])',r'\1\2 ',text)
 text=re.sub(r'(?<=[0-9])\.(?=[0-9])','. ',text)
 text=re.sub(r';(?=[0-9])','; ',text)
 terms='đang|để|đi|hay|trong|nếu|cũng|lại|đều|khi|là|không|đã|có|nằm|giữa|ngoài|đặt|vuông|dài|thỏa|chỉ|cách|thì|và|với|trên|theo|khớp|hoặc|chưa|đúng|thành|gồm|bằng|giữ|thuộc|phải|cần|thẳng|nên|rồi|được|sau|trước|đến|ở|tại|trùng|lệch|dù|hỏi|mới|cùng'
 text=re.sub(r'(AB|AM|MB|AN|NB|OA|OB|PD|PC|CPD|AOB|M|N|P|O|A|B|C|D)(?=(?:'+terms+r'))',r'\1 ',text)
 text=re.sub(r'(giữa|đến|đoạn|góc|đỉnh|tia|theo|và|của|cạnh|tại|trên|đúng|còn|cho|giữ|sửa|dời|thấy|đủ|là|ngoài|trùng|trước|sau|với|từ|có|không)(?=[A-Z])',r'\1 ',text)
 text=re.sub(r'(?<=[\w)])\s*([+−×÷=<>])\s*(?=[\w(□])',r' \1 ',text)
 text=re.sub(r' +',' ',text).strip()
 if quote:text=text.replace('§§UNCHANGED_QUOTED_STUDENT_WORK§§',quote)
 return text

def create():
 q=json.loads((R/'pre_sft_polish_queue.json').read_text('utf-8'));src={x['sample_id']:x for f in (R/'authored_batches').glob('*.jsonl') for x in read_rows(f)};base={x['sample_id']:x for x in read_rows(R/'exports/accepted_teacher_cases.jsonl')};dest=R/'derived_release/pre_sft_polished_sources.jsonl'
 if dest.exists():
  before=read_rows(dest);write_rows(E/('pre_sft_polish_draft_before_'+sha(dest.read_bytes())[:12]+'.jsonl'),before)

 rows=[];manifest=[]
 for i,c in enumerate(q['cases']):
  original=src[c['sample_id']];assert row_sha(original)==c['row_sha256'];x=deepcopy(original);quote=(x.get('student_work') or {}).get('text')
  for k in ['problem','requested_quantity']:x[k]=tidy(x[k],quote)
  x['initial_guidance']=[tidy(t,quote) for t in x['initial_guidance']]
  for g in x['givens']:g['text']=tidy(g['text'],quote)
  for h in x['hints']:
   for k in ['hint','question']:h[k]=tidy(h[k],quote)
  for st in x['worked_steps']:
   for k in ['title','reason','explanation','result']:st[k]=tidy(st[k],quote)
  for a in x['expected_answer']:a['quantity']=tidy(a['quantity'],quote);a['result']=tidy(a['result'],quote)
  if i==0:
   x['hints'][0]['hint']='Hai số đo trong câu viết đang được ghi theo các đơn vị độ dài khác nhau.'
   x['hints'][0]['question']='Số đo đầu tiên trong câu viết đang dùng đơn vị gì?'
  if i==1:x['worked_steps'][2]['explanation']='Xanh có B, C, F, H nên có 4 bút.'
  if i==5:x['hints'][2]['question']='Cách kiểm đã xét cả cạnh cuối và các góc, hay mới chỉ xét hai cạnh đầu?'
  if i==8:
   x['worked_steps'][0]['reason']='Ô trống là số bị chia; 4 là số chia khác 0; 213 là thương.'
   x['worked_steps'][2]['explanation']='852 : 4 = 213. Kiểm theo chia: 8 : 4 = 2; hạ 5; 5 : 4 = 1 dư 1; hạ 2 thành 12; 12 : 4 = 3 hết. Số chia 4 khác 0 nên phép chia có nghĩa.'
  if i==19:
   x['initial_guidance'][1]='Số bị mất tên đại lượng có thể là số túi hoặc lượng bi mỗi túi; hãy bổ sung câu gốc.'
   x['hints'][0]['question']='Số chưa rõ vai trò trong đề gốc đi cùng chữ túi hay chữ viên mỗi túi?'
  if i==38:x['hints'][1]['question']='Số chỉ quan hệ giảm trong đề mang đơn vị lần hay tem?'
  if i==40:x['hints'][0]['question']='Số chỉ quan hệ trong đề nói số lần hay số bưu ảnh bị lấy đi?'
  if i==42:x['worked_steps'][0]['reason']='Tên một phần cần dựa vào cách chia toàn bộ thành các phần bằng nhau.'
  if i==44:
   x['hints'][1]['hint']='Hãy đối chiếu các mảnh theo cùng một ô làm mốc.'
   x['hints'][1]['question']='Chỉ đếm số mảnh đã kiểm tra hết điều kiện của tên phần chưa?'
  fixes={'Hchỉ':'H chỉ','kíchthước':'kích thước','mặtvuông':'mặt vuông','chữnhật':'chữ nhật','ABFEtrong':'ABFE trong','ADHEkề':'ADHE kề','ABFEvì':'ABFE vì','CDHGở':'CDHG ở','ABFEcó':'ABFE có','CDHGcó':'CDHG có','ADHEchung':'ADHE chung','Ara':'A ra','Achia':'A chia','Acòn':'A còn','Bvẫn':'B vẫn','Bvì':'B vì','1/nkhi':'1/n khi','thànhncác':'thành n các'}
  def final_spacing(v):
   if isinstance(v,str):
    for a,b in fixes.items():v=v.replace(a,b)
    return v
   if isinstance(v,list):return [final_spacing(z) for z in v]
   if isinstance(v,dict):return {k:final_spacing(z) for k,z in v.items()}
   return v
  for key in ['problem','givens','requested_quantity','initial_guidance','hints','worked_steps','expected_answer']:x[key]=final_spacing(x[key])
  x['sample_id']=original['sample_id']+':polish_v1';x['provenance'].update({'derivation_method':'AI_DERIVED_PRE_SFT_POLISH','authoring_agent':'root','human_verified':False,'teacher_certified':False,'owner_human_reviewed':False,'independent_external_reviewer':False,'content_review_status':'PENDING_DERIVATIVE_QA','original_authorship_preserved':True})
  x['derivation']={'parent_sample_id':original['sample_id'],'original_source_row_sha256':row_sha(original),'original_owner_overlay_row_sha256':row_sha(base[original['sample_id']]),'parent_case_group_id':original['case_group_id'],'operation':'PROSE_SPACING_HINT_WORDING_AND_SINGLE_REDUNDANT_SENTENCE_REMOVAL','student_quote_and_observations_unchanged':True,'numeric_expressions_and_answer_values_unchanged':True,'no_new_human_attestation':True}
  assert x['student_work']==original['student_work']
  assert [s['expression'] for s in x['worked_steps']]==[s['expression'] for s in original['worked_steps']]
  assert [a['result'] for a in x['expected_answer']]==[tidy(a['result'],quote) for a in original['expected_answer']]
  assert inspect_case(x)['passed'],(i,inspect_case(x))
  rows.append(x);manifest.append({'index':i,'parent_sample_id':original['sample_id'],'sample_id':x['sample_id'],'source_row_sha256':row_sha(original),'parent_overlay_row_sha256':row_sha(base[original['sample_id']]),'derived_source_row_sha256':row_sha(x),'issues_addressed':c['issues'],'physical_or_vision_verification_claimed':False,'new_human_review_claim':False})
 write_rows(dest,rows);write_json(E/'pre_sft_polish_derivation_manifest_20261018.json',{'schema_version':'primary_math.polish_derivation.v1','utc':datetime.now(timezone.utc).isoformat(),'source_queue_sha256':sha((R/'pre_sft_polish_queue.json').read_bytes()),'cases':manifest,'status':'AWAITING_ACTUAL_DERIVATIVE_CONTENT_QA','original_sources_modified':False,'owner_signoffs_modified':False})
 print('DERIVED_DRAFTS',len(rows))
def show(start,end):
 rows=read_rows(R/'derived_release/pre_sft_polished_sources.jsonl')
 for i,x in enumerate(rows[start:end],start):print(json.dumps([i,x['sample_id'],x['problem'],x['givens'],x['requested_quantity'],x['student_work'],x['initial_guidance'],x['hints'],x['worked_steps'],x['expected_answer']],ensure_ascii=False))
if __name__=='__main__':
 if sys.argv[1]=='create':create()
 elif sys.argv[1]=='show':show(int(sys.argv[2]),int(sys.argv[3]))
