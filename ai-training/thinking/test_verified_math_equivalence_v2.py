"""Symbolic identity and adversarial resource-bound regression tests."""
import unittest
from verified_math_equivalence_v2 import equivalent


class EquivalenceTests(unittest.TestCase):
    refs = ['f0', 'f1', 'f2', 'f3']

    def test_commutativity_association_and_distributivity(self):
        for left, right in (
            ('f0+f1', 'f1+f0'), ('f0*f1', 'f1*f0'),
            ('(f0+f1)+f2', 'f0+(f1+f2)'),
            ('(f0*f1)*f2', 'f0*(f1*f2)'),
            ('f0*(f1+f2)', 'f0*f1+f0*f2'),
            ('f0-(f1-f2)', '(f0-f1)+f2'),
            ('(f0+f1)*2', 'f0+f0+f1+f1'),
            ('f0*f1/100', 'f0/100*f1'),
            ('(f0+f1)/f2', 'f0/f2+f1/f2'),
            ('(f0+f1+f2)/3', '(f2+f0+f1)/(1+2)'),
        ):
            with self.subTest(left=left, right=right):
                self.assertTrue(equivalent(left, right, self.refs))

    def test_no_sampled_value_or_numeric_collision_proof(self):
        self.assertFalse(equivalent('f0*f1', 'f0+f1', self.refs))  # Both are 4 at f0=f1=2.
        self.assertFalse(equivalent('f0', '2', self.refs))
        self.assertFalse(equivalent('f0-f1', 'f1-f0', self.refs))
        self.assertFalse(equivalent('f0/f1', 'f1/f0', self.refs))
        self.assertFalse(equivalent('f0+f1', 'f0+f2', self.refs))
        self.assertFalse(equivalent('f0+f1', 'f0+f1', [{'id': 'f0', 'value': 2}]))

    def test_remainder_requires_identical_ast_structure(self):
        self.assertTrue(equivalent('f0 % f1', '(f0%f1)', self.refs))
        self.assertTrue(equivalent('(f0%f1)+f2', '(f0%f1)+f2', self.refs))
        self.assertFalse(equivalent('(f0%f1)+f2', 'f2+(f0%f1)', self.refs))
        self.assertFalse(equivalent('f0%f1', 'f1%f0', self.refs))
        self.assertFalse(equivalent('f0%f1', 'f0/f1', self.refs))

    def test_unknown_names_unsafe_nodes_and_literals_rejected(self):
        for expression in ('f99', 'x', '__import__("os")', 'f0.__class__', 'f0[0]',
                           'f0**2', 'f0//f1', '-f0', 'True', '1.0', '4', '"f0"', '[f0]',
                           'lambda: f0', 'f0 if f1 else f2'):
            with self.subTest(expression=expression):
                self.assertFalse(equivalent(expression, expression, self.refs))
        self.assertFalse(equivalent('f0', 'f0', ['x']))
        self.assertFalse(equivalent('f0', 'f0', None))

    def test_zero_denominator_never_proves_invalid_expression(self):
        self.assertFalse(equivalent('f0/0', 'f0/0', self.refs))
        self.assertFalse(equivalent('f0/(f1-f1)', 'f0/(f1-f1)', self.refs))
        # This is an identity only where f0 is nonzero. Numeric gating of both
        # expressions remains mandatory in the caller.
        self.assertTrue(equivalent('f0/f0', '1', self.refs))

    def test_size_depth_degree_terms_and_coefficients_fail_closed(self):
        self.assertFalse(equivalent(' ' * 241 + 'f0', 'f0', self.refs))
        deep = 'f0+' * 14 + 'f1'
        self.assertFalse(equivalent(deep, deep, self.refs))
        def balanced(parts):
            if len(parts) == 1:
                return parts[0]
            midpoint = len(parts) // 2
            return '(' + balanced(parts[:midpoint]) + '*' + balanced(parts[midpoint:]) + ')'
        degree = balanced(['f0'] * 17)
        self.assertFalse(equivalent(degree, degree, self.refs))
        expansion = '*'.join('(' + '+'.join('f' + str(i) for i in range(start, start + 6)) + ')'
                             for start in (0, 6, 12))
        self.assertFalse(equivalent(expansion, expansion, ['f' + str(i) for i in range(18)]))
        coefficient = 'f0*1000*1000*1000*1000*1000'
        self.assertFalse(equivalent(coefficient, coefficient, self.refs))


if __name__ == '__main__':
    unittest.main()
