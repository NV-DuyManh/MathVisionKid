"""Offline fake-store checks; never instantiate a Drive client."""
import hashlib,importlib.util,json,shutil,tempfile,types,unittest
from pathlib import Path


def load(name):
 spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name('publisher_runtime.py'))
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

p=load('publisher_under_test')
class IntegrityError(ValueError):pass
class SnapshotBusyError(RuntimeError):pass

class FakeStore:
 def __init__(self):self.folder='folder';self.data={};self.proofs={};self.raw_reads=[];self.fail=None
 def put(self,name,snapshot,immutable=False):
  if self.fail and self.fail[0] in name:
   error=self.fail[1];self.fail=None;raise error
  data=Path(snapshot).read_bytes()
  if immutable and name in self.data and self.data[name]!=data:raise IntegrityError('immutable conflict')
  self.data[name]=data;h=hashlib.sha256(data).hexdigest();ref=self.raw_proof(name,h,len(data))
  self.proofs[name]={**ref,'name':name,'immutable':immutable};return self.proofs[name]
 def raw_proof(self,file_id,h,count):
  data=self.data[file_id]
  if len(data)!=count or hashlib.sha256(data).hexdigest()!=h:raise IntegrityError('raw mismatch')
  self.raw_reads.append(file_id)
  return {'id':file_id,'bytes':count,'sha256':h,'fresh_raw_readback_verified':True,'folder_id':self.folder}

class PublisherTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);(self.root/'training').mkdir()
  self.busy=False;self.store=FakeStore()
  def snapshot(source,dest):
   if self.busy:self.busy=False;raise SnapshotBusyError('source changing')
   dest=Path(dest);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
  def package(gen,work):
   work.mkdir(parents=True,exist_ok=True);archive=work/'checkpoint_step_000001.zip';archive.write_bytes(b'fake verified checkpoint')
   return archive,{'step':1,'rows_done':16,'manifest_sha256':p.sha(gen/'generation_manifest.json'),'generation':gen.name}
  self.lib=types.SimpleNamespace(IntegrityError=IntegrityError,SnapshotBusyError=SnapshotBusyError,snapshot_file=snapshot,package_generation=package)
  self.loop=p.PublicationLoop(self.root,self.lib,self.store)
 def tearDown(self):self.tmp.cleanup()
 def write(self,name,value):
  path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True)
  if isinstance(value,dict):path.write_text(json.dumps(value),encoding='utf-8')
  else:path.write_text(value,encoding='utf-8')
  return path
 def test_complete_waits_for_late_report_and_hash_bound_marker(self):
  self.write('training/run_complete.json',{'complete':True,'best':{'kind':'untrained_base'}})
  self.assertEqual(self.loop.cycle(),'CONTINUE')
  self.assertEqual(self.loop.state['state'],'WAITING_FINAL_REVIEW_PUBLICATION')
  report=self.write('training/final_semantic_assessment.json',{'decision':'KEEP_BASE'})
  self.assertEqual(self.loop.cycle(),'CONTINUE')
  name='training__final_semantic_assessment.json';reads=self.store.raw_reads.count(name)
  self.write('publication/finalize_requested.json',{'finalize_requested':True,'final_semantic_assessment_sha256':p.sha(report)})
  self.assertEqual(self.loop.cycle(),'DONE');self.assertGreater(self.store.raw_reads.count(name),reads)
  proof=json.loads(self.store.data['training_complete_publication_proof.json'])
  self.assertTrue(proof['publication_finalized']);self.assertTrue(proof['final_semantic_assessment_proof']['fresh_raw_readback_verified'])
  self.assertEqual(self.loop.state['state'],'COMPLETE_RAW_VERIFIED')
 def test_marker_without_report_does_not_finish(self):
  self.write('training/run_complete.json',{'complete':True})
  self.write('publication/finalize_requested.json',{'finalize_requested':True,'final_semantic_assessment_sha256':'a'*64})
  self.assertEqual(self.loop.cycle(),'CONTINUE')
  self.assertFalse(self.loop.state.get('publication_finalized',False))
 def test_busy_and_transient_errors_retry_then_recover(self):
  self.write('owner_run_scope.json',{'scope':'test'});self.busy=True
  self.assertEqual(self.loop.cycle(),'RETRY');self.assertTrue(self.loop.state['errors'][-1]['retryable'])
  self.store.fail=('owner_run_scope',TimeoutError('temporary network failure'))
  self.assertEqual(self.loop.cycle(),'RETRY');self.assertEqual(self.loop.cycle(),'CONTINUE')
  self.assertIn('owner_run_scope.json',self.loop.state['artifacts'])
 def test_integrity_conflict_is_fatal_not_retry(self):
  self.write('training/eval_step_000050/adapter_generations.jsonl','first full output')
  self.assertEqual(self.loop.cycle(),'CONTINUE')
  self.write('training/eval_step_000050/adapter_generations.jsonl','changed output')
  self.assertEqual(self.loop.cycle(),'FATAL');self.assertEqual(self.loop.state['state'],'ERROR')
  self.assertFalse(self.loop.state['last_error']['retryable'])
 def test_checkpoint_pointer_waits_for_raw_checkpoint_success(self):
  gen='generation_step_000001_rows_00000016'
  manifest=self.write('training/'+gen+'/generation_manifest.json',{'complete':True,'step':1,'rows_done':16})
  self.write('training/latest.json',{'generation':gen,'manifest_sha256':p.sha(manifest)})
  self.store.fail=('checkpoint_step_',TimeoutError('upload not yet complete'))
  self.assertEqual(self.loop.cycle(),'RETRY');self.assertNotIn('latest_checkpoint.json',self.store.data)
  self.assertEqual(self.loop.cycle(),'CONTINUE')
  pointer=json.loads(self.store.data['latest_checkpoint.json'])
  self.assertTrue(pointer['checkpoint']['fresh_raw_readback_verified'])
  self.assertTrue(pointer['pointer_written_after_raw_checkpoint'])
 def test_process_registry_survives_module_reload(self):
  other=load('publisher_second_import');registry=p._registry();self.assertIs(registry,other._registry())
  previous=registry.thread;registry.thread=types.SimpleNamespace(is_alive=lambda:True)
  try:
   with self.assertRaisesRegex(RuntimeError,'already active'):other.start(None,self.root)
  finally:registry.thread=previous
 def test_test_sources_upload_as_immutable_metadata(self):
  self.write('test_recovery_example.py','assert True')
  self.assertEqual(self.loop.cycle(),'CONTINUE')
  self.assertTrue(self.store.proofs['test_recovery_example.py']['immutable'])
 def test_wrong_final_report_hash_fails_closed(self):
  self.write('training/run_complete.json',{'complete':True})
  self.write('final_semantic_assessment.json',{'decision':'STOP'})
  self.write('publication/finalize_requested.json',{'finalize_requested':True,'final_semantic_assessment_sha256':'0'*64})
  self.assertEqual(self.loop.cycle(),'FATAL');self.assertFalse(self.loop.state.get('publication_finalized',False))

