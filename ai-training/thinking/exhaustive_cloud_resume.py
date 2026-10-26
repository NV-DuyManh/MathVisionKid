"""One bounded immutable cloud shard, verify, checkpoint, cleanup. No bulk init.

The connector orchestrator supplies actual upload IDs and fresh raw SHA receipts.
Generation and checkpoint transitions are deterministic and testable offline.
Only one manager may own this local publisher; Colab uses the same explicit lock.
"""
from __future__ import annotations
import argparse,gzip,hashlib,io,json,os,shutil,socket,zipfile
from collections import Counter
from contextlib import contextmanager,ExitStack
from datetime import datetime,timezone
from itertools import islice
from pathlib import Path
import exhaustive_multidigit_math as arithmetic
import exhaustive_primary_math as base

HERE=Path(__file__).resolve().parent
RUN=HERE/'cloud_publication/resume_20261018'
TEMP=RUN/'temporary_shard'
META=RUN/'metadata'
STATE=RUN/'working_cloud_state.json'
MAX_TEMP_BYTES=40*1024*1024
VERSION='exhaustive_cloud_resume.v1'

def utc():return datetime.now(timezone.utc).isoformat()
def dumps(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def digest(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf-8'))
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 t=p.with_suffix(p.suffix+'.writing');t.write_text(dumps(x)+'\n','utf-8');t.replace(p)
def filehash(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def configure_sources():
 s=arithmetic.scope_module
 for k in ('EVIDENCE_PATH','ANNEX_PATH'):
  original=getattr(s,k)
  marker='thinking/evidence/'
  # A long-lived process can configure more than once. The last marker is the
  # original evidence path; the first may be inside our metadata prefix.
  original=original[original.rindex(marker):]
  setattr(s,k,(META/original).relative_to(HERE.parent).as_posix())
 s.verify_source_evidence.cache_clear();s.verify_source_evidence()
def protected():return set(read(META/'thinking/data/exhaustive_math_v1/protected_numeric_signatures.json')['signatures'])

def domain_specs():
 specs=arithmetic.finite_domain_specs(maximum=100,dividend_maximum=100)
 return specs
def spec_id(s):return s.get('domain_id',s.get('domain',s.get('name')))
def normalize_specs():
 return [{**s,'cloud_domain_id':spec_id(s) or digest(dumps(s).encode())[:20]} for s in domain_specs()]
def init_reference():
 # This initializes only tiny reference metadata, never a replacement corpus.
 if STATE.exists():return read(STATE)
 old=read(RUN/'source_cloud_state.json')
 assert len(old['parts'])==14 and all(p.get('sha256') for p in old['parts'])
 if old.get('resume_version'):
  assert old['resume_version']==VERSION and isinstance(old.get('extension_shards'),list)
  assert isinstance(old.get('extension_domains'),dict)
  # A fresh Colab/runtime must restore the authoritative remote cursors. Never
  # clear a committed extension when its local reference directory is absent.
  for d in old['extension_domains'].values():
   assert d['cursor']==d['validated_pairs']==d['generated_pairs']
   assert d['missing_pairs']==d['expected_pairs']-d['validated_pairs']>=0
  save(STATE,old);return old
 assert old['accepted_cases']==1519171,'Unknown remote schema: inspect before creating extension metadata'
 old['resume_version']=VERSION;old['extension_shards']=[];old['extension_domains']={}
 old['storage_preflight']={'checked_utc':utc(),'drive_quota_available':False,'quota_bytes':None,'used_bytes':None,'remaining_bytes':None,
  'reason':'Current Drive connector exposes profile/file metadata but no about.storageQuota endpoint. Never infer free space from successful small uploads.',
  'max_temporary_shard_bytes':MAX_TEMP_BYTES,'max_connector_file_bytes':104857600,'large_domains':'BLOCKED_STORAGE_CAPACITY_UNVERIFIED',
  'bounded_phase':'Only small finite teaching domains, one shard at a time. Stop on quota/upload error; no checkpoint advancement.'}
 for s in normalize_specs():
  key=s['cloud_domain_id'];n=sum(1 for _ in arithmetic.iter_domain_pairs(s))
  old['extension_domains'][key]={'spec':s,'expected_pairs':n,'generated_pairs':0,'validated_pairs':0,'missing_pairs':n,'cursor':0,'status':'NOT_STARTED','EXHAUSTIVE_DOMAIN_COMPLETED':False}
 old['TRAINING_DATASET_READY']=False;old['all_requested_exhaustive_domains_completed']=False
 save(STATE,old);return old

@contextmanager
def manager_lock():
 RUN.mkdir(parents=True,exist_ok=True);p=RUN/'publisher.lock'
 try:fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
 except FileExistsError:raise RuntimeError('Publisher lock exists; inspect its PID/host before recovery. Do not start another manager.')
 os.write(fd,dumps({'pid':os.getpid(),'host':socket.gethostname(),'utc':utc()}).encode());os.close(fd)
 try:yield
 finally:p.unlink()

def gzwrite(path,rows):
 with Path(path).open('wb') as f:
  with gzip.GzipFile(filename='',mode='wb',fileobj=f,mtime=0,compresslevel=6) as g:
   for r in rows:g.write((dumps(r)+'\n').encode())
def gzrows(path):
 with gzip.open(path,'rt',encoding='utf-8') as f:
  for line in f:yield json.loads(line)

def deterministic_bundle(path,members):
 # ZipFile.write inherits wall-clock filesystem mtimes, permissions and host OS.
 # A retry must reproduce the same content-addressed name on every platform.
 with zipfile.ZipFile(path,'w',zipfile.ZIP_STORED) as z:
  for member in members:
   info=zipfile.ZipInfo(member.name,date_time=(1980,1,1,0,0,0))
   info.create_system=3;info.external_attr=0o100644<<16
   with member.open('rb') as src,z.open(info,'w') as dst:
    shutil.copyfileobj(src,dst,length=1024*1024)

def candidate_receipt():
 p=RUN/'next_cloud_state.json'
 return {'path':str(p),'sha256':filehash(p),'bytes':p.stat().st_size}

def exclusion_reason(row,signatures,holdout):
 sig=set(row['canonical_signatures'])
 return 'protected_numeric' if sig&signatures else 'selected_holdout' if sig&holdout else 'regression_only' if row.get('split')=='regression_only' else None

def remove_temporary_payload():
 resolved=TEMP.resolve()
 assert resolved==(RUN/'temporary_shard').resolve() and resolved.is_relative_to(RUN.resolve())
 if resolved.exists():shutil.rmtree(resolved)

def prepare(limit=5000):
 if not 1<=limit<=10000:raise ValueError('Bounded shard limit must be1..10000cases')
 state=init_reference()
 if (TEMP/'manifest.json').exists():
  manifest=read(TEMP/'manifest.json')
  # A failed upload resumes the same content, never advances or overwrites it.
  if manifest['parent_state_sha256']!=filehash(STATE):
   candidate=RUN/'next_cloud_state.json'
   if candidate.exists() and filehash(candidate)==filehash(STATE):
    raise RuntimeError('Checkpoint is already local; finish finalize-commit cleanup before preparing another shard.')
   raise AssertionError('Prepared shard parent checkpoint changed; no payload overwritten.')
  for k in ('source','view','bundle'):assert filehash(TEMP/manifest[k]['name'])==manifest[k]['sha256']
  return manifest
 configure_sources()
 # JSON canonicalization sorts keys; use the same explicit ordering both on
 # the freshly initialized object and after it has been read back from disk.
 target=next((state['extension_domains'][k] for k in sorted(state['extension_domains']) if state['extension_domains'][k]['missing_pairs']),None)
 if target is None:return {'phase_complete':True}
 s=target['spec'];start=target['cursor'];pairs=list(islice(arithmetic.iter_domain_pairs(s),start,start+limit))
 assert pairs and len(set(pairs))==len(pairs)
 key=s['cloud_domain_id'];end=start+len(pairs)
 shard_id=f'{key}__{start:09d}_{end:09d}'
 TEMP.mkdir(parents=True,exist_ok=False)
 signatures=protected();holdout_file=RUN/'holdout_signatures.json'
 holdout=set(read(holdout_file).get('signatures',[])) if holdout_file.exists() else set()
 exclusions=Counter();grades=Counter();topics=Counter();source=TEMP/'source.jsonl.gz';view=TEMP/'chat.jsonl.gz'
 pairhash=hashlib.sha256();selected=[];source_ids=set();chat_count=0
 try:
  # Stream one worked example and its four modes at a time; no shard-sized
  # source/chat lists. The pair/ID indexes are capped at 10,000 small entries.
  with ExitStack() as stack:
   handles=[stack.enter_context(p.open('wb')) for p in (source,view)]
   writers=[stack.enter_context(gzip.GzipFile(filename='',mode='wb',fileobj=f,mtime=0,compresslevel=6)) for f in handles]
   for a,b in pairs:
    row=arithmetic.make_row(s['operation'],a,b);arithmetic.validate_row(row)
    # The neutral serializer embeds JSON in message text. Canonicalize before
    # serializing both views so regenerated messages match reopened source.
    row=json.loads(dumps(row))
    assert row['sample_id'] not in source_ids;source_ids.add(row['sample_id'])
    pairhash.update((dumps([a,b])+'\n').encode());grades[str(row['grade'])]+=1;topics[row['topic']]+=1
    writers[0].write((dumps(row)+'\n').encode())
    reason=exclusion_reason(row,signatures,holdout)
    if reason:exclusions[reason]+=1
    else:
     modes=0
     for record in arithmetic.chat_records(row):writers[1].write((dumps(record)+'\n').encode());modes+=1
     assert modes==4;chat_count+=modes
     if len(selected)<32 and int(digest(row['sample_id'].encode())[:8],16)%97==0:selected.append(row)
    # ZIP_STORED duplicates these gzipped members; leave room for all bounded
    # gzip buffers, selected examples and the manifests before writing the ZIP.
    if 2*sum(f.tell() for f in handles)+1024*1024>=MAX_TEMP_BYTES:
     raise ValueError('Temporary shard budget reached; retry with a smaller --limit. Checkpoint is unchanged.')
 except BaseException:
  remove_temporary_payload();raise
 for actual,pair in zip(gzrows(source),pairs,strict=True):
  assert actual['sample_id']==base.make_id(s['operation'],*pair);arithmetic.validate_row(actual)
 assert sum(1 for _ in gzrows(source))==len(pairs)
 actual_chat=iter(gzrows(view));reopened_chat=0
 try:
  for row in gzrows(source):
   if exclusion_reason(row,signatures,holdout):continue
   for expected in arithmetic.chat_records(row):assert next(actual_chat)==expected;reopened_chat+=1
  assert next(actual_chat,None) is None and reopened_chat==chat_count==4*(len(pairs)-sum(exclusions.values()))
 finally:actual_chat.close()
 assert len(source_ids)==len(pairs)
 manifest={'schema_version':VERSION,'shard_id':shard_id,'cloud_domain_id':key,'operation':s['operation'],'start':start,'stop':end,'cases':len(pairs),'validated_pairs':len(pairs),
  'chat_rows':chat_count,'excluded_cases':dict(exclusions),'grades':dict(grades),'topics':dict(topics),
  'ordered_pair_sequence_sha256':pairhash.hexdigest(),'pair_validation':'Every reopened ordered pair, sourceID, trace and independent oracle checked; no overlap with preexisting ranges by finite domain specification.',
  'protected_index_sha256':filehash(META/'thinking/data/exhaustive_math_v1/protected_numeric_signatures.json'),
  'holdout_index_sha256':filehash(holdout_file) if holdout_file.exists() else None,
  'template_sha256':arithmetic.template_fingerprint(),'parent_state_sha256':filehash(STATE),'status':'PREPARED_NOT_COMMITTED',
  'source':{'name':source.name,'bytes':source.stat().st_size,'sha256':filehash(source)},'view':{'name':view.name,'bytes':view.stat().st_size,'sha256':filehash(view)}}
 save(TEMP/'manifest_payload.json',manifest)
 gzwrite(TEMP/'selected_cases.jsonl.gz',selected)
 bundle=TEMP/(shard_id+'.zip')
 deterministic_bundle(bundle,(source,view,TEMP/'manifest_payload.json'))
 manifest['bundle']={'name':bundle.name,'bytes':bundle.stat().st_size,'sha256':filehash(bundle)}
 manifest['remote_name']='MVK_'+shard_id+'_'+manifest['bundle']['sha256'][:16]+'.zip'
 assert sum(p.stat().st_size for p in TEMP.iterdir())<MAX_TEMP_BYTES,'Temporary shard budget exceeded; no upload or checkpoint occurred'
 save(TEMP/'manifest.json',manifest)
 save(RUN/'next_upload.json',{'shard_id':shard_id,'path':str(bundle),'name':manifest['remote_name'],'bytes':bundle.stat().st_size,'sha256':filehash(bundle),'mime_type':'application/zip'})
 return manifest

def stage_commit(proof_path):
 m=read(TEMP/'manifest.json');proof=read(proof_path);state=read(STATE)
 assert proof['fresh_raw_verified'] and proof['all_bytes_equal'] and proof['sha256']==m['bundle']['sha256'] and proof['bytes']==m['bundle']['bytes']
 assert proof.get('file_id') and proof.get('verified_utc')
 candidate=RUN/'next_cloud_state.json'
 if candidate.exists():
  staged=read(candidate)
  matching=[r for r in staged.get('extension_shards',[]) if r['shard_id']==m['shard_id']]
  if matching:
   r=matching[0]
   assert r['bundle']==m['bundle'] and r['file_id']==proof['file_id']
   assert staged['extension_shards'][-1]['shard_id']==m['shard_id']
   assert filehash(STATE) in (m['parent_state_sha256'],filehash(candidate))
   # Keep the original timestamp and raw receipt. A later verification can
   # confirm it, but must not change bytes already published as a checkpoint.
   return candidate_receipt()
 assert m['parent_state_sha256']==filehash(STATE)
 assert not any(c['shard_id']==m['shard_id'] for c in state['extension_shards'])
 d=state['extension_domains'][m['cloud_domain_id']];assert d['cursor']==m['start']
 record={k:v for k,v in m.items() if k not in ('parent_state_sha256','status')};record['file_id']=proof['file_id'];record['fresh_raw_verification']=proof
 state['extension_shards'].append(record);d['cursor']=m['stop'];d['generated_pairs']+=m['cases'];d['validated_pairs']+=m['validated_pairs'];d['missing_pairs']=d['expected_pairs']-d['validated_pairs']
 assert d['missing_pairs']>=0
 d['status']='COMPLETED' if not d['missing_pairs'] else 'IN_PROGRESS';d['EXHAUSTIVE_DOMAIN_COMPLETED']=not d['missing_pairs']
 state['accepted_cases']+=m['cases'];state['new_cases']+=m['cases'];state['training_chat_rows']+=m['chat_rows'];state['updated_utc']=utc();state['status']='CLOUD_RESUME_VERIFIED_SHARDS'
 state['next_action']='Upload this checkpoint to existing stateID, fresh-read verify it, then finalize local cleanup. No new shard before that succeeds.'
 save(RUN/'next_cloud_state.json',state)
 return candidate_receipt()

def finalize_commit(checkpoint_proof_path):
 p=read(checkpoint_proof_path);candidate=RUN/'next_cloud_state.json'
 assert p['fresh_raw_verified'] and p['all_bytes_equal'] and p['sha256']==filehash(candidate) and p['bytes']==candidate.stat().st_size
 assert p['file_id']=='1TLoQIbrRVmgsg-2uiUujCfM3HrK62Yme'
 state=read(candidate)
 shard_id=state['extension_shards'][-1]['shard_id']
 commit_path=RUN/'commits'/f'{shard_id}.json'
 if not (TEMP/'manifest.json').exists():
  assert commit_path.exists() and filehash(STATE)==filehash(candidate)
  prior_commit=read(commit_path);m=prior_commit['manifest']
  assert m['shard_id']==shard_id
  if TEMP.exists():
   resolved=TEMP.resolve();assert resolved==(RUN/'temporary_shard').resolve() and resolved.is_relative_to(RUN.resolve())
   shutil.rmtree(resolved)
  return {'committed':shard_id,'cases':m['cases'],'chat_rows':m['chat_rows'],'temporary_bytes_removed':0,'already_committed':True}
 m=read(TEMP/'manifest.json')
 assert state['extension_shards'][-1]['shard_id']==m['shard_id']
 assert filehash(STATE) in (m['parent_state_sha256'],filehash(candidate))
 # Keep bounded selected teaching examples only until the balanced release is published.
 selected=list(gzrows(TEMP/'selected_cases.jsonl.gz'))
 selected_path=RUN/'selected_arithmetic_cases.jsonl'
 prior=[]
 if selected_path.exists():prior=[json.loads(l) for l in selected_path.read_text('utf-8').splitlines()]
 byid={r['sample_id']:r for r in prior+selected}
 selected_temp=selected_path.with_suffix('.writing')
 selected_temp.write_text(''.join(dumps(r)+'\n' for r in byid.values()),'utf-8');selected_temp.replace(selected_path)
 chat_path=RUN/'selected_arithmetic_chat.jsonl'
 chat_temp=chat_path.with_suffix('.writing')
 chat_temp.write_text(''.join(dumps(c)+'\n' for r in byid.values() for c in arithmetic.chat_records(r)),'utf-8');chat_temp.replace(chat_path)
 # Journal before the atomic local checkpoint; an interruption during cleanup
 # can now be replayed even after temporary_shard/manifest.json was removed.
 save(commit_path,{'manifest':m,'checkpoint_receipt':p})
 save(STATE,state)
 resolved=TEMP.resolve();assert resolved== (RUN/'temporary_shard').resolve() and resolved.is_relative_to(RUN.resolve())
 removed=sum(f.stat().st_size for f in resolved.iterdir() if f.is_file());shutil.rmtree(resolved)
 return {'committed':m['shard_id'],'cases':m['cases'],'chat_rows':m['chat_rows'],'temporary_bytes_removed':removed}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','stage-commit','finalize-commit','state']);p.add_argument('--limit',type=int,default=5000);p.add_argument('--proof');a=p.parse_args()
 with manager_lock():
  if a.action=='prepare':result=prepare(a.limit)
  elif a.action=='stage-commit':result=stage_commit(a.proof)
  elif a.action=='finalize-commit':result=finalize_commit(a.proof)
  else:result=init_reference()
 print(dumps(result))
