"""Lossless semantic-field projection for training only; source corpus untouched."""
import json,hashlib
VERSION='verbal_training_render.v1'
MODE_LABELS={'worked_solution':'Giải đầy đủ, giải thích cách làm và kiểm tra kết quả.','hint_level_1':'Gợi ý bước đầu để em tự làm. Không nêu đáp số cuối hoặc chọn đáp án thay em.','hint_level_2':'Gợi ý thêm một bước để em tự làm. Không nêu đáp số cuối hoặc chọn đáp án thay em.','hint_level_3':'Gợi ý cách kiểm tra và hoàn thiện. Không nêu đáp số cuối hoặc chọn đáp án thay em.'}
def h(s):return hashlib.sha256(s.encode('utf8')).hexdigest()
def text(value,path):
 if not isinstance(value,str):raise ValueError('Expected source text at '+path)
 return value
def prompt(p):
 if set(p)-{'grade','problem','mode','student_work'}:raise ValueError('Unsupported prompt keys; do not silently drop fields')
 if p['mode'] not in MODE_LABELS:raise ValueError('Unknown tutor mode')
 if type(p['grade']) is not int or p['grade'] not in range(1,6):raise ValueError('Invalid grade')
 parts=[f"Toán lớp {p['grade']}.",text(p['problem'],'problem'),MODE_LABELS[p['mode']]]
 if p.get('student_work') is not None:
  work=p['student_work']
  if not isinstance(work,str):raise ValueError('Student work must remain actual provided text')
  parts+=['Lời làm em đã cung cấp:',work]
 return '\n\n'.join(parts)
def target(t,mode):
 parts=[];fields=[]
 def add(label,value,path):
  value=text(value,path)
  if value:parts.append((label+': ' if label else '')+value);fields.append({'source_path':path,'value':value,'rendered_occurrences':sum(value in x for x in parts)})
 if mode!='worked_solution':
  if set(t)!={'hint','question'}:raise ValueError('Unsupported hint fields')
  add('Gợi ý',t['hint'],'hint');add('Em thử trả lời',t['question'],'question')
 else:
  if set(t)!={'can_solve','initial_guidance','steps','answer'} or type(t['can_solve']) is not bool:raise ValueError('Unsupported worked fields')
  if not all(isinstance(t[k],list) for k in ['initial_guidance','steps','answer']):raise ValueError('Expected source lists')
  if not t['can_solve']:parts.append('Chưa thể đưa ra lời giải xác định theo dữ kiện hiện có.')
  for i,v in enumerate(t['initial_guidance']):add('Hướng dẫn',v,f'initial_guidance[{i}]')
  for i,step in enumerate(t['steps']):
   if set(step)-{'step_id','title','reason','expression','result','unit','explanation'}:raise ValueError('Unsupported step fields')
   parts.append(f'Bước {i+1}')
   for key,label in [('title','Nội dung'),('reason','Vì sao'),('expression','Phép tính hoặc quan hệ'),('result','Kết quả bước này'),('unit','Đơn vị'),('explanation','Giải thích')]:
    v=step.get(key)
    if v is not None:add(label,v,f'steps[{i}].{key}')
  for i,a in enumerate(t['answer']):
   if set(a)-{'quantity','result','unit'}:raise ValueError('Unsupported answer fields')
   for key,label in [('quantity','Đại lượng cần tìm'),('result','Đáp số'),('unit','Đơn vị đáp số')]:
    if a.get(key) is not None:add(label,a[key],f'answer[{i}].{key}')
 out='\n'.join(parts)
 if not out.strip():raise ValueError('Empty projected target')
 assert all(x['value'] in out for x in fields)
 return out,{'version':VERSION,'all_nonempty_semantic_text_fields_preserved':True,'numeric_calculation_performed_by_renderer':False,'fields':fields,'excluded_internal_metadata':['steps[*].step_id'],'can_solve':t.get('can_solve'),'rendered_target_sha256':h(out)}
def render(row):
 p=json.loads(row['messages'][1]['content']);t=json.loads(row['messages'][2]['content'])
 if p['mode']!=row['mode']:raise ValueError('Source mode mismatch')
 answer,proof=target(t,row['mode'])
 messages=[row['messages'][0],{'role':'user','content':prompt(p)},{'role':'assistant','content':answer}]
 return {**row,'messages':messages},proof
