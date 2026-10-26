"""Reconcile bounded local reference metadata after complete cloud readback."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
RUN=HERE/'cloud_publication/audit_finish_20261022'
def sha(b):return hashlib.sha256(b).hexdigest()
def write(path,v):path.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
projection=json.loads((RUN/'local_control_projection.json').read_text('utf8'))
receipt=projection['receipt'];assert receipt['state_written_last']
assert all(r['fresh_raw_readback_verified'] for r in receipt['controls'].values())
context=HERE.parent/'MATH_TRAINING_CONTEXT.md'
old=context.read_bytes();assert sha(old)=='222d3efeb1494f99c40d30c6d3ab1d8b2b5063980b59ecf51a7293e9dbc73a82'
updated=old+projection['context_delta'].encode('utf8')
assert sha(updated)==receipt['controls']['context']['sha256']
context.write_bytes(updated)
reference=HERE/'exhaustive_cloud_reference.json'
state=json.loads(reference.read_text('utf8'));state.update(projection['state_patch'])
write(reference,state)
artifacts=HERE/'data/primary_math_teacher_20261016/drive_artifacts.json'
refs=json.loads(artifacts.read_text('utf8'))
refs['latest_audit_finish_phase']=dict(evidence_progress_id=receipt['controls']['progress']['id'],
    evidence_member='audit_finish_20261022/runtime_observed.json',controls=receipt['controls'],
    notebook=receipt['notebook'],TRAINING_DATASET_READY=False,training_started=False)
write(artifacts,refs)
write(RUN/'four_controls_remote_verified.json',receipt)
print(json.dumps({'single_context_sha256':sha(updated),'four_controls_fresh_raw_verified':True,
                  'TRAINING_DATASET_READY':False,'training_started':False}))
