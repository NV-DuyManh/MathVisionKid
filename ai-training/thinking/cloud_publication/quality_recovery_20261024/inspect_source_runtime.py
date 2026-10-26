import pathlib,json,hashlib,collections
r=pathlib.Path('/content/mathvisionkid_quality_recovery_20261024')
rows=[json.loads(x) for x in (r/'training_view.jsonl').read_text().splitlines()]
targets=collections.Counter((x['mode'],x['messages'][-1]['content']) for x in rows)
samples=[];seen=set()
for g in range(1,6):
 for mode in ['worked_solution','hint_level_1','hint_level_2','hint_level_3']:
  candidates=[x for x in rows if x['grade']==g and x['mode']==mode]
  for x in candidates[:2 if mode=='worked_solution' else 1]:
   if x['sample_id'] not in seen:samples.append(x);seen.add(x['sample_id'])
for kind in ['missing','student']:
 candidates=[x for x in rows if x['mode']=='worked_solution' and ((not json.loads(x['messages'][-1]['content']).get('can_solve',True)) if kind=='missing' else bool(json.loads(x['messages'][1]['content']).get('student_work')))]
 for x in candidates[:5]:
  if x['sample_id'] not in seen:samples.append(x);seen.add(x['sample_id'])
manifest=json.loads((r/'sampling_manifest.json').read_bytes())
out={'rows':len(rows),'mode_counts':dict(collections.Counter(x['mode'] for x in rows)),'manifest_case_example':manifest['selected_cases_manifest'][0],'target_duplicates':{'unique':len(targets),'repeated_rows_beyond_first':sum(n-1 for n in targets.values())},'frequent_targets':[{'mode':m,'count':n,'target':t} for (m,t),n in targets.most_common(10)],'source_samples':samples,'install_status':json.loads((r/'install_status.json').read_bytes()) if (r/'install_status.json').exists() else None}
(r/'source_diagnostic.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps(out,ensure_ascii=False))
