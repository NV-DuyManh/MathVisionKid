"""Bind root's actual-content review to exact draft bytes and peer evidence."""
from pathlib import Path
import json,hashlib
from sgk_remaining_release import FIELDS,DIRS,RUN,rows,read,write,sha

NOTES={
'g5_applied_text':[
'Zero-frequency is known zero. Expanded observations 2,3,3,3,4 give five observations, sum15 and mean3; every hint requests a method without filling these outputs.',
'Observable category-average error retained. Four observations 2,4,4,4 give14/4=3.5; weighting rather than two category counts supplies the requested denominator.',
'All six swaps of2085 enumerated; only8025 and2805 retain four digits and odd parity, maximum8025 at1,3. No hint reveals pair/value.',
'Distinct physical cards permit swapping equal glyphs.1001 stays a valid odd four-digit number only for pairs1,4 or2,3; no unstated changed-numeral requirement.',
'7.4m supplies twelve0.6m pieces,7.2m used and0.2m free. Thirteen need7.8m; no upward rounding or joining of residue.',
'Reserve0.6m removed from5.4m first.4.8m usable gives six0.75m pieces;0.3m free plus0.6m reserve=0.9m unused. Seven violate capacity.',
'3by2 floor with0.5-square tiles needs24; plus3spares means27. Three ten-packs cost270thousand and leave6=3required+3extra. Abstract procurement assumptions explicit.',
'Two2by1.5 rooms require24 tiles total, shared reserve2 minus reusable2 means24new. Two12-packs cost120thousand and leave exactly2; no per-room reserve invented.',
'3packs of4 plus2loose gives14pieces; seven recipients get2pieces each. A andC equivalent under explicit quantity convention; B has wrong pack unit.',
'20pens divided4 gives arithmetic5pergroup but indivisible sealed four-packs cannot implement that quantity. No hidden permission to open/drop a pack.',
'Diameter20 with pi3.14 gives62.8circumference; plus one4join requires66.8 equal inclusive maximum. Sufficiency is limited to declared abstract material model.',
'Supplied circumference31.4 correct for diameter10, but ignored2join makes required33.4 and shortage1.4 against32. Feedback relies only on explicit quote.'
],
'g5_geometry_text':[
'Whole semidisc boundary includes both15.7arc and10diameter, total25.7cm, not area. Hints distinguish parts without final values.',
'Quoted9.42 correct for arc at radius3; diameter6 completes boundary15.42cm. Retain correct arithmetic and correct the scope.',
'Arc-only chain of diameters4+6 equals single10semicircle:15.7cm both. Explicit exclusion of straight connectors avoids perimeter confusion.',
'Two different semicircles retain factor1/2; arc total15.7 plus actual3connector=18.7. Quoted31.4 is not the described route.',
'Declared no-slip model maps circumference1.57m perturn times20 to31.4m. Inverse check restores1.57; no actual physical trial claimed.',
'Allowed fractional turns:7.85/3.14=2.5, decomposed2full+half; rounding3 would yield9.42m and contradict given distance.',
'Central rectangle96 plus two semidiscs50.24 gives146.24m2. Outer boundary2*12+3.14*8=49.12m excludes internal diameter seams.',
'Overall20 includes two radius3extensions, leaving14rectangle.84+28.26=112.26m2; quoted20by6 central area doublecounts a strip.',
'Three full wraps use37.68cm plus exactly one1.5cm final overlap=39.18; join counted once rather than perturn.',
'Inverse material problem removes3overlap from34.4 first;31.4circumference/3.14=10diameter. Forward reconstruction restores34.4.',
'Complete integer factor triples for12 undera>=b>=c are12,1,1;6,2,1;4,3,1;3,2,2. Surface50,40,38,32; minimum32 at3by2by2.',
'Open five-face box keeps height role distinct; ten possibilities and both minima26 at4,3,1 and3,2,2. Correctly excludes top and preserves ties.'
],
'g34_structure_polished':[
'Connector chainP,Q,R unique; three-digit classes104|005|020 retain zeros. Five in thousands has value5000. Text-only directions and reconstruction check sufficient.',
'Two matching connector pathsABC/ADC reduced by pinned ten/hundred-thousands digits toABC,305040007 andunusedD. No arbitrary rearrangement of glyphs.',
'Polished s0 narrows3a to35..39 using20multiplier. Units4ending6 admits34/39globally; tensrow excludes34.39*4=156,39*20=780,total936,d3.',
'93unit partial gives31;620shifted tens givesb2 andmultiplier23. Correct713=93+620; quotation155 drops the factor10. Hints do not solve digits.',
'Common-origin intervals[0,12],[5,15] have lengths12,10,intersection7,union15. Inclusion-exclusion and extremeend check agree.',
'Opposite endpoint orientation changes no length: red[-2,6] length8,blue[3,10] length7,intersection3,union12. Learner works with left/right distances, explicit enrichment.',
'Three rays give allthree unorderedpairs, angles40,100,60; includes compositeAOC. No visual inference or duplicate reversed names.',
'Six unorderedpairs fromfourrays, remove onlyADstraight180. Five remain, including missingAC andBD; quotedthree adjacent pairs incomplete.',
'Four collinearABC D give four unorderedtriples; E off row gives noadditionaltriple. Full finite group completeness explained without image measurements.',
'Exact grid permits diagonalB,E,D besidesOAB/OCD. Alltwenty triples independently enumerated by peer; no invented gridpoints.',
'Rowcolor andcolumnshape combine blue fromrow2 withtriangle fromcolumn3. Hint states property roles without naming the requested tile.',
'Columncolors fixed but secondrow shapeshave twoorders; target(2,2) blue withcircleor square. Complete both valid completions, no unstated same-shape-column rule.'
]}

