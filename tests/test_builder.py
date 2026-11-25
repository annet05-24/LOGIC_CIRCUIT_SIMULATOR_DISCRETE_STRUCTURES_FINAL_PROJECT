"""Tests for the rules of the logic builder (no window needed)."""
import unittest

from logic_sim.ui.builder import can_add, tokenize

ALL = ["A", "B", "AND", "OR", "NOT", "->", "(", ")"]


def allowed(tokens):
    """Every symbol that may come next."""
    return [t for t in ALL if can_add(tokens, t)]


class TestBuilderRules(unittest.TestCase):
    def test_tokenize_splits_brackets_and_arrows(self):
        self.assertEqual(tokenize("(A AND B)"), ["(", "A", "AND", "B", ")"])
        self.assertEqual(tokenize("A->B"), ["A", "->", "B"])
        self.assertEqual(tokenize("  "), [])

    def test_at_the_start(self):
        self.assertEqual(allowed([]), ["A", "B", "NOT", "("])

    def test_after_a_variable(self):
        self.assertEqual(allowed(["A"]), ["AND", "OR", "->"])

    def test_after_a_binary_operator(self):
        self.assertEqual(allowed(["A", "AND"]), ["A", "B", "NOT", "("])

    def test_after_not(self):
        self.assertEqual(allowed(["NOT"]), ["A", "B", "NOT", "("])

    def test_closing_bracket_needs_an_open_one(self):
        self.assertNotIn(")", allowed(["A"]))
        self.assertIn(")", allowed(["(", "A"]))
        self.assertNotIn(")", allowed(["(", "A", ")"]))

    def test_after_a_closing_bracket(self):
        self.assertEqual(allowed(["(", "A", ")"]), ["AND", "OR", "->"])

    def test_after_an_opening_bracket(self):
        self.assertEqual(allowed(["("]), ["A", "B", "NOT", "("])

    def test_a_full_expression_can_be_built_symbol_by_symbol(self):
        built = []
        for token in ["(", "A", "AND", "B", ")", "OR", "NOT", "A"]:
            self.assertTrue(can_add(built, token), token + " after " + str(built))
            built.append(token)

    def test_double_operator_is_blocked(self):
        self.assertFalse(can_add(["A", "AND"], "AND"))
        self.assertFalse(can_add(["A", "AND"], "OR"))


if __name__ == "__main__":
    unittest.main()