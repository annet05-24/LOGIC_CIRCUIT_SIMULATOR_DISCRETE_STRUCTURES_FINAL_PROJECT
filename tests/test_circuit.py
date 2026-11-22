import itertools
import unittest

from logic_sim.circuit import build_circuit, propagate


def var(name):
    return {"type": "VAR", "name": name}


class CircuitTests(unittest.TestCase):
    def test_nested_expression_all_combinations(self):
        ast = {"type": "OR", "left": {"type": "AND", "left": var("A"),
               "right": var("B")}, "right": {"type": "NOT", "operand": var("C")}}
        circuit = build_circuit(ast)
        self.assertEqual([g["type"] for g in circuit["gates"]], ["AND", "NOT", "OR"])
        for a, b, c in itertools.product((0, 1), repeat=3):
            values = propagate(circuit, {"A": a, "B": b, "C": c})
            self.assertEqual(values["OUT"], int((a and b) or not c))
            self.assertEqual(set(values), {"A", "B", "C", "g1", "g2", "g3", "OUT"})

    def test_repeated_variable_and_direct_output(self):
        circuit = build_circuit({"type": "AND", "left": var("A"), "right": var("A")})
        self.assertEqual(len(circuit["inputs"]), 1)
        self.assertEqual(circuit["gates"][0]["inputs"], ["A", "A"])
        self.assertEqual(propagate(circuit, {"A": 1})["OUT"], 1)
        direct = build_circuit(var("B"))
        self.assertEqual(propagate(direct, {"B": 0})["OUT"], 0)
        self.assertEqual(direct["output"]["from"], "B")

    def test_layout_and_invalid_inputs(self):
        circuit = build_circuit({"type": "NOT", "operand": var("A")})
        for node in circuit["inputs"] + circuit["gates"] + [circuit["output"]]:
            self.assertTrue(0 <= node["x"] <= 600 and 0 <= node["y"] <= 300)
        with self.assertRaises(ValueError):
            propagate(circuit, {"A": 2})
        with self.assertRaises(ValueError):
            build_circuit({"type": "XOR"})
