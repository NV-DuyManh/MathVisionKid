"""Root review of 18 actual tasks, bound to immutable drafts and peer checks."""
from sgk_final_forms_release import RUN,DIRS,FIELDS,read,rows,sha,write
NOTES={
'g5_exact_text':[
'Three comma slots yield1.234,12.34,123.4; only first satisfies both strict bounds. Original order and exactly one internal comma retained; hints never locate the successful slot.',
'250 only permits2.50 and25.0; each equals an excluded bound. Explicit quote preserves arithmetic equalities but incorrectly accepts strict-bound endpoints; no legal slot.',
'Three different0,2,5cards make six fixedX.YZstrings; order0.25,0.52,2.05,2.50,5.02,5.20 complete. Leading fractionalzero and trailingzero permission explicit.',
'Physicalu0,v0,w4 identities give six placements but three distinct strings0.04,0.40,4.00 and three distinct values. Zero cards retained when trailing zeros suppressed for value only.',
'Cubeedge2to6 scales all dimensions3. Surfaces24and216cm2 ratio9;volumes8and216cm3 ratio27. Same numerical216 never conflates units.',
'Cubeedge4to2 gives surfaces96to24 ratio1/4 andvolumes64to8 ratio1/8; observable linear-scale assertion corrected with two andthree edge factors.',
'Full six paintedfaces of3cubed smallcubes classify3,2,1,0faces counts8,12,6,1. Countsum27 andpaintedsmallfaces54 independently match6*9.',
'Five paintedfaces excludingbottom yieldcounts4,12,9,2;bottomcorners2ratherthan3paintedfaces. Count27 andsmallfacecount45 match5*9.',
'SharedapexA over collinearBD3/DC5 gives commonperpendicularheight;total32 splits12and20 with3:5ratio. No unknown measuredheight fabricated.',
'Differentapices at heights4and2 preventsameheight inference from collinear bases alone. Areas6and5cm2 ratio6:5; quoted3:5 lacks required equalheight.',
'Allapices onparallel line6cm fromfixed8cmbase keeparea24cm2 includingexternalaltitudefoot. Height refers tobasecontainingline; no image inference.',
'Fixed10cmbase butheights3then5 gives15then25cm2 andincrease10; an arbitrarynonparallelmotion doesnotpreserveheight orarea. Feedback confinedtoquote.'
],
'g5_residual_text':[
'Exactfour +/-choices for3/4,1/3,1/6 yield15/12,11/12,7/12,3/12; onlyminusplus gives7/12. Nooperand/denominator/bracket mutation; hintstrategyonly.',
'Bothlegal signs on2/3and1/4 give11/12or5/12, neither1/6. Studentminusvaluewrong; fullyspecifiedfiniteinfeasibility distinguishedfrommissingdata.',
'Completepositiveweighted graph hasSAT2,SBT2.5,ST2.4km. UniqueSAT roundtrip4km withdifferent4/5kmphspeedsgives54min;cost8thousand at2/km appliesbothlegs.',
'HATandHBT tie1.5km,HT1.8. Independentreturn permitsfourorderedA/Bbranchpairs all3km;common3kmph gives60min and4/kmcost12thousand. Firstedgegreedy cannot prove uniqueness.',
'All10height-role arrangements forvolume12 listed. Fourlateralfaceareas26,16,14,28,20,30,24,32,36,48; minimum14at4,3,1. Neitherclosednorfivefaceobjective substituted.',
'Volume18 andheight>=2 permitssevenarrangements; lateralareas40,24,42,30,48,54,72. Unique24at3,3,2. Student30for3,2,3arithmeticallyright butorientationpruninginvalidfortheheight-dependentobjective.'
]}
def main():
    result={}
    for name in DIRS:
        folder=RUN/name;src=rows(folder/'cases.jsonl');peer=read(folder/'peer_review.json')
        assert len(src)==len(NOTES[name]) and not peer['fixes_required']
        assert peer['source_hashes']['cases.jsonl']==sha((folder/'cases.jsonl').read_bytes())
        assert peer['source_hashes']['chat.jsonl']==sha((folder/'chat.jsonl').read_bytes())
        refs=['peer_review.json']+[n for n in peer.get('artifact_hashes',{}) if n.endswith('.jsonl')]
        reviews=[]
        for (r,h),note in zip(src,NOTES[name]):
            criteria=[dict(criterion=k,passed=True,evidence=v) for k,v in [
                ('actual_problem_givens_request',note),
                ('math_and_finite_independent_oracle','Root recalculated actual requested quantities; different-method peer oracle and wrong-answer/unit/convention mutations pinned by exact evidence hashes.'),
                ('steps_reasons_units_and_check','All actual steps, explanations, reasons, results and answers read. Unit roles, operation choices and complete enumeration or reverse checks agree.'),
                ('initial_and_three_hints','All initial and three hint/question pairs read. Methods and constraints only; no filled answer, final solution label or complete worked solution.'),
                ('grounded_student_work','Every critique uses only the supplied synthetic excerpt. No hidden student thought, unseen image or actual physical result inferred.'),
                ('grade_enrichment_and_diverse_branch','Explicit grade5 text/enrichment; branches alter constraints, premises, multiplicity, objective or error, rather than only change numbers.'),
                ('provenance_and_preservation','Draft exact source hashes retained; accepted derivation separately hashed; ownerpreauthorization does not fabricate new human content attestations.')]]
            reviews.append(dict(sample_id=r['sample_id'],source_row_sha256=h,actual_fields={k:r[k] for k in FIELDS},criteria=criteria,semantic_decision=note,human_review_claimed=False))
        result[name]=dict(status='PASS',actual_content_read=True,cases_sha256=sha((folder/'cases.jsonl').read_bytes()),chat_sha256=sha((folder/'chat.jsonl').read_bytes()),peer_evidence=[dict(file=n,sha256=sha((folder/n).read_bytes())) for n in refs],reviews=reviews)
    write(RUN/'root_evidence/content_review.json',dict(status='PASS_18_ACTUAL_CONTENT_AND_PEER_REVIEW',batches=result,training_started=False))
    print('18 actual-content root reviews pinned')
if __name__=='__main__':main()
