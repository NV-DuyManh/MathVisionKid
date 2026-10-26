"""Bounded, stdlib-only audit of explicit arithmetic claims, never answer grading.

No eval, model calls, app imports, response rewriting, unit conversion, or oracle.
Symbolic equality is interpreted ONLY as a polynomial identity, not an equation
to solve. A true identity does not prove the quantities match a word problem.
"""
from __future__ import annotations

import ast
import json
import re
from fractions import Fraction

MAX_CLAIM = 512
MAX_TEXT = 100_000
MAX_DEPTH = 16
MAX_NODES = 160
MAX_DEGREE = 4
MAX_BITS = 192
MAX_DIGITS = 24


class Unsupported(ValueError):
    pass


def _latex(s: str, depth: int = 0) -> str:
    if depth > MAX_DEPTH:
        raise Unsupported("LaTeX nesting limit")
    def group(pos):
        if pos >= len(s) or s[pos] != "{":
            raise Unsupported("fraction requires braced numerator and denominator")
        level = 1
        for end in range(pos + 1, len(s)):
            level += (s[end] == "{") - (s[end] == "}")
            if level > MAX_DEPTH:
                raise Unsupported("LaTeX nesting limit")
            if level == 0:
                return s[pos + 1:end], end + 1
        raise Unsupported("unclosed LaTeX group")
    out, i = [], 0
    while i < len(s):
        match = re.match(r"\\(?:dfrac|tfrac|frac)\s*", s[i:])
        if match:
            numerator, pos = group(i + len(match.group()))
            while pos < len(s) and s[pos].isspace():
                pos += 1
            denominator, i = group(pos)
            out.append("((" + _latex(numerator, depth + 1) + ")/(" + _latex(denominator, depth + 1) + "))")
        else:
            out.append(s[i])
            i += 1
    s = "".join(out)
    replacements = {
        r"\times": "*", r"\cdot": "*", r"\div": "/",
        r"\leq": "<=", r"\geq": ">=", r"\le": "<=", r"\ge": ">=",
        r"\neq": "!=", r"\ne": "!=", r"\%": "%",
        r"\left": "", r"\right": "", r"\,": " ", r"\;": " ", r"\!": " ",
    }
    # Match commands as tokens, never convert prefixes of unknown commands.
    s = re.sub(r"\\[A-Za-z]+|\\[%!,;]", lambda m: replacements.get(m.group(), m.group()), s)
    return s


def _bounded(poly):
    poly = {degree: value for degree, value in poly.items() if value}
    if len(poly) > MAX_DEGREE + 1 or any(d > MAX_DEGREE for d in poly):
        raise Unsupported("polynomial degree limit")
    if any(max(abs(v.numerator).bit_length(), v.denominator.bit_length()) > MAX_BITS for v in poly.values()):
        raise Unsupported("rational size limit")
    return poly


def _add(a, b, sign=1):
    result = dict(a)
    for degree, value in b.items():
        result[degree] = result.get(degree, Fraction()) + sign * value
    return _bounded(result)


def _mul(a, b):
    result = {}
    for da, va in a.items():
        for db, vb in b.items():
            result[da + db] = result.get(da + db, Fraction()) + va * vb
    return _bounded(result)


