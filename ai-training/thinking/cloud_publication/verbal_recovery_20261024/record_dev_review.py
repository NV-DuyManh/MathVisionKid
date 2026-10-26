from pathlib import Path
import json,hashlib
p=Path(__file__).parent/'review_step_000050'
# Root decisions entered only after reading actual full paired outputs and fixture/rubric.
# Tuple: base pass, candidate pass, base leak, candidate leak, new critical error, base reason, candidate reason.
D={
0:(False,True,False,False,False,'Writes47and40 correctly, but explicitly places digit4 as second from left in47, contradicting actual tens place. Full explanation contains a positional error.','Writes47and40withcorrect4*10+7 andtens/unit explanation, no false position claim.'),
1:(False,False,False,False,False,'Correct final ordering and later unit comparison, but false4<5<5 chain remains in explanation.','Correct final order but false5<5 is used to justify50<54 before a later correct units comparison. Both full-task outputs fail for contradictory reasoning.'),
2:(False,True,False,False,False,'Both required subtraction equations and checks are correct, but twice calls3or6 the result of original6+3 addition; original sum is9. Full explanation is inconsistent.','Correct9−6=3and9−3=6 and inverse3+6=9check; imprecise use of so-hang term does not change actual arithmetic relation.'),
3:(False,False,True,False,False,'Explicit8<9reveals withheld comparison.','Only repeats instruction to give a hint and withhold answer, without a task-specific next step. No answer leak but no useful hint.'),
4:(False,False,False,False,False,'Correct16<61 appears, but falsely claims1in61is tens and6in16is tens elsewhere, contradicting actual digit positions.','Correct inequality appears, but repeatedly misplaces1in61as tens and claims digit6is not larger than1. Full mathematical explanation is inconsistent.'),
5:(False,False,False,False,False,'Identifies candidates1..5and lack of uniqueness, but proposes only parity to determine more exactly; explicit own examples leave2or3 possibilities. Does not supply/request a condition sufficient for unique identification.','Recognizes1..5and nonuniqueness, but proposed extra condition is circular: number must be determinable. No concrete sufficient request such as revealing card or distinguishing property.'),
6:(True,True,False,False,False,'Correct inclusive64−46+1=19cards and covers both endpoints, consistent verification.','Correct inclusive calculation19cards and lists all19labels without omission.'),
7:(True,True,False,False,False,'Correct2m=200cm and200−185=15cm with inverse-sized difference and consistent units.','Correct common-unit conversion200cm, difference15cm and check; full answer supplied.'),
8:(True,True,False,False,False,'Correct4shape period,14=3*4+2and square at position2, consistent complete explanation. Mod notation is more advanced but translated into remainder meaning.','Correct4shape cycle and remainder2⇒square, no zero-based counting or false shape claim.'),
9:(False,False,True,True,False,'Explicitly gives26legs despite hint-only request.','Explicit20+6=26and repeated final26leak, so hint-only failure.'),
10:(True,True,False,False,False,'Correct repeated3+3=6 and multiplication, flags the provided addition as inappropriate for this two-group context.','Explicitly distinguishes true arithmetic3+2=5 from wrong contextual operation and correctly supplies6candies.'),
11:(False,False,False,False,False,'Finds contradiction but unconditionally treats17Wednesday as verified, gives18Thursday and never asks to check original calendar.','Finds contradiction but unconditionally selects17Wednesday and18Thursday without the required source verification.'),
12:(False,False,False,False,False,'Correct67with9*7+4and inverse check, but omits the explicitly required remainder-less-than-divisor check.','Correct67with inverse check but never verifies4<9 as required by the rubric.'),
13:(False,True,False,False,False,'Correct2390g/2kg390g final, but asserts2390−850=2390 in its check; substantive false equality.','Correct3240−850=2390g=2kg390g with consistent unit conversion and no false check.'),
14:(True,True,False,False,False,'Correct three equal sides total96cm, each32cm and sum check96.','Correct equal-three-side division32cm and multiplication check96.'),
15:(False,False,False,True,False,'Useful parentheses-then-subtraction cue, but then says either left-to-right or right-to-left is allowed without conditions, contradicting required operation order.','Leaks42 at intermediate and final positions and supplies the whole solution despite hint-only request.'),
16:(False,False,False,False,False,'Corrects quotient0, but says supplied check is unrelated and concludes student result was correct, contradicting actual claimed quotient7.','Correct quotient0 and inverse relation, but explicitly endorses student check as correct for the supplied wrong quotient; does not identify wrong factor substitution.'),
17:(False,False,False,False,False,'Invents20cm and claims it is exact without any measurement source.','Refuses a numeric guess, but accepts an unspecified image alone as sufficient; never requests measurable scale or a recorded measurement with unit as rubric requires.'),
18:(True,True,False,False,False,'Correct common-denominator comparison7/12<9/12<10/12 and original labels in ascending ray order.','Correct conversions and left-to-right order7/12,3/4,5/6, with consistent inequality.'),
19:(True,True,False,False,False,'Correct measured-quantity division10cups and10/12=5/6litre check.','Correct10cups by reciprocal multiplication and verifies original water volume.'),
20:(True,False,False,False,False,'Correct112total,81known,31missing and explicitly checks112/4=28 average.','Correct31points, but omits the explicitly required check of all-four-game average, so full requested task is incomplete.'),
21:(False,False,True,True,False,'Explicitly reveals4/7 despite hint-only request.','Explicitly reveals4/7 then repeats until1024token cap, nonEOS and truncated; hint leak plus completion failure.'),
22:(False,False,False,False,False,'Correct inequality but calls15a common divisor and supplies a false same-numerator heading; also truncates beforeEOS.','Correct common-denominator inequality, but falsely attributes numerator-versus-denominator comparison to the supplied student work, which actually compares two numerators; feedback is not grounded in the stated error.'),
23:(False,True,False,False,False,'Correct contradiction conclusion, but repeatedly asserts17/12*S>1 for arbitrary areaS and falsely restricts total area to1unit.','Explicitly normalizes whole to1 and uses17/12>1 plus nonoverlap condition; correctly concludes impossible without changing supplied fractions.'),
24:(True,False,False,False,True,'Correct different percentage bases,1.25*.8=1and100percent original.','Incorrectly subtracts.2*x rather than.2*1.25*x and claims1.25*.8=1.05, giving105percent instead of100percent; new critical arithmetic error.'),
25:(True,True,False,False,False,'Correct24litres/minute and24*1.25=30litres, with consistent decimal calculations and units.','Correct proportional-rate calculation24litres/minute then30litres, no changed time unit.'),
26:(True,True,False,False,False,'Correct conversion to24,15,8cm and cube edge1cm, then24*15*8=2880. Generic dimension/edge shorthand is imprecise but actual three-axis calculation is supplied and consistent.','Explicitly divides all three lengths by.1dm then multiplies24*15*8=2880, consistent checks.'),
27:(False,False,True,False,False,'Explicitly reveals forbidden.9km final distance.','Useful time conversion and individual-distance prompts without final leak, but stops before relating these distances by subtraction, omitting the required same-direction difference relation.'),
28:(True,True,False,False,False,'Correct square-unit explanation100*100=10000 and.6m2=6000cm2; addresses supplied length-factor error.','Correct10000square-centimetres-per-square-metre explanation and6000cm2, with incorrect60cm2 clearly marked as the supplied error rather than endorsed.'),
29:(False,True,False,False,False,'Eventually gives correct200000..225000range and lack of uniqueness, but earlier reversed inequality225000<=x<=200000 falsely declares no feasible value. Contradictory mathematical explanation.','Correct conditional.9x/.8x examples, recognizes unknown exact discount and requests exact percentage without choosing a unique original price.'),
}
def main():
 dev=[json.loads(x) for x in (p/'new_validation_candidates.jsonl').read_text(encoding='utf8').splitlines()]
 base=[json.loads(x) for x in (p/'training__eval_step_000000__base_generations.jsonl').read_text(encoding='utf8').splitlines()]
 cand=[json.loads(x) for x in (p/'training__eval_step_000050__adapter_generations.jsonl').read_text(encoding='utf8').splitlines()]
 for label,indices in [('g1_g2',range(12)),('g3_g4',range(12,24)),('g5',range(24,30))]:
  if not all(i in D and i<len(cand) for i in indices):continue
  records=[]
  for i in indices:
   bp,ap,bl,al,critical,br,ar=D[i];b,a=base[i],cand[i];f=dev[i];assert f['id']==b['fixture_id']==a['fixture_id']
   for side,ok in [(b,bp),(a,ap)]:
    if ok:assert side['ended_eos'] and not side['possibly_truncated'] and not side['timed_out']
   records.append({'fixture_id':f['id'],'grade':f['grade'],'mode':f['mode'],'base_pass':bp,'adapter_pass':ap,'base_hint_leak':bl,'adapter_hint_leak':al,'critical_new_error':critical,'base_reason':br,'adapter_reason':ar})
  paired=p/f'paired_{label}.json';assert paired.exists()
  report={'all_actual_fields_read':True,'human_review_claimed':False,'root_review':True,'input_pair_sha256':hashlib.sha256(paired.read_bytes()).hexdigest(),'decisions':records}
  target=p/f'semantic_{label}.json';raw=(json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode()
  if target.exists():assert target.read_bytes()==raw,'Do not silently change completed judgments'
  else:target.write_bytes(raw)
  print(json.dumps({'label':label,'base':sum(x['base_pass'] for x in records),'candidate':sum(x['adapter_pass'] for x in records)}))
if __name__=='__main__':main()
