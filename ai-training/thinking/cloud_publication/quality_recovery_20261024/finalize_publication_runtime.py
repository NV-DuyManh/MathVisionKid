import pathlib,json,hashlib
r=pathlib.Path('/content/mathvisionkid_quality_recovery_20261024')
assert recovery_process.poll()==recovery_probe_process.poll()==recovery_final_process.poll()==0
final=json.loads((r/'final_eval_publication_status.json').read_bytes())
assert final['state']=='COMPLETE_RAW_VERIFIED','Final evaluation proof files still publishing; do not finalize early'
assert all(x['fresh_raw_readback_verified'] for x in final['artifacts'].values())
pub=json.loads((r/'publication/publication_status.json').read_bytes())
report=r/'training/final_semantic_assessment.json';h=hashlib.sha256(report.read_bytes()).hexdigest()
proof=pub['artifacts']['training/final_semantic_assessment.json']
assert proof['sha256']==h and proof['fresh_raw_readback_verified']
assert json.loads(report.read_bytes())['new_adapter_improvement_demonstrated'] is False
p=r/'publication/finalize_requested.json';value={'finalize_requested':True,'final_semantic_assessment_sha256':h}
if p.exists():assert json.loads(p.read_bytes())==value
else:
 t=p.with_suffix('.pending');t.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n');t.replace(p)
print(json.dumps({'finalization_requested':True,'report_proof':proof,'final_eval_raw_verified_files':len(final['artifacts']),'source_rows_or_labels_changed':False}))
