"""Build bounded Colab payloads and preserve OCR cells when saving one notebook."""
import argparse
import base64
import copy
import hashlib
import io
import json
from pathlib import Path
import zipfile

HERE=Path(__file__).resolve().parent
EVIDENCE=HERE/'evidence'/'teacher_math_v3_20261013'

def save_notebook(receipt_path,original_path,target):
    receipt=json.loads(Path(receipt_path).read_text(encoding='utf-8'))
    value=receipt.get('data') or receipt.get('structured_content')
    if isinstance(value,str): value=json.loads(value)
    if not isinstance(value,dict) or 'cells' not in value:
        text=next(c['text'] for c in receipt['content'] if c.get('type')=='text')
        value=json.loads(text)
    live=value['cells']
    original=json.loads(Path(original_path).read_text(encoding='utf-8'))
    assert len(live)>=len(original['cells'])
    for before,now in zip(original['cells'][:8],live[:8]):
        assert ''.join(before['source'])==''.join(now['source']),'Original OCR source changed'
        assert before.get('id',before.get('metadata',{}).get('id'))==now['id'],'Original OCR ID changed'
        # Colab MCP omits output display metadata. Compare every exposed field
        # and preserve the original complete object (including that metadata).
        old_outputs=before.get('outputs',[]);new_outputs=now.get('outputs',[])
        assert len(old_outputs)==len(new_outputs),'Original OCR output count changed'
        for old_output,new_output in zip(old_outputs,new_outputs):
            assert all(old_output.get(k)==v for k,v in new_output.items()),'Original OCR output changed'
    result=copy.deepcopy(original)
    previous={c.get('id',c.get('metadata',{}).get('id')):c for c in original['cells']}
    rebuilt=[]
    for index,cell in enumerate(live):
        if index<8:
            rebuilt.append(copy.deepcopy(original['cells'][index]));continue
        item=copy.deepcopy(previous.get(cell['id'],{'metadata':{}}))
        item.update(cell_type=cell['cell_type'],id=cell['id'],source=cell['source'])
        if cell['cell_type']=='code':
            item.update(execution_count=cell.get('execution_count'),outputs=cell.get('outputs',[]))
        rebuilt.append(item)
    result['cells']=rebuilt
    assert result['cells'][:8]==original['cells'][:8]
    Path(target).parent.mkdir(parents=True,exist_ok=True)
    Path(target).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    print(json.dumps({'cells':len(rebuilt),'original_ocr_objects_preserved':True,'bytes':Path(target).stat().st_size,
        'sha256':hashlib.sha256(Path(target).read_bytes()).hexdigest()}))

def build_payload(source_files,data_files,configurations,index):
    """Trusted project files only, with a frozen SHA manifest inside the payload."""
    members={}
    for path in source_files:
        path=Path(path);members['src/'+path.name]=path.read_bytes()
    for key,path in data_files.items(): members[key]=Path(path).read_bytes()
    for name,config in configurations.items(): members['configs/'+name+'.json']=json.dumps(config,indent=2).encode()
    hashes={name:hashlib.sha256(data).hexdigest() for name,data in members.items()}
    members['bundle_manifest.json']=json.dumps({'files':hashes,'production_approved':False},indent=2).encode()
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,data in sorted(members.items()):archive.writestr(name,data)
    raw=stream.getvalue();payload=base64.b64encode(raw).decode()
    code='''# MATHVISIONKID — frozen teacher data/trainer deployment, no training in this cell
import base64,hashlib,io,json,subprocess,sys,zipfile
from pathlib import Path
from google.colab import drive
if not Path('/content/drive/MyDrive').exists():drive.mount('/content/drive')
homes=[p for p in Path('/content/drive/MyDrive').iterdir() if p.is_dir() and p.name.strip()=='MathVisionKidAI']
assert len(homes)==1,'Cannot identify project Drive root'
MVK_V3_ROOT=homes[0]/'ai-training'/'thinking'/'teacher_math_v3'
MVK_V3_ROOT.mkdir(parents=True,exist_ok=True)
raw=base64.b64decode(PAYLOAD)
assert hashlib.sha256(raw).hexdigest()==PAYLOAD_SHA
with zipfile.ZipFile(io.BytesIO(raw)) as archive:
    expected=json.loads(archive.read('bundle_manifest.json'))['files']
    for name in archive.namelist():
        target=(MVK_V3_ROOT/name).resolve()
        assert target.is_relative_to(MVK_V3_ROOT.resolve()),'Unsafe archive path'
        data=archive.read(name)
        if name in expected:assert hashlib.sha256(data).hexdigest()==expected[name]
        if target.exists():assert target.read_bytes()==data,'Frozen deployment changed: '+name
        else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
print('TEACHER_V3_BUNDLE',json.dumps({'sha256':PAYLOAD_SHA,'files':len(expected),'root':str(MVK_V3_ROOT)}))
'''.replace('PAYLOAD_SHA',repr(hashlib.sha256(raw).hexdigest())).replace('PAYLOAD',repr(payload))
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    (EVIDENCE/'deploy_cell.py').write_text(code,encoding='utf-8')
    (EVIDENCE/'deploy_args.json').write_text(json.dumps({'cellIndex':index,'language':'python','code':code},ensure_ascii=False),encoding='utf-8')
    (EVIDENCE/'bundle.zip').write_bytes(raw)
    (EVIDENCE/'bundle_manifest.json').write_text(json.dumps({'files':hashes,'zip_sha256':hashlib.sha256(raw).hexdigest()},indent=2),encoding='utf-8')
    print(json.dumps({'bytes':len(raw),'files':len(hashes),'sha256':hashlib.sha256(raw).hexdigest()}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='action',required=True)
    p=sub.add_parser('save_notebook');p.add_argument('receipt');p.add_argument('original');p.add_argument('target')
    args=parser.parse_args()
    if args.action=='save_notebook':save_notebook(args.receipt,args.original,args.target)
