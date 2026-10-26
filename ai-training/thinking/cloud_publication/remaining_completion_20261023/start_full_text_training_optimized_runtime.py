"""Explicit owner-authorized full-text training launch, not Run All."""
import json, threading, pathlib, sys, subprocess, hashlib, io, zipfile, importlib, traceback
from datetime import datetime,timezone
if 'text_training_drive' not in globals():
    from google.colab import auth
    import google.auth
    from googleapiclient.discovery import build
    auth.authenticate_user()
    _resume_creds,_=google.auth.default()
    text_training_drive=build('drive','v3',credentials=_resume_creds,cache_discovery=False)
assert not any(t.name=='MathVisionKidFullTextTraining' and t.is_alive() for t in threading.enumerate()),'Training already running'
TEXT_RUN_ROOT=pathlib.Path('/content/mathvisionkid_full_text_training')
TEXT_RUN_ROOT.mkdir(parents=True,exist_ok=True)
full_text_training_status={'state':'SETTING_UP_PINNED_TRAINING_DEPENDENCIES','training_started':False,
 'TEXT_TRAINING_DATASET_READY':True,'expected_train_rows':6502344,'validation_rows_reserved':24,'test_rows_reserved':24,
 'registered_utc':datetime.now(timezone.utc).isoformat(),'max_sequence_tokens':2048,'subset_limit':None}

def _full_text_worker():
    try:
        import gc
        gc.collect()
        log=TEXT_RUN_ROOT/'dependency_install.log'
        with log.open('w') as output:
            subprocess.run([sys.executable,'-m','pip','install','-q','transformers==5.16.1','peft==0.21.2','accelerate==1.15.0','bitsandbytes==0.50.2'],stdout=output,stderr=subprocess.STDOUT,check=True)
        full_text_training_status.update(state='VERIFYING_PUBLISHED_FULL_TEXT_RELEASE')
        from googleapiclient.http import MediaIoBaseDownload
        progress=TEXT_RUN_ROOT/'published_progress.zip'
        _meta=text_training_drive.files().get(fileId='1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX',fields='size').execute()
        assert 0<int(_meta['size'])<=32*1024*1024,'Unexpected control package size'
        with progress.open('wb') as output:
            downloader=MediaIoBaseDownload(output,text_training_drive.files().get_media(fileId='1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX'),chunksize=4*1024*1024)
            done=False
            while not done:_,done=downloader.next_chunk(num_retries=3)
        assert progress.stat().st_size==int(_meta['size'])
        code=TEXT_RUN_ROOT/'code';code.mkdir(exist_ok=True)
        prefix='full_text_training_release_20261023/'
        with zipfile.ZipFile(progress) as archive:
            ready=archive.read(prefix+'release_manifest.json')
            assert hashlib.sha256(ready).hexdigest()=='14dc5111ab4d0ac691a6f4b0d49f4395f8544145663bdd42df4e6da1fa6a4fdc'
            code_index=archive.read(prefix+'code_hashes.json')
            assert hashlib.sha256(code_index).hexdigest()=='75a376239b26a5551c652fb3bc3385f44342225738b8fe0d4fee8fd5f322b603'
            pins=json.loads(code_index)
            for member,pin in pins.items():
                name=pathlib.PurePosixPath(member).name
                if not name.endswith('.py'):raise ValueError('Unexpected code filename')
                raw=archive.read(prefix+member)
                assert len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256']
                (code/name).write_bytes(raw)

            execution_prefix='full_text_training_release_20261023/execution_optimization_20261023/'
            execution_index=archive.read(execution_prefix+'code_hashes.json')
            assert hashlib.sha256(execution_index).hexdigest()=='0205f1fa78bfd2504ad111213433fd0909f6db0f0ce00bf4923254dcbc94ef53'
            for name,pin in json.loads(execution_index).items():
                assert name in ('drive_quota_resilience.py','t4_microbatch_optimization_v2.py')
                raw=archive.read(execution_prefix+name)
                assert len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256']
                (code/name).write_bytes(raw)
        sys.path.insert(0,str(code));importlib.invalidate_caches()
        import torch
        assert torch.cuda.is_available() and 'T4' in torch.cuda.get_device_name(0),'Expected free T4 runtime'
        from importlib.metadata import version
        full_text_training_status['libraries']={name:version(name) for name in ['torch','transformers','peft','accelerate','bitsandbytes','tokenizers']}
        full_text_training_status['gpu']=torch.cuda.get_device_name(0)
        import full_text_training_run
        import drive_quota_resilience
        drive_quota_resilience.install(full_text_training_status)
        import t4_microbatch_optimization_v2
        importlib.reload(t4_microbatch_optimization_v2)
        t4_microbatch_optimization_v2.install(full_text_training_status,TEXT_RUN_ROOT)
        full_text_training_run.run(text_training_drive,progress,TEXT_RUN_ROOT,full_text_training_status)
    except BaseException as error:
        full_text_training_status.update(state='SETUP_OR_TRAINING_STOPPED',error_type=type(error).__name__,error=str(error),complete=False)
        (TEXT_RUN_ROOT/'last_error.txt').write_text(traceback.format_exc())
    finally:
        full_text_training_status['observed_utc']=datetime.now(timezone.utc).isoformat()
        (TEXT_RUN_ROOT/'runtime_status.json').write_text(json.dumps(full_text_training_status,ensure_ascii=False,indent=2))

full_text_training_thread=threading.Thread(target=_full_text_worker,name='MathVisionKidFullTextTraining',daemon=True)
full_text_training_thread.start()
print(json.dumps(full_text_training_status,ensure_ascii=False))
