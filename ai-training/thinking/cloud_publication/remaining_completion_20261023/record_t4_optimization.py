"""Append an execution overlay and actual measurements; retain the released data."""
from pathlib import Path
import hashlib,json,sys,zipfile
from datetime import datetime,timezone

def read_runtime(path):
    doc=json.loads(Path(path).read_bytes())
    value=doc.get('structured_content') or doc.get('data') or doc.get('result')
    text=''.join(''.join(x.get('text',[])) if isinstance(x.get('text'),list) else x.get('text','') for x in value['outputs'] if x.get('output_type')=='stream')
    return json.loads(text)

def main(staging,phase):
    staging=Path(staging);phase=Path(phase);parent=staging/'parents';out=staging/'optimized';out.mkdir(exist_ok=True)
    runtime=read_runtime(phase/'t4_probe_status_latest.json')
    recovered=read_runtime(phase/'quota_recovery_verified.json')
    assert runtime['worker_alive'] and runtime['state']=='TRAINING_ALL_TEXT'
    assert runtime['rows_done']>2640 and runtime['rows_done']==runtime['step']*16
    assert runtime['config']['expected_rows']==6502344 and runtime['config']['epochs']==1
    optimization=runtime['t4_batch_optimization']
    assert optimization['state'] in ('APPLIED','KEPT_ORIGINAL_BATCH','RUNTIME_OOM_FALLBACK_SAME_GROUP')
    assert optimization['benchmark_optimizer_updates']==0 and optimization['model_weights_unchanged_during_probe']
    assert optimization['source_or_target_bytes_changed']==0 and not optimization['truncation_allowed']
    assert recovered['last_verified_checkpoint']['step']==165 and recovered['last_verified_checkpoint']['fresh_raw_readback_verified']
    now=datetime.now(timezone.utc).isoformat()
    launcher=(phase/'start_full_text_training_optimized_runtime.py').read_bytes()
    launcher_ref=json.loads((phase/'optimized_launcher_remote_verified.json').read_bytes())
    assert launcher_ref['id']=='1ft_qo_-8QJRFe7k1ZJrrKzrL1By-qyUh' and launcher_ref['fresh_raw_readback_verified']
    assert launcher_ref['bytes']==len(launcher) and launcher_ref['sha256']==hashlib.sha256(launcher).hexdigest()
    run=dict(runtime_observation=runtime,run_folder_id=runtime['run_folder_id'],progress_file_id='1tES2KilfuodLlTxpl95_9zsAVmWi8Ow7',
             checkpoint_pointer_file_id='1cADUsyiQm-tRvjj5HYmTzmYX-tkkX59o',launcher=launcher_ref,training_started=True,epoch_complete=False,
             execution_overlay_member='full_text_training_release_20261023/execution_optimization_20261023/',original_semantic_config_unchanged=True)
    record=dict(observed_utc=now,current_run=run,prior_probe=recovered.get('t4_batch_optimization_history',[]),
                stopped_probe=recovered['t4_batch_optimization'],quota_error=recovered.get('error'),recovered_checkpoint=recovered['last_verified_checkpoint'],
                recovery='EXACT_PRE_PROBE_SNAPSHOT_VERIFIED_NO_OPTIMIZER_ATTEMPT',tests='7 CPU tests passed; actual train loss parity and max-length GPU probes recorded',
                quality_guarantee=False,all_6502344_train_rows_preserved=True,validation_test_separate=True)
    record_bytes=(json.dumps(record,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
    (phase/'t4_optimization_execution_record.json').write_bytes(record_bytes)
    package=out/'next_progress.zip';package.write_bytes((parent/'progress.zip').read_bytes())
    prefix=run['execution_overlay_member']
    with zipfile.ZipFile(package,'a',compression=zipfile.ZIP_DEFLATED) as archive:
        assert not any(x.startswith(prefix) for x in archive.namelist())
        archive.writestr(prefix+'code_hashes.json',(phase/'execution_code_hashes.json').read_bytes())
        archive.writestr(prefix+'execution_record.json',record_bytes)
        for name in ('drive_quota_resilience.py','t4_microbatch_optimization_v2.py','t4_microbatch_optimization.py','start_full_text_training_optimized_runtime.py','optimized_launcher_remote_verified.json','test_t4_microbatch_optimization.py','test_drive_quota_resilience.py','quota_recovery_verified.json','record_t4_optimization.py'):
            archive.writestr(prefix+name,(phase/name).read_bytes())
    with zipfile.ZipFile(parent/'progress.zip') as before,zipfile.ZipFile(package) as after:
        assert len(after.namelist())==len(set(after.namelist()))
        for name in before.namelist():
            assert hashlib.sha256(before.read(name)).digest()==hashlib.sha256(after.read(name)).digest(),name
    ids={'progress':'1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX','chat':'1tkSQoAlxXXRUg2AwYfvqsFKVEmM_LmR6','context':'13gdIPQTFKcekoQQtgo0TXc7RgeadzIN9','state':'1TLoQIbrRVmgsg-2uiUujCfM3HrK62Yme'}
    for kind in ('chat','state'):
        doc=json.loads((parent/(kind+'.json')).read_bytes())
        doc.setdefault('full_text_training_execution_history',[]).append(dict(previous=doc.get('current_full_text_training_run'),new_execution_record=record))
        doc.update(current_full_text_training_run=run,last_verified_training_checkpoint=runtime['last_verified_checkpoint'],training_started=True,gpu_used=True,model_weights_loaded=True,whole_training_epoch_completed=False)
        if kind=='state':doc['updated_utc']=now
        (out/('next_'+kind+'.json')).write_text(json.dumps(doc,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8')
    journal=(f'\n\n### Nhật ký 23/10/2026 — T4 execution overlay và khôi phục quota Drive\n'
      f'Mốc{now}; quan sát thực{runtime["observed_utc"]}:step{runtime["step"]},rows{runtime["rows_done"]}/6502344,worker_alive=true. '
      'Drive từng báo403rateLimitExceeded trong rawreadbackcheckpoint165, trước mọioptimizer/probe mới; checkpoint165/2640được rawreadback/hash và commitpointer thành công, không mất tiến độ. '
      f'Checkpoint khôi phục ID{recovered["last_verified_checkpoint"]["id"]},SHA{recovered["last_verified_checkpoint"]["sha256"]}. '
      'Đã thêmrequestspacing1.25s và boundedretry60s riêngrateLimitExceeded/429; lỗi quyền và storagekhông tự coi rate limit. '
      f'Benchmark trên train group thực chọnphysicalmicrobatch{optimization["physical_microbatch"]},gradientcheckpointing={optimization["gradient_checkpointing"]},selectedsupervisedlogits={optimization["selected_supervised_logits"]},speedupđođược={optimization.get("measured_speedup",1):.4f}x. '
      'Giữ nguyên optimizergroup16,LR,epoch1,toàn bộinput/target/mask/EOT,khôngtruncation; chỉgomđộdàitrongcùnggroup và bỏlogitkhôngcóloss. '
      'Thayđổithứtựcộngvàdropoutcóthểkhácquỹđạosốhọc;khônghứaweightbitidentical/chấtlượngbest. '
      '7CPUtests pass và GPUmaxlength1481/lossparitykhôngstepoptimizer được ghi evidence. '
      'Lầnbatchnaive2chậmhơn vàbatch4OOM ởprobe cũ giữ audit. Originalbase/release/config/data/frozen/eval giữ nguyên; overlayvàlauncherpinriêngtrongPROGRESS. '
      'TEXT_TRAINING_DATASET_READY=true;epochchưaxong;visual/thựchànhpendingvàTRAINING_DATASET_READY=falsegiữ nguyên.\n').encode()
    (out/'next_context.md').write_bytes((parent/'context.md').read_bytes()+journal)
    pins={}
    for kind,fid in ids.items():
        ext='.zip' if kind=='progress' else '.md' if kind=='context' else '.json'
        file=out/('next_'+kind+ext);b=file.read_bytes()
        pins[kind]=dict(id=fid,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),path=str(file.resolve()))
    (out/'prepared_pins.json').write_text(json.dumps(pins,indent=2))
    (phase/'optimized_launcher_pin.json').write_text(json.dumps(launcher_ref,indent=2))
    print(json.dumps(dict(controls=pins,launcher=launcher_ref),ensure_ascii=False))

if __name__=='__main__':main(*sys.argv[1:])
