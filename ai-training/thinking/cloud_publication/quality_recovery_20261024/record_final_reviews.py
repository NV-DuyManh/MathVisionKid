from pathlib import Path
import json,hashlib
p=Path(__file__).parent/'final_review'
reviews={
 1:[
  (True,False,'Correctly applies20−10 then+3 to13 and explains both directions. Repeated two-step explanation is unnecessary but mathematically consistent.'),
  (False,False,'Numerical5cm and7−2 are correct, but requested why-not7 explanation falsely says the right end is not the endpoint of the pencil, contradicting the given endpoints. Full-task explanation fails.'),
  (False,False,'Does not choose A or B, but falsely says three closed segments in A cannot identify a triangle and asks unnecessary geometry data. Hint is not conceptually sound or useful.'),
  (False,False,'Correct final contradiction and1versus4 argument, but also falsely identifies simultaneous first/last as a central position. The full explanation contains a substantive incorrect logical claim.')
 ],
 2:[
  (False,False,'Misreads minute-hand6 as60minutes and then concludes6:00 and7:00, contradicting described8:30 and9:30.'),
  (True,False,'Correctly derives constant difference5 and next values28,33, with both additions explained.'),
  (False,True,'Valid division relation45/5 but explicitly supplies forbidden final9parts, so hint full task fails.'),
  (True,False,'Correctly converts3dm to30cm and adds2cm to32cm, showing addition rather than digit concatenation; no invented student actions.')
 ],
 3:[
  (True,False,'Correctly identifiesIX=9,XVI=16 and adds9+16=25; all requested values supplied.'),
  (True,False,'Correct independent square areas9and25cm2 and additive total34cm2; consistent units and nonoverlap interpretation.'),
  (False,True,'Correct6cm=60mm and addition but explicitly reveals prohibited130mm, failing hint-only request.'),
  (True,False,'Computes8-to11 elapsed3hours, then explicitly distinguishes actual running time excluding unknown rest and concludes no unique result because rest duration is missing. Initial running-time label is imprecise but explicitly qualified and corrected; it does not assert180minutes as final actual running time.')
 ],
 4:[
  (False,False,'Correct reconstruction18/3=6 and7*6=42m, but user explicitly requests checking against known3/7part; output never performs or states that check. Full requested task incomplete; numerical answer alone correct.'),
  (True,False,'Correct70acute,110obtuse,180straight and separately identifies exact90right/exact180straight. General range wording is imprecise about strict endpoints, but actual requested classifications are consistent and correct.'),
  (False,False,'Identifies6and12 reduction but then falsely equates5/12*6/7 with5/12*1/2*6, dropping denominator7. No final5/14 leak, but hint reasoning changes product and is mathematically wrong.'),
  (True,False,'Identifies wrong divisor2 rather than3for three numbers and correct total48then48/3=16. Remarks stay grounded in provided division step and preserve correct sum.')
 ],
 5:[
  (True,False,'Correct trapezoid19.2cm2, removed triangle3cm2, subtraction16.2cm2, consistent formulas and units.'),
  (True,False,'Correct2hours plus.375hour→22.5minutes→22minutes30seconds, all three normalized parts supplied.'),
  (False,True,'Correct face9cm2,side3cm andcube27cm3 but explicitly reveals prohibited final volume, failing hint-only request.'),
  (True,False,'Correct0.75litre=750ml and900ml exceeds capacity, identifies contradiction with nonoverflow and fixed size. Suggests checking recorded nonoverflow/actual excess claim, a relevant supplied condition; does not silently change volume/capacity or invoke expansion. Wording is repetitive and less useful than explicitly rechecking numeric records, noted as a pedagogical limitation.')
 ]
}
for grade,judgments in reviews.items():
 pair=p/f'paired_g{grade}.json';rows=json.loads(pair.read_bytes());assert len(rows)==len(judgments)==4
 records=[]
 for row,(passed,leak,reason) in zip(rows,judgments):
  actual=row['base'];f=row['fixture'];assert row['adapter']==actual
  assert actual['ended_eos'] and not actual['possibly_truncated'] and not actual['timed_out']
  records.append({'fixture_id':f['id'],'grade':grade,'mode':f['mode'],'base_pass':passed,'selected_pass':passed,'base_hint_leak':leak,'selected_hint_leak':leak,'reason':reason,'selected_reuses_exact_base_output':True})
 result={'all_actual_fields_read':True,'human_review_claimed':False,'root_full_content_review':True,'selected_kind':'untrained_base','input_pair_sha256':hashlib.sha256(pair.read_bytes()).hexdigest(),'decisions':records}
 target=p/f'semantic_g{grade}.json';b=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode()
 if target.exists():assert target.read_bytes()==b
 else:target.write_bytes(b)
 print(json.dumps({'grade':grade,'pass':sum(x['base_pass'] for x in records),'count':len(records)}))
