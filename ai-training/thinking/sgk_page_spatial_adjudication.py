"""Retain cross-grade merges and honest unresolved spatial backlog."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).parent/'cloud_publication/sgk_page_audit_20261019'
OUT=ROOT/'g3_spatial_append'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 old=json.loads((ROOT/'g3_audit/candidate_adjudication.json').read_text('utf8'))
 src={}
 for l in (ROOT/'current_sources.jsonl').read_bytes().splitlines():
  r=json.loads(l)
  if r.get('split','train')=='train' and not any(w in r['sample_id'].lower() for w in ['eval','holdout','pilot','protected']):src[r['sample_id']]=(r,sha(l))
 selected=[]
 names={'g3_composite_polygon_count':'composite_polygon_enumeration','g3_fixed_stick_rectangles':'fixed_stick_rectangle_inventory','g3_painted_cube_faces':'assembled_cube_painted_faces'}
 for a in old['adjudications']:
  if a['candidate_id'] not in names:continue
  n=dict(a)
  n['draft_topic']=names[a['candidate_id']]
  n['status']='ORIGINAL_DRAFTS_CREATED_CROSS_REVIEW_PENDING'
  n['nearest_full_field_review_evidence']=[]
  for near in a['nearest_actual_training_sources']:
   row,h=src[near['sample_id']]
   assert h==near['source_row_sha256']
   n['nearest_full_field_review_evidence'].append(dict(sample_id=row['sample_id'],source_row_sha256=h,actual_fields_read=['problem','givens','requested_quantity','student_work','worked_steps','reason','explanation','expected_answer','initial_guidance','all_three_hints'],semantic_difference=a['semantic_adjudication']))
  n['authoring_performed']=True
  n['authoring_source_file']='g3_spatial_append/cases.jsonl'
  selected.append(n)
 g2=[json.loads(l) for l in (ROOT/'g2v1_audit/page_review.jsonl').read_text('utf8').splitlines()]
 g3=[json.loads(l) for l in (ROOT/'g3_audit/page_review.jsonl').read_text('utf8').splitlines()]
 def refs(rows,pages,book):
  return [dict(book_id=book,printed_page=r['printed_page'],source_image_sha256=r.get('image_sha256'),image_url=r.get('image_url',r.get('public_image_url')),basis='PARENT_OR_PRIOR_AGENT_ACTUAL_IMAGE_RECEIPT; not independently re-viewed by replacement agent') for r in rows if r.get('book_id',book)==book and r.get('printed_page') in pages]
 merges=[
 dict(canonical_form='composite_polygon_enumeration',sources=refs(g2,[104,111,131],'g2v1')+refs(g3,[22,57,66],'g3v1'),resolution='One merged three-case draft family; triangle and axis-aligned rectangle analogues only. Arbitrary quadrilateral enumeration, square-only subset counts and actual-pixel recognition remain separate pending scope.'),
 dict(canonical_form='area_preserving_cut_rearrangement',sources=refs(g2,[106,107],'g2v1')+refs(g3,[27],'g3v2'),resolution='Merge with G4 dissection candidate; no new case authored in this nine-case batch.'),
 dict(canonical_form='fixed_piece_assembly_feasibility',sources=refs(g2,[106,107,131],'g2v1')+refs(g3,[33],'g3v2'),resolution='Merge with G4 silhouette/polyomino candidate. Explicit piece geometry and allowed transformations required; pending.'),
 dict(canonical_form='collinear_enumeration_and_segment_pairs',sources=refs(g2,[98,99,100,101,110,111,130],'g2v1'),resolution='Merge with G3 collinearity and G4 edge/ray enumeration; not covered by triangle-count cases alone.'),
 dict(canonical_form='two_draw_multiset_without_replacement',sources=refs(g3,[59,109,124],'g3v2'),resolution='Merge G4 same-content candidate; actual valid train rows must be compared before authoring.'),
 dict(canonical_form='finite_inventory_collection_game',sources=refs(g3,[69],'g3v2'),resolution='Merge G2/G4 finite game; rule and state completeness pending source comparison.'),
 dict(canonical_form='non_overlapping_activity_interval_choice',sources=refs(g3,[84],'g3v2'),resolution='Pending full-field nearest train comparison; no new case authored.'),
 ]
 record=dict(selected_draft_forms=selected,cross_grade_merges=merges,source_file_sha256=sha((ROOT/'current_sources.jsonl').read_bytes()),source_line_count=len((ROOT/'current_sources.jsonl').read_bytes().splitlines()),protected_eval_pilot_used=False,semantic_review_scope='Six full nearest train rows read for three selected forms; keyword/index search is retrieval only, not proof of exhaustive semantic absence. Existing valid data retained.',draft_source_sha256=sha((OUT/'cases.jsonl').read_bytes()),case_count=9)
 (OUT/'adjudication.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 summary=json.loads((ROOT/'g3_audit/summary.json').read_text('utf8'))
 summary.update(network_access_used_for_remaining_actual_page_images=True,new_case_count=9,new_cases_status='DRAFT_PENDING_CONTENT_CROSS_REVIEW',boundary_label_correction={'g3v1':{'unnumbered_array_positions_1based':[1,2,3,4,5,124],'glossary_printed_pages':[122,123]},'g3v2':{'unnumbered_or_front_matter_array_positions_1based':[1,2,3,128],'glossary_printed_pages':[127]},'note':'Historical receipt printed_page for front/colophon rows is an array label; do not claim a printed footer there. Content and numbered glossary pages verified separately.'})
 (ROOT/'g3_audit/summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'adjudication_sha256':sha((OUT/'adjudication.json').read_bytes()),'selected_forms':len(selected),'merges':len(merges)}))
if __name__=='__main__':main()
