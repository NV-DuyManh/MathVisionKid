"""V2 source-pool labels, raw-hash linkage and immutable audit identity tests.
Uses local pinned tokenizer files; never loads model weights or makes network calls.
"""
import unittest,tempfile,json,gzip,hashlib,sqlite3
from pathlib import Path
from copy import deepcopy
import exhaustive_colab_loader as L
from exhaustive_primary_math import chat_records
from math_data_full_audit_v2 import FullArchiveAudit,plan_identity,DERIVATION_PROVENANCE
from math_data_full_audit import FullArchiveAudit as V1,plan_identity as v1_identity
from math_data_candidate_stream import build_recipe
from math_data_portable_resume import canonical,file_hash

class FullAuditV2Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tokenizer=L.load_qwen_tokenizer(Path.home()/'.cache/huggingface/hub/models--Qwen--Qwen3-1.7B/snapshots'/L.REVISION)
  p=Path(__file__).resolve().parent/'cloud_publication/sgk_completion_20261021/release/accepted_cases.jsonl'
  cls.original=json.loads(p.read_bytes().splitlines()[0])
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  self.source=deepcopy(self.original);self.source['sample_id']='peer_v2_fixture';self.source['case_group_id']='peer_v2_fixture_group';self.source['split']='train_candidate'
 def tearDown(self):self.tmp.cleanup()
 def entry(self,name,rows,role):
  p=self.root/(name+'.jsonl.gz');p.write_bytes(gzip.compress(''.join(canonical(x)+'\n'for x in rows).encode(),mtime=0))
  return dict(file_id=name,file_name=p.name,sha256=file_hash(p),bytes=p.stat().st_size,role=role,rows=len(rows)),p
 def fixture(self,name='x',change=None):
  chats=list(chat_records(self.source))
  # This is a fixture hash over the exact source JSONL bytes (without newline).
  rh=hashlib.sha256(canonical(self.source).encode()).hexdigest()
  for c in chats:c['source_row_sha256']=rh
  if change:change(chats)
  se,sp=self.entry(name+'s',[self.source],'candidate_source')
  ce,cp=self.entry(name+'c',chats,'candidate_chat')
  return build_recipe([{'members':[se,ce]}]),se,sp,ce,cp
 def run_audit(self,fixture,name):
  recipe,se,sp,ce,cp=fixture
  a=FullArchiveAudit(self.root/(name+'.db'),recipe,self.tokenizer)
  a.consume(se,sp,None);a.consume(ce,cp,None);r=a.report()
  self.assertGreater(r['max_sequence_tokens'],0)
  return a,r
 def test_builder_candidate_label_links_all_four_without_relabeling(self):
  self.assertEqual(self.source['split'],'train_candidate')
  before=canonical(self.source)
  a,r=self.run_audit(self.fixture(),'valid')
  self.assertTrue(r['full_archive_token_linkage_split_audit_complete'])
  self.assertEqual(r['source_labels_indexed'],{'train_candidate':1})
  self.assertEqual(r['candidate_source_train_chat_links'],4)
  self.assertEqual(r['source_hash_origins'],{'ORIGINAL_RAW_HASH_VERIFIED':4})
  self.assertEqual(a.db.execute('SELECT source_split FROM source_versions').fetchone()[0],'train_candidate')
  self.assertEqual(canonical(self.source),before)
  self.assertFalse(r['TRAINING_DATASET_READY']);self.assertFalse(r['training_started']);a.close()
 def test_candidate_cannot_link_eval_and_standard_source_split_must_match(self):
  for n,target in enumerate(['validation','test']):
   with self.subTest(candidate_to=target):
    def change(rows):
     for r in rows:r['split']=target
    a,r=self.run_audit(self.fixture('eval'+str(n),change),'eval'+str(n))
    self.assertEqual(r['issues']['SOURCE_CHAT_SPLIT_MISMATCH'],4)
    self.assertEqual(r['source_linkage_unverified_rows'],4)
    self.assertFalse(r['full_archive_token_linkage_split_audit_complete']);a.close()
  self.source['split']='validation'
  a,r=self.run_audit(self.fixture('standard_mismatch'),'standard_mismatch')
  self.assertEqual(r['issues']['SOURCE_CHAT_SPLIT_MISMATCH'],4);a.close()
  def standard_match(rows):
   for r in rows:r['split']='validation'
  a,r=self.run_audit(self.fixture('standard_match',standard_match),'standard_match')
  self.assertTrue(r['full_archive_token_linkage_split_audit_complete'])
  self.assertEqual(r['source_labels_indexed'],{'validation':1});a.close()
 def test_unknown_or_missing_source_label_remains_issue_and_unlinked(self):
  for n,label in enumerate(['mystery',None]):
   with self.subTest(label=label):
    if label is None:self.source.pop('split',None)
    else:self.source['split']=label
    a,r=self.run_audit(self.fixture('unknown'+str(n)),'unknown'+str(n))
    self.assertEqual(r['issues']['SOURCE_SPLIT_MISSING_OR_UNKNOWN'],1)
    self.assertEqual(r['source_linkage_unverified_rows'],4)
    self.assertFalse(r['full_archive_token_linkage_split_audit_complete']);a.close()
 def test_missing_fourth_chat_and_missing_or_unknown_chat_split_still_fail(self):
  a,r=self.run_audit(self.fixture('missingmode',lambda rs:rs.pop()),'missingmode')
  self.assertEqual(r['incomplete_four_mode_cases'],1)
  self.assertFalse(r['full_archive_token_linkage_split_audit_complete']);a.close()
  for n,label in enumerate([None,'train_candidate']):
   with self.subTest(chat_label=label):
    def change(rs):
     if label is None:rs[0].pop('split')
     else:rs[0]['split']=label
    recipe,se,sp,ce,cp=self.fixture('badsplit'+str(n),change)
    a=FullArchiveAudit(self.root/('badsplit'+str(n)+'.db'),recipe,self.tokenizer);a.consume(se,sp,None)
    with self.assertRaisesRegex(ValueError,'Explicit known chat split'):a.consume(ce,cp,None)
    self.assertFalse(a.report()['all_declared_members_scanned']);a.close()
 def test_wrong_existing_source_hash_never_fallbacks_to_other_source_version(self):
  a,r=self.run_audit(self.fixture('wronghash',lambda rs:rs[0].update(source_row_sha256='f'*64)),'wronghash')
  self.assertEqual(r['issues']['SOURCE_RAW_HASH_NOT_FOUND'],1)
  self.assertEqual(r['source_linkage_unverified_rows'],1)
  self.assertEqual(r['candidate_source_train_chat_links'],3)
  self.assertFalse(r['full_archive_token_linkage_split_audit_complete']);a.close()
 def test_v2_identity_refuses_v1_checkpoint_without_erasing_prior_issues(self):
  recipe,se,sp,ce,cp=self.fixture('identity')
  self.assertNotEqual(plan_identity(recipe),v1_identity(recipe))
  p=self.root/'v1.db';a=V1(p,recipe,self.tokenizer);a.consume(se,sp,None)
  self.assertEqual(a.report()['issues'],{'SOURCE_SPLIT_MISSING_OR_UNKNOWN':1});a.close()
  frozen=file_hash(p)
  with self.assertRaisesRegex(ValueError,'Different immutable audit identity'):FullArchiveAudit(p,recipe,self.tokenizer)
  self.assertEqual(file_hash(p),frozen)
  db=sqlite3.connect(p);self.assertEqual(db.execute('SELECT count(*) FROM issues').fetchone()[0],1);db.close()
  self.assertEqual(file_hash(Path(__file__).with_name('math_data_full_audit.py')),DERIVATION_PROVENANCE['parent_sha256'])
  self.assertEqual(file_hash(Path(__file__).with_name('exhaustive_primary_math.py')),DERIVATION_PROVENANCE['source_label_evidence_sha256'])
if __name__=='__main__':unittest.main()

