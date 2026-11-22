"""
TEMPORARY stand-in for Members 1 and 2, so the UI can be built and tested
before the real modules exist.

It only understands TWO expressions:
    "A AND B"            -> a small circuit: 2 inputs, 1 AND gate
    anything else        -> (A AND B) OR NOT C   (3 inputs, 3 gates)
An empty expression raises ValueError, like the real parser will for bad input.

It follows the formats in docs/CONTRACTS.md exactly.
Delete this file once USE_MOCK is False in backend.py and everything works.
"""
import itertools 


def _is_a_and_b(expression):
    """True if the text is 'A AND B' (ignoring spaces and upper/lower case)."""
    return expression.replace(" ", "").upper() == "AANDB"


def get_circuit(expression):
    if not expression:
        raise ValueError("Please enter an expression.")

    if _is_a_and_b(expression):
        return {
            "inputs": [
                {"id": "A", "x": 60, "y": 100},
                {"id": "B", "x": 60, "y": 190},
            ],
            "gates": [
                {"id": "g1", "type": "AND", "x": 260, "y": 145, "inputs": ["A", "B"]},
            ],
            "output": {"id": "OUT", "x": 460, "y": 145, "from": "g1"},
        }

    return {
        "inputs": [
            {"id": "A", "x": 60, "y": 70},
            {"id": "B", "x": 60, "y": 140},
            {"id": "C", "x": 60, "y": 215},
        ],
        "gates": [
            {"id": "g1", "type": "AND", "x": 230, "y": 105, "inputs": ["A", "B"]},
            {"id": "g2", "type": "NOT", "x": 230, "y": 215, "inputs": ["C"]},
            {"id": "g3", "type": "OR", "x": 400, "y": 160, "inputs": ["g1", "g2"]},
        ],
        "output": {"id": "OUT", "x": 540, "y": 160, "from": "g3"},
    }


def propagate(circuit, assignment):
    """Push 0/1 values through the gates (gates are listed in order)."""
    values = dict(assignment)
    for gate in circuit["gates"]:
        ins = [values[source] for source in gate["inputs"]]
        if gate["type"] == "AND":
            values[gate["id"]] = int(all(ins))
        elif gate["type"] == "OR":
            values[gate["id"]] = int(any(ins))
        elif gate["type"] == "NOT":
            values[gate["id"]] = int(not ins[0])
    out = circuit["output"]
    values[out["id"]] = values[out["from"]]
    return values


def get_truth_table(expression):
    """Computed straight from the formula, NOT from the circuit, so the two
    can be compared in tests (that is the whole point of the project's final check)."""
    if not expression:
        raise ValueError("Please enter an expression.")

    if _is_a_and_b(expression):
        variables = ["A", "B"]
        formula = lambda a, b: int(a and b)
    else:
        variables = ["A", "B", "C"]
        formula = lambda a, b, c: int((a and b) or (not c))

    rows = []
    for combo in itertools.product([0, 1], repeat=len(variables)):
        rows.append({"inputs": dict(zip(variables, combo)), "output": formula(*combo)})
    return {"variables": variables, "rows": rows}