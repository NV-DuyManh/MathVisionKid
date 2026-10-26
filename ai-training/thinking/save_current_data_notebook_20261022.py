"""Save a source-preserving MCP notebook snapshot; no cell execution."""
from pathlib import Path
from copy import deepcopy
import json,hashlib
HERE=Path(__file__).resolve().parent
RUN=HERE/'cloud_publication/data_resume_20261022'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    parent=RUN/'notebook_before_current_merge.ipynb';old=json.loads(parent.read_bytes())
    base=Path.home()/'.codex/integrations/colab-mcp'
    result=json.loads((base/'data_only_resume_all_cells_20261022.json').read_text('utf8'))
    assert not result['is_error'];cells=result['structured_content']['cells'];assert len(cells)==15
    oldmap={x['id']:x for x in old['cells']};live={x['id']:x for x in cells}
    assert set(oldmap)<=set(live)
    out=deepcopy(old);out['cells']=[]
    for c in cells:
        if c['id'] in oldmap:
            before=oldmap[c['id']];assert before['source']==c['source'] and before['cell_type']==c['cell_type']
            item=deepcopy(before)
        else:item=dict(id=c['id'],metadata={},cell_type=c['cell_type'])
        item['source']=c['source']
        if c['cell_type']=='code':
            item['outputs']=c.get('outputs',[])
            item['execution_count']=c.get('execution_count') if c.get('execution_count') is not None else item.get('execution_count')
        out['cells'].append(item)
    data=(json.dumps(out,ensure_ascii=False,indent=1)+'\n').encode()
    (RUN/'notebook_data_only_resume_saved.ipynb').write_bytes(data)
    receipt=dict(id='1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l',parent_sha256=sha(parent.read_bytes()),parent_cells=len(oldmap),cell_count=15,bytes=len(data),sha256=sha(data),all_parent_cell_sources_preserved=True,training_started=False,live_status='RUNTIME_OR_STATUS_MISSING',unsaved_prior_v3_source_recovered_as_progress_code=True)
    (RUN/'notebook_merge_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
    print(json.dumps(receipt))
if __name__=='__main__':main()
