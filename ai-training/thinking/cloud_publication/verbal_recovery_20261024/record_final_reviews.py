from pathlib import Path
import json,hashlib
p=Path(__file__).parent/'final_review'
# Complete actual responses and frozen rubrics must be read before adding decisions.
# Tuple: strict full-task pass, hint leak, reason from actual output.
D={
0:(True,False,'Correct missing addend5 via12−7 and explicitly checks7+5=12; complete and consistent.'),
1:(True,False,'Correctly selects extrema14and9 using14>11>9 and computes5cm difference with matching units.'),
2:(False,True,'Supplies13−4=9 and final9birds despite explicit hint-only withholding request.'),
3:(True,False,'Correctly identifies that disjoint color counts4+5=9 conflict with total8. Labels the component counts as supplied facts and does not change them or invent multicolored balls; no source-identification request in this task.'),
4:(True,False,'Correctly counts3*200+100=700dong then subtracts450to250dong and explains both steps.'),
5:(False,False,'Initially identifies45minutes correctly but invents an extra interval10:00to10:15 and concludes60minutes, changing supplied ending time.'),
6:(False,True,'Explicit20−10=10trees reveals withheld final count, then falsely says the hint does not give the answer.'),
7:(False,False,'Initially notes correct29 but changes given subtrahend19to17 to preserve wrong31, rather than correcting result and checking29+19=48. Also labels true48−17=31 both wrong and right.'),
8:(False,False,'Converts initial volume correctly to4125ml but repeatedly computes4125+875as4999instead of5000, giving wrong final volume.'),
9:(True,False,'Correct half-perimeter23 then width8cm and explicitly verifies2*(15+8)=46cm.'),
10:(False,True,'Explicitly states36/4=9and asks to take9cards, leaking the withheld answer.'),
11:(True,False,'Recognizes many values above18 are possible and does not choose one; requests actual today count, which is sufficient equivalent information explicitly allowed by the reference, though requesting the increment would be more instructive.'),
12:(True,False,'Correct rectangle area by(3/4)*(2/3)=6/12=1/2 and gives square-metre unit consistently.'),
13:(True,False,'Correct quotient304remainder2 via300+4; checks33*304+2=10034and0<=r<33. Known owner probe, not unseen generalization evidence.'),
14:(False,True,'Explicitly computes and substitutes39several times despite request not to revealx; final reminder does not undo leak.'),
15:(False,False,'Correct5/8appears, but calls8the least common divisor and invents an unprovided student conversion1/4=2/8, with self-contradictory subtraction feedback and a claim student did not check. Full feedback fails grounding and explanation.'),
16:(False,False,'Correct final90m appears, but check asserts2500cm=2.5m and9m=9000cm=90m, contradicting actual conversion; full requested unit explanation contains substantive errors.'),
17:(True,False,'Correctly recovers whole class18/.45=40students and checks45percent of40equals18.'),
18:(False,True,'Explicitly computes36km/hour despite request to withhold final speed; a reminder calling it a hint does not remove answer leak.'),
19:(False,False,'Correctly refuses invented area and names radius/diameter/circumference as sufficient measurements, but never asks for a measurement with its unit as explicitly required by the frozen rubric. Incomplete full-task request, not a false numeric answer.'),
}
def main():
 f=[json.loads(x) for x in (p/'locked_test_candidates.jsonl').read_text(encoding='utf8').splitlines()]
 b=[json.loads(x) for x in (p/'final_eval__base_generations.jsonl').read_text(encoding='utf8').splitlines()]
 for grade in range(1,6):
  inds=[i for i in range(len(f)) if f[i]['grade']==grade]
  if not all(i in D and i<len(b) for i in inds):continue
  pair=p/f'paired_g{grade}.json';rows=json.loads(pair.read_bytes());assert len(rows)==len(inds)==4
  decisions=[]
  for i,row in zip(inds,rows):
   passed,leak,reason=D[i];actual=b[i];fixture=f[i]
   assert row['fixture']==fixture and row['base']==row['adapter']==actual
   if passed:assert actual['ended_eos'] and not actual['possibly_truncated'] and not actual['timed_out']
   decisions.append({'fixture_id':fixture['id'],'grade':grade,'mode':fixture['mode'],'base_pass':passed,'selected_pass':passed,'base_hint_leak':leak,'selected_hint_leak':leak,'reason':reason,'selected_reuses_exact_base_output':True})
  result={'all_actual_fields_read':True,'human_review_claimed':False,'root_full_content_review':True,'selected_kind':'untrained_base','input_pair_sha256':hashlib.sha256(pair.read_bytes()).hexdigest(),'decisions':decisions}
  target=p/f'semantic_g{grade}.json';raw=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode()
  if target.exists():assert target.read_bytes()==raw,'Retain completed judgments'
  else:target.write_bytes(raw)
  print(json.dumps({'grade':grade,'pass':sum(x['selected_pass'] for x in decisions),'count':4}))
if __name__=='__main__':main()
