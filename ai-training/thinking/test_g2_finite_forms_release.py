"""Meaningful rejection tests for exact root review gates and additive union."""
import unittest
from copy import deepcopy
import g2_finite_forms_release as R

class ReviewAndUnionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.casebytes=(R.DRAFT/'cases.jsonl').read_bytes()
        cls.chatbytes=(R.DRAFT/'chat.jsonl').read_bytes()
        cls.source=R.rows(R.DRAFT/'cases.jsonl')
        cls.root=R.read(R.RUN/'root_content_review.json')
        cls.base=R.read(R.BASE)

    def test_real_root_review_accepts_only_exact_current_fields(self):
        result=R.validate_root(self.root,self.casebytes,self.chatbytes,self.source)
        self.assertEqual(len(result),6)

    def test_changed_content_cannot_reuse_root_review(self):
        root=deepcopy(self.root)
        root['reviews'][0]['actual_fields']['hints'][0]['hint']='Forged replacement'
        with self.assertRaisesRegex(ValueError,'reviewed fields differ'):
            R.validate_root(root,self.casebytes,self.chatbytes,self.source)

    def test_wrong_source_hash_cannot_reuse_root_review(self):
        root=deepcopy(self.root);root['reviews'][0]['source_row_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'row hash mismatch'):
            R.validate_root(root,self.casebytes,self.chatbytes,self.source)

    def test_unpassed_criterion_cannot_be_accepted(self):
        root=deepcopy(self.root);root['reviews'][0]['criteria'][0]['passed']=False
        with self.assertRaisesRegex(ValueError,'QA7 PASS required'):
            R.validate_root(root,self.casebytes,self.chatbytes,self.source)

    def test_unread_content_cannot_be_accepted(self):
        root=deepcopy(self.root);root['actual_content_read']=False
        with self.assertRaisesRegex(ValueError,'actual full-content'):
            R.validate_root(root,self.casebytes,self.chatbytes,self.source)

    def append_fixture(self):
        ref=dict(run_id='UNITTEST_NOT_PUBLISHED',bundle=dict(sha256='d'*64,bytes=10,file_id='UNITTEST_NOT_A_DRIVE_ID',file_name='fixture.zip'),source_member='source.jsonl',chat_member='chat.jsonl',cases=6,chat_rows=24)
        manifest=dict(accepted_cases=6,chat_rows=24,source_member='source.jsonl',chat_member='chat.jsonl',members={'source.jsonl':dict(sha256='e'*64,bytes=1),'chat.jsonl':dict(sha256='f'*64,bytes=2)})
        return ref,manifest,dict(TEST_ONLY_NO_REMOTE_PROOF=True)

    def test_additive_union_preserves_every_parent_prefix_and_artifact(self):
        ref,manifest,evidence=self.append_fixture();before=deepcopy(self.base)
        result=R.compile_append_only_union(self.base,ref,manifest,evidence)
        self.assertEqual(self.base,before)
        self.assertEqual(result['source_members'][:217],before['source_members'])
        self.assertEqual(result['chat_members'][:30],before['chat_members'])
        self.assertEqual(result['excluded_members'],before['excluded_members'])
        for k,v in before['artifacts'].items():self.assertEqual(result['artifacts'][k],v)
        self.assertEqual((len(result['artifacts']),len(result['source_members']),len(result['chat_members'])),(37,218,31))

    def test_union_rejects_existing_payload_id_even_with_new_bytes(self):
        ref,manifest,evidence=self.append_fixture()
        ref['bundle']['file_id']=self.base['chat_members'][0]['file_id']
        with self.assertRaisesRegex(ValueError,'reuses existing'):
            R.compile_append_only_union(self.base,ref,manifest,evidence)

    def test_union_rejects_referenced_member_bytes(self):
        ref,manifest,evidence=self.append_fixture()
        old=self.base['chat_members'][0]
        manifest['members']['chat.jsonl']['sha256']=old.get('member_sha256') or old['sha256']
        with self.assertRaisesRegex(ValueError,'already referenced'):
            R.compile_append_only_union(self.base,ref,manifest,evidence)

if __name__=='__main__':unittest.main()
