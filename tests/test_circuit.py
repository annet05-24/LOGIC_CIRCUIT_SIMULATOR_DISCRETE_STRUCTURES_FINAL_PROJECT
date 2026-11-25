import itertools
import unittest

from logic_sim.circuit import build_circuit, propagate

GATE_W, GATE_H = 70, 44     # gate size used by the UI (logic_sim/ui/shapes.py)
INPUT_R = 14                # input/output circle radius used by the UI


def var(name):
    return {"type": "VAR", "name": name}


def NOT(operand):
    return {"type": "NOT", "operand": operand}


def AND(left, right):
    return {"type": "AND", "left": left, "right": right}


def OR(left, right):
    return {"type": "OR", "left": left, "right": right}


A, B, C, D, E, F, G, H = (var(n) for n in "ABCDEFGH")

# Circuits of a realistic size: at most 6 gate columns and 5 gates per column.
SAMPLE_ASTS = [
    OR(AND(A, B), NOT(C)),
    NOT(A),
    AND(A, A),
    OR(OR(AND(A, B), AND(C, D)), AND(E, F)),
    OR(NOT(AND(NOT(A), NOT(B))), AND(C, NOT(D))),
    AND(AND(AND(OR(A, B), OR(C, D)), OR(E, F)), OR(G, H)),
    AND(A, OR(B, AND(C, OR(D, NOT(E))))),
    AND(OR(NOT(A), B), OR(NOT(B), A)),      # A <-> B after the parser rewrites it
]


def segments(points):
    """Split a flat [x1, y1, x2, y2, ...] list into ((xa, ya), (xb, yb)) pieces."""
    pairs = list(zip(points[0::2], points[1::2]))
    return list(zip(pairs, pairs[1:]))


def crosses_gate(segment, gate):
    """True if a horizontal or vertical segment passes through the gate's box."""
    (xa, ya), (xb, yb) = segment
    left, right = gate["x"] - GATE_W / 2 + 1, gate["x"] + GATE_W / 2 - 1
    top, bottom = gate["y"] - GATE_H / 2 + 1, gate["y"] + GATE_H / 2 - 1
    return (min(xa, xb) < right and max(xa, xb) > left and
            min(ya, yb) < bottom and max(ya, yb) > top)


def all_nodes(circuit):
    return circuit["inputs"] + circuit["gates"] + [circuit["output"]]


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


class ContractTests(unittest.TestCase):
    """The rules of section 5 in docs/CONTRACTS.md, checked on many circuits."""

    def test_ids_are_unique(self):
        for ast in SAMPLE_ASTS:
            ids = [node["id"] for node in all_nodes(build_circuit(ast))]
            self.assertEqual(len(ids), len(set(ids)))

    def test_gates_are_in_evaluation_order(self):
        for ast in SAMPLE_ASTS:
            circuit = build_circuit(ast)
            seen = {node["id"] for node in circuit["inputs"]}
            for gate in circuit["gates"]:
                for source in gate["inputs"]:
                    self.assertIn(source, seen, f"{gate['id']} uses {source} too early")
                seen.add(gate["id"])
            self.assertIn(circuit["output"]["from"], seen)

    def test_gate_types_and_input_counts(self):
        for ast in SAMPLE_ASTS:
            for gate in build_circuit(ast)["gates"]:
                expected = 1 if gate["type"] == "NOT" else 2
                self.assertIn(gate["type"], ("AND", "OR", "NOT"))
                self.assertEqual(len(gate["inputs"]), expected)

    def test_every_node_inside_canvas(self):
        crowded = AND(AND(OR(A, B), OR(C, D)), AND(OR(E, F), OR(G, H)))
        crowded = AND(crowded, AND(OR(A, C), OR(B, D)))   # 6 gates in one column
        for ast in SAMPLE_ASTS + [crowded]:
            for node in all_nodes(build_circuit(ast)):
                self.assertTrue(0 <= node["x"] <= 600, node)
                self.assertTrue(0 <= node["y"] <= 300, node)


