"""Independent exhaustive state/constraint reconstruction; no authored solution imports."""
from itertools import permutations,combinations,product
from fractions import Fraction as F
from decimal import Decimal
from collections import Counter
import calendar,copy
def sep(xs):return ';'.join(sorted(xs))
def show(f):
 f=F(f)
 return str(f.numerator) if f.denominator==1 else str(Decimal(f.numerator)/Decimal(f.denominator))
def solve(m):
 k=m['kind'];details={}
 if k=='angles':
  reps=[g[0] for g in m['groups']];pairs=list(combinations(reps,2));names=sorted(a+'O'+b for a,b in pairs)
  return {'Tên góc':';'.join(names),'Số góc':str(len(pairs))},{'unique_arms':reps,'unordered_pairs':[sorted(p) for p in pairs]}
 if k=='order':
  valid=[p for p in permutations(m['items']) if all(p.index(h)>p.index(l) for h,l in m['heavier'])];assert len(valid)==1
  return {'Nhẹ đến nặng':';'.join(valid[0])},{'permutations_tried':6,'valid':valid}
 if k=='pans':
  valid=[];fix=[];checks=[]
  for name,a,b,pan in m['records']:
   a,b=F(a),F(b);need='left' if a>b else 'right' if b>a else 'level';checks.append([name,str(a),str(b),need])
   if need==pan:valid.append(name)
   else:fix.append(name+':'+{'left':'trái thấp','right':'phải thấp','level':'ngang'}[need])
  return {'Bản ghi nhất quán':sep(valid),'Sửa chiều':';'.join(fix)},{'fraction_mass_comparisons':checks}
 if k=='mass_compare':
  v={a:F(b) for a,b in m['masses'].items()};order=sorted(v,key=v.get);pan='trái thấp' if v[m['left']]>v[m['right']] else 'phải thấp'
  return {'Nhẹ đến nặng':';'.join(order),'Chiều cân':pan,'Chênh lệch':show(max(v.values())-min(v.values()))},{'kg':{a:str(b) for a,b in v.items()}}
 if k in ['shelf','shelf_repair']:
  def cost(d):return F(2*d['H']*d['D']+(d['N']+2)*d['W']*d['D'],10000)*m['price']
  d=m['chosen'];assert all(type(d[x]) is int and lo<=d[x]<=hi for x,(lo,hi) in m['domain'].items());c=cost(d);assert c<=m['budget'];area=2*d['H']*d['D']+(d['N']+2)*d['W']*d['D'];spec=','.join(x+str(d[x]) for x in ['W','H','D','N'])
  if k=='shelf':r={'Thiết kế':spec,'Diện tích':str(area),'Chi phí':show(c),'Kết luận':'hợp lệ'}
  else:
   old=cost(m['old']);assert old>m['budget'];r={'Chi phí cũ':show(old),'Bản sửa':spec,'Chi phí sửa':show(c),'Kết luận':'hợp lệ'}
  return r,{'boards':{'sides':2,'horizontal':d['N']+2},'area_cm2':area,'cost_exact':str(c),'budget_slack':str(F(m['budget'])-c),'chosen_spec_only_no_optimum':True}
 if k in ['colors','colors_remaining']:
  colors=sorted(m['stock'],key=lambda c:['Đ','V','X'].index(c));expanded=[c for c in colors for _ in range(m['stock'][c])];valid=sorted({''.join(sorted((expanded[i] for i in ids),key=lambda c:colors.index(c))) for ids in combinations(range(len(expanded)),m['draw'])})
  if k=='colors':r={'Kết quả màu' if len(colors)==2 else 'Bộ màu':';'.join(valid),'Số kết quả' if len(colors)==2 else 'Số bộ':str(len(valid))}
  else:
   remaining=[]
   for s in valid:
    cnt=Counter(s);remaining.append(s+'→'+''.join(c+str(m['stock'][c]-cnt[c]) for c in colors))
   r={'Kết quả':';'.join(valid),'Kho còn':';'.join(remaining),'Số kết quả':str(len(valid))}
  return r,{'physical_subsets_tested':len(list(combinations(range(len(expanded)),m['draw']))),'distinct_color_multisets':valid}
 if k in ['incidence','incidence_broken']:
  seg=sorted({''.join(sorted(p)) for l in m.get('drawn',m['lines']) for p in combinations(l,2)});tri=sorted({''.join(sorted(p)) for l in m['lines'] for p in combinations(l,3)})
  return {'Đoạn':';'.join(seg),'Bộ ba':';'.join(tri),'Số đoạn':str(len(seg)),'Số bộ ba':str(len(tri))},{'endpoints':seg,'triples':tri,'drawn_components':m.get('drawn',m['lines'])}
 if k=='flowers':
  tokens={chr(97+i):F(v) for i,v in enumerate(m['values'])};eligible={a for a,v in tokens.items() if v==F(m['target'])};remain=set(tokens);own={'An':[],'Bình':[]};trace=[];stop=None
  for i,(who,t) in enumerate(m['moves'],1):
   assert t in remain
   if t in eligible:own[who].append(t);remain.remove(t)
   trace.append({'turn':i,'eligible_pick':t in eligible,'owned':copy.deepcopy(own),'remaining':sorted(remain)})
   if sum(map(len,own.values()))>=m['threshold']:stop=i;break
  assert stop is not None;winner=max(own,key=lambda x:len(own[x]));assert len(own['An'])!=len(own['Bình'])
  return {'Hoa hợp lệ':sep(eligible),'Chủ hoa':'An:'+','.join(own['An'])+';Bình:'+','.join(own['Bình']),'Còn trên bàn':sep(remain),'Kết luận':winner+' thắng lượt'+str(stop)},{'states':trace,'clarified_global_threshold':m['threshold']}
 if k=='memory':
  remain=set(m['cards']);own={'An':[],'Bình':[]};trace=[];stop=None
  for i,(who,a,b) in enumerate(m['moves'],1):
   assert a!=b and a in remain and b in remain
   hit=F(m['cards'][a])*F(m['cards'][b])==1
   if hit:remain-={a,b};own[who].append(''.join(sorted([a,b])))
   trace.append({'turn':i,'face_up_during_turn':[a,b],'reciprocal':hit,'face_down_after':sorted(remain),'removed':sorted(set(m['cards'])-remain),'owned':copy.deepcopy(own)})
   if len(own[who])>=m['threshold']:stop=i;winner=who;break
  assert stop is not None
  return {'Cặp sở hữu':'An:'+','.join(own['An'])+';Bình:'+','.join(own['Bình']),'Mặt còn sau lượt1':','.join(trace[0]['face_down_after'])+':úp','Kết luận':winner+' thắng lượt'+str(stop)},{'state_trace':trace}
 if k=='ambiguity':return {'Khả năng kết luận':'Chưa thể kết luận người thắng','Cần hỏi':';'.join(m['missing'])},{'missing_inputs':m['missing'],'no_winner_invented':True}
 if k in ['leap','leap_interval']:
  flags={y:calendar.isleap(y) for y in m['years']}
  # independent cross-check against integer residue definition, not a book four-year shortcut
  assert all(v==(y%400==0 or (y%4==0 and y%100!=0)) for y,v in flags.items())
  if k=='leap':r={'Năm nhuận':';'.join(str(y) for y in m['years'] if flags[y]),'Ngày tiếp':';'.join(str(y)+':'+('29/2' if flags[y] else '1/3') for y in m['years'])}
  else:r={'Tổng ngày':str(sum(366 if flags[y] else 365 for y in m['years'])),'Năm nhuận trong ba năm':';'.join(str(y) for y in m['years'] if flags[y]) or 'không có'}
  return r,{'gregorian_flags':flags,'source':'https://aa.usno.navy.mil/faq/leap_years'}
 if k=='column':
  good=[]
  for a,b in product(m['digits'],repeat=2):
   n=int(m['pattern'].replace('a',str(a)));s=int(m['result'].replace('b',str(b)))
   if n*m['factor']==s and (not m['distinct'] or a!=b):good.append((a,b))
  return {'Cặp(a,b)':';'.join(str(a)+','+str(b) for a,b in good),'Số cách':str(len(good))},{'digit_pairs_tried':len(m['digits'])**2,'valid':good,'multiplication_reconstruction':[[int(m['pattern'].replace('a',str(a))),m['factor'],int(m['result'].replace('b',str(b)))] for a,b in good]}
 if k=='card_column':
  good=[p for p in permutations(m['cards']) if (10*p[0]+p[1])*p[2]==m['target']]
  return {'Cách điền':';'.join('A'+str(a)+',B'+str(b)+',C'+str(c) for a,b,c in good),'Số cách':str(len(good))},{'permutations_tried':6,'valid':good}
 if k=='strips':
  d=m['pieces'];good=[]
  for p in permutations(d):
   if d[p[0]][0]!=m['start'] or d[p[-1]][1]!=m['end']:continue
   if all(d[p[i]][1]==d[p[i+1]][0] for i in range(len(p)-1)):good.append(p)
  if not good:r={'Chuỗi hợp lệ':'không có','Số chuỗi':'0'}
  else:
   assert len(good)==1;p=good[0];r={'Chuỗi':';'.join(p),'Số':''.join(d[a][2] for a in p),'Giá trị chữ số0':'0'}
  return r,{'ordered_permutations_tested':6,'valid':good,'original_g3_page_locator_unknown':True}
 if k in ['assign','assign_partial']:
  valid=[]
  for p in permutations(m['inventory']):
   d=dict(zip(m['people'],p))
   if all(d[a]<d[b] for a,b in m['less']):valid.append(d)
  if k=='assign':r={'Gán thẻ':';'.join(a+str(valid[0][a]) for a in m['people']),'Số cách':str(len(valid))}
  else:r={'Mọi cách':';'.join(','.join(a+str(d[a]) for a in m['people']) for d in sorted(valid,key=lambda d:tuple(d[a] for a in m['people']))),'Thẻ Nhi':'không duy nhất' if len({d['Nhi'] for d in valid})>1 else str(valid[0]['Nhi']),'Số cách':str(len(valid))}
  return r,{'permutations_tested':6,'valid':valid}
 if k=='rooms':
  inventory=[a*b for _,a,b in m['shapes']];valid=[]
  for p in set(permutations(inventory)):
   d=dict(zip(m['people'],p))
   if all(d[a]==d[b] for a,b in m['equal']):valid.append(d)
  assert len(valid)==1;v=valid[0]
  return {'Diện tích':';'.join(a+str(v[a]) for a in m['people']),'Mặt bằng':';'.join(a+(':'+'vuông' if v[a]==16 else ':'+'chữ nhật') for a in m['people'])},{'derived_area_inventory':inventory,'valid_area_assignments':valid}
 raise ValueError(k)
