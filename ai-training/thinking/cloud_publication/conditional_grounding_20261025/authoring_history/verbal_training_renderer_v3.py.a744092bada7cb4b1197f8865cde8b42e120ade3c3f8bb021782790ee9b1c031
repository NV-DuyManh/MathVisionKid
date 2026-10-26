"""Lossless semantic-field projection for training only; source corpus untouched."""
import json,hashlib
VERSION='verbal_training_render.v3'
MODE_LABELS={'worked_solution':'Giải đầy đủ, giải thích cách làm và kiểm tra kết quả.','hint_level_1':'Gợi ý bước đầu để em tự làm. Không nêu đáp số cuối hoặc chọn đáp án thay em.','hint_level_2':'Gợi ý thêm một bước để em tự làm. Không nêu đáp số cuối hoặc chọn đáp án thay em.','hint_level_3':'Gợi ý cách kiểm tra và hoàn thiện. Không nêu đáp số cuối hoặc chọn đáp án thay em.'}
def h(s):return hashlib.sha256(s.encode('utf8')).hexdigest()
def text(value,path):
 if not isinstance(value,str):raise ValueError('Expected source text at '+path)
 return value
def prompt(p):
 if set(p)-{'grade','problem','mode','student_work','givens','requested_quantity'}:raise ValueError('Unsupported prompt keys; do not silently drop fields')
 if p['mode'] not in MODE_LABELS:raise ValueError('Unknown tutor mode')
 if type(p['grade']) is not int or p['grade'] not in range(1,6):raise ValueError('Invalid grade')
 parts=[f"Toán lớp {p['grade']}.",text(p['problem'],'problem'),MODE_LABELS[p['mode']]]
 if p.get('givens'):
  if not isinstance(p['givens'],list):raise ValueError('Givens must retain original source list')
  parts.append('Dữ kiện đã cho:')
  for given in p['givens']:
   if set(given)-{'id','role','text','value','unit'}:raise ValueError('Unsupported given fields')
   parts.append(text(given['text'],'givens.text'))
   if given.get('value') is not None:
    value=given['value']
    if isinstance(value,(dict,list,bool)):raise ValueError('Unsupported given value')
    parts.append('Giá trị đã cho: '+str(value))
   if given.get('unit'):parts.append('Đơn vị dữ kiện: '+text(given['unit'],'givens.unit'))
 if p.get('requested_quantity'):parts.append('Cần tìm: '+text(p['requested_quantity'],'requested_quantity'))
 if p.get('student_work') is not None:
  work=p['student_work']
  if isinstance(work,dict):
   if set(work)-{'text','observations','origin'}:raise ValueError('Unsupported student work fields')
   parts+=['Lời làm em đã cung cấp:',text(work['text'],'student_work.text')]
   for observation in work.get('observations',[]):
    if set(observation)-{'excerpt','claim_scope','nature'}:raise ValueError('Unsupported student observation')
    parts+=['Trích lời làm đã cung cấp:',text(observation['excerpt'],'student_work.observation.excerpt')]
  elif isinstance(work,str):parts+=['Lời làm em đã cung cấp:',work]
  else:raise ValueError('Student work must remain actual provided text')
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
   if set(step)-{'step_id','title','reason','expression','result','unit','explanation','display_expression','display_result','exact_result_rational','relation_type'}:raise ValueError('Unsupported step fields')
   parts.append(f'Bước {i+1}')
   for key,label in [('title','Nội dung'),('reason','Vì sao'),('expression','Phép tính hoặc quan hệ'),('display_expression','Phép tính trình bày'),('result','Kết quả bước này'),('display_result','Kết quả trình bày'),('exact_result_rational','Giá trị chính xác'),('unit','Đơn vị'),('explanation','Giải thích')]:
    v=step.get(key)
    if v is not None:add(label,v,f'steps[{i}].{key}')
  for i,a in enumerate(t['answer']):
   if set(a)-{'quantity','result','unit','display_result','exact_result_rational'}:raise ValueError('Unsupported answer fields')
   for key,label in [('quantity','Đại lượng cần tìm'),('result','Đáp số'),('display_result','Đáp số trình bày'),('exact_result_rational','Đáp số chính xác'),('unit','Đơn vị đáp số')]:
    if a.get(key) is not None:add(label,a[key],f'answer[{i}].{key}')
 out='\n'.join(parts)
 if not out.strip():raise ValueError('Empty projected target')
 assert all(x['value'] in out for x in fields)
 return out,{'version':VERSION,'all_nonempty_semantic_text_fields_preserved':True,'numeric_calculation_performed_by_renderer':False,'fields':fields,'excluded_internal_metadata':['steps[*].step_id','steps[*].relation_type','givens[*].id','givens[*].role','student_work.origin','student_work.observations[*].nature','student_work.observations[*].claim_scope'],'can_solve':t.get('can_solve'),'rendered_target_sha256':h(out)}
def render(row):
 p=json.loads(row['messages'][1]['content']);t=json.loads(row['messages'][2]['content'])
 if p['mode']!=row['mode']:raise ValueError('Source mode mismatch')
 answer,proof=target(t,row['mode'])
 messages=[row['messages'][0],{'role':'user','content':prompt(p)},{'role':'assistant','content':answer}]
 return {**row,'messages':messages},proof
