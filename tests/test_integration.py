"""
End-to-end check from the project description (Section 3): the truth table
(Member 1) must agree with the simulated circuit (Member 2) on EVERY row.

Run from the project root:   python -m unittest discover -s tests -v
"""
import unittest

from logic_sim import backend

# Add more expressions here as the parser gets more capable.
EXPRESSIONS = [
    "(A AND B) OR NOT C",
]


class TestTruthTableMatchesCircuit(unittest.TestCase):
    def test_every_row_agrees(self):
        for expr in EXPRESSIONS:
            circuit = backend.get_circuit(expr)
            table = backend.get_truth_table(expr)
            out_id = circuit["output"]["id"]
            for row in table["rows"]:
                values = backend.propagate(circuit, row["inputs"])
                self.assertEqual(
                    values[out_id], row["output"],
                    msg=f"{expr!r} disagrees for inputs {row['inputs']}",
                )

    def test_table_has_every_combination(self):
        for expr in EXPRESSIONS:
            table = backend.get_truth_table(expr)
            self.assertEqual(len(table["rows"]), 2 ** len(table["variables"]))

    def test_bad_input_raises_value_error(self):
        with self.assertRaises(ValueError):
            backend.get_circuit("")


if __name__ == "__main__":
    unittest.main()