def _prepare(raw):
    if not isinstance(raw, str) or not raw.strip() or len(raw) > MAX_CLAIM:
        raise Unsupported("empty claim or claim length limit")
    s = _latex(raw.strip())
    s = s.translate(str.maketrans({"−": "-", "–": "-", "×": "*", "÷": "/", ":": "/", "≤": "<=", "≥": ">=", "≠": "!="}))
    if "**" in s or "//" in s:
        raise Unsupported("powers and floor division unsupported")
    token_pattern = re.compile(r"\s+|(?:\d+(?:[.,]\d+)?|\.\d+)|<=|>=|!=|==|[x()+*/%<>=-]")
    tokens, numbers, pos = [], {}, 0
    for match in token_pattern.finditer(s):
        if match.start() != pos:
            raise Unsupported("unknown text, unit, command, or code")
        pos = match.end()
        token = match.group()
        if token.isspace():
            continue
        if token[0].isdigit() or token.startswith("."):
            if sum(c.isdigit() for c in token) > MAX_DIGITS:
                raise Unsupported("number length limit")
            if "," in token:
                whole, decimal = token.split(",")
                if len(decimal) == 3 and 1 <= len(whole) <= 3 and whole != "0":
                    raise Unsupported("ambiguous decimal comma/thousands grouping")
                token = token.replace(",", ".")
            key = "n" + str(len(numbers))
            numbers[key] = Fraction(token)
            tokens.append(key)
        else:
            tokens.append(token)
    if pos != len(s):
        raise Unsupported("unknown text, unit, command, or code")
    # Comma-separated lists are not decimal arithmetic.
    if re.search(r"\d,\d+,", s):
        raise Unsupported("ambiguous comma list")
    level = 0
    for token in tokens:
        level += (token == "(") - (token == ")")
        if level < 0 or level > MAX_DEPTH:
            raise Unsupported("parenthesis nesting limit or mismatch")
    if level:
        raise Unsupported("parenthesis mismatch")
    # Convert each postfix percent by wrapping its complete immediate operand.
    i = 0
    while i < len(tokens):
        if tokens[i] != "%":
            i += 1
            continue
        if i == 0 or i + 1 < len(tokens) and tokens[i + 1] == "%":
            raise Unsupported("invalid percent")
        start = i - 1
        if tokens[start] == ")":
            nesting = 1
            start -= 1
            while start >= 0:
                nesting += (tokens[start] == ")") - (tokens[start] == "(")
                if nesting == 0:
                    break
                start -= 1
        elif tokens[start] not in numbers and tokens[start] != "x":
            raise Unsupported("percent requires a numerical operand")
        if start < 0:
            raise Unsupported("invalid percent operand")
        key = "n" + str(len(numbers))
        numbers[key] = Fraction(100)
        replacement = ["("] + tokens[start:i] + ["/", key, ")"]
        tokens[start:i + 1] = replacement
        i = start + len(replacement)
    # Conventional numerical coefficient followed by x is unambiguous.
    expanded = []
    for token in tokens:
        if expanded and token == "x" and (expanded[-1] in numbers or expanded[-1] == ")"):
            expanded.append("*")
        expanded.append(token)
    prepared = " ".join(expanded)
    def display_token(token):
        if token not in numbers:
            return token
        value = numbers[token]
        return str(value) if value.denominator == 1 else "(" + str(value) + ")"
    normalized = " ".join(display_token(t) for t in expanded)
    return prepared, normalized, numbers


def _poly(node, numbers, depth=0):
    if depth > MAX_DEPTH:
        raise Unsupported("AST depth limit")
    if isinstance(node, ast.Name):
        if node.id == "x":
            return {1: Fraction(1)}
        if node.id in numbers:
            return _bounded({0: numbers[node.id]})
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _poly(node.operand, numbers, depth + 1)
        return {d: (-v if isinstance(node.op, ast.USub) else v) for d, v in value.items()}
    if isinstance(node, ast.BinOp):
        left, right = _poly(node.left, numbers, depth + 1), _poly(node.right, numbers, depth + 1)
        if isinstance(node.op, ast.Add):
            return _add(left, right)
        if isinstance(node.op, ast.Sub):
            return _add(left, right, -1)
        if isinstance(node.op, ast.Mult):
            return _mul(left, right)
        if isinstance(node.op, ast.Div):
            if any(d != 0 for d in right) or not right.get(0):
                raise Unsupported("division by zero or variable expression")
            return _bounded({d: v / right[0] for d, v in left.items()})
    raise Unsupported("AST node/operator not allowed")


def _describe(poly):
    if not any(d for d in poly):
        return str(poly.get(0, Fraction()))
    return {str(d): str(v) for d, v in sorted(poly.items())}


