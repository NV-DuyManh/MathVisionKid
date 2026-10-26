import asyncio,json,sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path.home()/'.codex/integrations/colab-mcp'))
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
async def main():
 c=Path.home()/'.codex/integrations/colab-mcp';state=json.loads((c/'data_only_connection.json').read_bytes());assert state['notebook_url'].endswith('/1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l')
 async with Client(StreamableHttpTransport(state['mcp_url'],headers={'Authorization':'Bearer '+(c/'local_auth.txt').read_text().strip()}),timeout=90) as client:
  res=await client.call_tool('run_code_cell',{'cellId':'Zbzl6H2yEk2J'})
 v=res.structured_content or res.data;assert not res.is_error
 for o in v.get('outputs',[]):
  if o.get('output_type')=='error':raise RuntimeError(str(o))
 text=''.join(''.join(o['text']) if isinstance(o.get('text'),list) else o.get('text','') for o in v['outputs'] if o['output_type']=='stream');rows=json.loads(text)
 hints={};out=[]
 for row in rows:
  h=row['hints'];key=hashlib.sha256(json.dumps(h,ensure_ascii=False,sort_keys=True).encode()).hexdigest();hints[key]=h
  fields=['sample_id','problem','grade','givens','requested_quantity','student_work','initial_guidance','worked_steps','expected_answer','curriculum_assignment']
  item={k:row.get(k) for k in fields};item['actual_hints_hash']=key;out.append(item)
 print(json.dumps({'actual_distinct_hints':hints,'actual_train_source_rows':out},ensure_ascii=False))
asyncio.run(main())
