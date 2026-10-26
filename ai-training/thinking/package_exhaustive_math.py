"""Publish additive corpus without rewriting baseline sources or reducing corpus."""
import hashlib,json,shutil,sys,time,zipfile
from pathlib import Path
from collections import Counter
import exhaustive_primary_math as e
PROJECT=e.HERE.parent
BASE=e.HERE/'data/primary_math_teacher_20261016'
OUT=e.HERE/'evidence/primary_math_teacher_20261016/Primary_Math_Teacher_20261016_PROGRESS.zip'
SNAP=e.EVIDENCE/'snapshot/finite495_70071b60a78412b4/Primary_Math_Teacher_20261016_PROGRESS.zip'
def relative(p):return p.relative_to(PROJECT).as_posix()
def index():
 state=e.load(e.ROOT/'data_build_state.json')
 assert state['new_generated_cases']==1513633
 assert all(d['status']=='COMPLETED' for d in state['physical_shells'].values())
 sources=[e.load(p) for p in sorted((e.ROOT/'corpus').rglob('*.manifest.json'))]
 views=[e.load(p) for p in sorted((e.ROOT/'training_views').rglob('*.manifest.json'))]
 assert len(views)==len(sources)
 assert sum(x['source_cases'] for x in views)==1513633
 for m in sources+views:assert e.filehash(e.ROOT/m['path'])==m['sha256'],m['path']
 # Structural/fraction/decimal extensions retain their own generation policies
 # and explicit file sets. The integration receipt is written after their QA.
 extra=e.load(e.ROOT/'extension_integration.json')
 for group in extra['datasets']:
  for f in group['files']:assert e.filehash(PROJECT/f['path'])==f['sha256']
 extra_cases=sum(d['cases'] for d in extra['datasets']);extra_chat=sum(d['chat_rows'] for d in extra['datasets'])
 baseline=e.load(BASE/'data_build_state.json');assert baseline['accepted_cases']==782
 assert e.filehash(SNAP)=='70071b60a78412b4d8709959414be795d2076fb9d7f71d4547a247e8e714217a'
 registry={'schema_version':'mathvisionkid.full_corpus_and_views.v1','updated_utc':e.utc(),'status':'FIRST_EXHAUSTIVE_STAGE_COMPLETED_LARGER_SCOPE_IN_PROGRESS','accepted_cases':782+state['new_validated_accepted_cases']+extra_cases,'baseline_accepted_cases':782,'baseline_chat_rows':3128,'new_arithmetic_cases':state['new_validated_accepted_cases'],'new_other_cases':extra_cases,'chat_train_rows':3128+state['new_materialized_chat_rows']+extra_chat,'new_arithmetic_chat_rows':state['new_materialized_chat_rows'],'new_other_chat_rows':extra_chat,'new_all_validated_cases_preserved':state['new_validated_accepted_cases']+extra_cases,'protected_arithmetic_cases_excluded_from_new_view_but_preserved':state['protected_overlap_cases_preserved_outside_new_training_view'],'legacy_core_cases':495,'legacy_core_nodes_complete':165,'legacy_owner299_signoffs_unchanged':True,'new_automatic_acceptance_is_not_completed_human_review':True,'no_quality_penalty_based_on_origin':True,'model_training_started':False,'all_requested_large_domains_completed':False,'logical_domains':state['logical_domains'],'arithmetic_source_shards':sources,'arithmetic_training_view_shards':views,'extensions':extra,'baseline_references':{'full_snapshot':relative(SNAP),'source_registry':relative(e.EVIDENCE/'preservation_primary_inventory.json'),'other_existing_corpora_metadata_registry':relative(e.EVIDENCE/'preservation_other_corpora_metadata_hashes.json'),'polished_training_view':relative(BASE/'exports/teacher_chat_train_polished.jsonl'),'baseline_state':relative(BASE/'data_build_state.json')},'use_policy':'FULL CORPUS is append-only. Training inputs are only the explicit selected training-view files, never every JSONL, audit or snapshot in this package. Protected overlaps are retained accepted in the corpus and segregated from new views. Legacy numeric-overlap exceptions remain separately disclosed.','limits':['All first-stage ordered pairs are proven by actual shard readback sequence, independent closed-form counts and disjoint physical partitions; this is not exhaustive natural-language mathematics.','First stage addition/subtraction0..1000, table0..10, dividend0..1000/divisor1..9 andzero-divisor recognition; larger domains remain explicitly incomplete.','Current curriculum reference versus enrichment classification does not certify alllegal2026requirements or2006completeness.','Numeric exclusion is bounded canonical comparison against701known development fingerprints; does not prove universal semantic independence or inspect sealed concept tests.','Tokenizer audit scope is explicit; original768/512 configuration would cut some preserved baseline cases and is not automatically suitable. No training launched.']}
 e.save(e.ROOT/'full_corpus_and_training_views.json',registry)
 # Actual measured storage throughput estimates for unstarted tiers, not a
 # promise of elapsed time or an implicit claim of generated coverage.
 corpusbytes=sum(m['bytes'] for m in sources);viewbytes=sum(m['bytes'] for m in views)
 rate=corpusbytes/state['new_generated_cases'];v_rate=viewbytes/max(1,sum(m['included_cases'] for m in views))
 capacity={'utc':e.utc(),'measured_first_stage_corpus_gzip_bytes':corpusbytes,'measured_first_stage_view_gzip_bytes':viewbytes,'measured_corpus_bytes_per_case':rate,'measured_view_bytes_per_included_case':v_rate,'future_ranges':[],'status':'PLANNED_NOT_MATERIALIZED','next_exact_commands':['Python313 -Xutf8 thinking/exhaustive_primary_math.py run --op + --max 10000 --prev 1000 --workers 3 --width 25','Python313 -Xutf8 thinking/exhaustive_primary_math.py run --op - --max 10000 --prev 1000 --workers 3 --width 25'],'resource_policy':'Preflight free storage before starting any next full logical domain. Never claim a generated domain from symbolic cardinality alone. Full sources remain preserved.'}
 for n,prev in ((10000,1000),(100000,10000)):
  for op in ('+','-'):
   missing=e.shell_count(op,n,prev);capacity['future_ranges'].append({'operation':op,'previous_maximum':prev,'maximum':n,'remaining_new_pairs':missing,'estimated_source_gzip_bytes':round(missing*rate),'estimated_view_gzip_bytes':round(missing*v_rate),'status':'NOT_STARTED','next_ordered_input_pair':[0,prev+1] if op=='+' else [prev+1,0]})
 e.save(e.ROOT/'capacity_and_resume_plan.json',capacity)
 return registry

