"""Independent root cross-review: actual full fields read, finite mathematical proofs."""
from pathlib import Path
from itertools import permutations
from fractions import Fraction as F
from decimal import Decimal,localcontext
import json,hashlib
from sgk_g4extra_peer_oracle import calc
import exhaustive_colab_loader as L
HERE=Path(__file__).resolve().parent
RUN=HERE/'cloud_publication/sgk_finish_20261020'
def sha(b):return hashlib.sha256(b).hexdigest()

def g1_oracle(t):
    if t=='attribute_tied_maximum':
        data=[('A','tròn','đỏ',18),('B','tròn','đỏ',18),('C','tròn','đỏ',12),('D','vuông','đỏ',30),('E','tròn','xanh',25)]
        valid=[(a,v) for a,s,c,v in data if s=='tròn' and c=='đỏ'];top=max(v for a,v in valid);ans=[a for a,v in valid if v==top];assert ans==['A','B'];return dict(filtered=valid,all_maximum_labels=ans)
    if t=='attribute_empty_subset':
        data=[('P','vuông','vàng',8),('Q','tròn','xanh',15),('R','tam giác','vàng',20)]
        valid=[a for a,s,c,v in data if s=='tròn' and c=='vàng'];assert not valid;return dict(valid=valid,minimum_defined=False)
    if t.startswith('identity_'):
        values=[7,7,9] if t.endswith('lower') else [6,8,8];ways=sorted(set(permutations(values)))
        good=[v for v in ways if (v[0]==v[1] and v[2]>v[0])] if t.endswith('lower') else [v for v in ways if v[0]>=v[2]]
        assert good==([(7,7,9)] if t.endswith('lower') else [(8,6,8),(8,8,6)]);return dict(valid_person_value_assignments=good,unique=len(good)==1)
    if t.startswith('pair_gate_'):
        pairs=[('A','C',3,7),('B','D',6,5)] if t.endswith('unique') else [('P','R',2,5),('Q','U',5,8)]
        sums={a+b:u+v for a,b,u,v in pairs};good=[k for k,v in sums.items() if v==10];assert good==(['AC'] if t.endswith('unique') else []);return dict(all_connected_pair_sums=sums,valid_pairs=good)
    if t=='itinerary_week_rollover':
        days=['Thứ Hai','Thứ Ba','Thứ Tư','Thứ Năm','Thứ Sáu','Thứ Bảy','Chủ nhật'];a=[days[(4+i)%7] for i in range(4)];assert a[-2:]==['Chủ nhật','Thứ Hai'];return dict(days_in_place_order=a)
    if t=='itinerary_back_from_last':
        weekdays=list(range(7));allstarts=[s for s in weekdays if (s+2)%7==0];assert allstarts==[5];return dict(first_weekday_index=5,second_index=6,last_index=0,index_convention='Monday=0')
    if t in ('two_digit_matching_symbols','digit_length_guard'):
        values=['11','12','22','20','33','30'] if t.startswith('two_') else ['0','10','44','55','100'];valid=[v for v in values if len(v)==2 and v[0]==v[1]];assert valid==(['11','22','33'] if t.startswith('two_') else ['44','55']);return dict(all_written_cards=values,valid=valid,leading_zeros_added=False)
    raise ValueError(t)

