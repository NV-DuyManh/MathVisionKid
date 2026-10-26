"""Real pinned-tokenizer tests of complete-candidate source/chat audit gates."""
import unittest,tempfile,json,gzip
from pathlib import Path
from copy import deepcopy
import exhaustive_colab_loader as L
from exhaustive_primary_math import chat_records
from math_data_full_audit import FullArchiveAudit
from math_data_candidate_stream import build_recipe
from math_data_portable_resume import canonical,file_hash
class FullAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tokenizer=L.load_qwen_tokenizer(Path.home()/'.cache/huggingface/hub/models--Qwen--Qwen3-1.7B/snapshots'/L.REVISION)
        p=Path(__file__).resolve().parent/'cloud_publication/sgk_completion_20261021/release/accepted_cases.jsonl'
        cls.original=json.loads(p.read_bytes().splitlines()[0])
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.source=deepcopy(self.original);self.source['sample_id']='fullaudit_fixture';self.source['case_group_id']='fullaudit_fixture_group'
    def tearDown(self):self.temp.cleanup()
    def entry(self,name,items,role):
        raw=''.join(canonical(x)+'\n' for x in items).encode()
        p=self.root/(name+'.jsonl.gz');p.write_bytes(gzip.compress(raw,mtime=0))
        return dict(file_id=name,file_name=p.name,sha256=file_hash(p),bytes=p.stat().st_size,role=role,rows=len(items)),p
    def fixture(self,mutate=None,duplicate=False):
        chats=list(chat_records(self.source))
        if mutate:mutate(chats)
        if duplicate:chats=chats+deepcopy(chats)
        se,sp=self.entry('source',[self.source],'candidate_source')
        ce,cp=self.entry('chat',chats,'candidate_chat')
        recipe=build_recipe([{'members':[se,ce]}])
        return recipe,se,sp,ce,cp
    def test_real_tokens_full_source_linkage_and_read_time_hash_derivation(self):
        recipe,se,sp,ce,cp=self.fixture();a=FullArchiveAudit(self.root/'a.db',recipe,self.tokenizer)
        a.consume(se,sp,None);a.consume(ce,cp,None);r=a.report();a.close()
        self.assertTrue(r['full_archive_token_linkage_split_audit_complete'])
        self.assertEqual(r['unique_chat_rows_processed'],4);self.assertGreater(r['max_sequence_tokens'],0)
        self.assertEqual(r['source_hash_origins'],{'READ_TIME_DERIVED_BY_FULL_PROMPT_TARGET_LINKAGE':4})
        self.assertFalse(r['TRAINING_DATASET_READY']);self.assertFalse(r['training_started'])
    def test_chat_before_sources_refused(self):
        recipe,se,sp,ce,cp=self.fixture();a=FullArchiveAudit(self.root/'a.db',recipe,self.tokenizer)
        with self.assertRaisesRegex(ValueError,'every declared source'):a.consume(ce,cp)
        a.close()
    def test_missing_split_never_becomes_train(self):
        recipe,se,sp,ce,cp=self.fixture(lambda rows:rows[0].pop('split'))
        a=FullArchiveAudit(self.root/'a.db',recipe,self.tokenizer);a.consume(se,sp,None)
        with self.assertRaisesRegex(ValueError,'Explicit known chat split'):a.consume(ce,cp,None)
        self.assertFalse(a.report()['all_declared_members_scanned']);a.close()
    def test_tampered_target_fails_linkage_not_accepted_on_parser(self):
        def bad(rows):
            target=json.loads(rows[0]['messages'][2]['content']);target['answer']=[];rows[0]['messages'][2]['content']=canonical(target)
        recipe,se,sp,ce,cp=self.fixture(bad)
        a=FullArchiveAudit(self.root/'a.db',recipe,self.tokenizer);a.consume(se,sp,None);a.consume(ce,cp,None)
        r=a.report();a.close()
        self.assertEqual(r['issues']['SOURCE_CHAT_LINKAGE_UNVERIFIED'],1);self.assertFalse(r['full_archive_token_linkage_split_audit_complete'])
    def test_exact_duplicate_occurrences_preserved_and_counted(self):
        recipe,se,sp,ce,cp=self.fixture(duplicate=True)
        a=FullArchiveAudit(self.root/'a.db',recipe,self.tokenizer);a.consume(se,sp,None);a.consume(ce,cp,None)
        r=a.report();a.close()
        self.assertEqual((r['unique_chat_rows_processed'],r['physical_chat_occurrences_processed'],r['exact_duplicate_references']),(4,8,4))
        self.assertTrue(r['full_archive_token_linkage_split_audit_complete'])
    def test_resume_after_two_rows_checks_eof_and_four_modes(self):
        recipe,se,sp,ce,cp=self.fixture();db=self.root/'a.db'
        a=FullArchiveAudit(db,recipe,self.tokenizer);a.consume(se,sp,None);a.consume(ce,cp,2)
        self.assertFalse(a.report()['all_declared_members_scanned']);a.close()
        a=FullArchiveAudit(db,recipe,self.tokenizer);a.consume(ce,cp,None)
        self.assertTrue(a.report()['full_archive_token_linkage_split_audit_complete']);a.close()
    def test_declared_member_count_mismatch_stops(self):
        recipe,se,sp,ce,cp=self.fixture();ce['rows']+=1;recipe=build_recipe([{'members':[se,ce]}])
        a=FullArchiveAudit(self.root/'a.db',recipe,self.tokenizer);a.consume(se,sp,None)
        with self.assertRaisesRegex(ValueError,'row count'):a.consume(ce,cp,None)
        a.close()
    def test_wrong_existing_source_hash_never_replaced_to_pass(self):
        recipe,se,sp,ce,cp=self.fixture(lambda rows:rows[0].update(source_row_sha256='f'*64))
        a=FullArchiveAudit(self.root/'a.db',recipe,self.tokenizer);a.consume(se,sp,None);a.consume(ce,cp,None)
        r=a.report();a.close()
        self.assertIn('SOURCE_RAW_HASH_NOT_FOUND',r['issues']);self.assertFalse(r['full_archive_token_linkage_split_audit_complete'])
    def test_append_migration_preserves_old_evidence_and_indexes_new_source_first(self):
        recipe,se,sp,ce,cp=self.fixture();db=self.root/'a.db'
        a=FullArchiveAudit(db,recipe,self.tokenizer);a.consume(se,sp,None);a.consume(ce,cp,None);a.close()
        self.source['sample_id']='second';self.source['case_group_id']='second_group'
        se2,sp2=self.entry('source2',[self.source],'candidate_source')
        ce2,cp2=self.entry('chat2',list(chat_records(self.source)),'candidate_chat')
        new=build_recipe([{'members':[se,se2,ce,ce2]}])
        proof=FullArchiveAudit.extend_recipe(db,recipe,new);self.assertTrue(proof['prior_evidence_preserved'])
        a=FullArchiveAudit(db,new,self.tokenizer)
        self.assertEqual(a.report()['unique_chat_rows_processed'],4)
        self.assertEqual(a.next_entry()['role'],'candidate_source')
        a.consume(se2,sp2,None);a.consume(ce2,cp2,None)
        self.assertEqual(a.report()['unique_chat_rows_processed'],8)
        self.assertTrue(a.report()['full_archive_token_linkage_split_audit_complete']);a.close()
    def test_replaced_old_member_cannot_migrate_checkpoint(self):
        recipe,se,sp,ce,cp=self.fixture();db=self.root/'a.db'
        a=FullArchiveAudit(db,recipe,self.tokenizer);a.close()
        new=deepcopy(recipe);new['source_members'][0]['sha256']='f'*64
        with self.assertRaisesRegex(ValueError,'immutable'):FullArchiveAudit.extend_recipe(db,recipe,new)
        a=FullArchiveAudit(db,recipe,self.tokenizer);self.assertEqual(a.report()['members_complete'],0);a.close()
if __name__=='__main__':unittest.main()

