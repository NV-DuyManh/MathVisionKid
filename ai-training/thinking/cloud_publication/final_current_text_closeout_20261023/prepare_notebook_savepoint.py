"""Prepare an exact-ID data-only notebook savepoint from fresh live cells.

Run locally on bounded code/control metadata only. Publication is performed
separately through the Drive connector, followed by fresh raw readback.
"""
from copy import deepcopy
from pathlib import Path
import hashlib
import json

R = Path(__file__).resolve().parent
def read(name):
    return json.loads((R/name).read_bytes())
def sha(data):
    return hashlib.sha256(data).hexdigest()
def source(cell):
    value = cell.get('source', '')
    return ''.join(value) if isinstance(value, list) else value

raw = (R/'parent_notebook.ipynb').read_bytes()
parent_proof = read('parent_notebook_raw_verified.json')
assert parent_proof['id'] == '1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l'
assert parent_proof['fresh_raw_readback_verified'] is True
assert parent_proof['sha256'] == sha(raw) and parent_proof['bytes'] == len(raw)
parent = json.loads(raw)
original = json.loads((R.parent/'owner_resume_20261023/notebook_savepoint.ipynb').read_bytes())
live = read('cells_final.json')['cells']
assert len(live) >= 59
assert len({c['id'] for c in live}) == len(live)
assert [(c['id'], source(c)) for c in live[:50]] == [
    (c['id'], source(c)) for c in original['cells'][:50]]
assert {c['id'] for c in parent['cells']} <= {c['id'] for c in live}
runtime = read('final_runtime_observation.json')
assert runtime['worker_alive'] is False and runtime['final_metadata_alive'] is False
assert runtime['report']['all_declared_members_scanned'] is True
assert runtime['report']['unique_chat_rows_processed'] == 6502392
assert runtime['checkpoint']['fresh_raw_readback_verified'] is True
by_id = {c['id']:c for c in parent['cells']}
notebook = deepcopy(parent)
cells = []
for c in live:
    n = deepcopy(by_id.get(c['id'], {}))
    n.update(cell_type=c['cell_type'], id=c['id'], source=c['source'])
    n.setdefault('metadata', {})
    n['metadata'].setdefault('id', c['id'])
    if n['cell_type'] == 'code':
        n['outputs'] = deepcopy(c.get('outputs', n.get('outputs', [])))
        n.setdefault('execution_count', None)
    cells.append(n)
notebook['cells'] = cells
metadata = notebook.setdefault('metadata', {})
assert metadata.get('accelerator', 'none') == 'none'
metadata['accelerator'] = 'none'
metadata.setdefault('mathvisionkid', {}).update(
    fixed_existing_notebook_id=parent_proof['id'],
    current_text_candidate_rows=6502344,
    raw_chat_rows_all_current_splits=6502392,
    current_text_technical_metadata_complete=True,
    checkpoint=runtime['checkpoint'],
    full_archive_audit_complete=False,
    TRAINING_DATASET_READY=False,
    training_started=False,
    gpu_used=False,
    model_weights_loaded=False,
    instruction='Data preparation evidence only. Do not Run All or launch training.',
)
data = (json.dumps(notebook, ensure_ascii=False, indent=1)+'\n').encode('utf8')
assert len(data) <= 16*1024*1024
assert [(c['id'], source(c)) for c in notebook['cells'][:50]] == [
    (c['id'], source(c)) for c in original['cells'][:50]]
(R/'notebook_savepoint.ipynb').write_bytes(data)
proof = {'id':parent_proof['id'], 'bytes':len(data), 'sha256':sha(data),
         'cell_count':len(cells), 'original_50_cell_sources_preserved':True,
         'fresh_raw_readback_verified':False, 'publication_performed':False,
         'training_started':False}
(R/'notebook_prepared.json').write_text(json.dumps(proof, indent=2), encoding='utf8')
print(json.dumps(proof))
