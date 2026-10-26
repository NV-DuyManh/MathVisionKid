"""Collect bounded JSON metadata through the existing Colab MCP; no corpus transfer."""
import asyncio,base64,hashlib,io,json,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path.home()/'.codex/integrations/colab-mcp'))
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

async def main():
    root=Path(__file__).resolve().parent
    config=Path.home()/'.codex/integrations/colab-mcp'
    state=json.loads((config/'data_only_connection.json').read_bytes())
    assert state['notebook_url']=='https://colab.research.google.com/drive/1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l'
    cell=json.loads((root/'export_added.json').read_bytes())
    cell=(cell.get('structured_content') or cell.get('data') or cell)['newCellId']
    transport=StreamableHttpTransport(state['mcp_url'],headers={'Authorization':'Bearer '+(config/'local_auth.txt').read_text().strip()})
    async with Client(transport,timeout=90) as client:
        response=await client.call_tool('run_code_cell',{'cellId':cell})
    content=response.structured_content or response.data
    if response.is_error:raise RuntimeError('MCP metadata export failed; no raw payload printed')
    streams=[]
    for output in content.get('outputs',[]):
        if output.get('output_type')=='error':raise RuntimeError(str(output.get('ename'))+':'+str(output.get('evalue')))
        if output.get('output_type')=='stream':
            text=output.get('text','');streams.append(''.join(text) if isinstance(text,list) else text)
    receipt=json.loads(''.join(streams));encoded=receipt.pop('zip_b64')
    data=base64.b64decode(encoded,validate=True)
    assert len(data)==receipt['zip_bytes']<=4*1024*1024
    assert hashlib.sha256(data).hexdigest()==receipt['zip_sha256']
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        assert set(archive.namelist())=={x['name'] for x in receipt['files']}
        assert len(archive.namelist())==len(receipt['files'])
        for ref in receipt['files']:
            assert Path(ref['name']).name==ref['name'] and ref['name'].endswith('.json')
            raw=archive.read(ref['name']);assert len(raw)==ref['bytes']<=24*1024*1024
            assert hashlib.sha256(raw).hexdigest()==ref['sha256'];json.loads(raw)
            (root/ref['name']).write_bytes(raw)
    (root/'metadata_export_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(receipt,ensure_ascii=False))

if __name__=='__main__':asyncio.run(main())
