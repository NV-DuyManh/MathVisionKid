"""Run in the existing Colab kernel. Read exact train rows and metadata only."""
import ast,json,hashlib,sqlite3
from fractions import Fraction
from decimal import Decimal
from datetime import datetime,timezone

def _fraction_expression(text):
    def walk(n):
        if isinstance(n,ast.Constant) and type(n.value) in (int,float):
            return Fraction(ast.get_source_segment(text,n))
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.USub):return -walk(n.operand)
        assert isinstance(n,ast.BinOp)
        a,b=walk(n.left),walk(n.right)
        if isinstance(n.op,ast.Add):return a+b
        if isinstance(n.op,ast.Sub):return a-b
        if isinstance(n.op,ast.Mult):return a*b
        if isinstance(n.op,ast.Div):return a/b
        if isinstance(n.op,ast.Mod):return a%b
        raise ValueError('Unsupported independent oracle expression')
    return walk(ast.parse(text,mode='eval').body)

_dir=ROOT/'crosssplit_20261023/pinned_metadata'
_review_bytes=(_dir/'train17_semantic_review.json').read_bytes()
_cross_bytes=(_dir/'signature_crosswalk.json').read_bytes()
_policy_bytes=(_dir/'numeric_overlap_exception_policy.json').read_bytes()
_diagnostic_bytes=(_dir/'diagnostic.json').read_bytes()
_review=json.loads(_review_bytes);_cross=json.loads(_cross_bytes)
_selected={x['case_id']:x for x in _cross['matches'] if x['source_split']=='train_candidate' and x['linked_samples']}
assert len(_selected)==17 and set(_selected)==set(_crosssplit_train_rows)
assert json.loads(_policy_bytes)['owner_authorized'] is True
assert hashlib.sha256(_policy_bytes).hexdigest()=='c9aa008fb84b81e705e540c56d018c9c2d07278edc775fba57a6d28a2309e472'
_qa={x['sample_id']:x for x in _review['rows']};assert set(_qa)==set(_selected)
_checked=[];_eval_meta=[]
with sqlite3.connect(V3_DB.as_uri()+'?mode=ro',uri=True,timeout=30) as _d:
    _d.execute('PRAGMA query_only=ON')
    assert _d.execute('SELECT count(*) FROM members WHERE complete=1 AND next_line=expected_rows').fetchone()[0]==251
    assert _d.execute('SELECT count(*) FROM samples').fetchone()[0]==6502392
    assert _d.execute("SELECT count(*) FROM issues WHERE kind='CROSS_SPLIT_QUESTION'").fetchone()[0]==0
    assert _d.execute("SELECT count(*) FROM issues WHERE kind='CROSS_SPLIT_GROUP'").fetchone()[0]==0
    for sid,pin in sorted(_selected.items()):
        row=_crosssplit_train_rows[sid];qa=_qa[sid]
        assert audit_v3.digest(row)==pin['canonical_sha256']==qa['source_canonical_sha256']
        assert pin['raw_sha256']==qa['source_raw_sha256']
        actual=_d.execute('SELECT canonical_sha,signatures,source_split FROM source_versions WHERE id=? AND raw_sha=?',(sid,pin['raw_sha256'])).fetchone()
        assert actual and actual[0]==pin['canonical_sha256'] and actual[2]=='train_candidate'
        assert json.loads(actual[1])==audit_v3.L.source_signatures(row)
        assert row['student_work'] is None
        a,b=(Fraction(x['value']) for x in row['givens'])
        da,db=(Decimal(x['value']) for x in row['givens'])
        op=sid.split('_')[2]
        if op=='add':expected=[a+b];decimal=[da+db]
        elif op=='sub':expected=[a-b];decimal=[da-db]
        elif op=='mul':
            expected=[sum((a for _ in range(int(b))),Fraction(0))];decimal=[da*db]
            assert expected[0]==(a//10*10*b+(a%10)*b)
        elif op=='div':
            remaining=a;q=0
            while remaining>=b:remaining-=b;q+=1
            expected=[Fraction(q),remaining];decimal=[da//db,da%db]
            assert expected[0]*b+expected[1]==a and 0<=expected[1]<b
        else:raise ValueError('Unexpected exact train source operation')
        answers=[Fraction(x['result']) for x in row['expected_answer']]
        assert answers==expected==[Fraction(x) for x in decimal]
        assert [str(x) for x in expected]==qa['expected_results_independently_checked']
        for step in row['worked_steps']:
            if step.get('expression') is not None:
                assert _fraction_expression(step['expression'])==Fraction(step['result'])
        assert len(row['hints'])==3 and {h['level'] for h in row['hints']}=={1,2,3}
        expected_chat={x['sample_id']:x for x in pin['linked_samples']}
        chat=[]
        for x in _d.execute('SELECT s.id,s.mode,s.split,s.canonical_sha,o.raw_sha,s.source_raw_sha,s.linkage,s.sequence_tokens,s.completion_tokens FROM samples s JOIN occurrences o ON s.id=o.sample_id WHERE s.case_id=? ORDER BY s.id',(sid,)):
            sample,mode,split,canon,raw,source_raw,linkage,seq,completion=x
            assert sample in expected_chat and canon==expected_chat[sample]['canonical_sha256']
            assert mode==expected_chat[sample]['mode'] and split=='train' and source_raw==pin['raw_sha256'] and linkage==1
            assert 0<completion<=seq<=40960
            chat.append(dict(sample_id=sample,mode=mode,split=split,chat_raw_sha256=raw,chat_canonical_sha256=canon,source_raw_sha256=source_raw,linkage=linkage,sequence_tokens=seq,completion_tokens=completion))
        assert len(chat)==4 and len({x['mode'] for x in chat})==4
        _checked.append(dict(case_id=sid,source_raw_sha256=pin['raw_sha256'],source_canonical_sha256=pin['canonical_sha256'],source_signature_metadata_verified=True,oracle_passed=True,chat_bindings=chat))
    for pin in _cross['matches']:
        if pin['source_split'] not in ('validation','test'):continue
        found=_d.execute('SELECT canonical_sha,source_split,signatures FROM source_versions WHERE id=? AND raw_sha=?',(pin['case_id'],pin['raw_sha256'])).fetchone()
        assert found and found[0]==pin['canonical_sha256'] and found[1]==pin['source_split']
        _eval_meta.append(dict(case_id=pin['case_id'],source_raw_sha256=pin['raw_sha256'],source_canonical_sha256=pin['canonical_sha256'],split=pin['source_split'],signatures=json.loads(found[2])))
assert len(_eval_meta)==6
evidence=dict(schema='MathVisionKid.CurrentRecipeNumericOverlap17MachineEvidence.v1',observed_utc=datetime.now(timezone.utc).isoformat(),source_rows=17,chat_rows=68,all_fraction_decimal_oracles_passed=True,all_current_recipe_members_complete=True,current_normalized_question_conflicts=0,current_group_conflicts=0,numeric_expression_disjoint=False,source_chat_payload_bytes_changed=0,splits_changed=0,question_or_solution_text_of_eval_read=False,policy_sha256=hashlib.sha256(_policy_bytes).hexdigest(),semantic_review_sha256=hashlib.sha256(_review_bytes).hexdigest(),signature_crosswalk_sha256=hashlib.sha256(_cross_bytes).hexdigest(),diagnostic_sha256=hashlib.sha256(_diagnostic_bytes).hexdigest(),train_rows=_checked,current_eval_sources=_eval_meta,training_started=False,TRAINING_DATASET_READY=False,new_human_signoffs=0,scope='CURRENT_RECIPE_ONLY')
_machine_bytes=(json.dumps(evidence,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
(_dir/'train17_numeric_overlap_machine_evidence.json').write_bytes(_machine_bytes)
print(json.dumps(evidence,ensure_ascii=False))
