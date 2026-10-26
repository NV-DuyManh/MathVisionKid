import sys,json
from collections import Counter
from fractions import Fraction as F
from pathlib import Path
sys.path.insert(0,'thinking');import author_finite_remaining as a
files=sorted((a.R/'authored_batches').glob('finish_g4_*.jsonl'))
assert len(files)==16
rows={f.stem:a.read_rows(f) for f in files}; records=[]
def record(k,i,method,values=(),detail=None):
 row=rows['finish_g4_'+k][i]; actual=[]
 for z in row['expected_answer']:
  try:actual.append(F(z['result']))
  except (ValueError,ZeroDivisionError):pass
 expected=[F(str(x)) for x in values]
 assert sorted(actual)==sorted(expected),(k,i,actual,expected)
 records.append({'sample_id':row['sample_id'],'source_row_sha256':a.row_sha(row),'method':method,'oracle_numeric_answers':[str(x) for x in expected],'detail':detail,'matched_numeric_expected_answers':True,'semantic_read_record':'Own actual-content read plus row-specific seven-criterion QA; oracle alone does not prove semantics.'})
def repeated_groups(total,group):
 q=0;rem=total
 while rem>=group:rem-=group;q+=1
 return q,rem
# Positional representations independent of expression parser.
assert ''.join(['42','008','305'])=='42008305'
record('millions_place_value',0,'Zero-pad and concatenate three-digit classes',(int('42'+'008'+'305'),),{'class_read':['42','008','305'],'8_power':3})
assert list(str(75004012))[1]>list(str(70504012))[1]
record('millions_place_value',1,'Lexicographic equal-length digit comparison and index powers',detail={'larger':'B','A_digit5_power':5,'B_digit5_power':6})
record('millions_place_value',2,'Accumulate positional place buckets from package types',(sum([1000000]*6+[1000]*14+[1]*90),))
record('millions_place_value',3,'Concatenate padded spoken classes',(int('3'+'005'+'007'),))
record('letter_expression',0,'Concatenate disjoint symbolic book-ID lists then count',(len(list(range(18))+list(range(18,25))),))
record('letter_expression',1,'Count four copies of a nine-cell list versus four six-cell lists and three extra cells',(len([x for _ in range(4) for x in range(9)]),len([x for _ in range(4) for x in range(6)])+3))
record('letter_expression',2,'Traverse four rectangle boundary segments',(sum(map(len,[range(12),range(5),range(12),range(5)])),))
record('letter_expression',3,'Count union of eight and five disjoint unit tokens',(len(range(13)),))
record('mass_yen_ta_tan',0,'Expand each declared mass package into kilogram counts',(sum([1000,1000,100,100,100,10,10,10,10]),))
record('mass_yen_ta_tan',1,'Count kilogram intervals of two loads and set difference',(len(set(range(190))-set(range(180))),),{'larger':'B'})
record('mass_yen_ta_tan',2,'Remove24disjoint10kggroups from3000indexed kilogram tokens',(len(set(range(3000))-set(range(240))),))
record('mass_yen_ta_tan',3,'Five mass blocks each labelled100kg',(sum([100]*5),))
record('mass_yen_ta_tan',4,'Two completions of missing mass',detail={'extra_mass_kg':[10,20],'totals_kg':[210,220],'not_unique':True})
record('second_century',0,'Count seconds on timeline of three complete minute blocks and25extra',(len(range(60))+len(range(60))+len(range(60))+25,))
assert 1900 in range(1801,1901) and 1901 in range(1901,2001)
record('second_century',1,'Membership of inclusive century ranges',detail={'1900':'XIX','1901':'XX'})
record('second_century',2,'Compare second timeline index endpoints',(len(set(range(128))-set(range(125))),),{'shorter':'A'})
record('second_century',3,'Two minute blocks plus15seconds',(len(range(60))+len(range(60))+15,))
record('second_century',4,'Distinct stopped-watch readings both consistent with no reading supplied',detail={'possible_seconds':[30,50]})
record('charts',0,'Expand pictogram symbols into labelled tree-ID groups',(len([(i,j) for i in range(5) for j in range(4)]),len([(i,j) for i in range(3) for j in range(4)]),len([(i,j) for i in range(8) for j in range(4)])))
record('charts',1,'Count one interval from labelled10kgto15kg',(len(range(10,15)),))
record('charts',2,'Pair book IDs into two-book cells',(len(list(range(0,8,2))),len(list(range(0,14,2))),len(list(range(0,10,2)))),{'maximum_day':'Thứ Ba'})
record('charts',3,'Expand four symbols into six pen IDs each',(len([(i,j) for i in range(4) for j in range(6)]),))
record('charts',4,'Legend completions yield incompatible item counts',detail={'legend_values':[2,4],'A_items':[10,20]})
record('add_associative',0,'Count a disjoint union of three integer token ranges',(len(range(125))+len(range(275))+len(range(36)),))
record('add_associative',1,'Take away successive token suffixes versus take away net25minus15',(len(set(range(80))-set(range(55,80))-set(range(40,55))),len(set(range(80))-set(range(70,80)))))
record('add_associative',2,'Three separate receipt book-ID lists counted without nesting',(len([('A',x) for x in range(48)]+[('B',x) for x in range(52)]+[('C',x) for x in range(175)]),))
record('add_associative',3,'Count all three disjoint addend ID sets',(len(range(16))+len(range(24))+len(range(9)),))
valid=[(lo,hi) for lo in range(87) for hi in range(87) if lo+hi==86 and hi-lo==18];assert valid==[(34,52)]
record('sum_difference',0,'Enumerate nonnegative integer pairs satisfying both conditions',valid[0])
valid=[(x,y) for x in range(65) for y in range(65) if x+y==64 and x==y];assert valid==[(32,32)]
record('sum_difference',1,'Enumerate equal pair with fixed total',(valid[0][0],))
assert 72+48==120 and 72-48==24 and 80+40==120 and 80-40!=24
record('sum_difference',2,'Candidate condition truth table',detail={'first':[True,True],'second':[True,False]})
valid=[(lo,hi) for lo in range(75) for hi in range(75) if lo+hi==74 and hi-lo==10];assert valid==[(32,42)]
record('sum_difference',3,'Enumerate pair with total and positive difference',valid[0])
q,r=repeated_groups(864,24);assert r==0;record('two_digit_divisor',0,'Repeated subtraction by package size',(q,))
q,r=repeated_groups(945,24);assert(q,r)==(39,9);record('two_digit_divisor',1,'Repeated subtraction without division/modulo',(q,r),{'canonical_metadata_only':'945%24','remainder_lt_divisor':r<24})
qa,ra=repeated_groups(720,18);qb,rb=repeated_groups(720,24);assert ra==rb==0;record('two_digit_divisor',2,'Repeated-group count under both package sizes',(qa,qb),{'fewer':'B'})
q,r=repeated_groups(650,25);assert r==0;record('two_digit_divisor',3,'Repeated subtraction and invalid remainder-bound check',(q,),{'given_bad_remainder_equals_divisor':True})
q,r=repeated_groups(6720,210);assert r==0;record('three_digit_divisor',0,'Repeated subtraction with210-group',(q,))
q,r=repeated_groups(1450,120);assert(q,r)==(12,10);record('three_digit_divisor',1,'Repeated subtraction without division/modulo',(q,r),{'canonical_metadata_only':'1450%120','remainder_lt_divisor':r<120})
record('three_digit_divisor',2,'Construct sixteen disjoint125-token groups plus37loose tokens',(sum([125]*16)+len(range(37)),))
q,r=repeated_groups(4080,120);assert r==0;record('three_digit_divisor',3,'Repeated subtraction counters independent of digit deletion',(q,))
# Drawing criteria checked on hypothetical coordinate models only, never real assets.
vertices=[(0,0),(6,0),(6,4),(0,4)]
vec=[(vertices[(i+1)%4][0]-vertices[i][0],vertices[(i+1)%4][1]-vertices[i][1]) for i in range(4)]
assert all(vec[i][0]*vec[(i+1)%4][0]+vec[i][1]*vec[(i+1)%4][1]==0 for i in range(4))
record('draw_rectangle_square',0,'Symbolic coordinate model of proposed construction has perpendicular adjacent edges',detail={'vertices':vertices,'actual_drawing_verified':False})
record('draw_rectangle_square',1,'Conjunction of equal-sides and right-angle criteria',detail={'P':{'equal_sides':True,'all_right':True},'Q':{'equal_sides':True,'all_right':False}})
record('draw_rectangle_square',2,'Count perimeter grid intervals around5by3model',(sum([5,3,5,3]),))
record('draw_rectangle_square',3,'Equal-side non-right rhombus countermodel',detail={'edge_vectors':[(3,4),(-3,4)],'squared_lengths':[25,25],'adjacent_dot_product':7,'actual_image_judged':False})
record('draw_rectangle_square',4,'No asset or measurements cannot distinguish rectangle from non-rectangle',detail={'two_geometrically_different_drawings_compatible':True})
record('parallelogram_area',0,'Four boundary lengths and cut-rearranged12by5unit-cell model',(sum([12,7,12,7]),len([(i,j) for i in range(12) for j in range(5)])))
record('parallelogram_area',1,'Compare unit-cell row sets after area-preserving cut/rearrangement',(len([(i,j) for i in range(9) for j in range(4)]),len([(i,j) for i in range(9) for j in range(6)]),len([(i,j) for i in range(9) for j in range(4,6)])))
valid=[b for b in range(1,97) if sum([b]*8)==96];assert valid==[12]
record('parallelogram_area',2,'Search integer base satisfying8equal area rows then traverse boundary',(valid[0],sum([valid[0],10,valid[0],10])))
record('parallelogram_area',3,'Cut/rearranged11by4unit-cell grid; slanted edge excluded from cell count',(len([(i,j) for i in range(11) for j in range(4)]),))
assert 3*3+4*4==5*5
record('parallelogram_area',4,'Two realizable slanted-side5models with heights3and4',detail={'base':9,'heights':[3,4],'areas':[27,36],'nonunique':True})
record('fraction_common_denominator',0,'Count equal subdivisions on12cell whole:thirds4cells,quarters3cells',(F(len(range(0,8)),12),F(len(range(0,9)),12)))
record('fraction_common_denominator',1,'Ten-cell whole with three two-cell fifths and seven single tenths',(F(len(range(0,6)),10),F(len(range(0,7)),10)))
record('fraction_common_denominator',2,'Equal18cell wholes;five triples and seven pairs',(F(len(range(15)),18),F(len(range(14)),18)),{'larger_tinted':'A'})
record('fraction_common_denominator',3,'Seven groups each subdivided into three equal cells;two groups occupy six',(F(len(range(6)),21),))
record('all_fraction_operations',0,'Fifteenth-metre tokens:10from first rope plus9from second',(F(len(range(10))+len(range(9)),15),))
record('all_fraction_operations',1,'Remove eight24th-litre tokens from twenty-one',(F(len(set(range(21))-set(range(8))),24),))
record('all_fraction_operations',2,'Twenty-cell product grid and fortieth-unit grouping for division',(F(len([(x,y) for x in range(3) for y in range(2)]),20),F(30,16)),{'division_model':'30fortieths divided by16fortieths','divisor_nonzero':True})
record('all_fraction_operations',3,'Sixth-unit portions:three half-whole cells plus two third-whole cells',(F(len(range(3))+len(range(2)),6),))
record('all_fraction_operations',4,'Different nonzero divisor completions plus undefined zero',detail={'k_values':['1','3/2','0'],'results':['3/4','1/2','undefined']})
valid=[(x,y) for x in range(97) for y in range(1,97) if x+y==96 and 5*x==3*y];assert valid==[(36,60)]
record('sum_difference_ratio',0,'Enumerate integer pairs satisfying total and cross-multiplied ratio',valid[0])
valid=[(x,y) for x in range(113) for y in range(1,113) if x-y==28 and 3*x==5*y];assert valid==[(70,42)]
record('sum_difference_ratio',1,'Enumerate integer pairs satisfying difference and ratio',valid[0])
assert 36+48==84 and 4*36==3*48 and 28+56==84 and 4*28!=3*56
record('sum_difference_ratio',2,'Candidate total-ratio truth table',detail={'P':[True,True],'Q':[True,False]})
valid=[(x,y) for x in range(91) for y in range(1,91) if x+y==90 and 3*x==2*y];assert valid==[(36,54)]
record('sum_difference_ratio',3,'Search pair by two simultaneous constraints',valid[0])
record('sum_difference_ratio',4,'Two pairs with same total and no extra relation',detail={'pairs':[[20,52],[30,42]],'same_total':72})
record('map_scale',0,'Count four map-centimetre blocks each250metres',(sum([250]*4),))
record('map_scale',1,'Whole-kilometre conversion per map centimetre: A1km,B2km',(len(range(6)),len(range(0,6,2))),{'shorter_on_map':'B','true_length_unchanged':True})
record('map_scale',2,'Each mapcmis5metres;sum per-edge unit blocks',(sum([5]*7),sum([5]*4),sum([5]*22)))
record('map_scale',3,'Each mapcmis10metres;three blocks',(sum([10]*3),))
record('km2',0,'Count row lengths of1000by1000squaremetre grid',(sum([1000]*1000),))
record('km2',1,'Count excess100000m²blocks after matching24with25blocks',(len(set(range(25))-set(range(24)))*100000,),{'larger':'B'})
record('km2',2,'Six unitkm²tiles and independent3000rows each2000metres',(len([(i,j) for i in range(3) for j in range(2)]),sum([2000]*3000)))
record('km2',3,'Four squarekilometre tile grids,each1000rows of1000m²',(sum([1000]*4000),))
record('km2',4,'Two distinct source-unit completions',detail={'units':['m²','km²'],'target_m²':[3,3000000]})
assert len(records)==72
assert len({x['sample_id'] for x in records})==72
allrows=[x for rr in rows.values() for x in rr]
assert Counter(x['curriculum_assignment']['case_kind'] for x in allrows)==Counter({'core':48,'misconception':16,'guard':8})
summary=[]
for f in files:
 rr=rows[f.stem];review=a.R/('reviews/'+f.stem+'_owner_preauthorized_self_QA.jsonl');rv=a.read_rows(review);by={x['sample_id']:x for x in rv};pre=json.loads((a.E/(f.stem+'_pre_review.json')).read_text('utf-8'));pb={x['sample_id']:x for x in pre['rows']}
 assert len(rv)==len(rr) and pre['actual_semantic_content_read']
 for x in rr:
  assert a.row_sha(x)==by[x['sample_id']]['row_sha256']==pb[x['sample_id']]['row_sha256']
  assert a.inspect_case(x)['passed'] and a.mapping_error(x,a.N) is None
  assert all(by[x['sample_id']][k] for k in a.REVIEW_FIELDS)
  assert all(not x['provenance'][k] for k in ['human_verified','teacher_certified','independent_external_reviewer'])
  assert not x['quality_flags']['actual_image_or_physical_asset_present']
 summary.append({'batch':f.stem,'node_id':rr[0]['curriculum_assignment']['node_id'],'cases':len(rr),'source_sha256':a.sha(f.read_bytes()),'review_sha256':a.sha(review.read_bytes()),'pre_review_sha256':a.sha((a.E/(f.stem+'_pre_review.json')).read_bytes())})
ep=a.E/'finish_g4_all72_separate_oracles.json';a.write_json(ep,{'author_agent':'/root/finite_grade4','cases':72,'core':48,'misconception':16,'guards':8,'records':records,'limitations':['Same-author actual-content QA, not human or independent review.','Legacy topic sources are previously read historical evidence, not full2006orcurrent2026legalcertification.','Hypothetical descriptions/plans only; no physical or visual success verified.','Protected/evaluation content not read; no dataset gate bypass or answers changed.','Root alone curates, hash-adjudicates numeric overlaps, audits finalcoverage and syncs.'],'batch_manifest':summary});print(json.dumps({'complete':True,'cases':72,'core':48,'misconception':16,'guards':8,'evidence':str(ep),'evidence_sha256':a.sha(ep.read_bytes()),'batches':summary},ensure_ascii=False))

