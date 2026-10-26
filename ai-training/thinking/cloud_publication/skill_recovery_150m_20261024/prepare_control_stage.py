"""Build, but do not execute, one explicit CPU-thread four-control publication.

Inputs are caller-supplied canonical context bytes, run metadata and an explicit
code/metadata evidence map. No context file is edited; no Drive call occurs here.
"""
from __future__ import annotations
import argparse,base64,gzip,hashlib,importlib.util,json
from pathlib import Path,PurePosixPath

MAX_FILE=2*1024*1024
MAX_PAYLOAD=8*1024*1024
DEFAULT_RUNTIME_ROOT='/content/mathvisionkid_skill_recovery_150m_20261024'


def sha(data):return hashlib.sha256(data).hexdigest()


def read_object(data):
 def pairs(items):
  result={}
  for key,value in items:
   if key in result:raise ValueError('duplicate metadata key: '+key)
   result[key]=value
  return result
 value=json.loads(data.decode('utf-8'),object_pairs_hook=pairs,
                  parse_constant=lambda value:(_ for _ in ()).throw(ValueError('nonfinite JSON metadata')))
 if not isinstance(value,dict):raise ValueError('explicit metadata object required')
 return value


def build_stage(canonical_context_bytes,run_metadata,evidence_paths,output_script,*,
                runtime_root=DEFAULT_RUNTIME_ROOT,credentials_global='recovery_credentials',
                process_global='recovery_process',min_request_interval=1.25):
 """Return local stage-file pins. Caller executes the generated script later."""
 if not isinstance(canonical_context_bytes,bytes) or len(canonical_context_bytes)>MAX_FILE:
  raise ValueError('bounded canonical context bytes required')
 canonical_context_bytes.decode('utf-8')
 if not isinstance(run_metadata,dict):raise ValueError('run metadata object required')
 metadata_bytes=(json.dumps(run_metadata,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf-8')
 if len(metadata_bytes)>MAX_FILE:raise ValueError('run metadata exceeds bound')
 if not credentials_global.isidentifier() or not process_global.isidentifier():raise ValueError('not a Python global identifier')
 if not 0<=min_request_interval<=10:raise ValueError('invalid request throttle interval')
 runtime=PurePosixPath(runtime_root)
 if not runtime.is_absolute() or '..' in runtime.parts:raise ValueError('absolute explicit runtime root required')
 here=Path(__file__).resolve().parent
 sources={name:here/name for name in ('prepare_four_controls_runtime.py','four_controls_transaction.py','prepare_control_stage.py')}
 for name,path in evidence_paths.items():
  rel=PurePosixPath(name)
  if not name or rel.is_absolute() or '..' in rel.parts or '\\' in name or rel.as_posix()!=name:
   raise ValueError('unsafe archive-relative evidence path: '+name)
  if name in sources:raise ValueError('evidence cannot replace publication helper: '+name)
  sources[name]=Path(path).resolve(strict=True)
 payload={};hashes={};total=0
 for name,path in sorted(sources.items()):
  if path.suffix.lower() not in ('.py','.json','.md','.txt') or path.stat().st_size>MAX_FILE:
   raise ValueError('evidence must be bounded code/metadata: '+name)
  raw=path.read_bytes();raw.decode('utf-8')
  if path.suffix.lower()=='.json':read_object(raw)
  total+=len(raw)
  if total>MAX_PAYLOAD:raise ValueError('bounded evidence payload exceeded')
  payload[name]=base64.b64encode(raw).decode('ascii');hashes[name]=sha(raw)
 metadata_sha=sha(metadata_bytes);context_sha=sha(canonical_context_bytes)
 code=RUNTIME_TEMPLATE.replace('__PAYLOAD__',repr(payload)).replace('__HASHES__',repr(hashes))
 code=code.replace('__CONTEXT64__',repr(base64.b64encode(gzip.compress(canonical_context_bytes,mtime=0)).decode('ascii')))
 code=code.replace('__CONTEXT_SHA__',repr(context_sha)).replace('__RUN_METADATA__',repr(run_metadata))
 code=code.replace('__METADATA_SHA__',repr(metadata_sha)).replace('__RUNTIME_ROOT__',repr(str(runtime)))
 code=code.replace('__CREDENTIALS_GLOBAL__',repr(credentials_global)).replace('__PROCESS_GLOBAL__',repr(process_global))
 code=code.replace('__INTERVAL__',repr(float(min_request_interval)))
 compile(code,'generated_four_control_stage','exec')
 output=Path(output_script).resolve()
 if output.exists():raise FileExistsError('retain prior stage; use a fresh output-script path')
 output.parent.mkdir(parents=True,exist_ok=True)
 output.write_text(code,encoding='utf-8')
 return {'path':str(output),'bytes':output.stat().st_size,'sha256':sha(output.read_bytes()),
         'canonical_context_sha256':context_sha,'run_metadata_sha256':metadata_sha,
         'runtime_root':str(runtime),'source_hashes':hashes,'stage_executed':False,'drive_calls_made':False}


RUNTIME_TEMPLATE=r'''import pathlib,json,base64,gzip,hashlib,importlib.util,sys,threading,traceback
from datetime import datetime,timezone
assert not globals().get('recovery_controls_thread') or not recovery_controls_thread.is_alive(),'Control publication already active.'
qrec_control_root=pathlib.Path(__RUNTIME_ROOT__)
qrec_control_payload=__PAYLOAD__
qrec_control_hashes=__HASHES__
qrec_control_credentials_name=__CREDENTIALS_GLOBAL__
qrec_control_process_name=__PROCESS_GLOBAL__
qrec_control_run_metadata=__RUN_METADATA__
qrec_control_context=gzip.decompress(base64.b64decode(__CONTEXT64__))
assert hashlib.sha256(qrec_control_context).hexdigest()==__CONTEXT_SHA__
assert qrec_control_root.is_dir(),'Runtime root must already exist; this script does not launch training.'
assert qrec_control_credentials_name in globals(),'Explicit authenticated credentials global is missing.'
assert qrec_control_process_name in globals(),'Actual worker process global is missing; do not invent an observation.'
for qrec_name,qrec_encoded in qrec_control_payload.items():
 qrec_data=base64.b64decode(qrec_encoded);assert hashlib.sha256(qrec_data).hexdigest()==qrec_control_hashes[qrec_name]
 qrec_path=qrec_control_root/qrec_name;qrec_path.parent.mkdir(parents=True,exist_ok=True)
 if qrec_path.exists():assert qrec_path.read_bytes()==qrec_data,'Existing evidence differs: '+qrec_name
 else:qrec_path.write_bytes(qrec_data)
qrec_context_path=qrec_control_root/('canonical_context_'+__CONTEXT_SHA__+'.md')
if qrec_context_path.exists():assert qrec_context_path.read_bytes()==qrec_control_context
else:qrec_context_path.write_bytes(qrec_control_context)
def qrec_load_control(name):
 spec=importlib.util.spec_from_file_location('quality_recovery_'+name,qrec_control_root/(name+'.py'))
 mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod);return mod
qrec_prepare_controls=qrec_load_control('prepare_four_controls_runtime')
qrec_control_transaction=qrec_load_control('four_controls_transaction')
def _publish_quality_recovery_controls():
 status_path=qrec_control_root/'four_controls_publication_status.json'
 def status(value):
  tmp=status_path.with_suffix('.pending');tmp.write_bytes(qrec_prepare_controls.json_bytes(value));tmp.replace(status_path)
 work=qrec_control_root/'four_controls_publication'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
 try:
  status({'state':'READING_PARENTS','work':str(work),'branch':'skill_recovery_150m_20261024'})
  credentials=globals()[qrec_control_credentials_name]
  parents=qrec_control_transaction.download_current_parents_with_credentials(credentials,qrec_prepare_controls.IDS,work/'parents',min_request_interval=__INTERVAL__)
  process=globals()[qrec_control_process_name]
  exit_code=process.poll()
  observed={'observed_utc':datetime.now(timezone.utc).isoformat(),'worker_alive':exit_code is None,'worker_exit':exit_code,'pid':process.pid}
  actual=qrec_prepare_controls.capture_branch_metadata(qrec_control_root,worker_observation=observed)
  evidence={name:qrec_control_root/name for name in qrec_control_payload}
  prepared=qrec_prepare_controls.prepare_controls(parents,qrec_control_context,actual,evidence,work/'prepared',run_metadata=qrec_control_run_metadata)
  assert prepared['run_metadata_sha256']==__METADATA_SHA__
  status({'state':'PREPARED','work':str(work),'observation':actual,'controls':prepared['controls']})
  receipt=qrec_control_transaction.publish_with_credentials(credentials,prepared['parents'],prepared['controls'],work,receipt_path=work/'four_controls_raw_verified.json',min_request_interval=__INTERVAL__)
  assert [item['kind'] for item in receipt['verified_writes']]==['progress','chat','context','state']
  assert all(item['fresh_raw_readback_verified'] for item in receipt['verified_writes'])
  (qrec_control_root/'four_controls_verified_manifest.json').write_bytes(qrec_prepare_controls.json_bytes(receipt))
  status({'state':'COMPLETE_RAW_VERIFIED','work':str(work),'receipt':receipt,'canonical_context_sha256':__CONTEXT_SHA__,'run_metadata_sha256':__METADATA_SHA__})
 except Exception as error:
  status({'state':'ERROR','work':str(work),'error':repr(error),'traceback':traceback.format_exc()})
recovery_controls_thread=threading.Thread(target=_publish_quality_recovery_controls,name='MathVisionKidSkillRecoveryFourControls',daemon=True)
recovery_controls_thread.start()
print(json.dumps({'controls_thread_started':True,'canonical_context_sha256':__CONTEXT_SHA__,'run_metadata_sha256':__METADATA_SHA__,'data_or_weights_changed':False}))
'''


def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--context',type=Path,required=True,help='Read-only canonical MATH_TRAINING_CONTEXT.md input')
 parser.add_argument('--run-metadata',type=Path,required=True,help='Explicit JSON object describing this run/phase')
 parser.add_argument('--evidence-map',type=Path,help='JSON object: archive-relative name -> explicit local code/metadata path')
 parser.add_argument('--output-script',type=Path,required=True,help='Fresh local output; later execute explicitly in Colab')
 parser.add_argument('--runtime-root',default=DEFAULT_RUNTIME_ROOT)
 parser.add_argument('--credentials-global',default='recovery_credentials')
 parser.add_argument('--process-global',default='recovery_process')
 parser.add_argument('--min-request-interval',type=float,default=1.25)
 args=parser.parse_args()
 evidence=read_object(args.evidence_map.read_bytes()) if args.evidence_map else {}
 result=build_stage(args.context.read_bytes(),read_object(args.run_metadata.read_bytes()),evidence,args.output_script,
                    runtime_root=args.runtime_root,credentials_global=args.credentials_global,
                    process_global=args.process_global,min_request_interval=args.min_request_interval)
 print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
