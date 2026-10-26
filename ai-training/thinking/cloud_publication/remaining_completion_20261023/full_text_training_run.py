"""One full, resumable Qwen3 text epoch. Importing this file starts nothing."""
from dataclasses import asdict
from pathlib import Path
import hashlib, io, json, math, random, time

import full_text_training_contract as contract
from exhaustive_colab_loader import load_qwen_tokenizer, tokenize_assistant_only, pad_batch
from math_data_candidate_stream import CandidateStream
from math_data_drive_bootstrap import GoogleDriveReader, LazyDriveCache
from train_teacher_math_v3 import run_amp_update

PARENT='19ZxkfKVIggdcbSfsAdCtG1ibfJ0CRN3n'
SEED=20261023
ACCUMULATION=16
CHECKPOINT_UPDATES=100

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()

class RunStore:
    """One named run folder, exact filenames, and raw readback for each upload."""
    def __init__(self,api,release_sha,work):
        self.api=api;self.work=Path(work);self.work.mkdir(parents=True,exist_ok=True)
        self.name='MathVisionKid_FULL_TEXT_RUN_20261023_'+release_sha[:12]
        matches=self._find(PARENT,self.name)
        if len(matches)>1:raise ValueError('Multiple matching run folders; refusing duplicate run')
        if matches:
            if matches[0]['mimeType']!='application/vnd.google-apps.folder':raise ValueError('Run name is not a folder')
            self.folder=matches[0]['id']
        else:
            self.folder=api.files().create(body={'name':self.name,'mimeType':'application/vnd.google-apps.folder','parents':[PARENT]},fields='id').execute()['id']
    def _find(self,parent,name):
        if "'" in name:raise ValueError('Unsafe artifact name')
        result=self.api.files().list(q=f"'{parent}' in parents and name='{name}' and trashed=false",fields='files(id,name,mimeType,size),nextPageToken',pageSize=100).execute()
        if result.get('nextPageToken'):raise ValueError('Ambiguous artifact pagination')
        return result.get('files',[])
    def get(self,name):
        refs=self._find(self.folder,name)
        if len(refs)>1:raise ValueError('Duplicate run artifact')
        return refs[0] if refs else None
    def download(self,ref,path):
        from googleapiclient.http import MediaIoBaseDownload
        with Path(path).open('wb') as output:
            down=MediaIoBaseDownload(output,self.api.files().get_media(fileId=ref['id']),chunksize=8*1024*1024)
            done=False
            while not done:_,done=down.next_chunk(num_retries=3)
        if Path(path).stat().st_size!=int(ref['size']):raise ValueError('Run artifact download size mismatch')
    def put(self,name,path):
        from googleapiclient.http import MediaFileUpload
        ref=self.get(name)
        if ref and name.startswith('checkpoint_step_'):
            check=self.work/('existing_'+name);self.download(ref,check)
            if digest(check)!=digest(path):raise ValueError('Immutable checkpoint generation differs')
            check.unlink()
            return dict(id=ref['id'],name=name,bytes=int(ref['size']),sha256=digest(path),fresh_raw_readback_verified=True)
        media=MediaFileUpload(str(path),mimetype='application/octet-stream',chunksize=8*1024*1024,resumable=True)
        if ref:request=self.api.files().update(fileId=ref['id'],media_body=media,fields='id,size')
        else:request=self.api.files().create(body={'name':name,'parents':[self.folder]},media_body=media,fields='id,size')
        result=None
        while result is None:_,result=request.next_chunk(num_retries=3)
        readback=self.work/('readback_'+name)
        self.download(result,readback)
        actual=digest(path)
        if digest(readback)!=actual:raise ValueError('Checkpoint raw readback SHA mismatch')
        readback.unlink()
        return dict(id=result['id'],name=name,bytes=int(result['size']),sha256=actual,fresh_raw_readback_verified=True)
    def json(self,name,value):
        path=self.work/name;path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        return self.put(name,path)

