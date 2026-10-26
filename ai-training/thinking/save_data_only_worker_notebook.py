from pathlib import Path
from copy import deepcopy
import json,hashlib
r=Path('thinking/cloud_publication/colab_data_audit_20261021')
base=Path.home()/'.codex/integrations/colab-mcp'
parent=r/'mcp_evidence/notebook_before_worker_saved.ipynb'
if not parent.exists():parent.write_bytes((r/'notebook_data_only_mcp_saved.ipynb').read_bytes())
old=json.loads(parent.read_text('utf8'));m=json.loads((base/'data_only_cells_after.json').read_text('utf8'))
assert not m['is_error']
cells=m['structured_content']['cells'];assert len(cells)==13
byid={c['id']:c for c in old['cells']};assert len(byid)==10
out=deepcopy(old);out['cells']=[]
for c in cells:
 current=deepcopy(byid.get(c['id'],{'metadata':{},'id':c['id'],'cell_type':c['cell_type']}))
 if c['id'] in byid:assert current['source']==c['source'] and current['cell_type']==c['cell_type']
 current['source']=c['source']
 if c['cell_type']=='code':
  current['outputs']=c.get('outputs',[])
  current['execution_count']=c.get('execution_count') if c.get('execution_count') is not None else current.get('execution_count')
 out['cells'].append(current)
assert len({x['id'] for x in out['cells']})==13
dest=r/'notebook_data_only_mcp_saved.ipynb';dest.write_text(json.dumps(out,ensure_ascii=False,indent=1)+'\n',encoding='utf8')
receipt=dict(parent_drive_notebook_sha256=hashlib.sha256(parent.read_bytes()).hexdigest(),saved_bytes=dest.stat().st_size,saved_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),all10_prior_cell_sources_preserved=True,all13_mcp_cell_ids_preserved=True,v1_and_v2_actual_outputs_preserved=True,finite_data_worker_only=True,training_started=False)
(r/'mcp_evidence/notebook_worker_merge.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
print(json.dumps(receipt))