def check(row):
 actual={a['quantity']:a['result'] for a in row['expected_answer']};expected,proof=solve(row['independent_model'])
 unordered={'Tên góc','Bộ màu','Kết quả màu','Kết quả','Kho còn','Đoạn','Bộ ba'}
 assert set(actual)==set(expected)
 for q in expected:
  assert (set(actual[q].split(';'))==set(expected[q].split(';')) if q in unordered else actual[q]==expected[q]),(row['topic'],q,actual,expected)
 return proof
def mutations(row,h):
 expected,_=solve(row['independent_model']);out=[]
 for q,v in expected.items():
  bad=copy.deepcopy(expected);bad[q]=v+'__WRONG_OR_OMITTED_CONSTRAINT';assert bad!=expected
  out.append(dict(sample_id=row['sample_id'],source_row_sha256=h,mutation='alter_expected_field_'+q,rejected=bad!=expected,independent_expected=expected[q]))
 # Mathematical model mutations exercise constraints, not just altered answer strings.
 m=copy.deepcopy(row['independent_model']);k=m['kind'];mutated=None
 if k=='angles':
  if len(m['groups'][0])>1:m['groups'].append([m['groups'][0].pop()])
  else:m['groups'].pop()
  mutated='count_coincident_names_as_distinct_or_omit_arm'
 elif k=='pans':m['records'][0][3]='right';mutated='reverse_observed_pan'
 elif k=='mass_compare':m['left'],m['right']=m['right'],m['left'];mutated='swap_pan_identity'
 elif k in ['shelf','shelf_repair']:m['price']=1;mutated='drop_per_square_metre_price'
 elif k=='incidence':m['lines'][0].pop();mutated='omit_intermediate_endpoint'
 elif k=='incidence_broken':m['drawn'][0]=list('ABCD');mutated='invent_missing_drawn_connector'
 elif k=='flowers':m['threshold']=4;mutated='stop_at_wrong_global_threshold'
 elif k=='memory':m['threshold']=1;mutated='stop_at_wrong_pair_threshold'
 elif k=='ambiguity':m['missing'].pop();mutated='omit_required_game_state_question'
 elif k=='rooms':m['equal']=[['An','Chi']];mutated='change_identity_equality_premise'
 elif k=='colors':m['draw']+=1;mutated='wrong_draw_count'
 elif k=='colors_remaining':m['stock']['X']+=1;mutated='invent_extra_single_color_stock'
 elif k=='order':m['heavier'][0].reverse();mutated='reverse_low_pan_relation'
 elif k=='column':m['factor']+=1;mutated='wrong_one_digit_multiplier'
 elif k=='card_column':m['target']+=1;mutated='alter_fixed_product'
 elif k=='leap':m['years']=[2024,2101,2400];mutated='wrong_century_year'
 elif k=='leap_interval':m['years']=[2099,2100,2104];mutated='replace_common_with_leap'
 elif k=='assign':m['less'][0].reverse();mutated='reverse_identity_order'
 elif k=='assign_partial':m['less'].append(['Nhi','Lan']);mutated='invent_unprovided_rank'
 elif k=='strips':
  if expected.get('Số chuỗi')=='0':m['pieces']['Q'][0]='tròn';m['pieces']['Q'][1]='vuông';mutated='silently_flip_or_edit_forbidden_connector'
  else:m['pieces']['Q'][0]='invented';mutated='erase_matching_connector'
 if mutated:
  try:answer,_=solve(m);rejected=answer!=expected
  except AssertionError:rejected=True
  # In the no-solution strip variant, changing an already incompatible connector
  # leaves it unsatisfiable and is not advertised as a useful rejection test.
  if rejected:out.append(dict(sample_id=row['sample_id'],source_row_sha256=h,mutation=mutated,rejected=True))
 return out
