"""Record root's actual six-case content reading and independent bounded checks."""
from pathlib import Path
from collections import Counter
from fractions import Fraction
from decimal import Decimal,localcontext
import json,hashlib
from sgk_gap_release import evaluate

HERE=Path(__file__).resolve().parent
RUN=HERE/'cloud_publication/g2_finite_forms_20261021'
SOURCE=RUN/'numerals_cohort1/polished'
FIELDS=['problem','givens','requested_quantity','student_work','worked_steps','expected_answer','initial_guidance','hints']
DECISIONS=[
 'All two-digit numbers from0,2,7 are20,27,70,72: leading zero excluded, no parity filter, min20/max72/difference52. Both branches complete; hints only explain choice/order/check.',
 'Optional0 is not compulsory. Three nonzero tens each allow three remaining cards:9values10,14,18,40,41,48,80,81,84; difference74. Feedback addresses only supplied false mandatory-zero statement.',
 'Two distinct physical zero cards yield C-A and C-B but only value50. Min=max50 and difference0 are valid; hints do not give the single final numeral or counts.',
 'Two physical2cards must both be used:202,220 and four labeled arrangements. Difference18. Feedback points to explicit omission of B and two-digit20, not hidden thinking.',
 'All-card0,3,6 construction yields306,360,603,630 before filtering; strict greater-than306 leaves360,603,630 with difference270. Equality rejected without changing given threshold.',
 'All-card1,2,4 yields124,142,214,241,412,421. Maximum421 is below500, so no accepted numeral/min/max. Count0 is legitimate but cannot substitute for a nonexistent extremum. Feedback only evaluates supplied421 claim.'
]
CRITERIA=[
 ('statement_givens_request','Explicit finite card stock, reuse between trials and required positions/thresholds make each question well-posed.'),
 ('math_and_independent_oracle','Root enumerated decimal integers by digit-stock capacity independently of physical-card permutations; all values/counts and7Fraction/Decimal expressions agree.'),
 ('grade_and_representation','Grade2 tens/hundreds/comparison/subtraction, explicitly enrichment; polished learner prose avoids extrema/set jargon. No publisher-image or physical-success claim.'),
 ('steps_reasons_units_checks','Actual steps explain position choice, complete disjoint enumeration, comparison, card/count units, inverse arithmetic or exhaustion check.'),
 ('initial_and_three_hints_no_answer','Read initial guidance and all18hints: methods and questions only; no completed list, final numeral, count or final no-solution label supplied as a hint.'),
 ('observable_student_feedback','Only3explicit supplied synthetic student statements are corrected; other student_work is null. No inferred private thinking or unseen image.'),
 ('source_schema_provenance_hashes','Neutral schema, AI origin and false human flags retained; original drafts/50wording deltas are preserved. Source review hashes are separated from future export hashes.')
]
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    lines=(SOURCE/'cases.jsonl').read_bytes().splitlines()
    rows=[json.loads(b) for b in lines]
    assert len(rows)==6 and len(DECISIONS)==6
    reviews=[];oracles=[];numeric=[]
    for r,line,decision in zip(rows,lines,DECISIONS):
        m=r['independent_model'];stock=Counter(m['cards'].values());length=m['length']
        # A different search space: decimal values, rather than labeled card placements.
        values=[]
        for n in range(10**(length-1),10**length):
            digits=Counter(map(int,str(n)))
            if not all(c<=stock[d] for d,c in digits.items()):continue
            if m['bound'] is not None and n<=m['bound']:continue
            values.append(n)
        assert values==m['expected_values']
        answers={a['quantity']:a['result'] for a in r['expected_answer']}
        value_answer=next(a['result'] for a in r['expected_answer'] if a['quantity'] in ('Mọi số','Mọi giá trị','Mọi số được nhận'))
        assert value_answer==(';'.join(map(str,values)) if values else 'không có')
        if values:
            assert answers['Số nhỏ nhất']==str(min(values)) and answers['Số lớn nhất']==str(max(values))
            assert answers['Hiệu']==str(max(values)-min(values))
        else:assert answers['Số nhỏ nhất sau lọc']==answers['Số lớn nhất sau lọc']=='không tồn tại'
        assert len(r['hints'])==3 and [h['level'] for h in r['hints']]==[1,2,3]
        assert not any(r[k] for k in ['human_verified','teacher_certified','owner_human_reviewed'])
        for step in r['worked_steps']:
            assert step['reason'] and step['explanation'] and 'unit' in step
            if step.get('expression'):
                f=evaluate(step['expression'],'fraction');assert f==Fraction(step['result'])
                with localcontext() as ctx:
                    ctx.prec=90;d=evaluate(step['expression'],'decimal')
                    assert d==Decimal(f.numerator)/Decimal(f.denominator)
                numeric.append(dict(sample_id=r['sample_id'],step_id=step['step_id'],expression=step['expression'],fraction=str(f),decimal=str(d)))
        reviews.append(dict(sample_id=r['sample_id'],source_row_sha256=sha(line),actual_fields={k:r[k] for k in FIELDS},semantic_decision=decision,criteria=[dict(name=k,passed=True,evidence=v) for k,v in CRITERIA]))
        oracles.append(dict(sample_id=r['sample_id'],method='DECIMAL_INTEGER_RANGE_AND_DIGIT_CAPACITY_ROOT',values=values,minimum=min(values) if values else None,maximum=max(values) if values else None))
    assert len(numeric)==7
    result=dict(schema='MathVisionKid.root_full_content_QA.v1',status='PASS',actual_content_read=True,cases_sha256=sha((SOURCE/'cases.jsonl').read_bytes()),chat_sha256=sha((SOURCE/'chat.jsonl').read_bytes()),reviews=reviews,independent_root_oracles=oracles,fraction_decimal_steps=numeric,peer_evidence=[dict(file='numerals_cohort1/peer_review.json',sha256=sha((RUN/'numerals_cohort1/peer_review.json').read_bytes())),dict(file='numerals_cohort1/polished/peer_qa7.jsonl',sha256=sha((SOURCE/'peer_qa7.jsonl').read_bytes()))],scope='ONLY_SIX_FULLY_READ_POLISHED_DRAFTS; NOT_FULL_ARCHIVE_OR_HUMAN_ATTESTATION',new_human_review_claimed=False,training_started=False)
    (RUN/'root_content_review.json').write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(status='PASS',cases=6,hints_read=18,numeric=7,training_started=False)))
if __name__=='__main__':main()
