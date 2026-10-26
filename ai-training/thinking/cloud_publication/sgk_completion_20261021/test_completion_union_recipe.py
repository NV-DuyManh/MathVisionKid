"""Metadata-only fixtures. No actual bundle proof or training data fabricated."""
from pathlib import Path
import copy,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import sgk_completion_union_recipe as U

def digest(n):return format(n,'064x')
def fixture():
    artifacts={}
    members=[]
    for i in range(31):
        ref=dict(file_id='fixture_old_'+str(i),sha256=digest(i+1),bytes=100+i,file_name='fixture.zip')
        artifacts[ref['file_id']]=ref
        if i<25:
            members.append(dict(**ref,role='candidate_chat',member='candidate.jsonl',member_sha256=digest(i+100),member_bytes=50,rows=6501092-24 if i==0 else 1))
    base=dict(artifacts=artifacts,members=members);refs=[];manifests={}
    for i,(name,cases,chats) in enumerate(U.APPENDS):
        ref=dict(id='fixture_append_'+str(i),file_name='fixture_append.zip',sha256=digest(1000+i),bytes=1234+i)
        descriptor=dict(run_id=name,bundle=ref,source_member='source.jsonl',chat_member='chat.jsonl',cases=cases,chat_rows=chats)
        manifests[ref['sha256']]=dict(accepted_cases=cases,chat_rows=chats,members={'source.jsonl':dict(sha256=digest(2000+i),bytes=50),'chat.jsonl':dict(sha256=digest(3000+i),bytes=50)})
        refs.append(descriptor)
    return base,refs,manifests

class CompletionUnionTests(unittest.TestCase):
    def test_all_four_supplements_and_candidate_total_not_train_claim(self):
        recipe=U.compile_union(*fixture())
        self.assertEqual(len(recipe['artifacts']),35)
        self.assertEqual(len(recipe['chat_members']),29)
        self.assertEqual(recipe['declared_candidate_chat_rows'],6501780)
        self.assertEqual(recipe['raw_candidate_chat_rows_including_declared_current_splits'],6501828)
        self.assertTrue(recipe['historical_split_totals_pending_full_archive_audit'])
        self.assertFalse(recipe['actual_train_only_row_total_verified'])
        self.assertFalse(recipe['training_started'])

    def test_missing_manifest_refuses_partial_union(self):
        base,refs,manifests=fixture();manifests.pop(refs[-1]['bundle']['sha256'])
        with self.assertRaisesRegex(ValueError,'discovery unresolved'):U.compile_union(base,refs,manifests)

    def test_lost_append_descriptor_rejected(self):
        base,refs,manifests=fixture()
        with self.assertRaisesRegex(ValueError,'Exactly four'):U.compile_union(base,refs[:-1],manifests)

    def test_wrong_chat_count_rejected(self):
        base,refs,manifests=fixture();refs[-1]['chat_rows']-=4
        with self.assertRaisesRegex(ValueError,'raw declared chat count'):U.compile_union(base,refs,manifests)

    def test_wrong_source_count_rejected(self):
        base,refs,manifests=fixture();refs[-1]['cases']-=1
        with self.assertRaisesRegex(ValueError,'source/chat counts'):U.compile_union(base,refs,manifests)

    def test_missing_remote_receipt_blocks_before_any_verifier(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(U,'RUN',Path(temp)),patch.object(U,'verified_bundle') as verifier:
                with self.assertRaisesRegex(ValueError,'only AFTER RUN5'):U.main()
                verifier.assert_not_called()
                self.assertEqual(list(Path(temp).iterdir()),[])

if __name__=='__main__':unittest.main()
