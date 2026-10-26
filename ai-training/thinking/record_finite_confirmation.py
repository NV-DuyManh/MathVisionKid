from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent
RUN=HERE/'cloud_publication/final_confirmation_20261022'
p=json.loads((RUN/'local_projection.json').read_text('utf8'))
r=p['result'];assert r['state_written_last'] and r['finite_core_confirmed_complete']
assert all(v['fresh_raw_readback_verified'] for v in r['controls'].values())
context=HERE.parent/'MATH_TRAINING_CONTEXT.md'
old=context.read_bytes()
assert hashlib.sha256(old).hexdigest()=='692eb164552d63a30922437bcc602467047960d6d35f087a3cb434e1047fdf3f'
updated=old+p['context_delta'].encode('utf8')
assert hashlib.sha256(updated).hexdigest()==r['controls']['context']['sha256']
context.write_bytes(updated)
reference=HERE/'exhaustive_cloud_reference.json'
state=json.loads(reference.read_text('utf8'));state.update(p['state_patch'])
reference.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
artifact_path=HERE/'data/primary_math_teacher_20261016/drive_artifacts.json'
artifacts=json.loads(artifact_path.read_text('utf8'));artifacts['latest_finite_core_confirmation']=r
artifact_path.write_text(json.dumps(artifacts,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(RUN/'four_controls_remote_verified.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'finite_core_confirmed_complete':True,'four_controls_raw_verified':True,
    'context_matches_remote_hash':True,'full_expanded_dataset_complete':False,'training_started':False}))
