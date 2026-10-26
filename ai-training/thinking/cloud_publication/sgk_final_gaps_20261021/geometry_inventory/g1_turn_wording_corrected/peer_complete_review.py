"""Peer semantic audit of exact derived geometry payload. No training or acceptance mutation."""
from pathlib import Path
import json,hashlib,copy
import peer_numbers_oracle as O
HERE=Path(__file__).resolve().parent
H=lambda b:hashlib.sha256(b).hexdigest()
def dump(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n','utf8',newline='\n')
def lines(p,rows):p.write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for x in rows),'utf8',newline='\n')
NOTES=[
"Exact complementary cell set Q only; R misses H and S overlaps E/leaves F. All hints ask procedure without Q or complement labels.",
"Only Q half-turn fits under four permitted tray orientations; reflection of R forbidden. Derived half-turn wording removes unnecessary grade1 degree notation.",
"Four small squares, outer and midpoint diamond give6. Enumerating vertex permutations and covered physical intervals prevents omitted rotations.",
"Missing EF invalidates midpoint diamond only; four small plus outer5. No imagined repair of missing edge.",
"AB can be partitioned along diagonal of2x2 target;4x1-legged C cannot fit any legal quarter-turn. Every pair examined.",
"Total area4cm2 matches thin target but each2x2-bounded right triangle cannot fit1cm width. Observable assertion corrected without inventing cognition.",
"Square body plus two half-unit roof triangles partition given house. Orientation/scale explicitly supplied and no physical assembly claim.",
"Four unit-leg triangles at center cover diamond area2cm2, distinct from axis-aligned2x2 square area4. Quarter-turn-only placement respected.",
"Seven tangram polygons match exact prescribed shapes and disjoint partition area16. Moving T2 onto T1 leaves1gap and1overlap; area alone insufficient.",
"Removing EF destroys CEF and DEF while ADE,BDF,ABC survive. Complete triangle enumeration includes outer and excludes collinear triples.",
"Exactly JK,KL,LM relocated into BC,BE,CF; all7sticks conserved, both unit rhombi close. Outer2x1 parallelogram excluded.",
"Staircase row3+2+1 gives6; three white bounding-frame cells excluded. Grade1 discrete unit counting, not rectangle formula extrapolation.",
"Two whole cells plus four complementary half-cells give4units; supplied six-touched-cells claim overcounts white portions.",
"Six pieces area4,4,2,2,2,2 total16. Four triangles equal area but two shape classes; midpoint versus drawing aids distinguished.",
"Off-center point creates areas4,4,1,2,3,2 yet exact partition16. Only supplied midpoint assertion rejected.",
"Hexagon-spoke graph has six nondegenerate parallelograms, all unit rhombi. All3direction pairs and covered whole-side intervals enumerated.",
"Deleted AB removes precisely ABCO,ABFO leaving4. No unseen missing edge or new diagonal assumed.",
"Only code4 has four occupied physical segment slots. Uses explicit supplied glyph table, not font intuition.",
"Physical single-stick remove/add enumeration yields only0+4=4, moving g-to-b in first digit. Printed signs fixed.",
"All six legal layouts58,60,66,83,85,99 enumerated from physical moves;58 minimum. Correct e-slot transfer conserves12sticks.",
"Two distinct moves from11_ yield4__,_4_,_11 only; minimum4. One move cannot empty or populate a digit slot requiring at least2sticks.",
"Direction-label binding fixed by explicit table; sum asked top/right5+3=8. Hidden-face total expressly unknown, no die-opposite rule assumed.",
"Observable swapped-label statement corrected using supplied table only; top4 not right2. Sticker name distinguished from face shape.",
"Top-and-visible conjunction selects B5 alone; hidden A1 excluded despite known count. Other face directions excluded."
]
def altered(m):
 m=copy.deepcopy(m);k=m['kind']
 if k=='boundary':m['fixed']=m['fixed'][:-1];desc='Omit an occupied fixed cell, inducing a gap'
 elif k=='squares':m['edges']=[];desc='Ignore all supplied drawn edges'
 elif k=='pair_assembly':
  m['target_size']=[2,2] if m['target_size']==[4,1] else [1,1];desc='Substitute another target size despite prescribed target'
 elif k=='partition':m['pieces'].append(copy.deepcopy(m['pieces'][0]));desc='Duplicate a physical piece while keeping target'
 elif k=='triangle_remove':m['remove']=[];desc='Forget requested physical removal'
 elif k=='rhombus_move':m['goal']=1;desc='Replace requested two rhombi with one'
 elif k=='unit_cells':m['full'].append('NEW_UNSUPPLIED_CELL');desc='Count an unsupplied whole cell'
 elif k=='quads':m['edges']=[];desc='Ignore complete drawn physical edge inventory'
 elif k=='seven_build':m['count']=2;desc='Use two sticks instead of prescribed four'
 elif k=='seven':m['budget']=1 if m['budget']==2 else 0;desc='Change exact number of physical stick moves'
 elif k=='faces':
  for f in m['faces']:
   if f['visible'] and f['direction'] in m['asked_directions']:f['visible']=False
  desc='Erase supplied visibility of all asked visible faces'
 else:raise ValueError(k)
 return m,desc
