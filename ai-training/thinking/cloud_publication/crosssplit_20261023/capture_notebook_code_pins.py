import asyncio,json,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.home()/'.codex/integrations/colab-mcp'))
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
async def main():
 r=Path(__file__).resolve().parent;c=Path.home()/'.codex/integrations/colab-mcp';state=json.loads((c/'data_only_connection.json').read_bytes());assert state['notebook_url'].endswith('/1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l')
 async with Client(StreamableHttpTransport(state['mcp_url'],headers={'Authorization':'Bearer '+(c/'local_auth.txt').read_text().strip()}),timeout=60) as client:
  result=await client.call_tool('get_cells',{'includeOutputs':False})
 v=result.structured_content or result.data;assert not result.is_error
 cells=v['cells'];assert 50<=len(cells)<=120
 raw=(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode();assert len(raw)<8*1024*1024
 (r/'live_notebook_code_cells.json').write_bytes(raw)
 baseline=json.loads((r.parent/'owner_resume_20261023/notebook_savepoint.ipynb').read_bytes())
 def source(c):
  s=c.get('source','');return ''.join(s) if isinstance(s,list) else s
 expected=[hashlib.sha256(source(c).encode()).hexdigest() for c in baseline['cells'][:50]]
 actual=[hashlib.sha256(source(c).encode()).hexdigest() for c in cells[:50]]
 assert expected==actual
 pins={'notebook_id':'1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l','live_cell_count':len(cells),'first50_source_sha256':expected,'all_source_pins':[{'id':c.get('id') or c.get('metadata',{}).get('id'),'source_sha256':hashlib.sha256(source(c).encode()).hexdigest()} for c in cells],'original_first50_sources_unchanged':True,'live_outputs_downloaded':False,'training_started':False}
 (r/'live_notebook_source_pins.json').write_text(json.dumps(pins,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'code_control_bytes':len(raw),'cells':len(cells),'original_first50_sources_unchanged':True,'live_outputs_downloaded':False}))
asyncio.run(main())
