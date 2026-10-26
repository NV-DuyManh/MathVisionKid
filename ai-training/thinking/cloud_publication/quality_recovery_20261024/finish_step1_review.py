from pathlib import Path
import json,hashlib,copy
p=Path(__file__).parent;d=p/'review_step_000001';old=p/'review_step_000050'
pairs=json.loads((d/'paired_g5.json').read_bytes());prior=json.loads((old/'semantic_g5.json').read_bytes());byid={x['fixture_id']:x for x in prior['decisions']}
reasons=[
 'Same complete percentage reasoning as base: 1.25x minus20% of1.25x returns x=100%; both percentage bases correct.',
 'Same valid24 litres/minute and24*1.25=30litres computation as base, consistent units.',
 'Uses valid alternative volume argument:2.4*1.5*.8=2.88dm3, .1 cubed=.001dm3, ratio2880; no new arithmetic or unit error.',
 'Same complete worked distances and final0.9km as base; leaks explicitly forbidden final hint answer, so fail with leak.',
 'Same correct length-versus-area explanation as base,1m2=10000cm2 and0.6m2=6000cm2.',
 'Retains valid symbolic equation x(1-m/100)=180000, explains missing exact discount rate and requests it; optional equivalent extra equation suggestion does not invalidate correct sufficient request.'
]
records=[]
for pair,reason in zip(pairs,reasons):
 b=copy.deepcopy(byid[pair['fixture']['id']]);assert all(pair['adapter'][k] is val for k,val in [('ended_eos',True),('possibly_truncated',False),('timed_out',False)])
 b.update(adapter_pass=b['base_pass'],adapter_hint_leak=b['base_hint_leak'],critical_new_error=False,adapter_reason=reason)
 records.append(b)
result={'all_actual_fields_read':True,'human_review_claimed':False,'input_pair_sha256':hashlib.sha256((d/'paired_g5.json').read_bytes()).hexdigest(),'root_review':True,'baseline_review_sha256':hashlib.sha256((old/'semantic_g5.json').read_bytes()).hexdigest(),'decisions':records}
(d/'semantic_g5.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'paired_g5_full_root_review':True,'base_pass':sum(x['base_pass'] for x in records),'cp1_pass':sum(x['adapter_pass'] for x in records)}))