def audit_claim(rawspan: str, *, symbolic_identity: bool = False) -> dict:
    result = {"rawspan": rawspan, "normalized": None, "verdict": "unsupported"}
    try:
        prepared, normalized, numbers = _prepare(rawspan)
        result["normalized"] = normalized
        parts = re.split(r"(<=|>=|!=|==|=|<|>)", prepared)
        if len(parts) < 3 or len(parts) % 2 == 0 or any(not p.strip() for p in parts):
            raise Unsupported("requires a complete explicit comparison")
        values = []
        for expression in parts[::2]:
            tree = ast.parse(expression.strip(), mode="eval")
            if sum(1 for _ in ast.walk(tree)) > MAX_NODES:
                raise Unsupported("AST node limit")
            values.append(_poly(tree.body, numbers))
        symbolic = "x" in re.findall(r"\b[a-z]+\b", prepared)
        if symbolic and not symbolic_identity:
            raise Unsupported("symbolic expression requires explicit polynomial-identity opt-in; equation solving unsupported")
        checks = []
        for index, operator in enumerate(parts[1::2]):
            left, right = values[index:index + 2]
            entry = {"operator": operator, "rational_left": _describe(left), "rational_right": _describe(right)}
            if symbolic:
                if operator not in ("=", "=="):
                    raise Unsupported("variable inequalities/equation solving unsupported")
                truth = left == right
                entry["interpretation"] = "polynomial identity for every x; not equation solving"
                if not truth:
                    entry["correction"] = {"left_coefficients": _describe(left), "right_coefficients": _describe(right)}
            else:
                a, b = left.get(0, Fraction()), right.get(0, Fraction())
                truth = {"=": a == b, "==": a == b, "!=": a != b, "<": a < b, ">": a > b, "<=": a <= b, ">=": a >= b}[operator]
                if not truth:
                    entry["correction"] = {"actual_left": str(a), "actual_right": str(b), "true_relation": "=" if a == b else "<" if a < b else ">"}
            entry["verdict"] = "true" if truth else "false"
            checks.append(entry)
        result.update(verdict="true" if all(c["verdict"] == "true" for c in checks) else "false", claim_kind="polynomial_identity" if symbolic else "numerical_relation", comparisons=checks)
    except (Unsupported, SyntaxError, ValueError, OverflowError, RecursionError) as exc:
        result["reason"] = str(exc)
    return result


_SPANS = re.compile(r"\$\$(.*?)\$\$|(?<!\\)\$([^$\n]+?)(?<!\\)\$|\\\((.*?)\\\)|\\\[(.*?)\\\]", re.S)
_COMPARISON = re.compile(r"[=<>≤≥≠]|\\(?:leq?|geq?|neq?|ne)\b")


def audit_text(text: str, *, symbolic_identity: bool = False) -> dict:
    if not isinstance(text, str) or len(text) > MAX_TEXT:
        raise ValueError("response must be text within length limit")
    claims, occupied = [], []
    for match in _SPANS.finditer(text):
        content = next(g for g in match.groups() if g is not None)
        if _COMPARISON.search(content):
            audited = audit_claim(content, symbolic_identity=symbolic_identity)
            # A printed quotient followed by an out-of-span remainder is not
            # a standalone rational equality. Do not discard that context.
            suffix = text[match.end():].split("\n", 1)[0]
            if re.match(r"\s*(?:dư|remainder)\b", suffix, re.I):
                audited = {"normalized": audited["normalized"], "verdict": "unsupported",
                           "reason": "out-of-span remainder notation requires contextual interpretation"}
            audited.update(rawspan=match.group(), start=match.start(), end=match.end(), extracted_content=content)
            claims.append(audited)
        occupied.append((match.start(), match.end()))
    # Blank complete math spans so plain-line extraction never duplicates them.
    remainder = list(text)
    for start, end in occupied:
        for i in range(start, end):
            if remainder[i] != "\n":
                remainder[i] = " "
    position = 0
    for line in "".join(remainder).splitlines(keepends=True):
        if _COMPARISON.search(line):
            content = line.strip()
            start = position + len(line) - len(line.lstrip())
            end = start + len(content)
            rawspan = text[start:end]
            if any(left < end and right > start for left, right in occupied):
                audited = {"rawspan": rawspan, "normalized": None, "verdict": "unsupported",
                           "reason": "mixed plain-text claim and delimited math; context cannot be silently removed"}
            else:
                audited = audit_claim(rawspan, symbolic_identity=symbolic_identity)
            if re.match(r"^-\s+", content):
                audited = {"rawspan": rawspan, "normalized": None, "verdict": "unsupported",
                           "reason": "ambiguous Markdown bullet versus unary minus; use a delimited math span"}
            audited.update(start=start, end=end)
            claims.append(audited)
        position += len(line)
    claims.sort(key=lambda c: c["start"])
    return {"schema": "MathVisionKid.explicit_math_audit.v1", "claims": claims,
            "scope": "Only extracted explicit arithmetic relations/polynomial identities; unsupported claims remain unverified.",
            "final_answer_correctness_established": False, "word_problem_grounding_established": False,
            "response_modified": False, "symbolic_identity_opt_in": symbolic_identity}


if __name__ == "__main__":
    import sys
    print(json.dumps(audit_text(sys.stdin.read(MAX_TEXT + 1)), ensure_ascii=False, indent=2))
