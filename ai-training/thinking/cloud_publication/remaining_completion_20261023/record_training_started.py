"""Record actual optimizer progress, preserving immutable data-release evidence."""
import hashlib,json,sys,zipfile
from pathlib import Path
from datetime import datetime,timezone

def main(staging,phase):
    staging=Path(staging);phase=Path(phase);parent=staging/'prepared';out=staging/'training_started';out.mkdir(exist_ok=True)
    receipt=json.loads((phase/'training_status_latest.json').read_bytes())
    value=receipt.get('structured_content') or receipt.get('data')
    runtime=json.loads(''.join(''.join(o.get('text',[])) if isinstance(o.get('text'),list) else o.get('text','') for o in value['outputs'] if o.get('output_type')=='stream'))
    cp=runtime['last_verified_checkpoint']
    assert runtime['training_started'] and runtime['worker_alive'] and runtime['state']=='TRAINING_ALL_TEXT'
    assert runtime['expected_rows']==6502344 and runtime['config']['epochs']==1
    assert cp['fresh_raw_readback_verified'] and 0<cp['rows_done']<=runtime['rows_done']<6502344
    assert runtime['rows_done']==runtime['step']*16 and cp['rows_done']==cp['step']*16
    assert cp['epoch_complete'] is False
    launcher=json.loads((phase/'training_launcher_remote_verified.json').read_bytes())
    assert launcher['fresh_raw_readback_verified']
    run=dict(runtime_observation=runtime,run_folder_id=runtime['run_folder_id'],
             progress_file_id='1tES2KilfuodLlTxpl95_9zsAVmWi8Ow7',checkpoint_pointer_file_id='1cADUsyiQm-tRvjj5HYmTzmYX-tkkX59o',
             launcher=launcher,training_started=True,epoch_complete=False)
    raw=(json.dumps(run,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
    package=out/'next_progress.zip';package.write_bytes((parent/'next_progress.zip').read_bytes())
    prefix='full_text_training_release_20261023/training_started/'
    with zipfile.ZipFile(package,'a',compression=zipfile.ZIP_DEFLATED) as archive:
        assert not any(n.startswith(prefix) for n in archive.namelist())
        archive.writestr(prefix+'actual_run_started.json',raw)
        for name in ('start_full_text_training_runtime.py','training_status.py','training_launcher_remote_verified.json','full_text_training_release_validation.json','record_training_started.py'):
            archive.writestr(prefix+name,(phase/name).read_bytes())
    for kind in ('chat','state'):
        doc=json.loads((parent/('next_'+kind+'.json')).read_bytes())
        doc.update(training_started=True,gpu_used=True,model_weights_loaded=True,
                   current_full_text_training_run=run,last_verified_training_checkpoint=cp,
                   whole_training_epoch_completed=False)
        (out/('next_'+kind+'.json')).write_text(json.dumps(doc,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8')
    now=datetime.now(timezone.utc).isoformat()
    journal=('\n\n### Nhật ký 23/10/2026 — đã bắt đầu cập nhật trọng số Qwen3 trên T4\n'
      f'Mốc {now}: training_started=true được xác nhận bởi optimizer thực, không chỉ cài môi trường. '
      f'Quan sát {runtime["observed_utc"]}:step{runtime["step"]},rows_done{runtime["rows_done"]}/6502344,worker_alive=true. '
      f'Checkpoint train riêng ID{cp["id"]},step{cp["step"]},rows{cp["rows_done"]},bytes{cp["bytes"]},SHA256{cp["sha256"]},freshrawreadback=true; '
      'checkpoint auditV3 và source/history/eval giữ nguyên. Runfolder1Dacm9bRF_Fmyh3vlRpJG_5Ugpup2bPEq;'
      ' launcher đã kiểm rawreadback ID1ft_qo_-8QJRFe7k1ZJrrKzrL1By-qyUh. '
      'Phạm vi đủ6502344train,validation24/test24 giữriêng,epoch1 chưa hoàn tất; không tập5024/khônglấymẫu. '
      'Qwen3-1.7B revision70d244cc86ccca08cf5af4e1e306ecf908b1ad5e,QLoRA4bit,T4miễnphí,2048tokenkhôngcắt,assistantonlyloss. '
      'Immutable checkpoint generations được đọc raw/sohash rồi mới đổi pointer nhỏ; restart dùng optimizer/RNG/cursor tương ứng. '
      'Giữ TEXT_TRAINING_DATASET_READY=true theo lựa chọn chủ; toànchươngtrình/hình/thựchành cònpending. Lossđầutiên4.16518khôngchứngminhchấtlượngsuy luận; chưatuyênbốbest/100%.\n').encode()
    (out/'next_context.md').write_bytes((parent/'next_context.md').read_bytes()+journal)
    oldpins=json.loads((parent/'prepared_pins.json').read_bytes());pins={}
    for k,v in oldpins.items():
        path=out/('next_'+k+('.zip' if k=='progress' else '.md' if k=='context' else '.json'))
        b=path.read_bytes();pins[k]=dict(id=v['id'],bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
    (out/'prepared_pins.json').write_text(json.dumps(pins,indent=2))
    (phase/'actual_run_started.json').write_bytes(raw)
    print(json.dumps({'training_started':True,'last_cloud_checkpoint_rows':cp['rows_done'],'observed_rows':runtime['rows_done'],'controls':pins}))

if __name__=='__main__':main(*sys.argv[1:])
