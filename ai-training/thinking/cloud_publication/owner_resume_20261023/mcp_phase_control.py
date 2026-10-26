"""Bounded control over the already authorized data-only Colab MCP."""
import argparse,asyncio,json,sys
from pathlib import Path
sys.path.insert(0,str(Path.home()/'.codex/integrations/colab-mcp'))
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

R=Path(__file__).resolve().parent
async def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['status','launch','finalizer','cells','observe'])
    a=parser.parse_args()
    root=Path.home()/'.codex/integrations/colab-mcp';state=json.loads((root/'data_only_connection.json').read_bytes())
    assert state['notebook_url']=='https://colab.research.google.com/drive/1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l'
    transport=StreamableHttpTransport(state['mcp_url'],headers={'Authorization':'Bearer '+(root/'local_auth.txt').read_text().strip()})
    async with Client(transport,timeout=75) as client:
        if a.action=='cells':
            result=await client.call_tool('get_cells',{'includeOutputs':True})
        else:
            if a.action in ('status','observe'):
                content=(R/'runtime_status.py').read_text(encoding='utf8')
                if a.action=='observe':
                    content=content.replace("print(json.dumps(observation,ensure_ascii=False))", "with sqlite3.connect(V3_DB.as_uri()+'?mode=ro',uri=True,timeout=30) as count_db:\n    observation['unique_chat_rows_processed']=count_db.execute('SELECT count(*) FROM samples').fetchone()[0]\ncount_db.close()\nprint(json.dumps(observation,ensure_ascii=False))")
                result=await client.call_tool('update_cell',{'cellId':'NGRT7K_nW2sP','content':content})
                if result.is_error:raise RuntimeError(str(result))
                cell='NGRT7K_nW2sP'
            else:
                filename={'launch':'launch_single_worker.py','finalizer':'finalizer_setup.py'}[a.action]
                result=await client.call_tool('add_code_cell',{'cellIndex':52 if a.action=='launch' else 53,'language':'python','code':(R/filename).read_text(encoding='utf8')})
                data=result.structured_content or result.data
                (R/(a.action+'_added.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
                cell=data['newCellId']
            result=await client.call_tool('run_code_cell',{'cellId':cell})
        data=result.structured_content or result.data
        (R/(a.action+'_latest.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
        if result.is_error:raise RuntimeError(str(data))
        if a.action=='cells':print({'cells':len(data.get('cells',[]))});return
        for o in data.get('outputs',[]):
            if o.get('output_type')=='stream':
                text=o.get('text','');text=''.join(text) if isinstance(text,list) else text
                try:value=json.loads(text)
                except Exception:
                    print(text);continue
                if a.action in ('status','observe'):
                    (R/'runtime_observation.json').write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')
                    summary={k:value.get(k) for k in ['observed_utc','committed_physical_chat_rows','unique_chat_rows_processed','worker_alive','worker_state','worker_error','checkpoint_io','final_metadata_alive','final_metadata_status']}
                    summary['last_verified_checkpoint']={k:value.get('checkpoint',{}).get(k) for k in ['bytes','sha256','observed_utc']}
                    summary['issues_now']=value.get('issues_now')
                    summary['structural15_repair_alive']=value.get('structural15_repair_alive')
                    summary['structural15_repair_state']=value.get('structural15_repair_state')
                    print(json.dumps(summary,ensure_ascii=False))
                else:print(text)
            elif o.get('output_type')=='error':raise RuntimeError(str(o))

if __name__=='__main__':asyncio.run(main())