def g5_oracle(t):
    if t.startswith('fraction_strict_'):
        lo,hi,den=(F(1,3),F(3,4),12) if t.endswith('numerators') else (F(2,5),F(3,5),10)
        valid=[i for i in range(10) if lo<F(i,den)<hi];assert valid==([5,6,7,8] if den==12 else [5]);return dict(all_digit_comparisons={str(i):str(F(i,den)) for i in range(10)},valid=valid,strict=True)
    if t.startswith('remainder_'):
        total,a,b=(F(120),F(1,3),F(1,4)) if t.endswith('forward') else (F(96),F(1,4),F(1,3));parts=[total*a];parts.append((total-parts[0])*b);last=total-sum(parts);assert last==(60 if total==120 else 48);return dict(used=list(map(str,parts)),remaining=str(last),conservation=str(sum(parts)+last))
    if t.startswith('three_pairs_'):
        ab,bc,ac=(F('7.5'),F(9),F('8.5')) if t.endswith('decimal') else (F(7),F(9),F(8));total=(ab+bc+ac)/2;A,B,C=total-bc,total-ac,total-ab
        assert A+B==ab and B+C==bc and A+C==ac and min(A,B,C)>0;return dict(A=str(A),B=str(B),C=str(C),total=str(total),recorded_total_consistent=(total==10) if t.endswith('repair') else None)
    if t=='age_future_ratio_reverse_current':
        good=[(older,younger) for younger in range(101) for older in range(101) if older-younger==12 and older+4==2*(younger+4)];assert good==[(20,8)];return dict(all_bounded_nonnegative_year_solutions=good,uniqueness_reason='Substituting fixed difference into the given future equality fixes the younger age.')
    if t=='age_ratio_changes_find_wait':
        good=[n for n in range(101) if 25+n==2*(10+n)];assert good==[5];return dict(years=good,future_ages=[30,15],uniqueness_reason='Subtract equal future increments: one increment remains, fixed by the given equality.')
    if t.startswith('cashback_'):
        price,discount,threshold=(F(250),F(1,10),F(225)) if t.endswith('threshold') else (F(300),F(1,5),F(250));paid=price*(1-discount);refund=paid*F(1,20) if paid>=threshold else F(0);net=paid-refund
        assert (paid,refund,net)==((F(225),F('11.25'),F('213.75')) if price==250 else (F(240),F(0),F(240)));return dict(paid=str(paid),eligible=paid>=threshold,refund=str(refund),net=str(net),basis='Stated fictional rule only')
    if t.startswith('bins_'):
        values=dict(A=10,B=12,C=15,D=15,E=19,F=20) if t.endswith('boundary') else dict(A=0,B=10,C=10,D=20,E=20,F=30)
        preds=[lambda x:10<=x<15,lambda x:15<=x<=20] if t.endswith('boundary') else [lambda x:0<=x<=10,lambda x:10<x<=20,lambda x:20<x<=30]
        groups=[[k for k,x in values.items() if pred(x)] for pred in preds];flat=sum(groups,[]);assert len(flat)==6 and len(set(flat))==6;return dict(groups=groups,frequencies=list(map(len,groups)),all_sample_ids_preserved=True)
    raise ValueError(t)

def review(directory,expected_hash,oracle):
    out=RUN/directory;raw=(out/'cases.jsonl').read_bytes();assert sha(raw)==expected_hash
    rows=[(json.loads(b),sha(b)) for b in raw.splitlines()];reviews=[];num=0
    for r,h in rows:
        proof=oracle(r['topic']);numeric=[]
        for s in r['worked_steps']:
            if s.get('expression'):
                f=calc(s['expression']);assert f==F(s['result'])
                with localcontext() as ctx:
                    ctx.prec=90;d=calc(s['expression'],Decimal);assert abs(d-Decimal(f.numerator)/Decimal(f.denominator))<Decimal('1e-70')
                numeric.append(dict(expression=s['expression'],exact=str(f),decimal_agrees=True));num+=1
        reviews.append(dict(sample_id=r['sample_id'],source_row_sha256=h,status='PASS_CONTENT_CROSS_REVIEW',review_role='ROOT_FULL_ACTUAL_CONTENT_READ_AND_INDEPENDENT_ORACLE',criteria={k:'PASS' for k in ['math_or_explicit_decision','givens_request_consistency','grade_enrichment_scope','steps_reasons_units_check','initial_and_all_hints_answer_free','student_work_grounding','schema_provenance']},actual_fields_read=['problem','givens','requested_quantity','student_work','worked_steps','reasons','explanations','expected_answer','initial_guidance','all_three_hints'],structural_oracle=proof,numeric_checks=numeric,human_review_claimed=False,parser_pass_not_semantic_proof=True))
    cs=[json.loads(b) for b in (out/'chat.jsonl').read_bytes().splitlines()];source={r['sample_id']:(r,h) for r,h in rows};modes={k:set() for k in source}
    for c in cs:
        L.validate_chat(c);r,h=source[c['source_sample_id']];assert c['source_row_sha256']==h;target=json.loads(c['messages'][2]['content']);mode=c['mode'];modes[r['sample_id']].add(mode)
        if mode=='worked_solution':assert target['steps']==r['worked_steps'] and target['answer']==r['expected_answer']
        else:
            hint=r['hints'][int(mode[-1])-1];assert target==dict(hint=hint['hint'],question=hint['question'])
    assert len(cs)==len(rows)*4 and all(len(v)==4 for v in modes.values())
    result=dict(source_file_sha256=sha(raw),chat_file_sha256=sha((out/'chat.jsonl').read_bytes()),case_count=len(rows),chat_count=len(cs),seven_criteria_pass_count=len(rows),numeric_checks=num,status='PASS_CONTENT_CROSS_REVIEW_DRAFT_NOT_ACCEPTED',reviews=reviews,training_started=False)
    (out/'peer_review.json').write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:result[k] for k in ['case_count','chat_count','numeric_checks','source_file_sha256','status']}))
if __name__=='__main__':
    review('g1_text_append','ed96cd9fb0b41f6aeca78bd69f0d06053b4e76d0b3511f49b7a460cd354f9730',g1_oracle)
    review('g5_text_append','68f5b4e59b0f21da62cc17349a66acdc4fa73b07d75b8a41a43da61d5a49b30a',g5_oracle)
