"""Bounded MCP cell control, saving full receipts and printing compact results.

Uses the already authorized local Colab transport. No dataset download.
"""
import argparse
import ast
import asyncio
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path.home()/'.codex/integrations/colab-mcp'))
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

async def main():
    p=argparse.ArgumentParser()
    p.add_argument('tool')
    p.add_argument('--args-file',required=True)
    p.add_argument('--receipt',required=True)
    p.add_argument('--connection-file',default='data_only_connection.json')
    a=p.parse_args()
    connection=Path.home()/'.codex/integrations/colab-mcp'
    state=json.loads((connection/a.connection_file).read_text())
    if state.get('notebook_url') != 'https://colab.research.google.com/drive/1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l':
        raise ValueError('Refuse a connection to a different notebook; data-only target is required')
    token=(connection/'local_auth.txt').read_text().strip()
    transport=StreamableHttpTransport(state['mcp_url'],headers={'Authorization':f'Bearer {token}'})
    args=json.loads(Path(a.args_file).read_text(encoding='utf8'))
    async with Client(transport,timeout=90) as client:
        response=await client.call_tool(a.tool,args)
        result={'is_error':response.is_error,'data':response.data,
                'structured_content':response.structured_content,
                'content':[c.model_dump(mode='json') for c in response.content]}
    Path(a.receipt).write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str),encoding='utf8')
    print('receipt:',a.receipt)
    content=result.get('structured_content') or result.get('data')
    if isinstance(content,dict) and 'outputs' in content:
        for output in content['outputs']:
            if output.get('output_type')=='stream':
                value=output.get('text','')
                value=''.join(value) if isinstance(value,list) else value
                if len(value)<13000:
                    print(value)
                else:
                    print('Output retained in receipt; length',len(value))
            elif output.get('output_type')=='error':
                print(output.get('ename'),output.get('evalue'))
    elif content is not None:
        print(json.dumps(content,ensure_ascii=False,default=str)[:2000])

if __name__=='__main__':
    asyncio.run(main())
