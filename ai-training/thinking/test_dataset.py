import copy
from fractions import Fraction
import random
import unittest

import dataset

class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=dataset.build_dataset()

    def test_exact_fraction_and_decimal(self):
        self.assertEqual(dataset.exact('0.1+0.2'),Fraction(3,10))
        self.assertEqual(dataset.exact('1/3+2/5'),Fraction(11,15))
        self.assertEqual(dataset.exact('(20+8)*5/2'),70)

    def test_dangerous_expression_rejected(self):
        for expression in ('__import__("os")','2**100000','x+2','True+1'):
            with self.assertRaises(ValueError): dataset.exact(expression)

    def test_split_and_paraphrase_isolation(self):
        groups={s:{r['split_group_id'] for r in self.rows if r['split']==s} for s in ('train','val','test')}
        self.assertFalse(groups['train']&groups['val'])
        self.assertFalse(groups['train']&groups['test'])
        self.assertFalse(groups['val']&groups['test'])
        for r in self.rows:
            if r['target']['status']=='solved':
                self.assertIn(r['variant'], (0,1) if r['split']=='train' else (2,) if r['split']=='val' else (3,))

    def test_commutative_families_have_one_split(self):
        groups={}
        for r in self.rows:
            if r['topic'] in ('add_join','add_books','rectangle_area'):
                key=(r['topic'],tuple(sorted(r['parameters'])))
                self.assertEqual(groups.setdefault(key,r['split']),r['split'])

    def test_wrong_step_and_final_rejected(self):
        rows=copy.deepcopy(self.rows)
        rows[0]['target']['steps'][0]['result']='999'
        with self.assertRaises(AssertionError): dataset.validate(rows)
        rows=copy.deepcopy(self.rows)
        rows[0]['target']['answer']='999'
        with self.assertRaises(AssertionError): dataset.validate(rows)

    def test_scope_does_not_invent_answer(self):
        rows=[r for r in self.rows if r['target']['status']!='solved']
        self.assertTrue(rows)
        for r in rows: self.assertNotIn('answer',r['target'])

    def test_teacher_provenance_not_fabricated(self):
        self.assertTrue(all(r['human_verified'] is False for r in self.rows))
        self.assertEqual({r['grade'] for r in self.rows if r['grade']},set(range(1,6)))
        self.assertEqual(len({r['topic'] for r in self.rows if r['target']['status']=='solved'}),12)

    def test_semantic_oracles(self):
        rng=random.Random(9)
        for topic in dataset.TOPICS:
            params,grade,unit,questions,steps,key=dataset.make_case(topic,rng)
            self.assertEqual(dataset.exact(steps[-1][1]),key)
            if topic=='sub_remaining': self.assertLess(key,params[0])
            if topic=='sum_difference': self.assertEqual(key*2,params[0]+params[1])
            if topic=='trapezoid_area': self.assertEqual(key*2,(params[0]+params[1])*params[2])

    def test_repeatable_data(self):
        self.assertEqual(self.rows,dataset.build_dataset())

if __name__=='__main__': unittest.main()
