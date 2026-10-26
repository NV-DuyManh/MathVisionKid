"""Record verified branch observations; does not claim Drive control synchronization."""
from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parents[3]
phase=Path(__file__).resolve().parent
receipt=json.loads((phase/'budget_status_latest.json').read_bytes())
data=receipt.get('structured_content') or receipt.get('data')
observation=json.loads(''.join(t for o in data['outputs'] for t in o.get('text',[])))
training=observation['training/progress.json'];config=observation['training/run_config.json']
publication=observation['drive_publication/publication_status.json'];checkpoint=publication['last_checkpoint']
assert training['state']=='TRAINING' and training['step']>=100
assert checkpoint['fresh_raw_readback_verified'] and checkpoint['rows_done']==16*checkpoint['step']
assert config['target_steps']==734 and config['view_rows']==16000
record={'observed_utc':observation['observed_utc'],'training':training,'config':config,'checkpoint':checkpoint,
 'folder_id':publication['folder_id'],'whole_corpus_epoch_complete':False,'training_view_cases':4000,
 'training_view_rows':16000,'drive_four_controls_pending_sync':True,'last_verified_four_controls_proof':'four_controls_branch_preparation_verified.json',
 'connector_state':'Google Drive plugin not installed in current chat account; Colab authenticated Drive publisher is working',
 'local_temp_cleanup':'automatic policy rejected deletion; inspected temporary controls retained; no corpus/model staged on PC'}
(phase/'training_started_milestone.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
context=root/'MATH_TRAINING_CONTEXT.md';raw=context.read_bytes()
marker='### Nhật ký 23/10/2026 — nhánh 3 giờ đã cập nhật optimizer và checkpoint'
if marker.encode() not in raw:
 journal=(f'\n\n{marker}\nQuan sát {record["observed_utc"]}: step={training["step"]}, rows={training["rows_done"]}, supervised_tokens={training["supervised_tokens"]}; '
 f'Unsloth2026.10.7 trênT4, exactQwen3 revision70d244cc86ccca08cf5af4e1e306ecf908b1ad5e; NF4/FP16/r16/AdamW8bit, microbatch2, accumulation8. '
 'Fullscan 6502344train+24validation+24test/32chatmembers, chỉ dùngtrain; view4000case/16000chat, SHA14929ba64e5c94d812f1fc3804c771ca8e41fa92285aed3a925282c39b1e4331; '
 'manifestSHA444db8845af0c12bb528795b7e441b996571960dd58ab6898eb9394c77031545, seed20261023, rawrowSHA+sampleID bindexact, khôngcắtinput/assistant. '
 'Same16 lengthquantile benchmark TorchCE micro2=7.632730s/group, Unslothmicro2=4.931099s/group (1.547876x), chưaoptimizerupdate trongbenchmark; '
 'target734updates tính từngânsách đo4.931099s×1.35, dành1500s eval/export, deadline2026-10-23T17:15:52Z; khôngtuyênbốfullcorpus. '
 f'CPstep{checkpoint["step"]}/rows{checkpoint["rows_done"]} ID{checkpoint["id"]}, bytes{checkpoint["bytes"]}, SHA{checkpoint["sha256"]}, freshrawreadback=true. '
 f'Folder{publication["folder_id"]}; modelcũstep1056/16896giữriêng. Base28outputsđãlưu; semantics LLMreview khônghumanattestation; finaladapterevalpending. '
 'Driveconnectorhiệnkhôngcàiởtàikhoảnchatmới; Colabpublisher vẫnhoạtđộng, bốncontrolIDs chưasyncmốc mới này. Khoảng75MBcontroltạmPCchưaxóađượcdoautomaticpolicyrejected; khôngcorpus/modelPC.\n').encode('utf8')
 context.write_bytes(raw+journal)
registry=root/'thinking/data/primary_math_teacher_20261016/drive_artifacts.json';doc=json.loads(registry.read_bytes())
doc['latest_t4_budget3h_runtime']=record
registry.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'recorded':True,'observed_utc':record['observed_utc'],'step':training['step'],'checkpoint_verified_step':checkpoint['step'],'four_controls_sync_claimed':False}))
