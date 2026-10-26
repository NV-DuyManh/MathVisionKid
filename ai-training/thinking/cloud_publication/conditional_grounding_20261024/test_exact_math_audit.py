import unittest
from exact_math_audit import audit_claim, audit_text


class ExactMathAuditTests(unittest.TestCase):
    def test_true_inverse_arithmetic(self):
        self.assertEqual(audit_claim("63 + 4 = 67")["verdict"], "true")

    def test_false_percentage_product_and_basis_identity(self):
        self.assertEqual(audit_claim("1.25 * .8 = 1.05")["verdict"], "false")
        claim = audit_claim("1.25*x*.8 = 1.05*x", symbolic_identity=True)
        self.assertEqual(claim["verdict"], "false")
        self.assertEqual(claim["claim_kind"], "polynomial_identity")
        self.assertEqual(claim["comparisons"][0]["rational_left"], {"1": "1"})
        self.assertEqual(audit_claim("125% * 80% = 100%")["verdict"], "true")

    def test_exact_fraction_order_and_chain(self):
        self.assertEqual(audit_claim("9/12 < 7/12")["verdict"], "false")
        self.assertEqual(audit_claim("0 <= 4 < 9")["verdict"], "true")
        self.assertEqual(audit_claim("-2 < -1 < 0")["verdict"], "true")

    def test_decimal_comma_and_percent_are_not_modulo(self):
        self.assertEqual(audit_claim("1,25 × 0,8 = 1")["verdict"], "true")
        self.assertEqual(audit_claim("1 / 25% = 4")["verdict"], "true")
        self.assertEqual(audit_claim("(20+5)% = .25")["verdict"], "true")
        self.assertEqual(audit_claim("25% = .25")["verdict"], "true")
        self.assertEqual(audit_claim("1,000 = 1")["verdict"], "unsupported")
        self.assertEqual(audit_claim("1,2,3 = 1")["verdict"], "unsupported")

    def test_nested_latex_and_span_preservation(self):
        raw = r"Check $\frac{\frac{1}{2}}{\frac{3}{4}} = \frac{2}{3}$ then \(9/12<7/12\)."
        report = audit_text(raw)
        self.assertEqual([c["verdict"] for c in report["claims"]], ["true", "false"])
        for claim in report["claims"]:
            self.assertEqual(raw[claim["start"]:claim["end"]], claim["rawspan"])
        self.assertFalse(report["response_modified"])

    def test_latex_operators_percent_and_negative(self):
        self.assertEqual(audit_claim(r"-3 \times 2 \div 4 = -\frac{3}{2}")["verdict"], "true")
        self.assertEqual(audit_claim(r"25\% \leq 1")["verdict"], "true")
        self.assertEqual(audit_claim(r"\frac{1}{2 = 3")["verdict"], "unsupported")

    def test_units_and_unknown_text_not_deleted(self):
        for raw in ("1 m = 100 cm", "0,6 m² = 60 cm²", r"1\text{m}=100\text{cm}", "Thus 63+4=67", "1e3=1000"):
            with self.subTest(raw=raw):
                result = audit_claim(raw)
                self.assertEqual(result["verdict"], "unsupported")
                self.assertEqual(result["rawspan"], raw)

    def test_injection_and_resource_limits(self):
        for raw in ("__import__('os').system('echo bad')=0", "x.__class__=1", "abs(-1)=1", "1**100000=1", "1//1=1", "9"*25+"=1", "("*17+"1"+")"*17+"=1", "1/0=1", "x/x=1", "2^3=8", "1;print(1)=1"):
            with self.subTest(raw=raw):
                self.assertEqual(audit_claim(raw)["verdict"], "unsupported")

    def test_symbolic_scope_and_no_oracle_claim(self):
        self.assertEqual(audit_claim("(x+1)*(x-1)=x*x-1", symbolic_identity=True)["verdict"], "true")
        self.assertEqual(audit_claim("1.25x*.8=x", symbolic_identity=True)["verdict"], "true")
        self.assertEqual(audit_claim("x=67")["verdict"], "unsupported")
        self.assertEqual(audit_claim("x<1")["verdict"], "unsupported")
        report = audit_text("63+4=67\n1 m=100 cm")
        self.assertEqual([c["verdict"] for c in report["claims"]], ["true", "unsupported"])
        self.assertFalse(report["final_answer_correctness_established"])
        self.assertFalse(report["word_problem_grounding_established"])

    def test_contextual_remainder_and_markdown_ambiguity(self):
        report = audit_text(r"- $14 \div 4 = 3$ dư 2.")
        self.assertEqual(report["claims"][0]["verdict"], "unsupported")
        self.assertIn("remainder", report["claims"][0]["reason"])
        self.assertEqual(audit_text("- 64 - 46 = 18")["claims"][0]["verdict"], "unsupported")
        self.assertEqual(audit_text("-2 = -2")["claims"][0]["verdict"], "true")

    def test_plain_offsets_bind_trimmed_original_with_crlf(self):
        raw = "Heading\r\n  63 + 4 = 67 \t\r\n\t9/12 < 7/12   \r\n"
        claims = audit_text(raw)["claims"]
        self.assertEqual([c["verdict"] for c in claims], ["true", "false"])
        for claim in claims:
            self.assertEqual(raw[claim["start"]:claim["end"]], claim["rawspan"])
        mixed = "1 + $2=2$ 3 = 4"
        for claim in audit_text(mixed)["claims"]:
            self.assertEqual(mixed[claim["start"]:claim["end"]], claim["rawspan"])
        self.assertEqual(audit_text(mixed)["claims"][0]["verdict"], "unsupported")


if __name__ == "__main__":
    unittest.main()