class MissingParentMetadataTests(unittest.TestCase):
 def make_store(self,meta,found,folder=None):
  class Base:
   def __init__(self):self.parent='root';self.folder_name='run';self.folder=folder;self.calls=[]
   def metadata(self,file_id):return dict(meta)
   def find(self,parent,name):self.calls.append((parent,name));return found
  return p.parent_verified_store_class(types.SimpleNamespace(DriveStore=Base,IntegrityError=IntegrityError))()
 def test_missing_parents_accepts_exact_fresh_list_without_invention(self):
  raw={'id':'runid','name':'run','mimeType':'application/vnd.google-apps.folder','trashed':False}
  listed={**raw,'parents':['root']};store=self.make_store(raw,[listed])
  result=store.metadata('runid')
  self.assertEqual(result['parents'],listed['parents']);self.assertNotIn('parents',raw)
  self.assertEqual(store.calls,[('root','run')]);self.assertEqual(len(store.parent_fallback_proofs),1)
 def test_explicit_wrong_parent_fails_without_fallback(self):
  raw={'id':'runid','name':'run','mimeType':'application/vnd.google-apps.folder','parents':['wrong']}
  store=self.make_store(raw,[{**raw,'parents':['root']}])
  with self.assertRaisesRegex(IntegrityError,'Explicit'):store.metadata('runid')
  self.assertEqual(store.calls,[])
 def test_list_must_supply_actual_expected_parent_and_exact_identity(self):
  raw={'id':'runid','name':'run','mimeType':'application/vnd.google-apps.folder'}
  good={**raw,'parents':['root'],'trashed':False}
  for changed in ({'parents':['wrong']},{'parents':None},{'id':'other'},{'mimeType':'text/plain'},{'trashed':True}):
   with self.subTest(changed=changed):
    store=self.make_store(raw,[{**good,**changed}])
    with self.assertRaises(IntegrityError):store.metadata('runid')
    self.assertFalse(hasattr(store,'parent_fallback_proofs'))
 def test_duplicate_list_and_artifact_parent_scope(self):
  raw={'id':'artifact','name':'metadata.json','mimeType':'application/json'}
  good={**raw,'parents':['runid']}
  store=self.make_store(raw,[good],folder='runid')
  self.assertEqual(store.metadata('artifact')['parents'],['runid'])
  self.assertEqual(store.calls,[('runid','metadata.json')])
  store=self.make_store(raw,[good,good],folder='runid')
  with self.assertRaisesRegex(IntegrityError,'ambiguous'):store.metadata('artifact')
 def test_parent_root_skips_parent_inference(self):
  raw={'id':'root','name':'parent','mimeType':'application/vnd.google-apps.folder'}
  store=self.make_store(raw,[])
  self.assertEqual(store.metadata('root'),raw);self.assertEqual(store.calls,[])

if __name__=='__main__':unittest.main()