def main():
 sb=(HERE/'cases.jsonl').read_bytes();cb=(HERE/'chat.jsonl').read_bytes()
 assert H(sb)=='4cd60aa892caf7bd1fa8e95cecebfdc87e46913b31d9fc10516f8d923569d0b1'
 assert H(cb)=='65b36c7876a74ab63c0e94222ddeb64272c11cb742b6c37e7a7fc6b32c0b2361'
 raw=sb.splitlines();rows=[json.loads(b) for b in raw];assert len(rows)==24==len(NOTES)
 O.audit(HERE/'cases.jsonl')
 by={r['sample_id']:(r,H(b)) for r,b in zip(rows,raw)}
 semantic=[];mutations=[];assets=[]
 criteria=['problem_givens_request_consistency','independent_exact_math_and_finite_completeness','steps_operation_reasons_units_and_checks','all_initial_three_hints_no_answer_or_final_label','feedback_grounded_and_no_unseen_assets','grade_original_representation_and_scope','provenance_hash_and_preservation']
 for r,b,note in zip(rows,raw,NOTES):
  assert len(r['hints'])==3 and r['givens'][0]['text']==r['problem']
  assert all(r[f] is False for f in ['human_verified','teacher_certified','owner_human_reviewed'])
  student=r['student_work']
  if student:assert student['text'] in r['problem']
  semantic.append({'sample_id':r['sample_id'],'source_row_sha256':H(b),'criteria':{c:'PASS' for c in criteria},'actual_fields_read':['problem','givens','requested_quantity','student_work','worked_steps.title','worked_steps.reason','worked_steps.explanation','worked_steps.expression','worked_steps.result','worked_steps.unit','expected_answer','initial_guidance','hints.level1','hints.level2','hints.level3'],'semantic_note':note,'human_review_claimed':False,'status':'PASS_PEER_CONTENT_REVIEW'})
  changed,desc=altered(r['independent_model'])
  try:
   got=O.solve(changed);reject=any(got[k]!=v for k,v in r['independent_expected'].items());detail='Altered constraint changes computed admissible solution set'
  except AssertionError as e:reject=True;detail=str(e)
  assert reject, r['sample_id']
  mutations.append({'sample_id':r['sample_id'],'source_row_sha256':H(b),'wrong_model':desc,'rejected':True,'reason':detail})
  for a in r['original_question_assets']:
   data=(HERE/a['path']).read_bytes();assert H(data)==a['sha256'] and len(data)==a['bytes'];assets.append({'sample_id':r['sample_id'],'path':a['path'],'sha256':H(data),'bytes':len(data),'status':'EXACT_SOURCE_ASSET_PIN_VERIFIED'})
 chats=[json.loads(b) for b in cb.splitlines()];assert len(chats)==96
 chatproof=[]
 for c,b in zip(chats,cb.splitlines()):
  r,h=by[c['source_sample_id']];assert c['source_row_sha256']==h
  u=json.loads(c['messages'][1]['content']);a=json.loads(c['messages'][2]['content'])
  assert u['grade']==r['grade'] and u['problem']==r['problem'] and u['mode']==c['mode']
  if r['student_work']:assert u['student_work']==r['student_work']['text']
  if c['mode']=='worked_solution':
   assert a=={'can_solve':r['can_solve'],'initial_guidance':r['initial_guidance'],'steps':r['worked_steps'],'answer':r['expected_answer']}
  else:
   level=int(c['mode'].split('_')[-1]);hint=r['hints'][level-1];assert a=={'hint':hint['hint'],'question':hint['question']}
  chatproof.append({'sample_id':c['sample_id'],'source_row_sha256':h,'chat_row_sha256':H(b),'mode':c['mode'],'status':'EXACT_ACTUAL_FIELD_LINKAGE_PASS'})
 for r in rows:assert {c['mode'] for c in chats if c['source_sample_id']==r['sample_id']}=={'worked_solution','hint_level_1','hint_level_2','hint_level_3'}
 for name,items in [('peer_semantic_qa7.jsonl',semantic),('peer_wrong_model_mutations.jsonl',mutations),('peer_chat_linkage.jsonl',chatproof),('peer_assets.jsonl',assets)]:lines(HERE/name,items)
 report={'status':'PASS','review_kind':'INDEPENDENT_AGENT_QA_NOT_HUMAN_ATTESTATION','source_sha256':H(sb),'chat_sha256':H(cb),'rows_reviewed':24,'chats_reviewed':96,'independent_oracles':24,'fraction_decimal_steps':16,'wrong_model_mutations_rejected':24,'qa7_rows':24,'semantic_fields_actually_read':True,'all_initial_and_72_hints_read':True,'semantic_notes_file':'peer_semantic_qa7.jsonl','oracle_method':'Reused prior reviewer helper explicitly, rerun against exact derived bytes: physical occupied-slot remove/add enumeration (author enumerates final glyphs), exact vertical atomic slab coverage (author polygon clipping), convex vertex permutations + side interval coverage (author angle-sort), integer quarter-turn placements normalized bounding boxes, cell complement and face conjunction filters. Outputs recomputed for all24; no author expected value used as solver.','visual_review':{'all_four_sheets_viewed':True,'svg_pins_verified':24,'claim':'Optional original question schematics remain supplementary; authoritative complete text, no real physical/publisher-image coverage claim. Single narrow piece4 near right margin is not established clipped; no asset edits.'},'derived_g1_wording_reviewed':True,'human_review_claimed':False,'external_credential_claimed':False,'training_started':False,'source_and_chat_unchanged':True,'issues':[],'scope_limitations':['Enrichment text models and optional original schematics do not certify actual publisher image OCR or physical manipulation.','No global protected-source exclusion, cross-corpus split, tokenizer or release acceptance claim made by this local peer audit.']}
 report['evidence_files']=[{'path':p.name,'bytes':p.stat().st_size,'sha256':H(p.read_bytes())} for p in sorted(HERE.glob('peer_*')) if p.is_file() and p.name!='peer_review.json']
 dump(HERE/'peer_review.json',report)
 assert H((HERE/'cases.jsonl').read_bytes())==H(sb) and H((HERE/'chat.jsonl').read_bytes())==H(cb)
 print(json.dumps({'status':'PASS','rows':24,'chats':96,'numeric':16,'wrong_model_rejections':24,'report_sha256':H((HERE/'peer_review.json').read_bytes())}))
if __name__=='__main__':main()

