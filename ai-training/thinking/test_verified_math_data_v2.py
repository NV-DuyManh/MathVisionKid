import ast
from collections import Counter
from fractions import Fraction
import hashlib
import json
import pytest
from verified_math_data_v2 import (build, export, prompt, evaluate_expression,
                                  source_number, verify_expression, parse_plan)

@pytest.fixture(scope='module')
def rows():
    return build()

def test_full_dataset_has_independent_oracles_and_balanced_grade_split(rows):
    assert Counter(r['split'] for r in rows)=={'train':2000,'val':160,'test':160}
    assert len({r['topic'] for r in rows if r['target']['status']=='solve'})==24
    for split,each in [('train',400),('val',32),('test',32)]:
        assert Counter(r['grade'] for r in rows if r['split']==split)=={g:each for g in range(1,6)}
    for row in rows:
        if row['target']['status']=='solve':
            assert evaluate_expression(row['target']['expr'],row['facts'])==Fraction(row['oracle_answer'])
        else:assert row['oracle_answer'] is None
        assert not row['human_verified']

def test_source_spans_are_occurrence_order_and_canonical_numbers(rows):
    reordered=0;fractions=0;decimals=0
    for row in rows:
        previous=-1
        for i,fact in enumerate(row['facts']):
            start,end=fact['span'];assert start>previous;previous=end
            assert fact['id']=='f'+str(i)
            assert row['problem'][start:end]==fact['quote']
            assert source_number(fact['quote'])==Fraction(fact['value'])
            fractions+='/' in fact['quote'];decimals+=',' in fact['quote']
        if row['topic']=='missing_addend' and row['template_variant']==2:
            assert row['target']['expr']=='f0-f1';reordered+=1
    assert reordered and fractions and decimals

def test_templates_numeric_semantic_cases_and_questions_do_not_leak(rows):
    for key in ('wording_family','numeric_case_group','problem','sample_id'):
        partitions=[{r[key] for r in rows if r['split']==split} for split in ('train','val','test')]
        assert not partitions[0]&partitions[1]
        assert not partitions[0]&partitions[2]
        assert not partitions[1]&partitions[2]
    assert len({r['numeric_case_group'] for r in rows})==len(rows)

def test_prompt_only_contains_problem_grade_fact_ids_values_units(rows):
    for row in rows:
        data=json.loads(prompt(row))
        assert set(data)=={'grade','problem','facts'}
        assert data['problem']==row['problem']
        assert all(set(f)=={'id','value','unit'} for f in data['facts'])
        assert not {'target','topic','oracle_answer','expected_answer','status','expr'}&set(data)

@pytest.mark.parametrize('text,result',[('3,25',Fraction(13,4)),('2/3',Fraction(2,3)),('0',Fraction(0)),('12',Fraction(12))])
def test_vietnamese_decimal_and_fraction_source_not_float(text,result):
    assert source_number(text)==result

@pytest.mark.parametrize('text',['1.000','1 000','NaN','-3','3,25,1','½','__import__("os")'])
def test_ambiguous_or_unsupported_source_numbers_reject(text):
    with pytest.raises(ValueError):source_number(text)

def test_exact_fraction_arithmetic_and_integer_remainder():
    facts=[{'id':'f0','value':'2/3'},{'id':'f1','value':'3/7'}]
    assert evaluate_expression('f0+f1',facts)==Fraction(23,21)
    assert evaluate_expression('f0*f1',facts)==Fraction(2,7)
    assert evaluate_expression('f0/f1',facts)==Fraction(14,9)
    assert evaluate_expression('f0-f1',facts)==Fraction(5,21)
    assert evaluate_expression('f0%f1',[{'id':'f0','value':'25'},{'id':'f1','value':'4'}])==1
    with pytest.raises(ValueError):evaluate_expression('f0%f1',facts)
    with pytest.raises(ValueError):evaluate_expression('f0/f1',[{'id':'f0','value':'1'},{'id':'f1','value':'0'}])

@pytest.mark.parametrize('expr',["__import__('os').system('echo x')",'f0.__class__','f0[0]',
    '[f0 for x in range(9)]','f0**2','f0//2','-f0','f99+f0','f0+777','True','1.5','f0×f1','f0−f1',
    '('*150+'f0'+')'*150,'+'.join(['f0']*100)])
def test_unsafe_or_unapproved_ast_reject(expr):
    with pytest.raises(ValueError):evaluate_expression(expr,[{'id':'f0','value':'7'},{'id':'f1','value':'3'}])

def test_malformed_fact_metadata_cannot_supply_values():
    for facts in [[{'id':'f0','foo':'1'}],[{'id':'f0','value':True}],
                  [{'id':'f0','value':'1'},{'id':'f0','value':'2'}],[{'id':'role_initial','value':'1'}]]:
        with pytest.raises(ValueError):evaluate_expression('f0',facts)

def test_semantic_contract_rejects_accidental_right_answer_or_wrong_unit(rows):
    row=next(r for r in rows if r['topic']=='rectangle_area')
    assert verify_expression(row,row['target'])['accepted']
    wrong=dict(row['target'],unit='cm')
    assert not verify_expression(row,wrong)['accepted']
    # Commutation is arithmetically valid but strict plan match is deliberately
    # conservative; the training evaluator must credit numeric answers separately.
    reverse=dict(row['target'],expr='f1*f0')
    assert evaluate_expression(reverse['expr'],row['facts'])==Fraction(row['oracle_answer'])
    result=verify_expression(row,reverse)
    assert not result['accepted'] and result['reason']=='TEMPLATE_SEMANTIC_PLAN_MISMATCH'
    guard=next(r for r in rows if r['target']['status']=='clarify')
    assert not verify_expression(guard,{'status':'solve','expr':'f0','unit':'viên'})['accepted']

def test_duplicate_keys_nonfinite_and_unfinished_thought_reject():
    for text in ['{"status":"solve","status":"clarify","expr":null,"unit":null}',
                 '{"status":"solve","expr":NaN,"unit":""}',
                 '<think>{"status":"solve","expr":"f0","unit":""}']:
        with pytest.raises((ValueError,json.JSONDecodeError)):parse_plan(text)

def test_export_is_byte_deterministic_with_verified_hashes(tmp_path):
    a,b=tmp_path/'a',tmp_path/'b'
    report=export(a);assert report==export(b)
    for split,expected in report['fingerprints'].items():
        assert (a/(split+'.jsonl')).read_bytes()==(b/(split+'.jsonl')).read_bytes()
        assert hashlib.sha256((a/(split+'.jsonl')).read_bytes()).hexdigest()==expected
