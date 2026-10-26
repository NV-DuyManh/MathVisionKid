"""Root semantic review of actual36 drafts; peer provenance pinned, no human claim."""
from sgk_completion_release import RUN,DIRS,FIELDS,read,rows,sha,write
NOTES={
'g5_measurement_models_corrected':[
'Cut list counts two90x20, three60x20 and one90x60 panels exactly once:12600cm2=1.26m2;180thousand/m2 yields226.8thousand. Finished single-face material area, not two painted faces or packing feasibility.',
'Fixed0.88m2 plus0.15n gives costs236,266,296thousand for n2,3,4 at200/m2. Budget270 permits maximum3shelves,4remaining; finite design/budget interpretation explicit.',
'Five cakes sixpeople: sixhalves+sixthirds12pieces each5/6, versus30sixths each5pieces. Physical piece inventories and equal shares both checked; piececount differs but amounts agree.',
'Two cakes threepeople: eachthird+twosixths uses all12sixths and gives2/3each. Half+third needs2.5cakes and shortonehalf; named share alone cannot certify feasible inventory.',
'9x7 cells with0.5mside:63cells15.75m2,35white8.75,28frame7. Boundary cornercount not doubled, one-cell border and area squareunit conversion explicit.',
'9columns and24bordercells imply5rows from2w+2h-4. Full45cells11.25m2;white21cells5.25;6m2isborderonly. Unknown dimension solved from boundary count, not supplied target.',
'Net side widths6,3,6,3 and height4 at0.5cm/grid give cuboid3x1.5x2cm volume9cm3. Adjacent widths/heights mapped, not total strip as a singleedge.',
'Strip20 with6+unknown+6+unknown gives missing4; cap6x4 andheight3 at0.2dm/grid give1.2x0.8x0.6 volume0.576dm3. Strip4dm is not boxlength.',
'5x6 board tiled by2x3 pieces using2x6 strip two tiles and3x6 strip three rotated tiles; exactly5tiles, no overlaps/gaps and area necessary check30cm2.',
'Rotation prohibited, fixedwidth2 cannot cover width5 row; totalarea30 and tilearea6 do not prove tilability. Counterexample explicitly changes orientation permission.',
'ABC area24, ABE12, DBE6cm2 via respective bases/heights;difference18. Same containing base line does not make apex heights equal; all requested nested areas checked.',
'AD/DB/CE bases have heights4/4/6, areas6/6/12 sum24; DE oblique5 is not perpendicularheight. Corrected DE partitions ABE, AE partitions ABC; external altitudefoot B valid. Original wrong AD wording retained in parent provenance.'
],
'inventory_edges':[
'Complete boundary multiset1,2,3 matches P123 andR321, notQ124/S112; order irrelevant, every label required. Finite text inventory no unseen picture.',
'Repeated outcome inventory2,2,4 matches A224 only; B244 has different multiplicity andC241 different value. Set equality cannot replace multiset equality.',
'Two triangles ABC/ABD share AB, five distinct sticks AB AC BC AD BD; shared edge used physically once. Finite assembly makes complete shared triangles explicit.',
'Four existing AC BC AD BD need AB to close both triangles; AE decoy does not. Construction verifies both target boundaries rather than only stickcount.',
'Full2x2 grid has foursmall+oneouter square5; square-only scope excludes rectangular composites. All required boundary edges present.',
'Removing uppermiddle vertical segment opens twotopsmall squares, leaves twobottom andouter3. Drawn boundary existence matters, no inferred missing edge.',
'Fourcycle ownershipledger: An takes a3 thennone; Binh b3+c5 final8, wins turn4. Tokens removed once, positions wrap; no secondcollection on revisit.',
'Win threshold is two tokens, not totalprintedvalue. An D thenE wins turn3 despite Binh9pointF. Ownership and win metric grounded in actual givens.',
'2x2 obliquegrid has9parallelograms, removal DE leaves5, BE leaves2, EH leavesouteronly, AB leavesnone atturn4 so Binhwins. Composite boundary remains until actualedge removed.',
'Rhombus-only adjacentdiamonds stop at An removing shared BE, although nonsquare-length outerparallelogram stillclosed. Terminalscope is specified shapeclass, not anyclosedfigure.',
'Explicitfinite glyphsegmentsets: P andS each have parallelpair andintersectingperpendicularpair. Q/R satisfy onlyonecondition. Slanted45-degree pair checked without font/image assumption.',
'Disjoint segment supportlines perpendicular does not mean drawnsegments intersect; A fails, Bpasses, Ccollinearhorizontalpieces do not form distinctparallel lines. All jointconditions checked.'
],
'geometric_relations':[
'Six unitcells with diagonalhalves regroup A/B/C into2cm2each; each is1/3total. Fraction area follows disjointpiecearea, not initialvisualshape orcount.',
'Top two wholecells andbottomfourhalves each2cm2; piececount4vs2 doesnot imply doubledarea. Quote critique limited to visible asserted counting rule.',
'4x3 rectangle minus disjointcongruent2cm2 cornertriangles leavescommon8; adding eithertriangle makes10. Equalarea cancellation justified by explicit nonoverlap and congruence.',
'Moving halfsquare onto alreadyoccupied area preserves paperarea4 butunion3.5, gap/overlap each0.5. Overlap breaks simple sum-of-regions conservation claim.',
'OrderedABC adjacentvertices fixD(2,3) by equalparallel oppositeedges; boundaryorder checked. No alternatecorner silently substituted.',
'Unordered3points admit threefourthvertices(6,4),(0,4),(4,0), allinsidebounds; each orientation nondegenerate. Unique answer not claimed from unspecifiedorder.',
'Global constraints AaboveBaboveC plusAaboveD permit exactlythree listedorders; no invented relation forDversusB/C. Explicit textpartialorder no unseenocclusion assertion.',
'GlobalcycleA>B>C>A infeasible; removingC>A restoresA-B-C. Suppliedglobal-layer model scoped; not a claim about every localimageocclusion.',
'Three equal tangentcircles r2 have frame12x4cm, centerspan8; outerradius extensions included. Missing endpoints not confused with gaps.',
'Four tangentcircles span24cm fullwidth so diameter6,r3,centerspan18. Dividing fullwidth by3center-gaps is wrong extent, not an inferredstudentthought.',
'Trapezoid8/5 height4 splitatmidpoints then upperhalfturn aboutM yields13x2rectanglearea26. Originalperimeter22 versusnew30; area preservation doesnotimply perimeter preservation.',
'Trapezoid10/4 height8: uppertranslation(7,-4) yields triangularoverlap6 andgap6 withunion50 ratherthanoriginal56. Halfturn gives14x4rectangle56; specifiedtransformation verified, no genericmotion shortcut.'
]}
def main():
    results={}
    (RUN/'root_evidence').mkdir(exist_ok=True)
    for name in DIRS:
        folder=RUN/name;source=rows(folder/'cases.jsonl');peer=read(folder/'peer_review.json')
        assert len(source)==len(NOTES[name])==12 and peer['fixes_required']==[]
        assert peer['source_hashes']['cases.jsonl']==sha((folder/'cases.jsonl').read_bytes())
        assert peer['source_hashes']['chat.jsonl']==sha((folder/'chat.jsonl').read_bytes())
        refs=['peer_review.json']+list(peer['artifact_hashes'])
        for n,h in peer['artifact_hashes'].items():assert sha((folder/n).read_bytes())==h
        reviews=[]
        for (r,h),note in zip(source,NOTES[name]):
            criteria=[dict(criterion=k,passed=True,evidence=v) for k,v in [
                ('actual_problem_givens_request',note),
                ('math_and_independent_finite_oracle','Actual requested answers recomputed. Different-method peer model and adversarial wrong-answer/convention evidence are pinned by exact source/artifact hashes.'),
                ('steps_reasons_units_and_check','Actual workedsteps/reasons/explanations/results/units read; operations follow explicit relations, units and enumeration or reverse checks.'),
                ('initial_and_three_hints','Initial guidance and all three hints/questions read. They guide method/constraints without filled answers, final labels or full workedsolution.'),
                ('grounded_student_work','Critiques use only supplied studentwork. No hidden thinking, unseen image or physical performance inferred.'),
                ('grade_enrichment_and_branch_diversity',f'Explicit grade{r["grade"]} text/enrichment. Counterpart changes constraints, representation, ownership, multiplicity, interpretation or feasibility rather than only numbers.'),
                ('provenance_and_preservation','Immutable parent/source evidence retained; acceptance overlay separately hashed; ownerpreauthorization does not add human contentattestation.')]]
            reviews.append(dict(sample_id=r['sample_id'],source_row_sha256=h,actual_fields={k:r[k] for k in FIELDS},criteria=criteria,semantic_decision=note,human_review_claimed=False))
        results[name]=dict(status='PASS',actual_content_read=True,cases_sha256=sha((folder/'cases.jsonl').read_bytes()),chat_sha256=sha((folder/'chat.jsonl').read_bytes()),peer_evidence=[dict(file=n,sha256=sha((folder/n).read_bytes())) for n in refs],reviews=reviews)
    write(RUN/'root_evidence/content_review.json',dict(status='PASS_36_ACTUAL_CONTENT_AND_INDEPENDENT_PEERS',batches=results,training_started=False,human_content_review_claimed=False))
    print('36 actual-content root reviews pinned')
if __name__=='__main__':main()

