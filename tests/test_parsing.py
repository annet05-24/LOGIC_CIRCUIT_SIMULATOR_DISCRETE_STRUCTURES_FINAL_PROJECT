import unittest
from logic_sim.parsing import ExpressionError, parse, truth_table


class TestMemberOneParser(unittest.TestCase):
    def test_precedence(self):
        ast = parse("A OR B AND NOT C")
        self.assertEqual(ast["type"], "OR")
        self.assertEqual(ast["right"]["type"], "AND")

    def test_parentheses(self):
        ast = parse("(A OR B) AND C")
        self.assertEqual(ast["type"], "AND")
        self.assertEqual(ast["left"]["type"], "OR")

    def test_symbols(self):
        self.assertEqual(truth_table(parse("A & B"))["rows"][-1]["output"], 1)
        self.assertEqual(truth_table(parse("NOT A"))["rows"][0]["output"], 1)

    def test_implication_is_rewritten(self):
        ast = parse("A -> B")
        self.assertEqual(ast["type"], "OR")
        self.assertEqual(ast["left"]["type"], "NOT")

    def test_iff_is_rewritten(self):
        ast = parse("A IFF B")
        self.assertEqual(ast["type"], "AND")

    def test_truth_table_format_and_order(self):
        table = truth_table(parse("A AND B"))
        self.assertEqual(table["variables"], ["A", "B"])
        self.assertEqual(table["rows"][0], {"inputs": {"A": 0, "B": 0}, "output": 0})
        self.assertEqual(table["rows"][-1], {"inputs": {"A": 1, "B": 1}, "output": 1})

    def test_repeated_variable_only_once(self):
        self.assertEqual(truth_table(parse("A AND A"))["variables"], ["A"])

    def test_bad_expression(self):
        with self.assertRaises(ExpressionError):
            parse("A AND")

    def test_contract_rejects_lowercase_and_long_names(self):
        with self.assertRaises(ExpressionError):
            parse("a AND B")
        with self.assertRaises(ExpressionError):
            parse("AB AND C")

    def test_empty_expression(self):
        with self.assertRaises(ExpressionError):
            parse("")

    def test_tautology_builds_a_circuit(self):
        # Used to fail with "Constants are not supported".
        ast = parse("A OR NOT A")
        self.assertEqual(ast["type"], "OR")
        outputs = [row["output"] for row in truth_table(ast)["rows"]]
        self.assertEqual(outputs, [1, 1])

    def test_contradiction_builds_a_circuit(self):
        ast = parse("A AND NOT A")
        self.assertEqual(ast["type"], "AND")
        outputs = [row["output"] for row in truth_table(ast)["rows"]]
        self.assertEqual(outputs, [0, 0])

    def test_constant_result_with_implication(self):
        # A -> A is always true; the arrow must still become AND/OR/NOT only.
        ast = parse("A -> A")
        self.assertEqual(ast["type"], "OR")
        self.assertEqual(ast["left"]["type"], "NOT")
        outputs = [row["output"] for row in truth_table(ast)["rows"]]
        self.assertEqual(outputs, [1, 1])
        ast = parse("A <-> NOT A")      # always false
        self.assertEqual(ast["type"], "AND")
        outputs = [row["output"] for row in truth_table(ast)["rows"]]
        self.assertEqual(outputs, [0, 0])

    def test_typed_constants_still_rejected(self):
        with self.assertRaises(ExpressionError):
            parse("A OR 1")


if __name__ == "__main__":
    unittest.main()