def package():
 r=index();start=time.monotonic()
 candidates=[p for p in e.ROOT.rglob('*') if p.is_file() and p.suffix in ('.json','.jsonl','.gz','.py') and '.partial.' not in p.name and '.atomic' not in p.name and p.name!='teacher_chat_train_stage1.jsonl.gz' and not (p.suffix=='.gz' and 'training_views' in p.parts) and p.name!='teacher_chat.jsonl.gz']
 candidates += [p for p in e.EVIDENCE.rglob('*') if p.is_file() and p.suffix in ('.json','.jsonl','.gz','.py','.pdf','.txt','.zip') and 'remote_publication' not in p.name]
 candidates += [e.HERE/n for n in ('exhaustive_primary_math.py','exhaustive_curriculum_scope.py','exhaustive_run_stage.py','package_exhaustive_math.py','export_exhaustive_chat.py','exhaustive_fraction_math.py','exhaustive_decimal_math.py')]
 candidates=[p for p in candidates if p.exists()]
 paths={relative(p):p for p in candidates};assert not any('concept_challenge_v4' in x for x in paths)
 files=[]
 with zipfile.ZipFile(SNAP) as old:
  for info in old.infolist():
   if info.filename=='PACKAGE_MANIFEST.json':
    files.append({'path':'audit/finite495/PACKAGE_MANIFEST.json','sha256':e.digest(old.read(info.filename)),'baseline_zip_member':info.filename,'bytes':info.file_size})
   else:files.append({'path':info.filename,'sha256':e.digest(old.read(info.filename)),'baseline_zip_member':info.filename,'bytes':info.file_size})
  baselinepaths={f['path'] for f in files}
  for path,p in sorted(paths.items()):
   assert path not in baselinepaths,'Never overwrite baseline member while adding corpus'
   files.append({'path':path,'sha256':e.filehash(p),'bytes':p.stat().st_size})
  manifest={'status':r['status'],'accepted_cases':r['accepted_cases'],'chat_rows':r['chat_train_rows'],'all_requested_large_domains_completed':False,'baseline_source_snapshot_sha256':e.filehash(SNAP),'baseline_all_members_preserved':True,'authoritative_release_index':'thinking/data/exhaustive_math_v1/full_corpus_and_training_views.json','full_corpus_append_only':True,'never_train_all_files_from_package_glob':True,'training_started':False,'training_views_storage':{'kind':'SEPARATE_VERIFIED_DRIVE_COMBINED_GZIP_JSONL','drive_file_id':'1tkSQoAlxXXRUg2AwYfvqsFKVEmM_LmR6','combined_chat_sha256':e.load(e.ROOT/'publication/combined_chat_receipt.json')['sha256'],'individual_shards_in_this_zip':False,'shard_manifests_and_generators_preserved_for_reconstruction':True,'reason':'Connector512MiBperfilelimit; all accepted source cases stay in this ZIP, exact materialized chat in separateexistingDriveID.'},'files':files}
  tmp=OUT.with_suffix('.exhaustive.tmp.zip')
  with zipfile.ZipFile(tmp,'w',allowZip64=True) as z:
   for f in files:
    zi=zipfile.ZipInfo(f['path'],date_time=(2026,10,18,0,0,0));zi.compress_type=zipfile.ZIP_STORED if f['path'].endswith(('.gz','.zip')) else zipfile.ZIP_DEFLATED
    if 'baseline_zip_member' in f:z.writestr(zi,old.read(f['baseline_zip_member']))
    else:
     with paths[f['path']].open('rb') as inp,z.open(zi,'w',force_zip64=True) as target:shutil.copyfileobj(inp,target,1024*1024)
   z.writestr('PACKAGE_MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 with zipfile.ZipFile(tmp) as z:
  assert z.testzip() is None and len(z.namelist())==len(files)+1
  for f in files:
   h=hashlib.sha256()
   with z.open(f['path']) as inp:
    for chunk in iter(lambda:inp.read(1024*1024),b''):h.update(chunk)
   assert h.hexdigest()==f['sha256'],f['path']
 tmp.replace(OUT)
 result={'bytes':OUT.stat().st_size,'sha256':e.filehash(OUT),'members':len(files)+1,'accepted_cases':r['accepted_cases'],'chat_rows':r['chat_train_rows'],'seconds':round(time.monotonic()-start,2),'baseline_members_preserved':True,'fully_generated_domains_only_reported_complete':True}
 e.save(e.EVIDENCE/'package_build_receipt.json',result)
 print(e.dumps(result),flush=True)

if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='index':print(e.dumps(index()))
 else:package()