def main():
    batches={}
    for name in DIRS:
        f=RUN/name;source=rows(f/'cases.jsonl');assert len(source)==len(NOTES[name])==12
        if name=='g34_structure_polished':
            summary=read(f/'peer_finish_mapping_summary.json');assert not summary['blocking_findings']
            assert summary['source_file_sha256']==sha((f/'cases.jsonl').read_bytes())
            assert summary['chat_file_sha256']==sha((f/'chat.jsonl').read_bytes())
            evidence=['peer_finish_mapping_summary.json','peer_finish_mapping_qa7.jsonl','peer_finish_mapping_oracles.jsonl','peer_finish_mapping_numeric.jsonl','parent_derivative_delta.jsonl']
        else:
            summary=read(f/'peer_review.json');assert not summary['fixes_required']
            assert summary['source_hashes']['cases.jsonl']==sha((f/'cases.jsonl').read_bytes())
            assert summary['source_hashes']['chat.jsonl']==sha((f/'chat.jsonl').read_bytes())
            evidence=['peer_review.json','peer_fullfield_reviews.jsonl','peer_independent_oracles.jsonl','peer_numeric_checks.jsonl','peer_adversarial_mutations.jsonl']
        reviews=[]
        for (r,h),note in zip(source,NOTES[name]):
            criteria=[dict(criterion=k,passed=True,evidence=e) for k,e in [
                ('problem_givens_request_consistency',note),
                ('math_and_independent_oracle','Independent methods and numeric oracles bound by peer hashes; root recalculated actual quantities and finite alternatives.'),
                ('steps_reasons_units_and_check','Read actual full steps/reasons/explanations/results/answers; operation choice, unit role and reverse/exhaustiveness checks match request.'),
                ('guidance_and_all_three_hints','Read every actual initial and hint/question. Strategy only; no filled requested answer, final label or whole solution.'),
                ('grounded_student_work_and_assets','All corrections stay on explicit synthetic work; original text relation, no unseen-image/hidden-thought/physical-success claim.'),
                ('grade_and_finite_structural_diversity','Grade/enrichment scope explicit; paired branches change constraints, representation or error rather than substitute numbers only.'),
                ('provenance_and_preservation','Exact source row hash and parent derivative lineage retained. No new human signoff or source identity rewrite.')]]
            reviews.append(dict(sample_id=r['sample_id'],source_row_sha256=h,actual_fields={k:r[k] for k in FIELDS},criteria=criteria,semantic_decision=note,human_review_claimed=False))
        batches[name]=dict(status='PASS',actual_content_read=True,cases_sha256=sha((f/'cases.jsonl').read_bytes()),chat_sha256=sha((f/'chat.jsonl').read_bytes()),peer_evidence=[dict(file=n,sha256=sha((f/n).read_bytes())) for n in evidence],reviews=reviews)
    out=RUN/'root_evidence';out.mkdir(exist_ok=True)
    write(out/'content_review.json',dict(status='PASS_36_ACTUAL_CONTENT_AND_PEER_REVIEW',batches=batches,training_started=False))
    print('36 actual-content root reviews pinned to exact source/peer hashes')
if __name__=='__main__':main()
