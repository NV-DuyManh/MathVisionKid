"""Append measured adaptive execution while preserving every earlier member."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys,zipfile
from record_t4_optimization import read_runtime

def main(staging,phase):
    staging=Path(staging);phase=Path(phase);parent=staging/'parents';out=staging/'adaptive';out.mkdir(exist_ok=True)
    runtime=read_runtime(phase/'t4_adaptive_probe_status_latest.json');opt=runtime['t4_batch_optimization']
    assert runtime['worker_alive'] and runtime['state']=='TRAINING_ALL_TEXT'
    assert runtime['rows_done']==16*runtime['step'] and runtime['step']>=opt['before_step']+4
    assert runtime['config']['expected_rows']==6502344 and runtime['config']['epochs']==1
    assert runtime['config']['recipe_sha256']=='1bb69c394c7eaaea7034125c6b3361eebbbe0d77e0715a8454331fbe7cee3ff8'
    assert runtime['config']['release_sha256']=='14dc5111ab4d0ac691a6f4b0d49f4395f8544145663bdd42df4e6da1fa6a4fdc'
    config_sha=hashlib.sha256(json.dumps(runtime['config'],sort_keys=True).encode()).hexdigest()
    assert config_sha=='d8b0b09755917190b3dfa35250300d64b2b0552e838c6b641e110eb312034ac8'
    assert opt['version']==3 and opt['state'] in ('APPLIED','RUNTIME_OOM_FALLBACK_SAME_GROUP')
    assert opt['benchmark_optimizer_updates']==0 and opt['model_weights_unchanged_during_probe']
    assert not opt['truncation_allowed'] and opt['source_or_target_bytes_changed']==0
    assert runtime['last_verified_checkpoint']['fresh_raw_readback_verified']
    cp=runtime['last_verified_checkpoint']
    assert cp['config_sha256']==config_sha and cp['rows_done']==cp['step']*16
    assert 0<cp['step']<=runtime['step'] and not cp['epoch_complete']
    launcher=json.loads((phase/'adaptive_v3_launcher_remote_verified.json').read_bytes())
    raw_launcher=(phase/'start_full_text_training_adaptive_v3.py').read_bytes()
    assert launcher['fresh_raw_readback_verified'] and launcher['sha256']==hashlib.sha256(raw_launcher).hexdigest()
    now=datetime.now(timezone.utc).isoformat();prefix='full_text_training_release_20261023/execution_adaptive_v3_20261023/'
    run=dict(runtime_observation=runtime,run_folder_id=runtime['run_folder_id'],progress_file_id='1tES2KilfuodLlTxpl95_9zsAVmWi8Ow7',
             checkpoint_pointer_file_id='1cADUsyiQm-tRvjj5HYmTzmYX-tkkX59o',launcher=launcher,training_started=True,epoch_complete=False,
             execution_overlay_member=prefix,original_semantic_config_unchanged=True)
    record=dict(observed_utc=now,current_run=run,original_run_scope_unchanged=True,all_6502344_train_rows_preserved=True,
       tests='9 CPU tests passed; variable chunks preserve equal-example loss and causal gradient; actual GPU parity/memory probes recorded',
       selection='Fastest tested safe candidate at >=5% measured group speedup, otherwise previous microbatch2',
       probe_limit='One actual train optimizer group and padded shape stress; not a whole-corpus throughput or quality guarantee',
       prior_execution_history=runtime.get('t4_batch_optimization_history',[]),model_quality_guarantee=False)
    record_bytes=(json.dumps(record,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
    (phase/'t4_adaptive_v3_execution_record.json').write_bytes(record_bytes)
    package=out/'next_progress.zip';package.write_bytes((parent/'progress.zip').read_bytes())
    with zipfile.ZipFile(package,'a',compression=zipfile.ZIP_DEFLATED) as archive:
        assert not any(n.startswith(prefix) for n in archive.namelist())
        archive.writestr(prefix+'execution_record.json',record_bytes)
        archive.writestr(prefix+'code_hashes.json',(phase/'execution_v3_code_hashes.json').read_bytes())
        for name in ('drive_quota_resilience.py','t4_microbatch_optimization_v3.py','start_full_text_training_adaptive_v3.py','adaptive_v3_launcher_remote_verified.json','test_t4_adaptive_v3.py','build_t4_adaptive_v3.py','prepare_adaptive_launcher_v3.py','record_t4_adaptive_v3.py'):
            archive.writestr(prefix+name,(phase/name).read_bytes())
    with zipfile.ZipFile(parent/'progress.zip') as before,zipfile.ZipFile(package) as after:
        assert len(after.namelist())==len(set(after.namelist()))
        for name in before.namelist():assert hashlib.sha256(before.read(name)).digest()==hashlib.sha256(after.read(name)).digest(),name
    for kind in ('state','chat'):
        doc=json.loads((parent/(kind+'.json')).read_bytes())
        doc.setdefault('full_text_training_execution_history',[]).append(dict(previous=doc['current_full_text_training_run'],new_execution_record=record))
        doc.update(current_full_text_training_run=run,last_verified_training_checkpoint=runtime['last_verified_checkpoint'],training_started=True,whole_training_epoch_completed=False)
        if kind=='state':doc['updated_utc']=now
        (out/('next_'+kind+'.json')).write_text(json.dumps(doc,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8')
    journal=(f'\n\n### Nhật ký 23/10/2026 — batch linh hoạt V3 dùng thêm VRAM\n'
      f'Mốc {now}; quan sát {runtime["observed_utc"]}: step={runtime["step"]},rows={runtime["rows_done"]}/6502344,worker_alive=true. '
      f'Cap physical batch={opt["physical_microbatch"]},budget padded token={opt["padded_token_budget"]},speedup so V2 cùng nhóm đo={opt.get("measured_speedup",1):.5f}x. '
      'Sort chỉ trong group16,chiachunk theođộdài thực,cânlosschunklen/groupcount giữ equal-examplemean; khôngcắtinput/target/EOT,khôngđổiepoch/LR/recipe/splits. '
      '9CPUtests pass; GPUprobe khôngoptimizerupdates,phục hồiRNG/weights/scaler; memory stress cho cácshape khảthi,OOMretry cùnggroupkhôngackrows. '
      'Tốcđộ mộtgroup khôngbảođảmtốcđộtoàncorpus haychấtlượng; dùng nhiềuVRAMkhôngtựtăngtríthôngminh. '
      f'Checkpoint preprobe ID{opt["checkpoint_before"]["id"]},step{opt["checkpoint_before"]["step"]},SHA{opt["checkpoint_before"]["sha256"]},freshrawreadback=true. '
      'Thêmoverlaypinriêng,giữ tất cảmembernguồn/release/config/auditfrozen cũ. '
      'TEXT_TRAINING_DATASET_READY=true theo phạmvivăn bản;TRAINING_DATASET_READY toànchươngtrình=false,visual/thựchànhpending;epoch chưahoàntất.\n').encode()
    (out/'next_context.md').write_bytes((parent/'context.md').read_bytes()+journal)
    ids={'progress':'1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX','chat':'1tkSQoAlxXXRUg2AwYfvqsFKVEmM_LmR6','context':'13gdIPQTFKcekoQQtgo0TXc7RgeadzIN9','state':'1TLoQIbrRVmgsg-2uiUujCfM3HrK62Yme'}
    pins={}
    for kind,fid in ids.items():
        ext='.zip' if kind=='progress' else '.md' if kind=='context' else '.json';file=out/('next_'+kind+ext);b=file.read_bytes()
        pins[kind]=dict(id=fid,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),path=str(file.resolve()))
    (out/'prepared_pins.json').write_text(json.dumps(pins,indent=2))
    print(json.dumps(dict(controls=pins,launcher=launcher)))

if __name__=='__main__':main(*sys.argv[1:])