class LayoutTests(unittest.TestCase):
    def test_no_shapes_overlap(self):
        for ast in SAMPLE_ASTS:
            circuit = build_circuit(ast)
            gates = circuit["gates"]
            for g1, g2 in itertools.combinations(gates, 2):
                overlap = (abs(g1["x"] - g2["x"]) < GATE_W and
                           abs(g1["y"] - g2["y"]) < GATE_H)
                self.assertFalse(overlap, f"{g1['id']} overlaps {g2['id']}")
            for i1, i2 in itertools.combinations(circuit["inputs"], 2):
                self.assertGreaterEqual(abs(i1["y"] - i2["y"]), 2 * INPUT_R)
            for node in circuit["inputs"] + [circuit["output"]]:
                for gate in gates:
                    self.assertGreaterEqual(abs(node["x"] - gate["x"]),
                                            GATE_W / 2 + INPUT_R)

    def test_columns_go_left_to_right(self):
        for ast in SAMPLE_ASTS:
            circuit = build_circuit(ast)
            x = {node["id"]: node["x"] for node in all_nodes(circuit)}
            for gate in circuit["gates"]:
                for source in gate["inputs"]:
                    self.assertLess(x[source], gate["x"])
            self.assertLess(x[circuit["output"]["from"]], circuit["output"]["x"])

    def test_output_is_level_with_its_source(self):
        for ast in SAMPLE_ASTS + [A]:
            circuit = build_circuit(ast)
            y = {node["id"]: node["y"] for node in all_nodes(circuit)}
            self.assertEqual(circuit["output"]["y"], y[circuit["output"]["from"]])

    def test_not_gate_sits_level_with_its_input(self):
        circuit = build_circuit(AND(NOT(A), B))
        a = circuit["inputs"][0]
        not_gate = circuit["gates"][0]
        self.assertEqual(not_gate["type"], "NOT")
        self.assertEqual(not_gate["y"], a["y"])

    def test_one_wire_per_gate_input(self):
        for ast in SAMPLE_ASTS:
            circuit = build_circuit(ast)
            expected = sorted((s, g["id"]) for g in circuit["gates"] for s in g["inputs"])
            actual = sorted((w["from"], w["to"]) for w in circuit["wires"])
            self.assertEqual(actual, expected)

    def test_wires_are_horizontal_and_vertical_lines(self):
        for ast in SAMPLE_ASTS:
            for wire in build_circuit(ast)["wires"]:
                for (xa, ya), (xb, yb) in segments(wire["points"]):
                    self.assertTrue(xa == xb or ya == yb, wire)

    def test_wires_never_run_through_other_gates(self):
        # Problem 3: wires that skip a column used to cut through its gates.
        for ast in SAMPLE_ASTS:
            circuit = build_circuit(ast)
            for wire in circuit["wires"]:
                for gate in circuit["gates"]:
                    if gate["id"] in (wire["from"], wire["to"]):
                        continue
                    for segment in segments(wire["points"]):
                        self.assertFalse(crosses_gate(segment, gate),
                                         f"wire {wire['from']}->{wire['to']} "
                                         f"runs through {gate['id']}")

    def test_vertical_pieces_do_not_overlap(self):
        # Two different wires must never share the same vertical line.
        for ast in SAMPLE_ASTS:
            verticals = []
            for wire in build_circuit(ast)["wires"]:
                for (xa, ya), (xb, yb) in segments(wire["points"]):
                    if xa == xb and ya != yb:
                        verticals.append((xa, min(ya, yb), max(ya, yb), wire["from"]))
            for v1, v2 in itertools.combinations(verticals, 2):
                if v1[0] == v2[0] and v1[3] != v2[3]:
                    self.assertFalse(v1[1] < v2[2] and v2[1] < v1[2], (v1, v2))

    def test_inputs_keep_order_of_first_use(self):
        # Same order as the truth table columns, so toggles and table line up.
        circuit = build_circuit(AND(C, OR(A, B)))
        self.assertEqual([n["id"] for n in circuit["inputs"]], ["C", "A", "B"])


if __name__ == "__main__":
    unittest.main()
