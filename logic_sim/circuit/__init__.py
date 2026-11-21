"""
MEMBER 2: Circuit generation and graph mapping.

Replace the stubs below with the real implementation (you can split the code
into several files in this folder, e.g. mapper.py, layout.py, propagation.py).
Keep the function names, inputs and outputs exactly as in docs/CONTRACTS.md.
"""


def build_circuit(ast):
    """AST -> circuit graph with gates, wires and x/y positions. See CONTRACTS.md."""
    raise NotImplementedError("Member 2: implement build_circuit()")


def propagate(circuit, assignment):
    """(circuit, {"A": 1, ...}) -> {node_id: 0 or 1} for every node. See CONTRACTS.md."""
    raise NotImplementedError("Member 2: implement propagate()")