def run(api,progress,work,status):
    """Caller has explicitly authorized full text training on the free T4."""
    import torch
    from transformers import AutoModelForCausalLM, BitsAndBytesConfig, get_cosine_schedule_with_warmup
    from peft import (LoraConfig,get_peft_model,prepare_model_for_kbit_training,
                      get_peft_model_state_dict,set_peft_model_state_dict)
    if not torch.cuda.is_available():raise RuntimeError('Free GPU runtime required; no CPU fallback')
    import zipfile
    work=Path(work);work.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(progress) as archive:
        readiness=archive.read('full_text_training_release_20261023/release_manifest.json')
        ready=json.loads(readiness)
        candidate=archive.read(ready['source_candidate_manifest']['member'])
        adjudication=archive.read(ready['technical_adjudication']['member'])
        recipe_bytes=archive.read(ready['recipe_pointer']['member'])
    validated=contract.validate_release_evidence(candidate,adjudication,recipe_bytes,readiness,owner_scope=contract.OWNER_SCOPE)
    config=dict(model=contract.MODEL_ID,revision=contract.MODEL_REVISION,max_sequence_tokens=2048,
                expected_rows=6502344,epochs=1,accumulation=ACCUMULATION,microbatch=1,
                lr=1e-4,lora_r=16,lora_alpha=32,lora_dropout=.05,seed=SEED,
                recipe_sha256=contract.RECIPE_SHA256,release_sha256=hashlib.sha256(readiness).hexdigest())
    config_sha=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()
    store=RunStore(api,config['release_sha256'],work/'run_artifacts')
    status.update(state='LOADING_PINNED_MODEL',training_started=False,run_folder_id=store.folder,config=config)
    previous_config=store.get('run_config.json')
    if previous_config:
        config_path=work/'existing_run_config.json';store.download(previous_config,config_path)
        if json.loads(config_path.read_bytes())!=config:raise ValueError('Existing run configuration changed')
    else:store.json('run_config.json',config)
    reader=GoogleDriveReader(api);cache=LazyDriveCache(reader,validated.recipe,work/'payload_cache')
    stream=CandidateStream(validated.recipe,cache,'train')
    tokenizer=load_qwen_tokenizer()
    torch.manual_seed(SEED);torch.cuda.manual_seed_all(SEED)
    quant=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=torch.float16)
    model=AutoModelForCausalLM.from_pretrained(contract.MODEL_ID,revision=contract.MODEL_REVISION,
         quantization_config=quant,device_map={'':0},torch_dtype=torch.float16,trust_remote_code=False)
    model=prepare_model_for_kbit_training(model)
    model=get_peft_model(model,LoraConfig(task_type='CAUSAL_LM',r=16,lora_alpha=32,lora_dropout=.05,bias='none',
          target_modules=['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj']))
    model.config.use_cache=False;model.train()
    parameters=[p for p in model.parameters() if p.requires_grad]
    optimizer=torch.optim.AdamW(parameters,lr=config['lr'],weight_decay=.01)
    total_updates=math.ceil(config['expected_rows']/ACCUMULATION)
    scheduler=get_cosine_schedule_with_warmup(optimizer,max(1,int(total_updates*.03)),total_updates)
    scaler=torch.amp.GradScaler('cuda',init_scale=1024,growth_interval=2000)
    step=0;rows_done=0;cursor=None;epoch_complete=False
    checkpoint=work/'resume_state.pt';expected=store.get('checkpoint_receipt.json')
    if expected:
        receipt_path=work/'resume_receipt.json';store.download(expected,receipt_path)
        receipt=json.loads(receipt_path.read_bytes())
        existing=store.get(receipt['name'])
        if not existing or existing['id']!=receipt['id']:raise ValueError('Committed checkpoint generation absent')
        store.download(existing,checkpoint)
        if receipt['sha256']!=digest(checkpoint):raise ValueError('Resume checkpoint SHA changed')
        saved=torch.load(checkpoint,map_location='cpu',weights_only=True)
        if saved['config_sha256']!=config_sha:raise ValueError('Resume configuration differs')
        set_peft_model_state_dict(model,saved['adapter']);optimizer.load_state_dict(saved['optimizer'])
        scheduler.load_state_dict(saved['scheduler']);scaler.load_state_dict(saved['scaler'])
        torch.set_rng_state(saved['cpu_rng']);torch.cuda.set_rng_state(saved['cuda_rng'])
        step=saved['step'];rows_done=saved['rows_done'];cursor=saved['cursor'];epoch_complete=saved['epoch_complete']
        if not 0<=step<=total_updates or rows_done!=min(step*ACCUMULATION,config['expected_rows']):raise ValueError('Resume step/count inconsistent')
        if not isinstance(cursor,dict) or cursor.get('recipe_sha256')!=stream.identity or cursor.get('split')!='train':raise ValueError('Resume cursor identity/split invalid')
        ci=cursor.get('member_index');line=cursor.get('next_line')
        if type(ci) is not int or type(line) is not int or not 0<=ci<=len(stream.entries) or line<0:raise ValueError('Resume cursor bounds invalid')
        if ci==len(stream.entries) and line!=0:raise ValueError('Terminal cursor invalid')
        if ci<len(stream.entries) and line>stream.entries[ci]['rows']:raise ValueError('Cursor exceeds member rows')
        if epoch_complete and (rows_done!=config['expected_rows'] or ci!=len(stream.entries) or line!=0):raise ValueError('False completed checkpoint')
        del saved
    def persist():
        payload={'config_sha256':config_sha,'step':step,'rows_done':rows_done,'cursor':cursor,'epoch_complete':epoch_complete,
         'adapter':{k:v.detach().cpu() for k,v in get_peft_model_state_dict(model).items()},
         'optimizer':optimizer.state_dict(),'scheduler':scheduler.state_dict(),'scaler':scaler.state_dict(),
         'cpu_rng':torch.get_rng_state(),'cuda_rng':torch.cuda.get_rng_state()}
        temporary=work/'resume_state.pending';torch.save(payload,temporary);temporary.replace(checkpoint)
        generation=f'checkpoint_step_{step:07d}_rows_{rows_done:08d}_{digest(checkpoint)[:16]}.pt'
        proof=store.put(generation,checkpoint);proof.update(config_sha256=config_sha,step=step,rows_done=rows_done,epoch_complete=epoch_complete)
        # Previous generation remains intact; only this small pointer changes last.
        store.json('checkpoint_receipt.json',proof)
        status.update(last_verified_checkpoint=proof)
    def export_adapter():
        model.save_pretrained(work/'adapter');tokenizer.save_pretrained(work/'adapter')
        package=work/'adapter_release.zip'
        with zipfile.ZipFile(package,'w',compression=zipfile.ZIP_DEFLATED) as archive:
            for asset in (work/'adapter').iterdir():
                if asset.is_file():archive.write(asset,asset.name)
            archive.writestr('training_release.json',json.dumps(config,ensure_ascii=False,indent=2))
        proof=store.put('adapter_release.zip',package)
        status.update(adapter_artifact=proof,state='FULL_TEXT_EPOCH_COMPLETE',training_started=True,complete=True)
        store.json('progress.json',status)
    status.update(state='STREAMING_ALL_TRAIN_ROWS',step=step,rows_done=rows_done,training_started=step>0)
    if epoch_complete:
        export_adapter();return
    pending=[];started=time.monotonic();last_cursor=cursor;update_inflight=False
    def update_group(group):
        nonlocal step,rows_done,cursor,update_inflight
        def backward(items):
            loss_sum=0.
            for item in items:
                batch={k:torch.tensor(v,dtype=torch.long,device='cuda') for k,v in pad_batch([item['encoded']],tokenizer.pad_token_id).items()}
                with torch.autocast('cuda',dtype=torch.float16):loss=model(**batch).loss
                if not bool(torch.isfinite(loss)):raise FloatingPointError('Nonfinite forward loss; no row acknowledged')
                loss_sum+=float(loss.detach());scaler.scale(loss/len(items)).backward()
                del batch,loss
            return loss_sum/len(items)
        def overflow(event):status.update(state='RETRYING_SAME_GROUP_AFTER_AMP_OVERFLOW',overflow=event)
        update_inflight=True
        metric=run_amp_update(group,backward,optimizer,scaler,scheduler,
            lambda:(torch.get_rng_state(),torch.cuda.get_rng_state()),
            lambda s:(torch.set_rng_state(s[0]),torch.cuda.set_rng_state(s[1])),
            lambda:any(p.grad is not None for p in parameters) and all(bool(torch.isfinite(p.grad).all()) for p in parameters if p.grad is not None),
            lambda:torch.nn.utils.clip_grad_norm_(parameters,1.),overflow)
        step+=1;rows_done+=len(group);cursor=group[-1]['cursor']
        update_inflight=False
        status.update(state='TRAINING_ALL_TEXT',training_started=True,step=step,total_updates=total_updates,
                      rows_done=rows_done,expected_rows=config['expected_rows'],last_update=metric,seconds_this_session=round(time.monotonic()-started,1))
        if step==1 or step%CHECKPOINT_UPDATES==0:persist();store.json('progress.json',status)
        if step==1 or step%10==0:print(json.dumps(status,ensure_ascii=False),flush=True)
    try:
        for row,next_cursor,evidence in stream.events(cursor):
            last_cursor=asdict(next_cursor)
            if row is None:continue
            if rows_done+len(pending)>=config['expected_rows']:raise ValueError('Train stream exceeds exact released row count')
            if row['split']!='train':raise ValueError('Evaluation row reached optimizer')
            pending.append({'encoded':tokenize_assistant_only(row,tokenizer,2048),'cursor':last_cursor})
            if len(pending)==ACCUMULATION:update_group(pending);pending=[]
        if pending:update_group(pending);pending=[]
        if rows_done!=config['expected_rows']:raise ValueError('Train stream ended early')
        cursor=last_cursor;epoch_complete=True;persist()
        export_adapter()
    except BaseException as error:
        # Persist only the last optimizer-success cursor; pending rows replay.
        optimizer.zero_grad(set_to_none=True)
        status.update(state='TRAINING_STOPPED_WITH_CHECKPOINT',error_type=type(error).__name__,error=str(error),complete=False)
        if step>0 and not update_inflight:
            try:persist();store.json('progress.json',status)
            except Exception as save_error:status.update(checkpoint_save_error=str(save_error))
        elif update_inflight:
            status.update(recovery='DISCARD_UNCOMMITTED_RUNTIME_STATE_RESUME_LAST_VERIFIED_CLOUD_GENERATION')
        raise
