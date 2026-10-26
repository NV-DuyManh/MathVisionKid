"""Bounded symbolic rational identities, never proof by sampled fact values.

True means the formulas agree wherever both are defined. The caller must still
check the full question contract, units, grounding, and both numeric denominators.
Remainders are accepted only with identical validated AST structure.
"""
import ast
from fractions import Fraction
import re

FIXED_CONSTANTS = frozenset({0, 1, 2, 3, 10, 60, 100, 1000, 3600})
MAX_TERMS = 128
MAX_DEGREE = 16
COEFFICIENT_LIMIT = 10**12


def _checked(poly):
    result = {monomial: Fraction(coefficient) for monomial, coefficient in poly.items() if coefficient}
    if len(result) > MAX_TERMS:
        raise ValueError('POLYNOMIAL_TERM_LIMIT')
    for monomial, coefficient in result.items():
        if len(monomial) > MAX_DEGREE:
            raise ValueError('POLYNOMIAL_DEGREE_LIMIT')
        if abs(coefficient.numerator) > COEFFICIENT_LIMIT or coefficient.denominator > COEFFICIENT_LIMIT:
            raise ValueError('POLYNOMIAL_COEFFICIENT_LIMIT')
    return result


def _add(left, right, sign=1):
    result = dict(left)
    for monomial, coefficient in right.items():
        result[monomial] = result.get(monomial, Fraction(0)) + sign * coefficient
    return _checked(result)


def _multiply(left, right):
    result = {}
    for first, a in left.items():
        for second, b in right.items():
            monomial = tuple(sorted(first + second))
            if len(monomial) > MAX_DEGREE:
                raise ValueError('POLYNOMIAL_DEGREE_LIMIT')
            result[monomial] = result.get(monomial, Fraction(0)) + a * b
            # Fail conservatively before an expansion becomes expensive.
            _checked(result)
    return _checked(result)


def _parse(expression, allowed_refs):
    if type(expression) is not str or not expression.strip() or len(expression) > 240:
        raise ValueError('EXPRESSION_SIZE')
    tree = ast.parse(expression.strip(), mode='eval')
    if sum(1 for _ in ast.walk(tree)) > 80:
        raise ValueError('AST_NODE_LIMIT')

    def validate(node, depth=0):
        if depth > 12:
            raise ValueError('AST_DEPTH_LIMIT')
        if isinstance(node, ast.Name):
            if node.id not in allowed_refs:
                raise ValueError('UNKNOWN_FACT_REFERENCE')
        elif isinstance(node, ast.Constant):
            if type(node.value) is not int or node.value not in FIXED_CONSTANTS:
                raise ValueError('UNAPPROVED_CONSTANT')
        elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod)):
            validate(node.left, depth + 1)
            validate(node.right, depth + 1)
        else:
            raise ValueError('UNSUPPORTED_AST')

    validate(tree.body)
    return tree


def _rational(node):
    one = {(): Fraction(1)}
    if isinstance(node, ast.Name):
        return {(node.id,): Fraction(1)}, one
    if isinstance(node, ast.Constant):
        return _checked({(): Fraction(node.value)}), one
    p, q = _rational(node.left)
    r, s = _rational(node.right)
    if isinstance(node.op, ast.Add):
        numerator, denominator = _add(_multiply(p, s), _multiply(r, q)), _multiply(q, s)
    elif isinstance(node.op, ast.Sub):
        numerator, denominator = _add(_multiply(p, s), _multiply(r, q), -1), _multiply(q, s)
    elif isinstance(node.op, ast.Mult):
        numerator, denominator = _multiply(p, r), _multiply(q, s)
    elif isinstance(node.op, ast.Div):
        if not r:
            raise ValueError('IDENTICALLY_ZERO_DIVISOR')
        numerator, denominator = _multiply(p, s), _multiply(q, r)
    else:
        raise ValueError('REMAINDER_IS_NOT_A_RATIONAL_POLYNOMIAL')
    if not denominator:
        raise ValueError('IDENTICALLY_ZERO_DENOMINATOR')
    return numerator, denominator


def equivalent(candidate, reference, fact_ids):
    """Prove identity for symbolic fact IDs; never accepts fact values as input."""
    try:
        allowed = frozenset(fact_ids)
        if len(allowed) > 100 or any(type(name) is not str or not re.fullmatch(r'f[0-9]{1,2}', name) for name in allowed):
            raise ValueError('INVALID_FACT_IDS')
        left, right = _parse(candidate, allowed), _parse(reference, allowed)
        if any(isinstance(node, ast.Mod) for tree in (left, right) for node in ast.walk(tree)):
            return ast.dump(left, include_attributes=False) == ast.dump(right, include_attributes=False)
        p, q = _rational(left.body)
        r, s = _rational(right.body)
        return _multiply(p, s) == _multiply(r, q)
    except (ValueError, TypeError, SyntaxError, RecursionError, ZeroDivisionError, OverflowError):
        return False


prove_equivalent = equivalent
