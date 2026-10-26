"""Background bounded raw readback of the four existing metadata controls."""
import json,threading,hashlib
from pathlib import Path
from datetime import datetime,timezone
from googleapiclient.http import MediaIoBaseDownload

CONTROL_PARENTS={
 'progress':{'id':'1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX','bytes':16077326,'sha256':'8d8405ae61a65a43fff3593fb78e6c72198f98596a47b6384c1205f3cd726699'},
 'chat':{'id':'1tkSQoAlxXXRUg2AwYfvqsFKVEmM_LmR6','bytes':93166,'sha256':'0197fcc33f6cc1cd1d347ca672b66417268739992e54941cbe22994dcb7c87aa'},
 'context':{'id':'13gdIPQTFKcekoQQtgo0TXc7RgeadzIN9','bytes':809073,'sha256':'ca0cdf45025875c61d1278ab984124d5db644ec84f27618099be9d9f468349b1'},
 'state':{'id':'1TLoQIbrRVmgsg-2uiUujCfM3HrK62Yme','bytes':396476,'sha256':'6d79bb7d65eb80c25cb112b5c0d4e62af7f8a7a852909a2ce9f890f9fdde7b08'},
}
assert not any(t.name=='MathVisionKidFourControlParentsReadOnly' and t.is_alive() for t in threading.enumerate())
_parent_dir=ROOT/'crosssplit_20261023/control_publication'
_parent_dir.mkdir(exist_ok=True,parents=True)
cloud_control_parent_state={'state':'READING_EXISTING_METADATA_CONTROL_PARENTS','started_utc':datetime.now(timezone.utc).isoformat(),'corpus_downloaded_to_pc':False,'training_started':False}

def _read_control_parents_once():
    refs={}
    try:
        api=g2_connected_api()
        for kind,pin in CONTROL_PARENTS.items():
            metadata=api.files().get(fileId=pin['id'],fields='id,size,mimeType',supportsAllDrives=True).execute()
            assert metadata['id']==pin['id'] and int(metadata['size'])==pin['bytes']
            extension={'progress':'.zip','context':'.md','state':'.json','chat':'.json'}[kind]
            dest=_parent_dir/('parent_'+kind+extension)
            with dest.open('wb') as stream:
                download=MediaIoBaseDownload(stream,api.files().get_media(fileId=pin['id'],supportsAllDrives=True),chunksize=4*1024*1024)
                done=False
                while not done:_,done=download.next_chunk(num_retries=3)
            raw=dest.read_bytes();assert len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256']
            refs[kind]=dict(pin,path=str(dest),fresh_raw_readback_verified=True,observed_utc=datetime.now(timezone.utc).isoformat(),transport='AUTHORIZED_COLAB_DRIVE_API_FALLBACK_CONNECTOR_UNKNOWN_TOOL')
            cloud_control_parent_state.update(last_verified=kind,verified_count=len(refs))
        (_parent_dir/'parent_controls_raw_verified.json').write_text(json.dumps(refs,ensure_ascii=False,sort_keys=True,indent=2))
        cloud_control_parent_state.update(state='ALL_FOUR_PARENT_METADATA_CONTROLS_RAW_VERIFIED',refs=refs)
    except Exception as error:
        cloud_control_parent_state.update(state='CONTROL_PARENT_READ_STOPPED_WITH_EVIDENCE',error_type=type(error).__name__,error=str(error))
    cloud_control_parent_state['finished_utc']=datetime.now(timezone.utc).isoformat()
    (_parent_dir/'parent_read_status.json').write_text(json.dumps(cloud_control_parent_state,ensure_ascii=False,sort_keys=True,indent=2))

cloud_control_parent_thread=threading.Thread(target=_read_control_parents_once,name='MathVisionKidFourControlParentsReadOnly',daemon=True)
cloud_control_parent_thread.start()
print(json.dumps(cloud_control_parent_state,ensure_ascii=False))
