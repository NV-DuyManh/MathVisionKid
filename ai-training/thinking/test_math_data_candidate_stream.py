"""Meaningful data-only union, resume, tamper and provenance tests."""
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

import exhaustive_colab_loader as L
import math_data_candidate_stream as C
import math_data_portable_resume as P
from math_data_archive_audit import source_projection
from math_data_source_hash_overlay import VerifiedSourceHashOverlay


def rows(prefix='a',split='train'):
    for mode in L.MODES:
        yield {'sample_id':prefix+':'+mode,'source_sample_id':prefix,'case_group_id':prefix+'_group',
            'mode':mode,'split':split,'messages':[{'role':'system','content':'Tutor'},
            {'role':'user','content':P.canonical({'problem':'Question '+prefix,'grade':1,'mode':mode})},
            {'role':'assistant','content':P.canonical({'can_solve':True,'initial_guidance':['think'],'steps':[],'answer':[]}) if mode=='worked_solution' else P.canonical({'hint':'think','question':'why?'})}]}


class StreamTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()

    def entry(self,name,items,kind='plain'):
        raw=''.join(P.canonical(x)+'\n' for x in items).encode()
        path=self.root/(name+('.zip' if kind=='zip' else '.jsonl.gz' if kind=='gzip' else '.jsonl'))
        member=None
        if kind=='zip':
            member='data/accepted_chat.jsonl'
            with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
                z.writestr(member,raw);z.writestr('sealed/never_read.jsonl','notJSON')
        else:path.write_bytes(gzip.compress(raw,mtime=0) if kind=='gzip' else raw)
        e={'file_id':name,'file_name':path.name,'sha256':P.file_hash(path),'bytes':path.stat().st_size,
           'member':member,'role':'candidate_chat','rows':len(items)}
        if member:e.update(member_sha256=hashlib.sha256(raw).hexdigest(),member_bytes=len(raw))
        return e,path

    def recipe(self,*entries):return C.build_recipe([{'members':list(entries)}])

    def test_union_plain_gzip_zip_and_split_filter(self):
        a,pa=self.entry('a',list(rows('a')))
        b,pb=self.entry('b',list(rows('b'))+list(rows('eval','validation')),'gzip')
        c,pc=self.entry('c',list(rows('c')),'zip')
        recipe=self.recipe(a,b,c);paths={e['sha256']:p for e,p in [(a,pa),(b,pb),(c,pc)]}
        seen=[];consumer=C.DataOnlyConsumer(self.root/'a.sqlite',C.CandidateStream(recipe,paths,'train'))
        report=consumer.consume(lambda row,evidence:seen.append(row['sample_id']));consumer.close()
        self.assertEqual(len(seen),12);self.assertEqual(report['counts']['EXCLUDED_OTHER_SPLIT'],4)
        self.assertTrue(report['stream_exhausted']);self.assertEqual(report['complete_members'],3)
        self.assertEqual(report['incomplete_case_modes'],0);self.assertFalse(report['all_data_training_ready'])
        self.assertEqual(len(list(C.CandidateStream(recipe,paths,'validation').iter_with_cursors())),4)

    def test_history_and_diagnostic_excluded_without_opening(self):
        e,p=self.entry('a',list(rows()))
        history={**e,'role':'diagnostic_duplicate_excluded','sha256':'f'*64,'file_name':'not_present.zip'}
        recipe=self.recipe(e,history)
        self.assertEqual(len(recipe['chat_members']),1);self.assertEqual(len(recipe['excluded_members']),1)
        self.assertEqual(len(list(C.CandidateStream(recipe,{e['sha256']:p},'train').iter_with_cursors())),4)

    def test_future_supplement_unknown_key_discovered_not_skipped(self):
        e,p=self.entry('append',list(rows('new')),'zip');source='data/accepted_cases.jsonl'
        descriptor={'run_id':'unknown_future_label','bundle':e,'chat_member':e['member'],'source_member':source,'cases':1,'chat_rows':4}
        found=C.discover_supplements({'whatever_new_runs':[descriptor]});self.assertEqual(len(found),1)
        pending=C.build_recipe([],found);self.assertEqual(len(pending['pending_discovery']),1)
        with self.assertRaisesRegex(ValueError,'unresolved'):C.CandidateStream(pending,{},'train')
        manifest={'members':{e['member']:{'sha256':e['member_sha256'],'bytes':e['member_bytes']},source:{'sha256':'a'*64,'bytes':1}}}
        recipe=C.build_recipe([],found,{e['sha256']:manifest})
        self.assertEqual(recipe['raw_candidate_chat_rows_including_declared_current_splits'],4)
        self.assertEqual(len(list(C.CandidateStream(recipe,{e['sha256']:p},'train').iter_with_cursors())),4)

    def test_same_archive_in_multiple_controls_idempotent(self):
        e,p=self.entry('a',list(rows()),'zip');other={**e,'file_id':'runtime_new_locator'}
        recipe=self.recipe(e,other)
        self.assertEqual(len(recipe['chat_members']),1);self.assertEqual(len(recipe['duplicate_member_references']),1)
        self.assertEqual(C.recipe_identity(recipe,'train'),C.recipe_identity(self.recipe(e),'train'))

    def test_later_numeric_payload_manifest_supported_and_role_swap_rejected(self):
        entry,path=self.entry('numeric',list(rows('n')),'zip')
        run={'bundle':entry,'source_member':'source.jsonl.gz','chat_member':entry['member'],'cases':1,'chat_rows':4}
        metadata={'source':{'name':'source.jsonl.gz','sha256':'a'*64,'bytes':10},
                  'view':{'name':entry['member'],'sha256':entry['member_sha256'],'bytes':entry['member_bytes']}}
        recipe=C.build_recipe([],C.discover_supplements({'new_numeric_shards':[run]}),{entry['sha256']:metadata})
        self.assertEqual(len(recipe['source_members']),1);self.assertEqual(len(recipe['chat_members']),1)
        swapped={**metadata,'chat_member':'audit/history.jsonl'}
        with self.assertRaisesRegex(ValueError,'role'):
            C.build_recipe([],[run],{entry['sha256']:swapped})

    def test_durable_ack_and_reopen_only_unconsumed_rows(self):
        e,p=self.entry('a',list(rows()),'gzip');recipe=self.recipe(e);stream=C.CandidateStream(recipe,{e['sha256']:p},'train');db=self.root/'a.sqlite'
        called=[];first=C.DataOnlyConsumer(db,stream);first.consume(lambda row,ev:called.append(row['sample_id']),max_rows=2);first.close()
        second=C.DataOnlyConsumer(db,stream);report=second.consume(lambda row,ev:called.append(row['sample_id']));second.close()
        self.assertEqual(len(set(called)),4);self.assertEqual(len(called),4);self.assertTrue(report['stream_exhausted'])

    def test_handler_failure_does_not_ack_or_lose_row(self):
        e,p=self.entry('a',list(rows()));recipe=self.recipe(e);stream=C.CandidateStream(recipe,{e['sha256']:p},'train');db=self.root/'a.sqlite'
        consumer=C.DataOnlyConsumer(db,stream)
        def fail(row,evidence):raise RuntimeError('interrupted')
        with self.assertRaises(RuntimeError):consumer.consume(fail)
        self.assertEqual(consumer.report()['acknowledged_rows'],0);consumer.close()
        consumer=C.DataOnlyConsumer(db,stream);seen=[];consumer.consume(lambda row,ev:seen.append(row['sample_id']));consumer.close();self.assertEqual(len(seen),4)

    def test_append_only_recipe_migration_keeps_old_seen_and_cursor(self):
        a,pa=self.entry('a',list(rows('a')));b,pb=self.entry('b',list(rows('b')),'zip')
        old=self.recipe(a);new=self.recipe(a,b);paths={a['sha256']:pa,b['sha256']:pb};db=self.root/'a.sqlite'
        first=C.DataOnlyConsumer(db,C.CandidateStream(old,paths,'train'));first.consume(lambda row,ev:None);first.close()
        with self.assertRaisesRegex(ValueError,'recipe'):C.DataOnlyConsumer(db,C.CandidateStream(new,paths,'train'))
        C.DataOnlyConsumer.extend_recipe(db,old,new,'train')
        seen=[];next_consumer=C.DataOnlyConsumer(db,C.CandidateStream(new,paths,'train'));report=next_consumer.consume(lambda row,ev:seen.append(row['sample_id']));next_consumer.close()
        self.assertEqual(len(seen),4);self.assertTrue(all(x.startswith('b:') for x in seen));self.assertEqual(report['acknowledged_rows'],8)
        with self.assertRaisesRegex(ValueError,'prefix'):C.DataOnlyConsumer.extend_recipe(db,new,self.recipe(b,a),'train')

    def test_exact_duplicates_dedup_conflicting_duplicate_fails(self):
        a,pa=self.entry('a',list(rows()));b,pb=self.entry('b',list(rows())+list(rows('new')),'gzip')
        recipe=self.recipe(a,b);stream=C.CandidateStream(recipe,{a['sha256']:pa,b['sha256']:pb},'train')
        c=C.DataOnlyConsumer(self.root/'a.sqlite',stream);result=c.consume(lambda row,ev:None);c.close()
        self.assertEqual(result['acknowledged_rows'],8);self.assertEqual(result['counts']['EXACT_DUPLICATE_SAMPLE'],4)
        modified=list(rows());modified[0]['messages'][2]['content']='changed'
        bad,pbad=self.entry('bad',modified,'zip');r=self.recipe(a,bad)
        c=C.DataOnlyConsumer(self.root/'b.sqlite',C.CandidateStream(r,{a['sha256']:pa,bad['sha256']:pbad},'train'))
        with self.assertRaisesRegex(ValueError,'conflicting duplicate'):c.consume(lambda row,ev:None)
        c.close()

    def test_hash_and_inner_hash_tamper_rejected_before_handler(self):
        e,p=self.entry('a',list(rows()),'zip');recipe=self.recipe(e);bad=deepcopy(e);bad['member_sha256']='a'*64
        called=[]
        with self.assertRaises(ValueError):list(C.CandidateStream(self.recipe(bad),{bad['sha256']:p},'train').iter_with_cursors())
        p.write_bytes(p.read_bytes()+b'tamper')
        c=C.DataOnlyConsumer(self.root/'a.sqlite',C.CandidateStream(recipe,{e['sha256']:p},'train'))
        with self.assertRaises(ValueError):c.consume(lambda row,ev:called.append(row))
        c.close();self.assertEqual(called,[])

    def test_count_mismatch_never_marks_member_complete(self):
        e,p=self.entry('a',list(rows()));e['rows']=5
        c=C.DataOnlyConsumer(self.root/'a.sqlite',C.CandidateStream(self.recipe(e),{e['sha256']:p},'train'))
        with self.assertRaisesRegex(ValueError,'row count'):c.consume(lambda row,ev:None)
        self.assertEqual(c.report()['complete_members'],0);c.close()

    def test_cursor_split_and_protected_scope_rejected(self):
        e,p=self.entry('a',list(rows()));r=self.recipe(e);stream=C.CandidateStream(r,{e['sha256']:p},'train')
        with self.assertRaises(ValueError):list(stream.iter_with_cursors(C.Cursor(stream.identity,'test')))
        with self.assertRaises(ValueError):C.CandidateStream(r,{},None)
        with self.assertRaises(ValueError):self.recipe({**e,'member':'sealed/chat.jsonl','member_sha256':'a'*64})

    def test_missing_or_unknown_split_fails_before_callback(self):
        for i,value in enumerate([None,'train_candidate','evaluation','']):
            items=list(rows('bad'))
            if value is None:items[0].pop('split')
            else:items[0]['split']=value
            entry,path=self.entry('invalid_'+str(i),items)
            called=[]
            consumer=C.DataOnlyConsumer(self.root/(str(i)+'.sqlite'),C.CandidateStream(self.recipe(entry),{entry['sha256']:path},'train'))
            with self.assertRaisesRegex(ValueError,'explicit known split'):
                consumer.consume(lambda row,ev:called.append(row))
            self.assertEqual(consumer.report()['acknowledged_rows'],0);consumer.close();self.assertEqual(called,[])

    def test_real_overlay_applied_without_mutating_raw_split_or_claiming_all_rows(self):
        items=list(rows());e,p=self.entry('a',items,'zip')
        source={'sample_id':'a','case_group_id':'a_group','grade':1,'problem':'Question a','can_solve':True,
            'initial_guidance':['think'],'worked_steps':[],'expected_answer':[],'student_work':None,
            'hints':[{'level':i,'hint':'think','question':'why?'} for i in [1,2,3]]}
        projection=source_projection(source)
        overlay={'source_sample_id':'a','source_raw_row_sha256':'b'*64,'source_binding':{'member_sha256':'c'*64},
            'source_projection':projection,'source_projection_sha256':P.digest(projection),
            'chat_memberships':[{'sample_id':row['sample_id'],'original_chat_canonical_sha256':P.digest(row),'chat_binding':{'member_sha256':e['member_sha256']}} for row in items]}
        op=self.root/'overlay.jsonl';op.write_text(P.canonical(overlay)+'\n',encoding='utf8')
        mp=self.root/'manifest.json';P.save(mp,{'overlay':{'file_name':op.name,'sha256':P.file_hash(op),'bytes':op.stat().st_size}})
        verified=VerifiedSourceHashOverlay(mp,P.file_hash(mp));recipe=self.recipe(e)
        stream=C.CandidateStream(recipe,{e['sha256']:p},'train',verified)
        decorated=list(stream.iter_with_cursors())
        self.assertEqual(len(decorated),4);self.assertTrue(all(row['sourcehash_origin']=='DERIVED_FROM_VERIFIED_PINNED_SOURCE_MEMBER' for row,cursor in decorated))
        self.assertTrue(all('source_row_sha256' not in raw for raw in items))
        self.assertNotEqual(stream.identity,C.CandidateStream(recipe,{e['sha256']:p},'train').identity)
        db=self.root/'overlay_consumer.sqlite'
        first=C.DataOnlyConsumer(db,stream);first.consume(lambda row,ev:None,max_rows=1);first.close()
        changed_overlay=deepcopy(verified);changed_overlay.overlay_sha256='f'*64
        with self.assertRaisesRegex(ValueError,'recipe'):
            C.DataOnlyConsumer(db,C.CandidateStream(recipe,{e['sha256']:p},'train',changed_overlay))
        tamper=deepcopy(verified);tamper.chats[items[0]['sample_id']][1]['chat_binding']['member_sha256']='d'*64
        with self.assertRaises(ValueError):list(C.CandidateStream(recipe,{e['sha256']:p},'train',tamper).iter_with_cursors())


if __name__=='__main__':unittest.main(verbosity=2)
