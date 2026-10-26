import copy,json,os,shutil,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
import exhaustive_cloud_resume as c

class CloudResumeTests(unittest.TestCase):
 def test_fresh_runtime_restores_committed_remote_cursors(self):
  state=c.init_reference()
  key=next(iter(state['extension_domains']))
  d=state['extension_domains'][key]
  d.update(cursor=3,generated_pairs=3,validated_pairs=3,missing_pairs=d['expected_pairs']-3,status='IN_PROGRESS')
  state['extension_shards']=[{'shard_id':'already_remote','file_id':'preserved_remote_id'}]
  state['accepted_cases']+=3
  c.save(self.run/'source_cloud_state.json',state)
  c.STATE.unlink()
  actual=c.init_reference()
  self.assertEqual(actual,state)
  self.assertEqual(actual['extension_domains'][key]['cursor'],3)
  self.assertEqual(actual['extension_shards'][0]['file_id'],'preserved_remote_id')
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.run=Path(self.t.name)/'publisher';self.run.mkdir()
  self.old={k:getattr(c,k) for k in ('RUN','TEMP','STATE')}
  c.RUN=self.run;c.TEMP=self.run/'temporary_shard';c.STATE=self.run/'working_cloud_state.json'
  self.source=copy.deepcopy(c.read(self.old['RUN']/'source_cloud_state.json'))
  c.save(self.run/'source_cloud_state.json',self.source)
 def tearDown(self):
  for k,v in self.old.items():setattr(c,k,v)
  self.t.cleanup()
 def prep(self):return c.prepare(4)
 def proof(self,m):return {'file_id':'verified_source_id','fresh_raw_verified':True,'all_bytes_equal':True,'sha256':m['bundle']['sha256'],'bytes':m['bundle']['bytes'],'verified_utc':c.utc()}
 def test_failed_upload_prepares_identical_bytes_without_advancing(self):
  a=self.prep();before=c.filehash(c.STATE);b=self.prep();self.assertEqual(a,b);self.assertEqual(before,c.filehash(c.STATE));self.assertEqual(c.read(c.STATE)['accepted_cases'],1519171)
 def test_bad_hash_cannot_advance_checkpoint(self):
  m=self.prep();p=self.proof(m);p['sha256']='0'*64;c.save(self.run/'bad.json',p)
  with self.assertRaises(AssertionError):c.stage_commit(self.run/'bad.json')
  self.assertFalse((self.run/'next_cloud_state.json').exists());self.assertTrue(c.TEMP.exists())
 def test_verified_payload_still_requires_verified_remote_checkpoint(self):
  m=self.prep();c.save(self.run/'raw.json',self.proof(m));r=c.stage_commit(self.run/'raw.json')
  self.assertEqual(c.read(c.STATE)['accepted_cases'],1519171)
  p={'file_id':'wrong_id','fresh_raw_verified':True,'all_bytes_equal':True,'sha256':r['sha256'],'bytes':r['bytes']};c.save(self.run/'checkpoint.json',p)
  with self.assertRaises(AssertionError):c.finalize_commit(self.run/'checkpoint.json')
  self.assertTrue(c.TEMP.exists())
  p['file_id']='1TLoQIbrRVmgsg-2uiUujCfM3HrK62Yme';c.save(self.run/'checkpoint.json',p)
  c.finalize_commit(self.run/'checkpoint.json')
  state=c.read(c.STATE);self.assertEqual(state['accepted_cases'],1519175);self.assertEqual(state['parts'],self.source['parts']);self.assertFalse(c.TEMP.exists())
  replay=c.finalize_commit(self.run/'checkpoint.json');self.assertTrue(replay['already_committed'])
  self.assertEqual(c.read(c.STATE)['accepted_cases'],1519175)
 def test_rebuild_has_same_bundle_hash_despite_member_mtimes(self):
  a=self.prep();original=(c.TEMP/a['bundle']['name']).read_bytes()
  for name in ('source.jsonl.gz','chat.jsonl.gz','manifest_payload.json'):
   os.utime(c.TEMP/name,(1800000000,1800000000))
  rebuilt=self.run/'rebuilt.zip'
  c.deterministic_bundle(rebuilt,[c.TEMP/n for n in ('source.jsonl.gz','chat.jsonl.gz','manifest_payload.json')])
  self.assertEqual(original,rebuilt.read_bytes())
  with zipfile.ZipFile(rebuilt) as z:
   self.assertTrue(all(i.date_time==(1980,1,1,0,0,0) and i.create_system==3 for i in z.infolist()))
  shutil.rmtree(c.TEMP);b=self.prep()
  self.assertEqual(a,b)
 def stage(self):
  m=self.prep();c.save(self.run/'raw.json',self.proof(m));r=c.stage_commit(self.run/'raw.json')
  p={'file_id':'1TLoQIbrRVmgsg-2uiUujCfM3HrK62Yme','fresh_raw_verified':True,'all_bytes_equal':True,'sha256':r['sha256'],'bytes':r['bytes']}
  c.save(self.run/'checkpoint.json',p)
  return m,r
 def test_repeated_stage_after_remote_checkpoint_preserves_exact_bytes(self):
  m,r=self.stage();before=(self.run/'next_cloud_state.json').read_bytes()
  proof=self.proof(m);proof['verified_utc']='later_verified_time';c.save(self.run/'raw.json',proof)
  with patch.object(c,'utc',return_value='different_clock'):
   self.assertEqual(r,c.stage_commit(self.run/'raw.json'))
  self.assertEqual(before,(self.run/'next_cloud_state.json').read_bytes())
  self.assertEqual(c.read(c.STATE)['accepted_cases'],1519171)
 def test_finalize_replays_after_state_advanced_but_cleanup_crashed(self):
  m,_=self.stage()
  with patch.object(c.shutil,'rmtree',side_effect=OSError('simulated cleanup crash')):
   with self.assertRaises(OSError):c.finalize_commit(self.run/'checkpoint.json')
  self.assertEqual(c.read(c.STATE)['accepted_cases'],1519175)
  with self.assertRaises(RuntimeError):self.prep()
  with self.assertRaises(AssertionError):
   proof=self.proof(m);proof['file_id']='other_source_id';c.save(self.run/'other.json',proof);c.stage_commit(self.run/'other.json')
  c.stage_commit(self.run/'raw.json')
  c.finalize_commit(self.run/'checkpoint.json')
  self.assertFalse(c.TEMP.exists());self.assertEqual(c.read(c.STATE)['accepted_cases'],1519175)
 def test_finalize_replays_after_manifest_removed_mid_cleanup(self):
  m,_=self.stage()
  def partial_delete(path):
   (path/'manifest.json').unlink();raise OSError('simulated partial deletion')
  with patch.object(c.shutil,'rmtree',side_effect=partial_delete):
   with self.assertRaises(OSError):c.finalize_commit(self.run/'checkpoint.json')
  self.assertFalse((c.TEMP/'manifest.json').exists())
  replay=c.finalize_commit(self.run/'checkpoint.json');self.assertTrue(replay['already_committed'])
  self.assertFalse(c.TEMP.exists());self.assertEqual(c.read(c.STATE)['accepted_cases'],1519175)
 def test_configuration_is_idempotent_in_persistent_process(self):
  c.configure_sources();first=(c.arithmetic.scope_module.EVIDENCE_PATH,c.arithmetic.scope_module.ANNEX_PATH)
  c.configure_sources();self.assertEqual(first,(c.arithmetic.scope_module.EVIDENCE_PATH,c.arithmetic.scope_module.ANNEX_PATH))
 def test_budget_failure_leaves_checkpoint_and_no_partial_shard(self):
  c.init_reference();before=c.filehash(c.STATE)
  with patch.object(c,'MAX_TEMP_BYTES',1024):
   with self.assertRaises(ValueError):self.prep()
  self.assertEqual(before,c.filehash(c.STATE));self.assertFalse(c.TEMP.exists())
 def test_generation_interruption_leaves_checkpoint_and_no_partial_shard(self):
  c.init_reference();before=c.filehash(c.STATE);make=c.arithmetic.make_row;calls=[]
  def interrupted(*args):
   calls.append(args)
   if len(calls)>1:raise KeyboardInterrupt('simulated generation interruption')
   return make(*args)
  with patch.object(c.arithmetic,'make_row',side_effect=interrupted):
   with self.assertRaises(KeyboardInterrupt):self.prep()
  self.assertEqual(before,c.filehash(c.STATE));self.assertFalse(c.TEMP.exists())
 def test_exclusive_manager_lock(self):
  with c.manager_lock():
   with self.assertRaises(RuntimeError):
    with c.manager_lock():pass
 def test_nested_domains_no_old_ids_no_cross_domain_duplicate(self):
  seen=set()
  for s in c.normalize_specs():
   pairs=list(c.arithmetic.iter_domain_pairs(s));self.assertEqual(len(pairs),s['expected_pairs'])
   for a,b in pairs:
    key=(s['operation'],a,b);self.assertNotIn(key,seen);seen.add(key)
    if s['operation']=='*':self.assertTrue(a>10 or b>10)
    else:self.assertGreaterEqual(b,10)
  self.assertEqual(len(seen),110070)
 def test_invalid_local_limit_cannot_create_payload(self):
  for n in (0,10001):
   with self.assertRaises(ValueError):c.prepare(n)
  self.assertFalse(c.TEMP.exists())

if __name__=='__main__':unittest.main(verbosity=2)
