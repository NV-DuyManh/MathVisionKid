"""One bounded authorized notebook operation; no retries or Run All."""
import asyncio, json, sys
from pathlib import Path
sys.path.insert(0, str(Path.home()/'.codex/integrations/colab-mcp'))
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

async def main():
    root=Path.home()/'.codex/integrations/colab-mcp'
    connection=json.loads((root/'data_only_connection.json').read_bytes())
    assert connection['notebook_url']=='https://colab.research.google.com/drive/1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l'
    transport=StreamableHttpTransport(connection['mcp_url'],headers={'Authorization':'Bearer '+(root/'local_auth.txt').read_text().strip()})
    code_path=Path(sys.argv[1]); receipt=Path(sys.argv[2])
    async with Client(transport,timeout=75) as client:
        listed=await client.call_tool('get_cells',{'includeOutputs':False})
        if listed.is_error:raise RuntimeError(str(listed))
        cells=(listed.structured_content or listed.data)['cells']
        added=await client.call_tool('add_code_cell',{'cellIndex':len(cells),'language':'python','code':code_path.read_text(encoding='utf8')})
        if added.is_error:raise RuntimeError(str(added))
        add_data=added.structured_content or added.data
        result=await client.call_tool('run_code_cell',{'cellId':add_data['newCellId']})
        value=result.structured_content or result.data
        receipt.write_text(json.dumps({'add':add_data,'is_error':result.is_error,'result':value},ensure_ascii=False,indent=2),encoding='utf8')
        print('cell_id:',add_data['newCellId'])
        for item in value.get('outputs',[]):
            if item.get('output_type')=='stream':
                content=item.get('text',''); content=''.join(content) if isinstance(content,list) else content
                print(content if len(content)<12000 else 'Output retained in receipt: '+str(len(content)))
            elif item.get('output_type')=='error':print(item.get('ename'),item.get('evalue'))

if __name__=='__main__':asyncio.run(main())
